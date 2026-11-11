"""Checks for the World Skill folder: the four parts of the WorldSkills UK Mechanical Engineering CAD 2022
pre-competition activity (models/worldskill.py).

Run:  python tools/test_worldskill.py            sizes only (no browser)
      python tools/test_worldskill.py --browser  sizes, then the pages at desktop and phone size (needs playwright)

1. Sizes: for every part, points just inside and just outside the faces the competition sheet dimensions are
   tested against the solid, so each listed size is checked to 0.1 mm, plus the overall size and the mass.
2. Pages: the World Skill page, the hub filter and each part in the 3D viewer and the Build steps tab load with
   no errors or missing files, draw something and do not scroll sideways on a phone. Screenshots go to qa/.
"""
import functools, http.server, json, math, os, sys, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
sys.path.insert(0, os.path.join(ROOT, 'models'))
import cadquery as cq  # noqa: E402
import parts  # noqa: E402,F401
import worldskill as ws  # noqa: E402

DENSITY = {'Mild steel': 7.85, 'ABS plastic': 1.05, 'PEEK plastic': 1.30}   # g/cm3

# (what the sheet says, point, should the point be in material?)
CHECKS = dict(
    ws2022_crank=[
        ('shaft 15 dia: inside', (20, 7.4, 0), True), ('shaft 15 dia: outside', (20, 7.6, 0), False),
        ('taper to 12.2 at 43.5', (43.4, 6.0, 0), True), ('taper to 12.2 at 43.5 (outside)', (43.4, 6.2, 0), False),
        ('chamfer to 9.7 at 44.5', (44.4, 4.9, 0), True), ('chamfer (outside)', (44.4, 5.1, 0), False),
        ('length 44.5', (44.45, 0, 3), True), ('length 44.5 (beyond)', (44.6, 0, 3), False),
        ('4 THRU on the axis', (30, 0, 1.9), False), ('4 THRU wall', (30, 0, 2.1), True),
        ('11 THRU at 15.8 below', (8, 0, -15.8 + 5.4), False), ('11 THRU wall', (8, 0, -15.8 + 5.6), True),
        ('disc 55 dia', (8, 0, 27.4), True), ('disc 55 dia (outside)', (8, 0, 27.6), False),
        ('disc 11 thick', (10.95, 0, 24), True), ('disc 11 thick (beyond)', (11.05, 0, 24), False),
        ('recess 5.5 deep on the axis', (5.4, 0, 3), False), ('recess floor', (5.6, 0, 3), True),
        ('crescent (counterweight) full thickness', (1, 0, 20), True),
        ('boss 23.5 dia full thickness', (1, 0, -15.8 + 11.6), True), ('recess outside the boss', (1, 0, -15.8 + 11.9), False),
        ('R24 recess edge', (1, 0, -15.8 + 24.1), True),
        ('detail B 0.2 step inside 40', (10.9, 0, 15), False), ('detail B rim outside 40', (10.9, 0, 21), True),
        ('detail B land 20.5', (10.9, 0, 9.5), True),
        ('key slot 1.8 wide, R6.6', (40, 0, -5.5), False), ('key slot side', (40, 1.2, -5.5), True),
    ],
    ws2022_piston_head=[
        ('height 44 (crown top)', (0, 0, 43.9), True), ('crown top (above)', (0, 0, 44.1), False),
        ('crown 3.0 thick (SR59.5 inside)', (0, 0, 41.1), True), ('crown underside', (0, 0, 40.9), False),
        ('44 dia', (0, 21.9, 25), True), ('44 dia (outside)', (0, 22.1, 25), False),
        ('bore 38 (wall 3.0)', (0, 19.1, 25), True), ('bore 38 (inside)', (0, 18.9, 25), False),
        ('groove 2.0 x 40 dia at 29.3', (0, 21, 30.3), False), ('groove root 40 dia', (0, 19.9, 30.3), True),
        ('land between grooves', (0, 21, 32.8), True), ('groove at 34.3', (0, 21, 35.3), False),
        ('top land', (0, 21, 37.5), True),
        ('pin hole 11 at 18.5', (12, 0, 18.5 + 5.4), False), ('boss round the hole', (12, 0, 18.5 + 5.6), True),
        ('boss 17 dia', (12, 0, 18.5 + 8.4), True), ('above the boss', (12, 0, 18.5 + 8.6), False),
        ('16 between bosses', (7.9, 0, 24.5), False), ('boss inner end', (8.1, 0, 24.5), True),
        ('skirt cut-out 10 high on the pin side', (20.5, 0, 9.9), False), ('above the cut-out', (20.5, 0, 10.1), True),
        ('cut-out 24 wide', (16.7, 11.9, 9), False), ('outside the 24 width', (16.17, 12.6, 9), True),
        ('41.2 deg line, 2.0 in at the bottom', (0, 21, 0.2), True), ('41.2 deg line (cut side)', (12.8, 16, 2.0), False),
    ],
    ws2022_pull_cord_grill=[
        ('height 31 (dome)', (0, 0, 30.9), True), ('height 31 (above)', (0, 0, 31.1), False),
        ('rim 30 outside the 65', (35, 0, 29.9), True), ('rim 30 (above)', (35, 0, 30.1), False),
        ('top 1.0 thick, underside 29', (20, 0, 28.9), False), ('top', (20, 0, 29.1), True),
        ('boss 18 / 14, 3.0 deep', (8, 0, 26.1), True), ('boss inside 14', (6.9, 0, 27), False),
        ('cup 71 inside', (35.4, 0, 25), False), ('cup wall', (35.6, 0, 25), True),
        ('flange 95', (47.3, 0, 0.2), True), ('flange 95 (outside)', (47.7, 0, 0.2), False),
        ('flange 4.0 thick', (0, -43, 3.9), True), ('flange 4.0 thick (slot above)', (0, -43, 4.1), False),
        ('slot 8.0 wide at the top of the plan (cord box side)', (0, -38, 12), False),
        ('cord box 20 wide at 13.7: wall', (14.7, -40, 15), True), ('box inside', (16.0, -40, 15), False),
        ('box out to 50', (23.7, -49.9, 25), True), ('box end (beyond)', (23.7, -50.1, 25), False),
        ('cord hole 6.0 at 15 high', (23.7, -49, 15 + 2.9), False), ('end wall above the hole', (23.7, -49, 15 + 3.1), True),
        ('flange hole 4.0 at 11.7 deg', (43.75 * math.cos(math.radians(11.7)), -43.75 * math.sin(math.radians(11.7)), 2), False),
    ],
    ws2022_cord_case=[
        ('height 40', (0, 19, 39.9), True), ('height 40 (above)', (0, 19, 40.1), False),
        ('tube 40 / 36', (0, 19.9, 30), True), ('tube bore', (0, 17.9, 30), False),
        ('bore 25.5 deep (floor at 14.5)', (0, 15, 14.6), False), ('floor', (0, 15, 14.4), True),
        ('hub 16, 5.0 up from the floor', (0, 7.5, 19.4), True), ('hub top', (0, 7.5, 19.6), False),
        ('14 THRU', (0, 6.9, 10), False), ('14 THRU wall', (0, 7.1, 10), True),
        ('groove 49.1 between 7 and 15', (0, 24.5, 10), True), ('groove 49.1 (outside)', (0, 24.6, 10), False),
        ('flange 70', (0, 34.9, 16), True), ('flange 70 (outside)', (0, 35.1, 16), False),
        ('flange 15 to 17.5', (0, 30, 17.4), True), ('flange top', (30, 10, 17.6), False),
        ('base 64.4 at 7.0', (0, 32.1, 6.9), True), ('base (outside)', (0, 32.3, 6.9), False),
        ('recess 64, 3.5 deep', (0, 25, 3.4), False), ('above the recess', (0, 25, 3.6), True),
        ('pocket 1.0 deep (R11 to R19)', (15 * math.cos(math.radians(-175.9)), 15 * math.sin(math.radians(-175.9)), 4.4), False),
        ('pocket floor', (15 * math.cos(math.radians(-175.9)), 15 * math.sin(math.radians(-175.9)), 4.6), True),
        ('groove R19 to R20, 5.5 deep', (0, 19.5, 8.9), False), ('above the groove', (0, 19.5, 9.1), True),
        ('guide end wall R30.3 to R32', (-31, 0, 22), True), ('inside the guide', (-29, 0, 22), False),
        ('guide 10.0 high', (-31, 0, 27.4), True), ('guide top', (-31, 0, 27.6), False),
        ('guide side wall 1.7 at 17.5 wide', (-25, 7.9, 22), True), ('between the walls', (-25, 6.9, 22), False),
        ('4.0 hole 2.5 deep at 27.4 (through the 2.5 flange)', (-27.4, 0, 16), False), ('beside the hole', (-27.4, 2.1, 16), True),
    ],
)
SIZES = dict(ws2022_crank=(44.5, 55, 55), ws2022_piston_head=(44, 44, 44), ws2022_pull_cord_grill=(95, 97.5, 31),
             ws2022_cord_case=(70, 70, 40))


