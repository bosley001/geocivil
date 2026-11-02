"""Rapport PDF (reportlab). Polices DejaVu embarquées pour σ, λ, ≥, ², ³."""
from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from svglib.svglib import svg2rlg

from .plans import plan_details, plan_implantation

FD = Path(__file__).resolve().parent.parent / "assets" / "fonts"
pdfmetrics.registerFont(TTFont("DV", str(FD / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(FD / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV", boldItalic="DV-B")
ACC = colors.HexColor("#b4531a")
S = {"t": ParagraphStyle("t", fontName="DV-B", fontSize=20, leading=25, textColor=ACC),
     "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=13, leading=17, textColor=ACC, spaceBefore=12, spaceAfter=5, keepWithNext=1),
     "n": ParagraphStyle("n", fontName="DV", fontSize=9, leading=12.5),
     "s": ParagraphStyle("s", fontName="DV", fontSize=7.5, leading=10),
     "sb": ParagraphStyle("sb", fontName="DV-B", fontSize=7.5, leading=10)}
fmt = lambda x: f"{x:,.0f}".replace(",", " ")
ok = lambda b: "OK" if b else "NON"


def P(t, s="n"):
    return Paragraph(str(t), S[s])


def tbl(rows, widths, head=True):
    data = [[P(c, "sb" if head and i == 0 else "s") for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c9c7bf")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ece9e0")))
    t.setStyle(TableStyle(st))
    return t


def svg_flow(svg, width_mm=180):
    d = svg2rlg(BytesIO(svg.encode()))
    k = width_mm * mm / d.width
    d.width, d.height = d.width * k, d.height * k
    d.scale(k, k)
    return d


def _footer(c, doc):
    c.saveState()
    c.setFont("DV", 7)
    c.setFillColor(colors.grey)
    c.drawString(15 * mm, 9 * mm, "GéoCivil — pré-dimensionnement indicatif, à valider par un ingénieur agréé")
    c.drawRightString(195 * mm, 9 * mm, f"Page {doc.page}")
    c.restoreState()


def build_pdf(projet, soil, bld, an, m, d=None) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=16 * mm,
                            title=f"Note de pré-dimensionnement – {projet['nom']}", author="GéoCivil")
    v, g = an["verdict"], an["geometrie"]
    col = {"ok": "#2f7d3f", "warn": "#b7791f", "bad": "#b3261e"}[v["niveau"]]
    f = [P("Note de pré-dimensionnement", "t"), P(f"<b>{projet['nom']}</b> — {projet['ville']}"),
         P(f"{an['norme']} · béton C{an['materiaux']['fc28_MPa']:g} · acier fe {an['materiaux']['fe_MPa']:g} MPa · moteur v{an['version_moteur']} · {date.today():%d/%m/%Y}", "s"),
         Spacer(1, 6),
         Table([[P(f"<font color='white'><b>{v['texte']}</b><br/>Pression moyenne {v['pression_moyenne_kPa']} kPa pour {v['contrainte_admissible_kPa']:g} kPa admissibles "
                   f"(taux {v['taux'] * 100:.0f} %)</font>")]], colWidths=[180 * mm], style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(col)), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]),
         P("Données d'entrée", "h1"),
         tbl([["Sol", "Valeur", "Bâtiment", "Valeur"],
              ["Type de sol", soil["soil_type"], "Emprise", f"{bld['footprint_m2']:g} m² ({g['L_m']} × {g['l_m']} m)"],
              ["σ admissible", f"{soil['bearing_capacity_kpa']:g} kPa", "Niveaux", f"R+{bld['floors']} (h étage {bld['floor_height_m']:g} m)"],
              ["Nappe", f"{soil['water_table_depth_m']:g} m", "Trame", f"{g['poteaux_x']} × {g['poteaux_y']} poteaux (≈ {g['portee_x_m']} × {g['portee_y_m']} m)"],
              ["Zone inondable", "oui" if soil["flood_zone"] else "non", "Usage / toiture", f"{bld['usage']} / {bld['roof_type']}"],
              ["Étude géotechnique", soil["geotech_study"], "Verdict global", "toutes vérifications OK" if an["toutes_verifications_ok"] else "à revoir"]], [32, 38, 32, 78])]
    if an["alertes"]:
        f += [P("Alertes", "h1")] + [P(f"• {a}") for a in an["alertes"]]
    f += [P("Dalles", "h1"), tbl([["Niveau", "Ép.", "Travée x", "Travée y", "Chapeaux", "Contrainte acier ELS"]] +
         [[x["niveau"], f"{x['epaisseur_cm']:g} cm", f"{x['armatures_travee_x']['choix']}", x["armatures_travee_y"]["choix"], x["chapeaux_appui"]["choix"],
           f"σs = {x['verif_els']['sigma_s_MPa']} MPa"] for x in an["dalles"]], [34, 16, 32, 32, 32, 34])]
    f += [P("Poutres", "h1"), tbl([["Niveau", "Dir.", "Pos.", "L (m)", "Section", "Travée", "Appui", "Cadres", "τu / lim."]] +
         [[x["niveau"], x["direction"], x["position"], x["portee_m"], f"{x['section_cm'][0]:g}×{x['section_cm'][1]:g}", x["travee"]["choix"], x["appui_courant"]["choix"],
           x["effort_tranchant"]["cadres"], f"{x['effort_tranchant']['tau_u_MPa']}/{x['effort_tranchant']['limite_MPa']}"] for x in an["poutres"]], [28, 10, 18, 13, 18, 18, 18, 30, 27])]
    f += [P("Poteaux", "h1"), tbl([["Niveau", "Type", "Nu (kN)", "Section", "λ", "Armatures", "Cadres", "Nu ≤ Nu,lim"]] +
         [[x["niveau"], x["categorie"], x["Nu_kN"], f"{x['section_cm'][0]:g}×{x['section_cm'][1]:g}", x["elancement"], x["armatures"], x["cadres"],
           ok(x["verifications"][0]["ok"])] for x in an["poteaux"]["detail"]], [24, 20, 20, 20, 12, 24, 30, 30])]
    fd = an["fondations"]
    f += [P("Fondations", "h1"), P(f"Type retenu : <b>{fd['type_retenu']}</b> · fissuration {fd['classe_fissuration']} · taux d'occupation {fd['taux_occupation'] * 100:.0f} %")]
    if fd["semelles"]:
        f += [Spacer(1, 3), tbl([["Type", "Nb", "Côté A", "h", "Armatures", "Ancrage", "σ sol", "Poinçonn."]] +
              [[c, s["nombre"], f"{s['cote_A_m']:g} m", f"{s['hauteur_h_cm']:g} cm", s["armatures"], s["ancrage"], ok(s["verifications"][0]["ok"]), ok(s["verifications"][1]["ok"])]
               for c, s in fd["semelles"].items()], [18, 10, 18, 16, 46, 42, 14, 16])]
    f += [PageBreak(), P("Plans", "h1"), svg_flow(plan_implantation(an, _N(bld))), Spacer(1, 6), svg_flow(plan_details(an, _N(bld)))]
    f += [PageBreak(), P("Métré", "h1"), tbl([["Chapitre", "Poste", "Unité", "Quantité"]] + [[o["chapitre"], o["poste"], o["unite"], fmt(o["quantite"])] for o in m["ouvrages"]], [38, 100, 16, 26])]
    f += [P("Achats", "h1"), tbl([["Désignation", "Unité", "Quantité"]] + [[a["designation"], a["unite"], fmt(a["quantite"])] for a in m["achats"].values()], [110, 20, 50])]
    if d:
        rows = [["Désignation", "Qté", "Unité", "PU (FCFA)", "Total (FCFA)"]]
        for grp in ("brut", "pose"):
            rows += [[x["designation"], fmt(x["quantite"]), x["unite"], fmt(x["pu"]), fmt(x["total"])] for x in d["lignes"][grp]]
        s_ = d["sous_totaux"]
        rows += [["Main d'œuvre", "", "", f"{d['pourcentages']['mo_pct']:g} %", fmt(s_["main_oeuvre"])], ["Plomberie + électricité", "", "", f"{d['pourcentages']['lots_pct']:g} %", fmt(s_["plomberie_electricite"])],
                 ["Imprévus", "", "", f"{d['pourcentages']['imprevus_pct']:g} %", fmt(s_["imprevus"])], ["TOTAL ESTIMÉ", "", "", "", fmt(d["total_FCFA"])],
                 ["Coût par m² bâti", "", "", "", fmt(d["cout_par_m2_FCFA"])]]
        f += [P("Devis estimatif", "h1"), tbl(rows, [80, 20, 14, 32, 34])]
    f += [P("Hypothèses et limites", "h1")] + [P(f"• {h}", "s") for h in an["hypotheses"] + m["hypotheses"] + m["avertissements"]]
    f += [Spacer(1, 6), P("Ce document est un pré-dimensionnement automatisé. Il ne remplace ni l'étude géotechnique, ni la note de calcul et les plans d'exécution établis par un ingénieur "
                           "ou un bureau d'études agréé, qui engagent seuls la responsabilité de la construction.", "s")]
    doc.build(f, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


class _N:  # accès attribut aux dicts du bâtiment (plans.py attend un objet)
    def __init__(self, d): self.__dict__.update(d)
