"""ESP 2024: a harbour lane marker buoy for Harbour Shipping Ltd, designed by Oceans Technology Ltd (T Level
Employer-Set Project 8730-035, Summer 2024, Task 2).

The brief (product design specification): a buoy 1400 to 1800 mm high above the sea with a base diameter of 500 mm
(tolerance 25); standard fixings; green for buoys entering the harbour and red for buoys leaving; an alert if the
mooring cable breaks; a tracking system to find the buoy if it drifts away; a renewable power source giving 12 V
for these systems; a secure, watertight and easily reached place for the battery and electrics; materials that do
not rust or corrode; a modern, visible shape; able to take minor impacts; used in a harbour; 2000 pounds a buoy
(100 buoys, 200,000 pounds, 2 a week, 70 weeks).

Design A (preferred): a foam filled polyethylene float, 500 diameter, with a rubber fender in a groove round its
waist, a stainless steel tripod mast carrying three 20 W solar panels (one faces the sun whichever way the buoy
turns), an LED lantern, and a polyethylene topmark (a can for red, a cone for green) with the GNSS and mobile
antenna inside it. A lockable stainless steel canister in the middle of the float holds the battery and the control
unit (charger, GNSS tracker and alert). Under the float a stainless tail tube carries the ballast, a zinc anode and
the mooring eye; the mooring shackle pin is a load pin, so the control unit knows at once if the chain breaks.
Design B (concept only): a spherical float with a lattice tower and a small wind turbine (see wind_buoy()).

Every component is its own part (an Inventor .ipt), listed in PARTS below with its material and the features that
make it (the Inventor build steps). The sub-assemblies and the buoy are assemblies (.iam) of those parts.

Coordinates (mm): z = 0 is the design waterline, Z up, the buoy axis is x = y = 0. The front view looks along +Y.
The tripod legs stand at 90, 210 and 330 degrees (measured from +X towards +Y), so a solar panel faces the front.
"""
import functools
import math
import cadquery as cq

# ------------------------------------------------------------------ the numbers that define the design
FLOAT_R = 250                   # float radius: base diameter 500 (brief: 500 +- 25)
FLOAT_TOP, FLOAT_BOT = 250, -770  # float deck and bottom, from the design waterline
WALL = 6                        # rotomoulded polyethylene wall
FILLET_TOP, FILLET_BOT = 30, 50
GROOVE = (238, FLOAT_TOP - 110, FLOAT_TOP - 30)   # fender groove: radius, from z, to z
FENDER_R = 262                  # fender outside radius: 524 over the fender (brief: 525 max)
WELL_R = 145                    # equipment well in the middle of the float
WELL_BOT = FLOAT_TOP - 480      # floor of the well (inside)
DECK = (FLOAT_TOP, FLOAT_TOP + 6)   # deck plate z
DECK_R = 235
KEEL = (FLOAT_BOT - 10, FLOAT_BOT)   # keel plate z
KEEL_R = 210
TIE_R, TIE_ANG = 195, (30, 150, 270)  # tie rods: radius, angles
CAN_R, CAN_T = 142, 1.5         # equipment canister outside radius and wall
FLANGE = (DECK[1], DECK[1] + 8, 172)   # canister flange z0, z1, radius
LID_T = 8
LID = (FLANGE[1], FLANGE[1] + LID_T)
BOLT_PCD_R, N_BOLTS = 158, 8
SEAL_R = 148
M = DECK[1]                     # mast heights are measured from the top of the deck plate
LEG_ANG = (90, 210, 330)        # tripod legs
LEG_FOOT = (205, M + 10)        # leg foot centre: radius, top of the foot plate
LEG_TOP = (70, M + 914)         # leg top centre: radius, z (underside of the top plate)
LEG_OR, LEG_IR = 16.85, 14.85   # 33.7 x 2 tube
TOP_PLATE = (LEG_TOP[1], LEG_TOP[1] + 8, 110)
PANEL_ANG = (270, 30, 150)      # panel normals
PANEL = (118, 20, 300, M + 144, M + 544)  # back face distance from the axis, thickness, width, z0, z1
BRACKETS = (M + 214, M + 474)   # bracket centre heights
STRUT_ANG = (30, 150, 270)
TM_PLATE = (TOP_PLATE[1] + 232, TOP_PLATE[1] + 238, 125)
STRUT = (95, 6, 30, TOP_PLATE[1], TM_PLATE[0])   # radius, thickness, width, z0, z1
CAN_TM = (100, 5, TM_PLATE[1], TM_PLATE[1] + 260)   # topmark can radius, wall, z0, z1
CONE_TM = (125, 5, TM_PLATE[1], TM_PLATE[1] + 280)  # topmark cone base radius, wall, z0, apex
TAIL_R, TAIL_T = 44.45, 3.0     # tail tube 88.9 x 3
TAIL_FLANGE = (KEEL[0] - 12, KEEL[0], 100)
TAIL_BOT = -1650                # top of the tail bottom plate
BOT_PLATE = (TAIL_BOT - 10, TAIL_BOT, 160)
BALLAST = (46, 160, 260)        # ballast ring inside radius, outside radius, height
ANODE = (KEEL[0] - 300, KEEL[0] - 240, 66)   # zinc collar anode z0, z1, outside radius
EYE_T = 20                      # mooring eye plate thickness
PIN_R = 14                      # load pin 28 diameter
PIN_Z = BOT_PLATE[0] - 55       # load pin axis
CHAIN_D = 10                    # mooring chain wire diameter
CHAIN_LINKS = 4                 # links drawn on the buoy (the chain continues to the sinker)

# colours
RED = 'C8372D'
GREEN = '2E8B4A'
FOAM_C = 'E8D9A8'
STEEL_C = 'A9B4BF'      # 316L stainless
DARK = '2B2B2B'
RUBBER = '3A3A3A'
YELLOW = 'E8C23D'
PV_C = '1F2F5A'
ZINC_C = '9AA3AD'
GALV = '7F8A94'
CONCRETE = 'B8B3A8'
WHITE = 'EDEDED'
HDPE_C = 'D9DEE3'
ORANGE = 'E8A33D'

# Inventor commands
NEW_PART = 'File > New > Standard (mm).ipt'
SKETCH = '3D Model tab > Sketch panel > Start 2D Sketch'
EXTRUDE = '3D Model tab > Create panel > Extrude'
REVOLVE = '3D Model tab > Create panel > Revolve'
SWEEP = '3D Model tab > Create panel > Sweep'
HOLE = '3D Model tab > Modify panel > Hole'
FILLET = '3D Model tab > Modify panel > Fillet'
SHELL = '3D Model tab > Modify panel > Shell'
COMBINE = '3D Model tab > Modify panel > Combine'
CIRC_PATTERN = '3D Model tab > Pattern panel > Circular Pattern'
MIRROR_F = '3D Model tab > Pattern panel > Mirror'
NEW_ASSY = 'File > New > Standard (mm).iam'
PLACE = 'Assemble tab > Component panel > Place'
CONTENT = 'Assemble tab > Component panel > Place from Content Center'
CONSTRAIN = 'Assemble tab > Relationships panel > Constrain'
PATTERN = 'Assemble tab > Pattern panel > Pattern'

# densities, kg/m3 (a bought in part has the density that gives its catalogue mass)
MDPE_D = 950          # rotomoulded UV stabilised polyethylene
FOAM_D = 40           # closed cell polyurethane foam
EVA_D = 300           # closed cell EVA foam fender with a rubber skin
SS_D = 8000           # 316L stainless steel
HDPE_D = 960
EPDM_D = 1150
PA_D = 1150           # nylon cable gland
ZINC_D = 7140
GALV_D = 7850
CONC_D = 2400         # sinker concrete
BALLAST_D = 3400      # heavy (barytes) concrete in a polyethylene skin
SW_D = 1025           # sea water
CHAIN_KG_M = 2.2      # kg a metre of 10 mm chain in air
WATER_DEPTH = 5.0     # m, design depth of water at the buoy (harbour lane, high water)
CHAIN_LOAD = CHAIN_KG_M * (1 - SW_D / GALV_D) * WATER_DEPTH   # kg: weight in water of the chain hanging from the buoy


# ------------------------------------------------------------------ shape helpers
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, p0, d, h):
    """A cylinder of radius r from point p0, length h along the direction d."""
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r, h, cq.Vector(*p0), cq.Vector(*d)))


def zcyl(r, z0, z1, x=0, y=0):
    return cyl(r, (x, y, z0), (0, 0, 1), z1 - z0)


def xcyl(r, x0, x1, y=0, z=0):
    return cyl(r, (x0, y, z), (1, 0, 0), x1 - x0)


def ring(r0, r1, z0, z1, x=0, y=0):
    out = zcyl(r1, z0, z1, x, y)
    return out.cut(zcyl(r0, z0 - 1, z1 + 1, x, y)) if r0 > 0 else out


def torus(R, r, c, d):
    return cq.Workplane('XY').add(cq.Solid.makeTorus(R, r, cq.Vector(*c), cq.Vector(*d)))


def polar(r, a, z=0):
    a = math.radians(a)
    return (r * math.cos(a), r * math.sin(a), z)


def rotz(w, a):
    return w.rotate((0, 0, 0), (0, 0, 1), a)


def union(*shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.union(s)
    return out


def F(title, command, actions, shape, note=None):
    """One feature of a part: what you do in Inventor and the part as it stands afterwards."""
    return dict(title=title, command=command, actions=actions, shape=shape, note=note)


def leg_r(z):
    """Distance of a tripod leg centre line from the buoy axis at height z."""
    (r0, z0), (r1, z1) = LEG_FOOT, LEG_TOP
    return r0 + (r1 - r0) * (z - z0) / (z1 - z0)


def leg_solid(a=0, r=LEG_OR):
    """The full round of a tripod leg at angle a, extended past both ends (for cutting)."""
    (r0, z0), (r1, z1) = LEG_FOOT, LEG_TOP
    p0, p1 = polar(r0, a, z0), polar(r1, a, z1)
    d = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in d))
    u = [v / L for v in d]
    start = [p0[i] - u[i] * 60 for i in range(3)]
    return cyl(r, start, u, L + 120)


# ------------------------------------------------------------------ the parts
PARTS = []
GROUPS = [('float', 'Float and deck (SA1)'), ('equipment', 'Equipment canister: battery, control and tracking (SA2)'),
          ('tail', 'Tail tube, ballast and anode (SA3)'), ('mast', 'Tripod mast and solar panels (SA4)'),
          ('top', 'Lantern and topmark (SA5)'), ('mooring', 'Mooring, alert load pin and chain (SA6, SA7)')]


def part(key, name, group, material, colour, density, desc, origin=(0, 0, 0), file=None, bought=False, sustainable=False):
    def deco(fn):
        PARTS.append(dict(key=key, name=name, group=group, material=material, colour=colour, density=density,
                          desc=desc, origin=origin, feats=fn, file=file or key + '.ipt', bought=bought,
                          sustainable=sustainable))
        return fn
    return deco


# ---------------------------------------------------- SA1 float and deck
def float_outer(round_edges=True):
    w = zcyl(FLOAT_R, FLOAT_BOT, FLOAT_TOP)
    if not round_edges:
        return w
    w = w.faces('>Z').edges().fillet(FILLET_TOP)
    w = w.faces('<Z').edges().fillet(FILLET_BOT)
    return w


def float_cavity():
    """The space inside the polyethylene wall, round the equipment well: it is filled with foam."""
    t = WALL
    w = zcyl(FLOAT_R - t, FLOAT_BOT + t, FLOAT_TOP - t)
    w = w.faces('>Z').edges().fillet(FILLET_TOP - t)
    w = w.faces('<Z').edges().fillet(FILLET_BOT - t)
    g, z0, z1 = GROOVE
    w = w.cut(ring(g - t, FLOAT_R, z0 - t, z1 + t))
    w = w.cut(zcyl(WELL_R + t, WELL_BOT - t, FLOAT_TOP + 1))
    return w


def tie_holes(r=8):
    return union(*[zcyl(r, FLOAT_BOT - 50, FLOAT_TOP + 50, *polar(TIE_R, a)[:2]) for a in TIE_ANG])


@part('float_hull', 'float hull', 'float', 'Rotomoulded MDPE, UV stabilised, red or green all through, 6 wall', RED, MDPE_D,
      'The float: a 500 diameter polyethylene shell, moulded in one piece with the equipment well in the middle and a '
      'groove for the fender. The colour goes all the way through, so a scrape never shows bare material; it cannot rust.',
      origin=(0, 0, FLOAT_BOT))
