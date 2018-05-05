import argparse

import Colors
import Constants
import Drawables
import Events
import Graphs
import Pages
import PyDisplay


class TempPage1(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(pydisplay, event_handler, "temp2", page_size, Colors.BLACK)

        self.scatter = Graphs.Scatter(0, 0, *self.page_size)
        self.scatter.set_title("TEST")
        self.scatter.set_x_label("x axis")
        self.scatter.create_plot()
        self.scatter.add_dataset("test", [0, 1, 2, 3, -1, -2, -3], [0, 1, 2, 3, -1, -2, -3])
        # self.scatter.setup_new_data_source("test", TempPage1._new_data_from_fifo)

        self._drawables.append(self.scatter)

    @staticmethod
    def _new_data_from_fifo(graph, fifo_source, data):
        assert isinstance(graph, Graphs.Graph)
        print(graph)
        print("New data from {}: '{}'".format(fifo_source, data))
        x_value, y_value = list(map(float, data.split(" ")))
        graph.add_datum("test", x_value, y_value)


class TempPage2(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        super().__init__(pydisplay, event_handler, "temp1", (400, 300), Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Hello", 25, Colors.WHITE, Colors.BLUE, callback=self.button_callback)
        self.textBox = Drawables.TextBox(50, 110, 100, 50, "textbox here", 15, Colors.CYAN, Colors.BLACK)
        self.textBox2 = Drawables.TextBox(200, 50, 100, 50, "textbox here", 15, Colors.CYAN, Colors.BLACK, align_x=Drawables.TextBox.ALIGN_LEFT)
        self._drawables.append(self.button)
        self._drawables.append(self.textBox)
        self._drawables.append(self.textBox2)

        self._event_handler.register_event(object, Events.EventTypes.BUTTON_HOLD, self.button_27_callback)

    def button_callback(self, event):
        print("Button pressed!: {}".format(event))
        self._pydisplay.exit()

    def button_27_callback(self, event):
        print(event.pin)
        if event.pin != 27:
            return

        print("Button 27 pressed for {}!".format(event.duration))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--not_on_pitft", action='store_true', help="Don't run on piTFT screen?")
    parser.add_argument("--disable_touchscreen", action='store_true', help="Don't usetouchscreen?")
    parser.add_argument("--disable_button", action='store_true', help="Don't use buttons connected to GPIO pins?")

    args = parser.parse_args()

    page_classes = [TempPage1, TempPage2]
    page_class_args = [[], []]
    pydisplay = PyDisplay.PyDisplay(not args.not_on_pitft, not args.disable_touchscreen, not args.disable_button)
    pydisplay.setup_pages(page_classes, page_class_args, Pages.PageManager.SWITCHER_LOCATIONS["BOTTOM"])
    pydisplay.run()
