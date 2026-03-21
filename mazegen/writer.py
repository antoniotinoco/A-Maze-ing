"""Output file writer for A-Maze-Ing.

This module takes a generated maze and exports it to the text format expected
by the project:
- the maze grid in hexadecimal form,
- the entry coordinates,
- the exit coordinates,
- the solution path as movement letters.
"""

from .generator import MazeGenerator



def write_maze(gen: MazeGenerator, output_file: str) -> None:
    """Write the generated maze and solution data to a file.

    The output file contains, in order:
    1. The maze grid as hexadecimal digits, one row per line.
    2. A blank line.
    3. The entry coordinates.
    4. The exit coordinates.
    5. The solution path as a compact string such as ``EESSWN``.

    Args:
        gen: The maze generator instance containing the generated maze.
        output_file: Path of the file to create or overwrite.

    Raises:
        OSError: If the file cannot be written.
    """
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            for row in gen.to_hex_grid():
                file.write(row + "\n")

            file.write("\n")

            ex, ey = gen.entry
            file.write(f"{ex},{ey}\n")

            xx, xy = gen.exit
            file.write(f"{xx},{xy}\n")

            file.write(gen.solution_path_str() + "\n")
    except OSError as e:
        raise OSError(f"Could not write output file '{output_file}': {e}") from e
