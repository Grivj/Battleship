import pytest

from battleship.game import Board, BoardError
from battleship.models import MoveCommand, Orientation, Position, Ship


def test_board_init_valid():
    board = Board(10)
    assert board.size == 10
    assert board._ships == {}
    assert board._initial_ships_order == []


def test_board_init_invalid_size():
    with pytest.raises(ValueError, match="Board size must be positive"):
        Board(0)
    with pytest.raises(ValueError, match="Board size must be positive"):
        Board(-5)


@pytest.mark.parametrize(
    "pos, size, expected",
    [
        (Position(0, 0), 10, True),
        (Position(9, 9), 10, True),
        (Position(5, 5), 10, True),
        (Position(-1, 0), 10, False),
        (Position(0, -1), 10, False),
        (Position(10, 5), 10, False),
        (Position(5, 10), 10, False),
        (Position(0, 0), 1, True),
        (Position(1, 0), 1, False),
    ],
)
def test_board_is_within_bounds(pos: Position, size: int, expected: bool):
    board = Board(size)
    assert board.is_within_bounds(pos) == expected


def test_board_add_ship_valid():
    board = Board(10)
    ship1 = Ship(Position(0, 0), Orientation.N)
    ship2 = Ship(Position(5, 5), Orientation.E)
    board.add_ship(ship1)
    board.add_ship(ship2)
    assert board.get_ship_at(Position(0, 0)) is ship1
    assert board.get_ship_at(Position(5, 5)) is ship2
    assert board._initial_ships_order == [ship1, ship2]


def test_board_add_ship_out_of_bounds():
    board = Board(5)
    ship = Ship(Position(5, 0), Orientation.N)
    with pytest.raises(BoardError, match="Position .* is out of bounds"):
        board.add_ship(ship)


def test_board_add_ship_collision():
    board = Board(10)
    ship1 = Ship(Position(1, 1), Orientation.N)
    ship2 = Ship(Position(1, 1), Orientation.E)
    board.add_ship(ship1)
    with pytest.raises(BoardError, match="Position .* is already occupied by .*"):
        board.add_ship(ship2)


def test_board_apply_shoot_hit():
    board = Board(10)
    ship = Ship(Position(3, 3), Orientation.S)
    board.add_ship(ship)
    assert not ship.sunk
    board.apply_shoot(Position(3, 3))
    assert ship.sunk
    # Ship should still be findable at its position
    assert board.get_ship_at(Position(3, 3)) is ship


def test_board_apply_shoot_miss():
    board = Board(10)
    ship = Ship(Position(3, 3), Orientation.S)
    board.add_ship(ship)
    board.apply_shoot(Position(4, 4))
    assert not ship.sunk
    assert board.get_ship_at(Position(4, 4)) is None


def test_board_apply_shoot_already_sunk():
    board = Board(10)
    ship = Ship(Position(3, 3), Orientation.S, sunk=True)
    board.add_ship(ship)
    board.apply_shoot(Position(3, 3))  # Shoot again (does nothing)
    assert ship.sunk  # Should remain sunk


def test_board_apply_shoot_out_of_bounds():
    board = Board(10)
    ship = Ship(Position(0, 0), Orientation.N)
    board.add_ship(ship)
    board.apply_shoot(Position(10, 10))  # No error expected, just ignored
    assert not ship.sunk


def test_board_apply_move_sequence_simple():
    board = Board(10)
    ship = Ship(Position(1, 2), Orientation.N)
    board.add_ship(ship)
    start_pos = Position(1, 2)

    # Sequence: Move, Right, Move
    sequence = [MoveCommand.M, MoveCommand.R, MoveCommand.M]
    board.apply_move_sequence(start_pos, sequence)

    # Expected: (1, 2)N -> M -> (1, 3)N -> R -> (1, 3)E -> M -> (2, 3)E
    assert ship.position == Position(2, 3)
    assert ship.orientation == Orientation.E
    assert board.get_ship_at(start_pos) is None  # Original position is empty
    assert board.get_ship_at(Position(2, 3)) is ship  # Ship is at new position


def test_board_apply_move_sequence_rotate_only():
    board = Board(10)
    ship = Ship(Position(5, 5), Orientation.W)
    board.add_ship(ship)
    start_pos = Position(5, 5)

    # Sequence: LRLR
    sequence = [MoveCommand.L, MoveCommand.R, MoveCommand.L, MoveCommand.R]
    board.apply_move_sequence(start_pos, sequence)

    assert ship.position == Position(5, 5)  # Position unchanged
    assert ship.orientation == Orientation.W
    assert board.get_ship_at(start_pos) is ship  # Still at original position


def test_board_apply_move_sequence_move_off_board():
    board = Board(5)  # 0-4
    ship = Ship(Position(4, 4), Orientation.N)
    board.add_ship(ship)
    start_pos = Position(4, 4)

    sequence = [MoveCommand.M]
    with pytest.raises(BoardError, match=r"Target .* out of bounds .* on step"):
        board.apply_move_sequence(start_pos, sequence)

    # Ship state should not have changed
    assert ship.position == start_pos
    assert ship.orientation == Orientation.N
    assert board.get_ship_at(start_pos) is ship


def test_board_apply_move_sequence_ends_on_occupied_cell():
    board = Board(10)
    ship1 = Ship(Position(1, 1), Orientation.N)
    ship2 = Ship(Position(1, 2), Orientation.S)  # Target cell
    board.add_ship(ship1)
    board.add_ship(ship2)
    start_pos = Position(1, 1)

    sequence = [MoveCommand.M]
    with pytest.raises(BoardError, match=r"Collision at .* with .*!"):
        board.apply_move_sequence(start_pos, sequence)

    # Ship1 state should not have changed
    assert ship1.position == start_pos
    assert ship1.orientation == Orientation.N
    assert board.get_ship_at(start_pos) is ship1
    # Ship2 state unchanged
    assert ship2.position == Position(1, 2)
    assert board.get_ship_at(Position(1, 2)) is ship2