def _float_hull():
    f0, f1 = float_outer(False), float_outer()
    g, z0, z1 = GROOVE
    f2 = f1.cut(ring(g, FLOAT_R + 1, z0, z1))
    f3 = f2.cut(zcyl(WELL_R, WELL_BOT, FLOAT_TOP + 1))
    f4 = f3.cut(float_cavity())
    f5 = f4.cut(tie_holes())
    return [
        F('Revolve the float', EXTRUDE,
          [NEW_PART + ' and save it as float_hull.ipt.',
           'Start 2D Sketch on the XZ Plane (the floor). Circle diameter 500 on the origin. Finish Sketch.',
           'Extrude %d mm up. The origin is the bottom of the float; the design waterline is %d mm up.'
           % (FLOAT_TOP - FLOAT_BOT, -FLOAT_BOT)], f0, None),
        F('Round the top and bottom edges', FILLET,
          ['Fillet the top edge radius %d and the bottom edge radius %d. Click OK.' % (FILLET_TOP, FILLET_BOT)], f1,
          'Round edges shed waves and are kind to boats that touch the buoy.'),
        F('Fender groove', REVOLVE,
          ['Start 2D Sketch on the XY Plane. Rectangle %d deep by %d high on the outside edge, from %d to %d mm up.'
           % (FLOAT_R - GROOVE[0], GROOVE[2] - GROOVE[1], GROOVE[1] - FLOAT_BOT, GROOVE[2] - FLOAT_BOT),
           'Revolve it 360 degrees about the Y axis, Cut.'], f2, 'The rubber fender sits in this groove.'),
        F('Equipment well', HOLE,
          ['Hole on the top face, on the centre: diameter %d, depth %d. Click OK.' % (2 * WELL_R, FLOAT_TOP - WELL_BOT)], f3,
          'The well holds the stainless equipment canister (sub-assembly 2).'),
        F('Hollow it', SHELL,
          ['Click Shell. Thickness %d mm, Inside, no faces removed (a closed shell). Click OK.' % WALL], f4,
          'Rotomoulding makes a hollow part with an even wall. The space is then filled with foam (part 2).'),
        F('Tie rod holes', HOLE,
          ['Hole: diameter 16, Through All, at radius 195 on 30, 150 and 270 degrees (Circular Pattern of 3).',
           'Material: Polyethylene, red (green for an entrance buoy). Save.'], f5,
          'Three stainless tie rods clamp the deck plate and the keel plate to the float.'),
    ]


@part('float_foam', 'float foam fill', 'float', 'Closed cell polyurethane foam, 40 kg/m3', FOAM_C, FOAM_D,
      'Foam that fills the float. If the shell is ever holed by an impact, the float cannot fill with water: the buoy '
      'stays afloat and upright.', origin=(0, 0, FLOAT_BOT + WALL))
def _float_foam():
    f1 = float_cavity()
    f2 = f1.cut(tie_holes())
    return [F('The space inside the shell', REVOLVE,
              [NEW_PART + ' and save it as float_foam.ipt.',
               'Derive the cavity of float_hull.ipt: Manage tab > Derive, pick the inside of the shell. (Or revolve '
               'the inside profile: %d diameter, %d high, round the well of diameter %d.)'
               % (2 * (FLOAT_R - WALL), FLOAT_TOP - FLOAT_BOT - 2 * WALL, 2 * (WELL_R + WALL))], f1,
              'The foam is poured in liquid through a filling hole and expands to fill the shell.'),
            F('Tie rod holes', HOLE, ['Hole: diameter 16 Through All at radius 195, Circular Pattern of 3. Save.'], f2)]


@part('fender', 'fender ring', 'float', 'Closed cell EVA foam with a black rubber skin', RUBBER, EVA_D,
      'Soft fender in the groove round the float. Boats that bump the buoy hit this first: it takes minor impacts and '
      'protects the float and the boat. 524 over the fender (brief: 500 +- 25).', origin=(0, 0, GROOVE[1]))
def _fender():
    g, z0, z1 = GROOVE
    f1 = ring(g, FENDER_R, z0, z1)
    f2 = f1.faces('>Z').edges(cq.selectors.RadiusNthSelector(1)).fillet(12)
    f2 = f2.faces('<Z').edges(cq.selectors.RadiusNthSelector(1)).fillet(12)
    return [F('Ring', EXTRUDE, [NEW_PART + ' and save it as fender.ipt.',
                                'Sketch circles diameter %d and %d on the XZ Plane. Extrude %d mm.'
                                % (2 * GROOVE[0], 2 * FENDER_R, GROOVE[2] - GROOVE[1])], f1),
            F('Round the outside edges', FILLET, ['Fillet the two outside edges, radius 12. Save.'], f2,
              'It is stretched over the float and sits in the groove: no fixings to work loose.')]


@part('deck_plate', 'deck plate', 'float', '316L stainless steel plate, 6 thick', STEEL_C, SS_D,
      'Ring plate on top of the float. The tripod legs bolt to it, the canister flange sits on it and the tie rods '
      'clamp it down. It spreads the loads from the mast over the float.', origin=(0, 0, DECK[0]))
def _deck_plate():
    f1 = ring(143, DECK_R, *DECK)
    f2 = f1.cut(tie_holes())
    holes = [zcyl(6, DECK[0] - 1, DECK[1] + 1, *rotz_xy((LEG_FOOT[0], s * 34), a)) for a in LEG_ANG for s in (-1, 1)]
    f3 = f2.cut(union(*holes))
    return [F('Ring', EXTRUDE, [NEW_PART + ' and save it as deck_plate.ipt.',
                                'Sketch circles diameter 470 and 286 on the XZ Plane. Extrude 6 mm.'], f1),
            F('Tie rod holes', HOLE, ['Hole diameter 16 Through All at radius 195 on 30 degrees; Circular Pattern 3.'], f2),
            F('Leg bolt holes', HOLE, ['Hole M12 tapped, Through All, at radius 205, 34 mm either side of 90 degrees.',
                                       'Circular Pattern: 3 at 120 degrees. Save.'], f3,
              'Two M12 bolts hold each leg foot.')]


def rotz_xy(p, a):
    a = math.radians(a)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


@part('keel_plate', 'keel plate', 'float', '316L stainless steel plate, 10 thick', STEEL_C, SS_D,
      'Plate under the float. The tie rods pull it up against the float and the tail tube bolts to it, so the weight '
      'of the ballast and the pull of the mooring go into the whole float.', origin=(0, 0, KEEL[0]))
def _keel_plate():
    f1b = zcyl(KEEL_R, *KEEL)
    f2 = f1b.cut(tie_holes())
    f3 = f2.cut(union(*[zcyl(6, KEEL[0] - 1, KEEL[1] - 2, *polar(75, a)[:2]) for a in range(0, 360, 60)]))
    return [F('Disc', EXTRUDE, [NEW_PART + ' and save it as keel_plate.ipt.',
                                'Sketch a circle diameter 420 on the XZ Plane. Extrude 10 mm.'], f1b),
            F('Tie rod holes', HOLE, ['Hole diameter 16 Through All at radius 195 on 30 degrees; Circular Pattern 3.'], f2),
            F('Tail flange holes', HOLE, ['Hole M12 tapped, 8 deep from the bottom, at radius 75; Circular Pattern 6. Save.'], f3,
              'Blind holes, so no water path into the float.')]


@part('tie_rod', 'tie rod', 'float', 'A4 (316) stainless threaded rod M16', STEEL_C, SS_D,
      'One of three M16 rods through the float from the keel plate to the deck plate.',
      origin=polar(TIE_R, 30, KEEL[0] - 15), bought=True)
def _tie_rod():
    x, y, _ = polar(TIE_R, 30)
    f1 = zcyl(8, KEEL[0] - 15, DECK[1] + 14, x, y)
    return [F('Rod', EXTRUDE, ['Place from Content Center (threaded rod M16), or ' + NEW_PART + ': circle diameter 16, '
                                'Extrude %d mm. Save.' % (DECK[1] + 14 - KEEL[0] + 15)], f1, 'Threads shown at the major diameter, as Inventor shows a cosmetic thread.')]


@part('tie_rod_nut', 'tie rod nut M16', 'float', 'A4 (316) stainless hex nut M16, ISO 4032', STEEL_C, SS_D,
      'Standard nut on the bottom end of each tie rod, under the keel plate.', origin=polar(TIE_R, 30, KEEL[0] - 13), bought=True)
def _tie_rod_nut():
    x, y, _ = polar(TIE_R, 30)
    f1 = cq.Workplane('XY').polygon(6, 27.7).extrude(13).translate((x, y, KEEL[0] - 13))
    f2 = f1.cut(zcyl(8, KEEL[0] - 14, KEEL[0] + 1, x, y))
    return [F('Hexagon', EXTRUDE, ['Place from Content Center: ISO 4032 M16, or sketch a hexagon 24 across flats, Extrude 13.'], f1),
            F('Thread', HOLE, ['Hole M16 Through All on the centre. Save.'], f2)]


EYE_RING = (23, 6.5)            # eye nut ring: centre line radius, section radius


@part('eye_nut', 'lifting eye nut M16', 'float', 'A4 (316) stainless lifting eye nut M16, DIN 582', STEEL_C, SS_D,
      'Eye nut on the top of each tie rod. It clamps the deck plate, and the three eyes are the lifting points used to '
      'lift the buoy out of the water for servicing.', origin=polar(TIE_R, 30, DECK[1]), bought=True)
def _eye_nut():
    x, y, _ = polar(TIE_R, 30)
    R, r = EYE_RING
    f1 = zcyl(17, DECK[1], DECK[1] + 15, x, y)
    d = polar(1, 30 + 90)
    f2 = f1.union(torus(R, r, (x, y, DECK[1] + 15 + R + r - 4), d))
    f3 = f2.cut(zcyl(8, DECK[1] - 1, DECK[1] + 15, x, y))
    return [F('Collar', EXTRUDE, ['Place from Content Center (DIN 582 M16), or ' + NEW_PART + ': circle diameter 34, Extrude 15.'], f1),
            F('Eye', SWEEP, ['Sketch a circle diameter 13 and sweep it round a circle radius 23 standing on the collar.'], f2),
            F('Thread', HOLE, ['Hole M16, 15 deep, up the middle. Save.'], f3, 'Safe working load 700 kg each.')]


# ---------------------------------------------------- SA2 equipment canister
@part('canister', 'equipment canister', 'equipment', '316L stainless steel, 1.5 wall, welded', STEEL_C, SS_D,
      'Watertight stainless canister in the float well: it holds the battery and the control unit. Its flange sits on '
      'the deck plate and the hatch lid bolts to it.', origin=(0, 0, WELL_BOT))
def _canister():
    z0, z1 = WELL_BOT, FLANGE[0]
    f1 = zcyl(CAN_R, z0, z1)
    f2 = f1.cut(zcyl(CAN_R - CAN_T, z0 + 4, z1 + 1))
    f3 = f2.union(ring(CAN_R - CAN_T, FLANGE[2], FLANGE[0], FLANGE[1]))
    f4 = f3.cut(union(*[zcyl(5, FLANGE[0] - 1, FLANGE[1] + 1, *polar(BOLT_PCD_R, a)[:2]) for a in range(0, 360, 45)]))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as canister.ipt.',
                                'Sketch a circle diameter %d on the XZ Plane. Extrude %d mm.' % (2 * CAN_R, FLANGE[0] - WELL_BOT)], f1),
            F('Hollow it', SHELL, ['Shell: remove the top face, thickness %g mm (the bottom is 4 mm). Click OK.' % CAN_T], f2),
            F('Flange', EXTRUDE, ['Sketch circles diameter %d and %d on the top face. Extrude 8 mm, Join.'
                                  % (2 * (CAN_R - CAN_T), 2 * FLANGE[2])], f3,
              'The flange is welded on all round, so the canister is watertight.'),
            F('Lid bolt holes', HOLE, ['Hole M10 tapped Through All at radius 158; Circular Pattern 8. Save.'], f4)]


@part('mounting_plate', 'equipment mounting plate', 'equipment', 'HDPE sheet, 8 thick', HDPE_C, HDPE_D,
      'Plastic plate on the floor of the canister. The battery and control unit are screwed to it, and it lifts out '
      'in one piece for servicing.', origin=(0, 0, WELL_BOT + 4))
def _mounting_plate():
    z = WELL_BOT + 4
    f1 = zcyl(136, z, z + 8)
    f2 = f1.cut(box(-40, 40, 92, 112, z - 1, z + 9))
    return [F('Disc', EXTRUDE, [NEW_PART + ' and save it as mounting_plate.ipt.', 'Circle diameter 272. Extrude 8 mm.'], f1),
            F('Finger slot', EXTRUDE, ['Sketch an 80 x 20 slot near the edge. Extrude Cut Through All. Save.'], f2,
              'Lift the plate out by the slot.')]


EQ_Z = WELL_BOT + 12    # top of the mounting plate


