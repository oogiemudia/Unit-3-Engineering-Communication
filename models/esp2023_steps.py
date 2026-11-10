"""Autodesk Inventor build steps for the ESP 2023 lock gate models (see models/esp2023.py).

Same format as models/inventor_steps.py. Every stage is made with the same CadQuery shapes as the finished
models, and tools/build_steps.py checks that the last stage matches the finished model.

Each part has its own steps (the features listed with it in esp2023.PARTS). The gate leaf and the general
arrangement are assemblies: their steps place the parts one group at a time.

The hub's models use Z up. Inventor's default is Y up, so the hub's XY plane (the ground) is Inventor's XZ Plane,
and the hub's XZ plane (looking at the front) is Inventor's XY Plane.
"""
import esp2023 as E
from esp2023 import box, NEW_ASSY, PLACE, CONSTRAIN, MIRROR, PATTERN, CONTENT, EXTRUDE


def step(title, command, actions, parts, overlay=None, note=None):
    return dict(title=title, command=command, actions=actions, parts=parts, overlay=overlay, note=note)


# ------------------------------------------------------------------ each part
def part_steps(p):
    def fn():
        out = []
        for f in E.features(p['key']):
            ox, oy, oz = p['origin']
            out.append(step(f['title'], f['command'], f['actions'],
                            [(p['name'], f['shape'].translate((-ox, -oy, -oz)), p['colour'])], note=f['note']))
        return out
    return fn


# ------------------------------------------------------------------ gate leaf (an assembly of its parts)
def _pick(items, *keys):
    return [(n, s, E.colour(k)) for n, k, s in items if k in keys]


def gate_leaf():
    items = [it for it in E.leaf_items() if it[1] != 'pivot_pin']
    frame = []
    stages = [
        (('heel_post',), 'Place the heel post', PLACE,
         [NEW_ASSY + ' and save it as gate_leaf.iam.',
          'Place heel_post.ipt, right click and choose Place Grounded at Origin. Its origin is the pivot axis, so the '
          'whole leaf is built from the hinge.'],
         'Make the leaf a weldment: Environments tab > Convert to Weldment, so the welds and the welded parts are kept together.'),
        (('mitre_post',), 'Place the mitre post', CONSTRAIN,
         ['Place mitre_post.ipt. Constrain > Flush its bottom with the heel post bottom (50 mm above the cill).',
          'Mate its back face 1760 mm from the heel post face (Mate with offset), and Flush the front faces.'], None),
        (('girder',), 'Place the eight girders', PATTERN,
         ['Place girder.ipt between the posts: Mate the ends to the post faces and Flush the flange with the downstream face.',
          'Offset its centre 150 mm above the base. Then place seven more at ' + ', '.join(str(z) for z in E.GIRDERS[1:]) +
          ' mm (or Pattern with the levels typed in).'],
         'The girders are closer together near the bottom because the water pressure grows with depth: p = 1000 x 9.81 x depth.'),
        (('stiffener',), 'Slot in the stiffeners', CONSTRAIN,
         ['Place stiffener.ipt twice. Mate each into the girder slots, at 980 and 1565 mm from the pivot.'],
         'The slots interlock like an egg box: half depth in the girder, half depth in the stiffener.'),
        (('skin_plate',), 'Place the skin plate', CONSTRAIN,
         ['Place skin_plate.ipt. Mate its back face to the girder webs, Flush its bottom and its ends with the posts.'],
         'The skin plate is on the chamber (upstream) side, where the water is.'),
        (('actuator_bracket', 'lifting_lug', 'paddle_culvert'), 'Bracket, lifting lugs and paddle culvert', CONSTRAIN,
         ['Place actuator_bracket.ipt on the skin plate, 1000 mm from the pivot, its lug at 5800 mm.',
          'Place lifting_lug.ipt twice: on top of the heel post (300 mm from the pivot) and on top of the mitre post.',
          'Place paddle_culvert.ipt behind the paddle opening, between the second and third girders.',
          'Weldment: Welds panel > Fillet. Weld every joint of the frame (6 mm fillets for the skin plate, 8 mm for the posts).'],
         'The lifting lugs let the leaf be lifted out by mobile crane, as the brief asks.'),
        (('pintle_bush',), 'Press in the pintle bush', CONSTRAIN,
         ['Place pintle_bush.ipt. Constrain > Insert it into the bore in the foot of the heel post.'],
         'Bronze on stainless steel: durable, with no grease to wash into the canal.'),
        (('oak_fender',), 'Fit the oak fenders', PATTERN,
         ['Place oak_fender.ipt on the skin plate, 2600 mm up. Pattern it: 3 in a column, 900 mm apart.'],
         'Fenders at 2.6 m, 3.5 m and 4.4 m cover the water levels a boat sits at as the lock fills and empties.'),
        (('walkway_grating', 'handrail'), 'Walkway and handrail', CONSTRAIN,
         ['Place walkway_grating.ipt on top of the frame and handrail.ipt on its downstream edge.'],
         'The walkway lets the lock keeper cross the lock and gives access to look at the moving parts.'),
        (('cill_seal', 'heel_seal', 'mitre_seal'), 'Fit the seals', CONSTRAIN,
         ['Place cill_seal.ipt under the chamber face, heel_seal.ipt down the back of the heel post and '
          'mitre_seal.ipt on the mitre face.'],
         'Three seals stop water passing the gate: along the cill, behind the heel post in the quoin, and between the mitre posts.'),
        (('paddle_door', 'paddle_guide', 'paddle_rod', 'paddle_actuator'), 'Fit the gate paddle', CONSTRAIN,
         ['Place paddle_guide.ipt twice on the downstream face either side of the culvert (turn the second one over).',
          'Place paddle_door.ipt between the guides, over the culvert. Place paddle_rod.ipt on the door lug, and '
          'paddle_actuator.ipt on the top girder over the rod.',
          'Inspect tab > Interference > Analyze Interference: no parts should overlap. Save.'],
         'The paddle lets the lock empty through the gate before the gates open: the water levels must be equal first.'),
    ]
    out, keys = [], set()
    for ks, title, cmd, actions, note in stages:
        keys |= set(ks)
        out.append(step(title, cmd, actions, _pick(items, *keys), note=note))
    return out


