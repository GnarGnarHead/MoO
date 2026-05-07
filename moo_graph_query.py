from __future__ import annotations

import argparse
from fractions import Fraction
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from moo_graph_corpus import format_key, normalize_key
from moo_research_utils import connect_readonly, positive_int


Key = Tuple[int, int]


def _parse_key(raw: str) -> Key:
    value = Fraction(str(raw))
    return normalize_key(int(value.numerator), int(value.denominator))


def _connect(path: Path) -> sqlite3.Connection:
    return connect_readonly(path)


def _node_status(row: sqlite3.Row) -> str:
    key = int(row["p"]), int(row["q"])
    first_stage = int(row["first_stage"])
    confirmed_stage = row["confirmed_stage"]
    if key == (1, 1):
        return "certainty"
    if confirmed_stage is None:
        return "speculative"
    if first_stage < int(confirmed_stage):
        return "speculative_until_confirmed"
    return "confirmed_by_core_loop"


def _node_payload(row: sqlite3.Row) -> Dict[str, object]:
    return {
        "node_id": int(row["node_id"]),
        "frac": format_key((int(row["p"]), int(row["q"]))),
        "p": int(row["p"]),
        "q": int(row["q"]),
        "kind": str(row["kind"]),
        "status": _node_status(row),
        "first_stage": int(row["first_stage"]),
        "confirmed_stage": int(row["confirmed_stage"])
        if row["confirmed_stage"] is not None
        else None,
    }


def _edge_payload(row: sqlite3.Row) -> Dict[str, object]:
    return {
        "edge_id": int(row["edge_id"]),
        "stage": int(row["stage"]),
        "op": str(row["op"]),
        "left": row["left_label"],
        "right": row["right_label"],
        "result": row["result_label"],
    }


def _stats_payload(row: Optional[sqlite3.Row]) -> Dict[str, int]:
    return {
        "derivation_events": int(row["derivation_events"]) if row else 0,
        "+": int(row["plus_count"]) if row else 0,
        "-": int(row["minus_count"]) if row else 0,
        "*": int(row["multiply_count"]) if row else 0,
        "/": int(row["divide_count"]) if row else 0,
    }


def _node_for_key(conn: sqlite3.Connection, key: Key) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM nodes WHERE p = ? AND q = ?",
        (int(key[0]), int(key[1])),
    ).fetchone()


def _node_for_id(conn: sqlite3.Connection, node_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM nodes WHERE node_id = ?",
        (int(node_id),),
    ).fetchone()


def _node_stats(conn: sqlite3.Connection, node_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM node_stats WHERE node_id = ?",
        (int(node_id),),
    ).fetchone()


def _incoming_edges(conn: sqlite3.Connection, node_id: int, *, limit: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.label AS left_label,
          r.label AS right_label,
          out.label AS result_label
        FROM edges e
        LEFT JOIN nodes l ON l.node_id = e.left_node_id
        LEFT JOIN nodes r ON r.node_id = e.right_node_id
        JOIN nodes out ON out.node_id = e.result_node_id
        WHERE e.result_node_id = ?
        ORDER BY e.stage, e.edge_id
        LIMIT ?
        """,
        (int(node_id), int(limit)),
    ).fetchall()


def _outgoing_edges(conn: sqlite3.Connection, node_id: int, *, limit: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.label AS left_label,
          r.label AS right_label,
          out.label AS result_label
        FROM edges e
        LEFT JOIN nodes l ON l.node_id = e.left_node_id
        LEFT JOIN nodes r ON r.node_id = e.right_node_id
        JOIN nodes out ON out.node_id = e.result_node_id
        WHERE e.left_node_id = ? OR e.right_node_id = ?
        ORDER BY e.stage, e.edge_id
        LIMIT ?
        """,
        (int(node_id), int(node_id), int(limit)),
    ).fetchall()


def inspect_node(conn: sqlite3.Connection, key: Key, *, limit: int) -> Dict[str, object]:
    node = conn.execute(
        "SELECT * FROM nodes WHERE p = ? AND q = ?",
        (int(key[0]), int(key[1])),
    ).fetchone()
    if node is None:
        return {"found": False, "frac": format_key(key)}

    node_id = int(node["node_id"])
    payload = {
        "found": True,
        "node": _node_payload(node),
        "stats": _stats_payload(_node_stats(conn, node_id)),
        "incoming_edges": [_edge_payload(row) for row in _incoming_edges(conn, node_id, limit=limit)],
        "outgoing_edges": [_edge_payload(row) for row in _outgoing_edges(conn, node_id, limit=limit)],
    }
    return payload


def _input_node_ids(conn: sqlite3.Connection, node_id: int) -> Set[int]:
    rows = conn.execute(
        """
        SELECT left_node_id AS node_id FROM edges
        WHERE result_node_id = ? AND left_node_id IS NOT NULL
        UNION
        SELECT right_node_id AS node_id FROM edges
        WHERE result_node_id = ? AND right_node_id IS NOT NULL
        """,
        (int(node_id), int(node_id)),
    ).fetchall()
    return {int(row["node_id"]) for row in rows}


