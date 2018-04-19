import threading
import time

import pygame
import pygame.locals

import Constants
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

    def iteration(self):
        if not self._alive:
            return

        for event in pygame.event.get():
            if event.type is pygame.locals.MOUSEBUTTONDOWN:
                print("MOUSEBUTTONDOWN! {}".format(pygame.mouse.get_pos()))

                event = Events.EventTouchDown(pygame.mouse.get_pos())
                self._event_handler.event_occurred(event)
            elif event.type is pygame.locals.MOUSEBUTTONUP:
                print("MOUSEBUTTONUP! {}".format(pygame.mouse.get_pos()))
                event = Events.EventTouchUp(pygame.mouse.get_pos())
                self._event_handler.event_occurred(event)
                # TODO following line is just for testing
                event = Events.EventTouchHold(pygame.mouse.get_pos(), 0.1)
                self._event_handler.event_occurred(event)
            elif event.type is pygame.locals.MOUSEMOTION:
                print("MOUSEMOTION! {}".format(pygame.mouse.get_pos()))
                event = Events.EventTouchMotion(pygame.mouse.get_pos())
                self._event_handler.event_occurred(event)
                # pos = pygame.mouse.get_pos()
                # print(pos)


class ButtonController(Controller):
    def __init__(self, event_handler):
        super().__init__(event_handler)

    def iteration(self):
        if not self._alive:
            return