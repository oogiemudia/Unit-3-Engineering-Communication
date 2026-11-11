"""ESP 2025 Task 2 drawings: the A3 sheets for the automated pill dispenser, made from the CAD model (models/esp2025.py).

  ESP25-GA-01  General arrangement: front, plan and side views 1:2, isometric, sub-assemblies and notes
  ESP25-GA-02  Sections A-A (front to back) and B-B (side to side) 1:1, and the specification check
  ESP25-GA-03  Details: pharmacy lock and lid catch (2:1), worm drive (2:1), control panel (2:1)
  ESP25-GA-04  Part A design ideas: design A (round carousel) and design B (trapdoor cassette)
  ESP25-GA-05  Parts list (all 37 parts) with a ballooned view of the dispenser
  ESP25-GA-06  The six sub-assemblies, exploded, with their parts ballooned
  ESP25-GA-07  Assembly structure and order of assembly

Output: docs/ESP 2025/drawings/ESP25-GA-0n_*.svg and .png.
Run from the repository root:  python3 tools/esp2025_drawings.py [1 2 3 4 5 6 7]
"""
import math, os, sys
import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import esp2025 as E  # noqa: E402
import drawings as D  # noqa: E402
from esp2023_drawings import View, place, text_block, leader, section_view, comp  # noqa: E402
from esp2024_drawings import table, iso_fit, balloon, iproj, centre  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'ESP 2025', 'drawings')
OWNER, DATE = 'WBEP Ltd for the health trust', '2026-11-10'
EXTRA_STYLE = ('<style>.ph{fill:none;stroke:#555;stroke-width:0.25;stroke-dasharray:6,1.2,1,1.2,1,1.2}'
               '.box{fill:none;stroke:#111;stroke-width:0.3}.tbl{fill:none;stroke:#111;stroke-width:0.25}'
               '.lead{fill:none;stroke:#111;stroke-width:0.2}</style>')
NO = {p['key']: p['no'] for p in E.PARTS}
D.FAR_AXES['skip'] = True     # sections and details: no centre lines for axes outside the cut pieces
_N = {}


def calc():
    """Size, mass, battery, drive and cost numbers from the calculation sheet (computed once)."""
    if not _N:
        import esp2025_calcs as C
        _N.update(C.numbers())
    return _N


def finish(sh, name, title, number, scale, doctype='Assembly drawing', material='See parts list'):
    sh.add(EXTRA_STYLE)
    D.frame(sh, title, number, scale, 'third', material, doctype, OWNER, DATE)
    D.save(sh, name, OUT)
    print('drew', name, flush=True)


def items_of(keep=None, base=None):
    base = base if base is not None else E.dispenser_instances()
    return [(n, s, E.colour(k)) for n, k, s in base if keep is None or keep(n, k)]


def lead(sh, V, p, dx, dy, text, size=2.2):
    q = V.P(p)
    leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, text, size, 'start' if dx > 0 else 'end')


def _range(group):
    nos = [p['no'] for p in E.PARTS if p['group'] == group]
    return '%d-%d' % (nos[0], nos[-1])


