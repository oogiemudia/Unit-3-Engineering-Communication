"""Build steps for every model, written as the Autodesk Inventor commands a learner would use.

Each model has a function that returns a list of steps. A step is a dict with:
  title    short name of the step
  command  the Inventor command used, with where it sits on the ribbon
  actions  what to click and type, in order
  parts    the model as it stands after this step: a list of (part name, CadQuery shape, colour)
  overlay  optional shape drawn in the highlight colour: a sketch profile, sketch points or a cosmetic thread
  note     optional tip

The geometry of every stage is made with the same CadQuery operations as models/parts.py, and
tools/build_steps.py checks that the last step matches the finished model.

Plane names follow Inventor's default orientation (Y up): the XY Plane is the front, the XZ Plane is the
top (the ground) and the YZ Plane is the right side.
"""
import math
import cadquery as cq
from parts import (STEEL, ALU, BRASS, BLUE, GREEN, ORANGE, DARK, bolt, nut, washer)

NEW_PART = 'File > New > Standard (mm).ipt'
SKETCH = '3D Model tab > Sketch panel > Start 2D Sketch'
EXTRUDE = '3D Model tab > Create panel > Extrude'
REVOLVE = '3D Model tab > Create panel > Revolve'
COIL = '3D Model tab > Create panel > Coil'
HOLE = '3D Model tab > Modify panel > Hole'
FILLET = '3D Model tab > Modify panel > Fillet'
CHAMFER = '3D Model tab > Modify panel > Chamfer'
THREAD = '3D Model tab > Modify panel > Thread'
CIRC_PATTERN = '3D Model tab > Pattern panel > Circular Pattern'
WORK_PLANE = '3D Model tab > Work Features panel > Plane'
NEW_ASSY = 'File > New > Standard (mm).iam'
PLACE = 'Assemble tab > Component panel > Place'
CONTENT = 'Assemble tab > Component panel > Place from Content Center'
CONSTRAIN = 'Assemble tab > Relationships panel > Constrain'


def step(title, command, actions, parts, overlay=None, note=None):
    return dict(title=title, command=command, actions=actions, parts=parts, overlay=overlay, note=note)


def face(wp):
    """A closed sketch (one outer wire and any inner wires) as a flat face, for showing the profile."""
    wires = wp.wires().vals() if hasattr(wp, 'wires') else wp
    wires = sorted(wires, key=lambda w: -cq.Face.makeFromWires(w).Area())
    return cq.Workplane('XY').add(cq.Face.makeFromWires(wires[0], wires[1:]))


def points(pts, z, r=1.2):
    """Sketch points shown as small discs on a face at height z."""
    return cq.Workplane('XY').workplane(offset=z + 0.05).pushPoints(pts).circle(r).extrude(0.1)


def finish(dims):
    return 'Add the dimensions with Dimension (Sketch tab > Constrain panel): ' + dims + '. Click Finish Sketch.'


# ------------------------------------------------------------------ 1 step block
def step_block():
    prof = cq.Workplane('XZ').polyline([(0, 0), (60, 0), (60, 40), (30, 40), (30, 20), (0, 20)]).close()
    body = prof.extrude(-40)
    done = body.cut(cq.Workplane('XY').center(15, 20).circle(5).extrude(20))
    return [
        step('Sketch the step profile', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch and click the XY Plane (the front).',
              'Sketch tab > Create panel > Line: draw the six sided step outline from the origin.',
              finish('60 long, 40 high overall, the step 30 long and 20 high')],
             [], overlay=face(prof)),
        step('Extrude the block', EXTRUDE,
             ['Click Extrude. The profile is picked for you.', 'Distance A: 40 mm, direction into the screen.',
              'Output: Solid. Click OK.'],
             [('step block', body, BLUE)]),
        step('Drill the 10 mm hole', HOLE,
             ['Click Hole and click the top face of the lower step.',
              'Position the centre 15 from the left end and 20 from the front edge (half the depth).',
              'Type: Simple Hole. Diameter 10 mm. Termination: Through All. Click OK.'],
             [('step block', done, BLUE)]),
    ]


