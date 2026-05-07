from __future__ import annotations

import argparse
import json
import signal
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from moo_set_closure import bounded, complexity_key


Witness = Tuple[str, Fraction, Fraction]


@dataclass(frozen=True)
class NativeScanConfig:
    rounds: int
    max_abs_p: int
    max_abs_q: int
    max_abs_value: Optional[float]
    top_k: int
    include_ledger: bool
    ancestry_depth: int


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(int(value.numerator))
    return f"{int(value.numerator)}/{int(value.denominator)}"


def _format_gap(value: Optional[Fraction]) -> Optional[Dict[str, object]]:
    if value is None:
        return None
    return {"frac": _format_fraction(value), "float": float(value)}


def _witness_payload(witness: Optional[Witness]) -> Optional[Dict[str, object]]:
    if witness is None:
        return None
    op, a, b = witness
    return {
        "op": op,
        "a": _format_fraction(a),
        "b": _format_fraction(b),
        "expr": f"{_format_fraction(a)} {op} {_format_fraction(b)}",
    }


def _candidate_events(a: Fraction, b: Fraction) -> List[Tuple[str, Fraction, Fraction, Fraction]]:
    events = [
        ("+", a, b, a + b),
        ("*", a, b, a * b),
        ("-", a, b, a - b),
        ("-", b, a, b - a),
    ]
    if b != 0:
        events.append(("/", a, b, a / b))
    if a != 0:
        events.append(("/", b, a, b / a))
    return events


def _neighbor_map(values: Iterable[Fraction]) -> Dict[Fraction, Dict[str, object]]:
    ordered = sorted(values)
    out: Dict[Fraction, Dict[str, object]] = {}
    for idx, value in enumerate(ordered):
        left = ordered[idx - 1] if idx > 0 else None
        right = ordered[idx + 1] if idx + 1 < len(ordered) else None
        left_gap = value - left if left is not None else None
        right_gap = right - value if right is not None else None
        gaps = [gap for gap in (left_gap, right_gap) if gap is not None]
        min_gap = min(gaps) if gaps else None
        out[value] = {
            "left": _format_fraction(left) if left is not None else None,
            "right": _format_fraction(right) if right is not None else None,
            "left_gap": _format_gap(left_gap),
            "right_gap": _format_gap(right_gap),
            "min_gap": _format_gap(min_gap),
        }
    return out


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


def _ancestry_payload(
    value: Fraction,
    *,
    first_seen: Dict[Fraction, int],
    first_witness: Dict[Fraction, Optional[Witness]],
    depth: int,
) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "frac": _format_fraction(value),
        "first_seen_round": int(first_seen.get(value, -1)),
    }
    witness = first_witness.get(value)
    payload["first_witness"] = _witness_payload(witness)
    if depth <= 0 or witness is None:
        return payload
    _, a, b = witness
    payload["parents"] = [
        _ancestry_payload(a, first_seen=first_seen, first_witness=first_witness, depth=depth - 1),
        _ancestry_payload(b, first_seen=first_seen, first_witness=first_witness, depth=depth - 1),
    ]
    return payload


def _value_payload(
    value: Fraction,
    *,
    first_seen: Dict[Fraction, int],
    first_witness: Dict[Fraction, Optional[Witness]],
    derivation_counts: Dict[Fraction, int],
    op_counts: Dict[Fraction, Counter],
    neighbors: Dict[Fraction, Dict[str, object]],
    ancestry_depth: int = 0,
) -> Dict[str, object]:
    ops = op_counts.get(value, Counter())
    p = int(value.numerator)
    q = int(value.denominator)
    payload: Dict[str, object] = {
        "frac": _format_fraction(value),
        "p": p,
        "q": q,
        "value": float(value),
        "first_seen_round": int(first_seen.get(value, -1)),
        "first_witness": _witness_payload(first_witness.get(value)),
        "derivation_events": int(derivation_counts.get(value, 0)),
        "operation_signature": {op: int(ops.get(op, 0)) for op in ["+", "-", "*", "/"]},
        "distinct_ops": sum(1 for op in ["+", "-", "*", "/"] if ops.get(op, 0) > 0),
        "is_integer": q == 1,
        "abs_numerator": abs(p),
        "denominator_bucket": _denominator_bucket(q),
        "neighbors": neighbors.get(value),
    }
    if ancestry_depth > 0:
        payload["ancestry"] = _ancestry_payload(
            value, first_seen=first_seen, first_witness=first_witness, depth=ancestry_depth
        )
    return payload


