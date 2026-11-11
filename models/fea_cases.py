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


# ------------------------------------------------------------------ GrabCAD models (models/library.py)
GREY_IRON = dict(name='Iron, Gray (EN-GJL-250: E 110 GPa; cast iron has no yield point, so its 250 MPa tensile strength is used)',
                 E=110000, nu=0.26, yield_strength=250)
ALLOY_STEEL = dict(name='Steel, Alloy (709M40 / 42CrMo4, yield 680 MPa)', E=210000, nu=0.29, yield_strength=680)
EN8 = dict(name='Steel, Carbon (080M40 / EN8, yield 385 MPa)', E=210000, nu=0.29, yield_strength=385)
CASES['plummer_block'] = dict(
    part='housing base', material=GREY_IRON,
    story='The shaft pushes down on the bearing with 10 kN (about half the bearing\'s static rating). The base is held only by '
          'the two holding down bolts in its slots, so the foot bends between them.',
    fixed=[dict(test=cylinder(7), where='the curved ends of the two bolt slots')],
    loads=[dict(kind='force', value=10000, dir=(0, 0, -1), test=cylinder(40), where='the bearing seat (the 80 mm half bore)',
                how='Force, 10000 N, straight down')],
    hand_check='The foot as a beam between the bolts (210 mm apart) with the load in the middle: M = F L / 4 = 10000 x 210 / 4 = '
               '525000 N mm. Under the bore the section is about 60 wide and 25 deep: Z = 60 x 25^2 / 6 = 6250 mm^3, so '
               'M / Z = 84 MPa. The body and lugs either side of the bore stiffen it, so the FEA stress is lower.')
CASES['spur_gearbox'] = dict(
    part='output shaft', material=EN8,
    story='The gear wheel carries 250 N m. The tooth force is 2 x 250000 / 100 = 5000 N along the pitch line and 5000 x tan 20 = 1820 N '
          'towards the centre, 5320 N in all, which bends the shaft between its bearings.', mesh_size=3,
    fixed=[dict(test=cylinder(10), where='the bearing journals (the 20 mm diameters)')],
    loads=[dict(kind='force', value=5320, dir=(0, 0, -1), test=cylinder(12), where='the 24 mm wheel seat',
                how='Force, 5320 N, square to the shaft')],
    hand_check='Between simply supported bearings 74 apart, M = F L / 4 = 5320 x 74 / 4 = 98400 N mm; with both ends held, M = F L / 8 '
               '= 49200 N mm. Z = pi x 24^3 / 32 = 1357 mm^3, so the bending stress is between 36 and 73 MPa. The FEA holds the '
               'journals all round (nearer the held case), and the keyway and the shoulders raise the peak.')
CASES['universal_joint'] = dict(
    part='input yoke', material=ALLOY_STEEL,
    story='The joint passes 260 N m: the cross pushes up on one arm and down on the other with 5000 N each, 26 mm from the shaft line.',
    fixed=[dict(test=cylinder(11), where='the 22 mm shaft bore')],
    loads=[dict(kind='force', value=5000, dir=(0, 0, 1), test=lambda f: cylinder(10)(f) and f['c'][1] > 0,
                where='the cup hole in the left arm', how='Force, 5000 N, up'),
           dict(kind='force', value=5000, dir=(0, 0, -1), test=lambda f: cylinder(10)(f) and f['c'][1] < 0,
                where='the cup hole in the right arm', how='Force, 5000 N, down')],
    hand_check='Each arm is a cantilever 28 mm long from the bridge: M = 5000 x 28 = 140000 N mm. The arm is 8 thick and 32 deep, '
               'Z = 8 x 32^2 / 6 = 1365 mm^3, so the bending stress is 103 MPa at the root of the arm. The FEA peak (about 260 MPa) '
               'is in the sharp inside corner where the arm meets the bridge: a stress concentration of about 2.5. A 3 mm fillet '
               'there would bring it down a lot, which is why forged yokes have generous radii.')
C45 = dict(name='Steel, Carbon (C45 / 080M46, yield 430 MPa)', E=210000, nu=0.29, yield_strength=430)
S355 = dict(name='Steel, High Strength Low Alloy (S355, yield 355 MPa)', E=210000, nu=0.30, yield_strength=355)
CASES['toggle_clamp'] = dict(
    part='clamp arm', material=C45,
    story='The clamp holds the work down with 800 N (its rated holding force). The spindle pushes up on the end of the arm, and the '
          'pivot pin and the link pin hold it.',
    fixed=[dict(test=cylinder(3), where='the pivot pin hole and the link pin hole')],
    loads=[dict(kind='force', value=800, dir=(0, 0, 1), test=cylinder(4.25), where='the round ends of the spindle slot',
                how='Force, 800 N, up')],
    hand_check='The arm is a cantilever from the pivot: the slot centre is 92 mm in front of it, so M = 800 x 92 = 73600 N mm. The bar '
               'is 12 wide and 16 deep, Z = 12 x 16^2 / 6 = 512 mm^3, so the bending stress next to the pivot is M / Z = 144 MPa. '
               'The 6 mm pin hole sits in the middle of that section (Z drops to 485 mm^3, 152 MPa) and raises the stress round its '
               'edge by about 1.4, which is where the FEA finds its 210 MPa peak.')
