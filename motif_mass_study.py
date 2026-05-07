from __future__ import annotations

import argparse
import json
import math
import signal
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from statistics import median
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple


OPS = ("+", "-", "*", "/")
DEFAULT_BINDING_VALUES = ("22/7", "87/32", "52/75", "99/70", "34/21")


@dataclass(frozen=True)
class Edge:
    child: Fraction
    op: str
    a: Fraction
    b: Fraction
    pair: Tuple[Fraction, Fraction]
    motif: str
    child_round: int
    a_round: int
    b_round: int


@dataclass(frozen=True)
class MassConfig:
    native_report: Path
    aperture_report: Optional[Path]
    motif_report: Optional[Path]
    binding_report: Optional[Path]
    square_report: Optional[Path]
    triangle_report: Optional[Path]
    top_k: int
    major_count: int
    min_parent_q: int
    min_child_q: int
    include_rows: bool


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(int(value.numerator))
    return f"{int(value.numerator)}/{int(value.denominator)}"


def _parse_fraction(value: object) -> Optional[Fraction]:
    if value is None:
        return None
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return None


def _load_report(path: Optional[Path], *, require_ledger: bool = False) -> Optional[Dict[str, object]]:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Report is not a JSON object: {path}")
    if require_ledger and not isinstance(payload.get("ledger"), list):
        raise SystemExit(f"Report has no ledger: {path}")
    return payload


def _rows_by_frac(report: Dict[str, object]) -> Dict[Fraction, Dict[str, object]]:
    rows: Dict[Fraction, Dict[str, object]] = {}
    ledger = report.get("ledger")
    if not isinstance(ledger, list):
        return rows
    for row in ledger:
        if not isinstance(row, dict):
            continue
        try:
            value = Fraction(int(row["p"]), int(row["q"]))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
        rows[value] = row
    return rows


def _row_fraction(row: Dict[str, object]) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _row_int(row: Optional[Dict[str, object]], key: str, default: int = 0) -> int:
    if row is None:
        return int(default)
    try:
        return int(row.get(key, default))
    except (TypeError, ValueError):
        return int(default)


def _row_float(row: Optional[Dict[str, object]], key: str, default: float = 0.0) -> float:
    if row is None:
        return float(default)
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _complexity_key(value: Fraction) -> Tuple[int, int, int]:
    return (int(value.denominator), abs(int(value.numerator)), int(value.numerator))


def _sort_pair(a: Fraction, b: Fraction) -> Tuple[Fraction, Fraction]:
    ordered = sorted((a, b), key=_complexity_key)
    return ordered[0], ordered[1]


def _first_witness(row: Optional[Dict[str, object]]) -> Optional[Dict[str, object]]:
    witness = row.get("first_witness") if isinstance(row, dict) else None
    return witness if isinstance(witness, dict) else None


def _parents(row: Optional[Dict[str, object]]) -> Tuple[Optional[str], Optional[Fraction], Optional[Fraction]]:
    witness = _first_witness(row)
    if witness is None:
        return None, None, None
    op_raw = witness.get("op")
    op = str(op_raw) if op_raw is not None else None
    return op, _parse_fraction(witness.get("a")), _parse_fraction(witness.get("b"))


def _is_unit_fraction(value: Fraction) -> bool:
    return value.denominator > 1 and abs(value.numerator) == 1


def _is_skeleton(value: Fraction) -> bool:
    if value in {Fraction(0, 1), Fraction(1, 1), Fraction(-1, 1)}:
        return True
    if value in {Fraction(1, 2), Fraction(-1, 2)}:
        return True
    return _is_unit_fraction(value)


def _is_nontrivial(value: Fraction, *, min_q: int) -> bool:
    if _is_skeleton(value):
        return False
    if value.denominator == 1:
        return abs(value.numerator) > 2
    return value.denominator >= min_q and abs(value.numerator) > 1


def _kind(value: Fraction) -> str:
    if value == 0:
        return "zero"
    if value.denominator == 1:
        return "integer"
    if _is_unit_fraction(value):
        return "unit_fraction"
    if value.denominator <= 5:
        return "low_q_rational"
    if value.denominator <= 25:
        return "mid_q_rational"
    if value.denominator <= 100:
        return "high_q_rational"
    return "very_high_q_rational"


