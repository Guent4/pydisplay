import collections
import inspect
import os
import re

import select
import stat
import threading

import pygame

import Colors
import Drawables


class Chart(Drawables.Drawable):
    FIFO_CLOSING_COMMAND = "CLOSING"

    def __init__(self, x, y, width, height, bg_color=Colors.BLACK, fg_color=Colors.WHITE, cell_heights=20):
        """
        Note here that x and y are the top left coordinate of the entire Graph, not data_x and data_y or where the
        the plot is within the graph
        """
        super(Chart, self).__init__(x, y, width, height)
        self._bg_color = bg_color
        self._fg_color = fg_color
        self._cell_heights = cell_heights

        self._drawables = {"horizontal": [], "vertical": [], "headers": [], "data": []}

        self.datasets = collections.OrderedDict()
        self.fifo_sources = []

    def draw(self, surface):
        super().draw(surface)

        for line in self._drawables["horizontal"]:
            line.draw(surface)
        for line in self._drawables["vertical"]:
            line.draw(surface)
        for text in self._drawables["headers"]:
            text.draw(surface)
        for text in self._drawables["data"]:
            text.draw(surface)

    def move(self, dx, dy):
        super().move(dx, dy)

        for line in self._drawables["horizontal"]:
            line.move(dx, dy)
        for line in self._drawables["vertical"]:
            line.move(dx, dy)
        for text in self._drawables["headers"]:
            text.move(dx, dy)
        for text in self._drawables["data"]:
            text.move(dx, dy)

    def exit(self):
        for fifo_source in self.fifo_sources:
            if not (os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)):
                continue

            # Go through all of the fifos writing a command indicating that fifo should close
            with open(fifo_source, "w") as fifo:
                fifo.write(Chart.FIFO_CLOSING_COMMAND)

    def setup_new_data_source(self, fifo_source, new_data_callback):
        assert os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)

        print(fifo_source)
        self.fifo_sources.append(fifo_source)
        print(self.fifo_sources)

        def _get_new_data():
            while True:
                with open(fifo_source, "r") as fifo:
                    print("opened")
                    while True:
                        data = fifo.read().rstrip("\n")
                        if len(data) == 0:
                            break

                        # Check if the fifo is actually initiating closing
                        if data == Chart.FIFO_CLOSING_COMMAND:
                            return

                        # Data arrived so run the callback with the new data
                        new_data_callback(self, fifo_source, data)

        # Checking for new data needs to be done in a new thread so the select statement can block
        threading.Thread(target=_get_new_data).start()

    def add_dataset(self, name, data, bg_color=Colors.BLACK, fg_color=Colors.WHITE, formatting="{}", cell_width=100,
                    header_align_x=Drawables.Text.ALIGN_X_CENTER, data_align_x=Drawables.Text.ALIGN_X_LEFT):
        assert isinstance(name, str) and name not in self.datasets
        assert isinstance(data, list)
        assert Colors.is_color(bg_color) and Colors.is_color(fg_color)
        assert isinstance(formatting, str) and re.match(r"^[^{]*{[^{]*}[^{]*$", formatting)
        assert header_align_x in (Drawables.Text.ALIGN_X_LEFT, Drawables.Text.ALIGN_X_CENTER, Drawables.Text.ALIGN_X_RIGHT)
        assert data_align_x in (Drawables.Text.ALIGN_X_LEFT, Drawables.Text.ALIGN_X_CENTER, Drawables.Text.ALIGN_X_RIGHT)
        assert sum([dataset["cell_width"] for dataset in self.datasets.values()]) + cell_width <= self.width
        assert all([len(data) == len(dataset["data"]) for dataset in self.datasets.values()])

        # To pad left and right if alignments are selected to be to left and right
        pad = 4
        data_font_size = 12

        # Account for new vertical line
        vertical_line_height = (len(data) + 1) * self._cell_heights
        if len(self._drawables["vertical"]) == 0:
            self._drawables["vertical"].append(Drawables.Line(self.x, self.y, 0, vertical_line_height, color=self._fg_color))
        column_x = self.x + sum([dataset["cell_width"] for dataset in self.datasets.values()])
        self._drawables["vertical"].append(Drawables.Line(column_x + cell_width, self.y, 0, vertical_line_height, color=self._fg_color))

        # Deal with all horizontal lines
        if len(self._drawables["horizontal"]) == 0:
            for i in range(len(data) + 2):
                horizontal = Drawables.Line(self.x, self.y + i * self._cell_heights, column_x + cell_width, 0, color=self._fg_color)
                self._drawables["horizontal"].append(horizontal)
        else:
            for horizontal in self._drawables["horizontal"]:
                horizontal.width = column_x + cell_width

        # Deal with headers
        x_values = {
            Drawables.Text.ALIGN_X_LEFT: column_x + pad,
            Drawables.Text.ALIGN_X_CENTER: column_x + cell_width / 2,
            Drawables.Text.ALIGN_X_RIGHT: column_x + cell_width - pad
        }
        self._drawables["headers"].append(Drawables.Text(x_values[header_align_x], self.y + self._cell_heights / 2,
                                                         name, font_size=15, fg_color=fg_color,
                                                         align_x=header_align_x, align_y=Drawables.Text.ALIGN_Y_CENTER))

        # Deal with data
        for i, datum in enumerate(data):
            self._drawables["data"].append(Drawables.Text(x_values[data_align_x], self.y + (i + 1.5) * self._cell_heights,
                                                          formatting.format(datum), font_size=data_font_size, fg_color=fg_color,
                                                          align_x=data_align_x, align_y=Drawables.Text.ALIGN_Y_CENTER))

        # Store the input values
        self.datasets[name] = {"data": data, "bg_color": bg_color, "fg_color": fg_color, "formatting": formatting,
                               "cell_width": cell_width, "data_font_size": data_font_size, "pad": pad,
                               "header_align_x": header_align_x, "data_align_x": data_align_x}

    def add_datum(self, values):
        assert isinstance(values, dict) and values.keys() == self.datasets.keys()

        # Extend old vertical lines
        for vertical in self._drawables["vertical"]:
            vertical.height += self._cell_heights

        # Add extra horizontal line
        horizontal_y = self.y + (max([len(dataset["data"]) for dataset in self.datasets.values()]) + 2) * self._cell_heights
        horizontal_width = sum([dataset["cell_width"] for dataset in self.datasets.values()])
        self._drawables["horizontal"].append(Drawables.Line(self.x, horizontal_y, horizontal_width, 0, color=self._fg_color))

        # Add text for the new row's data
        column_x = self.x
        for i, (dataset_name, value) in enumerate(values.items()):
            dataset = self.datasets[dataset_name]
            x_values = {
                Drawables.Text.ALIGN_X_LEFT: column_x + dataset["pad"],
                Drawables.Text.ALIGN_X_CENTER: column_x + dataset["cell_width"] / 2,
                Drawables.Text.ALIGN_X_RIGHT: column_x + dataset["cell_width"] - dataset["pad"]
            }
            y_value = self.y + (len(dataset["data"]) + 1.5) * self._cell_heights

            dataset["data"].append(value)
            data_text = Drawables.Text(x_values[dataset["data_align_x"]], y_value, dataset["formatting"].format(value),
                                       dataset["data_font_size"], fg_color=dataset["fg_color"],
                                       align_x=dataset["data_align_x"], align_y=Drawables.Text.ALIGN_Y_CENTER)
            self._drawables["data"].append(data_text)

            column_x += dataset["cell_width"]


class Sorting(object):
    FIFO = 0
    LIFO = 1
    ASCENDING = 2
    DESCENDING = 3
    OTHER = -1

    def __init__(self, policy, column_name):
        pass