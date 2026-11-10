"""ESP 2024 Task 2 drawings: the A3 sheets for the harbour buoy, made from the CAD model (models/esp2024.py).

  ESP24-GA-01  General arrangement: front and side views 1:20 with the waterline and the heights, plan 1:10,
               isometric, parts summary and notes
  ESP24-GA-02  Section A-A through the float, canister and mast foot (1:8), view on the open hatch (1:5),
               how the 12 V power works, and the specification check
  ESP24-GA-03  Details: mooring eye, load pin and shackle (1:3), watertight hatch (1:2), lantern and topmark (1:5)
  ESP24-GA-04  Part A design ideas: design A (solar, polyethylene float) and design B (wind, steel sphere)
  ESP24-GA-05  Parts list (all 43 parts) with a ballooned view of the buoy
  ESP24-GA-06  The seven sub-assemblies, exploded, with their parts ballooned
  ESP24-GA-07  Assembly structure and order of assembly

Output: docs/ESP 2024/drawings/ESP24-GA-0n_*.svg and .png.
Run from the repository root:  python3 tools/esp2024_drawings.py [1 2 3 4 5 6 7]
"""
import json, math, os, sys
import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import esp2024 as E  # noqa: E402
import drawings as D  # noqa: E402
from esp2023_drawings import View, place, phantom, text_block, leader, section_view, parts_list, comp  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'ESP 2024', 'drawings')
OWNER, DATE = 'Harbour Shipping Ltd', '2026-11-10'
EXTRA_STYLE = ('<style>.ph{fill:none;stroke:#555;stroke-width:0.25;stroke-dasharray:6,1.2,1,1.2,1,1.2}'
               '.box{fill:none;stroke:#111;stroke-width:0.3}.tbl{fill:none;stroke:#111;stroke-width:0.25}'
               '.lead{fill:none;stroke:#111;stroke-width:0.2}.wl{fill:none;stroke:#1565D8;stroke-width:0.35;'
               'stroke-dasharray:5,1.5}.wlt{fill:#1565D8}</style>')
NO = {p['key']: p['no'] for p in E.PARTS}
_N = {}


def calc():
    """Floating, energy and cost numbers from the calculation sheet (computed once)."""
    if not _N:
        import esp2024_calcs as C
        _N.update(C.numbers())
    return _N


def finish(sh, name, title, number, scale, doctype='Assembly drawing', material='See parts list'):
    sh.add(EXTRA_STYLE)
    D.frame(sh, title, number, scale, 'third', material, doctype, OWNER, DATE)
    D.save(sh, name, OUT)
    print('drew', name)


def items_of(variant='red', keep=None):
    return [(n, s, E.colour(k, variant)) for n, k, s in E.buoy_instances(variant) if keep is None or keep(n, k)]


def waterline(sh, x0, x1, y, label=True):
    """The waterline: a blue chain line with the water symbol."""
    sh.add('<line class="wl" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (x0, y, x1, y))
    xs = x1 - 6
    sh.add('<polygon class="wlt" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f"/>' % (xs - 1.6, y - 2.6, xs + 1.6, y - 2.6, xs, y))
    for k, w in enumerate((3.0, 2.0, 1.0)):
        sh.line(xs - w / 2, y + 0.9 + k * 0.9, xs + w / 2, y + 0.9 + k * 0.9, 'thin')
    if label:
        sh.text(x0, y - 1.2, 'WL', size=2.2, anchor='start', weight='bold')


def table(sh, x, y, w, rows, h=4.4, size=2.05, title=None):
    if title:
        sh.text(x, y - 2, title, size=3, anchor='start', weight='bold')
    for r, row in enumerate(rows):
        xx = x
        for c, cell in enumerate(row):
            sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (xx, y + r * h, w[c], h))
            sh.text(xx + 1, y + r * h + h * 0.7, cell, size=size, anchor='start', weight='bold' if r == 0 else 'normal')
            xx += w[c]
    return y + len(rows) * h


def iso_fit(sh, shape, x, y, w, h, d=(-1, -1.3, 0.55)):
    """Draw an isometric (no hidden lines) to fit the box (x, y, w, h); returns (ox, oy, scale)."""
    D.ISO_DIR['d'] = d
    data = D.view_data(shape, 'iso', hidden=False)
    bx0, by0, bx1, by1 = data['bb']
    si = min(w / (bx1 - bx0), h / (by1 - by0))
    ox = x + (w - (bx1 - bx0) * si) / 2 - bx0 * si
    oy = y + (h - (by1 - by0) * si) / 2 + by1 * si
    D.draw_view(sh, data, ox, oy, si)
    return ox, oy, si


def balloon(sh, px, py, bx, by, no, r=2.6):
    sh.add('<line class="lead" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (px, py, bx, by))
    sh.add('<circle cx="%.2f" cy="%.2f" r="0.5" fill="#111"/>' % (px, py))
    sh.add('<circle class="box" cx="%.2f" cy="%.2f" r="%.2f" fill="#fff"/>' % (bx, by, r))
    sh.text(bx, by + 0.9, str(no), size=2.3, weight='bold')


def iproj(p):
    """Project a model point as the hidden line view does: the paper x axis is made square to the view direction first
    (drawings.proj uses it as given, which is only right when it is already square)."""
    n, vx, vy = D.basis('iso')
    k = sum(a * b for a, b in zip(vx, n))
    x = D.unit(tuple(a - k * b for a, b in zip(vx, n)))
    y = (n[1] * x[2] - n[2] * x[1], n[2] * x[0] - n[0] * x[2], n[0] * x[1] - n[1] * x[0])
    return sum(a * b for a, b in zip(p, x)), sum(a * b for a, b in zip(p, y))


def centre(s):
    bb = s.val().BoundingBox()
    return ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)


