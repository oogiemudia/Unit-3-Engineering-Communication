"""Autodesk Inventor build steps for the ESP 2025 automated pill dispenser models (see models/esp2025.py).

Same format as models/inventor_steps.py. Every stage is made with the same CadQuery shapes as the finished
models, and tools/build_steps.py checks that the last stage matches the finished model.

Each part has its own steps (the features listed with it in esp2025.PARTS). Each sub-assembly places its parts a
group at a time, and the dispenser places the six sub-assemblies in the order they are built.

The hub's models use Z up. Inventor's default is Y up, so the hub's XY plane (the table) is Inventor's XZ Plane,
and the hub's XZ plane (the front view) is Inventor's XY Plane.
"""
import esp2025 as E
from esp2025 import NEW_ASSY, PLACE, CONSTRAIN, EXTRUDE, CONTENT


def step(title, command, actions, parts, overlay=None, note=None):
    return dict(title=title, command=command, actions=actions, parts=parts, overlay=overlay, note=note)


# ------------------------------------------------------------------ each part
def part_steps(p):
    def fn():
        out = []
        ox, oy, oz = p['origin']
        for f in E.features(p['key']):
            out.append(step(f['title'], f['command'], f['actions'],
                            [(p['name'], f['shape'].translate((-ox, -oy, -oz)), p['colour'])], note=f['note']))
        return out
    return fn


# ------------------------------------------------------------------ the sub-assemblies
def sub_steps(d):
    def fn():
        items = E.sub_items(d['key'])
        out, keys = [], set()
        for names, title, cmd, actions, note in d['steps']:
            keys |= set(names)
            out.append(step(title, cmd, actions, [(n, s, E.colour(k)) for n, k, s in items if n in keys], note=note))
        return out
    return fn


# ------------------------------------------------------------------ the dispenser
STAGES = [
    ('chassis', 'Place the chassis', PLACE,
     [NEW_ASSY + ' and save it as esp2025_dispenser.iam.',
      'Place chassis.iam (sub-assembly 1: chassis, pharmacy lock and cam, chute and drop sensors) and Place Grounded.'],
     'Build each sub-assembly first (see its own Build steps), then place them here. The chassis is the base part.'),
    ('carousel', 'Carousel', CONSTRAIN,
     ['Place carousel.iam (sub-assembly 2): Insert the hub tube in the hole in the deck, Mate the bottom of the ribs to '
      'the deck, and Angle a blank segment over the drop hole (the home position).'],
     'In the factory the carousel goes in from the top and the drive gear is pressed on its hub from underneath.'),
    ('pod', 'Control pod', CONSTRAIN,
     ['Place control_pod.iam (sub-assembly 4) up through the carousel hub: Insert the column on the axis, with the '
      'button to the front.'], 'The pod does not turn: the carousel turns round it.'),
    ('base', 'Base, batteries and drive', CONSTRAIN,
     ['Place base.iam (sub-assembly 3) under the chassis: Mate the gasket to the bottom of the chassis wall, Insert '
      'the pod column in its socket, and check the worm touches the drive gear.'], None),
    ('ga', 'Cover screws', CONTENT,
     ['Place from Content Center: a 2.5 x 10 countersunk thread forming screw in one cover hole (Insert); '
      'Pattern, Circular, 4.'], 'The screws squeeze the gasket between the cover and the chassis.'),
    ('lid', 'Lid and hinge', CONSTRAIN,
     ['Place lid.iam (sub-assembly 5): Insert the hinge pin through the chassis knuckles, and Mate the lid gasket to '
      'the top of the chassis wall (closed). Turn the lock cam to Angle 0: locked.'], None),
    ('drawer', 'Drawer', CONSTRAIN,
     ['Place drawer.iam (sub-assembly 6) in the front opening: Mate the seal to the case, Flush the centre planes.',
      'Inspect tab > Interference > Analyze Interference: no parts overlap. Save.'],
     'All parts are now in place.'),
]


def dispenser_steps():
    items = [(n, k, s, E.sub_of(n)) for n, k, s in E.dispenser_instances()]
    out, done = [], set()
    for key, title, cmd, actions, note in STAGES:
        done.add(key)
        if key == 'drawer':
            note = 'All %d parts are now in place.' % len(items)
        out.append(step(title, cmd, actions, [(n, s, E.colour(k)) for n, k, s, sub in items if sub in done], note=note))
    return out


# ------------------------------------------------------------------ concept B
def cassette():
    full = {p: (p, w, c) for p, w, c in E.cassette_dispenser()}
    order = ['case', '28 compartments', 'trapdoors and latches', 'pill tray', 'clear lid', 'display and PRESS HERE button']
    texts = [
        ('Case', EXTRUDE, [E.NEW_PART + ' for the case: sketch 186 x 124, fillet the corners R10, Extrude 30, Shell 2.']),
        ('Compartments', EXTRUDE, ['Sketch a 22.8 x 21.6 pocket; Rectangular Pattern 7 x 4. Extrude Cut 18.']),
        ('Trapdoors and pill tray', EXTRUDE, ['Under the grid, a layer of 28 spring trapdoors and latches; a pill tray along the front.']),
        ('Lid and controls', CONSTRAIN, [NEW_ASSY + ' and save it as cassette.iam. Place the parts, the clear lid and the '
                                         'display and PRESS HERE button on top.']),
    ]
    groups = [order[:1], order[:2], order[:4], order]
    out = []
    for i, (title, cmd, actions) in enumerate(texts):
        note = None
        if i == len(texts) - 1:
            note = ('Rejected for the final design: 28 latches cost more and weigh more than one motor, every trapdoor '
                    'can stick or leak, and the box is too wide to hold in one hand.')
        out.append(step(title, cmd, actions, [full[p] for p in groups[i]], note=note))
    return out


STEPS = dict(esp2025_dispenser=dispenser_steps, esp2025_cassette=cassette)
for _d in E.SUBS:
    STEPS[E.sub_model_name(_d)] = sub_steps(_d)
for _p in E.PARTS:
    STEPS[E.part_model_name(_p)] = part_steps(_p)