@part('battery', 'battery 12.8 V 40 Ah', 'equipment', 'Bought in: LiFePO4 battery 12.8 V 40 Ah, 512 Wh, IP67', DARK, 1450,
      'The battery: lithium iron phosphate, safe in a sealed canister, 2000 or more full cycles, 512 Wh. It runs the '
      'lantern, tracker and alert for about two weeks with no sun.', origin=(0, -95, EQ_Z), bought=True)
def _battery():
    f1 = box(-97, 97, -95, -18, EQ_Z, EQ_Z + 170)
    f2 = f1.union(zcyl(7, EQ_Z + 170, EQ_Z + 178, -60, -56)).union(zcyl(7, EQ_Z + 170, EQ_Z + 178, 60, -56))
    return [F('Case', EXTRUDE, [NEW_PART + ' and save it as battery.ipt.', 'Sketch a 194 x 77 rectangle. Extrude 170 mm.'], f1,
              'Modelled from the maker\'s outline drawing.'),
            F('Terminals', EXTRUDE, ['Sketch two circles diameter 14, 120 apart. Extrude 8 mm. Save.'], f2)]


@part('battery_strap', 'battery strap', 'equipment', '316L stainless strip 25 x 3', STEEL_C, SS_D,
      'Strap over the battery, screwed to the mounting plate, so the battery cannot move as the buoy rolls.',
      origin=(0, -98, EQ_Z))
def _battery_strap():
    z1 = EQ_Z + 170
    f1 = box(-12.5, 12.5, -98, -15, z1, z1 + 3)
    f2 = f1.union(box(-12.5, 12.5, -98, -95, EQ_Z, z1)).union(box(-12.5, 12.5, -18, -15, EQ_Z, z1))
    return [F('Top', EXTRUDE, [NEW_PART + ' and save it as battery_strap.ipt.', 'Sketch a 25 x 83 rectangle. Extrude 3 mm.'], f1),
            F('Legs', EXTRUDE, ['Sketch the two legs on the end faces, 170 long. Extrude 3 mm, Join. Save.'], f2,
              'In sheet metal: Flange the two ends down.')]


@part('control_unit', 'control and tracking unit', 'equipment',
      'Bought in: IP67 box with 12 V MPPT solar charger, GNSS tracker and LTE-M modem, alert logic', ORANGE, 550,
      'The electronics: charges the battery from the panels, switches the lantern at dusk, reports the buoy\'s '
      'position every hour, and raises the alert at once if the load pin shows the chain has broken or the buoy '
      'leaves its watch circle.', origin=(0, 10, EQ_Z), bought=True)
def _control_unit():
    f1 = box(-100, 100, 10, 85, EQ_Z, EQ_Z + 200)
    f2 = f1.union(box(-80, 80, 85, 90, EQ_Z + 30, EQ_Z + 170))
    return [F('Box', EXTRUDE, [NEW_PART + ' and save it as control_unit.ipt.', 'Sketch a 200 x 75 rectangle. Extrude 200 mm.'], f1),
            F('Heat sink', EXTRUDE, ['Sketch a 160 x 140 rectangle on the back face. Extrude 5 mm, Join. Save.'], f2,
              'Modelled from the maker\'s outline drawing.')]


@part('hatch_seal', 'hatch O-ring', 'equipment', 'EPDM O-ring, 5 section, 296 inside diameter', RUBBER, EPDM_D,
      'O-ring between the hatch lid and the canister flange: it keeps the canister watertight (IP68).',
      origin=(0, 0, FLANGE[1]), bought=True)
def _hatch_seal():
    f1 = torus(SEAL_R, 2.5, (0, 0, FLANGE[1] + 2.5), (0, 0, 1))
    return [F('Ring', SWEEP, ['Place from Content Center (O-ring), or ' + NEW_PART + ': sketch a circle diameter 5 at radius '
                              '148 on the XY Plane, and Revolve it 360 degrees about the axis. Save.'], f1)]


@part('hatch_lid', 'hatch lid', 'equipment', '316L stainless steel plate, 8 thick', STEEL_C, SS_D,
      'The lid over the canister. Eight tamper proof bolts hold it down on the O-ring. Undo them and the whole battery '
      'and control unit are in reach.', origin=(0, 0, LID[0]))
def _hatch_lid():
    f1 = zcyl(FLANGE[2], *LID)
    f2 = f1.cut(ring(SEAL_R - 4, SEAL_R + 4, LID[0] - 1, LID[0] + 5))
    f3 = f2.cut(union(*[zcyl(5.5, LID[0] - 1, LID[1] + 1, *polar(BOLT_PCD_R, a)[:2]) for a in range(0, 360, 45)]))
    f4 = f3.cut(union(*[zcyl(8, LID[0] - 1, LID[1] + 1, *polar(92, a)[:2]) for a in (90, 270)]))
    return [F('Disc', EXTRUDE, [NEW_PART + ' and save it as hatch_lid.ipt.', 'Circle diameter %d. Extrude %d mm.'
                                % (2 * FLANGE[2], LID_T)], f1),
            F('O-ring groove', EXTRUDE, ['Sketch circles diameter 288 and 304 on the underside. Extrude Cut 5 mm.'], f2,
              'The groove holds the O-ring in place when the lid is lifted off.'),
            F('Bolt holes', HOLE, ['Hole diameter 11 Through All at radius 158; Circular Pattern 8.'], f3),
            F('Cable gland holes', HOLE, ['Hole M16 Through All, two at radius 92 on 90 and 270 degrees. Save.'], f4)]


@part('hatch_bolt', 'tamper proof bolt M10', 'equipment', 'A4 (316) stainless pin hex button head screw M10 x 20',
      STEEL_C, SS_D, 'Hatch lid bolt with a pin in the hex: it needs a special key, so the canister is secure.',
      origin=(BOLT_PCD_R, 0, LID[1]), bought=True)
def _hatch_bolt():
    x = BOLT_PCD_R
    f1 = zcyl(5, LID[1] - 16, LID[1], x, 0)
    f2 = f1.union(zcyl(8.5, LID[1], LID[1] + 6, x, 0))
    f3 = f2.cut(cq.Workplane('XY').polygon(6, 6.9).extrude(4).translate((x, 0, LID[1] + 2.01))).union(zcyl(1.2, LID[1] + 2, LID[1] + 5.5, x, 0))
    return [F('Shank', EXTRUDE, ['Place from Content Center (ISO 7380 M10 x 20), or circle diameter 10, Extrude 16.'], f1),
            F('Button head', EXTRUDE, ['Circle diameter 17 on the top. Extrude 6.'], f2),
            F('Pin hex socket', EXTRUDE, ['Sketch a hexagon 6 across flats. Extrude Cut 4; a pin diameter 2.4 is left in the middle. Save.'], f3,
              'Only a pin hex key fits.')]


@part('cable_gland', 'cable gland M16', 'equipment', 'Nylon IP68 cable gland M16', DARK, PA_D,
      'Where the cables from the panels, lantern and load pin pass through the lid. IP68 keeps the canister dry.',
      origin=(0, 92, LID[0]), bought=True)
def _cable_gland():
    f1 = zcyl(8, LID[0], LID[1], 0, 92)
    f2 = f1.union(cq.Workplane('XY').polygon(6, 24).extrude(16).translate((0, 92, LID[1])))
    f3 = f2.cut(zcyl(3.5, LID[0] - 1, LID[1] + 17, 0, 92))
    return [F('Thread', EXTRUDE, ['Place from Content Center, or circle diameter 16, Extrude 10.'], f1),
            F('Body', EXTRUDE, ['Hexagon 21 across flats on the top. Extrude 16.'], f2),
            F('Cable bore', HOLE, ['Hole diameter 7 Through All. Save.'], f3)]


# ---------------------------------------------------- SA3 tail tube, ballast and anode
@part('tail_tube', 'tail tube', 'tail', '316L stainless tube 88.9 x 3, flange and bottom plate welded', STEEL_C, SS_D,
      'Tube under the float. It holds the ballast low down, which keeps the buoy upright, and carries the mooring eye. '
      'Flange and bottom plate are welded on.', origin=(0, 0, TAIL_FLANGE[1]))
def _tail_tube():
    f1 = ring(TAIL_R - TAIL_T, TAIL_R, TAIL_BOT, KEEL[0])
    f2 = f1.union(ring(TAIL_R - TAIL_T, TAIL_FLANGE[2], TAIL_FLANGE[0], TAIL_FLANGE[1]))
    f3 = f2.union(zcyl(BOT_PLATE[2], BOT_PLATE[0], BOT_PLATE[1]))
    f4 = f3.cut(union(*[zcyl(6.5, TAIL_FLANGE[0] - 1, TAIL_FLANGE[1] + 1, *polar(75, a)[:2]) for a in range(0, 360, 60)]))
    return [F('Tube', EXTRUDE, [NEW_PART + ' and save it as tail_tube.ipt (a weldment).',
                                'Sketch circles diameter 88.9 and 82.9 on the XZ Plane. Extrude %d mm down.'
                                % (KEEL[0] - TAIL_BOT)], f1,
              'The origin is the top of the flange, under the keel plate.'),
            F('Flange', EXTRUDE, ['Circles diameter 82.9 and 200 on the top. Extrude 12 mm, Join.'], f2),
            F('Bottom plate', EXTRUDE, ['Circle diameter %d on the bottom. Extrude 10 mm, Join.' % (2 * BOT_PLATE[2])], f3,
              'The ballast ring sits on this plate.'),
            F('Flange holes', HOLE, ['Hole diameter 13 Through All at radius 75; Circular Pattern 6. Save.'], f4)]


@part('keel_bolt', 'hex bolt M12 x 20', 'tail', 'A4 (316) stainless hex bolt M12 x 20, ISO 4017', STEEL_C, SS_D,
      'Six standard bolts hold the tail tube flange to the keel plate.', origin=(75, 0, TAIL_FLANGE[0]), bought=True)
def _keel_bolt():
    f1 = zcyl(6, TAIL_FLANGE[0], KEEL[1] - 2, 75, 0)
    f2 = f1.union(cq.Workplane('XY').polygon(6, 20.8).extrude(8).translate((75, 0, TAIL_FLANGE[0] - 8)))
    return [F('Shank', EXTRUDE, ['Place from Content Center: ISO 4017 M12 x 20, or circle diameter 12, Extrude 20.'], f1),
            F('Head', EXTRUDE, ['Hexagon 18 across flats. Extrude 8. Save.'], f2)]


@part('ballast', 'ballast ring', 'tail', 'Heavy concrete (barytes), 3400 kg/m3, cast in a polyethylene skin', CONCRETE,
      BALLAST_D, 'Weight on the bottom of the tail. Being heavy and low it pulls the centre of gravity well below the '
      'centre of buoyancy, so the buoy floats upright and rights itself. It cannot rust.', origin=(0, 0, TAIL_BOT))
def _ballast():
    r0, r1, h = BALLAST
    f1 = ring(r0, r1, TAIL_BOT, TAIL_BOT + h)
    f2 = f1.faces('>Z').edges(cq.selectors.RadiusNthSelector(1)).chamfer(15)
    return [F('Ring', EXTRUDE, [NEW_PART + ' and save it as ballast.ipt.', 'Circles diameter %d and %d. Extrude %d mm.'
                                % (2 * r0, 2 * r1, h)], f1),
            F('Chamfer', '3D Model tab > Modify panel > Chamfer', ['Chamfer the top outside edge 15 mm. Save.'], f2,
              'Mass from the model: see the calculation sheet.')]


@part('ballast_collar', 'ballast collar', 'tail', '316L stainless split collar with two M8 screws', STEEL_C, SS_D,
      'Clamp collar on the tail tube above the ballast, so the ballast cannot lift off the bottom plate.',
      origin=(0, 0, TAIL_BOT + BALLAST[2]))
def _ballast_collar():
    z = TAIL_BOT + BALLAST[2]
    f1 = ring(TAIL_R, 85, z, z + 15)
    f2 = f1.cut(box(-1.5, 1.5, 0, 90, z - 1, z + 16))
    return [F('Ring', EXTRUDE, [NEW_PART + ' and save it as ballast_collar.ipt.', 'Circles diameter 88.9 and 170. Extrude 15.'], f1),
            F('Split', EXTRUDE, ['Sketch a 3 mm slot from the bore to the outside. Extrude Cut Through All. Save.'], f2,
              'Two M8 screws across the split clamp it to the tube.')]


@part('anode', 'zinc anode', 'tail', 'Zinc alloy split collar anode to MIL-DTL-18001, clamped by one bolt', ZINC_C, ZINC_D,
      'Sacrificial anode clamped round the tail tube. In sea water the zinc corrodes instead of the stainless steel and '
      'the galvanised chain: it is replaced at the yearly service.', origin=(0, 0, ANODE[0]), bought=True)
