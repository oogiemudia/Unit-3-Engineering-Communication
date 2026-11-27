"""CG 3.2 drawings: CAD models of the drawings in the City and Guilds Unit 3 resources for criterion 3.2.

Rahima (27 November 2026): learners are beginners, so the 3.2 lessons should show each City and Guilds drawing as a
real CAD model and how it is built, not only the hub's existing models. Every drawing in Unit 3 PowerPoint 7
(dimensions), PowerPoint 8 (limits and fits), PowerPoint 9 (geometric tolerances) and Worksheets 13, 14 and 15 that
shows a part is modelled here:

  PPT 7 slide 3   projection line block (45 long)          PPT 7 slides 4 to 7  slotted bar (the four arrangements)
  PPT 7 slide 9   radius plate (a, b) and domed pin (c)     PPT 7 slide 11       10 plate (dimensioning practice)
  PPT 7 slide 12  vee notch plate                           PPT 8 + Worksheet 14 three hole and shaft fits
  PPT 9 slide 5   stepped shaft (120 +/-2)                  PPT 9 slide 6 + WS15 flanged locator (inch drawing)
  Worksheet 13    bracket, hanger bracket and clevis bracket

Where a slide shows a shape without sizes, the sizes are scaled from the slide and the model note says so. The inch
drawing is converted to millimetres (x 25.4). Fits are modelled at the nominal size: the tolerance class sets the
fit, as it does in Inventor (the limits are in the description and on the drawing note).

Every part is built feature by feature the way it would be in Autodesk Inventor (STEPS), so the Build steps tab of the
viewer, and the build video, replay it. Units: mm, Z up, front view looks along +Y.
"""
import math
import cadquery as cq
from parts import STEEL, ALU, BRASS
from library import (F, xcyl, ycyl, zcyl, NEW_PART, NEW_ASSY, SKETCH, EXTRUDE, REVOLVE, HOLE, FILLET, CHAMFER,
                     PLACE, CONSTRAIN)

FOLDER = 'CG 3.2 drawings'
SOURCE = 'City and Guilds T Level Engineering, Unit 3 (criterion 3.2), %s'
MILD = STEEL
HOUSING = '8A96A8'


# ------------------------------------------------------------------ helpers
def prism(pts, y0, y1):
    """A profile drawn on the front (XZ) plane, extruded from y0 to y1."""
    return cq.Workplane('XZ').polyline(pts).close().extrude(y1 - y0).translate((0, y1, 0))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def _edges_fillet(wp, r, pred, chamfer=False):
    """Fillet (or chamfer) the edges for which pred(edge) is true; give the part back unchanged if the kernel fails."""
    solid = wp.val()
    edges = [e for e in solid.Edges() if pred(e)]
    if not edges:
        raise ValueError('no edges for fillet r=%s' % r)
    out = solid.chamfer(r, None, edges) if chamfer else solid.fillet(r, edges)
    assert out.isValid(), 'invalid after fillet'
    return cq.Workplane('XY').add(out)


def y_edge_at(x, z, tol=0.05):
    """A straight edge running along Y through (x, z)."""
    def p(e):
        if e.geomType() != 'LINE':
            return False
        a, b = e.startPoint(), e.endPoint()
        return abs(a.x - x) < tol and abs(b.x - x) < tol and abs(a.z - z) < tol and abs(b.z - z) < tol
    return p


def z_edge_at(x, y, tol=0.05):
    def p(e):
        if e.geomType() != 'LINE':
            return False
        a, b = e.startPoint(), e.endPoint()
        return abs(a.x - x) < tol and abs(b.x - x) < tol and abs(a.y - y) < tol and abs(b.y - y) < tol
    return p


def circle_at(r, axis, val, tol=0.05):
    def p(e):
        if e.geomType() != 'CIRCLE' or abs(e.radius() - r) > tol:
            return False
        return abs(getattr(e.Center(), axis) - val) < tol
    return p


# ================================================================== PPT 7 slide 3: projection line block
def projection_block():
    b1 = box(0, 45, 0, 20, 0, 25)
    b2 = b1.cut(box(20, 46, -1, 21, 19, 26))
    return [
        F('extrude the block', EXTRUDE,
          ['Start 2D Sketch on the XY Plane (the front). Draw a rectangle 45 wide and 25 high, corner on the origin. '
           'Add the 45 and 25 dimensions with the Dimension tool.',
           'Finish Sketch. Extrude: Profile = the rectangle, Distance 20. OK.'], b1),
        F('cut the step', EXTRUDE,
          ['Start 2D Sketch on the front face. Draw a rectangle from 20 along the top edge to the right end, 6 deep.',
           'Finish Sketch. Extrude: Profile = the rectangle, Cut, Through All. OK. Save.'], b2,
          note='Only the 45 is given on the slide; the 25 height, the 20 x 6 step and the 20 depth are scaled from it.'),
    ]


