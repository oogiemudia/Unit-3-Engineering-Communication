"""Render stills and short animations of every model in a headless browser, using docs/viewer.html.

Output (docs/media): <name>_iso.png (hub thumbnail), <name>_turntable.mp4, <name>_views.mp4, and, where the model
has them, <name>_explode.mp4 and <name>_section.mp4. Videos are H.264, 1280 x 720, 24 frames a second, silent.

Run from the repository root:  python3 tools/render.py [model names] [--bg FDF6E3 --suffix _cream] [--only step_block_views,...]
"""
import functools, http.server, json, math, os, subprocess, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
MEDIA = os.path.join(DOCS, 'media')
os.makedirs(MEDIA, exist_ok=True)
FPS = 24
W, H = 1280, 720


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def lerp(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]


ISO = [1, 1, 1]
VIEWS = [('front', [0, 0, 1], 'Front view'), ('plan', [0, 1, 0.0001], 'Plan'), ('right', [1, 0, 0], 'End view from the right')]


def turntable(iso, n=120):
    out = []
    a0 = math.atan2(iso[0], iso[2])
    for k in range(n):
        a = 2 * math.pi * k / n + a0
        out.append(dict(dir=[math.sin(a) * 1.41, 1, math.cos(a) * 1.41], caption=''))
    return out


def views(iso):
    out = []
    for name, d, cap in VIEWS:
        out += [dict(dir=lerp(iso, d, ease(k / 24)), caption='') for k in range(25)]
        out += [dict(dir=d, caption=cap) for _ in range(36)]
        out += [dict(dir=lerp(d, iso, ease(k / 18)), caption='') for k in range(19)]
    out += [dict(dir=iso, caption='Isometric view') for _ in range(30)]
    return out


def explode(iso):
    out = [dict(dir=iso, explode=0, caption='Assembled') for _ in range(24)]
    out += [dict(dir=iso, explode=ease(k / 36), caption='') for k in range(37)]
    out += [dict(dir=iso, explode=1, caption='Exploded view') for _ in range(48)]
    out += [dict(dir=iso, explode=1 - ease(k / 36), caption='') for k in range(37)]
    out += [dict(dir=iso, explode=0, caption='Assembled') for _ in range(12)]
    return out


def section(front):
    fd = [0.45, 0.35, 1]
    out = [dict(dir=fd, section=False, caption='The part') for _ in range(24)]
    out += [dict(dir=fd, section=True, depth=front * (1 - ease(k / 48)) + 0.01, caption='Cutting plane A-A')
            for k in range(49)]
    out += [dict(dir=lerp(fd, [0, 0, 1], ease(k / 30)), section=True, depth=0.0, caption='') for k in range(31)]
    out += [dict(dir=[0, 0, 1], section=True, depth=0.0, caption='Section A-A') for _ in range(54)]
    return out


def encode(frames_dir, out):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames_dir, 'f%04d.png'),
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    out], check=True)


def run(names, bg='F4F6F8', suffix='', kinds=None):
    cat = json.load(open(os.path.join(DOCS, 'models.json')))
    srv = serve()
    port = srv.server_address[1]
    tmp = os.path.join(ROOT, '.frames')
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = b.new_page(viewport=dict(width=W, height=H))
        for m in cat:
            if names and m['name'] not in names:
                continue
            pg.goto('http://127.0.0.1:%d/viewer.html?m=%s&render=1&w=%d&h=%d&bg=%s' % (port, m['name'], W, H, bg))
            pg.wait_for_function('window.U3 && window.U3.ready', timeout=120000)
            front = pg.evaluate('window.U3.front')
            iso = pg.evaluate('window.U3.iso')
            jobs = [('turntable', turntable(iso)), ('views', views(iso))]
            if m.get('exploded'):
                jobs.append(('explode', explode(iso)))
            if m.get('section'):
                jobs.append(('section', section(front)))
            pg.evaluate('s => window.U3.setState(s)', dict(dir=iso, explode=0, section=False, caption=''))
            pg.screenshot(path=os.path.join(MEDIA, '%s_iso%s.png' % (m['name'], suffix)))
            for kind, frames in jobs:
                if kinds and '%s_%s' % (m['name'], kind) not in kinds:
                    continue
                d = os.path.join(tmp, m['name'] + '_' + kind + suffix)
                os.makedirs(d, exist_ok=True)
                pg.evaluate('s => window.U3.setState(s)', dict(explode=0, section=False))
                for k, st in enumerate(frames):
                    pg.evaluate('s => window.U3.setState(s)', st)
                    pg.screenshot(path=os.path.join(d, 'f%04d.png' % k))
                encode(d, os.path.join(MEDIA, '%s_%s%s.mp4' % (m['name'], kind, suffix)))
                subprocess.run(['rm', '-rf', d])
                print(m['name'], kind, len(frames), 'frames', flush=True)
        b.close()
    srv.shutdown()


if __name__ == '__main__':
    args = sys.argv[1:]
    bg, suffix = 'F4F6F8', ''
    if '--bg' in args:
        i = args.index('--bg'); bg = args[i + 1]; del args[i:i + 2]
    if '--suffix' in args:
        i = args.index('--suffix'); suffix = args[i + 1]; del args[i:i + 2]
    kinds = None
    if '--only' in args:
        i = args.index('--only'); kinds = args[i + 1].split(','); del args[i:i + 2]
        args = args or sorted(set(k.rsplit('_', 1)[0] for k in kinds))
    run(args, bg, suffix, kinds)
