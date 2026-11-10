"""ESP 2026: an economy class three-seat set for Aero-Chair Ltd (T Level Employer-Set Project 8730-035, Summer 2026,
Task 2).

The brief (product design specification): three seats for flights under 3 hours. Each seat 432 to 457 mm wide, a
suitable height, no more than 8 kg per seat with its frame, cushions and seat belt, fixed to the aircraft floor,
reclining 3 to 6 degrees by hand and usable by people with access needs, a life vest store (305 x 305), adjustable
armrests, a tray table no bigger than 267 x 419 that stows away, a fixed head rest, a seat belt 1170 to 1420 mm long
with a buckle anyone can work, an A4 literature pocket, a personal entertainment screen with connections, durable,
wipe clean, at least 70 % sustainable and fire resistant materials, and a budget of 15,000 pounds a set.

Design A (preferred): a lightweight beam and leg seat. Two aluminium beam tubes on two machined legs carry four
spreaders; each seat has a fabric diaphragm, foam cushions in wipe clean covers, a carbon fibre back shell that
reclines 5 degrees on a hydraulic lock, lift up armrests, a lap belt with a lift lever buckle, and on the back of
each seat the tray table, screen, USB-C power and literature pocket for the passenger behind.
Design B (concept only): fixed shell seats on a single beam (see shell_seats()).

Every component is its own part (an Inventor .ipt), listed in PARTS below with its material and the features that
make it (the Inventor build steps). The single seat and the three-seat set are assemblies (.iam) of those parts.

Coordinates (mm): the cabin floor is z = 0, X runs across the aircraft along the row (the middle seat is at x = 0),
the passenger faces -Y (forwards), so +Y is aft, towards the row behind. The front view looks at the front of the
seats. The front beam tube is on the line y = 0.

Back coordinates: each seat back is drawn upright in its own frame. Its origin is the recline pivot, x across the
seat from the seat centre, y' aft and z' up the back. back() tilts it 12 degrees (upright) or 17 degrees (fully
reclined) and moves it to the pivot.
"""
import functools
import math
import cadquery as cq

# ------------------------------------------------------------------ the numbers that define the design
SEATS = [-500, 0, 500]          # seat centre lines (x)
SEAT_W = 450                    # seat width between the armrests (brief: 432 to 457)
ARM_W = 50                      # armrest width
SPREADERS = [-750, -250, 250, 750]   # seat dividers, under the armrests
SPR_T = 8                       # spreader plate thickness
LEGS = [-270, 270]              # the two legs, to suit the floor seat tracks
LEG_T = 10                      # leg plate thickness
FOOT_Y = (20, 528)              # front and rear track fittings: 508 apart (20 track pitches of 25.4)
BEAM_Y = (0, 330)               # front and rear beam tube axes
BEAM_Z = 330                    # beam tube axis height
BEAM_R, BEAM_WALL = 25, 1.5     # beam tube 50 x 1.5
BEAM_X = 770                    # beam tube ends at +-770
SEAT_H = 440                    # seat height: top of the cushion at the front edge
CUSH_Y = (-80, 370)             # cushion front and back (450 deep)
CUSH_TOP_BACK = 410             # top of the cushion at the back: the cushion slopes back 3.8 degrees
DIA_Z = BEAM_Z + BEAM_R         # 355, top of the beams, underside of the diaphragm
DIA_T = 1.5
PIV = (420, 390)                # recline pivot (y, z)
BACK_ANGLE = 12                 # upright back angle from vertical
RECLINE = 5                     # recline (brief: 3 to 6 degrees)
BACK_HW = 220                   # half width of the back shell
SHELL_T = 1.2                   # carbon fibre shell wall
BACK_TOP = 720                  # top of the back shell (z')
HEAD_TOP = 800                  # top of the head rest (z')
ARM_PIV = (360, 590)            # armrest pivot (y, z)
ARM_Z = (600, 640)              # armrest underside and top
ARM_UP = 90                     # armrests lift 90 degrees
TRAY = (415, 265, 12)           # tray table width, length, thickness (brief: up to 419 x 267)
TRAY_HINGE = (55, 270)          # tray hinge (y', z') on the back
TRAY_DEPLOY = 90 - BACK_ANGLE   # the tray turns 78 degrees to sit level
LOCK_X = 200                    # recline lock line, from the seat centre
ANCHOR = (60, 290)              # front end of the recline lock (y, z)
LEVER = (15, -100)              # rear end of the recline lock on the back lever (y', z')
VEST = (305, 305, 50)           # life vest pack (brief: 305 x 305)
BELT_Z = None                   # set below: top of the cushion under the belt

# colours
FRAME_C = 'A9B4BF'      # machined aluminium
SHELL_C = '2E3440'      # carbon fibre, painted
SEAT_C = '1F3A5F'       # navy wool blend cover
BACK_C = '24456E'
FOAM_C = 'E8D9A8'
HEAD_C = '9AA7B5'       # grey e-leather head rest cover
TRIM = 'C9D3DD'
STEEL_C = '8E979F'
BLACK = '2B2B2B'
ORANGE = 'E8A33D'
YELLOW = 'E8C23D'
WHITE = 'EDEDED'
STRAP_C = '5B6B7A'
TRAY_C = 'D9DEE3'
SCREEN_C = '111418'
RED = 'C8372D'

# Inventor commands
NEW_PART = 'File > New > Standard (mm).ipt'
SKETCH = '3D Model tab > Sketch panel > Start 2D Sketch'
EXTRUDE = '3D Model tab > Create panel > Extrude'
REVOLVE = '3D Model tab > Create panel > Revolve'
HOLE = '3D Model tab > Modify panel > Hole'
FILLET = '3D Model tab > Modify panel > Fillet'
SHELL = '3D Model tab > Modify panel > Shell'
RECT_PATTERN = '3D Model tab > Pattern panel > Rectangular Pattern'
MIRROR_F = '3D Model tab > Pattern panel > Mirror'
NEW_ASSY = 'File > New > Standard (mm).iam'
PLACE = 'Assemble tab > Component panel > Place'
CONTENT = 'Assemble tab > Component panel > Place from Content Center'
CONSTRAIN = 'Assemble tab > Relationships panel > Constrain'
MIRROR = 'Assemble tab > Pattern panel > Mirror'
PATTERN = 'Assemble tab > Pattern panel > Pattern'

# densities, kg/m3 (a bought in part or a sandwich panel has the density that gives its catalogue mass)
AL_D = 2810           # 7075-T6 aluminium
CFRP_D = 1550         # carbon fibre epoxy (fire retardant resin)
FOAM_D = 45           # fire blocked polyurethane foam
COVER_D = 300         # 2 mm wool and recycled polyester cover with fire blocking layer (0.6 kg/m2)
DIA_D = 750           # woven aramid suspension diaphragm
PA_D = 1150           # glass filled polyamide (PA6 GF30, recycled), fire retardant
PC_D = 1200           # fire retardant polycarbonate (moulded trim)
WEB_D = 1100          # polyester webbing
STEEL_D = 7850
TI_D = 4430


# ------------------------------------------------------------------ shape helpers
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, p0, d, h):
    """A cylinder of radius r from point p0, length h along the direction d."""
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r, h, cq.Vector(*p0), cq.Vector(*d)))


def xcyl(r, x0, x1, y=0, z=0):
    return cyl(r, (x0, y, z), (1, 0, 0), x1 - x0)


def ycyl(r, y0, y1, x=0, z=0):
    return cyl(r, (x, y0, z), (0, 1, 0), y1 - y0)


def zcyl(r, z0, z1, x=0, y=0):
    return cyl(r, (x, y, z0), (0, 0, 1), z1 - z0)


def yz_poly(pts, x0, x1):
    """A plate in the YZ plane from the outline pts (y, z), from x0 to x1."""
    return cq.Workplane('YZ').workplane(offset=x0).polyline(pts).close().extrude(x1 - x0)


def strut(p0, p1, w, x0, x1):
    """A straight bar of width w in the YZ plane from p0 to p1 (y, z), from x0 to x1."""
    dy, dz = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dy, dz)
    ny, nz = -dz / L * w / 2, dy / L * w / 2
    return yz_poly([(p0[0] + ny, p0[1] + nz), (p1[0] + ny, p1[1] + nz), (p1[0] - ny, p1[1] - nz), (p0[0] - ny, p0[1] - nz)], x0, x1)


def wedge_yz(y0, y1, z0, zt0, zt1, x0, x1):
    """A block from y0 to y1 with a flat bottom at z0 and a top that slopes from zt0 (at y0) to zt1 (at y1)."""
    return yz_poly([(y0, z0), (y1, z0), (y1, zt1), (y0, zt0)], x0, x1)


