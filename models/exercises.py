"""Additional CAD exercise: CAD models of fifteen exercise drawings (textbook isometrics, tutorial sheets and
general arrangements), built to the sizes on each drawing.

Each drawing gives one model (the exercise sheet "Uygulama 8, 9, 10" gives six). Every model is built feature by
feature the way it would be in Autodesk Inventor, and every assembly keeps each component as its own part. Where a
drawing leaves a size out, or two of its sizes disagree, the size used is stated in the model's note and in the
build step that uses it.

Units: mm (inch drawings are converted, 1 in = 25.4 mm). Z up, X along the length, Y back into the depth.
"""
import functools
import math
import cadquery as cq
from parts import STEEL, ALU, BRASS, BLUE, GREEN, ORANGE, DARK, hex_prism, _box, _cyl
from library import (F, P, T, R, chain, model_items, model_bom, model_steps, xcyl, ycyl, zcyl, yring, zring, sphere,
                     torus, hex_nut, orient, involute_gear, RED, BLACK, RUBBER, IRON, BRONZE, NEW_PART, SKETCH, EXTRUDE,
                     REVOLVE, HOLE, FILLET, CHAMFER, THREAD, CIRC, RECT, MIRROR, PLACE, CONTENT, CONSTRAIN, SPUR)

FOLDER = 'Additional CAD exercise'
YELLOW = 'E3C94A'
OLIVE = '8DA63C'
COPPER = 'C8703A'
PINK = 'C25BB5'
TEAL = '3AA6A0'
GLASS = '9CC8E6'
SS = 'B8C2CC'          # stainless steel
CAST = '8E9AA8'        # cast aluminium
SWEEP = '3D Model tab > Create panel > Sweep'
SPLIT = '3D Model tab > Modify panel > Split'
SHELL = '3D Model tab > Modify panel > Shell'
WORKPLANE = '3D Model tab > Work Features panel > Plane'
COIL = '3D Model tab > Create panel > Coil'
RIB = '3D Model tab > Create panel > Rib'
LOFT = '3D Model tab > Create panel > Loft'
FRAME = 'Design tab > Frame panel > Insert Frame'
TUBE = 'Environments tab > Begin panel > Tube and Pipe'


# ------------------------------------------------------------------ geometry helpers
def xring(r0, r1, x0, x1, y=0, z=0):
    return xcyl(r1, x0, x1, y, z).cut(xcyl(r0, x0 - 1, x1 + 1, y, z))


PLANES = {
    # name: (origin of the sketch plane as a function of the start offset a0 and end offset a1, x direction, normal)
    'XY': (lambda a0, a1: (0, 0, a0), (1, 0, 0), (0, 0, 1)),     # sketch x, y = model X, Y; extrude +Z from a0 to a1
    'XZ': (lambda a0, a1: (0, a1, 0), (1, 0, 0), (0, -1, 0)),    # sketch x, y = model X, Z; extrude from Y = a0 to a1
    'YZ': (lambda a0, a1: (a0, 0, 0), (0, 1, 0), (1, 0, 0)),     # sketch x, y = model Y, Z; extrude +X from a0 to a1
}
PROFILE_FACE = {'XY': '<Z', 'XZ': '<Y', 'YZ': '<X'}


def path_wp(plane, path, a0=0, a1=1):
    """A closed 2D path on a model plane: a list of points (line to) and (mid, end) pairs (three point arc)."""
    org, xd, nd = PLANES[plane]
    w = cq.Workplane(cq.Plane(org(a0, a1), xd, nd)).moveTo(*path[0])
    for seg in path[1:]:
        w = w.threePointArc(seg[0], seg[1]) if isinstance(seg[0], (tuple, list)) else w.lineTo(*seg)
    return w.close()


def sk(plane, path, a0, a1):
    """Extrude a closed path (see path_wp) between offsets a0 and a1 along the plane's axis."""
    return path_wp(plane, path, a0, a1).extrude(a1 - a0)


def face_of(solid, plane):
    """The sketch profile of a prism made by sk(), as an overlay for the Build steps tab."""
    return cq.Workplane('XY').add(solid.faces(PROFILE_FACE[plane]).val())


def rev(path, axis='z'):
    """Revolve a half section about an axis. The path is (r, along) pairs: radius first, then the distance along the axis."""
    if axis == 'z':
        w = path_wp('XZ', path, 0, 0)       # sketch x = radius (model X), sketch y = along (model Z)
        return w.revolve(360, (0, 0, 0), (0, 1, 0))
    if axis == 'x':
        pts = [(p[1], p[0]) if not isinstance(p[0], (tuple, list)) else ((p[0][1], p[0][0]), (p[1][1], p[1][0])) for p in path]
        w = path_wp('XZ', pts, 0, 0)       # sketch x = along (model X), sketch y = radius (model Z)
        return w.revolve(360, (0, 0, 0), (1, 0, 0))
    if axis == 'y':
        pts = [(p[1], p[0]) if not isinstance(p[0], (tuple, list)) else ((p[0][1], p[0][0]), (p[1][1], p[1][0])) for p in path]
        w = path_wp('YZ', pts, 0, 0)       # sketch x = along (model Y), sketch y = radius (model Z)
        return w.revolve(360, (0, 0, 0), (1, 0, 0))


def tangent(p, c, r, side):
    """Point where a line from p touches the circle (c, r); side +1 or -1 picks which of the two."""
    dx, dy = p[0] - c[0], p[1] - c[1]
    d = math.hypot(dx, dy)
    th = math.atan2(dy, dx) + side * math.acos(r / d)
    return (c[0] + r * math.cos(th), c[1] + r * math.sin(th))


def hull_path(circles):
    """Closed path round the convex hull of circles [(x, y, r), ...] given anticlockwise round the hull."""
    n = len(circles)
    tps = []
    for i in range(n):
        (x0, y0, r0), (x1, y1, r1) = circles[i], circles[(i + 1) % n]
        d = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / d, (y1 - y0) / d
        a = (r0 - r1) / d
        b = math.sqrt(1 - a * a)
        nx, ny = a * ux + b * uy, a * uy - b * ux          # outward normal, on the right of the travel direction
        tps.append(((x0 + r0 * nx, y0 + r0 * ny), (x1 + r1 * nx, y1 + r1 * ny)))
    path = [tps[0][0]]
    for i in range(n):
        path.append(tps[i][1])
        x, y, r = circles[(i + 1) % n]
        p_in, p_out = tps[i][1], tps[(i + 1) % n][0]
        t0 = math.atan2(p_in[1] - y, p_in[0] - x)
        t1 = math.atan2(p_out[1] - y, p_out[0] - x)
        sweep = (t1 - t0) % (2 * math.pi)
        if sweep > 1e-6:
            tm = t0 + sweep / 2
            path.append(((x + r * math.cos(tm), y + r * math.sin(tm)), p_out))
    return path


def slot_xy(x0, y0, x1, y1, w, z0, z1):
    """A slot (obround) of width w between two centres, extruded from z0 to z1."""
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    s = cq.Workplane('XY').slot2D(L + w, w, 0).extrude(z1 - z0)
    return s.rotate((0, 0, 0), (0, 0, 1), ang).translate(((x0 + x1) / 2, (y0 + y1) / 2, z0))


def try_fillet(w, sel, r):
    try:
        out = w.edges(sel).fillet(r)
        return out if out.val().isValid() else w
    except Exception:
        return w


def hex_bolt(d, length, af, head, p, axis='-z'):
    """Hex head bolt: the underside of the head at p, the shank going along axis (major diameter, as CAD shows threads)."""
    b = hex_prism(af, head).edges('>Z').chamfer(min(0.8, head * 0.15)).translate((0, 0, 0))
    shank = cq.Workplane('XY').circle(d / 2).extrude(-length).faces('<Z').chamfer(min(1.0, d * 0.1))
    w = b.union(shank)                                  # made with the head on +Z of the origin, shank down -Z
    turn = {'-z': lambda s: s, 'z': lambda s: s.rotate((0, 0, 0), (1, 0, 0), 180),
            '-x': lambda s: s.rotate((0, 0, 0), (0, 1, 0), 90), 'x': lambda s: s.rotate((0, 0, 0), (0, 1, 0), -90),
            '-y': lambda s: s.rotate((0, 0, 0), (1, 0, 0), -90), 'y': lambda s: s.rotate((0, 0, 0), (1, 0, 0), 90)}[axis]
    return turn(w).translate(p)


def nut_on(d, af, h, p, axis='z'):
    """Hex nut with its base at p, standing along axis."""
    return hex_nut(af, h, d, (0, 0, 0), 'z').rotate((0, 0, 0), (1, 0, 0), {'z': 0, '-z': 180, 'y': -90, '-y': 90, 'x': 0, '-x': 0}[axis]) \
        .rotate((0, 0, 0), (0, 1, 0), {'x': 90, '-x': -90}.get(axis, 0)).translate(p)


# ------------------------------------------------------------------ the model framework
def single(name, title, part, description, uses, criteria='3.1, 3.2', section='y', iso=(1, -1, 0.8), note=None):
    return dict(name=name, title=title, parts=[part], assembly=[], explode=None, description=description, uses=uses,
                criteria=criteria, section=section, iso=iso, note=note, material=part['material'])


def ex_steps(mdl):
    """Build steps: each part feature by feature, then (for an assembly) the assembly."""
    if mdl['assembly']:
        return model_steps(mdl)
    p = mdl['parts'][0]
    steps = []
    last = len(p['features']) - 1
    for k, f in enumerate(p['features']):
        acts = list(f['actions'])
        if k == 0:
            acts = [NEW_PART + ' and save it as %s.' % p['file']] + acts
        if k == last:
            acts = acts + ['Save %s.' % p['file']]
        steps.append(dict(title=f['title'][0].upper() + f['title'][1:], command=f['command'], actions=acts,
                          parts=[(p['name'], f['shape'], p['colour'])] if f['shape'] is not None else [],
                          overlay=f.get('overlay'), note=f.get('note')))
    return steps


# ================================================================== 1 exercise sheet, T8: fork bracket
@functools.lru_cache(None)
def fork_bracket():
    L, W, TB = 72, 44, 10                 # base: length, width (13 + 18 + 13), thickness
    C, RB, RH = (36, 54), 18, 9           # boss centre (x, z), boss radius (36 diameter), bore radius (18)
    tr = tangent((L, 18), C, RB, 1)
    tl = (L - tr[0], tr[1])
    lug_path = [(0, 0), (L, 0), (L, 18), tr, ((36, 54 + RB), tl), (0, 18)]
    base = _box(0, L, 0, W, 0, TB)
    lug_a = sk('XZ', lug_path, 0, 13)
    b1 = base
    b2 = base.union(lug_a)
    b3 = b2.union(sk('XZ', lug_path, W - 13, W))
    b4 = b3.cut(ycyl(RH, -1, W + 1, 36, 54))
    b5 = b4.cut(_box(18, 54, -1, W + 1, -1, 2))
    b6 = b5.cut(zcyl(4, -1, TB + 1, 9, W / 2)).cut(zcyl(4, -1, TB + 1, 63, W / 2))
    b7 = b6.cut(zcyl(2, 54, 54 + RB + 1, 36, 6.5)).cut(zcyl(2, 54, 54 + RB + 1, 36, W - 6.5))
    part = P('fork_bracket', 'fork bracket', 'EN-GJL-250 grey cast iron', 'Bracket', IRON, [
        F('sketch the base', SKETCH, ['Start 2D Sketch on the XZ Plane (the ground). Two Point Rectangle 72 x 44 from the origin.',
                                      'Finish Sketch.'], None, overlay=face_of(b1, 'XY')),
        F('extrude the base', EXTRUDE, ['Extrude the rectangle 10 mm upwards.'], b1),
        F('sketch the lug', SKETCH,
          ['Start 2D Sketch on the front face of the base. Draw the lug outline: the bottom edge 72 long, vertical ends 18 high, '
           'a 36 diameter circle centred 36 along and 54 up, and two lines from the tops of the ends Tangent to the circle.',
           'Trim the inside of the circle away. Finish Sketch.'], b1, overlay=face_of(lug_a, 'XZ')),
        F('extrude the front lug', EXTRUDE, ['Extrude the lug outline 13 mm back into the part, Join.'], b2),
        F('mirror the lug', MIRROR,
          ['Mirror: the lug feature about the middle plane of the base (22 from the front), so the second lug sits 18 behind it.'], b3,
          note='The sheet gives the lugs as 13, 18 and 13 (44 in all) but the base as 36 wide. The base is made 44 wide here so the '
               'lugs stand on it; check this with your tutor.'),
        F('bore through both bosses', HOLE, ['Hole on the front boss face, on the boss centre: Simple Hole, diameter 18, Through All.'], b4),
        F('relief under the base', EXTRUDE,
          ['Sketch a rectangle 36 x 44 in the middle of the underside. Extrude, Cut, 2 mm deep.'], b5,
          note='The relief means the bracket sits on two pads, so it rocks less on an uneven surface.'),
        F('holding down holes', HOLE,
          ['Hole on the top of the base between the lugs, 9 from each end (54 apart) and 22 from the front: Simple Hole, diameter 8, '
           'Through All.'], b6),
        F('oil holes', HOLE, ['Hole on the top of each boss, on its middle: Simple Hole, diameter 4, To the bore.'], b7),
    ])
    return single('ax_fork_bracket', 'Fork bracket (exercise T8)', part,
                  'A cast iron fork bracket from the exercise sheet: a 72 x 44 base with a relief underneath, two lugs 13 thick with an 18 gap '
                  'carrying a 36 diameter boss with an 18 bore 54 above the base, two holding down holes and oil holes.',
                  'Isometric to orthographic: lugs, tangent lines, holes on two axes; the section shows the bore and the relief.',
                  section='x', iso=(1, -1.2, 0.9),
                  note='The sheet gives 13 + 18 + 13 = 44 across the lugs but 36 across the base: the base is made 44.')


# ================================================================== 2 exercise sheet, T8: pedestal bearing
@functools.lru_cache(None)
def pedestal_bearing():
    L, W, TB = 74, 42, 10
    ZC, RB, RH, BL = 50, 18, 9, 35        # boss centre height, boss radius, bore radius, boss length
    y0, y1 = (W - BL) / 2, (W + BL) / 2
    base = _box(0, L, 0, W, 0, TB)
    b1 = try_fillet(base, '|Z', 6)
    tr = tangent((54, TB), (37, ZC), RB - 1, 1)
    tl = (L - tr[0], tr[1])
    web_path = [(20, TB - 1), (54, TB - 1), tr, ((37, ZC + RB - 1), tl)]
    web = sk('XZ', web_path, 16, 26)
    b2 = b1.union(web)
    rib = _box(32.5, 41.5, y0, y1, TB - 1, ZC - 8)
    b3 = b2.union(rib)
    b4 = b3.union(ycyl(RB, y0, y1, 37, ZC))
    b5 = b4.cut(ycyl(RH, y0 - 1, y1 + 1, 37, ZC))
    b6 = b5.cut(_box(29, 45, -1, W + 1, -1, 4))
    b7 = b6
    for x in (12, 62):
        b7 = b7.cut(slot_xy(x, 17, x, 25, 8, -1, TB + 1)).cut(slot_xy(x, 17, x, 25, 14, TB - 3, TB + 1))
    b6a = b6                                # the build steps show the slots before the counterbores
    for x in (12, 62):
        b6a = b6a.cut(slot_xy(x, 17, x, 25, 8, -1, TB + 1))
    part = P('pedestal_bearing', 'pedestal bearing', 'EN-GJL-250 grey cast iron', 'Bearing', IRON, [
        F('base plate', EXTRUDE, ['Sketch a rectangle 74 x 42 on the XZ Plane. Extrude it 10 mm up.'], base),
        F('round the base corners', FILLET, ['Fillet the four vertical corners, radius 6.'], b1),
        F('web', EXTRUDE,
          ['Sketch on the XY Plane (the front) a 36 circle centred 37 along and 50 up, and two lines from the base (at 20 and 54) '
           'Tangent to the circle. Extrude the outline 10 mm, Midplane, from the middle of the base.'], b2,
          overlay=face_of(web, 'XZ')),
        F('rib', EXTRUDE, ['Sketch a rectangle 9 wide under the boss on the top of the base, 35 long. Extrude it up to the boss centre.'], b3,
          note='The web and the rib make a cross shaped column, stiff in both directions.'),
        F('boss', EXTRUDE, ['Sketch a 36 circle on the front, centred 37 along and 50 up. Extrude 35 mm, Midplane about the middle of the base.'], b4),
        F('bore', HOLE, ['Hole on the boss end: Simple Hole, diameter 18, Through All.'], b5),
        F('relief under the base', EXTRUDE, ['Sketch a rectangle 16 wide across the middle of the underside. Extrude, Cut, 4 mm.'], b6),
        F('slots', EXTRUDE,
          ['Sketch on the top of the base two Center to Center Slots 8 long and 8 wide, 12 from each end. Extrude, Cut, Through All.'],
          b6a, note='The slots let the pedestal slide 8 mm to line the bore up with the shaft before the bolts are tightened.'),
        F('counterbores', EXTRUDE, ['Sketch slots on the same centres 14 wide (R7). Extrude, Cut, 3 mm.'], b7),
    ])
    return single('ax_pedestal_bearing', 'Pedestal bearing (exercise T8)', part,
                  'A cast iron pedestal from the exercise sheet: a 74 x 42 base with a relief and two counterbored slots, a web and rib '
                  'column, and a 36 diameter boss 35 long with an 18 bore, 50 above the base.',
                  'A boss on a column: tangent lines, counterbored slots, a section through the bore.', section='y', iso=(1, -1.2, 0.9),
                  note='The web is shown 10 thick and the rib 9 thick (the "10" and "9" on the sheet).')


# ================================================================== 3 exercise sheet, T9: slotted boss flange
@functools.lru_cache(None)
def slotted_boss_flange():
    fl = hull_path([(0, 0, 30), (-40, 0, 10)])
    plate = sk('XY', fl, 0, 8)
    b1 = plate
    b2 = b1.union(zcyl(20, 0, 48))
    b3 = b2.cut(zcyl(13, -1, 49))
    b4 = b3.cut(_box(-8, 8, -21, 21, 42, 49))
    b5 = b4.cut(zcyl(6.25, -1, 9, -40, 0))
    b6 = try_fillet(b5, cq.selectors.BoxSelector((-21, -21, 7), (21, 21, 9)), 2)
    part = P('slotted_boss_flange', 'slotted boss flange', 'EN-GJL-250 grey cast iron', 'Flange', IRON, [
        F('sketch the flange', SKETCH, ['Sketch on the XZ Plane: a circle R30 on the origin and a circle R10 40 to the left. Draw two '
                                        'lines Tangent to both, and trim. The flange is 80 long overall.'], None, overlay=face_of(plate, 'XY'),
          note='The sheet does not size the big end of the flange; R30 was scaled from the drawing.'),
        F('extrude the flange', EXTRUDE, ['Extrude 8 mm.'], b1),
        F('boss', EXTRUDE, ['Sketch a 40 circle on the top of the flange, on the origin. Extrude it to 48 from the bottom (40 mm).'], b2),
        F('bore', HOLE, ['Hole on the top of the boss: Simple Hole, diameter 26, Through All.'], b3),
        F('slot across the top', EXTRUDE, ['Sketch a rectangle 16 wide across the top of the boss. Extrude, Cut, 6 mm.'], b4),
        F('bolt hole', HOLE, ['Hole on the small end: Simple Hole, diameter 12.5, Through All, concentric with the R10 end.'], b5),
        F('fillet the boss root', FILLET, ['Fillet: radius 2 round the bottom of the boss.'], b6),
    ])
    return single('ax_slotted_boss_flange', 'Slotted boss flange (exercise T9)', part,
                  'A flanged boss from the exercise sheet: an 80 long flange 8 thick with an R10 end and a 12.5 hole, a 40 diameter boss '
                  '48 high with a 26 bore, and a slot 16 wide and 6 deep across its top.',
                  'Tangent arcs, a slot through a cylinder (the curve it makes), section through the boss.', section='y',
                  iso=(1, -1.1, 0.9), note='The big end of the flange is not sized on the sheet; it is drawn R30.')


