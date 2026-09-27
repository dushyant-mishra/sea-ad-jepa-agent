"""Independent, data-free V29 protocol-v4 edge-case fixtures.

These tests establish necessary properties of the mathematical contracts. They
DO NOT validate Claude's future NB-GLM/permutation implementation or real-data
biology; wire their adversarial examples into that implementation separately.
"""
from __future__ import annotations

import math
import unittest


def loo_center(values):
    n = len(values)
    if n < 2:
        raise ValueError("requires >=2 cells in stratum")
    total = sum(values)
    return [(n * y - total) / (n - 1) for y in values]


def clr_with_pseudocount(counts, pseudo):
    x = [math.log(v + pseudo) for v in counts]
    mean = sum(x) / len(x)
    return [v - mean for v in x]


class V29IndependentProtocolContractTests(unittest.TestCase):
    def test_loo_centered_counts_are_not_nb_glm_responses(self):
        raw = [0, 4, 12, 12]
        centered = loo_center(raw)
        self.assertLess(min(centered), 0)
        self.assertTrue(any(v != int(v) for v in centered))
        self.assertTrue(all(isinstance(v, int) and v >= 0 for v in raw))

    def test_loo_centering_does_not_require_evaluation_outcomes_for_within_stratum_rank(self):
        raw = [0, 4, 12, 12]
        centered = loo_center(raw)
        for i in range(len(raw)):
            for j in range(len(raw)):
                self.assertEqual((raw[i] > raw[j]) - (raw[i] < raw[j]),
                                 (centered[i] > centered[j]) -
                                 (centered[i] < centered[j]))

    def test_zero_aware_clr_is_not_invariant_to_common_count_scaling(self):
        x1 = clr_with_pseudocount([1, 0, 0, 0], 0.5)
        x10 = clr_with_pseudocount([10, 0, 0, 0], 0.5)
        self.assertGreater(max(abs(a-b) for a, b in zip(x1, x10)), 0.5)
        y1 = clr_with_pseudocount([1, 2, 3, 4], 0)
        y10 = clr_with_pseudocount([10, 20, 30, 40], 0)
        self.assertTrue(all(abs(a-b) < 1e-12 for a, b in zip(y1, y10)))

    def test_shared_denominator_correlates_constant_independent_numerators(self):
        D = [25, 40, 80, 160]
        p = [math.log1p(10000 / d) for d in D]
        q = [math.log1p(20000 / d) for d in D]
        self.assertEqual(sorted(p), p[::-1])
        self.assertEqual(sorted(q), q[::-1])
        self.assertEqual(sorted(range(4), key=p.__getitem__),
                         sorted(range(4), key=q.__getitem__))

    def test_revised_control_module_has_nineteen_not_twenty_genes(self):
        ambient = "SNAP25 SYT1 RBFOX3 PLP1 MBP MOBP GFAP AQP4 SLC1A2 FLT1".split()
        myeloid = "AIF1 ITGAM SPI1 FCER1G TYROBP LAPTM5".split()
        mitochondrial = "MT-CO1 MT-ND1 MT-ATP6".split()
        genes = ambient + myeloid + mitochondrial
        self.assertEqual(len(genes), 19)
        self.assertEqual(len(set(genes)), 19)
        self.assertNotIn("MEG3", genes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
