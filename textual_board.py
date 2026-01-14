from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Set, Tuple

from textual.app import App, ComposeResult
from textual.widgets import Static

from game2048 import Board, add_random_tile, slide_down, slide_left, slide_right, slide_up
from textual_animation import (
    FRAME_DELAY,
    MovePlan,
    decorate_cell_chars,
    horizontal_star_positions,
    merge_color,
    merge_level,
    merge_pulse_sequence,
    plan_move,
)

CELL_WIDTH = 6

SPECIAL_BOARD_ROWS = [
    [2, 2, 4, 8],
    [16, 32, 64, 128],
    [256, 512, 1024, 0],
    [0, 0, 0, 0],
]


def format_grid(
    grid: List[List[int]],
    *,
    highlight_map: Optional[Dict[Tuple[int, int], int]] = None,
    pulse_colors: Optional[List[str]] = None,
    pulse_index: int = 0,
    border: str = "-",
    corner: str = "+",
    vertical: str = "|",
) -> str:
    size = len(grid)
    highlight_map = highlight_map or {}

    lines = []
    for row_index, row in enumerate(grid):
        lines.append(
            _horizontal_line(
                size,
                {row_index - 1, row_index},
                highlight_map,
                pulse_colors,
                pulse_index,
                border,
                corner,
            )
        )
        cells = []
        for col_index, value in enumerate(row):
            merge_value = highlight_map.get((row_index, col_index))
            cell = _render_cell(value, merge_value, pulse_colors, pulse_index)
            cells.append(cell)
        lines.append(vertical + vertical.join(cells) + vertical)
    lines.append(
        _horizontal_line(size, {size - 1}, highlight_map, pulse_colors, pulse_index, border, corner)
    )
    return "\n".join(lines)


def _horizontal_line(
    size: int,
    row_indices: Set[int],
    highlight_map: Dict[Tuple[int, int], int],
    pulse_colors: Optional[List[str]],
    pulse_index: int,
    border: str,
    corner: str,
) -> str:
    segments = []
    for col_index in range(size):
        merge_value = 0
        for row_index in row_indices:
            if row_index < 0 or row_index >= size:
                continue
            merge_value = max(merge_value, highlight_map.get((row_index, col_index), 0))
        segment_chars = [border] * CELL_WIDTH
        if merge_value:
            level = merge_level(merge_value)
            star_positions = horizontal_star_positions(CELL_WIDTH, merge_value)
            for index in star_positions:
                segment_chars[index] = "*"
            segment = _apply_star_colors(
                segment_chars, star_positions, level, pulse_colors, pulse_index
            )
        else:
            segment = "".join(segment_chars)
        segments.append(segment)
    return corner + corner.join(segments) + corner


def _render_cell(
    value: int,
    merge_value: Optional[int],
    pulse_colors: Optional[List[str]],
    pulse_index: int,
) -> str:
    if not value:
        return " " * CELL_WIDTH
    value_str = str(value)
    base_len = len(value_str)
    left = (CELL_WIDTH - base_len) // 2
    start = max(0, left)
    end = start + base_len
    cell_chars = [" "] * CELL_WIDTH
    for offset, char in enumerate(value_str):
        index = start + offset
        if index < CELL_WIDTH:
            cell_chars[index] = char
    if merge_value:
        level = merge_level(merge_value)
        cell_chars, star_positions = decorate_cell_chars(cell_chars, start, end, level)
        return _apply_star_colors(cell_chars, star_positions, level, pulse_colors, pulse_index)
    return "".join(cell_chars)


def _apply_star_colors(
    cell_chars: List[str],
    star_positions: Set[int],
    level: int,
    pulse_colors: Optional[List[str]],
    pulse_index: int,
) -> str:
    if not star_positions:
        return "".join(cell_chars)
    base_color = merge_color(level, None)
    ordered_positions = sorted(star_positions)
    position_index = {pos: idx for idx, pos in enumerate(ordered_positions)}
    pieces = []
    for index, char in enumerate(cell_chars):
        if index not in star_positions:
            pieces.append(char)
            continue
        if pulse_colors:
            color = pulse_colors[(pulse_index + position_index[index]) % len(pulse_colors)]
            pieces.append(f"[bold {color}]{char}[/]")
        elif base_color:
            pieces.append(f"[{base_color}]{char}[/]")
        else:
            pieces.append(char)
    return "".join(pieces)


