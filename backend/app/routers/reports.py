import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import current_user
from ..engine.plans import plan_details, plan_implantation
from ..engine.report_pdf import build_pdf
from ..models import Project, ShareLink, User
from ..services import compute_bundle, project_dicts
from .auth import limiter
from .projects import _own

router = APIRouter(tags=["rapports et partage"])
PLANS = {"implantation": plan_implantation, "details": plan_details}


def _calc(db, p, owner_id):
    try:
        return compute_bundle(db, p, owner_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))


def _pdf(db, p, owner_id, prices: bool) -> Response:
    an, m, d = _calc(db, p, owner_id)
    pj, soil, bld = project_dicts(p)
    return Response(build_pdf(pj, soil, bld, an, m, d if prices else None), media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="note-de-calcul.pdf"'})


def _svg(db, p, owner_id, name: str) -> Response:
    if name not in PLANS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan inconnu")
    an, _, _ = _calc(db, p, owner_id)
    return Response(PLANS[name](an, p.building), media_type="image/svg+xml")


# ------------------------------------------------------------ propriétaire
@router.get("/projects/{pid}/report.pdf")
def report(pid: int, prices: bool = True, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _pdf(db, _own(db, user, pid), user.id, prices)


@router.get("/projects/{pid}/plans/{name}.svg")
def plan(pid: int, name: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _svg(db, _own(db, user, pid), user.id, name)


class ShareIn(BaseModel):
    label: str = Field(default="", max_length=120)
    include_prices: bool = False
    expires_in_days: int | None = Field(default=30, ge=1, le=365)


def _h(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/projects/{pid}/shares", status_code=201)
def create_share(pid: int, data: ShareIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = _own(db, user, pid)
    token = secrets.token_urlsafe(24)
    exp = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days) if data.expires_in_days else None
    s = ShareLink(project_id=p.id, token_hash=_h(token), label=data.label, include_prices=data.include_prices, expires_at=exp)
    db.add(s)
    db.commit()
    return {"id": s.id, "token": token, "path": f"/shared/{token}", "expires_at": exp, "include_prices": s.include_prices,
            "note": "Le jeton n'est affiché qu'une seule fois."}


@router.get("/projects/{pid}/shares")
def list_shares(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = _own(db, user, pid)
    now = datetime.now(timezone.utc)
    return [{"id": s.id, "label": s.label, "include_prices": s.include_prices, "created_at": s.created_at, "expires_at": s.expires_at,
             "active": _active(s, now)} for s in db.scalars(select(ShareLink).where(ShareLink.project_id == p.id).order_by(ShareLink.id.desc()))]


@router.delete("/projects/{pid}/shares/{sid}", status_code=204)
def revoke_share(pid: int, sid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = _own(db, user, pid)
    s = db.get(ShareLink, sid)
    if not s or s.project_id != p.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lien introuvable")
    s.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=204)


# ------------------------------------------------------------ public (lecture seule)
def _active(s: ShareLink, now) -> bool:
    exp = s.expires_at.replace(tzinfo=timezone.utc) if s.expires_at and s.expires_at.tzinfo is None else s.expires_at
    return s.revoked_at is None and (exp is None or exp > now)


def _shared(db: Session, token: str) -> tuple[ShareLink, Project]:
    s = db.scalar(select(ShareLink).where(ShareLink.token_hash == _h(token)))
    if not s or not _active(s, datetime.now(timezone.utc)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lien invalide ou expiré")
    return s, db.get(Project, s.project_id)


@router.get("/shared/{token}")
@limiter.limit("60/minute")
def shared_view(request: Request, token: str, db: Session = Depends(get_db)):
    s, p = _shared(db, token)
    an, m, d = _calc(db, p, p.owner_id)
    out = {"lecture_seule": True, "projet": {"nom": p.name, "ville": p.city, "type": p.building_type}, "analyse": an, "metre": m}
    if s.include_prices:
        out["devis"] = d
    return out


@router.get("/shared/{token}/report.pdf")
@limiter.limit("20/minute")
def shared_pdf(request: Request, token: str, db: Session = Depends(get_db)):
    s, p = _shared(db, token)
    return _pdf(db, p, p.owner_id, s.include_prices)


@router.get("/shared/{token}/plans/{name}.svg")
@limiter.limit("60/minute")
def shared_plan(request: Request, token: str, name: str, db: Session = Depends(get_db)):
    _, p = _shared(db, token)
    return _svg(db, p, p.owner_id, name)
