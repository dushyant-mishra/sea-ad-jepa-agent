from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_harness_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("jepa_post_td_harness_contract_v1_multiblock", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


class TargetPortfolioMultiBlockTests(unittest.TestCase):
    def _build(self, foundations, qualifications, specialists=(), fused_candidates=()):
        return M.build_target_portfolio(
            foundation_candidates=foundations,
            qualifications=qualifications,
            specialist_candidates=specialists,
            fused_candidates=fused_candidates,
        )

    def test_c1_c3_survive_without_c6_pass(self):
        p = self._build(("C1", "C3"), {"C1": "PASS", "C3": "PASS", "C6": "FAIL"})
        self.assertEqual([b["candidate"] for b in p["blocks"]], ["C1", "C3"])
        self.assertEqual(p["foundation_candidates"], ["C1", "C3"])
        self.assertEqual(p["fused_candidates"], [])

    def test_c1_c2_c3_survive_without_c4_pass(self):
        p = self._build(
            ("C1", "C2", "C3"),
            {"C1": "PASS", "C2": "PASS", "C3": "PASS", "C4": "FAIL"},
        )
        self.assertEqual([b["candidate"] for b in p["blocks"]], ["C1", "C2", "C3"])

    def test_c6_cannot_rescue_failed_constituent(self):
        for failed in ("C1", "C3"):
            q = {"C1": "PASS", "C3": "PASS", "C6": "PASS"}
            q[failed] = "FAIL"
            with self.assertRaisesRegex(M.PostTDContractError, failed):
                self._build(("C1", "C3"), q, fused_candidates=("C6",))

    def test_c4_cannot_rescue_failed_constituent(self):
        for failed in ("C1", "C2", "C3"):
            q = {"C1": "PASS", "C2": "PASS", "C3": "PASS", "C4": "PASS"}
            q[failed] = "FAIL"
            with self.assertRaisesRegex(M.PostTDContractError, failed):
                self._build(("C1", "C2", "C3"), q, fused_candidates=("C4",))

    def test_c5_cannot_be_sole_foundation(self):
        with self.assertRaisesRegex(M.PostTDContractError, "specialist"):
            self._build(("C5",), {"C5": "PASS"})
        with self.assertRaisesRegex(M.PostTDContractError, "foundation"):
            self._build((), {"C5": "PASS"}, specialists=("C5",))

    def test_not_estimable_is_never_promoted(self):
        for candidate in ("C1", "C2", "C3"):
            with self.assertRaisesRegex(M.PostTDContractError, candidate):
                self._build((candidate,), {candidate: "NOT_ESTIMABLE"})

    def test_independent_c1_c2_and_single_blocks_remain_valid(self):
        p = self._build(("C1", "C2"), {"C1": "PASS", "C2": "PASS"})
        self.assertEqual([b["candidate"] for b in p["blocks"]], ["C1", "C2"])
        for candidate in ("C1", "C2", "C3"):
            single = self._build((candidate,), {candidate: "PASS"})
            self.assertEqual([b["candidate"] for b in single["blocks"]], [candidate])

    def test_fused_behavior_remains_optional_and_non_authorizing(self):
        c6 = self._build(
            ("C1", "C3"),
            {"C1": "PASS", "C3": "PASS", "C6": "PASS"},
            fused_candidates=("C6",),
        )
        self.assertEqual(c6["fused_candidates"], ["C6"])
        self.assertFalse(c6["authority"]["training_authorized"])
        c4 = self._build(
            ("C1", "C2", "C3"),
            {"C1": "PASS", "C2": "PASS", "C3": "PASS", "C4": "PASS"},
            fused_candidates=("C4",),
        )
        self.assertEqual(c4["fused_candidates"], ["C4"])

    def test_every_retained_block_keeps_rare_preservation_cross_cutting(self):
        p = self._build(
            ("C1", "C2", "C3"),
            {"C1": "PASS", "C2": "PASS", "C3": "PASS", "C5": "PASS"},
            specialists=("C5",),
        )
        self.assertTrue(all(b["rare_preservation_cross_cutting"] for b in p["blocks"]))


if __name__ == "__main__":
    unittest.main()
