from __future__ import annotations

import argparse
import json
import signal
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo_targets import KNOWN_TARGETS


DEFAULT_PROBES = {
    "pi": "22/7",
    "e": "87/32",
    "ln2": "52/75",
    "sqrt2": "99/70",
    "phi": "34/21",
}


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


def _load_report(path: Path, *, require_ledger: bool = False) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Report is not a JSON object: {path}")
    if require_ledger and not isinstance(payload.get("ledger"), list):
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


def _is_unit_fraction(value: Fraction) -> bool:
    return value.denominator > 1 and abs(value.numerator) == 1


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


def _parents_from_witness(row: Optional[Dict[str, object]]) -> Tuple[Optional[str], Optional[Fraction], Optional[Fraction]]:
    witness = _witness_payload(row)
    if witness is None:
        return None, None, None
    op_raw = witness.get("op")
    op = str(op_raw) if op_raw is not None else None
    return op, _parse_fraction(witness.get("a")), _parse_fraction(witness.get("b"))


def _operation_signature(row: Optional[Dict[str, object]]) -> Dict[str, int]:
    signature = row.get("operation_signature") if isinstance(row, dict) else None
    if not isinstance(signature, dict):
        return {op: 0 for op in ["+", "-", "*", "/"]}
    return {op: _row_int(signature, op, 0) for op in ["+", "-", "*", "/"]}


def _operation_shares(row: Optional[Dict[str, object]]) -> Dict[str, float]:
    signature = _operation_signature(row)
    total = sum(signature.values())
    if total <= 0:
        return {op: 0.0 for op in ["+", "-", "*", "/"]}
    return {op: float(signature[op] / total) for op in ["+", "-", "*", "/"]}


def _safe_target_value(name: str) -> Optional[float]:
    target = KNOWN_TARGETS.get(name)
    return float(target.value) if target is not None else None


def _external_probe_payload(name: str, value: Fraction) -> Dict[str, object]:
    target_value = _safe_target_value(name)
    payload: Dict[str, object] = {
        "name": name,
        "selected_speculative_node": _format_fraction(value),
        "target_value": target_value,
        "selected_value": float(value),
    }
    if target_value is not None:
        error = abs(float(value) - target_value)
        payload["absolute_error"] = error
        payload["relative_error"] = error / abs(target_value) if target_value != 0 else None
    return payload


def _compact_hub_payload(hub: Dict[str, object]) -> Dict[str, object]:
    return {
        "frac": hub.get("frac"),
        "kind": hub.get("kind"),
        "first_seen_round": hub.get("first_seen_round"),
        "derivation_events": hub.get("derivation_events"),
        "child_count": hub.get("child_count"),
        "nontrivial_child_count": hub.get("nontrivial_child_count"),
        "operation_counts": hub.get("operation_counts"),
        "inspected_children": hub.get("inspected_children"),
    }


def _compact_pair_payload(pair: Dict[str, object]) -> Dict[str, object]:
    return {
        "parents": pair.get("parents"),
        "parent_kinds": pair.get("parent_kinds"),
        "child_count": pair.get("child_count"),
        "operation_counts": pair.get("operation_counts"),
        "inspected_children": pair.get("inspected_children"),
    }


def _compact_motif_payload(motif: Dict[str, object]) -> Dict[str, object]:
    return {
        "motif": motif.get("motif"),
        "child_count": motif.get("child_count"),
        "operation_counts": motif.get("operation_counts"),
        "inspected_children": motif.get("inspected_children"),
    }


