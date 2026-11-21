#!/usr/bin/env python3
"""Launch move_group for the AR4 palletizing robot (MoveIt 2, ROS 2 Jazzy).

Loads the robot description from ar4_description, the SRDF, kinematics,
OMPL planning pipeline, joint limits and the controller configuration, and
starts the move_group node.

Usage:
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

    # Trajectory execution (controllers + joint limits)
    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }
    moveit_controllers = {
        "moveit_simple_controller_manager": load_yaml(
            "ar4_moveit_config", "config/moveit_controllers.yaml"
        ),
        "moveit_controller_manager": (
            "moveit_simple_controller_manager/MoveItSimpleControllerManager"
        ),
    }
    moveit_joint_limits = {
        "robot_description_planning": load_yaml(
            "ar4_moveit_config", "config/joint_limits.yaml"
        )
    }

    # Planning scene monitor (publishes the planning scene for RViz)
    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "planning_scene_monitor_options": {
            "name": "planning_scene_monitor",
            "robot_description": "robot_description",
            "joint_state_topic": "/joint_states",
            "attached_collision_object_topic": "/move_group/attached_collision_object",
            "publish_planning_scene_topic": "/move_group/monitored_planning_scene",
            "monitored_planning_scene_topic": "/move_group/monitored_planning_scene",
            "wait_for_initial_state_timeout": 10.0,
        },
    }

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description_config,
            robot_description_semantic_config,
            robot_description_kinematics,
            ompl_planning_pipeline_config,
            trajectory_execution,
            moveit_controllers,
            moveit_joint_limits,
            planning_scene_monitor_parameters,
        ],
    )

    return LaunchDescription([move_group_node])