# ------------------------------------------------------------------ GA-01 general arrangement
def ga01():
    sh = D.Sheet()
    n = calc()
    s = 1 / 2
    allc = comp(items_of())
    bb = allc.BoundingBox()
    # front view
    Fd, fox, foy = place(allc, 'front', s, 40, 40, hidden=False)
    F = View(sh, None, 'front', s, fox, foy, data=Fd)
    fx0, fy0, fx1, fy1 = F.bb()
    sh.text((fx0 + fx1) / 2, fy0 - 12, 'FRONT VIEW, 1:2', size=3, weight='bold')
    a, b = F.P((-E.R_CASE, 0, bb.zmin)), F.P((E.R_CASE, 0, bb.zmin))
    D.dim_h(sh, a[0], b[0], fy1 + 6, a[1], 'Ø%d' % (2 * E.R_CASE))
    a, b = F.P((E.R_CASE, 0, bb.zmax)), F.P((E.R_CASE, 0, bb.zmin))
    D.dim_v(sh, a[1], b[1], fx1 + 8, a[0], '%.0f' % (bb.zmax - bb.zmin))
    a, b = F.P((-E.DRAWER_OPEN[0], 0, E.DRAWER_OPEN[1])), F.P((E.DRAWER_OPEN[0], 0, E.DRAWER_OPEN[1]))
    D.dim_h(sh, a[0], b[0], fy1 + 13, a[1], '%d DRAWER' % (2 * E.DRAWER_OPEN[0]))
    lead(sh, F, (E.BTN[0], 0, E.LID_Z[1] + 1), 10, -9, 'PRESS HERE BUTTON (%d)' % NO['button'])
    lead(sh, F, (-E.R_CASE + 3, 0, E.LID_Z[0] + 10), -6, -8, 'CLEAR LID (%d)' % NO['lid'])
    # plan, under the front view (third angle)
    Pd, pox, poy = place(allc, 'plan', s, 40, fy1 + 24, hidden=False)
    P = View(sh, None, 'plan', s, pox, poy, data=Pd)
    px0, py0, px1, py1 = P.bb()
    sh.text((px0 + px1) / 2, py1 + 8, 'PLAN, 1:2', size=3, weight='bold')
    a, b = P.P((E.R_CASE, bb.ymin, 0)), P.P((E.R_CASE, bb.ymax, 0))
    D.dim_v(sh, a[1], b[1], px1 + 8, a[0], '%.0f' % (bb.ymax - bb.ymin))
    lead(sh, P, (E.polar(E.R_CASE, E.LOCK_ANG)[0], E.polar(E.R_CASE, E.LOCK_ANG)[1], 0), 22, 12,
         'PHARMACY LOCK (%d)' % NO['pharmacy_lock'])
    lead(sh, P, (E.R_CASE * 0.3, E.HINGE[0] + 1, 0), 12, -6, 'HINGE (%d)' % NO['hinge_pin'])
    lead(sh, P, (0, bb.ymin, 0), -26, 6, 'DRAWER (%d)' % NO['drawer'])
    # side view, from the right
    Rd, rox, roy = place(allc, 'right', s, 150, 40, hidden=False)
    R = View(sh, None, 'right', s, rox, foy, data=Rd)
    rx0, ry0, rx1, ry1 = R.bb()
    sh.text((rx0 + rx1) / 2, fy0 - 12, 'SIDE VIEW, 1:2', size=3, weight='bold')
    a, b = R.P((0, bb.ymin, bb.zmin)), R.P((0, bb.ymax, bb.zmin))
    D.dim_h(sh, a[0], b[0], fy1 + 6, a[1], '%.0f' % (bb.ymax - bb.ymin))
    # isometric
    iso_fit(sh, allc, 150, 92, 104, 80, d=(-1, -1.4, 0.9))
    sh.text(202, 180, 'ISOMETRIC (NOT TO SCALE)', size=3, weight='bold')
    # sub-assemblies and notes
    rows = [('Items', 'Sub-assembly', 'File')] + [
        (_range(d['key']), 'SA%d %s' % (d['no'], d['title']), d['file']) for d in E.SUBS]
    yb = table(sh, 268, 24, (13, 62, 61), rows, title='SUB-ASSEMBLIES (FULL LIST ESP25-GA-05)')
    sz = n['size']
    cap = n['capacity']
    text_block(sh, 268, yb + 7, [
        'NOTES',
        '1. Dimensions in millimetres. Do not scale.',
        '2. Overall %.0f x %.0f x %.0f (brief 190 x 190 x 60).' % sz,
        '3. Mass %.0f g with 4 AAA cells (brief 500 g max).' % (n['mass'] * 1000),
        '4. 28 compartments + 2 capped blanks on a carousel at 12°:',
        '    once a day for 28 days or twice a day for 14 days.',
        '5. Each compartment holds %d of the largest pills (Ø5 x 20);' % cap['total'],
        '    the brief asks for 3.',
        '6. At a dose time the buzzer sounds and the light beside the',
        '    PRESS HERE button flashes until the button is pressed; the',
        '    carousel turns one step and the pills drop into the drawer.',
        '7. The lid is held by a pharmacy key cam lock (%d, %d):' % (NO['pharmacy_lock'], NO['lock_cam']),
        '    only the pharmacy can open it to refill.',
        '8. Sealed: lid and cover gaskets (%d), pod O-ring (%d),' % (NO['gasket'], NO['pod_oring']),
        '    door seals (%d), drawer seal (%d).' % (NO['door_seal'], NO['drawer_seal']),
        '9. Case parts polypropylene (recycling code 5), marked PP 5.',
        '10. Each part has its own drawing ESP25-Pnn (nn = item).',
    ], size=2.3)
    finish(sh, 'ESP25-GA-01_general_arrangement', 'ESP 2025 pill dispenser, GA', 'ESP25-GA-01', 'AS SHOWN')


# ------------------------------------------------------------------ GA-02 sections
def label(sh, V, p, x1, y1, text, size=2.2):
    """A leader from the model point p to a label whose elbow is at (x1, y1) on the paper; the text runs away from the
    view (to the left of the elbow if the elbow is left of the point)."""
    q = V.P(p)
    leader(sh, q[0], q[1], x1, y1, text, size, 'start' if x1 >= q[0] else 'end')


