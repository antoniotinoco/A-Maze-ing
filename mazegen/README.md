_This reusable module has been created as part of the 42 curriculum by aben-sal and atinoco-._

## MazeGen — Reusable Module
MazeGen is a reusable Python module that generates, solves, and exposes maze structures using a wall-bit encoding system.

### Installation
pip install mazegen-1.0.0-py3-none-any.whl

### Basic Example
from mazegen import MazeGenerator

mg = MazeGenerator(width=20, height=15)
mg.generate()
print(mg.solution_path_str())

### Custom Parameters
- width, height: maze dimensions
- entry: tuple (x, y) for the start cell, default (0, 0)
- exit: tuple (x, y) for the end cell, default (width-1, height-1)
- seed: integer for reproducible generation, default None
- perfect: bool, if True only one path exists between any two cells

### Accessing the maze structure
mg.grid          # 2D list of integers (wall bit flags)
mg.stamp42       # set of (x,y) cells forming the 42 pattern

### Accessing the solution
mg.solution_path()      # ['N', 'E', 'E', 'S', ...]
mg.solution_path_str()  # 'NEES...'