def _top_values(
    values: Iterable[Fraction],
    *,
    top_k: int,
    key,
    payload,
) -> List[Dict[str, object]]:
    ordered = sorted(values, key=key)
    return [payload(value) for value in ordered[: max(0, int(top_k))]]


def native_emergence_scan(config: NativeScanConfig) -> Dict[str, object]:
    one = Fraction(1, 1)
    s_prev: Set[Fraction] = {one}
    delta_prev: Set[Fraction] = {one}
    first_seen: Dict[Fraction, int] = {one: 0}
    first_witness: Dict[Fraction, Optional[Witness]] = {one: None}
    derivation_counts: DefaultDict[Fraction, int] = defaultdict(int)
    op_counts: DefaultDict[Fraction, Counter] = defaultdict(Counter)
    round_rows: List[Dict[str, object]] = []

    def allow(value: Fraction) -> bool:
        return bounded(
            value,
            max_abs_p=config.max_abs_p,
            max_abs_q=config.max_abs_q,
            max_abs_value=config.max_abs_value,
        )

    for round_idx in range(1, config.rounds + 1):
        s_list = sorted(s_prev, key=complexity_key)
        delta_list = sorted(delta_prev, key=complexity_key)
        new_delta: Set[Fraction] = set()
        new_ops: Counter = Counter()
        retained_ops: Counter = Counter()
        candidate_events = 0
        retained_events = 0

        for a in delta_list:
            for b in s_list:
                for op, left, right, out in _candidate_events(a, b):
                    candidate_events += 1
                    if not allow(out):
                        continue
                    retained_events += 1
                    retained_ops[op] += 1
                    derivation_counts[out] += 1
                    op_counts[out][op] += 1
                    if out in s_prev or out in new_delta:
                        continue
                    new_delta.add(out)
                    first_seen[out] = int(round_idx)
                    first_witness[out] = (op, left, right)
                    new_ops[op] += 1

        s_now = s_prev.union(new_delta)
        round_rows.append(
            {
                "round": int(round_idx),
                "size_prev": len(s_prev),
                "size_now": len(s_now),
                "new_values": len(new_delta),
                "candidate_events": int(candidate_events),
                "retained_events": int(retained_events),
                "retained_operation_events": {
                    op: int(retained_ops.get(op, 0)) for op in ["+", "-", "*", "/"]
                },
                "new_value_first_witness_ops": {op: int(new_ops.get(op, 0)) for op in ["+", "-", "*", "/"]},
            }
        )

        if not new_delta:
            s_prev = s_now
            delta_prev = set()
            break

        s_prev = s_now
        delta_prev = new_delta

    neighbors = _neighbor_map(s_prev)
    values = sorted(s_prev, key=complexity_key)
    non_integers = [value for value in values if value.denominator != 1]
    nonzero_non_integers = [value for value in non_integers if value != 0]

    def payload(value: Fraction, *, ancestry_depth: Optional[int] = None) -> Dict[str, object]:
        depth = config.ancestry_depth if ancestry_depth is None else ancestry_depth
        return _value_payload(
            value,
            first_seen=first_seen,
            first_witness=first_witness,
            derivation_counts=derivation_counts,
            op_counts=op_counts,
            neighbors=neighbors,
            ancestry_depth=depth,
        )

    def multiplicity_key(value: Fraction) -> Tuple[int, int, Tuple[int, int, int]]:
        return (-int(derivation_counts.get(value, 0)), int(first_seen.get(value, 999999)), complexity_key(value))

    def diversity_key(value: Fraction) -> Tuple[int, int, int, Tuple[int, int, int]]:
        ops = op_counts.get(value, Counter())
        distinct_ops = sum(1 for op in ["+", "-", "*", "/"] if ops.get(op, 0) > 0)
        return (
            -distinct_ops,
            -int(derivation_counts.get(value, 0)),
            int(first_seen.get(value, 999999)),
            complexity_key(value),
        )

    def early_noninteger_key(value: Fraction) -> Tuple[int, int, int, Tuple[int, int, int]]:
        return (
            int(first_seen.get(value, 999999)),
            -int(derivation_counts.get(value, 0)),
            -int(value.denominator),
            complexity_key(value),
        )

    def tight_neighbor_key(value: Fraction) -> Tuple[Fraction, int, Tuple[int, int, int]]:
        min_gap_payload = neighbors.get(value, {}).get("min_gap")
        if isinstance(min_gap_payload, dict) and min_gap_payload.get("frac") is not None:
            gap_text = str(min_gap_payload["frac"])
            gap = Fraction(gap_text)
        else:
            gap = Fraction(10**18, 1)
        return (gap, int(first_seen.get(value, 999999)), complexity_key(value))

    first_seen_counts = Counter(first_seen.values())
    denominator_buckets = Counter(_denominator_bucket(int(value.denominator)) for value in values)
    sign_counts = Counter("negative" if value < 0 else "zero" if value == 0 else "positive" for value in values)

    rankings = {
        "derivation_multiplicity": _top_values(
            values, top_k=config.top_k, key=multiplicity_key, payload=payload
        ),
        "non_integer_multiplicity": _top_values(
            non_integers, top_k=config.top_k, key=multiplicity_key, payload=payload
        ),
        "operation_diversity": _top_values(values, top_k=config.top_k, key=diversity_key, payload=payload),
        "early_non_integers": _top_values(
            nonzero_non_integers, top_k=config.top_k, key=early_noninteger_key, payload=payload
        ),
        "tight_neighbors": _top_values(
            nonzero_non_integers, top_k=config.top_k, key=tight_neighbor_key, payload=payload
        ),
    }

    report: Dict[str, object] = {
        "schema_version": 1,
        "method": {
            "status": "historical_exploratory_closure",
            "alignment": (
                "This scan reuses generated values as operands. It is not "
                "aligned MoO computation; use strict_stage_moo.py for current "
                "graph-first runs."
            ),
            "target_blind": True,
            "recomputed_closure": True,
            "closure_rule": "Each round combines the previous delta with the previous retained set.",
            "derivation_event_semantics": (
                "Counts bounded oriented operation events, including events that land on values "
                "already seen in earlier rounds."
            ),
            "interpretation_order": [
                "Inspect MoO-native rankings and witnesses first.",
                "Use external recognition or classical baselines only after candidate values or chains are selected.",
            ],
        },
        "config": {
            "rounds": int(config.rounds),
            "max_abs_p": int(config.max_abs_p),
            "max_abs_q": int(config.max_abs_q),
            "max_abs_value": config.max_abs_value,
            "top_k": int(config.top_k),
            "include_ledger": bool(config.include_ledger),
            "ancestry_depth": int(config.ancestry_depth),
        },
        "final": {
            "size": len(s_prev),
            "max_round_completed": round_rows[-1]["round"] if round_rows else 0,
            "non_integer_values": len(non_integers),
            "integer_values": len(values) - len(non_integers),
            "first_seen_counts": {str(k): int(v) for k, v in sorted(first_seen_counts.items())},
            "denominator_buckets": {k: int(v) for k, v in sorted(denominator_buckets.items())},
            "sign_counts": {k: int(v) for k, v in sorted(sign_counts.items())},
        },
        "rounds": round_rows,
        "rankings": rankings,
    }
    if config.include_ledger:
        report["ledger"] = [payload(value, ancestry_depth=0) for value in values]
    return report


