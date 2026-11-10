"""ESP 2025 Task 2: calculations (size and mass against the brief, pill capacity, battery life, the drive, the lid
catch, waterproofing, cost and the maximum number of units for each budget, the programme) and the reflective notes.

Every size and mass comes from models/esp2025.py (the CAD model) and the lid catch FEA in docs/ESP 2025/fea, so the
calculations, drawings and model always agree. Prices, labour times and current draws are stated assumptions,
listed once in the tables below.
Writes docs/ESP 2025/ESP25_calculations.html and .pdf, ESP25_reflective_notes.html and .pdf, ESP25_calculations.json.
Run from the repository root:  /home/user/venv/bin/python tools/esp2025_calcs.py
"""
import json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import esp2025 as E  # noqa: E402

FOLDER = os.path.join(ROOT, 'docs', 'ESP 2025')
G = 9.81
LIMIT = (190, 190, 60)          # mm, brief
MASS_LIMIT = 0.5                # kg with batteries, brief
BUDGETS = [(1500, 97500, 65.0, 30), (3000, 120000, 40.0, 35)]   # units, budget £, target £ a unit, weeks (brief)
LABOUR = 17.0                   # £ an hour (brief)

# ------------------------------------------------------------------ battery life: what draws current (at the 6 V battery)
# (load, mA while on, seconds on a day, note) for twice a day dosing, the worst case
LOADS = [
    ('Microcontroller asleep with the clock running', 0.004, 86400, 'all day'),
    ('Display (reflective LCD, always on)', 0.012, 86400, 'all day, no backlight'),
    ('Gear motor turning the carousel', 120.0, 2 * 1.6, '2 doses, 4 turns of the worm at 150 rpm = 1.6 s each'),
    ('Alarm: buzzer and flashing light, until the button is pressed', 30.0, 2 * 180, '2 doses; allow 3 minutes each before the patient presses'),
    ('Microcontroller awake (dose, display update, sensors)', 3.0, 2 * 10 + 24 * 2, '10 s a dose and 2 s an hour'),
    ('Home and drop sensors (infrared)', 20.0, 2 * 3, 'only while the carousel turns and the pills fall'),
    ('NFC programming by the pharmacy', 0.0, 0, 'powered by the phone or tablet, not the battery'),
]
CELL_MAH = 1100                 # AAA alkaline at a low current
USABLE = 0.80                   # use 80 % before the low battery warning
PILL_D, PILL_L = E.PILL
PILL_DENSITY = 1.3              # g/cm3, a typical tablet
MU_DECK = 0.30                  # PP on PP, pills dragged on the deck
MU_WORM = 0.25                  # acetal on acetal, dry
WORM_EFF = 0.40                 # efficiency of a single start acetal worm (self locking)
MOTOR_STALL = 0.098             # N m: N20 gear motor 6 V 200:1 stall torque (about 1 kg cm)
MOTOR_RPM = 150
PRY = 200                       # N, a strong pull on the front of the lid to force it open (assumption)
CATCH_YIELD = 75                # MPa, PP-GF30 tensile strength (conservative)

# ------------------------------------------------------------------ cost assumptions
# material: (name, £/kg, buy to fly ratio (sprues, runners, scrap), note)
MATERIALS = {
    'pp':    ('Polypropylene homopolymer, white or blue', 1.60, 1.08, 'Recyclable (code 5)'),
    'cpp':   ('Clarified polypropylene, clear', 2.10, 1.08, 'Recyclable (code 5); clear like glass'),
    'ppgf':  ('PP with 30 % glass fibre', 3.20, 1.10, 'Stiff and strong for the catch'),
    'pom':   ('Acetal (POM)', 3.80, 1.10, 'Low friction gears, no grease'),
    'sil':   ('Silicone rubber', 12.0, 1.15, 'Seals that stay soft for years'),
    'tpe':   ('TPE feet', 6.0, 1.10, 'Bought as a reel of self adhesive feet'),
    'bought': ('Bought in part', 0.0, 1.0, 'Price each in the parts table'),
}
# part key: (material, moulding or fitting seconds each, bought in price £ each)
PART_COST = {
    'chassis': ('pp', 40, 0), 'pharmacy_lock': ('bought', 20, 1.90), 'lock_cam': ('bought', 5, 0.15),
    'chute': ('pp', 15, 0), 'drop_sensor': ('bought', 15, 0.30),
    'carousel': ('pp', 35, 0), 'drive_gear': ('pom', 18, 0),
    'bottom_cover': ('pp', 30, 0), 'foot': ('tpe', 3, 0), 'main_pcb': ('bought', 30, 5.20),
    'battery_holder': ('bought', 10, 0.35), 'battery': ('bought', 3, 0.25), 'gear_motor': ('bought', 15, 2.20),
    'motor_clamp': ('pp', 8, 0), 'worm': ('pom', 10, 0), 'home_sensor': ('bought', 10, 0.40),
    'battery_door': ('pp', 10, 0), 'door_seal': ('sil', 5, 0), 'security_screw': ('bought', 8, 0.06),
    'cover_screw': ('bought', 8, 0.03),
    'pod_column': ('pp', 18, 0), 'pod_oring': ('bought', 5, 0.08), 'panel_pcb': ('bought', 15, 1.10),
    'lcd': ('bought', 10, 1.60), 'tact_switch': ('bought', 0, 0.08), 'led': ('bought', 0, 0.05),
    'led_lens': ('cpp', 8, 0), 'buzzer': ('bought', 0, 0.35), 'button': ('sil', 10, 0),
    'display_window': ('cpp', 8, 0), 'pod_cap': ('pp', 20, 0),
    'lid': ('cpp', 35, 0), 'gasket': ('sil', 8, 0), 'lid_catch': ('ppgf', 12, 0), 'hinge_pin': ('bought', 15, 0.05),
    'drawer': ('pp', 18, 0), 'drawer_seal': ('sil', 8, 0),
}
MOULD_RATE = 28.0               # £ an hour for an injection moulding machine with its share of the operator (the
                                # seconds above are cycle time per part for moulded parts, fitting time for bought parts)
