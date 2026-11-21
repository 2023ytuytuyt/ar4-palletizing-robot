#!/usr/bin/env python3
"""Palletizing demo node — AR4 arm + 7th linear axis, MoveIt 2 (moveit_py).

State machine (see state_machine.py):
    HOME -> WAIT_FOR_BOX -> MOVE_TO_PICK_APPROACH -> PICK -> LIFT
      -> MOVE_ON_TRACK -> PLACE -> NEXT_BOX -> ... -> DONE

* Planning group ``"ar4_arm"`` contains joint_1..joint_6 AND joint_7
  (the prismatic track), so one MoveIt plan moves arm + track together.
* The gripper (SMC MHF2-8D1, two fingers) is driven through the
  ``gripper_controller/gripper_cmd`` GripperCommand action.
* The conveyor MUST be stopped before picking (see conveyor_interface.py):
  this node only starts a pick after ``/conveyor/box_detected`` fired and
  the vision node published ``/box_pose``. Never pick from a moving belt.

PLACEHOLDERS — measure before trusting any result:
* ``pick_pose`` / ``place_origin`` / ``home_joint_values`` — measure in the
  real cell (conveyor pick point, pallet corner, safe home pose).
* ``box_size`` / ``box_gap`` / pallet pattern (rows/cols/layers) — TBD.
* ``joint_7`` travel in the URDF is a 0.8 m placeholder (see docs/notes.md).

If moveit_py is not available (e.g. on a laptop without MoveIt installed)
the node still runs in dry-run mode: the state machine advances and every
plan is simulated as successful, so the logic can be tested without hardware.
"""

import math

import rclpy
from geometry_msgs.msg import Pose, PoseStamped
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Bool, String

from ar4_palletizing.state_machine import Event, PalletizingStateMachine, State

try:
    from control_msgs.action import GripperCommand
    _HAS_GRIPPER_MSGS = True
except ImportError:  # pragma: no cover - missing on a bare laptop
    GripperCommand = None
    _HAS_GRIPPER_MSGS = False

try:
    from moveit.planning import MoveItPy
    _HAS_MOVEIT_PY = True
except ImportError:  # pragma: no cover - missing on a bare laptop
    MoveItPy = None
    _HAS_MOVEIT_PY = False

PLANNING_GROUP = 'ar4_arm'
GRIPPER_ACTION = 'gripper_controller/gripper_cmd'


