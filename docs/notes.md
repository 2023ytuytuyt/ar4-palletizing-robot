# Notes — meshes, MoveIt 2 and ros2_control

## 1. Exporting real meshes from SolidWorks

The URDF currently uses simple box/cylinder placeholder geometry. To replace it
with the real design from `last dance.zip` (assembly `01-last one.SLDASM`):

1. In SolidWorks, open the assembly and **save each link as its own part**:
   base carriage, turret (J1), upper arm (J2), forearm (J3), wrist roll (J4),
   wrist bend (J5), flange (J6), gripper body + the two MHF2 fingers.
2. For each part: **File → Save As → STL** (binary, fine resolution) or **STEP
   AP214**. STL is simplest for RViz/Gazebo; STEP keeps more detail but needs
   conversion (e.g. `assimp` / FreeCAD) before Gazebo can use it.
3. Put the meshes in `ar4_description/meshes/` (one subfolder per link) and
   replace the `<geometry>` blocks in `ar4_palletizing.urdf.xacro` with e.g.:
   ```xml
   <mesh filename="package://ar4_description/meshes/link2/link2.stl" scale="0.001 0.001 0.001"/>
   ```
   (scale 0.001 if the STL was exported in millimetres — check the units!)
4. Measure the real values in SolidWorks (Tools → Mass Properties) and fill in
   every `MEASURE FROM SOLIDWORKS` property at the top of the Xacro: link
   lengths (distance between joint axes), masses, and the **track travel length**
   (the 0.8 m placeholder for `joint_7`).
5. Keep the joint origins consistent: each joint origin sits on the previous
   joint's axis, at the measured distance along the link.

## 2. joint_7 in MoveIt 2

The 7th axis is a prismatic joint (`world` → `base_link`). Two options:

- **One planning group** (`ar4_arm`): add `joint_7` to the group's joints in
  `ar4_moveit_config/config/ar4_palletizing.srdf` together with `joint_1`…`joint_6`.
  MoveIt then plans arm + track motion together (best for palletizing across a row).
- **Two groups**: `ar4_arm` (joints 1–6) + `track` (joint_7 only). Simpler, but
  the palletizing code must move the track and the arm in two separate plans.

Recommended: start with one group including `joint_7`; the track is slow, so
give it a low velocity/acceleration scaling in the MoveIt config.

## 3. joint_7 in ros2_control

Add `joint_7` to the `JointTrajectoryController` joints list in the
ros2_control config (same list as joints 1–6), e.g.:

```yaml
joint_trajectory_controller:
  ros__parameters:
    joints:
      - joint_7
      - joint_1
      - joint_2
      - joint_3
      - joint_4
      - joint_5
      - joint_6
    command_interfaces:
      - position
    state_interfaces:
      - position
      - velocity
```

For simulation, start with **Mock Components** (`ros2_control` mock hardware —
no real hardware needed); later swap the mock for the real
`AR4HardwareInterface` (Teensy 4.1) without changing the controller config.

## 4. Gripper fingers

`finger_left_joint` / `finger_right_joint` are prismatic joints. In the real
system the MHF2 is pneumatic (open/close, not position-controlled), so in
ros2_control they are best driven by a simple on/off (or a `GripperActionController`
later). In simulation they can stay as position joints for now.

## 5. Conveyor + vision (later)

- Conveyor stops at the pick point (recommended) + photoelectric/proximity
  sensor signalling ROS 2 — do NOT pick from a moving belt.
- Fixed USB camera above the pick point (eye-to-hand); locate the box with
  classical OpenCV (threshold → contours → box centre/angle) via `cv_bridge`,
  or ArUco markers; transform camera → base with TF.
- Pallet position is fixed; the pallet pattern (boxes per row, layers) is still TBD.
