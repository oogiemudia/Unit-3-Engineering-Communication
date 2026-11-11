"""Parametric CAD models for Unit 3 Engineering representations (City and Guilds 8730, criteria 3.1 and 3.2).

Every model is plain CadQuery Python, so a learner or tutor can change a number and rebuild it.
Units are millimetres. Z is up, X runs along the length and Y runs back into the depth of the part,
so the front view looks along +Y.

Each entry in MODELS gives a function that returns a list of (part name, CadQuery shape, colour) and the
information the catalogue, the drawings and the viewer use.
"""
import math
import cadquery as cq

STEEL = '9AA6B2'
ALU = 'C9D3DD'
BRASS = 'D4B25A'
BLUE = '5B8DEF'
GREEN = '3FA37C'
ORANGE = 'E8A33D'
DARK = '4A5562'


# ------------------------------------------------------------------ helpers
def hex_prism(af, h):
    """Hexagon across flats af, height h, sitting on z = 0."""
    return cq.Workplane('XY').polygon(6, af / math.cos(math.radians(30))).extrude(h)


def bolt(d=8, length=40, af=13, head=5.3):
    """Simplified hex head bolt with its shank along -Z from the underside of the head at z = 0."""
    h = hex_prism(af, head).edges('>Z').chamfer(0.8)
    shank = cq.Workplane('XY').circle(d / 2).extrude(-length).faces('<Z').chamfer(0.8)
    return h.union(shank)


def nut(d=8, af=13, h=6.5):
    n = hex_prism(af, h).faces('>Z').workplane().hole(d)
    return n.edges('>Z or <Z').chamfer(0.5)


def washer(d_in=8.4, d_out=17, t=1.6):
    return cq.Workplane('XY').circle(d_out / 2).circle(d_in / 2).extrude(t)


# ------------------------------------------------------------------ 1 step block
def step_block():
    """The step block used in the criterion 3.1 lesson (Activity 1): 60 long, 40 deep, 40 high, a 10 mm hole
    through the lower step."""
    base = cq.Workplane('XY').box(60, 40, 20, centered=False)
    upper = cq.Workplane('XY').box(30, 40, 20, centered=False).translate((30, 0, 20))
    body = base.union(upper)
    body = body.cut(cq.Workplane('XY').center(15, 20).circle(5).extrude(20))
    return [('step block', body, BLUE)]


# ------------------------------------------------------------------ 2 sloping block (auxiliary view)
def sloping_block():
    """A block with a 45 degree sloping face and a 12 mm hole drilled square to the slope.
    The hole only shows its true shape in an auxiliary view."""
    w, d, h = 70, 40, 50
    body = cq.Workplane('XZ').polyline([(0, 0), (w, 0), (w, 20), (w - 30, h), (0, h)]).close().extrude(-d)
    # hole square to the sloping face, centred on it
    p1 = cq.Vector(w, 0, 20)
    p2 = cq.Vector(w - 30, 0, h)
    mid = (p1 + p2) * 0.5 + cq.Vector(0, d / 2, 0)
    n = cq.Vector(30, 0, 30).normalized()
    drill = cq.Solid.makeCylinder(6, 60, (mid - n * 30).toPnt() and cq.Vector(mid - n * 30), n)
    body = body.cut(cq.Workplane('XY').add(drill))
    return [('sloping block', body, ORANGE)]


# ------------------------------------------------------------------ 3 flanged bush (sections)
def flanged_bush():
    """Flanged bush: a classic part for a full section. Flange 70 diameter, body 40 diameter, bore 24."""
    flange = cq.Workplane('XY').circle(35).extrude(10)
    body = cq.Workplane('XY').workplane(offset=10).circle(20).extrude(40)
    part = flange.union(body)
    part = part.faces('>Z').workplane().hole(24)
    part = part.faces('<Z').workplane().polarArray(27.5, 45, 360, 4).hole(8)
    part = part.faces('>Z').edges('not %LINE').edges(cq.selectors.RadiusNthSelector(0)).chamfer(1)
    return [('flanged bush', part, BRASS)]


