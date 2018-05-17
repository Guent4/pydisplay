import pygame

from pydisplay import Colors
from pydisplay import Constants
from pydisplay import Drawables
from pydisplay import Events
from pydisplay import PyDisplay


class Page(object):
    def __init__(self, pydisplay, event_handler, page_name, page_size=Constants.PI_TFT_SCREEN_SIZE, bg_color=Colors.BLACK):
        """
        This is the parent class for all Pages.  A Page is what gets displayed on the screen.  You will be making children
        classes of Page based on your personal needs.  These children Pages are passed into PageManager to be rendered.
        The most important task when creating your own child class is to remember to add all of your needed Drawables to
        self._drawables or else the Drawables wouldn't get drawn.
        :param pydisplay: Reference to the PyDisplay instance that this Page exists under.  This is useful when your
                    custom Page needs to access a function in PyDisplay (i.e. exit).
        :param event_handler: The event handler to handle events
        :param page_name: Name of the page (if you use a PageManager, thenn this is the name displayed on the switcher)
        :param page_size: Size of the pag.  If it is larger than the screen, then scrolling would be enabled
        :param bg_color: Background color of the page
        """
        assert isinstance(pydisplay, PyDisplay.PyDisplay)
        assert isinstance(page_size, tuple) and len(page_size) == 2
        assert Colors.is_color(bg_color)

        self.location_on_screen = (0, 0)                    # This is the location (top left) of the page on the screen
        self.screen_size = Constants.PI_TFT_SCREEN_SIZE     # This is the size of the screen

        self._pydisplay = pydisplay
        self._event_handler = event_handler
        self.page_name = str(page_name)
        self.page_size = page_size
        self.bg_color = bg_color
        self.scrollable = True

        self._drawables = []
        self._enabled = False
        self._visible = False

        self._location_on_page = (0, 0)                     # This is what is displayed on the screen w.r.t. the page

    @property
    def drawables(self):
        """
        Getter for Drawables on the page
        :return: None
        """
        return self._drawables

    @drawables.setter
    def drawables(self, drawables):
        """
        Setter for Drawables on the page
        :param drawables: A single Drawable or a list of Drawables
        :return: None
        """
        if isinstance(drawables, list):
            assert all(isinstance(d, Drawables.Drawable) for d in drawables)
            self._drawables.extend(drawables)
        else:
            assert isinstance(drawables, Drawables.Drawable)
            self._drawables.append(drawables)

    @property
    def visible(self):
        """
        Get visibility of the page (visibility is important for switching between pages)
        :return: Current page visibility
        """
        return self._visible

    @visible.setter
    def visible(self, visible):
        """
        Set page visibility (will also affect the visibility of all of the Drawables on the page)
        :param visible: New visibility
        :return:
        """
        self._visible = visible
        for drawable in self._drawables:
            drawable.visible = visible

    def enable(self):
        """
        Enable the page (register events).  Will enable scrolling and call enable on all of the Drawables
        :return: None
        """
        self._enabled = True

        if self.scrollable:
            self._event_handler.register_event(self, Events.EventTypes.TOUCH_MOVEMENT, self._scroll)
        for drawable in self._drawables:
            drawable.enable(self._event_handler)

    def disable(self):
        """
        Disable the page (unregister events).  Will disable scrolling and call disable on all of the Drawables
        :return: None
        """
        self._enabled = False

        if self.scrollable:
            self._event_handler.unregister_event(self, Events.EventTypes.TOUCH_MOVEMENT)
        for drawable in self._drawables:
            drawable.disable(self._event_handler)

    def draw(self, surface):
        """
        Draw function for this page; wipes the page by drawing background color and then draws all of the drawables
        :param surface: The surface on which everything will be drawn
        :return:
        """
        surface.fill(self.bg_color)

        # Draw the items on the page
        for drawable in self._drawables:
            drawable.move(*self.location_on_screen)
            drawable.draw(surface)
            drawable.move(-self.location_on_screen[0], -self.location_on_screen[1])

    def exit(self):
        """
        Gracefully exit (will call exit on all of the Drawables)
        :return:
        """
        for drawable in self.drawables:
            drawable.exit()

    def _scroll(self, event):
        """
        Internal scroll method; this is invoked when there is a TOUCH_MOVEMENT event.
        :param event: The TOUCH_MOVEMENT event that triggered this callback method.
        :return: None
        """
        assert isinstance(event, Events.EventTouchMovement)
        if not self._position_inside_page_on_screen(event.position_start) or event.no_movement or any(
                [drawable.position_inside(event.position_start) for drawable in self._drawables]):
            return

        dx = event.position_new[0] - event.position_old[0]
        dy = event.position_new[1] - event.position_old[1]

        min_dx = -(self.page_size[0] - (self._location_on_page[0] + self.screen_size[0]))
        max_dx = 0 - self._location_on_page[0]
        min_dy = -(self.page_size[1] - (self._location_on_page[1] + self.screen_size[1]))
        max_dy = 0 - self._location_on_page[1]
        dx = min(dx, max_dx) if dx > 0 else max(dx, min_dx)
        dy = min(dy, max_dy) if dy > 0 else max(dy, min_dy)

        for drawable in self._drawables:
            drawable.move(dx, dy)

        self._location_on_page = (self._location_on_page[0] + dx, self._location_on_page[1] + dy)

    def _position_inside_page_on_screen(self, position):
        """
        Detect if a certain position is inside the Page or not (i.e. switcher area doesn't count as part of the Page)
        :param position: A tuple or list of length 2 indicating the (x, y) coordintates
        :return: True if position inside the viewable region of the Page and False otherwise
        """
        assert (isinstance(position, tuple) or isinstance(position, list)) and len(position) == 2
        left = self.location_on_screen[0]
        right = self.location_on_screen[0] + self.screen_size[0]
        top = self.location_on_screen[1]
        bottom = self.location_on_screen[1] + self.screen_size[1]
        return left <= position[0] <= right and top <= position[1] <= bottom


