from __future__ import annotations

import argparse
import json
import math
import random
import signal
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from moo_set_closure import bounded, closure_round_delta, complexity_key
from moo_targets import Target, parse_targets


@dataclass(frozen=True)
class BaselineConfig:
    rounds: int
    max_abs_p: int
    max_abs_q: int
    max_abs_value: Optional[float]
    targets: Tuple[Target, ...]
    decoys: int
    seed: int


Witness = Tuple[str, Fraction, Fraction]


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(int(value.numerator))
    return f"{int(value.numerator)}/{int(value.denominator)}"


def _best_in_set(values: Iterable[Fraction], *, target: float) -> Tuple[Fraction, float]:
    best: Optional[Tuple[float, int, int, str, Fraction]] = None
    for value in values:
        err = abs(float(value) - float(target))
        row = (
            float(err),
            int(value.denominator),
            abs(int(value.numerator)),
            _format_fraction(value),
            value,
        )
        if best is None or row < best:
            best = row
    if best is None:
        return Fraction(0, 1), float("inf")
    return best[4], float(best[0])


def _canonical_cf(value: Fraction) -> List[int]:
    n = int(value.numerator)
    d = int(value.denominator)
    if d <= 0:
        raise ValueError("continued fraction denominator must be positive")
    terms: List[int] = []
    while d:
        a = n // d
        terms.append(int(a))
        n, d = d, n - (a * d)
    if len(terms) >= 2 and terms[-1] == 1:
        terms[-2] += 1
        terms.pop()
    return terms


def _target_cf_terms(target: float, *, max_terms: int = 32) -> List[int]:
    x = float(target)
    terms: List[int] = []
    for _ in range(max_terms):
        if not math.isfinite(x):
            break
        a = math.floor(x)
        terms.append(int(a))
        frac = x - a
        if abs(frac) < 1e-15:
            break
        x = 1.0 / frac
    return terms


def _convergents_from_terms(terms: Sequence[int]) -> List[Fraction]:
    out: List[Fraction] = []
    p_m2, p_m1 = 0, 1
    q_m2, q_m1 = 1, 0
    for a in terms:
        p = int(a) * p_m1 + p_m2
        q = int(a) * q_m1 + q_m2
        if q != 0:
            out.append(Fraction(p, q))
        p_m2, p_m1 = p_m1, p
        q_m2, q_m1 = q_m1, q
    return out


def _intermediate_fractions_from_terms(terms: Sequence[int]) -> Set[Fraction]:
    out: Set[Fraction] = set()
    if not terms:
        return out
    p_m2, p_m1 = 0, 1
    q_m2, q_m1 = 1, 0
    for idx, a_raw in enumerate(terms):
        a = int(a_raw)
        start = a if idx == 0 else 1
        for m in range(start, a + 1):
            p = m * p_m1 + p_m2
            q = m * q_m1 + q_m2
            if q != 0:
                out.add(Fraction(p, q))
        p = a * p_m1 + p_m2
        q = a * q_m1 + q_m2
        p_m2, p_m1 = p_m1, p
        q_m2, q_m1 = q_m1, q
    return out


def _cf_class(value: Fraction, *, target: float) -> str:
    if value.denominator <= 0 or value < 0:
        return "not_positive"
    terms = _target_cf_terms(target)
    convergents = set(_convergents_from_terms(terms))
    if value in convergents:
        return "convergent"
    intermediates = _intermediate_fractions_from_terms(terms)
    if value in intermediates:
        return "semiconvergent"
    return "non_cf"


def _stern_brocot_depth(value: Fraction) -> Optional[int]:
    if value <= 0:
        return None
    terms = _canonical_cf(value)
    if not terms:
        return None
    return max(0, sum(terms) - 1)


def _calkin_wilf_path(value: Fraction) -> Optional[str]:
    if value <= 0:
        return None
    a = int(value.numerator)
    b = int(value.denominator)
    reverse_steps: List[str] = []
    while a != b:
        if a <= 0 or b <= 0:
            return None
        if a < b:
            reverse_steps.append("L")
            b -= a
        else:
            reverse_steps.append("R")
            a -= b
    return "".join(reversed(reverse_steps))


def _calkin_wilf_rank(value: Fraction) -> Optional[int]:
    path = _calkin_wilf_path(value)
    if path is None:
        return None
    bits = "1" + "".join("0" if step == "L" else "1" for step in path)
    return int(bits, 2)


