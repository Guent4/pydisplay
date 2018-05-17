import collections
import inspect
import os
import stat
import threading

import pygame

import Colors
import Drawables


class GraphTypes(object):
    """
    All of the graph types supported
    """
    SCATTER = 0
    BAR = 1
    HISTOGRAM = 2
    LINE = 3


class Graph(Drawables.Drawable):
    # This is the restricted word that you should not send to the fifo; when this command is read, the data feed closes
    FIFO_CLOSING_COMMAND = "CLOSING"

    def __init__(self, x, y, width, height):
        """
        Create a graph with an option of multiple datasets.
        :param x: The x coordinate of the top left corner of the graph
        :param y: The y coordinate of the top left corner of the graph
        :param width: The width of the graph
        :param height: The height of the graph
        """
        super(Graph, self).__init__(x, y, width, height)

        self._plot = {"x": 0, "y": 0, "width": 0, "height": 0, "bg_color": None, "fg_color": None}
        self._axis = {"x_min": -10, "x_max": 10, "x_interval": 2, "y_min": -7, "y_max": 7, "y_interval": 2}
        self._drawables = {"title": None, "x_label": None, "y_label": None, "x_axis": None, "y_axis": None,
                           "x_ticks": [], "x_numbers": [], "y_ticks": [], "y_numbers": []}

        self.create_plot()

        self.datasets = collections.OrderedDict()
        self.fifo_sources = []

    def create_plot(self, offset_left=30, offset_right=10, offset_top=30, offset_bottom=30, fg_color=Colors.WHITE):
        """
        Define the plot area (the area that the graph actually exists; does not include the axes labels, titles, tick
        labels).  The defaults are customized for the PiTFT screen with a PageManger switcher bar
        :param offset_left: How much the left side of the plot should be offset from the left side of the graph
        :param offset_right: How much the right side of the plot should be offset from the right side of the graph
        :param offset_top: How much the top of the plot should be offset from the top of the graph
        :param offset_bottom: How much the bottom of the plot should be offset from the bottom of the graph
        :param fg_color: The color of the plot (this would define the axes colors and default label colors
        :return: None
        """
        self._plot["offset_x"] = offset_left
        self._plot["offset_y"] = offset_top
        self._plot["width"] = self.width - offset_right - offset_left
        self._plot["height"] = self.height - offset_top - offset_bottom
        self._plot["fg_color"] = fg_color

        # Regenerate the stuff
        self.set_bounds()

    def set_bounds(self, x_min=None, x_max=None, x_interval=None, y_min=None, y_max=None, y_interval=None):
        """
        Set bounds for the two axes and the tick interval.  This does a lot of the calculations and creates the
        Drawables that are needed for the plot (axes, ticks, tick labels).  Call this method again when any of the
        bounds change.
        :param x_min: Minimum x value
        :param x_max: Maximum x value (must be greater than x_min)
        :param x_interval: Amount between tick marks on x axis (must be greater than 0)
        :param y_min: Minimum y value
        :param y_max: Maximum y value (must be greater than y_min)
        :param y_interval: Amount between tick marks on y axis (must be greater than 0)
        :return: None
        """
        if x_min is None: x_min = self._axis["x_min"]
        if x_max is None: x_max = self._axis["x_max"]
        if x_interval is None: x_interval = self._axis["x_interval"]
        if y_min is None: y_min = self._axis["y_min"]
        if y_max is None: y_max = self._axis["y_max"]
        if y_interval is None: y_interval = self._axis["y_interval"]

        # Make sure the inputs are reasonable
        assert x_max > x_min and x_interval > 0, (x_min, x_max, x_interval)
        assert y_max > y_min and y_interval > 0, (y_min, y_max, y_interval)

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
                Drawables.Text(x=tick_x, y=plot_y + height + 2, text=str(tick_value), font_size=12, fg_color=self._plot["fg_color"],
                               align_x=Drawables.Text.ALIGN_X_CENTER, align_y=Drawables.Text.ALIGN_Y_TOP)
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
                Drawables.Text(x=plot_x - 2, y=tick_y, text=str(tick_value), font_size=12, fg_color=self._plot["fg_color"],
                               align_x=Drawables.Text.ALIGN_X_RIGHT, align_y=Drawables.Text.ALIGN_Y_CENTER)
            )

    def draw(self, surface):
        """
        Draw the graph.  This graph has a list of its own drawables so it needs to draw those too
        :param surface: The surface onto which the chart should be drawn
        :return: None
        """
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
        """
        Overrides the Drawable move function.  This graph has a bunch of its own drawables so it needs to move those too
        :param dx: The amount things should move in the x direction (positive or negative float)
        :param dy: The amount things should move in the y direction (positive or negative float)
        :return: None
        """
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
        """
        Exit out of this graph. This involves closing the fifo data feed
        :return: None
        """
        for fifo_source in self.fifo_sources:
            if not (os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)):
                continue

            # Go through all of the fifos writing a command indicating that fifo should close
            with open(fifo_source, "w") as fifo:
                fifo.write(Graph.FIFO_CLOSING_COMMAND)

    def setup_new_data_source(self, fifo_source, new_data_callback):
        """
        Set up a new data_source/data feed.  This new source must be a fifo from which this function will automatically
        and continuously try to read from in a new thread until this Graph is exited.  When there is a new data point,
        the new_data_callback function will be triggered and you can define what to do in that (though you probably will
        want to call the add_datum function)
        :param fifo_source: The filepath (relative or absolute) to the data source
        :param new_data_callback: The callback function that will process the data read from the fifo
        :return: None
        """
        assert os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)

        self.fifo_sources.append(fifo_source)

        def _get_new_data():
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

        # Checking for new data needs to be done in a new thread so the select statement can block
        threading.Thread(target=_get_new_data).start()

    def add_dataset(self, name, x_data, y_data, color=Colors.GREEN):
        """
        Add a new dataset with its own custom color
        :param name: Name of the dataset (must be unique)
        :param x_data: List of x data values
        :param y_data: List of y data values
        :param color: Color scheme for this dataset
        :return: None
        """
        assert isinstance(name, str) and name not in self.datasets
        assert isinstance(x_data, list) and all([isinstance(x, int) or isinstance(x, float) for x in x_data])
        assert isinstance(y_data, list) and all([isinstance(y, int) or isinstance(y, float) for y in y_data])
        assert len(x_data) == len(y_data)

        self.datasets[name] = {"color": color, "xs": x_data, "ys":y_data}

    def remove_dataset(self, name):
        """
        Remove a dataset.
        :param name: Name of the dataset
        :return: True if there was a dataset with that name and False otherwise
        """
        if name in self.datasets:
            del self.datasets[name]
            return True
        else:
            return False

    def add_datum(self, dataset_name, x_value, y_value):
        """
        Add a new data point.
        :param dataset_name: The dataset this data point belongs to
        :param x_value: The x value
        :param y_value: The y value
        :return: None
        """
        if dataset_name in self.datasets:
            self.datasets[dataset_name]["xs"].append(x_value)
            self.datasets[dataset_name]["ys"].append(y_value)
        else:
            self.datasets[dataset_name] = {"color": Colors.GREEN, "xs": [x_value], "ys": [y_value]}

    def set_title(self, text, distance_from_top_of_graph=5, font_size=20, fg_color=None):
        """
        Set the title of the graph.
        :param text: The text to display
        :param distance_from_top_of_graph: Distance top of text is from the top of graph
        :param font_size: Font size
        :param fg_color: Font color
        :return: None
        """
        fg_color = self._plot["fg_color"] if fg_color is None else fg_color
        self._drawables["title"] = Drawables.Text(x=self.width / 2, y=self.y + distance_from_top_of_graph,
                                                  text=text, font_size=font_size, fg_color=fg_color,
                                                  align_x=Drawables.Text.ALIGN_X_CENTER, align_y=Drawables.Text.ALIGN_Y_TOP)

    def set_x_label(self, text, distance_from_bottom_of_graph=5, font_size=15, fg_color=None):
        """
        Set the x label (this will be centered at the bottom of the chart)
        :param text: Text to display
        :param distance_from_bottom_of_graph: Distance bottom of text is from bottom of graph
        :param font_size: Font size
        :param fg_color: Font color
        :return: None
        """
        x = self.x + self._plot["offset_x"] + self._plot["width"] / 2
        y = self.y + self.height - distance_from_bottom_of_graph
        fg_color = self._plot["fg_color"] if fg_color is None else fg_color
        self._drawables["x_label"] = Drawables.Text(x=x, y=y, text=text, font_size=font_size, fg_color=fg_color,
                                                    align_x=Drawables.Text.ALIGN_X_CENTER, align_y=Drawables.Text.ALIGN_Y_BOTTOM)

    def set_y_label(self, text, distance_from_left_of_graph=5, font_size=15, fg_color=None):
        """
        Set the y label (this will be rotated and centered on the left of the chart)
        :param text: Text to display
        :param distance_from_left_of_graph: Distance top of text (upward direction of letters) is from left of graph
        :param font_size: Font size
        :param fg_color: Font color
        :return: None
        """
        x = self.x + distance_from_left_of_graph
        y = self.y + self._plot["offset_y"] + self._plot["height"] / 2
        fg_color = self._plot["fg_color"] if fg_color is None else fg_color
        self._drawables["y_label"] = Drawables.Text(x=x, y=y, text=text, font_size=font_size, fg_color=fg_color,
                                                    align_x=Drawables.Text.ALIGN_X_LEFT, align_y=Drawables.Text.ALIGN_Y_CENTER, rotate=90)

    def _datum_position(self, x_value, y_value):
        """
        Internal calculation.  Given a x value and a y value, calculate the position on the graph to display the point
        :param x_value: x value of a data point
        :param y_value: y value of a data point
        :return: Tuple of x, y coordinate
        """
        assert isinstance(x_value, int) or isinstance(x_value, float)
        assert isinstance(y_value, int) or isinstance(y_value, float)
        x = self._axis["y_axis_x"] + x_value * (self._plot["width"] / abs(self._axis["x_max"] - self._axis["x_min"]))
        y = self._axis["x_axis_y"] - y_value * (self._plot["height"] / abs(self._axis["y_max"] - self._axis["y_min"]))

        if x < self.x + self._plot["offset_x"] or x > self.x + self._plot["offset_x"] + self._plot["width"] or \
                y < self.y + self._plot["offset_y"] or y > self.y + self._plot["offset_y"] + self._plot["height"]:
            return None, None

        return int(x), int(y)

    def _axis_value_calculate(self):
        """
        Internal calculation for getting some axes values.
        :return: None
        """
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
    def __init__(self, x, y, width, height, connect_points=False):
        """
        Create a scatter plot.  Note that if connect_points=True and if a data point is not within the x bounds or y
        bounds, the line to and from this point will not be drawn.
        :param x: The x coordinate of the top left corner of the graph
        :param y: The y coordinate of the top left corner of the graph
        :param width: The width of the graph
        :param height: The height of the graph
        :param connect_points: Should lines be drawn between points?
        """
        super(Scatter, self).__init__(x, y, width, height)

        assert isinstance(connect_points, bool)

        self._connect_points = connect_points

    def draw(self, surface):
        """
        Customized draw function.
        :param surface: The surface onto which the graph should be drawn
        :return: None
        """
        super().draw(surface)

        # Draw datapoints
        for dataset_name in self.datasets:
            color = self.datasets[dataset_name]["color"]
            data_x = self.datasets[dataset_name]["xs"]
            data_y = self.datasets[dataset_name]["ys"]

            for i, (x_value, y_value, next_x, next_y) in enumerate(zip(data_x, data_y, data_x[1:], data_y[1:])):
                x, y = self._datum_position(x_value, y_value)
                x2, y2 = self._datum_position(next_x, next_y)

                if x is not None and y is not None and x2 is not None and y2 is not None:
                    pygame.draw.line(surface,color,(x,y), (x2,y2))

                if i == 0 and x is not None and y is not None:
                    pygame.draw.circle(surface, color, (x, y), 1)
                if x2 is not None and y2 is not None:
                    pygame.draw.circle(surface, color, (x2, y2), 1)


