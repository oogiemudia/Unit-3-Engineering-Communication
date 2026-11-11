"""Workshop library models: complete assemblies of the kind found in online CAD libraries such as GrabCAD, designed
from scratch for the hub (none of them is copied from anyone's upload).

Every component is its own part, built feature by feature the way it would be in Autodesk Inventor, then placed
into the assembly. Each model gives the hub:
  * the assembly (one entry in MODELS, with a parts list and exploded positions),
  * Inventor build steps: every part feature by feature, then the assembly a few parts at a time (STEPS),
  * a Stress Analysis load case for one part (FEA, read by models/fea_cases.py),
  * a Dynamic Simulation where something moves (SIMS, read by tools/build_sim.py).

Units: mm. Z up, X along the length, Y back into the depth (the front view looks along +Y).
"""
import functools
import math
import cadquery as cq
from parts import STEEL, ALU, BRASS, BLUE, GREEN, ORANGE, DARK, hex_prism, _box, _cyl, _csk, cap_screw, csk_screw

RED = 'C0504D'
BLACK = '2E3338'
RUBBER = '3A3F44'
IRON = '6E7F99'
BRONZE = 'B08D57'

NEW_PART = 'File > New > Standard (mm).ipt'
NEW_ASSY = 'File > New > Standard (mm).iam'
SKETCH = '3D Model tab > Sketch panel > Start 2D Sketch'
EXTRUDE = '3D Model tab > Create panel > Extrude'
REVOLVE = '3D Model tab > Create panel > Revolve'
HOLE = '3D Model tab > Modify panel > Hole'
FILLET = '3D Model tab > Modify panel > Fillet'
CHAMFER = '3D Model tab > Modify panel > Chamfer'
THREAD = '3D Model tab > Modify panel > Thread'
SPLIT = '3D Model tab > Modify panel > Split'
CIRC = '3D Model tab > Pattern panel > Circular Pattern'
RECT = '3D Model tab > Pattern panel > Rectangular Pattern'
MIRROR = '3D Model tab > Pattern panel > Mirror'
SPUR = 'Design tab > Power Transmission panel > Spur Gear'
BEARING = 'Design tab > Power Transmission panel > Bearing'
PLACE = 'Assemble tab > Component panel > Place'
CONTENT = 'Assemble tab > Component panel > Place from Content Center'
CONSTRAIN = 'Assemble tab > Relationships panel > Constrain'


# ------------------------------------------------------------------ small geometry helpers
def ycyl(r, y0, y1, x=0, z=0):
    return _cyl(r, (x, y0, z), (0, 1, 0), y1 - y0)


def xcyl(r, x0, x1, y=0, z=0):
    return _cyl(r, (x0, y, z), (1, 0, 0), x1 - x0)


def zcyl(r, z0, z1, x=0, y=0):
    return _cyl(r, (x, y, z0), (0, 0, 1), z1 - z0)


def yring(r0, r1, y0, y1, x=0, z=0):
    return ycyl(r1, y0, y1, x, z).cut(ycyl(r0, y0 - 1, y1 + 1, x, z))


def zring(r0, r1, z0, z1, x=0, y=0):
    return zcyl(r1, z0, z1, x, y).cut(zcyl(r0, z0 - 1, z1 + 1, x, y))


def sphere(r, c):
    return cq.Workplane('XY').add(cq.Solid.makeSphere(r, cq.Vector(*c), cq.Vector(0, 0, 1), -90, 90, 360))


def torus(R, r, c, d):
    return cq.Workplane('XY').add(cq.Solid.makeTorus(R, r, cq.Vector(*c), cq.Vector(*d)))


def hex_nut(af, h, d, p, axis='z'):
    """Hex nut with its base at p, standing along +axis."""
    n = hex_prism(af, h).cut(cq.Workplane('XY').circle(d / 2).extrude(h)).edges('>Z or <Z').chamfer(0.6)
    return orient(n, axis).translate(p)


def orient(w, axis):
    """Turn a shape made along +Z so that it points along axis ('x', 'y', 'z', '-x', '-y' or '-z')."""
    return {'z': w, '-z': w.rotate((0, 0, 0), (1, 0, 0), 180), 'x': w.rotate((0, 0, 0), (0, 1, 0), 90),
            '-x': w.rotate((0, 0, 0), (0, 1, 0), -90), 'y': w.rotate((0, 0, 0), (1, 0, 0), -90),
            '-y': w.rotate((0, 0, 0), (1, 0, 0), 90)}[axis]


def stud(d, z0, z1, x, y):
    return zcyl(d / 2, z0, z1, x, y).faces('>Z or <Z').chamfer(0.8)


def flat_washer(d_in, d_out, t, z0, x, y):
    return zring(d_in / 2, d_out / 2, z0, z0 + t, x, y)


def involute_gear(m, z, face, backlash=0.15, n=6):
    """Spur gear outline (20 degree pressure angle) extruded along +Z from z = 0, centred on the origin."""
    rp, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    rb = rp * math.cos(math.radians(20))
    inv = lambda a: math.tan(a) - a
    psi_p = (math.pi * m / 2 - backlash) / (2 * rp)

    def psi(r):
        r = max(r, rb)
        return psi_p + inv(math.radians(20)) - inv(math.acos(rb / r))
    r0 = max(rf, rb)
    radii = [r0 + (ra - r0) * k / n for k in range(n + 1)]
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        if r0 - rf > 1e-6:                      # a radial flank below the base circle (fewer than 42 teeth)
            pts.append((rf * math.cos(c - psi(r0)), rf * math.sin(c - psi(r0))))
        for r in radii:
            pts.append((r * math.cos(c - psi(r)), r * math.sin(c - psi(r))))
        for r in reversed(radii):
            pts.append((r * math.cos(c + psi(r)), r * math.sin(c + psi(r))))
        if r0 - rf > 1e-6:
            pts.append((rf * math.cos(c + psi(r0)), rf * math.sin(c + psi(r0))))
        h = c + math.pi / z
        pts.append((rf * math.cos(h), rf * math.sin(h)))
    return cq.Workplane('XY').polyline(pts).close().extrude(face)


# ------------------------------------------------------------------ the part and model framework
def F(title, command, actions, shape, overlay=None, note=None):
    """One feature of a part: what Inventor does, and the part as it stands after it."""
    return dict(title=title, command=command, actions=actions, shape=shape, overlay=overlay, note=note)


def P(key, name, material, group, colour, features, instances=None, bought=False, file=None):
    """A part. features build it in the position of its first instance; instances are (name, transform) pairs."""
    return dict(key=key, name=name, material=material, group=group, colour=colour, features=features,
                instances=instances or [(name, None)], bought=bought, file=file or key + '.ipt')


def T(dx=0, dy=0, dz=0):
    return lambda w: w.translate((dx, dy, dz))


def R(point, axis, deg):
    return lambda w: w.rotate(point, tuple(point[i] + axis[i] for i in range(3)), deg)


def chain(*fs):
    def go(w):
        for f in fs:
            w = f(w)
        return w
    return go


def placed(p):
    final = p['features'][-1]['shape']
    return [(n, tf(final) if tf else final, p['colour']) for n, tf in p['instances']]


def model_items(mdl):
    out = []
    for p in mdl['parts']:
        out += placed(p)
    return out


def model_bom(mdl):
    return [dict(no=k + 1, name=p['name'], qty=len(p['instances']), material=p['material'], group=p['group'], model=None,
                 file=p['file'], bought=p['bought'], instances=[n for n, tf in p['instances']])
            for k, p in enumerate(mdl['parts'])]


def model_steps(mdl):
    """Inventor build steps: each part feature by feature (bought-in parts come from Content Center), then the assembly."""
    steps = []
    for p in mdl['parts']:
        if p['bought']:
            continue
        first_name, tf = p['instances'][0]
        for k, f in enumerate(p['features']):
            acts = list(f['actions'])
            if k == 0:
                acts = [NEW_PART + ' and save it as %s.' % p['file']] + acts
            if k == len(p['features']) - 1:
                acts = acts + ['Save %s.' % p['file']]
            shape = tf(f['shape']) if tf else f['shape']
            ov = f.get('overlay')
            if ov is not None and tf:
                ov = tf(ov)
            steps.append(dict(title='%s: %s' % (p['name'][0].upper() + p['name'][1:], f['title']), command=f['command'],
                              actions=acts, parts=[(p['name'] if len(p['instances']) == 1 else first_name, shape, p['colour'])]
                              if f['shape'] is not None else [], overlay=ov, note=f.get('note')))
    items = {n: (n, w, c) for n, w, c in model_items(mdl)}
    shown = []
    for k, a in enumerate(mdl['assembly']):
        title, command, actions, names = a[:4]
        note = a[4] if len(a) > 4 else None
        if k == 0:
            actions = [NEW_ASSY + ' and save it as %s.iam.' % mdl['name']] + list(actions)
        shown += [items[n] for n in names]
        steps.append(dict(title='Assembly: ' + title, command=command, actions=actions, parts=list(shown), overlay=None,
                          note=note))
    assert len(shown) == len(items), (mdl['name'], set(items) - {n for n, w, c in shown})
    return steps


