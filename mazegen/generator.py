"""Maze generation and solving logic for the A-Maze-ing project.

This module contains the core algorithmic part of the project. It defines:
- wall bit flags for each direction,
- helper mappings for movement and opposites,
- the 42-shaped blocked pattern placed in the maze,
- the :class:`MazeGenerator` class that builds and solves mazes.

The grid uses hexadecimal-style wall encoding:
- each cell starts as ``0xF`` which means all four walls are closed,
- opening a passage removes one bit from the current cell and the matching
  opposite wall from the neighboring cell.
"""

import random
from collections import deque
from typing import Optional

# Bit flags representing the four possible walls of a cell.
NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8

# For any direction, this mapping gives the matching opposite wall.
OPPOSITE = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}

# Coordinate movement associated with each direction.
DIRECTION_DELTA = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

# Human-readable letters used to store the solution path.
DIRECTION_LETTER = {
    NORTH: "N",
    EAST: "E",
    SOUTH: "S",
    WEST: "W",
}

# Dimensions of the embedded "42" glyph inside the maze.
_GLYPH_WIDTH = 7
_GLYPH_HEIGHT = 5

# Coordinates of all blocked cells that form the 42 pattern.
_GLYPH_CELLS = [
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 2),
    (2, 0),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (4, 0),
    (5, 0),
    (6, 0),
    (6, 1),
    (4, 2),
    (5, 2),
    (6, 2),
    (4, 3),
    (4, 4),
    (5, 4),
    (6, 4),
]


