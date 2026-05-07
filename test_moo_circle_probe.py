from __future__ import annotations

import unittest
import sqlite3
import tempfile
from contextlib import closing
from fractions import Fraction
from pathlib import Path

from moo_circle_probe import (
    exact_sqrt_fraction,
    pythagorean_shell_summary,
    quadratic_form,
    unit_shell_point,
)


class CircleProbeTests(unittest.TestCase):
    def test_unit_shell_point_is_exact(self) -> None:
        x, y = unit_shell_point(Fraction(1, 2))
        self.assertEqual(x, Fraction(3, 5))
        self.assertEqual(y, Fraction(4, 5))
        self.assertEqual(quadratic_form(x, y), Fraction(1, 1))

    def test_unit_shell_point_handles_negative_parameter(self) -> None:
        x, y = unit_shell_point(Fraction(-1, 2))
        self.assertEqual(x, Fraction(3, 5))
        self.assertEqual(y, Fraction(-4, 5))
        self.assertEqual(quadratic_form(x, y), Fraction(1, 1))

    def test_exact_sqrt_fraction(self) -> None:
        self.assertEqual(exact_sqrt_fraction(Fraction(9, 25)), Fraction(3, 5))
        self.assertEqual(exact_sqrt_fraction(Fraction(0, 1)), Fraction(0, 1))
        self.assertIsNone(exact_sqrt_fraction(Fraction(2, 1)))
        self.assertIsNone(exact_sqrt_fraction(Fraction(-1, 4)))

    def test_pythagorean_scan_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "corpus.sqlite"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    "CREATE TABLE nodes("
                    "node_id INTEGER PRIMARY KEY, p INTEGER, q INTEGER, label TEXT, "
                    "kind TEXT, first_stage INTEGER, confirmed_stage INTEGER)"
                )
                conn.execute(
                    "CREATE TABLE node_stats("
                    "node_id INTEGER, p INTEGER, q INTEGER, kind TEXT, "
                    "first_stage INTEGER, confirmed_stage INTEGER, derivation_events INTEGER, "
                    "plus_count INTEGER, minus_count INTEGER, multiply_count INTEGER, divide_count INTEGER)"
                )
                for node_id, p in enumerate((0, 1, 2), start=1):
                    conn.execute(
                        "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
                        "VALUES(?, ?, 1, ?, 'integer', ?, ?)",
                        (node_id, p, str(p), max(1, p), max(1, p)),
                    )
                conn.commit()
            finally:
                conn.close()

            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                with self.assertRaises(SystemExit):
                    pythagorean_shell_summary(
                        conn,
                        max_denominator=10,
                        max_abs_value=4,
                        limit=3,
                        include_degenerate=True,
                        max_pairs=3,
                        full_scan=False,
                    )


if __name__ == "__main__":
    unittest.main()
