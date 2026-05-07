from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence


def connect_readonly(path: Path) -> sqlite3.Connection:
    db_path = Path(path)
    if not db_path.exists():
        raise SystemExit(f"Corpus DB does not exist: {db_path}")
    if not db_path.is_file():
        raise SystemExit(f"Corpus DB path is not a file: {db_path}")

    uri = f"{db_path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def strict_alignment_payload(conn: sqlite3.Connection) -> Dict[str, object]:
    non_core_operand_edges = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges e
            JOIN nodes l ON l.node_id = e.left_node_id
            JOIN nodes r ON r.node_id = e.right_node_id
            WHERE e.op != 'seed'
              AND (
                NOT (l.q = 1 AND l.p >= 1 AND l.p <= e.stage)
                OR NOT (r.q = 1 AND r.p >= 1 AND r.p <= e.stage)
              )
            """
        ).fetchone()["n"]
    )
    speculative_input_edges = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges e
            JOIN nodes l ON l.node_id = e.left_node_id
            JOIN nodes r ON r.node_id = e.right_node_id
            WHERE e.op != 'seed'
              AND (
                l.confirmed_stage IS NULL
                OR r.confirmed_stage IS NULL
                OR l.confirmed_stage > e.stage
                OR r.confirmed_stage > e.stage
              )
            """
        ).fetchone()["n"]
    )
    status = "pass" if speculative_input_edges == 0 and non_core_operand_edges == 0 else "fail"
    return {
        "operand_rule": (
            "positive-spine strict corpus: only confirmed positive-spine "
            "iterations may be operands"
        ),
        "speculative_nodes_are_operands": False,
        "speculative_input_edges": speculative_input_edges,
        "non_core_operand_edges": non_core_operand_edges,
        "status": status,
    }


def require_strict_alignment(conn: sqlite3.Connection) -> Dict[str, object]:
    alignment = strict_alignment_payload(conn)
    if alignment["status"] != "pass":
        raise SystemExit(
            "Corpus failed strict alignment check: "
            f"speculative_input_edges={alignment['speculative_input_edges']}, "
            f"non_core_operand_edges={alignment['non_core_operand_edges']}"
        )
    return alignment


def positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


def nonnegative_float(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report_metadata(
    *,
    tool_path: Path,
    db_path: Path,
    argv: Optional[Sequence[str]],
    schema_version: str,
    include_checksums: bool,
) -> Dict[str, object]:
    tool = Path(tool_path)
    db = Path(db_path)
    if argv is None:
        command = shlex.join(sys.argv)
    else:
        command = shlex.join([sys.executable, str(tool), *list(argv)])

    generated_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "schema_version": schema_version,
        "generated_at_utc": generated_at,
        "tool": tool.name,
        "tool_path": str(tool),
        "command": command,
        "db_path": str(db),
        "checksums_included": bool(include_checksums),
        "db_sha256": file_sha256(db) if include_checksums else None,
        "tool_sha256": file_sha256(tool) if include_checksums else None,
    }


def emit_json(payload: Dict[str, object], *, pretty: bool, write: Optional[Path]) -> None:
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n"
    if write is not None:
        output_path = Path(write)
        if output_path.exists():
            raise SystemExit(f"Refusing to overwrite existing report: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text, end="")
