"""Autodesk Inventor build steps for the ESP 2023 lock gate models (see models/esp2023.py).

Same format as models/inventor_steps.py. Every stage is made with the same CadQuery functions as the finished
models, and tools/build_steps.py checks that the last stage matches the finished model.

The hub's models use Z up. Inventor's default is Y up, so the hub's XY plane (the ground) is Inventor's XZ Plane,
and the hub's XZ plane (looking at the front) is Inventor's XY Plane.
"""
import cadquery as cq
import esp2023 as E
from esp2023 import box, zcyl, ucyl

NEW_PART = 'File > New > Standard (mm).ipt'
SKETCH = '3D Model tab > Sketch panel > Start 2D Sketch'
EXTRUDE = '3D Model tab > Create panel > Extrude'
HOLE = '3D Model tab > Modify panel > Hole'
FILLET = '3D Model tab > Modify panel > Fillet'
SPLIT = '3D Model tab > Modify panel > Split'
RECT_PATTERN = '3D Model tab > Pattern panel > Rectangular Pattern'
WORK_PLANE = '3D Model tab > Work Features panel > Plane'
NEW_ASSY = 'File > New > Standard (mm).iam'
PLACE = 'Assemble tab > Component panel > Place'
CONSTRAIN = 'Assemble tab > Relationships panel > Constrain'
MIRROR = 'Assemble tab > Pattern panel > Mirror'


def step(title, command, actions, parts, overlay=None, note=None):
    return dict(title=title, command=command, actions=actions, parts=parts, overlay=overlay, note=note)


def flat(wp, z):
    """A sketch profile drawn as a thin plate at height z, so the viewer can show it."""
    return wp.translate((0, 0, z))