# ================================================================== PPT 7 slides 4 to 7: slotted bar
SLOT_W = [17, 25, 21, 15, 28, 14]        # widths of the six bottom steps, left to right (total 120)
SLOT_Z = [6, 14, 0, 18, 4, 22]           # height of each bottom step above the lowest point


def slotted_bar():
    feats = []
    b = box(0, 120, 0, 25, 0, 48)
    feats.append(F('extrude the bar', EXTRUDE,
                   ['Start 2D Sketch on the XY Plane (the front). Draw a rectangle 120 long and 48 high, corner on the '
                    'origin.', 'Finish Sketch. Extrude: Profile = the rectangle, Distance 25. OK.'], b))
    x = 0
    k = 0
    for w, z in zip(SLOT_W, SLOT_Z):
        if z > 0:
            k += 1
            b = b.cut(box(x - (0.01 if x == 0 else 0), x + w + (0.01 if x + w == 120 else 0), -1, 26, -1, z))
            feats.append(F('cut step %d (%g wide, %g up)' % (k, w, z), EXTRUDE,
                           ['Start 2D Sketch on the front face. Draw a rectangle %g wide and %g high on the bottom edge, '
                            'starting %g from the left end.' % (w, z, x),
                            'Finish Sketch. Extrude: Profile = the rectangle, Cut, Through All. OK.'], b))
        x += w
    feats[-1]['actions'].append('Save.')
    feats[-1]['note'] = ('The slides show this bar with no numbers (they teach the arrangement, not the sizes). The 120 '
                         'length and the step sizes are scaled from slide 7. On the drawing it is dimensioned four ways: '
                         'parallel, running, chain and combined.')
    return feats


# ================================================================== PPT 7 slide 9: radius plate (a and b)
def radius_plate():
    p1 = box(0, 60, 0, 10, 0, 40)
    p2 = _edges_fillet(p1, 5, y_edge_at(0, 40))
    p3 = p2.cut(ycyl(15, -1, 11, 60, 40))
    # (b): the R15 hollow blends into the top and the side with R5 rounds
    p4 = _edges_fillet(p3, 5, lambda e: y_edge_at(45, 40)(e) or y_edge_at(60, 25)(e))
    return [
        F('extrude the plate', EXTRUDE,
          ['Start 2D Sketch on the XY Plane. Draw a rectangle 60 by 40.', 'Finish Sketch. Extrude: Distance 10. OK.'], p1),
        F('R5 corner (slide 9 a)', FILLET,
          ['Fillet: Radius 5, select the top left edge (the one through the thickness). OK.',
           'On the drawing this is dimensioned R5 with one arrowhead, from the centre of the arc.'], p2),
        F('R15 hollow', EXTRUDE,
          ['Start 2D Sketch on the front face. Draw a circle R15 centred on the top right corner.',
           'Finish Sketch. Extrude: Profile = the quarter circle inside the plate, Cut, Through All. OK.'], p3),
        F('R5 blends (slide 9 b)', FILLET,
          ['Fillet: Radius 5, select the two sharp edges where the R15 hollow meets the top and the side. OK. Save.',
           'The edge now runs R5 into R15: the reverse curve of slide 9 (b).'], p4,
          note='Slide 9 shows (a) and (b) as separate sketches with no overall sizes; they are put on one 60 x 40 x 10 '
               'plate here so learners can see both.'),
    ]


# ================================================================== PPT 7 slide 9 (c): domed pin
def domed_pin():
    L, R, SR = 50.0, 12.0, 30.0
    c = L - math.sqrt(SR * SR - R * R)
    p1 = xcyl(R, 0, L)
    mid = (c + SR * math.cos(math.asin(R / SR) / 2), SR * math.sin(math.asin(R / SR) / 2))

    def turned(ch):
        w = cq.Workplane('XY').moveTo(0, 0)
        w = w.lineTo(0, R - ch).lineTo(ch, R) if ch else w.lineTo(0, R)
        return w.lineTo(L, R).threePointArc(mid, (c + SR, 0)).close().revolve(360, (0, 0, 0), (1, 0, 0))
    p2 = turned(0)
    p3 = turned(1)
    return [
        F('extrude the pin', EXTRUDE,
          ['Start 2D Sketch on the YZ Plane (the end). Draw a circle 24 diameter on the origin.',
           'Finish Sketch. Extrude: Distance 50. OK.'], p1),
        F('spherical end SR30', REVOLVE,
          ['Start 2D Sketch on the XY Plane. Draw an arc of radius 30 across the end face, its centre on the axis, '
           'from the top edge to the bottom edge of the pin, and close it with a line down the end face.',
           'Finish Sketch. Revolve: Profile = the dome, Axis = the pin axis, Full, Join. OK.',
           'On the drawing this is SR30: S for spherical, R for radius.'], p2),
        F('chamfer the other end', CHAMFER,
          ['Chamfer: Distance 1, select the circular edge at the flat end. OK. Save.'], p3,
          note='Only SR30 is given on slide 9 (c); the 24 diameter and 50 length are scaled from the slide.'),
    ]


