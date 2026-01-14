import unittest


def main() -> None:
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
