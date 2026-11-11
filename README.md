# Unit 3 CAD hub

CAD models, engineering drawings and short animations for T Level Engineering, Unit 3 Engineering representations (City and Guilds 8730 Core, criteria 3.1 and 3.2). Built for the 2026-27 delivery at ACEL, Openshaw.

Every model is written in Python with [CadQuery](https://cadquery.readthedocs.io), so a size can be changed and the model, the drawings and the animations rebuilt in one go. Because every drawing is projected from the same 3D model with hidden line removal, the front view, plan, end view and isometric view always agree with each other.

## Open the hub

The website lives in the `docs` folder. To publish it (once): on GitHub open **Settings, then Pages**, set **Source** to "Deploy from a branch", choose branch `main` and folder `/docs`, then save. After a minute or two the hub is at:

`https://oogiemudia.github.io/Unit-3-Engineering-Communication/`

- `index.html`: the catalogue, with a spinning preview of each model
- `viewer.html?m=<model>`: the 3D viewer (isometric, front, plan and end views, perspective, edges, explode and section A-A)
- `viewer.html?m=<model>&tab=steps`: the Build steps tab, which rebuilds the model one stage at a time with the Autodesk Inventor command for each step (add `&step=3` to open a given step)
- `viewer.html?m=<model>&tab=sim`: the Simulation tab (moving assemblies only), an Inventor Dynamic Simulation step by step, with the motion and graphs
- `viewer.html?m=<model>&tab=fea`: the FEA tab, an Inventor Stress Analysis study of the model, step by step, with real results

## Lesson demonstrations

Three step-by-step pages for the board. Click Next, or use the arrow keys or a presentation clicker, and each idea arrives on a real 3D model. Drag to turn the model at any step. A step can be linked to directly, for example `lines.html#3`.

| Page | What it shows | Lesson slides |
|---|---|---|
| `auxiliary.html` | How an auxiliary view works, in nine steps: the part, the front view (the sloping face is just a line), the plan (the hole looks oval), the line of sight at 90° to the face, the view square on (the true shape), the front view on a sheet of glass, a second sheet parallel to the sloping face, the second sheet folding flat beside the front view, and the finished drawing. Uses the block from slide 85 (`auxiliary.html`) or the vee block (`auxiliary.html?m=vee_block`). | 84, 85 |
| `lines.html` | Line types on a real view: each click adds the next type of line to the step block (construction, outline, hidden detail, centre line, projection, dimension, leader), ending on the finished front view from slide 87. Hidden detail and the centre line sit where the hole really is, inside the see-through block. | 86, 87 |
| `scale.html` | Scale: the real part beside its drawing on an A4 sheet at 1:1, 2:1, 5:1 (too big for the sheet), 1:2, 1:5 and 1:10, then 2:1, 1:1, 1:2 and 1:5 side by side on an A3 sheet. "Hold the part up to the drawing" lays the real part over its drawing so the difference in size is plain. Works for the step block, the vee block and the slide 85 block (`?m=`). | Part 3, scale |

The views in the demonstrations come from the same CAD models as everything else, through `tools/demos.py`, so they agree with the drawing sheets and the 3D viewer. The 3D viewer links to the demonstrations that use the model on screen.

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
| Machine vice | 3.1, 3.2 | A 17-part assembly (our own design, of the kind found in online CAD libraries): parts list, section through the lead screw, standard fasteners, Inventor build steps part by part then the assembly, Dynamic Simulation of the screw closing the jaw, and Stress Analysis of the moving jaw. | third angle, first angle, section A-A | turntable, views, explode, section |

## ESP 2023 lock gates (Employer-Set Project, Task 2)

The ESP 2023 project (8730-035, Summer 2023: new automated lock gates for Canal Heritage) keeps every file it generates in one folder, `docs/ESP 2023/`, with its own project page (`docs/ESP 2023/index.html`). Its models also appear in the catalogue under the ESP 2023 filter. Every component is its own part model (41 parts, `esp2023_p01_heel_post` to `esp2023_p41_cill`), each with build steps, a drawing with a key sizes table and a STEP file; these show only under the ESP 2023 filter. In the 3D viewer the GA and the gate leaf have a parts list: click a part to open it, or untick it to hide it.

| Model | Criteria | Use it for | Drawings | Animations |
|---|---|---|---|---|
| ESP 2023 lock gates (GA) | 3.1, 3.2 | The preferred design: a pair of steel mitre gates assembled from 41 parts (120 in all): leaves, paddles, hinges, encoders, electric drives, chambers, CCTV and call points. Simulation of the paddles and gates. | dimensioned GA at 1:50, hinge and seal details, parts list, third angle, first angle | turntable, views, simulation |
| ESP 2023 gate leaf | 3.1, 3.2 | One leaf assembled from its 19 parts: welded frame, fenders, walkway, seals, bush and paddle. | dimensioned leaf sheet, third angle, first angle, section A-A | turntable, views, section |
| ESP 2023 part 01 to 41 | 3.1 | Every component on its own. Part 20 (bottom pintle) has the FEA. | one sheet each with a key sizes table | still |
| ESP 2023 skin plate panel | 3.2 | FEA with true hydrostatic pressure, checked against Roark (within 2 %). | third angle, first angle | turntable, views |
| ESP 2023 concept B: lift gate | 3.1 | The second design idea for Part A. | design ideas sheet, third angle, first angle | turntable, views |

The folder also holds the supporting calculations and design notes (PDF). See `docs/ESP 2023/README.md`. A model joins a project folder by setting `folder` in its `MODELS` entry: the build tools then write all its files there.

## ESP 2026 economy seat set (Employer-Set Project, Task 2)

The ESP 2026 project (8730-035, Summer 2026: an economy class three-seat set for Aero-Chair Ltd) keeps every file it generates in `docs/ESP 2026/`, with its own project page (`docs/ESP 2026/index.html`), and shows in the catalogue under the ESP 2026 filter. Every component is its own part model (39 parts, `esp2026_p01_beam_tube` to `esp2026_p39_life_vest`), each with build steps, a drawing with a key sizes table and a STEP file. Drawing numbers use the prefix ESP26 (set per folder in `PROJECTS` in `tools/drawings.py`).

| Model | Criteria | Use it for | Drawings | Animations |
|---|---|---|---|---|
| ESP 2026 three-seat set (GA) | 3.1, 3.2 | The preferred design: beam and leg seat set assembled from 39 parts (128 in all). Simulation of the recline, armrests and trays. | GA at 1:10, single seat section, mechanism details, parts list, third angle, first angle | turntable, views, simulation |
| ESP 2026 single seat | 3.1, 3.2 | The middle seat on its own: cushion, carbon back, head rest, recline lock, belt, tray, screen, pocket, life vest. | third angle, first angle, section A-A | turntable, views, section |
| ESP 2026 sub-assembly 1 to 7 | 3.1, 3.2 | How the set goes together: frame, seat pan, seat back, recline lock, armrest, lap belt and life vest pouch, each built part by part, with an exploded view. | standard sheets; exploded sheet GA-06, structure and order GA-07 | turntable, views, explode |
| ESP 2026 part 01 to 39 | 3.1 | Every component on its own. Part 4 (leg) has the FEA (9 g forward), checked by a hand truss calculation. | one sheet each with a key sizes table | still |
| ESP 2026 concept B: fixed shell seats | 3.1 | The second design idea for Part A. | design ideas sheet, third angle, first angle | turntable, views |

The folder also holds the Part A calculations (cost, weight, size, seat height) and the Part B reflective notes (PDF). See `docs/ESP 2026/README.md`.

## ESP 2024 harbour buoy (Employer-Set Project, Task 2)

The ESP 2024 project (8730-035, Summer 2024: a solar powered harbour marker buoy for Harbour Shipping Ltd) keeps every file it generates in `docs/ESP 2024/`, with its own project page (`docs/ESP 2024/index.html`), and shows in the catalogue under the ESP 2024 filter. Every component is its own part model (43 parts, `esp2024_p01_float_hull` to `esp2024_p43_sinker_eye`), each with build steps, a drawing with a key sizes table and a STEP file. Drawing numbers use the prefix ESP24.

| Model | Criteria | Use it for | Drawings | Animations |
|---|---|---|---|---|
| ESP 2024 harbour buoy (GA) | 3.1, 3.2 | The preferred design (red, leaving the harbour), assembled from 43 parts (77 in the buoy). Simulation of the buoy rolling and drifting off when the chain breaks. | GA, float section, details, parts list, third angle, first angle, section A-A | turntable, views, section, simulation |
| ESP 2024 harbour buoy, green | 3.1 | The entrance buoy: green float and lens, cone topmark. | third angle, first angle | turntable, views |
| ESP 2024 sub-assembly 1 to 7 | 3.1, 3.2 | How the buoy goes together: float, equipment canister, tail, mast, lantern and topmark, mooring, and the sinker, each built part by part, with an exploded view. | standard sheets; exploded sheet GA-06, structure and order GA-07 | turntable, views, explode |
| ESP 2024 part 01 to 43 | 3.1 | Every component on its own. Part 23 (mooring eye) has the FEA at the chain breaking load, checked by hand. | one sheet each with a key sizes table | still |
| ESP 2024 concept B: wind powered spherical buoy | 3.1 | The second design idea for Part A. | design ideas sheet, third angle, first angle | turntable, views |

The folder also holds the Part A calculations (energy produced against energy needed, floating and stability, mooring loads, cost, time) and the Part B reflective notes (PDF). See `docs/ESP 2024/README.md`.

## ESP 2025 automated pill dispenser (Employer-Set Project, Task 2)

The ESP 2025 project (an automated pill dispenser for WBEP Ltd and a health trust) keeps every file it generates in `docs/ESP 2025/`, with its own project page (`docs/ESP 2025/index.html`), and shows in the catalogue under the ESP 2025 filter. Every component is its own part model (37 parts, `esp2025_p01_chassis` to `esp2025_p37_drawer_seal`), each with build steps, a drawing with a key sizes table and a STEP file. Drawing numbers use the prefix ESP25.

| Model | Criteria | Use it for | Drawings | Animations |
|---|---|---|---|---|
| ESP 2025 automated pill dispenser (GA) | 3.1, 3.2 | The preferred design, assembled from 37 different parts. Simulation of a dose being dispensed and the pharmacy unlocking the lid to refill it. | GA, sections, details, parts list, third angle, first angle, section A-A | turntable, views, section, simulation |
| ESP 2025 sub-assembly 1 to 6 | 3.1, 3.2 | How the dispenser goes together: chassis and lock, carousel, base with batteries and drive, control pod, lid, drawer, each built part by part, with an exploded view. | standard sheets; exploded sheet GA-06, structure and order GA-07 | turntable, views, explode |
| ESP 2025 part 01 to 37 | 3.1 | Every component on its own. Part 34 (lid catch) has the FEA for someone forcing the locked lid, checked by hand. | one sheet each with a key sizes table | still |
| ESP 2025 concept B: trapdoor cassette | 3.1 | The second design idea for Part A. | design ideas sheet, third angle, first angle | turntable, views |

The folder also holds the Part A calculations (size and mass, capacity, battery life, drive, cost and the most units each budget buys, programme) and the Part B reflective notes (PDF). See `docs/ESP 2025/README.md`.

For each model the `docs` folder holds:

| Folder | Contents |
|---|---|
| `step/` | STEP file (opens in Fusion, Inventor, SolidWorks, Onshape, FreeCAD) |
| `stl/` | STL file (3D printing, quick viewing) |
| `glb/` | glTF file used by the web viewer |
| `drawings/` | A3 drawing sheets as SVG (editable) and PNG: third angle, first angle, and section A-A where useful |
| `media/` | Isometric still (PNG) and silent MP4 clips, 1280 x 720 |
| `sim/` | The Simulation tab: one JSON file per moving assembly with the Inventor steps, the motion and the graphs |
| `fea/` | The FEA tab: one JSON file per model with the load case, the Inventor steps, the surface mesh and the results |
| `steps/` | The Build steps tab: one JSON file per model with the Inventor commands, and a GLB and edges file for every stage |

## Drawing conventions used

- Projection: first and third angle, with the projection symbol in the title block (BS 8888:2025, ISO 5456-2).
- Lines: thick continuous for visible outlines, thin dashed for hidden detail, thin chain (shown in blue) for centre lines (ISO 128 series).
- Sections: cutting plane A-A shown on the plan, hatching at 45 degrees, touching parts hatched in opposite directions, standard parts (bolts, nuts, washers, pins, rods, springs) not sectioned.
- Threads: drawn by convention, thick line at the major diameter and thin line at the minor diameter, three-quarter circle in the end view.
- Title block: the fields from ISO 7200:2004 (legal owner, title, identification number, document type, created by, approved by, date of issue, revision, sheet), plus scale, units, material and projection.
- Sizes: overall sizes only. Full dimensioning and tolerancing belong to criterion 3.2 and will be added as 3.2 resources are built.

Simplifications: bolts and nuts are simplified (no thread helix), and the threaded shaft is modelled at the major diameter, which is how CAD packages show a cosmetic thread.

## Build steps (Autodesk Inventor)

The Build steps tab in the viewer takes a learner through making each model in Autodesk Inventor, one feature at a time. Each step gives the command (for example Extrude, Hole, Circular Pattern, Coil or Constrain), where it sits on the ribbon, and the clicks and values to enter. The 3D view shows the model after that step: sketches appear as a flat amber profile, material the step adds is amber, material it cuts away is shown in see-through red, and in assembly steps the parts already placed turn see-through so the new part stands out.

The steps are written in `models/inventor_steps.py`. Plane names follow Inventor's default (Y up): the XY Plane is the front, the XZ Plane is the top and the YZ Plane is the side. The stage models are made in CadQuery with the same operations as `models/parts.py`, so they are a guide to the Inventor workflow rather than Inventor files. To change a step, edit `models/inventor_steps.py` and run `python3 tools/build_steps.py <model>`.

## Simulation (Inventor Dynamic Simulation)

The bolted joint, the pin and housing fit and the pneumatic cylinder move, so they have a Simulation tab. It takes a learner through an Inventor Dynamic Simulation: open the environment, turn the assembly constraints into joints, add a spring or a screw joint, drive a joint with imposed motion from the Input Grapher, run the Simulation Player, plot the results in the Output Grapher and record a video. In the viewer the moving parts are highlighted, the fixed parts turn see-through, and Play runs the same motion with a live graph of position and force. The steps and motion are in `tools/build_sim.py`. Single parts do not move, so they have the FEA tab instead.

## FEA (Inventor Stress Analysis)

The FEA tab takes a learner through a static stress analysis in Autodesk Inventor: open the Stress Analysis environment, create a study, assign the material, fix the part, apply the load, set up and view the mesh, run it, then read the von Mises stress, displacement and safety factor and write the report. Each step shows the matching picture: fixed faces in blue, loaded faces in amber with arrows, the mesh, and colour plots of the results on the deformed shape.

The load cases are in `models/fea_cases.py` (which part, material, fixed faces and loads, with a one line story). `tools/build_fea.py` meshes each part with gmsh, solves linear elasticity with 10 node tetrahedra in scikit-fem, and writes `docs/fea/<model>.json`. The solver was checked against a cantilever hand calculation (tip deflection within 0.2 %). Inventor's own answers will be close but not identical, because its mesh is different: that is a useful discussion point.

## Rebuild everything

```bash
pip install cadquery trimesh playwright   # Playwright needs Chromium: python -m playwright install chromium
# also needed: ffmpeg and rsvg-convert (librsvg)
python3 tools/build_models.py   # STEP, STL, GLB, edges, docs/models.json
python3 tools/drawings.py       # drawing sheets (SVG and PNG)
python3 tools/build_steps.py    # Build steps tab: a model of every stage (checks the last stage matches the finished model)
python3 tools/build_sim.py      # Simulation tab: Dynamic Simulation steps and motion for the moving assemblies
python3 tools/build_fea.py      # FEA tab: mesh and solve each load case (needs gmsh and scikit-fem)
python3 tools/render.py         # stills and MP4 animations
python3 tools/demos.py          # views for the lesson demonstrations (docs/demos/data.json)
python3 tools/render.py step_block --bg FDF6E3 --suffix _cream   # cream background for the dyslexia friendly decks
```

To add a model, write a function in `models/parts.py` that returns a list of `(part name, CadQuery shape, colour)` and add an entry to `MODELS`.

## Credits

Models, drawings and animations made for this course. The web viewer uses [three.js](https://threejs.org) (MIT licence, see `docs/vendor/THREE_LICENSE.txt`).