# ================================================================== PPT 7 slide 11: the 10 plate
def ten_plate():
    p1 = box(0, 75, 0, 10, 0, 45)
    p2 = p1.cut(box(-1, 10, -1, 11, 40, 46))
    p3 = p2.cut(box(59, 76, -1, 11, 23, 46))
    p4 = _edges_fillet(p3, 10, y_edge_at(59, 23))
    p5 = _edges_fillet(p4, 12, y_edge_at(75, 0), chamfer=True)
    p6 = p5.cut(ycyl(5, -1, 11, 10, 10))
    return [
        F('extrude the 10 plate', EXTRUDE,
          ['Start 2D Sketch on the XY Plane. Draw a rectangle 75 by 45.', 'Finish Sketch. Extrude: Distance 10 '
           '(the leader note says 10 PLATE). OK.'], p1),
        F('cut the 10 x 5 step', EXTRUDE,
          ['Start 2D Sketch on the front face. Draw a rectangle 10 wide and 5 deep at the top left corner.',
           'Finish Sketch. Extrude: Cut, Through All. OK. The left edge is now 40 high.'], p2),
        F('cut the corner notch', EXTRUDE,
          ['Start 2D Sketch on the front face. Draw a rectangle from 59 along the top (10 + 49) to the right end, '
           'down to 23 above the base (12 + 11).', 'Finish Sketch. Extrude: Cut, Through All. OK.'], p3),
        F('R10 in the notch', FILLET,
          ['Fillet: Radius 10, select the inside corner edge of the notch. OK.'], p4),
        F('chamfer the corner 12 x 45 degrees', CHAMFER,
          ['Chamfer: Equal distance 12, select the bottom right edge. OK. The angle between the chamfer and the base is '
           '135 degrees, as dimensioned.'], p5),
        F('hole 10 diameter', HOLE,
          ['Hole: Placement = on the front face, 10 from the left and 10 from the bottom. Simple hole, diameter 10, '
           'Through All. OK. Save.'], p6),
    ]


# ================================================================== PPT 7 slide 12: vee notch plate
def notch_plate():
    p1 = box(0, 90, 0, 10, 0, 50)
    p2 = _edges_fillet(p1, 20, y_edge_at(0, 50))
    p3 = _edges_fillet(p2, 10, y_edge_at(90, 50))
    p4 = p3.cut(box(-1, 20, -1, 11, -1, 10))
    xa = 30 + 10 * math.tan(math.radians(30))
    p5 = p4.cut(prism([(30, 50), (xa, 40), (45, 50), (46, 55), (29, 55)], -1, 11))
    p6 = p5.cut(ycyl(5, -1, 11, 75, 15))
    return [
        F('extrude the plate', EXTRUDE,
          ['Start 2D Sketch on the XY Plane. Draw a rectangle 90 by 50.', 'Finish Sketch. Extrude: Distance 10. OK.'], p1),
        F('R20 corner', FILLET, ['Fillet: Radius 20, select the top left edge. OK.'], p2),
        F('R10 corner', FILLET, ['Fillet: Radius 10, select the top right edge. OK.'], p3),
        F('cut the 20 x 10 step', EXTRUDE,
          ['Start 2D Sketch on the front face. Draw a rectangle 20 wide and 10 high at the bottom left corner.',
           'Finish Sketch. Extrude: Cut, Through All. OK.'], p4),
        F('cut the vee notch', EXTRUDE,
          ['Start 2D Sketch on the front face. Draw the vee: 15 wide on the top edge, starting 30 from the left, 10 '
           'deep, with its left side at 30 degrees to the vertical.',
           'Finish Sketch. Extrude: Cut, Through All. OK.'], p5),
        F('hole 10 diameter', HOLE,
          ['Hole: Placement = on the front face, 15 from the right end (75 from the left) and 15 above the base. '
           'Simple hole, diameter 10, Through All. OK. Save.'], p6,
          note='The 10 thickness is assumed (the slide shows one view only).'),
    ]


# ================================================================== PPT 8 + Worksheet 14: hole and shaft fits
FITS = {
    'clearance': dict(d=42.0, code='H9/d10', hole=(42.000, 42.062), shaft=(41.820, 41.920),
                      slide='PowerPoint 8 slides 4 and 5, Worksheet 14 (42 H9 d10)'),
    'transition': dict(d=57.0, code='H7/n6', hole=(57.000, 57.030), shaft=(57.020, 57.039),
                       slide='PowerPoint 8 slides 8 and 9, Worksheet 14 (57 H7 n6)'),
    'interference': dict(d=80.0, code='H7/s6', hole=(80.000, 80.030), shaft=(80.059, 80.078),
                         slide='PowerPoint 8 slides 6 and 7, Worksheet 14 (80 H7 s6)'),
}