def _anode():
    f1 = ring(TAIL_R, ANODE[2], ANODE[0], ANODE[1])
    f2 = f1.cut(box(-2, 2, 0, 80, ANODE[0] - 1, ANODE[1] + 1))
    return [F('Ring', EXTRUDE, ['Place from Content Center, or ' + NEW_PART + ': circles diameter 88.9 and 132, Extrude 60.'], f1),
            F('Split', EXTRUDE, ['Sketch a 4 mm slot through one side of the ring. Extrude Cut Through All. Save.'], f2)]


EYE_Z = PIN_Z + 1       # the hole is 1 mm above the pin, so the pin bears on the bottom of the hole


@part('mooring_eye', 'mooring eye', 'tail', '316L stainless plate, 20 thick, welded to the bottom plate', STEEL_C, SS_D,
      'Padeye under the tail. The mooring shackle and load pin fit through its hole, so every pull from the chain goes '
      'through this plate. See the FEA.', origin=(0, 0, BOT_PLATE[0]))
def _mooring_eye():
    t = EYE_T / 2
    z0 = BOT_PLATE[0]
    f1 = box(-t, t, -45, 45, EYE_Z, z0).union(xcyl(45, -t, t, 0, EYE_Z))
    f2 = f1.cut(xcyl(PIN_R + 1, -t - 1, t + 1, 0, EYE_Z))
    return [F('Plate', EXTRUDE, [NEW_PART + ' and save it as mooring_eye.ipt.',
                                 'Start 2D Sketch on the YZ Plane: a 90 wide plate 54 high with a round end radius 45. '
                                 'Extrude 20 mm, Symmetric.'], f1, 'The origin is the top of the plate, on the weld.'),
            F('Pin hole', HOLE, ['Hole diameter 30 Through All on the centre of the round end. Save.'], f2,
              'The 28 diameter load pin fits with 2 mm clearance.')]


# ---------------------------------------------------- SA4 tripod mast and solar panels
@part('tripod_leg', 'tripod leg', 'mast', '316L stainless tube 33.7 x 2 with welded foot plate', STEEL_C, SS_D,
      'One of the three legs of the mast, from a foot on the deck plate to the top plate. A tripod is stiff and light '
      'and leaves the hatch in the middle free.', origin=(LEG_FOOT[0], 0, DECK[1]))
def _tripod_leg():
    (r0, z0), (r1, z1) = LEG_FOOT, LEG_TOP
    tube = leg_solid(0).cut(leg_solid(0, LEG_IR))
    f1 = tube.intersect(box(-300, 300, -300, 300, z0, z1))
    f2 = f1.union(box(178, 232, -46, 46, DECK[1], z0))
    f3 = f2.cut(union(*[zcyl(6.5, DECK[1] - 1, z0 + 1, r0, s * 34) for s in (-1, 1)]))
    return [F('Tube', SWEEP,
              [NEW_PART + ' and save it as tripod_leg.ipt.',
               'Start 2D Sketch on the XY Plane: a line from (%d, %d) to (%d, %d), the leg centre line (it leans in %.1f '
               'degrees). Finish Sketch.' % (r0, z0 - M, r1, z1 - M, math.degrees(math.atan2(r0 - r1, z1 - z0))),
               'Sketch circles diameter 33.7 and 29.7 on a plane square to the line. Sweep along the line. Cut both '
               'ends level (Extrude Cut with a horizontal sketch).'], f1,
              'The origin is the middle of the foot, on the deck plate.'),
            F('Foot plate', EXTRUDE, ['Sketch a 54 x 92 rectangle under the tube. Extrude %d mm, Join (welded).' % (z0 - M)], f2),
            F('Bolt holes', HOLE, ['Hole diameter 13 Through All, 34 mm either side of the tube. Save.'], f3,
              'Two M12 bolts hold each foot to the deck plate.')]


@part('leg_bolt', 'hex bolt M12 x 16', 'mast', 'A4 (316) stainless hex bolt M12 x 16, ISO 4017', STEEL_C, SS_D,
      'Six standard bolts hold the leg feet to the deck plate.', origin=(LEG_FOOT[0], 34, LEG_FOOT[1]), bought=True)
def _leg_bolt():
    x, y, z = LEG_FOOT[0], 34, LEG_FOOT[1]
    f1 = zcyl(6, DECK[0], z, x, y)
    f2 = f1.union(cq.Workplane('XY').polygon(6, 20.8).extrude(8).translate((x, y, z)))
    return [F('Shank', EXTRUDE, ['Place from Content Center: ISO 4017 M12 x 16, or circle diameter 12, Extrude 16.'], f1),
            F('Head', EXTRUDE, ['Hexagon 18 across flats. Extrude 8. Save.'], f2)]


@part('top_plate', 'mast top plate', 'mast', '316L stainless steel plate, 8 thick', STEEL_C, SS_D,
      'Plate on top of the three legs: the lantern and the topmark struts stand on it.', origin=(0, 0, TOP_PLATE[0]))
def _top_plate():
    z0, z1, r = TOP_PLATE
    f1 = zcyl(r, z0, z1)
    f2 = f1.cut(zcyl(10, z0 - 1, z1 + 1))
    return [F('Disc', EXTRUDE, [NEW_PART + ' and save it as top_plate.ipt.', 'Circle diameter 220. Extrude 8 mm.'], f1),
            F('Cable hole', HOLE, ['Hole diameter 20 on the centre, Through All. Save.'], f2,
              'The lantern cable runs down inside a leg to the canister.')]


def bracket_shape(zc):
    """A panel bracket at height zc, drawn for the panel that faces +X: a bar behind the panel and two tabs that
    clamp round the legs at +-60 degrees."""
    n0 = PANEL[0]
    r = leg_r(zc)
    t = r * math.sin(math.radians(60))
    bar = box(n0 - 6, n0, -(t + 8), t + 8, zc - 20, zc + 20)
    tabs = union(*[box(r / 2, n0 - 3, s * t - 8, s * t + 8, zc - 20, zc + 20) for s in (-1, 1)])
    legs = union(leg_solid(60), leg_solid(-60))
    return bar, bar.union(tabs).cut(legs)


@part('bracket_lower', 'lower panel bracket', 'mast', '316L stainless flat bar 6 thick, saddle tabs welded', STEEL_C, SS_D,
      'Bracket across two legs that the bottom of a solar panel bolts to. The tabs are shaped to sit round the legs '
      'and are held by U-bolts.', origin=(PANEL[0], 0, BRACKETS[0]))
def _bracket_lower():
    bar, f2 = bracket_shape(BRACKETS[0])
    return [F('Bar', EXTRUDE, [NEW_PART + ' and save it as bracket_lower.ipt.', 'Sketch a %.0f x 40 rectangle. Extrude 6 mm.'
                               % (2 * leg_r(BRACKETS[0]) * math.sin(math.radians(60)) + 16)], bar),
            F('Saddle tabs', EXTRUDE, ['Sketch the two 16 wide tabs back to the legs. Extrude 40, Join.',
                                       'Cut the saddles: Combine, Cut, with the leg tubes placed as a derived part. Save.'], f2)]


@part('bracket_upper', 'upper panel bracket', 'mast', '316L stainless flat bar 6 thick, saddle tabs welded', STEEL_C, SS_D,
      'Bracket across two legs for the top of a solar panel. The legs are closer together here, so the tabs are longer.',
      origin=(PANEL[0], 0, BRACKETS[1]))
def _bracket_upper():
    bar, f2 = bracket_shape(BRACKETS[1])
    return [F('Bar', EXTRUDE, [NEW_PART + ' and save it as bracket_upper.ipt.', 'Sketch a %.0f x 40 rectangle. Extrude 6 mm.'
                               % (2 * leg_r(BRACKETS[1]) * math.sin(math.radians(60)) + 16)], bar),
            F('Saddle tabs', EXTRUDE, ['Sketch the two 16 wide tabs back to the legs. Extrude 40, Join; Combine, Cut the leg tubes. Save.'], f2)]


@part('solar_panel', 'solar panel 20 W', 'mast', 'Bought in: 20 W monocrystalline marine panel, 400 x 300 x 20, glass front',
      PV_C, 750, 'One of three 20 W panels round the mast. Whichever way the buoy turns on its chain, one panel faces '
                 'the sun. Near upright, so rain and spray wash them clean and birds cannot sit on them.',
      origin=(PANEL[0], 0, PANEL[3]), bought=True)
def _solar_panel():
    n0, t, w, z0, z1 = PANEL
    f1 = box(n0, n0 + t, -w / 2, w / 2, z0, z1)
    f2 = f1.cut(box(n0 + t - 2, n0 + t + 1, -w / 2 + 12, w / 2 - 12, z0 + 12, z1 - 12))
    return [F('Panel', EXTRUDE, [NEW_PART + ' and save it as solar_panel.ipt.', 'Sketch a 300 x 400 rectangle. Extrude 20 mm.'], f1),
            F('Glass', EXTRUDE, ['Sketch the cell area 12 in from the edges. Extrude Cut 2 mm. Save.'], f2,
              'Modelled from the maker\'s outline drawing.')]


# ---------------------------------------------------- SA5 lantern and topmark
LZ = TOP_PLATE[1]


@part('lantern_body', 'lantern base', 'top', 'Bought in: LED marine lantern 2 to 3 NM, base in UV stable polycarbonate',
      DARK, 900, 'Base of the LED lantern: the LEDs, driver and light sensor. It flashes at night so the buoy can be '
                 'seen from 2 to 3 nautical miles.', origin=(0, 0, LZ), bought=True)
def _lantern_body():
    f1 = zcyl(70, LZ, LZ + 12)
    f2 = f1.union(zcyl(55, LZ + 12, LZ + 40))
    return [F('Flange', EXTRUDE, [NEW_PART + ' and save it as lantern_body.ipt.', 'Circle diameter 140. Extrude 12 mm.'], f1),
            F('Body', EXTRUDE, ['Circle diameter 110 on top. Extrude 28 mm. Save.'], f2,
              'Three M8 bolts through the flange into the top plate.')]


@part('lantern_lens', 'lantern lens', 'top', 'Bought in: Fresnel lens, polycarbonate, red or green', RED, 1200,
      'The coloured lens: red for a buoy leaving the harbour, green for one entering (IALA region A).',
      origin=(0, 0, LZ + 40), bought=True)
def _lantern_lens():
    f1 = zcyl(52, LZ + 40, LZ + 140)
    f2 = f1.cut(zcyl(46, LZ + 40 - 1, LZ + 134))
    return [F('Lens', EXTRUDE, [NEW_PART + ' and save it as lantern_lens.ipt.', 'Circle diameter 104. Extrude 100 mm.'], f1),
            F('Hollow it', SHELL, ['Shell: remove the bottom face, thickness 6 mm. Save.'], f2)]


@part('lantern_cap', 'lantern cap', 'top', 'Bought in: lantern top cap with bird spikes, polycarbonate', DARK, 1200,
      'Top cap of the lantern.', origin=(0, 0, LZ + 140), bought=True)
def _lantern_cap():
    f1 = zcyl(58, LZ + 140, LZ + 152)
    f2 = f1.union(zcyl(3, LZ + 152, LZ + 180, 0, 0))
    return [F('Cap', EXTRUDE, [NEW_PART + ' and save it as lantern_cap.ipt.', 'Circle diameter 116. Extrude 12 mm.'], f1),
            F('Bird spike', EXTRUDE, ['Circle diameter 6 on the centre. Extrude 28 mm. Save.'], f2,
              'Stops birds perching and fouling the lens.')]


@part('topmark_strut', 'topmark strut', 'top', '316L stainless flat bar 30 x 6', STEEL_C, SS_D,
      'One of three flat bars from the top plate up round the lantern to the topmark plate.',
      origin=(STRUT[0], 0, STRUT[3]))
def _topmark_strut():
    r, t, w, z0, z1 = STRUT
    f1 = box(r, r + t, -w / 2, w / 2, z0, z1)
    return [F('Bar', EXTRUDE, [NEW_PART + ' and save it as topmark_strut.ipt.', 'Sketch a %d x %d rectangle. Extrude %d mm. Save.'
                               % (t, w, z1 - z0)], f1,
              'Welded to the top plate and the topmark plate. Thin, so they hardly hide the light.')]


@part('topmark_plate', 'topmark plate', 'top', '316L stainless steel plate, 6 thick', STEEL_C, SS_D,
      'Plate on the struts above the lantern: the topmark and the antenna sit on it.', origin=(0, 0, TM_PLATE[0]))
def _topmark_plate():
    z0, z1, r = TM_PLATE
    f1 = zcyl(r, z0, z1)
    f2 = f1.cut(zcyl(6, z0 - 1, z1 + 1))
    return [F('Disc', EXTRUDE, [NEW_PART + ' and save it as topmark_plate.ipt.', 'Circle diameter %d. Extrude %d mm.' % (2 * r, z1 - z0)], f1),
            F('Cable hole', HOLE, ['Hole diameter 12 on the centre. Save.'], f2)]