def ga02():
    sh = D.Sheet()
    n = calc()
    items = items_of()
    crop = ((-100, 100), (-100, 100), (-10, 60))
    skip = ('screw', 'cell', 'pin', 'sensor', 'switch', 'light', 'buzzer', 'display', 'board', 'foot')
    # A-A: on the centre line, front to back, seen from the right (the front is on the left)
    A = section_view(sh, items, 'x', 0, -1, 'right', crop, 1, 52, 32, None, hatch_mm=1.0, skip=skip)
    ax0, ay0, ax1, ay1 = A.bb()
    sh.text((ax0 + ax1) / 2, ay1 + 18, 'SECTION A-A, FRONT TO BACK ON THE CENTRE LINE, 1:1', size=3, weight='bold')
    a, b = A.P((0, E.R_CASE, 0)), A.P((0, E.R_CASE, E.LID_Z[1]))
    D.dim_v(sh, a[1], b[1], ax1 + 6, a[0], '%d' % E.LID_Z[1])
    for p, x1, y1, t in (((0, -60, E.CAR_Z[1] - 4), 50, 40, 'COMPARTMENT (%d)' % NO['carousel']),
                         ((0, -55, E.DECK[0] + 1), 50, 56, 'DECK, DROP HOLE (%d)' % NO['chassis']),
                         ((0, -72, E.CHUTE[1] + 3), 50, 66, 'CHUTE (%d)' % NO['chute']),
                         ((0, -75, E.DRAWER[1] + 1), 50, 78, 'DRAWER (%d)' % NO['drawer']),
                         ((0, 0, E.LID_Z[1] + 1), 120, 22, 'CONTROL POD (SA4)'),
                         ((0, 60, E.LID_Z[1] - 1), 232, 22, 'CLEAR LID (%d)' % NO['lid']),
                         ((0, E.HINGE[0], E.HINGE[1]), 252, 46, 'HINGE PIN (%d)' % NO['hinge_pin']),
                         ((0, E.GEAR_RP, E.GEAR_Z[1]), 214, ay1 + 8, 'GEAR (%d), WORM (%d)' % (NO['drive_gear'], NO['worm'])),
                         ((0, 30, E.COVER[1] - 1), 120, ay1 + 8, 'BOTTOM COVER (%d)' % NO['bottom_cover'])):
        label(sh, A, p, x1, y1, t)
    # B-B: side to side, seen from the front
    B = section_view(sh, items, 'y', 0, 1, 'front', crop, 1, 56, 140, None, hatch_mm=1.0, skip=skip)
    bx0, by0, bx1, by1 = B.bb()
    sh.text((bx0 + bx1) / 2, by1 + 20, 'SECTION B-B, SIDE TO SIDE ON THE CENTRE LINE, 1:1', size=3, weight='bold')
    a, b = B.P((-E.R_CASE, 0, 0)), B.P((E.R_CASE, 0, 0))
    D.dim_h(sh, a[0], b[0], by1 + 5, a[1], 'Ø%d' % (2 * E.R_CASE))
    for p, x1, y1, t in (((-E.R_CASE + 1, 0, E.CH_Z[1] + 0.5), 52, 140, 'GASKET (%d)' % NO['gasket']),
                         ((-E.GROOVE[2] - 1, 0, (E.GROOVE[0] + E.GROOVE[1]) / 2), 52, 150, 'O-RING (%d)' % NO['pod_oring']),
                         ((-E.POD_R[1] + 1, 0, 20), 52, 166, 'POD COLUMN (%d)' % NO['pod_column']),
                         ((-E.BAT_X[0], 0, E.BAT_ZC), 52, 184, 'AAA CELLS (%d)' % NO['battery']),
                         ((E.BAT_X[1] + 4, 0, E.BAT_ZC + 4), 248, 168, 'HOLDER (%d)' % NO['battery_holder']),
                         ((E.DOOR[0] + 6, 0, -1.5), 248, 196, 'BATTERY DOOR (%d)' % NO['battery_door'])):
        label(sh, B, p, x1, y1, t)
    sh.text(22, 240, 'Section planes A-A and B-B are the two centre lines of the plan on ESP25-GA-01.', size=2.3, anchor='start')
    # specification check
    c = n['costs']['cases']
    rows = [('Brief', 'This design'),
            ('190 x 190 x 60 max', '%.0f x %.0f x %.0f' % n['size']),
            ('500 g max with batteries', '%.0f g' % (n['mass'] * 1000)),
            ('3 pills (Ø5 x 20) each', '%d of the largest' % n['capacity']['total']),
            ('28 days once, 14 twice', '28 compartments'),
            ('Battery powered', '4 x AAA, %.0f days' % n['battery']['days']),
            ('Alarm until dispensed', 'Buzzer until pressed'),
            ('PRESS HERE, flashing light', 'Button %d, light %d' % (NO['button'], NO['led'])),
            ('Tamper proof', 'Self-locking worm'),
            ('Pharmacy lock', 'Keyed cam lock (%d)' % NO['pharmacy_lock']),
            ('Waterproof', 'Gaskets, O-ring, seals'),
            ('Recyclable casing', 'PP code 5, %.0f %% of mass' % (100 * n['recycle']['share'])),
            ('Repeated use', 'Refill, reprogram by NFC'),
            ('£%d each (1500)' % c[0]['target'], '£%.2f each' % c[0]['unit']),
            ('£%d each (3000)' % c[1]['target'], '£%.2f each' % c[1]['unit'])]
    table(sh, 290, 30, (52, 63), rows, h=4.6, size=2.1, title='SPECIFICATION CHECK')
    dr = n['drive']
    text_block(sh, 290, 112, [
        'HOW A DOSE IS GIVEN',
        '1. At the dose time the buzzer (%d) sounds and the' % NO['buzzer'],
        '    light (%d) flashes beside the PRESS HERE button (%d).' % (NO['led'], NO['button']),
        '2. The patient presses the button: the motor (%d)' % NO['gear_motor'],
        '    turns the worm (%d) %d times, the gear (%d) 4 teeth' % (NO['worm'], dr['turns'], NO['drive_gear']),
        '    and the carousel 12°, in %.1f s.' % dr['t_step'],
        '3. The next compartment comes over the drop hole and',
        '    the pills fall down the chute (%d) into the drawer (%d).' % (NO['chute'], NO['drawer']),
        '4. The drop sensors (%d) see them fall; the alarm stops.' % NO['drop_sensor'],
        '5. The home sensor (%d) under the gear sees the hole' % NO['home_sensor'],
        '    in it once a turn: the position is checked every turn.',
        '',
        'The worm is self-locking (lead %.1f°, friction %.1f°):' % (dr['lead'], dr['fric']),
        'the carousel cannot be turned by hand to the next dose.',
    ], size=2.3)
    finish(sh, 'ESP25-GA-02_sections', 'ESP 2025 sections A-A and B-B', 'ESP25-GA-02', '1:1')