def _range(group):
    nos = [p['no'] for p in E.PARTS if p['group'] == group]
    return '%d-%d' % (nos[0], nos[-1])


# ------------------------------------------------------------------ GA-01 general arrangement
def ga01():
    sh = D.Sheet()
    n = calc()
    h = n['moored']['h']
    s = 1 / 20
    allc = comp(items_of())
    bb = allc.BoundingBox()
    # front view
    Fd, fox, foy = place(allc, 'front', s, 40, 34, hidden=False)
    F = View(sh, None, 'front', s, fox, foy, data=Fd)
    fx0, fy0, fx1, fy1 = F.bb()
    w = F.P((0, 0, h))
    waterline(sh, fx0 - 22, fx1 + 12, w[1])
    sh.text((fx0 + fx1) / 2, fy1 + 9, 'FRONT VIEW, 1:20', size=3, weight='bold')
    # heights on the left, from the waterline
    for k, (z, lab) in enumerate(((E.CAN_TM[3], '%.0f ABOVE THE SEA' % (E.CAN_TM[3] - h)),
                                  (E.DECK[1], '%.0f' % (E.DECK[1] - h)))):
        a = F.P((-E.FENDER_R, 0, z))
        D.dim_v(sh, a[1], w[1], fx0 - 8 - 9 * k, a[0] if k else fx0 + 8, lab)
    a, b = F.P((-E.FLOAT_R, 0, E.FLOAT_BOT)), F.P((-E.FLOAT_R, 0, E.BOT_PLATE[0]))
    D.dim_v(sh, w[1], a[1], fx0 - 8, a[0], '%.0f' % (h - E.FLOAT_BOT))
    D.dim_v(sh, w[1], b[1], fx0 - 17, b[0] + 12, '%.0f' % (h - E.BOT_PLATE[0]))
    # overall height on the right
    a, b = F.P((E.FENDER_R, 0, bb.zmax)), F.P((E.FENDER_R, 0, bb.zmin))
    D.dim_v(sh, a[1], b[1], fx1 + 20, fx1 - 10, '%.0f OVERALL' % (bb.zmax - bb.zmin))
    # diameters
    a, b = F.P((-E.FLOAT_R, 0, E.FLOAT_BOT)), F.P((E.FLOAT_R, 0, E.FLOAT_BOT))
    sh.text(b[0] + 3, a[1] - 3, 'Ø%d FLOAT' % (2 * E.FLOAT_R), size=2.2, anchor='start')
    a = F.P((E.FENDER_R, 0, (E.GROOVE[1] + E.GROOVE[2]) / 2))
    leader(sh, a[0], a[1], a[0] + 8, a[1] - 8, 'Ø%d FENDER' % (2 * E.FENDER_R), 2.2)
    a = F.P((0, 0, E.PIN_Z))
    leader(sh, a[0] + 1, a[1], a[0] + 9, a[1] + 6, 'LOAD PIN (%d)' % NO['load_pin'], 2.2)
    a = F.P((0, 0, bb.zmin + 30))
    leader(sh, a[0] + 1, a[1], a[0] + 9, a[1] + 2, 'CHAIN TO SINKER', 2.2)
    # side view (third angle: viewed from the right, drawn on the right)
    Rd, rox, roy = place(allc, 'right', s, 112, 34, hidden=False)
    R = View(sh, None, 'right', s, rox, foy, data=Rd)
    rx0, ry0, rx1, ry1 = R.bb()
    waterline(sh, rx0 - 6, rx1 + 8, w[1], label=False)
    sh.text((rx0 + rx1) / 2, fy1 + 9, 'SIDE VIEW, 1:20', size=3, weight='bold')
    # plan, 1:10, top right of the views
    sp = 1 / 10
    Pd, pox, poy = place(allc, 'plan', sp, 150, 30, hidden=False)
    P = View(sh, None, 'plan', sp, pox, poy, data=Pd)
    px0, py0, px1, py1 = P.bb()
    sh.text((px0 + px1) / 2, py1 + 6, 'PLAN, 1:10', size=3, weight='bold')
    a, b = P.P((-E.FENDER_R, 0, 0)), P.P((E.FENDER_R, 0, 0))
    D.dim_h(sh, a[0], b[0], py0 - 4, a[1], 'Ø%d' % (2 * E.FENDER_R))
    sh.text((px0 + px1) / 2, py1 + 10, '3 SOLAR PANELS AT 120°', size=2.2)
    # isometric
    ox, oy, si = iso_fit(sh, allc, 205, 16, 80, 222)
    sh.text(245, 244, 'ISOMETRIC (NOT TO SCALE)', size=3, weight='bold')
    # parts summary and notes
    rows = [('Items', 'Sub-assembly', 'Qty', 'Main material')] + [
        (_range(g), t.split(' (')[0].split(':')[0], '1', mat) for (g, t), mat in zip(E.GROUPS, (
            'MDPE, PU foam, EVA, 316L', '316L, LiFePO4, EPDM', '316L, heavy concrete, zinc', '316L, PV panels',
            'PC lens, MDPE, 316L', 'Galvanised steel'))]
    yb = table(sh, 296, 24, (13, 46, 8, 43), rows, title='SUB-ASSEMBLIES (FULL LIST ESP24-GA-05)')
    m = n['moored']
    text_block(sh, 296, yb + 6, [
        'NOTES',
        '1. Dimensions in millimetres. Do not scale.',
        '2. WL: waterline moored, with the hanging chain (%.1f kg in water).' % E.CHAIN_LOAD,
        '3. Top %.0f mm above the sea (brief 1400 to 1800); green' % (E.CAN_TM[3] - h),
        '    buoy %.0f mm; %.0f mm if the chain breaks.' % (n['above']['green'], n['above']['red_free']),
        '4. Float Ø%d at the waterline (brief 500 ±25).' % (2 * E.FLOAT_R),
        '5. Mass %.1f kg (CAD). GM %.0f mm: stable, %.0f° heel in a gale.' % (m['mass'], m['GM'], n['wind']['heel']),
        '6. Shown red (leaving the harbour). Green (entering):',
        '    green float and lens, cone topmark (%d) for the can (%d).' % (NO['topmark_cone'], NO['topmark_can']),
        '7. All metal 316L stainless or galvanised, with a zinc anode (%d).' % NO['anode'],
        '8. 3 x 20 W solar panels, 12.8 V 40 Ah battery in a locked,',
        '    watertight canister (section on ESP24-GA-02).',
        '9. Load pin (%d) in the shackle: if the pull drops to zero the' % NO['load_pin'],
        '    chain has broken; GNSS tracker sends an alert and position.',
        '10. Each part has its own drawing ESP24-Pnn (nn = item).',
    ], size=2.3)
    finish(sh, 'ESP24-GA-01_general_arrangement', 'ESP 2024 harbour buoy, GA', 'ESP24-GA-01', 'AS SHOWN')