def union(*shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.union(s)
    return out


def cushion_top(y):
    """Top of the seat cushion cover at y."""
    return SEAT_H + (CUSH_TOP_BACK - SEAT_H) * (y - CUSH_Y[0]) / (CUSH_Y[1] - CUSH_Y[0])


BELT_Y = (306, 354)                       # the lap belt webbing, 48 wide, across the cushion
BELT_Z = cushion_top(BELT_Y[0])           # it lies on the cushion: 414.4


def F(title, command, actions, shape, note=None):
    """One feature of a part: what you do in Inventor and the part as it stands afterwards."""
    return dict(title=title, command=command, actions=actions, shape=shape, note=note)


# ------------------------------------------------------------------ the parts
# Each part is drawn where it sits: the frame parts at x = 0 (moved across to each spreader or leg), the seat parts
# on the middle seat (x = 0), the back parts in the back frame. 'origin' is the point that becomes the origin of the
# part file, so each part model starts from a sensible datum.
PARTS = []
GROUPS = [('structure', 'Seat structure (shared by the three seats)'), ('seat', 'Seat pan, back and head rest (each seat)'),
          ('recline', 'Recline mechanism (each seat)'), ('armrest', 'Armrests'), ('belt', 'Seat belt (each seat)'),
          ('amenity', 'Tray table, screen, pocket and life vest (each seat)')]


def part(key, name, group, material, colour, density, desc, origin=(0, 0, 0), file=None, bought=False, sustainable=False):
    def deco(fn):
        PARTS.append(dict(key=key, name=name, group=group, material=material, colour=colour, density=density,
                          desc=desc, origin=origin, feats=fn, file=file or key + '.ipt', bought=bought,
                          sustainable=sustainable))
        return fn
    return deco


# ---------------------------------------------------- seat structure
@part('beam_tube', 'beam tube', 'structure', '7075-T6 aluminium tube 50 x 1.5, 70 % recycled', FRAME_C, AL_D,
      'Cross beam tube. Two run the full width of the set, front and rear, and carry the four spreaders and the two '
      'legs. Thin walled tube is the lightest way to carry the seat loads to the legs.',
      origin=(-BEAM_X, 0, BEAM_Z), sustainable=True)
def _beam_tube():
    f1 = xcyl(BEAM_R, -BEAM_X, BEAM_X, 0, BEAM_Z)
    f2 = f1.cut(xcyl(BEAM_R - BEAM_WALL, -BEAM_X - 1, BEAM_X + 1, 0, BEAM_Z))
    return [
        F('Extrude the bar', EXTRUDE,
          [NEW_PART + ' and save it as beam_tube.ipt.',
           'Start 2D Sketch on the YZ Plane. Circle diameter 50 on the origin. Finish Sketch.',
           'Extrude 1540 mm along X. Click OK.'], f1,
          'The origin is the left end of the tube, on its axis.'),
        F('Make it a tube', HOLE,
          ['Click Hole. Placement: Concentric, on the end face. Diameter 47, Termination Through All. Click OK.',
           'Material: Aluminum 7075-T6 (add it in the Material Browser if needed). Save.'], f2,
          'A 1.5 mm wall: the tube weighs 0.64 kg a metre. Beams are bought as recycled aluminium tube.'),
    ]


@part('beam_end_cap', 'beam end cap', 'structure', 'Fire retardant polycarbonate, moulded', BLACK, PC_D,
      'Push in cap that closes each end of the beam tubes, so there are no sharp edges at the aisle.',
      origin=(BEAM_X, 0, BEAM_Z))
def _beam_end_cap():
    f1 = xcyl(BEAM_R, BEAM_X, BEAM_X + 6, 0, BEAM_Z)
    f2 = f1.union(xcyl(BEAM_R - BEAM_WALL, BEAM_X - 12, BEAM_X, 0, BEAM_Z))
    return [
        F('Cap', EXTRUDE, [NEW_PART + ' and save it as beam_end_cap.ipt.',
                           'Sketch a circle diameter 50 on the YZ Plane. Extrude 6 mm.'], f1),
        F('Spigot', EXTRUDE, ['Sketch a circle diameter 47 on the back face. Extrude 12 mm. Save.'], f2,
          'The spigot is a push fit in the tube.'),
    ]


def spreader_shape():
    t = SPR_T / 2
    (ya, yb), z = BEAM_Y, BEAM_Z
    f1 = union(xcyl(35, -t, t, ya, z), xcyl(35, -t, t, yb, z), box(-t, t, ya, yb, z - 15, z + 15))
    f2 = f1.union(box(-t, t, 330, 390, z, ARM_PIV[1])).union(xcyl(20, -t, t, *ARM_PIV))
    f3 = f2.union(box(-t, t, 360, PIV[0], PIV[1] - 15, PIV[1] + 15)).union(xcyl(16, -t, t, *PIV))
    f4 = f3.cut(xcyl(BEAM_R, -t - 1, t + 1, ya, z)).cut(xcyl(BEAM_R, -t - 1, t + 1, yb, z))
    f4 = f4.cut(xcyl(6, -t - 1, t + 1, *ARM_PIV)).cut(xcyl(6, -t - 1, t + 1, *PIV))
    f5 = f4.cut(box(-t - 1, t + 1, 348, 372, 430, 560)).cut(box(-t - 1, t + 1, 60, 270, z - 8, z + 8))
    return f1, f2, f3, f4, f5


@part('spreader', 'spreader', 'structure', '7075-T6 aluminium plate, 8 thick, machined', FRAME_C, AL_D,
      'Seat divider plate, one under each armrest. It clamps on both beam tubes and carries the armrest pivot, the '
      'recline pivot of the backs either side of it and the seat belt anchors.', origin=(0, 0, BEAM_Z))
def _spreader():
    f1, f2, f3, f4, f5 = spreader_shape()
    return [
        F('Beam bosses and web', EXTRUDE,
          [NEW_PART + ' and save it as spreader.ipt.',
           'Start 2D Sketch on the YZ Plane. Two circles diameter 70 at 0 and 330 mm along Y, on the origin line, '
           'and a 30 mm wide bar joining them. Finish Sketch.', 'Extrude 8 mm, Symmetric. Click OK.'], f1,
          'The origin is on the front beam axis.'),
        F('Armrest post', EXTRUDE,
          ['Sketch on the side face: rectangle 60 wide from 330 to 390 mm along Y, up to 260 mm above the origin, with '
           'a circle diameter 40 at its top (the armrest pivot boss). Extrude 8 mm, Symmetric, Join.'], f2),
        F('Recline pivot arm', EXTRUDE,
          ['Sketch a 30 mm bar from the post to a circle diameter 32 at 420 along and 60 above the origin. Extrude '
           '8 mm, Symmetric, Join.'], f3, 'Both backs either side of the spreader turn on this boss.'),
        F('Beam bores and pivot holes', HOLE,
          ['Hole: diameter 50 Through All on each beam boss (the tubes pass through).',
           'Hole: diameter 12 Through All on the armrest pivot and on the recline pivot.'], f4),
        F('Lightening holes', EXTRUDE,
          ['Sketch a 24 x 130 slot in the post and a 210 x 16 slot in the web. Extrude Cut Through All.',
           'Material: Aluminum 7075-T6. Save.'], f5, 'Every gram counts: each slot saves weight where the plate is lightly loaded.'),
    ]


LEG_A, LEG_B = (FOOT_Y[0], 45), (FOOT_Y[1], 45)          # foot nodes
LEG_C, LEG_D = (BEAM_Y[0], BEAM_Z), (BEAM_Y[1], BEAM_Z)    # beam nodes
BAR = (LEG_A[0] + (LEG_C[0] - LEG_A[0]) * (150 - LEG_A[1]) / (LEG_C[1] - LEG_A[1]), 150)   # baggage bar on the front strut


@part('leg', 'leg', 'structure', '7075-T6 aluminium plate, 10 thick, machined', FRAME_C, AL_D,
      'Machined leg: a braced frame from the two beam tubes down to the front and rear track fittings. Two per set. '
      'It carries every seat load into the aircraft floor.', origin=(0, LEG_A[0], 0))
def _leg():
    t = LEG_T / 2
    f1 = union(strut(LEG_A, LEG_C, 40, -t, t), strut(LEG_B, LEG_D, 40, -t, t))
    f2 = f1.union(strut(LEG_C, LEG_D, 30, -t, t)).union(strut(LEG_A, LEG_D, 30, -t, t))
    f3 = f2.union(xcyl(35, -t, t, *LEG_C)).union(xcyl(35, -t, t, *LEG_D))
    f3 = f3.union(box(-t, t, LEG_A[0] - 30, LEG_A[0] + 30, 25, 45)).union(box(-t, t, LEG_B[0] - 30, LEG_B[0] + 30, 25, 45))
    f4 = f3.cut(xcyl(BEAM_R, -t - 1, t + 1, *LEG_C)).cut(xcyl(BEAM_R, -t - 1, t + 1, *LEG_D)).cut(xcyl(10, -t - 1, t + 1, *BAR))
    return [
        F('Struts', EXTRUDE,
          [NEW_PART + ' and save it as leg.ipt.',
           'Start 2D Sketch on the YZ Plane. Draw the front strut 40 wide from the front foot (20, 45) up to the front '
           'beam (0, 330), and the rear strut 40 wide from the rear foot (528, 45) up to the rear beam (330, 330).',
           'Extrude 10 mm, Symmetric.'], f1, 'The origin is the front track fitting point on the floor.'),
        F('Chord and brace', EXTRUDE,
          ['Sketch a 30 mm bar between the two beam points and a 30 mm brace from the front foot to the rear beam. '
           'Extrude 10 mm, Symmetric, Join.'], f2,
          'Struts, chord and brace make two triangles: a braced frame carries load by tension and compression, not bending.'),
        F('Beam bosses and feet', EXTRUDE,
          ['Sketch circles diameter 70 on the beam points and 60 x 20 pads under each foot. Extrude 10 mm, Symmetric, Join.'], f3),
        F('Bores', HOLE,
          ['Hole: diameter 50 Through All on both bosses (the beam tubes), and diameter 20 on the front strut 150 mm up '
           '(the baggage bar). Material: Aluminum 7075-T6. Save.'], f4,
          'See the FEA: the leg under a 9 g forward crash load.'),
    ]


@part('beam_collar', 'beam clamp collar', 'structure', '7075-T6 aluminium, split collar with M5 screw', FRAME_C, AL_D,
      'Split clamp collar beside each leg boss. It locks the leg to the beam tube so the leg cannot slide.',
      origin=(0, 0, BEAM_Z))
def _beam_collar():
    f1 = xcyl(32, -4, 4, 0, BEAM_Z).cut(xcyl(BEAM_R, -5, 5, 0, BEAM_Z))
    f2 = f1.union(box(-4, 4, -6, 6, BEAM_Z - 44, BEAM_Z - 31))
    f3 = f2.cut(box(-5, 5, -1, 1, BEAM_Z - 45, BEAM_Z - 24))
    return [
        F('Ring', EXTRUDE, [NEW_PART + ' and save it as beam_collar.ipt.',
                            'Sketch circles diameter 64 and 50 on the YZ Plane. Extrude 8 mm, Symmetric.'], f1),
        F('Clamp lug', EXTRUDE, ['Sketch a 12 x 13 rectangle under the ring. Extrude 8 mm, Symmetric, Join.'], f2),
        F('Split', EXTRUDE, ['Sketch a 2 mm slot up the middle of the lug into the bore. Extrude Cut Through All. Save.'], f3,
          'An M5 screw across the lug closes the split and grips the tube.'),
    ]


@part('track_fitting', 'track fitting', 'structure', '7075-T6 aluminium, machined', FRAME_C, AL_D,
      'Floor fitting under each foot of a leg. It sits in the aircraft seat track and is held by the track stud. '
      'Two per leg.', origin=(0, 0, 0))
def _track_fitting():
    f1 = box(-12, 12, -30, 30, 0, 25)
    f2 = f1.cut(zcyl(6, -1, 26))
    f3 = f2.cut(box(-13, 13, -31, -22, 18, 26)).cut(box(-13, 13, 22, 31, 18, 26))
    return [
        F('Block', EXTRUDE, [NEW_PART + ' and save it as track_fitting.ipt.',
                             'Sketch a 24 x 60 rectangle on the XZ Plane (the floor), centred. Extrude 25 mm.'], f1),
        F('Stud hole', HOLE, ['Hole on the top face, on the centre: diameter 12, Through All.'], f2),
        F('Chamfered ends', EXTRUDE, ['Sketch 9 x 8 steps at each end of the top. Extrude Cut Through All. Save.'], f3,
          'The leg foot pad (60 long) sits on the top.'),
    ]


@part('track_stud', 'track stud', 'structure', 'Bought in: 15-5PH stainless track stud with shear plunger', STEEL_C,
      STEEL_D, 'Seat track stud. Its foot slides under the lips of the aircraft seat track and locks at a 25.4 mm '
      'pitch, so the row can be moved to any seat pitch the airline wants.', bought=True)
def _track_stud():
    f1 = zcyl(6, -20, 25)
    f2 = f1.union(zcyl(10, -20, -12))
    return [
        F('Stud', EXTRUDE, ['Place from Content Center, or ' + NEW_PART + ': circle diameter 12 on the XZ Plane, '
                            'Extrude 45 mm, 20 mm below the floor.'], f1),
        F('Track foot', EXTRUDE, ['Sketch a circle diameter 20 on the bottom face. Extrude 8 mm. Save.'], f2,
          'The foot locks under the lips of the floor track.'),
    ]


@part('baggage_bar', 'baggage bar', 'structure', '6061 aluminium tube 20 x 1.2, recycled', FRAME_C, AL_D,
      'Restraint bar across the front of the under seat space. It stops bags sliding forward into the passengers\' '
      'feet in a hard landing.', origin=(-700, BAR[0], BAR[1]), sustainable=True)
def _baggage_bar():
    f1 = xcyl(10, -700, 700, *BAR)
    f2 = f1.cut(xcyl(8.8, -701, 701, *BAR))
    return [
        F('Extrude the bar', EXTRUDE, [NEW_PART + ' and save it as baggage_bar.ipt.',
                                       'Sketch a circle diameter 20 on the YZ Plane. Extrude 1400 mm along X.'], f1),
        F('Make it a tube', HOLE, ['Hole: diameter 17.6, Through All, concentric. Save.'], f2),
    ]


# ---------------------------------------------------- seat pan, back and head rest (each seat, drawn on the middle seat)
@part('seat_diaphragm', 'seat diaphragm', 'seat', 'Woven aramid and polyester suspension, fire retardant', BLACK, DIA_D,
      'The seat pan: a tight woven diaphragm stretched between the beam tubes. Lighter than a metal pan and it gives '
      'a little, so the cushion can be thinner.', origin=(-223, BEAM_Y[0] - BEAM_R, DIA_Z))
def _seat_diaphragm():
    f1 = box(-223, 223, BEAM_Y[0] - BEAM_R, BEAM_Y[1] + BEAM_R, DIA_Z, DIA_Z + DIA_T)
    return [F('Extrude the sheet', EXTRUDE,
              [NEW_PART + ' and save it as seat_diaphragm.ipt.',
               'Sketch a 446 x 380 rectangle on the XZ Plane. Extrude 1.5 mm. Save.'], f1,
              'In the seat it wraps round both tubes and is laced tight underneath.')]


def foam_shape():
    return wedge_yz(CUSH_Y[0] + 2, CUSH_Y[1] - 2, DIA_Z + DIA_T, SEAT_H - 2, CUSH_TOP_BACK - 2, -223, 223)


@part('seat_foam', 'seat cushion foam', 'seat', 'Fire blocked polyurethane foam, 45 kg/m3, 30 % bio based', FOAM_C, FOAM_D,
      'Seat cushion. Thicker at the front (80 mm) than the back (50 mm), so the seat slopes back 3.8 degrees and '
      'the passenger does not slide forward.', origin=(-223, CUSH_Y[0] + 2, DIA_Z + DIA_T))
def _seat_foam():
    f1 = foam_shape()
    return [F('Extrude the profile', EXTRUDE,
              [NEW_PART + ' and save it as seat_foam.ipt.',
               'Start 2D Sketch on the YZ Plane: the side profile, 446 deep, 80 high at the front and 50 at the back. '
               'Finish Sketch.', 'Extrude 446 mm, Symmetric. Save.'], f1,
              'Fire blocked foam passes the oil burner test for seat cushions (CS 25.853(c)).')]


@part('seat_cover', 'seat cushion cover', 'seat', 'Wool and recycled polyester, wipe clean, fire blocked, 2 mm', SEAT_C,
      COVER_D, 'Dress cover over the seat cushion. Hook and loop fastened, so the crew can change it between flights; '
      'stain resistant and wipe clean.', origin=(-225, CUSH_Y[0], DIA_Z + DIA_T), sustainable=True)
def _seat_cover():
    f1 = wedge_yz(CUSH_Y[0], CUSH_Y[1], DIA_Z + DIA_T, SEAT_H, CUSH_TOP_BACK, -225, 225)
    f2 = f1.cut(foam_shape())
    return [
        F('Outer shape', EXTRUDE, [NEW_PART + ' and save it as seat_cover.ipt.',
                                   'Sketch the side profile 450 deep, 82 high at the front and 52 at the back. '
                                   'Extrude 450 mm, Symmetric.'], f1, 'The top of the cover at the front edge is the seat height: 440 mm.'),
        F('Hollow it', SHELL, ['Click Shell. Remove the bottom face. Thickness 2 mm, Inside. Save.'], f2,
          'A 2 mm skin: the wool blend face, the fire blocking layer and the stain resistant finish.'),
    ]


def back_shell_shape():
    w, t = BACK_HW, SHELL_T
    f1 = box(-w, w, 0, 45, 40, BACK_TOP)
    f2 = f1.cut(box(-w + t, w - t, -1, 45 - t, 40 + t, BACK_TOP - t))
    lugs = box(214, 220, -15, 25, -20, 45).union(box(-220, -214, -15, 25, -20, 45))
    f3 = f2.union(lugs).cut(xcyl(6, -221, 221, 0, 0))
    f4 = f3.union(box(LOCK_X + 4, LOCK_X + 12, 5, 25, -110, 42)).cut(xcyl(4, LOCK_X + 3, LOCK_X + 13, *LEVER))
    return f1, f2, f3, f4


@part('back_shell', 'back shell', 'seat', 'Carbon fibre epoxy, 1.2 mm, fire retardant resin', SHELL_C, CFRP_D,
      'The seat back: a thin carbon fibre shell, open at the front for the back cushion. It turns on the recline '
      'pivot, and carries the tray table, screen and literature pocket for the passenger behind.')
def _back_shell():
    f1, f2, f3, f4 = back_shell_shape()
    return [
        F('Block out the back', EXTRUDE,
          [NEW_PART + ' and save it as back_shell.ipt.',
           'Start 2D Sketch on the XZ Plane (here: the back seen from above, Y up the back is Inventor Y). Rectangle '
           '440 x 45. Extrude 680 mm, starting 40 mm above the origin. The origin is the recline pivot.'], f1,
          'Parts of the back are drawn upright; the assembly tilts the back 12 degrees.'),
        F('Shell it', SHELL, ['Click Shell. Remove the front face. Thickness 1.2 mm, Inside. Click OK.'], f2,
          'A 1.2 mm carbon fibre shell is stiff and very light: under 1 kg.'),
        F('Pivot lugs', EXTRUDE,
          ['Sketch a 6 x 40 rectangle on each side face, from 20 below to 45 above the origin. Extrude Join.',
           'Hole: diameter 12, Through All, on the origin (the recline pivot axis).'], f3),
        F('Recline lever', EXTRUDE,
          ['Sketch a 20 mm wide lever under the shell, 204 mm from the centre, down to 110 mm below the pivot. Extrude 8 mm.',
           'Hole: diameter 8 at 100 mm below the pivot, 15 mm behind it (the recline lock pin). Save.'], f4,
          'The recline lock pushes on this lever: the back can only move when the lock is released.'),
    ]


def back_foam_shape():
    return box(-210, 210, -30, 0, 22, 708)


@part('back_foam', 'back cushion foam', 'seat', 'Fire blocked polyurethane foam, 45 kg/m3, 30 % bio based', FOAM_C, FOAM_D,
      'Back cushion, 30 mm thick, in the front of the back shell.', origin=(0, 0, 22))
def _back_foam():
    f1 = back_foam_shape()
    f2 = f1.edges('|Z and <Y').fillet(10)
    return [
        F('Extrude the pad', EXTRUDE, [NEW_PART + ' and save it as back_foam.ipt.',
                                       'Sketch a 420 x 30 rectangle on the XZ Plane, 22 mm up. Extrude 686 mm.'], f1),
        F('Round the front edges', FILLET, ['Fillet the two front vertical edges, radius 10. Save.'], f2,
          'Lumbar shaping comes from the cover pattern and the diaphragm, not extra foam.'),
    ]


@part('back_cover', 'back cushion cover', 'seat', 'Wool and recycled polyester, wipe clean, fire blocked, 2 mm', BACK_C,
      COVER_D, 'Dress cover over the back cushion. Zipped at the back, so it can be changed in minutes.',
      origin=(0, 0, 20), sustainable=True)
def _back_cover():
    f1 = box(-212, 212, -32, 0, 20, 710).edges('|Z and <Y').fillet(11)
    f2 = f1.cut(back_foam_shape().edges('|Z and <Y').fillet(10))
    return [
        F('Outer shape', EXTRUDE, [NEW_PART + ' and save it as back_cover.ipt.',
                                   'Sketch a 424 x 32 rectangle, 20 mm up. Extrude 690 mm. Fillet the front edges R11.'], f1),
        F('Hollow it', SHELL, ['Shell: remove the back face, thickness 2 mm. Save.'], f2),
    ]


@part('headrest', 'head rest', 'seat', 'Moulded foam on a PA6 frame, grey e-leather cover (recycled leather fibre)',
      HEAD_C, 120, 'Fixed head rest on top of the back, as the brief asks: no moving parts, nothing to break.',
      origin=(0, 0, BACK_TOP), sustainable=True)
def _headrest():
    f1 = box(-200, 200, -50, 40, BACK_TOP, HEAD_TOP)
    f2 = f1.edges('|Y').fillet(25)
    f3 = f2.edges('|X and <Y').fillet(12)
    return [
        F('Block', EXTRUDE, [NEW_PART + ' and save it as headrest.ipt.',
                             'Sketch a 400 x 90 rectangle on the XZ Plane, 720 mm up (the top of the back shell). Extrude 80 mm.'], f1),
        F('Round the corners', FILLET, ['Fillet the four front to back edges, radius 25.'], f2),
        F('Soft front', FILLET, ['Fillet the two front edges across the seat, radius 12. Save.'], f3,
          'The head rest stands 50 mm in front of the back cushion so it meets the back of the head.'),
    ]


@part('back_pivot_pin', 'recline pivot pin', 'seat', '17-4PH stainless steel, 12 dia', STEEL_C, STEEL_D,
      'Pin through a spreader and the pivot lugs of the backs either side. Both backs turn on it. Two per set.',
      origin=(-36, PIV[0], PIV[1]))
def _back_pivot_pin():
    f1 = xcyl(6, -36, 36, *PIV)
    f2 = f1.union(xcyl(9, 36, 39, *PIV))
    return [F('Pin', EXTRUDE, [NEW_PART + ' and save it as back_pivot_pin.ipt.', 'Circle diameter 12. Extrude 72 mm.'], f1),
            F('Head', EXTRUDE, ['Circle diameter 18 on one end. Extrude 3 mm. Save.'], f2,
              'A circlip in a groove holds the other end.')]


@part('end_pivot_pin', 'end recline pivot pin', 'seat', '17-4PH stainless steel, 12 dia', STEEL_C, STEEL_D,
      'Shorter pin through an end spreader and one back. Two per set, one at each end.', origin=(-36, PIV[0], PIV[1]))
def _end_pivot_pin():
    f1 = xcyl(6, -36, 4, *PIV)
    f2 = f1.union(xcyl(9, 4, 8, *PIV))
    return [F('Pin', EXTRUDE, [NEW_PART + ' and save it as end_pivot_pin.ipt.', 'Circle diameter 12. Extrude 40 mm.'], f1),
            F('Head', EXTRUDE, ['Circle diameter 18 on one end. Extrude 4 mm. Save.'], f2)]


# ---------------------------------------------------- recline mechanism (each seat)
def lock_line(recline=0.0):
    """Front and rear pin of the recline lock (y, z), its length and its angle, for the back at recline degrees."""
    a = math.radians(-(BACK_ANGLE + recline))
    ly, lz = LEVER
    ry = PIV[0] + ly * math.cos(a) - lz * math.sin(a)
    rz = PIV[1] + ly * math.sin(a) + lz * math.cos(a)
    L = math.hypot(ry - ANCHOR[0], rz - ANCHOR[1])
    return ANCHOR, (ry, rz), L, math.degrees(math.atan2(rz - ANCHOR[1], ry - ANCHOR[0]))


@part('recline_bracket', 'recline lock bracket', 'recline', '7075-T6 aluminium, machined', FRAME_C, AL_D,
      'Half clamp under the front beam tube that the front end of the recline lock pins to.',
      origin=(LOCK_X + 4, ANCHOR[0], ANCHOR[1]))
def _recline_bracket():
    x0, x1 = LOCK_X + 4, LOCK_X + 12
    ring = xcyl(31, x0, x1, BEAM_Y[0], BEAM_Z).cut(box(x0 - 1, x1 + 1, -40, 40, BEAM_Z, BEAM_Z + 40))
    f1 = ring.cut(xcyl(BEAM_R, x0 - 1, x1 + 1, BEAM_Y[0], BEAM_Z))
    f2 = f1.union(box(x0, x1, 15, ANCHOR[0] + 12, ANCHOR[1] - 12, 305)).cut(xcyl(BEAM_R, x0 - 1, x1 + 1, BEAM_Y[0], BEAM_Z))
    f3 = f2.cut(xcyl(4, x0 - 1, x1 + 1, *ANCHOR))
    return [
        F('Half ring', EXTRUDE, [NEW_PART + ' and save it as recline_bracket.ipt.',
                                 'Sketch the lower half of a ring, 62 outside and 50 inside, on the YZ Plane. Extrude 8 mm.'], f1),
        F('Tab', EXTRUDE, ['Sketch a tab from the ring back to 72 mm behind the beam axis. Extrude 8 mm, Join.'], f2),
        F('Pin hole', HOLE, ['Hole diameter 8, Through All, 60 behind and 40 below the beam axis. Save.'], f3),
    ]


@part('recline_lock', 'recline lock body', 'recline', 'Bought in: hydraulic locking cylinder, 22 dia, 1500 N', ORANGE,
      2600, 'Hydraulic recline lock (a "hydrolock"). Locked, it holds the back where it is. Press the recline '
            'button and the valve opens: lean back to recline, sit up and it returns.', bought=True)
def _recline_lock():
    f1 = xcyl(8, -4, 4, 0, 0).union(box(-4, 4, 0, 14, -6, 6))
    f2 = f1.union(ycyl(11, 12, 210))
    f3 = f2.cut(ycyl(5, 20, 211)).cut(xcyl(4, -5, 5, 0, 0))
    return [
        F('Eye', EXTRUDE, ['Place from Content Center or ' + NEW_PART + ' and save it as recline_lock.ipt.',
                           'Sketch a circle diameter 16 on the YZ Plane. Extrude 8 mm, Symmetric. Sketch a 14 x 12 neck. Extrude.'], f1),
        F('Cylinder', EXTRUDE, ['Circle diameter 22 on the end of the neck. Extrude 198 mm.'], f2),
        F('Bore and pin hole', HOLE, ['Hole diameter 10, 191 deep, on the end. Hole diameter 8 through the eye. Save.'], f3,
          'The origin is the front pin: the lock turns about it as the back reclines.'),
    ]


@part('recline_rod', 'recline lock rod', 'recline', 'Bought in: chromed steel rod 8 dia with eye (part of the lock)',
      TRIM, STEEL_D, 'Piston rod of the recline lock. It slides into the cylinder as the back reclines.', bought=True)
def _recline_rod():
    f1 = xcyl(8, -4, 4, 0, 0).cut(xcyl(4, -5, 5, 0, 0))
    f2 = f1.union(ycyl(4, -200, -6))
    return [
        F('Eye', EXTRUDE, ['Circle diameter 16 on the YZ Plane, Extrude 8 mm Symmetric. Hole diameter 8 through it.'], f1,
          'The origin is the rear pin, on the back lever.'),
        F('Rod', EXTRUDE, ['Circle diameter 8 on the eye. Extrude 194 mm forward. Save.'], f2),
    ]


@part('lock_pin', 'recline lock pin', 'recline', '17-4PH stainless steel, 8 dia', STEEL_C, STEEL_D,
      'Headed pin at each end of the recline lock. Two per seat.', origin=(LOCK_X - 7, 0, 0))
def _lock_pin():
    f1 = xcyl(4, LOCK_X - 4, LOCK_X + 12)
    f2 = f1.union(xcyl(7, LOCK_X - 7, LOCK_X - 4))
    return [F('Pin', EXTRUDE, [NEW_PART + ' and save it as lock_pin.ipt.', 'Circle diameter 8. Extrude 16 mm.'], f1),
            F('Head', EXTRUDE, ['Circle diameter 14 on one end. Extrude 3 mm. Save.'], f2)]


@part('recline_button', 'recline button', 'recline', 'Fire retardant polycarbonate button and bezel', YELLOW, PC_D,
      'Large recline button on top of the armrest, 25 mm from its front: easy to find and press with a thumb or the '
      'side of a hand, and the cabin crew can reach it from the aisle.', origin=(0, -25, ARM_Z[1]))
def _recline_button():
    f1 = zcyl(12, ARM_Z[1], ARM_Z[1] + 3, 0, -25)
    f2 = f1.union(zcyl(8, ARM_Z[1] + 3, ARM_Z[1] + 7, 0, -25))
    return [F('Bezel', EXTRUDE, [NEW_PART + ' and save it as recline_button.ipt.', 'Circle diameter 24. Extrude 3 mm.'], f1),
            F('Button', EXTRUDE, ['Circle diameter 16 on the top. Extrude 4 mm. Save.'], f2,
              'A Bowden cable inside the armrest links the button to the valve on the recline lock.')]


# ---------------------------------------------------- armrests (drawn on the spreader at x = 0, lowered)
def armrest_shape():
    a0, a1 = ARM_Z
    f1 = box(-25, 25, -40, 380, a0, a1)
    f2 = f1.union(box(-25, 25, 330, 390, 565, a0)).union(xcyl(30, -25, 25, *ARM_PIV).intersect(box(-25, 25, 330, 390, 560, a0)))
    f3 = f2.cut(box(-5, 5, 300, 400, 550, a1 + 1))
    f4 = f3.cut(box(-22.5, 22.5, -37.5, 300, a0 - 1, a1 - 2.5)).cut(xcyl(6, -26, 26, *ARM_PIV))
    return f1, f2, f3, f4


@part('armrest', 'armrest', 'armrest', 'Glass filled polyamide PA6 GF30 (recycled), fire retardant', SHELL_C, PA_D,
      'Lift up armrest, four per set. It turns 90 degrees on its pivot at the back so a passenger with access needs '
      'can slide across from an aisle wheelchair; detents hold it up or down.', origin=(0, ARM_PIV[0], ARM_PIV[1]))
def _armrest():
    f1, f2, f3, f4 = armrest_shape()
    return [
        F('Bar', EXTRUDE, [NEW_PART + ' and save it as armrest.ipt.',
                           'Sketch a 50 x 420 rectangle on the XZ Plane, 600 mm up. Extrude 40 mm.'], f1),
        F('Pivot end', EXTRUDE, ['Sketch the pivot end on the YZ Plane: 60 long, down to 565, round on the pivot. '
                                 'Extrude 50 mm, Symmetric, Join.'], f2),
        F('Slot for the spreader', EXTRUDE, ['Sketch a 10 mm slot up the middle of the pivot end. Extrude Cut 100 mm.'], f3,
          'The spreader fits in the slot, between the two cheeks.'),
        F('Hollow and pivot hole', SHELL, ['Shell: remove the bottom face, 2.5 mm walls (an open channel).',
                                           'Hole: diameter 12, Through All, on the pivot. Save.'], f4,
          'A moulded channel: stiff, light and quick to make.'),
    ]


@part('armrest_pad', 'armrest pad', 'armrest', 'Soft touch TPE over foam, wipe clean', BLACK, 600,
      'Soft pad on top of each armrest.', origin=(0, 0, ARM_Z[1]))
def _armrest_pad():
    f1 = box(-25, 25, 0, 330, ARM_Z[1], ARM_Z[1] + 8)
    f2 = f1.edges('|Y and >Z').fillet(4)
    return [F('Pad', EXTRUDE, [NEW_PART + ' and save it as armrest_pad.ipt.', 'Sketch a 50 x 330 rectangle. Extrude 8 mm.'], f1),
            F('Round the edges', FILLET, ['Fillet the two long top edges, radius 4. Save.'], f2)]


@part('armrest_pin', 'armrest pivot pin', 'armrest', '17-4PH stainless steel, 12 dia', STEEL_C, STEEL_D,
      'Pin through the armrest cheeks and the spreader.', origin=(-25, ARM_PIV[0], ARM_PIV[1]))
def _armrest_pin():
    f1 = xcyl(6, -25, 25, *ARM_PIV)
    f2 = f1.union(xcyl(9, 25, 28, *ARM_PIV))
    return [F('Pin', EXTRUDE, [NEW_PART + ' and save it as armrest_pin.ipt.', 'Circle diameter 12. Extrude 50 mm.'], f1),
            F('Head', EXTRUDE, ['Circle diameter 18 on one end. Extrude 3 mm. Save.'], f2)]


# ---------------------------------------------------- seat belt (each seat, middle seat)
@part('belt_anchor', 'belt anchor', 'belt', '7075-T6 aluminium, machined', FRAME_C, AL_D,
      'Lap belt anchor bolted to the spreader each side of the seat. Two per seat; the right one is the mirror image.',
      origin=(227, 330, 388))
def _belt_anchor():
    f1 = box(227, 246, 315, 345, 368, 408)
    f2 = f1.cut(xcyl(5, 226, 247, 330, 388))
    return [F('Block', EXTRUDE, [NEW_PART + ' and save it as belt_anchor.ipt.', 'Sketch a 30 x 40 rectangle on the YZ Plane. Extrude 19 mm.'], f1),
            F('Bolt hole', HOLE, ['Hole diameter 10, Through All, in the middle. Save.'], f2,
              'An M10 bolt holds it to the spreader; the webbing loop goes round it.')]


def strap(sx):
    """Lap belt webbing from the anchor on side sx up and across the cushion towards the middle."""
    y0, y1 = BELT_Y
    xa, xb = (225, 227) if sx > 0 else (-227, -225)
    up = box(xa, xb, y0, y1, 385, BELT_Z + 2)
    if sx > 0:
        across = box(40, 227, y0, y1, BELT_Z, BELT_Z + 2)
    else:
        across = box(-227, -40, y0, y1, BELT_Z, BELT_Z + 2)
    return up, up.union(across)


@part('belt_strap_buckle', 'belt webbing, buckle side', 'belt', 'Polyester webbing 48 wide, 380 long', STRAP_C, WEB_D,
      'Fixed length half of the lap belt, from the left anchor to the buckle. Shown laid on the cushion.',
      origin=(-227, BELT_Y[0], 385))
def _belt_strap_buckle():
    f1, f2 = strap(-1)
    return [F('Strap up from the anchor', EXTRUDE, [NEW_PART + ' and save it as belt_strap_buckle.ipt.',
                                                     'Sketch a 2 x 48 rectangle. Extrude 31 mm up.'], f1),
            F('Strap across the cushion', EXTRUDE, ['Sketch a 2 x 48 rectangle on the side face. Extrude 187 mm across. Save.'], f2,
              'Shown short and laid flat: in use the webbing goes round the lap.')]


@part('belt_strap_adjust', 'belt webbing, adjuster side', 'belt', 'Polyester webbing 48 wide, 790 to 1040 long', STRAP_C,
      WEB_D, 'Adjustable half of the lap belt, from the right anchor through the slide bar in the tongue.',
      origin=(225, BELT_Y[0], 385))
def _belt_strap_adjust():
    f1, f2 = strap(1)
    return [F('Strap up from the anchor', EXTRUDE, [NEW_PART + ' and save it as belt_strap_adjust.ipt.',
                                                     'Sketch a 2 x 48 rectangle. Extrude 31 mm up.'], f1),
            F('Strap across the cushion', EXTRUDE, ['Sketch a 2 x 48 rectangle on the side face. Extrude 187 mm across. Save.'], f2)]


BZ = BELT_Z + 2     # top of the webbing


@part('buckle_body', 'buckle body', 'belt', 'Aluminium alloy, anodised (part of the TSO-C22 belt)', TRIM, 2700,
      'Lift lever buckle body, on the end of the buckle side webbing. The tongue slides into the slot and latches.',
      origin=(-50, BELT_Y[0] - 1, BZ), bought=True)
def _buckle_body():
    f1 = box(-50, 20, BELT_Y[0] - 1, BELT_Y[1] + 1, BZ, BZ + 10)
    f2 = f1.cut(box(0, 21, 318, 342, BZ + 3, BZ + 7))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as buckle_body.ipt.', 'Sketch a 70 x 50 rectangle. Extrude 10 mm.'], f1),
            F('Tongue slot', EXTRUDE, ['Sketch a 24 x 4 slot on the end face. Extrude Cut 21 mm. Save.'], f2)]


