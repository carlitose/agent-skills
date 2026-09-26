import unittest

from toy.calc import add, half


class CalcTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_half(self):
        self.assertEqual(half(8), 4)


if __name__ == "__main__":
    unittest.main()
