from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib

import numpy as np
import pytest

from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import (
    MaskingBurdenLadderAuthorityV2,
)
from sea_ad_jepa.v5.masking_qualification_decision_v1 import POLICIES
from sea_ad_jepa.v5.masking_qualification_decision_v2 import (
    MaskingRungDecisionReceiptV2,
    evaluate_rung_v2,
)
from sea_ad_jepa.v5.masking_qualification_execution_authority_v4 import (
    MaskingQualificationExecutionAuthorityV4,
)
from sea_ad_jepa.v5.masking_terminal_evidence_assembly_v1 import (
    TerminalPolicyRawEvidenceV1,
    assemble_policy_decision_evidence,
)
from sea_ad_jepa.v5.masking_terminal_mechanical_controls_v1 import (
    TerminalMechanicalControlReceiptV1,
    mask_grid_digest,
)
from sea_ad_jepa.v5.masking_terminal_one_rung_executor_v1 import (
    TerminalOneRungExecutionResultV1,
    TerminalOneRungRawResultArtifactV1,
    _fill_donor_values,
    _require_complete,
    _validate_requested_rung,
    _verify_prior_rung_results,
)
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class _Interval:
    mean: float
    lower_two_sided: float
    upper_two_sided: float
    lower_one_sided: float
    upper_one_sided: float


class _Precision(QualificationPrecisionAuthorityV4):
    def interval(self, matrix, donor_source_code):
        values = np.asarray(matrix, dtype=float)
        mean = float(np.mean(values))
        if np.all(values == values.flat[0]):
            span = 0.0
        else:
            span = float(np.max(np.abs(values - mean)))
        return _Interval(
            mean=mean,
            lower_two_sided=mean - span,
            upper_two_sided=mean + span,
            lower_one_sided=mean - span,
            upper_one_sided=mean + span,
        )


def precision() -> QualificationPrecisionAuthorityV4:
    return _Precision(
        authority_id="TEST_QUALIFICATION_PRECISION_AUTHORITY_V4",
        support_estimability_authority_sha256=h("support"),
        target_panel_authority_sha256=h("panel"),
        target_panel_sizing_receipt_sha256=h("sizing"),
        outer_split_authority_sha256=h("split"),
        required_target_count=128,
        null_equivalence_margin_numerator=1,
        null_equivalence_margin_denominator=100,
    )