ASSEMBLY_MIN = 14               # minutes a unit: final assembly, wiring the two boards, closing the case
TEST_MIN = 6                    # minutes a unit: program by NFC, run a dose, leak test (air decay), label, pack
PACK = 0.90                     # £ a unit: recycled card box, pharmacy instructions, patient card
OVERHEAD = 0.15                 # factory overhead and profit margin on the factory cost
TOOLING = 31000                 # £: aluminium injection mould tools for the 15 moulded parts (family tools)
DESIGN_PROTO = 9000             # £: design sign-off, 10 prototypes, IP67 and drop tests, user trial
# (task, start week, end week): the programme for 1500; for 3000 production runs at twice the rate with a second line
PROGRAMME = [('Design and drawings (this task), health trust approval', 0, 4),
             ('Prototypes 3D printed, user trial with patients and pharmacists', 3, 9),
             ('Mould tools made and first parts sampled', 6, 16),
             ('Tests: IP67 water, 1 m drop, 10,000 dose cycles, EMC; changes', 14, 18),
             ('Production line set up, pilot batch of 50', 17, 19)]
LINE_RATE = 150                 # units a week on one assembly line (one shift, 2 operators)


def gbp(v, d=0):
    return '£' + (format(round(v), ',') if d == 0 else '%.2f' % v)


def parts_table(items):
    by = E.masses(items)
    rows = []
    for p in E.PARTS:
        q, m = by.get(p['key'], [0, 0.0])
        mat, secs, buy = PART_COST[p['key']]
        name, price, btf, _ = MATERIALS[mat]
        raw = m * btf * price
        rows.append(dict(no=p['no'], key=p['key'], name=p['name'], qty=q, mass=m, mat=mat, raw=raw,
                         secs=secs * q, process=secs * q / 3600 * MOULD_RATE, bought=buy * q, recyclable=p['recyclable']))
    return rows


def costs(items):
    rows = parts_table(items)
    material = sum(r['raw'] for r in rows)
    bought = sum(r['bought'] for r in rows)
    process = sum(r['process'] for r in rows)
    labour = (ASSEMBLY_MIN + TEST_MIN) / 60 * LABOUR
    factory = material + bought + process + labour + PACK
    variable = factory * (1 + OVERHEAD)
    fixed = TOOLING + DESIGN_PROTO
    out = dict(rows=rows, material=material, bought=bought, process=process, labour=labour, pack=PACK,
               factory=factory, overhead=factory * OVERHEAD, variable=variable, fixed=fixed, cases=[])
    for units, budget, target, weeks in BUDGETS:
        unit = variable + fixed / units
        maxn = int((budget - fixed) / variable)
        out['cases'].append(dict(units=units, budget=budget, target=target, weeks=weeks, unit=unit, total=unit * units,
                                 maxn=maxn, ok=unit <= target))
    return out


def battery(n_doses=2):
    rows = []
    for name, ma, secs, note in LOADS:
        rows.append((name, ma, secs, ma * secs / 3600, note))
    day = sum(r[3] for r in rows)
    usable = CELL_MAH * USABLE
    return dict(rows=rows, day=day, usable=usable, days=usable / day, refills=usable / day / 14)


def drive(items):
    by = E.masses(items)
    car = by['carousel'][1] + by['drive_gear'][1]
    cap = E.capacity()
    pill_g = math.pi * (PILL_D / 2) ** 2 * PILL_L / 1000 * PILL_DENSITY
    pills = cap['total'] * (E.N_SEG - 2) * pill_g / 1000          # kg, every compartment full of the largest pills
    r_mean = (E.HUB[1] + E.CAR_OUT[0]) / 2 / 1000
    T_car = MU_DECK * (car + pills) * G * r_mean
    ratio = E.GEAR_N
    T_motor = T_car / ratio / WORM_EFF
    lead = math.degrees(math.atan(E.WORM_PITCH / (math.pi * 2 * (E.WORM_R[0] + E.WORM_R[1]) / 2)))
    fric = math.degrees(math.atan(MU_WORM))
    t_step = 4 / (MOTOR_RPM / 60)
    return dict(car=car, pills=pills, pill_g=pill_g, r_mean=r_mean, T_car=T_car, ratio=ratio, T_motor=T_motor,
                sf=MOTOR_STALL / T_motor, lead=lead, fric=fric, locking=lead < fric, t_step=t_step,
                turns=E.SEG / (360 / E.GEAR_N))


