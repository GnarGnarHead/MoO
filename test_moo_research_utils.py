from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from moo_research_utils import connect_readonly, strict_alignment_payload


def _create_alignment_db(path: Path, *, fail: bool = False) -> None:
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
            "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
            "VALUES(1, 1, 1, '1', 'integer', 1, 1)"
        )
        conn.execute(
            "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
            "VALUES(2, 2, 1, '2', 'integer', 2, 2)"
        )
        conn.execute(
            "INSERT INTO edges(edge_id, stage, op, left_node_id, right_node_id, result_node_id) "
            "VALUES(1, 2, '+', 1, 1, 2)"
        )
        if fail:
            conn.execute(
                "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
                "VALUES(3, 3, 2, '3/2', 'rational', 2, NULL)"
            )
            conn.execute(
                "INSERT INTO edges(edge_id, stage, op, left_node_id, right_node_id, result_node_id) "
                "VALUES(2, 2, '+', 3, 1, 2)"
            )
        conn.commit()
    finally:
        conn.close()


class ResearchUtilsTests(unittest.TestCase):
    def test_connect_readonly_missing_file_does_not_create_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.sqlite"
            with self.assertRaises(SystemExit):
                connect_readonly(path)
            self.assertFalse(path.exists())

    def test_connect_readonly_rejects_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus.sqlite"
            _create_alignment_db(path)
            with closing(connect_readonly(path)) as conn:
                with self.assertRaises(sqlite3.OperationalError):
                    conn.execute("CREATE TABLE should_fail(x INTEGER)")

    def test_strict_alignment_payload_pass_and_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            passing = Path(tmp) / "pass.sqlite"
            failing = Path(tmp) / "fail.sqlite"
            _create_alignment_db(passing)
            _create_alignment_db(failing, fail=True)

            with closing(connect_readonly(passing)) as conn:
                self.assertEqual(strict_alignment_payload(conn)["status"], "pass")
            with closing(connect_readonly(failing)) as conn:
                payload = strict_alignment_payload(conn)
                self.assertEqual(payload["status"], "fail")
                self.assertGreater(payload["speculative_input_edges"], 0)


if __name__ == "__main__":
    unittest.main()