# ------------------------------------------------------------------ GA-03 details
def ga03():
    import esp2025_calcs as C
    sh = D.Sheet()
    n = calc()
    base = E.dispenser_instances()
    # C: lock and catch. Turn the dispenser so the lock is at the front, then cut through the cam arm and the hook.
    turn = -90 - E.LOCK_ANG
    rot = [(nm, k, E.rotz(s_, turn)) for nm, k, s_ in base]
    near = items_of(keep=lambda nm, k: k in ('chassis', 'pharmacy_lock', 'lock_cam', 'lid', 'lid_catch', 'gasket',
                                             'bottom_cover', 'carousel'), base=rot)
    sc = 2
    xc = (max(E.CATCH['x'][0], -11.5) + E.CATCH['x'][1]) / 2      # through the cam arm and the hook
    C_ = section_view(sh, near, 'x', xc, -1, 'right', ((-40, 40), (-96, -70), (-4, 56)), sc, 24, 30, None, hatch_mm=0.8,
                      skip=('lock',))
    cx0, cy0, cx1, cy1 = C_.bb()
    for p, y1, t in (((xc, -E.R_CASE - 1, E.LOCK_Z + 5), 104, 'CAM LOCK (%d)' % NO['pharmacy_lock']),
                     ((xc, -sum(E.CAM_R) / 2, E.LOCK_Z + 2), 116, 'CAM (%d), LOCKED' % NO['lock_cam']),
                     ((xc, -sum(E.CATCH['r']) / 2, 36), 70, 'LID CATCH (%d)' % NO['lid_catch']),
                     ((xc, -E.R_CASE + 1, E.CH_Z[1] + 0.5), 52, 'GASKET (%d)' % NO['gasket']),
                     ((xc, -84, E.LID_Z[1] - 1), 38, 'LID (%d)' % NO['lid']),
                     ((xc, -84, E.DECK[0] + 1), 84, 'DECK (%d)' % NO['chassis'])):
        label(sh, C_, p, cx1 + 8, y1, t)
    sh.text(50, cy1 + 10, 'DETAIL C: LOCK AND LID CATCH, 2:1', size=3, weight='bold')
    sh.text(50, cy1 + 14, '(section through the cam and the hook)', size=2.2)
    fea = n['fea']
    ch = n['catch']
    text_block(sh, 18, cy1 + 22, [
        'The cam (%d) lies on the hook of the catch (%d):' % (NO['lock_cam'], NO['lid_catch']),
        'the lid cannot be lifted. A quarter turn of the',
        'pharmacy key turns the cam up, clear of the hook.',
        'Checked for a %d N pry on the lid edge:' % C.PRY,
        '  hand calculation %.1f MPa, safety factor %.1f;' % (ch['total'], ch['sf']),
        '  FEA peak %.1f MPa, safety factor %.1f' % (fea.get('vm_max', 0), fea.get('sf_min', 0)),
        '  (PP-GF30, yield %d MPa).' % C.CATCH_YIELD,
    ], size=2.3)
    # D: worm drive, section at the worm axis height, seen from above
    drive = items_of(keep=lambda nm, k: k in ('drive_gear', 'worm', 'gear_motor', 'motor_clamp', 'bottom_cover', 'carousel'))
    sd = 2
    Dv = section_view(sh, drive, 'z', E.WORM_ZC, -1, 'plan', ((-12, E.MOTOR_X[1] + 3), (34, 62), (-4, 20)), sd, 118, 40,
                      None, hatch_mm=0.8, skip=('motor',))
    dx0, dy0, dx1, dy1 = Dv.bb()
    dr = n['drive']
    for p, x1, y1, t in (((0, E.WORM_Y + E.WORM_R[0], E.WORM_ZC), 128, 26, 'WORM (%d), MODULE %g' % (NO['worm'], E.GEAR_M)),
                         ((40, E.WORM_Y + 5, E.WORM_ZC), 200, 26, 'GEAR MOTOR (%d)' % NO['gear_motor']),
                         ((sum(E.CLAMP_X) / 2, E.WORM_Y - 7, E.WORM_ZC), 236, dy1 + 7, 'CLAMP (%d)' % NO['motor_clamp']),
                         ((-6, E.GEAR_RP - 4, E.WORM_ZC), 150, dy1 + 7, 'DRIVE GEAR (%d), %d TEETH' % (NO['drive_gear'], E.GEAR_N))):
        label(sh, Dv, p, x1, y1, t)
    sh.text((dx0 + dx1) / 2, dy1 + 16, 'DETAIL D: WORM DRIVE, 2:1', size=3, weight='bold')
    sh.text((dx0 + dx1) / 2, dy1 + 20, '(section at the worm axis, %g above the base, looking down)' % E.WORM_ZC, size=2.2)
    text_block(sh, 118, dy1 + 28, [
        'Ratio %d:1. Torque at the carousel %.1f N mm (full of pills);' % (dr['ratio'], dr['T_car'] * 1000),
        'motor torque needed %.2f N mm, safety factor %.0f.' % (dr['T_motor'] * 1000, dr['sf']),
        'The worm is self-locking: its lead angle (%.1f°) is less than' % dr['lead'],
        'the friction angle (%.1f°), so the gear cannot drive the worm.' % dr['fric'],
    ], size=2.3)
    # E: control panel, plan of the pod
    pod = items_of(keep=lambda nm, k: E.sub_of(nm) == 'pod')
    se = 2
    Pd, pox, poy = place(comp(pod), 'plan', se, 258, 46)
    Pv = View(sh, None, 'plan', se, pox, poy, data=Pd)
    ex0, ey0, ex1, ey1 = Pv.bb()
    a, b = Pv.P((-E.POD_R[1], 0, 0)), Pv.P((E.POD_R[1], 0, 0))
    D.dim_h(sh, a[0], b[0], ey0 - 5, a[1], 'Ø%d' % (2 * E.POD_R[1]))
    for p, x1, y1, t in (((E.BTN[0] - 6, E.BTN[1] - 8, 0), 300, ey1 + 7, 'PRESS HERE BUTTON (%d)' % NO['button']),
                         ((E.LED_XY[0], E.LED_XY[1], 0), 352, ey1 + 7, 'FLASHING LIGHT (%d, %d)' % (NO['led'], NO['led_lens'])),
                         ((E.BUZ_XY[0], E.BUZ_XY[1], 0), 262, ey1 + 7, 'BUZZER (%d)' % NO['buzzer']),
                         ((-8, 12, 0), 262, 34, 'DISPLAY (%d), WINDOW (%d)' % (NO['lcd'], NO['display_window']))):
        label(sh, Pv, p, x1, y1, t)
    sh.text((ex0 + ex1) / 2, ey1 + 16, 'DETAIL E: CONTROL PANEL, 2:1', size=3, weight='bold')
    text_block(sh, 262, ey1 + 24, [
        'The flashing light is next to the button, as the brief asks.',
        'The display shows the time, the next dose and the battery.',
        'The button, lens and window flanges are clamped by the',
        'cap (%d) on silicone: the panel is sealed.' % NO['pod_cap'],
    ], size=2.3)
    finish(sh, 'ESP25-GA-03_details', 'ESP 2025 dispenser details', 'ESP25-GA-03', 'AS SHOWN', 'Detail drawing')


