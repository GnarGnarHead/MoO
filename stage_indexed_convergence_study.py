from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import json
import signal
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo_targets import Target, parse_targets


@dataclass(frozen=True)
class RationalRow:
    stage: int
    p: int
    q: int
    derivation_events: int
    first_op: str
    first_a: str
    first_b: str

    @property
    def value(self) -> float:
        return self.p / self.q

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.p, self.q)

    @property
    def label(self) -> str:
        return f"{self.p}/{self.q}"


def _load_rationals(path: Path) -> List[RationalRow]:
    rows: List[RationalRow] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                continue
            try:
                p = int(payload["p"])
                q = int(payload["q"])
            except (KeyError, TypeError, ValueError):
                continue
            if p <= 0 or q <= 1:
                continue
            witness = payload.get("first_witness")
            if not isinstance(witness, dict):
                witness = {}
            rows.append(
                RationalRow(
                    stage=int(payload.get("first_stage", max(abs(p), q))),
                    p=p,
                    q=q,
                    derivation_events=int(payload.get("derivation_events", 0)),
                    first_op=str(witness.get("op", "")),
                    first_a=str(witness.get("a", "")),
                    first_b=str(witness.get("b", "")),
                )
            )
    rows.sort(key=lambda row: (row.stage, row.q, abs(row.p), row.p))
    return rows


def _side(row: RationalRow, target: Target) -> str:
    diff = row.value - float(target.value)
    if diff < 0:
        return "below"
    if diff > 0:
        return "above"
    return "exact"


def _row_payload(row: RationalRow, *, target: Optional[Target] = None) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "frac": row.label,
        "p": row.p,
        "q": row.q,
        "value": row.value,
        "first_stage": row.stage,
        "derivation_events": row.derivation_events,
        "first_witness": {
            "op": row.first_op,
            "a": row.first_a,
            "b": row.first_b,
            "expr": f"{row.first_a} {row.first_op} {row.first_b}".strip(),
        },
    }
    if target is not None:
        error = abs(row.value - float(target.value))
        payload["target"] = target.name
        payload["absolute_error"] = error
        payload["side"] = _side(row, target)
    return payload


def _better_for_target(candidate: RationalRow, incumbent: Optional[RationalRow], target: Target) -> bool:
    if incumbent is None:
        return True
    c_error = abs(candidate.value - float(target.value))
    i_error = abs(incumbent.value - float(target.value))
    if c_error < i_error:
        return True
    if c_error > i_error:
        return False
    return (candidate.q, abs(candidate.p), candidate.p) < (
        incumbent.q,
        abs(incumbent.p),
        incumbent.p,
    )


def _record_chain(rows: Sequence[RationalRow], *, target: Target) -> List[RationalRow]:
    chain: List[RationalRow] = []
    best: Optional[RationalRow] = None
    idx = 0
    while idx < len(rows):
        stage = rows[idx].stage
        stage_best: Optional[RationalRow] = None
        while idx < len(rows) and rows[idx].stage == stage:
            row = rows[idx]
            if _better_for_target(row, stage_best, target):
                stage_best = row
            idx += 1
        if stage_best is not None and _better_for_target(stage_best, best, target):
            best = stage_best
            chain.append(stage_best)
    return chain


def _transition_payload(prev: RationalRow, curr: RationalRow, *, target: Target) -> Dict[str, object]:
    determinant = curr.p * prev.q - prev.p * curr.q
    return {
        "from": prev.label,
        "to": curr.label,
        "stage_gap": int(curr.stage - prev.stage),
        "determinant": int(determinant),
        "abs_determinant": abs(int(determinant)),
        "side_from": _side(prev, target),
        "side_to": _side(curr, target),
        "side_flip": _side(prev, target) != _side(curr, target),
    }


def _recurrence_payload(
    older: RationalRow,
    prev: RationalRow,
    curr: RationalRow,
) -> Optional[Dict[str, object]]:
    num_delta = curr.p - older.p
    den_delta = curr.q - older.q
    if prev.p == 0 or prev.q == 0:
        return None
    if num_delta % prev.p != 0 or den_delta % prev.q != 0:
        return None
    a_num = num_delta // prev.p
    a_den = den_delta // prev.q
    if a_num != a_den or a_num <= 0:
        return None
    return {
        "from": [older.label, prev.label],
        "to": curr.label,
        "coefficient": int(a_num),
        "rule": "curr = coefficient * previous + older",
    }


def _chain_analysis(chain: Sequence[RationalRow], *, target: Target) -> Dict[str, object]:
    transitions = [
        _transition_payload(chain[idx - 1], chain[idx], target=target)
        for idx in range(1, len(chain))
    ]
    recurrence_rows: List[Dict[str, object]] = []
    for idx in range(2, len(chain)):
        recurrence = _recurrence_payload(chain[idx - 2], chain[idx - 1], chain[idx])
        if recurrence is not None:
            recurrence_rows.append(recurrence)

    determinant_counts = Counter(str(row["abs_determinant"]) for row in transitions)
    side_flips = sum(1 for row in transitions if bool(row["side_flip"]))
    final = chain[-1] if chain else None
    return {
        "target": target.name,
        "target_value": float(target.value),
        "chain_length": len(chain),
        "final": _row_payload(final, target=target) if final is not None else None,
        "determinant_abs_counts": dict(sorted(determinant_counts.items(), key=lambda item: int(item[0]))),
        "unimodular_steps": int(determinant_counts.get("1", 0)),
        "side_flips": int(side_flips),
        "recurrence_supported_steps": len(recurrence_rows),
        "chain": [_row_payload(row, target=target) for row in chain],
        "transitions": transitions,
        "recurrences": recurrence_rows,
    }


def run_convergence_study(
    *,
    ledger: Path,
    targets: Sequence[Target],
) -> Dict[str, object]:
    rows = _load_rationals(ledger)
    analyses = [_chain_analysis(_record_chain(rows, target=target), target=target) for target in targets]

    shared = {
        "targets": [target.name for target in targets],
        "candidate_rationals": len(rows),
        "total_chain_nodes": sum(int(row["chain_length"]) for row in analyses),
        "total_unimodular_steps": sum(int(row["unimodular_steps"]) for row in analyses),
        "total_recurrence_supported_steps": sum(
            int(row["recurrence_supported_steps"]) for row in analyses
        ),
        "interpretation": (
            "A target shadow has structural value only when it belongs to a record-improving chain. "
            "Unimodular steps and recurrence rows are evidence of shared rational convergence structure; "
            "the decimal error is only an external probe label."
        ),
    }
    return {
        "framing": {
            "run_type": "structure-first convergence study over a saved stage-indexed MoO ledger",
            "source_ledger": str(ledger),
            "point_warning": "Individual approximating points are not treated as meaningful alone.",
            "chain_rule": "For each target, keep only stage-by-stage record-improving speculative rational nodes.",
            "structure_tests": [
                "determinant between consecutive record nodes",
                "side alternation around the external target",
                "continued-fraction-style recurrence: curr = a * previous + older",
            ],
        },
        "shared_structure": shared,
        "targets": analyses,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Structure-first convergence chains over a saved strict-stage MoO ledger."
    )
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--targets", default="pi,e,ln2,sqrt2,phi")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = run_convergence_study(
        ledger=Path(args.ledger),
        targets=parse_targets(str(args.targets)),
    )
    text = json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True) + "\n"
    if args.write is not None:
        out_path = Path(args.write)
        if out_path.exists():
            raise SystemExit(f"Refusing to overwrite existing report: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        return 0
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