@part('buckle_lever', 'buckle lift lever', 'belt', 'Aluminium alloy, anodised, red release mark', RED, 2700,
      'The lift lever. Pull it up and the tongue is released: one movement, with either hand, by the passenger or the '
      'crew. No buttons to find or press hard.', origin=(-45, 309, BZ + 10), bought=True)
def _buckle_lever():
    f1 = box(-45, 15, 309, 351, BZ + 10, BZ + 14)
    f2 = f1.union(box(5, 15, 309, 351, BZ + 14, BZ + 17))
    return [F('Lever', EXTRUDE, [NEW_PART + ' and save it as buckle_lever.ipt.', 'Sketch a 60 x 42 rectangle. Extrude 4 mm.'], f1),
            F('Finger lip', EXTRUDE, ['Sketch a 10 x 42 rectangle at the free end. Extrude 3 mm. Save.'], f2,
              'The lip makes the lever easy to lift with one finger.')]


@part('belt_tongue', 'belt tongue', 'belt', 'Steel, zinc plated, with slide bar adjuster', STEEL_C, STEEL_D,
      'Tongue (link) on the adjustable webbing. It latches into the buckle; the slide bar sets the belt length.',
      origin=(5, 318, BZ + 3), bought=True)
def _belt_tongue():
    f1 = box(5, 60, 318, 342, BZ + 3, BZ + 7)
    f2 = f1.union(box(42, 60, 312, 348, BZ, BZ + 7))
    return [F('Plate', EXTRUDE, [NEW_PART + ' and save it as belt_tongue.ipt.', 'Sketch a 55 x 24 rectangle. Extrude 4 mm.'], f1),
            F('Slide bar', EXTRUDE, ['Sketch an 18 x 36 rectangle at the outer end. Extrude 7 mm down to the webbing. Save.'], f2,
              'The webbing passes round the slide bar: pull the free end to tighten.')]


