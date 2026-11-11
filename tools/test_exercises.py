"""Checks for the Additional CAD exercise folder (models/exercises.py).

Run:  python tools/test_exercises.py            sizes and clashes only (no browser)
      python tools/test_exercises.py --browser  then the pages at desktop and phone size (needs playwright)

1. Sizes: for every model, points just inside and just outside the faces of the main sizes on its drawing are tested
   against the solid (to 0.1 mm, inch sizes converted), plus the overall size. The valve body mass is compared with
   the 9.606 kg on its sheet.
2. Assemblies: no two parts overlap by more than 1 mm^3, and every part is a single valid solid.
3. Pages: the folder page (every picture and link exists), the hub filter, and each model in the 3D viewer, the Build
   steps tab, the FEA tab and (for the five that move) the Simulation tab load with no errors or missing files, draw
   something and do not scroll sideways on a phone. Screenshots go to qa/.
"""
import functools, http.server, itertools, os, sys, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
sys.path.insert(0, os.path.join(ROOT, 'models'))
import cadquery as cq  # noqa: E402
import parts  # noqa: E402,F401
import exercises as ex  # noqa: E402

IN = 25.4
H = ex.HELI
# (what the drawing says, point, should the point be in material?)
CHECKS = dict(
    ax_fork_bracket=[('base 10 thick', (5, 22, 9.9), True), ('base 10 thick (above)', (5, 22, 10.1), False),
                     ('relief under the base', (36, 22, 1), False), ('18 bore', (36, 10, 54 + 8.9), False),
                     ('18 bore wall', (36, 10, 54 + 9.1), True), ('boss 36 top', (36, 10, 71.9), True), ('boss 36 top (above)', (36, 10, 72.1), False),
                     ('4 oil hole in the top', (36, 6, 68), False),
                     ('lug gap 18: inner face at 13', (36, 12.9, 66), True), ('lug gap 18 (gap)', (36, 13.1, 66), False),
                     ('8 hole at 9', (12.9, 22, 5), False), ('8 hole wall', (13.1, 22, 5), True)],
    ax_pedestal_bearing=[('18 bore', (37, 21, 58.9), False), ('18 bore wall', (37, 21, 59.1), True),
                         ('boss 36 top at 68', (37, 21, 67.9), True), ('boss top (above)', (37, 21, 68.1), False),
                         ('base 10 thick', (25, 21, 9.9), True), ('relief 16 x 4 under the base', (37, 21, 1), False)],
    ax_slotted_boss_flange=[('26 bore', (12.9, 0, 20), False), ('26 bore wall', (13.1, 0, 20), True),
                            ('40 boss', (19.9, 0, 20), True), ('40 boss (outside)', (20.1, 0, 20), False),
                            ('flange 8 thick', (25, 0, 7.9), True), ('flange 8 thick (above)', (25, 0, 8.1), False),
                            ('12.5 hole', (-40, 6.1, 4), False), ('12.5 hole wall', (-40, 6.4, 4), True),
                            ('slot 16 wide', (7.9, 15, 45), False), ('slot side', (8.1, 15, 45), True),
                            ('slot 6 deep', (0, 15, 41.9), True), ('boss 48 high', (15, 0, 47.9), True)],
    ax_corner_boss_bracket=[('32 bore', (15.9, 62, 10), False), ('32 bore wall', (16.1, 62, 10), True),
                            ('50 boss', (24.9, 62, 10), True), ('50 boss (outside)', (25.1, 62, 25), False),
                            ('boss 30 high', (20, 62, 29.9), True), ('plate 8 thick', (20, 30, 7.9), True),
                            ('plate 8 thick (above)', (20, 30, 8.1), False), ('13 lug hole', (38.4, 0, 4), False),
                            ('13 lug hole wall', (38.6, 0, 4), True), ('12 cross hole at 20 high', (20, 62, 20), False)],
    ax_saddle_block=[('R28 saddle', (60, 40, 33 - 27.9), False), ('R28 saddle wall', (60, 40, 33 - 28.1), True),
                     ('R20 saddle', (60, 74, 33 - 19.9), False), ('R20 saddle wall', (60, 74, 33 - 20.1), True),
                     ('base 15 thick', (5, 48, 14.9), True), ('base 15 (above)', (5, 48, 15.1), False),
                     ('9 hole', (17.4, 28, 8), False), ('9 hole wall', (17.6, 28, 8), True)],
    ax_clamp_lever=[('28 bore', (0, 13.9, 10), False), ('28 bore wall', (0, 14.1, 10), True), ('42 boss', (0, 20.9, 10), True),
                    ('42 boss (outside)', (0, 21.1, 10), False), ('8.5 bolt hole', (-33, 10, 28.2), False),
                    ('8.5 bolt hole wall', (-33, 10, 28.4), True), ('arm slot', (60, 0, 15), False), ('slot floor 8', (60, 0, 7.9), True),
                    ('slot 20 wide', (60, 9.9, 15), False), ('slot wall', (60, 10.1, 15), True)],
    ax_roller_assembly=[('roller 100', (0, 0, 72 + 49.9), True), ('roller 100 (outside)', (0, 0, 72 + 50.1), False),
                        ('spindle 16', (0, 0, 72 + 7.9), True), ('base 150 long', (74.9, 0, 10), True), ('base 150 (beyond)', (75.1, 0, 10), False)],
    ax_valve_body=[('flange 146', (70, 72.9, 0), True), ('flange 146 (outside)', (70, 73.1, 0), False),
                   ('42 bore', (70, 0, 20.9), False), ('42 bore wall', (70, 0, 21.1), True),
                   ('166 over the flanges', (82.9, 30, 0), True), ('166 (beyond)', (83.1, 30, 0), False)],
    ax_machinists_jack=[('base 132 long', (65.9, 0, 7), True), ('base 132 (beyond)', (66.1, 0, 7), False),
                        ('16 pivot hole', (0, 21, 61.9), True), ('base 14 thick', (40, 0, 13.9), True), ('base 14 (above)', (40, 0, 14.1), False)],
    ax_planetary_gears=[('ring gear 65', (32.4, 0, 5), True), ('ring gear 65 (outside)', (32.6, 0, 5), False),
                        ('ring tooth tips 58', (28.9, 0, 5), False), ('carrier shaft 8', (3.9, 0, 40), True),
                        ('carrier shaft 8 (outside)', (4.1, 0, 40), False)],
    ax_tube_bracket_45=[('base 65 long', (64.9, 25, 3), True), ('base 65 (beyond)', (65.1, 25, 3), False),
                        ('base 6 thick', (55, 10, 5.9), True), ('base 6 (above)', (55, 10, 6.1), False),
                        ('20 bore', (30, 30, 35), False), ('26 tube', (30 - 12.9, 30, 35), True)],
    ax_angle_bracket=[('base 3.75 in long', (47.5, 0, 5), True), ('base 3.75 in (beyond)', (47.7, 0, 5), False),
                      ('base 0.38 in thick', (35, 0, 9.6), True), ('base 0.38 in (above)', (35, 0, 9.75), False),
                      ('0.50 in bore', (30, 0, 1.5 * IN + 6.3), False), ('0.50 in bore wall', (30, 0, 1.5 * IN + 6.4), True)],
    ax_crankshaft_4=[('619 long', (618.9, 0, 0), True), ('619 (beyond)', (619.1, 0, 0), False), ('main 64', (129, 0, 31.9), True),
                     ('main 64 (outside)', (129, 0, 32.1), False), ('pin 1: 64 on a 44 throw', (186, 0, -75.9), True),
                     ('pin 1 (outside)', (186, 0, -76.1), False), ('flange 144', (610, 0, 71.9), True), ('flange 144 (outside)', (610, 0, 72.1), False),
                     ('10 hole on 109', (612, 54.5 * 0.866, 54.5 * 0.5), False)],
    ax_crankshaft_3=[('564.88 long', (564.8, 0, 0), True), ('564.88 (beyond)', (564.98, 0, 0), False), ('main 2.50 in', (45, 0, 31.7), True),
                     ('main 2.50 in (outside)', (45, 0, 31.8), False), ('pin 3.00 in on a 2.50 in throw', (136.48, 0, -63.5 - 38.0), True),
                     ('pin (outside)', (136.48, 0, -63.5 - 38.2), False)],
    ax_v_pulley=[('5.63 in outside', (71.45, 0, 15), True), ('5.63 in (outside)', (71.6, 0, 15), False),
                 ('0.75 in bore', (9.5, 0, 0), False), ('0.75 in bore wall', (9.6, 0, 0), True), ('V groove', (64, 0, 0), False),
                 ('0.76 in hole on 3.43 in', (43.55 * 0.9239, 43.55 * 0.3827, 0), False)],
    ax_pipe_run_valves=[('70 pipe wall', (32.5, 0, 200), True), ('70 pipe (outside)', (35.1, 0, 200), False), ('60 bore', (29.9, 0, 200), False),
                        ('top run 850 up', (600, 0, 850 + 32.5), True), ('top run ends at 755', (754.9, 0, 850 + 32.5), True),
                        ('top run (beyond)', (755.1, 0, 850 + 32.5), False), ('bottom run ends at 855', (854.9, 0, 32.5), True),
                        ('bottom run (beyond)', (855.1, 0, 32.5), False)],
    ax_steam_line_loop=[('8 in top run at 2400', (750, 0, 2400 + 105), True), ('8 in (outside)', (750, 0, 2400 + 110), False),
                        ('4 in inlet, 2000 long', (0, -1999.9, 300 + 54), True), ('inlet (beyond)', (0, -2000.1, 300 + 54), False),
                        ('8 in right leg at 1500', (1500 + 105, 0, 2050), True), ('6 in bottom run at 1000', (650 + 0, 0, 1000 + 80), True)],
    ax_oil_pan=[('6.60 in deep', (300, 0, -167.6 + 2.5), True), ('6.60 in (below)', (300, 0, -167.7), False),
                ('flange 8 thick', (5, 0, -4), True), ('flange (below)', (5, 0, -8.1), False), ('shallow end 1.93 in', (80, 0, -49 + 2.5), True),
                ('shallow end (below)', (80, 0, -49.1), False), ('sump is hollow', (300, 0, -80), False)],
    ax_engine_block=[('3.684 in bore', (61.6 + 46.7, 0, -90), False), ('bore wall', (61.6 + 46.9, 0, -90), True),
                     ('water jacket', (61.6 + 60, 0, -80), False), ('deck between bores 2 and 3', (0, 0, -5), True),
                     ('11 head bolt hole', (61.6 + 42, 40, -30), False), ('bolt boss through the jacket', (61.6 + 42 + 7, 40, -40), True),
                     ('546 long', (272.9, -40, -90), True), ('546 (beyond)', (273.1, -40, -90), False)],
    ax_helicopter=[('rotor 10.4 m', (H['XM'] + 5199, 0, H['ZC'] + 1630), True), ('rotor (beyond)', (H['XM'] + 5201, 0, H['ZC'] + 1630), False),
                   ('skid tube', (2000, 950, 77), True), ('skid bore', (2000, 950, 40), False)],
)
SIZES = dict(ax_fork_bracket=(72, 44, 72), ax_crankshaft_4=(619, 144, 160), ax_crankshaft_3=(564.88, None, None),
             ax_v_pulley=(143.0, 143.0, 41.4), ax_engine_block=(546, 239, 180), ax_angle_bracket=(95.25, 76.2, None),
             ax_valve_body=(166, 176, 156), ax_saddle_block=(120, 96, 33), ax_tube_bracket_45=(65, 50, None))