# ------------------------------------------------------------------ 2 sloping block
def sloping_block():
    w, d, h = 70, 40, 50
    prof = cq.Workplane('XZ').polyline([(0, 0), (w, 0), (w, 20), (w - 30, h), (0, h)]).close()
    body = prof.extrude(-d)
    p1, p2 = cq.Vector(w, 0, 20), cq.Vector(w - 30, 0, h)
    mid = (p1 + p2) * 0.5 + cq.Vector(0, d / 2, 0)
    n = cq.Vector(30, 0, 30).normalized()
    drill = cq.Solid.makeCylinder(6, 60, cq.Vector(mid - n * 30), n)
    done = body.cut(cq.Workplane('XY').add(drill))
    return [
        step('Sketch the side profile', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XY Plane (the front).',
              'Line: draw the five sided outline starting at the origin.',
              finish('70 long, 50 high, 20 high at the right hand end, the slope 30 across and 30 up (45 degrees)')],
             [], overlay=face(prof)),
        step('Extrude the block', EXTRUDE,
             ['Click Extrude. Distance A: 40 mm, into the screen. Click OK.'],
             [('sloping block', body, ORANGE)]),
        step('Drill a hole square to the slope', HOLE,
             ['Click Hole and click the sloping face. Inventor drills square to the face you pick.',
              'Position the centre in the middle of the face: half way along the slope and 20 from the front edge.',
              'Type: Simple Hole. Diameter 12 mm. Termination: Distance, 30 mm. Drill Point: Flat. Click OK.'],
             [('sloping block', done, ORANGE)],
             note='Look at the front view: the hole is not seen as a circle until you add an auxiliary view square to the slope.'),
    ]


# ------------------------------------------------------------------ 3 flanged bush
def flanged_bush():
    flange = cq.Workplane('XY').circle(35).extrude(10)
    body = cq.Workplane('XY').workplane(offset=10).circle(20).extrude(40)
    a = flange.union(body)
    b = a.faces('>Z').workplane().hole(24)
    c1 = b.faces('<Z').workplane().polarArray(27.5, 45, 360, 1).hole(8)
    c = b.faces('<Z').workplane().polarArray(27.5, 45, 360, 4).hole(8)
    d = c.faces('>Z').edges('not %LINE').edges(cq.selectors.RadiusNthSelector(0)).chamfer(1)
    return [
        step('Sketch the flange circle', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XZ Plane (the top).',
              'Sketch tab > Create panel > Circle (Center Point): click the origin and drag out a circle.',
              finish('diameter 70')],
             [], overlay=face(cq.Workplane('XY').circle(35))),
        step('Extrude the flange', EXTRUDE, ['Click Extrude. Distance A: 10 mm, upwards. Click OK.'],
             [('flanged bush', flange, BRASS)]),
        step('Sketch the body circle', SKETCH,
             ['Start 2D Sketch and click the top face of the flange.',
              'Circle (Center Point) on the projected centre point.', finish('diameter 40')],
             [('flanged bush', flange, BRASS)], overlay=face(cq.Workplane('XY').workplane(offset=10).circle(20))),
        step('Extrude the body', EXTRUDE,
             ['Click Extrude. Distance A: 40 mm, upwards. Boolean: Join. Click OK.'],
             [('flanged bush', a, BRASS)]),
        step('Bore the 24 mm hole', HOLE,
             ['Click Hole and click the top face of the body.', 'Click the circular edge to make the hole concentric.',
              'Simple Hole. Diameter 24 mm. Termination: Through All. Click OK.'],
             [('flanged bush', b, BRASS)]),
        step('Drill one bolt hole', HOLE,
             ['Click Hole and click the top face of the flange.',
              'Place the centre on a 55 mm pitch circle (27.5 from the centre) at 45 degrees.',
              'Simple Hole. Diameter 8 mm. Termination: Through All. Click OK.'],
             [('flanged bush', c1, BRASS)]),
        step('Pattern the bolt holes', CIRC_PATTERN,
             ['Click Circular Pattern. Features: pick the 8 mm hole in the browser.',
              'Rotation Axis: pick the outside face of the body (its axis is used).',
              'Placement: 4 occurrences over 360 degrees. Click OK.'],
             [('flanged bush', c, BRASS)]),
        step('Chamfer the bore', CHAMFER,
             ['Click Chamfer. Method: Distance. Distance 1 mm.',
              'Pick the top edge of the 24 mm bore. Click OK.'],
             [('flanged bush', d, BRASS)]),
    ]


# ------------------------------------------------------------------ 4 bolted joint
def _plate_stages():
    rect = cq.Workplane('XY').rect(80, 40)
    a = cq.Workplane('XY').box(80, 40, 10, centered=(True, True, False))
    b = a.faces('>Z').workplane().hole(9)
    c = b.edges('|Z').fillet(4)
    return rect, a, b, c


