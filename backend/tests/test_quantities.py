from io import BytesIO
from types import SimpleNamespace as N

import pytest
from openpyxl import load_workbook

from app.engine.analysis import analyze
from app.engine.quantities import devis, metres

from .conftest import PROJECT, signup
from .test_engine import BLD, SOIL

PRIX = {"ciment": 6500, "sable": 12000, "gravier": 22000, "acier": 850, "bloc": 450, "bloc10": 380, "tole": 12000, "charpente": 8000,
        "carrelage": 9000, "peinture": 3500, "porte": 60000, "fenetre": 45000, "hardcore": 15000, "fouille": 3500, "coffrage": 4500,
        "etancheite": 7500, "mo_pct": 35, "lots_pct": 12, "imprevus_pct": 5}


def calc(**bld):
    s, b = N(**SOIL), N(**{**BLD, **bld})
    return metres(s, b, analyze(s, b))


def test_metre_ordres_de_grandeur():
    m = calc()
    a = m["achats"]
    assert 40 < m["ratios"]["acier_kg_par_m3_beton"] < 200
    # ~ 4 à 7 sacs de ciment par m² bâti pour une maison courante
    assert 3 < a["ciment"]["quantite"] / m["ratios"]["surface_batie_m2"] < 8
    assert a["tole"]["quantite"] > 120 * 1.1 and "etancheite" not in a


def test_terrasse_remplace_toiture_tole():
    a = calc(roof_type="terrasse")["achats"]
    assert "etancheite" in a and "tole" not in a and "charpente" not in a


def test_plus_d_etages_plus_de_matieres():
    q = [calc(floors=n)["achats"] for n in (0, 1, 2)]
    for k in ("ciment", "acier", "bloc", "carrelage"):
        assert q[0][k]["quantite"] < q[1][k]["quantite"] < q[2][k]["quantite"]


def test_devis_somme_coherente():
    d = devis(calc(), PRIX)
    s = d["sous_totaux"]
    base = s["materiaux_bruts"] + s["fournitures_posees"]
    assert s["main_oeuvre"] == pytest.approx(s["materiaux_bruts"] * 0.35, abs=1)
    assert s["plomberie_electricite"] == pytest.approx(base * 0.12, abs=1)
    assert d["total_FCFA"] == pytest.approx(sum(s.values()), abs=2)
    assert 80_000 < d["cout_par_m2_FCFA"] < 400_000


def test_endpoint_prix_utilisateur_et_excel(client):
    h = signup(client)
    pid = client.post("/projects", json=PROJECT, headers=h).json()["id"]
    r1 = client.get(f"/projects/{pid}/quantities", headers=h).json()
    client.put("/prices/overrides", json={"key": "ciment", "value": 13000}, headers=h)
    r2 = client.get(f"/projects/{pid}/quantities", headers=h).json()
    assert r2["devis"]["total_FCFA"] > r1["devis"]["total_FCFA"]
    x = client.get(f"/projects/{pid}/export/devis.xlsx", headers=h)
    assert x.status_code == 200 and "devis-villa-test.xlsx" in x.headers["content-disposition"]
    wb = load_workbook(BytesIO(x.content))
    assert wb.sheetnames == ["Devis", "Métré", "Hypothèses"]
    formulas = [c.value for row in wb["Devis"].iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=")]
    assert len(formulas) > 15 and any("SUM(" in f for f in formulas)
    other = signup(client, "z@test.cm")
    assert client.get(f"/projects/{pid}/quantities", headers=other).status_code == 404