def _nodes_by_ids(conn: sqlite3.Connection, node_ids: Set[int], *, limit: int) -> List[Dict[str, object]]:
    if not node_ids:
        return []
    placeholders = ",".join("?" for _ in node_ids)
    rows = conn.execute(
        f"""
        SELECT *
        FROM nodes
        WHERE node_id IN ({placeholders})
        ORDER BY COALESCE(confirmed_stage, 999999999), first_stage, q, p
        LIMIT ?
        """,
        tuple(sorted(node_ids)) + (int(limit),),
    ).fetchall()
    return [_node_payload(row) for row in rows]


def _nearby_result_rows(conn: sqlite3.Connection, node_id: int, *, limit: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        WITH input_nodes(node_id) AS (
          SELECT left_node_id FROM edges
          WHERE result_node_id = ? AND left_node_id IS NOT NULL
          UNION
          SELECT right_node_id FROM edges
          WHERE result_node_id = ? AND right_node_id IS NOT NULL
        )
        SELECT
          out.*,
          COUNT(e.edge_id) AS shared_operand_edges,
          GROUP_CONCAT(DISTINCT e.op) AS shared_ops,
          MIN(e.stage) AS first_shared_stage
        FROM edges e
        JOIN nodes out ON out.node_id = e.result_node_id
        WHERE out.node_id != ?
          AND (
            e.left_node_id IN (SELECT node_id FROM input_nodes)
            OR e.right_node_id IN (SELECT node_id FROM input_nodes)
          )
        GROUP BY out.node_id
        ORDER BY shared_operand_edges DESC, first_shared_stage ASC, out.q ASC, ABS(out.p) ASC
        LIMIT ?
        """,
        (int(node_id), int(node_id), int(node_id), int(limit)),
    ).fetchall()


def _nearby_payload(row: sqlite3.Row) -> Dict[str, object]:
    payload = _node_payload(row)
    payload["shared_operand_edges"] = int(row["shared_operand_edges"])
    payload["shared_ops"] = [] if row["shared_ops"] is None else str(row["shared_ops"]).split(",")
    payload["first_shared_stage"] = int(row["first_shared_stage"])
    return payload


def node_neighborhood(conn: sqlite3.Connection, key: Key, *, limit: int) -> Dict[str, object]:
    node = _node_for_key(conn, key)
    if node is None:
        return {"found": False, "frac": format_key(key)}
    node_id = int(node["node_id"])
    return {
        "found": True,
        "target": inspect_node(conn, key, limit=limit),
        "input_nodes": _nodes_by_ids(conn, _input_node_ids(conn, node_id), limit=limit),
        "nearby_results": [
            _nearby_payload(row)
            for row in _nearby_result_rows(conn, node_id, limit=limit)
        ],
    }


def compare_nodes(conn: sqlite3.Connection, left_key: Key, right_key: Key, *, limit: int) -> Dict[str, object]:
    left = _node_for_key(conn, left_key)
    right = _node_for_key(conn, right_key)
    if left is None or right is None:
        return {
            "found": False,
            "left": {"found": left is not None, "frac": format_key(left_key)},
            "right": {"found": right is not None, "frac": format_key(right_key)},
        }

    left_id = int(left["node_id"])
    right_id = int(right["node_id"])
    left_stats = _stats_payload(_node_stats(conn, left_id))
    right_stats = _stats_payload(_node_stats(conn, right_id))
    left_inputs = _input_node_ids(conn, left_id)
    right_inputs = _input_node_ids(conn, right_id)
    left_nearby = {int(row["node_id"]): row for row in _nearby_result_rows(conn, left_id, limit=limit * 4)}
    right_nearby = {int(row["node_id"]): row for row in _nearby_result_rows(conn, right_id, limit=limit * 4)}
    shared_nearby_ids = set(left_nearby).intersection(right_nearby)
    shared_nearby = []
    for node_id in sorted(
        shared_nearby_ids,
        key=lambda nid: (
            -int(left_nearby[nid]["shared_operand_edges"]) - int(right_nearby[nid]["shared_operand_edges"]),
            int(left_nearby[nid]["first_shared_stage"]),
        ),
    )[:limit]:
        payload = _node_payload(left_nearby[node_id])
        payload["left_shared_operand_edges"] = int(left_nearby[node_id]["shared_operand_edges"])
        payload["right_shared_operand_edges"] = int(right_nearby[node_id]["shared_operand_edges"])
        shared_nearby.append(payload)

    return {
        "found": True,
        "left": {
            "node": _node_payload(left),
            "stats": left_stats,
        },
        "right": {
            "node": _node_payload(right),
            "stats": right_stats,
        },
        "same_node": left_id == right_id,
        "shared_input_nodes": _nodes_by_ids(
            conn,
            left_inputs.intersection(right_inputs),
            limit=limit,
        ),
        "operation_delta": {
            op: left_stats[op] - right_stats[op]
            for op in ("derivation_events", "+", "-", "*", "/")
        },
        "shared_nearby_results": shared_nearby,
    }


def later_confirmed_nodes(conn: sqlite3.Connection, *, limit: int) -> List[Dict[str, object]]:
    rows = conn.execute(
        """
        SELECT n.*, s.derivation_events, s.plus_count, s.minus_count, s.multiply_count, s.divide_count
        FROM nodes n
        JOIN node_stats s ON s.node_id = n.node_id
        WHERE n.confirmed_stage IS NOT NULL
          AND n.first_stage < n.confirmed_stage
        ORDER BY n.confirmed_stage, n.first_stage, n.q, n.p
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()
    payloads = []
    for row in rows:
        payload = _node_payload(row)
        payload["speculative_for_stages"] = int(row["confirmed_stage"]) - int(row["first_stage"])
        payload["stats"] = _stats_payload(row)
        payloads.append(payload)
    return payloads


def corpus_summary(conn: sqlite3.Connection) -> Dict[str, object]:
    config = conn.execute("SELECT value FROM meta WHERE key = 'config_json'").fetchone()
    latest_stage = conn.execute(
        """
        SELECT *
        FROM stages
        ORDER BY stage DESC
        LIMIT 1
        """
    ).fetchone()
    node_kinds = conn.execute(
        "SELECT kind, COUNT(*) AS n FROM nodes GROUP BY kind ORDER BY kind"
    ).fetchall()
    edge_ops = conn.execute(
        "SELECT op, COUNT(*) AS n FROM edges GROUP BY op ORDER BY op"
    ).fetchall()
    operand_violations = conn.execute(
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
    ).fetchone()
    speculative_input_edges = conn.execute(
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
    ).fetchone()
    return {
        "config": json.loads(config["value"]) if config is not None else None,
        "nodes": int(conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]),
        "edges": int(conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]),
        "latest_stage": dict(latest_stage) if latest_stage is not None else None,
        "node_kinds": {str(row["kind"]): int(row["n"]) for row in node_kinds},
        "edge_ops": {str(row["op"]): int(row["n"]) for row in edge_ops},
        "alignment": {
            "operand_rule": "only confirmed positive core-loop iterations may be operands",
            "speculative_nodes_are_operands": False,
            "speculative_input_edges": int(speculative_input_edges["n"]),
            "non_core_operand_edges": int(operand_violations["n"]),
            "status": "pass"
            if int(speculative_input_edges["n"]) == 0 and int(operand_violations["n"]) == 0
            else "fail",
        },
    }


