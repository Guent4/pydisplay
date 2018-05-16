import collections
import functools
import inspect
import os
import re
import stat
import threading

import Colors
import Drawables


class Sorting(object):
    """
    The types of sorting possible.  FIFO means that most recent is at the bottom.  LIFO means that most recent is at the
    top.  OTHER means that you are providing your own compare function (which must take in 2 arguments, return -1, 0, or
    1 accordingly).
    """
    FIFO = 0
    LIFO = 1
    ASCENDING = 2
    DESCENDING = 3
    OTHER = -1


class Chart(Drawables.Drawable):
    # This is the restricted word that you should not send to the fifo; when this command is read, the data feed closes
    FIFO_CLOSING_COMMAND = "CLOSING"

    def __init__(self, x, y, width, height, fg_color=Colors.WHITE, cell_heights=20):
        """
        Create a chart with columns of data (each column is called a dataset).  The first row is the headers of the
        columns and everything below are data points.  All of the columns must have the same number of data points.
        :param x: The x coordinate of the top left corner of the chart
        :param y: The y coordinate of the top left corner of the chart
        :param width: The width of the chart (the sum of column widths cannot exceed this)
        :param height: The height of the chart (not directly used)
        :param fg_color: The default foreground color of the chart(lines and text will by default be this color)
        :param cell_heights: The height of each cell in the chart
        """
        super(Chart, self).__init__(x, y, width, height)
        self._fg_color = fg_color
        self._cell_heights = cell_heights

        self._drawables = {"horizontal": [], "vertical": [], "headers": [], "data": {}}

        self.datasets = collections.OrderedDict()
        self.fifo_sources = []
        self._can_add_more_datasets = True

        self._sorting_scheme = {"sorting_scheme": Sorting.FIFO, "dataset_name": None, "other_compare_func": None}

    def draw(self, surface):
        """
        Draw the chart.  This chart has a list of its own drawables so it needs to draw those too
        :param surface: The surface onto which the chart should be drawn
        :return: None
        """
        super().draw(surface)

        for line in self._drawables["horizontal"]:
            line.draw(surface)
        for line in self._drawables["vertical"]:
            line.draw(surface)
        for text in self._drawables["headers"]:
            text.draw(surface)
        for dataset_texts in self._drawables["data"].values():
            for text in dataset_texts:
                text.draw(surface)

    def move(self, dx, dy):
        """
        Overrides the Drawable move function.  This chart has a list of its own drawables so it needs to move those too
        :param dx: The amount things should move in the x direction (positive or negative float)
        :param dy: The amount things should move in the y direction (positive or negative float)
        :return: None
        """
        super().move(dx, dy)

        for line in self._drawables["horizontal"]:
            line.move(dx, dy)
        for line in self._drawables["vertical"]:
            line.move(dx, dy)
        for text in self._drawables["headers"]:
            text.move(dx, dy)
        for dataset_texts in self._drawables["data"].values():
            for text in dataset_texts:
                text.move(dx, dy)

    def exit(self):
        """
        Exit out of this chart. This involves closing the fifo data feed
        :return: None
        """
        for fifo_source in self.fifo_sources:
            if not (os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)):
                continue

            # Go through all of the fifos writing a command indicating that fifo should close
            with open(fifo_source, "w") as fifo:
                fifo.write(Chart.FIFO_CLOSING_COMMAND)

    def setup_new_data_source(self, fifo_source, new_data_callback):
        """
        Set up a new data_source/data feed.  This new source must be a fifo from which this function will automatically
        and continuously try to read from in a new thread until this Chart is exited.  When there is a new data point,
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
                        if data == Chart.FIFO_CLOSING_COMMAND:
                            return

                        # Data arrived so run the callback with the new data
                        new_data_callback(self, fifo_source, data)

        # Checking for new data needs to be done in a new thread so the select statement can block
        threading.Thread(target=_get_new_data).start()

    def add_dataset(self, name, data, font_color=Colors.WHITE, formatting="{}", cell_width=100,
                    header_align_x=Drawables.Text.ALIGN_X_CENTER, data_align_x=Drawables.Text.ALIGN_X_LEFT):
        """
        Add a new dataset (or column) to the chart.  Note that this funciton cannot be called after the add_datum
        function has been called.
        :param name: Name of the column (will show up as a header and must be unique)
        :param data: A list of data points for this column (all columns must have the same number of datapoints.
        :param font_color: Color of the font of the text in this column
        :param formatting: If you wat custom formatting; for example, if you want percent signs, you can pass in "{}%"
        :param cell_width: Width of the cells in this column
        :param header_align_x: How should the header be aligned (pick from Drawables.Text x align options)
        :param data_align_x: How should the data values be aligned (pick from Drawables.Text x align options)
        :return: None
        """
        assert isinstance(name, str) and name not in self.datasets
        assert isinstance(data, list)
        assert Colors.is_color(font_color)
        assert isinstance(formatting, str) and re.match(r"^[^{]*{[^{]*}[^{]*$", formatting)
        assert header_align_x in (Drawables.Text.ALIGN_X_LEFT, Drawables.Text.ALIGN_X_CENTER, Drawables.Text.ALIGN_X_RIGHT)
        assert data_align_x in (Drawables.Text.ALIGN_X_LEFT, Drawables.Text.ALIGN_X_CENTER, Drawables.Text.ALIGN_X_RIGHT)
        assert sum([dataset["cell_width"] for dataset in self.datasets.values()]) + cell_width <= self.width
        assert all([len(data) == len(dataset["data"]) for dataset in self.datasets.values()])
        assert self._can_add_more_datasets

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
                                                         name, font_size=15, fg_color=font_color,
                                                         align_x=header_align_x, align_y=Drawables.Text.ALIGN_Y_CENTER))

        # Deal with data
        data_drawables = []
        for i, datum in enumerate(data):
            data_drawables.append(Drawables.Text(x_values[data_align_x], self.y + (i + 1.5) * self._cell_heights,
                                                 formatting.format(datum), font_size=data_font_size, fg_color=font_color,
                                                 align_x=data_align_x, align_y=Drawables.Text.ALIGN_Y_CENTER))
        self._drawables["data"][name] = data_drawables

        # Store the input values
        self.datasets[name] = {"data": data, "insertion_order": range(len(data)), "font_color": font_color,
                               "formatting": formatting, "cell_width": cell_width, "data_font_size": data_font_size,
                               "pad": pad, "header_align_x": header_align_x, "data_align_x": data_align_x}

        self._sort()

    def add_datum(self, values):
        """
        Add new datum.  This will automatically add the datum to the chart and draw a new row for this.  After the data
        point is added, the chart is resorted as desired (set the sorting scheme using add_sorting_scheme; default is
        FIFO so new data appears at the bottom).
        :param values: A dictionary of values (must have the same keys as the names of the columns and must have a
                    key/value pair for every column.
        :return: None
        """
        assert isinstance(values, dict) and values.keys() == self.datasets.keys()

        # Mark that you can't add more datasets
        self._can_add_more_datasets = False

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
            dataset["insertion_order"].append(max(dataset["insertion_order"]) + 1)
            data_text = Drawables.Text(x_values[dataset["data_align_x"]], y_value, dataset["formatting"].format(value),
                                       dataset["data_font_size"], fg_color=dataset["fg_color"],
                                       align_x=dataset["data_align_x"], align_y=Drawables.Text.ALIGN_Y_CENTER)
            self._drawables["data"][dataset_name].append(data_text)

            column_x += dataset["cell_width"]

        # Since new datapoint, sort if not FIFO
        if self._sorting_scheme != Sorting.FIFO:
            self._sort()

    def add_sorting_scheme(self, sorting_scheme, dataset_name=None, other_compare_func=None):
        """
        If a custom sorting scheme is desired for this chart; default is FIFO.  Refer to the Chart.Sorting class for the
        options.  Chart is automatically resorted after this is specified.
        :param sorting_scheme: One of the options in Chart.Sorting.
        :param dataset_name: Only needed for Sorting.ASCENDING, Sorting.DESCENDING, and Sorting.OTHER; this defines the
                    column to actually do the sorting on.  Pass in the name of the column.
        :param other_compare_func: Only needed for Sorting.OTHER; this is where you define your own custom compare
                    function.  The column (which you specify via dataset_name) will be sorted via this compare function.
        :return: None
        """
        assert sorting_scheme in [Sorting.FIFO, Sorting.LIFO, Sorting.ASCENDING, Sorting.DESCENDING, Sorting.OTHER]
        if sorting_scheme == Sorting.FIFO or sorting_scheme == Sorting.LIFO:
            assert dataset_name is None and other_compare_func is None
        elif sorting_scheme == Sorting.ASCENDING or sorting_scheme == Sorting.DESCENDING:
            assert dataset_name is not None and dataset_name in self.datasets and other_compare_func is None
        else:
            assert dataset_name is not None and dataset_name in self.datasets and other_compare_func is not None
            assert callable(other_compare_func) and len(inspect.getfullargspec(other_compare_func).args) == 2

        self._sorting_scheme["sorting_scheme"] = sorting_scheme
        self._sorting_scheme["dataset_name"] = dataset_name
        self._sorting_scheme["other_compare_func"] = other_compare_func

        # Sort the rows
        self._sort()

    def _sort(self):
        """
        Internal function that sorts the datasets accordingly.
        :return: None
        """
        if self._sorting_scheme["sorting_scheme"] == Sorting.FIFO:
            for dataset_name, dataset in self.datasets.items():
                zipped = zip(dataset["data"], dataset["insertion_order"])
                zipped = sorted(zipped, key=lambda x: x[1])
                dataset["data"] = [x[0] for x in zipped]
                dataset["insertion_order"] = [x[1] for x in zipped]
        elif self._sorting_scheme["sorting_scheme"] == Sorting.LIFO:
            for dataset_name, dataset in self.datasets.items():
                zipped = zip(dataset["data"], dataset["insertion_order"])
                zipped = sorted(zipped, key=lambda x: x[1], reverse=True)
                dataset["data"] = [x[0] for x in zipped]
                dataset["insertion_order"] = [x[1] for x in zipped]
        elif self._sorting_scheme["sorting_scheme"] == Sorting.ASCENDING:
            dataset_name_sorting = self._sorting_scheme["dataset_name"]
            dataset_sorting = self.datasets[dataset_name_sorting]
            zipped_sorting = zip(dataset_sorting["data"], dataset_sorting["insertion_order"])
            zipped_sorting = sorted(zipped_sorting, key=lambda x: x[0])
            insertion_order_sorting = [x[1] for x in zipped_sorting]
            for dataset_name, dataset in self.datasets.items():
                zipped = zip(dataset["data"], dataset["insertion_order"])
                zipped = sorted(zipped, key=lambda x: x[1])
                dataset["data"] = [zipped[i][0] for i in insertion_order_sorting]
                dataset["insertion_order"] = insertion_order_sorting
        elif self._sorting_scheme["sorting_scheme"] == Sorting.DESCENDING:
            dataset_name_sorting = self._sorting_scheme["dataset_name"]
            dataset_sorting = self.datasets[dataset_name_sorting]
            zipped_sorting = zip(dataset_sorting["data"], dataset_sorting["insertion_order"])
            zipped_sorting = sorted(zipped_sorting, key=lambda x: x[0], reverse=True)
            insertion_order_sorting = [x[1] for x in zipped_sorting]
            for dataset_name, dataset in self.datasets.items():
                zipped = zip(dataset["data"], dataset["insertion_order"])
                zipped = sorted(zipped, key=lambda x: x[1])
                dataset["data"] = [zipped[i][0] for i in insertion_order_sorting]
                dataset["insertion_order"] = insertion_order_sorting
        elif self._sorting_scheme["sorting_scheme"] == Sorting.OTHER:
            dataset_name_sorting = self._sorting_scheme["dataset_name"]
            dataset_sorting = self.datasets[dataset_name_sorting]
            zipped_sorting = zip(dataset_sorting["data"], dataset_sorting["insertion_order"])
            zipped_sorting = sorted(zipped_sorting, key=functools.cmp_to_key(self._sorting_scheme["other_compare_func"]))
            insertion_order_sorting = [x[1] for x in zipped_sorting]
            for dataset_name, dataset in self.datasets.items():
                zipped = zip(dataset["data"], dataset["insertion_order"])
                zipped = sorted(zipped, key=lambda x: x[1])
                dataset["data"] = [zipped[i][0] for i in insertion_order_sorting]
                dataset["insertion_order"] = insertion_order_sorting
        else:
            raise ValueError

        # Update the actual items in the chart
        for dataset_name, dataset in self.datasets.items():
            texts = self._drawables["data"][dataset_name]
            for datum, text in zip(dataset["data"], texts):
                text.text = dataset["formatting"].format(datum)