# ------------------------------------------------------------------ GA-02 section through the float
def ga02():
    sh = D.Sheet()
    n = calc()
    h = n['moored']['h']
    s = 1 / 8
    keep = lambda nm, k: E.sub_of(nm) in ('float', 'equipment', 'mast', 'tail')
    items = items_of(keep=keep)
    crop = ((-300, 300), (-300, 300), (E.KEEL[0] - 140, E.M + 620))
    A = section_view(sh, items, 'y', 0, 1, 'front', crop, s, 32, 22, None, hatch_mm=1.6,
                     skip=('bolt', 'rod', 'nut', 'gland', 'panel', 'bracket'))
    ax0, ay0, ax1, ay1 = A.bb()
    wl = A.P((0, 0, h))
    waterline(sh, ax0 - 16, ax1 + 10, wl[1])
    sh.text((ax0 + ax1) / 2, ay1 + 10, 'SECTION A-A ON THE CENTRE LINE, 1:8', size=3, weight='bold')
    # sizes
    a, b = A.P((-E.FLOAT_R, 0, E.FLOAT_BOT)), A.P((E.FLOAT_R, 0, E.FLOAT_BOT))
    D.dim_h(sh, a[0], b[0], ay1 + 4, a[1], 'Ø%d' % (2 * E.FLOAT_R))
    a, b = A.P((-E.FLOAT_R, 0, E.FLOAT_TOP)), A.P((-E.FLOAT_R, 0, E.FLOAT_BOT))
    D.dim_v(sh, a[1], b[1], ax0 - 8, a[0], '%d' % (E.FLOAT_TOP - E.FLOAT_BOT))
    a, b = A.P((-E.WELL_R, 0, E.FLOAT_TOP)), A.P((-E.WELL_R, 0, E.WELL_BOT))
    D.dim_v(sh, a[1], b[1], a[0] + 4, a[0], '%d DEEP' % (E.FLOAT_TOP - E.WELL_BOT))
    a, b = A.P((-E.WELL_R, 0, E.WELL_BOT)), A.P((E.WELL_R, 0, E.WELL_BOT))
    D.dim_h(sh, a[0], b[0], a[1] + 5, a[1], 'Ø%d WELL' % (2 * E.WELL_R))

    def lead(p, dx, dy, text):
        q = A.P(p)
        leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, text, 2.2, 'start' if dx > 0 else 'end')
    lead((E.FLOAT_R - 3, 0, -560), 14, 8, 'MDPE HULL %d WALL (%d)' % (E.WALL, NO['float_hull']))
    lead((200, 0, -350), 26, 10, 'PU FOAM FILL (%d)' % NO['float_foam'])
    lead((E.FENDER_R - 4, 0, E.GROOVE[2] - 30), 16, 10, 'FENDER (%d)' % NO['fender'])
    lead((E.CAN_R - 1, 0, -150), 34, 6, 'STAINLESS CANISTER (%d)' % NO['canister'])
    lead((60, 0, E.EQ_Z + 120), 42, -14, 'CONTROL AND TRACKING UNIT (%d)' % NO['control_unit'])
    q = A.P((0, 0, E.WELL_BOT))
    sh.text(ax0, ay1 + 15, 'The battery (%d) is in front of the cut: see the view on the open hatch.' % NO['battery'],
            size=2.2, anchor='start')
    lead((100, 0, E.LID[1]), 36, -26, 'LOCKED LID (%d), 8 BOLTS (%d)' % (NO['hatch_lid'], NO['hatch_bolt']))
    lead((E.DECK_R - 10, 0, E.DECK[1]), 18, 6, 'DECK PLATE (%d)' % NO['deck_plate'])
    lead((E.KEEL_R - 10, 0, E.KEEL[0]), 22, 8, 'KEEL PLATE (%d)' % NO['keel_plate'])
    lead((0, 0, E.KEEL[0] - 80), 30, 10, 'TAIL Ø88.9 TO BALLAST (%d)' % NO['tail_tube'])
    lead((0, 0, E.M + 560), 24, -10, 'TRIPOD LEG (%d)' % NO['tripod_leg'])
    # view on the open hatch (plan, lid and bolts off), 1:5
    sv = 1 / 5
    eq = [(nm, s_, c) for nm, s_, c in items_of(keep=lambda nm, k: E.sub_of(nm) == 'equipment')
          if not any(t in nm for t in ('lid', 'gland', 'O-ring'))]
    Vd, vox, voy = place(comp(eq), 'plan', sv, 185, 30)
    V = View(sh, None, 'plan', sv, vox, voy, data=Vd)
    vx0, vy0, vx1, vy1 = V.bb()
    sh.text((vx0 + vx1) / 2, vy1 + 18, 'VIEW ON THE OPEN HATCH, LID OFF, 1:5', size=3, weight='bold')
    for p, dx, dy, t in (((-70, -56, 0), -16, 10, 'BATTERY (%d)' % NO['battery']),
                         ((-70, 50, 0), -16, -8, 'CONTROL UNIT (%d)' % NO['control_unit']),
                         ((-E.BOLT_PCD_R * 0.7071, -E.BOLT_PCD_R * 0.7071, 0), -10, 14, 'M10 TAPPED, 8 ON R%d' % E.BOLT_PCD_R)):
        q = V.P(p)
        leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, t, 2.2, 'start' if dx > 0 else 'end')
    # power diagram and specification check
    en = n['energy']
    text_block(sh, 262, 108, [
        'HOW THE 12 V POWER WORKS',
        '3 x 20 W panels (%d) → MPPT charger in the control unit (%d)' % (NO['solar_panel'], NO['control_unit']),
        '→ LiFePO4 12.8 V 40 Ah battery (%d) → 12 V to:' % NO['battery'],
        '   • LED lantern (%d), flashing at night only' % NO['lantern_body'],
        '   • GNSS tracker and LTE-M modem (antenna %d)' % NO['antenna'],
        '   • load pin (%d): chain break alert' % NO['load_pin'],
        'Cables pass through glands (%d) in the lid; none through the hull.' % NO['cable_gland'],
        'Needed %.1f Wh a day; panels make %.1f Wh in December' % (en['need'], en['dec']),
        '(%.1f x more); the battery alone lasts %.0f days.' % (en['ratio'], en['days']),
    ], size=2.3)
    rows = [('Brief', 'This design'),
            ('1400 to 1800 above the sea', '%.0f red, %.0f green' % (n['above']['red'], n['above']['green'])),
            ('Base Ø500 ±25', 'Ø%d, Ø%d over fender' % (2 * E.FLOAT_R, 2 * E.FENDER_R)),
            ('Standard fixings', 'ISO M10, M12, M16, A4-80'),
            ('Green in, red out', 'Coloured all through'),
            ('Alert if the cable breaks', 'Load pin (%d)' % NO['load_pin']),
            ('Tracking if it drifts', 'GNSS + LTE-M reports'),
            ('Renewable 12 V', '3 x 20 W solar, 12.8 V'),
            ('Secure, watertight battery', 'Canister, O-ring, 8 bolts'),
            ('Must not rust', '316L, MDPE, zinc anode'),
            ('Visible, modern', 'Light, topmark, %.0f high' % (E.CAN_TM[3] - h)),
            ('Takes minor impacts', 'EVA fender, foam filled'),
            ('£2000 a buoy', 'About £%s' % format(round(n['costs']['total']), ','))]
    table(sh, 260, 150, (50, 48), rows, h=4.3, size=2.05, title='SPECIFICATION CHECK')
    finish(sh, 'ESP24-GA-02_float_section', 'ESP 2024 float section', 'ESP24-GA-02', 'AS SHOWN')


