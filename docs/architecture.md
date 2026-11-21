# Architecture — AR4 Palletizing Robot

> **ملخص عربي:** دي خريطة النظام كله — الكاميرا بتشوف الصندوق، نود الرؤية بيحسب مكانه، نود الـ palletizing بيخطط الحركة، MoveIt 2 بيحسب المسار، ros2_control بينفذه، والتنفيذ بيحصل في Gazebo (دلوقتي) أو على الهاردوير الحقيقي (بعدين). المحور السابع الخطي (`joint_7`) جزء من كل ده.

## 1. System overview

The robot is a 6-axis AR4 arm mounted on a 7th linear axis (aluminium extrusion
track + ball screw). Very small boxes arrive on a conveyor. A fixed camera above
the pick point locates each box with classical OpenCV. The arm picks the box,
slides along the track to the pallet position, and places it. The pallet position
is fixed; the pallet pattern (boxes per row, number of layers) is still TBD.

Everything is developed in simulation first (Gazebo). The real hardware
(Teensy 4.1 + AR4HardwareInterface) replaces the simulation layer later,
without changing the layers above it.

## 2. System diagram

```
                          ┌─────────────────────┐
                          │  Fixed USB camera   │
                          │  (eye-to-hand,      │
                          │   above pick point) │
                          └──────────┬──────────┘
                                     │ /camera/image_raw
                                     ▼
                          ┌─────────────────────┐
                          │  Vision node        │
                          │  (ar4_palletizing)  │
                          │  OpenCV: threshold  │
                          │  -> contours ->     │
                          │  minAreaRect        │
                          │  centre + angle     │
                          └──────────┬──────────┘
                                     │ /box_pose (geometry_msgs/PoseStamped, base frame)
                                     ▼
                          ┌─────────────────────┐        ┌──────────────────┐
                          │  Palletizing demo   │◄───────│ Conveyor sensor  │
                          │  (ar4_palletizing)  │  box    │ (photoelectric / │
                          │  state machine:     │  ready  │  proximity)      │
                          │  wait -> pick ->    │  signal │ "box at pick     │
                          │  move -> place ->   │         │  point, conveyor │
                          │  repeat             │         │  stopped"        │
                          └──────────┬──────────┘        └──────────────────┘
                                     │ MoveIt 2 planning request
                                     │ (target pose, planning group ar4_arm)
                                     ▼
                          ┌─────────────────────┐
                          │  MoveIt 2           │
                          │  (ar4_moveit_config)│
                          │  planning group     │
                          │  ar4_arm = joints   │
                          │  1-6 + joint_7      │
                          │  gripper group =    │
                          │  finger joints      │
                          └──────────┬──────────┘
                                     │ JointTrajectory (trajectory_msgs)
                                     ▼
                          ┌─────────────────────┐
                          │  ros2_control       │
                          │  (ar4_control)      │
                          │  JointTrajectory    │
                          │  Controller (60 Hz) │
                          │  joints: joint_7,   │
                          │  joint_1..joint_6   │
                          └──────────┬──────────┘
                                     │ hardware interface
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
         ┌──────────────────┐              ┌──────────────────┐
         │  Gazebo (now)    │              │  Real hardware   │
         │  ros_gz_sim +    │              │  (later)         │
         │  Mock Components │              │  Teensy 4.1 +    │
         │  world: track,   │              │  AR4Hardware-    │
         │  conveyor,       │              │  Interface,      │
         │  pallet, boxes   │              │  MHF2 pneumatics │
         └──────────────────┘              └──────────────────┘
```

### TF tree

```
world -> joint_7 (prismatic) -> base_link -> joint_1 -> link1 -> joint_2 -> link2
  -> joint_3 -> link3 -> joint_4 -> link4 -> joint_5 -> link5 -> joint_6 -> link6
  -> gripper_fixed -> gripper_base -> finger_left_joint / finger_right_joint
world -> camera_link (static transform, measured after calibration — TBD)
world -> conveyor_frame, pallet_frame (fixed, TBD once the cell layout is measured)
```

See [urdf-guide.md](urdf-guide.md) for the full joint/link chain.

## 3. Package map

