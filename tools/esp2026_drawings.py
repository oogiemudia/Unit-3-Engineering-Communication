"""ESP 2026 Task 2 drawings: the fully dimensioned A3 sheets for the economy three-seat set, made from the CAD model.

  ESP26-GA-01  General arrangement, 1:10: plan, front view, end view with the reclined back chain dotted,
               isometric, parts summary and notes
  ESP26-GA-02  Single seat: section A-A on the seat centre line (1:5) with the reclined back and the tray down
               chain dotted, view B on the back of the seat (1:8), and the specification check
  ESP26-GA-03  Details: recline mechanism, armrest pivot, seat belt buckle and track fitting
  ESP26-GA-04  Part A design ideas: design A (beam and leg seat) and design B (fixed shell seats), with notes
  ESP26-GA-05  Parts list (bill of materials) for all the parts, with a ballooned view of the set

Output: docs/ESP 2026/drawings/ESP26-GA-0n_*.svg and .png.
Run from the repository root:  python3 tools/esp2026_drawings.py [1 2 3 4 5]
"""
import json, math, os, sys
import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import esp2026 as E  # noqa: E402
import drawings as D  # noqa: E402
from esp2023_drawings import View, place, phantom, text_block, leader, arc_dim, section_view, parts_list, comp  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'ESP 2026', 'drawings')
OWNER, DATE = 'Aero-Chair Ltd', '2026-11-10'
EXTRA_STYLE = ('<style>.ph{fill:none;stroke:#555;stroke-width:0.25;stroke-dasharray:6,1.2,1,1.2,1,1.2}'
               '.note{font-size:2.6px}.box{fill:none;stroke:#111;stroke-width:0.3}.tbl{fill:none;stroke:#111;stroke-width:0.25}'
               '.lead{fill:none;stroke:#111;stroke-width:0.2}.floor{fill:none;stroke:#111;stroke-width:0.35}</style>')
D.VIEWS['rear'] = ((0, 1, 0), (-1, 0, 0))     # looking at the back of a seat, from the row behind

NO = {p['key']: p['no'] for p in E.PARTS}


def finish(sh, name, title, number, scale, doctype='Assembly drawing', material='See parts list'):
    sh.add(EXTRA_STYLE)
    D.frame(sh, title, number, scale, 'third', material, doctype, OWNER, DATE)
    D.save(sh, name, OUT)
    print('drew', name)


def bbox(items):
    return comp(items).BoundingBox()


def floor(sh, a, b):
    """The cabin floor line with short hatch marks under it."""
    sh.line(a[0], a[1], b[0], b[1], 'floor')
    x = a[0] + 1
    while x < b[0] - 1:
        sh.line(x, a[1], x - 1.6, a[1] + 1.6, 'thin')
        x += 3


def leg_fea():
    f = os.path.join(ROOT, 'docs', 'ESP 2026', 'fea', 'esp2026_p04_leg.json')
    if os.path.exists(f):
        r = json.load(open(f))['results']
        return r['vm_max'], r['sf_min']
    return 0.0, 0.0


def _range(group):
    nos = [p['no'] for p in E.PARTS if p['group'] == group]
    return '%d-%d' % (nos[0], nos[-1]) if len(nos) > 1 else str(nos[0])


def set_items(**kw):
    return [(n, s, E.colour(k)) for n, k, s in E.set_instances(**kw)]


