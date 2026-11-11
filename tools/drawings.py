"""Engineering drawings made straight from the CAD models with hidden line removal.

For every model: a third angle sheet and a first angle sheet (front view, plan, end view and an isometric view,
with hidden detail, centre lines, overall sizes, a projection symbol and an ISO 7200 style title block), and a
section A-A sheet for the models that have one. Output: SVG (editable) and PNG.

Run from the repository root:  python3 tools/drawings.py
"""
import json, math, os, subprocess, sys
import cadquery as cq
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepLib import BRepLib
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Cone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import parts  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'drawings')
os.makedirs(OUT, exist_ok=True)
DATE = '2026-11-08'
NOT_SECTIONED = ('bolt', 'nut', 'washer', 'pin', 'rod', 'spring', 'shaft', 'screw', 'tommy bar', 'ball')
# model name: (thread start x, thread end x, minor radius) for threads drawn by convention
THREADS = {'threaded_shaft': (103, 127, 6.9)}

# view directions: (normal towards the viewer, x direction on the paper)
VIEWS = {
    'front': ((0, -1, 0), (1, 0, 0)),
    'plan': ((0, 0, 1), (1, 0, 0)),
    'right': ((1, 0, 0), (0, 1, 0)),
    'left': ((-1, 0, 0), (0, -1, 0)),
    'iso': ((1, -1, 1), (1, 1, 0)),
}


def unit(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


ISO_DIR = {}


def basis(view):
    if view == 'iso' and ISO_DIR.get('d'):
        d = ISO_DIR['d']
        n, vx = d, (1, 1, 0) if d[0] * d[1] < 0 else (1, -1, 0)
        n, vx = unit(n), unit(vx)
        vy = (n[1] * vx[2] - n[2] * vx[1], n[2] * vx[0] - n[0] * vx[2], n[0] * vx[1] - n[1] * vx[0])
        return n, vx, vy
    n, vx = VIEWS[view]
    n, vx = unit(n), unit(vx)
    vy = (n[1] * vx[2] - n[2] * vx[1], n[2] * vx[0] - n[0] * vx[2], n[0] * vx[1] - n[1] * vx[0])
    return n, vx, vy


def proj(p, view):
    n, vx, vy = basis(view)
    return (p[0] * vx[0] + p[1] * vx[1] + p[2] * vx[2], p[0] * vy[0] + p[1] * vy[1] + p[2] * vy[2])


def polylines(shape, defl=0.02):
    out = []
    if shape is None or shape.IsNull():
        return out
    BRepLib.BuildCurves3d_s(shape, 1e-6)
    for e in cq.Shape.cast(shape).Edges():
        c = BRepAdaptor_Curve(e.wrapped)
        pts = GCPnts_QuasiUniformDeflection(c, defl, c.FirstParameter(), c.LastParameter())
        if pts.IsDone() and pts.NbPoints() > 1:
            out.append([(pts.Value(k).X(), pts.Value(k).Y()) for k in range(1, pts.NbPoints() + 1)])
    return out


def hlr(shape, view, hidden=True):
    n, vx, vy = basis(view)
    algo = HLRBRep_Algo()
    algo.Add(shape.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*n), gp_Dir(*vx))))
    algo.Update()
    algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    vis = polylines(h.VCompound()) + polylines(h.OutLineVCompound()) + polylines(h.Rg1LineVCompound())
    hid = (polylines(h.HCompound()) + polylines(h.OutLineHCompound())) if hidden else []
    return vis, hid


FAR_AXES = dict(skip=False)   # set per model (model key skip_far_axes): leave out axes that do not pass through the part


def _passes_through(o, d, sb, tol=0.5):
    """True if the axis line (point o, direction d) comes within the bounding box sb (grown by tol)."""
    c = ((sb.xmin + sb.xmax) / 2, (sb.ymin + sb.ymax) / 2, (sb.zmin + sb.zmax) / 2)
    t = sum((c[i] - o[i]) * d[i] for i in range(3))
    p = [o[i] + d[i] * t for i in range(3)]
    lo, hi = (sb.xmin, sb.ymin, sb.zmin), (sb.xmax, sb.ymax, sb.zmax)
    return all(lo[i] - tol <= p[i] <= hi[i] + tol for i in range(3))


