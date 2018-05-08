import os
import select
import stat
import threading

import pygame

import Colors
import Drawables


class GraphTypes(object):
    SCATTER = 0
    BAR = 1
    HISTOGRAM = 2
    LINE = 3


class Graph(Drawables.Drawable):
    FIFO_CLOSING_COMMAND = "CLOSING"

    def __init__(self, x, y, width, height):
        """
        Note here that x and y are the top left coordinate of the entire Graph, not data_x and data_y or where the
        the plot is within the graph
        """
        super(Graph, self).__init__(x, y, width, height)

        self._plot = {"x": 0, "y": 0, "width": 0, "height": 0, "bg_color": None, "fg_color": None}
        self._axis = {"x_min": 0, "x_max": 0, "x_interval": 0, "y_min": 0, "y_max": 0, "y_interval": 0}
        self._drawables = {"title": None, "x_label": None, "y_label": None, "x_axis": None, "y_axis": None,
                           "x_ticks": [], "x_numbers": [], "y_ticks": [], "y_numbers": []}

        self.create_plot()
        self.set_bounds(x_min=-10, x_max=10, x_interval=2, y_min=-7, y_max=7, y_interval=2)

        self.datasets = dict()
        self.fifo_sources = []

    def create_plot(self, offset_left=40, offset_right=10, offset_top=30, offset_bottom=30, bg_color=Colors.BLACK, fg_color=Colors.WHITE):
        self._plot["offset_x"] = offset_left
        self._plot["offset_y"] = offset_top
        self._plot["width"] = self.width - offset_right - offset_left
        self._plot["height"] = self.height - offset_top - offset_bottom
        self._plot["bg_color"] = bg_color
        self._plot["fg_color"] = fg_color

    def set_bounds(self, x_min=None, x_max=None, x_interval=None, y_min=None, y_max=None, y_interval=None):
        if x_min is None: x_min = self._axis["x_min"]
        if x_max is None: x_max = self._axis["x_max"]
        if x_interval is None: x_interval = self._axis["x_interval"]
        if y_min is None: y_min = self._axis["y_min"]
        if y_max is None: y_max = self._axis["y_max"]
        if y_interval is None: y_interval = self._axis["y_interval"]

        # Make sure the inputs are reasonable
        assert x_max > x_min and x_interval > 0
        assert y_max > y_min and y_interval > 0

        # Store the variables
        self._axis["x_min"] = x_min
        self._axis["x_max"] = x_max
        self._axis["x_interval"] = x_interval
        self._axis["y_min"] = y_min
        self._axis["y_max"] = y_max
        self._axis["y_interval"] = y_interval

        # Some local variables
        plot_x = self.x + self._plot["offset_x"]
        plot_y = self.y + self._plot["offset_y"]
        width = self._plot["width"]
        height = self._plot["height"]

        # Figure out the axes
        self._axis_value_calculate()
        self._drawables["x_axis"] = Drawables.Line(plot_x, self._axis["x_axis_y"], width, 0, self._plot["fg_color"])
        self._drawables["y_axis"] = Drawables.Line(self._axis["y_axis_x"], plot_y, 0, height, self._plot["fg_color"])

        # Figure out x tick marks
        if x_min <= 0 and x_max <= 0:
            x_num_ticks = abs(x_max - x_min) / x_interval
            x_tick_distance_apart = width / x_num_ticks
            x_ticks_x = [plot_x + width - i * x_tick_distance_apart for i in
                         range(int(x_num_ticks), -1, -1)]
            x_ticks_values = [x_max - i * x_interval for i in range(int(x_num_ticks), -1, -1)]
        elif x_min >= 0 and x_max >= 0:
            x_num_ticks = abs(x_max - x_min) / x_interval
            x_tick_distance_apart = width / x_num_ticks
            x_ticks_x = [plot_x + i * x_tick_distance_apart for i in range(int(x_num_ticks) + 1)]
            x_ticks_values = [x_min + i * x_interval for i in range(int(x_num_ticks) + 1)]
        else:
            x_num_ticks_positive = x_max / x_interval
            x_num_ticks_negative = abs(x_min) / x_interval
            x_tick_distance_apart = width / (x_num_ticks_positive + x_num_ticks_negative)
            x_ticks_x = [self._axis["y_axis_x"] - i * x_tick_distance_apart for i in range(int(x_num_ticks_negative), -1, -1)]
            x_ticks_x.extend([self._axis["y_axis_x"] + i * x_tick_distance_apart for i in range(int(x_num_ticks_positive) + 1)])
            x_ticks_values = [-i * x_interval for i in range(int(x_num_ticks_negative), -1, -1)]
            x_ticks_values.extend([i * x_interval for i in range(int(x_num_ticks_positive) + 1)])
        for tick_x, tick_value in zip(x_ticks_x, x_ticks_values):
            self._drawables["x_ticks"].append(Drawables.Line(tick_x, plot_y + height - 4, 0, 4, self._plot["fg_color"]))
            self._drawables["x_numbers"].append(
                Drawables.TextBox(x=tick_x, y=plot_y + height, width=20, height=10, text=str(tick_value), size=10,
                                  bg_color=self._plot["bg_color"], fg_color=self._plot["fg_color"],
                                  align_x=Drawables.TextBox.ALIGN_X_CENTER, align_y=Drawables.TextBox.ALIGN_Y_TOP)
            )

        # Figure out y tick marks
        if y_min <= 0 and y_max <= 0:
            y_num_ticks = abs(y_max - y_min) / y_interval
            y_ticks_values = [y_max - i * y_interval for i in range(int(y_num_ticks) + 1)]
        elif y_min >= 0 and y_max >= 0:
            y_num_ticks = abs(y_max - y_min) / y_interval
            y_ticks_values = [y_min + i * y_interval for i in range(int(y_num_ticks) + 1)]
        else:
            y_num_ticks_positive = y_max / y_interval
            y_num_ticks_negative = abs(y_min) / y_interval
            y_ticks_values = [-i * y_interval for i in range(int(y_num_ticks_negative) + 1)]
            y_ticks_values.extend([i * y_interval for i in range(int(y_num_ticks_positive) + 1)])
        y_ticks_values = list(set(y_ticks_values))
        y_ticks_y = [self._datum_position(0, y_tick_value)[1] for y_tick_value in y_ticks_values]
        for tick_y, tick_value in zip(y_ticks_y, y_ticks_values):
            self._drawables["y_ticks"].append(Drawables.Line(plot_x, tick_y, 4, 0, self._plot["fg_color"]))
            self._drawables["y_numbers"].append(
                Drawables.TextBox(x=plot_x, y=tick_y, width=20, height=10, text=str(tick_value), size=10,
                                  bg_color=self._plot["bg_color"], fg_color=self._plot["fg_color"],
                                  align_x=Drawables.TextBox.ALIGN_X_LEFT, align_y=Drawables.TextBox.ALIGN_Y_CENTER)
            )

    def draw(self, surface):
        super().draw(surface)

        if self._drawables["title"] is not None: self._drawables["title"].draw(surface)
        if self._drawables["x_label"] is not None: self._drawables["x_label"].draw(surface)
        if self._drawables["y_label"] is not None: self._drawables["y_label"].draw(surface)

        self._drawables["x_axis"].draw(surface)
        for tick in self._drawables["x_ticks"]:
            tick.draw(surface)
        for number in self._drawables["x_numbers"]:
            number.draw(surface)

        self._drawables["y_axis"].draw(surface)
        for tick in self._drawables["y_ticks"]:
            tick.draw(surface)
        for number in self._drawables["y_numbers"]:
            number.draw(surface)


    def move(self, dx, dy):
        super().move(dx, dy)

        # Need to update values for x_axis_y and y_axis_x
        self._axis_value_calculate()

        # Move all of the drawables
        if self._drawables["title"] is not None: self._drawables["title"].move(dx, dy)
        if self._drawables["x_label"] is not None: self._drawables["x_label"].move(dx, dy)
        if self._drawables["y_label"] is not None: self._drawables["y_label"].move(dx, dy)

        self._drawables["x_axis"].move(dx, dy)
        for tick in self._drawables["x_ticks"]:
            tick.move(dx, dy)
        for number in self._drawables["x_numbers"]:
            number.move(dx, dy)

        self._drawables["y_axis"].move(dx, dy)
        for tick in self._drawables["y_ticks"]:
            tick.move(dx, dy)
        for number in self._drawables["y_numbers"]:
            number.move(dx, dy)

    def exit(self):
        for fifo_source in self.fifo_sources:
            if not (os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)):
                continue

            # Go through all of the fifos writing a command indicating that fifo should close
            with open(fifo_source, "w") as fifo:
                fifo.write(Graph.FIFO_CLOSING_COMMAND)

    def setup_new_data_source(self, fifo_source, new_data_callback):
        assert os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)

        self.fifo_sources = self.fifo_sources.append(fifo_source)

        def _get_new_data():
            try:
                while True:
                    with open(fifo_source, "r") as fifo:
                        while True:
                            data = fifo.read().rstrip("\n")
                            if len(data) == 0:
                                break

                            # Check if the fifo is actually initiating closing
                            if data == Graph.FIFO_CLOSING_COMMAND:
                                return

                            # Data arrived so run the callback with the new data
                            new_data_callback(self, fifo_source, data)
            except:
                print("{} closed!".format(fifo_source))

        # Checking for new data needs to be done in a new thread so the select statement can block
        threading.Thread(target=_get_new_data).start()

    def add_dataset(self, name, x_data, y_data, color=Colors.GREEN):
        assert isinstance(name, str) and name not in self.datasets
        assert isinstance(x_data, list) and all([isinstance(x, int) or isinstance(x, float) for x in x_data])
        assert isinstance(y_data, list) and all([isinstance(y, int) or isinstance(y, float) for y in y_data])
        assert len(x_data) == len(y_data)

        self.datasets[name] = {"color": color, "xs": x_data, "ys":y_data}

    def add_datum(self, dataset_name, x_value, y_value):
        if dataset_name in self.datasets:
            self.datasets[dataset_name]["xs"].append(x_value)
            self.datasets[dataset_name]["ys"].append(y_value)
        else:
            self.datasets[dataset_name] = {"color": Colors.GREEN, "xs": [x_value], "ys": [y_value]}

    def set_title(self, text, distance_from_top_of_graph=10, height=20, font_size=20, bg_color=Colors.BLACK, fg_color=Colors.WHITE):
        self._drawables["title"] = Drawables.TextBox(x=self.width / 2, y=self.y + distance_from_top_of_graph,
                                                     width=self.width, height=height,
                                                     text=text, size=font_size,
                                                     bg_color=bg_color, fg_color=fg_color,
                                                     align_x=Drawables.TextBox.ALIGN_X_CENTER, align_y=Drawables.TextBox.ALIGN_Y_TOP)

    def set_x_label(self, text, distance_from_bottom_of_graph=10, height=15, font_size=15, bg_color=Colors.BLACK, fg_color=Colors.WHITE):
        self._drawables["x_label"] = Drawables.TextBox(x=0, y=self.y + self.height - distance_from_bottom_of_graph - height,
                                                       width=self.width, height=height,
                                                       text=text, size=font_size,
                                                       bg_color=bg_color, fg_color=fg_color,
                                                       align_x=Drawables.TextBox.ALIGN_X_CENTER, align_y=Drawables.TextBox.ALIGN_Y_BOTTOM)

    def set_y_label(self, text, distance_from_left_of_graph=10, height=15, font_size=15, bg_color=Colors.BLACK, fg_color=Colors.WHITE):
        # TODO fix this after the text box rotations are fixed
        # self._drawables["y_label"] = Drawables.TextBox(x=0, y=self.y + self.height - distance_from_bottom_of_graph - height,
        #                                                width=self.width, height=height,
        #                                                text=text, size=font_size,
        #                                                bg_color=bg_color, fg_color=fg_color,
        #                                                align_x=Drawables.TextBox.ALIGN_CENTER, align_y=Drawables.TextBox.ALIGN_BOTTOM)
        pass

    def _datum_position(self, x_value, y_value):
        x = self._axis["y_axis_x"] + x_value * (self._plot["width"] / abs(self._axis["x_max"] - self._axis["x_min"]))
        y = self._axis["x_axis_y"] - y_value * (self._plot["height"] / abs(self._axis["y_max"] - self._axis["y_min"]))

        return int(x), int(y)

    def _axis_value_calculate(self):
        # Local variables
        plot_x = self.x + self._plot["offset_x"]
        plot_y = self.y + self._plot["offset_y"]

        # Figure out the x-axis
        if self._axis["y_min"] <= 0 and self._axis["y_max"] <= 0:
            # Everything is negative (the x axis will show at the very top
            self._axis["x_axis_y"] = plot_y
        elif self._axis["y_min"] >= 0 and self._axis["y_max"] >= 0:
            # Everything is positive (the x axis will show at the very bottom
            self._axis["x_axis_y"] = plot_y + self._plot["height"]
        else:
            # There are both positive and negative values so the x axis will show in the middle of the screen
            self._axis["x_axis_y"] = plot_y + abs(self._axis["y_max"]) / float(self._axis["y_max"] - self._axis["y_min"]) * self._plot["height"]

        # Figure out the y-axis
        if self._axis["x_min"] <= 0 and self._axis["x_max"] <= 0:
            # Everything is negative (the y axis will show at the very top
            self._axis["y_axis_x"] = plot_x + self._plot["width"]
        elif self._axis["x_min"] >= 0 and self._axis["x_max"] >= 0:
            # Everything is positive (the y axis will show at the very bottom
            self._axis["y_axis_x"] = plot_x
        else:
            # There are both positive and negative values so the y axis will show in the middle of the screen
            self._axis["y_axis_x"] = plot_x + abs(self._axis["x_min"]) / float(self._axis["x_max"] - self._axis["x_min"]) * self._plot["width"]


