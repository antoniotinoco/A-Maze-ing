"""Maze generation module — core MazeGenerator class."""

import random
from collections import deque
from typing import Optional


NORTH: int = 0b0001  # bit 0
EAST:  int = 0b0010  # bit 1
SOUTH: int = 0b0100  # bit 2
WEST:  int = 0b1000  # bit 3

OPPOSITE: dict[int, int] = {
    NORTH: SOUTH,
    EAST:  WEST,
    SOUTH: NORTH,
    WEST:  EAST,
}

DIRECTION_DELTA: dict[int, tuple[int, int]] = {
    NORTH: (0, -1),
    EAST:  (1,  0),
    SOUTH: (0,  1),
    WEST:  (-1, 0),
}

DIRECTION_LETTER: dict[int, str] = {
    NORTH: "N",
    EAST:  "E",
    SOUTH: "S",
    WEST:  "W",
}

_GLYPH_WIDTH:  int = 8
_GLYPH_HEIGHT: int = 5

_GLYPH_CELLS: list[tuple[int, int]] = [
    # "4"  (columns 0-2)
    (0, 0), (0, 1), (0, 2),
    (1, 2),
    (2, 2), (2, 3), (2, 4),
    # "2"  (columns 4-6)
    (4, 0), (5, 0), (6, 0),
    (6, 1),
    (4, 2), (5, 2), (6, 2),
    (4, 3),
    (4, 4), (5, 4), (6, 4),
]


class MazeGenerator:
    """Generates a random maze and exposes its structure and solution."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None,
        seed: Optional[int] = None,
        perfect: bool = True,
    ) -> None:
        """Initialise generator parameters."""
        self.width = width
        self.height = height
        self.entry = entry
        self.exit: tuple[int, int] = (
            exit if exit is not None else (width - 1, height - 1)
        )
        self.seed = seed
        self.perfect = perfect

        self.grid: list[list[int]] = []
        self._solution: list[str] = []
        self._rng = random.Random(seed)
        self._42_anchor: Optional[tuple[int, int]] = None

    def generate(self) -> None:
        """Generate the maze in-place, populating self.grid."""
        self._init_grid()
        self._carve_passages()
        self._embed_42()
        if not self.perfect:
            self._add_loops()
        self._solve()

    def _init_grid(self) -> None:
        """Allocate grid with all walls closed (0xF per cell)."""
        self.grid = [
            [0xF for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def _carve_passages(self) -> None:
        """Carve passages using an iterative DFS (recursive backtracker)."""
        visited: list[list[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        sx, sy = self.entry
        stack: list[tuple[int, int]] = [(sx, sy)]
        visited[sy][sx] = True

        while stack:
            x, y = stack[-1]
            directions = list(DIRECTION_DELTA.keys())
            self._rng.shuffle(directions)

            moved = False
            for direction in directions:
                dx, dy = DIRECTION_DELTA[direction]
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and not visited[ny][nx]
                ):
                    self._open_wall(x, y, nx, ny, direction)
                    visited[ny][nx] = True
                    stack.append((nx, ny))
                    moved = True
                    break

            if not moved:
                stack.pop()

    def _open_wall(
        self, x: int, y: int, nx: int, ny: int, direction: int
    ) -> None:
        """Remove the wall between (x,y) and (nx,ny) in both cells."""
        self.grid[y][x]   &= ~direction
        self.grid[ny][nx] &= ~OPPOSITE[direction]

    def _embed_42(self) -> None:
        """Embed the '42' pattern as fully closed cells inside the maze."""
        min_w = _GLYPH_WIDTH + 2
        min_h = _GLYPH_HEIGHT + 2

        if self.width < min_w or self.height < min_h:
            print(
                "Warning: maze is too small to embed the '42' pattern "
                f"(need at least {min_w}x{min_h})."
            )
            return

        ax = (self.width  - _GLYPH_WIDTH)  // 2
        ay = (self.height - _GLYPH_HEIGHT) // 2
        self._42_anchor = (ax, ay)

        glyph_set: set[tuple[int, int]] = set(
            (ax + dx, ay + dy) for dx, dy in _GLYPH_CELLS
        )

        for gx, gy in glyph_set:
            self.grid[gy][gx] = 0xF

        for gx, gy in glyph_set:
            for direction, (ddx, ddy) in DIRECTION_DELTA.items():
                nx, ny = gx + ddx, gy + ddy
                if (nx, ny) not in glyph_set:
                    self.grid[ny][nx] |= OPPOSITE[direction]

    def _add_loops(self) -> None:
        """Knock down a few extra walls to create loops."""
        num_loops = max(1, (self.width * self.height) // 20)
        attempts = 0
        added = 0

        while added < num_loops and attempts < num_loops * 10:
            attempts += 1
            x = self._rng.randint(0, self.width - 2)
            y = self._rng.randint(0, self.height - 2)
            direction = self._rng.choice([EAST, SOUTH])
            dx, dy = DIRECTION_DELTA[direction]
            nx, ny = x + dx, y + dy

            if (
                self.grid[y][x] & direction
                and not self._would_create_wide_area(x, y, nx, ny, direction)
            ):
                self._open_wall(x, y, nx, ny, direction)
                added += 1

    def _would_create_wide_area(
        self, x: int, y: int, nx: int, ny: int, direction: int
    ) -> bool:
        """Return True if opening this wall would create a 3x3 open area."""
        for cx in range(max(0, x - 1), min(self.width - 3, x + 1) + 1):
            for cy in range(max(0, y - 1), min(self.height - 3, y + 1) + 1):
                if self._is_3x3_open(cx, cy, x, y, nx, ny, direction):
                    return True
        return False

    def _is_3x3_open(
        self,
        cx: int, cy: int,
        ox: int, oy: int,
        nx: int, ny: int,
        direction: int,
    ) -> bool:
        """Return True if the 3x3 block at (cx,cy) would be fully open."""
        for bx in range(cx, cx + 3):
            for by in range(cy, cy + 3):
                walls = self.grid[by][bx]
                if (bx, by) == (ox, oy):
                    walls &= ~direction
                if (bx, by) == (nx, ny):
                    walls &= ~OPPOSITE[direction]
                if bx < cx + 2 and (walls & EAST):
                    return False
                if by < cy + 2 and (walls & SOUTH):
                    return False
        return True









    def cell(self, x: int, y: int) -> int:
        """Return the wall bitmask for cell (x, y)."""
        return self.grid[y][x]

    def is_wall(self, x: int, y: int, direction: int) -> bool:
        """Return True if the given wall of cell (x, y) is closed."""
        return bool(self.grid[y][x] & direction)

    def solution_path(self) -> list[str]:
        """Return the shortest path as a list of direction letters."""
        return list(self._solution)

    def solution_path_str(self) -> str:
        """Return the shortest path as a single string e.g. 'NESSWW'."""
        return "".join(self._solution)

    def to_hex_grid(self) -> list[str]:
        """Return the grid as rows of hex characters (one char per cell)."""
        return [
            "".join(format(self.grid[y][x], "X") for x in range(self.width))
            for y in range(self.height)
        ]

    # ------------------------------------------------------------------
    # Private helpers (stubs — to be implemented)
    # ------------------------------------------------------------------

    def _solve(self) -> None:
        """Compute shortest path from entry to exit (BFS)."""
        # TODO: BFS over self.grid; store result in self._solution
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Short developer representation."""
        return (
            f"MazeGenerator(width={self.width}, height={self.height}, "
            f"seed={self.seed}, perfect={self.perfect})"
        )
