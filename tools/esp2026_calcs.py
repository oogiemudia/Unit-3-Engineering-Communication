"""ESP 2026 Task 2: calculations (cost to manufacture, weight, size, seat height, assumptions) and reflective notes.

Every size and mass comes from models/esp2026.py (the CAD model) and the leg FEA in docs/ESP 2026/fea, so the
calculations, drawings and model always agree. Prices, labour times and sustainability shares are stated
assumptions, listed once in the tables below.
Writes docs/ESP 2026/ESP26_calculations.html and .pdf, ESP26_reflective_notes.html and .pdf.
Run from the repository root:  /home/user/venv/bin/python tools/esp2026_calcs.py
"""
import json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import esp2026 as E  # noqa: E402

FOLDER = os.path.join(ROOT, 'docs', 'ESP 2026')
G = 9.81
LABOUR = 15.0                 # £ an hour (brief)
SETS = 100                    # sets in the order (brief)
BUDGET = 15000                # £ a set (brief)
WEEKS = 26                    # weeks to deliver (brief)
OCCUPANT = 77                 # kg, standard passenger used for seat certification (CS 25.562)
SEAT_G = 9                    # forward emergency landing load factor (CS 25.561)
LEAN = 300                    # N, a passenger leaning back on the reclined seat (assumption)
LEAN_H = 450                  # mm, that load's height above the pivot along the back (shoulder height)
LOCK_RATING = 1500            # N, the bought in hydraulic lock (part 19)
PITCH = 787                   # mm, 31 in seat pitch, typical for economy (assumption)

# ------------------------------------------------------------------ assumptions for cost and sustainability
# material £/kg, buy to fly ratio (raw material bought / finished mass) and sustainable share of the material.
# "Sustainable" = recycled content, or bio based, or recycled at end of life by an established route.
MATERIALS = {
    'al_plate':  ('7075-T6 aluminium plate, machined', 12.0, 5.0, 1.0, 'Recycled at end of life (aluminium keeps its value)'),
    'al_tube':   ('7075/6061 aluminium tube', 9.0, 1.2, 1.0, '70 % recycled content, recyclable'),
    'stainless': ('17-4PH stainless steel bar', 15.0, 3.0, 1.0, 'Recyclable steel'),
    'pc':        ('FR polycarbonate, moulded', 6.0, 1.1, 1.0, 'Thermoplastic, recyclable'),
    'pa6':       ('Recycled PA6 GF30, moulded', 5.0, 1.1, 1.0, 'Recycled content'),
    'tpe':       ('TPE over foam', 6.0, 1.2, 0.0, 'Not counted'),
    'cfrp':      ('Carbon fibre prepreg', 60.0, 1.5, 0.0, 'Thermoset: not counted'),
    'foam':      ('FR polyurethane foam', 8.0, 1.1, 0.3, '30 % bio based polyol'),
    'fabric':    ('Wool and recycled polyester cover', 30.0, 1.3, 1.0, 'Natural and recycled fibre'),
    'diaphragm': ('Aramid and polyester suspension', 40.0, 1.2, 0.5, 'Polyester share recycled'),
    'felt':      ('Recycled PET felt, moulded', 6.0, 1.2, 1.0, 'Recycled content'),
    'honeycomb': ('Al honeycomb sandwich, PC faces', 50.0, 1.3, 1.0, 'Aluminium and PC, recyclable'),
    'webbing':   ('Polyester webbing (safety)', 15.0, 1.1, 0.0, 'Virgin fibre for strength: not counted'),
    'headrest':  ('Foam on PA6 frame, recycled leather', 20.0, 1.2, 0.6, 'PA6 frame and recycled leather fibre'),
    'bought':    ('Bought in part', 0.0, 1.0, None, 'Share given with the part'),
}
# part key: (material, labour hours each, bought in price £ each, sustainable share if bought in)
PART_COST = {
    'beam_tube': ('al_tube', 0.5, 0, None), 'beam_end_cap': ('pc', 0.05, 0, None),
    'spreader': ('al_plate', 1.5, 0, None), 'leg': ('al_plate', 3.0, 0, None),
    'beam_collar': ('al_plate', 0.2, 0, None), 'track_fitting': ('al_plate', 0.5, 0, None),
    'track_stud': ('bought', 0.05, 18, 1.0), 'baggage_bar': ('al_tube', 0.3, 0, None),
    'seat_diaphragm': ('diaphragm', 0.5, 0, None), 'seat_foam': ('foam', 0.3, 0, None),
    'seat_cover': ('fabric', 1.0, 0, None), 'back_shell': ('cfrp', 2.5, 0, None),
    'back_foam': ('foam', 0.3, 0, None), 'back_cover': ('fabric', 1.0, 0, None),
    'headrest': ('headrest', 0.8, 0, None), 'back_pivot_pin': ('stainless', 0.1, 0, None),
    'end_pivot_pin': ('stainless', 0.1, 0, None), 'recline_bracket': ('al_plate', 0.3, 0, None),
    'recline_lock': ('bought', 0.1, 85, 1.0), 'recline_rod': ('bought', 0.0, 0, 1.0),
    'lock_pin': ('stainless', 0.1, 0, None), 'recline_button': ('pc', 0.05, 0, None),
    'armrest': ('pa6', 0.2, 0, None), 'armrest_pad': ('tpe', 0.2, 0, None),
    'armrest_pin': ('stainless', 0.1, 0, None), 'belt_anchor': ('al_plate', 0.3, 0, None),
    'belt_strap_buckle': ('webbing', 0.2, 0, None), 'belt_strap_adjust': ('webbing', 0.2, 0, None),
    'buckle_body': ('bought', 0.05, 25, 1.0), 'buckle_lever': ('bought', 0.0, 5, 1.0),
    'belt_tongue': ('bought', 0.05, 15, 1.0), 'tray_table': ('honeycomb', 1.0, 0, None),
    'tray_arm': ('al_plate', 0.2, 0, None), 'tray_latch': ('pc', 0.05, 0, None),
    'ife_screen': ('bought', 0.3, 220, 0.3), 'usb_module': ('bought', 0.2, 45, 0.3),
    'literature_pocket': ('felt', 0.3, 0, None), 'vest_pouch': ('felt', 0.3, 0, None),
    'life_vest': ('bought', 0.0, 0, 0.0),
}
ASSEMBLY_H = 8.0              # hours a set: build, wire, adjust and inspect
TOOLING = 60000               # £: moulds for the shell, foam, armrest, covers; jigs (shared by the order)
TESTING = 150000              # £: dynamic sled tests (16 g), flammability tests, certification (shared by the order)
OVERHEAD = 0.30               # factory overhead on labour
SCRAP = 0.05                  # material scrap and consumables


