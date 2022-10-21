from pygame import Vector2

FRAME_LIMIT = 60

CELL_SIZE = 16

DISPLAY_WIDTH = 32 * CELL_SIZE
DISPLAY_HEIGHT = 20 * CELL_SIZE
HALF_DISPLAY = Vector2((DISPLAY_WIDTH / 2) - (CELL_SIZE / 2),
                       (DISPLAY_HEIGHT / 2) - (CELL_SIZE))

WORLD_WIDTH = 40 * CELL_SIZE
WORLD_HEIGHT = 30 * CELL_SIZE