def bolted_joint():
    rect, a, b, plate = _plate_stages()
    p2 = plate.translate((0, 0, 10))
    w = washer().translate((0, 0, 20))
    bt = bolt(8, 40, 13, 5.3).translate((0, 0, 20 + 1.6))
    n = nut().translate((0, 0, -6.5))
    lower, upper = ('lower plate', plate, ALU), ('upper plate', p2, BLUE)
    return [
        step('Plate part: sketch the rectangle', SKETCH,
             [NEW_PART + ' and save it as plate.ipt.', 'Start 2D Sketch on the XZ Plane (the top).',
              'Sketch tab > Create panel > Rectangle (Two Point Center): click the origin and drag.',
              finish('80 by 40')],
             [], overlay=face(rect)),
        step('Plate part: extrude', EXTRUDE, ['Click Extrude. Distance A: 10 mm, upwards. Click OK.'],
             [('plate', a, ALU)]),
        step('Plate part: clearance hole', HOLE,
             ['Click Hole and click the top face. Place the centre on the centre of the plate.',
              'Simple Hole. Diameter 9 mm (clearance for M8). Termination: Through All. Click OK.'],
             [('plate', b, ALU)]),
        step('Plate part: round the corners', FILLET,
             ['Click Fillet. Radius 4 mm.', 'Pick the four vertical corner edges. Click OK. Save plate.ipt.'],
             [('plate', plate, ALU)]),
        step('Assembly: place the lower plate', PLACE,
             [NEW_ASSY + ' and save it as bolted_joint.iam.', 'Click Place and choose plate.ipt.',
              'Right click and pick Place Grounded at Origin, then press Esc.'],
             [lower]),
        step('Assembly: place the upper plate', CONSTRAIN,
             ['Click Place, choose plate.ipt again and click once in the window to add a second copy.',
              'Click Constrain. Type: Insert. Pick the top edge of the hole in the lower plate, then the bottom edge of the hole in the upper plate. Click OK.',
              'Add a Mate constraint between a side face of each plate so they line up.'],
             [lower, upper]),
        step('Assembly: add the washer', CONTENT,
             ['Click Place from Content Center. Fasteners > Washers > Plain. Pick an M8 plain washer (8.4 x 17 x 1.6).',
              'Constrain > Insert: the washer bore onto the top edge of the hole in the upper plate.'],
             [lower, upper, ('washer', w, STEEL)]),
        step('Assembly: add the bolt', CONTENT,
             ['Place from Content Center. Fasteners > Bolts > Hex Head. Pick an M8 x 40 hex head bolt.',
              'Constrain > Insert: the underside of the bolt head onto the top of the washer.'],
             [lower, upper, ('washer', w, STEEL), ('hex bolt M8 x 40', bt, DARK)]),
        step('Assembly: add the nut', CONTENT,
             ['Place from Content Center. Fasteners > Nuts > Hex. Pick an M8 hex nut.',
              'Constrain > Insert: the nut onto the bottom edge of the hole in the lower plate.',
              'Save bolted_joint.iam.'],
             [lower, upper, ('washer', w, STEEL), ('hex bolt M8 x 40', bt, DARK), ('hex nut M8', n, STEEL)],
             note='Content Center parts come with their threads and exact standard sizes. The hub models them simplified.'),
    ]


