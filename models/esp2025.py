"""ESP 2025: an automated pill dispenser for a health trust, designed by Westview Biomedical Engineering Products
(WBEP) Ltd (T Level Employer-Set Project 8730-035, Summer 2025, Task 2).

The brief (product design specification): no bigger than 190 x 190 x 60 mm, any shape; no more than 0.5 kg with
the batteries; at least three pills in each compartment (a pill is a cylinder up to 20 long and 5 diameter);
battery powered; easy for the pharmacy to reprogram, refill and dispense: once a day medication refilled every 28
days, twice a day medication every 14 days; an alarm that sounds until the pills are dispensed; a 'press here'
button next to a flashing light for the patient to start the dispenser; tamper-proof with little maintenance; the
tablets held securely by a lock only the pharmacy can open; a recyclable casing; waterproof; suitable for repeated
use. Budget 65 pounds a unit for 1500 units (97,500 pounds), or 3000 units if they can be made for 40 pounds
(120,000 pounds). Labour 17 pounds an hour. 30 weeks for 1500 units, 35 weeks for 3000.

Design A (preferred): a round carousel dispenser, 180 across and 58 high. A carousel of 30 segments (28 pill
compartments and 2 blanks) turns over a deck with one drop hole. At each dose time the buzzer sounds and the light
beside the PRESS HERE button flashes; the patient presses the button, a worm drive turns the carousel one segment,
the pills fall through the hole and down a chute into the pull-out drawer, and the drop sensor in the chute stops
the alarm. 28 compartments are 28 days at one dose a day or 14 days at two. The clear lid is hinged at the back
and held shut by a cam lock that only the pharmacy key turns. The case is polypropylene (one recyclable plastic),
sealed by gaskets and O-rings so it is waterproof. Four AAA cells sit under two doors held by tamper-proof screws.
The pharmacy reprograms it with a phone or tablet by NFC (no socket, so nothing to let water in).
Design B (concept only): a rectangular cassette with 28 spring trapdoors (see cassette_dispenser()).

Every component is its own part (an Inventor .ipt), listed in PARTS below with its material and the features that
make it (the Inventor build steps). The six sub-assemblies and the dispenser are assemblies (.iam) of those parts.

Coordinates (mm): z = 0 is the underside of the bottom cover (the feet stand 3 mm lower), Z up, the axis of the
carousel is x = y = 0. The front (drawer and drop hole) is -Y; the hinge is at the back (+Y). The front view looks
along +Y. Angles are measured from +X towards +Y.
"""
import functools
import math
import cadquery as cq

# ------------------------------------------------------------------ the numbers that define the design
R_CASE = 90                     # outside radius of the case: 180 across (brief: 190 max)
WALL = 2.0                      # chassis wall, PP
R_IN = R_CASE - WALL            # 88, inside of the chassis wall
COVER = (0, 2)                  # bottom cover plate z
GASKET = (88.3, 89.8)           # gasket ring radii (the same part between cover and chassis, and chassis and lid)
CH_Z = (3, 32)                  # chassis wall from z, to z (a gasket 1 thick under it)
DECK = (28, 30)                 # deck (the floor the pills sit on) z
CAR_Z = (30, 50)                # carousel z
HUB = (39.5, 41.5)              # carousel hub tube inside and outside radius
HUB_BOT = 4.5                   # bottom of the hub tube (the drive gear is pressed on it)
CAR_OUT = (78, 79.5)            # carousel outer ring radii: 1.5 inside the lid catch, which swings in a little as the lid opens
N_SEG, SEG = 30, 12             # 30 segments of 12 degrees: 28 compartments and 2 blanks
RIB = 1.0                       # rib between compartments
DROP = (44, 78, 10.4)           # drop hole in the deck: from radius, to radius, angular width (degrees), at -90
HOME = -90                      # the drop hole is at the front
LID_Z = (33, 54)                # lid z (the gasket under it is 32 to 33)
LID_T, LID_TOP = 1.8, 2.0       # lid wall and top thickness
LID_HOLE = 36.5                 # hole in the lid round the control pod
COLLAR = (LID_HOLE, 38.0, 43.5)  # collar round the hole: inside radius, outside radius, bottom z
HINGE = (93.5, 34, 3.5)         # hinge axis y, z and knuckle radius
PIN_R = 1.5                     # hinge pin 3 diameter
POD_R = (32, 35)                # pod column inside and outside radius
POD_TOP = 51.5                  # top of the pod column (the pod cap sits on it)
GROOVE = (43.75, 46.75, 33.5)   # O-ring groove in the pod column: z0, z1, groove bottom radius
PCB_Z = (42.5, 44.1)            # panel PCB z
BTN = (0, -14)                  # PRESS HERE button centre
LED_XY = (20, -6)               # flashing light beside the button
BUZ_XY = (-20, -6)              # buzzer
GEAR_Z = (4.5, 9.5)             # drive gear (worm wheel) z
GEAR_N, GEAR_M = 120, 0.8       # teeth, module: pitch diameter 96
GEAR_RP = GEAR_N * GEAR_M / 2   # 48
GEAR_RA, GEAR_RF = GEAR_RP + GEAR_M, GEAR_RP - 1.25 * GEAR_M   # tip and root radius
WORM_R = (2.0, 3.8)             # worm root and tip radius
WORM_PITCH = math.pi * GEAR_M   # 2.513: one turn of the single start worm moves the wheel one tooth
WORM_Y = GEAR_RA + WORM_R[1]    # worm axis y: drawn tip to tip with the wheel (the teeth are simplified)
WORM_ZC = (GEAR_Z[0] + GEAR_Z[1]) / 2   # 7.0, worm and motor axis z
FLAG_ANG = 150                  # home mark (a hole in the gear) and the home sensor under it, at the home position
HOME_R = 44                      # radius of the home mark and the sensor
LOCK_ANG = -55                  # the pharmacy lock: radial, front right
CAM_R = (84.5, 87)              # lock cam plate from radius, to radius (on the end of the lock barrel)
LOCK_Z = 16                     # lock axis height
BOSS_R, BOSS_ANG = 60, (45, 135, 225, 315)   # screw bosses joining the cover to the chassis
FOOT = (70, 6, 3)               # feet: radius from the axis, foot radius, height
BAT = (56, 78, 24)              # battery holder x from, x to, half length (right hand one; the left is mirrored)
BAT_X = (61.7, 72.3)            # AAA cell axes (along Y)
BAT_ZC = 8.0                    # cell axis height
AAA = (5.25, 44.5)              # AAA cell radius and length
DOOR_OPEN = (58, 76, 21)        # battery door opening in the cover: x from, x to, half width in y
DOOR = (55, 79, 31)             # battery door flange
DOOR_SCREW = (67, 27.5)         # security screw positions (x, +-y)
DRAWER = (22, 10, 20.5, -42.5)  # drawer tub half width, bottom z, top z, back y
DRAWER_OPEN = (23, 9.5, 21)     # opening in the chassis front wall: half width, z0, z1
CHUTE = (9, 21, -81, -42.5, 1.5)  # chute outside half width, bottom z, front y, back y, wall
PCB = (30, 66, 79)              # main PCB half width, y from, y to

# colours
PP_C = 'E9ECEF'         # white polypropylene case
CLEAR = 'BFD9EE'        # clear (clarified) polypropylene lid and window
CAR_C = 'F2F4F6'        # natural PP carousel
BLUE = '2C5AA0'         # WBEP blue for the pod cap and drawer
GREEN = '2E9E5B'        # PRESS HERE button
AMBER = 'F2A623'        # flashing light
RUBBER = '3A3A3A'
PCB_C = '1E6B3A'
POM_C = 'F7F3E8'
STEEL_C = 'A9B4BF'
DARK = '2B2B2B'
BRASS_C = 'C9A44B'
BAT_C = '3366AA'
LCD_C = '4F6F5A'

# Inventor commands
NEW_PART = 'File > New > Standard (mm).ipt'
SKETCH = '3D Model tab > Sketch panel > Start 2D Sketch'
EXTRUDE = '3D Model tab > Create panel > Extrude'
REVOLVE = '3D Model tab > Create panel > Revolve'
SWEEP = '3D Model tab > Create panel > Sweep'
EMBOSS = '3D Model tab > Create panel > Emboss'
HOLE = '3D Model tab > Modify panel > Hole'
FILLET = '3D Model tab > Modify panel > Fillet'
CHAMFER = '3D Model tab > Modify panel > Chamfer'
SHELL = '3D Model tab > Modify panel > Shell'
CIRC_PATTERN = '3D Model tab > Pattern panel > Circular Pattern'
RECT_PATTERN = '3D Model tab > Pattern panel > Rectangular Pattern'
MIRROR_F = '3D Model tab > Pattern panel > Mirror'
NEW_ASSY = 'File > New > Standard (mm).iam'
PLACE = 'Assemble tab > Component panel > Place'
CONTENT = 'Assemble tab > Component panel > Place from Content Center'
CONSTRAIN = 'Assemble tab > Relationships panel > Constrain'
PATTERN = 'Assemble tab > Pattern panel > Pattern'
MIRROR_C = 'Assemble tab > Pattern panel > Mirror'

# densities, kg/m3 (a bought in part has the density that gives its catalogue mass)
PP_D = 905              # polypropylene (case, carousel, drawer): recycling code 5
CPP_D = 900             # clarified (clear) polypropylene
PPGF_D = 1120           # polypropylene, 30 % glass filled (lid catch)
POM_D = 1410            # acetal (worm and drive gear: low friction, no grease)
SIL_D = 1150            # silicone rubber (gaskets, O-ring, button)
TPE_D = 1100            # feet
SS_D = 8000             # A2 stainless steel
ZN_D = 6600             # zinc die cast (lock body)
STEEL_D = 7850


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


def ycyl(r, y0, y1, x=0, z=0):
    return cyl(r, (x, y0, z), (0, 1, 0), y1 - y0)


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


def sector(r0, r1, a0, a1, z0, z1):
    """A ring segment from angle a0 to a1 (degrees)."""
    pts = [polar(r0, a0)[:2]]
    n = max(4, int(abs(a1 - a0) / 2))
    pts += [polar(r1, a0 + (a1 - a0) * k / n)[:2] for k in range(n + 1)]
    pts += [polar(r0, a1 - (a1 - a0) * k / n)[:2] for k in range(n + 1)]
    return cq.Workplane('XY').polyline(pts).close().extrude(z1 - z0).translate((0, 0, z0))


def F(title, command, actions, shape, note=None):
    """One feature of a part: what you do in Inventor and the part as it stands afterwards."""
    return dict(title=title, command=command, actions=actions, shape=shape, note=note)


def at_lock(w):
    """Parts of the lock are drawn on the front (along -Y, the lock axis at x = 0), then turned to the lock angle."""
    return rotz(w, LOCK_ANG + 90)


# ------------------------------------------------------------------ the parts
PARTS = []
GROUPS = [('chassis', 'Chassis, pharmacy lock and chute (SA1)'), ('carousel', 'Carousel and drive gear (SA2)'),
          ('base', 'Base: bottom cover, batteries and drive (SA3)'),
          ('pod', 'Control pod: display, PRESS HERE button, light and alarm (SA4)'),
          ('lid', 'Lid and hinge (SA5)'), ('drawer', 'Dispensing drawer (SA6)')]


def part(key, name, group, material, colour, density, desc, origin=(0, 0, 0), file=None, bought=False, recyclable=False):
    def deco(fn):
        PARTS.append(dict(key=key, name=name, group=group, material=material, colour=colour, density=density,
                          desc=desc, origin=origin, feats=fn, file=file or key + '.ipt', bought=bought,
                          recyclable=recyclable))
        return fn
    return deco


# ---------------------------------------------------- SA1 chassis, lock and chute
def drop_hole(z0, z1):
    return sector(DROP[0], DROP[1], HOME - DROP[2] / 2, HOME + DROP[2] / 2, z0, z1)


def catch_notch(z0, z1):
    """Slot in the deck for the lid catch to pass through."""
    return at_lock(catch_band(CATCH['r'][0] - SLOT_GAP, R_IN + 1, z0, z1, 1))


def knuckle(x0, x1):
    y, z, r = HINGE
    return xcyl(r, x0, x1, y, z)


