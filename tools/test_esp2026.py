"""Browser checks for the ESP 2026 seat set pages, at desktop and phone size.

Run:  python tools/test_esp2026.py [page names]   (needs playwright with Chromium)

For each page and tab it loads the page from a local server and checks:
  * no JavaScript errors and no failed requests (404s),
  * the 3D canvas (or page) actually drew something,
  * no sideways scrolling at phone width.
Screenshots go to docs/ESP 2026/qa/ so they can be looked at in the pull request.
"""
import functools, http.server, os, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
OUT = os.path.join(DOCS, 'ESP 2026', 'qa')

SIZES = dict(desktop=(1280, 800), phone=(390, 844))
# (name, url, what to check, button to press first)
PAGES = [
    ('hub', 'index.html', None, None),
    ('hub_esp_filter', 'index.html', 'esp', '#filters [data-f="ESP 2026"]'),
    ('hub_esp2023_filter', 'index.html', 'esp23', '#filters [data-f="ESP 2023"]'),
    ('project', 'ESP%202026/index.html', 'results', None),
    ('project_parts', 'ESP%202026/index.html#parts', 'parts', None),
    ('set_3d', 'viewer.html?m=esp2026_seat_set', 'canvas', None),
    ('set_parts_list', 'viewer.html?m=esp2026_seat_set', 'bom', '#bomBtn'),
    ('set_steps', 'viewer.html?m=esp2026_seat_set&tab=steps', 'canvas', None),
    ('set_sim', 'viewer.html?m=esp2026_seat_set&tab=sim', 'canvas', None),
    ('seat_3d', 'viewer.html?m=esp2026_single_seat', 'canvas', None),
    ('seat_parts_list', 'viewer.html?m=esp2026_single_seat', 'bom', '#bomBtn'),
    ('seat_steps', 'viewer.html?m=esp2026_single_seat&tab=steps&step=7', 'canvas', None),
    ('part_leg', 'viewer.html?m=esp2026_p04_leg', 'canvas', None),
    ('part_back_shell_steps', 'viewer.html?m=esp2026_p12_back_shell&tab=steps', 'canvas', None),
    ('part_armrest', 'viewer.html?m=esp2026_p23_armrest', 'canvas', None),
    ('part_buckle', 'viewer.html?m=esp2026_p29_buckle_body', 'canvas', None),
    ('leg_fea', 'viewer.html?m=esp2026_p04_leg&tab=fea&step=10', 'canvas', None),
    ('shell_3d', 'viewer.html?m=esp2026_shell_seats', 'canvas', None),
    # older models, to show the shared viewer and the ESP 2023 project still work
    ('esp2023_ga', 'viewer.html?m=esp2023_lock_gates', 'canvas', None),
    ('hub_cylinder_fea', 'viewer.html?m=pneumatic_cylinder&tab=fea&step=10', 'canvas', None),
]

# extra checks: how many things the page must show
COUNT = dict(
    esp="document.querySelectorAll('#grid .card').length",
    esp23="document.querySelectorAll('#grid .card').length",
    parts="document.querySelectorAll('#parts .pcard').length",
    results="document.querySelectorAll('#results tr, #legs tr').length",
    bom="document.querySelectorAll('table.bom tr').length",
)
# 42 cards under the ESP 2026 filter (3 assemblies + 39 parts), 45 under ESP 2023 as before, 39 parts in the gallery,
# the two results tables filled in from ESP26_calculations.json, and a parts list with rows in the viewer
NEED = dict(esp=42, esp23=45, parts=39, results=14, bom=10)

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