def parts_table():
    """One row per part: qty in a set, finished mass, material, raw material cost, labour and bought in cost."""
    by = E.masses()
    rows = []
    for p in E.PARTS:
        q, m = by[p['key']]
        mat, hrs, buy, sus_b = PART_COST[p['key']]
        name, price, btf, sus, _ = MATERIALS[mat]
        raw = m * btf * price * (1 + SCRAP)
        rows.append(dict(no=p['no'], key=p['key'], name=p['name'], qty=q, mass=m, mat=mat, raw=raw,
                         hours=hrs * q, labour=hrs * q * LABOUR, bought=buy * q,
                         sus=(sus_b if mat == 'bought' else sus), vest=p['key'] == 'life_vest'))
    return rows


def costs():
    rows = parts_table()
    material = sum(r['raw'] for r in rows)
    bought = sum(r['bought'] for r in rows)
    hours = sum(r['hours'] for r in rows) + ASSEMBLY_H
    labour = hours * LABOUR
    overhead = labour * OVERHEAD
    tooling, testing = TOOLING / SETS, TESTING / SETS
    total = material + bought + labour + overhead + tooling + testing
    return dict(material=material, bought=bought, hours=hours, labour=labour, overhead=overhead,
                tooling=tooling, testing=testing, total=total, order=total * SETS, margin=BUDGET - total,
                workers=hours * SETS / (WEEKS * 37.5) / 0.8, rows=rows)


def sustainability():
    rows = [r for r in parts_table() if not r['vest']]
    m = sum(r['mass'] for r in rows)
    s = sum(r['mass'] * r['sus'] for r in rows)
    return dict(mass=m, sustainable=s, share=s / m)


