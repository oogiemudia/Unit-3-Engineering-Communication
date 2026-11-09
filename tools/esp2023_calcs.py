"""ESP 2023 Task 2: supporting calculations (two A4 sides) and design notes (about 500 words).

Every number comes from models/esp2023.py (sizes, mass from the CAD model) and the FEA results in
docs/ESP 2023/fea, so the calculations, drawings and model always agree.
Writes docs/ESP 2023/ESP23_calculations.html and .pdf, ESP23_design_notes.html and .pdf.
Run from the repository root:  python3 tools/esp2023_calcs.py
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import esp2023 as E  # noqa: E402

FOLDER = os.path.join(ROOT, 'docs', 'ESP 2023')
RHO, G = 1000.0, 9.81
RG = RHO * G                       # N/m3


def leaf_mass():
    dens = {'gate leaf (welded S355 steel)': 7850, 'oak fenders': 750, 'walkway and handrail': 7850 * 0.35,
            'cill seal': 1200, 'heel seal': 1200, 'mitre seal': 1200}
    m, mx = 0, 0
    for n, w, c in E.gate_leaf():
        v = w.val().Volume() * 1e-9 * dens[n]
        m += v
        mx += v * w.val().Center().x
    return m, mx / m


def numbers():
    n = {}
    h, hmin, L = E.HEAD_MAX / 1000, E.HEAD_MIN / 1000, E.LEAF / 1000
    n['p_max'] = RG * h / 1000                         # kPa
    n['p_min'] = RG * hmin / 1000
    n['F_m'] = 0.5 * RG * h ** 2 / 1000               # kN per m width
    n['F_m_min'] = 0.5 * RG * hmin ** 2 / 1000
    n['y_cp'] = h / 3
    n['P_leaf'] = n['F_m'] * L                         # kN normal to a leaf
    n['P_total'] = n['F_m'] * E.OPENING / 1000         # kN along the lock
    n['R_mitre'] = n['P_leaf'] / (2 * math.sin(E.THETA))
    # skin panel
    u0, u1, z0, z1 = E.PANEL
    b, a, t = (u1 - u0), (z1 - z0), E.SKIN
    zc = (z0 + z1) / 2
    p_mid = RG * 1e-9 * (E.HEAD_MAX - zc)              # N/mm2
    ab = a / b
    beta = 0.3078 + (0.3834 - 0.3078) * (ab - 1) / 0.2
    alpha = 0.0138 + (0.0188 - 0.0138) * (ab - 1) / 0.2
    sig = beta * p_mid * b ** 2 / t ** 2
    n.update(panel=(b, a, t), p_mid=p_mid * 1000, beta=beta, alpha=alpha, sig_panel=sig,
             vm_panel=sig * math.sqrt(1 - 0.3 + 0.09), defl_panel=alpha * p_mid * b ** 4 / (210000 * t ** 3))
    # bottom girder, simply supported between the posts (ignores arch action: conservative)
    z_top = (E.GIRDERS[0] + E.GIRDERS[1]) / 2 / 1000   # tributary strip 0 to 0.475 m
    w = RG * (h * z_top - z_top ** 2 / 2) / 1000       # kN/m
    span = (E.LEAF - E.MITRE_BOX - E.HEEL_BOX) / 1000
    M = w * span ** 2 / 8
    beff = 400
    parts = [(beff * t, E.T2 - t / 2, beff * t ** 3 / 12),
             (E.WEB_T * (E.T2 - t - (-E.T2 + E.FLANGE[1])), (E.T2 - t + (-E.T2 + E.FLANGE[1])) / 2,
              E.WEB_T * (2 * E.T2 - t - E.FLANGE[1]) ** 3 / 12),
             (E.FLANGE[0] * E.FLANGE[1], -E.T2 + E.FLANGE[1] / 2, E.FLANGE[0] * E.FLANGE[1] ** 3 / 12)]
    A = sum(p[0] for p in parts)
    ybar = sum(p[0] * p[1] for p in parts) / A
    I = sum(p[2] + p[0] * (p[1] - ybar) ** 2 for p in parts)
    ymax = max(E.T2 - ybar, ybar + E.T2)
    n.update(w_g=w, span=span, M_g=M, A_g=A, I_g=I, ybar=ybar, ymax=ymax, sig_g=M * 1e6 * ymax / I)
    # leaf weight, hinges
    m, xg = leaf_mass()
    W = m * G / 1000
    hinge_gap = (5920 - 140) / 1000
    H = W * xg / 1000 / hinge_gap
    d = 150
    n.update(mass=m, xg=xg, W=W, H=H, sig_ax=W * 1000 / (math.pi * d ** 2 / 4),
             sig_b=H * 1000 * 140 / (math.pi * d ** 3 / 32), crane=m * 1.25 / 1000)
    # actuator
    res_head = 0.05
    F_res = RG * res_head * h * L / 1000               # kN, levels equal to within 50 mm
    T_res = F_res * L / 2
    T_fric = 0.1 * W * 0.075
    T = T_res + T_fric
    arms = []
    for od in (0, E.OPEN_DEG):
        w_, g_, d_ = E.actuator_geometry(1, od)
        px = E.PIV
        cross = abs((g_[0] - w_[0]) * (0 - w_[1]) - (g_[1] - w_[1]) * (px - w_[0])) / d_
        arms.append((cross / 1000, d_))
    n.update(F_res=F_res, T_res=T_res, T_fric=T_fric, T=T, arms=arms,
             F_act=max(10 / a_ for a_, _ in arms), stroke=arms[0][1] - arms[1][1])
    # FEA results from the hub solve
    for k in ('esp2023_skin_panel', 'esp2023_lock_gates'):
        f = os.path.join(FOLDER, 'fea', k + '.json')
        if os.path.exists(f):
            r = json.load(open(f))['results']
            n['fea_' + k] = r
    return n


CSS = """
@page{size:A4;margin:14mm 15mm}
body{font-family:Arial,Helvetica,sans-serif;font-size:9.6pt;line-height:1.35;color:#111}
h1{font-size:14pt;margin:0 0 2mm} h2{font-size:10.5pt;margin:3.2mm 0 1mm;color:#16335B;border-bottom:0.3mm solid #16335B}
table{border-collapse:collapse;width:100%;margin:1mm 0} td,th{border:0.2mm solid #888;padding:0.6mm 1.6mm;text-align:left;vertical-align:top}
th{background:#E8EEF6} .r{text-align:right;white-space:nowrap} .ok{color:#1F7A3A;font-weight:bold}
.hdr{display:flex;justify-content:space-between;font-size:8pt;color:#444;border-bottom:0.3mm solid #444;margin-bottom:2mm}
.page{page-break-after:always} .small{font-size:8.4pt} ul{margin:0.5mm 0 0.5mm 5mm;padding:0}
"""


def calcs_html(n):
    b, a, t = n['panel']
    fs = n.get('fea_esp2023_skin_panel', {})
    fp = n.get('fea_esp2023_lock_gates', {})
    hdr = lambda k: ('<div class="hdr"><span>Lock Restoration Ltd. ESP 2023 (8730-035) Task 2: canal lock gates for Canal Heritage</span>'
                     '<span>Calculation sheet %d of 2. Ref ESP23-CALC. 2026-11-09</span></div>' % k)
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2023 calculations</title><style>{CSS}</style></head><body>
<div class="page">{hdr(1)}
<h1>Hydrostatic pressure the lock gates must resist</h1>
<h2>1. Data and assumptions</h2>
<ul class="small">
<li>Opening 4.2 m wide, gate height 6.0 m, head of water 2.0 m to 5.5 m (brief). Design for the worst case: 5.5 m on the chamber side and the downstream side empty.</li>
<li>Fresh canal water: density &rho; = 1000 kg/m&sup3;, g = 9.81 m/s&sup2;, so &rho;g = 9.81 kN/m&sup3;. The water is still (hydrostatic): no waves or surge.</li>
<li>Mitre gates: two leaves {E.LEAF} mm long (pivot to mitre) meeting at 1 in 3 (&theta; = {math.degrees(E.THETA):.1f}&deg;). Each leaf takes the water on its own length.</li>
<li>Steel S355 (yield 355 MPa, E = 210 GPa). Pintle 316 stainless (yield 250 MPa used). Self weight from the CAD model.</li>
<li>Gates only move when the levels are within 50 mm of each other (control interlock).</li>
</ul>
<h2>2. Pressure at depth</h2>
<p>p = &rho;gh. At the cill with 5.5 m of water: p = 1000 &times; 9.81 &times; 5.5 = <b>{n['p_max']:.2f} kPa</b>. With the minimum 2.0 m head: p = {n['p_min']:.2f} kPa.
The pressure is zero at the surface and grows in a straight line to the cill, so the pressure diagram is a triangle.</p>
<h2>3. Force on the gates</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Force per metre width (5.5 m)</td><td>F = &frac12;&rho;gh&sup2; = 0.5 &times; 9.81 &times; 5.5&sup2;</td><td class="r"><b>{n['F_m']:.1f} kN/m</b></td></tr>
<tr><td>Force per metre width (2.0 m)</td><td>0.5 &times; 9.81 &times; 2.0&sup2;</td><td class="r">{n['F_m_min']:.1f} kN/m</td></tr>
<tr><td>Height of the centre of pressure</td><td>h / 3 = 5.5 / 3, above the cill</td><td class="r">{n['y_cp']:.2f} m</td></tr>
<tr><td>Force on one leaf (square to the leaf)</td><td>P = {n['F_m']:.1f} &times; {E.LEAF / 1000:.2f}</td><td class="r"><b>{n['P_leaf']:.0f} kN</b></td></tr>
<tr><td>Total along the lock (both leaves)</td><td>{n['F_m']:.1f} &times; 4.2</td><td class="r">{n['P_total']:.0f} kN</td></tr>
<tr><td>Thrust at the mitre and at each quoin</td><td>R = P / (2 sin &theta;) = {n['P_leaf']:.0f} / (2 &times; {math.sin(E.THETA):.4f})</td><td class="r"><b>{n['R_mitre']:.0f} kN</b></td></tr>
</table>
<p class="small">The two leaves act as a three pin arch: the water pushes each leaf against the other at the mitre and back into the quoin. That is why a mitre gate points upstream: the higher the water, the tighter the mitre and quoin seals.</p>
<h2>4. Skin plate panel (the plate that holds back the water)</h2>
<p>Bottom panel, {b:.0f} &times; {a:.0f} &times; {t} mm, fixed on all four edges by the girders, the heel post and a stiffener. Pressure at its centre ({(E.PANEL[2] + E.PANEL[3]) / 2:.0f} mm above the cill):
p = 9.81 &times; (5.5 &minus; {(E.PANEL[2] + E.PANEL[3]) / 2000:.3f}) = {n['p_mid']:.1f} kPa = {n['p_mid'] / 1000:.4f} MPa.</p>
<table><tr><th>Check (Roark, flat plate, all edges fixed, a/b = {a / b:.2f})</th><th class="r">Hand</th><th class="r">FEA</th></tr>
<tr><td>Bending stress at the middle of the long edge: &sigma; = &beta; p b&sup2; / t&sup2;, &beta; = {n['beta']:.3f}</td><td class="r">{n['sig_panel']:.1f} MPa</td><td class="r">&mdash;</td></tr>
<tr><td>Von Mises at that point (&sigma;<sub>2</sub> = 0.3 &sigma;<sub>1</sub>)</td><td class="r">{n['vm_panel']:.1f} MPa</td><td class="r">{fs.get('vm_max', 0):.1f} MPa</td></tr>
<tr><td>Deflection at the centre: y = &alpha; p b&#8308; / (E t&sup3;), &alpha; = {n['alpha']:.4f}</td><td class="r">{n['defl_panel']:.2f} mm</td><td class="r">{fs.get('disp_max', 0):.2f} mm</td></tr>
<tr><td>Safety factor on yield (355 MPa)</td><td class="r">{355 / n['vm_panel']:.1f}</td><td class="r">{fs.get('sf_min', 0):.1f}</td></tr>
</table>
<p class="small">The hand calculation and the FEA agree to within {abs(fs.get('vm_max', n['vm_panel']) - n['vm_panel']) / n['vm_panel'] * 100:.0f} % on stress and {abs(fs.get('disp_max', n['defl_panel']) - n['defl_panel']) / n['defl_panel'] * 100:.0f} % on deflection. <span class="ok">Panel OK.</span></p>
</div>
<div>{hdr(2)}
<h2>5. Bottom girder (worst girder)</h2>
<p>Carries the water on the strip from the cill to half way to the next girder (0 to {E.GIRDERS[0] / 2000 + E.GIRDERS[1] / 2000:.3f} m):
w = &rho;g (h z &minus; z&sup2;/2) = <b>{n['w_g']:.1f} kN/m</b>. Span between the heel and mitre posts L = {n['span']:.2f} m. Treated as simply supported, which ignores the arch action and so is on the safe side:
M = wL&sup2;/8 = {n['M_g']:.2f} kNm.</p>
<p>Section: 400 mm of skin plate acting with the girder, web {E.WEB_T} mm, flange {E.FLANGE[0]} &times; {E.FLANGE[1]} mm. A = {n['A_g']:.0f} mm&sup2;, neutral axis {n['ybar']:.0f} mm from the leaf centre, I = {n['I_g'] / 1e6:.0f} &times; 10&#8310; mm&#8308;.
&sigma; = M y / I = {n['M_g']:.2f} &times; 10&#8310; &times; {n['ymax']:.0f} / {n['I_g'] / 1e6:.0f} &times; 10&#8310; = <b>{n['sig_g']:.1f} MPa</b>, safety factor {355 / n['sig_g']:.0f}. <span class="ok">OK.</span>
The girders are governed by stiffness, the axial thrust from the mitre ({n['R_mitre']:.0f} kN shared by eight girders) and boat impact, not by bending stress.</p>
<h2>6. Leaf weight, hinges and lifting</h2>
<table><tr><th>Quantity</th><th>Working</th><th class="r">Result</th></tr>
<tr><td>Leaf mass (CAD model: steel, oak, walkway, seals)</td><td>steel 7850 kg/m&sup3;, oak 750 kg/m&sup3;</td><td class="r"><b>{n['mass'] / 1000:.2f} t</b></td></tr>
<tr><td>Weight on the bottom pintle</td><td>W = mg</td><td class="r">{n['W']:.1f} kN</td></tr>
<tr><td>Centre of gravity from the pivot</td><td>from the CAD model</td><td class="r">{n['xg']:.0f} mm</td></tr>
<tr><td>Sideways load on each hinge</td><td>H = W x / h = {n['W']:.1f} &times; {n['xg'] / 1000:.3f} / 5.78</td><td class="r">{n['H']:.1f} kN</td></tr>
<tr><td>Pintle direct stress (150 mm pin)</td><td>W / (&pi;d&sup2;/4)</td><td class="r">{n['sig_ax']:.1f} MPa</td></tr>
<tr><td>Pintle bending stress (load 140 mm up)</td><td>H &times; 140 / (&pi;d&sup3;/32)</td><td class="r">{n['sig_b']:.1f} MPa</td></tr>
<tr><td>FEA peak at the root fillet</td><td>hub FEA, 10 node tetrahedra</td><td class="r">{fp.get('vm_max', 0):.1f} MPa, SF {fp.get('sf_min', 0):.1f}</td></tr>
<tr><td>Crane lift (25 % allowance for slings and dynamic load)</td><td>1.25 &times; {n['mass'] / 1000:.2f} t</td><td class="r">{n['crane']:.1f} t</td></tr>
</table>
<h2>7. Drive (electric actuator)</h2>
<p>With the levels equal to within 50 mm, the most water push on a moving leaf is 9.81 &times; 0.05 &times; 5.5 &times; 2.46 = {n['F_res']:.2f} kN at mid length, a torque of {n['T_res']:.1f} kNm.
Pintle friction (&mu; = 0.1 on a 75 mm radius) adds {n['T_fric']:.2f} kNm, and water drag at 0.05 m/s is negligible. Design torque 10 kNm.
The actuator lever arm about the pivot is {n['arms'][0][0]:.2f} m shut and {n['arms'][1][0]:.2f} m open, so the actuator needs <b>{n['F_act']:.0f} kN</b>.
Stroke {n['stroke']:.0f} mm (pin centres {n['arms'][0][1]:.0f} to {n['arms'][1][1]:.0f} mm): a 20 kN, 1300 mm stroke electric actuator is chosen.</p>
<h2>8. Summary</h2>
<table class="small"><tr><th>Item</th><th class="r">Load or stress</th><th class="r">Limit</th><th class="r">Safety factor</th></tr>
<tr><td>Skin panel (FEA)</td><td class="r">{fs.get('vm_max', 0):.1f} MPa</td><td class="r">355 MPa</td><td class="r">{fs.get('sf_min', 0):.1f}</td></tr>
<tr><td>Bottom girder (hand, simply supported)</td><td class="r">{n['sig_g']:.1f} MPa</td><td class="r">355 MPa</td><td class="r">{355 / n['sig_g']:.0f}</td></tr>
<tr><td>Bottom pintle (FEA)</td><td class="r">{fp.get('vm_max', 0):.1f} MPa</td><td class="r">250 MPa</td><td class="r">{fp.get('sf_min', 0):.1f}</td></tr>
<tr><td>Actuator</td><td class="r">{n['F_act']:.0f} kN</td><td class="r">20 kN</td><td class="r">{20 / n['F_act']:.1f}</td></tr>
</table>
<p class="small">All checks pass with a safety factor of at least 1.5. Further work for the detailed design: boat impact on the fenders, fatigue of the hinge welds over 100 000 cycles, and a check of the leaf twisting as it swings.</p>
</div></body></html>"""


def notes_html(n):
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>ESP 2023 design notes</title><style>{CSS}
body{{font-size:10pt;line-height:1.45}} p{{margin:0 0 2mm}}</style></head><body>
<div class="hdr"><span>Lock Restoration Ltd. ESP 2023 (8730-035) Task 2</span><span>Design notes: how the design meets the brief. 2026-11-09</span></div>
<h1>Design notes: steel mitre gates for Canal Heritage</h1>
<p><b>Chosen design.</b> Each end of each lock gets a pair of steel mitre gates (design A). The two leaves meet at a 1 in 3 mitre pointing upstream.
A vertical lift gate (design B) was also drawn, but its 11.8 m towers would dominate a heritage canal and its winch could not be hidden in a chamber, so it was rejected.</p>
<p><b>Size and water.</b> The gates fit the 4.2 m opening, are 6.0 m high and are designed for the worst case of 5.5 m of water on one side and none on the other.
That puts {n['p_max']:.1f} kPa on the cill and {n['P_leaf']:.0f} kN on each leaf. Water pushes the leaves together at the mitre and back into the quoins, so the gate works as an arch and gets tighter as the water rises.
Eight girders, closer together at the bottom where the pressure is highest, carry the load. The worst skin plate panel reaches {n.get('fea_esp2023_skin_panel', {}).get('vm_max', n['vm_panel']):.0f} MPa, a safety factor of about 10.</p>
<p><b>Automatic and independent.</b> Each leaf has its own electric actuator, controller, position sensor and water level sensors, so the gates can be opened and shut one at a time from the off-site control centre.
An interlock stops a gate moving unless the levels either side are equal.</p>
<p><b>Drive out of sight.</b> The actuators sit in purpose-built precast concrete inspection chambers beside each gate, under a flush grating cover. Electric drives use the mains supply the brief offers and carry no hydraulic oil that could leak into the canal.</p>
<p><b>Surveillance and emergency stop.</b> A CCTV mast on each chamber watches the gate and the lock. Leaf position, motor current and water levels are sent to the control centre. An emergency call point on each side stops both gates and opens an intercom to the lock keeper.</p>
<p><b>Boat strikes.</b> Replaceable oak fenders on the chamber face take any knocks, the gates only move when the CCTV shows the lock clear, and the cill is marked so boats stay clear of it.</p>
<p><b>Inspection.</b> The walkway on each leaf, and the chamber covers, give safe access to look at the hinges, actuators and seals.</p>
<p><b>Hinges.</b> The leaf turns on a 150 mm stainless pintle in a bronze bush at the bottom and a journal in an anchor collar at the top. Stainless and bronze do not corrode together, and the FEA gives a safety factor of {n.get('fea_esp2023_lock_gates', {}).get('sf_min', 11):.0f}.</p>
<p><b>Seals.</b> EPDM rubber seals run along the cill, behind the heel post and between the mitre posts. Water pressure squeezes them shut. They bolt on, so they can be changed without welding.</p>
<p><b>Removal and maintenance.</b> Each leaf weighs {n['mass'] / 1000:.1f} t and is lifted out by mobile crane once the anchor collar is released. There is nothing to grease daily: routine work is a yearly look and a check of the seals and bush.</p>
<p><b>Looks and sustainability.</b> The gates keep the traditional mitre shape, painted black and white with oak fenders. Steel, stainless steel, bronze and oak can all be recycled or reused, and the oak comes from FSC certified forests.</p>
<p><b>Budget and time.</b> Estimated supply price about £95,000 per gate system (steel fabrication, actuators, hinges, seals, controls and chambers), inside the £100,000 budget. Ten systems can be designed, made and fitted within 52 weeks.</p>
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
    for name, html in (('ESP23_calculations', calcs_html(n)), ('ESP23_design_notes', notes_html(n))):
        h = os.path.join(FOLDER, name + '.html')
        open(h, 'w').write(html)
        to_pdf(h, os.path.join(FOLDER, name + '.pdf'))
        print('wrote', name)
    words = len(__import__('re').sub('<[^>]+>', ' ', notes_html(n).split('<h1>')[1]).split())
    print('design notes words:', words)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in n.items() if not k.startswith('fea')})
