import argparse
import os
import time

import pygame

import Constants
import Controllers
import Demo
import Events
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
        self._button_ctrl = None
        if enable_button:
            self._button_ctrl = Controllers.ButtonController(self._event_handler)
            for pin in Constants.PI_TFT_BUTTON_PINS:
                self._button_ctrl.add_physical_button(Controllers.PhysicalButton(pin, True))

        # TODO remove this!!! JUST FOR TESTING
        pages = [Demo.TempPage1(self._event_handler), Demo.TempPage2(self._event_handler)]
        self.page_manager = Pages.PageManager(self._event_handler, pages, Pages.PageManager.SWITCHER_LOCATIONS["BOTTOM"])

    def stop(self):
        self._alive = False

        # Stop the event handler and controllers
        self._event_handler.stop()
        if self._touch_ctrl is not None: self._touch_ctrl.stop()
        if self._button_ctrl is not None: self._button_ctrl.stop()

    def run(self):
        try:
            while self._alive:
                start_time = time.time()
                self.page_manager.draw(self.surface)
                pygame.display.flip()

                # Handle controllers and their generated events
                if self._touch_ctrl is not None: self._touch_ctrl.iteration()
                if self._button_ctrl is not None: self._button_ctrl.iteration()
                self._event_handler.iteration()

                # Sleep for the refresh interval
                time.sleep(max(0, Constants.REFRESH_INTERVAL - (time.time() - start_time)))

        finally:
            self.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--not_on_pitft", action='store_true', help="Don't run on piTFT screen?")
    parser.add_argument("--disable_touchscreen", action='store_true', help="Don't usetouchscreen?")
    parser.add_argument("--disable_button", action='store_true', help="Don't use buttons connected to GPIO pins?")

    args = parser.parse_args()

    PyDisplay(on_pitft=not args.not_on_pitft, enable_touchscreen=not args.disable_touchscreen, enable_button=not args.disable_button).run()
