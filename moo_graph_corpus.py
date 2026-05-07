from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, Optional, Tuple


SCHEMA_VERSION = 1
Key = Tuple[int, int]


@dataclass(frozen=True)
class GraphCorpusConfig:
    generator: str
    max_stage: int
    max_abs_p: int
    max_abs_q: int
    max_abs_value: Optional[float]
    retain_confirmed_edges: bool = True

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "generator": self.generator,
            "max_stage": int(self.max_stage),
            "max_abs_p": int(self.max_abs_p),
            "max_abs_q": int(self.max_abs_q),
            "max_abs_value": float(self.max_abs_value)
            if self.max_abs_value is not None
            else None,
            "retain_confirmed_edges": bool(self.retain_confirmed_edges),
        }


def normalize_key(p: int, q: int = 1) -> Key:
    if q == 0:
        raise ZeroDivisionError("zero denominator")
    if q < 0:
        p = -p
        q = -q
    value = Fraction(int(p), int(q))
    return int(value.numerator), int(value.denominator)


def format_key(key: Key) -> str:
    p, q = key
    if q == 1:
        return str(p)
    return f"{p}/{q}"


def node_kind(key: Key) -> str:
    p, q = key
    if key == (1, 1):
        return "certainty"
    if q == 1 and p > 1:
        return "positive_integer"
    if q == 1:
        return "relational_integer"
    return "rational"


def confirmed_stage_for_key(key: Key) -> Optional[int]:
    p, q = key
    if q == 1 and p >= 1:
        return int(p)
    return None


def bounded_key(
    key: Key,
    *,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
) -> bool:
    p, q = key
    if abs(p) > int(max_abs_p):
        return False
    if abs(q) > int(max_abs_q):
        return False
    if max_abs_value is not None and abs(p / q) > float(max_abs_value):
        return False
    return True