@part('antenna', 'GNSS and mobile antenna', 'top', 'Bought in: combined GNSS and LTE-M puck antenna, IP67', WHITE, 900,
      'The antenna for the tracker. It sits inside the polyethylene topmark, which radio passes through, so it is out '
      'of sight and protected.', origin=(0, 0, TM_PLATE[1]), bought=True)
def _antenna():
    f1 = zcyl(45, TM_PLATE[1], TM_PLATE[1] + 18)
    f2 = f1.faces('>Z').edges().fillet(8)
    return [F('Puck', EXTRUDE, [NEW_PART + ' and save it as antenna.ipt.', 'Circle diameter 90. Extrude 18 mm.'], f1),
            F('Round the top', FILLET, ['Fillet the top edge radius 8. Save.'], f2)]


@part('topmark_can', 'topmark, can (red)', 'top', 'Rotomoulded MDPE, red, retro-reflective red bands', RED, MDPE_D,
      'Red can topmark for a buoy leaving the harbour (port hand mark). Big and bright at the top of the buoy, so its '
      'shape and colour can be seen from a distance by day.', origin=(0, 0, CAN_TM[2]))
def _topmark_can():
    r, t, z0, z1 = CAN_TM
    f1 = zcyl(r, z0, z1)
    f2 = f1.cut(zcyl(r - t, z0 - 1, z1 - t))
    return [F('Cylinder', EXTRUDE, [NEW_PART + ' and save it as topmark_can.ipt.', 'Circle diameter 200. Extrude 260 mm.'], f1),
            F('Hollow it', SHELL, ['Shell: remove the bottom face, thickness 5 mm. Save.'], f2,
              'Hollow: light, and radio passes through polyethylene to the antenna inside.')]


@part('topmark_cone', 'topmark, cone (green)', 'top', 'Rotomoulded MDPE, green, retro-reflective green bands', GREEN, MDPE_D,
      'Green cone topmark, point up, for a buoy entering the harbour (starboard hand mark). Fitted instead of the can.',
      origin=(0, 0, CONE_TM[2]))
def _topmark_cone():
    r, t, z0, z1 = CONE_TM
    h = z1 - z0
    f1 = cq.Workplane('XY').add(cq.Solid.makeCone(r, 4, h, cq.Vector(0, 0, z0)))   # a small flat tip, 8 across
    k = 1 - (t * math.hypot(r, h) / r) / h          # the inner cone is the outer one scaled down: about 5 mm wall
    inner = cq.Solid.makeCone(r * k, 2, h * k, cq.Vector(0, 0, z0 - 0.01))
    f2 = f1.cut(cq.Workplane('XY').add(inner))
    return [F('Cone', REVOLVE, [NEW_PART + ' and save it as topmark_cone.ipt.',
                                'Sketch a right triangle 125 wide and 280 high on the XY Plane. Revolve 360 degrees.'], f1),
            F('Hollow it', SHELL, ['Shell: remove the bottom face, thickness 5 mm. Save.'], f2)]


# ---------------------------------------------------- SA6 and SA7 mooring
SH_EAR = (11, 25)       # shackle ear faces (x)
SH_LEG_X = 18           # shackle leg centre line (x)
SH_R = 7                # shackle bar radius
SH_DROP = 70            # pin axis to bow centre
BOW_Z = PIN_Z - SH_DROP  # centre of the bow
CROWN = BOW_Z - SH_LEG_X  # bow crown centre line
SW_EYE = (20, 7)        # swivel eye: centre line radius, section radius
SW_TOP = CROWN + SH_R + SW_EYE[1] - SW_EYE[0]    # swivel top eye centre (its top bar rests on the bow crown)
SW_BOT = SW_TOP - 90                              # swivel bottom eye centre
CR = CHAIN_D / 2
LINK_A = 9 + CR                                  # link crown centre line radius (inside width 18)
LINK_S = 4 * CHAIN_D + CHAIN_D - 2 * LINK_A      # straight part (inside length 52 = 4d)
LINK_PITCH = 4 * CHAIN_D
LINK1_TOP = SW_BOT - SW_EYE[0] + SW_EYE[1] + CR  # link 1 top crown centre line (it rests on the swivel eye)


def link_shape(top, plane='YZ'):
    """One chain link with its top crown centre line at z = top, in the YZ or XZ plane."""
    a, s = LINK_A, LINK_S
    c1, c2 = top - a, top - a - s
    d = (1, 0, 0) if plane == 'YZ' else (0, 1, 0)
    half_up = box(-100, 100, -100, 100, c1, c1 + 100)
    half_dn = box(-100, 100, -100, 100, c2 - 100, c2)
    t1 = torus(a, CR, (0, 0, c1), d).intersect(half_up)
    t2 = torus(a, CR, (0, 0, c2), d).intersect(half_dn)
    if plane == 'YZ':
        bars = [cyl(CR, (0, sy * a, c2), (0, 0, 1), s) for sy in (-1, 1)]
    else:
        bars = [cyl(CR, (sx * a, 0, c2), (0, 0, 1), s) for sx in (-1, 1)]
    return t1, union(t1, t2, *bars)


@part('shackle', 'bow shackle', 'mooring', 'Bought in: 316 stainless bow shackle, WLL 3.25 t (pin replaced by the load pin)',
      STEEL_C, SS_D, 'Standard bow shackle joining the swivel to the mooring eye. Its pin is the load pin (item 39).',
      origin=(0, 0, PIN_Z), bought=True)
def _shackle():
    e0, e1 = SH_EAR
    ears = union(*[xcyl(18, s * e1 if s < 0 else e0, s * e0 if s < 0 else e1, 0, PIN_Z) for s in (-1, 1)])
    legs = union(*[zcyl(SH_R, BOW_Z, PIN_Z, s * SH_LEG_X, 0) for s in (-1, 1)])
    bow = torus(SH_LEG_X, SH_R, (0, 0, BOW_Z), (0, 1, 0)).intersect(box(-60, 60, -60, 60, BOW_Z - 60, BOW_Z))
    f1 = union(ears, legs)
    f2 = f1.union(bow)
    f3 = f2.cut(xcyl(PIN_R, -40, 40, 0, PIN_Z))
    return [F('Ears and legs', EXTRUDE, ['Place from Content Center (bow shackle), or ' + NEW_PART + ': two ears diameter 36 x 14, '
                                         '22 apart, and two legs diameter %d down %d mm.' % (2 * SH_R, SH_DROP)], f1),
            F('Bow', SWEEP, ['Sweep a circle diameter %d round a half circle radius %d joining the legs.' % (2 * SH_R, SH_LEG_X)], f2),
            F('Pin holes', HOLE, ['Hole diameter 28 Through All through both ears. Save.'], f3)]


@part('load_pin', 'load pin (alert sensor)', 'mooring',
      'Bought in: 17-4PH stainless strain gauge load pin, 28 dia, 0 to 50 kN, 4 to 20 mA, IP68', YELLOW, SS_D,
      'The alert sensor: the shackle pin is a load pin that measures the pull of the chain all the time. If the chain '
      'breaks the pull falls to nothing, and the control unit sends an alert with the buoy\'s position.',
      origin=(-29, 0, PIN_Z), bought=True)
def _load_pin():
    e1 = SH_EAR[1]
    f1 = xcyl(PIN_R, -e1 - 4, e1, 0, PIN_Z)
    f2 = f1.union(xcyl(20, e1, e1 + 6, 0, PIN_Z))
    f3 = f2.union(xcyl(8, e1 + 6, e1 + 26, 0, PIN_Z))
    return [F('Pin', EXTRUDE, ['Place from Content Center or ' + NEW_PART + ': circle diameter 28 on the YZ Plane, Extrude 54.'], f1,
              'Strain gauges in two grooves inside the pin measure the shear on it.'),
            F('Head', EXTRUDE, ['Circle diameter 40 on one end. Extrude 6.'], f2),
            F('Cable connector', EXTRUDE, ['Circle diameter 16 on the head. Extrude 20. Save.'], f3,
              'The cable runs up the tail tube to the canister.')]


@part('swivel', 'mooring swivel', 'mooring', 'Bought in: 316 stainless eye and eye swivel, WLL 2 t', STEEL_C, SS_D,
      'Lets the buoy turn on its chain without twisting the chain.', origin=(0, 0, SW_TOP), bought=True)
def _swivel():
    R, r = SW_EYE
    top = torus(R, r, (0, 0, SW_TOP), (1, 0, 0))
    body = zcyl(14, SW_BOT + R, SW_TOP - R - 2)
    bot = torus(R, r, (0, 0, SW_BOT), (0, 1, 0))
    f1 = top.union(body)
    f2 = f1.union(bot)
    return [F('Top eye and body', REVOLVE, ['Place from Content Center (swivel), or ' + NEW_PART + ': an eye (circle '
                                            'diameter 14 round radius 20) and a body diameter 28.'], f1),
            F('Bottom eye', SWEEP, ['A second eye at 90 degrees to the first. Save.'], f2,
              'The two halves turn on a bearing inside the body.')]


@part('chain_link', 'chain link %d mm' % CHAIN_D, 'mooring', 'Grade 30 long link chain, %d mm, hot dip galvanised' % CHAIN_D, GALV, GALV_D,
      'Mooring chain. Shown here: the first links under the buoy. The chain runs down to the sinker (sub-assembly 7); '
      'its length is about 3 times the depth of water.', origin=(0, 0, LINK1_TOP + CR), bought=True)
def _chain_link():
    t1, f2 = link_shape(LINK1_TOP, 'YZ')
    return [F('Crown', SWEEP, ['Place from Content Center (chain), or ' + NEW_PART + ': sweep a circle diameter %d round a '
                               'half circle radius %g.' % (CHAIN_D, LINK_A)], t1),
            F('Link', SWEEP, ['Sweep the circle along the whole link path: %d long and %d wide inside. Save.'
                              % (LINK_PITCH, 2 * LINK_A - CHAIN_D)], f2,
              'Each link is turned 90 degrees to the one before.')]


SINK = (600, 350)       # sinker block side and height
SINK_EYE = (40, 8)      # sinker eye: centre line radius, bar radius


@part('sinker', 'concrete sinker', 'mooring', 'Reinforced concrete C32/40, 600 x 600 x 350, about 300 kg', CONCRETE, CONC_D,
      'Block on the harbour bed that the chain is fixed to. Concrete does not rust and needs no maintenance.',
      origin=(0, 0, -SINK[1]))
def _sinker():
    a, h = SINK
    f1 = box(-a / 2, a / 2, -a / 2, a / 2, -h, 0)
    f2 = f1.edges('>Z').chamfer(30)
    f3 = f2.cut(sinker_eye_shape())
    return [F('Block', EXTRUDE, [NEW_PART + ' and save it as sinker.ipt.', 'Sketch a 600 x 600 square. Extrude 350 mm.'], f1,
              'The origin is the middle of the top face.'),
            F('Chamfer the top', '3D Model tab > Modify panel > Chamfer', ['Chamfer the top edges 30 mm.'], f2),
            F('Eye bar cast in', COMBINE, ['Combine, Cut: the eye bar (item 43) placed in the block. Save.'], f3,
              'The eye is cast in when the concrete is poured.')]


def sinker_eye_shape():
    R, r = SINK_EYE
    legs = union(*[zcyl(r, -250, 0, s * R, 0) for s in (-1, 1)])
    arch = torus(R, r, (0, 0, 0), (0, 1, 0)).intersect(box(-80, 80, -80, 80, 0, 80))
    feet = union(*[cyl(r, (s * R, 0, -250), (s, 0, 0), 60) for s in (-1, 1)])
    return union(legs, arch, feet)


@part('sinker_eye', 'sinker eye bar', 'mooring', '316 stainless round bar 16 dia, bent', STEEL_C, SS_D,
      'U-bar cast into the sinker; the bottom link of the chain goes round it.', origin=(0, 0, 0))
def _sinker_eye():
    R, r = SINK_EYE
    f1 = union(*[zcyl(r, -250, 0, s * R, 0) for s in (-1, 1)]).union(
        torus(R, r, (0, 0, 0), (0, 1, 0)).intersect(box(-80, 80, -80, 80, 0, 80)))
    f2 = sinker_eye_shape()
    return [F('U-bar', SWEEP, [NEW_PART + ' and save it as sinker_eye.ipt.', 'Sweep a circle diameter 16 along a U: two '
                               'legs 250 long, 80 apart, joined by a half circle.'], f1),
            F('Feet', SWEEP, ['Sweep the ends out 60 mm each side, so the bar cannot pull out of the concrete. Save.'], f2)]


