"""Minimal unit checks for the ar4_palletizing application nodes.

Run with:  python3 -m pytest test/test_nodes.py
(or:  colcon test --packages-select ar4_palletizing)

* State-machine transitions are pure Python — always tested.
* Vision contour detection needs OpenCV (cv2) + numpy; if they are not
  installed the test is skipped gracefully instead of failing.
* The ROS nodes themselves are NOT spun up here (that needs a ROS 2
  install + MoveIt); only the logic they depend on is tested.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ar4_palletizing.state_machine import (  # noqa: E402
    Event,
    PalletizingStateMachine,
    State,
)


def test_state_machine_happy_path():
    sm = PalletizingStateMachine(total_boxes=2)
    assert sm.state == State.IDLE
    sm.advance(Event.START)
    assert sm.state == State.HOME
    sm.advance(Event.HOMED)
    assert sm.state == State.WAIT_FOR_BOX
    sm.advance(Event.BOX_DETECTED)
    assert sm.state == State.MOVE_TO_PICK_APPROACH
    sm.advance(Event.PLAN_OK)
    assert sm.state == State.PICK
    sm.advance(Event.PICK_DONE)
    assert sm.state == State.LIFT
    sm.advance(Event.LIFT_DONE)
    assert sm.state == State.MOVE_ON_TRACK
    sm.advance(Event.TRACK_DONE)
    assert sm.state == State.PLACE
    sm.advance(Event.PLACE_DONE)
    assert sm.state == State.NEXT_BOX
    assert sm.boxes_placed == 1
    sm.advance(Event.MORE_BOXES)
    assert sm.state == State.WAIT_FOR_BOX


def test_state_machine_done_after_all_boxes():
    sm = PalletizingStateMachine(total_boxes=1)
    for event in (Event.START, Event.HOMED, Event.BOX_DETECTED, Event.PLAN_OK,
                  Event.PICK_DONE, Event.LIFT_DONE, Event.TRACK_DONE,
                  Event.PLACE_DONE):
        sm.advance(event)
    assert sm.state == State.NEXT_BOX
    sm.advance(Event.ALL_PLACED)
    assert sm.state == State.DONE
    assert sm.is_done()


def test_state_machine_plan_failure_goes_to_error_and_resets():
    sm = PalletizingStateMachine(total_boxes=1)
    sm.advance(Event.START)
    sm.advance(Event.HOMED)
    sm.advance(Event.BOX_DETECTED)
    sm.advance(Event.PLAN_FAILED)
    assert sm.state == State.ERROR
    sm.advance(Event.RESET)
    assert sm.state == State.IDLE
    assert sm.boxes_placed == 0


def test_state_machine_rejects_bad_total():
    with pytest.raises(ValueError):
        PalletizingStateMachine(total_boxes=0)


cv2 = pytest.importorskip('cv2')
np = pytest.importorskip('numpy')

from ar4_palletizing.vision_utils import detect_box  # noqa: E402


def test_vision_detects_white_rectangle_on_black():
    img = np.zeros((200, 300), dtype=np.uint8)
    # White rectangle (the "box") on a black background (the "conveyor").
    cv2.rectangle(img, (100, 70), (200, 130), 255, -1)
    result = detect_box(img, threshold_value=127, min_contour_area=100.0,
                        invert=False)
    assert result is not None
    cx, cy = result['center']
    assert abs(cx - 150) < 3
    assert abs(cy - 100) < 3
    assert result['area'] > 5000


def test_vision_returns_none_for_empty_image():
    img = np.zeros((200, 300), dtype=np.uint8)
    assert detect_box(img, threshold_value=127, min_contour_area=100.0,
                      invert=False) is None
