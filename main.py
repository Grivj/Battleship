import argparse
import logging
import sys
from pathlib import Path

from battleship.game import Board, BoardError
from battleship.models import OperationType, Ship
from battleship.parser import ParsedOperation, ParseError, parse_input_file

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _load_simulation_setup(
    filepath: Path,
) -> tuple[int, list[Ship], list[ParsedOperation]]:
    """Loads and parses the simulation setup from the input file."""
    logger.info(f"Reading simulation setup from: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return parse_input_file(f)
    except FileNotFoundError:
        logger.error(f"Input file not found at '{filepath}'")
        raise
    except ParseError as e:
        logger.error(f"Error parsing input file '{filepath}':\n{e}")
        raise
    except Exception as e:  # Catch other potential file reading errors
        logger.exception(f"Failed to read or parse input file '{filepath}'")
        raise RuntimeError(f"Failed to read or parse input file '{filepath}'") from e


def _write_simulation_results(filepath: Path, final_states: list[str]) -> None:
    """Writes the final ship states to the output file."""
    logger.info(f"Writing {len(final_states)} final ship state(s) to: {filepath}")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for state in final_states:
                f.write(state + "\n")
        logger.info("Output written successfully.")
    except IOError as e:
        logger.exception(f"Failed to write output file '{filepath}'")
        raise RuntimeError(f"Failed to write output file '{filepath}'") from e


def _execute_operation(board: Board, operation: ParsedOperation, op_index: int) -> None:
    """Executes a single parsed operation on the board."""
    op_type = operation[0]
    try:
        if op_type is OperationType.MOVE:
            assert len(operation) == 3, "Move operation tuple should have 3 elements"
            _, start_pos, sequence = operation
            board.apply_move_sequence(start_pos, sequence)
        elif op_type is OperationType.SHOOT:
            assert len(operation) == 2, "Shoot operation tuple should have 2 elements"
            _, target_pos = operation
            board.apply_shoot(target_pos)
        else:
            # Should not happen if parser is correct, but defensive check
            logger.error(
                f"Unknown operation type '{op_type}' encountered at index {op_index}."
            )
    except (BoardError, ValueError) as e:
        # Log operation errors as warnings and continue simulation
        logger.warning(f"Error during operation {op_index} ({operation}): {e}")


def main():
    """Main function to run the battleship simulation."""
    parser = argparse.ArgumentParser(
        description="Simulate battleship movements and shots based on an input file."
    )
    parser.add_argument("input_file", help="Path to the input file.")
    parser.add_argument("output_file", help="Path to the output file.")
    args = parser.parse_args()

    # Construct full paths using input/ and output/ directories
    input_dir = Path("input")
    output_dir = Path("output")
    input_filepath = input_dir / args.input_file
    output_filepath = output_dir / args.output_file

    # Ensure output directory exists (optional but good practice)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load setup
        size, initial_ships, operations = _load_simulation_setup(input_filepath)

        # Initialize board
        logger.info(f"Initializing board of size {size}x{size}.")
        board = Board(size)

        # Add initial ships (keep error handling here as it's critical setup)
        logger.info(f"Placing {len(initial_ships)} initial ship(s)...")
        for ship in initial_ships:
            try:
                board.add_ship(ship)
            except BoardError as e:
                logger.error(f"Critical Error: Failed adding initial ship {ship}: {e}")
                sys.exit(1)  # Exit on critical initial setup error

        logger.info(f"Applying {len(operations)} operation(s)...")
        for i, op in enumerate(operations, start=1):
            _execute_operation(board, op, i)

        _write_simulation_results(output_filepath, board.get_final_ship_states())

    except (FileNotFoundError, ParseError, BoardError, ValueError, RuntimeError) as e:
        # Catch errors raised/re-raised from helpers or board setup
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)
    except Exception as e:
        # Catch any other unexpected errors
        logger.exception(f"An unexpected critical error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
