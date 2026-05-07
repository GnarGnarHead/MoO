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

from motif_mass_study import (
    Edge,
    OPS,
    _aperture_payload,
    _aperture_rows,
    _complexity_key,
    _edge_from_row,
    _format_fraction,
    _is_nontrivial,
    _is_skeleton,
    _kind,
    _load_report,
    _operation_signature,
    _parents,
    _row_fraction,
    _row_int,
    _rows_by_frac,
)


@dataclass(frozen=True)
class AtlasConfig:
    native_report: Path
    aperture_report: Optional[Path]
    top_k: int
    child_limit: int
    min_parent_q: int
    min_child_q: int


def _optional_path(raw: object) -> Optional[Path]:
    text = str(raw) if raw is not None else ""
    if not text.strip():
        return None
    path = Path(text)
    if not path.exists():
        return None
    return path


def _maybe_median(values: Iterable[float]) -> Optional[float]:
    items = [float(value) for value in values]
    if not items:
        return None
    return float(median(items))


def _counter_payload(counter: Counter, *, limit: Optional[int] = None) -> Dict[str, int]:
    items = counter.most_common(limit) if limit is not None else sorted(counter.items())
    return {str(key): int(value) for key, value in items}


def _round_counts(values: Iterable[Fraction], *, rows_by_frac: Dict[Fraction, Dict[str, object]]) -> Dict[str, int]:
    counts = Counter()
    for value in values:
        counts[str(_row_int(rows_by_frac.get(value), "first_seen_round", -1))] += 1
    return _counter_payload(counts)


def _denominator_counts(values: Iterable[Fraction], *, rows_by_frac: Dict[Fraction, Dict[str, object]]) -> Dict[str, int]:
    counts = Counter()
    for value in values:
        row = rows_by_frac.get(value)
        if row is None:
            counts["missing"] += 1
        else:
            counts[str(row.get("denominator_bucket"))] += 1
    return _counter_payload(counts)


def _kind_counts(values: Iterable[Fraction]) -> Dict[str, int]:
    return _counter_payload(Counter(_kind(value) for value in values))


def _cap3_counts(values: Iterable[Fraction], *, aperture_by_frac: Dict[Fraction, Dict[str, object]]) -> Dict[str, int]:
    counts = Counter()
    for value in values:
        payload = _aperture_payload(aperture_by_frac.get(value))
        counts[str(payload.get("cap3_status"))] += 1
    return _counter_payload(counts)


def _aperture_median(values: Iterable[Fraction], *, aperture_by_frac: Dict[Fraction, Dict[str, object]]) -> Optional[float]:
    aperture_values: List[float] = []
    for value in values:
        payload = _aperture_payload(aperture_by_frac.get(value))
        aperture = payload.get("first_witness_aperture_float")
        if aperture is not None:
            aperture_values.append(float(aperture))
    return _maybe_median(aperture_values)


def _derivation_mass(values: Iterable[Fraction], *, rows_by_frac: Dict[Fraction, Dict[str, object]]) -> int:
    return sum(_row_int(rows_by_frac.get(value), "derivation_events", 0) for value in values)


def _value_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
    aperture_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    edge = edges_by_child.get(value)
    aperture = _aperture_payload(aperture_by_frac.get(value))
    op, a, b = _parents(row)
    return {
        "frac": _format_fraction(value),
        "p": int(value.numerator),
        "q": int(value.denominator),
        "kind": _kind(value),
        "is_skeleton": _is_skeleton(value),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "denominator_bucket": str(row.get("denominator_bucket")) if row is not None else None,
        "derivation_events": _row_int(row, "derivation_events", 0),
        "operation_signature": _operation_signature(row),
        "first_witness_op": op,
        "first_witness_parents": (
            [_format_fraction(a), _format_fraction(b)]
            if a is not None and b is not None
            else []
        ),
        "first_witness_parent_kinds": (
            [_kind(a), _kind(b)]
            if a is not None and b is not None
            else []
        ),
        "first_witness_motif": edge.motif if edge is not None else None,
        "first_witness_aperture": aperture.get("first_witness_aperture"),
        "cap3_status": aperture.get("cap3_status"),
    }