# ------------------------------------------------------------------ 5 threaded shaft
def threaded_shaft():
    prof = cq.Workplane('XZ').polyline([(0, 0), (0, 15), (60, 15), (60, 10), (100, 10), (100, 8), (128, 8),
                                        (128, 0)]).close()
    s = cq.Workplane('YZ').circle(15).extrude(60)
    s = s.union(cq.Workplane('YZ').workplane(offset=60).circle(10).extrude(40))
    s = s.union(cq.Workplane('YZ').workplane(offset=100).circle(8).extrude(28))
    a = s
    b = a.cut(cq.Workplane('YZ').workplane(offset=100).circle(10).circle(6.5).extrude(3))
    c = b.faces('>X').chamfer(1).faces('<X').chamfer(1)
    key = cq.Workplane('XY').workplane(offset=15 - 3.5).center(30, 0).slot2D(30, 6).extrude(10)
    d = c.cut(key)
    thread = cq.Workplane('XY').add(cq.Solid.makeCylinder(8.2, 24, cq.Vector(103, 0, 0), cq.Vector(1, 0, 0)))
    T = 'threaded shaft'
    return [
        step('Sketch half the shaft profile', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XY Plane (the front).',
              'Line: draw half of the stepped outline above a horizontal centre line through the origin.',
              'Format panel > Centerline: change the bottom line to a centre line, so Inventor dimensions diameters.',
              finish('diameters 30, 20 and 16; lengths 60, 40 and 28')],
             [], overlay=face(prof)),
        step('Revolve the shaft', REVOLVE,
             ['Click Revolve. Profile: the sketch. Axis: the centre line.', 'Extents: Full (360 degrees). Click OK.'],
             [(T, a, STEEL)]),
        step('Cut the thread undercut', REVOLVE,
             ['Start 2D Sketch on the XY Plane. Draw a rectangle 3 wide at the start of the 16 mm diameter, from 13 mm diameter up past the outside.',
              'Finish Sketch, then Revolve. Axis: the shaft centre line. Boolean: Cut. Click OK.'],
             [(T, b, STEEL)]),
        step('Chamfer both ends', CHAMFER,
             ['Click Chamfer. Distance 1 mm.', 'Pick the outside edge at each end of the shaft. Click OK.'],
             [(T, c, STEEL)]),
        step('Cut the keyway', EXTRUDE,
             [WORK_PLANE + ': Tangent to Surface and Parallel to Plane. Pick the 30 mm diameter and the XZ Plane.',
              'Start 2D Sketch on that work plane.',
              'Sketch tab > Create panel > Slot (Center to Center): centres 24 apart (30 long overall), 6 wide, centred 30 from the left end.',
              'Finish Sketch. Extrude, Boolean: Cut, Distance 3.5 mm, into the shaft. Click OK.'],
             [(T, d, STEEL)]),
        step('Add the M16 thread', THREAD,
             ['Click Thread and pick the 16 mm diameter face.',
              'Specification: ISO Metric profile, size 16, designation M16x2. Untick Full Length and set 24 mm from the undercut.',
              'Leave Display in Model ticked. Click OK.'],
             [(T, d, STEEL)], overlay=thread,
             note='Inventor threads are cosmetic: the solid stays at the 16 mm major diameter and the drawing shows the thread by convention.'),
    ]


# ------------------------------------------------------------------ 6 PCD flange
def pcd_flange():
    f = cq.Workplane('XY').circle(60).extrude(15)
    a = f.union(cq.Workplane('XY').workplane(offset=15).circle(25).extrude(20))
    b = a.faces('>Z').workplane().hole(30)
    c1 = b.faces('<Z').workplane().polarArray(45, 0, 360, 1).hole(10)
    c = b.faces('<Z').workplane().polarArray(45, 0, 360, 6).hole(10)
    d = c.faces('>Z').edges('not %LINE').edges(cq.selectors.RadiusNthSelector(0)).chamfer(1.5)
    P = 'PCD flange'
    return [
        step('Sketch the flange circle', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XZ Plane (the top).',
              'Circle (Center Point) on the origin.', finish('diameter 120')],
             [], overlay=face(cq.Workplane('XY').circle(60))),
        step('Extrude the flange', EXTRUDE, ['Click Extrude. Distance A: 15 mm, upwards. Click OK.'],
             [(P, f, ALU)]),
        step('Sketch and extrude the hub', EXTRUDE,
             ['Start 2D Sketch on the top face of the flange. Circle on the centre, diameter 50. Finish Sketch.',
              'Extrude. Distance A: 20 mm, upwards. Boolean: Join. Click OK.'],
             [(P, a, ALU)]),
        step('Bore the 30 mm hole', HOLE,
             ['Click Hole, click the top face of the hub, then click its circular edge to make the hole concentric.',
              'Simple Hole. Diameter 30 mm. Termination: Through All. Click OK.'],
             [(P, b, ALU)]),
        step('Drill one hole on the PCD', HOLE,
             ['Start 2D Sketch on the top face of the flange. Draw a construction circle of diameter 90 (the PCD).',
              'Sketch tab > Create panel > Point: put a point on the PCD, in line with the X axis. Finish Sketch.',
              'Hole: pick the point. Simple Hole. Diameter 10 mm. Through All. Click OK.'],
             [(P, c1, ALU)]),
        step('Pattern six holes', CIRC_PATTERN,
             ['Click Circular Pattern. Features: the 10 mm hole. Rotation Axis: the bore.',
              'Placement: 6 occurrences over 360 degrees, so they are 60 degrees apart. Click OK.'],
             [(P, c, ALU)]),
        step('Chamfer the bore', CHAMFER,
             ['Click Chamfer. Distance 1.5 mm. Pick the top edge of the bore. Click OK.'],
             [(P, d, ALU)]),
    ]


