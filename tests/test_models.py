from battleship.models import Orientation, Position, Ship


def test_orientation_rotate_left():
    assert Orientation.N.rotate_left() == Orientation.W
    assert Orientation.W.rotate_left() == Orientation.S
    assert Orientation.S.rotate_left() == Orientation.E
    assert Orientation.E.rotate_left() == Orientation.N


def test_orientation_rotate_right():
    assert Orientation.N.rotate_right() == Orientation.E
    assert Orientation.E.rotate_right() == Orientation.S
    assert Orientation.S.rotate_right() == Orientation.W
    assert Orientation.W.rotate_right() == Orientation.N


def test_orientation_to_vector():
    assert Orientation.N.to_vector() == (0, 1)
    assert Orientation.E.to_vector() == (1, 0)
    assert Orientation.S.to_vector() == (0, -1)
    assert Orientation.W.to_vector() == (-1, 0)


def test_position_move():
    pos = Position(1, 1)
    assert pos.move(Orientation.N) == Position(1, 2)
    assert pos.move(Orientation.E) == Position(2, 1)
    assert pos.move(Orientation.S) == Position(1, 0)
    assert pos.move(Orientation.W) == Position(0, 1)


def test_ship_rotate_left():
    ship = Ship(Position(0, 0), Orientation.N)
    ship.rotate_left()
    assert ship.orientation == Orientation.W
    ship.rotate_left()
    assert ship.orientation == Orientation.S
    ship.rotate_left()
    assert ship.orientation == Orientation.E
    ship.rotate_left()
    assert ship.orientation == Orientation.N


def test_ship_rotate_right():
    ship = Ship(Position(0, 0), Orientation.N)
    ship.rotate_right()
    assert ship.orientation == Orientation.E
    ship.rotate_right()
    assert ship.orientation == Orientation.S
    ship.rotate_right()
    assert ship.orientation == Orientation.W
    ship.rotate_right()
    assert ship.orientation == Orientation.N


def test_ship_move_forward():
    ship = Ship(Position(1, 1), Orientation.N)
    ship.move_forward()
    assert ship.position == Position(1, 2)
    ship.orientation = Orientation.E
    ship.move_forward()
    assert ship.position == Position(2, 2)
    ship.orientation = Orientation.S
    ship.move_forward()
    assert ship.position == Position(2, 1)
    ship.orientation = Orientation.W
    ship.move_forward()
    assert ship.position == Position(1, 1)


def test_ship_sink():
    ship = Ship(Position(0, 0), Orientation.N)
    assert not ship.sunk
    ship.sink()
    assert ship.sunk


def test_ship_str_representation():
    ship = Ship(Position(1, 3), Orientation.N)
    assert str(ship) == "(1, 3, N)"
    ship.sunk = True
    assert str(ship) == "(1, 3, N) SUNK"
