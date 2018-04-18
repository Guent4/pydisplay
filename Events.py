import inspect


class EventTypes(object):
    TOUCH_DOWN = 0
    TOUCH_MOTION = 1
    TOUCH_UP = 2

    TOUCH_HOLD = 3
    # Marked by down, motion, and up being in around the same place
    # Defined by position and hold duration (in seconds)

    TOUCH_MOVEMENT = 4
    # Marked by motion changing
    # Defined by previous position and new position

    TOUCH_DRAG = 5
    # Marked by down location and up location with no regard to motion in between
    # Defined by down location and up location

    BUTTON_DOWN = 6
    BUTTON_UP = 7
    BUTTON_HOLD = 8

    ALL = [TOUCH_DOWN, TOUCH_MOTION, TOUCH_UP, TOUCH_HOLD, TOUCH_MOVEMENT, TOUCH_DRAG, BUTTON_DOWN, BUTTON_UP, BUTTON_HOLD]

    @staticmethod
    def is_valid_event_type(event_type):
        return event_type in EventTypes.ALL


class Event(object):
    def __init__(self, event_type):
        self.event_type = event_type


class EventTouchDown(Event):
    def __init__(self, position):
        super().__init__(EventTypes.TOUCH_DOWN)
        self.position = position


class EventTouchMotion(Event):
    def __init__(self, position):
        super().__init__(EventTypes.TOUCH_MOTION)
        self.position = position


class EventTouchUp(Event):
    def __init__(self, position):
        super().__init__(EventTypes.TOUCH_UP)
        self.position = position


class EventTouchHold(Event):
    def __init__(self, position, duration):
        super().__init__(EventTypes.TOUCH_HOLD)
        self.position = position
        self.duration = duration


class EventTouchMovement(Event):
    def __init__(self, position_old, position_new):
        super().__init__(EventTypes.TOUCH_MOVEMENT)
        self.position_old = position_old
        self.position_new = position_new


class EventTouchDrag(Event):
    def __init__(self, position_start, position_end):
        super().__init__(EventTypes.TOUCH_DRAG)
        self.position_start = position_start
        self.position_end = position_end


class EventButtonDown(Event):
    def __init__(self, pin):
        super().__init__(EventTypes.BUTTON_DOWN)
        self.pin = pin


class EventButtonUp(Event):
    def __init__(self, pin):
        super().__init__(EventTypes.BUTTON_UP)
        self.pin = pin


class EventButtonHold(Event):
    def __init__(self, pin, duration):
        super().__init__(EventTypes.BUTTON_HOLD)
        self.pin = pin
        self.duration = duration


class EventHandler(object):
    def __init__(self):
        self._alive = True
        self._event_listeners = {event_type: dict() for event_type in EventTypes.ALL}
        self._unregister_list = []

    def stop(self):
        self._alive = False

    def iteration(self):
        if not self._alive:
            return

    def register_event(self, object, event_type, callback):
        assert EventTypes.is_valid_event_type(event_type)
        assert len(inspect.getfullargspec(callback).args) == 2

        self._event_listeners[event_type][object] = callback

    def unregister_event(self, object, event_type):
        assert EventTypes.is_valid_event_type(event_type)

        self._unregister_list.append((object, event_type))

    def event_occurred(self, event):
        assert isinstance(event, Event)

        for object, event_type in self._unregister_list:
            if object in self._event_listeners[event_type]:
                del self._event_listeners[event_type][object]

        for _, callback in self._event_listeners[event.event_type].items():
            callback(event)