CASES['swivel_castor'] = dict(
    part='fork', material=S355,
    story='The castor carries 150 kg (1470 N, say 1500 N). The axle pushes up on the legs and the balls in the track hold the crown.',
    fixed=[dict(test=lambda f: f['t'] == 'TORUS', where='the ball track in the crown')],
    loads=[dict(kind='force', value=1500, dir=(0, 0, 1), test=cylinder(5.25), where='the axle holes in the legs',
                how='Force, 1500 N, up')],
    hand_check='Each leg carries 750 N. Where a leg (centre 35 mm out, 22 mm to the side) meets the crown, the nearest point of the '
               'ball track (60 diameter) is about 14.6 mm away, so the crown bends as a short cantilever: M = 750 x 14.6 = 10950 N mm. '
               'The crown is 6 thick and about 24 wide there, Z = 24 x 6^2 / 6 = 144 mm^3, so M / Z = 76 MPa. The FEA peak (85 MPa) '
               'is at the edge of the ball track, close to this.')
CASES['screw_jack'] = dict(
    part='body', material=GREY_IRON,
    story='The jack lifts 3 tonnes (30 kN). The nut flange presses down on the top of the body, and the floor holds its base.',
    fixed=[dict(test=plane('z', 0), where='the underside of the base')],
    loads=[dict(kind='force', value=30000, dir=(0, 0, -1), test=plane('z', 120), where='the top of the boss (under the nut flange)',
                how='Force, 30000 N, straight down')],
    hand_check='Compressive stress = F / A. On the top face (a ring 56 to 70 diameter) A = pi x (35^2 - 28^2) = 1385 mm^2, so '
               '30000 / 1385 = 22 MPa. Lower down, at 100 mm high, the wall is 38 to 64 diameter: A = 2083 mm^2 and the stress 14 MPa. '
               'Cast iron is far stronger in compression than in tension, so a jack body is a good use of it. The FEA peak (85 MPa) is '
               'at the edge of the set screw hole, 10 mm below the top: a hole in a 7 mm wall carrying load concentrates the stress '
               'about 3 to 4 times, as the hand value of 22 MPa suggests.')



CASES['flange_coupling'] = dict(
    part='flange B (recess)', material=C45,
    story='The coupling carries 430 N m of torque. Shaft B pushes its key against the side of the keyway in flange B, and the six '
          'bolts hold the flange to flange A.',
    fixed=[dict(test=cylinder(6.5), where='the six bolt holes')],
    loads=[dict(kind='force', value=20000, dir=(0, -1, 0), test=plane('y', -6), where='one side wall of the keyway',
                how='Force, 20000 N, across the keyway (430 N m / 21.5 mm radius)')],
    hand_check='Bearing stress on the keyway wall = F / A. The wall runs from the bore (19.1 mm from the centre) to 23.3 mm, so it is 4.2 mm high and '
               '81 mm long: A = 340 mm^2 and 20000 / 340 = 59 MPa, the same as the FEA peak (59 MPa), which is at the inner corner of the wall '
               'where the keyway meets the bore. The six bolts each carry 430 / (6 x 0.06) = 1194 N, so the flange itself is lightly loaded.')

CASES['knuckle_joint'] = dict(
    part='eye end', material=EN8,
    story='The tie rods pull the joint apart with 50 kN. The pin pulls on the eye and the tie rod holds the other end.',
    fixed=[dict(test=cylinder(12), where='the tapped hole for the tie rod')],
    loads=[dict(kind='force', value=50000, dir=(-1, 0, 0), test=lambda f: cylinder(12.5)(f) and f['c'][0] < 0,
                where='the half of the pin hole the pin pulls on', how='Force, 50000 N, along the rod towards the fork')],
    hand_check='Tension across the eye, beside the pin hole: A = (50 - 25) x 31 = 775 mm^2, so 50000 / 775 = 65 MPa. A pin-loaded hole '
               'concentrates the stress about twice at the sides of the hole, giving about 130 MPa: the FEA peak (132 MPa) is just there, at '
               'the side of the pin hole. The M24 tie rod (353 mm^2 stress area) carries 50000 / 353 = 142 MPa, so it is the weakest link.')

