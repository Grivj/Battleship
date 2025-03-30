import io

import pytest

from battleship.models import MoveCommand, OperationType, Orientation, Position, Ship
from battleship.parser import (
    ParseError,
    parse_board_size,
    parse_initial_ships,
    parse_input_file,
    parse_move_sequence,
    parse_operation,
)


def test_parse_board_size_valid():
    assert parse_board_size("10") == 10
    assert parse_board_size(" 5 \n") == 5


def test_parse_board_size_invalid():
    with pytest.raises(ParseError, match="Invalid board size format"):
        parse_board_size("abc")
    with pytest.raises(ParseError, match="Invalid board size format"):
        parse_board_size("5.5")
    with pytest.raises(ParseError, match="Invalid board size format"):
        parse_board_size("")  # Empty string


def test_parse_board_size_zero_or_negative():
    with pytest.raises(ParseError, match="Board size must be a positive integer"):
        parse_board_size("0")
    with pytest.raises(ParseError, match="Board size must be a positive integer"):
        parse_board_size("-5")


def test_parse_initial_ships_valid():
    line = "(0, 0, N) (9, 2, E) ( 5 , 5 , s )"
    expected_ships = [
        Ship(Position(0, 0), Orientation.N),
        Ship(Position(9, 2), Orientation.E),
        Ship(Position(5, 5), Orientation.S),
    ]
    parsed_ships = parse_initial_ships(line)
    # Compare attrs since dataclasses instances won't be identical
    assert len(parsed_ships) == len(expected_ships)
    for parsed, expected in zip(parsed_ships, expected_ships):
        assert parsed.position == expected.position
        assert parsed.orientation == expected.orientation
        assert parsed.sunk == expected.sunk  # Default should be False


def test_parse_initial_ships_single():
    line = "(1, 1, W)"
    expected_ships = [Ship(Position(1, 1), Orientation.W)]
    parsed_ships = parse_initial_ships(line)
    assert len(parsed_ships) == len(expected_ships)
    assert parsed_ships[0].position == expected_ships[0].position
    assert parsed_ships[0].orientation == expected_ships[0].orientation


def test_parse_initial_ships_empty():
    line = "  "
    assert parse_initial_ships(line) == []


def test_parse_initial_ships_invalid_format():
    with pytest.raises(ParseError, match="Invalid characters or format"):
        parse_initial_ships("(0, 0, N) abc (1, 1, E)")
    with pytest.raises(ParseError, match="Invalid characters or format"):
        parse_initial_ships("(0, 0, N), (1, 1, E)")  # Comma invalid
    with pytest.raises(ParseError, match="Invalid trailing characters or format"):
        parse_initial_ships("(0, 0, N) (1, 1, E) extra")
    with pytest.raises(
        ParseError, match=r"Invalid trailing characters or format.*\(0, 0, X\)"
    ):
        parse_initial_ships("(0, 0, X)")
    with pytest.raises(
        ParseError, match=r"Invalid trailing characters or format.*\(a, 0, N\)"
    ):
        parse_initial_ships("(a, 0, N)")
    with pytest.raises(
        ParseError, match=r"Invalid trailing characters or format.*'abc'"
    ):
        parse_initial_ships("abc")


def test_parse_operation_shoot_valid():
    assert parse_operation("(1, 2)") == (OperationType.SHOOT, Position(1, 2))
    assert parse_operation(" ( 5 , 9 ) ") == (OperationType.SHOOT, Position(5, 9))


def test_parse_operation_move_valid():
    assert parse_operation("(0, 0) MRMLMM") == (
        OperationType.MOVE,
        Position(0, 0),
        [
            MoveCommand.M,
            MoveCommand.R,
            MoveCommand.M,
            MoveCommand.L,
            MoveCommand.M,
            MoveCommand.M,
        ],
    )
    assert parse_operation(" ( 3, 4 ) LmR \n") == (
        OperationType.MOVE,
        Position(3, 4),
        [MoveCommand.L, MoveCommand.M, MoveCommand.R],
    )


def test_parse_operation_invalid():
    with pytest.raises(ParseError, match="Invalid operation format"):
        parse_operation("(1, 2) abc")  # Invalid move sequence chars
    with pytest.raises(ParseError, match="Invalid operation format"):
        parse_operation("shoot (1, 2)")  # Wrong format
    with pytest.raises(ParseError, match="Invalid operation format"):
        parse_operation("(1, 2, N)")  # Looks like ship, not op
    with pytest.raises(ParseError, match="Invalid operation format"):
        parse_operation("(1, 2) LRM extra")  # Extra chars after move
    with pytest.raises(ParseError, match="Invalid operation format"):
        parse_operation("(a, 2) LRM")  # Invalid coord
    with pytest.raises(ParseError, match="Invalid operation format"):
        parse_operation("(1, b)")  # Invalid coord


