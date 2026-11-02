"""Métrés et devis déduits de l'analyse BAEL (aciers lus dans les choix de ferraillage réels)."""
import re
from collections import defaultdict
from math import ceil, sqrt

from .bael import AREA

KG = lambda phi: 0.00617 * phi * phi          # kg/m d'un HA de diamètre phi (mm)
rd = lambda x, n=2: round(float(x), n)
BRUT = ("ciment", "sable", "gravier", "acier", "bloc", "bloc10", "hardcore", "peinture", "coffrage")
POSE = ("fouille", "tole", "charpente", "carrelage", "etancheite", "porte", "fenetre")


def _bars(t):
    g = re.match(r"(\d+)HA(\d+)", t)
    return int(g[1]), int(g[2])


def _spaced(t):
    g = re.match(r"HA(\d+) e=([\d.]+) cm", t)
    return int(g[1]), float(g[2]) / 100


def metres(soil, bld, an: dict) -> dict:
    F, hf, S = bld.floors + 1, bld.floor_height_m, bld.footprint_m2
    L = sqrt(S * bld.length_width_ratio)
    l = S / L
    nx, ny = ceil(L / bld.column_span_m) + 1, ceil(l / bld.column_span_m) + 1
    ax, ay = L / (nx - 1), l / (ny - 1)
    P, Ls = 2 * (L + l), ny * L + nx * l
    D = 1.5 if soil.soil_type == "argile" else 1.2
    hd = an["dalles"][0]["epaisseur_cm"] / 100
    bw, hb = an["poutres"][0]["section_cm"][0] / 100, an["poutres"][0]["section_cm"][1] / 100
    a = an["poteaux"]["section_cm"][0] / 100
    cnt = an["geometrie"]["repartition_poteaux"]
    terr = bld.roof_type == "terrasse"
    V, st, cf, warn = defaultdict(float), defaultdict(float), defaultdict(float), []

    # ---- fondations
    kind, sem = an["fondations"]["type_retenu"], an["fondations"]["semelles"]
    hs, exc = 0.30, 0.0
    if kind.startswith("pieux"):
        warn.append("Fondations profondes (pieux) : quantités de fondations non calculées, étude spécifique requise.")
    elif kind.startswith("radier"):
        e = 0.40 if F >= 3 else 0.30
        V["propreté"] += S * 1.1 * 0.05
        V["radier"] += S * 1.1 * e
        st["fondations"] += S * 1.1 * e * 100
        cf["fondations"] += P * e
        exc += (L + 1) * (l + 1) * (e + 0.5)
        hs = e
        warn.append("Radier : béton et acier estimés au ratio (100 kg/m³), ferraillage détaillé non calculé en phase 1.")
    else:
        if kind.startswith("semelles filantes"):
            warn.append("Semelles filantes recommandées : quantités calculées sur les semelles isolées équivalentes (indicatif).")
        hs = sem[next(iter(sem))]["hauteur_h_cm"] / 100
        for f in sem.values():
            n, A, h = f["nombre"], f["cote_A_m"], f["hauteur_h_cm"] / 100
            nb, dia = _bars(f["armatures"])
            V["semelles"] += n * A * A * h
            V["propreté"] += n * (A + 0.2) ** 2 * 0.05
            cf["fondations"] += n * 4 * A * h
            exc += n * (A + 0.6) ** 2 * D
            st["fondations"] += n * 2 * nb * (A + 0.1) * KG(dia)
    fut = max(D - hs + 0.3, 0.3)
    V["fûts"] = sum(cnt.values()) * a * a * fut
    cf["fondations"] += sum(cnt.values()) * 4 * a * fut
    # longrines (minimum constructif 25×30, 4HA12, cadres HA6 e=20)
    V["longrines"] = Ls * 0.25 * 0.30
    st["fondations"] += Ls * 4 * KG(12) + Ls / 0.20 * (2 * 0.19 + 2 * 0.24 + 0.2) * KG(6)
    cf["fondations"] += Ls * 0.85
    exc += Ls * 0.5 * 0.5
    decap = (L + 2) * (l + 2) * 0.2

    # ---- poteaux
    for r in an["poteaux"]["detail"]:
        n = cnt[r["categorie"]]
        nb, dia = _bars(r["armatures"])
        phit, e = _spaced(r["cadres"])
        V["poteaux"] += n * a * a * (hf - hb)
        cf["ossature"] += n * 4 * a * (hf - hb)
        st["poteaux"] += n * (nb * (hf + 0.04 * dia) * KG(dia) + (ceil((hf - hb) / e) + 1) * (4 * (a - 0.06) + 0.2) * KG(phit))
        if r["niveau"] == "RDC":
            st["poteaux"] += n * nb * (fut + 0.2) * KG(dia)

    # ---- poutres
    lev_n = {"Plancher courant": F - 1, "Toiture": 1}
    for r in an["poutres"]:
        x = r["direction"] == "x"
        lines, spans, Lb = (ny, nx - 1, ax) if x else (nx, ny - 1, ay)
        nl = 2 if r["position"] == "rive" else max(lines - 2, 0)
        k = nl * spans * lev_n[r["niveau"]]
        if not k:
            continue
        nb, dia = _bars(r["travee"]["choix"])
        na, dna = _bars(r["appui_courant"]["choix"])
        phit, e = _spaced(r["effort_tranchant"]["cadres"])
        V["poutres"] += k * bw * (hb - hd) * Lb
        cf["ossature"] += k * (bw + 2 * (hb - hd)) * Lb
        st["poutres"] += k * (nb * (Lb + 0.4) * KG(dia) + na * 0.6 * Lb * KG(dna)
                              + (ceil(Lb / e) + 1) * (2 * (bw - 0.06) + 2 * (hb - 0.06) + 0.2) * KG(phit))

    # ---- dalles
    area = L * l
    V["dalles"] = area * hd * F * 1.04      # +4 % : escalier et trémies (forfait)
    cf["ossature"] += area * F
    for r in an["dalles"]:
        d1, s1 = _spaced(r["armatures_travee_x"]["choix"])
        d2, s2 = _spaced(r["armatures_travee_y"]["choix"])
        d3, s3 = _spaced(r["chapeaux_appui"]["choix"])
        A1, A2, A3 = AREA[d1] / s1, AREA[d2] / s2, AREA[d3] / s3
        n = lev_n[r["niveau"]]
        st["dalles"] += n * area * 0.785 * (A1 + A2 + 0.9 * A3)

    # ---- maçonnerie, enduits, finitions
    hw = hf - hb
    portes, fen = ceil(S * F / 25) + F, ceil(S * F / 12)
    ext = max(0.6 * P * hw * F, P * hw * F - fen * 1.44 - 0.2 * portes * 1.9) + P * 0.6
    inte = max(0.6 * 0.35 * S * hw * F, 0.35 * S * hw * F - 0.8 * portes * 1.9)
    joints = ext * 0.012 + inte * 0.008
    enduit = (ext + inte) * 0.04 + S * F * 0.015 + S * F * 0.04      # murs 2 faces + plafonds + chape
    if terr:
        enduit += S * 0.06                                            # forme de pente
    util = 0.9 * S * F
    toit = (L + 0.8) * (l + 0.8) * sqrt(1 + (bld.roof_slope_pct / 100) ** 2)

    # ---- agrégats
    v25 = sum(V[k] for k in ("semelles", "radier", "longrines", "fûts", "poteaux", "poutres", "dalles"))
    vdal, vprop = S * 0.10, V["propreté"]
    W = 1.05
    cim = (v25 * 350 + vdal * 300 + vprop * 150) * W + joints * 350 + enduit * 400
    sab = (v25 * 0.40 + vdal * 0.45 + vprop * 0.5) * W + (joints + enduit) * 1.1
    gra = (v25 * 0.80 + vdal * 0.85 + vprop * 0.9) * W
    eau = ((v25 * 0.175 + vdal * 0.17 + vprop * 0.12) * W + (joints + enduit) * 0.25)
    acier = sum(st.values()) * 1.05
    coffr = sum(cf.values())
    ratio = sum(st.values()) / v25 if v25 else 0
    if not 45 <= ratio <= 220:
        warn.append(f"Ratio d'acier atypique ({ratio:.0f} kg/m³ de béton) : à contrôler.")

    O = lambda c, p, u, q, d="": {"chapitre": c, "poste": p, "unite": u, "quantite": rd(q), "detail": d}
    ouv = [O("1. Terrassement", "Décapage terre végétale", "m³", decap), O("1. Terrassement", "Fouilles (semelles, longrines)", "m³", exc),
           O("1. Terrassement", "Tout-venant sous dallage (20 cm)", "m³", S * 0.2),
           O("2. Fondations", "Béton de propreté", "m³", vprop), O("2. Fondations", "Béton semelles / radier", "m³", V["semelles"] + V["radier"]),
           O("2. Fondations", "Béton fûts de poteaux", "m³", V["fûts"]), O("2. Fondations", "Béton longrines (minimum constructif)", "m³", V["longrines"]),
           O("2. Fondations", "Acier fondations", "kg", st["fondations"]), O("2. Fondations", "Dallage RDC (10 cm)", "m³", vdal),
           O("3. Ossature", "Béton poteaux", "m³", V["poteaux"]), O("3. Ossature", "Béton poutres", "m³", V["poutres"]),
           O("3. Ossature", "Béton dalles (escalier inclus, +4 %)", "m³", V["dalles"]),
           O("3. Ossature", "Acier poteaux", "kg", st["poteaux"]), O("3. Ossature", "Acier poutres", "kg", st["poutres"]),
           O("3. Ossature", "Acier dalles", "kg", st["dalles"]), O("3. Ossature", "Coffrage (ossature + fondations)", "m²", coffr),
           O("4. Maçonnerie", "Murs extérieurs 15 cm + soubassement (net)", "m²", ext), O("4. Maçonnerie", "Cloisons 10 cm (net)", "m²", inte),
           O("4. Maçonnerie", "Mortier joints", "m³", joints), O("4. Maçonnerie", "Enduits, chape et forme de pente", "m³", enduit),
           O("5. Toiture", "Étanchéité terrasse" if terr else "Couverture tôle (avec recouvrement 10 %)", "m²", (L * l + P * 0.5) if terr else toit * 1.10),
           O("6. Finitions", "Carrelage (surface utile + 10 %)", "m²", util * 1.10), O("6. Finitions", "Portes", "u", portes),
           O("6. Finitions", "Fenêtres", "u", fen)]
    if not terr:
        ouv.insert(-3, O("5. Toiture", "Charpente", "m²", toit))
    ach = {"ciment": ("Ciment 50 kg", "sac", ceil(cim / 50)), "sable": ("Sable", "m³", sab), "gravier": ("Gravier", "m³", gra),
           "acier": ("Acier HA (chutes 5 % incluses)", "kg", acier), "bloc": ("Parpaings 15 cm (+5 %)", "u", ext * 12.5 * 1.05),
           "bloc10": ("Parpaings 10 cm (+5 %)", "u", inte * 12.5 * 1.05), "hardcore": ("Tout-venant", "m³", S * 0.2),
           "peinture": ("Peinture (3 couches)", "L", ((ext + inte) * 2 + util) * 0.3), "coffrage": ("Coffrage (bois, étais, pointes)", "m²", coffr),
           "fouille": ("Terrassement (fouilles + décapage)", "m³", exc + decap), "carrelage": ("Carrelage posé", "m²", util * 1.10),
           "porte": ("Portes", "u", portes), "fenetre": ("Fenêtres", "u", fen)}
    if terr:
        ach["etancheite"] = ("Étanchéité terrasse posée", "m²", L * l + P * 0.5)
    else:
        ach["tole"] = ("Couverture tôle posée", "m²", toit * 1.10)
        ach["charpente"] = ("Charpente", "m²", toit)
    return {"ouvrages": ouv, "achats": {k: {"designation": v[0], "unite": v[1], "quantite": rd(v[2])} for k, v in ach.items()},
            "ratios": {"acier_kg_par_m3_beton": rd(ratio, 0), "beton_C25_m3": rd(v25), "surface_batie_m2": rd(S * F), "eau_m3": rd(eau)},
            "avertissements": warn,
            "hypotheses": ["Béton C25 : 350 kg de ciment/m³ (dallage C20 : 300), pertes de 5 %.",
                           "Aciers lus dans le ferraillage calculé (longueurs avec recouvrements et crochets), + 5 % de chutes.",
                           "Chapeaux de dalle et longrines : approximations de métré (longrines 25×30 cm, 4HA12, minimum constructif).",
                           "Cloisons : 0,35 m par m² de plancher ; ouvertures déduites des murs ; escalier au forfait (+4 % de dalle).",
                           "Ratios d'acier issus du calcul strict BAEL, sans majoration constructive : à valider avec les plans d'exécution.",
                           "Métré d'avant-projet à ± 15 % : à affiner avec les plans d'exécution."]}


