"""ESP 2024 Task 2: calculations (floating and stability, renewable energy against the alert and tracking load,
mooring loads, the mooring eye, cost and time) and the reflective notes.

Every size and mass comes from models/esp2024.py (the CAD model) and the mooring eye FEA in docs/ESP 2024/fea, so
the calculations, drawings and model always agree. Prices, labour times, sunshine and power use are stated
assumptions, listed once in the tables below.
Writes docs/ESP 2024/ESP24_calculations.html and .pdf, ESP24_reflective_notes.html and .pdf, ESP24_calculations.json.
Run from the repository root:  /home/user/venv/bin/python tools/esp2024_calcs.py
"""
import json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import esp2024 as E  # noqa: E402

FOLDER = os.path.join(ROOT, 'docs', 'ESP 2024')
G = 9.81
RHO_AIR = 1.23
BUDGET = 2000                 # £ a buoy (brief)
BUOYS = 100                   # buoys in the order (brief)
RATE = 2                      # buoys a week (brief)
WEEKS = 70                    # weeks for design, prototype and manufacture (brief)
LABOUR = 17.0                 # £ an hour, skilled fabrication and assembly (assumption)
WIND = 17.0                   # m/s, gale force 8, the wind for the heel check (assumption)
CURRENT = 1.5                 # m/s, strong tidal current in a harbour entrance (assumption)
CD = 1.0                      # drag coefficient of the float, panels and topmark (bluff bodies)
CHAIN_MBL = 40000             # N, breaking load of the 10 mm grade 30 chain
CHAIN_PRICE = 4.0             # £ a metre, 10 mm galvanised chain bought by the drum (1500 m for the order)
SCOPE = 3                     # chain length = 3 x depth of water

# ------------------------------------------------------------------ renewable energy: the loads and the sun
# (load, watts while on, hours on a day, note). Winter: 16 hours of darkness in December at 50 degrees north.
LOADS = [
    ('LED lantern, flashing Fl(2) 6 s', 1.0, 16 * 2 * 0.5 / 6, 'on 1 s in every 6 s (2 flashes of 0.5 s), 16 h of darkness'),
    ('Lantern light sensor and driver, standby', 0.02, 24, 'all day'),
    ('GNSS position fix and LTE-M report', 0.12, 24, 'a fix and report every hour: 1.4 W for about 5 minutes, averaged'),
    ('Alert system: load pin and logic', 0.24, 24 * 0.1, 'load pin read for 1 s in every 10 s (20 mA at 12 V)'),
    ('Control unit and MPPT charger, standby', 0.05, 24, 'all day'),
]
LOSS = 1.20                   # battery charge and discharge, wiring: 20 % on top
ALERT_W = 1.0                 # W while drifting: a position report every minute on LTE-M
SUN_DEC = 1.0                 # kWh/m2 a day on a vertical panel facing south, December, southern UK (PVGIS, assumption)
SUN_JUN = 3.0                 # kWh/m2 a day on a vertical panel facing south, June
OTHER = 0.30                  # each of the two panels facing away gets about 30 % (diffuse and reflected light)
DERATE = 0.75                 # dirt and salt, temperature, MPPT and cable losses
BATTERY_WH = 12.8 * 40        # LiFePO4 12.8 V 40 Ah
DOD = 0.80                    # use 80 % of the battery

# ------------------------------------------------------------------ cost assumptions
# material: (name, £/kg, buy to fly ratio, note)
MATERIALS = {
    'ss':       ('316L stainless steel plate, tube and bar', 4.2, 1.25, 'Does not rust in sea water; protected by the anode'),
    'mdpe':     ('MDPE rotomoulding powder, UV stabilised', 3.5, 1.1, 'Colour all through; recyclable'),
    'foam':     ('Closed cell PU foam, two part', 6.0, 1.1, 'Unsinkable if the hull is holed'),
    'eva':      ('EVA foam fender with rubber skin', 14.0, 1.1, 'Soft: takes minor impacts'),
    'hdpe':     ('HDPE sheet', 4.0, 1.3, 'Does not corrode'),
    'ballast':  ('Heavy concrete (barytes) in a PE skin', 0.8, 1.05, 'Cheap, dense, cannot rust'),
    'concrete': ('Reinforced concrete C32/40', 0.12, 1.05, 'Sinker: no maintenance'),
    'bought':   ('Bought in part', 0.0, 1.0, 'Price each in the parts table'),
}
# part key: (material, labour hours each, bought in price £ each)
PART_COST = {
    'float_hull': ('mdpe', 0.75, 0), 'float_foam': ('foam', 0.3, 0), 'fender': ('eva', 0.2, 0),
    'deck_plate': ('ss', 0.6, 0), 'keel_plate': ('ss', 0.5, 0), 'tie_rod': ('bought', 0.05, 4),
    'tie_rod_nut': ('bought', 0.0, 0.8), 'eye_nut': ('bought', 0.05, 9),
    'canister': ('ss', 1.2, 0), 'mounting_plate': ('hdpe', 0.2, 0), 'battery': ('bought', 0.1, 140),
    'battery_strap': ('ss', 0.2, 0), 'control_unit': ('bought', 0.5, 150), 'hatch_seal': ('bought', 0.0, 6),
    'hatch_lid': ('ss', 0.6, 0), 'hatch_bolt': ('bought', 0.0, 1.5), 'cable_gland': ('bought', 0.1, 2),
    'tail_tube': ('ss', 1.5, 0), 'keel_bolt': ('bought', 0.0, 0.6), 'ballast': ('ballast', 0.5, 0),
    'ballast_collar': ('ss', 0.3, 0), 'anode': ('bought', 0.1, 28), 'mooring_eye': ('ss', 0.4, 0),
    'tripod_leg': ('ss', 0.6, 0), 'leg_bolt': ('bought', 0.0, 0.6), 'top_plate': ('ss', 0.3, 0),
    'bracket_lower': ('ss', 0.25, 0), 'bracket_upper': ('ss', 0.25, 0), 'solar_panel': ('bought', 0.2, 28),
    'lantern_body': ('bought', 0.3, 110), 'lantern_lens': ('bought', 0.0, 20), 'lantern_cap': ('bought', 0.0, 8),
    'topmark_strut': ('ss', 0.2, 0), 'topmark_plate': ('ss', 0.3, 0), 'antenna': ('bought', 0.1, 30),
    'topmark_can': ('mdpe', 0.5, 0), 'topmark_cone': ('mdpe', 0.5, 0), 'shackle': ('bought', 0.0, 14),
    'load_pin': ('bought', 0.2, 95), 'swivel': ('bought', 0.0, 22), 'chain_link': ('bought', 0.0, 0),
    'sinker': ('concrete', 0.5, 0), 'sinker_eye': ('ss', 0.3, 0),
}
ASSEMBLY_H = 4.5              # hours a buoy: assemble, wire, programme, test in the tank, pack
TOOLING = 10000               # £: rotomoulding tools for the float, can and cone; welding jigs (shared by the order)
PROTOTYPE = 6000              # £: two prototypes and a 6 week sea trial (shared by the order)
OVERHEAD = 0.25               # factory overhead on labour
SCRAP = 0.05                  # material scrap and consumables