| Package | Status | What it does |
|---|---|---|
| `ar4_description` | **Exists** | URDF/Xacro of the arm + track + MHF2 gripper, RViz launch (`view_robot.launch.py`) |
| `ar4_bringup` | **Exists (skeleton)** | Gazebo launch (`gazebo.launch.py`) — spawns the URDF in an empty world; conveyor/pallet/boxes worlds come later |
| `ar4_moveit_config` | Done | MoveIt 2 config: SRDF (planning groups `ar4_arm`, `gripper`), kinematics, OMPL planner config, `move_group` launch |
| `ar4_control` | Done | ros2_control config: JointTrajectoryController (joints `joint_7`, `joint_1`–`joint_6`), joint state broadcaster, gripper controller; Mock Components for simulation, AR4HardwareInterface for real hardware |
| `ar4_gazebo` | Done | Gazebo worlds and models: track + conveyor + pallet + boxes, `ros_gz_bridge` config, sensor plugins |
| `ar4_palletizing` (vision) | Done | OpenCV box-detection node `vision_node` + `vision_utils` (classical CV, see [vision-guide.md](vision-guide.md)), camera calibration files (TBD) |
| `ar4_palletizing` | Done | The demo application: state machine (wait → pick → move → place), pallet pattern logic, conveyor interface |
| `ar4_gazebo` (bringup) | Done | `palletizing_world.launch.py` brings up Gazebo + control + robot spawn together; full MoveIt + demo bringup is the next step |

Status note: only `ar4_description` and `ar4_bringup` exist in the repo today.
All packages in the table above now exist in `src/` — build them with `colcon build` (see [setup.md](setup.md)). What remains is filling in measured values and running them on a ROS 2 machine.
them in that order (description → control → MoveIt → Gazebo world → vision → demo).

## 4. Data flow of one pick-and-place cycle

1. **Box arrives.** The conveyor moves a box to the pick point and **stops**
   (recommended design — do not pick from a moving belt). The photoelectric /
   proximity sensor signals "box ready" to the palletizing node.
2. **See.** The fixed camera captures a frame. The vision node (OpenCV) finds
   the box contour, computes its centre and rotation angle in the image, and
   converts them to a 3D pose in the robot base frame using the camera
   calibration + the static camera→base TF.
3. **Plan pick.** The palletizing node sends the pick pose (above the box, then
   down to the box) to MoveIt 2. MoveIt plans a path for planning group
   `ar4_arm` — joints 1–6 **and** `joint_7` together, so the track can move
   while the arm moves.
4. **Execute pick.** MoveIt sends the trajectory to the JointTrajectoryController.
   ros2_control executes it (in Gazebo now, on the Teensy later). The gripper
   closes (`finger_left_joint` / `finger_right_joint` — in reality a pneumatic
   on/off command to the MHF2 solenoid valve).
5. **Plan place.** The palletizing node looks up the next free slot in the
   pallet pattern (pattern still TBD) and sends the place pose to MoveIt. The
   plan moves the arm up, slides `joint_7` along the track to the right
   position, and lowers the box into its slot.
6. **Place and release.** The gripper opens, the arm lifts clear, and the
   palletizing node waits for the next "box ready" signal.
7. **Repeat** until the pallet layer/row is full, then continue with the next
   row/layer (pattern TBD).

## 5. Design decisions (and why)

- **Simulation first, hardware later.** Phases 1–5 of the roadmap run on a
  laptop only (Ubuntu 24.04 + ROS 2 Jazzy). No hardware is needed to start.
  See [faq.md](faq.md).
- **One planning group including `joint_7`.** The track is part of the robot's
  kinematics, not a separate machine. Planning arm + track together gives
  shorter, collision-free paths to any pallet slot. See
  [moveit-guide.md](moveit-guide.md).
- **Classical OpenCV, no deep learning.** One small fixed-shape box on a
  contrasting conveyor under fixed lighting is a threshold + contour problem,
  not a learning problem. See [vision-guide.md](vision-guide.md).
- **Conveyor stops at the pick point.** Picking from a moving belt needs
  conveyor tracking and tight timing; stopping the belt at the pick point
  makes the pick deterministic. The conveyor behaviour (stop vs. continuous)
  is still an open item — see [hardware-checklist.md](hardware-checklist.md).
- **Mock Components in simulation.** ros2_control runs against mock hardware
  in Gazebo, so the controller config is identical when the real
  AR4HardwareInterface is swapped in later.

## 6. Where to read next

- [setup.md](setup.md) — install and run everything, in order
- [urdf-guide.md](urdf-guide.md) — the robot description in detail
- [moveit-guide.md](moveit-guide.md) — planning groups and poses
- [vision-guide.md](vision-guide.md) — the camera pipeline
- [hardware-checklist.md](hardware-checklist.md) — everything still undecided
- [faq.md](faq.md) — quick answers
