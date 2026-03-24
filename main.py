"""Main application flow for the A-Maze-ing project.

This module connects all major parts of the program:
- it reads and validates the config,
- builds a maze generator,
- generates and writes the maze,
- launches the interactive terminal UI.
"""

from config import config, validate_config
from display import print_ui, WALL_COLORS, STAMP_COLORS
from mazegen import MazeGenerator
from writer import write_maze
from typing import Any


def _build_generator(cfg: dict[str, Any]) -> MazeGenerator:
    """Create a :class:`MazeGenerator` from validated configuration values.

    Args:
        cfg: Validated configuration dictionary.

    Returns:
        A configured :class:`MazeGenerator` instance.
    """
    return MazeGenerator(
        cfg["WIDTH"],
        cfg["HEIGHT"],
        cfg["ENTRY"],
        cfg["EXIT"],
        seed=cfg.get("SEED"),
        perfect=cfg["PERFECT"],
    )


def _generate_and_write(gen: MazeGenerator, output_file: str) -> None:
    """Generate a maze and immediately save it to disk.

    This helper keeps the main flow easier to read by grouping together the
    two actions that always happen back-to-back.

    Args:
        gen: Maze generator instance to use.
        output_file: Path of the output file to write.
    """
    gen.generate()
    write_maze(gen, output_file)


def main(config_path: str) -> None:
    """Run the complete maze program.

    The function first loads the configuration and generates the maze. If that
    succeeds, it enters a small interactive loop where the user can:
    - quit,
    - toggle the solution display,
    - cycle wall colors,
    - regenerate the maze.

    Args:
        config_path: Path to the configuration file provided by the user.
    """
    try:
        cfg = validate_config(config(config_path))
        gen = _build_generator(cfg)
        _generate_and_write(gen, cfg["OUTPUT_FILE"])
    except Exception as e:
        print(f"Error: {e}")
        return

    show_solution = False
    color_index = 0
    stamp_color_index = 0

    while True:
        print_ui(gen, show_solution, color_index, stamp_color_index)
        command = input("> ").strip().lower()

        if command == "q":
            break
        if command == "s":
            show_solution = not show_solution
            continue
        if command == "c":
            color_index = (color_index + 1) % len(WALL_COLORS)
            continue
        if command == "t":
            stamp_color_index = (stamp_color_index + 1) % len(STAMP_COLORS)
            continue
        if command == "r":
            try:
                if cfg.get("SEED") is not None:
                    cfg["SEED"] += 1
                gen = _build_generator(cfg)
                _generate_and_write(gen, cfg["OUTPUT_FILE"])
                show_solution = False
            except Exception as e:
                print(f"Error: {e}")
                break
            continue

        print("Unknown command. Use r, s, c, t or q.")