class MazeGenerator:
    """Generate, solve, and export a maze.

    The maze is stored as a 2D grid of integers. Each integer uses bit flags to
    represent which walls are still present in that cell.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Starting cell as ``(x, y)``.
        exit: Target cell as ``(x, y)``.
        seed: Optional random seed for reproducible generation.
        perfect: Whether the maze should stay perfect (one unique path between
            any two cells) or allow extra passages and cycles.
        grid: 2D wall-encoded maze grid.
        stamp42: Set of blocked cells used to draw the 42 pattern.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None,
        seed: Optional[int] = None,
        perfect: bool = True,
    ):
        """Initialize the maze generator with user configuration.

        Args:
            width: Maze width in cells.
            height: Maze height in cells.
            entry: Entry coordinate.
            exit: Exit coordinate. If ``None``, defaults to the bottom-right
                cell.
            seed: Optional seed used to make random generation reproducible.
            perfect: If ``True``, keep the maze perfect. If ``False``, open
                extra passages after generation to create loops.

        Raises:
            TypeError: If width/height/entry/exit/perfect have wrong types.
            ValueError: If dimensions are not positive, coordinates are out of
                bounds, or entry and exit are the same cell.
        """
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("width and height must be integers")
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive integers")
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise TypeError("entry must be a tuple of (x, y)")
        if exit is not None and (
            not isinstance(exit, tuple) or len(exit) != 2
        ):
            raise TypeError("exit must be a tuple of (x, y)")
        if not isinstance(perfect, bool):
            raise TypeError("perfect must be a boolean")
        if seed is not None and not isinstance(seed, int):
            raise TypeError("seed must be an integer or None")

        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit if exit else (width - 1, height - 1)
        self.seed = seed
        self.perfect = perfect

        ex, ey = self.entry
        if not (0 <= ex < width and 0 <= ey < height):
            raise ValueError("entry is out of bounds")

        ox, oy = self.exit
        if not (0 <= ox < width and 0 <= oy < height):
            raise ValueError("exit is out of bounds")

        if self.entry == self.exit:
            raise ValueError("entry and exit must be different")

        self.grid: list[list[int]] = []
        self._solution: list[str] = []
        self._rng = random.Random(seed)
        self.stamp42: set[tuple[int, int]] = set()

    def generate(self) -> None:
        """Generate a complete maze and compute its solution.

        The generation process is:
        1. Initialize the grid with all walls closed.
        2. Place the 42 blocked pattern.
        3. Carve a perfect maze with depth-first search.
        4. Optionally add extra passages for non-perfect mode.
        5. Solve the maze from entry to exit.

        Several attempts are allowed in case a generated layout is invalid.

        Raises:
            ValueError: If entry or exit lies inside the 42 pattern.
            RuntimeError: If no valid maze is produced after many attempts.
        """
        max_attempts = 100
        for _ in range(max_attempts):
            self._init_grid()
            self._set_stamp42()

            if self.entry in self.stamp42 or self.exit in self.stamp42:
                raise ValueError(
                    "Entry or exit cannot be inside the 42 pattern"
                )

            self._carve_passages()

            if not self._all_non42_visited():
                continue

            if not self.perfect:
                self._add_extra_passages()

            self._solve()
            if self._solution:
                return

        raise RuntimeError(
            "Failed to generate a valid maze after multiple attempts"
        )

    def _init_grid(self) -> None:
        """Create a fresh grid where every cell starts fully closed.

        ``0xF`` means all four walls are present:
        - North bit set
        - East bit set
        - South bit set
        - West bit set
        """
        self.grid = [
            [0xF for _ in range(self.width)] for _ in range(self.height)
        ]

    def _set_stamp42(self) -> None:
        """Place the 42 pattern in the center of the maze when possible.

        If the maze is too small, the pattern is skipped.
        The pattern cells are stored in ``self.stamp42`` and are treated as
        blocked cells during generation.
        """
        if self.width < _GLYPH_WIDTH + 2 or self.height < _GLYPH_HEIGHT + 2:
            print("Warning: Maze too small for 42 pattern – pattern omitted.")
            self.stamp42 = set()
            return

        ax = (self.width - _GLYPH_WIDTH) // 2
        ay = (self.height - _GLYPH_HEIGHT) // 2
        self.stamp42 = {(ax + dx, ay + dy) for dx, dy in _GLYPH_CELLS}

    def _carve_passages(self) -> None:
        """Carve a perfect maze using iterative depth-first search.

        The algorithm uses a stack:
        - start from the entry,
        - randomly choose an unvisited neighbor,
        - open the wall between current cell and neighbor,
        - continue until no moves remain, then backtrack.

        Cells belonging to the 42 stamp are marked as already visited so the
        algorithm never enters them.
        """
        if self.entry in self.stamp42:
            return

        visited = [[False] * self.width for _ in range(self.height)]

        for x, y in self.stamp42:
            visited[y][x] = True

        sx, sy = self.entry
        stack = [(sx, sy)]
        visited[sy][sx] = True

        while stack:
            x, y = stack[-1]
            directions = list(DIRECTION_DELTA.keys())
            self._rng.shuffle(directions)

            moved = False
            for direction in directions:
                dx, dy = DIRECTION_DELTA[direction]
                nx, ny = x + dx, y + dy

                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if visited[ny][nx]:
                    continue

                self._open_wall(x, y, nx, ny, direction)
                visited[ny][nx] = True
                stack.append((nx, ny))
                moved = True
                break

            if not moved:
                stack.pop()

    def _open_wall(
        self,
        x: int,
        y: int,
        nx: int,
        ny: int,
        direction: int,
    ) -> None:
        """Open the wall between a cell and one of its neighbors.

        The wall is removed from both cells so the maze stays consistent.

        Args:
            x: Current cell x-coordinate.
            y: Current cell y-coordinate.
            nx: Neighbor cell x-coordinate.
            ny: Neighbor cell y-coordinate.
            direction: Direction bit from current cell to neighbor.
        """
        self.grid[y][x] &= ~direction
        self.grid[ny][nx] &= ~OPPOSITE[direction]

    def _solve(self) -> None:
        """Solve the maze from entry to exit using breadth-first search.

        Breadth-first search is used so the first found path is also the
        shortest path in number of moves.
        The solution is stored as direction letters in ``self._solution``.
        """
        queue: deque[tuple[int, int, list[str]]] = deque()
        visited = set()

        sx, sy = self.entry
        queue.append((sx, sy, []))
        visited.add((sx, sy))

        while queue:
            x, y, path = queue.popleft()

            if (x, y) == self.exit:
                self._solution = path
                return

            for direction, (dx, dy) in DIRECTION_DELTA.items():
                if self.is_wall(x, y, direction):
                    continue

                nx, ny = x + dx, y + dy
                if (nx, ny) in visited:
                    continue

                visited.add((nx, ny))
                queue.append((nx, ny, path + [DIRECTION_LETTER[direction]]))

        self._solution = []

    def is_wall(self, x: int, y: int, direction: int) -> bool:
        """Return whether a wall exists in a given direction from a cell.

        Args:
            x: Cell x-coordinate.
            y: Cell y-coordinate.
            direction: One of the wall direction bit flags.

        Returns:
            ``True`` if the wall is closed, ``False`` if a passage is open.
        """
        return bool(self.grid[y][x] & direction)

    def solution_path_str(self) -> str:
        """Return the solution path as one compact string."""
        return "".join(self._solution)

    def solution_path(self) -> list[str]:
        """Return the solution path as a list of movement letters."""
        return list(self._solution)

    def to_hex_grid(self) -> list[str]:
        """Export the internal grid as hexadecimal text rows.

        Each cell value is converted to a single hexadecimal character, which
        matches the wall-bit encoding used by the project.
        """
        return [
            "".join(format(self.grid[y][x], "X") for x in range(self.width))
            for y in range(self.height)
        ]

    def __repr__(self) -> str:
        """Return a short developer-friendly representation of the maze."""
        return f"MazeGenerator({self.width}x{self.height})"

    def _all_non42_visited(self) -> bool:
        """Check that every normal cell was reached during carving.

        A non-42 cell that still equals ``0xF`` was never carved into, meaning
        that part of the maze stayed isolated.

        Returns:
            ``True`` if every non-stamp cell was visited, else ``False``.
        """
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.stamp42 and self.grid[y][x] == 0xF:
                    return False
        return True

    def _is_3x3_open(self, tx: int, ty: int) -> bool:
        """Check whether a 3x3 area has become fully open internally.

        This helper is used in non-perfect mode to prevent creating large open
        rooms that would break the maze-like structure.

        Args:
            tx: Top-left x-coordinate of the 3x3 block.
            ty: Top-left y-coordinate of the 3x3 block.

        Returns:
            ``True`` if the 3x3 block has no internal walls, else ``False``.
        """
        for y in range(ty, ty + 3):
            for x in range(tx, tx + 3):
                if x + 1 <= tx + 2:
                    if (
                        (self.grid[y][x] & EAST)
                        or (self.grid[y][x + 1] & WEST)
                    ):
                        return False
                if y + 1 <= ty + 2:
                    if (
                        (self.grid[y][x] & SOUTH)
                        or (self.grid[y + 1][x] & NORTH)
                    ):
                        return False
        return True

    def _add_extra_passages(self) -> None:
        """Open extra walls to create a non-perfect maze with loops.

        Random closed walls are selected and tested one by one.
        A candidate opening is kept only if it does not create a fully open 3x3
        area. This adds cycles while preserving a more maze-like appearance.
        """
        if self.perfect:
            return

        target = max(1, (self.width * self.height) // 10)
        opened = 0
        attempts = 0
        max_attempts = target * 20

        while opened < target and attempts < max_attempts:
            attempts += 1
            x = self._rng.randrange(self.width)
            y = self._rng.randrange(self.height)
            if (x, y) in self.stamp42:
                continue

            directions = list(DIRECTION_DELTA.keys())
            self._rng.shuffle(directions)

            for direction in directions:
                dx, dy = DIRECTION_DELTA[direction]
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if (nx, ny) in self.stamp42:
                    continue
                if not (self.grid[y][x] & direction):
                    continue

                self.grid[y][x] &= ~direction
                self.grid[ny][nx] &= ~OPPOSITE[direction]

                invalid = False
                if self.width >= 3 and self.height >= 3:
                    for ty in range(self.height - 2):
                        for tx in range(self.width - 2):
                            if self._is_3x3_open(tx, ty):
                                invalid = True
                                break
                        if invalid:
                            break

                if invalid:
                    self.grid[y][x] |= direction
                    self.grid[ny][nx] |= OPPOSITE[direction]
                else:
                    opened += 1
                    break