# ------------------------------------------------------------------ GA-03 details
def ga03():
    sh = D.Sheet()
    n = calc()
    allitems = items_of()
    # B: mooring eye, load pin, shackle, swivel: side view on the eye plate (looking along the pin), 1:3
    sb = 1 / 3
    keys = ('tail tube', 'ballast ring', 'mooring eye', 'load pin', 'bow shackle', 'swivel', 'chain link 1')
    z1 = E.TAIL_BOT + 40
    clip = cq.Solid.makeBox(200, 200, z1 - (E.SW_BOT - 60), cq.Vector(-100, -100, E.SW_BOT - 60))
    part = [(nm, cq.Workplane().add(s_.val().intersect(clip)), c) for nm, s_, c in allitems if nm in keys]
    Bd, box_, boy = place(comp(part), 'right', sb, 60, 30)
    B = View(sh, None, 'right', sb, box_, boy, data=Bd)
    bx0, by0, bx1, by1 = B.bb()
    sh.text((bx0 + bx1) / 2, by1 + 10, 'DETAIL B: MOORING EYE AND LOAD PIN, 1:3', size=3, weight='bold')
    a, b = B.P((0, -45, E.BOT_PLATE[0])), B.P((0, 45, E.BOT_PLATE[0]))
    D.dim_h(sh, a[0], b[0], by0 - 3, a[1], '90 EYE')
    a, b = B.P((0, 45, E.BOT_PLATE[0])), B.P((0, 45, E.EYE_Z))
    D.dim_v(sh, a[1], b[1], bx1 + 5, a[0], '%d' % (E.BOT_PLATE[0] - E.EYE_Z))
    for p, dx, dy, t in (((0, 8, E.PIN_Z), 26, 10, 'LOAD PIN Ø%d (%d)' % (2 * E.PIN_R, NO['load_pin'])),
                         ((0, -30, E.EYE_Z + 20), -18, -10, 'EYE, %d PLATE (%d)' % (E.EYE_T, NO['mooring_eye'])),
                         ((0, -E.SH_R, E.BOW_Z), -18, 8, 'BOW SHACKLE (%d)' % NO['shackle']),
                         ((0, 10, (E.SW_TOP + E.SW_BOT) / 2), 22, 4, 'SWIVEL (%d)' % NO['swivel']),
                         ((0, -80, E.TAIL_BOT + 20), -10, -8, 'BALLAST (%d), CUT AWAY' % NO['ballast'])):
        q = B.P(p)
        leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, t, 2.2, 'start' if dx > 0 else 'end')
    fea = n['fea']
    text_block(sh, 30, by1 + 18, [
        'Designed for the chain breaking load, %d kN: the chain fails first.' % (40),
        'FEA peak %.0f MPa at the hole edge, safety factor %.1f on 316L.' % (fea.get('vm_max', 0), fea.get('sf_min', 0)),
        'Hand check: net section %.0f MPa, pin bearing %.0f MPa.' % (n['eye']['net'], n['eye']['bearing']),
    ], size=2.3)
    # C: watertight hatch, section on y = 0, 1:2
    sc = 1 / 2
    hatch = [it for it in allitems if (E.sub_of(it[0]) in ('float', 'equipment') or it[0].startswith('tripod'))
             and 'tie rod' not in it[0] and 'eye nut' not in it[0]]
    xs = E.BOLT_PCD_R
    C = section_view(sh, hatch, 'y', 0, 1, 'front', ((40, 215), (-215, 215), (E.FLOAT_TOP - 70, E.LID[1] + 30)), sc,
                     165, 40, None, hatch_mm=1.0, skip=('bolt', 'rod', 'nut', 'gland', 'leg'))
    cx0, cy0, cx1, cy1 = C.bb()
    sh.text((cx0 + cx1) / 2, cy1 + 26, 'DETAIL C: WATERTIGHT LOCKED HATCH, 1:2', size=3, weight='bold')
    for p, dx, dy, t in (((E.SEAL_R, 0, E.FLANGE[1]), -4, 24, 'O-RING (%d) IN THE LID GROOVE' % NO['hatch_seal']),
                         ((xs, 0, E.LID[1] + 4), -16, -10, 'TAMPER PROOF M10 (%d), SPECIAL KEY' % NO['hatch_bolt']),
                         ((E.FLANGE[2] - 5, 0, E.FLANGE[0] + 4), 8, 46, 'FLANGE ON THE DECK PLATE (%d)' % NO['canister']),
                         ((E.CAN_R, 0, E.FLOAT_TOP - 40), -16, 16, 'CANISTER WALL %g (%d)' % (E.CAN_T, NO['canister']))):
        q = C.P(p)
        leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, t, 2.2, 'start' if dx > 0 else 'end')
    a, b = C.P((E.FLANGE[2], 0, E.LID[0])), C.P((E.FLANGE[2], 0, E.LID[1]))
    D.dim_v(sh, a[1], b[1], cx1 + 5, a[0], '%d' % E.LID_T)
    # D: lantern and topmark, section on y = 0, 1:5
    sd = 1 / 5
    top = [it for it in allitems if E.sub_of(it[0]) == 'top' or it[0] in ('mast top plate',)]
    Dv = section_view(sh, top, 'y', 0, 1, 'front', ((-200, 200), (-200, 200), (E.TOP_PLATE[0] - 5, E.CAN_TM[3] + 5)), sd,
                      292, 26, None, hatch_mm=1.2, skip=('strut', 'antenna', 'lantern'))
    dx0, dy0, dx1, dy1 = Dv.bb()
    sh.text((dx0 + dx1) / 2, dy1 + 9, 'DETAIL D: LANTERN AND TOPMARK, 1:5', size=3, weight='bold')
    a, b = Dv.P((-E.CAN_TM[0], 0, E.CAN_TM[3])), Dv.P((E.CAN_TM[0], 0, E.CAN_TM[3]))
    D.dim_h(sh, a[0], b[0], dy0 - 4, a[1], 'Ø%d' % (2 * E.CAN_TM[0]))
    a, b = Dv.P((E.CAN_TM[0], 0, E.CAN_TM[3])), Dv.P((E.CAN_TM[0], 0, E.CAN_TM[2]))
    D.dim_v(sh, a[1], b[1], dx1 + 6, a[0], '%d' % (E.CAN_TM[3] - E.CAN_TM[2]))
    for p, dx, dy, t in (((0, 0, E.TM_PLATE[1] + 9), -22, 10, 'GNSS / LTE ANTENNA (%d)' % NO['antenna']),
                         ((0, 0, E.LZ + 70), -26, 14, 'LED LANTERN (%d, %d, %d)' % (NO['lantern_body'], NO['lantern_lens'],
                                                                                 NO['lantern_cap'])),
                         ((E.STRUT[0], 0, E.TOP_PLATE[1] + 120), 14, 8, 'STRUT (%d)' % NO['topmark_strut']),
                         ((-E.CAN_TM[0], 0, E.CAN_TM[3] - 80), -12, -10, 'CAN TOPMARK (%d)' % NO['topmark_can'])):
        q = Dv.P(p)
        leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, t, 2.2, 'start' if dx > 0 else 'end')
    text_block(sh, 280, 160, [
        'NOTES',
        '1. The lid is held by 8 tamper proof screws (%d): only the' % NO['hatch_bolt'],
        '    harbour staff key opens it. The O-ring (%d) seals it (IP68).' % NO['hatch_seal'],
        '2. To change the battery: undo 8 screws, lift the lid with the',
        '    cables, undo the strap (%d), lift the battery out.' % NO['battery_strap'],
        '3. The antenna (%d) is inside the polyethylene topmark,' % NO['antenna'],
        '    which radio waves pass through, safe from birds and knocks.',
        '4. The green buoy has the cone (%d) in place of the can.' % NO['topmark_cone'],
        '5. The load pin (%d) is a strain gauged shackle pin: the' % NO['load_pin'],
        '    control unit reads the pull; zero pull = chain broken.',
    ], size=2.3)
    finish(sh, 'ESP24-GA-03_details', 'ESP 2024 buoy details', 'ESP24-GA-03', 'AS SHOWN', 'Detail drawing')


