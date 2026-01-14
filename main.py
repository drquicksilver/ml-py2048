import random

from game2048 import Board
from textual_board import BoardApp


if __name__ == "__main__":
    size = 4
    empty_rows = [[0] * size for _ in range(size)]
    row_index = random.randrange(size)
    col_index = random.randrange(size)
    empty_rows[row_index][col_index] = 2
    board = Board.from_rows(empty_rows)
    BoardApp(board).run()
