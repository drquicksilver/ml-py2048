from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import random


@dataclass(frozen=True)
class Board:
    size: int
    grid: List[List[int]]

    @classmethod
    def from_rows(cls, rows: Iterable[Iterable[int]]) -> "Board":
        grid = [list(row) for row in rows]
        if not grid:
            raise ValueError("Board rows cannot be empty.")
        size = len(grid)
        if any(len(row) != size for row in grid):
            raise ValueError("Board must be square.")
        return cls(size=size, grid=grid)

    def is_full(self) -> bool:
        return all(value != 0 for row in self.grid for value in row)

    def has_moves(self) -> bool:
        if not self.is_full():
            return True
        size = self.size
        for row_index in range(size):
            for col_index in range(size):
                value = self.grid[row_index][col_index]
                if row_index + 1 < size and self.grid[row_index + 1][col_index] == value:
                    return True
                if col_index + 1 < size and self.grid[row_index][col_index + 1] == value:
                    return True
        return False

    def score(self) -> int:
        return sum(tile_score(value) for row in self.grid for value in row)


def tile_score(value: int) -> int:
    if value <= 0:
        return 0
    exponent = 0
    temp = value
    while temp > 1:
        temp //= 2
        exponent += 1
    return 3**exponent


def _merge_row_left(row: Sequence[int]) -> List[int]:
    compact = [value for value in row if value != 0]
    merged: List[int] = []
    i = 0
    while i < len(compact):
        if i + 1 < len(compact) and compact[i] == compact[i + 1]:
            merged.append(compact[i] * 2)
            i += 2
        else:
            merged.append(compact[i])
            i += 1
    merged.extend([0] * (len(row) - len(merged)))
    return merged


def slide_left(board: Board) -> Tuple[Board, bool]:
    new_rows = [_merge_row_left(row) for row in board.grid]
    changed = new_rows != board.grid
    return Board(size=board.size, grid=new_rows), changed


def slide_right(board: Board) -> Tuple[Board, bool]:
    reversed_rows = [list(reversed(row)) for row in board.grid]
    merged = [_merge_row_left(row) for row in reversed_rows]
    new_rows = [list(reversed(row)) for row in merged]
    changed = new_rows != board.grid
    return Board(size=board.size, grid=new_rows), changed


def _transpose(grid: List[List[int]]) -> List[List[int]]:
    return [list(column) for column in zip(*grid)]


def slide_up(board: Board) -> Tuple[Board, bool]:
    transposed = _transpose(board.grid)
    merged = [_merge_row_left(row) for row in transposed]
    new_rows = _transpose(merged)
    changed = new_rows != board.grid
    return Board(size=board.size, grid=new_rows), changed


def slide_down(board: Board) -> Tuple[Board, bool]:
    transposed = _transpose(board.grid)
    reversed_rows = [list(reversed(row)) for row in transposed]
    merged = [_merge_row_left(row) for row in reversed_rows]
    restored = [list(reversed(row)) for row in merged]
    new_rows = _transpose(restored)
    changed = new_rows != board.grid
    return Board(size=board.size, grid=new_rows), changed


def add_random_tile(board: Board, rng: Optional[random.Random] = None) -> Board:
    rng = rng or random.Random()
    empty: List[Tuple[int, int]] = [
        (row_index, col_index)
        for row_index, row in enumerate(board.grid)
        for col_index, value in enumerate(row)
        if value == 0
    ]
    if not empty:
        return board
    row_index, col_index = rng.choice(empty)
    value = 4 if rng.random() < 0.1 else 2
    new_grid = [list(row) for row in board.grid]
    new_grid[row_index][col_index] = value
    return Board(size=board.size, grid=new_grid)