# ---------------------------------------------------- tray, screen, pocket (on the back, back coordinates) and life vest
TW, TL, TT = TRAY


@part('tray_table', 'tray table', 'amenity', 'Aluminium honeycomb sandwich with PC laminate faces', TRAY_C, 250,
      'Tray table on the back of the seat for the passenger behind: 415 x 265 (the brief allows up to 419 x 267). '
      'It folds down on its hinge to sit level and stows flat against the back.', origin=(0, TRAY_HINGE[0], TRAY_HINGE[1]))
def _tray_table():
    y0 = TRAY_HINGE[0] - TT / 2
    f1 = box(-TW / 2, TW / 2, y0, y0 + TT, TRAY_HINGE[1] - 8, TRAY_HINGE[1] - 8 + TL)
    f2 = f1.edges('|Y').fillet(15)
    f3 = f2.cut(xcyl(4, -TW / 2 - 1, -TW / 2 + 3.5, *TRAY_HINGE)).cut(xcyl(4, TW / 2 - 3.5, TW / 2 + 1, *TRAY_HINGE))
    f4 = f3.cut(ycyl(40, y0 + TT - 1.5, y0 + TT + 1, 0, TRAY_HINGE[1] + 150))
    return [
        F('Panel', EXTRUDE, [NEW_PART + ' and save it as tray_table.ipt.',
                             'Sketch a 415 x 265 rectangle on the XY Plane. Extrude 12 mm.'], f1),
        F('Round the corners', FILLET, ['Fillet the four corner edges, radius 15.'], f2),
        F('Hinge holes', HOLE, ['Hole diameter 8, 4 deep, in each end, 8 mm up from the bottom edge.'], f3),
        F('Cup recess', EXTRUDE, ['Sketch a circle diameter 80 on the top face. Extrude Cut 1.5 mm. Save.'], f4,
          'The recess stops a cup sliding.'),
    ]


