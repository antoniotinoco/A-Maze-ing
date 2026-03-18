import pygame

CELL = 25

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 100, 255)
RED = (255, 80, 80)
GREEN = (80, 255, 80)
STAMP = (180, 180, 180)

COLORS = [
    (255, 255, 255),
    (0, 255, 0),
    (255, 255, 0),
    (0, 255, 255),
]

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8


def draw_maze(screen, grid, gen, wall_color):
    rows = len(grid)
    cols = len(grid[0])

    for y in range(rows):
        for x in range(cols):
            cell = grid[y][x]

            px = x * CELL
            py = y * CELL

            pygame.draw.rect(screen, BLACK, (px, py, CELL, CELL))

            # draw 42
            if hasattr(gen, "stamp42") and (x, y) in gen.stamp42:
                pygame.draw.rect(screen, STAMP, (px, py, CELL, CELL))

            # walls
            if cell & NORTH:
                pygame.draw.line(screen, wall_color, (px, py), (px + CELL, py), 2)

            if cell & SOUTH:
                pygame.draw.line(screen, wall_color, (px, py + CELL), (px + CELL, py + CELL), 2)

            if cell & WEST:
                pygame.draw.line(screen, wall_color, (px, py), (px, py + CELL), 2)

            if cell & EAST:
                pygame.draw.line(screen, wall_color, (px + CELL, py), (px + CELL, py + CELL), 2)


def draw_path(screen, path, entry):
    x, y = entry

    # start from center of entry cell
    px = x * CELL + CELL // 2
    py = y * CELL + CELL // 2

    for move in path:
        nx, ny = x, y

        if move == "N":
            ny -= 1
        elif move == "S":
            ny += 1
        elif move == "E":
            nx += 1
        elif move == "W":
            nx -= 1

        # next cell center
        npx = nx * CELL + CELL // 2
        npy = ny * CELL + CELL // 2

        pygame.draw.line(screen, BLUE, (px, py), (npx, npy), 4)

        # move forward
        x, y = nx, ny
        px, py = npx, npy


def draw_points(screen, entry, exit_pos):
    sx, sy = entry
    ex, ey = exit_pos

    pygame.draw.rect(screen, GREEN, (sx * CELL + 5, sy * CELL + 5, CELL - 10, CELL - 10))
    pygame.draw.rect(screen, RED, (ex * CELL + 5, ey * CELL + 5, CELL - 10, CELL - 10))