class BoardApp(App):
    def __init__(self, board: Board) -> None:
        super().__init__()
        self.board = board
        self._board_view = Static()
        self._status_message = ""
        self._game_over = False
        self._animating = False
        self._animations_enabled = True

    def compose(self) -> ComposeResult:
        self._board_view.update(self._render_display(self.board.grid))
        yield self._board_view

    async def on_key(self, event) -> None:
        if self._game_over or self._animating:
            return

        move_map = {
            "left": slide_left,
            "right": slide_right,
            "up": slide_up,
            "down": slide_down,
        }
        move = move_map.get(event.key)
        if event.key == "A":
            self._animations_enabled = not self._animations_enabled
            self._board_view.update(self._render_display(self.board.grid))
            return
        if event.key == "X":
            self._load_special_board()
            return
        if move is None:
            return

        new_board, changed = move(self.board)
        if not changed:
            return

        plan = plan_move(self.board, event.key)
        self._animating = True
        if self._animations_enabled:
            await self._animate_move(plan)
        self.board = new_board
        if self._animations_enabled:
            await self._show_merge_highlight(plan.merge_values)
        else:
            self._board_view.update(self._render_display(self.board.grid))

        self.board = add_random_tile(self.board)
        self._board_view.update(self._render_display(self.board.grid))
        if not self.board.has_moves():
            self._game_over = True
            self._status_message = "Game Over: no moves left."
            self._board_view.update(self._render_display(self.board.grid))
        self._animating = False

    async def _animate_move(self, plan: MovePlan) -> None:
        if plan.max_steps == 0:
            return
        for step in range(1, plan.max_steps + 1):
            grid = plan.grid_for_step(step)
            self._board_view.update(self._render_display(grid))
            await asyncio.sleep(FRAME_DELAY)

    async def _show_merge_highlight(self, merge_values: Dict[Tuple[int, int], int]) -> None:
        if not merge_values:
            return
        colors, delay = merge_pulse_sequence(merge_values)
        for index, _color in enumerate(colors):
            pulse_colors = colors if colors != [None] else None
            self._board_view.update(
                self._render_display(
                    self.board.grid,
                    highlight_map=merge_values,
                    pulse_colors=pulse_colors,
                    pulse_index=index,
                )
            )
            await asyncio.sleep(delay)

    def _render_display(
        self,
        grid: List[List[int]],
        *,
        highlight_map: Optional[Dict[Tuple[int, int], int]] = None,
        pulse_colors: Optional[List[str]] = None,
        pulse_index: int = 0,
    ) -> str:
        board_text = format_grid(
            grid,
            highlight_map=highlight_map,
            pulse_colors=pulse_colors,
            pulse_index=pulse_index,
        )
        lines = board_text.splitlines()
        score_text = self._score_text()
        indicator = self._animation_indicator()
        right_lines = [indicator, score_text]
        if self._status_message:
            right_lines.append(self._status_message)
        target_line = len(lines) // 2
        start_line = min(target_line, max(0, len(lines) - len(right_lines)))
        padded_lines = []
        for index, line in enumerate(lines):
            right_index = index - start_line
            suffix = f"  {right_lines[right_index]}" if 0 <= right_index < len(right_lines) else ""
            padded_lines.append(line + suffix)
        return "\n".join(padded_lines)

    def _animation_indicator(self) -> str:
        state = "ON" if self._animations_enabled else "OFF"
        return f"\\[A]nimations {state}"

    def _score_text(self) -> str:
        return f"Score: {self.board.score()}"

    def _load_special_board(self) -> None:
        self.board = Board.from_rows(SPECIAL_BOARD_ROWS)
        self._game_over = False
        self._status_message = ""
        self._board_view.update(self._render_display(self.board.grid))