def fit_parts(kind):
    f = FITS[kind]
    r = f['d'] / 2
    hl = 40.0
    h1 = ycyl(r + 15, 0, hl)
    h2 = h1.cut(ycyl(r, -1, hl + 1))
    h3 = _edges_fillet(h2, 1, lambda e: circle_at(r, 'y', 0)(e) or circle_at(r, 'y', hl)(e), chamfer=True)
    s1 = ycyl(r, hl / 2, hl / 2 + 120)
    s2 = _edges_fillet(s1, 1.5, circle_at(r, 'y', hl / 2), chamfer=True)
    return h1, h2, h3, s1, s2


def fit_steps(kind):
    f = FITS[kind]
    h1, h2, h3, s1, s2 = fit_parts(kind)
    d = '%g' % f['d']
    hole = 'hole %.3f to %.3f' % f['hole']
    shaft = 'shaft %.3f to %.3f' % f['shaft']
    H = ('Housing', HOUSING)
    S = ('Shaft', STEEL)
    return [
        dict(part=H, f=F('housing: extrude the collar', EXTRUDE,
                         ['%s and save it as housing.ipt.' % NEW_PART,
                          'Start 2D Sketch on the XZ Plane. Draw a circle %g diameter on the origin.' % (f['d'] + 30),
                          'Finish Sketch. Extrude: Distance 40. OK.'], h1)),
        dict(part=H, f=F('housing: the bore, %s %s' % (d, f['code'].split('/')[0]), HOLE,
                         ['Hole: Placement = Concentric on the end face, Simple hole, diameter %s, Through All.' % d,
                          'Tolerance: in the Hole dialog (or on the drawing) set the fit class %s: %s. The model is '
                          'made at the nominal %s; the limits go on the drawing.' % (f['code'].split('/')[0], hole, d)],
                         h2)),
        dict(part=H, f=F('housing: chamfer the bore', CHAMFER,
                         ['Chamfer: Distance 1, select both bore edges (a lead in for the shaft). OK. Save.'], h3)),
        dict(part=S, f=F('shaft: extrude %s %s' % (d, f['code'].split('/')[1]), EXTRUDE,
                         ['%s and save it as shaft.ipt.' % NEW_PART,
                          'Start 2D Sketch on the XZ Plane. Draw a circle %s diameter.' % d,
                          'Finish Sketch. Extrude: Distance 120. OK.',
                          'Tolerance: %s, so the %s. Modelled at the nominal %s.' % (f['code'].split('/')[1], shaft, d)],
                         s1)),
        dict(part=S, f=F('shaft: chamfer the lead end', CHAMFER,
                         ['Chamfer: Distance 1.5, select the circular edge at the lead end. OK. Save.'], s2)),
        dict(part=None, f=F('assemble: shaft into housing', PLACE,
                            ['%s and save it as fit_%s.iam.' % (NEW_ASSY, kind),
                             'Place housing.ipt (grounded) and shaft.ipt.',
                             'Constrain: Insert, the shaft chamfer edge to the bore edge, offset 20 (half way in). OK.',
                             'Inspect tab > Analyze Interference shows none, because both parts are at the nominal '
                             'size. The real fit (%s) comes from the tolerances: use Design tab > Limits/Fits '
                             'Mechanical to check it. Save.' % kind], s2)),
    ]


# ================================================================== PPT 9 slide 5: stepped shaft 120 +/- 2
def stepped_shaft():
    s1 = xcyl(27.5, 0, 50)
    s2 = s1.union(xcyl(20, 50 - 0.01, 120))
    s3 = _edges_fillet(s2, 1, lambda e: circle_at(27.5, 'x', 0)(e) or circle_at(20, 'x', 120)(e), chamfer=True)
    return [
        F('extrude the 55 diameter', EXTRUDE,
          ['Start 2D Sketch on the YZ Plane (the end). Draw a circle 55 diameter on the origin.',
           'Finish Sketch. Extrude: Distance 50 (50 +/- 1 on the drawing). OK.'], s1),
        F('extrude the 40 diameter', EXTRUDE,
          ['Start 2D Sketch on the end face. Draw a circle 40 diameter, concentric.',
           'Finish Sketch. Extrude: Distance 70 (70 +/- 1), Join. OK. Overall 120 (120 +/- 2).'], s2),
        F('chamfer both ends', CHAMFER,
          ['Chamfer: Distance 1, select the two end edges. OK. Save.'], s3,
          note='PowerPoint 9 slide 5 gives the lengths 50 +/- 1, 70 +/- 1 and 120 +/- 2 but no diameters; 55 and 40 '
               'are scaled from the slide.'),
    ]


# ================================================================== PPT 9 slide 6 + Worksheet 15: flanged locator (inches)
IN = 25.4


