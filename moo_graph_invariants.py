from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from itertools import combinations
from statistics import median
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from rational_baselines import baseline_features, format_key, normalize_key


Key = Tuple[int, int]
COMMUTATIVE_OPS = {"+", "*"}


def node_status(row: sqlite3.Row) -> str:
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


def node_payload(row: sqlite3.Row) -> Dict[str, object]:
    key = int(row["p"]), int(row["q"])
    return {
        "node_id": int(row["node_id"]),
        "frac": format_key(key),
        "p": int(key[0]),
        "q": int(key[1]),
        "kind": str(row["kind"]),
        "status": node_status(row),
        "first_stage": int(row["first_stage"]),
        "confirmed_stage": int(row["confirmed_stage"])
        if row["confirmed_stage"] is not None
        else None,
    }


def confirmation_lag(row: sqlite3.Row) -> Optional[int]:
    if row["confirmed_stage"] is None:
        return None
    return int(row["confirmed_stage"]) - int(row["first_stage"])


def node_for_key(conn: sqlite3.Connection, key: Key) -> Optional[sqlite3.Row]:
    p, q = normalize_key(*key)
    return conn.execute(
        "SELECT * FROM nodes WHERE p = ? AND q = ?",
        (int(p), int(q)),
    ).fetchone()


def _operand_key(row: sqlite3.Row, prefix: str) -> Optional[Key]:
    p = row[f"{prefix}_p"]
    q = row[f"{prefix}_q"]
    if p is None or q is None:
        return None
    return int(p), int(q)


def _algebraic_witness(row: sqlite3.Row, *, normalize_commutative: bool) -> Tuple[object, ...]:
    op = str(row["op"])
    left = _operand_key(row, "left")
    right = _operand_key(row, "right")
    if normalize_commutative and op in COMMUTATIVE_OPS and left is not None and right is not None:
        ordered = tuple(sorted((left, right)))
        return op, ordered[0], ordered[1]
    return op, left, right


def _input_pair(row: sqlite3.Row, *, normalize_commutative: bool) -> Tuple[object, ...]:
    op = str(row["op"])
    left = _operand_key(row, "left")
    right = _operand_key(row, "right")
    if normalize_commutative and op in COMMUTATIVE_OPS and left is not None and right is not None:
        ordered = tuple(sorted((left, right)))
        return ordered[0], ordered[1]
    return left, right


