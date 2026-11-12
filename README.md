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

**Hidden detail in the 3D viewer.** A shaded model covers the edges behind it, so on its own the viewer could not show hidden detail. `tools/build_hidden.py` runs the same hidden line removal as the drawing sheets for the front view, plan and both end views of every model, and saves the hidden edges and hole sides in `docs/<folder>/hidden/<model>.json`. The viewer draws them as thin dashed lines when you press Front view, Plan or End view (orthographic camera, model assembled, no section); the Hidden detail box turns them off. A hidden edge that sits exactly behind a visible edge is left out, as on a drawing. The views videos show them too.

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

## GrabCAD models

Ten complete multi-part assemblies of the kind people share in online CAD libraries such as GrabCAD. GrabCAD uploads belong to their authors, so none are copied: every model here is our own design, modelled from scratch in CadQuery (`models/library.py`, and the vice in `models/parts.py`). All their files are in `docs/GrabCAD models/`, with a folder page (`docs/GrabCAD models/index.html`) and a GrabCAD models filter in the catalogue. Drawing numbers use the prefix GC.

Each model has every component as its own part with a parts list, third angle, first angle and section drawings, Inventor build steps (every part feature by feature, then the assembly a few parts at a time), turntable, views, exploded and section videos, a Dynamic Simulation and a Stress Analysis checked by hand. Criteria 3.1 and 3.2.

| Model | Parts | What it shows |
|---|---|---|
| Machine vice | 17 | Lead screw closing a sliding jaw: section through the screw, standard fasteners. Simulation of the screw closing the jaw; FEA of the moving jaw. |
| Plummer block bearing | 24 | A split cast iron housing with a deep groove ball bearing on a shaft: half section, cap bolts, a turned shaft. Simulation of the shaft, balls and cage turning; FEA of the housing base. |
| Spur gearbox | 36 | A 20 tooth pinion driving a 40 tooth wheel (true involute teeth) in a box with bearings and covers. Simulation of the 2 to 1 reduction; FEA of the output shaft. |
| Universal joint | 15 | Two yokes and a cross with needle cups and circlips. Simulation of the output swinging 25 degrees each way; FEA of a yoke. |
| Toggle clamp | 14 | A four-bar linkage that locks past dead centre: base, arm, handle, link plates and pins. Simulation of the handle opening the arm; FEA of the clamp arm. |
| Swivel castor | 30 | A top plate on a ball race, a fork, a wheel with a tyre and an axle bolt. Simulation of the wheel rolling and the fork swivelling; FEA of the fork. |
| Screw jack | 10 | The classic screw jack: cast body, bronze bush, square thread spindle, tommy bar and load cup. Simulation of five turns lifting 30 mm; FEA of the body. |
| Flanged shaft coupling | 24 | A protected flanged coupling: two flanges with a spigot and recess, keys and six bolts on a pitch circle. Simulation of the shafts turning together; FEA of a flange keyway. |
| Knuckle joint | 9 | The classic knuckle joint drawn in proportion to the rod diameter: eye, fork, pin, collar and taper pin. Simulation of the eye swinging on the pin; FEA of the eye end in tension. |
| Piston and crank (single cylinder engine) | 25 | A single cylinder slider-crank: crankshaft, split connecting rod, piston with rings, finned barrel, head and flywheel. Simulation of the piston stroke; FEA of the connecting rod. |

## World Skill (WorldSkills UK Mechanical Engineering: CAD)

