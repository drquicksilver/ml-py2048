import unittest
from pathlib import Path

from textual.widgets import OptionList

from auto_play import AutoPlayApp
from auto_players import StrategySpec


class DummyPlayer:
    def next_move(self, _grid):
        return "up"


class TestableAutoPlayApp(AutoPlayApp):
    def on_mount(self) -> None:
        self._strategies = [
            StrategySpec(name="Dummy", factory=DummyPlayer, source="dummy"),
        ]
        for spec in self._strategies:
            self._menu.add_option(spec.name)
        self._menu.highlighted = 0

    def on_option_list_option_selected(self, event) -> None:
        if not self._strategies:
            return
        index = event.option_index
        self._selected = self._strategies[index]
        self._status.update(f"Running: {self._selected.name}")
        self._start_time = 0.0
        self._move_count = 0
        self._stats.update("Starting...")


class TestAutoPlayMenu(unittest.TestCase):
    def test_enter_selects_strategy(self):
        app = TestableAutoPlayApp(strategy_dir=Path("."))
        app.on_mount()
        option = app._menu.options[0]
        event = OptionList.OptionSelected(app._menu, option, 0)
        app.on_option_list_option_selected(event)
        self.assertIsNotNone(app._selected)
        self.assertTrue(app._menu.display)
