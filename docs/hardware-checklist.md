# Hardware Checklist — everything still open

> **ملخص عربي:** دي قايمة كل حاجة في الهاردوير لسه متحددتش — كل بند مفتوح، ومكتوب جنبه بيمنع إيه من الشغل. لما يتحدد بند، علّم عليه وحدّث الملف ده والـ URDF.

**Status of every item below: ⏳ OPEN.** Nothing here has been decided yet.
Each item says what it blocks — do not start the blocked work until the item
is decided, or you will redo it.

## 1. The box (what we are palletizing)

| # | Item | Status | Blocks |
|---|---|---|---|
| 1.1 | **Box dimensions** (length × width × height, in cm) | ⏳ OPEN | Gripper finger gap and closing travel; pallet slot size; box model in Gazebo; `minAreaRect` size checks in vision |
| 1.2 | **Box weight** (grams) | ⏳ OPEN | Whether the MHF2 grip is strong enough; arm payload check; Gazebo box mass |
| 1.3 | **Box material / surface** (cardboard? plastic? smooth?) | ⏳ OPEN | Friction between fingers and box — smooth plastic needs more grip force than cardboard |

## 2. The 7th axis (linear track)

| # | Item | Status | Blocks |
|---|---|---|---|
| 2.1 | **Actual track travel length** (m) | ⏳ OPEN | `track_travel` in the URDF (0.8 m is only a placeholder); how many pallet slots the robot can reach; MoveIt planning limits |
| 2.2 | **Track motor + driver** (stepper? servo? which model) | ⏳ OPEN | Track speed/acceleration in MoveIt (`joint_7` limits); ros2_control hardware interface for `joint_7` |
| 2.3 | **Ball screw lead** (mm per revolution) | ⏳ OPEN | Converting motor steps/revolutions to metres of travel |
| 2.4 | **Limit switches at both ends of the track** | ⏳ OPEN | Safe homing of `joint_7`; prevents the carriage running off the rail — a safety item, not optional |
| 2.5 | **Homing procedure for `joint_7`** | ⏳ OPEN | How the robot finds track zero at startup |

## 3. The pallet

| # | Item | Status | Blocks |
|---|---|---|---|
| 3.1 | **Pallet pattern** — boxes per row, rows per layer, number of layers | ⏳ OPEN | Place poses in the palletizing demo; whether the track travel covers all slots |
| 3.2 | **Pallet size and position** (fixed, measured in the cell) | ⏳ OPEN | Pallet frame in TF; collision object in MoveIt; Gazebo world |
| 3.3 | **Box spacing on the pallet** (gap between boxes) | ⏳ OPEN | Place pose calculation; finger clearance when placing next to an already-placed box |

## 4. Gripper pneumatics (SMC MHF2-8D1)

| # | Item | Status | Blocks |
|---|---|---|---|
| 4.1 | **Compressor / air source** (which one, pressure in bar) | ⏳ OPEN | Whether the gripper can close at all on the real robot |
| 4.2 | **Solenoid valve** (which model, how it is driven) | ⏳ OPEN | ros2_control gripper interface (on/off output); wiring to the Teensy |
| 4.3 | **Pressure regulator** | ⏳ OPEN | Grip force — too much pressure crushes a small box, too little drops it |
| 4.4 | **Hoses and fittings** (diameter, routing along the arm) | ⏳ OPEN | Hose routing must not limit joint motion — check in the real assembly |

## 5. Power and safety

| # | Item | Status | Blocks |
|---|---|---|---|
| 5.1 | **Power supply** (voltage/current for arm motors + track motor) | ⏳ OPEN | Motor drivers; any real-hardware test |
| 5.2 | **Emergency stop** (button, wiring, what it cuts) | ⏳ OPEN | Any real-hardware test — do not run the real arm without an E-stop |
| 5.3 | **Motor drivers** for J1–J6 (which ones) | ⏳ OPEN | Teensy ↔ driver wiring; AR4HardwareInterface |

## 6. Control hardware

| # | Item | Status | Blocks |
|---|---|---|---|
| 6.1 | **Teensy 4.1** (board on hand? pins assigned?) | ⏳ OPEN | AR4HardwareInterface; ros2_control real-hardware bring-up |
| 6.2 | **AR4HardwareInterface** (adapted to this arm + track?) | ⏳ OPEN | Real-hardware control; `joint_7` needs its own channel in the interface |

## 7. Conveyor + sensors

| # | Item | Status | Blocks |
|---|---|---|---|
| 7.1 | **Does the conveyor stop at the pick point, or run continuously?** | ⏳ OPEN | The whole pick logic. Recommended: stop at the pick point + sensor signal. Picking from a moving belt needs conveyor tracking and is much harder |
| 7.2 | **Photoelectric / proximity sensor at the pick point** (which model, wiring) | ⏳ OPEN | "Box ready" signal to the palletizing node; without it the demo cannot know when to pick |
| 7.3 | **Conveyor control interface** (how ROS 2 starts/stops the belt) | ⏳ OPEN | The conveyor node in `ar4_palletizing` |
| 7.4 | **Camera** (which USB camera, resolution) | ⏳ OPEN | Vision node; calibration; pixel→metre scale |

## How to use this checklist

1. When an item is decided, change its status to ✅ DECIDED, write the value
   in the table, and update the place that consumes it (URDF property, MoveIt
   config, vision tuning, or the demo code).
2. Decide items in this order: box (1) → track travel (2.1) → pallet pattern
   (3.1) → conveyor behaviour (7.1). Those four unlock almost all the
   simulation work; pneumatics, power and safety unlock the hardware work.
3. Keep this file as the single source of truth for "what is still unknown".
   If a value appears in code or docs, it must match a ✅ DECIDED row here —
   otherwise it is a placeholder.
