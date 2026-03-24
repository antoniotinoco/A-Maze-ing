_This project has been created as part of the 42 curriculum by aben-sal and atinoco-._

# A-Maze-ing

A Python maze generator that creates, solves, and displays mazes in the terminal.
The generation logic is packaged as a reusable pip-installable module.

---

## Description

A-Maze-ing generates random mazes from a configuration file and displays them
in the terminal with colored ASCII rendering. The program supports perfect mazes
(exactly one path between any two cells) and non-perfect mazes (with loops).
Every maze contains a "42" pattern formed by fully closed cells, and the
shortest solution path can be toggled on and off interactively.

The core generation logic is available as a standalone pip-installable package
called `mazegen`, which can be reused in any other Python project.

---

## Instructions

### Requirements

- Python 3.10 or later
- A terminal with ANSI color support

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd a-maze-ing

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the project and its dev dependencies
make install
```

### Running the program
```bash
make run
```

Or directly:
```bash
python3 a_maze_ing.py config.txt
```

### Interactive commands

| Key | Action |
|-----|--------|
| `r` | Regenerate a new maze |
| `s` | Show / hide the solution path |
| `c` | Cycle wall colors |
| `t` | Cycle 42 stamp colors |
| `q` | Quit |

### Linting and type checking
```bash
make lint         # flake8 + mypy
make lint-strict  # flake8 + mypy --strict
```

### Cleaning up
```bash
make clean
```

---

## Configuration File

The program reads a plain text configuration file. Each line must follow the
`KEY=VALUE` format. Lines starting with `#` are treated as comments and ignored.

### Mandatory keys

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `WIDTH` | integer | Number of cells horizontally | `WIDTH=20` |
| `HEIGHT` | integer | Number of cells vertically | `HEIGHT=15` |
| `ENTRY` | x,y | Entry cell coordinates | `ENTRY=0,0` |
| `EXIT` | x,y | Exit cell coordinates | `EXIT=19,14` |
| `OUTPUT_FILE` | string | Path of the output file | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | True/False | Whether the maze is perfect | `PERFECT=True` |

### Optional keys

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `SEED` | integer | Random seed for reproducibility | `SEED=42` |

### Example config file
```
# A-Maze-ing configuration
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

---

## Output File Format

The output file contains:
1. The maze grid: one row per line, one hexadecimal digit per cell.
2. A blank line.
3. The entry coordinates.
4. The exit coordinates.
5. The shortest solution path as a string of `N`, `E`, `S`, `W` letters.

Each hexadecimal digit encodes which walls are closed using bit flags:

| Bit | Direction |
|-----|-----------|
| 0 (LSB) | North |
| 1 | East |
| 2 | South |
| 3 | West |

A closed wall sets the bit to `1`, an open passage sets it to `0`.

---

## Maze Generation Algorithm

The program uses two algorithms: **recursive backtracker** (iterative depth-first
search) to generate the maze, and **breadth-first search** to solve it.

### Generation | Recursive Backtracker

1. All cells start fully walled.
2. The "42" pattern cells are marked as blocked.
3. Starting from the entry cell, the algorithm randomly picks an unvisited
   neighbor, removes the wall between them, and moves to that neighbor.
4. When no unvisited neighbors remain, it backtracks along the stack until
   a cell with unvisited neighbors is found.
5. The process ends when the stack is empty and all reachable cells have
   been visited.
6. If `PERFECT=False`, extra random walls are removed after generation to
   create loops, while preventing any fully open 3×3 area.

### Why recursive backtracker

- It is simple to implement correctly and easy to reason about.
- It produces mazes with long, winding corridors which look visually
  interesting in the terminal.
- It naturally integrates a seed for full reproducibility.
- Adapting it to work around blocked cells (the "42" pattern) requires
  minimal changes, just marking those cells as already visited.
- Its iterative version avoids Python recursion limit issues on large mazes.

### Solving | Breadth-First Search

1. Starting from the entry cell, BFS explores all immediate neighbors first
   before moving further.
2. Each node in the queue carries the full path taken to reach it.
3. When a branch hits a dead end, it simply produces no new queue entries
   and silently disappears (no explicit backtracking needed).
4. The first time the exit cell is reached, the search stops immediately.

### Why BFS for solving

- Because BFS explores level by level, the first time it reaches the exit
  it is guaranteed to have taken the fewest steps, making the solution
  the shortest possible path.
- It is straightforward to implement and reason about.
- Unlike DFS, it never needs to backtrack or discard partial solutions
  explicitly. Dead end branches just die naturally when the queue moves on.

---

## Reusable Module | mazegen

The maze generation logic is packaged as a standalone pip-installable module.
It has no external dependencies and can be used in any Python 3.10+ project.

### Installation
```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic example
```python
from mazegen import MazeGenerator

mg = MazeGenerator(width=20, height=15, seed=42)
mg.generate()

print(mg.solution_path_str())   # e.g. "EESSWWN..."
print(mg.solution_path())       # ['E', 'E', 'S', 'S', 'W', 'W', 'N', ...]
```