def _major_items_for_child(
    rankings: Dict[str, object],
    key: str,
    child: str,
) -> List[Dict[str, object]]:
    items = rankings.get(key)
    if not isinstance(items, list):
        return []
    out: List[Dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        inspected = item.get("inspected_children")
        if isinstance(inspected, list) and child in {str(entry) for entry in inspected}:
            if key == "operation_motifs":
                out.append(_compact_motif_payload(item))
            elif "pair" in key:
                out.append(_compact_pair_payload(item))
            else:
                out.append(_compact_hub_payload(item))
    return out


def _motif_context(
    value: Fraction,
    *,
    motif_report: Optional[Dict[str, object]],
) -> Dict[str, object]:
    if motif_report is None:
        return {}
    frac = _format_fraction(value)
    inspected_all = motif_report.get("inspected")
    inspected = inspected_all.get(frac) if isinstance(inspected_all, dict) else None
    rankings_raw = motif_report.get("rankings")
    rankings = rankings_raw if isinstance(rankings_raw, dict) else {}
    context: Dict[str, object] = {
        "present_in_motif_report": isinstance(inspected, dict),
        "major_operation_motifs": _major_items_for_child(rankings, "operation_motifs", frac),
        "major_parent_hubs": _major_items_for_child(rankings, "nontrivial_parent_hubs", frac),
        "major_parent_pair_motifs": _major_items_for_child(rankings, "nontrivial_parent_pair_motifs", frac),
        "shared_parent_pairs_for_inspected": _major_items_for_child(
            rankings, "shared_parent_pairs_for_inspected", frac
        ),
    }
    if isinstance(inspected, dict):
        hubs = inspected.get("direct_parent_hubs")
        ancestors = inspected.get("nontrivial_ancestors")
        context["direct_parent_hubs"] = [
            _compact_hub_payload(hub) for hub in hubs if isinstance(hub, dict)
        ] if isinstance(hubs, list) else []
        context["nontrivial_ancestors"] = [
            {
                "frac": item.get("frac"),
                "first_seen_round": item.get("first_seen_round"),
                "derivation_events": item.get("derivation_events"),
            }
            for item in ancestors
            if isinstance(item, dict)
        ] if isinstance(ancestors, list) else []
        context["ancestor_count"] = inspected.get("ancestor_count")
    return context


def _aperture_context(
    value: Fraction,
    *,
    aperture_report: Optional[Dict[str, object]],
) -> Dict[str, object]:
    if aperture_report is None:
        return {}
    inspected_all = aperture_report.get("inspected")
    if not isinstance(inspected_all, dict):
        return {}
    row = inspected_all.get(_format_fraction(value))
    if not isinstance(row, dict):
        return {}
    cap_status: Dict[str, object] = {}
    cap_checks = row.get("cap_checks")
    if isinstance(cap_checks, list):
        for check in cap_checks:
            if not isinstance(check, dict):
                continue
            cap = str(check.get("cap_frac"))
            cap_status[cap] = {
                "final_fits_cap": check.get("final_fits_cap"),
                "ancestry_fits_cap": check.get("ancestry_fits_cap"),
                "escape_and_return": check.get("escape_and_return"),
                "blocker_count": check.get("blocker_count"),
                "max_blockers": check.get("max_blockers"),
            }
    return {
        "first_witness_aperture": row.get("first_witness_aperture"),
        "aperture_excess": row.get("aperture_excess"),
        "aperture_ratio": row.get("aperture_ratio"),
        "first_witness_ancestry_size": row.get("first_witness_ancestry_size"),
        "cap_status": cap_status,
    }


def _threshold_context(
    value: Fraction,
    *,
    threshold_report: Optional[Dict[str, object]],
) -> Dict[str, object]:
    if threshold_report is None:
        return {}
    target = _format_fraction(value)
    targets = threshold_report.get("targets")
    if not isinstance(targets, list):
        return {}
    for item in targets:
        if not isinstance(item, dict) or item.get("target") != target:
            continue
        baseline = item.get("baseline_edge_under_low")
        return {
            "target_present_in_low_cap": item.get("target_present_in_low"),
            "target_allowed_by_low_bounds": item.get("target_allowed_by_low_bounds"),
            "target_low_bound_reasons": item.get("target_low_bound_reasons"),
            "nearest_bound_blockers": item.get("nearest_bound_blockers"),
            "round_delays_in_high_ancestry": item.get("round_delays_in_high_ancestry"),
            "baseline_edge_under_low": {
                "same_witness_possible_in_low_budget": baseline.get("same_witness_possible_in_low_budget"),
                "reasons": baseline.get("reasons"),
            } if isinstance(baseline, dict) else None,
        }
    return {}


def _value_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    op, a, b = _parents_from_witness(row)
    parent_values = [parent for parent in (a, b) if parent is not None]
    return {
        "frac": _format_fraction(value),
        "present": row is not None,
        "p": int(value.numerator),
        "q": int(value.denominator),
        "value": float(value),
        "kind": _kind(value),
        "denominator_bucket": _denominator_bucket(value.denominator),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "first_witness": _witness_payload(row),
        "first_witness_op": op,
        "first_witness_parent_kinds": [_kind(parent) for parent in parent_values],
        "derivation_events": _row_int(row, "derivation_events", 0),
        "operation_signature": _operation_signature(row),
        "operation_shares": _operation_shares(row),
    }


def _parse_probes(raw: str) -> List[Tuple[str, Fraction]]:
    probes: List[Tuple[str, Fraction]] = []
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise SystemExit("No probes specified.")
    for part in parts:
        if "=" not in part:
            raise SystemExit(f"Probe must be name=fraction, got: {part}")
        name, frac_raw = [piece.strip() for piece in part.split("=", 1)]
        frac = _parse_fraction(frac_raw)
        if not name or frac is None:
            raise SystemExit(f"Invalid probe: {part}")
        probes.append((name, frac))
    return probes


def _default_probe_arg() -> str:
    return ",".join(f"{name}={frac}" for name, frac in DEFAULT_PROBES.items())


def _binding_signature(row: Dict[str, object]) -> Dict[str, object]:
    value = row.get("value_payload")
    motif = row.get("motif_context")
    aperture = row.get("aperture_context")
    if not isinstance(value, dict):
        value = {}
    if not isinstance(motif, dict):
        motif = {}
    if not isinstance(aperture, dict):
        aperture = {}
    direct_hubs = motif.get("direct_parent_hubs")
    major_motifs = motif.get("major_operation_motifs")
    aperture_payload = aperture.get("first_witness_aperture")
    cap_status = aperture.get("cap_status")
    cap3 = cap_status.get("3") if isinstance(cap_status, dict) else None
    return {
        "first_seen_round": value.get("first_seen_round"),
        "first_witness_op": value.get("first_witness_op"),
        "parent_kinds": value.get("first_witness_parent_kinds"),
        "denominator_bucket": value.get("denominator_bucket"),
        "first_witness_aperture": aperture_payload.get("frac") if isinstance(aperture_payload, dict) else None,
        "cap3_escape_and_return": cap3.get("escape_and_return") if isinstance(cap3, dict) else None,
        "direct_parent_hubs": [
            hub.get("frac") for hub in direct_hubs if isinstance(hub, dict)
        ] if isinstance(direct_hubs, list) else [],
        "major_operation_motifs": [
            item.get("motif") for item in major_motifs if isinstance(item, dict)
        ] if isinstance(major_motifs, list) else [],
    }


def _summary(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    first_seen = Counter()
    witness_ops = Counter()
    buckets = Counter()
    apertures = Counter()
    cap3 = Counter()
    direct_hubs = Counter()
    major_motifs = Counter()
    for row in rows:
        signature = row.get("binding_signature")
        if not isinstance(signature, dict):
            continue
        first_seen[str(signature.get("first_seen_round"))] += 1
        witness_ops[str(signature.get("first_witness_op"))] += 1
        buckets[str(signature.get("denominator_bucket"))] += 1
        apertures[str(signature.get("first_witness_aperture"))] += 1
        escape = signature.get("cap3_escape_and_return")
        value = row.get("value_payload")
        final_status = "unknown"
        if isinstance(value, dict):
            val = value.get("value")
            try:
                final_status = "final_outside_cap3" if abs(float(val)) > 3 else "final_inside_cap3"
            except (TypeError, ValueError):
                pass
        if escape is True:
            cap3["escape_and_return"] += 1
        elif escape is False:
            cap3[final_status] += 1
        else:
            cap3["unknown"] += 1
        for hub in signature.get("direct_parent_hubs", []):
            direct_hubs[str(hub)] += 1
        for motif in signature.get("major_operation_motifs", []):
            major_motifs[str(motif)] += 1
    return {
        "probe_count": len(rows),
        "present_count": sum(
            1
            for row in rows
            if isinstance(row.get("value_payload"), dict) and row["value_payload"].get("present")
        ),
        "first_seen_counts": dict(sorted(first_seen.items())),
        "first_witness_op_counts": dict(sorted(witness_ops.items())),
        "denominator_bucket_counts": dict(sorted(buckets.items())),
        "first_witness_aperture_counts": dict(sorted(apertures.items())),
        "cap3_status_counts": dict(sorted(cap3.items())),
        "direct_parent_hub_counts": dict(direct_hubs.most_common()),
        "major_operation_motif_counts": dict(major_motifs.most_common()),
    }


def _common_ancestor_payload(motif_report: Optional[Dict[str, object]]) -> List[Dict[str, object]]:
    if motif_report is None:
        return []
    rankings_raw = motif_report.get("rankings")
    rankings = rankings_raw if isinstance(rankings_raw, dict) else {}
    items = rankings.get("common_ancestors_for_inspected")
    if not isinstance(items, list):
        return []
    return [
        {
            "frac": item.get("frac"),
            "first_seen_round": item.get("first_seen_round"),
            "derivation_events": item.get("derivation_events"),
            "child_count": item.get("child_count"),
            "nontrivial_child_count": item.get("nontrivial_child_count"),
            "inspected_descendants": item.get("inspected_descendants"),
        }
        for item in items
        if isinstance(item, dict)
    ]


def build_report(
    *,
    native_report_path: Path,
    motif_report_path: Optional[Path],
    aperture_report_path: Optional[Path],
    threshold_report_path: Optional[Path],
    probes: Sequence[Tuple[str, Fraction]],
) -> Dict[str, object]:
    native_report = _load_report(native_report_path, require_ledger=True)
    rows_by_frac = _rows_by_frac(native_report)
    motif_report = _load_report(motif_report_path) if motif_report_path is not None else None
    aperture_report = _load_report(aperture_report_path) if aperture_report_path is not None else None
    threshold_report = _load_report(threshold_report_path) if threshold_report_path is not None else None

    rows: List[Dict[str, object]] = []
    for name, frac in probes:
        row: Dict[str, object] = {
            "external_probe": _external_probe_payload(name, frac),
            "value_payload": _value_payload(frac, rows_by_frac=rows_by_frac),
            "motif_context": _motif_context(frac, motif_report=motif_report),
            "aperture_context": _aperture_context(frac, aperture_report=aperture_report),
            "threshold_context": _threshold_context(frac, threshold_report=threshold_report),
        }
        row["binding_signature"] = _binding_signature(row)
        rows.append(row)

    return {
        "schema_version": 1,
        "method": {
            "source": "Binding-structure profile over saved MoO analysis reports.",
            "runtime_semantics_changed": False,
            "definition": (
                "A binding profile is the MoO-native construction context around a speculative node selected "
                "by an external probe: first witness, operation signature, motif neighborhood, construction "
                "aperture, and bounded-cap behavior."
            ),
            "caution": (
                "External names do not identify MoO nodes. They only select already-emergent speculative "
                "nodes for inspection."
            ),
        },
        "sources": {
            "native_report": str(native_report_path),
            "motif_report": str(motif_report_path) if motif_report_path is not None else None,
            "aperture_report": str(aperture_report_path) if aperture_report_path is not None else None,
            "threshold_report": str(threshold_report_path) if threshold_report_path is not None else None,
        },
        "summary": _summary(rows),
        "common_ancestors_for_inspected": _common_ancestor_payload(motif_report),
        "bindings": rows,
    }


def _optional_path(raw: str) -> Optional[Path]:
    if raw.lower() in {"", "none", "null", "-"}:
        return None
    return Path(raw)


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Build a binding-structure profile for external probe-selected MoO nodes."
    )
    parser.add_argument("--native-report", type=str, default="out/experiments/native_r6_full.json")
    parser.add_argument("--motif-report", type=str, default="out/experiments/motif_r5.json")
    parser.add_argument("--aperture-report", type=str, default="out/experiments/construction_aperture_r6.json")
    parser.add_argument("--threshold-report", type=str, default="out/experiments/witness_threshold_r5.json")
    parser.add_argument("--probes", type=str, default=_default_probe_arg())
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--write", type=str, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = build_report(
        native_report_path=Path(str(args.native_report)),
        motif_report_path=_optional_path(str(args.motif_report)),
        aperture_report_path=_optional_path(str(args.aperture_report)),
        threshold_report_path=_optional_path(str(args.threshold_report)),
        probes=_parse_probes(str(args.probes)),
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