# ------------------------------------------------------------------ 4 bolted joint (assembly, GA, exploded)
def bolted_joint():
    """Two plates held by an M8 bolt, washer and nut. Used for assembly drawings, GA drawings and exploded views."""
    plate = cq.Workplane('XY').box(80, 40, 10, centered=(True, True, False)).faces('>Z').workplane().hole(9)
    plate = plate.edges('|Z').fillet(4)
    p1 = plate
    p2 = plate.translate((0, 0, 10))
    b = bolt(8, 40, 13, 5.3).translate((0, 0, 20 + 1.6))
    w = washer().translate((0, 0, 20))
    n = nut().translate((0, 0, -6.5))
    return [('lower plate', p1, ALU), ('upper plate', p2, BLUE), ('washer', w, STEEL),
            ('hex bolt M8 x 40', b, DARK), ('hex nut M8', n, STEEL)]


# ------------------------------------------------------------------ 5 threaded shaft
def threaded_shaft():
    """Stepped shaft with a keyway, an M16 thread, a thread undercut and chamfers."""
    s = cq.Workplane('YZ').circle(15).extrude(60)
    s = s.union(cq.Workplane('YZ').workplane(offset=60).circle(10).extrude(40))
    s = s.union(cq.Workplane('YZ').workplane(offset=100).circle(8).extrude(28))
    # undercut 3 wide at the end of the thread
    s = s.cut(cq.Workplane('YZ').workplane(offset=100).circle(10).circle(6.5).extrude(3))
    s = s.faces('>X').chamfer(1).faces('<X').chamfer(1)
    # keyway 6 wide, 3.5 deep, 30 long on the 30 diameter
    key = cq.Workplane('XY').workplane(offset=15 - 3.5).center(30, 0).slot2D(30, 6).extrude(10)
    s = s.cut(key)
    return [('threaded shaft', s, STEEL)]


# ------------------------------------------------------------------ 6 PCD flange
def pcd_flange():
    """Flange with six holes equally spaced on a 90 mm pitch circle diameter (PCD)."""
    f = cq.Workplane('XY').circle(60).extrude(15)
    f = f.union(cq.Workplane('XY').workplane(offset=15).circle(25).extrude(20))
    f = f.faces('>Z').workplane().hole(30)
    f = f.faces('<Z').workplane().polarArray(45, 0, 360, 6).hole(10)
    f = f.faces('>Z').edges('not %LINE').edges(cq.selectors.RadiusNthSelector(0)).chamfer(1.5)
    return [('PCD flange', f, ALU)]


# ------------------------------------------------------------------ 7 annotation plate (Activity 5)
def annotation_plate():
    """The 100 x 60 x 10 plate from Activity 5: four 6.6 mm holes countersunk to 13 mm at 90 degrees,
    a 40 mm bore with a 1 x 45 degree chamfer."""
    p = cq.Workplane('XY').box(100, 60, 10, centered=(True, True, False))
    p = p.faces('>Z').workplane().rect(76, 36, forConstruction=True).vertices().cskHole(6.6, 13, 90)
    p = p.faces('>Z').workplane().hole(40)
    p = p.faces('>Z').edges(cq.selectors.RadiusNthSelector(1)).chamfer(1)
    return [('annotation plate', p, BLUE)]


# ------------------------------------------------------------------ 8 hole features
def hole_features():
    """One block, four holes: plain clearance, counterbore, countersink and a blind tapping drill hole."""
    b = cq.Workplane('XY').box(110, 40, 20, centered=(False, True, False))
    top = lambda: b.faces('>Z').workplane(origin=(0, 0, 20))
    b = top().pushPoints([(15, 0)]).hole(6.6)                    # plain clearance hole for M6
    b = top().pushPoints([(40, 0)]).cboreHole(6.6, 11, 6.5)      # counterbore for an M6 cap head screw
    b = top().pushPoints([(68, 0)]).cskHole(6.6, 13, 90)         # countersink for an M6 countersunk screw
    b = top().pushPoints([(95, 0)]).hole(5, 15)                  # blind tapping drill hole for M6, 15 deep
    return [('hole features block', b, GREEN)]


# ------------------------------------------------------------------ 9 vee block
def vee_block():
    """Vee block: a standard workshop item and a good orthographic exercise (a vee, a slot, hidden detail)."""
    w, d, h = 80, 50, 50
    v = cq.Workplane('XZ').polyline([(0, 0), (w, 0), (w, h), (w / 2 + 20, h), (w / 2, h - 20), (w / 2 - 20, h),
                                     (0, h)]).close().extrude(-d)
    v = v.cut(cq.Workplane('XY').box(8, d, 12, centered=(True, False, False)).translate((w / 2, 0, h - 20 - 8)))
    v = v.cut(cq.Workplane('XY').box(30, d, 6, centered=(True, False, False)).translate((w / 2, 0, 0)))
    return [('vee block', v, ORANGE)]


