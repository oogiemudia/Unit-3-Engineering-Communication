"""Load cases for the FEA tab: which part is analysed, its material, where it is held and how it is loaded.

Each case is analysed with a linear static solve (tools/build_fea.py: gmsh tetrahedral mesh, quadratic
elements, scikit-fem). The same set-up is written as the Autodesk Inventor Stress Analysis steps in the
viewer, so learners can repeat the study in Inventor and compare their answers.

Faces are picked with a test on a small description of each face:
  t  type: 'PLANE', 'CYLINDER', 'CONE', ...
  c  centre of the face (x, y, z), mm
  n  outward normal at the centre (planar faces), else None
  r  radius (cylindrical faces), else None
  a  area, mm2
Units: mm, N, MPa.
"""

STEEL = dict(name='Steel', E=210000, nu=0.30, yield_strength=207)
ALUMINIUM = dict(name='Aluminum 6061', E=68900, nu=0.33, yield_strength=275)
BRASS = dict(name='Brass', E=100000, nu=0.34, yield_strength=200)

near = lambda a, b, tol=0.05: abs(a - b) < tol


def plane(axis, value, sign=None):
    """A planar face lying on axis = value; sign picks the outward normal direction if given."""
    k = 'xyz'.index(axis)

    def test(f):
        if f['t'] != 'PLANE' or not near(f['c'][k], value) or abs(abs(f['n'][k]) - 1) > 1e-3:
            return False
        return sign is None or f['n'][k] * sign > 0
    return test


def cylinder(r):
    return lambda f: f['t'] == 'CYLINDER' and near(f['r'], r)


CASES = dict(
    step_block=dict(
        part='step block', material=STEEL,
        story='The block sits on a bench and a 5 kN press pushes down on the top of the high step.',
        fixed=[dict(test=plane('z', 0), where='the bottom face')],
        loads=[dict(kind='force', value=5000, dir=(0, 0, -1), test=plane('z', 40), where='the top face of the high step',
                    how='Force, 5000 N, direction straight down')]),
    sloping_block=dict(
        part='sloping block', material=STEEL,
        story='The block is bolted down and a 10 kN load pushes square onto the sloping face.',
        fixed=[dict(test=plane('z', 0), where='the bottom face')],
        loads=[dict(kind='force', value=10000, dir='normal',
                    test=lambda f: f['t'] == 'PLANE' and f['n'] is not None and near(f['n'][0], 0.7071, 0.01) and near(f['n'][2], 0.7071, 0.01),
                    where='the sloping face', how='Force, 10000 N, normal to the face (the default direction)')]),
    flanged_bush=dict(
        part='flanged bush', material=BRASS,
        story='The flange sits on a housing and a 5 kN axial load presses on the end of the bush.',
        fixed=[dict(test=plane('z', 0), where='the underside of the flange')],
        loads=[dict(kind='force', value=5000, dir=(0, 0, -1), test=plane('z', 50), where='the top end face of the bush',
                    how='Force, 5000 N, along the axis towards the flange')]),
    bolted_joint=dict(
        part='lower plate', material=ALUMINIUM,
        story='The lower plate is held at both ends and the bolt pulls down on it with 2 kN.',
        fixed=[dict(test=plane('x', -40), where='the left end face'), dict(test=plane('x', 40), where='the right end face')],
        loads=[dict(kind='force', value=2000, dir=(0, 0, -1), test=cylinder(4.5), where='the inside of the bolt hole',
                    how='Force, 2000 N, straight down')]),
    threaded_shaft=dict(
        part='threaded shaft', material=STEEL,
        story='The shaft is held at its large end and a 500 N side load acts on the threaded end.',
        fixed=[dict(test=plane('x', 0), where='the end face of the 30 mm diameter')],
        loads=[dict(kind='force', value=500, dir=(0, 0, -1), test=cylinder(8), where='the 16 mm threaded diameter',
                    how='Force, 500 N, straight down (square to the shaft)')]),
    pcd_flange=dict(
        part='PCD flange', material=ALUMINIUM,
        story='The flange is bolted down through its six holes and the hub carries a 10 kN axial load.',
        fixed=[dict(test=cylinder(5), where='the six bolt holes')],
        loads=[dict(kind='force', value=10000, dir=(0, 0, -1), test=plane('z', 35), where='the top face of the hub',
                    how='Force, 10000 N, along the axis towards the flange')]),
    annotation_plate=dict(
        part='annotation plate', material=ALUMINIUM,
        story='The plate is screwed down through its four countersunk holes and a 2 kN load pulls down on the bore.',
        fixed=[dict(test=cylinder(3.3), where='the four 6.6 mm holes')],
        loads=[dict(kind='force', value=2000, dir=(0, 0, -1), test=cylinder(20), where='the 40 mm bore',
                    how='Force, 2000 N, straight down')]),
    hole_features=dict(
        part='hole features block', material=ALUMINIUM,
        story='The block is a beam held at both ends with 5 kN spread over its top face. Watch the stress gather round the holes.',
        fixed=[dict(test=plane('x', 0), where='the left end face'), dict(test=plane('x', 110), where='the right end face')],
        loads=[dict(kind='force', value=5000, dir=(0, 0, -1), test=plane('z', 20), where='the top face',
                    how='Force, 5000 N, straight down')]),
    vee_block=dict(
        part='vee block', material=STEEL,
        story='A round bar presses down into the vee with 5 kN and the block stands on its two feet.',
        fixed=[dict(test=plane('z', 0), where='the two feet (bottom faces)')],
        loads=[dict(kind='force', value=5000, dir=(0, 0, -1),
                    test=lambda f: f['t'] == 'PLANE' and f['n'] is not None and near(abs(f['n'][0]), 0.7071, 0.01) and f['n'][2] > 0.5,
                    where='the two faces of the vee', how='Force, 5000 N, straight down (pick both faces in one load)')]),
    l_bracket=dict(
        part='L bracket', material=STEEL,
        story='The bracket is a shelf bracket: the upright is screwed to a wall and 500 N sits on the base.',
        fixed=[dict(test=plane('x', 0), where='the back face of the upright (against the wall)')],
        loads=[dict(kind='force', value=500, dir=(0, 0, -1), test=plane('z', 5, sign=1), where='the top face of the base',
                    how='Force, 500 N, straight down')]),
    fit_pair=dict(
        part='housing (hole 20 H7)', material=ALUMINIUM,
        story='The housing is bolted down and the pin pushes sideways on the hole with 2 kN.',
        fixed=[dict(test=plane('z', 0), where='the bottom face')],
        loads=[dict(kind='force', value=2000, dir=(1, 0, 0), test=cylinder(10), where='the 20 mm hole',
                    how='Force, 2000 N, along the length of the housing')]),
    pneumatic_cylinder=dict(
        part='barrel', material=ALUMINIUM,
        story='The barrel is held by the end caps and filled with air at 6 bar (0.6 MPa).',
        fixed=[dict(test=plane('x', 0), where='the rear end face'), dict(test=plane('x', 80), where='the front end face')],
        loads=[dict(kind='pressure', value=0.6, test=cylinder(16), where='the bore (inside face)',
                    how='Pressure, 0.6 MPa')]),
)


