"""ESP 2026 assembly checks: clashes between every pair of parts at several positions of the motion, and parts
that touch nothing (floating). Run from the repository root:  python3 tools/esp2026_checks.py

Positions checked: everything upright and stowed; backs half reclined (2.5 degrees); backs fully reclined
(5 degrees); trays folded down; armrests up; and backs reclined with the trays down and the armrests up.
A clash is a shared volume of more than 1 mm3. A part floats if it is more than 0.05 mm from every other part.
Writes docs/ESP 2026/qa/assembly_checks.json.
"""
import itertools, json, os, sys
import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import esp2026 as E  # noqa: E402

R = E.RECLINE
POSITIONS = [
    ('upright, stowed', dict()),
    ('backs half reclined', dict(recline=(R / 2,) * 3)),
    ('backs fully reclined', dict(recline=(R,) * 3)),
    ('trays down', dict(tray=(E.TRAY_DEPLOY,) * 3)),
    ('armrests up', dict(arms=(E.ARM_UP,) * 4)),
    ('reclined, trays down, armrests up', dict(recline=(R,) * 3, tray=(E.TRAY_DEPLOY,) * 3, arms=(E.ARM_UP,) * 4)),
]


def overlaps(a, b, tol=0.5):
    return not (a.xmax < b.xmin - tol or b.xmax < a.xmin - tol or a.ymax < b.ymin - tol or b.ymax < a.ymin - tol
                or a.zmax < b.zmin - tol or b.zmax < a.zmin - tol)


def clashes(items):
    solids = [(n, s.val()) for n, k, s in items]
    bbs = [s.BoundingBox() for n, s in solids]
    out = []
    for i, j in itertools.combinations(range(len(solids)), 2):
        if not overlaps(bbs[i], bbs[j], 0):
            continue
        v = solids[i][1].intersect(solids[j][1]).Volume()
        if v > 1.0:
            out.append((solids[i][0], solids[j][0], round(v, 1)))
    return out


def floating(items):
    solids = [(n, s.val()) for n, k, s in items]
    bbs = [s.BoundingBox() for n, s in solids]
    out = []
    for i, (n, s) in enumerate(solids):
        near = [j for j in range(len(solids)) if j != i and overlaps(bbs[i], bbs[j], 0.1)]
        if not any(s.distance(solids[j][1]) < 0.05 for j in near):
            out.append(n)
    return out


def main():
    report = dict(positions=[], floating=None)
    ok = True
    for name, kw in POSITIONS:
        items = E.set_instances(**kw)
        c = clashes(items)
        print('%-36s %3d parts  clashes: %d' % (name, len(items), len(c)))
        for x in c:
            print('   ', x)
        ok &= not c
        report['positions'].append(dict(position=name, parts=len(items), clashes=c))
    fl = floating(E.set_instances())
    print('floating parts:', fl or 'none')
    ok &= not fl
    report['floating'] = fl
    d = os.path.join(ROOT, 'docs', 'ESP 2026', 'qa')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'assembly_checks.json'), 'w') as f:
        json.dump(report, f, indent=1)
    print('PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
