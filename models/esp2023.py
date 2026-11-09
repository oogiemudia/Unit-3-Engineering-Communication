"""ESP 2023: replacement lock gates for Canal Heritage (T Level Employer-Set Project 8730-035, Summer 2023, Task 2).

The brief: a gate system for each end of five 200 year old locks. Each gate fits an opening 4.2 m wide, has an
overall height of 6 m and holds a head of water between 2 m and 5.5 m. The gates open and close automatically and
independently, the drive sits out of sight in an inspection chamber beside each gate, and the gates must be easy
to lift out by mobile crane, durable at the hinges, sealed, protected against boat strikes, watched by cameras and
fitted with an emergency call point.

Design A (preferred): a pair of steel mitre gates. Design B (concept only): a single vertical lift gate.

Coordinates (mm): the lock centre line is the Y axis, upstream (the full chamber side) is +Y, the cill is z = 0
and the lock walls are at x = -2100 and x = +2100 (the 4.2 m opening). When the gates are shut the two leaves meet
on the centre line at a mitre, pointing upstream at 1 in 3 (18.4 degrees), so the water pressure pushes the mitre
posts together and seals the gap.

Every model here is plain CadQuery, generated from the numbers below, like the rest of the Unit 3 CAD hub.
"""
import math
import cadquery as cq

# ------------------------------------------------------------------ the numbers that define the design
OPENING = 4200            # clear width between the lock walls
HEIGHT = 6000             # overall height of a gate leaf, cill to walkway
HEAD_MAX = 5500           # greatest head of water the gates hold
HEAD_MIN = 2000
THETA = math.atan(1 / 3)  # mitre angle: 1 in 3, 18.43 degrees
C, S = math.cos(THETA), math.sin(THETA)
LEAF = 2460               # leaf length, heel pivot to mitre face (measured along the leaf centre line)
GAP = 15                  # half the gap at the mitre, filled by the 30 mm mitre seal
PIV = GAP + LEAF * C      # x of each heel pivot (hollow quoin centre), 2348.8
T2 = 225                  # half the leaf thickness (leaf is 450 thick)
SKIN = 12                 # skin plate on the upstream (chamber) face
HEEL_R = 225              # heel post radius (it turns in a hollow quoin)
HEEL_BOX = 400            # heel post box section length along the leaf
MITRE_BOX = 300           # mitre post box section length
TOP = 5960                # top of the steel; the walkway grating sits on top up to HEIGHT
GIRDERS = [150, 800, 1450, 2150, 2900, 3750, 4700, 5860]   # girder levels, closer together at the bottom
WEB_T = 20                # girder web thickness
FLANGE = (200, 20)        # girder downstream flange: height, thickness
STIFFENERS = [(980, 995), (1565, 1580)]   # vertical stiffener plates along the leaf (u from, u to)
FENDERS = [2600, 3500, 4400]              # oak rubbing fender levels on the chamber face
OPEN_DEG = 90 - math.degrees(THETA)       # a leaf turns 71.6 degrees to lie in its recess
BRACKET_U = 1000          # actuator bracket position along the leaf
EYE_R = 45                # actuator rod eye (spherical bearing) radius
ACT_Z = 5800              # actuator centre height
W_OFF = (2400, 1400)      # actuator rear pivot, measured from the heel pivot (x outwards, y upstream)
CHAMBER = (300, 2650, 600, 2400)   # inspection chamber x from, x to (from the pivot), y from, y to

# colours
LEAF_C = '4F6D7A'         # painted steel (heritage grey-green)
WHITE = 'E6E6E6'
OAK = 'A0703C'
RUBBER = '2B2B2B'
STAINLESS = 'C9D3DD'
CONCRETE = 'B5B0A6'
ACT_C = '3FA37C'
DARK = '4A5562'
YELLOW = 'E8C23D'
ORANGE = 'E8A33D'


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def zcyl(r, z0, z1, x=0, y=0):
    return cq.Workplane('XY').workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def ucyl(r, u0, u1, v, z):
    """A round bar along the leaf (local X)."""
    return cq.Workplane('YZ').workplane(offset=u0).center(v, z).circle(r).extrude(u1 - u0)


