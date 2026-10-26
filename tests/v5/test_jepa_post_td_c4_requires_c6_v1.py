from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_harness_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("jepa_post_td_harness_contract_v1", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


class C4RequiresC6Tests(unittest.TestCase):
    def test_c4_is_blocked_without_independently_qualified_c6(self):
        with self.assertRaisesRegex(M.PostTDContractError, "C6"):
            M.build_target_portfolio(
                selected_candidate="C4",
                qualifications={
                    "C1": "PASS",
                    "C2": "PASS",
                    "C3": "PASS",
                    "C4": "PASS",
                },
            )

    def test_c4_is_blocked_when_c6_not_estimable_or_failed(self):
        for status in ("FAIL", "NOT_ESTIMABLE"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(M.PostTDContractError, "C6"):
                    M.build_target_portfolio(
                        selected_candidate="C4",
                        qualifications={
                            "C1": "PASS",
                            "C2": "PASS",
                            "C3": "PASS",
                            "C6": status,
                            "C4": "PASS",
                        },
                    )

    def test_c4_remains_available_after_c6_and_all_constituents_pass(self):
        portfolio = M.build_target_portfolio(
            selected_candidate="C4",
            qualifications={
                "C1": "PASS",
                "C2": "PASS",
                "C3": "PASS",
                "C6": "PASS",
                "C4": "PASS",
            },
        )
        self.assertEqual(portfolio["fused_candidate"], "C4")
        self.assertEqual(
            [block["candidate"] for block in portfolio["blocks"]],
            ["C1", "C3", "C2"],
        )

    def test_c4_failure_still_does_not_delete_independent_blocks(self):
        portfolio = M.build_target_portfolio(
            foundation_candidates=("C1", "C2", "C3"),
            qualifications={
                "C1": "PASS",
                "C2": "PASS",
                "C3": "PASS",
                "C6": "PASS",
                "C4": "FAIL",
            },
        )
        self.assertEqual(
            [block["candidate"] for block in portfolio["blocks"]],
            ["C1", "C2", "C3"],
        )


if __name__ == "__main__":
    unittest.main()
