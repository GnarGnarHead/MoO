from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from constructionist_math import Graph, Node
from moo_graph_corpus import Key, bounded_key, format_key, normalize_key
from strict_stage_moo import OPS, _frontier_pairs, _result_for, build_strict_stage_graph


EdgeSignature = Tuple[int, str, str, str, str]


def _retain_result(
    key: Key,
    *,
    stage: int,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
    retain_confirmed_edges: bool,
) -> bool:
    p, q = key
    if retain_confirmed_edges and q == 1 and 1 <= p <= stage:
        return True
    return bounded_key(
        key,
        max_abs_p=max_abs_p,
        max_abs_q=max_abs_q,
        max_abs_value=max_abs_value,
    )


def _node_status(key: Key, *, first_stage: int) -> str:
    if key == (1, 1):
        return "certainty"
    p, q = key
    if q == 1 and p >= 1:
        if first_stage < p:
            return "speculative_until_confirmed"
        return "confirmed_by_core_loop"
    return "speculative"


def _strict_stage_memory_graph(
    *,
    max_stage: int,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
    retain_confirmed_edges: bool,
) -> Graph:
    graph = Graph()
    one = graph.get_or_create_ref(1)
    graph._record_edge("seed", [], one, {"stage": 1})  # noqa: SLF001
    operands: Dict[int, Node] = {1: one}

    for stage in range(1, int(max_stage) + 1):
        stage_node = graph._get_or_create_grounded_ref(stage)  # noqa: SLF001
        operands[stage] = stage_node
        for a, b in _frontier_pairs(stage):
            left = operands[a]
            right = operands[b]
            for op in OPS:
                result_key = _result_for(op, a, b)
                if not _retain_result(
                    result_key,
                    stage=stage,
                    max_abs_p=max_abs_p,
                    max_abs_q=max_abs_q,
                    max_abs_value=max_abs_value,
                    retain_confirmed_edges=retain_confirmed_edges,
                ):
                    continue
                result = graph._intern_value(  # noqa: SLF001
                    Fraction(int(result_key[0]), int(result_key[1])),
                    seed_op=op,
                    seed_inputs=[left, right],
                )
                graph._record_edge(op, [left, right], result, {"stage": stage})  # noqa: SLF001
    return graph


def _memory_node_rows(graph: Graph) -> Dict[Key, Dict[str, object]]:
    first_stage: Dict[Key, int] = {}
    for edge in graph.edges:
        key = graph.numeric_value(edge.output)
        if key is None:
            continue
        stage = int(edge.metadata.get("stage", 1))
        first_stage[key] = min(stage, first_stage.get(key, stage))

    rows: Dict[Key, Dict[str, object]] = {}
    for key, node in graph.nodes_by_value.items():
        normalized = normalize_key(*key)
        if normalized not in first_stage and normalized == (1, 1):
            first_stage[normalized] = 1
        stage = first_stage.get(normalized)
        if stage is None:
            continue
        p, q = normalized
        confirmed_stage = p if q == 1 and p >= 1 else None
        rows[normalized] = {
            "frac": format_key(normalized),
            "first_stage": int(stage),
            "confirmed_stage": confirmed_stage,
            "status": _node_status(normalized, first_stage=int(stage)),
            "node_status": node.status,
        }
    return rows


def _memory_edge_signatures(graph: Graph) -> Counter[EdgeSignature]:
    signatures: Counter[EdgeSignature] = Counter()
    for edge in graph.edges:
        result_key = graph.numeric_value(edge.output)
        if result_key is None:
            continue
        stage = int(edge.metadata.get("stage", 1))
        if edge.op == "seed":
            left = ""
            right = ""
        else:
            left_key = graph.numeric_value(edge.inputs[0])
            right_key = graph.numeric_value(edge.inputs[1])
            if left_key is None or right_key is None:
                continue
            left = format_key(left_key)
            right = format_key(right_key)
        signatures[(stage, edge.op, left, right, format_key(result_key))] += 1
    return signatures


def _sqlite_rows(path: Path) -> Tuple[Dict[Key, Dict[str, object]], Counter[EdgeSignature]]:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        node_rows: Dict[Key, Dict[str, object]] = {}
        for row in conn.execute("SELECT * FROM nodes"):
            key = normalize_key(int(row["p"]), int(row["q"]))
            first_stage = int(row["first_stage"])
            node_rows[key] = {
                "frac": format_key(key),
                "first_stage": first_stage,
                "confirmed_stage": int(row["confirmed_stage"])
                if row["confirmed_stage"] is not None
                else None,
                "status": _node_status(key, first_stage=first_stage),
                "kind": str(row["kind"]),
            }

        edge_rows = conn.execute(
            """
            SELECT
              e.stage,
              e.op,
              l.label AS left_label,
              r.label AS right_label,
              out.label AS result_label
            FROM edges e
            LEFT JOIN nodes l ON l.node_id = e.left_node_id
            LEFT JOIN nodes r ON r.node_id = e.right_node_id
            JOIN nodes out ON out.node_id = e.result_node_id
            """
        ).fetchall()
        edge_signatures: Counter[EdgeSignature] = Counter()
        for row in edge_rows:
            edge_signatures[
                (
                    int(row["stage"]),
                    str(row["op"]),
                    "" if row["left_label"] is None else str(row["left_label"]),
                    "" if row["right_label"] is None else str(row["right_label"]),
                    str(row["result_label"]),
                )
            ] += 1
        return node_rows, edge_signatures
    finally:
        conn.close()