def _top_values(
    values: Iterable[Fraction],
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    edges_by_child: Dict[Fraction, Edge],
    aperture_by_frac: Dict[Fraction, Dict[str, object]],
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
        _value_payload(
            value,
            rows_by_frac=rows_by_frac,
            edges_by_child=edges_by_child,
            aperture_by_frac=aperture_by_frac,
        )
        for value in ordered[:limit]
    ]


def _motif_parts(motif: str) -> Tuple[str, str, str, str]:
    parts = motif.split(":")
    if len(parts) != 4:
        return motif, "unknown", "unknown", "unknown"
    return parts[0], parts[1], parts[2], parts[3]


def _native_reading_for_motif(motif: str, child_count: int, median_aperture: Optional[float]) -> str:
    op, left, right, relation = _motif_parts(motif)
    aperture = "unknown aperture" if median_aperture is None else f"median aperture {median_aperture:g}"
    return f"{op} corridor from {left} and {right}, {relation}, {child_count} observed children, {aperture}"


def _native_reading_for_parent(value: Fraction, child_count: int, dominant_op: Optional[str]) -> str:
    op = dominant_op or "mixed"
    return f"{_kind(value)} parent hub with {child_count} observed first-witness children, dominated by {op}"


def _edge_payload(edge: Edge) -> Dict[str, object]:
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


