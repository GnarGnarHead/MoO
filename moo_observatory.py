from __future__ import annotations

import argparse
import json
import signal
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo_corpus import Corpus, CorpusConfig, best_baseline_for_target, bounded
from moo_set_closure import closure_round_delta, complexity_key
from moo_targets import Target, parse_targets


def _best_in_set(values: Iterable[Fraction], *, target: float) -> Tuple[Fraction, float]:
    best: Optional[Tuple[float, Fraction]] = None
    for value in values:
        err = abs(float(value) - float(target))
        row = (float(err), value)
        if best is None:
            best = row
            continue
        if row[0] < best[0]:
            best = row
            continue
        if row[0] == best[0]:
            # Deterministic tie-break: prefer simpler rationals.
            if complexity_key(value) < complexity_key(best[1]):
                best = row
    if best is None:
        return Fraction(0, 1), float("inf")
    return best[1], float(best[0])


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(int(value.numerator))
    return f"{int(value.numerator)}/{int(value.denominator)}"


def extend_corpus(
    *,
    corpus: Corpus,
    config: CorpusConfig,
    targets: Sequence[Target],
    to_round: int,
    verbose: bool,
) -> None:
    corpus.ensure_seed()
    corpus.upsert_targets([(t.name, t.value) for t in targets])
    corpus.commit()

    stored = corpus.load_values()
    current_round = corpus.max_round()
    if current_round >= to_round:
        if verbose:
            print(f"# noop (already at round {current_round})")
        return

    def key_to_fraction(key: Tuple[int, int]) -> Fraction:
        return Fraction(int(key[0]), int(key[1]))

    s_prev: set[Fraction] = {key_to_fraction(k) for k, r in stored.items() if r <= current_round}
    delta_prev: set[Fraction] = {key_to_fraction(k) for k, r in stored.items() if r == current_round}
    first_seen: Dict[Fraction, int] = {key_to_fraction(k): int(r) for k, r in stored.items()}

    for round_idx in range(current_round + 1, to_round + 1):
        corpus.append_event("round_started", {"round": round_idx}, round_idx=round_idx)

        new_delta, witness = closure_round_delta(
            s_prev=s_prev,
            delta_prev=delta_prev,
            allow=lambda v: bounded(v, config=config),
        )

        size_prev = len(s_prev)
        s_now = s_prev.union(new_delta)
        size_now = len(s_now)

        # Store new values + first witness occurrence.
        for value in sorted(new_delta, key=complexity_key):
            op, a, b = witness.get(value, ("?", Fraction(0, 1), Fraction(0, 1)))
            corpus.insert_new_value(
                value=value,
                first_seen_round=round_idx,
                op=op,
                a=a,
                b=b,
                meta={"generator": "set_closure"},
            )
            first_seen[value] = int(round_idx)

        # Probes (targeted controls + baseline)
        best_fracs_for_landmarks: Dict[str, str] = {}
        for t in targets:
            best_value, best_error = _best_in_set(s_now, target=t.value)
            base_value, base_error = best_baseline_for_target(target=t.value, config=config)

            last = corpus.last_best_so_far(t.name)
            is_best_so_far = last is None or best_error < last[0]

            corpus.insert_probe_best(
                target_name=t.name,
                round_idx=round_idx,
                best_value=best_value,
                best_error=best_error,
                best_first_seen_round=int(first_seen.get(best_value, round_idx)),
                is_best_so_far=is_best_so_far,
                baseline_value=base_value,
                baseline_error=base_error,
            )
            if is_best_so_far:
                corpus.append_event(
                    "probe_record",
                    {
                        "target": t.name,
                        "round": round_idx,
                        "best": _format_fraction(best_value),
                        "error": float(best_error),
                        "baseline": _format_fraction(base_value),
                        "baseline_error": float(base_error),
                    },
                    round_idx=round_idx,
                )
            best_fracs_for_landmarks[t.name] = _format_fraction(best_value)

        # Cross-target landmarks: same best fraction for >=2 targets this round.
        frac_to_targets: Dict[str, List[str]] = {}
        for target_name, frac in best_fracs_for_landmarks.items():
            frac_to_targets.setdefault(frac, []).append(target_name)
        landmarks = {frac: names for frac, names in frac_to_targets.items() if len(names) >= 2}
        if landmarks:
            corpus.append_event(
                "landmarks",
                {"round": round_idx, "shared_best": dict(sorted(landmarks.items()))},
                round_idx=round_idx,
            )

        corpus.record_round(
            round_idx=round_idx,
            size_prev=size_prev,
            size_now=size_now,
            new_values=len(new_delta),
        )
        corpus.append_event(
            "round_completed",
            {
                "round": round_idx,
                "size_prev": size_prev,
                "size_now": size_now,
                "new_values": len(new_delta),
                "landmarks": dict(sorted(landmarks.items())) if landmarks else {},
            },
            round_idx=round_idx,
        )
        corpus.commit()

        if verbose:
            print(f"# round {round_idx}: +{len(new_delta)} (size {size_prev} -> {size_now})")
            for t in targets:
                # print best + baseline, not full tables
                best_row = corpus.conn.execute(
                    "SELECT best_p, best_q, best_error, baseline_p, baseline_q, baseline_error, is_best_so_far "
                    "FROM probe_best WHERE target_name=? AND round=?",
                    (t.name, round_idx),
                ).fetchone()
                if best_row is None:
                    continue
                best_val = Fraction(int(best_row["best_p"]), int(best_row["best_q"]))
                base_val = Fraction(int(best_row["baseline_p"]), int(best_row["baseline_q"]))
                flag = " *" if int(best_row["is_best_so_far"]) == 1 else ""
                print(
                    f"  - {t.name}{flag}: best={_format_fraction(best_val)} err={float(best_row['best_error']):.6g} "
                    f"(baseline={_format_fraction(base_val)} err={float(best_row['baseline_error']):.6g})"
                )

        # Advance in-memory sets.
        s_prev = s_now
        delta_prev = new_delta


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Incrementally extend a persistent MoO set-closure corpus and run probes."
    )
    parser.add_argument("--db", type=str, required=True, help="SQLite corpus path.")
    parser.add_argument(
        "--to-round",
        type=int,
        required=True,
        help="Extend (or confirm) the corpus up to this closure-round (inclusive).",
    )
    parser.add_argument("--targets", type=str, default="pi,e", help="Targets (or 'all').")
    parser.add_argument("--max-abs-p", type=int, default=100, help="Max abs numerator bound.")
    parser.add_argument("--max-abs-q", type=int, default=100, help="Max abs denominator bound.")
    parser.add_argument(
        "--max-abs-value",
        type=float,
        default=4.0,
        help="Max abs numeric value bound.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output.")
    parser.add_argument("--dump-config", action="store_true", help="Print stored config and exit.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    cfg = CorpusConfig(
        generator="set_closure_round",
        max_abs_p=max(0, int(args.max_abs_p)),
        max_abs_q=max(1, int(args.max_abs_q)),
        max_abs_value=float(args.max_abs_value) if args.max_abs_value is not None else None,
    )
    targets = parse_targets(str(args.targets))

    db_path = Path(str(args.db))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with Corpus(db_path) as corpus:
        corpus.init_schema()
        corpus.ensure_config(cfg)
        if bool(args.dump_config):
            print(json.dumps(cfg.to_jsonable(), indent=2, sort_keys=True))
            return
        extend_corpus(
            corpus=corpus,
            config=cfg,
            targets=targets,
            to_round=int(args.to_round),
            verbose=not bool(args.quiet),
        )


if __name__ == "__main__":
    main()
