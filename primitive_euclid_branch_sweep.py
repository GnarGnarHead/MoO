from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo_circle_probe import fraction_key, fraction_record
from moo_circle_square_probe import (
    _corpus_payload,
    _load_nodes,
    _stage_payload,
    _strict_binary_witness,
    _value_node_payload,
    strict_self_product_witness,
)
from moo_research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)
from prime_shell_features import factor_record


Key = Tuple[int, int]
REQUIRED_GENERATOR_LABELS = (
    "m",
    "n",
    "m2",
    "n2",
    "m2_minus_n2",
    "two_mn",
    "m2_plus_n2",
)
REQUIRED_SHELL_LABELS = ("x", "y", "r")
REQUIRED_SQUARE_LABELS = ("x_square", "y_square", "r_square")
SQUARE_PROVENANCE_SOURCES = (
    "self_product_edge",
    "core_confirmation_only",
    "other_graph_witness",
    "absent",
)


@dataclass(frozen=True)
class PrimitiveEuclidBranch:
    m: int
    n: int

    @property
    def m2(self) -> int:
        return self.m * self.m

    @property
    def n2(self) -> int:
        return self.n * self.n

    @property
    def odd_leg(self) -> int:
        return self.m2 - self.n2

    @property
    def even_leg(self) -> int:
        return 2 * self.m * self.n

    @property
    def x(self) -> int:
        return min(self.odd_leg, self.even_leg)

    @property
    def y(self) -> int:
        return max(self.odd_leg, self.even_leg)

    @property
    def r(self) -> int:
        return self.m2 + self.n2

    @property
    def component_height(self) -> int:
        return max(self.x, self.y, self.r)

    @property
    def m_plus_n(self) -> int:
        return self.m + self.n

    @property
    def m_times_n(self) -> int:
        return self.m * self.n

    @property
    def max_mn(self) -> int:
        return max(self.m, self.n)

    @property
    def euclid_expression_complexity(self) -> int:
        return self.m2 + self.n2 + self.m_times_n


def generate_primitive_branches(max_m: int) -> List[PrimitiveEuclidBranch]:
    branches: List[PrimitiveEuclidBranch] = []
    for m in range(2, int(max_m) + 1):
        for n in range(1, m):
            if gcd(m, n) != 1:
                continue
            if (m - n) % 2 != 1:
                continue
            branches.append(PrimitiveEuclidBranch(m=m, n=n))
    branches.sort(key=lambda branch: (branch.r, branch.component_height, branch.m_plus_n, branch.m, branch.n))
    return branches


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "strict",
        "claim_status": "lead",
        "object_language": "primitive_euclid_branch_sweep",
        "allowed_claim_language": [
            "This report records complete, partial, and absent primitive Euclid branches in a strict MoO graph corpus.",
            "A branch is inspected through exact node presence, graph stages, Euclid-generator fields, shell-square fields, and strict self-product witnesses.",
            "Square node presence is separated from branch-local self-product provenance.",
            "Absence and partial visibility are first-class data, not discarded failures.",
        ],
        "disallowed_claim_language": [
            "Do not claim a primitive-branch ordering law from one corpus.",
            "Do not claim primes explain MoO geometry without size, denominator, parameter-size, and graph-cost controls.",
            "Do not treat a square node as branch-constructed merely because the integer spine eventually confirmed it.",
            "Do not claim MoO squares the circle, defines the Euclidean circle, constructs pi, or proves new number theory from this report.",
        ],
    }


def _node_row(value: int, nodes: Dict[Key, sqlite3.Row]) -> Optional[sqlite3.Row]:
    return nodes.get(fraction_key(Fraction(int(value), 1)))


def _row_for_label(
    label: str,
    values: Dict[str, int],
    nodes: Dict[Key, sqlite3.Row],
) -> Optional[sqlite3.Row]:
    return _node_row(values[label], nodes)


def _coverage(rows: Iterable[Optional[sqlite3.Row]], total: int) -> Dict[str, object]:
    present = [row for row in rows if row is not None]
    return {
        "present": len(present),
        "total": int(total),
        "missing": int(total) - len(present),
        "ratio": float(len(present) / int(total)) if int(total) else 0.0,
    }