# ================================================================== 1 plummer block bearing
@functools.lru_cache(None)
def plummer_block():
    H = 65                       # shaft centre height
    RB, WB = 40, 18              # bearing 6208: OD 80, width 18, bore 40
    PCD, RBALL, NBALL = 30, 6, 9
    FOOT = (120, 27.5, 20)       # foot half length, half width, thickness
    LUG = (95, 22)               # lug half length, half width
    BODY = (55, 30)              # body half length (also the cap radius), half width
    CAP_TOP = H + 20             # top of the cap lugs
    STUD_X = 75

    def bores(w):
        """The bore through the housing: bearing seat, grease space, shaft clearance and the felt seal grooves."""
        c = ycyl(RB, -WB / 2, WB / 2, 0, H)
        c = c.union(ycyl(30, -14, 14, 0, H)).union(ycyl(21, -BODY[1] - 1, BODY[1] + 1, 0, H))
        for s in (1, -1):
            c = c.union(ycyl(27, min(s * 20, s * 26), max(s * 20, s * 26), 0, H))
        return w.cut(c)

    # base (lower half of the housing)
    foot = _box(-FOOT[0], FOOT[0], -FOOT[1], FOOT[1], 0, FOOT[2])
    b1 = foot.union(_box(-LUG[0], LUG[0], -LUG[1], LUG[1], FOOT[2], H)).union(_box(-BODY[0], BODY[0], -BODY[1], BODY[1], FOOT[2], H))
    b2 = bores(b1)
    slots = cq.Workplane('XY').pushPoints([(105, 0), (-105, 0)]).slot2D(26, 14, 0).extrude(FOOT[2])
    b3 = b2.cut(slots)
    b4 = b3
    for x in (STUD_X, -STUD_X):
        b4 = b4.cut(zcyl(6, H - 24, H + 1, x, 0))
    b5 = b4.edges('|Z').edges(cq.selectors.BoxSelector((-121, -28, 5), (121, 28, 15))).fillet(4)
    # cap (upper half)
    c1 = ycyl(BODY[0], -BODY[1], BODY[1], 0, H).intersect(_box(-60, 60, -40, 40, H, H + 60))
    c1 = c1.union(_box(-LUG[0], LUG[0], -LUG[1], LUG[1], H, CAP_TOP))
    c2 = bores(c1)
    c3 = c2
    for x in (STUD_X, -STUD_X):
        c3 = c3.cut(zcyl(6.6, H - 1, CAP_TOP + 1, x, 0))
    top = H + BODY[0]
    c4 = c3.union(zcyl(9, top - 4, top + 2, 0, 0)).cut(zcyl(3, H + RB - 1, top + 3, 0, 0))
    # bearing
    race = torus(PCD, RBALL, (0, 0, H), (0, 1, 0))
    outer0 = yring(34, RB, -WB / 2, WB / 2, 0, H)
    outer = outer0.cut(race)
    inner0 = yring(20, 26, -WB / 2, WB / 2, 0, H)
    inner = inner0.cut(race)
    ball = sphere(RBALL - 0.05, (PCD, 0, H))
    cage0 = yring(28.5, 31.5, -7.5, 7.5, 0, H)
    cage = cage0
    for k in range(NBALL):
        cage = cage.cut(sphere(RBALL + 0.2, (PCD, 0, H)).rotate((0, 0, H), (0, 1, H), 360 * k / NBALL))
    seal = yring(20, 27, 20, 26, 0, H)
    shaft0 = ycyl(20, -90, 90, 0, H)
    shaft = shaft0.faces('>Y or <Y').chamfer(1.5)
    stud0 = stud(12, H - 24, CAP_TOP + 15, STUD_X, 0)
    washer = flat_washer(13, 24, 2.5, CAP_TOP, STUD_X, 0)
    nut = hex_nut(18, 10, 12, (STUD_X, 0, CAP_TOP + 2.5))
    nip = zcyl(3, top - 8, top + 2, 0, 0).union(hex_prism(11, 7).translate((0, 0, top + 2)))
    nip = nip.union(zcyl(2.2, top + 9, top + 12, 0, 0)).union(sphere(3.5, (0, 0, top + 14)))

    mirror_x = R((0, 0, 0), (0, 0, 1), 180)
    balls = [('ball %d' % (k + 1), R((0, 0, H), (0, 1, 0), 360 * k / NBALL)) for k in range(NBALL)]
    parts = [
        P('housing_base', 'housing base', 'EN-GJL-250 grey cast iron', 'Housing', IRON, [
            F('sketch the foot', SKETCH, ['Start 2D Sketch on the XZ Plane (the ground). Rectangle (Two Point Center) 240 x 55 on the origin.',
                                           'Finish Sketch.'], None, overlay=cq.Workplane('XY').add(foot.faces('<Z').val())),
            F('extrude the foot, body and lugs', EXTRUDE,
              ['Extrude the foot 20 mm upwards.', 'Sketch on its top: a rectangle 110 x 60 (the body) and one 190 x 44 (the stud lugs), '
               'both centred. Extrude them 45 mm, Join, so the split line is 65 mm (the shaft centre height) above the base.'], b1),
            F('the bore', REVOLVE,
              ['Sketch on the XY Plane (the front, through the shaft axis) the half section of the bore: bearing seat 80 diameter '
               'x 18 wide, grease space 60 x 28, shaft clearance 42, two felt seal grooves 54 x 6 at 20 to 26 from the middle.',
               'Revolve it about the shaft axis, Cut. The upper half cuts nothing, because the base stops at the split line.'], b2,
              note='The bore is cut in both halves with the same sketch, as the halves are machined together.'),
            F('slots for the holding down bolts', EXTRUDE,
              ['Sketch on the top of the foot: two Slots (Center to Center) 12 long x 14 wide, 105 each side of the middle.',
               'Extrude, Cut, Through All.'], b3, note='Slots let the block slide along to line the shaft up before the bolts are tightened.'),
            F('tapped holes for the cap studs', HOLE,
              ['Hole on the split face, 75 each side of the middle: Tapped Hole, M12x1.75, Distance 24 mm.'], b4),
            F('round the foot corners', FILLET, ['Fillet: radius 4 mm on the four vertical corners of the foot.'], b5),
        ]),
        P('housing_cap', 'housing cap', 'EN-GJL-250 grey cast iron', 'Housing', IRON, [
            F('half cylinder and lugs', EXTRUDE,
              ['Sketch on the XY Plane: a half circle of radius 55 on the shaft axis (centre 65 up), and a rectangle 190 x 20 on the split line.',
               'Extrude the half circle 60 mm (Symmetric) and the rectangle 44 mm (Symmetric).'], c1),
            F('the bore', REVOLVE, ['Revolve the same bore section as the base, Cut.'], c2),
            F('clearance holes for the studs', HOLE, ['Hole 75 each side: Simple Hole, diameter 13, Through All.'], c3),
            F('boss and hole for the grease nipple', HOLE,
              ['Sketch a 18 mm circle on the XZ Plane at the top. Extrude it to 2 mm above the cap (Join).',
               'Hole on the boss: Tapped Hole, M6x1, To the bearing seat.'], c4),
        ]),
        P('outer_ring', 'bearing outer ring', '100Cr6 bearing steel', 'Bearing 6208', STEEL, [
            F('ring', REVOLVE, ['Sketch the ring section on the XY Plane: 68 to 80 diameter, 18 wide. Revolve 360 degrees.'], outer0),
            F('ball track', REVOLVE, ['Sketch a 12 mm circle on the pitch diameter (60). Revolve, Cut.'], outer,
              note='Inventor can make the whole bearing in one go with Design tab > Bearing; it is built here part by part so you can see inside it.'),
        ]),
        P('inner_ring', 'bearing inner ring', '100Cr6 bearing steel', 'Bearing 6208', STEEL, [
            F('ring and ball track', REVOLVE, ['Sketch the ring section: 40 to 52 diameter, 18 wide. Revolve 360 degrees.',
                                               'Sketch the 12 mm ball circle on the 60 pitch diameter and Revolve, Cut.'], inner),
        ]),
        P('cage', 'bearing cage', 'Pressed steel', 'Bearing 6208', BRASS, [
            F('band', REVOLVE, ['Sketch 57 to 63 diameter, 15 wide on the pitch diameter. Revolve 360 degrees.'], cage0),
            F('ball pockets', CIRC, ['Revolve a 12.4 mm circle on the pitch diameter as a Cut (one pocket).',
                                     'Circular Pattern: 9 pockets about the bearing axis.'], cage),
        ]),
        P('ball', 'ball 12 mm', '100Cr6 bearing steel', 'Bearing 6208', STEEL,
          [F('sphere', REVOLVE, ['Sketch a half circle of diameter 11.9 with a centre line. Revolve 360 degrees.'], ball)],
          instances=balls),
        P('felt_seal', 'felt seal', 'Wool felt', 'Housing', RUBBER,
          [F('ring', EXTRUDE, ['Sketch circles of diameter 40 and 54. Extrude 6 mm.'], seal)],
          instances=[('felt seal 1', None), ('felt seal 2', R((0, 0, H), (0, 0, 1), 180))]),
        P('shaft', 'shaft', '080M40 steel', 'Shaft', STEEL,
          [F('cylinder', EXTRUDE, ['Sketch a 40 mm circle on the XZ Plane. Extrude 180 mm Symmetric.'], shaft0),
           F('chamfer the ends', CHAMFER, ['Chamfer 1.5 mm on both end edges.'], shaft)]),
        P('stud', 'stud M12 x 74', 'Steel, grade 8.8', 'Fasteners (bought in)', DARK, [F('stud', CONTENT, [], stud0)],
          instances=[('stud 1', None), ('stud 2', mirror_x)], bought=True),
        P('washer', 'washer M12', 'Steel', 'Fasteners (bought in)', STEEL, [F('washer', CONTENT, [], washer)],
          instances=[('washer 1', None), ('washer 2', mirror_x)], bought=True),
        P('nut', 'hex nut M12', 'Steel, grade 8', 'Fasteners (bought in)', DARK, [F('nut', CONTENT, [], nut)],
          instances=[('nut 1', None), ('nut 2', mirror_x)], bought=True),
        P('grease_nipple', 'grease nipple M6', 'Zinc plated steel', 'Fasteners (bought in)', BRASS, [F('nipple', CONTENT, [], nip)],
          bought=True),
    ]
    bearing = ['bearing outer ring', 'bearing inner ring', 'bearing cage'] + [n for n, tf in balls]
    assembly = [
        ('place the housing base', PLACE, ['Place housing_base.ipt, right click, Place Grounded at Origin.'], ['housing base']),
        ('build the bearing', CONSTRAIN,
         ['Place the outer ring, inner ring and cage. Constrain > Mate their axes and Flush their middle planes.',
          'Place ball.ipt nine times: Mate each ball centre to the pitch circle and to a cage pocket.',
          'Inventor users can save this as a sub-assembly, bearing_6208.iam.'], bearing),
        ('drop the shaft and bearing into the base', CONSTRAIN,
         ['Place shaft.ipt. Insert: the bearing bore onto the shaft, with the bearing in the middle of the shaft.',
          'Constrain > Mate: the shaft axis to the bore axis of the base, and Flush the bearing middle plane with the base middle plane.'],
         ['shaft']),
        ('felt seals', CONSTRAIN, ['Place felt_seal.ipt twice. Mate each to the shaft axis and Flush it with the side of its groove.'],
         ['felt seal 1', 'felt seal 2']),
        ('studs', CONTENT, ['Place from Content Center: Fasteners > Bolts > Studs, M12 x 74. Insert one into each tapped hole.'],
         ['stud 1', 'stud 2']),
        ('fit the cap', CONSTRAIN, ['Place housing_cap.ipt. Mate its split face to the split face of the base, and Insert a stud hole onto each stud.'],
         ['housing cap']),
        ('washers and nuts', CONTENT, ['Place from Content Center: ISO 7089 M12 washer and ISO 4032 M12 nut, two of each. Insert them on the studs.'],
         ['washer 1', 'washer 2', 'nut 1', 'nut 2']),
        ('grease nipple', CONTENT, ['Place from Content Center: Fittings > Grease Nipple, straight, M6. Insert it into the hole on the top boss.'],
         ['grease nipple M6'], 'Grease pumped in here fills the space each side of the bearing; the felt seals keep it in and the dirt out.'),
    ]
    ex = {'housing cap': (0, 0, 110), 'washer 1': (0, 0, 150), 'washer 2': (0, 0, 150), 'nut 1': (0, 0, 175),
          'nut 2': (0, 0, 175), 'grease nipple M6': (0, 0, 160), 'stud 1': (0, 0, 70), 'stud 2': (0, 0, 70),
          'felt seal 1': (0, 50, 55), 'felt seal 2': (0, -50, 55), 'shaft': (0, 0, 55), 'bearing outer ring': (0, 0, 55),
          'bearing inner ring': (0, 0, 55), 'bearing cage': (0, 0, 55)}
    ex.update({n: (0, 0, 55) for n, tf in balls})
    return dict(name='plummer_block', title='Plummer block bearing', parts=parts, assembly=assembly, explode=ex,
                description='A split plummer block (pillow block) carrying a 40 mm shaft on a 6208 ball bearing: cast iron base and cap '
                            'held by studs and nuts, the bearing modelled ring by ring with its nine balls and cage, felt seals and a '
                            'grease nipple. 24 parts.',
                uses='Assembly and section drawings of a split housing, a rolling bearing shown in section, parts list, studs and nuts.',
                criteria='3.1, 3.2', section='x', iso=(1, -1.2, 0.9))