def flanged_locator():
    R = 1.000 * IN
    t = 0.375 * IN
    bl = 0.500 * IN
    f1 = ycyl(R, 0, t)
    f2 = f1.union(ycyl(0.500 * IN, t - 0.01, t + bl))
    f3 = f2.cut(ycyl(0.250 * IN, -1, t + bl + 1))
    pcd = 0.750 * IN
    f4 = f3
    for a in (0, 180, 270):
        x, z = pcd * math.cos(math.radians(a)), pcd * math.sin(math.radians(a))
        f4 = f4.cut(ycyl(0.125 * IN, -1, t + 1, x, z))
    w = 0.380 * IN
    f5 = f4.cut(box(-w / 2, w / 2, -1, t + 0.001, 0.750 * IN, R + 1))
    return [
        F('extrude the flange', EXTRUDE,
          ['Start 2D Sketch on the XZ Plane (the front). Draw a circle 2.000 in (50.8 mm) diameter on the origin.',
           'Finish Sketch. Extrude: Distance 0.375 in (9.53 mm). OK.'], f1),
        F('extrude the boss', EXTRUDE,
          ['Start 2D Sketch on the back face. Draw a circle 1.000 in (25.4 mm) diameter, concentric.',
           'Finish Sketch. Extrude: Distance 0.500 in (12.7 mm), Join. OK.'], f2),
        F('centre bore', HOLE,
          ['Hole: Concentric on the front face, diameter 0.500 in (12.7 mm), Through All. OK.'], f3),
        F('three holes on the pitch circle', HOLE,
          ['Start 2D Sketch on the front face. Draw a construction circle 1.500 in (38.1 mm) diameter. Put hole '
           'centres on it at 3, 6 and 9 o\'clock.',
           'Finish Sketch. Hole: From Sketch, diameter 0.250 in (6.35 mm), Through the flange. OK.'], f4),
        F('slot at the top', EXTRUDE,
          ['Start 2D Sketch on the front face. Draw a rectangle 0.380 in (9.65 mm) wide, centred on the vertical '
           'centre line, from the rim down to 0.750 in (19.05 mm) above the centre.',
           'Finish Sketch. Extrude: Cut, Distance = the flange thickness. OK. Save.'], f5,
          note='The City and Guilds drawing is in inches; each size is converted (x 25.4). The upper limit of each size '
               'is used (2.000, 1.000, 0.500). The GDT frames (perpendicularity, position, parallelism, flatness) go '
               'on the drawing, not in the model.'),
    ]


# ================================================================== Worksheet 13: bracket
def ws13_bracket():
    b1 = box(0, 100, 0, 120, 0, 20)
    up = box(0, 100, 70, 120, 0, 75).union(xcyl(25, 0, 100, 95, 75))
    b2 = b1.union(up)
    b3 = b2.cut(xcyl(10, -1, 101, 95, 75))
    b5 = b3.cut(zcyl(7.5, -1, 21, 80, 20))
    return [
        F('extrude the base', EXTRUDE,
          ['Start 2D Sketch on the XY Plane. Draw a rectangle 100 wide and 120 deep.',
           'Finish Sketch. Extrude: Distance 20. OK.'], b1),
        F('extrude the upright', EXTRUDE,
          ['Start 2D Sketch on the side (YZ) plane. Draw the upright: 50 thick at the back of the base, up to 75, with '
           'an R25 arc on top centred 75 up.', 'Finish Sketch. Extrude: Distance 100, Join. OK.'], b2),
        F('hole R10 through the upright', HOLE,
          ['Hole: Concentric with the R25 arc, diameter 20 (R10), Through All. OK.'], b3),
        F('hole R7.5 in the base', HOLE,
          ['Hole: Placement = on the top of the base, 20 from the front and 20 from the right end, diameter 15 '
           '(R7.5), Through All. OK. Save.'], b5,
          note='The worksheet drawing is first angle (the plan is below the front view), so the upright is at the back. '
               'Its R20 marks the hole position 20 from the corner: the pictorial view shows a square corner.'),
    ]


# ================================================================== Worksheet 13: hanger bracket
def _tangent(px, pz, cx, cz, r, side):
    """The point where a line from (px, pz) touches the circle (cx, cz, r) on the given side (+1 right, -1 left)."""
    dx, dz = px - cx, pz - cz
    d = math.hypot(dx, dz)
    a = math.atan2(dz, dx)
    b = math.acos(r / d)
    t = a - b if side > 0 else a + b
    return cx + r * math.cos(t), cz + r * math.sin(t)


def _offset_line(p, q, dist, inward):
    """Line p-q moved dist towards the point inward."""
    dx, dz = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dz)
    nx, nz = -dz / L, dx / L
    if (inward[0] - p[0]) * nx + (inward[1] - p[1]) * nz < 0:
        nx, nz = -nx, -nz
    return (p[0] + nx * dist, p[1] + nz * dist), (q[0] + nx * dist, q[1] + nz * dist)


def _meet(l1, l2):
    (x1, z1), (x2, z2) = l1
    (x3, z3), (x4, z4) = l2
    den = (x1 - x2) * (z3 - z4) - (z1 - z2) * (x3 - x4)
    t = ((x1 - x3) * (z3 - z4) - (z1 - z3) * (x3 - x4)) / den
    return x1 + t * (x2 - x1), z1 + t * (z2 - z1)