def _sample_keys(keys: Iterable[Key], *, limit: int) -> List[str]:
    return [
        format_key(key)
        for key in sorted(keys, key=lambda item: (item[1], abs(item[0]), item[0]))[:limit]
    ]


def _sample_edges(edges: Iterable[EdgeSignature], *, limit: int) -> List[Dict[str, object]]:
    rows = []
    for stage, op, left, right, result in sorted(edges)[:limit]:
        rows.append(
            {
                "stage": stage,
                "op": op,
                "left": left,
                "right": right,
                "result": result,
            }
        )
    return rows


def run_alignment_check(
    *,
    max_stage: int,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
    retain_confirmed_edges: bool,
    sample_limit: int,
) -> Dict[str, object]:
    memory_graph = _strict_stage_memory_graph(
        max_stage=max_stage,
        max_abs_p=max_abs_p,
        max_abs_q=max_abs_q,
        max_abs_value=max_abs_value,
        retain_confirmed_edges=retain_confirmed_edges,
    )
    memory_nodes = _memory_node_rows(memory_graph)
    memory_edges = _memory_edge_signatures(memory_graph)

    with tempfile.TemporaryDirectory(prefix="moo_alignment_") as tmpdir:
        db_path = Path(tmpdir) / "strict_stage.sqlite"
        sqlite_summary = build_strict_stage_graph(
            db_path=db_path,
            max_stage=max_stage,
            max_abs_p=max_abs_p,
            max_abs_q=max_abs_q,
            max_abs_value=max_abs_value,
            max_edges=None,
            time_limit_seconds=None,
            commit_every=max_stage,
            retain_confirmed_edges=retain_confirmed_edges,
            verbose=False,
        )
        sqlite_nodes, sqlite_edges = _sqlite_rows(db_path)

    memory_node_keys = set(memory_nodes)
    sqlite_node_keys = set(sqlite_nodes)
    memory_edge_set = set(memory_edges)
    sqlite_edge_set = set(sqlite_edges)
    common_nodes = memory_node_keys.intersection(sqlite_node_keys)
    first_stage_mismatches = [
        key
        for key in common_nodes
        if memory_nodes[key]["first_stage"] != sqlite_nodes[key]["first_stage"]
    ]
    confirmed_stage_mismatches = [
        key
        for key in common_nodes
        if memory_nodes[key]["confirmed_stage"] != sqlite_nodes[key]["confirmed_stage"]
    ]
    edge_count_mismatches = [
        edge
        for edge in memory_edge_set.intersection(sqlite_edge_set)
        if memory_edges[edge] != sqlite_edges[edge]
    ]

    missing_in_sqlite = memory_node_keys - sqlite_node_keys
    missing_in_memory = sqlite_node_keys - memory_node_keys
    edges_missing_in_sqlite = memory_edge_set - sqlite_edge_set
    edges_missing_in_memory = sqlite_edge_set - memory_edge_set

    passed = not (
        missing_in_sqlite
        or missing_in_memory
        or edges_missing_in_sqlite
        or edges_missing_in_memory
        or first_stage_mismatches
        or confirmed_stage_mismatches
        or edge_count_mismatches
    )
    return {
        "passed": passed,
        "config": {
            "max_stage": int(max_stage),
            "max_abs_p": int(max_abs_p),
            "max_abs_q": int(max_abs_q),
            "max_abs_value": max_abs_value,
            "retain_confirmed_edges": retain_confirmed_edges,
        },
        "memory": {
            "nodes": len(memory_nodes),
            "edges": sum(memory_edges.values()),
        },
        "sqlite": {
            "nodes": len(sqlite_nodes),
            "edges": sum(sqlite_edges.values()),
            "summary": sqlite_summary,
        },
        "differences": {
            "nodes_missing_in_sqlite": _sample_keys(missing_in_sqlite, limit=sample_limit),
            "nodes_missing_in_memory": _sample_keys(missing_in_memory, limit=sample_limit),
            "first_stage_mismatches": _sample_keys(first_stage_mismatches, limit=sample_limit),
            "confirmed_stage_mismatches": _sample_keys(
                confirmed_stage_mismatches,
                limit=sample_limit,
            ),
            "edges_missing_in_sqlite": _sample_edges(
                edges_missing_in_sqlite,
                limit=sample_limit,
            ),
            "edges_missing_in_memory": _sample_edges(
                edges_missing_in_memory,
                limit=sample_limit,
            ),
            "edge_count_mismatches": _sample_edges(edge_count_mismatches, limit=sample_limit),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check small strict-stage MoO agreement between in-memory and SQLite graph paths."
    )
    parser.add_argument("--max-stage", type=int, default=6)
    parser.add_argument("--max-abs-p", type=int, default=50)
    parser.add_argument("--max-abs-q", type=int, default=50)
    parser.add_argument("--max-abs-value", type=float, default=4.0)
    parser.add_argument("--drop-confirmed-edge-exemption", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=12)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = run_alignment_check(
        max_stage=max(1, int(args.max_stage)),
        max_abs_p=max(0, int(args.max_abs_p)),
        max_abs_q=max(1, int(args.max_abs_q)),
        max_abs_value=float(args.max_abs_value)
        if args.max_abs_value is not None
        else None,
        retain_confirmed_edges=not bool(args.drop_confirmed_edge_exemption),
        sample_limit=max(1, int(args.sample_limit)),
    )
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
