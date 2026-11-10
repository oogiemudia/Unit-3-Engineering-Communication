"""ESP 2024 assembly checks: clashes between every pair of parts and parts that touch nothing (floating), for the
red buoy, the green buoy and the sinker. The buoy has no moving parts in service except the chain and swivel, so
it is checked as built. A clash is a shared volume of more than 1 mm3. A part floats if it is more than 0.05 mm
from every other part. Writes docs/ESP 2024/qa/assembly_checks.json.
Run from the repository root:  python3 tools/esp2024_checks.py
"""
import itertools, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import esp2024 as E  # noqa: E402

ASSEMBLIES = [('red buoy (leaving the harbour)', lambda: E.buoy_instances('red')),
              ('green buoy (entering the harbour)', lambda: E.buoy_instances('green')),
              ('sinker and ground chain', E.sinker_items)]


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
    report = dict(assemblies=[])
    ok = True
    for name, fn in ASSEMBLIES:
        items = fn()
        c = clashes(items)
        fl = floating(items)
        print('%-36s %3d parts  clashes: %d  floating: %s' % (name, len(items), len(c), fl or 'none'))
        for x in c:
            print('   ', x)
        ok &= not c and not fl
        report['assemblies'].append(dict(assembly=name, parts=len(items), clashes=c, floating=fl))
    d = os.path.join(ROOT, 'docs', 'ESP 2024', 'qa')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'assembly_checks.json'), 'w') as f:
        json.dump(report, f, indent=1)
    print('PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
