#!/usr/bin/env python3
"""Spawn the AR4 palletizing robot in Gazebo (ros_gz_sim).

NOTE: this is the OLD minimal launch (empty world, skeleton). The main
simulation launch is now ar4_gazebo:
    ros2 launch ar4_gazebo palletizing_world.launch.py
which starts the full palletizing cell (track, conveyor + boxes, pallet,
fixed camera) plus ros2_control. This file is kept for quick empty-world
tests only.
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
    xacro_file = os.path.join(pkg_desc, 'urdf', 'ar4_palletizing.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    return LaunchDescription([
        # Gazebo (empty world for now — add conveyor, pallet and boxes later)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gz, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': '-r empty.sdf'}.items(),
        ),
        # Publish robot description + TF
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        # Spawn the robot in Gazebo
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
        # TODO: add ros_gz_bridge for /clock and joint states once the
        # ros2_control Gazebo plugins are added to the URDF.
    ])
