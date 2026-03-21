"""Command-line entry point for the A-Maze-ing project.

This small wrapper allows the project to be launched with:

    python3 a_maze_ing.py config.txt

It checks that the user passed exactly one argument and then forwards that
argument to the real ``main`` function inside the package.
"""

import sys
from mazegen.main import main


if __name__ == "__main__":
    """Validate command-line arguments and start the program."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    config_file = sys.argv[1]

    main(config_file)
