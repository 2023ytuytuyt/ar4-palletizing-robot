# URDF Guide — ar4_palletizing.urdf.xacro

> **ملخص عربي:** ملف الـ URDF هو وصف الروبوت — كل لينك ومفصل، من التراك لحد صوابع الجريبر. كل المقاسات اللي فيه دلوقتي تقريبية ومتعلمة "قيسها من السوليد" — الملف ده بيقولك إيه اللي يتقاس وإزاي تملاه بالأرقام الحقيقية.

## 1. File location

```
src/ar4_description/urdf/ar4_palletizing.urdf.xacro
```

It is a Xacro file (URDF + macros/properties), processed at launch time by
`xacro` into plain URDF for `robot_state_publisher`. Check that it expands
cleanly:

```bash
xacro src/ar4_description/urdf/ar4_palletizing.urdf.xacro > /tmp/ar4.urdf
check_urdf /tmp/ar4.urdf
```

## 2. Kinematic chain

```
world
  └─ joint_7 (prismatic, axis X) ── base_link          [7th axis: linear track]
       └─ joint_1 (revolute, axis Z) ── link1          [turret]
            └─ joint_2 (revolute, axis Y) ── link2     [upper arm]
                 └─ joint_3 (revolute, axis Y) ── link3 [forearm]
                      └─ joint_4 (revolute, axis Z) ── link4 [wrist roll]
                           └─ joint_5 (revolute, axis Y) ── link5 [wrist bend]
                                └─ joint_6 (revolute, axis Z) ── link6 [flange]
                                     └─ gripper_fixed (fixed) ── gripper_base [MHF2 body]
                                          ├─ finger_left_joint (prismatic, axis -Y) ── finger_left
                                          └─ finger_right_joint (prismatic, axis +Y) ── finger_right
```

Joint summary:

| Joint | Type | Parent → Child | Axis | Limit (placeholder) |
|---|---|---|---|---|
| `joint_7` | prismatic | `world` → `base_link` | X (1 0 0) | 0 → `track_travel` (0.8 m) |
| `joint_1` | revolute | `base_link` → `link1` | Z (0 0 1) | ±3.14 rad |
| `joint_2` | revolute | `link1` → `link2` | Y (0 1 0) | ±2.09 rad |
| `joint_3` | revolute | `link2` → `link3` | Y (0 1 0) | ±2.09 rad |
| `joint_4` | revolute | `link3` → `link4` | Z (0 0 1) | ±3.14 rad |
| `joint_5` | revolute | `link4` → `link5` | Y (0 1 0) | ±2.09 rad |
| `joint_6` | revolute | `link5` → `link6` | Z (0 0 1) | ±3.14 rad |
| `gripper_fixed` | fixed | `link6` → `gripper_base` | — | — |
| `finger_left_joint` | prismatic | `gripper_base` → `finger_left` | −Y (0 −1 0) | 0 → `finger_travel` |
| `finger_right_joint` | prismatic | `gripper_base` → `finger_right` | +Y (0 1 0) | 0 → `finger_travel` |

Rules that must stay true when you edit the file:

- Each joint's `<origin>` sits **on the previous joint's axis**, at the
  measured distance along the link. The link's visual/collision geometry is
  drawn from that origin.
- `joint_7` moves the **whole arm** along X. Its `lower` limit is 0 and its
  `upper` limit is the track travel — the arm starts at one end of the track.
- The gripper fingers slide along Y and close towards each other. In the real
  system the MHF2 is pneumatic (open/close), so the finger joints are
  position joints in simulation only.

## 3. Xacro properties — full list

All dimensions live as named `<xacro:property>` values at the top of the file.
**Every single one is a placeholder.** None of them is a measured value from
the SolidWorks design. Each is marked `MEASURE FROM SOLIDWORKS` in the file.

| Property | Placeholder value | What it really is — measure this |
|---|---|---|
| `track_travel` | 0.8 (m) | Real travel length of the linear track |
| `base_size_x` / `base_size_y` / `base_size_z` | 0.20 / 0.20 / 0.10 (m) | Carriage (moving base) size |
| `link1_height` | 0.10 (m) | Distance J1 axis → J2 axis |
| `link2_length` | 0.25 (m) | Distance J2 axis → J3 axis |
| `link3_length` | 0.22 (m) | Distance J3 axis → J4 axis |
| `link4_length` | 0.08 (m) | Distance J4 axis → J5 axis |
| `link5_length` | 0.07 (m) | Distance J5 axis → J6 axis |
| `link6_length` | 0.05 (m) | Distance J6 axis → gripper mount |
| `link1_radius` | 0.07 (m) | Turret radius |
| `link2_width` / `link3_width` | 0.06 / 0.05 (m) | Upper arm / forearm width |
| `wrist_radius` | 0.035 (m) | Wrist link radius |
| `gripper_body_x` / `gripper_body_y` / `gripper_body_z` | 0.04 / 0.05 / 0.04 (m) | MHF2 gripper body size |
| `finger_length` | 0.03 (m) | Finger length |
| `finger_width` | 0.008 (m) | Finger width |
| `finger_gap` | 0.02 (m) | Half-distance between fingers when open |
| `finger_travel` | 0.01 (m) | Closing travel per finger |
| `mass_base` | 2.0 (kg) | Carriage mass |
| `mass_link1` … `mass_link6` | 1.5 / 1.0 / 0.8 / 0.4 / 0.3 / 0.2 (kg) | Link masses |
| `mass_gripper` / `mass_finger` | 0.2 / 0.05 (kg) | Gripper body / finger mass |
| `j1_limit` … `j6_limit` | 3.14 / 2.09 / 2.09 / 3.14 / 2.09 / 3.14 (rad) | Joint limits |