# ------------------------------------------------------------------ 7 annotation plate
def annotation_plate():
    a = cq.Workplane('XY').box(100, 60, 10, centered=(True, True, False))
    b = a.faces('>Z').workplane().rect(76, 36, forConstruction=True).vertices().cskHole(6.6, 13, 90)
    c = b.faces('>Z').workplane().hole(40)
    d = c.faces('>Z').edges(cq.selectors.RadiusNthSelector(1)).chamfer(1)
    pts = [(x, y) for x in (-38, 38) for y in (-18, 18)]
    P = 'annotation plate'
    return [
        step('Sketch the plate', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XZ Plane (the top).',
              'Rectangle (Two Point Center) on the origin.', finish('100 by 60')],
             [], overlay=face(cq.Workplane('XY').rect(100, 60))),
        step('Extrude the plate', EXTRUDE, ['Click Extrude. Distance A: 10 mm. Click OK.'], [(P, a, BLUE)]),
        step('Sketch the hole centres', SKETCH,
             ['Start 2D Sketch on the top face.', 'Draw a 76 by 36 rectangle on the centre and make it Construction (Format panel).',
              'Point: put a point on each corner of the construction rectangle. Click Finish Sketch.'],
             [(P, a, BLUE)], overlay=points(pts, 10)),
        step('Countersink the four holes', HOLE,
             ['Click Hole. Inventor picks all four sketch points.',
              'Type: Countersink. Diameter 6.6 mm, countersink diameter 13 mm, angle 90 degrees. Through All. Click OK.'],
             [(P, b, BLUE)]),
        step('Bore the 40 mm hole', HOLE,
             ['Click Hole and place it on the centre of the plate. Simple Hole. Diameter 40 mm. Through All. Click OK.'],
             [(P, c, BLUE)]),
        step('Chamfer the bore', CHAMFER,
             ['Click Chamfer. Distance 1 mm (1 x 45 degrees). Pick the top edge of the 40 mm bore. Click OK.'],
             [(P, d, BLUE)]),
    ]


# ------------------------------------------------------------------ 8 hole features
def hole_features():
    b = cq.Workplane('XY').box(110, 40, 20, centered=(False, True, False))
    stages = [b]
    top = lambda: stages[-1].faces('>Z').workplane(origin=(0, 0, 20))
    stages.append(top().pushPoints([(15, 0)]).hole(6.6))
    stages.append(top().pushPoints([(40, 0)]).cboreHole(6.6, 11, 6.5))
    stages.append(top().pushPoints([(68, 0)]).cskHole(6.6, 13, 90))
    stages.append(top().pushPoints([(95, 0)]).hole(5, 15))
    P = 'hole features block'
    pos = ' Place the centre on the centre line of the top face, %s from the left end.'
    return [
        step('Sketch the block', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XZ Plane (the top).',
              'Rectangle (Two Point): start at the origin.', finish('110 by 40')],
             [], overlay=face(cq.Workplane('XY').center(55, 0).rect(110, 40))),
        step('Extrude the block', EXTRUDE, ['Click Extrude. Distance A: 20 mm. Click OK.'], [(P, stages[0], GREEN)]),
        step('Clearance hole', HOLE,
             ['Click Hole and click the top face.' + pos % '15',
              'Type: Simple Hole. Diameter 6.6 mm (clearance for M6). Through All. Click OK.'],
             [(P, stages[1], GREEN)]),
        step('Counterbored hole (CBORE)', HOLE,
             ['Click Hole and click the top face.' + pos % '40',
              'Type: Counterbore. Diameter 6.6 mm, counterbore diameter 11 mm, counterbore depth 6.5 mm. Through All. Click OK.'],
             [(P, stages[2], GREEN)], note='A counterbore lets a cap head screw sit below the surface.'),
        step('Countersunk hole (CSK)', HOLE,
             ['Click Hole and click the top face.' + pos % '68',
              'Type: Countersink. Diameter 6.6 mm, countersink diameter 13 mm, angle 90 degrees. Through All. Click OK.'],
             [(P, stages[3], GREEN)]),
        step('Blind tapping drill hole', HOLE,
             ['Click Hole and click the top face.' + pos % '95',
              'Type: Simple Hole. Diameter 5 mm (tapping drill for M6). Termination: Distance, 15 mm. Drill Point: Flat. Click OK.'],
             [(P, stages[4], GREEN)],
             note='For a real tapped hole choose Tapped Hole, M6x1, and Inventor adds the 5 mm drill and a cosmetic thread.'),
    ]


