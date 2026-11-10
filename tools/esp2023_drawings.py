"""ESP 2023 Task 2 drawings: the fully dimensioned A3 sheets for the lock gates, made from the CAD model.

  ESP23-GA-01  General arrangement, 1:50: plan (shut, with the open position chain dotted), elevation from
               downstream, hydrostatic pressure diagram, parts list
  ESP23-GA-02  Gate leaf: elevation with girder levels, plan, section C-C through the girders
  ESP23-GA-03  Hinge, seal and mitre details, 1:10 and 1:20
  ESP23-GA-04  Part A design ideas: design A (mitre gates) and design B (lift gate), with notes
  ESP23-GA-05  Parts list (bill of materials) for all 41 parts, with a ballooned view of one leaf

Output: docs/ESP 2023/drawings/ESP23-GA-0n_*.svg and .png.
Run from the repository root:  python3 tools/esp2023_drawings.py
"""
import math, os, sys
import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import esp2023 as E  # noqa: E402
import drawings as D  # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Curve  # noqa: E402
from OCP.GCPnts import GCPnts_QuasiUniformDeflection  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'ESP 2023', 'drawings')
OWNER, DATE = 'Lock Restoration Ltd', '2026-11-10'
EXTRA_STYLE = ('<style>.ph{fill:none;stroke:#555;stroke-width:0.25;stroke-dasharray:6,1.2,1,1.2,1,1.2}'
               '.wat{fill:none;stroke:#1565D8;stroke-width:0.35}.watf{fill:#DCEBFB;stroke:#1565D8;stroke-width:0.3}'
               '.note{font-size:2.6px}.box{fill:none;stroke:#111;stroke-width:0.3}.tbl{fill:none;stroke:#111;stroke-width:0.25}'
               '.lead{fill:none;stroke:#111;stroke-width:0.2}</style>')


def _pintle_fea():
    import json
    f = os.path.join(ROOT, 'docs', 'ESP 2023', 'fea', 'esp2023_p20_bottom_pintle.json')
    if os.path.exists(f):
        r = json.load(open(f))['results']
        return r['vm_max'], r['sf_min']
    return 21.0, 11.0


PINTLE_FEA = _pintle_fea()


def comp(items):
    return cq.Compound.makeCompound([w.val() for n, w, c in items])


class View:
    """A projected view placed on the sheet: model point -> paper point."""

    def __init__(self, sh, shape, view, s, ox, oy, hidden=True, label=None, data=None):
        self.view, self.s, self.ox, self.oy = view, s, ox, oy
        self.data = data or D.view_data(shape, view, hidden)
        D.draw_view(sh, self.data, ox, oy, s, label)

    def P(self, p):
        x, y = D.proj(p, self.view)
        return self.ox + x * self.s, self.oy - y * self.s

    def bb(self):
        x0, y0, x1, y1 = self.data['bb']
        return self.ox + x0 * self.s, self.oy - y1 * self.s, self.ox + x1 * self.s, self.oy - y0 * self.s


def place(shape, view, s, left, top, hidden=True):
    """Origin offsets that put the view's top left corner at (left, top) on the paper."""
    data = D.view_data(shape, view, hidden)
    x0, y0, x1, y1 = data['bb']
    return data, left - x0 * s, top + y1 * s


def phantom(sh, shape, view, ox, oy, s):
    vis, hid = D.hlr(shape, view, hidden=False)
    sh.path(vis, 'ph', ox, oy, s)


def text_block(sh, x, y, lines, size=2.6, gap=1.45, weight='normal'):
    for k, t in enumerate(lines):
        sh.text(x, y + k * size * gap, t, size=size, anchor='start', weight=weight)


def leader(sh, x0, y0, x1, y1, label, size=2.6, anchor='start'):
    D.arrow(sh, x0, y0, math.degrees(math.atan2(y0 - y1, x0 - x1)), 2.2)
    sh.add('<polyline class="lead" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f"/>' % (
        x0, y0, x1, y1, x1 + (6 if anchor == 'start' else -6), y1))
    sh.text(x1 + (7 if anchor == 'start' else -7), y1 + 0.9, label, size=size, anchor=anchor)


