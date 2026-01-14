from __future__ import annotations

import asyncio
import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import OptionList, Static

from auto_players import StrategySpec, apply_move, legal_moves, load_strategies, max_tile, spawn_tile
from game2048 import starting_board


class AutoPlayApp(App):
    def __init__(self, strategy_dir: Path) -> None:
        super().__init__()
        self._strategy_dir = strategy_dir
        self._strategies: list[StrategySpec] = []
        self._errors: list[str] = []
        self._menu = OptionList()
        self._stats = Static()
        self._status = Static()
        self._debug = Static()
        self._selected: StrategySpec | None = None
        self._move_count = 0
        self._start_time = 0.0
        self._running = False

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
        self._selected = self._strategies[index]
        self._status.update(f"Running: {self._selected.name}")
        self._start_time = time.monotonic()
        self._move_count = 0
        self._stats.update("Starting...")
        self._running = True
        self.run_worker(self._run_game(self._selected), exclusive=True)

    async def _run_game(self, strategy: StrategySpec) -> None:
        board = starting_board()
        rng = None
        player = strategy.factory()
        while True:
            if not board.has_moves():
                self._stats.update(self._format_stats(board, "Game Over"))
                self._status.update("Game Over")
                self._running = False
                self._menu.focus()
                self._menu.refresh()
                return

            grid_view = tuple(tuple(row) for row in board.grid)
            direction = player.next_move(grid_view)
            self._move_count += 1

            legal = legal_moves(board)
            if direction not in legal:
                message = f"Illegal move at {self._move_count}: {direction}"
                self._stats.update(self._format_stats(board, message))
                self._status.update(message)
                self._running = False
                self._menu.focus()
                self._menu.refresh()
                return

            board = apply_move(board, direction)
            board = spawn_tile(board, rng=rng)
            self._stats.update(self._format_stats(board, "Running"))
            await asyncio.sleep(0)

    def on_key(self, event) -> None:
        if event.key not in {"enter", "return"}:
            return
        self._debug.update(
            f"key={event.key} highlighted={self._menu.highlighted} running={self._running}"
        )
        if not self._strategies:
            return
        if self._menu.highlighted is None:
            return
        self._start_strategy(self._menu.highlighted)

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
