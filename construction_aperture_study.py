from __future__ import annotations

import argparse
import json
import signal
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple


DEFAULT_INSPECT = ("22/7", "87/32", "52/75", "99/70", "34/21")


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


def _load_report(path: Path) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Report is not a JSON object: {path}")
    ledger = payload.get("ledger")
    if not isinstance(ledger, list):
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


def _row_int(row: Optional[Dict[str, object]], key: str, default: int = 0) -> int:
    if row is None:
        return int(default)
    try:
        return int(row.get(key, default))
    except (TypeError, ValueError):
        return int(default)


def _complexity_key(value: Fraction) -> Tuple[int, int, int]:
    return (int(value.denominator), abs(int(value.numerator)), int(value.numerator))


def _witness(row: Optional[Dict[str, object]]) -> Tuple[Optional[str], Optional[Fraction], Optional[Fraction]]:
    if row is None:
        return None, None, None
    witness = row.get("first_witness")
    if not isinstance(witness, dict):
        return None, None, None
    op_raw = witness.get("op")
    op = str(op_raw) if op_raw is not None else None
    return op, _parse_fraction(witness.get("a")), _parse_fraction(witness.get("b"))


def _witness_payload(row: Optional[Dict[str, object]]) -> Optional[Dict[str, object]]:
    if row is None:
        return None
    witness = row.get("first_witness")
    if not isinstance(witness, dict):
        return None
    return {
        "op": witness.get("op"),
        "a": witness.get("a"),
        "b": witness.get("b"),
        "expr": witness.get("expr"),
    }


def _operation_signature(row: Optional[Dict[str, object]]) -> Dict[str, int]:
    signature = row.get("operation_signature") if isinstance(row, dict) else None
    if not isinstance(signature, dict):
        return {op: 0 for op in ["+", "-", "*", "/"]}
    return {op: _row_int(signature, op, 0) for op in ["+", "-", "*", "/"]}


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


def _config(report: Dict[str, object]) -> Dict[str, object]:
    config = report.get("config")
    return dict(config) if isinstance(config, dict) else {}


def _round_budget(report: Dict[str, object]) -> int:
    config = _config(report)
    rounds = _row_int(config, "rounds", 0)
    final = report.get("final")
    if isinstance(final, dict):
        rounds = max(rounds, _row_int(final, "max_round_completed", 0))
    return rounds


def _ancestry_values(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    depth: int,
    seen: Set[Fraction],
) -> Set[Fraction]:
    if value in seen:
        return {value}
    out = {value}
    if depth <= 0:
        return out
    row = rows_by_frac.get(value)
    op, a, b = _witness(row)
    if op is None or a is None or b is None:
        return out
    next_seen = set(seen)
    next_seen.add(value)
    out.update(_ancestry_values(a, rows_by_frac=rows_by_frac, depth=depth - 1, seen=next_seen))
    out.update(_ancestry_values(b, rows_by_frac=rows_by_frac, depth=depth - 1, seen=next_seen))
    return out


def _cap_payload(
    cap: Fraction,
    *,
    value: Fraction,
    ancestry: Set[Fraction],
) -> Dict[str, object]:
    blockers = sorted(
        [ancestor for ancestor in ancestry if abs(ancestor) > cap],
        key=lambda item: (-abs(item), _complexity_key(item)),
    )
    final_fits = abs(value) <= cap
    ancestry_fits = not blockers
    return {
        "cap": float(cap),
        "cap_frac": _format_fraction(cap),
        "final_fits_cap": bool(final_fits),
        "ancestry_fits_cap": bool(ancestry_fits),
        "escape_and_return": bool(final_fits and not ancestry_fits),
        "blocker_count": len(blockers),
        "max_blockers": [
            {"frac": _format_fraction(item), "abs_value": float(abs(item))}
            for item in blockers[:8]
        ],
    }


