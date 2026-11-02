from sqlalchemy.orm import Session

from .engine.analysis import analyze
from .engine.quantities import devis, metres
from .models import Project
from .routers.prices import effective_prices
from .schemas import BuildingOut, SoilOut


def compute_bundle(db: Session, p: Project, owner_id: int):
    """Analyse BAEL + métré + devis (prix du propriétaire du projet). Lève ValueError si hors périmètre."""
    an = analyze(p.soil, p.building)
    m = metres(p.soil, p.building, an)
    prix = {x.key: x.value for x in effective_prices(db, owner_id, p.city)}
    return an, m, devis(m, prix)


def project_dicts(p: Project):
    return ({"nom": p.name, "ville": p.city}, SoilOut.model_validate(p.soil).model_dump(), BuildingOut.model_validate(p.building).model_dump())
