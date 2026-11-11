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


# ------------------------------------------------------------------ machine vice (hub model 13)
DUCTILE_IRON = dict(name='Iron, Ductile (EN-GJS-400; add to the library if needed: E 169 GPa)', E=169000, nu=0.29,
                    yield_strength=276)
CASES['machine_vice'] = dict(
    part='moving jaw', material=DUCTILE_IRON,
    story='The tommy bar is pulled with 200 N at its end. Through the M16 x 2 lead screw that clamps the work with about '
          '10 kN, which pushes back on the face of the moving jaw while the screw thread holds it.',
    fixed=[dict(test=cylinder(8), where='the M16 threaded hole (the lead screw holds the jaw here)')],
    loads=[dict(kind='force', value=10000, dir=(1, 0, 0), test=plane('x', 111, sign=-1), where='the front (clamping) face',
                how='Force, 10000 N, pushing the jaw back along the screw (away from the work)')],
    hand_check='Screw: torque 200 N x 80 mm = 16 N m; clamping force = 2 pi T efficiency / pitch = 2 pi x 16000 x 0.2 / 2 '
               '= about 10 kN. Jaw: the load acts on the jaw face, centred 38 mm above the screw axis, so the head bends where it '
               'meets the tongue: M = 10000 x 38 = 380000 N mm; section 69 wide x 35 deep, Z = 69 x 35^2 / 6 = 14090 mm^3; '
               'bending stress = M / Z = 27 MPa. The FEA peak (about 63 MPa) is at the sharp inside corner where the head meets the '
               'tongue: a stress concentration of about 2.3, as expected for a corner with no fillet.')

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


# ------------------------------------------------------------------ ESP 2026 economy three-seat set (models/esp2026.py)
import esp2026 as _seat  # noqa: E402

AL7075 = dict(name='Aluminum 7075-T6 (add to the library if needed: E 71.7 GPa, yield 503 MPa)', E=71700, nu=0.33,
              yield_strength=503)
SEAT_OCCUPANT = 77                       # kg, the standard passenger mass used for seat certification (CS 25.562)
SEAT_G = 9                               # emergency landing forward load factor, CS 25.561
SEAT_SET_MASS = 23.5                     # kg, the three-seat set without life vests, from the CAD model (esp2026.set_mass)
LEG_FORWARD = round(SEAT_G * 9.81 * (3 * SEAT_OCCUPANT + SEAT_SET_MASS) / 2)   # N on each leg


def _mid(p, q, oy=_seat.LEG_A[0]):
    """Middle of a strut, on the plate centre plane, in the coordinates of the leg part file."""
    return [0.0, (p[0] + q[0]) / 2 - oy, (p[1] + q[1]) / 2]


def _probe(name, p, q):
    return dict(name=name, at=_mid(p, q), r=8)


CASES.update(
    esp2026_p04_leg=dict(
        part='leg', material=AL7075, mesh_size=5,
        story='A 9 g forward emergency landing (CS 25.561): three 77 kg passengers and the seat itself push forwards on '
              'the beam tubes, and the leg holds them back from its two track fittings. Each of the two legs takes half: '
              '%.1f kN.' % (LEG_FORWARD / 1000),
        fixed=[dict(test=plane('z', 25, sign=-1), where='the underside of the two foot pads (the track fittings)')],
        loads=[dict(kind='force', value=LEG_FORWARD, dir=(0, -1, 0), test=cylinder(25), where='the two beam tube bores',
                    how='Force, %d N, forwards (along -Y): pick both bores' % LEG_FORWARD,
                    note='Half of the load goes into each beam bore. The real crash test is dynamic (CS 25.562, 16 g); '
                         'this static 9 g check is the one used to size the structure first.')],
        probes=[_probe('front strut', _seat.LEG_A, _seat.LEG_C), _probe('rear strut', _seat.LEG_B, _seat.LEG_D),
                _probe('brace', _seat.LEG_A, _seat.LEG_D), _probe('top chord', _seat.LEG_C, _seat.LEG_D)],
        mesh_note='The plate is 10 mm thick and the struts 30 to 40 mm wide, so a 5 mm mesh puts two or more '
                  'quadratic elements through the thickness. ',
        hand_check='Treat the leg as a pin jointed truss (struts, chord and brace): half the load at each beam bore, '
                   'reactions at the two feet. The member forces divided by the strut areas give the stress in the '
                   'middle of each strut, away from the joints: see the ESP 2026 calculation sheet, section 6.'),
)