# ------------------------------------------------------------------ 10 L bracket
def l_bracket():
    """Bent L bracket, 5 mm plate, a slot in the base and a hole in the upright, with a 6 mm inside bend radius."""
    t = 5
    base = cq.Workplane('XY').box(60, 40, t, centered=False)
    up = cq.Workplane('XY').box(t, 40, 50, centered=False)
    br = base.union(up)
    br = br.edges('|Y').edges(cq.selectors.BoxSelector((t - 0.1, -1, t - 0.1), (t + 0.1, 41, t + 0.1))).fillet(6)
    br = br.edges('|Y').edges(cq.selectors.BoxSelector((-0.1, -1, -0.1), (0.1, 41, 0.1))).fillet(t + 6)
    br = br.cut(cq.Workplane('XY').center(40, 20).slot2D(18, 7, 0).extrude(t))
    br = br.cut(cq.Workplane('YZ').center(20, 32).circle(4).extrude(t))
    return [('L bracket', br, GREEN)]


# ------------------------------------------------------------------ 11 shaft and housing fit (3.2)
def fit_pair():
    """A 20 mm H7 hole in a housing and a 20 mm g6 pin: the pair used for limits and fits in criterion 3.2.
    The model is at nominal size; the tolerances are on the drawing."""
    housing = cq.Workplane('XY').box(60, 40, 30, centered=(True, True, False)).faces('>Z').workplane().hole(20)
    housing = housing.edges('|Z').fillet(3)
    pin = cq.Workplane('XY').circle(10).extrude(45).faces('>Z or <Z').chamfer(0.8).translate((0, 0, -5))
    return [('housing (hole 20 H7)', housing, ALU), ('pin (shaft 20 g6)', pin, STEEL)]


# ------------------------------------------------------------------ 12 pneumatic cylinder (fluid power link)
def pneumatic_cylinder():
    """Single-acting pneumatic cylinder with spring return: the real thing behind the symbol in Part 2."""
    bore, L = 32, 80
    barrel = cq.Workplane('YZ').circle(bore / 2 + 2).circle(bore / 2).extrude(L)
    cap_r = cq.Workplane('YZ').rect(44, 44).extrude(12).edges('|X').fillet(3).translate((-12, 0, 0))
    cap_r = cap_r.cut(cq.Workplane('XZ').center(-6, 0).circle(3).extrude(-30, both=True))
    cap_f = cq.Workplane('YZ').rect(44, 44).extrude(12).edges('|X').fillet(3).translate((L, 0, 0))
    cap_f = cap_f.cut(cq.Workplane('YZ').circle(6.5).extrude(200, both=True))
    piston = cq.Workplane('YZ').circle(bore / 2 - 0.5).extrude(10).translate((6, 0, 0))
    rod = cq.Workplane('YZ').circle(6).extrude(L + 12 + 30).translate((6, 0, 0))
    turns = 7
    spring = cq.Workplane('XY').add(cq.Solid.makeCylinder(1.2, 1, cq.Vector(0, 0, 0)))
    helix = cq.Wire.makeHelix(pitch=(L - 26) / turns, height=L - 26, radius=11)
    prof = cq.Workplane('XZ').center(11, 0).circle(1.2)
    spring = prof.sweep(cq.Workplane('XY').add(helix), isFrenet=True)
    spring = spring.rotate((0, 0, 0), (0, 1, 0), 90).translate((16, 0, 0))
    return [('barrel', barrel, ALU), ('rear cap with air port', cap_r, DARK), ('front cap', cap_f, DARK),
            ('piston', piston, ORANGE), ('piston rod', rod, STEEL), ('return spring', spring, BRASS)]


