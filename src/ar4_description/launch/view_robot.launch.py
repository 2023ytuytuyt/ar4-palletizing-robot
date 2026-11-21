#!/usr/bin/env python3
"""View the AR4 palletizing robot in RViz.

Launches robot_state_publisher (from the Xacro), joint_state_publisher_gui
(sliders to move the joints by hand, including joint_7 on the track) and RViz.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg = get_package_share_directory('ar4_description')
    xacro_file = os.path.join(pkg, 'urdf', 'ar4_palletizing.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(pkg, 'rviz', 'view_robot.rviz')]
            if os.path.exists(os.path.join(pkg, 'rviz', 'view_robot.rviz'))
            else [],
        ),
    ])