# ------------------------------------------------------------------ GA-01 general arrangement
def ga01():
    sh = D.Sheet()
    s = 1 / 10
    items = set_items()
    allc = comp(items)
    bb = allc.BoundingBox()
    # plan, top left
    P_data, pox, poy = place(allc, 'plan', s, 30, 22, hidden=False)
    P = View(sh, None, 'plan', s, pox, poy, data=P_data)
    px0, py0, px1, py1 = P.bb()
    sh.text((px0 + px1) / 2, py0 - 3, 'PLAN', size=3.0, weight='bold')
    a, b = P.P((bb.xmax, bb.ymin, 0)), P.P((bb.xmax, bb.ymax, 0))
    D.dim_v(sh, b[1], a[1], px1 + 8, px1, '%.0f' % (bb.ymax - bb.ymin))
    a = P.P((0, -80, 0))
    sh.text(a[0], py1 + 4.5, 'FORWARD (PASSENGERS FACE THIS WAY)', size=2.3)
    D.arrow(sh, a[0], py1 + 9.5, 90, 2.2)
    sh.line(a[0], py1 + 5.5, a[0], py1 + 9.5, 'thin')
    # front view, under the plan (third angle), same x
    top = py1 + 26
    F_data, fox, foy = place(allc, 'front', s, 30, top, hidden=False)
    fox = pox
    F = View(sh, None, 'front', s, fox, foy, data=F_data)
    fx0, fy0, fx1, fy1 = F.bb()
    a, b = F.P((-1000, 0, 0)), F.P((1000, 0, 0))
    floor(sh, (fx0 - 6, a[1]), (fx1 + 6, a[1]))
    sh.text(fx1 + 1, a[1] - 1, 'FLOOR', size=2.2, anchor='start')
    sh.text((fx0 + fx1) / 2, fy1 + 30, 'FRONT VIEW', size=3.0, weight='bold')
    # widths under the front view
    a, b = F.P((bb.xmin, 0, 0)), F.P((bb.xmax, 0, 0))
    D.dim_h(sh, a[0], b[0], fy1 + 22, a[1], '%.0f OVERALL' % (bb.xmax - bb.xmin))
    a, b = F.P((E.LEGS[0], 0, 0)), F.P((E.LEGS[1], 0, 0))
    D.dim_h(sh, a[0], b[0], fy1 + 14, a[1] + 2, '%d LEGS' % (E.LEGS[1] - E.LEGS[0]))
    for x0, x1 in ((E.SEATS[0], E.SEATS[1]), (E.SEATS[1], E.SEATS[2])):
        a, b = F.P((x0, 0, 0)), F.P((x1, 0, 0))
        D.dim_h(sh, a[0], b[0], fy1 + 7, F.P((0, 0, 200))[1], '%d' % (x1 - x0))
    # seat width between the armrests, above the middle seat
    a, b = F.P((-E.SEAT_W / 2, 0, E.ARM_Z[1])), F.P((E.SEAT_W / 2, 0, E.ARM_Z[1]))
    D.dim_h(sh, a[0], b[0], fy0 - 4, a[1], '%d SEAT' % E.SEAT_W)
    a, b = F.P((E.SEATS[2] + E.SEAT_W / 2, 0, E.ARM_Z[1])), F.P((E.SEATS[2] + E.SEAT_W / 2 + E.ARM_W, 0, E.ARM_Z[1]))
    sh.text(b[0] + 1, a[1] - 3, 'ARMREST %d' % E.ARM_W, size=2.2, anchor='start')
    # heights on the left
    z0 = F.P((bb.xmin, 0, 0))
    for k, (z, lab) in enumerate(((E.SEAT_H, '%d SEAT HEIGHT' % E.SEAT_H), (E.ARM_Z[1] + 8, '%d' % (E.ARM_Z[1] + 8)),
                                   (bb.zmax, '%.0f' % bb.zmax))):
        zz = F.P((bb.xmin, 0, z))
        D.dim_v(sh, zz[1], z0[1], fx0 - 6 - 7 * k, fx0, lab)
    # end view, right of the front view, with the reclined back chain dotted
    E_data, eox, eoy = place(allc, 'right', s, fx1 + 24, top, hidden=False)
    eoy = foy
    Ev = View(sh, None, 'right', s, eox, eoy, data=E_data)
    ex0, ey0, ex1, ey1 = Ev.bb()
    rec = [(n, s_, c) for n, s_, c in set_items(recline=(E.RECLINE,) * 3) if E.group_of(n) in ('back', 'tray')]
    phantom(sh, comp(rec), 'right', eox, eoy, s)
    a = Ev.P((0, -200, 0))
    floor(sh, (ex0 - 4, a[1]), (ex1 + 6, a[1]))
    sh.text((ex0 + ex1) / 2 - 8, ey0 - 12, 'END VIEW (FROM RIGHT)', size=3.0, weight='bold')
    a, b = Ev.P((0, E.FOOT_Y[0], 0)), Ev.P((0, E.FOOT_Y[1], 0))
    D.dim_h(sh, a[0], b[0], ey1 + 7, a[1] + 1, '%d TRACK' % (E.FOOT_Y[1] - E.FOOT_Y[0]))
    # back angles: 12 degrees upright, 17 reclined
    c = Ev.P((0, E.PIV[0], E.PIV[1]))
    sh.line(c[0], c[1], c[0], c[1] - 50, 'thin')
    arc_dim(sh, c, 46, -90, -90 + E.BACK_ANGLE, '', 0, 0)
    sh.text(c[0] + 1.2, c[1] - 48, '%d°' % E.BACK_ANGLE, size=2.4, anchor='start')
    up = E.back_point((0, 0, 800), 0, E.RECLINE)
    q = Ev.P(up)
    sh.text(q[0] - 2, q[1] - 5, 'RECLINED %d° (+%d°), CHAIN DOTTED' % (E.BACK_ANGLE + E.RECLINE, E.RECLINE), size=2.2, anchor='end')
    # isometric, top right
    D.ISO_DIR['d'] = (-1, -1.4, 0.8)
    I = D.view_data(allc, 'iso', hidden=False)
    iw, ih = I['bb'][2] - I['bb'][0], I['bb'][3] - I['bb'][1]
    si = min(110 / iw, 80 / ih)
    ix, iy = 292 - I['bb'][0] * si + (110 - iw * si) / 2, 18 + I['bb'][3] * si
    D.draw_view(sh, I, ix, iy, si)
    sh.text(347, 102, 'ISOMETRIC VIEW (NOT TO SCALE)', size=3.0, weight='bold')
    rows = [(_range('structure'), 'Beams, legs, spreaders, track fittings', '1 set', '7075-T6 aluminium, recycled'),
            (_range('seat'), 'Seat pans, cushions, backs, head rests', 3, 'Carbon fibre, FR foam, wool blend'),
            (_range('recline'), 'Recline locks and buttons', 3, 'Hydraulic lock, stainless pins'),
            (_range('armrest'), 'Lift up armrests', 4, 'PA6 GF30 recycled, TPE pad'),
            (_range('belt'), 'Lap belts, lift lever buckles', 3, 'Polyester webbing, aluminium'),
            (_range('amenity'), 'Trays, screens, pockets, life vests', 3, 'Honeycomb panel, bought in')]
    yb = parts_list(sh, 292, 110, [list(r) for r in rows], widths=(10, 50, 10, 42), title='PARTS (FULL LIST ON ESP26-GA-05)')
    m = E.set_mass()
    text_block(sh, 292, yb + 6, [
        'NOTES',
        '1. Dimensions in millimetres. Heights above the cabin floor. Do not scale.',
        '2. Seat width %d between the armrests (spec: 432 to 457).' % E.SEAT_W,
        '3. Backs %d° from vertical upright, %d° reclined (%d° recline, spec 3 to 6).' % (
            E.BACK_ANGLE, E.BACK_ANGLE + E.RECLINE, E.RECLINE),
        '4. Mass of the set %.1f kg without life vests: %.2f kg a seat (spec: 8 kg).' % (m, m / 3),
        '5. Legs fixed to the seat tracks by 4 track fittings (5) and studs (6),',
        '    at any 25.4 mm pitch, so the airline chooses the seat pitch.',
        '6. Each part has its own drawing ESP26-Pnn (nn = item number).',
        '7. Hidden detail left off for clarity: see GA-02 and the part drawings.',
    ], size=2.3)
    finish(sh, 'ESP26-GA-01_general_arrangement', 'ESP 2026 three-seat set, GA', 'ESP26-GA-01', '1:10')


# ------------------------------------------------------------------ GA-02 single seat
def middle(n):
    """Items for the drawings of the middle seat: the seat itself, the frame either side, the armrest to its left."""
    if n.startswith('seat 2 '):
        return True
    if n.startswith('seat '):
        return False
    return n in ('front beam tube', 'rear beam tube', 'spreader 2', 'leg 1', 'beam clamp collar 1a', 'beam clamp collar 1b',
                 'track fitting 1a', 'track fitting 1b', 'track stud 1a', 'track stud 1b', 'baggage bar',
                 'recline pivot pin 2', 'armrest 2', 'armrest pad 2', 'armrest pin 2', 'recline button 1')