def failed_execution_result() -> TerminalOneRungExecutionResultV1:
    run_contract_root = h("run-contract")
    terminal_manifest = h("terminal-manifest")
    target_count = 128
    shape = (target_count, 104)
    source = np.array([0] * 40 + [1] * 34 + [2] * 30, dtype=np.int64)
    folds = np.arange(104, dtype=np.int64) % 4

    mask_grids = {
        policy: tuple(
            tuple(h(f"{policy}:mask:{target}:{fold}") for fold in range(4))
            for target in range(target_count)
        )
        for policy in POLICIES
    }
    mask_roots = {
        (policy, target, fold): mask_grids[policy][target][fold]
        for policy in POLICIES
        for target in range(target_count)
        for fold in range(4)
    }
    mechanical = TerminalMechanicalControlReceiptV1(
        run_contract_sha256=run_contract_root,
        terminal_input_manifest_sha256=terminal_manifest,
        mask_grid_sha256=mask_grid_digest(mask_roots),
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
    )
    mechanical_root = mechanical.canonical_digest()

    raw_by_policy = {}
    for policy in POLICIES:
        effective = np.zeros((target_count, 4), dtype=float)
        if policy != "UNIFORM_RANDOM":
            effective.fill(7.0)
        raw_by_policy[policy] = TerminalPolicyRawEvidenceV1(
            policy_id=policy,
            burden_numerator=1,
            burden_denominator=20,
            target_ids=[f"target-{i:04d}" for i in range(target_count)],
            donor_ids=[f"donor-{i:03d}" for i in range(104)],
            donor_source_code=source,
            donor_outer_fold=folds,
            source_names={0: "HVS", 1: "NPH52", 2: "SEA_AD"},
            policy_mask_sha256_by_target_fold=mask_grids[policy],
            mechanical_control_receipt_sha256=mechanical_root,
            actual_policy_scores=np.full(shape, 0.20),
            actual_uniform_scores=np.full(shape, 0.20),
            shuffled_same_mask_scores=np.zeros(shape),
            negative_control_delta=np.zeros(shape),
            planted_detect_excess=np.full(shape, 0.40),
            planted_after_mask_excess=np.zeros(shape),
            nonlinear_actual_scores=np.full(shape, 0.05),
            nonlinear_shuffled_same_mask_scores=np.zeros(shape),
            effective_targeted_n_by_target_fold=effective,
            replay_exact=True,
            untreated_identity_exact=True,
            no_privileged_metadata=True,
        )

    artifact = TerminalOneRungRawResultArtifactV1(
        run_contract_sha256=run_contract_root,
        burden_numerator=1,
        burden_denominator=20,
        prior_rung_decision_receipt_sha256=(),
        terminal_input_manifest_sha256=terminal_manifest,
        split_receipt_sha256=h("split-receipt"),
        target_eligibility_receipt_sha256=h("eligibility"),
        target_selection_receipt_sha256=h("selection"),
        mechanical_control_receipt_sha256=mechanical_root,
        raw_policy_evidence_sha256={
            policy: raw_by_policy[policy].canonical_digest() for policy in POLICIES
        },
    )
    artifact.bind_raw_evidence(raw_by_policy, mechanical)

    p = precision()
    decision_evidence = [
        assemble_policy_decision_evidence(raw_evidence=raw_by_policy[policy], precision=p)
        for policy in POLICIES
    ]
    rung = evaluate_rung_v2(decision_evidence)
    assert rung.qualified is False
    assert rung.selected_policy_id == "NO_POLICY_QUALIFIED"

    execution = MaskingQualificationExecutionAuthorityV4(
        authority_id="TEST_FAILED_EXECUTION",
        run_contract_authority_sha256=run_contract_root,
        raw_result_artifact_sha256=artifact.canonical_digest(),
        rung_decision_receipt_sha256=rung.canonical_digest(),
        selected_policy_id=rung.selected_policy_id,
        selected_burden_numerator=1,
        selected_burden_denominator=20,
        execution_status="EXECUTED_FAIL",
    )
    execution.bind_rung_decision_receipt(rung)
    return TerminalOneRungExecutionResultV1(
        raw_evidence_by_policy=raw_by_policy,
        mechanical_control_receipt=mechanical,
        raw_result_artifact=artifact,
        rung_decision_receipt=rung,
        execution_authority=execution,
    )


def ladder() -> MaskingBurdenLadderAuthorityV2:
    return MaskingBurdenLadderAuthorityV2(
        authority_id="TEST_FULL104_BURDEN_LADDER_V2",
        census_authority_sha256=h("census"),
    )


def receipt(numerator: int, denominator: int, *, qualified: bool):
    selected = "RIDGE8_CONDITIONAL" if qualified else "NO_POLICY_QUALIFIED"
    return MaskingRungDecisionReceiptV2(
        burden_numerator=numerator,
        burden_denominator=denominator,
        qualified=qualified,
        selected_policy_id=selected,
        policy_receipt_sha256={
            policy: h(f"{numerator}/{denominator}:{policy}") for policy in POLICIES
        },
    )


def test_first_invocation_can_open_only_first_frozen_rung():
    requested, prior = _validate_requested_rung(
        burden_ladder=ladder(),
        numerator=1,
        denominator=20,
        prior_rung_receipts=(),
    )
    assert requested == Fraction(1, 20)
    assert prior == ()

    with pytest.raises(ValueError, match="only lawful next rung"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(),
        )


def test_ladder_helper_accepts_already_verified_failed_first_rung_receipt():
    first = receipt(1, 20, qualified=False)
    requested, prior = _validate_requested_rung(
        burden_ladder=ladder(),
        numerator=1,
        denominator=10,
        prior_rung_receipts=(first,),
    )
    assert requested == Fraction(1, 10)
    assert prior == (first.canonical_digest(),)


def test_higher_rung_cannot_open_after_lower_rung_qualified():
    first = receipt(1, 20, qualified=True)
    with pytest.raises(ValueError, match="higher burden cannot open"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
        )


