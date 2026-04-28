from __future__ import annotations

import argparse
import json
import signal
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from statistics import median
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple


OPS = ("+", "-", "*", "/")


@dataclass(frozen=True)
class SaturationConfig:
    report: Path
    top_k: int
    emergence_round: Optional[int]
    saturation_round: Optional[int]
    inspect_fracs: Tuple[Fraction, ...]
    min_parent_q: int
    min_child_q: int
    child_limit: int


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


def _denominator_bucket(q: int) -> str:
    if q == 1:
        return "1"
    if q <= 5:
        return "2-5"
    if q <= 10:
        return "6-10"
    if q <= 25:
        return "11-25"
    if q <= 50:
        return "26-50"
    if q <= 100:
        return "51-100"
    return ">100"


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
        "round_relation": _round_relation(edge.child_round, edge.a_round, edge.b_round),
    }


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
        "distinct_ops": _row_int(row, "distinct_ops", 0),
    }


def _safe_stats(values: Sequence[float]) -> Dict[str, object]:
    if not values:
        return {"min": None, "median": None, "max": None}
    ordered = sorted(float(value) for value in values)
    return {
        "min": ordered[0],
        "median": float(median(ordered)),
        "max": ordered[-1],
    }


def _int_stats(values: Sequence[int]) -> Dict[str, object]:
    if not values:
        return {"min": None, "median": None, "max": None}
    ordered = sorted(int(value) for value in values)
    return {
        "min": ordered[0],
        "median": float(median(ordered)),
        "max": ordered[-1],
    }


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
    return [_value_payload(value, rows_by_frac) for value in ordered[:limit]]


def _bounded_ceiling(source: Dict[str, object]) -> Optional[int]:
    config = source.get("config")
    if not isinstance(config, dict):
        return None
    max_abs_p = _row_int(config, "max_abs_p", 0)
    max_abs_q = _row_int(config, "max_abs_q", 0)
    max_abs_value = _row_float(config, "max_abs_value", 0.0)
    if max_abs_p <= 0 or max_abs_q <= 0 or max_abs_value <= 0:
        return None
    values: Set[Fraction] = set()
    for q in range(1, max_abs_q + 1):
        for p in range(-max_abs_p, max_abs_p + 1):
            if abs(p / q) <= max_abs_value:
                values.add(Fraction(p, q))
    return len(values)


def _round_rows(source: Dict[str, object]) -> List[Dict[str, object]]:
    rounds = source.get("rounds")
    if not isinstance(rounds, list):
        return []
    return [dict(row) for row in rounds if isinstance(row, dict)]


def _cohort_payload(
    round_idx: int,
    *,
    rows: Sequence[Dict[str, object]],
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
) -> Dict[str, object]:
    cohort = [row for row in rows if _row_int(row, "first_seen_round", -1) == round_idx]
    values = [_row_fraction(row) for row in cohort]
    edges = [edges_by_child[value] for value in values if value in edges_by_child]
    op_counts = Counter(edge.op for edge in edges)
    relation_counts = Counter(
        _round_relation(edge.child_round, edge.a_round, edge.b_round) for edge in edges
    )
    parent_round_pair_counts = Counter(
        f"{min(edge.a_round, edge.b_round)},{max(edge.a_round, edge.b_round)}" for edge in edges
    )
    return {
        "round": int(round_idx),
        "size": len(cohort),
        "kind_counts": {key: int(value) for key, value in sorted(Counter(_kind(value) for value in values).items())},
        "denominator_buckets": {
            key: int(value)
            for key, value in sorted(Counter(_denominator_bucket(value.denominator) for value in values).items())
        },
        "sign_counts": {
            key: int(value)
            for key, value in sorted(
                Counter("negative" if value < 0 else "zero" if value == 0 else "positive" for value in values).items()
            )
        },
        "first_witness_operation_counts": {op: int(op_counts.get(op, 0)) for op in OPS},
        "round_relation_counts": {key: int(value) for key, value in sorted(relation_counts.items())},
        "parent_round_pair_counts": {
            key: int(value) for key, value in sorted(parent_round_pair_counts.items())
        },
        "q_stats": _int_stats([value.denominator for value in values]),
        "abs_numerator_stats": _int_stats([abs(value.numerator) for value in values]),
        "abs_value_stats": _safe_stats([abs(float(value)) for value in values]),
        "derivation_event_stats": _int_stats([_row_int(row, "derivation_events", 0) for row in cohort]),
        "top_derivation_values": _top_values(values, rows_by_frac=rows_by_frac, limit=10),
    }


