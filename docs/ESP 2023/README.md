# ESP 2023: canal lock gates

T Level Design and Development Employer-Set Project (8730-035), Summer 2023, Task 2. Lock Restoration Ltd designs new automated lock gates for Canal Heritage: each gate fits a 4.2 m opening, is 6 m high and holds a head of 2 m to 5.5 m of water. Everything generated for the project is in this folder. Open `index.html` for the project page.

| File or folder | Contents |
|---|---|
| `drawings/ESP23-GA-01_general_arrangement` | A3, 1:50: plan (shut, open position chain dotted), elevation, water levels, pressure diagram, parts list |
| `drawings/ESP23-GA-02_gate_leaf` | A3: leaf elevation with girder levels, plan, section C-C |
| `drawings/ESP23-GA-03_hinge_and_seal_details` | A3: pintle, anchor collar, mitre seal, heel post in the quoin |
| `drawings/ESP23-GA-04_design_ideas` | A3: Part A design ideas A (mitre gates) and B (lift gate), hydrostatic load, comparison |
| `drawings/esp2023_*` | The hub's standard sheets for each model: third angle, first angle, section A-A |
| `ESP23_calculations.pdf` | Supporting calculations, two A4 sides, with assumptions |
| `ESP23_design_notes.pdf` | How the design meets the brief (about 500 words) |
| `step/`, `stl/`, `glb/`, `edges/` | 3D model files |
| `media/` | Stills and MP4 animations, including `esp2023_lock_gates_sim.mp4` (the gates opening) |
| `qa/` | Browser check screenshots of every page and tab, at desktop and phone size |
| `steps/`, `sim/`, `fea/` | Data for the viewer's Build steps, Simulation and FEA tabs |

Sources: `models/esp2023.py` (the models), `models/esp2023_steps.py` (Inventor build steps), `tools/build_sim.py` (simulation), `models/fea_cases.py` (FEA load cases), `tools/esp2023_drawings.py` (dimensioned sheets), `tools/esp2023_calcs.py` (calculations and notes).

Rebuild from the repository root:

```bash
M="esp2023_lock_gates esp2023_gate_leaf esp2023_skin_panel esp2023_lift_gate"
python3 tools/build_models.py $M && python3 tools/build_steps.py $M && python3 tools/build_sim.py
python3 tools/build_fea.py esp2023_skin_panel esp2023_lock_gates
python3 tools/drawings.py $M && python3 tools/esp2023_drawings.py && python3 tools/esp2023_calcs.py
python3 tools/render.py $M
python3 tools/test_esp2023.py   # browser checks, desktop and phone; screenshots to qa/
```
