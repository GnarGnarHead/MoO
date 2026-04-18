from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CorpusConfig:
    generator: str
    max_abs_p: int
    max_abs_q: int
    max_abs_value: Optional[float]

    def to_jsonable(self) -> Dict[str, object]:
        return {
            "generator": self.generator,
            "max_abs_p": int(self.max_abs_p),
            "max_abs_q": int(self.max_abs_q),
            "max_abs_value": float(self.max_abs_value) if self.max_abs_value is not None else None,
        }


def _fraction_key(value: Fraction) -> Tuple[int, int]:
    value = Fraction(int(value.numerator), int(value.denominator))
    return int(value.numerator), int(value.denominator)


class Corpus:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self) -> None:
        self.conn.close()

    def init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rounds (
              round INTEGER PRIMARY KEY,
              size_prev INTEGER NOT NULL,
              size_now INTEGER NOT NULL,
              new_values INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS canon_values (
              p INTEGER NOT NULL,
              q INTEGER NOT NULL,
              first_seen_round INTEGER NOT NULL,
              PRIMARY KEY (p, q)
            );

            CREATE INDEX IF NOT EXISTS idx_canon_values_first_seen_round
              ON canon_values(first_seen_round);

            CREATE TABLE IF NOT EXISTS occurrences (
              occ_id INTEGER PRIMARY KEY AUTOINCREMENT,
              round INTEGER NOT NULL,
              p INTEGER NOT NULL,
              q INTEGER NOT NULL,
              op TEXT NOT NULL,
              a_p INTEGER,
              a_q INTEGER,
              b_p INTEGER,
              b_q INTEGER,
              meta_json TEXT,
              FOREIGN KEY (p, q) REFERENCES canon_values(p, q)
            );

            CREATE INDEX IF NOT EXISTS idx_occurrences_round
              ON occurrences(round);

            CREATE TABLE IF NOT EXISTS targets (
              name TEXT PRIMARY KEY,
              value REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS probe_best (
              target_name TEXT NOT NULL,
              round INTEGER NOT NULL,
              best_p INTEGER NOT NULL,
              best_q INTEGER NOT NULL,
              best_error REAL NOT NULL,
              best_first_seen_round INTEGER NOT NULL,
              is_best_so_far INTEGER NOT NULL,
              baseline_p INTEGER NOT NULL,
              baseline_q INTEGER NOT NULL,
              baseline_error REAL NOT NULL,
              PRIMARY KEY (target_name, round),
              FOREIGN KEY (target_name) REFERENCES targets(name),
              FOREIGN KEY (best_p, best_q) REFERENCES canon_values(p, q)
            );

            CREATE INDEX IF NOT EXISTS idx_probe_best_round
              ON probe_best(round);

            CREATE TABLE IF NOT EXISTS events (
              event_id INTEGER PRIMARY KEY AUTOINCREMENT,
              round INTEGER,
              event_type TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_round
              ON events(round);
            """
        )
        self._set_meta_if_missing("schema_version", str(SCHEMA_VERSION))

    def _get_meta(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return str(row["value"])

    def _set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    def _set_meta_if_missing(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO NOTHING",
            (key, value),
        )

    def ensure_config(self, config: CorpusConfig) -> None:
        stored = self._get_meta("config_json")
        if stored is None:
            self._set_meta("config_json", json.dumps(config.to_jsonable(), sort_keys=True))
            self.conn.commit()
            return

        try:
            parsed = json.loads(stored)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Corpus has invalid config_json") from exc

        expected = config.to_jsonable()
        if parsed != expected:
            raise RuntimeError(
                "Corpus config mismatch. Refusing to mix generator semantics.\n"
                f"stored={parsed}\nexpected={expected}"
            )

    def ensure_seed(self) -> None:
        one = (1, 1)
        row = self.conn.execute(
            "SELECT 1 FROM canon_values WHERE p=? AND q=?", one
        ).fetchone()
        if row is not None:
            return

        self.conn.execute(
            "INSERT INTO canon_values(p, q, first_seen_round) VALUES(?, ?, ?)",
            (1, 1, 0),
        )
        self.conn.execute(
            "INSERT INTO occurrences(round, p, q, op, meta_json) VALUES(?, ?, ?, ?, ?)",
            (0, 1, 1, "seed", json.dumps({"note": "S0 seed Ref(1)"}, sort_keys=True)),
        )
        self.append_event("round_started", {"round": 0}, round_idx=0)
        self.append_event("round_completed", {"round": 0, "new_values": 1}, round_idx=0)
        self.conn.execute(
            "INSERT INTO rounds(round, size_prev, size_now, new_values) VALUES(?, ?, ?, ?)",
            (0, 0, 1, 1),
        )
        self.conn.commit()

    def max_round(self) -> int:
        row = self.conn.execute("SELECT MAX(round) AS r FROM rounds").fetchone()
        if row is None or row["r"] is None:
            return 0
        return int(row["r"])

    def load_values(self) -> Dict[Tuple[int, int], int]:
        rows = self.conn.execute(
            "SELECT p, q, first_seen_round FROM canon_values"
        ).fetchall()
        out: Dict[Tuple[int, int], int] = {}
        for row in rows:
            key = (int(row["p"]), int(row["q"]))
            out[key] = int(row["first_seen_round"])
        return out

    def upsert_targets(self, targets: Sequence[Tuple[str, float]]) -> None:
        self.conn.executemany(
            "INSERT INTO targets(name, value) VALUES(?, ?) "
            "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
            [(str(name), float(value)) for name, value in targets],
        )

    def insert_new_value(
        self,
        *,
        value: Fraction,
        first_seen_round: int,
        op: str,
        a: Optional[Fraction],
        b: Optional[Fraction],
        meta: Optional[Dict[str, object]] = None,
    ) -> None:
        p, q = _fraction_key(value)
        self.conn.execute(
            "INSERT INTO canon_values(p, q, first_seen_round) VALUES(?, ?, ?)",
            (p, q, int(first_seen_round)),
        )
        a_key = _fraction_key(a) if a is not None else None
        b_key = _fraction_key(b) if b is not None else None
        meta_json = json.dumps(meta or {}, sort_keys=True)
        self.conn.execute(
            "INSERT INTO occurrences(round, p, q, op, a_p, a_q, b_p, b_q, meta_json) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                int(first_seen_round),
                p,
                q,
                str(op),
                a_key[0] if a_key is not None else None,
                a_key[1] if a_key is not None else None,
                b_key[0] if b_key is not None else None,
                b_key[1] if b_key is not None else None,
                meta_json,
            ),
        )

    def record_round(self, *, round_idx: int, size_prev: int, size_now: int, new_values: int) -> None:
        self.conn.execute(
            "INSERT INTO rounds(round, size_prev, size_now, new_values) VALUES(?, ?, ?, ?)",
            (int(round_idx), int(size_prev), int(size_now), int(new_values)),
        )

    def append_event(self, event_type: str, payload: Dict[str, object], *, round_idx: Optional[int]) -> None:
        self.conn.execute(
            "INSERT INTO events(round, event_type, payload_json) VALUES(?, ?, ?)",
            (
                int(round_idx) if round_idx is not None else None,
                str(event_type),
                json.dumps(payload, sort_keys=True),
            ),
        )

    def last_best_so_far(self, target_name: str) -> Optional[Tuple[float, int, int]]:
        row = self.conn.execute(
            "SELECT best_error, best_p, best_q FROM probe_best "
            "WHERE target_name = ? AND is_best_so_far = 1 "
            "ORDER BY round DESC LIMIT 1",
            (str(target_name),),
        ).fetchone()
        if row is None:
            return None
        return float(row["best_error"]), int(row["best_p"]), int(row["best_q"])

    def insert_probe_best(
        self,
        *,
        target_name: str,
        round_idx: int,
        best_value: Fraction,
        best_error: float,
        best_first_seen_round: int,
        is_best_so_far: bool,
        baseline_value: Fraction,
        baseline_error: float,
    ) -> None:
        best_p, best_q = _fraction_key(best_value)
        base_p, base_q = _fraction_key(baseline_value)
        self.conn.execute(
            "INSERT INTO probe_best("
            "  target_name, round, best_p, best_q, best_error, best_first_seen_round, is_best_so_far,"
            "  baseline_p, baseline_q, baseline_error"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(target_name),
                int(round_idx),
                best_p,
                best_q,
                float(best_error),
                int(best_first_seen_round),
                1 if is_best_so_far else 0,
                base_p,
                base_q,
                float(baseline_error),
            ),
        )

    def commit(self) -> None:
        self.conn.commit()

    def __enter__(self) -> "Corpus":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.close()


def bounded(value: Fraction, *, config: CorpusConfig) -> bool:
    p = int(value.numerator)
    q = int(value.denominator)
    if q <= 0:
        return False
    if abs(p) > config.max_abs_p:
        return False
    if abs(q) > config.max_abs_q:
        return False
    if config.max_abs_value is not None and abs(float(value)) > config.max_abs_value:
        return False
    return True


def best_baseline_for_target(
    *,
    target: float,
    config: CorpusConfig,
) -> Tuple[Fraction, float]:
    """
    Baseline: best rational p/q within bounds, optimizing |p/q - target|.

    This ignores MoO generation order and serves as a null model for "how good can the
    window get, regardless of emergence?".
    """
    best: Optional[Tuple[float, Fraction]] = None
    max_q = int(config.max_abs_q)
    max_p = int(config.max_abs_p)
    for q in range(1, max_q + 1):
        p0 = int(round(float(target) * q))
        for p in (p0 - 1, p0, p0 + 1):
            if abs(p) > max_p:
                continue
            f = Fraction(int(p), int(q))
            if not bounded(f, config=config):
                continue
            err = abs(float(f) - float(target))
            if best is None or err < best[0]:
                best = (float(err), f)
    if best is None:
        return Fraction(0, 1), float("inf")
    return best[1], float(best[0])
