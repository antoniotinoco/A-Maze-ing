"""Output file writer for A-Maze-Ing."""

from mazegen import MazeGenerator


def write_maze(gen: MazeGenerator, output_file: str) -> None:
    """Write the maze grid, entry, exit and solution path to a file."""
    try:
        with open(output_file, "w") as f:
            for row in gen.to_hex_grid():
                f.write(row + "\n")

            f.write("\n")

            ex, ey = gen.entry
            f.write(f"{ex},{ey}\n")

            xx, xy = gen.exit
            f.write(f"{xx},{xy}\n")

            f.write(gen.solution_path_str() + "\n")

    except OSError as e:
        raise OSError(f"Could not write output file '{output_file}': {e}")