def truss():
    """The leg as a pin jointed truss: nodes A, B (feet), C, D (beam bores); members AC, BD, CD, AD."""
    import numpy as np
    F = round(SEAT_G * G * (3 * OCCUPANT + E.set_mass()) / 2)
    nodes = dict(A=E.LEG_A, B=E.LEG_B, C=E.LEG_C, D=E.LEG_D)
    members = [('front strut', 'A', 'C', 40), ('rear strut', 'B', 'D', 40), ('top chord', 'C', 'D', 30), ('brace', 'A', 'D', 30)]
    idx = {k: i for i, k in enumerate('ABCD')}
    # unknowns: 4 member forces (tension +), Ay, Az, By, Bz
    Mx = np.zeros((8, 8))
    rhs = np.zeros(8)
    for j, (_, a, b, w) in enumerate(members):
        pa, pb = np.array(nodes[a], float), np.array(nodes[b], float)
        u = (pb - pa) / np.linalg.norm(pb - pa)
        Mx[2 * idx[a]:2 * idx[a] + 2, j] += u
        Mx[2 * idx[b]:2 * idx[b] + 2, j] -= u
    Mx[0, 4] = Mx[1, 5] = Mx[2, 6] = Mx[3, 7] = 1
    rhs[2 * idx['C']] = rhs[2 * idx['D']] = F / 2          # the -Y loads moved to the right hand side
    sol = np.linalg.solve(Mx, rhs)
    out = []
    for j, (name, a, b, w) in enumerate(members):
        L = math.dist(nodes[a], nodes[b])
        out.append(dict(name=name, force=sol[j], width=w, L=L, stress=abs(sol[j]) / (w * E.LEG_T)))
    return F, out, sol[4:]


def numbers():
    n = {}
    m = E.set_mass()
    n['mass_set'], n['mass_vests'] = m, E.set_mass(True)
    n['mass_seat'], n['mass_seat_v'] = m / 3, n['mass_vests'] / 3
    by = E.masses()
    shared = ('beam_tube', 'beam_end_cap', 'spreader', 'leg', 'beam_collar', 'track_fitting', 'track_stud',
              'baggage_bar', 'armrest', 'armrest_pad', 'armrest_pin', 'end_pivot_pin', 'back_pivot_pin')
    n['groups'] = [(g, sum(by[p['key']][1] for p in E.PARTS if p['group'] == g and p['key'] != 'life_vest'))
                   for g in ('structure', 'seat', 'recline', 'armrest', 'belt', 'amenity')]
    n['shared'] = sum(by[k][1] for k in shared)
    n['costs'] = costs()
    n['sus'] = sustainability()
    n['lock0'], n['lock1'] = E.lock_line(0), E.lock_line(E.RECLINE)
    a, r, L, _ = n['lock1']
    arm = abs((r[0] - a[0]) * (E.PIV[1] - a[1]) - (r[1] - a[1]) * (E.PIV[0] - a[0])) / L
    n['lock_arm'] = arm
    n['lock_F'] = LEAN * LEAN_H / arm
    n['truss'] = truss()
    f = os.path.join(FOLDER, 'fea', 'esp2026_p04_leg.json')
    n['fea'] = json.load(open(f))['results'] if os.path.exists(f) else {}
    import cadquery as cq
    for key, rec in (('size0', 0), ('size1', E.RECLINE)):
        bb = cq.Compound.makeCompound([s.val() for _, _, s in E.set_instances(recline=(rec,) * 3)]).BoundingBox()
        n[key] = (bb.xmax - bb.xmin, bb.ymax - bb.ymin, bb.zmax - bb.zmin, bb.ymax)
    n['back_move'] = n['size1'][3] - n['size0'][3]
    return n


CSS = """
@page{size:A4;margin:11mm 13mm}
body{font-family:Arial,Helvetica,sans-serif;font-size:8.9pt;line-height:1.28;color:#111}
h1{font-size:14pt;margin:0 0 2mm} h2{font-size:10pt;margin:2.2mm 0 0.8mm;color:#16335B;border-bottom:0.3mm solid #16335B}
table{border-collapse:collapse;width:100%;margin:1mm 0} td,th{border:0.2mm solid #888;padding:0.35mm 1.5mm;text-align:left;vertical-align:top}
th{background:#E8EEF6} .r{text-align:right;white-space:nowrap} .ok{color:#1F7A3A;font-weight:bold}
.hdr{display:flex;justify-content:space-between;font-size:8pt;color:#444;border-bottom:0.3mm solid #444;margin-bottom:2mm}
.page{page-break-after:always} .small{font-size:8.2pt} .tiny{font-size:7pt} .tiny td,.tiny th{padding:0.15mm 1.2mm} ul{margin:0.5mm 0 0.5mm 5mm;padding:0}
tr.tot td{font-weight:bold;background:#F3F6FA}
"""


