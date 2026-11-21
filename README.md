# AR4 Palletizing Robot — ROS 2 Simulation

> **ملخص عربي:** مشروع تخرج — ذراع روبوت AR4 بستة محاور دوّارة مركّب على محور سابع خطي (تراك ألومنيوم + ball screw) لرصّ صناديق صغيرة جدًا جاية على سير ناقل، مع جريبر SMC MHF2-8D1 بصابعين. المشروع ده سيميوليشن ROS 2 (Jazzy) الأول، والهاردوير ييجي بعدين.

## What this is

A ROS 2 (Jazzy) simulation of a palletizing robot arm for the graduation project:

- **6-axis AR4 arm** (Annin Robotics AR4, 3D-printed parts) for pick-and-place
- **7th axis: linear track** — aluminium extrusion rail + ball screw, moving the whole arm along the pallet row
- **Gripper: SMC MHF2-8D1**, two-finger pneumatic gripper
- **Conveyor + computer vision** — very small boxes arrive on a conveyor; a fixed camera + classical OpenCV (threshold, contours, ArUco) locates each box before picking
- **Stack:** ROS 2 Jazzy, URDF/Xacro, RViz, Gazebo, MoveIt 2, ros2_control

## Hardware summary

| Part | Details |
|---|---|
| Arm | AR4, 6 revolute joints (J1–J6) |
| 7th axis | Prismatic joint on a linear track (ball screw). Travel length: **TBD — measure from SolidWorks** (0.8 m in the URDF is only a placeholder) |
| Gripper | SMC MHF2-8D1, two-finger pneumatic |
| Boxes | Very small — exact dimensions/weight TBD |
| Vision | Fixed USB camera above the pick point (eye-to-hand), OpenCV via cv_bridge |
| Control (later) | Teensy 4.1 + AR4HardwareInterface, JointTrajectoryController at 60 Hz |

## Repo layout

```
ar4-palletizing-robot/
├── README.md
├── .gitignore
├── docs/                      # Full documentation (see docs/faq.md for the index)
│   ├── architecture.md        # System overview + package map
│   ├── setup.md               # Install + build + run guide
│   ├── urdf-guide.md          # URDF structure + SolidWorks mesh export
│   ├── moveit-guide.md        # Planning groups, joint_7 in MoveIt
│   ├── vision-guide.md        # Classical OpenCV box detection
│   ├── hardware-checklist.md  # Hardware TODO (all open)
│   ├── faq.md
│   └── notes.md               # SolidWorks mesh export, MoveIt + ros2_control notes
└── src/
    ├── ar4_description/       # URDF/Xacro + RViz launch
    ├── ar4_moveit_config/     # MoveIt 2: SRDF, kinematics, OMPL, move_group
    ├── ar4_control/           # ros2_control: controllers + Mock hardware
    ├── ar4_gazebo/            # Gazebo world (track, conveyor, pallet, boxes, camera)
    ├── ar4_bringup/           # Gazebo launch (skeleton — see ar4_gazebo)
    └── ar4_palletizing/       # Demo app: state machine, vision node, conveyor interface
```

## Setup

Requirements: **Ubuntu 24.04 + ROS 2 Jazzy**.

```bash
# 1. Install ROS 2 Jazzy (desktop-full) and tools
sudo apt install ros-jazzy-desktop-full python3-colcon-common-extensions python3-rosdep -y
sudo rosdep init && rosdep update
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc && source ~/.bashrc

# 2. Clone and build
git clone <this-repo-url> ~/ar4_ws
cd ~/ar4_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash

# 3. View the robot in RViz
ros2 launch ar4_description view_robot.launch.py

# 4. Run the full simulation (Gazebo world + controllers)
ros2 launch ar4_gazebo palletizing_world.launch.py

# 5. MoveIt 2 planning (separate terminal)
ros2 launch ar4_moveit_config move_group.launch.py
ros2 launch ar4_moveit_config moveit_rviz.launch.py

# 6. Palletizing demo (vision + state machine + conveyor)
ros2 launch ar4_palletizing palletizing_demo.launch.py
```

> First run on a fresh machine: the URDF dimensions are placeholders marked
> `MEASURE FROM SOLIDWORKS` — measure the real values from the SolidWorks
> assembly and fill them in before trusting any simulation result. See
> [docs/urdf-guide.md](docs/urdf-guide.md) and [docs/setup.md](docs/setup.md).

## Roadmap

1. **URDF** — robot description with all 7 joints + gripper ✅ (placeholder geometry — measure real values from SolidWorks)
2. **RViz** — visualize, check joint limits and TF tree ✅ (`ar4_description`)
3. **Gazebo** — simulate the arm, track, conveyor and boxes ✅ (`ar4_gazebo/palletizing_world.sdf`)
4. **MoveIt 2** — planning group including `joint_7`, pick-and-place planning ✅ (`ar4_moveit_config`)
5. **ros2_control** — JointTrajectoryController (Mock Components first, real hardware later) ✅ (`ar4_control`)
6. **Palletizing demo** — vision → pick → move on track → place on pallet, in Gazebo ✅ (`ar4_palletizing`)

> ✅ = code is in the repo. It has NOT been run on a ROS 2 machine yet — the
> first `colcon build` + launch must happen on Ubuntu 24.04 with ROS 2 Jazzy,
> then real dimensions from SolidWorks replace the placeholders.

## TODO (open items)

- [ ] Exact box dimensions (cm) and weight
- [ ] Actual 7th-axis track travel length (measure from SolidWorks — replace the 0.8 m placeholder)
- [ ] Pallet pattern (boxes per row, number of layers)
- [ ] MHF2 pneumatic supply: compressor/air source, solenoid valve, regulator, hoses
- [ ] Power supply for the arm + track motor
- [ ] Emergency stop
- [ ] Limit switches at both ends of the track
- [ ] Conveyor: does it stop at the pick point, or run continuously? (recommended: stop at pick point + photoelectric/proximity sensor)
- [ ] Export real link meshes from SolidWorks (STEP/STL) and replace the placeholder box/cylinder geometry in the URDF
- [ ] Measure real link lengths, masses and inertias from SolidWorks and fill in the `MEASURE FROM SOLIDWORKS` properties in the Xacro
