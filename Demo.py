import argparse

import Chart
import Colors
import Constants
import Drawables
import Events
import Graphs
import Pages
import PyDisplay


class ScatterDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(pydisplay, event_handler, "Scatter", page_size, Colors.BLACK)

        self.scatter = Graphs.Scatter(0, 0, *self.page_size)
        self.scatter.set_title("TEST")
        self.scatter.set_x_label("x axis")
        self.scatter.set_y_label("y axis")
        self.scatter.add_dataset("test", [0, 1, 2, 3, -1, -2, -3, -11, -10], [0, 1, 2, 3, -1, -2, -3, -11, -6])
        # self.scatter.setup_new_data_source("test", ScatterDemo._new_data_from_fifo)

        # self.line = Graphs.Line(0, 0, *self.page_size)
        # self.line.set_title("TEST")
        # self.line.set_x_label("x axis")
        # self.line.set_y_label("y axis")
        # self.line.create_plot()
        # self.line.add_dataset("test1", [0, 1, 2, 3, -1, -2, -3], [1, 2, 3, 4, 0, -1, -2], color=Colors.RED)
        # self.line.add_dataset("test2", [0, -1, -2, -3, 1, 2, 3], [1, 2, 3, 4, 0, -1, -2], color=Colors.GREEN)
        #
        # self.bar = Graphs.Bar(0, 0, *self.page_size)
        # self.bar.set_title("TEST")
        # self.bar.set_x_label("x axis")
        # self.bar.set_y_label("y axis")
        # self.bar.add_dataset("test", [0, 1, 2, 3, -1, -2, -3], [0, 1, 2, 3, -1, -2, -3], color=Colors.BLUE)

        self._drawables.append(self.scatter)
        # self._drawables.append(self.line)
        # self._drawables.append(self.bar)

    @staticmethod
    def _new_data_from_fifo(graph, fifo_source, data):
        assert isinstance(graph, Graphs.Graph)
        print("New data from {}: '{}'".format(fifo_source, data))
        x_value, y_value = list(map(float, data.split(" ")))
        graph.add_datum("test", x_value, y_value)


class BarDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(pydisplay, event_handler, "Bar", page_size, Colors.BLACK)

        self.bar = Graphs.Bar(0, 0, *self.page_size)
        self.bar.set_title("TEST")
        self.bar.set_x_label("x axis")
        self.bar.set_y_label("y axis")
        self.bar.add_dataset("test", [0, 1, 2, 3, -1, -2, -3], [0, 1, 2, 3, -1, -2, -3], color=Colors.BLUE)
        # self.bar.setup_new_data_source("test", ScatterDemo._new_data_from_fifo)

        self._drawables.append(self.bar)

    @staticmethod
    def _new_data_from_fifo(graph, fifo_source, data):
        assert isinstance(graph, Graphs.Graph)
        print("New data from {}: '{}'".format(fifo_source, data))
        x_value, y_value = list(map(float, data.split(" ")))
        graph.add_datum("test", x_value, y_value)


class ButtonsTextDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        super().__init__(pydisplay, event_handler, "Buttons", (400, 300), Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Hello", 25, Colors.WHITE, Colors.BLUE,
                                       callback=self.button_callback)
        self.textBox = Drawables.Text(50, 110, "textbox here", 15, Colors.RED, Drawables.Text.ALIGN_X_CENTER, Drawables.Text.ALIGN_Y_CENTER, rotate=90)
        self.textBox2 = Drawables.Text(200, 100, "textbox here", 15, Colors.WHITE, Drawables.Text.ALIGN_X_RIGHT, Drawables.Text.ALIGN_Y_TOP)
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


class ChartDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(pydisplay, event_handler, "Chart", page_size, Colors.BLACK)

        self.chart = Chart.Chart(0, 0, *page_size)
        self.chart.add_dataset("test1", [0, 1, 2, 3, -1, -2, -3])
        self.chart.add_dataset("test2", [0, 1, 2, 3, -1, -2, -3])
        self.chart.add_sorting_scheme(Chart.Sorting.OTHER, "test1", ChartDemo._compare)
        # self.chart.setup_new_data_source("test", ChartDemo._new_data_from_fifo)

        self._drawables.append(self.chart)

    @staticmethod
    def _compare(a, b):
        return abs(a[0]) - abs(b[0])

    @staticmethod
    def _new_data_from_fifo(chart, fifo_source, data):
        assert isinstance(chart, Chart.Chart)
        values = list(map(float, data.split(" ")))
        values_dict = {"test1": values[0], "test2": values[1]}
        chart.add_datum(values_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--not_on_pitft", action='store_true', help="Don't run on piTFT screen?")
    parser.add_argument("--disable_touchscreen", action='store_true', help="Don't usetouchscreen?")
    parser.add_argument("--disable_button", action='store_true', help="Don't use buttons connected to GPIO pins?")

    args = parser.parse_args()

    page_classes = [BarDemo, ScatterDemo, ChartDemo, ButtonsTextDemo]
    page_class_args = [[], [], [], []]
    pydisplay = PyDisplay.PyDisplay(not args.not_on_pitft, not args.disable_touchscreen, not args.disable_button)
    pydisplay.setup_pages(page_classes, page_class_args, Pages.PageManager.SWITCHER_LOCATIONS["BOTTOM"])
    pydisplay.run()
