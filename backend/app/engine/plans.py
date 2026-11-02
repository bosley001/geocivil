"""Plans SVG (implantation des poteaux et semelles, détails de ferraillage). Aucune dépendance."""
from html import escape
from math import ceil, sqrt

CAT = {"angle": "P1", "rive": "P2", "courant": "P3"}
INK, GRID, FILL, ACC = "#1d1d1b", "#9a9a94", "#f3d9c8", "#b4531a"


def _t(x, y, s, size=11, anchor="middle", color=INK, bold=False):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" font-family="Helvetica"'
            f'{" font-weight=\"bold\"" if bold else ""}>{escape(str(s))}</text>')


def _svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')


def _geo(bld):
    L = sqrt(bld.footprint_m2 * bld.length_width_ratio)
    l = bld.footprint_m2 / L
    nx, ny = ceil(L / bld.column_span_m) + 1, ceil(l / bld.column_span_m) + 1
    return L, l, nx, ny


def plan_implantation(an: dict, bld) -> str:
    L, l, nx, ny = _geo(bld)
    W, M = 760, 80
    k = min((W - 2 * M) / L, 420 / l)
    ax, ay = L / (nx - 1), l / (ny - 1)
    leg = [f"{CAT[r['categorie']]} ({r['categorie']}) : poteau {r['section_cm'][0]:g}×{r['section_cm'][1]:g} cm, {r['armatures']}"
           for r in an["poteaux"]["detail"] if r["niveau"] == "RDC"]
    sem = an["fondations"]["semelles"] if an["fondations"]["type_retenu"].startswith("semelles") else {}
    for c, f in sem.items():
        leg.append(f"Semelle {CAT[c]} : {f['cote_A_m']:g}×{f['cote_A_m']:g} m, h={f['hauteur_h_cm']:g} cm, {f['armatures']}")
    H = int(l * k + 2 * M + 24 * len(leg) + 30)
    o = [_t(W / 2, 28, f"PLAN D'IMPLANTATION DES POTEAUX ET SEMELLES — {L:.2f} × {l:.2f} m", 14, bold=True)]
    x0, y0 = M, M
    for i in range(nx):
        x = x0 + i * ax * k
        o.append(f'<line x1="{x:.1f}" y1="{y0 - 20}" x2="{x:.1f}" y2="{y0 + l * k + 20}" stroke="{GRID}" stroke-dasharray="6 4"/>')
        o.append(_t(x, y0 - 28, chr(65 + i) if i < 26 else i, 12, bold=True))
        if i:
            o.append(_t(x - ax * k / 2, y0 - 8, f"{ax:.2f}", 10, color=ACC))
    for j in range(ny):
        y = y0 + j * ay * k
        o.append(f'<line x1="{x0 - 20}" y1="{y:.1f}" x2="{x0 + L * k + 20}" y2="{y:.1f}" stroke="{GRID}" stroke-dasharray="6 4"/>')
        o.append(_t(x0 - 34, y + 4, j + 1, 12, bold=True))
        if j:
            o.append(_t(x0 - 46, y - ay * k / 2 + 4, f"{ay:.2f}", 10, color=ACC))
    o.append(f'<rect x="{x0}" y="{y0}" width="{L * k:.1f}" height="{l * k:.1f}" fill="none" stroke="{INK}" stroke-width="2"/>')
    a = an["poteaux"]["section_cm"][0] / 100
    nodes = []
    for i in range(nx):
        for j in range(ny):
            ex, ey = i in (0, nx - 1), j in (0, ny - 1)
            c = "angle" if ex and ey else ("rive" if ex or ey else "courant")
            nodes.append((c, x0 + i * ax * k, y0 + j * ay * k))
    for c, x, y in nodes:                     # semelles d'abord, puis poteaux et repères au premier plan
        if c in sem:
            s = sem[c]["cote_A_m"] * k
            o.append(f'<rect x="{x - s / 2:.1f}" y="{y - s / 2:.1f}" width="{s:.1f}" height="{s:.1f}" fill="{FILL}" stroke="{ACC}" stroke-dasharray="4 2"/>')
    for c, x, y in nodes:
        p = max(a * k, 8)
        h = (sem[c]["cote_A_m"] * k if c in sem else p) / 2
        o.append(f'<rect x="{x - p / 2:.1f}" y="{y - p / 2:.1f}" width="{p:.1f}" height="{p:.1f}" fill="{INK}"/>')
        o.append(_t(x, y + h + 11, CAT[c], 10, color=ACC, bold=True))
    y = y0 + l * k + 50
    for s in leg:
        o.append(_t(M, y, s, 11, "start"))
        y += 24
    return _svg(W, H, "".join(o))


def _dots(xs, y, r=4, fill=INK):
    return "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>' for x in xs)


