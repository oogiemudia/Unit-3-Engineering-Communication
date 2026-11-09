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


# ------------------------------------------------------------------ ESP 2023 lock gates
def smooth(t, t0, t1):
    u = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    return u * u * (3 - 2 * u)


def esp_gate_sim():
    """Both leaves open, wait, then shut again, each on its own timetable (the brief asks for gates that work
    independently). The real gates take about 60 s each way; the simulation runs 10 times faster."""
    D, OPEN = 16, esp.OPEN_DEG
    times = {-1: (1.5, 7.5, 9.5, 15.5), 1: (1.0, 7.0, 9.0, 15.0)}

    def angle(side, t):
        a, b, c, d = times[side]
        return OPEN * (smooth(t, a, b) - smooth(t, c, d))

    motion, graph = [], []
    for side in (-1, 1):
        n = 'left' if side < 0 else 'right'
        sg = 1 if side < 0 else -1          # the left leaf turns anticlockwise seen from above, the right clockwise
        a, b, c, d = times[side]
        keys = ease_keys([(0, 0), (a, 0), (b, sg * OPEN), (c, sg * OPEN), (d, 0), (D, 0)])
        piv = [side * esp.PIV, 0, 0]
        leaf = (['%s gate leaf' % n, '%s oak fenders' % n, '%s walkway and handrail' % n, '%s cill seal' % n, '%s heel seal' % n]
            + (['mitre seal'] if side < 0 else []))
        for p in leaf:
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
        motion.append(dict(part='%s actuator body' % n, kind='turn', axis=[0, 0, 1], centre=list(w), keys=ease_keys(swing), lin=True))
        motion.append(dict(part='%s actuator rod' % n, kind='move', axis=u0, keys=ease_keys(slide), lin=True))
        motion.append(dict(part='%s actuator rod' % n, kind='turn', axis=[0, 0, 1], centre=list(w), keys=ease_keys(swing), lin=True))
        graph.append(dict(name='%s leaf angle' % n.capitalize(), unit='deg', keys=[[t, abs(v)] for t, v in keys]))
        if side > 0:
            graph.append(dict(name='Right actuator length', unit='mm', lin=True,
                              keys=ease_keys([(t, d0 + v) for t, v in slide][::5])))
    moving = sorted({m['part'] for m in motion})
    w, g0, d0 = esp.actuator_geometry(1, 0)
    _, g1, d1 = esp.actuator_geometry(1, OPEN)
    steps = common_start('esp2023_lock_gates.iam') + [
        step('joints', 'Check the hinge joints', JOINT,
             ['In Standard Joints find the Revolution joint for each leaf: the heel post journal in the anchor collar, '
              'and the heel post bore on the bottom pintle.',
              'If a leaf has two joints (one at the top and one at the bottom) Inventor shows the second as redundant. '
              'Keep one Revolution joint per leaf, on the pivot axis, and delete the other.',
              'Each leaf, with its fenders, seals and walkway, should be one Welded group.'],
             'A revolution joint lets a part turn about one axis and nothing else: one degree of freedom.'),
        step('joints', 'Join the actuators', JOINT,
             ['Each actuator needs three joints. Insert Joint, Revolution: the actuator body rear pivot on the plinth axis.',
              'Insert Joint, Cylindrical: the rod inside the body bore, so the rod can slide out.',
              'Insert Joint, Spherical: the rod eye centre on the leaf bracket.'],
             'The rod eye is a spherical bearing, so the actuator can follow the leaf as it swings.'),
        step('motion', 'Drive the leaves', 'Right click a leaf Revolution joint > Properties > dof 1 (R) > Edit imposed motion',
             ['Tick Enable imposed motion. Drive: Position.',
              'Right leaf, in the Input Grapher: 0 degrees at 1 s, -71.6 degrees (fully open) at 7 s, hold to 9 s, back to 0 at 15 s.',
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
    ] + common_end(D, 'the angle of each leaf Revolution joint and the position and force of the actuator Cylindrical joint')
    return dict(duration=D,
                story='The two leaves open into their recesses and shut again, each driven by its own electric actuator '
                      'in the inspection chamber. Real time is about 60 s each way; this runs 10 times faster.',
                moving=moving, motion=motion, graph=graph, steps=steps)


SIMS['esp2023_lock_gates'] = esp_gate_sim()
FOLDER = {'esp2023_lock_gates': 'ESP 2023'}


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