def ws13_hanger():
    CZ, R = -125.0, 20.0
    tr = _tangent(50, 0, 0, CZ, R, +1)
    tl = _tangent(-50, 0, 0, CZ, R, -1)
    f1 = box(-65, 65, -12.5, 12.5, 0, 5)
    f2 = f1.cut(zcyl(3, -1, 6, -57.5, 0)).cut(zcyl(3, -1, 6, 57.5, 0))
    web = (cq.Workplane('XZ').moveTo(-50, 0).lineTo(50, 0).lineTo(*tr)
           .threePointArc((0, CZ - R), tl).close().extrude(5).translate((0, 2.5, 0)))
    w1 = f2.union(web)
    inside = (0, -60)
    top = ((-60, -15), (60, -15))
    rl = _offset_line((50, 0), tr, 15, inside)
    ll = _offset_line((-50, 0), tl, 15, inside)
    a, b = _meet(top, ll), _meet(top, rl)
    c = (0.0, -108.0)    # the window closes in an R5 just above the boss, as drawn
    cutter = prism([a, b, c], -3, 3)
    cutter = _edges_fillet(cutter, 10, lambda e: y_edge_at(*a)(e) or y_edge_at(*b)(e))
    cutter = _edges_fillet(cutter, 5, y_edge_at(*c))
    w2 = w1.cut(cutter)
    bo = w2.union(ycyl(R, -7.5, 7.5, 0, CZ))
    bo2 = bo.cut(ycyl(10, -8, 8, 0, CZ))
    return [
        F('extrude the top plate', EXTRUDE,
          ['Start 2D Sketch on the XY Plane (the top). Draw a rectangle 130 by 25, centred.',
           'Finish Sketch. Extrude: Distance 5. OK.'], f1),
        F('two holes 6 diameter', HOLE,
          ['Hole: Placement = on the top face, 7.5 from each end on the centre line. Simple hole, diameter 6, Through '
           'All. OK.'], f2),
        F('extrude the web', EXTRUDE,
          ['Start 2D Sketch on the XZ Plane (the front). Draw lines from the plate 100 apart down to touch a circle 40 '
           'diameter 125 below the plate, and close it round the circle.',
           'Finish Sketch. Extrude: Symmetric, Distance 5, Join. OK.'], w1),
        F('cut the window', EXTRUDE,
          ['Start 2D Sketch on the web face. Draw a triangle 15 in from each edge (the 15 arm width), then Fillet the '
           'sketch corners: R10 at the top two, R5 at the bottom.',
           'Finish Sketch. Extrude: Cut, Through All. OK.'], w2),
        F('extrude the boss', EXTRUDE,
          ['Start 2D Sketch on the web face. Draw a circle 40 diameter at the bottom of the web.',
           'Finish Sketch. Extrude: Symmetric, Distance 15, Join. OK.'], bo),
        F('bore 20 diameter', HOLE,
          ['Hole: Concentric with the boss, diameter 20, Through All. OK. Save.'], bo2,
          note='The web thickness (5) and the hole positions (7.5 from the ends) are scaled from the worksheet drawing.'),
    ]


# ================================================================== Worksheet 13: clevis bracket
def ws13_clevis():
    trap = [(0, 0), (60, 0), (40, 35), (20, 35)]

    def side(x0, x1):
        return cq.Workplane('YZ').polyline(trap).close().extrude(x1 - x0).translate((x0, 0, 0))
    c1 = box(0, 26, 0, 60, 0, 3)
    c2 = c1.union(side(0, 4)).union(side(23, 26))
    c3 = c2.union(xcyl(12, -4, 0.01, 30, 22))
    c4 = c3.cut(xcyl(5.1, -5, 4.5, 30, 22)).cut(xcyl(6, 22.5, 27, 30, 22))
    c5 = c4
    for y in (9, 51):
        cone = cq.Workplane('XY').add(cq.Solid.makeCone(3, 5, 2.001, cq.Vector(13, y, 1.0), cq.Vector(0, 0, 1)))
        c5 = c5.cut(zcyl(3, -1, 4, 13, y)).cut(cone)
    return [
        F('extrude the base', EXTRUDE,
          ['Start 2D Sketch on the XY Plane. Draw a rectangle 26 by 60.', 'Finish Sketch. Extrude: Distance 3. OK.'], c1),
        F('extrude the two sides', EXTRUDE,
          ['Start 2D Sketch on the YZ Plane (the end). Draw the trapezium: 60 at the base, 20 at the top, 35 high.',
           'Finish Sketch. Extrude the left side 4 thick and the right side 3 thick, Join. OK.'], c2),
        F('boss 24 diameter', EXTRUDE,
          ['Start 2D Sketch on the outside face of the left side. Draw a circle 24 diameter, 22 up and central.',
           'Finish Sketch. Extrude: Distance 4, Join. OK.'], c3),
        F('M12 thread and 12 hole', HOLE,
          ['Hole: Concentric with the boss, Tapped hole, M12 x 1.75, through the boss and the left side.',
           'Hole: in line, on the right side, Simple hole, diameter 12, Through. OK.'], c4),
        F('two countersunk holes 6 diameter', HOLE,
          ['Hole: Placement = on the base, 13 from the side and 9 from each end (42 apart). Countersink, diameter 6, '
           'countersink 2 x 45 degrees, Through All. OK. Save.'], c5,
          note='The boss height (22) and its 4 projection are scaled from the worksheet drawing. The tapped hole is '
               'modelled at the tap drill size (10.2) with an M12 cosmetic thread, as Inventor does.'),
    ]