def ga02():
    sh = D.Sheet()
    s = 1 / 5
    items = [(n, s_, c) for n, s_, c in set_items() if middle(n)]
    crop = ((-300, 0), (-120, 700), (-30, 1200))
    A = section_view(sh, items, 'x', 0, -1, 'right', crop, s, 42, 30, None, hatch_mm=1.4,
                     skip=('pin', 'stud', 'rod', 'buckle', 'tongue', 'webbing'))
    ax0, ay0, ax1, ay1 = A.bb()
    rec = [(n, s_, c) for n, s_, c in set_items(recline=(0, E.RECLINE, 0)) if n.startswith('seat 2') and E.group_of(n) == 'back']
    rec = [it for it in rec if 'arm' not in it[0]]
    phantom(sh, comp(rec), 'right', A.ox, A.oy, s)
    tray = [(n, s_, c) for n, s_, c in set_items(tray=(0, E.TRAY_DEPLOY, 0)) if n == 'seat 2 tray table']
    phantom(sh, comp(tray), 'right', A.ox, A.oy, s)
    f = A.P((0, -120, 0))
    floor(sh, (ax0 - 4, f[1]), (ax1 + 4, f[1]))
    sh.text((ax0 + ax1) / 2, 284, 'SECTION A-A ON THE SEAT CENTRE LINE, 1:5', size=3, weight='bold')
    # heights, left
    zs = [(E.SEAT_H, '%d SEAT HEIGHT' % E.SEAT_H), (E.ARM_Z[1] + 8, '%d ARMREST' % (E.ARM_Z[1] + 8))]
    bbz = bbox([(n, s_, c) for n, s_, c in items]).zmax
    zs.append((bbz, '%.0f' % bbz))
    for k, (z, lab) in enumerate(zs):
        a, b = A.P((0, -80, 0)), A.P((0, -80, z))
        D.dim_v(sh, b[1], a[1], ax0 - 7 - 7 * k, ax0 + 2 if k else a[0], lab)
    # cushion depth and track pitch, bottom
    a, b = A.P((0, E.CUSH_Y[0], E.SEAT_H)), A.P((0, E.CUSH_Y[1], E.CUSH_TOP_BACK))
    D.dim_h(sh, a[0], b[0], a[1] - 9, a[1], '%d' % (E.CUSH_Y[1] - E.CUSH_Y[0]))
    a, b = A.P((0, E.FOOT_Y[0], 0)), A.P((0, E.FOOT_Y[1], 0))
    D.dim_h(sh, a[0], b[0], f[1] + 8, f[1] + 1, '%d TRACK FITTINGS' % (E.FOOT_Y[1] - E.FOOT_Y[0]))
    # back angle and recline
    c = A.P((0, E.PIV[0], E.PIV[1]))
    sh.line(c[0], c[1], c[0], c[1] - 110, 'thin')
    arc_dim(sh, c, 90, -90, -90 + E.BACK_ANGLE, '', 0, 0)
    arc_dim(sh, c, 104, -90 + E.BACK_ANGLE, -90 + E.BACK_ANGLE + E.RECLINE, '', 0, 0)
    sh.text(c[0] - 2, c[1] - 88, '%d° UPRIGHT' % E.BACK_ANGLE, size=2.3, anchor='end')
    sh.text(c[0] - 2, c[1] - 102, '+%d° RECLINE' % E.RECLINE, size=2.3, anchor='end')
    # tray height when down
    h = E.back_point((0, E.TRAY_HINGE[0] + E.TT / 2, E.TRAY_HINGE[1]), 0)
    hp = A.P(h)
    far = A.P((0, h[1] + 260, h[2]))
    D.dim_v(sh, hp[1], f[1], far[0] + 8, far[0], '%.0f TRAY' % h[2])
    # leaders with item numbers
    def lead(p, dx, dy, text, anchor='start'):
        q = A.P(p)
        leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, text, 2.2, anchor)
    lead((0, 100, 410), -10, -40, 'CUSHION FOAM (%d), COVER (%d)' % (NO['seat_foam'], NO['seat_cover']), 'end')
    lead((0, 200, 355.7), 34, 8, 'DIAPHRAGM (%d)' % NO['seat_diaphragm'])
    lead((0, 330, 305), 22, 22, 'BEAM TUBE Ø50 (%d)' % NO['beam_tube'])
    lead((0, 150, 250), 25, 20, 'LIFE VEST (%d) IN POUCH (%d)' % (NO['life_vest'], NO['vest_pouch']))
    lead(E.back_point((0, -20, 450), 0), -22, 22, 'BACK FOAM (%d), COVER (%d)' % (NO['back_foam'], NO['back_cover']), 'end')
    lead(E.back_point((0, 44, 600), 0), 20, -30, 'CARBON BACK SHELL 1.2 (%d)' % NO['back_shell'])
    lead(E.back_point((0, -30, 760), 0), -16, -6, 'FIXED HEAD REST (%d)' % NO['headrest'], 'end')
    lead(E.back_point((0, 60, 650), 0), 22, -12, 'SCREEN (%d)' % NO['ife_screen'])
    lead(E.back_point((0, 60, 420), 0), 24, -8, 'TRAY (%d), DOWN CHAIN DOTTED' % NO['tray_table'])
    lead(E.back_point((0, 68, 150), 0), 22, 4, 'A4 POCKET (%d)' % NO['literature_pocket'])
    lead((0, 330, E.BELT_Z + 8), -6, -30, 'BUCKLE (%d, %d)' % (NO['buckle_body'], NO['buckle_lever']), 'end')
    # section line on a small key plan
    text_block(sh, 306, 148, ['KEY: A-A IS ON THE MIDDLE SEAT', 'CENTRE LINE, LOOKING LEFT.',
                             'Hatched: cut parts. Pins, studs and',
                             'belt parts are not sectioned.',
                             'Chain dotted: back reclined %d°,' % E.RECLINE, 'tray table folded down level.'], size=2.2)
    # view B: the back of the seat, true shape, upright
    sb = 1 / 8
    back = [(n.replace('seat 2 ', ''), k, s_) for n, k, s_ in [(n, k, tf(E.shape(k))) for n, k, tf in E.seat_instances(2, 0)]
            if E.group_of(n) in ('back', 'tray')]
    keys = {'back_shell', 'headrest', 'tray_table', 'tray_arm', 'tray_latch', 'ife_screen', 'usb_module', 'literature_pocket'}
    raw = [(n, E.shape(k) if 'left' not in n else E.shape(k).mirror('YZ'), E.colour(k))
           for n, k, s_ in back if k in keys]
    bc = comp(raw)
    B_data, box_, boy = place(bc, 'rear', sb, 240, 36)
    B = View(sh, None, 'rear', sb, box_, boy, data=B_data)
    bx0, by0, bx1, by1 = B.bb()
    sh.text((bx0 + bx1) / 2, by1 + 22, 'VIEW B: BACK OF THE SEAT (TRUE SHAPE), 1:8', size=3, weight='bold')
    TW, TL = E.TW, E.TL
    zt = E.TRAY_HINGE[1] - 8
    a, b = B.P((TW / 2, 60, zt)), B.P((-TW / 2, 60, zt))
    D.dim_h(sh, a[0], b[0], by1 + 15, by1, '%d TRAY' % TW)
    a, b = B.P((-TW / 2, 60, zt)), B.P((-TW / 2, 60, zt + TL))
    D.dim_v(sh, b[1], a[1], bx1 + 6, a[0], '%d' % TL)
    a, b = B.P((125, 60, 715)), B.P((-125, 60, 715))
    D.dim_h(sh, a[0], b[0], by0 - 3, a[1], '250 SCREEN')
    a, b = B.P((-125, 60, 555)), B.P((-125, 60, 715))
    D.dim_v(sh, b[1], a[1], bx1 + 6, a[0] + 6, '160')
    a, b = B.P((165, 60, 40)), B.P((-165, 60, 40))
    D.dim_h(sh, a[0], b[0], by1 + 7, by1, '330 POCKET')
    a, b = B.P((-165, 60, 40)), B.P((-165, 60, 255))
    D.dim_v(sh, b[1], a[1], bx1 + 6, a[0], '215')
    for p, dx, dy, t in (((0, 60, E.LATCH_Z), -16, -3, 'LATCH (%d)' % NO['tray_latch']),
                         ((165, 60, 625), -8, -26, 'USB-C, USB-A, AUDIO (%d)' % NO['usb_module']),
                         ((-212, 60, E.TRAY_HINGE[1]), 12, 8, 'HINGE ARM (%d)' % NO['tray_arm'])):
        q = B.P(p)
        leader(sh, q[0], q[1], q[0] + dx, q[1] + dy, t, 2.2, 'end' if dx < 0 else 'start')
    # specification check, right column
    m = E.set_mass()
    rows = [('Seat width 432 to 457', '%d between armrests' % E.SEAT_W),
            ('Suitable height', 'Seat %d, armrest %d' % (E.SEAT_H, E.ARM_Z[1] + 8)),
            ('Max 8 kg a seat', '%.2f kg (CAD mass)' % (m / 3)),
            ('Fixed to the floor', '4 track fittings + studs'),
            ('Manual recline 3 to 6°', '%d°, button on armrest' % E.RECLINE),
            ('Life vest 305 x 305', 'Pouch 316 x 336 inside'),
            ('Adjustable armrests', 'Lift 90°, all four'),
            ('Tray up to 267 x 419', '%d x %d, stows flat' % (TL, TW)),
            ('Fixed head rest', 'Item %d, no adjuster' % NO['headrest']),
            ('Belt 1170 to 1420', '1170 to 1420, lift lever'),
            ('A4 literature', 'Pocket 326 x 213 inside'),
            ('Screen and connections', '10.1 in, USB-C, USB-A, jack'),
            ('Fire resistant', 'FR foam, covers, resin'),
            ('70 % sustainable', 'See calculation sheet')]
    x, y, w = 306, 40, (52, 48)
    sh.text(x, y - 2, 'SPECIFICATION CHECK', size=3, anchor='start', weight='bold')
    for r, row in enumerate([('Product design specification', 'This design')] + rows):
        xx = x
        for c, cell in enumerate(row):
            sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="4.4"/>' % (xx, y + r * 4.4, w[c]))
            sh.text(xx + 1, y + r * 4.4 + 3.1, cell, size=2.05, anchor='start', weight='bold' if r == 0 else 'normal')
            xx += w[c]
    finish(sh, 'ESP26-GA-02_single_seat', 'ESP 2026 single seat', 'ESP26-GA-02', 'AS SHOWN')


