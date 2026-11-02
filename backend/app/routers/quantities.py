import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import current_user
from ..engine.analysis import analyze
from ..engine.export_xlsx import build_xlsx
from ..engine.quantities import devis, metres
from ..models import User
from .prices import effective_prices
from .projects import _own

router = APIRouter(prefix="/projects", tags=["métrés et devis"])


def _build(db: Session, user: User, pid: int) -> dict:
    p = _own(db, user, pid)
    try:
        an = analyze(p.soil, p.building)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    m = metres(p.soil, p.building, an)
    prix = {x.key: x.value for x in effective_prices(db, user.id, p.city)}
    d = devis(m, prix)
    return {"projet": {"id": p.id, "nom": p.name, "ville": p.city}, "analyse_ok": an["toutes_verifications_ok"],
            "metre": m, "devis": d}


@router.get("/{pid}/quantities")
def quantities(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _build(db, user, pid)


@router.get("/{pid}/export/devis.xlsx")
def export_devis(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = _build(db, user, pid)
    name = re.sub(r"[^a-z0-9]+", "-", r["projet"]["nom"].lower()).strip("-") or "projet"
    return Response(build_xlsx(r["projet"], r["metre"], r["devis"]),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="devis-{name}.xlsx"'})
