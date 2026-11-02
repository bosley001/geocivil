from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

F = lambda **k: Font(name="Arial", size=k.pop("size", 10), **k)
BLUE, HEAD = "0000FF", PatternFill("solid", fgColor="D9D9D9")
NUM, MONEY = "#,##0.00;-#,##0.00;-", "#,##0;-#,##0;-"


def _w(ws, r, c, v, font=None, fmt=None, fill=None, al=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font or F()
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
    if al:
        cell.alignment = al
    return cell


def build_xlsx(projet: dict, m: dict, d: dict) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Devis"
    _w(ws, 1, 1, f"Devis estimatif – {projet['nom']}", F(bold=True, size=14))
    _w(ws, 2, 1, f"Ville : {projet['ville']} · Surface bâtie : {m['ratios']['surface_batie_m2']} m² · Montants en FCFA", F(italic=True))
    _w(ws, 3, 1, "Cellules en bleu : prix unitaires et pourcentages modifiables, les totaux se recalculent.", F(italic=True, color="808080"))
    r = 5
    for j, h in enumerate(("Désignation", "Unité", "Quantité", "Prix unitaire", "Total"), 1):
        _w(ws, r, j, h, F(bold=True), fill=HEAD, al=Alignment(horizontal="center"))
    subs = {}
    for grp, titre in (("brut", "MATÉRIAUX BRUTS (main d'œuvre ajoutée en %)"), ("pose", "FOURNITURES POSÉES (main d'œuvre incluse)")):
        r += 1
        _w(ws, r, 1, titre, F(bold=True))
        first = r + 1
        for x in d["lignes"][grp]:
            r += 1
            _w(ws, r, 1, x["designation"])
            _w(ws, r, 2, x["unite"])
            _w(ws, r, 3, x["quantite"], fmt=NUM)
            _w(ws, r, 4, x["pu"], F(color=BLUE), MONEY)
            _w(ws, r, 5, f"=C{r}*D{r}", fmt=MONEY)
        r += 1
        _w(ws, r, 1, "Sous-total", F(bold=True))
        _w(ws, r, 5, f"=SUM(E{first}:E{r - 1})" if r > first else 0, F(bold=True), MONEY)
        subs[grp] = r
    r += 2
    pct = {}
    for k, lab in (("mo_pct", "Main d'œuvre (% des matériaux bruts)"), ("lots_pct", "Plomberie + électricité (% des matériaux et fournitures)"),
                   ("imprevus_pct", "Imprévus (% du total)")):
        _w(ws, r, 1, lab)
        _w(ws, r, 4, d["pourcentages"][k] / 100, F(color=BLUE), "0.0%")
        pct[k] = r
        r += 1
    r += 1
    b, p = f"E{subs['brut']}", f"E{subs['pose']}"
    rows = [("Main d'œuvre", f"={b}*D{pct['mo_pct']}"), ("Plomberie + électricité", f"=({b}+{p})*D{pct['lots_pct']}")]
    start = r
    for lab, fml in rows:
        _w(ws, r, 1, lab)
        _w(ws, r, 5, fml, fmt=MONEY)
        r += 1
    _w(ws, r, 1, "Imprévus")
    _w(ws, r, 5, f"=({b}+{p}+E{start}+E{start + 1})*D{pct['imprevus_pct']}", fmt=MONEY)
    r += 1
    _w(ws, r, 1, "TOTAL ESTIMÉ", F(bold=True, size=11), fill=HEAD)
    _w(ws, r, 5, f"={b}+{p}+SUM(E{start}:E{r - 1})", F(bold=True, size=11), MONEY, HEAD)
    tot = r
    r += 1
    _w(ws, r, 1, "Coût par m² bâti")
    _w(ws, r, 5, f"=IFERROR(E{tot}/{m['ratios']['surface_batie_m2']},0)", fmt=MONEY)
    for col, w in zip("ABCDE", (52, 9, 12, 16, 18)):
        ws.column_dimensions[col].width = w

    w2 = wb.create_sheet("Métré")
    for j, h in enumerate(("Chapitre", "Poste", "Unité", "Quantité"), 1):
        _w(w2, 1, j, h, F(bold=True), fill=HEAD)
    for i, o in enumerate(m["ouvrages"], 2):
        _w(w2, i, 1, o["chapitre"])
        _w(w2, i, 2, o["poste"])
        _w(w2, i, 3, o["unite"])
        _w(w2, i, 4, o["quantite"], fmt=NUM)
    for col, w in zip("ABCD", (22, 52, 9, 14)):
        w2.column_dimensions[col].width = w

    w3 = wb.create_sheet("Hypothèses")
    lines = ["Ratios : " + ", ".join(f"{k} = {v}" for k, v in m["ratios"].items()), ""]
    lines += ["Avertissements :"] + m["avertissements"] + ["", "Hypothèses :"] + m["hypotheses"]
    lines += ["", "Pré-dimensionnement et métré indicatifs, à valider par un ingénieur agréé. Prix indicatifs, à ajuster."]
    for i, t in enumerate(lines, 1):
        _w(w3, i, 1, t, F(bold=t.endswith(":")))
    w3.column_dimensions["A"].width = 120
    wb.calculation.fullCalcOnLoad = True
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
