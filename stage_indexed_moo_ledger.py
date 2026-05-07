from __future__ import annotations

import argparse
from dataclasses import dataclass
import heapq
import json
import math
import signal
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo_targets import Target, parse_targets


Key = Tuple[int, int]
Witness = Tuple[str, int, int]


OPS = ("+", "-", "*", "/")


@dataclass(slots=True)
class NodeRecord:
    first_stage: int
    derivation_events: int = 0
    plus: int = 0
    minus: int = 0
    multiply: int = 0
    divide: int = 0
    first_witness: Optional[Witness] = None


def _format_key(key: Key) -> str:
    p, q = key
    if q == 1:
        return str(p)
    return f"{p}/{q}"


def _normalize(p: int, q: int = 1) -> Key:
    if q == 0:
        raise ZeroDivisionError("zero denominator")
    if q < 0:
        p = -p
        q = -q
    g = math.gcd(abs(p), q)
    return p // g, q // g


def _bounded(
    key: Key,
    *,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
) -> bool:
    p, q = key
    if abs(p) > max_abs_p or abs(q) > max_abs_q:
        return False
    if max_abs_value is not None and abs(p / q) > float(max_abs_value):
        return False
    return True


def _retain_result(
    key: Key,
    *,
    stage: int,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
) -> bool:
    p, q = key
    if q == 1 and 1 <= p <= stage:
        return True
    return _bounded(
        key,
        max_abs_p=max_abs_p,
        max_abs_q=max_abs_q,
        max_abs_value=max_abs_value,
    )


def _record(
    nodes: Dict[Key, NodeRecord],
    key: Key,
    *,
    stage: int,
    op: str,
    a: int,
    b: int,
) -> bool:
    record = nodes.get(key)
    if record is None:
        record = NodeRecord(first_stage=stage, first_witness=(op, a, b))
        nodes[key] = record
        is_new = True
    else:
        is_new = False

    record.derivation_events += 1
    if op == "+":
        record.plus += 1
    elif op == "-":
        record.minus += 1
    elif op == "*":
        record.multiply += 1
    elif op == "/":
        record.divide += 1
    else:
        raise ValueError(f"unknown op: {op}")
    return is_new


def _events_for_pair(a: int, b: int) -> Tuple[Tuple[str, Key], ...]:
    return (
        ("+", (a + b, 1)),
        ("-", (a - b, 1)),
        ("*", (a * b, 1)),
        ("/", _normalize(a, b)),
    )


def _classify(key: Key, *, stage: int) -> str:
    p, q = key
    if key == (1, 1):
        return "order_1_certainty"
    if q == 1 and p > 1 and p <= stage:
        return "order_2_confirmed_core_iteration"
    if q == 1 and p > stage:
        return "order_3_not_yet_core_iteration"
    if q == 1:
        return "order_3_relational_integer"
    return "order_3_rational"


def _record_payload(key: Key, record: NodeRecord, *, stage: int) -> Dict[str, object]:
    p, q = key
    witness = None
    if record.first_witness is not None:
        op, a, b = record.first_witness
        if op == "core_loop":
            expr = f"core_loop({a})"
        elif op == "seed":
            expr = "seed(1)"
        else:
            expr = f"{a} {op} {b}"
        witness = {"op": op, "a": str(a), "b": str(b), "expr": expr}
    return {
        "frac": _format_key(key),
        "p": int(p),
        "q": int(q),
        "value": float(p / q),
        "status": _classify(key, stage=stage),
        "first_stage": int(record.first_stage),
        "derivation_events": int(record.derivation_events),
        "operation_signature": {
            "+": int(record.plus),
            "-": int(record.minus),
            "*": int(record.multiply),
            "/": int(record.divide),
        },
        "first_witness": witness,
    }


def _complexity_key(item: Tuple[Key, NodeRecord]) -> Tuple[int, int, int]:
    key, _ = item
    p, q = key
    return q, abs(p), p


