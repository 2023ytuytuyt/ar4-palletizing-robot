"""Palletizing state machine (pure Python, no ROS dependency).

Kept separate from the ROS node so the transition logic can be unit-tested
without a ROS install. The ROS node (palletizing_demo.py) wraps this class
and calls :meth:`PalletizingStateMachine.advance` on each event
(plan finished, gripper done, sensor fired, ...).

States
------
IDLE -> HOME -> WAIT_FOR_BOX -> MOVE_TO_PICK_APPROACH -> PICK -> LIFT
  -> MOVE_ON_TRACK -> PLACE -> NEXT_BOX -> (repeat or DONE)
Any failure event moves to ERROR; ``reset()`` brings it back to IDLE.
"""

from enum import Enum


class State(Enum):
    IDLE = 'IDLE'
    HOME = 'HOME'
    WAIT_FOR_BOX = 'WAIT_FOR_BOX'
    MOVE_TO_PICK_APPROACH = 'MOVE_TO_PICK_APPROACH'
    PICK = 'PICK'
    LIFT = 'LIFT'
    MOVE_ON_TRACK = 'MOVE_ON_TRACK'
    PLACE = 'PLACE'
    NEXT_BOX = 'NEXT_BOX'
    DONE = 'DONE'
    ERROR = 'ERROR'


class Event(Enum):
    START = 'start'
    HOMED = 'homed'
    BOX_DETECTED = 'box_detected'
    PLAN_OK = 'plan_ok'
    PLAN_FAILED = 'plan_failed'
    PICK_DONE = 'pick_done'
    LIFT_DONE = 'lift_done'
    TRACK_DONE = 'track_done'
    PLACE_DONE = 'place_done'
    ALL_PLACED = 'all_placed'
    MORE_BOXES = 'more_boxes'
    ERROR = 'error'
    RESET = 'reset'


# (current_state, event) -> next_state
_TRANSITIONS = {
    (State.IDLE, Event.START): State.HOME,
    (State.HOME, Event.HOMED): State.WAIT_FOR_BOX,
    (State.WAIT_FOR_BOX, Event.BOX_DETECTED): State.MOVE_TO_PICK_APPROACH,
    (State.MOVE_TO_PICK_APPROACH, Event.PLAN_OK): State.PICK,
    (State.PICK, Event.PICK_DONE): State.LIFT,
    (State.LIFT, Event.LIFT_DONE): State.MOVE_ON_TRACK,
    (State.MOVE_ON_TRACK, Event.TRACK_DONE): State.PLACE,
    (State.PLACE, Event.PLACE_DONE): State.NEXT_BOX,
    (State.NEXT_BOX, Event.MORE_BOXES): State.WAIT_FOR_BOX,
    (State.NEXT_BOX, Event.ALL_PLACED): State.DONE,
    (State.DONE, Event.RESET): State.IDLE,
}


class PalletizingStateMachine:
    """Small deterministic state machine for one palletizing cycle per box."""

    def __init__(self, total_boxes: int = 1):
        if total_boxes < 1:
            raise ValueError('total_boxes must be >= 1')
        self.total_boxes = total_boxes
        self.state = State.IDLE
        self.boxes_placed = 0

    def advance(self, event: Event) -> State:
        """Apply an event, return the new state.

        Any ``ERROR`` / ``PLAN_FAILED`` event (except a reset) moves to ERROR.
        Unknown (state, event) pairs leave the state unchanged.
        """
        if event == Event.RESET:
            self.state = State.IDLE
            self.boxes_placed = 0
            return self.state
        if event in (Event.ERROR, Event.PLAN_FAILED):
            self.state = State.ERROR
            return self.state
        if event == Event.PLACE_DONE:
            self.boxes_placed += 1
        nxt = _TRANSITIONS.get((self.state, event))
        if nxt is not None:
            self.state = nxt
        return self.state

    def is_done(self) -> bool:
        return self.state == State.DONE

    def reset(self) -> State:
        return self.advance(Event.RESET)
