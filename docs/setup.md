# Setup Guide — AR4 Palletizing Robot

> **ملخص عربي:** من الصفر لحد ما تشوف الروبوت بيتحرك في RViz و Gazebo — تنصيب Ubuntu 24.04 و ROS 2 Jazzy، وبعدين clone وبناء وتشغيل، بالترتيب، ومع حل أشهر الأخطاء.

## 1. Requirements

| Item | Version |
|---|---|
| OS | Ubuntu 24.04 (Noble) — 64-bit, desktop |
| ROS 2 | Jazzy Jalisco (the ROS 2 release for Ubuntu 24.04) |
| Disk | ~10 GB free for ROS 2 desktop-full + Gazebo |
| Network | Internet for `apt` and `rosdep` |

No robot hardware is needed. Everything in this guide runs in simulation.

## 2. Install ROS 2 Jazzy

Run the commands in order. Copy-paste one block at a time and check for errors
before moving on.

```bash
# 2.1 Locale (ROS 2 needs UTF-8)
sudo apt update && sudo apt install locales software-properties-common curl -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2.2 Enable the universe repository
sudo add-apt-repository universe

# 2.3 Add the ROS 2 apt repository and key
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 2.4 Install ROS 2 Jazzy (desktop-full = RViz + Gazebo + tools)
sudo apt update
sudo apt install ros-jazzy-desktop-full -y

# 2.5 Install build tools
sudo apt install python3-colcon-common-extensions python3-rosdep -y
sudo rosdep init
rosdep update
```

### 2.6 Source ROS 2 in every new terminal

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 3. Verify the installation

Open two terminals:

```bash
# Terminal 1
ros2 run demo_nodes_cpp talker
```

```bash
# Terminal 2
ros2 run demo_nodes_py listener
```

If Terminal 2 prints `Hello World` messages, ROS 2 works. (Close both with
`Ctrl+C`.)

## 4. Clone the repo and build

```bash
# 4.1 Clone into a workspace
git clone https://github.com/2023ytuytuyt/ar4-palletizing-robot.git ~/ar4_ws
cd ~/ar4_ws

# 4.2 Install package dependencies
rosdep install --from-paths src --ignore-src -r -y

# 4.3 Build
colcon build

# 4.4 Source the workspace (do this in every new terminal, after sourcing ROS)
source ~/ar4_ws/install/setup.bash
```

Tip: add the workspace source line to `~/.bashrc` after the ROS line, so you
do not have to type it every time:

```bash
echo "source ~/ar4_ws/install/setup.bash" >> ~/.bashrc
```

## 5. Run it, in order

Do the steps in this order — each one builds on the previous one.

### Step 1 — View the robot in RViz

```bash
ros2 launch ar4_description view_robot.launch.py
```

What you should see: the robot model in RViz and a **Joint State Publisher**
window with sliders. Move the sliders — including `joint_7` — and the robot
moves. This checks that the URDF parses and the TF tree is correct.

> Note: all link lengths, masses and the `joint_7` travel in the URDF are
> placeholders marked `MEASURE FROM SOLIDWORKS` (see
> [urdf-guide.md](urdf-guide.md)). The model will look right in shape, but do
> not trust any reach or dynamics numbers until the real values are filled in.

### Step 2 — Spawn the robot in Gazebo

```bash
ros2 launch ar4_bringup gazebo.launch.py
```

What you should see: Gazebo opens with an empty world and the robot spawned
in it. This is a skeleton launch — the conveyor, pallet and boxes worlds are
not built yet (see [architecture.md](architecture.md)).

### Step 3 — MoveIt 2 demo

```bash
# Package ar4_moveit_config is in the repo (src/ar4_moveit_config)
ros2 launch ar4_moveit_config demo.launch.py
```

This will open RViz with the MotionPlanning plugin: drag the interactive
marker to a target pose, press **Plan & Execute**, and watch the arm + track
move. See [moveit-guide.md](moveit-guide.md) for the planning groups.

### Step 4 — Palletizing demo

```bash
# Package ar4_palletizing is in the repo (src/ar4_palletizing)
ros2 launch ar4_bringup palletizing.launch.py
```

This will bring up Gazebo + MoveIt + control + vision + the demo state
machine together, and run full pick-and-place cycles from the conveyor to the
pallet.

## 6. Everyday workflow

```bash
cd ~/ar4_ws
colcon build --packages-select <package_name>   # rebuild one package
source install/setup.bash                       # re-source after every build
ros2 launch <package> <launch_file>.py          # run something
```

After editing the Xacro, rebuild `ar4_description` and re-run the launch —
`robot_state_publisher` reads the Xacro at launch time, so a rebuild is enough.

## 7. Troubleshooting

### `xacro: command not found` / `package 'xacro' not found`

The `xacro` package is part of `ros-jazzy-desktop-full`. If it is missing:

```bash
sudo apt install ros-jazzy-xacro ros-jazzy-urdf ros-jazzy-robot-state-publisher -y
```

Then rebuild: `cd ~/ar4_ws && colcon build`.

### `ros2 launch ...` says the package is not found

You forgot to source the workspace, or you built in a different terminal.
Run:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ar4_ws/install/setup.bash
ros2 pkg list | grep ar4
```

If the package still does not appear, rebuild: `cd ~/ar4_ws && colcon build`.

### `colcon build` fails with a CMake error

- Check that `CMakeLists.txt` exists in the package (every package needs one).
- Read the first error line in the output — it usually names the missing
  dependency. Install it with `sudo apt install ros-jazzy-<name>` or add it
  to the package's `package.xml`, then run `rosdep install --from-paths src
  --ignore-src -r -y` again.
- If the build is half-broken, clean and rebuild:
  `cd ~/ar4_ws && rm -rf build install log && colcon build`.

### Controller spawner fails (`controller_manager` / `spawner` errors)

- Make sure `ros2_control` is installed:
  `sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers -y`.
- Check the controller YAML: joint names must match the URDF exactly
  (`joint_7`, `joint_1` … `joint_6`). A typo in one joint name stops the
  spawner.
- Check that the `ros2_control` node is actually running before the spawner
  starts — the launch file order matters (controller manager first, spawner
  second).

### `gz_sim` not found / Gazebo does not start

Gazebo (gz sim) comes with `ros-jazzy-desktop-full`. If it is missing:

```bash
sudo apt install ros-jazzy-ros-gz -y
gz sim --version
```

Also check the `ros_gz_sim` package is found: `ros2 pkg list | grep ros_gz`.
If Gazebo opens but the robot does not appear, check the spawn node output —
it needs the `robot_description` topic, which `robot_state_publisher`
publishes.

### `joint_state_publisher_gui` not found

```bash
sudo apt install ros-jazzy-joint-state-publisher-gui -y
```

Then rebuild the workspace (`colcon build`) — the launch file references
this package, and rosdep should have installed it; if it did not, the
manual install above fixes it.

### RViz shows the robot but joints do not move with the sliders

- Check the `joint_state_publisher_gui` node is running (`ros2 node list`).
- Check the joint names in RViz's **RobotModel → Description Topic** are the
  ones from the URDF (`joint_1` … `joint_7`, `finger_left_joint`,
  `finger_right_joint`).
- If the model is grey/white, the material colours come from the Xacro —
  that is cosmetic only.

### Everything was working, now nothing launches

The most common cause is a terminal that was opened before the last build.
Close it, open a fresh terminal, source ROS + workspace again, and retry.