# ------------------------------------------------------------------ GA-04 Part A design ideas
def ga04():
    sh = D.Sheet()
    n = calc()
    A = comp(items_of())
    B = comp(E.wind_buoy())
    for its, title, x in ((A, 'DESIGN A: SOLAR, POLYETHYLENE FLOAT (PREFERRED)', 16), (B, 'DESIGN B: WIND, STEEL SPHERE', 212)):
        iso_fit(sh, its, x, 18, 80, 140)
        s = 1 / 40
        Fd, fox, foy = place(its, 'front', s, x + 112, 30, hidden=False)
        Fv = View(sh, None, 'front', s, fox, foy, data=Fd)
        b = Fv.bb()
        w = Fv.P((0, 0, n['moored']['h'] if x < 100 else 0))
        waterline(sh, b[0] - 10, b[2] + 10, w[1], label=False)
        sh.text((b[0] + b[2]) / 2, b[3] + 5, 'FRONT, 1:40', size=2.2)
        sh.text(x + 90, 168, title, size=3.4, weight='bold')
    m = n['moored']
    text_block(sh, 16, 176, [
        'Ø%d rotomoulded polyethylene float, foam filled, red or green' % (2 * E.FLOAT_R),
        'all through, with a soft EVA fender. Stainless tripod mast with',
        'three 20 W panels at 120°, LED lantern, topmark with the antenna inside.',
        'Battery and electronics in a locked watertight canister in the float.',
        'Load pin shackle: chain break alert. Ballast tail keeps it upright.',
        'Mass %.0f kg (CAD), top %.0f mm above the sea, GM %.0f mm.' % (m['mass'], n['above']['red'], m['GM']),
    ], size=2.4)
    text_block(sh, 212, 176, [
        'Ø500 painted steel sphere with a lattice tower, a small vertical',
        'axis wind turbine, lantern and topmark. Battery inside the sphere',
        'through a bolted manhole. Simple shapes, cheap to weld.',
        'But: the turbine bearings and blades wear out at sea, it makes',
        'nothing on calm days, and the steel rusts unless it is painted',
        'every year. Hard steel float damages boats that hit it.',
    ], size=2.4)
    rows = [('Requirement', 'Design A', 'Design B'),
            ('Height 1400 to 1800, Ø500', '%.0f, Ø%d' % (n['above']['red'], 2 * E.FLOAT_R), 'About %.0f, Ø500' % B.BoundingBox().zmax),
            ('Renewable 12 V', 'Solar, no moving parts', 'Wind turbine, bearings'),
            ('Energy in December', '%.0f Wh a day (%.1f x need)' % (n['energy']['dec'], n['energy']['ratio']), 'None on calm days'),
            ('No rust', '316L, MDPE, zinc anode', 'Painted steel: rusts'),
            ('Minor impacts', 'Soft fender, foam fill', 'Dents; damages boats'),
            ('Visible', 'Colour all through + light', 'Paint fades'),
            ('Cost a buoy (£2000)', 'About £%s' % format(round(n['costs']['total']), ','), 'About £1,750 + painting'),
            ('Maintenance', 'Anode once a year', 'Paint, turbine bearings')]
    table(sh, 16, 202, (52, 52, 48), rows, h=4.5, size=2.25, title='COMPARISON AGAINST THE BRIEF')
    text_block(sh, 178, 206, [
        'WHY DESIGN A',
        'It meets every point of the brief with no moving parts and nothing that',
        'can rust, so it needs one visit a year. Design B is a little cheaper',
        'to make but costs more to keep, and gives no power on calm winter days.',
    ], size=2.4)
    finish(sh, 'ESP24-GA-04_design_ideas', 'ESP 2024 design ideas A and B', 'ESP24-GA-04', 'AS SHOWN', 'Design sketch',
           'See notes')