class PageManager(object):
    SWITCHER_LOCATIONS = {
        "NONE": 0,
        "TOP": 1,
        "BOTTOM": 2,
    }
    SWITCHER_HEIGHT = 20

    def __init__(self, event_handler, pages, switcher_location):
        """
        This is the module that manages the pages.  This allows support for multiple pages and has the logic for
        switching between pages.  You do not need to directly create an instance of this because PyDisplay creates it
        automatically.
        :param event_handler: Event handler (needs to register events for the switcher)
        :param pages: A list of page instances (must have at least one page)
        :param switcher_location: Where to put the switcher?  Refer to SWITCHER_LOCATIONS for options
        """
        assert isinstance(event_handler, Events.EventHandler)
        assert isinstance(pages, list) and len(pages) >= 1 and all([isinstance(page, Page) for page in pages])
        assert switcher_location in PageManager.SWITCHER_LOCATIONS.values()
        self._event_handler = event_handler
        self.pages = pages
        self.switcher_location = switcher_location
        self.switcher_pages = [(i, page) for i, page in enumerate(self.pages)]

        # Make sure all pages have an event_handler
        for page in pages:
            page.event_handler = self._event_handler

        # Create the switcher
        self.switcher_drawables = []
        if self.switcher_location != PageManager.SWITCHER_LOCATIONS["NONE"]:
            at_top = self.switcher_location == PageManager.SWITCHER_LOCATIONS["TOP"]
            page_screen_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - PageManager.SWITCHER_HEIGHT)
            top = 0 if at_top else (Constants.PI_TFT_SCREEN_SIZE[1] - PageManager.SWITCHER_HEIGHT)
            width = Constants.PI_TFT_SCREEN_SIZE[0] / len(self.switcher_pages)
            for page_num, page in self.switcher_pages:
                page.screen_size = page_screen_size
                page.location_on_screen = (0, PageManager.SWITCHER_HEIGHT if at_top else 0)
                button = Drawables.Button(x=width * page_num, y=top, width=width, height=PageManager.SWITCHER_HEIGHT,
                                          text=page.page_name, font_size=15, bg_color=Colors.WHITE, fg_color=Colors.BLACK,
                                          callback=self._set_page_callback, args=[page_num])
                button.visible = True
                button.enable(self._event_handler)
                self.switcher_drawables.append(button)

        # Go to the starting page
        self.page_num = 0
        self.set_page(self.page_num)

    def draw(self, surface):
        """
        Draw the current page along with the switcher (if enabled)
        :param surface: The surface to draw onto
        :return: None
        """
        self.pages[self.page_num].draw(surface)

        for drawable in self.switcher_drawables:
            drawable.draw(surface)

        top = 0 if self.switcher_location == PageManager.SWITCHER_LOCATIONS["TOP"] else (Constants.PI_TFT_SCREEN_SIZE[1] - PageManager.SWITCHER_HEIGHT)
        pygame.draw.line(surface, Colors.WHITE, (0, top), (Constants.PI_TFT_SCREEN_SIZE[0], top), 1)

    def exit(self):
        """
        Graceful exit all pages
        :return: None
        """
        for page in self.pages:
            page.exit()

    def set_page(self, page_num):
        """
        Go to a certain page directly (next time draw is called, this new page would be the one drawn)
        :param page_num: The index of the Page inside the list of pages to go to
        :return: None
        """
        assert isinstance(page_num, int) and page_num < len(self.pages)
        self.page_num = page_num

        for i, page in enumerate(self.pages):
            if i == page_num:
                page.visible = True
                page.enable()
            else:
                page.visible = False
                page.disable()

        if self.switcher_location != PageManager.SWITCHER_LOCATIONS["NONE"]:
            for pn, drawable in enumerate(self.switcher_drawables):
                assert isinstance(drawable, Drawables.Button)
                drawable.bg_color = Colors.BLACK if pn == page_num else Colors.WHITE
                drawable.fg_color = Colors.WHITE if pn == page_num else Colors.BLACK

    def next_page(self, switcher_only=False):
        """
        Go to next page (similar to set_page)
        :param switcher_only: DEPRECATED; has no function
        :return: The page_num for the new page
        """
        if switcher_only:
            assert len(self.switcher_pages) >= 0
            switcher_page_nums = [page_num for page_num, _ in self.switcher_pages]
            while True:
                page_num = (self.page_num + 1) % len(self.pages)
                if page_num in switcher_page_nums:
                    break
        else:
            page_num = (self.page_num + 1) % len(self.pages)

        self.set_page(page_num)
        return page_num

    def prev_page(self, switcher_only=False):
        """
        Go to previous page (similar to set_page)
        :param switcher_only: DEPRECATED; has no function
        :return: The page_num for the new page
        """
        if switcher_only:
            assert len(self.switcher_pages) >= 0
            switcher_page_nums = [page_num for page_num, _ in self.switcher_pages]
            while True:
                page_num = (self.page_num - 1) % len(self.pages)
                if page_num in switcher_page_nums:
                    break
        else:
            page_num = (self.page_num - 1) % len(self.pages)

        self.set_page(page_num)
        return page_num


    def _set_page_callback(self, event, page_num):
        """
        Callback for going to the a set page (used by the switcher to toggle between pages)
        :param event: The event that triggered this callback
        :param page_num: The page number to go to
        :return: None
        """
        self.set_page(page_num)