class Line(Graph):
    def __init__(self, x, y, width, height):
        """
        Create a scatter plot.  Note that if a data point is not within the x bounds or y bounds, the line to and from
        this point will not be drawn.
        :param x: The x coordinate of the top left corner of the graph
        :param y: The y coordinate of the top left corner of the graph
        :param width: The width of the graph
        :param height: The height of the graph
        """
        super(Line, self).__init__(x, y, width, height)

    def draw(self, surface):
        """
        Customized draw function.
        :param surface: The surface onto which the graph should be drawn
        :return: None
        """
        super().draw(surface)

        # Draw datapoints
        for dataset_name in self.datasets:
            color = self.datasets[dataset_name]["color"]
            data_x = self.datasets[dataset_name]["xs"]
            data_y = self.datasets[dataset_name]["ys"]

            for x_value, y_value, next_x, next_y in zip(data_x, data_y, data_x[1:], data_y[1:]):
                x, y = self._datum_position(x_value, y_value)
                x2, y2 = self._datum_position(next_x, next_y)
                if x is not None and y is not None and x2 is not None and y2 is not None:
                    pygame.draw.line(surface,color,(x,y), (x2,y2))

    def generate_ys_from_function(self, func, num_xs=100):
        """
        Given a function that takes in a single x value and will return the corresponding y value, this function will
        generate a list of x and y values to fill the graph.
        :param func: A function that takes in a single x value and will return the corresponding y value
        :param num_xs: Number of xs and ys to return; note that on the PiTFT the screen has 320 pixels total in the
                    horizontal direction and this graph takes up around 200ish of those pixels, so 100 is reasonable)
        :return: A tuple of lists: (xs, ys)
        """
        assert callable(func) and len(inspect.getfullargspec(func).args) == 1
        assert isinstance(num_xs, int) and num_xs > 0

        x_interval = (self._axis["x_max"] - self._axis["x_min"]) / num_xs

        xs = []
        ys = []
        x = self._axis["x_min"]
        while x <= self._axis["x_max"]:
            xs.append(x)
            ys.append(func(x))
            x += x_interval

        return xs, ys