def bar(p0, p1, r):
    """A round bar between two points (x, y, z)."""
    v = cq.Vector(*p1) - cq.Vector(*p0)
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r, v.Length, cq.Vector(*p0), v.normalized()))


def mitre_cut():
    """Everything beyond the mitre face, in leaf coordinates. The mitre face is the plane u = LEAF + v / 3,
    which becomes the plane x = -GAP once the leaf is placed in the lock."""
    pts = [(LEAF - 2000 / 3, -2000), (LEAF + 2000 / 3, 2000), (LEAF + 4000, 2000), (LEAF + 4000, -2000)]
    return cq.Workplane('XY').workplane(offset=-500).polyline(pts).close().extrude(9000)


# ------------------------------------------------------------------ the gate leaf, in its own coordinates
# u (X) runs along the leaf from the heel pivot to the mitre, v (Y) points to the chamber (upstream) face,
# z (Z) is up. The pivot is the Z axis.
def heel_post():
    hp = zcyl(HEEL_R, 50, 5850).union(box(0, HEEL_BOX, -T2, T2, 50, 5850))
    # fabricated from 25 mm plate: hollow above a solid bearing block at the bottom
    hp = hp.cut(zcyl(HEEL_R - 25, 350, 5825).union(box(0, HEEL_BOX - 25, -T2 + 25, T2 - 25, 350, 5825)))
    hp = hp.cut(zcyl(80, 50, 300))                         # bore for the bottom pintle
    return hp.union(zcyl(100, 5850, 6000))                 # top journal for the anchor collar


def leaf_frame_raw(stage=6):
    """The welded steel leaf before its mitre end is trimmed. stage limits it to the first members, for the
    build steps: heel post, mitre post, girders, stiffeners, skin plate, actuator bracket."""
    span = (HEEL_BOX, LEAF - MITRE_BOX)
    hp = heel_post()
    mp = box(LEAF - MITRE_BOX, LEAF + 400, -T2, T2, 50, TOP)
    mp = mp.cut(box(LEAF - MITRE_BOX + 25, LEAF - 90, -T2 + 25, T2 - 25, 75, TOP - 25))   # hollow box post
    skin = box(HEEL_BOX, LEAF + 400, T2 - SKIN, T2, 50, TOP)
    girders = None
    for z in GIRDERS:
        g = box(span[0], span[1], -T2 + FLANGE[1], T2 - SKIN, z - WEB_T / 2, z + WEB_T / 2)
        fz0, fz1 = max(50, z - FLANGE[0] / 2), min(TOP, z + FLANGE[0] / 2)
        g = g.union(box(span[0], span[1], -T2, -T2 + FLANGE[1], fz0, fz1))
        girders = g if girders is None else girders.union(g)
    stiff = None
    for u0, u1 in STIFFENERS:
        s = box(u0, u1, -T2 + FLANGE[1], T2 - SKIN, 50, TOP)
        stiff = s if stiff is None else stiff.union(s)
    bracket = box(BRACKET_U - 50, BRACKET_U + 50, T2, T2 + 125, 5700, 5900)
    order = [hp, mp, girders, stiff, skin, bracket][:stage]
    out = order[0]
    for o in order[1:]:
        out = out.union(o)
    return out


def leaf_frame():
    """The welded steel leaf: heel post, mitre post, eight girders, two stiffeners, skin plate and the actuator
    bracket, trimmed to the mitre."""
    return leaf_frame_raw().cut(mitre_cut())


def fenders():
    """FSC oak rubbing fenders on the chamber face: a boat touches timber, not the steel skin."""
    f = None
    for z in FENDERS:
        b = box(HEEL_BOX + 100, LEAF - MITRE_BOX - 50, T2, T2 + 150, z - 100, z + 100)
        b = b.edges('|X').fillet(20)
        f = b if f is None else f.union(b)
    return f


def walkway():
    """Galvanised grating walkway on top of the leaf with a handrail on the downstream edge."""
    w = box(HEEL_BOX, LEAF - MITRE_BOX, -T2, T2, TOP, HEIGHT)
    v, r = -T2 + 25, 24
    us = [HEEL_BOX + 100, (HEEL_BOX + LEAF - MITRE_BOX) / 2, LEAF - MITRE_BOX - 100]
    for u in us:
        w = w.union(cq.Workplane('XY').workplane(offset=HEIGHT).center(u, v).circle(r).extrude(1100))
    for z in (HEIGHT + 550, HEIGHT + 1100 - r):
        w = w.union(ucyl(r, us[0] - r, us[-1] + r, v, z))
    return w


