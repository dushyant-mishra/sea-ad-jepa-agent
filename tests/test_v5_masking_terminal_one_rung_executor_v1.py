from __future__ import annotations

from fractions import Fraction
import hashlib

import numpy as np
import pytest

from sea_ad_jepa.v5 import masking_terminal_one_rung_executor_v1 as executor_module
from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import (
    MaskingBurdenLadderAuthorityV2,
)
from sea_ad_jepa.v5.masking_qualification_decision_v1 import POLICIES
from sea_ad_jepa.v5.masking_qualification_decision_v2 import (
    MaskingRungDecisionReceiptV2,
)
from sea_ad_jepa.v5.masking_qualification_execution_authority_v4 import (
    MaskingQualificationExecutionAuthorityV4,
)
from sea_ad_jepa.v5.masking_terminal_evidence_assembly_v1 import (
    TerminalPolicyRawEvidenceV1,
)
from sea_ad_jepa.v5.masking_terminal_mechanical_controls_v1 import (
    TerminalMechanicalControlReceiptV1,
)
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4
from sea_ad_jepa.v5.masking_terminal_one_rung_executor_v1 import (
    TerminalOneRungRawResultArtifactV1,
    _fill_donor_values,
    _require_complete,
    _validate_requested_rung,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def ladder() -> MaskingBurdenLadderAuthorityV2:
    return MaskingBurdenLadderAuthorityV2(
        authority_id="TEST_FULL104_BURDEN_LADDER_V2",
        census_authority_sha256=h("census"),
    )


def precision() -> QualificationPrecisionAuthorityV4:
    return QualificationPrecisionAuthorityV4(
        authority_id="TEST_PRECISION_V4",
        support_estimability_authority_sha256=h("support"),
        target_panel_authority_sha256=h("panel"),
        target_panel_sizing_receipt_sha256=h("sizing"),
        outer_split_authority_sha256=h("outer-split"),
        required_target_count=128,
        null_equivalence_margin_numerator=1,
        null_equivalence_margin_denominator=1000,
    )


def raw_evidence_bundle(
    rung_receipt: MaskingRungDecisionReceiptV2,
    *,
    run_contract_sha256: str = h("run-contract"),
    terminal_input_manifest_sha256: str = h("manifest"),
):
    controls = TerminalMechanicalControlReceiptV1(
        run_contract_sha256=run_contract_sha256,
        terminal_input_manifest_sha256=terminal_input_manifest_sha256,
        mask_grid_sha256=h(
            f"mask-grid:{rung_receipt.burden_numerator}/{rung_receipt.burden_denominator}"
        ),
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
    )
    mechanical_root = controls.canonical_digest()
    donor_ids = tuple(f"D{i:03d}" for i in range(104))
    donor_source = np.zeros(104, dtype=np.int64)
    donor_fold = np.tile(np.arange(4, dtype=np.int64), 26)
    zeros = np.zeros((1, 104), dtype=np.float64)
    effective = np.zeros((1, 4), dtype=np.float64)
    raw = {}
    for policy in POLICIES:
        raw[policy] = TerminalPolicyRawEvidenceV1(
            policy_id=policy,
            burden_numerator=rung_receipt.burden_numerator,
            burden_denominator=rung_receipt.burden_denominator,
            target_ids=("T0",),
            donor_ids=donor_ids,
            donor_source_code=donor_source,
            donor_outer_fold=donor_fold,
            source_names={0: "SRC"},
            policy_mask_sha256_by_target_fold=(
                tuple(
                    h(
                        f"mask:{policy}:{rung_receipt.burden_numerator}/"
                        f"{rung_receipt.burden_denominator}:{fold}"
                    )
                    for fold in range(4)
                ),
            ),
            mechanical_control_receipt_sha256=mechanical_root,
            actual_policy_scores=zeros,
            actual_uniform_scores=zeros,
            shuffled_same_mask_scores=zeros,
            negative_control_delta=zeros,
            planted_detect_excess=zeros,
            planted_after_mask_excess=zeros,
            nonlinear_actual_scores=zeros,
            nonlinear_shuffled_same_mask_scores=zeros,
            effective_targeted_n_by_target_fold=effective,
            replay_exact=True,
            untreated_identity_exact=True,
            no_privileged_metadata=True,
        )
    return raw, controls


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


def raw_artifact(
    rung_receipt: MaskingRungDecisionReceiptV2,
    *,
    run_contract_sha256: str = h("run-contract"),
    terminal_input_manifest_sha256: str = h("manifest"),
    prior_receipt_roots: tuple[str, ...] = (),
    prior_execution_roots: tuple[str, ...] = (),
    raw_evidence_by_policy=None,
    mechanical_control_receipt=None,
) -> TerminalOneRungRawResultArtifactV1:
    mechanical_root = (
        mechanical_control_receipt.canonical_digest()
        if mechanical_control_receipt is not None
        else h("mechanical")
    )
    raw_roots = (
        {
            policy: raw_evidence_by_policy[policy].canonical_digest()
            for policy in POLICIES
        }
        if raw_evidence_by_policy is not None
        else {
            policy: h(
                f"raw:{rung_receipt.burden_numerator}/{rung_receipt.burden_denominator}:{policy}"
            )
            for policy in POLICIES
        }
    )
    return TerminalOneRungRawResultArtifactV1(
        run_contract_sha256=run_contract_sha256,
        burden_numerator=rung_receipt.burden_numerator,
        burden_denominator=rung_receipt.burden_denominator,
        prior_rung_decision_receipt_sha256=prior_receipt_roots,
        prior_rung_execution_authority_sha256=prior_execution_roots,
        terminal_input_manifest_sha256=terminal_input_manifest_sha256,
        split_receipt_sha256=h("split"),
        target_eligibility_receipt_sha256=h("eligibility"),
        target_selection_receipt_sha256=h("selection"),
        mechanical_control_receipt_sha256=mechanical_root,
        raw_policy_evidence_sha256=raw_roots,
    )


def execution_authority(
    rung_receipt: MaskingRungDecisionReceiptV2,
    *,
    run_contract_sha256: str = h("run-contract"),
    artifact: TerminalOneRungRawResultArtifactV1 | None = None,
) -> MaskingQualificationExecutionAuthorityV4:
    status = "EXECUTED_PASS" if rung_receipt.qualified else "EXECUTED_FAIL"
    if artifact is None:
        artifact = raw_artifact(
            rung_receipt,
            run_contract_sha256=run_contract_sha256,
        )
    return MaskingQualificationExecutionAuthorityV4(
        authority_id="TEST_EXECUTION",
        run_contract_authority_sha256=run_contract_sha256,
        raw_result_artifact_sha256=artifact.canonical_digest(),
        rung_decision_receipt_sha256=rung_receipt.canonical_digest(),
        selected_policy_id=rung_receipt.selected_policy_id,
        selected_burden_numerator=rung_receipt.burden_numerator,
        selected_burden_denominator=rung_receipt.burden_denominator,
        execution_status=status,
    )


def test_first_invocation_can_open_only_first_frozen_rung():
    requested, prior, prior_execution = _validate_requested_rung(
        burden_ladder=ladder(),
        numerator=1,
        denominator=20,
        prior_rung_receipts=(),
        prior_rung_execution_authorities=(),
        prior_rung_raw_result_artifacts=(),
        expected_run_contract_sha256=h("run-contract"),
        expected_terminal_input_manifest_sha256=h("manifest"),
    )
    assert requested == Fraction(1, 20)
    assert prior == ()
    assert prior_execution == ()

    with pytest.raises(ValueError, match="only lawful next rung"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(),
            prior_rung_execution_authorities=(),
            prior_rung_raw_result_artifacts=(),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
        )


def test_second_rung_requires_exact_failed_first_rung_receipt(monkeypatch):
    first = receipt(1, 20, qualified=False)
    raw_by_policy, controls = raw_evidence_bundle(first)
    first_artifact = raw_artifact(
        first,
        raw_evidence_by_policy=raw_by_policy,
        mechanical_control_receipt=controls,
    )
    first_execution = execution_authority(first, artifact=first_artifact)
    monkeypatch.setattr(
        executor_module,
        "assemble_policy_decision_evidence",
        lambda *, raw_evidence, precision: raw_evidence.policy_id,
    )
    monkeypatch.setattr(
        executor_module,
        "evaluate_rung_v2",
        lambda evidence, *, precision: first,
    )
    requested, prior, prior_execution = _validate_requested_rung(
        burden_ladder=ladder(),
        numerator=1,
        denominator=10,
        prior_rung_receipts=(first,),
        prior_rung_execution_authorities=(first_execution,),
        prior_rung_raw_result_artifacts=(first_artifact,),
        expected_run_contract_sha256=h("run-contract"),
        expected_terminal_input_manifest_sha256=h("manifest"),
        prior_rung_raw_evidence_by_policy=(raw_by_policy,),
        prior_rung_mechanical_control_receipts=(controls,),
        precision=precision(),
    )
    assert requested == Fraction(1, 10)
    assert prior == (first.canonical_digest(),)
    assert prior_execution == (first_execution.canonical_digest(),)


def test_h1_self_consistent_hash_triple_without_raw_evidence_cannot_open_next_rung():
    first = receipt(1, 20, qualified=False)
    first_artifact = raw_artifact(first)
    first_execution = execution_authority(first, artifact=first_artifact)
    with pytest.raises(ValueError, match="actual prior raw-policy evidence"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
            prior_rung_execution_authorities=(first_execution,),
            prior_rung_raw_result_artifacts=(first_artifact,),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
        )


def test_h1_prior_decision_must_rederive_from_bound_raw_evidence(monkeypatch):
    first = receipt(1, 20, qualified=False)
    raw_by_policy, controls = raw_evidence_bundle(first)
    first_artifact = raw_artifact(
        first,
        raw_evidence_by_policy=raw_by_policy,
        mechanical_control_receipt=controls,
    )
    first_execution = execution_authority(first, artifact=first_artifact)
    rederived_other = receipt(1, 20, qualified=True)
    monkeypatch.setattr(
        executor_module,
        "assemble_policy_decision_evidence",
        lambda *, raw_evidence, precision: raw_evidence.policy_id,
    )
    monkeypatch.setattr(
        executor_module,
        "evaluate_rung_v2",
        lambda evidence, *, precision: rederived_other,
    )
    with pytest.raises(ValueError, match="does not rederive from bound raw evidence"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
            prior_rung_execution_authorities=(first_execution,),
            prior_rung_raw_result_artifacts=(first_artifact,),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
            prior_rung_raw_evidence_by_policy=(raw_by_policy,),
            prior_rung_mechanical_control_receipts=(controls,),
            precision=precision(),
        )


def test_higher_rung_cannot_open_after_lower_rung_qualified():
    first = receipt(1, 20, qualified=True)
    first_artifact = raw_artifact(first)
    with pytest.raises(ValueError, match="proven failed prior execution"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
            prior_rung_execution_authorities=(execution_authority(first, artifact=first_artifact),),
            prior_rung_raw_result_artifacts=(first_artifact,),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
        )


def test_prior_receipts_must_be_exact_contiguous_prefix():
    wrong_first = receipt(1, 10, qualified=False)
    wrong_artifact = raw_artifact(wrong_first)
    with pytest.raises(ValueError, match="exact ascending ladder prefix"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=3,
            denominator=20,
            prior_rung_receipts=(wrong_first,),
            prior_rung_execution_authorities=(execution_authority(wrong_first, artifact=wrong_artifact),),
            prior_rung_raw_result_artifacts=(wrong_artifact,),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
        )




def test_h1_prior_receipt_without_execution_authority_cannot_open_next_rung():
    first = receipt(1, 20, qualified=False)
    with pytest.raises(ValueError, match="receipt, execution authority, and raw-result artifact"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
            prior_rung_execution_authorities=(),
            prior_rung_raw_result_artifacts=(raw_artifact(first),),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
        )


def test_h1_prior_execution_from_different_run_contract_cannot_open_next_rung():
    first = receipt(1, 20, qualified=False)
    foreign_artifact = raw_artifact(first, run_contract_sha256=h("other-contract"))
    foreign = execution_authority(
        first,
        run_contract_sha256=h("other-contract"),
        artifact=foreign_artifact,
    )
    with pytest.raises(ValueError, match="different run contract"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
            prior_rung_execution_authorities=(foreign,),
            prior_rung_raw_result_artifacts=(foreign_artifact,),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
        )

def test_h1_forged_execution_root_cannot_open_next_rung():
    first = receipt(1, 20, qualified=False)
    first_artifact = raw_artifact(first)
    valid = execution_authority(first, artifact=first_artifact)
    forged = MaskingQualificationExecutionAuthorityV4(
        **{**valid.__dict__, "raw_result_artifact_sha256": h("forged-raw-result")}
    )
    with pytest.raises(ValueError, match="raw result artifact root mismatch"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
            prior_rung_execution_authorities=(forged,),
            prior_rung_raw_result_artifacts=(first_artifact,),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
        )


def test_h1_smaller_or_historical_manifest_cannot_unlock_full104_next_rung():
    first = receipt(1, 20, qualified=False)
    historical_artifact = raw_artifact(
        first,
        terminal_input_manifest_sha256=h("historical-smaller-run-manifest"),
    )
    execution = execution_authority(first, artifact=historical_artifact)
    with pytest.raises(ValueError, match="different authenticated FULL104 manifest"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
            prior_rung_execution_authorities=(execution,),
            prior_rung_raw_result_artifacts=(historical_artifact,),
            expected_run_contract_sha256=h("run-contract"),
            expected_terminal_input_manifest_sha256=h("manifest"),
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
        prior_rung_execution_authority_sha256=(),
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

def test_terminal_executor_live_checkpoint_gate_fails_closed_on_validator_error(monkeypatch):
    monkeypatch.setattr(
        executor_module,
        "_live_checkpoint_validation_errors",
        lambda payload: ["HEAD_MISMATCH"],
    )
    with pytest.raises(ValueError, match="live-valid machine/worktree checkpoint"):
        executor_module._assert_live_machine_checkpoint(
            {"git": {"worktree_path": "/tmp/x"}}
        )


def test_terminal_executor_live_checkpoint_gate_accepts_only_empty_error_set(monkeypatch):
    monkeypatch.setattr(
        executor_module,
        "_live_checkpoint_validation_errors",
        lambda payload: [],
    )
    executor_module._assert_live_machine_checkpoint(
        {"git": {"worktree_path": "/tmp/x"}}
    )


def test_terminal_executor_checkpoint_validator_rejects_missing_git_snapshot():
    assert executor_module._live_checkpoint_validation_errors({}) == [
        "CHECKPOINT_GIT_SNAPSHOT_MISSING"
    ]


def test_terminal_executor_calls_live_checkpoint_gate_before_authority_consumption():
    import inspect

    source = inspect.getsource(executor_module.execute_one_terminal_rung)
    checkpoint_bind = source.index(
        "run_contract.bind_machine_checkpoint_semantic(machine_checkpoint_payload)"
    )
    live_gate = source.index("_assert_live_machine_checkpoint(machine_checkpoint_payload)")
    parameter_bind = source.index("run_contract.bind_parameters(parameters)")
    assert checkpoint_bind < live_gate < parameter_bind

