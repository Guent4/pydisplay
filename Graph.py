import os
import select
import stat
import threading

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

        self.title = ""
        self.x_label = ""
        self.y_label = ""
        self.x_bounds = [0, 10]
        self.x_bounds = [0, 10]
        self.datasets = dict()

    def setup_new_data_source(self, fifo_source):
        assert os.path.exists(fifo_source) and stat.S_ISFIFO(os.stat(fifo_source).st_mode)

        def _get_new_data():
            with open(fifo_source, "r") as fifo:
                while True:
                    select.select([fifo], [], [fifo])
                    data = fifo.read()
                    self._new_data(fifo_source, data)

        threading.Thread(target=_get_new_data).start()

    def add_dataset(self, name, x_data, y_data):
        assert isinstance(name, str) and name not in self.datasets
        assert isinstance(x_data, list) and all([isinstance(x, int) or isinstance(x, float) for x in x_data])
        assert isinstance(y_data, list) and all([isinstance(y, int) or isinstance(y, float) for y in y_data])
        assert len(x_data) == len(y_data)

        self.datasets[name] = [x_data, y_data]

    def _new_data(self, fifo_source, data):
        print("New data from {}: '{}'".format(fifo_source, data))


class Scatter(Graph):
    def __init__(self, x, y, width, height):
        super(Scatter, self).__init__(x, y, width, height)

    def draw(self, surface):
        pass
