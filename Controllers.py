import time

import pygame
import pygame.locals

import Constants
import Events

try:
    import RPi.GPIO as GPIO
except:
    pass


class Controller(object):
    def __init__(self, event_handler):
        assert isinstance(event_handler, Events.EventHandler)

        self._event_handler = event_handler
        self._alive = True
        self._enabled = False

    def stop(self):
        self._alive = False

    def iteration(self):
        if not self._alive:
            return

        raise NotImplementedError("Controller must have iteration function responding to screen refreshs")


class TouchScreenController(Controller):
    def __init__(self, event_handler):
        super().__init__(event_handler)

        self.down = False
        self.down_positions = []
        self.down_time = None

    def iteration(self):
        if not self._alive:
            return

        for event in pygame.event.get():
            if event.type is pygame.locals.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                self._event_handler.event_occurred(Events.EventTouchDown(pos))

                self.down = True
                self.down_positions = [pos]
                self.down_time = time.time()
            elif event.type is pygame.locals.MOUSEMOTION:
                if not self.down:
                    continue
                pos = pygame.mouse.get_pos()

                self._event_handler.event_occurred(Events.EventTouchMotion(pos))
                self._event_handler.event_occurred(Events.EventTouchMovement(self.down_positions[-1], pos))

                if self.down_positions[-1] != pos:
                    self.down_positions.append(pos)
            elif event.type is pygame.locals.MOUSEBUTTONUP:
                if not self.down:
                    continue
                pos = pygame.mouse.get_pos()

                if self.down_positions[-1] != pos:
                    self.down_positions.append(pos)
                duration = time.time() - self.down_time

                self._event_handler.event_occurred(Events.EventTouchUp(pos))
                self._event_handler.event_occurred(Events.EventTouchDrag(self.down_positions, duration))

                self.down = False
                self.down_positions = []
                self.down_time = None


class PhysicalButton(object):
    """ This is used to register a pin as a button for ButtonController and is used by ButtonController for metadata """
    def __init__(self, gpio_pin, pull_up):
        assert isinstance(gpio_pin, int)
        assert isinstance(pull_up, bool)

        self.gpio_pin = gpio_pin
        self.pull_up = pull_up
        self.pressed = False
        self.press_start_time = None


class ButtonController(Controller):
    def __init__(self, event_handler):
        super().__init__(event_handler)

        GPIO.setmode(GPIO.BCM)

        self._physical_buttons = []
        self._remove_physical_button = []

    def add_physical_button(self, physical_button):
        assert isinstance(physical_button, PhysicalButton)
        if physical_button.gpio_pin in Constants.PI_TFT_BUTTON_PINS:
            GPIO.setup(physical_button.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            GPIO.setup(physical_button.gpio_pin, GPIO.IN)

        self._physical_buttons.append(physical_button)

    def remove_physical_button(self, physical_button):
        assert isinstance(physical_button, PhysicalButton)

        self._remove_physical_button.append(physical_button.gpio_pin)

    def iteration(self):
        if not self._alive:
            return

        for pin in self._remove_physical_button:
            del self._physical_buttons[pin]

        for physical_button in self._physical_buttons:
            assert isinstance(physical_button, PhysicalButton)

            value_when_pressed = 0 if physical_button.pull_up else 1
            pressed = GPIO.input(physical_button.gpio_pin) == value_when_pressed
            if pressed and not physical_button.pressed:
                # Just started pressing this button
                self._event_handler.event_occurred(Events.EventButtonDown(physical_button.gpio_pin))

                physical_button.pressed = True
                physical_button.press_start_time = time.time()
            elif not pressed and physical_button.pressed:
                # Releasing press of this button
                self._event_handler.event_occurred(Events.EventButtonUp(physical_button.gpio_pin))
                duration = time.time() - physical_button.press_start_time
                self._event_handler.event_occurred(Events.EventButtonHold(physical_button.gpio_pin, duration))

                physical_button.pressed = False
                physical_button.press_start_time = None