def axes_of(shape):
    """Cylindrical and conical faces: axis point, direction, radius and length along the axis."""
    found = []
    sb = shape.BoundingBox() if FAR_AXES['skip'] else None
    for f in shape.Faces():
        ad = BRepAdaptor_Surface(f.wrapped)
        st = ad.GetType()
        if st not in (GeomAbs_Cylinder, GeomAbs_Cone):
            continue
        ax = ad.Cylinder().Axis() if st == GeomAbs_Cylinder else ad.Cone().Axis()
        r = ad.Cylinder().Radius() if st == GeomAbs_Cylinder else None
        o = ax.Location()
        d = ax.Direction()
        o, d = (o.X(), o.Y(), o.Z()), (d.X(), d.Y(), d.Z())
        if sb is not None and not _passes_through(o, d, sb):
            continue    # a curved face whose axis is far outside the part (a part of a large ring): no centre line
        ts = []
        for v in f.Vertices():
            p = v.toTuple()
            ts.append(sum((p[i] - o[i]) * d[i] for i in range(3)))
        bb = f.BoundingBox()
        for p in ((bb.xmin, bb.ymin, bb.zmin), (bb.xmax, bb.ymax, bb.zmax)):
            ts.append(sum((p[i] - o[i]) * d[i] for i in range(3)))
        if not ts:
            continue
        if r is None:
            r = max(bb.xlen, bb.ylen, bb.zlen) / 2
        found.append(dict(o=o, d=d, r=r, t0=min(ts), t1=max(ts)))
    return found


def centre_lines(shape, view):
    n, vx, vy = basis(view)
    marks, lines, seen = [], [], set()
    for a in axes_of(shape):
        dn = abs(sum(a['d'][i] * n[i] for i in range(3)))
        c = proj(a['o'], view)
        if dn > 0.99:
            key = ('m', round(c[0], 1), round(c[1], 1))
            if key in seen:
                continue
            seen.add(key)
            marks.append((c, a['r']))
        elif dn < 0.01:
            p0 = [a['o'][i] + a['d'][i] * a['t0'] for i in range(3)]
            p1 = [a['o'][i] + a['d'][i] * a['t1'] for i in range(3)]
            q0, q1 = proj(p0, view), proj(p1, view)
            key = ('l', round(q0[0], 1), round(q0[1], 1), round(q1[0], 1), round(q1[1], 1))
            if key in seen or math.dist(q0, q1) < 0.5:
                continue
            seen.add(key)
            lines.append((q0, q1))
    # keep the largest radius per mark position
    best = {}
    for c, r in marks:
        k = (round(c[0], 1), round(c[1], 1))
        best[k] = max(best.get(k, 0), r)
    return [((k[0], k[1]), r) for k, r in best.items()], lines


def bbox(pls):
    xs = [p[0] for pl in pls for p in pl]
    ys = [p[1] for pl in pls for p in pl]
    return min(xs), min(ys), max(xs), max(ys)