def _value_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    ancestry_depth: int,
    caps: Sequence[Fraction],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    ancestry = _ancestry_values(value, rows_by_frac=rows_by_frac, depth=ancestry_depth, seen=set())
    aperture = max((abs(item) for item in ancestry), default=abs(value))
    aperture_values = sorted(
        [item for item in ancestry if abs(item) == aperture],
        key=_complexity_key,
    )
    final_abs = abs(value)
    excess = aperture - final_abs
    ratio: Optional[float]
    if final_abs == 0:
        ratio = None
    else:
        ratio = float(aperture / final_abs)
    return {
        "frac": _format_fraction(value),
        "p": int(value.numerator),
        "q": int(value.denominator),
        "value": float(value),
        "abs_value": float(final_abs),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "first_witness": _witness_payload(row),
        "derivation_events": _row_int(row, "derivation_events", 0),
        "operation_signature": _operation_signature(row),
        "denominator_bucket": _denominator_bucket(value.denominator),
        "first_witness_ancestry_size": len(ancestry),
        "first_witness_aperture": {
            "frac": _format_fraction(aperture),
            "float": float(aperture),
            "values": [_format_fraction(item) for item in aperture_values[:8]],
        },
        "aperture_excess": {
            "frac": _format_fraction(excess),
            "float": float(excess),
        },
        "aperture_ratio": ratio,
        "cap_checks": [_cap_payload(cap, value=value, ancestry=ancestry) for cap in caps],
    }


def _payload_fraction(row: Dict[str, object]) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _payload_first_seen(row: Dict[str, object]) -> int:
    return _row_int(row, "first_seen_round", 999999)


def _payload_aperture(row: Dict[str, object]) -> Fraction:
    aperture = row.get("first_witness_aperture")
    if not isinstance(aperture, dict):
        return Fraction(0, 1)
    parsed = _parse_fraction(aperture.get("frac"))
    return parsed if parsed is not None else Fraction(0, 1)


def _payload_excess(row: Dict[str, object]) -> Fraction:
    excess = row.get("aperture_excess")
    if not isinstance(excess, dict):
        return Fraction(0, 1)
    parsed = _parse_fraction(excess.get("frac"))
    return parsed if parsed is not None else Fraction(0, 1)


def _payload_ratio(row: Dict[str, object]) -> float:
    ratio = row.get("aperture_ratio")
    try:
        return float(ratio)
    except (TypeError, ValueError):
        return -1.0


def _cap_check(row: Dict[str, object], cap: Fraction) -> Optional[Dict[str, object]]:
    target = _format_fraction(cap)
    checks = row.get("cap_checks")
    if not isinstance(checks, list):
        return None
    for check in checks:
        if isinstance(check, dict) and check.get("cap_frac") == target:
            return check
    return None


def _top_rows(rows: Sequence[Dict[str, object]], *, key, limit: int) -> List[Dict[str, object]]:
    return [dict(row) for row in sorted(rows, key=key)[: max(0, int(limit))]]


def _ranking_payload(rows: Sequence[Dict[str, object]], *, caps: Sequence[Fraction], top_k: int) -> Dict[str, object]:
    rankings: Dict[str, object] = {
        "largest_aperture_excess": _top_rows(
            rows,
            key=lambda row: (
                -_payload_excess(row),
                _payload_first_seen(row),
                _complexity_key(_payload_fraction(row)),
            ),
            limit=top_k,
        ),
        "largest_aperture_ratio": _top_rows(
            [row for row in rows if row.get("aperture_ratio") is not None],
            key=lambda row: (
                -_payload_ratio(row),
                _payload_first_seen(row),
                _complexity_key(_payload_fraction(row)),
            ),
            limit=top_k,
        ),
        "largest_absolute_aperture": _top_rows(
            rows,
            key=lambda row: (
                -_payload_aperture(row),
                _payload_first_seen(row),
                _complexity_key(_payload_fraction(row)),
            ),
            limit=top_k,
        ),
    }
    for cap in caps:
        check_key = _format_fraction(cap)
        escaped = [
            row
            for row in rows
            if isinstance(_cap_check(row, cap), dict)
            and bool(_cap_check(row, cap).get("escape_and_return"))
        ]
        rankings[f"escape_and_return_cap_{check_key}"] = _top_rows(
            escaped,
            key=lambda row: (
                -_payload_aperture(row),
                -_payload_excess(row),
                _payload_first_seen(row),
                _complexity_key(_payload_fraction(row)),
            ),
            limit=top_k,
        )
    return rankings


