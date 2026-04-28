from __future__ import annotations

import argparse
import json
import signal
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class MotifConfig:
    report: Path
    top_k: int
    inspect_fracs: Tuple[Fraction, ...]
    ancestor_depth: int
    min_parent_q: int
    min_child_q: int
    include_skeleton: bool


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
    return tuple(sorted((a, b), key=_complexity_key))  # type: ignore[return-value]


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


def _value_payload(value: Fraction, rows_by_frac: Dict[Fraction, Dict[str, object]]) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    return {
        "frac": _format_fraction(value),
        "p": int(value.numerator),
        "q": int(value.denominator),
        "value": float(value),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "derivation_events": _row_int(row, "derivation_events", 0),
    }


def _child_summary(
    child: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(child, {})
    op, a, b = _parents(row)
    payload = _value_payload(child, rows_by_frac)
    payload.update(
        {
            "first_witness": row.get("first_witness"),
            "op": op,
            "parents": [
                _format_fraction(parent) for parent in (a, b) if parent is not None
            ],
        }
    )
    return payload


def _ancestry(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    depth: int,
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    payload = _value_payload(value, rows_by_frac)
    if row is None:
        payload["missing"] = True
        return payload
    payload["first_witness"] = row.get("first_witness")
    if depth <= 0:
        return payload
    _, a, b = _parents(row)
    parents = []
    for parent in (a, b):
        if parent is not None:
            parents.append(_ancestry(parent, rows_by_frac=rows_by_frac, depth=depth - 1))
    if parents:
        payload["parents"] = parents
    return payload


def _ancestor_set(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    depth: int,
) -> Set[Fraction]:
    if depth <= 0:
        return set()
    row = rows_by_frac.get(value)
    if row is None:
        return set()
    _, a, b = _parents(row)
    out: Set[Fraction] = set()
    for parent in (a, b):
        if parent is None:
            continue
        out.add(parent)
        out.update(_ancestor_set(parent, rows_by_frac=rows_by_frac, depth=depth - 1))
    return out


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
    return [_child_summary(child, rows_by_frac=rows_by_frac) for child in ordered[:limit]]


def _parent_hub_payload(
    parent: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    parent_children: Dict[Fraction, Set[Fraction]],
    parent_ops: Dict[Fraction, Counter],
    parent_pairs: Dict[Fraction, Counter],
    inspected: Set[Fraction],
    min_child_q: int,
    child_limit: int,
) -> Dict[str, object]:
    children = parent_children.get(parent, set())
    inspected_children = sorted(children.intersection(inspected), key=_complexity_key)
    nontrivial_children = [
        child for child in children if _is_nontrivial(child, min_q=min_child_q)
    ]
    paired_with = [
        {"frac": _format_fraction(value), "count": int(count)}
        for value, count in parent_pairs.get(parent, Counter()).most_common(8)
    ]
    payload = _value_payload(parent, rows_by_frac)
    payload.update(
        {
            "kind": _kind(parent),
            "is_skeleton": _is_skeleton(parent),
            "child_count": len(children),
            "nontrivial_child_count": len(nontrivial_children),
            "operation_counts": {
                op: int(parent_ops.get(parent, Counter()).get(op, 0)) for op in ["+", "-", "*", "/"]
            },
            "paired_with_top": paired_with,
            "inspected_children": [_format_fraction(child) for child in inspected_children],
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
    child_limit: int,
) -> Dict[str, object]:
    children = pair_children.get(pair, set())
    inspected_children = sorted(children.intersection(inspected), key=_complexity_key)
    return {
        "parents": [_format_fraction(pair[0]), _format_fraction(pair[1])],
        "parent_kinds": [_kind(pair[0]), _kind(pair[1])],
        "child_count": len(children),
        "operation_counts": {
            op: int(pair_ops.get(pair, Counter()).get(op, 0)) for op in ["+", "-", "*", "/"]
        },
        "inspected_children": [_format_fraction(child) for child in inspected_children],
        "children": _top_children(children, rows_by_frac=rows_by_frac, limit=child_limit),
    }


def motif_graph_study(config: MotifConfig) -> Dict[str, object]:
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
    inspected = set(config.inspect_fracs)

    parent_children: DefaultDict[Fraction, Set[Fraction]] = defaultdict(set)
    parent_ops: DefaultDict[Fraction, Counter] = defaultdict(Counter)
    parent_pairs: DefaultDict[Fraction, Counter] = defaultdict(Counter)
    pair_children: DefaultDict[Tuple[Fraction, Fraction], Set[Fraction]] = defaultdict(set)
    pair_ops: DefaultDict[Tuple[Fraction, Fraction], Counter] = defaultdict(Counter)
    operation_motifs: DefaultDict[str, Set[Fraction]] = defaultdict(set)
    operation_motif_ops: DefaultDict[str, Counter] = defaultdict(Counter)
    edges: List[Dict[str, object]] = []

    for row in rows:
        child = _row_fraction(row)
        op, a, b = _parents(row)
        if op is None or a is None or b is None:
            continue
        pair = _sort_pair(a, b)
        for parent, other in ((a, b), (b, a)):
            parent_children[parent].add(child)
            parent_ops[parent][op] += 1
            parent_pairs[parent][other] += 1
        pair_children[pair].add(child)
        pair_ops[pair][op] += 1

        round_relation = "same_parent_round"
        a_round = _row_int(rows_by_frac.get(a), "first_seen_round", -1)
        b_round = _row_int(rows_by_frac.get(b), "first_seen_round", -1)
        child_round = _row_int(row, "first_seen_round", -1)
        if a_round == child_round - 1 and b_round == child_round - 1:
            round_relation = "both_prev_round"
        elif a_round == child_round - 1 or b_round == child_round - 1:
            round_relation = "one_prev_round"
        elif a_round < child_round - 1 and b_round < child_round - 1:
            round_relation = "older_parents"
        motif = f"{op}:{_kind(a)}:{_kind(b)}:{round_relation}"
        operation_motifs[motif].add(child)
        operation_motif_ops[motif][op] += 1
        edges.append(
            {
                "child": child,
                "op": op,
                "a": a,
                "b": b,
                "child_round": child_round,
                "a_round": a_round,
                "b_round": b_round,
                "motif": motif,
            }
        )

    def parent_hub_key(parent: Fraction) -> Tuple[int, int, int, Tuple[int, int, int]]:
        children = parent_children.get(parent, set())
        nontrivial_count = sum(
            1 for child in children if _is_nontrivial(child, min_q=config.min_child_q)
        )
        return (
            -len(children),
            -nontrivial_count,
            _row_int(rows_by_frac.get(parent), "first_seen_round", 999999),
            _complexity_key(parent),
        )

    def nontrivial_parent_hub_key(parent: Fraction) -> Tuple[int, int, Tuple[int, int, int]]:
        children = parent_children.get(parent, set())
        nontrivial_count = sum(
            1 for child in children if _is_nontrivial(child, min_q=config.min_child_q)
        )
        return (
            -nontrivial_count,
            -len(children),
            _complexity_key(parent),
        )

    def pair_key(pair: Tuple[Fraction, Fraction]) -> Tuple[int, int, Tuple[int, int, int], Tuple[int, int, int]]:
        children = pair_children.get(pair, set())
        inspected_count = len(children.intersection(inspected))
        return (
            -len(children),
            -inspected_count,
            _complexity_key(pair[0]),
            _complexity_key(pair[1]),
        )

    def motif_key(motif: str) -> Tuple[int, int, str]:
        children = operation_motifs.get(motif, set())
        inspected_count = len(children.intersection(inspected))
        return (-len(children), -inspected_count, motif)

    parent_candidates = sorted(parent_children.keys(), key=parent_hub_key)
    if not config.include_skeleton:
        nontrivial_parent_candidates = [
            parent
            for parent in parent_children
            if _is_nontrivial(parent, min_q=config.min_parent_q)
        ]
    else:
        nontrivial_parent_candidates = list(parent_children.keys())
    nontrivial_parent_candidates = sorted(nontrivial_parent_candidates, key=nontrivial_parent_hub_key)

    pair_candidates = sorted(pair_children.keys(), key=pair_key)
    nontrivial_pair_candidates = [
        pair
        for pair in pair_candidates
        if config.include_skeleton
        or (
            _is_nontrivial(pair[0], min_q=config.min_parent_q)
            and _is_nontrivial(pair[1], min_q=config.min_parent_q)
        )
    ]

    parent_child_limit = min(10, max(3, config.top_k))
    parent_hubs = [
        _parent_hub_payload(
            parent,
            rows_by_frac=rows_by_frac,
            parent_children=parent_children,
            parent_ops=parent_ops,
            parent_pairs=parent_pairs,
            inspected=inspected,
            min_child_q=config.min_child_q,
            child_limit=parent_child_limit,
        )
        for parent in parent_candidates[: config.top_k]
    ]
    nontrivial_parent_hubs = [
        _parent_hub_payload(
            parent,
            rows_by_frac=rows_by_frac,
            parent_children=parent_children,
            parent_ops=parent_ops,
            parent_pairs=parent_pairs,
            inspected=inspected,
            min_child_q=config.min_child_q,
            child_limit=parent_child_limit,
        )
        for parent in nontrivial_parent_candidates[: config.top_k]
    ]

    parent_pair_motifs = [
        _pair_payload(
            pair,
            rows_by_frac=rows_by_frac,
            pair_children=pair_children,
            pair_ops=pair_ops,
            inspected=inspected,
            child_limit=parent_child_limit,
        )
        for pair in pair_candidates[: config.top_k]
    ]
    nontrivial_pair_motifs = [
        _pair_payload(
            pair,
            rows_by_frac=rows_by_frac,
            pair_children=pair_children,
            pair_ops=pair_ops,
            inspected=inspected,
            child_limit=parent_child_limit,
        )
        for pair in nontrivial_pair_candidates[: config.top_k]
    ]

    operation_motif_payloads: List[Dict[str, object]] = []
    for motif in sorted(operation_motifs, key=motif_key)[: config.top_k]:
        children = operation_motifs[motif]
        operation_motif_payloads.append(
            {
                "motif": motif,
                "child_count": len(children),
                "operation_counts": {
                    op: int(operation_motif_ops[motif].get(op, 0)) for op in ["+", "-", "*", "/"]
                },
                "inspected_children": [
                    _format_fraction(child) for child in sorted(children.intersection(inspected), key=_complexity_key)
                ],
                "example_children": _top_children(
                    children, rows_by_frac=rows_by_frac, limit=parent_child_limit
                ),
            }
        )

    inspected_payload: Dict[str, object] = {}
    ancestor_sets: Dict[Fraction, Set[Fraction]] = {}
    for value in config.inspect_fracs:
        row = rows_by_frac.get(value)
        if row is None:
            inspected_payload[_format_fraction(value)] = {"present": False}
            continue
        ancestors = _ancestor_set(value, rows_by_frac=rows_by_frac, depth=config.ancestor_depth)
        ancestor_sets[value] = ancestors
        op, a, b = _parents(row)
        parent_payloads = []
        for parent in (a, b):
            if parent is None:
                continue
            parent_payloads.append(
                _parent_hub_payload(
                    parent,
                    rows_by_frac=rows_by_frac,
                    parent_children=parent_children,
                    parent_ops=parent_ops,
                    parent_pairs=parent_pairs,
                    inspected=inspected,
                    min_child_q=config.min_child_q,
                    child_limit=6,
                )
            )
        inspected_payload[_format_fraction(value)] = {
            "present": True,
            "child": _child_summary(value, rows_by_frac=rows_by_frac),
            "ancestry": _ancestry(value, rows_by_frac=rows_by_frac, depth=config.ancestor_depth),
            "direct_parent_hubs": parent_payloads,
            "ancestor_count": len(ancestors),
            "nontrivial_ancestors": [
                _value_payload(parent, rows_by_frac)
                for parent in sorted(
                    [p for p in ancestors if _is_nontrivial(p, min_q=config.min_parent_q)],
                    key=_complexity_key,
                )
            ],
        }

    ancestor_to_inspected: DefaultDict[Fraction, List[Fraction]] = defaultdict(list)
    for target, ancestors in ancestor_sets.items():
        for ancestor in ancestors:
            ancestor_to_inspected[ancestor].append(target)

    common_ancestors: List[Dict[str, object]] = []
    for ancestor, targets in ancestor_to_inspected.items():
        if len(targets) < 2:
            continue
        if not config.include_skeleton and not _is_nontrivial(ancestor, min_q=config.min_parent_q):
            continue
        payload = _value_payload(ancestor, rows_by_frac)
        payload.update(
            {
                "inspected_descendants": [
                    _format_fraction(target) for target in sorted(targets, key=_complexity_key)
                ],
                "child_count": len(parent_children.get(ancestor, set())),
                "nontrivial_child_count": sum(
                    1
                    for child in parent_children.get(ancestor, set())
                    if _is_nontrivial(child, min_q=config.min_child_q)
                ),
                "operation_counts": {
                    op: int(parent_ops.get(ancestor, Counter()).get(op, 0))
                    for op in ["+", "-", "*", "/"]
                },
            }
        )
        common_ancestors.append(payload)
    common_ancestors.sort(
        key=lambda row: (
            -len(row.get("inspected_descendants", [])),
            -int(row.get("child_count", 0)),
            _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
        )
    )

    shared_parent_pairs: List[Dict[str, object]] = []
    for pair, children in pair_children.items():
        inspected_children = children.intersection(inspected)
        if not inspected_children:
            continue
        shared_parent_pairs.append(
            _pair_payload(
                pair,
                rows_by_frac=rows_by_frac,
                pair_children=pair_children,
                pair_ops=pair_ops,
                inspected=inspected,
                child_limit=parent_child_limit,
            )
        )
    shared_parent_pairs.sort(key=lambda row: (-len(row["inspected_children"]), -int(row["child_count"])))

    source_final = source.get("final") if isinstance(source.get("final"), dict) else {}
    return {
        "schema_version": 1,
        "method": {
            "source_report": str(config.report),
            "target_blind": True,
            "recomputed_closure": False,
            "graph": "first-witness parent graph",
            "purpose": (
                "Find reusable construction scaffolds and check whether inspected "
                "attractor approximants sit downstream of shared motifs."
            ),
        },
        "config": {
            "top_k": int(config.top_k),
            "inspect_fracs": [_format_fraction(value) for value in config.inspect_fracs],
            "ancestor_depth": int(config.ancestor_depth),
            "min_parent_q": int(config.min_parent_q),
            "min_child_q": int(config.min_child_q),
            "include_skeleton": bool(config.include_skeleton),
        },
        "source_final": source_final,
        "counts": {
            "ledger_rows": len(rows),
            "first_witness_edges": len(edges),
            "unique_parents": len(parent_children),
            "unique_parent_pairs": len(pair_children),
            "operation_motifs": len(operation_motifs),
        },
        "rankings": {
            "parent_hubs": parent_hubs,
            "nontrivial_parent_hubs": nontrivial_parent_hubs,
            "parent_pair_motifs": parent_pair_motifs,
            "nontrivial_parent_pair_motifs": nontrivial_pair_motifs,
            "operation_motifs": operation_motif_payloads,
            "shared_parent_pairs_for_inspected": shared_parent_pairs[: config.top_k],
            "common_ancestors_for_inspected": common_ancestors[: config.top_k],
        },
        "inspected": inspected_payload,
    }


def _parse_inspect_fracs(raw: str) -> Tuple[Fraction, ...]:
    out: List[Fraction] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            out.append(Fraction(text))
        except (ValueError, ZeroDivisionError) as exc:
            raise SystemExit(f"Invalid fraction in --inspect-fracs: {text!r}") from exc
    return tuple(out)


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Study first-witness parent motifs from a saved MoO native ledger."
    )
    parser.add_argument("--report", type=str, required=True, help="native_emergence_scan.py JSON with ledger.")
    parser.add_argument("--top-k", type=int, default=20, help="Rows per ranking.")
    parser.add_argument(
        "--inspect-fracs",
        type=str,
        default="22/7,87/32,52/75,99/70,34/21",
        help="Comma-separated fractions to inspect as downstream approximants.",
    )
    parser.add_argument("--ancestor-depth", type=int, default=3, help="Depth for inspected ancestry overlap.")
    parser.add_argument("--min-parent-q", type=int, default=3, help="Minimum q for nontrivial parent filtering.")
    parser.add_argument("--min-child-q", type=int, default=3, help="Minimum q for nontrivial child counting.")
    parser.add_argument("--include-skeleton", action="store_true", help="Include skeleton/unit-fraction motifs.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = MotifConfig(
        report=Path(str(args.report)),
        top_k=max(1, int(args.top_k)),
        inspect_fracs=_parse_inspect_fracs(str(args.inspect_fracs)),
        ancestor_depth=max(1, int(args.ancestor_depth)),
        min_parent_q=max(1, int(args.min_parent_q)),
        min_child_q=max(1, int(args.min_child_q)),
        include_skeleton=bool(args.include_skeleton),
    )
    payload = motif_graph_study(config)
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