def test_parse_input_file_valid_example():
    input_data = """
    10
    (0, 0, N) (9, 2, E)
    (0, 0) MRMLMM
    (9, 2)
    """
    file = io.StringIO(
        input_data.strip()
    )  # Use strip to remove leading/trailing blank lines

    size, initial_ships, operations = parse_input_file(file)

    assert size == 10
    assert len(initial_ships) == 2
    assert initial_ships[0].position == Position(0, 0)
    assert initial_ships[0].orientation == Orientation.N
    assert initial_ships[1].position == Position(9, 2)
    assert initial_ships[1].orientation == Orientation.E

    assert len(operations) == 2
    assert operations[0] == (
        OperationType.MOVE,
        Position(0, 0),
        [
            MoveCommand.M,
            MoveCommand.R,
            MoveCommand.M,
            MoveCommand.L,
            MoveCommand.M,
            MoveCommand.M,
        ],
    )
    assert operations[1] == (OperationType.SHOOT, Position(9, 2))


def test_parse_input_file_no_operations():
    input_data = """
    5
    (1, 1, S) (3, 3, W)
    """
    file = io.StringIO(input_data.strip())
    size, initial_ships, operations = parse_input_file(file)
    assert size == 5
    assert len(initial_ships) == 2
    assert initial_ships[0].position == Position(1, 1)
    assert initial_ships[1].position == Position(3, 3)
    assert operations == []


def test_parse_input_file_empty_ships_line():
    input_data = """
    8

    (0, 0) M
    (1, 1)
    """
    file = io.StringIO(input_data.strip())
    size, initial_ships, operations = parse_input_file(file)
    assert size == 8
    assert initial_ships == []
    assert len(operations) == 2
    assert operations[0] == (OperationType.MOVE, Position(0, 0), [MoveCommand.M])
    assert operations[1] == (OperationType.SHOOT, Position(1, 1))


def test_parse_input_file_empty_lines_ignored():
    input_data_blank_line_2 = """
    10

    (0, 0, N) (9, 2, E)


    (0, 0) MRMLMM

    (9, 2)

    """
    with pytest.raises(
        ParseError,
        match=r"Error on line 3.*Invalid operation format: '\(0, 0, N\) \(9, 2, E\)'",
    ):
        parse_input_file(io.StringIO(input_data_blank_line_2.strip()))

    input_data_blanks_in_ops = """
    10
    (0, 0, N) (9, 2, E)

    (0, 0) MRMLMM

    (9, 2)

    """
    file = io.StringIO(input_data_blanks_in_ops.strip())
    size, initial_ships, operations = parse_input_file(file)
    assert size == 10
    assert len(initial_ships) == 2
    assert len(operations) == 2
    assert operations[0] == (
        OperationType.MOVE,
        Position(0, 0),
        [
            MoveCommand.M,
            MoveCommand.R,
            MoveCommand.M,
            MoveCommand.L,
            MoveCommand.M,
            MoveCommand.M,
        ],
    )
    assert operations[1] == (OperationType.SHOOT, Position(9, 2))


def test_parse_input_file_error_handling():
    # Error on line 1
    input_data_bad_size = "abc\n(0, 0, N)\n(0, 0) M"
    file = io.StringIO(input_data_bad_size)
    with pytest.raises(ParseError, match="Error on line 1.*Invalid board size format"):
        parse_input_file(file)

    # Error on line 2
    input_data_bad_ships = "10\n(0, 0, X)\n(0, 0) M"
    file = io.StringIO(input_data_bad_ships)
    with pytest.raises(
        ParseError,
        match=r"Error on line 2 \(Initial Ships\): Invalid trailing characters.*\(0, 0, X\)",
    ):
        parse_input_file(file)

    # Error on line 3 (first operation)
    input_data_bad_op1 = "10\n(0, 0, N)\n(0, 0) MX"
    file = io.StringIO(input_data_bad_op1)
    with pytest.raises(ParseError, match="Error on line 3.*Invalid operation format"):
        parse_input_file(file)

    # Error on line 4 (second operation)
    input_data_bad_op2 = "10\n(0, 0, N)\n(0, 0) M\nshoot (1, 1)"
    file = io.StringIO(input_data_bad_op2)
    with pytest.raises(ParseError, match="Error on line 4.*Invalid operation format"):
        parse_input_file(file)


def test_parse_input_file_empty_file():
    file = io.StringIO("")
    with pytest.raises(ParseError, match="Input file is empty"):
        parse_input_file(file)


def test_parse_input_file_missing_lines():
    file = io.StringIO("10\n")
    with pytest.raises(
        ParseError, match="must contain at least board size and initial ships line"
    ):
        parse_input_file(file)


def test_parse_move_sequence_valid():
    assert parse_move_sequence("LMR") == [MoveCommand.L, MoveCommand.M, MoveCommand.R]
    assert parse_move_sequence("mrmlmm") == [
        MoveCommand.M,
        MoveCommand.R,
        MoveCommand.M,
        MoveCommand.L,
        MoveCommand.M,
        MoveCommand.M,
    ]
    assert parse_move_sequence("") == []


def test_parse_move_sequence_invalid():
    with pytest.raises(ParseError, match="Invalid character 'X'"):
        parse_move_sequence("LRMX")
