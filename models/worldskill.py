"""World Skill: the parts from the WorldSkills UK Mechanical Engineering CAD pre-competition activity.

WorldSkills UK has published one practice paper for this competition from 2020 to 2026: the 2022
"Pre-Passive Activity: Part Modelling Speed Test" (1 hour, "create 3D models for all of the parts shown on the
part drawings"). It is still the activity the 2025 and 2026 technical handbooks point to:
https://www.worldskillsuk.org/wp-content/uploads/2022/02/Mechanical-Engineering-CAD-Pre-Passive-Activity-2022.pdf

Its two A3 sheets give four parts, all modelled here to the sizes on those sheets:
  sheet 1 of 5: crank (mild steel) and piston head (mild steel)
  sheet 2 of 5: pull cord grill (ABS) and cord case (PEEK)
Where a drawing leaves a size out, the size is scaled from the sheet and the step that uses it says so.

Every part is built feature by feature the way it would be in Autodesk Inventor (STEPS), so the Build steps tab
of the viewer can replay it. Units: mm, Z up, front view looks along +Y.
"""
import math
import cadquery as cq
from parts import STEEL, _box, _cyl
from library import (F, xcyl, ycyl, zcyl, zring, NEW_PART, SKETCH, EXTRUDE, REVOLVE, HOLE, FILLET,
                     CIRC)

FOLDER = 'World Skill'
SOURCE = ('WorldSkills UK Mechanical Engineering CAD, Pre-Passive Activity 2022 (Part Modelling Speed Test), '
          'sheet %s')
GRILL_ORANGE = 'F0904F'
PEEK_GREY = 'CDD1D6'
MILD_STEEL = STEEL


def _fillet(wp, r, pred):
    """Fillet the edges for which pred(edge) is true; if the kernel cannot do it, give the part back unchanged."""
    solid = wp.val()
    edges = [e for e in solid.Edges() if pred(e)]
    if not edges:
        return wp
    try:
        out = solid.fillet(r, edges)
        if out.isValid() and out.Volume() > 0.9 * solid.Volume():
            return cq.Workplane('XY').add(out)
    except Exception:
        pass
    return wp


def _circle_edge(e, radius, axis_val=None, axis='x', tol=0.05):
    if e.geomType() != 'CIRCLE':
        return False
    if abs(e.radius() - radius) > tol:
        return False
    if axis_val is None:
        return True
    c = e.Center()
    return abs(getattr(c, axis) - axis_val) < tol


def _rz(deg):
    return lambda w: w.rotate((0, 0, 0), (0, 0, 1), deg)


