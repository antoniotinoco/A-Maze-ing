import pygame

from .config import config, validate_config
from .writer import write_maze
from .generator import MazeGenerator
from .display import draw_maze, draw_path, draw_points, COLORS, CELL, BLACK


def main(config_path):
    # 1. LOAD CONFIG
    try:
        cfg = validate_config(config(config_path))
    except Exception as e:
        print(f"Config error: {e}")
        return

    # 2. CREATE GENERATOR
    gen = MazeGenerator(
        cfg["WIDTH"],
        cfg["HEIGHT"],
        cfg["ENTRY"],
        cfg["EXIT"],
        perfect=cfg["PERFECT"],
    )

    gen.generate()

    grid = gen.grid
    path = gen.solution_path_str()
    entry = gen.entry
    exit_pos = gen.exit

    write_maze(gen, cfg["OUTPUT_FILE"])

    # 3. INIT PYGAME
    pygame.init()

    screen = pygame.display.set_mode((len(grid[0]) * CELL, len(grid) * CELL))
    pygame.display.set_caption("Maze | R:regen S:solution C:color Q:quit")

    clock = pygame.time.Clock()

    show_solution = False
    color_index = 0


    # 4. MAIN LOOP

    running = True
    while running:
        screen.fill(BLACK)

        draw_maze(screen, grid, gen, COLORS[color_index])
        draw_points(screen, entry, exit_pos)

        if show_solution:
            draw_path(screen, path, entry)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                # QUIT
                if event.key == pygame.K_q:
                    running = False

                # SHOW/HIDE SOLUTION
                elif event.key == pygame.K_s:
                    show_solution = not show_solution

                # CHANGE COLOR
                elif event.key == pygame.K_c:
                    color_index = (color_index + 1) % len(COLORS)

                # REGENERATE
                elif event.key == pygame.K_r:
                    gen.generate()

                    grid = gen.grid
                    path = gen.solution_path_str()
                    entry = gen.entry
                    exit_pos = gen.exit

                    show_solution = False

                    # UPDATE OUTPUT FILE
                    write_maze(gen, cfg["OUTPUT_FILE"])

        clock.tick(60)

    pygame.quit()