from __future__ import annotations

from fractions import Fraction
from math import gcd, isqrt
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from rational_baselines import fraction_payload


IntTriple = Tuple[int, int, int]


def _lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(int(a) * int(b)) // gcd(int(a), int(b))


def lcm_many(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        result = _lcm(result, int(value))
    return result


def gcd_many(values: Iterable[int]) -> int:
    result = 0
    for value in values:
        result = gcd(result, abs(int(value)))
    return result


def prime_factorization(n: int) -> Dict[int, int]:
    value = abs(int(n))
    if value < 2:
        return {}

    factors: Dict[int, int] = {}
    while value % 2 == 0:
        factors[2] = factors.get(2, 0) + 1
        value //= 2

    divisor = 3
    while divisor * divisor <= value:
        while value % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            value //= divisor
        divisor += 2

    if value > 1:
        factors[value] = factors.get(value, 0) + 1
    return factors


def squarefree_kernel(n: int) -> int:
    kernel = 1
    for prime, exponent in prime_factorization(n).items():
        if exponent % 2:
            kernel *= int(prime)
    return kernel


def _mod4_class_counts(factors: Dict[int, int]) -> Dict[str, int]:
    counts = {"0": 0, "1": 0, "2": 0, "3": 0}
    for prime, exponent in factors.items():
        counts[str(int(prime) % 4)] += int(exponent)
    return counts


def _factor_list(factors: Dict[int, int]) -> List[Dict[str, int]]:
    return [
        {
            "prime": int(prime),
            "exponent": int(exponent),
            "mod4": int(prime) % 4,
        }
        for prime, exponent in sorted(factors.items())
    ]


def factor_record(n: int) -> Dict[str, object]:
    value = int(n)
    factors = prime_factorization(value)
    odd_3mod4 = [
        int(prime)
        for prime, exponent in sorted(factors.items())
        if int(prime) % 4 == 3 and int(exponent) % 2 == 1
    ]
    return {
        "integer": value,
        "abs": abs(value),
        "sign": -1 if value < 0 else 1 if value > 0 else 0,
        "is_zero": value == 0,
        "is_unit": abs(value) == 1,
        "factors": _factor_list(factors),
        "mod4_class_exponent_counts": _mod4_class_counts(factors),
        "squarefree_kernel": squarefree_kernel(value),
        "odd_3mod4_prime_exponents": odd_3mod4,
        "fermat_two_square_obstruction": {
            "applicable": value >= 0,
            "present": bool(odd_3mod4) if value >= 0 else None,
            "odd_3mod4_primes": odd_3mod4 if value >= 0 else [],
        },
    }


def fraction_factor_record(value: Fraction) -> Dict[str, object]:
    frac = Fraction(value)
    return {
        "value": fraction_payload(frac),
        "numerator": factor_record(int(frac.numerator)),
        "denominator": factor_record(int(frac.denominator)),
    }


def integerize_shell(x: Fraction, y: Fraction, r: Fraction) -> Dict[str, object]:
    values = [Fraction(x), Fraction(y), Fraction(r)]
    common_denominator = lcm_many(value.denominator for value in values)
    integerized = tuple(
        int(value.numerator * (common_denominator // value.denominator))
        for value in values
    )
    reduction = gcd_many(integerized)
    primitive = tuple(
        int(component // reduction) if reduction else int(component)
        for component in integerized
    )
    return {
        "common_denominator": int(common_denominator),
        "integerized_triple": {
            "x": int(integerized[0]),
            "y": int(integerized[1]),
            "r": int(integerized[2]),
        },
        "gcd_integerized_xyz": int(reduction),
        "primitive_reduction_factor": int(reduction),
        "primitive_integer_triple": {
            "x": int(primitive[0]),
            "y": int(primitive[1]),
            "r": int(primitive[2]),
        },
        "primitive_abs_triple": {
            "x": abs(int(primitive[0])),
            "y": abs(int(primitive[1])),
            "r": abs(int(primitive[2])),
        },
        "integerized_check": {
            "form": "x*x + y*y",
            "value": int(integerized[0] * integerized[0] + integerized[1] * integerized[1]),
            "target": int(integerized[2] * integerized[2]),
            "exact": integerized[0] * integerized[0] + integerized[1] * integerized[1]
            == integerized[2] * integerized[2],
        },
    }


def _dict_to_triple(raw: Dict[str, object], key: str) -> IntTriple:
    triple = raw[key]
    if not isinstance(triple, dict):
        raise TypeError(f"{key} must be a dict")
    return int(triple["x"]), int(triple["y"]), int(triple["r"])


def _recover_euclid_parameters(abs_x: int, abs_y: int, abs_r: int) -> Optional[Dict[str, int]]:
    if abs_x <= 0 or abs_y <= 0 or abs_r <= 0:
        return None
    if abs_x * abs_x + abs_y * abs_y != abs_r * abs_r:
        return None

    leg_a, leg_b = sorted((int(abs_x), int(abs_y)))
    for n in range(1, isqrt(abs_r) + 1):
        for m in range(n + 1, isqrt(abs_r) + 2):
            if m * m + n * n != abs_r:
                continue
            generated_odd = m * m - n * n
            generated_even = 2 * m * n
            if sorted((generated_odd, generated_even)) != [leg_a, leg_b]:
                continue
            return {
                "m": int(m),
                "n": int(n),
                "m2": int(m * m),
                "n2": int(n * n),
                "m2_minus_n2": int(generated_odd),
                "two_mn": int(generated_even),
                "m2_plus_n2": int(abs_r),
                "gcd_mn": int(gcd(m, n)),
                "opposite_parity": (m - n) % 2 == 1,
            }
    return None


def euclid_parameter_profile(primitive_abs_triple: IntTriple) -> Dict[str, object]:
    abs_x, abs_y, abs_r = (abs(int(part)) for part in primitive_abs_triple)
    parameters = _recover_euclid_parameters(abs_x, abs_y, abs_r)
    if parameters is None:
        return {
            "parameter_found": False,
            "reason": "primitive triple did not match Euclid parameter constraints",
            "parameters": None,
        }

    m = int(parameters["m"])
    n = int(parameters["n"])
    return {
        "parameter_found": True,
        "reason": None,
        "parameters": parameters,
        "factorization": {
            "m": factor_record(m),
            "n": factor_record(n),
            "m2": factor_record(m * m),
            "n2": factor_record(n * n),
            "m2_minus_n2": factor_record(int(parameters["m2_minus_n2"])),
            "two_mn": factor_record(int(parameters["two_mn"])),
            "m2_plus_n2": factor_record(int(parameters["m2_plus_n2"])),
        },
    }


def shell_prime_profile(x: Fraction, y: Fraction, r: Fraction) -> Dict[str, object]:
    normalized = {
        "x": fraction_payload(Fraction(x)),
        "y": fraction_payload(Fraction(y)),
        "r": fraction_payload(Fraction(r)),
    }
    integerized = integerize_shell(Fraction(x), Fraction(y), Fraction(r))
    integer_triple = _dict_to_triple(integerized, "integerized_triple")
    primitive_triple = _dict_to_triple(integerized, "primitive_integer_triple")
    primitive_abs_triple = _dict_to_triple(integerized, "primitive_abs_triple")
    euclid = euclid_parameter_profile(primitive_abs_triple)
    return {
        "profile_version": "prime_shell_features.v1",
        "normalization_note": (
            "Prime and Euclid-parameter features are computed after clearing rational "
            "denominators and reducing to a primitive integer triple."
        ),
        "rational_shell": normalized,
        "integer_normalization": integerized,
        "factorization": {
            "rational_components": {
                "x": fraction_factor_record(Fraction(x)),
                "y": fraction_factor_record(Fraction(y)),
                "r": fraction_factor_record(Fraction(r)),
            },
            "integerized_triple": {
                "x": factor_record(integer_triple[0]),
                "y": factor_record(integer_triple[1]),
                "r": factor_record(integer_triple[2]),
            },
            "primitive_integer_triple": {
                "x": factor_record(primitive_triple[0]),
                "y": factor_record(primitive_triple[1]),
                "r": factor_record(primitive_triple[2]),
            },
            "primitive_norm_warning": (
                "Factoring r*r is tautological for two-square obstruction because all "
                "prime exponents are even; inspect r and Euclid parameters instead."
            ),
            "primitive_norm_r_square": factor_record(primitive_abs_triple[2] * primitive_abs_triple[2]),
        },
        "euclid_parameters": euclid,
    }
