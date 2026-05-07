from __future__ import annotations

import unittest
from fractions import Fraction

from rational_baselines import (
    baseline_features,
    continued_fraction,
    farey_neighbors,
    format_key,
    parse_key,
    stern_brocot_path,
)


class RationalBaselineTests(unittest.TestCase):
    def test_parse_and_format_normalize(self) -> None:
        self.assertEqual(parse_key("68/42"), (34, 21))
        self.assertEqual(format_key((68, 42)), "34/21")
        self.assertEqual(format_key((-8, -6)), "4/3")

    def test_continued_fraction(self) -> None:
        self.assertEqual(continued_fraction(Fraction(22, 7)), [3, 7])
        self.assertEqual(continued_fraction(Fraction(34, 21)), [1, 1, 1, 1, 1, 1, 2])
        self.assertEqual(continued_fraction(Fraction(-4, 3)), [-2, 1, 2])

    def test_stern_brocot_path(self) -> None:
        self.assertEqual(stern_brocot_path(Fraction(1, 1))["depth"], 0)
        self.assertEqual(stern_brocot_path(Fraction(2, 1))["path"], "R")
        self.assertEqual(stern_brocot_path(Fraction(1, 2))["path"], "L")
        self.assertEqual(stern_brocot_path(Fraction(3, 2))["path"], "RL")
        self.assertFalse(stern_brocot_path(Fraction(-4, 3))["applicable"])

    def test_farey_neighbors(self) -> None:
        neighbors = farey_neighbors(Fraction(1, 2), order=2)
        self.assertEqual(neighbors["left"]["frac"], "0")
        self.assertEqual(neighbors["right"]["frac"], "1")

    def test_baseline_features_normalize(self) -> None:
        features = baseline_features((68, 42))
        self.assertEqual(features["frac"], "34/21")
        self.assertEqual(features["denominator_height"], 21)
        self.assertEqual(features["component_height"], 34)


if __name__ == "__main__":
    unittest.main()