def cill_seal():
    """Rubber cill seal along the bottom of the chamber face."""
    return box(HEEL_BOX, LEAF + 400, T2 - 85, T2, 0, 50).cut(mitre_cut())


def heel_seal():
    """Rubber heel seal down the back of the heel post, against the hollow quoin."""
    return box(-HEEL_R - 30, -HEEL_R, -40, 40, 50, 5850)


# ------------------------------------------------------------------ placing parts in the lock
def to_lock(wp, side, open_deg=0.0):
    """Leaf coordinates to lock coordinates. side = -1 is the left leaf, +1 the right (a mirror image)."""
    w = wp.rotate((0, 0, 0), (0, 0, 1), math.degrees(THETA) + open_deg).translate((-PIV, 0, 0))
    return w.mirror('YZ') if side > 0 else w


def lock_point(u, v, z, side, open_deg=0.0):
    a = THETA + math.radians(open_deg)
    x, y = -PIV + u * math.cos(a) - v * math.sin(a), u * math.sin(a) + v * math.cos(a)
    return (-x if side > 0 else x, y, z)


def actuator_geometry(side, open_deg):
    """Rear pivot W, rod eye centre G and the distance between them, in lock coordinates."""
    g = lock_point(BRACKET_U, T2 + 125 + EYE_R, ACT_Z, side, open_deg)
    wx = -(PIV + W_OFF[0]) if side < 0 else PIV + W_OFF[0]
    w = (wx, W_OFF[1], ACT_Z)
    return w, g, math.dist(w[:2], g[:2])


ACT_BODY = 1900           # actuator body length from the rear pivot
ACT_CAP = 50              # solid rear cap
ROD_LEN = 1600            # rod length, eye centre to rod end


def actuator(side, open_deg=0.0):
    """Electro-mechanical linear actuator: body (tube, rear cap, motor) and rod with a spherical eye."""
    w, g, d = actuator_geometry(side, open_deg)
    u = cq.Vector(g[0] - w[0], g[1] - w[1], 0).normalized()
    W = cq.Vector(*w)
    body = cq.Workplane('XY').add(cq.Solid.makeCylinder(70, ACT_BODY, W, u))
    body = body.cut(cq.Workplane('XY').add(cq.Solid.makeCylinder(40, ACT_BODY - ACT_CAP, W + u * ACT_CAP, u)))
    # motor and gearbox under the tube
    ang = math.degrees(math.atan2(u.y, u.x))
    motor = box(200, 650, -75, 75, -235, -85).rotate((0, 0, 0), (0, 0, 1), ang).translate(w)
    body = body.union(motor)
    G = cq.Vector(*g)
    rod = cq.Workplane('XY').add(cq.Solid.makeCylinder(35, ROD_LEN, G - u * ROD_LEN, u))
    rod = rod.union(cq.Workplane('XY').add(cq.Solid.makeSphere(EYE_R, G, angleDegrees1=-90, angleDegrees2=90)))
    return body, rod


def chamber(side):
    """Purpose built inspection chamber beside the gate (concrete, cover removed for clarity), with a plinth for
    the actuator pivot and a slot in the lock side wall for the actuator rod."""
    x0, x1, y0, y1 = PIV + CHAMBER[0], PIV + CHAMBER[1], CHAMBER[2], CHAMBER[3]
    t = 150
    c = box(x0, x1, y0, y1, 5000, HEIGHT).cut(box(x0 + t, x1 - t, y0 + t, y1 - t, 5000 + t, HEIGHT + 1))
    c = c.cut(box(x0 - 1, x0 + t + 1, 800, 2300, 5550, HEIGHT + 1))
    c = c.union(zcyl(150, 5000 + t, 5700, PIV + W_OFF[0], W_OFF[1]))
    return c.mirror('YZ') if side < 0 else c