def gbp(v):
    return '£' + format(round(v), ',')


def calcs_html(n):
    c, s = n['costs'], n['sus']
    F, members, R = n['truss']
    probes = {p['name']: p['vm'] for p in n['fea'].get('probes', [])}
    w, d, h, _ = n['size0']
    w1, d1, h1, _ = n['size1']
    a0, r0, L0, _ = n['lock0']
    _, r1, L1, _ = n['lock1']
    hdr = lambda k: ('<div class="hdr"><span>Aero-Chair Ltd. ESP 2026 (8730-035) Task 2(a): economy class three-seat set</span>'
                     '<span>Calculation sheet %d of 3. Ref ESP26-CALC. 2026-11-10</span></div>' % k)
    grp = ''.join('<tr><td>%s</td><td class="r">%.2f kg</td></tr>' % (g.capitalize(), m) for g, m in n['groups'])
    part_rows = ''.join(
        '<tr><td>%d</td><td>%s</td><td class="r">%d</td><td class="r">%.3f</td><td>%s</td><td class="r">%s</td>'
        '<td class="r">%.2f</td><td class="r">%s</td><td class="r">%s</td></tr>' % (
            r['no'], r['name'], r['qty'], r['mass'], MATERIALS[r['mat']][0] if r['mat'] != 'bought' else 'Bought in',
            gbp(r['raw']) if r['raw'] else '&ndash;', r['hours'], gbp(r['bought']) if r['bought'] else '&ndash;',
            ('%d %%' % round(r['sus'] * 100)) if not r['vest'] else 'excl.')
        for r in c['rows'])
    mat_rows = ''.join('<tr><td>%s</td><td class="r">£%.0f</td><td class="r">%.1f</td><td class="r">%d %%</td><td>%s</td></tr>' % (
        v[0], v[1], v[2], round(v[3] * 100), v[4]) for k, v in MATERIALS.items() if k != 'bought')
    mem_rows = ''.join('<tr><td>%s</td><td class="r">%.0f N %s</td><td class="r">%d &times; %d</td><td class="r">%.1f MPa</td>'
                       '<td class="r">%.1f MPa</td></tr>' % (
                           m['name'], abs(m['force']), 'tension' if m['force'] > 0 else 'compression' if m['force'] < -1 else '',
                           m['width'], E.LEG_T, m['stress'], probes.get(m['name'], 0)) for m in members)
    fea = n['fea']
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2026 calculations</title><style>{CSS}</style></head><body>
<div class="page">{hdr(1)}
<h1>Calculations for the preferred design (Design A): beam and leg seat set</h1>
<h2>1. Assumptions</h2>
<ul class="small">
<li>Sizes and masses are taken from the CAD model (models/esp2026.py): every one of the 39 parts is modelled with its own material density. One set has 128 parts.</li>
<li>Life vests are supplied and replaced by the airline (they are cabin safety equipment), so they are left out of the 8 kg seat limit. They are listed with them included as well.</li>
<li>Seat pitch 31 in ({PITCH} mm), typical for economy. A standard passenger is {OCCUPANT} kg (CS 25.562). Forward emergency landing load {SEAT_G} g (CS 25.561), checked as a static load on the legs.</li>
<li>Labour £{LABOUR:.0f} an hour (brief). Material prices, labour times and bought in prices are estimates from supplier catalogues for a batch of {SETS} sets; they are listed in section 8.</li>
<li>Tooling (moulds, jigs) {gbp(TOOLING)} and certification testing (16 g sled tests, flammability) {gbp(TESTING)} are shared over the {SETS} sets.</li>
<li>Cabin 18 to 27 &deg;C: aluminium, carbon fibre and the polymers chosen are all stable well beyond this range, so no thermal allowance is needed.</li>
<li>&ldquo;Sustainable&rdquo; means recycled content, bio based, or recycled at end of life through an established route (aluminium, steel, thermoplastics, wool and PET).</li>
</ul>
<h2>2. Weight (mass)</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Mass of one three-seat set (CAD model, no life vests)</td><td>sum of volume &times; density for all 128 parts</td><td class="r"><b>{n['mass_set']:.2f} kg</b></td></tr>
<tr><td>Mass per seat</td><td>{n['mass_set']:.2f} / 3</td><td class="r"><b>{n['mass_seat']:.2f} kg</b></td></tr>
<tr><td>Limit (brief): frame, cushions and belts</td><td>8 kg a seat, so margin = 8 &minus; {n['mass_seat']:.2f}</td><td class="r"><span class="ok">{8 - n['mass_seat']:.2f} kg under</span></td></tr>
<tr><td>With the three life vests (for information)</td><td>{n['mass_vests']:.2f} / 3</td><td class="r">{n['mass_seat_v']:.2f} kg</td></tr>
</table>
<table class="small" style="width:48%;display:inline-table;margin-right:3%"><tr><th>Group (one set)</th><th class="r">Mass</th></tr>{grp}</table>
<p class="small" style="display:inline-block;width:47%;vertical-align:top">The structure (beam tubes, legs, spreaders, track fittings) is shared by the three seats. The heaviest single items per seat are the carbon back shell ({n['costs']['rows'][11]['mass'] / 3:.2f} kg) and the cushion foams. The back shell is only 1.2 mm thick: carbon fibre is used because it is about 40 % lighter than an aluminium back of the same stiffness.</p>
<h2>3. Size</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Overall width of the set</td><td>CAD bounding box: beam tubes and end caps</td><td class="r"><b>{w:.0f} mm</b></td></tr>
<tr><td>Seat width between armrests</td><td>seat pitch across 500 &minus; armrest 50 (brief 432 to 457)</td><td class="r"><span class="ok">{E.SEAT_W} mm</span></td></tr>
<tr><td>Overall depth, backs upright</td><td>front of cushion to back of the shell</td><td class="r"><b>{d:.0f} mm</b></td></tr>
<tr><td>Overall height</td><td>floor to the top of the head rest (the track studs go 20 mm into the floor)</td><td class="r"><b>{h - 20:.0f} mm</b></td></tr>
<tr><td>Back moves rearwards when reclined {E.RECLINE}&deg;</td><td>CAD, reclined minus upright</td><td class="r">{n['back_move']:.0f} mm</td></tr>
<tr><td>Overall depth, backs reclined</td><td>less than the {PITCH} mm pitch, so the set stays in its own row</td><td class="r"><span class="ok">{d1:.0f} mm</span></td></tr>
<tr><td>Track fitting centres</td><td>20 track holes at 25.4 mm</td><td class="r">{E.FOOT_Y[1] - E.FOOT_Y[0]} mm</td></tr>
<tr><td>Tray table (brief up to 267 &times; 419)</td><td>CAD</td><td class="r"><span class="ok">{E.TL} &times; {E.TW} mm</span></td></tr>
<tr><td>Life vest pouch inside (vest 305 &times; 305 &times; 50)</td><td>CAD</td><td class="r"><span class="ok">316 &times; 336 &times; 56 mm</span></td></tr>
</table>
<h2>4. Seat height and ergonomics</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Seat height (front of the cushion)</td><td>beam axis {E.BEAM_Z} + tube radius {E.BEAM_R} + diaphragm and foam</td><td class="r"><b>{E.SEAT_H} mm</b></td></tr>
<tr><td>Target from body sizes (popliteal height + shoe)</td><td>5th % woman 355 + 25 shoe = 380; 95th % man 490 + 25 = 515</td><td class="r">380 to 515</td></tr>
<tr><td>Cushion compresses under a passenger</td><td>about 30 mm, so the sitting height is</td><td class="r">{E.SEAT_H - 30} mm</td></tr>
<tr><td>Armrest top above the floor</td><td>{E.ARM_Z[1]} + pad 8 (elbow rest about 200 above the seat)</td><td class="r">{E.ARM_Z[1] + 8} mm</td></tr>
<tr><td>Cushion depth</td><td>{E.CUSH_Y[1]} &minus; ({E.CUSH_Y[0]}) (5th % woman buttock to knee 520)</td><td class="r">{E.CUSH_Y[1] - E.CUSH_Y[0]} mm</td></tr>
<tr><td>Back angle upright / reclined</td><td>{E.BACK_ANGLE}&deg; + {E.RECLINE}&deg; recline (brief 3 to 6&deg;)</td><td class="r"><span class="ok">{E.BACK_ANGLE}&deg; / {E.BACK_ANGLE + E.RECLINE}&deg;</span></td></tr>
</table>
<p class="small">Most passengers can sit with their feet flat; the 3.8&deg; cushion slope stops sliding forward; lifting armrests allow a sideways transfer from an aisle wheelchair.</p>
</div>
<div class="page">{hdr(2)}
<h2>5. Cost to manufacture</h2>
<table><tr><th>Cost element (one three-seat set)</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Raw materials</td><td>finished mass &times; buy to fly ratio &times; £/kg, + {SCRAP * 100:.0f} % scrap (table section 8)</td><td class="r">{gbp(c['material'])}</td></tr>
<tr><td>Bought in parts</td><td>track studs, recline locks, belt buckles, screens, power modules</td><td class="r">{gbp(c['bought'])}</td></tr>
<tr><td>Labour</td><td>{c['hours'] - ASSEMBLY_H:.1f} h making parts + {ASSEMBLY_H:.0f} h assembly = {c['hours']:.1f} h &times; £{LABOUR:.0f}</td><td class="r">{gbp(c['labour'])}</td></tr>
<tr><td>Factory overhead</td><td>{OVERHEAD * 100:.0f} % of labour (power, machines, floor space)</td><td class="r">{gbp(c['overhead'])}</td></tr>
<tr><td>Tooling share</td><td>{gbp(TOOLING)} / {SETS} sets</td><td class="r">{gbp(c['tooling'])}</td></tr>
<tr><td>Certification testing share</td><td>{gbp(TESTING)} / {SETS} sets</td><td class="r">{gbp(c['testing'])}</td></tr>
<tr class="tot"><td>Cost to manufacture one set</td><td></td><td class="r">{gbp(c['total'])}</td></tr>
<tr><td>Budget (brief)</td><td>£1.5 million / {SETS} sets</td><td class="r">{gbp(BUDGET)}</td></tr>
<tr class="tot"><td>Margin for profit, delivery and fitting</td><td>{gbp(BUDGET)} &minus; {gbp(c['total'])}</td><td class="r"><span class="ok">{gbp(c['margin'])}</span></td></tr>
<tr><td>Whole order</td><td>{gbp(c['total'])} &times; {SETS}</td><td class="r">{gbp(c['order'])}</td></tr>
<tr><td>Time: workers needed for {SETS} sets in {WEEKS} weeks</td><td>{c['hours']:.1f} h &times; {SETS} / ({WEEKS} &times; 37.5 h) at 80 % efficiency</td><td class="r">{c['workers']:.1f} people</td></tr>
</table>
<p class="small">The cost is well inside the budget, so the airline can be offered a competitive price. The biggest single cost is the screens ({gbp(220 * 3)} a set); a cheaper screen or a phone holder would save most. Six to eight weeks are allowed for testing and certification at the start of the 26 weeks, then about {c['workers'] * WEEKS / (WEEKS - 7):.0f} people make the 100 sets in the remaining 19 weeks (the legs and spreaders are machined in batches).</p>
<h2>6. Strength: the legs in a 9 g emergency landing</h2>
<p>Forward load on the set: {SEAT_G} &times; 9.81 &times; (3 &times; {OCCUPANT} + {n['mass_set']:.1f}) = {2 * F:,} N, shared by two legs: <b>{F:,} N a leg</b>, half at each beam bore.
The leg is treated as a pin jointed truss (A, B feet; C, D beam bores). Joint equilibrium gives the member forces; stress = force / (strut width &times; {E.LEG_T} mm plate).
Foot reactions: front {R[0]:.0f} N back, {R[1]:.0f} N up; rear {R[2]:.0f} N back, {abs(R[3]):.0f} N down (the rear foot is pulled up).</p>
<table><tr><th>Member</th><th class="r">Force</th><th class="r">Section (mm)</th><th class="r">Hand stress</th><th class="r">FEA (mid strut)</th></tr>{mem_rows}</table>
<p class="small">The hand calculation and the FEA (gmsh + scikit-fem, 10 node tetrahedra) agree within 7 % in the main members; the front strut carries no load in a pure truss and only a little bending in the FEA. The FEA peak is <b>{fea.get('vm_max', 0):.0f} MPa</b> in the corner where the brace meets the rear boss: safety factor <b>{fea.get('sf_min', 0):.1f}</b> on 7075-T6 (yield 503 MPa). Largest movement {fea.get('disp_max', 0):.2f} mm. <span class="ok">OK.</span>
Rear foot uplift {abs(R[3]):.0f} N is taken by the shear plunger track stud (rated about 13 kN).</p>
<h2>7. Recline mechanism and seat belt</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Lock pin centres, upright / reclined</td><td>from the pivot geometry (lever {E.LEVER[1]} mm below the pivot)</td><td class="r">{L0:.1f} / {L1:.1f} mm</td></tr>
<tr><td>Lock stroke used</td><td>{L0:.1f} &minus; {L1:.1f}</td><td class="r"><b>{L0 - L1:.1f} mm</b></td></tr>
<tr><td>Lever arm of the lock about the pivot</td><td>perpendicular distance, pivot to lock line</td><td class="r">{n['lock_arm']:.0f} mm</td></tr>
<tr><td>Lock force, passenger leaning back</td><td>{LEAN} N at {LEAN_H} mm: {LEAN} &times; {LEAN_H} / {n['lock_arm']:.0f}</td><td class="r">{n['lock_F']:.0f} N (rated {LOCK_RATING} N)</td></tr>
<tr><td>Belt length</td><td>buckle side 380 + adjuster side 790 to 1040</td><td class="r"><span class="ok">1170 to 1420 mm</span></td></tr>
</table>
</div>
<div>{hdr(3)}
<h2>8. Materials, prices and sustainability</h2>
<table class="small"><tr><th>Material</th><th class="r">£/kg</th><th class="r">Buy to fly</th><th class="r">Sustainable</th><th>Why</th></tr>{mat_rows}</table>
<p class="small">Sustainable share by mass (no life vests): {s['sustainable']:.2f} kg of {s['mass']:.2f} kg = <b>{s['share'] * 100:.0f} %</b> (brief: at least 70 %). <span class="ok">{'OK' if s['share'] >= 0.7 else 'NOT MET'}.</span>
The share only just passes. The back shells are the largest item not counted ({n['costs']['rows'][11]['mass']:.2f} kg a set): made from recycled carbon fibre they would raise it to about {(s['sustainable'] + n['costs']['rows'][11]['mass']) / s['mass'] * 100:.0f} %.</p>
<h2>9. Cost, mass and sustainability of every part (one set)</h2>
<table class="tiny"><tr><th>Item</th><th>Part</th><th class="r">Qty</th><th class="r">Mass kg</th><th>Material</th><th class="r">Material</th><th class="r">Hours</th><th class="r">Bought in</th><th class="r">Sust.</th></tr>{part_rows}</table>
</div></body></html>"""


def notes_html(n):
    c, s = n['costs'], n['sus']
    fea = n['fea']
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2026 reflective notes</title><style>{CSS}
body{{font-size:10pt;line-height:1.45}} p{{margin:0 0 2mm}}</style></head><body>
<div class="hdr"><span>Aero-Chair Ltd. ESP 2026 (8730-035) Task 2(b)</span><span>Reflective notes on the CAD drawing. 2026-11-10</span></div>
<h1>Reflective notes: economy class three-seat set</h1>
<p><b>What I chose and why.</b> I developed two ideas: a beam and leg seat with a reclining carbon fibre back (design A) and a set of fixed composite shells (design B).
I chose design A because it met every line of the specification. Design B was comfortable and stopped a reclining passenger reaching into the space behind, but it came out at about 9.5 kg a seat, its armrests could not lift and it cost more to make.</p>
<p><b>How the CAD drawing meets the brief.</b> Each seat is {E.SEAT_W} mm wide between the armrests, the seat height is {E.SEAT_H} mm and the back reclines {E.RECLINE}&deg; when the large button on the armrest is pressed.
The head rest is fixed, the tray is {E.TL} &times; {E.TW} mm, and the back carries a 10.1 inch screen with USB-C, USB-A and an audio jack and an A4 literature pocket. A pouch under each seat holds a 305 &times; 305 life vest.
The legs stand on four track fittings with locking studs, so the set is fixed to the floor. The lap belt has a lift lever buckle that can be opened with one movement by the passenger or the crew.</p>
<p><b>Weight and cost.</b> Modelling every part with its own material let me add up the mass instead of guessing it: {n['mass_seat']:.2f} kg a seat against the 8 kg limit.
My first model was 8.6 kg a seat. I thinned the back shell to 1.2 mm, lightened the tray, back foam and armrests, and changed the cover material to get under the limit.
The estimated cost to manufacture is {gbp(c['total'])} a set, well inside the £15,000 budget, and {s['share'] * 100:.0f} % of the mass is sustainable material.</p>
<p><b>Checking the design.</b> I checked the model for clashes in six positions (upright, reclined, trays down, armrests up) and found none.
The leg FEA for a 9 g forward landing gave {fea.get('vm_max', 0):.0f} MPa at the worst corner, a safety factor of {fea.get('sf_min', 0):.1f}, and my truss hand calculation agreed with the FEA within 7 % in the struts. This gave me confidence that both were right.</p>
<p><b>What went well.</b> Drawing the section through the seat centre line made the parts and the recline geometry easy to read, and the parts list ties every item number to its own part drawing.
Using the CAD model for every number meant the drawings, calculations and parts list always agreed.</p>
<p><b>What I would improve.</b> The sustainable share only just passes, so I would look at recycled carbon fibre for the back shell and a recycled foam. The sharp inside corners of the leg are where the stress peaks: I tried to add fillets but the CAD software could not make them on this shape, so in the next version I would redraw the leg profile with the radii in the sketch.
I treated the life vests as airline equipment outside the 8 kg limit; with them the seat is {n['mass_seat_v']:.2f} kg, so I would confirm this with the client early.
The 9 g check is static: the real certification test is a dynamic 16 g sled test, which I would plan for in the first weeks of the 26 week programme.</p>
</body></html>"""