# ------------------------------------------------------------------ 9 vee block
def vee_block():
    w, d, h = 80, 50, 50
    prof = cq.Workplane('XZ').polyline([(0, 0), (w, 0), (w, h), (w / 2 + 20, h), (w / 2, h - 20), (w / 2 - 20, h),
                                        (0, h)]).close()
    a = prof.extrude(-d)
    b = a.cut(cq.Workplane('XY').box(8, d, 12, centered=(True, False, False)).translate((w / 2, 0, h - 20 - 8)))
    c = b.cut(cq.Workplane('XY').box(30, d, 6, centered=(True, False, False)).translate((w / 2, 0, 0)))
    P = 'vee block'
    return [
        step('Sketch the vee profile', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XY Plane (the front).',
              'Line: draw the outline with the vee in the top, starting at the origin.',
              finish('80 wide, 50 high, the vee 40 across the top and 20 deep, centred')],
             [], overlay=face(prof)),
        step('Extrude the block', EXTRUDE, ['Click Extrude. Distance A: 50 mm, into the screen. Click OK.'],
             [(P, a, ORANGE)]),
        step('Cut the relief slot', EXTRUDE,
             ['Start 2D Sketch on the front face. Rectangle 8 wide, centred on the vee, from 8 below the bottom of the vee to above it.',
              'Finish Sketch. Extrude, Boolean: Cut, Extents: Through All. Click OK.'],
             [(P, b, ORANGE)], note='The relief slot gives clearance so a round bar sits on the two faces of the vee.'),
        step('Cut the base slot', EXTRUDE,
             ['Start 2D Sketch on the front face. Rectangle 30 wide and 6 high, centred on the bottom edge.',
              'Finish Sketch. Extrude, Boolean: Cut, Through All. Click OK.'],
             [(P, c, ORANGE)]),
    ]


# ------------------------------------------------------------------ 10 L bracket
def l_bracket():
    t = 5
    prof = cq.Workplane('XZ').polyline([(0, 0), (60, 0), (60, t), (t, t), (t, 50), (0, 50)]).close()
    a = prof.extrude(-40)
    b = a.edges('|Y').edges(cq.selectors.BoxSelector((t - 0.1, -1, t - 0.1), (t + 0.1, 41, t + 0.1))).fillet(6)
    c = b.edges('|Y').edges(cq.selectors.BoxSelector((-0.1, -1, -0.1), (0.1, 41, 0.1))).fillet(t + 6)
    d = c.cut(cq.Workplane('XY').center(40, 20).slot2D(18, 7, 0).extrude(t))
    e = d.cut(cq.Workplane('YZ').center(20, 32).circle(4).extrude(t))
    P = 'L bracket'
    return [
        step('Sketch the L profile', SKETCH,
             [NEW_PART + ' to start a new part.', 'Start 2D Sketch on the XY Plane (the front).',
              'Line: draw the L shape from the origin.', finish('base 60 long, upright 50 high, both 5 thick')],
             [], overlay=face(prof)),
        step('Extrude the bracket', EXTRUDE, ['Click Extrude. Distance A: 40 mm, into the screen. Click OK.'],
             [(P, a, GREEN)]),
        step('Inside bend radius', FILLET,
             ['Click Fillet. Radius 6 mm. Pick the inside corner edge. Click OK.'], [(P, b, GREEN)]),
        step('Outside bend radius', FILLET,
             ['Click Fillet. Radius 11 mm (6 inside + 5 thickness). Pick the outside corner edge. Click OK.'],
             [(P, c, GREEN)], note='Inside radius plus thickness gives an even 5 mm wall round the bend, as bent plate has.'),
        step('Cut the slot in the base', EXTRUDE,
             ['Start 2D Sketch on the top of the base. Slot (Center to Center): centres 11 apart (18 long overall), 7 wide, centred 40 from the back and in the middle of the width.',
              'Finish Sketch. Extrude, Boolean: Cut, Through All. Click OK.'],
             [(P, d, GREEN)]),
        step('Drill the hole in the upright', HOLE,
             ['Click Hole and click the outside face of the upright. Centre 32 up from the bottom, in the middle of the width.',
              'Simple Hole. Diameter 8 mm. Through All. Click OK.'],
             [(P, e, GREEN)],
             note='You can also make this part with the Sheet Metal tools: Face, then Flange, with a 5 mm thickness and a 6 mm bend radius.'),
    ]