def _motif_payload(
    motif: str,
    children: Set[Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    inspected: Set[Fraction],
    child_limit: int,
) -> Dict[str, object]:
    return {
        "motif": motif,
        "child_count": len(children),
        "inspected_children": [
            _format_fraction(value) for value in sorted(children.intersection(inspected), key=_complexity_key)
        ],
        "example_children": _top_values(children, rows_by_frac=rows_by_frac, limit=child_limit),
    }


def _parent_payload(
    parent: Fraction,
    children: Set[Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    inspected: Set[Fraction],
    min_child_q: int,
    child_limit: int,
) -> Dict[str, object]:
    nontrivial_children = [
        child for child in children if _is_nontrivial(child, min_q=min_child_q)
    ]
    payload = _value_payload(parent, rows_by_frac)
    payload.update(
        {
            "child_count": len(children),
            "nontrivial_child_count": len(nontrivial_children),
            "inspected_children": [
                _format_fraction(value) for value in sorted(children.intersection(inspected), key=_complexity_key)
            ],
            "top_children": _top_values(children, rows_by_frac=rows_by_frac, limit=child_limit),
        }
    )
    return payload


def _layer_rankings(
    round_idx: int,
    *,
    rows: Sequence[Dict[str, object]],
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
    inspected: Set[Fraction],
    min_parent_q: int,
    min_child_q: int,
    top_k: int,
    child_limit: int,
) -> Dict[str, object]:
    motif_children: DefaultDict[str, Set[Fraction]] = defaultdict(set)
    parent_children: DefaultDict[Fraction, Set[Fraction]] = defaultdict(set)
    pair_children: DefaultDict[Tuple[Fraction, Fraction], Set[Fraction]] = defaultdict(set)
    for row in rows:
        if _row_int(row, "first_seen_round", -1) != round_idx:
            continue
        child = _row_fraction(row)
        edge = edges_by_child.get(child)
        if edge is None:
            continue
        motif_children[edge.motif].add(child)
        for parent in (edge.a, edge.b):
            parent_children[parent].add(child)
        pair_children[edge.pair].add(child)

    def motif_key(motif: str) -> Tuple[int, int, str]:
        children = motif_children[motif]
        return (-len(children), -len(children.intersection(inspected)), motif)

    def parent_key(parent: Fraction) -> Tuple[int, int, int, Tuple[int, int, int]]:
        children = parent_children[parent]
        nontrivial_count = sum(1 for child in children if _is_nontrivial(child, min_q=min_child_q))
        return (
            -nontrivial_count,
            -len(children),
            _row_int(rows_by_frac.get(parent), "first_seen_round", 999999),
            _complexity_key(parent),
        )

    def pair_key(pair: Tuple[Fraction, Fraction]) -> Tuple[int, int, Tuple[int, int, int], Tuple[int, int, int]]:
        children = pair_children[pair]
        return (
            -len(children),
            -len(children.intersection(inspected)),
            _complexity_key(pair[0]),
            _complexity_key(pair[1]),
        )

    parent_candidates = [
        parent for parent in parent_children if _is_nontrivial(parent, min_q=min_parent_q)
    ]
    pair_candidates = [
        pair
        for pair in pair_children
        if _is_nontrivial(pair[0], min_q=min_parent_q)
        and _is_nontrivial(pair[1], min_q=min_parent_q)
    ]
    return {
        "round": int(round_idx),
        "top_motifs": [
            _motif_payload(
                motif,
                motif_children[motif],
                rows_by_frac=rows_by_frac,
                inspected=inspected,
                child_limit=child_limit,
            )
            for motif in sorted(motif_children, key=motif_key)[:top_k]
        ],
        "top_parent_hubs": [
            _parent_payload(
                parent,
                parent_children[parent],
                rows_by_frac=rows_by_frac,
                inspected=inspected,
                min_child_q=min_child_q,
                child_limit=child_limit,
            )
            for parent in sorted(parent_candidates, key=parent_key)[:top_k]
        ],
        "top_parent_pairs": [
            {
                "parents": [_format_fraction(pair[0]), _format_fraction(pair[1])],
                "parent_kinds": [_kind(pair[0]), _kind(pair[1])],
                "child_count": len(pair_children[pair]),
                "inspected_children": [
                    _format_fraction(value)
                    for value in sorted(pair_children[pair].intersection(inspected), key=_complexity_key)
                ],
                "top_children": _top_values(pair_children[pair], rows_by_frac=rows_by_frac, limit=child_limit),
            }
            for pair in sorted(pair_candidates, key=pair_key)[:top_k]
        ],
    }


def _motif_transition(
    emergence_round: int,
    saturation_round: int,
    *,
    rows: Sequence[Dict[str, object]],
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
    inspected: Set[Fraction],
    top_k: int,
    child_limit: int,
) -> Dict[str, object]:
    by_round: Dict[int, DefaultDict[str, Set[Fraction]]] = {
        emergence_round: defaultdict(set),
        saturation_round: defaultdict(set),
    }
    for row in rows:
        child_round = _row_int(row, "first_seen_round", -1)
        if child_round not in by_round:
            continue
        child = _row_fraction(row)
        edge = edges_by_child.get(child)
        if edge is not None:
            by_round[child_round][edge.motif].add(child)

    emergence_motifs = set(by_round[emergence_round])
    saturation_motifs = set(by_round[saturation_round])
    shared = emergence_motifs.intersection(saturation_motifs)
    saturation_only = saturation_motifs - emergence_motifs
    emergence_only = emergence_motifs - saturation_motifs

    def transition_payload(motif: str) -> Dict[str, object]:
        emergence_children = by_round[emergence_round].get(motif, set())
        saturation_children = by_round[saturation_round].get(motif, set())
        return {
            "motif": motif,
            "emergence_count": len(emergence_children),
            "saturation_count": len(saturation_children),
            "growth": len(saturation_children) - len(emergence_children),
            "inspected_children": [
                _format_fraction(value)
                for value in sorted(
                    emergence_children.union(saturation_children).intersection(inspected),
                    key=_complexity_key,
                )
            ],
            "saturation_examples": _top_values(
                saturation_children, rows_by_frac=rows_by_frac, limit=child_limit
            ),
        }

    shared_rows = sorted(
        [transition_payload(motif) for motif in shared],
        key=lambda row: (-int(row["saturation_count"]), -int(row["growth"]), str(row["motif"])),
    )
    saturation_only_rows = sorted(
        [transition_payload(motif) for motif in saturation_only],
        key=lambda row: (-int(row["saturation_count"]), str(row["motif"])),
    )
    emergence_only_rows = sorted(
        [transition_payload(motif) for motif in emergence_only],
        key=lambda row: (-int(row["emergence_count"]), str(row["motif"])),
    )
    return {
        "emergence_round": int(emergence_round),
        "saturation_round": int(saturation_round),
        "emergence_motif_count": len(emergence_motifs),
        "saturation_motif_count": len(saturation_motifs),
        "shared_motif_count": len(shared),
        "saturation_only_motif_count": len(saturation_only),
        "emergence_only_motif_count": len(emergence_only),
        "top_shared_motifs": shared_rows[:top_k],
        "top_saturation_only_motifs": saturation_only_rows[:top_k],
        "top_emergence_only_motifs": emergence_only_rows[:top_k],
    }


def _inspected_payload(
    inspect_fracs: Sequence[Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
    emergence_round: int,
    saturation_round: int,
) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for value in inspect_fracs:
        row = rows_by_frac.get(value)
        if row is None:
            out[_format_fraction(value)] = {"present": False}
            continue
        first_seen = _row_int(row, "first_seen_round", -1)
        if first_seen == emergence_round:
            layer = "emergence"
        elif first_seen == saturation_round:
            layer = "saturation"
        elif first_seen < emergence_round:
            layer = "pre_emergence"
        else:
            layer = "other"
        payload = _value_payload(value, rows_by_frac)
        payload.update(
            {
                "present": True,
                "layer": layer,
                "first_witness_edge": _edge_payload(edges_by_child.get(value)),
            }
        )
        out[_format_fraction(value)] = payload
    return out


def saturation_layer_study(config: SaturationConfig) -> Dict[str, object]:
    source = json.loads(config.report.read_text(encoding="utf-8"))
    if not isinstance(source, dict):
        raise SystemExit(f"Report is not a JSON object: {config.report}")
    ledger = source.get("ledger")
    if not isinstance(ledger, list):
        raise SystemExit(
            "Source report has no ledger. Build one first with: "
            "python3 native_emergence_scan.py --rounds 6 --include-ledger --write out/experiments/native_r6_full.json"
        )
    rows = [dict(row) for row in ledger if isinstance(row, dict)]
    rows_by_frac = {_row_fraction(row): row for row in rows}
    edges_by_child: Dict[Fraction, Edge] = {}
    for row in rows:
        edge = _edge_from_row(row, rows_by_frac=rows_by_frac)
        if edge is not None:
            edges_by_child[edge.child] = edge

    source_final = source.get("final") if isinstance(source.get("final"), dict) else {}
    max_round = _row_int(source_final, "max_round_completed", 0)
    saturation_round = config.saturation_round if config.saturation_round is not None else max_round
    emergence_round = (
        config.emergence_round
        if config.emergence_round is not None
        else max(0, int(saturation_round) - 1)
    )
    inspected = set(config.inspect_fracs)
    ceiling = _bounded_ceiling(source)
    final_size = _row_int(source_final, "size", len(rows))

    return {
        "schema_version": 1,
        "method": {
            "source_report": str(config.report),
            "target_blind": True,
            "recomputed_closure": False,
            "purpose": (
                "Compare the penultimate emergence layer with the final saturated "
                "layer in a saved bounded MoO corpus."
            ),
        },
        "config": {
            "top_k": int(config.top_k),
            "emergence_round": int(emergence_round),
            "saturation_round": int(saturation_round),
            "inspect_fracs": [_format_fraction(value) for value in config.inspect_fracs],
            "min_parent_q": int(config.min_parent_q),
            "min_child_q": int(config.min_child_q),
            "child_limit": int(config.child_limit),
        },
        "source_final": source_final,
        "bounded_ceiling": ceiling,
        "saturated": bool(ceiling is not None and final_size == ceiling),
        "rounds": _round_rows(source),
        "cohorts": {
            str(emergence_round): _cohort_payload(
                int(emergence_round),
                rows=rows,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
            ),
            str(saturation_round): _cohort_payload(
                int(saturation_round),
                rows=rows,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
            ),
        },
        "rankings": {
            str(emergence_round): _layer_rankings(
                int(emergence_round),
                rows=rows,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
                inspected=inspected,
                min_parent_q=config.min_parent_q,
                min_child_q=config.min_child_q,
                top_k=config.top_k,
                child_limit=config.child_limit,
            ),
            str(saturation_round): _layer_rankings(
                int(saturation_round),
                rows=rows,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
                inspected=inspected,
                min_parent_q=config.min_parent_q,
                min_child_q=config.min_child_q,
                top_k=config.top_k,
                child_limit=config.child_limit,
            ),
        },
        "motif_transition": _motif_transition(
            int(emergence_round),
            int(saturation_round),
            rows=rows,
            rows_by_frac=rows_by_frac,
            edges_by_child=edges_by_child,
            inspected=inspected,
            top_k=config.top_k,
            child_limit=config.child_limit,
        ),
        "inspected": _inspected_payload(
            config.inspect_fracs,
            rows_by_frac=rows_by_frac,
            edges_by_child=edges_by_child,
            emergence_round=int(emergence_round),
            saturation_round=int(saturation_round),
        ),
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
        description="Compare emergence and saturation layers in a saved MoO native ledger."
    )
    parser.add_argument("--report", type=str, required=True, help="native_emergence_scan.py JSON with ledger.")
    parser.add_argument("--top-k", type=int, default=12, help="Rows per ranking.")
    parser.add_argument("--emergence-round", type=int, default=None, help="Penultimate layer; defaults to max_round-1.")
    parser.add_argument("--saturation-round", type=int, default=None, help="Final layer; defaults to source max round.")
    parser.add_argument(
        "--inspect-fracs",
        type=str,
        default="22/7,87/32,52/75,99/70,34/21",
        help="Comma-separated fractions to inspect after ranking; empty string disables.",
    )
    parser.add_argument("--min-parent-q", type=int, default=3, help="Minimum q for nontrivial rational parents.")
    parser.add_argument("--min-child-q", type=int, default=3, help="Minimum q for nontrivial rational children.")
    parser.add_argument("--child-limit", type=int, default=6, help="Example children per ranking row.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = SaturationConfig(
        report=Path(str(args.report)),
        top_k=max(1, int(args.top_k)),
        emergence_round=int(args.emergence_round) if args.emergence_round is not None else None,
        saturation_round=int(args.saturation_round) if args.saturation_round is not None else None,
        inspect_fracs=_parse_inspect_fracs(str(args.inspect_fracs)),
        min_parent_q=max(1, int(args.min_parent_q)),
        min_child_q=max(1, int(args.min_child_q)),
        child_limit=max(1, int(args.child_limit)),
    )
    payload = saturation_layer_study(config)
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