# ------------------------------------------------------------------ 13 machine vice (an assembly of 17 parts)
# A 100 mm drill press (machine) vice, the kind of assembly found in every workshop and in online CAD libraries.
# The model is our own design. X runs along the screw (the fixed jaw at the left), Y across the jaws, Z up.
VICE = dict(
    base=(220, 130, 12),        # base length, width, thickness
    rail=(35, 205, 35, 50, 42),  # rails from x, to x, inside y, outside y, top z
    jaw_h=80,                   # top of both jaws
    fixed=35,                   # fixed jaw from x = 0 to 35
    open=60,                    # opening between the jaw plates in the model
    jaw_l=35,                   # moving jaw length along X
    tongue=34.5,                # half width of the moving jaw tongue that runs between the rails
    axis_z=27,                  # screw axis height
    screw=(16, 2.0),            # M16 x 2 lead screw: major diameter and pitch
    journal=14,                 # journal diameter where the screw runs in the end block
    plate=(100, 30, 8),         # jaw plate width, height, thickness
    end=(205, 220),             # end block from x, to x
)


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def _cyl(r, p, d, h):
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r, h, cq.Vector(*p), cq.Vector(*d)))


def _csk(p, d, dia, csk_dia, depth):
    """Countersunk clearance hole cutter (90 degree) starting at point p and going along d."""
    cone = cq.Solid.makeCone(csk_dia / 2, 0, csk_dia / 2, cq.Vector(*p), cq.Vector(*d))
    return _cyl(dia / 2, p, d, depth).union(cq.Workplane('XY').add(cone))


def csk_screw(d=6, length=16, head=12, p=(0, 0, 0), direction=(0, 0, -1)):
    """Countersunk head screw: the head top at p, the shank going along direction."""
    h = (head - d) / 2
    cone = cq.Solid.makeCone(head / 2, d / 2, h, cq.Vector(*p), cq.Vector(*direction))
    tip = [p[i] + direction[i] * h for i in range(3)]
    return cq.Workplane('XY').add(cone).union(_cyl(d / 2, tip, direction, length - h))


def cap_screw(d=8, length=30, head_d=13, head_h=8, p=(0, 0, 0), direction=(0, 0, -1)):
    """Socket head cap screw: the underside of the head at p, the shank going along direction, a hex socket."""
    back = [-c for c in direction]
    head = _cyl(head_d / 2, p, back, head_h)
    top = [p[i] + back[i] * head_h for i in range(3)]
    hex_w = 0.75 * d   # 6 mm A/F key for M8
    sock = cq.Workplane(cq.Plane(origin=top, xDir=(0, 1, 0) if abs(direction[0]) > 0.5 else (1, 0, 0),
                                 normal=direction)).polygon(6, hex_w / math.cos(math.radians(30))).extrude(head_h * 0.55)
    return head.cut(sock).union(_cyl(d / 2, p, direction, length))


