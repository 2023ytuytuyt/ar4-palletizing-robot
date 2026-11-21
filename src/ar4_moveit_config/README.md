# ar4_moveit_config — MoveIt 2 configuration (ROS 2 Jazzy)

MoveIt 2 planning configuration for the AR4 palletizing robot
(`ar4_description/urdf/ar4_palletizing.urdf.xacro`).

## Planning groups — why joint_7 is inside `ar4_arm`

| Group | Joints | Purpose |
|---|---|---|
| `ar4_arm` | `joint_7` (prismatic track) + `joint_1`…`joint_6` (revolute) | One planning group for the whole arm + track |
| `gripper` | `finger_left_joint`, `finger_right_joint` (placeholder — real gripper has three jaws) | 3-Claw servo gripper |

The 7th axis is **inside** `ar4_arm` on purpose (see `docs/notes.md`): MoveIt
then plans arm + track motion **together** in a single plan. That is what
palletizing across a pallet row needs — the robot slides along the track to
the next column while the arm moves to the place pose. Splitting them into
two groups would force two separate plans (move track, then move arm) for
every box.

The track is slow (ball screw), so `joint_7` has deliberately low
velocity/acceleration limits in `config/joint_limits.yaml`.

End effector: `claw_gripper` (parent link `link6`, group `gripper`).

## Files

| File | What it is |
|---|---|
| `config/ar4_palletizing.srdf` | Groups, end effector, disabled collisions, `home`/`pick`/`open`/`closed` states |
| `config/kinematics.yaml` | KDL IK solver for `ar4_arm` |
| `config/joint_limits.yaml` | Planning velocity/acceleration limits (conservative placeholders) |
| `config/moveit_controllers.yaml` | `arm_controller` (joint_7 + joint_1..6) and `gripper_controller` via ros2_control |
| `config/ompl_planning.yaml` | OMPL, `RRTConnect` default |
| `config/sensors_3d.yaml` | Empty — the fixed pick-point camera is eye-to-hand OpenCV, not a MoveIt sensor |
| `launch/move_group.launch.py` | Starts the `move_group` node |
| `launch/moveit_rviz.launch.py` | Starts RViz with the MoveIt plugin |

## Run it

```bash
# Build (from the workspace root)
colcon build --packages-select ar4_moveit_config
source install/setup.bash

# Terminal 1: planning node
ros2 launch ar4_moveit_config move_group.launch.py

# Terminal 2: RViz + MoveIt plugin
ros2 launch ar4_moveit_config moveit_rviz.launch.py
```

In RViz, add the **MotionPlanning** display, select planning group
`ar4_arm`, and plan to the `home` or `pick` group state (or drag the
interactive marker). For real execution the `arm_controller` /
`gripper_controller` must be running under ros2_control — see
`ar4_control` (Mock Components in simulation, `AR4HardwareInterface` on
the real robot).

## Placeholders — read before trusting a plan

- The `home` and `pick` group states in the SRDF are **placeholder joint
  values**. Verify them in RViz and replace them with real, reachable poses.
- The joint limits in `joint_limits.yaml` are **conservative placeholders**,
  not measured motor/drive limits.
- No real link meshes or measured dimensions are used yet — the URDF is
  still placeholder box/cylinder geometry (see `docs/notes.md`).