Also placeholder (not properties, but hard-coded in the links): the inertia
values (`ixx`, `iyy`, `izz`) are small round numbers, and the joint
`effort` / `velocity` limits are guesses. Replace them with real values once
the masses and the motor datasheets are known.

## 4. Exporting real meshes from SolidWorks

The URDF currently uses simple box/cylinder geometry. To use the real design
from `last dance.zip` (assembly `01-last one.SLDASM`):

1. **Split the assembly into one part per link.** In SolidWorks, open the
   assembly and save each link as its own part: base carriage, turret (J1),
   upper arm (J2), forearm (J3), wrist roll (J4), wrist bend (J5), flange
   (J6), gripper body + the two MHF2 fingers.
2. **Export each part as STL** (binary, fine resolution). Use **File → Save
   As → STL**. STEP AP214 also works but needs conversion (e.g. `assimp` or
   FreeCAD) before Gazebo can use it — STL is simplest for RViz/Gazebo.
3. **Put the meshes in the package:**
   `src/ar4_description/meshes/<link>/<link>.stl` (one subfolder per link).
4. **Replace the geometry blocks** in the Xacro, e.g. for `link2`:
   ```xml
   <visual>
     <geometry>
       <mesh filename="package://ar4_description/meshes/link2/link2.stl"
             scale="0.001 0.001 0.001"/>
     </geometry>
   </visual>
   ```
   Do the same for the `<collision>` block (or keep a simplified box/cylinder
   for collision — simpler collision geometry makes Gazebo faster and more
   stable).
5. **Mind the units — mm → m scale.** SolidWorks works in millimetres; URDF
   works in metres. If the STL was exported in mm, use
   `scale="0.001 0.001 0.001"`. If it was exported in metres, use
   `scale="1 1 1"`. Check with a known feature: after loading in RViz, the
   link must be the right size. A 1000× too big or too small robot is almost
   always this scale factor.
6. **Check the mesh origin.** The STL's origin must match the joint origin
   used in the URDF (each joint origin sits on the previous joint's axis).
   If a mesh appears offset or rotated in RViz, add an `<origin xyz="..."
   rpy="..."/>` inside the `<visual>` / `<collision>` block to correct it —
   do not move the joint origins to fix a mesh offset.

## 5. Filling in the real link lengths and masses

1. In SolidWorks, open the assembly `01-last one.SLDASM`.
2. For each link, measure the **distance between the two joint axes** it
   connects (e.g. J2 axis → J3 axis = `link2_length`). Use the Measure tool
   between the two joint rotation axes, not between part edges.
3. For each link, use **Tools → Mass Properties** to read its mass. Use the
   mass of the link alone (without the motor, unless the motor is part of
   that link in the assembly).
4. Edit only the `<xacro:property>` values at the top of the file — the rest
   of the URDF uses those names, so one edit updates every link.
5. Measure the **track travel** the same way: distance between the two end
   positions of the carriage on the rail (or the ball screw's usable stroke),
   and put it in `track_travel`.
6. After every edit, re-run:
   ```bash
   xacro src/ar4_description/urdf/ar4_palletizing.urdf.xacro > /tmp/ar4.urdf
   check_urdf /tmp/ar4.urdf
   ros2 launch ar4_description view_robot.launch.py
   ```
   and check in RViz that the arm still looks right and the joints move
   within their limits.

## 6. Common mistakes

- **Guessing a dimension and forgetting it is a guess.** If a value is not
  measured, leave the `MEASURE FROM SOLIDWORKS` comment on it.
- **Mixing up link length and link body size.** `link2_length` is the distance
  between joint axes; the box drawn for `link2` is just its visible body.
  They are different numbers.
- **Wrong STL scale.** See step 5 above — the most common "my robot is huge"
  bug.
- **Moving joint origins to fix a mesh.** Fix the mesh `<origin>` instead;
  joint origins define the kinematics.
- **Forgetting the fingers.** The MHF2 fingers are separate links with their
  own joints. If you replace the gripper body mesh, replace the finger meshes
  too, or the fingers will float in the wrong place.
