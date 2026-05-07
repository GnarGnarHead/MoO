from __future__ import annotations

import argparse
import json
import math
import sqlite3
from collections import Counter
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo_graph_invariants import family_graph_invariants
from moo_research_utils import (
    connect_readonly,
    emit_json,
    nonnegative_float,
    positive_int,
    report_metadata,
    require_strict_alignment,
    strict_alignment_payload,
)
from rational_baselines import baseline_features, format_key, normalize_key, parse_key


Key = Tuple[int, int]


def unit_shell_point(t: Fraction) -> Tuple[Fraction, Fraction]:
    denominator = 1 + t * t
    return (1 - t * t) / denominator, (2 * t) / denominator


def quadratic_form(x: Fraction, y: Fraction) -> Fraction:
    return x * x + y * y


def exact_sqrt_fraction(value: Fraction) -> Optional[Fraction]:
    if value < 0:
        return None
    numerator_root = math.isqrt(value.numerator)
    denominator_root = math.isqrt(value.denominator)
    if numerator_root * numerator_root != value.numerator:
        return None
    if denominator_root * denominator_root != value.denominator:
        return None
    return Fraction(numerator_root, denominator_root)


def fraction_key(value: Fraction) -> Key:
    return normalize_key(int(value.numerator), int(value.denominator))


def fraction_record(value: Fraction) -> Dict[str, object]:
    key = fraction_key(value)
    return {
        "frac": format_key(key),
        "p": int(key[0]),
        "q": int(key[1]),
        "value_float": float(value),
    }


def _connect(path: Path) -> sqlite3.Connection:
    return connect_readonly(path)


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return str(row["value"])


