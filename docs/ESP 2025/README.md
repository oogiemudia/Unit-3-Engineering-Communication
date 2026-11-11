# ESP 2025: automated pill dispenser

T Level Design and Development Employer-Set Project, 2025, Task 2. WBEP Ltd designs an automated pill dispenser for a health trust: no bigger than 190 x 190 x 60 mm, 0.5 kg or less with its batteries, at least 3 pills (up to Ø5 x 20 mm) in each compartment, refilled every 28 days for once a day or every 14 days for twice a day, battery powered, an alarm that sounds until the pills are dispensed, a PRESS HERE button next to a flashing light, tamper proof with a lock only the pharmacy can open, waterproof, a recyclable casing that can be used again and again, and £97,500 for 1500 units (£65 each) or £120,000 for 3000 (£40 each). Everything generated for the project is in this folder. Open `index.html` for the project page.

The design is built the way it would be in Inventor: **37 separate parts** (each a `.ipt` with its own model, build steps, drawing and STEP file), put together into **six sub-assemblies** (chassis, lock and chute; carousel; base, batteries and drive; control pod; lid and hinge; dispensing drawer: `esp2025_saN_*`, each with an exploded view and build steps that add the parts in order). The six are placed into the dispenser with four cover screws. The parts are listed in `models/esp2025.py` (`PARTS`) with their material, density and the features that make them.

| File or folder | Contents |
|---|---|
| `drawings/ESP25-GA-01_general_arrangement` | A3: front, plan and side views 1:2 with the overall sizes, isometric, sub-assemblies, notes |
| `drawings/ESP25-GA-02_sections` | A3: sections A-A and B-B 1:1, how a dose is given, specification check |
| `drawings/ESP25-GA-03_details` | A3: pharmacy lock and lid catch, worm drive, control panel (2:1) |
| `drawings/ESP25-GA-04_design_ideas` | A3: Part A design ideas A (round carousel) and B (trapdoor cassette), comparison against the brief |
| `drawings/ESP25-GA-05_parts_list` | A3: the full parts list (37 items) and a ballooned view of the dispenser |
| `drawings/ESP25-GA-06_sub_assemblies` | A3: the six sub-assemblies exploded, every part ballooned to the parts list |
| `drawings/ESP25-GA-07_assembly_order` | A3: the assembly structure and the stages of assembly |
| `drawings/esp2025_pNN_*` | One sheet per part (ESP25-P01 to P37): third angle and first angle, key sizes table |
| `drawings/esp2025_*` | The hub's standard sheets for the assemblies: third angle, first angle, section A-A |
| `ESP25_calculations.pdf` | Part A calculations: size and mass, capacity, battery life, the drive, the lid catch, waterproofing, cost and the most units each budget buys, programme, recycling, every assumption |
| `ESP25_calculations.json` | The key results, read by the project page |
| `ESP25_reflective_notes.pdf` | Part B reflective notes (about 500 words) |
| `step/`, `stl/`, `glb/`, `edges/` | 3D model files |
| `media/` | Stills and MP4 animations, including `esp2025_dispenser_sim.mp4` (a dose, then a pharmacy refill) |
| `qa/` | Clash and floating check results and browser check screenshots, at desktop and phone size |
| `steps/`, `sim/`, `fea/` | Data for the viewer's Build steps, Simulation and FEA tabs |

Sources: `models/esp2025.py` (the models), `models/esp2025_steps.py` (Inventor build steps), `tools/build_sim.py` (simulation), `models/fea_cases.py` (FEA load case), `tools/esp2025_checks.py` (clash and floating part checks), `tools/esp2025_drawings.py` (dimensioned sheets), `tools/esp2025_calcs.py` (calculations and notes).

Rebuild from the repository root (CadQuery, gmsh, scikit-fem and Playwright are needed):

```bash
M=$(python3 -c "import sys; sys.path.insert(0, 'models'); import esp2025; print(' '.join(m['name'] for m in esp2025.MODELS))")
python3 tools/build_models.py $M && python3 tools/build_steps.py $M && python3 tools/build_sim.py esp2025_dispenser
python3 tools/build_fea.py esp2025_p34_lid_catch && python3 tools/esp2025_checks.py
python3 tools/esp2025_calcs.py && python3 tools/drawings.py $M && python3 tools/esp2025_drawings.py
python3 tools/render.py $M
python3 tools/test_esp2025.py   # browser checks, desktop and phone; screenshots to qa/
```
