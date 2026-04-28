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
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class ResidualConfig:
    report: Path
    top_k: int
    min_q: int
    min_abs_value: float
    exclude_integers: bool
    exclude_unit_fractions: bool
    exclude_boundary_q_ratio: float
    min_bucket_size: int
    ancestry_depth: int
    inspect_fracs: Tuple[Fraction, ...]


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


def _bucket_number(value: int) -> str:
    value = abs(int(value))
    if value == 0:
        return "0"
    if value == 1:
        return "1"
    if value <= 5:
        return "2-5"
    if value <= 10:
        return "6-10"
    if value <= 25:
        return "11-25"
    if value <= 50:
        return "26-50"
    if value <= 100:
        return "51-100"
    return ">100"


def _row_fraction(row: Dict[str, object]) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _row_int(row: Dict[str, object], key: str, default: int = 0) -> int:
    try:
        return int(row.get(key, default))
    except (TypeError, ValueError):
        return int(default)


def _row_float(row: Dict[str, object], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _complexity_key(row: Dict[str, object]) -> Tuple[int, int, int]:
    return (_row_int(row, "q", 1), _row_int(row, "abs_numerator", 0), _row_int(row, "p", 0))


def _median_abs_deviation(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    center = float(median(values))
    return float(median([abs(v - center) for v in values]))


def _first_witness(row: Dict[str, object]) -> Optional[Dict[str, object]]:
    witness = row.get("first_witness")
    if isinstance(witness, dict):
        return witness
    return None


def _parent_fracs(row: Dict[str, object]) -> Tuple[Optional[Fraction], Optional[Fraction]]:
    witness = _first_witness(row)
    if witness is None:
        return None, None
    return _parse_fraction(witness.get("a")), _parse_fraction(witness.get("b"))


def _nontrivial_fraction(value: Optional[Fraction], *, min_q: int) -> bool:
    if value is None:
        return False
    if value.denominator == 1:
        return abs(value.numerator) > 1
    if value.denominator < min_q:
        return False
    if abs(value.numerator) == 1:
        return False
    return True


def _filter_reasons(
    row: Dict[str, object],
    *,
    config: ResidualConfig,
    max_q: int,
) -> List[str]:
    value = _row_fraction(row)
    p = int(value.numerator)
    q = int(value.denominator)
    reasons: List[str] = []
    if config.exclude_integers and q == 1:
        reasons.append("integer")
    if q < config.min_q:
        reasons.append("small_q")
    if config.exclude_unit_fractions and abs(p) == 1 and q > 1:
        reasons.append("unit_fraction")
    if abs(float(value)) < float(config.min_abs_value):
        reasons.append("near_zero")
    if config.exclude_boundary_q_ratio > 0 and max_q > 0:
        threshold = max(1, math.floor(max_q * float(config.exclude_boundary_q_ratio)))
        if q >= threshold:
            reasons.append("boundary_q")
    return reasons


def _bucket_key(row: Dict[str, object]) -> Tuple[str, str]:
    return (str(_row_int(row, "first_seen_round", -1)), _bucket_number(_row_int(row, "q", 1)))


def _broad_bucket_key(row: Dict[str, object]) -> Tuple[str]:
    return (str(_row_int(row, "first_seen_round", -1)),)


def _stats(values: Sequence[float]) -> Dict[str, object]:
    if not values:
        return {"size": 0, "median": 0.0, "mad": 0.0}
    return {
        "size": len(values),
        "median": float(median(values)),
        "mad": _median_abs_deviation(values),
    }


def _ancestry(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    depth: int,
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    if row is None:
        return {"frac": _format_fraction(value), "missing": True}
    payload: Dict[str, object] = {
        "frac": _format_fraction(value),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "first_witness": row.get("first_witness"),
    }
    if depth <= 0:
        return payload
    a, b = _parent_fracs(row)
    parents: List[Dict[str, object]] = []
    for parent in (a, b):
        if parent is not None:
            parents.append(_ancestry(parent, rows_by_frac=rows_by_frac, depth=depth - 1))
    if parents:
        payload["parents"] = parents
    return payload


def _annotate_row(
    row: Dict[str, object],
    *,
    stats_by_bucket: Dict[Tuple[str, str], Dict[str, object]],
    stats_by_round: Dict[Tuple[str], Dict[str, object]],
    config: ResidualConfig,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
    filtered_out: bool,
    filter_reasons: Sequence[str],
) -> Dict[str, object]:
    events = max(0, _row_int(row, "derivation_events"))
    log_events = math.log1p(events)
    bucket = _bucket_key(row)
    broad = _broad_bucket_key(row)
    stat = stats_by_bucket.get(bucket, {"size": 0, "median": 0.0, "mad": 0.0})
    if int(stat.get("size", 0)) < config.min_bucket_size:
        stat = stats_by_round.get(broad, stat)
        bucket_kind = "round"
    else:
        bucket_kind = "round_and_q_band"
    center = float(stat.get("median", 0.0))
    mad = float(stat.get("mad", 0.0))
    scale = max(1.4826 * mad, 0.25)
    residual_log = log_events - center
    robust_z = residual_log / scale
    frac = _row_fraction(row)
    a, b = _parent_fracs(row)
    parent_rounds = []
    for parent in (a, b):
        parent_row = rows_by_frac.get(parent) if parent is not None else None
        parent_rounds.append(_row_int(parent_row, "first_seen_round", -1) if parent_row else None)
    witness = _first_witness(row)
    op = str(witness.get("op")) if witness is not None and witness.get("op") is not None else None
    payload: Dict[str, object] = {
        "frac": _format_fraction(frac),
        "p": int(frac.numerator),
        "q": int(frac.denominator),
        "value": float(frac),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "first_witness": row.get("first_witness"),
        "parent_first_seen_rounds": parent_rounds,
        "derivation_events": events,
        "operation_signature": row.get("operation_signature", {}),
        "distinct_ops": _row_int(row, "distinct_ops"),
        "neighbors": row.get("neighbors"),
        "residual": {
            "bucket": list(bucket),
            "bucket_kind": bucket_kind,
            "bucket_size": int(stat.get("size", 0)),
            "bucket_median_log1p_events": center,
            "bucket_mad_log1p_events": mad,
            "log1p_events": log_events,
            "residual_log1p_events": residual_log,
            "robust_z": robust_z,
        },
        "witness_nontriviality": {
            "op": op,
            "parent_a": _format_fraction(a) if a is not None else None,
            "parent_b": _format_fraction(b) if b is not None else None,
            "nontrivial_parent_count": sum(
                1 for parent in (a, b) if _nontrivial_fraction(parent, min_q=config.min_q)
            ),
        },
        "filtered_out": bool(filtered_out),
        "filter_reasons": list(filter_reasons),
    }
    if config.ancestry_depth > 0:
        payload["ancestry"] = _ancestry(frac, rows_by_frac=rows_by_frac, depth=config.ancestry_depth)
    return payload


def residual_study(config: ResidualConfig) -> Dict[str, object]:
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
    source_config = source.get("config") if isinstance(source.get("config"), dict) else {}
    max_q = int(source_config.get("max_abs_q", 0) or 0)

    excluded: Counter = Counter()
    included_rows: List[Dict[str, object]] = []
    filter_map: Dict[Fraction, List[str]] = {}
    for row in rows:
        reasons = _filter_reasons(row, config=config, max_q=max_q)
        filter_map[_row_fraction(row)] = reasons
        if reasons:
            for reason in reasons:
                excluded[reason] += 1
            continue
        included_rows.append(row)

    logs_by_bucket: DefaultDict[Tuple[str, str], List[float]] = defaultdict(list)
    logs_by_round: DefaultDict[Tuple[str], List[float]] = defaultdict(list)
    for row in included_rows:
        value = math.log1p(max(0, _row_int(row, "derivation_events")))
        logs_by_bucket[_bucket_key(row)].append(value)
        logs_by_round[_broad_bucket_key(row)].append(value)

    stats_by_bucket = {key: _stats(values) for key, values in logs_by_bucket.items()}
    stats_by_round = {key: _stats(values) for key, values in logs_by_round.items()}

    annotated = [
        _annotate_row(
            row,
            stats_by_bucket=stats_by_bucket,
            stats_by_round=stats_by_round,
            config=config,
            rows_by_frac=rows_by_frac,
            filtered_out=False,
            filter_reasons=[],
        )
        for row in included_rows
    ]

    def residual_key(row: Dict[str, object]) -> Tuple[float, int, int, Tuple[int, int, int]]:
        residual = row.get("residual") if isinstance(row.get("residual"), dict) else {}
        return (
            -float(residual.get("robust_z", 0.0)),
            -int(row.get("derivation_events", 0)),
            int(row.get("first_seen_round", 999999)),
            (int(row.get("q", 1)), abs(int(row.get("p", 0))), int(row.get("p", 0))),
        )

    def nontrivial_witness(row: Dict[str, object]) -> bool:
        witness = row.get("witness_nontriviality")
        if not isinstance(witness, dict):
            return False
        return int(witness.get("nontrivial_parent_count", 0)) >= 2

    def mixed_ops(row: Dict[str, object]) -> bool:
        return int(row.get("distinct_ops", 0)) >= 3

    inspected: Dict[str, object] = {}
    for value in config.inspect_fracs:
        source_row = rows_by_frac.get(value)
        if source_row is None:
            inspected[_format_fraction(value)] = {"present": False}
            continue
        reasons = filter_map.get(value, [])
        inspected[_format_fraction(value)] = _annotate_row(
            source_row,
            stats_by_bucket=stats_by_bucket,
            stats_by_round=stats_by_round,
            config=config,
            rows_by_frac=rows_by_frac,
            filtered_out=bool(reasons),
            filter_reasons=reasons,
        )

    source_final = source.get("final") if isinstance(source.get("final"), dict) else {}
    return {
        "schema_version": 1,
        "method": {
            "source_report": str(config.report),
            "target_blind": True,
            "recomputed_closure": False,
            "residual_formula": (
                "log1p(derivation_events) minus bucket median, scaled by robust MAD. "
                "Buckets are first_seen_round x denominator band, with round-only fallback."
            ),
            "purpose": (
                "Subtract the obvious arithmetic skeleton before looking for nontrivial "
                "MoO-native prominence."
            ),
        },
        "config": {
            "top_k": int(config.top_k),
            "min_q": int(config.min_q),
            "min_abs_value": float(config.min_abs_value),
            "exclude_integers": bool(config.exclude_integers),
            "exclude_unit_fractions": bool(config.exclude_unit_fractions),
            "exclude_boundary_q_ratio": float(config.exclude_boundary_q_ratio),
            "min_bucket_size": int(config.min_bucket_size),
            "ancestry_depth": int(config.ancestry_depth),
            "inspect_fracs": [_format_fraction(value) for value in config.inspect_fracs],
        },
        "source_final": source_final,
        "filter_counts": {
            "source_rows": len(rows),
            "included_rows": len(included_rows),
            "excluded_rows": len(rows) - len(included_rows),
            "excluded_by_reason": {key: int(value) for key, value in sorted(excluded.items())},
        },
        "bucket_counts": {
            "/".join(key): int(stat["size"]) for key, stat in sorted(stats_by_bucket.items())
        },
        "rankings": {
            "residual_prominence": sorted(annotated, key=residual_key)[: config.top_k],
            "nontrivial_witness_residuals": sorted(
                [row for row in annotated if nontrivial_witness(row)], key=residual_key
            )[: config.top_k],
            "mixed_operation_residuals": sorted(
                [row for row in annotated if mixed_ops(row)], key=residual_key
            )[: config.top_k],
        },
        "inspected": inspected,
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
        description="Residual MoO-native emergence study over a saved target-blind ledger."
    )
    parser.add_argument("--report", type=str, required=True, help="native_emergence_scan.py JSON with ledger.")
    parser.add_argument("--top-k", type=int, default=20, help="Rows per ranking.")
    parser.add_argument("--min-q", type=int, default=3, help="Exclude denominators smaller than this.")
    parser.add_argument("--min-abs-value", type=float, default=0.05, help="Exclude near-zero values.")
    parser.add_argument("--keep-integers", action="store_true", help="Do not filter integer values.")
    parser.add_argument("--keep-unit-fractions", action="store_true", help="Do not filter unit fractions.")
    parser.add_argument(
        "--exclude-boundary-q-ratio",
        type=float,
        default=0.9,
        help="Exclude q >= ratio * max_abs_q from the source report; <=0 disables.",
    )
    parser.add_argument("--min-bucket-size", type=int, default=8, help="Fallback to round bucket below this size.")
    parser.add_argument("--ancestry-depth", type=int, default=1, help="First-witness ancestry depth in ranked rows.")
    parser.add_argument(
        "--inspect-fracs",
        type=str,
        default="22/7,87/32,52/75,99/70,34/21",
        help="Comma-separated fractions to inspect after ranking; empty string disables.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = ResidualConfig(
        report=Path(str(args.report)),
        top_k=max(1, int(args.top_k)),
        min_q=max(1, int(args.min_q)),
        min_abs_value=max(0.0, float(args.min_abs_value)),
        exclude_integers=not bool(args.keep_integers),
        exclude_unit_fractions=not bool(args.keep_unit_fractions),
        exclude_boundary_q_ratio=float(args.exclude_boundary_q_ratio),
        min_bucket_size=max(1, int(args.min_bucket_size)),
        ancestry_depth=max(0, int(args.ancestry_depth)),
        inspect_fracs=_parse_inspect_fracs(str(args.inspect_fracs)),
    )
    payload = residual_study(config)
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
