import Colors
import Drawables


class Page(object):
    def __init__(self, event_handler, bg_color):
        self._event_handler = event_handler
        self._bg_color = bg_color

        self._drawables = []
        self._enabled = False
        self._visible = False

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

        for drawable in self._drawables:
            drawable.disable(self._event_handler)

    def draw(self, surface):
        surface.fill(self._bg_color)

        # Draw the items on the page
        for drawable in self._drawables:
            drawable.draw(surface)


class TempPage(Page):
    def __init__(self, event_handler):
        super().__init__(event_handler, Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Hello", 10, Colors.WHITE, Colors.BLUE, callback=self.button_callback)
        self._drawables.append(self.button)

    def button_callback(self, event):
        print("Button pressed!: {}".format(event))