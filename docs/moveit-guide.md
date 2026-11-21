# MoveIt 2 Guide — planning with the 7th axis

> **ملخص عربي:** MoveIt هو اللي بيخطط الحركة — بتقوله "روح للنقطة دي" وهو يحسب المسار. المجموعة `ar4_arm` فيها المفاصل السبعة كلهم مع بعض (الذراع + التراك)، فالروبوت يقدر يتحرك على التراك وهو بيحرك ذراعه في نفس الوقت.

## 1. Status

The MoveIt 2 config package (`ar4_moveit_config`) **is in this repo**
(`src/ar4_moveit_config/`): SRDF with the `ar4_arm` group (joints 1–7),
kinematics, OMPL planner config and `move_group` launch files. This guide
explains how it is built and used. (You can also regenerate it with the
MoveIt Setup Assistant from the URDF in `ar4_description`, but the shipped
config already matches the URDF.)

Install MoveIt 2 first:

```bash
sudo apt install ros-jazzy-moveit -y
```

## 2. Planning groups

### `ar4_arm` — the main group (joints 1–7 together)

```yaml
# ar4_moveit_config/config/ar4_palletizing.srdf
groups:
  - name: ar4_arm
    joints:
      - joint_7
      - joint_1
      - joint_2
      - joint_3
      - joint_4
      - joint_5
      - joint_6
```

### Why `joint_7` is inside the group

The 7th axis is part of the robot's kinematics, not a separate machine. The
pallet is long and the boxes land in different slots along it, so the arm
often needs the track to reach a slot. If `joint_7` were in a separate group,
every place motion would need two separate plans (move track, then move arm),
and MoveIt could not find the short combined motion (slide while the arm
moves). With all 7 joints in one group, MoveIt plans the whole motion at once
and finds the shortest collision-free path to any pallet slot.

The alternative (two groups: `ar4_arm` = joints 1–6, `track` = `joint_7`
only) is simpler to set up but makes the palletizing code do two plans per
place. Start with one group; split only if a specific motion proves
impossible to plan that way.

### `gripper` — the gripper group

```yaml
groups:
  - name: gripper
    joints:
      - finger_left_joint
      - finger_right_joint
```

The 3-Claw is servo-driven (SG90), so in the real system the jaws are driven
by a servo position command, matching the position trajectory. In MoveIt the gripper group is used for named poses only:

- `open` — fingers at `finger_gap` (open)
- `close` — fingers at `finger_gap - finger_travel` (closed on the box)

The exact closed position depends on the real box width — still TBD (see
[hardware-checklist.md](hardware-checklist.md)).

## 3. Running MoveIt in RViz

```bash
# The package is in the repo (src/ar4_moveit_config)
ros2 launch ar4_moveit_config demo.launch.py
```

This opens RViz with the MotionPlanning plugin:

1. In the **MotionPlanning** panel, the planning group is `ar4_arm` and the
   start state is the robot's current state.
2. Drag the orange interactive marker to a target pose (or type a pose in the
   **Goal State** fields).
3. Press **Plan** to see the planned path (green), then **Execute** to run it
   on the simulated robot.
4. Or press **Plan & Execute** to do both at once.

Use the demo to test reachability before writing any code: if MoveIt cannot
plan to a pallet slot, either the slot is outside the workspace, or the URDF
dimensions (still placeholders — see [urdf-guide.md](urdf-guide.md)) are wrong.

## 4. Adding a new pose

Poses (home, pick approach, place slots, ...) are stored as named states in
the SRDF. Add one in the Setup Assistant (**Robot Poses** tab) or by hand:

```xml
<!-- ar4_moveit_config/config/ar4_palletizing.srdf -->
<group_state name="home" group="ar4_arm">
  <joint name="joint_7" value="0.4"/>
  <joint name="joint_1" value="0"/>
  <joint name="joint_2" value="0"/>
  <joint name="joint_3" value="0"/>
  <joint name="joint_4" value="0"/>
  <joint name="joint_5" value="0"/>
  <joint name="joint_6" value="0"/>
</group_state>
```

Notes:

- The numbers above are examples, not tuned values — pick the home pose so
  the arm is folded safely above the track, clear of the conveyor and the
  pallet.
- Every joint in the group needs a value in each named state, including
  `joint_7`. A good home for `joint_7` is the middle of the track, so the
  robot can reach both ends with a short slide.
- Named states are also the clean way for the palletizing node to command
  repeatable poses (home, safe retract) without hard-coding joint values in
  the application code.

## 5. Velocity and acceleration scaling — the slow track

The track (ball screw) is much slower than the arm joints. If MoveIt plans
the track at arm speed, the trajectory will demand more from the track motor
than it can deliver. Handle this in the MoveIt config:

- In `joint_limits.yaml`, set low `max_velocity` / `max_acceleration` for
  `joint_7` (real values TBD from the track motor + ball screw datasheet).
- In the application code, use `move_group.setMaxVelocityScalingFactor()` and
  `setMaxAccelerationScalingFactor()` — e.g. 0.5 for normal moves, lower
  (0.2–0.3) when carrying a box.
- The `joint_7` limit in the URDF already caps velocity at 0.2 m/s, but that
  is a **placeholder** — replace it with the real track speed once the motor
  is chosen.

Also: the arm should move slower while carrying a box than while moving
empty, even if the planner allows full speed. The palletizing node sets the
scaling factor per motion (fast when empty, slow when loaded).

## 6. Collision checking

MoveIt uses the URDF collision geometry. Right now that geometry is simple
boxes/cylinders (placeholders), so collision checking is approximate. Once
real STL meshes are exported (see [urdf-guide.md](urdf-guide.md)), keep the
collision geometry simplified — detailed meshes make planning slow and can
produce false collisions on small features. A common setup is: detailed mesh
for `<visual>`, simplified box/cylinder for `<collision>`.

Add the conveyor, pallet and boxes as **collision objects** in the planning
scene (from the palletizing node), so MoveIt plans around them instead of
through them. The table / floor the track sits on should be a collision object
too.

## 7. What to verify first (checklist)

- [ ] `demo.launch.py` opens and the robot appears in RViz
- [ ] Planning group `ar4_arm` lists all 7 joints (`joint_7`, `joint_1`–`joint_6`)
- [ ] A plan to a pose above the pick point succeeds
- [ ] A plan to the far end of the pallet succeeds **and** moves `joint_7`
      (if the track never moves, `joint_7` is not in the group)
- [ ] `joint_7` moves slowly — check the trajectory timing, not just the path
- [ ] The gripper group has `open` and `close` named states
