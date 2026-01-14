from auto_players import MOVE_DIRECTIONS, legal_moves_from_grid


class RotatingPlayer:
    def __init__(self) -> None:
        self._index = -1

    def next_move(self, grid):
        legal = set(legal_moves_from_grid(grid))
        for offset in range(1, len(MOVE_DIRECTIONS) + 1):
            candidate_index = (self._index + offset) % len(MOVE_DIRECTIONS)
            candidate = MOVE_DIRECTIONS[candidate_index]
            if candidate in legal:
                self._index = candidate_index
                return candidate
        return MOVE_DIRECTIONS[0]


STRATEGY = {
    "name": "Rotating move",
    "factory": RotatingPlayer,
}
