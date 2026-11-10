"""Autodesk Inventor build steps for the ESP 2026 economy seat models (see models/esp2026.py).

Same format as models/inventor_steps.py. Every stage is made with the same CadQuery shapes as the finished
models, and tools/build_steps.py checks that the last stage matches the finished model.

Each part has its own steps (the features listed with it in esp2026.PARTS). The single seat and the three-seat
set are assemblies: their steps place the parts one group at a time, in the order they would be built.

The hub's models use Z up. Inventor's default is Y up, so the hub's XY plane (the floor) is Inventor's XZ Plane,
and the hub's XZ plane (looking at the front of the seats) is Inventor's XY Plane.
"""
import esp2026 as E
from esp2026 import box, NEW_ASSY, PLACE, CONSTRAIN, MIRROR, PATTERN, CONTENT, EXTRUDE


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


def staged(items, stages, name_of=lambda n: n):
    """Build an assembly a group at a time: stages are (keys, title, command, actions, note)."""
    out, keys = [], set()
    for ks, title, cmd, actions, note in stages:
        keys |= set(ks)
        out.append(step(title, cmd, actions, [(name_of(n), s, E.colour(k)) for n, k, s in items if k in keys], note=note))
    return out


# ------------------------------------------------------------------ the single seat
def single_seat():
    items = E.seat_items()
    stages = [
        (('seat_diaphragm', 'seat_foam', 'seat_cover'), 'Seat pan and cushion', PLACE,
         [NEW_ASSY + ' and save it as single_seat.iam.',
          'Place seat_diaphragm.ipt, right click and Place Grounded. In the set it sits on the beam tubes, 355 mm up.',
          'Place seat_foam.ipt and Mate its bottom to the top of the diaphragm. Place seat_cover.ipt over the foam: '
          'Mate the inside faces of the cover to the foam.'],
         'The seat height is the top of the cover at the front edge: 440 mm above the floor.'),
        (('back_shell',), 'Place the back shell', CONSTRAIN,
         ['Place back_shell.ipt. Constrain > Insert is not possible without the spreaders, so in this sub-assembly '
          'use Angle: 12 degrees between the back and the vertical, and Mate the pivot axis 420 mm aft and 390 mm up.'],
         'In the three-seat set the back pivots on the spreader pins. Suppress the Angle constraint to let it recline.'),
        (('back_foam', 'back_cover', 'headrest'), 'Back cushion and head rest', CONSTRAIN,
         ['Place back_foam.ipt in the open front of the shell (Mate the back face of the foam to the shell edge).',
          'Place back_cover.ipt over it, and headrest.ipt on top of the shell (Mate, then Flush the centre planes).'],
         'The head rest is fixed, as the brief asks: it sits 50 mm forward of the back cushion to meet the head.'),
        (('recline_bracket', 'recline_lock', 'recline_rod', 'lock_pin'), 'Recline lock', CONSTRAIN,
         ['Place recline_bracket.ipt under the front beam position, 204 mm right of the seat centre.',
          'Place recline_lock.ipt and recline_rod.ipt. Insert the rod in the bore of the lock (Mate axis to axis).',
          'Pin the front eye to the bracket and the rod eye to the back lever with lock_pin.ipt (Insert).'],
         'Pressing the recline button opens a valve in the lock; the passenger leans back and the rod slides in 9 mm.'),
        (('belt_anchor', 'belt_strap_buckle', 'belt_strap_adjust', 'buckle_body', 'buckle_lever', 'belt_tongue'),
         'Lap belt', CONSTRAIN,
         ['Place belt_anchor.ipt each side (Mirror Components for the left one).',
          'Place the two webbing halves, buckle_body.ipt with buckle_lever.ipt on top, and belt_tongue.ipt in the buckle slot.'],
         'A lift lever buckle: lift the lever and the tongue comes free. Anyone can open it with either hand, and the '
         'crew can open it from the aisle.'),
        (('tray_table', 'tray_arm', 'tray_latch', 'ife_screen', 'usb_module', 'literature_pocket'),
         'Fit out the back', CONSTRAIN,
         ['Place literature_pocket.ipt, the two tray_arm.ipt brackets and tray_table.ipt on the back of the shell '
          '(Insert the hinge stubs into the tray holes). Add an Angle constraint 0 to 78 degrees for the tray.',
          'Place tray_latch.ipt above the tray, ife_screen.ipt and usb_module.ipt at the top.'],
         'These serve the passenger in the row behind.'),
        (('vest_pouch', 'life_vest'), 'Life vest pouch', CONSTRAIN,
         ['Place vest_pouch.ipt under the seat (its top Mates to the bottom of the beam tubes) and life_vest.ipt inside it.',
          'Inspect tab > Interference > Analyze Interference: no parts should overlap. Save.'],
         'The vest is 305 x 305 x 50, as the brief says; the pouch is 316 x 336 x 56 inside.'),
    ]
    return staged(items, stages, lambda n: n.replace('seat 2 ', ''))


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