def _ledger_rankings(ledger: Sequence[Dict[str, object]], *, top_k: int) -> Dict[str, object]:
    rows = [dict(row) for row in ledger]

    def row_int(row: Dict[str, object], key: str, default: int = 0) -> int:
        try:
            return int(row.get(key, default))
        except (TypeError, ValueError):
            return int(default)

    def row_complexity(row: Dict[str, object]) -> Tuple[int, int, int]:
        return (row_int(row, "q", 1), row_int(row, "abs_numerator", 0), row_int(row, "p", 0))

    def is_non_integer(row: Dict[str, object]) -> bool:
        return row_int(row, "q", 1) != 1

    def is_nonzero(row: Dict[str, object]) -> bool:
        return row_int(row, "p", 0) != 0

    def multiplicity_key(row: Dict[str, object]) -> Tuple[int, int, Tuple[int, int, int]]:
        return (-row_int(row, "derivation_events"), row_int(row, "first_seen_round", 999999), row_complexity(row))

    def diversity_key(row: Dict[str, object]) -> Tuple[int, int, int, Tuple[int, int, int]]:
        return (
            -row_int(row, "distinct_ops"),
            -row_int(row, "derivation_events"),
            row_int(row, "first_seen_round", 999999),
            row_complexity(row),
        )

    def early_noninteger_key(row: Dict[str, object]) -> Tuple[int, int, int, Tuple[int, int, int]]:
        return (
            row_int(row, "first_seen_round", 999999),
            -row_int(row, "derivation_events"),
            -row_int(row, "q", 1),
            row_complexity(row),
        )

    def tight_neighbor_key(row: Dict[str, object]) -> Tuple[Fraction, int, Tuple[int, int, int]]:
        gap = Fraction(10**18, 1)
        neighbors = row.get("neighbors")
        if isinstance(neighbors, dict):
            min_gap = neighbors.get("min_gap")
            if isinstance(min_gap, dict) and min_gap.get("frac") is not None:
                try:
                    gap = Fraction(str(min_gap["frac"]))
                except (ValueError, ZeroDivisionError):
                    gap = Fraction(10**18, 1)
        return (gap, row_int(row, "first_seen_round", 999999), row_complexity(row))

    non_integers = [row for row in rows if is_non_integer(row)]
    nonzero_non_integers = [row for row in non_integers if is_nonzero(row)]
    n = max(0, int(top_k))
    return {
        "derivation_multiplicity": sorted(rows, key=multiplicity_key)[:n],
        "non_integer_multiplicity": sorted(non_integers, key=multiplicity_key)[:n],
        "operation_diversity": sorted(rows, key=diversity_key)[:n],
        "early_non_integers": sorted(nonzero_non_integers, key=early_noninteger_key)[:n],
        "tight_neighbors": sorted(nonzero_non_integers, key=tight_neighbor_key)[:n],
    }