# ------------------------------------------------------------------ ESP 2024 harbour buoy (models/esp2024.py)
import esp2024 as _buoy  # noqa: E402

SS316L = dict(name='Stainless Steel 316L (add to the library if needed: E 193 GPa, yield 170 MPa)', E=193000, nu=0.27,
              yield_strength=170)
CHAIN_MBL = 40000                        # N, minimum breaking load of the 10 mm grade 30 mooring chain (EN 818 / ISO 1834)
_EYE_HOLE = _buoy.EYE_Z - _buoy.BOT_PLATE[0]   # hole centre below the top of the mooring eye (part coordinates)
_EYE_T = _buoy.EYE_T

CASES.update(
    esp2024_p23_mooring_eye=dict(
        part='mooring eye', material=SS316L, mesh_size=3,
        story='The worst pull the mooring can put on the buoy is the breaking load of the chain: %.0f kN. The mooring eye '
              'must not yield before the chain breaks, so the buoy is never the weak link. The pin pulls straight down '
              'through the hole; the top of the eye is welded to the tail bottom plate.' % (CHAIN_MBL / 1000),
        fixed=[dict(test=plane('z', 0), where='the top face of the eye (the weld to the bottom plate)')],
        loads=[dict(kind='force', value=CHAIN_MBL, dir=(0, 0, -1), test=cylinder(_buoy.PIN_R + 1), where='the pin hole',
                    how='Force, %d N, straight down (Direction: pick a vertical edge, then Flip if needed)' % CHAIN_MBL,
                    note='Inventor spreads the force over the whole hole face. In the real eye the pin bears on the bottom '
                         'half, so the stress round the hole is higher than here: see the hand check of the bearing stress.')],
        probes=[dict(name='plate above the hole', at=[0.0, 0.0, -12.0], r=6),
                dict(name='side of the hole (net section)', at=[0.0, 30.0, _EYE_HOLE], r=5)],
        mesh_note='The plate is %d mm thick and the hole %d mm across, so a 3 mm mesh puts several quadratic elements '
                  'through the thickness and round the hole. ' % (_EYE_T, 2 * _buoy.PIN_R + 2),
        hand_check='Plate above the hole: %d / (90 x %d) = %.1f MPa. Net section beside the hole: %d / ((90 - %d) x %d) = %.1f MPa. '
                   'Pin bearing on the hole: %d / (%d x %d) = %.1f MPa. Round the edge of the hole the stress rises by a '
                   'stress concentration factor of about 2 to 3. The FEA, like Inventor, spreads the force round the whole hole, so half of it '
                   'goes straight into the plate above and the FEA beside the hole is about half the hand value; the real pin bears on '
                   'the bottom of the hole, so design to the hand value. See the ESP 2024 calculation sheet, section 6.' % (
                       CHAIN_MBL, _EYE_T, CHAIN_MBL / (90 * _EYE_T), CHAIN_MBL, 2 * _buoy.PIN_R + 2, _EYE_T,
                       CHAIN_MBL / ((90 - 2 * _buoy.PIN_R - 2) * _EYE_T), CHAIN_MBL, 2 * _buoy.PIN_R, _EYE_T,
                       CHAIN_MBL / (2 * _buoy.PIN_R * _EYE_T))),
)