# ------------------------------------------------------------------ ESP 2023 lock gates (models/esp2023.py)
S355 = dict(name='Steel S355 (add to the library: E 210 GPa, yield 355 MPa)', E=210000, nu=0.30, yield_strength=355)
STAINLESS = dict(name='Stainless Steel', E=193000, nu=0.30, yield_strength=250)
LEAF_WEIGHT = 87200          # N: one leaf and everything that turns with it, 8.89 t, from the CAD model (esp2023.leaf_mass)
LEAF_PULL = 19500            # N: leaf weight x centre of gravity 1290 mm from the pivot / 5770 mm between the hinges

CASES.update(
    esp2023_skin_panel=dict(
        part='skin plate panel', material=S355, mesh_size=8,
        story='The bottom skin plate panel holds back the water in a full lock (5.5 m head). It is welded on all four '
              'edges to the girders, the heel post and a stiffener.',
        fixed=[dict(test=plane('x', 400), where='the heel post edge'), dict(test=plane('x', 980), where='the stiffener edge'),
               dict(test=plane('z', 160), where='the bottom girder edge'), dict(test=plane('z', 790), where='the second girder edge')],
        loads=[dict(kind='hydrostatic', value=5500, test=plane('y', 225, sign=1), where='the chamber (water) face',
                    how='Pressure, 0.0493 MPa (the water pressure at the middle of the panel, 475 mm above the cill)',
                    note='Water pressure grows with depth: p = 1000 x 9.81 x depth. At the bottom of the panel it is 0.0524 MPa, at '
                         'the top 0.0462 MPa. Inventor Stress Analysis applies an even pressure, so use the value at the middle '
                         'of the panel: it gives the same total force. The hub solve uses the true varying pressure.')],
        mesh_note='The plate is only 12 mm thick, so the elements must be small enough to fit two or more through the thickness. ',
        hand_check='Roark, rectangular plate with all edges fixed, a/b = 630/580 = 1.09: stress at the middle of the long edge '
                   '= 0.340 x p x b^2 / t^2 = 0.340 x 0.0493 x 580^2 / 12^2 = 39 MPa; deflection at the centre = 0.0160 x p x b^4 '
                   '/ (E t^3) = 0.25 mm.'),
    esp2023_p20_bottom_pintle=dict(
        part='bottom pintle', material=STAINLESS,
        story='The bottom pintle carries the whole weight of a leaf (8.9 t, 87.2 kN) and the sideways push from the leaf '
              'trying to tip forwards (19.5 kN). It is held into the cill by four M24 anchor bolts.',
        fixed=[dict(test=plane('z', -80), where='the underside of the base plate')],
        loads=[dict(kind='force', value=LEAF_WEIGHT, dir=(0, 0, -1), test=plane('z', 280), where='the top of the pin',
                    how='Force, 87200 N, straight down (the weight of the leaf)'),
               dict(kind='force', value=LEAF_PULL, dir=(0.9487, -0.3162, 0), test=cylinder(75), where='the side of the pin',
                    how='Force, 19500 N, along the closed leaf towards the quoin (Direction: pick the leaf edge, then Flip if needed)')],
        hand_check='Direct stress 87200 / (pi x 150^2 / 4) = 4.9 MPa. Bending 19500 x 140 / (pi x 150^3 / 32) = 8.2 MPa. '
                   'Together about 13 MPa on the plain pin. The 15 mm root fillet raises this by a stress concentration factor of '
                   'about 1.6, to about 21 MPa, which is where the FEA finds its peak.'),
)
