import os
import time

import pygame

import Constants
import Controllers
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

        # At this point, we don't have pages so can't create a page manager
        self.page_manager = None

    def setup_pages(self, page_classes, page_class_args, page_manager_location):
        assert len(page_classes) > 0
        assert len(page_classes) == len(page_class_args)

        # PageManager is responsible for all of the pages including displaying the pages and switching between pages
        pages = [cls(self._event_handler, *arg) for cls, arg in zip(page_classes, page_class_args)]
        self.page_manager = Pages.PageManager(self._event_handler, pages, page_manager_location)

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
                if self.page_manager is not None:
                    self.page_manager.draw(self.surface)
                pygame.display.flip()

                # Handle controllers and their generated events
                if self._touch_ctrl is not None: self._touch_ctrl.iteration()
                if self._button_ctrl is not None: self._button_ctrl.iteration()
                self._event_handler.iteration()

                # Sleep for the refresh interval
                time.sleep(max(0, Constants.REFRESH_INTERVAL - (time.time() - start_time)))
        except:
            print("EXCEPTION!")
        finally:
            self.stop()