# ------------------------------------------------------------------ GA-03 details
def ga03():
    sh = D.Sheet()
    items = set_items()
    seat2 = [it for it in items if middle(it[0])]
    # C: recline mechanism, section on the line of the recline lock, 1:2
    xl = E.LOCK_X
    C = section_view(sh, seat2, 'x', xl, -1, 'right', ((xl - 20, xl + 20), (25, 450), (255, 455)), 1 / 2, 28, 26, None,
                     hatch_mm=1.2, skip=('pin', 'rod', 'recline lock'))
    cx0, cy0, cx1, cy1 = C.bb()
    rec = [(n, s_, c) for n, s_, c in set_items(recline=(0, E.RECLINE, 0))
           if n in ('seat 2 recline lock rod', 'seat 2 back shell')]
    ph = [(n, w.val().intersect(cq.Solid.makeBox(40, 425, 200, cq.Vector(xl - 20, 25, 255))), c) for n, w, c in rec]
    ph = [(n, cq.Workplane().add(v), c) for n, v, c in ph]
    phantom(sh, comp(ph), 'right', C.ox, C.oy, 1 / 2)
    sh.text((cx0 + cx1) / 2, cy1 + 18, 'DETAIL C: RECLINE MECHANISM (SECTION ON THE LOCK), 1:2', size=3, weight='bold')
    anchor, rear, L0, _ = E.lock_line(0)
    _, rear1, L1, _ = E.lock_line(E.RECLINE)
    a, b = C.P((xl, *anchor)), C.P((xl, *rear))
    D.dim_h(sh, a[0], b[0], cy1 + 8, a[1], '%.1f PIN CENTRES (UPRIGHT)' % L0)
    p = C.P((xl, 150, 290))
    leader(sh, p[0], p[1] + 5.5, p[0] + 6, cy1 + 2, 'HYDRAULIC RECLINE LOCK (%d), ROD (%d)' % (NO['recline_lock'], NO['recline_rod']), 2.2)
    p = C.P((xl, 50, 300))
    leader(sh, p[0], p[1], p[0] + 2, cy1 + 2, 'BRACKET (%d) ON FRONT BEAM' % NO['recline_bracket'], 2.2)
    p = C.P((xl, rear[0] + 6, rear[1] + 40))
    leader(sh, p[0], p[1], p[0] + 14, p[1] - 22, 'BACK LEVER (%d)' % NO['back_shell'], 2.2)
    q = C.P((xl, rear1[0], rear1[1]))
    sh.text(q[0] - 3, q[1] + 9, 'RECLINED: %.1f (STROKE %.1f)' % (L1, L0 - L1), size=2.2, anchor='end')
    p = C.P((xl, E.PIV[0], E.PIV[1]))
    sh.text(p[0] + 4, p[1] - 6, 'PIVOT (%d)' % NO['back_pivot_pin'], size=2.2, anchor='start')
    # D: armrest pivot and lift, side view of armrest 2, 1:5
    arm = [it for it in items if it[0] in ('armrest 2', 'armrest pad 2', 'armrest pin 2', 'recline button 1', 'spreader 2')]
    sd = 1 / 5
    clip = cq.Solid.makeBox(60, 520, 480, cq.Vector(-280, -80, 520))
    armc = [(n, cq.Workplane().add(w.val().intersect(clip)), c) for n, w, c in arm]
    Dd, dox, doy = place(comp(armc), 'right', sd, 300, 92)
    Dv = View(sh, None, 'right', sd, dox, doy, data=Dd)
    up = [it for it in set_items(arms=(0, E.ARM_UP, 0, 0)) if it[0] in ('armrest 2', 'armrest pad 2', 'recline button 1')]
    phantom(sh, comp(up), 'right', dox, doy, sd)
    dx0, dy0, dx1, dy1 = Dv.bb()
    sh.text((dx0 + dx1) / 2, dy1 + 18, 'DETAIL D: ARMREST LIFTS 90° (CHAIN DOTTED), 1:5', size=3, weight='bold')
    c = Dv.P((-250, *E.ARM_PIV))
    a = Dv.P((-250, -40, E.ARM_Z[1]))
    D.dim_h(sh, a[0], c[0], dy1 + 7, c[1], '%d' % (E.ARM_PIV[0] + 40))
    leader(sh, c[0], c[1], c[0] - 12, c[1] + 14, 'PIVOT PIN Ø12 (%d)' % NO['armrest_pin'], 2.2, 'end')
    b = Dv.P((-250, -25, E.ARM_Z[1] + 7))
    leader(sh, b[0], b[1], b[0] - 3, b[1] - 14, 'RECLINE BUTTON (%d)' % NO['recline_button'], 2.2, 'end')
    sp = Dv.P((-250, 360, 540))
    sh.text(sp[0] + 7, sp[1] + 3, 'SPREADER (%d)' % NO['spreader'], size=2.2, anchor='start')
    # E: seat belt buckle and tongue, plan, 1:1
    belt = [it for it in items if it[0].startswith('seat 2 ') and any(t in it[0] for t in ('buckle', 'tongue', 'webbing'))]
    clip = cq.Solid.makeBox(150, 120, 100, cq.Vector(-80, 270, 380))
    beltc = [(n, cq.Workplane().add(w.val().intersect(clip)), c) for n, w, c in belt]
    beltc = [it for it in beltc if it[1].val().Volume() > 1]
    Ed, eox, eoy = place(comp(beltc), 'plan', 1, 30, 165)
    Ev = View(sh, None, 'plan', 1, eox, eoy, data=Ed)
    ex0, ey0, ex1, ey1 = Ev.bb()
    sh.text((ex0 + ex1) / 2, ey1 + 14, 'DETAIL E: LAP BELT BUCKLE, PLAN, 1:1', size=3, weight='bold')
    a, b = Ev.P((-50, 330, 0)), Ev.P((20, 330, 0))
    D.dim_h(sh, a[0], b[0], ey0 - 5, ey0, '70')
    a, b = Ev.P((20, E.BELT_Y[0] - 1, 0)), Ev.P((20, E.BELT_Y[1] + 1, 0))
    p = Ev.P((-15, 330, 0))
    leader(sh, p[0], p[1], p[0] - 10, ey1 + 6, 'LIFT LEVER (%d): LIFT TO OPEN' % NO['buckle_lever'], 2.2, 'end')
    p = Ev.P((50, 330, 0))
    leader(sh, p[0], p[1], p[0] + 4, ey1 + 6, 'TONGUE AND SLIDE BAR (%d)' % NO['belt_tongue'], 2.2)
    # F: track fitting, section on the leg, 1:1
    tf = [it for it in items if it[0] in ('leg 2', 'track fitting 2a', 'track stud 2a')]
    xf = E.LEGS[1]
    Fv = section_view(sh, tf, 'x', xf, -1, 'right', ((xf - 15, xf + 15), (-15, 60), (-22, 75)), 1, 207, 140, None,
                      hatch_mm=1.2, skip=('stud',))
    fx0, fy0, fx1, fy1 = Fv.bb()
    sh.text((fx0 + fx1) / 2, fy0 - 5, 'DETAIL F: TRACK FITTING, 1:1', size=3, weight='bold')
    a = Fv.P((xf, -25, 0))
    b = Fv.P((xf, 75, 0))
    floor(sh, (a[0], a[1]), (fx0, a[1]))
    floor(sh, (fx1, a[1]), (b[0], b[1]))
    a, b = Fv.P((xf, -10, 0)), Fv.P((xf, 50, 0))
    D.dim_h(sh, a[0], b[0], fy1 + 6, fy1, '60')
    a, b = Fv.P((xf, 50, 0)), Fv.P((xf, 50, 25))
    D.dim_v(sh, b[1], a[1], fx1 + 6, a[0], '25')
    p = Fv.P((xf, E.FOOT_Y[0], -16))
    leader(sh, p[0], p[1], p[0] - 22, p[1] + 4, 'TRACK STUD (%d) LOCKS IN THE SEAT TRACK' % NO['track_stud'], 2.2, 'end')
    p = Fv.P((xf, 40, 12))
    leader(sh, p[0], p[1], p[0] + 22, p[1] - 6, 'FITTING (%d)' % NO['track_fitting'], 2.2)
    p = Fv.P((xf, 35, 55))
    leader(sh, p[0], p[1], p[0] + 18, p[1] - 6, 'LEG (%d)' % NO['leg'], 2.2)
    vm, sf = leg_fea()
    text_block(sh, 303, 168, [
        'NOTES',
        '1. Recline: press the button (%d) and the hydraulic lock (%d) opens;' % (NO['recline_button'], NO['recline_lock']),
        '    lean back up to %d°. Let go and the back is held. Sit up and the' % E.RECLINE,
        '    back follows. Large button, light force: usable by all passengers.',
        '2. Armrests (%d) lift 90° on their pivot pins for access from the aisle.' % NO['armrest'],
        '3. Lap belt: lift lever buckle, opened with one movement of either hand,',
        '    by the passenger or the crew. Length 1170 to 1420 by the slide bar.',
        '4. Leg FEA, 9 g forward: peak %.0f MPa at the brace to boss corner,' % vm,
        '    safety factor %.1f on 7075-T6. Strut stresses agree with the hand' % sf,
        '    calculation (ESP26 calculation sheet, section 6).',
    ], size=2.3)
    finish(sh, 'ESP26-GA-03_mechanism_details', 'ESP 2026 mechanism details', 'ESP26-GA-03', 'AS SHOWN', 'Detail drawing')


