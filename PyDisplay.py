import os
import time

import pygame

import Constants
import Controllers
import Events
import Pages


class PyDisplay(object):
    def __init__(self, on_pitft=True, enable_touchscreen=True, enable_button=True):
        """
        This is the wrapper around the library.  Import this class and create an instance to use this library.  Here are
        the steps to using this library:
        1. Create custom children Page classes
        2. Create an instance of PyDisplay
        3. Run setup_pages passing in the children Page classes (NOT INSTANCES) and the args to initiate the pages
        4. Run the run function
        :param on_pitft: Display on the piTFT screen?
        :param enable_touchscreen: Enable touchscreen?
        :param enable_button: Enable physical buttons?
        """
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

    def setup_pages(self, page_classes, page_class_args, switcher_location=Pages.PageManager.SWITCHER_LOCATIONS["BOTTOM"]):
        """
        Call this function to actually setup all of the pages to display.
        :param page_classes: A list of Page classes.  Don't actually pass in instances of the classes, but rather the
                    classes themselves; PyDisplay will automatically initiate these classes for you.
        :param page_class_args: List of list of arguments to be passed into the custom child Page __init__ functions.
        :param switcher_location: Where should the switcher be?  Use from Pages.PageManager.SWITCHER_LOCATIONS
        :return:
        """
        assert isinstance(page_classes, list) and isinstance(page_class_args, list)
        assert len(page_classes) > 0 and len(page_classes) == len(page_class_args)
        assert all([isinstance(args, list) for args in page_class_args])
        assert switcher_location in Pages.PageManager.SWITCHER_LOCATIONS.keys()

        # PageManager is responsible for all of the pages including displaying the pages and switching between pages
        pages = [cls(self, self._event_handler, *arg) for cls, arg in zip(page_classes, page_class_args)]
        self.page_manager = Pages.PageManager(self._event_handler, pages, switcher_location)

    def exit(self):
        """
        Gracefully exit (will stop the controllers that detect events and also call exit for page_manager)
        :return: None
        """
        if not self._alive:
            return

        self._alive = False

        # Stop the event handler and controllers
        self._event_handler.stop()
        if self._touch_ctrl is not None: self._touch_ctrl.stop()
        if self._button_ctrl is not None: self._button_ctrl.stop()

        if self.page_manager is not None:
            self.page_manager.exit()

    def run(self):
        """
        Start running PyDisplay!  This function keeps the display alive so terminating this function ends the display.
        Call PyDisplay.exit to gracefully quit out of displaying things.
        :return:
        """
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
        except Exception as e:
            print("EXCEPTION! {}".format(e))
        finally:
            self.exit()