# ------------------------------------------------------------------ svg helpers
class Sheet:
    W, H = 420.0, 297.0

    def __init__(self):
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def path(self, pls, cls, tx, ty, s, flip=True):
        d = []
        for pl in pls:
            pts = [(tx + p[0] * s, ty - p[1] * s if flip else ty + p[1] * s) for p in pl]
            d.append('M' + ' L'.join('%.2f,%.2f' % q for q in pts))
        if d:
            self.add('<path class="%s" d="%s"/>' % (cls, ' '.join(d)))

    def line(self, x1, y1, x2, y2, cls):
        self.add('<line class="%s" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (cls, x1, y1, x2, y2))

    def text(self, x, y, s, size=3.5, anchor='middle', weight='normal', rot=0):
        tr = ' transform="rotate(%d %.2f %.2f)"' % (rot, x, y) if rot else ''
        self.add('<text x="%.2f" y="%.2f" font-size="%.2f" text-anchor="%s" font-weight="%s"%s>%s</text>' % (
            x, y, size, anchor, weight, tr, s))

    def svg(self):
        style = ('<style>path,line,circle,polygon{fill:none;stroke:#111;stroke-linecap:round;stroke-linejoin:round}'
                 '.vis{stroke-width:0.5}.hid{stroke-width:0.25;stroke-dasharray:2.5,1.2}'
                 '.ctr{stroke-width:0.25;stroke-dasharray:8,1.5,1.5,1.5;stroke:#1565D8}.dim{stroke-width:0.25}'
                 '.thin{stroke-width:0.25}.hat{stroke-width:0.18}.bord{stroke-width:0.7}.cut{stroke-width:0.25;'
                 'stroke-dasharray:8,1.5,1.5,1.5}.cutend{stroke-width:0.7}'
                 'rect.bord,rect.thin{fill:none;stroke:#111}text{font-family:Arial,Helvetica,sans-serif;fill:#111}.arrow{fill:#111;stroke:none}</style>')
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" '
                'height="%dmm" viewBox="0 0 %d %d">%s<rect x="0" y="0" width="%d" height="%d" fill="#fff" '
                'stroke="none"/>%s</svg>' % (self.W, self.H, self.W, self.H, style, self.W, self.H, '\n'.join(self.parts)))


def arrow(sh, x, y, ang, size=2.5):
    a = math.radians(ang)
    p1 = (x - size * math.cos(a) + size * 0.3 * math.sin(a), y - size * math.sin(a) - size * 0.3 * math.cos(a))
    p2 = (x - size * math.cos(a) - size * 0.3 * math.sin(a), y - size * math.sin(a) + size * 0.3 * math.cos(a))
    sh.add('<polygon class="arrow" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f"/>' % (x, y, p1[0], p1[1], p2[0], p2[1]))


def dim_h(sh, x1, x2, y, ext_from, val):
    """Horizontal dimension at paper height y; extension lines from the feature height ext_from."""
    for x in (x1, x2):
        sh.line(x, ext_from + (1.5 if y > ext_from else -1.5), x, y + (2 if y > ext_from else -2), 'dim')
    sh.line(x1, y, x2, y, 'dim')
    arrow(sh, x1, y, 180)
    arrow(sh, x2, y, 0)
    sh.text((x1 + x2) / 2, y - 1.2, val)


def dim_v(sh, y1, y2, x, ext_from, val):
    for yy in (y1, y2):
        sh.line(ext_from + (-1.5 if x < ext_from else 1.5), yy, x + (-2 if x < ext_from else 2), yy, 'dim')
    sh.line(x, y1, x, y2, 'dim')
    arrow(sh, x, y1, 270 if y1 < y2 else 90)
    arrow(sh, x, y2, 90 if y1 < y2 else 270)
    sh.text(x - 1.2, (y1 + y2) / 2, val, rot=-90)


def proj_symbol(sh, x, y, angle, s=1.0):
    """BS 8888 / ISO 5456-2 projection symbol, about 24 x 10 at s = 1."""
    D, d, L, g = 9 * s, 4.5 * s, 10 * s, 3.5 * s
    cy = y + D / 2
    if angle == 'first':
        tx, cx = x, x + L + g + D / 2
    else:
        cx, tx = x + D / 2, x + D + g
    sh.add('<polygon class="vis" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f"/>' % (
        tx, cy - d / 2, tx + L, cy - D / 2, tx + L, cy + D / 2, tx, cy + d / 2))
    sh.add('<circle class="vis" cx="%.2f" cy="%.2f" r="%.2f"/>' % (cx, cy, D / 2))
    sh.add('<circle class="vis" cx="%.2f" cy="%.2f" r="%.2f"/>' % (cx, cy, d / 2))
    sh.line(x - 1.5, cy, x + L + g + D + 1.5, cy, 'ctr')
    sh.line(cx, cy - D / 2 - 1.5, cx, cy + D / 2 + 1.5, 'ctr')


