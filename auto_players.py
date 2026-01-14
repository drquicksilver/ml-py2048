from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

from game2048 import Board, add_random_tile, slide_down, slide_left, slide_right, slide_up

MOVE_DIRECTIONS = ["up", "right", "down", "left"]


@dataclass(frozen=True)
class StrategySpec:
    name: str
    factory: Callable[[], object]
    source: str


def legal_moves(board: Board) -> List[str]:
    moves = []
    for direction, mover in _move_map().items():
        _new_board, changed = mover(board)
        if changed:
            moves.append(direction)
    return moves


def legal_moves_from_grid(grid: Iterable[Iterable[int]]) -> List[str]:
    board = Board.from_rows(grid)
    return legal_moves(board)


def apply_move(board: Board, direction: str) -> Board:
    mover = _move_map().get(direction)
    if mover is None:
        raise ValueError(f"Unknown direction: {direction}")
    new_board, _changed = mover(board)
    return new_board


def max_tile(board: Board) -> int:
    return max(value for row in board.grid for value in row)


def spawn_tile(board: Board, rng) -> Board:
    return add_random_tile(board, rng=rng)


def load_strategies(directory: Path) -> Tuple[List[StrategySpec], List[str]]:
    strategies: List[StrategySpec] = []
    errors: List[str] = []
    if not directory.exists():
        return strategies, errors

    for path in sorted(directory.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module_name = f"strategy_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            errors.append(f"Failed to load spec for {path.name}")
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        strategy = getattr(module, "STRATEGY", None)
        if not isinstance(strategy, dict):
            continue
        name = strategy.get("name")
        factory = strategy.get("factory")
        if not isinstance(name, str) or not callable(factory):
            continue
        strategies.append(StrategySpec(name=name, factory=factory, source=path.stem))

    name_counts = {}
    for spec in strategies:
        name_counts[spec.name] = name_counts.get(spec.name, 0) + 1
    final_strategies = []
    for spec in strategies:
        if name_counts[spec.name] > 1:
            name = f"{spec.name} ({spec.source})"
        else:
            name = spec.name
        final_strategies.append(StrategySpec(name=name, factory=spec.factory, source=spec.source))

    return final_strategies, errors


def _move_map():
    return {
        "left": slide_left,
        "right": slide_right,
        "up": slide_up,
        "down": slide_down,
    }