# ================================================================== 1 crank (sheet 1)
def crank():
    """Axis along X: the back face of the disc at x = 0, the shaft pointing along +X, the crank pin hole below the
    axis (-Z). Section A-A on the sheet is the XZ plane, so the hub's section A-A is the same cut."""
    PIN_Z = -15.8
    # 1. revolve the disc and shaft (one sketch on the XZ plane, revolved about the X axis)
    prof = [(0, 0), (0, 27.5), (11, 27.5), (11, 7.5), (31, 7.5), (43.5, 6.1), (44.5, 4.85), (44.5, 0)]
    c1 = cq.Workplane('XZ').polyline(prof).close().revolve(360, (0, 0, 0), (1, 0, 0))
    # 2. round the disc rim (R1.5 TYP. on the sheet)
    c2 = _fillet(c1, 1.5, lambda e: _circle_edge(e, 27.5))
    # 3. crescent recess on the back face: inside R24 about the pin, outside the 23.5 boss, 5.5 deep
    pocket = xcyl(24, -1, 5.5, 0, PIN_Z).cut(xcyl(23.5 / 2, -2, 6, 0, PIN_Z))
    c3 = c2.cut(pocket)
    c3f = _fillet(c3, 1.5, lambda e: e.geomType() == 'CIRCLE' and abs(e.Center().x - 5.5) < 0.05
                  and abs(e.radius() - 24) < 0.05)
    # 4. holes: 11 THRU for the crank pin, 4 THRU down the middle of the shaft
    c4 = c3f.cut(xcyl(5.5, -1, 12, 0, PIN_Z)).cut(xcyl(2.0, -1, 46))
    # 5. detail B: the face inside 40 is 0.2 below the rim, leaving a 20.5 land round the shaft
    c5 = c4.cut(xcyl(20, 10.8, 11.05).cut(xcyl(20.5 / 2, 10.7, 11.1)))
    # 6. key slot under the shaft: 1.8 wide, cut by an R6.6 circle 6.8 from the end and 11.1 below the axis
    c6 = c5.cut(ycyl(6.6, -0.9, 0.9, 44.5 - 6.8, -11.1))
    feats = [
        F('revolve the disc and shaft', REVOLVE,
          ['Start 2D Sketch on the XZ Plane. Draw half the profile above the X axis: the disc 55 diameter and 11 thick, '
           'the shaft 15 diameter to 31 from the back face, a taper to 12.2 at 43.5 and a 1.0 chamfer to 9.7 at 44.5 '
           '(overall length 44.5).',
           'Finish Sketch. Revolve: Profile = the half profile, Axis = the X axis, Full. OK.'], c1),
        F('round the rim', FILLET, ['Fillet: radius 1.5 (R1.5 TYP.), select the two rim edges of the 55 disc. OK.'], c2),
        F('crescent recess (counterweight)', EXTRUDE,
          ['Start 2D Sketch on the back face. Draw a circle R24 and a circle 23.5 diameter, both centred 15.8 below '
           'the axis (the crank pin centre).',
           'Finish Sketch. Extrude: Profile = the ring between the two circles, Cut, Distance 5.5. OK.',
           'Fillet R1.5 round the bottom of the recess. The full-thickness crescent left at the top is the '
           'counterweight.'], c3f),
        F('pin hole and centre hole', HOLE,
          ['Hole: Placement = Concentric with the 23.5 boss, Simple Hole, diameter 11, Termination Through All.',
           'Hole: Placement = on the axis of the shaft end, Simple Hole, diameter 4, Through All (it runs the whole '
           'length, see section A-A).'], c4),
        F('detail B face step', EXTRUDE,
          ['Start 2D Sketch on the front face of the disc (shaft side). Draw circles 40 and 20.5 diameter on the axis.',
           'Finish Sketch. Extrude: Profile = the ring between them, Cut, Distance 0.2 (detail B at 2:1).'], c5),
        F('key slot under the shaft', EXTRUDE,
          ['Start 2D Sketch on the XZ Plane. Draw a circle R6.6 with its centre 6.8 from the shaft end and 11.1 below '
           'the axis.',
           'Finish Sketch. Extrude: Profile = the circle inside the shaft, Cut, Symmetric, Distance 1.8 (the 1.8 slot '
           'in the end view). Save.'], c6,
          note='The sheet gives the R6.6 cutter position (6.8 and 11.1) and the slot width (1.8). It is a seat for a '
               'small key that drives whatever fits on the taper.'),
    ]
    return feats