# ------------------------------------------------------------------ gate leaf (one welded part, then a sub-assembly)
def gate_leaf():
    F, LC = 'gate leaf (welded S355 steel)', E.LEAF_C
    T2, L = E.T2, E.LEAF
    heel_solid = zcyl(E.HEEL_R, 50, 5850).union(box(0, E.HEEL_BOX, -T2, T2, 50, 5850))
    heel_hollow = heel_solid.cut(zcyl(E.HEEL_R - 25, 350, 5825).union(box(0, E.HEEL_BOX - 25, -T2 + 25, T2 - 25, 350, 5825)))
    heel_bored = heel_hollow.cut(zcyl(80, 50, 300))
    hp = heel_bored.union(zcyl(100, 5850, 6000))
    stages = []
    for k in range(2, 7):
        stages.append(E.leaf_frame_raw(k))
    final = E.leaf_frame()
    prof_heel = zcyl(E.HEEL_R, 50, 51).union(box(0, E.HEEL_BOX, -T2, T2, 50, 51))
    girder_prof = None
    for z in E.GIRDERS:
        g = box(E.HEEL_BOX, E.HEEL_BOX + 2, -T2 + E.FLANGE[1], T2 - E.SKIN, z - E.WEB_T / 2, z + E.WEB_T / 2)
        g = g.union(box(E.HEEL_BOX, E.HEEL_BOX + 2, -T2, -T2 + E.FLANGE[1], max(50, z - 100), min(E.TOP, z + 100)))
        girder_prof = g if girder_prof is None else girder_prof.union(g)
    fen = E.fenders()
    fen1 = box(E.HEEL_BOX + 100, L - E.MITRE_BOX - 50, T2, T2 + 150, E.FENDERS[0] - 100, E.FENDERS[0] + 100).edges('|X').fillet(20)
    walk = E.walkway()
    grating = box(E.HEEL_BOX, L - E.MITRE_BOX, -T2, T2, E.TOP, E.HEIGHT)
    cill, heel_seal, mitre_seal = E.cill_seal(), E.heel_seal(), E._mitre_seal_local()
    return [
        step('Heel post: sketch the section', SKETCH,
             [NEW_PART + ' and save it as gate_leaf_frame.ipt.',
              'Start 2D Sketch on the XZ Plane (the ground). Draw a circle of diameter 450 on the origin: this is the round '
              'back of the heel post, and the origin is the pivot axis.',
              'Draw a rectangle from the centre of the circle, 400 along the leaf (X) and 450 wide (225 each side of X).',
              'Add the dimensions (Sketch tab > Constrain panel > Dimension): diameter 450, 400 and 450. Click Finish Sketch.'],
             [], overlay=prof_heel,
             note='Every gate size comes from the brief: a 4.2 m opening, 6 m high, holding up to 5.5 m of water. The leaf is 450 thick.'),
        step('Heel post: extrude it', EXTRUDE,
             ['Click Extrude and pick both regions of the sketch (the circle and the rectangle).',
              'Distance A: 5800 mm, upwards. Then in the Extrude dialog open Advanced and set a 50 mm start offset, so the post '
              'runs from 50 to 5850 above the cill (the bottom 50 mm is the cill seal).', 'Click OK.'],
             [(F, heel_solid, LC)]),
        step('Heel post: make it hollow', EXTRUDE,
             ['Start 2D Sketch on a Work Plane 350 mm above the base (Work Features panel > Plane > Offset from Plane).',
              'Offset the outline 25 mm inwards (Sketch tab > Modify panel > Offset): the post is made from 25 mm plate.',
              'Extrude the inner profile, Cut, Distance 5475 mm, upwards. Click OK.'],
             [(F, heel_hollow, LC)],
             note='The bottom 300 mm stays solid: it is the bearing block that sits on the pintle.'),
        step('Heel post: bore for the pintle', HOLE,
             ['Click Hole and pick the bottom face of the heel post, on the pivot axis (the origin).',
              'Simple Hole. Diameter 160 mm. Termination: Distance, 250 mm. Click OK.'],
             [(F, heel_bored, LC)],
             note='The 150 mm stainless pintle fits in this bore with a bronze bush: the leaf turns on it.'),
        step('Heel post: top journal', EXTRUDE,
             ['Start 2D Sketch on the top face of the heel post. Circle, diameter 200, on the pivot axis. Finish Sketch.',
              'Extrude 150 mm upwards. Click OK.'],
             [(F, hp, LC)], note='The anchor collar (the top hinge) fits round this journal.'),
        step('Mitre post', EXTRUDE,
             ['Sketch on the XZ Plane: a rectangle from X = 2160 to X = 2860, 450 wide. Extrude from 50 to 5960 mm.',
              'Make it a hollow box: sketch the inner rectangle (25 mm walls, ending 90 mm before the mitre) and Extrude Cut.',
              'The extra length past 2460 is trimmed to the mitre angle at the end.'],
             [(F, stages[0], LC)]),
        step('Horizontal girders', EXTRUDE,
             ['Start 2D Sketch on a Work Plane at X = 400 (the face of the heel post).',
              'Draw the eight T sections: web 20 thick from the downstream flange to the skin, flange 200 x 20, at heights '
              + ', '.join(str(z) for z in E.GIRDERS) + ' mm.',
              'Extrude all eight profiles 1760 mm along X, to the mitre post. Click OK.'],
             [(F, stages[1], LC)], overlay=girder_prof,
             note='The girders are closer together near the bottom because the water pressure grows with depth: '
                  'p = 1000 x 9.81 x depth, about 54 kPa at 5.5 m.'),
        step('Vertical stiffeners', EXTRUDE,
             ['Sketch on the XZ Plane at Z = 50: two rectangles 15 wide (X 980 to 995 and 1565 to 1580), between the flange and the skin.',
              'Extrude them up to 5960 mm. Click OK.'],
             [(F, stages[2], LC)], note='The stiffeners split the skin plate into panels about 580 x 630, which keeps the plate stress low.'),
        step('Skin plate', EXTRUDE,
             ['Sketch on the XZ Plane: a rectangle 12 mm thick on the chamber (upstream) face, from X = 400 to 2860.',
              'Extrude from 50 to 5960 mm. Click OK.'],
             [(F, stages[3], LC)], note='The 12 mm skin plate on the chamber face holds back the water.'),
        step('Actuator bracket', EXTRUDE,
             ['Sketch on the skin plate face: a rectangle 100 wide (centred 1000 mm from the pivot) and 200 high (5700 to 5900).',
              'Extrude it 125 mm out from the skin. Click OK.'],
             [(F, stages[4], LC)], note='The electric actuator rod eye bolts to this bracket.'),
        step('Trim the mitre end', SPLIT,
             ['Click Work Features panel > Plane > Angle to Plane around Edge. Pick the end face of the mitre post and the '
              'vertical edge where the leaf centre line meets X = 2460. Angle 18.43 degrees (1 in 3).',
              'Click Split. Split Tool: the new work plane. Choose Trim Solid and pick the side beyond the mitre to remove.',
              'Click OK. Save gate_leaf_frame.ipt.'],
             [(F, final, LC)],
             note='Both leaves are cut at 1 in 3 so they meet at the mitre, pointing upstream. The water pushes the mitre faces together.'),
        step('Oak fenders: one fender', FILLET,
             [NEW_PART + ' and save it as oak_fenders.ipt.',
              'Sketch a 150 x 200 rectangle on a Work Plane at X = 500, against the skin plate face, with its centre at 2600 mm high.',
              'Extrude it 1610 mm along the leaf. Fillet the four long edges, radius 20 mm.'],
             [(F, final, LC), ('oak fenders', fen1, E.OAK)],
             note='FSC certified oak: a sustainable, replaceable rubbing face for boats.'),
        step('Oak fenders: pattern them', RECT_PATTERN,
             ['Click Rectangular Pattern and pick the fender.', 'Direction 1: the Y axis (up). Count 3. Spacing 900 mm. Click OK.',
              'Save oak_fenders.ipt.'],
             [(F, final, LC), ('oak fenders', fen, E.OAK)],
             note='Fenders at 2.6 m, 3.5 m and 4.4 m cover the water levels a boat sits at as the lock fills and empties.'),
        step('Walkway and handrail', EXTRUDE,
             [NEW_PART + ' and save it as walkway.ipt.',
              'Sketch a 1760 x 450 rectangle on the XZ Plane and Extrude 40 mm: the galvanised grating.',
              'Sketch three circles, diameter 48.3, near the downstream edge and Extrude 1100 mm: the handrail posts.',
              'Sketch two circles diameter 48.3 on a plane square to the leaf and Extrude 1608 mm: the mid rail and top rail.'],
             [(F, final, LC), ('oak fenders', fen, E.OAK), ('walkway and handrail', walk, E.WHITE)],
             note='The walkway lets the lock keeper cross the lock and look at the moving parts.'),
        step('Seals', SPLIT,
             [NEW_PART + ' for each seal: cill_seal.ipt (85 x 50 strip under the chamber face, trimmed at the mitre with Split), '
              'heel_seal.ipt (30 x 80 strip down the back of the heel post) and mitre_seal.ipt (30 wide strip on the mitre face).',
              'Use the material EPDM rubber (Manage tab > Styles Editor if it is not in your library).'],
             [(F, final, LC), ('oak fenders', fen, E.OAK), ('walkway and handrail', walk, E.WHITE),
              ('cill seal', cill, E.RUBBER), ('heel seal', heel_seal, E.RUBBER), ('mitre seal', mitre_seal, E.RUBBER)],
             note='Three seals stop water passing the gate: along the cill, behind the heel post in the quoin, and between the mitre posts.'),
        step('Put the leaf together', CONSTRAIN,
             [NEW_ASSY + ' and save it as gate_leaf.iam.',
              'Place gate_leaf_frame.ipt and right click, Place Grounded at Origin.',
              'Place the fenders, walkway and seals. Constrain each with Mate (face to face) and Flush, using the sizes above.',
              'Check with Inspect tab > Interference > Analyze Interference: no parts should overlap.'],
             [(F, final, LC), ('oak fenders', fen, E.OAK), ('walkway and handrail', walk, E.WHITE),
              ('cill seal', cill, E.RUBBER), ('heel seal', heel_seal, E.RUBBER), ('mitre seal', mitre_seal, E.RUBBER)]),
    ]