# ------------------------------------------------------------------ GA-05 parts list
def ga05():
    sh = D.Sheet()
    items = E.buoy_instances() + E.sinker_items()
    rows = E.bom([nm for nm, k, s_ in items], items)
    # the cone topmark is in the green buoy only
    rows.append(dict(no=NO['topmark_cone'], name=E.PART['topmark_cone']['name'], qty=0, material=E.PART['topmark_cone']['material'],
                     group='top', file=E.PART['topmark_cone']['file'], bought=False))
    rows.sort(key=lambda r: r['no'])
    x, y, hh = 14, 18, 4.15
    wd = (9, 46, 9, 90, 48)
    W = sum(wd)
    sh.text(x, y - 2, 'PARTS LIST: ONE BUOY WITH ITS SINKER', size=3.2, anchor='start', weight='bold')
    lines = [('h', ('Item', 'Part', 'Qty', 'Material and finish', 'Part file / drawing'))]
    g = None
    for r in rows:
        if r['group'] != g:
            g = r['group']
            lines.append(('g', dict(E.GROUPS)[g].upper()))
        q = r['qty'] if r['qty'] else '(1)'
        lines.append(('r', (r['no'], r['name'], q, r['material'], '%s  ESP24-P%02d' % (r['file'], r['no']))))
    yy = y
    for kind, row in lines:
        if kind == 'g':
            sh.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#EEF2F6" stroke="#111" stroke-width="0.25"/>' % (x, yy, W, hh))
            sh.text(x + 1.2, yy + 3.0, row, size=2.1, anchor='start', weight='bold')
        else:
            xx = x
            for c, cell in enumerate(row):
                sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (xx, yy, wd[c], hh))
                txt = str(cell)
                limit = int(wd[c] / 1.08)
                if len(txt) > limit:
                    txt = txt[:limit - 1] + '…'
                sh.text(xx + 1.0, yy + 3.0, txt, size=2.0, anchor='start', weight='bold' if kind == 'h' else 'normal')
                xx += wd[c]
        yy += hh
    total = sum(r['qty'] for r in rows)
    sh.text(x, yy + 4, '%d different parts, %d parts in one buoy and its sinker. (1): item %d replaces item %d on a green buoy.' % (
        len(rows), total, NO['topmark_cone'], NO['topmark_can']), size=2.3, anchor='start')
    # ballooned isometric of the buoy, and the sinker
    bi = E.buoy_instances()
    ox, oy, si = iso_fit(sh, comp([(nm, s_, None) for nm, k, s_ in bi]), 262, 24, 100, 222)
    sh.text(312, 18, 'THE BUOY (RED)', size=3, weight='bold')
    hidden = {'float_foam', 'mounting_plate', 'battery', 'battery_strap', 'control_unit', 'hatch_seal', 'tie_rod', 'keel_bolt',
              'antenna', 'canister'}
    first = {}
    for nm, k, s_ in bi:
        if k not in hidden and k not in first:
            first[k] = centre(s_)
    first['float_hull'] = (-E.FLOAT_R * 0.7, -E.FLOAT_R * 0.7, -400)
    first['fender'] = (-E.FENDER_R * 0.7, -E.FENDER_R * 0.7, E.GROOVE[1] + 40)
    first['tail_tube'] = (0, -E.TAIL_R, -1100)
    first['topmark_can'] = (0, -E.CAN_TM[0], E.CAN_TM[3] - 80)
    marks = []
    for k, c in first.items():
        px, py = iproj(c)
        marks.append((NO[k], ox + px * si, oy - py * si))
    cx = 312
    left = sorted([m for m in marks if m[1] < cx], key=lambda m: m[2])
    right = sorted([m for m in marks if m[1] >= cx], key=lambda m: m[2])
    for col, bxp in ((left, 258), (right, 368)):
        k = len(col)
        for j, (no, px, py) in enumerate(col):
            byp = 26 + j * (196 / max(1, k - 1))
            balloon(sh, px, py, bxp, byp, no)
    # the sinker, small, bottom right
    sk = E.sinker_items()
    sox, soy, ssi = iso_fit(sh, comp([(nm, s_, None) for nm, k, s_ in sk]), 380, 150, 26, 50)
    sh.text(393, 206, 'SINKER', size=2.4, weight='bold')
    for key, bx, by in (('sinker', 404, 214), ('sinker_eye', 404, 156), ('chain_link', 382, 146)):
        nm = [nm for nm, k, s_ in sk if k == key][0]
        px, py = iproj(centre([s_ for n_, k, s_ in sk if n_ == nm][0]))
        balloon(sh, sox + px * ssi, soy - py * ssi, bx, by, NO[key])
    hid = sorted(NO[k] for k in hidden)
    text_block(sh, 14, yy + 10, [
        'Not seen in the view of the buoy: items %s, inside the float, canister, tail flange or topmark' % ', '.join(str(v) for v in hid),
        '(see the section ESP24-GA-02 and the details ESP24-GA-03), and item %d (green buoy only).' % NO['topmark_cone'],
        'Each part has its own STEP file, drawing ESP24-Pnn and Inventor build steps on the ESP 2024 page.',
    ], size=2.3)
    finish(sh, 'ESP24-GA-05_parts_list', 'ESP 2024 parts list', 'ESP24-GA-05', 'NTS', 'Parts list')


