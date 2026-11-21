#!/usr/bin/env python3
"""Box vision node — classical OpenCV only (no deep learning, no YOLO).

Subscribes to the fixed camera above the pick point (eye-to-hand),
finds the box with threshold -> contours -> largest contour ->
``cv2.minAreaRect`` (see vision_utils.detect_box) and publishes:

* ``/box_pose`` (geometry_msgs/PoseStamped) — box centre + yaw angle,
  in the CAMERA frame. The demo node must transform camera -> base_link
  with TF (camera calibration + hand-eye transform, still TBD).
* ``/vision/debug_image`` (sensor_msgs/Image) — image with the detected
  rectangle drawn, for RViz / rqt_image_view.

The z position is 0.0 in the camera frame: the box lies on the conveyor
plane, so the real height comes from the known conveyor height (TBD).
"""

import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from sensor_msgs.msg import Image

from ar4_palletizing.vision_utils import detect_box, draw_detection

try:
    import cv2
    _HAS_CV2 = True
except ImportError:  # pragma: no cover - opencv not installed
    cv2 = None
    _HAS_CV2 = False


class VisionNode(Node):
    """ROS 2 node wrapping :func:`vision_utils.detect_box`."""

    def __init__(self):
        super().__init__('vision_node')

        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('threshold_value', 127)
        self.declare_parameter('min_contour_area', 100.0)
        self.declare_parameter('invert', True)  # dark box on light conveyor
        self.declare_parameter('camera_frame', 'camera_frame')  # TBD: TF name

        p = self.get_parameter
        self.threshold_value = int(p('threshold_value').value)
        self.min_contour_area = float(p('min_contour_area').value)
        self.invert = bool(p('invert').value)
        self.camera_frame = str(p('camera_frame').value)

        self.bridge = CvBridge()
        self.pose_pub = self.create_publisher(PoseStamped, '/box_pose', 10)
        self.debug_pub = self.create_publisher(Image, '/vision/debug_image', 10)
        self.create_subscription(
            Image, str(p('camera_topic').value), self._on_image, 10)
        self.get_logger().info('Vision node ready (threshold=%d, min_area=%.0f)'
                               % (self.threshold_value, self.min_contour_area))

    def _on_image(self, msg: Image):
        if not _HAS_CV2:
            self.get_logger().error('OpenCV (cv2) is not installed')
            return
        try:
            bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:  # noqa: BLE001 - bad image encoding
            self.get_logger().error('cv_bridge failed: %s' % exc)
            return
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        detection = detect_box(gray, self.threshold_value,
                               self.min_contour_area, self.invert)
        if detection is None:
            self.debug_pub.publish(self.bridge.cv2_to_imgmsg(bgr, 'bgr8'))
            return

        # Publish the box pose in the camera frame.
        pose = PoseStamped()
        pose.header = msg.header
        pose.header.frame_id = self.camera_frame
        # NOTE: pixel centre -> metric pose needs camera intrinsics
        # (calibration) + TF. Until then we publish the pixel centre in
        # x/y as a placeholder so the pipeline can be tested end-to-end.
        pose.pose.position.x = detection['center'][0]
        pose.pose.position.y = detection['center'][1]
        pose.pose.position.z = 0.0
        import math
        yaw = math.radians(detection['angle'])
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        self.pose_pub.publish(pose)

        debug = draw_detection(bgr, detection)
        self.debug_pub.publish(self.bridge.cv2_to_imgmsg(debug, 'bgr8'))
        self.get_logger().info(
            'Box at (%.0f, %.0f) px, angle %.1f deg, area %.0f'
            % (detection['center'][0], detection['center'][1],
               detection['angle'], detection['area']))


def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
