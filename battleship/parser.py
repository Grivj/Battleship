import re
from typing import TextIO

from .models import MoveCommand, OperationType, Orientation, Position, Ship


class ParseError(ValueError):
    """Custom exception for parsing errors."""

    pass


# Regex patterns
# Matches "(x, y, O)" allowing for whitespace and ensuring orientation is N, E, S, or W
SHIP_REGEX = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*([NESWnesw])\s*\)")
# Matches "(x, y)" allowing for whitespace
COORD_REGEX = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)")
# Matches "(x, y) LRM..." allowing for whitespace and ensuring moves are L, R, or M
MOVE_REGEX = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*([LRMlrm]+)")


def parse_board_size(line: str) -> int:
    """Parses the board size from the first line."""
    stripped_line = line.strip()
    try:
        size = int(stripped_line)
    except ValueError:
        raise ParseError(
            f"Invalid board size format: '{stripped_line}'. Expected an integer, got {stripped_line}."
        ) from None

    if size <= 0:
        raise ParseError("Board size must be a positive integer.")

    return size


def parse_initial_ships(line: str) -> list[Ship]:
    """Parses the initial ship positions and orientations from the second line."""
    ships: list[Ship] = []
    if not (line := line.strip()):
        return ships

    processed_line_len = 0
    last_match_end = 0
    for match in SHIP_REGEX.finditer(line):
        # Check for unexpected characters between matches
        if match.start() > last_match_end:
            if unmatched_part := line[last_match_end : match.start()].strip():
                raise ParseError(
                    f"Invalid characters or format in initial ships line near '{unmatched_part}' in '{line}'"
                )

        x, y, orient_char = match.groups()
        try:
            orientation = Orientation[orient_char.upper()]
            pos = Position(int(x), int(y))
            ships.append(Ship(position=pos, orientation=orientation))
            last_match_end = match.end()
            processed_line_len += len(
                match.group(0).replace(" ", "")
            )  # Count non-whitespace chars in match
        except (ValueError, KeyError) as e:
            # Shouldn't happen if regex matches, but good practice 🤓
            raise ParseError(f"Invalid ship format within '{match.group(0)}'") from e

    if trailing_part := line[last_match_end:].strip():
        raise ParseError(
            f"Invalid trailing characters or format in initial ships line: '{trailing_part}' in '{line}'"
        )

    return ships


ParsedOperation = (
    tuple[OperationType, Position] | tuple[OperationType, Position, list[MoveCommand]]
)


def parse_move_sequence(sequence_str: str) -> list[MoveCommand]:
    """Parses a move sequence string into a list of MoveCommand."""
    commands: list[MoveCommand] = []
    for char in sequence_str.upper():
        try:
            commands.append(MoveCommand[char])
        except KeyError as e:
            # This should ideally be caught by MOVE_REGEX, but defensive check 🤓
            raise ParseError(
                f"Invalid character '{char}' in move sequence '{sequence_str}'"
            ) from e
    return commands


def parse_operation(line: str) -> ParsedOperation:
    """
    Parses a non-empty, stripped operation line (shoot or move).
    Assumes the caller has handled empty/whitespace lines.
    """

    if not line or not (line := line.strip()):
        raise ParseError("Operation line is empty.")

    if move_match := MOVE_REGEX.fullmatch(line):
        # Move operation 🏃
        x, y, sequence_str = move_match.groups()
        try:
            return (
                OperationType.MOVE,
                Position(int(x), int(y)),
                parse_move_sequence(sequence_str),
            )
        except (ValueError, ParseError) as e:
            # Catch potential errors from Position or sequence parsing
            raise ParseError(f"Invalid move operation format '{line}': {e}") from e

    if shoot_match := COORD_REGEX.fullmatch(line):
        # Shoot operation 🔫
        x, y = shoot_match.groups()
        try:
            return OperationType.SHOOT, Position(int(x), int(y))
        except ValueError:
            # If int conversion fails
            raise ParseError(f"Invalid coordinate numbers in shoot operation: '{line}'")

    # If neither MOVE nor SHOOT pattern matched fully
    raise ParseError(
        f"Invalid operation format: '{line}'. Expected '(x, y)' or '(x, y) LRM...'."
    )


def parse_input_file(file: TextIO) -> tuple[int, list[Ship], list[ParsedOperation]]:
    """Parses the entire input file stream."""

    if not (lines := list(file)):
        raise ParseError("Input file is empty.")

    # Line 1: Board Size
    try:
        size = parse_board_size(lines[0])
    except ParseError as e:
        raise ParseError(f"Error on line 1 (Board Size): {e}") from e

    if len(lines) < 2:
        # Allow simulations with no operations, but size and ships are required.
        initial_ships_line = ""
        operation_lines = []
        if lines:  # Check if there's at least a size line
            raise ParseError(
                "Input file must contain at least board size and initial ships line."
            )
            # If only size is given, still raise error as ship line is mandatory.
    else:
        initial_ships_line = lines[1]
        operation_lines = lines[2:]

    # Line 2: Initial Ships
    try:
        initial_ships = parse_initial_ships(initial_ships_line)
    except ParseError as e:
        raise ParseError(f"Error on line 2 (Initial Ships): {e}") from e

    # Subsequent Lines: Operations
    operations: list[ParsedOperation] = []
    for i, line in enumerate(operation_lines, start=3):
        if not (stripped_line := line.strip()):
            continue
        try:
            # parse_operation now guaranteed to return ParsedOperation or raise
            op = parse_operation(stripped_line)
            operations.append(op)
        except ParseError as e:
            raise ParseError(f"Error on line {i}: {e}") from e
        except ValueError as e:
            # Catch potential errors from Position int conversion if regex somehow fails
            raise ParseError(
                f"Error on line {i}: Invalid number format in operation '{line}'. {e}"
            ) from e

    return size, initial_ships, operations