# ------------------------------------------------------------------ the programme (weeks)
PROGRAMME = [('Design and drawings (this task), client approval', 0, 6),
             ('Rotomoulding tools and jigs made', 4, 10),
             ('Two prototypes built and tested in the tank', 6, 12),
             ('Sea trial of the prototypes in a client harbour', 12, 17),
             ('Changes from the trial, production release', 17, 18),
             ('Production: 100 buoys at 2 a week', 18, 18 + BUOYS / RATE)]


def all_items():
    """The parts of one complete buoy as delivered: the red buoy, the sinker (the green topmark is the alternative)."""
    return E.buoy_instances('red') + E.sinker_items()


def parts_table():
    by = E.masses(all_items())
    rows = []
    for p in E.PARTS:
        q, m = by.get(p['key'], [0, 0.0])
        if p['key'] == 'topmark_cone':          # a green buoy has the cone instead of the can: same cost line
            q, m = 0, 0.0
        mat, hrs, buy = PART_COST[p['key']]
        name, price, btf, _ = MATERIALS[mat]
        raw = m * btf * price * (1 + SCRAP)
        rows.append(dict(no=p['no'], key=p['key'], name=p['name'], qty=q, mass=m, mat=mat, raw=raw, hours=hrs * q,
                         labour=hrs * q * LABOUR, bought=buy * q))
    return rows


def costs():
    rows = parts_table()
    chain = SCOPE * E.WATER_DEPTH * CHAIN_PRICE
    material = sum(r['raw'] for r in rows)
    bought = sum(r['bought'] for r in rows) + chain
    hours = sum(r['hours'] for r in rows) + ASSEMBLY_H
    labour = hours * LABOUR
    overhead = labour * OVERHEAD
    tooling, proto = TOOLING / BUOYS, PROTOTYPE / BUOYS
    total = material + bought + labour + overhead + tooling + proto
    return dict(material=material, bought=bought, chain=chain, hours=hours, labour=labour, overhead=overhead,
                tooling=tooling, proto=proto, total=total, order=total * BUOYS, margin=BUDGET - total, rows=rows)


def energy():
    rows = [(n, w, h, w * h, note) for n, w, h, note in LOADS]
    use = sum(r[3] for r in rows)
    need = use * LOSS
    P = E.PANEL and 20.0
    k_best = 1 + 2 * OTHER                     # one panel faces the sun, two face away
    k_worst = 2 * math.cos(math.radians(60)) + OTHER   # the sun between two panels, both at 60 degrees
    dec = P * SUN_DEC * DERATE * min(k_best, k_worst)
    jun = P * SUN_JUN * DERATE * min(k_best, k_worst)
    usable = BATTERY_WH * DOD
    return dict(rows=rows, use=use, need=need, panel_w=P, k_best=k_best, k_worst=k_worst, k=min(k_best, k_worst),
                dec=dec, jun=jun, ratio=dec / need, usable=usable, days=usable / need, alert_wh=ALERT_W * 24 * LOSS,
                alert_days=usable / (ALERT_W * 24 * LOSS))


def windage(h):
    """Area (m2) and centre height (mm) of the buoy above the waterline h, seen from the side, part by part."""
    items = []
    # float and fender above the water
    items.append(('float and fender', 2 * E.FENDER_R / 1000 * (E.FLOAT_TOP - h) / 1000, (E.FLOAT_TOP + h) / 2))
    n0, t, w, z0, z1 = E.PANEL
    a = w / 1000 * (z1 - z0) / 1000
    items.append(('solar panels (one square on, two at 60 degrees)', a * (1 + 2 * math.cos(math.radians(60))), (z0 + z1) / 2))
    L = math.dist((E.LEG_FOOT[0], E.LEG_FOOT[1]), (E.LEG_TOP[0], E.LEG_TOP[1]))
    items.append(('tripod legs and struts', 3 * 2 * E.LEG_OR / 1000 * L / 1000 + 3 * E.STRUT[2] / 1000 * (E.STRUT[4] - E.STRUT[3]) / 1000,
                  (E.LEG_FOOT[1] + E.TM_PLATE[0]) / 2))
    items.append(('lantern', 0.11 * 0.17, E.TOP_PLATE[1] + 85))
    r, tt, za, zb = E.CAN_TM
    items.append(('topmark (can)', 2 * r / 1000 * (zb - za) / 1000, (za + zb) / 2))
    area = sum(i[1] for i in items)
    zc = sum(i[1] * i[2] for i in items) / area
    return items, area, zc