def _round_relation(child_round: int, a_round: int, b_round: int) -> str:
    if a_round == child_round - 1 and b_round == child_round - 1:
        return "both_prev_round"
    if a_round == child_round - 1 or b_round == child_round - 1:
        return "one_prev_round"
    if a_round < child_round - 1 and b_round < child_round - 1:
        return "older_parents"
    return "same_parent_round"


def _edge_from_row(row: Dict[str, object], *, rows_by_frac: Dict[Fraction, Dict[str, object]]) -> Optional[Edge]:
    child = _row_fraction(row)
    op, a, b = _parents(row)
    if op is None or a is None or b is None:
        return None
    child_round = _row_int(row, "first_seen_round", -1)
    a_round = _row_int(rows_by_frac.get(a), "first_seen_round", -1)
    b_round = _row_int(rows_by_frac.get(b), "first_seen_round", -1)
    relation = _round_relation(child_round, a_round, b_round)
    motif = f"{op}:{_kind(a)}:{_kind(b)}:{relation}"
    return Edge(
        child=child,
        op=op,
        a=a,
        b=b,
        pair=_sort_pair(a, b),
        motif=motif,
        child_round=child_round,
        a_round=a_round,
        b_round=b_round,
    )


def _operation_signature(row: Optional[Dict[str, object]]) -> Dict[str, int]:
    signature = row.get("operation_signature") if isinstance(row, dict) else None
    if not isinstance(signature, dict):
        return {op: 0 for op in OPS}
    return {op: _row_int(signature, op, 0) for op in OPS}


def _operation_shares(row: Optional[Dict[str, object]]) -> Dict[str, float]:
    signature = _operation_signature(row)
    total = sum(signature.values())
    if total <= 0:
        return {op: 0.0 for op in OPS}
    return {op: signature[op] / total for op in OPS}


def _aperture_rows(report: Optional[Dict[str, object]]) -> Dict[Fraction, Dict[str, object]]:
    rows: Dict[Fraction, Dict[str, object]] = {}
    if report is None:
        return rows
    raw_rows = report.get("rows")
    if not isinstance(raw_rows, list):
        return rows
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        value = _parse_fraction(row.get("frac"))
        if value is not None:
            rows[value] = row
    return rows


def _payload_fraction(payload: object, key: str) -> Optional[Fraction]:
    if not isinstance(payload, dict):
        return None
    return _parse_fraction(payload.get(key))


def _payload_float(payload: object, key: str) -> Optional[float]:
    if not isinstance(payload, dict):
        return None
    try:
        value = payload.get(key)
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _aperture_payload(row: Optional[Dict[str, object]]) -> Dict[str, object]:
    if row is None:
        return {
            "first_witness_aperture": None,
            "aperture_excess": None,
            "aperture_ratio": None,
            "cap3_status": None,
        }
    aperture = row.get("first_witness_aperture")
    excess = row.get("aperture_excess")
    ratio = row.get("aperture_ratio")
    aperture_frac = _payload_fraction(aperture, "frac")
    excess_frac = _payload_fraction(excess, "frac")
    cap3_status = None
    cap_checks = row.get("cap_checks")
    if isinstance(cap_checks, list):
        for check in cap_checks:
            if not isinstance(check, dict):
                continue
            if str(check.get("cap_frac")) != "3":
                continue
            if not bool(check.get("final_fits_cap")):
                cap3_status = "final_outside_cap3"
            elif bool(check.get("escape_and_return")):
                cap3_status = "escape_and_return"
            elif bool(check.get("ancestry_fits_cap")):
                cap3_status = "ancestry_fits_cap3"
            else:
                cap3_status = "blocked_without_escape"
            break
    return {
        "first_witness_aperture": _format_fraction(aperture_frac) if aperture_frac is not None else None,
        "first_witness_aperture_float": _payload_float(aperture, "float"),
        "aperture_excess": _format_fraction(excess_frac) if excess_frac is not None else None,
        "aperture_excess_float": _payload_float(excess, "float"),
        "aperture_ratio": None if ratio is None else float(ratio),
        "cap3_status": cap3_status,
    }