def plan_details(an: dict, bld) -> str:
    o = [_t(380, 26, "DÉTAILS DE FERRAILLAGE (sections types)", 14, bold=True)]
    # --- semelle
    sem = an["fondations"]["semelles"]
    if an["fondations"]["type_retenu"].startswith("semelles") and sem:
        c = "courant" if "courant" in sem else next(iter(sem))
        f = sem[c]
        A, h, a = f["cote_A_m"], f["hauteur_h_cm"] / 100, an["poteaux"]["section_cm"][0] / 100
        k = 190 / A
        x0, yb = 30, 250
        o.append(f'<rect x="{x0}" y="{yb - h * k:.1f}" width="{A * k:.1f}" height="{h * k:.1f}" fill="{FILL}" stroke="{INK}" stroke-width="1.5"/>')
        o.append(f'<rect x="{x0 + (A - a) / 2 * k:.1f}" y="{yb - h * k - 70:.1f}" width="{a * k:.1f}" height="70" fill="#dcdcd6" stroke="{INK}"/>')
        n = int(f["armatures"].split("HA")[0])
        xs = [x0 + (0.05 + (A - 0.10) * i / max(n - 1, 1)) * k for i in range(n)]
        o.append(_dots(xs, yb - 0.05 * k, 3.5, ACC))
        o += [_t(x0 + A * k / 2, yb + 22, f"Semelle {CAT[c]} : {A:g} × {A:g} m, h = {h * 100:g} cm", 11, bold=True),
              _t(x0 + A * k / 2, yb + 40, f["armatures"], 11, color=ACC), _t(x0 + A * k / 2, yb + 56, f["ancrage"], 9)]
    # --- poteau
    r = max((x for x in an["poteaux"]["detail"] if x["niveau"] == "RDC"), key=lambda x: x["Nu_kN"])
    a = r["section_cm"][0]
    k, x0, y0 = 150 / a, 300, 110
    o.append(f'<rect x="{x0}" y="{y0}" width="{a * k:.1f}" height="{a * k:.1f}" fill="#dcdcd6" stroke="{INK}" stroke-width="1.5"/>')
    e = 3 * k
    o.append(f'<rect x="{x0 + e}" y="{y0 + e}" width="{a * k - 2 * e:.1f}" height="{a * k - 2 * e:.1f}" fill="none" stroke="{INK}" stroke-width="1.5"/>')
    nb = int(r["armatures"].split("HA")[0])
    p = [x0 + e + 3, x0 + a * k - e - 3]
    pts = [(px, py) for px in p for py in (y0 + e + 3, y0 + a * k - e - 3)]
    if nb >= 8:
        m = x0 + a * k / 2
        pts += [(m, y0 + e + 3), (m, y0 + a * k - e - 3), (x0 + e + 3, y0 + a * k / 2), (x0 + a * k - e - 3, y0 + a * k / 2)]
    o.append("".join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{ACC}"/>' for px, py in pts))
    o += [_t(x0 + a * k / 2, y0 + a * k + 24, f"Poteau {a:g} × {a:g} cm (RDC)", 11, bold=True),
          _t(x0 + a * k / 2, y0 + a * k + 42, r["armatures"], 11, color=ACC), _t(x0 + a * k / 2, y0 + a * k + 58, f"cadres {r['cadres']}", 10)]
    # --- poutre
    b = max(an["poutres"], key=lambda x: x["travee"]["As_cm2"])
    bw, hb = b["section_cm"]
    k, x0, y0 = 230 / hb, 560, 60
    wpx, hpx = bw * k, hb * k
    hd = an["dalles"][0]["epaisseur_cm"] * k
    o.append(f'<rect x="{x0 - 30}" y="{y0}" width="{wpx + 60:.1f}" height="{hd:.1f}" fill="#dcdcd6" stroke="{INK}"/>')
    o.append(f'<rect x="{x0}" y="{y0 + hd:.1f}" width="{wpx:.1f}" height="{hpx - hd:.1f}" fill="#dcdcd6" stroke="{INK}" stroke-width="1.5"/>')
    e = 3 * k
    o.append(f'<rect x="{x0 + e}" y="{y0 + e + 0:.1f}" width="{wpx - 2 * e:.1f}" height="{hpx - 2 * e:.1f}" fill="none" stroke="{INK}" stroke-width="1.5"/>')
    nb = int(b["travee"]["choix"].split("HA")[0])
    o.append(_dots([x0 + e + 4 + (wpx - 2 * e - 8) * i / max(nb - 1, 1) for i in range(nb)], y0 + hpx - e - 4, 4.5, ACC))
    o.append(_dots([x0 + e + 4, x0 + wpx - e - 4], y0 + e + 4, 3.5))
    o += [_t(x0 + wpx / 2, y0 + hpx + 24, f"Poutre {bw:g} × {hb:g} cm", 11, bold=True), _t(x0 + wpx / 2, y0 + hpx + 42, f"travée : {b['travee']['choix']}", 11, color=ACC),
          _t(x0 + wpx / 2, y0 + hpx + 58, f"cadres {b['effort_tranchant']['cadres']}", 10)]
    return _svg(760, 340, "".join(o))
