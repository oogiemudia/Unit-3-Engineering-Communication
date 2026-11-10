"""ESP 2025 assembly checks: clashes between every pair of parts, and parts that touch nothing (floating), for the
pill dispenser at each position of its motion: closed and locked at home; the carousel part way through a step
and one step on; the drawer pulled out; the cam unlocked; the lid open 2.5, 5, 15, 30, 60 and 100 degrees. A clash is a shared
volume of more than 1 mm3. A part floats if it is more than 0.05 mm from every other part (checked closed).
Also checks the size and mass against the brief. Writes docs/ESP 2025/qa/assembly_checks.json.
Run from the repository root:  python3 tools/esp2025_checks.py
"""
import itertools, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import cadquery as cq  # noqa: E402
import esp2025 as E  # noqa: E402

POSITIONS = [('closed, locked, carousel at home', dict()),
             ('carousel half way through a step (6 degrees)', dict(carousel=6)),
             ('carousel one step on (12 degrees)', dict(carousel=12)),
             ('carousel at the last dose (28 steps, 336 degrees)', dict(carousel=336)),
             ('drawer pulled out 35 mm', dict(drawer=35)),
             ('cam unlocked (90 degrees)', dict(cam=90)),
             ('lid open 2.5 degrees', dict(cam=90, lid=2.5)),
             ('lid open 5 degrees', dict(cam=90, lid=5)),
             ('lid open 15 degrees', dict(cam=90, lid=15)),
             ('lid open 30 degrees', dict(cam=90, lid=30)),
             ('lid open 60 degrees', dict(cam=90, lid=60)),
             ('lid open 100 degrees', dict(cam=90, lid=100))]


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


def main(quick=False):
    base = E.dispenser_instances()
    report = dict(positions=[])
    ok = True
    for k, (name, pose) in enumerate(POSITIONS[:1] if quick else POSITIONS):
        items = E.posed(base, **pose)
        c = clashes(items)
        fl = floating(items) if k == 0 else []
        print('%-50s %3d parts  clashes: %d  floating: %s' % (name, len(items), len(c), fl or 'none'), flush=True)
        for x in c:
            print('   ', x)
        ok &= not c and not fl
        report['positions'].append(dict(position=name, parts=len(items), clashes=c, floating=fl))
    # the lock works: with the cam locked, lifting the lid 1 degree must push the catch into the cam
    its = [x for x in E.posed(base, lid=1) if x[0] in ('lock cam', 'lid catch')]
    held = bool(clashes(its))
    print('locked lid lifted 1 degree: the catch hits the cam:', 'yes, the lid is held' if held else 'NO, the lock does not hold')
    ok &= held
    report['lock_holds'] = held
    # invalid solids
    bad = [p['key'] for p in E.PARTS if not E.shape(p['key']).val().isValid() or len(E.shape(p['key']).solids().vals()) != 1]
    print('parts that are not one valid solid:', bad or 'none')
    ok &= not bad
    comp = cq.Compound.makeCompound([s.val() for n, k, s in base])
    bb = comp.BoundingBox()
    size = [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]
    mass = E.total_mass(base)
    print('overall size %s mm (brief 190 x 190 x 60), mass %.0f g (brief 500 g max)' % (size, mass * 1000))
    ok &= bb.xlen <= 190 and bb.ylen <= 190 and bb.zlen <= 60 and mass <= 0.5
    report.update(size=size, mass_kg=round(mass, 4), invalid=bad, ok=ok)
    d = os.path.join(ROOT, 'docs', 'ESP 2025', 'qa')
    os.makedirs(d, exist_ok=True)
    if not quick:
        with open(os.path.join(d, 'assembly_checks.json'), 'w') as f:
            json.dump(report, f, indent=1)
    print('PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main('--quick' in sys.argv)
