"""Repair regression: exercises the five unchanged-source assertions from
#517 after dropping the deliberate expectedFailure decorators and runner.
Original #517 remains immutable and still reports five expected RED at #351.
Additional tests probe recomputed forged digests, numeric domains and address
aliasing. These are code/fixture checks, not issuer or biological authority.
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
    def test_red_nan_trainable_parameter_count_must_be_refused(self):
        # NaN comparison: relative_difference() becomes NaN, and NaN > tolerance is False.
        with self.assertRaises(M.PostTDContractError):
            M.validate_matched_compute(_compute(), _compute(trainable_parameters=float("nan")))

    def test_red_nan_teacher_flops_must_be_refused(self):
        # A scientific matched-compute claim cannot accept an incomparable FLOP count.
        with self.assertRaises(M.PostTDContractError):
            M.validate_matched_compute(_compute(), _compute(teacher_flops=float("nan")))

    def test_red_portfolio_payload_tamper_must_be_refused_by_preflight(self):
        # The saved digest does not describe this mutated portfolio anymore.
        portfolio, plan = _portfolio_and_plan()
        portfolio["blocks"][0]["candidate"] = "C5"
        with self.assertRaises(M.PostTDContractError):
            _preflight(portfolio, plan)

    def test_red_architecture_authority_tamper_must_be_refused_by_preflight(self):
        # Preflight compares caller-provided digests but does not recompute or check plan flags.
        portfolio, plan = _portfolio_and_plan()
        plan["authority"]["training_authorized"] = True
        with self.assertRaises(M.PostTDContractError):
            _preflight(portfolio, plan)

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



class PostTD517AdditionalHardeningTests(unittest.TestCase):
    def test_valid_matched_compute_and_rehearsal_remain_enabled_only_as_fixture(self):
        self.assertEqual(M.validate_matched_compute(_compute(), _compute())["status"], "MATCHED_COMPUTE_PASS")
        portfolio, plan = _portfolio_and_plan()
        receipt = _preflight(portfolio, plan)
        self.assertEqual(receipt["status"], "READY_FOR_SYNTHETIC_REHEARSAL_ONLY")
        self.assertIs(receipt["authority"]["training_authorized"], False)
        self.assertIs(receipt["authority"]["real_data_authorized"], False)
        self.assertIs(receipt["authority"]["stage4_authorized"], False)

    def test_other_nonfinite_and_invalid_compute_fields_refuse(self):
        for field, value in (
            ("trainable_parameters", True),
            ("trainable_parameters", -1),
            ("trainable_parameters", 2.0),
            ("cell_presentations", float("nan")),
            ("evaluation_exposures", True),
            ("optimizer_updates", -1),
            ("student_flops", float("inf")),
            ("teacher_flops", float("-inf")),
            ("evidence_budget", float("nan")),
            ("mask_budget", float("inf")),
            ("mask_budget", -0.1),
            ("hardware_class", ""),
        ):
            with self.subTest(field=field, value=repr(value)):
                with self.assertRaises(M.PostTDContractError):
                    M.validate_matched_compute(_compute(), _compute(**{field: value}))

    def test_invalid_reference_and_tolerance_also_refuse(self):
        for field in ("teacher_flops", "trainable_parameters", "mask_budget"):
            with self.subTest(field=field):
                with self.assertRaises(M.PostTDContractError):
                    M.validate_matched_compute(_compute(**{field: float("nan")}), _compute())
        for field in ("parameter_relative_tolerance", "flop_relative_tolerance"):
            for value in (float("nan"), float("inf"), True, -1):
                with self.subTest(field=field, value=repr(value)):
                    with self.assertRaises(M.PostTDContractError):
                        M.validate_matched_compute(_compute(), _compute(), **{field: value})

    def test_recomputed_mutated_authority_flag_is_still_refused(self):
        for location, key, value in (
            ("plan", "training_authorized", True),
            ("plan", "stage4_authorized", 0),
            ("portfolio", "target_selection_authorized", True),
            ("portfolio", "training_authorized", 0),
        ):
            with self.subTest(location=location, key=key, value=value):
                portfolio, plan = _portfolio_and_plan()
                target = portfolio if location == "portfolio" else plan
                target["authority"][key] = value
                digest = "portfolio_sha256" if location == "portfolio" else "architecture_sha256"
                target[digest] = M._canonical_sha256({k: v for k, v in target.items() if k != digest})
                if location == "portfolio":
                    plan["portfolio_sha256"] = portfolio["portfolio_sha256"]
                    plan["architecture_sha256"] = M._canonical_sha256({
                        k: v for k, v in plan.items() if k != "architecture_sha256"
                    })
                with self.assertRaises(M.PostTDContractError):
                    _preflight(portfolio, plan)

    def test_recomputed_rehearsal_scope_tamper_refuses(self):
        for mutation in ("status", "semantics"):
            with self.subTest(mutation=mutation):
                portfolio, plan = _portfolio_and_plan()
                if mutation == "status":
                    plan["status"] = "TRAINING_AUTHORIZED"
                else:
                    first = next(iter(plan["output_semantics"]))
                    plan["output_semantics"][first]["production_selection_authority"] = True
                plan["architecture_sha256"] = M._canonical_sha256({
                    k: v for k, v in plan.items() if k != "architecture_sha256"
                })
                with self.assertRaises(M.PostTDContractError):
                    _preflight(portfolio, plan)

    def test_exact_integer_address_domains_and_legitimate_query_exclusion(self):
        args = dict(policy="RICH_Q_BLIND_COMPLEMENTARY",
                    measured_addresses=[1, 2], student_visible_addresses=[2],
                    query_address=1, target_block_addresses=[])
        self.assertEqual(M.derive_teacher_evidence_set(**args), frozenset({2}))
        for location, bad in (
            ("query_address", True),
            ("query_address", "1"),
            ("query_address", 1.0),
            ("query_address", -1),
            ("measured_addresses", [True, 2]),
            ("student_visible_addresses", [False, 2]),
            ("target_block_addresses", [True]),
        ):
            with self.subTest(location=location, bad=repr(bad)):
                updated = dict(args)
                updated[location] = bad
                with self.assertRaises(M.PostTDContractError):
                    M.derive_teacher_evidence_set(**updated)


if __name__ == "__main__":
    unittest.main()
