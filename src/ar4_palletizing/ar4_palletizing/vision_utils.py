"""Classical OpenCV box detection (pure function, no ROS dependency).

Pipeline: grayscale -> threshold -> contours -> largest contour ->
``cv2.minAreaRect`` -> box centre (pixels) + angle + size.

Classical computer vision ONLY: no deep learning, no YOLO. This is the
agreed approach for one small, fixed-shape box on a contrasting conveyor
under fixed lighting. A pretrained YOLO would only be considered later if
box types or clutter require it.

The returned centre is in IMAGE pixels. Converting pixels to a pose in the
robot base frame needs the camera calibration + TF (camera -> base_link),
which is done by the caller (vision_node.py publishes the pose in the
camera frame; the demo node must transform it).
"""

from typing import Optional

import cv2
import numpy as np


def detect_box(gray_image, threshold_value: int = 127,
               min_contour_area: float = 100.0, invert: bool = True):
    """Detect the largest box-like contour in a grayscale image.

    Parameters
    ----------
    gray_image : np.ndarray
        Single-channel (grayscale) image.
    threshold_value : int
        Threshold for ``cv2.threshold`` (0-255).
    min_contour_area : float
        Contours smaller than this (pixels^2) are ignored as noise.
    invert : bool
        True if the box is DARK on a LIGHT conveyor (THRESH_BINARY_INV);
        False if the box is LIGHT on a DARK conveyor.

    Returns
    -------
    dict | None
        ``{'center': (x, y), 'size': (w, h), 'angle': deg,
        'area': float, 'corners': np.ndarray (4, 2)}`` or None if no
        contour passes the area filter.
    """
    if gray_image is None or gray_image.size == 0:
        return None
    flag = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
    _, binary = cv2.threshold(gray_image, threshold_value, 255, flag)
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    if area < min_contour_area:
        return None
    rect = cv2.minAreaRect(contour)
    (cx, cy), (w, h), angle = rect
    corners = cv2.boxPoints(rect)
    return {
        'center': (float(cx), float(cy)),
        'size': (float(w), float(h)),
        'angle': float(angle),
        'area': area,
        'corners': corners,
    }


def draw_detection(bgr_image, detection: Optional[dict]):
    """Draw the detected box rectangle + centre on a BGR image (debug view)."""
    if detection is None:
        return bgr_image
    out = bgr_image.copy()
    pts = np.int32(detection['corners'])
    cv2.drawContours(out, [pts], 0, (0, 255, 0), 2)
    cx, cy = detection['center']
    cv2.circle(out, (int(cx), int(cy)), 4, (0, 0, 255), -1)
    cv2.putText(out, 'angle %.1f deg' % detection['angle'],
                (int(cx) + 10, int(cy)), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 255, 0), 1)
    return out