VALVE_MASS = 9.606   # kg, on the sheet (AISI 316L)


def solid_of(items):
    return cq.Compound.makeCompound([w.val() for n, w, c in items])


def check_sizes():
    fails, report = [], []
    for m in ex.MODELS:
        name = m['name']
        items = m['fn']()
        comp = solid_of(items)
        before = len(fails)
        for n, w, c in items:
            v = w.val()
            if not v.isValid() or len(w.solids().vals()) != 1:
                fails.append((name, n, 'not one valid solid'))
        bb = comp.BoundingBox()
        got = (round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2))
        for a, b in zip(got, SIZES.get(name, (None, None, None))):
            if b is not None and abs(a - b) > 0.1:
                fails.append((name, 'overall size', got, SIZES[name]))
        for what, p, inside in CHECKS[name]:
            got_in = any(w.val().isInside(cq.Vector(*p), 1e-4) for n, w, c in items)
            if got_in != inside:
                fails.append((name, what, p, 'in material' if got_in else 'empty'))
        clashes = 0
        if len(items) > 1:
            boxes = [w.val().BoundingBox() for n, w, c in items]
            for (i, (na, wa, _)), (j, (nb, wb, _)) in itertools.combinations(enumerate(items), 2):
                A, B = boxes[i], boxes[j]
                if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin:
                    continue
                v = wa.val().intersect(wb.val()).Volume()
                if v > 1:
                    clashes += 1
                    fails.append((name, 'clash', na, nb, round(v, 1)))
        extra = ''
        if name == 'ax_valve_body':
            kg = comp.Volume() * 8.0e-6
            extra = '  %.2f kg (sheet %.3f kg)' % (kg, VALVE_MASS)
            if abs(kg - VALVE_MASS) / VALVE_MASS > 0.15:
                fails.append((name, 'mass', kg, VALVE_MASS))
        report.append('%-24s %-4s %2d parts %3d size checks %s mm%s' % (
            name, 'ok' if len(fails) == before else 'FAIL', len(items), len(CHECKS[name]), ' x '.join('%g' % g for g in got), extra))
    for r in report:
        print(r)
    return fails