def devis(m: dict, prix: dict) -> dict:
    """prix : clé -> valeur FCFA. MO sur les matériaux bruts ; postes « posés » sans MO supplémentaire."""
    lignes = {"brut": [], "pose": []}
    for grp, keys in (("brut", BRUT), ("pose", POSE)):
        for k in keys:
            a = m["achats"].get(k)
            if a and a["quantite"] > 0:
                pu = prix.get(k, 0.0)
                lignes[grp].append({"cle": k, **a, "pu": pu, "total": rd(a["quantite"] * pu, 0)})
    brut = sum(x["total"] for x in lignes["brut"])
    pose = sum(x["total"] for x in lignes["pose"])
    mo = brut * prix.get("mo_pct", 35) / 100
    lots = (brut + pose) * prix.get("lots_pct", 12) / 100
    imp = (brut + pose + mo + lots) * prix.get("imprevus_pct", 5) / 100
    tot = brut + pose + mo + lots + imp
    S = m["ratios"]["surface_batie_m2"]
    return {"lignes": lignes, "pourcentages": {k: prix.get(k, d) for k, d in (("mo_pct", 35), ("lots_pct", 12), ("imprevus_pct", 5))},
            "sous_totaux": {"materiaux_bruts": rd(brut, 0), "fournitures_posees": rd(pose, 0), "main_oeuvre": rd(mo, 0),
                            "plomberie_electricite": rd(lots, 0), "imprevus": rd(imp, 0)},
            "total_FCFA": rd(tot, 0), "cout_par_m2_FCFA": rd(tot / S, 0) if S else 0}