class Bar(Graph):
    def __init__(self, x, y, width, height, num_columns, column_width=0.8):
        """
        Create a bar graph.
        :param x: The x coordinate of the top left corner of the graph
        :param y: The y coordinate of the top left corner of the graph
        :param width: The width of the graph
        :param height: The height of the graph
        :param num_columns: Number of columns that will be displayed (cannot be changed later)
        :param column_width: Each bar gets a maximum width; 0.8 means each bar takes up 80% of that maximum width; must
                    be > 0 and <= 1.0
        """
        super(Graph, self).__init__(x, y, width, height)

        assert num_columns is None or (isinstance(num_columns, int) and num_columns > 0, num_columns)
        assert column_width is None or (isinstance(column_width, float) and 0 < column_width <= 1)

        self._plot = {"x": 0, "y": 0, "width": 0, "height": 0, "bg_color": None, "fg_color": None}
        self._axis = {"x_min": 0, "x_max": num_columns, "x_interval": 1, "y_min": -7, "y_max": 7, "y_interval": 2}
        self._drawables = {"title": None, "x_label": None, "y_label": None, "x_axis": None, "y_axis": None,
                           "x_ticks": [], "x_numbers": [], "y_ticks": [], "y_numbers": []}
        self._bars = {"num_columns": num_columns, "column_width": column_width}
        self._can_set_bars = True

        self.create_plot()

        self.datasets = collections.OrderedDict()
        self.fifo_sources = []

    def set_bounds(self, x_min=None, x_max=None, x_interval=None, y_min=None, y_max=None, y_interval=None):
        """
        Refer to the documentation for Graph.set_bounds.  Note that for Bar graphs, x_min, x_max, and x_interval cannot
        be manually changed.
        :param x_min: Not used!
        :param x_max: Not used!
        :param x_interval: Not used!
        :param y_min: Minimum y value
        :param y_max: Maximum y value (must be greater than y_min)
        :param y_interval: Amount between tick marks on y axis (must be greater than 0)
        :return: None
        """
        super(Bar, self).set_bounds(y_min=y_min, y_max=y_max, y_interval=y_interval)

    def add_dataset(self, name, x_data, y_data, color=Colors.GREEN):
        """
        Add a new dataset with its own custom color
        :param name: Name of the dataset (must be unique)
        :param x_data: Not necessary!
        :param y_data: List of y data values (must have same length as the set number of columns
        :param color: Color scheme for this dataset
        :return: None
        """
        assert isinstance(name, str) and name not in self.datasets
        assert isinstance(y_data, list) and all([isinstance(y, int) or isinstance(y, float) for y in y_data])
        assert len(y_data) == self._bars["num_columns"]

        self.datasets[name] = {"color": color, "ys": y_data}

        self._can_set_bars = False


    def draw(self, surface):
        """
        Customized draw function.
        :param surface: The surface onto which the graph should be drawn
        :return: None
        """
        super().draw(surface)

        # Draw datapoints
        one_side = (self._plot["width"] / abs(self._axis["x_max"] - self._axis["x_min"])) * self._bars["column_width"] * 0.5
        for dataset_name in self.datasets:
            color = self.datasets[dataset_name]["color"]
            data_x = list(map(lambda x: x + 0.5, range(self._bars["num_columns"])))
            data_y = self.datasets[dataset_name]["ys"]

            for x_value, y_value in zip(data_x, data_y):
                x, y = self._datum_position(x_value, max(min(y_value, self._axis["y_max"]), self._axis["y_min"]))
                rect = (x - one_side, self._axis["x_axis_y"], one_side * 2, y - self._axis["x_axis_y"])
                pygame.draw.rect(surface, color, rect)


class Histogram(Graph):
    def __init__(self, x, y, width, height):
        """
        Create a histogram plot.
        :param x: The x coordinate of the top left corner of the graph
        :param y: The y coordinate of the top left corner of the graph
        :param width: The width of the graph
        :param height: The height of the graph
        """
        super(Histogram, self).__init__(x, y, width, height)

    def draw(self, surface):
        """
        Customized draw function.
        :param surface: The surface onto which the graph should be drawn
        :return: None
        """
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