@part('chassis', 'chassis', 'chassis', 'Polypropylene (PP) homopolymer, white, 2 wall, injection moulded', PP_C, PP_D,
      'The main moulding: the round wall of the case and the deck the pills sit on, in one piece. The deck has the '
      'drop hole at the front; the wall has the drawer opening, the hole for the pharmacy lock and the two hinge '
      'knuckles. Four bosses under the deck take the screws that hold the bottom cover on.', origin=(0, 0, CH_Z[0]),
      recyclable=True)
def _chassis():
    z0, z1 = CH_Z
    f1 = ring(R_IN, R_CASE, z0, z1).union(zcyl(R_IN, DECK[0], DECK[1]))
    f2 = f1.cut(zcyl(HUB[1] + 1, DECK[0] - 1, DECK[1] + 1))
    f3 = f2.cut(drop_hole(DECK[0] - 1, DECK[1] + 1))
    bosses = union(*[zcyl(4, COVER[1], DECK[0], *polar(BOSS_R, a)[:2]) for a in BOSS_ANG])
    f4 = f3.union(bosses).cut(union(*[zcyl(1.25, COVER[1] - 1, COVER[1] + 10, *polar(BOSS_R, a)[:2]) for a in BOSS_ANG]))
    w, za, zb = DRAWER_OPEN
    f5 = f4.cut(box(-w, w, -R_CASE - 5, -R_IN + 3, za, zb))
    f6 = f5.cut(at_lock(ycyl(8, -R_CASE - 1, -R_IN + 1, 0, LOCK_Z)))
    y, zh, r = HINGE
    lugs = union(*[box(s * 16 if s > 0 else -44, 44 if s > 0 else -16, 78, y, 26, 32).union(knuckle(*sorted((s * 16, s * 44))))
                   for s in (1, -1)]).cut(zcyl(R_IN, 0, 40))
    f7 = f6.union(lugs).cut(xcyl(PIN_R, -50, 50, y, zh))
    f8 = f7.cut(catch_notch(DECK[0] - 1, DECK[1] + 1))
    return [
        F('Wall', REVOLVE, [NEW_PART + ' and save it as chassis.ipt.',
                            'Start 2D Sketch on the XZ Plane: circles diameter %d and %d. Extrude %d mm (the wall).'
                            % (2 * R_CASE, 2 * R_IN, z1 - z0),
                            'Sketch a circle diameter %d on the XZ Plane, offset %d mm. Extrude %d mm, Join (the deck).'
                            % (2 * R_IN, DECK[0] - z0, DECK[1] - DECK[0])], f1,
          'One moulding in polypropylene: the same plastic as every other moulded part, so the case recycles as one.'),
        F('Hub hole', HOLE, ['Hole on the deck, on the centre: diameter %d, Through All.' % (2 * HUB[1] + 2)], f2,
          'The hub of the carousel passes down through this hole to the drive gear.'),
        F('Drop hole', EXTRUDE, ['Sketch on the deck: a ring segment from radius %d to %d, %.1f degrees wide, at the '
                                 'front. Extrude Cut Through All.' % DROP], f3,
          'Only one compartment is ever over this hole, so the patient can only ever get one dose.'),
        F('Screw bosses', EXTRUDE, ['Sketch circles diameter 8 at radius %d on 45 degrees, under the deck. Extrude down '
                                    'to the bottom of the wall. Circular Pattern 4.' % BOSS_R,
                                    'Hole diameter 2.5, 10 deep, from the bottom of each boss (for the cover screws).'], f4),
        F('Drawer opening', EXTRUDE, ['Sketch a %d x %.1f rectangle on the XY Plane at the front, %.1f up. Extrude Cut '
                                      'through the front wall.' % (2 * w, zb - za, za - z0)], f5),
        F('Lock hole', HOLE, ['Work plane at %d degrees. Hole diameter 16 through the wall, %d up from the bottom of the '
                              'case, for the pharmacy cam lock.' % (LOCK_ANG, LOCK_Z)], f6),
        F('Hinge knuckles', EXTRUDE, ['Sketch the two lugs on the YZ Plane at the back and extrude them 28 mm each side '
                                      'of the middle, 16 to 44 mm out; add a circle radius %.1f at y %.1f, z %.0f and '
                                      'Extrude, Join.' % (r, y, zh),
                                      'Hole diameter %d along the hinge axis, Through All.' % (2 * PIN_R)], f7,
          'The lid knuckle fits between them.'),
        F('Catch slot', EXTRUDE, ['Sketch a %g x %g rectangle on the deck at the edge, at %d degrees. Extrude Cut Through '
                                  'All. Save.' % (CATCH['x'][1] - CATCH['x'][0] + 2, R_IN + 1 - CATCH['r'][0] + SLOT_GAP, LOCK_ANG)], f8, 'The catch on the lid passes down through this slot to '
                                                                 'the cam of the lock.'),
    ]


@part('pharmacy_lock', 'pharmacy cam lock', 'chassis', 'Bought in: 16 mm cam lock, zinc die cast, pharmacy key (keyed alike)',
      STEEL_C, ZN_D, 'Cam lock in the front right of the case. Only the pharmacy has the key: a quarter turn swings '
      'the cam out of the way of the lid catch so the lid can be opened to refill.', origin=polar(R_CASE, LOCK_ANG, LOCK_Z), bought=True)
def _pharmacy_lock():
    f1 = at_lock(ycyl(10, -R_CASE - 2, -R_CASE, 0, LOCK_Z).union(ycyl(8, -R_CASE, -87, 0, LOCK_Z)))
    f2 = f1.cut(at_lock(box(-1, 1, -R_CASE - 3, -R_CASE - 0.8, LOCK_Z - 4, LOCK_Z + 4)))
    return [F('Head and barrel', REVOLVE, [NEW_PART + ' and save it as pharmacy_lock.ipt (or download the maker\'s model).',
                                           'Revolve: head diameter 20 x 2, barrel diameter 16 x 3.'], f1),
            F('Key slot', EXTRUDE, ['Sketch a 2 x 8 slot on the head. Extrude Cut 1.2 deep. Save.'], f2,
              'Keyed alike: one pharmacy key opens every dispenser; patients do not have one.')]


@part('lock_cam', 'lock cam', 'chassis', 'Zinc plated steel, 2.5 thick', STEEL_C, STEEL_D,
      'The cam on the end of the lock barrel. Locked, it lies over the hook of the lid catch so the lid cannot lift; '
      'unlocked, it points up, clear of the hook.', origin=polar(87, LOCK_ANG, LOCK_Z))
def _lock_cam():
    r0, r1 = CAM_R
    f1 = at_lock(ycyl(4, -r1, -r0, 0, LOCK_Z).union(box(-11.5, 0, -r1, -r0, LOCK_Z - 3.5, LOCK_Z + 3.5)))
    f2 = f1.cut(at_lock(box(-1.5, 1.5, -r1 - 1, -r0 + 1, LOCK_Z - 1.5, LOCK_Z + 1.5)))
    return [F('Cam plate', EXTRUDE, [NEW_PART + ' and save it as lock_cam.ipt.',
                                     'Sketch a circle diameter 8 and an arm 11.5 x 7 from it. Extrude %g mm.' % (CAM_R[1] - CAM_R[0])], f1),
            F('Square hole', EXTRUDE, ['Sketch a 3 x 3 square on the centre. Extrude Cut Through All. Save.'], f2,
              'The square end of the lock barrel turns the cam.')]


@part('chute', 'dispensing chute', 'chassis', 'Polypropylene (PP), 1.5 wall, injection moulded', PP_C, PP_D,
      'A short square tube under the drop hole that guides the falling pills into the drawer. The drop sensors look '
      'across it through two small windows.', origin=(0, CHUTE[3], CHUTE[1]), recyclable=True)
def _chute():
    w, z0, y0, y1, t = CHUTE
    f1 = box(-w, w, y0, y1, z0, DECK[0])
    f2 = f1.cut(box(-w + t, w - t, y0 + t, y1 - t, z0 - 1, DECK[0] + 1))
    f3 = f2.cut(xcyl(1.5, -w - 1, w + 1, -60, 24.5))
    return [F('Block', EXTRUDE, [NEW_PART + ' and save it as chute.ipt.',
                                 'Sketch an %d x %d rectangle. Extrude %d mm.' % (2 * w, y1 - y0, DECK[0] - z0)], f1),
            F('Hollow it', SHELL, ['Shell: remove the top and bottom faces, thickness %g. Click OK.' % t], f2),
            F('Sensor windows', HOLE, ['Hole diameter 3 through both side walls, 19 mm from the front, 3.5 mm from the '
                                       'top. Save.'], f3, 'The infrared beam crosses the chute here.')]


@part('drop_sensor', 'drop sensor (infrared)', 'chassis', 'Bought in: 3 mm infrared LED or photodiode in a black PBT housing',
      DARK, 1300, 'An infrared emitter on one side of the chute and a receiver on the other. When the pills fall '
      'through the beam the control unit knows the dose has been dispensed and stops the alarm.',
      origin=(CHUTE[0], -60, 24.5), bought=True)
def _drop_sensor():
    w = CHUTE[0]
    f1 = box(w, w + 3.5, -63, -57, 22, 27)
    f2 = f1.union(xcyl(1.5, w - CHUTE[4], w, -60, 24.5))
    return [F('Housing', EXTRUDE, [NEW_PART + ' and save it as drop_sensor.ipt.', 'Sketch 6 x 5. Extrude 3.5 mm.'], f1),
            F('Lens', EXTRUDE, ['Sketch a circle diameter 3 on the face. Extrude 1.5 mm. Save.'], f2,
              'The lens sits in the window of the chute.')]


# ---------------------------------------------------- SA2 carousel and drive gear
def seg_centre(k):
    """Angle of the middle of segment k when the carousel is at home (segment 0, a blank, over the drop hole)."""
    return HOME - SEG * k


BLANKS = (0, N_SEG - 1)


@part('carousel', 'carousel', 'carousel', 'Polypropylene (PP), natural, injection moulded', CAR_C, PP_D,
      'The carousel: 30 segments of 12 degrees between an inner and outer ring, with no bottom: the pills sit on the '
      'deck and are pushed round by the ribs. 28 segments hold a dose each; the 2 blanks are capped so nothing can be '
      'put in them. The hub tube goes down through the deck to the drive gear.', origin=(0, 0, HUB_BOT), recyclable=True)
def _carousel():
    z0, z1 = CAR_Z
    f1 = ring(HUB[0], HUB[1], z0, z1).union(ring(CAR_OUT[0], CAR_OUT[1], z0, z1))
    f2 = f1.union(ring(HUB[0], HUB[1], HUB_BOT, z0))
    rib = box(HUB[1] - 0.5, CAR_OUT[0] + 0.5, -RIB / 2, RIB / 2, z0, z1)
    f3 = f2.union(union(*[rotz(rib, seg_centre(k) + SEG / 2) for k in range(N_SEG)]))
    caps = union(*[sector(HUB[1] - 0.5, CAR_OUT[0] + 0.5, seg_centre(k) - SEG / 2, seg_centre(k) + SEG / 2, z1 - 1.5, z1)
                   for k in BLANKS])
    f4 = f3.union(caps)
    keys = union(*[rotz(box(HUB[0] - 1.2, HUB[0] + 0.1, -1, 1, HUB_BOT, HUB_BOT + 6), a) for a in (0, 120, 240)])
    f5 = f4.union(keys)
    return [
        F('Rings', REVOLVE, [NEW_PART + ' and save it as carousel.ipt.',
                             'Sketch circles diameter %d and %d, and %d and %d on the XZ Plane. Extrude %d mm.'
                             % (2 * HUB[0], 2 * HUB[1], 2 * CAR_OUT[0], 2 * CAR_OUT[1], z1 - z0)], f1),
        F('Hub tube', EXTRUDE, ['Extrude the inner ring down %.1f mm, Join.' % (z0 - HUB_BOT)], f2,
          'The tube passes down through the deck; the drive gear is pressed onto its end.'),
        F('Ribs', CIRC_PATTERN, ['Sketch one rib %g thick from the inner to the outer ring. Extrude %d mm, Join.'
                                 % (RIB, z1 - z0), 'Circular Pattern: %d ribs at %d degrees.' % (N_SEG, SEG)], f3,
          'Each 12 degree segment holds one dose: a press of the button turns the carousel one segment.'),
        F('Caps on the 2 blanks', EXTRUDE, ['Sketch the two segments either side of the front rib. Extrude 1.5 mm down '
                                            'from the top, Join.'], f4,
          'The blank under the drop hole is where the carousel waits when it is filled, so no pills can fall out while '
          'the pharmacy loads it.'),
        F('Drive keys', CIRC_PATTERN, ['Sketch a 2 x 1.3 key inside the bottom of the hub tube. Extrude 6 mm, Join.',
                                       'Circular Pattern 3. Save.'], f5, 'The drive gear has three slots that fit these keys.'),
    ]


