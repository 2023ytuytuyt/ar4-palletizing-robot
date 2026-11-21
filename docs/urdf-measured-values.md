# URDF measured values — from SolidWorks (2026-11-21)

All dimensions in the URDF are now **measured**, not placeholders. Source:
`01-last one.SLDASM`, measured with the `MeasureAR4` macro (v2),
file `ar4_measurements v2` (93 parts, 2026-11-21 18:24 EET).
The raw file is saved with the project notes; the derivation script is
`/tmp/build_frames.py` (kept in the agent workspace, not in the repo).

## How it was measured

1. The macro writes, per part: mass (kg), volume, centre of mass, bounding
   box, and the full 16-value component transform (rotation + translation).
2. The transform layout was decoded from the data itself:
   elements 0–8 are the 3×3 rotation as three column-triplets
   (triplet *i* = the image of the part's local axis *i*),
   elements 9–11 are the part origin in the assembly frame (metres),
   elements 12–15 are always `(1, 0, 0, 0)`.
   Proof: all five J1 parts' origins lie **exactly** (0.0 mm) on the J1 axis
   line through the J1 spindle origin — see the cross-check below.
3. The SolidWorks assembly frame has **X = up** (the track runs along
   assembly Y). Everything is converted to ROS (Z = up) with
   `(x, y, z)_ros = (z, -y, x)_asm`, a right-handed rotation.
4. Each joint frame: origin = its shaft/spindle part's origin,
   Z axis = that shaft's long axis. Link frames are built from the joint
   frames (X = perpendicular direction toward the next joint).
   Joint origins in the URDF are the relative transforms between these
   frames; a forward-kinematics check reproduces the measured J6 pose
   exactly (position and rotation) at all-zero joint values.

## Joint axes (ROS frame, mm)

| Joint | Shaft part used | Origin (ROS, mm) | Axis (ROS) |
|---|---|---|---|
| J7 (track) | HGR15 rail (local Z) / carriage plate origin | (259.9, 71.1, 0.0) | (0, 1, 0) |
| J1 | J1 Spindle | (301.0, 108.0, 92.2) | (0, 0, 1) |
| J2 | J2 Drive Spindle | (365.2, 110.9, 169.8) | (0, 1, 0) |
| J3 | J3 Spindle | (659.3, 138.8, 250.3) | (0, -1, 0) |
| J4 | J4 Main Shaft | (735.0, 102.1, 250.3) | (-1, 0, 0) |
| J5 | J5 Housing (local Y) | (710.0, 131.8, 238.4) | (0, 0.958, 0.288) |
| J6 | J6 gripper mount (local Z) | (902.2, 101.6, 251.8) | (1, 0, 0) |

Cross-checks that the decode is right:

- J1: J1 Spindle, J1 Turret Housing, J1 Turret Platform, J1 Base Plate and
  J1 timing pulley origins are all 0.0 mm from the J1 axis line.
- J3: J3 Spindle and J3 Bearing Cup share the exact same origin
  (250.3, -138.8, 659.3) mm in assembly coordinates; the J4 Turret Housing
  origin also lies on the J3 axis line.
- J2 ∥ J3 (both pitch axes), J1 ⊥ J2, J4 ⊥ J5, J4 ∥ J6 — as a serial
  6R arm must be.

## Link lengths (perpendicular distance between joint axes)

| Pair | mm | Note |
|---|---|---|
| J1 → J2 | **64.2** | shoulder height above the J1 plane |
| J2 → J3 | **304.9** | upper arm |
| J3 → J4 | **0.0** | the J4 axis passes through the J3 axis (the J4 shaft runs through the elbow); the J4 frame sits 84.1 mm from the J3 origin along the arm |
| J4 → J5 | **20.0** | wrist offset |
| J5 → J6 | **21.5** | wrist offset (point-to-point 195.0 mm, mostly along the J6 axis) |

The URDF joint origins also carry the along-axis offsets (e.g. J2 sits
77.6 mm along the J1 axis from the J1 origin), so the full relative
transforms — not just these perpendicular distances — are what the URDF
uses.

## Link masses (kg, from SolidWorks mass properties)

| Link | Mass | Main contributors |
|---|---|---|
| base (carriage) | 0.791 | 7th-axis plate 0.495, J1 Base Plate 0.296 |
| link1 (J1) | 0.596 | J1 Spindle 0.132, Turret Housing 0.129, motor 17HS15 0.139 |
| link2 (J2) | 0.991 | J2 Arm 0.230, Turret Housing 0.208, motor 23HS22 0.333 |
| link3 (J3) | 0.118 | motor 14HS13 0.073, J3 Spindle 0.026 |
| link4 (J4) | 0.192 | motor 17LS13 0.070, Turret Housing 0.058 |
| link5 (J5) | 0.320 | side cover cap 0.095, Housing 0.084, motor 11HS20 0.065 |
| link6 (J6) | 0.123 | main bearing arm 0.075, housing 0.024 |
| gripper (MHF2) | 0.10 | SMC catalogue value — not yet measured |
| **arm total** | **~3.1** | (without track; track subassembly Assem2 = 2.454 kg) |

Centres of mass and inertias in the URDF are the mass-weighted values from
the same file; inertias are box approximations from each link's aggregate
bounding box. The old placeholder masses (2.0 / 1.5 / 1.0 / … kg) were
2–3× too heavy.

## Track

- HGR15 rail: 500 mm long; 8020 framing: 551.56 mm; ballscrew SFU1204-500;
  ballscrew end supports (_bf10 / _bk10) 452 mm apart.
- **Usable travel: 0.45 m (ESTIMATE).** Rail 500 − HGW15CC blocks 39 mm −
  end margins ≈ 450 mm. The carriage as measured sits ~12 mm from the
  −Y rail end, so joint_7 = 0 is the measured carriage position and
  +0.45 m runs it to the far end.
- Confirm from the two limit-switch positions (only one Limit Switch Mount
  is in the measurement file).

## Joint zero = the SolidWorks pose

**Read this before touching the joint values.** The URDF joint origins
reproduce the exact pose the arm had in `01-last one.SLDASM` when all
joint values are 0. That is the calibrated zero of this URDF — not a
canonical "arm straight up" pose. The zero offsets are baked into the
origins because the joint angles in the SolidWorks pose are unknown; the
kinematics are exact up to that constant offset per joint (verified by
the FK check above). Consequences:

- `ros2 launch ar4_description ...` with all zeros shows the arm exactly
  as it looks in SolidWorks.
- Joint limits in the URDF are still placeholders and are expressed
  around this zero — check them against the AR4 datasheet / physical end
  stops before running hardware.
- MoveIt named poses ("home", "pick", …) are joint values in this same
  convention; re-teach them from the new zero if they were made against
  the old placeholder URDF.

## Still estimated / to do

- [ ] Track travel: confirm 0.45 m from the two limit-switch positions.
- [ ] J5 frame: axis from the J5 Housing local-Y direction and centre from
      the housing origin (no J5 shaft part in the assembly). Verify in RViz
      that the wrist pitch looks right.
- [ ] J6 frame: axis from the gripper-mount local-Z; centre = gripper-mount
      origin. Same RViz check.
- [ ] MHF2 gripper: export an STL from `MHF2-8D1.SLDASM` (run `ExportSTL.bas`
      with that assembly open) and replace the placeholder gripper boxes;
      measure its mass (catalogue says ~0.10 kg).
- [ ] Meshes: verify in RViz that all 17 STLs sit correctly on their links.
      A wrong local frame shows up immediately as a floating/misplaced part.
- [ ] Joint limits: replace the placeholder ±limits with the AR4 values.
- [ ] Box size/weight, pallet pattern, conveyor stop-vs-continuous: still
      open (see README TODO).
