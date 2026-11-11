"""Write docs/Additional CAD exercise/index.html: the folder page for the Additional CAD exercise models.

The model cards are filled in by the page from docs/models.json. The reading notes (the sizes chosen where a drawing
leaves one out or disagrees with itself) come from each model's note in models/exercises.py, and the source drawings
are the images in the folder's "source drawings" subfolder. Run from the repository root:
    python3 tools/build_exercise_page.py
"""
import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import parts  # noqa: E402,F401  (parts first: it loads the exercises)
import exercises as ex  # noqa: E402

FOLDER = os.path.join(ROOT, 'docs', ex.FOLDER)

# the drawings as they were supplied: file in "source drawings/", what it shows, and the credit marked on it
SOURCES = {
    'turkish': ('exercise_sheet_T8_T9_T10.png', 'Exercise sheet "Uygulama 8, 9, 10" (six parts)',
                'Turkish technical drawing textbook exercise sheet'),
    'roller': ('roller_assembly.png', 'Roller assembly, drawing RA_01', 'Textbook assembly exercise (no sizes on the sheet)'),
    'valve_body': ('valve_body.png', 'Valve body', 'CAD CAM Tutorial by Mahtabalam (SolidWorks)'),
    'jack': ('machinists_jack.png', "Machinist's jack", 'CAD CAM Tutorial by Mahtabalam (SolidWorks assembly)'),
    'planetary': ('planetary_gears.png', 'Planetary gear assembly', 'CAD CAM Tutorial by Mahtabalam (SolidWorks)'),
    'bracket_45': ('tube_bracket_45.png', 'Bracket with a 45 degree tube', 'CAD practice exercise (no credit on the sheet)'),
    'angle_bracket': ('angle_bracket.png', 'Angle bracket (inches)', 'Trazoide Industrial'),
    'crankshaft_4': ('crankshaft_4.png', 'Cigüeñal (crankshaft), sheet 4 of 7', 'Planos, Conjunto Automoción (Spanish drawing set)'),
    'crankshaft_3': ('crankshaft_3.png', 'Three throw crankshaft (inches)', 'SolidWorks drawing (no credit on the sheet)'),
    'v_pulley': ('v_pulley.png', 'V-belt pulley (inches)', 'SolidWorks Guide for Beginners'),
    'pipe_run': ('pipe_run.png', 'Pipe run with valves', 'Computer generated sketch (sizes do not agree)'),
    'steam_line': ('steam_line.png', 'Sample piping isometric with a bill of materials', 'Poster "Isometric drawings: turning P&ID into reality on site"'),
    'oil_pan': ('oil_pan.png', 'Engine oil pan (overall inch sizes)', 'Product drawing (no credit on the sheet)'),
    'engine_block': ('engine_block.png', 'Engine block deck plan (inches)', 'Engineering blueprint (no credit on the sheet)'),
    'helicopter': ('helicopter.png', 'Helicopter concept sketch', 'Concept sketch (no usable sizes)'),
}

CSS = """:root{--bg:#F4F6F8;--card:#FFFFFF;--ink:#16335B;--text:#1F2A37;--muted:#4E5A68;--line:#D5DCE4;--accent:#1565D8;--amber:#E8A33D}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif;line-height:1.5}
header{background:var(--ink);color:#fff;padding:26px 16px 22px}
.wrap{max-width:1200px;margin:0 auto;padding:0 16px}
header .wrap{padding:0}
header a{color:#BFD6F6}
h1{margin:4px 0 6px;font-size:28px}
header p{margin:0;max-width:820px;color:#DCE6F2}
h2{color:var(--ink);font-size:21px;margin:26px 0 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:16/9;object-fit:cover;background:#F4F6F8;border-bottom:1px solid var(--line)}
.card .b{padding:10px 12px 12px;display:flex;flex-direction:column;gap:6px;flex:1}
.card h3{margin:0;font-size:17px;color:var(--ink)}
.card p{margin:0;font-size:14px;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12px;background:#E8EEF6;color:var(--ink);border-radius:999px;padding:2px 9px}
.links{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:14px;margin-top:auto;padding-top:4px}
.links+.links{margin-top:0}
a{color:var(--accent)}
a.btn{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;border-radius:8px;padding:5px 10px;font-weight:bold;font-size:14px}
.box{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--amber);border-radius:8px;padding:12px 16px;font-size:15px}
.box p{margin:0 0 8px}.box p:last-child{margin:0}
.src img{aspect-ratio:4/3;object-fit:contain;background:#fff}
table{border-collapse:collapse;width:100%;background:var(--card);font-size:14px}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:8px}
th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{background:#E8EEF6;color:var(--ink)}
tr:last-child td{border-bottom:0}
footer{color:var(--muted);font-size:13px;padding:26px 0 30px}"""