def _load_report(path: Path, *, top_k: int, include_ledger: bool) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Report is not a JSON object: {path}")
    ledger = payload.get("ledger")
    if not isinstance(ledger, list):
        raise SystemExit(
            "Report has no ledger. Recreate it with: "
            "python3 native_emergence_scan.py --include-ledger --write <path>"
        )
    payload = dict(payload)
    payload["rankings"] = _ledger_rankings(ledger, top_k=top_k)
    method = dict(payload.get("method", {})) if isinstance(payload.get("method"), dict) else {}
    method["source_report"] = str(path)
    method["recomputed_closure"] = False
    payload["method"] = method
    config = dict(payload.get("config", {})) if isinstance(payload.get("config"), dict) else {}
    config["top_k"] = int(top_k)
    config["include_ledger"] = bool(include_ledger)
    payload["config"] = config
    if not include_ledger:
        payload.pop("ledger", None)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Target-blind MoO-native emergence scan over bounded rational closure."
    )
    parser.add_argument("--from-report", type=str, default=None, help="Rerank a saved ledger report.")
    parser.add_argument("--rounds", type=int, default=5, help="Closure rounds; 5 is the local default.")
    parser.add_argument("--max-abs-p", type=int, default=100, help="Max absolute numerator.")
    parser.add_argument("--max-abs-q", type=int, default=100, help="Max absolute denominator.")
    parser.add_argument("--max-abs-value", type=float, default=4.0, help="Max absolute value.")
    parser.add_argument("--top-k", type=int, default=12, help="Rows per ranking.")
    parser.add_argument("--ancestry-depth", type=int, default=1, help="Parent witness depth for ranked rows.")
    parser.add_argument("--include-ledger", action="store_true", help="Include one compact row for every value.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.from_report is not None:
        payload = _load_report(
            Path(str(args.from_report)),
            top_k=max(1, int(args.top_k)),
            include_ledger=bool(args.include_ledger),
        )
    else:
        config = NativeScanConfig(
            rounds=max(0, int(args.rounds)),
            max_abs_p=max(0, int(args.max_abs_p)),
            max_abs_q=max(1, int(args.max_abs_q)),
            max_abs_value=float(args.max_abs_value) if args.max_abs_value is not None else None,
            top_k=max(1, int(args.top_k)),
            include_ledger=bool(args.include_ledger),
            ancestry_depth=max(0, int(args.ancestry_depth)),
        )
        payload = native_emergence_scan(config)
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