@part('tray_arm', 'tray hinge arm', 'amenity', '7075-T6 aluminium, machined', FRAME_C, AL_D,
      'Hinge bracket each side of the tray, bonded to the back shell. Its stub is the tray hinge pin; a stop sets the '
      'tray level when it is folded down.', origin=(209, 45, TRAY_HINGE[1]))
def _tray_arm():
    f1 = box(209, 215, 45, 70, TRAY_HINGE[1] - 15, TRAY_HINGE[1] + 15)
    f2 = f1.union(xcyl(4, 204, 209, *TRAY_HINGE))
    return [F('Bracket', EXTRUDE, [NEW_PART + ' and save it as tray_arm.ipt.', 'Sketch a 25 x 30 rectangle. Extrude 6 mm.'], f1),
            F('Hinge stub', EXTRUDE, ['Circle diameter 8 on the inner face, 10 mm from the shell. Extrude 5 mm. Save.'], f2,
              'Mirror the part for the other side in the assembly.')]


LATCH_Z = 537


@part('tray_latch', 'tray latch', 'amenity', 'Fire retardant polycarbonate, moulded', BLACK, PC_D,
      'Turn button that holds the stowed tray up. Turn it a quarter turn to let the tray down.', origin=(0, 45, LATCH_Z))
def _tray_latch():
    f1 = ycyl(8, 45, 50, 0, LATCH_Z)
    f2 = f1.union(box(-12, 12, 50, 60, LATCH_Z - 5, LATCH_Z + 5))
    return [F('Base', EXTRUDE, [NEW_PART + ' and save it as tray_latch.ipt.', 'Circle diameter 16. Extrude 5 mm.'], f1),
            F('Turn tab', EXTRUDE, ['Sketch a 24 x 10 rectangle on the base. Extrude 10 mm. Save.'], f2)]


@part('ife_screen', 'entertainment screen', 'amenity', 'Bought in: 10.1 inch touch screen, 1280 x 800, Bluetooth audio',
      SCREEN_C, 760, 'Personal entertainment screen in the back of the seat, at the eye height of the passenger '
                     'behind. Streams films from the cabin server and pairs with Bluetooth headphones.',
      origin=(0, 45, 555), bought=True)
def _ife_screen():
    f1 = box(-125, 125, 45, 62, 555, 715)
    f2 = f1.cut(box(-110, 110, 60, 63, 568, 705))
    return [F('Housing', EXTRUDE, [NEW_PART + ' and save it as ife_screen.ipt.', 'Sketch a 250 x 160 rectangle. Extrude 17 mm.'], f1),
            F('Glass recess', EXTRUDE, ['Sketch the 220 x 137 display area. Extrude Cut 2 mm. Save.'], f2,
              'Modelled from the maker\'s outline drawing.')]


@part('usb_module', 'power and audio module', 'amenity', 'Bought in: USB-C 60 W and USB-A ports, 3.5 mm audio jack',
      BLACK, 1100, 'Connectivity: a USB-C fast charge port, a USB-A port and a headphone jack beside the screen.',
      origin=(140, 45, 600), bought=True)
def _usb_module():
    f1 = box(140, 190, 45, 58, 600, 650)
    f2 = f1.cut(box(152, 178, 57, 59, 632, 640)).cut(box(155, 175, 57, 59, 618, 624)).cut(ycyl(3, 57, 59, 165, 608))
    return [F('Body', EXTRUDE, [NEW_PART + ' and save it as usb_module.ipt.', 'Sketch a 50 x 50 square. Extrude 13 mm.'], f1),
            F('Ports', EXTRUDE, ['Sketch the USB-C, USB-A and 3.5 mm jack openings. Extrude Cut 2 mm. Save.'], f2)]


@part('literature_pocket', 'literature pocket', 'amenity', 'Fire retardant recycled PET felt, moulded', '3B4A5C', 300,
      'Pocket on the back of the seat for the safety card, magazines and A4 papers (it takes A4 landscape).',
      origin=(0, 45, 40), sustainable=True)
def _literature_pocket():
    f1 = box(-165, 165, 45, 70, 40, 255)
    f2 = f1.cut(box(-163, 163, 47, 68, 42, 256))
    return [F('Block', EXTRUDE, [NEW_PART + ' and save it as literature_pocket.ipt.', 'Sketch a 330 x 25 rectangle. Extrude 215 mm.'], f1),
            F('Shell', SHELL, ['Shell: remove the top face, thickness 2 mm. Save.'], f2,
              'Inside: 326 wide x 213 deep x 21, so A4 (297 x 210) fits on its side.')]


@part('vest_pouch', 'life vest pouch', 'amenity', 'Fire retardant recycled PET felt, moulded, with pull tab', '3B4A5C', 300,
      'Pouch under the seat for the life vest, hung from the two beam tubes. The front opens with a pull tab, so the '
      'vest can be reached sitting down.', origin=(-170, -5, 245))
def _vest_pouch():
    f1 = box(-170, 150, -5, 335, 245, BEAM_Z - BEAM_R)
    f2 = f1.cut(box(-168, 148, -3, 333, 247, BEAM_Z - BEAM_R - 2))
    f3 = f2.union(box(-30, 10, -15, -5, 250, 270))
    return [F('Block', EXTRUDE, [NEW_PART + ' and save it as vest_pouch.ipt.', 'Sketch a 320 x 340 rectangle. Extrude 60 mm.'], f1),
            F('Shell', SHELL, ['Shell, inside, thickness 2 mm (a closed box).'], f2,
              'Inside 316 x 336 x 56: room for the 305 x 305 vest.'),
            F('Pull tab', EXTRUDE, ['Sketch a 40 x 20 tab on the front face. Extrude 10 mm. Save.'], f3)]


@part('life_vest', 'life vest', 'amenity', 'Bought in: adult life vest in its pack, 305 x 305 x 50', ORANGE, 110,
      'The life vest the airline supplies, packed 305 x 305 (the size in the brief).', origin=(-162.5, 12, 247), bought=True)
def _life_vest():
    f1 = box(-162.5, 142.5, 12, 12 + VEST[1], 247, 247 + VEST[2])
    return [F('Pack', EXTRUDE, [NEW_PART + ' and save it as life_vest.ipt.', 'Sketch a 305 x 305 square. Extrude 50 mm. Save.'], f1,
              'Modelled to check it fits the pouch.')]


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
def back_tf(sx, recline=0.0):
    """Back coordinates to cabin coordinates for the seat at sx, with the back reclined by recline degrees."""
    return lambda w: w.rotate((0, 0, 0), (1, 0, 0), -(BACK_ANGLE + recline)).translate((sx, PIV[0], PIV[1]))