# ------------------------------------------------------------------ GA-06 exploded sub-assemblies
def exploded(key):
    d = E.SUB[key]
    return [(nm, k, s_.translate(d['explode'].get(nm, (0, 0, 0)))) for nm, k, s_ in E.sub_items(key)]


def ga06():
    sh = D.Sheet()
    cells = [(14 + c * 97, 16 + r * 116) for r in range(2) for c in range(4)]
    for (x, y), d in zip(cells, E.SUBS):
        items = exploded(d['key'])
        sh.add('<rect class="thin" x="%.2f" y="%.2f" width="95" height="112"/>' % (x, y))
        sh.text(x + 2, y + 5, 'SA%d %s' % (d['no'], d['title'].upper()), size=3, anchor='start', weight='bold')
        sh.text(x + 2, y + 9, d['file'] + ', exploded', size=2.2, anchor='start')
        ox, oy, si = iso_fit(sh, comp([(nm, s_, None) for nm, k, s_ in items]), x + 11, y + 12, 73, 78, d=(-1, -1.3, 0.7))
        cx = x + 47.5
        seen = {}
        for nm, k, s_ in items:
            px, py = iproj(centre(s_))
            seen.setdefault(NO[k], (ox + px * si, oy - py * si))
        left = sorted([(no, p) for no, p in seen.items() if p[0] < cx], key=lambda t: t[1][1])
        right = sorted([(no, p) for no, p in seen.items() if p[0] >= cx], key=lambda t: t[1][1])
        for col, bx in ((left, x + 4.5), (right, x + 90.5)):
            k = len(col)
            for j, (no, (px, py)) in enumerate(col):
                by = (y + 16 + j * (72 / (k - 1))) if k > 1 else min(max(py, y + 16), y + 88)
                balloon(sh, px, py, bx, by, no)
        rows = E.bom([nm for nm, k, s_ in E.sub_items(d['key'])], E.sub_items(d['key']))
        lines = ['%d  %s x%d' % (r['no'], r['name'], r['qty']) for r in rows]
        half = (len(lines) + 1) // 2 if len(lines) > 5 else len(lines)
        for j, t in enumerate(lines):
            col, row = (0, j) if j < half else (1, j - half)
            sh.text(x + 2 + col * 47, y + 96 + row * 2.9, t[:34], size=1.75, anchor='start')
    x, y = cells[7]
    text_block(sh, x + 2, y + 6, [
        'HOW THE BUOY IS BUILT',
        'Each sub-assembly is its own .iam,',
        'made from its parts (numbers are the',
        'items on the parts list, ESP24-GA-05).',
        '',
        'Top level, esp2024_buoy.iam:',
        '  SA1 float',
        '  SA2 equipment canister',
        '  SA3 tail and ballast',
        '  SA4 mast and solar panels',
        '  SA5 lantern and topmark',
        '  SA6 mooring and load pin',
        'Laid on site: SA7 sinker, joined',
        'by the chain (3 x the depth).',
        '',
        'Order of assembly: ESP24-GA-07.',
    ], size=2.3)
    finish(sh, 'ESP24-GA-06_sub_assemblies', 'ESP 2024 sub-assemblies, exploded', 'ESP24-GA-06', 'NTS')