# ================================================================== 2 piston head (sheet 1)
def piston_head():
    """Z up, crown at the top. The gudgeon pin axis runs along X so that section A-A of the hub (the XZ plane) is
    section C-C of the sheet, through the pin bosses. The end view of the hub is the sheet's front view."""
    SC = -18.5   # centre of the crown spheres: SR62.5 with its top at 44
    # 1. revolve the body: 44 diameter to 40 high, a SR62.5 crown to 44
    def arc_mid(R, r_end):
        a0 = math.atan2(math.sqrt(R * R - r_end * r_end), r_end)
        am = (a0 + math.pi / 2) / 2
        return (R * math.cos(am), SC + R * math.sin(am)), SC + math.sqrt(R * R - r_end * r_end)
    m1, z1 = arc_mid(62.5, 22)
    p1 = (cq.Workplane('XZ').moveTo(0, 0).lineTo(22, 0).lineTo(22, z1).threePointArc(m1, (0, SC + 62.5)).close()
          .revolve(360, (0, 0, 0), (0, 1, 0)))
    p2 = _fillet(p1, 1.0, lambda e: _circle_edge(e, 22, 40.0, 'z'))
    # 3. ring grooves: 2 wide, down to 40 diameter, 29.3 and 34.3 above the bottom
    p3 = p2.cut(zring(20, 23, 29.3, 31.3)).cut(zring(20, 23, 34.3, 36.3))
    # 4. hollow it: 38 bore up to a SR59.5 crown underside (3 mm crown, 3 mm wall)
    m2, z2 = arc_mid(59.5, 19)
    cav = (cq.Workplane('XZ').moveTo(0, -1).lineTo(19, -1).lineTo(19, z2).threePointArc(m2, (0, SC + 59.5)).close()
           .revolve(360, (0, 0, 0), (0, 1, 0)))
    p4 = p3.cut(cav)
    p4f = _fillet(p4, 3.0, lambda e: e.geomType() == 'CIRCLE' and abs(e.radius() - 19) < 0.05 and e.Center().z > 30)
    # 5. pin bosses: 17 diameter, 16 apart inside, on the pin axis 18.5 up
    boss = xcyl(8.5, 8, 21.9, 0, 18.5).union(xcyl(8.5, -21.9, -8, 0, 18.5)).intersect(zcyl(21.99, 0, 40))
    p5 = p4f.union(boss)
    p5f = _fillet(p5, 1.0, lambda e: e.geomType() == 'CIRCLE' and abs(e.radius() - 8.5) < 0.05
                  and abs(abs(e.Center().x) - 8) < 0.05)
    # 6. gudgeon pin hole 11 through both sides
    p6 = p5f.cut(xcyl(5.5, -30, 30, 0, 18.5))
    # 7. skirt cut-out: in the view along the pin, 24 wide and 10 high in the middle, then 41.2 degrees down to
    #    2 mm in from the outside; cut through all along the pin axis
    t = (20 - 12) * math.tan(math.radians(41.2))
    e = 20 + 2 * 8 / t   # carry the 41.2 degree line on below the bottom, so no corner of the cut sits on the bottom face
    top = 10 - 0.02      # the bosses touch z = 10 on a line; 0.02 lower keeps the kernel off that tangent contact
    pts = [(-e, -2), (-12, t), (-12, top), (12, top), (12, t), (e, -2)]
    cut = cq.Workplane('YZ').workplane(offset=-30).polyline(pts).close().extrude(60)
    p7 = p6.cut(cut)
    feats = [
        F('revolve the body and crown', REVOLVE,
          ['Start 2D Sketch on the XZ Plane. Half profile: 44 diameter, 40 high, then an arc SR62.5 to the top at '
           '44.0 on the axis.',
           'Finish Sketch. Revolve about the Z axis, Full. OK.'], p1),
        F('round the crown edge', FILLET, ['Fillet R1.0 (R1.0 TYP.) on the edge where the crown meets the 44 diameter.'], p2),
        F('ring grooves', REVOLVE,
          ['Start 2D Sketch on the XZ Plane. Two rectangles 2.0 high, from 44 diameter in to 40 diameter: the lower one '
           'from 29.3 to 31.3, the upper one 5.0 higher, from 34.3 to 36.3.',
           'Finish Sketch. Revolve: both rectangles, Cut, about the Z axis. OK.'], p3),
        F('hollow the inside', REVOLVE,
          ['Start 2D Sketch on the XZ Plane. Inside profile: 38 diameter from the bottom up to an arc SR59.5 '
           '(concentric with the SR62.5 crown, so the crown is 3.0 thick).',
           'Finish Sketch. Revolve, Cut, about the Z axis. Fillet R3.0 where the bore meets the crown underside.'], p4f),
        F('gudgeon pin bosses', EXTRUDE,
          ['Start 2D Sketch on a work plane through the axis. Circle 17 diameter, 18.5 above the bottom.',
           'Finish Sketch. Extrude from the inside wall to 8.0 from the centre (a 16.0 gap for the connecting rod), '
           'then Mirror to the other side. Fillet R1.0 round the boss ends.'], p5f),
        F('gudgeon pin hole', HOLE,
          ['Hole: Placement = Concentric with the boss, Simple Hole, diameter 11.0, Termination Through All '
           '(both walls).'], p6),
        F('skirt cut-outs', EXTRUDE,
          ['Start 2D Sketch on the YZ Plane (square on to the pin hole, as the front view on the sheet). Sketch the '
           'cut-out: 24.0 wide and 10.0 high in the middle, then lines at 41.2 degrees down to 2.0 in from the '
           'outside at the bottom.',
           'Finish Sketch. Extrude: Cut, Through All, Symmetric. OK. Save.'], p7,
          note='The cut-outs clear the crankshaft webs and make the piston lighter. Section C-C on the sheet is the '
               'section A-A of this model.'),
    ]
    return feats