class Scatter(Graph):
    def __init__(self, x, y, width, height):
        super(Scatter, self).__init__(x, y, width, height)

    def draw(self, surface):
        super().draw(surface)

        # Draw datapoints
        for dataset_name in self.datasets:
            color = self.datasets[dataset_name]["color"]
            data_x = self.datasets[dataset_name]["xs"]
            data_y = self.datasets[dataset_name]["ys"]

            for x_value, y_value in zip(data_x, data_y):
                x, y = self._datum_position(x_value, y_value)
                pygame.draw.circle(surface, color, (x, y), 1)


class Line(Graph):
    def __init__(self, x, y, width, height):
        super(Line, self).__init__(x, y, width, height)

    def draw(self, surface):
        super().draw(surface)

        # Draw datapoints
        for dataset_name in self.datasets:
            color = self.datasets[dataset_name]["color"]
            data_x = self.datasets[dataset_name]["xs"]
            data_y = self.datasets[dataset_name]["ys"]

            for x_value, y_value, next_x, next_y in zip(data_x, data_y, data_x[1:], data_y[1:]):
                x, y = self._datum_position(x_value, y_value)
                x2, y2 = self._datum_position(next_x, next_y)
                pygame.draw.line(surface,color,(x,y), (x2,y2))


class Bar(Graph):
    def __init__(self, x, y, width, height):
        super(Bar, self).__init__(x, y, width, height)

    def draw(self, surface):
        super().draw(surface)

        # Draw datapoints
        for dataset_name in self.datasets:
            color = self.datasets[dataset_name]["color"]
            data_x = self.datasets[dataset_name]["xs"]
            data_y = self.datasets[dataset_name]["ys"]

            for x_value, y_value in zip(data_x, data_y):
                x, y = self._datum_position(x_value, y_value)
                rect = (x - 8/2, y, 8, y_value * 11)
                pygame.draw.rect(surface,color,rect)


class Histogram(Graph):
    def __init__(self, x, y, width, height):
        super(Histogram, self).__init__(x, y, width, height)

    def draw(self, surface):
        super().draw(surface)

        # Draw datapoints
        for dataset_name in self.datasets:
            color = self.datasets[dataset_name]["color"]
            data_x = self.datasets[dataset_name]["xs"]
            data_y = self.datasets[dataset_name]["ys"]

            for x_value, y_value in zip(data_x, data_y):
                x, y = self._datum_position(x_value, y_value)
                rect = (x - 12/2, y, 13, y_value * 11)
                pygame.draw.rect(surface,color,rect)