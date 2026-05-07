from __future__ import annotations

import argparse
import json
import signal
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple


DEFAULT_TARGETS = ("22/7", "87/32", "52/75", "99/70", "34/21")


@dataclass(frozen=True)
class GridCell:
    q_cap: int
    value_cap: float
    report_name: str


DEFAULT_GRID = (
    GridCell(80, 3.0, "native_r5_q80_v3.json"),
    GridCell(80, 4.0, "native_r5_q80.json"),
    GridCell(80, 5.0, "native_r5_q80_v5.json"),
    GridCell(90, 3.0, "native_r5_q90_v3.json"),
    GridCell(90, 4.0, "native_r5_q90_v4.json"),
    GridCell(90, 5.0, "native_r5_q90_v5.json"),
    GridCell(100, 3.0, "native_r5_v3.json"),
    GridCell(100, 4.0, "native_r5_full.json"),
    GridCell(100, 5.0, "native_r5_v5.json"),
)


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


def _row_float(row: Optional[Dict[str, object]], key: str, default: float = 0.0) -> float:
    if row is None:
        return float(default)
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return float(default)


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


def _allowed_by_config(value: Fraction, config: Dict[str, object]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    max_abs_p = _row_int(config, "max_abs_p", 0)
    max_abs_q = _row_int(config, "max_abs_q", 0)
    max_abs_value_raw = config.get("max_abs_value")
    if max_abs_p > 0 and abs(value.numerator) > max_abs_p:
        reasons.append(f"abs_numerator>{max_abs_p}")
    if max_abs_q > 0 and value.denominator > max_abs_q:
        reasons.append(f"denominator>{max_abs_q}")
    if max_abs_value_raw is not None:
        try:
            max_abs_value = Fraction(str(max_abs_value_raw))
        except (ValueError, ZeroDivisionError):
            max_abs_value = None
        if max_abs_value is not None and abs(value) > max_abs_value:
            reasons.append(f"abs_value>{_format_fraction(max_abs_value)}")
    return not reasons, reasons


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


def _value_status(
    value: Fraction,
    *,
    high_rows: Dict[Fraction, Dict[str, object]],
    low_rows: Dict[Fraction, Dict[str, object]],
    low_config: Dict[str, object],
) -> Dict[str, object]:
    high_row = high_rows.get(value)
    low_row = low_rows.get(value)
    allowed, reasons = _allowed_by_config(value, low_config)
    return {
        "frac": _format_fraction(value),
        "value": float(value),
        "abs_value": float(abs(value)),
        "allowed_by_low_bounds": bool(allowed),
        "low_bound_reasons": reasons,
        "present_in_high": high_row is not None,
        "present_in_low": low_row is not None,
        "high_first_seen_round": _row_int(high_row, "first_seen_round", -1),
        "low_first_seen_round": _row_int(low_row, "first_seen_round", -1),
        "low_round_delay": (
            _row_int(low_row, "first_seen_round", -1) - _row_int(high_row, "first_seen_round", -1)
            if high_row is not None and low_row is not None
            else None
        ),
    }


def _baseline_edge_diagnosis(
    child: Fraction,
    *,
    high_rows: Dict[Fraction, Dict[str, object]],
    low_rows: Dict[Fraction, Dict[str, object]],
    low_report: Dict[str, object],
) -> Dict[str, object]:
    high_row = high_rows.get(child)
    low_config = _config(low_report)
    rounds = _round_budget(low_report)
    op, a, b = _witness(high_row)
    child_allowed, child_reasons = _allowed_by_config(child, low_config)
    diagnosis: Dict[str, object] = {
        "child": _format_fraction(child),
        "baseline_witness": _witness_payload(high_row),
        "low_round_budget": int(rounds),
        "child_allowed_by_low_bounds": bool(child_allowed),
        "child_low_bound_reasons": child_reasons,
        "same_witness_possible_in_low_budget": False,
        "same_witness_earliest_low_round": None,
        "reasons": [],
        "parents": [],
    }
    reasons: List[str] = []
    if op is None or a is None or b is None:
        reasons.append("no_baseline_witness")
        diagnosis["reasons"] = reasons
        return diagnosis
    if not child_allowed:
        reasons.append("child_excluded_by_low_bound")

    parent_rounds: List[int] = []
    for parent in (a, b):
        status = _value_status(parent, high_rows=high_rows, low_rows=low_rows, low_config=low_config)
        diagnosis["parents"].append(status)
        if not bool(status["present_in_low"]):
            reasons.append(f"parent_missing:{_format_fraction(parent)}")
            continue
        parent_rounds.append(int(status["low_first_seen_round"]))

    if len(parent_rounds) == 2:
        earliest = max(parent_rounds) + 1
        diagnosis["same_witness_earliest_low_round"] = int(earliest)
        if earliest > rounds:
            reasons.append(f"same_witness_after_low_round_budget:{earliest}")
        if child_allowed and earliest <= rounds:
            diagnosis["same_witness_possible_in_low_budget"] = True

    diagnosis["reasons"] = sorted(set(reasons))
    return diagnosis


def _ancestry_tree(
    value: Fraction,
    *,
    high_rows: Dict[Fraction, Dict[str, object]],
    low_rows: Dict[Fraction, Dict[str, object]],
    low_config: Dict[str, object],
    depth: int,
    seen: Set[Fraction],
) -> Dict[str, object]:
    status = _value_status(value, high_rows=high_rows, low_rows=low_rows, low_config=low_config)
    row = high_rows.get(value)
    status["first_witness"] = _witness_payload(row)
    if depth <= 0 or value in seen:
        return status
    op, a, b = _witness(row)
    if op is None or a is None or b is None:
        return status
    next_seen = set(seen)
    next_seen.add(value)
    status["parents"] = [
        _ancestry_tree(
            a,
            high_rows=high_rows,
            low_rows=low_rows,
            low_config=low_config,
            depth=depth - 1,
            seen=next_seen,
        ),
        _ancestry_tree(
            b,
            high_rows=high_rows,
            low_rows=low_rows,
            low_config=low_config,
            depth=depth - 1,
            seen=next_seen,
        ),
    ]
    return status


def _walk_tree(tree: Dict[str, object]) -> List[Dict[str, object]]:
    rows = [tree]
    parents = tree.get("parents")
    if isinstance(parents, list):
        for parent in parents:
            if isinstance(parent, dict):
                rows.extend(_walk_tree(parent))
    return rows


def _dedupe_value_rows(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    seen: Set[str] = set()
    out: List[Dict[str, object]] = []
    for row in rows:
        frac = str(row.get("frac"))
        if frac in seen:
            continue
        seen.add(frac)
        out.append(row)
    return out


def _nearest_bound_blockers(tree: Dict[str, object]) -> List[Dict[str, object]]:
    if not bool(tree.get("allowed_by_low_bounds", True)):
        return [
            {
                "frac": tree.get("frac"),
                "abs_value": tree.get("abs_value"),
                "high_first_seen_round": tree.get("high_first_seen_round"),
                "low_bound_reasons": tree.get("low_bound_reasons", []),
            }
        ]
    blockers: List[Dict[str, object]] = []
    parents = tree.get("parents")
    if isinstance(parents, list):
        for parent in parents:
            if isinstance(parent, dict):
                blockers.extend(_nearest_bound_blockers(parent))
    return _dedupe_value_rows(blockers)


def _target_payload(
    target: Fraction,
    *,
    high_rows: Dict[Fraction, Dict[str, object]],
    low_rows: Dict[Fraction, Dict[str, object]],
    high_report: Dict[str, object],
    low_report: Dict[str, object],
    ancestry_depth: int,
) -> Dict[str, object]:
    low_config = _config(low_report)
    high_row = high_rows.get(target)
    low_row = low_rows.get(target)
    tree = _ancestry_tree(
        target,
        high_rows=high_rows,
        low_rows=low_rows,
        low_config=low_config,
        depth=ancestry_depth,
        seen=set(),
    )
    tree_rows = _dedupe_value_rows(_walk_tree(tree))
    hard_bound_blockers = [
        {
            "frac": row.get("frac"),
            "abs_value": row.get("abs_value"),
            "high_first_seen_round": row.get("high_first_seen_round"),
            "low_bound_reasons": row.get("low_bound_reasons", []),
        }
        for row in tree_rows
        if not bool(row.get("allowed_by_low_bounds", True))
    ]
    missing_allowed_values = [
        {
            "frac": row.get("frac"),
            "abs_value": row.get("abs_value"),
            "high_first_seen_round": row.get("high_first_seen_round"),
        }
        for row in tree_rows
        if bool(row.get("allowed_by_low_bounds", False)) and not bool(row.get("present_in_low", False))
    ]
    round_delays = [
        {
            "frac": row.get("frac"),
            "high_first_seen_round": row.get("high_first_seen_round"),
            "low_first_seen_round": row.get("low_first_seen_round"),
            "low_round_delay": row.get("low_round_delay"),
        }
        for row in tree_rows
        if row.get("low_round_delay") is not None and int(row.get("low_round_delay", 0)) > 0
    ]
    allowed_by_low, low_bound_reasons = _allowed_by_config(target, low_config)
    return {
        "target": _format_fraction(target),
        "target_present_in_high": high_row is not None,
        "target_present_in_low": low_row is not None,
        "target_allowed_by_low_bounds": bool(allowed_by_low),
        "target_low_bound_reasons": low_bound_reasons,
        "high_first_seen_round": _row_int(high_row, "first_seen_round", -1),
        "low_first_seen_round": _row_int(low_row, "first_seen_round", -1),
        "high_first_witness": _witness_payload(high_row),
        "low_first_witness": _witness_payload(low_row),
        "baseline_edge_under_low": _baseline_edge_diagnosis(
            target, high_rows=high_rows, low_rows=low_rows, low_report=low_report
        ),
        "nearest_bound_blockers": _nearest_bound_blockers(tree),
        "hard_bound_blockers_in_high_ancestry": hard_bound_blockers,
        "missing_allowed_values_in_high_ancestry": missing_allowed_values,
        "round_delays_in_high_ancestry": round_delays,
        "high_ancestry_compared_to_low": tree,
        "source_reports": {
            "high": str(high_report.get("method", {}).get("source_report", "")),
            "low": str(low_report.get("method", {}).get("source_report", "")),
        },
    }


def _grid_presence(
    *,
    experiments_dir: Path,
    targets: Sequence[Fraction],
) -> Tuple[List[Dict[str, object]], List[str]]:
    rows: List[Dict[str, object]] = []
    missing_reports: List[str] = []
    for cell in DEFAULT_GRID:
        path = experiments_dir / cell.report_name
        if not path.exists():
            missing_reports.append(str(path))
            continue
        report = _load_report(path)
        by_frac = _rows_by_frac(report)
        final = report.get("final") if isinstance(report.get("final"), dict) else {}
        row: Dict[str, object] = {
            "q_cap": int(cell.q_cap),
            "value_cap": float(cell.value_cap),
            "report": str(path),
            "source_size": _row_int(final, "size", 0),
            "targets": {},
        }
        target_rows: Dict[str, object] = {}
        for target in targets:
            ledger_row = by_frac.get(target)
            target_rows[_format_fraction(target)] = {
                "present": ledger_row is not None,
                "first_seen_round": _row_int(ledger_row, "first_seen_round", -1),
                "first_witness": _witness_payload(ledger_row),
            }
        row["targets"] = target_rows
        rows.append(row)
    return rows, missing_reports


def _minimum_observed_value_caps(grid: Sequence[Dict[str, object]], targets: Sequence[Fraction]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for target in targets:
        label = _format_fraction(target)
        target_rows: List[Dict[str, object]] = []
        for row in grid:
            targets_payload = row.get("targets")
            if not isinstance(targets_payload, dict):
                continue
            target_payload = targets_payload.get(label)
            if not isinstance(target_payload, dict) or not bool(target_payload.get("present")):
                continue
            target_rows.append(
                {
                    "q_cap": row.get("q_cap"),
                    "value_cap": row.get("value_cap"),
                    "first_seen_round": target_payload.get("first_seen_round"),
                }
            )
        min_cap = min((float(row["value_cap"]) for row in target_rows), default=None)
        out[label] = {
            "minimum_observed_value_cap": min_cap,
            "present_cells": target_rows,
        }
    return out


def build_report(
    *,
    experiments_dir: Path,
    low_report_path: Path,
    high_report_path: Path,
    targets: Sequence[Fraction],
    ancestry_depth: int,
) -> Dict[str, object]:
    low_report = _load_report(low_report_path)
    high_report = _load_report(high_report_path)
    low_report.setdefault("method", {})
    high_report.setdefault("method", {})
    if isinstance(low_report["method"], dict):
        low_report["method"]["source_report"] = str(low_report_path)
    if isinstance(high_report["method"], dict):
        high_report["method"]["source_report"] = str(high_report_path)
    low_rows = _rows_by_frac(low_report)
    high_rows = _rows_by_frac(high_report)
    grid, missing_grid_reports = _grid_presence(experiments_dir=experiments_dir, targets=targets)
    per_target = [
        _target_payload(
            target,
            high_rows=high_rows,
            low_rows=low_rows,
            high_report=high_report,
            low_report=low_report,
            ancestry_depth=ancestry_depth,
        )
        for target in targets
    ]
    missing_allowed = [
        row["target"]
        for row in per_target
        if not bool(row["target_present_in_low"]) and bool(row["target_allowed_by_low_bounds"])
    ]
    value_excluded = [
        row["target"]
        for row in per_target
        if not bool(row["target_present_in_low"]) and not bool(row["target_allowed_by_low_bounds"])
    ]
    present_low = [row["target"] for row in per_target if bool(row["target_present_in_low"])]
    return {
        "schema_version": 1,
        "method": {
            "source": "Compare saved native emergence ledgers without recomputing closure.",
            "low_report": str(low_report_path),
            "high_report": str(high_report_path),
            "ancestry_depth": int(ancestry_depth),
            "closure_rule": "Each round combines the previous delta with the previous retained set.",
            "interpretation": (
                "A value can be absent under a tighter value cap because the final value is excluded, "
                "because a witness parent is excluded, or because a parent is delayed beyond the round budget."
            ),
        },
        "comparison": {
            "low_config": _config(low_report),
            "high_config": _config(high_report),
            "low_round_budget": _round_budget(low_report),
            "high_round_budget": _round_budget(high_report),
            "targets": [_format_fraction(target) for target in targets],
        },
        "summary": {
            "present_under_low": present_low,
            "missing_but_low_value_allowed": missing_allowed,
            "missing_because_target_value_excluded": value_excluded,
            "minimum_observed_value_caps": _minimum_observed_value_caps(grid, targets),
            "missing_grid_reports": missing_grid_reports,
        },
        "targets": per_target,
        "grid": grid,
    }


def _parse_targets(raw: str) -> Tuple[Fraction, ...]:
    targets: List[Fraction] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        targets.append(Fraction(chunk))
    if not targets:
        raise SystemExit("No targets provided.")
    return tuple(targets)


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Audit why MoO approximants cross the |v| <= 3 to |v| <= 4 witness threshold."
    )
    parser.add_argument("--experiments-dir", type=str, default="out/experiments")
    parser.add_argument("--low-report", type=str, default="out/experiments/native_r5_v3.json")
    parser.add_argument("--high-report", type=str, default="out/experiments/native_r5_full.json")
    parser.add_argument("--targets", type=str, default=",".join(DEFAULT_TARGETS))
    parser.add_argument("--ancestry-depth", type=int, default=4)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = build_report(
        experiments_dir=Path(str(args.experiments_dir)),
        low_report_path=Path(str(args.low_report)),
        high_report_path=Path(str(args.high_report)),
        targets=_parse_targets(str(args.targets)),
        ancestry_depth=max(0, int(args.ancestry_depth)),
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
