from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from moo_research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)


Key = Tuple[int, int]


@dataclass(frozen=True)
class BranchSpec:
    name: str
    relation: str
    op: str
    output: Callable[[int], int]
    description: str


LINEAR_BRANCHES = {
    "even": BranchSpec(
        name="even",
        relation="n -> n+n",
        op="+",
        output=lambda n: n + n,
        description="twofold recurrence / self-addition branch",
    ),
    "square": BranchSpec(
        name="square",
        relation="n -> n*n",
        op="*",
        output=lambda n: n * n,
        description="self-relation / self-multiplicative branch",
    ),
}


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return str(row["value"])


def _json_meta(conn: sqlite3.Connection, key: str) -> Optional[object]:
    value = _meta_value(conn, key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _corpus_config(conn: sqlite3.Connection) -> Dict[str, object]:
    config = _json_meta(conn, "config_json")
    if isinstance(config, dict):
        return dict(config)
    latest_stage = conn.execute(
        "SELECT stage FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    return {
        "max_stage": int(latest_stage["stage"]) if latest_stage is not None else None,
        "max_abs_p": None,
        "max_abs_q": None,
        "max_abs_value": None,
        "retain_confirmed_edges": None,
    }


def _corpus_payload(conn: sqlite3.Connection) -> Dict[str, object]:
    latest_stage = conn.execute(
        "SELECT * FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    node_count = conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()
    edge_count = conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()
    return {
        "schema_version": _meta_value(conn, "schema_version"),
        "config": _corpus_config(conn),
        "latest_stage": dict(latest_stage) if latest_stage is not None else None,
        "nodes": int(node_count["n"]),
        "edges": int(edge_count["n"]),
        "alignment": require_strict_alignment(conn),
    }


def _load_integer_nodes(conn: sqlite3.Connection) -> Dict[int, sqlite3.Row]:
    return {
        int(row["p"]): row
        for row in conn.execute("SELECT * FROM nodes WHERE q = 1").fetchall()
    }


def _node_payload(row: Optional[sqlite3.Row]) -> Dict[str, object]:
    if row is None:
        return {"present": False, "node": None}
    confirmed_stage = row["confirmed_stage"]
    return {
        "present": True,
        "node": {
            "node_id": int(row["node_id"]),
            "value": int(row["p"]),
            "first_stage": int(row["first_stage"]),
            "confirmed_stage": int(confirmed_stage) if confirmed_stage is not None else None,
            "kind": str(row["kind"]),
        },
    }


def _strict_binary_edge(
    conn: sqlite3.Connection,
    *,
    left_value: int,
    op: str,
    right_value: int,
    result_value: int,
    nodes: Dict[int, sqlite3.Row],
) -> Dict[str, object]:
    left = nodes.get(int(left_value))
    right = nodes.get(int(right_value))
    result = nodes.get(int(result_value))
    if left is None or right is None or result is None:
        missing = []
        if left is None:
            missing.append("left")
        if right is None:
            missing.append("right")
        if result is None:
            missing.append("result")
        return {"present": False, "reason": "required_node_absent", "missing": missing}
    row = conn.execute(
        """
        SELECT edge_id, stage, op
        FROM edges
        WHERE op = ?
          AND left_node_id = ?
          AND right_node_id = ?
          AND result_node_id = ?
        ORDER BY stage, edge_id
        LIMIT 1
        """,
        (op, int(left["node_id"]), int(right["node_id"]), int(result["node_id"])),
    ).fetchone()
    if row is None and op in {"+", "*"} and int(left["node_id"]) != int(right["node_id"]):
        row = conn.execute(
            """
            SELECT edge_id, stage, op
            FROM edges
            WHERE op = ?
              AND left_node_id = ?
              AND right_node_id = ?
              AND result_node_id = ?
            ORDER BY stage, edge_id
            LIMIT 1
            """,
            (op, int(right["node_id"]), int(left["node_id"]), int(result["node_id"])),
        ).fetchone()
    if row is None:
        return {"present": False, "reason": "no_retained_relation_edge"}
    return {
        "present": True,
        "edge_id": int(row["edge_id"]),
        "stage": int(row["stage"]),
        "op": str(row["op"]),
    }


def _field_blockers(
    *,
    result_value: int,
    candidate_stage: int,
    config: Dict[str, object],
) -> List[str]:
    blockers: List[str] = []
    max_stage = config.get("max_stage")
    max_abs_p = config.get("max_abs_p")
    max_abs_q = config.get("max_abs_q")
    max_abs_value = config.get("max_abs_value")
    retain_confirmed_edges = bool(config.get("retain_confirmed_edges", False))
    if max_stage is not None and int(candidate_stage) > int(max_stage):
        blockers.append("candidate_stage_beyond_U")
    if retain_confirmed_edges and 1 <= int(result_value) <= int(candidate_stage):
        return blockers
    if max_abs_p is not None and abs(int(result_value)) > int(max_abs_p):
        blockers.append("outside_max_abs_p")
    if max_abs_q is not None and 1 > int(max_abs_q):
        blockers.append("outside_max_abs_q")
    if max_abs_value is not None and abs(float(result_value)) > float(max_abs_value):
        blockers.append("outside_max_abs_value")
    return blockers


def relation_lineage_entry(
    conn: sqlite3.Connection,
    *,
    spec: BranchSpec,
    source: int,
    nodes: Dict[int, sqlite3.Row],
    config: Dict[str, object],
) -> Dict[str, object]:
    result = int(spec.output(int(source)))
    source_row = nodes.get(int(source))
    result_row = nodes.get(result)
    candidate_stage = int(source)
    source_confirmed = (
        source_row is not None
        and source_row["confirmed_stage"] is not None
        and int(source_row["confirmed_stage"]) <= candidate_stage
    )
    relation_permitted = bool(source_confirmed)
    edge = _strict_binary_edge(
        conn,
        left_value=source,
        op=spec.op,
        right_value=source,
        result_value=result,
        nodes=nodes,
    )
    spine_witnessed = (
        result_row is not None
        and result_row["confirmed_stage"] is not None
        and int(result_row["confirmed_stage"]) <= int(config.get("max_stage", int(result_row["confirmed_stage"])))
    )
    blockers = _field_blockers(
        result_value=result,
        candidate_stage=candidate_stage,
        config=config,
    )

    readings: List[str] = []
    if bool(edge["present"]):
        readings.append("witnessed_through_branch")
    if spine_witnessed:
        readings.append("witnessed_through_counting_spine")
    if relation_permitted and not bool(edge["present"]):
        readings.append("permitted_but_not_witnessed_in_field")
    if not relation_permitted:
        readings.append("not_yet_permitted_by_recurrence")
    if result_row is None:
        readings.append("value_not_visible_in_field")

    return {
        "branch": spec.name,
        "relation": spec.relation,
        "description": spec.description,
        "source": int(source),
        "result": int(result),
        "candidate_stage": candidate_stage,
        "source_node": _node_payload(source_row),
        "result_node": _node_payload(result_row),
        "relation_permitted": relation_permitted,
        "branch_witness": edge,
        "counting_spine_witnessed": bool(spine_witnessed),
        "field_blockers": blockers,
        "moo_reading": readings,
        "machine_fields": {
            "edge_present": bool(edge["present"]),
            "result_node_present": result_row is not None,
            "source_confirmed_at_candidate_stage": bool(source_confirmed),
        },
    }


def relation_lineage_report(
    conn: sqlite3.Connection,
    *,
    branch: str,
    max_source: int,
) -> Dict[str, object]:
    spec = LINEAR_BRANCHES[branch]
    nodes = _load_integer_nodes(conn)
    config = _corpus_config(conn)
    entries = [
        relation_lineage_entry(
            conn,
            spec=spec,
            source=n,
            nodes=nodes,
            config=config,
        )
        for n in range(1, int(max_source) + 1)
    ]
    counts: Dict[str, int] = {}
    for entry in entries:
        for reading in entry["moo_reading"]:
            counts[reading] = counts.get(reading, 0) + 1
    return {
        "report_type": "branch_lineage",
        "schema_version": "branch_lineage.v1",
        "branch_definition": {
            "name": spec.name,
            "relation": spec.relation,
            "description": spec.description,
            "moo_definition": "same relation repeated along the unfolding of MoO",
        },
        "parameters": {"branch": branch, "max_source": int(max_source)},
        "corpus": _corpus_payload(conn),
        "summary": {
            "entry_count": len(entries),
            "moo_reading_counts": {key: counts[key] for key in sorted(counts)},
        },
        "entries": entries,
    }


def _factor_pair(value: int) -> Optional[Tuple[int, int]]:
    if value < 4:
        return None
    for a in range(2, int(value**0.5) + 1):
        if value % a == 0:
            return a, value // a
    return None


def prime_lineage_entry(
    conn: sqlite3.Connection,
    *,
    value: int,
    nodes: Dict[int, sqlite3.Row],
    config: Dict[str, object],
) -> Dict[str, object]:
    row = nodes.get(int(value))
    spine_witnessed = row is not None and row["confirmed_stage"] is not None
    factor_pair = _factor_pair(int(value))
    product_edge: Dict[str, object]
    if factor_pair is None:
        product_edge = {"present": False, "reason": "no_nontrivial_product_landing"}
    else:
        product_edge = _strict_binary_edge(
            conn,
            left_value=factor_pair[0],
            op="*",
            right_value=factor_pair[1],
            result_value=value,
            nodes=nodes,
        )
    readings = ["witnessed_through_counting_spine"] if spine_witnessed else []
    if value >= 2 and factor_pair is None:
        readings.append("prime_branch_member")
        readings.append("irreducibility_condition")
    elif factor_pair is not None:
        readings.append("product_branch_landing")
        if bool(product_edge["present"]):
            readings.append("witnessed_through_product_branch")
        else:
            readings.append("product_landing_permitted_but_not_witnessed_in_field")
    return {
        "branch": "prime",
        "relation": "counting-spine value read by prime-branch membership or product-branch landing",
        "value": int(value),
        "value_node": _node_payload(row),
        "counting_spine_witnessed": bool(spine_witnessed),
        "nontrivial_product_landing": None
        if factor_pair is None
        else {"left": factor_pair[0], "right": factor_pair[1]},
        "product_branch_witness": product_edge,
        "moo_reading": readings,
        "machine_fields": {
            "factor_pair_found": factor_pair is not None,
            "product_edge_present": bool(product_edge.get("present")),
            "config_max_stage": config.get("max_stage"),
        },
    }


def prime_lineage_report(conn: sqlite3.Connection, *, max_value: int) -> Dict[str, object]:
    nodes = _load_integer_nodes(conn)
    config = _corpus_config(conn)
    entries = [
        prime_lineage_entry(conn, value=value, nodes=nodes, config=config)
        for value in range(2, int(max_value) + 1)
    ]
    counts: Dict[str, int] = {}
    for entry in entries:
        for reading in entry["moo_reading"]:
            counts[reading] = counts.get(reading, 0) + 1
    return {
        "report_type": "branch_lineage",
        "schema_version": "branch_lineage.v3",
        "branch_definition": {
            "name": "prime",
            "relation": "counting-spine values sharing the repeated irreducibility relation",
            "description": "prime branch membership is witnessed by the irreducibility condition",
            "moo_definition": "same irreducibility relation repeated along the unfolding of MoO",
        },
        "parameters": {"branch": "prime", "max_value": int(max_value)},
        "corpus": _corpus_payload(conn),
        "summary": {
            "entry_count": len(entries),
            "moo_reading_counts": {key: counts[key] for key in sorted(counts)},
        },
        "entries": entries,
    }


def branch_lineage_report(conn: sqlite3.Connection, *, branch: str, limit: int) -> Dict[str, object]:
    if branch == "prime":
        return prime_lineage_report(conn, max_value=limit)
    return relation_lineage_report(conn, branch=branch, max_source=limit)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit MoO branch lineage as repeated relation, not value presence alone."
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--branch", choices=sorted([*LINEAR_BRANCHES, "prime"]), required=True)
    parser.add_argument("--limit", type=positive_int, default=20)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--with-checksums", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    with connect_readonly(Path(args.db)) as conn:
        payload = branch_lineage_report(
            conn,
            branch=str(args.branch),
            limit=int(args.limit),
        )
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version=str(payload.get("schema_version", "branch_lineage.v3")),
        include_checksums=bool(args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