def _rounds_from_rows(rows: Iterable[Dict[str, object]]) -> List[int]:
    rounds = {
        _row_int(row, "first_seen_round", -1)
        for row in rows
        if _row_int(row, "first_seen_round", -1) >= 0
    }
    return sorted(rounds)


def _safe_div(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return numerator / denominator


def _maybe_median(values: Iterable[float]) -> Optional[float]:
    items = [float(value) for value in values]
    if not items:
        return None
    return float(median(items))


def _counter_payload(counter: Counter, *, limit: Optional[int] = None) -> Dict[str, int]:
    items = counter.most_common(limit) if limit is not None else sorted(counter.items())
    return {str(key): int(value) for key, value in items}


def _top_values(
    values: Iterable[Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    limit: int,
) -> List[Dict[str, object]]:
    ordered = sorted(
        set(values),
        key=lambda value: (
            -_row_int(rows_by_frac.get(value), "derivation_events", 0),
            _row_int(rows_by_frac.get(value), "first_seen_round", 999999),
            _complexity_key(value),
        ),
    )
    return [
        {
            "frac": _format_fraction(value),
            "first_seen_round": _row_int(rows_by_frac.get(value), "first_seen_round", -1),
            "derivation_events": _row_int(rows_by_frac.get(value), "derivation_events", 0),
            "kind": _kind(value),
        }
        for value in ordered[:limit]
    ]


def _extract_values_from_rows(report: Optional[Dict[str, object]], key: str) -> List[Fraction]:
    values: List[Fraction] = []
    if report is None:
        return values
    rows = report.get(key)
    if not isinstance(rows, list):
        return values
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = _parse_fraction(row.get("frac"))
        if value is not None:
            values.append(value)
    return values


def _binding_values(report: Optional[Dict[str, object]]) -> List[Fraction]:
    if report is None:
        return [Fraction(value) for value in DEFAULT_BINDING_VALUES]
    values: List[Fraction] = []
    bindings = report.get("bindings")
    if not isinstance(bindings, list):
        return [Fraction(value) for value in DEFAULT_BINDING_VALUES]
    for row in bindings:
        if not isinstance(row, dict):
            continue
        probe = row.get("external_probe")
        value = _parse_fraction(probe.get("selected_speculative_node") if isinstance(probe, dict) else None)
        if value is not None:
            values.append(value)
    return values


def _binding_control_values(report: Optional[Dict[str, object]]) -> List[Fraction]:
    if report is None:
        return []
    concentration = report.get("concentration")
    if not isinstance(concentration, dict):
        return []
    controls = concentration.get("matched_controls")
    if not isinstance(controls, dict):
        return []
    rows = controls.get("values")
    if not isinstance(rows, list):
        return []
    values: List[Fraction] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = _parse_fraction(row.get("frac"))
        if value is not None:
            values.append(value)
    return values


def _source_path(path: Optional[Path]) -> Optional[str]:
    return str(path) if path is not None else None


def _build_report(config: MassConfig) -> Dict[str, object]:
    native_report = _load_report(config.native_report, require_ledger=True)
    if native_report is None:
        raise SystemExit(f"Could not read native report: {config.native_report}")
    aperture_report = _load_report(config.aperture_report)
    motif_report = _load_report(config.motif_report)
    binding_report = _load_report(config.binding_report)
    square_report = _load_report(config.square_report)
    triangle_report = _load_report(config.triangle_report)

    rows_by_frac = _rows_by_frac(native_report)
    rows = list(rows_by_frac.values())
    aperture_by_frac = _aperture_rows(aperture_report)
    rounds = _rounds_from_rows(rows)

    edges_by_child: Dict[Fraction, Edge] = {}
    motif_children: DefaultDict[str, Set[Fraction]] = defaultdict(set)
    motif_ops: DefaultDict[str, Counter] = defaultdict(Counter)
    parent_children: DefaultDict[Fraction, Set[Fraction]] = defaultdict(set)
    parent_ops: DefaultDict[Fraction, Counter] = defaultdict(Counter)
    pair_children: DefaultDict[Tuple[Fraction, Fraction], Set[Fraction]] = defaultdict(set)
    pair_ops: DefaultDict[Tuple[Fraction, Fraction], Counter] = defaultdict(Counter)

    for row in rows:
        edge = _edge_from_row(row, rows_by_frac=rows_by_frac)
        if edge is None:
            continue
        edges_by_child[edge.child] = edge
        motif_children[edge.motif].add(edge.child)
        motif_ops[edge.motif][edge.op] += 1
        parent_children[edge.a].add(edge.child)
        parent_children[edge.b].add(edge.child)
        parent_ops[edge.a][edge.op] += 1
        parent_ops[edge.b][edge.op] += 1
        pair_children[edge.pair].add(edge.child)
        pair_ops[edge.pair][edge.op] += 1

    derivation_by_value = {
        value: _row_int(row, "derivation_events", 0)
        for value, row in rows_by_frac.items()
    }
    motif_derivation_mass = {
        motif: sum(derivation_by_value.get(child, 0) for child in children)
        for motif, children in motif_children.items()
    }
    parent_derivation_mass = {
        parent: sum(derivation_by_value.get(child, 0) for child in children)
        for parent, children in parent_children.items()
    }
    pair_derivation_mass = {
        pair: sum(derivation_by_value.get(child, 0) for child in children)
        for pair, children in pair_children.items()
    }

    def parent_major_key(parent: Fraction) -> Tuple[int, int, int, Tuple[int, int, int]]:
        nontrivial_count = sum(
            1 for child in parent_children[parent] if _is_nontrivial(child, min_q=config.min_child_q)
        )
        return (
            -nontrivial_count,
            -len(parent_children[parent]),
            _row_int(rows_by_frac.get(parent), "first_seen_round", 999999),
            _complexity_key(parent),
        )

    def pair_major_key(pair: Tuple[Fraction, Fraction]) -> Tuple[int, int, int, Tuple[int, int, int], Tuple[int, int, int]]:
        return (
            -len(pair_children[pair]),
            -pair_derivation_mass.get(pair, 0),
            min(
                _row_int(rows_by_frac.get(pair[0]), "first_seen_round", 999999),
                _row_int(rows_by_frac.get(pair[1]), "first_seen_round", 999999),
            ),
            _complexity_key(pair[0]),
            _complexity_key(pair[1]),
        )

    def motif_major_key(motif: str) -> Tuple[int, int, str]:
        return (-len(motif_children[motif]), -motif_derivation_mass.get(motif, 0), motif)

    parent_candidates = [
        parent
        for parent in parent_children
        if _is_nontrivial(parent, min_q=config.min_parent_q)
    ]
    pair_candidates = [
        pair
        for pair in pair_children
        if _is_nontrivial(pair[0], min_q=config.min_parent_q)
        and _is_nontrivial(pair[1], min_q=config.min_parent_q)
    ]
    major_parents = set(sorted(parent_candidates, key=parent_major_key)[: config.major_count])
    major_pairs = set(sorted(pair_candidates, key=pair_major_key)[: config.major_count])
    major_motifs = set(sorted(motif_children.keys(), key=motif_major_key)[: config.major_count])

    def mass_row(value: Fraction) -> Dict[str, object]:
        row = rows_by_frac.get(value)
        if row is None:
            return {
                "frac": _format_fraction(value),
                "p": int(value.numerator),
                "q": int(value.denominator),
                "present": False,
            }
        edge = edges_by_child.get(value)
        aperture = _aperture_payload(aperture_by_frac.get(value))
        motif = edge.motif if edge is not None else None
        motif_mass = len(motif_children.get(motif, set())) if motif is not None else 0
        motif_deriv = motif_derivation_mass.get(motif, 0) if motif is not None else 0
        direct_parents: List[Fraction] = []
        if edge is not None:
            direct_parents = [edge.a, edge.b]
        parent_child_sum = sum(len(parent_children.get(parent, set())) for parent in direct_parents)
        parent_derivation_sum = sum(parent_derivation_mass.get(parent, 0) for parent in direct_parents)
        parent_payloads = [
            {
                "frac": _format_fraction(parent),
                "kind": _kind(parent),
                "first_seen_round": _row_int(rows_by_frac.get(parent), "first_seen_round", -1),
                "child_count": len(parent_children.get(parent, set())),
                "derivation_mass": parent_derivation_mass.get(parent, 0),
                "is_major_parent": parent in major_parents,
            }
            for parent in direct_parents
        ]
        pair = edge.pair if edge is not None else None
        return {
            "frac": _format_fraction(value),
            "p": int(value.numerator),
            "q": int(value.denominator),
            "value": float(value),
            "kind": _kind(value),
            "present": True,
            "is_skeleton": _is_skeleton(value),
            "denominator_bucket": str(row.get("denominator_bucket")),
            "first_seen_round": _row_int(row, "first_seen_round", -1),
            "derivation_events": _row_int(row, "derivation_events", 0),
            "operation_signature": _operation_signature(row),
            "operation_shares": _operation_shares(row),
            "first_witness_op": edge.op if edge is not None else None,
            "first_witness_parents": [_format_fraction(parent) for parent in direct_parents],
            "first_witness_parent_kinds": [_kind(parent) for parent in direct_parents],
            "first_witness_motif": motif,
            "motif_child_count": motif_mass,
            "motif_derivation_mass": motif_deriv,
            "local_share_of_motif_derivation_mass": _safe_div(
                float(_row_int(row, "derivation_events", 0)), float(motif_deriv)
            ),
            "direct_parent_hubs": parent_payloads,
            "direct_parent_child_count_sum": parent_child_sum,
            "direct_parent_derivation_mass_sum": parent_derivation_sum,
            "parent_pair_child_count": len(pair_children.get(pair, set())) if pair is not None else 0,
            "parent_pair_derivation_mass": pair_derivation_mass.get(pair, 0) if pair is not None else 0,
            "in_major_motif": motif in major_motifs if motif is not None else False,
            "in_major_parent": any(parent in major_parents for parent in direct_parents),
            "in_major_parent_pair": pair in major_pairs if pair is not None else False,
            **aperture,
        }

    mass_rows = {value: mass_row(value) for value in rows_by_frac}

    max_derivation_log = max((math.log1p(_row_int(row, "derivation_events", 0)) for row in rows), default=1.0)
    max_motif_log = max((math.log1p(int(row["motif_child_count"])) for row in mass_rows.values()), default=1.0)
    max_parent_log = max((math.log1p(int(row["direct_parent_child_count_sum"])) for row in mass_rows.values()), default=1.0)
    max_aperture = max(
        (
            float(row["first_witness_aperture_float"])
            for row in mass_rows.values()
            if row.get("first_witness_aperture_float") is not None
        ),
        default=1.0,
    )
    for row in mass_rows.values():
        deriv_component = math.log1p(int(row.get("derivation_events", 0))) / max_derivation_log
        motif_component = math.log1p(int(row.get("motif_child_count", 0))) / max_motif_log
        parent_component = math.log1p(int(row.get("direct_parent_child_count_sum", 0))) / max_parent_log
        aperture_float = row.get("first_witness_aperture_float")
        aperture_component = (float(aperture_float) / max_aperture) if aperture_float is not None and max_aperture else 0.0
        row["triage_mass_score"] = (deriv_component + motif_component + parent_component + aperture_component) / 4.0

    def compact(row: Dict[str, object]) -> Dict[str, object]:
        return {
            "frac": row.get("frac"),
            "first_seen_round": row.get("first_seen_round"),
            "denominator_bucket": row.get("denominator_bucket"),
            "derivation_events": row.get("derivation_events"),
            "first_witness_op": row.get("first_witness_op"),
            "first_witness_motif": row.get("first_witness_motif"),
            "motif_child_count": row.get("motif_child_count"),
            "direct_parent_child_count_sum": row.get("direct_parent_child_count_sum"),
            "first_witness_aperture": row.get("first_witness_aperture"),
            "cap3_status": row.get("cap3_status"),
            "in_major_motif": row.get("in_major_motif"),
            "in_major_parent": row.get("in_major_parent"),
            "in_major_parent_pair": row.get("in_major_parent_pair"),
            "triage_mass_score": row.get("triage_mass_score"),
        }

    def top_mass_rows(key: str, *, values: Optional[Iterable[Fraction]] = None, limit: Optional[int] = None) -> List[Dict[str, object]]:
        selected = list(values) if values is not None else list(mass_rows.keys())
        ordered = sorted(
            selected,
            key=lambda value: (
                -float(mass_rows[value].get(key, 0.0) or 0.0),
                -int(mass_rows[value].get("derivation_events", 0) or 0),
                _complexity_key(value),
            ),
        )
        return [compact(mass_rows[value]) for value in ordered[: (limit or config.top_k)]]

    def cohort_payload(name: str, values: Iterable[Fraction]) -> Dict[str, object]:
        requested = list(dict.fromkeys(values))
        present = [value for value in requested if value in mass_rows]
        present_rows = [mass_rows[value] for value in present]
        if not present_rows:
            return {
                "name": name,
                "requested_count": len(requested),
                "present_count": 0,
                "missing": [_format_fraction(value) for value in requested],
            }
        first_seen_counts = Counter(str(row.get("first_seen_round")) for row in present_rows)
        bucket_counts = Counter(str(row.get("denominator_bucket")) for row in present_rows)
        op_counts = Counter(str(row.get("first_witness_op")) for row in present_rows)
        motif_counts = Counter(str(row.get("first_witness_motif")) for row in present_rows)
        cap_counts = Counter(str(row.get("cap3_status")) for row in present_rows)
        major_motif_hits = sum(1 for row in present_rows if bool(row.get("in_major_motif")))
        major_parent_hits = sum(1 for row in present_rows if bool(row.get("in_major_parent")))
        major_pair_hits = sum(1 for row in present_rows if bool(row.get("in_major_parent_pair")))
        escape_hits = sum(1 for row in present_rows if row.get("cap3_status") == "escape_and_return")
        return {
            "name": name,
            "requested_count": len(requested),
            "present_count": len(present_rows),
            "missing": [_format_fraction(value) for value in requested if value not in mass_rows],
            "median_derivation_events": _maybe_median(
                float(row.get("derivation_events", 0) or 0) for row in present_rows
            ),
            "median_motif_child_count": _maybe_median(
                float(row.get("motif_child_count", 0) or 0) for row in present_rows
            ),
            "median_direct_parent_child_count_sum": _maybe_median(
                float(row.get("direct_parent_child_count_sum", 0) or 0) for row in present_rows
            ),
            "median_first_witness_aperture": _maybe_median(
                float(row.get("first_witness_aperture_float"))
                for row in present_rows
                if row.get("first_witness_aperture_float") is not None
            ),
            "median_triage_mass_score": _maybe_median(
                float(row.get("triage_mass_score", 0.0) or 0.0) for row in present_rows
            ),
            "major_motif_rate": major_motif_hits / len(present_rows),
            "major_parent_rate": major_parent_hits / len(present_rows),
            "major_parent_pair_rate": major_pair_hits / len(present_rows),
            "cap3_escape_and_return_rate": escape_hits / len(present_rows),
            "first_seen_counts": _counter_payload(first_seen_counts),
            "denominator_bucket_counts": _counter_payload(bucket_counts),
            "first_witness_op_counts": _counter_payload(op_counts),
            "cap3_status_counts": _counter_payload(cap_counts),
            "top_motif_counts": _counter_payload(motif_counts, limit=min(8, config.top_k)),
            "top_by_derivation_events": top_mass_rows("derivation_events", values=present, limit=min(6, config.top_k)),
            "top_by_motif_child_count": top_mass_rows("motif_child_count", values=present, limit=min(6, config.top_k)),
            "top_by_parent_hub_mass": top_mass_rows("direct_parent_child_count_sum", values=present, limit=min(6, config.top_k)),
            "top_by_triage_mass_score": top_mass_rows("triage_mass_score", values=present, limit=min(6, config.top_k)),
        }

    binding_values = _binding_values(binding_report)
    binding_controls = _binding_control_values(motif_report)
    square_values = _extract_values_from_rows(square_report, "square_rows")
    triangle_values = _extract_values_from_rows(triangle_report, "triangle_rows")
    round5_values = [value for value, row in rows_by_frac.items() if _row_int(row, "first_seen_round", -1) == 5]
    round6_values = [value for value, row in rows_by_frac.items() if _row_int(row, "first_seen_round", -1) == 6]
    aperture4_values = [
        value
        for value, row in mass_rows.items()
        if row.get("first_witness_aperture") == "4"
    ]
    cap3_escape_values = [
        value
        for value, row in mass_rows.items()
        if row.get("cap3_status") == "escape_and_return"
    ]

    cohorts = {
        "binding_probes": cohort_payload("binding_probes", binding_values),
        "binding_matched_controls": cohort_payload("binding_matched_controls", binding_controls),
        "square_family": cohort_payload("square_family", square_values),
        "triangle_family": cohort_payload("triangle_family", triangle_values),
        "round5_values": cohort_payload("round5_values", round5_values),
        "round6_values": cohort_payload("round6_values", round6_values),
        "aperture4_values": cohort_payload("aperture4_values", aperture4_values),
        "cap3_escape_and_return": cohort_payload("cap3_escape_and_return", cap3_escape_values),
        "full_corpus": cohort_payload("full_corpus", rows_by_frac.keys()),
    }

    top_motifs = [
        {
            "motif": motif,
            "child_count": len(motif_children[motif]),
            "derivation_mass": motif_derivation_mass.get(motif, 0),
            "operation_counts": {op: int(motif_ops[motif].get(op, 0)) for op in OPS},
            "top_children": _top_values(motif_children[motif], rows_by_frac=rows_by_frac, limit=min(6, config.top_k)),
        }
        for motif in sorted(motif_children.keys(), key=motif_major_key)[: config.top_k]
    ]
    top_parents = [
        {
            "frac": _format_fraction(parent),
            "kind": _kind(parent),
            "first_seen_round": _row_int(rows_by_frac.get(parent), "first_seen_round", -1),
            "child_count": len(parent_children[parent]),
            "nontrivial_child_count": sum(
                1 for child in parent_children[parent] if _is_nontrivial(child, min_q=config.min_child_q)
            ),
            "derivation_mass": parent_derivation_mass.get(parent, 0),
            "operation_counts": {op: int(parent_ops[parent].get(op, 0)) for op in OPS},
            "top_children": _top_values(parent_children[parent], rows_by_frac=rows_by_frac, limit=min(6, config.top_k)),
        }
        for parent in sorted(parent_candidates, key=parent_major_key)[: config.top_k]
    ]

    summary = {
        "value_count": len(rows_by_frac),
        "first_witness_edge_count": len(edges_by_child),
        "operation_motif_count": len(motif_children),
        "direct_parent_hub_count": len(parent_children),
        "parent_pair_count": len(pair_children),
        "rounds": [int(value) for value in rounds],
        "major_count": int(config.major_count),
        "largest_operation_motif": top_motifs[0] if top_motifs else None,
        "largest_parent_hub": top_parents[0] if top_parents else None,
        "binding_probe_comparison": {
            "binding_probe_median_motif_child_count": cohorts["binding_probes"].get("median_motif_child_count"),
            "matched_control_median_motif_child_count": cohorts["binding_matched_controls"].get("median_motif_child_count"),
            "binding_probe_major_motif_rate": cohorts["binding_probes"].get("major_motif_rate"),
            "matched_control_major_motif_rate": cohorts["binding_matched_controls"].get("major_motif_rate"),
            "binding_probe_median_aperture": cohorts["binding_probes"].get("median_first_witness_aperture"),
            "matched_control_median_aperture": cohorts["binding_matched_controls"].get("median_first_witness_aperture"),
        },
    }

    report: Dict[str, object] = {
        "schema_version": 1,
        "method": {
            "source": "Motif-mass study over saved MoO ledgers; no closure recomputation.",
            "target_blind_core": True,
            "external_probe_use": (
                "External probes only select cohort values after native rows are built. "
                "Their labels are not runtime MoO identities."
            ),
            "definitions": {
                "local_derivation_mass": "derivation_events recorded for a reduced rational value.",
                "operation_motif_mass": "number and derivation-event sum of values sharing the same first-witness operation motif.",
                "direct_parent_hub_mass": "sum of first-witness child counts and derivation-event mass for the two direct parents.",
                "aperture": "saved first-witness ancestry aperture from construction_aperture_study.py when available.",
                "triage_mass_score": (
                    "A bounded ranking helper averaging log-scaled local, motif, parent, and aperture components. "
                    "It is not a MoO-native theorem."
                ),
            },
            "limitations": [
                "Motifs are based on saved first witnesses, not every possible derivation.",
                "Construction aperture is first-witness aperture, not globally minimal aperture.",
                "Cohorts such as binding_probes are analysis-layer selections.",
            ],
        },
        "sources": {
            "native_report": str(config.native_report),
            "aperture_report": _source_path(config.aperture_report),
            "motif_report_for_controls": _source_path(config.motif_report),
            "binding_report": _source_path(config.binding_report),
            "square_report": _source_path(config.square_report),
            "triangle_report": _source_path(config.triangle_report),
        },
        "config": {
            "top_k": int(config.top_k),
            "major_count": int(config.major_count),
            "min_parent_q": int(config.min_parent_q),
            "min_child_q": int(config.min_child_q),
        },
        "summary": summary,
        "rankings": {
            "top_operation_motifs_by_child_count": top_motifs,
            "top_parent_hubs_by_child_count": top_parents,
            "top_values_by_derivation_events": top_mass_rows("derivation_events"),
            "top_values_by_motif_child_count": top_mass_rows("motif_child_count"),
            "top_values_by_parent_hub_mass": top_mass_rows("direct_parent_child_count_sum"),
            "top_values_by_triage_mass_score": top_mass_rows("triage_mass_score"),
        },
        "cohorts": cohorts,
    }
    if config.include_rows:
        report["rows"] = [mass_rows[value] for value in sorted(mass_rows, key=_complexity_key)]
    return report


def _optional_path(raw: object) -> Optional[Path]:
    text = str(raw) if raw is not None else ""
    if not text.strip():
        return None
    path = Path(text)
    if not path.exists():
        return None
    return path


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Measure MoO motif mass over saved reports without recomputing closure."
    )
    parser.add_argument("--native-report", type=str, default="out/experiments/native_r6_full.json")
    parser.add_argument("--aperture-report", type=str, default="out/experiments/construction_aperture_r6.json")
    parser.add_argument("--motif-report", type=str, default="out/experiments/motif_persistence_r6.json")
    parser.add_argument("--binding-report", type=str, default="out/experiments/binding_structure_r6.json")
    parser.add_argument("--square-report", type=str, default="out/experiments/concept_square_r6.json")
    parser.add_argument("--triangle-report", type=str, default="out/experiments/concept_triangle_r6.json")
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--major-count", type=int, default=10)
    parser.add_argument("--min-parent-q", type=int, default=3)
    parser.add_argument("--min-child-q", type=int, default=3)
    parser.add_argument("--include-rows", action="store_true", help="Include a mass row for every corpus value.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = MassConfig(
        native_report=Path(str(args.native_report)),
        aperture_report=_optional_path(args.aperture_report),
        motif_report=_optional_path(args.motif_report),
        binding_report=_optional_path(args.binding_report),
        square_report=_optional_path(args.square_report),
        triangle_report=_optional_path(args.triangle_report),
        top_k=max(1, int(args.top_k)),
        major_count=max(1, int(args.major_count)),
        min_parent_q=max(1, int(args.min_parent_q)),
        min_child_q=max(1, int(args.min_child_q)),
        include_rows=bool(args.include_rows),
    )
    payload = _build_report(config)
    text = json.dumps(payload, indent=2 if bool(args.pretty) else None, sort_keys=True) + "\n"
    if args.write is not None:
        out_path = Path(str(args.write))
        if out_path.exists():
            raise SystemExit(f"Refusing to overwrite existing file: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        return
    try:
        print(text, end="")
    except BrokenPipeError:
        raise SystemExit(0) from None


if __name__ == "__main__":
    main()