# ------------------------------------------------------------------ GA-04 Part A design ideas
def ga04():
    sh = D.Sheet()
    n = calc()
    A = comp(items_of())
    B = comp([(p, s_, c) for p, s_, c in E.cassette_dispenser()])
    for shp, title, x in ((A, 'DESIGN A: ROUND CAROUSEL (PREFERRED)', 16), (B, 'DESIGN B: TRAPDOOR CASSETTE', 212)):
        iso_fit(sh, shp, x, 18, 110, 110, d=(-1, -1.4, 0.9))
        s = 1 / 4
        Fd, fox, foy = place(shp, 'front', s, x + 130, 40, hidden=False)
        Fv = View(sh, None, 'front', s, fox, foy, data=Fd)
        b = Fv.bb()
        sh.text((b[0] + b[2]) / 2, b[3] + 5, 'FRONT, 1:4', size=2.2)
        Pd, pox, poy = place(shp, 'plan', s, x + 130, b[3] + 14, hidden=False)
        Pv = View(sh, None, 'plan', s, pox, poy, data=Pd)
        b2 = Pv.bb()
        sh.text((b2[0] + b2[2]) / 2, b2[3] + 5, 'PLAN, 1:4', size=2.2)
        sh.text(x + 92, 140, title, size=3.4, weight='bold')
    bb = B.BoundingBox()
    text_block(sh, 16, 148, [
        'Ø%d round polypropylene case. A carousel of 28 compartments' % (2 * E.R_CASE),
        'turns over a deck with one drop hole, driven by a worm and a',
        'small gear motor. Control pod in the middle: display, buzzer,',
        'PRESS HERE button and the flashing light beside it. Clear lid',
        'locked by a pharmacy key. Pills fall into a pull-out drawer.',
        'Mass %.0f g, %.0f x %.0f x %.0f.' % ((n['mass'] * 1000,) + tuple(n['size'])),
    ], size=2.4)
    text_block(sh, 212, 148, [
        '%.0f x %.0f x %.0f rectangular case. 28 compartments in 4 rows' % (bb.xlen, bb.ylen, bb.zlen),
        'of 7, each with its own spring trapdoor held by a small solenoid',
        'latch. At a dose time one latch lets go and the pills drop into',
        'a tray along the front. Display and button on the front.',
        'No turning parts, but 28 latches, 28 places for water to get in',
        'and too wide to hold in one hand.',
    ], size=2.4)
    c = n['costs']['cases'][0]
    rows = [('Requirement', 'Design A', 'Design B'),
            ('190 x 190 x 60 max', '%.0f x %.0f x %.0f' % n['size'], '%.0f x %.0f x %.0f' % (bb.xlen, bb.ylen, bb.zlen)),
            ('500 g with batteries', '%.0f g (CAD)' % (n['mass'] * 1000), 'About 600 g (28 latches)'),
            ('3 pills a compartment', '%d of the largest' % n['capacity']['total'], 'About 8'),
            ('Battery life', '%.0f days on 4 AAA' % n['battery']['days'], 'Latches use more power'),
            ('Tamper proof', 'Self-locking worm', 'Latch can be forced'),
            ('Waterproof', '4 seals, O-ring', '28 trapdoors to seal'),
            ('Cost each (1500)', '£%.2f' % c['unit'], 'About £80 (28 latches)'),
            ('Parts to assemble', '%d' % n['parts'], 'Over 100')]
    table(sh, 16, 192, (48, 48, 48), rows, h=4.6, size=2.25, title='COMPARISON AGAINST THE BRIEF')
    text_block(sh, 172, 196, [
        'WHY DESIGN A',
        'It meets every point of the brief with one motor in place of 28',
        'latches, so it is lighter, cheaper and uses less power. Only four',
        'joints need sealing, and the self-locking worm stops anyone',
        'turning the carousel to reach the next dose early.',
    ], size=2.4)
    finish(sh, 'ESP25-GA-04_design_ideas', 'ESP 2025 design ideas A and B', 'ESP25-GA-04', 'AS SHOWN', 'Design sketch',
           'See notes')


