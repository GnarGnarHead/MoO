from __future__ import annotations

import argparse
import json
import math
import signal
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple


OPS = ("+", "-", "*", "/")


@dataclass(frozen=True)
class PersistenceConfig:
    report: Path
    top_k: int
    inspect_fracs: Tuple[Fraction, ...]
    min_parent_q: int
    min_child_q: int
    major_count: int
    control_count: int
    include_skeleton: bool


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


def _row_fraction(row: Dict[str, object]) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _row_int(row: Optional[Dict[str, object]], key: str, default: int = 0) -> int:
    if row is None:
        return int(default)
    try:
        return int(row.get(key, default))
    except (TypeError, ValueError):
        return int(default)


def _complexity_key(value: Fraction) -> Tuple[int, int, int]:
    return (int(value.denominator), abs(int(value.numerator)), int(value.numerator))


def _sort_pair(a: Fraction, b: Fraction) -> Tuple[Fraction, Fraction]:
    ordered = sorted((a, b), key=_complexity_key)
    return ordered[0], ordered[1]


def _first_witness(row: Dict[str, object]) -> Optional[Dict[str, object]]:
    witness = row.get("first_witness")
    if isinstance(witness, dict):
        return witness
    return None


def _parents(row: Dict[str, object]) -> Tuple[Optional[str], Optional[Fraction], Optional[Fraction]]:
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