# ------------------------------------------------------------------ the catalogue entries
PARTS = [
    dict(name='cg_projection_block', title='CG 3.2: projection line block', fn=projection_block, colour=ALU,
         src='PowerPoint 7 slide 3', material='Aluminium alloy', iso=(1, -1.2, 0.9),
         description='The block on PowerPoint 7 slide 3, dimensioned 45 long to teach projection lines: a small gap '
                     'at the part, the dimension line, and a short extension past it.',
         uses='Extrude and an extrude cut; the first drawing learners dimension.'),
    dict(name='cg_slotted_bar', title='CG 3.2: slotted bar (four arrangements)', fn=slotted_bar, colour=ALU,
         src='PowerPoint 7 slides 4 to 7', material='Aluminium alloy', iso=(1, -1.3, 0.8),
         description='The stepped bar used on PowerPoint 7 slides 4 to 7 to show parallel, running, chain and combined '
                     'dimensioning: 120 long, 48 high, with six steps along the bottom.',
         uses='One extrude and five extrude cuts, each sized from the left end (a datum), as parallel dimensioning does.'),
    dict(name='cg_radius_plate', title='CG 3.2: radius plate', fn=radius_plate, colour=ALU,
         src='PowerPoint 7 slide 9 (a) and (b)', material='Aluminium alloy', iso=(1, -1.2, 0.9),
         description='Slide 9 (a) and (b) on one plate: an R5 outside corner, and an R15 hollow blended with R5 rounds '
                     '(the reverse curve).', uses='Fillets and a circular cut; radii are dimensioned with R.'),
    dict(name='cg_domed_pin', title='CG 3.2: domed pin SR30', fn=domed_pin, colour=STEEL,
         src='PowerPoint 7 slide 9 (c)', material='Mild steel', iso=(1, -1.2, 0.9),
         description='Slide 9 (c): a 24 diameter pin with a spherical end, dimensioned SR30.',
         uses='Extrude, a revolved spherical end and a chamfer.'),
    dict(name='cg_ten_plate', title='CG 3.2: the 10 plate', fn=ten_plate, colour=STEEL,
         src='PowerPoint 7 slide 11', material='Mild steel', iso=(1, -1.2, 0.9),
         description='The dimensioning practice plate on PowerPoint 7 slide 11: 75 by 45, 10 thick, with a 10 x 5 step, '
                     'an R10 notch, a 12 x 45 degree chamfer (135 degrees) and a 10 diameter hole.',
         uses='Every dimension type on one part: linear, radius, diameter and angular.'),
    dict(name='cg_notch_plate', title='CG 3.2: vee notch plate', fn=notch_plate, colour=STEEL,
         src='PowerPoint 7 slide 12', material='Mild steel', iso=(1, -1.2, 0.9),
         description='The plate on PowerPoint 7 slide 12: 90 by 50 with R20 and R10 corners, a 15 wide, 30 degree vee notch, a '
                     '20 x 10 step and a 10 diameter hole 15 from the edges.',
         uses='Fillets, extrude cuts and a hole; the drawing shows every line and mark named on the slide.'),
    dict(name='cg_stepped_shaft', title='CG 3.2: stepped shaft 120 +/- 2', fn=stepped_shaft, colour=STEEL,
         src='PowerPoint 9 slide 5', material='Mild steel', iso=(1, -1.2, 0.9),
         description='The shaft on PowerPoint 9 slide 5: 50 +/- 1 and 70 +/- 1 long, 120 +/- 2 overall, so learners see '
                     'tolerance build-up on a real part.', uses='Two extrudes and a chamfer.'),
    dict(name='cg_flanged_locator', title='CG 3.2: flanged locator (GDT)', fn=flanged_locator, colour=STEEL,
         src='PowerPoint 9 slide 6 and Worksheet 15', material='Mild steel', iso=(1, -1.2, 0.9),
         description='The GDT example on PowerPoint 9 slide 6 and Worksheet 15 (an inch drawing, converted to mm): a '
                     '2.000 in flange with a 1.000 in boss, a 0.500 in bore, three 0.250 in holes on a 1.500 in pitch '
                     'circle and a slot. Its frames show perpendicularity, position, parallelism and flatness.',
         uses='Extrude, holes on a pitch circle and a slot; the GDT frames and datums go on its drawing.'),
    dict(name='cg_ws13_bracket', title='CG 3.2: Worksheet 13 bracket', fn=ws13_bracket, colour=STEEL,
         src='Worksheet 13, drawing 1 (Bracket)', material='Mild steel', iso=(-1, -1.2, 0.9),
         description='The bracket learners dimension on Worksheet 13: a 100 x 120 x 20 base, an upright with an R25 top '
                     'and an R10 hole 75 up and an R7.5 hole 20 from the corner.',
         uses='Extrude, join and holes; a first angle drawing.'),
    dict(name='cg_ws13_hanger', title='CG 3.2: Worksheet 13 hanger bracket', fn=ws13_hanger, colour=STEEL,
         src='Worksheet 13, drawing 2', material='Mild steel', iso=(1, -1.2, 0.9),
         description='The hanger bracket on Worksheet 13: a 130 x 25 x 5 top plate with two 6 diameter holes, a web '
                     '100 wide at the top down to a 40 diameter boss 125 below, with a window (15 arms, R10 and R5) and '
                     'a 20 bore.', uses='Tangent lines to a circle, a cut with filleted corners, a symmetric boss.'),
    dict(name='cg_ws13_clevis', title='CG 3.2: Worksheet 13 clevis bracket', fn=ws13_clevis, colour=STEEL,
         src='Worksheet 13, drawing 3', material='Mild steel', iso=(1, -1.2, 0.9),
         description='The clevis bracket on Worksheet 13: a 26 x 60 base, two trapezium sides 35 high, a 24 diameter '
                     'boss with an M12 thread, and two 6 diameter countersunk holes 42 apart.',
         uses='Extrude, join, a tapped hole and countersunk holes.'),
]