### Custom parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | `int` | required | Number of cells horizontally |
| `height` | `int` | required | Number of cells vertically |
| `entry` | `tuple[int, int]` | `(0, 0)` | Entry cell coordinates |
| `exit` | `tuple[int, int]` | `(width-1, height-1)` | Exit cell coordinates |
| `seed` | `int \| None` | `None` | Random seed for reproducibility |
| `perfect` | `bool` | `True` | If True, exactly one path between any two cells |

### Accessing the maze structure
```python
mg.grid          # list[list[int]] — 2D wall-encoded grid, accessed as grid[y][x]
mg.stamp42       # set[tuple[int, int]] — cells forming the 42 pattern
mg.entry         # tuple[int, int] — entry coordinates
mg.exit          # tuple[int, int] — exit coordinates
```

Each integer in `grid` encodes walls as bit flags (same table as output format above).
Use `mg.is_wall(x, y, direction)` to check individual walls:
```python
from mazegen.generator import NORTH, EAST, SOUTH, WEST

if mg.is_wall(0, 0, EAST):
    print("Wall to the east of (0, 0)")
```

### Accessing the solution
```python
mg.solution_path()      # list of direction letters ['N', 'E', ...]
mg.solution_path_str()  # compact string "NE..."
mg.to_hex_grid()        # list of hex strings, one per row
```

### Rebuilding the package from source
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install build
python -m build
# output appears in dist/
```

---

## Team and Project Management

### Roles

| Member | Responsibilities |
|--------|-----------------|
| `atinoco-` | Maze generation algorithm, package structure, helper files, Makefile, README |
| `aben-sal` | Maze solution algorithm, terminal display, configuration parsing, output file format |

### Planning

Initially we estimated the project would split evenly between the generation
logic and the display/output side. In practice the generation took longer than
expected. Getting the "42" pattern to work correctly with the DFS carving and
ensuring full connectivity across all maze sizes required several iterations.
The packaging and reusability part also took more time than
anticipated because of Python import system subtleties when mixing a
pip-installable package with a plain script project.

### What worked well

- Separating the generation logic into its own module early made testing much
  easier and the packaging step straightforward at the end.
- Using BFS for the solution guaranteed correctness and shortest path without
  extra complexity.
- The iterative DFS avoided Python recursion limit issues on larger mazes.

### What could be improved

- Adding support for multiple generation algorithms (Prim's, Kruskal's) would
  make the project more interesting and is listed as a bonus.
- The terminal display is limited by cell size. Very large mazes become hard
  to read. A graphical MLX display would scale better.

### Tools used

- **VS Code** — main editor
- **mypy** — static type checking
- **flake8** — code style
- **pytest** — local unit testing (not submitted)
- **Claude (Anthropic)** — used for guidance on Python packaging (`pyproject.toml`
  setup, pip-installable module structure), resolving mypy type errors, and
  reviewing exception handling patterns. All generated suggestions were reviewed,
  tested, and adapted manually before inclusion.

---

## Resources

- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Recursive backtracker — Think Labyrinth](http://www.astrolog.org/labyrnth/algrithm.htm)
- [Spanning trees and perfect mazes](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Randomized_depth-first_search)
- [Python packaging guide — PyPA](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [pyproject.toml reference — setuptools](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html)
- [mypy documentation](https://mypy.readthedocs.io/en/stable/)
- [flake8 documentation](https://flake8.pycqa.org/en/latest/)
- [PEP 257 — Docstring conventions](https://peps.python.org/pep-0257/)
- [collections.deque — Python docs](https://docs.python.org/3/library/collections.html#collections.deque)
- [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code)