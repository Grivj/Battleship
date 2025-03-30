import logging
from dataclasses import dataclass

from .models import MoveCommand, Position, Ship

logger = logging.getLogger(__name__)


class BoardError(Exception):
    """Custom exception for board-related errors."""

    pass


@dataclass
class Board:
    """Represents the game board and manages ship states."""

    size: int

    def __post_init__(self):
        if self.size <= 0:
            raise ValueError("Board size must be positive.")
        # Store ships mapped by their current position for quick lookup
        # Note: We store the actual Ship objects
        self._ships: dict[Position, Ship] = {}
        # Keep a separate list to maintain the original order for final output
        self._initial_ships_order: list[Ship] = []

    def is_within_bounds(self, position: Position) -> bool:
        """Checks if a position is within the board boundaries."""
        return 0 <= position.x < self.size and 0 <= position.y < self.size

    def add_ship(self, ship: Ship) -> None:
        """Adds a ship to the board at its initial position."""
        logger.debug(f"Attempting to place ship {ship}...")
        if not self.is_within_bounds(ship.position):
            msg = f"Position {ship.position} is out of bounds (Board Size: {self.size}x{self.size})."
            logger.error(f"❌ Failed to add ship {ship}: {msg}")
            raise BoardError(msg)
        if ship.position in self._ships:
            msg = f"Position {ship.position} is already occupied by {self._ships[ship.position]}."
            logger.error(f"❌ Failed to add ship {ship}: {msg}")
            raise BoardError(msg)

        logger.info(f"➕ Placed ship {ship} at {ship.position}")
        self._ships[ship.position] = ship
        self._initial_ships_order.append(ship)

    def get_ship_at(self, position: Position) -> Ship | None:
        """Returns the ship at the given position, or None if empty."""
        return self._ships.get(position)

    def _simulate_move(
        self, start_ship_state: Ship, sequence: list[MoveCommand]
    ) -> Ship:
        """
        Simulates a move sequence step-by-step, checking boundaries.
        Returns the calculated final ship state without modifying the board.
        Raises BoardError if move goes out of bounds, ValueError for invalid chars.
        """
        # Work on a copy to avoid side effects during simulation
        current_ship_state = Ship(
            start_ship_state.position, start_ship_state.orientation
        )
        logger.debug(
            f"➡️ Simulating move: Start={start_ship_state}, Sequence={sequence}"
        )

        for i, command in enumerate(sequence):
            action_taken = "Unknown"
            match command:
                case MoveCommand.L:
                    current_ship_state.rotate_left()
                    action_taken = "Rotated Left"
                case MoveCommand.R:
                    current_ship_state.rotate_right()
                    action_taken = "Rotated Right"
                case MoveCommand.M:
                    potential_next_pos = current_ship_state.position.move(
                        current_ship_state.orientation
                    )
                    if not self.is_within_bounds(potential_next_pos):
                        msg = f"Target {potential_next_pos} out of bounds (Board: {self.size}x{self.size}) on step {i+1}."
                        logger.warning(f"⚠️ Boundary breach during simulation: {msg}")
                        raise BoardError(msg)
                    current_ship_state.move_forward()
                    action_taken = "Moved Forward"
            logger.debug(
                f"   Sim Step {i+1} ({command.name}): {action_taken} -> {current_ship_state}"
            )

        logger.debug(f"🏁 Simulation Result: {current_ship_state}")
        return current_ship_state

    def apply_move_sequence(
        self, start_pos: Position, sequence: list[MoveCommand]
    ) -> None:
        """Applies a sequence of movements to the ship at start_pos."""
        logger.info(f"➡️ Attempting move: Start={start_pos}, Sequence={sequence}")
        if not (ship_to_move := self.get_ship_at(start_pos)):
            logger.warning(f"❌ Move failed: No ship found at {start_pos}!")
            raise BoardError(
                f"No ship found at starting position {start_pos} for move sequence."
            )

        # Requirement isn't explicit, but let's assume sunk ships cannot move
        if ship_to_move.sunk:
            logger.warning(f"🟡 Move ignored: Ship at {start_pos} is already sunk.")
            return

        original_position = ship_to_move.position
        original_ship_state_str = str(ship_to_move)  # Capture state before simulation

        try:
            final_simulated_state = self._simulate_move(ship_to_move, sequence)
        except BoardError as e:
            logger.warning(
                f"❌ Move sequence {sequence} failed for {original_ship_state_str}: {e}"
            )
            raise  # Re-raise the specific error (e.g., out of bounds)
        except ValueError as e:  # Should not happen with Enum but capture just in case
            logger.error(
                f"💥 Unexpected error in move sequence {sequence} for {original_ship_state_str}: {e}"
            )
            raise e

        final_position = final_simulated_state.position
        final_orientation = final_simulated_state.orientation

        colliding_ship = self._ships.get(final_position)
        if (
            final_position != original_position
            and colliding_ship
            and colliding_ship is not ship_to_move
        ):
            msg = f"Collision at {final_position} with {colliding_ship}!"
            logger.warning(
                f"❌ Move sequence {sequence} failed for {original_ship_state_str}: {msg}"
            )
            raise BoardError(msg)

        # Commit the move if simulation and checks passed
        final_state_str = (
            f"({final_position.x}, {final_position.y}, {final_orientation.name})"
        )
        logger.info(
            f"✅ Move committed: {original_ship_state_str} -> {final_state_str}"
        )
        ship_to_move.position = final_position
        ship_to_move.orientation = final_orientation

        if final_position != original_position:
            logger.debug(
                f"   🗺️ Map update: Removing from {original_position}, adding at {final_position}."
            )
            if self._ships.get(original_position) is ship_to_move:
                del self._ships[original_position]
            self._ships[final_position] = ship_to_move
            return

        logger.debug(
            f"   🗺️ Map update: No change needed (ship ended at {original_position})."
        )

    def apply_shoot(self, target_pos: Position) -> None:
        """Applies a shoot operation at the target position."""
        logger.info(f"💥 Applying shoot: Target={target_pos}")
        # Requirement isn't explicit, but let's assume out-of-bounds shots are ignored
        if not self.is_within_bounds(target_pos):
            logger.warning(f"⚠️ Shoot ignored: Target {target_pos} is out of bounds.")
            return

        if not (ship_hit := self.get_ship_at(target_pos)):
            logger.info(f"   ⚪ Shoot at {target_pos}: Miss.")
            return

        if not ship_hit.sunk:
            logger.info(f"   🎯 Shoot at {target_pos}: Hit! Sinking {ship_hit}.")
            ship_hit.sink()
            return

        logger.info(
            f"   🟡 Shoot at {target_pos}: Hit, but {ship_hit} was already sunk."
        )

    def get_final_ship_states(self) -> list[str]:
        """Returns the final state of all ships as strings, preserving initial order."""
        return [str(ship) for ship in self._initial_ships_order]