# ================================================================== 3 pull cord grill (sheet 2)
def _bottom_dir(img_deg, r):
    """The sheet's grill plan is a view from underneath with the box at the top: image x = model X and image up =
    model -Y. Angles are measured anticlockwise on the sheet."""
    a = math.radians(img_deg)
    return (r * math.cos(a), -r * math.sin(a))


def pull_cord_grill():
    N = 23   # slots round the cage, counted on the sheet (15.65 degree pitch)
    # 1. revolve the cage, flange, cup and top in one profile
    a_r, b_r = 32.5, 32.5 - math.sqrt(36 - 25)
    ac = math.radians(56.44 + (90 - 56.44) / 2)
    mid = (b_r + 6 * math.cos(ac), 25 + 6 * math.sin(ac))
    prof = (cq.Workplane('XZ').moveTo(36.4, 0).lineTo(47.5, 0).lineTo(45.9, 4).lineTo(45.6, 4).lineTo(37.5, 30)
            .lineTo(a_r, 30).threePointArc(mid, (b_r, 31)).lineTo(0, 31).lineTo(0, 29).lineTo(35.5, 29)
            .lineTo(35.5, 21).lineTo(36.4, 21).close())
    g1 = prof.revolve(360, (0, 0, 0), (0, 1, 0))
    # 2. the boss under the top: 18 outside, 14 inside, 3.0 deep
    g2 = g1.union(zring(7, 9, 26, 29.01))
    # 3. the slots in the cage: 8.0 wide, radial, 23 of them
    slot = (_box(30, 50, -4, 4, 4, 21)
            .union(_box(30, 50, -4, 4, 21, 31).cut(zcyl(37.5, 20, 32)))
            .union(_box(30, 39.6, -4, 4, -1, 4.01)))
    slots = None
    for k in range(N):
        img = 90 + 360 * k / N                    # a slot at the top of the sheet's plan (90 degrees), ribs between
        x, y = _bottom_dir(img, 1)
        s = slot.rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(y, x)))
        slots = s if slots is None else slots.union(s)
    one = slot.rotate((0, 0, 0), (0, 0, 1), -90)
    g3 = g2.cut(slots)
    # 4. the cord box: 20 wide, 13.7 off centre, out to 50 from the centre, walls 2.0, full height
    outer = _box(13.7, 33.7, -50, -20, 0, 30).cut(zcyl(35.5, -1, 29))
    g4 = g3.union(outer)
    g5 = g4.cut(_box(15.7, 31.7, -48, -5, -1, 29))
    # 6. cord hole 6.0 through the 2.0 end wall, 10.0 in from the side and 15.0 up
    g6 = g5.cut(ycyl(3, -51, -47, 23.7, 15))
    # 7. three 4.0 holes in the flange on the 87.5 pitch circle
    g7 = g6
    for img in (90 + 31.3, 11.7, 270 - 23.5):
        x, y = _bottom_dir(img, 43.75)
        g7 = g7.cut(zcyl(2, -1, 5, x, y))
    feats = [
        F('revolve the body', REVOLVE,
          ['Start 2D Sketch on the XZ Plane. Half profile: the flange 95 diameter at the bottom, 4.0 thick, sloping in '
           'to the cone; the cone up to the 75 diameter cup at 29.0/30.0; the cup wall 71 inside from 21.0 up; the '
           'top 1.0 above the cup and the middle 65 diameter raised to 31.0 with an R6.0 edge.',
           'Inside the cone the profile is 72.8 diameter (the inner edge of the slots, 36.4 radius) down to the '
           'bottom; the flange is 80 inside.',
           'Finish Sketch. Revolve about the Z axis, Full. OK.'], g1),
        F('boss under the top', EXTRUDE,
          ['Start 2D Sketch on the underside of the top. Circles 18.0 and 14.0 diameter on the centre.',
           'Finish Sketch. Extrude the ring 3.0 down (Join).'], g2),
        F('cage slots', CIRC,
          ['Start 2D Sketch on the XY Plane. One radial slot 8.0 wide, centred on the line to the cord box.',
           'Finish Sketch. Extrude: Cut, from the flange up to the cup (21.0) through the cone, and up to the top '
           'outside the cup so the ribs stand proud of it.',
           'Circular Pattern: the slot cut, about the Z axis, 23 occurrences, 360 degrees. '
           'The rib pitch (15.65 degrees) and the slot width are scaled from the plan; the sheet gives 8.0.'],
          g3, overlay=one),
        F('cord box', EXTRUDE,
          ['Start 2D Sketch on the XY Plane. Rectangle 20.0 wide, its inner side 13.7 from the centre line, out to 50.0 '
           'from the centre. Finish Sketch. Extrude 30.0 (Join), stopping at the inside of the cup.'], g4),
        F('hollow the box', EXTRUDE,
          ['Start 2D Sketch on the bottom face. Offset the box outline in by 2.0 (wall 2.0, see the plan).',
           'Finish Sketch. Extrude: Cut, To the underside of the top. The box now opens into the cup.'], g5),
        F('cord hole', HOLE,
          ['Hole on the end face of the box: 10.0 from its side and 15.0 up. Simple Hole 6.0 diameter, Distance 2.0 '
           '(through the 2.0 wall).'], g6),
        F('flange holes', HOLE,
          ['Hole: 3 x 4.0 THRU in the flange on the 87.5 pitch circle, at 31.3 degrees, 11.7 degrees and 23.5 '
           'degrees from the centre lines, as on the plan. Save.'], g7,
          note='The plan on the sheet is a view from underneath, so its angles read anticlockwise from below.'),
    ]
    return feats