# ------------------------------------------------------------------ GA-04 Part A design ideas
def ga04():
    sh = D.Sheet()
    A_items = set_items(recline=(0, E.RECLINE, 0), tray=(0, 0, 0), arms=(0, 0, 0, E.ARM_UP))
    B_items = E.shell_seats()
    for k, (its, title, x, iso) in enumerate(((A_items, 'DESIGN A: BEAM AND LEG SEAT (PREFERRED)', 18, (-1, -1.4, 0.8)),
                                             (B_items, 'DESIGN B: FIXED SHELL SEATS', 214, (-1, -1.4, 0.8)))):
        D.ISO_DIR['d'] = iso
        data = D.view_data(comp(its), 'iso', hidden=False)
        w, h = data['bb'][2] - data['bb'][0], data['bb'][3] - data['bb'][1]
        si = min(100 / w, 92 / h)
        ox, oy = x + (100 - w * si) / 2 - data['bb'][0] * si, 22 + data['bb'][3] * si
        D.draw_view(sh, data, ox, oy, si)
        # side elevation and plan, 1:20, beside the 3D view
        s = 1 / 25
        Sd, sox, soy = place(comp(its), 'right', s, x + 118, 30, hidden=False)
        View(sh, None, 'right', s, sox, soy, data=Sd)
        Pd, pox, poy = place(comp(its), 'plan', s, x + 108, 30 + (Sd['bb'][3] - Sd['bb'][1]) * s + 10, hidden=False)
        Pv = View(sh, None, 'plan', s, pox, poy, data=Pd)
        sh.text(x + 118 + 18, 26, 'SIDE, 1:25', size=2.2)
        pb = Pv.bb()
        sh.text((pb[0] + pb[2]) / 2, pb[3] + 4, 'PLAN, 1:25', size=2.2)
        sh.text(x + 60, 129, title, size=3.4, weight='bold')
    m = E.set_mass()
    text_block(sh, 18, 136, [
        'Two 50 mm aluminium beam tubes on two machined legs; four spreaders',
        'carry the armrests and the backs. Shown: middle back reclined, aisle armrest up.',
        'Seat pan: woven diaphragm on the tubes, 80 to 50 mm FR foam, wool cover.',
        'Back: 1.2 mm carbon fibre shell, 12° upright, reclines %d° on a hydraulic' % E.RECLINE,
        'lock released by a large button on the armrest. Fixed head rest.',
        'Belt: lap belt with a lift lever buckle on the centre line of the seat.',
        'Behind: tray %d x %d, 10.1 in screen, USB-C, A4 pocket. Vest pouch below.' % (E.TL, E.TW),
        'Mass from the CAD model: %.1f kg a set, %.2f kg a seat.' % (m, m / 3),
    ], size=2.4)
    text_block(sh, 214, 136, [
        'Three moulded composite shells on one box beam and two pedestal legs.',
        'Recline: the seat pan slides forward and tilts; the shell back is fixed,',
        'so a reclining passenger never reaches into the space of the one behind.',
        'Armrests are part of the shell: they cannot lift, so access is harder.',
        'Head rest moulded in; tray and screen in the fixed back.',
        'Mass estimate: shell 3.2 kg, slide 1.6 kg, beam share 1.4 kg, cushions,',
        'belt and fittings 3.3 kg: about 9.5 kg a seat. Over the 8 kg limit.',
        'Rejected: too heavy, costs more, fails the armrest and access needs.',
    ], size=2.4)
    rows = [('Seat width 432 to 457', '%d' % E.SEAT_W, '430'), ('Mass, 8 kg a seat max', '%.2f kg' % (m / 3), 'about 9.5 kg'),
            ('Recline 3 to 6°, by hand', '%d°, button' % E.RECLINE, '6°, lever and slide'),
            ('Adjustable armrests', 'Lift 90°', 'Fixed'), ('Access needs', 'Good: lift up arms', 'Poor'),
            ('Tray, screen, A4 pocket', 'Yes', 'Yes'), ('Life vest 305 x 305', 'Under seat pouch', 'In the shell base'),
            ('Cost to make a set', 'about £%s' % format(round(cost_estimate()), ','), 'about £6,900'),
            ('Sustainable materials', '%d %% by mass' % round(sustainable_share() * 100), 'about 45 %')]
    x, y, wds = 18, 176, (66, 40, 40)
    sh.text(x, y - 2, 'COMPARISON AGAINST THE PRODUCT DESIGN SPECIFICATION', size=3, anchor='start', weight='bold')
    for r, row in enumerate([('Requirement', 'Design A', 'Design B')] + rows):
        xx = x
        for c, cell in enumerate(row):
            sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="4.6"/>' % (xx, y + r * 4.6, wds[c]))
            sh.text(xx + 1.2, y + r * 4.6 + 3.3, cell, size=2.3, anchor='start', weight='bold' if r == 0 else 'normal')
            xx += wds[c]
    text_block(sh, 175, 178, [
        'WHY DESIGN A',
        'Design A meets every line of the specification. It is the lightest',
        '(%.2f kg a seat against 8 kg), so it saves fuel on every flight.' % (m / 3),
        'Every armrest lifts, so a passenger with access needs can transfer',
        'from an aisle wheelchair. Covers and cushions are changed in minutes.',
        'Calculations (cost, mass, size, seat height): ESP26 calculation sheet.',
    ], size=2.4)
    finish(sh, 'ESP26-GA-04_design_ideas', 'ESP 2026 design ideas A and B', 'ESP26-GA-04', 'AS SHOWN', 'Design sketch',
           'See notes')


