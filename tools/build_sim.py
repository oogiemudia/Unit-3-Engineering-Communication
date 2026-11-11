"""Write docs/sim/<model>.json for the Simulation tab: an Autodesk Inventor Dynamic Simulation of each moving
assembly, step by step, with the motion the viewer plays and the graphs it draws.

Only assemblies with parts that move get a Simulation tab. Single parts have the FEA tab instead.
Motion keys are (time s, value) pairs, eased between keys. Distances in mm, angles in degrees, CAD axes
(Z up). Run from the repository root:  python3 tools/build_sim.py
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'sim')
sys.path.insert(0, os.path.join(ROOT, 'models'))
import esp2023 as esp  # noqa: E402
import esp2026 as seat  # noqa: E402
import esp2024 as buoy_m  # noqa: E402
import esp2025 as pill  # noqa: E402

ENV = 'Environments tab > Begin panel > Dynamic Simulation'
SETTINGS = 'Dynamic Simulation tab > Manage panel > Simulation Settings'
JOINT = 'Dynamic Simulation tab > Joint panel > Insert Joint'
PLAYER = 'Dynamic Simulation tab > Manage panel > Simulation Player'
GRAPHER = 'Dynamic Simulation tab > Results panel > Output Grapher'


def step(view, title, command, actions, note=None):
    return dict(view=view, title=title, command=command, actions=actions, note=note)


def common_start(assembly):
    return [
        step('model', 'Open the Dynamic Simulation environment', ENV,
             ['Open %s in Inventor.' % assembly, 'Click the Environments tab, then Dynamic Simulation.'],
             'Dynamic Simulation works out how an assembly moves, and the forces and speeds as it moves.'),
        step('joints', 'Turn constraints into joints', SETTINGS,
             ['Click Simulation Settings and tick Automatically convert constraints to standard joints. Click OK.',
              'Open Standard Joints in the browser to see the joints Inventor made from your assembly constraints.'],
             'Parts held together with no movement between them become one rigid group, listed under Welded group.'),
    ]


def common_end(final_time, what):
    return [
        step('play', 'Run the simulation', PLAYER,
             ['In the Simulation Player set Final Time to %g s and Images to %d.' % (final_time, final_time * 50),
              'Click Run. The assembly moves and the timeline fills in.', 'Use the slider to scrub back and forth.'],
             'Press Play below to run the same motion here.'),
        step('graph', 'Plot the results', GRAPHER,
             ['Open the Output Grapher.', 'Under Standard Joints, tick %s.' % what,
              'The graph shows each value against time. Click on the graph to move the simulation to that moment.']),
        step('graph', 'Record a video', PLAYER,
             ['In the Simulation Player click Record (the red dot) and choose a file name and format.',
              'Click Run again. Inventor saves a video of the motion for your portfolio.'],
             'You can also export a moment to Stress Analysis (Export to FEA) to check a part at its highest load.'),
    ]


def ease_keys(points):
    return [[round(t, 3), round(v, 3)] for t, v in points]


CYL_STROKE = [(0, 0), (1, 0), (2.5, 20), (3.5, 20), (5, 0), (6, 0)]
SIMS = dict(
    pneumatic_cylinder=dict(
        duration=6,
        story='Air at 6 bar pushes the piston out 20 mm. When the air is let out, the spring pushes it back.',
        moving=['piston', 'piston rod', 'return spring'],
        motion=[
            dict(part='piston', kind='move', axis=[1, 0, 0], keys=ease_keys(CYL_STROKE)),
            dict(part='piston rod', kind='move', axis=[1, 0, 0], keys=ease_keys(CYL_STROKE)),
            dict(part='return spring', kind='stretch', axis=[1, 0, 0], anchor=70, length0=54,
                 keys=ease_keys([(t, 54 - s) for t, s in CYL_STROKE])),
        ],
        graph=[dict(name='Rod position', unit='mm', keys=ease_keys(CYL_STROKE)),
               dict(name='Spring force', unit='N', keys=ease_keys([(t, 20 + 0.8 * s) for t, s in CYL_STROKE])),
               dict(name='Air pressure', unit='bar', step=True, keys=[[0, 0], [1, 6], [3.5, 0], [6, 0]])],
        steps=lambda: common_start('pneumatic_cylinder.iam') + [
            step('joints', 'Check the sliding joint', JOINT,
                 ['Find the Prismatic joint between the barrel and the piston in Standard Joints.',
                  'If it is missing, click Insert Joint, choose Prismatic, pick the barrel bore and then the piston edge. Click OK.',
                  'The piston and rod should be one Welded group, so they move together.'],
                 'A prismatic joint lets a part slide along one line and nothing else: one degree of freedom.'),
            step('joints', 'Add the return spring', JOINT,
                 ['Click Insert Joint. Under Force Joints choose Spring / Damper / Jack.',
                  'Pick a point on the front face of the piston, then a point on the inside face of the front cap.',
                  'Stiffness 0.8 N/mm, Free Length 89 mm (the two points are 64 mm apart, so the spring already pushes 20 N when the piston is back). Click OK.'],
                 'Turn off the spring part itself (right click > Enabled) so it does not get in the way: the force joint does its job.'),
            step('motion', 'Drive the piston', 'Right click the Prismatic joint > Properties > dof 1 > Edit imposed motion',
                 ['Tick Enable imposed motion. Drive: Position.',
                  'Click the graph button to open the Input Grapher and enter the points: 0 mm at 1 s, 20 mm at 2.5 s, 20 mm at 3.5 s, 0 mm at 5 s.',
                  'Click OK twice.'],
                 'This stands in for the air: out stroke when the valve opens, back stroke when it closes.'),
        ] + common_end(6, 'the position of the Prismatic joint and the force in the spring')),
    bolted_joint=dict(
        duration=6,
        story='The nut is screwed up the bolt: 20 turns for 25 mm, because an M8 thread has a 1.25 mm pitch.',
        moving=['hex nut M8'],
        motion=[
            dict(part='hex nut M8', kind='move', axis=[0, 0, 1], keys=ease_keys([(0, -25), (0.5, -25), (4.5, 0), (6, 0)])),
            dict(part='hex nut M8', kind='turn', axis=[0, 0, 1], centre=[0, 0, 0],
                 keys=ease_keys([(0, 0), (0.5, 0), (4.5, 7200), (6, 7200)])),
        ],
        graph=[dict(name='Nut height', unit='mm', keys=ease_keys([(0, -25), (0.5, -25), (4.5, 0), (6, 0)])),
               dict(name='Turns', unit='', keys=ease_keys([(0, 0), (0.5, 0), (4.5, 20), (6, 20)]))],
        steps=lambda: common_start('bolted_joint.iam') + [
            step('joints', 'Make the nut screw onto the bolt', JOINT,
                 ['Delete the Insert constraint joint for the nut if Inventor made one.',
                  'Click Insert Joint and choose Cylindrical. Pick the bolt shank, then the nut bore. Click OK.',
                  'Then Insert Joint, Screw: pick the cylindrical joint, Pitch 1.25 mm. Click OK.'],
                 'A screw joint ties turning to moving: 1 turn moves the nut 1.25 mm along the bolt.'),
            step('motion', 'Turn the nut', 'Right click the Cylindrical joint > Properties > dof 1 (R) > Edit imposed motion',
                 ['Tick Enable imposed motion. Drive: Position.',
                  'In the Input Grapher: 0 degrees at 0.5 s and 7200 degrees (20 turns) at 4.5 s.', 'Click OK twice.']),
        ] + common_end(6, 'the position and the angle of the Cylindrical joint')),
    fit_pair=dict(
        duration=5,
        story='The pin slides down into the 20 H7 hole. With a clearance fit it goes in by hand.',
        moving=['pin (shaft 20 g6)'],
        motion=[dict(part='pin (shaft 20 g6)', kind='move', axis=[0, 0, 1], keys=ease_keys([(0, 50), (0.5, 50), (3, 0), (5, 0)]))],
        graph=[dict(name='Pin height', unit='mm', keys=ease_keys([(0, 50), (0.5, 50), (3, 0), (5, 0)])),
               dict(name='Pin speed', unit='mm/s', keys=ease_keys([(0, 0), (0.5, 0), (1.75, -30), (3, 0), (5, 0)]))],
        steps=lambda: common_start('fit_pair.iam') + [
            step('joints', 'Check the pin joint', JOINT,
                 ['Find the Cylindrical joint between the housing hole and the pin.',
                  'If it is missing, click Insert Joint, choose Cylindrical and pick the hole, then the pin. Click OK.'],
                 'A cylindrical joint allows two movements: sliding along the axis and turning about it.'),
            step('motion', 'Push the pin in', 'Right click the Cylindrical joint > Properties > dof 2 (T) > Edit imposed motion',
                 ['Tick Enable imposed motion. Drive: Position.',
                  'In the Input Grapher: 50 mm at 0.5 s and 0 mm at 3 s (fully home).', 'Click OK twice.']),
        ] + common_end(5, 'the position and the velocity of the Cylindrical joint')),
)



# ------------------------------------------------------------------ machine vice: the tommy bar closes the jaw
VICE_MOVE = [(0, 0), (0.5, 0), (6.5, -40), (8, -40)]           # moving jaw x, mm: the opening goes from 60 to 20
VICE_TURN = [(t, -x / 2 * 360) for t, x in VICE_MOVE]           # M16 x 2: 2 mm a turn, so 20 turns = 7200 degrees
_vice_jaw = ['moving jaw', 'moving jaw plate', 'jaw plate screw 3', 'jaw plate screw 4']
_vice_screw = ['lead screw', 'thrust collar', 'collar pin', 'tommy bar', 'handle ball 1', 'handle ball 2']
SIMS['machine_vice'] = dict(
    duration=8,
    story='Turning the tommy bar turns the lead screw in the end block. The screw cannot move along, so the moving jaw, '
          'which is the nut, slides 2 mm for every turn: 20 turns close the jaws from 60 mm to 20 mm.',
    moving=_vice_jaw + _vice_screw,
    motion=[dict(part=n, kind='move', axis=[1, 0, 0], keys=ease_keys(VICE_MOVE)) for n in _vice_jaw] +
           [dict(part=n, kind='turn', axis=[1, 0, 0], centre=[0, 0, 27], keys=ease_keys(VICE_TURN)) for n in _vice_screw],
    graph=[dict(name='Jaw opening', unit='mm', keys=ease_keys([(t, 60 + x) for t, x in VICE_MOVE])),
           dict(name='Screw turns', unit='', keys=ease_keys([(t, -x / 2) for t, x in VICE_MOVE]))],
    steps=lambda: common_start('machine_vice.iam') + [
        step('joints', 'Let the screw turn in the end block', JOINT,
             ['Find the joint between the end block bore and the screw journal. It should be a Revolution joint.',
              'If it is not, click Insert Joint, choose Revolution, pick the bore edge in the end block, then the journal edge on the screw. Click OK.',
              'The collar, pin, tommy bar and balls are fixed to the screw, so they are one Welded group with it.'],
             'A revolution joint lets a part turn about one axis and nothing else: one degree of freedom.'),
        step('joints', 'Let the jaw slide on the rails', JOINT,
             ['Check for a Prismatic joint between the body rails and the moving jaw.',
              'If it is missing, Insert Joint, Prismatic: pick a rail top face, then the underside of the jaw head. Click OK.',
              'The jaw plate and its two screws are one Welded group with the moving jaw.']),
        step('joints', 'Link the screw to the jaw', JOINT,
             ['Click Insert Joint. Under Rolling Joints choose Screw.',
              'Pick the cylindrical face of the screw thread, then the threaded hole in the moving jaw.',
              'Pitch 2 mm. Click OK.'],
             'The screw joint ties turning to moving: one turn of the screw moves the jaw 2 mm.'),
        step('motion', 'Turn the tommy bar', 'Right click the Revolution joint > Properties > dof 1 (R) > Edit imposed motion',
             ['Tick Enable imposed motion. Drive: Position.',
              'In the Input Grapher: 0 degrees at 0.5 s and 7200 degrees (20 turns) at 6.5 s.', 'Click OK twice.']),
    ] + common_end(8, 'the angle of the Revolution joint and the position of the Prismatic joint'))


# ------------------------------------------------------------------ ESP 2023 lock gates
def smooth(t, t0, t1):
    u = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    return u * u * (3 - 2 * u)


def esp_gate_sim():
    """The paddles lift to let the lock empty, then both leaves open, wait and shut again, each on its own
    timetable (the brief asks for gates that work independently), and the paddles drop. The real gates take about
    60 s each way; the simulation runs 10 times faster."""
    D, OPEN, LIFT = 20, esp.OPEN_DEG, esp.PADDLE_LIFT
    times = {-1: (3.5, 9.5, 11.5, 17.5), 1: (3.0, 9.0, 11.0, 17.0)}
    paddle = ease_keys([(0, 0), (0.5, 0), (2.0, LIFT), (18.0, LIFT), (19.5, 0), (D, 0)])

    def angle(side, t):
        a, b, c, d = times[side]
        return OPEN * (smooth(t, a, b) - smooth(t, c, d))

    names = [n for n, s, c in esp.lock_gates(0)]
    motion, graph = [], []
    for side in (-1, 1):
        n = 'left' if side < 0 else 'right'
        sg = 1 if side < 0 else -1          # the left leaf turns anticlockwise seen from above, the right clockwise
        a, b, c, d = times[side]
        keys = ease_keys([(0, 0), (a, 0), (b, sg * OPEN), (c, sg * OPEN), (d, 0), (D, 0)])
        piv = [side * esp.PIV, 0, 0]
        mine = [p for p in names if p.startswith(n + ' ') or (p == 'mitre seal' and side < 0)]
        for p in mine:
            g = esp.group_of(p)
            if g == 'paddle':
                motion.append(dict(part=p, kind='move', axis=[0, 0, 1], keys=paddle))
            if g in ('leaf', 'paddle'):
                motion.append(dict(part=p, kind='turn', axis=[0, 0, 1], centre=piv, keys=keys))
        # the actuator follows the leaf: its body swings about the rear pivot and the rod slides out of it
        w, g0, d0 = esp.actuator_geometry(side, 0)
        a0 = math.atan2(g0[1] - w[1], g0[0] - w[0])
        u0 = [(g0[0] - w[0]) / d0, (g0[1] - w[1]) / d0, 0]
        ts = [round(k * 0.1, 2) for k in range(D * 10 + 1)]
        swing, slide = [], []
        for t in ts:
            ww, g, dd = esp.actuator_geometry(side, angle(side, t))
            at = math.atan2(g[1] - ww[1], g[0] - ww[0])
            swing.append((t, math.degrees(at - a0)))
            slide.append((t, dd - d0))
        for p in mine:
            g = esp.group_of(p)
            if g == 'body':
                motion.append(dict(part=p, kind='turn', axis=[0, 0, 1], centre=list(w), keys=ease_keys(swing), lin=True))
            if g == 'rod':
                motion.append(dict(part=p, kind='move', axis=u0, keys=ease_keys(slide), lin=True))
                motion.append(dict(part=p, kind='turn', axis=[0, 0, 1], centre=list(w), keys=ease_keys(swing), lin=True))
        graph.append(dict(name='%s leaf angle' % n.capitalize(), unit='deg', keys=[[t, abs(v)] for t, v in keys]))
        if side > 0:
            graph.append(dict(name='Right actuator length', unit='mm', lin=True,
                              keys=ease_keys([(t, d0 + v) for t, v in slide][::5])))
    graph.append(dict(name='Paddle opening', unit='mm', keys=paddle))
    moving = sorted({m['part'] for m in motion})
    w, g0, d0 = esp.actuator_geometry(1, 0)
    _, g1, d1 = esp.actuator_geometry(1, OPEN)
    steps = common_start('esp2023_lock_gates.iam') + [
        step('joints', 'Check the hinge joints', JOINT,
             ['In Standard Joints find the Revolution joint for each leaf: the pintle bush on the bottom pintle, and the '
              'heel post journal in the collar bush.',
              'If a leaf has two joints (one at the top and one at the bottom) Inventor shows the second as redundant. '
              'Keep one Revolution joint per leaf, on the pivot axis, and delete the other.',
              'Every part of the leaf sub-assembly (frame, fenders, seals, walkway, paddle guides) should be one Welded group.'],
             'A revolution joint lets a part turn about one axis and nothing else: one degree of freedom.'),
        step('joints', 'Join the actuators', JOINT,
             ['Each actuator needs three joints. Insert Joint, Revolution: the actuator body rear eye on the pivot pin.',
              'Insert Joint, Cylindrical: the rod inside the body bore, so the rod can slide out.',
              'Insert Joint, Revolution: the rod end eye on the front pivot pin in the leaf bracket.'],
             'The rod end has a spherical bearing, so the actuator can follow the leaf as it swings.'),
        step('joints', 'Join the paddles', JOINT,
             ['Insert Joint, Prismatic: the paddle door sliding up the paddle guides. The paddle rod is welded to the door.',
              'Right click the joint > Properties > dof 1 (T) > Edit imposed motion: 0 at 0.5 s, %d mm at 2 s, hold, back '
              'to 0 at 19.5 s.' % LIFT],
             'The paddles let the lock empty through the gates first: the gates can only open when the water is level on both sides.'),
        step('motion', 'Drive the leaves', 'Right click a leaf Revolution joint > Properties > dof 1 (R) > Edit imposed motion',
             ['Tick Enable imposed motion. Drive: Position.',
              'Right leaf, in the Input Grapher: 0 degrees at 3 s, -71.6 degrees (fully open) at 9 s, hold to 11 s, back to 0 at 17 s.',
              'Left leaf: the same, but +71.6 degrees, starting half a second later, so you can see the leaves work independently.',
              'Click OK twice.'],
             'The real gates take about 60 s to open. This simulation runs 10 times faster. '
             'Each leaf turns %.1f degrees, from the mitre (1 in 3) into its recess in the lock wall.' % OPEN),
        step('motion', 'Check the actuator stroke', JOINT,
             ['Right click the actuator Cylindrical joint > Properties and look at dof 2 (T): Inventor works out how far the rod '
              'slides as the leaf turns.',
              'Pin to pin length: %.0f mm with the gate shut and %.0f mm with it open, a stroke of %.0f mm.' % (d0, d1, d0 - d1),
              'Check the rod never pulls out of the body: at full length %.0f mm of the rod is still inside.' % (esp.ACT_BODY - (d0 - esp.ROD_LEN))],
             'Choose an actuator with at least this stroke. A 1300 mm stroke electric actuator gives some spare.'),
    ] + common_end(D, 'the angle of each leaf Revolution joint, the position of the actuator Cylindrical joint and the paddle Prismatic joint')
    return dict(duration=D,
                story='The paddles lift to empty the lock through the gates, then the two leaves open into their recesses '
                      'and shut again, each driven by its own electric actuator in its inspection chamber, and the paddles '
                      'drop. Real time is about 60 s for each leaf; this runs 10 times faster.',
                moving=moving, motion=motion, graph=graph, steps=steps)


SIMS['esp2023_lock_gates'] = esp_gate_sim()
FOLDER = {'esp2023_lock_gates': 'ESP 2023'}


# ------------------------------------------------------------------ ESP 2026 economy three-seat set
def esp_seat_sim():
    """Each back reclines 5 degrees on its recline lock and comes back up (the three seats one after another, as
    each passenger is free to choose), then the aisle armrests lift 90 degrees for access and drop, then the tray
    tables on the backs fold down level and stow."""
    D, R, UP, TRAY = 20, seat.RECLINE, seat.ARM_UP, seat.TRAY_DEPLOY
    rec_t = [(0.5, 2.5, 5.5, 7.5), (1.0, 3.0, 6.0, 8.0), (1.5, 3.5, 6.5, 8.5)]
    arm_t = {3: (9.0, 10.5, 12.0, 13.5), 4: (9.0, 10.5, 12.0, 13.5)}
    tray_t = (14.0, 15.8, 17.6, 19.4)

    def prof(t, a, b, c, d, v):
        return v * (smooth(t, a, b) - smooth(t, c, d))

    def keys4(a, b, c, d, v):
        return ease_keys([(0, 0), (a, 0), (b, v), (c, v), (d, 0), (D, 0)])

    names = [n for n, s_, c in seat.seat_set()]
    motion, graph = [], []
    ts = [round(k * 0.1, 2) for k in range(D * 10 + 1)]
    for i, sx in enumerate(seat.SEATS):
        n = i + 1
        pre = 'seat %d ' % n
        a, b, c, d = rec_t[i]
        back_keys = keys4(a, b, c, d, -R)
        piv = [sx, seat.PIV[0], seat.PIV[1]]
        hinge = list(seat.back_point((0, seat.TRAY_HINGE[0], seat.TRAY_HINGE[1]), sx))
        anchor, r0, L0, ang0 = seat.lock_line(0)
        lock_c = [sx + seat.LOCK_X, anchor[0], anchor[1]]
        u0 = [0, math.cos(math.radians(ang0)), math.sin(math.radians(ang0))]
        swing, slide = [], []
        for t in ts:
            _, _, L, ang = seat.lock_line(prof(t, a, b, c, d, R))
            swing.append((t, ang - ang0))
            slide.append((t, L - L0))
        for p in names:
            if not p.startswith(pre):
                continue
            g = seat.group_of(p)
            if g == 'tray':
                motion.append(dict(part=p, kind='turn', axis=[1, 0, 0], centre=hinge, keys=keys4(*tray_t, -TRAY)))
            if g in ('back', 'tray'):
                motion.append(dict(part=p, kind='turn', axis=[1, 0, 0], centre=piv, keys=back_keys))
            if g == 'rod':
                motion.append(dict(part=p, kind='move', axis=u0, keys=ease_keys(slide), lin=True))
            if g in ('rod', 'lock'):
                motion.append(dict(part=p, kind='turn', axis=[1, 0, 0], centre=lock_c, keys=ease_keys(swing), lin=True))
        if n == 2:
            graph.append(dict(name='Seat 2 back angle from vertical', unit='deg',
                              keys=[[t, seat.BACK_ANGLE - v] for t, v in back_keys]))
            graph.append(dict(name='Seat 2 recline lock length', unit='mm', lin=True,
                              keys=ease_keys([(t, L0 + v) for t, v in slide][::5])))
    for k, x in enumerate(seat.SPREADERS, 1):
        if k not in arm_t:
            continue
        keys = keys4(*arm_t[k], -UP)
        for p in names:
            if p in ('armrest %d' % k, 'armrest pad %d' % k, 'armrest pin %d' % k, 'recline button %d' % (k - 1)):
                motion.append(dict(part=p, kind='turn', axis=[1, 0, 0], centre=[x, seat.ARM_PIV[0], seat.ARM_PIV[1]], keys=keys))
        if k == 4:
            graph.append(dict(name='Aisle armrest angle', unit='deg', keys=[[t, -v] for t, v in keys]))
    graph.append(dict(name='Tray table angle', unit='deg', keys=[[t, -v] for t, v in keys4(*tray_t, -TRAY)]))
    moving = sorted({m['part'] for m in motion})
    _, _, L0, _ = seat.lock_line(0)
    _, _, L1, _ = seat.lock_line(R)
    steps = common_start('esp2026_seat_set.iam') + [
        step('joints', 'Check the recline joints', JOINT,
             ['In Standard Joints find the Revolution joint for each back: the back lugs on the recline pivot pins.',
              'Every part fixed to a back (shell, cushion, cover, head rest, screen, power module, pocket, tray arms, '
              'latch) should be in one Welded group with it.'],
             'A revolution joint lets the back turn about the pivot axis and nothing else: one degree of freedom.'),
        step('joints', 'Join the recline locks', JOINT,
             ['Each lock needs three joints. Insert Joint, Revolution: the lock eye on the front pin in the bracket.',
              'Insert Joint, Cylindrical: the rod in the bore of the lock, so it can slide.',
              'Insert Joint, Revolution: the rod eye on the rear pin in the back lever.'],
             'Locked, the hydraulic valve stops the rod sliding, so the back is held. The recline button opens the valve.'),
        step('joints', 'Join the armrests and trays', JOINT,
             ['Insert Joint, Revolution: each armrest on its pivot pin.',
              'Insert Joint, Revolution: each tray table on its hinge stubs.'], None),
        step('motion', 'Drive the backs', 'Right click a back Revolution joint > Properties > dof 1 (R) > Edit imposed motion',
             ['Tick Enable imposed motion. Drive: Position.',
              'Seat 1: 0 at 0.5 s, %g degrees (fully reclined) at 2.5 s, hold to 5.5 s, back to 0 at 7.5 s.' % R,
              'Seats 2 and 3: the same, half a second and a second later: each passenger chooses for themselves.'],
             'The back reclines from 12 to %d degrees from vertical: %d degrees of recline, inside the 3 to 6 the brief allows.' % (
                 seat.BACK_ANGLE + R, R)),
        step('motion', 'Check the recline lock stroke', JOINT,
             ['Right click a lock Cylindrical joint > Properties and look at dof 2 (T): Inventor works out how far the rod '
              'slides as the back reclines.',
              'Pin to pin: %.1f mm upright, %.1f mm reclined, a stroke of %.1f mm.' % (L0, L1, L0 - L1)],
             'Choose a lock with at least this stroke: a 20 mm stroke lock leaves room to spare.'),
        step('motion', 'Lift the armrests, lower the trays', 'Edit imposed motion on the armrest and tray joints',
             ['Aisle armrests: 0 at 9 s, 90 degrees up at 10.5 s, hold, down again by 13.5 s.',
              'Trays: 0 at 14 s, %d degrees (level) at 15.8 s, hold, stowed again by 19.4 s.' % TRAY,
              'Click OK twice.'],
             'The armrest lifts clear of the seat, so a passenger can slide across from an aisle wheelchair.'),
    ] + common_end(D, 'the angle of each back, lock and armrest joint, the position of the lock Cylindrical joints and the tray angle')
    return dict(duration=D,
                story='Each back reclines 5 degrees and comes back up, one seat after another; the aisle armrests lift '
                      '90 degrees for access; then the tray tables fold down level and stow again.',
                moving=moving, motion=motion, graph=graph, steps=steps)


SIMS['esp2026_seat_set'] = esp_seat_sim()
FOLDER['esp2026_seat_set'] = 'ESP 2026'


# ------------------------------------------------------------------ ESP 2024 harbour buoy
def esp_buoy_sim():
    """Waves roll the buoy about its centre of gravity and lift it up and down; the load pin feels the chain pull
    rise and fall with each wave. Then the chain breaks below the second link: the pull falls to nothing, the
    control unit raises the alert, the buoy rises as the chain's weight comes off, and it drifts away with the
    tide while the tracker reports where it is."""
    D, T, BREAK = 16, 3.0, 8.0
    moored, free = buoy_m.float_line(extra=buoy_m.CHAIN_LOAD), buoy_m.float_line()
    BUOY_LIFT, BUOY_ZG = moored['h'] - free['h'], moored['zg']
    pull0 = buoy_m.CHAIN_LOAD * 9.81 / 1000
    ts = [round(k * 0.1, 2) for k in range(D * 10 + 1)]

    def smooth01(t, a, b):
        return smooth(t, a, b)

    roll = [(t, (10 if t < BREAK else 10 - 4 * smooth01(t, BREAK, BREAK + 4)) * math.sin(2 * math.pi * t / T)) for t in ts]
    heave = [(t, 40 * math.sin(2 * math.pi * t / T - 1.2) + BUOY_LIFT * smooth01(t, BREAK, BREAK + 2)) for t in ts]
    drift = [(t, 900 * smooth01(t, BREAK + 1, D)) for t in ts]
    fall = [(t, -900 * smooth01(t, BREAK, BREAK + 1.2)) for t in ts]
    pull = [(t, 0.0 if t >= BREAK else round(pull0 + 0.45 * max(0.0, math.sin(2 * math.pi * t / T - 1.2)), 3)) for t in ts]
    names = [n for n, s_, c in buoy_m.buoy()]
    lost = ['chain link 3', 'chain link 4']
    motion = []
    for p in names:
        if p in lost:
            motion.append(dict(part=p, kind='move', axis=[0, 0, 1], keys=ease_keys(fall), lin=True))
            motion.append(dict(part=p, kind='turn', axis=[0, 1, 0], centre=[0, 0, BUOY_ZG], keys=ease_keys(
                [(t, v if t < BREAK else roll[int(BREAK * 10)][1]) for t, v in roll]), lin=True))
            continue
        motion.append(dict(part=p, kind='turn', axis=[0, 1, 0], centre=[0, 0, BUOY_ZG], keys=ease_keys(roll), lin=True))
        motion.append(dict(part=p, kind='move', axis=[0, 0, 1], keys=ease_keys(heave), lin=True))
        motion.append(dict(part=p, kind='move', axis=[1, 0, 0], keys=ease_keys(drift), lin=True))
    graph = [dict(name='Roll angle', unit='deg', lin=True, keys=ease_keys(roll[::2])),
             dict(name='Load pin pull', unit='kN', lin=True, keys=ease_keys(pull[::2])),
             dict(name='Distance from its mooring', unit='m', lin=True, keys=ease_keys([(t, v / 1000) for t, v in drift[::4]]))]
    steps = common_start('esp2024_buoy.iam') + [
        step('joints', 'Free the buoy', JOINT,
             ['In Standard Joints, every part of the buoy above the broken link is one Welded group: the buoy moves as one body.',
              'Delete the grounded constraint on the float and Insert Joint > Spatial (6 degrees of freedom) between the '
              'float and the ground, so the buoy can roll, heave and drift.'],
             'Inventor has no sea, so the wave motion is put in as imposed motion, from the roll and heave worked out on '
             'the calculation sheet.'),
        step('joints', 'Join the chain', JOINT,
             ['Insert Joint, Spherical (ball) between the shackle and the swivel and between each pair of links.',
              'Chain links 3 and 4 get their own Spatial joint, so they can fall away when the chain breaks.'], None),
        step('motion', 'Roll and heave in the waves', 'Right click the Spatial joint > Properties > Edit imposed motion',
             ['dof 5 (rotation about Y): enable imposed motion, Position, a sine wave of 10 degrees amplitude and a 3 s '
              'period (use the Input Grapher: Sine).',
              'dof 3 (translation in Z): a sine wave of 40 mm amplitude, the same period.'],
             'The buoy rolls about its centre of gravity, %d mm below the waterline. A GM of %d mm brings it '
             'back upright every time.' % (-BUOY_ZG, moored['GM'])),
        step('motion', 'Break the chain at 8 s', 'Dynamic Simulation tab > Joint panel > Insert Joint (suppress at 8 s)',
             ['Suppress the joint between chain links 2 and 3 at 8 s (Construct, then right click > Suppress at time).',
              'Links 3 and 4 fall away. Add imposed motion on dof 3: the buoy rises %.0f mm as the weight of the hanging '
              'chain comes off, then dof 1 (X): it drifts 0.9 m with the tide by 16 s.' % BUOY_LIFT],
             'At the moment the chain breaks the load pin reads zero. The control unit sees this and sends an alert with '
             'the GNSS position at once, then reports the position every minute while the buoy drifts.'),
    ] + common_end(D, 'the rotation of the Spatial joint, the force in the shackle joint (the load pin) and the X position')
    return dict(duration=D,
                story='Waves roll the buoy up to 10 degrees and lift it up and down; the load pin feels each pull of the '
                      'chain. At 8 s the chain breaks: the pull falls to zero, the alert goes out, the buoy rises and '
                      'drifts off with the tide while the tracker follows it.',
                moving=sorted(names), motion=motion, graph=graph, steps=steps)


SIMS['esp2024_buoy'] = esp_buoy_sim()
FOLDER['esp2024_buoy'] = 'ESP 2024'


# ------------------------------------------------------------------ ESP 2025 automated pill dispenser
def esp_pill_sim():
    """A dose: the alarm sounds and the light flashes; the patient presses PRESS HERE; the motor turns the worm four
    times, the drive gear four teeth and the carousel one step of 12 degrees, so the next compartment drops its pills
    down the chute; the alarm stops. The patient pulls the drawer out, takes the pills and pushes it back. Then the
    pharmacist turns the key (the cam turns 90 degrees), opens the lid to refill and closes and locks it again."""
    D = 20
    STEP = pill.SEG
    TURNS = STEP / (360 / pill.GEAR_N)
    t_press, t_turn = (3.0, 3.2, 3.4), (3.4, 5.0)
    drawer_t, cam_t, lid_t = (6.0, 7.5, 9.0, 10.5), (11.0, 12.0, 18.0, 19.0), (12.2, 14.0, 16.0, 17.8)
    a = math.radians(pill.LOCK_ANG)
    lock_c = [87 * math.cos(a), 87 * math.sin(a), pill.LOCK_Z]
    lock_ax = [round(-math.cos(a), 5), round(-math.sin(a), 5), 0]   # the inward axis, as pill.cam_turn
    hinge = [0, pill.HINGE[0], pill.HINGE[1]]
    worm_c = [0, pill.WORM_Y, pill.WORM_ZC]

    def hold(a_, b_, c_, d_, v):
        return ease_keys([(0, 0), (a_, 0), (b_, v), (c_, v), (d_, 0), (D, 0)])

    carousel = ease_keys([(0, 0), (t_turn[0], 0), (t_turn[1], STEP), (D, STEP)])
    worm = ease_keys([(0, 0), (t_turn[0], 0), (t_turn[1], 360 * TURNS), (D, 360 * TURNS)])
    button = ease_keys([(0, 0), (t_press[0], 0), (t_press[1], -0.8), (t_press[2], 0), (D, 0)])
    drawer = hold(*drawer_t, -35)
    cam = hold(*cam_t, 90)
    lid = hold(*lid_t, -100)
    motion = []
    for p in pill.CAROUSEL_PARTS:
        motion.append(dict(part=p, kind='turn', axis=[0, 0, 1], centre=[0, 0, 0], keys=carousel))
    motion.append(dict(part='worm', kind='turn', axis=[1, 0, 0], centre=worm_c, keys=worm))
    motion.append(dict(part='PRESS HERE button', kind='move', axis=[0, 0, 1], keys=button))
    for p in ('dispensing drawer', 'drawer seal'):
        motion.append(dict(part=p, kind='move', axis=[0, 1, 0], keys=drawer))
    motion.append(dict(part='lock cam', kind='turn', axis=lock_ax, centre=lock_c, keys=cam))
    for p in pill.LID_PARTS:
        motion.append(dict(part=p, kind='turn', axis=[1, 0, 0], centre=hinge, keys=lid))
    alarm = [(0, 0), (1.0, 0), (1.01, 1), (5.0, 1), (5.01, 0), (D, 0)]
    graph = [dict(name='Alarm and flashing light (1 = on)', unit='', lin=True, keys=ease_keys(alarm)),
             dict(name='Carousel angle', unit='deg', keys=carousel),
             dict(name='Drawer pulled out', unit='mm', keys=[[t, -v] for t, v in drawer]),
             dict(name='Lid angle', unit='deg', keys=[[t, -v] for t, v in lid])]
    moving = sorted({m['part'] for m in motion})
    steps = common_start('esp2025_dispenser.iam') + [
        step('joints', 'Check the carousel and drive joints', JOINT,
             ['In Standard Joints find the Revolution joint of the carousel (its hub in the deck) and of the worm (on the '
              'motor shaft). The drive gear is in one Welded group with the carousel.',
              'Insert Joint > 3D Contact or Worm Gear: pick the worm and the drive gear, ratio %d:1.' % pill.GEAR_N],
             'A worm gear joint ties the two together: %d turns of the worm move the carousel %d degrees.' % (TURNS, STEP)),
        step('joints', 'Join the button, drawer, cam and lid', JOINT,
             ['Insert Joint, Prismatic: the PRESS HERE button in its hole, and the drawer in its opening.',
              'Insert Joint, Revolution: the lock cam on the lock axis, and the lid on the hinge pin.'], None),
        step('motion', 'The alarm and the button', 'Right click the button Prismatic joint > Properties > Edit imposed motion',
             ['The alarm and the light are switched by the program, not by a joint: they run from 1 s until the drop '
              'sensors see the pills (shown on the graph).',
              'Button: 0 at 3 s, pressed 0.8 mm at 3.2 s, back at 3.4 s.'],
             'The alarm keeps sounding until the pills have been dispensed, as the brief asks.'),
        step('motion', 'Turn one dose', 'Right click the worm Revolution joint > Properties > Edit imposed motion',
             ['Worm: 0 at 3.4 s, %d degrees (%d turns) at 5 s.' % (360 * TURNS, TURNS),
              'The worm gear joint turns the carousel %d degrees: the next compartment is over the drop hole.' % STEP],
             'The self-locking worm holds the carousel still between doses.'),
        step('motion', 'Take the pills', 'Edit imposed motion on the drawer Prismatic joint',
             ['Drawer: 0 at 6 s, 35 mm out at 7.5 s, hold to 9 s, back in by 10.5 s.'], None),
        step('motion', 'Pharmacy refill', 'Edit imposed motion on the cam and lid Revolution joints',
             ['Cam: 0 at 11 s, 90 degrees (unlocked) at 12 s, hold, back to 0 (locked) by 19 s.',
              'Lid: 0 at 12.2 s, 100 degrees open at 14 s, hold to 16 s, shut by 17.8 s. Click OK.'],
             'Only the pharmacy key turns the cam; with the cam at 0 the lid catch cannot lift.'),
    ] + common_end(D, 'the angle of the carousel and lid joints and the position of the drawer joint')
    return dict(duration=D,
                story='The alarm sounds and the light flashes; the patient presses PRESS HERE and the carousel turns one '
                      'step, dropping the next dose into the drawer. The drawer is pulled out and pushed back. Then the '
                      'pharmacist unlocks the lid with the key, opens it to refill and locks it again.',
                moving=moving, motion=motion, graph=graph, steps=steps)


SIMS['esp2025_dispenser'] = esp_pill_sim()
FOLDER['esp2025_dispenser'] = 'ESP 2025'


def build():
    for name, s in SIMS.items():
        steps = s['steps']() if callable(s['steps']) else s['steps']
        out = dict(name=name, duration=s['duration'], story=s['story'], moving=s['moving'], motion=s['motion'],
                   graph=s['graph'], steps=steps)
        out_dir = os.path.join(ROOT, 'docs', FOLDER[name], 'sim') if name in FOLDER else OUT
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name + '.json'), 'w') as f:
            json.dump(out, f, indent=1)
        print(name, len(out['steps']), 'steps')


if __name__ == '__main__':
    build()