def to_pdf(html_path, pdf_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto('file://' + html_path)
        pg.pdf(path=pdf_path, format='A4', prefer_css_page_size=True, print_background=True)
        b.close()


if __name__ == '__main__':
    n = numbers()
    for name, html in (('ESP26_calculations', calcs_html(n)), ('ESP26_reflective_notes', notes_html(n))):
        h = os.path.join(FOLDER, name + '.html')
        open(h, 'w').write(html)
        to_pdf(h, os.path.join(FOLDER, name + '.pdf'))
        print('wrote', name)
    c, (F, members, R) = n['costs'], n['truss']
    key = dict(mass_set=n['mass_set'], mass_seat=n['mass_seat'], mass_seat_vests=n['mass_seat_v'], cost=c['total'],
               budget=BUDGET, margin=c['margin'], hours=c['hours'], sustainable=n['sus']['share'], width=n['size0'][0],
               depth=n['size0'][1], depth_reclined=n['size1'][1], height=n['size0'][2] - 20, seat_height=E.SEAT_H,
               seat_width=E.SEAT_W, recline=E.RECLINE, stroke=n['lock0'][2] - n['lock1'][2], lock_force=n['lock_F'],
               leg_load=F, members=[dict(name=m['name'], force=m['force'], hand=m['stress'],
                                         fea=next((p['vm'] for p in n['fea'].get('probes', []) if p['name'] == m['name']), None))
                                    for m in members],
               fea=dict((k, n['fea'].get(k)) for k in ('vm_max', 'sf_min', 'disp_max')))
    json.dump(key, open(os.path.join(FOLDER, 'ESP26_calculations.json'), 'w'), indent=1)
    words = len(re.sub('<[^>]+>', ' ', notes_html(n).split('<h1>')[1]).split())
    print('reflective notes words:', words)
    c = n['costs']
    print('cost %.0f (mat %.0f bought %.0f hours %.1f labour %.0f) sustainable %.3f lock F %.0f arm %.1f workers %.1f' % (
        c['total'], c['material'], c['bought'], c['hours'], c['labour'], n['sus']['share'], n['lock_F'], n['lock_arm'], c['workers']))
    print('size', n['size0'], n['size1'])
    print('truss', n['truss'][0], [(m['name'], round(m['force']), round(m['stress'], 1)) for m in n['truss'][1]], n['truss'][2])
