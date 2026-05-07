from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from statistics import median
from typing import DefaultDict, Dict, List, Optional, Sequence, Tuple

from moo_research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
    strict_alignment_payload,
)
from moo_graph_invariants import node_graph_invariants
from rational_baselines import (
    baseline_features,
    continued_fraction,
    format_key,
    normalize_key,
    parse_key,
    stern_brocot_path,
)


Key = Tuple[int, int]
COMMUTATIVE_OPS = {"+", "*"}


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


def _node_for_key(conn: sqlite3.Connection, key: Key) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM nodes WHERE p = ? AND q = ?",
        (int(key[0]), int(key[1])),
    ).fetchone()


def _node_stats(conn: sqlite3.Connection, node_id: int) -> Dict[str, int]:
    row = conn.execute(
        "SELECT * FROM node_stats WHERE node_id = ?",
        (int(node_id),),
    ).fetchone()
    if row is None:
        return {"derivation_events": 0, "+": 0, "-": 0, "*": 0, "/": 0, "seed": 0}
    seed_count = conn.execute(
        "SELECT COUNT(*) AS n FROM edges WHERE result_node_id = ? AND op = 'seed'",
        (int(node_id),),
    ).fetchone()
    return {
        "derivation_events": int(row["derivation_events"]),
        "+": int(row["plus_count"]),
        "-": int(row["minus_count"]),
        "*": int(row["multiply_count"]),
        "/": int(row["divide_count"]),
        "seed": int(seed_count["n"]),
    }


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


def _operand_key(row: sqlite3.Row, prefix: str) -> Optional[Key]:
    p = row[f"{prefix}_p"]
    q = row[f"{prefix}_q"]
    if p is None or q is None:
        return None
    return int(p), int(q)


def _operand_payload(row: sqlite3.Row, prefix: str) -> Optional[Dict[str, object]]:
    node_id = row[f"{prefix}_node_id"]
    if node_id is None:
        return None
    key = int(row[f"{prefix}_p"]), int(row[f"{prefix}_q"])
    return {
        "node_id": int(node_id),
        "frac": format_key(key),
        "kind": str(row[f"{prefix}_kind"]),
        "first_stage": int(row[f"{prefix}_first_stage"]),
        "confirmed_stage": int(row[f"{prefix}_confirmed_stage"])
        if row[f"{prefix}_confirmed_stage"] is not None
        else None,
    }