def gear_outline():
    pts = []
    for k in range(GEAR_N):
        a = 360.0 * k / GEAR_N
        for r, da in ((GEAR_RF, -0.9), (GEAR_RA, -0.4), (GEAR_RA, 0.4), (GEAR_RF, 0.9)):
            pts.append(polar(r, a + da)[:2])
    return pts


@part('drive_gear', 'drive gear (worm wheel)', 'carousel', 'Acetal (POM), injection moulded, %d teeth module %g' % (GEAR_N, GEAR_M),
      POM_C, POM_D, 'The worm wheel, pressed onto the bottom of the carousel hub. The worm turns it one tooth for every '
      'turn, so the carousel moves slowly and exactly, and the worm cannot be turned back by forcing the carousel. '
      'A small hole in it tells the home sensor where the carousel is.', origin=(0, 0, GEAR_Z[0]))
def _drive_gear():
    z0, z1 = GEAR_Z
    f1 = cq.Workplane('XY').polyline(gear_outline()).close().extrude(z1 - z0).translate((0, 0, z0))
    f2 = f1.cut(zcyl(HUB[1], z0 - 1, z1 + 1))
    f3 = f2.cut(union(*[rotz(box(HUB[1] - 0.2, HUB[1] + 1.2, -1, 1, z0 - 1, z1 + 1), a) for a in (0, 120, 240)]))
    f4 = f3.cut(zcyl(1.5, z0 - 1, z1 + 1, *polar(HOME_R, FLAG_ANG)[:2]))
    return [F('Gear blank and teeth', EXTRUDE, [NEW_PART + ' and save it as drive_gear.ipt.',
                                                'Design tab > Power Transmission > Spur Gear: %d teeth, module %g, '
                                                'face width %d (or sketch one tooth and Circular Pattern %d).'
                                                % (GEAR_N, GEAR_M, z1 - z0, GEAR_N)], f1,
              'Teeth drawn simplified (straight). A real worm wheel has a curved (throated) face to wrap round the worm.'),
            F('Bore', HOLE, ['Hole diameter %d on the centre, Through All.' % (2 * HUB[1])], f2),
            F('Key slots', CIRC_PATTERN, ['Sketch a 2 x 1.4 slot in the bore. Extrude Cut Through All. Circular Pattern 3.'], f3),
            F('Home mark', HOLE, ['Hole diameter 3, Through All, on radius %d at %d degrees. Save.' % (HOME_R, FLAG_ANG)], f4,
              'At home the hole is over the home sensor. Nothing sticks out, so the gear passes the worm all the way round.')]


# ---------------------------------------------------- SA3 base: bottom cover, batteries and drive
@part('bottom_cover', 'bottom cover', 'base', 'Polypropylene (PP), white, 2 thick, injection moulded', PP_C, PP_D,
      'The bottom of the case. The batteries, the main circuit board and the drive sit on it, the control pod stands '
      'in a socket in the middle, and four screws pull it up against the gasket under the chassis.',
      origin=(0, 0, 0), recyclable=True)
def _bottom_cover():
    f1 = zcyl(R_CASE, *COVER)
    f1 = f1.faces('<Z').edges().fillet(1.5)
    f2 = f1.union(ring(86, R_IN - 0.1, COVER[1], 6))
    f3 = f2.union(ring(POD_R[1], POD_R[1] + 2, COVER[1], 6))
    x0, x1, h = DOOR_OPEN
    opens = box(x0, x1, -h, h, -1, COVER[1] + 1)
    f4 = f3.cut(opens).cut(opens.mirror('YZ'))
    bos = union(*[zcyl(2.5, COVER[1], 6, s * DOOR_SCREW[0], t * DOOR_SCREW[1]) for s in (1, -1) for t in (1, -1)])
    holes = union(*[zcyl(1.1, -1, 6.5, s * DOOR_SCREW[0], t * DOOR_SCREW[1]) for s in (1, -1) for t in (1, -1)])
    f5 = f4.union(bos).cut(holes)
    csk = union(*[cq.Workplane('XY').add(cq.Solid.makeCone(3.0, 1.25, 1.75, cq.Vector(*polar(BOSS_R, a, -0.01)))).union(
        zcyl(1.25, -1, 3, *polar(BOSS_R, a)[:2])) for a in BOSS_ANG])
    f6 = f5.cut(csk)
    return [
        F('Plate', EXTRUDE, [NEW_PART + ' and save it as bottom_cover.ipt.',
                             'Sketch a circle diameter %d on the XZ Plane. Extrude %d mm. Fillet the bottom edge 1.5.'
                             % (2 * R_CASE, COVER[1])], f1),
        F('Locating rim and pod socket', EXTRUDE, ['Sketch circles diameter 172 and %.1f, and %d and %d. Extrude 4 mm, Join.'
                                                   % (2 * R_IN - 0.2, 2 * POD_R[1], 2 * POD_R[1] + 4)], f3,
          'The rim locates the cover inside the chassis wall; the control pod stands in the socket.'),
        F('Battery door openings', EXTRUDE, ['Sketch an %d x %d rectangle %d mm right of the centre. Extrude Cut Through '
                                             'All. Mirror it to the left.' % (x1 - x0, 2 * h, x0)], f4),
        F('Door screw bosses', EXTRUDE, ['Sketch circles diameter 5 at x %d, y %.1f. Extrude 4 mm, Join; Mirror twice.'
                                         % DOOR_SCREW,
                                         'Hole diameter 2.2 up through each boss (for the security screws).'], f5),
        F('Cover screw holes', HOLE, ['Hole: countersunk 6 x 90 degrees, diameter 2.5, Through All, at radius %d on 45 '
                                      'degrees; Circular Pattern 4. Save.' % BOSS_R], f6,
          'The screws go up into the bosses under the deck of the chassis.'),
    ]


@part('foot', 'rubber foot', 'base', 'Thermoplastic elastomer (TPE), black, self adhesive', RUBBER, TPE_D,
      'Four soft feet so the dispenser does not slide on a table when the button is pressed or the drawer pulled.',
      origin=polar(FOOT[0], 45, -FOOT[2]))
def _foot():
    x, y, _ = polar(FOOT[0], 45)
    f1 = zcyl(FOOT[1], -FOOT[2], 0, x, y)
    f2 = f1.faces('<Z').edges().fillet(1.5)
    return [F('Disc', EXTRUDE, [NEW_PART + ' and save it as foot.ipt.', 'Circle diameter %d. Extrude %d mm.' % (2 * FOOT[1], FOOT[2])], f1),
            F('Round edge', FILLET, ['Fillet the bottom edge 1.5. Save.'], f2)]


@part('main_pcb', 'main circuit board', 'base', 'Bought in: FR4 board 1.6 thick with microcontroller, clock, NFC and motor driver',
      PCB_C, 2600, 'The control unit: a low power microcontroller with a real time clock keeps the dose times, drives '
      'the motor, reads the sensors and the button, sounds the alarm and flashes the light. The pharmacy programs it '
      'with a phone or tablet through the NFC antenna printed round the edge of the board.', origin=(0, PCB[1], COVER[1]), bought=True)
def _main_pcb():
    w, y0, y1 = PCB
    f1 = box(-w, w, y0, y1, COVER[1], COVER[1] + 1.6)
    z = COVER[1] + 1.6
    f2 = f1.union(box(-6, 6, 69, 75, z, z + 1.4)).union(box(10, 16, 70, 74, z, z + 1.2)).union(box(-24, -14, 70, 75, z, z + 5))
    return [F('Board', EXTRUDE, [NEW_PART + ' and save it as main_pcb.ipt.', 'Sketch %d x %d. Extrude 1.6 mm.' % (2 * w, y1 - y0)], f1),
            F('Main components', EXTRUDE, ['Microcontroller 12 x 6, motor driver 6 x 4, connector 10 x 5 x 5 for the '
                                           'pod cable. Extrude, Join. Save.'], f2,
              'Modelled only as blocks, to check the space. The NFC antenna is a copper track round the board.')]


@part('battery_holder', 'battery holder 2 x AAA', 'base', 'Bought in: ABS battery holder for 2 x AAA with springs', DARK, 1300,
      'Holds two AAA cells. The two holders are wired in series: 4 x AAA, 6 V. The cells go in from underneath '
      'through the battery door.', origin=(BAT[0], -BAT[2], COVER[1]), bought=True)
def _battery_holder():
    x0, x1, h = BAT
    f1 = box(x0, x1, -h, h, COVER[1], 14)
    pockets = union(*[ycyl(AAA[0] + 0.05, -AAA[1] / 2, AAA[1] / 2, x, BAT_ZC) for x in BAT_X])
    f2 = f1.cut(pockets).cut(box(DOOR_OPEN[0] + 0.5, DOOR_OPEN[1] - 0.5, -AAA[1] / 2, AAA[1] / 2, COVER[1] - 1, BAT_ZC))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as battery_holder.ipt.', 'Sketch %d x %d. Extrude 12 mm.' % (x1 - x0, 2 * h)], f1),
            F('Cell pockets', EXTRUDE, ['Sketch two circles diameter 10.6, %.1f apart, on the end face. Extrude Cut %.1f '
                                        'mm. Cut the bottom open for loading. Save.' % (BAT_X[1] - BAT_X[0], AAA[1])], f2)]


@part('battery', 'AAA cell', 'base', 'Bought in: AAA alkaline cell 1.5 V, about 1100 mAh (or NiMH rechargeable)', BAT_C, 2950,
      'A standard AAA cell. Four of them run the dispenser for many months (see the calculation sheet); the pharmacy changes them at a refill '
      'when the display shows low battery.', origin=(BAT_X[0], -AAA[1] / 2, BAT_ZC), bought=True)
def _battery():
    x = BAT_X[0]
    f1 = ycyl(AAA[0], -AAA[1] / 2, AAA[1] / 2 - 0.8, x, BAT_ZC)
    f2 = f1.union(ycyl(1.8, AAA[1] / 2 - 0.8, AAA[1] / 2, x, BAT_ZC))
    return [F('Cell', EXTRUDE, [NEW_PART + ' and save it as battery.ipt.', 'Circle diameter 10.5. Extrude 43.7 mm.'], f1),
            F('Positive terminal', EXTRUDE, ['Circle diameter 3.6 on the end. Extrude 0.8 mm, Join. Save.'], f2)]


MOTOR_X = (17, 51)      # gear motor from x (gearbox face), to x (end cap): the gearbox clears the gear teeth
SHAFT = (-7, MOTOR_X[0])   # motor shaft (long shaft version), through the worm
CLAMP_X = (MOTOR_X[0] + 13, MOTOR_X[0] + 21)   # motor clamp, over the motor body


def motor_body(x0, x1):
    return xcyl(6, x0, x1, WORM_Y, WORM_ZC).intersect(box(x0, x1, WORM_Y - 7, WORM_Y + 7, WORM_ZC - 5, WORM_ZC + 5))


@part('gear_motor', 'gear motor 6 V', 'base', 'Bought in: N20 metal gear motor, 6 V, 200:1, 150 rpm, with D shaft', STEEL_C, 3000,
      'A small DC gear motor. It turns the worm 4 times for each dose: 4 teeth of the drive gear, 12 degrees of the '
      'carousel. It only runs for under 2 seconds a dose.', origin=(MOTOR_X[0], WORM_Y, WORM_ZC), bought=True)