PART = {p['key']: p for p in PARTS}
for _i, _p in enumerate(PARTS, 1):
    _p['no'] = _i


@functools.lru_cache(maxsize=None)
def features(key):
    return PART[key]['feats']()


def shape(key):
    """The finished part where it is drawn."""
    return features(key)[-1]['shape']


def part_shape(key):
    """The finished part in its own part file (its origin moved to the part datum)."""
    ox, oy, oz = PART[key]['origin']
    return shape(key).translate((-ox, -oy, -oz))


# ------------------------------------------------------------------ placing parts
IDENT = lambda w: w


def _rz(a):
    return lambda w: rotz(w, a)


def _t(dx=0, dy=0, dz=0):
    return lambda w: w.translate((dx, dy, dz))


VARIANT = dict(red=dict(hull=RED, lens=RED, topmark='topmark_can'),
               green=dict(hull=GREEN, lens=GREEN, topmark='topmark_cone'))


def instances(variant='red'):
    """Every part of the buoy: (instance name, part key, transform, sub-assembly key)."""
    out = [('float hull', 'float_hull', IDENT, 'float'), ('float foam fill', 'float_foam', IDENT, 'float'),
           ('fender ring', 'fender', IDENT, 'float'), ('deck plate', 'deck_plate', IDENT, 'float'),
           ('keel plate', 'keel_plate', IDENT, 'float')]
    for k, a in enumerate(TIE_ANG, 1):
        out += [('tie rod %d' % k, 'tie_rod', _rz(a - 30), 'float'), ('tie rod nut %d' % k, 'tie_rod_nut', _rz(a - 30), 'float'),
                ('lifting eye nut %d' % k, 'eye_nut', _rz(a - 30), 'float')]
    out += [('equipment canister', 'canister', IDENT, 'equipment'), ('mounting plate', 'mounting_plate', IDENT, 'equipment'),
            ('battery', 'battery', IDENT, 'equipment'), ('battery strap', 'battery_strap', IDENT, 'equipment'),
            ('control and tracking unit', 'control_unit', IDENT, 'equipment'), ('hatch O-ring', 'hatch_seal', IDENT, 'equipment'),
            ('hatch lid', 'hatch_lid', IDENT, 'equipment')]
    out += [('lid bolt %d' % (k + 1), 'hatch_bolt', _rz(45 * k), 'equipment') for k in range(N_BOLTS)]
    out += [('cable gland 1', 'cable_gland', IDENT, 'equipment'), ('cable gland 2', 'cable_gland', _rz(180), 'equipment')]
    out += [('tail tube', 'tail_tube', IDENT, 'tail')]
    out += [('tail flange bolt %d' % (k + 1), 'keel_bolt', _rz(60 * k), 'tail') for k in range(6)]
    out += [('ballast ring', 'ballast', IDENT, 'tail'), ('ballast collar', 'ballast_collar', IDENT, 'tail'),
            ('zinc anode', 'anode', IDENT, 'tail'), ('mooring eye', 'mooring_eye', IDENT, 'tail')]
    for k, a in enumerate(LEG_ANG, 1):
        out.append(('tripod leg %d' % k, 'tripod_leg', _rz(a), 'mast'))
        out += [('leg bolt %d%s' % (k, 'ab'[j]), 'leg_bolt', (lambda w, a=a, j=j: rotz(w.mirror('XZ') if j else w, a)), 'mast')
                for j in (0, 1)]
    out.append(('mast top plate', 'top_plate', IDENT, 'mast'))
    for k, a in enumerate(PANEL_ANG, 1):
        out += [('lower panel bracket %d' % k, 'bracket_lower', _rz(a), 'mast'),
                ('upper panel bracket %d' % k, 'bracket_upper', _rz(a), 'mast'),
                ('solar panel %d' % k, 'solar_panel', _rz(a), 'mast')]
    out += [('lantern base', 'lantern_body', IDENT, 'top'), ('lantern lens', 'lantern_lens', IDENT, 'top'),
            ('lantern cap', 'lantern_cap', IDENT, 'top')]
    out += [('topmark strut %d' % (k + 1), 'topmark_strut', _rz(a), 'top') for k, a in enumerate(STRUT_ANG)]
    out += [('topmark plate', 'topmark_plate', IDENT, 'top'), ('antenna', 'antenna', IDENT, 'top'),
            ('topmark', VARIANT[variant]['topmark'], IDENT, 'top')]
    out += [('bow shackle', 'shackle', IDENT, 'mooring'), ('load pin', 'load_pin', IDENT, 'mooring'),
            ('swivel', 'swivel', IDENT, 'mooring')]
    for k in range(CHAIN_LINKS):
        tf = (lambda w, k=k: w.translate((0, 0, -k * LINK_PITCH))) if k % 2 == 0 else \
             (lambda w, k=k: rotz(w, 90).translate((0, 0, -k * LINK_PITCH)))
        out.append(('chain link %d' % (k + 1), 'chain_link', tf, 'mooring'))
    return out


def colour(key, variant='red'):
    if key == 'float_hull':
        return VARIANT[variant]['hull']
    if key == 'lantern_lens':
        return VARIANT[variant]['lens']
    return PART[key]['colour']


def buoy_instances(variant='red'):
    """Every part in the buoy: (instance name, part key, shape)."""
    return [(n, k, tf(shape(k))) for n, k, tf, sub in instances(variant)]


def buoy(variant='red'):
    """Design A, the preferred design: a harbour lane marker buoy. A 500 diameter foam filled polyethylene float
    with a rubber fender, a stainless tripod mast with three 20 W solar panels, an LED lantern and a topmark with the
    tracking antenna inside it; a lockable watertight canister for the battery and the control and tracking unit;
    a stainless tail with ballast and a zinc anode; and a load pin in the mooring shackle that raises the alert if
    the chain breaks. Shown as a red (leaving the harbour) buoy."""
    return [(n, s, colour(k, variant)) for n, k, s in buoy_instances(variant)]


def buoy_green():
    """The same buoy as an entrance (green) buoy: green float, green lantern lens and a green cone topmark in
    place of the red can. Every other part is the same."""
    return buoy('green')


# the sinker on the harbour bed (sub-assembly 7), drawn with the top of the sinker at z = 0
def sinker_instances():
    """The sinker with its eye bar, and the bottom links of the ground chain rising from the eye (pulled up, so the
    bottom crown of link 1 bears on the underside of the arch of the eye bar)."""
    R, r = SINK_EYE
    out = [('concrete sinker', 'sinker', IDENT), ('sinker eye bar', 'sinker_eye', IDENT)]
    top1 = R - (r + CR) + LINK_PITCH + 2 * CR     # top crown centre line of link 1
    for k in range(3):
        dz = top1 - LINK1_TOP + k * LINK_PITCH
        tf = (lambda w, dz=dz: w.translate((0, 0, dz))) if k % 2 == 0 else (lambda w, dz=dz: rotz(w, 90).translate((0, 0, dz)))
        out.append(('ground chain link %d' % (k + 1), 'chain_link', tf))
    return out


def sinker_items():
    return [(n, k, tf(shape(k))) for n, k, tf in sinker_instances()]


def masses(items=None):
    """Mass of every instance (kg), by part key: {key: [qty, mass]}."""
    items = items if items is not None else buoy_instances()
    by = {}
    for n, k, s in items:
        m = s.val().Volume() * 1e-9 * PART[k]['density']
        by.setdefault(k, [0, 0.0])
        by[k][0] += 1
        by[k][1] += m
    return by


def buoy_mass(variant='red'):
    return sum(m for q, m in masses(buoy_instances(variant)).values())


# ------------------------------------------------------------------ floating: waterline, buoyancy and stability
def envelope(items):
    """Solids that displace sea water: the float's outside shape (the well, canister and foam are all inside it),
    the fender, every part below the float, and the sealed inside of the tail tube. They do not overlap."""
    g, z0, z1 = GROOVE
    out = [float_outer().cut(ring(g, FLOAT_R + 1, z0, z1)).val(),
           zcyl(TAIL_R - TAIL_T, TAIL_BOT, KEEL[0]).val()]
    for n, k, s in items:
        v = s.val()
        if k == 'fender' or v.BoundingBox().zmax <= FLOAT_BOT + 0.5:
            out.append(v)
    return out


def below(solids, h):
    """Volume (mm3) and centroid z of the solids below the plane z = h."""
    cut = cq.Solid.makeBox(4000, 4000, 4000, cq.Vector(-2000, -2000, h - 4000))
    vol, mz = 0.0, 0.0
    for v in solids:
        c = v.intersect(cut)
        vv = c.Volume()
        if vv > 0:
            vol += vv
            mz += vv * c.Center().z
    return vol, (mz / vol if vol else 0.0)


def mass_props(items):
    """Total mass (kg) and centre of gravity (x, y, z) of the items."""
    m, mx, my, mz = 0.0, 0.0, 0.0, 0.0
    for n, k, s in items:
        v = s.val()
        mm = v.Volume() * 1e-9 * PART[k]['density']
        c = v.Center()
        m += mm
        mx, my, mz = mx + mm * c.x, my + mm * c.y, mz + mm * c.z
    return m, (mx / m, my / m, mz / m)


def float_line(items=None, extra=0.0, extra_z=None):
    """Where the buoy floats: the waterline height h (mm, on the drawing's z) where the sea water pushed aside
    weighs the same as the buoy plus 'extra' kg hung from the mooring eye (the chain), then the stability.
    Returns a dict with the waterline, displaced volume, centre of buoyancy, centre of gravity and GM."""
    items = items if items is not None else buoy_instances()
    sol = envelope(items)
    m, G = mass_props(items)
    need = (m + extra) / SW_D * 1e9            # mm3 of sea water to push aside
    lo, hi = FLOAT_BOT, FLOAT_TOP
    for _ in range(40):
        h = (lo + hi) / 2
        if below(sol, h)[0] < need:
            lo = h
        else:
            hi = h
    vol, zb = below(sol, h)
    zg = G[2]
    if extra:
        zg = (m * G[2] + extra * (extra_z if extra_z is not None else PIN_Z)) / (m + extra)
    I = math.pi * (2 * FLOAT_R) ** 4 / 64      # second moment of the waterplane (a 500 circle)
    BM = I / vol
    return dict(h=h, mass=m, extra=extra, vol=vol, zb=zb, zg=zg, BM=BM, GM=zb + BM - zg, G=G,
                full=below(sol, FLOAT_TOP)[0], reserve=below(sol, FLOAT_TOP)[0] * 1e-9 * SW_D - m - extra)


# ------------------------------------------------------------------ Design B concept: spherical float with wind turbine
def wind_buoy():
    """Design B, a concept: a 500 diameter spherical steel float with a lattice tower, a small vertical axis wind
    turbine, a lantern and a topmark, on a single chain. Simple to make, but the turbine has moving parts that need
    servicing and the steel float needs painting to stop it rusting."""
    out = []
    sphere = cq.Workplane('XY').sphere(250).translate((0, 0, -50))
    out.append(('steel spherical float', sphere, RED))
    legs = union(*[box(-8, 8, -8, 8, 150, 1200).translate(polar(120, a)[:2] + (0,)) for a in (0, 120, 240)])
    rings = union(*[ring(110, 135, z, z + 10) for z in (450, 800, 1150)])
    out.append(('lattice tower', legs.union(rings), RED))
    blades = union(*[box(-4, 4, -60, 60, 1210, 1450).translate(polar(70, a)[:2] + (0,)) for a in (0, 120, 240)])
    hub = zcyl(12, 1200, 1460).union(zcyl(75, 1200, 1210)).union(zcyl(75, 1450, 1460))
    out.append(('vertical axis wind turbine', blades.union(hub), WHITE))
    out.append(('lantern', zcyl(55, 1460, 1600), DARK))
    out.append(('topmark (can)', zcyl(90, 1600, 1780), RED))
    out.append(('tail and ballast', zcyl(40, -900, -290).union(zcyl(130, -900, -750)), STEEL_C))
    return out


# ------------------------------------------------------------------ parts list
def bom(names, items):
    """Parts list rows for the instances in names."""
    keys = {n: k for n, k, s in items}
    rows = {}
    for n in names:
        rows.setdefault(keys[n], []).append(n)
    out = []
    for p in PARTS:
        if p['key'] in rows:
            out.append(dict(no=p['no'], name=p['name'], qty=len(rows[p['key']]), material=p['material'],
                            group=p['group'], model=part_model_name(p), file=p['file'], bought=p['bought'],
                            instances=rows[p['key']]))
    return out


def part_model_name(p):
    return 'esp2024_p%02d_%s' % (p['no'], p['key'])


def _part_fn(p):
    def fn():
        return [(p['name'], part_shape(p['key']), p['colour'])]
    fn.__doc__ = p['desc']
    return fn