CASES['piston_crank'] = dict(
    part='connecting rod', material=C45,
    story='At the top of the stroke the burning gas presses on the piston at 40 bar. The gudgeon pin pushes the rod down onto the crank pin.',
    fixed=[dict(test=cylinder(10), where='the big end bore (on the crank pin)')],
    loads=[dict(kind='force', value=7850, dir=(0, 0, -1), test=cylinder(6),
                where='the small end bore (the gudgeon pin bears on it)', how='Force, 7850 N, straight down (4 MPa x the 1963 mm^2 piston area)')],
    hand_check='Compression in the 12 x 12 shank = 7850 / 144 = 55 MPa. Buckling (Euler, pinned ends): P = pi^2 x E x I / L^2 = pi^2 x 210000 x '
               '1728 / 100^2 = 358 kN, 45 times the load. Bearing on the gudgeon pin = 7850 / (12 x 17) = 38 MPa. The FEA peak (102 MPa) is at '
               'the edge of the small end bore, where the 5 mm wall above the shank carries the pin load: about twice the shank stress.')


# ------------------------------------------------------------------ Additional CAD exercise (models/exercises.py)
import math as _math  # noqa: E402
DUCTILE = dict(name='Iron, Ductile (EN-GJS-400-15, yield 250 MPa)', E=169000, nu=0.275, yield_strength=250)
SS316L = dict(name='Stainless Steel, 316L (annealed, yield 170 MPa)', E=193000, nu=0.27, yield_strength=170)
AISI1020 = dict(name='Steel, Mild (AISI 1020 hot rolled, yield 210 MPa)', E=200000, nu=0.29, yield_strength=210)
LM25 = dict(name='Aluminium, cast (LM25 as cast, 0.2% proof 80 MPa)', E=71000, nu=0.33, yield_strength=80)
LM6 = dict(name='Aluminium, cast (LM6 as cast, 0.2% proof 60 MPa)', E=71000, nu=0.33, yield_strength=60)
A356 = dict(name='Aluminium, cast (A356-T6, yield 165 MPa)', E=72400, nu=0.33, yield_strength=165)
CAST_STEEL = dict(name='Steel, Cast (GP240GH / WCB, yield 240 MPa)', E=200000, nu=0.30, yield_strength=240)
S275 = dict(name='Steel, Structural (S275, yield 275 MPa)', E=210000, nu=0.30, yield_strength=275)


def _seat(theta):
    """The planet bearing seat in the carrier at angle theta (degrees)."""
    return lambda f: cylinder(4.5)(f) and abs(((_math.degrees(_math.atan2(f['c'][1], f['c'][0])) - theta + 180) % 360) - 180) < 20


def _tang(theta):
    t = _math.radians(theta)
    return (round(-_math.sin(t), 4), round(_math.cos(t), 4), 0)


CASES['ax_fork_bracket'] = dict(
    part='fork bracket', material=GREY_IRON,
    story='A pin through the two lugs carries 10 kN straight down (say from a lever or a link). The base is bolted to a frame.',
    fixed=[dict(test=plane('z', 0), where='the underside of the base (both pads)')],
    loads=[dict(kind='force', value=10000, dir=(0, 0, -1), test=cylinder(9), where='the 18 mm pin holes in both lugs',
                how='Force, 10000 N, straight down')],
    hand_check='Each lug carries 5000 N. Bearing on the pin hole = F / (d x t) = 5000 / (18 x 13) = 21 MPa. Compression in a '
               'lug (13 thick, 36 wide) = 5000 / 468 = 11 MPa. Both are small for cast iron, which is strong in compression. '
               'The FEA agrees: the lugs read up to 26 MPa, at the crown above the pin holes (Inventor spreads a force over '
               'the whole hole, top half included, so the crown is pulled down too). The peak, 28 MPa, is at a corner of the '
               'relief under the base, right beside the fixed face.')
CASES['ax_pedestal_bearing'] = dict(
    part='pedestal bearing', material=GREY_IRON,
    story='A shaft in the 18 mm bore pushes down with 8 kN. The base sits on a bed plate, held by bolts in its two slots.',
    fixed=[dict(test=plane('z', 0), where='the underside of the base')],
    loads=[dict(kind='force', value=8000, dir=(0, 0, -1), test=cylinder(9), where='the 18 mm bore', how='Force, 8000 N, straight down')],
    hand_check='Bearing pressure in the bore = F / (d x L) = 8000 / (18 x 35) = 12.7 MPa. The cross shaped column (a 10 mm web '
               'and a 9 mm rib, about 590 mm^2) carries 8000 / 590 = 13.6 MPa in compression. The FEA peak, 28 MPa, is at a '
               'corner of the relief under the base, beside the fixed face, and the sides of the bore read about 25 MPa, where '
               'the force spread round the bore drags on the metal. All of it is under a ninth of the strength of the iron.')