# ------------------------------------------------------------------ skin plate panel
def skin_panel():
    u0, u1, z0, z1 = E.PANEL
    plate = box(u0, u1, E.T2 - E.SKIN, E.T2, z0, z1)
    return [
        step('Sketch the panel', SKETCH,
             [NEW_PART + ' and save it as skin_panel.ipt.', 'Start 2D Sketch on the XY Plane (the front).',
              'Draw a rectangle 580 wide and 630 high, its bottom left corner 400 along and 160 up from the origin, so the '
              'panel sits where it does in the leaf.', 'Finish Sketch.'],
             [], overlay=box(u0, u1, E.T2 - 1, E.T2, z0, z1)),
        step('Extrude the plate', EXTRUDE,
             ['Click Extrude. Distance 12 mm. Click OK.'],
             [('skin plate panel', plate, E.LEAF_C)],
             note='The panel is held on all four edges by the girders, the heel post and a stiffener, so in the FEA all four edge faces are fixed.'),
    ]


# ------------------------------------------------------------------ lock gates general arrangement
def lock_gates():
    L, R = -1, 1
    fixed = {s: dict((p, (p, w, c)) for p, w, c in E.fixed_parts(s)) for s in (L, R)}
    ch = [fixed[s]['%s inspection chamber' % n] for s, n in ((L, 'left'), (R, 'right'))]
    hinges = [fixed[s]['%s %s' % (n, k)] for s, n in ((L, 'left'), (R, 'right')) for k in ('bottom pintle', 'anchor collar')]
    leafL, leafR = E.leaf_parts(L), E.leaf_parts(R)
    acts = []
    for s, n in ((L, 'left'), (R, 'right')):
        b, r = E.actuator(s)
        acts += [('%s actuator body' % n, b, E.ACT_C), ('%s actuator rod' % n, r, E.STAINLESS)]
    cams = [fixed[s]['%s %s' % (n, k)] for s, n in ((L, 'left'), (R, 'right')) for k in ('CCTV mast', 'call point')]
    w, g0, d0 = E.actuator_geometry(R, 0)
    return [
        step('Lay out the lock and the chambers', PLACE,
             [NEW_ASSY + ' and save it as esp2023_lock_gates.iam.',
              'Place inspection_chamber.ipt and right click, Place Grounded. Place a second copy for the other side.',
              'The lock walls are 4200 apart. Each chamber starts 300 mm behind the pivot, and is 2350 x 1800 x 1000 deep '
              'with 150 mm walls, a slot for the actuator rod and a plinth for the actuator pivot.'],
             ch, note='The drive goes in a purpose-built chamber beside each gate, out of sight under a grating cover (left off here so you can see in).'),
        step('Place the hinges', CONSTRAIN,
             ['Place bottom_pintle.ipt twice and anchor_collar.ipt twice.',
              'The pivot axes are %.0f mm each side of the lock centre line, in the hollow quoins.' % E.PIV,
              'Constrain > Mate each pintle axis to the collar axis above it, and Flush the pintle base with the cill (Z = 0).'],
             ch + hinges, note='The bottom pintle takes the weight of the leaf. The anchor collar at the top stops the leaf toppling forwards.'),
        step('Place the left leaf', CONSTRAIN,
             ['Place gate_leaf.iam (the sub-assembly from the gate leaf build steps).',
              'Constrain > Insert: the heel post bore onto the left pintle. Mate the top journal axis to the collar axis.',
              'Constrain > Angle: 18.43 degrees between the leaf and the line across the lock, so the mitre points upstream.'],
             ch + hinges + leafL,
             note='Suppress the Angle constraint later so the leaf can turn on its hinge for the simulation.'),
        step('Mirror the right leaf', MIRROR,
             ['Click Mirror. Pick the parts of the left leaf. Mirror plane: the YZ Plane (the lock centre line).',
              'Leave the mitre seal out (it belongs to the left leaf only). Choose Mirror for the parts, so Inventor makes '
              'right hand copies, and click Next, then OK.',
              'Constrain the right leaf to its pintle and collar the same way.'],
             ch + hinges + leafL + leafR,
             note='The two mitre posts close on to the 30 mm mitre seal. Check with Analyze Interference that nothing overlaps.'),
        step('Fit the actuators', CONSTRAIN,
             ['Place actuator_body.ipt and actuator_rod.ipt for each side.',
              'Constrain > Mate the body pivot axis to the plinth axis, 250 mm above it.',
              'Constrain > Mate the rod axis to the body axis, and Mate the rod eye centre to the bracket on the leaf.',
              'Shut, the pivot to eye length is %.0f mm.' % d0],
             ch + hinges + leafL + leafR + acts,
             note='An electric actuator needs only the mains supply that the brief offers, and has no hydraulic oil to leak into the canal.'),
        step('Add the CCTV masts and call points', PLACE,
             ['Place cctv_mast.ipt on the far corner of each chamber and call_point.ipt on the near corner.',
              'Constrain each with Mate to the top of the chamber wall. Save the assembly.'],
             ch + hinges + leafL + leafR + acts + cams,
             note='The cameras let the control centre watch each gate. The call point lets anyone stop the gates in an emergency.'),
    ]


