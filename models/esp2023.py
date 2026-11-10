"""ESP 2023: replacement lock gates for Canal Heritage (T Level Employer-Set Project 8730-035, Summer 2023, Task 2).

The brief: a gate system for each end of five 200 year old locks. Each gate fits an opening 4.2 m wide, has an
overall height of 6 m and holds a head of water between 2 m and 5.5 m. The gates open and close automatically and
independently, the drive sits out of sight in an inspection chamber beside each gate, and the gates must be easy
to lift out by mobile crane, durable at the hinges, sealed, protected against boat strikes, watched by cameras and
sensors and fitted with an emergency call point.

Design A (preferred): a pair of steel mitre gates. Design B (concept only): a single vertical lift gate.

Every component is its own part (an Inventor .ipt), listed in PARTS below with its material and the features
that make it (the Inventor build steps). The gate leaf and the general arrangement are assemblies (.iam) of those
parts: gate_leaf() and lock_gates().

Coordinates (mm): the lock centre line is the Y axis, upstream (the full chamber side) is +Y, the cill is z = 0
and the lock walls are at x = -2100 and x = +2100 (the 4.2 m opening). When the gates are shut the two leaves meet
on the centre line at a mitre, pointing upstream at 1 in 3 (18.4 degrees), so the water pressure pushes the mitre
posts together and seals the gap.

Leaf coordinates: u (X) runs along the left leaf from the heel pivot to the mitre, v (Y) points to the chamber
(upstream) face, z is up. The pivot is the Z axis. The right leaf is the mirror image.

Every model here is plain CadQuery, generated from the numbers below, like the rest of the Unit 3 CAD hub.
"""
import functools
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
T2 = 225                  # half the leaf thickness (450 thick)
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
EYE_R = 45                # actuator rod end eye radius
BRACKET_V = T2 + 125 + EYE_R   # rod end pin, 395 from the leaf centre line
ACT_Z = 5800              # actuator centre height
W_OFF = (2400, 1400)      # actuator rear pivot, measured from the heel pivot (x outwards, y upstream)
CHAMBER = (300, 2650, 600, 2400)   # inspection chamber x from, x to (from the pivot), y from, y to
ACT_BODY = 1900           # actuator body length from the rear pivot
ROD_LEN = 1600            # rod length, eye centre to rod end
PADDLE = (1670, 2070, 925, 1325)   # paddle opening in the skin plate: u from, u to, z from, z to
PADDLE_U, PADDLE_V = 1870, -300    # paddle rod axis (on the downstream side)
PADDLE_LIFT = 500         # the paddle door rises 500 mm to open
SLOT_Z = 5550             # bottom of the slot in the chamber wall for the actuator rod

# colours
LEAF_C = '4F6D7A'         # painted steel (heritage grey-green)
WHITE = 'E6E6E6'
OAK = 'A0703C'
RUBBER = '2B2B2B'
STAINLESS = 'C9D3DD'
BRONZE = 'B08D57'
CONCRETE = 'B5B0A6'
ACT_C = '3FA37C'
DARK = '4A5562'
YELLOW = 'E8C23D'
ORANGE = 'E8A33D'
GRP = '7D8B5A'
RED = 'C8372D'

# Inventor commands
NEW_PART = 'File > New > Standard (mm).ipt'
SKETCH = '3D Model tab > Sketch panel > Start 2D Sketch'
EXTRUDE = '3D Model tab > Create panel > Extrude'
REVOLVE = '3D Model tab > Create panel > Revolve'
HOLE = '3D Model tab > Modify panel > Hole'
FILLET = '3D Model tab > Modify panel > Fillet'
SPLIT = '3D Model tab > Modify panel > Split'
RECT_PATTERN = '3D Model tab > Pattern panel > Rectangular Pattern'
MIRROR_F = '3D Model tab > Pattern panel > Mirror'
NEW_ASSY = 'File > New > Standard (mm).iam'
PLACE = 'Assemble tab > Component panel > Place'
CONTENT = 'Assemble tab > Component panel > Place from Content Center'
CONSTRAIN = 'Assemble tab > Relationships panel > Constrain'
MIRROR = 'Assemble tab > Pattern panel > Mirror'
PATTERN = 'Assemble tab > Pattern panel > Pattern'

STEEL_D, STAINLESS_D, OAK_D, RUBBER_D, CONCRETE_D = 7850, 8000, 750, 1200, 2400


# ------------------------------------------------------------------ shape helpers
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def zcyl(r, z0, z1, x=0, y=0):
    return cq.Workplane('XY').workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def cyl(r, p0, d, h):
    """A cylinder of radius r from point p0, length h along the direction d."""
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r, h, cq.Vector(*p0), cq.Vector(*d)))


def xcyl(r, x0, x1, y=0, z=0):
    return cyl(r, (x0, y, z), (1, 0, 0), x1 - x0)


def ycyl(r, y0, y1, x=0, z=0):
    return cyl(r, (x, y0, z), (0, 1, 0), y1 - y0)


def ucyl(r, u0, u1, v, z):
    """A round bar along the leaf (local X)."""
    return xcyl(r, u0, u1, v, z)


def hexagon(af, z0, z1, x=0, y=0):
    return cq.Workplane('XY').workplane(offset=z0).center(x, y).polygon(6, af / math.cos(math.pi / 6)).extrude(z1 - z0)