class GraphCorpus:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "GraphCorpus":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if exc_type is None:
            self.conn.commit()
        self.close()

    def init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS nodes (
              node_id INTEGER PRIMARY KEY AUTOINCREMENT,
              p INTEGER NOT NULL,
              q INTEGER NOT NULL,
              label TEXT NOT NULL,
              kind TEXT NOT NULL,
              first_stage INTEGER NOT NULL,
              confirmed_stage INTEGER,
              first_edge_id INTEGER,
              UNIQUE(p, q)
            );

            CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
            CREATE INDEX IF NOT EXISTS idx_nodes_first_stage ON nodes(first_stage);
            CREATE INDEX IF NOT EXISTS idx_nodes_confirmed_stage ON nodes(confirmed_stage);

            CREATE TABLE IF NOT EXISTS edges (
              edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
              stage INTEGER NOT NULL,
              op TEXT NOT NULL,
              left_node_id INTEGER,
              right_node_id INTEGER,
              result_node_id INTEGER NOT NULL,
              FOREIGN KEY(left_node_id) REFERENCES nodes(node_id),
              FOREIGN KEY(right_node_id) REFERENCES nodes(node_id),
              FOREIGN KEY(result_node_id) REFERENCES nodes(node_id)
            );

            CREATE INDEX IF NOT EXISTS idx_edges_stage ON edges(stage);
            CREATE INDEX IF NOT EXISTS idx_edges_op ON edges(op);
            CREATE INDEX IF NOT EXISTS idx_edges_left ON edges(left_node_id);
            CREATE INDEX IF NOT EXISTS idx_edges_right ON edges(right_node_id);
            CREATE INDEX IF NOT EXISTS idx_edges_result ON edges(result_node_id);

            CREATE TABLE IF NOT EXISTS stages (
              stage INTEGER PRIMARY KEY,
              candidate_events INTEGER NOT NULL,
              retained_events INTEGER NOT NULL,
              new_nodes INTEGER NOT NULL,
              new_edges INTEGER NOT NULL,
              total_nodes INTEGER NOT NULL,
              total_edges INTEGER NOT NULL,
              elapsed_seconds REAL NOT NULL
            );

            CREATE VIEW IF NOT EXISTS node_stats AS
              SELECT
                n.node_id,
                n.p,
                n.q,
                n.label,
                n.kind,
                n.first_stage,
                n.confirmed_stage,
                COUNT(e.edge_id) AS derivation_events,
                SUM(CASE WHEN e.op = '+' THEN 1 ELSE 0 END) AS plus_count,
                SUM(CASE WHEN e.op = '-' THEN 1 ELSE 0 END) AS minus_count,
                SUM(CASE WHEN e.op = '*' THEN 1 ELSE 0 END) AS multiply_count,
                SUM(CASE WHEN e.op = '/' THEN 1 ELSE 0 END) AS divide_count
              FROM nodes n
              LEFT JOIN edges e ON e.result_node_id = n.node_id
              GROUP BY n.node_id;
            """
        )
        self._set_meta_if_missing("schema_version", str(SCHEMA_VERSION))

    def _set_meta_if_missing(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO NOTHING",
            (key, value),
        )

    def _set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    def _get_meta(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return str(row["value"])

    def ensure_config(self, config: GraphCorpusConfig) -> None:
        stored = self._get_meta("config_json")
        expected = config.to_jsonable()
        if stored is None:
            self._set_meta("config_json", json.dumps(expected, sort_keys=True))
            self.conn.commit()
            return
        try:
            parsed = json.loads(stored)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Corpus has invalid config_json") from exc
        if parsed != expected:
            raise RuntimeError(
                "Graph corpus config mismatch. Refusing to mix semantics.\n"
                f"stored={parsed}\nexpected={expected}"
            )

    def node_id_for_key(self, key: Key) -> Optional[int]:
        row = self.conn.execute(
            "SELECT node_id FROM nodes WHERE p = ? AND q = ?",
            (int(key[0]), int(key[1])),
        ).fetchone()
        if row is None:
            return None
        return int(row["node_id"])

    def ensure_node(self, key: Key, *, first_stage: int) -> Tuple[int, bool]:
        key = normalize_key(*key)
        confirmed_stage = confirmed_stage_for_key(key)
        row = self.conn.execute(
            "SELECT node_id, first_stage, confirmed_stage FROM nodes WHERE p = ? AND q = ?",
            (int(key[0]), int(key[1])),
        ).fetchone()
        if row is None:
            cur = self.conn.execute(
                "INSERT INTO nodes(p, q, label, kind, first_stage, confirmed_stage) "
                "VALUES(?, ?, ?, ?, ?, ?)",
                (
                    int(key[0]),
                    int(key[1]),
                    format_key(key),
                    node_kind(key),
                    int(first_stage),
                    confirmed_stage,
                ),
            )
            return int(cur.lastrowid), True

        node_id = int(row["node_id"])
        old_first = int(row["first_stage"])
        old_confirmed = row["confirmed_stage"]
        if int(first_stage) < old_first or (
            confirmed_stage is not None and old_confirmed is None
        ):
            self.conn.execute(
                "UPDATE nodes SET first_stage = ?, confirmed_stage = COALESCE(confirmed_stage, ?) "
                "WHERE node_id = ?",
                (min(int(first_stage), old_first), confirmed_stage, node_id),
            )
        return node_id, False

    def ensure_core_integer(self, n: int) -> Tuple[int, bool]:
        return self.ensure_node((int(n), 1), first_stage=int(n))

    def insert_edge(
        self,
        *,
        stage: int,
        op: str,
        left_node_id: Optional[int],
        right_node_id: Optional[int],
        result_node_id: int,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id) "
            "VALUES(?, ?, ?, ?, ?)",
            (
                int(stage),
                str(op),
                int(left_node_id) if left_node_id is not None else None,
                int(right_node_id) if right_node_id is not None else None,
                int(result_node_id),
            ),
        )
        edge_id = int(cur.lastrowid)
        self.conn.execute(
            "UPDATE nodes SET first_edge_id = COALESCE(first_edge_id, ?) WHERE node_id = ?",
            (edge_id, int(result_node_id)),
        )
        return edge_id

    def record_stage(
        self,
        *,
        stage: int,
        candidate_events: int,
        retained_events: int,
        new_nodes: int,
        new_edges: int,
        elapsed_seconds: float,
    ) -> None:
        total_nodes = int(self.conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"])
        total_edges = int(self.conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"])
        self.conn.execute(
            "INSERT INTO stages(stage, candidate_events, retained_events, new_nodes, "
            "new_edges, total_nodes, total_edges, elapsed_seconds) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (
                int(stage),
                int(candidate_events),
                int(retained_events),
                int(new_nodes),
                int(new_edges),
                total_nodes,
                total_edges,
                float(elapsed_seconds),
            ),
        )

    def summary(self) -> Dict[str, object]:
        node_count = int(self.conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"])
        edge_count = int(self.conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"])
        max_stage_row = self.conn.execute("SELECT MAX(stage) AS s FROM stages").fetchone()
        max_stage = int(max_stage_row["s"]) if max_stage_row["s"] is not None else 0
        kind_rows = self.conn.execute(
            "SELECT kind, COUNT(*) AS n FROM nodes GROUP BY kind ORDER BY kind"
        ).fetchall()
        op_rows = self.conn.execute(
            "SELECT op, COUNT(*) AS n FROM edges GROUP BY op ORDER BY op"
        ).fetchall()
        non_core_operand_edges = int(
            self.conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM edges e
                JOIN nodes l ON l.node_id = e.left_node_id
                JOIN nodes r ON r.node_id = e.right_node_id
                WHERE e.op != 'seed'
                  AND (
                    NOT (l.q = 1 AND l.p >= 1 AND l.p <= e.stage)
                    OR NOT (r.q = 1 AND r.p >= 1 AND r.p <= e.stage)
                  )
                """
            ).fetchone()["n"]
        )
        speculative_input_edges = int(
            self.conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM edges e
                JOIN nodes l ON l.node_id = e.left_node_id
                JOIN nodes r ON r.node_id = e.right_node_id
                WHERE e.op != 'seed'
                  AND (
                    l.confirmed_stage IS NULL
                    OR r.confirmed_stage IS NULL
                    OR l.confirmed_stage > e.stage
                    OR r.confirmed_stage > e.stage
                  )
                """
            ).fetchone()["n"]
        )
        return {
            "max_stage": max_stage,
            "nodes": node_count,
            "edges": edge_count,
            "node_kinds": {str(row["kind"]): int(row["n"]) for row in kind_rows},
            "edge_ops": {str(row["op"]): int(row["n"]) for row in op_rows},
            "alignment": {
                "operand_rule": (
                    "positive-spine strict corpus: only confirmed positive-spine "
                    "iterations may be operands"
                ),
                "speculative_nodes_are_operands": False,
                "speculative_input_edges": speculative_input_edges,
                "non_core_operand_edges": non_core_operand_edges,
                "status": "pass"
                if speculative_input_edges == 0 and non_core_operand_edges == 0
                else "fail",
            },
        }
