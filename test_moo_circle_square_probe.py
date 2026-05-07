from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from fractions import Fraction
from pathlib import Path

from moo_circle_square_probe import (
    circle_square_alignment_summary,
    circle_square_candidate,
    strict_self_product_witness,
)


def _create_fixture(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "CREATE TABLE stages("
            "stage INTEGER PRIMARY KEY, candidate_events INTEGER, retained_events INTEGER, "
            "new_nodes INTEGER, new_edges INTEGER, total_nodes INTEGER, total_edges INTEGER, "
            "elapsed_seconds REAL)"
        )
        conn.execute(
            "CREATE TABLE nodes("
            "node_id INTEGER PRIMARY KEY, p INTEGER, q INTEGER, label TEXT, "
            "kind TEXT, first_stage INTEGER, confirmed_stage INTEGER)"
        )
        conn.execute(
            "CREATE TABLE edges("
            "edge_id INTEGER PRIMARY KEY, stage INTEGER, op TEXT, "
            "left_node_id INTEGER, right_node_id INTEGER, result_node_id INTEGER)"
        )
        conn.execute(
            "CREATE TABLE node_stats("
            "node_id INTEGER, p INTEGER, q INTEGER, kind TEXT, "
            "first_stage INTEGER, confirmed_stage INTEGER, derivation_events INTEGER, "
            "plus_count INTEGER, minus_count INTEGER, multiply_count INTEGER, divide_count INTEGER)"
        )
        conn.execute("INSERT INTO meta(key, value) VALUES('schema_version', 'test')")
        conn.execute(
            "INSERT INTO stages VALUES(5, 0, 0, 0, 0, 6, 3, 0.0)"
        )
        nodes = [
            (1, 3, 1, "3", "positive_integer", 3, 3),
            (2, 4, 1, "4", "positive_integer", 4, 4),
            (3, 5, 1, "5", "positive_integer", 5, 5),
            (4, 9, 1, "9", "positive_integer", 3, 9),
            (5, 16, 1, "16", "positive_integer", 4, 16),
            (6, 25, 1, "25", "positive_integer", 5, 25),
        ]
        conn.executemany(
            "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            nodes,
        )
        edges = [
            (1, 3, "*", 1, 1, 4),
            (2, 4, "*", 2, 2, 5),
            (3, 5, "*", 3, 3, 6),
        ]
        conn.executemany(
            "INSERT INTO edges(edge_id, stage, op, left_node_id, right_node_id, result_node_id) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            edges,
        )
        stats = [
            (1, 3, 1, "positive_integer", 3, 3, 0, 0, 0, 0, 0),
            (2, 4, 1, "positive_integer", 4, 4, 0, 0, 0, 0, 0),
            (3, 5, 1, "positive_integer", 5, 5, 0, 0, 0, 0, 0),
            (4, 9, 1, "positive_integer", 3, 9, 1, 0, 0, 1, 0),
            (5, 16, 1, "positive_integer", 4, 16, 1, 0, 0, 1, 0),
            (6, 25, 1, "positive_integer", 5, 25, 1, 0, 0, 1, 0),
        ]
        conn.executemany(
            "INSERT INTO node_stats("
            "node_id, p, q, kind, first_stage, confirmed_stage, derivation_events, "
            "plus_count, minus_count, multiply_count, divide_count"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            stats,
        )
        conn.commit()
    finally:
        conn.close()


class CircleSquareProbeTests(unittest.TestCase):
    def test_strict_self_product_witness_detects_integer_square(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                source = conn.execute("SELECT * FROM nodes WHERE p = 3 AND q = 1").fetchone()
                square = conn.execute("SELECT * FROM nodes WHERE p = 9 AND q = 1").fetchone()
                payload = strict_self_product_witness(conn, source, square)

        self.assertTrue(payload["present"])
        self.assertEqual(payload["stage"], 3)

    def test_circle_square_candidate_for_345_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                nodes = {
                    (int(row["p"]), int(row["q"])): row
                    for row in conn.execute("SELECT * FROM nodes").fetchall()
                }
                payload = circle_square_candidate(
                    conn,
                    Fraction(3, 1),
                    Fraction(4, 1),
                    Fraction(5, 1),
                    nodes,
                )

        self.assertTrue(payload["completion"]["complete_family"])
        self.assertEqual(payload["completion"]["strict_self_product_witness_count"], 3)
        self.assertTrue(payload["completion"]["all_square_components_have_strict_self_product_witness"])
        self.assertEqual(payload["phase_alignment"]["combined"]["stage_spread"], 2)
        self.assertEqual(payload["phase_alignment"]["phase_delta"], 0)

    def test_alignment_summary_finds_345_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                payload = circle_square_alignment_summary(
                    conn,
                    max_denominator=1,
                    max_abs_value=5,
                    limit=3,
                    include_negative=False,
                    include_degenerate=False,
                    require_complete_family=True,
                    max_pairs=100,
                    full_scan=False,
                )

        self.assertEqual(payload["summary"]["candidate_count"], 1)
        self.assertEqual(payload["summary"]["complete_family_count"], 1)
        self.assertEqual(payload["summary"]["with_all_strict_self_product_witnesses_count"], 1)
        first = payload["top_low_stage_spread_complete_families"][0]
        self.assertEqual(first["shell"]["x"]["frac"], "3")
        self.assertEqual(first["shell"]["y"]["frac"], "4")
        self.assertEqual(first["shell"]["r"]["frac"], "5")


if __name__ == "__main__":
    unittest.main()