SIM = set(ex.SIM_MODELS)
PAGES = [('ax_folder', 'Additional%20CAD%20exercise/index.html', 'cards', None, True),
         ('hub_ax_filter', 'index.html', 'hubcards', '[data-f="Additional CAD exercise"]', True)] + [
    pg for m in ex.MODELS for pg in (
        (m['name'] + '_3d', 'viewer.html?m=' + m['name'], 'canvas', None, True),
        (m['name'] + '_steps_last', 'viewer.html?m=%s&tab=steps&step=99' % m['name'], 'canvas', None, True),
        (m['name'] + '_fea', 'viewer.html?m=%s&tab=fea' % m['name'], 'canvas', None, False)) +
    (((m['name'] + '_sim', 'viewer.html?m=%s&tab=sim' % m['name'], 'canvas', None, False),) if m['name'] in SIM else ())]
COUNT = dict(cards="document.querySelectorAll('.card').length", hubcards="document.querySelectorAll('#grid .card').length")
DREW = """() => {
  const c = document.querySelector('canvas'); if (!c) return 0;
  const g = document.createElement('canvas'); g.width = 64; g.height = 64;
  const x = g.getContext('2d'); x.drawImage(c, 0, 0, 64, 64);
  const d = x.getImageData(0, 0, 64, 64).data; const first = d.slice(0, 3).join();
  let n = 0; for (let i = 0; i < d.length; i += 4) if ([d[i], d[i+1], d[i+2]].join() !== first) n++;
  return n;
}"""


