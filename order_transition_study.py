from __future__ import annotations

import argparse
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple


OPS = ("+", "-", "*", "/")


def format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(int(value.numerator))
    return f"{int(value.numerator)}/{int(value.denominator)}"


def parse_fraction(raw: str) -> Fraction:
    text = raw.strip()
    if not text:
        raise ValueError("empty fraction")
    return Fraction(text)


def classify_value(value: Fraction, *, stage: int) -> Dict[str, object]:
    if value == 1:
        return {
            "order": 1,
            "status": "certainty",
            "reason": "1 is the only certainty",
        }

    if value.denominator == 1 and value.numerator > 1:
        n = int(value.numerator)
        if n <= stage:
            return {
                "order": 2,
                "status": "confirmed_positive_spine_iteration",
                "reason": f"positive spine has reached {n}",
            }
        return {
            "order": 3,
            "status": "not_yet_positive_spine_iteration",
            "reason": f"positive spine has only reached {stage}",
        }

    if value.denominator == 1:
        return {
            "order": 3,
            "status": "relational_removal_integer",
            "reason": "not confirmed by the current positive-spine rule",
        }

    return {
        "order": 3,
        "status": "unconfirmed_rational_construction",
        "reason": "fractions are constructions, not confirmed positive-spine iterations",
    }


def operation_value(op: str, a: Fraction, b: Fraction) -> Optional[Fraction]:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            return None
        return a / b
    raise ValueError(f"unknown op: {op}")


def stage_operations(stage: int) -> List[Tuple[str, Fraction, Fraction, Fraction]]:
    if stage < 2:
        return []
    operands = [Fraction(n, 1) for n in range(1, stage + 1)]
    events: List[Tuple[str, Fraction, Fraction, Fraction]] = []
    for a in operands:
        for b in operands:
            for op in OPS:
                out = operation_value(op, a, b)
                if out is None:
                    continue
                events.append((op, a, b, out))
    return events


def summarize_values(values: Iterable[Fraction], *, stage: int, limit: int) -> List[Dict[str, object]]:
    ordered = sorted(set(values), key=lambda v: (abs(v.numerator) + abs(v.denominator), v.denominator, v.numerator))
    rows: List[Dict[str, object]] = []
    for value in ordered[: max(0, limit)]:
        row = {
            "value": format_fraction(value),
            "p": int(value.numerator),
            "q": int(value.denominator),
        }
        row.update(classify_value(value, stage=stage))
        rows.append(row)
    return rows


def stage_indexed_report(
    *,
    max_stage: int,
    sample_size: int,
    inspect_values: Sequence[Fraction],
) -> Dict[str, object]:
    if max_stage < 1:
        raise ValueError("max_stage must be >= 1")

    first_constructed_stage: Dict[Fraction, int] = {}
    first_witnesses: DefaultDict[Fraction, List[str]] = defaultdict(list)
    stages: List[Dict[str, object]] = []

    for stage in range(1, max_stage + 1):
        events = stage_operations(stage)
        by_status: DefaultDict[str, List[Fraction]] = defaultdict(list)
        new_future_wholes: List[Fraction] = []

        for op, a, b, out in events:
            if out not in first_constructed_stage:
                first_constructed_stage[out] = stage
            if first_constructed_stage[out] == stage and len(first_witnesses[out]) < 4:
                first_witnesses[out].append(
                    f"{format_fraction(a)} {op} {format_fraction(b)}"
                )
            classification = classify_value(out, stage=stage)
            status = str(classification["status"])
            by_status[status].append(out)
            if status == "not_yet_core_iteration":
                if first_constructed_stage[out] == stage:
                    new_future_wholes.append(out)

        promoted: List[Dict[str, object]] = []
        stage_value = Fraction(stage, 1)
        if stage > 1 and first_constructed_stage.get(stage_value, stage) < stage:
            promoted.append(
                {
                    "value": format_fraction(stage_value),
                    "first_constructed_stage": int(first_constructed_stage[stage_value]),
                    "confirmed_stage": int(stage),
                    "first_witnesses": first_witnesses.get(stage_value, []),
                }
            )

        inspected_rows: List[Dict[str, object]] = []
        for value in inspect_values:
            row = {
                "value": format_fraction(value),
                "first_constructed_stage": first_constructed_stage.get(value),
                "first_witnesses": first_witnesses.get(value, []),
            }
            row.update(classify_value(value, stage=stage))
            inspected_rows.append(row)

        stages.append(
            {
                "stage": int(stage),
                "universe": [str(n) for n in range(1, stage + 1)],
                "new_core_loop_value": "1" if stage == 1 else str(stage),
                "construction_events": len(events),
                "unique_constructed_values": len({out for _, _, _, out in events}),
                "promoted_by_core_loop": promoted,
                "new_unconfirmed_future_wholes": summarize_values(
                    new_future_wholes,
                    stage=stage,
                    limit=sample_size,
                ),
                "unconfirmed_future_wholes": summarize_values(
                    by_status.get("not_yet_core_iteration", []),
                    stage=stage,
                    limit=sample_size,
                ),
                "unconfirmed_rationals": summarize_values(
                    by_status.get("unconfirmed_rational_construction", []),
                    stage=stage,
                    limit=sample_size,
                ),
                "relational_removal_integers": summarize_values(
                    by_status.get("relational_removal_integer", []),
                    stage=stage,
                    limit=sample_size,
                ),
                "inspected_values": inspected_rows,
            }
        )

    return {
        "framing": {
            "certainty": "1",
            "stage_rule": "U_n confirms positive-spine iterations 1..n",
            "construction_rule": (
                "operations over confirmed stage values may produce speculative "
                "results before the positive spine confirms them; those speculative "
                "results are inspected, not operated on"
            ),
        },
        "max_stage": int(max_stage),
        "sample_size": int(sample_size),
        "stages": stages,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect MoO stage-indexed confirmation versus speculative construction."
    )
    parser.add_argument("--max-stage", type=int, default=6)
    parser.add_argument("--sample-size", type=int, default=12)
    parser.add_argument(
        "--inspect",
        default="2,3,6,3/2,0,-1",
        help="Comma-separated values to classify at each stage.",
    )
    parser.add_argument("--write", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    inspect_values = [
        parse_fraction(part)
        for part in str(args.inspect).split(",")
        if part.strip()
    ]
    report = stage_indexed_report(
        max_stage=int(args.max_stage),
        sample_size=int(args.sample_size),
        inspect_values=inspect_values,
    )
    text = json.dumps(report, indent=2 if args.pretty else None, sort_keys=True)
    print(text)
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
