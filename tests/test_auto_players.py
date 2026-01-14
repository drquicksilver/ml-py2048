import unittest
from pathlib import Path

from auto_players import load_strategies


class TestStrategyLoading(unittest.TestCase):
    def test_loads_builtin_strategies(self):
        strategy_dir = Path(__file__).resolve().parents[1] / "strategies"
        strategies, errors = load_strategies(strategy_dir)
        names = {spec.name for spec in strategies}
        self.assertIn("Random legal move", names)
        self.assertIn("Rotating move", names)
        self.assertIn("Priority move", names)
        self.assertEqual(errors, [])