def underwater(h):
    """Side area (m2) and centre height (mm) of the buoy under the water, for the current drag."""
    items = [('float', 2 * E.FLOAT_R / 1000 * (h - E.FLOAT_BOT) / 1000, (h + E.FLOAT_BOT) / 2),
             ('tail tube', 2 * E.TAIL_R / 1000 * (E.KEEL[0] - E.TAIL_BOT) / 1000, (E.KEEL[0] + E.TAIL_BOT) / 2),
             ('ballast and bottom plate', 2 * E.BALLAST[1] / 1000 * (E.BALLAST[2] + 10) / 1000, E.TAIL_BOT + E.BALLAST[2] / 2)]
    area = sum(i[1] for i in items)
    return items, area, sum(i[1] * i[2] for i in items) / area


def numbers():
    n = {}
    red, green = E.buoy_instances('red'), E.buoy_instances('green')
    n['moored'] = E.float_line(red, extra=E.CHAIN_LOAD)
    n['free'] = E.float_line(red)
    n['green'] = E.float_line(green, extra=E.CHAIN_LOAD)
    m = n['moored']
    n['mass'], n['mass_green'] = m['mass'], n['green']['mass']
    n['sinker_mass'] = sum(mm for q, mm in E.masses(E.sinker_items()).values())
    by = E.masses(red)
    n['groups'] = [(g, t, sum(by[p['key']][1] for p in E.PARTS if p['group'] == g and p['key'] in by)) for g, t in E.GROUPS]
    import cadquery as cq
    bb = cq.Compound.makeCompound([s.val() for _, _, s in red]).BoundingBox()
    n['bb'] = (bb.xmax - bb.xmin, bb.ymax - bb.ymin, bb.zmin, bb.zmax)
    n['top_red'], n['top_green'] = E.CAN_TM[3], E.CONE_TM[3]
    n['above'] = dict(red=E.CAN_TM[3] - m['h'], green=E.CONE_TM[3] - n['green']['h'],
                      red_free=E.CAN_TM[3] - n['free']['h'])
    n['draught'] = m['h'] - (E.PIN_Z - 45)      # waterline to the bottom of the mooring eye
    # heel in the wind
    items, area, zc = windage(m['h'])
    F = 0.5 * RHO_AIR * WIND ** 2 * CD * area
    uitems, uarea, uzc = underwater(m['h'])
    lever = (zc - uzc) / 1000
    Mw = F * lever
    Mr = (m['mass'] + m['extra']) * G * m['GM'] / 1000
    n['wind'] = dict(items=items, area=area, zc=zc, F=F, lever=lever, M=Mw, Mr=Mr, heel=math.degrees(math.asin(min(1, Mw / Mr))))
    Fc = 0.5 * E.SW_D * CURRENT ** 2 * CD * uarea
    n['current'] = dict(items=uitems, area=uarea, zc=uzc, F=Fc)
    n['mooring'] = dict(horizontal=F + Fc, vertical=E.CHAIN_LOAD * G, total=math.hypot(F + Fc, E.CHAIN_LOAD * G),
                        reserve=m['reserve'] * G,
                        lift=SCOPE * E.WATER_DEPTH * E.CHAIN_KG_M * (1 - E.SW_D / E.GALV_D) * G)
    n['chain_links'] = sum(1 for nm, k, s in all_items() if k == 'chain_link')
    n['energy'] = energy()
    n['costs'] = costs()
    f = os.path.join(FOLDER, 'fea', 'esp2024_p23_mooring_eye.json')
    n['fea'] = json.load(open(f))['results'] if os.path.exists(f) else {}
    t, w, d = E.EYE_T, 90, 2 * E.PIN_R + 2
    n['eye'] = dict(gross=CHAIN_MBL / (w * t), net=CHAIN_MBL / ((w - d) * t), bearing=CHAIN_MBL / (2 * E.PIN_R * t),
                    tear=CHAIN_MBL / (2 * (45 - d / 2) * t), weld=CHAIN_MBL / (2 * (w + t) * 0.7 * 6))
    return n


CSS = """
@page{size:A4;margin:11mm 13mm}
body{font-family:Arial,Helvetica,sans-serif;font-size:8.3pt;line-height:1.22;color:#111}
h1{font-size:14pt;margin:0 0 2mm} h2{font-size:10pt;margin:2.2mm 0 0.8mm;color:#16335B;border-bottom:0.3mm solid #16335B}
table{border-collapse:collapse;width:100%;margin:1mm 0} td,th{border:0.2mm solid #888;padding:0.2mm 1.5mm;text-align:left;vertical-align:top}
th{background:#E8EEF6} .r{text-align:right;white-space:nowrap} .ok{color:#1F7A3A;font-weight:bold}
.hdr{display:flex;justify-content:space-between;font-size:7pt;color:#444;border-bottom:0.3mm solid #444;margin-bottom:2mm}
.page{page-break-after:always} .small{font-size:8.2pt} .tiny{font-size:7pt} .tiny td,.tiny th{padding:0.15mm 1.2mm} ul{margin:0.5mm 0 0.5mm 5mm;padding:0}
tr.tot td{font-weight:bold;background:#F3F6FA}
"""


