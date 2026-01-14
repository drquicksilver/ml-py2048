# AGENTS.md

## Repository structure
- `main.py`: entry point that builds a demo board and launches the Textual UI.
- `game2048.py`: core board data structure and move/random-tile logic.
- `textual_board.py`: Textual rendering + key handling for board updates.
- `tests/`: unit tests for the 2048 logic.
- `pyproject.toml` / `uv.lock`: project metadata and dependency lock.

## Workflow
- After making code changes, run the test suite:
  - `uv run test`