# ================================================================== 2 spur gearbox
@functools.lru_cache(None)
def spur_gearbox():
    M, Z1, Z2, FACE = 2.5, 20, 40, 25
    CD = M * (Z1 + Z2) / 2       # 75
    ZC = 72                      # shaft centre height
    X1, X2 = 0, CD
    IN = (-35, CD + 60, -30, 30, 12)      # inside of the housing: x0, x1, y0, y1, floor top
    OUT = (-45, CD + 70, -44, 44, 0, 135)  # outside: x0, x1, y0, y1, z0, top
    RBR = 23.5                    # 6204 bearing outside radius (47 diameter, 20 bore, 14 wide)
    CAP_R, CAP_T, PCD_R = 34, 8, 29
    FEET = [(OUT[0] - 12, 0), (OUT[1] + 12, 0)]

    # housing
    h1 = _box(OUT[0], OUT[1], OUT[2], OUT[3], OUT[4], OUT[5])
    h1 = h1.union(_box(OUT[0] - 25, OUT[1] + 25, OUT[2], OUT[3], 0, 12))
    h2 = h1.cut(_box(IN[0], IN[1], IN[2], IN[3], IN[4], OUT[5] + 1))
    h3 = h2
    for x in (X1, X2):
        h3 = h3.cut(ycyl(RBR, OUT[2] - 1, OUT[3] + 1, x, ZC))
    h4 = h3
    cap_holes = []
    for x, angs in ((X1, (90, 210, 330)), (X2, (90, 210, 330))):
        for a in angs:
            px, pz = x + PCD_R * math.cos(math.radians(a)), ZC + PCD_R * math.sin(math.radians(a))
            cap_holes.append((px, pz))
            h4 = h4.cut(ycyl(2.5, OUT[3] - 10, OUT[3] + 1, px, pz)).cut(ycyl(2.5, OUT[2] - 1, OUT[2] + 10, px, pz))
    cover_pts = [(x, y) for x in (OUT[0] + 15, (OUT[0] + OUT[1]) / 2, OUT[1] - 15) for y in (37, -37)]
    h5 = h4
    for x, y in cover_pts:
        h5 = h5.cut(zcyl(3, OUT[5] - 12, OUT[5] + 1, x, y))
    for x in (OUT[0] - 12.5, OUT[1] + 12.5):
        for y in (30, -30):
            h5 = h5.cut(zcyl(5.5, -1, 13, x, y))
    h6 = h5.cut(xcyl(6, OUT[1] - 11, OUT[1] + 1, 0, 22))
    # cover
    cv0 = _box(OUT[0], OUT[1], OUT[2], OUT[3], OUT[5], OUT[5] + 8)
    cv = cv0
    for x, y in cover_pts:
        cv = cv.cut(_csk((x, y, OUT[5] + 8), (0, 0, -1), 6.6, 12, 10))
    cv = cv.cut(zcyl(8, OUT[5] - 1, OUT[5] + 9, (OUT[0] + OUT[1]) / 2, 0))
    cv = cv.edges('|Z').fillet(5)
    # gears and shafts (shafts along Y)
    g1 = involute_gear(M, Z1, FACE).rotate((0, 0, 0), (1, 0, 0), -90).translate((X1, -FACE / 2, ZC))
    p1 = ycyl(10, -44, 90, X1, ZC).union(ycyl(12, -30, 30, X1, ZC))
    p2 = p1.union(g1.intersect(ycyl(40, -FACE / 2, FACE / 2, X1, ZC)))
    p3 = p2.cut(_box(X1 - 3, X1 + 3, 55, 85, ZC + 10 - 3.5, ZC + 11)).faces('>Y or <Y').chamfer(1)
    g2 = involute_gear(M, Z2, FACE).rotate((0, 0, 0), (0, 0, 1), 180 / Z2).rotate((0, 0, 0), (1, 0, 0), -90).translate((X2, -FACE / 2, ZC))
    w1 = g2.cut(ycyl(12, -20, 20, X2, ZC))
    w2 = w1.cut(_box(X2 - 4, X2 + 4, -20, 20, ZC, ZC + 12 + 3.3))
    web = yring(20, 42, -FACE / 2 + 7, FACE / 2 - 7, X2, ZC)
    w3 = w2.cut(yring(20, 41, -FACE / 2 - 1, -FACE / 2 + 7, X2, ZC)).cut(yring(20, 41, FACE / 2 - 7, FACE / 2 + 1, X2, ZC))
    w4 = w3
    for k in range(6):
        a = math.radians(60 * k + 30)
        w4 = w4.cut(ycyl(6, -20, 20, X2 + 30.5 * math.cos(a), ZC + 30.5 * math.sin(a)))
    s1 = ycyl(10, -90, 44, X2, ZC).union(ycyl(12, -30, 30, X2, ZC))
    s2 = s1.cut(_box(X2 - 4, X2 + 4, -16, 16, ZC + 12 - 4, ZC + 13)).cut(_box(X2 - 3, X2 + 3, -85, -55, ZC + 10 - 3.5, ZC + 11))
    s3 = s2.faces('>Y or <Y').chamfer(1)
    key = _box(X2 - 4, X2 + 4, -15, 15, ZC + 12 - 4, ZC + 12 + 3.3).edges('|Z').fillet(3.9)
    # bearings (single bought-in parts), caps, seals
    brg = yring(10, RBR, 30, 44, X1, ZC)
    for y0 in (29.6, 43.6):          # the shields each side, drawn as shallow recesses between the rings
        brg = brg.cut(yring(13.5, 20, y0, y0 + 0.8, X1, ZC))

    def cap(through):
        c = ycyl(CAP_R, 44, 44 + CAP_T, X1, ZC).faces('>Y').chamfer(0.8)
        for a in (90, 210, 330):
            px, pz = X1 + PCD_R * math.cos(math.radians(a)), ZC + PCD_R * math.sin(math.radians(a))
            c = c.cut(ycyl(2.75, 43, 45 + CAP_T, px, pz)).cut(ycyl(4.6, 44 + CAP_T - 3, 45 + CAP_T, px, pz))
        if through:
            c = c.cut(ycyl(16, 43, 50, X1, ZC)).cut(ycyl(11, 43, 53, X1, ZC))
        return c
    capt, capb = cap(True), cap(False)
    seal = yring(10, 16, 44, 50, X1, ZC)
    scr = cap_screw(5, 12, 8.5, 5, (X1 + PCD_R * math.cos(math.radians(90)), 44 + CAP_T - 3, ZC + PCD_R), (0, -1, 0))

    def at(x, y_mirror, a=None):
        f = [T(x - X1, 0, 0)]
        if y_mirror:
            f = [R((X1, 0, ZC), (0, 0, 1), 180), T(x - X1, 0, 0)]
        return chain(*f)
    cs = []
    for x, side, tag in ((X1, False, 'A'), (X1, True, 'B'), (X2, False, 'C'), (X2, True, 'D')):
        for k, a in enumerate((0, 120, 240)):
            cs.append(('cap screw %s%d' % (tag, k + 1), chain(R((X1, 0, ZC), (0, 1, 0), -a), at(x, side))))
    cover_scr = csk_screw(6, 16, 12, (0, 0, OUT[5] + 8), (0, 0, -1))
    plug = zcyl(8, OUT[5] + 2, OUT[5] + 8, (OUT[0] + OUT[1]) / 2, 0).union(
        hex_prism(22, 8).translate(((OUT[0] + OUT[1]) / 2, 0, OUT[5] + 8))).union(
        zcyl(8, OUT[5] - 6, OUT[5] + 2, (OUT[0] + OUT[1]) / 2, 0))
    plug = plug.cut(zcyl(8, OUT[5] - 7, OUT[5] + 0.0, (OUT[0] + OUT[1]) / 2, 0))
    drain = xcyl(6, OUT[1] - 10, OUT[1], 0, 22).union(orient(hex_prism(17, 7), 'x').translate((OUT[1], 0, 22)))

    parts = [
        P('housing', 'gearbox housing', 'EN-GJL-250 grey cast iron', 'Housing', IRON, [
            F('solid block and feet', EXTRUDE,
              ['Sketch a rectangle 190 x 88 on the XZ Plane and Extrude it 135 mm up.',
               'Sketch a rectangle 240 x 88 on the bottom face and Extrude it 12 mm (the mounting feet), Join.'], h1),
            F('shell it out', '3D Model tab > Modify panel > Shell',
              ['Shell: remove the top face, thickness 10 mm on the end walls. Then Extrude Cut the side walls back so they are 14 thick '
               '(they carry the bearings), and the floor 12.'], h2,
              note='A cast housing is hollow so the gears can run in oil, with walls thick enough to hold the bearings.'),
            F('bearing bores', HOLE, ['Two holes on a side wall, 72 up, 75 apart: Simple Hole, diameter 47 (H7), Through All.'], h3),
            F('tapped holes for the bearing caps', CIRC,
              ['Hole on the side wall: Tapped M5x0.8, 10 deep, 29 from the bore centre, straight up.',
               'Circular Pattern: 3 holes round each bore. Mirror to the other side wall.'], h4),
            F('holes for the cover and the feet', HOLE,
              ['Hole on the top of the walls: 6 Tapped Holes M6x1, 12 deep.',
               'Hole on the feet: 4 Simple Holes diameter 11 for M10 holding down bolts.'], h5),
            F('drain hole', HOLE, ['Hole on the right end wall, 22 up: Tapped Hole M12x1.5, Through All.'], h6),
        ]),
        P('cover', 'cover', 'EN AW-5083 aluminium', 'Housing', ALU, [
            F('plate', EXTRUDE, ['Sketch a 190 x 88 rectangle on the top of the housing and Extrude 8 mm.'], cv0),
            F('holes and corners', HOLE, ['Hole: 6 x countersunk diameter 6.6, 12 x 90 degrees. Hole diameter 16 (Tapped M16) in the middle '
                                          'for the oil filler. Fillet the four corners 5 mm.'], cv),
        ]),
        P('pinion_shaft', 'input pinion shaft', '655M13 case hardened steel', 'Gears and shafts', ORANGE, [
            F('shaft', REVOLVE, ['Sketch the half section: 20 diameter journals, 24 diameter in the middle from 30 to 30. Revolve.'], p1),
            F('pinion teeth', SPUR,
              ['Design tab > Spur Gear: Module 2.5, 20 teeth, face width 25, pressure angle 20. Gear 1 on the shaft cylinder.',
               'Or sketch one tooth space with the involute and pattern it 20 times.'], p2,
              note='A small pinion is cut straight on its shaft: it is smaller than a hub and key would need.'),
            F('keyway and chamfers', EXTRUDE, ['Sketch a 6 x 30 keyway on the input end. Extrude Cut 3.5 deep. Chamfer the ends 1 mm.'], p3),
        ]),
        P('wheel', 'gear wheel', '080M40 steel, hardened', 'Gears and shafts', GREEN, [
            F('teeth', SPUR, ['Spur Gear: Module 2.5, 40 teeth, face 25. The centre distance is (20 + 40) x 2.5 / 2 = 75 mm.'], g2),
            F('bore', HOLE, ['Hole on the gear centre: diameter 24 (H7), Through All.'], w1),
            F('keyway', EXTRUDE, ['Sketch an 8 x 3.3 keyway on the bore. Extrude Cut Through All.'], w2),
            F('recessed web', REVOLVE, ['Revolve Cut the two side recesses from diameter 40 to 82, 7 deep, leaving a 11 mm web.'], w3),
            F('lightening holes', CIRC, ['Hole diameter 12 in the web, 30.5 from the centre. Circular Pattern: 6.'], w4),
        ]),
        P('output_shaft', 'output shaft', '080M40 steel', 'Gears and shafts', STEEL, [
            F('shaft', REVOLVE, ['Revolve the half section: 20 journals, 24 in the middle.'], s1),
            F('keyways', EXTRUDE, ['Keyway 8 x 4 x 32 for the wheel; keyway 6 x 3.5 x 30 on the output end. Extrude Cut each.'], s2),
            F('chamfers', CHAMFER, ['Chamfer 1 mm on both ends.'], s3),
        ]),
        P('key', 'key 8 x 7 x 30', 'Bright steel', 'Gears and shafts', DARK,
          [F('key', EXTRUDE, ['Sketch an 8 x 30 slot shape and Extrude 7.3 mm.'], key)]),
        P('bearing', 'ball bearing 6204', 'Bought in', 'Bought in', STEEL, [F('bearing', BEARING, [], brg)],
          instances=[('bearing A', None), ('bearing B', R((X1, 0, ZC), (0, 0, 1), 180)), ('bearing C', T(CD, 0, 0)),
                     ('bearing D', chain(R((X1, 0, ZC), (0, 0, 1), 180), T(CD, 0, 0)))], bought=True),
        P('cap_through', 'through cap', 'EN AW-5083 aluminium', 'Housing', ALU, [
            F('disc and screw holes', EXTRUDE, ['Sketch a 68 circle, Extrude 8. Holes: 3 counterbored for M5 on a 58 PCD.'], cap(False)),
            F('seal pocket', HOLE, ['Hole on the inside face: diameter 32, 6 deep (seal pocket), then diameter 22 Through All.'], capt),
        ], instances=[('through cap (input)', None), ('through cap (output)', chain(R((X1, 0, ZC), (0, 0, 1), 180), T(CD, 0, 0)))]),
        P('cap_blind', 'blind cap', 'EN AW-5083 aluminium', 'Housing', ALU, [
            F('disc, holes and chamfer', EXTRUDE, ['Sketch a 68 circle, Extrude 8. Holes for M5 on a 58 PCD. Chamfer the outside edge 0.8.'], capb),
        ], instances=[('blind cap (input)', R((X1, 0, ZC), (0, 0, 1), 180)), ('blind cap (output)', T(CD, 0, 0))]),
        P('lip_seal', 'lip seal 20 x 32 x 6', 'Nitrile rubber', 'Bought in', RUBBER, [F('seal', CONTENT, [], seal)],
          instances=[('lip seal (input)', None), ('lip seal (output)', chain(R((X1, 0, ZC), (0, 0, 1), 180), T(CD, 0, 0)))], bought=True),
        P('cap_screw', 'cap screw ISO 4762 M5 x 12', 'Steel, grade 12.9', 'Bought in', DARK, [F('screw', CONTENT, [], scr)],
          instances=cs, bought=True),
        P('cover_screw', 'countersunk screw ISO 10642 M6 x 16', 'Steel, grade 8.8', 'Bought in', DARK, [F('screw', CONTENT, [], cover_scr)],
          instances=[('cover screw %d' % (k + 1), T(x, y, 0)) for k, (x, y) in enumerate(cover_pts)], bought=True),
        P('filler_plug', 'filler plug M16', 'Steel', 'Bought in', DARK, [F('plug', CONTENT, [], plug)], bought=True),
        P('drain_plug', 'drain plug M12', 'Steel', 'Bought in', DARK, [F('plug', CONTENT, [], drain)], bought=True),
    ]
    caps_in = ['bearing A', 'bearing B', 'through cap (input)', 'blind cap (input)', 'lip seal (input)']
    asm = [
        ('place the housing', PLACE, ['Place housing.ipt Grounded at Origin.'], ['gearbox housing']),
        ('input pinion shaft and its bearings', CONSTRAIN,
         ['Place input_pinion_shaft.ipt and Mate its axis to the left bore axis. Place two 6204 bearings from Content Center '
          '(Shafts > Bearings > Ball Bearings, ISO 15, 6204) and Insert them onto the journals against the shoulders.'],
         ['input pinion shaft', 'bearing A', 'bearing B']),
        ('wheel, key and output shaft', CONSTRAIN,
         ['Place output_shaft.ipt in the right bore. Place the key and Insert it in its keyway.',
          'Place gear_wheel.ipt: Mate its bore to the shaft and its keyway to the key, Flush its middle with the pinion middle.',
          'Constrain > Motion > Rotation: pick the pinion and the wheel, ratio 2 (Reverse), so turning one turns the other.',
          'Place two more bearings on the output shaft.'], ['output shaft', 'key 8 x 7 x 30', 'gear wheel', 'bearing C', 'bearing D'],
         'Turn the input shaft with the mouse (Free Rotate is not needed: just drag a tooth) and the wheel turns at half the speed.'),
        ('bearing caps and seals', CONSTRAIN,
         ['Place the two through caps (where a shaft comes out) and two blind caps. Mate each to the wall and Insert a screw hole on a tapped hole.',
          'Place lip seals from Content Center (Shaft parts > Seals) in the through caps.'],
         ['through cap (input)', 'blind cap (input)', 'through cap (output)', 'blind cap (output)', 'lip seal (input)', 'lip seal (output)']),
        ('cap screws', CONTENT, ['Place from Content Center: ISO 4762 M5 x 12 socket head cap screws, 12 off. Insert each one in a cap counterbore.',
                                 'Tip: place one, then use Pattern Component, Associative, to follow the hole pattern.'],
         [n for n, tf in cs]),
        ('cover, screws and plugs', CONTENT,
         ['Place cover.ipt: Mate it to the top of the housing and line up the holes.',
          'Place 6 ISO 10642 M6 x 16 countersunk screws, the M16 filler plug and the M12 drain plug.'],
         ['cover'] + ['cover screw %d' % (k + 1) for k in range(6)] + ['filler plug M16', 'drain plug M12']),
    ]
    ex = {'cover': (0, 0, 120), 'filler plug M16': (0, 0, 170)}
    ex.update({'cover screw %d' % (k + 1): (0, 0, 150) for k in range(6)})
    ex.update({'input pinion shaft': (0, 0, 200), 'output shaft': (0, 0, 200), 'key 8 x 7 x 30': (0, 0, 230),
               'gear wheel': (0, 0, 260), 'drain plug M12': (50, 0, 0)})
    for n, s in (('A', 1), ('B', -1), ('C', 1), ('D', -1)):
        ex['bearing ' + n] = (0, s * 40, 200)
    for n, s, x in (('through cap (input)', 1, 0), ('blind cap (input)', -1, 0), ('through cap (output)', -1, 0),
                    ('blind cap (output)', 1, 0), ('lip seal (input)', 1, 0), ('lip seal (output)', -1, 0)):
        ex[n] = (0, s * (70 if 'seal' not in n else 55), 0)
    for n, tf in cs:
        ex[n] = (0, (1 if n[11] in 'AD' else -1) * 100, 0)
    return dict(name='spur_gearbox', title='Spur gearbox', parts=parts, assembly=asm, explode=ex,
                description='A single stage reduction gearbox: a 20 tooth pinion drives a 40 tooth wheel (module 2.5, ratio 2:1) on two shafts '
                            'carried by four 6204 ball bearings in a cast iron housing, with bearing caps, lip seals, a cover and oil plugs. 36 parts.',
                uses='Gear conventions (pitch circle, module, centre distance), keys and keyways, bearing housings, a large parts list.',
                criteria='3.1, 3.2', section='z', iso=(1, -1.3, 1))