def back_point(p, sx, recline=0.0):
    a = math.radians(-(BACK_ANGLE + recline))
    x, y, z = p
    return (sx + x, PIV[0] + y * math.cos(a) - z * math.sin(a), PIV[1] + y * math.sin(a) + z * math.cos(a))


def _t(dx=0, dy=0, dz=0):
    return lambda w: w.translate((dx, dy, dz))


def _mx(x=0):
    """Mirror across the YZ plane, then move to x."""
    return lambda w: w.mirror('YZ').translate((x, 0, 0))


IDENT = lambda w: w


def arm_tf(x, up=0.0):
    return lambda w: w.rotate((0, ARM_PIV[0], ARM_PIV[1]), (1, ARM_PIV[0], ARM_PIV[1]), -up).translate((x, 0, 0))


def tray_tf(down=0.0):
    return lambda w: w.rotate((0, TRAY_HINGE[0], TRAY_HINGE[1]), (1, TRAY_HINGE[0], TRAY_HINGE[1]), -down)


def lock_tf(sx, recline=0.0, rod=False):
    a, r, L, ang = lock_line(recline)
    p = r if rod else a
    return lambda w: w.rotate((0, 0, 0), (1, 0, 0), ang).translate((sx + LOCK_X, p[0], p[1]))


def structure_instances():
    """The shared structure: (instance name, part key, transform)."""
    out = [('front beam tube', 'beam_tube', IDENT), ('rear beam tube', 'beam_tube', _t(dy=BEAM_Y[1]))]
    k = 0
    for side in (-1, 1):
        for y in BEAM_Y:
            k += 1
            out.append(('beam end cap %d' % k, 'beam_end_cap', (_t(dy=y) if side > 0 else (lambda w, y=y: w.mirror('YZ').translate((0, y, 0))))))
    for k, x in enumerate(SPREADERS, 1):
        out.append(('spreader %d' % k, 'spreader', _t(x)))
    for k, x in enumerate(LEGS, 1):
        out.append(('leg %d' % k, 'leg', _t(x)))
        sx = 1 if x > 0 else -1
        for j, y in enumerate(BEAM_Y):
            out.append(('beam clamp collar %d%s' % (k, 'ab'[j]), 'beam_collar', _t(x - sx * (LEG_T / 2 + 4), y)))
        for j, y in enumerate(FOOT_Y):
            out.append(('track fitting %d%s' % (k, 'ab'[j]), 'track_fitting', _t(x, y)))
            out.append(('track stud %d%s' % (k, 'ab'[j]), 'track_stud', _t(x, y)))
    out.append(('baggage bar', 'baggage_bar', IDENT))
    k = 0
    for x, kind in ((-250, 'back_pivot_pin'), (250, 'back_pivot_pin')):
        out.append(('recline pivot pin %d' % (2 if x < 0 else 3), kind, _t(x)))
    out.append(('recline pivot pin 1', 'end_pivot_pin', _mx(-750)))
    out.append(('recline pivot pin 4', 'end_pivot_pin', _t(750)))
    return out


def seat_instances(n, sx, recline=0.0, tray=0.0):
    """One seat: (instance name, part key, transform). n is the seat number, 1 to 3 from the left."""
    B = back_tf(sx, recline)
    T = tray_tf(tray)
    pre = 'seat %d ' % n
    out = [(pre + 'diaphragm', 'seat_diaphragm', _t(sx)), (pre + 'cushion foam', 'seat_foam', _t(sx)),
           (pre + 'cushion cover', 'seat_cover', _t(sx)),
           (pre + 'back shell', 'back_shell', B), (pre + 'back cushion foam', 'back_foam', B),
           (pre + 'back cushion cover', 'back_cover', B), (pre + 'head rest', 'headrest', B),
           (pre + 'recline lock bracket', 'recline_bracket', _t(sx)),
           (pre + 'recline lock', 'recline_lock', lock_tf(sx, recline)),
           (pre + 'recline lock rod', 'recline_rod', lock_tf(sx, recline, rod=True)),
           (pre + 'recline lock pin, front', 'lock_pin', _t(sx, ANCHOR[0], ANCHOR[1])),
           (pre + 'recline lock pin, rear', 'lock_pin', lambda w, B=B: B(w.translate((0, LEVER[0], LEVER[1])))),
           (pre + 'belt anchor, right', 'belt_anchor', _t(sx)), (pre + 'belt anchor, left', 'belt_anchor', _mx(sx)),
           (pre + 'belt webbing, buckle side', 'belt_strap_buckle', _t(sx)),
           (pre + 'belt webbing, adjuster side', 'belt_strap_adjust', _t(sx)),
           (pre + 'buckle body', 'buckle_body', _t(sx)), (pre + 'buckle lift lever', 'buckle_lever', _t(sx)),
           (pre + 'belt tongue', 'belt_tongue', _t(sx)),
           (pre + 'tray table', 'tray_table', lambda w, B=B, T=T: B(T(w))),
           (pre + 'tray hinge arm, right', 'tray_arm', B), (pre + 'tray hinge arm, left', 'tray_arm', lambda w, B=B: B(w.mirror('YZ'))),
           (pre + 'tray latch', 'tray_latch', B), (pre + 'entertainment screen', 'ife_screen', B),
           (pre + 'power and audio module', 'usb_module', B), (pre + 'literature pocket', 'literature_pocket', B),
           (pre + 'life vest pouch', 'vest_pouch', _t(sx)), (pre + 'life vest', 'life_vest', _t(sx))]
    return out


def armrest_instances(up=(0, 0, 0, 0)):
    out = []
    for k, x in enumerate(SPREADERS, 1):
        A = arm_tf(x, up[k - 1])
        out += [('armrest %d' % k, 'armrest', A), ('armrest pad %d' % k, 'armrest_pad', A), ('armrest pin %d' % k, 'armrest_pin', A)]
        if k > 1:
            out.append(('recline button %d' % (k - 1), 'recline_button', A))
    return out


def colour(key):
    return PART[key]['colour']


def set_instances(recline=(0, 0, 0), tray=(0, 0, 0), arms=(0, 0, 0, 0)):
    """Every part in the three-seat set: (instance name, part key, shape)."""
    out = [(n, k, tf(shape(k))) for n, k, tf in structure_instances()]
    for i, sx in enumerate(SEATS):
        out += [(n, k, tf(shape(k))) for n, k, tf in seat_instances(i + 1, sx, recline[i], tray[i])]
    out += [(n, k, tf(shape(k))) for n, k, tf in armrest_instances(arms)]
    return out


def seat_set(recline=(0, 0, 0), tray=(0, 0, 0), arms=(0, 0, 0, 0)):
    """Design A, the preferred design: an economy class three-seat set for flights under 3 hours. Two aluminium beam
    tubes on two machined legs with track fittings carry four spreaders. Each seat has a woven diaphragm, foam
    cushions in wipe clean covers, a carbon fibre back that reclines 5 degrees on a hydraulic lock, a fixed head
    rest and a lap belt with a lift lever buckle; lift up armrests; and, on each back, the tray table, screen, USB-C
    power and A4 pocket for the passenger behind. Life vests are stowed in pouches under the seats."""
    return [(n, s, colour(k)) for n, k, s in set_instances(recline, tray, arms)]


def group_of(name):
    """How an instance moves in the simulation: 'back', 'tray', 'rod', 'lock', 'arm' (with its number) or 'fixed'."""
    if name.startswith('seat '):
        base = name.split(' ', 2)[2]
        if base in ('back shell', 'back cushion foam', 'back cushion cover', 'head rest', 'tray hinge arm, right',
                    'tray hinge arm, left', 'tray latch', 'entertainment screen', 'power and audio module',
                    'literature pocket', 'recline lock pin, rear'):
            return 'back'
        if base == 'tray table':
            return 'tray'
        if base == 'recline lock rod':
            return 'rod'
        if base == 'recline lock':
            return 'lock'
        return 'fixed'
    if name.startswith('armrest') or name.startswith('recline button'):
        return 'arm'
    return 'fixed'


# ------------------------------------------------------------------ one seat on its own (the middle seat)
def seat_items():
    """The middle seat with the frame parts round it: the two spreaders, the pins, armrests and its share of the
    beams, for the single seat drawing."""
    items = [(n, k, tf(shape(k))) for n, k, tf in seat_instances(2, 0)]
    return items


def single_seat():
    """One seat (the middle seat) on its own: diaphragm, cushion and cover, carbon fibre back with its cushion,
    head rest, recline lock, lap belt, tray table, screen, power module, literature pocket and life vest pouch.
    Drawn in cabin coordinates on the middle seat line."""
    return [(n.replace('seat 2 ', ''), s, colour(k)) for n, k, s in seat_items()]


def masses():
    """Mass of every instance in the set (kg), by part key, and the total."""
    by = {}
    for n, k, s in set_instances():
        m = s.val().Volume() * 1e-9 * PART[k]['density']
        by.setdefault(k, [0, 0.0])
        by[k][0] += 1
        by[k][1] += m
    return by


def set_mass(with_vests=False):
    by = masses()
    return sum(m for k, (q, m) in by.items() if with_vests or k != 'life_vest')


# ------------------------------------------------------------------ Design B concept: fixed shell seats
def shell_seats():
    """Design B, a concept: three moulded fixed shell seats on one central box beam and two pedestal legs. The
    seat pan slides forward to recline inside the shell, so the back never moves into the space of the passenger
    behind. Comfortable and robust, but the shells and the slide make it about 9.5 kg a seat."""
    out = []
    shell = None
    for sx in SEATS:
        back = box(sx - 235, sx + 235, 380, 470, 380, 1150).edges('|Y').fillet(60)
        side = box(sx - 235, sx + 235, -40, 470, 360, 700).cut(box(sx - 215, sx + 215, -50, 450, 380, 701))
        s = back.union(side)
        shell = s if shell is None else shell.union(s)
    out.append(('fixed shells', shell, SHELL_C))
    pans = union(*[box(sx - 213, sx + 213, -60, 440, 380, 450) for sx in SEATS])
    out.append(('sliding seat pans and cushions', pans, SEAT_C))
    beam = box(-760, 760, 100, 260, 270, 360)
    out.append(('box beam', beam, FRAME_C))
    legs = union(*[box(x - 40, x + 40, 60, 300, 0, 270).union(box(x - 50, x + 50, -20, 520, 0, 25)) for x in (-380, 380)])
    out.append(('pedestal legs and track rails', legs, FRAME_C))
    tables = union(*[box(sx - 205, sx + 205, 470, 490, 700, 960) for sx in SEATS])
    out.append(('tray tables (stowed)', tables, TRAY_C))
    return out


# ------------------------------------------------------------------ parts list
def instance_keys(items):
    return {n: k for n, k, s in items}


def bom(names, items):
    """Parts list rows for the instances in names."""
    keys = instance_keys(items)
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
    return 'esp2026_p%02d_%s' % (p['no'], p['key'])


def _part_fn(p):
    def fn():
        return [(p['name'], part_shape(p['key']), p['colour'])]
    fn.__doc__ = p['desc']
    return fn