The four parts of the WorldSkills UK Mechanical Engineering: CAD pre-competition activity, the 2022 "Part Modelling Speed Test" (1 hour, create 3D models for all the parts on the drawings). It is the only practice paper WorldSkills UK has published for this competition from 2020 to 2026, and the 2025 and 2026 technical handbooks still point to it: [the 2022 activity (PDF)](https://www.worldskillsuk.org/wp-content/uploads/2022/02/Mechanical-Engineering-CAD-Pre-Passive-Activity-2022.pdf). The National Qualifier and Final papers are not published, and the handbooks' 2019 and 2018 sample projects give no part drawings.

Every part is modelled to the sizes on the competition sheets (`models/worldskill.py`) and all its files are in `docs/World Skill/`, with a folder page (`docs/World Skill/index.html`) and a World Skill filter in the catalogue. Each has Inventor build steps (feature by feature), third angle, first angle and section drawings (prefix WS), a STEP file and turntable, views and section videos. Section A-A on each hub drawing is the section on the competition sheet. `python tools/test_worldskill.py` checks over 100 sizes from the sheets against the solids (add `--browser` for the page checks).

| Part | Sheet | What it shows | Material, mass |
|---|---|---|---|
| Crank | 1 of 5 | 55 disc with a counterweight crescent recess, 11 crank pin hole 15.8 off centre, 15 shaft with a taper, a key slot and a 4 hole through. Section A-A. | Mild steel, 197 g |
| Piston head | 1 of 5 | 44 x 44 piston: SR62.5 crown 3.0 thick, two ring grooves, 17 pin bosses with an 11 hole, skirt cut-outs at 41.2 degrees. Section A-A is section C-C on the sheet. | Mild steel, 143 g |
| Pull cord grill | 2 of 5 | 95 flange, slotted cone and 75 cup, cord box 20 wide with a 6.0 cord hole, 3 x 4.0 holes. Section A-A is section D-D. | ABS, 31 g |
| Cord case | 2 of 5 | Recoil starter pulley: 49.1 cord groove, 70 flange, 40 tube and 16 hub, cord guide, six gussets, 16 pockets underneath. Section A-A is section E-E. | PEEK, 49 g |

## Additional CAD exercise

Twenty models from fifteen exercise drawings: the six parts of a textbook exercise sheet ("Uygulama 8, 9, 10"), tutorial drawings in millimetres and inches, two piping isometrics, an engine oil pan, an engine block deck and a helicopter concept sketch. They are built in `models/exercises.py` and all their files are in `docs/Additional CAD exercise/`, with a folder page (`docs/Additional CAD exercise/index.html`) that shows every source drawing (in `source drawings/`) and how each was read, and an Additional CAD exercise filter in the catalogue. Every model has Inventor build steps, third angle and first angle drawings (prefix AX), a section where it helps, a STEP file, videos and an FEA of one part with a hand check; the five that move have a Dynamic Simulation. Inch drawings are converted to millimetres. Where a drawing leaves a size out or disagrees with itself, the size used is stated in the model note, the build step and on the folder page. `python tools/test_exercises.py` checks the main sizes against the drawings (add `--browser` for the page checks), and `python tools/build_exercise_page.py` rebuilds the folder page.

| Model | Parts | What it shows |
|---|---|---|
| Fork bracket (T8) | 1 | Cast fork: 72 x 44 base, two 13 mm lugs with an 18 bore. The lugs (13 + 18 + 13 = 44) are wider than the 36 base on the sheet, so the base is 44. |
| Pedestal bearing (T8) | 1 | Base with counterbored slots, a cross shaped column and an 18 bore in a 36 boss. |
| Slotted boss flange (T9) | 1 | Flange with a slotted 40 boss and a 26 bore. |
| Boss bracket (T9) | 1 | Two bolting lugs, a rib and a 50 boss with a cross hole. |
| Saddle bearing block (T10) | 1 | 120 x 96 base with a stepped R28 / R20 saddle. |
| Split clamp lever (T10) | 1 | Split clamp boss on a 28 shaft with a pinch bolt and a slotted arm. |
| Roller assembly | 11 | Base, two brackets, spindle, bronze bushes, cast roller and M10 bolts (no sizes on the sheet: scaled from the bolts). Simulation of the roller turning. |
| Valve body | 1 | AISI 316L valve body with two round flanges, an oval top flange and a side port. |
| Machinist's jack | 6 | Base with lugs, swivel, M16 pivot bolt and nut, M20 screw and lock nut. Simulation of the screw rising and the swivel tilting. |
| Planetary gear set | 12 | Module 1: 12 tooth sun, three 24 tooth planets, 60 tooth ring, carrier, bearings and lock nuts. Simulation of the 6 to 1 reduction. |
| Tube bracket, 45 degree | 1 | Base, upright tube and a 45 degree tube with a square flange. |
| Angle bracket (inches) | 1 | Cast bracket with a channel column, a 30 degree top plate and a side boss. |
| Crankshaft, four cylinder | 1 | 619 long, five 64 journals, four pins on a 44 throw, counterweighted webs, flywheel flange. |
| Crankshaft, three throw (inches) | 1 | Three pins at 120 degrees, pear shaped webs, 564.88 long. |
| V-belt pulley (inches) | 1 | 80 degree groove, web with eight lightening holes, hub and bore. |
| Pipe run with three gate valves | 74 | 70 mm pipe, bends, three flanged gate valves (body, bonnet, stem and gate, handwheel), slip-on flanges, M16 bolting. Simulation of the valves opening. |
| Steam line loop | 64 | Schedule 40 pipe (8, 6 and 4 inch), long radius elbows, reducers, a 6 x 4 tee, gate, ball and needle valves, weld neck flanges and two pipe supports, from the isometric's bill of materials. |
| Engine oil pan | 1 | Shelled sump with a bolting flange, shallow and deep sections, filter and drain bosses. |
| Engine block deck | 1 | Four 3.684 in bores at 4.85 in centres, head bolt and push rod holes, water jacket. |
| Light helicopter (concept) | 15 | Cabin pod and canopy, cowling, tail boom, fin with a ducted fan, rotor and skids, to proportion only. Simulation of the rotors running up. |

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
python3 tools/build_hidden.py   # hidden detail for the viewer's front, plan and end views (run before render.py)
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