# ------------------------------------------------------------------ concept B: lift gate
def lift_gate():
    full = dict((p, (p, w, c)) for p, w, c in E.lift_gate())
    w, t = E.OPENING + 400, 400
    panel0 = box(-w / 2, w / 2, -t / 2, t / 2, 0, E.HEIGHT)
    return [
        step('Gate panel', EXTRUDE,
             [NEW_PART + ' and save it as lift_gate_panel.ipt.', 'Sketch a 4600 x 400 rectangle on the XZ Plane and Extrude it 6000 mm up.'],
             [('lift gate panel', panel0, E.LEAF_C)]),
        step('Lighten the panel', EXTRUDE,
             ['Sketch four 4000 x 700 rectangles on the downstream face, at 1000, 2500, 4000 and 5400 mm.',
              'Extrude Cut 150 mm deep. Click OK.'],
             [full['lift gate panel']], note='The pockets show where the stiffening girders would be.'),
        step('Towers, beam and counterweights', EXTRUDE,
             [NEW_PART + ' for the guide towers (700 x 900, 11 m high, with a 150 mm slot for the gate), the lifting beam and the counterweights.'],
             [full['lift gate panel'], full['guide towers'], full['lifting beam and winch house'], full['counterweights']]),
        step('Assemble the concept', CONSTRAIN,
             [NEW_ASSY + ' and save it as lift_gate.iam. Place the towers grounded, then Mate the panel into the slots.'],
             [full['lift gate panel'], full['guide towers'], full['lifting beam and winch house'], full['counterweights']],
             note='Rejected for the final design: the 11 m towers would tower over a heritage canal, and the gate must lift '
                  'high enough for boats to pass under, so it is slow and needs a large winch.'),
    ]


STEPS = dict(esp2023_lock_gates=lock_gates, esp2023_gate_leaf=gate_leaf, esp2023_skin_panel=skin_panel,
             esp2023_lift_gate=lift_gate)