def frame(sh, title, number, scale, angle, material, doctype, owner='T Level Engineering, Unit 3', date=None):
    sh.add('<rect class="bord" x="10" y="10" width="400" height="277"/>')
    x0, y0, w, h = 230, 252, 180, 35
    sh.add('<rect class="thin" x="%d" y="%d" width="%d" height="%d"/>' % (x0, y0, w, h))
    rows = [y0 + 7, y0 + 14, y0 + 21, y0 + 28]
    for yy in rows:
        sh.line(x0, yy, x0 + w, yy, 'thin')
    for xx in (x0 + 60, x0 + 120):
        sh.line(xx, y0, xx, y0 + 28, 'thin')

    def cell(cx, cy, lab, val, bold=False):
        sh.text(cx + 1.5, cy + 2.6, lab, size=1.8, anchor='start')
        size = min(2.9 if not bold else 3.2, 57 / (0.6 * max(len(str(val)), 1)))   # long text shrinks to fit its cell
        sh.text(cx + 1.5, cy + 6.1, val, size=size, anchor='start', weight='bold' if bold else 'normal')
    cell(x0, y0, 'Legal owner', owner)
    cell(x0 + 60, y0, 'Document type', doctype)
    cell(x0 + 120, y0, 'Identification number', number, True)
    cell(x0, y0 + 7, 'Title', title, True)
    cell(x0 + 60, y0 + 7, 'Material', material)
    cell(x0 + 120, y0 + 7, 'Revision', 'A')
    cell(x0, y0 + 14, 'Created by', 'Unit 3 CAD hub')
    cell(x0 + 60, y0 + 14, 'Approved by', '(tutor)')
    cell(x0 + 120, y0 + 14, 'Date of issue', date or DATE)
    cell(x0, y0 + 21, 'Scale', scale, True)
    cell(x0 + 60, y0 + 21, 'Units', 'mm')
    cell(x0 + 120, y0 + 21, 'Sheet', '1 of 1')
    sh.text(x0 + 1.5, y0 + 30.8, 'Projection', size=1.8, anchor='start')
    proj_symbol(sh, x0 + 22, y0 + 29.3, angle, 0.55)
    sh.text(x0 + 62, y0 + 32.5, '%s angle projection. Drawn from the CAD model with hidden line removal.' % angle.capitalize(),
            size=2.2, anchor='start')


STD_SCALES = [(5, 1), (2, 1), (1, 1), (1, 2), (1, 5), (1, 10), (1, 20), (1, 25), (1, 50), (1, 100)]


def pick_scale(wmm, hmm, aw, ah):
    for a, b in STD_SCALES:
        s = a / b
        if wmm * s <= aw and hmm * s <= ah:
            return s, '%d:%d' % (a, b)
    return 0.01, '1:100'


def draw_view(sh, data, ox, oy, s, label=None):
    vis, hid, marks, lines = data['vis'], data['hid'], data['marks'], data['lines']
    sh.path(hid, 'hid', ox, oy, s)
    sh.path(vis, 'vis', ox, oy, s)
    for (c, r) in marks:
        e = r * s + 2.5
        x, y = ox + c[0] * s, oy - c[1] * s
        sh.line(x - e, y, x + e, y, 'ctr')
        sh.line(x, y - e, x, y + e, 'ctr')
    for (q0, q1) in lines:
        ux, uy = q1[0] - q0[0], q1[1] - q0[1]
        L = math.hypot(ux, uy)
        ux, uy = ux / L, uy / L
        sh.line(ox + (q0[0] - ux * 2.5 / s) * s, oy - (q0[1] - uy * 2.5 / s) * s,
                ox + (q1[0] + ux * 2.5 / s) * s, oy - (q1[1] + uy * 2.5 / s) * s, 'ctr')
    if label:
        x0, y0, x1, y1 = data['bb']
        sh.text(ox + (x0 + x1) / 2 * s, oy - y0 * s + 8, label, size=3.0, weight='bold')


def view_data(shape, view, hidden=True):
    vis, hid = hlr(shape, view, hidden)
    marks, lines = centre_lines(shape, view) if view != 'iso' else ([], [])
    return dict(vis=vis, hid=hid, marks=marks, lines=lines, bb=bbox(vis + hid))