CASES['ax_slotted_boss_flange'] = dict(
    part='slotted boss flange', material=GREY_IRON,
    story='A shaft in the 26 mm bore pushes sideways with 3 kN, trying to bend the boss over. The flange is bolted down.',
    fixed=[dict(test=plane('z', 0), where='the underside of the flange')],
    loads=[dict(kind='force', value=3000, dir=(1, 0, 0), test=cylinder(13), where='the 26 mm bore', how='Force, 3000 N, sideways (+X)')],
    hand_check='The boss is a short tube cantilever. The load acts about 28 mm above the flange: M = 3000 x 28 = 84000 N mm. '
               'For a tube 40 outside, 26 inside, Z = pi (40^4 - 26^4) / (32 x 40) = 5162 mm^3, so the bending stress at the '
               'flange is 84000 / 5162 = 16 MPa. The slot across the top weakens the end, but there the moment is small. The '
               'FEA peak, 21 MPa, is just there, round the root of the boss where it meets the flange: the sharp corner adds '
               'about a third.')
CASES['ax_corner_boss_bracket'] = dict(
    part='boss bracket', material=GREY_IRON,
    story='The bracket is bolted through its two lugs and carries 1 kN (about 100 kg) pressing down on the top of the boss, 62 mm out.',
    fixed=[dict(test=cylinder(6.5), where='the two 13 mm lug holes')],
    loads=[dict(kind='force', value=1000, dir=(0, 0, -1), test=plane('z', 30, 1), where='the top face of the boss',
                how='Force, 1000 N, straight down')],
    hand_check='The plate and rib are a cantilever from the line through the two bolts: M = 1000 x 62 = 62000 N mm. The worst '
               'section is that line, where the rib has only just started: the plate (88 wide, less the two 13 mm holes, 8 '
               'thick), the two lug bosses and the low end of the rib. I = 5900 mm^4 about a centroid 5.1 mm above the '
               'underside, so the underside sees 62000 x 5.1 / 5900 = 54 MPa (compression) and the top of the rib 62000 x 6.8 '
               '/ 5900 = 71 MPa (tension). Grey iron is weak in tension, so this is why the load is 1 kN and not more: at 2 kN '
               'the safety factor drops to about 1.3. The FEA shows the same bending, but not evenly across the width: the '
               'metal beside the bolts carries most of it (about 50 to 65 MPa next to the lug holes) and the middle carries '
               'less (about 35 MPa at the top of the rib), because the simple figures assume the whole width works equally. '
               'The peak, 94 MPa, is at the underside edge of a lug hole, where the fixed bolt hole concentrates the stress. '
               'The lowest safety factor is 2.6.')
CASES['ax_saddle_block'] = dict(
    part='saddle bearing block', material=GREY_IRON,
    story='A 56 mm shaft (or bearing shell) sits in the R28 saddle and presses down with 20 kN. The block is bolted down.',
    fixed=[dict(test=plane('z', 0), where='the underside of the base')],
    loads=[dict(kind='force', value=20000, dir=(0, 0, -1), test=cylinder(28), where='the R28 saddle', how='Force, 20000 N, straight down')],
    hand_check='Bearing pressure on the projected area = F / (d x L) = 20000 / (56 x 53) = 6.7 MPa. The block under the saddle '
               '(68 x 70) carries 20000 / 4760 = 4.2 MPa in compression. A saddle block is stiff and lightly stressed. Under '
               'the middle of the saddle the FEA reads about 3 MPa. Its peak, 28 MPa, is at the top edges of the saddle: '
               'Inventor spreads the force evenly over the whole half round face, so the steep sides near the top are dragged '
               'down too. A real shaft presses hardest at the bottom.')
