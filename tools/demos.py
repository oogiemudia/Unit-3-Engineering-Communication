"""Data for the three lesson demonstrations (auxiliary views, line types on a real view, scale).

Every view comes from the same CadQuery models as the rest of the hub, with hidden line removal, so the
demonstrations, the drawing sheets and the 3D viewer always agree. Output: docs/demos/data.json

Run from the repository root:  python3 tools/demos.py
"""
import json, math, os, sys
import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import parts  # noqa: E402
import drawings  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'demos')
os.makedirs(OUT, exist_ok=True)

# the sloping face each auxiliary demonstration looks at square on: the outward normal of that face (CAD axes)
AUX_FACES = {
    'sloping_block': (1, 0, 1),     # the 45 degree face with the 12 mm hole (lesson slide 85)
    'vee_block': (-1, 0, 1),        # the right hand face of the vee
}
DEMO_MODELS = ['step_block', 'sloping_block', 'vee_block']


def r(v, n=2):
    return round(v, n)


def pls(lines):
    return [[[r(x), r(y)] for x, y in pl] for pl in lines]


def seg_dist(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    L = ax * ax + ay * ay
    t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L))
    return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)


def covered(pl, others, tol=0.05):
    """True when every point of pl lies on one of the other polylines: a hidden edge behind a visible one."""
    segs = [(o[i], o[i + 1]) for o in others for i in range(len(o) - 1)]
    pts = []
    for i in range(len(pl) - 1):        # test points every millimetre, not only the ends
        a, b = pl[i], pl[i + 1]
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
        pts += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k + 1)]
    return all(any(seg_dist(p, a, b) < tol for a, b in segs) for p in pts)


def view(shape, name):
    d = drawings.view_data(shape, name)
    # a hidden edge that sits exactly behind a visible edge is not drawn: the visible line wins
    hid = [pl for pl in d['hid'] if not covered(pl, d['vis'])]
    return dict(vis=pls(d['vis']), hid=pls(hid),
                lines=[[[r(a[0]), r(a[1])], [r(b[0]), r(b[1])]] for a, b in d['lines']],
                marks=[[[r(c[0]), r(c[1])], r(rad)] for c, rad in d['marks']],
                bb=[r(v) for v in d['bb']])


def unit(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def sloping_face(shape, normal):
    """The planar face with this outward normal: its outline corners and any circular holes in it."""
    n = unit(normal)
    best = None
    for f in shape.Faces():
        if f.geomType() != 'PLANE':
            continue
        fn = f.normalAt().toTuple()
        if sum(fn[i] * n[i] for i in range(3)) > 0.999:
            if best is None or f.Area() > best.Area():
                best = f
    assert best is not None, normal
    outer = [v.toTuple() for v in best.outerWire().Vertices()]
    holes = []
    for w in best.innerWires():
        e = w.Edges()[0]
        if e.geomType() == 'CIRCLE':
            c = e.arcCenter().toTuple()
            holes.append(dict(c=[r(x) for x in c], r=r(e.radius())))
    # order the outline corners round the face
    cx = sum(p[0] for p in outer) / len(outer); cy = sum(p[1] for p in outer) / len(outer); cz = sum(p[2] for p in outer) / len(outer)
    s = unit((-n[2], 0, n[0])) if abs(n[1]) < 0.9 else (1, 0, 0)       # along the slope, in the XZ plane
    yv = (0, 1, 0)
    outer.sort(key=lambda p: math.atan2((p[1] - cy), sum((p[i] - (cx, cy, cz)[i]) * s[i] for i in range(3))))
    return dict(normal=[r(x, 5) for x in n], slope=[r(x, 5) for x in s], centre=[r(cx), r(cy), r(cz)],
                corners=[[r(x) for x in p] for p in outer], holes=holes, area=r(best.Area()))


def main():
    data = {}
    for spec in parts.MODELS:
        if spec['name'] not in DEMO_MODELS:
            continue
        items = spec['fn']()
        shape = items[0][1].val() if hasattr(items[0][1], 'val') else items[0][1]
        drawings.ISO_DIR['d'] = spec.get('iso', (1, -1, 1))
        bb = shape.BoundingBox()
        entry = dict(title=spec['title'], size=[r(bb.xlen), r(bb.ylen), r(bb.zlen)],
                     min=[r(bb.xmin), r(bb.ymin), r(bb.zmin)],
                     front=view(shape, 'front'), plan=view(shape, 'plan'))
        if spec['name'] in AUX_FACES:
            entry['aux'] = sloping_face(shape, AUX_FACES[spec['name']])
        data[spec['name']] = entry
        print(spec['name'], entry['size'], 'aux' if 'aux' in entry else '')
    with open(os.path.join(OUT, 'data.json'), 'w') as fh:
        json.dump(data, fh, separators=(',', ':'))
    print('wrote docs/demos/data.json')


if __name__ == '__main__':
    main()
