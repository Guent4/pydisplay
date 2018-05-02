import argparse

import Colors
import Constants
import Drawables
import Events
import Graphs
import Pages
import PyDisplay


class TempPage1(Pages.Page):
    def __init__(self, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(event_handler, "temp2", page_size, Colors.BLACK)

        self.scatter = Graphs.Scatter(0, 0, *self.page_size)
        self.scatter.set_title("TEST")
        self.scatter.set_x_label("x axis")
        self.scatter.set_y_label("y axis")
        self.scatter.create_plot()
        self.scatter.add_dataset("test", [0, 1, 2, 3, -1, -2, -3], [0, 1, 2, 3, -1, -2, -3])
        # self.scatter.setup_new_data_source("test", TempPage1._new_data_from_fifo)

        self.line = Graphs.Line(0, 0, *self.page_size)
        self.line.set_title("TEST")
        self.line.set_x_label("x axis")
        self.line.set_y_label("y axis")
        self.line.create_plot()
        self.line.add_dataset("test", [0, 1, 2, 3, -1, -2, -3], [1, 2, 3, 4, 0, -1, -2], color=Colors.RED)

        self.line2 = Graphs.Line(0, 0, *self.page_size)
        self.line2.set_title("TEST")
        self.line2.set_x_label("x axis")
        self.line2.set_y_label("y axis")
        self.line2.create_plot()
        self.line2.add_dataset("test", [0, -1, -2, -3, 1, 2, 3], [1, 2, 3, 4, 0, -1, -2], color=Colors.RED)

        self.bar = Graphs.Bar(0, 0, *self.page_size)
        self.bar.set_title("TEST")
        self.bar.set_x_label("x axis")
        self.bar.set_y_label("y axis")
        self.bar.create_plot()
        self.bar.add_dataset("test", [0, 1, 2, 3, -1, -2, -3], [0, 1, 2, 3, -1, -2, -3], color=Colors.BLUE)

        self._drawables.append(self.scatter)
        self._drawables.append(self.line)
        self._drawables.append(self.line2)
        self._drawables.append(self.bar)

    @staticmethod
    def _new_data_from_fifo(graph, fifo_source, data):
        assert isinstance(graph, Graphs.Graph)
        print(graph)
        print("New data from {}: '{}'".format(fifo_source, data))
        x_value, y_value = list(map(float, data.split(" ")))
        graph.add_datum("test", x_value, y_value)


class TempPage2(Pages.Page):
    def __init__(self, event_handler):
        super().__init__(event_handler, "temp1", (400, 300), Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Hello", 25, Colors.WHITE, Colors.BLUE, callback=self.button_callback)
        self.textBox = Drawables.TextBox(50, 110, 100, 50, "textbox here", 15, Colors.CYAN, Colors.RED, "center", "center", rotate = 90)
        self.textBox2 = Drawables.TextBox(200, 100, 100, 50, "textbox here", 15, Colors.CYAN, Colors.WHITE, "right", "top")
        self._drawables.append(self.button)
        self._drawables.append(self.textBox)
        self._drawables.append(self.textBox2)

        self._event_handler.register_event(object, Events.EventTypes.BUTTON_HOLD, self.button_27_callback)

    def button_callback(self, event):
        print("Button pressed!: {}".format(event))

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
