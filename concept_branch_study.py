from __future__ import annotations

import argparse
import json
import math
import signal
from collections import Counter
from fractions import Fraction
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Sequence, Tuple


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


def _load_report(path: Path) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Report is not a JSON object: {path}")
    if not isinstance(payload.get("ledger"), list):
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


def _config(report: Dict[str, object]) -> Dict[str, object]:
    config = report.get("config")
    return dict(config) if isinstance(config, dict) else {}


def _complexity_key(value: Fraction) -> Tuple[int, int, int]:
    return (int(value.denominator), abs(int(value.numerator)), int(value.numerator))


def _is_square_int(value: int) -> bool:
    if value < 0:
        return False
    root = math.isqrt(value)
    return root * root == value


def _is_exact_rational_square(value: Fraction) -> bool:
    if value < 0:
        return False
    return _is_square_int(int(value.numerator)) and _is_square_int(int(value.denominator))


def _sqrt_fraction(value: Fraction) -> Optional[Fraction]:
    if not _is_exact_rational_square(value):
        return None
    return Fraction(math.isqrt(int(value.numerator)), math.isqrt(int(value.denominator)))


def _witness(row: Optional[Dict[str, object]]) -> Tuple[Optional[str], Optional[Fraction], Optional[Fraction]]:
    if row is None:
        return None, None, None
    witness = row.get("first_witness")
    if not isinstance(witness, dict):
        return None, None, None
    op_raw = witness.get("op")
    op = str(op_raw) if op_raw is not None else None
    return op, _parse_fraction(witness.get("a")), _parse_fraction(witness.get("b"))


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


def _operation_signature(row: Optional[Dict[str, object]]) -> Dict[str, int]:
    signature = row.get("operation_signature") if isinstance(row, dict) else None
    if not isinstance(signature, dict):
        return {op: 0 for op in ["+", "-", "*", "/"]}
    return {op: _row_int(signature, op, 0) for op in ["+", "-", "*", "/"]}


def _operation_share(row: Optional[Dict[str, object]], op: str) -> float:
    signature = _operation_signature(row)
    total = sum(signature.values())
    if total <= 0:
        return 0.0
    return float(signature.get(op, 0) / total)


def _addition_share(row: Optional[Dict[str, object]]) -> float:
    return _operation_share(row, "+")


def _multiplication_share(row: Optional[Dict[str, object]]) -> float:
    return _operation_share(row, "*")


def _division_share(row: Optional[Dict[str, object]]) -> float:
    return _operation_share(row, "/")


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