# ------------------------------------------------------------------ ESP 2025 automated pill dispenser (models/esp2025.py)
import os as _os, sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'tools'))
import esp2025 as _pill  # noqa: E402
import esp2025_calcs as _pc  # noqa: E402

PPGF30 = dict(name='PP, 30 % glass filled (add to the library: E 6.5 GPa, Poisson 0.38, yield 75 MPa)', E=6500, nu=0.38,
              yield_strength=_pc.CATCH_YIELD)
_C = _pill.CATCH
_OZ = _pill.CATCH_ORIGIN[2]
_FLANGE_TOP = _pill.LID_Z[1] - _pill.LID_TOP - _OZ        # flange top, heat staked to the lid (part coordinates)
_LIP_TOP = _C['z'][1] - _OZ                               # top of the hook, where the cam bears


def _catch_pt(x, r, z):
    """A point on radius r (from the dispenser axis), in line with x across the catch sketch, at height z, in part
    coordinates."""
    import math as _m
    a = _m.atan2(-sum(_C['r']) / 2, x)
    px, py = _pill._rot_xy(r * _m.cos(a), r * _m.sin(a), _pill.LOCK_ANG + 90)
    ox, oy, oz = _pill.CATCH_ORIGIN
    return [round(px - ox, 3), round(py - oy, 3), round(z - oz, 3)]


_xm = sum(_C['x']) / 2
_hc = _pc.catch_hand()
CASES.update(
    esp2025_p34_lid_catch=dict(
        part='lid catch', material=PPGF30, mesh_size=1.0,
        story='Someone tries to force the locked lid open, pulling up hard on its front edge: %d N, all taken by the catch. '
              'The cam of the pharmacy lock holds the hook down, so the tab is pulled in tension and bent, and the hook is '
              'bent and sheared. The catch must not break or bend far enough to slip off the cam. Only the flange is held '
              'here, so the long tab is free to bend; in the dispenser the edge of the slot in the deck is %g mm inside the '
              'tab and stops it bending in any further, so the real catch moves less than this study shows.' % (_pc.PRY, _pill.SLOT_GAP),
        fixed=[dict(test=plane('z', _FLANGE_TOP, 1), where='the top face of the flange (heat staked to the lid)')],
        loads=[dict(kind='force', value=_pc.PRY, dir=(0, 0, -1), test=plane('z', _LIP_TOP, 1), where='the top face of the hook',
                    how='Force, %d N, on the top face of the hook, straight down (the cam pushes on it as the lid is pulled up)'
                        % _pc.PRY)],
        probes=[dict(name='inside face of the tab, above the hook', at=_catch_pt(_xm, _C['r'][0], _C['z'][1] + 4), r=1.0),
                dict(name='outside face of the tab, above the hook', at=_catch_pt(_xm, _C['r'][1], _C['z'][1] + 4), r=1.0)],
        mesh_note='The tab is only %.1f mm thick, so a 1 mm mesh of quadratic (10 node) elements puts nodes on both faces and through the middle. '
                  % (_C['r'][1] - _C['r'][0]),
        hand_check='Tab: direct stress %d / (%g x %g) = %.1f MPa, plus bending from the hook being %.2f mm off the middle of '
                   'the tab: 6 x %d x %.2f / (%g x %g²) = %.1f MPa, total %.1f MPa, safety factor %.1f on %d MPa. Hook: bending '
                   '%.1f MPa, shear %.1f MPa. The inside corner where the hook meets the tab raises the stress locally. '
                   'See the ESP 2025 calculation sheet, section 6.' % (
                       _pc.PRY, _hc['b'], _hc['t'], _hc['direct'], _hc['e'], _pc.PRY, _hc['e'], _hc['b'], _hc['t'],
                       _hc['bend'], _hc['total'], _hc['sf'], _pc.CATCH_YIELD, _hc['lip_bend'], _hc['lip_shear'])),
)