SCRIPT = """<script>
fetch('../models.json').then(r => r.json()).then(cat => {
  const ms = cat.filter(m => m.folder === 'Additional CAD exercise' && !m.part);
  const q = s => encodeURIComponent(s).replace(/%%2F/g, '/');
  const src = %s;
  document.getElementById('grid').innerHTML = ms.map(m => {
    const base = '../' + q(m.base || '');
    const d = m.drawings || {};
    const dl = [['third', 'Third angle'], ['first', 'First angle'], ['section', 'Section']]
      .filter(([k]) => d[k]).map(([k, t]) => `<a href="../${q(d[k])}.png">${t}</a>`).join(' ');
    const v = 'viewer.html?m=' + m.name;
    const n = m.parts.length;
    const vids = [['turntable', 'Spin'], ['views', 'Views']].concat(m.exploded ? [['explode', 'Exploded']] : [])
      .concat(m.section ? [['section', 'Section cut']] : []).concat(m.sim ? [['sim', 'Simulation']] : [])
      .map(([k, t]) => `<a href="${base}media/${m.name}_${k}.mp4">${t}</a>`).join(' ');
    return `<div class="card"><a href="../${v}"><img src="${base}media/${m.name}_iso.png" alt="${m.title}" loading="lazy"></a><div class="b">
      <h3>${m.title}</h3><div class="chips"><span class="chip">${n === 1 ? 'Single part' : n + ' parts'}</span><span class="chip">${m.size_mm.map(Math.round).join(' x ')} mm</span></div>
      <p>${m.description}</p>
      <div class="links"><a class="btn" href="../${v}">3D viewer</a><a href="../${v}&tab=steps">Build steps</a>${m.sim ? `<a href="../${v}&tab=sim">Simulation</a>` : ''}<a href="../${v}&tab=fea">FEA</a></div>
      <div class="links">Drawings: ${dl} · <a href="../${q(m.files.step)}">STEP</a> · <a href="source%%20drawings/${src[m.name]}">Source drawing</a></div>
      <div class="links">Videos: ${vids}</div></div></div>`;
  }).join('');
});
</script>"""


def main():
    rows = []
    for name, meta in ex.META.items():
        m = meta['fn']()
        file, what, credit = SOURCES[meta['source']]
        note = m.get('note') or 'Modelled to the sizes on the drawing.'
        rows.append('<tr><td>%s</td><td><a href="source%%20drawings/%s">%s</a></td><td>%s</td></tr>'
                    % (html.escape(meta['title']), file, html.escape(what), html.escape(note)))
    cards = []
    for key, (file, what, credit) in SOURCES.items():
        cards.append('<div class="card src"><a href="source%%20drawings/%s"><img src="source%%20drawings/%s" alt="%s" loading="lazy"></a>'
                     '<div class="b"><h3>%s</h3><p>%s</p></div></div>'
                     % (file, file, html.escape(what), html.escape(what), html.escape(credit)))
    src_map = '{' + ', '.join("'%s': '%s'" % (n, SOURCES[v['source']][0]) for n, v in ex.META.items()) + '}'
    page = """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Additional CAD exercise</title>
<meta name="description" content="CAD models of fifteen exercise drawings (textbook sheets, tutorial drawings, piping isometrics and a concept sketch): 20 models with drawings, Inventor build steps, FEA, simulations and STEP files.">
<style>
%s
</style>
</head>
<body>
<header><div class="wrap">
  <a href="../index.html">Unit 3 CAD hub</a>
  <h1>Additional CAD exercise</h1>
  <p>Fifteen exercise drawings, modelled in 3D: textbook sheets, tutorial drawings in millimetres and inches, two piping isometrics, an engine oil pan, an engine block deck and a helicopter concept sketch. The exercise sheet "Uygulama 8, 9, 10" holds six parts, so there are 20 models: 15 single parts and 5 assemblies.</p>
</div></header>
<main class="wrap">
<h2>What each model has</h2>
<div class="box"><p>Each model is built feature by feature as in Autodesk Inventor (the Build steps tab), and each assembly keeps every component as its own part, with a parts list. Every model has third angle and first angle drawings (and a section where it helps), a STEP file, turntable and views videos, and an Inventor Stress Analysis of one part checked by hand. The five assemblies that move (roller, machinist's jack, planetary gears, pipe run with valves and helicopter) also have a Dynamic Simulation.</p>
<p>Inch drawings are converted to millimetres (1 in = 25.4 mm). Where a drawing leaves a size out, or two of its sizes disagree, the size used is given below and in the build step that uses it.</p></div>
<h2>Models</h2>
<div class="grid" id="grid"><p>Loading…</p></div>
<h2>How each drawing was read</h2>
<div class="tw"><table>
<tr><th>Model</th><th>Drawing</th><th>Sizes chosen and things to know</th></tr>
%s
</table></div>
<h2>Source drawings</h2>
<div class="box">These are the drawings the models were made from, as they were supplied. The credit is the one marked on each sheet; the drawings belong to their authors and are here so the models can be checked against them.</div>
<div class="grid" style="margin-top:16px">
%s
</div>
</main>
<footer class="wrap">Files for every model (STEP, STL, GLB, drawings as SVG and PNG, videos, build steps, FEA and simulation data) are in this folder of the repository: docs/Additional CAD exercise/. The models are built by models/exercises.py.</footer>
%s
</body>
</html>
""" % (CSS, '\n'.join(rows), '\n'.join(cards), SCRIPT % src_map)
    with open(os.path.join(FOLDER, 'index.html'), 'w') as f:
        f.write(page)
    print('wrote', os.path.join(FOLDER, 'index.html'))


if __name__ == '__main__':
    main()