def check_sizes():
    fails, report = [], []
    for m in ws.MODELS:
        name = m['name']
        shape = m['fn']()[0][1].val()
        assert shape.isValid(), name
        bb = shape.BoundingBox()
        got = (round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2))
        want = SIZES[name]
        if any(abs(a - b) > 0.05 for a, b in zip(got, want)):
            fails.append((name, 'overall size', got, want))
        before = len(fails)
        for what, p, inside in CHECKS[name]:
            got_in = shape.isInside(cq.Vector(*p), 1e-4)
            if got_in != inside:
                fails.append((name, what, p, 'in material' if got_in else 'empty'))
        mass = shape.Volume() / 1000 * DENSITY[m['material']]
        report.append('%-24s %-5s %4d size checks  %s  %.0f g (%s)' % (name, 'ok' if len(fails) == before else 'FAIL', len(CHECKS[name]),
                                                                     ' x '.join('%g' % g for g in got), mass, m['material']))
    for r in report:
        print(r)
    return fails


PAGES = [('ws_folder', 'World%20Skill/index.html', 'cards', None),
         ('hub_ws_filter', 'index.html', 'hubcards', '[data-f="World Skill"]')] + [
    pg for m in ws.MODELS for pg in (
        (m['name'] + '_3d', 'viewer.html?m=' + m['name'], 'canvas', None),
        (m['name'] + '_steps_last', 'viewer.html?m=%s&tab=steps&step=99' % m['name'], 'canvas', None))]
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
            for name, url, kind, press in PAGES:
                pg = b.new_page(viewport=dict(width=w, height=h), device_scale_factor=1, is_mobile=size == 'phone',
                                has_touch=size == 'phone')
                errs = []
                pg.on('console', lambda m, e=errs: e.append(m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
                pg.on('pageerror', lambda x, e=errs: e.append(str(x)))
                pg.on('response', lambda r, e=errs: e.append('%d %s' % (r.status, r.url))
                      if r.status >= 400 and r.request.method != 'HEAD' and 'favicon' not in r.url else None)
                pg.goto(base + url, wait_until='load')
                pg.wait_for_timeout(3500)
                if press:
                    pg.click(press)
                    pg.wait_for_timeout(800)
                if kind == 'cards':   # the cards' pictures and links must all exist
                    for href in pg.evaluate("[...document.querySelectorAll('.card a, .card img')].map(a => a.href || a.src)"):
                        r = pg.request.head(href) if href.startswith(base) else None
                        if r is not None and r.status >= 400:
                            errs.append('%d %s' % (r.status, href))
                drew = pg.evaluate(DREW) if kind == 'canvas' else 999
                count = pg.evaluate(COUNT[kind]) if kind in COUNT else 4
                wide = pg.evaluate('document.documentElement.scrollWidth - window.innerWidth')
                pg.screenshot(path=os.path.join(out, 'ws_%s_%s.png' % (size, name)))
                ok = not errs and drew > 20 and wide <= 1 and count >= 4
                if not ok:
                    fails.append((size, name, errs[:3], drew, wide, count))
                print('%-4s %-8s %-36s errors %d  drawn px %4d  overflow %d' % ('ok' if ok else 'FAIL', size, name, len(errs), drew, wide))
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
