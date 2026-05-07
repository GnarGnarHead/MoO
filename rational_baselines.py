from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple


Key = Tuple[int, int]


def normalize_key(p: int, q: int = 1) -> Key:
    if q == 0:
        raise ZeroDivisionError("zero denominator")
    value = Fraction(int(p), int(q))
    return int(value.numerator), int(value.denominator)


def parse_key(raw: str) -> Key:
    value = Fraction(str(raw))
    return normalize_key(int(value.numerator), int(value.denominator))


def format_key(key: Key) -> str:
    p, q = normalize_key(*key)
    if q == 1:
        return str(p)
    return f"{p}/{q}"


def fraction_payload(value: Fraction) -> Dict[str, object]:
    key = normalize_key(value.numerator, value.denominator)
    return {
        "frac": format_key(key),
        "p": int(key[0]),
        "q": int(key[1]),
    }


def continued_fraction(value: Fraction) -> List[int]:
    n = int(value.numerator)
    d = int(value.denominator)
    terms: List[int] = []
    while d:
        a = n // d
        terms.append(int(a))
        n, d = d, n - a * d
    return terms


def _append_run(runs: List[Tuple[str, int]], turn: str) -> None:
    if runs and runs[-1][0] == turn:
        prev_turn, prev_count = runs[-1]
        runs[-1] = prev_turn, prev_count + 1
    else:
        runs.append((turn, 1))


def stern_brocot_path(value: Fraction) -> Dict[str, object]:
    p = int(value.numerator)
    q = int(value.denominator)
    if p <= 0:
        return {
            "applicable": False,
            "reason": "Stern-Brocot path is reported only for positive rationals.",
            "depth": None,
            "path": None,
            "path_runs": [],
        }

    left_p, left_q = 0, 1
    right_p, right_q = 1, 0
    runs: List[Tuple[str, int]] = []

    while True:
        mid_p = left_p + right_p
        mid_q = left_q + right_q
        cmp = p * mid_q - mid_p * q
        if cmp == 0:
            break
        if cmp > 0:
            left_p, left_q = mid_p, mid_q
            _append_run(runs, "R")
        else:
            right_p, right_q = mid_p, mid_q
            _append_run(runs, "L")

    depth = sum(count for _, count in runs)
    path_runs = [{"turn": turn, "count": count} for turn, count in runs]
    path: Optional[str]
    if depth <= 128:
        path = "".join(turn * count for turn, count in runs)
    else:
        path = None
    return {
        "applicable": True,
        "reason": None,
        "depth": int(depth),
        "path": path,
        "path_runs": path_runs,
    }


def farey_neighbors(value: Fraction, order: Optional[int] = None) -> Dict[str, object]:
    n = int(order) if order is not None else int(value.denominator)
    if n < 1:
        raise ValueError("Farey order must be at least 1")

    p = int(value.numerator)
    q = int(value.denominator)
    left: Optional[Fraction] = None
    right: Optional[Fraction] = None

    for d in range(1, n + 1):
        left_n = (p * d - 1) // q
        left_candidate = Fraction(left_n, d)
        if left_candidate < value and (left is None or left_candidate > left):
            left = left_candidate

        right_n = (p * d) // q + 1
        right_candidate = Fraction(right_n, d)
        if right_candidate > value and (right is None or right_candidate < right):
            right = right_candidate

    return {
        "order": int(n),
        "left": fraction_payload(left) if left is not None else None,
        "right": fraction_payload(right) if right is not None else None,
    }


def _max_abs(values: Sequence[int]) -> int:
    return max((abs(int(value)) for value in values), default=0)


def baseline_features(key: Key) -> Dict[str, object]:
    p, q = normalize_key(*key)
    value = Fraction(p, q)
    terms = continued_fraction(value)
    stern_brocot = stern_brocot_path(value)
    return {
        "frac": format_key((p, q)),
        "p": int(p),
        "q": int(q),
        "value_float": float(value),
        "denominator_height": int(q),
        "numerator_abs": abs(int(p)),
        "component_height": max(abs(int(p)), int(q)),
        "continued_fraction": {
            "terms": terms,
            "length": len(terms),
            "max_abs_partial_quotient": _max_abs(terms),
        },
        "stern_brocot": stern_brocot,
        "farey": farey_neighbors(value, order=q),
    }