ESP_MATERIAL = {'esp2023_lock_gates': 'See parts list', 'esp2023_gate_leaf': 'S355 steel, see parts list',
                'esp2023_skin_panel': 'S355 steel plate', 'esp2023_lift_gate': 'Concept, see notes',
                'esp2026_seat_set': 'See parts list', 'esp2026_single_seat': 'See parts list',
                'esp2026_shell_seats': 'Concept, see notes', 'esp2024_buoy': 'See parts list',
                'esp2024_buoy_green': 'See parts list', 'esp2024_wind_buoy': 'Concept, see notes',
                'esp2025_dispenser': 'See parts list', 'esp2025_cassette': 'Concept, see notes'}
# each Employer-Set Project folder: the client named in the title block, the drawing date and the drawing number prefix
PROJECTS = {'ESP 2023': dict(owner='Lock Restoration Ltd', date='2026-11-10', prefix='ESP23'),
            'ESP 2026': dict(owner='Aero-Chair Ltd', date='2026-11-10', prefix='ESP26'),
            'ESP 2024': dict(owner='Harbour Shipping Ltd', date='2026-11-10', prefix='ESP24'),
            'ESP 2025': dict(owner='WBEP Ltd for the health trust', date='2026-11-10', prefix='ESP25'),
            'GrabCAD models': dict(owner='T Level Engineering, Unit 3', date='2026-11-11', prefix='GC')}


def owner_of(m):
    return PROJECTS[m['folder']]['owner'] if m.get('folder') in PROJECTS else 'T Level Engineering, Unit 3'


def date_of(m):
    return PROJECTS[m['folder']]['date'] if m.get('folder') in PROJECTS else None


def prefix_of(m):
    return PROJECTS[m['folder']]['prefix'] if m.get('folder') in PROJECTS else 'U3'


def material_of(m):
    if m.get('part'):
        return m['part']['material'].replace('Bought in: ', '').split(',')[0][:30]
    if m['name'] in ESP_MATERIAL:
        return ESP_MATERIAL[m['name']]
    if m.get('sub') or m.get('folder') == 'GrabCAD models':
        return 'See parts list'        # a sub-assembly: its parts list gives the material of each part
    return {'flanged_bush': 'CZ121 brass', 'pcd_flange': '6082-T6 aluminium', 'threaded_shaft': '080M40 steel',
            'bolted_joint': 'See parts list', 'fit_pair': 'See parts list', 'pneumatic_cylinder': 'See parts list',
            'machine_vice': 'See parts list'
            }.get(m['name'], 'S275 steel' if m['name'] in ('l_bracket', 'vee_block') else '6082-T6 aluminium')


