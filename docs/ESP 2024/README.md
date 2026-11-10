# ESP 2024: harbour marker buoy

T Level Design and Development Employer-Set Project (8730-035), Summer 2024, Task 2. Oceans Technology Ltd designs marker buoys for Harbour Shipping Ltd: 1400 to 1800 mm above the sea on a 500 ±25 mm base, green for entering and red for leaving the harbour, an alert if the mooring cable breaks, tracking if it drifts, renewable 12 V power, a secure watertight battery space, no rust, and £2000 a buoy for 100 buoys (2 a week) in 70 weeks. Everything generated for the project is in this folder. Open `index.html` for the project page.

The design is built the way it would be in Inventor: **43 separate parts** (each a `.ipt` with its own model, build steps, drawing and STEP file), put together into **seven sub-assemblies** (float, equipment canister, tail and ballast, mast and solar panels, lantern and topmark, mooring and load pin, and the sinker: `esp2024_saN_*`, each with an exploded view and build steps that add one part at a time). Six of them are placed into the buoy (77 parts); the sinker is laid on the harbour bed and joined by the chain. The parts are listed in `models/esp2024.py` (`PARTS`) with their material, density and the features that make them. The waterline and stability are worked out from the parts themselves (`float_line`).

| File or folder | Contents |
|---|---|
| `drawings/ESP24-GA-01_general_arrangement` | A3: front and side views 1:20 with the waterline and heights above the sea, plan 1:10, isometric, notes |
| `drawings/ESP24-GA-02_float_section` | A3: section A-A through the float and canister (1:8), the open hatch (1:5), the 12 V power, specification check |
| `drawings/ESP24-GA-03_details` | A3: mooring eye and load pin (1:3), watertight locked hatch (1:2), lantern and topmark (1:5) |
| `drawings/ESP24-GA-04_design_ideas` | A3: Part A design ideas A (solar, polyethylene float) and B (wind, steel sphere), comparison against the brief |
| `drawings/ESP24-GA-05_parts_list` | A3: the full parts list (43 items) and a ballooned view of the buoy and sinker |
| `drawings/ESP24-GA-06_sub_assemblies` | A3: the seven sub-assemblies exploded, every part ballooned to the parts list |
| `drawings/ESP24-GA-07_assembly_order` | A3: the assembly structure and the six stages of assembly |
| `drawings/esp2024_pNN_*` | One sheet per part (ESP24-P01 to P43): third angle and first angle, key sizes table |
| `drawings/esp2024_*` | The hub's standard sheets for the assemblies: third angle, first angle, section A-A |
| `ESP24_calculations.pdf` | Part A calculations: mass and waterline, stability, energy produced against energy needed, mooring loads and the mooring eye, cost, time, materials, every assumption |
| `ESP24_calculations.json` | The key results, read by the project page |
| `ESP24_reflective_notes.pdf` | Part B reflective notes (about 500 words) |
| `step/`, `stl/`, `glb/`, `edges/` | 3D model files |
| `media/` | Stills and MP4 animations, including `esp2024_buoy_sim.mp4` (rolling in waves, chain break and drift) |
| `qa/` | Clash and floating check results and browser check screenshots, at desktop and phone size |
| `steps/`, `sim/`, `fea/` | Data for the viewer's Build steps, Simulation and FEA tabs |

Sources: `models/esp2024.py` (the models), `models/esp2024_steps.py` (Inventor build steps), `tools/build_sim.py` (simulation), `models/fea_cases.py` (FEA load case), `tools/esp2024_checks.py` (clash and floating part checks), `tools/esp2024_drawings.py` (dimensioned sheets), `tools/esp2024_calcs.py` (calculations and notes).

Rebuild from the repository root (CadQuery, gmsh, scikit-fem and Playwright are needed):

```bash
M=$(python3 -c "import sys; sys.path.insert(0, 'models'); import esp2024; print(' '.join(m['name'] for m in esp2024.MODELS))")
python3 tools/build_models.py $M && python3 tools/build_steps.py $M && python3 tools/build_sim.py esp2024_buoy
python3 tools/build_fea.py esp2024_p23_mooring_eye && python3 tools/esp2024_checks.py
python3 tools/esp2024_calcs.py && python3 tools/drawings.py $M && python3 tools/esp2024_drawings.py
python3 tools/render.py $M
python3 tools/test_esp2024.py   # browser checks, desktop and phone; screenshots to qa/
```
