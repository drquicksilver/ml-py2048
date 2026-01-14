from auto_players import legal_moves_from_grid


class PriorityPlayer:
    def next_move(self, grid):
        legal = set(legal_moves_from_grid(grid))
        for candidate in ["down", "left", "up", "right"]:
            if candidate in legal:
                return candidate
        return "down"


STRATEGY = {
    "name": "Priority move",
    "factory": PriorityPlayer,
}
