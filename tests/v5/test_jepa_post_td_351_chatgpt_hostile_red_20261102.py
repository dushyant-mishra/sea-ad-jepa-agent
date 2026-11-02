"""Non-author post-TD #351 hostile characterization; implementation UNCHANGED.

Exact base: PR #351 at 2abcb9fe156eac340ff12adff9426ed38d929e3e.
These are five intentionally expected RED cases. A green runner means all five
known gaps were reproduced, NOT that the implementation is accepted or safe.
The fixture remains non-authorizing. No Task4, issuer, human or training claim.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/v5/jepa_post_td_harness_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("jepa_post_td_351_hostile_source", SOURCE)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def _compute(**overrides):
    values = dict(
        trainable_parameters=1000, teacher_flops=100.0, student_flops=100.0,
        cell_presentations=100, optimizer_updates=10, evaluation_exposures=4,
        evidence_budget=0.6, mask_budget=0.4, hardware_class="fixture",
    )
    values.update(overrides)
    return M.MatchedComputeContract(**values)


def _preflight(portfolio, plan):
    with tempfile.TemporaryDirectory() as output:
        return M.build_synthetic_rehearsal_preflight(
            repo_root=ROOT, portfolio=portfolio, architecture_plan=plan,
            synthetic_package_sha256="1" * 64, output_root=output,
        )


def _portfolio_and_plan():
    portfolio = M.build_target_portfolio(
        selected_candidate="C1", qualifications={"C1": "PASS"},
    )
    plan = M.build_architecture_plan(
        portfolio=portfolio, ema_half_life_presentations=1000,
    )
    return portfolio, plan


class GPTPostTD351HostileTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_red_nan_trainable_parameter_count_must_be_refused(self):
        # NaN comparison: relative_difference() becomes NaN, and NaN > tolerance is False.
        with self.assertRaises(M.PostTDContractError):
            M.validate_matched_compute(_compute(), _compute(trainable_parameters=float("nan")))

    @unittest.expectedFailure
    def test_red_nan_teacher_flops_must_be_refused(self):
        # A scientific matched-compute claim cannot accept an incomparable FLOP count.
        with self.assertRaises(M.PostTDContractError):
            M.validate_matched_compute(_compute(), _compute(teacher_flops=float("nan")))

    @unittest.expectedFailure
    def test_red_portfolio_payload_tamper_must_be_refused_by_preflight(self):
        # The saved digest does not describe this mutated portfolio anymore.
        portfolio, plan = _portfolio_and_plan()
        portfolio["blocks"][0]["candidate"] = "C5"
        with self.assertRaises(M.PostTDContractError):
            _preflight(portfolio, plan)

    @unittest.expectedFailure
    def test_red_architecture_authority_tamper_must_be_refused_by_preflight(self):
        # Preflight compares caller-provided digests but does not recompute or check plan flags.
        portfolio, plan = _portfolio_and_plan()
        plan["authority"]["training_authorized"] = True
        with self.assertRaises(M.PostTDContractError):
            _preflight(portfolio, plan)

    @unittest.expectedFailure
    def test_red_gene_query_boolean_alias_must_be_refused(self):
        # bool is an int subclass; int(True) aliases address 1 inside the evidence constructor.
        with self.assertRaises(M.PostTDContractError):
            M.derive_teacher_evidence_set(
                policy="RICH_Q_BLIND_COMPLEMENTARY",
                measured_addresses=[1, 2],
                student_visible_addresses=[2],
                query_address=True,
                target_block_addresses=[],
            )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GPTPostTD351HostileTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # Reviewer GREEN means exactly five known RED behaviors still reproduce.
    # Any repaired behavior yields an unexpected success and fails this frozen review.
    if not result.wasSuccessful() or len(result.expectedFailures) != 5:
        raise SystemExit("expected five distinct, deliberately unfixed RED cases")