def _incoming_rows(conn: sqlite3.Connection, node_id: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.node_id AS left_node_id,
          l.p AS left_p,
          l.q AS left_q,
          l.kind AS left_kind,
          l.first_stage AS left_first_stage,
          l.confirmed_stage AS left_confirmed_stage,
          r.node_id AS right_node_id,
          r.p AS right_p,
          r.q AS right_q,
          r.kind AS right_kind,
          r.first_stage AS right_first_stage,
          r.confirmed_stage AS right_confirmed_stage
        FROM edges e
        LEFT JOIN nodes l ON l.node_id = e.left_node_id
        LEFT JOIN nodes r ON r.node_id = e.right_node_id
        WHERE e.result_node_id = ?
        ORDER BY e.stage, e.edge_id
        """,
        (int(node_id),),
    ).fetchall()


def _outgoing_rows(conn: sqlite3.Connection, node_id: int, *, limit: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.label AS left_label,
          r.label AS right_label,
          out.node_id AS result_node_id,
          out.p AS result_p,
          out.q AS result_q,
          out.kind AS result_kind,
          out.first_stage AS result_first_stage,
          out.confirmed_stage AS result_confirmed_stage
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


def _outgoing_summary(conn: sqlite3.Connection, node_id: int, *, limit: int) -> Dict[str, object]:
    rows = conn.execute(
        """
        SELECT op, COUNT(*) AS n
        FROM edges
        WHERE left_node_id = ? OR right_node_id = ?
        GROUP BY op
        ORDER BY op
        """,
        (int(node_id), int(node_id)),
    ).fetchall()
    examples = []
    for row in _outgoing_rows(conn, node_id, limit=limit):
        result_key = int(row["result_p"]), int(row["result_q"])
        examples.append(
            {
                "edge_id": int(row["edge_id"]),
                "stage": int(row["stage"]),
                "op": str(row["op"]),
                "left": row["left_label"],
                "right": row["right_label"],
                "result": {
                    "node_id": int(row["result_node_id"]),
                    "frac": format_key(result_key),
                    "kind": str(row["result_kind"]),
                    "first_stage": int(row["result_first_stage"]),
                    "confirmed_stage": int(row["result_confirmed_stage"])
                    if row["result_confirmed_stage"] is not None
                    else None,
                },
            }
        )
    histogram = {str(row["op"]): int(row["n"]) for row in rows}
    return {
        "edge_occurrences": sum(histogram.values()),
        "operation_histogram": histogram,
        "examples": examples,
    }


def _algebraic_key(row: sqlite3.Row, *, normalize_commutative: bool) -> Tuple[object, ...]:
    op = str(row["op"])
    left = _operand_key(row, "left")
    right = _operand_key(row, "right")
    if normalize_commutative and op in COMMUTATIVE_OPS and left is not None and right is not None:
        ordered = tuple(sorted((left, right)))
        return op, ordered[0], ordered[1]
    return op, left, right


def _input_pair_key(row: sqlite3.Row, *, normalize_commutative: bool) -> Tuple[object, ...]:
    op = str(row["op"])
    left = _operand_key(row, "left")
    right = _operand_key(row, "right")
    if normalize_commutative and op in COMMUTATIVE_OPS and left is not None and right is not None:
        ordered = tuple(sorted((left, right)))
        return ordered[0], ordered[1]
    return left, right


def _incoming_example(row: sqlite3.Row) -> Dict[str, object]:
    return {
        "edge_id": int(row["edge_id"]),
        "stage": int(row["stage"]),
        "op": str(row["op"]),
        "left": _operand_payload(row, "left"),
        "right": _operand_payload(row, "right"),
    }


def _incoming_summary(rows: List[sqlite3.Row], *, limit: int) -> Dict[str, object]:
    op_counts = Counter(str(row["op"]) for row in rows)
    directed_witnesses = {_algebraic_key(row, normalize_commutative=False) for row in rows}
    normalized_witnesses = {_algebraic_key(row, normalize_commutative=True) for row in rows}
    directed_input_pairs = {_input_pair_key(row, normalize_commutative=False) for row in rows}
    normalized_input_pairs = {_input_pair_key(row, normalize_commutative=True) for row in rows}
    return {
        "edge_occurrences": len(rows),
        "operation_histogram": {op: int(op_counts[op]) for op in sorted(op_counts)},
        "witness_counts": {
            "unique_directed_algebraic": len(directed_witnesses),
            "unique_commutative_normalized_algebraic": len(normalized_witnesses),
            "distinct_directed_input_pairs": len(directed_input_pairs),
            "distinct_commutative_normalized_input_pairs": len(normalized_input_pairs),
        },
        "examples": [_incoming_example(row) for row in rows[:limit]],
    }


def _shared_input_neighborhood(
    conn: sqlite3.Connection,
    node_id: int,
    *,
    limit: int,
) -> Dict[str, object]:
    total = conn.execute(
        """
        WITH input_nodes(node_id) AS (
          SELECT left_node_id FROM edges
          WHERE result_node_id = ? AND left_node_id IS NOT NULL
          UNION
          SELECT right_node_id FROM edges
          WHERE result_node_id = ? AND right_node_id IS NOT NULL
        ),
        nearby(node_id) AS (
          SELECT e.result_node_id
          FROM edges e
          WHERE e.result_node_id != ?
            AND (
              e.left_node_id IN (SELECT node_id FROM input_nodes)
              OR e.right_node_id IN (SELECT node_id FROM input_nodes)
            )
          GROUP BY e.result_node_id
        )
        SELECT COUNT(*) AS n FROM nearby
        """,
        (int(node_id), int(node_id), int(node_id)),
    ).fetchone()
    rows = conn.execute(
        """
        WITH input_nodes(node_id) AS (
          SELECT left_node_id FROM edges
          WHERE result_node_id = ? AND left_node_id IS NOT NULL
          UNION
          SELECT right_node_id FROM edges
          WHERE result_node_id = ? AND right_node_id IS NOT NULL
        )
        SELECT
          out.node_id,
          out.p,
          out.q,
          out.kind,
          out.first_stage,
          out.confirmed_stage,
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
    examples = []
    for row in rows:
        key = int(row["p"]), int(row["q"])
        examples.append(
            {
                "node_id": int(row["node_id"]),
                "frac": format_key(key),
                "kind": str(row["kind"]),
                "status": _node_status(row),
                "first_stage": int(row["first_stage"]),
                "confirmed_stage": int(row["confirmed_stage"])
                if row["confirmed_stage"] is not None
                else None,
                "shared_operand_edges": int(row["shared_operand_edges"]),
                "shared_ops": []
                if row["shared_ops"] is None
                else sorted(str(row["shared_ops"]).split(",")),
                "first_shared_stage": int(row["first_shared_stage"]),
            }
        )
    return {
        "nearby_result_count": int(total["n"]),
        "examples": examples,
    }


def _claim_boundary(*, evidence_layer: str, claim_status: str) -> Dict[str, object]:
    return {
        "evidence_layer": evidence_layer,
        "claim_status": claim_status,
        "allowed_claim_language": [
            "This report exposes strict-stage graph features beside classical rational baselines.",
            "A node can be described by its construction edges, witness diversity, neighborhood, and confirmation status in this corpus.",
            "Corpus-wide rankings are screening statistics tied to the recorded corpus parameters.",
        ],
        "disallowed_claim_language": [
            "Do not call a node unusual from a single-node dossier.",
            "Do not treat first_seen_stage as an intrinsic mathematical cost outside this generator and bound set.",
            "Do not promote exploratory closure motifs into strict-stage claims without a strict graph query and promotion criteria.",
        ],
    }


def _ratio_payload(node: sqlite3.Row, baselines: Dict[str, object], stats: Dict[str, int]) -> Dict[str, object]:
    first_stage = int(node["first_stage"])
    denominator = int(baselines["denominator_height"])
    stern = baselines["stern_brocot"]
    stern_depth = stern["depth"] if isinstance(stern, dict) else None
    ratios: Dict[str, object] = {
        "first_stage_over_denominator_height": first_stage / denominator
        if denominator
        else None,
        "derivation_events_over_denominator_height": stats["derivation_events"] / denominator
        if denominator
        else None,
    }
    if isinstance(stern_depth, int) and stern_depth > 0:
        ratios["first_stage_over_stern_brocot_depth"] = first_stage / stern_depth
        ratios["derivation_events_over_stern_brocot_depth"] = (
            stats["derivation_events"] / stern_depth
        )
    else:
        ratios["first_stage_over_stern_brocot_depth"] = None
        ratios["derivation_events_over_stern_brocot_depth"] = None
    return ratios


def node_dossier(
    conn: sqlite3.Connection,
    key: Key,
    *,
    limit: int,
) -> Dict[str, object]:
    key = normalize_key(*key)
    node = _node_for_key(conn, key)
    payload: Dict[str, object] = {
        "report_type": "node_dossier",
        "corpus": _corpus_payload(conn),
        "query": {"node": format_key(key), "normalized_key": {"p": key[0], "q": key[1]}},
        "claim_boundary": _claim_boundary(evidence_layer="strict", claim_status="observation"),
    }
    if node is None:
        payload["found"] = False
        payload["classical_baselines"] = baseline_features(key)
        return payload

    node_id = int(node["node_id"])
    stats = _node_stats(conn, node_id)
    incoming = _incoming_rows(conn, node_id)
    baselines = baseline_features(key)
    payload.update(
        {
            "found": True,
            "node": _node_payload(node),
            "classical_baselines": baselines,
            "moo_arrival": {
                "first_stage": int(node["first_stage"]),
                "confirmed_stage": int(node["confirmed_stage"])
                if node["confirmed_stage"] is not None
                else None,
                "status": _node_status(node),
                "operation_histogram": {
                    "+": stats["+"],
                    "-": stats["-"],
                    "*": stats["*"],
                    "/": stats["/"],
                    "seed": stats["seed"],
                },
            },
            "construction_witnesses": _incoming_summary(incoming, limit=limit),
            "graph_role": {
                "shared_input_neighborhood": _shared_input_neighborhood(
                    conn,
                    node_id,
                    limit=limit,
                ),
                "outgoing_participation": _outgoing_summary(conn, node_id, limit=limit),
            },
            "baseline_ratios": _ratio_payload(node, baselines, stats),
            "graph_invariants": node_graph_invariants(conn, key),
        }
    )
    return payload


def _node_filter_clause(kind: str) -> str:
    if kind == "all":
        return "1 = 1"
    if kind == "rational":
        return "q != 1"
    if kind == "confirmed":
        return "confirmed_stage IS NOT NULL"
    if kind == "speculative":
        return "confirmed_stage IS NULL"
    raise ValueError(f"unknown node kind filter: {kind}")


def _ranking_rows(conn: sqlite3.Connection, *, kind: str) -> List[sqlite3.Row]:
    clause = _node_filter_clause(kind)
    return conn.execute(
        f"""
        SELECT *
        FROM node_stats
        WHERE {clause}
        ORDER BY q ASC, ABS(p) ASC, p ASC
        """
    ).fetchall()


def _normalized_witness_counts(conn: sqlite3.Connection) -> Dict[int, int]:
    rows = conn.execute(
        """
        SELECT
          e.result_node_id,
          e.op,
          l.p AS left_p,
          l.q AS left_q,
          r.p AS right_p,
          r.q AS right_q
        FROM edges e
        LEFT JOIN nodes l ON l.node_id = e.left_node_id
        LEFT JOIN nodes r ON r.node_id = e.right_node_id
        """
    ).fetchall()
    grouped: DefaultDict[int, set] = defaultdict(set)
    for row in rows:
        op = str(row["op"])
        left = None
        right = None
        if row["left_p"] is not None and row["left_q"] is not None:
            left = int(row["left_p"]), int(row["left_q"])
        if row["right_p"] is not None and row["right_q"] is not None:
            right = int(row["right_p"]), int(row["right_q"])
        if op in COMMUTATIVE_OPS and left is not None and right is not None:
            ordered = tuple(sorted((left, right)))
            witness = op, ordered[0], ordered[1]
        else:
            witness = op, left, right
        grouped[int(row["result_node_id"])].add(witness)
    return {node_id: len(witnesses) for node_id, witnesses in grouped.items()}


def _metric_value(
    row: sqlite3.Row,
    *,
    rank_by: str,
    unique_witness_counts: Dict[int, int],
) -> float:
    if rank_by == "derivation_events":
        return float(row["derivation_events"])
    if rank_by == "unique_normalized_witnesses":
        return float(unique_witness_counts.get(int(row["node_id"]), 0))
    if rank_by == "first_stage":
        return float(row["first_stage"])
    if rank_by == "confirmation_lag":
        if row["confirmed_stage"] is None:
            return 0.0
        return float(int(row["confirmed_stage"]) - int(row["first_stage"]))
    raise ValueError(f"unknown ranking metric: {rank_by}")


def _control_value(features: Dict[str, object], *, control: str) -> Optional[object]:
    if control == "none":
        return "all"
    if control == "denominator":
        return int(features["denominator_height"])
    if control == "component_height":
        return int(features["component_height"])
    if control == "stern_brocot_depth":
        stern = features["stern_brocot"]
        if isinstance(stern, dict) and stern.get("applicable"):
            return int(stern["depth"])
        return None
    raise ValueError(f"unknown control: {control}")


def _ranking_baseline_features(key: Key) -> Dict[str, object]:
    p, q = normalize_key(*key)
    value = Fraction(p, q)
    terms = continued_fraction(value)
    stern = stern_brocot_path(value)
    return {
        "denominator_height": int(q),
        "component_height": max(abs(int(p)), int(q)),
        "continued_fraction": {
            "length": len(terms),
        },
        "stern_brocot": stern,
    }


def _directional_percentile(values: List[float], value: float, *, direction: str) -> float:
    if not values:
        return 0.0
    equal = sum(1 for item in values if item == value)
    if direction == "high":
        more_ordinary = sum(1 for item in values if item < value)
    elif direction == "low":
        more_ordinary = sum(1 for item in values if item > value)
    else:
        raise ValueError(f"unknown direction: {direction}")
    return 100.0 * (more_ordinary + 0.5 * equal) / len(values)


def corpus_baseline_rankings(
    conn: sqlite3.Connection,
    *,
    limit: int,
    kind: str,
    rank_by: str,
    control: str,
    direction: str,
    min_peer_group: int,
) -> Dict[str, object]:
    rows = _ranking_rows(conn, kind=kind)
    unique_counts: Dict[int, int] = {}
    if rank_by == "unique_normalized_witnesses":
        unique_counts = _normalized_witness_counts(conn)

    records: List[Dict[str, object]] = []
    groups: DefaultDict[object, List[float]] = defaultdict(list)
    skipped = 0
    for row in rows:
        key = int(row["p"]), int(row["q"])
        features = _ranking_baseline_features(key)
        group_key = _control_value(features, control=control)
        if group_key is None:
            skipped += 1
            continue
        metric = _metric_value(row, rank_by=rank_by, unique_witness_counts=unique_counts)
        record = {
            "node": _node_payload(row),
            "metric_value": metric,
            "control_value": group_key,
            "baseline_features": {
                "denominator_height": features["denominator_height"],
                "component_height": features["component_height"],
                "continued_fraction_length": features["continued_fraction"]["length"],
                "stern_brocot_depth": features["stern_brocot"]["depth"]
                if isinstance(features["stern_brocot"], dict)
                else None,
            },
        }
        records.append(record)
        groups[group_key].append(metric)

    ranked = []
    for record in records:
        values = groups[record["control_value"]]
        if len(values) < int(min_peer_group):
            continue
        med = float(median(values))
        metric = float(record["metric_value"])
        residual = metric - med if direction == "high" else med - metric
        ranked.append(
            {
                **record,
                "peer_group": {
                    "control": control,
                    "value": record["control_value"],
                    "size": len(values),
                    "median": med,
                },
                "directional_percentile": _directional_percentile(
                    values,
                    metric,
                    direction=direction,
                ),
                "residual_from_peer_median": residual,
            }
        )

    ranked.sort(
        key=lambda item: (
            -float(item["directional_percentile"]),
            -float(item["residual_from_peer_median"]),
            -float(item["metric_value"]) if direction == "high" else float(item["metric_value"]),
            int(item["node"]["q"]),
            abs(int(item["node"]["p"])),
        )
    )
    return {
        "report_type": "corpus_baseline_rankings",
        "corpus": _corpus_payload(conn),
        "parameters": {
            "kind": kind,
            "rank_by": rank_by,
            "control": control,
            "direction": direction,
            "min_peer_group": int(min_peer_group),
            "included_nodes": len(records),
            "skipped_nodes": skipped,
        },
        "claim_boundary": _claim_boundary(evidence_layer="strict", claim_status="lead"),
        "rankings": ranked[:limit],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Research-layer scrutiny reports over a strict-stage MoO graph corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--node", help="Build a node dossier for a rational key, e.g. 34/21.")
    mode.add_argument(
        "--corpus-baselines",
        action="store_true",
        help="Rank corpus nodes within a classical rational baseline peer group.",
    )
    parser.add_argument("--limit", type=positive_int, default=12)
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
    parser.add_argument(
        "--kind",
        choices=("rational", "speculative", "confirmed", "all"),
        default="rational",
        help="Node filter for --corpus-baselines.",
    )
    parser.add_argument(
        "--rank-by",
        choices=(
            "derivation_events",
            "unique_normalized_witnesses",
            "first_stage",
            "confirmation_lag",
        ),
        default="derivation_events",
        help="Metric for --corpus-baselines.",
    )
    parser.add_argument(
        "--control",
        choices=("denominator", "component_height", "stern_brocot_depth", "none"),
        default="denominator",
        help="Peer-group baseline for --corpus-baselines.",
    )
    parser.add_argument(
        "--direction",
        choices=("high", "low"),
        default="high",
        help="Whether high or low metric values are ranked as stronger leads.",
    )
    parser.add_argument(
        "--min-peer-group",
        type=positive_int,
        default=3,
        help="Minimum peer-group size for a ranked corpus result.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    with closing(_connect(Path(args.db))) as conn:
        require_strict_alignment(conn)
        if args.node:
            try:
                node_key = parse_key(str(args.node))
            except (ValueError, ZeroDivisionError) as exc:
                parser.error(f"invalid --node value: {exc}")
            payload = node_dossier(
                conn,
                node_key,
                limit=int(args.limit),
            )
        else:
            payload = corpus_baseline_rankings(
                conn,
                limit=int(args.limit),
                kind=str(args.kind),
                rank_by=str(args.rank_by),
                control=str(args.control),
                direction=str(args.direction),
                min_peer_group=int(args.min_peer_group),
            )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_research_report.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