def _edge_from_row(
    row: Dict[str, object],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Optional[Edge]:
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


def _value_payload(value: Fraction, rows_by_frac: Dict[Fraction, Dict[str, object]]) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    return {
        "frac": _format_fraction(value),
        "p": int(value.numerator),
        "q": int(value.denominator),
        "value": float(value),
        "kind": _kind(value),
        "is_skeleton": _is_skeleton(value),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "derivation_events": _row_int(row, "derivation_events", 0),
    }


def _edge_payload(edge: Optional[Edge]) -> Optional[Dict[str, object]]:
    if edge is None:
        return None
    return {
        "child": _format_fraction(edge.child),
        "op": edge.op,
        "a": _format_fraction(edge.a),
        "b": _format_fraction(edge.b),
        "pair": [_format_fraction(edge.pair[0]), _format_fraction(edge.pair[1])],
        "motif": edge.motif,
        "child_round": int(edge.child_round),
        "a_round": int(edge.a_round),
        "b_round": int(edge.b_round),
    }


def _top_children(
    children: Iterable[Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    limit: int,
) -> List[Dict[str, object]]:
    ordered = sorted(
        set(children),
        key=lambda value: (
            -_row_int(rows_by_frac.get(value), "derivation_events", 0),
            _row_int(rows_by_frac.get(value), "first_seen_round", 999999),
            _complexity_key(value),
        ),
    )
    return [_value_payload(child, rows_by_frac) for child in ordered[:limit]]


def _rounds_from_source(source: Dict[str, object], rows: Sequence[Dict[str, object]]) -> List[int]:
    source_rounds = source.get("rounds")
    seen: Set[int] = set()
    if isinstance(source_rounds, list):
        for row in source_rounds:
            if isinstance(row, dict):
                value = _row_int(row, "round", -1)
                if value > 0:
                    seen.add(value)
    if not seen:
        for row in rows:
            value = _row_int(row, "first_seen_round", -1)
            if value > 0:
                seen.add(value)
    return sorted(seen)


def _round_counts(children: Set[Fraction], *, rows_by_frac: Dict[Fraction, Dict[str, object]], rounds: Sequence[int]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for round_idx in rounds:
        cumulative = 0
        new_children = 0
        for child in children:
            child_round = _row_int(rows_by_frac.get(child), "first_seen_round", -1)
            if child_round <= round_idx:
                cumulative += 1
            if child_round == round_idx:
                new_children += 1
        out.append(
            {
                "round": int(round_idx),
                "new_children": int(new_children),
                "cumulative_children": int(cumulative),
            }
        )
    return out


def _persistence_stats(children: Set[Fraction], *, rows_by_frac: Dict[Fraction, Dict[str, object]], rounds: Sequence[int]) -> Dict[str, object]:
    active_rounds = sorted(
        {
            _row_int(rows_by_frac.get(child), "first_seen_round", -1)
            for child in children
            if _row_int(rows_by_frac.get(child), "first_seen_round", -1) > 0
        }
    )
    if active_rounds:
        first_active = active_rounds[0]
        last_active = active_rounds[-1]
        active_span = last_active - first_active + 1
        active_ratio = len(active_rounds) / active_span if active_span > 0 else 0.0
        first_round_children = sum(
            1
            for child in children
            if _row_int(rows_by_frac.get(child), "first_seen_round", -1) <= first_active
        )
    else:
        first_active = None
        last_active = None
        active_span = 0
        active_ratio = 0.0
        first_round_children = 0
    return {
        "rounds_active": len(active_rounds),
        "active_rounds": [int(value) for value in active_rounds],
        "first_active_round": first_active,
        "last_active_round": last_active,
        "active_span": int(active_span),
        "active_ratio": float(active_ratio),
        "growth_after_first_active": max(0, len(children) - first_round_children),
        "timeline": _round_counts(children, rows_by_frac=rows_by_frac, rounds=rounds),
    }


def _parent_payload(
    parent: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    parent_children: Dict[Fraction, Set[Fraction]],
    parent_ops: Dict[Fraction, Counter],
    parent_pairs: Dict[Fraction, Counter],
    inspected: Set[Fraction],
    rounds: Sequence[int],
    min_child_q: int,
    child_limit: int,
) -> Dict[str, object]:
    children = set(parent_children.get(parent, set()))
    nontrivial_children = [
        child for child in children if _is_nontrivial(child, min_q=min_child_q)
    ]
    payload = _value_payload(parent, rows_by_frac)
    payload.update(_persistence_stats(children, rows_by_frac=rows_by_frac, rounds=rounds))
    payload.update(
        {
            "child_count": len(children),
            "nontrivial_child_count": len(nontrivial_children),
            "operation_counts": {
                op: int(parent_ops.get(parent, Counter()).get(op, 0)) for op in OPS
            },
            "paired_with_top": [
                {"frac": _format_fraction(value), "count": int(count)}
                for value, count in parent_pairs.get(parent, Counter()).most_common(8)
            ],
            "inspected_children": [
                _format_fraction(child)
                for child in sorted(children.intersection(inspected), key=_complexity_key)
            ],
            "top_children": _top_children(
                children, rows_by_frac=rows_by_frac, limit=child_limit
            ),
        }
    )
    return payload


def _pair_payload(
    pair: Tuple[Fraction, Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    pair_children: Dict[Tuple[Fraction, Fraction], Set[Fraction]],
    pair_ops: Dict[Tuple[Fraction, Fraction], Counter],
    inspected: Set[Fraction],
    rounds: Sequence[int],
    child_limit: int,
) -> Dict[str, object]:
    children = set(pair_children.get(pair, set()))
    payload: Dict[str, object] = {
        "parents": [_format_fraction(pair[0]), _format_fraction(pair[1])],
        "parent_kinds": [_kind(pair[0]), _kind(pair[1])],
        "child_count": len(children),
        "operation_counts": {
            op: int(pair_ops.get(pair, Counter()).get(op, 0)) for op in OPS
        },
        "inspected_children": [
            _format_fraction(child)
            for child in sorted(children.intersection(inspected), key=_complexity_key)
        ],
        "children": _top_children(children, rows_by_frac=rows_by_frac, limit=child_limit),
    }
    payload.update(_persistence_stats(children, rows_by_frac=rows_by_frac, rounds=rounds))
    return payload


def _motif_payload(
    motif: str,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    motif_children: Dict[str, Set[Fraction]],
    motif_ops: Dict[str, Counter],
    inspected: Set[Fraction],
    rounds: Sequence[int],
    child_limit: int,
) -> Dict[str, object]:
    children = set(motif_children.get(motif, set()))
    payload: Dict[str, object] = {
        "motif": motif,
        "child_count": len(children),
        "operation_counts": {
            op: int(motif_ops.get(motif, Counter()).get(op, 0)) for op in OPS
        },
        "inspected_children": [
            _format_fraction(child)
            for child in sorted(children.intersection(inspected), key=_complexity_key)
        ],
        "example_children": _top_children(children, rows_by_frac=rows_by_frac, limit=child_limit),
    }
    payload.update(_persistence_stats(children, rows_by_frac=rows_by_frac, rounds=rounds))
    return payload


def _candidate_controls(
    *,
    rows: Sequence[Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
    inspected: Set[Fraction],
    inspect_present: Sequence[Fraction],
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    min_child_q: int,
    control_count: int,
) -> List[Fraction]:
    if not inspect_present or control_count <= 0:
        return []

    def score(candidate: Fraction) -> Tuple[float, Tuple[int, int, int]]:
        candidate_row = rows_by_frac[candidate]
        candidate_round = _row_int(candidate_row, "first_seen_round", 999999)
        candidate_q = max(1, int(candidate.denominator))
        candidate_abs = abs(float(candidate))
        best = float("inf")
        for target in inspect_present:
            target_row = rows_by_frac[target]
            target_round = _row_int(target_row, "first_seen_round", 999999)
            target_q = max(1, int(target.denominator))
            target_abs = abs(float(target))
            value = (
                abs(candidate_round - target_round) * 1000.0
                + abs(math.log(candidate_q + 1.0) - math.log(target_q + 1.0)) * 100.0
                + abs(candidate_abs - target_abs)
            )
            best = min(best, value)
        return best, _complexity_key(candidate)

    candidates: List[Fraction] = []
    for row in rows:
        value = _row_fraction(row)
        if value in inspected or value not in edges_by_child:
            continue
        if not _is_nontrivial(value, min_q=min_child_q):
            continue
        candidates.append(value)
    return sorted(candidates, key=score)[:control_count]


def _coverage_payload(
    values: Sequence[Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
    major_parents: Set[Fraction],
    major_pairs: Set[Tuple[Fraction, Fraction]],
    major_motifs: Set[str],
) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    counts = Counter()
    for value in values:
        edge = edges_by_child.get(value)
        parent_hit = bool(edge and (edge.a in major_parents or edge.b in major_parents))
        pair_hit = bool(edge and edge.pair in major_pairs)
        motif_hit = bool(edge and edge.motif in major_motifs)
        any_hit = parent_hit or pair_hit or motif_hit
        if parent_hit:
            counts["major_parent"] += 1
        if pair_hit:
            counts["major_pair"] += 1
        if motif_hit:
            counts["major_motif"] += 1
        if any_hit:
            counts["any_major"] += 1
        payload = _value_payload(value, rows_by_frac)
        payload.update(
            {
                "first_witness_edge": _edge_payload(edge),
                "covered_by_major_parent": parent_hit,
                "covered_by_major_pair": pair_hit,
                "covered_by_major_motif": motif_hit,
                "covered_by_any_major": any_hit,
            }
        )
        rows.append(payload)
    size = len(values)
    return {
        "size": size,
        "major_parent_hits": int(counts["major_parent"]),
        "major_pair_hits": int(counts["major_pair"]),
        "major_motif_hits": int(counts["major_motif"]),
        "any_major_hits": int(counts["any_major"]),
        "major_parent_rate": counts["major_parent"] / size if size else 0.0,
        "major_pair_rate": counts["major_pair"] / size if size else 0.0,
        "major_motif_rate": counts["major_motif"] / size if size else 0.0,
        "any_major_rate": counts["any_major"] / size if size else 0.0,
        "values": rows,
    }


def motif_persistence_study(config: PersistenceConfig) -> Dict[str, object]:
    source = json.loads(config.report.read_text(encoding="utf-8"))
    if not isinstance(source, dict):
        raise SystemExit(f"Report is not a JSON object: {config.report}")
    ledger = source.get("ledger")
    if not isinstance(ledger, list):
        raise SystemExit(
            "Source report has no ledger. Build one first with: "
            "python3 native_emergence_scan.py --rounds 5 --include-ledger --write out/experiments/native_r5_full.json"
        )

    rows = [dict(row) for row in ledger if isinstance(row, dict)]
    rows_by_frac = {_row_fraction(row): row for row in rows}
    rounds = _rounds_from_source(source, rows)
    inspected = set(config.inspect_fracs)

    parent_children: DefaultDict[Fraction, Set[Fraction]] = defaultdict(set)
    parent_ops: DefaultDict[Fraction, Counter] = defaultdict(Counter)
    parent_pairs: DefaultDict[Fraction, Counter] = defaultdict(Counter)
    pair_children: DefaultDict[Tuple[Fraction, Fraction], Set[Fraction]] = defaultdict(set)
    pair_ops: DefaultDict[Tuple[Fraction, Fraction], Counter] = defaultdict(Counter)
    motif_children: DefaultDict[str, Set[Fraction]] = defaultdict(set)
    motif_ops: DefaultDict[str, Counter] = defaultdict(Counter)
    edges: List[Edge] = []
    edges_by_child: Dict[Fraction, Edge] = {}

    for row in rows:
        edge = _edge_from_row(row, rows_by_frac=rows_by_frac)
        if edge is None:
            continue
        edges.append(edge)
        edges_by_child[edge.child] = edge
        for parent, other in ((edge.a, edge.b), (edge.b, edge.a)):
            parent_children[parent].add(edge.child)
            parent_ops[parent][edge.op] += 1
            parent_pairs[parent][other] += 1
        pair_children[edge.pair].add(edge.child)
        pair_ops[edge.pair][edge.op] += 1
        motif_children[edge.motif].add(edge.child)
        motif_ops[edge.motif][edge.op] += 1

    def parent_persistence_key(parent: Fraction) -> Tuple[int, int, int, int, Tuple[int, int, int]]:
        stats = _persistence_stats(parent_children[parent], rows_by_frac=rows_by_frac, rounds=rounds)
        nontrivial_count = sum(
            1 for child in parent_children[parent] if _is_nontrivial(child, min_q=config.min_child_q)
        )
        return (
            -int(stats["rounds_active"]),
            -nontrivial_count,
            -len(parent_children[parent]),
            int(stats["first_active_round"] or 999999),
            _complexity_key(parent),
        )

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

    def pair_persistence_key(pair: Tuple[Fraction, Fraction]) -> Tuple[int, int, int, Tuple[int, int, int], Tuple[int, int, int]]:
        stats = _persistence_stats(pair_children[pair], rows_by_frac=rows_by_frac, rounds=rounds)
        return (
            -int(stats["rounds_active"]),
            -len(pair_children[pair]),
            int(stats["first_active_round"] or 999999),
            _complexity_key(pair[0]),
            _complexity_key(pair[1]),
        )

    def motif_persistence_key(motif: str) -> Tuple[int, int, int, str]:
        stats = _persistence_stats(motif_children[motif], rows_by_frac=rows_by_frac, rounds=rounds)
        inspected_count = len(motif_children[motif].intersection(inspected))
        return (
            -int(stats["rounds_active"]),
            -len(motif_children[motif]),
            -inspected_count,
            motif,
        )

    parent_candidates = list(parent_children.keys())
    if not config.include_skeleton:
        parent_candidates = [
            parent for parent in parent_candidates if _is_nontrivial(parent, min_q=config.min_parent_q)
        ]
    parent_by_persistence = sorted(parent_candidates, key=parent_persistence_key)
    parent_by_major = sorted(parent_candidates, key=parent_major_key)

    pair_candidates = list(pair_children.keys())
    if not config.include_skeleton:
        pair_candidates = [
            pair
            for pair in pair_candidates
            if _is_nontrivial(pair[0], min_q=config.min_parent_q)
            and _is_nontrivial(pair[1], min_q=config.min_parent_q)
        ]
    pair_by_persistence = sorted(pair_candidates, key=pair_persistence_key)

    motifs_by_persistence = sorted(motif_children.keys(), key=motif_persistence_key)
    motifs_by_major = sorted(
        motif_children.keys(),
        key=lambda motif: (-len(motif_children[motif]), -len(motif_children[motif].intersection(inspected)), motif),
    )

    major_parents = set(parent_by_major[: config.major_count])
    major_pairs = set(pair_by_persistence[: config.major_count])
    major_motifs = set(motifs_by_major[: config.major_count])

    inspect_present = [value for value in config.inspect_fracs if value in edges_by_child]
    controls = _candidate_controls(
        rows=rows,
        edges_by_child=edges_by_child,
        inspected=inspected,
        inspect_present=inspect_present,
        rows_by_frac=rows_by_frac,
        min_child_q=config.min_child_q,
        control_count=config.control_count,
    )

    child_limit = min(10, max(3, config.top_k))
    inspected_payload: Dict[str, object] = {}
    for value in config.inspect_fracs:
        row = rows_by_frac.get(value)
        edge = edges_by_child.get(value)
        if row is None:
            inspected_payload[_format_fraction(value)] = {"present": False}
            continue
        parent_payloads = []
        if edge is not None:
            for parent in (edge.a, edge.b):
                parent_payloads.append(
                    _parent_payload(
                        parent,
                        rows_by_frac=rows_by_frac,
                        parent_children=parent_children,
                        parent_ops=parent_ops,
                        parent_pairs=parent_pairs,
                        inspected=inspected,
                        rounds=rounds,
                        min_child_q=config.min_child_q,
                        child_limit=6,
                    )
                )
        payload = _value_payload(value, rows_by_frac)
        payload.update(
            {
                "present": True,
                "first_witness_edge": _edge_payload(edge),
                "direct_parent_hubs": parent_payloads,
                "motif_membership": (
                    _motif_payload(
                        edge.motif,
                        rows_by_frac=rows_by_frac,
                        motif_children=motif_children,
                        motif_ops=motif_ops,
                        inspected=inspected,
                        rounds=rounds,
                        child_limit=6,
                    )
                    if edge is not None
                    else None
                ),
            }
        )
        inspected_payload[_format_fraction(value)] = payload

    source_final = source.get("final") if isinstance(source.get("final"), dict) else {}
    return {
        "schema_version": 1,
        "method": {
            "source_report": str(config.report),
            "target_blind": True,
            "recomputed_closure": False,
            "graph": "saved first-witness parent graph sliced by child first_seen_round",
            "purpose": (
                "Test whether major parent hubs and operation motifs persist across "
                "round prefixes, instead of treating the final round as a one-off snapshot."
            ),
            "control_selection": (
                "Deterministic matched controls from present nontrivial ledger values, "
                "scored by first-seen round, denominator scale, and absolute value distance "
                "to inspected approximants."
            ),
        },
        "config": {
            "top_k": int(config.top_k),
            "inspect_fracs": [_format_fraction(value) for value in config.inspect_fracs],
            "min_parent_q": int(config.min_parent_q),
            "min_child_q": int(config.min_child_q),
            "major_count": int(config.major_count),
            "control_count": int(config.control_count),
            "include_skeleton": bool(config.include_skeleton),
        },
        "source_final": source_final,
        "counts": {
            "ledger_rows": len(rows),
            "rounds": [int(value) for value in rounds],
            "first_witness_edges": len(edges),
            "unique_parents": len(parent_children),
            "unique_parent_pairs": len(pair_children),
            "operation_motifs": len(motif_children),
            "nontrivial_parent_candidates": len(parent_candidates),
            "nontrivial_parent_pair_candidates": len(pair_candidates),
        },
        "major_sets": {
            "parents": [_format_fraction(value) for value in sorted(major_parents, key=parent_major_key)],
            "parent_pairs": [
                [_format_fraction(pair[0]), _format_fraction(pair[1])]
                for pair in sorted(major_pairs, key=pair_persistence_key)
            ],
            "operation_motifs": sorted(major_motifs),
        },
        "rankings": {
            "persistent_parent_hubs": [
                _parent_payload(
                    parent,
                    rows_by_frac=rows_by_frac,
                    parent_children=parent_children,
                    parent_ops=parent_ops,
                    parent_pairs=parent_pairs,
                    inspected=inspected,
                    rounds=rounds,
                    min_child_q=config.min_child_q,
                    child_limit=child_limit,
                )
                for parent in parent_by_persistence[: config.top_k]
            ],
            "final_major_parent_hubs": [
                _parent_payload(
                    parent,
                    rows_by_frac=rows_by_frac,
                    parent_children=parent_children,
                    parent_ops=parent_ops,
                    parent_pairs=parent_pairs,
                    inspected=inspected,
                    rounds=rounds,
                    min_child_q=config.min_child_q,
                    child_limit=child_limit,
                )
                for parent in parent_by_major[: config.top_k]
            ],
            "persistent_parent_pair_motifs": [
                _pair_payload(
                    pair,
                    rows_by_frac=rows_by_frac,
                    pair_children=pair_children,
                    pair_ops=pair_ops,
                    inspected=inspected,
                    rounds=rounds,
                    child_limit=child_limit,
                )
                for pair in pair_by_persistence[: config.top_k]
            ],
            "persistent_operation_motifs": [
                _motif_payload(
                    motif,
                    rows_by_frac=rows_by_frac,
                    motif_children=motif_children,
                    motif_ops=motif_ops,
                    inspected=inspected,
                    rounds=rounds,
                    child_limit=child_limit,
                )
                for motif in motifs_by_persistence[: config.top_k]
            ],
            "final_major_operation_motifs": [
                _motif_payload(
                    motif,
                    rows_by_frac=rows_by_frac,
                    motif_children=motif_children,
                    motif_ops=motif_ops,
                    inspected=inspected,
                    rounds=rounds,
                    child_limit=child_limit,
                )
                for motif in motifs_by_major[: config.top_k]
            ],
        },
        "concentration": {
            "inspected": _coverage_payload(
                inspect_present,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
                major_parents=major_parents,
                major_pairs=major_pairs,
                major_motifs=major_motifs,
            ),
            "matched_controls": _coverage_payload(
                controls,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
                major_parents=major_parents,
                major_pairs=major_pairs,
                major_motifs=major_motifs,
            ),
        },
        "inspected": inspected_payload,
    }


def _parse_inspect_fracs(raw: str) -> Tuple[Fraction, ...]:
    if not raw.strip():
        return tuple()
    out: List[Fraction] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            out.append(Fraction(text))
        except (ValueError, ZeroDivisionError) as exc:
            raise SystemExit(f"Invalid --inspect-fracs value: {text!r}") from exc
    return tuple(out)


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Study persistence of MoO first-witness parent motifs from a saved native ledger."
    )
    parser.add_argument("--report", type=str, required=True, help="native_emergence_scan.py JSON with ledger.")
    parser.add_argument("--top-k", type=int, default=12, help="Rows per ranking.")
    parser.add_argument(
        "--inspect-fracs",
        type=str,
        default="22/7,87/32,52/75,99/70,34/21",
        help="Comma-separated fractions to inspect after ranking; empty string disables.",
    )
    parser.add_argument("--min-parent-q", type=int, default=3, help="Minimum q for nontrivial rational parents.")
    parser.add_argument("--min-child-q", type=int, default=3, help="Minimum q for nontrivial rational children.")
    parser.add_argument("--major-count", type=int, default=10, help="Number of final major parents/pairs/motifs for concentration checks.")
    parser.add_argument("--control-count", type=int, default=25, help="Number of deterministic matched controls.")
    parser.add_argument("--include-skeleton", action="store_true", help="Allow arithmetic skeleton values in parent/pair rankings.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = PersistenceConfig(
        report=Path(str(args.report)),
        top_k=max(1, int(args.top_k)),
        inspect_fracs=_parse_inspect_fracs(str(args.inspect_fracs)),
        min_parent_q=max(1, int(args.min_parent_q)),
        min_child_q=max(1, int(args.min_child_q)),
        major_count=max(1, int(args.major_count)),
        control_count=max(0, int(args.control_count)),
        include_skeleton=bool(args.include_skeleton),
    )
    payload = motif_persistence_study(config)
    indent = 2 if bool(args.pretty) else None
    text = json.dumps(payload, indent=indent, sort_keys=True) + "\n"
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