# ------------------------------------------------------------------ the three-seat set
def seat_set():
    """The top level assembly, built from the seven sub-assemblies (and the four back pivot pins)."""
    items = E.set_instances()
    def sub(n):
        if n.startswith('recline pivot pin'):
            return 'pins'
        return E.sub_of(n)
    stages = [
        ('frame', 'Place the frame', PLACE,
         [NEW_ASSY + ' and save it as esp2026_seat_set.iam.',
          'Place frame.iam (sub-assembly 1: legs, track fittings, beam tubes, collars, spreaders, end caps, baggage bar) '
          'and Place Grounded.'],
         'Build each sub-assembly first (see its own Build steps), then place them here. The frame is the base.'),
        ('seat_pan', 'Seat pans', PATTERN,
         ['Place seat_pan.iam (sub-assembly 2) on the beam tubes of the middle seat: Mate the underside of the '
          'diaphragm to the tops of the tubes and Flush its centre plane with the seat centre line.',
          'Pattern > Rectangular: 3 along X, 500 mm apart, centred.'], None),
        ('seat_back', 'Seat backs', CONSTRAIN,
         ['Place seat_back.iam (sub-assembly 3) for each seat. Line up the pivot lugs with the holes in the spreaders.',
          'Add an Angle constraint of 12 degrees between each back and the vertical (upright).'], None),
        ('pins', 'Back pivot pins', CONSTRAIN,
         ['Insert back_pivot_pin.ipt through the two middle spreaders and end_pivot_pin.ipt through the end ones, '
          'through the lugs of the backs.'],
         'Each back turns on these pins: upright at 12 degrees from vertical, reclined at 17.'),
        ('recline_lock', 'Recline locks', CONSTRAIN,
         ['Place recline_lock.iam (sub-assembly 4) for each seat: Mate the bracket to the underside of the front tube, '
          '204 mm right of the seat centre, and pin the rod eye to the lever on the back shell.'],
         'Pressing the recline button opens the lock; the passenger leans back and the rod slides in 9 mm.'),
        ('armrest', 'Armrests', PATTERN,
         ['Place armrest.iam (sub-assembly 5) on the first spreader: Insert its pivot pin through the spreader.',
          'Pattern: 4 along X, 500 mm apart. Suppress the button on the left hand armrest (it has none).'],
         'Each armrest lifts 90 degrees; the end ones let a passenger transfer from an aisle wheelchair.'),
        ('lap_belt', 'Lap belts', PATTERN,
         ['Place lap_belt.iam (sub-assembly 6) on the middle seat: bolt each anchor to its spreader (M10 bolts from '
          'Content Center). Pattern: 3 along X, 500 mm apart.'], None),
        ('life_vest', 'Life vest pouches', PATTERN,
         ['Place life_vest_pouch.iam (sub-assembly 7) under the middle seat: Mate its top to the underside of the '
          'beam tubes. Pattern: 3 along X, 500 mm apart.',
          'Inspect tab > Interference > Analyze Interference upright, reclined, with the trays down and the armrests '
          'up: no parts overlap. Save.'],
         'All 128 parts are now in place: 7 sub-assemblies plus the 4 pivot pins.'),
    ]
    out, done = [], set()
    for key, title, cmd, actions, note in stages:
        done.add(key)
        out.append(step(title, cmd, actions, [(n, s, E.colour(k)) for n, k, s in items if sub(n) in done], note=note))
    return out


# ------------------------------------------------------------------ concept B
def shell_seats():
    full = {p: (p, w, c) for p, w, c in E.shell_seats()}
    order = ['pedestal legs and track rails', 'box beam', 'fixed shells', 'sliding seat pans and cushions', 'tray tables (stowed)']
    texts = [
        ('Pedestal legs', EXTRUDE, [E.NEW_PART + ' for the two pedestal legs: 80 x 240 posts, 270 high, on 100 x 540 rails.']),
        ('Box beam', EXTRUDE, [E.NEW_PART + ' for the box beam: 160 x 90 section, 1520 long, on top of the legs.']),
        ('Fixed shells', EXTRUDE, [E.NEW_PART + ' for one shell (sides and a back 1150 high), then Rectangular Pattern 3 at 500.']),
        ('Sliding seat pans', EXTRUDE, ['Sketch the three seat pans 426 x 500 and Extrude 70 mm.']),
        ('Assemble the concept', CONSTRAIN, [NEW_ASSY + ' and save it as shell_seats.iam. Place the legs grounded, Mate '
                                             'the beam on top, then the shells, pans and trays.']),
    ]
    out = []
    for i, (title, cmd, actions) in enumerate(texts):
        note = None
        if i == len(texts) - 1:
            note = ('Rejected for the final design: the fixed shells weigh about 9.5 kg a seat (the brief allows 8), '
                    'cost more to make, and the shell sides make it harder for a passenger with access needs to slide across.')
        out.append(step(title, cmd, actions, [full[p] for p in order[:i + 1]], note=note))
    return out


STEPS = dict(esp2026_seat_set=seat_set, esp2026_single_seat=single_seat, esp2026_shell_seats=shell_seats)
for _d in E.SUBS:
    STEPS[E.sub_model_name(_d)] = sub_steps(_d)
for _p in E.PARTS:
    STEPS[E.part_model_name(_p)] = part_steps(_p)