# ================================================================== 3 universal joint
@functools.lru_cache(None)
def universal_joint():
    ARM_T, ARM_IN, ARM_W = 8, 22, 16       # yoke arm thickness, inside half gap, half width
    RCUP, RTR = 10, 7                      # bearing cup outside radius, trunnion radius
    HUB = (25, 60, 18, 11)                 # hub from x, to x, radius, bore radius

    # yoke: built along -X (the input side), arms on +-Y
    hub = xcyl(HUB[2], -HUB[1], -HUB[0], 0, 0)
    y1 = hub.union(_box(-HUB[0] - 3, -HUB[0] + 5, -ARM_IN - ARM_T, ARM_IN + ARM_T, -ARM_W, ARM_W))
    for s in (1, -1):
        arm = _box(-HUB[0] - 3, 0, min(s * ARM_IN, s * (ARM_IN + ARM_T)), max(s * ARM_IN, s * (ARM_IN + ARM_T)), -ARM_W, ARM_W)
        arm = arm.union(ycyl(ARM_W, min(s * ARM_IN, s * (ARM_IN + ARM_T)), max(s * ARM_IN, s * (ARM_IN + ARM_T))))
        y1 = y1.union(arm)
    y2 = y1.cut(ycyl(RCUP, -40, 40))
    y3 = y2.cut(xcyl(HUB[3], -HUB[1] - 1, -HUB[0] - 4))
    y4 = y3.cut(zcyl(4, 0, HUB[2] + 1, -45, 0))
    yoke = y4.faces('<X').chamfer(1.5)
    # cross (spider)
    c1 = _box(-10, 10, -10, 10, -10, 10)
    c2 = c1.union(ycyl(RTR, -29, 29)).union(zcyl(RTR, -29, 29))
    c3 = c2.cut(xcyl(2, -11, 11)).union(xcyl(3.5, 10, 14))
    cup0 = ycyl(RCUP, 20, 30).cut(ycyl(RTR, 19, 29))
    clip = yring(8.5, 13, 30, 31.2).cut(_box(-3, 3, 30 - 1, 32, 9, 14))
    shaft0 = xcyl(HUB[3], -140, -HUB[0] - 4)
    shaft = shaft0.cut(_box(-60, -30, -12, 12, HUB[3] - 1, HUB[3] + 1)).faces('<X').chamfer(1)
    grub = zcyl(4, HUB[3] - 1, HUB[2] - 1, -45, 0).cut(hex_prism(4, 3).translate((-45, 0, HUB[2] - 4)))

    turn_b = R((0, 0, 0), (1, 0, 0), 90)      # the output yoke: turned 90 degrees about the shaft line ...
    flip_b = R((0, 0, 0), (0, 0, 1), 180)     # ... and facing the other way
    yb = chain(flip_b, turn_b)
    cupz = R((0, 0, 0), (1, 0, 0), 90)
    mir = R((0, 0, 0), (0, 0, 1), 180)
    parts = [
        P('yoke', 'yoke', '709M40 alloy steel, forged', 'Yokes and cross', STEEL, [
            F('hub', EXTRUDE, ['Sketch a 36 mm circle on the YZ Plane. Extrude 35 mm.'], hub),
            F('bridge and arms', EXTRUDE,
              ['Sketch on the XY Plane the side view of one arm: 8 thick, from the hub to the joint centre, with a 16 radius end.',
               'Extrude 32 mm Symmetric. Mirror the arm about the XZ Plane. Add the bridge, 8 x 60 x 32.'], y1),
            F('cross holes for the bearing cups', HOLE, ['Hole through both arms on the joint centre: diameter 20 (H7), Through All.'], y2),
            F('shaft bore', HOLE, ['Hole on the end of the hub: diameter 22 (H7), 32 deep.'], y3),
            F('grub screw hole', HOLE, ['Hole on the hub, 20 from its end, from the top: Tapped M8x1.25 into the bore.'], y4),
            F('chamfer', CHAMFER, ['Chamfer 1.5 mm on the end of the hub.'], yoke),
        ], instances=[('input yoke', None), ('output yoke', yb)]),
        P('cross', 'cross (spider)', '815M17 case hardened steel', 'Yokes and cross', ORANGE, [
            F('centre block', EXTRUDE, ['Sketch a 20 x 20 square, Extrude 20 Symmetric.'], c1),
            F('four trunnions', EXTRUDE, ['Sketch a 14 circle on one face, Extrude 19. Circular Pattern: 4 about the X axis.'], c2),
            F('grease way and nipple boss', HOLE, ['Hole diameter 4 through the block for the grease. Extrude a 7 mm boss for the nipple.'], c3,
              note='Grease from the nipple runs down drillings in each trunnion to the needle bearings in the cups.'),
        ]),
        P('cup', 'bearing cup', 'Bearing steel (needle roller cup)', 'Bearings', BRASS,
          [F('cup', REVOLVE, ['Revolve the cup section: 20 outside, 14 inside, 10 long with a 1 mm closed end.'], cup0)],
          instances=[('cup 1', None), ('cup 2', mir), ('cup 3', cupz), ('cup 4', chain(cupz, R((0, 0, 0), (1, 0, 0), 180)))]),
        P('circlip', 'circlip 20', 'Spring steel', 'Bearings', DARK,
          [F('clip', EXTRUDE, ['Sketch circles 17 and 26, and a 6 mm gap. Extrude 1.2 mm.'], clip)],
          instances=[('circlip 1', None), ('circlip 2', mir), ('circlip 3', cupz), ('circlip 4', chain(cupz, R((0, 0, 0), (1, 0, 0), 180)))]),
        P('shaft', 'shaft 22', '080M40 steel', 'Shafts', STEEL, [
            F('shaft', EXTRUDE, ['Sketch a 22 circle and Extrude 111 mm.'], shaft0),
            F('flat for the grub screw', EXTRUDE, ['Sketch on a plane tangent to the top: 30 x 24. Extrude Cut 1 mm. Chamfer the free end 1 mm.'],
              shaft)], instances=[('input shaft', None), ('output shaft', yb)]),
        P('grub_screw', 'grub screw ISO 4027 M8 x 8', 'Steel, 45H', 'Bought in', DARK, [F('screw', CONTENT, [], grub)],
          instances=[('grub screw 1', None), ('grub screw 2', yb)], bought=True),
    ]
    asm = [
        ('input yoke', PLACE, ['Place yoke.ipt Grounded at Origin.'], ['input yoke']),
        ('cross into the input yoke', CONSTRAIN,
         ['Place cross.ipt. Constrain > Mate: the axis of one pair of trunnions to the cross hole axis in the yoke.',
          'Constrain > Angle: free, so the cross can swing.'], ['cross (spider)']),
        ('cups and circlips (input side)', CONSTRAIN,
         ['Place bearing_cup.ipt twice: Insert each over a trunnion and into a yoke hole.',
          'Place two circlips and Mate them against the outside of the arms.'], ['cup 1', 'cup 2', 'circlip 1', 'circlip 2']),
        ('output yoke', CONSTRAIN, ['Place yoke.ipt again. Mate its cross hole axis to the other pair of trunnions.'], ['output yoke']),
        ('cups and circlips (output side)', CONSTRAIN, ['Insert the last two cups and circlips the same way.'],
         ['cup 3', 'cup 4', 'circlip 3', 'circlip 4']),
        ('shafts and grub screws', CONTENT,
         ['Place shaft_22.ipt twice and Insert each into a yoke bore. Turn the flat to the top.',
          'Place from Content Center: ISO 4027 M8 x 8 cup point grub screws, and Insert one in each hub.'],
         ['input shaft', 'output shaft', 'grub screw 1', 'grub screw 2'],
         'A universal joint passes the turning from one shaft to another that is at an angle to it, as in a car propeller shaft.'),
    ]
    ex = {'input yoke': (-60, 0, 0), 'output yoke': (60, 0, 0), 'input shaft': (-130, 0, 0), 'output shaft': (130, 0, 0),
          'grub screw 1': (-60, 0, 40), 'grub screw 2': (60, 40, 0), 'cup 1': (0, 25, 0), 'cup 2': (0, -25, 0),
          'cup 3': (0, 0, 25), 'cup 4': (0, 0, -25), 'circlip 1': (0, 45, 0), 'circlip 2': (0, -45, 0),
          'circlip 3': (0, 0, 45), 'circlip 4': (0, 0, -45)}
    return dict(name='universal_joint', title='Universal joint', parts=parts, assembly=asm, explode=ex,
                description='A Hooke type universal joint for 22 mm shafts: two forged yokes, a hardened cross with four trunnions, needle '
                            'bearing cups held by circlips, and the shafts fixed by grub screws. 15 parts.',
                uses='Assembly of parts at right angles, repeated parts placed by rotating, exploded views along three axes, angular motion.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.2, 0.9))


# ================================================================== 4 toggle clamp
TOGGLE = dict(A=(40.0, 40.0), B=(75.0, 20.0), D0=(54.0, 54.0), RH=15.0, OVER=4.0, TIP=-70.0, SPX=-55.0)


def _xz(p, r, ang):
    return (p[0] + r * math.cos(math.radians(ang)), p[1] + r * math.sin(math.radians(ang)))


def toggle_points():
    """Closed position: the handle crank point C sits a few degrees past the line from B to D (over centre)."""
    A, B, D = TOGGLE['A'], TOGGLE['B'], TOGGLE['D0']
    a_bd = math.degrees(math.atan2(D[1] - B[1], D[0] - B[0]))
    C = _xz(B, TOGGLE['RH'], a_bd + TOGGLE['OVER'])
    L = math.dist(C, D)
    return A, B, C, D, L


def toggle_pose(arm_turn):
    """The arm turned up by arm_turn degrees (counterclockwise seen from the front): the link and handle positions.
    Returns (D, C, handle angle change, link angle change), angles counterclockwise in degrees."""
    A, B, C0, D0, L = toggle_points()
    rA = math.dist(A, D0)
    a0 = math.degrees(math.atan2(D0[1] - A[1], D0[0] - A[0]))
    D = _xz(A, rA, a0 - arm_turn)
    # C is where the circle about B (radius RH) meets the circle about D (radius L): take the branch nearest the last C
    d = math.dist(B, D)
    a = (TOGGLE['RH'] ** 2 - L ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(TOGGLE['RH'] ** 2 - a ** 2, 0))
    ux, uz = (D[0] - B[0]) / d, (D[1] - B[1]) / d
    m = (B[0] + a * ux, B[1] + a * uz)
    cands = [(m[0] - h * uz, m[1] + h * ux), (m[0] + h * uz, m[1] - h * ux)]
    hb0 = math.atan2(C0[1] - B[1], C0[0] - B[0])
    C = min(cands, key=lambda c: abs(math.atan2(c[1] - B[1], c[0] - B[0]) - hb0))
    dh = math.degrees(math.atan2(C[1] - B[1], C[0] - B[0]) - hb0)
    dl = math.degrees(math.atan2(C[1] - D[1], C[0] - D[0]) - math.atan2(C0[1] - D0[1], C0[0] - D0[0]))
    return D, C, dh, dl


def _plate_xz(pts_r, y0, y1):
    """A plate in the XZ plane made of round-ended bars joining the given (x, z, r) bosses, from y0 to y1."""
    w = None
    for k in range(len(pts_r)):
        x, z, r = pts_r[k]
        c = ycyl(r, y0, y1, x, z)
        w = c if w is None else w.union(c)
        if k:
            px, pz, pr = pts_r[k - 1]
            ang = math.atan2(z - pz, x - px)
            hw = min(r, pr)
            nx, nz = -math.sin(ang) * hw, math.cos(ang) * hw
            poly = cq.Workplane('XZ', origin=(0, y1, 0)).polyline([(px + nx, pz + nz), (x + nx, z + nz), (x - nx, z - nz),
                                                                  (px - nx, pz - nz)]).close().extrude(y1 - y0)
            w = w.union(poly)
    return w


@functools.lru_cache(None)
def toggle_clamp():
    A, B, C, D, L = toggle_points()
    T_ = TOGGLE
    CHEEK = (10, 13)                 # cheek inside and outside y
    PIN_R = 3
    # base: a pressed steel plate with two cheeks bent up
    b1 = _box(20, 95, -20, 20, 0, 4).edges('|Z').fillet(5)
    cheek_pts = [(25, 4), (95, 4), (95, 34), (60, 60), (25, 60)]
    cheeks = None
    for s in (1, -1):
        y0, y1 = (CHEEK[0], CHEEK[1]) if s > 0 else (-CHEEK[1], -CHEEK[0])
        ch = cq.Workplane('XZ', origin=(0, y1, 0)).polyline(cheek_pts).close().extrude(y1 - y0)
        cheeks = ch if cheeks is None else cheeks.union(ch)
    b2 = b1.union(cheeks)
    b3 = b2
    for p in (A, B):
        b3 = b3.cut(ycyl(PIN_R, -20, 20, p[0], p[1]))
    b4 = b3
    for x in (32, 83):
        for y in (14, -14):
            b4 = b4.cut(zcyl(3.25, -1, 5, x, y))
    # arm: a bar from the spindle slot to the pivot, with a tail up to the link pin
    zc = A[1]
    a1 = _box(T_['TIP'], A[0], -6, 6, zc - 8, zc + 8).union(ycyl(8, -6, 6, A[0], zc)).union(_plate_xz([(A[0], zc, 8), (D[0], D[1], 7)], -6, 6))
    a1 = a1.union(ycyl(8, -6, 6, T_['TIP'], zc))
    a2 = a1.cut(cq.Workplane('XY').center(T_['SPX'] + 3, 0).slot2D(26, 8.5, 0).extrude(100).translate((0, 0, -10)))
    a3 = a2.cut(ycyl(PIN_R, -7, 7, A[0], zc)).cut(ycyl(PIN_R, -7, 7, D[0], D[1]))
    # handle: hub at B, crank lug to C, lever up and back, round end for the grip
    hang = 50
    E = _xz(B, 70, hang)
    G = _xz(B, 150, hang)
    h1 = _plate_xz([(C[0], C[1], 6), (B[0], B[1], 8), (E[0], E[1], 5)], -6, 6)
    rod = _cyl(5, (E[0], 0, E[1]), (math.cos(math.radians(hang)), 0, math.sin(math.radians(hang))), 80)
    h2 = h1.union(rod)
    h3 = h2.cut(ycyl(PIN_R, -7, 7, B[0], B[1])).cut(ycyl(PIN_R, -7, 7, C[0], C[1]))
    grip = _cyl(10, (E[0] + 5 * math.cos(math.radians(hang)), 0, E[1] + 5 * math.sin(math.radians(hang))),
                (math.cos(math.radians(hang)), 0, math.sin(math.radians(hang))), 75)
    grip = grip.cut(rod)
    # link plates, pins
    lk0 = _plate_xz([(D[0], D[1], 6), (C[0], C[1], 6)], 6.5, 8.5)
    lk = lk0.cut(ycyl(PIN_R, 6, 9, D[0], D[1])).cut(ycyl(PIN_R, 6, 9, C[0], C[1]))

    def pin(p, half, head):
        return ycyl(PIN_R, -half, half, p[0], p[1]).union(ycyl(5, half, half + head, p[0], p[1])).union(
            ycyl(5, -half - head, -half, p[0], p[1]))
    pinA, pinB = pin(A, CHEEK[1], 1.5), pin(B, CHEEK[1], 1.5)
    pinD, pinC = pin(D, 8.5, 1), pin(C, 8.5, 1)
    # spindle, nuts and pad
    sx = T_['SPX']
    sp = zcyl(4, 10, zc + 24, sx, 0).faces('>Z').chamfer(0.8)
    nut_lo = hex_nut(13, 6.5, 8, (sx, 0, zc - 8 - 6.5))
    nut_hi = hex_nut(13, 6.5, 8, (sx, 0, zc + 8))
    pad = zcyl(9, 2, 10, sx, 0).union(zcyl(6, 10, 14, sx, 0)).cut(zcyl(4, 6, 15, sx, 0)).faces('<Z').edges().fillet(2)
    sp = sp.union(zcyl(4, 6, 10, sx, 0))

    mir = R((0, 0, 0), (0, 0, 1), 180)
    parts = [
        P('base', 'base', 'S275 steel sheet, 3 mm, zinc plated', 'Frame', BLUE, [
            F('base plate', EXTRUDE, ['Sketch a 75 x 40 rectangle on the XZ Plane (the ground). Extrude 4 mm. Fillet the corners 5 mm.'], b1),
            F('two cheeks', EXTRUDE,
              ['Sketch the cheek outline on the XY Plane (the front): 70 long, 60 high with a sloping top. Extrude 3 mm, 10 mm out from '
               'the middle. Mirror it about the XY Plane.'], b2,
              note='In the factory the base and cheeks are one blank, pressed and bent up. Inventor can model it that way with the Sheet Metal tools.'),
            F('pivot holes', HOLE, ['Hole through both cheeks at the arm pivot (40, 40) and the handle pivot (75, 20): diameter 6, Through All.'], b3),
            F('fixing holes', RECT, ['Hole diameter 6.5 in the base, then Rectangular Pattern 2 x 2: 51 apart along the base and 28 across.'], b4),
        ]),
        P('arm', 'clamp arm', 'C45 steel, blackened', 'Moving parts', ORANGE, [
            F('bar and tail', EXTRUDE,
              ['Sketch on the XY Plane: a 110 x 16 bar from the pivot to the front, rounded both ends, and a tail from the pivot up to '
               'the link pin at (54, 54). Extrude 12 mm Symmetric.'], a1),
            F('spindle slot', EXTRUDE, ['Sketch a Slot 17.5 long x 8.5 wide on the top, at the front end. Extrude Cut Through All.'], a2,
              note='The slot lets the spindle be moved along to suit the work.'),
            F('pin holes', HOLE, ['Hole diameter 6 at the pivot and at the tail. Through All.'], a3),
        ]),
        P('handle', 'handle', 'C45 steel, blackened', 'Moving parts', ORANGE, [
            F('crank and lever', EXTRUDE,
              ['Sketch on the XY Plane: the hub (16 diameter) at the handle pivot, a lug 15 long to the link pin, and a 10 wide lever '
               '70 long at 50 degrees. Extrude 12 Symmetric.'], h1),
            F('round end for the grip', EXTRUDE, ['Work Plane at the end of the lever. Circle diameter 10, Extrude 80 along the lever.'], h2),
            F('pin holes', HOLE, ['Hole diameter 6 at the pivot and at the lug. Through All.'], h3),
        ]),
        P('link', 'link plate', 'S275 steel, 2 mm', 'Moving parts', STEEL, [
            F('plate', EXTRUDE, ['Sketch two 12 mm circles %.1f apart and the tangent lines. Extrude 2 mm.' % L], lk0),
            F('holes', HOLE, ['Hole diameter 6 at both centres.'], lk),
        ], instances=[('link plate 1', None), ('link plate 2', lambda w: w.mirror('XZ'))]),
        P('pin_long', 'pivot pin 6 x 26', 'Steel, case hardened', 'Pins', DARK,
          [F('pin', REVOLVE, ['Revolve the pin section: 6 diameter, 26 long, with 10 x 1.5 heads (the second head is riveted over).'], pinA)],
          instances=[('pivot pin A', None), ('pivot pin B', T(B[0] - A[0], 0, B[1] - A[1]))]),
        P('pin_short', 'link pin 6 x 17', 'Steel, case hardened', 'Pins', DARK,
          [F('pin', REVOLVE, ['Revolve the pin section: 6 diameter, 17 long, with 10 x 1 heads.'], pinD)],
          instances=[('link pin D', None), ('link pin C', T(C[0] - D[0], 0, C[1] - D[1]))]),
        P('spindle', 'spindle M8 x 66', 'Steel, zinc plated', 'Spindle', STEEL,
          [F('threaded rod', EXTRUDE, ['Sketch an 8 mm circle, Extrude 66 mm. Chamfer the top. Thread M8x1.25, Full Length.'], sp)]),
        P('nut', 'hex nut M8', 'Steel, zinc plated', 'Bought in', DARK, [F('nut', CONTENT, [], nut_lo)],
          instances=[('nut (lower)', None), ('nut (upper)', T(0, 0, nut_hi.val().BoundingBox().zmin - nut_lo.val().BoundingBox().zmin))],
          bought=True),
        P('pad', 'pressure pad', 'Neoprene rubber', 'Spindle', RUBBER,
          [F('pad', REVOLVE, ['Revolve the pad section: 18 diameter x 8, a 12 diameter neck, an 8 mm bore. Fillet the bottom edge 2 mm.'], pad)]),
        P('grip', 'handle grip', 'PVC, red', 'Moving parts', RED,
          [F('grip', REVOLVE, ['Revolve the grip section: 20 diameter, 75 long, 10 mm bore.'], grip)]),
    ]
    asm = [
        ('place the base', PLACE, ['Place base.ipt Grounded at Origin.'], ['base']),
        ('arm and pivot pin', CONSTRAIN, ['Place clamp_arm.ipt between the cheeks. Constrain > Insert the pivot hole on the cheek hole.',
                                          'Place pivot_pin.ipt through both with Insert.'], ['clamp arm', 'pivot pin A']),
        ('handle and pivot pin', CONSTRAIN, ['Place handle.ipt between the cheeks. Insert its hub on the rear cheek hole, and the second pivot pin.'],
         ['handle', 'pivot pin B']),
        ('links and link pins', CONSTRAIN,
         ['Place link_plate.ipt twice, one each side of the arm tail. Insert one end on the tail hole and the other on the handle lug.',
          'Place the two link pins with Insert.'], ['link plate 1', 'link plate 2', 'link pin D', 'link pin C'],
         'Drag the handle: the arm swings up and down. With the handle down, the link pin C is just past the line through the other two '
         'pins, so pushing on the arm cannot open it. That is the toggle (over centre) action.'),
        ('spindle, nuts and pad', CONTENT,
         ['Place spindle.ipt in the slot and two ISO 4032 M8 nuts from Content Center, one each side of the arm.',
          'Place pressure_pad.ipt on the bottom of the spindle and grip.ipt on the handle.'],
         ['spindle M8 x 66', 'nut (lower)', 'nut (upper)', 'pressure pad', 'handle grip']),
    ]
    ex = {'clamp arm': (-40, 0, 40), 'spindle M8 x 66': (-40, 0, 110), 'nut (lower)': (-40, 0, 60), 'nut (upper)': (-40, 0, 140),
          'pressure pad': (-40, 0, 20), 'handle': (50, 0, 40), 'handle grip': (90, 0, 90), 'link plate 1': (0, 30, 60),
          'link plate 2': (0, -30, 60), 'link pin D': (0, 60, 60), 'link pin C': (0, 60, 60), 'pivot pin A': (0, 50, 0),
          'pivot pin B': (0, 50, 0)}
    return dict(name='toggle_clamp', title='Toggle clamp', parts=parts, assembly=asm, explode=ex,
                description='A vertical hold-down toggle clamp: a pressed steel base, an arm with an adjustable M8 spindle and rubber pad, '
                            'a handle and two link plates on four pins. Pushing the handle down carries the link just past dead centre, '
                            'so the clamp locks shut. 14 parts.',
                uses='Linkages and pin joints, over-centre (toggle) action, sheet metal parts, assembly and exploded views.',
                criteria='3.1, 3.2', section='y', iso=(-1, -1.3, 0.9))


# ================================================================== 5 swivel castor
@functools.lru_cache(None)
def swivel_castor():
    RW, WW, AX = 50, 32, 35           # wheel radius, wheel width, axle offset from the swivel axis
    ZA = RW                           # axle height
    CROWN = (104, 110)
    BALL_Z, PCD, NB = 111.5, 30, 20
    TOP = (113, 117)
    LEG = (20, 24)
    # top plate
    t1 = _box(-45, 45, -45, 45, TOP[0], TOP[1]).edges('|Z').fillet(8)
    t2 = t1.cut(torus(PCD, 3, (0, 0, BALL_Z), (0, 0, 1)))
    t3 = t2.cut(zcyl(5, TOP[0] - 1, TOP[1] + 1))
    for x in (35, -35):
        for y in (35, -35):
            t3 = t3.cut(zcyl(4.5, TOP[0] - 1, TOP[1] + 1, x, y))
    # fork: crown and two legs, one pressing
    c1 = zcyl(40, CROWN[0], CROWN[1]).union(_box(0, AX + 14, -LEG[1], LEG[1], CROWN[0], CROWN[1]))
    legs = None
    for s in (1, -1):
        y0, y1 = (LEG[0], LEG[1]) if s > 0 else (-LEG[1], -LEG[0])
        lg = _box(AX - 12, AX + 12, y0, y1, ZA, CROWN[0]).union(ycyl(12, y0, y1, AX, ZA))
        legs = lg if legs is None else legs.union(lg)
    f2 = c1.union(legs)
    f3 = f2.cut(torus(PCD, 3, (0, 0, BALL_Z), (0, 0, 1))).cut(zcyl(5, CROWN[0] - 1, CROWN[1] + 1))
    f4 = f3.cut(ycyl(5.25, -30, 30, AX, ZA))
    ball = sphere(2.95, (PCD, 0, BALL_Z))
    kp = zcyl(5, CROWN[0] - 2, TOP[1], 0, 0).union(zcyl(9, TOP[1], TOP[1] + 4, 0, 0)).union(zcyl(8, CROWN[0] - 4, CROWN[0], 0, 0))
    kp = kp.faces('>Z').edges().fillet(2)
    # wheel
    hub0 = ycyl(36, -WW / 2, WW / 2, AX, ZA)
    hub1 = hub0.cut(yring(14, 30, WW / 2 - 8, WW / 2 + 1, AX, ZA)).cut(yring(14, 30, -WW / 2 - 1, -WW / 2 + 8, AX, ZA))
    hub = hub1.cut(ycyl(10, -20, 20, AX, ZA))
    tyre0 = yring(36, RW, -15, 15, AX, ZA)
    tyre = tyre0.edges(cq.selectors.RadiusNthSelector(-1)).fillet(5)
    tube = yring(5.25, 10, -WW / 2, WW / 2, AX, ZA)
    spacer = yring(5.25, 8, WW / 2, LEG[0], AX, ZA)
    bolt_ = ycyl(5, -LEG[1], LEG[1] + 10, AX, ZA).union(orient(hex_prism(16, 6.4), '-y').translate((AX, -LEG[1], ZA)))
    nut_ = orient(hex_prism(16, 8).cut(cq.Workplane('XY').circle(5).extrude(8)), 'y').translate((AX, LEG[1], ZA))
    mir = R((0, 0, 0), (0, 0, 1), 180)
    mir_axle = chain(T(-AX, 0, 0), mir, T(AX, 0, 0))
    balls = [('ball %d' % (k + 1), R((0, 0, 0), (0, 0, 1), 360 * k / NB)) for k in range(NB)]
    parts = [
        P('top_plate', 'top plate', 'S235 steel, zinc plated', 'Swivel head', BLUE, [
            F('square plate', EXTRUDE, ['Sketch a 90 x 90 square on the XZ Plane, Extrude 4 mm. Fillet the corners 8 mm.'], t1),
            F('ball track', REVOLVE, ['Sketch a 6 mm circle on a 60 mm pitch diameter, 1.5 below the plate. Revolve, Cut.'], t2,
              note='In the factory the track is pressed into the plate, not cut.'),
            F('holes', HOLE, ['Hole diameter 10 in the middle (king pin). Holes diameter 9 for the M8 fixing bolts, on a 70 x 70 square.'], t3),
        ]),
        P('fork', 'fork', 'S355 steel, pressed, zinc plated', 'Fork', BLUE, [
            F('crown', EXTRUDE, ['Sketch an 80 diameter circle with a 49 x 48 tab towards the axle. Extrude 6 mm.'], c1),
            F('legs', EXTRUDE, ['Sketch the leg on the XY Plane, 24 wide with a 12 radius end round the axle. Extrude 4 mm, 20 out from '
                                'the middle, Join. Mirror it.'], f2),
            F('ball track and king pin hole', REVOLVE, ['Revolve Cut the 6 mm track (60 pitch diameter) in the top of the crown. Hole 10 in the middle.'],
              f3),
            F('axle hole', HOLE, ['Hole through both legs at the axle: diameter 10.5, Through All.'], f4,
              note='The axle is 35 mm behind the swivel axis, so the wheel trails behind and lines itself up with the direction of travel.'),
        ]),
        P('ball', 'ball 6 mm', 'Carbon steel', 'Swivel head', STEEL, [F('sphere', REVOLVE, ['Revolve a half circle, diameter 5.9.'], ball)],
          instances=balls),
        P('king_pin', 'king pin rivet', 'Steel, case hardened', 'Swivel head', DARK,
          [F('rivet', REVOLVE, ['Revolve the rivet: 10 shank, 18 head, 16 peened head underneath. Fillet the top 2 mm.'], kp)]),
        P('hub', 'wheel centre', 'Polypropylene', 'Wheel', GREEN, [
            F('disc', EXTRUDE, ['Sketch a 72 circle on the XY Plane at the axle. Extrude 32 Symmetric.'], hub0),
            F('dished sides', REVOLVE, ['Revolve Cut a recess from diameter 28 to 60, 8 deep, on each side.'], hub1),
            F('bore', HOLE, ['Hole diameter 20 through the middle for the roller bearing tube.'], hub),
        ]),
        P('tyre', 'tyre', 'Rubber, 80 Shore A', 'Wheel', BLACK, [
            F('ring', EXTRUDE, ['Sketch circles 72 and 100. Extrude 30 Symmetric.'], tyre0),
            F('rounded edges', FILLET, ['Fillet 5 mm on the two outside edges.'], tyre),
        ]),
        P('tube', 'bearing tube', 'Steel (plain roller bearing)', 'Wheel', STEEL,
          [F('tube', EXTRUDE, ['Sketch circles 10.5 and 20. Extrude 32 Symmetric.'], tube)]),
        P('spacer', 'spacer', 'Steel', 'Wheel', STEEL, [F('tube', EXTRUDE, ['Sketch circles 10.5 and 16. Extrude 4.'], spacer)],
          instances=[('spacer 1', None), ('spacer 2', mir_axle)]),
        P('axle_bolt', 'axle bolt M10 x 58', 'Steel, grade 8.8', 'Bought in', DARK, [F('bolt', CONTENT, [], bolt_)], bought=True),
        P('axle_nut', 'nut M10', 'Steel, grade 8', 'Bought in', DARK, [F('nut', CONTENT, [], nut_)], bought=True),
    ]
    wheel = ['wheel centre', 'tyre', 'bearing tube', 'spacer 1', 'spacer 2']
    asm = [
        ('place the fork', PLACE, ['Place fork.ipt Grounded at Origin.'], ['fork']),
        ('balls in the track', CONSTRAIN, ['Place ball.ipt and Mate its centre to the circle at the bottom of the track.',
                                           'Pattern Component: Circular, 20 balls round the swivel axis.'], [n for n, tf in balls]),
        ('top plate and king pin', CONSTRAIN, ['Place top_plate.ipt: Mate its track onto the balls and its centre hole to the fork centre.',
                                               'Place king_pin_rivet.ipt with Insert into the centre holes.'],
         ['top plate', 'king pin rivet'], 'The rivet is peened over under the crown, but loose enough for the head to turn on the balls.'),
        ('wheel', CONSTRAIN, ['Place wheel_centre.ipt and tyre.ipt; Mate their axes and middle planes (the tyre is moulded on in the factory).',
                              'Place bearing_tube.ipt in the bore and the two spacers each side.'], wheel),
        ('axle bolt and nut', CONTENT, ['Place from Content Center: ISO 4017 M10 x 58 hex bolt and ISO 4032 M10 nut. Insert through the legs and wheel.'],
         ['axle bolt M10 x 58', 'nut M10']),
    ]
    ex = {'top plate': (0, 0, 70), 'king pin rivet': (0, 0, 120), 'axle bolt M10 x 58': (0, -90, 0), 'nut M10': (0, 80, 0),
          'spacer 1': (0, 45, 0), 'spacer 2': (0, -45, 0)}
    ex.update({n: (0, 0, 35) for n, tf in balls})
    ex.update({n: (0, 0, -70) for n in ('wheel centre', 'tyre', 'bearing tube')})
    return dict(name='swivel_castor', title='Swivel castor', parts=parts, assembly=asm, explode=ex,
                description='A 100 mm swivel castor: a top plate turning on 20 balls in a pressed track, a pressed steel fork held by a king '
                            'pin rivet, and a rubber tyred wheel on a bearing tube and M10 axle bolt. 30 parts.',
                uses='Ball races, offset (trailing) axles, pressed parts, an assembly with many repeated parts, section through the swivel.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.3, 0.8))


# ================================================================== 6 screw jack
@functools.lru_cache(None)
def screw_jack():
    PITCH = 6
    body_pts = [(45, 0), (60, 0), (60, 15), (40, 22), (32, 100), (35, 100), (35, 120), (28, 120), (28, 90), (19, 90), (19, 30)]
    prof = cq.Workplane('XZ').polyline(body_pts).close()
    b1 = prof.revolve(360, (0, 0, 0), (0, 1, 0))
    b2 = b1.cut(xcyl(4, 23.5, 36, 0, 110))
    b3 = b2
    for k in range(4):
        b3 = b3.cut(zcyl(5, -1, 16, 52 * math.cos(math.radians(45 + 90 * k)), 52 * math.sin(math.radians(45 + 90 * k))))
    nprof = cq.Workplane('XZ').polyline([(18, 90), (28, 90), (28, 120), (40, 120), (40, 127), (18, 127)]).close()
    n1 = nprof.revolve(360, (0, 0, 0), (0, 1, 0))
    nut = n1.cut(xcyl(4, 23.5, 29, 0, 110))
    sprof = cq.Workplane('XZ').polyline([(0, 70), (18, 70), (18, 175), (30, 175), (30, 215), (12, 215), (12, 225), (0, 225)]).close()
    s1 = sprof.revolve(360, (0, 0, 0), (0, 1, 0))
    s2 = s1.cut(xcyl(8, -40, 40, 0, 195)).cut(ycyl(8, -40, 40, 0, 195))
    s3 = s2.cut(zcyl(4, 205, 226)).faces('<Z').chamfer(2)
    cprof = cq.Workplane('XZ').polyline([(12.2, 215), (35, 215), (35, 240), (10, 240), (10, 230), (4.5, 230), (4.5, 225), (12.2, 225)]).close()
    c1 = cprof.revolve(360, (0, 0, 0), (0, 1, 0))
    cup = c1.faces('>Z').edges(cq.selectors.RadiusNthSelector(-1)).chamfer(1.5)
    for a in (0, 45, 90, 135):
        g = _box(-40, 40, -1.5, 1.5, 238, 241).rotate((0, 0, 0), (0, 0, 1), a)
        cup = cup.cut(g)
    wsh = zring(4.3, 9, 230, 232)
    scr = cap_screw(8, 25, 13, 8, (0, 0, 232), (0, 0, -1))
    bar = xcyl(7, -125, 125, 0, 195).faces('<X or >X').chamfer(1)
    setscr = xcyl(4, 23.5, 35, 0, 110).cut(orient(hex_prism(4, 3), '-x').translate((35, 0, 110)))
    ballk = sphere(12, (132, 0, 195)).cut(xcyl(7, 119, 125, 0, 195))
    parts = [
        P('body', 'body', 'EN-GJL-250 grey cast iron', 'Body', IRON, [
            F('revolve the body', REVOLVE, ['Sketch the half section on the XY Plane: base 120 diameter x 15, tapering to 64 at 100 high, '
                                            'a 70 x 20 boss on top; inside, a 56 bore 30 deep for the nut and a 38 bore below. Revolve 360.'], b1),
            F('set screw hole', HOLE, ['Hole on the side of the boss, 10 below the top: Tapped M8x1.25, into the nut bore.'], b2),
            F('holding down holes', CIRC, ['Hole diameter 10 in the base at 52 from the centre. Circular Pattern: 4.'], b3),
        ]),
        P('nut', 'bronze bush', 'CuSn12 phosphor bronze', 'Body', BRONZE, [
            F('flanged nut', REVOLVE, ['Revolve the section: 56 diameter x 30, an 80 x 7 flange, a 36 bore.'], n1),
            F('thread and lock hole', THREAD, ['Thread: square thread 36 x 6 (Inventor: add a custom thread or model it with Coil).',
                                               'Hole for the set screw, matching the body hole.'], nut,
              note='Bronze is used for the nut because it runs well against a steel screw and wears out first, so the nut, not the screw, is replaced.'),
        ]),
        P('spindle', 'screw spindle', '080M40 steel', 'Screw', STEEL, [
            F('revolve the spindle', REVOLVE, ['Revolve the half section: thread 36 diameter x 105, head 60 x 40, spigot 24 x 10.'], s1),
            F('tommy bar holes', HOLE, ['Two holes diameter 16 through the head, at right angles, 20 below its top.'], s2),
            F('tapped hole and chamfer', HOLE, ['Hole on the spigot: Tapped M8x1.25, 20 deep. Chamfer the bottom end 2 mm.',
                                                'Thread: square 36 x 6 on the 36 mm diameter.'], s3),
        ]),
        P('cup', 'load cup', 'C45 steel', 'Screw', ORANGE, [
            F('revolve the cup', REVOLVE, ['Revolve the half section: 70 diameter x 25, a 24.4 bore for the spigot and a 20 recess for the screw head.'], c1),
            F('grooves and chamfer', EXTRUDE, ['Sketch four 3 mm grooves across the top and Extrude Cut 2 deep. Chamfer the top edge 1.5.'], cup,
              note='The cup is free to turn on the spigot, so the load stays still while the screw turns under it.'),
        ]),
        P('washer', 'washer M8', 'Steel', 'Bought in', STEEL, [F('washer', CONTENT, [], wsh)], bought=True),
        P('cup_screw', 'cap screw M8 x 25', 'Steel, grade 8.8', 'Bought in', DARK, [F('screw', CONTENT, [], scr)], bought=True),
        P('set_screw', 'set screw M8 x 12', 'Steel, 45H', 'Bought in', DARK, [F('screw', CONTENT, [], setscr)], bought=True),
        P('tommy_bar', 'tommy bar', 'S275 steel', 'Screw', STEEL,
          [F('bar', EXTRUDE, ['Sketch a 14 circle, Extrude 250 Symmetric. Chamfer the ends 1 mm.'], bar)]),
        P('bar_ball', 'bar end ball', 'S275 steel', 'Screw', DARK,
          [F('ball', REVOLVE, ['Revolve a 24 mm ball and cut a 14 hole 15 deep for the bar.'], ballk)],
          instances=[('bar end ball 1', None), ('bar end ball 2', R((0, 0, 0), (0, 0, 1), 180))]),
    ]
    asm = [
        ('place the body', PLACE, ['Place body.ipt Grounded at Origin.'], ['body']),
        ('press in the bronze bush', CONSTRAIN, ['Place nut.ipt (the bronze bush the screw runs in). Insert its flange onto the top of the body. Line up the set screw holes.'], ['bronze bush']),
        ('lock the nut', CONTENT, ['Place from Content Center: ISO 4026 M8 x 12 set screw. Insert into the boss hole.'], ['set screw M8 x 12']),
        ('screw in the spindle', CONSTRAIN, ['Place screw_spindle.ipt. Mate its axis to the nut axis; Mate the head 50 above the nut flange.'],
         ['screw spindle']),
        ('cup, washer and screw', CONTENT, ['Place load_cup.ipt on the spigot (Insert). Place an M8 washer and an ISO 4762 M8 x 25 cap screw.'],
         ['load cup', 'washer M8', 'cap screw M8 x 25']),
        ('tommy bar', CONSTRAIN, ['Place tommy_bar.ipt in one of the head holes and Mate its middle to the axis. Insert a ball on each end.'],
         ['tommy bar', 'bar end ball 1', 'bar end ball 2'], 'One turn of the bar lifts the load by one pitch: 6 mm.'),
    ]
    ex = {'bronze bush': (0, 0, 60), 'set screw M8 x 12': (60, 0, 0), 'screw spindle': (0, 0, 120), 'load cup': (0, 0, 190),
          'washer M8': (0, 0, 230), 'cap screw M8 x 25': (0, 0, 270), 'tommy bar': (0, -90, 120), 'bar end ball 1': (60, -90, 120),
          'bar end ball 2': (-60, -90, 120)}
    return dict(name='screw_jack', title='Screw jack', parts=parts, assembly=asm, explode=ex,
                description='The classic screw jack: a cast iron body, a bronze nut locked by a set screw, a 36 x 6 square thread spindle '
                            'turned by a tommy bar, and a load cup that stays still while the screw turns. 10 parts.',
                uses='The standard assembly drawing exercise: half and full sections, threads, a turned part and a casting, parts list.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.3, 0.8))


# ================================================================== 7 flanged shaft coupling
@functools.lru_cache(None)
def flange_coupling():
    RF, TF, RH, LH = 80, 20, 40, 60      # flange radius and thickness, hub radius and length
    RS, PCD, NB = 20, 60, 6              # shaft radius, bolt circle radius, bolts
    RIM = (72, 16)                       # protecting rim inside radius and length past the flange
    SPIG = (30, 3)                       # spigot radius and depth

    def flange(sign):
        """sign -1: the left flange (A, with the spigot), +1: the right flange (B, with the recess)."""
        x0 = 0 if sign > 0 else -TF
        f1 = xcyl(RF, x0, x0 + TF).union(xcyl(RH, *sorted((sign * TF, sign * (TF + LH)))))
        rim = xcyl(RF, *sorted((sign * TF, sign * (TF + RIM[1])))).cut(xcyl(RIM[0], -200, 200))
        f2 = f1.union(rim)
        if sign < 0:
            f3 = f2.union(xcyl(SPIG[0], 0, SPIG[1]))
        else:
            f3 = f2.cut(xcyl(SPIG[0] + 0.05, -1, SPIG[1]))
        f4 = f3.cut(xcyl(RS, -200, 200))
        f5 = f4.cut(_box(-TF - LH - 1, SPIG[1] + 1, -6, 6, RS - 1, RS + 3.3) if sign < 0 else _box(-1, TF + LH + 1, -6, 6, RS - 1, RS + 3.3))
        f6 = f5
        for k in range(NB):
            a = math.radians(30 + 60 * k)
            f6 = f6.cut(xcyl(6.5, -TF - 1, TF + 1, PCD * math.cos(a), PCD * math.sin(a)))
        return [f1, f2, f3, f4, f5, f6]
    fa, fb = flange(-1), flange(1)
    sh0 = xcyl(RS, -200, -1)
    sh = sh0.cut(_box(-TF - LH + 5, -TF - 5, -6, 6, RS - 5, RS + 1)).faces('<X').chamfer(1.5)
    key = _box(-TF - LH + 5, -TF - 5, -6, 6, RS - 5, RS + 3).edges('|Z').fillet(5.9)
    bolt0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(6, 55, cq.Vector(-TF, 0, 0), cq.Vector(1, 0, 0)))
    bolt0 = bolt0.union(orient(hex_prism(18, 8), '-x').translate((-TF, 0, 0))).faces('>X').chamfer(1)
    wsh = orient(cq.Workplane('XY').circle(12).circle(6.5).extrude(2.5), 'x').translate((TF, 0, 0))
    nut0 = orient(hex_prism(18, 10).cut(cq.Workplane('XY').circle(6).extrude(10)), 'x').translate((TF + 2.5, 0, 0))

    def at_bolt(k):
        a = math.radians(30 + 60 * k)
        return T(0, PCD * math.cos(a), PCD * math.sin(a))
    mx = R((0, 0, 0), (0, 0, 1), 180)
    parts = [
        P('flange_a', 'flange A (spigot)', 'C45 steel, forged', 'Flanges', BLUE, [
            F('flange and hub', EXTRUDE, ['Sketch a 160 circle on the YZ Plane, Extrude 20. Sketch an 80 circle on its back, Extrude 60.'], fa[0]),
            F('protecting rim', EXTRUDE, ['Sketch circles 144 and 160 on the back of the flange. Extrude 16 mm, Join.'], fa[1],
              note='The rim covers the bolt heads, so nothing can catch on them while the shaft turns. That makes it a protected type coupling.'),
            F('spigot', EXTRUDE, ['Sketch a 60 circle on the front face, Extrude 3 mm. It fits a recess in the other flange and lines the two up.'], fa[2]),
            F('bore', HOLE, ['Hole on the centre: diameter 40 (H7), Through All.'], fa[3]),
            F('keyway', EXTRUDE, ['Sketch a 12 wide keyway on the bore. Extrude Cut 3.3 deep, Through All.'], fa[4]),
            F('bolt holes', CIRC, ['Hole diameter 13 on a 120 pitch circle. Circular Pattern: 6.'], fa[5]),
        ]),
        P('flange_b', 'flange B (recess)', 'C45 steel, forged', 'Flanges', GREEN, [
            F('flange and hub', EXTRUDE, ['As flange A: 160 x 20 flange and 80 x 60 hub.'], fb[0]),
            F('protecting rim', EXTRUDE, ['Rim 144 to 160 diameter, 16 long.'], fb[1]),
            F('recess', HOLE, ['Hole on the front face: diameter 60.1, 3 deep (the spigot fits in it).'], fb[2]),
            F('bore and keyway', HOLE, ['Hole 40 (H7) Through All. Keyway 12 wide, 3.3 deep.'], fb[4]),
            F('bolt holes', CIRC, ['Hole 13 on a 120 pitch circle. Circular Pattern: 6.'], fb[5]),
        ]),
        P('shaft', 'shaft 40', '080M40 steel', 'Shafts', STEEL, [
            F('shaft', EXTRUDE, ['Sketch a 40 circle, Extrude 199 mm.'], sh0),
            F('keyway and chamfer', EXTRUDE, ['Sketch a 12 x 50 keyway (round ends) on the top. Extrude Cut 5 deep. Chamfer the end 1.5.'], sh),
        ], instances=[('shaft A', None), ('shaft B', mx)]),
        P('key', 'key 12 x 8 x 50', 'Bright steel', 'Shafts', DARK,
          [F('key', EXTRUDE, ['Sketch a 12 x 50 round ended key. Extrude 8 mm.'], key)], instances=[('key A', None), ('key B', mx)]),
        P('bolt', 'hex bolt ISO 4014 M12 x 55', 'Steel, grade 8.8', 'Bought in', DARK, [F('bolt', CONTENT, [], bolt0)],
          instances=[('bolt %d' % (k + 1), at_bolt(k)) for k in range(NB)], bought=True),
        P('washer', 'washer M12', 'Steel', 'Bought in', STEEL, [F('washer', CONTENT, [], wsh)],
          instances=[('washer %d' % (k + 1), at_bolt(k)) for k in range(NB)], bought=True),
        P('nut', 'hex nut M12', 'Steel, grade 8', 'Bought in', DARK, [F('nut', CONTENT, [], nut0)],
          instances=[('nut %d' % (k + 1), at_bolt(k)) for k in range(NB)], bought=True),
    ]
    asm = [
        ('shaft A, key and flange A', PLACE, ['Place shaft_40.ipt Grounded. Place key.ipt and Insert it in the keyway.',
                                              'Place flange_A.ipt: Mate its bore to the shaft and its keyway to the key.'],
         ['shaft A', 'key A', 'flange A (spigot)']),
        ('shaft B, key and flange B', CONSTRAIN, ['Do the same with the second shaft, key and flange_B.ipt.',
                                                  'Constrain > Insert: the spigot of flange A into the recess of flange B.',
                                                  'Mate a bolt hole of A to a bolt hole of B, so the holes line up.'],
         ['shaft B', 'key B', 'flange B (recess)']),
        ('bolts, washers and nuts', CONTENT,
         ['Place from Content Center: ISO 4014 M12 x 55 bolt, ISO 7089 washer and ISO 4032 nut. Insert one set in a hole.',
          'Pattern Component: follow the flange hole pattern to place the other five.'],
         ['bolt %d' % (k + 1) for k in range(NB)] + ['washer %d' % (k + 1) for k in range(NB)] + ['nut %d' % (k + 1) for k in range(NB)],
         'The torque passes from shaft A through key A to flange A, through the six bolts (in shear) to flange B, and through key B to shaft B.'),
    ]
    ex = {'shaft A': (-130, 0, 0), 'key A': (-130, 0, 40), 'flange A (spigot)': (-60, 0, 0), 'shaft B': (130, 0, 0),
          'key B': (130, 0, 40), 'flange B (recess)': (60, 0, 0)}
    ex.update({'bolt %d' % (k + 1): (-150, 0, 0) for k in range(NB)})
    ex.update({'washer %d' % (k + 1): (120, 0, 0) for k in range(NB)})
    ex.update({'nut %d' % (k + 1): (150, 0, 0) for k in range(NB)})
    return dict(name='flange_coupling', title='Flanged shaft coupling', parts=parts, assembly=asm, explode=ex,
                description='A protected type flanged coupling joining two 40 mm shafts: two forged flanges with a spigot and recess to line '
                            'them up, keys, and six M12 bolts on a 120 mm pitch circle, hidden inside rims. 24 parts.',
                uses='Keys and keyways, spigot and recess location, bolts on a pitch circle, half sections of a turned assembly.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.3, 0.8))


# ================================================================== 8 knuckle joint
@functools.lru_cache(None)
def knuckle_joint():
    D = 25                                   # rod diameter: every other size is in proportion to it
    RE, TE, TF = D, 31, 19                   # eye radius, eye thickness, fork prong thickness
    GAP = TE / 2 + 0.5                       # half gap between the prongs
    # eye end
    e1 = zcyl(RE, -TE / 2, TE / 2).union(_box(0, 45, -15, 15, -TE / 2, TE / 2)).union(xcyl(20, 40, 90))
    e2 = e1.cut(zcyl(D / 2, -20, 20))
    e3 = e2.cut(xcyl(12, 50, 91)).edges(cq.selectors.BoxSelector((89, -25, -25), (91, 25, 25))).chamfer(1.5)
    # fork end
    pr = None
    for s in (1, -1):
        z0, z1 = sorted((s * GAP, s * (GAP + TF)))
        p = zcyl(RE, z0, z1).union(_box(-50, 0, -RE, RE, z0, z1))
        pr = p if pr is None else pr.union(p)
    f1 = pr.union(_box(-75, -45, -RE, RE, -GAP - TF, GAP + TF)).union(xcyl(20, -125, -70))
    f2 = f1.cut(zcyl(D / 2, -50, 50))
    f3 = f2.cut(xcyl(12, -126, -85)).edges(cq.selectors.BoxSelector((-126, -25, -25), (-124, 25, 25))).chamfer(1.5)
    # pin, collar, taper pin
    zb = -GAP - TF                           # underside of the lower prong
    p1 = zcyl(D / 2, zb - 13, GAP + TF).union(zcyl(20, GAP + TF, GAP + TF + 8))
    p2 = p1.cut(xcyl(3, -15, 15, 0, zb - 5)).faces('<Z').chamfer(1.5)
    col = zring(D / 2, 19, zb - 10, zb).cut(xcyl(3, -20, 20, 0, zb - 5)).faces('<Z').edges().chamfer(0.5)
    tp = cq.Workplane('XY').add(cq.Solid.makeCone(3, 2.6, 44, cq.Vector(-22, 0, zb - 5), cq.Vector(1, 0, 0)))
    rod = xcyl(12, 52, 280).faces('>X').chamfer(1.5)
    lock = orient(hex_prism(36, 19).cut(cq.Workplane('XY').circle(12).extrude(19)), 'x').translate((90, 0, 0)).edges('not |X').chamfer(1)
    mx = R((0, 0, 0), (0, 0, 1), 180)
    mrod = chain(mx, T(-125 + 90, 0, 0))     # the second rod and nut, at the fork end
    parts = [
        P('eye_end', 'eye end', '080M40 steel, forged', 'Knuckle', BLUE, [
            F('eye, neck and boss', EXTRUDE, ['Sketch a 50 circle on the XZ Plane, Extrude 31 Symmetric. Add the 45 x 30 neck and Revolve the 40 boss.'], e1),
            F('pin hole', HOLE, ['Hole on the eye centre: diameter 25 (H9), Through All.'], e2),
            F('tapped hole for the tie rod', HOLE, ['Hole on the end of the boss: Tapped M24x3, 40 deep. Chamfer the end 1.5.'], e3),
        ]),
        P('fork_end', 'fork end', '080M40 steel, forged', 'Knuckle', GREEN, [
            F('prongs, block and boss', EXTRUDE, ['Sketch the prong outline (50 wide, round end) on the XZ Plane. Extrude 19, 16 from the middle; Mirror. '
                                                  'Add the 30 x 50 x 70 block and Revolve the 40 boss.'], f1),
            F('pin hole', HOLE, ['Hole through both prongs: diameter 25 (H9), Through All.'], f2),
            F('tapped hole', HOLE, ['Tapped M24x3, 40 deep in the end of the boss. Chamfer 1.5.'], f3),
        ]),
        P('pin', 'knuckle pin', '080M40 steel, hardened', 'Knuckle', ORANGE, [
            F('head and shank', REVOLVE, ['Revolve: 25 diameter shank 82 long, 40 x 8 head.'], p1),
            F('taper pin hole and chamfer', HOLE, ['Hole diameter 6 across the shank, 5 above the end of the collar. Chamfer the end 1.5.'], p2),
        ]),
        P('collar', 'collar', 'S275 steel', 'Knuckle', STEEL, [
            F('collar', REVOLVE, ['Revolve: 38 outside, 25 bore, 10 long. Hole diameter 6 across. Chamfer 0.5.'], col)]),
        P('taper_pin', 'taper pin 6 x 44', 'Steel', 'Bought in', DARK, [F('taper pin', CONTENT, [], tp)], bought=True),
        P('tie_rod', 'tie rod M24', 'S355 steel', 'Tie rods', STEEL, [F('rod', EXTRUDE, ['Sketch a 24 circle, Extrude 228. Chamfer. Thread M24x3, 60 long.'], rod)],
          instances=[('tie rod 1', None), ('tie rod 2', mrod)]),
        P('lock_nut', 'lock nut M24', 'Steel, grade 8', 'Bought in', DARK, [F('nut', CONTENT, [], lock)],
          instances=[('lock nut 1', None), ('lock nut 2', mrod)], bought=True),
    ]
    asm = [
        ('fork end', PLACE, ['Place fork_end.ipt Grounded at Origin.'], ['fork end']),
        ('eye end between the prongs', CONSTRAIN, ['Place eye_end.ipt. Mate the eye hole axis to the fork hole axis and its middle plane to the fork middle.'],
         ['eye end']),
        ('pin, collar and taper pin', CONSTRAIN, ['Place knuckle_pin.ipt with Insert into the top prong. Place the collar under the lower prong.',
                                                  'Place a taper pin from Content Center (ISO 2339, 6 x 44) through the collar and pin.'],
         ['knuckle pin', 'collar', 'taper pin 6 x 44'], 'The taper pin holds the collar on, so the pin cannot come out.'),
        ('tie rods and lock nuts', CONTENT, ['Place tie_rod.ipt in each tapped hole and an M24 lock nut on each, tight against the boss.'],
         ['tie rod 1', 'tie rod 2', 'lock nut 1', 'lock nut 2']),
    ]
    ex = {'eye end': (40, 0, 0), 'knuckle pin': (0, 0, 90), 'collar': (0, 0, -70), 'taper pin 6 x 44': (0, 0, -100),
          'tie rod 1': (160, 0, 0), 'lock nut 1': (90, 0, 0), 'tie rod 2': (-160, 0, 0), 'lock nut 2': (-90, 0, 0)}
    return dict(name='knuckle_joint', title='Knuckle joint', parts=parts, assembly=asm, explode=ex,
                description='The classic knuckle joint joining two 24 mm tie rods: a forged eye end and fork end, a knuckle pin held by a collar '
                            'and taper pin, and lock nuts. Every size is in proportion to the 25 mm rod diameter. 9 parts.',
                uses='A standard drawing exercise: proportions from one diameter, a pin joint, sections with standard parts unhatched.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.3, 0.9))


# ================================================================== 9 piston and crank (single cylinder engine)
ENGINE = dict(R=25.0, L=100.0, BORE=25.0)


def engine_pose(theta):
    """Crank turned theta degrees (about +Y): crank pin offset (x, z), piston rise and the rod angle (degrees about +Y)."""
    r, L = ENGINE['R'], ENGINE['L']
    t = math.radians(theta)
    px, pz = r * math.sin(t), r * math.cos(t)
    zp = pz + math.sqrt(L * L - px * px)
    psi = math.degrees(math.asin(-px / L))
    return (px, pz), zp - (r + L), psi


@functools.lru_cache(None)
def piston_crank():
    r, L, B = ENGINE['R'], ENGINE['L'], ENGINE['BORE']
    ZG = r + L                                  # gudgeon pin height at top dead centre
    # crankshaft: main journals on Y, two webs, the crank pin at the top
    web = None
    for s in (1, -1):
        y0, y1 = sorted((s * 8, s * 18))
        w = _plate_xz([(0, -12, 30), (0, 0, 22), (0, r, 15)], y0, y1)
        web = w if web is None else web.union(w)
    cs1 = ycyl(12, -45, -8).union(ycyl(12, 8, 95)).union(web)
    cs2 = cs1.union(ycyl(10, -8, 8, 0, r))
    cs3 = cs2.cut(_box(-4, 4, 70, 92, 12 - 3.5, 13)).faces('>Y or <Y').chamfer(1)
    # crankcase frame: base, two bearing pedestals, deck on four pillars
    fr1 = _box(-70, 70, -60, 60, -70, -60)
    ped = None
    for s in (1, -1):
        y0, y1 = sorted((s * 25, s * 40))
        p = _box(-40, 40, y0, y1, -60, 15).union(ycyl(30, y0, y1))
        ped = p if ped is None else ped.union(p)
    fr2 = fr1.union(ped)
    pil = None
    for x in (55, -55):
        for y in (45, -45):
            c = zcyl(6, -60, 52, x, y)
            pil = c if pil is None else pil.union(c)
    fr3 = fr2.union(pil).union(_box(-65, 65, -55, 55, 52, 60))
    fr4 = fr3.cut(ycyl(16, -50, 50)).cut(zcyl(32, 50, 61))
    fr5 = fr4
    for x in (35, -35):
        for y in (35, -35):
            fr5 = fr5.cut(zcyl(4, 45, 61, x, y))
    bush = yring(12, 16, 25, 40)
    # cylinder barrel with fins and flanges, head
    ba1 = zring(B, 31, 60, 165).union(_box(-45, 45, -45, 45, 60, 68)).union(_box(-40, 40, -40, 40, 157, 165))
    ba2 = ba1
    for k in range(5):
        ba2 = ba2.union(zring(30, 44, 80 + 15 * k, 83 + 15 * k))
    ba3 = ba2.cut(zcyl(B, 59, 166))
    for x in (35, -35):
        for y in (35, -35):
            ba3 = ba3.cut(zcyl(4.5, 59, 69, x, y))
    for x in (30, -30):
        for y in (30, -30):
            ba3 = ba3.cut(zcyl(4, 152, 166, x, y))
    hd1 = _box(-40, 40, -40, 40, 165, 180).edges('|Z').fillet(4)
    hd2 = hd1.cut(zcyl(B, 164, 169))
    hd3 = hd2.cut(zcyl(7, 168, 181, 10, 0))
    for x in (30, -30):
        for y in (30, -30):
            hd3 = hd3.cut(zcyl(4.5, 164, 181, x, y))
    for k in range(4):
        hd3 = hd3.cut(_box(-41, 41, -1.5 + 0, 1.5, 172, 181).rotate((0, 0, 0), (0, 0, 1), 0).translate((0, -24 + 16 * k, 0)))
    # piston, rings, gudgeon pin, circlips
    zc = ZG
    pi1 = zcyl(B - 0.1, zc - 20, zc + 30)
    pi2 = pi1.cut(zcyl(21, zc - 21, zc + 24))
    boss = ycyl(8, -24.9, 24.9, 0, zc).intersect(zcyl(B - 0.1, zc - 20, zc + 30)).cut(_box(-30, 30, -9.5, 9.5, zc - 30, zc + 30))
    pi3 = pi2.union(boss).cut(ycyl(6, -30, 30, 0, zc)).cut(ycyl(6.8, 19, 20.2, 0, zc)).cut(ycyl(6.8, -20.2, -19, 0, zc))
    pi4 = pi3.cut(zring(22.4, 26, zc + 23, zc + 25)).cut(zring(22.4, 26, zc + 18, zc + 20))
    ring_ = zring(22.5, B, zc + 23.05, zc + 24.95).cut(_box(-1, 1, 20, 30, zc + 20, zc + 28))
    gp = ycyl(6, -19, 19, 0, zc).cut(ycyl(3.5, -20, 20, 0, zc))
    clip = yring(5, 6.7, 19.05, 20.15, 0, zc).cut(_box(-1.5, 1.5, 18, 21, zc + 4, zc + 8))
    # connecting rod and big end cap (split on the crank pin centre line)
    rd1 = ycyl(11, -8.5, 8.5, 0, zc).union(_box(-6, 6, -6, 6, r + 14, zc - 9))
    big_up = ycyl(18, -7.9, 7.9, 0, r).intersect(_box(-10, 10, -10, 10, r, r + 20)).union(_box(-22, 22, -7.9, 7.9, r, r + 10))
    rd2 = rd1.union(big_up)
    rd3 = rd2.cut(ycyl(6, -10, 10, 0, zc)).cut(ycyl(10, -10, 10, 0, r))
    for x in (16, -16):
        rd3 = rd3.cut(zcyl(3.2, r - 1, r + 11, x, 0))
    cap0 = ycyl(18, -7.9, 7.9, 0, r).intersect(_box(-10, 10, -10, 10, r - 20, r)).union(_box(-22, 22, -7.9, 7.9, r - 10, r))
    cap = cap0.cut(ycyl(10, -10, 10, 0, r))
    for x in (16, -16):
        cap = cap.cut(zcyl(3.2, r - 11, r + 1, x, 0))
    bb = zcyl(3, r - 10, r + 16, 16, 0).union(hex_prism(10, 4).translate((16, 0, r - 14))).faces('>Z').chamfer(0.5)
    bn = hex_nut(10, 5, 6, (16, 0, r + 10))
    mx = R((0, 0, 0), (0, 0, 1), 180)
    # flywheel, key, spark plug, head bolts
    fw1 = ycyl(70, 60, 75).union(ycyl(25, 52, 80))
    fw2 = fw1.cut(ycyl(12, 50, 90)).cut(_box(-4, 4, 50, 90, 10, 15.3))
    fw3 = fw2.cut(yring(30, 60, 66, 76))
    for k in range(5):
        a = math.radians(72 * k)
        fw3 = fw3.cut(ycyl(9, 59, 76, 45 * math.cos(a), 45 * math.sin(a)))
    fkey = _box(-4, 4, 70, 92, 12 - 3.5, 15.3).edges('|Y').fillet(0.5)
    plug = zcyl(7, 168, 180, 10, 0).union(hex_prism(21, 10).translate((10, 0, 180))).union(zcyl(8, 190, 210, 10, 0))
    plug = plug.union(zcyl(2.5, 210, 220, 10, 0))
    hb = cap_screw(8, 25, 13, 8, (30, 30, 180), (0, 0, -1))
    hb_inst = [('head screw %d' % (k + 1), T(dx, dy, 0)) for k, (dx, dy) in enumerate(((0, 0), (-60, 0), (0, -60), (-60, -60)))]
    rod_g = ['connecting rod', 'big end cap', 'big end bolt 1', 'big end bolt 2', 'big end nut 1', 'big end nut 2']
    parts = [
        P('crankcase', 'crankcase frame', 'EN AC-42100 aluminium casting', 'Frame', ALU, [
            F('base plate', EXTRUDE, ['Sketch a 140 x 120 rectangle on the XZ Plane. Extrude 10 mm.'], fr1),
            F('bearing pedestals', EXTRUDE, ['Sketch the pedestal (80 wide, a 60 round top) on the XY Plane. Extrude 15 mm, 25 out from the middle. Mirror.'], fr2),
            F('pillars and deck', EXTRUDE, ['Four 12 mm pillars at the corners up to 112 high, then a 130 x 110 x 8 deck on top.'], fr3),
            F('bearing bores and crank opening', HOLE, ['Hole diameter 32 through both pedestals for the bushes. Hole diameter 64 in the deck for the rod.'], fr4),
            F('tapped holes for the barrel', HOLE, ['Hole on the deck: Tapped M8, 4 off on a 70 x 70 square.'], fr5),
        ]),
        P('crankshaft', 'crankshaft', '817M40 steel, forged', 'Crank', ORANGE, [
            F('journals and webs', EXTRUDE, ['Revolve the two 24 mm main journals (37 and 87 long). Sketch the web (a 60 counterweight, the 44 hub and the 30 pin boss) and '
                                            'Extrude 10 mm, 8 out from the middle; Mirror.'], cs1),
            F('crank pin', EXTRUDE, ['Sketch a 20 circle on the web face, 25 above the axis (the throw: half the 50 mm stroke). Extrude between the webs.'], cs2),
            F('keyway and chamfers', EXTRUDE, ['Keyway 8 x 3.5 x 22 for the flywheel. Chamfer the ends 1 mm.'], cs3),
        ]),
        P('bush', 'main bearing bush', 'CuSn7Zn4Pb7 bronze', 'Crank', BRONZE, [F('bush', REVOLVE, ['Revolve: 24 bore, 32 outside, 15 long.'], bush)],
          instances=[('main bush 1', None), ('main bush 2', mx)]),
        P('barrel', 'cylinder barrel', 'EN AC-43000 aluminium, cast iron liner', 'Cylinder', ALU, [
            F('tube and flanges', EXTRUDE, ['Revolve the 62 tube, 105 long. Add a 90 x 90 x 8 base flange and an 80 x 80 x 8 top flange.'], ba1),
            F('cooling fins', RECT, ['Revolve one fin (88 diameter, 3 thick). Rectangular Pattern: 5, 15 apart up the barrel.'], ba2),
            F('bore and holes', HOLE, ['Hole: the 50 bore (H7), Through All. 4 clearance holes in the base flange, 4 Tapped M8 in the top.'], ba3),
        ]),
        P('head', 'cylinder head', 'EN AC-43000 aluminium', 'Cylinder', ALU, [
            F('block', EXTRUDE, ['Sketch an 80 x 80 square, Extrude 15. Fillet the corners 4.'], hd1),
            F('combustion chamber', HOLE, ['Hole on the underside: diameter 50, 4 deep.'], hd2),
            F('spark plug, screw holes and fins', HOLE, ['Tapped Hole M14x1.25 for the spark plug, 10 off centre. Four clearance holes 9.',
                                                         'Extrude Cut four 3 mm slots across the top (cooling fins).'], hd3),
        ]),
        P('head_screw', 'cap screw M8 x 25', 'Steel, grade 12.9', 'Bought in', DARK, [F('screw', CONTENT, [], hb)], instances=hb_inst, bought=True),
        P('piston', 'piston', 'EN AC-48000 aluminium', 'Piston and rod', STEEL, [
            F('blank', EXTRUDE, ['Sketch a 49.8 circle, Extrude 50.'], pi1),
            F('hollow it', HOLE, ['Hole from the bottom: diameter 42, 45 deep (a 6 mm crown, a 3.9 mm skirt).'], pi2),
            F('pin bosses and pin hole', EXTRUDE, ['Extrude the two 16 mm pin bosses across the inside. Hole diameter 12 through them. '
                                                   'Revolve Cut the circlip grooves.'], pi3),
            F('ring grooves', REVOLVE, ['Revolve Cut two grooves, 2 wide and 2.5 deep, 5 and 10 below the crown.'], pi4),
        ]),
        P('ring', 'piston ring', 'Cast iron', 'Piston and rod', DARK, [F('ring', EXTRUDE, ['Sketch circles 45 and 50 with a 2 mm gap. Extrude 1.9.'], ring_)],
          instances=[('piston ring 1', None), ('piston ring 2', T(0, 0, -5))]),
        P('gudgeon_pin', 'gudgeon pin', 'Steel, case hardened', 'Piston and rod', STEEL, [F('pin', EXTRUDE, ['Sketch circles 12 and 7, Extrude 38 Symmetric.'], gp)]),
        P('circlip', 'circlip', 'Spring steel', 'Piston and rod', DARK, [F('clip', EXTRUDE, ['Sketch circles 10 and 13.4 with a 3 mm gap. Extrude 1.1.'], clip)],
          instances=[('circlip 1', None), ('circlip 2', lambda w: w.mirror('XZ'))]),
        P('con_rod', 'connecting rod', 'C45 steel, forged', 'Piston and rod', BLUE, [
            F('small end and shank', EXTRUDE, ['Sketch the 22 small end eye and a 12 x 12 shank on the XY Plane, centres 100 apart. Extrude.'], rd1),
            F('big end (top half)', EXTRUDE, ['Sketch the top half of the 36 big end and the 44 wide bolt bosses. Extrude 15.8 Symmetric.'], rd2),
            F('bores and bolt holes', HOLE, ['Hole 12 at the small end, 20 at the big end, and two 6.4 bolt holes 32 apart.'], rd3,
              note='In the factory the rod and cap are made as one forging, bored together and then split, so they must go back together the same way.'),
        ]),
        P('cap', 'big end cap', 'C45 steel, forged', 'Piston and rod', BLUE, [
            F('cap', EXTRUDE, ['Sketch the bottom half of the big end, 44 wide. Extrude 15.8 Symmetric. Holes 20 and two 6.4.'], cap)]),
        P('big_end_bolt', 'big end bolt M6 x 30', 'Steel, grade 10.9', 'Bought in', DARK, [F('bolt', CONTENT, [], bb)],
          instances=[('big end bolt 1', None), ('big end bolt 2', mx)], bought=True),
        P('big_end_nut', 'nut M6', 'Steel, grade 10', 'Bought in', DARK, [F('nut', CONTENT, [], bn)],
          instances=[('big end nut 1', None), ('big end nut 2', mx)], bought=True),
        P('flywheel', 'flywheel', 'EN-GJL-250 grey cast iron', 'Crank', IRON, [
            F('rim and hub', EXTRUDE, ['Sketch a 140 circle, Extrude 15. Add a 50 hub, 28 long.'], fw1),
            F('bore and keyway', HOLE, ['Hole 24 (H7) through the hub. Keyway 8 x 3.3.'], fw2),
            F('dished web and holes', CIRC, ['Revolve Cut a recess 60 to 120 diameter, 9 deep. Hole 18 at 45 radius, Circular Pattern 5.'], fw3,
              note='The heavy flywheel stores energy from the power stroke and carries the crank round the other three strokes.'),
        ]),
        P('key', 'key 8 x 7 x 22', 'Bright steel', 'Crank', DARK, [F('key', EXTRUDE, ['Sketch 8 x 22, Extrude 6.8.'], fkey)]),
        P('spark_plug', 'spark plug M14', 'Bought in', 'Bought in', BLACK, [F('plug', CONTENT, [], plug)], bought=True),
    ]
    piston_g = ['piston', 'piston ring 1', 'piston ring 2', 'gudgeon pin', 'circlip 1', 'circlip 2']
    asm = [
        ('crankcase and bushes', PLACE, ['Place crankcase_frame.ipt Grounded. Place two bushes and Insert them in the pedestal bores.'],
         ['crankcase frame', 'main bush 1', 'main bush 2']),
        ('crankshaft, key and flywheel', CONSTRAIN, ['Place crankshaft.ipt: Mate its axis to the bush axis and Flush its middle with the frame.',
                                                     'Place the key and flywheel.ipt on the long end.'], ['crankshaft', 'key 8 x 7 x 22', 'flywheel']),
        ('piston sub-assembly', CONSTRAIN, ['Place piston.ipt, two rings, the gudgeon pin (Insert through the bosses) and two circlips.'], piston_g),
        ('connecting rod', CONSTRAIN, ['Place connecting_rod.ipt. Mate the small end to the gudgeon pin and the big end to the crank pin.',
                                       'Place the cap, the two bolts and two nuts.'], rod_g,
         'Now drag the flywheel: the crank turns, the rod rocks and the piston slides up and down.'),
        ('barrel, head and spark plug', CONTENT, ['Place cylinder_barrel.ipt: Mate its bore to the piston and its flange to the deck.',
                                                  'Place cylinder_head.ipt, four ISO 4762 M8 x 25 screws and the spark plug.'],
         ['cylinder barrel', 'cylinder head'] + [n for n, tf in hb_inst] + ['spark plug M14']),
    ]
    ex = {'cylinder head': (0, 0, 150), 'spark plug M14': (0, 0, 200), 'cylinder barrel': (0, 0, 90), 'flywheel': (0, 90, 0),
          'key 8 x 7 x 22': (0, 60, 20), 'main bush 1': (0, 40, 0), 'main bush 2': (0, -40, 0)}
    ex.update({n: (0, 0, 190) for n, tf in hb_inst})
    ex.update({n: (-120, 0, 40) for n in piston_g})
    ex.update({'piston ring 1': (-120, 0, 75), 'piston ring 2': (-120, 0, 60), 'circlip 1': (-120, 45, 40), 'circlip 2': (-120, -45, 40),
               'gudgeon pin': (-120, 70, 40), 'big end cap': (0, 0, -40),
               'big end bolt 1': (0, 0, -70), 'big end bolt 2': (0, 0, -70), 'big end nut 1': (0, 0, 30), 'big end nut 2': (0, 0, 30)})
    return dict(name='piston_crank', title='Piston and crank (single cylinder engine)', parts=parts, assembly=asm, explode=ex,
                description='The slider-crank at the heart of an engine: a crankshaft with a 25 mm throw in bronze bushes, a split connecting '
                            'rod 100 mm between centres, a 50 mm piston with two rings, gudgeon pin and circlips, a finned barrel, head, '
                            'spark plug and flywheel. 25 parts.',
                uses='Turning motion into straight line motion, split big end with bolts, sections through a piston and barrel, parts list.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.3, 0.8))


FOLDER = 'GrabCAD models'
BUILDERS = [plummer_block, spur_gearbox, universal_joint, toggle_clamp, swivel_castor, screw_jack, flange_coupling, knuckle_joint, piston_crank]


def _fn(b):
    def fn():
        return model_items(b())
    fn.__doc__ = b().get('description')
    return fn


# what the catalogue needs without building the model (building every model on import would be slow)
META = dict(
    plummer_block=dict(title='Plummer block bearing', fn=plummer_block),
    spur_gearbox=dict(title='Spur gearbox', fn=spur_gearbox),
    universal_joint=dict(title='Universal joint', fn=universal_joint),
    toggle_clamp=dict(title='Toggle clamp', fn=toggle_clamp),
    swivel_castor=dict(title='Swivel castor', fn=swivel_castor),
    screw_jack=dict(title='Screw jack', fn=screw_jack),
    flange_coupling=dict(title='Flanged shaft coupling', fn=flange_coupling),
    knuckle_joint=dict(title='Knuckle joint', fn=knuckle_joint),
    piston_crank=dict(title='Piston and crank (single cylinder engine)', fn=piston_crank),
)
SUMMARY = {}   # filled from each builder's description, criteria, uses, section and iso, in the same order as BUILDERS


class _Lazy(dict):
    """A MODELS entry whose explode positions, description and so on come from the builder when first asked for."""
    LAZY = ('description', 'criteria', 'uses', 'section', 'explode', 'iso')

    def __init__(self, name, b):
        super().__init__(name=name, title=META[name]['title'], folder=FOLDER, fn=_fn(b),
                         bom=(lambda: model_bom(b())))
        self._b = b

    def _fill(self, k):
        if k in self.LAZY and not dict.__contains__(self, k):
            m = self._b()
            for kk in self.LAZY:
                dict.__setitem__(self, kk, m[kk])

    def __getitem__(self, k):
        self._fill(k)
        return dict.__getitem__(self, k)

    def get(self, k, d=None):
        self._fill(k)
        return dict.get(self, k, d)


def _fn(b):
    def fn():
        return model_items(b())
    return fn


MODELS = [_Lazy(n, v['fn']) for n, v in META.items()]
STEPS = {n: (lambda b=v['fn']: model_steps(b())) for n, v in META.items()}