def ortho_sheet(m, shape, angle, number):
    sh = Sheet()
    side = 'right' if angle == 'third' else 'left'
    F = view_data(shape, 'front')
    P = view_data(shape, 'plan')
    E = view_data(shape, side)
    I = view_data(shape, 'iso', hidden=False)
    fw, fh = F['bb'][2] - F['bb'][0], F['bb'][3] - F['bb'][1]
    pw, ph = P['bb'][2] - P['bb'][0], P['bb'][3] - P['bb'][1]
    ew, eh = E['bb'][2] - E['bb'][0], E['bb'][3] - E['bb'][1]
    gap = 22
    # the three views must fit in the left part of the sheet, with room for dimensions
    s, sc = pick_scale(fw + ew + 0.0, fh + ph, 250 - gap * 2, 200 - gap * 2)
    totw = (fw + ew) * s + gap
    toth = (fh + ph) * s + gap
    x_left = 22 + (250 - totw) / 2
    y_top = 18 + (240 - toth) / 2
    fx = x_left - F['bb'][0] * s
    if angle == 'third':
        py = y_top + P['bb'][3] * s                    # plan above the front view
        fy = y_top + ph * s + gap + F['bb'][3] * s
    else:
        fy = y_top + F['bb'][3] * s                    # front view above, plan below
        py = y_top + fh * s + gap + P['bb'][3] * s
    px = fx                                            # plan and front share x
    ex = x_left + fw * s + gap - E['bb'][0] * s
    ey = fy                                            # end view and front share height
    draw_view(sh, F, fx, fy, s, 'FRONT VIEW')
    draw_view(sh, P, px, py, s, 'PLAN')
    draw_view(sh, E, ex, ey, s, 'END VIEW (FROM %s)' % side.upper())
    th_ = THREADS.get(m['name'])
    if th_:
        x0t, x1t, rmin = th_
        # thread convention: thin line at the minor diameter in the front view and plan
        for (ox, oy) in ((fx, fy), (px, py)):
            for r in (rmin, -rmin):
                sh.line(ox + x0t * s, oy - r * s, ox + x1t * s, oy - r * s, 'thin')
        if side == 'right':
            # three-quarter circle at the minor diameter, seen from the threaded end
            cx, cy, rr = ex, ey, rmin * s
            sh.add('<path class="thin" d="M%.2f,%.2f A%.2f,%.2f 0 1 1 %.2f,%.2f"/>' % (cx + rr, cy, rr, rr, cx, cy - rr))
        sh.text(22, 242, 'M16 thread drawn by convention: thick line at the major diameter, thin line at the minor '
                'diameter, a three-quarter circle in the end view.', size=2.8, anchor='start')
    # isometric, top right, fitted
    iw, ih = I['bb'][2] - I['bb'][0], I['bb'][3] - I['bb'][1]
    si = min(120 / iw, 95 / ih, s * 1.0)
    ix = 285 - I['bb'][0] * si + (120 - iw * si) / 2
    iy = 25 + I['bb'][3] * si + (95 - ih * si) / 2
    draw_view(sh, I, ix, iy, si)
    sh.text(285 + 60, 128, 'ISOMETRIC VIEW (NOT TO SCALE)', size=3.0, weight='bold')
    # overall sizes
    x0, y0, x1, y1 = F['bb']
    dim_h(sh, fx + x0 * s, fx + x1 * s, fy - y0 * s + 17, fy - y0 * s, '%g' % round(fw, 1))
    dim_v(sh, fy - y1 * s, fy - y0 * s, fx + x0 * s - 12, fx + x0 * s, '%g' % round(fh, 1))
    e0, f0, e1, f1 = E['bb']
    dim_h(sh, ex + e0 * s, ex + e1 * s, ey - f0 * s + 17, ey - f0 * s, '%g' % round(ew, 1))
    if m.get('part'):
        # component drawing: the key sizes of every feature, from the part's own data, in a table under the iso
        pt = m['part']
        sh.text(285, 140, 'KEY SIZES (mm)', size=3.0, weight='bold', anchor='start')
        yk = 147
        for line in pt.get('sizes', []):
            sh.text(285, yk, line, size=2.6, anchor='start')
            yk += 5.2
        sh.text(285, yk + 3, 'Material: ' + pt['material'], size=2.6, anchor='start')
        sh.text(285, yk + 8.2, 'Part file: %s. Item %d on %s-GA-05.' % (pt['file'], pt['no'], prefix_of(m)), size=2.6, anchor='start')
        sh.text(22, 248, 'Dimensions in millimetres. Overall sizes on the views; feature sizes in the table.', size=2.8,
                anchor='start')
    else:
        sh.text(22, 248, 'Dimensions in millimetres. Overall sizes only: full dimensioning is criterion 3.2.', size=2.8,
                anchor='start')
    sh.text(22, 254, 'Centre lines are shown in blue. Hidden detail is shown dashed.', size=2.8, anchor='start')
    doctype = 'Assembly drawing' if len(m['parts']) > 1 else 'Detail drawing'
    frame(sh, m['title'], number, sc, angle, material_of(m), doctype, owner_of(m), date_of(m))
    return sh


