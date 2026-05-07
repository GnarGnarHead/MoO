from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from branch_lineage import branch_lineage_report


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
            "'{\"generator\":\"test\",\"max_abs_p\":10,\"max_abs_q\":10,"
            "\"max_abs_value\":10.0,\"max_stage\":16,\"retain_confirmed_edges\":true}'"
            ")"
        )
        conn.execute("INSERT INTO stages VALUES(16, 0, 0, 0, 0, 16, 5, 0.0)")
        nodes = [
            (n, n, 1, str(n), "certainty" if n == 1 else "positive_integer", n, n)
            for n in range(1, 17)
        ]
        conn.executemany(
            "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            nodes,
        )
        edges = [
            (1, 1, "seed", None, None, 1),
            (2, 2, "+", 2, 2, 4),
            (3, 2, "*", 2, 2, 4),
            (4, 3, "+", 3, 3, 6),
            (5, 3, "*", 2, 3, 6),
        ]
        conn.executemany(
            "INSERT INTO edges(edge_id, stage, op, left_node_id, right_node_id, result_node_id) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            edges,
        )
        conn.commit()
    finally:
        conn.close()


class BranchLineageTests(unittest.TestCase):
    def test_even_branch_records_repeated_relation_witness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                report = branch_lineage_report(conn, branch="even", limit=3)

        entry = report["entries"][2]
        self.assertEqual(entry["source"], 3)
        self.assertEqual(entry["result"], 6)
        self.assertIn("witnessed_through_branch", entry["moo_reading"])
        self.assertIn("witnessed_through_counting_spine", entry["moo_reading"])
        self.assertTrue(entry["branch_witness"]["present"])

    def test_square_branch_separates_branch_membership_from_retained_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                report = branch_lineage_report(conn, branch="square", limit=4)

        entry = report["entries"][3]
        self.assertEqual(entry["source"], 4)
        self.assertEqual(entry["result"], 16)
        self.assertTrue(entry["relation_permitted"])
        self.assertFalse(entry["branch_witness"]["present"])
        self.assertTrue(entry["counting_spine_witnessed"])
        self.assertIn("permitted_but_not_witnessed_in_field", entry["moo_reading"])
        self.assertIn("witnessed_through_counting_spine", entry["moo_reading"])
        self.assertIn("outside_max_abs_p", entry["field_blockers"])
        self.assertIn("outside_max_abs_value", entry["field_blockers"])

    def test_prime_branch_is_not_just_factor_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                report = branch_lineage_report(conn, branch="prime", limit=6)

        five = report["entries"][3]
        six = report["entries"][4]
        self.assertEqual(five["value"], 5)
        self.assertEqual(five["branch"], "prime")
        self.assertIn("prime_branch_member", five["moo_reading"])
        self.assertIn("irreducibility_condition", five["moo_reading"])
        self.assertIsNone(five["nontrivial_product_landing"])
        self.assertEqual(six["value"], 6)
        self.assertEqual(six["branch"], "prime")
        self.assertIn("product_branch_landing", six["moo_reading"])
        self.assertIn("witnessed_through_product_branch", six["moo_reading"])
        self.assertEqual(six["nontrivial_product_landing"], {"left": 2, "right": 3})


if __name__ == "__main__":
    unittest.main()