def _gear_motor():
    x0, x1 = MOTOR_X
    f1 = box(x0, x0 + 9, WORM_Y - 6, WORM_Y + 6, WORM_ZC - 5, WORM_ZC + 5).union(motor_body(x0 + 9, x1 - 3))
    f2 = f1.union(motor_body(x1 - 3, x1).intersect(box(x1 - 3, x1, WORM_Y - 5, WORM_Y + 5, WORM_ZC - 5, WORM_ZC + 5)))
    f3 = f2.union(xcyl(1.5, SHAFT[0], SHAFT[1], WORM_Y, WORM_ZC))
    return [F('Gearbox', EXTRUDE, [NEW_PART + ' and save it as gear_motor.ipt (or download the maker\'s model).',
                                   'Sketch 12 x 10. Extrude 9 mm.'], f1),
            F('Motor and end cap', EXTRUDE, ['Sketch a circle diameter 12 with flats 10 apart. Extrude 22 mm, Join; end '
                                             'cap 10 x 10 x 3.'], f2),
            F('Shaft', EXTRUDE, ['Circle diameter 3 on the gearbox face. Extrude %d mm. Save.' % (SHAFT[1] - SHAFT[0])], f3)]


@part('motor_clamp', 'motor clamp', 'base', 'Polypropylene (PP), injection moulded', PP_C, PP_D,
      'A U-shaped clamp over the motor. Its legs clip into the bottom cover, so the motor cannot move away from the gear.',
      origin=(CLAMP_X[0], WORM_Y, COVER[1]), recyclable=True)
def _motor_clamp():
    y, z = WORM_Y, WORM_ZC
    f1 = box(CLAMP_X[0], CLAMP_X[1], y - 8, y + 8, COVER[1], z + 7)
    f2 = f1.cut(box(CLAMP_X[0] - 1, CLAMP_X[1] + 1, y - 6, y + 6, COVER[1] - 1, z + 5))
    return [F('Block', EXTRUDE, [NEW_PART + ' and save it as motor_clamp.ipt.', 'Sketch 16 x %d. Extrude 8 mm.' % (z + 7 - COVER[1])], f1),
            F('Motor slot', EXTRUDE, ['Sketch the 12 x 10 slot from the bottom. Extrude Cut Through All. Save.'], f2)]


@part('worm', 'worm', 'base', 'Acetal (POM), single start, module %g' % GEAR_M, POM_C, POM_D,
      'The worm on the motor shaft. One turn moves the drive gear one tooth. A worm cannot be turned by the gear, so '
      'nobody can turn the carousel by hand to reach the next dose.', origin=(-6, WORM_Y, WORM_ZC))
def _worm():
    y, z = WORM_Y, WORM_ZC
    f1 = xcyl(WORM_R[0], -6, 6, y, z)
    f2 = f1.union(union(*[xcyl(WORM_R[1], x - 0.5, x + 0.5, y, z) for x in (-2 * WORM_PITCH, -WORM_PITCH, 0, WORM_PITCH, 2 * WORM_PITCH)]))
    f3 = f2.cut(xcyl(1.5, -7, 7, y, z))
    return [F('Core', EXTRUDE, [NEW_PART + ' and save it as worm.ipt.', 'Circle diameter %g. Extrude 12 mm.' % (2 * WORM_R[0])], f1),
            F('Thread', '3D Model tab > Create panel > Coil',
              ['Sketch the tooth profile on the XY Plane, 1.8 deep. Coil: pitch %.3f mm, 5 turns, about the axis.' % WORM_PITCH], f2,
              'Shown here as five rings at the pitch (Inventor shows the real helix).'),
            F('Bore', HOLE, ['Hole diameter 3 Through All on the axis (a D bore for the motor shaft). Save.'], f3)]


@part('home_sensor', 'home sensor', 'base', 'Bought in: reflective optical sensor (infrared)', DARK, 1300,
      'A reflective light sensor under the drive gear, looking up at it. Once a turn of the carousel the hole in the '
      'gear passes over it and the light is not reflected, so the control unit always knows which compartment is over '
      'the drop hole.', origin=polar(HOME_R, FLAG_ANG, COVER[1]), bought=True)
def _home_sensor():
    r, z1 = HOME_R, GEAR_Z[0] - 0.5
    f1 = box(r - 3, r + 3, -3, 3, COVER[1], z1 - 0.5)
    f2 = f1.union(zcyl(1, z1 - 0.5, z1, r, -1.4)).union(zcyl(1, z1 - 0.5, z1, r, 1.4))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as home_sensor.ipt.', 'Sketch 6 x 6. Extrude %g mm.' % (z1 - 0.5 - COVER[1])],
              rotz(f1, FLAG_ANG)),
            F('Light and eye', EXTRUDE, ['Sketch two circles diameter 2, 2.8 apart, on the top. Extrude 0.5 mm, Join. Save.'],
              rotz(f2, FLAG_ANG), 'One is an infrared light, the other a light sensor: 0.5 mm under the gear.')]


@part('battery_door', 'battery door', 'base', 'Polypropylene (PP), white, injection moulded', PP_C, PP_D,
      'Door under each battery holder, held by two tamper-proof screws: the pharmacy changes the batteries; the patient '
      'cannot open it.', origin=(DOOR[0], -DOOR[2], -2.5), recyclable=True)
def _battery_door():
    x0, x1, h = DOOR
    f1 = box(x0, x1, -h, h, -2.5, -1)
    a0, a1, ho = DOOR_OPEN
    f2 = f1.union(box(a0 + 0.2, a1 - 0.2, -ho + 0.2, ho - 0.2, -1, COVER[1] - 0.2))
    cs = union(*[cq.Workplane('XY').add(cq.Solid.makeCone(2.6, 1.1, 1.5, cq.Vector(DOOR_SCREW[0], t * DOOR_SCREW[1], -2.51)))
                 for t in (1, -1)])
    f3 = f2.cut(cs)
    return [F('Flange', EXTRUDE, [NEW_PART + ' and save it as battery_door.ipt.', 'Sketch %d x %d. Extrude 1.5 mm.' % (x1 - x0, 2 * h)], f1),
            F('Plug', EXTRUDE, ['Sketch %.1f x %.1f on the top face. Extrude 2.8 mm, Join.' % (a1 - a0 - 0.4, 2 * ho - 0.4)], f2,
              'The plug fills the opening in the cover.'),
            F('Screw holes', HOLE, ['Hole: countersunk 5.2 x 90 degrees, diameter 2.2, at x %d, y %.1f; Mirror. Save.' % DOOR_SCREW], f3)]


@part('door_seal', 'battery door seal', 'base', 'Silicone rubber sheet, 1 thick, die cut', RUBBER, SIL_D,
      'Flat seal between the battery door and the cover, so no water gets to the batteries.',
      origin=(DOOR[0], -DOOR[2], -1))
def _door_seal():
    x0, x1, h = DOOR
    a0, a1, ho = DOOR_OPEN
    f1 = box(x0, x1, -h, h, -1, 0).cut(box(a0, a1, -ho, ho, -2, 1))
    f2 = f1.cut(union(*[zcyl(1.1, -2, 1, DOOR_SCREW[0], t * DOOR_SCREW[1]) for t in (1, -1)]))
    return [F('Frame', EXTRUDE, [NEW_PART + ' and save it as door_seal.ipt.', 'Sketch the %d x %d frame, %d wide. Extrude 1 mm.'
                                 % (x1 - x0, 2 * h, h - ho)], f1),
            F('Screw holes', HOLE, ['Holes diameter 2.2 for the screws. Save.'], f2)]


@part('security_screw', 'security screw M2.2 x 8', 'base', 'Bought in: A2 stainless pin Torx (tamper-proof) countersunk screw',
      STEEL_C, SS_D, 'Holds the battery door. It needs a pin Torx bit, which the pharmacy has and the patient does not.',
      origin=(DOOR_SCREW[0], DOOR_SCREW[1], -2.5), bought=True)
def _security_screw():
    x, y = DOOR_SCREW
    f1 = cq.Workplane('XY').add(cq.Solid.makeCone(2.6, 1.1, 1.5, cq.Vector(x, y, -2.5))).union(zcyl(1.1, -1, 6, x, y))
    f2 = f1.cut(zcyl(0.6, -3, -1.8, x, y))
    return [F('Screw', REVOLVE, ['Place from Content Center, or ' + NEW_PART + ': revolve a countersunk head diameter 5.2 '
                                 'and a shank diameter 2.2, 7 long.'], f1),
            F('Pin Torx recess', EXTRUDE, ['Sketch the recess on the head. Extrude Cut 0.7 mm. Save.'], f2)]


@part('cover_screw', 'cover screw 2.5 x 10', 'base', 'Bought in: A2 stainless countersunk screw for plastics (thread forming)',
      STEEL_C, SS_D, 'Four screws from underneath hold the bottom cover to the chassis bosses and squeeze the gasket.',
      origin=polar(BOSS_R, 45, 0), bought=True)
def _cover_screw():
    x, y, _ = polar(BOSS_R, 45)
    f1 = cq.Workplane('XY').add(cq.Solid.makeCone(3.0, 1.25, 1.75, cq.Vector(x, y, 0))).union(zcyl(1.25, 1.75, 11, x, y))
    f2 = f1.cut(zcyl(0.7, -1, 0.9, x, y))
    return [F('Screw', REVOLVE, ['Place from Content Center, or ' + NEW_PART + ': revolve a countersunk head diameter 6 and '
                                 'a shank diameter 2.5, 11 long.'], f1),
            F('Recess', EXTRUDE, ['Sketch a Torx T8 recess. Extrude Cut 0.9 mm. Save.'], f2)]


# ---------------------------------------------------- SA4 control pod
@part('pod_column', 'pod column', 'pod', 'Polypropylene (PP), white, 3 wall, injection moulded', PP_C, PP_D,
      'The fixed column in the middle of the dispenser. It stands in the socket of the bottom cover, passes up through '
      'the carousel hub and holds the panel board at the top. The lid closes round it on an O-ring.',
      origin=(0, 0, COVER[1]), recyclable=True)
def _pod_column():
    f1 = ring(POD_R[0], POD_R[1], COVER[1], POD_TOP)
    f2 = f1.union(ring(POD_R[0] - 2, POD_R[0], PCB_Z[0] - 1.5, PCB_Z[0]))
    z0, z1, rb = GROOVE
    f3 = f2.cut(ring(rb, POD_R[1] + 1, z0, z1))
    f4 = f3.cut(box(-6, 6, -POD_R[1] - 1, 0, COVER[1] - 1, COVER[1] + 6))
    return [F('Tube', EXTRUDE, [NEW_PART + ' and save it as pod_column.ipt.',
                                'Sketch circles diameter %d and %d. Extrude %.1f mm.' % (2 * POD_R[1], 2 * POD_R[0], POD_TOP - COVER[1])], f1),
            F('Board ledge', EXTRUDE, ['Sketch a ring 2 wide inside the tube, %.1f up. Extrude 1.5 mm, Join.' % (PCB_Z[0] - 1.5 - COVER[1])], f2),
            F('O-ring groove', REVOLVE, ['Sketch a %.1f x %g rectangle on the outside, %.2f up. Revolve Cut.'
                                         % (POD_R[1] - rb, z1 - z0, z0 - COVER[1])], f3,
              'The O-ring here seals against the collar of the lid.'),
            F('Cable slot', EXTRUDE, ['Sketch a 12 x 6 slot at the bottom, at the front. Extrude Cut through the wall. Save.'], f4,
              'The ribbon cable from the main board comes in here.')]


@part('pod_oring', 'pod O-ring', 'pod', 'Silicone O-ring, 67 inside diameter x 3 section', RUBBER, SIL_D,
      'Seals the gap between the fixed control pod and the lid, so water cannot get in round the middle.',
      origin=(0, 0, (GROOVE[0] + GROOVE[1]) / 2), bought=True)
def _pod_oring():
    f1 = torus(GROOVE[2] + 1.5, 1.5, (0, 0, (GROOVE[0] + GROOVE[1]) / 2), (0, 0, 1))
    return [F('Ring', SWEEP, [NEW_PART + ' and save it as pod_oring.ipt (or Place from Content Center: O-ring 67 x 3).',
                              'Sweep a circle diameter 3 round a circle diameter %g. Save.' % (2 * GROOVE[2] + 3)], f1)]