def hatch(pls, spacing, direction=1):
    """45 degree hatch lines for one or more closed loops, using the even-odd rule."""
    segs = []
    for pl in pls:
        for k in range(len(pl) - 1):
            segs.append((pl[k], pl[k + 1]))
    vals = [p[0] + direction * p[1] for pl in pls for p in pl]
    out = []
    c = math.floor(min(vals) / spacing) * spacing + spacing / 2
    while c < max(vals):
        xs = []
        for (u1, v1), (u2, v2) in segs:
            g1, g2 = u1 + direction * v1 - c, u2 + direction * v2 - c
            if (g1 > 0) != (g2 > 0):
                t = g1 / (g1 - g2)
                xs.append((u1 + t * (u2 - u1), v1 + t * (v2 - v1)))
        xs.sort(key=lambda p: p[0])
        for k in range(0, len(xs) - 1, 2):
            out.append([xs[k], xs[k + 1]])
        c += spacing
    return out


def cut_faces_2d(half, y0, view='front'):
    loops = []
    for f in half.Faces():
        if f.geomType() != 'PLANE':
            continue
        n = f.normalAt()
        c = f.Center()
        if abs(n.y + 1) < 1e-3 and abs(c.y - y0) < 1e-3:
            for w in f.Wires():
                pts = []
                for e in w.Edges():
                    ad = BRepAdaptor_Curve(e.wrapped)
                    gp = GCPnts_QuasiUniformDeflection(ad, 0.02, ad.FirstParameter(), ad.LastParameter())
                    seg = [gp.Value(k) for k in range(1, gp.NbPoints() + 1)]
                    seg = [proj((p.X(), p.Y(), p.Z()), view) for p in seg]
                    pts.append(seg)
                # chain the edge polylines into one closed loop
                loop = list(pts[0])
                rest = pts[1:]
                while rest:
                    end = loop[-1]
                    best = min(range(len(rest)), key=lambda k: min(math.dist(end, rest[k][0]), math.dist(end, rest[k][-1])))
                    seg = rest.pop(best)
                    if math.dist(end, seg[-1]) < math.dist(end, seg[0]):
                        seg = seg[::-1]
                    loop.extend(seg[1:])
                loop.append(loop[0])
                loops.append(loop)
    return loops


def section_sheet(m, items, number):
    """Full section A-A on the front view, with the cutting plane shown on the plan."""
    sh = Sheet()
    comp = cq.Compound.makeCompound([w.val() for n, w, c in items])
    bb = comp.BoundingBox()
    y0 = (bb.ymin + bb.ymax) / 2
    keep = cq.Solid.makeBox(bb.xlen + 20, bb.ylen, bb.zlen + 20, cq.Vector(bb.xmin - 10, y0, bb.zmin - 10))
    pieces, hatched = [], []
    for k, (n, w, c) in enumerate(items):
        solid = w.val()
        if len(items) > 1 and any(t in n.lower() for t in NOT_SECTIONED):
            pieces.append(solid)
            continue
        half = solid.intersect(keep)
        pieces.append(half)
        hatched.append((k, half))
    halfcomp = cq.Compound.makeCompound(pieces)
    S = view_data(halfcomp, 'front', hidden=False)
    P = view_data(comp, 'plan')
    sw, shh = S['bb'][2] - S['bb'][0], S['bb'][3] - S['bb'][1]
    pw, ph = P['bb'][2] - P['bb'][0], P['bb'][3] - P['bb'][1]
    gap = 26
    s, sc = pick_scale(max(sw, pw), shh + ph, 300, 200)
    s2, sc2 = pick_scale(sw + pw, max(shh, ph), 300 - gap, 200)
    if m.get('folder') == 'GrabCAD models' and s2 > s:
        # a tall model: plan on the left, section on the right (both labelled, so they need not line up)
        s, sc = s2, sc2
        x_left = 22 + (380 - (sw + pw) * s - gap) / 2
        y_mid = 18 + 225 / 2
        px = x_left - P['bb'][0] * s
        py = y_mid + (P['bb'][1] + P['bb'][3]) / 2 * s
        sx = x_left + pw * s + gap - S['bb'][0] * s
        sy = y_mid + (S['bb'][1] + S['bb'][3]) / 2 * s
    else:
        x_left = 22 + (380 - max(sw, pw) * s) / 2
        toth = (shh + ph) * s + gap
        y_top = 18 + (225 - toth) / 2
        py = y_top + P['bb'][3] * s
        sy = y_top + ph * s + gap + S['bb'][3] * s
        sx = x_left - S['bb'][0] * s
        px = sx
    # hatching first, so the outlines sit on top
    for j, (k, half) in enumerate(hatched):
        loops = cut_faces_2d(half, y0)
        if loops:
            hl = hatch(loops, 3.0 / s if s >= 1 else 3.0 / s, 1 if j % 2 == 0 else -1)
            sh.path(hl, 'hat', sx, sy, s)
    draw_view(sh, S, sx, sy, s, 'SECTION A-A')
    draw_view(sh, P, px, py, s, 'PLAN')
    # cutting plane on the plan: y = y0, which in plan coordinates is the paper y of model y
    cy = py - y0 * s
    xa, xb = px + P['bb'][0] * s - 8, px + P['bb'][2] * s + 8
    sh.line(xa, cy, xb, cy, 'cut')
    sh.line(xa, cy, xa + 6, cy, 'cutend')
    sh.line(xb - 6, cy, xb, cy, 'cutend')
    for x in (xa + 1, xb - 1):
        sh.line(x, cy, x, cy + 7, 'cutend')
        arrow(sh, x, cy + 8.5, 90, 3)
        sh.text(x + (-3.5 if x < (xa + xb) / 2 else 3.5), cy + 9, 'A', size=4.5, weight='bold')
    note = ('Standard parts on the cutting plane (bolts, nuts, washers, pins, rods and springs) are not sectioned. '
            if len(items) > 1 else '')
    sh.text(22, 248, 'Section A-A: the cutting plane runs through the centre. Hatching at 45 degrees shows cut material.',
            size=2.8, anchor='start')
    if note:
        sh.text(22, 254, note + 'Adjacent parts are hatched in opposite directions.', size=2.8, anchor='start')
    doctype = 'Assembly drawing' if len(items) > 1 else 'Detail drawing'
    frame(sh, m['title'] + ', section A-A', number, sc, 'third', material_of(m), doctype, owner_of(m), date_of(m))
    return sh