CASES['ax_clamp_lever'] = dict(
    part='split clamp lever', material=DUCTILE,
    story='The lever is clamped on a 28 mm shaft. A hand pushes the end of the arm sideways with 1000 N to turn the shaft.',
    fixed=[dict(test=cylinder(14), where='the 28 mm clamp bore')],
    loads=[dict(kind='force', value=1000, dir=(0, 1, 0), test=cylinder(15), where='the round end of the arm', how='Force, 1000 N, sideways (+Y)')],
    hand_check='At the start of the slot, 52 mm from the end, M = 1000 x 52 = 52000 N mm. There the arm is a U: an 8 mm floor '
               '30 wide and two 5 mm walls 12 high. I = 37000 mm^4 about the vertical axis, Z = 37000 / 15 = 2467 mm^3, so the '
               'bending stress is 21 MPa. The push also twists the arm: a U open at the top twists about a point just below '
               'its floor, about 12 mm below where the push acts, so T = 1000 x 12 = 12000 N mm. An open section is weak in '
               'twist: J = (30 x 8^3 + 2 x 12 x 5^3) / 3 = 6100 mm^4, and the shear stress in the floor is T t / J = 12000 x 8 '
               '/ 6100 = 16 MPa. Together, von Mises = sqrt(21^2 + 3 x 16^2) = 35 MPa, the same as the FEA peak (35 MPa), '
               'which is on the bottom edges of the arm where the slot starts. Torque on the shaft = 1000 x 0.098 = 98 N m.')
CASES['ax_roller_assembly'] = dict(
    part='bracket (right)', material=GREY_IRON, mesh_size=6,
    story='The roller carries 10 kN, shared by the two brackets: the spindle pushes down on each bracket hole with 5 kN.',
    fixed=[dict(test=plane('z', 20, -1), where='the underside of the bracket foot')],
    loads=[dict(kind='force', value=5000, dir=(0, 0, -1), test=cylinder(8), where='the 16 mm spindle hole', how='Force, 5000 N, straight down')],
    hand_check='Bearing on the spindle hole = 5000 / (16 x 14) = 22 MPa. The upright (14 x 36) carries 5000 / 504 = 9.9 MPa in '
               'compression. The FEA peak, 26 MPa, is at the sides of the spindle hole, close to the bearing figure.')
CASES['ax_valve_body'] = dict(
    part='valve body', material=SS316L,
    story='Hydrostatic test: the valve is filled with water at 60 bar (6 MPa, 1.5 x a 40 bar rating) with its end flanges blanked off.',
    fixed=[dict(test=lambda f: plane('x', 79, 1)(f) or plane('x', -79, -1)(f), where='the two end flange faces')],
    loads=[dict(kind='pressure', value=6.0,
                test=lambda f: (f['t'] == 'PLANE' and (near(abs(f['c'][0]), 26, 0.5) or near(abs(f['c'][1]), 36, 0.5) or near(f['c'][2], -41, 0.5)))
                or (f['t'] == 'CYLINDER' and f['r'] is not None and (near(f['r'], 21) or near(f['r'], 10)) and abs(f['c'][1]) < 40),
                where='the inside of the chamber and the main bore', how='Pressure, 6 MPa')],
    hand_check='The bore is a thick tube: hoop stress = p r / t = 6 x 21 / 19 = 6.6 MPa. The flat chamber walls are the weak '
               'spot: a long plate 52 wide and 10 thick, held at its edges, has a bending stress of p b^2 / (2 t^2) = 6 x 52^2 '
               '/ (2 x 10^2) = 81 MPa at its edges. Flat walls on a pressure vessel bend; round ones only stretch. The FEA '
               'peak, 59 MPa, is in a corner of the chamber, a little below the long plate figure: the chamber walls are short '
               'and their corners stiffen them. The lowest safety factor is 2.9 at the test pressure.', mesh_size=8)
CASES['ax_machinists_jack'] = dict(
    part='base', material=AISI1020,
    story='The jack props a 2 tonne casting: 20 kN comes down the screw and swivel onto the pivot bolt in the two base lugs.',
    fixed=[dict(test=plane('z', 0), where='the underside of the base')],
    loads=[dict(kind='force', value=20000, dir=(0, 0, -1), test=cylinder(8), where='the 16 mm pivot holes in both lugs',
                how='Force, 20000 N, straight down')],
    hand_check='Each lug carries 10000 N. Bearing on the pivot hole = 10000 / (16 x 10) = 62.5 MPa. Each lug (10 thick, about '
               '40 wide) carries 10000 / 400 = 25 MPa in compression. The FEA peak, 52 MPa, is at the edge of a pivot hole, '
               'close to the bearing figure, and the lugs read about 24 MPa a little lower down, as the compression figure '
               'says.')