def vice_stages():
    """Every part of the machine vice, and the stages each one is built in (used by the Build steps tab)."""
    V = VICE
    L, W, T = V['base']
    rx0, rx1, ry0, ry1, rz = V['rail']
    zc, H, F = V['axis_z'], V['jaw_h'], V['fixed']
    pw, ph, pt = V['plate']
    pz = H - ph / 2                         # jaw plate screws: height of their centre line
    J = F + pt + V['open'] + pt             # moving jaw front face x (111)
    J1 = J + V['jaw_l']
    e0, e1 = V['end']
    s = {}
    # body: base plate, rails and fixed jaw, one casting
    s['body_base'] = _box(0, L, -W / 2, W / 2, 0, T).edges('|Z').fillet(6)
    up = _box(0, F, -ry1, ry1, T, rz).union(_box(rx0, rx1, ry0, ry1, T, rz)).union(_box(rx0, rx1, -ry1, -ry0, T, rz))
    s['body_rails'] = s['body_base'].union(up)
    s['body_jaw'] = s['body_rails'].union(_box(0, F, -ry1, ry1, rz, H))
    holes = [(50, 57.5), (50, -57.5), (170, 57.5), (170, -57.5)]
    b = s['body_jaw']
    for x, y in holes:
        b = b.cut(_cyl(6.5, (x, y, -1), (0, 0, 1), T + 2))
    s['body_holes'] = b
    for y in (42.5, -42.5):                 # M8 tapped holes in the rail ends for the end block screws
        b = b.cut(_cyl(4, (rx1, y, zc), (-1, 0, 0), 25))
    s['body_tapped'] = b
    for y in (30, -30):                     # M6 tapped holes for the fixed jaw plate
        b = b.cut(_cyl(3, (F, y, pz), (-1, 0, 0), 14))
    s['body'] = b
    # moving jaw: an inverted T, its tongue running between the rails, threaded M16 for the lead screw
    t = V['tongue']
    prof = (cq.Workplane('YZ').workplane(offset=J)
            .polyline([(-t, T + 1), (t, T + 1), (t, rz + 0.5), (ry1, rz + 0.5), (ry1, H), (-ry1, H), (-ry1, rz + 0.5),
                       (-t, rz + 0.5)]).close())
    s['mjaw_profile'] = prof
    m = prof.extrude(V['jaw_l'])
    s['mjaw_block'] = m
    m = m.cut(_cyl(V['screw'][0] / 2, (J - 1, 0, zc), (1, 0, 0), V['jaw_l'] + 2))
    s['mjaw_thread'] = m
    for y in (30, -30):
        m = m.cut(_cyl(3, (J, y, pz), (1, 0, 0), 14))
    s['moving jaw'] = m
    # end block: carries the screw journal, held to the rail ends by two M8 cap screws
    e = _box(e0, e1, -ry1, ry1, T, rz)
    s['end_block'] = e
    e = e.cut(_cyl(V['journal'] / 2, (e0 - 1, 0, zc), (1, 0, 0), e1 - e0 + 2))
    s['end_bore'] = e
    for y in (42.5, -42.5):
        e = e.cut(_cyl(4.5, (e0 - 1, y, zc), (1, 0, 0), e1 - e0 + 2)).cut(_cyl(7, (e1 - 8.5, y, zc), (1, 0, 0), 9))
    s['end block'] = e
    # jaw plates (the same part twice), two M6 countersunk holes each
    def plate(x0, face_x, sign):
        p = _box(x0, x0 + pt, -pw / 2, pw / 2, H - ph, H)
        q = p
        for y in (30, -30):
            q = q.cut(_csk((face_x, y, pz), (-sign, 0, 0), 6.6, 12, pt + 1))
        return p, q
    s['plate_blank'], s['fixed jaw plate'] = plate(F, F + pt, 1)
    _, s['moving jaw plate'] = plate(J - pt, J - pt, -1)
    # lead screw: thread, journal and the handle boss, revolved from one half profile
    rs, rj = V['screw'][0] / 2, V['journal'] / 2
    x_thread, x_boss, x_end = 45, e1 + 8, e1 + 30
    half = [(x_thread, 0), (x_thread, rs), (e0, rs), (e0, rj), (x_boss, rj), (x_boss, 14), (x_end, 14), (x_end, 0)]
    s['screw_profile'] = cq.Workplane('XZ', origin=(0, 0, zc)).polyline([(x, z) for x, z in half]).close()
    ls = cq.Workplane('XY').add(cq.Solid.makeCylinder(rs, e0 - x_thread, cq.Vector(x_thread, 0, zc), cq.Vector(1, 0, 0)))
    ls = ls.union(_cyl(rj, (e0, 0, zc), (1, 0, 0), x_boss - e0)).union(_cyl(14, (x_boss, 0, zc), (1, 0, 0), x_end - x_boss))
    s['screw_revolved'] = ls
    bar_x = x_boss + 12
    ls = ls.cut(_cyl(5.25, (bar_x, -20, zc), (0, 1, 0), 40)).cut(_cyl(2, (e1 + 4, 0, zc - 10), (0, 0, 1), 20))
    s['screw_holes'] = ls
    ls = ls.faces('<X').chamfer(1.5).edges(cq.selectors.BoxSelector((x_end - 1, -20, zc - 20), (x_end + 1, 20, zc + 20))).chamfer(1)
    s['lead screw'] = ls
    # thrust collar and its pin, outside the end block
    c = _cyl(13, (e1, 0, zc), (1, 0, 0), 8).cut(_cyl(rj, (e1 - 1, 0, zc), (1, 0, 0), 10))
    s['collar_ring'] = c
    s['thrust collar'] = c.cut(_cyl(2, (e1 + 4, 0, zc - 20), (0, 0, 1), 40))
    s['collar pin'] = _cyl(2, (e1 + 4, 0, zc - 13), (0, 0, 1), 26).faces('>Z or <Z').chamfer(0.4)
    # tommy bar and its two end balls
    s['tommy bar'] = _cyl(5, (bar_x, -80, zc), (0, 1, 0), 160)
    for k, sign in ((1, 1), (2, -1)):
        ball = cq.Workplane('XY').add(cq.Solid.makeSphere(10, cq.Vector(bar_x, sign * 82, zc), cq.Vector(0, 0, 1), -90, 90, 360))
        s['ball_plain_%d' % k] = ball
        s['handle ball %d' % k] = ball.cut(_cyl(5, (bar_x, sign * 70, zc), (0, sign, 0), 10))
    # fasteners
    for k, y in ((1, 30), (2, -30)):
        s['jaw plate screw %d' % k] = csk_screw(6, 16, 12, (F + pt, y, pz), (-1, 0, 0))
        s['jaw plate screw %d' % (k + 2)] = csk_screw(6, 16, 12, (J - pt, y, pz), (1, 0, 0))
    for k, y in ((1, 42.5), (2, -42.5)):
        s['cap screw M8 x 30 %d' % k] = cap_screw(8, 30, 13, 8, (e1 - 8.5, y, zc), (-1, 0, 0))
    s['_dims'] = dict(J=J, J1=J1, bar_x=bar_x, x_thread=x_thread, x_boss=x_boss, x_end=x_end, pz=pz)
    return s


