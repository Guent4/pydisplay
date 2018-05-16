import pygame

import Colors
import Events


class Drawable(object):
    def __init__(self, x, y, width, height):
        """
        This class is just the most basic level of anything that should be drawn on the screen.  Lines, buttons, etc. are
        all children classes of Drawables.  If you want to add your own custom objects, have them extend Drawables.
        Every drawable has a x, y, width, and height.  The x, y are whatever you define it to be; for a rectangle, that's
        probably top left corner, while for a circle, it's probably the center.  The same applies to the width and height.
        Note that IT IS VERY IMPORTANT for all coordinates and sizes of your children classes be based off of this x, y,
        width, and height or else when pages are scrolled, the drawables would not move.
        :param x: Some reference (in x and width direction) of where the drawable is situated
        :param y: Some reference (in y and height direction) of where the drawable is situated
        :param width: Indicator of how wide the object is (uses of this varies, but can be useful for position_inside())
        :param height: Indicator of how tall the object is (uses of this varies, but can be useful for position_inside())
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._enabled = False
        self._visible = False

    @property
    def visible(self):
        """
        Getter for the visible attribute (if not visible, will not be drawn)
        :return: Current visibility (boolean)
        """
        return self._visible

    @visible.setter
    def visible(self, visible):
        """
        Set the visibility of the drawable (if not visible, will not be drawn)
        :param visible: New visibility (boolean)
        """
        assert isinstance(visible, bool)
        self._visible = visible

    def enable(self, event_handler):
        """
        Enable the drawable.  Depending on different Drawables, this may mean different things.  An example is Button;
        if enabled, then the button can be pressed.
        :param event_handler: An EventHandler used for registering an event (i.e. TOUCH_DRAG for button)
        :return: None
        """
        assert isinstance(event_handler, Events.EventHandler)
        self._enabled = True

    def disable(self, event_handler):
        """
        Opposite of enable.
        :param event_handler: An EventHandler useful for unregistering the registered event
        :return: None
        """
        assert isinstance(event_handler, Events.EventHandler)
        self._enabled = False

    def draw(self, surface):
        """
        Draw the Drawable if this Drawable is visible.
        :param surface: The surface on which the Drawable is drawn on.
        :return: None
        """
        if not self._visible:
            return

    def exit(self):
        """
        For graceful cleanup of anything necessary when the app is exiting/quitting.
        :return: None
        """
        pass

    def move(self, dx, dy):
        """
        Drawable is moved.  This is needed for when the page is scrolled (all Drawables are moved in the x and y
        directions).  Depending on the Drawable, you may need to add extra calculations in this function to updated
        local variables that are based of of the Drawable x and y.  For example, if some drawable D has a x and y, but
        also has center_x and center_y local variables to make something easier to handle.  Move also needs to update
        these local variables.
        :param dx: The amount things should move in the x direction (positive or negative float)
        :param dy: The amount things should move in the y direction (positive or negative float)
        :return: None
        """
        self.x += dx
        self.y += dy

    def position_inside(self, position):
        """
        A function indidcating whether of not position is inside the object.  This is up to you to define what "inside"
        means.  An example of this is Button; if a click position is in the button, then the button does something.
        :param position: A tuple or list of length 2 indicating x and y position
        :return: Whether or not position is inside Drawable (boolean)
        """
        assert (isinstance(position, tuple) or isinstance(position, list)) and len(position) == 2
        return False


class Line(Drawable):
    def __init__(self, x, y, width, height, color=Colors.WHITE, line_width=1):
        """
        A simple line class.  Note that one end of the line is (x, y) while the other is (x + width, y + height).
        :param x: The x position of one end of the line
        :param y: The y position of one end of the line
        :param width: x distance from self.x to the other end of the line (positive or negative float)
        :param height: y distance from self.y to the other end of the line (positive or negative float)
        :param color: Color of the line (pick from Colors or pass in a tuple of length 3 with positive integers)
        :param line_width: Positive integer indicating the width of the line
        """
        super().__init__(x, y, width, height)
        assert Colors.is_color(color)
        assert isinstance(self.line_width, int) and self.line_width > 0
        self.color = color
        self.line_width = line_width

    def draw(self, surface):
        """
        Just implementing the Drawable draw function so this line can be drawn.
        :param surface: The surface on which the Drawable is drawn on.
        :return: None
        """
        pygame.draw.line(surface, self.color, [self.x, self.y], [self.x + self.width, self.y + self.height])


class Button(Drawable):
    SHAPES = {
        "rectangle": 0,
        "circle": 1
    }

    def __init__(self, x, y, width, height, text, font_size, bg_color, fg_color, shape=SHAPES["rectangle"], callback=None, args=None):
        """
        Rectangular or circular button with text on it.  Can define custom callback function and extra arguments to pass in
        when button is pressed.
        :param x: Top left coordinate for rectangular button and center for circular
        :param y: Top left coordinate for rectangular button and center for circular
        :param width: Width for rectangular button and radius for circular
        :param height: Height for rectangular button and nothing for circular
        :param text: Text on the button
        :param font_size: Size of the text on the button
        :param bg_color: Button background color
        :param fg_color: Text color
        :param shape: Shape (pick from the class SHAPES options)
        :param callback: Callback function when button is pressed.  First parameter passed in will the the event that
                        triggered the callback and args is passed in as the remaining parameters.
        :param args: Extra arguments to be passed into the callback function
        """
        super().__init__(x, y, width, height)
        assert shape in Button.SHAPES.keys()
        assert args is None or isinstance(args, list)
        self.radius = width     # for circle button width becomes the radius.
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.font_size = font_size
        self._my_font = pygame.font.Font(None, font_size)
        self.shape = shape
        self.callback = callback
        self.args = args if args is not None else []

    def enable(self, event_handler):
        """
        Enable the button (register to event_handler for a TOUCH_DRAG event)
        :param event_handler: The event handler that handles all events
        :return: None
        """
        super().enable(event_handler)
        event_handler.register_event(self, Events.EventTypes.TOUCH_DRAG, self.event_callback)

    def disable(self, event_handler):
        """
        Disable the button (unregister to event_handler for a TOUCH_DRAG event)
        :param event_handler: The event handler that handles all events
        :return: None
        """
        super().disable(event_handler)
        event_handler.unregister_event(self, Events.EventTypes.TOUCH_DRAG)

    def draw(self, surface):
        """
        Custom draw function
        :param surface: The surface on which the Drawable is drawn on.
        :return: None
        """
        super().draw(surface)
        if self.shape == 0:
            pygame.draw.circle(surface, self.bg_color, (self.x, self.y), self.radius)
            text_surface = self._my_font.render(self.text, True, self.fg_color)
            text_rect = text_surface.get_rect(center=(self.x, self.y))
            surface.blit(text_surface, text_rect)
        else:
            rect = (self.x, self.y, self.width, self.height)
            pygame.draw.rect(surface, self.bg_color, rect)
            text_surface = self._my_font.render(self.text, True, self.fg_color)
            text_rect = text_surface.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
            surface.blit(text_surface, text_rect)

    def event_callback(self, event):
        """
        This is the function that is registered to the event_handler to be triggered upon TOUCH_DRAG events.  This
        checks to see if the button is enabled, the TOUCH_DRAG event has no significant movement (refer to documentation
        for TOUCH_DRAG), and whether or not the press was inside the button.
        :param event: The event that triggered this callback
        :return: None
        """
        assert isinstance(event, Events.EventTouchDrag)

        if self._enabled and event.no_movement and self.position_inside(event.position_end):
            self.callback(event, *self.args)

    def position_inside(self, pos):
        """
        Given a position, see if inside the button.
        :param pos: (x, y) coordinate
        :returns: True if pos inside button, False otherwise
        """
        if self.shape == 0:
            distance = ((pos[1] - self.y) ** 2 + (pos[0] - self.x) ** 2) ** 0.5
            return distance <= self.radius
        else:
            left = self.x
            right = self.x + self.width
            top = self.y
            bottom = self.y + self.height
            return left <= pos[0] <= right and top <= pos[1] <= bottom


class Text(Drawable):
    # These are the different alignments possible (for x and y directions)
    ALIGN_X_CENTER = 0
    ALIGN_X_LEFT = 1
    ALIGN_X_RIGHT = 2
    ALIGN_Y_CENTER = 3
    ALIGN_Y_TOP = 4
    ALIGN_Y_BOTTOM = 5

    def __init__(self, x, y, text, font_size, fg_color, align_x=ALIGN_X_CENTER, align_y=ALIGN_Y_CENTER, rotate=0):
        """
        Create a text to display on the screen
        :param x: This is the x position of the text (what it actually means depends on align_x)
        :param y: This is the y position of the text (what it actually means depends on align_y)
        :param text: This is the actual text to display
        :param font_size: Size of the font
        :param fg_color: Font color
        :param align_x: How do you want to define the x coordinate?  Center of text (ALIGN_X_CENTER), left of text
                    (ALIGN_X_LEFT) or right of text (ALIGN_X_RIGHT)?  These will come in handy when you know where you
                    want text to extend from and don't know the coordinates of the left most part of the text will be.
        :param align_y: Refer to align_x.  Similar but use ALIGN_Y_CENTER, ALIGN_Y_TOP, and ALIGN_Y_BOTTOM
        :param rotate: How much do you want the text to be rotated?
        """
        super().__init__(x, y, 0, 0)
        assert Colors.is_color(fg_color)
        assert align_x in [Text.ALIGN_X_CENTER, Text.ALIGN_X_LEFT, Text.ALIGN_X_RIGHT]
        assert align_y in [Text.ALIGN_Y_CENTER, Text.ALIGN_Y_TOP, Text.ALIGN_Y_BOTTOM]
        assert (isinstance(rotate, int) or isinstance(rotate, float)) and 0 <= rotate <= 360
        self.text = text
        self.fg_color = fg_color
        self._my_font = pygame.font.Font(None, font_size)
        self.align_x = align_x
        self.align_y = align_y
        self._rotate = rotate

    def draw(self, surface):
        """
        Custom draw function
        :param surface: The surface on which the Drawable is drawn on.
        :return: None
        """
        super().draw(surface)
        text_surface = self._my_font.render(str(self.text), True, self.fg_color)
        text_surface = pygame.transform.rotate(text_surface, self._rotate)
        text_rect = text_surface.get_rect(**self._convert_align_to_arguments())
        surface.blit(text_surface, text_rect)

    def _convert_align_to_arguments(self):
        """
        Convert the alignment to a dictionary to pass into get_rect.
        :return: dict to pass into get_rect
        """
        dict = {}
        if self.align_x == Text.ALIGN_X_LEFT:
            dict["left"] = self.x
        elif self.align_x == Text.ALIGN_X_RIGHT:
            dict["right"] = self.x
        else:
            dict["centerx"] = self.x

        if self.align_y == Text.ALIGN_Y_TOP:
            dict["top"] = self.y
        elif self.align_y == Text.ALIGN_Y_BOTTOM:
            dict["bottom"] = self.y
        else:
            dict["centery"] = self.y
        return dict