import unittest

from auto_players import legal_moves_from_grid
from strategies.priority import PriorityPlayer
from strategies.random_legal import RandomLegalPlayer
from strategies.rotating import RotatingPlayer


class FakeRng:
    def __init__(self, choice_value):
        self.choice_value = choice_value

    def choice(self, _sequence):
        return self.choice_value


class TestStrategies(unittest.TestCase):
    def test_random_legal_returns_legal_move(self):
        grid = [
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        legal = legal_moves_from_grid(grid)
        rng = FakeRng(choice_value=legal[-1])
        player = RandomLegalPlayer(rng=rng)
        move = player.next_move(grid)
        self.assertIn(move, legal)

    def test_rotating_player_advances_cycle(self):
        grid = [
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        player = RotatingPlayer()
        first = player.next_move(grid)
        second = player.next_move(grid)
        self.assertEqual(first, "right")
        self.assertEqual(second, "down")

    def test_priority_player_picks_down_first(self):
        grid = [
            [0, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        player = PriorityPlayer()
        move = player.next_move(grid)
        self.assertEqual(move, "down")
