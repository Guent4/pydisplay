import argparse
import random

from pydisplay import Chart
from pydisplay import Colors
from pydisplay import Constants
from pydisplay import Drawables
from pydisplay import Events
from pydisplay import Graphs
from pydisplay import Pages
from pydisplay import PyDisplay


class ScatterDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(pydisplay, event_handler, "Scatter", page_size, Colors.BLACK)

        self.scatter = Graphs.Scatter(0, 0, *self.page_size, connect_points=True)
        self.scatter.set_title("TEST")
        self.scatter.set_x_label("x axis")
        self.scatter.set_y_label("y axis")
        self.scatter.add_dataset("test", [0, 1, 2, 3, -1, -2, -3, -11, -10], [0, 1, 2, 3, -1, -2, -3, -11, -6])
        self.scatter.setup_new_data_source("testScatter", ScatterDemo._new_data_from_fifo)

        self._drawables.append(self.scatter)

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

        self.bar = Graphs.Bar(0, 0, *self.page_size, num_columns=7)
        self.bar.set_title("TEST")
        self.bar.set_x_label("x axis")
        self.bar.set_y_label("y axis")
        self.bar.add_dataset("test1", None, [0, 1, 2, 3, -1, -2, -10], color=Colors.BLUE)
        self.bar.add_dataset("test2", None, [-10, 0, 1, 2, 3, -1, -2], color=Colors.GREEN)

        self._drawables.append(self.bar)

    @staticmethod
    def _new_data_from_fifo(graph, fifo_source, data):
        assert isinstance(graph, Graphs.Graph)
        print("New data from {}: '{}'".format(fifo_source, data))
        x_value, y_value = list(map(float, data.split(" ")))
        graph.add_datum("test", x_value, y_value)


class HistogramDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(pydisplay, event_handler, "Hist", page_size, Colors.BLACK)

        options = [x + 0.5 for x in range(6)]

        self.hist = Graphs.Histogram(0, 0, *self.page_size, Graphs.Histogram.generate_bins(0, 7, 1))
        self.hist.set_title("TEST")
        self.hist.set_x_label("x axis")
        self.hist.set_y_label("y axis")
        self.hist.add_dataset("test1", [random.choice(options) for _ in range(30)], None, color=Colors.BLUE)
        self.hist.add_dataset("test2", [random.choice(options) for _ in range(30)], None, color=Colors.GREEN)
        self.hist.setup_new_data_source("testHist", HistogramDemo._new_data_from_fifo)

        self._drawables.append(self.hist)

    @staticmethod
    def _new_data_from_fifo(graph, fifo_source, data):
        assert isinstance(graph, Graphs.Graph)
        print("New data from {}: '{}'".format(fifo_source, data))
        x_value = float(data)
        graph.add_datum("test", x_value, None)


class LineDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (Constants.PI_TFT_SCREEN_SIZE[0], Constants.PI_TFT_SCREEN_SIZE[1] - Pages.PageManager.SWITCHER_HEIGHT)
        super().__init__(pydisplay, event_handler, "Line", page_size, Colors.BLACK)

        self.line = Graphs.Line(0, 0, *self.page_size)
        self.line.set_title("TEST")
        self.line.set_x_label("x axis")
        self.line.set_y_label("y axis")
        self.line.add_dataset("linear", *self.line.generate_ys_from_function(LineDemo._x_to_y_linear))
        self.line.add_dataset("quadratic", *self.line.generate_ys_from_function(LineDemo._x_to_y_quadratic))

        self._drawables.append(self.line)

    @staticmethod
    def _x_to_y_linear(x):
        return x / 2

    @staticmethod
    def _x_to_y_quadratic(x):
        return x ** 2


class ButtonsTextDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        super().__init__(pydisplay, event_handler, "Buttons", (400, 300), Colors.BLACK)

        self.button = Drawables.Button(50, 50, 100, 50, "Hello", 25, Colors.WHITE, Colors.BLUE, callback=self.button_callback)
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
        self._pydisplay.exit()


class ChartDemo(Pages.Page):
    def __init__(self, pydisplay, event_handler):
        page_size = (500, 500)
        super().__init__(pydisplay, event_handler, "Chart", page_size, Colors.BLACK)

        self.chart = Chart.Chart(0, 0, *page_size)
        self.chart.add_dataset("test1", [0, 1, 2, 3, -1, -2, -3])
        self.chart.add_dataset("test2", [0, 1, 2, 3, -1, -2, -3])
        self.chart.add_dataset("test3", [0, 1, 2, 3, -1, -2, -3])
        self.chart.add_dataset("test4", [0, 1, 2, 3, -1, -2, -3])
        self.chart.add_sorting_scheme(Chart.Sorting.OTHER, "test1", ChartDemo._compare)
        self.chart.setup_new_data_source("testChart", ChartDemo._new_data_from_fifo)

        self._drawables.append(self.chart)

    @staticmethod
    def _compare(a, b):
        return abs(a[0]) - abs(b[0])

    @staticmethod
    def _new_data_from_fifo(chart, fifo_source, data):
        assert isinstance(chart, Chart.Chart)
        values = list(map(float, data.split(" ")))
        values_dict = {"test1": values[0], "test2": values[1], "test3": values[2], "test4": values[3]}
        chart.add_datum(values_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--not_on_pitft", action='store_true', help="Don't run on piTFT screen?")
    parser.add_argument("--disable_touchscreen", action='store_true', help="Don't usetouchscreen?")
    parser.add_argument("--disable_button", action='store_true', help="Don't use buttons connected to GPIO pins?")

    args = parser.parse_args()

    page_classes = [ChartDemo, HistogramDemo, BarDemo, LineDemo, ScatterDemo, ButtonsTextDemo]
    page_class_args = [[], [], [], [], [], []]
    pydisplay = PyDisplay.PyDisplay(not args.not_on_pitft, not args.disable_touchscreen, not args.disable_button)
    pydisplay.setup_pages(page_classes, page_class_args, Pages.PageManager.SWITCHER_LOCATIONS["BOTTOM"])
    pydisplay.run()
