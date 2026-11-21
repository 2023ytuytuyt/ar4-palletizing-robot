# Meshes — real AR4-MK4 parts (from `AR4-MK4 3D Print final files.rar`)

Source: the user's Drive upload of 2026-11-21 (68 STL files, AR4-MK4 3D print
files). These 17 structural parts are staged here, renamed per URDF link.
All sizes below were measured from the STL bounding boxes (millimetres).

> **Units:** STL files are in **mm** — in the URDF use
> `scale="0.001 0.001 0.001"`.
>
> **Origins measured 2026-11-21:** all 17 meshes are wired into the URDF
> with origins computed from the SolidWorks measurement file
> (`ar4_measurements` v2, 93 parts). See `docs/urdf-measured-values.md`
> for the method. Verify visually in RViz that every mesh sits correctly
> on its link.

## Link → mesh mapping (measured bounding-box size, mm)

| URDF link | Mesh file | Size (X × Y × Z, mm) |
|---|---|---|
| base (plate) | `base_plate.stl` (J1 Base Plate) | 150.0 × 245.0 × 12.7 |
| link1 | `link1_turret_housing.stl` (J1 Turret Housing) | 88.9 × 88.9 × 60.0 |
| link1 | `link1_turret_platform.stl` (J1 Turret Platform) | 94.9 × 104.4 × 12.7 |
| link1 | `link1_spindle.stl` (J1 Spindle) | — |
| link2 | `link2_arm.stl` (J2 Arm) | 76.0 × 373.0 × 12.7 |
| link2 | `link2_spindle.stl` (J2 Spindle) | — |
| link2 | `link2_turret_housing.stl` (J2 Turret Housing) | — |
| link3 | `link3_spindle.stl` (J3 Spindle) | 60.0 × 60.0 × 26.0 |
| link3 | `link3_bearing_cup.stl` (J3 Bearing Cup) | — |
| link4 | `link4_main_shaft.stl` (J4 Main Shaft) | 25.4 × 25.4 × 116.3 |
| link4 | `link4_turret_housing.stl` (J4 Turret Housing) | 58.8 × 60.0 × 45.4 |
| link5 | `link5_housing.stl` (J5 Housing) | 107.7 × 50.0 × 40.0 |
| link5 | `link5_belt_carrier.stl` (J5 Belt Carrier) | 50.4 × 38.5 × 20.0 |
| link6 | `link6_housing.stl` (J6 Housing 35mm) | 79.1 × 41.0 × 44.5 |
| link6 | `link6_gripper_mount.stl` (J6 gripper mount) | 48.0 × 32.0 × 16.0 |
| link6 | `link6_bearing_arm.stl` (J6 main bearing arm) | 150.0 × 50.0 × 14.0 |
| link6 | `link6_bearing_cap.stl` (J6 bearing cap) | 46.0 × 46.0 × 10.0 |

Other STLs in the RAR (motor mounts, spacers, pulleys, limit-switch mounts,
covers, encoder housings) are small detail parts — useful for the physical
build, not needed as URDF meshes.

## Note: "Box ..." STLs are NOT the pallet boxes

`Box Base Tray`, `Box Cover`, `Front Box Base`, `Rear Box Base` in the RAR are
the AR4 electronics enclosure (the control box), not the small boxes to be
palletized. The size/weight of the palletizing boxes is still unknown.

## Still needed (from SolidWorks on Windows)

1. ~~**Joint-axis distances**~~ — **measured 2026-11-21**: J1→J2 64.2 mm,
   J2→J3 304.9 mm, J3→J4 0.0 mm (axes intersect), J4→J5 20.0 mm,
   J5→J6 21.5 mm. See `docs/urdf-measured-values.md`.
2. ~~**Masses per link**~~ — **measured 2026-11-21** from the same file
   (arm total ~3.1 kg; see `docs/urdf-measured-values.md`).
3. **Track travel length** — 0.45 m in the URDF is an ESTIMATE (rail 500 mm,
   blocks 39 mm, end supports 452 mm apart); confirm from the two
   limit-switch positions.
4. **3-Claw gripper STLs** — the gripper is in `at.rar` (Drive, 2026-11-21):
   `3-Claw Gripper Assembly.SLDASM` + Housing, Guide Plate, Jaws x3, Scroll Disc,
   SG90 servo. Export with `ExportSTL.bas` (open the gripper assembly, run the
   macro) — the STLs land in `C:\meshes`. Then wire them into the URDF,
   replacing the two placeholder finger joints with three jaw joints.
5. **Palletizing box size/weight** — the small boxes to be palletized (cm + grams).
6. **Pallet pattern** — boxes per row, number of layers.