# ================================================================== 4 exercise sheet, T9: corner boss bracket
@functools.lru_cache(None)
def corner_boss_bracket():
    CY = 62
    fl = hull_path([(-32, 0, 14), (32, 0, 14), (0, CY, 25)])
    plate = sk('XY', fl, 0, 8)
    b1 = plate
    b2 = b1.union(zcyl(25, 0, 30, 0, CY))
    rib = sk('YZ', [(-10, 7), (CY - 12, 7), (CY - 12, 30), (CY - 25, 30)], -5, 5)
    b3 = b2.union(rib)
    b4 = b3.union(zcyl(10, 7, 11, -32, 0)).union(zcyl(10, 7, 11, 32, 0))
    b5 = b4.cut(zcyl(16, -1, 31, 0, CY))
    b6 = b5.cut(zcyl(6.5, -1, 12, -32, 0)).cut(zcyl(6.5, -1, 12, 32, 0))
    b7 = b6.cut(xcyl(6, -26, 26, CY, 20))
    part = P('corner_boss_bracket', 'boss bracket', 'EN-GJL-250 grey cast iron', 'Bracket', IRON, [
        F('sketch the plate', SKETCH, ['Sketch on the XZ Plane: circles R14 at (-32, 0) and (32, 0) and R25 at (0, 62). Lines Tangent to '
                                       'each pair, then trim to the outside.'], None, overlay=face_of(plate, 'XY')),
        F('extrude the plate', EXTRUDE, ['Extrude 8 mm.'], b1),
        F('boss', EXTRUDE, ['Sketch a 50 circle at (0, 62). Extrude it to 30 from the bottom (22 above the plate).'], b2),
        F('rib', RIB,
          ['Sketch on the YZ Plane a line from the plate, 10 in front of the lug centres, up to the top of the boss.',
           'Rib: thickness 10, Midplane, extend to the plate.'], b3, overlay=face_of(rib, 'YZ')),
        F('lug bosses', EXTRUDE, ['Sketch 20 circles on the lug centres. Extrude 3 mm up from the plate.'], b4),
        F('bore', HOLE, ['Hole on the top of the boss: Simple Hole, diameter 32, Through All.'], b5),
        F('lug holes', HOLE, ['Hole on each lug boss: Simple Hole, diameter 13, Through All.'], b6),
        F('cross hole', HOLE, ['Work Plane tangent to the side of the boss. Hole 10 below the top, across the boss: '
                               'Simple Hole, diameter 12, Through All.'], b7),
    ])
    return single('ax_corner_boss_bracket', 'Boss bracket (exercise T9)', part,
                  'A three point bracket from the exercise sheet: a plate 8 thick round two R14 lugs 64 apart and a 50 diameter boss '
                  '62 behind them, the boss 22 high with a 32 bore and a 12 cross hole, a sloping rib 10 thick, and 13 holes in 20 bosses.',
                  'A plate made of tangent arcs, a rib, a cross hole meeting a bore.', section='x', iso=(1, -1, 0.9))


# ================================================================== 5 exercise sheet, T10: saddle bearing block
@functools.lru_cache(None)
def saddle_block():
    L, W, TB, H = 120, 96, 15, 33
    base = _box(0, L, 0, W, 0, TB)
    b1 = base
    b2 = b1.union(_box(26, 94, 13, 83, TB, H))
    b3a = b2.cut(ycyl(28, 12, 65, 60, H))
    b3 = b3a.cut(ycyl(20, 64, 84, 60, H))
    b4 = b3
    for x in (13, 107):
        for y in (28, 68):
            b4 = b4.cut(zcyl(4.5, -1, TB + 1, x, y))
    b5 = b4.cut(xcyl(3, 80, 95, 48, 27))
    part = P('saddle_block', 'saddle bearing block', 'EN-GJL-250 grey cast iron', 'Bearing', IRON, [
        F('base', EXTRUDE, ['Sketch a rectangle 120 x 96 on the XZ Plane. Extrude 15 mm.'], b1),
        F('upper block', EXTRUDE, ['Sketch a rectangle 68 x 70 in the middle of the base. Extrude it to 33 from the bottom.'], b2),
        F('saddle, R28 part', EXTRUDE,
          ['Sketch on the front face a half circle R28 centred on the top edge, 60 along. Extrude, Cut, 52 mm deep.'], b3a),
        F('saddle, R20 part', EXTRUDE,
          ['Sketch a half circle R20 on the same centre on the back face. Extrude, Cut, up to the first cut.'], b3,
          note='The step from R28 to R20 is a shoulder for the bearing shell to stop against.'),
        F('holding down holes', HOLE, ['Hole on the top of the base: Simple Hole, diameter 9, Through All, at 13 from each end, 40 apart.'], b4),
        F('oil hole', HOLE, ['Hole on the right end of the block, 6 below the top: Simple Hole, diameter 6, into the saddle.'], b5),
    ])
    return single('ax_saddle_block', 'Saddle bearing block (exercise T10)', part,
                  'A cast iron saddle block from the exercise sheet: a 120 x 96 base 15 thick with four 9 holes, and a block 68 x 70 '
                  'standing 33 high, cut with a half bore R28 for 52 mm and R20 for the rest.',
                  'Half bores, a stepped saddle, hole positions from a datum; the section shows the step in the saddle.',
                  section='x', iso=(1, -1.2, 0.9),
                  note='Some sizes on this part of the sheet are hard to read; the base is taken as 120 x 96 x 15 and the block 68 x 70.')


# ================================================================== 6 exercise sheet, T10: split clamp lever
@functools.lru_cache(None)
def clamp_lever():
    H = 48
    boss = zcyl(21, 0, H)
    b1 = boss
    lug_path = [(-12, 0), (-33, 0), ((-41.5, 3.5), (-45, 12)), (-45, H - 12), ((-41.5, H - 3.5), (-33, H)), (-12, H)]
    lug = sk('XZ', lug_path, -15, 15)
    b2 = b1.union(lug)
    arm = sk('XY', hull_path([(10, 0, 15), (88, 0, 15)])[:], 0, 20)
    b3 = b2.union(arm)
    b4 = b3.cut(zcyl(14, -1, H + 1))
    b5 = b4.cut(_box(-50, -5, -1, 1, -1, H + 1))
    b6 = b5.cut(ycyl(4.25, -16, 16, -33, 24))
    b7 = b6.cut(slot_xy(46, 0, 88, 0, 20, 8, 21))
    part = P('clamp_lever', 'split clamp lever', 'EN-GJS-400 ductile iron', 'Lever', IRON, [
        F('boss', EXTRUDE, ['Sketch a 42 circle on the XZ Plane. Extrude 48 mm.'], b1),
        F('clamp lug', EXTRUDE, ['Sketch on the XY Plane the lug outline: from the boss out to 45 from the centre, 48 high, with R12 '
                                 'corners on its outer end. Extrude 30 mm, Midplane.'], b2, overlay=face_of(lug, 'XZ')),
        F('arm', EXTRUDE, ['Sketch on the XZ Plane a circle R15 88 from the centre and two lines Tangent to it and to the boss. '
                           'Extrude 20 mm.'], b3),
        F('bore', HOLE, ['Hole on the top of the boss: Simple Hole, diameter 28, Through All.'], b4),
        F('split', EXTRUDE, ['Sketch a rectangle 2 wide from the bore out through the lug. Extrude, Cut, Through All.'], b5,
          note='Tightening a bolt across the split squeezes the bore onto its shaft: the lever is clamped without a key.'),
        F('clamp bolt hole', HOLE, ['Hole on the front face of the lug, 33 from the centre and 24 up: Simple Hole, diameter 8.5, '
                                    'Through All ("Boydan boya": right through).'], b6),
        F('arm slot', EXTRUDE, ['Sketch a Center to Center Slot 20 wide from 46 to 88 along the arm. Extrude, Cut, 12 mm deep.'], b7),
    ])
    return single('ax_clamp_lever', 'Split clamp lever (exercise T10)', part,
                  'A split clamp lever from the exercise sheet: a 42 diameter boss 48 high with a 28 bore, split through a clamp lug '
                  'with an 8.5 bolt hole, and an arm 30 wide and 20 deep with a slot 20 wide reaching 88 from the bore.',
                  'Split clamps, a slot in an arm, holes on three axes; section through the bore and the split.',
                  section='x', iso=(1, -1.1, 1),
                  note='The lug height and the bolt hole height (24 up) are read from the picture.')


# ================================================================== 7 roller assembly
@functools.lru_cache(None)
def roller_assembly():
    ZS = 72                                 # spindle axis height
    RR, WR = 50, 42                         # roller radius and width
    # 1 base
    base0 = _box(-75, 75, -36, 36, 0, 20)
    base1 = try_fillet(base0, '|Z', 8)
    base2 = base1.cut(_box(-30, 30, -37, 37, -1, 3))
    base3 = base2
    for x in (-60, 60):
        for y in (-24, 24):
            base3 = base3.cut(zcyl(5, 4, 21, x, y))
    # 2 bracket (the right hand one; the left one is the same part turned round)
    foot = _box(31, 75, -36, 36, 20, 30)
    up = _box(31, 45, -18, 18, 29, ZS).union(xcyl(18, 31, 45, 0, ZS))
    br1 = foot.union(up)
    gus = sk('XZ', [(44, 29), (70, 29), (44, 62)], -5, 5)
    br2 = br1.union(gus)
    br3 = br2.cut(xcyl(8, 30, 46, 0, ZS))
    br4 = br3
    for y in (-24, 24):
        br4 = br4.cut(zcyl(5.5, 19, 31, 60, y))
    br5 = try_fillet(br4, cq.selectors.BoxSelector((30, -37, 19), (76, 37, 21)), 1.5)
    # 3 spindle, 4 bush, 5 roller
    sp0 = xcyl(8, -52, 52, 0, ZS)
    sp1 = sp0.faces('<X or >X').chamfer(1)
    bush0 = rev([(8.1, 0), (11, 0), (11, 21), (15, 21), (15, 31), (8.1, 31)], "x").translate((0, 0, ZS))
    bush1 = bush0.faces('>X').chamfer(0.5)
    rol_path = [(11.02, -21), (20, -21), (20, -6), (40, -6), (40, -21), (RR, -21), (RR, 21), (40, 21), (40, 6), (20, 6), (20, 21), (11.02, 21)]
    rol0 = rev(rol_path, 'x').translate((0, 0, ZS))
    rol1 = try_fillet(rol0, cq.selectors.BoxSelector((-22, -51, ZS - 51), (22, 51, ZS + 51)), 0.6)
    bolt = hex_bolt(10, 20, 16, 6.4, (60, -24, 30))
    turn = R((0, 0, 0), (0, 0, 1), 180)
    bolts = [('hex bolt %d' % (k + 1), tf) for k, tf in enumerate(
        [None, T(0, 48, 0), chain(T(-120, 0, 0)), chain(T(-120, 48, 0))])]
    parts = [
        P('base', 'base', 'EN-GJL-250 grey cast iron', 'Frame', IRON, [
            F('base plate', EXTRUDE, ['Sketch a rectangle 150 x 72 on the XZ Plane, centred. Extrude 20 mm.'], base0),
            F('round the corners', FILLET, ['Fillet the four vertical corners, radius 8.'], base1),
            F('relief underneath', EXTRUDE, ['Sketch a rectangle 60 wide across the middle of the underside. Extrude, Cut, 3 mm.'], base2),
            F('tapped holes', HOLE, ['Hole on the top face at (+-60, +-24): Tapped Hole, M10x1.5, thread depth 16, drill depth 17.'], base3,
              note='Tapped holes are modelled at the thread size (10), the way CAD shows a cosmetic thread.')]),
        P('bracket', 'bracket', 'EN-GJL-250 grey cast iron', 'Frame', IRON, [
            F('foot', EXTRUDE, ['Sketch a rectangle 44 x 72 on the XZ Plane, from 31 to 75 along. Extrude 10 mm.'], foot),
            F('upright', EXTRUDE, ['Sketch on the YZ Plane a rectangle 36 wide up to the spindle centre (72 up) and a circle R18 on '
                                   'the centre. Extrude 14 mm from the inside face of the foot.'], br1),
            F('gusset', RIB, ['Sketch a sloping line from the outside of the upright to the foot. Rib: 10 thick, Midplane.'], br2,
              overlay=face_of(gus, 'XZ')),
            F('spindle hole', HOLE, ['Hole on the upright, on the R18 centre: Simple Hole, diameter 16, Through All.'], br3),
            F('bolt holes', HOLE, ['Hole on the foot at 60 along and 24 each side: Simple Hole, diameter 11, Through All.'], br4),
            F('round the foot', FILLET, ['Fillet: radius 1.5 on the bottom edges of the foot.'], br5)],
          instances=[('bracket (right)', None), ('bracket (left)', turn)]),
        P('spindle', 'spindle', '709M40 alloy steel', 'Roller', STEEL, [
            F('spindle', EXTRUDE, ['Sketch a 16 circle on the YZ Plane. Extrude 104 mm, Midplane.'], sp0),
            F('chamfer the ends', CHAMFER, ['Chamfer: 1 mm on both ends.'], sp1)]),
        P('bush', 'bush', 'Bronze, soft tin (CuSn8)', 'Roller', BRONZE, [
            F('flanged bush', REVOLVE, ['Sketch the half section on the XY Plane: bore 16, body 22 for 21 mm, flange 30 for 10 mm. '
                                        'Revolve about the axis.'], bush0),
            F('chamfer', CHAMFER, ['Chamfer 0.5 mm on the outer edge of the flange.'], bush1)],
          instances=[('bush (right)', None), ('bush (left)', turn)]),
        P('roller', 'roller', 'Cast steel (GS-45)', 'Roller', ORANGE, [
            F('roller section', REVOLVE,
              ['Sketch the half section on the XY Plane: rim 100 to 80 diameter and 42 wide, web 12 thick, hub 40 to 22 diameter.',
               'Revolve about the axis.'], rol0),
            F('round the edges', FILLET, ['Fillet: radius 0.6 on the rim and hub edges.'], rol1)]),
        P('hex_bolt', 'hex bolt M10 x 1.5 x 20', 'Steel, mild (ANSI B18.2.3.5M)', 'Fasteners (bought in)', DARK,
          [F('bolt', CONTENT, [], bolt)], instances=bolts, bought=True),
    ]
    assembly = [
        ('place the base', PLACE, ['Place base.ipt, right click, Place Grounded at Origin.'], ['base']),
        ('brackets', CONSTRAIN, ['Place bracket.ipt twice. Mate each foot to the top of the base, and Insert its bolt holes onto '
                                 'the tapped holes, the uprights facing each other.'], ['bracket (right)', 'bracket (left)']),
        ('bolt the brackets down', CONTENT, ['Place from Content Center: ANSI B18.2.3.5M hex bolt M10 x 1.5 x 20, four of them. '
                                              'Insert each into a foot hole.'], [n for n, tf in bolts]),
        ('roller', CONSTRAIN, ['Place roller.ipt. Mate its axis to the spindle holes and Flush its middle plane with the middle of '
                               'the base.'], ['roller']),
        ('bushes', CONSTRAIN, ['Place bush.ipt twice. Insert each bush into the roller bore, flange outwards.'],
         ['bush (right)', 'bush (left)']),
        ('spindle', CONSTRAIN, ['Place spindle.ipt. Mate its axis to the bracket holes and centre it with Flush.'], ['spindle'],
         'The bushes turn on the fixed spindle; their flanges take any end load against the brackets.'),
    ]
    ex = {'roller': (0, 0, 90), 'bush (right)': (60, 0, 90), 'bush (left)': (-60, 0, 90), 'spindle': (0, -110, 90),
          'bracket (right)': (60, 0, 0), 'bracket (left)': (-60, 0, 0)}
    ex.update({n: (0, 0, 60) for n, tf in bolts})
    return dict(name='ax_roller_assembly', title='Roller assembly', parts=parts, assembly=assembly, explode=ex,
                description='A roller on a fixed spindle: a cast steel roller 100 diameter turning on two flanged bronze bushes, the alloy '
                            'steel spindle held in two cast iron brackets, bolted to a cast iron base with four M10 bolts. 11 parts.',
                uses='Assembly drawing with item balloons, parts list, bushes and a spindle in section.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.3, 0.9), material='See parts list',
                note='The drawing gives no sizes (scale 1:2). The sizes were scaled from it using the M10 bolts.')


