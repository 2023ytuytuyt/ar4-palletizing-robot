#!/usr/bin/env python3
"""Launch the palletizing application nodes.

Launches vision_node, conveyor_interface and palletizing_demo with the
parameters from config/palletizing_params.yaml. This launch does NOT start
MoveIt, Gazebo or the robot itself — run the bringup launch first
(ar4_bringup gazebo.launch.py + MoveIt config) and then this one.

Requires: ROS 2 Jazzy, the ar4_palletizing package built (colcon build).
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('ar4_palletizing')
    params = os.path.join(pkg, 'config', 'palletizing_params.yaml')

    return LaunchDescription([
        Node(
            package='ar4_palletizing',
            executable='vision_node',
            name='vision_node',
            parameters=[params],
            output='screen',
        ),
        Node(
            package='ar4_palletizing',
            executable='conveyor_interface',
            name='conveyor_interface',
            parameters=[params],
            output='screen',
        ),
        Node(
            package='ar4_palletizing',
            executable='palletizing_demo',
            name='palletizing_demo',
            parameters=[params],
            output='screen',
        ),
    ])
