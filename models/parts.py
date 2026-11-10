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
]


# ------------------------------------------------------------------ project folders
# Projects such as ESP 2023 keep every file they generate (models, drawings, animations, steps, simulation and
# FEA) together in their own folder under docs/, named by the model's 'folder' key.
from esp2023 import MODELS as ESP2023_MODELS  # noqa: E402
from esp2026 import MODELS as ESP2026_MODELS  # noqa: E402

MODELS += ESP2023_MODELS + ESP2026_MODELS


def base_of(m):
    """The folder under docs/ that holds a model's files, with a trailing slash ('' for the hub's own models)."""
    return m['folder'] + '/' if m.get('folder') else ''
