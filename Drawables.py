import pygame

import Events


class Drawable(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._enabled = False
        self._visible = False

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible

    def enable(self, event_handler):
        assert isinstance(event_handler, Events.EventHandler)
        self._enabled = True

    def disable(self, event_handler):
        assert isinstance(event_handler, Events.EventHandler)
        self._enabled = False

    def draw(self, surface):
        if not self._visible:
            return

    def exit(self):
        pass

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def position_inside(self, position):
        pass


class Button(Drawable):
    def __init__(self, x, y, width, height, text, size, bg_color, fg_color, callback=None, shape=1, args=None):
        assert args is None or isinstance(args, list)
        super().__init__(x, y, width, height)
        self._top_left = (x, y)
        self._dim = (width, height)
        self.radius = width     # for circle button width becomes the radius.
        self._center = (x + width / 2, y + height / 2)
        self.text = text
        self.shape = shape      # 0 = circle button
        self.bg_color = bg_color
        self.fg_color = fg_color
        self._my_font = pygame.font.Font(None, size)
        self.callback = callback
        self.args = args if args is not None else []

    def enable(self, event_handler):
        super().enable(event_handler)
        event_handler.register_event(self, Events.EventTypes.TOUCH_DRAG, self.event_callback)

    def disable(self, event_handler):
        super().disable(event_handler)
        event_handler.unregister_event(self, Events.EventTypes.TOUCH_DRAG)

    def draw(self, surface):
        super().draw(surface)
        if self.shape == 0:
            pygame.draw.circle(surface, self.bg_color, self._top_left, self.radius)
            text_surface = self._my_font.render(self.text, True, self.fg_color)
            text_rect = text_surface.get_rect(center=self._top_left)
            surface.blit(text_surface, text_rect)
        else:
            rect = (self._top_left[0], self._top_left[1], self._dim[0], self._dim[1])
            pygame.draw.rect(surface, self.bg_color, rect)
            text_surface = self._my_font.render(self.text, True, self.fg_color)
            text_rect = text_surface.get_rect(center=self._center)
            surface.blit(text_surface, text_rect)

    def event_callback(self, event):
        assert isinstance(event, Events.EventTouchDrag)

        if self._enabled and event.no_movement and self.position_inside(event.position_end):
            self.callback(event, *self.args)

    def position_inside(self, pos):
        """
        Given a (x, y), see if inside the button.
        :param pos: a (x, y) coordinate
        :returns: True if pos inside button, False otherwise
        """
        if self.shape == 0:
            distance = ((pos[1] - self._top_left[1]) ** (2) + (pos[0] - self._top_left[0]) ** (2)) ** (0.5)
            return distance <= self.radius
        else:
            left = self._top_left[0]
            right = self._top_left[0] + self._dim[0]
            top = self._top_left[1]
            bottom = self._top_left[1] + self._dim[1]
            return left <= pos[0] <= right and top <= pos[1] <= bottom


class TextBox(Drawable):
    ALIGN_CENTER = 0
    ALIGN_LEFT = 1
    ALIGN_RIGHT = 2
    ALIGN_TOP = 1
    ALIGN_BOTTOM = 2

    def __init__(self, x, y, width, height, text, size, bg_color, fg_color, align_x=ALIGN_CENTER, align_y=ALIGN_CENTER):
        super().__init__(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self._my_font = pygame.font.Font(None, size)
        self._align_x = align_x
        self._align_y = align_y

    def enable(self, event_handler):
        super().enable(event_handler)

    def disable(self, event_handler):
        super().disable(event_handler)

    def draw(self, surface):
        super().draw(surface)
        if self._align_x == TextBox.ALIGN_CENTER:
            # TODO fix this
            # rect = (self.x, self.y, self.width, self.height)
            # pygame.draw.rect(surface, self.bg_color, rect)
            text_surface = self._my_font.render(self.text, True, self.fg_color)
            text_rect = text_surface.get_rect(center=[self.x, self.y])
            surface.blit(text_surface, text_rect)
        elif self._align_x == TextBox.ALIGN_LEFT:
            # TODO fix this
            # rect = (self.x, self.y, self.width, self.height)
            # pygame.draw.rect(surface, self.bg_color, rect)
            text_surface = self._my_font.render(self.text, True, self.fg_color)
            text_rect = text_surface.get_rect(left=self.x, centery=self.y)
            surface.blit(text_surface, text_rect)
        elif self._align_x == TextBox.ALIGN_RIGHT:
            raise NotImplemented
        else:
            raise Exception

    def position_inside(self, position):
        pass
