from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from primitive_euclid_branch_sweep import (
    branch_payload,
    generate_primitive_branches,
    primitive_branch_sweep,
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
        conn.execute("INSERT INTO meta(key, value) VALUES('schema_version', 'test')")
        conn.execute(
            "INSERT INTO meta(key, value) VALUES("
            "'config_json', "
            "'{\"generator\":\"test\",\"max_abs_p\":200,\"max_abs_q\":200,"
            "\"max_abs_value\":4.0,\"max_stage\":25,\"retain_confirmed_edges\":true}'"
            ")"
        )
        conn.execute("INSERT INTO stages VALUES(25, 0, 0, 0, 0, 13, 0, 0.0)")
        nodes = [
            (1, 1, 1, "1", "certainty", 1, 1),
            (2, 2, 1, "2", "positive_integer", 1, 2),
            (3, 3, 1, "3", "positive_integer", 2, 3),
            (4, 4, 1, "4", "positive_integer", 2, 4),
            (5, 5, 1, "5", "positive_integer", 5, 5),
            (6, 9, 1, "9", "positive_integer", 9, 9),
            (7, 16, 1, "16", "positive_integer", 16, 16),
            (8, 25, 1, "25", "positive_integer", 25, 25),
            (9, 12, 1, "12", "positive_integer", 12, 12),
            (10, 13, 1, "13", "positive_integer", 13, 13),
        ]
        conn.executemany(
            "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            nodes,
        )
        conn.commit()
    finally:
        conn.close()


class PrimitiveEuclidBranchSweepTests(unittest.TestCase):
    def test_generate_primitive_branches_uses_euclid_rules(self) -> None:
        branches = generate_primitive_branches(4)
        triples = [(branch.x, branch.y, branch.r, branch.m, branch.n) for branch in branches]

        self.assertEqual(
            triples,
            [
                (3, 4, 5, 2, 1),
                (5, 12, 13, 3, 2),
                (8, 15, 17, 4, 1),
                (7, 24, 25, 4, 3),
            ],
        )

    def test_branch_payload_records_self_product_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                nodes = {
                    (int(row["p"]), int(row["q"])): row
                    for row in conn.execute("SELECT * FROM nodes").fetchall()
                }
                branch = generate_primitive_branches(2)[0]
                payload = branch_payload(conn, branch, nodes)

        self.assertEqual(payload["primitive_triple"]["label"], "3,4,5")
        self.assertEqual(payload["failure_category"], "self_product_witness_missing")
        self.assertEqual(payload["first_complete_stage"], 25)
        self.assertEqual(payload["generator_coverage"], 1.0)
        self.assertEqual(payload["shell_coverage"], 1.0)
        self.assertEqual(payload["square_coverage"], 1.0)
        self.assertEqual(payload["self_product_witness_coverage"], 0.0)
        self.assertTrue(payload["square_node_complete"])
        self.assertFalse(payload["square_self_product_complete"])
        self.assertEqual(
            payload["square_provenance_summary"]["source_counts"]["core_confirmation_only"],
            3,
        )
        self.assertEqual(payload["square_provenance"]["x"]["square_node_source"], "core_confirmation_only")
        self.assertEqual(payload["square_provenance"]["x"]["confirmed_stage"], 9)

    def test_sweep_records_partial_square_missing_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                payload = primitive_branch_sweep(conn, max_m=3)

        self.assertEqual(payload["summary"]["branch_count"], 2)
        self.assertEqual(payload["summary"]["node_complete_branch_count"], 1)
        self.assertEqual(payload["summary"]["failure_category_counts"]["self_product_witness_missing"], 1)
        self.assertEqual(payload["summary"]["failure_category_counts"]["square_components_missing"], 1)
        first, second = payload["branches"]
        self.assertEqual(first["graph_cost_rank"], 1)
        self.assertIsNone(second["graph_cost_rank"])
        self.assertEqual(second["primitive_triple"]["label"], "5,12,13")
        self.assertEqual(second["failure_category"], "square_components_missing")
        self.assertEqual(second["square_provenance"]["x"]["square_node_source"], "core_confirmation_only")
        self.assertEqual(second["square_provenance"]["y"]["square_node_source"], "absent")
        self.assertIn(
            "output_excluded_by_max_abs_value",
            second["square_provenance"]["y"]["retention_blocker"]["all"],
        )
        self.assertEqual(
            payload["summary"]["square_provenance_source_counts"],
            {
                "absent": 2,
                "core_confirmation_only": 4,
                "other_graph_witness": 0,
                "self_product_edge": 0,
            },
        )

    def test_square_provenance_detects_branch_self_product_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute(
                    "INSERT INTO edges(edge_id, stage, op, left_node_id, right_node_id, result_node_id) "
                    "VALUES(1, 3, '*', 3, 3, 6)"
                )
                conn.commit()
                nodes = {
                    (int(row["p"]), int(row["q"])): row
                    for row in conn.execute("SELECT * FROM nodes").fetchall()
                }
                branch = generate_primitive_branches(2)[0]
                payload = branch_payload(conn, branch, nodes)

        self.assertEqual(payload["square_provenance"]["x"]["square_node_source"], "self_product_edge")
        self.assertTrue(payload["square_provenance"]["x"]["self_product_edge_present"])
        self.assertTrue(payload["square_provenance"]["x"]["self_product_edge_operands_confirmed_at_stage"])
        self.assertEqual(payload["square_provenance_summary"]["source_counts"]["self_product_edge"], 1)


if __name__ == "__main__":
    unittest.main()
