#!/usr/bin/env python3
"""Start ros2_control for the AR4 palletizing robot.

Launches:
  - robot_state_publisher (from the main Xacro)
  - controller_manager (ros2_control_node) with config/ros2_controllers.yaml
  - spawners for joint_state_broadcaster, arm_controller, gripper_controller

Prerequisite: add the ros2_control include line to the main URDF first —
see config/ar4.ros2_control.xacro header. Until then the controller_manager
has no hardware and the spawners will fail.

Usage:
    ros2 launch ar4_control control.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_desc = get_package_share_directory('ar4_description')
    pkg_ctrl = get_package_share_directory('ar4_control')
    xacro_file = os.path.join(pkg_desc, 'urdf', 'ar4_palletizing.urdf.xacro')
    controllers_yaml = os.path.join(pkg_ctrl, 'config', 'ros2_controllers.yaml')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        name='controller_manager',
        parameters=[
            {'robot_description': robot_description},
            controllers_yaml,
        ],
        output='screen',
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen',
    )

    def spawner(name):
        return Node(
            package='controller_manager',
            executable='spawner',
            name=f'{name}_spawner',
            arguments=[name],
            output='screen',
        )

    # Spawners start a few seconds after the controller manager so it is
    # up and has loaded the hardware before they try to activate controllers.
    return LaunchDescription([
        controller_manager,
        robot_state_publisher,
        TimerAction(period=2.0, actions=[spawner('joint_state_broadcaster')]),
        TimerAction(period=3.0, actions=[spawner('arm_controller')]),
        TimerAction(period=4.0, actions=[spawner('gripper_controller')]),
    ])
