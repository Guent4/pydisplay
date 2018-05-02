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
        pass

    def disable(self, event_handler):
        assert isinstance(event_handler, Events.EventHandler)
        self._enabled = False
        pass

    def draw(self, surface):
        if not self._visible:
            return

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def position_inside(self, position):
        pass


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


class TextBox(Drawable):
    def __init__(self, x, y, width, height, text, size, bg_color, fg_color, x_align, y_align, rotate=0):
        super().__init__(x, y, width, height)
        self.width = width
        self.height = height
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self._my_font = pygame.font.Font(None, size)
        self._align = self.set_align(x_align,y_align)
        self._rotate = rotate

    def set_align(self, x_align, y_align):
        dict = {}
        if x_align == "left":
            dict['left'] = self.x
        elif x_align == "right":
            dict['right'] = self.x + self.width
        else:
            dict['centerx'] = self.x + self.width/2

        if y_align == "top":
            dict['top'] = self.y
        elif y_align == "bottom":
            dict['bottom'] = self.y + self.height
        else:
            dict['centery'] = self.y + self.height/2
        return dict

    def enable(self, event_handler):
        super().enable(event_handler)

    def disable(self, event_handler):
        super().disable(event_handler)

    def draw(self, surface):
        super().draw(surface)
        if (self._rotate % 90) == 0:
            if ((self._rotate / 90) % 2) == 0:
                rect = (self.x, self.y, self.width, self.height)
            else:
                rect = (self.x, self.y, self.height, self.width)

            pygame.draw.rect(surface, self.bg_color, rect)
        text_surface = self._my_font.render(self.text, True, self.fg_color)
        text_surface = pygame.transform.rotate(text_surface, self._rotate)
        text_rect = text_surface.get_rect(**self._align)
        surface.blit(text_surface, text_rect)

    # def rotate_rect(self, rect, ):


    def position_inside(self, position):
        pass
