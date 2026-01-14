import random

from auto_players import legal_moves_from_grid


class RandomLegalPlayer:
    def __init__(self, rng=None) -> None:
        self._rng = rng or random.Random()

    def next_move(self, grid):
        moves = legal_moves_from_grid(grid)
        return self._rng.choice(moves)


STRATEGY = {
    "name": "Random legal move",
    "factory": RandomLegalPlayer,
}
