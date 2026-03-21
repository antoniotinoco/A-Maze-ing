"""Terminal rendering utilities for the A-Maze-ing project.

This module converts the logical maze structure into a colored ASCII-style
terminal view. It is responsible only for presentation:
- clearing the screen,
- building a visual canvas,
- painting walls, empty space, entry, exit, the 42 stamp, and the solution,
- returning the final UI text shown to the player.
"""

from .generator import EAST, SOUTH

# Terminal escape codes used to style the interface.
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"

FG_BRIGHT_BLACK = "\033[90m"
FG_BRIGHT_MAGENTA = "\033[95m"
FG_BRIGHT_CYAN = "\033[96m"

BG_BLACK = "\033[40m"
BG_OLIVE = "\033[43m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[107m"
BG_MAGENTA = "\033[45m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"

# Available wall color themes that the user can cycle through.
WALL_COLORS = [
    ("olive", BG_OLIVE),
    ("green", BG_GREEN),
    ("white", BG_WHITE),
    ("cyan", BG_CYAN),
]

# Logical cell types used on the temporary drawing canvas.
EMPTY = "empty"
WALL = "wall"
STAMP = "stamp"
ENTRY = "entry"
EXIT = "exit"
DOT = "dot"

# Size of one maze cell in terminal "pixels".
CELL_W = 3
CELL_H = 2
PIX = "  "



def clear_screen() -> None:
    """Clear the terminal and move the cursor to the top-left corner."""
    print(CLEAR, end="")



def _paint(kind: str, wall_bg: str) -> str:
    """Convert a logical canvas cell into a colored terminal string.

    Args:
        kind: One of the canvas cell types such as ``WALL`` or ``ENTRY``.
        wall_bg: ANSI background color used for walls.

    Returns:
        A short styled string representing one visual block in the terminal.
    """
    if kind == WALL:
        return f"{wall_bg}{PIX}{RESET}"
    if kind == STAMP:
        return f"{BG_WHITE}{PIX}{RESET}"
    if kind == ENTRY:
        return f"{BG_MAGENTA}{PIX}{RESET}"
    if kind == EXIT:
        return f"{BG_RED}{PIX}{RESET}"
    if kind == DOT:
        return f"{BG_BLACK}{FG_BRIGHT_CYAN}• {RESET}"
    return f"{BG_BLACK}{PIX}{RESET}"