def _set_bom():
    items = set_instances()
    return bom([n for n, k, s in items], items)


def _seat_bom():
    items = [(n.replace('seat 2 ', ''), k, s) for n, k, s in seat_items()]
    return bom([n for n, k, s in items], items)


# ------------------------------------------------------------------ sub-assemblies
# How the set is built, the way it would be in Inventor: seven sub-assemblies (.iam), each made from its parts,
# then placed into the top level assembly. Each one is shown on the middle seat (or the second armrest) in cabin
# coordinates. 'explode' moves each part away from where it sits (mm) for the exploded views; 'steps' place the
# parts one at a time (names, title, command, actions, note).
FRAME_NAMES = ['leg 1', 'leg 2', 'track fitting 1a', 'track fitting 1b', 'track fitting 2a', 'track fitting 2b',
               'track stud 1a', 'track stud 1b', 'track stud 2a', 'track stud 2b', 'front beam tube', 'rear beam tube',
               'beam clamp collar 1a', 'beam clamp collar 1b', 'beam clamp collar 2a', 'beam clamp collar 2b',
               'spreader 1', 'spreader 2', 'spreader 3', 'spreader 4',
               'beam end cap 1', 'beam end cap 2', 'beam end cap 3', 'beam end cap 4', 'baggage bar']


def _frame_explode():
    ex = {}
    for n in FRAME_NAMES:
        if n.startswith('track fitting'):
            ex[n] = (0, 0, -90)
        elif n.startswith('track stud'):
            ex[n] = (0, 0, -200)
        elif 'beam tube' in n:
            ex[n] = (0, 0, 220)
        elif n.startswith('beam clamp'):
            ex[n] = (0, 0, 220)
        elif n.startswith('spreader'):
            ex[n] = (0, 0, 450)
        elif n.startswith('beam end cap'):
            ex[n] = (0, 0, 220)
        elif n == 'baggage bar':
            ex[n] = (0, -220, 0)
    return ex


SUBS = [
    dict(no=1, key='frame', title='frame', file='frame.iam', names=FRAME_NAMES, explode=_frame_explode(),
         desc='The structure shared by the three seats: two machined legs on four track fittings and studs, the front '
              'and rear beam tubes clamped by collars, four spreaders, end caps and the baggage bar.',
         steps=[
             (['leg 1', 'leg 2'], 'Place the legs', PLACE,
              [NEW_ASSY + ' and save it as frame.iam.', 'Place leg.ipt and Place Grounded. Place a second leg 540 mm '
               'along X (Mate the faces to the work plane with an offset of 270 each side of the centre).'], None),
             (['track fitting 1a', 'track fitting 1b', 'track fitting 2a', 'track fitting 2b',
               'track stud 1a', 'track stud 1b', 'track stud 2a', 'track stud 2b'], 'Track fittings and studs', CONSTRAIN,
              ['Place track_fitting.ipt under each foot: Mate the top of the fitting to the underside of the foot, then '
               'Flush the sides.', 'Place track_stud.ipt in each fitting: Insert the stud head into the stud hole.'],
              'The studs lock into the aircraft seat track; the feet are 508 mm (20 track pitches) apart.'),
             (['front beam tube', 'rear beam tube'], 'Beam tubes', CONSTRAIN,
              ['Place beam_tube.ipt twice. Insert each tube into its bores in the two legs (axis to axis), and Flush the '
               'tube centre plane with the assembly YZ plane so it sticks out 770 each side.'], None),
             (['beam clamp collar 1a', 'beam clamp collar 1b', 'beam clamp collar 2a', 'beam clamp collar 2b'],
              'Clamp collars', CONSTRAIN, ['Place beam_collar.ipt on each tube beside each leg boss: Insert the collar '
                                           'bore on the tube and Mate its face to the leg.'],
              'The collars stop the legs sliding along the tubes.'),
             (['spreader 1', 'spreader 2', 'spreader 3', 'spreader 4'], 'Spreaders', PATTERN,
              ['Place spreader.ipt and Insert its two bores on the tubes at X = -750.',
               'Pattern > Rectangular: 4 along X, 500 mm apart.'],
              'The spreaders sit under the armrests and carry the armrest and recline pivots.'),
             (['beam end cap 1', 'beam end cap 2', 'beam end cap 3', 'beam end cap 4', 'baggage bar'],
              'End caps and baggage bar', CONSTRAIN,
              ['Place beam_end_cap.ipt in each tube end (Insert).', 'Place baggage_bar.ipt through the holes in the front '
               'struts of the legs (Insert), centred.', 'Inspect tab > Analyze Interference: no overlaps. Save.'], None),
         ]),
    dict(no=2, key='seat_pan', title='seat pan', file='seat_pan.iam',
         names=['seat 2 diaphragm', 'seat 2 cushion foam', 'seat 2 cushion cover'],
         explode={'diaphragm': (0, 0, 0), 'cushion foam': (0, 0, 140), 'cushion cover': (0, 0, 280)},
         desc='One seat pan: the woven diaphragm that spans the beam tubes, the foam cushion and its wipe clean cover.',
         steps=[
             (['diaphragm'], 'Diaphragm', PLACE, [NEW_ASSY + ' and save it as seat_pan.iam.',
                                                  'Place seat_diaphragm.ipt and Place Grounded.'], None),
             (['cushion foam'], 'Cushion foam', CONSTRAIN, ['Place seat_foam.ipt. Mate its underside to the top of the '
                                                             'diaphragm and Flush the front edges and the centre planes.'],
              'The foam is 80 mm deep at the front and 50 at the back, so the seat slopes back 3.8 degrees.'),
             (['cushion cover'], 'Cover', CONSTRAIN, ['Place seat_cover.ipt over the foam: Mate the inside faces to the '
                                                      'foam. Save.'],
              'The cover is removable (hook and loop) so it can be cleaned or changed.'),
         ]),
    dict(no=3, key='seat_back', title='seat back', file='seat_back.iam',
         names=['seat 2 back shell', 'seat 2 back cushion foam', 'seat 2 back cushion cover', 'seat 2 head rest',
                'seat 2 literature pocket', 'seat 2 tray hinge arm, right', 'seat 2 tray hinge arm, left',
                'seat 2 tray table', 'seat 2 tray latch', 'seat 2 entertainment screen', 'seat 2 power and audio module'],
         explode={'back shell': (0, 0, 0), 'back cushion foam': (0, -220, 0), 'back cushion cover': (0, -380, 0),
                  'head rest': (0, -120, 220), 'literature pocket': (0, 160, -60), 'tray hinge arm, right': (90, 230, 0),
                  'tray hinge arm, left': (-90, 230, 0), 'tray table': (0, 330, 0), 'tray latch': (0, 300, 120),
                  'entertainment screen': (0, 240, 160), 'power and audio module': (0, 240, 220)},
         desc='One seat back: the carbon fibre shell with its cushion, cover and fixed head rest, and on the back the '
              'A4 pocket, tray table with its hinge arms and latch, screen and power module for the passenger behind.',
         steps=[
             (['back shell'], 'Back shell', PLACE, [NEW_ASSY + ' and save it as seat_back.iam.',
                                                    'Place back_shell.ipt and Place Grounded.'], None),
             (['back cushion foam', 'back cushion cover'], 'Back cushion', CONSTRAIN,
              ['Place back_foam.ipt in the open front of the shell (Mate its back face to the shell rim, Flush the centre '
               'planes).', 'Place back_cover.ipt over the foam (Mate inside faces to the foam).'], None),
             (['head rest'], 'Fixed head rest', CONSTRAIN, ['Place headrest.ipt on top of the shell: Mate its underside to '
                                                             'the top of the shell and Flush the centre planes.'],
              'Fixed, as the brief asks: there is no adjuster.'),
             (['literature pocket'], 'Literature pocket', CONSTRAIN,
              ['Place literature_pocket.ipt on the lower back of the shell (Mate, then Flush the centre planes).'],
              'Holds A4 safety cards and magazines.'),
             (['tray hinge arm, right', 'tray hinge arm, left', 'tray table', 'tray latch'], 'Tray table', CONSTRAIN,
              ['Place tray_arm.ipt on each side of the shell (Mate), Mirror Components for the second one.',
               'Place tray_table.ipt: Insert the hinge stubs into the tray holes. Add an Angle constraint 0 degrees '
               '(stowed); the tray turns 78 degrees to sit level.', 'Place tray_latch.ipt above the tray.'], None),
             (['entertainment screen', 'power and audio module'], 'Screen and power', CONSTRAIN,
              ['Place ife_screen.ipt in the recess at the top of the back and usb_module.ipt beside it (Mate, Flush). Save.'],
              None),
         ]),
    dict(no=4, key='recline_lock', title='recline lock', file='recline_lock.iam',
         names=['seat 2 recline lock bracket', 'seat 2 recline lock', 'seat 2 recline lock rod',
                'seat 2 recline lock pin, front', 'seat 2 recline lock pin, rear'],
         explode={'recline lock bracket': (0, -80, 30), 'recline lock pin, front': (45, -40, 0), 'recline lock': (0, 0, 0),
                  'recline lock rod': (0, 90, 0), 'recline lock pin, rear': (45, 180, 0)},
         desc='One recline lock: the bracket clamped under the front beam, the hydraulic locking cylinder and its rod, '
              'and the two pins. Pressing the button on the armrest opens the lock so the back can recline 5 degrees.',
         steps=[
             (['recline lock'], 'Locking cylinder', PLACE, [NEW_ASSY + ' and save it as recline_lock.iam.',
                                                            'Place recline_lock.ipt and Place Grounded.'], None),
             (['recline lock rod'], 'Rod', CONSTRAIN, ['Place recline_rod.ipt and Insert it in the bore of the cylinder '
                                                       '(axis to axis).'], 'Bought in as one unit with the cylinder.'),
             (['recline lock bracket', 'recline lock pin, front'], 'Bracket and front pin', CONSTRAIN,
              ['Place recline_bracket.ipt and line up its pin hole with the front eye (Insert).',
               'Place lock_pin.ipt through the bracket and the eye (Insert).'], None),
             (['recline lock pin, rear'], 'Rear pin', CONSTRAIN,
              ['Place lock_pin.ipt in the rod eye (Insert). In the set it also passes through the lever on the back shell. '
               'Save.'], None),
         ]),
    dict(no=5, key='armrest', title='armrest', file='armrest.iam',
         names=['armrest 2', 'armrest pad 2', 'armrest pin 2', 'recline button 1'],
         explode={'armrest 2': (0, 0, 0), 'armrest pad 2': (0, 0, 70), 'armrest pin 2': (110, 0, 0),
                  'recline button 1': (0, -40, 90)},
         desc='One armrest: the glass filled nylon arm, its soft pad, the pivot pin it lifts on and the recline button '
              'in its front end (on three of the four armrests).',
         steps=[
             (['armrest 2'], 'Armrest', PLACE, [NEW_ASSY + ' and save it as armrest.iam.',
                                                'Place armrest.ipt and Place Grounded.'], None),
             (['armrest pad 2'], 'Pad', CONSTRAIN, ['Place armrest_pad.ipt on top (Mate, Flush the centre planes).'], None),
             (['recline button 1'], 'Recline button', CONSTRAIN,
              ['Place recline_button.ipt in the hole on top of the front end (Insert).'],
              'Large and light to press, so every passenger can use it.'),
             (['armrest pin 2'], 'Pivot pin', CONSTRAIN,
              ['Place armrest_pin.ipt in the pivot hole (Insert). In the set it passes through the spreader too. Save.'],
              'The armrest lifts 90 degrees on this pin.'),
         ]),
    dict(no=6, key='lap_belt', title='lap belt', file='lap_belt.iam',
         names=['seat 2 belt anchor, right', 'seat 2 belt anchor, left', 'seat 2 belt webbing, buckle side',
                'seat 2 belt webbing, adjuster side', 'seat 2 buckle body', 'seat 2 buckle lift lever', 'seat 2 belt tongue'],
         explode={'belt anchor, right': (90, 0, -60), 'belt anchor, left': (-90, 0, -60),
                  'belt webbing, buckle side': (0, 0, 0), 'belt webbing, adjuster side': (0, 0, 0),
                  'buckle body': (0, 0, 60), 'buckle lift lever': (0, 0, 120), 'belt tongue': (0, -70, 60)},
         desc='One lap belt: an anchor each side, the two webbing halves, the buckle body with its lift lever and the '
              'tongue with the slide bar adjuster. Length 1170 to 1420 mm.',
         steps=[
             (['belt anchor, right', 'belt anchor, left'], 'Anchors', PLACE,
              [NEW_ASSY + ' and save it as lap_belt.iam.', 'Place belt_anchor.ipt twice, 450 mm apart (Mirror Components '
                                                             'for the left one).'], None),
             (['belt webbing, buckle side', 'belt webbing, adjuster side'], 'Webbing', CONSTRAIN,
              ['Place belt_strap_buckle.ipt on the right anchor and belt_strap_adjust.ipt on the left anchor (Mate the '
               'loop to the anchor).'], None),
             (['buckle body', 'buckle lift lever'], 'Buckle', CONSTRAIN,
              ['Place buckle_body.ipt on the end of the buckle side webbing and buckle_lever.ipt on top of it (Mate, '
               'Flush).'], 'Lift the lever and the tongue comes free.'),
             (['belt tongue'], 'Tongue', CONSTRAIN,
              ['Place belt_tongue.ipt on the adjuster side webbing and Insert it in the buckle slot. Save.'],
              'The slide bar sets the length.'),
         ]),
    dict(no=7, key='life_vest', title='life vest pouch', file='life_vest_pouch.iam',
         names=['seat 2 life vest pouch', 'seat 2 life vest'],
         explode={'life vest pouch': (0, 0, 0), 'life vest': (0, -380, 0)},
         desc='The pouch under each seat and the life vest pack (305 x 305 x 50) that slides into it.',
         steps=[
             (['life vest pouch'], 'Pouch', PLACE, [NEW_ASSY + ' and save it as life_vest_pouch.iam.',
                                                    'Place vest_pouch.ipt and Place Grounded.'], None),
             (['life vest'], 'Life vest', CONSTRAIN, ['Place life_vest.ipt inside the pouch: Mate it to the pouch floor '
                                                      'and Flush the centre planes. Save.'],
              'The pull tab lets the passenger pull the pouch open.'),
         ]),
]
SUB = {d['key']: d for d in SUBS}