def _build_report(config: AtlasConfig) -> Dict[str, object]:
    native_report = _load_report(config.native_report, require_ledger=True)
    if native_report is None:
        raise SystemExit(f"Could not read native report: {config.native_report}")
    aperture_report = _load_report(config.aperture_report)

    rows_by_frac = _rows_by_frac(native_report)
    rows = list(rows_by_frac.values())
    aperture_by_frac = _aperture_rows(aperture_report)

    edges_by_child: Dict[Fraction, Edge] = {}
    motif_edges: DefaultDict[str, List[Edge]] = defaultdict(list)
    motif_children: DefaultDict[str, Set[Fraction]] = defaultdict(set)
    parent_edges: DefaultDict[Fraction, List[Edge]] = defaultdict(list)
    parent_children: DefaultDict[Fraction, Set[Fraction]] = defaultdict(set)
    pair_edges: DefaultDict[Tuple[Fraction, Fraction], List[Edge]] = defaultdict(list)
    pair_children: DefaultDict[Tuple[Fraction, Fraction], Set[Fraction]] = defaultdict(set)

    for row in rows:
        edge = _edge_from_row(row, rows_by_frac=rows_by_frac)
        if edge is None:
            continue
        edges_by_child[edge.child] = edge
        motif_edges[edge.motif].append(edge)
        motif_children[edge.motif].add(edge.child)
        for parent in (edge.a, edge.b):
            parent_edges[parent].append(edge)
            parent_children[parent].add(edge.child)
        pair_edges[edge.pair].append(edge)
        pair_children[edge.pair].add(edge.child)

    motif_mass = {
        motif: _derivation_mass(children, rows_by_frac=rows_by_frac)
        for motif, children in motif_children.items()
    }
    parent_mass = {
        parent: _derivation_mass(children, rows_by_frac=rows_by_frac)
        for parent, children in parent_children.items()
    }
    pair_mass = {
        pair: _derivation_mass(children, rows_by_frac=rows_by_frac)
        for pair, children in pair_children.items()
    }

    def motif_key(motif: str) -> Tuple[int, int, str]:
        return (-len(motif_children[motif]), -motif_mass.get(motif, 0), motif)

    def motif_derivation_key(motif: str) -> Tuple[int, int, str]:
        return (-motif_mass.get(motif, 0), -len(motif_children[motif]), motif)

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

    def parent_key(parent: Fraction) -> Tuple[int, int, int, Tuple[int, int, int]]:
        nontrivial_children = sum(
            1 for child in parent_children[parent] if _is_nontrivial(child, min_q=config.min_child_q)
        )
        return (
            -nontrivial_children,
            -len(parent_children[parent]),
            _row_int(rows_by_frac.get(parent), "first_seen_round", 999999),
            _complexity_key(parent),
        )

    def pair_key(pair: Tuple[Fraction, Fraction]) -> Tuple[int, int, Tuple[int, int, int], Tuple[int, int, int]]:
        return (
            -len(pair_children[pair]),
            -pair_mass.get(pair, 0),
            _complexity_key(pair[0]),
            _complexity_key(pair[1]),
        )

    def motif_payload(motif: str) -> Dict[str, object]:
        children = set(motif_children[motif])
        edges = list(motif_edges[motif])
        parent_counter = Counter()
        pair_counter = Counter()
        for edge in edges:
            parent_counter[edge.a] += 1
            parent_counter[edge.b] += 1
            pair_counter[edge.pair] += 1
        median_aperture = _aperture_median(children, aperture_by_frac=aperture_by_frac)
        return {
            "motif": motif,
            "native_reading": _native_reading_for_motif(motif, len(children), median_aperture),
            "child_count": len(children),
            "derivation_mass": motif_mass.get(motif, 0),
            "median_child_derivation_events": _maybe_median(
                _row_int(rows_by_frac.get(child), "derivation_events", 0) for child in children
            ),
            "median_first_witness_aperture": median_aperture,
            "first_seen_counts": _round_counts(children, rows_by_frac=rows_by_frac),
            "denominator_bucket_counts": _denominator_counts(children, rows_by_frac=rows_by_frac),
            "child_kind_counts": _kind_counts(children),
            "cap3_status_counts": _cap3_counts(children, aperture_by_frac=aperture_by_frac),
            "operation_counts": _counter_payload(Counter(edge.op for edge in edges)),
            "top_local_parent_hubs": [
                {
                    "frac": _format_fraction(parent),
                    "kind": _kind(parent),
                    "first_seen_round": _row_int(rows_by_frac.get(parent), "first_seen_round", -1),
                    "local_edge_count": int(count),
                    "global_child_count": len(parent_children.get(parent, set())),
                    "global_derivation_mass": parent_mass.get(parent, 0),
                }
                for parent, count in parent_counter.most_common(config.child_limit)
            ],
            "top_local_parent_pairs": [
                {
                    "parents": [_format_fraction(pair[0]), _format_fraction(pair[1])],
                    "parent_kinds": [_kind(pair[0]), _kind(pair[1])],
                    "local_edge_count": int(count),
                    "global_child_count": len(pair_children.get(pair, set())),
                }
                for pair, count in pair_counter.most_common(min(6, config.child_limit))
            ],
            "top_children": _top_values(
                children,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
                aperture_by_frac=aperture_by_frac,
                limit=config.child_limit,
            ),
        }

    def parent_payload(parent: Fraction) -> Dict[str, object]:
        children = set(parent_children[parent])
        edges = list(parent_edges[parent])
        op_counts = Counter(edge.op for edge in edges)
        motif_counts = Counter(edge.motif for edge in edges)
        dominant = op_counts.most_common(1)[0][0] if op_counts else None
        nontrivial_children = [
            child for child in children if _is_nontrivial(child, min_q=config.min_child_q)
        ]
        return {
            "frac": _format_fraction(parent),
            "kind": _kind(parent),
            "native_reading": _native_reading_for_parent(parent, len(children), dominant),
            "first_seen_round": _row_int(rows_by_frac.get(parent), "first_seen_round", -1),
            "child_count": len(children),
            "nontrivial_child_count": len(nontrivial_children),
            "derivation_mass": parent_mass.get(parent, 0),
            "operation_counts": _counter_payload(op_counts),
            "top_motif_counts": _counter_payload(motif_counts, limit=config.child_limit),
            "first_seen_counts": _round_counts(children, rows_by_frac=rows_by_frac),
            "denominator_bucket_counts": _denominator_counts(children, rows_by_frac=rows_by_frac),
            "child_kind_counts": _kind_counts(children),
            "cap3_status_counts": _cap3_counts(children, aperture_by_frac=aperture_by_frac),
            "median_first_witness_aperture": _aperture_median(children, aperture_by_frac=aperture_by_frac),
            "top_children": _top_values(
                children,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
                aperture_by_frac=aperture_by_frac,
                limit=config.child_limit,
            ),
        }

    def pair_payload(pair: Tuple[Fraction, Fraction]) -> Dict[str, object]:
        children = set(pair_children[pair])
        edges = list(pair_edges[pair])
        op_counts = Counter(edge.op for edge in edges)
        motif_counts = Counter(edge.motif for edge in edges)
        return {
            "parents": [_format_fraction(pair[0]), _format_fraction(pair[1])],
            "parent_kinds": [_kind(pair[0]), _kind(pair[1])],
            "child_count": len(children),
            "derivation_mass": pair_mass.get(pair, 0),
            "operation_counts": _counter_payload(op_counts),
            "top_motif_counts": _counter_payload(motif_counts, limit=config.child_limit),
            "first_seen_counts": _round_counts(children, rows_by_frac=rows_by_frac),
            "cap3_status_counts": _cap3_counts(children, aperture_by_frac=aperture_by_frac),
            "median_first_witness_aperture": _aperture_median(children, aperture_by_frac=aperture_by_frac),
            "top_children": _top_values(
                children,
                rows_by_frac=rows_by_frac,
                edges_by_child=edges_by_child,
                aperture_by_frac=aperture_by_frac,
                limit=config.child_limit,
            ),
            "example_edges": [_edge_payload(edge) for edge in sorted(edges, key=lambda item: _complexity_key(item.child))[:4]],
        }

    nontrivial_values = [
        value
        for value in rows_by_frac
        if _is_nontrivial(value, min_q=config.min_child_q)
    ]

    max_deriv = max(
        (math.log1p(_row_int(rows_by_frac.get(value), "derivation_events", 0)) for value in nontrivial_values),
        default=1.0,
    )
    max_motif = max((math.log1p(len(motif_children[edge.motif])) for edge in edges_by_child.values()), default=1.0)
    max_parent = max((math.log1p(len(parent_children[parent])) for parent in parent_children), default=1.0)

    def corridor_score(value: Fraction) -> float:
        row = rows_by_frac.get(value)
        edge = edges_by_child.get(value)
        deriv_component = math.log1p(_row_int(row, "derivation_events", 0)) / max_deriv
        motif_component = 0.0
        parent_component = 0.0
        if edge is not None:
            motif_component = math.log1p(len(motif_children[edge.motif])) / max_motif
            parent_component = (
                math.log1p(len(parent_children[edge.a]) + len(parent_children[edge.b])) / max_parent
            )
        return (deriv_component + motif_component + parent_component) / 3.0

    native_high_mass_values = sorted(
        nontrivial_values,
        key=lambda value: (-_row_int(rows_by_frac.get(value), "derivation_events", 0), _complexity_key(value)),
    )[: config.top_k]
    native_high_corridor_values = sorted(
        nontrivial_values,
        key=lambda value: (-corridor_score(value), _complexity_key(value)),
    )[: config.top_k]

    top_motifs_by_child_count = sorted(motif_children.keys(), key=motif_key)[: config.top_k]
    top_motifs_by_derivation_mass = sorted(motif_children.keys(), key=motif_derivation_key)[: config.top_k]
    top_parent_hubs = sorted(parent_candidates, key=parent_key)[: config.top_k]
    top_parent_pairs = sorted(pair_candidates, key=pair_key)[: config.top_k]

    top_motif_set = set(top_motifs_by_child_count)
    shared_parent_counter = Counter()
    for motif in top_motif_set:
        for edge in motif_edges[motif]:
            shared_parent_counter[edge.a] += 1
            shared_parent_counter[edge.b] += 1

    return {
        "schema_version": 1,
        "method": {
            "source": "Blind native corridor atlas from saved first-witness ledgers.",
            "recomputed_closure": False,
            "uses_external_probe_labels": False,
            "definition": (
                "A corridor is a recurring first-witness construction region: operation motif, "
                "direct parent hub, or parent-pair channel with many observed children inside "
                "the saved ledger and/or high derivation mass."
            ),
            "iteration_scope": (
                "Observed children are values already present in the saved native report. "
                "The atlas does not score projected descendants beyond the report's iteration."
            ),
            "limitations": [
                "Uses saved first witnesses, not all possible derivations.",
                "Aperture is saved first-witness aperture when an aperture report is provided.",
                "No external labels are used, so interpretation is deliberately deferred.",
            ],
        },
        "sources": {
            "native_report": str(config.native_report),
            "aperture_report": str(config.aperture_report) if config.aperture_report is not None else None,
        },
        "config": {
            "top_k": int(config.top_k),
            "child_limit": int(config.child_limit),
            "min_parent_q": int(config.min_parent_q),
            "min_child_q": int(config.min_child_q),
        },
        "summary": {
            "value_count": len(rows_by_frac),
            "first_witness_edge_count": len(edges_by_child),
            "operation_corridor_count": len(motif_children),
            "parent_hub_count": len(parent_children),
            "parent_pair_count": len(pair_children),
            "top_operation_corridor": motif_payload(top_motifs_by_child_count[0]) if top_motifs_by_child_count else None,
            "top_parent_hub": parent_payload(top_parent_hubs[0]) if top_parent_hubs else None,
        },
        "atlas": {
            "operation_corridors_by_child_count": [motif_payload(motif) for motif in top_motifs_by_child_count],
            "operation_corridors_by_derivation_mass": [motif_payload(motif) for motif in top_motifs_by_derivation_mass],
            "parent_hub_corridors": [parent_payload(parent) for parent in top_parent_hubs],
            "parent_pair_corridors": [pair_payload(pair) for pair in top_parent_pairs],
            "shared_parent_hubs_across_top_operation_corridors": [
                {
                    "frac": _format_fraction(parent),
                    "kind": _kind(parent),
                    "first_seen_round": _row_int(rows_by_frac.get(parent), "first_seen_round", -1),
                    "local_edge_count": int(count),
                    "global_child_count": len(parent_children.get(parent, set())),
                    "global_derivation_mass": parent_mass.get(parent, 0),
                }
                for parent, count in shared_parent_counter.most_common(config.top_k)
            ],
            "native_high_mass_values": [
                _value_payload(
                    value,
                    rows_by_frac=rows_by_frac,
                    edges_by_child=edges_by_child,
                    aperture_by_frac=aperture_by_frac,
                )
                for value in native_high_mass_values
            ],
            "native_high_corridor_values": [
                {
                    **_value_payload(
                        value,
                        rows_by_frac=rows_by_frac,
                        edges_by_child=edges_by_child,
                        aperture_by_frac=aperture_by_frac,
                    ),
                    "corridor_score": corridor_score(value),
                }
                for value in native_high_corridor_values
            ],
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Build a blind MoO corridor atlas from saved reports without external labels."
    )
    parser.add_argument("--native-report", type=str, default="out/experiments/native_r6_full.json")
    parser.add_argument("--aperture-report", type=str, default="out/experiments/construction_aperture_r6.json")
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--child-limit", type=int, default=8)
    parser.add_argument("--min-parent-q", type=int, default=3)
    parser.add_argument("--min-child-q", type=int, default=3)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = AtlasConfig(
        native_report=Path(str(args.native_report)),
        aperture_report=_optional_path(args.aperture_report),
        top_k=max(1, int(args.top_k)),
        child_limit=max(1, int(args.child_limit)),
        min_parent_q=max(1, int(args.min_parent_q)),
        min_child_q=max(1, int(args.min_child_q)),
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
