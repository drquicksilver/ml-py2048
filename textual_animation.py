from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from game2048 import Board

FRAME_DELAY = 0.05

# Merge highlight hierarchy (progressively more dramatic):
# - 4: simple asterisks around the value, no color.
# - 8: keep the current highlight (asterisks + bold yellow).
# - 16: same as 8 (subtle step up).
# - 32: compass points (N/S in borders, E/W inside the cell).
# - 64: compass + diagonal corners (extra border/corner asterisks).
# - 128+: compass + diagonal corners + pulsing color.


def merge_level(merge_value: int) -> int:
    if merge_value >= 128:
        return 6
    if merge_value >= 64:
        return 5
    if merge_value >= 32:
        return 4
    if merge_value >= 8:
        return 2
    if merge_value >= 4:
        return 1
    return 0


def merge_color(level: int, pulse_color: Optional[str]) -> Optional[str]:
    if level >= 6 and pulse_color:
        return f"bold {pulse_color}"
    if level >= 2:
        return "bold yellow"
    return None


def horizontal_star_positions(segment_len: int, merge_value: int) -> Set[int]:
    level = merge_level(merge_value)
    if level < 4:
        return set()
    positions = {segment_len // 2}
    if level >= 5:
        positions.update({0, segment_len - 1})
    if level >= 6 and segment_len >= 3:
        positions.update({1, segment_len - 2})
    return positions


def decorate_cell_chars(
    cell_chars: List[str], value_start: int, value_end: int, level: int
) -> Tuple[List[str], Set[int]]:
    width = len(cell_chars)
    positions: Set[int] = set()

    def place(index: int) -> None:
        if index < 0 or index >= width:
            return
        if value_start <= index < value_end:
            return
        cell_chars[index] = "*"
        positions.add(index)

    if level >= 1:
        place(value_start - 1)
        place(value_end)
    if level >= 4:
        place(value_start - 2)
        place(value_end + 1)
    if level >= 5:
        place(0)
        place(width - 1)
    if level >= 6:
        place(1)
        place(width - 2)
    return cell_chars, positions


def merge_pulse_sequence(
    merge_values: Dict[Tuple[int, int], int],
) -> Tuple[List[Optional[str]], float]:
    if not merge_values:
        return [None], FRAME_DELAY
    max_merge = max(merge_values.values())
    if max_merge >= 2048:
        colors = ["red", "magenta", "yellow", "green", "cyan", "white", "blue", "red"]
        delay = FRAME_DELAY * 3.2
    elif max_merge >= 1024:
        colors = ["red", "magenta", "yellow", "green", "cyan", "white", "red"]
        delay = FRAME_DELAY * 2.9
    elif max_merge >= 512:
        colors = ["red", "magenta", "yellow", "green", "cyan", "white"]
        delay = FRAME_DELAY * 2.5
    elif max_merge >= 256:
        colors = ["red", "magenta", "yellow", "cyan", "white"]
        delay = FRAME_DELAY * 2.2
    elif max_merge >= 128:
        colors = ["red", "yellow", "white", "red"]
        delay = FRAME_DELAY * 2
    elif max_merge >= 64:
        colors = ["yellow", "white"]
        delay = FRAME_DELAY * 1.5
    else:
        colors = [None]
        delay = FRAME_DELAY
    return colors, delay


class MovePlan:
    def __init__(
        self,
        size: int,
        moves: List[Tuple[int, int, int, int, int]],
        merge_values: Dict[Tuple[int, int], int],
    ) -> None:
        self.size = size
        self.moves = moves
        self.merge_values = merge_values
        self.max_steps = self._compute_max_steps()

    def _compute_max_steps(self) -> int:
        max_steps = 0
        for start_row, start_col, end_row, end_col, _value in self.moves:
            max_steps = max(max_steps, abs(end_row - start_row) + abs(end_col - start_col))
        return max_steps

    def grid_for_step(self, step: int) -> List[List[int]]:
        grid = [[0] * self.size for _ in range(self.size)]
        for start_row, start_col, end_row, end_col, value in self.moves:
            row = _step_position(start_row, end_row, step)
            col = _step_position(start_col, end_col, step)
            grid[row][col] = value
        return grid


def plan_move(board: Board, direction: str) -> MovePlan:
    if direction in {"left", "right"}:
        return _plan_horizontal(board, direction)
    return _plan_vertical(board, direction)


def _step_position(start: int, end: int, step: int) -> int:
    distance = abs(end - start)
    if distance == 0:
        return start
    travel = min(step, distance)
    direction = 1 if end > start else -1
    return start + direction * travel


def _plan_horizontal(board: Board, direction: str) -> MovePlan:
    size = board.size
    moves: List[Tuple[int, int, int, int, int]] = []
    merge_values: Dict[Tuple[int, int], int] = {}
    for row_index, row in enumerate(board.grid):
        if direction == "left":
            row_moves, row_merges = _plan_row_left(row)
            for start_col, end_col, value in row_moves:
                moves.append((row_index, start_col, row_index, end_col, value))
            for col_index, merge_value in row_merges.items():
                merge_values[(row_index, col_index)] = merge_value
        else:
            reversed_row = list(reversed(row))
            row_moves, row_merges = _plan_row_left(reversed_row)
            for start_col, end_col, value in row_moves:
                start = size - 1 - start_col
                end = size - 1 - end_col
                moves.append((row_index, start, row_index, end, value))
            for col_index, merge_value in row_merges.items():
                merge_values[(row_index, size - 1 - col_index)] = merge_value
    return MovePlan(size=size, moves=moves, merge_values=merge_values)


def _plan_vertical(board: Board, direction: str) -> MovePlan:
    size = board.size
    moves: List[Tuple[int, int, int, int, int]] = []
    merge_values: Dict[Tuple[int, int], int] = {}
    for col_index in range(size):
        column = [board.grid[row_index][col_index] for row_index in range(size)]
        if direction == "up":
            col_moves, col_merges = _plan_row_left(column)
            for start_row, end_row, value in col_moves:
                moves.append((start_row, col_index, end_row, col_index, value))
            for row_index, merge_value in col_merges.items():
                merge_values[(row_index, col_index)] = merge_value
        else:
            reversed_col = list(reversed(column))
            col_moves, col_merges = _plan_row_left(reversed_col)
            for start_row, end_row, value in col_moves:
                start = size - 1 - start_row
                end = size - 1 - end_row
                moves.append((start, col_index, end, col_index, value))
            for row_index, merge_value in col_merges.items():
                merge_values[(size - 1 - row_index, col_index)] = merge_value
    return MovePlan(size=size, moves=moves, merge_values=merge_values)


def _plan_row_left(row: List[int]) -> Tuple[List[Tuple[int, int, int]], Dict[int, int]]:
    targets: List[dict] = []
    moves: List[Tuple[int, int, int]] = []
    merge_targets: Dict[int, int] = {}
    write_index = 0
    for index, value in enumerate(row):
        if value == 0:
            continue
        if targets and targets[-1]["value"] == value and not targets[-1]["merged"]:
            target = targets[-1]
            target["value"] = int(target["value"]) * 2
            target["merged"] = True
            end_index = int(target["index"])
            merge_targets[end_index] = int(target["value"])
            moves.append((index, end_index, value))
        else:
            end_index = write_index
            targets.append({"value": value, "index": end_index, "merged": False})
            write_index += 1
            moves.append((index, end_index, value))
    return moves, merge_targets
