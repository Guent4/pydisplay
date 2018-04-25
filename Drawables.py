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
    def __init__(self, x, y, width, height, text, size, bg_color, fg_color, x_align, y_align, rotate=0):
        super().__init__(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self._my_font = pygame.font.Font(None, size)
        self._align = self.set_align(x_align,y_align)
        self._rotate = rotate

    def set_align(self, x_align, y_align):
        if x_align == "left":
            if y_align == "top":
                return 1
            elif y_align == "bottom":
                return 2
            else:
                return 3
        elif x_align == "right":
            if y_align == "top":
                return 4
            elif y_align == "bottom":
                return 5
            else:
                return 6
        else:
            if y_align == "top":
                return 7
            elif y_align == "bottom":
                return 8
            else:
                return 9

    def enable(self, event_handler):
        super().enable(event_handler)

    def disable(self, event_handler):
        super().disable(event_handler)

    def draw(self, surface):
        super().draw(surface)
        # rect = (self._top_left[0], self._top_left[1], self._dim[0], self._dim[1])
        # pygame.draw.rect(surface, self.bg_color, rect)
        text_surface = self._my_font.render(self.text, True, self.fg_color)
        text_surface = pygame.transform.rotate(text_surface, self._rotate)
        text_rect = self.set_text_rect(text_surface,self._align)
        surface.blit(text_surface, text_rect)

    # def rotate_rect(self, rect, ):


    def set_text_rect(self,text_surface, align):
        if align == 1:
            return text_surface.get_rect(topleft=self._top_left)
        elif align == 2:
            return text_surface.get_rect(left=self._top_left[0], bottom=(self._top_left[1]+self.height))
        elif align == 3:
            return text_surface.get_rect(left=self._top_left[0], centery=self._center[1])
        elif align == 4:
            return text_surface.get_rect(right=(self._top_left[0] + self.width), top=self._top_left[1])
        elif align == 5:
            return text_surface.get_rect(right=(self._top_left[0] + self.width), bottom=(self._top_left[1]+self.height))
        elif align == 6:
            return text_surface.get_rect(right=(self._top_left[0] + self.width), centery=self._center[1])
        elif align == 7:
            return text_surface.get_rect(centerx=self._center[0], top=self._top_left[1])
        elif align == 8:
            return text_surface.get_rect(centerx=self._center[0], bottom=(self._top_left[1]+self.height))
        else:
            return text_surface.get_rect(center=self._center)

    def position_inside(self, position):
        pass