@part('panel_pcb', 'panel circuit board', 'pod', 'Bought in: FR4 board 1.6 thick', PCB_C, 1900,
      'The small round board in the top of the pod: it carries the display, the button switch, the flashing light '
      'and the buzzer, and is joined to the main board by a ribbon cable.', origin=(0, 0, PCB_Z[0]), bought=True)
def _panel_pcb():
    f1 = zcyl(POD_R[0] - 0.2, *PCB_Z)
    return [F('Board', EXTRUDE, [NEW_PART + ' and save it as panel_pcb.ipt.', 'Circle diameter %.1f. Extrude 1.6 mm. Save.'
                                 % (2 * POD_R[0] - 0.4)], f1)]


@part('lcd', 'display', 'pod', 'Bought in: low power LCD module 30 x 20, shows the time, next dose and battery', LCD_C, 2500,
      'Shows the time, the next dose time, how many doses are left and a low battery warning, for the patient and '
      'the pharmacy.', origin=(-15, 1, PCB_Z[1]), bought=True)
def _lcd():
    z = PCB_Z[1]
    f1 = box(-15, 15, 1, 21, z, z + 3.5)
    f2 = f1.cut(box(-13, 13, 3, 19, z + 3.2, z + 4))
    return [F('Module', EXTRUDE, [NEW_PART + ' and save it as lcd.ipt.', 'Sketch 30 x 20. Extrude 3.5 mm.'], f1),
            F('Glass', EXTRUDE, ['Sketch the 26 x 16 viewing area. Extrude Cut 0.3 mm. Save.'], f2)]


@part('tact_switch', 'button switch', 'pod', 'Bought in: 6 x 6 tactile switch, IP67', DARK, 1500,
      'The switch under the PRESS HERE button.', origin=(BTN[0] - 3, BTN[1] - 3, PCB_Z[1]), bought=True)
def _tact_switch():
    x, y = BTN
    z = PCB_Z[1]
    f1 = box(x - 3, x + 3, y - 3, y + 3, z, z + 3.5)
    f2 = f1.union(zcyl(1.75, z + 3.5, 50, x, y))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as tact_switch.ipt.', 'Sketch 6 x 6. Extrude 3.5 mm.'], f1),
            F('Plunger', EXTRUDE, ['Circle diameter 3.5. Extrude 2.4 mm, Join. Save.'], f2)]


@part('led', 'flashing light (LED)', 'pod', 'Bought in: 5 mm high brightness amber LED', AMBER, 1200,
      'The light beside the button. It flashes when a dose is due, until the pills have been dispensed.',
      origin=(LED_XY[0], LED_XY[1], PCB_Z[1]), bought=True)
def _led():
    x, y = LED_XY
    f1 = zcyl(2.5, PCB_Z[1], 48, x, y)
    f2 = f1.union(cq.Workplane('XY').sphere(2.5).translate((x, y, 48))).union(zcyl(2.9, PCB_Z[1], PCB_Z[1] + 1, x, y))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as led.ipt.', 'Circle diameter 5. Extrude 3.9 mm.'], f1),
            F('Dome and rim', REVOLVE, ['Revolve the dome radius 2.5 on top and a rim diameter 5.8 at the bottom. Save.'], f2)]


@part('led_lens', 'light lens', 'pod', 'Clarified polypropylene, clear, injection moulded', CLEAR, CPP_D,
      'Clear light pipe through the pod cap, with a flange that seals under the cap. It carries the flashing light to '
      'the top, next to the button.', origin=(LED_XY[0], LED_XY[1], 50.5), recyclable=True)
def _led_lens():
    x, y = LED_XY
    f1 = zcyl(5.5, 50.5, POD_TOP, x, y)
    f2 = f1.union(zcyl(3.6, POD_TOP, 54, x, y))
    f3 = f2.faces('>Z').edges().fillet(1.0)
    return [F('Flange', EXTRUDE, [NEW_PART + ' and save it as led_lens.ipt.', 'Circle diameter 11. Extrude 1 mm.'], f1),
            F('Light pipe', EXTRUDE, ['Circle diameter 7.2. Extrude 2.5 mm, Join.'], f2),
            F('Round top', FILLET, ['Fillet the top edge 1. Save.'], f3)]


@part('buzzer', 'buzzer', 'pod', 'Bought in: 9 mm piezo sounder, 85 dB at 10 cm, sealed', DARK, 1800,
      'Sounds the alarm when a dose is due and keeps sounding until the pills have been dispensed.',
      origin=(BUZ_XY[0], BUZ_XY[1], PCB_Z[1]), bought=True)
def _buzzer():
    x, y = BUZ_XY
    f1 = zcyl(4.5, PCB_Z[1], POD_TOP, x, y)
    f2 = f1.cut(zcyl(1, POD_TOP - 0.5, POD_TOP + 1, x, y))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as buzzer.ipt.', 'Circle diameter 9. Extrude 7.4 mm.'], f1),
            F('Sound hole', HOLE, ['Hole diameter 2, 0.5 deep, on the top. Save.'], f2)]


@part('button', 'PRESS HERE button', 'pod', 'Silicone rubber, green, moulded with raised PRESS HERE letters', GREEN, SIL_D,
      'The big green button the patient presses when the light flashes and the alarm sounds. Its flange is clamped '
      'under the pod cap, so it seals the hole as well.', origin=(BTN[0], BTN[1], 50), recyclable=False)
def _button():
    x, y = BTN
    f1 = zcyl(14, 50, POD_TOP, x, y)
    f2 = f1.union(zcyl(11, POD_TOP, 55, x, y))
    f3 = f2.faces('>Z').edges().fillet(1.5)
    try:
        # the letters start 0.3 inside the top face, so they are one solid with it, and stand 0.6 proud
        txt = cq.Workplane('XY').text('PRESS', 3.6, 0.9, kind='bold').translate((x, y + 2.6, 55 - 0.3)).union(
            cq.Workplane('XY').text('HERE', 3.6, 0.9, kind='bold').translate((x, y - 2.6, 55 - 0.3)))
        f4 = f3.union(txt)
        if not f4.val().isValid() or len(f4.solids().vals()) != 1:
            raise ValueError
    except Exception:
        f4 = f3
    return [F('Flange', EXTRUDE, [NEW_PART + ' and save it as button.ipt.', 'Circle diameter 28. Extrude 1.5 mm.'], f1),
            F('Button', EXTRUDE, ['Circle diameter 22 on the flange. Extrude 3.5 mm, Join.'], f2),
            F('Round top', FILLET, ['Fillet the top edge 1.5.'], f3),
            F('PRESS HERE', EMBOSS, ['Sketch the text PRESS HERE, 3.6 high, bold, in two lines on the top face. '
                                     'Emboss 0.6 mm, Emboss from Face. Save.'], f4, 'Raised letters can be felt as well as seen.')]


@part('display_window', 'display window', 'pod', 'Clarified polypropylene, clear, 1.5 thick', CLEAR, CPP_D,
      'Clear window over the display, sealed under the pod cap.', origin=(-17, 0.5, 50), recyclable=True)
def _display_window():
    f1 = box(-17, 17, 0.5, 22, 50, POD_TOP)
    return [F('Pane', EXTRUDE, [NEW_PART + ' and save it as display_window.ipt.', 'Sketch 34 x 21.5. Extrude 1.5 mm. Save.'], f1)]


@part('pod_cap', 'pod cap', 'pod', 'Polypropylene (PP), WBEP blue, injection moulded, printed', BLUE, PP_D,
      'The top of the control pod: the face the patient uses. It has the button, the light, the display window and '
      'the buzzer grille, and is welded to the column so it cannot be prised off.', origin=(0, 0, POD_TOP), recyclable=True)
def _pod_cap():
    f1 = zcyl(POD_R[1], POD_TOP, LID_Z[1]).union(ring(POD_R[0] - 1.5, POD_R[0], 49, POD_TOP))
    f2 = f1.faces('>Z').edges().fillet(1.0)
    f3 = f2.cut(zcyl(11.5, 40, 60, *BTN)).cut(zcyl(3.6, 40, 60, *LED_XY)).cut(box(-13, 13, 3, 19, 40, 60))
    holes = union(*[zcyl(0.8, POD_TOP - 1, 60, BUZ_XY[0] + dx, BUZ_XY[1] + dy) for dx, dy in ((0, 0), (2.5, 0), (-2.5, 0), (0, 2.5), (0, -2.5))])
    f4 = f3.cut(holes)
    return [F('Disc and spigot', EXTRUDE, [NEW_PART + ' and save it as pod_cap.ipt.',
                                           'Circle diameter %d, Extrude %.1f mm; ring diameter %d / %d, Extrude 2.5 mm down.'
                                           % (2 * POD_R[1], LID_Z[1] - POD_TOP, 2 * POD_R[0], 2 * POD_R[0] - 3)], f1),
            F('Round edge', FILLET, ['Fillet the top edge 1.'], f2),
            F('Openings', EXTRUDE, ['Sketch the button hole diameter 23, the light hole diameter 7.2 and the 26 x 16 '
                                    'display window. Extrude Cut Through All.'], f3),
            F('Buzzer grille', HOLE, ['Five holes diameter 1.6 over the buzzer. Save.'], f4)]


# ---------------------------------------------------- SA5 lid and hinge
@part('lid', 'lid', 'lid', 'Clarified polypropylene (PP), clear, 1.8 wall, injection moulded', CLEAR, CPP_D,
      'The clear lid: the patient can see the doses left but cannot reach them. It is hinged at the back, closes on '
      'the gasket and round the pod O-ring, and is held shut by the lid catch and the pharmacy lock.',
      origin=(0, 0, LID_Z[0]), recyclable=True)
def _lid():
    z0, z1 = LID_Z
    f1 = zcyl(R_CASE, z0, z1).faces('>Z').edges().fillet(4)
    inner = zcyl(R_CASE - LID_T, z0 - 1, z1 - LID_TOP).faces('>Z').edges().fillet(2.2)
    f2 = f1.cut(inner)
    f3 = f2.cut(zcyl(LID_HOLE, z0, z1 + 1)).union(ring(COLLAR[0], COLLAR[1], COLLAR[2], z1 - 0.5))
    y, zh, r = HINGE
    lug = box(-15, 15, 78, y, zh, zh + 6).union(knuckle(-15, 15)).cut(zcyl(R_CASE - LID_T, 0, 60))
    f4 = f3.union(lug).cut(xcyl(PIN_R, -20, 20, y, zh))
    return [
        F('Body', EXTRUDE, [NEW_PART + ' and save it as lid.ipt.',
                            'Circle diameter %d on the XZ Plane. Extrude %d mm. Fillet the top edge 4.' % (2 * R_CASE, z1 - z0)], f1),
        F('Hollow it', SHELL, ['Shell: remove the bottom face, thickness %g (top %g). Fillet the inside top edge 2.2.'
                               % (LID_T, LID_TOP)], f2, 'Clear PP lets the patient and the carer see how many doses are left.'),
        F('Pod hole and collar', EXTRUDE, ['Hole diameter %d in the top on the centre. Sketch circles diameter %d and %d; '
                                           'Extrude %.1f mm down, Join.' % (2 * LID_HOLE, 2 * COLLAR[0], 2 * COLLAR[1], z1 - 0.5 - COLLAR[2])], f3,
          'The collar closes over the O-ring on the pod.'),
        F('Hinge knuckle', EXTRUDE, ['Sketch the lug and the knuckle (radius %.1f at y %.1f, z %.0f) on the YZ Plane. '
                                     'Extrude 30 mm, symmetric. Hole diameter %d along the axis. Save.' % (r, y, zh, 2 * PIN_R)], f4),
    ]


@part('gasket', 'gasket ring', 'lid', 'Silicone rubber, 1 thick, die cut ring %g / %g' % (2 * GASKET[0], 2 * GASKET[1]),
      RUBBER, SIL_D, 'Flat silicone ring. One seals the lid to the chassis, and the same part seals the chassis to the '
      'bottom cover: together with the O-ring and the door and drawer seals the dispenser is waterproof.',
      origin=(0, 0, CH_Z[1]))
def _gasket():
    f1 = ring(GASKET[0], GASKET[1], CH_Z[1], LID_Z[0])
    return [F('Ring', EXTRUDE, [NEW_PART + ' and save it as gasket.ipt.', 'Circles diameter %g and %g. Extrude 1 mm. Save.'
                                % (2 * GASKET[0], 2 * GASKET[1])], f1)]


