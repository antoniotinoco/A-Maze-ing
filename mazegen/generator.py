import random
from collections import deque
from typing import Optional

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8

OPPOSITE = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}

DIRECTION_DELTA = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

DIRECTION_LETTER = {
    NORTH: "N",
    EAST: "E",
    SOUTH: "S",
    WEST: "W",
}

_GLYPH_WIDTH = 8
_GLYPH_HEIGHT = 5

_GLYPH_CELLS = [
    (0,0),(0,1),(0,2),
    (1,2),
    (2,0),(2,1),(2,2),(2,3),(2,4),

    (4,0),(5,0),(6,0),
    (6,1),
    (4,2),(5,2),(6,2),
    (4,3),
    (4,4),(5,4),(6,4),
]


class MazeGenerator:

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None,
        seed: Optional[int] = None,
        perfect: bool = True,
    ):
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit if exit else (width - 1, height - 1)
        self.seed = seed
        self.perfect = perfect

        self.grid = []
        self._solution = []
        self._rng = random.Random(seed)

        # visual only
        self.stamp42 = set()

    # --------------------------------------------------

    def generate(self):
        while True:
            self._init_grid()
            self._carve_passages()
            self._embed_42()
    
            self._solve()
    
            # GUARANTEE solution exists
            if self._solution:
                break

    # --------------------------------------------------

    def _init_grid(self):
        self.grid = [[0xF for _ in range(self.width)] for _ in range(self.height)]

    # --------------------------------------------------

    def _carve_passages(self):
        visited = [[False]*self.width for _ in range(self.height)]

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

                if 0 <= nx < self.width and 0 <= ny < self.height and not visited[ny][nx]:
                    self._open_wall(x, y, nx, ny, direction)
                    visited[ny][nx] = True
                    stack.append((nx, ny))
                    moved = True
                    break

            if not moved:
                stack.pop()

    # --------------------------------------------------

    def _open_wall(self, x, y, nx, ny, direction):
        self.grid[y][x] &= ~direction
        self.grid[ny][nx] &= ~OPPOSITE[direction]

    # --------------------------------------------------

    def _embed_42(self):
        if self.width < _GLYPH_WIDTH + 2 or self.height < _GLYPH_HEIGHT + 2:
            print("Maze too small for 42")
            return
    
        ax = (self.width - _GLYPH_WIDTH) // 2
        ay = (self.height - _GLYPH_HEIGHT) // 2
    
        glyph = set((ax + dx, ay + dy) for dx, dy in _GLYPH_CELLS)
    
        self.stamp42 = set(glyph)
    
        for gx, gy in glyph:
            for direction, (dx, dy) in DIRECTION_DELTA.items():
                nx, ny = gx + dx, gy + dy
    
                # ❗ ONLY close walls INSIDE the glyph
                if (nx, ny) in glyph:
                    self.grid[gy][gx] |= direction
                    self.grid[ny][nx] |= OPPOSITE[direction]
    
        # IMPORTANT: DO NOT isolate cells completely
        # ensure each glyph cell has at least ONE opening
        for gx, gy in glyph:
            openings = 0
    
            for direction, (dx, dy) in DIRECTION_DELTA.items():
                nx, ny = gx + dx, gy + dy
    
                if not (self.grid[gy][gx] & direction):
                    openings += 1
    
            # if fully closed → open ONE side
            if openings == 0:
                for direction, (dx, dy) in DIRECTION_DELTA.items():
                    nx, ny = gx + dx, gy + dy
    
                    if (nx, ny) not in glyph:
                        self._open_wall(gx, gy, nx, ny, direction)
                        break

    # --------------------------------------------------

    def _solve(self):
        queue = deque()
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

        # fallback (should NEVER happen now)
        self._solution = []

    # --------------------------------------------------

    def is_wall(self, x, y, direction):
        return bool(self.grid[y][x] & direction)

    def solution_path_str(self):
        return "".join(self._solution)

    def solution_path(self):
        return list(self._solution)

    def to_hex_grid(self):
        return [
            "".join(format(self.grid[y][x], "X") for x in range(self.width))
            for y in range(self.height)
        ]

    # --------------------------------------------------

    def __repr__(self):
        return f"MazeGenerator({self.width}x{self.height})"