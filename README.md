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
├── docs/
│   └── notes.md               # SolidWorks mesh export, MoveIt + ros2_control notes
└── src/
    ├── ar4_description/       # URDF/Xacro + RViz launch
    │   ├── package.xml
    │   ├── urdf/ar4_palletizing.urdf.xacro
    │   └── launch/view_robot.launch.py
    └── ar4_bringup/           # Gazebo launch (skeleton)
        ├── package.xml
        └── launch/gazebo.launch.py
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

# 4. Spawn it in Gazebo (skeleton — see docs/notes.md)
ros2 launch ar4_bringup gazebo.launch.py
```

## Roadmap

1. **URDF** — robot description with all 7 joints + gripper (done, placeholder geometry)
2. **RViz** — visualize, check joint limits and TF tree
3. **Gazebo** — simulate the arm, track, conveyor and boxes
4. **MoveIt 2** — planning group including `joint_7`, pick-and-place planning
5. **ros2_control** — JointTrajectoryController (Mock Components first, real hardware later)
6. **Palletizing demo** — vision → pick → move on track → place on pallet, in Gazebo

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