# ================================================================== 8 machinist's jack
@functools.lru_cache(None)
def machinists_jack():
    ZP, RL = 54, 20                         # pivot height (from the bottom of the base), lug end radius
    plate = _box(-66, 66, -29, 29, 0, 14)
    b1 = try_fillet(plate, '|Z', 5)
    tr = tangent((37.5, 14), (0, ZP), RL, 1)
    lug_path = [(-37.5, 13), (37.5, 13), tr, ((0, ZP + RL), (-tr[0], tr[1]))]
    lug = sk('XZ', lug_path, 16, 26)
    b2 = b1.union(lug)
    b3 = b2.union(sk('XZ', lug_path, -26, -16))
    b4 = b3.cut(ycyl(8, -27, 27, 0, ZP))
    b5 = b4.cut(zcyl(7, -1, 15, -50, 0)).cut(zcyl(7, -1, 15, 50, 0))
    # swivel: 32 x 32, top 50 above the pivot, R22 round the pivot
    TOP = ZP + 50
    sr = tangent((16, TOP), (0, ZP), 22, -1)
    sw_path = [(-16, TOP), (-sr[0], sr[1]), ((0, ZP - 22), sr), (16, TOP)]
    sw0 = sk('XZ', sw_path, -16, 16)
    sw1 = sw0.cut(ycyl(8, -17, 17, 0, ZP))
    sw2 = sw1.cut(zcyl(10, TOP - 34, TOP + 1)).cut(zcyl(8.75, TOP - 38, TOP - 33))
    sw3 = sw2.faces('>Z').edges('not %CIRCLE').chamfer(1)
    bolt = hex_bolt(16, 68, 25, 10, (0, -26, ZP), 'y')
    nut = nut_on(16, 25, 10, (0, 26, ZP), 'y')
    lock0 = zring(10, 22.5, TOP, TOP + 8)
    lock1 = lock0.faces('>Z').edges().chamfer(0.8)
    S0 = TOP - 24                           # bottom of the screw
    scr0 = zcyl(10, S0, S0 + 32).union(zcyl(8, S0 + 32, S0 + 40)).union(zcyl(10, S0 + 40, S0 + 56))
    scr1 = scr0.cut(xcyl(5.25, -11, 11, 0, S0 + 48))
    scr2 = scr1.faces('>Z or <Z').chamfer(1)
    parts = [
        P('base', 'base', 'Steel AISI 1020', 'Jack', YELLOW, [
            F('base plate', EXTRUDE, ['Sketch a rectangle 132 x 58 on the XZ Plane, centred. Extrude 14 mm.'], plate),
            F('round the corners', FILLET, ['Fillet the four vertical corners R5.'], b1),
            F('first lug', EXTRUDE, ['Sketch on the XY Plane the lug: a line 75 long on the plate, a circle R20 centred 54 up, two lines '
                                     'Tangent to it. Extrude 10 mm, starting 16 behind the middle (a 32 gap between the lugs).'], b2,
              overlay=face_of(lug, 'XZ')),
            F('second lug', MIRROR, ['Mirror the lug about the XY Plane.'], b3),
            F('pivot holes', HOLE, ['Hole on the lug, on the R20 centre: Simple Hole, diameter 16, Through All.'], b4),
            F('holding down holes', HOLE, ['Hole on the plate 100 apart (16 from each end): Simple Hole, diameter 14, Through All.'], b5)]),
        P('swivel', 'swivel', 'Steel AISI 1020', 'Jack', OLIVE, [
            F('body', EXTRUDE, ['Sketch on the XY Plane: the top 32 wide, a circle R22 50 below it, lines Tangent to the circle. '
                                'Extrude 32 mm, Midplane.'], sw0, overlay=face_of(sw0, 'XZ')),
            F('pivot hole', HOLE, ['Hole on the front face on the R22 centre: Simple Hole, diameter 16, Through All.'], sw1),
            F('tapped hole for the screw', HOLE, ['Hole on the top face: Tapped Hole, M20x2.5, thread depth 34, drill depth 38.'], sw2),
            F('chamfer the top', CHAMFER, ['Chamfer 1 x 45 on the top edges.'], sw3)]),
        P('bolt', 'bolt M16 x 2.0 x 68', 'Steel AISI 1020', 'Jack', STEEL, [F('bolt', CONTENT, [], bolt)], bought=True),
        P('nut', 'standard nut M16 x 2.0', 'Steel AISI 1020', 'Jack', PINK, [F('nut', CONTENT, [], nut)], bought=True),
        P('lock_nut', 'lock nut M20 x 2.5', 'Steel AISI 1020', 'Jack', STEEL, [
            F('ring', EXTRUDE, ['Sketch circles of 45 and 20 diameter. Extrude 8 mm.'], lock0),
            F('chamfer', CHAMFER, ['Chamfer 0.8 on the top edges. Add the knurl as a cosmetic (decal) or with Emboss.'], lock1,
              note='The 20 hole is threaded M20x2.5 with the Thread command; the outside is knurled for a grip.')]),
        P('screw', 'screw M20 x 2.5 x 56', 'Steel AISI 1020', 'Jack', COPPER, [
            F('screw', REVOLVE, ['Sketch the half section: 20 diameter for 32 (the thread), a neck 16 diameter for 8, then 20 diameter '
                                 'for 16. Revolve.'], scr0),
            F('cross hole', HOLE, ['Hole across the head, 8 below the top: Simple Hole, diameter 10.5, Through All.'], scr1,
              note='A tommy bar through this hole turns the screw.'),
            F('chamfers', CHAMFER, ['Chamfer 1 x 45 on both ends.'], scr2),
            F('thread', THREAD, ['Thread: the bottom 32 mm, M20x2.5 (a cosmetic thread, shown on the drawing).'], scr2)]),
    ]
    assembly = [
        ('place the base', PLACE, ['Place base.ipt Grounded at Origin.'], ['base']),
        ('swivel between the lugs', CONSTRAIN, ['Place swivel.ipt. Mate its pivot hole axis to the lug hole axis, and Mate a side '
                                                'face to the inside of a lug.'], ['swivel']),
        ('bolt and nut', CONTENT, ['Place bolt M16 x 68 and a nut M16: Insert the bolt through the lugs and the swivel, the nut on its end.'],
         ['bolt M16 x 2.0 x 68', 'standard nut M16 x 2.0']),
        ('lock nut', CONSTRAIN, ['Place lock_nut.ipt: Mate it to the top of the swivel, on the screw axis.'], ['lock nut M20 x 2.5']),
        ('screw', CONSTRAIN, ['Place screw.ipt: Insert it through the lock nut into the tapped hole, 24 deep.'],
         ['screw M20 x 2.5 x 56'], 'Turning the screw sets the height; the lock nut is then tightened down on the swivel to hold it.'),
    ]
    ex = {'swivel': (0, 0, 60), 'bolt M16 x 2.0 x 68': (0, -90, 0), 'standard nut M16 x 2.0': (0, 70, 0),
          'lock nut M20 x 2.5': (0, 0, 100), 'screw M20 x 2.5 x 56': (0, 0, 150)}
    return dict(name='ax_machinists_jack', title="Machinist's jack", parts=parts, assembly=assembly, explode=ex,
                description="A machinist's jack for propping work on a machine table: a base with two lugs, a swivel on an M16 bolt, "
                            "and an M20 screw with a lock nut to set the height. 6 parts, all AISI 1020 steel.",
                uses='Assembly from detail drawings, sections A-A, B-B, C-C and D-D, threads, a parts list.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.3, 0.9), material='Steel AISI 1020')


# ================================================================== 9 valve body
@functools.lru_cache(None)
def valve_body():
    ZB, ZT = -51, 67                       # bottom of the body, underside of the top flange
    ZS = 20                                # height of the side port axis
    core0 = sk('XY', hull_path([(-16, -26, 20), (16, -26, 20), (16, 26, 20), (-16, 26, 20)]), ZB, ZT)
    b1 = core0
    neck = xcyl(40, -63, 63)
    b2 = b1.union(neck)
    fl = xcyl(73, 63, 79).union(xcyl(40, 78.9, 83))
    b3 = b2.union(fl).union(fl.mirror('YZ'))
    top = sk('XY', hull_path([(0, -18, 60), (0, 18, 60)]), ZT, ZT + 16)
    b4 = b3.union(top)
    side = ycyl(25, -84, -30, 0, ZS).union(_box(-65, 65, -98, -82, ZS - 40, ZS + 40))
    b5 = b4.union(side)
    cham = None
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = sk('XZ', [(0, 0), (-sx * 7.5, 0), (0, -sz * 7.5)], -99, -81).translate((sx * 65, 0, ZS + sz * 40))
            cham = c if cham is None else cham.union(c)
    b6 = b5.cut(cham)
    chamber = sk('XY', hull_path([(-16, -26, 10), (16, -26, 10), (16, 26, 10), (-16, 26, 10)]), -41, 57)
    b7 = b6.cut(chamber)
    b8 = b7.cut(xcyl(21, -84, 84))
    b9 = b8.cut(sk('XY', hull_path([(0, -18, 20), (0, 18, 20)]), 50, ZT + 17))
    b10 = b9.cut(ycyl(20, -99, -20, 0, ZS)).cut(ycyl(30, -99, -93, 0, ZS))
    b3a = b2.union(xcyl(73, 63, 79))         # build step views: one flange, its raised face, the side port boss, one ring of holes
    b3b = b3a.union(xcyl(40, 78.9, 83))
    b4a = b4.union(ycyl(25, -84, -30, 0, ZS))
    b11a = b10
    for k in range(6):
        a = math.radians(30 + 60 * k)
        b11a = b11a.cut(xcyl(8, 62, 84, 55 * math.cos(a), 55 * math.sin(a)))
    b11 = b10
    for sx in (-1, 1):
        for k in range(6):
            a = math.radians(30 + 60 * k)
            b11 = b11.cut(xcyl(8, 62, 84, 55 * math.cos(a), 55 * math.sin(a)).mirror('YZ') if sx < 0
                          else xcyl(8, 62, 84, 55 * math.cos(a), 55 * math.sin(a)))
    b12 = b11
    for (x, y) in ((0, 64), (0, -64), (45, 22), (-45, 22), (45, -22), (-45, -22)):
        b12 = b12.cut(zcyl(7, ZT - 1, ZT + 17, x, y))
    b13 = b12
    for x in (-43.25, 43.25):
        for z in (ZS - 25, ZS + 25):
            b13 = b13.cut(ycyl(7.5, -99, -81, x, z))
    part = P('valve_body', 'valve body', 'Stainless steel AISI 316L', 'Valve', SS, [
        F('body', EXTRUDE, ['Sketch on the XZ Plane a rectangle 72 x 92 with R20 corners, centred. Extrude from 51 below the axis '
                            'to 67 above it.'], b1),
        F('through neck', EXTRUDE, ['Sketch an 80 circle on the YZ Plane. Extrude 126 mm, Midplane.'], b2),
        F('first round flange', EXTRUDE, ['Sketch a 146 circle on a Work Plane 63 from the middle. Extrude 16 mm outwards.'], b3a),
        F('raised face', EXTRUDE, ['Sketch an 80 circle on the flange. Extrude 4 mm.'], b3b),
        F('second round flange', MIRROR, ['Mirror the flange and its raised face about the YZ Plane (166 between the flange '
                                          'faces).'], b3),
        F('top flange', EXTRUDE, ['Sketch on the top of the body a slot with R60 ends 36 apart (120 wide, 156 long). Extrude 16 mm.'], b4),
        F('side port boss', EXTRUDE, ['Sketch a 50 circle on the front of the body, 20 above the axis. Extrude it to 82 in front of '
                                      'the axis.'], b4a),
        F('side flange', EXTRUDE, ['Sketch a rectangle 130 x 80 on the end of the boss. Extrude 16 mm (the flange face is 98 from '
                                   'the axis).'], b5),
        F('flange corner chamfers', CHAMFER, ['Chamfer the four corners of the side flange 5 x 45 (7.5 on the sketch).'], b6),
        F('chamber', EXTRUDE, ['Sketch on the XZ Plane a rectangle 52 x 72 with R10 corners. Extrude, Cut, from 41 below the axis '
                               'to 57 above it (98 high).'], b7, note='Section A-A on the sheet shows the chamber: 52 wide and 98 high, '
                                                                     'walls 10 thick.'),
        F('through bore', HOLE, ['Hole on a round flange: Simple Hole, diameter 42, Through All.'], b8),
        F('top port', EXTRUDE, ['Sketch on the top flange a slot 40 wide with its ends 36 apart. Extrude, Cut, into the chamber.'], b9),
        F('side port bore', HOLE, ['Hole on the side flange: Counterbore, diameter 40, counterbore 60 x 5, into the chamber.'], b10),
        F('round flange holes', CIRC, ['Hole 16 diameter on the 110 pitch circle, Through the flange. Circular Pattern: 6.'], b11a),
        F('holes in the other flange', MIRROR, ['Mirror the holes about the YZ Plane (12 holes, the "12 x 16" on the sheet).'], b11),
        F('top flange holes', HOLE, ['Hole 14 diameter, Through the top flange: two on the long axis 64 from the middle and four '
                                     'at 45 and 22. (6 x 14 on the sheet.)'], b12),
        F('side flange holes', RECT, ['Hole 15 diameter on the side flange, 86.5 x 50 apart. Rectangular Pattern 2 x 2.'], b13),
    ])
    return single('ax_valve_body', 'Valve body', part,
                  'A three port valve body in 316L stainless steel: a 42 bore through two 146 flanges 166 apart, a 52 x 98 chamber, '
                  'a slotted top port on an oval flange and a 40 side port on a rectangular flange 98 from the axis.',
                  'Reading a part from sections A-A and B-B, flanges and hole patterns, a casting with an inside chamber.',
                  section='y', iso=(1, -1.2, 0.8),
                  note='The sheet gives the weight as 9.606 kg; this model is checked against that. Unlabelled corner radii (R5) are left sharp.')


# ================================================================== 10 planetary gear set
@functools.lru_cache(None)
def planetary_gears():
    FACE, RP = 10, 18                      # face width, planet orbit radius
    ring0 = zcyl(32.5, 0, FACE)
    cutter = involute_gear(1, 60, FACE + 2, backlash=-0.12).translate((0, 0, -1)).rotate((0, 0, 0), (0, 0, 1), 3)
    ring1 = ring0.cut(cutter)
    ring2 = ring1.cut(zcyl(29.0, -1, FACE + 1))
    sun0 = involute_gear(1, 12, FACE)
    sun1a = sun0.union(zcyl(4, -20, 0.01))
    sun1 = sun1a.union(zcyl(2.5, -30, -19.99))
    sun2 = sun1.cut(zring(2.0, 3, -26, -25.25))
    pl0 = involute_gear(1, 24, FACE).intersect(zcyl(12.85, -1, FACE + 1))
    pl0 = pl0.rotate((0, 0, 0), (0, 0, 1), 7.5).translate((RP, 0, 0))
    pl1a = pl0.union(zcyl(4, FACE - 0.01, FACE + 1.5, RP, 0))
    pl1 = pl1a.union(zcyl(2, FACE + 1.49, FACE + 5.5, RP, 0))
    pl2 = pl1.union(zcyl(1.5, FACE + 5.49, FACE + 11, RP, 0))
    car0 = sk('XY', hull_path([(RP * math.cos(math.radians(a)), RP * math.sin(math.radians(a)), 7.5) for a in (0, 120, 240)]),
              FACE + 1.5, FACE + 5.5)
    car1a = car0.union(zcyl(4, FACE + 5.49, FACE + 45.5))
    car1 = car1a.union(zcyl(2.5, FACE + 45.49, FACE + 55.5))
    car2 = car1
    for a in (0, 120, 240):
        car2 = car2.cut(zcyl(4.5, FACE, FACE + 6, RP * math.cos(math.radians(a)), RP * math.sin(math.radians(a))))
    car3 = car2.cut(zring(2.0, 3, FACE + 50.5, FACE + 51.25))
    brg = zring(2, 4.5, FACE + 1.5, FACE + 5.5, RP, 0).cut(zring(2.6, 3.9, FACE + 1.3, FACE + 1.8, RP, 0)).cut(
        zring(2.6, 3.9, FACE + 5.2, FACE + 5.7, RP, 0))
    nut = hex_nut(5.5, 4, 3, (RP, 0, FACE + 5.5))
    rot = lambda a: R((0, 0, 0), (0, 0, 1), a)
    planets = [('planet gear %d' % (k + 1), rot(120 * k) if k else None) for k in range(3)]
    brgs = [('bearing %d' % (k + 1), rot(120 * k) if k else None) for k in range(3)]
    nuts = [('lock nut M3 %d' % (k + 1), rot(120 * k) if k else None) for k in range(3)]
    parts = [
        P('ring_gear', 'ring gear', 'Steel AISI 1020', 'Gears', RED, [
            F('blank', EXTRUDE, ['Sketch a 65 circle on the XZ Plane. Extrude 10 mm.'], ring0),
            F('internal teeth', SPUR, ['Design tab > Spur Gear can make an internal gear; here the teeth are cut with a sketch: '
                                       'module 1, 60 teeth, 20 degree pressure angle, pitch diameter 60, root 62.5. Extrude, Cut, '
                                       'Through All, and Circular Pattern the tooth space 60 times.'], ring1,
              note='Gear table on the sheet: ring gear, 60 teeth, module 1, pitch circle 60, addendum circle 62.502, dedendum circle 57.95.'),
            F('tip circle', EXTRUDE, ['Sketch a 58 circle. Extrude, Cut, Through All (the tooth tips, 57.95 on the sheet).'], ring2)]),
        P('sun_gear', 'sun gear', 'Steel AISI 1020', 'Gears', BRASS, [
            F('teeth', SPUR, ['Spur Gear: module 1, 12 teeth, face width 10. Pitch 12, tip 14, root 9.5.'], sun0),
            F('input shaft', EXTRUDE, ['Sketch an 8 circle on the back of the gear. Extrude 20 mm.'], sun1a),
            F('shaft end', EXTRUDE, ['Sketch a 5 circle on the end of the shaft. Extrude 10 mm (30 in all).'], sun1),
            F('circlip groove', REVOLVE, ['Sketch a groove 0.75 wide and 0.5 deep, 5 from the end. Revolve, Cut.'], sun2)]),
        P('planet_gear', 'planet gear', 'Steel AISI 1020', 'Gears', TEAL, [
            F('teeth', SPUR, ['Spur Gear: module 1, 24 teeth, face width 10. Pitch 24, tip 26 (turned to 25.7), root 21.5.'], pl0),
            F('collar', EXTRUDE, ['Sketch an 8 circle on the gear face. Extrude 1.5 mm (a spacer collar).'], pl1a),
            F('bearing seat', EXTRUDE, ['Sketch a 4 circle on the collar. Extrude 4 mm.'], pl1),
            F('threaded end', EXTRUDE, ['Sketch a 3 circle on the bearing seat. Extrude 5.5 mm.'], pl2),
            F('thread', THREAD, ['Thread: M3x0.5 on the 3 end (a cosmetic thread).'], pl2,
              note='The planets are spaced 120 degrees apart. That only works because (60 + 12) / 3 = 24 is a whole number.')],
          instances=planets),
        P('carrier', 'carrier', 'Steel AISI 1020', 'Carrier', GREEN, [
            F('plate', EXTRUDE, ['Sketch three R7.5 circles on an 18 radius at 120 degrees and join them with tangent lines. '
                                 'Extrude 4 mm.'], car0),
            F('output shaft', EXTRUDE, ['Sketch an 8 circle on the plate. Extrude 40 mm.'], car1a),
            F('shaft end', EXTRUDE, ['Sketch a 5 circle on the end of the shaft. Extrude 10 mm.'], car1),
            F('bearing seats', CIRC, ['Hole 9 diameter on one lobe, Through. Circular Pattern: 3.'], car2),
            F('circlip groove', REVOLVE, ['Groove 0.75 wide and 0.5 deep near the end of the shaft.'], car3)]),
        P('bearing', 'bearing 684 (4 x 9 x 4)', 'Bearing steel', 'Bought in', STEEL, [F('bearing', BEARING_CMD, [], brg)],
          instances=brgs, bought=True),
        P('lock_nut', 'lock nut ISO 7040 M3', 'Steel, zinc plated', 'Bought in', DARK, [F('nut', CONTENT, [], nut)],
          instances=nuts, bought=True),
    ]
    assembly = [
        ('place the ring gear', PLACE, ['Place ring_gear.ipt Grounded at Origin.'], ['ring gear']),
        ('sun gear', CONSTRAIN, ['Place sun_gear.ipt. Mate its axis to the ring axis and Flush the gear faces.'], ['sun gear']),
        ('planets', CONSTRAIN, ['Place planet_gear.ipt three times. Mate each axis on an 18 radius, 120 degrees apart, and turn '
                                'each so its teeth sit in the sun and ring tooth spaces (Angle constraint).'], [n for n, tf in planets]),
        ('bearings', CONTENT, ['Place from Content Center: Deep groove ball bearing 684 (4 x 9 x 4), three of them, on the planet pins.'],
         [n for n, tf in brgs]),
        ('carrier', CONSTRAIN, ['Place carrier.ipt. Insert its bearing seats onto the bearings.'], ['carrier']),
        ('lock nuts', CONTENT, ['Place from Content Center: ISO 7040 M3 nylon insert lock nut, three of them.'], [n for n, tf in nuts]),
    ]
    ex = {'carrier': (0, 0, 70), 'sun gear': (0, 0, -60)}
    ex.update({n: (0, 0, 85) for n, tf in brgs})
    ex.update({n: (0, 0, 100) for n, tf in nuts})
    ex.update({n: (0, 0, 35) for n, tf in planets})
    return dict(name='ax_planetary_gears', title='Planetary gear set', parts=parts, assembly=assembly, explode=ex,
                description='An epicyclic gear set, module 1: a 12 tooth sun gear drives three 24 tooth planets inside a 60 tooth ring '
                            'gear, and the planets drive the carrier and its output shaft at one sixth of the sun speed. 12 parts.',
                uses='Gears drawn by convention, a gear table, exploded views, a parts list, gear ratios.',
                criteria='3.1, 3.2', section='y', iso=(1, -1.4, 1.1), material='Steel AISI 1020',
                note='The sheet shows one bearing per planet ("bearing from toolbox") but none in the parts list; bearings 684 are added.')


BEARING_CMD = 'Assemble tab > Component panel > Place from Content Center (Bearings)'


# ================================================================== 11 bracket with a 45 degree tube
@functools.lru_cache(None)
def tube_bracket_45():
    XC, YC = 30, 30                       # vertical tube axis
    s2 = math.sqrt(0.5)
    base0 = _box(0, 65, 0, 50, 0, 6)
    b1 = try_fillet(base0, '|Z', 5)
    b2 = b1.union(zcyl(13, 0, 40, XC, YC))
    axis_o, d = (XC, YC, 13), (s2, 0, s2)
    L = 22 / s2                           # to the flange face, 35 high and 22 along
    b3 = b2.union(_cyl(13, axis_o, d, L - 4))
    fl0 = sk('XY', hull_path([(-12, -12, 6), (12, -12, 6), (12, 12, 6), (-12, 12, 6)]), 0, 4)
    fl = fl0.rotate((0, 0, 0), (0, 1, 0), 45).translate((XC + (L - 4) * s2, YC, 13 + (L - 4) * s2))
    b4 = b3.union(fl)
    back = sk('XZ', [(0, 6), (22, 6), (22, 24), ((20.2, 28.2), (16, 30)), (0, 30)], 38, 50)
    b5 = b4.union(back)
    step = _box(0, 10, 0, 16, 6, 15)
    lug = sk('XZ', [(22, 6), (38, 6), (38, 10), ((30, 18), (22, 10))], 0, 6)
    b6a = b5.union(step)
    b6 = b6a.union(lug)
    b7a = b6.cut(zcyl(10, -1, 41, XC, YC))
    b7 = b7a.cut(_cyl(10, (XC - 4 * s2, YC, 13 - 4 * s2), d, L + 6))
    b8 = b7.cut(_box(XC - 3, XC + 3, YC - 14, YC, 30, 41))
    b9a = b8.cut(ycyl(2, 37, 51, 8, 22))
    b9b = b9a.cut(zcyl(2, 5, 16, 5, 8))
    b9 = b9b.cut(ycyl(2, -1, 7, 30, 10))
    holes = None
    for u in (-13, 13):
        for v in (-13, 13):
            h = zcyl(2, -1, 5, u, v)
            holes = h if holes is None else holes.union(h)
    holes = holes.rotate((0, 0, 0), (0, 1, 0), 45).translate((XC + (L - 4) * s2, YC, 13 + (L - 4) * s2))
    b10a = b9.cut(holes)
    b10 = b10a.cut(zcyl(2, -1, 7, 58, 8)).cut(zcyl(2, -1, 7, 58, 43))
    part = P('tube_bracket_45', 'tube bracket', 'Aluminium alloy, cast (LM25)', 'Bracket', CAST, [
        F('base', EXTRUDE, ['Sketch a rectangle 65 x 50 on the XZ Plane. Extrude 6 mm.'], base0),
        F('round the base corners', FILLET, ['Fillet the four vertical corners R5.'], b1),
        F('vertical tube', EXTRUDE, ['Sketch a 26 circle 30 from the left end. Extrude it to 40 from the bottom.'], b2),
        F('45 degree tube', EXTRUDE, ['Work Plane at 45 degrees through the tube axis. Sketch a 26 circle on a plane square to the '
                                      '45 degree axis and Extrude it up to the flange.'], b3),
        F('square flange', EXTRUDE, ['Sketch a 36 square with R6 corners on the end of the tube, centred on its axis 35 above the '
                                     'base. Extrude 4 mm.'], b4),
        F('back wall', EXTRUDE, ['Sketch on the back face the wall: 22 long, 30 high, an R6 round on its top corner. Extrude 12 mm.'], b5,
          overlay=face_of(back, 'XZ')),
        F('step block', EXTRUDE, ['Sketch a 10 x 16 rectangle on the top of the base at the front left corner. Extrude 9 mm (15 '
                                  'from the bottom).'], b6a),
        F('front lug', EXTRUDE, ['Sketch on the front face the lug: 16 wide, straight sides 4 high and an R8 round top (18 from the '
                                 'bottom). Extrude 6 mm back.'], b6),
        F('vertical bore', HOLE, ['Hole 20 diameter down the vertical tube, Through All.'], b7a),
        F('45 degree bore', HOLE, ['Hole on the flange face, on the tube axis: 20 diameter, To the vertical bore.'], b7),
        F('slot in the tube', EXTRUDE, ['Sketch a rectangle 6 wide at the top of the tube. Extrude, Cut, 10 mm deep, through the front wall.'], b8),
        F('hole across the back wall', HOLE, ['Hole 4 diameter, Through, across the back wall, 8 from the left end and 22 up.'], b9a),
        F('hole in the step block', HOLE, ['Hole 4 diameter, 10 deep, down the middle of the step block.'], b9b),
        F('hole in the front lug', HOLE, ['Hole 4 diameter, Through, on the R8 centre of the front lug.'], b9),
        F('flange holes', RECT, ['Hole 4 diameter at one corner of a 26 square on the flange. Rectangular Pattern 2 x 2, 26 '
                                 'apart.'], b10a),
        F('base holes', HOLE, ['Hole 4 diameter, Through, in the base 58 from the left end, 8 and 43 from the front.'], b10),
    ])
    return single('ax_tube_bracket_45', 'Tube bracket, 45 degree', part,
                  'A cast bracket from a dimensioned isometric: a 65 x 50 base, a 26 tube 40 high with a slot in its top, a second 26 '
                  'tube at 45 degrees to a 36 square flange with four 4 holes, and lugs with 4 holes.',
                  'Auxiliary views (the 45 degree flange), work planes, many small features.', section='y', iso=(1, -1.1, 0.9),
                  note='Small radii (R2) are left sharp. The lug sizes not given are scaled from the picture.')


IN = 25.4


# ================================================================== 12 angle bracket (inch drawing)
@functools.lru_cache(None)
def angle_bracket():
    BL, BW, BT = 3.75 * IN, 3.00 * IN, 0.38 * IN
    base0 = _box(-BL / 2, BL / 2, -BW / 2, BW / 2, 0, BT)
    b1 = try_fillet(base0, '|Z', 0.50 * IN)
    b2 = b1.cut(_box(-0.565 * IN, 0.565 * IN, -BW / 2 - 1, BW / 2 + 1, -1, 0.06 * IN))
    CW, CD, WT = 1.88 * IN, 1.38 * IN, 0.31 * IN        # column width, depth, wall
    ZP = 2.66 * IN                                       # height of the middle of the top plate
    tilt = -30                                           # the plate faces the front, high at the back
    col_top = ZP + 30
    col = _box(-CW / 2, CW / 2, -CD / 2, CD / 2, BT - 0.1, col_top)
    plane_cut = _box(-60, 60, -80, 80, 0, 80).rotate((0, 0, 0), (1, 0, 0), -tilt).translate((0, 0, ZP))
    col1 = col.cut(plane_cut)
    b3 = b2.union(col1)
    pocket = _box(-CW / 2 + WT, CW / 2 - WT, -CD / 2 - 1, CD / 2 - WT, BT, col_top).cut(
        _box(-60, 60, -80, 80, -WT, 80).rotate((0, 0, 0), (1, 0, 0), -tilt).translate((0, 0, ZP)))
    b4 = b3.cut(pocket)
    # build step views: the column is made as a channel open at the front and trimmed; the top plate then closes it, which
    # gives the same solid as the pocket (b5)
    chan = col.cut(_box(-CW / 2 + WT, CW / 2 - WT, -CD / 2 - 1, CD / 2 - WT, BT, col_top + 1))
    b3a = b2.union(chan)
    b3b = b2.union(chan.cut(plane_cut))
    PL, PW, PT = 2.38 * IN, 1.88 * IN, 0.31 * IN
    plate0 = sk('XY', hull_path([(-PW / 2 + 7.9, -PL / 2 + 7.9, 7.9), (PW / 2 - 7.9, -PL / 2 + 7.9, 7.9),
                                 (PW / 2 - 7.9, PL / 2 - 7.9, 7.9), (-PW / 2 + 7.9, PL / 2 - 7.9, 7.9)]), -PT, 0)
    holes = None
    for x in (-0.63 * IN, 0.63 * IN):
        for y in (-0.87 * IN, 0.87 * IN):
            h = zcyl(0.155 * IN, -PT - 1, 1, x, y)
            holes = h if holes is None else holes.union(h)
    place = lambda w: w.rotate((0, 0, 0), (1, 0, 0), -tilt).translate((0, 0, ZP))
    b5 = b4.union(place(plate0))
    b6 = b5.cut(place(holes))
    ZB = 1.50 * IN
    b7 = b6.union(xcyl(0.375 * IN, CW / 2 - 1, CW / 2 + 0.59 * IN, 0, ZB))
    b8 = b7.cut(xcyl(0.25 * IN, CW / 2 - WT - 1, CW / 2 + 0.59 * IN + 1, 0, ZB))
    b9 = b8
    for x in (-1.375 * IN, 1.375 * IN):
        for y in (-1.0 * IN, 1.0 * IN):
            b9 = b9.cut(zcyl(0.19 * IN, -1, BT + 1, x, y))
    part = P('angle_bracket', 'angle bracket', 'Aluminium alloy, cast (LM6)', 'Bracket', CAST, [
        F('base', EXTRUDE, ['Sketch a rectangle 3.75 x 3.00 in (95.25 x 76.2 mm) on the XZ Plane. Extrude 0.38 in (9.65).'], base0,
          note='The drawing is in inches; the model is in millimetres (x 25.4).'),
        F('round the base corners', FILLET, ['Fillet the four vertical corners R0.50 in.'], b1),
        F('relief under the base', EXTRUDE, ['Sketch a strip 1.13 in wide across the underside. Extrude, Cut, 0.06 in.'], b2),
        F('column', EXTRUDE, ['Sketch on the top of the base the column as a channel open at the front: a 1.88 x 1.38 in rectangle '
                              'with a 1.26 x 1.07 in notch from the front edge (walls 0.31 in). Extrude it up past the top.'], b3a,
          note='An even wall thickness lets the casting cool evenly, so it does not crack.'),
        F('trim the column top', SPLIT, ['Work Plane at 30 degrees through a line 2.66 in up, sloping down to the front. Split > '
                                         'Trim Solid with the plane, and remove the top.'], b3b),
        F('top plate', EXTRUDE, ['Sketch on the 30 degree Work Plane a rectangle 1.88 x 2.38 in with R0.31 corners. Extrude 0.31 in '
                                 'down. It closes the top of the channel.'], b5),
        F('top plate holes', RECT, ['Hole 0.31 in diameter, on the centres of the R0.31 corners: 1.26 x 1.74 in apart. Rectangular Pattern 2 x 2.'], b6),
        F('side boss', EXTRUDE, ['Sketch a 0.75 in circle on the side of the column, 1.50 in up. Extrude 0.59 in out.'], b7),
        F('boss bore', HOLE, ['Hole 0.50 in diameter, through the boss and the wall.'], b8),
        F('base holes', RECT, ['Hole 0.38 in diameter, 2.75 x 2.00 in apart. Rectangular Pattern 2 x 2.'], b9),
    ])
    return single('ax_angle_bracket', 'Angle bracket (inch drawing)', part,
                  'A cast angle bracket from an inch dimensioned isometric: a 3.75 x 3.00 in base with four holes, a hollow column, a '
                  'top plate at 30 degrees with four holes, and a side boss with a 0.50 in bore. Modelled in millimetres.',
                  'Inclined faces and true shape (auxiliary view), inch to millimetre conversion, shelled castings.',
                  section='x', iso=(1, -1.3, 0.9),
                  note='Inch drawing converted to mm. The column is read as a channel open at the front, because the drawing shows its inside '
                       'corner. The top plate holes sit on the centres of its R0.31 corners (0.63 and 0.87 in from the centre lines).')


# ================================================================== 13 four throw crankshaft
@functools.lru_cache(None)
def crankshaft_4():
    RT = 44                                         # throw (crank radius)
    xs = [186 + 114 * k for k in range(4)]          # crank pin centres from the front end
    ups = [-1, 1, 1, -1]                            # pins 1 and 4 down, 2 and 3 up
    h = 16.5
    n_l, n_r = (-math.cos(math.radians(h)), math.sin(math.radians(h))), (math.cos(math.radians(h)), math.sin(math.radians(h)))
    c = 44 * math.sin(math.radians(h)) + 36

    def web(x0, up):
        """One web 15.5 thick from x0: disc R70 + counterweight wedge to R80 + round end R36 on the pin."""
        disc = xcyl(70, x0, x0 + 15.5)
        pin_end = xcyl(36, x0, x0 + 15.5, 0, RT)
        big = xcyl(80, x0, x0 + 15.5)
        # build the wedge as the region n.p <= c for both normals, as a polygon
        tl = lambda n, t: (c * n[0] - t * n[1], c * n[1] + t * n[0])
        # intersection of the two lines
        apex = (0, c / n_r[1])
        far = 400
        pl_pts = [apex, tl(n_l, -far) if tl(n_l, -far)[1] < apex[1] else tl(n_l, far), (-far, -far), (far, -far),
                  tl(n_r, far) if tl(n_r, far)[1] < apex[1] else tl(n_r, -far)]
        wedge = sk('YZ', pl_pts, x0, x0 + 15.5).intersect(big)
        w = disc.union(wedge).union(pin_end)
        return w if up > 0 else w.rotate((0, 0, 0), (1, 0, 0), 180)

    stub = xcyl(16, 0, 110.01)
    s1 = stub.union(xcyl(32, 110, 148.01))
    s2 = s1
    for k, (xc, up) in enumerate(zip(xs, ups)):
        s2 = s2.union(web(xc - 38, up)).union(web(xc + 22.5, up))
    s3 = s2
    for xc, up in zip(xs, ups):
        s3 = s3.union(xcyl(32, xc - 22.6, xc + 22.6, 0, RT * up))
    s4 = s3
    for xc in xs[:3]:
        s4 = s4.union(xcyl(32, xc + 37.9, xc + 76.1))
    s4 = s4.union(xcyl(32, xs[3] + 37.9, 604.01))

    def throw(base, xc, up):
        """The build steps make the shaft throw by throw: front web, crank pin, rear web (the same solid as s4 at the end)."""
        a = base.union(web(xc - 38, up))
        b = a.union(xcyl(32, xc - 22.6, xc + 22.6, 0, RT * up))
        return a, b, b.union(web(xc + 22.5, up))
    t1 = throw(s1, xs[0], ups[0])
    j2 = t1[2].union(xcyl(32, xs[0] + 37.9, xs[0] + 76.1))
    t2 = throw(j2, xs[1], ups[1])
    j3 = t2[2].union(xcyl(32, xs[1] + 37.9, xs[1] + 76.1))
    t3 = throw(j3, xs[2], ups[2])[2].union(xcyl(32, xs[2] + 37.9, xs[2] + 76.1))
    s5 = s4.union(xcyl(72, 604, 619))
    s6 = s5
    for k in range(6):
        a = math.radians(30 + 60 * k)
        s6 = s6.cut(xcyl(5, 603, 620, 54.5 * math.cos(a), 54.5 * math.sin(a)))
    s7a = s6.edges(cq.selectors.BoxSelector((618, -80, -80), (620, 80, 80))).edges(cq.selectors.RadiusNthSelector(-1)).chamfer(2)
    s7 = s7a.faces('<X').chamfer(1)
    part = P('crankshaft_4', 'crankshaft', 'Forged steel 42CrMo4', 'Crankshaft', STEEL, [
        F('front stub and journal', REVOLVE, ['Sketch on the XY Plane the half section: 32 diameter for 110, then 64 diameter for 38. '
                                              'Revolve about the axis.'], s1),
        F('throw 1: front web', EXTRUDE,
          ['Sketch a web on the end face of the front journal: a circle R70 on the main axis, a circle R36 on the pin centre 44 '
           'below the axis, and two lines Tangent to the R36 circle at 33 degrees to each other, closed by an arc R80 on the main '
           'axis (the counterweight, opposite the pin). Trim. Extrude 15.5 mm.'], t1[0], overlay=face_of(web(xs[0] - 38, ups[0]), 'YZ'),
          note='Section A-A on the sheet shows the web: the R80 counterweight, the 33 degree sides and the R36 (72 diameter) pin end.'),
        F('throw 1: crank pin', EXTRUDE, ['Sketch a 64 circle on the web face on the R36 centre, 44 below the axis. Extrude 45 mm.'],
          t1[1], note='Stroke = 2 x throw = 2 x 44 = 88 mm.'),
        F('throw 1: rear web', MIRROR, ['Work Plane through the middle of the crank pin (Offset 22.5 from the web face). Mirror the '
                                        'front web about it.'], t1[2]),
        F('main journal 2', EXTRUDE, ['Sketch a 64 circle on the main axis on the rear web. Extrude 38 mm.'], j2),
        F('throw 2: front web', EXTRUDE, ['Sketch the same web on the end of journal 2, but with the pin centre 44 above the axis '
                                          '(throw 2 is turned 180 degrees from throw 1). Extrude 15.5 mm.'], t2[0]),
        F('throw 2: crank pin', EXTRUDE, ['Sketch a 64 circle on the R36 centre, 44 above the axis. Extrude 45 mm.'], t2[1]),
        F('throw 2: rear web', MIRROR, ['Work Plane through the middle of the pin. Mirror the front web about it.'], t2[2]),
        F('main journal 3', EXTRUDE, ['Sketch a 64 circle on the main axis on the rear web. Extrude 38 mm.'], j3),
        F('throw 3 and journal 4', RECT, ['Rectangular Pattern: the two throw 2 webs, its pin and journal 3. Direction along the '
                                          'shaft axis, 2 occurrences, 114 apart.'], t3,
          note='Throws 2 and 3 point the same way, so a pattern copies throw 2.'),
        F('throw 4 and the rear journal', RECT, ['Rectangular Pattern: the two throw 1 webs, its pin and journal 2. 2 occurrences, '
                                                 '342 apart (3 x 114). The copied journal ends at 604, where the flange starts.'], s4,
          note='Pins 1 and 4 point down and pins 2 and 3 point up, so the shaft balances end to end.'),
        F('flange', EXTRUDE, ['Sketch a 144 circle on the end of the rear journal. Extrude 15 mm (619 overall).'], s5),
        F('flange holes', CIRC, ['Hole 10 diameter on the 109 pitch circle, Through. Circular Pattern: 6.'], s6,
          note='The flywheel bolts to these holes.'),
        F('flange chamfer', CHAMFER, ['Chamfer 2 mm on the outside edge of the flange.'], s7a),
        F('front end chamfer', CHAMFER, ['Chamfer 1 mm on the front end of the stub.'], s7),
    ])
    return single('ax_crankshaft_4', 'Crankshaft, four cylinder', part,
                  'A four throw crankshaft 619 long: a 32 front stub, five 64 main journals, four 64 crank pins on a 44 throw (pins 1 '
                  'and 4 opposite 2 and 3), eight counterweighted webs and a 144 flywheel flange with six 10 holes.',
                  'Long parts and sections (A-A through a pin, B-B through a journal), equal spacing, counterweights.',
                  section='y', iso=(1, -1.6, 0.8),
                  note='The 72 and 78 diameters on the sections are taken as the round ends of the webs; the webs are 15.5 thick '
                       '((76 - 45) / 2).')


# ================================================================== 14 three throw crankshaft (inch drawing)
@functools.lru_cache(None)
def crankshaft_3():
    RT, RM, RP = 63.5, 63.5 / 2, 76.2 / 2          # throw, main journal radius, pin radius
    WT, PL, ML, SL = 19.0, 54.62, 53.34, 90.17     # web thickness, pin, main and stub lengths
    pins = []
    x = SL
    for k in range(3):
        pins.append((x + WT + PL / 2, 120 * k))
        x += 2 * WT + PL + (ML if k < 2 else 0)
    L = x + SL                                       # 564.88

    def web(x0, ang, fil=True):
        w = sk('YZ', hull_path([(0, 0, 50.8), (0, -RT, 44.45)]), x0, x0 + WT)
        if fil:
            w = try_fillet(w, None, 2.54)
        return w.rotate((0, 0, 0), (1, 0, 0), ang)
    s1 = xcyl(RM, 0, SL + 0.01)
    s2 = s1
    for xc, a in pins:
        s2 = s2.union(web(xc - PL / 2 - WT, a)).union(web(xc + PL / 2, a))
    s3 = s2
    for xc, a in pins:
        pz, py = -RT * math.cos(math.radians(a)), RT * math.sin(math.radians(a))      # on the web's R1.75 end
        s3 = s3.union(xcyl(RP, xc - PL / 2 - 0.1, xc + PL / 2 + 0.1, py, pz))
    s4 = s3
    for (x0, _), (x1, _) in zip(pins[:-1], pins[1:]):
        s4 = s4.union(xcyl(RM, x0 + PL / 2 + WT - 0.1, x1 - PL / 2 - WT + 0.1))
    s5 = s4.union(xcyl(RM, L - SL - 0.1, L))
    s6 = s5.faces('<X').chamfer(1.5).faces('>X').chamfer(1.5)

    # the build steps make the shaft throw by throw (the same solid as s5 at the end)
    stg = []
    base = s1
    for k, (xc, a) in enumerate(pins):
        x0 = xc - PL / 2 - WT
        pz, py = -RT * math.cos(math.radians(a)), RT * math.sin(math.radians(a))
        w0 = base.union(web(x0, a, False))
        w1 = base.union(web(x0, a))
        pn = w1.union(xcyl(RP, xc - PL / 2 - 0.1, xc + PL / 2 + 0.1, py, pz))
        rw = pn.union(web(xc + PL / 2, a))
        stg.append((w0, w1, pn, rw))
        if k < 2:
            base = rw.union(xcyl(RM, xc + PL / 2 + WT - 0.1, pins[k + 1][0] - PL / 2 - WT + 0.1))
            stg[-1] += (base,)
    part = P('crankshaft_3', 'crankshaft', 'Forged steel 42CrMo4', 'Crankshaft', STEEL, [
        F('front stub', EXTRUDE, ['Sketch a 2.50 in (63.5) circle on the YZ Plane. Extrude 3.55 in (90.17).'], s1,
          note='The drawing is in inches; the model is in millimetres (x 25.4).'),
        F('throw 1: front web', EXTRUDE,
          ['Sketch a web on the end of the stub: a circle R2.00 in (50.8) on the main axis and a circle R1.75 in (44.45) on the pin '
           'centre, 2.50 in (63.5) below, joined by two Tangent lines. Trim. Extrude 0.75 in (19).'], stg[0][0],
          overlay=face_of(web(pins[0][0] - PL / 2 - WT, 0, False), 'YZ'),
          note='The drawing crowns the web faces with an R169 radius; the model keeps them flat.'),
        F('throw 1: web edges', FILLET, ['Fillet R0.10 in (2.54): the outside edge on both faces of the web.'], stg[0][1]),
        F('throw 1: crank pin', EXTRUDE, ['Sketch a 3.00 in (76.2) circle on the web face on the R1.75 centre. Extrude 2.15 in '
                                          '(54.62).'], stg[0][2]),
        F('throw 1: rear web', MIRROR, ['Work Plane through the middle of the pin. Mirror the web and its fillets about it.'],
          stg[0][3]),
        F('main journal 2', EXTRUDE, ['Sketch a 2.50 in (63.5) circle on the main axis on the rear web. Extrude 2.10 in (53.34).'],
          stg[0][4]),
        F('throw 2: front web', EXTRUDE, ['Sketch the same web on the end of journal 2, with the pin centre turned 120 degrees from '
                                          'throw 1 (a construction line at 120 degrees). Extrude 0.75 in (19).'], stg[1][0],
          note='Three throws at 120 degrees: one cylinder fires every 240 degrees of a four stroke cycle.'),
        F('throw 2: web edges', FILLET, ['Fillet R0.10 in (2.54) round both faces of the web.'], stg[1][1]),
        F('throw 2: crank pin', EXTRUDE, ['Sketch a 3.00 in circle on the R1.75 centre. Extrude 2.15 in (54.62).'], stg[1][2]),
        F('throw 2: rear web', MIRROR, ['Mirror the web and its fillets about a Work Plane through the middle of the pin.'],
          stg[1][3]),
        F('main journal 3', EXTRUDE, ['Sketch a 2.50 in circle on the main axis on the rear web. Extrude 2.10 in (53.34).'],
          stg[1][4]),
        F('throw 3: front web', EXTRUDE, ['Sketch the web on the end of journal 3, the pin centre turned 240 degrees from throw 1. '
                                          'Extrude 0.75 in (19).'], stg[2][0]),
        F('throw 3: web edges', FILLET, ['Fillet R0.10 in (2.54) round both faces of the web.'], stg[2][1]),
        F('throw 3: crank pin', EXTRUDE, ['Sketch a 3.00 in circle on the R1.75 centre. Extrude 2.15 in (54.62).'], stg[2][2]),
        F('throw 3: rear web', MIRROR, ['Mirror the web and its fillets about a Work Plane through the middle of the pin.'],
          stg[2][3]),
        F('rear stub', EXTRUDE, ['Sketch a 2.50 in circle on the last web. Extrude 3.55 in (90.17). 22.24 in (564.88) overall.'], s5),
        F('end chamfers', CHAMFER, ['Chamfer the two shaft ends 1.5 mm.'], s6),
    ])
    return single('ax_crankshaft_3', 'Crankshaft, three throw', part,
                  'A three throw crankshaft from an inch drawing: 2.50 in main journals and stubs, three 3.00 in crank pins on a 2.50 in '
                  'throw at 120 degrees, and six pear shaped webs 0.75 in thick. 564.88 mm (22.24 in) long.',
                  'Polar (angular) spacing, inch drawings, filleted webs, long parts on a sheet.',
                  section='y', iso=(1, -1.6, 0.8),
                  note='The R169 crown on the web faces and the R0.64 edge rounds are left off; the webs are flat 19 mm plates with '
                       'R2.54 edges.')


# ================================================================== 15 V-belt pulley (inch drawing)
@functools.lru_cache(None)
def v_pulley():
    RO, RR, RI = 5.63 * IN / 2, 4.75 * IN / 2, 4.30 * IN / 2     # outside, groove root and rim inside radii
    HW, WW = 1.63 * IN / 2, 0.38 * IN / 2                        # half rim width, half web thickness
    RH, RB, HL = 2.13 * IN / 2, 0.75 * IN / 2, 1.51 * IN / 2      # hub radius, bore radius, half hub length
    gw = (RO - RR) * math.tan(math.radians(40))                   # half width of the V at the outside diameter
    blank = rev([(RB, -HL), (RH, -HL), (RH, -WW), (RI, -WW), (RI, -HW), (RO, -HW), (RO, HW), (RI, HW), (RI, WW), (RH, WW),
                 (RH, HL), (RB, HL)])
    groove = rev([(RR, 0), (RO + 1, -gw - 1 * math.tan(math.radians(40))), (RO + 1, gw + 1 * math.tan(math.radians(40)))])
    p2 = blank.cut(groove)
    p3 = p2
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        p3 = p3.cut(zcyl(0.38 * IN, -WW - 1, WW + 1, 3.43 * IN / 2 * math.cos(a), 3.43 * IN / 2 * math.sin(a)))
    p4 = try_fillet(p3, cq.selectors.BoxSelector((-RO - 1, -RO - 1, -0.1), (RO + 1, RO + 1, 0.1)), 2.54)
    p5 = p4.edges(cq.selectors.RadiusNthSelector(0)).chamfer(0.76)
    part = P('v_pulley', 'V-belt pulley', 'Cast iron EN-GJL-250', 'Pulley', IRON, [
        F('blank', REVOLVE, ['Sketch the half section on the XZ Plane: hub 2.13 in diameter x 1.51 in, web 0.38 in thick, rim 4.30 '
                             'to 5.63 in diameter x 1.63 in wide. Revolve 360 degrees about the axis.'], blank,
          note='The drawing is in inches; the model is in millimetres (x 25.4).'),
        F('V groove', REVOLVE, ['Sketch the groove: 80 degrees included (40 degrees each side of the centre line), root on a 4.75 in '
                                'diameter. Revolve, Cut.'], p2,
          note='The 0.38 in ball on the sheet is a gauge for checking the groove.'),
        F('lightening holes', CIRC, ['Hole 0.76 in diameter, Through, on the 3.43 in pitch circle. Circular Pattern: 8 at 45 degrees.'], p3,
          note='Lightening holes take weight out of the web without making it weaker where the load goes.'),
        F('groove root fillet', FILLET, ['Fillet the root of the V R0.10 in (2.54).'], p4),
        F('bore chamfers', CHAMFER, ['Chamfer the bore 0.03 in x 45 degrees both ends.'], p5),
    ])
    return single('ax_v_pulley', 'V-belt pulley (inch drawing)', part,
                  'A cast iron V-belt pulley from an inch drawing: 5.63 in outside, an 80 degree groove, a 0.38 in web with eight 0.76 in '
                  'lightening holes on a 3.43 in pitch circle, and a 2.13 in hub with a 0.75 in bore. Modelled in millimetres.',
                  'Revolved parts, half sections, circular patterns, inch to millimetre conversion.',
                  section='y', iso=(1, -1.2, 1.0),
                  note='The groove root diameter (4.75 in) is read as 5.25 in less two lots of 0.25 in, as the section shows.')


# ------------------------------------------------------------------ pipework helpers
def tube(p0, d, length, ro, ri):
    """A straight pipe from p0 along the unit direction d."""
    return _cyl(ro, p0, d, length).cut(_cyl(ri, tuple(p0[i] - d[i] for i in range(3)), d, length + 2))


def elbow(a, da, db, R, ro, ri, angle=90):
    """A pipe bend that starts at a flowing along da and turns towards db (at right angles to da) on bend radius R."""
    pl = cq.Plane(origin=a, xDir=db, normal=da)
    return cq.Workplane(pl).circle(ro).circle(ri).revolve(angle, (R, 0, 0), (R, 1, 0))


def hole_ring(n, pcd, a0=0):
    return [(pcd / 2 * math.cos(math.radians(a0 + 360 * k / n)), pcd / 2 * math.sin(math.radians(a0 + 360 * k / n))) for k in range(n)]


# ================================================================== 16 pipe run with three gate valves
PV = dict(RO=35, RI=30, BR=105, FR=82.5, FT=18, FF=90, PCD=130, HR=9, RISER=850, TOP=650, LOW=750)


def _gate_valve_local():
    """A small flanged gate valve, flow along X, stem up +Z, centred on the origin (shared by the three valves)."""
    FR, FT, FF, PCD, HR = PV['FR'], PV['FT'], PV['FF'], PV['PCD'], PV['HR']
    b1a = xcyl(40, -FF + FT - 0.1, FF - FT + 0.1)
    b1b = b1a.union(zcyl(52, -55, 70))
    b1 = b1b.union(zcyl(60, 69.9, 82))
    b2 = b1.union(xcyl(FR, -FF, -FF + FT)).union(xcyl(FR, FF - FT, FF))
    b3a = b2.cut(xcyl(PV['RI'], -FF - 1, FF + 1))
    b3 = b3a.cut(_box(-12, 12, -38, 38, -42, 83))
    b4 = b3
    for y, z in hole_ring(4, PCD, 45):
        b4 = b4.cut(xcyl(HR, -FF - 1, FF + 1, y, z))
    bon1 = zcyl(60, 82, 94).union(zcyl(28, 93.9, 175)).union(zcyl(20, 174.9, 192))
    bon2 = bon1.cut(zcyl(10, 81, 193))
    stem1 = _box(-10, 10, -36, 36, -35, 35)
    stem2 = stem1.union(zcyl(9, 34.9, 240))
    hub = zcyl(16, 196, 214)
    rim = cq.Workplane(cq.Plane(origin=(75, 0, 205), xDir=(-1, 0, 0), normal=(0, 1, 0))).circle(7).revolve(360, (75, 0, 0), (75, 1, 0))
    hw1 = hub.union(rim)
    for a in (0, 90):
        hw1 = hw1.union(_cyl(5, (-72 * math.cos(math.radians(a)), -72 * math.sin(math.radians(a)), 205),
                             (math.cos(math.radians(a)), math.sin(math.radians(a)), 0), 144))
    spk = [_cyl(5, (-72 * math.cos(math.radians(a)), -72 * math.sin(math.radians(a)), 205),
                (math.cos(math.radians(a)), math.sin(math.radians(a)), 0), 144) for a in (0, 90)]
    hw_s1 = hub.union(spk[0])              # build step views: spokes before the rim, so each step is one solid
    hw_s2 = hw_s1.union(spk[1])
    hw2 = hw1.cut(zcyl(9.5, 190, 220))
    fl0 = xcyl(FR, -FF - FT, -FF)
    fl1 = fl0.union(xcyl(45, -FF - FT - 22, -FF - FT + 0.1))
    fl2 = fl1.cut(xcyl(PV['RO'], -FF - FT - 23, -FF + 1))
    fl3 = fl2
    for y, z in hole_ring(4, PCD, 45):
        fl3 = fl3.cut(xcyl(HR, -FF - FT - 1, -FF + 1, y, z))
    y, z = hole_ring(4, PCD, 45)[0]
    bolt = hex_bolt(16, 60, 24, 10, (-FF - FT, y, z), axis='x')
    nut = nut_on(16, 24, 13, (-FF + FT, y, z), axis='x')
    return dict(body=(b1a, b1b, b1, b2, b3a, b3, b4), bonnet=(bon1, bon2), stem=(stem1, stem2), wheel=(hub, hw_s1, hw_s2, hw1, hw2),
                flange=(fl0, fl1, fl2, fl3),
                bolt=bolt, nut=nut)


@functools.lru_cache(None)
def pipe_run_valves():
    RO, RI, BR, FF, FT = PV['RO'], PV['RI'], PV['BR'], PV['FF'], PV['FT']
    H = PV['RISER']
    XT, XB, ZR = BR + 225, BR + 300, H / 2           # valve centres: top run, bottom run, riser
    g = _gate_valve_local()
    Ry = R((0, 0, 0), (0, 1, 0), -90)
    Rz = R((0, 0, 0), (0, 0, 1), 90)
    valves = [('top', T(XT, 0, H), (1, 0, 0), (0, 0, 1), (XT, 0, H)),
              ('riser', chain(Ry, Rz, T(0, 0, ZR)), (0, 0, 1), (0, -1, 0), (0, 0, ZR)),
              ('bottom', T(XB, 0, 0), (1, 0, 0), (0, 0, 1), (XB, 0, 0))]
    flip = R((0, 0, 0), (0, 0, 1), 180)                  # the other end of a valve
    turn_b = lambda k: R((0, 0, 0), (1, 0, 0), 90 * k)    # the next bolt round the flange
    inst = lambda label: [('%s %s valve' % (label, v), tf) for v, tf, *_ in valves]
    fl_inst, bolt_inst, nut_inst = [], [], []
    ex = {}
    for v, tf, ax, st, c in valves:
        for side, sgn in (('inlet', -1), ('outlet', 1)):
            ftf = chain(flip, tf) if sgn > 0 else tf
            fl_inst.append(('flange %s, %s' % (v, side), ftf))
            ex['flange %s, %s' % (v, side)] = tuple(sgn * 60 * a for a in ax)
            for k in range(4):
                btf = chain(turn_b(k), flip, tf) if sgn > 0 else chain(turn_b(k), tf)
                bn, nn = 'bolt M16 %s %s %d' % (v, side, k + 1), 'nut M16 %s %s %d' % (v, side, k + 1)
                bolt_inst.append((bn, btf)); nut_inst.append((nn, btf))
                ex[bn] = tuple(sgn * 160 * a for a in ax)
                ex[nn] = tuple(sgn * 100 * a for a in ax)
        ex['bonnet %s valve' % v] = tuple(120 * a for a in st)
        ex['stem and gate %s valve' % v] = tuple(220 * a for a in st)
        ex['handwheel %s valve' % v] = tuple(320 * a for a in st)
    # pipes and bends (made in place)
    e1 = elbow((0, 0, BR), (0, 0, -1), (1, 0, 0), BR, RO, RI)                 # bottom bend: riser down into the bottom run
    pipes = [
        ('riser_low', 'riser pipe, lower', tube((0, 0, BR), (0, 0, 1), ZR - FF - BR, RO, RI), 'Riser 230 long'),
        ('riser_up', 'riser pipe, upper', tube((0, 0, ZR + FF), (0, 0, 1), H - BR - ZR - FF, RO, RI), 'Riser 230 long'),
        ('top_in', 'top pipe, inlet', tube((BR, 0, H), (1, 0, 0), XT - FF - BR, RO, RI), ''),
        ('top_out', 'top pipe, outlet', tube((XT + FF, 0, H), (1, 0, 0), BR + PV['TOP'] - XT - FF, RO, RI), ''),
        ('low_in', 'bottom pipe, inlet', tube((BR, 0, 0), (1, 0, 0), XB - FF - BR, RO, RI), ''),
        ('low_out', 'bottom pipe, outlet', tube((XB + FF, 0, 0), (1, 0, 0), BR + PV['LOW'] - XB - FF, RO, RI), ''),
    ]
    PIPE_MAT = 'Steel pipe EN 10216-2 P235GH, 70 x 5'
    parts = [P('bend', '90 degree bend R105', PIPE_MAT, 'Pipework', SS, [
        F('bend', SWEEP, ['Sketch two circles, 70 and 60, on the XY Plane 105 from the origin. Revolve them 90 degrees about the Y axis '
                          '(a long radius bend: 1.5 x the pipe diameter).'], e1,
          note='In Inventor Tube and Pipe the bends come from the Content Center; this is the same shape as a part.')],
        instances=[('bend 1 (bottom)', None), ('bend 2 (top)', R((0, 0, H / 2), (1, 0, 0), 180))])]
    for key, name, shape, _ in pipes:
        L = round(shape.val().BoundingBox().xlen if 'top' in key or 'low' in key else shape.val().BoundingBox().zlen)
        parts.append(P(key, '%s, %d long' % (name, L), PIPE_MAT, 'Pipework', SS, [
            F('pipe', EXTRUDE, ['Sketch two circles, 70 and 60 diameter. Extrude %d mm.' % L], shape)]))
    parts += [
        P('valve_body', 'gate valve body', 'Cast steel GP240GH', 'Gate valves', BLUE, [
            F('neck', EXTRUDE, ['Sketch an 80 circle on the YZ Plane. Extrude 144, Symmetric (the run between the end flanges).'],
              g['body'][0]),
            F('body', EXTRUDE, ['Sketch a 104 circle on the XY Plane on the centre. Extrude from 55 below the axis to 70 above it.'],
              g['body'][1]),
            F('bonnet flange', EXTRUDE, ['Sketch a 120 circle on the top of the body. Extrude 12.'], g['body'][2]),
            F('end flanges', EXTRUDE, ['Sketch a 165 circle on each end of the neck. Extrude 18 mm outwards (180 face to face).'],
              g['body'][3]),
            F('bore', HOLE, ['Hole on an end flange: diameter 60, Through All, along the flow.'], g['body'][4]),
            F('gate pocket', EXTRUDE, ['Sketch a 24 x 76 rectangle on the top of the bonnet flange. Extrude, Cut, 125 deep (the pocket '
                                       'the gate slides in).'], g['body'][5]),
            F('flange holes', CIRC, ['Hole 18 diameter on the 130 pitch circle, Through both flanges. Circular Pattern: 4.'], g['body'][6])],
          instances=inst('body')),
        P('bonnet', 'bonnet and yoke', 'Cast steel GP240GH', 'Gate valves', BLUE, [
            F('bonnet', REVOLVE, ['Sketch the half section: flange 120 x 12, neck 56 to 175 high, boss 40. Revolve.'], g['bonnet'][0]),
            F('stem bore', HOLE, ['Hole 20 diameter, Through, on the axis.'], g['bonnet'][1])], instances=inst('bonnet')),
        P('stem', 'stem and gate', 'Stainless steel 1.4021', 'Gate valves', SS, [
            F('gate', EXTRUDE, ['Sketch a 72 x 70 rectangle on the XZ Plane. Extrude 20 mm, both sides.'], g['stem'][0]),
            F('stem', EXTRUDE, ['Sketch an 18 circle on top of the gate. Extrude 205 mm.'], g['stem'][1],
              note='A rising stem: turning the handwheel lifts the stem and the gate out of the flow.')],
          instances=inst('stem and gate')),
        P('handwheel', 'handwheel 160', 'Cast iron EN-GJL-200', 'Gate valves', RED, [
            F('hub', EXTRUDE, ['Sketch a 32 circle on the XY Plane. Extrude 18 mm.'], g['wheel'][0]),
            F('first pair of spokes', EXTRUDE, ['Sketch a 10 circle on a Work Plane 72 from the axis. Extrude 144 across the hub.'],
              g['wheel'][1]),
            F('second pair of spokes', CIRC, ['Circular Pattern: the spokes, 2 at 90 degrees (four spokes).'], g['wheel'][2]),
            F('rim', REVOLVE, ['Sketch a 14 circle on the XZ Plane, 75 from the axis, on the spoke ends. Revolve it 360 degrees '
                               'about the axis (a 164 rim).'], g['wheel'][3]),
            F('bore', HOLE, ['Hole 19 diameter, Through, on the axis.'], g['wheel'][4])], instances=inst('handwheel')),
        P('flange', 'slip-on flange DN65', 'Steel P250GH', 'Flanges', DARK, [
            F('flange', EXTRUDE, ['Sketch a 165 circle on the YZ Plane. Extrude 18 mm.'], g['flange'][0]),
            F('hub', EXTRUDE, ['Sketch a 90 circle on the back of the flange. Extrude 22 mm (the hub).'], g['flange'][1]),
            F('bore', HOLE, ['Hole 70 diameter, Through (the pipe slips in and is welded).'], g['flange'][2]),
            F('bolt holes', CIRC, ['Hole 18 diameter on the 130 pitch circle. Circular Pattern: 4.'], g['flange'][3])],
          instances=fl_inst),
        P('bolt', 'hex bolt ISO 4017 M16 x 60', 'Steel 8.8', 'Bought in', STEEL, [F('bolt', CONTENT, [], g['bolt'])],
          instances=bolt_inst, bought=True),
        P('nut', 'hex nut ISO 4032 M16', 'Steel 8', 'Bought in', DARK, [F('nut', CONTENT, [], g['nut'])],
          instances=nut_inst, bought=True),
    ]
    names = lambda key: [n for p in parts if p['key'] == key for n, tf in p['instances']]
    assembly = [
        ('bottom run', PLACE, ['Place bend.ipt Grounded at the foot of the riser and the two bottom pipes along X from it (or route '
                               'the run with Tube and Pipe: bottom run 750, bends R105).'],
         ['bend 1 (bottom)'] + names('low_in') + names('low_out')),
        ('riser', CONSTRAIN, ['Place the two riser pipes on the bend (Mate the axes, Flush the ends), leaving the gap for the riser '
                              'valve, and the second bend at the top (850 up).'],
         names('riser_low') + names('riser_up') + ['bend 2 (top)']),
        ('top run', CONSTRAIN, ['Place the two top pipes along X from the top bend (top run 650).'], names('top_in') + names('top_out')),
        ('flanges', CONSTRAIN, ['Place flange.ipt six times: Insert each one onto a pipe end at a valve gap, face flush with the pipe '
                                'end.'], names('flange')),
        ('gate valve sub-assembly: body', PLACE,
         ['File > New > Standard (mm).iam and save it as gate_valve.iam (a sub-assembly). Place valve_body.ipt Grounded.'],
         names('valve_body'),
         'The gate valve is built once as a sub-assembly and placed three times, so these steps show all three valves.'),
        ('gate valve sub-assembly: bonnet', CONSTRAIN, ['Place bonnet.ipt: Insert its flange on the body flange.'], names('bonnet')),
        ('gate valve sub-assembly: stem and gate', CONSTRAIN, ['Place stem.ipt: Mate the stem axis to the bonnet bore and slide the gate '
                                                               'into the pocket.'], names('stem')),
        ('gate valve sub-assembly: handwheel', CONSTRAIN,
         ['Place handwheel.ipt: Insert it on the top of the stem. Save gate_valve.iam.',
          'In ax_pipe_run_valves.iam, Place gate_valve.iam three times: Mate each end flange face to a pipe flange and line up the '
          'bolt holes (Mate the hole axes).'], names('handwheel')),
        ('bolts and nuts', CONTENT, ['Place from Content Center: ISO 4017 M16 x 60 bolts and ISO 4032 M16 nuts, 4 per joint, 24 of each.'],
         names('bolt') + names('nut')),
    ]
    return dict(name='ax_pipe_run_valves', title='Pipe run with three gate valves', parts=parts, assembly=assembly, explode=ex,
                description='A 70 mm steel pipe run: an 850 riser with a top run of 650 and a bottom run of 750, long radius bends, and '
                            'three flanged gate valves, one on each run, bolted to slip-on flanges with M16 bolts. 74 parts.',
                uses='Pipework isometrics, flanged joints, repeated parts (instances), valve assemblies, rising stem mechanism.',
                criteria='3.1, 3.2', section=None, iso=(1, -1.2, 0.7), material='See parts list', mesh_scale=3,
                note='The drawing is an AI sketch and its sizes do not agree (for example two 750 runs, a 250 flange on a 70 pipe). '
                     'Kept: pipe 70 diameter, riser 850, runs 650 and 750, three valves. The middle valve is drawn with two handwheels; '
                     'the model gives it one. Flanges are DN65 sized (165 diameter, 4 x M16).')


# ================================================================== 17 steam line loop from a piping isometric
NPS = {8: (219.1, 8.18, 304.8), 6: (168.3, 7.11, 228.6), 4: (114.3, 6.02, 152.4)}    # OD, wall (Sch 40), long radius bend


def _bw_valve(od, length, kind):
    """A butt weld valve, flow along X, centred on the origin, stem up +Z.

    Returns the stages of its three parts, each a list of (title, command, actions, shape): body, bonnet with stem, handwheel."""
    ro = od / 2
    ri = ro - NPS[{219.1: 8, 168.3: 6, 114.3: 4}[od]][1]
    b0 = xcyl(ro, -length / 2, length / 2)
    b1 = b0.union(xcyl(1.12 * ro, -0.32 * length, 0.32 * length))
    b2 = b1.union(zcyl(1.3 * ro, -1.05 * ro, 1.25 * ro))
    b3 = b2.union(zcyl(1.42 * ro, 1.249 * ro, 1.42 * ro))
    body = b3.cut(xcyl(ri, -length / 2 - 1, length / 2 + 1))
    top = 3.6 * ro if kind == 'gate' else 2.6 * ro
    n0 = zcyl(1.42 * ro, 1.42 * ro, 1.58 * ro)
    n1 = n0.union(zcyl(0.5 * ro, 1.579 * ro, top))
    n2 = n1.union(zcyl(0.32 * ro, top - 0.01, top + 0.2 * ro))
    bon = n2.union(zcyl(0.1 * ro, top + 0.19 * ro, top + 0.75 * ro))
    zw, Rw = top + 0.45 * ro, (1.0 if kind == 'gate' else 0.7) * ro
    rim = cq.Workplane(cq.Plane(origin=(Rw, 0, zw), xDir=(-1, 0, 0), normal=(0, 1, 0))).circle(0.07 * ro).revolve(
        360, (Rw, 0, 0), (Rw, 1, 0))
    w0 = zcyl(0.2 * ro, zw - 0.08 * ro, zw + 0.08 * ro)
    wheel = w0.union(rim)
    for a in (0, 120, 240):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        wheel = wheel.union(_cyl(0.045 * ro, (0.15 * ro * c, 0.15 * ro * s, zw), (c, s, 0), Rw - 0.17 * ro))
    w3 = wheel
    wheel = wheel.cut(zcyl(0.1 * ro, zw - ro, zw + ro))
    sp = [_cyl(0.045 * ro, (0.15 * ro * math.cos(math.radians(a)), 0.15 * ro * math.sin(math.radians(a)), zw),
               (math.cos(math.radians(a)), math.sin(math.radians(a)), 0), Rw - 0.17 * ro) for a in (0, 120, 240)]
    w1s = w0.union(sp[0])                  # build step views: the spokes go on before the rim, so each step is one solid
    w2s = w1s.union(sp[1]).union(sp[2])
    f = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')
    body_steps = [
        ('weld end barrel', EXTRUDE, ['Sketch a %s circle (the pipe outside diameter) on the YZ Plane. Extrude %s, Symmetric: the '
                                      'face to face length, so the pipe butt welds to each end.' % (f(od), f(length))], b0),
        ('body', EXTRUDE, ['Sketch a %s circle on the YZ Plane. Extrude %s, Symmetric (the thicker middle of the body).'
                           % (f(2.24 * ro), f(0.64 * length))], b1),
        ('bonnet neck', EXTRUDE, ['Sketch a %s circle on the XY Plane on the centre. Extrude from %s below the axis to %s above it.'
                                  % (f(2.6 * ro), f(1.05 * ro), f(1.25 * ro))], b2),
        ('bonnet flange', EXTRUDE, ['Sketch a %s circle on the top of the neck. Extrude %s.' % (f(2.84 * ro), f(0.171 * ro))], b3),
        ('bore', HOLE, ['Hole on a weld end: diameter %s (the pipe bore), Through All.' % f(2 * ri)], body),
    ]
    bonnet_steps = [
        ('bonnet flange', EXTRUDE, ['Sketch a %s circle on the XY Plane. Extrude %s (it bolts to the body flange).'
                                    % (f(2.84 * ro), f(0.16 * ro))], n0),
        ('yoke', EXTRUDE, ['Sketch a %s circle on the flange. Extrude %s.' % (f(ro), f(top - 1.579 * ro))], n1),
        ('gland', EXTRUDE, ['Sketch a %s circle on the top of the yoke. Extrude %s.' % (f(0.64 * ro), f(0.2 * ro))], n2),
        ('stem', EXTRUDE, ['Sketch a %s circle on the gland. Extrude %s (the stem the handwheel turns).' % (f(0.2 * ro), f(0.56 * ro))],
         bon),
    ]
    wheel_steps = [
        ('hub', EXTRUDE, ['Sketch a %s circle on the XY Plane. Extrude %s, Symmetric.' % (f(0.4 * ro), f(0.16 * ro))], w0),
        ('first spoke', EXTRUDE, ['Sketch a %s circle on a Work Plane on the hub side. Extrude it %s out (to the middle of the '
                                  'rim).' % (f(0.09 * ro), f(Rw - 0.17 * ro))], w1s),
        ('pattern the spokes', CIRC, ['Circular Pattern: the spoke, 3 round the axis.'], w2s),
        ('rim', REVOLVE, ['Sketch a %s circle on the XZ Plane, %s from the axis, on the spoke ends. Revolve it 360 degrees about '
                          'the axis.' % (f(0.14 * ro), f(Rw))], w3),
        ('bore', HOLE, ['Hole on the hub: diameter %s, Through All (it fits the stem).' % f(0.2 * ro)], wheel),
    ]
    return body_steps, bonnet_steps, wheel_steps


def _wn_flange(od, flange_r, t, hub_r, length):
    """A weld neck flange along +X from x = 0 (the face) to x = length (the weld end)."""
    ro = od / 2
    ri = ro - NPS[{219.1: 8, 168.3: 6, 114.3: 4}[od]][1]
    return rev([(ri, 0), (flange_r, 0), (flange_r, t), (hub_r, t), (ro, length), (ri, length)], axis='x')


def _pipe_support(h, ro, axis):
    """A pipe support standing on Z = 0 with the pipe saddle at the top (pipe axis along 'x' or 'y'); h = pipe underside.

    Returns its stages, a list of (title, command, actions, shape); the last shape is the support."""
    base0 = _box(-125, 125, -125, 125, 0, 16)
    base = base0
    for x in (-95, 95):
        for y in (-95, 95):
            base = base.cut(zcyl(9, -1, 17, x, y))
    col = _box(-50, 50, -50, 50, 15.9, h - 19.9).cut(_box(-44, 44, -44, 44, 15, h))
    w, a = ro + 25, 40
    if axis == 'x':
        saddle = _box(-a, a, -w, w, h - 20, h + 0.4 * ro)
        cutter = xcyl(ro, -200, 200, 0, h + ro)
    else:
        saddle = _box(-w, w, -a, a, h - 20, h + 0.4 * ro)
        cutter = ycyl(ro, -200, 200, 0, h + ro)
    s1 = base.union(col)
    s = s1.union(saddle.cut(cutter))
    s2 = s
    g = min(120, h / 3)
    for sgn in (-1, 1):
        s = s.union(sk('XZ', [(sgn * 50, 16), (sgn * 120, 16), (sgn * 50, 16 + g)], -4, 4))
        if sgn < 0:
            s3 = s
    f = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')
    return [
        ('base plate', EXTRUDE, ['Sketch a 250 x 250 square on the XY Plane, centred. Extrude 16 mm.'], base0),
        ('holding down holes', RECT, ['Hole 18 diameter, Through, at one corner, 95 from both centre lines. Rectangular Pattern '
                                      '2 x 2, 190 apart (for M16 anchor bolts).'], base),
        ('box column', EXTRUDE, ['Sketch a 100 x 100 square and a 88 x 88 square inside it on the top of the plate. Extrude %s up '
                                 '(a 100 x 100 x 6 box section).' % f(h - 35.8)], s1),
        ('saddle', EXTRUDE, ['Sketch on the side of the column the saddle: a rectangle %s wide with a %s radius arc cut into its top '
                             '(the pipe outside). Extrude 80, Symmetric.' % (f(2 * w), f(ro))], s2),
        ('first gusset', RIB, ['Sketch a triangle on the XZ Plane against the column: 70 along the plate (from the column face to 120 out) and %s up the column. '
                               'Extrude 8, Symmetric (or Rib).' % f(g)], s3),
        ('mirror the gusset', MIRROR, ['Mirror the gusset about the YZ Plane.'], s),
    ]


@functools.lru_cache(None)
def steam_line_loop():
    o8, w8, R8 = NPS[8]; o6, w6, R6 = NPS[6]; o4, w4, R4 = NPS[4]
    r8, i8, r6, i6, r4, i4 = o8 / 2, o8 / 2 - w8, o6 / 2, o6 / 2 - w6, o4 / 2, o4 / 2 - w4
    ZB, ZT, XR, ZI = 1000.0, 2400.0, 1500.0, 300.0        # bottom run, top run, right leg, inlet level
    XT, TC, TM = 500.0, 143.0, 130.0                     # tee centre, run and branch centre to end
    RL = 203.0                                           # reducer length
    GV = (XR, 0, 1750.0); GL = 419.0                     # gate valve centre and length
    BV, BL = 950.0, 267.0                                # ball valve centre and face to face
    NV = (0, -1200.0, ZI); NL = 292.0
    WN = 88.9
    # fittings
    e8 = elbow((0, 0, ZT - R8), (0, 0, 1), (1, 0, 0), R8, r8, i8)
    e6 = elbow((R6, 0, ZB), (-1, 0, 0), (0, 0, 1), R6, r6, i6)
    e4 = elbow((XT, 0, ZI + R4), (0, 0, -1), (-1, 0, 0), R4, r4, i4)
    flip_x = R((XR / 2, 0, 0), (0, 0, 1), 180)
    e4b = chain(R((0, 0, 0), (1, 1, 1), 120), T(-300, -500, 300))
    red = rev([(r6, 0), (r6, 50), (r8, RL - 50), (r8, RL), (i8, RL), (i8, RL - 50), (i6, 50), (i6, 0)])
    red_l = red.translate((0, 0, ZT - R8 - RL))
    tee0 = xcyl(r6, XT - TC, XT + TC, 0, ZB)
    tee1 = tee0.union(zcyl(r4, ZB - TM, ZB - 0.5 * r6, XT, 0))
    tee2 = tee1.cut(xcyl(i6, XT - TC - 1, XT + TC + 1, 0, ZB))
    tee = tee2.cut(zcyl(i4, ZB - TM - 1, ZB, XT, 0))
    # valves
    gate_st = _bw_valve(o8, GL, 'gate')
    needle_st = _bw_valve(o4, NL, 'globe')
    gate_tf = chain(R((0, 0, 0), (0, 1, 0), -90), R((0, 0, 0), (0, 0, 1), 180), T(*GV))       # flow down the right leg, wheel out to +X
    needle_tf = chain(R((0, 0, 0), (0, 0, 1), 90), T(*NV))                                   # flow along -Y, wheel up
    FR6, FT6, PCD6 = 279.4 / 2, 25.4, 241.3
    bv0 = xcyl(FR6, -BL / 2, -BL / 2 + FT6)
    bv1 = bv0.union(xcyl(FR6, BL / 2 - FT6, BL / 2))
    bv2 = bv1.union(xcyl(r6 + 12, -BL / 2 + FT6 - 0.1, BL / 2 - FT6 + 0.1))
    bv3 = bv2.union(sphere(1.25 * r6, (0, 0, 0)))
    bv4 = bv3.union(zcyl(0.3 * r6, 0, 1.9 * r6))
    bv5 = bv4.cut(xcyl(i6, -BL / 2 - 1, BL / 2 + 1))
    bv1s = bv0.union(xcyl(r6 + 12, -BL / 2 + FT6 - 0.1, BL / 2 - FT6 + 0.1))     # build step view: the barrel before the mirror
    bvb = bv5
    for y, z in hole_ring(8, PCD6, 22.5):
        bvb = bvb.cut(xcyl(11.2, -BL / 2 - 1, BL / 2 + 1, y, z))
    lv0 = _box(-20, 3.2 * r6, -14, 14, 1.9 * r6, 1.9 * r6 + 16)
    lv1 = lv0.union(zcyl(25, 1.9 * r6, 1.9 * r6 + 30))
    lever = lv1.union(_box(3.0 * r6, 3.4 * r6, -18, 18, 1.9 * r6 - 10, 1.9 * r6 + 16))
    ball_tf = T(BV, 0, ZB)
    wn0 = _wn_flange(o6, FR6, FT6, 96, WN)
    wn = wn0
    for y, z in hole_ring(8, PCD6, 22.5):
        wn = wn.cut(xcyl(11.2, -1, FT6 + 1, y, z))
    wn_r = T(BV + BL / 2, 0, ZB)                                    # outlet flange: face on the valve, neck going +X
    wn_l = chain(R((0, 0, 0), (0, 0, 1), 180), T(BV - BL / 2, 0, ZB))
    y, z = hole_ring(8, PCD6, 22.5)[0]
    bolt = hex_bolt(20, 90, 30, 12.5, (FT6, y, z), axis='-x')      # head on the flange back face, shank into the valve
    nut = nut_on(20, 30, 18, (-FT6, y, z), axis='-x')
    bolt_inst, nut_inst, ex = [], [], {}
    for side, ftf in (('outlet', wn_r), ('inlet', wn_l)):
        sgn = 1 if side == 'outlet' else -1
        for k in range(8):
            tf = chain(R((0, 0, 0), (1, 0, 0), 45 * k), T(BL / 2, 0, 0), ftf)
            bolt_inst.append(('bolt M20 %s %d' % (side, k + 1), tf)); nut_inst.append(('nut M20 %s %d' % (side, k + 1), tf))
            ex['bolt M20 %s %d' % (side, k + 1)] = (sgn * 250, 0, 0)
    bolt0 = bolt.translate((-BL / 2, 0, 0))     # placed by the transforms above (T(BL / 2) then the flange position)
    nut0 = nut.translate((-BL / 2, 0, 0))
    sup_t_st = [(t, c, a, w.translate((1222, 0, 0))) for t, c, a, w in _pipe_support(ZB - r6, r6, 'x')]
    sup_s = _pipe_support(ZI - r4, r4, 'y')[-1][3].translate((0, -1600, 0))
    # straight pipes: (key, name, NPS, start, direction, length)
    runs = [
        ('p8_top', 'top run', 8, (R8, 0, ZT), (1, 0, 0), XR - 2 * R8),
        ('p8_leg_up', 'right leg above the gate valve', 8, (XR, 0, GV[2] + GL / 2), (0, 0, 1), ZT - R8 - GV[2] - GL / 2),
        ('p8_leg_low', 'right leg below the gate valve', 8, (XR, 0, ZB + R6 + RL), (0, 0, 1), GV[2] - GL / 2 - ZB - R6 - RL),
        ('p6_riser', 'left riser', 6, (0, 0, ZB + R6), (0, 0, 1), ZT - R8 - RL - ZB - R6),
        ('p6_left', 'tee to the left bend', 6, (R6, 0, ZB), (1, 0, 0), XT - TC - R6),
        ('p6_mid', 'tee to the ball valve', 6, (XT + TC, 0, ZB), (1, 0, 0), BV - BL / 2 - WN - XT - TC),
        ('p6_right', 'ball valve to the right bend', 6, (BV + BL / 2 + WN, 0, ZB), (1, 0, 0), XR - R6 - BV - BL / 2 - WN),
        ('p4_drop', 'branch drop', 4, (XT, 0, ZI + R4), (0, 0, 1), ZB - TM - ZI - R4),
        ('p4_cross', 'cross pipe', 4, (R4, 0, ZI), (1, 0, 0), XT - 2 * R4),
        ('p4_in1', 'inlet to the needle valve', 4, (0, -R4, ZI), (0, -1, 0), -NV[1] - NL / 2 - R4),
        ('p4_in2', 'inlet end', 4, (0, NV[1] - NL / 2, ZI), (0, -1, 0), 2000 + NV[1] - NL / 2),
    ]
    sizes = {8: (r8, i8), 6: (r6, i6), 4: (r4, i4)}
    PM = 'Carbon steel A106 Gr B, Sch 40'
    parts = []
    for key, name, n, p0, d, L in runs:
        ro, ri = sizes[n]
        parts.append(P(key, '%d" pipe, %s, %d long' % (n, name, round(L)), PM, 'Pipe', SS, [
            F('pipe', EXTRUDE, ['Sketch two circles, %.1f and %.1f diameter (%d inch, Schedule 40). Extrude %d mm.'
                                % (2 * ro, 2 * ri, n, round(L))], tube(p0, d, L, ro, ri))]))
    parts += [
        P('elbow8', '8" elbow 90 LR', 'A234 WPB', 'Fittings', TEAL, [F('elbow', REVOLVE, [
            'Sketch circles 219.1 and 202.7 on the XY Plane, 304.8 from the origin. Revolve 90 degrees (long radius = 1.5 x 8 in).'], e8)],
          instances=[('8" elbow top left', None), ('8" elbow top right', flip_x)]),
        P('elbow6', '6" elbow 90 LR', 'A234 WPB', 'Fittings', TEAL, [F('elbow', REVOLVE, [
            'Sketch circles 168.3 and 154.1, 228.6 from the origin. Revolve 90 degrees.'], e6)],
          instances=[('6" elbow bottom left', None), ('6" elbow bottom right', flip_x)]),
        P('elbow4', '4" elbow 90 LR', 'A234 WPB', 'Fittings', TEAL, [F('elbow', REVOLVE, [
            'Sketch circles 114.3 and 102.3, 152.4 from the origin. Revolve 90 degrees.'], e4)],
          instances=[('4" elbow 1', None), ('4" elbow 2', e4b)]),
        P('reducer', '8" x 6" concentric reducer', 'A234 WPB', 'Fittings', TEAL, [F('reducer', REVOLVE, [
            'Sketch the half section: 6 in end, 50 straight, taper, 8 in end, 203 long. Revolve.'], red_l)],
          instances=[("reducer left riser", None), ("reducer right leg", T(XR, 0, ZB + R6 - (ZT - R8 - RL)))]),
        P('tee', '6" x 4" reducing tee', 'A234 WPB', 'Fittings', TEAL, [
            F('run', EXTRUDE, ['Sketch a 168.3 circle on the YZ Plane. Extrude 286, Symmetric (the run, 143 centre to end).'], tee0),
            F('branch', EXTRUDE, ['Sketch a 114.3 circle on the XY Plane on the centre. Extrude 130 down (the branch, centre to end).'],
              tee1),
            F('run bore', HOLE, ['Hole on a run end: diameter 154.1, Through All.'], tee2),
            F('branch bore', HOLE, ['Hole on the branch end: diameter 102.3, To the run bore.'], tee)]),
        P('gate_body', '8" gate valve body GV-101', 'A216 WCB', 'Valves', BLUE,
          [F(t, c, a, gate_tf(w)) for t, c, a, w in gate_st[0]],
          ),
        P('gate_bonnet', '8" gate valve bonnet and stem', 'A216 WCB', 'Valves', BLUE,
          [F(t, c, a, gate_tf(w)) for t, c, a, w in gate_st[1]]),
        P('gate_wheel', '8" gate valve handwheel', 'Cast iron', 'Valves', RED,
          [F(t, c, a, gate_tf(w)) for t, c, a, w in gate_st[2]]),
        P('ball_body', '6" ball valve body BV-101', 'A216 WCB', 'Valves', ORANGE, [
            F('first end flange', EXTRUDE, ['Sketch a 279.4 circle on a Work Plane 133.5 from the centre. Extrude 25.4 mm inwards '
                                            '(a class 150 flange).'], ball_tf(bv0)),
            F('body barrel', EXTRUDE, ['Sketch a 192.3 circle on the inside face of the flange. Extrude 216 mm, to where the other '
                                       'flange starts.'], ball_tf(bv1s)),
            F('second end flange', MIRROR, ['Mirror the flange about the YZ Plane: 267 face to face (short pattern).'],
              ball_tf(bv2)),
            F('ball housing', REVOLVE, ['Sketch a half circle R105 on the XZ Plane on the centre. Revolve 360 degrees (the round body '
                                        'round the ball).'], ball_tf(bv3)),
            F('stem neck', EXTRUDE, ['Sketch a 50.5 circle on the XY Plane on the centre. Extrude 160 up.'], ball_tf(bv4)),
            F('bore', HOLE, ['Hole on a flange face: diameter 154.1, Through All (full bore).'], ball_tf(bv5)),
            F('flange bolt holes', CIRC, ['Hole 22.4 diameter on the 241.3 pitch circle, Through All. Circular Pattern: 8 '
                                          '(class 150, 6 in).'], ball_tf(bvb))]),
        P('ball_lever', '6" ball valve lever', 'Steel, painted', 'Valves', RED, [
            F('handle', EXTRUDE, ['Sketch a 289 x 28 rectangle on the top of the stem neck, from 20 behind the stem along the pipe. '
                                  'Extrude 16.'], ball_tf(lv0)),
            F('stem boss', EXTRUDE, ['Sketch a 50 circle on the stem centre. Extrude 30.'], ball_tf(lv1)),
            F('grip', EXTRUDE, ['Sketch a 34 x 36 rectangle at the end of the handle. Extrude 26 (10 below the handle).'],
              ball_tf(lever))]),
        P('needle_body', '4" needle valve body NV-101', 'A182 F304', 'Valves', BLUE,
          [F(t, c, a, needle_tf(w)) for t, c, a, w in needle_st[0]]),
        P('needle_bonnet', '4" needle valve bonnet and stem', 'A182 F304', 'Valves', BLUE,
          [F(t, c, a, needle_tf(w)) for t, c, a, w in needle_st[1]]),
        P('needle_wheel', '4" needle valve handwheel', 'Cast iron', 'Valves', RED,
          [F(t, c, a, needle_tf(w)) for t, c, a, w in needle_st[2]]),
        P('wn_flange', '6" weld neck flange, class 150', 'A105', 'Flanges', DARK, [
            F('flange and neck', REVOLVE, ['Sketch the half section on the XZ Plane: 279.4 diameter x 25.4 thick, the hub tapering from '
                                           '192 to 168.3 at the weld end, 88.9 long, bore 154.1. Revolve.'], wn_r(wn0)),
            F('bolt holes', CIRC, ['Hole 22.4 diameter on the 241.3 pitch circle, Through the flange. Circular Pattern: 8.'], wn_r(wn))],
          instances=[('6" flange, ball valve outlet', None), ('6" flange, ball valve inlet', lambda w: wn_l(wn))]),
        P('support_tall', 'pipe support SP-101, tall', 'Steel S275', 'Supports', OLIVE,
          [F(t, c, a, w) for t, c, a, w in sup_t_st]),
        P('support_short', 'pipe support SP-101, short', 'Steel S275', 'Supports', OLIVE, [
            F('copy the tall support', 'Manage tab > Parameters panel > Parameters',
              ['Open support_tall.ipt and Save As support_short.ipt. Manage tab > Parameters: change the column height to 207 (the '
               'saddle under the 4 in pipe, 243 up) and turn the saddle sketch 90 degrees, so it sits across the inlet pipe.'], sup_s,
              note='Saving a copy and changing its parameters is quicker than modelling the same support twice.')]),
        P('bolt', 'stud bolt M20 x 90', 'A193 B7', 'Bought in', STEEL, [F('bolt', CONTENT, [], bolt0)],
          instances=bolt_inst, bought=True),
        P('nut', 'hex nut M20', 'A194 2H', 'Bought in', DARK, [F('nut', CONTENT, [], nut0)], instances=nut_inst, bought=True),
    ]
    names = lambda *keys: [n for p in parts if p['key'] in keys for n, tf in p['instances']]
    pipe_keys = [r[0] for r in runs]
    assembly = [
        ('supports', PLACE, ['Place support_tall.ipt Grounded on the floor (Z = 0, the T.O.C. line), 1222 along the bottom run, and '
                             'support_short.ipt Grounded under the inlet, 1600 out.'], names('support_tall', 'support_short')),
        ('bottom run: tee', CONSTRAIN, ['Place tee.ipt. Mate its run axis to a Work Axis 1000 up (the bottom run) and its branch '
                                        'axis 500 along, pointing down.'], names('tee')),
        ('bottom run: 6 in elbows', CONSTRAIN, ['Place elbow6.ipt twice, at the two bottom corners of the loop: Mate each end axis to '
                                                'the run axis and to a leg axis.'], names('elbow6')),
        ('bottom run: pipes', CONSTRAIN, ['Place the three 6 in pipes between the tee, the elbows and the ball valve: Mate each axis '
                                          'to the run, Flush the ends to the fitting faces (butt welds).'],
         names('p6_left', 'p6_mid', 'p6_right')),
        ('ball valve sub-assembly: body and lever', PLACE,
         ['File > New > Standard (mm).iam and save it as ball_valve.iam (a sub-assembly).',
          'Place ball_body.ipt Grounded. Place ball_lever.ipt: Mate its boss to the top of the stem neck and its handle along the pipe '
          '(valve open).'], names('ball_body', 'ball_lever'),
         'A sub-assembly is built and checked on its own, then placed in the main assembly as one component.'),
        ('ball valve sub-assembly: weld neck flanges', CONSTRAIN,
         ['Place wn_flange.ipt twice. Mate each flange face to a valve end flange and Mate one bolt hole axis on each to a valve '
          'bolt hole, so the holes line up.'], names('wn_flange')),
        ('ball valve sub-assembly: bolting', CONTENT,
         ['Place from Content Center: 16 stud bolts M20 x 90 (A193 B7) through the flange holes and 16 hex nuts M20 (A194 2H) on '
          'them. Save ball_valve.iam.',
          'In ax_steam_line_loop.iam, Place ball_valve.iam on the bottom run: Mate its axis to the run and Flush the flange necks to '
          'the pipe ends.'], names('bolt', 'nut')),
        ('left riser', CONSTRAIN, ['Place reducer.ipt on the top of the left 6 in elbow (small end down) and the 6 in riser pipe '
                                   'between them: Mate the axes, Flush the ends.'], ['reducer left riser'] + names('p6_riser')),
        ('top run', CONSTRAIN, ['Place elbow8.ipt twice at the top corners and the 8 in top pipe between them.'],
         ['8" elbow top left', '8" elbow top right'] + names('p8_top')),
        ('right leg: reducer and lower pipe', CONSTRAIN, ['Place the second reducer on the right 6 in elbow and the lower 8 in leg pipe '
                                                          'on it.'], ['reducer right leg'] + names('p8_leg_low')),
        ('gate valve sub-assembly', CONSTRAIN,
         ['File > New > Standard (mm).iam and save it as gate_valve.iam. Place gate_body.ipt Grounded, Mate gate_bonnet.ipt to the '
          'body flange and Insert gate_wheel.ipt on the stem. Save gate_valve.iam.',
          'In ax_steam_line_loop.iam, Place gate_valve.iam on the right leg: Mate its axis to the leg, Flush its lower weld end to the '
          'lower pipe and turn the handwheel out to +X.'], names('gate_body', 'gate_bonnet', 'gate_wheel')),
        ('right leg: upper pipe', CONSTRAIN, ['Place the upper 8 in leg pipe between the gate valve and the top right elbow.'],
         names('p8_leg_up')),
        ('branch: drop and cross pipes', CONSTRAIN, ['Place the 4 in drop pipe under the tee branch, elbow4.ipt twice at the foot and '
                                                     'the corner, and the 4 in cross pipe between them.'],
         names('p4_drop', 'p4_cross') + ['4" elbow 1', '4" elbow 2']),
        ('needle valve sub-assembly', CONSTRAIN,
         ['File > New > Standard (mm).iam and save it as needle_valve.iam. Place needle_body.ipt Grounded, Mate needle_bonnet.ipt to '
          'the body flange and Insert needle_wheel.ipt on the stem. Save needle_valve.iam.',
          'In ax_steam_line_loop.iam, Place needle_valve.iam on the inlet line (wheel up).'],
         names('needle_body', 'needle_bonnet', 'needle_wheel')),
        ('inlet pipes', CONSTRAIN, ['Place the two 4 in inlet pipes either side of the needle valve, the outer one resting on the short '
                                    'support.'], names('p4_in1', 'p4_in2')),
    ]
    ex.update({n: (0, 0, 250) for n in names('ball_lever')})
    ex.update({n: (250, 0, 0) for n in names('gate_wheel')})
    ex.update({n: (150, 0, 0) for n in names('gate_bonnet')})
    ex.update({n: (0, 0, 220) for n in names('needle_wheel')})
    ex.update({n: (0, 0, 130) for n in names('needle_bonnet')})
    ex.update({'6" flange, ball valve outlet': (120, 0, 0), '6" flange, ball valve inlet': (-120, 0, 0)})
    return dict(name='ax_steam_line_loop', title='Steam line loop (piping isometric)', parts=parts, assembly=assembly, explode=ex,
                description='A steam line built from a piping isometric and its bill of materials: an 8 inch top run with a gate valve, '
                            'a 6 inch loop with a flanged ball valve, a 6 x 4 tee and a 4 inch inlet with a needle valve, on two pipe '
                            'supports. Schedule 40 pipe, long radius elbows.',
                uses='Reading a piping isometric and a BOM, standard pipe sizes (NPS, schedules), fittings, Tube and Pipe.',
                criteria='3.1, 3.2', section=None, iso=(1, -1.1, 0.8), material='See parts list', mesh_scale=8,
                note='The isometric is a teaching poster and some of its callouts and BOM lines do not agree. The model keeps the BOM sizes '
                     'and counts; it adds two 8 inch elbows, two 8 x 6 reducers and the flange bolting, which the loop needs but the BOM '
                     'leaves out. The gate and needle valves are butt welded, so the only flanges are the two on the ball valve.')


# ================================================================== 18 oil pan (sump), overall inch sizes only
@functools.lru_cache(None)
def oil_pan():
    L, W, FT = 21.13 * IN, 9.29 * IN, 8.0                 # 536.7 long, flange 236 wide, flange 8 thick
    WS, WALL = 8.62 * IN / 2 + 3, 5.0                     # sump outer half width (112.5), wall
    D1, D2, XS = 1.93 * IN, 6.60 * IN, 5.85 * IN          # shallow depth 49, deep 167.6, shallow length 148.6
    X0, X1 = 12.0, L - 12.0
    prof = lambda o: [(X0 + o, 0 + (1 if o else 0)), (X0 + o, -D1 + o), (XS - 0.4 * o, -D1 + o), (XS + 45 - 0.4 * o, -D2 + o),
                      (X1 - o, -D2 + o), (X1 - o, 0 + (1 if o else 0))]
    flange = sk('XY', hull_path([(25, 25, 25), (L - 25, 25, 25), (L - 25, W - 25, 25), (25, W - 25, 25)]), -FT, 0).translate((0, -W / 2, 0))
    outer = sk('XZ', prof(0), -WS, WS)
    outer = try_fillet(outer, '|Y', 20)
    s1 = flange.union(outer)
    s2 = s1
    bolts = [(x, sgn * 121) for x in (20, 92, 164, 236, 308, 380, 452, L - 20) for sgn in (-1, 1)] + \
            [(-2, y) for y in (-60, 60)] + [(L + 2, y) for y in (-60, 0, 60)]
    for x, y in bolts:
        s2 = s2.union(zcyl(9, -FT, 0, x, y))
    inner = sk('XZ', prof(WALL), -WS + WALL, WS - WALL)
    inner = try_fillet(inner, '|Y', 15)
    s3 = s2.cut(inner)
    s1a = flange.union(sk('XZ', prof(0), -WS, WS))                           # build step views: before the fillets
    s3a = s2.cut(sk('XZ', prof(WALL), -WS + WALL, WS - WALL))
    s4 = s3
    for x, y in bolts:
        s4 = s4.cut(zcyl(4.5, -FT - 1, 1, x, y))
    XF, ZF = 470.0, -95.0
    s5a = s4.union(ycyl(40, -134, -WS + 2, XF, ZF))
    s5 = s5a.union(_box(XF - 40, XF + 40, -WS - 10, -WS + 2, ZF, -FT))
    s6a = s5.cut(ycyl(25, -135, -124, XF, ZF))
    s6 = s6a.cut(ycyl(10, -136, -WS + WALL + 1, XF, ZF))
    XD = XS + 7.57 * IN - 7.0
    s7a = s6.union(zcyl(15, -D2 - 8, -D2 + 1, XD, 40))
    s7 = s7a.cut(zcyl(7, -D2 - 9, -D2 + WALL + 1, XD, 40))
    part = P('oil_pan', 'oil pan', 'Cast aluminium A356-T6', 'Sump', CAST, [
        F('flange', EXTRUDE, ['Sketch a rectangle 21.13 x 9.29 in (536.7 x 236) with R25 corners on the XY Plane. Extrude 8 mm down.'],
          flange, note='Only the overall sizes are given (in inches); the rest is read from the views.'),
        F('sump', EXTRUDE, ['Sketch the side profile on the XZ Plane: shallow end 1.93 in (49) deep for 5.85 in (148.6), a slope, then '
                            'the deep end, 6.60 in (167.6) deep. Extrude 225 wide, Symmetric.'], s1a),
        F('round the sump', FILLET, ['Fillet R20 the edges across the width of the sump (the bends in the bottom and the ends).'],
          s1),
        F('bolt bosses', EXTRUDE, ['Sketch 18 diameter circles on the 21 bolt centres round the flange edge (8 down each side, 2 on '
                                   'the front end and 3 on the back). Extrude 8 mm.'], s2),
        F('hollow', EXTRUDE, ['Sketch on the XZ Plane the inside profile, 5 mm inside the outside one (Offset 5). Extrude, Cut, '
                              '215 wide, Symmetric, up through the flange.'], s3a,
          note='A die cast or sand cast sump is a thin even wall. A Shell would also hollow the flange, so the inside is cut '
               'with an offset sketch instead.'),
        F('round the inside', FILLET, ['Fillet R15 the inside bends (the outside R20 less the 5 wall).'], s3),
        F('bolt holes', HOLE, ['Hole 9 diameter, Through, on every boss (M8 clearance).'], s4),
        F('oil filter boss', EXTRUDE, ['Sketch an 80 circle on a Work Plane on the side, 470 along and 95 down. Extrude out to 134 from '
                                       'the centre line (10.55 in overall width).'], s5a),
        F('boss web', EXTRUDE, ['Sketch on the side an 80 wide rectangle from the boss centre up to the flange. Extrude 12 mm '
                                '(10 out from the wall).'], s5),
        F('filter seat', EXTRUDE, ['Sketch a 50 circle on the boss face. Extrude, Cut, 10 mm.'], s6a),
        F('oil way', HOLE, ['Hole 20 diameter from the seat into the sump.'], s6),
        F('drain boss', EXTRUDE, ['Sketch a 30 circle under the deep end. Extrude 8 mm down.'], s7a),
        F('drain hole', HOLE, ['Hole 14 diameter into the sump (for an M14 drain plug).'], s7),
    ])
    return single('ax_oil_pan', 'Engine oil pan', part,
                  'A cast aluminium engine oil pan (sump) 21.13 x 10.55 x 6.60 in: a flanged rim with 21 bolt bosses, a shallow front '
                  'section and a deep rear sump, an oil filter boss on the side and a drain boss underneath. 5 mm wall.',
                  'Shelled castings, working from overall sizes, side and plan views, reading a photo realistic drawing.',
                  section='y', iso=(1, -1.3, 0.9),
                  note='The drawing gives only overall sizes (21.13, 9.29, 8.62, 10.55, 1.93, 5.85, 6.60, 7.57, 7.67 in). The wall, bosses, '
                       'filter boss and drain sizes are typical values, not from the sheet. The cross ribs on the side are left off.')


# ================================================================== 19 engine block deck (inch drawing)
@functools.lru_cache(None)
def engine_block():
    L, YT, YB, H = 546.0, 81.0, -158.0, 180.0           # length, deck edges from the bore line, block depth
    RB, PB = 3.684 * IN / 2, 4.85 * IN                    # bore radius 46.8, bore spacing 123.2
    xs = [-1.5 * PB, -0.5 * PB, 0.5 * PB, 1.5 * PB]
    b1 = _box(-L / 2, L / 2, YB, YT, -H, 0)
    b1 = try_fillet(b1, '|Z', 0.54 * IN)
    b2 = b1
    for x in xs:
        b2 = b2.cut(zcyl(RB, -H - 1, 1, x, 0))
    jacket = None
    for x in xs:
        r = zring(RB + 8.5, RB + 23, -140, -15, x, 0)
        jacket = r if jacket is None else jacket.union(r)
    b3 = b2.cut(jacket)
    bolts = [(x + dx, dy) for x in xs for dx in (-42, 42) for dy in (-40, 40)]
    b3a = b3
    for c in bolts:                                      # solid bosses through the jacket, so the bolts stay dry
        b3a = b3a.union(zcyl(9, -141, -14, *c))
    b4 = b3a
    for c in bolts:
        b4 = b4.cut(zcyl(5.5, -60, 1, *c))
    b5 = b4
    for x in xs:
        for dx in (-22, 22):
            b5 = b5.cut(zcyl(5.75, -H - 1, 1, x + dx, -97)).cut(zcyl(15, -10, 1, x + dx, -97))
    b6 = b5
    for x in xs:
        for a in (90, 270):
            c = (x + (RB + 16) * math.cos(math.radians(a)), (RB + 16) * math.sin(math.radians(a)))
            b6 = b6.cut(zcyl(5, -16, 1, *c))
    b7 = b6.cut(zcyl(7, -20, 1, -L / 2 + 0.54 * IN + 4, YT - 18)).cut(zcyl(7, -20, 1, L / 2 - 0.54 * IN - 4, YT - 18))
    part = P('engine_block', 'cylinder block (deck)', 'Cast iron EN-GJL-250', 'Block', IRON, [
        F('block', EXTRUDE, ['Sketch the deck outline on the XY Plane: 546 x 239 with R13.7 (0.54 in) corners, the bore line 81 from '
                             'the top edge. Extrude 180 down.'], b1,
          note='The drawing is the deck (top face) plan only, in inches. The block depth (180) is not given; it is chosen to show '
               'the bores and water jacket.'),
        F('cylinder bores', HOLE, ['Hole 3.684 in (93.6) diameter, Through, at 4.85 in (123.2) centres: Rectangular Pattern 4.'], b2),
        F('water jacket', REVOLVE, ['Sketch a ring 111.6 to 140.6 diameter round each bore on a Work Plane 15 below the deck. Extrude, '
                                    'Cut, 125 deep (the coolant space).'], b3,
          note='The coolant surrounds each cylinder, so the heat from burning fuel goes into the water and out through the radiator.'),
        F('head bolt bosses', EXTRUDE, ['Sketch 18 diameter circles on the 16 head bolt centres (84 x 80 round each bore) on the Work Plane 15 '
                                        'below the deck. Extrude 125 down, Join.'], b3a,
          note='The head bolt holes are 58 from the bore centre, inside the water jacket. Solid bosses carry them through the '
               'coolant, so the bolts do not open into the water.'),
        F('head bolt holes', RECT, ['Hole 0.43 in (11) diameter, 60 deep, four round each bore: 16 holes ("0.42/0.43 DIA CAST 16 HOLES").'], b4),
        F('push rod holes', HOLE, ['Hole 0.453 in (11.5) diameter, Through, with a 30 counterbore 10 deep, two to each cylinder: 8 holes '
                                   '("0.448/0.458 DIA THRU 8 HOLES").'], b5),
        F('coolant holes', HOLE, ['Hole 10 diameter, 16 deep into the jacket, front and back of each bore.'], b6),
        F('dowel holes', HOLE, ['Hole 14 diameter, 20 deep, in the two top corners (the head locating dowels).'], b7),
    ])
    return single('ax_engine_block', 'Engine block deck', part,
                  'A four cylinder engine block worked from its deck plan (an inch drawing): 3.684 in bores at 4.85 in centres, 16 head '
                  'bolt holes, 8 push rod holes, coolant holes and a water jacket round the bores, 546 x 239 x 180 mm.',
                  'Dimensioning from a datum (rear face), equal spacing, hidden internal features, inch drawings.',
                  section='y', iso=(1, -1.2, 1.1),
                  note='Only the deck plan is given, so the depth (180), the water jacket and the coolant holes are typical, and the cast '
                       'water passages shown as irregular shapes on the deck are simplified to round holes. The head bolt holes fall '
                       'inside the water jacket, so solid bosses carry them through the coolant.')


# ================================================================== 20 helicopter (concept sketch, no usable sizes)
HELI = dict(ZC=1400.0, XM=2000.0, ZB=1650.0, XF=8150.0, RF=520.0, ROTOR=5200.0)


def _tube_bend(a, da, db, R, ro, ri, angle=90):
    return elbow(a, da, db, R, ro, ri, angle)


@functools.lru_cache(None)
def helicopter():
    ZC, XM, ZB, XF, RF = HELI['ZC'], HELI['XM'], HELI['ZB'], HELI['XF'], HELI['RF']
    POD = [(0, 0), ((420, 120), (650, 520)), (800, 1300), (800, 2700), ((700, 3400), (420, 4100)), (0, 4100)]
    pod = rev(POD, axis='x')
    pod = pod.translate((0, 0, ZC))
    pod_sketch = face_of(sk('XZ', [(p[1], p[0]) if not isinstance(p[0], (tuple, list)) else ((p[0][1], p[0][0]), (p[1][1], p[1][0]))
                                   for p in POD], -0.5, 0.5), 'XZ').translate((0, 0, ZC))
    glass_zone = _box(-10, 1500, -900, 900, ZC - 150, ZC + 900).union(
        sk('XZ', [(1400, ZC - 150), (1900, ZC + 900), (1400, ZC + 900)], -900, 900))
    canopy = pod.intersect(glass_zone)
    body = pod.cut(glass_zone)
    cowl0 = slot_xy(2350, 0, 3550, 0, 900, ZC + 600, ZC + 1020)
    cowl1 = try_fillet(cowl0, '>Z', 140)
    cowl2 = cowl1.union(xcyl(130, 3900, 4250, 0, ZC + 850))
    cowl3 = cowl2.cut(xcyl(100, 3950, 4260, 0, ZC + 850))
    cowl4 = cowl3.cut(pod)
    cowl = cowl4.cut(zcyl(61, ZC, ZC + 1100, XM, 0))
    BOOM = [(0, 3700), (240, 3700), (115, XF - RF + 40), (0, XF - RF + 40)]
    boom0 = rev(BOOM, axis='x').translate((0, 0, ZB))
    boom_sketch = face_of(sk('XZ', [(p[1], p[0]) for p in BOOM], -0.5, 0.5), 'XZ').translate((0, 0, ZB))
    boom1 = boom0.cut(pod)
    boom = boom1.cut(ycyl(RF, -300, 300, XF, ZB))
    duct = ycyl(RF, -120, 120, XF, ZB).cut(ycyl(400, -121, 121, XF, ZB))
    fin = sk('XZ', [(XF - 380, ZB + 360), (XF + 220, ZB + 1750), (XF + 620, ZB + 1750), (XF + 380, ZB + 360)], -45, 45)
    fin1 = duct.union(fin)
    fin2 = fin1.union(sk('XZ', [(XF - 200, ZB - 470), (XF + 250, ZB - 900), (XF + 420, ZB - 900), (XF + 330, ZB - 380)], -35, 35))
    fin_part = fin2.cut(ycyl(400, -200, 200, XF, ZB))
    ZS = ZB + 135
    stab0 = _box(7000, 7420, -800, 800, ZS - 20, ZS + 20)
    stab1 = stab0.union(_box(7000, 7420, 795, 835, ZS - 260, ZS + 260))
    stab2 = stab1.union(_box(7000, 7420, -835, -795, ZS - 260, ZS + 260))
    stab = stab2.cut(boom)
    mast0 = zcyl(60, ZC + 800, ZC + 1560, XM, 0)
    mast = mast0.union(zcyl(110, ZC + 1020, ZC + 1060, XM, 0))
    hub0 = zcyl(190, ZC + 1560, ZC + 1700, XM, 0)
    hub1 = hub0.union(_box(XM - 330, XM + 330, -110, 110, ZC + 1580, ZC + 1680))
    hub = hub1.cut(zcyl(61, ZC + 1550, ZC + 1710, XM, 0))
    blade_wp = lambda: cq.Workplane(cq.Plane(origin=(XM + 330, 0, ZC + 1630), xDir=(0, 1, 0), normal=(1, 0, 0))).ellipse(175, 22)
    blade_sketch = cq.Workplane('XY').add(blade_wp().extrude(1).faces('<X').val())
    blade0 = blade_wp().extrude(HELI['ROTOR'] - 330)
    blade = blade0.union(_box(XM + 330, XM + 700, -70, 70, ZC + 1600, ZC + 1660))
    fan0 = ycyl(110, -60, 60, XF, ZB)
    fan = fan0
    for k in range(10):
        a = 360 * k / 10
        bl = _box(100, 395, -55, 55, -14, 14).rotate((0, 0, 0), (1, 0, 0), 25).rotate((0, 0, 0), (0, 1, 0), a)
        fan = fan.union(bl.translate((XF, 0, ZB)))
        if k == 0:
            fan1 = fan
    YS, RS, rs = 950.0, 40.0, 34.0
    skid0 = tube((450, YS, RS), (1, 0, 0), 3350, RS, rs)
    skid = skid0.union(_tube_bend((450, YS, RS), (-1, 0, 0), (0, 0, 1), 300, RS, rs, 60))
    ZT = ZC - 800 - RS - 5
    xt0 = 1550.0
    ct0 = tube((xt0, -YS + 300, ZT), (0, 1, 0), 2 * (YS - 300), RS, rs)
    ct = ct0
    ct_side = []
    for sgn in (-1, 1):
        a = (xt0, sgn * (YS - 300), ZT)
        ct = ct.union(_tube_bend(a, (0, sgn, 0), (0, 0, -1), 300, RS, rs))
        ct_side.append(ct)
        ct = ct.union(tube((xt0, sgn * YS, ZT - 300), (0, 0, -1), ZT - 300 - 2 * RS, RS, rs))
        ct_side.append(ct)
    tube_sketch = cq.Workplane('XY').add(cq.Workplane(cq.Plane(origin=(xt0, -YS + 300, ZT), xDir=(1, 0, 0), normal=(0, 1, 0)))
                                         .circle(RS).circle(rs).extrude(1).faces('<Y').val())
    AL = 'Aluminium alloy 2024-T3'
    parts = [
        P('fuselage', 'fuselage', AL + ' and composite', 'Airframe', 'D9DDE2', [
            F('sketch the side profile', SKETCH,
              ['Start 2D Sketch on the XZ Plane. Draw half the fuselage outline above a horizontal centre line 1400 up: the nose arc '
               '(three point arc through 420 x 120 to 650 x 520), the 1600 diameter cabin (a line 800 above the axis from 1300 to '
               '2700) and the tail cone arc closing at 4100.', 'Finish Sketch.'], None, overlay=pod_sketch,
              note='Proportions only: the sketch has no usable sizes, so the cabin is sized for a light helicopter (1.6 m wide).'),
            F('revolve the pod', REVOLVE, ['Revolve the profile 360 degrees about the centre line.'], pod),
            F('split off the canopy', SPLIT, ['Split > Split Solid with a sketch on the XZ Plane: a line 150 below the axis from the '
                                              'nose to the pillar, then the pillar line. Keep the rear: the glazed nose is its own part '
                                              '(canopy.ipt).'], body,
              note='Splitting one revolved body keeps the canopy and the cabin exactly matched where they meet.')]),
        P('canopy', 'canopy glazing', 'Polycarbonate', 'Airframe', GLASS, [
            F('derive the pod', '3D Model tab > Create panel > Derive', ['Derive fuselage.ipt before its split (Derive Part: the solid '
                                                                         'body only).'], pod),
            F('keep the nose', SPLIT, ['Split > Split Solid with the same sketch as the fuselage. This time keep the nose.'], canopy)]),
        P('cowling', 'engine cowling', 'Composite (carbon fibre)', 'Airframe', 'B9C0C8', [
            F('sketch the cowling', SKETCH, ['Work Plane 600 above the fuselage axis. Start 2D Sketch: Center to Center Slot 1200 '
                                             'between centres, 900 wide, from 2350 back from the nose.', 'Finish Sketch.'], None,
              overlay=face_of(cowl0, 'XY')),
            F('extrude the cowling', EXTRUDE, ['Extrude the slot 420 mm up.'], cowl0),
            F('round the top', FILLET, ['Fillet: radius 140 on the top edge.'], cowl1),
            F('exhaust', EXTRUDE, ['Sketch a 260 circle on a Work Plane 100 inside the back of the cowling, 250 above its bottom. '
                                   'Extrude 350 back, so the pipe stands 250 out of the cowling.'], cowl2),
            F('exhaust bore', EXTRUDE, ['Sketch a 200 circle on the exhaust end. Extrude, Cut, 310 deep.'], cowl3),
            F('trim to the fuselage', '3D Model tab > Modify panel > Combine',
              ['Derive the fuselage pod as a body. Combine: Cut, the pod from the cowling, so its underside follows the cabin roof.'],
              cowl4),
            F('mast hole', HOLE, ['Hole on the cowling top, 2000 back from the nose: Simple Hole, diameter 122, Through All.'], cowl)]),
        P('tail_boom', 'tail boom', AL, 'Airframe', 'D9DDE2', [
            F('sketch the boom section', SKETCH, ['Start 2D Sketch on the XZ Plane, 1650 up: half the boom, 480 diameter at 3700 '
                                                  'tapering to 230 at the fin.', 'Finish Sketch.'], None, overlay=boom_sketch),
            F('revolve the boom', REVOLVE, ['Revolve the half section about the boom axis (a tapered round boom).'], boom0),
            F('trim to the fuselage', '3D Model tab > Modify panel > Combine', ['Combine: Cut, the fuselage pod from the boom.'], boom1),
            F('duct opening', EXTRUDE, ['Sketch a 1040 circle on the XZ Plane on the fan centre. Extrude, Cut, Symmetric, 600.'], boom)]),
        P('fin', 'fin and fan duct', 'Composite', 'Airframe', ORANGE, [
            F('fan duct', EXTRUDE, ['Sketch on the XZ Plane two circles on the fan centre: 1040 and 800. Extrude the ring 240, '
                                    'Symmetric.'], duct,
              note='A fan in a duct (a shrouded tail rotor) is quieter and safer on the ground than an open tail rotor.'),
            F('upper fin', EXTRUDE, ['Sketch the swept fin above the duct (a four sided outline 1390 high, raked back). Extrude 90, '
                                     'Symmetric, Join.'], fin1),
            F('lower fin', EXTRUDE, ['Sketch the small fin below the duct. Extrude 70, Symmetric, Join.'], fin2),
            F('clear the duct', EXTRUDE, ['Sketch an 800 circle on the fan centre. Extrude, Cut, Symmetric, 400, so no fin is left '
                                          'inside the duct.'], fin_part)]),
        P('stabiliser', 'horizontal stabiliser', 'Composite', 'Airframe', ORANGE, [
            F('stabiliser', EXTRUDE, ['Sketch a 420 x 1600 rectangle on a Work Plane across the top of the boom, 7000 back. Extrude '
                                      '40, Symmetric.'], stab0),
            F('end plate', EXTRUDE, ['Sketch a 420 x 520 rectangle on the right end. Extrude 40 out.'], stab1),
            F('mirror the end plate', MIRROR, ['Mirror the end plate about the XZ Plane.'], stab2),
            F('trim to the boom', '3D Model tab > Modify panel > Combine', ['Combine: Cut, the tail boom from the stabiliser.'], stab)]),
        P('mast', 'main rotor mast', 'Steel 4340', 'Rotor', STEEL, [
            F('shaft', EXTRUDE, ['Sketch a 120 circle on the XY Plane, 2000 back from the nose. Extrude 760 up from 2200 to 2960.'],
              mast0),
            F('collar', EXTRUDE, ['Sketch a 220 circle on a Work Plane 2420 up (the cowling top). Extrude 40.'], mast)]),
        P('rotor_hub', 'main rotor hub', 'Titanium Ti-6Al-4V', 'Rotor', DARK, [
            F('hub disc', EXTRUDE, ['Sketch a 380 circle on the mast top. Extrude 140.'], hub0),
            F('blade grips', EXTRUDE, ['Sketch a 660 x 220 rectangle across the hub, 20 above its base. Extrude 100.'], hub1),
            F('mast bore', HOLE, ['Hole on the hub top: Simple Hole, diameter 122, Through All.'], hub)]),
        P('blade', 'main rotor blade', 'Composite (glass fibre)', 'Rotor', 'E8E8E8', [
            F('sketch the aerofoil', SKETCH, ['Work Plane at the end of the grip, 330 from the mast. Start 2D Sketch: Ellipse 350 x 44 '
                                              '(a simple aerofoil).', 'Finish Sketch.'], None, overlay=blade_sketch),
            F('extrude the blade', EXTRUDE, ['Extrude 4870 out. Rotor diameter 2 x 5200 = 10.4 m.'], blade0),
            F('root fitting', EXTRUDE, ['Sketch a 370 x 140 rectangle on the XY Plane over the root. Extrude 60, Symmetric about the '
                                        'blade, Join.'], blade)],
          instances=[('main rotor blade 1', None), ('main rotor blade 2', R((XM, 0, 0), (0, 0, 1), 180))]),
        P('tail_fan', 'tail fan', 'Aluminium alloy', 'Rotor', DARK, [
            F('fan hub', EXTRUDE, ['Sketch a 220 circle on the XZ Plane on the fan centre. Extrude 120, Symmetric.'], fan0),
            F('first blade', EXTRUDE, ['Sketch a 295 x 110 rectangle on a Work Plane through the axis, from 100 to 395 out. Extrude 28, '
                                       'Symmetric, then Rotate it 25 degrees about its length (the pitch).'], fan1),
            F('pattern the blades', CIRC, ['Circular Pattern: the blade, 10 round the fan axis.'], fan,
              note='Uneven blade spacing is used on real fans to spread the noise; here they are even.')]),
        P('skid', 'landing skid', 'Aluminium tube 6061-T6, 80 x 6', 'Landing gear', 'A7ADB5', [
            F('skid tube', SWEEP, ['Sketch an 80 and a 68 circle on the YZ Plane at the back of the skid. Sweep 3350 forward along a '
                                   'straight path.'], skid0),
            F('front bend', SWEEP, ['Sweep the same profile round a 300 radius bend turned up 60 degrees at the front.'], skid)],
          instances=[('skid right', None), ('skid left', T(0, -2 * YS, 0))]),
        P('cross_tube', 'cross tube', 'Aluminium tube 6061-T6, 80 x 6', 'Landing gear', 'A7ADB5', [
            F('sketch the tube', SKETCH, ['Start 2D Sketch on a Work Plane across the tube end: an 80 circle and a 68 circle.',
                                          'Finish Sketch.'], None, overlay=tube_sketch),
            F('top tube', SWEEP, ['Sweep the tube 1300 across under the cabin.'], ct0),
            F('left bend', SWEEP, ['Sweep the end round a 300 radius bend, turning down.'], ct_side[0]),
            F('left leg', SWEEP, ['Sweep straight down to the skid.'], ct_side[1]),
            F('mirror to the right', MIRROR, ['Mirror the bend and the leg about the XZ Plane. The legs are 1900 apart.'], ct)],
          instances=[('cross tube front', None), ('cross tube rear', T(1150, 0, 0))]),
    ]
    assembly = [
        ('place the fuselage', PLACE, ['Place fuselage.ipt, right click, Place Grounded at Origin.'], ['fuselage']),
        ('canopy', CONSTRAIN, ['Place canopy.ipt. Mate its split face to the split face of the fuselage (Flush) and Mate the two '
                               'XZ Planes, so the glazing fills the nose.'], ['canopy glazing']),
        ('engine cowling', CONSTRAIN, ['Place cowling.ipt. Mate its underside to the cabin roof and Mate its mast hole axis to a Work '
                                       'Axis 2000 back from the nose.'], ['engine cowling']),
        ('tail boom', CONSTRAIN, ['Place tail_boom.ipt. Mate its axis to a Work Axis 1650 up (Flush the front to the tail cone).'],
         ['tail boom']),
        ('fin and fan duct', CONSTRAIN, ['Place fin.ipt. Insert the duct on the boom opening (axis to axis, mid planes Flush).'],
         ['fin and fan duct']),
        ('horizontal stabiliser', CONSTRAIN, ['Place stabiliser.ipt. Mate its underside to the top of the boom, 7000 back, and its '
                                              'middle to the XZ Plane.'], ['horizontal stabiliser']),
        ('landing gear sub-assembly: cross tubes', PLACE,
         ['File > New > Standard (mm).iam and save it as landing_gear.iam (a sub-assembly).',
          'Place cross_tube.ipt Grounded, then a second copy: Mate the two XZ Planes and Offset the YZ Planes 1150 apart.'],
         ['cross tube front', 'cross tube rear'],
         'A sub-assembly is built and checked on its own, then placed in the main assembly as one component.'),
        ('landing gear sub-assembly: skids', CONSTRAIN,
         ['Place skid.ipt twice. Insert the foot of each leg on the top of a skid (Mate the leg axis to a point on the skid). Save '
          'landing_gear.iam.', 'In ax_helicopter.iam, Place landing_gear.iam: Mate the top of the cross tubes to the belly.'],
         ['skid right', 'skid left']),
        ('rotor head sub-assembly: mast', PLACE,
         ['File > New > Standard (mm).iam and save it as rotor_head.iam.', 'Place mast.ipt Grounded.'], ['main rotor mast']),
        ('rotor head sub-assembly: hub', CONSTRAIN, ['Place rotor_hub.ipt. Insert the hub bore on the top of the mast.'],
         ['main rotor hub']),
        ('rotor head sub-assembly: blades', CONSTRAIN,
         ['Place blade.ipt twice. Mate each root fitting into a grip and Angle the two blades 180 degrees apart. Save rotor_head.iam.',
          'In ax_helicopter.iam, Place rotor_head.iam: Insert the mast collar on the cowling top.'],
         ['main rotor blade 1', 'main rotor blade 2']),
        ('tail fan', CONSTRAIN, ['Place tail_fan.ipt. Mate its axis to the duct axis and Flush its mid plane with the XZ Plane.'],
         ['tail fan']),
    ]
    ex = {'canopy glazing': (-900, 0, 0), 'engine cowling': (0, 0, 700), 'tail boom': (500, 0, 0), 'fin and fan duct': (1200, 0, 0),
          'horizontal stabiliser': (800, 0, -500), 'main rotor mast': (0, 0, 1200), 'main rotor hub': (0, 0, 1700),
          'main rotor blade 1': (0, 0, 2100), 'main rotor blade 2': (0, 0, 2100), 'tail fan': (1200, 900, 0),
          'skid right': (0, 900, -700), 'skid left': (0, -900, -700), 'cross tube front': (0, 0, -400), 'cross tube rear': (0, 0, -400)}
    return dict(name='ax_helicopter', title='Light helicopter (concept)', parts=parts, assembly=assembly, explode=ex,
                description='A light helicopter modelled from a concept sketch: a revolved cabin pod with a glazed nose, engine cowling, '
                            'tapering tail boom, fin with a ducted tail fan, stabiliser, a two blade 10.4 m main rotor and tubular skids. '
                            '15 parts.',
                uses='Concept sketches to 3D, revolves, lofts and sweeps, top level assemblies, proportion.',
                criteria='3.1, 3.2', section=None, iso=(1, -1.6, 0.7), material='See parts list', mesh_scale=20,
                note='The sketch has no usable sizes (its numbers do not match each other), so the model is to proportion only, at '
                     'a light helicopter scale: cabin 1.6 m, overall 8.8 m, rotor 10.4 m. The cabin is a revolved pod; doors, windows and '
                     'details are left off.')


# ------------------------------------------------------------------ the catalogue entries (built lazily)
BUILDERS = [fork_bracket, pedestal_bearing, slotted_boss_flange, corner_boss_bracket, saddle_block, clamp_lever, roller_assembly,
            valve_body, machinists_jack, planetary_gears, tube_bracket_45, angle_bracket, crankshaft_4, crankshaft_3, v_pulley,
            pipe_run_valves, steam_line_loop, oil_pan, engine_block, helicopter]
# what the catalogue needs without building the model (building every model on import would be slow)
META = {
    'ax_fork_bracket': dict(title='Fork bracket (exercise T8)', fn=fork_bracket, source='turkish'),
    'ax_pedestal_bearing': dict(title='Pedestal bearing (exercise T8)', fn=pedestal_bearing, source='turkish'),
    'ax_slotted_boss_flange': dict(title='Slotted boss flange (exercise T9)', fn=slotted_boss_flange, source='turkish'),
    'ax_corner_boss_bracket': dict(title='Boss bracket (exercise T9)', fn=corner_boss_bracket, source='turkish'),
    'ax_saddle_block': dict(title='Saddle bearing block (exercise T10)', fn=saddle_block, source='turkish'),
    'ax_clamp_lever': dict(title='Split clamp lever (exercise T10)', fn=clamp_lever, source='turkish'),
    'ax_roller_assembly': dict(title='Roller assembly', fn=roller_assembly, source='roller'),
    'ax_valve_body': dict(title='Valve body', fn=valve_body, source='valve_body'),
    'ax_machinists_jack': dict(title="Machinist's jack", fn=machinists_jack, source='jack'),
    'ax_planetary_gears': dict(title='Planetary gear set', fn=planetary_gears, source='planetary'),
    'ax_tube_bracket_45': dict(title='Tube bracket, 45 degree', fn=tube_bracket_45, source='bracket_45'),
    'ax_angle_bracket': dict(title='Angle bracket (inch drawing)', fn=angle_bracket, source='angle_bracket'),
    'ax_crankshaft_4': dict(title='Crankshaft, four cylinder', fn=crankshaft_4, source='crankshaft_4'),
    'ax_crankshaft_3': dict(title='Crankshaft, three throw', fn=crankshaft_3, source='crankshaft_3'),
    'ax_v_pulley': dict(title='V-belt pulley (inch drawing)', fn=v_pulley, source='v_pulley'),
    'ax_pipe_run_valves': dict(title='Pipe run with three gate valves', fn=pipe_run_valves, source='pipe_run'),
    'ax_steam_line_loop': dict(title='Steam line loop (piping isometric)', fn=steam_line_loop, source='steam_line'),
    'ax_oil_pan': dict(title='Engine oil pan', fn=oil_pan, source='oil_pan'),
    'ax_engine_block': dict(title='Engine block deck', fn=engine_block, source='engine_block'),
    'ax_helicopter': dict(title='Light helicopter (concept)', fn=helicopter, source='helicopter'),
}


def _items_fn(b):
    def fn():
        return model_items(b())
    return fn


class _Lazy(dict):
    """A MODELS entry whose explode positions, description and so on come from the builder when first asked for."""
    LAZY = ('description', 'criteria', 'uses', 'section', 'explode', 'iso', 'material', 'note', 'mesh_scale')

    def __init__(self, name, b):
        super().__init__(name=name, title=META[name]['title'], folder=FOLDER, fn=_items_fn(b), source=META[name]['source'])
        self._b = b

    def _fill(self, k):
        if k in self.LAZY and not dict.__contains__(self, k):
            m = self._b()
            for kk in self.LAZY:
                dict.__setitem__(self, kk, m.get(kk))
            if m['assembly']:
                dict.__setitem__(self, 'bom', lambda: model_bom(self._b()))
                dict.__setitem__(self, 'sim', self['name'] in SIM_MODELS)

    def __getitem__(self, k):
        self._fill(k if k not in ('bom', 'sim') else 'description')
        return dict.__getitem__(self, k)

    def get(self, k, d=None):
        self._fill(k if k not in ('bom', 'sim') else 'description')
        return dict.get(self, k, d)

    def __contains__(self, k):
        self._fill(k if k not in ('bom', 'sim') else 'description')
        return dict.__contains__(self, k)


SIM_MODELS = ('ax_roller_assembly', 'ax_machinists_jack', 'ax_planetary_gears', 'ax_pipe_run_valves', 'ax_helicopter')
MODELS = [_Lazy(n, v['fn']) for n, v in META.items()]
STEPS = {n: (lambda b=v['fn']: ex_steps(b())) for n, v in META.items()}