def _stage_spread(rows: Sequence[Optional[sqlite3.Row]]) -> Optional[int]:
    payload = _stage_payload(rows)
    if payload["stage_spread"] is None:
        return None
    return int(payload["stage_spread"])


def _first_visible_stage(rows: Sequence[Optional[sqlite3.Row]]) -> Optional[int]:
    stages = [int(row["first_stage"]) for row in rows if row is not None]
    return min(stages) if stages else None


def _complete_stage(rows: Sequence[Optional[sqlite3.Row]]) -> Optional[int]:
    if any(row is None for row in rows):
        return None
    stages = [int(row["first_stage"]) for row in rows if row is not None]
    return max(stages) if stages else None


def _value_presence_payload(values: Dict[str, int], nodes: Dict[Key, sqlite3.Row]) -> Dict[str, object]:
    return {
        label: _value_node_payload(Fraction(value, 1), nodes)
        for label, value in values.items()
    }


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


def _corpus_config(conn: sqlite3.Connection) -> Dict[str, object]:
    config = _json_meta(conn, "config_json")
    if isinstance(config, dict):
        return dict(config)
    latest_stage = conn.execute(
        "SELECT stage FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    return {
        "max_stage": int(latest_stage["stage"]) if latest_stage is not None else None,
        "max_abs_p": None,
        "max_abs_q": None,
        "max_abs_value": None,
        "retain_confirmed_edges": None,
    }


def _incoming_edge_summary(conn: sqlite3.Connection, node_id: int) -> Dict[str, object]:
    rows = conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.p AS left_p,
          l.q AS left_q,
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
    op_counts = Counter(str(row["op"]) for row in rows)
    first_stage = min((int(row["stage"]) for row in rows), default=None)
    return {
        "count": len(rows),
        "first_stage": first_stage,
        "op_counts": {op: int(op_counts[op]) for op in sorted(op_counts)},
        "first_edges": [
            {
                "edge_id": int(row["edge_id"]),
                "stage": int(row["stage"]),
                "op": str(row["op"]),
                "left": None
                if row["left_p"] is None
                else {
                    "p": int(row["left_p"]),
                    "q": int(row["left_q"]),
                },
                "right": None
                if row["right_p"] is None
                else {
                    "p": int(row["right_p"]),
                    "q": int(row["right_q"]),
                },
            }
            for row in rows[:5]
        ],
    }