# ------------------------------------------------------------------ 11 pin and housing fit
def fit_pair():
    a = cq.Workplane('XY').box(60, 40, 30, centered=(True, True, False))
    b = a.faces('>Z').workplane().hole(20)
    housing = b.edges('|Z').fillet(3)
    p1 = cq.Workplane('XY').circle(10).extrude(45).translate((0, 0, -5))
    pin = cq.Workplane('XY').circle(10).extrude(45).faces('>Z or <Z').chamfer(0.8).translate((0, 0, -5))
    H, PN = 'housing (hole 20 H7)', 'pin (shaft 20 g6)'
    return [
        step('Housing: sketch and extrude', EXTRUDE,
             [NEW_PART + ' and save it as housing.ipt.', 'Start 2D Sketch on the XZ Plane. Rectangle (Two Point Center) 60 by 40 on the origin. Finish Sketch.',
              'Extrude. Distance A: 30 mm. Click OK.'],
             [('housing', a, ALU)]),
        step('Housing: the 20 H7 hole', HOLE,
             ['Click Hole and place it on the centre of the top face. Simple Hole. Diameter 20 mm. Through All. Click OK.',
              'In the Parameters dialog (Manage tab) you can give the hole diameter the H7 tolerance so the drawing shows it.'],
             [('housing', b, ALU)]),
        step('Housing: round the corners', FILLET,
             ['Click Fillet. Radius 3 mm. Pick the four vertical corner edges. Click OK. Save housing.ipt.'],
             [('housing', housing, ALU)]),
        step('Pin: sketch and extrude', EXTRUDE,
             [NEW_PART + ' and save it as pin.ipt.', 'Start 2D Sketch on the XZ Plane. Circle on the origin, diameter 20. Finish Sketch.',
              'Extrude. Distance A: 45 mm. Click OK.'],
             [('pin', p1, STEEL)]),
        step('Pin: chamfer the ends', CHAMFER,
             ['Click Chamfer. Distance 0.8 mm. Pick the edge at each end. Click OK. Save pin.ipt.'],
             [('pin', pin, STEEL)], note='The g6 tolerance goes on the drawing: the model is at the nominal 20 mm.'),
        step('Assembly: fit the pin', CONSTRAIN,
             [NEW_ASSY + ' and save it as fit_pair.iam.', 'Place housing.ipt and right click, Place Grounded at Origin.',
              'Place pin.ipt. Constrain > Mate: pick the pin axis and the hole axis.',
              'Constrain > Flush with an offset of 5 mm: the bottom of the pin 5 below the bottom of the housing. Click OK.'],
             [(H, housing, ALU), (PN, pin, STEEL)]),
    ]