def _summary_payload(rows: Sequence[Dict[str, object]], *, caps: Sequence[Fraction]) -> Dict[str, object]:
    first_seen_counts = Counter(str(_row_int(row, "first_seen_round", -1)) for row in rows)
    aperture_buckets = Counter()
    excess_positive = 0
    for row in rows:
        aperture = _payload_aperture(row)
        if aperture <= 1:
            aperture_buckets["<=1"] += 1
        elif aperture <= 2:
            aperture_buckets["(1,2]"] += 1
        elif aperture <= 3:
            aperture_buckets["(2,3]"] += 1
        elif aperture <= 4:
            aperture_buckets["(3,4]"] += 1
        else:
            aperture_buckets[">4"] += 1
        if _payload_excess(row) > 0:
            excess_positive += 1

    cap_counts: Dict[str, object] = {}
    by_round: DefaultDict[str, Counter] = defaultdict(Counter)
    for cap in caps:
        cap_label = _format_fraction(cap)
        final_fits = 0
        ancestry_fits = 0
        escape = 0
        for row in rows:
            check = _cap_check(row, cap)
            if not isinstance(check, dict):
                continue
            if bool(check.get("final_fits_cap")):
                final_fits += 1
            if bool(check.get("ancestry_fits_cap")):
                ancestry_fits += 1
            if bool(check.get("escape_and_return")):
                escape += 1
                by_round[cap_label][str(_row_int(row, "first_seen_round", -1))] += 1
        cap_counts[cap_label] = {
            "final_fits_cap": final_fits,
            "ancestry_fits_cap": ancestry_fits,
            "escape_and_return": escape,
            "escape_and_return_by_first_seen_round": {
                key: int(value) for key, value in sorted(by_round[cap_label].items())
            },
        }

    return {
        "value_count": len(rows),
        "first_seen_counts": {key: int(value) for key, value in sorted(first_seen_counts.items())},
        "aperture_buckets": {key: int(value) for key, value in sorted(aperture_buckets.items())},
        "values_with_positive_aperture_excess": int(excess_positive),
        "cap_counts": cap_counts,
    }


def _inspect_payload(
    rows_by_label: Dict[str, Dict[str, object]],
    labels: Sequence[str],
) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for label in labels:
        row = rows_by_label.get(label)
        out[label] = dict(row) if row is not None else None
    return out


def _parse_caps(raw: str) -> Tuple[Fraction, ...]:
    caps: List[Fraction] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        caps.append(Fraction(chunk))
    if not caps:
        raise SystemExit("No caps provided.")
    return tuple(caps)


def _parse_inspect(raw: str) -> Tuple[str, ...]:
    return tuple(chunk.strip() for chunk in raw.split(",") if chunk.strip())


def build_report(
    *,
    source_report_path: Path,
    ancestry_depth: int,
    caps: Sequence[Fraction],
    inspect_labels: Sequence[str],
    top_k: int,
    include_rows: bool,
) -> Dict[str, object]:
    source = _load_report(source_report_path)
    rows_by_frac = _rows_by_frac(source)
    values = sorted(rows_by_frac, key=_complexity_key)
    rows = [
        _value_payload(
            value,
            rows_by_frac=rows_by_frac,
            ancestry_depth=ancestry_depth,
            caps=caps,
        )
        for value in values
    ]
    rows_by_label = {str(row["frac"]): row for row in rows}
    report: Dict[str, object] = {
        "schema_version": 1,
        "method": {
            "source": "First-witness construction aperture over a saved native emergence ledger.",
            "source_report": str(source_report_path),
            "ancestry_depth": int(ancestry_depth),
            "round_budget": _round_budget(source),
            "caps": [_format_fraction(cap) for cap in caps],
            "limitation": (
                "This measures the aperture of the saved first-witness ancestry, not the globally "
                "minimal aperture over all possible derivations."
            ),
        },
        "source_config": _config(source),
        "summary": _summary_payload(rows, caps=caps),
        "rankings": _ranking_payload(rows, caps=caps, top_k=top_k),
        "inspected": _inspect_payload(rows_by_label, inspect_labels),
    }
    if include_rows:
        report["rows"] = rows
    return report


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Compute first-witness construction aperture over a saved MoO ledger."
    )
    parser.add_argument("--source-report", type=str, default="out/experiments/native_r6_full.json")
    parser.add_argument("--ancestry-depth", type=int, default=8)
    parser.add_argument("--caps", type=str, default="3,4")
    parser.add_argument("--inspect", type=str, default=",".join(DEFAULT_INSPECT))
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--include-rows", action="store_true", help="Include compact aperture row for every value.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = build_report(
        source_report_path=Path(str(args.source_report)),
        ancestry_depth=max(0, int(args.ancestry_depth)),
        caps=_parse_caps(str(args.caps)),
        inspect_labels=_parse_inspect(str(args.inspect)),
        top_k=max(1, int(args.top_k)),
        include_rows=bool(args.include_rows),
    )
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