def _incoming_before_confirmed_count(
    conn: sqlite3.Connection,
    node_id: int,
    confirmed_stage: Optional[int],
) -> int:
    if confirmed_stage is None:
        return 0
    row = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM edges
        WHERE result_node_id = ?
          AND stage < ?
        """,
        (int(node_id), int(confirmed_stage)),
    ).fetchone()
    return int(row["n"]) if row is not None else 0


def _retention_blocker(
    *,
    source_value: int,
    square_value: int,
    source_row: Optional[sqlite3.Row],
    config: Dict[str, object],
) -> Dict[str, object]:
    max_stage = config.get("max_stage")
    max_abs_p = config.get("max_abs_p")
    max_abs_q = config.get("max_abs_q")
    max_abs_value = config.get("max_abs_value")
    confirmed_stage = None
    if source_row is not None and source_row["confirmed_stage"] is not None:
        confirmed_stage = int(source_row["confirmed_stage"])
    candidate_edge_stage = int(source_value) if int(source_value) >= 1 else None
    blockers: List[str] = []
    if source_row is None or confirmed_stage is None:
        blockers.append("operand_not_confirmed")
    if max_stage is not None and candidate_edge_stage is not None and candidate_edge_stage > int(max_stage):
        blockers.append("edge_not_generated_at_current_U")
        if "operand_not_confirmed" not in blockers:
            blockers.append("operand_not_confirmed")
    if max_abs_p is not None and abs(int(square_value)) > int(max_abs_p):
        blockers.append("output_excluded_by_max_abs_p")
    if max_abs_q is not None and 1 > int(max_abs_q):
        blockers.append("output_excluded_by_max_abs_q")
    if max_abs_value is not None and abs(float(square_value)) > float(max_abs_value):
        blockers.append("output_excluded_by_max_abs_value")
    if not blockers:
        blockers.append("unknown")
    return {
        "primary": blockers[0],
        "all": blockers,
        "candidate_edge_stage": candidate_edge_stage,
        "source_confirmed_stage": confirmed_stage,
        "config_snapshot": {
            "max_stage": int(max_stage) if max_stage is not None else None,
            "max_abs_p": int(max_abs_p) if max_abs_p is not None else None,
            "max_abs_q": int(max_abs_q) if max_abs_q is not None else None,
            "max_abs_value": float(max_abs_value) if max_abs_value is not None else None,
        },
    }


def _square_provenance_payload(
    conn: sqlite3.Connection,
    *,
    label: str,
    source_value: int,
    square_value: int,
    nodes: Dict[Key, sqlite3.Row],
    config: Dict[str, object],
) -> Dict[str, object]:
    source_row = _node_row(source_value, nodes)
    square_row = _node_row(square_value, nodes)
    self_product = strict_self_product_witness(conn, source_row, square_row)
    self_product_stage = (
        int(self_product["stage"])
        if bool(self_product.get("present")) and self_product.get("stage") is not None
        else None
    )
    operands_confirmed = False
    if self_product_stage is not None and source_row is not None:
        confirmed_stage = source_row["confirmed_stage"]
        operands_confirmed = confirmed_stage is not None and int(confirmed_stage) <= self_product_stage

    incoming_edges: Optional[Dict[str, object]] = None
    incoming_before_confirmed = 0
    if square_row is not None:
        incoming_edges = _incoming_edge_summary(conn, int(square_row["node_id"]))
        incoming_before_confirmed = _incoming_before_confirmed_count(
            conn,
            int(square_row["node_id"]),
            int(square_row["confirmed_stage"]) if square_row["confirmed_stage"] is not None else None,
        )

    if square_row is None:
        source = "absent"
    elif bool(self_product.get("present")):
        source = "self_product_edge"
    elif (
        square_row["confirmed_stage"] is not None
        and int(square_row["first_stage"]) == int(square_row["confirmed_stage"])
        and incoming_before_confirmed == 0
    ):
        source = "core_confirmation_only"
    else:
        source = "other_graph_witness"

    return {
        "label": label,
        "component": fraction_record(Fraction(source_value, 1)),
        "square": fraction_record(Fraction(square_value, 1)),
        "node_present": square_row is not None,
        "first_stage": int(square_row["first_stage"]) if square_row is not None else None,
        "confirmed_stage": int(square_row["confirmed_stage"])
        if square_row is not None and square_row["confirmed_stage"] is not None
        else None,
        "incoming_edges": incoming_edges
        if incoming_edges is not None
        else {
            "count": 0,
            "first_stage": None,
            "op_counts": {},
            "first_edges": [],
        },
        "incoming_before_confirmed_count": int(incoming_before_confirmed),
        "self_product_edge_present": bool(self_product.get("present")),
        "self_product_edge_stage": self_product_stage,
        "self_product_edge_operands_confirmed_at_stage": bool(operands_confirmed),
        "self_product_edge": self_product,
        "square_node_source": source,
        "retention_blocker": None
        if square_row is not None
        else _retention_blocker(
            source_value=source_value,
            square_value=square_value,
            source_row=source_row,
            config=config,
        ),
    }


def _binary_generator_witnesses(
    conn: sqlite3.Connection,
    values: Dict[str, int],
    nodes: Dict[Key, sqlite3.Row],
) -> Dict[str, object]:
    m = Fraction(values["m"], 1)
    n = Fraction(values["n"], 1)
    m2 = Fraction(values["m2"], 1)
    n2 = Fraction(values["n2"], 1)
    odd_leg = Fraction(values["m2_minus_n2"], 1)
    even_leg = Fraction(values["two_mn"], 1)
    radius = Fraction(values["m2_plus_n2"], 1)
    mn = m * n
    two_m = 2 * m
    two_n = 2 * n
    return {
        "m_self_product": strict_self_product_witness(
            conn,
            nodes.get(fraction_key(m)),
            nodes.get(fraction_key(m2)),
        ),
        "n_self_product": strict_self_product_witness(
            conn,
            nodes.get(fraction_key(n)),
            nodes.get(fraction_key(n2)),
        ),
        "m2_minus_n2_witness": _strict_binary_witness(conn, m2, "-", n2, odd_leg, nodes),
        "m2_plus_n2_witness": _strict_binary_witness(conn, m2, "+", n2, radius, nodes),
        "two_mn_witness": {
            "m_times_n": _strict_binary_witness(conn, m, "*", n, mn, nodes),
            "two_times_mn": _strict_binary_witness(conn, Fraction(2, 1), "*", mn, even_leg, nodes),
            "two_m_times_n": _strict_binary_witness(conn, two_m, "*", n, even_leg, nodes),
            "m_times_two_n": _strict_binary_witness(conn, m, "*", two_n, even_leg, nodes),
        },
    }


def _generator_witness_coverage(witnesses: Dict[str, object]) -> Dict[str, object]:
    two_mn = witnesses["two_mn_witness"]
    if not isinstance(two_mn, dict):
        two_mn_present = False
    else:
        two_mn_present = any(bool(payload["present"]) for payload in two_mn.values())
    fields = [
        bool(witnesses["m_self_product"]["present"]),
        bool(witnesses["n_self_product"]["present"]),
        bool(witnesses["m2_minus_n2_witness"]["present"]),
        bool(witnesses["m2_plus_n2_witness"]["present"]),
        two_mn_present,
    ]
    return {
        "present": int(sum(1 for item in fields if item)),
        "total": len(fields),
        "missing": int(len(fields) - sum(1 for item in fields if item)),
        "ratio": float(sum(1 for item in fields if item) / len(fields)),
        "two_mn_any_path_present": two_mn_present,
    }


def _self_product_payload(
    conn: sqlite3.Connection,
    shell_values: Dict[str, int],
    square_values: Dict[str, int],
    nodes: Dict[Key, sqlite3.Row],
) -> Dict[str, object]:
    witnesses = {}
    present_count = 0
    for label in REQUIRED_SHELL_LABELS:
        source = _node_row(shell_values[label], nodes)
        square = _node_row(square_values[f"{label}_square"], nodes)
        payload = strict_self_product_witness(conn, source, square)
        witnesses[label] = payload
        if bool(payload["present"]):
            present_count += 1
    return {
        "witnesses": witnesses,
        "coverage": {
            "present": present_count,
            "total": len(REQUIRED_SHELL_LABELS),
            "missing": len(REQUIRED_SHELL_LABELS) - present_count,
            "ratio": float(present_count / len(REQUIRED_SHELL_LABELS)),
        },
    }


def _square_provenance_summary(square_provenance: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    counts = Counter(str(payload["square_node_source"]) for payload in square_provenance.values())
    self_product_count = sum(
        1 for payload in square_provenance.values() if bool(payload["self_product_edge_present"])
    )
    present_count = sum(1 for payload in square_provenance.values() if bool(payload["node_present"]))
    return {
        "source_counts": {
            source: int(counts.get(source, 0)) for source in SQUARE_PROVENANCE_SOURCES
        },
        "present_count": int(present_count),
        "self_product_edge_count": int(self_product_count),
        "square_node_complete": present_count == len(REQUIRED_SHELL_LABELS),
        "square_self_product_complete": self_product_count == len(REQUIRED_SHELL_LABELS),
    }


def _failure_category(
    *,
    generator_present: int,
    generator_complete: bool,
    shell_present: int,
    shell_complete: bool,
    square_complete: bool,
    all_self_products_present: bool,
) -> str:
    if generator_present == 0 and shell_present == 0:
        return "absent_under_bounds"
    if generator_complete and shell_complete and square_complete:
        if all_self_products_present:
            return "complete_branch"
        return "self_product_witness_missing"
    if generator_complete and shell_complete and not square_complete:
        return "square_components_missing"
    if shell_complete and not generator_complete:
        return "shell_visible_generator_unrecovered"
    if generator_present > 0 and not shell_complete:
        return "generator_visible_shell_incomplete"
    if shell_present > 0 and not generator_complete:
        return "shell_visible_generator_unrecovered"
    return "absent_under_bounds"


def _branch_factorization(branch: PrimitiveEuclidBranch) -> Dict[str, object]:
    return {
        "m": factor_record(branch.m),
        "n": factor_record(branch.n),
        "m2": factor_record(branch.m2),
        "n2": factor_record(branch.n2),
        "m2_minus_n2": factor_record(branch.odd_leg),
        "two_mn": factor_record(branch.even_leg),
        "m2_plus_n2": factor_record(branch.r),
        "x": factor_record(branch.x),
        "y": factor_record(branch.y),
        "r": factor_record(branch.r),
    }


def branch_payload(
    conn: sqlite3.Connection,
    branch: PrimitiveEuclidBranch,
    nodes: Dict[Key, sqlite3.Row],
) -> Dict[str, object]:
    config = _corpus_config(conn)
    generator_values = {
        "m": branch.m,
        "n": branch.n,
        "m2": branch.m2,
        "n2": branch.n2,
        "m2_minus_n2": branch.odd_leg,
        "two_mn": branch.even_leg,
        "m2_plus_n2": branch.r,
    }
    shell_values = {
        "x": branch.x,
        "y": branch.y,
        "r": branch.r,
    }
    square_values = {
        "x_square": branch.x * branch.x,
        "y_square": branch.y * branch.y,
        "r_square": branch.r * branch.r,
    }
    generator_rows = [_row_for_label(label, generator_values, nodes) for label in REQUIRED_GENERATOR_LABELS]
    shell_rows = [_row_for_label(label, shell_values, nodes) for label in REQUIRED_SHELL_LABELS]
    square_rows = [_row_for_label(label, square_values, nodes) for label in REQUIRED_SQUARE_LABELS]
    all_rows = [*generator_rows, *shell_rows, *square_rows]
    generator_coverage = _coverage(generator_rows, len(REQUIRED_GENERATOR_LABELS))
    shell_coverage = _coverage(shell_rows, len(REQUIRED_SHELL_LABELS))
    square_coverage = _coverage(square_rows, len(REQUIRED_SQUARE_LABELS))
    self_product = _self_product_payload(conn, shell_values, square_values, nodes)
    square_provenance = {
        label: _square_provenance_payload(
            conn,
            label=label,
            source_value=shell_values[label],
            square_value=square_values[f"{label}_square"],
            nodes=nodes,
            config=config,
        )
        for label in REQUIRED_SHELL_LABELS
    }
    square_provenance_summary = _square_provenance_summary(square_provenance)
    generator_witnesses = _binary_generator_witnesses(conn, generator_values, nodes)
    generator_witness_coverage = _generator_witness_coverage(generator_witnesses)
    first_complete_stage = _complete_stage(all_rows)
    all_self_products_present = int(self_product["coverage"]["present"]) == int(self_product["coverage"]["total"])
    failure_category = _failure_category(
        generator_present=int(generator_coverage["present"]),
        generator_complete=int(generator_coverage["missing"]) == 0,
        shell_present=int(shell_coverage["present"]),
        shell_complete=int(shell_coverage["missing"]) == 0,
        square_complete=int(square_coverage["missing"]) == 0,
        all_self_products_present=all_self_products_present,
    )
    return {
        "primitive_triple": {
            "x": branch.x,
            "y": branch.y,
            "r": branch.r,
            "label": f"{branch.x},{branch.y},{branch.r}",
        },
        "euclid_parameters": {
            "m": branch.m,
            "n": branch.n,
            "m2": branch.m2,
            "n2": branch.n2,
            "m2_minus_n2": branch.odd_leg,
            "two_mn": branch.even_leg,
            "m2_plus_n2": branch.r,
            "gcd_mn": gcd(branch.m, branch.n),
            "opposite_parity": (branch.m - branch.n) % 2 == 1,
        },
        "euclid_valid": (
            gcd(branch.m, branch.n) == 1
            and (branch.m - branch.n) % 2 == 1
            and branch.x * branch.x + branch.y * branch.y == branch.r * branch.r
        ),
        "size_controls": {
            "radius": branch.r,
            "component_height": branch.component_height,
            "m_plus_n": branch.m_plus_n,
            "max_mn": branch.max_mn,
            "m_times_n": branch.m_times_n,
            "m2_plus_n2": branch.r,
            "euclid_expression_complexity": branch.euclid_expression_complexity,
        },
        "radius": branch.r,
        "component_height": branch.component_height,
        "m_plus_n": branch.m_plus_n,
        "m_times_n": branch.m_times_n,
        "generator_values": {
            label: fraction_record(Fraction(value, 1))
            for label, value in generator_values.items()
        },
        "shell_values": {
            label: fraction_record(Fraction(value, 1))
            for label, value in shell_values.items()
        },
        "square_values": {
            label: fraction_record(Fraction(value, 1))
            for label, value in square_values.items()
        },
        "node_presence": {
            "generator": _value_presence_payload(generator_values, nodes),
            "shell": _value_presence_payload(shell_values, nodes),
            "square_components": _value_presence_payload(square_values, nodes),
        },
        "factorization": _branch_factorization(branch),
        "generator_witnesses": generator_witnesses,
        "generator_witness_coverage": generator_witness_coverage,
        "self_product_witnesses": self_product["witnesses"],
        "square_provenance": square_provenance,
        "square_provenance_summary": square_provenance_summary,
        "coverage_counts": {
            "generator": generator_coverage,
            "shell": shell_coverage,
            "square_components": square_coverage,
            "self_product_witnesses": self_product["coverage"],
        },
        "generator_coverage": float(generator_coverage["ratio"]),
        "shell_coverage": float(shell_coverage["ratio"]),
        "square_coverage": float(square_coverage["ratio"]),
        "self_product_witness_coverage": float(self_product["coverage"]["ratio"]),
        "first_visible_stage": _first_visible_stage(all_rows),
        "first_complete_stage": first_complete_stage,
        "generator_phase_spread": _stage_spread(generator_rows),
        "shell_phase_spread": _stage_spread(shell_rows),
        "square_phase_spread": _stage_spread(square_rows),
        "node_complete_branch": first_complete_stage is not None,
        "square_node_complete": bool(square_provenance_summary["square_node_complete"]),
        "square_self_product_complete": bool(square_provenance_summary["square_self_product_complete"]),
        "branch_constructed_square_layer": bool(square_provenance_summary["square_self_product_complete"]),
        "strict_self_product_complete_branch": first_complete_stage is not None and all_self_products_present,
        "failure_category": failure_category,
        "graph_cost_rank": None,
        "radius_size_rank": None,
        "component_height_rank": None,
        "parameter_size_rank": None,
    }


def _assign_dense_rank(rows: List[Dict[str, object]], rank_field: str, key_field: str) -> None:
    values = sorted({int(row[key_field]) for row in rows})
    ranks = {value: index + 1 for index, value in enumerate(values)}
    for row in rows:
        row[rank_field] = ranks[int(row[key_field])]


def _assign_parameter_rank(rows: List[Dict[str, object]]) -> None:
    keys = sorted(
        {
            (
                int(row["m_plus_n"]),
                int(row["size_controls"]["max_mn"]),
                int(row["m_times_n"]),
            )
            for row in rows
        }
    )
    ranks = {key: index + 1 for index, key in enumerate(keys)}
    for row in rows:
        key = (
            int(row["m_plus_n"]),
            int(row["size_controls"]["max_mn"]),
            int(row["m_times_n"]),
        )
        row["parameter_size_rank"] = ranks[key]


def _assign_graph_cost_rank(rows: List[Dict[str, object]]) -> None:
    complete = [
        row for row in rows if row["first_complete_stage"] is not None
    ]
    keys = sorted(
        {
            (
                int(row["first_complete_stage"]),
                int(row["component_height"]),
                int(row["m_plus_n"]),
            )
            for row in complete
        }
    )
    ranks = {key: index + 1 for index, key in enumerate(keys)}
    for row in complete:
        key = (
            int(row["first_complete_stage"]),
            int(row["component_height"]),
            int(row["m_plus_n"]),
        )
        row["graph_cost_rank"] = ranks[key]


def _rank_branches(rows: List[Dict[str, object]]) -> None:
    _assign_dense_rank(rows, "radius_size_rank", "radius")
    _assign_dense_rank(rows, "component_height_rank", "component_height")
    _assign_parameter_rank(rows)
    _assign_graph_cost_rank(rows)


def primitive_branch_sweep(
    conn: sqlite3.Connection,
    *,
    max_m: int,
) -> Dict[str, object]:
    nodes = _load_nodes(conn)
    branches = generate_primitive_branches(max_m)
    branch_rows = [branch_payload(conn, branch, nodes) for branch in branches]
    _rank_branches(branch_rows)
    category_counts: Dict[str, int] = {}
    square_source_counts = Counter()
    for row in branch_rows:
        category = str(row["failure_category"])
        category_counts[category] = category_counts.get(category, 0) + 1
        for source, count in row["square_provenance_summary"]["source_counts"].items():
            square_source_counts[str(source)] += int(count)
    node_complete = [row for row in branch_rows if bool(row["node_complete_branch"])]
    strict_complete = [row for row in branch_rows if bool(row["strict_self_product_complete_branch"])]
    generator_complete = [
        row for row in branch_rows if int(row["coverage_counts"]["generator"]["missing"]) == 0
    ]
    shell_complete = [
        row for row in branch_rows if int(row["coverage_counts"]["shell"]["missing"]) == 0
    ]
    square_complete = [
        row for row in branch_rows if int(row["coverage_counts"]["square_components"]["missing"]) == 0
    ]
    return {
        "report_type": "primitive_euclid_branch_sweep",
        "corpus": _corpus_payload(conn),
        "claim_boundary": _claim_boundary(),
        "parameters": {
            "max_m": int(max_m),
            "n_rule": "1 <= n < m",
            "primitive_rule": "gcd(m,n)=1 and m-n odd",
            "branch_count": len(branch_rows),
        },
        "rank_definitions": {
            "graph_cost_rank": (
                "Dense rank among node-complete branches by first_complete_stage, "
                "then component_height, then m_plus_n. Incomplete branches have null rank."
            ),
            "radius_size_rank": "Dense rank by primitive radius r=m*m+n*n.",
            "component_height_rank": "Dense rank by max(x,y,r).",
            "parameter_size_rank": "Dense rank by (m+n, max(m,n), m*n).",
        },
        "provenance_definitions": {
            "self_product_edge": "The square node has a strict branch-local edge v * v -> v*v.",
            "core_confirmation_only": "The square node appears at its core-loop confirmation stage without an earlier graph witness.",
            "other_graph_witness": "The square node has graph provenance, but not from the branch-local self-product edge.",
            "absent": "The square node is absent from the corpus.",
        },
        "summary": {
            "branch_count": len(branch_rows),
            "node_complete_branch_count": len(node_complete),
            "strict_self_product_complete_branch_count": len(strict_complete),
            "generator_complete_count": len(generator_complete),
            "shell_complete_count": len(shell_complete),
            "square_complete_count": len(square_complete),
            "square_self_product_complete_count": len(
                [row for row in branch_rows if bool(row["square_self_product_complete"])]
            ),
            "square_provenance_source_counts": {
                source: int(square_source_counts.get(source, 0))
                for source in SQUARE_PROVENANCE_SOURCES
            },
            "failure_category_counts": {
                key: category_counts[key] for key in sorted(category_counts)
            },
        },
        "branches": branch_rows,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sweep primitive Euclid branches over a strict MoO graph corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--max-m", type=positive_int, default=8)
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
    with closing(connect_readonly(Path(args.db))) as conn:
        require_strict_alignment(conn)
        payload = primitive_branch_sweep(conn, max_m=int(args.max_m))
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="primitive_euclid_branch_sweep.v2",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