def cctv(side):
    """Camera mast on the far corner of the chamber, looking down the gate, and an emergency call point."""
    x, y = PIV + CHAMBER[1] - 75, CHAMBER[3] - 75
    m = zcyl(60, HEIGHT, 9000, x, y)
    cam = box(-150, 150, -75, 75, -75, 75).rotate((0, 0, 0), (0, 0, 1), -125).translate((x - 120, y - 170, 8850))
    m = m.union(cam).union(box(x - 140, x - 60, y - 40, y + 40, 8800, 8920))
    cp = box(x - 75, x + 75, 600, 750, HEIGHT, 7200)
    cp = cp.union(box(x - 110, x + 110, 595 - 80, 600, 6900, 7150))
    if side < 0:
        m, cp = m.mirror('YZ'), cp.mirror('YZ')
    return m, cp


def pintle(side):
    """Stainless steel bottom pintle (the lower hinge): a 150 mm pin on a base plate set in the cill."""
    p = zcyl(75, 0, 280).union(box(-300, 300, -300, 300, -80, 0))
    p = p.edges(cq.selectors.BoxSelector((-80, -80, -1), (80, 80, 1))).fillet(15)    # root fillet
    p = p.edges(cq.selectors.BoxSelector((-80, -80, 279), (80, 80, 281))).fillet(10)  # rounded top
    return p.translate((side * PIV, 0, 0))


def anchor_collar(side):
    """Top hinge: a collar round the heel post journal, held back into the wall by an anchor strap."""
    c = zcyl(180, 5870, 5970).cut(zcyl(105, 5870, 5970))
    c = c.union(box(170, 900, -60, 60, 5870, 5970))
    c = c.translate((PIV, 0, 0))
    return c.mirror('YZ') if side < 0 else c


def _mitre_seal_local():
    """The mitre seal in leaf coordinates (left leaf), found by trimming in lock coordinates and moving back."""
    s = box(LEAF - 60, LEAF + 400, -40, 40, 50, TOP)
    s = to_lock(s, -1).intersect(box(-GAP, GAP, -3000, 3000, 0, 7000))
    return s.translate((PIV, 0, 0)).rotate((0, 0, 0), (0, 0, 1), -math.degrees(THETA))


def leaf_parts(side, open_deg=0.0):
    """Everything that turns with one leaf, as (name, shape, colour) in lock coordinates."""
    n = 'left' if side < 0 else 'right'
    items = [('%s gate leaf' % n, leaf_frame(), LEAF_C), ('%s oak fenders' % n, fenders(), OAK),
             ('%s walkway and handrail' % n, walkway(), WHITE), ('%s cill seal' % n, cill_seal(), RUBBER),
             ('%s heel seal' % n, heel_seal(), RUBBER)]
    if side < 0:
        items.append(('mitre seal', _mitre_seal_local(), RUBBER))
    return [(p, to_lock(w, side, open_deg), c) for p, w, c in items]


def fixed_parts(side):
    n = 'left' if side < 0 else 'right'
    m, cp = cctv(side)
    return [('%s bottom pintle' % n, pintle(side), STAINLESS), ('%s anchor collar' % n, anchor_collar(side), DARK),
            ('%s inspection chamber' % n, chamber(side), CONCRETE), ('%s CCTV mast' % n, m, ORANGE),
            ('%s call point' % n, cp, YELLOW)]


def lock_gates(open_deg=0.0):
    """Design A, the preferred design: a pair of steel mitre gates for a 4.2 m wide lock, 6 m high, holding up to
    5.5 m of water. Each leaf turns on a stainless pintle and an anchor collar, is driven by an electric actuator in
    an inspection chamber, and carries oak fenders, rubber seals, a walkway, a CCTV mast and a call point."""
    items = []
    for side in (-1, 1):
        n = 'left' if side < 0 else 'right'
        items += leaf_parts(side, open_deg)
        body, rod = actuator(side, open_deg)
        items += [('%s actuator body' % n, body, ACT_C), ('%s actuator rod' % n, rod, STAINLESS)]
        items += fixed_parts(side)
    return items