def _safe_median(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return float(median(values))


def _root_rows(
    value: Fraction,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> List[Tuple[Fraction, Dict[str, object]]]:
    root = _sqrt_fraction(value)
    if root is None:
        return []
    roots = [root] if root == 0 else sorted({root, -root}, key=_complexity_key)
    out: List[Tuple[Fraction, Dict[str, object]]] = []
    for candidate in roots:
        row = rows_by_frac.get(candidate)
        if row is not None:
            out.append((candidate, row))
    return out


def _first_available_self_product_round(
    value: Fraction,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Optional[int]:
    roots = _root_rows(value, rows_by_frac)
    if not roots:
        return None
    earliest_root_round = min(_row_int(row, "first_seen_round", 999999) for _, row in roots)
    if earliest_root_round >= 999999:
        return None
    return int(earliest_root_round + 1)


def _is_self_product_first_witness(value: Fraction, row: Optional[Dict[str, object]]) -> bool:
    op, a, b = _witness(row)
    return bool(op == "*" and a is not None and b is not None and a == b and a * b == value)


def _is_integer_square_scaffold(value: Fraction) -> bool:
    return value.denominator == 1 and _is_square_int(int(value.numerator))


def _integer_square_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    n = math.isqrt(int(value.numerator)) if value >= 0 and value.denominator == 1 else 0
    prev_square = Fraction((n - 1) * (n - 1), 1) if n > 0 else None
    odd_increment = Fraction(2 * n - 1, 1) if n > 0 else None
    prev_row = rows_by_frac.get(prev_square) if prev_square is not None else None
    odd_row = rows_by_frac.get(odd_increment) if odd_increment is not None else None
    return {
        "frac": _format_fraction(value),
        "n": int(n),
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "first_witness": _witness_payload(row),
        "previous_square": _format_fraction(prev_square) if prev_square is not None else None,
        "odd_increment": _format_fraction(odd_increment) if odd_increment is not None else None,
        "previous_square_present": prev_row is not None if prev_square is not None else None,
        "odd_increment_present": odd_row is not None if odd_increment is not None else None,
        "odd_increment_relation": (
            f"{_format_fraction(prev_square)} + {_format_fraction(odd_increment)} = {_format_fraction(value)}"
            if prev_square is not None and odd_increment is not None
            else None
        ),
    }


def _square_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    root = _sqrt_fraction(value)
    roots = _root_rows(value, rows_by_frac)
    first_available_round = _first_available_self_product_round(value, rows_by_frac)
    value_round = _row_int(row, "first_seen_round", -1)
    root_payloads = [
        {
            "frac": _format_fraction(root_value),
            "first_seen_round": _row_int(root_row, "first_seen_round", -1),
            "first_witness": _witness_payload(root_row),
        }
        for root_value, root_row in roots
    ]
    timing = "missing_root"
    if first_available_round is not None:
        if value_round < first_available_round:
            timing = "arrived_before_self_product_available"
        elif value_round == first_available_round:
            timing = "arrived_when_self_product_first_available"
        else:
            timing = "arrived_after_self_product_available"
    return {
        "frac": _format_fraction(value),
        "p": int(value.numerator),
        "q": int(value.denominator),
        "value": float(value),
        "sqrt_abs": _format_fraction(root) if root is not None else None,
        "roots_present": root_payloads,
        "first_seen_round": value_round,
        "first_witness": _witness_payload(row),
        "derivation_events": _row_int(row, "derivation_events", 0),
        "operation_signature": _operation_signature(row),
        "addition_share": _addition_share(row),
        "multiplication_share": _multiplication_share(row),
        "division_share": _division_share(row),
        "denominator_bucket": _denominator_bucket(value.denominator),
        "is_integer_square_scaffold": _is_integer_square_scaffold(value),
        "self_product_first_witness": _is_self_product_first_witness(value, row),
        "first_available_self_product_round": first_available_round,
        "self_product_timing": timing,
    }


def _triangle_roots(value: Fraction) -> List[Fraction]:
    if value < 0:
        return []
    discriminant = Fraction(1, 1) + 8 * value
    root = _sqrt_fraction(discriminant)
    if root is None:
        return []
    return sorted({(-1 + root) / 2, (-1 - root) / 2}, key=_complexity_key)


def _is_exact_rational_triangle(value: Fraction) -> bool:
    return bool(_triangle_roots(value))


def _triangle_root_rows(
    value: Fraction,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> List[Tuple[Fraction, Dict[str, object]]]:
    out: List[Tuple[Fraction, Dict[str, object]]] = []
    for candidate in _triangle_roots(value):
        row = rows_by_frac.get(candidate)
        if row is not None:
            out.append((candidate, row))
    return out


def _triangle_formula_routes(
    value: Fraction,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> List[Dict[str, object]]:
    half = Fraction(1, 2)
    half_row = rows_by_frac.get(half)
    if half_row is None:
        return []
    routes: List[Dict[str, object]] = []
    half_round = _row_int(half_row, "first_seen_round", 999999)
    for root in _triangle_roots(value):
        successor = root + 1
        product = root * successor
        root_row = rows_by_frac.get(root)
        successor_row = rows_by_frac.get(successor)
        product_row = rows_by_frac.get(product)
        if root_row is None or successor_row is None or product_row is None:
            continue
        root_round = _row_int(root_row, "first_seen_round", 999999)
        successor_round = _row_int(successor_row, "first_seen_round", 999999)
        product_seen_round = _row_int(product_row, "first_seen_round", 999999)
        product_route_round = max(root_round, successor_round) + 1
        product_available_round = product_seen_round
        formula_round = max(product_available_round, half_round) + 1
        routes.append(
            {
                "root": _format_fraction(root),
                "successor": _format_fraction(successor),
                "product": _format_fraction(product),
                "half": _format_fraction(half),
                "root_first_seen_round": root_round,
                "successor_first_seen_round": successor_round,
                "product_first_seen_round": product_seen_round,
                "product_route_round": product_route_round,
                "first_available_triangle_formula_round": formula_round,
            }
        )
    return sorted(
        routes,
        key=lambda route: (
            int(route["first_available_triangle_formula_round"]),
            _complexity_key(Fraction(str(route["root"]))),
        ),
    )


def _first_available_triangle_formula_round(
    value: Fraction,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Optional[int]:
    routes = _triangle_formula_routes(value, rows_by_frac)
    if not routes:
        return None
    return int(routes[0]["first_available_triangle_formula_round"])


def _integer_triangle_index(value: Fraction) -> Optional[int]:
    if value.denominator != 1 or value.numerator < 0:
        return None
    discriminant = 8 * int(value.numerator) + 1
    root = math.isqrt(discriminant)
    if root * root != discriminant:
        return None
    if (root - 1) % 2 != 0:
        return None
    return int((root - 1) // 2)


def _is_integer_triangle_scaffold(value: Fraction) -> bool:
    return _integer_triangle_index(value) is not None


def _integer_triangle_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    n = _integer_triangle_index(value)
    previous_triangle = Fraction((n - 1) * n // 2, 1) if n is not None and n > 0 else None
    increment = Fraction(n, 1) if n is not None and n > 0 else None
    previous_row = rows_by_frac.get(previous_triangle) if previous_triangle is not None else None
    increment_row = rows_by_frac.get(increment) if increment is not None else None
    first_available_additive_round = None
    if previous_row is not None and increment_row is not None:
        first_available_additive_round = max(
            _row_int(previous_row, "first_seen_round", 999999),
            _row_int(increment_row, "first_seen_round", 999999),
        ) + 1
    value_round = _row_int(row, "first_seen_round", -1)
    timing = "missing_additive_route"
    if first_available_additive_round is not None:
        if value_round < first_available_additive_round:
            timing = "arrived_before_additive_route_available"
        elif value_round == first_available_additive_round:
            timing = "arrived_when_additive_route_first_available"
        else:
            timing = "arrived_after_additive_route_available"
    return {
        "frac": _format_fraction(value),
        "n": int(n) if n is not None else None,
        "first_seen_round": value_round,
        "first_witness": _witness_payload(row),
        "previous_triangle": _format_fraction(previous_triangle) if previous_triangle is not None else None,
        "increment": _format_fraction(increment) if increment is not None else None,
        "previous_triangle_present": previous_row is not None if previous_triangle is not None else None,
        "increment_present": increment_row is not None if increment is not None else None,
        "additive_relation": (
            f"{_format_fraction(previous_triangle)} + {_format_fraction(increment)} = {_format_fraction(value)}"
            if previous_triangle is not None and increment is not None
            else None
        ),
        "first_available_additive_round": first_available_additive_round,
        "additive_timing": timing,
    }


def _triangle_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    value_round = _row_int(row, "first_seen_round", -1)
    root_payloads = [
        {
            "frac": _format_fraction(root_value),
            "first_seen_round": _row_int(root_row, "first_seen_round", -1),
            "first_witness": _witness_payload(root_row),
        }
        for root_value, root_row in _triangle_root_rows(value, rows_by_frac)
    ]
    routes = _triangle_formula_routes(value, rows_by_frac)
    first_available_round = int(routes[0]["first_available_triangle_formula_round"]) if routes else None
    timing = "missing_formula_route"
    if first_available_round is not None:
        if value_round < first_available_round:
            timing = "arrived_before_formula_route_available"
        elif value_round == first_available_round:
            timing = "arrived_when_formula_route_first_available"
        else:
            timing = "arrived_after_formula_route_available"
    return {
        "frac": _format_fraction(value),
        "p": int(value.numerator),
        "q": int(value.denominator),
        "value": float(value),
        "triangle_roots_present": root_payloads,
        "triangle_formula_routes": routes,
        "first_seen_round": value_round,
        "first_witness": _witness_payload(row),
        "derivation_events": _row_int(row, "derivation_events", 0),
        "operation_signature": _operation_signature(row),
        "addition_share": _addition_share(row),
        "multiplication_share": _multiplication_share(row),
        "division_share": _division_share(row),
        "denominator_bucket": _denominator_bucket(value.denominator),
        "is_integer_triangle_scaffold": _is_integer_triangle_scaffold(value),
        "first_available_triangle_formula_round": first_available_round,
        "triangle_formula_timing": timing,
    }


def _anchor_payload(
    value: Fraction,
    *,
    rows_by_frac: Dict[Fraction, Dict[str, object]],
) -> Dict[str, object]:
    row = rows_by_frac.get(value)
    return {
        "frac": _format_fraction(value),
        "present": row is not None,
        "first_seen_round": _row_int(row, "first_seen_round", -1),
        "first_witness": _witness_payload(row),
        "derivation_events": _row_int(row, "derivation_events", 0),
        "operation_signature": _operation_signature(row),
        "addition_share": _addition_share(row),
        "multiplication_share": _multiplication_share(row),
        "division_share": _division_share(row),
    }


def _top_rows(rows: Sequence[Dict[str, object]], *, key, limit: int) -> List[Dict[str, object]]:
    return [dict(row) for row in sorted(rows, key=key)[: max(0, int(limit))]]


def _cohort_stats(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    return {
        "count": len(rows),
        "first_seen_counts": {
            str(key): int(value)
            for key, value in sorted(Counter(_row_int(row, "first_seen_round", -1) for row in rows).items())
        },
        "denominator_buckets": {
            str(key): int(value)
            for key, value in sorted(Counter(str(row.get("denominator_bucket", "unknown")) for row in rows).items())
        },
        "median_derivation_events": _safe_median([float(_row_int(row, "derivation_events", 0)) for row in rows]),
        "median_addition_share": _safe_median([float(row.get("addition_share", 0.0)) for row in rows]),
        "median_multiplication_share": _safe_median([float(row.get("multiplication_share", 0.0)) for row in rows]),
        "median_division_share": _safe_median([float(row.get("division_share", 0.0)) for row in rows]),
    }


def build_square_report(
    *,
    source_report_path: Path,
    top_k: int,
    include_rows: bool,
) -> Dict[str, object]:
    source = _load_report(source_report_path)
    rows_by_frac = _rows_by_frac(source)
    exact_square_values = sorted(
        [value for value in rows_by_frac if _is_exact_rational_square(value)],
        key=_complexity_key,
    )
    positive_non_square_values = sorted(
        [value for value in rows_by_frac if value > 0 and not _is_exact_rational_square(value)],
        key=_complexity_key,
    )
    square_rows = [
        _square_payload(value, rows_by_frac=rows_by_frac) for value in exact_square_values
    ]
    positive_non_square_rows = [
        {
            "frac": _format_fraction(value),
            "p": int(value.numerator),
            "q": int(value.denominator),
            "value": float(value),
            "first_seen_round": _row_int(rows_by_frac.get(value), "first_seen_round", -1),
            "derivation_events": _row_int(rows_by_frac.get(value), "derivation_events", 0),
            "operation_signature": _operation_signature(rows_by_frac.get(value)),
            "addition_share": _addition_share(rows_by_frac.get(value)),
            "multiplication_share": _multiplication_share(rows_by_frac.get(value)),
            "division_share": _division_share(rows_by_frac.get(value)),
            "denominator_bucket": _denominator_bucket(value.denominator),
        }
        for value in positive_non_square_values
    ]

    self_product_first = [row for row in square_rows if bool(row["self_product_first_witness"])]
    on_time = [
        row
        for row in square_rows
        if row.get("self_product_timing") == "arrived_when_self_product_first_available"
    ]
    before_self_product = [
        row
        for row in square_rows
        if row.get("self_product_timing") == "arrived_before_self_product_available"
    ]
    integer_squares = [
        _integer_square_payload(value, rows_by_frac=rows_by_frac)
        for value in exact_square_values
        if _is_integer_square_scaffold(value)
    ]

    report: Dict[str, object] = {
        "schema_version": 1,
        "method": {
            "source": "Concept-branch probe over a saved MoO ledger.",
            "source_report": str(source_report_path),
            "concept": "square_like",
            "runtime_semantics_changed": False,
            "native_signatures": [
                "exact rational square value class",
                "self-product first witness",
                "self-product opportunity timing",
                "integer-square odd-increment scaffold where available",
            ],
            "limitation": (
                "This uses saved first witnesses and value classes. It does not enumerate every derivation "
                "and does not add geometry to runtime semantics."
            ),
        },
        "source_config": _config(source),
        "summary": {
            "ledger_values": len(rows_by_frac),
            "positive_values": len([value for value in rows_by_frac if value > 0]),
            "exact_square_values": len(square_rows),
            "positive_non_square_values": len(positive_non_square_rows),
            "self_product_first_witness_values": len(self_product_first),
            "self_product_on_time_values": len(on_time),
            "arrived_before_self_product_available": len(before_self_product),
            "integer_square_scaffold_values": len(integer_squares),
            "square_cohort": _cohort_stats(square_rows),
            "positive_non_square_cohort": _cohort_stats(positive_non_square_rows),
        },
        "integer_square_scaffold": integer_squares,
        "rankings": {
            "self_product_first_witness": _top_rows(
                self_product_first,
                key=lambda row: (
                    _row_int(row, "first_seen_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
            "top_square_derivation_events": _top_rows(
                square_rows,
                key=lambda row: (
                    -_row_int(row, "derivation_events", 0),
                    _row_int(row, "first_seen_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
            "top_square_multiplication_share": _top_rows(
                square_rows,
                key=lambda row: (
                    -float(row.get("multiplication_share", 0.0)),
                    _row_int(row, "first_seen_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
            "arrived_before_self_product_available": _top_rows(
                before_self_product,
                key=lambda row: (
                    _row_int(row, "first_seen_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
        },
    }
    if include_rows:
        report["square_rows"] = square_rows
    return report


def build_triangle_report(
    *,
    source_report_path: Path,
    top_k: int,
    include_rows: bool,
) -> Dict[str, object]:
    source = _load_report(source_report_path)
    rows_by_frac = _rows_by_frac(source)
    exact_triangle_values = sorted(
        [value for value in rows_by_frac if _is_exact_rational_triangle(value)],
        key=_complexity_key,
    )
    positive_non_triangle_values = sorted(
        [value for value in rows_by_frac if value > 0 and not _is_exact_rational_triangle(value)],
        key=_complexity_key,
    )
    triangle_rows = [
        _triangle_payload(value, rows_by_frac=rows_by_frac) for value in exact_triangle_values
    ]
    positive_non_triangle_rows = [
        {
            "frac": _format_fraction(value),
            "p": int(value.numerator),
            "q": int(value.denominator),
            "value": float(value),
            "first_seen_round": _row_int(rows_by_frac.get(value), "first_seen_round", -1),
            "derivation_events": _row_int(rows_by_frac.get(value), "derivation_events", 0),
            "operation_signature": _operation_signature(rows_by_frac.get(value)),
            "addition_share": _addition_share(rows_by_frac.get(value)),
            "multiplication_share": _multiplication_share(rows_by_frac.get(value)),
            "division_share": _division_share(rows_by_frac.get(value)),
            "denominator_bucket": _denominator_bucket(value.denominator),
        }
        for value in positive_non_triangle_values
    ]

    formula_available = [
        row for row in triangle_rows if row.get("triangle_formula_timing") != "missing_formula_route"
    ]
    formula_on_time = [
        row
        for row in triangle_rows
        if row.get("triangle_formula_timing") == "arrived_when_formula_route_first_available"
    ]
    before_formula = [
        row
        for row in triangle_rows
        if row.get("triangle_formula_timing") == "arrived_before_formula_route_available"
    ]
    integer_triangles = [
        _integer_triangle_payload(value, rows_by_frac=rows_by_frac)
        for value in exact_triangle_values
        if _is_integer_triangle_scaffold(value)
    ]
    additive_on_time = [
        row
        for row in integer_triangles
        if row.get("additive_timing") == "arrived_when_additive_route_first_available"
    ]

    report: Dict[str, object] = {
        "schema_version": 1,
        "method": {
            "source": "Concept-branch probe over a saved MoO ledger.",
            "source_report": str(source_report_path),
            "concept": "triangle_like",
            "runtime_semantics_changed": False,
            "native_signatures": [
                "exact nonnegative rational triangular value class",
                "rational root relation t = r * (r + 1) / 2",
                "formula-route opportunity timing when the required intermediate product remains in the corpus",
                "integer triangular additive scaffold where available",
                "anchor comparison for 1, 2, 3, and 4",
            ],
            "limitation": (
                "This uses saved first witnesses and value classes. It does not enumerate every derivation, "
                "requires formula-route intermediates to be present in the bounded corpus, and does not add "
                "geometry to runtime semantics."
            ),
        },
        "source_config": _config(source),
        "summary": {
            "ledger_values": len(rows_by_frac),
            "positive_values": len([value for value in rows_by_frac if value > 0]),
            "exact_triangle_values": len(triangle_rows),
            "positive_non_triangle_values": len(positive_non_triangle_rows),
            "triangle_formula_route_available_values": len(formula_available),
            "triangle_formula_on_time_values": len(formula_on_time),
            "arrived_before_triangle_formula_route_available": len(before_formula),
            "integer_triangle_scaffold_values": len(integer_triangles),
            "integer_triangle_additive_on_time_values": len(additive_on_time),
            "triangle_cohort": _cohort_stats(triangle_rows),
            "positive_non_triangle_cohort": _cohort_stats(positive_non_triangle_rows),
        },
        "anchor_rows": [
            _anchor_payload(Fraction(n, 1), rows_by_frac=rows_by_frac) for n in [1, 2, 3, 4]
        ],
        "integer_triangle_scaffold": integer_triangles,
        "rankings": {
            "formula_route_first_available": _top_rows(
                formula_available,
                key=lambda row: (
                    _row_int(row, "first_available_triangle_formula_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
            "top_triangle_derivation_events": _top_rows(
                triangle_rows,
                key=lambda row: (
                    -_row_int(row, "derivation_events", 0),
                    _row_int(row, "first_seen_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
            "top_triangle_addition_share": _top_rows(
                triangle_rows,
                key=lambda row: (
                    -float(row.get("addition_share", 0.0)),
                    _row_int(row, "first_seen_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
            "arrived_before_formula_route_available": _top_rows(
                before_formula,
                key=lambda row: (
                    _row_int(row, "first_seen_round", 999999),
                    _complexity_key(Fraction(int(row["p"]), int(row["q"]))),
                ),
                limit=top_k,
            ),
        },
    }
    if include_rows:
        report["triangle_rows"] = triangle_rows
    return report


def build_report(
    *,
    source_report_path: Path,
    top_k: int,
    include_rows: bool,
    concept: str,
) -> Dict[str, object]:
    if concept == "square":
        return build_square_report(
            source_report_path=source_report_path,
            top_k=top_k,
            include_rows=include_rows,
        )
    if concept == "triangle":
        return build_triangle_report(
            source_report_path=source_report_path,
            top_k=top_k,
            include_rows=include_rows,
        )
    raise SystemExit(f"Unsupported concept: {concept}")


def main(argv: Optional[Sequence[str]] = None) -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description="Probe concept branches over a saved MoO ledger."
    )
    parser.add_argument("--source-report", type=str, default="out/experiments/native_r6_full.json")
    parser.add_argument("--concept", choices=["square", "triangle"], default="square")
    parser.add_argument("--top-k", type=int, default=16)
    parser.add_argument("--include-rows", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--write", type=str, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = build_report(
        source_report_path=Path(str(args.source_report)),
        top_k=max(1, int(args.top_k)),
        include_rows=bool(args.include_rows),
        concept=str(args.concept),
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