CASES['ax_planetary_gears'] = dict(
    part='carrier', material=AISI1020,
    story='The output shaft drives a load of 3 N m (the sun gives 0.5 N m, times the 6 to 1 ratio). Each planet pushes its bearing '
          'seat round with 3000 / (3 x 18) = 56 N, and the 8 mm shaft is held in a coupling.', mesh_size=1.2,
    fixed=[dict(test=cylinder(4), where='the 8 mm output shaft')],
    loads=[dict(kind='force', value=55.6, dir=_tang(a), test=_seat(a), where='the bearing seat at %d degrees' % a,
                how='Force, 55.6 N, round the shaft axis (at right angles to the radius)') for a in (0, 120, 240)],
    hand_check='Torsion in the 8 mm shaft: tau = 16 T / (pi d^3) = 16 x 3000 / (pi x 512) = 30 MPa, a von Mises stress of '
               'sqrt(3) x 30 = 52 MPa. Bending of a lobe: each seat is 7.5 mm from the plate edge, M = 56 x 7.5 = 420 N mm on '
               'a 15 x 4 section (Z = 40 mm^3): 10 MPa. The FEA peak, 51 MPa, is on the surface of the shaft: the same as the '
               'torsion figure.')
CASES['ax_tube_bracket_45'] = dict(
    part='tube bracket', material=LM25,
    story='A pipe bolted to the square flange pushes on it with 1 kN, square to the flange face. The base is bolted down.',
    fixed=[dict(test=plane('z', 0), where='the underside of the base')],
    loads=[dict(kind='force', value=1000, dir='normal',
                test=lambda f: f['t'] == 'PLANE' and f['n'] is not None and near(f['n'][0], 0.7071, 0.01) and near(f['n'][2], 0.7071, 0.01)
                and f['a'] > 400, where='the face of the square flange', how='Force, 1000 N, normal to the face')],
    hand_check='The 45 degree tube is a short cantilever from the upright tube: about 30 mm long, M = 1000 x 30 = 30000 N mm. '
               'A tube 26 outside and 20 inside has Z = pi (26^4 - 20^4) / (32 x 26) = 1121 mm^3, so the bending stress is 27 '
               'MPa. The FEA peak, 33 MPa, is where the 45 degree tube meets the upright: the sharp corner adds about a fifth.')
CASES['ax_angle_bracket'] = dict(
    part='angle bracket', material=LM6,
    story='A 1 kN load (about 100 kg: a small motor or a pipe) sits on the 30 degree top plate. The base is bolted down through its four holes.',
    fixed=[dict(test=plane('z', 0), where='the underside of the base')],
    loads=[dict(kind='force', value=1000, dir=(0, 0, -1),
                test=lambda f: f['t'] == 'PLANE' and f['n'] is not None and near(f['n'][2], 0.866, 0.01) and near(f['n'][1], -0.5, 0.01)
                and f['a'] > 1500, where='the top face of the plate', how='Force, 1000 N, straight down')],
    hand_check='The column is a channel (a 7.9 mm back wall 47.6 wide and two 7.9 mm sides 27 deep): A = 804 mm^2, so the '
               'direct stress is 1000 / 804 = 1.2 MPa. The load sits about 4 mm in front of the centroid of the channel, which '
               'adds about 1 MPa of bending, so the column itself is lightly loaded. The FEA peak, 33 MPa, is somewhere else: '
               'at the front edge of each side wall, where it meets the underside of the plate overhang in a sharp 60 degree '
               'inside corner. The plate is held by the side walls and the back but not across the open front, so the load '
               'goes into the walls at their front edges. A sharp inside corner has no true peak (the finer the mesh, the '
               'higher it reads); a few millimetres away the FEA reads 15 MPa or less. Cast LM6 is weak (60 MPa proof), so the '
               'lowest safety factor is 1.8, and a fillet of R3 or more in those corners is worth adding.')
CASES['ax_crankshaft_4'] = dict(
    part='crankshaft', material=ALLOY_STEEL,
    story='Cylinder 2 fires: 6 MPa of gas pressure on an 86 mm piston (5809 mm^2) pushes its crank pin down with 35 kN. The five main '
          'journals sit in their bearings.', mesh_size=12,
    fixed=[dict(test=lambda f: cylinder(32)(f) and abs(f['c'][1]) < 1 and abs(f['c'][2]) < 1, where='the five main journals')],
    loads=[dict(kind='force', value=35000, dir=(0, 0, -1), test=lambda f: cylinder(32)(f) and near(f['c'][0], 300, 2) and f['c'][2] > 10,
                where='crank pin 2', how='Force, 35000 N, straight down')],
    hand_check='Pin 2 spans 114 mm between the centres of mains 2 and 3. Simply supported, M = F L / 4 = 35000 x 114 / 4 = '
               '997500 N mm; with the journals held, about half, 499000 N mm. The 64 mm pin has Z = pi x 64^3 / 32 = 25700 '
               'mm^3: 19 to 39 MPa. The FEA peak, 19 MPa, is the held figure: the webs and the main journals either side stop '
               'the pin bending like a free beam. It sits in the sharp corner where the pin meets a web (real crankshafts have '
               'fillets there).')
