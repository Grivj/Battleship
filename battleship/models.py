from dataclasses import dataclass
from enum import Enum, auto


class Orientation(Enum):
    N = auto()
    E = auto()
    S = auto()
    W = auto()

    def rotate_left(self) -> "Orientation":
        """Rotates the orientation 90 degrees counter-clockwise."""
        match self:
            case Orientation.N:
                return Orientation.W
            case Orientation.W:
                return Orientation.S
            case Orientation.S:
                return Orientation.E
            case Orientation.E:
                return Orientation.N

    def rotate_right(self) -> "Orientation":
        """Rotates the orientation 90 degrees clockwise."""
        match self:
            case Orientation.N:
                return Orientation.E
            case Orientation.E:
                return Orientation.S
            case Orientation.S:
                return Orientation.W
            case Orientation.W:
                return Orientation.N

    def to_vector(self) -> tuple[int, int]:
        """Returns the change in (x, y) for moving one step in this orientation."""
        match self:
            case Orientation.N:
                return (0, 1)
            case Orientation.E:
                return (1, 0)
            case Orientation.S:
                return (0, -1)
            case Orientation.W:
                return (-1, 0)


class OperationType(Enum):
    MOVE = auto()
    SHOOT = auto()


class MoveCommand(Enum):
    L = auto()
    R = auto()
    M = auto()


@dataclass(frozen=True)
class Position:
    """
    Represents a position on the board. Frozen for immutability and hashability.
    """

    x: int
    y: int

    def move(self, orientation: Orientation) -> "Position":
        """Calculates the new position after moving one step in the given orientation."""
        dx, dy = orientation.to_vector()
        return Position(self.x + dx, self.y + dy)


@dataclass
class Ship:
    position: Position
    orientation: Orientation
    sunk: bool = False

    def rotate_left(self) -> None:
        """Rotates the ship 90 degrees counter-clockwise."""
        self.orientation = self.orientation.rotate_left()

    def rotate_right(self) -> None:
        """Rotates the ship 90 degrees clockwise."""
        self.orientation = self.orientation.rotate_right()

    def move_forward(self) -> None:
        """Moves the ship one step forward in its current orientation."""
        self.position = self.position.move(self.orientation)

    def sink(self) -> None:
        """Marks the ship as sunk."""
        self.sunk = True

    def __str__(self) -> str:
        status = " SUNK" if self.sunk else ""
        return (
            f"({self.position.x}, {self.position.y}, {self.orientation.name}){status}"
        )