def check_pages():
    from playwright.sync_api import sync_playwright
    out = os.environ.get('QA_OUT', os.path.join(ROOT, 'qa'))
    os.makedirs(out, exist_ok=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=DOCS))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d/' % srv.server_address[1]
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for size, (w, h) in dict(desktop=(1280, 800), phone=(390, 844)).items():
            for name, url, kind, press, on_phone in PAGES:
                if size == 'phone' and not on_phone:
                    continue
                pg = b.new_page(viewport=dict(width=w, height=h), device_scale_factor=1, is_mobile=size == 'phone',
                                has_touch=size == 'phone')
                errs = []
                pg.on('console', lambda m, e=errs: e.append(m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
                pg.on('pageerror', lambda x, e=errs: e.append(str(x)))
                pg.on('response', lambda r, e=errs: e.append('%d %s' % (r.status, r.url))
                      if r.status >= 400 and r.request.method != 'HEAD' and 'favicon' not in r.url else None)
                pg.goto(base + url, wait_until='load')
                pg.wait_for_timeout(4000)
                if press:
                    pg.click(press)
                    pg.wait_for_timeout(800)
                if kind == 'cards':   # the cards' pictures and links must all exist
                    for href in pg.evaluate("[...document.querySelectorAll('.card a, .card img, td a')].map(a => a.href || a.src)"):
                        r = pg.request.head(href) if href.startswith(base) else None
                        if r is not None and r.status >= 400:
                            errs.append('%d %s' % (r.status, href))
                drew = pg.evaluate(DREW) if kind == 'canvas' else 999
                count = pg.evaluate(COUNT[kind]) if kind in COUNT else 20
                wide = pg.evaluate('document.documentElement.scrollWidth - window.innerWidth')
                pg.screenshot(path=os.path.join(out, 'ax_%s_%s.png' % (size, name)))
                ok = not errs and drew > 20 and wide <= 1 and count >= 20
                if not ok:
                    fails.append((size, name, errs[:3], drew, wide, count))
                print('%-4s %-8s %-40s errors %d  drawn px %4d  overflow %d' % ('ok' if ok else 'FAIL', size, name, len(errs), drew, wide))
                pg.close()
        b.close()
    srv.shutdown()
    return fails


if __name__ == '__main__':
    fails = check_sizes()
    if '--browser' in sys.argv:
        fails += check_pages()
    if fails:
        print('\nFailures:')
        for f in fails:
            print(' ', f)
        sys.exit(1)
    print('\nAll checks passed.')
