# Unit 3 CAD hub

CAD models, engineering drawings and short animations for T Level Engineering, Unit 3 Engineering representations (City and Guilds 8730 Core, criteria 3.1 and 3.2). Built for the 2026-27 delivery at ACEL, Openshaw.

Every model is written in Python with [CadQuery](https://cadquery.readthedocs.io), so a size can be changed and the model, the drawings and the animations rebuilt in one go. Because every drawing is projected from the same 3D model with hidden line removal, the front view, plan, end view and isometric view always agree with each other.

## Open the hub

The website lives in the `docs` folder. To publish it (once): on GitHub open **Settings, then Pages**, set **Source** to "Deploy from a branch", choose branch `main` and folder `/docs`, then save. After a minute or two the hub is at:

`https://oogiemudia.github.io/Unit-3-Engineering-Communication/`

- `index.html`: the catalogue, with a spinning preview of each model
- `viewer.html?m=<model>`: the 3D viewer (isometric, front, plan and end views, perspective, edges, explode and section A-A)

## What is in it

| Model | Criteria | Use it for | Drawings | Animations |
|---|---|---|---|---|
| Step block | 3.1 | Isometric drawing, first and third angle projection, the glass box, Activity 1. | third angle, first angle | turntable, views |
| Sloping block | 3.1 | Auxiliary views: why a hole on a sloping face looks oval until it is viewed square on. | third angle, first angle | turntable, views |
| Flanged bush | 3.1, 3.2 | Full section A-A, hatching, centre lines, repeated holes on a PCD. | third angle, first angle, section A-A | turntable, views, section |
| Bolted joint | 3.1 | Assembly and general arrangement drawings, exploded views, parts lists, standard fasteners. | third angle, first angle, section A-A | turntable, views, explode, section |
| Threaded shaft | 3.1, 3.2 | Screw thread conventions, undercuts, chamfers, keyways, detail views. | third angle, first angle | turntable, views |
| PCD flange | 3.1, 3.2 | Pitch circle diameter, equally spaced holes, centre marks, half sections. | third angle, first angle, section A-A | turntable, views, section |
| Annotation plate | 3.1, 3.2 | Activity 5: countersinks, a bore with a chamfer, centre marks, hole notes and abbreviations. | third angle, first angle, section A-A | turntable, views, section |
| Hole features block | 3.1 | Clearance hole, counterbore (CBORE), countersink (CSK) and a blind tapping drill hole, side by side. | third angle, first angle, section A-A | turntable, views, section |
| Vee block | 3.1 | Orthographic practice: a vee, a relief slot and hidden detail. | third angle, first angle | turntable, views |
| L bracket | 3.1, 3.2 | Bent plate with an inside radius, a slot and a hole: views, hidden detail and dimensioning. | third angle, first angle | turntable, views |
| Pin and housing fit | 3.2 | Limits and fits: a 20 H7 hole and a 20 g6 pin, clearance fit. | third angle, first angle, section A-A | turntable, views, explode, section |
| Pneumatic cylinder | 3.1 | The real component behind the single-acting, spring-return cylinder symbol (ISO 1219-1:2012). | third angle, first angle, section A-A | turntable, views, explode, section |

For each model the `docs` folder holds:

| Folder | Contents |
|---|---|
| `step/` | STEP file (opens in Fusion, Inventor, SolidWorks, Onshape, FreeCAD) |
| `stl/` | STL file (3D printing, quick viewing) |
| `glb/` | glTF file used by the web viewer |
| `drawings/` | A3 drawing sheets as SVG (editable) and PNG: third angle, first angle, and section A-A where useful |
| `media/` | Isometric still (PNG) and silent MP4 clips, 1280 x 720 |

## Drawing conventions used

- Projection: first and third angle, with the projection symbol in the title block (BS 8888:2025, ISO 5456-2).
- Lines: thick continuous for visible outlines, thin dashed for hidden detail, thin chain (shown in blue) for centre lines (ISO 128 series).
- Sections: cutting plane A-A shown on the plan, hatching at 45 degrees, touching parts hatched in opposite directions, standard parts (bolts, nuts, washers, pins, rods, springs) not sectioned.
- Threads: drawn by convention, thick line at the major diameter and thin line at the minor diameter, three-quarter circle in the end view.
- Title block: the fields from ISO 7200:2004 (legal owner, title, identification number, document type, created by, approved by, date of issue, revision, sheet), plus scale, units, material and projection.
- Sizes: overall sizes only. Full dimensioning and tolerancing belong to criterion 3.2 and will be added as 3.2 resources are built.

Simplifications: bolts and nuts are simplified (no thread helix), and the threaded shaft is modelled at the major diameter, which is how CAD packages show a cosmetic thread.

## Rebuild everything

```bash
pip install cadquery trimesh playwright   # Playwright needs Chromium: python -m playwright install chromium
# also needed: ffmpeg and rsvg-convert (librsvg)
python3 tools/build_models.py   # STEP, STL, GLB, edges, docs/models.json
python3 tools/drawings.py       # drawing sheets (SVG and PNG)
python3 tools/render.py         # stills and MP4 animations
python3 tools/render.py step_block --bg FDF6E3 --suffix _cream   # cream background for the dyslexia friendly decks
```

To add a model, write a function in `models/parts.py` that returns a list of `(part name, CadQuery shape, colour)` and add an entry to `MODELS`.

## Credits

Models, drawings and animations made for this course. The web viewer uses [three.js](https://threejs.org) (MIT licence, see `docs/vendor/THREE_LICENSE.txt`).
