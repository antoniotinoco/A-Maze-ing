"""Configuration parsing and validation for the A-Maze-ing project.

This module is responsible for:
- reading the plain-text configuration file,
- checking that all required keys exist,
- converting text values into the right Python types,
- validating that coordinates and dimensions make sense.

The goal is to keep all configuration-related logic in one place so the
rest of the program can safely work with already validated values.
"""

from typing import Any


def config(path: str = "config.txt") -> dict[str, str]:
    """Read a configuration file and return its raw key/value pairs.

    The file is expected to use the format:

        KEY=value

    Empty lines and comment lines starting with ``#`` are ignored.
    At this stage, values are kept as strings. Type conversion happens later
    in :func:`validate_config`.

    Args:
        path: Path to the configuration file.

    Returns:
        A dictionary containing the parsed configuration values as strings.

    Raises:
        ValueError: If a line is malformed, a key is invalid, a key appears
            more than once, a value is empty, or required keys are missing.
    """
    required_keys = {
        "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"
    }
    optional_keys = {"SEED"}
    allowed_keys = required_keys | optional_keys
    parsed = {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue
                if "=" not in line or line.count("=") != 1:
                    raise ValueError(f"Invalid line format | {line}")

                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip()

                if key not in allowed_keys:
                    raise ValueError(f"Invalid key: {key}")
                if key in parsed:
                    raise ValueError(f"Duplicate key: {key}")
                if not value:
                    raise ValueError(
                        f"{key} cannot be assigned an empty value"
                    )

                parsed[key] = value
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: '{path}'")

    missing = required_keys - parsed.keys()
    if missing:
        raise ValueError(f"Missing keys: {sorted(missing)}")

    return parsed


def validate_config(parsed: dict[str, Any]) -> dict[str, Any]:
    """Convert and validate parsed configuration values.

    This function turns raw strings into usable Python values:
    - ``WIDTH`` and ``HEIGHT`` become integers,
    - ``PERFECT`` becomes a boolean,
    - ``ENTRY`` and ``EXIT`` become ``(x, y)`` tuples,
    - ``SEED`` becomes an integer if present.

    It also checks that the maze dimensions are positive, that entry and exit
    are inside the maze bounds, and that they are not the same cell.

    Args:
        parsed: Raw configuration dictionary produced by :func:`config`.

    Returns:
        The same dictionary, updated in place with validated Python values.

    Raises:
        ValueError: If one or more fields have invalid types or invalid values.
    """
    try:
        width = int(parsed["WIDTH"])
        height = int(parsed["HEIGHT"])
    except ValueError as e:
        raise ValueError("WIDTH and HEIGHT must be integers") from e

    if width <= 0 or height <= 0:
        raise ValueError("WIDTH and HEIGHT must be positive integers")

    parsed["WIDTH"] = width
    parsed["HEIGHT"] = height

    perfect = parsed["PERFECT"]
    if perfect == "True":
        parsed["PERFECT"] = True
    elif perfect == "False":
        parsed["PERFECT"] = False
    else:
        raise ValueError("PERFECT must be True or False")

    parsed["ENTRY"] = _parse_coordinates(parsed["ENTRY"], "ENTRY")
    parsed["EXIT"] = _parse_coordinates(parsed["EXIT"], "EXIT")

    ex, ey = parsed["ENTRY"]
    xx, xy = parsed["EXIT"]

    if not (0 <= ex < width and 0 <= ey < height):
        raise ValueError("ENTRY must be inside the maze bounds")
    if not (0 <= xx < width and 0 <= xy < height):
        raise ValueError("EXIT must be inside the maze bounds")
    if parsed["ENTRY"] == parsed["EXIT"]:
        raise ValueError("ENTRY and EXIT must be different")

    if "SEED" in parsed:
        try:
            parsed["SEED"] = int(parsed["SEED"])
        except ValueError as e:
            raise ValueError("SEED must be an integer") from e

    return parsed


def _parse_coordinates(value: str, name: str) -> tuple[int, int]:
    """Parse a coordinate string written as ``x,y``.

    Args:
        value: Coordinate string such as ``"3,5"``.
        name: Name of the field being parsed, used in error messages.

    Returns:
        A tuple ``(x, y)`` of integers.

    Raises:
        ValueError: If the value is not in the expected ``x,y`` format.
    """
    try:
        x_str, y_str = value.split(",")
        return int(x_str), int(y_str)
    except ValueError as e:
        raise ValueError(f"{name} must be in format x,y with integers") from e
