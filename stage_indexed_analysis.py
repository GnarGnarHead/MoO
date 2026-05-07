from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, int):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _witness_ops(witnesses: Iterable[object]) -> Set[str]:
    ops: Set[str] = set()
    for witness in witnesses:
        if not isinstance(witness, str):
            continue
        parts = witness.split()
        if len(parts) >= 3:
            ops.add(parts[1])
    return ops


def _route_type(ops: Set[str]) -> str:
    if "*" in ops:
        return "multiplicative"
    if "+" in ops:
        return "additive"
    if "/" in ops:
        return "division"
    if "-" in ops:
        return "subtractive"
    return "unknown"


def _promotion_rows(report: Dict[str, object]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    stages = report.get("stages")
    if not isinstance(stages, list):
        return rows

    for stage in stages:
        if not isinstance(stage, dict):
            continue
        promotions = stage.get("promoted_by_core_loop")
        if not isinstance(promotions, list):
            continue
        for item in promotions:
            if not isinstance(item, dict):
                continue
            value = str(item.get("value", ""))
            first_stage = _as_int(item.get("first_constructed_stage"))
            confirmed_stage = _as_int(item.get("confirmed_stage"))
            witnesses = item.get("first_witnesses")
            witness_list = witnesses if isinstance(witnesses, list) else []
            ops = _witness_ops(witness_list)
            gap = confirmed_stage - first_stage
            ratio = float(confirmed_stage / first_stage) if first_stage > 0 else 0.0
            rows.append(
                {
                    "value": value,
                    "first_constructed_stage": first_stage,
                    "confirmed_stage": confirmed_stage,
                    "promotion_gap": gap,
                    "compression_ratio": ratio,
                    "route_type": _route_type(ops),
                    "witness_ops": sorted(ops),
                    "first_witnesses": witness_list,
                }
            )
    return rows


def _stage_samples(stages: Sequence[object], sample_points: Sequence[int]) -> List[Dict[str, object]]:
    by_stage = {
        _as_int(stage.get("stage")): stage
        for stage in stages
        if isinstance(stage, dict)
    }
    rows: List[Dict[str, object]] = []
    for point in sample_points:
        stage = by_stage.get(int(point))
        if not isinstance(stage, dict):
            continue
        events = _as_int(stage.get("construction_events"))
        unique_values = _as_int(stage.get("unique_constructed_values"))
        rows.append(
            {
                "stage": int(point),
                "construction_events": events,
                "unique_constructed_values": unique_values,
                "unique_per_event": float(unique_values / events) if events else 0.0,
            }
        )
    return rows


def analyze_stage_indexed_report(report: Dict[str, object]) -> Dict[str, object]:
    stages_obj = report.get("stages")
    stages = stages_obj if isinstance(stages_obj, list) else []
    final_stage = stages[-1] if stages and isinstance(stages[-1], dict) else {}
    max_stage = _as_int(report.get("max_stage"), _as_int(final_stage.get("stage")))
    promotions = _promotion_rows(report)

    top_by_gap = sorted(
        promotions,
        key=lambda row: (-int(row["promotion_gap"]), int(row["first_constructed_stage"]), row["value"]),
    )[:12]
    top_by_ratio = sorted(
        promotions,
        key=lambda row: (-float(row["compression_ratio"]), int(row["confirmed_stage"]), row["value"]),
    )[:12]

    route_counts: Dict[str, int] = {}
    for row in promotions:
        route = str(row["route_type"])
        route_counts[route] = route_counts.get(route, 0) + 1

    additive_rows = [row for row in promotions if row["route_type"] == "additive"]
    multiplicative_rows = [row for row in promotions if row["route_type"] == "multiplicative"]

    inspected = final_stage.get("inspected_values")
    inspected_rows = inspected if isinstance(inspected, list) else []

    sample_points = sorted({1, 2, 3, 4, 5, 10, 12, 25, 50, max_stage})
    return {
        "source_max_stage": max_stage,
        "stage_count": len(stages),
        "final_stage": {
            "stage": _as_int(final_stage.get("stage")),
            "construction_events": _as_int(final_stage.get("construction_events")),
            "unique_constructed_values": _as_int(final_stage.get("unique_constructed_values")),
            "unique_per_event": (
                float(
                    _as_int(final_stage.get("unique_constructed_values"))
                    / _as_int(final_stage.get("construction_events"))
                )
                if _as_int(final_stage.get("construction_events")) > 0
                else 0.0
            ),
        },
        "stage_samples": _stage_samples(stages, sample_points),
        "promotions": {
            "count": len(promotions),
            "route_counts": route_counts,
            "additive_only_values": [row["value"] for row in additive_rows],
            "multiplicative_values_count": len(multiplicative_rows),
            "top_by_gap": top_by_gap,
            "top_by_compression_ratio": top_by_ratio,
        },
        "final_inspected_values": inspected_rows,
        "interpretation": {
            "core_compute_rule": (
                "confirmed core-loop iterations are operands; speculative outputs "
                "are recorded as real nodes, inspected, and not operated on until promotion"
            ),
            "promotion_gap": "confirmed_stage - first_constructed_stage",
            "additive_only_hint": "addition-only promotions mark values with no earlier multiplicative witness in the current stage range",
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize a stage-indexed MoO core report.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--write", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    summary = analyze_stage_indexed_report(report)
    text = json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True)
    print(text)
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
