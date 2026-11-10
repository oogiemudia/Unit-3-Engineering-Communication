# ESP 2026 quality assurance (master prompt stage B17)

Checked 2026-11-10 on branch `claude/esp-2026`. Every line was checked, not assumed.

| # | Check | Result | Notes |
|---|---|---|---|
| 1 | Brief: every requirement and deliverable answered | Pass | Part A: two designs as 3D, side and plan sketches with notes (GA-04); section (GA-02), details (GA-03) cover the belt lock, materials, armrest mechanism, manual recline, head rest, tray, A4 pocket, life vest, screen and floor fixing. Calculations PDF covers cost, weight, size, seat height and all assumptions. Part B: dimensioned, scaled drawings (GA-01 to 03, GA-05, P01 to P39) and reflective notes PDF. PDS table on GA-02 checks all 14 requirements. |
| 2 | Parts list: every component its own part, quantities match | Pass | 39 parts, each its own `@part` model. Parts list on GA-05 is generated from the placed instances: 128 in all, every quantity equal to the count in the assembly. |
| 3 | Part models: single valid solid, sizes match drawing and calcs | Pass | All 39 part shapes are one valid solid each. Drawing sizes, key sizes tables and calculations are all read from the same model constants. |
| 4 | Clashes | Pass | 0 overlaps over 1 mm³ at 6 positions: upright, backs half reclined, backs fully reclined, trays down, armrests up, everything combined (`qa/assembly_checks.json`). |
| 5 | Floating parts | Pass | Every one of the 128 parts is within 0.05 mm of another part (checked upright; the moving parts turn about pins they stay on). |
| 6 | Files | Pass | STEP, STL, GLB, edges, steps and drawings exist for all 42 models (3 assemblies + 39 parts); `docs/models.json` has every entry. |
| 7 | Drawings checked by eye | Pass | GA-01 to GA-05 and all 39 part sheets looked at. Fixed during QA: GA-02 labels and spec table overlapping view B, GA-03 detail D off the sheet and E/F overlapping, GA-04 plans off the sheet, long part titles running out of the title block (now shrink to fit). Third angle symbol, hatching on cut parts, item numbers matching GA-05. |
| 8 | Build steps | Pass | `build_steps.py` confirms the last stage equals the finished model for all 42; every step names an Inventor command (Place, Constrain, Pattern, Extrude, Content Center...). |
| 9 | Simulation | Pass | Backs recline 12° to 17° one after another (lock 353.9 to 345.1 mm, stroke 8.8 mm), right hand armrests lift 0 to 90°, trays fold 0 to 78° to sit level. Video frames checked at 0, 6, 11 and 17 s match the graphs. |
| 10 | FEA and hand checks | Pass | Leg, 9 g forward, 11,235 N a leg: rear strut 18.7 vs 19.2 MPa, brace 28.8 vs 31.0, chord 18.0 vs 18.7 (within 7 %); front strut is a zero-force member in the truss (2.5 MPa bending in FEA). Peak 227 MPa at the brace corner, SF 2.2 on 7075-T6. |
| 11 | Calculations and notes | Pass | Numbers come from the model and FEA (23.50 kg set, 7.83 kg a seat, £5,362 a set, 71 % sustainable). Reflective notes 534 words (about 500 asked). |
| 12 | Browser checks | Pass | `tools/test_esp2026.py`: 40 of 40 pass (20 pages and tabs, desktop and phone), no errors, no sideways scroll. Screenshots in this folder. |
| 13 | Hub models unchanged | Pass | All 57 existing entries in `docs/models.json` identical to before; no existing files under `docs/` changed apart from the hub page filter. `tools/drawings.py` only shrinks title block text that is too long for its cell. |
| 14 | GitHub and project files | Pass | Branch pushed, pull request open and assigned to rahimachy26, folder copied to project files `ESP 2026`. Live site check is due after merging. |

Known limits, stated in the calculations: life vests are treated as airline equipment outside the 8 kg limit (8.35 kg a seat with them); the leg corners are sharp because CadQuery could not fillet this profile; the 9 g check is static, the 16 g dynamic test is planned in the programme.

## Update: assembly build-up (sub-assemblies)

Added after the first merge, at Rahima's request, to show how the parts and components are put together.

| # | Check | Result | Notes |
|---|---|---|---|
| 2 | Parts list | Pass | Every one of the 124 seat, frame and armrest instances belongs to exactly one of the 7 sub-assemblies; the 4 back pivot pins are placed at the top level (they join the backs to the spreaders). Each sub-assembly's parts list is generated from its instances. |
| 6 | Files | Pass | 49 ESP 2026 models (3 assemblies, 7 sub-assemblies, 39 parts) with STEP, STL, GLB, edges, steps and drawings; `docs/models.json` has every entry, existing entries unchanged. |
| 7 | Drawings | Pass | GA-06 (sub-assemblies exploded, every part ballooned) and GA-07 (structure tree and the 8 stages of assembly) checked by eye; balloons moved to the panel edges so none sits on geometry. |
| 8 | Build steps | Pass | Each sub-assembly adds one part (or one matching group) per step; the set now places the sub-assemblies in 8 stages (25, 34, 67, 71, 86, 101, 122, 128 parts). `build_steps.py` confirms every last stage matches its finished model. |
| 12 | Browser checks | Pass | `tools/test_esp2026.py`: 50 of 50 pass (25 pages and tabs, desktop and phone), including the 7 sub-assembly cards on the project page and the build steps, 3D and parts list tabs of the sub-assemblies. No errors, no sideways scroll. Fixed during QA: the catalogue now carries each sub-assembly's number and file name, so the project page can list them. |
| 13 | Hub models unchanged | Pass | All 99 earlier entries in `docs/models.json` identical; `tools/build_models.py` only gains the per-part explode map (a dict), the single-axis explode used by the hub models is unchanged. |
| 14 | GitHub and project files | Pass | New branch `claude/esp-2026-assembly` and pull request (the first one is merged), assigned to rahimachy26; project files `ESP 2026` updated. |