def _integer_complexities(limit: int) -> Dict[int, int]:
    limit = max(1, int(limit))
    costs: Dict[int, int] = {1: 1}
    for n in range(2, limit + 1):
        best = n
        for a in range(1, (n // 2) + 1):
            best = min(best, costs[a] + costs[n - a])
        for a in range(2, int(math.sqrt(n)) + 1):
            if n % a == 0:
                best = min(best, costs[a] + costs[n // a])
        costs[n] = best
    costs[0] = 0
    return costs


def _witness_payload(witness: Optional[Witness]) -> Optional[Dict[str, object]]:
    if witness is None:
        return None
    op, a, b = witness
    return {
        "op": op,
        "a": _format_fraction(a),
        "b": _format_fraction(b),
    }


def _target_payloads(config: BaselineConfig) -> Tuple[Target, ...]:
    targets = list(config.targets)
    if config.decoys <= 0:
        return tuple(targets)
    rng = random.Random(int(config.seed))
    upper = float(config.max_abs_value) if config.max_abs_value is not None else 4.0
    upper = max(1.0, upper)
    for idx in range(1, int(config.decoys) + 1):
        targets.append(Target(name=f"decoy{idx}", value=rng.uniform(0.0, upper)))
    return tuple(targets)


def baseline_report(config: BaselineConfig) -> Dict[str, object]:
    targets = _target_payloads(config)
    one = Fraction(1, 1)
    s_prev: Set[Fraction] = {one}
    delta_prev: Set[Fraction] = {one}
    first_seen: Dict[Fraction, int] = {one: 0}
    first_witness: Dict[Fraction, Optional[Witness]] = {one: None}
    best_so_far: Dict[str, Tuple[float, Fraction]] = {}
    improvements: Dict[str, List[Dict[str, object]]] = {target.name: [] for target in targets}
    best_by_round: Dict[str, List[Dict[str, object]]] = {target.name: [] for target in targets}
    round_rows: List[Dict[str, int]] = []
    int_costs = _integer_complexities(max(config.max_abs_p, config.max_abs_q))

    def annotate(*, target: Target, value: Fraction, err: float, round_idx: int) -> Dict[str, object]:
        p = int(value.numerator)
        q = int(value.denominator)
        stern_depth = _stern_brocot_depth(value)
        cw_path = _calkin_wilf_path(value)
        p_cost = int_costs.get(abs(p))
        q_cost = int_costs.get(abs(q))
        total_cost = (p_cost + q_cost) if p_cost is not None and q_cost is not None else None
        return {
            "target": target.name,
            "target_value": float(target.value),
            "round": int(round_idx),
            "frac": _format_fraction(value),
            "p": p,
            "q": q,
            "error": float(err),
            "first_seen_round": int(first_seen.get(value, round_idx)),
            "first_witness": _witness_payload(first_witness.get(value)),
            "cf_class": _cf_class(value, target=target.value),
            "stern_brocot_depth": stern_depth,
            "calkin_wilf_depth": len(cw_path) if cw_path is not None else None,
            "calkin_wilf_rank": _calkin_wilf_rank(value),
            "farey_order": q,
            "integer_complexity": {
                "abs_p": p_cost,
                "q": q_cost,
                "sum": total_cost,
            },
            "emergence_tuple": [
                int(first_seen.get(value, round_idx)),
                q,
                abs(p),
                float(err),
            ],
        }

    for round_idx in range(1, config.rounds + 1):
        new_delta, witnesses = closure_round_delta(
            s_prev=s_prev,
            delta_prev=delta_prev,
            allow=lambda v: bounded(
                v,
                max_abs_p=config.max_abs_p,
                max_abs_q=config.max_abs_q,
                max_abs_value=config.max_abs_value,
            ),
        )
        for value in new_delta:
            first_seen.setdefault(value, int(round_idx))
            first_witness.setdefault(value, witnesses.get(value))

        s_now = s_prev.union(new_delta)
        round_rows.append(
            {
                "round": int(round_idx),
                "size_prev": len(s_prev),
                "size_now": len(s_now),
                "new_values": len(new_delta),
            }
        )

        for target in targets:
            value, err = _best_in_set(s_now, target=target.value)
            row = annotate(target=target, value=value, err=err, round_idx=round_idx)
            best_by_round[target.name].append(row)
            prev = best_so_far.get(target.name)
            if prev is None or err < prev[0]:
                best_so_far[target.name] = (float(err), value)
                improvements[target.name].append(row)

        if not new_delta:
            s_prev = s_now
            delta_prev = set()
            break
        s_prev = s_now
        delta_prev = new_delta

    return {
        "schema_version": 1,
        "framing": {
            "status": "historical_exploratory_closure_baseline",
            "alignment": (
                "This report is an external baseline over exploratory closure "
                "values. It is not aligned MoO computation."
            ),
        },
        "config": {
            "rounds": int(config.rounds),
            "max_abs_p": int(config.max_abs_p),
            "max_abs_q": int(config.max_abs_q),
            "max_abs_value": config.max_abs_value,
            "targets": [{"name": target.name, "value": target.value} for target in targets],
            "decoys": int(config.decoys),
            "seed": int(config.seed),
        },
        "final": {
            "size": len(s_prev),
            "max_round_completed": round_rows[-1]["round"] if round_rows else 0,
        },
        "rounds": round_rows,
        "improvements": improvements,
        "best_by_round": best_by_round,
    }


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description=(
            "Compare historical exploratory closure approximants against rational baselines."
        )
    )
    parser.add_argument("--rounds", type=int, default=5, help="Closure rounds; 5 is the local default.")
    parser.add_argument("--max-abs-p", type=int, default=100, help="Max absolute numerator.")
    parser.add_argument("--max-abs-q", type=int, default=100, help="Max absolute denominator.")
    parser.add_argument("--max-abs-value", type=float, default=4.0, help="Max absolute value.")
    parser.add_argument("--targets", type=str, default="pi,e,sqrt2,phi,ln2", help="Targets or 'all'.")
    parser.add_argument("--decoys", type=int, default=0, help="Add N seeded random target controls.")
    parser.add_argument("--seed", type=int, default=1, help="Seed for decoy targets.")
    parser.add_argument("--compact", action="store_true", help="Omit per-round best rows from output.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--write", type=str, default=None, help="Write JSON to a new file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = BaselineConfig(
        rounds=max(0, int(args.rounds)),
        max_abs_p=max(0, int(args.max_abs_p)),
        max_abs_q=max(1, int(args.max_abs_q)),
        max_abs_value=float(args.max_abs_value) if args.max_abs_value is not None else None,
        targets=parse_targets(str(args.targets)),
        decoys=max(0, int(args.decoys)),
        seed=int(args.seed),
    )
    payload = baseline_report(config)
    if bool(args.compact):
        payload = dict(payload)
        payload.pop("best_by_round", None)
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
