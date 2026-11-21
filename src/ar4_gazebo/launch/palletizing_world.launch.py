#!/usr/bin/env python3
"""Launch the full AR4 palletizing cell in Gazebo (main simulation launch).

Starts:
  - Gazebo Harmonic with worlds/palletizing_world.sdf (track, conveyor + 3
    boxes, pallet, fixed camera above the pick point)
  - robot_state_publisher + spawn of the AR4 URDF on the track
  - ros_gz_bridge (config/gz_bridge.yaml — /clock, camera later)
  - ros2_control: controller_manager + joint_state_broadcaster,
    arm_controller, gripper_controller (via ar4_control/control.launch.py)

Prerequisite: add the ros2_control include line to the main URDF first —
see ar4_description/config/ar4.ros2_control.xacro header.

Usage:
    ros2 launch ar4_gazebo palletizing_world.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_desc = get_package_share_directory('ar4_description')
    pkg_gz = get_package_share_directory('ros_gz_sim')
    pkg_ctrl = get_package_share_directory('ar4_control')
    pkg_cell = get_package_share_directory('ar4_gazebo')

    xacro_file = os.path.join(pkg_desc, 'urdf', 'ar4_palletizing.urdf.xacro')
    world_file = os.path.join(pkg_cell, 'worlds', 'palletizing_world.sdf')
    bridge_yaml = os.path.join(pkg_cell, 'config', 'gz_bridge.yaml')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    return LaunchDescription([
        # Gazebo with the palletizing world
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gz, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': f'-r {world_file}'}.items(),
        ),
        # Publish robot description + TF
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen',
        ),
        # Spawn the robot on the track (same pose as the old bringup launch)
        Node(
            package='ros_gz_sim',
            executable='create',
            name='spawn_ar4',
            arguments=[
                '-topic', 'robot_description',
                '-name', 'ar4_palletizing',
                '-x', '0.0', '-y', '0.0', '-z', '0.1',
            ],
            output='screen',
        ),
        # Gazebo <-> ROS bridge (/clock; camera entries are in the yaml)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_bridge',
            parameters=[{'config_file': bridge_yaml}],
            output='screen',
        ),
        # ros2_control: controller manager + spawners
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ctrl, 'launch', 'control.launch.py')
            ),
        ),
    ])
