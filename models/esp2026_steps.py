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


# ------------------------------------------------------------------ the three-seat set
def seat_set():
    items = E.set_instances()
    stages = [
        (('beam_tube', 'leg', 'beam_collar', 'track_fitting', 'track_stud'), 'Beams and legs', PLACE,
         [NEW_ASSY + ' and save it as esp2026_seat_set.iam.',
          'Place beam_tube.ipt, right click and Place Grounded: the front tube, on the origin line, 330 mm up. Place '
          'the rear tube 330 mm behind it (Mate with offset).',
          'Place leg.ipt twice, 270 mm each side of the centre: Insert each bore on to its tube. Place beam_collar.ipt '
          'beside each leg boss. Place track_fitting.ipt and track_stud.ipt under each foot.'],
         'The legs stand on the aircraft seat tracks; the studs lock into the tracks every 25.4 mm.'),
        (('spreader', 'beam_end_cap', 'baggage_bar'), 'Spreaders, end caps and baggage bar', PATTERN,
         ['Place spreader.ipt on the tubes at x = -750 and Insert both bores. Pattern it: 4 along X, 500 mm apart.',
          'Place beam_end_cap.ipt in the four tube ends, and baggage_bar.ipt through the front struts of the legs.'],
         'The spreaders sit under the armrests, so each seat is 450 mm wide between the armrests.'),
        (('seat_diaphragm', 'seat_foam', 'seat_cover'), 'Seat pans and cushions', PATTERN,
         ['Place seat_diaphragm.ipt on the tubes of the middle seat, then seat_foam.ipt and seat_cover.ipt.',
          'Pattern the three parts: 3 along X, 500 mm apart, centred.'], None),
        (('back_shell', 'back_foam', 'back_cover', 'headrest', 'back_pivot_pin', 'end_pivot_pin'),
         'Backs and pivot pins', CONSTRAIN,
         ['Place the back sub-assembly (back shell, cushion, cover, head rest) for each seat.',
          'Insert back_pivot_pin.ipt through the two middle spreaders and end_pivot_pin.ipt through the end ones, '
          'through the lugs of the backs. Add an Angle constraint of 12 degrees for each back (upright).'],
         'Each back turns on the pins: upright at 12 degrees from vertical, reclined at 17.'),
        (('recline_bracket', 'recline_lock', 'recline_rod', 'lock_pin'), 'Recline locks', CONSTRAIN,
         ['For each seat: place recline_bracket.ipt on the front tube, recline_lock.ipt and recline_rod.ipt, and pin '
          'both ends with lock_pin.ipt.'], None),
        (('armrest', 'armrest_pad', 'armrest_pin', 'recline_button'), 'Armrests', PATTERN,
         ['Place armrest.ipt on the end spreader: Insert armrest_pin.ipt through the cheeks and the spreader. Add '
          'armrest_pad.ipt on top. Pattern: 4 along X, 500 mm apart.',
          'Place recline_button.ipt on the front of the three armrests to the right of each seat.'],
         'Each armrest lifts 90 degrees for access; the end ones let a passenger transfer from an aisle wheelchair.'),
        (('belt_anchor', 'belt_strap_buckle', 'belt_strap_adjust', 'buckle_body', 'buckle_lever', 'belt_tongue'),
         'Seat belts', CONTENT,
         ['Place the belt anchors on the spreaders (two per seat, M10 bolts from Content Center), then the belt '
          'webbing, buckle, lever and tongue for each seat.'], None),
        (('tray_table', 'tray_arm', 'tray_latch', 'ife_screen', 'usb_module', 'literature_pocket', 'vest_pouch', 'life_vest'),
         'Trays, screens, pockets and life vests', CONSTRAIN,
         ['Fit each back with its literature pocket, tray arms, tray, latch, screen and power module.',
          'Place a vest_pouch.ipt with its life_vest.ipt under each seat.',
          'Inspect tab > Interference > Analyze Interference upright, reclined, with the trays down and the armrests '
          'up: no parts overlap. Save.'],
         'Each seat now has everything the product design specification asks for.'),
    ]
    return staged(items, stages)


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
for _p in E.PARTS:
    STEPS[E.part_model_name(_p)] = part_steps(_p)
