import inspect

from pydisplay import Constants


class EventTypes(object):
    """
    These are all of the possible event types.  For more details on the events, refer to the specific event classes
    """

    # These correspond directly to MOUSEBUTTONDOWN, MOUSEBUTTONMOTIION, and MOUSEBUTTONUP
    TOUCH_DOWN = 0
    TOUCH_MOTION = 1
    TOUCH_UP = 2

    # Marked by motion changing; defined by previous position and new position (refer to EventTouchMovement)
    TOUCH_MOVEMENT = 3

    # Created upon up; defined by all positions between down and up (inclusive) and duration (refer to EventTouchDrag)
    TOUCH_DRAG = 4

    # These directly correspond to the immediate events of the button being pressed or released
    BUTTON_DOWN = 5
    BUTTON_UP = 6

    # This is triggered when the button is released (will contain information on how long the button was held for)
    BUTTON_HOLD = 7

    ALL = (TOUCH_DOWN, TOUCH_MOTION, TOUCH_UP, TOUCH_MOVEMENT, TOUCH_DRAG, BUTTON_DOWN, BUTTON_UP, BUTTON_HOLD)

    @staticmethod
    def is_valid_event_type(event_type):
        """
        Check if provided event type is valid
        :param event_type: The thing to check if it's a valid event type
        :return: True if it's a valid event type and False otherwise
        """
        return event_type in EventTypes.ALL


class Event(object):
    def __init__(self, event_type):
        """
        Generic event class.  Not directly used; just used as a parent class for the specific events.
        :param event_type: The actual type of event (must be one of the ones in EventTypes)
        """
        assert EventTypes.is_valid_event_type(event_type)
        self.event_type = event_type


class EventTouchDown(Event):
    def __init__(self, position):
        """
        This is the event corresponding directly to the MOUSEBUTTONDOWN event.  Nothing special to it.
        :param position: The position (x, y coordinates) at which the event was triggered.
        """
        super().__init__(EventTypes.TOUCH_DOWN)
        assert isinstance(position, tuple) and len(position) == 2 and all([isinstance(v, int) for v in position])
        self.position = position


class EventTouchMotion(Event):
    def __init__(self, position):
        """
        This is the event corresponding directly to the MOUSEBUTTONMOTION event.  Nothing special to it.
        :param position: The position (x, y coordinates) at which the event was triggered.
        """
        super().__init__(EventTypes.TOUCH_MOTION)
        assert isinstance(position, tuple) and len(position) == 2 and all([isinstance(v, int) for v in position])
        self.position = position


class EventTouchUp(Event):
    """
    This is the event corresponding directly to the MOUSEBUTTONUP event.  Nothing special to it.
    :param position: The position (x, y coordinates) at which the event was triggered.
    """
    def __init__(self, position):
        super().__init__(EventTypes.TOUCH_UP)
        assert isinstance(position, tuple) and len(position) == 2 and all([isinstance(v, int) for v in position])
        self.position = position


class EventTouchMovement(Event):
    """
    This is the event corresponding to a movement of the mouse/finger.  This is therefore triggered in between a
    MOUSEBUTTONUP and a MOUSEBUTTONDOWN event.  This contains information on the position of the initial MOUSEBUTTONDOWN
    event position, the previous position, and the new position.  The no_movement variable indicates whether or not the
    movement is significant (based on the TOUCH_HOLD_TOLERANCE variables in Constants).
    :param position_old: This is the previous position (x, y coordinate)
    :param position_new: This is the new position (x, y coordinate)
    :param position_start: This is the position where the initial MOUSEBUTTONDOWN event was triggered (x, y coordinate)
    """
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
        """
        This is the event corresponding to the full duration in which the mouse/finger was pressed down.  This is
        triggered at the same time as EventTouchUp.  This has information on all of the positions during which the
        mouse/finger was pressed down.  The no_movement variable is True if during the whole duration, the positions
        did not move much (based on the TOUCH_HOLD_TOLERANCE variables in Constants).
        """
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
        """
        A button was pressed down (in the last iteration, it was not pressed down).
        :param pin: The GPIO pin to which this button is registered to.
        """
        super().__init__(EventTypes.BUTTON_DOWN)
        assert isinstance(pin, int)
        self.pin = pin


class EventButtonUp(Event):
    def __init__(self, pin):
        """
        A button was released (in the last iteration, it was pressed down)
        :param pin: The GPIO pin to which this button is registered to.
        """
        super().__init__(EventTypes.BUTTON_UP)
        assert isinstance(pin, int)
        self.pin = pin


class EventButtonHold(Event):
    def __init__(self, pin, duration):
        """
        A button was held for a certain amount of time.  This event is triggered at the same time as EventButtonUp.
        Also includes information on how long the button was held down for.
        :param pin: The GPIO pin to which this button is registered to.
        :param duration: Duration the button was held down for (in seconds as a float)
        """
        super().__init__(EventTypes.BUTTON_HOLD)
        assert isinstance(pin, int)
        assert isinstance(duration, float)
        self.pin = pin
        self.duration = duration


class EventHandler(object):
    def __init__(self):
        """
        This is the event handler that handles all of the incoming events and handles triggering the correct callbacks
        based on the events.  Objects can register itself to listen to a specific event with this event_handler in order
        for some action to occur when an event occurs.  The object can also unregister itself accordingly.
        """
        self._alive = True
        self._event_listeners = {event_type: dict() for event_type in EventTypes.ALL}
        self._unregister_list = []
        self._register_list = []

    def start(self):
        """
        Stop this EventHandler from processing more events.
        :return: None
        """
        self._alive = True

    def stop(self):
        """
        Stop this EventHandler from processing more events.
        :return: None
        """
        self._alive = False

    def iteration(self):
        """
        DEPRECATED.  Something to do every draw iteration if this is alive.
        :return: None
        """
        if not self._alive:
            return

    def register_event(self, obj, event_type, callback):
        """
        Register an object and a callback to run when a certain event is triggered.
        :param obj: The object (in most cases, pass in self)
        :param event_type: The type of event interested in
        :param callback: The callback to run when triggered (must take 2 arguments, the obj itself, and the event that
                    triggered the callback)
        :return: None
        """
        assert EventTypes.is_valid_event_type(event_type)
        assert callable(callback) and len(inspect.getfullargspec(callback).args) == 2

        self._register_list.append((obj, event_type, callback))

    def unregister_event(self, obj, event_type):
        """
        Unregister an event.
        :param obj: The object (in most cases, pass in self) to be unregistered
        :param event_type: The type of event that the obj was registered for
        :return: None
        """
        assert EventTypes.is_valid_event_type(event_type)

        self._unregister_list.append((obj, event_type))

    def event_occurred(self, event):
        """
        Call this function when an event has occurred.  This will handle dispatching the right callback.
        :param event: The event that was triggered
        :return: None
        """
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
