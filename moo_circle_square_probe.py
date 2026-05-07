from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from moo_circle_probe import (
    exact_sqrt_fraction,
    fraction_key,
    fraction_record,
    quadratic_form,
)
from moo_graph_invariants import family_graph_invariants, node_payload, node_status
from moo_research_utils import (
    connect_readonly,
    emit_json,
    nonnegative_float,
    positive_int,
    report_metadata,
    require_strict_alignment,
    strict_alignment_payload,
)
from rational_baselines import format_key, normalize_key


Key = Tuple[int, int]


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


def _claim_boundary(claim_status: str) -> Dict[str, object]:
    return {
        "evidence_layer": "strict",
        "claim_status": claim_status,
        "object_language": "circle_square_alignment",
        "allowed_claim_language": [
            "This report exposes rational quadratic-shell candidates and their associated square components in a strict MoO graph corpus.",
            "A circle-square alignment candidate means shell and square component nodes are present with named graph-invariant timing and witness fields.",
            "Literal self-product witnesses are audited under the strict operand rule; rational square nodes may be present without rational self-product edges.",
        ],
        "disallowed_claim_language": [
            "Do not claim MoO squares the circle from this report.",
            "Do not claim MoO defines the Euclidean circle.",
            "Do not claim MoO constructs pi.",
            "Do not treat absence of rational self-product witnesses as a failure; speculative rational nodes are not operands in strict-stage MoO.",
        ],
    }


def _load_nodes(conn: sqlite3.Connection) -> Dict[Key, sqlite3.Row]:
    return {
        (int(row["p"]), int(row["q"])): row
        for row in conn.execute("SELECT * FROM nodes").fetchall()
    }