# ------------------------------------------------------------------ GA-05 parts list
def ga05():
    sh = D.Sheet()
    base = E.dispenser_instances()
    rows = E.bom([nm for nm, k, s_ in base], base)
    rows.sort(key=lambda r: r['no'])
    x, y, hh = 14, 18, 5.4
    wd = (9, 44, 9, 86, 46)
    W = sum(wd)
    sh.text(x, y - 2, 'PARTS LIST: ONE PILL DISPENSER', size=3.2, anchor='start', weight='bold')
    lines = [('h', ('Item', 'Part', 'Qty', 'Material and finish', 'Part file / drawing'))]
    g = None
    for r in rows:
        if r['group'] != g:
            g = r['group']
            lines.append(('g', dict(E.GROUPS)[g].upper()))
        lines.append(('r', (r['no'], r['name'], r['qty'], r['material'], '%s  ESP25-P%02d' % (r['file'], r['no']))))
    hh = min(hh, (282 - y) / len(lines))
    yy = y
    for kind, row in lines:
        if kind == 'g':
            sh.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#EEF2F6" stroke="#111" stroke-width="0.25"/>' % (x, yy, W, hh))
            sh.text(x + 1.2, yy + hh * 0.72, row, size=2.0, anchor='start', weight='bold')
        else:
            xx = x
            for c, cell in enumerate(row):
                sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (xx, yy, wd[c], hh))
                txt = str(cell)
                limit = int(wd[c] / 1.05)
                if len(txt) > limit:
                    txt = txt[:limit - 1] + '…'
                sh.text(xx + 1.0, yy + hh * 0.72, txt, size=1.95, anchor='start', weight='bold' if kind == 'h' else 'normal')
                xx += wd[c]
        yy += hh
    total = sum(r['qty'] for r in rows)
    # ballooned isometric, lid open so the inside shows
    shown = E.posed(base, cam=90, lid=100)
    ox, oy, si = iso_fit(sh, comp([(nm, s_, None) for nm, k, s_ in shown]), 236, 26, 150, 170, d=(-1, -1.4, 0.9))
    sh.text(312, 20, 'THE DISPENSER, LID OPEN (%d PARTS)' % total, size=3, weight='bold')
    hidden = {'main_pcb', 'battery_holder', 'battery', 'gear_motor', 'motor_clamp', 'worm', 'home_sensor', 'chute',
              'drop_sensor', 'drive_gear', 'panel_pcb', 'lcd', 'tact_switch', 'led', 'buzzer', 'pod_oring', 'pod_column',
              'lock_cam', 'door_seal', 'gasket', 'security_screw', 'battery_door', 'foot', 'cover_screw', 'drawer_seal'}
    first = {}
    for nm, k, s_ in shown:
        if k not in hidden and k not in first:
            first[k] = centre(s_)
    first['chassis'] = E.polar(E.R_CASE, -150, 18)
    first['bottom_cover'] = E.polar(E.R_CASE, -120, 1)
    first['carousel'] = E.polar(70, 160, E.CAR_Z[1])
    first['pharmacy_lock'] = E.polar(E.R_CASE + 1, E.LOCK_ANG, E.LOCK_Z)
    first['drawer'] = (0, -90, 15)
    pt = lambda p, lid=0: E.lid_open(cq.Workplane().add(cq.Vertex.makeVertex(*p)), lid).val().toTuple() if lid else p
    first['lid'] = pt((0, 60, E.LID_Z[1]), 100)
    first['hinge_pin'] = (-E.R_CASE * 0.45, E.HINGE[0], E.HINGE[1])
    marks = []
    for k, c in first.items():
        px, py = iproj(c)
        marks.append((NO[k], ox + px * si, oy - py * si))
    cx = 312
    left = sorted([m for m in marks if m[1] < cx], key=lambda m: m[2])
    right = sorted([m for m in marks if m[1] >= cx], key=lambda m: m[2])
    for col, bxp in ((left, 238), (right, 396)):
        k = len(col)
        for j, (no, px, py) in enumerate(col):
            byp = 30 + j * (160 / max(1, k - 1))
            balloon(sh, px, py, bxp, byp, no)
    hid = sorted(NO[k] for k in hidden)
    text_block(sh, 236, 206, [
        '%d different parts, %d parts in one dispenser.' % (len(rows), total),
        'Not seen in this view (inside or underneath): items',
        ', '.join(str(v) for v in hid[:13]) + ',',
        ', '.join(str(v) for v in hid[13:]) + '.',
        'See the sections ESP25-GA-02, the details ESP25-GA-03 and',
        'the exploded sub-assemblies ESP25-GA-06. Each part has its own',
        'STEP file, drawing ESP25-Pnn and Inventor build steps.',
    ], size=2.3)
    finish(sh, 'ESP25-GA-05_parts_list', 'ESP 2025 parts list', 'ESP25-GA-05', 'NTS', 'Parts list')


