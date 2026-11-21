# FAQ

> **ملخص عربي:** أسئلة سريعة بإجابات سريعة — ابدأ من هنا لو مستعجل.

## Do I need hardware to start?

**No.** The whole project starts in simulation on a laptop (Ubuntu 24.04 +
ROS 2 Jazzy): URDF in RViz, the arm in Gazebo, MoveIt planning, ros2_control
with Mock Components. That is 70–80% of the project. The real hardware
(Teensy 4.1, motors, SG90 servo) is swapped in later, and the layers
above ros2_control do not change. See [architecture.md](architecture.md) and
[setup.md](setup.md).

## Why is `joint_7` in the planning group?

Because the track is part of the robot. The pallet is long and the boxes land
in different slots along it, so the arm usually needs the track to reach a
slot. With `joint_7` in planning group `ar4_arm` (joints 1–7 together),
MoveIt plans arm + track motion in one plan and finds the shortest
collision-free path. A separate track group would force two plans per place
motion. See [moveit-guide.md](moveit-guide.md).

## Why classical OpenCV and not YOLO?

There is one box type, with a fixed rectangular shape, on a contrasting
conveyor, under fixed lighting, one box at a time at the pick point. That is
a threshold + contour problem: the box is found by brightness, its centre and
angle come from `minAreaRect`. A neural network adds a GPU, model files and
unexplained failure modes, and solves nothing extra here. A pretrained YOLO
would only be reconsidered if the setup changes (several box types, clutter,
unfixable lighting). See [vision-guide.md](vision-guide.md).

## What if `colcon build` fails?

Read the first error line — it usually names the missing dependency. Then:

```bash
cd ~/ar4_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

If the build is half-broken, clean and rebuild:

```bash
rm -rf build install log && colcon build
source install/setup.bash
```

If the error mentions a missing ROS package, install it:
`sudo apt install ros-jazzy-<package-name>`. More cases in
[setup.md](setup.md#7-troubleshooting).

## How do I replace the placeholder dimensions?

Every dimension in `src/ar4_description/urdf/ar4_palletizing.urdf.xacro` is a
named `xacro:property` at the top of the file, marked `MEASURE FROM
SOLIDWORKS`. Measure the real value in SolidWorks (distance between joint
axes for link lengths, Tools → Mass Properties for masses, usable stroke for
`track_travel`), edit only the property value, then re-check:

```bash
xacro src/ar4_description/urdf/ar4_palletizing.urdf.xacro > /tmp/ar4.urdf
check_urdf /tmp/ar4.urdf
ros2 launch ar4_description view_robot.launch.py
```

Full instructions — including mesh export (STL per link, mm→m scale) — are in
[urdf-guide.md](urdf-guide.md).

## Where do I start, in one line?

Install ROS 2 Jazzy, clone the repo, build it, and run the RViz launch:

```bash
git clone https://github.com/2023ytuytuyt/ar4-palletizing-robot.git ~/ar4_ws
cd ~/ar4_ws && colcon build && source install/setup.bash
ros2 launch ar4_description view_robot.launch.py
```

Then follow the roadmap in the [README](../README.md): Gazebo → MoveIt 2 →
ros2_control → palletizing demo.

## Which docs file do I need?

| Question | File |
|---|---|
| How does the whole system fit together? | [architecture.md](architecture.md) |
| How do I install and run things? | [setup.md](setup.md) |
| How is the URDF built / how do I fix dimensions? | [urdf-guide.md](urdf-guide.md) |
| How does planning work with the track? | [moveit-guide.md](moveit-guide.md) |
| How does the camera find the box? | [vision-guide.md](vision-guide.md) |
| What hardware is still undecided? | [hardware-checklist.md](hardware-checklist.md) |
| Mesh export, MoveIt and ros2_control notes | [notes.md](notes.md) |
