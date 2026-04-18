from __future__ import annotations

import argparse
import json
import signal
from pathlib import Path
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from moo_set_closure import bounded, closure_round_delta
from moo_targets import Target, parse_targets


@dataclass(frozen=True)
class ProbeConfig:
    rounds: int
    max_abs_p: int
    max_abs_q: int
    max_abs_value: Optional[float]
    top_k: int
    targets: Tuple[Target, ...]


def _format_fraction(value: Fraction) -> str:
    p = int(value.numerator)
    q = int(value.denominator)
    if q == 1:
        return str(p)
    return f"{p}/{q}"


def _best_approximants(
    values: Iterable[Fraction], *, target: float, top_k: int
) -> List[Tuple[float, Fraction]]:
    scored: List[Tuple[float, int, int, Fraction]] = []
    for value in values:
        err = abs(float(value) - target)
        scored.append((float(err), int(value.denominator), abs(int(value.numerator)), value))
    scored.sort(key=lambda row: (row[0], row[1], row[2], _format_fraction(row[3])))
    return [(err, value) for err, _, _, value in scored[: max(0, int(top_k))]]


def closure_probe(config: ProbeConfig) -> Dict[str, object]:
    """
    Iterative closure from {1} under + - * /, bounded to keep exploration finite.

    This matches the informal MoO "set iteration" story:
      S0 = {1}
      Sn+1 = Sn ∪ {a op b : a,b in Sn}

    but computes each round incrementally by only combining new elements (delta)
    with the previous set (Sn), which is sufficient to generate all new elements
    appearing at that round.
    """
    one = Fraction(1, 1)
    s_prev: Set[Fraction] = {one}
    delta_prev: Set[Fraction] = {one}
    depth: Dict[Fraction, int] = {one: 0}

    rounds_payload: List[Dict[str, object]] = []
    best_so_far: Dict[str, Tuple[float, Fraction]] = {}
    improvement_chains: Dict[str, List[Dict[str, object]]] = {}

    for round_idx in range(1, config.rounds + 1):
        new_delta, _ = closure_round_delta(
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
            depth.setdefault(value, round_idx)

        s_now = s_prev.union(new_delta)

        round_report: Dict[str, object] = {
            "round": round_idx,
            "size_prev": len(s_prev),
            "size_now": len(s_now),
            "new_values": len(new_delta),
            "best": {},
            "improvements": {},
            "landmarks": {},
        }

        best_fracs_by_target: Dict[str, str] = {}
        for target in config.targets:
            best_list = _best_approximants(s_now, target=target.value, top_k=config.top_k)
            payload_rows: List[Dict[str, object]] = []
            for err, value in best_list:
                payload_rows.append(
                    {
                        "frac": _format_fraction(value),
                        "p": int(value.numerator),
                        "q": int(value.denominator),
                        "error": float(err),
                        "first_round": int(depth.get(value, round_idx)),
                    }
                )
            round_report["best"][target.name] = payload_rows
            if payload_rows:
                best_fracs_by_target[target.name] = str(payload_rows[0]["frac"])

            if best_list:
                best_err, best_value = best_list[0]
                prev = best_so_far.get(target.name)
                if prev is None or best_err < prev[0]:
                    best_so_far[target.name] = (float(best_err), best_value)
                    event = {
                        "frac": _format_fraction(best_value),
                        "p": int(best_value.numerator),
                        "q": int(best_value.denominator),
                        "error": float(best_err),
                        "round": round_idx,
                        "first_round": int(depth.get(best_value, round_idx)),
                    }
                    round_report["improvements"][target.name] = event
                    improvement_chains.setdefault(target.name, []).append(event)

        # Cross-target landmarks: fractions that are simultaneously "best" for multiple targets.
        frac_to_targets: Dict[str, List[str]] = {}
        for target_name, frac in best_fracs_by_target.items():
            frac_to_targets.setdefault(frac, []).append(target_name)
        round_report["landmarks"] = {
            frac: targets
            for frac, targets in sorted(frac_to_targets.items())
            if len(targets) >= 2
        }

        rounds_payload.append(round_report)

        if not new_delta:
            # Saturated under current bounds.
            s_prev = s_now
            delta_prev = set()
            break

        s_prev = s_now
        delta_prev = new_delta

    return {
        "schema_version": 1,
        "config": {
            "rounds": config.rounds,
            "max_abs_p": config.max_abs_p,
            "max_abs_q": config.max_abs_q,
            "max_abs_value": config.max_abs_value,
            "top_k": config.top_k,
            "targets": [{"name": t.name, "value": t.value} for t in config.targets],
        },
        "final": {
            "size": len(s_prev),
            "max_depth": max(depth.values(), default=0),
        },
        "improvement_chains": improvement_chains,
        "rounds": rounds_payload,
    }
def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Probe MoO-style closure sets for rational patterns approaching constants."
    )
    parser.add_argument("--rounds", type=int, default=5, help="Number of closure rounds.")
    parser.add_argument(
        "--max-abs-p",
        type=int,
        default=100,
        help="Max absolute numerator bound for retained fractions.",
    )
    parser.add_argument(
        "--max-abs-q",
        type=int,
        default=100,
        help="Max absolute denominator bound for retained fractions.",
    )
    parser.add_argument(
        "--max-abs-value",
        type=float,
        default=4.0,
        help="Max absolute numeric value bound (float) for retained fractions.",
    )
    parser.add_argument(
        "--top-k", type=int, default=10, help="How many best approximants to report per round."
    )
    parser.add_argument(
        "--targets",
        type=str,
        default="pi,e",
        help="Comma-separated targets: pi,e,tau,sqrt2,sqrt3,phi,ln2,ln10,all (or numeric literals)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    parser.add_argument(
        "--write",
        type=str,
        default=None,
        help="Write full JSON payload to a file (refuses to overwrite).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = ProbeConfig(
        rounds=max(0, int(args.rounds)),
        max_abs_p=max(0, int(args.max_abs_p)),
        max_abs_q=max(1, int(args.max_abs_q)),
        max_abs_value=float(args.max_abs_value) if args.max_abs_value is not None else None,
        top_k=max(1, int(args.top_k)),
        targets=parse_targets(str(args.targets)),
    )
    payload = closure_probe(config)
    indent = 2 if args.pretty else None
    if args.write is not None:
        out_path = Path(str(args.write))
        if out_path.exists():
            raise SystemExit(f"Refusing to overwrite existing file: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=indent, sort_keys=True) + "\n", encoding="utf-8")
        return
    try:
        print(json.dumps(payload, indent=indent, sort_keys=True))
    except BrokenPipeError:
        raise SystemExit(0) from None


if __name__ == "__main__":
    main()