def union(*shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.union(s)
    return out


def mitre_cut():
    """Everything beyond the mitre face, in leaf coordinates. The mitre face is the plane u = LEAF + v / 3,
    which becomes the plane x = -GAP once the leaf is placed in the lock."""
    pts = [(LEAF - 2000 / 3, -2000), (LEAF + 2000 / 3, 2000), (LEAF + 4000, 2000), (LEAF + 4000, -2000)]
    return cq.Workplane('XY').workplane(offset=-500).polyline(pts).close().extrude(9000)


def F(title, command, actions, shape, note=None):
    """One feature of a part: what you do in Inventor and the part as it stands afterwards."""
    return dict(title=title, command=command, actions=actions, shape=shape, note=note)


# ------------------------------------------------------------------ the parts
# Each part is drawn where it sits (leaf coordinates for the parts that turn with a leaf, lock coordinates of the
# right hand side for the fixed parts, actuator coordinates for the drive). 'origin' is the point that becomes the
# origin of the part file, so each part model starts from a sensible datum.
PARTS = []
GROUPS = [('frame', 'Gate leaf frame (welded fabrication)'), ('leaf', 'Fitted to each leaf'),
          ('hinge', 'Hinges and gate position sensor'), ('drive', 'Drive (one per leaf)'),
          ('chamber', 'Inspection chamber, controls and CCTV'), ('civil', 'Civil works')]


def part(key, name, group, material, colour, density, desc, origin=(0, 0, 0), file=None, bought=False):
    def deco(fn):
        PARTS.append(dict(key=key, name=name, group=group, material=material, colour=colour, density=density,
                          desc=desc, origin=origin, feats=fn, file=file or key + '.ipt', bought=bought))
        return fn
    return deco


# ---------------------------------------------------- gate leaf frame
@part('heel_post', 'heel post', 'frame', 'S355 steel, 25 mm plate, welded', LEAF_C, STEEL_D,
      'Round backed box post the leaf turns on. Hollow, with a solid bearing block at the foot, a bore for the '
      'pintle bush and a journal at the top for the anchor collar.')
def _heel_post():
    f1 = zcyl(HEEL_R, 50, 5850).union(box(0, HEEL_BOX, -T2, T2, 50, 5850))
    f2 = f1.cut(zcyl(HEEL_R - 25, 350, 5825).union(box(0, HEEL_BOX - 25, -T2 + 25, T2 - 25, 350, 5825)))
    f3 = f2.cut(zcyl(95, 49, 300))
    f4 = f3.union(zcyl(100, 5850, 6000))
    return [
        F('Sketch and extrude the section', EXTRUDE,
          [NEW_PART + ' and save it as heel_post.ipt.',
           'Start 2D Sketch on the XZ Plane (the ground). Circle diameter 450 on the origin (the pivot axis). Rectangle '
           'from the centre, 400 along X and 450 wide (225 each side). Finish Sketch.',
           'Extrude both regions 5800 mm up, with a 50 mm start offset (Advanced), so the post runs from 50 to 5850.'],
          f1, 'The origin of this part is the pivot axis: every other part of the leaf is placed from it.'),
        F('Make it hollow', EXTRUDE,
          ['Work Features panel > Plane > Offset from Plane: 5825 mm above the XZ Plane. Sketch on it.',
           'Project the outline (Sketch tab > Project Geometry) and Offset it 25 mm inwards: 25 mm plate.',
           'Extrude the inner region, Cut, 5475 mm downwards. Click OK.'],
          f2, 'The bottom 300 mm stays solid: the bearing block that sits on the pintle.'),
        F('Bore for the pintle bush', HOLE,
          ['Click Hole. Placement: the bottom face, on the pivot axis.',
           'Simple Hole, diameter 190 mm, Distance 250 mm. Click OK.'],
          f3, 'The bronze pintle bush is pressed into this bore.'),
        F('Top journal', EXTRUDE,
          ['Sketch on the top face: circle diameter 200 on the pivot axis. Extrude 150 mm up. Click OK.',
           'Material: Steel S355 (Manage tab > Styles Editor if it is not in your library). Save.'],
          f4, 'The anchor collar and its bush fit round this journal: the top hinge.'),
    ]


@part('mitre_post', 'mitre post', 'frame', 'S355 steel, 25 mm plate, welded', LEAF_C, STEEL_D,
      'Hollow box post at the free end of the leaf, cut at 1 in 3 so the two leaves meet at the mitre.',
      origin=(LEAF - MITRE_BOX, 0, 0))
def _mitre_post():
    f1 = box(LEAF - MITRE_BOX, LEAF + 400, -T2, T2, 50, TOP)
    f2 = f1.cut(box(LEAF - MITRE_BOX + 25, LEAF - 90, -T2 + 25, T2 - 25, 75, TOP - 25))
    f3 = f2.cut(mitre_cut())
    return [
        F('Extrude the box', EXTRUDE,
          [NEW_PART + ' and save it as mitre_post.ipt.',
           'Sketch on the XZ Plane: rectangle 700 x 450 with its left edge on the origin. Extrude 5910 mm up.'],
          f1, 'The post is drawn 700 long; the end is trimmed to the mitre angle later.'),
        F('Make it hollow', EXTRUDE,
          ['Sketch on a work plane 5935 mm up: rectangle 25 mm in from the left, front and back faces, ending 490 mm '
           'from the left end. Extrude Cut 5860 mm down.'],
          f2, 'The ends and the mitre end stay solid.'),
        F('Trim the mitre', SPLIT,
          ['Work Features panel > Plane > Angle to Plane around Edge: the vertical line 300 mm along X on the leaf '
           'centre line, 18.43 degrees (1 in 3) to the end face.',
           'Click Split, Trim Solid, and remove the end beyond the plane. Save.'],
          f3, 'The water pushes the two mitre faces together, so the gates seal harder the higher the water.'),
    ]


@part('girder', 'girder', 'frame', 'S355 steel, web 20, flange 200 x 20', LEAF_C, STEEL_D,
      'Horizontal T girder between the heel and mitre posts. Eight per leaf, closer together near the bottom. '
      'Half depth slots take the stiffeners.', origin=(HEEL_BOX, 0, 0))
def _girder():
    web = box(HEEL_BOX, LEAF - MITRE_BOX, -T2 + FLANGE[1], T2 - SKIN, -WEB_T / 2, WEB_T / 2)
    fl = box(HEEL_BOX, LEAF - MITRE_BOX, -T2, -T2 + FLANGE[1], -FLANGE[0] / 2, FLANGE[0] / 2)
    f1 = web.union(fl)
    f2 = f1
    for u0, u1 in STIFFENERS:
        f2 = f2.cut(box(u0, u1, 4, T2 - SKIN + 1, -WEB_T, WEB_T))
    return [
        F('Extrude the T section', EXTRUDE,
          [NEW_PART + ' and save it as girder.ipt.',
           'Sketch on the YZ Plane: the T. Web 418 x 20 (from the flange to the skin plate), flange 200 x 20 on the '
           'downstream edge. Extrude 1760 mm along X.'],
          f1, 'The flange is on the downstream side. The skin plate, welded to the other edge of the web, acts as the second flange.'),
        F('Slots for the stiffeners', EXTRUDE,
          ['Sketch on the top face of the web: two rectangles 15 wide and 209 long from the skin edge, 580 and 1165 mm '
           'from the left end. Extrude Cut Through All. Save.'],
          f2, 'Half depth slots: the girder and the stiffener slot into each other like an egg box, then are welded.'),
    ]


@part('stiffener', 'stiffener', 'frame', 'S355 steel plate, 15 thick', LEAF_C, STEEL_D,
      'Vertical stiffener plate, two per leaf. Splits the skin plate into panels about 580 x 630.',
      origin=(STIFFENERS[0][0], 0, 0))
def _stiffener():
    u0, u1 = STIFFENERS[0]
    f1 = box(u0, u1, -T2 + FLANGE[1], T2 - SKIN, 50, TOP)
    f2 = f1
    for z in GIRDERS:
        f2 = f2.cut(box(u0 - 1, u1 + 1, -T2, 4, z - WEB_T / 2, z + WEB_T / 2))
    return [
        F('Extrude the plate', EXTRUDE,
          [NEW_PART + ' and save it as stiffener.ipt.',
           'Sketch on the YZ Plane: rectangle 418 wide x 5910 high, 50 mm up. Extrude 15 mm.'],
          f1),
        F('Slots for the girders', EXTRUDE,
          ['Sketch on the side face: eight rectangles 20 high and 209 deep from the flange edge, centred at the girder '
           'levels ' + ', '.join(str(z) for z in GIRDERS) + '. Extrude Cut Through All. Save.'],
          f2, 'The stiffener slots over the girders from the downstream side.'),
    ]


@part('skin_plate', 'skin plate', 'frame', 'S355 steel plate, 12 thick', LEAF_C, STEEL_D,
      'The 12 mm plate on the chamber (upstream) face that holds back the water, with the opening for the gate paddle.',
      origin=(HEEL_BOX, 0, 0))
def _skin_plate():
    f1 = box(HEEL_BOX, LEAF - MITRE_BOX, T2 - SKIN, T2, 50, TOP)
    a, b, c, d = PADDLE
    f2 = f1.cut(box(a, b, T2 - SKIN - 1, T2 + 1, c, d))
    return [
        F('Extrude the plate', EXTRUDE,
          [NEW_PART + ' and save it as skin_plate.ipt.',
           'Sketch on the XY Plane (the front): rectangle 1760 wide x 5910 high, 50 mm up. Extrude 12 mm.'],
          f1, 'Water pressure grows with depth: 54 kPa at the cill with 5.5 m of water.'),
        F('Paddle opening', EXTRUDE,
          ['Sketch on the front face: square 400 x 400, its bottom left corner 1270 from the left edge and 925 up. '
           'Extrude Cut Through All. Save.'],
          f2, 'The paddle opening lets water through the gate to empty the lock before the gates open.'),
    ]


@part('actuator_bracket', 'actuator bracket', 'frame', 'S355 steel, welded', LEAF_C, STEEL_D,
      'Clevis bracket on the chamber face that the actuator rod end pins to.', origin=(BRACKET_U, T2, ACT_Z))
def _actuator_bracket():
    u, v = BRACKET_U, BRACKET_V
    f1 = box(u - 80, u + 80, T2, T2 + 20, 5620, 5780)
    f2 = f1.union(box(u - 50, u + 50, T2 + 20, v, 5720, 5755)).union(zcyl(50, 5720, 5755, u, v))
    f3 = f2.union(box(u - 10, u + 10, T2 + 20, v - 50, 5640, 5720))
    f4 = f3.cut(zcyl(20, 5700, 5760, u, v))
    return [
        F('Base plate', EXTRUDE, [NEW_PART + ' and save it as actuator_bracket.ipt.',
                                  'Sketch a 160 x 160 square on the XY Plane and Extrude 20 mm.'], f1),
        F('Lug', EXTRUDE, ['Sketch on a work plane 100 mm above the plate centre: a slot 100 wide reaching 150 mm out, '
                           'with a full round end (radius 50). Extrude 35 mm.'], f2),
        F('Gusset', EXTRUDE, ['Sketch on the YZ Plane under the lug: rectangle 100 x 80. Extrude 20 mm, Symmetric.'], f3),
        F('Pin hole', HOLE, ['Hole on the lug, concentric with the round end: diameter 40, Through All. Save.'], f4,
          'The rod end eye sits on this lug and a 40 mm pin goes through both.'),
    ]


@part('lifting_lug', 'lifting lug', 'frame', 'S355 steel plate, 30 thick', LEAF_C, STEEL_D,
      'Crane lifting lug. Two on top of each leaf, one over the heel post and one over the mitre post, so the leaf '
      'can be lifted out by mobile crane.')
def _lifting_lug():
    f1 = box(-80, 80, -15, 15, 0, 120).union(ycyl(80, -15, 15, 0, 120))
    f2 = f1.cut(ycyl(30, -16, 16, 0, 120))
    return [
        F('Extrude the outline', EXTRUDE,
          [NEW_PART + ' and save it as lifting_lug.ipt.',
           'Sketch on the XZ Plane: 160 wide, 120 high, with a full round top (radius 80). Extrude 30 mm, Symmetric.'], f1),
        F('Shackle hole', HOLE, ['Hole concentric with the round top: diameter 60, Through All. Save.'], f2,
          'Takes a 9.5 t shackle. The leaf weighs about 9 t.'),
    ]


@part('paddle_culvert', 'paddle culvert', 'frame', 'S355 steel, 15 mm plate box', LEAF_C, STEEL_D,
      'Square box that carries the water from the paddle opening in the skin plate, through the leaf, to the paddle door.',
      origin=(PADDLE_U, 0, (PADDLE[2] + PADDLE[3]) / 2))
def _paddle_culvert():
    a, b, c, d = PADDLE
    f1 = box(a - 15, b + 15, -T2, T2 - SKIN, c - 15, d + 15)
    f2 = f1.cut(box(a, b, -T2 - 1, T2, c, d))
    return [
        F('Extrude the box', EXTRUDE, [NEW_PART + ' and save it as paddle_culvert.ipt.',
                                       'Sketch on the XZ Plane: square 430 x 430. Extrude 438 mm.'], f1),
        F('Make it a tube', EXTRUDE, ['Sketch on one end: square 400 x 400, centred. Extrude Cut Through All. Save.'], f2),
    ]


# ---------------------------------------------------- fitted to each leaf
@part('oak_fender', 'oak fender', 'leaf', 'FSC oak, 150 x 200', OAK, OAK_D,
      'Rubbing fender on the chamber face: a boat touches timber, not the steel skin. Three per leaf, replaceable.',
      origin=(HEEL_BOX + 100, T2, 0))
def _oak_fender():
    f1 = box(HEEL_BOX + 100, LEAF - MITRE_BOX - 50, T2, T2 + 150, -100, 100)
    f2 = f1.edges('|X').fillet(20)
    return [
        F('Extrude the timber', EXTRUDE, [NEW_PART + ' and save it as oak_fender.ipt.',
                                          'Sketch a 150 x 200 rectangle on the YZ Plane. Extrude 1610 mm along X.'], f1),
        F('Round the edges', FILLET, ['Fillet the four long edges, radius 20 mm. Material: Oak (or Wood). Save.'], f2,
          'FSC certified oak: sustainable, and easy to replace after a boat strike.'),
    ]


@part('walkway_grating', 'walkway grating', 'leaf', 'Galvanised steel grating, 40 deep', WHITE, STEEL_D * 0.35,
      'Walkway on top of the leaf, so the lock keeper can cross and look at the moving parts.', origin=(HEEL_BOX, 0, TOP))
def _walkway_grating():
    f1 = box(HEEL_BOX, LEAF - MITRE_BOX, -T2, T2, TOP, HEIGHT)
    f2 = f1
    for v in (-125, -75, -25, 25, 75, 125):
        f2 = f2.cut(box(HEEL_BOX + 80, LEAF - MITRE_BOX - 80, v - 15, v + 15, TOP - 1, HEIGHT + 1))
    return [
        F('Extrude the panel', EXTRUDE, [NEW_PART + ' and save it as walkway_grating.ipt.',
                                         'Sketch a 1760 x 450 rectangle on the XZ Plane. Extrude 40 mm.'], f1),
        F('Drainage slots', EXTRUDE, ['Sketch one slot 1600 x 30 and Extrude Cut Through All, then Rectangular Pattern: '
                                      '6 slots at 50 mm. Save.'], f2, 'The slots show the open grating: water drains through.'),
    ]


@part('handrail', 'handrail', 'leaf', 'Galvanised steel tube, 48.3 dia', WHITE, STEEL_D * 0.12,
      'Handrail on the downstream edge of the walkway: three posts and two rails, welded.',
      origin=(HEEL_BOX + 100, -T2 + 25, HEIGHT))
def _handrail():
    v, r = -T2 + 25, 24
    us = [HEEL_BOX + 100, (HEEL_BOX + LEAF - MITRE_BOX) / 2, LEAF - MITRE_BOX - 100]
    f1 = union(*[zcyl(r, HEIGHT, HEIGHT + 1100, u, v) for u in us])
    f2 = f1
    for z in (HEIGHT + 550, HEIGHT + 1100 - r):
        f2 = f2.union(ucyl(r, us[0] - r, us[-1] + r, v, z))
    return [
        F('Posts', EXTRUDE, [NEW_PART + ' and save it as handrail.ipt.',
                             'Sketch three circles diameter 48.3 on the XZ Plane, 780 mm apart. Extrude 1100 mm.'], f1),
        F('Rails', EXTRUDE, ['Sketch two circles diameter 48.3 on the YZ Plane, at 550 and 1076 mm. Extrude 1608 mm '
                             'along X. Save.'], f2, 'Top rail at 1.1 m, as the building regulations ask for a guard.'),
    ]


@part('cill_seal', 'cill seal', 'leaf', 'EPDM rubber, 85 x 50', RUBBER, RUBBER_D,
      'Seal along the bottom of the leaf, against the cill.', origin=(HEEL_BOX, T2, 0))
def _cill_seal():
    f1 = box(HEEL_BOX, LEAF + 400, T2 - 85, T2, 0, 50)
    f2 = f1.cut(mitre_cut())
    return [
        F('Extrude the strip', EXTRUDE, [NEW_PART + ' and save it as cill_seal.ipt.',
                                         'Sketch an 85 x 50 rectangle on the YZ Plane. Extrude 2460 mm along X.'], f1),
        F('Trim at the mitre', SPLIT, ['Split with a work plane at 18.43 degrees, as for the mitre post. Material: '
                                       'EPDM rubber. Save.'], f2),
    ]


@part('heel_seal', 'heel seal', 'leaf', 'EPDM rubber, 30 x 80', RUBBER, RUBBER_D,
      'Seal down the back of the heel post, against the hollow quoin in the lock wall.', origin=(-HEEL_R, 0, 0))
def _heel_seal():
    f1 = box(-HEEL_R - 30, -HEEL_R, -40, 40, 50, 5850)
    return [F('Extrude the strip', EXTRUDE, [NEW_PART + ' and save it as heel_seal.ipt.',
                                             'Sketch a 30 x 80 rectangle on the XZ Plane. Extrude 5800 mm up. Save.'], f1)]


@part('mitre_seal', 'mitre seal', 'leaf', 'EPDM rubber, 30 thick', RUBBER, RUBBER_D,
      'Seal on the mitre face of the left leaf. The right leaf closes on to it.', origin=(LEAF, 0, 0))
def _mitre_seal():
    s = box(LEAF - 60, LEAF + 400, -40, 40, 50, TOP)
    s = to_lock(s, -1).intersect(box(-GAP, GAP, -3000, 3000, 0, 7000))
    f1 = s.translate((PIV, 0, 0)).rotate((0, 0, 0), (0, 0, 1), -math.degrees(THETA))
    return [F('Extrude and trim', EXTRUDE, [NEW_PART + ' and save it as mitre_seal.ipt.',
                                            'Sketch the seal section on the XZ Plane: 30 wide across the mitre, 84 long '
                                            'on the slope. Extrude 5910 mm up. Save.'], f1,
              'Only one leaf carries the mitre seal.')]


@part('pintle_bush', 'pintle bush', 'leaf', 'Aluminium bronze, cup bush', BRONZE, 7600,
      'Cup bush pressed into the foot of the heel post. It turns on the pintle and carries the weight of the leaf.',
      origin=(0, 0, 50))
def _pintle_bush():
    f1 = zcyl(95, 50, 300)
    f2 = f1.cut(zcyl(75, 49, 280))
    return [
        F('Extrude the cylinder', EXTRUDE, [NEW_PART + ' and save it as pintle_bush.ipt.',
                                            'Circle diameter 190 on the XZ Plane. Extrude 250 mm.'], f1),
        F('Bore', HOLE, ['Hole on the bottom face: diameter 150, Distance 230 mm (a cup). Material: Bronze. Save.'], f2,
          'Bronze on stainless steel wears slowly and needs no grease under water: a durable hinge.'),
    ]


@part('paddle_door', 'paddle door', 'leaf', 'Stainless steel 316, 20 plate', STAINLESS, STAINLESS_D,
      'Sliding door over the paddle culvert on the downstream face. The water pushes it on to its guides.',
      origin=(PADDLE_U, -T2, 875))
def _paddle_door():
    f1 = box(1620, 2120, -T2 - 20, -T2, 875, 1375)
    f2 = f1.union(box(PADDLE_U - 25, PADDLE_U + 25, -T2 - 100, -T2 - 20, 1300, 1375))
    return [
        F('Extrude the door', EXTRUDE, [NEW_PART + ' and save it as paddle_door.ipt.',
                                        'Sketch a 500 x 500 square on the XY Plane. Extrude 20 mm.'], f1),
        F('Rod lug', EXTRUDE, ['Sketch on the top face: rectangle 50 x 80 at the middle, out from the front. Extrude 75 mm '
                               'down. Save.'], f2, 'The paddle rod screws into this lug.'),
    ]


@part('paddle_guide', 'paddle guide', 'leaf', 'Stainless steel 316, angle', STAINLESS, STAINLESS_D,
      'Guide each side of the paddle door. Two per leaf, handed by turning one over.', origin=(1580, -T2, 700))
def _paddle_guide():
    f1 = box(1580, 1620, -T2 - 20, -T2, 700, 2000).union(box(1580, 1640, -T2 - 40, -T2 - 20, 700, 2000))
    return [F('Extrude the angle', EXTRUDE, [NEW_PART + ' and save it as paddle_guide.ipt.',
                                             'Sketch the L section on the XZ Plane: 40 x 20 with a 60 x 20 lip. Extrude '
                                             '1300 mm up. Save.'], f1,
              'Place the second guide in the assembly turned over (or with Mirror).')]


@part('paddle_rod', 'paddle rod', 'leaf', 'Stainless steel 316 bar, 30 dia', STAINLESS, STAINLESS_D,
      'Rod from the paddle door up to the paddle actuator.', origin=(PADDLE_U, PADDLE_V, 1375))
def _paddle_rod():
    f1 = zcyl(15, 1375, 5800, PADDLE_U, PADDLE_V)
    return [F('Extrude the bar', EXTRUDE, [NEW_PART + ' and save it as paddle_rod.ipt.',
                                           'Circle diameter 30 on the XZ Plane. Extrude 4425 mm. Save.'], f1)]


@part('paddle_actuator', 'paddle actuator', 'leaf', 'Bought in: electric linear actuator, 500 mm stroke, IP68', ACT_C,
      3000, 'Small electric actuator on the top girder that lifts the paddle door 500 mm. Bought in; modelled as an '
      'envelope with its fixing bracket.', origin=(PADDLE_U, PADDLE_V, 5200), bought=True)
def _paddle_actuator():
    u, v = PADDLE_U, PADDLE_V
    f1 = zcyl(45, 5200, 6400, u, v).cut(zcyl(20, 5199, 6350, u, v))
    f2 = f1.union(box(u - 40, u + 40, v - 40, v + 40, 6400, 6550))
    f3 = f2.union(box(u - 50, u + 50, -T2 - 20, -T2, 5760, 5960))
    f3 = f3.union(box(u - 20, u + 20, -262, -T2 - 20, 5780, 5820)).union(box(u - 20, u + 20, -262, -T2 - 20, 5900, 5940))
    return [
        F('Body', EXTRUDE, [NEW_PART + ' and save it as paddle_actuator.ipt.',
                            'Circle diameter 90 on the XZ Plane, Extrude 1200 mm. Hole diameter 40, 1150 deep, from the bottom.'], f1),
        F('Motor', EXTRUDE, ['Sketch an 80 x 80 square on the top face. Extrude 150 mm.'], f2),
        F('Fixing bracket', EXTRUDE, ['Sketch the 100 x 200 bracket plate 75 mm from the axis and Extrude 20 mm, then two '
                                      '40 x 40 standoffs to the body. Save.'], f3,
          'It bolts to the downstream flange of the top girder.'),
    ]


# ---------------------------------------------------- hinges and the gate position sensor (right hand side, lock coordinates)
@part('bottom_pintle', 'bottom pintle', 'hinge', 'Stainless steel 316, 150 dia pin', STAINLESS, STAINLESS_D,
      'The bottom hinge: a 150 mm pin on a base plate set in the cill and held down by four anchor bolts.',
      origin=(PIV, 0, 0))
def _bottom_pintle():
    f1 = box(-300, 300, -300, 300, -80, 0)
    f2 = f1.union(zcyl(75, 0, 280))
    f3 = f2.edges(cq.selectors.BoxSelector((-80, -80, -1), (80, 80, 1))).fillet(15)
    f3 = f3.edges(cq.selectors.BoxSelector((-80, -80, 279), (80, 80, 281))).fillet(10)
    f4 = f3
    for sx in (-1, 1):
        for sy in (-1, 1):
            f4 = f4.cut(zcyl(13, -81, 1, sx * 225, sy * 225))
    sh = lambda w: w.translate((PIV, 0, 0))
    return [
        F('Base plate', EXTRUDE, [NEW_PART + ' and save it as bottom_pintle.ipt.',
                                  'Sketch a 600 x 600 square centred on the origin on the XZ Plane. Extrude 80 mm down.'], sh(f1)),
        F('Pin', EXTRUDE, ['Sketch on the top face: circle diameter 150 on the origin. Extrude 280 mm up.'], sh(f2)),
        F('Fillets', FILLET, ['Fillet the root of the pin, radius 15 mm, and the top edge, radius 10 mm.'], sh(f3),
          'The root fillet keeps the stress down where the pin meets the plate: see the FEA.'),
        F('Bolt holes', HOLE, ['Hole on the top face of the plate: diameter 26, Through All, at 225 mm from the centre '
                               'each way (450 mm square). Material: Stainless Steel. Save.'], sh(f4)),
    ]


@part('anchor_bolt', 'anchor bolt M24', 'hinge', 'Stainless steel A4, M24 x 410 resin anchor and nut', STAINLESS,
      STAINLESS_D, 'Resin anchor stud and nut. Four hold each pintle into the cill and two hold each anchor plate '
      'into the lock wall.', bought=True)
def _anchor_bolt():
    f1 = zcyl(12, -380, 30)
    f2 = f1.union(hexagon(36, 0, 24))
    return [
        F('Stud', EXTRUDE, ['Place from Content Center (Fasteners > Bolts) or ' + NEW_PART + ': circle diameter 24, '
                            'Extrude 410 mm.'], f1),
        F('Nut', EXTRUDE, ['Sketch a hexagon 36 across the flats 380 mm from the bottom. Extrude 24 mm. Save.'], f2),
    ]


@part('anchor_collar', 'anchor collar', 'hinge', 'S355 steel forging, galvanised', DARK, STEEL_D,
      'The top hinge: a collar round the heel post journal on an arm that is anchored back into the lock wall. It '
      'stops the leaf tipping forwards. Release it and the leaf lifts straight out.', origin=(PIV, 0, 5870))
def _anchor_collar():
    f1 = zcyl(180, 5870, 5970)
    f2 = f1.union(box(170, 900, -60, 60, 5870, 5970))
    f3 = f2.cut(zcyl(120, 5869, 5971))
    sh = lambda w: w.translate((PIV, 0, 0))
    return [
        F('Collar', EXTRUDE, [NEW_PART + ' and save it as anchor_collar.ipt.',
                              'Circle diameter 360 on the XZ Plane. Extrude 100 mm.'], sh(f1)),
        F('Arm', EXTRUDE, ['Sketch a 730 x 120 rectangle from 170 mm out to 900 mm. Extrude 100 mm, Join.'], sh(f2)),
        F('Bore', HOLE, ['Hole on the centre: diameter 240, Through All. Save.'], sh(f3), 'The collar bush fits in this bore.'),
    ]


@part('collar_bush', 'collar bush', 'hinge', 'Aluminium bronze', BRONZE, 7600,
      'Bush in the anchor collar that the heel post journal turns in.', origin=(PIV, 0, 5870))
def _collar_bush():
    f1 = zcyl(120, 5870, 5970, PIV).cut(zcyl(100, 5869, 5971, PIV))
    return [F('Revolve the bush', REVOLVE, [NEW_PART + ' and save it as collar_bush.ipt.',
                                            'Sketch a 20 x 100 rectangle 100 mm from the Z axis on the XY Plane. Revolve '
                                            '360 degrees about the axis. Save.'], f1)]


@part('anchor_plate', 'anchor plate', 'hinge', 'S355 steel plate, 25 thick, galvanised', DARK, STEEL_D,
      'Plate set into the lock wall that the anchor collar arm bears against, held by two anchor bolts.',
      origin=(PIV + 900, 0, 5920))
def _anchor_plate():
    f1 = box(PIV + 900, PIV + 925, -150, 150, 5820, 6020)
    f2 = f1.cut(xcyl(13, PIV + 899, PIV + 926, -100, 5920)).cut(xcyl(13, PIV + 899, PIV + 926, 100, 5920))
    return [
        F('Extrude the plate', EXTRUDE, [NEW_PART + ' and save it as anchor_plate.ipt.',
                                         'Sketch a 300 x 200 rectangle on the YZ Plane. Extrude 25 mm.'], f1),
        F('Bolt holes', HOLE, ['Two holes diameter 26, Through All, 200 mm apart. Save.'], f2),
    ]


@part('encoder_bracket', 'encoder bracket', 'hinge', 'Stainless steel 316, bent plate', STAINLESS, STAINLESS_D,
      'Bracket on the anchor collar arm that holds the gate position encoder over the pivot.', origin=(PIV, 0, 5970))
def _encoder_bracket():
    f1 = box(260, 290, -40, 40, 5970, 6130)
    f2 = f1.union(box(-60, 290, -40, 40, 6110, 6130))
    sh = lambda w: w.translate((PIV, 0, 0))
    return [
        F('Upright', EXTRUDE, [NEW_PART + ' and save it as encoder_bracket.ipt.',
                               'Sketch a 30 x 80 rectangle. Extrude 160 mm up.'], sh(f1)),
        F('Top plate', EXTRUDE, ['Sketch a 350 x 80 rectangle on the top. Extrude 20 mm down, Join. Save.'], sh(f2)),
    ]


@part('position_encoder', 'gate position encoder', 'hinge', 'Bought in: absolute rotary encoder, IP68', ORANGE, 2000,
      'Absolute rotary encoder on the pivot axis, driven by the heel post journal. It tells the control centre the '
      'exact angle of the leaf: the sensor system the brief asks for.', origin=(PIV, 0, 6000), bought=True)
def _position_encoder():
    f1 = zcyl(50, 6020, 6110, PIV)
    f2 = f1.union(zcyl(10, 6000, 6020, PIV)).union(box(PIV + 40, PIV + 70, -12, 12, 6050, 6080))
    return [
        F('Body', EXTRUDE, [NEW_PART + ' and save it as position_encoder.ipt.',
                            'Circle diameter 100. Extrude 90 mm.'], f1),
        F('Shaft and cable gland', EXTRUDE, ['Circle diameter 20 on the bottom face, Extrude 20 mm. A 30 x 24 gland on '
                                             'the side. Save.'], f2),
    ]


# ---------------------------------------------------- drive (actuator coordinates: origin at the rear pivot, X towards the leaf)
@part('actuator_body', 'actuator body', 'drive', 'Bought in: electro-mechanical linear actuator, 20 kN, 1300 stroke, IP68',
      ACT_C, 2500, 'The actuator tube with its rear pivot eye. Bought in from an actuator maker; modelled from the '
      'catalogue sizes.', bought=True)
def _actuator_body():
    f1 = box(0, 70, -40, 40, -40, 40).union(zcyl(50, -40, 40))
    f2 = f1.union(xcyl(70, 70, ACT_BODY))
    f3 = f2.cut(xcyl(40, 120, ACT_BODY + 1)).cut(zcyl(20, -41, 41))
    return [
        F('Rear eye', EXTRUDE, [NEW_PART + ' and save it as actuator_body.ipt.',
                                'Sketch on the XZ Plane: a slot 80 wide from the origin to 70 mm, round end radius 50 '
                                'on the origin. Extrude 80 mm, Symmetric.'], f1),
        F('Tube', EXTRUDE, ['Sketch on the YZ Plane 70 mm along: circle diameter 140. Extrude 1830 mm.'], f2),
        F('Bore and pivot hole', HOLE, ['Hole on the tube end: diameter 80, 1780 deep. Hole through the eye: diameter 40. Save.'],
          f3, 'The origin is the rear pivot: the actuator turns about it as the leaf opens.'),
    ]


@part('actuator_motor', 'actuator motor and gearbox', 'drive', 'Bought in: 1.1 kW motor and gearbox, 230 V', DARK, 3000,
      'Motor and gearbox under the actuator tube. Runs from the mains supply in the control panel.', bought=True)
def _actuator_motor():
    f1 = box(200, 650, -75, 75, -235, -40)
    f2 = f1.cut(xcyl(70, 0, 2000))
    return [
        F('Block', EXTRUDE, [NEW_PART + ' and save it as actuator_motor.ipt.',
                             'Sketch a 450 x 150 rectangle. Extrude 195 mm.'], f1),
        F('Saddle', EXTRUDE, ['Sketch a circle diameter 140 on the end face, its centre 40 mm above the top. Extrude Cut '
                              'Through All, so the motor sits on the tube. Save.'], f2),
    ]


@part('actuator_rod', 'actuator rod', 'drive', 'Stainless steel 316 bar, 70 dia, hard chromed', STAINLESS, STAINLESS_D,
      'The actuator rod. It slides out of the tube as the leaf shuts.')
def _actuator_rod():
    f1 = xcyl(35, -ROD_LEN, -110)
    return [F('Extrude the bar', EXTRUDE, [NEW_PART + ' and save it as actuator_rod.ipt.',
                                           'Circle diameter 70 on the YZ Plane, 110 mm back from the origin. Extrude '
                                           '1490 mm back along X. Save.'], f1,
              'The origin is the rod end pin, so the rod is placed from the pin on the leaf.')]


@part('rod_end', 'rod end eye', 'drive', 'Stainless steel 316, with spherical bearing', STAINLESS, STAINLESS_D,
      'Eye on the end of the actuator rod. It pins to the actuator bracket on the leaf.')
def _rod_end():
    f1 = zcyl(45, -40, 40)
    f2 = f1.union(xcyl(30, -110, -35))
    f3 = f2.cut(zcyl(20, -41, 41))
    return [
        F('Eye', EXTRUDE, [NEW_PART + ' and save it as rod_end.ipt.', 'Circle diameter 90. Extrude 80 mm, Symmetric.'], f1),
        F('Neck', EXTRUDE, ['Circle diameter 60 on the YZ Plane. Extrude 75 mm back along X.'], f2),
        F('Pin hole', HOLE, ['Hole on the eye centre: diameter 40, Through All. Save.'], f3,
          'A spherical bearing in the eye lets the rod follow the leaf without bending.'),
    ]


@part('pivot_pedestal', 'pivot pedestal', 'drive', 'S355 steel, galvanised', DARK, STEEL_D,
      'Pedestal on the plinth that the rear eye of the actuator pins to.', origin=(PIV + W_OFF[0], W_OFF[1], 5700))
def _pivot_pedestal():
    x, y = PIV + W_OFF[0], W_OFF[1]
    f1 = zcyl(95, 5700, 5720, x, y)
    f2 = f1.union(zcyl(50, 5720, 5755, x, y))
    f3 = f2.cut(zcyl(20, 5699, 5756, x, y))
    return [
        F('Base plate', EXTRUDE, [NEW_PART + ' and save it as pivot_pedestal.ipt.', 'Circle diameter 190. Extrude 20 mm.'], f1),
        F('Boss', EXTRUDE, ['Circle diameter 100 on the top. Extrude 35 mm.'], f2),
        F('Pin hole', HOLE, ['Hole on the centre: diameter 40, Through All. Save.'], f3),
    ]


@part('pivot_pin', 'pivot pin', 'drive', 'Stainless steel 316, 40 dia', STAINLESS, STAINLESS_D,
      'Headed pin, two per actuator: one at the rear pivot, one through the rod end eye and the leaf bracket.',
      origin=(0, 0, ACT_Z - 65))
def _pivot_pin():
    f1 = zcyl(20, ACT_Z - 65, ACT_Z + 40)
    f2 = f1.union(zcyl(30, ACT_Z + 40, ACT_Z + 55))
    return [
        F('Pin', EXTRUDE, [NEW_PART + ' and save it as pivot_pin.ipt.', 'Circle diameter 40. Extrude 105 mm.'], f1),
        F('Head', EXTRUDE, ['Circle diameter 60 on the top. Extrude 15 mm. Save.'], f2),
    ]


# ---------------------------------------------------- inspection chamber, controls and CCTV (right hand side)
CX0, CX1, CY0, CY1 = PIV + CHAMBER[0], PIV + CHAMBER[1], CHAMBER[2], CHAMBER[3]
WALL = 150
COVER_L = (CX1 - CX0 - 2 * WALL) / 3


@part('inspection_chamber', 'inspection chamber', 'chamber', 'Precast concrete C40/50', CONCRETE, CONCRETE_D,
      'Purpose built chamber beside the gate for the drive: 2350 x 1800 x 1000 deep, 150 walls, a slot in the lock '
      'side wall for the actuator rod and a rebate for the cover panels. Handed: left and right.',
      origin=(CX0, CY0, 5000))
def _inspection_chamber():
    t = WALL
    f0 = box(CX0, CX1, CY0, CY1, 5000, HEIGHT)
    f1 = f0.cut(box(CX0 + t, CX1 - t, CY0 + t, CY1 - t, 5000 + t, HEIGHT + 1))
    f2 = f1.cut(box(CX0 - 1, CX0 + t + 1, 800, 2300, SLOT_Z, HEIGHT + 1))
    f3 = f2.cut(box(CX0 + t, CX1 - t, CY0 + 75, CY0 + t, HEIGHT - 50, HEIGHT + 1))
    f3 = f3.cut(box(CX0 + t, CX1 - t, CY1 - t, CY1 - 75, HEIGHT - 50, HEIGHT + 1))
    return [
        F('Box', EXTRUDE, [NEW_PART + ' and save it as inspection_chamber.ipt.',
                           'Sketch a 2350 x 1800 rectangle. Extrude 1000 mm.'], f0),
        F('Hollow it out', 'Shell', ['3D Model tab > Modify panel > Shell. Remove the top face. Thickness 150 mm.'], f1,
          'Shell gives the same result in one step: 150 mm walls and floor.'),
        F('Slot for the actuator', EXTRUDE, ['Sketch on the lock side wall: rectangle 1500 wide and 450 deep from the top. '
                                             'Extrude Cut Through the wall.'], f2,
          'The actuator rod reaches through the slot to the leaf.'),
        F('Cover rebate', EXTRUDE, ['Sketch two 75 mm strips on the top of the long walls. Extrude Cut 50 mm. Save.'], f3,
          'The cover panels sit flush with the ground in this rebate.'),
    ]


@part('actuator_plinth', 'actuator plinth', 'chamber', 'Concrete C40/50, cast in the chamber', CONCRETE, CONCRETE_D,
      'Plinth in the chamber that carries the pivot pedestal. Cast against the end wall.',
      origin=(PIV + W_OFF[0], W_OFF[1], 5150))
def _actuator_plinth():
    x, y = PIV + W_OFF[0], W_OFF[1]
    f1 = zcyl(150, 5000 + WALL, 5700, x, y)
    f2 = f1.intersect(box(CX0 + WALL, CX1 - WALL, CY0 + WALL, CY1 - WALL, 5000, 6000))
    return [
        F('Cylinder', EXTRUDE, [NEW_PART + ' and save it as actuator_plinth.ipt.', 'Circle diameter 300. Extrude 550 mm.'], f1),
        F('Trim to the wall', EXTRUDE, ['Sketch a line 100 mm from the centre and Extrude Cut the back off, where it is '
                                        'cast against the chamber wall. Save.'], f2),
    ]


@part('cover_panel', 'chamber cover panel', 'chamber', 'GRP grating panel, 50 deep, 30 kN/m2', GRP, 900,
      'Removable cover panel over the chamber. Three per chamber. Lift one out to inspect the drive.',
      origin=(CX0 + WALL, CY0 + 75, HEIGHT - 50))
def _cover_panel():
    x0, x1 = CX0 + WALL, CX0 + WALL + COVER_L - 1
    f1 = box(x0, x1, CY0 + 75, CY1 - 75, HEIGHT - 50, HEIGHT)
    xm = (x0 + x1) / 2
    f2 = f1.cut(zcyl(15, HEIGHT - 51, HEIGHT + 1, xm, CY0 + 300)).cut(zcyl(15, HEIGHT - 51, HEIGHT + 1, xm, CY1 - 300))
    return [
        F('Extrude the panel', EXTRUDE, [NEW_PART + ' and save it as cover_panel.ipt.',
                                         'Sketch a 682 x 1650 rectangle. Extrude 50 mm.'], f1),
        F('Lifting holes', HOLE, ['Two holes diameter 30, Through All, 225 mm in from each end. Save.'], f2,
          'The lifting keys go in these holes.'),
    ]


@part('control_panel', 'control panel', 'chamber', 'Bought in: stainless IP66 enclosure, controller, mains isolator, UPS',
      'D9DEE3', 1500, 'Control panel on the chamber end wall: the actuator controller, the mains isolator and a '
      'battery back up, linked to the off-site control centre.', origin=(CX1 - WALL, 2000, 5250), bought=True)
def _control_panel():
    x1 = CX1 - WALL
    f1 = box(x1 - 150, x1, 1800, 2200, 5250, 5750)
    f2 = f1.union(box(x1 - 165, x1 - 150, 1830, 1860, 5450, 5550))
    return [
        F('Enclosure', EXTRUDE, [NEW_PART + ' and save it as control_panel.ipt.', 'Sketch a 400 x 500 rectangle. Extrude 150 mm.'], f1),
        F('Door handle', EXTRUDE, ['Sketch a 30 x 100 rectangle on the door. Extrude 15 mm. Save.'], f2),
    ]


MAST = (CX1 - 75, CY1 - 75)


@part('cctv_mast', 'CCTV mast', 'chamber', 'Galvanised steel tube, 120 dia, on a base plate', ORANGE, STEEL_D * 0.15,
      'Camera mast on the far corner of the chamber.', origin=(MAST[0], MAST[1], HEIGHT))
def _cctv_mast():
    mx, my = MAST
    f1 = box(mx - 75, mx + 75, my - 75, my + 75, HEIGHT, HEIGHT + 20)
    f2 = f1.union(zcyl(60, HEIGHT + 20, 9000, mx, my))
    return [
        F('Base plate', EXTRUDE, [NEW_PART + ' and save it as cctv_mast.ipt.', 'Sketch a 150 x 150 square. Extrude 20 mm.'], f1),
        F('Tube', EXTRUDE, ['Circle diameter 120 on the top. Extrude 2980 mm. Save.'], f2),
    ]


@part('cctv_camera', 'CCTV camera', 'chamber', 'Bought in: PTZ camera with bracket, IP67', 'F2F2F2', 1200,
      'Pan, tilt and zoom camera looking down the gate, so the control centre can watch it work.', bought=True,
      origin=(MAST[0], MAST[1], 8800))
def _cctv_camera():
    mx, my = MAST
    f1 = box(mx - 140, mx - 60, my - 110, my + 40, 8800, 8920)
    cam = box(-150, 150, -75, 75, -75, 75).rotate((0, 0, 0), (0, 0, 1), -125).translate((mx - 130, my - 185, 8850))
    f2 = f1.union(cam)
    return [
        F('Bracket', EXTRUDE, [NEW_PART + ' and save it as cctv_camera.ipt.', 'Sketch an 80 x 150 rectangle beside the mast. Extrude 120 mm.'], f1),
        F('Camera', EXTRUDE, ['Sketch a 300 x 150 rectangle turned 125 degrees. Extrude 150 mm. Save.'], f2),
    ]


CP_X = CX1 - 75


@part('call_point_post', 'call point post', 'chamber', 'Stainless steel box section 150 x 150', 'D9DEE3', STEEL_D * 0.1,
      'Post on the near corner of the chamber that carries the emergency call point.', origin=(CP_X, CY0, HEIGHT))
def _call_point_post():
    f1 = box(CP_X - 75, CP_X + 75, CY0, CY0 + 150, HEIGHT, HEIGHT + 1200)
    return [F('Extrude the post', EXTRUDE, [NEW_PART + ' and save it as call_point_post.ipt.',
                                            'Sketch a 150 x 150 square. Extrude 1200 mm. Save.'], f1)]


@part('call_point', 'emergency call point', 'chamber', 'Bought in: stop button and intercom, IP66', YELLOW, 1500,
      'Emergency call point: a stop button that halts the gates and an intercom to the lock keeper.',
      origin=(CP_X, CY0, HEIGHT + 900), bought=True)
def _call_point():
    f1 = box(CP_X - 110, CP_X + 110, CY0 - 85, CY0, HEIGHT + 900, HEIGHT + 1150)
    f2 = f1.union(ycyl(30, CY0 - 110, CY0 - 85, CP_X, HEIGHT + 1060))
    return [
        F('Box', EXTRUDE, [NEW_PART + ' and save it as call_point.ipt.', 'Sketch a 220 x 250 rectangle. Extrude 85 mm.'], f1),
        F('Stop button', EXTRUDE, ['Circle diameter 60 on the front. Extrude 25 mm. Colour it red. Save.'], f2),
    ]


# ---------------------------------------------------- civil works
CILL = (-2750, 2750, -900, 1200, -600)


@part('cill', 'cill', 'civil', 'Precast concrete C40/50', CONCRETE, CONCRETE_D,
      'New concrete cill across the lock: the gates seal on its top and the pintles are set into it.', origin=(0, 0, 0))
def _cill():
    x0, x1, y0, y1, z0 = CILL
    f1 = box(x0, x1, y0, y1, z0, 0)
    f2 = f1.cut(box(-PIV - 300, -PIV + 300, -300, 300, -80, 1)).cut(box(PIV - 300, PIV + 300, -300, 300, -80, 1))
    f3 = f2
    for sx in (-1, 1):
        for dx in (-1, 1):
            for dy in (-1, 1):
                f3 = f3.cut(zcyl(14, -400, 1, sx * PIV + dx * 225, dy * 225))
    return [
        F('Extrude the cill', EXTRUDE, [NEW_PART + ' and save it as cill.ipt.', 'Sketch a 5500 x 2100 rectangle. Extrude 600 mm down.'], f1),
        F('Pintle pockets', EXTRUDE, ['Sketch two 600 x 600 squares on the pivot axes. Extrude Cut 80 mm.'], f2),
        F('Anchor holes', HOLE, ['Holes diameter 28, 400 deep, on a 450 mm square round each pivot. Save.'], f3),
    ]


PART = {p['key']: p for p in PARTS}
for _i, _p in enumerate(PARTS, 1):
    _p['no'] = _i


@functools.lru_cache(maxsize=None)
def features(key):
    return PART[key]['feats']()


def shape(key):
    """The finished part where it sits in the design."""
    return features(key)[-1]['shape']


def part_shape(key):
    """The finished part in its own part file (its origin moved to the part datum)."""
    ox, oy, oz = PART[key]['origin']
    return shape(key).translate((-ox, -oy, -oz))


# ------------------------------------------------------------------ placing parts
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
    g = lock_point(BRACKET_U, BRACKET_V, ACT_Z, side, open_deg)
    wx = -(PIV + W_OFF[0]) if side < 0 else PIV + W_OFF[0]
    w = (wx, W_OFF[1], ACT_Z)
    return w, g, math.dist(w[:2], g[:2])


def _t(dx=0, dy=0, dz=0):
    return lambda w: w.translate((dx, dy, dz))


IDENT = lambda w: w


def leaf_instances(side):
    """Every part that turns with one leaf: (instance name, part key, how to move the part from where it is drawn)."""
    pin = lambda w: w.translate((BRACKET_U, BRACKET_V, 0))
    out = [('heel post', 'heel_post', IDENT), ('mitre post', 'mitre_post', IDENT)]
    out += [('girder %d' % (k + 1), 'girder', _t(dz=z)) for k, z in enumerate(GIRDERS)]
    out += [('stiffener %d' % (k + 1), 'stiffener', _t(dx=u0 - STIFFENERS[0][0])) for k, (u0, u1) in enumerate(STIFFENERS)]
    out += [('skin plate', 'skin_plate', IDENT), ('actuator bracket', 'actuator_bracket', IDENT),
            ('lifting lug 1', 'lifting_lug', _t(300, 0, 5850)), ('lifting lug 2', 'lifting_lug', _t(LEAF - 180, 0, TOP)),
            ('paddle culvert', 'paddle_culvert', IDENT), ('pintle bush', 'pintle_bush', IDENT)]
    out += [('oak fender %d' % (k + 1), 'oak_fender', _t(dz=z)) for k, z in enumerate(FENDERS)]
    out += [('walkway grating', 'walkway_grating', IDENT), ('handrail', 'handrail', IDENT),
            ('cill seal', 'cill_seal', IDENT), ('heel seal', 'heel_seal', IDENT),
            ('paddle door', 'paddle_door', IDENT), ('paddle guide 1', 'paddle_guide', IDENT),
            ('paddle guide 2', 'paddle_guide', lambda w: w.mirror('YZ', (PADDLE_U, 0, 0))),
            ('paddle rod', 'paddle_rod', IDENT), ('paddle actuator', 'paddle_actuator', IDENT),
            ('pivot pin, front', 'pivot_pin', pin)]
    if side < 0:
        out.append(('mitre seal', 'mitre_seal', IDENT))
    return out


def fixed_instances():
    """The parts fixed to the lock on the right hand side (lock coordinates). The left side is the mirror image."""
    W = (PIV + W_OFF[0], W_OFF[1])
    bolt_side = lambda y: (lambda w: w.rotate((0, 0, 0), (0, 1, 0), -90).translate((PIV + 900, y, 5920)))
    out = [('bottom pintle', 'bottom_pintle', IDENT)]
    out += [('anchor bolt %d' % (k + 1), 'anchor_bolt', _t(PIV + dx, dy, 0))
            for k, (dx, dy) in enumerate([(-225, -225), (225, -225), (225, 225), (-225, 225)])]
    out += [('anchor collar', 'anchor_collar', IDENT), ('collar bush', 'collar_bush', IDENT),
            ('anchor plate', 'anchor_plate', IDENT), ('anchor bolt 5', 'anchor_bolt', bolt_side(-100)),
            ('anchor bolt 6', 'anchor_bolt', bolt_side(100)), ('encoder bracket', 'encoder_bracket', IDENT),
            ('gate position encoder', 'position_encoder', IDENT),
            ('inspection chamber', 'inspection_chamber', IDENT), ('actuator plinth', 'actuator_plinth', IDENT)]
    out += [('cover panel %d' % (k + 1), 'cover_panel', _t(dx=k * COVER_L)) for k in range(3)]
    out += [('control panel', 'control_panel', IDENT), ('CCTV mast', 'cctv_mast', IDENT), ('CCTV camera', 'cctv_camera', IDENT),
            ('call point post', 'call_point_post', IDENT), ('emergency call point', 'call_point', IDENT),
            ('pivot pedestal', 'pivot_pedestal', IDENT), ('pivot pin, rear', 'pivot_pin', _t(W[0], W[1], 0))]
    return out


def actuator_instances(side, open_deg=0.0):
    """The actuator body, motor, rod and rod end, placed in lock coordinates for the leaf at open_deg."""
    w, g, d = actuator_geometry(side, open_deg)
    ang = math.degrees(math.atan2(g[1] - w[1], g[0] - w[0]))
    at_w = lambda s: s.rotate((0, 0, 0), (0, 0, 1), ang).translate(w)
    at_g = lambda s: s.rotate((0, 0, 0), (0, 0, 1), ang).translate(g)
    return [('actuator body', 'actuator_body', at_w), ('actuator motor and gearbox', 'actuator_motor', at_w),
            ('actuator rod', 'actuator_rod', at_g), ('rod end eye', 'rod_end', at_g)]


def colour(key):
    return PART[key]['colour']


def ga_instances(open_deg=0.0):
    """Every part in the general arrangement: (instance name, part key, shape in lock coordinates)."""
    out = [('cill', 'cill', shape('cill'))]
    for side in (-1, 1):
        n = 'left' if side < 0 else 'right'
        for nm, key, tf in leaf_instances(side):
            full = nm if nm == 'mitre seal' else '%s %s' % (n, nm)
            out.append((full, key, to_lock(tf(shape(key)), side, open_deg)))
        for nm, key, tf in actuator_instances(side, open_deg):
            out.append(('%s %s' % (n, nm), key, tf(shape(key))))
        for nm, key, tf in fixed_instances():
            s = tf(shape(key))
            out.append(('%s %s' % (n, nm), key, s.mirror('YZ') if side < 0 else s))
    return out


def lock_gates(open_deg=0.0):
    """Design A, the preferred design: a pair of steel mitre gates for a 4.2 m wide lock, 6 m high, holding up to
    5.5 m of water. Each leaf is a welded steel frame of separate parts (heel post, mitre post, girders, stiffeners,
    skin plate) carrying oak fenders, seals, a walkway, lifting lugs and a gate paddle. It turns on a stainless
    pintle and an anchor collar with bronze bushes, has a position encoder on its pivot, and is driven by an electric
    actuator in an inspection chamber with a control panel, cover panels, a CCTV mast and an emergency call point."""
    return [(n, s, colour(k)) for n, k, s in ga_instances(open_deg)]


def instance_keys(items_fn):
    return {n: k for n, k, s in items_fn()}


def group_of(name):
    """Which way an instance moves in the simulation: 'leaf', 'paddle', 'body', 'rod' or 'fixed'."""
    base = name.replace('left ', '', 1).replace('right ', '', 1)
    if base in ('paddle door', 'paddle rod'):
        return 'paddle'
    if base in ('actuator body', 'actuator motor and gearbox'):
        return 'body'
    if base in ('actuator rod', 'rod end eye'):
        return 'rod'
    if name == 'mitre seal' or any(base == nm for nm, k, t in leaf_instances(-1)):
        return 'leaf'
    return 'fixed'


# ------------------------------------------------------------------ single leaf, for the detail drawing
def leaf_items():
    return [(nm, key, tf(shape(key))) for nm, key, tf in leaf_instances(-1)]


def gate_leaf():
    """One gate leaf (the left hand leaf) on its own: the welded frame (heel post, mitre post, eight girders, two
    stiffeners, skin plate, actuator bracket, lifting lugs, paddle culvert) with its oak fenders, walkway, handrail,
    seals, bush and gate paddle. Drawn in its own coordinates: X along the leaf from the heel pivot, Y towards the
    chamber face."""
    return [(nm, s, colour(k)) for nm, k, s in leaf_items() if k != 'pivot_pin']


def leaf_frame():
    """The welded frame of one leaf as one solid (for calculations)."""
    return union(*[s for nm, k, s in leaf_items() if PART[k]['group'] == 'frame'])


def leaf_mass():
    """Mass of one leaf with everything that turns with it (kg) and the distance of its centre of gravity from the pivot."""
    m = mx = 0
    for nm, k, s in leaf_items():
        if k == 'pivot_pin':
            continue
        v = s.val().Volume() * 1e-9 * PART[k]['density']
        m += v
        mx += v * s.val().Center().x
    return m, mx / m


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


# ------------------------------------------------------------------ parts list
def bom(names):
    """Parts list rows for the instances in names: item number, part, quantity, material, model and instance names."""
    rows = {}
    keys = instance_keys(lambda: ga_instances(0))
    keys.update(instance_keys(leaf_items))
    for n in names:
        k = keys[n]
        rows.setdefault(k, []).append(n)
    out = []
    for p in PARTS:
        if p['key'] in rows:
            out.append(dict(no=p['no'], name=p['name'], qty=len(rows[p['key']]), material=p['material'],
                            group=p['group'], model=part_model_name(p), file=p['file'], bought=p['bought'],
                            instances=rows[p['key']]))
    return out


def part_model_name(p):
    return 'esp2023_p%02d_%s' % (p['no'], p['key'])


def _part_fn(p):
    def fn():
        return [(p['name'], part_shape(p['key']), p['colour'])]
    fn.__doc__ = p['desc']
    return fn


def _ga_bom():
    return bom([n for n, s, c in lock_gates(0)])


def _leaf_bom():
    return bom([n for n, s, c in gate_leaf()])


GA_HIDE = ['%s cover panel %d' % (n, k) for n in ('left', 'right') for k in (1, 2, 3)]

MODELS = [
    dict(name='esp2023_lock_gates', title='ESP 2023 lock gates (GA)', fn=lock_gates, criteria='3.1, 3.2',
         uses='ESP 2023 Task 2, Part B: the preferred design, a pair of mitre gates assembled from %d separate parts. '
              'General arrangement, parts list, simulation of the gates opening.' % len(PARTS),
         section=None, explode=None, iso=(-1, -1.3, 0.9), folder='ESP 2023', sim=True, fea=False, bom=_ga_bom,
         hide=GA_HIDE),
    dict(name='esp2023_gate_leaf', title='ESP 2023 gate leaf', fn=gate_leaf, criteria='3.1, 3.2',
         uses='ESP 2023 Task 2: one leaf assembled from its parts: welded frame, fenders, walkway, seals, paddle. '
              'Detail drawing and section A-A through the girders.',
         section='y', explode=None, iso=(-1, -1, 0.8), folder='ESP 2023', bom=_leaf_bom),
    dict(name='esp2023_skin_panel', title='ESP 2023 skin plate panel', fn=skin_panel, criteria='3.2',
         uses='ESP 2023 Task 2: the skin plate panel that takes the highest water pressure. FEA with hydrostatic '
              'pressure, checked by hand.',
         section=None, explode=None, iso=(-1, 1, 0.8), folder='ESP 2023'),
    dict(name='esp2023_lift_gate', title='ESP 2023 concept B: lift gate', fn=lift_gate, criteria='3.1',
         uses='ESP 2023 Task 2, Part A: the second design idea, a vertical lift gate, for comparison with the '
              'mitre gates.',
         section=None, explode=None, folder='ESP 2023', fea=False),
]

for _p in PARTS:
    MODELS.append(dict(
        name=part_model_name(_p), title='ESP 2023 part %02d: %s' % (_p['no'], _p['name']), fn=_part_fn(_p),
        criteria='3.1', uses='ESP 2023 component, item %d on the parts list: %s. %s' % (_p['no'], _p['material'], _p['desc']),
        description=_p['desc'], section=None, explode=None, folder='ESP 2023', part=dict(no=_p['no'], key=_p['key'],
        group=_p['group'], material=_p['material'], file=_p['file'], bought=_p['bought']),
        fea=None if _p['key'] == 'bottom_pintle' else False, media='still'))


# ------------------------------------------------------------------ key sizes for each part drawing
SIZES = dict(
    heel_post=['Section: R225 round back + 400 x 450 box', 'Height 5800 (50 to 5850 above the cill)',
               '25 plate; solid bearing block bottom 300', 'Bush bore Ø190 x 250 deep', 'Top journal Ø200 x 150'],
    mitre_post=['Box 700 x 450 before trimming, 5910 high', '25 plate, hollow 75 to 5935 high',
                'Mitre end cut at 1 in 3 (18.43°)'],
    girder=['Length 1760 between the posts', 'Web 418 x 20, flange 200 x 20', '2 slots 15 wide x 209 deep at 580 and 1165'],
    stiffener=['Plate 418 x 15 x 5910 high', '8 slots 20 x 209 at the girder levels',
               'Girder levels ' + ', '.join(str(z) for z in GIRDERS)],
    skin_plate=['Plate 1760 x 5910 x 12', 'Paddle opening 400 x 400, 1270 from the heel end, 875 up from its base'],
    actuator_bracket=['Base plate 160 x 160 x 20', 'Lug 100 wide x 35, R50 end, 150 out', 'Pin hole Ø40',
                      'Gusset 100 x 80 x 20'],
    lifting_lug=['Plate 160 x 200 x 30, R80 top', 'Shackle hole Ø60, 120 up'],
    paddle_culvert=['Box 430 x 430 outside, 400 x 400 inside', 'Length 438 (through the leaf)', '15 plate'],
    oak_fender=['Timber 1610 x 200 x 150', 'Long edges R20', 'Fender levels 2600, 3500, 4400'],
    walkway_grating=['Panel 1760 x 450 x 40', '6 drainage slots 1600 x 30 at 50 pitch'],
    handrail=['Tube Ø48.3, 3 posts 1100 high at 780 centres', 'Rails at 550 and 1076 above the walkway, 1608 long'],
    cill_seal=['Strip 85 x 50, 2460 long', 'Mitre end cut at 1 in 3'],
    heel_seal=['Strip 30 x 80 x 5800 long'],
    mitre_seal=['30 thick across the mitre, 84 wide on the slope', '5910 high'],
    pintle_bush=['Ø190 outside x 250 long', 'Bore Ø150 x 230 deep (cup)'],
    paddle_door=['Plate 500 x 500 x 20', 'Rod lug 50 x 80 x 75 on the top edge'],
    paddle_guide=['Angle 40 x 20 with a 60 x 20 lip', 'Length 1300'],
    paddle_rod=['Bar Ø30 x 4425 long'],
    paddle_actuator=['Body Ø90 x 1200, bore Ø40', 'Motor 80 x 80 x 150', 'Bracket plate 100 x 200 x 20', 'Stroke 500'],
    bottom_pintle=['Base plate 600 x 600 x 80', 'Pin Ø150 x 280 high', 'Root fillet R15, top R10',
                   '4 holes Ø26 on a 450 square'],
    anchor_bolt=['M24 stud, 410 long', 'Hex nut M24 (36 A/F x 24)'],
    anchor_collar=['Collar Ø360 x 100, bore Ø240', 'Arm 730 x 120 x 100, to 900 from the pivot'],
    collar_bush=['Ø240 outside, Ø200 bore, 100 long'],
    anchor_plate=['Plate 300 x 200 x 25', '2 holes Ø26 at 200 centres'],
    encoder_bracket=['Upright 30 x 80 x 160', 'Top plate 350 x 80 x 20'],
    position_encoder=['Body Ø100 x 90', 'Shaft Ø20 x 20'],
    actuator_body=['Tube Ø140 x 1830', 'Bore Ø80 x 1780', 'Rear eye 80 thick, R50, hole Ø40', 'Pivot to tube end 1900'],
    actuator_motor=['Block 450 x 150 x 195', 'Saddle R70 to suit the tube'],
    actuator_rod=['Bar Ø70 x 1490', 'Ends 110 from the rod end pin'],
    rod_end=['Eye Ø90 x 80, hole Ø40', 'Neck Ø60 x 75'],
    pivot_pedestal=['Base Ø190 x 20', 'Boss Ø100 x 35', 'Pin hole Ø40'],
    pivot_pin=['Pin Ø40 x 105', 'Head Ø60 x 15'],
    inspection_chamber=['Outside 2350 x 1800 x 1000 deep', 'Walls and floor 150', 'Rod slot 1500 wide x 450 deep',
                        'Cover rebate 75 wide x 50 deep on the long walls'],
    actuator_plinth=['Ø300 x 550 high', 'Trimmed flat where it is cast against the end wall'],
    cover_panel=['Panel 682 x 1650 x 50', '2 lifting holes Ø30, 225 in from the ends'],
    control_panel=['Enclosure 400 wide x 500 high x 150 deep', 'Handle 30 x 100 x 15'],
    cctv_mast=['Base plate 150 x 150 x 20', 'Tube Ø120 x 2980'],
    cctv_camera=['Camera 300 x 150 x 150', 'Bracket 80 x 150 x 120'],
    call_point_post=['Box section 150 x 150 x 1200 high'],
    call_point=['Box 220 x 250 x 85', 'Stop button Ø60'],
    cill=['5500 x 2100 x 600 deep', '2 pintle pockets 600 x 600 x 80 deep at ±%.0f' % PIV,
          '8 anchor holes Ø28 x 400 deep'],
)
for _p in PARTS:
    _p['sizes'] = SIZES[_p['key']]
for _m in MODELS:
    if _m.get('part'):
        _m['part']['sizes'] = PART[_m['part']['key']]['sizes']