def _buoy_bom(variant='red'):
    def fn():
        items = buoy_instances(variant)
        return bom([n for n, k, s in items], items)
    return fn


# ------------------------------------------------------------------ sub-assemblies
# How the buoy is built, the way it would be in Inventor: six sub-assemblies (.iam) are made from their parts and
# placed into the top level assembly; the sinker (sub-assembly 7) is laid on the harbour bed and joined by the chain.
# 'explode' moves each part away from where it sits (mm) for the exploded views; 'steps' place the parts a group at a
# time (names, title, command, actions, note).
def _names(sub):
    return [n for n, k, tf, s in instances() if s == sub]


def _explode_float():
    ex = {'float hull': (0, 0, 0), 'float foam fill': (0, 0, 0), 'fender ring': (0, 0, 0),
          'deck plate': (0, 0, 380), 'keel plate': (0, 0, -380)}
    for k in (1, 2, 3):
        ex['tie rod %d' % k] = (0, 0, 900)
        ex['tie rod nut %d' % k] = (0, 0, -520)
        ex['lifting eye nut %d' % k] = (0, 0, 560)
    ex['fender ring'] = (0, 0, 0)
    return ex


def _explode_equipment():
    ex = {'equipment canister': (0, 0, 0), 'mounting plate': (0, 0, 560), 'battery': (0, 0, 700),
          'battery strap': (0, 0, 900), 'control and tracking unit': (0, 0, 760), 'hatch O-ring': (0, 0, 1150),
          'hatch lid': (0, 0, 1250), 'cable gland 1': (0, 0, 1400), 'cable gland 2': (0, 0, 1400)}
    for k in range(N_BOLTS):
        ex['lid bolt %d' % (k + 1)] = (0, 0, 1350)
    return ex


def _explode_tail():
    ex = {'tail tube': (0, 0, 0), 'ballast ring': (0, 0, 220), 'ballast collar': (0, 0, 380), 'zinc anode': (0, 0, 140),
          'mooring eye': (0, 0, -180)}
    for k in range(6):
        ex['tail flange bolt %d' % (k + 1)] = (0, 0, -220)
    return ex


def _explode_mast():
    ex = {'mast top plate': (0, 0, 220)}
    for k, a in enumerate(LEG_ANG, 1):
        ex['tripod leg %d' % k] = (0, 0, 0)
        ex['leg bolt %da' % k] = ex['leg bolt %db' % k] = (0, 0, 120)
    for k, a in enumerate(PANEL_ANG, 1):
        ux, uy, _ = polar(1, a)
        ex['lower panel bracket %d' % k] = (ux * 120, uy * 120, 0)
        ex['upper panel bracket %d' % k] = (ux * 120, uy * 120, 0)
        ex['solar panel %d' % k] = (ux * 300, uy * 300, 0)
    return ex


def _explode_top():
    ex = {'lantern base': (0, 0, 0), 'lantern lens': (0, 0, 90), 'lantern cap': (0, 0, 180), 'topmark plate': (0, 0, 300),
          'antenna': (0, 0, 380), 'topmark': (0, 0, 560)}
    for k, a in enumerate(STRUT_ANG, 1):
        ux, uy, _ = polar(1, a)
        ex['topmark strut %d' % k] = (ux * 120, uy * 120, 0)
    return ex


def _explode_mooring():
    ex = {'bow shackle': (0, 0, 0), 'load pin': (-120, 0, 0), 'swivel': (0, 0, -90)}
    for k in range(CHAIN_LINKS):
        ex['chain link %d' % (k + 1)] = (0, 0, -180 - 50 * k)
    return ex


SUBS = [
    dict(no=1, key='float', title='float', file='float.iam', explode=_explode_float(),
         desc='The float: the polyethylene hull, its foam fill and fender, clamped between the stainless deck plate and '
              'keel plate by three tie rods with nuts underneath and lifting eye nuts on top.',
         steps=[
             (['float hull', 'float foam fill'], 'Hull and foam', PLACE,
              [NEW_ASSY + ' and save it as float.iam.', 'Place float_hull.ipt and Place Grounded.',
               'Place float_foam.ipt and Mate its outside to the inside of the shell (it fills it exactly).'],
              'At the factory the foam is poured into the shell through a filling hole.'),
             (['fender ring'], 'Fender', CONSTRAIN,
              ['Place fender.ipt: Mate its inside face to the bottom of the groove and Flush its top with the top of the groove.'],
              'The fender is stretched over the float into the groove.'),
             (['deck plate', 'keel plate'], 'Deck and keel plates', CONSTRAIN,
              ['Place deck_plate.ipt on top: Mate it to the top of the float and Insert one tie rod hole on the hole in the hull.',
               'Place keel_plate.ipt underneath the same way.'], None),
             (['tie rod 1', 'tie rod 2', 'tie rod 3', 'tie rod nut 1', 'tie rod nut 2', 'tie rod nut 3'], 'Tie rods and nuts',
              PATTERN, ['Place tie_rod.ipt (Content Center, M16 threaded rod): Insert it in a hole, 15 mm below the keel plate.',
                        'Place an M16 nut (Content Center, ISO 4032) under the keel plate (Insert).',
                        'Pattern > Circular: rod and nut, 3 round the float axis.'], None),
             (['lifting eye nut 1', 'lifting eye nut 2', 'lifting eye nut 3'], 'Lifting eye nuts', PATTERN,
              ['Place eye_nut.ipt (DIN 582 M16) on top of each rod: Insert. Circular Pattern 3. Save.'],
              'Tightening the eye nuts clamps the float between the plates; the eyes are the lifting points.'),
         ]),
    dict(no=2, key='equipment', title='equipment canister', file='equipment_canister.iam', explode=_explode_equipment(),
         desc='The secure watertight canister: stainless canister, mounting plate, battery and strap, the control and '
              'tracking unit, the O-ring, the hatch lid with eight tamper proof bolts and the two cable glands.',
         steps=[
             (['equipment canister'], 'Canister', PLACE, [NEW_ASSY + ' and save it as equipment_canister.iam.',
                                                          'Place canister.ipt and Place Grounded.'], None),
             (['mounting plate', 'battery', 'battery strap', 'control and tracking unit'], 'Battery and control unit',
              CONSTRAIN, ['Place mounting_plate.ipt on the floor of the canister (Mate, Insert the edge).',
                          'Place battery.ipt and control_unit.ipt on the plate (Mate, then Flush to the sketch lines).',
                          'Place battery_strap.ipt over the battery (Mate the inside of the strap to the battery).'],
              'Everything sits low in the canister: it helps keep the buoy upright.'),
             (['hatch O-ring', 'hatch lid'], 'O-ring and lid', CONSTRAIN,
              ['Place hatch_seal.ipt on the flange (Mate, Insert). Place hatch_lid.ipt over it: Mate the underside to the '
               'flange and Insert a bolt hole on a flange hole.'], 'The O-ring in its groove makes the hatch watertight.'),
             (['lid bolt %d' % (k + 1) for k in range(N_BOLTS)] + ['cable gland 1', 'cable gland 2'], 'Bolts and glands',
              PATTERN, ['Place a tamper proof M10 screw (Content Center, ISO 7380) in one hole (Insert); Circular Pattern 8.',
                        'Place cable_gland.ipt in each gland hole (Insert). Save.'], None),
         ]),
    dict(no=3, key='tail', title='tail and ballast', file='tail.iam', explode=_explode_tail(),
         desc='The tail: the stainless tail tube with its six flange bolts, the ballast ring and its collar, the zinc '
              'anode and the mooring eye.',
         steps=[
             (['tail tube'], 'Tail tube', PLACE, [NEW_ASSY + ' and save it as tail.iam.', 'Place tail_tube.ipt and Place Grounded.'], None),
             (['mooring eye'], 'Mooring eye', CONSTRAIN, ['Place mooring_eye.ipt under the bottom plate: Mate, then Flush its '
                                                           'centre plane with the YZ Plane (it is welded on).'], None),
             (['ballast ring', 'ballast collar'], 'Ballast', CONSTRAIN,
              ['Place ballast.ipt over the tube onto the bottom plate (Insert). Place ballast_collar.ipt on top (Insert).'],
              'The ballast keeps the buoy upright.'),
             (['zinc anode'], 'Anode', CONSTRAIN, ['Place anode.ipt on the tube 450 mm below the keel plate (Insert, Offset).'],
              'It protects the steel by corroding first.'),
             (['tail flange bolt %d' % (k + 1) for k in range(6)], 'Flange bolts', PATTERN,
              ['Place an M12 x 20 bolt (Content Center, ISO 4017) in one flange hole (Insert); Circular Pattern 6. Save.'],
              'In the buoy they screw into the keel plate.'),
         ]),
    dict(no=4, key='mast', title='mast and solar panels', file='mast.iam', explode=_explode_mast(),
         desc='The tripod mast: three legs with two bolts each, the top plate, and on each face a lower and an upper '
              'bracket carrying a 20 W solar panel.',
         steps=[
             (['tripod leg 1', 'tripod leg 2', 'tripod leg 3'], 'Legs', PATTERN,
              [NEW_ASSY + ' and save it as mast.iam.', 'Place tripod_leg.ipt and Place Grounded at 90 degrees.',
               'Pattern > Circular: 3 legs round the axis.'], None),
             (['mast top plate'], 'Top plate', CONSTRAIN, ['Place top_plate.ipt: Mate its underside to the top ends of the '
                                                            'legs and Insert it on the axis.'], 'It is welded to the legs.'),
             (['lower panel bracket 1', 'lower panel bracket 2', 'lower panel bracket 3', 'upper panel bracket 1',
               'upper panel bracket 2', 'upper panel bracket 3'], 'Panel brackets', PATTERN,
              ['Place bracket_lower.ipt and bracket_upper.ipt on the front face: Tangent the saddles to the legs.',
               'Circular Pattern: 3.'], None),
             (['solar panel 1', 'solar panel 2', 'solar panel 3'], 'Solar panels', PATTERN,
              ['Place solar_panel.ipt on the front brackets (Mate its back to the brackets, Flush the centre planes).',
               'Circular Pattern: 3.'], 'One panel always faces the sun, whichever way the buoy turns.'),
             (['leg bolt %d%s' % (k, c) for k in (1, 2, 3) for c in 'ab'], 'Leg bolts', PATTERN,
              ['Place an M12 x 16 bolt (Content Center) in each foot hole (Insert); Circular Pattern 3. Save.'], None),
         ]),
    dict(no=5, key='top', title='lantern and topmark', file='lantern_topmark.iam', explode=_explode_top(),
         desc='The top: the LED lantern (base, coloured lens and cap), the three topmark struts and plate, the antenna '
              'and the topmark (a red can, or a green cone for an entrance buoy).',
         steps=[
             (['lantern base', 'lantern lens', 'lantern cap'], 'Lantern', PLACE,
              [NEW_ASSY + ' and save it as lantern_topmark.iam.', 'Place lantern_body.ipt and Place Grounded.',
               'Place lantern_lens.ipt and lantern_cap.ipt on top (Mate, Insert).'], 'Bought in as one lantern.'),
             (['topmark strut 1', 'topmark strut 2', 'topmark strut 3'], 'Struts', PATTERN,
              ['Place topmark_strut.ipt at 30 degrees, its foot Mated to the lantern mounting plane; Circular Pattern 3.'], None),
             (['topmark plate', 'antenna'], 'Topmark plate and antenna', CONSTRAIN,
              ['Place topmark_plate.ipt on the struts (Mate). Place antenna.ipt on its centre (Mate, Insert).'], None),
             (['topmark'], 'Topmark', CONSTRAIN,
              ['Place topmark_can.ipt (red buoy) or topmark_cone.ipt (green buoy) over the antenna: Mate, Insert. Save.'],
              'Polyethylene lets the radio signals through to the antenna inside.'),
         ]),
    dict(no=6, key='mooring', title='mooring and alert pin', file='mooring.iam', explode=_explode_mooring(),
         desc='The mooring connection: the bow shackle, the load pin that is the alert sensor, the swivel and the first '
              'links of the chain.',
         steps=[
             (['bow shackle', 'load pin'], 'Shackle and load pin', PLACE,
              [NEW_ASSY + ' and save it as mooring.iam.', 'Place shackle.ipt and Place Grounded.',
               'Place load_pin.ipt in the shackle ears (Insert), connector to the right.'], None),
             (['swivel'], 'Swivel', CONSTRAIN, ['Place swivel.ipt: Tangent its top eye to the inside of the shackle bow.'], None),
             (['chain link %d' % (k + 1) for k in range(CHAIN_LINKS)], 'Chain', CONSTRAIN,
              ['Place chain_link.ipt: Tangent its crown to the bottom of the swivel eye, at 90 degrees to the eye.',
               'Place each next link the same way, turned 90 degrees. Save.'], 'The chain continues to the sinker.'),
         ]),
]
SINKER_SUB = dict(no=7, key='sinker', title='sinker and ground chain', file='sinker.iam',
                  explode={'concrete sinker': (0, 0, 0), 'sinker eye bar': (0, 0, 400), 'ground chain link 1': (0, 0, 560),
                           'ground chain link 2': (0, 0, 640), 'ground chain link 3': (0, 0, 720)},
                  desc='The sinker on the harbour bed: the concrete block with its cast in eye bar and the bottom links of '
                       'the chain. The chain between the sinker and the buoy is about 3 times the depth of water.',
                  steps=[
                      (['sinker eye bar'], 'Eye bar', PLACE, [NEW_ASSY + ' and save it as sinker.iam.',
                                                              'Place sinker_eye.ipt and Place Grounded.'], None),
                      (['concrete sinker'], 'Concrete block', CONSTRAIN,
                       ['Place sinker.ipt round the bar: Flush its top with the base of the eye, Flush the centre planes.'],
                       'At the works the bar is set in the mould and the concrete poured round it.'),
                      (['ground chain link 1', 'ground chain link 2', 'ground chain link 3'], 'Ground chain', CONSTRAIN,
                       ['Place chain_link.ipt round the eye (Tangent), then two more links. Save.'],
                       'Joined to the buoy chain with a joining shackle when the buoy is laid.'),
                  ])
