from __future__ import annotations

import argparse
import json
import math
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from moo_graph_corpus import format_key, normalize_key


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    limit = math.isqrt(n)
    for candidate in range(3, limit + 1, 2):
        if n % candidate == 0:
            return False
    return True


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _node_id_for_int(conn: sqlite3.Connection, value: int) -> Optional[int]:
    key = normalize_key(int(value), 1)
    row = conn.execute(
        "SELECT node_id FROM nodes WHERE p = ? AND q = ?",
        (int(key[0]), int(key[1])),
    ).fetchone()
    if row is None:
        return None
    return int(row["node_id"])


def _node_status(row: sqlite3.Row) -> str:
    p, q = int(row["p"]), int(row["q"])
    first_stage = int(row["first_stage"])
    confirmed_stage = row["confirmed_stage"]
    if (p, q) == (1, 1):
        return "certainty"
    if confirmed_stage is None:
        return "speculative"
    if first_stage < int(confirmed_stage):
        return "speculative_until_confirmed"
    return "confirmed_by_core_loop"


def _edge_payload(row: sqlite3.Row) -> Dict[str, object]:
    return {
        "edge_id": int(row["edge_id"]),
        "stage": int(row["stage"]),
        "op": str(row["op"]),
        "left": row["left_label"],
        "right": row["right_label"],
        "result": row["result_label"],
    }


def _inspect_int(conn: sqlite3.Connection, value: int, *, edge_limit: int) -> Dict[str, object]:
    key = normalize_key(int(value), 1)
    node = conn.execute(
        "SELECT * FROM nodes WHERE p = ? AND q = ?",
        (int(key[0]), int(key[1])),
    ).fetchone()
    if node is None:
        return {"found": False, "frac": format_key(key), "p": int(key[0]), "q": int(key[1])}

    node_id = int(node["node_id"])
    stats = conn.execute("SELECT * FROM node_stats WHERE node_id = ?", (node_id,)).fetchone()
    incoming = conn.execute(
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
        (node_id, int(edge_limit)),
    ).fetchall()
    return {
        "found": True,
        "node_id": node_id,
        "frac": format_key(key),
        "kind": str(node["kind"]),
        "status": _node_status(node),
        "first_stage": int(node["first_stage"]),
        "confirmed_stage": int(node["confirmed_stage"])
        if node["confirmed_stage"] is not None
        else None,
        "stats": {
            "derivation_events": int(stats["derivation_events"]) if stats else 0,
            "+": int(stats["plus_count"]) if stats else 0,
            "-": int(stats["minus_count"]) if stats else 0,
            "*": int(stats["multiply_count"]) if stats else 0,
            "/": int(stats["divide_count"]) if stats else 0,
        },
        "incoming_edges": [_edge_payload(row) for row in incoming],
    }


def _edge_exists(
    conn: sqlite3.Connection,
    *,
    left_value: int,
    op: str,
    right_value: int,
    result_value: int,
    allow_commuted: bool,
) -> bool:
    left_id = _node_id_for_int(conn, left_value)
    right_id = _node_id_for_int(conn, right_value)
    result_id = _node_id_for_int(conn, result_value)
    if left_id is None or right_id is None or result_id is None:
        return False
    candidates = [(left_id, right_id)]
    if allow_commuted and left_id != right_id:
        candidates.append((right_id, left_id))
    for left_candidate, right_candidate in candidates:
        row = conn.execute(
            """
            SELECT 1
            FROM edges
            WHERE left_node_id = ?
              AND right_node_id = ?
              AND result_node_id = ?
              AND op = ?
            LIMIT 1
            """,
            (left_candidate, right_candidate, result_id, op),
        ).fetchone()
        if row is not None:
            return True
    return False


def _power_final_edge_exists(conn: sqlite3.Connection, *, base: int, exponent: int) -> bool:
    if exponent <= 1:
        return True
    return _edge_exists(
        conn,
        left_value=base ** (exponent - 1),
        op="*",
        right_value=base,
        result_value=base**exponent,
        allow_commuted=True,
    )


