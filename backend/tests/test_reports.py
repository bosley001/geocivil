import xml.etree.ElementTree as ET
from io import BytesIO

from pypdf import PdfReader

from .conftest import PROJECT, signup


def mk(client, h):
    return client.post("/projects", json=PROJECT, headers=h).json()["id"]


def test_pdf_et_plans(client):
    h = signup(client)
    pid = mk(client, h)
    r = client.get(f"/projects/{pid}/report.pdf", headers=h)
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    rd = PdfReader(BytesIO(r.content))
    txt = "".join(p.extract_text() for p in rd.pages)
    assert len(rd.pages) >= 5 and "Villa test" in txt and "TOTAL ESTIMÉ" in txt and "σ" in txt
    no = client.get(f"/projects/{pid}/report.pdf?prices=false", headers=h).content
    assert "TOTAL ESTIMÉ" not in "".join(p.extract_text() for p in PdfReader(BytesIO(no)).pages)
    for name in ("implantation", "details"):
        s = client.get(f"/projects/{pid}/plans/{name}.svg", headers=h)
        assert s.status_code == 200 and ET.fromstring(s.text).tag.endswith("svg")
    assert "P3" in client.get(f"/projects/{pid}/plans/implantation.svg", headers=h).text
    assert client.get(f"/projects/{pid}/plans/inconnu.svg", headers=h).status_code == 404


def test_partage_cycle_de_vie(client):
    h, other = signup(client), signup(client, "o@test.cm")
    pid = mk(client, h)
    assert client.post(f"/projects/{pid}/shares", json={}, headers=other).status_code == 404
    s = client.post(f"/projects/{pid}/shares", json={"label": "Client X"}, headers=h).json()
    tok = s["token"]
    pub = client.get(f"/shared/{tok}")                       # sans authentification
    assert pub.status_code == 200 and pub.json()["lecture_seule"] and "devis" not in pub.json()
    assert client.get(f"/shared/{tok}/report.pdf").content[:4] == b"%PDF"
    assert client.get(f"/shared/{tok}/plans/details.svg").status_code == 200
    assert client.get("/shared/jeton-bidon").status_code == 404
    lst = client.get(f"/projects/{pid}/shares", headers=h).json()
    assert lst[0]["active"] and "token" not in lst[0]
    assert client.delete(f"/projects/{pid}/shares/{s['id']}", headers=h).status_code == 204
    assert client.get(f"/shared/{tok}").status_code == 404


def test_partage_avec_prix_et_expiration(client):
    from datetime import datetime, timedelta, timezone
    from app.database import SessionLocal
    from app.models import ShareLink
    h = signup(client)
    pid = mk(client, h)
    s = client.post(f"/projects/{pid}/shares", json={"include_prices": True}, headers=h).json()
    assert "devis" in client.get(f"/shared/{s['token']}").json()
    with SessionLocal() as db:
        db.get(ShareLink, s["id"]).expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
    assert client.get(f"/shared/{s['token']}").status_code == 404
