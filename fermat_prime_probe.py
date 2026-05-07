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


def _parse_primes(raw: str) -> List[int]:
    primes: List[int] = []
    for part in str(raw).split(","):
        text = part.strip()
        if not text:
            continue
        value = int(text)
        if value <= 2 or not _is_prime(value):
            raise SystemExit(f"Expected odd prime exponents; got {value!r}.")
        primes.append(value)
    if not primes:
        raise SystemExit("At least one odd prime exponent is required.")
    return primes


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


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


def _inspect_integer_node(conn: sqlite3.Connection, value: int, *, edge_limit: int) -> Dict[str, object]:
    key = normalize_key(int(value), 1)
    node = conn.execute(
        "SELECT * FROM nodes WHERE p = ? AND q = ?",
        (int(key[0]), int(key[1])),
    ).fetchone()
    if node is None:
        return {
            "found": False,
            "frac": format_key(key),
            "p": int(key[0]),
            "q": int(key[1]),
        }

    node_id = int(node["node_id"])
    stats = conn.execute(
        "SELECT * FROM node_stats WHERE node_id = ?",
        (node_id,),
    ).fetchone()
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
        "p": int(key[0]),
        "q": int(key[1]),
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


def _node_id_for_int(conn: sqlite3.Connection, value: int) -> Optional[int]:
    key = normalize_key(int(value), 1)
    row = conn.execute(
        "SELECT node_id FROM nodes WHERE p = ? AND q = ?",
        (int(key[0]), int(key[1])),
    ).fetchone()
    if row is None:
        return None
    return int(row["node_id"])


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
    rows = [(left_id, right_id)]
    if allow_commuted and left_id != right_id:
        rows.append((right_id, left_id))
    for candidate_left, candidate_right in rows:
        found = conn.execute(
            """
            SELECT 1
            FROM edges
            WHERE left_node_id = ?
              AND right_node_id = ?
              AND result_node_id = ?
              AND op = ?
            LIMIT 1
            """,
            (candidate_left, candidate_right, result_id, op),
        ).fetchone()
        if found is not None:
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


def _floor_pth_root(value: int, exponent: int) -> int:
    if value < 0:
        raise ValueError("value must be non-negative")
    if value in {0, 1}:
        return value
    lo, hi = 1, 1
    while hi**exponent <= value:
        hi *= 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if mid**exponent <= value:
            lo = mid
        else:
            hi = mid
    return lo


def _nearest_c(sum_value: int, exponent: int) -> Tuple[int, int, int]:
    root = _floor_pth_root(sum_value, exponent)
    candidates = sorted({max(1, root), root + 1})
    best_c = candidates[0]
    best_power = best_c**exponent
    best_gap = best_power - sum_value
    for c in candidates[1:]:
        power = c**exponent
        gap = power - sum_value
        if abs(gap) < abs(best_gap):
            best_c, best_power, best_gap = c, power, gap
    return best_c, best_power, best_gap