CATCH = dict(x=(-24, -4.5), r=(81.0, 84.0), lip=86.0, z=(9, 12.5), flange=(81.0, 85.0, 50.5))   # sketch: x across, r out, z up
SLOT_GAP = 0.3                  # the inner edge of the catch slot in the deck is this far inside the tab: it guides the tab


def catch_band(r0, r1, z0, z1, grow=0):
    """Part of a ring (r0 to r1, round the dispenser axis) across the width of the catch, before it is turned to the lock."""
    return ring(r0, r1, z0, z1).intersect(box(CATCH['x'][0] - grow, CATCH['x'][1] + grow, -R_CASE - 5, -60, z0, z1))


def catch_local():
    r0, r1 = CATCH['r']
    za, zb = CATCH['z']
    fr0, fr1, fz = CATCH['flange']
    tab = catch_band(r0, r1, za, fz)
    lip = catch_band(r1 - 0.01, CATCH['lip'], za, zb)
    flange = catch_band(fr0, fr1, fz, LID_Z[1] - LID_TOP)
    return tab, lip, flange


def _rot_xy(x, y, a):
    a = math.radians(a)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


CATCH_ORIGIN = _rot_xy(sum(CATCH['x']) / 2, -CATCH['r'][0], LOCK_ANG + 90) + (CATCH['z'][0],)


@part('lid_catch', 'lid catch', 'lid', 'Polypropylene, 30 % glass filled (PP-GF30), injection moulded', DARK, PPGF_D,
      'A hook that hangs down from inside the lid, through the slot in the deck, to the lock. When the pharmacy lock '
      'is turned, the cam lies over the hook and the lid cannot be lifted: the part that stops anyone forcing the lid '
      '(FEA load case).', origin=CATCH_ORIGIN)
def _lid_catch():
    tab, lip, flange = catch_local()
    _cr, _cw = CATCH['r'], CATCH['x'][1] - CATCH['x'][0]
    f1 = at_lock(tab.union(flange))
    f2 = at_lock(tab.union(flange).union(lip))
    return [F('Tab and flange', EXTRUDE, [NEW_PART + ' and save it as lid_catch.ipt.',
                                          'Sketch the L shape on the YZ Plane: a tab %g thick, %.1f long, and a flange %g x %g '
                                          'at the top. Extrude %g mm.' % (_cr[1] - _cr[0], CATCH['flange'][2] - CATCH['z'][0],
                                                                        CATCH['flange'][1] - CATCH['flange'][0],
                                                                        LID_Z[1] - LID_TOP - CATCH['flange'][2], _cw)], f1,
              'Heat staked to the inside of the lid top.'),
            F('Hook', EXTRUDE, ['Sketch a %g x %g rectangle on the outside of the bottom of the tab. Extrude %g mm, Join. Save.'
                                % (CATCH['lip'] - _cr[1], CATCH['z'][1] - CATCH['z'][0], _cw)],
              f2, 'The cam of the lock lies on top of the hook.')]


@part('hinge_pin', 'hinge pin', 'lid', 'A2 stainless steel pin, 3 diameter x %d' % 88, STEEL_C, SS_D,
      'The pin the lid turns on. It is pressed in through the three knuckles and cannot be pulled out with the lid shut.',
      origin=(-44, HINGE[0], HINGE[1]), bought=True)
def _hinge_pin():
    f1 = xcyl(PIN_R, -44, 44, HINGE[0], HINGE[1])
    f2 = f1.faces('<X or >X').chamfer(0.3)
    return [F('Pin', EXTRUDE, [NEW_PART + ' and save it as hinge_pin.ipt.', 'Circle diameter 3. Extrude 88 mm.'], f1),
            F('Chamfers', CHAMFER, ['Chamfer both ends 0.3. Save.'], f2)]


# ---------------------------------------------------- SA6 dispensing drawer
@part('drawer', 'dispensing drawer', 'drawer', 'Polypropylene (PP), WBEP blue, injection moulded', BLUE, PP_D,
      'The pills fall into this drawer. The patient pulls it out by the finger grip, tips the pills into a hand or a '
      'cup and pushes it back; it clicks home against its seal.', origin=(0, -R_CASE, DRAWER[1]), recyclable=True)
def _drawer():
    w, z0, z1, yb = DRAWER
    tub = box(-w, w, -95, yb, z0, z1).intersect(zcyl(90.5, z0 - 1, z1 + 1))
    f1 = tub
    f2 = f1.cut(box(-w + 1.5, w - 1.5, -88, yb - 1.5, z0 + 1.5, z1 + 1).intersect(zcyl(88.5, 0, 30)))
    front = ring(90.5, 92, z0 - 1, z1 + 1).intersect(box(-25, 25, -95, -80, z0 - 1, z1 + 1))
    f3 = f2.union(front)
    f4 = f3.cut(box(-12, 12, -95, -91, z1 - 3, z1 + 2))
    return [F('Tub', EXTRUDE, [NEW_PART + ' and save it as drawer.ipt.',
                               'Sketch a %d x %.1f rectangle, its front on an arc radius 90.5. Extrude %.1f mm.'
                               % (2 * w, -yb - 90.5, z1 - z0)], f1),
            F('Hollow it', SHELL, ['Shell: remove the top face, thickness 1.5.'], f2),
            F('Front', EXTRUDE, ['Sketch arcs radius 90.5 and 92 on the XZ Plane, 50 wide. Extrude %.1f mm, Join.' % (z1 - z0 + 2)], f3,
              'The front follows the round case.'),
            F('Finger grip', EXTRUDE, ['Sketch a 24 x 3 notch at the top of the front. Extrude Cut 1 mm deep. Save.'], f4)]


@part('drawer_seal', 'drawer seal', 'drawer', 'Silicone rubber, 0.5 thick, moulded frame', RUBBER, SIL_D,
      'A thin frame on the back of the drawer front. It presses on the case round the opening when the drawer is '
      'pushed home, so water cannot get in.', origin=(0, -90.5, DRAWER_OPEN[1] - 1))
def _drawer_seal():
    w, za, zb = DRAWER_OPEN
    f1 = ring(90, 90.5, za - 1, zb + 1).intersect(box(-25, 25, -95, -80, za - 1, zb + 1))
    f2 = f1.cut(box(-w, w, -95, -80, za, zb))
    return [F('Frame', EXTRUDE, [NEW_PART + ' and save it as drawer_seal.ipt.', 'Sketch arcs radius 90 and 90.5. Extrude %.1f mm.' % (zb - za + 2)], f1),
            F('Opening', EXTRUDE, ['Sketch the %d x %.1f opening. Extrude Cut Through All. Save.' % (2 * w, zb - za)], f2)]


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


def _mx(w):
    return w.mirror('YZ')


def _my(w):
    return w.mirror('XZ')


def instances():
    """Every part of the dispenser: (instance name, part key, transform, sub-assembly key)."""
    out = [('chassis', 'chassis', IDENT, 'chassis'), ('pharmacy lock', 'pharmacy_lock', IDENT, 'chassis'),
           ('lock cam', 'lock_cam', IDENT, 'chassis'), ('dispensing chute', 'chute', IDENT, 'chassis'),
           ('drop sensor, emitter', 'drop_sensor', IDENT, 'chassis'), ('drop sensor, receiver', 'drop_sensor', _mx, 'chassis')]
    out += [('carousel', 'carousel', IDENT, 'carousel'), ('drive gear', 'drive_gear', IDENT, 'carousel')]
    out += [('bottom cover', 'bottom_cover', IDENT, 'base'), ('base gasket', 'gasket', _t(dz=COVER[1] - CH_Z[1]), 'base')]
    out += [('rubber foot %d' % (k + 1), 'foot', _rz(90 * k), 'base') for k in range(4)]
    out += [('main circuit board', 'main_pcb', IDENT, 'base'),
            ('battery holder, right', 'battery_holder', IDENT, 'base'), ('battery holder, left', 'battery_holder', _mx, 'base')]
    dx = BAT_X[1] - BAT_X[0]
    out += [('AAA cell 1', 'battery', IDENT, 'base'), ('AAA cell 2', 'battery', lambda w: _my(w).translate((dx, 0, 0)), 'base'),
            ('AAA cell 3', 'battery', lambda w: _mx(_my(w)), 'base'), ('AAA cell 4', 'battery', lambda w: _mx(w.translate((dx, 0, 0))), 'base')]
    out += [('gear motor', 'gear_motor', IDENT, 'base'), ('motor clamp', 'motor_clamp', IDENT, 'base'),
            ('worm', 'worm', IDENT, 'base'), ('home sensor', 'home_sensor', IDENT, 'base')]
    out += [('battery door, right', 'battery_door', IDENT, 'base'), ('battery door, left', 'battery_door', _mx, 'base'),
            ('door seal, right', 'door_seal', IDENT, 'base'), ('door seal, left', 'door_seal', _mx, 'base')]
    out += [('security screw %d' % (k + 1), 'security_screw', tf, 'base')
            for k, tf in enumerate((IDENT, _my, _mx, lambda w: _mx(_my(w))))]
    out += [('pod column', 'pod_column', IDENT, 'pod'), ('pod O-ring', 'pod_oring', IDENT, 'pod'),
            ('panel circuit board', 'panel_pcb', IDENT, 'pod'), ('display', 'lcd', IDENT, 'pod'),
            ('button switch', 'tact_switch', IDENT, 'pod'), ('flashing light', 'led', IDENT, 'pod'),
            ('light lens', 'led_lens', IDENT, 'pod'), ('buzzer', 'buzzer', IDENT, 'pod'),
            ('PRESS HERE button', 'button', IDENT, 'pod'), ('display window', 'display_window', IDENT, 'pod'),
            ('pod cap', 'pod_cap', IDENT, 'pod')]
    out += [('lid', 'lid', IDENT, 'lid'), ('lid gasket', 'gasket', IDENT, 'lid'), ('lid catch', 'lid_catch', IDENT, 'lid'),
            ('hinge pin', 'hinge_pin', IDENT, 'lid')]
    out += [('dispensing drawer', 'drawer', IDENT, 'drawer'), ('drawer seal', 'drawer_seal', IDENT, 'drawer')]
    out += [('cover screw %d' % (k + 1), 'cover_screw', _rz(90 * k), 'ga') for k in range(4)]
    return out


def colour(key):
    return PART[key]['colour']


# moving parts and how they move (used by the simulation and the clash check at each position)
LID_PARTS = ('lid', 'lid gasket', 'lid catch')
CAROUSEL_PARTS = ('carousel', 'drive gear')


def lid_open(w, deg):
    """Swing a lid part open about the hinge axis (the front goes up)."""
    return w.rotate((0, HINGE[0], HINGE[1]), (1, HINGE[0], HINGE[1]), -deg)


def cam_turn(w, deg):
    """Turn the lock cam about the lock axis (90 = unlocked, pointing up)."""
    a = math.radians(LOCK_ANG)
    p = (87 * math.cos(a), 87 * math.sin(a), LOCK_Z)
    return w.rotate(p, (p[0] - math.cos(a), p[1] - math.sin(a), p[2]), deg)    # turning about the inward axis: the arm goes up


def posed(items, lid=0.0, cam=0.0, carousel=0.0, drawer=0.0):
    """The parts in a position of the motion: lid angle, cam angle, carousel angle, drawer out (mm)."""
    out = []
    for n, k, s in items:
        if n in LID_PARTS and lid:
            s = lid_open(s, lid)
        elif n == 'lock cam' and cam:
            s = cam_turn(s, cam)
        elif n in CAROUSEL_PARTS and carousel:
            s = rotz(s, carousel)
        elif n in ('dispensing drawer', 'drawer seal') and drawer:
            s = s.translate((0, -drawer, 0))
        out.append((n, k, s))
    return out


def dispenser_instances():
    """Every part in the dispenser: (instance name, part key, shape)."""
    return [(n, k, tf(shape(k))) for n, k, tf, sub in instances()]


def dispenser():
    """Design A, the preferred design: an automated pill dispenser. A carousel of 28 compartments turns over a deck
    with one drop hole; when a dose is due the buzzer sounds and the light beside the PRESS HERE button flashes, the
    patient presses the button, the worm drive turns the carousel one step and the pills drop into the drawer. Clear
    lid locked by a pharmacy key, polypropylene case sealed against water, four AAA cells, reprogrammed by NFC."""
    return [(n, s, colour(k)) for n, k, s in dispenser_instances()]