def _items(p):
    return lambda: [(p['title'].split(': ')[1], p['fn']()[-1]['shape'], p['colour'])]


def _steps(p):
    def go():
        feats = p['fn']()
        name = p['title'].split(': ')[1]
        file = p['name'].replace('cg_', '') + '.ipt'
        out = []
        for k, f in enumerate(feats):
            acts = list(f['actions'])
            if k == 0:
                acts = [NEW_PART + ' and save it as %s.' % file] + acts
            out.append(dict(title='%s: %s' % (name[0].upper() + name[1:], f['title']), command=f['command'],
                            actions=acts, parts=[(name, f['shape'], p['colour'])], overlay=f.get('overlay'),
                            note=f.get('note')))
        return out
    return go


def _fit_items(kind):
    def go():
        h1, h2, h3, s1, s2 = fit_parts(kind)
        return [('Housing', h3, HOUSING), ('Shaft', s2, STEEL)]
    return go


def _fit_steps_fn(kind):
    def go():
        out = []
        have = {}
        for st in fit_steps(kind):
            f = st['f']
            if st['part']:
                have[st['part'][0]] = (f['shape'], st['part'][1])
            parts_ = [(n, s, c) for n, (s, c) in have.items()]
            out.append(dict(title=f['title'][0].upper() + f['title'][1:], command=f['command'], actions=f['actions'],
                            parts=parts_, overlay=None, note=f.get('note')))
        return out
    return go


FIT_MODELS = []
for _k, _f in FITS.items():
    FIT_MODELS.append(dict(
        name='cg_fit_%s' % _k, title='CG 3.2: %s fit %g %s' % (_k, _f['d'], _f['code']), folder=FOLDER,
        fn=_fit_items(_k), criteria='3.2', section='y', explode=None, iso=(1, -1.2, 0.9), fea=False,
        uses='Two parts and an assembly; the fit is set by the tolerance classes, not by modelling the parts '
             'different sizes.',
        description='A %s fit from %s: a collar with a %g %s bore (%s) and a shaft %s (%s), half way in. Both are '
                    'modelled at the nominal %g; the fit comes from the tolerances.'
                    % (_k, _f['slide'], _f['d'], _f['code'].split('/')[0], 'hole %.3f to %.3f' % _f['hole'],
                       _f['code'].split('/')[1], 'shaft %.3f to %.3f' % _f['shaft'], _f['d']),
        source=SOURCE % _f['slide'], material='Cast iron and mild steel'))

MODELS = [dict(name=p['name'], title=p['title'], folder=FOLDER, fn=_items(p), criteria='3.2', uses=p['uses'],
               description=p['description'], section='y', explode=None, iso=p['iso'], fea=False,
               source=SOURCE % p['src'], material=p['material'])
          for p in PARTS] + FIT_MODELS
STEPS = {p['name']: _steps(p) for p in PARTS}
STEPS.update({'cg_fit_%s' % k: _fit_steps_fn(k) for k in FITS})
MATERIAL = {m['name']: m['material'] for m in MODELS}
