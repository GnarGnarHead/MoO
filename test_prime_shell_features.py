from __future__ import annotations

import unittest
from fractions import Fraction

from prime_shell_features import (
    factor_record,
    integerize_shell,
    prime_factorization,
    shell_prime_profile,
    squarefree_kernel,
)


class PrimeShellFeatureTests(unittest.TestCase):
    def test_factor_record_tracks_mod4_obstruction(self) -> None:
        record = factor_record(21)

        self.assertEqual(prime_factorization(21), {3: 1, 7: 1})
        self.assertEqual(record["odd_3mod4_prime_exponents"], [3, 7])
        self.assertTrue(record["fermat_two_square_obstruction"]["present"])
        self.assertEqual(squarefree_kernel(45), 5)

    def test_integerize_shell_clears_rational_denominators(self) -> None:
        payload = integerize_shell(Fraction(3, 5), Fraction(4, 5), Fraction(1, 1))

        self.assertEqual(payload["common_denominator"], 5)
        self.assertEqual(payload["integerized_triple"], {"x": 3, "y": 4, "r": 5})
        self.assertEqual(payload["primitive_integer_triple"], {"x": 3, "y": 4, "r": 5})
        self.assertTrue(payload["integerized_check"]["exact"])

    def test_shell_prime_profile_recovers_euclid_parameters(self) -> None:
        profile = shell_prime_profile(Fraction(3, 4), Fraction(1, 1), Fraction(5, 4))
        euclid = profile["euclid_parameters"]

        self.assertEqual(profile["integer_normalization"]["common_denominator"], 4)
        self.assertEqual(
            profile["integer_normalization"]["primitive_integer_triple"],
            {"x": 3, "y": 4, "r": 5},
        )
        self.assertTrue(euclid["parameter_found"])
        self.assertEqual(euclid["parameters"]["m"], 2)
        self.assertEqual(euclid["parameters"]["n"], 1)
        self.assertEqual(euclid["parameters"]["m2_minus_n2"], 3)
        self.assertEqual(euclid["parameters"]["two_mn"], 4)
        self.assertEqual(euclid["parameters"]["m2_plus_n2"], 5)


if __name__ == "__main__":
    unittest.main()
