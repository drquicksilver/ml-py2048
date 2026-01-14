import unittest

from game2048 import (
    Board,
    add_random_tile,
    slide_down,
    slide_left,
    slide_right,
    slide_up,
    tile_score,
)


class FakeRng:
    def __init__(self, choice_value, random_value):
        self.choice_value = choice_value
        self.random_value = random_value

    def choice(self, _sequence):
        return self.choice_value

    def random(self):
        return self.random_value


class TestGame2048Moves(unittest.TestCase):
    def test_slide_left_merges_once(self):
        board = Board.from_rows(
            [
                [2, 2, 2, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ]
        )
        moved, changed = slide_left(board)
        self.assertTrue(changed)
        self.assertEqual(
            moved.grid,
            [
                [4, 2, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
        )

    def test_slide_left_compacts_and_merges(self):
        board = Board.from_rows(
            [
                [2, 0, 2, 4],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ]
        )
        moved, changed = slide_left(board)
        self.assertTrue(changed)
        self.assertEqual(
            moved.grid,
            [
                [4, 4, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
        )

    def test_slide_right(self):
        board = Board.from_rows(
            [
                [2, 0, 2, 2],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ]
        )
        moved, changed = slide_right(board)
        self.assertTrue(changed)
        self.assertEqual(
            moved.grid,
            [
                [0, 0, 2, 4],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
        )

    def test_slide_up(self):
        board = Board.from_rows(
            [
                [2, 0, 0, 0],
                [2, 0, 0, 0],
                [4, 0, 0, 0],
                [4, 0, 0, 0],
            ]
        )
        moved, changed = slide_up(board)
        self.assertTrue(changed)
        self.assertEqual(
            moved.grid,
            [
                [4, 0, 0, 0],
                [8, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
        )

    def test_slide_down(self):
        board = Board.from_rows(
            [
                [2, 0, 0, 0],
                [2, 0, 0, 0],
                [4, 0, 0, 0],
                [4, 0, 0, 0],
            ]
        )
        moved, changed = slide_down(board)
        self.assertTrue(changed)
        self.assertEqual(
            moved.grid,
            [
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [4, 0, 0, 0],
                [8, 0, 0, 0],
            ],
        )

    def test_no_change_returns_false(self):
        board = Board.from_rows(
            [
                [2, 4, 8, 16],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ]
        )
        moved, changed = slide_left(board)
        self.assertFalse(changed)
        self.assertEqual(
            moved.grid,
            [
                [2, 4, 8, 16],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
        )


class TestRandomTile(unittest.TestCase):
    def test_add_random_tile_picks_position_and_value(self):
        board = Board.from_rows(
            [
                [0, 0],
                [0, 0],
            ]
        )
        rng = FakeRng(choice_value=(0, 1), random_value=0.05)
        updated = add_random_tile(board, rng=rng)
        self.assertEqual(updated.grid, [[0, 4], [0, 0]])

    def test_full_board_is_full(self):
        board = Board.from_rows([[2, 4], [8, 16]])
        self.assertTrue(board.is_full())

    def test_has_moves_with_empty_cell(self):
        board = Board.from_rows([[2, 4], [8, 0]])
        self.assertTrue(board.has_moves())

    def test_has_moves_with_merge_available(self):
        board = Board.from_rows([[2, 4], [8, 8]])
        self.assertTrue(board.has_moves())

    def test_has_moves_no_merge(self):
        board = Board.from_rows([[2, 4], [8, 16]])
        self.assertFalse(board.has_moves())

    def test_tile_score_powers_of_two(self):
        self.assertEqual(tile_score(2), 3)
        self.assertEqual(tile_score(4), 9)
        self.assertEqual(tile_score(8), 27)
        self.assertEqual(tile_score(16), 81)

    def test_board_score(self):
        board = Board.from_rows(
            [
                [2, 0],
                [4, 8],
            ]
        )
        self.assertEqual(board.score(), 3 + 9 + 27)