def _branch_payload(
    conn: sqlite3.Connection,
    *,
    a: int,
    b: int,
    c: int,
    exponent: int,
    edge_limit: int,
) -> Dict[str, object]:
    a_power = a**exponent
    b_power = b**exponent
    left_sum = a_power + b_power
    c_power = c**exponent
    gap = c_power - left_sum
    branch = {
        "a_power": _inspect_integer_node(conn, a_power, edge_limit=edge_limit),
        "b_power": _inspect_integer_node(conn, b_power, edge_limit=edge_limit),
        "left_sum": _inspect_integer_node(conn, left_sum, edge_limit=edge_limit),
        "c_power": _inspect_integer_node(conn, c_power, edge_limit=edge_limit),
        "gap": _inspect_integer_node(conn, gap, edge_limit=edge_limit),
    }
    found_count = sum(1 for item in branch.values() if bool(item.get("found")))
    branch_edges = {
        "a_power_final_multiply": _power_final_edge_exists(
            conn,
            base=a,
            exponent=exponent,
        ),
        "b_power_final_multiply": _power_final_edge_exists(
            conn,
            base=b,
            exponent=exponent,
        ),
        "left_sum_from_powers": _edge_exists(
            conn,
            left_value=a_power,
            op="+",
            right_value=b_power,
            result_value=left_sum,
            allow_commuted=True,
        ),
        "c_power_final_multiply": _power_final_edge_exists(
            conn,
            base=c,
            exponent=exponent,
        ),
    }
    found_edge_count = sum(1 for value in branch_edges.values() if value)
    return {
        "a": int(a),
        "b": int(b),
        "c": int(c),
        "p": int(exponent),
        "values": {
            "a^p": int(a_power),
            "b^p": int(b_power),
            "a^p+b^p": int(left_sum),
            "c^p": int(c_power),
            "gap": int(gap),
            "abs_gap": abs(int(gap)),
            "relative_gap": float(abs(gap) / left_sum) if left_sum else None,
            "exact_collapse": gap == 0,
        },
        "graph_presence": {
            "found_branch_nodes": found_count,
            "total_branch_nodes": len(branch),
            "found_branch_edges": found_edge_count,
            "total_branch_edges": len(branch_edges),
            "all_main_branch_nodes_found": all(
                bool(branch[name].get("found"))
                for name in ["a_power", "b_power", "left_sum", "c_power"]
            ),
            "all_main_branch_edges_found": all(branch_edges.values()),
        },
        "branch_edges": branch_edges,
        "graph": branch,
    }


def fermat_prime_probe(
    *,
    db_path: Path,
    primes: Sequence[int],
    min_base: int,
    max_base: int,
    top_k: int,
    edge_limit: int,
) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    collisions: List[Dict[str, object]] = []
    with _connect(db_path) as conn:
        for exponent in primes:
            for a in range(min_base, max_base + 1):
                for b in range(a, max_base + 1):
                    left_sum = a**exponent + b**exponent
                    c, c_power, gap = _nearest_c(left_sum, exponent)
                    payload = _branch_payload(
                        conn,
                        a=a,
                        b=b,
                        c=c,
                        exponent=exponent,
                        edge_limit=edge_limit,
                    )
                    rows.append(payload)
                    if c_power == left_sum:
                        collisions.append(payload)

    near_misses = sorted(
        rows,
        key=lambda row: (
            row["values"]["abs_gap"],  # type: ignore[index]
            row["values"]["a^p+b^p"],  # type: ignore[index]
            row["p"],
            row["a"],
            row["b"],
        ),
    )[:top_k]
    graph_rich = sorted(
        rows,
        key=lambda row: (
            -int(row["graph_presence"]["found_branch_edges"]),  # type: ignore[index]
            -int(row["graph_presence"]["found_branch_nodes"]),  # type: ignore[index]
            row["values"]["abs_gap"],  # type: ignore[index]
            row["p"],
            row["a"],
            row["b"],
        ),
    )[:top_k]
    return {
        "framing": {
            "probe": "Fermat prime non-collapse probe",
            "equation": "a^p + b^p = c^p for odd prime p",
            "moo_rule": (
                "Exponentiation is not added as a MoO primitive here. "
                "Power targets are external repeated-multiplication probes; "
                "evidence comes from graph nodes and construction edges in the SQLite corpus."
            ),
            "inspection_rule": "A near miss is not evidence unless its branch nodes are present in the graph.",
        },
        "db": str(db_path),
        "config": {
            "primes": [int(p) for p in primes],
            "min_base": int(min_base),
            "max_base": int(max_base),
            "top_k": int(top_k),
            "edge_limit": int(edge_limit),
        },
        "collision_count": len(collisions),
        "collisions": collisions[:top_k],
        "nearest_non_collapses": near_misses,
        "graph_rich_branches": graph_rich,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe Fermat odd-prime non-collapse against a MoO graph corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--primes", default="3,5,7")
    parser.add_argument("--min-base", type=int, default=2)
    parser.add_argument("--max-base", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--edge-limit", type=int, default=4)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = fermat_prime_probe(
        db_path=Path(args.db),
        primes=_parse_primes(str(args.primes)),
        min_base=max(1, int(args.min_base)),
        max_base=max(1, int(args.max_base)),
        top_k=max(1, int(args.top_k)),
        edge_limit=max(1, int(args.edge_limit)),
    )
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