def _push_top(
    heap: List[Tuple[Tuple[float, int, int, int], Key]],
    key: Key,
    record: NodeRecord,
    *,
    score: float,
    limit: int,
) -> None:
    p, q = key
    item = ((float(score), -q, -abs(p), -p), key)
    if len(heap) < limit:
        heapq.heappush(heap, item)
        return
    if item[0] > heap[0][0]:
        heapq.heapreplace(heap, item)


def _top_payloads(
    heap: List[Tuple[Tuple[float, int, int, int], Key]],
    nodes: Dict[Key, NodeRecord],
    *,
    stage: int,
    reverse_score: bool = True,
) -> List[Dict[str, object]]:
    rows = [key for _, key in heap]
    rows.sort(
        key=lambda key: (
            -float(nodes[key].derivation_events) if reverse_score else float(nodes[key].derivation_events),
            key[1],
            abs(key[0]),
            key[0],
        )
    )
    return [_record_payload(key, nodes[key], stage=stage) for key in rows]


def _target_probes(
    nodes: Dict[Key, NodeRecord],
    *,
    targets: Sequence[Target],
    stage: int,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for target in targets:
        best_key: Optional[Key] = None
        best_error = float("inf")
        for key in nodes:
            p, q = key
            err = abs((p / q) - float(target.value))
            if err < best_error:
                best_error = err
                best_key = key
                continue
            if err == best_error and best_key is not None:
                if (q, abs(p), p) < (best_key[1], abs(best_key[0]), best_key[0]):
                    best_key = key
        if best_key is None:
            continue
        payload = _record_payload(best_key, nodes[best_key], stage=stage)
        payload["target"] = target.name
        payload["target_value"] = float(target.value)
        payload["absolute_error"] = float(best_error)
        rows.append(payload)
    return rows


def run_ledger(
    *,
    max_stage: int,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
    max_nodes: Optional[int],
    time_limit_seconds: Optional[float],
    top_k: int,
    targets: Sequence[Target],
) -> Dict[str, object]:
    started = time.perf_counter()
    nodes: Dict[Key, NodeRecord] = {
        (1, 1): NodeRecord(first_stage=1, first_witness=("seed", 1, 1))
    }
    candidate_events = 0
    retained_events = 0
    stop_reason = "max_stage"
    rounds: List[Dict[str, object]] = []
    final_stage = 0

    for stage in range(1, max_stage + 1):
        stage_new = 0
        stage_retained = 0
        stage_candidate = 0

        core_key = (stage, 1)
        if core_key not in nodes:
            nodes[core_key] = NodeRecord(
                first_stage=stage,
                first_witness=("core_loop", stage, 1),
            )
            stage_new += 1

        pairs = [(stage, b) for b in range(1, stage + 1)]
        if stage > 1:
            pairs.extend((a, stage) for a in range(1, stage))

        for a, b in pairs:
            for op, key in _events_for_pair(a, b):
                stage_candidate += 1
                if not _retain_result(
                    key,
                    stage=stage,
                    max_abs_p=max_abs_p,
                    max_abs_q=max_abs_q,
                    max_abs_value=max_abs_value,
                ):
                    continue
                stage_retained += 1
                if _record(nodes, key, stage=stage, op=op, a=a, b=b):
                    stage_new += 1

        candidate_events += stage_candidate
        retained_events += stage_retained
        final_stage = stage
        rounds.append(
            {
                "stage": int(stage),
                "new_nodes": int(stage_new),
                "size_now": int(len(nodes)),
                "candidate_events": int(stage_candidate),
                "retained_events": int(stage_retained),
                "elapsed_seconds": time.perf_counter() - started,
            }
        )

        if max_nodes is not None and len(nodes) >= max_nodes:
            stop_reason = "max_nodes"
            break
        if time_limit_seconds is not None and time.perf_counter() - started >= time_limit_seconds:
            stop_reason = "time_limit"
            break

    counts: Dict[str, int] = {
        "order_1_certainty": 0,
        "order_2_confirmed_core_iteration": 0,
        "order_3_not_yet_core_iteration": 0,
        "order_3_relational_integer": 0,
        "order_3_rational": 0,
    }
    top_all: List[Tuple[Tuple[float, int, int, int], Key]] = []
    top_rational: List[Tuple[Tuple[float, int, int, int], Key]] = []
    top_division: List[Tuple[Tuple[float, int, int, int], Key]] = []
    n = max(1, int(top_k))

    for key, record in nodes.items():
        status = _classify(key, stage=final_stage)
        counts[status] += 1
        _push_top(top_all, key, record, score=record.derivation_events, limit=n)
        if key[1] != 1:
            _push_top(top_rational, key, record, score=record.derivation_events, limit=n)
            _push_top(top_division, key, record, score=record.divide, limit=n)

    elapsed = time.perf_counter() - started
    return {
        "framing": {
            "run_type": "bounded strict stage-indexed MoO ledger",
            "core_rule": (
                "confirmed core-loop iterations are operands; speculative outputs "
                "are real nodes inspected after construction, not operands"
            ),
            "full_field_note": "This is full only inside the explicit stage and value bounds.",
        },
        "config": {
            "max_stage": int(max_stage),
            "max_abs_p": int(max_abs_p),
            "max_abs_q": int(max_abs_q),
            "max_abs_value": max_abs_value,
            "max_nodes": max_nodes,
            "time_limit_seconds": time_limit_seconds,
            "top_k": int(top_k),
            "targets": [target.name for target in targets],
        },
        "final": {
            "stage": int(final_stage),
            "confirmed_operand_count": int(final_stage),
            "stop_reason": stop_reason,
            "elapsed_seconds": elapsed,
            "unique_nodes": int(len(nodes)),
            "speculative_nodes": int(
                len(nodes)
                - counts["order_1_certainty"]
                - counts["order_2_confirmed_core_iteration"]
            ),
            "candidate_events": int(candidate_events),
            "retained_events": int(retained_events),
            "status_counts": counts,
        },
        "rounds": rounds,
        "rankings": {
            "derivation_multiplicity": _top_payloads(top_all, nodes, stage=final_stage),
            "rational_multiplicity": _top_payloads(top_rational, nodes, stage=final_stage),
            "division_multiplicity": _top_payloads(top_division, nodes, stage=final_stage),
        },
        "target_probes": _target_probes(nodes, targets=targets, stage=final_stage),
        "_nodes": nodes,
    }


def _write_ledger(path: Path, nodes: Dict[Key, NodeRecord], *, stage: int) -> None:
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for key, record in sorted(nodes.items(), key=_complexity_key):
            handle.write(json.dumps(_record_payload(key, record, stage=stage), sort_keys=True))
            handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bounded strict stage-indexed MoO ledger preserving speculative rational nodes."
    )
    parser.add_argument("--max-stage", type=int, default=1000)
    parser.add_argument("--max-abs-p", type=int, default=1000)
    parser.add_argument("--max-abs-q", type=int, default=1000)
    parser.add_argument("--max-abs-value", type=float, default=4.0)
    parser.add_argument("--max-nodes", type=int)
    parser.add_argument("--time-limit-seconds", type=float)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--targets", default="pi,e,ln2,sqrt2,phi")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--write-ledger", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    targets = parse_targets(str(args.targets))
    report = run_ledger(
        max_stage=max(1, int(args.max_stage)),
        max_abs_p=max(0, int(args.max_abs_p)),
        max_abs_q=max(1, int(args.max_abs_q)),
        max_abs_value=float(args.max_abs_value) if args.max_abs_value is not None else None,
        max_nodes=int(args.max_nodes) if args.max_nodes is not None else None,
        time_limit_seconds=float(args.time_limit_seconds)
        if args.time_limit_seconds is not None
        else None,
        top_k=max(1, int(args.top_k)),
        targets=targets,
    )
    nodes = report.pop("_nodes")

    if args.write_ledger is not None:
        _write_ledger(Path(args.write_ledger), nodes, stage=int(report["final"]["stage"]))

    text = json.dumps(report, indent=2 if args.pretty else None, sort_keys=True) + "\n"
    if args.write is not None:
        out_path = Path(args.write)
        if out_path.exists():
            raise SystemExit(f"Refusing to overwrite existing report: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    if not args.quiet:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