# ================================================================== 4 cord case (sheet 2)
def cord_case():
    """Z up. Built in the orientation of the sheet's plan (the cord box at -Y), then turned 90 degrees so the box
    points along -X: section A-A of the hub (the XZ plane) is then section E-E of the sheet, through the box."""
    turn = _rz(-90)
    # 1. revolve the body: base, cord groove, flange and tube
    prof = [(0, 0), (66.4 / 2, 0), (64.4 / 2, 7), (49.1 / 2, 7), (49.1 / 2, 15), (35, 15), (35, 17.5), (20, 17.5),
            (20, 40), (0, 40)]
    c1 = cq.Workplane('XZ').polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    # 2. bore of the tube (36 inside, 25.5 deep from the top) with the 16 hub standing 5.0 up from its floor
    c2 = c1.cut(zcyl(18, 14.5, 41)).union(zcyl(8, 14.4, 19.5))
    # 3. 14 hole through the middle
    c3 = c2.cut(zcyl(7, -1, 41))
    # 4. recess in the bottom: 64 diameter, 3.5 deep
    c4 = c3.cut(zcyl(32, -1, 3.5))
    # 5. 16 pockets in the bottom (R11 to R19, 1.0 deep) between spokes on 22.5 degree centres, and a groove
    #    R19 to R20, 5.5 deep
    ring = zring(11, 19, 3.4, 4.5)
    spokes = None
    for k in range(16):
        img = 90 - 4.1 + 11.25 + 22.5 * k        # bottom view: the first pocket 4.1 degrees off the centre line
        a = -img                                   # bottom view to model (image up = model -Y)
        s = _box(9, 22, -0.75, 0.75, 3, 5).rotate((0, 0, 0), (0, 0, 1), a)
        spokes = s if spokes is None else spokes.union(s)
    pockets = ring.cut(spokes)
    c5 = c4.cut(pockets).cut(zring(19, 20, 3.4, 9.0))
    # 6. six gussets on the flange: 12.0 long, 3.0 high, 2.5 thick, 60 degrees apart (29.6 from the centre line)
    rib = (cq.Workplane('XZ').polyline([(19.8, 17.5), (32, 17.5), (19.8, 20.5)]).close().extrude(1.25, both=True))
    ribs = None
    for k in range(6):
        r = rib.rotate((0, 0, 0), (0, 0, 1), 90 - 29.6 + 60 * k)
        ribs = r if ribs is None else ribs.union(r)
    c6 = c5.union(ribs)
    # 7. the cord guide: walls 1.7 thick, 17.5 wide, 10.0 high, its end on R30.3 / R32.0
    end = zring(30.3, 32, 17.5, 27.5).intersect(_box(-8.75, 8.75, -40, 0, 17, 28))
    sides = (_box(7.05, 8.75, -31.5, -18, 17.5, 27.5).union(_box(-8.75, -7.05, -31.5, -18, 17.5, 27.5))
             .intersect(zcyl(31, 17, 28)))
    c7 = c6.union(end).union(sides)
    # 8. 4.0 hole 2.5 deep in the flange inside the guide, 27.4 from the centre
    c8 = c7.cut(zcyl(2, 15, 17.6, 0, -27.4))
    feats = [
        F('revolve the body', REVOLVE,
          ['Start 2D Sketch on the XZ Plane. Half profile: base 64.4 diameter at 7.0 (drafted out to the bottom), the '
           'cord groove 49.1 diameter from 7.0 to 15.0, the flange 70 diameter from 15.0 to 17.5, then the tube '
           '40 diameter up to 40.0.',
           'Finish Sketch. Revolve about the Z axis, Full. OK.'], turn(c1)),
        F('bore and hub', REVOLVE,
          ['Revolve Cut the 36 bore 25.5 deep from the top, then Revolve (Join) the 16 hub 5.0 up from the floor of '
           'the bore.'], turn(c2)),
        F('centre hole', HOLE, ['Hole: Concentric, Simple Hole, diameter 14.0, Through All.'], turn(c3)),
        F('recess in the bottom', EXTRUDE,
          ['Start 2D Sketch on the bottom face. Circle 64.0. Finish Sketch. Extrude: Cut, 3.5.'], turn(c4)),
        F('pockets and groove in the bottom', CIRC,
          ['Start 2D Sketch on the floor of the recess. One pocket between R11.0 and R19.0, bounded by two spokes; '
           'its centre line 4.1 degrees off the vertical centre line (detail F).',
           'Finish Sketch. Extrude: Cut 1.0. Circular Pattern: 16 occurrences (22.5 degree centres).',
           'Sketch the ring R19.0 to R20.0 and Extrude: Cut 5.5 from the bottom of the recess.'], turn(c5),
          note='The spoke width (1.5) is scaled from detail F; the sheet gives the 22.5 degree and 6.3 centres.'),
        F('gussets on the flange', CIRC,
          ['Start 2D Sketch on a work plane through the axis. Triangle 12.0 long on the flange and 3.0 high on the tube.',
           'Finish Sketch. Extrude 2.5 Symmetric (Join). Circular Pattern: 6 occurrences, 60 degrees apart, the first '
           '29.6 degrees from the centre line.'], turn(c6)),
        F('cord guide', EXTRUDE,
          ['Start 2D Sketch on the flange top. The guide: two side walls 1.7 thick, 17.5 wide over the walls, from '
           'the tube out to the end wall between R30.3 and R32.0.',
           'Finish Sketch. Extrude 10.0 (Join).'], turn(c7)),
        F('hole in the guide', HOLE,
          ['Hole on the flange top inside the guide, 27.4 from the centre: Simple Hole 4.0, Distance 2.5. Save.'],
          turn(c8)),
    ]
    return feats