VICE_PARTS = [('body', BLUE), ('moving jaw', BLUE), ('end block', BLUE), ('fixed jaw plate', STEEL),
              ('moving jaw plate', STEEL), ('lead screw', STEEL), ('thrust collar', STEEL), ('collar pin', DARK),
              ('tommy bar', STEEL), ('handle ball 1', DARK), ('handle ball 2', DARK),
              ('jaw plate screw 1', DARK), ('jaw plate screw 2', DARK), ('jaw plate screw 3', DARK),
              ('jaw plate screw 4', DARK), ('cap screw M8 x 30 1', DARK), ('cap screw M8 x 30 2', DARK)]


def machine_vice():
    """A 100 mm machine (drill press) vice made of 17 separate parts: a cast body with rails and a fixed jaw, a sliding
    jaw driven by an M16 x 2 lead screw, an end block, hardened jaw plates, a thrust collar and a tommy bar handle."""
    s = vice_stages()
    return [(n, s[n], c) for n, c in VICE_PARTS]


VICE_BOM = [  # item, part, material, group, instances (the part names in the model)
    (1, 'Body', 'EN-GJS-400 ductile iron', 'Body and jaws', ['body']),
    (2, 'Moving jaw', 'EN-GJS-400 ductile iron', 'Body and jaws', ['moving jaw']),
    (3, 'Jaw plate', 'C45 steel, hardened', 'Body and jaws', ['fixed jaw plate', 'moving jaw plate']),
    (4, 'End block', 'EN-GJS-400 ductile iron', 'Body and jaws', ['end block']),
    (5, 'Lead screw M16 x 2', 'C45 steel', 'Screw and handle', ['lead screw']),
    (6, 'Thrust collar', 'S275 steel', 'Screw and handle', ['thrust collar']),
    (7, 'Collar pin 4 x 26', 'Spring steel', 'Screw and handle', ['collar pin']),
    (8, 'Tommy bar 10 x 160', 'S275 steel, zinc plated', 'Screw and handle', ['tommy bar']),
    (9, 'Handle ball', 'Phenolic plastic', 'Screw and handle', ['handle ball 1', 'handle ball 2']),
    (10, 'Countersunk screw ISO 10642 M6 x 16', 'Steel, grade 8.8', 'Fasteners (bought in)',
     ['jaw plate screw 1', 'jaw plate screw 2', 'jaw plate screw 3', 'jaw plate screw 4']),
    (11, 'Socket head cap screw ISO 4762 M8 x 30', 'Steel, grade 12.9', 'Fasteners (bought in)',
     ['cap screw M8 x 30 1', 'cap screw M8 x 30 2']),
]


def vice_bom():
    return [dict(no=no, name=name, qty=len(inst), material=mat, group=grp, model=None, file=None,
                 bought=grp.startswith('Fasteners'), instances=inst) for no, name, mat, grp, inst in VICE_BOM]


VICE_EXPLODE = {
    'moving jaw': (0, 0, 90), 'moving jaw plate': (-35, 0, 90), 'jaw plate screw 3': (-75, 0, 90),
    'jaw plate screw 4': (-75, 0, 90), 'fixed jaw plate': (0, 0, 130), 'jaw plate screw 1': (40, 0, 130),
    'jaw plate screw 2': (40, 0, 130), 'end block': (40, 0, 70), 'cap screw M8 x 30 1': (90, 0, 70),
    'cap screw M8 x 30 2': (90, 0, 70), 'lead screw': (150, 0, 0), 'thrust collar': (200, 0, 0),
    'collar pin': (200, 0, 45), 'tommy bar': (240, 0, 0), 'handle ball 1': (240, 35, 0), 'handle ball 2': (240, -35, 0),
}

