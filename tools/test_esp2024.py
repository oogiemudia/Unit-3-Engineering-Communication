"""Browser checks for the ESP 2024 harbour buoy pages, at desktop and phone size.

Run:  python tools/test_esp2024.py [page names]   (needs playwright with Chromium)

For each page and tab it loads the page from a local server and checks:
  * no JavaScript errors and no failed requests (404s),
  * the 3D canvas (or page) actually drew something,
  * no sideways scrolling at phone width.
Screenshots go to docs/ESP 2024/qa/ so they can be looked at in the pull request.
"""
import functools, http.server, os, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
OUT = os.path.join(DOCS, 'ESP 2024', 'qa')

SIZES = dict(desktop=(1280, 800), phone=(390, 844))
# (name, url, what to check, button to press first)
PAGES = [
    ('hub', 'index.html', None, None),
    ('hub_esp_filter', 'index.html', 'esp', '#filters [data-f="ESP 2024"]'),
    ('hub_esp2026_filter', 'index.html', 'esp26', '#filters [data-f="ESP 2026"]'),
    ('project', 'ESP%202024/index.html', 'results', None),
    ('project_parts', 'ESP%202024/index.html#parts', 'parts', None),
    ('project_subs', 'ESP%202024/index.html', 'subs', None),
    ('buoy_3d', 'viewer.html?m=esp2024_buoy', 'canvas', None),
    ('buoy_parts_list', 'viewer.html?m=esp2024_buoy', 'bom', '#bomBtn'),
    ('buoy_steps', 'viewer.html?m=esp2024_buoy&tab=steps&step=3', 'canvas', None),
    ('buoy_sim', 'viewer.html?m=esp2024_buoy&tab=sim', 'canvas', None),
    ('green_3d', 'viewer.html?m=esp2024_buoy_green', 'canvas', None),
    ('wind_3d', 'viewer.html?m=esp2024_wind_buoy', 'canvas', None),
    ('part_float_hull_steps', 'viewer.html?m=esp2024_p01_float_hull&tab=steps', 'canvas', None),
    ('part_canister', 'viewer.html?m=esp2024_p09_canister', 'canvas', None),
    ('part_tripod_leg', 'viewer.html?m=esp2024_p24_tripod_leg', 'canvas', None),
    ('part_shackle', 'viewer.html?m=esp2024_p38_shackle', 'canvas', None),
    ('eye_fea', 'viewer.html?m=esp2024_p23_mooring_eye&tab=fea&step=10', 'canvas', None),
    ('sub_float_steps', 'viewer.html?m=esp2024_sa1_float&tab=steps&step=4', 'canvas', None),
    ('sub_equipment_3d', 'viewer.html?m=esp2024_sa2_equipment', 'canvas', None),
    ('sub_mast_parts_list', 'viewer.html?m=esp2024_sa4_mast', 'bom', '#bomBtn'),
    ('sub_sinker_steps', 'viewer.html?m=esp2024_sa7_sinker&tab=steps&step=2', 'canvas', None),
    # older models, to show the shared viewer and the other ESP projects still work
    ('esp2026_ga', 'viewer.html?m=esp2026_seat_set', 'canvas', None),
    ('esp2023_ga', 'viewer.html?m=esp2023_lock_gates', 'canvas', None),
    ('hub_cylinder_fea', 'viewer.html?m=pneumatic_cylinder&tab=fea&step=10', 'canvas', None),
]

# extra checks: how many things the page must show
COUNT = dict(
    esp="document.querySelectorAll('#grid .card').length",
    esp26="document.querySelectorAll('#grid .card').length",
    parts="document.querySelectorAll('#parts .pcard').length",
    results="document.querySelectorAll('#results tr').length",
    subs="document.querySelectorAll('#subs .card').length",
    bom="document.querySelectorAll('table.bom tr').length",
)
# 53 cards under the ESP 2024 filter (3 assemblies + 7 sub-assemblies + 43 parts), 49 under ESP 2026 as before, 43 parts in the
# gallery, the results table filled in from ESP24_calculations.json, and a parts list with rows in the viewer
NEED = dict(esp=53, esp26=49, parts=43, results=10, subs=7, bom=5)

DREW = """() => {
  const c = document.querySelector('canvas'); if (!c) return 0;
  const g = document.createElement('canvas'); g.width = 64; g.height = 64;
  const x = g.getContext('2d'); x.drawImage(c, 0, 0, 64, 64);
  const d = x.getImageData(0, 0, 64, 64).data; const first = d.slice(0, 3).join();
  let n = 0; for (let i = 0; i < d.length; i += 4) if ([d[i], d[i+1], d[i+2]].join() !== first) n++;
  return n;
}"""


def main():
    # optional page names on the command line run just those pages
    pages = [pg for pg in PAGES if pg[0] in sys.argv[1:]] or PAGES
    os.makedirs(OUT, exist_ok=True)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=DOCS)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d/' % srv.server_address[1]
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for size, (w, h) in SIZES.items():
            for name, url, kind, press in pages:
                pg = b.new_page(viewport=dict(width=w, height=h), device_scale_factor=1,
                                is_mobile=size == 'phone', has_touch=size == 'phone')
                errs = []
                pg.on('console', lambda m, e=errs: e.append(m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
                pg.on('pageerror', lambda x, e=errs: e.append(str(x)))
                # failed requests are caught here (the console message has no URL); a missing sim file is checked with HEAD and is expected for models without a simulation
                pg.on('response', lambda r, e=errs: e.append('%d %s' % (r.status, r.url))
                      if r.status >= 400 and r.request.method != 'HEAD' and 'favicon' not in r.url else None)
                pg.goto(base + url, wait_until='load')
                pg.wait_for_timeout(3500)
                if press:
                    pg.click(press)
                    pg.wait_for_timeout(800)
                drew = pg.evaluate(DREW) if kind in ('canvas', 'bom') else 999
                count = pg.evaluate(COUNT[kind]) if kind in COUNT else 0
                wide = pg.evaluate('document.documentElement.scrollWidth - window.innerWidth')
                pg.screenshot(path=os.path.join(OUT, '%s_%s.png' % (size, name)))
                ok = not errs and drew > 20 and wide <= 1 and count >= NEED.get(kind, 0)
                if not ok:
                    fails.append((size, name, errs[:3], drew, wide, count))
                print('%-4s %-8s %-20s errors %d  drawn px %4d  overflow %d%s' % ('ok' if ok else 'FAIL', size, name, len(errs), drew, wide,
                      '  items %d' % count if kind in COUNT else ''))
                pg.close()
        b.close()
    srv.shutdown()
    if fails:
        print('\nFailures:')
        for f in fails:
            print(' ', f)
        sys.exit(1)
    print('\nAll %d checks passed.' % (len(SIZES) * len(pages)))


if __name__ == '__main__':
    main()