SUBS.append(SINKER_SUB)
SUB = {d['key']: d for d in SUBS}
for _d in SUBS:
    if _d['key'] != 'sinker':
        _d['names'] = _names(_d['key'])
SINKER_SUB['names'] = [n for n, k, tf in sinker_instances()]


def sub_model_name(d):
    return 'esp2024_sa%d_%s' % (d['no'], d['key'])


def sub_items(key):
    """The instances of one sub-assembly: (name, part key, shape)."""
    if key == 'sinker':
        return sinker_items()
    by = {n: (k, s) for n, k, s in buoy_instances()}
    return [(n, by[n][0], by[n][1]) for n in SUB[key]['names']]


def sub_of(name):
    for n, k, tf, s in instances():
        if n == name:
            return s
    return None


def _sub_fn(d):
    def fn():
        return [(n, s, colour(k)) for n, k, s in sub_items(d['key'])]
    fn.__doc__ = d['desc']
    return fn


def _sub_bom(d):
    def fn():
        items = sub_items(d['key'])
        return bom([n for n, k, s in items], items)
    return fn


MODELS = [
    dict(name='esp2024_buoy', title='ESP 2024 harbour buoy (GA)', fn=buoy, criteria='3.1, 3.2',
         uses='ESP 2024 Task 2, Part B: the preferred design, a harbour lane marker buoy assembled from separate parts '
              '(red, leaving the harbour). General arrangement, parts list, section through the float, simulation of '
              'the buoy rolling in waves and drifting off when the chain breaks.',
         section='y', explode=None, iso=(-1, -1.3, 0.55), folder='ESP 2024', sim=True, fea=False, bom=_buoy_bom('red')),
    dict(name='esp2024_buoy_green', title='ESP 2024 harbour buoy, green (entrance)', fn=buoy_green, criteria='3.1',
         uses='ESP 2024 Task 2: the same buoy for entering the harbour: green float, green lens and a cone topmark.',
         section=None, explode=None, iso=(-1, -1.3, 0.55), folder='ESP 2024', fea=False, bom=_buoy_bom('green')),
    dict(name='esp2024_wind_buoy', title='ESP 2024 concept B: wind powered spherical buoy', fn=wind_buoy, criteria='3.1',
         uses='ESP 2024 Task 2, Part A: the second design idea, a steel spherical buoy with a lattice tower and a small '
              'wind turbine, for comparison with design A.', section=None, explode=None, iso=(-1, -1.3, 0.55),
         folder='ESP 2024', fea=False),
]

for _d in SUBS:
    MODELS.append(dict(
        name=sub_model_name(_d), title='ESP 2024 sub-assembly %d: %s' % (_d['no'], _d['title']), fn=_sub_fn(_d),
        criteria='3.1, 3.2', uses='ESP 2024 sub-assembly %s: %s' % (_d['file'], _d['desc']), description=_d['desc'],
        section=None, explode=_d['explode'], folder='ESP 2024', bom=_sub_bom(_d), fea=False,
        iso=(-1, -1.3, 0.7), sub=dict(no=_d['no'], key=_d['key'], file=_d['file'])))

for _p in PARTS:
    MODELS.append(dict(
        name=part_model_name(_p), title='ESP 2024 part %02d: %s' % (_p['no'], _p['name']), fn=_part_fn(_p),
        criteria='3.1', uses='ESP 2024 component, item %d on the parts list: %s. %s' % (_p['no'], _p['material'], _p['desc']),
        description=_p['desc'], section=None, explode=None, folder='ESP 2024', part=dict(no=_p['no'], key=_p['key'],
        group=_p['group'], material=_p['material'], file=_p['file'], bought=_p['bought']),
        fea=None if _p['key'] == 'mooring_eye' else False, media='still'))


# ------------------------------------------------------------------ key sizes for each part drawing
def _bar(z):
    return 2 * leg_r(z) * math.sin(math.radians(60)) + 16


SIZES = dict(
    float_hull=['Ø%d x %d high, %d wall' % (2 * FLOAT_R, FLOAT_TOP - FLOAT_BOT, WALL),
                'Top edge R%d, bottom edge R%d' % (FILLET_TOP, FILLET_BOT),
                'Fender groove Ø%d x %d, %d to %d up' % (2 * GROOVE[0], GROOVE[2] - GROOVE[1], GROOVE[1] - FLOAT_BOT, GROOVE[2] - FLOAT_BOT),
                'Well Ø%d x %d deep' % (2 * WELL_R, FLOAT_TOP - WELL_BOT), 'Tie rod holes Ø16 at R%d, 3 off' % TIE_R],
    float_foam=['Fills the shell: Ø%d x %d' % (2 * (FLOAT_R - WALL), FLOAT_TOP - FLOAT_BOT - 2 * WALL),
                'Round the well Ø%d' % (2 * (WELL_R + WALL))],
    fender=['Ø%d / Ø%d x %d' % (2 * GROOVE[0], 2 * FENDER_R, GROOVE[2] - GROOVE[1]), 'Outside edges R12'],
    deck_plate=['Ø%d / Ø286 x %d' % (2 * DECK_R, DECK[1] - DECK[0]), 'Holes Ø16 at R%d, 3 off' % TIE_R,
                'M12 tapped, 6 off, at R%d' % LEG_FOOT[0]],
    keel_plate=['Ø%d x %d' % (2 * KEEL_R, KEEL[1] - KEEL[0]), 'Holes Ø16 at R%d, 3 off' % TIE_R, 'M12 x 8 deep, 6 off, at R75'],
    tie_rod=['M16 x %d' % (DECK[1] + 14 - KEEL[0] + 15)],
    tie_rod_nut=['M16, 24 A/F x 13'],
    eye_nut=['M16, collar Ø34 x 15', 'Eye Ø%d inside, bar Ø%d' % (2 * (EYE_RING[0] - EYE_RING[1]), 2 * EYE_RING[1])],
    canister=['Ø%d x %d, %g wall, 4 base' % (2 * CAN_R, FLANGE[0] - WELL_BOT, CAN_T), 'Flange Ø%d x 8' % (2 * FLANGE[2]),
              'M10 tapped, %d off, at R%d' % (N_BOLTS, BOLT_PCD_R)],
    mounting_plate=['Ø272 x 8', 'Slot 80 x 20'],
    battery=['194 x 77 x 170', 'Terminals Ø14, 120 apart'],
    battery_strap=['Strip 25 x 3', 'Inside 77 x 170'],
    control_unit=['200 x 75 x 200', 'Heat sink 160 x 140 x 5'],
    hatch_seal=['O-ring Ø%d inside, 5 section' % (2 * SEAL_R - 5)],
    hatch_lid=['Ø%d x %d' % (2 * FLANGE[2], LID_T), 'Groove Ø%d / Ø%d x 5' % (2 * SEAL_R - 8, 2 * SEAL_R + 8),
               'Holes Ø11, %d off, at R%d' % (N_BOLTS, BOLT_PCD_R), 'M16 gland holes, 2 off, at R92'],
    hatch_bolt=['M10 x 16 thread', 'Button head Ø17 x 6, pin hex 6 A/F'],
    cable_gland=['M16 x %d thread' % LID_T, 'Hexagon 21 A/F x 16', 'Cable Ø7'],
    tail_tube=['Tube Ø88.9 x 3 x %d' % (KEEL[0] - TAIL_BOT), 'Flange Ø%d x 12, 6 holes Ø13 at R75' % (2 * TAIL_FLANGE[2]),
               'Bottom plate Ø%d x 10' % (2 * BOT_PLATE[2])],
    keel_bolt=['M12 x 20, 18 A/F head'],
    ballast=['Ø%d / Ø%d x %d' % (2 * BALLAST[0], 2 * BALLAST[1], BALLAST[2]), 'Top outside chamfer 15'],
    ballast_collar=['Ø88.9 / Ø170 x 15', 'Split 3'],
    anode=['Ø88.9 / Ø%d x %d' % (2 * ANODE[2], ANODE[1] - ANODE[0]), 'One split'],
    mooring_eye=['Plate %d thick, 90 wide' % EYE_T, 'End R45, hole Ø%d' % (2 * PIN_R + 2),
                 'Hole centre %d below the top' % (BOT_PLATE[0] - EYE_Z)],
    tripod_leg=['Tube Ø33.7 x 2', 'Centre line (%d, %d) to (%d, %d)' % (LEG_FOOT[0], LEG_FOOT[1] - M, LEG_TOP[0], LEG_TOP[1] - M),
                'Foot 54 x 92 x %d, holes Ø13, 68 apart' % (LEG_FOOT[1] - M)],
    leg_bolt=['M12 x 16, 18 A/F head'],
    top_plate=['Ø%d x %d' % (2 * TOP_PLATE[2], TOP_PLATE[1] - TOP_PLATE[0]), 'Cable hole Ø20'],
    bracket_lower=['Bar 6 x 40, %.0f long' % _bar(BRACKETS[0]), 'Two saddle tabs 16 wide'],
    bracket_upper=['Bar 6 x 40, %.0f long' % _bar(BRACKETS[1]), 'Two saddle tabs 16 wide'],
    solar_panel=['%d x %d x %d' % (PANEL[2], PANEL[4] - PANEL[3], PANEL[1]), 'Cells %d x %d' % (PANEL[2] - 24, PANEL[4] - PANEL[3] - 24)],
    lantern_body=['Flange Ø140 x 12', 'Body Ø110 x 28'],
    lantern_lens=['Ø104 x 100, 6 wall'],
    lantern_cap=['Ø116 x 12', 'Spike Ø6 x 28'],
    topmark_strut=['Flat bar %d x %d x %d' % (STRUT[2], STRUT[1], STRUT[4] - STRUT[3])],
    topmark_plate=['Ø%d x %d' % (2 * TM_PLATE[2], TM_PLATE[1] - TM_PLATE[0]), 'Hole Ø12'],
    antenna=['Ø90 x 18', 'Top edge R8'],
    topmark_can=['Ø%d x %d, %d wall' % (2 * CAN_TM[0], CAN_TM[3] - CAN_TM[2], CAN_TM[1])],
    topmark_cone=['Ø%d base x %d high, %d wall' % (2 * CONE_TM[0], CONE_TM[3] - CONE_TM[2], CONE_TM[1])],
    shackle=['Ears Ø36 x 14, 22 apart', 'Bar Ø%d, bow R%d' % (2 * SH_R, SH_LEG_X), 'Pin holes Ø%d' % (2 * PIN_R)],
    load_pin=['Pin Ø%d x 54' % (2 * PIN_R), 'Head Ø40 x 6', 'Connector Ø16 x 20'],
    swivel=['Eyes R%d centre line, bar Ø%d' % (SW_EYE[0], 2 * SW_EYE[1]),
            'Body Ø28', 'Eyes 90 apart'],
    chain_link=['Wire Ø%d' % CHAIN_D, 'Inside %d x %d (pitch %d)' % (LINK_PITCH, 2 * LINK_A - CHAIN_D, LINK_PITCH)],
    sinker=['%d x %d x %d' % (SINK[0], SINK[0], SINK[1]), 'Top chamfer 30'],
    sinker_eye=['Bar Ø%d' % (2 * SINK_EYE[1]), 'Legs 250, %d apart' % (2 * SINK_EYE[0]), 'Feet 60'],
)
for _p in PARTS:
    _p['sizes'] = SIZES[_p['key']]
for _m in MODELS:
    if _m.get('part'):
        _m['part']['sizes'] = PART[_m['part']['key']]['sizes']