# ------------------------------------------------------------------ single leaf, for the detail drawing
def gate_leaf():
    """One gate leaf (the left hand leaf) on its own: the welded steel frame with its skin plate, girders and
    stiffeners, the oak fenders, the walkway and the rubber seals. Drawn in its own coordinates: X along the leaf
    from the heel pivot, Y towards the chamber face."""
    return [('gate leaf (welded S355 steel)', leaf_frame(), LEAF_C), ('oak fenders', fenders(), OAK),
            ('walkway and handrail', walkway(), WHITE), ('cill seal', cill_seal(), RUBBER),
            ('heel seal', heel_seal(), RUBBER), ('mitre seal', _mitre_seal_local(), RUBBER)]


# ------------------------------------------------------------------ the skin plate panel, for the FEA
PANEL = (HEEL_BOX, STIFFENERS[0][0], GIRDERS[0] + WEB_T / 2, GIRDERS[1] - WEB_T / 2)   # u0, u1, z0, z1


def skin_panel():
    """The most heavily loaded skin plate panel: 12 mm S355 plate, 580 x 630, between the bottom two girders,
    the heel post and the first stiffener, where the water pressure is greatest. Used for the FEA."""
    u0, u1, z0, z1 = PANEL
    return [('skin plate panel', box(u0, u1, T2 - SKIN, T2, z0, z1), LEAF_C)]


# ------------------------------------------------------------------ Design B concept: vertical lift gate
def lift_gate():
    """Design B, a concept: one steel gate that lifts straight up between two guide towers, balanced by
    counterweights. Simple to seal, but the towers stand 11 m high over a heritage lock."""
    w, t = OPENING + 400, 400
    panel = box(-w / 2, w / 2, -t / 2, t / 2, 0, HEIGHT)
    for z in (1000, 2500, 4000, 5400):
        panel = panel.cut(box(-w / 2 + 300, w / 2 - 300, -t / 2 - 1, -t / 2 + 150, z, z + 700))
    towers = None
    for sx in (-1, 1):
        x0 = sx * (OPENING / 2 + 100)
        tw = box(min(x0, x0 + sx * 700), max(x0, x0 + sx * 700), -450, 450, 0, 11000)
        tw = tw.cut(box(min(x0, x0 + sx * 150), max(x0, x0 + sx * 150), -t / 2 - 10, t / 2 + 10, -1, 11001))
        towers = tw if towers is None else towers.union(tw)
    beam = box(-OPENING / 2 - 800, OPENING / 2 + 800, -450, 450, 11000, 11800)
    cw = None
    for sx in (-1, 1):
        x0 = sx * (OPENING / 2 + 450)
        c = box(x0 - 175, x0 + 175, 500, 800, 4000, 7000)
        cw = c if cw is None else cw.union(c)
    return [('lift gate panel', panel, LEAF_C), ('guide towers', towers, CONCRETE), ('lifting beam and winch house', beam, DARK),
            ('counterweights', cw, ORANGE)]


MODELS = [
    dict(name='esp2023_lock_gates', title='ESP 2023 lock gates (GA)', fn=lock_gates, criteria='3.1, 3.2',
         uses='ESP 2023 Task 2, Part B: the preferred design, a pair of mitre gates with hinges, seals, drive, '
              'fenders and CCTV. General arrangement, simulation of the gates opening, FEA of the bottom pintle.',
         section=None, explode=None, iso=(-1, -1.3, 0.9), folder='ESP 2023', sim=True),
    dict(name='esp2023_gate_leaf', title='ESP 2023 gate leaf', fn=gate_leaf, criteria='3.1, 3.2',
         uses='ESP 2023 Task 2: one welded steel leaf with its girders, stiffeners, fenders and seals. Detail '
              'drawing and section A-A through the girders.',
         section='y', explode=None, iso=(-1, -1, 0.8), folder='ESP 2023'),
    dict(name='esp2023_skin_panel', title='ESP 2023 skin plate panel', fn=skin_panel, criteria='3.2',
         uses='ESP 2023 Task 2: the skin plate panel that takes the highest water pressure. FEA with hydrostatic '
              'pressure, checked by hand.',
         section=None, explode=None, iso=(-1, 1, 0.8), folder='ESP 2023'),
    dict(name='esp2023_lift_gate', title='ESP 2023 concept B: lift gate', fn=lift_gate, criteria='3.1',
         uses='ESP 2023 Task 2, Part A: the second design idea, a vertical lift gate, for comparison with the '
              'mitre gates.',
         section=None, explode=None, folder='ESP 2023', fea=False),
]