CASES['ax_crankshaft_3'] = dict(
    part='crankshaft', material=ALLOY_STEEL,
    story='Cylinder 1 fires: 6 MPa on a 5 in (127 mm) piston, 12670 mm^2, pushes crank pin 1 with 76 kN. The main journals and the '
          'front stub sit in bearings.', mesh_size=14, mesh_min=6, mesh_curvature=8,
    fixed=[dict(test=cylinder(31.75), where='the main journals and stubs')],
    loads=[dict(kind='force', value=76000, dir=(0, 0, -1), test=lambda f: cylinder(38.1)(f) and f['c'][0] < 180,
                where='crank pin 1', how='Force, 76000 N, straight down')],
    hand_check='Pin 1 (centre 136 mm along) sits between the front stub (centre 45) and main 1 (centre 209): a = 91, b = 73, L '
               '= 164. Simply supported, M = F a b / L = 76000 x 91 x 73 / 164 = 3.08 x 10^6 N mm. The 76.2 mm pin has Z = pi '
               'x 76.2^3 / 32 = 43400 mm^3, so 71 MPa; held journals bring this down towards half. The FEA peak, 40 MPa, is at '
               'the sharp corners where the journals either side of pin 1 meet the webs: a little over half the free beam '
               'figure, as expected with the journals held. The lowest safety factor is 17.')
CASES['ax_v_pulley'] = dict(
    part='V-belt pulley', material=GREY_IRON,
    story='The belt pulls on the groove with 2 kN in all (the tight side and the slack side together). The pulley is keyed on a '
          '0.75 in shaft.',
    fixed=[dict(test=cylinder(9.525), where='the 0.75 in bore')],
    loads=[dict(kind='force', value=2000, dir=(0, -1, 0), test=lambda f: f['t'] == 'CONE' and abs(f['c'][2]) < 12,
                where='the two flanks of the V groove', how='Force, 2000 N, towards the belt (-Y)')],
    hand_check='Bearing on the shaft = 2000 / (19.05 x 38.4) = 2.7 MPa. The 0.38 in web carries the pull as shear: on the hub '
               'circle (54 diameter) the web area is pi x 54 x 9.65 = 1640 mm^2, about 1.2 MPa. Pulleys are sized for '
               'stiffness, balance and casting, so the stresses are low. The FEA peak, 4 MPa, is in the web: the pulley could '
               'carry many times this pull.')
CASES['ax_pipe_run_valves'] = dict(
    part='body top valve', material=CAST_STEEL,
    story='Hydrostatic test of the top gate valve: 24 bar (2.4 MPa, 1.5 x PN16) inside, with its end flanges bolted to the pipe flanges.',
    fixed=[dict(test=lambda f: plane('x', 240, -1)(f) or plane('x', 420, 1)(f), where='the two end flange faces')],
    loads=[dict(kind='pressure', value=2.4,
                test=lambda f: cylinder(30)(f) or (f['t'] == 'PLANE' and 300 < f['c'][0] < 360 and abs(f['c'][1]) <= 38.5
                                                   and 800 < f['c'][2] < 925),
                where='the bore and the gate pocket', how='Pressure, 2.4 MPa')],
    hand_check='Hoop stress in the 60 mm bore (10 mm wall) = p r / t = 2.4 x 30 / 10 = 7.2 MPa. The flat sides of the gate '
               'pocket (24 wide, about 14 thick) bend: p b^2 / (2 t^2) = 2.4 x 24^2 / (2 x 14^2) = 3.5 MPa. Cast valve bodies '
               'are made thick for the casting and for pipe loads, not for pressure alone. In the middle of the pocket walls '
               'the FEA reads about 6 MPa, as these figures say. Its peak, 41 MPa, runs along the four sharp inside corners of '
               'the gate pocket. A sharp inside corner has no true peak (the finer the mesh, the higher it reads), and a real '
               'casting has a radius there. Even so, the lowest safety factor is 5.8.')
CASES['ax_steam_line_loop'] = dict(
    part='pipe support SP-101, tall', material=S275,
    story='The tall support carries the 6 in line near the ball valve: about 300 kg of pipe, water and valve, doubled for safety '
          'and for friction as the hot line grows: 6 kN down on the saddle.', mesh_size=12,
    fixed=[dict(test=plane('z', 0, -1), where='the underside of the base plate')],
    loads=[dict(kind='force', value=6000, dir=(0, 0, -1), test=cylinder(84.15), where='the saddle (cut to the 168.3 pipe)',
                how='Force, 6000 N, straight down')],
    hand_check='The 100 x 100 x 6 box column has A = 100^2 - 88^2 = 2256 mm^2: 6000 / 2256 = 2.7 MPa. Buckling (Euler, a free '
               'top so the effective length is 2 x 900 = 1800): I = (100^4 - 88^4) / 12 = 3.34 x 10^6 mm^4, P = pi^2 E I / L^2 '
               '= 2130 kN, over 350 times the load. Pipe supports are sized for stiffness and for knocks, not for the weight '
               'alone. The FEA peak, 17 MPa, is at the top of the column, where the ends of the saddle block sit on the column '
               'walls: sharp corners again, and still small.')
