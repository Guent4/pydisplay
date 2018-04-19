import time

import pygame
import pygame.locals

import Events


class Controller(object):
    def __init__(self, event_handler):
        self._event_handler = event_handler
        self._alive = True

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
                print("MOUSEBUTTONDOWN!")
                pos = pygame.mouse.get_pos()

                event = Events.EventTouchDown(pos)
                self._event_handler.event_occurred(event)

                self.down = True
                self.down_positions = [pos]
                self.down_time = time.time()
            elif event.type is pygame.locals.MOUSEMOTION:
                if not self.down:
                    continue
                print("MOUSEMOTION!")
                pos = pygame.mouse.get_pos()

                event = Events.EventTouchMotion(pos)
                self._event_handler.event_occurred(event)
                event = Events.EventTouchMovement(self.down_positions[-1], pos)
                self._event_handler.event_occurred(event)

                if self.down_positions[-1] != pos:
                    self.down_positions.append(pos)
            elif event.type is pygame.locals.MOUSEBUTTONUP:
                if not self.down:
                    continue
                print("MOUSEBUTTONUP!")
                pos = pygame.mouse.get_pos()

                if self.down_positions[-1] != pos:
                    self.down_positions.append(pos)
                duration = time.time() - self.down_time

                event = Events.EventTouchUp(pos)
                self._event_handler.event_occurred(event)
                event = Events.EventTouchDrag(self.down_positions, duration)
                self._event_handler.event_occurred(event)

                self.down = False
                self.down_positions = []
                self.down_time = None


class ButtonController(Controller):
    def __init__(self, event_handler):
        super().__init__(event_handler)

    def iteration(self):
        if not self._alive:
            return