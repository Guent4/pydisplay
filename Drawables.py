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

    def draw(self, surface):
        if not self._visible:
            return

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible

    def enable(self, event_handler):
        assert isinstance(event_handler, Events.EventHandler)
        self._enabled = True
        pass

    def disable(self, event_handler):
        assert isinstance(event_handler, Events.EventHandler)
        self._enabled = False
        pass

    def move(self, dx, dy):
        self.x += dx
        self.y += dy


class Button(Drawable):
    def __init__(self, x, y, width, height, text, size, bg_color, fg_color, callback=None, args=None):
        assert args is None or isinstance(args, list)
        super().__init__(x, y, width, height)
        self.text = text
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
        rect = (self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, rect)
        text_surface = self._my_font.render(self.text, True, self.fg_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
        surface.blit(text_surface, text_rect)

    def event_callback(self, event):
        assert isinstance(event, Events.EventTouchDrag)

        if self._enabled and event.no_movement and self._click_inside(event.position_end):
            self.callback(event, *self.args)

    def _click_inside(self, pos):
        """
        Given a (x, y), see if inside the button.
        :param pos: a (x, y) coordinate
        :returns: True if pos inside button, False otherwise
        """
        left = self.x
        right = self.x + self.width
        top = self.y
        bottom = self.y + self.height
        return left <= pos[0] <= right and top <= pos[1] <= bottom