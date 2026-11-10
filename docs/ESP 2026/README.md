# ESP 2026: economy class three-seat set

T Level Design and Development Employer-Set Project (8730-035), Summer 2026, Task 2. Aero-Chair Ltd designs an economy class three-seat set for a short haul aircraft: seats 432 to 457 mm wide, at most 8 kg a seat, a 3 to 6 degree manual recline, lap belt, tray table, screen, literature pocket and life vest, 100 sets within £1.5 million in 26 weeks. Everything generated for the project is in this folder. Open `index.html` for the project page.

The design is built the way it would be in Inventor: **39 separate parts** (each a `.ipt` with its own model, build steps, drawing and STEP file), put together into **seven sub-assemblies** (frame, seat pan, seat back, recline lock, armrest, lap belt, life vest pouch: `esp2026_saN_*`, each with an exploded view and build steps that add one part at a time), which are then placed into the three-seat set (128 parts in all). The parts are listed in `models/esp2026.py` (`PARTS`) with their material, density and the features that make them.

| File or folder | Contents |
|---|---|
| `drawings/ESP26-GA-01_general_arrangement` | A3, 1:10: front view, plan, end view (reclined back chain dotted), isometric, main sizes |
| `drawings/ESP26-GA-02_single_seat` | A3: section A-A on the seat centre line (1:5), the back of the seat (1:8), specification check |
| `drawings/ESP26-GA-03_mechanism_details` | A3: recline lock, lifting armrest, lap belt buckle, track fitting |
| `drawings/ESP26-GA-04_design_ideas` | A3: Part A design ideas A (beam and leg seat) and B (fixed shell seats), 3D, side and plan, comparison |
| `drawings/ESP26-GA-05_parts_list` | A3: the full parts list (39 items) and a ballooned view of the set |
| `drawings/ESP26-GA-06_sub_assemblies` | A3: the seven sub-assemblies exploded, every part ballooned to the parts list |
| `drawings/ESP26-GA-07_assembly_order` | A3: the assembly structure (set, sub-assemblies, parts) and the eight stages of assembly |
| `drawings/esp2026_pNN_*` | One sheet per part (ESP26-P01 to P39): third angle and first angle, key sizes table |
| `drawings/esp2026_*` | The hub's standard sheets for the assemblies: third angle, first angle, section A-A |
| `ESP26_calculations.pdf` | Part A calculations: cost to manufacture, weight, size, seat height, leg strength, every assumption |
| `ESP26_calculations.json` | The key results, read by the project page |
| `ESP26_reflective_notes.pdf` | Part B reflective notes (about 500 words) |
| `step/`, `stl/`, `glb/`, `edges/` | 3D model files |
| `media/` | Stills and MP4 animations, including `esp2026_seat_set_sim.mp4` (recline, armrests and trays) |
| `qa/` | Clash check results and browser check screenshots of every page and tab, at desktop and phone size |
| `steps/`, `sim/`, `fea/` | Data for the viewer's Build steps, Simulation and FEA tabs |

Sources: `models/esp2026.py` (the models), `models/esp2026_steps.py` (Inventor build steps), `tools/build_sim.py` (simulation), `models/fea_cases.py` (FEA load case), `tools/esp2026_checks.py` (clash and floating part checks), `tools/esp2026_drawings.py` (dimensioned sheets), `tools/esp2026_calcs.py` (calculations and notes).

Rebuild from the repository root (CadQuery, gmsh, scikit-fem and Playwright are needed):

```bash
M=$(python3 -c "import sys; sys.path.insert(0, 'models'); import esp2026; print(' '.join(m['name'] for m in esp2026.MODELS))")
python3 tools/build_models.py $M && python3 tools/build_steps.py $M && python3 tools/build_sim.py
python3 tools/build_fea.py esp2026_p04_leg && python3 tools/esp2026_checks.py
python3 tools/esp2026_calcs.py && python3 tools/drawings.py $M && python3 tools/esp2026_drawings.py
python3 tools/render.py $M
python3 tools/test_esp2026.py   # browser checks, desktop and phone; screenshots to qa/
```