def _return_payload(
    conn: sqlite3.Connection,
    *,
    base: int,
    modulus: int,
    edge_limit: int,
) -> Dict[str, object]:
    power = base**modulus
    delta = power - base
    integral_return = delta % modulus == 0
    quotient = delta // modulus if integral_return else None
    values = {
        "a": int(base),
        "m": int(modulus),
        "a^m": int(power),
        "a^m-a": int(delta),
        "(a^m-a)/m": int(quotient) if quotient is not None else None,
        "integral_return": bool(integral_return),
    }
    graph = {
        "a": _inspect_int(conn, base, edge_limit=edge_limit),
        "m": _inspect_int(conn, modulus, edge_limit=edge_limit),
        "a^m": _inspect_int(conn, power, edge_limit=edge_limit),
        "a^m-a": _inspect_int(conn, delta, edge_limit=edge_limit),
        "quotient": _inspect_int(conn, quotient, edge_limit=edge_limit)
        if quotient is not None
        else None,
    }
    corridor_edges = {
        "power_final_multiply": _power_final_edge_exists(conn, base=base, exponent=modulus),
        "delta_subtraction": _edge_exists(
            conn,
            left_value=power,
            op="-",
            right_value=base,
            result_value=delta,
            allow_commuted=False,
        ),
        "return_division": _edge_exists(
            conn,
            left_value=delta,
            op="/",
            right_value=modulus,
            result_value=quotient,
            allow_commuted=False,
        )
        if quotient is not None
        else False,
    }
    main_nodes = ["a", "m", "a^m", "a^m-a"]
    if quotient is not None:
        main_nodes.append("quotient")
    found_nodes = sum(1 for name in main_nodes if graph[name] is not None and bool(graph[name].get("found")))
    found_edges = sum(1 for value in corridor_edges.values() if value)
    return {
        "a": int(base),
        "m": int(modulus),
        "modulus_is_prime": _is_prime(modulus),
        "values": values,
        "graph_presence": {
            "found_corridor_nodes": found_nodes,
            "total_corridor_nodes": len(main_nodes),
            "found_corridor_edges": found_edges,
            "total_corridor_edges": len(corridor_edges),
            "full_corridor_nodes_found": found_nodes == len(main_nodes),
            "full_corridor_edges_found": found_edges == len(corridor_edges),
        },
        "corridor_edges": corridor_edges,
        "graph": graph,
    }


def _modulus_summary(rows: List[Dict[str, object]]) -> Dict[str, object]:
    total = len(rows)
    integral = sum(1 for row in rows if bool(row["values"]["integral_return"]))  # type: ignore[index]
    full_nodes = sum(1 for row in rows if bool(row["graph_presence"]["full_corridor_nodes_found"]))  # type: ignore[index]
    full_edges = sum(1 for row in rows if bool(row["graph_presence"]["full_corridor_edges_found"]))  # type: ignore[index]
    edge_hits = sum(int(row["graph_presence"]["found_corridor_edges"]) for row in rows)  # type: ignore[index]
    node_hits = sum(int(row["graph_presence"]["found_corridor_nodes"]) for row in rows)  # type: ignore[index]
    return {
        "m": int(rows[0]["m"]) if rows else None,
        "modulus_is_prime": bool(rows[0]["modulus_is_prime"]) if rows else None,
        "cases": total,
        "integral_returns": integral,
        "integral_return_rate": float(integral / total) if total else 0.0,
        "full_corridor_node_cases": full_nodes,
        "full_corridor_edge_cases": full_edges,
        "avg_corridor_nodes_found": float(node_hits / total) if total else 0.0,
        "avg_corridor_edges_found": float(edge_hits / total) if total else 0.0,
    }