def top_nodes(conn: sqlite3.Connection, *, limit: int) -> List[Dict[str, object]]:
    rows = conn.execute(
        """
        SELECT *
        FROM node_stats
        ORDER BY derivation_events DESC, q ASC, ABS(p) ASC, p ASC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()
    out: List[Dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "node_id": int(row["node_id"]),
                "frac": format_key((int(row["p"]), int(row["q"]))),
                "kind": str(row["kind"]),
                "status": _node_status(row),
                "first_stage": int(row["first_stage"]),
                "confirmed_stage": int(row["confirmed_stage"])
                if row["confirmed_stage"] is not None
                else None,
                "derivation_events": int(row["derivation_events"]),
                "operation_signature": {
                    "+": int(row["plus_count"]),
                    "-": int(row["minus_count"]),
                    "*": int(row["multiply_count"]),
                    "/": int(row["divide_count"]),
                },
            }
        )
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query a strict-stage MoO graph corpus.")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--node", help="Fraction to inspect, e.g. 34/21.")
    parser.add_argument(
        "--neighborhood",
        action="store_true",
        help="With --node, show input nodes and nearby results sharing those inputs.",
    )
    parser.add_argument("--compare", nargs=2, metavar=("A", "B"), help="Compare two nodes.")
    parser.add_argument(
        "--confirmations",
        action="store_true",
        help="List values seen speculatively before the core loop confirmed them.",
    )
    parser.add_argument("--top-derived", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--limit", type=positive_int, default=25)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    with closing(_connect(Path(args.db))) as conn:
        if args.node and args.neighborhood:
            payload: object = node_neighborhood(conn, _parse_key(str(args.node)), limit=int(args.limit))
        elif args.node:
            payload: object = inspect_node(conn, _parse_key(str(args.node)), limit=int(args.limit))
        elif args.compare:
            left, right = args.compare
            payload = compare_nodes(
                conn,
                _parse_key(str(left)),
                _parse_key(str(right)),
                limit=int(args.limit),
            )
        elif args.confirmations:
            payload = {"later_confirmed": later_confirmed_nodes(conn, limit=int(args.limit))}
        elif args.top_derived:
            payload = {"top_derived": top_nodes(conn, limit=int(args.limit))}
        elif args.summary:
            payload = corpus_summary(conn)
        else:
            raise SystemExit(
                "Pass --node <fraction>, --node <fraction> --neighborhood, "
                "--compare A B, --confirmations, --top-derived, or --summary."
            )
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