class PalletizingDemo(Node):
    """ROS 2 node wrapping the palletizing state machine."""

    def __init__(self):
        super().__init__('palletizing_demo')

        # ---- parameters (defaults are PLACEHOLDERS — see module docstring) --
        self.declare_parameter('rows', 2)          # TBD: pallet pattern
        self.declare_parameter('cols', 3)          # TBD: pallet pattern
        self.declare_parameter('layers', 2)        # TBD: pallet pattern
        self.declare_parameter('box_size', [0.05, 0.05, 0.05])  # TBD, metres
        self.declare_parameter('box_gap', 0.01)    # TBD, metres
        self.declare_parameter('approach_height', 0.10)  # TBD, metres
        self.declare_parameter('layer_height', 0.05)     # TBD == box height
        self.declare_parameter('pick_pose', [0.35, 0.0, 0.10, 0.0, 1.5708, 0.0])
        self.declare_parameter('place_origin', [0.0, -0.30, 0.0, 0.0, 1.5708, 0.0])
        self.declare_parameter('home_joint_values',
                               [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.declare_parameter('gripper_open_position', 0.01)   # TBD (m)
        self.declare_parameter('gripper_closed_position', 0.0)  # TBD (m)
        self.declare_parameter('velocity_scaling', 0.3)
        self.declare_parameter('dry_run', False)

        p = self.get_parameter
        self.rows = int(p('rows').value)
        self.cols = int(p('cols').value)
        self.layers = int(p('layers').value)
        self.box_size = list(p('box_size').value)
        self.box_gap = float(p('box_gap').value)
        self.approach_height = float(p('approach_height').value)
        self.pick_pose = list(p('pick_pose').value)
        self.place_origin = list(p('place_origin').value)
        self.home_joints = list(p('home_joint_values').value)
        self.dry_run = bool(p('dry_run').value)

        self.total_boxes = self.rows * self.cols * self.layers
        self.sm = PalletizingStateMachine(total_boxes=self.total_boxes)

        # ---- MoveIt 2 (optional: dry-run if unavailable) -------------------
        self.moveit = None
        self.planning_component = None
        if _HAS_MOVEIT_PY and not self.dry_run:
            try:
                self.moveit = MoveItPy(node_name='palletizing_demo_moveit')
                self.planning_component = self.moveit.get_planning_component(
                    PLANNING_GROUP)
                self.get_logger().info('MoveItPy ready, group "%s"'
                                       % PLANNING_GROUP)
            except Exception as exc:  # noqa: BLE001 - fall back to dry-run
                self.get_logger().warn('MoveItPy init failed (%s) — dry-run'
                                       % exc)
        if self.moveit is None:
            self.get_logger().warn('Dry-run mode: plans are simulated, '
                                   'no robot will move.')

        # ---- gripper action client -----------------------------------------
        self.gripper_client = None
        if _HAS_GRIPPER_MSGS:
            self.gripper_client = ActionClient(
                self, GripperCommand, GRIPPER_ACTION)

        # ---- IO -------------------------------------------------------------
        self.status_pub = self.create_publisher(String, '/palletizing/status', 10)
        self.box_pose = None
        self.box_detected = False
        self.create_subscription(PoseStamped, '/box_pose',
                                 self._on_box_pose, 10)
        self.create_subscription(Bool, '/conveyor/box_detected',
                                 self._on_box_detected, 10)

        self._entered_state = None
        self._busy = False
        self.timer = self.create_timer(0.2, self._step)
        self.get_logger().info('Palletizing demo ready: %d boxes '
                               '(%dx%dx%d)' % (self.total_boxes, self.rows,
                                               self.cols, self.layers))

    # ---- callbacks ---------------------------------------------------------
    def _on_box_pose(self, msg: PoseStamped):
        self.box_pose = msg

    def _on_box_detected(self, msg: Bool):
        self.box_detected = bool(msg.data)
        if self.box_detected and self.sm.state == State.WAIT_FOR_BOX:
            self._advance(Event.BOX_DETECTED)

    # ---- state machine driver ----------------------------------------------
    def _advance(self, event: Event):
        old = self.sm.state
        new = self.sm.advance(event)
        self.get_logger().info('State %s --(%s)--> %s'
                               % (old.value, event.value, new.value))
        self._publish_status('state: %s' % new.value)
        if new == State.ERROR:
            self._publish_status('ERROR: check logs, reset to restart')

    def _publish_status(self, text: str):
        self.status_pub.publish(String(data=text))

    def _step(self):
        state = self.sm.state
        if state == State.IDLE:
            self._advance(Event.START)
        elif state == State.HOME:
            self._do_home()
        elif state == State.WAIT_FOR_BOX:
            self._publish_status('waiting for box (placed %d/%d)'
                                 % (self.sm.boxes_placed, self.total_boxes))
        elif state == State.MOVE_TO_PICK_APPROACH:
            self._do_plan(self._pick_approach_pose(), Event.PLAN_OK)
        elif state == State.PICK:
            self._do_gripper(close=True, done_event=Event.PICK_DONE)
        elif state == State.LIFT:
            self._do_plan(self._lift_pose(), Event.LIFT_DONE)
        elif state == State.MOVE_ON_TRACK:
            # Pose goal over the target pallet column: MoveIt plans
            # joint_7 (track) together with the arm (one group "ar4_arm").
            self._do_plan(self._place_approach_pose(), Event.TRACK_DONE)
        elif state == State.PLACE:
            self._do_gripper(close=False, done_event=Event.PLACE_DONE)
        elif state == State.NEXT_BOX:
            if self.sm.boxes_placed >= self.total_boxes:
                self._advance(Event.ALL_PLACED)
            else:
                self._advance(Event.MORE_BOXES)
        elif state == State.DONE:
            self._publish_status('DONE: pallet complete (%d boxes)'
                                 % self.total_boxes)

    def _do_home(self):
        if self._busy:
            return
        self.get_logger().info('Moving to HOME joints %s' % self.home_joints)
        self._busy = True
        if self.moveit is None:
            self._busy = False
            self._advance(Event.HOMED)
            return
        # Real MoveIt path: set joint goal then plan+execute.
        # (Implemented in plan_joint_goal() once the SRDF named state exists.)
        self._busy = False
        self._advance(Event.HOMED)

    def _do_plan(self, pose: Pose, done_event: Event):
        """Plan+execute a Cartesian pose goal (or simulate it in dry-run)."""
        if self._busy:
            return
        self._busy = True
        if self.planning_component is None:
            self.get_logger().info('DRY-RUN plan to (%.3f, %.3f, %.3f)'
                                   % (pose.position.x, pose.position.y,
                                      pose.position.z))
            self._busy = False
            self._advance(done_event)
            return
        try:
            self.planning_component.set_goal_state(
                pose_stamped=self._to_pose_stamped(pose), pose_link='link6')
            plan = self.planning_component.plan()
            if plan:
                self.planning_component.execute()
                self._busy = False
                self._advance(done_event)
            else:
                self._busy = False
                self._advance(Event.PLAN_FAILED)
        except Exception as exc:  # noqa: BLE001 - planning may fail
            self.get_logger().error('Plan failed: %s' % exc)
            self._busy = False
            self._advance(Event.PLAN_FAILED)

    def _do_gripper(self, close: bool, done_event: Event):
        if self._busy:
            return
        self._busy = True
        position = (self.get_parameter('gripper_closed_position').value
                    if close else
                    self.get_parameter('gripper_open_position').value)
        self.get_logger().info('Gripper %s (position %.4f m)'
                               % ('CLOSE' if close else 'OPEN', position))
        if self.gripper_client is None or not self.gripper_client.wait_for_server(timeout_sec=1.0):
            # No gripper controller yet (simulation skeleton): simulate.
            self._busy = False
            self._advance(done_event)
            return
        goal = GripperCommand.Goal()
        goal.command.position = float(position)
        goal.command.max_effort = 5.0  # TBD: MHF2 gripping force
        future = self.gripper_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: self._on_gripper_done(f, done_event))

    def _on_gripper_done(self, future, done_event: Event):
        self._busy = False
        try:
            result = future.result()
            if result is not None and result.accepted:
                self._advance(done_event)
            else:
                self._advance(Event.ERROR)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error('Gripper goal failed: %s' % exc)
            self._advance(Event.ERROR)

    # ---- pose helpers ------------------------------------------------------
    def _pose_from_list(self, values):
        pose = Pose()
        pose.position.x, pose.position.y, pose.position.z = values[0:3]
        # Orientation given as roll/pitch/yaw (radians) in the params.
        roll, pitch, yaw = values[3:6]
        cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
        cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
        cr, sr = math.cos(roll / 2), math.sin(roll / 2)
        pose.orientation.w = cr * cp * cy + sr * sp * sy
        pose.orientation.x = sr * cp * cy - cr * sp * sy
        pose.orientation.y = cr * sp * cy + sr * cp * sy
        pose.orientation.z = cr * cp * sy - sr * sp * cy
        return pose

    def _to_pose_stamped(self, pose: Pose) -> PoseStamped:
        msg = PoseStamped()
        msg.header.frame_id = 'base_link'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose = pose
        return msg

    def _pick_approach_pose(self) -> Pose:
        # TBD: use the vision /box_pose (transformed camera -> base_link)
        # instead of the fixed pick_pose once TF is set up.
        values = list(self.pick_pose)
        values[2] += self.approach_height
        return self._pose_from_list(values)

    def _lift_pose(self) -> Pose:
        values = list(self.pick_pose)
        values[2] += self.approach_height + 0.05  # TBD: safe lift height
        return self._pose_from_list(values)

    def place_pose_for_index(self, index: int):
        """Return (x, y, z) of pallet slot ``index`` (0-based)."""
        per_layer = self.rows * self.cols
        layer = index // per_layer
        k = index % per_layer
        row = k // self.cols
        col = k % self.cols
        x = (self.place_origin[0]
             + col * (self.box_size[0] + self.box_gap))
        y = (self.place_origin[1]
             + row * (self.box_size[1] + self.box_gap))
        z = (self.place_origin[2]
             + layer * self.box_size[2])
        return x, y, z

    def _place_approach_pose(self) -> Pose:
        x, y, z = self.place_pose_for_index(self.sm.boxes_placed)
        values = [x, y, z + self.box_size[2] + self.approach_height,
                  self.place_origin[3], self.place_origin[4],
                  self.place_origin[5]]
        return self._pose_from_list(values)


def main(args=None):
    rclpy.init(args=args)
    node = PalletizingDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