# ------------------------------------------------------------------ GA-06 exploded sub-assemblies
def exploded(key):
    d = E.SUB[key]
    return [(nm, k, s_.translate(d['explode'].get(nm, (0, 0, 0)))) for nm, k, s_ in E.sub_items(key)]


def ga06():
    sh = D.Sheet()
    cells = [(14 + c * 132, 16 + r * 117) for r in range(2) for c in range(3)]
    for (x, y), d in zip(cells, E.SUBS):
        cw, ch = 130, 114
        items = exploded(d['key'])
        sh.add('<rect class="thin" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (x, y, cw, ch))
        sh.text(x + 2, y + 5, 'SA%d %s' % (d['no'], d['title'].upper()), size=3, anchor='start', weight='bold')
        sh.text(x + 2, y + 9, d['file'] + ', exploded', size=2.2, anchor='start')
        ox, oy, si = iso_fit(sh, comp([(nm, s_, None) for nm, k, s_ in items]), x + 14, y + 12, cw - 28, 74, d=(-1, -1.4, 0.9))
        cx = x + cw / 2
        seen = {}
        for nm, k, s_ in items:
            px, py = iproj(centre(s_))
            seen.setdefault(NO[k], (ox + px * si, oy - py * si))
        left = sorted([(no, p) for no, p in seen.items() if p[0] < cx], key=lambda t: t[1][1])
        right = sorted([(no, p) for no, p in seen.items() if p[0] >= cx], key=lambda t: t[1][1])
        for col, bx in ((left, x + 5), (right, x + cw - 5)):
            k = len(col)
            for j, (no, (px, py)) in enumerate(col):
                by = (y + 16 + j * (70 / (k - 1))) if k > 1 else min(max(py, y + 16), y + 86)
                balloon(sh, px, py, bx, by, no)
        rows = E.bom([nm for nm, k, s_ in E.sub_items(d['key'])], E.sub_items(d['key']))
        lines = ['%d  %s x%d' % (r['no'], r['name'], r['qty']) for r in rows]
        half = (len(lines) + 1) // 2 if len(lines) > 6 else len(lines)
        for j, t in enumerate(lines):
            col, row = (0, j) if j < half else (1, j - half)
            sh.text(x + 2 + col * 64, y + 93 + row * 2.6, t[:42], size=1.8, anchor='start')
    sh.text(14, 252, 'Numbers are the items on the parts list (ESP25-GA-05). Order of assembly: ESP25-GA-07.', size=2.4,
            anchor='start')
    finish(sh, 'ESP25-GA-06_sub_assemblies', 'ESP 2025 sub-assemblies, exploded', 'ESP25-GA-06', 'NTS')


# ------------------------------------------------------------------ GA-07 assembly structure and order
def ga07():
    import esp2025_steps as ST
    sh = D.Sheet()
    x, y = 16, 20
    sh.text(x, y, 'ASSEMBLY STRUCTURE', size=3.2, anchor='start', weight='bold')
    y += 6
    base = E.dispenser_instances()
    sh.text(x, y, 'esp2025_dispenser.iam  (%d parts)' % len(base), size=2.5, anchor='start', weight='bold')
    yy = y + 4.5
    for d in E.SUBS:
        items = E.sub_items(d['key'])
        rows = E.bom([nm for nm, k, s_ in items], items)
        sh.line(x + 2, yy - 4.0, x + 2, yy - 0.8, 'thin')
        sh.line(x + 2, yy - 0.8, x + 5, yy - 0.8, 'thin')
        sh.text(x + 6, yy, 'SA%d %s  (%s)' % (d['no'], d['title'], d['file']), size=2.2, anchor='start', weight='bold')
        yy += 3.0
        for r in rows:
            sh.text(x + 10, yy, '%2d  %s  x%d' % (r['no'], r['name'], r['qty']), size=1.85, anchor='start')
            yy += 2.45
        yy += 0.8
    sh.line(x + 2, yy - 4.0, x + 2, yy - 0.8, 'thin')
    sh.line(x + 2, yy - 0.8, x + 5, yy - 0.8, 'thin')
    sh.text(x + 6, yy, '%d  cover screw  x4 (placed in the top level)' % NO['cover_screw'], size=2.0, anchor='start', weight='bold')
    stages = ST.dispenser_steps()
    sh.text(254, 20, 'ORDER OF ASSEMBLY (BUILD STEPS OF THE DISPENSER)', size=3.2, weight='bold')
    cw, chh = 64, 66
    for i, stg in enumerate(stages):
        r, c = divmod(i, 4)
        cx, cy = 110 + c * (cw + 2), 25 + r * (chh + 3)
        sh.add('<rect class="thin" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (cx, cy, cw, chh))
        shape = comp([(nm, s_, None) for nm, s_, c_ in stg['parts']])
        iso_fit(sh, shape, cx + 3, cy + 8, cw - 6, chh - 13, d=(-1, -1.4, 0.9))
        sh.text(cx + 2, cy + 4.5, '%d. %s' % (i + 1, stg['title']), size=2.4, anchor='start', weight='bold')
        sh.text(cx + cw - 2, cy + chh - 2, '%d parts' % len(stg['parts']), size=2.0, anchor='end')
    text_block(sh, 110, 170, [
        'HOW TO READ THIS SHEET',
        'Left: the assembly structure. The top level assembly, esp2025_dispenser.iam, is made from six sub-assemblies,',
        'each its own .iam, and the four cover screws. Under each sub-assembly are its parts, with the item numbers of',
        'the parts list (ESP25-GA-05). Right: the order the dispenser is put together, with the parts placed so far.',
        '',
        '1. Build each sub-assembly first, from its parts (exploded views on ESP25-GA-06).',
        '2. Place the chassis and ground it. Drop the carousel in from the top; put the control pod up through its hub.',
        '3. Press the drive gear onto the hub from underneath, then fit the base: the worm meets the gear.',
        '4. Screw the cover on (4 screws squeeze the gasket). Fit the lid with its hinge pin, lock it, push the drawer in.',
        '5. Check for interference: no parts overlap at any position (docs/ESP 2025/qa/assembly_checks.json).',
        '',
        'Every step, with the Inventor command to use, is on the Build steps tab of each model.',
    ], size=2.4)
    finish(sh, 'ESP25-GA-07_assembly_order', 'ESP 2025 assembly structure and order', 'ESP25-GA-07', 'NTS')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['1', '2', '3', '4', '5', '6', '7']
    for k in which:
        dict(zip('1234567', (ga01, ga02, ga03, ga04, ga05, ga06, ga07)))[k]()
