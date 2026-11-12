"""Hidden detail for the viewer's Front, Plan and End view buttons, from the CAD models with hidden line removal.

The viewer draws the model as a shaded solid with its edges, so an edge at the back is simply covered up. On an
orthographic drawing that edge is drawn as a thin dashed line. This tool works out, for each principal view, the
edges and outlines (including the sides of holes and bosses) that cannot be seen, using the same hidden line
removal as the drawing sheets in docs/drawings, and saves them for the viewer to draw dashed.

Output: docs/<folder>/hidden/<name>.json = {"front": [polyline, ...], "plan": [...], "right": [...], "left": [...]}.
Each polyline is a flat list x0, y0, z0, x1, y1, z1, ... in glTF coordinates (Y up), on a plane just in front of
the model, so the viewer can draw it over the solid in that view.

Run from the repository root:  python3 tools/build_hidden.py [model names]
"""
import json, math, os, sys, time
import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import parts  # noqa: E402
from drawings import hlr, basis  # noqa: E402
from build_models import to_gl  # noqa: E402

DOCS = os.path.join(ROOT, 'docs')
VIEWS = ('front', 'plan', 'right', 'left')


def seg_dist(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    L = ax * ax + ay * ay
    t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L))
    return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)


class SegIndex:
    """Visible segments in a coarse grid, so 'is this point on a visible line' stays fast on big assemblies."""

    def __init__(self, pls, cell):
        self.cell, self.grid = cell, {}
        for pl in pls:
            for a, b in zip(pl, pl[1:]):
                for i in range(int(min(a[0], b[0]) // cell) - 1, int(max(a[0], b[0]) // cell) + 2):
                    for j in range(int(min(a[1], b[1]) // cell) - 1, int(max(a[1], b[1]) // cell) + 2):
                        self.grid.setdefault((i, j), []).append((a, b))

    def on(self, p, tol):
        return any(seg_dist(p, a, b) < tol for a, b in self.grid.get((int(p[0] // self.cell), int(p[1] // self.cell)), ()))


def uncovered(pl, index, step, tol):
    """The pieces of a hidden polyline that do not sit exactly behind a visible line (the visible line wins)."""
    pts = []
    for a, b in zip(pl, pl[1:]):
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        pts += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k)]
    pts.append(pl[-1])
    out, cur = [], []
    for p in pts:
        if index.on(p, tol):
            if len(cur) > 1:
                out.append(cur)
            cur = []
        else:
            cur.append(p)
    if len(cur) > 1:
        out.append(cur)
    return out


def simplify(pl, tol):
    """Drop points that sit on the straight line between their neighbours (the sampling above adds many)."""
    out = [pl[0]]
    for i in range(1, len(pl) - 1):
        if seg_dist(pl[i], out[-1], pl[i + 1]) > tol:
            out.append(pl[i])
    out.append(pl[-1])
    return out


def hidden_lines(shape):
    bb = shape.BoundingBox()
    corners = [(x, y, z) for x in (bb.xmin, bb.xmax) for y in (bb.ymin, bb.ymax) for z in (bb.zmin, bb.zmax)]
    out = {}
    for view in VIEWS:
        n, vx, vy = basis(view)
        # a plane just in front of the nearest point of the model, so the lines sit over the solid
        c = max(sum(p[i] * n[i] for i in range(3)) for p in corners) + 1.0
        vis, hid = hlr(shape, view)
        size = max(bb.xlen, bb.ylen, bb.zlen)
        step, tol = max(0.5, size / 400), max(0.05, size / 4000)
        index = SegIndex(vis, max(2.0, size / 50))
        pieces = [simplify(q, tol) for pl in hid for q in uncovered(pl, index, step, tol)]
        pls = []
        for pl in pieces:
            pts = []
            for u, v in pl:
                p = tuple(u * vx[i] + v * vy[i] + c * n[i] for i in range(3))
                pts += [round(t, 2) for t in to_gl(p)]
            if len(pts) >= 6:
                pls.append(pts)
        out[view] = pls
    return out


def build(only=None):
    for m in parts.MODELS:
        if only and m['name'] not in only:
            continue
        t = time.time()
        items = [(n, w, c) for n, w, c in m['fn']() if n not in (m.get('hide') or [])]
        comp = cq.Compound.makeCompound([w.val() for n, w, c in items])
        data = hidden_lines(comp)
        d = os.path.join(DOCS, parts.base_of(m), 'hidden')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, m['name'] + '.json'), 'w') as f:
            json.dump(data, f, separators=(',', ':'))
        print(m['name'], {k: len(v) for k, v in data.items()}, '%.1f s' % (time.time() - t), flush=True)


if __name__ == '__main__':
    build(sys.argv[1:] or None)