def catch_hand():
    x0, x1 = E.CATCH['x']
    b = x1 - x0
    t = E.CATCH['r'][1] - E.CATCH['r'][0]
    lip = E.CATCH['lip'] - E.CATCH['r'][1]
    h = E.CATCH['z'][1] - E.CATCH['z'][0]
    e = (E.CATCH['r'][1] + E.CATCH['lip']) / 2 - (E.CATCH['r'][0] + E.CATCH['r'][1]) / 2   # load line to tab centre
    direct = PRY / (b * t)
    bend = PRY * e / (b * t ** 2 / 6)
    lip_bend = PRY * (lip / 2) / (b * h ** 2 / 6)
    lip_shear = PRY / (b * h)
    return dict(b=b, t=t, lip=lip, h=h, e=e, direct=direct, bend=bend, total=direct + bend, lip_bend=lip_bend,
                lip_shear=lip_shear, sf=CATCH_YIELD / (direct + bend))


def numbers():
    import cadquery as cq
    n = {}
    items = E.dispenser_instances()
    comp = cq.Compound.makeCompound([s.val() for _, _, s in items])
    bb = comp.BoundingBox()
    n['size'] = (bb.xlen, bb.ylen, bb.zlen)
    by = E.masses(items)
    n['mass'] = sum(m for q, m in by.values())
    n['groups'] = [(g, t, sum(by[p['key']][1] for p in E.PARTS if p['group'] == g and p['key'] in by)) for g, t in E.GROUPS]
    n['battery_mass'] = by['battery'][1]
    n['parts'] = len(items)
    n['capacity'] = E.capacity()
    n['battery'] = battery()
    n['drive'] = drive(items)
    n['catch'] = catch_hand()
    n['costs'] = costs(items)
    rec = sum(r['mass'] for r in n['costs']['rows'] if r['recyclable'])
    case = sum(r['mass'] for r in n['costs']['rows'] if r['key'] in ('chassis', 'bottom_cover', 'lid', 'pod_cap', 'drawer', 'pod_column', 'battery_door'))
    n['recycle'] = dict(recyclable=rec, share=rec / n['mass'], case=case)
    f = os.path.join(FOLDER, 'fea', 'esp2025_p%02d_lid_catch.json' % E.PART['lid_catch']['no'])
    n['fea'] = json.load(open(f))['results'] if os.path.exists(f) else {}
    weeks = []
    for units, budget, target, wk in BUDGETS:
        lines = 1 if units <= 1500 else 2
        prod = math.ceil(units / (LINE_RATE * lines))
        start = PROGRAMME[-1][2]
        weeks.append(dict(units=units, lines=lines, prod=prod, start=start, end=start + prod + 1, limit=wk))
    n['programme'] = weeks
    return n


CSS = """
@page{size:A4;margin:11mm 13mm}
body{font-family:Arial,Helvetica,sans-serif;font-size:8.3pt;line-height:1.22;color:#111}
h1{font-size:14pt;margin:0 0 2mm} h2{font-size:10pt;margin:2.2mm 0 0.8mm;color:#16335B;border-bottom:0.3mm solid #16335B}
table{border-collapse:collapse;width:100%;margin:1mm 0} td,th{border:0.2mm solid #888;padding:0.2mm 1.5mm;text-align:left;vertical-align:top}
th{background:#E8EEF6} .r{text-align:right;white-space:nowrap} .ok{color:#1F7A3A;font-weight:bold} .no{color:#B3261E;font-weight:bold}
.hdr{display:flex;justify-content:space-between;font-size:7pt;color:#444;border-bottom:0.3mm solid #444;margin-bottom:2mm}
.page{page-break-after:always} .small{font-size:8.2pt} .tiny{font-size:7pt} .tiny td,.tiny th{padding:0.15mm 1.2mm} ul{margin:0.5mm 0 0.5mm 5mm;padding:0}
tr.tot td{font-weight:bold;background:#F3F6FA}
"""


def okno(ok, text):
    return '<span class="%s">%s</span>' % ('ok' if ok else 'no', text)