def sub_model_name(d):
    return 'esp2026_sa%d_%s' % (d['no'], d['key'])


def sub_items(key):
    """The instances of one sub-assembly: (display name, part key, shape), names without the 'seat 2 ' prefix."""
    d = SUB[key]
    by = {n: (k, s) for n, k, s in set_instances()}
    return [(n.replace('seat 2 ', ''), by[n][0], by[n][1]) for n in d['names']]


def sub_of(name):
    """Which sub-assembly an instance of the set belongs to (the back pivot pins go in at the top level)."""
    for d in SUBS:
        for n in d['names']:
            base = n.replace('seat 2 ', '')
            if name == n or (name.startswith('seat ') and name.split(' ', 2)[2] == base) or \
               (d['key'] == 'armrest' and name.split(' ')[0] in ('armrest', 'recline') and
                name.rsplit(' ', 1)[0] in ('armrest', 'armrest pad', 'armrest pin', 'recline button')):
                return d['key']
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
    dict(name='esp2026_seat_set', title='ESP 2026 three-seat set (GA)', fn=seat_set, criteria='3.1, 3.2',
         uses='ESP 2026 Task 2, Part B: the preferred design, an economy class three-seat set assembled from %d '
              'separate parts. General arrangement, parts list, simulation of the recline, armrests and tray.' % len(PARTS),
         section=None, explode=None, iso=(-1, -1.4, 0.8), folder='ESP 2026', sim=True, fea=False, bom=_set_bom),
    dict(name='esp2026_single_seat', title='ESP 2026 single seat', fn=single_seat, criteria='3.1, 3.2',
         uses='ESP 2026 Task 2: one seat (the middle seat) and everything fitted to it. Section A-A down the middle of '
              'the seat shows the cushion, back, recline lock and life vest pouch.',
         section='y', explode=None, iso=(-1, -1.2, 0.7), folder='ESP 2026', bom=_seat_bom, fea=False),
    dict(name='esp2026_shell_seats', title='ESP 2026 concept B: fixed shell seats', fn=shell_seats, criteria='3.1',
         uses='ESP 2026 Task 2, Part A: the second design idea, fixed shell seats with a sliding seat pan, for '
              'comparison with design A.', section=None, explode=None, iso=(-1, -1.4, 0.8), folder='ESP 2026', fea=False),
]

for _d in SUBS:
    MODELS.append(dict(
        name=sub_model_name(_d), title='ESP 2026 sub-assembly %d: %s' % (_d['no'], _d['title']), fn=_sub_fn(_d),
        criteria='3.1, 3.2', uses='ESP 2026 sub-assembly %s: %s' % (_d['file'], _d['desc']), description=_d['desc'],
        section=None, explode=_d['explode'], folder='ESP 2026', bom=_sub_bom(_d), fea=False,
        iso=(-1, -1.3, 0.9), sub=dict(no=_d['no'], key=_d['key'], file=_d['file'])))

for _p in PARTS:
    MODELS.append(dict(
        name=part_model_name(_p), title='ESP 2026 part %02d: %s' % (_p['no'], _p['name']), fn=_part_fn(_p),
        criteria='3.1', uses='ESP 2026 component, item %d on the parts list: %s. %s' % (_p['no'], _p['material'], _p['desc']),
        description=_p['desc'], section=None, explode=None, folder='ESP 2026', part=dict(no=_p['no'], key=_p['key'],
        group=_p['group'], material=_p['material'], file=_p['file'], bought=_p['bought']),
        fea=None if _p['key'] == 'leg' else False, media='still'))


# ------------------------------------------------------------------ key sizes for each part drawing
SIZES = dict(
    beam_tube=['Tube Ø50 x 1.5 wall', 'Length 1540 (to ±770)', 'Two per set, 330 apart'],
    beam_end_cap=['Cap Ø50 x 6', 'Spigot Ø47 x 12'],
    spreader=['Plate 8 thick', 'Beam bores Ø50 at 330 centres, bosses Ø70', 'Armrest pivot Ø12, 360 aft and 260 up',
              'Recline pivot Ø12, 420 aft and 60 up', 'Slots 24 x 130 and 210 x 16'],
    leg=['Plate 10 thick', 'Struts 40 wide, chord and brace 30 wide', 'Feet 508 apart, pads 60 x 20',
         'Beam bores Ø50 at 330 centres, 330 up', 'Baggage bar hole Ø20, 150 up'],
    beam_collar=['Ring Ø64 / Ø50 x 8', 'Lug 12 x 13, 2 mm split'],
    track_fitting=['Block 24 x 60 x 25', 'Stud hole Ø12', 'End steps 9 x 8'],
    track_stud=['Stud Ø12 x 45', 'Foot Ø20 x 8'],
    baggage_bar=['Tube Ø20 x 1.2', 'Length 1400'],
    seat_diaphragm=['Sheet 446 x 380 x 1.5'],
    seat_foam=['446 wide x 446 deep', '80 high at the front, 50 at the back'],
    seat_cover=['450 wide x 450 deep, 2 thick', 'Top 440 above the floor at the front edge'],
    back_shell=['Shell 440 x 45 x 680, 1.2 wall, open front', 'Pivot lugs 6 x 40, hole Ø12',
                'Recline lever 8 x 20, pin hole Ø8 at 100 below the pivot'],
    back_foam=['420 x 30 x 686', 'Front edges R10'],
    back_cover=['424 x 32 x 690, 2 thick', 'Front edges R11'],
    headrest=['400 x 90 x 80', 'Corners R25, front edges R12'],
    back_pivot_pin=['Pin Ø12 x 72', 'Head Ø18 x 3'],
    end_pivot_pin=['Pin Ø12 x 40', 'Head Ø18 x 4'],
    recline_bracket=['Half ring Ø62 / Ø50 x 8', 'Pin hole Ø8, 60 aft and 40 down from the beam axis'],
    recline_lock=['Cylinder Ø22 x 198', 'Bore Ø10', 'Eye Ø16 x 8, hole Ø8'],
    recline_rod=['Rod Ø8 x 194', 'Eye Ø16 x 8, hole Ø8'],
    lock_pin=['Pin Ø8 x 16', 'Head Ø14 x 3'],
    recline_button=['Bezel Ø24 x 3', 'Button Ø16 x 4'],
    armrest=['Bar 50 x 420 x 40, 2.5 mm walls', 'Pivot end 60 long, slot 10 wide', 'Pivot hole Ø12'],
    armrest_pad=['Pad 50 x 330 x 8', 'Top edges R4'],
    armrest_pin=['Pin Ø12 x 50', 'Head Ø18 x 3'],
    belt_anchor=['Block 19 x 30 x 40', 'Bolt hole Ø10'],
    belt_strap_buckle=['Webbing 48 x 2', 'Length in use 380'],
    belt_strap_adjust=['Webbing 48 x 2', 'Length in use 790 to 1040'],
    buckle_body=['Body 70 x 50 x 10', 'Tongue slot 24 x 4 x 21'],
    buckle_lever=['Lever 60 x 42 x 4', 'Finger lip 10 x 42 x 3'],
    belt_tongue=['Plate 55 x 24 x 4', 'Slide bar 18 x 36 x 7'],
    tray_table=['Panel 415 x 265 x 12', 'Corners R15', 'Hinge holes Ø8 x 4, 8 up', 'Cup recess Ø80 x 1.5'],
    tray_arm=['Bracket 6 x 25 x 30', 'Hinge stub Ø8 x 5'],
    tray_latch=['Base Ø16 x 5', 'Tab 24 x 10 x 10'],
    ife_screen=['Housing 250 x 160 x 17', 'Display 220 x 137'],
    usb_module=['Body 50 x 50 x 13', 'USB-C, USB-A, 3.5 mm jack'],
    literature_pocket=['Outside 330 x 215 x 25, 2 wall', 'Inside 326 x 213 x 21 (A4 on its side)'],
    vest_pouch=['Outside 320 x 340 x 60, 2 wall', 'Inside 316 x 336 x 56', 'Pull tab 40 x 20 x 10'],
    life_vest=['Pack 305 x 305 x 50'],
)
for _p in PARTS:
    _p['sizes'] = SIZES[_p['key']]
for _m in MODELS:
    if _m.get('part'):
        _m['part']['sizes'] = PART[_m['part']['key']]['sizes']