def _node_fraction(row: sqlite3.Row) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _within_caps(
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


def _candidate_rows(
    nodes: Dict[Key, sqlite3.Row],
    *,
    max_denominator: int,
    max_abs_value: Optional[float],
    include_negative: bool,
    include_degenerate: bool,
) -> List[sqlite3.Row]:
    rows = []
    for row in nodes.values():
        value = _node_fraction(row)
        if not include_negative and value < 0:
            continue
        if not include_degenerate and value == 0:
            continue
        if _within_caps(
            value,
            max_denominator=max_denominator,
            max_abs_value=max_abs_value,
        ):
            rows.append(row)
    rows.sort(key=lambda row: (_node_fraction(row), int(row["q"]), abs(int(row["p"]))))
    return rows


def _stage_payload(rows: Sequence[Optional[sqlite3.Row]]) -> Dict[str, object]:
    present = [row for row in rows if row is not None]
    stages = [int(row["first_stage"]) for row in present]
    missing_count = len(rows) - len(present)
    return {
        "present_count": len(present),
        "missing_count": missing_count,
        "min_first_stage": min(stages) if stages else None,
        "max_first_stage": max(stages) if stages else None,
        "stage_spread": max(stages) - min(stages) if stages and missing_count == 0 else None,
    }


def strict_self_product_witness(
    conn: sqlite3.Connection,
    source_row: Optional[sqlite3.Row],
    square_row: Optional[sqlite3.Row],
) -> Dict[str, object]:
    if source_row is None:
        return {"present": False, "reason": "source_node_absent"}
    if square_row is None:
        return {"present": False, "reason": "square_node_absent"}
    row = conn.execute(
        """
        SELECT edge_id, stage, op
        FROM edges
        WHERE op = '*'
          AND left_node_id = ?
          AND right_node_id = ?
          AND result_node_id = ?
        ORDER BY stage, edge_id
        LIMIT 1
        """,
        (
            int(source_row["node_id"]),
            int(source_row["node_id"]),
            int(square_row["node_id"]),
        ),
    ).fetchone()
    if row is None:
        source_is_confirmed_positive_integer = (
            int(source_row["q"]) == 1
            and int(source_row["p"]) >= 1
            and source_row["confirmed_stage"] is not None
        )
        reason = "no_retained_strict_self_product_edge_recorded"
        note = (
            "for confirmed integer sources, the edge may be absent because the square "
            "fell outside output retention bounds at the first possible strict stage"
        )
        if not source_is_confirmed_positive_integer:
            reason = "source_is_not_a_confirmed_positive_integer_operand"
            note = "speculative rational nodes are not operands in strict-stage MoO"
        return {
            "present": False,
            "reason": reason,
            "strict_operand_note": note,
        }
    return {
        "present": True,
        "edge_id": int(row["edge_id"]),
        "stage": int(row["stage"]),
        "op": str(row["op"]),
    }


def _component_payload(
    conn: sqlite3.Connection,
    label: str,
    value: Fraction,
    nodes: Dict[Key, sqlite3.Row],
) -> Dict[str, object]:
    source_key = fraction_key(value)
    square = value * value
    square_key = fraction_key(square)
    source_row = nodes.get(source_key)
    square_row = nodes.get(square_key)
    return {
        "label": label,
        "source": {
            "value": fraction_record(value),
            "present": source_row is not None,
            "node": node_payload(source_row) if source_row is not None else None,
        },
        "square": {
            "value": fraction_record(square),
            "present": square_row is not None,
            "node": node_payload(square_row) if square_row is not None else None,
        },
        "strict_self_product_witness": strict_self_product_witness(
            conn,
            source_row,
            square_row,
        ),
    }


def _phase_payload(
    shell_rows: Sequence[Optional[sqlite3.Row]],
    square_rows: Sequence[Optional[sqlite3.Row]],
) -> Dict[str, object]:
    shell = _stage_payload(shell_rows)
    squares = _stage_payload(square_rows)
    combined = _stage_payload([*shell_rows, *square_rows])
    phase_delta = None
    if shell["max_first_stage"] is not None and squares["max_first_stage"] is not None:
        phase_delta = int(squares["max_first_stage"]) - int(shell["max_first_stage"])
    return {
        "shell": shell,
        "square_components": squares,
        "combined": combined,
        "phase_delta": phase_delta,
    }


def circle_square_candidate(
    conn: sqlite3.Connection,
    x: Fraction,
    y: Fraction,
    r: Fraction,
    nodes: Dict[Key, sqlite3.Row],
) -> Dict[str, object]:
    x_key = fraction_key(x)
    y_key = fraction_key(y)
    r_key = fraction_key(r)
    x2_key = fraction_key(x * x)
    y2_key = fraction_key(y * y)
    r2_key = fraction_key(r * r)
    shell_rows = [nodes.get(x_key), nodes.get(y_key), nodes.get(r_key)]
    square_rows = [nodes.get(x2_key), nodes.get(y2_key), nodes.get(r2_key)]
    components = [
        _component_payload(conn, "x", x, nodes),
        _component_payload(conn, "y", y, nodes),
        _component_payload(conn, "r", r, nodes),
    ]
    self_product_count = sum(
        1
        for component in components
        if bool(component["strict_self_product_witness"]["present"])
    )
    family_keys = [
        ("x", x_key),
        ("y", y_key),
        ("r", r_key),
        ("x_square", x2_key),
        ("y_square", y2_key),
        ("r_square", r2_key),
    ]
    return {
        "shell": {
            "x": fraction_record(x),
            "y": fraction_record(y),
            "r": fraction_record(r),
            "quadratic_check": {
                "form": "x*x + y*y",
                "value": fraction_record(quadratic_form(x, y)),
                "target": fraction_record(r * r),
                "exact": quadratic_form(x, y) == r * r,
            },
        },
        "components": components,
        "completion": {
            "shell_components_present": all(row is not None for row in shell_rows),
            "square_components_present": all(row is not None for row in square_rows),
            "complete_family": all(row is not None for row in [*shell_rows, *square_rows]),
            "strict_self_product_witness_count": int(self_product_count),
            "all_square_components_have_strict_self_product_witness": self_product_count == 3,
        },
        "phase_alignment": _phase_payload(shell_rows, square_rows),
        "graph_invariant_summary": family_graph_invariants(
            conn,
            family_keys,
            include_node_invariants=False,
        ),
    }


def circle_square_alignment_summary(
    conn: sqlite3.Connection,
    *,
    max_denominator: int,
    max_abs_value: Optional[float],
    limit: int,
    include_negative: bool,
    include_degenerate: bool,
    require_complete_family: bool,
    max_pairs: int,
    full_scan: bool,
) -> Dict[str, object]:
    nodes = _load_nodes(conn)
    rows = _candidate_rows(
        nodes,
        max_denominator=max_denominator,
        max_abs_value=max_abs_value,
        include_negative=include_negative,
        include_degenerate=include_degenerate,
    )
    estimated_pair_count = len(rows) * (len(rows) + 1) // 2
    if not full_scan and estimated_pair_count > int(max_pairs):
        raise SystemExit(
            "Refusing circle-square scan over "
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
            if not _within_caps(
                r,
                max_denominator=max_denominator,
                max_abs_value=max_abs_value,
            ):
                continue
            candidate = circle_square_candidate(conn, x, y, r, nodes)
            if require_complete_family and not bool(candidate["completion"]["complete_family"]):
                continue
            candidates.append(candidate)

    complete = [candidate for candidate in candidates if bool(candidate["completion"]["complete_family"])]
    with_any_self_product = [
        candidate
        for candidate in candidates
        if int(candidate["completion"]["strict_self_product_witness_count"]) > 0
    ]
    with_all_self_product = [
        candidate
        for candidate in candidates
        if bool(candidate["completion"]["all_square_components_have_strict_self_product_witness"])
    ]
    low_spread = sorted(
        complete,
        key=lambda candidate: (
            int(candidate["phase_alignment"]["combined"]["stage_spread"])
            if candidate["phase_alignment"]["combined"]["stage_spread"] is not None
            else 10**12,
            int(candidate["phase_alignment"]["combined"]["max_first_stage"])
            if candidate["phase_alignment"]["combined"]["max_first_stage"] is not None
            else 10**12,
            -int(candidate["completion"]["strict_self_product_witness_count"]),
            int(candidate["graph_invariant_summary"]["baseline_envelope"]["max_component_height"])
            if candidate["graph_invariant_summary"]["baseline_envelope"]["max_component_height"] is not None
            else 10**12,
        ),
    )
    high_witness = sorted(
        complete,
        key=lambda candidate: (
            -int(candidate["graph_invariant_summary"]["total_incoming_derivation_events"]),
            int(candidate["phase_alignment"]["combined"]["stage_spread"])
            if candidate["phase_alignment"]["combined"]["stage_spread"] is not None
            else 10**12,
        ),
    )
    high_self_product = sorted(
        with_any_self_product,
        key=lambda candidate: (
            -int(candidate["completion"]["strict_self_product_witness_count"]),
            int(candidate["phase_alignment"]["combined"]["stage_spread"])
            if candidate["phase_alignment"]["combined"]["stage_spread"] is not None
            else 10**12,
            int(candidate["phase_alignment"]["combined"]["max_first_stage"])
            if candidate["phase_alignment"]["combined"]["max_first_stage"] is not None
            else 10**12,
        ),
    )
    return {
        "report_type": "circle_square_alignment_summary",
        "corpus": _corpus_payload(conn),
        "claim_boundary": _claim_boundary("lead"),
        "parameters": {
            "max_denominator": int(max_denominator),
            "max_abs_value": float(max_abs_value) if max_abs_value is not None else None,
            "include_negative": bool(include_negative),
            "include_degenerate": bool(include_degenerate),
            "require_complete_family": bool(require_complete_family),
            "eligible_node_count": len(rows),
            "estimated_pair_count": int(estimated_pair_count),
            "max_pairs": int(max_pairs),
            "full_scan": bool(full_scan),
        },
        "summary": {
            "candidate_count": len(candidates),
            "complete_family_count": len(complete),
            "with_any_strict_self_product_witness_count": len(with_any_self_product),
            "with_all_strict_self_product_witnesses_count": len(with_all_self_product),
            "nondegenerate": not include_degenerate,
        },
        "top_low_stage_spread_complete_families": low_spread[:limit],
        "top_high_witness_complete_families": high_witness[:limit],
        "top_strict_self_product_families": high_self_product[:limit],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only circle-square branch alignment probe over a strict MoO graph corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--max-denominator", type=positive_int, default=20)
    parser.add_argument("--max-abs-value", type=nonnegative_float, default=5.0)
    parser.add_argument("--limit", type=positive_int, default=12)
    parser.add_argument("--include-negative", action="store_true")
    parser.add_argument("--include-degenerate", action="store_true")
    parser.add_argument("--require-complete-family", action="store_true")
    parser.add_argument(
        "--max-pairs",
        type=positive_int,
        default=2_000_000,
        help="Safety cap for pair scans unless --full-scan is passed.",
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Allow scans above --max-pairs.",
    )
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
        payload = circle_square_alignment_summary(
            conn,
            max_denominator=int(args.max_denominator),
            max_abs_value=args.max_abs_value,
            limit=int(args.limit),
            include_negative=bool(args.include_negative),
            include_degenerate=bool(args.include_degenerate),
            require_complete_family=bool(args.require_complete_family),
            max_pairs=int(args.max_pairs),
            full_scan=bool(args.full_scan),
        )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_circle_square_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
