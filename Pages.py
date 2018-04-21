import Colors
import Constants
import Drawables
import Events


class Page(object):
    def __init__(self, event_handler, page_size=Constants.PI_TFT_SCREEN_SIZE, bg_color=Colors.BLACK):
        self._screen_size = Constants.PI_TFT_SCREEN_SIZE

        assert isinstance(event_handler, Events.EventHandler)
        assert isinstance(page_size, tuple) and len(page_size) == 2
        assert page_size[0] >= self._screen_size[0] and page_size[1] >= self._screen_size[1]
        assert Colors.is_color(bg_color)

        self._event_handler = event_handler
        self.page_size = page_size
        self.bg_color = bg_color
        self.scrollable = True

        self._drawables = []
        self._enabled = False
        self._visible = False

        self._location = (0, 0)
        self._event_handler.register_event(self, Events.EventTypes.TOUCH_MOVEMENT, self._scroll)

    @property
    def drawables(self):
        return self._drawables

    @drawables.setter
    def drawables(self, drawables):
        if isinstance(drawables, list):
            assert all(isinstance(d, Drawables.Drawable) for d in drawables)
            self._drawables.extend(drawables)
        else:
            assert isinstance(drawables, Drawables.Drawable)
            self._drawables.append(drawables)

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible
        for drawable in self._drawables:
            drawable.visible = visible

    def enable(self):
        self._enabled = True

        for drawable in self._drawables:
            drawable.enable(self._event_handler)

    def disable(self):
        self._enabled = False

        self._event_handler.unregister_event(self, Events.EventTypes.TOUCH_MOVEMENT)
        for drawable in self._drawables:
            drawable.disable(self._event_handler)

    def draw(self, surface):
        surface.fill(self.bg_color)

        # Draw the items on the page
        for drawable in self._drawables:
            drawable.draw(surface)

    def _scroll(self, event):
        assert isinstance(event, Events.EventTouchMovement)
        dx = event.position_new[0] - event.position_old[0]
        dy = event.position_new[1] - event.position_old[1]

        min_dx = 0 - self._location[0]
        max_dx = self.page_size[0] - (self._location[0] + self._screen_size[0])
        min_dy = 0 - self._location[1]
        max_dy = self.page_size[1] - (self._location[1] + self._screen_size[1])
        dx = min(dx, max_dx) if dx > 0 else max(dx, min_dx)
        dy = min(dy, max_dy) if dy > 0 else max(dy, min_dy)

        for drawable in self._drawables:
            drawable.move(dx, dy)

        self._location = (self._location[0] + dx, self._location[1] + dy)


class TempPage(Page):
    def __init__(self, event_handler):
        super().__init__(event_handler, (400, 300), Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Hello", 3, Colors.WHITE, Colors.BLUE, callback=self.button_callback)
        self._drawables.append(self.button)

        self._event_handler.register_event(object, Events.EventTypes.BUTTON_HOLD, self.button_27_callback)

    def button_callback(self, event):
        print("Button pressed!: {}".format(event))

    def button_27_callback(self, event):
        print(event.pin)
        if event.pin != 27:
            return

        print("Button 27 pressed for {}!".format(event.duration))