# ------------------------------------------------------------------ GA-07 assembly structure and order
def ga07():
    import esp2024_steps as ST
    sh = D.Sheet()
    x, y = 16, 20
    sh.text(x, y, 'ASSEMBLY STRUCTURE', size=3.2, anchor='start', weight='bold')
    y += 6
    bi = E.buoy_instances()
    sh.text(x, y, 'esp2024_buoy.iam  (%d parts)' % len(bi), size=2.5, anchor='start', weight='bold')
    yy = y + 4.5
    for d in E.SUBS:
        items = E.sub_items(d['key'])
        rows = E.bom([nm for nm, k, s_ in items], items)
        sh.line(x + 2, yy - 4.2, x + 2, yy - 0.8, 'thin')
        sh.line(x + 2, yy - 0.8, x + 5, yy - 0.8, 'thin')
        lab = 'SA%d %s  (%s)' % (d['no'], d['title'], d['file']) + ('  laid on site' if d['key'] == 'sinker' else '')
        sh.text(x + 6, yy, lab, size=2.3, anchor='start', weight='bold')
        yy += 3.2
        for r in rows:
            sh.text(x + 10, yy, '%2d  %s  x%d' % (r['no'], r['name'], r['qty']), size=1.9, anchor='start')
            yy += 2.6
        yy += 1.0
    stages = ST.buoy_steps('red')()
    sh.text(254, 20, 'ORDER OF ASSEMBLY (BUILD STEPS OF THE BUOY)', size=3.2, weight='bold')
    cw, chh = 48, 128
    for i, stg in enumerate(stages):
        cx, cy = 106 + i * (cw + 2), 25
        sh.add('<rect class="thin" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (cx, cy, cw, chh))
        shape = comp([(nm, s_, None) for nm, s_, c_ in stg['parts']])
        iso_fit(sh, shape, cx + 3, cy + 10, cw - 6, chh - 18)
        sh.text(cx + 2, cy + 4.5, '%d. %s' % (i + 1, stg['title']), size=2.4, anchor='start', weight='bold')
        sh.text(cx + cw - 2, cy + chh - 2, '%d parts' % len(stg['parts']), size=2.0, anchor='end')
    text_block(sh, 106, 166, [
        'HOW TO READ THIS SHEET',
        'Left: the assembly structure. The top level assembly, esp2024_buoy.iam, is made from six sub-assemblies,',
        'each its own .iam; the sinker (SA7) is a seventh, laid on the harbour bed and joined by the chain.',
        'Under each sub-assembly are its parts, with the item numbers of the parts list (ESP24-GA-05).',
        'Right: the order the buoy is put together, one picture per build step, with the parts placed so far.',
        '',
        '1. Build each sub-assembly first, from its parts (exploded views on ESP24-GA-06).',
        '2. Place the float and ground it. Lower the equipment canister into the well.',
        '3. Bolt the tail under the keel plate and the mast on the deck plate.',
        '4. Fit the lantern and topmark, then the shackle, load pin, swivel and chain.',
        '5. Check for interference: no parts overlap (checked: docs/ESP 2024/qa/assembly_checks.json).',
        '',
        'Every step, with the Inventor command to use, is on the Build steps tab of each model.',
    ], size=2.4)
    finish(sh, 'ESP24-GA-07_assembly_order', 'ESP 2024 assembly structure and order', 'ESP24-GA-07', 'NTS')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['1', '2', '3', '4', '5', '6', '7']
    for k in which:
        dict(zip('1234567', (ga01, ga02, ga03, ga04, ga05, ga06, ga07)))[k]()