def cost_estimate():
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import esp2026_calcs as C
    return C.costs()['total']


def sustainable_share():
    import esp2026_calcs as C
    return C.sustainability()['share']


# ------------------------------------------------------------------ GA-05 parts list
def ga05():
    sh = D.Sheet()
    rows = E._set_bom()
    x, y, h = 16, 18, 4.3
    wd = (9, 50, 9, 92, 50)
    heads = ('Item', 'Part', 'Qty', 'Material and finish', 'Part file / drawing')
    W = sum(wd)
    sh.text(x, y - 2, 'PARTS LIST: ONE THREE-SEAT SET', size=3.2, anchor='start', weight='bold')
    lines = [('h', heads)]
    g = None
    for r in rows:
        if r['group'] != g:
            g = r['group']
            lines.append(('g', dict(E.GROUPS)[g].upper()))
        mat = r['material'] + (' (bought in)' if r['bought'] and 'Bought' not in r['material'] else '')
        lines.append(('r', (r['no'], r['name'], r['qty'], mat.replace('Bought in: ', 'Bought in. '),
                            '%s  ESP26-P%02d' % (r['file'], r['no']))))
    yy = y
    for kind, row in lines:
        if kind == 'g':
            sh.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#EEF2F6" stroke="#111" stroke-width="0.25"/>' % (x, yy, W, h))
            sh.text(x + 1.2, yy + 3.1, row, size=2.15, anchor='start', weight='bold')
        else:
            xx = x
            for c, cell in enumerate(row):
                sh.add('<rect class="tbl" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (xx, yy, wd[c], h))
                txt = str(cell)
                limit = int(wd[c] / 1.12)
                if len(txt) > limit:
                    txt = txt[:limit - 1] + '…'
                sh.text(xx + 1.0, yy + 3.1, txt, size=2.1, anchor='start', weight='bold' if kind == 'h' else 'normal')
                xx += wd[c]
        yy += h
    total = sum(r['qty'] for r in rows)
    sh.text(x, yy + 4.5, '%d different parts, %d parts in all, for one three-seat set.' % (len(rows), total), size=2.4, anchor='start')
    # ballooned isometric of the set from the front
    items = E.set_instances(arms=(0, 0, 0, E.ARM_UP), tray=(0, 0, 0))
    D.ISO_DIR['d'] = (-1, -1.4, 0.8)
    data = D.view_data(comp([(n, s_, None) for n, k, s_ in items]), 'iso', hidden=False)
    bx0, by0, bx1, by1 = data['bb']
    si = min(110 / (bx1 - bx0), 150 / (by1 - by0))
    ox = 272 + (110 - (bx1 - bx0) * si) / 2 - bx0 * si
    oy = 34 + (150 - (by1 - by0) * si) / 2 + by1 * si
    D.draw_view(sh, data, ox, oy, si)
    sh.text(327, 22, 'THE SET FROM THE FRONT (AISLE ARMREST UP)', size=3, weight='bold')
    # one balloon per part, on an instance that can be seen from the front
    pick = {'beam_tube': 'front beam tube', 'beam_end_cap': 'beam end cap 3', 'spreader': 'spreader 4', 'leg': 'leg 2',
            'beam_collar': 'beam clamp collar 2a', 'track_fitting': 'track fitting 2a', 'track_stud': 'track stud 2a',
            'baggage_bar': 'baggage bar', 'seat_diaphragm': 'seat 3 diaphragm', 'seat_foam': 'seat 3 cushion foam',
            'seat_cover': 'seat 1 cushion cover', 'back_shell': 'seat 3 back shell', 'back_foam': 'seat 2 back cushion foam',
            'back_cover': 'seat 1 back cushion cover', 'headrest': 'seat 2 head rest', 'back_pivot_pin': 'recline pivot pin 3',
            'end_pivot_pin': 'recline pivot pin 4', 'recline_bracket': 'seat 3 recline lock bracket',
            'recline_lock': 'seat 3 recline lock', 'recline_rod': 'seat 3 recline lock rod', 'lock_pin': 'seat 3 recline lock pin, front',
            'recline_button': 'recline button 2', 'armrest': 'armrest 4', 'armrest_pad': 'armrest pad 2', 'armrest_pin': 'armrest pin 4',
            'belt_anchor': 'seat 1 belt anchor, left', 'belt_strap_buckle': 'seat 1 belt webbing, buckle side',
            'belt_strap_adjust': 'seat 1 belt webbing, adjuster side', 'buckle_body': 'seat 2 buckle body',
            'buckle_lever': 'seat 1 buckle lift lever', 'belt_tongue': 'seat 3 belt tongue',
            'vest_pouch': 'seat 1 life vest pouch', 'life_vest': 'seat 2 life vest'}
    inst = {n: (k, s_) for n, k, s_ in items}
    marks = []
    for key, nm in pick.items():
        k, s_ = inst[nm]
        bb = s_.val().BoundingBox()
        c = ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
        if key in ('beam_tube',):
            c = (-650, -25, E.BEAM_Z)
        if key == 'baggage_bar':
            c = (-600, E.BAR[0] - 10, E.BAR[1])
        if key in ('back_shell', 'back_foam', 'back_cover'):
            c = {'back_shell': (720, bb.ymin + 30, 900), 'back_foam': (100, bb.ymin + 10, 800),
                 'back_cover': (-600, bb.ymin + 5, 700)}[key]
        if key in ('seat_foam', 'seat_diaphragm', 'vest_pouch', 'life_vest'):
            c = {'seat_foam': (720, -82, 400), 'seat_diaphragm': (680, -10, 356), 'vest_pouch': (-500, -5, 275),
                 'life_vest': (0, -6, 270)}[key]
        px, py = D.proj(c, 'iso')
        marks.append((E.PART[key]['no'], ox + px * si, oy - py * si))
    cx = 272 + 55
    left = sorted([m for m in marks if m[1] < cx], key=lambda m: m[2])
    right = sorted([m for m in marks if m[1] >= cx], key=lambda m: m[2])
    for col, bxp in ((left, 266), (right, 392)):
        n = len(col)
        for j, (no, px, py) in enumerate(col):
            byp = 36 + j * (150 / max(1, n - 1)) if n > 1 else py
            sh.add('<line class="lead" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (px, py, bxp + (3 if bxp < cx else -3), byp))
            sh.add('<circle cx="%.2f" cy="%.2f" r="0.6" fill="#111"/>' % (px, py))
            sh.add('<circle class="box" cx="%.2f" cy="%.2f" r="3"/>' % (bxp, byp))
            sh.text(bxp, byp + 1.0, str(no), size=2.5, weight='bold')
    shown = sorted(E.PART[k]['no'] for k in pick)
    behind = [p['no'] for p in E.PARTS if p['no'] not in shown]
    text_block(sh, 262, 200, [
        'NOTES',
        '1. Items %s are on the back of each seat:' % ', '.join(str(n) for n in behind),
        '    see view B on ESP26-GA-02.',
        '2. Bought in items are modelled from the maker\'s catalogue sizes.',
        '3. Each part has its own drawing, ESP26-Pnn (nn = item), and its own',
        '    STEP file and Inventor build steps on the ESP 2026 project page.',
    ], size=2.3)
    finish(sh, 'ESP26-GA-05_parts_list', 'ESP 2026 parts list', 'ESP26-GA-05', 'NTS', 'Parts list')


# ------------------------------------------------------------------ GA-06 exploded sub-assemblies
def iso_fit(sh, shape, x, y, w, h, d=(-1, -1.3, 0.9)):
    """Draw an isometric (no hidden lines) to fit the box (x, y, w, h); returns (ox, oy, scale)."""
    D.ISO_DIR['d'] = d
    data = D.view_data(shape, 'iso', hidden=False)
    bx0, by0, bx1, by1 = data['bb']
    si = min(w / (bx1 - bx0), h / (by1 - by0))
    ox = x + (w - (bx1 - bx0) * si) / 2 - bx0 * si
    oy = y + (h - (by1 - by0) * si) / 2 + by1 * si
    D.draw_view(sh, data, ox, oy, si)
    return ox, oy, si


def balloon(sh, px, py, bx, by, no):
    sh.add('<line class="lead" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (px, py, bx, by))
    sh.add('<circle cx="%.2f" cy="%.2f" r="0.5" fill="#111"/>' % (px, py))
    sh.add('<circle class="box" cx="%.2f" cy="%.2f" r="2.6" fill="#fff"/>' % (bx, by))
    sh.text(bx, by + 0.9, str(no), size=2.3, weight='bold')


def exploded(key):
    """The parts of a sub-assembly moved apart by its explode offsets: (name, part key, shape)."""
    d = E.SUB[key]
    out = []
    for n, k, s_ in E.sub_items(key):
        dx, dy, dz = d['explode'].get(n, (0, 0, 0))
        out.append((n, k, s_.translate((dx, dy, dz))))
    return out


def ga06():
    sh = D.Sheet()
    cells = [(14 + c * 97, 16 + r * 116) for r in range(2) for c in range(4)]
    for (x, y), d in zip(cells, E.SUBS):
        items = exploded(d['key'])
        sh.add('<rect class="thin" x="%.2f" y="%.2f" width="95" height="112"/>' % (x, y))
        sh.text(x + 2, y + 5, 'SA%d %s' % (d['no'], d['title'].upper()), size=3, anchor='start', weight='bold')
        sh.text(x + 2, y + 9, d['file'] + ', exploded', size=2.2, anchor='start')
        ox, oy, si = iso_fit(sh, comp([(n, s_, None) for n, k, s_ in items]), x + 11, y + 14, 73, 76)
        # one balloon per part number, pushed out from the middle of the view
        cx, cy = x + 47.5, y + 52
        seen = {}
        for n, k, s_ in items:
            bb = s_.val().BoundingBox()
            px, py = D.proj(((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2), 'iso')
            seen.setdefault(E.PART[k]['no'], (ox + px * si, oy - py * si))
        left = sorted([(no, p) for no, p in seen.items() if p[0] < cx], key=lambda t: t[1][1])
        right = sorted([(no, p) for no, p in seen.items() if p[0] >= cx], key=lambda t: t[1][1])
        for col, bx in ((left, x + 4.5), (right, x + 90.5)):
            n = len(col)
            for j, (no, (px, py)) in enumerate(col):
                by = (y + 16 + j * (74 / (n - 1))) if n > 1 else min(max(py, y + 16), y + 90)
                balloon(sh, px, py, bx, by, no)
        rows = E.bom([n for n, k, s_ in E.sub_items(d['key'])], E.sub_items(d['key']))
        lines = ['%d  %s x%d' % (r['no'], r['name'], r['qty']) for r in rows]
        half = (len(lines) + 1) // 2 if len(lines) > 5 else len(lines)
        for j, t in enumerate(lines):
            col, row = (0, j) if j < half else (1, j - half)
            sh.text(x + 2 + col * 47, y + 96 + row * 2.9, t[:36], size=1.75, anchor='start')
    x, y = cells[7]
    text_block(sh, x + 2, y + 6, [
        'HOW THE SET IS BUILT',
        'Each sub-assembly is its own .iam,',
        'made from its parts (numbers are the',
        'items on the parts list, ESP26-GA-05).',
        '',
        'Top level, esp2026_seat_set.iam:',
        '  SA1 frame x1',
        '  SA2 seat pan x3',
        '  SA3 seat back x3',
        '  back pivot pins (16, 17) x2 + x2',
        '  SA4 recline lock x3',
        '  SA5 armrest x4 (button on 3)',
        '  SA6 lap belt x3',
        '  SA7 life vest pouch x3',
        '',
        'Order of assembly and the stages: ESP26-GA-07.',
        'Each sub-assembly has its own Inventor',
        'build steps on the project page.',
    ], size=2.3)
    finish(sh, 'ESP26-GA-06_sub_assemblies', 'ESP 2026 sub-assemblies, exploded', 'ESP26-GA-06', 'NTS')


# ------------------------------------------------------------------ GA-07 assembly structure and order
def ga07():
    import esp2026_steps as ST
    sh = D.Sheet()
    # the structure tree, left
    x, y = 16, 20
    sh.text(x, y, 'ASSEMBLY STRUCTURE', size=3.2, anchor='start', weight='bold')
    y += 6
    sh.text(x, y, 'esp2026_seat_set.iam  (128 parts)', size=2.5, anchor='start', weight='bold')
    groups = [(d['file'], 'SA%d %s' % (d['no'], d['title']), {1: 1, 2: 3, 3: 3, 4: 3, 5: 4, 6: 3, 7: 3}[d['no']],
               E.bom([n for n, k, s_ in E.sub_items(d['key'])], E.sub_items(d['key']))) for d in E.SUBS]
    order = [groups[0], groups[1], groups[2], ('pins', 'Back pivot pins', 1, [dict(no=16, name='recline pivot pin', qty=2),
                                                                             dict(no=17, name='end recline pivot pin', qty=2)])] + groups[3:]
    yy = y + 4.5
    for f, t, q, rows in order:
        sh.line(x + 2, yy - 4.2, x + 2, yy - 0.8, 'thin')
        sh.line(x + 2, yy - 0.8, x + 5, yy - 0.8, 'thin')
        label = '%s  (%s)  x%d' % (t, f, q) if f != 'pins' else '%s (placed at the top level)' % t
        sh.text(x + 6, yy, label, size=2.3, anchor='start', weight='bold')
        yy += 3.4
        for r in rows:
            sh.text(x + 10, yy, '%2d  %s  x%d' % (r['no'], r['name'], r['qty']), size=1.95, anchor='start')
            yy += 2.75
        yy += 1.2
    # the order of assembly: one picture per stage, right
    stages = ST.seat_set()
    sh.text(254, 20, 'ORDER OF ASSEMBLY (BUILD STEPS OF THE SET)', size=3.2, weight='bold')
    cw, chh = 74, 62
    for i, stg in enumerate(stages):
        c, r = i % 4, i // 4
        cx, cy = 104 + c * (cw + 2.5), 25 + r * (chh + 3)
        sh.add('<rect class="thin" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (cx, cy, cw, chh))
        shape = comp([(n, s_, None) for n, s_, c_ in stg['parts']])
        iso_fit(sh, shape, cx + 3, cy + 8, cw - 6, chh - 14, d=(-1, -1.4, 0.8))
        sh.text(cx + 2, cy + 4.5, '%d. %s' % (i + 1, stg['title']), size=2.5, anchor='start', weight='bold')
        sh.text(cx + cw - 2, cy + chh - 2, '%d parts' % len(stg['parts']), size=2.0, anchor='end')
    text_block(sh, 104, 166, [
        'HOW TO READ THIS SHEET',
        'Left: the assembly structure. The top level assembly, esp2026_seat_set.iam, is made from seven',
        'sub-assemblies (each its own .iam) and the four back pivot pins. Under each sub-assembly are its',
        'parts, with the item numbers of the parts list (ESP26-GA-05) and how many go in one sub-assembly.',
        'Right: the order the set is put together, one picture per build step, with the parts placed so far.',
        '',
        '1. Build each sub-assembly first, from its parts (exploded views on ESP26-GA-06).',
        '2. Place the frame and ground it.',
        '3. Add the seat pans and the backs, then pin the backs to the spreaders.',
        '4. Fit the recline locks, armrests, lap belts and life vest pouches.',
        '5. Check for interference upright, reclined, trays down and armrests up: no parts overlap.',
        '',
        'Every step, with the Inventor command to use, is on the Build steps tab of each model.',
    ], size=2.4)
    finish(sh, 'ESP26-GA-07_assembly_order', 'ESP 2026 assembly structure and order', 'ESP26-GA-07', 'NTS')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['1', '2', '3', '4', '5', '6', '7']
    for k in which:
        dict(zip('1234567', (ga01, ga02, ga03, ga04, ga05, ga06, ga07)))[k]()