def masses(items=None):
    """Mass of every instance (kg), by part key: {key: [qty, mass]}."""
    items = items if items is not None else dispenser_instances()
    by = {}
    for n, k, s in items:
        m = s.val().Volume() * 1e-9 * PART[k]['density']
        by.setdefault(k, [0, 0.0])
        by[k][0] += 1
        by[k][1] += m
    return by


def total_mass(items=None):
    return sum(m for q, m in masses(items).values())


# ------------------------------------------------------------------ pill capacity of a compartment
PILL = (5.0, 20.0)      # the largest pill in the brief: diameter, length


def capacity():
    """How many of the largest pills fit in one compartment, lying flat in layers, each pill along the radius:
    in each layer the pills lie in rows across the segment; a row at radius r fits floor(width(r) / d) pills,
    where width is the gap between the ribs at the inner end of the row."""
    d, L = PILL
    depth = CAR_Z[1] - CAR_Z[0] - 1.5      # allow 1.5 under the lid gap... keep clear of the top
    layers = int(depth // d)
    rows, r = [], HUB[1]
    while r + L <= CAR_OUT[0] + 1e-6:
        width = 2 * math.pi * r / N_SEG - RIB
        rows.append(dict(r=r, width=width, n=int(width // d)))
        r += L
    per_layer = sum(x['n'] for x in rows)
    return dict(layers=layers, rows=rows, per_layer=per_layer, total=per_layer * layers, depth=depth,
                volume=(math.pi * (CAR_OUT[0] ** 2 - HUB[1] ** 2) / N_SEG - RIB * (CAR_OUT[0] - HUB[1])) * (CAR_Z[1] - CAR_Z[0]) / 1000)


# ------------------------------------------------------------------ Design B concept: cassette with trapdoors
def cassette_dispenser():
    """Design B, a concept: a rectangular dispenser, 186 x 124 x 52, with 28 compartments in 4 rows of 7, each with
    its own spring trapdoor held by a small solenoid latch. At a dose time the latch under that compartment lets go
    and the pills drop into a tray along the front. No moving carousel, but 28 latches cost more, weigh more and use
    more power, and every trapdoor is a place for water to get in."""
    out = []
    body = box(-93, 93, -62, 62, 0, 30).edges('|Z').fillet(10)
    body = body.cut(box(-90, 90, -59, 59, 2, 31).edges('|Z').fillet(8))
    out.append(('case', body, PP_C))
    grid = box(-88, 88, -40, 57, 12, 30)
    for i in range(7):
        for j in range(4):
            x0 = -86 + i * 24.8
            y0 = -38 + j * 23.6
            grid = grid.cut(box(x0, x0 + 22.8, y0, y0 + 21.6, 11, 31))
    out.append(('28 compartments', grid, CAR_C))
    out.append(('trapdoors and latches', box(-88, 88, -40, 57, 9, 12), DARK))
    out.append(('pill tray', box(-80, 80, -60, -42, 2, 14), BLUE))
    lid = box(-93, 93, -62, 62, 30, 46).edges('|Z').fillet(10).cut(box(-91, 91, -60, 60, 29, 44).edges('|Z').fillet(8))
    out.append(('clear lid', lid, CLEAR))
    out.append(('display and PRESS HERE button', box(-30, 30, -58, -46, 46, 52), GREEN))
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
    return 'esp2025_p%02d_%s' % (p['no'], p['key'])


def _part_fn(p):
    def fn():
        return [(p['name'], part_shape(p['key']), p['colour'])]
    fn.__doc__ = p['desc']
    return fn


def _ga_bom():
    items = dispenser_instances()
    return bom([n for n, k, s in items], items)


# ------------------------------------------------------------------ sub-assemblies
# How the dispenser is built, the way it would be in Inventor: six sub-assemblies (.iam) are made from their parts
# and placed into the top level assembly. 'explode' moves each part away from where it sits (mm) for the exploded
# views; 'steps' place the parts a group at a time (names, title, command, actions, note).
def _names(sub):
    return [n for n, k, tf, s in instances() if s == sub]


def _lockdir(d):
    a = math.radians(LOCK_ANG)
    return (d * math.cos(a), d * math.sin(a), 0)


SUBS = [
    dict(no=1, key='chassis', title='chassis, lock and chute', file='chassis.iam',
         explode={'chassis': (0, 0, 0), 'pharmacy lock': _lockdir(45), 'lock cam': _lockdir(-25),
                  'dispensing chute': (0, 0, -45), 'drop sensor, emitter': (30, 0, -45), 'drop sensor, receiver': (-30, 0, -45)},
         desc='The chassis (wall and deck in one moulding) with the pharmacy cam lock and its cam, and the chute under the '
              'drop hole with the two infrared drop sensors.',
         steps=[
             (['chassis'], 'Chassis', PLACE, [NEW_ASSY + ' and save it as chassis.iam.', 'Place chassis.ipt and Place Grounded.'], None),
             (['pharmacy lock', 'lock cam'], 'Pharmacy lock', CONSTRAIN,
              ['Place pharmacy_lock.ipt in the lock hole from outside: Insert (head on the wall, barrel axis on the hole axis).',
               'Place lock_cam.ipt on the end of the barrel: Mate the cam to the barrel end, Angle 0 (locked: pointing sideways).'],
              'The lock is bought in, keyed alike so one pharmacy key opens every dispenser.'),
             (['dispensing chute', 'drop sensor, emitter', 'drop sensor, receiver'], 'Chute and drop sensors', CONSTRAIN,
              ['Place chute.ipt under the deck: Mate its top to the underside of the deck, Flush its sides on the drop hole.',
               'Place drop_sensor.ipt on one side (Insert the lens in the window); Mirror Components for the other side. Save.'],
              'The beam across the chute sees the pills fall.'),
         ]),
    dict(no=2, key='carousel', title='carousel', file='carousel.iam',
         explode={'carousel': (0, 0, 0), 'drive gear': (0, 0, -40)},
         desc='The carousel of 28 compartments and 2 blanks, with the worm wheel pressed onto the bottom of its hub.',
         steps=[
             (['carousel'], 'Carousel', PLACE, [NEW_ASSY + ' and save it as carousel.iam.', 'Place carousel.ipt and Place Grounded.'], None),
             (['drive gear'], 'Drive gear', CONSTRAIN,
              ['Place drive_gear.ipt: Insert its bore on the hub tube, Flush its bottom with the end of the tube, and line a '
               'key slot up with a key (Angle). Save.'],
              'In the factory the gear is pressed on after the carousel is dropped into the chassis, from underneath.'),
         ]),
    dict(no=3, key='base', title='base, batteries and drive', file='base.iam', explode={},
         desc='The bottom cover carrying everything that is changed or serviced: main board, battery holders and cells, '
              'the gear motor with its clamp and worm, the home sensor, the battery doors with their seals and '
              'tamper-proof screws, the feet and the gasket.',
         steps=[
             (['bottom cover', 'rubber foot 1', 'rubber foot 2', 'rubber foot 3', 'rubber foot 4'], 'Bottom cover and feet',
              PLACE, [NEW_ASSY + ' and save it as base.iam.', 'Place bottom_cover.ipt and Place Grounded.',
                      'Place foot.ipt under it at 45 degrees (Mate, Insert on the sketch point); Pattern, Circular, 4.'], None),
             (['main circuit board', 'battery holder, right', 'battery holder, left', 'AAA cell 1', 'AAA cell 2',
               'AAA cell 3', 'AAA cell 4'], 'Board and batteries', CONSTRAIN,
              ['Place main_pcb.ipt at the back (Mate to the cover, Flush to the centre plane).',
               'Place battery_holder.ipt on the right (Mate, Flush its pockets over the opening); Mirror Components to the left.',
               'Place battery.ipt in each pocket (Insert); four cells, 6 V.'], 'Four AAA cells last many months: see the calculation sheet.'),
             (['gear motor', 'motor clamp', 'worm', 'home sensor'], 'Drive', CONSTRAIN,
              ['Place gear_motor.ipt (Mate its flat to the cover, Flush its axis %.1f from the centre).' % WORM_Y,
               'Place motor_clamp.ipt over it (Mate). Place worm.ipt on the shaft (Insert, Flush the middle on the YZ Plane).',
               'Place home_sensor.ipt at %d degrees (Mate, Flush to its sketch line).' % FLAG_ANG], None),
             (['battery door, right', 'battery door, left', 'door seal, right', 'door seal, left', 'security screw 1',
               'security screw 2', 'security screw 3', 'security screw 4', 'base gasket'], 'Doors, seals and gasket',
              CONSTRAIN, ['Place door_seal.ipt and battery_door.ipt under each opening (Mate, Insert on a screw hole); Mirror.',
                          'Place a security screw (Content Center, pin Torx) in each hole (Insert); Pattern.',
                          'Place gasket.ipt on top of the cover (Mate, Insert). Save.'], None),
         ]),
    dict(no=4, key='pod', title='control pod', file='control_pod.iam',
         explode={'pod column': (0, 0, 0), 'pod O-ring': (0, 0, 25), 'panel circuit board': (0, 0, 32), 'display': (0, 0, 40),
                  'button switch': (0, 0, 40), 'flashing light': (0, 0, 40), 'buzzer': (0, 0, 40), 'light lens': (0, 0, 52),
                  'PRESS HERE button': (0, 0, 52), 'display window': (0, 0, 52), 'pod cap': (0, 0, 66)},
         desc='The control pod: the column, its O-ring, the panel board with the display, button switch, flashing light '
              'and buzzer, the light lens, the PRESS HERE button, the display window and the cap.',
         steps=[
             (['pod column', 'pod O-ring'], 'Column and O-ring', PLACE,
              [NEW_ASSY + ' and save it as control_pod.iam.', 'Place pod_column.ipt and Place Grounded.',
               'Place pod_oring.ipt in the groove (Insert).'], None),
             (['panel circuit board', 'display', 'button switch', 'flashing light', 'buzzer'], 'Panel board', CONSTRAIN,
              ['Place panel_pcb.ipt on the ledge (Mate, Insert).',
               'Place lcd.ipt, tact_switch.ipt, led.ipt and buzzer.ipt on the board (Mate, Flush to the sketch points).'],
              'In the factory these are soldered on the board before it goes in.'),
             (['light lens', 'PRESS HERE button', 'display window', 'pod cap'], 'Lens, button, window and cap', CONSTRAIN,
              ['Place led_lens.ipt over the LED, button.ipt over the switch and display_window.ipt over the display (Mate, Insert).',
               'Place pod_cap.ipt on top: Mate it to the top of the column, Insert the button hole on the button. Save.'],
              'The cap clamps the flanges of the button, lens and window: each one is sealed.'),
         ]),
    dict(no=5, key='lid', title='lid and hinge', file='lid.iam',
         explode={'lid': (0, 0, 0), 'lid gasket': (0, 0, -25), 'lid catch': (0, 0, -40), 'hinge pin': (70, 0, 0)},
         desc='The clear lid with its gasket, the lid catch that the pharmacy lock holds, and the stainless hinge pin.',
         steps=[
             (['lid'], 'Lid', PLACE, [NEW_ASSY + ' and save it as lid.iam.', 'Place lid.ipt and Place Grounded.'], None),
             (['lid gasket', 'lid catch'], 'Gasket and catch', CONSTRAIN,
              ['Place gasket.ipt under the lid wall (Mate, Insert).',
               'Place lid_catch.ipt: Mate its flange to the inside of the lid top at %d degrees.' % LOCK_ANG], None),
             (['hinge pin'], 'Hinge pin', CONSTRAIN, ['Place hinge_pin.ipt in the knuckle (Insert, Flush the middle). Save.'],
              'In the dispenser the pin also goes through the two knuckles of the chassis.'),
         ]),
    dict(no=6, key='drawer', title='dispensing drawer', file='drawer.iam',
         explode={'dispensing drawer': (0, 0, 0), 'drawer seal': (0, 25, 0)},
         desc='The pull-out drawer the pills fall into, with its seal.',
         steps=[
             (['dispensing drawer'], 'Drawer', PLACE, [NEW_ASSY + ' and save it as drawer.iam.', 'Place drawer.ipt and Place Grounded.'], None),
             (['drawer seal'], 'Seal', CONSTRAIN, ['Place drawer_seal.ipt on the back of the front (Mate, Flush). Save.'], None),
         ]),
]
_ex = {n: (0, 0, 0) for n in ('bottom cover',)}
for _k in range(4):
    _ex['rubber foot %d' % (_k + 1)] = (0, 0, -20)
_ex.update({'main circuit board': (0, 0, 30), 'battery holder, right': (0, 0, 30), 'battery holder, left': (0, 0, 30),
            'AAA cell 1': (0, 0, 55), 'AAA cell 2': (0, 0, 55), 'AAA cell 3': (0, 0, 55), 'AAA cell 4': (0, 0, 55),
            'gear motor': (35, 0, 25), 'motor clamp': (35, 0, 50), 'worm': (-30, 0, 25), 'home sensor': (0, 0, 30),
            'battery door, right': (0, 0, -45), 'battery door, left': (0, 0, -45), 'door seal, right': (0, 0, -30),
            'door seal, left': (0, 0, -30), 'security screw 1': (0, 0, -60), 'security screw 2': (0, 0, -60),
            'security screw 3': (0, 0, -60), 'security screw 4': (0, 0, -60), 'base gasket': (0, 0, 70)})
SUBS[2]['explode'] = _ex
SUB = {d['key']: d for d in SUBS}
for _d in SUBS:
    _d['names'] = _names(_d['key'])


def sub_model_name(d):
    return 'esp2025_sa%d_%s' % (d['no'], d['key'])


def sub_items(key):
    """The instances of one sub-assembly: (name, part key, shape)."""
    by = {n: (k, s) for n, k, s in dispenser_instances()}
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
    dict(name='esp2025_dispenser', title='ESP 2025 automated pill dispenser (GA)', fn=dispenser, criteria='3.1, 3.2',
         uses='ESP 2025 Task 2, Part B: the preferred design, an automated pill dispenser assembled from separate parts. '
              'General arrangement, parts list, section through the middle, simulation of a dose being dispensed and the '
              'pharmacy unlocking the lid to refill it.',
         section='y', explode=None, iso=(-1, -1.4, 0.9), folder='ESP 2025', sim=True, fea=False, bom=_ga_bom),
    dict(name='esp2025_cassette', title='ESP 2025 concept B: trapdoor cassette', fn=cassette_dispenser, criteria='3.1',
         uses='ESP 2025 Task 2, Part A: the second design idea, a rectangular cassette with 28 spring trapdoors, for '
              'comparison with design A.', section=None, explode=None, iso=(-1, -1.4, 0.9), folder='ESP 2025', fea=False),
]

for _d in SUBS:
    MODELS.append(dict(
        name=sub_model_name(_d), title='ESP 2025 sub-assembly %d: %s' % (_d['no'], _d['title']), fn=_sub_fn(_d),
        criteria='3.1, 3.2', uses='ESP 2025 sub-assembly %s: %s' % (_d['file'], _d['desc']), description=_d['desc'],
        section=None, explode=_d['explode'], folder='ESP 2025', bom=_sub_bom(_d), fea=False,
        iso=(-1, -1.4, 0.9), sub=dict(no=_d['no'], key=_d['key'], file=_d['file'])))

FEA_PART = 'lid_catch'
for _p in PARTS:
    MODELS.append(dict(
        name=part_model_name(_p), title='ESP 2025 part %02d: %s' % (_p['no'], _p['name']), fn=_part_fn(_p),
        criteria='3.1', uses='ESP 2025 component, item %d on the parts list: %s. %s' % (_p['no'], _p['material'], _p['desc']),
        description=_p['desc'], section=None, explode=None, folder='ESP 2025', part=dict(no=_p['no'], key=_p['key'],
        group=_p['group'], material=_p['material'], file=_p['file'], bought=_p['bought']),
        fea=None if _p['key'] == FEA_PART else False, media='still', skip_far_axes=True))


# ------------------------------------------------------------------ key sizes for each part drawing
SIZES = dict(
    chassis=['Ø%d x %d high, %g wall' % (2 * R_CASE, CH_Z[1] - CH_Z[0], WALL),
             'Deck %d thick, %d up; hub hole Ø%d' % (DECK[1] - DECK[0], DECK[0] - CH_Z[0], 2 * HUB[1] + 2),
             'Drop hole R%d to R%d, %.1f° wide' % DROP, 'Drawer opening %d x %.1f' % (2 * DRAWER_OPEN[0], DRAWER_OPEN[2] - DRAWER_OPEN[1]),
             'Lock hole Ø16 at %d°, %d up' % (LOCK_ANG, LOCK_Z - CH_Z[0]), 'Hinge Ø%d holes, axis y %.1f' % (2 * PIN_R, HINGE[0]),
             'Bosses Ø8 at R%d, 4 off' % BOSS_R],
    pharmacy_lock=['Head Ø20 x 2', 'Barrel Ø16 x 3', 'Key slot 2 x 8'],
    lock_cam=['Hub Ø8, arm 11.5 x 7', '%g thick, 3 x 3 square hole' % (CAM_R[1] - CAM_R[0])],
    chute=['%d x %d x %d, %g wall' % (2 * CHUTE[0], CHUTE[3] - CHUTE[2], DECK[0] - CHUTE[1], CHUTE[4]), 'Windows Ø3, 2 off'],
    drop_sensor=['6 x 5 x 3.5', 'Lens Ø3 x 1.5'],
    carousel=['Ø%d / Ø%d x %d' % (2 * CAR_OUT[1], 2 * HUB[0], CAR_Z[1] - CAR_Z[0]),
              '%d segments at %d°, ribs %g' % (N_SEG, SEG, RIB), 'Hub tube Ø%d / Ø%d x %.1f' % (2 * HUB[1], 2 * HUB[0], CAR_Z[0] - HUB_BOT),
              '2 blanks capped 1.5', '3 keys 2 x 1.3'],
    drive_gear=['%d teeth, module %g, pitch Ø%d' % (GEAR_N, GEAR_M, 2 * GEAR_RP), 'Tip Ø%.1f, root Ø%.1f' % (2 * GEAR_RA, 2 * GEAR_RF),
                'Face %d, bore Ø%d' % (GEAR_Z[1] - GEAR_Z[0], 2 * HUB[1]), 'Home mark Ø3 at R%d' % HOME_R],
    bottom_cover=['Ø%d x %d' % (2 * R_CASE, COVER[1]), 'Rim Ø172 / Ø%.1f x 4' % (2 * R_IN - 0.2),
                  'Socket Ø%d / Ø%d x 4' % (2 * POD_R[1], 2 * POD_R[1] + 4),
                  'Door openings %d x %d, 2 off' % (DOOR_OPEN[1] - DOOR_OPEN[0], 2 * DOOR_OPEN[2]),
                  'CSK holes Ø2.5 at R%d, 4 off' % BOSS_R],
    foot=['Ø%d x %d, edge R1.5' % (2 * FOOT[1], FOOT[2])],
    main_pcb=['%d x %d x 1.6' % (2 * PCB[0], PCB[2] - PCB[1])],
    battery_holder=['%d x %d x 12' % (BAT[1] - BAT[0], 2 * BAT[2]), 'Pockets Ø10.6 x %.1f, 2 off' % AAA[1]],
    battery=['AAA: Ø%.1f x %.1f' % (2 * AAA[0], AAA[1])],
    gear_motor=['Gearbox 12 x 10 x 9', 'Motor Ø12 (10 flats) x 22', 'Shaft Ø3 x %d' % (SHAFT[1] - SHAFT[0])],
    motor_clamp=['16 x 8 x %d' % (WORM_ZC + 7 - COVER[1]), 'Slot 12 x 10'],
    worm=['Root Ø%g, tip Ø%.1f, 12 long' % (2 * WORM_R[0], 2 * WORM_R[1]), 'Pitch %.3f (module %g), 1 start' % (WORM_PITCH, GEAR_M), 'Bore Ø3'],
    home_sensor=['6 x 6 x %g body' % (GEAR_Z[0] - 1 - COVER[1]), 'Light and eye Ø2, 2.8 apart'],
    battery_door=['Flange %d x %d x 1.5' % (DOOR[1] - DOOR[0], 2 * DOOR[2]),
                  'Plug %.1f x %.1f x 2.8' % (DOOR_OPEN[1] - DOOR_OPEN[0] - 0.4, 2 * DOOR_OPEN[2] - 0.4), 'CSK Ø2.2, 2 off'],
    door_seal=['%d x %d frame, 1 thick' % (DOOR[1] - DOOR[0], 2 * DOOR[2]), 'Opening %d x %d' % (DOOR_OPEN[1] - DOOR_OPEN[0], 2 * DOOR_OPEN[2])],
    security_screw=['M2.2 x 7, CSK Ø5.2', 'Pin Torx recess'],
    cover_screw=['2.5 x 11, CSK Ø6', 'Torx T8'],
    pod_column=['Ø%d / Ø%d x %.1f' % (2 * POD_R[1], 2 * POD_R[0], POD_TOP - COVER[1]),
                'O-ring groove Ø%d x %g' % (2 * GROOVE[2], GROOVE[1] - GROOVE[0]), 'Ledge %.1f up' % (PCB_Z[0] - 1.5 - COVER[1]),
                'Cable slot 12 x 6'],
    pod_oring=['Ø%d inside x 3 section' % (2 * GROOVE[2])],
    panel_pcb=['Ø%.1f x 1.6' % (2 * POD_R[0] - 0.4)],
    lcd=['30 x 20 x 3.5', 'View 26 x 16'],
    tact_switch=['6 x 6 x 3.5', 'Plunger Ø3.5'],
    led=['Ø5 LED, rim Ø5.8', '6.4 high'],
    led_lens=['Flange Ø11 x 1', 'Pipe Ø7.2 x 2.5'],
    buzzer=['Ø9 x 7.4', 'Sound hole Ø2'],
    button=['Flange Ø28 x 1.5', 'Button Ø22 x 3.5, R1.5', 'PRESS HERE, 3.6 high, 0.6 raised'],
    display_window=['34 x 21.5 x 1.5'],
    pod_cap=['Ø%d x %.1f, spigot Ø%d' % (2 * POD_R[1], LID_Z[1] - POD_TOP, 2 * POD_R[0]),
             'Button hole Ø23, light hole Ø7.2', 'Window 26 x 16', 'Grille 5 x Ø1.6'],
    lid=['Ø%d x %d, %g wall, %g top' % (2 * R_CASE, LID_Z[1] - LID_Z[0], LID_T, LID_TOP), 'Top edge R4',
         'Pod hole Ø%d, collar Ø%d' % (2 * LID_HOLE, 2 * COLLAR[1]), 'Knuckle R%.1f x 30' % HINGE[2]],
    gasket=['Ø%g / Ø%g x 1' % (2 * GASKET[0], 2 * GASKET[1])],
    lid_catch=['Tab %g x %g x %.1f' % (CATCH['x'][1] - CATCH['x'][0], CATCH['r'][1] - CATCH['r'][0], CATCH['flange'][2] - CATCH['z'][0]),
               'Hook %g x %g' % (CATCH['lip'] - CATCH['r'][1], CATCH['z'][1] - CATCH['z'][0]),
               'Flange %g x %g' % (CATCH['flange'][1] - CATCH['flange'][0], LID_Z[1] - LID_TOP - CATCH['flange'][2])],
    hinge_pin=['Ø%d x 88, ends 0.3 chamfer' % (2 * PIN_R)],
    drawer=['%d x %.1f x %.1f, 1.5 wall' % (2 * DRAWER[0], -DRAWER[3] - 90.5, DRAWER[2] - DRAWER[1]), 'Front R90.5 / R92 x 50', 'Grip 24 x 3'],
    drawer_seal=['R90 / R90.5 frame 50 x %.1f' % (DRAWER_OPEN[2] - DRAWER_OPEN[1] + 2)],
)
for _p in PARTS:
    _p['sizes'] = SIZES[_p['key']]
for _m in MODELS:
    if _m.get('part'):
        _m['part']['sizes'] = PART[_m['part']['key']]['sizes']