MODELS = [
    dict(name='step_block', title='Step block', fn=step_block, criteria='3.1',
         uses='Isometric drawing, first and third angle projection, the glass box, Activity 1.',
         section=None, explode=None, iso=(-1, -1, 1)),
    dict(name='sloping_block', title='Sloping block', fn=sloping_block, criteria='3.1',
         uses='Auxiliary views: why a hole on a sloping face looks oval until it is viewed square on.',
         section=None, explode=None),
    dict(name='flanged_bush', title='Flanged bush', fn=flanged_bush, criteria='3.1, 3.2',
         uses='Full section A-A, hatching, centre lines, repeated holes on a PCD.',
         section='y', explode=None),
    dict(name='bolted_joint', title='Bolted joint', fn=bolted_joint, criteria='3.1',
         uses='Assembly and general arrangement drawings, exploded views, parts lists, standard fasteners.',
         section='y', explode=(0, 0, 1)),
    dict(name='threaded_shaft', title='Threaded shaft', fn=threaded_shaft, criteria='3.1, 3.2',
         uses='Screw thread conventions, undercuts, chamfers, keyways, detail views.',
         section=None, explode=None),
    dict(name='pcd_flange', title='PCD flange', fn=pcd_flange, criteria='3.1, 3.2',
         uses='Pitch circle diameter, equally spaced holes, centre marks, half sections.',
         section='y', explode=None),
    dict(name='annotation_plate', title='Annotation plate', fn=annotation_plate, criteria='3.1, 3.2',
         uses='Activity 5: countersinks, a bore with a chamfer, centre marks, hole notes and abbreviations.',
         section='y', explode=None),
    dict(name='hole_features', title='Hole features block', fn=hole_features, criteria='3.1',
         uses='Clearance hole, counterbore (CBORE), countersink (CSK) and a blind tapping drill hole, side by side.',
         section='y', explode=None),
    dict(name='vee_block', title='Vee block', fn=vee_block, criteria='3.1',
         uses='Orthographic practice: a vee, a relief slot and hidden detail.',
         section=None, explode=None, iso=(-1, -1, 1)),
    dict(name='l_bracket', title='L bracket', fn=l_bracket, criteria='3.1, 3.2',
         uses='Bent plate with an inside radius, a slot and a hole: views, hidden detail and dimensioning.',
         section=None, explode=None),
    dict(name='fit_pair', title='Pin and housing fit', fn=fit_pair, criteria='3.2',
         uses='Limits and fits: a 20 H7 hole and a 20 g6 pin, clearance fit.',
         section='y', explode=(0, 0, 1)),
    dict(name='pneumatic_cylinder', title='Pneumatic cylinder', fn=pneumatic_cylinder, criteria='3.1',
         uses='The real component behind the single-acting, spring-return cylinder symbol (ISO 1219-1:2012).',
         section='y', explode=(1, 0, 0)),
    dict(name='machine_vice', title='Machine vice', fn=machine_vice, criteria='3.1, 3.2',
         uses='A full assembly of 17 parts: general arrangement, parts list, section through the lead screw, exploded view, '
              'standard fasteners (countersunk and cap screws) and a screw thread that turns into straight line motion.',
         section='y', explode=VICE_EXPLODE, iso=(-1, -1.3, 0.9), bom=vice_bom),
]


# ------------------------------------------------------------------ project folders
# Projects such as ESP 2023 keep every file they generate (models, drawings, animations, steps, simulation and
# FEA) together in their own folder under docs/, named by the model's 'folder' key.
from esp2023 import MODELS as ESP2023_MODELS  # noqa: E402
from esp2026 import MODELS as ESP2026_MODELS  # noqa: E402
from esp2024 import MODELS as ESP2024_MODELS  # noqa: E402
from esp2025 import MODELS as ESP2025_MODELS  # noqa: E402

MODELS += ESP2023_MODELS + ESP2026_MODELS + ESP2024_MODELS + ESP2025_MODELS


def base_of(m):
    """The folder under docs/ that holds a model's files, with a trailing slash ('' for the hub's own models)."""
    return m['folder'] + '/' if m.get('folder') else ''
