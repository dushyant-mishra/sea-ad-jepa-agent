from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_harness_contract_v1.py"
CSPEC = importlib.util.spec_from_file_location("jepa_post_td_harness_contract_v1", CONTRACT_PATH)
assert CSPEC and CSPEC.loader
C = importlib.util.module_from_spec(CSPEC)
sys.modules[CSPEC.name] = C
CSPEC.loader.exec_module(C)

CLI_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_rehearsal_preflight_v1.py"
RSPEC = importlib.util.spec_from_file_location("jepa_post_td_rehearsal_preflight_v1", CLI_PATH)
assert RSPEC and RSPEC.loader
R = importlib.util.module_from_spec(RSPEC)
sys.modules[RSPEC.name] = R
RSPEC.loader.exec_module(R)


class TeacherEvidencePolicyTests(unittest.TestCase):
    def test_rich_q_blind_teacher_excludes_query_value_only(self):
        visible = C.derive_teacher_evidence_set(
            policy="RICH_Q_BLIND_COMPLEMENTARY",
            measured_addresses={1, 2, 3, 4, 5},
            student_visible_addresses={1, 2},
            query_address=3,
            target_block_addresses={3},
        )
        self.assertEqual(visible, frozenset({1, 2, 4, 5}))

    def test_same_evidence_q_blind_control_gets_no_extra_teacher_evidence(self):
        visible = C.derive_teacher_evidence_set(
            policy="SAME_EVIDENCE_Q_BLIND_CONTROL",
            measured_addresses={1, 2, 3, 4, 5},
            student_visible_addresses={1, 2, 3},
            query_address=3,
            target_block_addresses={3},
        )
        self.assertEqual(visible, frozenset({1, 2}))

    def test_whole_block_blind_excludes_every_block_member(self):
        visible = C.derive_teacher_evidence_set(
            policy="WHOLE_BLOCK_BLIND_CONDITIONAL",
            measured_addresses={1, 2, 3, 4, 5},
            student_visible_addresses={1, 2},
            query_address=None,
            target_block_addresses={3, 4},
        )
        self.assertEqual(visible, frozenset({1, 2, 5}))

    def test_q_visible_reference_keeps_query(self):
        visible = C.derive_teacher_evidence_set(
            policy="RICH_Q_VISIBLE_REFERENCE",
            measured_addresses={1, 2, 3},
            student_visible_addresses={1},
            query_address=3,
            target_block_addresses={3},
        )
        self.assertIn(3, visible)


class RehearsalPreflightCLITests(unittest.TestCase):
    def make_inputs(self, root: Path):
        portfolio = C.build_target_portfolio(
            selected_candidate="C6",
            qualifications={"C1": "PASS", "C3": "PASS", "C6": "PASS"},
        )
        plan = C.build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=20_000)
        pp = root / "portfolio.json"
        ap = root / "architecture.json"
        pp.write_text(json.dumps(portfolio), encoding="utf-8")
        ap.write_text(json.dumps(plan), encoding="utf-8")
        return pp, ap

    def test_run_preflight_from_paths_writes_exactly_one_non_authorizing_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pp, ap = self.make_inputs(root)
            out = root / "receipt.json"
            receipt = R.run_preflight_from_paths(
                repo_root=ROOT,
                portfolio_path=pp,
                architecture_path=ap,
                synthetic_package_sha256="a" * 64,
                output_root=root,
                receipt_path=out,
            )
            self.assertTrue(out.is_file())
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(loaded, receipt)
            self.assertEqual(receipt["status"], "READY_FOR_SYNTHETIC_REHEARSAL_ONLY")
            self.assertFalse(receipt["authority"]["training_authorized"])
            self.assertFalse(receipt["authority"]["real_data_authorized"])

    def test_preflight_receipt_is_write_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pp, ap = self.make_inputs(root)
            out = root / "receipt.json"
            out.write_text("occupied", encoding="utf-8")
            with self.assertRaisesRegex(R.RehearsalPreflightError, "already exists"):
                R.run_preflight_from_paths(
                    repo_root=ROOT,
                    portfolio_path=pp,
                    architecture_path=ap,
                    synthetic_package_sha256="b" * 64,
                    output_root=root,
                    receipt_path=out,
                )

    def test_preflight_rejects_unbound_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pp, ap = self.make_inputs(root)
            architecture = json.loads(ap.read_text(encoding="utf-8"))
            architecture["portfolio_sha256"] = "0" * 64
            ap.write_text(json.dumps(architecture), encoding="utf-8")
            with self.assertRaisesRegex(C.PostTDContractError, "not bound"):
                R.run_preflight_from_paths(
                    repo_root=ROOT,
                    portfolio_path=pp,
                    architecture_path=ap,
                    synthetic_package_sha256="c" * 64,
                    output_root=root,
                    receipt_path=root / "receipt.json",
                )


if __name__ == "__main__":
    unittest.main()
