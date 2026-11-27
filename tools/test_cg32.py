"""Checks for the CG 3.2 drawings folder (models/cg32.py): the City and Guilds criterion 3.2 drawings as CAD models.

Run:  python tools/test_cg32.py

For every model, points just inside and just outside the faces the City and Guilds drawing dimensions are tested
against the solid, so each size given on the drawing is checked to 0.1 mm. Then each model's last build step must be
the finished model, and every part must be one valid solid.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import cadquery as cq  # noqa: E402
import parts  # noqa: E402
import inventor_steps as st  # noqa: E402

IN = 25.4
# (what the drawing says, point, should the point be in material?)
CHECKS = dict(
    cg_projection_block=[('length 45', (44.9, 10, 1), True), ('length 45 (beyond)', (45.1, 10, 1), False)],
    cg_ten_plate=[
        ('75 long', (74.9, 5, 15), True), ('75 long (beyond)', (75.1, 5, 15), False),
        ('45 high', (30, 5, 44.9), True), ('45 high (above)', (30, 5, 45.1), False),
        ('10 x 5 step', (5, 5, 40.1), False), ('left edge 40 high', (5, 5, 39.9), True),
        ('notch from 10 + 49', (59.1, 5, 44), False), ('top edge to 59', (58.9, 5, 44), True),
        ('notch floor 12 + 11', (72, 5, 22.9), True), ('notch (above the floor)', (72, 5, 23.1), False),
        ('R10 in the notch', (60.5, 5, 24.5), True),
        ('chamfer 12 x 45 deg', (74, 5, 0.5), False), ('chamfer (inside)', (62, 5, 0.5), True),
        ('hole 10 at 10, 10', (10, 5, 14.9), False), ('hole wall', (10, 5, 15.1), True),
        ('10 PLATE', (30, 9.9, 20), True), ('10 PLATE (behind)', (30, 10.1, 20), False),
    ],
    cg_notch_plate=[
        ('90 long', (89.9, 5, 25), True), ('90 long (beyond)', (90.1, 5, 25), False),
        ('step 20 x 10', (19.9, 5, 9.9), False), ('step corner', (20.1, 5, 10.1), True),
        ('vee 10 deep', (35.8, 5, 40.5), False), ('vee floor', (36, 5, 39.5), True),
        ('vee 15 wide', (44.9, 5, 49.95), False), ('top past the vee', (45.5, 5, 49.5), True),
        ('hole 10 at 15, 15', (75, 5, 19.9), False), ('hole wall', (75, 5, 20.1), True),
        ('R20 corner', (1, 5, 49), False), ('R10 corner', (89.5, 5, 49.5), False),
    ],
    cg_stepped_shaft=[
        ('50 +/- 1', (49.9, 0, 26), True), ('50 (step)', (50.1, 0, 26), False),
        ('120 +/- 2', (119.9, 0, 5), True), ('120 (beyond)', (120.1, 0, 5), False),
    ],
    cg_flanged_locator=[
        ('flange 2.000 dia', (0, 5, -0.999 * IN), True), ('flange (outside)', (0, 5, -1.001 * IN), False),
        ('flange 0.375 thick', (-0.9 * IN, 0.37 * IN, 0), True), ('flange 0.375 (behind)', (-0.9 * IN, 0.38 * IN, 0), False),
        ('bore 0.500', (0, 5, 0.249 * IN), False), ('bore wall', (0, 5, 0.26 * IN), True),
        ('boss 1.000 x 0.500', (0, 0.87 * IN, 0.49 * IN), True), ('boss length', (0, 0.876 * IN, 0.4 * IN), False),
        ('3 x 0.250 on 1.500 PCD', (0.75 * IN, 5, 0.12 * IN), False), ('next to the hole', (0.75 * IN, 5, 0.13 * IN), True),
        ('slot to 0.750 from centre', (0, 5, 0.76 * IN), False), ('below the slot', (0, 5, 0.74 * IN), True),
    ],
    cg_ws13_bracket=[
        ('base 100 x 120 x 20', (99.9, 1, 19.9), True), ('base 20 thick', (50, 30, 20.1), False),
        ('upright R25 top at 75', (50, 95, 99.9), True), ('above R25', (50, 95, 100.1), False),
        ('R10 hole', (50, 95, 84.9), False), ('R10 wall', (50, 95, 85.1), True),
        ('R7.5 hole 20, 20 from the corner', (80, 20 + 7.4, 10), False), ('hole wall', (80, 20 + 7.6, 10), True),
    ],
    cg_ws13_hanger=[
        ('plate 130', (64.9, 0, 2.5), True), ('plate 130 (beyond)', (65.1, 0, 2.5), False),
        ('plate 25', (0, 12.4, 2.5), True), ('plate 25 (beyond)', (0, 12.6, 2.5), False),
        ('6 holes', (57.5, 2.9, 2.5), False),
        ('web 100 at the top', (49.5, 0, -0.5), True), ('outside the web', (50.5, 0, -0.5), False),
        ('boss 40 dia at 125', (0, 7, -125 - 19.9), True), ('boss (outside)', (0, 7, -125 - 20.1), False),
        ('boss 15 long', (0, 7.4, -140), True), ('boss length (beyond)', (0, 7.6, -140), False),
        ('bore 20', (0, 0, -125 - 9.9), False), ('bore wall', (0, 0, -125 - 10.1), True),
        ('window', (0, 0, -50), False), ('15 arm', (-38, 0, -20), True),
    ],
    cg_ws13_clevis=[
        ('base 26', (25.9, 30, 1.5), True), ('base 26 (beyond)', (26.1, 30, 1.5), False),
        ('base 60', (13, 59.9, 1.5), True), ('base 60 (beyond)', (13, 60.1, 1.5), False),
        ('left side 4', (3.9, 30, 30), True), ('between sides', (4.1, 30, 30), False),
        ('right side 3', (23.1, 30, 30), True), ('right side (beyond)', (26.1, 30, 30), False),
        ('top 20 at 35', (2, 39.9, 34.9), True), ('top 20 (beyond)', (2, 40.1, 34.9), False),
        ('6 holes 42 apart, 9 from the end', (13, 9, 1.5), False), ('', (13, 51, 1.5), False),
        ('countersink', (13, 9 + 4.6, 2.9), False), ('countersink (outside)', (13, 9 + 5.2, 2.9), True),
        ('boss 24', (-2, 30, 22 + 11.9), True), ('boss (outside)', (-2, 30, 22 + 12.1), False),
        ('12 hole in the right side', (24.5, 30, 22 + 5.9), False),
    ],
)
for kind, d, (h0, h1), (s0, s1) in (('clearance', 42, (42.000, 42.062), (41.820, 41.920)),
                                     ('transition', 57, (57.000, 57.030), (57.020, 57.039)),
                                     ('interference', 80, (80.000, 80.030), (80.059, 80.078))):
    CHECKS['cg_fit_' + kind] = [('bore %g' % d, (d / 2 - 0.05, 30, 0), 'Shaft'), ('collar %g' % (d + 30), (d / 2 + 14.9, 10, 0), 'Housing')]


def inside(shape, p):
    return shape.val().isInside(cq.Vector(*p))


def main():
    bad = 0
    cg = [m for m in parts.MODELS if m.get('folder') == 'CG 3.2 drawings']
    assert len(cg) == 14, len(cg)
    for m in cg:
        items = m['fn']()
        steps = st.STEPS[m['name']]()
        for name, shape, colour in items:
            if not shape.val().isValid() or len(shape.solids().vals()) != 1:
                print('FAIL', m['name'], name, 'not one valid solid'); bad += 1
        last = {n: s for n, s, c in steps[-1]['parts']}
        for name, shape, colour in items:
            if abs(last[name].val().Volume() - shape.val().Volume()) > 1e-3:
                print('FAIL', m['name'], name, 'last build step is not the finished part'); bad += 1
        for what, p, want in CHECKS.get(m['name'], []):
            if isinstance(want, str):
                got = inside(dict((n, s) for n, s, c in items)[want], p)
                want = True
            else:
                got = inside(items[0][1], p)
            if got != want:
                print('FAIL', m['name'], what, p, 'in material' if got else 'empty'); bad += 1
        print('ok' if not bad else '..', m['name'], len(steps), 'steps')
    print('checks failed:', bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
