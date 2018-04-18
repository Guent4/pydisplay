import os
import time

import pygame

import Colors
import Constants
import Events
import Controllers

import Pages


class PyDisplay(object):
    def __init__(self, on_pitft=True, enable_touchscreen=True, enable_button=True):
        self._starting_time = time.time()

        self._alive = True

        # Display on piTFT?
        if on_pitft:
            os.putenv('SDL_VIDEODRIVER', 'fbcon')  # Display on piTFT
            os.putenv('SDL_FBDEV', '/dev/fb1')
            os.putenv('SDL_MOUSEDRV', 'TSLIB')  # Track mouse clicks on piTFT
            os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

        # Start up pygame
        pygame.init()
        pygame.mouse.set_visible(not on_pitft)
        self.surface_size = Constants.PI_TFT_SCREEN_SIZE
        self.surface = pygame.display.set_mode(self.surface_size)

        # Start up EventHandler and the controllers
        self._event_handler = Events.EventHandler()
        self._touch_ctrl = Controllers.TouchScreenController(self._event_handler) if enable_touchscreen else None
        self._button_ctrl = Controllers.ButtonController(self._event_handler) if enable_button else None

        # TODO remove this!!! JUST FOR TESTING
        self.a = Pages.TempPage(self._event_handler)
        self.a.enable()
        self.a.visible = True

        print("starting")

    def stop(self):
        self._alive = False

        # Stop the event handler and controllers
        self._event_handler.stop()
        if self._touch_ctrl is not None: self._touch_ctrl.stop()
        if self._button_ctrl is not None: self._button_ctrl.stop()

    def run(self):
        try:
            while self._alive:
                self.a.draw(self.surface)
                pygame.display.flip()

                # Handle controllers and their generated events
                self._touch_ctrl.iteration()
                self._button_ctrl.iteration()
                self._event_handler.iteration()

                # Sleep for the refresh interval
                time.sleep(Constants.REFRESH_INTERVAL)

        finally:
            self.stop()


if __name__ == "__main__":
    PyDisplay(on_pitft=True, enable_touchscreen=True, enable_button=True).run()