CASES['ax_oil_pan'] = dict(
    part='oil pan', material=A356,
    story='A common workshop mistake: a trolley jack is put under the sump. It lifts on the drain boss with 2 kN. The pan is bolted '
          'to the engine all round its flange.', mesh_size=10, mesh_min=4, mesh_curvature=8,
    fixed=[dict(test=cylinder(4.5), where='the 18 bolt holes')],
    loads=[dict(kind='force', value=2000, dir=(0, 0, 1),
                test=lambda f: f['t'] == 'PLANE' and f['n'] is not None and f['n'][2] < -0.99 and f['c'][2] < -170,
                where='the underside of the drain boss', how='Force, 2000 N, straight up')],
    hand_check='A point load on a 5 mm plate: for a round plate of radius a = 110 (the half width of the sump) loaded over the '
               '15 mm boss, sigma = 3 F (1 + nu) ln(a / r0) / (2 pi t^2) = 3 x 2000 x 1.33 x ln(110 / 15) / (2 pi x 25) = 101 '
               'MPa. That is over half the strength of A356-T6 from a small jack load, which is why you never jack a car on '
               'its sump. The FEA peak, 94 MPa, is in the floor of the sump right beside the drain boss, close to this figure. '
               'The floor lifts 0.8 mm and the lowest safety factor is 1.8.')
CASES['ax_engine_block'] = dict(
    part='cylinder block (deck)', material=GREY_IRON,
    story='Cylinder 2 at peak firing pressure, 6 MPa (60 bar), pushing out on its bore. The block sits on its bottom face.', mesh_size=22, mesh_min=12, mesh_curvature=6,
    fixed=[dict(test=plane('z', -180, -1), where='the bottom face of the block')],
    loads=[dict(kind='pressure', value=6.0, test=lambda f: cylinder(46.787)(f) and near(f['c'][0], -61.6, 2), where='the bore of cylinder 2',
                how='Pressure, 6 MPa')],
    hand_check='Where the water jacket surrounds it the bore wall is 8.5 mm thick (bore radius 46.8, jacket at 55.3): hoop '
               'stress = p r / t = 6 x 46.8 / 8.5 = 33 MPa. For a wall this thick the stress is highest at the bore (Lame): 6 '
               'x (55.3^2 + 46.8^2) / (55.3^2 - 46.8^2) = 36 MPa, and the FEA reads about 36 MPa on the bore. Its peak, 52 '
               "MPa, is where the wall is thinner: between the bores, where the next cylinder's water jacket comes within 6.6 "
               'mm of the bore, and beside the head bolt holes. Cast iron is strong enough (lowest safety factor 4.9), and a '
               'thin wall passes the heat to the water quickly.')
CASES['ax_helicopter'] = dict(
    part='cross tube front', material=ALUMINIUM,
    story='A firm landing at 2 g: a 1500 kg helicopter puts 1500 x 9.81 x 2 = 29.4 kN on its skids, 14.7 kN through each cross tube. '
          'The skids hold the ends of the legs.', mesh_size=12,
    fixed=[dict(test=plane('z', 80, -1), where='the bottom ends of the two legs (on the skids)')],
    loads=[dict(kind='force', value=14700, dir=(0, 0, -1), test=lambda f: cylinder(40)(f) and f['c'][2] > 500,
                where='the top of the cross tube (under the cabin)', how='Force, 14700 N, straight down')],
    hand_check='Treat the arched tube as a beam on two supports 1900 apart, loaded over the middle 1300: M = (F / 2) x (950 - '
               '1300 / 4) = 7350 x 625 = 4.6 x 10^6 N mm. For an 80 x 6 tube, I = pi (80^4 - 68^4) / 64 = 961000 mm^4 and Z = '
               '24000 mm^3, so the stress is up to 191 MPa; the stiff bends hold the ends, which brings it down. Skid gear is '
               'designed to bend (and so absorb energy) in a hard landing. The FEA peak, 85 MPa, is in the legs near the '
               'bends, well under the free beam figure, and the cross tube sags 5.7 mm. The lowest safety factor is 3.2.')