def dim_aligned(sh, p0, p1, off, val):
    """Dimension between two paper points, offset square to the line by off (paper mm)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy * off, ux * off
    a0, a1 = (p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny)
    sgn = 1 if off > 0 else -1
    ex, ey = nx / abs(off) * 2, ny / abs(off) * 2
    for p, a in ((p0, a0), (p1, a1)):
        sh.line(p[0] + ex * 0.75, p[1] + ey * 0.75, a[0] + ex, a[1] + ey, 'dim')
    sh.line(a0[0], a0[1], a1[0], a1[1], 'dim')
    ang = math.degrees(math.atan2(dy, dx))
    D.arrow(sh, a0[0], a0[1], ang + 180)
    D.arrow(sh, a1[0], a1[1], ang)
    mx, my = (a0[0] + a1[0]) / 2 - uy * 1.6 * sgn, (a0[1] + a1[1]) / 2 + ux * 1.6 * sgn
    rot = ang if -90 < ang <= 90 else ang + 180
    sh.add('<text x="%.2f" y="%.2f" font-size="3" text-anchor="middle" transform="rotate(%.1f %.2f %.2f)">%s</text>' % (
        mx, my, rot, mx, my, val))


def arc_dim(sh, c, r, a0, a1, label, lx, ly):
    """Angle dimension: an arc of radius r (paper mm) about c from a0 to a1 degrees (paper angles, y down)."""
    p0 = (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)))
    p1 = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
    large = 1 if abs(a1 - a0) > 180 else 0
    sweep = 1 if a1 > a0 else 0
    sh.add('<path class="dim" d="M%.2f,%.2f A%.2f,%.2f 0 %d %d %.2f,%.2f"/>' % (p0[0], p0[1], r, r, large, sweep, p1[0], p1[1]))
    D.arrow(sh, p0[0], p0[1], a0 - 90 if sweep else a0 + 90, 2)
    D.arrow(sh, p1[0], p1[1], a1 + 90 if sweep else a1 - 90, 2)
    sh.text(lx, ly, label, size=3)


def cut_loops(half, axis, value, view):
    """Closed loops of the planar faces of `half` lying on the cutting plane axis = value, projected into view."""
    k = 'xyz'.index(axis)
    loops = []
    for f in half.Faces():
        if f.geomType() != 'PLANE':
            continue
        n, c = f.normalAt(), f.Center()
        if abs(abs([n.x, n.y, n.z][k]) - 1) > 1e-3 or abs([c.x, c.y, c.z][k] - value) > 1e-3:
            continue
        for w in f.Wires():
            pts = []
            for e in w.Edges():
                ad = BRepAdaptor_Curve(e.wrapped)
                gp = GCPnts_QuasiUniformDeflection(ad, 0.05, ad.FirstParameter(), ad.LastParameter())
                seg = [D.proj((gp.Value(i).X(), gp.Value(i).Y(), gp.Value(i).Z()), view) for i in range(1, gp.NbPoints() + 1)]
                pts.append(seg)
            loop = list(pts[0])
            rest = pts[1:]
            while rest:
                end = loop[-1]
                j = min(range(len(rest)), key=lambda q: min(math.dist(end, rest[q][0]), math.dist(end, rest[q][-1])))
                seg = rest.pop(j)
                if math.dist(end, seg[-1]) < math.dist(end, seg[0]):
                    seg = seg[::-1]
                loop.extend(seg[1:])
            loop.append(loop[0])
            loops.append(loop)
    return loops


def section_view(sh, items, axis, value, keep, view, crop, s, left, top, label, hatch_mm=1.6, skip=()):
    """Cut the parts on the plane axis = value, keep the side keep (+1 or -1), crop to the box crop
    ((x0, x1), (y0, y1), (z0, z1)) and draw it with hatching. Returns the View."""
    k = 'xyz'.index(axis)
    lo = [crop[i][0] for i in range(3)]
    hi = [crop[i][1] for i in range(3)]
    if keep > 0:
        lo[k] = value
    else:
        hi[k] = value
    cb = cq.Solid.makeBox(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], cq.Vector(*lo))
    pieces, hatched = [], []
    for n, w, c in items:
        try:
            piece = w.val().intersect(cb)
        except Exception:
            continue
        if piece.Volume() < 1:
            continue
        pieces.append(piece)
        if not any(t in n for t in skip):
            hatched.append(piece)
    shape = cq.Compound.makeCompound(pieces)
    data, ox, oy = place(shape, view, s, left, top)
    data = dict(data)
    data['hid'] = []
    for j, piece in enumerate(hatched):
        loops = cut_loops(piece, axis, value, view)
        if loops:
            sh.path(D.hatch(loops, hatch_mm / s, 1 if j % 2 == 0 else -1), 'hat', ox, oy, s)
    return View(sh, None, view, s, ox, oy, label=label, data=data)


def parts_list(sh, x, y, rows, widths=(8, 52, 9, 50), title='PARTS LIST'):
    sh.text(x, y - 1.5, title, size=3, anchor='start', weight='bold')
    h = 5
    heads = ('Item', 'Part', 'Qty', 'Material and finish')
    allrows = [heads] + rows
    W = sum(widths)
    sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (x, y, W, h * len(allrows)))
    for r, row in enumerate(allrows):
        yy = y + r * h
        if r:
            sh.line(x, yy, x + W, yy, 'thin')
        xx = x
        for c, cell in enumerate(row):
            sh.text(xx + 1.2, yy + 3.5, str(cell), size=2.3, anchor='start', weight='bold' if r == 0 else 'normal')
            xx += widths[c]
            if c < len(row) - 1:
                sh.line(xx, y, xx, y + h * len(allrows), 'thin')
    return y + h * len(allrows)


def finish(sh, name, title, number, scale, doctype='Assembly drawing', material='See parts list'):
    sh.add(EXTRA_STYLE)
    D.frame(sh, title, number, scale, 'third', material, doctype, OWNER, DATE)
    D.save(sh, name, OUT)
    print('drew', name)


# ------------------------------------------------------------------ GA-01 general arrangement
def _range(group):
    nos = [p['no'] for p in E.PARTS if p['group'] == group]
    return '%d-%d' % (nos[0], nos[-1]) if len(nos) > 1 else str(nos[0])


GA_ROWS = [
    (_range('frame'), 'Gate leaf frame, welded (L and R)', 2, 'S355 steel; blast cleaned, epoxy painted'),
    (_range('leaf'), 'Fenders, walkway, seals, bush, paddle', '2 sets', 'Oak, galvanised steel, EPDM, bronze, 316'),
    (_range('hinge'), 'Pintle, collar, anchors, encoder', '2 sets', '316 stainless, bronze, S355 galvanised'),
    (_range('drive'), 'Electric actuator, pedestal, pins', '2 sets', '1300 stroke, 20 kN, IP68, mains'),
    (_range('chamber'), 'Chamber, covers, panel, CCTV, call point', '2 sets', 'Precast concrete, GRP, stainless'),
    (_range('civil'), 'Cill', 1, 'Precast concrete C40/50'),
]


def ga01():
    sh = D.Sheet()
    s = 1 / 50
    shut = [it for it in E.lock_gates(0) if it[0] != 'cill']      # the cill is shown on GA-03; here it is the CILL line
    no_mast = [it for it in shut if 'CCTV' not in it[0] and 'call point' not in it[0]]
    allc = comp(shut)
    # plan, top left
    P_data, pox, poy = place(allc, 'plan', s, 30, 22)
    walls_y = (-450, 3500)
    P = View(sh, None, 'plan', s, pox, poy, label=None, data=P_data)
    moving = [it for it in E.lock_gates(E.OPEN_DEG) if E.group_of(it[0]) != 'fixed']
    phantom(sh, comp(moving), 'plan', pox, poy, s)
    # lock walls (thin lines) with the quoin recess
    for sx in (-1, 1):
        a, b = P.P((sx * E.OPENING / 2, walls_y[0], 0)), P.P((sx * E.OPENING / 2, -350, 0))
        sh.line(a[0], a[1], b[0], b[1], 'vis')
        a, b = P.P((sx * E.OPENING / 2, 2900, 0)), P.P((sx * E.OPENING / 2, walls_y[1], 0))
        sh.line(a[0], a[1], b[0], b[1], 'vis')
        lx = P.P((sx * E.OPENING / 2, 1700, 0))
        sh.text(lx[0] - sx * 1.5, lx[1], 'LOCK WALL', size=2.2, anchor='middle', rot=-90)
    x0, y0, x1, y1 = P.bb()
    sh.text((x0 + x1) / 2, y1 + 22, 'PLAN (gates shut; open position chain dotted)', size=3.0, weight='bold')
    # plan dimensions
    a, b = P.P((-E.OPENING / 2, -450, 0)), P.P((E.OPENING / 2, -450, 0))
    D.dim_h(sh, a[0], b[0], y1 + 6, a[1], '4200 OPENING')
    a, b = P.P((-E.PIV, 0, 0)), P.P((E.PIV, 0, 0))
    D.dim_h(sh, a[0], b[0], y1 + 14, a[1], '%.0f PIVOT CENTRES' % (2 * E.PIV))
    p0 = P.P((-E.PIV, 0, 0))
    p1 = P.P((-E.GAP, E.LEAF * E.S, 0))
    dim_aligned(sh, p0, p1, -16, '2460 LEAF')
    # mitre angle
    c = P.P((E.PIV, 0, 0))
    sh.line(c[0] - 2, c[1], c[0] - 32, c[1], 'thin')
    arc_dim(sh, c, 26, 180, 180 + math.degrees(E.THETA), '18.4° (1 IN 3)', c[0] - 22, c[1] + 5)
    cl = P.P((-E.PIV, 0, 0))
    arc_dim(sh, cl, 15, -math.degrees(E.THETA), -90, '71.6° SWING', cl[0] - 12, cl[1] - 17)
    # centre line of the lock
    a, b = P.P((0, -700, 0)), P.P((0, 3500, 0))
    sh.line(a[0], a[1], b[0], b[1], 'ctr')
    sh.text(b[0] + 1, b[1] + 2, 'CL LOCK', size=2.4, anchor='start')
    up = P.P((0, 2500, 0))
    D.arrow(sh, up[0], up[1] - 6, -90, 2.5)
    sh.line(up[0], up[1] + 4, up[0], up[1] - 6, 'thin')
    sh.text(up[0] + 2, up[1] + 1, 'FLOW / UPSTREAM (LOCK CHAMBER SIDE)', size=2.4, anchor='start')
    # chamber size
    ch = P.P((E.PIV + E.CHAMBER[0], E.CHAMBER[2], 0)), P.P((E.PIV + E.CHAMBER[1], E.CHAMBER[3], 0))
    D.dim_h(sh, ch[0][0], ch[1][0], ch[1][1] - 6, ch[1][1], '%d' % (E.CHAMBER[1] - E.CHAMBER[0]))
    D.dim_v(sh, ch[1][1], ch[0][1], ch[1][0] + 8, ch[1][0], '%d' % (E.CHAMBER[3] - E.CHAMBER[2]))

    # elevation from downstream, below the plan (third angle)
    el = comp(no_mast)
    top = y1 + 30
    F_data, fox, foy = place(el, 'front', s, 30, top)
    fox = pox  # plan and elevation share x, so they line up
    F = View(sh, None, 'front', s, fox, foy, label=None, data=F_data)
    fx0, fy0, fx1, fy1 = F.bb()
    sh.text((fx0 + fx1) / 2, fy1 + 7, 'ELEVATION FROM DOWNSTREAM (CCTV masts and call points left off)', size=3.0, weight='bold')
    a, b = F.P((-E.PIV - 600, 0, 0)), F.P((E.PIV + 600, 0, 0))
    sh.line(a[0], a[1], b[0], b[1], 'vis')
    sh.text(b[0] + 1, b[1] + 1, 'CILL', size=2.4, anchor='start')
    za, zb = F.P((-E.PIV, 0, 0)), F.P((-E.PIV, 0, E.HEIGHT))
    D.dim_v(sh, zb[1], za[1], za[0] - 12, za[0] - 4, '6000')
    zc = F.P((-E.PIV, 0, E.HEIGHT + 1100))
    D.dim_v(sh, zc[1], zb[1], za[0] - 12, za[0] - 4, '1100')
    # water levels
    for z, lab in ((E.HEAD_MAX, 'MAX WATER (5.5 m HEAD)'), (E.HEAD_MIN, 'MIN WATER (2.0 m HEAD)')):
        a, b = F.P((-E.PIV - 200, 0, z)), F.P((E.PIV + 1000, 0, z))
        sh.add('<line class="wat" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke-dasharray="3,1.5"/>' % (a[0], a[1], b[0], b[1]))
        sh.add('<polygon class="watf" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f"/>' % (b[0] - 3, a[1] - 2.4, b[0] - 1, a[1] - 2.4, b[0] - 2, a[1]))
        sh.text(b[0] + 1, b[1] - 1, lab, size=2.3, anchor='start')
    # hydrostatic pressure diagram beside the elevation
    base = F.P((E.PIV + 2600, 0, 0))
    topw = F.P((E.PIV + 2600, 0, E.HEAD_MAX))
    pw = 14  # paper mm for 53.96 kPa
    sh.add('<polygon class="watf" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f"/>' % (topw[0], topw[1], base[0], base[1], base[0] + pw, base[1]))
    for k in range(1, 6):
        yk = topw[1] + (base[1] - topw[1]) * k / 6
        sh.line(base[0], yk, base[0] + pw * k / 6, yk, 'thin')
        D.arrow(sh, base[0], yk, 180, 1.5)
    sh.text(base[0] + pw / 2, base[1] + 4, 'p = ρgh = 53.96 kPa', size=2.4)
    zr = F.P((E.PIV + 2600, 0, E.HEAD_MAX / 3))
    D.arrow(sh, base[0] - 0.5, zr[1], 180, 2.8)
    sh.line(base[0] - 0.5, zr[1], base[0] + pw + 4, zr[1], 'vis')
    text_block(sh, base[0] + 3, topw[1] - 14, ['HYDROSTATIC', 'PRESSURE', 'F = ½ρgh² = 148 kN/m', 'acts h/3 = 1.83 m', 'above the cill'], size=2.3)
    a = F.P((E.PIV - 400, 0, E.TOP))
    leader(sh, a[0], a[1] + 6, a[0] + 22, a[1] - 10, 'WALKWAY (10)', 2.3)

    # isometric, right column
    iso_shape = comp(shut)
    D.ISO_DIR['d'] = (-1, -1.3, 0.9)
    I = D.view_data(iso_shape, 'iso', hidden=False)
    iw, ih = I['bb'][2] - I['bb'][0], I['bb'][3] - I['bb'][1]
    si = min(120 / iw, 78 / ih)
    ix, iy = 287 - I['bb'][0] * si, 20 + I['bb'][3] * si
    D.draw_view(sh, I, ix, iy, si)
    sh.text(347, 104, 'ISOMETRIC VIEW (NOT TO SCALE)', size=3.0, weight='bold')
    yb = parts_list(sh, 287, 114, [list(r) for r in GA_ROWS], widths=(10, 52, 10, 48), title='PARTS (FULL LIST ON ESP23-GA-05)')
    text_block(sh, 287, yb + 6, [
        'NOTES',
        '1. Dimensions in millimetres. Levels are above the cill. Do not scale.',
        '2. Gates hold a head of 2.0 to 5.5 m; water on the upstream (chamber) side.',
        '3. Each leaf has its own actuator, position encoder and control panel, so the',
        '    gates work independently. A gate only opens once its paddles have levelled',
        '    the water either side.',
        '4. Leaf %.1f t each: lifted out by mobile crane on its two lifting lugs (7),' % (E.leaf_mass()[0] / 1000),
        '    after the anchor collar (22) is released.',
        '5. Chamber cover panels (35) shown fitted. Hydrostatic calculations: see the',
        '    ESP23 calculation sheets. Every part has its own drawing ESP23-Pnn.',
    ], size=2.3)
    finish(sh, 'ESP23-GA-01_general_arrangement', 'ESP 2023 lock gates, GA', 'ESP23-GA-01', '1:50')


# ------------------------------------------------------------------ GA-02 gate leaf
def ga02():
    sh = D.Sheet()
    items = E.gate_leaf()
    leaf = comp(items)
    s = 1 / 50
    # elevation (from downstream: front view)
    F_data, fox, foy = place(leaf, 'front', s, 40, 30)
    F = View(sh, None, 'front', s, fox, foy, data=F_data)
    fx0, fy0, fx1, fy1 = F.bb()
    sh.text((fx0 + fx1) / 2, fy1 + 20, 'ELEVATION FROM DOWNSTREAM, 1:50', size=3, weight='bold')
    # girder levels, chained from the cill on the left
    zs = [0] + E.GIRDERS + [E.HEIGHT]
    xk = fx0 - 8
    for a, b in zip(zs[:-1], zs[1:]):
        pa, pb = F.P((-E.HEEL_R, 0, a)), F.P((-E.HEEL_R, 0, b))
        D.dim_v(sh, pb[1], pa[1], xk, fx0 - 1, '%d' % (b - a))
    sh.text(xk - 8, (fy0 + fy1) / 2, 'GIRDER CENTRES FROM CILL', size=2.4, rot=-90)
    pa, pb = F.P((-E.HEEL_R, 0, 0)), F.P((-E.HEEL_R, 0, E.HEIGHT))
    D.dim_v(sh, pb[1], pa[1], xk - 14, fx0 - 1, '6000')
    # lengths along the bottom
    yb = fy1 + 6
    for (u0, u1, lab, dy) in ((0, E.HEEL_BOX, '400', 0), (E.HEEL_BOX, E.STIFFENERS[0][0], '580', 0),
                              (E.STIFFENERS[0][1], E.STIFFENERS[1][0], '570', 0), (E.STIFFENERS[1][1], E.LEAF - E.MITRE_BOX, '580', 0),
                              (0, E.LEAF, '2460 PIVOT TO MITRE (ON CL)', 8)):
        a, b = F.P((u0, 0, 0)), F.P((u1, 0, 0))
        D.dim_h(sh, a[0], b[0], yb + dy, fy1, lab)
    leader(sh, *F.P((E.LEAF - E.MITRE_BOX + 20, 0, 6550)), F.P((E.LEAF, 0, 6900))[0] + 10, F.P((E.LEAF, 0, 6900))[1], 'HANDRAIL 48.3 DIA, 1100 HIGH', 2.3)
    p = F.P((900, 0, 150))
    leader(sh, p[0], p[1] - 1, p[0] + 54, p[1] - 22, 'GIRDER: WEB 20, FLANGE 200 x 20', 2.3)
    p = F.P((990, 0, 3000))
    leader(sh, p[0], p[1], p[0] + 58, p[1] + 6, 'STIFFENER 15 PLATE', 2.3)
    p = F.P((0, 0, 5925))
    leader(sh, p[0], p[1], p[0] - 4, p[1] - 14, 'JOURNAL 200 DIA', 2.3, anchor='end')
    # plan, 1:25, top right
    s2 = 1 / 25
    P_data, pox, poy = place(leaf, 'plan', s2, 165, 30)
    P = View(sh, None, 'plan', s2, pox, poy, data=P_data)
    px0, py0, px1, py1 = P.bb()
    sh.text((px0 + px1) / 2, py1 + 16, 'PLAN, 1:25', size=3, weight='bold')
    a, b = P.P((0, -E.T2, 0)), P.P((0, E.T2, 0))
    D.dim_v(sh, b[1], a[1], px0 - 6, a[0], '450')
    a, b = P.P((E.HEEL_BOX, E.T2, 0)), P.P((E.HEEL_BOX, E.T2 + 150, 0))
    D.dim_v(sh, b[1], a[1], px1 + 6, P.P((E.LEAF, 0, 0))[0], '150')
    a, b = P.P((-E.HEEL_R, 0, 0)), P.P((E.LEAF, 0, 0))
    D.dim_h(sh, a[0], b[0], py1 + 7, py1, '%d' % (E.LEAF + E.HEEL_R))
    c = P.P((0, 0, 0))
    leader(sh, c[0] - 6, c[1] + 2, c[0] - 4, c[1] + 12, 'HEEL POST R225, 25 PLATE', 2.3, anchor='end')
    m = P.P((E.LEAF, 0, 0))
    leader(sh, m[0], m[1], m[0] + 6, m[1] - 9, 'MITRE FACE 1 IN 3', 2.3)
    f = P.P((1500, E.T2 + 150, 0))
    leader(sh, f[0], f[1], f[0] + 10, f[1] - 9, 'OAK FENDERS 150 x 200 (CHAMBER FACE)', 2.3)
    # section C-C at u = 700 through the bottom girders, 1:10
    C = section_view(sh, items, 'x', 700, 1, 'left', ((-400, 3000), (-700, 700), (-10, 950)), 1 / 10, 175, 105,
                     None, hatch_mm=1.2)
    cx0, cy0, cx1, cy1 = C.bb()
    sh.text((cx0 + cx1) / 2, cy1 + 16, 'SECTION C-C (BOTTOM OF LEAF), 1:10', size=3, weight='bold')
    for z0, z1, lab, dx in ((0, 50, '50', 6), (0, 150, '150', 13), (150, 800, '650 GIRDER CENTRES', 13)):
        a, b = C.P((700, -E.T2, z0)), C.P((700, -E.T2, z1))
        D.dim_v(sh, b[1], a[1], cx1 + dx, a[0], lab)
    a, b = C.P((700, -E.T2, 0)), C.P((700, E.T2, 0))
    D.dim_h(sh, a[0], b[0], cy1 + 6, cy1, '450')
    p = C.P((700, E.T2 - 6, 470))
    leader(sh, p[0], p[1], p[0] - 30, p[1] - 22, 'SKIN PLATE 12', 2.3, anchor='end')
    p = C.P((700, 0, 800))
    leader(sh, p[0], p[1], p[0] + 14, p[1] - 22, 'GIRDER WEB 20', 2.3)
    p = C.P((700, -E.T2 + 10, 150))
    leader(sh, p[0], p[1], p[0] + 28, p[1] + 22, 'FLANGE 200 x 20', 2.3)
    p = C.P((700, E.T2 - 40, 25))
    leader(sh, p[0], p[1], p[0] - 30, p[1] + 10, 'CILL SEAL, EPDM 85 x 50', 2.3, anchor='end')
    sh.text(cx0 - 2, cy0 - 3, '← UPSTREAM (WATER)', size=2.3, anchor='end')
    sh.text(cx1 + 2, cy0 - 3, 'DOWNSTREAM →', size=2.3, anchor='start')
    # cutting plane C-C on the plan
    a, b = P.P((700, -E.T2 - 60, 0)), P.P((700, E.T2 + 200, 0))
    sh.line(a[0], a[1], b[0], b[1], 'cut')
    for q in (a, b):
        sh.text(q[0] + 2.5, q[1] + (3 if q is a else -1), 'C', size=4, weight='bold')
    text_block(sh, 287, 175, [
        'NOTES',
        '1. Welded S355 steel (EN 10025), all welds continuous fillet, 6 mm minimum.',
        '2. Blast clean to Sa 2.5, three coat epoxy paint, 300 microns, black and white.',
        '3. Leaf mass %.1f t. Centre of gravity %.0f mm from the pivot.' % (E.leaf_mass()[0] / 1000, E.leaf_mass()[1]),
        '4. Girders closer together near the bottom, where the water pressure is greatest.',
        '5. Bottom panel 580 x 630 x 12: bending stress 39 MPa (hand), 34 MPa',
        '    von Mises (FEA). Safety factor 10 on S355.',
        '6. All steel and oak can be recycled or reused at the end of life.',
    ], size=2.3)
    finish(sh, 'ESP23-GA-02_gate_leaf', 'ESP 2023 gate leaf', 'ESP23-GA-02', 'AS SHOWN', 'Detail drawing',
           'S355 steel, see notes')


# ------------------------------------------------------------------ GA-03 details
def ga03():
    sh = D.Sheet()
    right = [it for it in E.lock_gates(0) if it[0].startswith('right') or it[0] == 'mitre seal']
    left = [it for it in E.lock_gates(0) if it[0].startswith('left') or it[0] == 'mitre seal']
    s = 1 / 10
    X = E.PIV
    # D: bottom pintle, section on the pivot (plane y = 0, looking from downstream)
    Dv = section_view(sh, right, 'y', 0, 1, 'front', ((X - 450, X + 450), (-400, 400), (-90, 420)), s, 70, 30, None,
                      skip=('bottom pintle', 'anchor bolt'))
    x0, y0, x1, y1 = Dv.bb()
    sh.text((x0 + x1) / 2, y1 + 16, 'DETAIL D: BOTTOM PINTLE (SECTION ON PIVOT), 1:10', size=3, weight='bold')
    a, b = Dv.P((X - 75, 0, 200)), Dv.P((X + 75, 0, 200))
    sh.text((a[0] + b[0]) / 2, a[1] - 2, 'Ø150', size=2.6)
    a, b = Dv.P((X - 300, 0, -80)), Dv.P((X + 300, 0, -80))
    D.dim_h(sh, a[0], b[0], y1 + 7, y1, '600')
    a, b = Dv.P((X + 300, 0, -80)), Dv.P((X + 300, 0, 0))
    D.dim_v(sh, b[1], a[1], x1 + 6, a[0], '80')
    a, b = Dv.P((X + 75, 0, 0)), Dv.P((X + 75, 0, 280))
    D.dim_v(sh, b[1], a[1], x1 + 14, a[0], '280')
    p = Dv.P((X - 78, 0, 270))
    leader(sh, p[0], p[1], x0 - 4, p[1] - 8, 'BRONZE BUSH Ø190/Ø150 (15)', 2.3, anchor='end')
    p = Dv.P((X - 300, 0, -40))
    leader(sh, p[0], p[1], x0 - 4, p[1] + 8, '316 STAINLESS PINTLE (20)', 2.3, anchor='end')
    sh.text(x0 - 11, p[1] + 12.5, '4 x M24 ANCHORS (21) INTO THE CILL (41)', size=2.3, anchor='end')
    # E: top anchor collar, section on the pivot
    Ev = section_view(sh, right, 'y', 0, 1, 'front', ((X - 450, X + 950), (-400, 400), (5650, 6200)), s, 160, 22, None)
    x0, y0, x1, y1 = Ev.bb()
    sh.text((x0 + x1) / 2, y1 + 16, 'DETAIL E: TOP ANCHOR COLLAR (SECTION ON PIVOT), 1:10', size=3, weight='bold')
    a, b = Ev.P((X - 100, 0, 6000)), Ev.P((X + 100, 0, 6000))
    D.dim_h(sh, a[0], b[0], y0 - 5, a[1], 'Ø200')
    a, b = Ev.P((X + 180, 0, 5870)), Ev.P((X + 900, 0, 5870))
    D.dim_h(sh, a[0], b[0], y1 + 7, y1, '720 ARM TO ANCHOR PLATE (24)')
    p = Ev.P((X - 180, 0, 5920))
    leader(sh, p[0], p[1], p[0] + 1, y0 - 6, 'COLLAR Ø360 (22), BRONZE BUSH Ø240/Ø200 (23)', 2.3, anchor='end')
    p = Ev.P((X + 50, 0, 6080))
    leader(sh, p[0], p[1], p[0] + 26, p[1] - 8, 'POSITION ENCODER (26) ON BRACKET (25)', 2.3)
    # F: mitre joint, plan section at z = 3000
    Fv = section_view(sh, right + left, 'z', 3000, -1, 'plan', ((-450, 450), (380, 1200), (2700, 3000)), s, 30, 140, None)
    x0, y0, x1, y1 = Fv.bb()
    sh.text((x0 + x1) / 2, y1 + 16, 'DETAIL F: MITRE (PLAN SECTION AT 3.0 m), 1:10', size=3, weight='bold')
    a, b = Fv.P((-15, 700, 3000)), Fv.P((15, 700, 3000))
    leader(sh, (a[0] + b[0]) / 2 + 1, a[1] + 2, x1 + 4, a[1] + 14, 'MITRE SEAL, EPDM 30 x 80', 2.3)
    sh.text(x1 + 11, a[1] + 18, '(COMPRESSED BY THE WATER)', size=2.3, anchor='start')
    p = Fv.P((-200, 640, 3000))
    leader(sh, p[0], p[1], x0 + 30, y1 + 6, 'HOLLOW MITRE POST, 25 PLATE', 2.3)
    sh.text((x0 + x1) / 2, y0 - 3, 'UPSTREAM (WATER)', size=2.3)
    # G: heel post in the hollow quoin, plan section at 3.0 m, 1:20
    Gv = section_view(sh, right, 'z', 3000, -1, 'plan', ((X - 700, X + 400), (-420, 900), (2700, 3000)), 1 / 20, 200, 140, None)
    x0, y0, x1, y1 = Gv.bb()
    sh.text((x0 + x1) / 2, y1 + 16, 'DETAIL G: HEEL POST IN QUOIN (PLAN AT 3.0 m), 1:20', size=3, weight='bold')
    c = Gv.P((X, 0, 3000))
    r = (E.HEEL_R + 30) / 20
    sh.add('<path class="vis" d="M%.2f,%.2f A%.2f,%.2f 0 0 1 %.2f,%.2f"/>' % (c[0] + 2, c[1] - r, r, r, c[0] + 2, c[1] + r))
    leader(sh, c[0] + r + 1, c[1] - 3, c[0] + r + 14, c[1] - 14, 'HOLLOW QUOIN (GRANITE, EXISTING)', 2.3)
    p = Gv.P((X + E.HEEL_R + 15, 0, 3000))
    leader(sh, p[0], p[1] + 1, p[0] + 12, p[1] + 12, 'HEEL SEAL, EPDM 30 x 80', 2.3)
    a, b = Gv.P((X - 225, 0, 3000)), Gv.P((X + 225, 0, 3000))
    sh.text(c[0], c[1] + r + 4, 'R225', size=2.4)
    text_block(sh, 287, 195, [
        'NOTES',
        '1. Hinges are the critical parts: stainless pintle and bronze bush do not',
        '    corrode together, and the bush is replaced at each lift out.',
        '2. Pintle loads: 87.2 kN down (leaf weight) and 19.5 kN sideways.',
        '    FEA peak %.1f MPa at the root fillet, safety factor %.1f.' % PINTLE_FEA,
        '3. Water pushes the leaves into the mitre and the quoins, so the seals',
        '    tighten as the head rises: no water is lost through the gates.',
        '4. EPDM seals are bolted on in lengths and replaced without welding.',
    ], size=2.3)
    finish(sh, 'ESP23-GA-03_hinge_and_seal_details', 'ESP 2023 hinge and seal details', 'ESP23-GA-03', 'AS SHOWN',
           'Detail drawing')


# ------------------------------------------------------------------ GA-04 Part A design ideas
def ga04():
    sh = D.Sheet()
    D.ISO_DIR['d'] = (-1, -1.3, 0.9)
    A = D.view_data(comp(E.lock_gates(30)), 'iso', hidden=False)
    D.ISO_DIR['d'] = (-1, -1.2, 0.8)
    B = D.view_data(comp(E.lift_gate()), 'iso', hidden=False)
    for k, (data, title, x) in enumerate(((A, 'DESIGN A: STEEL MITRE GATES (PREFERRED)', 20), (B, 'DESIGN B: VERTICAL LIFT GATE', 215))):
        w, h = data['bb'][2] - data['bb'][0], data['bb'][3] - data['bb'][1]
        si = min(170 / w, 125 / h)
        ox, oy = x + (175 - w * si) / 2 - data['bb'][0] * si, 22 + data['bb'][3] * si
        D.draw_view(sh, data, ox, oy, si)
        sh.text(x + 87, 154, title, size=3.4, weight='bold')
    text_block(sh, 20, 164, [
        'Two leaves meet at a 1 in 3 mitre. Water pressure pushes them together,',
        'so the mitre and quoin seals get tighter as the head rises (2 to 5.5 m).',
        'Hinges: 316 stainless pintle in a bronze bush, anchor collar at the top.',
        'Drive: one electric actuator per leaf, hidden in an inspection chamber.',
        'Surveillance: CCTV mast per side, a position encoder on each pivot,',
        'emergency call point. Boats: oak fenders on the chamber face.',
        'Looks: the traditional shape, black and white paint, oak, walkway.',
        'Sustainable: steel and oak recycled or reused; no hydraulic oil.',
        'Lift out: %.1f t leaf by mobile crane on two lifting lugs.' % (E.leaf_mass()[0] / 1000),
    ], size=2.5)
    text_block(sh, 215, 164, [
        'One steel gate 4.6 m wide lifts straight up between two concrete towers,',
        'balanced by counterweights and lifted by a winch on a beam 11 m up.',
        'Seals: simple, the gate presses on flat seats on the walls and cill.',
        'Drive: winch motor, in the head house on top of the towers.',
        'Boats must pass under the raised gate, so it lifts at least 3 m clear.',
        'Problems: towers 11.8 m high stand out over a heritage canal; the drive',
        'cannot be hidden in a chamber; slow to lift; hard to crane out.',
        'Rejected: does not meet the aesthetic or the inspection chamber needs.',
    ], size=2.5)
    text_block(sh, 215, 204, [
        'HYDROSTATIC LOAD (BOTH DESIGNS), WORST CASE 5.5 m HEAD, DOWNSTREAM EMPTY',
        'p = ρgh = 1000 x 9.81 x 5.5 = 53.96 kPa at the cill (0 at the surface)',
        'F = ½ρgh² = 148.4 kN per metre width, acting h/3 = 1.83 m above the cill',
        'Design A: each 2.46 m leaf carries 365 kN; mitre thrust R = F / (2 sin 18.4°) = 577 kN',
        'Design B: the 4.6 m gate carries 683 kN, all of it on the two wall seats',
        'Full calculations and assumptions: ESP 2023 calculation sheets.',
    ], size=2.4)
    # comparison table
    rows = [('Meets 4.2 m x 6 m, 5.5 m head', 'Yes', 'Yes'), ('Drive hidden in a chamber', 'Yes', 'No'),
            ('Heritage appearance', 'Good', 'Poor'), ('Sealing', 'Good, self tightening', 'Good'),
            ('Crane removal', '%.1f t per leaf' % (E.leaf_mass()[0] / 1000), 'About 15 t, high lift'), ('Independent operation', 'Yes, per leaf', 'One gate'),
            ('Estimated cost per gate system', 'About £95,000', 'About £130,000')]
    x, y, wds = 20, 222, (70, 50, 50)
    sh.text(x, y - 2, 'COMPARISON AGAINST THE BRIEF', size=3, anchor='start', weight='bold')
    hdr = ('Requirement', 'Design A', 'Design B')
    for r, row in enumerate([hdr] + rows):
        xx = x
        for c, cell in enumerate(row):
            sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="4.6"/>' % (xx, y + r * 4.6, wds[c]))
            sh.text(xx + 1.2, y + r * 4.6 + 3.3, cell, size=2.3, anchor='start', weight='bold' if r == 0 else 'normal')
            xx += wds[c]
    finish(sh, 'ESP23-GA-04_design_ideas', 'ESP 2023 design ideas A and B', 'ESP23-GA-04', 'NTS', 'Design sketch',
           'See notes')


# ------------------------------------------------------------------ GA-05 parts list
def ga05():
    sh = D.Sheet()
    rows = E.bom([n for n, s_, c in E.lock_gates(0)])
    # the table, left half of the sheet
    x, y, h = 16, 18, 4.45
    wd = (9, 50, 9, 92, 50)
    heads = ('Item', 'Part', 'Qty', 'Material and finish', 'Part file / drawing')
    W = sum(wd)
    sh.text(x, y - 2, 'PARTS LIST: ONE GATE SYSTEM (A PAIR OF LEAVES)', size=3.2, anchor='start', weight='bold')
    lines = [('h', heads)]
    g = None
    for r in rows:
        if r['group'] != g:
            g = r['group']
            lines.append(('g', dict(E.GROUPS)[g].upper()))
        mat = r['material'] + (' (bought in)' if r['bought'] and 'Bought' not in r['material'] else '')
        lines.append(('r', (r['no'], r['name'], r['qty'], mat.replace('Bought in: ', 'Bought in. '),
                            '%s  ESP23-P%02d' % (r['file'], r['no']))))
    yy = y
    for kind, row in lines:
        if kind == 'g':
            sh.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#EEF2F6" stroke="#111" stroke-width="0.25"/>' % (x, yy, W, h))
            sh.text(x + 1.2, yy + 3.2, row, size=2.2, anchor='start', weight='bold')
        else:
            xx = x
            for c, cell in enumerate(row):
                sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (xx, yy, wd[c], h))
                txt = str(cell)
                limit = int(wd[c] / 1.12)
                if len(txt) > limit:
                    txt = txt[:limit - 1] + '…'
                sh.text(xx + 1.0, yy + 3.2, txt, size=2.15, anchor='start', weight='bold' if kind == 'h' else 'normal')
                xx += wd[c]
        yy += h
    total = sum(r['qty'] for r in rows)
    sh.text(x, yy + 4.5, '%d different parts, %d parts in all. Quantities are for one gate system: a pair of leaves with '
            'their hinges, drives and chambers.' % (len(rows), total), size=2.4, anchor='start')
    # ballooned isometric of the left leaf from downstream, right of the table
    leaf = E.leaf_items()
    leaf = [it for it in leaf if it[1] != 'pivot_pin']
    D.ISO_DIR['d'] = (1, -1.4, 0.75)
    data = D.view_data(comp([(n, s_, None) for n, k, s_ in leaf]), 'iso', hidden=False)
    bx0, by0, bx1, by1 = data['bb']
    si = min(118 / (bx1 - bx0), 150 / (by1 - by0))
    ox = 268 + (118 - (bx1 - bx0) * si) / 2 - bx0 * si
    oy = 34 + (150 - (by1 - by0) * si) / 2 + by1 * si
    D.draw_view(sh, data, ox, oy, si)
    sh.text(327, 22, 'ONE LEAF FROM DOWNSTREAM, ITEMS 1 TO 19', size=3, weight='bold')
    seen, marks = set(), []
    for n, k, s_ in leaf:
        if k in seen:
            continue
        seen.add(k)
        bb = s_.val().BoundingBox()
        c = ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
        if k in ('girder',):
            c = (1280, -225, 3750)
        if k == 'skin_plate':
            c = (2160, 219, 3300)
        if k == 'stiffener':
            c = (987, -205, 2500)
        px, py = D.proj(c, 'iso')
        marks.append((E.PART[k]['no'], ox + px * si, oy - py * si))
    # balloons in two columns either side of the view, in the order of their height on the paper
    cx = 268 + 59
    left = sorted([m for m in marks if m[1] < cx], key=lambda m: m[2])
    right = sorted([m for m in marks if m[1] >= cx], key=lambda m: m[2])
    for col, bxp in ((left, 262), (right, 392)):
        n = len(col)
        for j, (no, px, py) in enumerate(col):
            byp = 40 + j * (140 / max(1, n - 1)) if n > 1 else py
            sh.add('<line class="lead" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (px, py, bxp + (3 if bxp < cx else -3), byp))
            sh.add('<circle cx="%.2f" cy="%.2f" r="0.6" fill="#111"/>' % (px, py))
            sh.add('<circle class="box" cx="%.2f" cy="%.2f" r="3"/>' % (bxp, byp))
            sh.text(bxp, byp + 1.0, str(no), size=2.6, weight='bold')
    text_block(sh, 262, 196, [
        'NOTES',
        '1. Items 1 to 8 are welded into one leaf frame (6 mm fillet welds minimum).',
        '2. Bought in items are modelled from the maker\'s catalogue sizes.',
        '3. Fixed items (20 to 41) are shown on ESP23-GA-01 and GA-03.',
        '4. Each part has its own drawing, ESP23-Pnn (nn = item), and its own',
        '    STEP file and Inventor build steps on the ESP 2023 project page.',
    ], size=2.3)
    finish(sh, 'ESP23-GA-05_parts_list', 'ESP 2023 parts list', 'ESP23-GA-05', 'NTS', 'Parts list')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['1', '2', '3', '4', '5']
    for k in which:
        dict(zip('12345', (ga01, ga02, ga03, ga04, ga05)))[k]()
