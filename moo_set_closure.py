from __future__ import annotations

from fractions import Fraction
from typing import Callable, Dict, Optional, Set, Tuple


Witness = Tuple[str, Fraction, Fraction]


def complexity_key(value: Fraction) -> Tuple[int, int, int]:
    """
    Deterministic tie-break / enumeration key for rationals.

    Preference order:
    - smaller denominators
    - smaller |numerator|
    - smaller numerator (stable sign ordering)
    """
    return (int(value.denominator), abs(int(value.numerator)), int(value.numerator))


def bounded(
    value: Fraction,
    *,
    max_abs_p: int,
    max_abs_q: int,
    max_abs_value: Optional[float],
) -> bool:
    p = int(value.numerator)
    q = int(value.denominator)
    if q <= 0:
        return False
    if abs(p) > int(max_abs_p):
        return False
    if abs(q) > int(max_abs_q):
        return False
    if max_abs_value is not None and abs(float(value)) > float(max_abs_value):
        return False
    return True


def closure_round_delta(
    *,
    s_prev: Set[Fraction],
    delta_prev: Set[Fraction],
    allow: Callable[[Fraction], bool],
) -> Tuple[Set[Fraction], Dict[Fraction, Witness]]:
    """
    One incremental closure round from {1} under + - * /.

    This computes the next-round delta by combining only the previous round's
    delta with the previous round's set:

      delta_{n+1} = {a op b : a in delta_n, b in S_n} \\ S_n

    This is sufficient for closure-round semantics because any "new" value must
    involve at least one newly introduced operand.

    Returns:
      (new_delta, witness) where witness[out] = (op, a, b) for the first
      construction observed in the deterministic enumeration order.
    """
    s_list = sorted(s_prev, key=complexity_key)
    delta_list = sorted(delta_prev, key=complexity_key)
    new_delta: Set[Fraction] = set()
    witness: Dict[Fraction, Witness] = {}

    for a in delta_list:
        for b in s_list:
            candidates = [
                ("+", a + b),
                ("*", a * b),
                ("-", a - b),
                ("-", b - a),
            ]
            if b != 0:
                candidates.append(("/", a / b))
            if a != 0:
                candidates.append(("/", b / a))

            for op, out in candidates:
                if out in s_prev or out in new_delta:
                    continue
                if not allow(out):
                    continue
                new_delta.add(out)
                witness.setdefault(out, (op, a, b))

    return new_delta, witness

