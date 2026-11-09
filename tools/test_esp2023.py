"""Browser checks for the ESP 2023 lock gate pages, at desktop and phone size.

Run:  python tools/test_esp2023.py          (needs playwright with Chromium)

For each page and tab it loads the page from a local server and checks:
  * no JavaScript errors and no failed requests (404s),
  * the 3D canvas (or page) actually drew something,
  * no sideways scrolling at phone width.
Screenshots go to docs/ESP 2023/qa/ so they can be looked at in the pull request.
"""
import functools, http.server, os, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
OUT = os.path.join(DOCS, 'ESP 2023', 'qa')

SIZES = dict(desktop=(1280, 800), phone=(390, 844))
PAGES = [
    ('hub', 'index.html', None),
    ('project', 'ESP%202023/index.html', None),
    ('ga_3d', 'viewer.html?m=esp2023_lock_gates', 'canvas'),
    ('ga_steps', 'viewer.html?m=esp2023_lock_gates&tab=steps', 'canvas'),
    ('ga_sim', 'viewer.html?m=esp2023_lock_gates&tab=sim', 'canvas'),
    ('ga_fea', 'viewer.html?m=esp2023_lock_gates&tab=fea&step=10', 'canvas'),
    ('leaf_3d', 'viewer.html?m=esp2023_gate_leaf', 'canvas'),
    ('leaf_steps', 'viewer.html?m=esp2023_gate_leaf&tab=steps&step=16', 'canvas'),
    ('panel_fea', 'viewer.html?m=esp2023_skin_panel&tab=fea&step=10', 'canvas'),
    ('lift_3d', 'viewer.html?m=esp2023_lift_gate', 'canvas'),
    # a hub model, to show the shared viewer still works for the older models
    ('hub_cylinder_fea', 'viewer.html?m=pneumatic_cylinder&tab=fea&step=10', 'canvas'),
]

DREW = """() => {
  const c = document.querySelector('canvas'); if (!c) return 0;
  const g = document.createElement('canvas'); g.width = 64; g.height = 64;
  const x = g.getContext('2d'); x.drawImage(c, 0, 0, 64, 64);
  const d = x.getImageData(0, 0, 64, 64).data; const first = d.slice(0, 3).join();
  let n = 0; for (let i = 0; i < d.length; i += 4) if ([d[i], d[i+1], d[i+2]].join() !== first) n++;
  return n;
}"""


def main():
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
            for name, url, kind in PAGES:
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
                drew = pg.evaluate(DREW) if kind == 'canvas' else 999
                wide = pg.evaluate('document.documentElement.scrollWidth - window.innerWidth')
                pg.screenshot(path=os.path.join(OUT, '%s_%s.png' % (size, name)))
                ok = not errs and drew > 20 and wide <= 1
                if not ok:
                    fails.append((size, name, errs[:3], drew, wide))
                print('%-4s %-8s %-18s errors %d  drawn px %4d  overflow %d' % ('ok' if ok else 'FAIL', size, name, len(errs), drew, wide))
                pg.close()
        b.close()
    srv.shutdown()
    if fails:
        print('\nFailures:')
        for f in fails:
            print(' ', f)
        sys.exit(1)
    print('\nAll %d checks passed.' % (len(SIZES) * len(PAGES)))


if __name__ == '__main__':
    main()