# ------------------------------------------------------------------ the catalogue entries
PARTS = [
    dict(name='ws2022_crank', title='WorldSkills 2022: crank', fn=crank, colour=MILD_STEEL, sheet='1 of 5',
         material='Mild steel', section='y', iso=(1.2, -1.0, 0.8),
         description='The crank from sheet 1 of the WorldSkills UK 2022 part modelling speed test: a 55 diameter disc '
                     'with a counterweight crescent on the back, an 11 crank pin hole 15.8 off centre, a 15 shaft with a '
                     'taper and key slot, and a 4 hole down the middle. Mild steel.',
         uses='Revolve, offset holes, a recess left by two circles, a detail view at 2:1, section A-A through the pin '
              'hole and shaft.'),
    dict(name='ws2022_piston_head', title='WorldSkills 2022: piston head', fn=piston_head, colour=MILD_STEEL,
         sheet='1 of 5', material='Mild steel', section='y', iso=(1, -1.2, 0.9),
         description='The piston head from sheet 1: 44 diameter, 44 high, an SR62.5 crown 3.0 thick, two ring '
                     'grooves, pin bosses 17 diameter with an 11 pin hole, and skirt cut-outs at 41.2 degrees. '
                     'Mild steel.',
         uses='Revolved profiles, spherical faces, ring grooves, bosses and a cut through all; section A-A is section '
              'C-C on the sheet.'),
    dict(name='ws2022_pull_cord_grill', title='WorldSkills 2022: pull cord grill', fn=pull_cord_grill,
         colour=GRILL_ORANGE, sheet='2 of 5', material='ABS plastic', section='y', iso=(1, -1.1, 0.9),
         description='The pull cord grill from sheet 2: a 75 diameter cup on a slotted cone down to a 95 flange with '
                     'three 4.0 holes, a cord box 20 wide with a 6.0 cord hole, and a boss under the top. ABS plastic, '
                     'smooth, light orange.',
         uses='A moulded plastic part: revolve, a circular pattern of slots, a hollow box with 2.0 walls and holes on '
              'a pitch circle; section A-A is section D-D on the sheet.'),
    dict(name='ws2022_cord_case', title='WorldSkills 2022: cord case', fn=cord_case, colour=PEEK_GREY,
         sheet='2 of 5', material='PEEK plastic', section='y', iso=(-1, -1.2, 0.9),
         description='The cord case (recoil starter pulley) from sheet 2: a 49.1 cord groove between a 64.4 base and '
                     'a 70 flange, a 40 tube with a 16 hub, a cord guide, six gussets and 16 pockets in the bottom. '
                     'PEEK plastic.',
         uses='Revolve, a pattern of pockets on the underside, gussets and a cord guide; section A-A is section E-E on '
              'the sheet.'),
]


