from __future__ import annotations

import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.timer import Timer
from textual.widgets import OptionList, Static

from auto_players import StrategySpec, apply_move, legal_moves, load_strategies, max_tile, spawn_tile
from game2048 import starting_board


class AutoPlayMenu(OptionList):
    def watch_highlighted(self, highlighted: int | None) -> None:
        super().watch_highlighted(highlighted)
        self.refresh()


class AutoPlayApp(App):
    def __init__(self, strategy_dir: Path) -> None:
        super().__init__()
        self._strategy_dir = strategy_dir
        self._strategies: list[StrategySpec] = []
        self._errors: list[str] = []
        self._menu = AutoPlayMenu()
        self._stats = Static()
        self._status = Static()
        self._debug = Static()
        self._selected: StrategySpec | None = None
        self._move_count = 0
        self._start_time = 0.0
        self._running = False
        self._board = None
        self._player = None
        self._rng = None
        self._auto_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Static("Select an automated player strategy:")
        yield self._menu
        yield self._status
        yield self._debug
        yield self._stats

    def on_mount(self) -> None:
        self._strategies, self._errors = load_strategies(self._strategy_dir)
        if not self._strategies:
            self._status.update("No strategies found.")
            return
        for spec in self._strategies:
            self._menu.add_option(spec.name)
        self._menu.focus()
        if self._errors:
            self._status.update("Some strategies failed to load; check console output.")
            for error in self._errors:
                print(error)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if not self._strategies:
            return
        self._start_strategy(event.option_index)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self._debug.update(
            f"highlighted={event.option_index} running={self._running} focus={self._menu.has_focus}"
        )
        self._menu.refresh()

    def _start_strategy(self, index: int) -> None:
        self._stop_autoplay()
        self._selected = self._strategies[index]
        self._status.update(f"Running: {self._selected.name}")
        self._start_time = time.monotonic()
        self._move_count = 0
        self._stats.update("Starting...")
        self._running = True
        self._board = starting_board()
        self._rng = None
        self._player = self._selected.factory()
        self._auto_timer = self.set_interval(0.01, self._run_step, name="auto_play")

    def _stop_autoplay(self) -> None:
        if self._auto_timer is None:
            return
        timer = self._auto_timer
        self._auto_timer = None
        timer.pause()
        self.call_later(timer.stop)

    def _finish_run(self, board, status: str, status_line: str | None = None) -> None:
        self._stats.update(self._format_stats(board, status))
        self._status.update(status_line or status)
        self._running = False
        self._stop_autoplay()
        self._menu.focus()
        self._menu.refresh()

    def _run_step(self) -> None:
        if not self._running or self._board is None or self._player is None:
            return
        board = self._board
        if not board.has_moves():
            self._finish_run(board, "Game Over")
            return

        grid_view = tuple(tuple(row) for row in board.grid)
        direction = self._player.next_move(grid_view)
        self._move_count += 1

        legal = legal_moves(board)
        if direction not in legal:
            message = f"Illegal move at {self._move_count}: {direction}"
            self._finish_run(board, message, message)
            return

        board = apply_move(board, direction)
        board = spawn_tile(board, rng=self._rng)
        self._board = board
        self._stats.update(self._format_stats(board, "Running"))

    def _format_stats(self, board, status: str) -> str:
        elapsed = time.monotonic() - self._start_time
        lines = [
            f"Status: {status}",
            f"Move: {self._move_count}",
            f"Score: {board.score()}",
            f"Max tile: {max_tile(board)}",
            f"Elapsed: {elapsed:.2f}s",
        ]
        return "\n".join(lines)


def main() -> None:
    strategy_dir = Path(__file__).parent / "strategies"
    AutoPlayApp(strategy_dir).run()