# ------------------------------------------------------------------ 12 pneumatic cylinder
def pneumatic_cylinder():
    bore, L = 32, 80
    barrel = cq.Workplane('YZ').circle(bore / 2 + 2).circle(bore / 2).extrude(L)
    cap_r0 = cq.Workplane('YZ').rect(44, 44).extrude(12).edges('|X').fillet(3).translate((-12, 0, 0))
    cap_r = cap_r0.cut(cq.Workplane('XZ').center(-6, 0).circle(3).extrude(-30, both=True))
    cap_f = cq.Workplane('YZ').rect(44, 44).extrude(12).edges('|X').fillet(3).translate((L, 0, 0))
    cap_f = cap_f.cut(cq.Workplane('YZ').circle(6.5).extrude(200, both=True))
    piston = cq.Workplane('YZ').circle(bore / 2 - 0.5).extrude(10).translate((6, 0, 0))
    rod = cq.Workplane('YZ').circle(6).extrude(L + 12 + 30).translate((6, 0, 0))
    turns = 7
    helix = cq.Wire.makeHelix(pitch=(L - 26) / turns, height=L - 26, radius=11)
    prof = cq.Workplane('XZ').center(11, 0).circle(1.2)
    spring = prof.sweep(cq.Workplane('XY').add(helix), isFrenet=True)
    spring = spring.rotate((0, 0, 0), (0, 1, 0), 90).translate((16, 0, 0))
    B = ('barrel', barrel, ALU)
    R = ('rear cap with air port', cap_r, DARK)
    F = ('front cap', cap_f, DARK)
    PI = ('piston', piston, ORANGE)
    RO = ('piston rod', rod, STEEL)
    SP = ('return spring', spring, BRASS)
    return [
        step('Barrel: a tube', EXTRUDE,
             [NEW_PART + ' and save it as barrel.ipt.', 'Start 2D Sketch on the YZ Plane. Two circles on the origin: diameter 36 and diameter 32. Finish Sketch.',
              'Extrude: click inside the ring so only the ring is picked. Distance A: 80 mm. Click OK.'],
             [B]),
        step('Rear cap: square end plate', FILLET,
             [NEW_PART + ' and save it as rear_cap.ipt.', 'Sketch a 44 by 44 Rectangle (Two Point Center) on the YZ Plane and Extrude it 12 mm.',
              'Fillet: radius 3 mm on the four edges along the thickness. Click OK.'],
             [('rear cap with air port', cap_r0, DARK)]),
        step('Rear cap: air port', HOLE,
             ['Click Hole and click a side face of the cap, half way through its 12 mm thickness and in the middle.',
              'Simple Hole. Diameter 6 mm. Through All. Click OK. Save rear_cap.ipt.'],
             [R], note='This is the port where the air comes in on the cylinder symbol.'),
        step('Front cap with rod hole', HOLE,
             ['Make front_cap.ipt the same way: 44 by 44 square, Extrude 12 mm, Fillet 3 mm.',
              'Hole on the centre of the face. Simple Hole. Diameter 13 mm. Through All. Click OK.'],
             [F]),
        step('Piston and piston rod', EXTRUDE,
             ['piston.ipt: Circle diameter 31 on the YZ Plane, Extrude 10 mm.',
              'rod.ipt: Circle diameter 12 on the YZ Plane, Extrude 122 mm.'],
             [PI, RO]),
        step('Return spring', COIL,
             [NEW_PART + ' and save it as spring.ipt.', 'Start 2D Sketch on the XY Plane. Draw a centre line along the X axis, and a circle of diameter 2.4 with its centre 11 from the line. Finish Sketch.',
              'Click Coil. Profile: the circle. Axis: the centre line.',
              'Coil Size tab: Type Pitch and Height. Pitch 7.71 mm, Height 54 mm (7 turns). Click OK.'],
             [SP]),
        step('Assembly: barrel and caps', CONSTRAIN,
             [NEW_ASSY + ' and save it as pneumatic_cylinder.iam.', 'Place barrel.ipt and right click, Place Grounded at Origin.',
              'Place rear_cap.ipt and front_cap.ipt. For each: Constrain > Mate the cap face to the end of the barrel, then Mate the cap centre axis to the barrel axis.'],
             [B, R, F]),
        step('Assembly: piston and rod', CONSTRAIN,
             ['Place piston.ipt and rod.ipt.', 'Constrain > Insert: the rod end into the piston face, so they share an axis.',
              'Constrain > Mate: the piston axis to the barrel axis, and the back of the piston 6 mm from the rear cap.'],
             [B, R, F, PI, RO]),
        step('Assembly: the spring', CONSTRAIN,
             ['Place spring.ipt.', 'Constrain > Mate: the spring axis to the rod axis.',
              'Constrain > Mate: one end of the spring against the front of the piston. Save the assembly.'],
             [B, R, F, PI, RO, SP],
             note='Spring return: air pushes the piston out, and the spring pushes it back when the air is let out.'),
    ]


STEPS = dict(step_block=step_block, sloping_block=sloping_block, flanged_bush=flanged_bush,
             bolted_joint=bolted_joint, threaded_shaft=threaded_shaft, pcd_flange=pcd_flange,
             annotation_plate=annotation_plate, hole_features=hole_features, vee_block=vee_block,
             l_bracket=l_bracket, fit_pair=fit_pair, pneumatic_cylinder=pneumatic_cylinder)


# ESP 2023 lock gate project: its steps live in their own file
from esp2023_steps import STEPS as ESP2023_STEPS  # noqa: E402
from esp2026_steps import STEPS as ESP2026_STEPS  # noqa: E402
from esp2024_steps import STEPS as ESP2024_STEPS  # noqa: E402
from esp2025_steps import STEPS as ESP2025_STEPS  # noqa: E402

STEPS.update(ESP2023_STEPS)
STEPS.update(ESP2026_STEPS)
STEPS.update(ESP2024_STEPS)
STEPS.update(ESP2025_STEPS)
