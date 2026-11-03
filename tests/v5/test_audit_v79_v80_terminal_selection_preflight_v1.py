"""Mutation/regression proof for original V79/V80 terminal-law conflict; no fitting.

CI must provide actual frozen raw source artifacts from original PR #348.
All cases consume public/frozen synthetic contract metadata, never controller truth.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts/v5/audit_v79_v80_terminal_selection_preflight_v1.py"
spec = importlib.util.spec_from_file_location("v79v80_terminal_preflight", MODULE)
assert spec and spec.loader
A = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = A
spec.loader.exec_module(A)


class OriginalContractBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = ("V79_CONTRACT_PATH", "V80_BINDING_PATH", "V80_RECEIPT_PATH")
        missing = [name for name in names if not os.environ.get(name)]
        if missing:
            raise RuntimeError(f"CI must fetch pinned frozen historical artifacts: {missing}")
        cls.raw = [Path(os.environ[name]).read_bytes() for name in names]

    def _run(self, raws=None):
        return A.analyze_terminal_scope(*(self.raw if raws is None else raws))

    def test_01_authentic_frozen_contracts_expose_precise_terminal_split_and_block(self):
        r = self._run()
        self.assertEqual(r["status"], "BLOCKED_EXTERNAL_V79_TERMINAL_LOCK_VS_V80_291_NONREGRESSION_SELECTION")
        t = r["frozen_terminal"]
        self.assertEqual(t["index_zero_based"], 206)
        self.assertEqual(t["confirmatory_inclusive_boundary_row_count"], 207)
        self.assertEqual(t["before_terminal"], {"rows": 206, "hard_fail_class": 204, "nonhard_limit_class": 2})
        self.assertEqual(t["terminal_gate"]["hard_fail_class"], 1)
        self.assertEqual(t["post_terminal_forensic_only"], {"rows": 85, "hard_fail_class": 83, "nonhard_limit_class": 2})
        self.assertEqual(t["original_total"], {"rows": 292, "hard_fail_class": 288, "nonhard_limit_class": 4})
        self.assertEqual(len(t["confirmatory_roster_sha256"]), 64)
        self.assertEqual(len(t["forensic_roster_sha256"]), 64)

    def test_02_no_qualification_selection_model_or_training_authority(self):
        r = self._run()
        self.assertTrue(all(x is False for x in r["authority"].values()))
        self.assertFalse(r["frozen_v80_requirement"]["reconciliation_issued"])
        self.assertEqual(r["frozen_v80_requirement"]["historical_pass_rows_claimed"], 291)
        self.assertFalse(r["frozen_terminal"]["post_terminal_may_select_reject_or_qualify"])
        law = r["proposed_prospective_rule_NOT_IN_FORCE"]
        self.assertEqual(law["preserve_preterminal_hard_gate_passes"], 204)
        self.assertTrue(law["terminal_hard_failure_must_be_repaired"])
        self.assertTrue(law["requires_independently_frozen_authorized_successor_law"])

    def test_03_wrong_or_mutated_v79_source_rejected(self):
        modified = bytearray(self.raw[0])
        modified[0] ^= 1
        for raw in (b"{}", bytes(modified), b""):
            with self.subTest(raw_len=len(raw)), self.assertRaises(A.TerminalSelectionPreflightError):
                self._run([raw, self.raw[1], self.raw[2]])

    def test_04_reissued_v80_binding_cannot_silently_override_frozen_291(self):
        binding = json.loads(self.raw[1])
        binding["v79"]["passed_gates"] = 207
        modified = json.dumps(binding).encode()
        with self.assertRaisesRegex(A.TerminalSelectionPreflightError, "identity mismatch"):
            self._run([self.raw[0], modified, self.raw[2]])

    def test_05_modified_or_truncated_receipt_rejected(self):
        for raw in (b"{}", self.raw[2][:-1]):
            with self.subTest(raw_len=len(raw)), self.assertRaises(A.TerminalSelectionPreflightError):
                self._run([self.raw[0], self.raw[1], raw])

    def test_06_v79_reordered_gate_names_cannot_change_terminal_scope(self):
        contract = json.loads(self.raw[0])
        contract["gates"]["list"][205], contract["gates"]["list"][206] = (
            contract["gates"]["list"][206], contract["gates"]["list"][205]
        )
        modified = json.dumps(contract).encode()
        with self.assertRaises(A.TerminalSelectionPreflightError):
            self._run([modified, self.raw[1], self.raw[2]])

    def test_07_exact_nonhard_limit_class_is_not_silently_promoted_to_hard(self):
        r = self._run()
        self.assertEqual(r["frozen_terminal"]["before_terminal"]["nonhard_limit_class"], 2)
        self.assertEqual(r["frozen_terminal"]["post_terminal_forensic_only"]["nonhard_limit_class"], 2)
        self.assertTrue(r["proposed_prospective_rule_NOT_IN_FORCE"]["honor_original_two_nonhard_LIMIT_classes"])


if __name__ == "__main__":
    unittest.main()