def _json_meta(conn: sqlite3.Connection, key: str) -> Optional[object]:
    value = _meta_value(conn, key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _corpus_payload(conn: sqlite3.Connection) -> Dict[str, object]:
    latest_stage = conn.execute(
        """
        SELECT *
        FROM stages
        ORDER BY stage DESC
        LIMIT 1
        """
    ).fetchone()
    node_count = conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()
    edge_count = conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()
    return {
        "schema_version": _meta_value(conn, "schema_version"),
        "config": _json_meta(conn, "config_json"),
        "latest_stage": dict(latest_stage) if latest_stage is not None else None,
        "nodes": int(node_count["n"]),
        "edges": int(edge_count["n"]),
        "alignment": strict_alignment_payload(conn),
    }


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
    key = int(row["p"]), int(row["q"])
    return {
        "node_id": int(row["node_id"]),
        "frac": format_key(key),
        "p": int(key[0]),
        "q": int(key[1]),
        "kind": str(row["kind"]),
        "status": _node_status(row),
        "first_stage": int(row["first_stage"]),
        "confirmed_stage": int(row["confirmed_stage"])
        if row["confirmed_stage"] is not None
        else None,
    }


def _incoming_edge_examples(
    conn: sqlite3.Connection,
    node_id: int,
    *,
    limit: int,
) -> List[Dict[str, object]]:
    rows = conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.label AS left_label,
          r.label AS right_label
        FROM edges e
        LEFT JOIN nodes l ON l.node_id = e.left_node_id
        LEFT JOIN nodes r ON r.node_id = e.right_node_id
        WHERE e.result_node_id = ?
        ORDER BY e.stage, e.edge_id
        LIMIT ?
        """,
        (int(node_id), int(limit)),
    ).fetchall()
    return [
        {
            "edge_id": int(row["edge_id"]),
            "stage": int(row["stage"]),
            "op": str(row["op"]),
            "left": row["left_label"],
            "right": row["right_label"],
        }
        for row in rows
    ]


def _stats_payload(row: Optional[sqlite3.Row]) -> Dict[str, int]:
    if row is None:
        return {"derivation_events": 0, "+": 0, "-": 0, "*": 0, "/": 0}
    return {
        "derivation_events": int(row["derivation_events"]),
        "+": int(row["plus_count"]),
        "-": int(row["minus_count"]),
        "*": int(row["multiply_count"]),
        "/": int(row["divide_count"]),
    }


def _load_node_maps(conn: sqlite3.Connection) -> Tuple[Dict[Key, sqlite3.Row], Dict[int, Dict[str, int]]]:
    nodes = {
        (int(row["p"]), int(row["q"])): row
        for row in conn.execute("SELECT * FROM nodes").fetchall()
    }
    stats = {
        int(row["node_id"]): _stats_payload(row)
        for row in conn.execute("SELECT * FROM node_stats").fetchall()
    }
    return nodes, stats


def _node_with_stats(
    key: Key,
    nodes: Dict[Key, sqlite3.Row],
    stats: Dict[int, Dict[str, int]],
    *,
    conn: Optional[sqlite3.Connection] = None,
    edge_limit: int = 3,
) -> Dict[str, object]:
    key = normalize_key(*key)
    row = nodes.get(key)
    payload: Dict[str, object] = {
        "present": row is not None,
        "key": {"p": int(key[0]), "q": int(key[1]), "frac": format_key(key)},
        "baseline": baseline_features(key),
    }
    if row is not None:
        node_id = int(row["node_id"])
        payload["node"] = _node_payload(row)
        payload["stats"] = stats.get(node_id, _stats_payload(None))
        if conn is not None:
            payload["incoming_edge_examples"] = _incoming_edge_examples(
                conn,
                node_id,
                limit=edge_limit,
            )
    return payload


def _claim_boundary(claim_status: str) -> Dict[str, object]:
    return {
        "evidence_layer": "strict",
        "claim_status": claim_status,
        "object_language": "unit_quadratic_shell",
        "allowed_claim_language": [
            "This report exposes exact rational unit-quadratic-shell candidates over a strict MoO graph corpus.",
            "A complete candidate means the relevant rational component nodes are present in this corpus.",
            "The parametrization is an external probe until MoO-native orbit and refinement criteria are defined.",
        ],
        "disallowed_claim_language": [
            "Do not claim MoO defines the circle from x*x + y*y = r*r alone.",
            "Do not claim MoO constructs pi from this report.",
            "Do not treat the unit-shell parametrization as an internal MoO derivation.",
        ],
    }


def _presence(node: Dict[str, object]) -> bool:
    return bool(node["present"])


def _max_stage(nodes: Iterable[Dict[str, object]]) -> Optional[int]:
    stages: List[int] = []
    for node in nodes:
        if not _presence(node):
            continue
        payload = node.get("node")
        if isinstance(payload, dict):
            stages.append(int(payload["first_stage"]))
    if not stages:
        return None
    return max(stages)


def _witness_total(nodes: Iterable[Dict[str, object]]) -> int:
    total = 0
    for node in nodes:
        if not _presence(node):
            continue
        stats = node.get("stats")
        if isinstance(stats, dict):
            total += int(stats["derivation_events"])
    return total


def _light_component_metrics(
    keys: Iterable[Key],
    nodes: Dict[Key, sqlite3.Row],
    stats: Dict[int, Dict[str, int]],
) -> Dict[str, object]:
    key_list = [normalize_key(*key) for key in keys]
    stages: List[int] = []
    confirmation_lags: List[int] = []
    denominator_heights: List[int] = []
    component_heights: List[int] = []
    op_counts: Counter[str] = Counter()
    witnesses = 0
    present = 0
    for normalized in key_list:
        denominator_heights.append(int(normalized[1]))
        component_heights.append(max(abs(int(normalized[0])), int(normalized[1])))
        row = nodes.get(normalized)
        if row is None:
            continue
        present += 1
        stages.append(int(row["first_stage"]))
        if row["confirmed_stage"] is not None:
            confirmation_lags.append(int(row["confirmed_stage"]) - int(row["first_stage"]))
        node_stats = stats.get(int(row["node_id"]), _stats_payload(None))
        witnesses += int(node_stats["derivation_events"])
        for op in ("+", "-", "*", "/"):
            op_counts[op] += int(node_stats.get(op, 0))
    return {
        "max_component_first_stage": max(stages) if stages else None,
        "component_derivation_events": witnesses,
        "graph_invariant_summary": {
            "vocabulary_version": "graph_invariants.v1",
            "component_count": len(key_list),
            "present_component_count": int(present),
            "missing_component_count": len(key_list) - present,
            "max_first_stage": max(stages) if stages else None,
            "max_confirmation_lag": max(confirmation_lags) if confirmation_lags else None,
            "total_incoming_derivation_events": int(witnesses),
            "aggregate_operation_signature": {
                "incoming_derivation_events": int(witnesses),
                "counts": {op: int(op_counts[op]) for op in sorted(op_counts) if int(op_counts[op])},
            },
            "baseline_envelope": {
                "max_denominator_height": max(denominator_heights) if denominator_heights else None,
                "max_component_height": max(component_heights) if component_heights else None,
            },
        },
    }


def _sign_variants(x: Fraction, y: Fraction) -> List[Tuple[Fraction, Fraction]]:
    variants = {(-x, -y), (-x, y), (x, -y), (x, y)}
    return sorted(variants, key=lambda pair: (pair[0], pair[1]))


def _symmetry_payload(
    x: Fraction,
    y: Fraction,
    nodes: Dict[Key, sqlite3.Row],
) -> Dict[str, object]:
    variants = []
    for sx, sy in _sign_variants(x, y):
        x_key = fraction_key(sx)
        y_key = fraction_key(sy)
        variants.append(
            {
                "x": fraction_record(sx),
                "y": fraction_record(sy),
                "x_node_present": x_key in nodes,
                "y_node_present": y_key in nodes,
                "complete": x_key in nodes and y_key in nodes,
            }
        )
    return {
        "variant_count": len(variants),
        "complete_variant_count": sum(1 for item in variants if item["complete"]),
        "all_variants_complete": all(bool(item["complete"]) for item in variants),
        "variants": variants,
    }


def unit_shell_dossier_for_t(
    conn: sqlite3.Connection,
    t_key: Key,
) -> Dict[str, object]:
    nodes, stats = _load_node_maps(conn)
    t_key = normalize_key(*t_key)
    t = Fraction(*t_key)
    x, y = unit_shell_point(t)
    q_value = quadratic_form(x, y)

    t_node = _node_with_stats(t_key, nodes, stats, conn=conn)
    x_node = _node_with_stats(fraction_key(x), nodes, stats, conn=conn)
    y_node = _node_with_stats(fraction_key(y), nodes, stats, conn=conn)
    components = [t_node, x_node, y_node]
    component_keys = [
        ("t", t_key),
        ("x", fraction_key(x)),
        ("y", fraction_key(y)),
    ]
    return {
        "report_type": "unit_shell_dossier",
        "corpus": _corpus_payload(conn),
        "claim_boundary": _claim_boundary("observation"),
        "relation_status": "external_parametrized_candidate_relation",
        "parameter": {
            "formula_role": "t",
            "value": fraction_record(t),
            "node": t_node,
        },
        "point": {
            "x": {"formula": "(1 - t*t) / (1 + t*t)", "value": fraction_record(x), "node": x_node},
            "y": {"formula": "(2*t) / (1 + t*t)", "value": fraction_record(y), "node": y_node},
        },
        "quadratic_check": {
            "form": "x*x + y*y",
            "value": fraction_record(q_value),
            "target": fraction_record(Fraction(1, 1)),
            "exact": q_value == 1,
        },
        "completion": {
            "t_node_present": _presence(t_node),
            "x_node_present": _presence(x_node),
            "y_node_present": _presence(y_node),
            "complete_point": _presence(t_node) and _presence(x_node) and _presence(y_node),
            "max_component_first_stage": _max_stage(components),
            "component_derivation_events": _witness_total(components),
        },
        "graph_invariant_summary": family_graph_invariants(conn, component_keys),
        "symmetry_coverage": _symmetry_payload(x, y, nodes),
    }


def _node_fraction(row: sqlite3.Row) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _node_within_caps(
    value: Fraction,
    *,
    max_denominator: int,
    max_abs_value: Optional[float],
) -> bool:
    if value.denominator > int(max_denominator):
        return False
    if max_abs_value is not None and abs(float(value)) > float(max_abs_value):
        return False
    return True


def _candidate_t_rows(
    nodes: Dict[Key, sqlite3.Row],
    *,
    max_denominator: int,
    max_abs_value: Optional[float],
) -> List[sqlite3.Row]:
    rows = []
    for row in nodes.values():
        value = _node_fraction(row)
        if _node_within_caps(
            value,
            max_denominator=max_denominator,
            max_abs_value=max_abs_value,
        ):
            rows.append(row)
    rows.sort(key=lambda row: (int(row["first_stage"]), int(row["q"]), abs(int(row["p"])), int(row["p"])))
    return rows


def _unit_shell_candidate(
    row: sqlite3.Row,
    nodes: Dict[Key, sqlite3.Row],
    stats: Dict[int, Dict[str, int]],
) -> Dict[str, object]:
    t = _node_fraction(row)
    x, y = unit_shell_point(t)
    t_key = fraction_key(t)
    x_key = fraction_key(x)
    y_key = fraction_key(y)
    metrics = _light_component_metrics((t_key, x_key, y_key), nodes, stats)
    symmetry = _symmetry_payload(x, y, nodes)
    return {
        "t": fraction_record(t),
        "t_node_status": _node_status(row),
        "x": fraction_record(x),
        "y": fraction_record(y),
        "complete_point": t_key in nodes and x_key in nodes and y_key in nodes,
        "x_node_present": x_key in nodes,
        "y_node_present": y_key in nodes,
        "max_component_first_stage": metrics["max_component_first_stage"],
        "component_derivation_events": metrics["component_derivation_events"],
        "graph_invariant_summary": metrics["graph_invariant_summary"],
        "symmetry_variant_count": symmetry["variant_count"],
        "symmetry_complete_variants": symmetry["complete_variant_count"],
    }


def unit_shell_summary(
    conn: sqlite3.Connection,
    *,
    max_denominator: int,
    max_abs_value: Optional[float],
    limit: int,
    only_complete: bool,
) -> Dict[str, object]:
    nodes, stats = _load_node_maps(conn)
    candidates = [
        _unit_shell_candidate(row, nodes, stats)
        for row in _candidate_t_rows(
            nodes,
            max_denominator=max_denominator,
            max_abs_value=max_abs_value,
        )
    ]
    if only_complete:
        candidates = [candidate for candidate in candidates if candidate["complete_point"]]

    complete = [candidate for candidate in candidates if candidate["complete_point"]]
    missing_x = sum(1 for candidate in candidates if not candidate["x_node_present"])
    missing_y = sum(1 for candidate in candidates if not candidate["y_node_present"])
    parameter_status_distribution = Counter(str(candidate["t_node_status"]) for candidate in candidates)
    complete_parameter_status_distribution = Counter(
        str(candidate["t_node_status"]) for candidate in complete
    )
    stage_distribution = Counter(
        int(candidate["max_component_first_stage"])
        for candidate in complete
        if candidate["max_component_first_stage"] is not None
    )
    denominator_distribution = Counter(
        max(int(candidate["x"]["q"]), int(candidate["y"]["q"]))
        for candidate in complete
    )
    low_cost = sorted(
        complete,
        key=lambda candidate: (
            int(candidate["max_component_first_stage"])
            if candidate["max_component_first_stage"] is not None
            else 10**12,
            max(int(candidate["x"]["q"]), int(candidate["y"]["q"])),
            abs(float(candidate["t"]["value_float"])),
        ),
    )
    high_witness = sorted(
        complete,
        key=lambda candidate: (
            -int(candidate["component_derivation_events"]),
            int(candidate["max_component_first_stage"])
            if candidate["max_component_first_stage"] is not None
            else 10**12,
        ),
    )
    return {
        "report_type": "unit_shell_summary",
        "corpus": _corpus_payload(conn),
        "claim_boundary": _claim_boundary("lead"),
        "parameters": {
            "max_denominator": int(max_denominator),
            "max_abs_value": float(max_abs_value) if max_abs_value is not None else None,
            "only_complete": bool(only_complete),
        },
        "summary": {
            "candidate_count": len(candidates),
            "complete_point_count": len(complete),
            "missing_x_count": missing_x,
            "missing_y_count": missing_y,
            "all_symmetry_variants_complete_count": sum(
                1
                for candidate in complete
                if int(candidate["symmetry_complete_variants"])
                == int(candidate["symmetry_variant_count"])
            ),
            "parameter_status_distribution": {
                status: int(parameter_status_distribution[status])
                for status in sorted(parameter_status_distribution)
            },
            "complete_parameter_status_distribution": {
                status: int(complete_parameter_status_distribution[status])
                for status in sorted(complete_parameter_status_distribution)
            },
            "stage_distribution": {
                str(stage): int(stage_distribution[stage])
                for stage in sorted(stage_distribution)
            },
            "denominator_distribution": {
                str(denominator): int(denominator_distribution[denominator])
                for denominator in sorted(denominator_distribution)
            },
        },
        "top_low_stage_complete_points": low_cost[:limit],
        "top_high_witness_complete_points": high_witness[:limit],
    }


def pythagorean_shell_summary(
    conn: sqlite3.Connection,
    *,
    max_denominator: int,
    max_abs_value: Optional[float],
    limit: int,
    include_degenerate: bool,
    max_pairs: int,
    full_scan: bool,
) -> Dict[str, object]:
    nodes, stats = _load_node_maps(conn)
    rows = []
    for row in nodes.values():
        value = _node_fraction(row)
        if value < 0:
            continue
        if not include_degenerate and value == 0:
            continue
        if _node_within_caps(
            value,
            max_denominator=max_denominator,
            max_abs_value=max_abs_value,
        ):
            rows.append(row)
    rows.sort(key=lambda row: (int(row["q"]), int(row["p"])))
    estimated_pair_count = len(rows) * (len(rows) + 1) // 2
    if not full_scan and estimated_pair_count > int(max_pairs):
        raise SystemExit(
            "Refusing pythagorean scan over "
            f"{estimated_pair_count} candidate pairs; raise --max-pairs or pass --full-scan."
        )

    candidates = []
    for i, left in enumerate(rows):
        x = _node_fraction(left)
        for right in rows[i:]:
            y = _node_fraction(right)
            if not include_degenerate and (x == 0 or y == 0):
                continue
            r = exact_sqrt_fraction(quadratic_form(x, y))
            if r is None:
                continue
            if not _node_within_caps(
                r,
                max_denominator=max_denominator,
                max_abs_value=max_abs_value,
            ):
                continue
            r_key = fraction_key(r)
            x_key = fraction_key(x)
            y_key = fraction_key(y)
            metrics = _light_component_metrics((x_key, y_key, r_key), nodes, stats)
            candidates.append(
                {
                    "x": fraction_record(x),
                    "y": fraction_record(y),
                    "r": fraction_record(r),
                    "r_node_present": r_key in nodes,
                    "complete_shell": r_key in nodes,
                    "max_component_first_stage": metrics["max_component_first_stage"],
                    "component_derivation_events": metrics["component_derivation_events"],
                    "graph_invariant_summary": metrics["graph_invariant_summary"],
                    "quadratic_check": {
                        "form": "x*x + y*y",
                        "value": fraction_record(quadratic_form(x, y)),
                        "target": fraction_record(r * r),
                        "exact": quadratic_form(x, y) == r * r,
                    },
                }
            )

    complete = [candidate for candidate in candidates if candidate["complete_shell"]]
    complete.sort(
        key=lambda candidate: (
            int(candidate["max_component_first_stage"])
            if candidate["max_component_first_stage"] is not None
            else 10**12,
            int(candidate["r"]["q"]),
            int(candidate["r"]["p"]),
            int(candidate["x"]["q"]) + int(candidate["y"]["q"]),
        )
    )
    high_witness = sorted(
        complete,
        key=lambda candidate: (
            -int(candidate["component_derivation_events"]),
            int(candidate["max_component_first_stage"])
            if candidate["max_component_first_stage"] is not None
            else 10**12,
        ),
    )
    radius_distribution = Counter(str(candidate["r"]["frac"]) for candidate in complete)
    top_radii = sorted(
        radius_distribution.items(),
        key=lambda item: (-int(item[1]), parse_key(item[0])),
    )[:limit]
    return {
        "report_type": "pythagorean_shell_summary",
        "corpus": _corpus_payload(conn),
        "claim_boundary": _claim_boundary("lead"),
        "parameters": {
            "max_denominator": int(max_denominator),
            "max_abs_value": float(max_abs_value) if max_abs_value is not None else None,
            "include_degenerate": bool(include_degenerate),
            "eligible_node_count": len(rows),
            "estimated_pair_count": estimated_pair_count,
            "max_pairs": int(max_pairs),
            "full_scan": bool(full_scan),
        },
        "summary": {
            "candidate_count": len(candidates),
            "complete_shell_count": len(complete),
            "missing_radius_node_count": len(candidates) - len(complete),
            "distinct_radius_count": len(radius_distribution),
            "top_radius_distribution": [
                {"radius": radius, "count": int(count)}
                for radius, count in top_radii
            ],
        },
        "top_low_stage_complete_shells": complete[:limit],
        "top_high_witness_complete_shells": high_witness[:limit],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only unit-quadratic-shell probes over a strict MoO graph corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--unit-circle",
        action="store_true",
        help="Report exact rational unit quadratic-shell candidates generated from t.",
    )
    mode.add_argument(
        "--pythagorean",
        action="store_true",
        help="Scan existing nonnegative rational node pairs satisfying x*x + y*y = r*r.",
    )
    parser.add_argument("--node", help="With --unit-circle, build a dossier for this t value.")
    parser.add_argument("--max-denominator", type=positive_int, default=40)
    parser.add_argument("--max-abs-value", type=nonnegative_float, default=4.0)
    parser.add_argument("--limit", type=positive_int, default=12)
    parser.add_argument(
        "--max-pairs",
        type=positive_int,
        default=2_000_000,
        help="Safety cap for --pythagorean pair scans unless --full-scan is passed.",
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Allow --pythagorean scans above --max-pairs.",
    )
    parser.add_argument("--only-complete", action="store_true")
    parser.add_argument("--include-degenerate", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--write",
        type=Path,
        help="Also write the JSON report to this path. Existing files are never overwritten.",
    )
    parser.add_argument(
        "--experiment-id",
        help="Stable research experiment ID to include in the report payload.",
    )
    parser.add_argument(
        "--with-checksums",
        action="store_true",
        help="Include SHA-256 hashes for the corpus DB and report tool in report metadata.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    with closing(_connect(Path(args.db))) as conn:
        require_strict_alignment(conn)
        if args.unit_circle and args.node:
            try:
                node_key = parse_key(str(args.node))
            except (ValueError, ZeroDivisionError) as exc:
                parser.error(f"invalid --node value: {exc}")
            payload = unit_shell_dossier_for_t(conn, node_key)
        elif args.unit_circle:
            payload = unit_shell_summary(
                conn,
                max_denominator=int(args.max_denominator),
                max_abs_value=args.max_abs_value,
                limit=int(args.limit),
                only_complete=bool(args.only_complete),
            )
        else:
            if args.node:
                parser.error("--node is only supported with --unit-circle.")
            payload = pythagorean_shell_summary(
                conn,
                max_denominator=int(args.max_denominator),
                max_abs_value=args.max_abs_value,
                limit=int(args.limit),
                include_degenerate=bool(args.include_degenerate),
                max_pairs=int(args.max_pairs),
                full_scan=bool(args.full_scan),
            )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_circle_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
