from __future__ import annotations

import argparse
import json
import math
import signal
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo_graph_corpus import (
    GraphCorpus,
    GraphCorpusConfig,
    Key,
    bounded_key,
    normalize_key,
)


OPS = ("+", "-", "*", "/")


def _result_for(op: str, a: int, b: int) -> Key:
    if op == "+":
        return a + b, 1
    if op == "-":
        return a - b, 1
    if op == "*":
        return a * b, 1
    if op == "/":
        return normalize_key(a, b)
    raise ValueError(f"unknown op: {op}")


def _frontier_pairs(stage: int) -> Iterable[Tuple[int, int]]:
    for b in range(1, stage + 1):
        yield stage, b
    for a in range(1, stage):
        yield a, stage


def _retain_result(
    key: Key,
    *,
    stage: int,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
    retain_confirmed_edges: bool,
) -> bool:
    p, q = key
    if retain_confirmed_edges and q == 1 and 1 <= p <= stage:
        return True
    return bounded_key(
        key,
        max_abs_p=max_abs_p,
        max_abs_q=max_abs_q,
        max_abs_value=max_abs_value,
    )


def build_strict_stage_graph(
    *,
    db_path: Path,
    max_stage: int,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
    max_edges: Optional[int],
    time_limit_seconds: Optional[float],
    commit_every: int,
    retain_confirmed_edges: bool,
    verbose: bool,
) -> Dict[str, object]:
    if db_path.exists():
        raise SystemExit(f"Refusing to overwrite existing graph corpus: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=int(max_stage),
        max_abs_p=int(max_abs_p),
        max_abs_q=int(max_abs_q),
        max_abs_value=max_abs_value,
        retain_confirmed_edges=bool(retain_confirmed_edges),
    )
    started = time.perf_counter()
    stop_reason = "max_stage"
    last_stage = 0

    with GraphCorpus(db_path) as corpus:
        corpus.init_schema()
        corpus.ensure_config(config)
        one_id, _ = corpus.ensure_core_integer(1)
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=one_id,
        )

        operand_cache: Dict[int, int] = {1: one_id}
        total_edges = 1

        for stage in range(1, int(max_stage) + 1):
            stage_started = time.perf_counter()
            new_nodes = 0
            retained_events = 0
            candidate_events = 0
            new_edges = 0

            stage_node_id, created = corpus.ensure_core_integer(stage)
            operand_cache[stage] = stage_node_id
            if created:
                new_nodes += 1

            for a, b in _frontier_pairs(stage):
                left_id = operand_cache.get(a)
                if left_id is None:
                    left_id, created = corpus.ensure_core_integer(a)
                    operand_cache[a] = left_id
                    if created:
                        new_nodes += 1
                right_id = operand_cache.get(b)
                if right_id is None:
                    right_id, created = corpus.ensure_core_integer(b)
                    operand_cache[b] = right_id
                    if created:
                        new_nodes += 1

                for op in OPS:
                    candidate_events += 1
                    result_key = _result_for(op, a, b)
                    if not _retain_result(
                        result_key,
                        stage=stage,
                        max_abs_p=max_abs_p,
                        max_abs_q=max_abs_q,
                        max_abs_value=max_abs_value,
                        retain_confirmed_edges=retain_confirmed_edges,
                    ):
                        continue
                    result_id, created = corpus.ensure_node(result_key, first_stage=stage)
                    if created:
                        new_nodes += 1
                    corpus.insert_edge(
                        stage=stage,
                        op=op,
                        left_node_id=left_id,
                        right_node_id=right_id,
                        result_node_id=result_id,
                    )
                    retained_events += 1
                    new_edges += 1
                    total_edges += 1
                    if max_edges is not None and total_edges >= int(max_edges):
                        stop_reason = "max_edges"
                        break
                if stop_reason != "max_stage":
                    break
            last_stage = stage
            corpus.record_stage(
                stage=stage,
                candidate_events=candidate_events,
                retained_events=retained_events,
                new_nodes=new_nodes,
                new_edges=new_edges,
                elapsed_seconds=time.perf_counter() - stage_started,
            )
            if verbose:
                summary = corpus.summary()
                print(
                    f"# U{stage}: +{new_nodes} nodes, +{new_edges} edges "
                    f"(total {summary['nodes']} nodes / {summary['edges']} edges)"
                )
            if stage % max(1, int(commit_every)) == 0:
                corpus.conn.commit()
            if stop_reason != "max_stage":
                break
            if (
                time_limit_seconds is not None
                and time.perf_counter() - started >= float(time_limit_seconds)
            ):
                stop_reason = "time_limit"
                break

        corpus.conn.commit()
        summary = corpus.summary()

    summary.update(
        {
            "db": str(db_path),
            "stop_reason": stop_reason,
            "elapsed_seconds": time.perf_counter() - started,
            "requested_max_stage": int(max_stage),
            "final_stage": int(last_stage),
            "config": config.to_jsonable(),
        }
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the canonical strict-stage graph-first MoO corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--max-stage", type=int, default=100)
    parser.add_argument("--max-abs-p", type=int, default=1000)
    parser.add_argument("--max-abs-q", type=int, default=1000)
    parser.add_argument("--max-abs-value", type=float)
    parser.add_argument("--max-edges", type=int)
    parser.add_argument("--time-limit-seconds", type=float)
    parser.add_argument("--commit-every", type=int, default=25)
    parser.add_argument(
        "--drop-confirmed-edge-exemption",
        action="store_true",
        help="Apply output bounds even to edges landing on currently confirmed positive integers.",
    )
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = build_strict_stage_graph(
        db_path=Path(args.db),
        max_stage=max(1, int(args.max_stage)),
        max_abs_p=max(0, int(args.max_abs_p)),
        max_abs_q=max(1, int(args.max_abs_q)),
        max_abs_value=float(args.max_abs_value)
        if args.max_abs_value is not None
        else None,
        max_edges=int(args.max_edges) if args.max_edges is not None else None,
        time_limit_seconds=float(args.time_limit_seconds)
        if args.time_limit_seconds is not None
        else None,
        commit_every=max(1, int(args.commit_every)),
        retain_confirmed_edges=not bool(args.drop_confirmed_edge_exemption),
        verbose=not bool(args.quiet),
    )
    text = json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True)
    if args.summary is not None:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text + "\n", encoding="utf-8")
    if not bool(args.quiet):
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