def calcs_html(n):
    c, bat, dr, ca, cap = n['costs'], n['battery'], n['drive'], n['catch'], n['capacity']
    fea = n['fea']
    sx, sy, sz = n['size']
    hdr = lambda k: ('<div class="hdr"><span>WBEP Ltd for the health trust. ESP 2025 (8730-035) Task 2: automated pill '
                     'dispenser</span><span>Calculation sheet %d of 4. Ref ESP25-CALC. 2026-11-10</span></div>' % k)
    grp = ''.join('<tr><td>%s</td><td class="r">%.0f g</td></tr>' % (t.split(' (')[0], mm * 1000) for g, t, mm in n['groups'])
    bat_rows = ''.join('<tr><td>%s</td><td class="r">%g mA</td><td class="r">%g s</td><td class="r">%.3f mAh</td><td>%s</td></tr>' % r
                       for r in bat['rows'])
    row_cap = ''.join('<tr><td>Row %d: pills from radius %.1f to %.1f</td><td>gap between ribs at the inner end %.1f mm / %g mm</td>'
                      '<td class="r">%d a layer</td></tr>' % (i + 1, r['r'], r['r'] + PILL_L, r['width'], PILL_D, r['n'])
                      for i, r in enumerate(cap['rows']))
    part_rows = ''.join(
        '<tr><td>%d</td><td>%s</td><td class="r">%d</td><td class="r">%.1f</td><td>%s</td><td class="r">%s</td>'
        '<td class="r">%s</td><td class="r">%s</td></tr>' % (
            r['no'], r['name'], r['qty'], r['mass'] * 1000, MATERIALS[r['mat']][0] if r['mat'] != 'bought' else 'Bought in',
            gbp(r['raw'], 2) if r['raw'] >= 0.005 else '&ndash;', gbp(r['process'], 2) if r['process'] >= 0.005 else '&ndash;',
            gbp(r['bought'], 2) if r['bought'] else '&ndash;')
        for r in c['rows'] if r['qty'])
    mat_rows = ''.join('<tr><td>%s</td><td class="r">£%.2f</td><td class="r">%.2f</td><td>%s</td></tr>' % v
                       for k, v in MATERIALS.items() if k != 'bought')
    case_rows = ''.join(
        '<tr><td>%d units</td><td class="r">%s</td><td class="r">%s + %s / %d = <b>%s</b></td><td class="r">%s</td>'
        '<td class="r">%s</td><td class="r">(%s &minus; %s) / %s = <b>%s</b></td></tr>' % (
            x['units'], gbp(x['budget']), gbp(c['variable'], 2), gbp(c['fixed']), x['units'], gbp(x['unit'], 2),
            okno(x['ok'], '%s target' % gbp(x['target'])), gbp(x['total']), gbp(x['budget']), gbp(c['fixed']),
            gbp(c['variable'], 2), format(x['maxn'], ',')) for x in c['cases'])
    prog_rows = ''.join('<tr><td>%s</td><td class="r">%g</td><td class="r">%g</td><td class="r">%g</td></tr>' % (t, a, b, b - a)
                        for t, a, b in PROGRAMME)
    prog_rows += ''.join('<tr><td>Production of %d units: %d line%s at %d a week, then delivery</td><td class="r">%d</td>'
                         '<td class="r">%d</td><td class="r">%d</td></tr>' % (
                             w['units'], w['lines'], 's' if w['lines'] > 1 else '', LINE_RATE * w['lines'], w['start'], w['end'],
                             w['end'] - w['start']) for w in n['programme'])
    fea_line = ('FEA (PP-GF30, %d N): peak von Mises %.1f MPa, safety factor %.1f.' % (PRY, fea['vm_max'], fea['sf_min'])
                if fea else 'FEA: run tools/build_fea.py first.')
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2025 calculations</title><style>{CSS}</style></head><body>
<div class="page">{hdr(1)}
<h1>Calculations for the preferred design (Design A): carousel pill dispenser</h1>
<h2>1. Assumptions</h2>
<ul class="small">
<li>Sizes and masses come from the CAD model (models/esp2025.py): all {len(E.PARTS)} parts are modelled with their own material density; the dispenser has {n['parts']} parts in all.</li>
<li>The largest pill in the brief: a cylinder {PILL_D:g} mm across and {PILL_L:g} mm long, {PILL_DENSITY} g/cm&sup3; ({dr['pill_g']:.2f} g).</li>
<li>Twice a day dosing is the worst case for the battery. The patient presses the button within 3 minutes of the alarm on average.</li>
<li>Labour £{LABOUR:.0f} an hour (brief). Material and bought in prices are supplier estimates for batches of 1500 to 3000; moulding at £{MOULD_RATE:.0f} an hour of machine time with its operator share.</li>
<li>Friction: pills and PP carousel on the PP deck &mu; = {MU_DECK}; acetal worm on acetal gear &mu; = {MU_WORM}.</li>
<li>Prying force on the lid {PRY} N: a strong two handed pull at the front edge by someone trying to get at the pills.</li>
</ul>
<h2>2. Size and mass against the brief</h2>
<table><tr><th>Check</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Length (front of the drawer to the back of the hinge)</td><td>CAD bounding box (brief: 190 max)</td><td class="r">{okno(sy <= LIMIT[1], '%.1f mm' % sy)}</td></tr>
<tr><td>Width</td><td>case &Oslash;{2 * E.R_CASE} (brief: 190 max)</td><td class="r">{okno(sx <= LIMIT[0], '%.1f mm' % sx)}</td></tr>
<tr><td>Height (feet to the top of the button)</td><td>CAD bounding box (brief: 60 max)</td><td class="r">{okno(sz <= LIMIT[2], '%.1f mm' % sz)}</td></tr>
<tr><td>Mass with the batteries, empty</td><td>sum of volume &times; density for all {n['parts']} parts; cells {n['battery_mass'] * 1000:.0f} g</td><td class="r">{okno(n['mass'] <= MASS_LIMIT, '%.0f g' % (n['mass'] * 1000))}</td></tr>
<tr><td>Mass when full of the largest pills</td><td>{n['mass'] * 1000:.0f} + {dr['pills'] * 1000:.0f} g of pills ({cap['total']} in each of {E.N_SEG - 2} compartments)</td><td class="r">{(n['mass'] + dr['pills']) * 1000:.0f} g</td></tr>
</table>
<table class="small" style="width:48%;display:inline-table;margin-right:3%"><tr><th>Sub-assembly</th><th class="r">Mass</th></tr>{grp}</table>
<p class="small" style="display:inline-block;width:47%;vertical-align:top">The brief limits the unit with its batteries: {n['mass'] * 1000:.0f} g leaves {(MASS_LIMIT - n['mass']) * 1000:.0f} g in hand. The walls are 1.8 to 2 mm of polypropylene, the lightest common moulding plastic (905 kg/m&sup3;), and four AAA cells ({n['battery_mass'] * 1000:.0f} g) were chosen in place of AA cells to save about 50 g.</p>
<h2>3. Doses and pill capacity</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Compartments</td><td>{E.N_SEG} segments of {E.SEG}&deg;, less 2 capped blanks</td><td class="r">{E.N_SEG - 2}</td></tr>
<tr><td>Once a day medication</td><td>{E.N_SEG - 2} compartments &divide; 1 a day (brief: refill every 28 days)</td><td class="r">{okno(True, '%d days' % (E.N_SEG - 2))}</td></tr>
<tr><td>Twice a day medication</td><td>{E.N_SEG - 2} &divide; 2 a day (brief: refill every 14 days)</td><td class="r">{okno(True, '%d days' % ((E.N_SEG - 2) // 2))}</td></tr>
{row_cap}
<tr><td>Layers</td><td>depth {cap['depth']:.1f} mm (a 1.5 mm gap kept under the lid) &divide; {PILL_D:g} mm</td><td class="r">{cap['layers']}</td></tr>
<tr><td>Largest pills in one compartment</td><td>{cap['per_layer']} a layer &times; {cap['layers']} layers (brief: at least 3)</td><td class="r">{okno(cap['total'] >= 3, '%d' % cap['total'])}</td></tr>
<tr><td>Volume of one compartment</td><td>(&pi;(R<sub>o</sub>&sup2; &minus; R<sub>i</sub>&sup2;) / {E.N_SEG} &minus; rib) &times; depth</td><td class="r">{cap['volume']:.1f} cm&sup3;</td></tr>
<tr><td>Gap under the lid</td><td>{E.LID_Z[1] - E.LID_TOP:g} &minus; {E.CAR_Z[1]} (smaller than a pill, so pills cannot climb into the next compartment)</td><td class="r">{E.LID_Z[1] - E.LID_TOP - E.CAR_Z[1]:.1f} mm</td></tr>
</table>
</div>
<div class="page">{hdr(2)}
<h2>4. Battery life (4 &times; AAA, 6 V)</h2>
<table class="small"><tr><th>Load</th><th class="r">Current</th><th class="r">Time a day</th><th class="r">Charge a day</th><th>How it is used</th></tr>{bat_rows}
<tr class="tot"><td>Total a day, twice a day dosing</td><td></td><td></td><td class="r">{bat['day']:.2f} mAh</td><td></td></tr></table>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Usable charge</td><td>{CELL_MAH} mAh &times; {USABLE} (cells in series: the same current flows through all four)</td><td class="r">{bat['usable']:.0f} mAh</td></tr>
<tr><td>Battery life</td><td>{bat['usable']:.0f} / {bat['day']:.2f}</td><td class="r">{okno(True, '%.0f days' % bat['days'])}</td></tr>
<tr><td>Refills on one set of cells (twice a day)</td><td>{bat['days']:.0f} / 14</td><td class="r">{bat['refills']:.0f}</td></tr>
</table>
<p class="small">The pharmacy changes the cells at a refill when the display shows the low battery sign (at 20 % left there are still about {bat['days'] * 0.2 / USABLE:.0f} days). The clock keeps time for 2 minutes without cells, long enough to change them.</p>
<h2>5. The drive: worm and wheel</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Carousel and gear (CAD)</td><td>sum of volume &times; density</td><td class="r">{dr['car'] * 1000:.0f} g</td></tr>
<tr><td>Pills, every compartment full</td><td>{cap['total']} &times; {E.N_SEG - 2} &times; {dr['pill_g']:.2f} g</td><td class="r">{dr['pills'] * 1000:.0f} g</td></tr>
<tr><td>Torque to turn the carousel</td><td>&mu; m g r = {MU_DECK} &times; {dr['car'] + dr['pills']:.3f} &times; 9.81 &times; {dr['r_mean']:.4f}</td><td class="r">{dr['T_car'] * 1000:.1f} N mm</td></tr>
<tr><td>Gear ratio</td><td>{E.GEAR_N} teeth, single start worm</td><td class="r">{dr['ratio']}:1</td></tr>
<tr><td>Torque at the motor</td><td>{dr['T_car'] * 1000:.1f} / {dr['ratio']} / {WORM_EFF} (efficiency)</td><td class="r">{dr['T_motor'] * 1000:.2f} N mm</td></tr>
<tr><td>Safety factor on the motor</td><td>stall {MOTOR_STALL * 1000:.0f} N mm / {dr['T_motor'] * 1000:.2f}: it never struggles, even with a stuck pill</td><td class="r">{okno(dr['sf'] > 5, '%.0f' % dr['sf'])}</td></tr>
<tr><td>Worm turns a dose</td><td>{E.SEG}&deg; / (360 / {E.GEAR_N})&deg; a tooth</td><td class="r">{dr['turns']:.0f}</td></tr>
<tr><td>Time to turn one dose</td><td>{dr['turns']:.0f} turns at {MOTOR_RPM} rpm</td><td class="r">{dr['t_step']:.1f} s</td></tr>
<tr><td>Can the carousel be forced round by hand?</td><td>worm lead angle tan&#8315;&sup1;({E.WORM_PITCH:.3f} / &pi; &times; {E.WORM_R[0] + E.WORM_R[1]:.1f}) = {dr['lead']:.1f}&deg; &lt; friction angle tan&#8315;&sup1;{MU_WORM} = {dr['fric']:.1f}&deg;</td><td class="r">{okno(dr['locking'], 'No: self locking')}</td></tr>
</table>
<h2>6. Tamper-proof lock: the lid catch</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Prying force on the lid, all taken by the catch hook</td><td>assumption (the hinge takes the rest of the lid)</td><td class="r">{PRY} N</td></tr>
<tr><td>Direct stress in the tab</td><td>{PRY} / ({ca['b']:g} &times; {ca['t']:g})</td><td class="r">{ca['direct']:.1f} MPa</td></tr>
<tr><td>Bending in the tab: the cam presses on the hook {ca['e']:.2f} mm out from the middle of the tab</td><td>{PRY} &times; {ca['e']:.2f} / ({ca['b']:g} &times; {ca['t']:g}&sup2; / 6)</td><td class="r">{ca['bend']:.1f} MPa</td></tr>
<tr><td>Total in the tab (outside face)</td><td>{ca['direct']:.1f} + {ca['bend']:.1f}</td><td class="r">{ca['total']:.1f} MPa</td></tr>
<tr><td>Hook bending and shear at its root</td><td>{PRY} &times; {ca['lip'] / 2:.1f} / ({ca['b']:g} &times; {ca['h']:g}&sup2; / 6); {PRY} / ({ca['b']:g} &times; {ca['h']:g})</td><td class="r">{ca['lip_bend']:.1f}; {ca['lip_shear']:.1f} MPa</td></tr>
<tr><td>Safety factor (PP-GF30, {CATCH_YIELD} MPa)</td><td>{CATCH_YIELD} / {ca['total']:.1f}</td><td class="r">{okno(ca['sf'] >= 1.5, '%.1f' % ca['sf'])}</td></tr>
<tr><td colspan="3" class="small">{fea_line} The FEA also shows the stress round the inside corner of the hook, where the hand calculation has no stress concentration. The lock cam is steel and the lock body zinc: both are much stronger than the plastic catch, so the catch sets the limit.</td></tr>
</table>
</div>
<div class="page">{hdr(3)}
<h2>7. Waterproof and tamper-proof: how every way in is closed</h2>
<table class="small"><tr><th>Opening</th><th>How it is sealed</th><th>Who can open it</th></tr>
<tr><td>Lid to chassis</td><td>Silicone gasket ring (item {E.PART['gasket']['no']}), clamped by the catch</td><td>Pharmacy key only</td></tr>
<tr><td>Lid round the control pod</td><td>O-ring (item {E.PART['pod_oring']['no']}) in the pod column, inside the lid collar</td><td>&ndash;</td></tr>
<tr><td>Button, light, display window</td><td>Each has a flange clamped under the pod cap; the cap is welded to the column</td><td>Nobody (sealed for life)</td></tr>
<tr><td>Bottom cover to chassis</td><td>The same gasket ring, squeezed by four screws</td><td>Factory</td></tr>
<tr><td>Battery doors</td><td>Silicone seals (item {E.PART['door_seal']['no']}), pin Torx security screws</td><td>Pharmacy (bit kept at the counter)</td></tr>
<tr><td>Drawer</td><td>Silicone frame seal on the drawer front, pressed on the case when it clicks home</td><td>Patient (empty except the dose)</td></tr>
<tr><td>Programming</td><td>NFC through the plastic: no socket, no hole</td><td>Pharmacy app</td></tr>
</table>
<p class="small">Target IP67 (30 minutes under 1 m of water); each unit gets an air leak test at the end of the line. Only the compartment over the drop hole is ever open to the drawer, the worm cannot be back driven, and the lid needs the pharmacy key, so the patient can only ever take the dose that is due.</p>
<h2>8. Cost of one unit, and the most units each budget can buy</h2>
<table><tr><th>Cost a unit</th><th>Working</th><th class="r">£</th></tr>
<tr><td>Materials for the moulded parts</td><td>mass &times; price &times; buy to fly, every part (table 11)</td><td class="r">{gbp(c['material'], 2)}</td></tr>
<tr><td>Moulding</td><td>cycle seconds &times; £{MOULD_RATE:.0f} an hour</td><td class="r">{gbp(c['process'], 2)}</td></tr>
<tr><td>Bought in parts (electronics, lock, cells, screws)</td><td>supplier prices for 1500+</td><td class="r">{gbp(c['bought'], 2)}</td></tr>
<tr><td>Assembly and test labour</td><td>({ASSEMBLY_MIN} + {TEST_MIN}) min &times; £{LABOUR:.0f} an hour</td><td class="r">{gbp(c['labour'], 2)}</td></tr>
<tr><td>Packaging and instructions</td><td></td><td class="r">{gbp(c['pack'], 2)}</td></tr>
<tr><td>Overhead and margin</td><td>{OVERHEAD * 100:.0f} % of {gbp(c['factory'], 2)}</td><td class="r">{gbp(c['overhead'], 2)}</td></tr>
<tr class="tot"><td>Cost a unit before the one-off costs</td><td></td><td class="r">{gbp(c['variable'], 2)}</td></tr>
<tr><td>One-off: mould tools and design, prototypes and tests</td><td>{gbp(TOOLING)} + {gbp(DESIGN_PROTO)}, shared by the order</td><td class="r">{gbp(c['fixed'])}</td></tr>
</table>
<table><tr><th>Order</th><th class="r">Budget</th><th class="r">Cost a unit</th><th class="r">Against</th><th class="r">Order cost</th><th class="r">Most units the budget can buy</th></tr>{case_rows}</table>
<p class="small">{'Both orders come in under their target.' if all(x['ok'] for x in c['cases']) else ' '.join(('The %s order comes in under its £%.0f target.' if x['ok'] else 'The %s order is over its £%.0f target, so that budget buys fewer units (right hand column).') % (format(x['units'], ','), x['target']) for x in c['cases'])} The £40 target for 3000 units is the hard one: the electronics ({gbp(sum(r['bought'] for r in c['rows'] if r['key'] in ('main_pcb', 'panel_pcb', 'lcd', 'gear_motor', 'drop_sensor', 'home_sensor', 'buzzer', 'led', 'tact_switch')), 2)}) are the biggest cost, so the design uses one motor and one drop hole in place of a motor or latch for each compartment.</p>
<h2>9. Programme</h2>
<table><tr><th>Task</th><th class="r">Start week</th><th class="r">End week</th><th class="r">Weeks</th></tr>{prog_rows}</table>
<p class="small">1500 units are delivered in week {n['programme'][0]['end']} (brief: 30 weeks); 3000 units, with a second assembly line, in week {n['programme'][1]['end']} (brief: 35 weeks).</p>
<h2>10. Materials and recycling</h2>
<table class="small"><tr><th>Material</th><th class="r">£/kg</th><th class="r">Buy to fly</th><th>Why</th></tr>{mat_rows}</table>
<p class="small">All the case parts are polypropylene: {n['recycle']['case'] * 1000:.0f} g of the {n['mass'] * 1000:.0f} g. With the clear lid and carousel, {n['recycle']['share'] * 100:.0f} % of the mass is recyclable polypropylene (code 5) and needs no separating; the boards, cells and lock come out with eight screws for WEEE recycling.</p>
</div>
<div>{hdr(4)}
<h2>11. Mass and cost of every part (one dispenser)</h2>
<table class="tiny"><tr><th>Item</th><th>Part</th><th class="r">Qty</th><th class="r">Mass g</th><th>Material</th><th class="r">Material</th><th class="r">Moulding</th><th class="r">Bought in</th></tr>{part_rows}</table>
</div></body></html>"""


def notes_html(n):
    c, bat, cap, ca = n['costs'], n['battery'], n['capacity'], n['catch']
    fea = n['fea']
    sx, sy, sz = n['size']
    c1, c2 = c['cases']
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2025 reflective notes</title><style>{CSS}
body{{font-size:10pt;line-height:1.45}} p{{margin:0 0 2mm}}</style></head><body>
<div class="hdr"><span>WBEP Ltd for the health trust. ESP 2025 (8730-035) Task 2, Part B</span><span>Reflective notes on the CAD drawing. 2026-11-10</span></div>
<h1>Reflective notes: automated pill dispenser</h1>
<p><b>How my ideas developed.</b> I sketched two dispensers. Design B was a rectangular cassette with 28 compartments, each with its own spring trapdoor and latch. It was simple to fill, but 28 latches cost more, weigh more and use more battery than one motor, and every trapdoor could leak or jam. Design A is a round carousel that turns over a deck with a single drop hole, so only the dose that is due can ever reach the patient. I chose design A.</p>
<p><b>How the design meets the specification.</b> The dispenser is {sx:.0f} &times; {sy:.0f} &times; {sz:.0f} mm, inside the 190 &times; 190 &times; 60 mm limit, and the CAD model gives a mass of {n['mass'] * 1000:.0f} g with its four AAA cells, under 0.5 kg. There are 28 compartments, so it holds 28 days of once a day doses or 14 days of twice a day doses. Each compartment holds {cap['total']} of the largest pills (the brief asks for at least three). When a dose is due the buzzer sounds and the light next to the green PRESS HERE button flashes. Pressing the button turns the carousel one step and the pills drop into the drawer. The alarm keeps going until the drop sensor sees the pills fall. Only the pharmacy key opens the lid, and the worm drive cannot be turned by hand, so it is tamper-proof. Gaskets, an O-ring and seals make it waterproof, the case is polypropylene so it can be recycled, and four cells last about {bat['days']:.0f} days.</p>
<p><b>What changed as I worked.</b> The interference check found problems I had not seen on paper. The motor gearbox overlapped the gear teeth, so I moved the motor along the worm axis. The home flag on the gear hit the worm at the last doses, so I used a hole in the gear and a sensor underneath instead. The lock cam turned down into the bottom cover, so I made it turn up. My first lid catch was 8 mm wide and the FEA gave a safety factor of only 1.0, so I made it wider, thicker and curved to follow the case. Checking the lid at small angles then showed it swinging into the carousel, so I made the carousel slightly smaller.</p>
<p><b>Checking it is safe and affordable.</b> The lid catch is the part that stops someone forcing the lid. My hand calculation gave {ca['total']:.0f} MPa at a {PRY} N pull and the FEA gave {fea.get('vm_max', 0):.0f} MPa, a safety factor of {fea.get('sf_min', 0):.1f}. The cost is {gbp(c1['unit'], 2)} a unit for 1500 units (target £65) and {gbp(c2['unit'], 2)} a unit for 3000 (target £40), {'so the health trust can order the larger batch' if c2['ok'] else 'so the £%s budget buys %s units, not 3000' % (format(c2['budget'], ','), format(c2['maxn'], ','))}. {'The programme fits inside 30 and 35 weeks.' if all(w['end'] <= w['limit'] for w in n['programme']) else 'The programme is longer than the brief allows, so production must start sooner.'}</p>
<p><b>What I would improve.</b> I would test a prototype with patients who have arthritis, to check the button and the drawer are easy to use. I would also look at a rechargeable cell to save waste, and at a version that sends a message to a carer if a dose is missed.</p>
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
    os.makedirs(FOLDER, exist_ok=True)
    for name, html in (('ESP25_calculations', calcs_html(n)), ('ESP25_reflective_notes', notes_html(n))):
        h = os.path.join(FOLDER, name + '.html')
        open(h, 'w').write(html)
        to_pdf(h, os.path.join(FOLDER, name + '.pdf'))
        print('wrote', name)
    c, bat, cap = n['costs'], n['battery'], n['capacity']
    key = dict(size=n['size'], mass=n['mass'], parts=n['parts'], compartments=E.N_SEG - 2, pills=cap['total'],
               battery_days=bat['days'], day_mah=bat['day'], motor_sf=n['drive']['sf'], step_s=n['drive']['t_step'],
               self_locking=n['drive']['locking'], catch_hand=n['catch']['total'], catch_sf=n['catch']['sf'], pry=PRY,
               cost_variable=c['variable'], fixed=c['fixed'],
               cases=[dict((k, v) for k, v in x.items()) for x in c['cases']], programme=n['programme'],
               recyclable=n['recycle']['share'], fea=dict((k, n['fea'].get(k)) for k in ('vm_max', 'sf_min', 'disp_max')),
               probes=n['fea'].get('probes', []))
    json.dump(key, open(os.path.join(FOLDER, 'ESP25_calculations.json'), 'w'), indent=1)
    words = len(re.sub('<[^>]+>', ' ', notes_html(n).split('<h1>')[1]).split())
    print('reflective notes words:', words)
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in key.items() if k not in ('probes',)}, indent=0, default=str))