def incoming_rows(conn: sqlite3.Connection, node_id: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.node_id AS left_node_id,
          l.p AS left_p,
          l.q AS left_q,
          r.node_id AS right_node_id,
          r.p AS right_p,
          r.q AS right_q
        FROM edges e
        LEFT JOIN nodes l ON l.node_id = e.left_node_id
        LEFT JOIN nodes r ON r.node_id = e.right_node_id
        WHERE e.result_node_id = ?
        ORDER BY e.stage, e.edge_id
        """,
        (int(node_id),),
    ).fetchall()


def operation_signature(rows: Sequence[sqlite3.Row]) -> Dict[str, object]:
    counts = Counter(str(row["op"]) for row in rows)
    total = sum(counts.values())
    dominant_op = None
    if counts:
        dominant_op = sorted(counts.items(), key=lambda item: (-int(item[1]), item[0]))[0][0]
    return {
        "incoming_derivation_events": int(total),
        "counts": {op: int(counts[op]) for op in sorted(counts)},
        "dominant_op": dominant_op,
    }


def witness_family_counts(rows: Sequence[sqlite3.Row]) -> Dict[str, int]:
    directed_witnesses = {_algebraic_witness(row, normalize_commutative=False) for row in rows}
    normalized_witnesses = {_algebraic_witness(row, normalize_commutative=True) for row in rows}
    directed_pairs = {_input_pair(row, normalize_commutative=False) for row in rows}
    normalized_pairs = {_input_pair(row, normalize_commutative=True) for row in rows}
    return {
        "unique_directed_algebraic": int(len(directed_witnesses)),
        "unique_commutative_normalized_algebraic": int(len(normalized_witnesses)),
        "distinct_directed_input_pairs": int(len(directed_pairs)),
        "distinct_commutative_normalized_input_pairs": int(len(normalized_pairs)),
    }


def shared_input_neighborhood_ids(conn: sqlite3.Connection, node_id: int) -> Set[int]:
    rows = conn.execute(
        """
        WITH input_nodes(node_id) AS (
          SELECT left_node_id FROM edges
          WHERE result_node_id = ? AND left_node_id IS NOT NULL
          UNION
          SELECT right_node_id FROM edges
          WHERE result_node_id = ? AND right_node_id IS NOT NULL
        )
        SELECT e.result_node_id
        FROM edges e
        WHERE e.result_node_id != ?
          AND (
            e.left_node_id IN (SELECT node_id FROM input_nodes)
            OR e.right_node_id IN (SELECT node_id FROM input_nodes)
          )
        GROUP BY e.result_node_id
        """,
        (int(node_id), int(node_id), int(node_id)),
    ).fetchall()
    return {int(row["result_node_id"]) for row in rows}


def _control_value(features: Dict[str, object], control: str) -> object:
    if control == "denominator":
        return int(features["denominator_height"])
    if control == "component_height":
        return int(features["component_height"])
    raise ValueError(f"unknown baseline control: {control}")


def _all_node_stats(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute("SELECT * FROM node_stats").fetchall()


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
    metric: str,
    unique_witness_counts: Dict[int, int],
) -> Optional[float]:
    if metric == "incoming_derivation_events":
        return float(row["derivation_events"])
    if metric == "distinct_witness_families":
        return float(unique_witness_counts.get(int(row["node_id"]), 0))
    if metric == "first_stage":
        return float(row["first_stage"])
    if metric == "confirmation_lag":
        if row["confirmed_stage"] is None:
            return None
        return float(int(row["confirmed_stage"]) - int(row["first_stage"]))
    raise ValueError(f"unknown invariant metric: {metric}")


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


def baseline_adjusted_rank(
    conn: sqlite3.Connection,
    key: Key,
    *,
    metric: str,
    control: str,
    direction: str,
    min_peer_group: int = 3,
) -> Dict[str, object]:
    p, q = normalize_key(*key)
    rows = _all_node_stats(conn)
    target = None
    groups: DefaultDict[object, List[float]] = defaultdict(list)
    unique_counts: Dict[int, int] = {}
    if metric == "distinct_witness_families":
        unique_counts = _normalized_witness_counts(conn)

    for row in rows:
        row_key = int(row["p"]), int(row["q"])
        if row_key == (p, q):
            target = row
        features = baseline_features(row_key)
        group_key = _control_value(features, control)
        value = _metric_value(row, metric=metric, unique_witness_counts=unique_counts)
        if value is None:
            continue
        groups[group_key].append(float(value))

    if target is None:
        return {
            "available": False,
            "reason": "target node is absent from node_stats",
            "metric": metric,
            "control": control,
        }

    target_features = baseline_features((p, q))
    target_group = _control_value(target_features, control)
    target_value = _metric_value(target, metric=metric, unique_witness_counts=unique_counts)
    if target_value is None:
        return {
            "available": False,
            "reason": "metric is not defined for this node",
            "metric": metric,
            "control": control,
            "control_value": target_group,
        }

    values = groups[target_group]
    if len(values) < int(min_peer_group):
        return {
            "available": False,
            "reason": "peer group is smaller than min_peer_group",
            "metric": metric,
            "control": control,
            "control_value": target_group,
            "metric_value": float(target_value),
            "peer_group_size": len(values),
            "min_peer_group": int(min_peer_group),
        }

    med = float(median(values))
    residual = float(target_value) - med if direction == "high" else med - float(target_value)
    return {
        "available": True,
        "metric": metric,
        "control": control,
        "direction": direction,
        "control_value": target_group,
        "metric_value": float(target_value),
        "peer_group_size": len(values),
        "peer_group_median": med,
        "residual_from_peer_median": residual,
        "directional_percentile": _directional_percentile(
            values,
            float(target_value),
            direction=direction,
        ),
    }


def baseline_adjusted_rank_suite(
    conn: sqlite3.Connection,
    key: Key,
    *,
    min_peer_group: int = 3,
) -> Dict[str, object]:
    suite = {
        "incoming_derivation_events": "high",
        "distinct_witness_families": "high",
        "confirmation_lag": "high",
        "first_stage": "low",
    }
    return {
        metric: {
            control: baseline_adjusted_rank(
                conn,
                key,
                metric=metric,
                control=control,
                direction=direction,
                min_peer_group=min_peer_group,
            )
            for control in ("denominator", "component_height")
        }
        for metric, direction in suite.items()
    }


def node_graph_invariants(
    conn: sqlite3.Connection,
    key: Key,
    *,
    include_baseline_rank: bool = True,
    min_peer_group: int = 3,
) -> Dict[str, object]:
    p, q = normalize_key(*key)
    row = node_for_key(conn, (p, q))
    payload: Dict[str, object] = {
        "vocabulary_version": "graph_invariants.v1",
        "present": row is not None,
        "key": {"p": int(p), "q": int(q), "frac": format_key((p, q))},
        "baselines": {
            "denominator_height": int(q),
            "component_height": max(abs(int(p)), int(q)),
            "classical": baseline_features((p, q)),
        },
    }
    if row is None:
        return payload

    rows = incoming_rows(conn, int(row["node_id"]))
    payload.update(
        {
            "node": node_payload(row),
            "arrival": {
                "first_stage": int(row["first_stage"]),
                "confirmed_stage": int(row["confirmed_stage"])
                if row["confirmed_stage"] is not None
                else None,
                "confirmation_lag": confirmation_lag(row),
                "status": node_status(row),
            },
            "incoming_derivation_events": len(rows),
            "distinct_witness_families": witness_family_counts(rows),
            "operation_signature": operation_signature(rows),
            "neighborhood_overlap": {
                "metric": "shared_input_result_count",
                "shared_input_result_count": len(shared_input_neighborhood_ids(conn, int(row["node_id"]))),
            },
        }
    )
    if include_baseline_rank:
        payload["baseline_adjusted_rank"] = baseline_adjusted_rank_suite(
            conn,
            (p, q),
            min_peer_group=min_peer_group,
        )
    return payload


def family_graph_invariants(
    conn: sqlite3.Connection,
    named_keys: Sequence[Tuple[str, Key]],
    *,
    include_node_invariants: bool = True,
) -> Dict[str, object]:
    members = []
    neighborhood_sets: Dict[str, Set[int]] = {}
    aggregate_ops: Counter[str] = Counter()
    first_stages: List[int] = []
    confirmation_lags: List[int] = []
    denominator_heights: List[int] = []
    component_heights: List[int] = []
    total_incoming = 0

    for label, key in named_keys:
        normalized = normalize_key(*key)
        row = node_for_key(conn, normalized)
        baseline = baseline_features(normalized)
        denominator_heights.append(int(baseline["denominator_height"]))
        component_heights.append(int(baseline["component_height"]))
        member: Dict[str, object] = {
            "label": label,
            "key": {"p": int(normalized[0]), "q": int(normalized[1]), "frac": format_key(normalized)},
            "present": row is not None,
        }
        if row is not None:
            rows = incoming_rows(conn, int(row["node_id"]))
            ops = operation_signature(rows)
            aggregate_ops.update({op: int(count) for op, count in ops["counts"].items()})
            total_incoming += len(rows)
            first_stages.append(int(row["first_stage"]))
            lag = confirmation_lag(row)
            if lag is not None:
                confirmation_lags.append(int(lag))
            neighborhood_sets[label] = shared_input_neighborhood_ids(conn, int(row["node_id"]))
            member["node"] = node_payload(row)
            if include_node_invariants:
                member["graph_invariants"] = node_graph_invariants(
                    conn,
                    normalized,
                    include_baseline_rank=False,
                )
        members.append(member)

    overlaps = []
    for left, right in combinations(sorted(neighborhood_sets), 2):
        left_set = neighborhood_sets[left]
        right_set = neighborhood_sets[right]
        union = left_set | right_set
        intersection = left_set & right_set
        overlaps.append(
            {
                "left": left,
                "right": right,
                "intersection_count": len(intersection),
                "union_count": len(union),
                "jaccard": float(len(intersection) / len(union)) if union else None,
            }
        )

    return {
        "vocabulary_version": "graph_invariants.v1",
        "member_count": len(named_keys),
        "present_member_count": sum(1 for member in members if bool(member["present"])),
        "missing_member_count": sum(1 for member in members if not bool(member["present"])),
        "max_first_stage": max(first_stages) if first_stages else None,
        "max_confirmation_lag": max(confirmation_lags) if confirmation_lags else None,
        "total_incoming_derivation_events": int(total_incoming),
        "aggregate_operation_signature": {
            "incoming_derivation_events": int(sum(aggregate_ops.values())),
            "counts": {op: int(aggregate_ops[op]) for op in sorted(aggregate_ops)},
        },
        "baseline_envelope": {
            "max_denominator_height": max(denominator_heights) if denominator_heights else None,
            "max_component_height": max(component_heights) if component_heights else None,
        },
        "neighborhood_overlap": {
            "metric": "pairwise_shared_input_neighborhood_jaccard",
            "pairs": overlaps,
        },
        "members": members,
    }
