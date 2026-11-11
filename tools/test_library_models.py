"""Browser checks for the GrabCAD models folder (the machine vice and the nine models added with it), at desktop and
phone size.

Run:  python tools/test_library_models.py [page names]   (needs playwright with Chromium)

For each page and tab it loads the page from a local server and checks:
  * no JavaScript errors and no failed requests (404s),
  * the 3D canvas (or page) actually drew something,
  * no sideways scrolling at phone width.
Screenshots go to qa/ at the top of the repository (or the folder named by QA_OUT), to be looked at by hand.
"""
import functools, http.server, os, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
OUT = os.environ.get('QA_OUT', os.path.join(ROOT, 'qa'))

SIZES = dict(desktop=(1280, 800), phone=(390, 844))
# (name, url, what to check, button to press first)
PAGES = [
    ('hub', 'index.html', None, None),
    ('vice_3d', 'viewer.html?m=machine_vice', 'canvas', None),
    ('vice_parts_list', 'viewer.html?m=machine_vice', 'bom', '#bomBtn'),
    ('vice_steps_first', 'viewer.html?m=machine_vice&tab=steps&step=1', 'canvas', None),
    ('vice_steps_part', 'viewer.html?m=machine_vice&tab=steps&step=10', 'canvas', None),
    ('vice_steps_last', 'viewer.html?m=machine_vice&tab=steps&step=26', 'canvas', None),
    ('vice_sim', 'viewer.html?m=machine_vice&tab=sim', 'canvas', None),
    ('vice_fea_load', 'viewer.html?m=machine_vice&tab=fea&step=5', 'canvas', None),
    ('vice_fea_vm', 'viewer.html?m=machine_vice&tab=fea&step=10', 'canvas', None),
    ('grabcad_folder', 'GrabCAD%20models/index.html', 'cards', None),
    ('hub_grabcad_filter', 'index.html', None, '[data-f="GrabCAD models"]'),
] + [pg for n in ('plummer_block', 'spur_gearbox', 'universal_joint', 'toggle_clamp', 'swivel_castor', 'screw_jack',
                  'flange_coupling', 'knuckle_joint', 'piston_crank') for pg in (
    (n + '_3d', 'viewer.html?m=' + n, 'canvas', None),
    (n + '_parts_list', 'viewer.html?m=' + n, 'bom', '#bomBtn'),
    (n + '_steps_last', 'viewer.html?m=%s&tab=steps&step=99' % n, 'canvas', None),
    (n + '_sim', 'viewer.html?m=%s&tab=sim' % n, 'canvas', None),
    (n + '_fea_vm', 'viewer.html?m=%s&tab=fea&step=10' % n, 'canvas', None),
)] + [
    # older models, to show the shared viewer still works
    ('hub_bolted_joint', 'viewer.html?m=bolted_joint', 'bom', None),
    ('esp2025_ga', 'viewer.html?m=esp2025_dispenser', 'bom', '#bomBtn'),
]

COUNT = dict(bom="document.querySelectorAll('table.bom tr').length", cards="document.querySelectorAll('.card').length")
NEED = dict(bom=0, cards=9)
NEED_BY_PAGE = dict(vice_parts_list=12, esp2025_ga=5)
# a thin part (the gearbox output shaft) covers few pixels in the 64 x 64 sample
MIN_DRAWN = dict(spur_gearbox_fea_vm=10)

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
                ok = not errs and drew > MIN_DRAWN.get(name, 20) and wide <= 1 and count >= NEED_BY_PAGE.get(name, NEED.get(kind, 0))
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