# ------------------------------------------------------------------ skin plate panel
def skin_panel():
    u0, u1, z0, z1 = E.PANEL
    plate = box(u0, u1, E.T2 - E.SKIN, E.T2, z0, z1)
    return [
        step('Sketch the panel', '3D Model tab > Sketch panel > Start 2D Sketch',
             [E.NEW_PART + ' and save it as skin_panel.ipt.', 'Start 2D Sketch on the XY Plane (the front).',
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
    items = E.ga_instances(0)

    def pick(pred):
        return [(n, s, E.colour(k)) for n, k, s in items if pred(n, k)]
    base = lambda n: n.replace('left ', '', 1).replace('right ', '', 1)
    leaf_names = {nm for nm, k, t in E.leaf_instances(-1)} | {'mitre seal'}
    groups = [
        ('Place the cill', PLACE,
         [NEW_ASSY + ' and save it as esp2023_lock_gates.iam.',
          'Place cill.ipt, right click and Place Grounded at Origin. The origin is on the lock centre line, on top of the cill.'],
         lambda n, k: k == 'cill', 'The concrete cill is where the gates seal at the bottom, and it holds the pintles.'),
        ('Fit the hinges', CONSTRAIN,
         ['Place bottom_pintle.ipt in each pocket, %.0f mm each side of the centre line. Insert four anchor_bolt.ipt '
          '(Content Center, or the part) through each base plate.' % E.PIV,
          'Place anchor_collar.ipt and collar_bush.ipt over each pivot, 5870 mm up, with the arm pointing into the wall. '
          'Place anchor_plate.ipt at the end of each arm with two more anchor bolts.'],
         lambda n, k: k in ('bottom_pintle', 'anchor_bolt', 'anchor_collar', 'collar_bush', 'anchor_plate'),
         'The pintle takes the weight of the leaf. The anchor collar at the top stops it tipping forwards.'),
        ('Place the left leaf', CONSTRAIN,
         ['Place gate_leaf.iam (the sub-assembly from the gate leaf build steps).',
          'Constrain > Insert: the pintle bush on to the left pintle. Mate the top journal axis to the collar axis.',
          'Constrain > Angle: 18.43 degrees between the leaf and the line across the lock, so the mitre points upstream.'],
         lambda n, k: n.startswith('left') and base(n) in leaf_names and k != 'pivot_pin' or n == 'mitre seal',
         'Suppress the Angle constraint later so the leaf can turn on its hinge for the simulation.'),
        ('Mirror the right leaf', MIRROR,
         ['Click Mirror. Pick gate_leaf.iam. Mirror plane: the YZ Plane (the lock centre line).',
          'Leave the mitre seal out (only the left leaf has it). Constrain the right leaf to its pintle and collar.'],
         lambda n, k: base(n) in leaf_names and k != 'pivot_pin',
         'The two mitre posts close on to the 30 mm mitre seal.'),
        ('Inspection chambers', PLACE,
         ['Place inspection_chamber.ipt beside each quoin, 300 mm behind the pivot, its top at ground level (6000).',
          'Place actuator_plinth.ipt in each chamber against the end wall, and control_panel.ipt on the end wall.'],
         lambda n, k: k in ('inspection_chamber', 'actuator_plinth', 'control_panel'),
         'The drive goes in a purpose-built chamber beside each gate, out of sight, as the brief asks.'),
        ('Fit the actuators', CONSTRAIN,
         ['Place pivot_pedestal.ipt on each plinth. Place actuator_body.ipt and Mate its rear eye to the pedestal; '
          'place actuator_motor.ipt under the tube.',
          'Place actuator_rod.ipt in the tube bore (Mate axis to axis) and rod_end.ipt on the end of the rod.',
          'Pin the rod end to the bracket on the leaf and the rear eye to the pedestal with pivot_pin.ipt.'],
         lambda n, k: k in ('pivot_pedestal', 'actuator_body', 'actuator_motor', 'actuator_rod', 'rod_end', 'pivot_pin'),
         'An electric actuator needs only the mains supply the brief offers, and has no hydraulic oil to leak into the canal.'),
        ('Sensors, CCTV and call points', PLACE,
         ['Place encoder_bracket.ipt on each anchor collar arm and position_encoder.ipt over the pivot, its shaft on the journal.',
          'Place cctv_mast.ipt and cctv_camera.ipt on the far corner of each chamber, call_point_post.ipt and '
          'call_point.ipt on the near corner.'],
         lambda n, k: k in ('encoder_bracket', 'position_encoder', 'cctv_mast', 'cctv_camera', 'call_point_post', 'call_point'),
         'The encoder tells the control centre the angle of each leaf; the cameras let it watch; the call point lets anyone stop the gates.'),
        ('Cover the chambers', PATTERN,
         ['Place cover_panel.ipt in the rebate of each chamber and Pattern it: 3 along the chamber.',
          'Inspect tab > Interference > Analyze Interference with the leaves shut, half open and open. Save.'],
         lambda n, k: k == 'cover_panel',
         'In the 3D viewer the covers are hidden at first so you can see the drive: tick them on in the parts list.'),
    ]
    out, preds = [], []
    for title, cmd, actions, pred, note in groups:
        preds.append(pred)
        out.append(step(title, cmd, actions, pick(lambda n, k: any(p(n, k) for p in preds)), note=note))
    return out


# ------------------------------------------------------------------ concept B: lift gate
def lift_gate():
    full = dict((p, (p, w, c)) for p, w, c in E.lift_gate())
    w, t = E.OPENING + 400, 400
    panel0 = box(-w / 2, w / 2, -t / 2, t / 2, 0, E.HEIGHT)
    return [
        step('Gate panel', EXTRUDE,
             [E.NEW_PART + ' and save it as lift_gate_panel.ipt.', 'Sketch a 4600 x 400 rectangle on the XZ Plane and Extrude it 6000 mm up.'],
             [('lift gate panel', panel0, E.LEAF_C)]),
        step('Lighten the panel', EXTRUDE,
             ['Sketch four 4000 x 700 rectangles on the downstream face, at 1000, 2500, 4000 and 5400 mm.',
              'Extrude Cut 150 mm deep. Click OK.'],
             [full['lift gate panel']], note='The pockets show where the stiffening girders would be.'),
        step('Towers, beam and counterweights', EXTRUDE,
             [E.NEW_PART + ' for the guide towers (700 x 900, 11 m high, with a 150 mm slot for the gate), the lifting beam and the counterweights.'],
             [full['lift gate panel'], full['guide towers'], full['lifting beam and winch house'], full['counterweights']]),
        step('Assemble the concept', CONSTRAIN,
             [NEW_ASSY + ' and save it as lift_gate.iam. Place the towers grounded, then Mate the panel into the slots.'],
             [full['lift gate panel'], full['guide towers'], full['lifting beam and winch house'], full['counterweights']],
             note='Rejected for the final design: the 11 m towers would tower over a heritage canal, and the gate must lift '
                  'high enough for boats to pass under, so it is slow and needs a large winch.'),
    ]


STEPS = dict(esp2023_lock_gates=lock_gates, esp2023_gate_leaf=gate_leaf, esp2023_skin_panel=skin_panel,
             esp2023_lift_gate=lift_gate)
for _p in E.PARTS:
    STEPS[E.part_model_name(_p)] = part_steps(_p)
