#!/usr/bin/env python3
"""Launch RViz with the MoveIt 2 plugin for the AR4 palletizing robot.

Loads the same robot description, SRDF, kinematics and planning config as
move_group.launch.py, then starts RViz. Add the "MotionPlanning" display in
RViz to plan and execute motions for the "ar4_arm" group.

Usage:
    ros2 launch ar4_moveit_config moveit_rviz.launch.py
    # (in a second terminal)
    ros2 launch ar4_moveit_config move_group.launch.py
"""
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    with open(absolute_file_path, "r") as file:
        return yaml.safe_load(file)


def generate_launch_description():
    desc_pkg = get_package_share_directory("ar4_description")
    moveit_pkg = get_package_share_directory("ar4_moveit_config")

    # Robot description (URDF from Xacro)
    xacro_file = os.path.join(desc_pkg, "urdf", "ar4_palletizing.urdf.xacro")
    robot_description = ParameterValue(
        Command(["xacro ", xacro_file]),
        value_type=str,
    )
    robot_description_config = {"robot_description": robot_description}

    # Semantic description (SRDF)
    srdf_file = os.path.join(moveit_pkg, "config", "ar4_palletizing.srdf")
    with open(srdf_file, "r") as file:
        robot_description_semantic_config = {
            "robot_description_semantic": file.read()
        }

    # Kinematics (KDL solver)
    robot_description_kinematics = {
        "robot_description_kinematics": load_yaml(
            "ar4_moveit_config", "config/kinematics.yaml"
        )
    }

    # Planning pipeline (OMPL, RRTConnect default)
    ompl_planning_pipeline_config = {
        "move_group": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": (
                "default_planner_request_adapters/AddTimeOptimalParameterization "
                "default_planner_request_adapters/ResolveConstraintFrames "
                "default_planner_request_adapters/FixWorkspaceBounds "
                "default_planner_request_adapters/CheckStartStateBounds "
                "default_planner_request_adapters/CheckStartStateCollision"
            ),
            "start_state_max_bounds_error": 0.1,
        },
        "ompl": load_yaml("ar4_moveit_config", "config/ompl_planning.yaml"),
    }

    # Joint limits
    moveit_joint_limits = {
        "robot_description_planning": load_yaml(
            "ar4_moveit_config", "config/joint_limits.yaml"
        )
    }

    # RViz config: use the package's moveit.rviz if it exists, otherwise
    # start plain RViz (add the MotionPlanning display manually).
    rviz_config = os.path.join(moveit_pkg, "config", "moveit.rviz")
    rviz_args = ["-d", rviz_config] if os.path.exists(rviz_config) else []

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        arguments=rviz_args,
        parameters=[
            robot_description_config,
            robot_description_semantic_config,
            robot_description_kinematics,
            ompl_planning_pipeline_config,
            moveit_joint_limits,
        ],
    )

    return LaunchDescription([rviz_node])
