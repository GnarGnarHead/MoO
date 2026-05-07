from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from moo_graph_invariants import family_graph_invariants, node_graph_invariants


def _create_fixture(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
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
        nodes = [
            (1, 1, 1, "1", "certainty", 1, 1),
            (2, 2, 1, "2", "positive_integer", 2, 2),
            (3, 3, 1, "3", "positive_integer", 3, 3),
            (4, 6, 1, "6", "positive_integer", 3, 6),
        ]
        conn.executemany(
            "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            nodes,
        )
        edges = [
            (1, 1, "seed", None, None, 1),
            (2, 2, "+", 1, 1, 2),
            (3, 3, "+", 2, 1, 3),
            (4, 3, "*", 2, 3, 4),
            (5, 6, "+", 3, 3, 4),
        ]
        conn.executemany(
            "INSERT INTO edges(edge_id, stage, op, left_node_id, right_node_id, result_node_id) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            edges,
        )
        stats = [
            (1, 1, 1, "certainty", 1, 1, 1, 0, 0, 0, 0),
            (2, 2, 1, "positive_integer", 2, 2, 1, 1, 0, 0, 0),
            (3, 3, 1, "positive_integer", 3, 3, 1, 1, 0, 0, 0),
            (4, 6, 1, "positive_integer", 3, 6, 2, 1, 0, 1, 0),
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


class GraphInvariantTests(unittest.TestCase):
    def test_node_graph_invariants_report_shared_vocabulary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                payload = node_graph_invariants(conn, (6, 1), min_peer_group=1)

        self.assertTrue(payload["present"])
        self.assertEqual(payload["vocabulary_version"], "graph_invariants.v1")
        self.assertEqual(payload["arrival"]["first_stage"], 3)
        self.assertEqual(payload["arrival"]["confirmed_stage"], 6)
        self.assertEqual(payload["arrival"]["confirmation_lag"], 3)
        self.assertEqual(payload["incoming_derivation_events"], 2)
        self.assertEqual(payload["operation_signature"]["counts"], {"+": 1, "*": 1})
        self.assertEqual(
            payload["distinct_witness_families"]["unique_commutative_normalized_algebraic"],
            2,
        )
        self.assertIn("baseline_adjusted_rank", payload)

    def test_family_graph_invariants_summarize_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                payload = family_graph_invariants(
                    conn,
                    [("two", (2, 1)), ("three", (3, 1)), ("six", (6, 1))],
                    include_node_invariants=False,
                )

        self.assertEqual(payload["present_member_count"], 3)
        self.assertEqual(payload["missing_member_count"], 0)
        self.assertEqual(payload["max_first_stage"], 3)
        self.assertEqual(payload["max_confirmation_lag"], 3)
        self.assertEqual(payload["total_incoming_derivation_events"], 4)
        self.assertEqual(payload["baseline_envelope"]["max_component_height"], 6)


if __name__ == "__main__":
    unittest.main()
