from __future__ import annotations

import argparse
import json
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


INSPECTED = ("22/7", "87/32", "52/75", "99/70", "34/21")


@dataclass(frozen=True)
class GridCell:
    q_cap: int
    value_cap: float
    report_name: str


DEFAULT_GRID = (
    GridCell(80, 3.0, "motif_persistence_r5_q80_v3.json"),
    GridCell(80, 4.0, "motif_persistence_r5_q80.json"),
    GridCell(80, 5.0, "motif_persistence_r5_q80_v5.json"),
    GridCell(90, 3.0, "motif_persistence_r5_q90_v3.json"),
    GridCell(90, 4.0, "motif_persistence_r5_q90_v4.json"),
    GridCell(90, 5.0, "motif_persistence_r5_q90_v5.json"),
    GridCell(100, 3.0, "motif_persistence_r5_v3.json"),
    GridCell(100, 4.0, "motif_persistence_r5.json"),
    GridCell(100, 5.0, "motif_persistence_r5_v5.json"),
)


def _load_json(path: Path) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Report is not a JSON object: {path}")
    return payload


def _rate(payload: Dict[str, object], key: str) -> float:
    try:
        return float(payload.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _int(payload: Dict[str, object], key: str) -> int:
    try:
        return int(payload.get(key, 0))
    except (TypeError, ValueError):
        return 0


def _top_parent(report: Dict[str, object]) -> Dict[str, object]:
    rankings = report.get("rankings")
    if not isinstance(rankings, dict):
        return {}
    rows = rankings.get("final_major_parent_hubs")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return {}
    row = rows[0]
    return {
        "frac": row.get("frac"),
        "child_count": _int(row, "child_count"),
        "nontrivial_child_count": _int(row, "nontrivial_child_count"),
        "active_rounds": row.get("active_rounds", []),
        "inspected_children": row.get("inspected_children", []),
    }


def _minus_four_thirds(report: Dict[str, object]) -> Optional[Dict[str, object]]:
    rankings = report.get("rankings")
    if not isinstance(rankings, dict):
        return None
    rows = rankings.get("final_major_parent_hubs")
    if not isinstance(rows, list):
        return None
    for idx, row in enumerate(rows, start=1):
        if isinstance(row, dict) and row.get("frac") == "-4/3":
            return {
                "rank": idx,
                "child_count": _int(row, "child_count"),
                "nontrivial_child_count": _int(row, "nontrivial_child_count"),
                "active_rounds": row.get("active_rounds", []),
                "inspected_children": row.get("inspected_children", []),
            }
    return None


def _inspected_edges(report: Dict[str, object]) -> Tuple[Dict[str, str], List[str], List[str]]:
    inspected = report.get("inspected")
    if not isinstance(inspected, dict):
        return {}, [], list(INSPECTED)
    edges: Dict[str, str] = {}
    present: List[str] = []
    missing: List[str] = []
    for value in INSPECTED:
        row = inspected.get(value)
        if not isinstance(row, dict) or not bool(row.get("present")):
            missing.append(value)
            continue
        present.append(value)
        edge = row.get("first_witness_edge")
        if isinstance(edge, dict) and edge.get("motif") is not None:
            edges[value] = str(edge["motif"])
    return edges, present, missing


def _concentration(report: Dict[str, object], group: str) -> Dict[str, object]:
    concentration = report.get("concentration")
    if not isinstance(concentration, dict):
        return {}
    row = concentration.get(group)
    if not isinstance(row, dict):
        return {}
    return {
        "size": _int(row, "size"),
        "major_parent_hits": _int(row, "major_parent_hits"),
        "major_parent_rate": _rate(row, "major_parent_rate"),
        "major_motif_hits": _int(row, "major_motif_hits"),
        "major_motif_rate": _rate(row, "major_motif_rate"),
        "any_major_hits": _int(row, "any_major_hits"),
        "any_major_rate": _rate(row, "any_major_rate"),
    }


def build_summary(experiments_dir: Path) -> Dict[str, object]:
    reports: Dict[Tuple[int, float], Dict[str, object]] = {}
    for cell in DEFAULT_GRID:
        path = experiments_dir / cell.report_name
        if not path.exists():
            raise SystemExit(f"Missing persistence report for q={cell.q_cap}, v={cell.value_cap}: {path}")
        reports[(cell.q_cap, cell.value_cap)] = _load_json(path)

    baseline = reports[(100, 4.0)]
    baseline_edges, _, _ = _inspected_edges(baseline)
    cells: List[Dict[str, object]] = []

    for cell in DEFAULT_GRID:
        report = reports[(cell.q_cap, cell.value_cap)]
        source_final = report.get("source_final") if isinstance(report.get("source_final"), dict) else {}
        edges, present, missing = _inspected_edges(report)
        matching_edges = {
            value: motif
            for value, motif in edges.items()
            if baseline_edges.get(value) == motif
        }
        inspected_conc = _concentration(report, "inspected")
        control_conc = _concentration(report, "matched_controls")
        m43 = _minus_four_thirds(report)
        cells.append(
            {
                "q_cap": int(cell.q_cap),
                "value_cap": float(cell.value_cap),
                "report": str(experiments_dir / cell.report_name),
                "source_size": _int(source_final, "size"),
                "first_seen_counts": source_final.get("first_seen_counts", {}),
                "inspected_present_count": len(present),
                "inspected_missing_count": len(missing),
                "inspected_present": present,
                "inspected_missing": missing,
                "inspected_edges": edges,
                "baseline_edge_match_count": len(matching_edges),
                "all_baseline_edges_matched": len(matching_edges) == len(INSPECTED),
                "top_final_parent": _top_parent(report),
                "minus_four_thirds": m43,
                "minus_four_thirds_is_top_parent": bool(m43 and int(m43["rank"]) == 1),
                "inspected_concentration": inspected_conc,
                "matched_control_concentration": control_conc,
            }
        )

    full_survival = [
        row
        for row in cells
        if int(row["inspected_present_count"]) == len(INSPECTED)
        and bool(row["minus_four_thirds_is_top_parent"])
        and bool(row["all_baseline_edges_matched"])
    ]
    value_cap_3 = [row for row in cells if float(row["value_cap"]) == 3.0]
    value_cap_4_or_5 = [row for row in cells if float(row["value_cap"]) >= 4.0]

    return {
        "schema_version": 1,
        "method": {
            "source": "motif_persistence_study.py reports over a 3x3 bounded replay grid",
            "q_caps": [80, 90, 100],
            "value_caps": [3.0, 4.0, 5.0],
            "rounds": 5,
            "max_abs_p": 100,
            "baseline_cell": {"q_cap": 100, "value_cap": 4.0},
            "inspected_fracs": list(INSPECTED),
        },
        "baseline_inspected_edges": baseline_edges,
        "summary": {
            "cells": len(cells),
            "full_survival_cells": len(full_survival),
            "full_survival_cells_detail": [
                {"q_cap": row["q_cap"], "value_cap": row["value_cap"]}
                for row in full_survival
            ],
            "value_cap_3_present_counts": [
                {
                    "q_cap": row["q_cap"],
                    "present": row["inspected_present_count"],
                    "missing": row["inspected_missing"],
                }
                for row in value_cap_3
            ],
            "value_cap_4_or_5_all_present": all(
                int(row["inspected_present_count"]) == len(INSPECTED)
                for row in value_cap_4_or_5
            ),
            "minus_four_thirds_top_parent_all_cells": all(
                bool(row["minus_four_thirds_is_top_parent"]) for row in cells
            ),
        },
        "cells": cells,
    }


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Summarize a 3x3 MoO motif persistence bounded replay grid."
    )
    parser.add_argument("--experiments-dir", type=str, default="out/experiments")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = build_summary(Path(str(args.experiments_dir)))
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