def _solution_steps(entry: tuple[int, int], path: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Turn a solution string into a list of movement segments.

    Example:
        If the entry is ``(0, 0)`` and the path is ``"ES"``, the result is a
        list of segments showing movement from ``(0, 0)`` to ``(1, 0)`` and
        then from ``(1, 0)`` to ``(1, 1)``.

    Args:
        entry: Starting maze coordinate.
        path: Solution path using letters ``N``, ``S``, ``E``, ``W``.

    Returns:
        A list of ``((x1, y1), (x2, y2))`` movement pairs.
    """
    x, y = entry
    steps: list[tuple[tuple[int, int], tuple[int, int]]] = []

    for move in path:
        nx, ny = x, y
        if move == "N":
            ny -= 1
        elif move == "S":
            ny += 1
        elif move == "E":
            nx += 1
        elif move == "W":
            nx -= 1
        steps.append(((x, y), (nx, ny)))
        x, y = nx, ny

    return steps



def _cell_origin(x: int, y: int) -> tuple[int, int]:
    """Return the top-left canvas position of maze cell ``(x, y)``.

    The visual canvas is larger than the logical maze because each maze cell is
    expanded into a small rectangle with room for surrounding walls.
    """
    return 1 + x * (CELL_W + 1), 1 + y * (CELL_H + 1)



def _cell_center(x: int, y: int) -> tuple[int, int]:
    """Return the center position of maze cell ``(x, y)`` on the canvas.

    This is mainly used to draw the solution path through the middle of cells.
    """
    ox, oy = _cell_origin(x, y)
    return ox + CELL_W // 2, oy + CELL_H // 2



def _fill_rect(canvas: list[list[str]], x0: int, y0: int, w: int, h: int, kind: str) -> None:
    """Fill a rectangular area of the canvas with one logical cell type.

    Args:
        canvas: 2D drawing buffer.
        x0: Left coordinate of the rectangle.
        y0: Top coordinate of the rectangle.
        w: Rectangle width.
        h: Rectangle height.
        kind: Logical type to write into the rectangle.
    """
    for yy in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            canvas[yy][xx] = kind



def _build_canvas(gen, show_solution: bool) -> list[list[str]]:
    """Create the full logical drawing canvas for the maze.

    The canvas starts completely filled with walls. The function then opens the
    inside of each maze cell, removes walls where passages exist, paints the 42
    stamp, paints entry and exit, and optionally overlays the solution.

    Args:
        gen: Maze generator containing the maze data.
        show_solution: Whether the solution path should be drawn.

    Returns:
        A 2D list of logical cell type strings.
    """
    rows = gen.height * (CELL_H + 1) + 1
    cols = gen.width * (CELL_W + 1) + 1
    canvas = [[WALL for _ in range(cols)] for _ in range(rows)]

    for y in range(gen.height):
        for x in range(gen.width):
            ox, oy = _cell_origin(x, y)
            _fill_rect(canvas, ox, oy, CELL_W, CELL_H, EMPTY)

            cell = gen.grid[y][x]
            if not (cell & EAST):
                _fill_rect(canvas, ox + CELL_W, oy, 1, CELL_H, EMPTY)
            if not (cell & SOUTH):
                _fill_rect(canvas, ox, oy + CELL_H, CELL_W, 1, EMPTY)
            if not (cell & EAST) and not (cell & SOUTH):
                canvas[oy + CELL_H][ox + CELL_W] = EMPTY

    for x, y in gen.stamp42:
        ox, oy = _cell_origin(x, y)
        _fill_rect(canvas, ox, oy, CELL_W, CELL_H, STAMP)

    ex, ey = gen.entry
    ox, oy = _cell_origin(ex, ey)
    _fill_rect(canvas, ox, oy, CELL_W, CELL_H, ENTRY)

    xx, xy = gen.exit
    ox, oy = _cell_origin(xx, xy)
    _fill_rect(canvas, ox, oy, CELL_W, CELL_H, EXIT)

    if show_solution:
        steps = _solution_steps(gen.entry, gen.solution_path_str())
        sx, sy = _cell_center(*gen.entry)
        canvas[sy][sx] = DOT

        for (x1, y1), (x2, y2) in steps:
            px1, py1 = _cell_center(x1, y1)
            px2, py2 = _cell_center(x2, y2)

            dx = 0 if px1 == px2 else (1 if px2 > px1 else -1)
            dy = 0 if py1 == py2 else (1 if py2 > py1 else -1)

            cx, cy = px1, py1
            while (cx, cy) != (px2, py2):
                canvas[cy][cx] = DOT
                cx += dx
                cy += dy
            canvas[cy][cx] = DOT

        # Repaint start/end so they remain visible above the solution path.
        ox, oy = _cell_origin(ex, ey)
        _fill_rect(canvas, ox, oy, CELL_W, CELL_H, ENTRY)
        ox, oy = _cell_origin(xx, xy)
        _fill_rect(canvas, ox, oy, CELL_W, CELL_H, EXIT)

    return canvas



def render_maze(gen, show_solution: bool = False, color_index: int = 0) -> str:
    """Render the maze as one complete terminal string.

    Args:
        gen: Maze generator containing the maze data.
        show_solution: Whether to display the solution path.
        color_index: Index of the currently selected wall color theme.

    Returns:
        The full text interface ready to be printed to the terminal.
    """
    color_name, wall_bg = WALL_COLORS[color_index]
    canvas = _build_canvas(gen, show_solution)

    lines: list[str] = []
    lines.append(f"{FG_BRIGHT_MAGENTA}{BOLD}A-Maze-ing{RESET}  {FG_BRIGHT_BLACK}{gen.width}x{gen.height}{RESET}")
    lines.append("")

    for row in canvas:
        lines.append("".join(_paint(kind, wall_bg) for kind in row))

    lines.append("")
    lines.append(
        f"{FG_BRIGHT_BLACK}legend:{RESET} "
        f"{_paint(ENTRY, wall_bg)}{RESET}=entry  "
        f"{_paint(EXIT, wall_bg)}{RESET}=exit  "
        f"{_paint(DOT, wall_bg)}{RESET}=solution  "
    )
    lines.append(
        f"{FG_BRIGHT_BLACK}wall:{RESET} {color_name}    "
        f"{FG_BRIGHT_BLACK}commands:{RESET} r regenerate | s solution | c color | q quit"
    )

    return "\n".join(lines)



def print_ui(gen, show_solution: bool, color_index: int) -> None:
    """Clear the screen and print the current maze interface.

    Args:
        gen: Maze generator containing the maze data.
        show_solution: Whether the solution path should be visible.
        color_index: Currently selected wall color theme.
    """
    clear_screen()
    print(render_maze(gen, show_solution, color_index))