def save(sh, base, out=OUT):
    os.makedirs(out, exist_ok=True)
    svg = os.path.join(out, base + '.svg')
    with open(svg, 'w') as f:
        f.write(sh.svg())
    subprocess.run(['rsvg-convert', '-w', '2480', '-b', 'white', '-o', os.path.join(out, base + '.png'), svg], check=True)


def main(only=None):
    cat = json.load(open(os.path.join(ROOT, 'docs', 'models.json')))
    for k, m in enumerate(cat):
        if only and m['name'] not in only:
            continue
        spec = [x for x in parts.MODELS if x['name'] == m['name']][0]
        ISO_DIR['d'] = spec.get('iso', (1, -1, 1))
        FAR_AXES['skip'] = spec.get('skip_far_axes', False)
        items = spec['fn']()
        comp = cq.Compound.makeCompound([w.val() for n, w, c in items])
        base = parts.base_of(spec)
        out = os.path.join(ROOT, 'docs', base, 'drawings')
        if spec.get('part'):
            number = '%s-P%02d' % (prefix_of(spec), spec['part']['no'])
        elif base:
            esp = [x['name'] for x in parts.MODELS if x.get('folder') == spec['folder'] and not x.get('part')]
            number = '%s-%02d' % (prefix_of(spec), esp.index(m['name']) + 1)
        else:
            number = 'U3-%03d' % (k + 1)
        print('drawing', m['name'])
        save(ortho_sheet(m, comp, 'third', number + '-3'), m['name'] + '_third_angle', out)
        save(ortho_sheet(m, comp, 'first', number + '-1'), m['name'] + '_first_angle', out)
        files = dict(third=base + 'drawings/%s_third_angle' % m['name'], first=base + 'drawings/%s_first_angle' % m['name'])
        if m.get('section'):
            save(section_sheet(m, items, number + '-S'), m['name'] + '_section', out)
            files['section'] = base + 'drawings/%s_section' % m['name']
        m['drawings'] = files
    with open(os.path.join(ROOT, 'docs', 'models.json'), 'w') as f:
        json.dump(cat, f, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:] or None)
