import pygame

import Colors
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


class Line(Drawable):
    def __init__(self, x, y, width, height, color=Colors.WHITE, line_width=1):
        super().__init__(x, y, width, height)
        self.color = color
        self.line_width = line_width

    def draw(self, surface):
        pygame.draw.line(surface, self.color, [self.x, self.y], [self.x + self.width, self.y + self.height])


class Button(Drawable):
    def __init__(self, x, y, width, height, text, size, bg_color, fg_color, callback=None, shape=1, args=None):
        assert args is None or isinstance(args, list)
        super().__init__(x, y, width, height)
        self.radius = width     # for circle button width becomes the radius.
        self._center = (self.x + width / 2, self.y + height / 2)
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
            distance = ((pos[1] - self.y) ** (2) + (pos[0] - self.x) ** (2)) ** (0.5)
            return distance <= self.radius
        else:
            left = self.x
            right = self.x + self.width
            top = self.y
            bottom = self.y + self.height
            return left <= pos[0] <= right and top <= pos[1] <= bottom


class Text(Drawable):
    ALIGN_X_CENTER = 0
    ALIGN_X_LEFT = 1
    ALIGN_X_RIGHT = 2
    ALIGN_Y_CENTER = 3
    ALIGN_Y_TOP = 4
    ALIGN_Y_BOTTOM = 5

    def __init__(self, x, y, text, font_size, fg_color, align_x=ALIGN_X_CENTER, align_y=ALIGN_Y_CENTER, rotate=0):
        assert align_x in [Text.ALIGN_X_CENTER, Text.ALIGN_X_LEFT, Text.ALIGN_X_RIGHT]
        assert align_y in [Text.ALIGN_Y_CENTER, Text.ALIGN_Y_TOP, Text.ALIGN_Y_BOTTOM]

        super().__init__(x, y, 0, 0)
        self.text = text
        self.fg_color = fg_color
        self._my_font = pygame.font.Font(None, font_size)
        self.align_x = align_x
        self.align_y = align_y
        self._rotate = rotate

    def set_align(self, align_x, align_y):
        dict = {}
        if align_x == Text.ALIGN_X_LEFT:
            dict["left"] = self.x
        elif align_x == Text.ALIGN_X_RIGHT:
            dict["right"] = self.x
        else:
            dict["centerx"] = self.x

        if align_y == Text.ALIGN_Y_TOP:
            dict["top"] = self.y
        elif align_y == Text.ALIGN_Y_BOTTOM:
            dict["bottom"] = self.y
        else:
            dict["centery"] = self.y
        return dict

    def enable(self, event_handler):
        super().enable(event_handler)

    def disable(self, event_handler):
        super().disable(event_handler)

    def draw(self, surface):
        super().draw(surface)
        text_surface = self._my_font.render(self.text, True, self.fg_color)
        text_surface = pygame.transform.rotate(text_surface, self._rotate)
        align = self.set_align(self.align_x, self.align_y)
        text_rect = text_surface.get_rect(**align)
        surface.blit(text_surface, text_rect)