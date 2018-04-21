import inspect

import Constants
import Controllers


class EventTypes(object):
    TOUCH_DOWN = 0
    TOUCH_MOTION = 1
    TOUCH_UP = 2

    TOUCH_MOVEMENT = 3
    # Marked by motion changing
    # Defined by previous position and new position

    TOUCH_DRAG = 4
    # Created upon up
    # Defined by all positions between down and up (inclusive) and duration

    BUTTON_DOWN = 5
    BUTTON_UP = 6
    BUTTON_HOLD = 7

    ALL = [TOUCH_DOWN, TOUCH_MOTION, TOUCH_UP, TOUCH_MOVEMENT, TOUCH_DRAG, BUTTON_DOWN, BUTTON_UP, BUTTON_HOLD]

    @staticmethod
    def is_valid_event_type(event_type):
        return event_type in EventTypes.ALL


class Event(object):
    def __init__(self, event_type):
        self.event_type = event_type


class EventTouchDown(Event):
    def __init__(self, position):
        super().__init__(EventTypes.TOUCH_DOWN)
        assert isinstance(position, tuple) and len(position) == 2 and all([isinstance(v, int) for v in position])
        self.position = position


class EventTouchMotion(Event):
    def __init__(self, position):
        super().__init__(EventTypes.TOUCH_MOTION)
        assert isinstance(position, tuple) and len(position) == 2 and all([isinstance(v, int) for v in position])
        self.position = position


class EventTouchUp(Event):
    def __init__(self, position):
        super().__init__(EventTypes.TOUCH_UP)
        assert isinstance(position, tuple) and len(position) == 2 and all([isinstance(v, int) for v in position])
        self.position = position


class EventTouchMovement(Event):
    def __init__(self, position_old, position_new, position_start):
        super().__init__(EventTypes.TOUCH_MOVEMENT)
        assert isinstance(position_old, tuple) and len(position_old) == 2 and all([isinstance(v, int) for v in position_old])
        assert isinstance(position_new, tuple) and len(position_new) == 2 and all([isinstance(v, int) for v in position_new])
        assert isinstance(position_start, tuple) and len(position_start) == 2 and all([isinstance(v, int) for v in position_start])
        self.position_old = position_old
        self.position_new = position_new
        self.position_start = position_start
        dx = abs(position_new[0] - position_old[0])
        dy = abs(position_new[1] - position_old[1])
        self.no_movement = dx <= Constants.TOUCH_HOLD_TOLERANCE and dy <= Constants.TOUCH_HOLD_TOLERANCE


class EventTouchDrag(Event):
    def __init__(self, positions, duration):
        super().__init__(EventTypes.TOUCH_DRAG)
        assert isinstance(duration, float)
        self.positions = positions
        self.position_start = positions[0]
        self.position_end = positions[-1]
        xs = [x for x, _ in self.positions]
        ys = [y for _, y in self.positions]
        self.no_movement = (max(xs) - min(xs)) <= Constants.TOUCH_HOLD_TOLERANCE and (max(ys) - min(ys)) <= Constants.TOUCH_HOLD_TOLERANCE


class EventButtonDown(Event):
    def __init__(self, pin):
        super().__init__(EventTypes.BUTTON_DOWN)
        assert isinstance(pin, int)
        self.pin = pin


class EventButtonUp(Event):
    def __init__(self, pin):
        super().__init__(EventTypes.BUTTON_UP)
        assert isinstance(pin, int)
        self.pin = pin


class EventButtonHold(Event):
    def __init__(self, pin, duration):
        super().__init__(EventTypes.BUTTON_HOLD)
        assert isinstance(pin, int)
        assert isinstance(duration, float)
        self.pin = pin
        self.duration = duration


class EventHandler(object):
    def __init__(self):
        self._alive = True
        self._event_listeners = {event_type: dict() for event_type in EventTypes.ALL}
        self._unregister_list = []
        self._register_list = []

    def stop(self):
        self._alive = False

    def iteration(self):
        if not self._alive:
            return

    def register_event(self, obj, event_type, callback):
        assert EventTypes.is_valid_event_type(event_type)
        assert len(inspect.getfullargspec(callback).args) == 2

        self._register_list.append((obj, event_type, callback))

    def unregister_event(self, obj, event_type):
        assert EventTypes.is_valid_event_type(event_type)

        self._unregister_list.append((obj, event_type))

    def event_occurred(self, event):
        assert isinstance(event, Event)

        for obj, event_type, callback in self._register_list:
            self._event_listeners[event_type][obj] = callback
        self._register_list = []

        for obj, event_type in self._unregister_list:
            if obj in self._event_listeners[event_type]:
                del self._event_listeners[event_type][obj]
        self._unregister_list = []

        for _, callback in self._event_listeners[event.event_type].items():
            callback(event)
