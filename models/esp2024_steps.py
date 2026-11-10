"""Autodesk Inventor build steps for the ESP 2024 harbour buoy models (see models/esp2024.py).

Same format as models/inventor_steps.py. Every stage is made with the same CadQuery shapes as the finished
models, and tools/build_steps.py checks that the last stage matches the finished model.

Each part has its own steps (the features listed with it in esp2024.PARTS). Each sub-assembly places its parts a
group at a time, and the buoy places the six sub-assemblies in the order they are built.

The hub's models use Z up. Inventor's default is Y up, so the hub's XY plane (the waterline) is Inventor's XZ Plane,
and the hub's XZ plane (the front view) is Inventor's XY Plane.
"""
import esp2024 as E
from esp2024 import NEW_ASSY, PLACE, CONSTRAIN, EXTRUDE


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


# ------------------------------------------------------------------ the buoy
def buoy_steps(variant='red'):
    def fn():
        items = [(n, k, s, E.sub_of(n)) for n, k, s in E.buoy_instances(variant)]
        top = 'topmark_can.ipt (a red can)' if variant == 'red' else 'topmark_cone.ipt (a green cone)'
        stages = [
            ('float', 'Place the float', PLACE,
             [NEW_ASSY + ' and save it as esp2024_buoy%s.iam.' % ('' if variant == 'red' else '_green'),
              'Place float.iam (sub-assembly 1: hull, foam, fender, deck and keel plates, tie rods and eye nuts) and '
              'Place Grounded.'],
             'Build each sub-assembly first (see its own Build steps), then place them here. The float is the base.'),
            ('equipment', 'Equipment canister', CONSTRAIN,
             ['Place equipment_canister.iam (sub-assembly 2) in the well: Insert the canister on the well (axis to axis, '
              'flange underside to the top of the deck plate). Line up a lid bolt hole with the X axis (Angle 0).'],
             'The battery and control unit sit low in the float, inside a locked, watertight canister.'),
            ('tail', 'Tail and ballast', CONSTRAIN,
             ['Place tail.iam (sub-assembly 3) under the keel plate: Mate the flange to the keel plate and Insert a flange '
              'bolt in a tapped hole.'],
             'The ballast hangs %d mm below the waterline, which keeps the buoy upright.' % -E.TAIL_BOT),
            ('mast', 'Mast and solar panels', CONSTRAIN,
             ['Place mast.iam (sub-assembly 4) on the deck plate: Mate the leg feet to the deck plate and Insert the leg '
              'bolts in the tapped holes, a leg on the +Y side.'], None),
            ('top', 'Lantern and topmark', CONSTRAIN,
             ['Place lantern_topmark.iam (sub-assembly 5) on the mast top plate: Mate the lantern base and strut feet to '
              'the plate and Insert on the axis. Use %s.' % top],
             'Red can for a buoy leaving the harbour, green cone for one entering.'),
            ('mooring', 'Mooring and load pin', CONSTRAIN,
             ['Place mooring.iam (sub-assembly 6): Insert the load pin through the mooring eye, the pin bearing on the '
              'bottom of the hole.',
              'Inspect tab > Interference > Analyze Interference: no parts overlap. Save.'],
             'All %d parts are now in place. On site the chain is joined to the sinker (sub-assembly 7).' % len(items)),
        ]
        out, done = [], set()
        for key, title, cmd, actions, note in stages:
            done.add(key)
            out.append(step(title, cmd, actions, [(n, s, E.colour(k, variant)) for n, k, s, sub in items if sub in done],
                            note=note))
        return out
    return fn


# ------------------------------------------------------------------ concept B
def wind_buoy():
    full = {p: (p, w, c) for p, w, c in E.wind_buoy()}
    order = ['steel spherical float', 'tail and ballast', 'lattice tower', 'vertical axis wind turbine', 'lantern',
             'topmark (can)']
    texts = [
        ('Spherical float', EXTRUDE, [E.NEW_PART + ' for the float: Revolve a half circle radius 250 (a 500 sphere).']),
        ('Tail and ballast', EXTRUDE, ['Sketch the tail Ø80 down 610 mm and a ballast disc Ø260 x 150. Extrude.']),
        ('Lattice tower', EXTRUDE, ['Three 16 x 16 legs on a 240 circle, 1050 high, with three rings. Extrude, Circular Pattern 3.']),
        ('Wind turbine', EXTRUDE, ['Three blades 120 x 240 on a 140 circle round a hub shaft, end plates Ø150.']),
        ('Lantern and topmark', CONSTRAIN, [NEW_ASSY + ' and save it as wind_buoy.iam. Place the parts, the lantern and '
                                            'a can topmark on top.']),
    ]
    out = []
    groups = [order[:1], order[:2], order[:3], order[:4], order]
    for i, (title, cmd, actions) in enumerate(texts):
        note = None
        if i == len(texts) - 1:
            note = ('Rejected for the final design: the turbine has bearings and blades that wear out at sea and need '
                    'servicing, the steel float must be painted to stop rust, and a wind turbine gives no power on calm '
                    'days, so a big battery is still needed.')
        out.append(step(title, cmd, actions, [full[p] for p in groups[i]], note=note))
    return out


STEPS = dict(esp2024_buoy=buoy_steps('red'), esp2024_buoy_green=buoy_steps('green'), esp2024_wind_buoy=wind_buoy)
for _d in E.SUBS:
    STEPS[E.sub_model_name(_d)] = sub_steps(_d)
for _p in E.PARTS:
    STEPS[E.part_model_name(_p)] = part_steps(_p)