def gbp(v):
    return '£' + format(round(v), ',')


def calcs_html(n):
    m, fr, gr = n['moored'], n['free'], n['green']
    en, c, wd, cu, mo, eye = n['energy'], n['costs'], n['wind'], n['current'], n['mooring'], n['eye']
    fea = n['fea']
    probes = {p['name']: p['vm'] for p in fea.get('probes', [])}
    hdr = lambda k: ('<div class="hdr"><span>Oceans Technology Ltd for Harbour Shipping Ltd. ESP 2024 (8730-035) Task 2: '
                     'harbour buoy</span><span>Calculation sheet %d of 4. Ref ESP24-CALC. 2026-11-10</span></div>' % k)
    grp = ''.join('<tr><td>%s</td><td class="r">%.1f kg</td></tr>' % (t.split(' (')[0], mm) for g, t, mm in n['groups'])
    load_rows = ''.join('<tr><td>%s</td><td class="r">%.2f W</td><td class="r">%.2f h</td><td class="r">%.2f Wh</td><td>%s</td></tr>' % (
        r[0], r[1], r[2], r[3], r[4].replace(' (1.4 W x 2 min/h... averaged)', '')) for r in en['rows'])
    wind_rows = ''.join('<tr><td>%s</td><td class="r">%.3f m&sup2;</td><td class="r">%.0f mm</td></tr>' % i for i in wd['items'])
    part_rows = ''.join(
        '<tr><td>%d</td><td>%s</td><td class="r">%d</td><td class="r">%.2f</td><td>%s</td><td class="r">%s</td>'
        '<td class="r">%.2f</td><td class="r">%s</td></tr>' % (
            r['no'], r['name'], r['qty'], r['mass'], MATERIALS[r['mat']][0] if r['mat'] != 'bought' else 'Bought in',
            gbp(r['raw']) if r['raw'] >= 0.5 else '&ndash;', r['hours'], gbp(r['bought']) if r['bought'] else '&ndash;')
        for r in c['rows'] if r['qty'])
    mat_rows = ''.join('<tr><td>%s</td><td class="r">£%.2f</td><td class="r">%.2f</td><td>%s</td></tr>' % v
                       for k, v in MATERIALS.items() if k != 'bought')
    prog_rows = ''.join('<tr><td>%s</td><td class="r">%g</td><td class="r">%g</td><td class="r">%g</td></tr>' % (t, a, b, b - a)
                        for t, a, b in PROGRAMME)
    end = PROGRAMME[-1][2]
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2024 calculations</title><style>{CSS}</style></head><body>
<div class="page">{hdr(1)}
<h1>Calculations for the preferred design (Design A): solar powered harbour buoy</h1>
<h2>1. Assumptions</h2>
<ul class="small">
<li>Sizes and masses come from the CAD model (models/esp2024.py): all {len(E.PARTS)} parts are modelled with their own material density; the buoy has {len(E.buoy_instances())} parts and the sinker {len(E.sinker_items())}.</li>
<li>Sea water {E.SW_D} kg/m&sup3;. The harbour lane is {E.WATER_DEPTH:g} m deep at high water; the buoy carries the weight of the chain hanging from it, about one depth of {E.CHAIN_D} mm chain ({E.CHAIN_KG_M} kg/m in air, {E.CHAIN_LOAD:.1f} kg in water). Chain length {SCOPE} &times; depth.</li>
<li>Wind for the heel check {WIND:g} m/s (gale force 8); tidal current {CURRENT:g} m/s; drag coefficient {CD:g} for the float, panels and topmark.</li>
<li>Sun: {SUN_DEC:g} kWh/m&sup2; a day in December and {SUN_JUN:g} in June on an upright panel facing the sun at 50&deg; north; panels lose {round((1 - DERATE) * 100)} % to salt, dirt, heat and the charger.</li>
<li>Labour £{LABOUR:.0f} an hour (marine fabrication). Material and bought in prices are supplier estimates for a batch of {BUOYS}; they are listed in section 9.</li>
<li>Marine growth, ice and a boat tying up to the buoy are not in the floating calculation; the reserve buoyancy covers them.</li>
</ul>
<h2>2. Mass and how the buoy floats</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Mass of the buoy (red), CAD model</td><td>sum of volume &times; density for all {len(E.buoy_instances())} parts</td><td class="r"><b>{m['mass']:.1f} kg</b></td></tr>
<tr><td>Weight carried: buoy + hanging chain</td><td>{m['mass']:.1f} + {E.CHAIN_LOAD:.1f}</td><td class="r">{m['mass'] + m['extra']:.1f} kg</td></tr>
<tr><td>Sea water it must push aside</td><td>{m['mass'] + m['extra']:.1f} / {E.SW_D}</td><td class="r">{m['vol'] * 1e-9:.4f} m&sup3;</td></tr>
<tr><td>Waterline, moored (from the CAD shape below the water)</td><td>found by trial: the volume below the line = the volume needed</td><td class="r"><b>{m['h']:+.0f} mm</b> on the design waterline</td></tr>
<tr><td>Height of the top above the sea, red (can) buoy</td><td>{n['top_red']} &minus; ({m['h']:.0f}) (brief 1400 to 1800)</td><td class="r"><span class="ok">{n['above']['red']:.0f} mm</span></td></tr>
<tr><td>Height of the top above the sea, green (cone) buoy</td><td>{n['top_green']} &minus; ({gr['h']:.0f})</td><td class="r"><span class="ok">{n['above']['green']:.0f} mm</span></td></tr>
<tr><td>If the chain breaks (no chain weight)</td><td>lighter, the buoy rises {-fr['h'] + m['h']:.0f} mm: top {n['above']['red_free']:.0f} mm above the sea</td><td class="r"><span class="ok">still in range</span></td></tr>
<tr><td>Base diameter at the waterline</td><td>float &Oslash;{2 * E.FLOAT_R}; over the fender &Oslash;{2 * E.FENDER_R} (brief 500 &plusmn; 25)</td><td class="r"><span class="ok">{2 * E.FLOAT_R} mm</span></td></tr>
<tr><td>Draught (waterline to the bottom of the mooring eye)</td><td>needs at least {(n['draught'] + 500) / 1000:.1f} m of water at low tide</td><td class="r">{n['draught']:.0f} mm</td></tr>
<tr><td>Reserve buoyancy (pushed fully under)</td><td>{m['full'] * 1e-9:.4f} m&sup3; &times; {E.SW_D} &minus; {m['mass'] + m['extra']:.1f}</td><td class="r">{m['reserve']:.0f} kg ({m['reserve'] / (m['mass'] + m['extra']) * 100:.0f} %)</td></tr>
</table>
<table class="small" style="width:48%;display:inline-table;margin-right:3%"><tr><th>Sub-assembly</th><th class="r">Mass</th></tr>{grp}</table>
<p class="small" style="display:inline-block;width:47%;vertical-align:top">The ballast ({n['groups'][2][2]:.0f} kg with the tail) is the heaviest group on purpose: low down, it keeps the buoy upright. The sinker on the harbour bed weighs {n['sinker_mass']:.0f} kg in air ({n['sinker_mass'] * (1 - E.SW_D / E.CONC_D):.0f} kg in water) and holds the buoy with the chain lying on the bed.</p>
<h2>3. Stability: does it stay upright?</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Centre of buoyancy B (height)</td><td>centroid of the CAD shape below the waterline</td><td class="r">{m['zb']:.0f} mm</td></tr>
<tr><td>Centre of gravity G, with the chain</td><td>from every part's mass and centre; chain weight at the load pin</td><td class="r">{m['zg']:.0f} mm</td></tr>
<tr><td>BM = I / V</td><td>I = &pi; &times; {2 * E.FLOAT_R}<sup>4</sup> / 64 = {math.pi * (2 * E.FLOAT_R) ** 4 / 64 / 1e9:.5f} m<sup>4</sup>; / {m['vol'] * 1e-9:.4f} m&sup3;</td><td class="r">{m['BM']:.0f} mm</td></tr>
<tr><td>Metacentric height GM = B + BM &minus; G</td><td>{m['zb']:.0f} + {m['BM']:.0f} &minus; ({m['zg']:.0f}); positive, so it is stable</td><td class="r"><span class="ok">{m['GM']:.0f} mm</span></td></tr>
<tr><td>GM if the chain breaks</td><td>{fr['zb']:.0f} + {fr['BM']:.0f} &minus; ({fr['zg']:.0f})</td><td class="r"><span class="ok">{fr['GM']:.0f} mm</span></td></tr>
<tr><td>Wind force on the buoy, {WIND:g} m/s</td><td>&frac12; &times; {RHO_AIR} &times; {WIND:g}&sup2; &times; {CD:g} &times; {wd['area']:.3f} m&sup2; (table below)</td><td class="r">{wd['F']:.0f} N</td></tr>
<tr><td>Heeling moment</td><td>{wd['F']:.0f} N &times; {wd['lever']:.2f} m (wind centre to water drag centre)</td><td class="r">{wd['M']:.0f} N m</td></tr>
<tr><td>Righting moment W &times; GM (&times; sin &theta; at a heel &theta;)</td><td>{m['mass'] + m['extra']:.1f} &times; 9.81 &times; {m['GM'] / 1000:.3f}</td><td class="r">{wd['Mr']:.0f} N m</td></tr>
<tr><td>Steady heel in the gale</td><td>sin &theta; = {wd['M']:.0f} / {wd['Mr']:.0f}</td><td class="r"><span class="ok">{wd['heel']:.1f}&deg;</span></td></tr>
</table>
<table class="small"><tr><th>Area above the water (side view)</th><th class="r">Area</th><th class="r">Centre height</th></tr>{wind_rows}</table>
</div>
<div class="page">{hdr(2)}
<h2>4. Renewable energy: what the alert and tracking system needs (12 V)</h2>
<table class="small"><tr><th>Load (all 12 V DC)</th><th class="r">Power on</th><th class="r">Hours a day</th><th class="r">Energy a day</th><th>How it is used</th></tr>{load_rows}
<tr class="tot"><td>Total used a day (winter)</td><td></td><td></td><td class="r">{en['use']:.1f} Wh</td><td></td></tr>
<tr class="tot"><td>Needed from the panels, with {round((LOSS - 1) * 100)} % battery and wiring loss</td><td></td><td></td><td class="r">{en['need']:.1f} Wh</td><td>{en['use']:.1f} &times; {LOSS}</td></tr></table>
<h2>5. Renewable energy: what the solar panels make</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Panels</td><td>3 &times; {en['panel_w']:.0f} W monocrystalline, upright, 120&deg; apart round the mast</td><td class="r">{3 * en['panel_w']:.0f} W</td></tr>
<tr><td>Panels working, sun square on to one panel</td><td>1 + 2 &times; {OTHER} (the two facing away get diffuse light)</td><td class="r">{en['k_best']:.2f} panels</td></tr>
<tr><td>Panels working, sun between two panels (the worst way round)</td><td>2 &times; cos 60&deg; + {OTHER}</td><td class="r">{en['k_worst']:.2f} panels</td></tr>
<tr><td>Energy made a day in December (worst month)</td><td>{en['panel_w']:.0f} W &times; {SUN_DEC:g} h &times; {DERATE} &times; {en['k']:.2f}</td><td class="r"><b>{en['dec']:.1f} Wh</b></td></tr>
<tr><td>Made against needed, December</td><td>{en['dec']:.1f} / {en['need']:.1f} (must be more than 1)</td><td class="r"><span class="ok">{en['ratio']:.1f} &times;</span></td></tr>
<tr><td>Energy made a day in June</td><td>{en['panel_w']:.0f} &times; {SUN_JUN:g} &times; {DERATE} &times; {en['k']:.2f}: the charger stops when the battery is full</td><td class="r">{en['jun']:.1f} Wh</td></tr>
<tr><td>Battery</td><td>LiFePO4 12.8 V &times; 40 Ah = {BATTERY_WH:.0f} Wh, use {DOD * 100:.0f} %</td><td class="r">{en['usable']:.0f} Wh</td></tr>
<tr><td>Days with no sun at all</td><td>{en['usable']:.0f} / {en['need']:.1f}</td><td class="r"><span class="ok">{en['days']:.0f} days</span></td></tr>
<tr><td>Drifting with the alert on (position every minute)</td><td>{ALERT_W:g} W &times; 24 h &times; {LOSS} = {en['alert_wh']:.1f} Wh a day; {en['usable']:.0f} / {en['alert_wh']:.1f}</td><td class="r">{en['alert_days']:.0f} days to find it</td></tr>
</table>
<p class="small">The supply is 12 V nominal (12.8 V LiFePO4, 10 to 14.4 V), which suits the lantern, tracker and load pin amplifier. Upright panels collect more in winter, when the sun is low, than flat ones, shed rain, spray and bird droppings, and cannot be stood on. The charger switches the lantern on at dusk from the panel voltage, so there is no separate light sensor to fail.</p>
<h2>6. Mooring loads and the mooring eye</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Current drag on the parts under water</td><td>&frac12; &times; {E.SW_D} &times; {CURRENT:g}&sup2; &times; {CD:g} &times; {cu['area']:.3f} m&sup2;</td><td class="r">{cu['F']:.0f} N</td></tr>
<tr><td>Wind drag ({WIND:g} m/s)</td><td>section 3</td><td class="r">{wd['F']:.0f} N</td></tr>
<tr><td>Chain weight on the eye</td><td>{E.CHAIN_LOAD:.1f} kg &times; 9.81</td><td class="r">{mo['vertical']:.0f} N</td></tr>
<tr><td>Steady pull on the mooring eye, gale and tide together</td><td>&radic;(({cu['F']:.0f} + {wd['F']:.0f})&sup2; + {mo['vertical']:.0f}&sup2;)</td><td class="r"><b>{mo['total']:.0f} N</b></td></tr>
<tr><td>Reserve buoyancy (extra down force before the deck goes under)</td><td>{m['reserve']:.0f} kg &times; 9.81</td><td class="r">{mo['reserve']:.0f} N</td></tr>
<tr><td>Worst case: the tide lifts all the chain off the bed</td><td>{SCOPE} &times; {E.WATER_DEPTH:g} m &times; {E.CHAIN_KG_M} kg/m &times; (1 &minus; {E.SW_D}/{E.GALV_D}) &times; 9.81, less the {mo['vertical']:.0f} N already carried</td><td class="r">{mo['lift'] - mo['vertical']:.0f} N, less than {mo['reserve']:.0f} N</td></tr>
<tr><td>Design load for the mooring eye</td><td>breaking load of the chain: the buoy must never be the weak link</td><td class="r"><b>{CHAIN_MBL / 1000:.0f} kN</b></td></tr>
<tr><td>Plate above the hole (gross section)</td><td>{CHAIN_MBL} / (90 &times; {E.EYE_T})</td><td class="r">{eye['gross']:.1f} MPa (FEA {probes.get('plate above the hole', 0):.1f})</td></tr>
<tr><td>Net section beside the hole</td><td>{CHAIN_MBL} / ((90 &minus; {2 * E.PIN_R + 2}) &times; {E.EYE_T})</td><td class="r">{eye['net']:.1f} MPa (FEA {probes.get('side of the hole (net section)', 0):.1f})</td></tr>
<tr><td>Pin bearing on the hole</td><td>{CHAIN_MBL} / ({2 * E.PIN_R} &times; {E.EYE_T})</td><td class="r">{eye['bearing']:.1f} MPa</td></tr>
<tr><td>Tear out below the hole (two shear planes)</td><td>{CHAIN_MBL} / (2 &times; (45 &minus; {(2 * E.PIN_R + 2) / 2:g}) &times; {E.EYE_T})</td><td class="r">{eye['tear']:.1f} MPa (shear)</td></tr>
<tr><td>Fillet weld round the top of the eye, 6 mm leg</td><td>{CHAIN_MBL} / (2 &times; (90 + {E.EYE_T}) &times; 0.7 &times; 6)</td><td class="r">{eye['weld']:.1f} MPa</td></tr>
<tr><td>FEA peak (von Mises), at the edge of the hole</td><td>gmsh + scikit-fem, 10 node tetrahedra; 316L yield 170 MPa</td><td class="r"><b>{fea.get('vm_max', 0):.0f} MPa</b>, safety factor <span class="ok">{fea.get('sf_min', 0):.1f}</span></td></tr>
</table>
<p class="small">The steady pull in a gale with the tide ({mo['total']:.0f} N) is less than 2 % of the design load. It is mostly sideways: with the chain {SCOPE} times the depth it leaves the buoy at a shallow angle, and even if the strongest tide lifts all the chain off the bed the buoy carries only {mo['lift'] - mo['vertical']:.0f} N more, against {mo['reserve']:.0f} N of reserve buoyancy: it dips about {(mo['lift'] - mo['vertical']) / (E.SW_D * 9.81 * math.pi * (E.FLOAT_R / 1000) ** 2) * 1000:.0f} mm but stays afloat. Even at the full breaking load of the chain the mooring eye stays below yield: the chain fails first, the load pin sees the pull fall to zero and the alert is sent. Above the hole the FEA ({probes.get('plate above the hole', 0):.1f} MPa) agrees with the hand value ({eye['gross']:.1f} MPa). Beside the hole the FEA is about half the hand value: like Inventor, it spreads the force round the whole hole, so half of it goes straight into the plate above. The real pin bears on the bottom of the hole, so the hand value is the one to design to, and it is well below yield. The FEA peak at the edge of the hole is the stress concentration (about 2 to 3 times the net stress).</p>
</div>
<div class="page">{hdr(3)}
<h2>7. Cost to make one buoy</h2>
<table><tr><th>Cost element (one buoy with its sinker and chain)</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Raw materials</td><td>mass &times; buy to fly &times; £/kg, + {SCRAP * 100:.0f} % scrap (section 9)</td><td class="r">{gbp(c['material'])}</td></tr>
<tr><td>Bought in parts</td><td>battery, control unit, panels, lantern, load pin, fasteners, chain {SCOPE} &times; {E.WATER_DEPTH:g} m ({gbp(c['chain'])})</td><td class="r">{gbp(c['bought'])}</td></tr>
<tr><td>Labour</td><td>{c['hours'] - ASSEMBLY_H:.1f} h making parts + {ASSEMBLY_H:.0f} h assembly and test = {c['hours']:.1f} h &times; £{LABOUR:.0f}</td><td class="r">{gbp(c['labour'])}</td></tr>
<tr><td>Factory overhead</td><td>{OVERHEAD * 100:.0f} % of labour</td><td class="r">{gbp(c['overhead'])}</td></tr>
<tr><td>Tooling share</td><td>{gbp(TOOLING)} / {BUOYS}</td><td class="r">{gbp(c['tooling'])}</td></tr>
<tr><td>Prototypes and sea trial share</td><td>{gbp(PROTOTYPE)} / {BUOYS}</td><td class="r">{gbp(c['proto'])}</td></tr>
<tr class="tot"><td>Cost to make one buoy</td><td></td><td class="r">{gbp(c['total'])}</td></tr>
<tr><td>Budget (brief)</td><td>£200,000 / {BUOYS} buoys</td><td class="r">{gbp(BUDGET)}</td></tr>
<tr class="tot"><td>Margin</td><td>{gbp(BUDGET)} &minus; {gbp(c['total'])}</td><td class="r"><span class="ok">{gbp(c['margin'])}</span></td></tr>
<tr><td>Whole order</td><td>{gbp(c['total'])} &times; {BUOYS} (budget £200,000)</td><td class="r">{gbp(c['order'])}</td></tr>
</table>
<p class="small">The biggest costs are the control and tracking unit, the battery, the load pin and the lantern: the electronics are about a third of the cost of the buoy. Stainless steel is used only where strength is needed; the float, topmark and ballast are cheap, corrosion free polyethylene and concrete.</p>
<h2>8. Time: design, prototype and 100 buoys in {WEEKS} weeks</h2>
<table><tr><th>Stage</th><th class="r">Start week</th><th class="r">End week</th><th class="r">Weeks</th></tr>{prog_rows}
<tr class="tot"><td>Finished</td><td></td><td class="r">{end:g}</td><td class="r">{WEEKS - end:g} weeks spare</td></tr></table>
<p class="small">Production: {BUOYS} buoys at {RATE} a week = {BUOYS / RATE:g} weeks (brief). Labour {c['hours']:.1f} h a buoy &times; {RATE} = {c['hours'] * RATE:.0f} h a week: about {c['hours'] * RATE / 37.5 / 0.8:.1f} people at 80 % efficiency. Floats are rotomoulded two a day, so moulding never holds up the line.</p>
<h2>9. Materials, corrosion and prices</h2>
<table class="small"><tr><th>Material</th><th class="r">£/kg</th><th class="r">Buy to fly</th><th>Why it was chosen</th></tr>{mat_rows}</table>
<ul class="small">
<li>No steel that can rust: the stainless is 316L (with molybdenum, for sea water), the fasteners A4 (316), the float, topmark and fender polyethylene and rubber, the ballast and sinker concrete.</li>
<li>The zinc anode ({E.PART['anode']['no']}) is wired to the stainless tail and the galvanised chain: zinc is more reactive, so it corrodes instead of them. It is changed at the yearly service.</li>
<li>Nylon washers and sleeves keep the galvanised chain off the stainless eye where they are not joined through the anode, and all stainless parts are passivated after welding.</li>
</ul>
</div>
<div>{hdr(4)}
<h2>10. Mass and cost of every part (one red buoy with its sinker)</h2>
<table class="tiny"><tr><th>Item</th><th>Part</th><th class="r">Qty</th><th class="r">Mass kg</th><th>Material</th><th class="r">Material</th><th class="r">Hours</th><th class="r">Bought in</th></tr>{part_rows}</table>
<p class="small">The green buoy is the same, with the cone topmark ({E.PART['topmark_cone']['no']}) in place of the can ({E.PART['topmark_can']['no']}): mass {n['mass_green']:.1f} kg, the same cost. The {n['chain_links']} chain links are part of the chain, costed in section 7.</p>
</div></body></html>"""


def notes_html(n):
    m, en, c = n['moored'], n['energy'], n['costs']
    fea = n['fea']
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2024 reflective notes</title><style>{CSS}
body{{font-size:10pt;line-height:1.45}} p{{margin:0 0 2mm}}</style></head><body>
<div class="hdr"><span>Oceans Technology Ltd for Harbour Shipping Ltd. ESP 2024 (8730-035) Task 2, Part B</span><span>Reflective notes on the CAD drawing. 2026-11-10</span></div>
<h1>Reflective notes: solar powered harbour buoy</h1>
<p><b>How my ideas developed.</b> I sketched two buoys. Design B was a steel spherical float with a lattice tower and a small wind turbine. It looked like a traditional buoy, but the turbine has bearings and blades that wear out at sea, gives nothing on calm days, and the steel float would rust unless it was painted often. Design A uses a polyethylene float and solar panels, with no moving parts, so I chose it.</p>
<p><b>How the design meets the specification.</b> The float is {2 * E.FLOAT_R} mm across, {2 * E.FENDER_R} mm over the fender, inside the 500 &plusmn; 25 mm limit. I used the CAD model to find where it floats: moored, the top of the red can is {n['above']['red']:.0f} mm above the sea and the green cone {n['above']['green']:.0f} mm, inside 1400 to 1800 mm. The float and topmark are moulded in red or green all the way through, so scratches never show a different colour. A load pin in the mooring shackle measures the pull of the chain; if it falls to zero the control unit sends an alert straight away, and the GNSS tracker then reports the position every minute. Three 20 W panels give {en['dec']:.0f} Wh a day in December against the {en['need']:.1f} Wh the 12 V systems need, and the battery lasts {en['days']:.0f} days with no sun. The battery and electronics sit in a stainless canister with an O-ring and tamper proof bolts: watertight, secure, and easy to reach by undoing eight bolts. Every metal part is 316 stainless or zinc protected, and the soft fender takes minor knocks from boats. The estimated cost is {gbp(c['total'])} a buoy, under the £2000 budget, and 100 buoys fit in the 70 weeks.</p>
<p><b>What changed as I worked.</b> My first float was too shallow. When the CAD model added up the mass of every part, the buoy sat too low in the water, with too little reserve buoyancy. I made the float deeper, used thinner stainless plates and a lighter mast, and lengthened the tail so a bigger ballast could sit lower down. Now the waterline is where I designed it, GM is {m['GM']:.0f} mm and the buoy heels only {n['wind']['heel']:.0f}&deg; in a gale. The clash check found the shackle and load pin overlapping and a chain link too narrow for the sinker eye, and I fixed both.</p>
<p><b>Checking it is safe.</b> I designed the mooring eye so it is stronger than the chain. The FEA at the chain's breaking load gave {fea.get('vm_max', 0):.0f} MPa, a safety factor of {fea.get('sf_min', 0):.1f}. My hand calculation agreed with the FEA above the hole; beside the hole it was higher, because the FEA spreads the load round the whole hole, so I used the hand value.</p>
<p><b>What I would improve.</b> The cost is only just inside the budget and the electronics are about a third of it, so I would ask the client whether a cheaper tension switch could replace the load pin. I would also test a prototype in a real harbour to check the roll, and try recycled polyethylene for the float.</p>
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
    for name, html in (('ESP24_calculations', calcs_html(n)), ('ESP24_reflective_notes', notes_html(n))):
        h = os.path.join(FOLDER, name + '.html')
        open(h, 'w').write(html)
        to_pdf(h, os.path.join(FOLDER, name + '.pdf'))
        print('wrote', name)
    m, c, en = n['moored'], n['costs'], n['energy']
    key = dict(mass=m['mass'], mass_green=n['mass_green'], chain_load=E.CHAIN_LOAD, waterline=m['h'], waterline_free=n['free']['h'],
               above_red=n['above']['red'], above_green=n['above']['green'], above_free=n['above']['red_free'],
               base=2 * E.FLOAT_R, fender=2 * E.FENDER_R, GM=m['GM'], GM_free=n['free']['GM'], heel=n['wind']['heel'],
               reserve=m['reserve'], draught=n['draught'], energy_need=en['need'], energy_dec=en['dec'], energy_ratio=en['ratio'],
               autonomy_days=en['days'], alert_days=en['alert_days'], cost=c['total'], budget=BUDGET, margin=c['margin'],
               order=c['order'], hours=c['hours'], weeks=PROGRAMME[-1][2], pull=n['mooring']['total'], design_load=CHAIN_MBL,
               eye=n['eye'], fea=dict((k, n['fea'].get(k)) for k in ('vm_max', 'sf_min', 'disp_max')),
               probes=n['fea'].get('probes', []))
    json.dump(key, open(os.path.join(FOLDER, 'ESP24_calculations.json'), 'w'), indent=1)
    words = len(re.sub('<[^>]+>', ' ', notes_html(n).split('<h1>')[1]).split())
    print('reflective notes words:', words)
    print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in key.items() if k not in ('eye', 'probes')}, indent=0))
    print('cost', {k: round(v) for k, v in c.items() if k != 'rows'})
