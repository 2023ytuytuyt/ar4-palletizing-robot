#!/usr/bin/env python3
"""Conveyor interface node.

RULE: the conveyor STOPS at the pick point and the robot only picks from a
stopped belt. Never pick from a moving belt — the box position would change
between the vision measurement and the grasp.

Interface
---------
* Subscribes ``/conveyor/box_detected`` (std_msgs/Bool) — photoelectric /
  proximity sensor at the pick point. ``True`` = a box is at the pick point.
* Publishes ``/conveyor/stop`` (std_msgs/Bool) — ``True`` = conveyor motor
  stopped. This node asserts stop as soon as a box is detected, and the
  palletizing demo waits for this before starting a pick.
* Service ``/conveyor/set_stop`` (std_srvs/SetBool) — manual stop / resume
  (e.g. from a GUI or an operator button). ``True`` = stop, ``False`` = run.
* Publishes ``/conveyor/status`` (std_msgs/String) — human-readable state.

On real hardware ``/conveyor/stop`` would drive the conveyor motor
contactor / VFD enable through the PLC or a relay output. In simulation it
is only a signal other nodes react to.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool


class ConveyorInterface(Node):
    """Bridges the pick-point sensor and the conveyor stop command."""

    def __init__(self):
        super().__init__('conveyor_interface')
        self.declare_parameter('auto_stop_on_detect', True)

        self.stopped = False
        self.box_present = False

        self.stop_pub = self.create_publisher(Bool, '/conveyor/stop', 10)
        self.status_pub = self.create_publisher(String, '/conveyor/status', 10)
        self.create_subscription(Bool, '/conveyor/box_detected',
                                 self._on_box_detected, 10)
        self.create_service(SetBool, '/conveyor/set_stop',
                            self._on_set_stop)
        self.timer = self.create_timer(0.5, self._publish_status)
        self.get_logger().info('Conveyor interface ready (auto_stop=%s)'
                               % self.get_parameter('auto_stop_on_detect').value)

    def _on_box_detected(self, msg: Bool):
        self.box_present = bool(msg.data)
        if self.box_present and self.get_parameter('auto_stop_on_detect').value:
            if not self.stopped:
                self.get_logger().info('Box at pick point — STOPPING conveyor')
            self.set_stopped(True)
        elif not self.box_present and self.stopped:
            # Box was taken away; conveyor may run again.
            self.set_stopped(False)

    def _on_set_stop(self, request, response):
        self.set_stopped(bool(request.data))
        response.success = True
        response.message = ('conveyor stopped' if self.stopped
                            else 'conveyor running')
        return response

    def set_stopped(self, stopped: bool):
        self.stopped = stopped
        self.stop_pub.publish(Bool(data=stopped))

    def _publish_status(self):
        state = 'STOPPED' if self.stopped else 'RUNNING'
        box = 'box present' if self.box_present else 'no box'
        self.status_pub.publish(
            String(data='conveyor %s, %s' % (state, box)))


def main(args=None):
    rclpy.init(args=args)
    node = ConveyorInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
