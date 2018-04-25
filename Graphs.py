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
    def __init__(self, x, y, width, height):
        """ Note here that x and y are the top left coordinate, not data_x and data_y """
        super(Graph, self).__init__(x, y, width, height)

        self._title = None
        self._x_label = None
        self._y_label = None
        self.x_bounds = [-10, 10, 2]
        self.y_bounds = [-7, 7, 2]

        self._plot_x = 40
        self._plot_y = 30
        self._plot_width = self.width - self._plot_x
        self._plot_height = self.height - self._plot_y - 30
        self._plot_bg_color = Colors.BLACK
        self._plot_axis_color = Colors.WHITE
        self._x_axis_y = -1
        self._y_axis_x = -1

        self.datasets = dict()

    def draw(self, surface):
        super().draw(surface)

        if self._title is not None: self._title.draw(surface)
        if self._x_label is not None: self._x_label.draw(surface)
        if self._y_label is not None: self._y_label.draw(surface)

        # Draw the x axis
        assert len(self.x_bounds) == 3 and self.x_bounds[1] > self.x_bounds[0] and self.x_bounds[2] > 0
        if self.y_bounds[0] <= 0 and self.y_bounds[1] <= 0:
            # Everything is negative (the x axis will show at the very top
            self._x_axis_y = self._plot_y
        elif self.y_bounds[0] >= 0 and self.y_bounds[1] >= 0:
            # Everything is positive (the x axis will show at the very bottom
            self._x_axis_y = self._plot_y + self._plot_height
        else:
            # There are both positive and negative values so the x axis will show in the middle of the screen
            self._x_axis_y = self._plot_y + abs(self.y_bounds[1]) / float(self.y_bounds[1] - self.y_bounds[0]) * self._plot_height
        pygame.draw.line(surface, self._plot_axis_color, [self._plot_x, self._x_axis_y], [self._plot_x + self._plot_width, self._x_axis_y])

        # Draw the y axis
        assert len(self.y_bounds) == 3 and self.y_bounds[1] > self.y_bounds[0] and self.y_bounds[2] > 0
        if self.x_bounds[0] <= 0 and self.x_bounds[1] <= 0:
            # Everything is negative (the y axis will show at the very top
            self._y_axis_x = self._plot_x + self._plot_width
        elif self.x_bounds[0] >= 0 and self.x_bounds[1] >= 0:
            # Everything is positive (the y axis will show at the very bottom
            self._y_axis_x = self._plot_x
        else:
            # There are both positive and negative values so the y axis will show in the middle of the screen
            self._y_axis_x = self._plot_x + abs(self.x_bounds[0]) / float(self.x_bounds[1] - self.x_bounds[0]) * self._plot_width
        pygame.draw.line(surface, self._plot_axis_color, [self._y_axis_x, self._plot_y], [self._y_axis_x, self._plot_y + self._plot_height])

        # Draw x tick marks
        if self.x_bounds[0] <= 0 and self.x_bounds[1] <= 0:
            x_num_ticks = abs(self.x_bounds[1] - self.x_bounds[0]) / self.x_bounds[2]
            x_tick_distance_apart = self._plot_width / x_num_ticks
            x_ticks_x = [self._plot_x + self._plot_width - i * x_tick_distance_apart for i in range(int(x_num_ticks), -1, -1)]
            x_ticks_values = [self.x_bounds[1] - i * self.x_bounds[2] for i in range(int(x_num_ticks), -1, -1)]
        elif self.x_bounds[0] >= 0 and self.x_bounds[1] >= 0:
            x_num_ticks = abs(self.x_bounds[1] - self.x_bounds[0]) / self.x_bounds[2]
            x_tick_distance_apart = self._plot_width / x_num_ticks
            x_ticks_x = [self._plot_x + i * x_tick_distance_apart for i in range(int(x_num_ticks) + 1)]
            x_ticks_values = [self.x_bounds[0] + i * self.x_bounds[2] for i in range(int(x_num_ticks) + 1)]
        else:
            x_num_ticks_positive = self.x_bounds[1] / self.x_bounds[2]
            x_num_ticks_negative = abs(self.x_bounds[0]) / self.x_bounds[2]
            x_tick_distance_apart = self._plot_width / (x_num_ticks_positive + x_num_ticks_negative)
            x_ticks_x = [self._y_axis_x - i * x_tick_distance_apart for i in range(int(x_num_ticks_negative), -1, -1)]
            x_ticks_x.extend([self._y_axis_x + i * x_tick_distance_apart for i in range(int(x_num_ticks_positive) + 1)])
            x_ticks_values = [-i * self.x_bounds[2] for i in range(int(x_num_ticks_negative), -1, -1)]
            x_ticks_values.extend([i * self.x_bounds[2] for i in range(int(x_num_ticks_positive) + 1)])
        for tick_x, tick_value in zip(x_ticks_x, x_ticks_values):
            pygame.draw.line(surface, self._plot_axis_color, [tick_x, self._plot_y + self._plot_height], [tick_x, self._plot_y + self._plot_height - 4])
            Drawables.TextBox(x=tick_x, y=self._plot_y + self._plot_height,
                              width=20, height=10,
                              text=str(tick_value), size=10,
                              bg_color=self._plot_bg_color, fg_color=self._plot_axis_color,
                              align_x=Drawables.TextBox.ALIGN_CENTER, align_y=Drawables.TextBox.ALIGN_TOP).draw(surface)

        # Draw y tick marks
        if self.y_bounds[0] <= 0 and self.y_bounds[1] <= 0:
            y_num_ticks = abs(self.y_bounds[1] - self.y_bounds[0]) / self.y_bounds[2]
            y_ticks_values = [self.y_bounds[1] - i * self.y_bounds[2] for i in range(int(y_num_ticks) + 1)]
        elif self.y_bounds[0] >= 0 and self.y_bounds[1] >= 0:
            y_num_ticks = abs(self.y_bounds[1] - self.y_bounds[0]) / self.y_bounds[2]
            y_ticks_values = [self.y_bounds[0] + i * self.y_bounds[2] for i in range(int(y_num_ticks) + 1)]
        else:
            y_num_ticks_positive = self.y_bounds[1] / self.y_bounds[2]
            y_num_ticks_negative = abs(self.y_bounds[0]) / self.y_bounds[2]
            y_ticks_values = [-i * self.y_bounds[2] for i in range(int(y_num_ticks_negative) + 1)]
            y_ticks_values.extend([i * self.y_bounds[2] for i in range(int(y_num_ticks_positive) + 1)])
        y_ticks_values = list(set(y_ticks_values))
        y_ticks_y = [self._datum_position(0, y_tick_value)[1] for y_tick_value in y_ticks_values]
        for tick_y, tick_value in zip(y_ticks_y, y_ticks_values):
            pygame.draw.line(surface, self._plot_axis_color, [self._plot_x, tick_y], [self._plot_x + 4, tick_y])
            Drawables.TextBox(x=self._plot_x, y=tick_y,
                              width=20, height=10,
                              text=str(tick_value), size=10,
                              bg_color=self._plot_bg_color, fg_color=self._plot_axis_color,
                              align_x=Drawables.TextBox.ALIGN_LEFT, align_y=Drawables.TextBox.ALIGN_CENTER).draw(surface)

    def setup_new_data_source(self, fifo_source, new_data_callback):
        assert os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)

        def _get_new_data():
            try:
                while True:
                    with open(fifo_source, "r") as fifo:
                        while True:
                            data = fifo.read().rstrip("\n")
                            if len(data) == 0:
                                break
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
        self._title = Drawables.TextBox(x=0, y=self.y + distance_from_top_of_graph,
                                        width=self.width, height=height,
                                        text=text, size=font_size,
                                        bg_color=bg_color, fg_color=fg_color,
                                        align_x=Drawables.TextBox.ALIGN_CENTER, align_y=Drawables.TextBox.ALIGN_TOP)

    def set_x_label(self, text, distance_from_bottom_of_graph=10, height=15, font_size=15, bg_color=Colors.BLACK, fg_color=Colors.WHITE):
        self._x_label = Drawables.TextBox(x=0, y=self.y + self.height - distance_from_bottom_of_graph - height,
                                          width=self.width, height=height,
                                          text=text, size=font_size,
                                          bg_color=bg_color, fg_color=fg_color,
                                          align_x=Drawables.TextBox.ALIGN_CENTER, align_y=Drawables.TextBox.ALIGN_BOTTOM)

    def create_plot(self, plot_x=40, plot_y=30, plot_width=260, plot_height=150, axis_color=Colors.WHITE):
        self._plot_x = plot_x
        self._plot_y = plot_y
        self._plot_width = plot_width
        self._plot_height = plot_height
        self._plot_axis_color = axis_color

    def _datum_position(self, x_value, y_value):
        x = self._y_axis_x + x_value * (self._plot_width / abs(self.x_bounds[1] - self.x_bounds[0]))
        y = self._x_axis_y - y_value * (self._plot_height / abs(self.y_bounds[1] - self.y_bounds[0]))

        return int(x), int(y)


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
