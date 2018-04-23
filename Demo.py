import Colors
import Drawables
import Events
import Pages


class TempPage1(Pages.Page):
    def __init__(self, event_handler):
        super().__init__(event_handler, "temp1", (400, 300), Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Hello", 25, Colors.WHITE, Colors.BLUE, callback=self.button_callback)
        self._drawables.append(self.button)

        self._event_handler.register_event(object, Events.EventTypes.BUTTON_HOLD, self.button_27_callback)

    def button_callback(self, event):
        print("Button pressed!: {}".format(event))

    def button_27_callback(self, event):
        print(event.pin)
        if event.pin != 27:
            return

        print("Button 27 pressed for {}!".format(event.duration))


class TempPage2(Pages.Page):
    def __init__(self, event_handler):
        super().__init__(event_handler, "temp2", (400, 300), Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Bye", 25, Colors.WHITE, Colors.BLUE, callback=self.button_callback)
        self._drawables.append(self.button)

        self._event_handler.register_event(object, Events.EventTypes.BUTTON_HOLD, self.button_27_callback)

    def button_callback(self, event):
        print("Button pressed!: {}".format(event))

    def button_27_callback(self, event):
        print(event.pin)
        if event.pin != 27:
            return

        print("Button 27 pressed for {}!".format(event.duration))