def test_board_apply_move_sequence_moves_through_occupied_cell():
    board = Board(10)
    ship1 = Ship(Position(1, 1), Orientation.N)
    ship2 = Ship(Position(1, 2), Orientation.S)  # Intermediate cell
    # ship3 not needed for this part of the test
    board.add_ship(ship1)
    board.add_ship(ship2)
    start_pos = Position(1, 1)

    # Move ship1 North twice (through ship2's initial spot, ends on empty (1,3))
    sequence = [MoveCommand.M, MoveCommand.M]
    board.apply_move_sequence(start_pos, sequence)

    # Expected: (1, 1)N -> M -> (1, 2)N -> M -> (1, 3)N
    # Should succeed because only the *final* position is checked for collision
    assert ship1.position == Position(1, 3)
    assert ship1.orientation == Orientation.N
    assert board.get_ship_at(start_pos) is None
    assert board.get_ship_at(Position(1, 2)) is ship2  # ship2 is untouched
    assert board.get_ship_at(Position(1, 3)) is ship1  # ship1 moved here

    # Reset and test collision at the end
    board = Board(10)
    ship1 = Ship(Position(1, 1), Orientation.N)
    ship2 = Ship(Position(1, 2), Orientation.S)  # Intermediate cell
    ship3 = Ship(Position(1, 3), Orientation.W)  # Final cell IS occupied
    board.add_ship(ship1)
    board.add_ship(ship2)
    board.add_ship(ship3)
    start_pos = Position(1, 1)

    sequence = [MoveCommand.M, MoveCommand.M]
    with pytest.raises(BoardError, match=r"Collision at .* with .*!"):
        board.apply_move_sequence(start_pos, sequence)


def test_board_apply_move_sequence_no_ship_at_start():
    board = Board(10)
    sequence = [MoveCommand.M]
    with pytest.raises(BoardError, match="No ship found at starting position"):
        board.apply_move_sequence(Position(0, 0), sequence)


def test_board_apply_move_sequence_sunk_ship():
    board = Board(10)
    ship = Ship(Position(1, 1), Orientation.N, sunk=True)
    board.add_ship(ship)
    start_pos = Position(1, 1)

    # Attempt to move sunk ship - should do nothing, no error
    sequence = [MoveCommand.M]
    board.apply_move_sequence(start_pos, sequence)

    assert ship.position == start_pos
    assert ship.orientation == Orientation.N
    assert ship.sunk
    assert board.get_ship_at(start_pos) is ship


def test_board_apply_move_sequence_ends_at_start_pos():
    board = Board(10)
    ship = Ship(Position(1, 1), Orientation.N)
    board.add_ship(ship)
    start_pos = Position(1, 1)

    # Move sequence that returns to origin: N -> M -> (1,2) -> R -> E -> M -> (2,2) -> R -> S -> M -> (2,1) -> R -> W -> M -> (1,1)
    sequence = [
        MoveCommand.M,
        MoveCommand.R,
        MoveCommand.M,
        MoveCommand.R,
        MoveCommand.M,
        MoveCommand.R,
        MoveCommand.M,
    ]
    board.apply_move_sequence(start_pos, sequence)

    assert ship.position == start_pos
    assert ship.orientation == Orientation.W  # Final orientation after sequence
    assert board.get_ship_at(start_pos) is ship


def test_board_apply_move_sequence_ends_at_start_pos_occupied_by_another():
    # This tests if the check `if colliding_ship is not ship_to_move:` works
    board = Board(10)
    ship1 = Ship(Position(1, 1), Orientation.N)
    ship2 = Ship(Position(2, 1), Orientation.W)
    board.add_ship(ship1)
    board.add_ship(ship2)
    start_pos1 = Position(1, 1)

    # Sequence for ship1: N -> M -> (1,2) -> R -> E -> M -> (2,2) -> R -> S -> M -> (2,1)
    # This ends where ship2 is. Should collide.
    sequence = [
        MoveCommand.M,
        MoveCommand.R,
        MoveCommand.M,
        MoveCommand.R,
        MoveCommand.M,
    ]
    with pytest.raises(BoardError, match=r"Collision at .* with .*!"):
        board.apply_move_sequence(start_pos1, sequence)

    assert ship1.position == start_pos1  # ship1 should not have moved
    assert ship1.orientation == Orientation.N


def test_board_get_final_ship_states():
    board = Board(10)
    ship1 = Ship(Position(0, 0), Orientation.N)
    ship2 = Ship(Position(9, 2), Orientation.E)
    ship3 = Ship(Position(5, 5), Orientation.S)

    board.add_ship(ship1)
    board.add_ship(ship2)
    board.add_ship(ship3)

    # Simulate some operations
    sequence1 = [
        MoveCommand.M,
        MoveCommand.R,
        MoveCommand.M,
        MoveCommand.L,
        MoveCommand.M,
        MoveCommand.M,
    ]
    board.apply_move_sequence(Position(0, 0), sequence1)
    board.apply_shoot(Position(9, 2))  # Sink ship2
    # ship3 remains untouched

    final_states = board.get_final_ship_states()

    assert final_states == [
        "(1, 3, N)",  # ship1 moved
        "(9, 2, E) SUNK",  # ship2 sunk
        "(5, 5, S)",  # ship3 untouched
    ]