def test_prior_receipts_must_be_exact_contiguous_prefix():
    wrong_first = receipt(1, 10, qualified=False)
    with pytest.raises(ValueError, match="exact ascending ladder prefix"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=3,
            denominator=20,
            prior_rung_receipts=(wrong_first,),
        )


def test_fill_donor_values_rejects_duplicate_target_donor_evidence():
    matrix = np.full((2, 3), np.nan)
    seen = np.zeros((2, 3), dtype=bool)
    _fill_donor_values(
        matrix,
        seen,
        target_index=0,
        donor_pairs=((1, 0.25),),
        label="primary",
    )
    with pytest.raises(ValueError, match="duplicate primary evidence"):
        _fill_donor_values(
            matrix,
            seen,
            target_index=0,
            donor_pairs=((1, 0.30),),
            label="primary",
        )


def test_require_complete_rejects_missing_donor_cell():
    matrix = np.zeros((2, 3), dtype=float)
    seen = np.ones((2, 3), dtype=bool)
    seen[1, 2] = False
    with pytest.raises(ValueError, match="missing=1"):
        _require_complete(matrix, seen, "primary")


def test_raw_result_artifact_binds_exactly_all_policy_arms():
    common = dict(
        run_contract_sha256=h("run-contract"),
        burden_numerator=1,
        burden_denominator=20,
        prior_rung_decision_receipt_sha256=(),
        terminal_input_manifest_sha256=h("manifest"),
        split_receipt_sha256=h("split"),
        target_eligibility_receipt_sha256=h("eligibility"),
        target_selection_receipt_sha256=h("selection"),
        mechanical_control_receipt_sha256=h("mechanical"),
    )
    artifact = TerminalOneRungRawResultArtifactV1(
        **common,
        raw_policy_evidence_sha256={
            policy: h(f"raw:{policy}") for policy in POLICIES
        },
    )
    artifact.validate()
    assert len(artifact.canonical_digest()) == 64
    assert artifact.training_authorized is False
    assert artifact.protected_outcomes_authorized is False

    with pytest.raises(ValueError, match="every policy arm exactly once"):
        TerminalOneRungRawResultArtifactV1(
            **common,
            raw_policy_evidence_sha256={
                policy: h(f"raw:{policy}") for policy in POLICIES[:-1]
            },
        ).validate()


def test_bare_failed_rung_receipt_cannot_authorize_escalation():
    fake = receipt(1, 20, qualified=False)
    with pytest.raises(ValueError, match="bare rung receipt is insufficient"):
        _verify_prior_rung_results(
            prior_rung_results=(fake,),
            run_contract_sha256=h("run-contract"),
            precision=precision(),
        )


def test_prior_failed_result_is_mechanically_recomputed_before_escalation():
    result = failed_execution_result()
    verified = _verify_prior_rung_results(
        prior_rung_results=(result,),
        run_contract_sha256=h("run-contract"),
        precision=precision(),
    )
    requested, roots = _validate_requested_rung(
        burden_ladder=ladder(),
        numerator=1,
        denominator=10,
        prior_rung_receipts=verified,
    )
    assert requested == Fraction(1, 10)
    assert roots == (result.rung_decision_receipt.canonical_digest(),)


def test_tampered_prior_rung_decision_cannot_authorize_escalation():
    result = failed_execution_result()
    fake_rung = MaskingRungDecisionReceiptV2(
        burden_numerator=1,
        burden_denominator=20,
        qualified=False,
        selected_policy_id="NO_POLICY_QUALIFIED",
        policy_receipt_sha256={
            policy: h(f"fake-policy-receipt:{policy}") for policy in POLICIES
        },
    )
    tampered = TerminalOneRungExecutionResultV1(
        raw_evidence_by_policy=result.raw_evidence_by_policy,
        mechanical_control_receipt=result.mechanical_control_receipt,
        raw_result_artifact=result.raw_result_artifact,
        rung_decision_receipt=fake_rung,
        execution_authority=result.execution_authority,
    )
    with pytest.raises(ValueError, match="not the mechanical result"):
        _verify_prior_rung_results(
            prior_rung_results=(tampered,),
            run_contract_sha256=h("run-contract"),
            precision=precision(),
        )