def _items(p):
    return lambda: [(p['title'].split(': ')[1], p['fn']()[-1]['shape'], p['colour'])]


def _steps(p):
    def go():
        feats = p['fn']()
        name = p['title'].split(': ')[1]
        file = p['name'].replace('ws2022_', '') + '.ipt'
        out = []
        for k, f in enumerate(feats):
            acts = list(f['actions'])
            if k == 0:
                acts = [NEW_PART + ' and save it as %s.' % file] + acts
            if k == len(feats) - 1 and not acts[-1].endswith('Save.'):
                acts.append('Save %s.' % file)
            out.append(dict(title='%s: %s' % (name[0].upper() + name[1:], f['title']), command=f['command'],
                            actions=acts, parts=[(name, f['shape'], p['colour'])], overlay=f.get('overlay'),
                            note=f.get('note')))
        return out
    return go


MODELS = [dict(name=p['name'], title=p['title'], folder=FOLDER, fn=_items(p), criteria='3.1, 3.2', uses=p['uses'],
               description=p['description'], section=p['section'], explode=None, iso=p['iso'], fea=False,
               source=SOURCE % p['sheet'], material=p['material'])
          for p in PARTS]
STEPS = {p['name']: _steps(p) for p in PARTS}
MATERIAL = {p['name']: p['material'] for p in PARTS}
