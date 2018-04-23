WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

YELLOW = (255,255,0)
MAGENTA = (255,0,255)
CYAN = (0,238,238)
PURPLE = (128,0,128)



def is_color(color):
    return isinstance(color, tuple) and len(color) == 3 and all([0 <= x <= 255 for x in color])