def fermat_little_probe(
    *,
    db_path: Path,
    min_modulus: int,
    max_modulus: int,
    min_base: int,
    max_base: int,
    top_k: int,
    edge_limit: int,
) -> Dict[str, object]:
    by_modulus: Dict[int, List[Dict[str, object]]] = {}
    rows: List[Dict[str, object]] = []
    with _connect(db_path) as conn:
        for modulus in range(min_modulus, max_modulus + 1):
            if modulus < 2:
                continue
            for base in range(min_base, max_base + 1):
                payload = _return_payload(
                    conn,
                    base=base,
                    modulus=modulus,
                    edge_limit=edge_limit,
                )
                rows.append(payload)
                by_modulus.setdefault(modulus, []).append(payload)

    summaries = [_modulus_summary(items) for _, items in sorted(by_modulus.items())]
    prime_summaries = [row for row in summaries if row["modulus_is_prime"]]
    composite_summaries = [row for row in summaries if not row["modulus_is_prime"]]
    graph_rich = sorted(
        rows,
        key=lambda row: (
            -int(row["graph_presence"]["found_corridor_edges"]),  # type: ignore[index]
            -int(row["graph_presence"]["found_corridor_nodes"]),  # type: ignore[index]
            not bool(row["values"]["integral_return"]),  # type: ignore[index]
            row["m"],
            row["a"],
        ),
    )[:top_k]
    failures = [
        row
        for row in rows
        if bool(row["modulus_is_prime"]) and not bool(row["values"]["integral_return"])  # type: ignore[index]
    ][:top_k]
    composite_returns = [
        row
        for row in rows
        if not bool(row["modulus_is_prime"]) and bool(row["values"]["integral_return"])  # type: ignore[index]
    ][:top_k]
    return {
        "framing": {
            "probe": "Fermat Little return-corridor probe",
            "equation": "a^m - a, inspected through division by m",
            "moo_rule": (
                "Modular arithmetic and exponentiation are not added as primitives. "
                "The probe computes return targets externally and inspects graph nodes, "
                "corridor edges, and prime/composite contrast."
            ),
            "certainty_anchor_rule": (
                "Base 1 is retained by default. In MoO, self-reference through 1 is "
                "not trivial noise; it is the certainty anchor that makes later "
                "correlations interpretable."
            ),
            "inspection_rule": "The structural signal is return-corridor shape, not mere existence.",
        },
        "db": str(db_path),
        "config": {
            "min_modulus": int(min_modulus),
            "max_modulus": int(max_modulus),
            "min_base": int(min_base),
            "max_base": int(max_base),
            "top_k": int(top_k),
            "edge_limit": int(edge_limit),
        },
        "modulus_summaries": summaries,
        "prime_summary": {
            "moduli": [row["m"] for row in prime_summaries],
            "avg_integral_return_rate": sum(float(row["integral_return_rate"]) for row in prime_summaries)
            / len(prime_summaries)
            if prime_summaries
            else None,
            "avg_corridor_edges_found": sum(float(row["avg_corridor_edges_found"]) for row in prime_summaries)
            / len(prime_summaries)
            if prime_summaries
            else None,
        },
        "composite_summary": {
            "moduli": [row["m"] for row in composite_summaries],
            "avg_integral_return_rate": sum(float(row["integral_return_rate"]) for row in composite_summaries)
            / len(composite_summaries)
            if composite_summaries
            else None,
            "avg_corridor_edges_found": sum(float(row["avg_corridor_edges_found"]) for row in composite_summaries)
            / len(composite_summaries)
            if composite_summaries
            else None,
        },
        "prime_return_failures": failures,
        "composite_integral_returns": composite_returns,
        "graph_rich_returns": graph_rich,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe Fermat Little return corridors against a MoO graph corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--min-modulus", type=int, default=2)
    parser.add_argument("--max-modulus", type=int, default=12)
    parser.add_argument("--min-base", type=int, default=1)
    parser.add_argument("--max-base", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--edge-limit", type=int, default=3)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = fermat_little_probe(
        db_path=Path(args.db),
        min_modulus=max(2, int(args.min_modulus)),
        max_modulus=max(2, int(args.max_modulus)),
        min_base=max(1, int(args.min_base)),
        max_base=max(1, int(args.max_base)),
        top_k=max(1, int(args.top_k)),
        edge_limit=max(1, int(args.edge_limit)),
    )
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
