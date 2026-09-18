import hashlib
import pytest
from sea_ad_jepa.v5.masking_qualification_run_contract_v4 import (
    MaskingQualificationRunContractV4, DECISION_RULE_ID, EXECUTION_SOURCE_ROLE_ID,
    FREEZE_POLICY_ID, STRICT_SUPPORT_POLICY_ID, TERMINAL_UNIVERSE_ID
)

def h(x): return hashlib.sha256(x.encode()).hexdigest()

def contract(**updates):
    names=[
        "design","params","manifest","obs","support","census","budget","burden","split",
        "panel-plan","calibration-precision","panel-receipt","panel","precision","nl-plan","nl-receipt","nonlinear","rng",
        "checkpoint","reference","streaming","panel-source","calibration-precision-source","capacity-source","panel-authority-source","precision-source",
        "donor-source","control-source","nlcal-source","nlauth-source","nlexec-source","decision-source",
        "execution-source","spillover-source"
    ]
    r={n:h(n) for n in names}
    values=dict(
        authority_id="TEST",
        qualification_design_authority_sha256=r["design"],
        qualification_parameters_authority_sha256=r["params"],
        full104_block_manifest_sha256=r["manifest"],
        observation_state_sha256=r["obs"],
        support_estimability_authority_sha256=r["support"],
        census_authority_sha256=r["census"],
        target_evidence_budget_template_sha256=r["budget"],
        burden_ladder_authority_sha256=r["burden"],
        outer_split_authority_sha256=r["split"],
        target_panel_sizing_plan_sha256=r["panel-plan"],
        control_calibration_precision_plan_sha256=r["calibration-precision"],
        target_panel_sizing_receipt_sha256=r["panel-receipt"],
        target_panel_authority_sha256=r["panel"],
        precision_authority_sha256=r["precision"],
        nonlinear_sampling_calibration_plan_sha256=r["nl-plan"],
        nonlinear_sampling_calibration_receipt_sha256=r["nl-receipt"],
        nonlinear_challenge_authority_sha256=r["nonlinear"],
        rng_replay_authority_sha256=r["rng"],
        machine_worktree_checkpoint_sha256=r["checkpoint"],
        canonical_reference_source_sha256=r["reference"],
        full104_streaming_execution_source_sha256=r["streaming"],
        target_panel_sizing_source_sha256=r["panel-source"],
        control_calibration_precision_source_sha256=r["calibration-precision-source"],
        control_capacity_calibration_source_sha256=r["capacity-source"],
        target_panel_authority_source_sha256=r["panel-authority-source"],
        precision_evaluator_source_sha256=r["precision-source"],
        donor_evidence_source_sha256=r["donor-source"],
        control_executor_source_sha256=r["control-source"],
        nonlinear_sampling_calibration_source_sha256=r["nlcal-source"],
        nonlinear_authority_source_sha256=r["nlauth-source"],
        nonlinear_executor_source_sha256=r["nlexec-source"],
        decision_evaluator_source_sha256=r["decision-source"],
        execution_authority_source_sha256=r["execution-source"],
        anti_spillover_test_source_sha256=r["spillover-source"],
        execution_source_role_id=EXECUTION_SOURCE_ROLE_ID,
        decision_rule_id=DECISION_RULE_ID,
        freeze_policy_id=FREEZE_POLICY_ID,
        support_state_policy_id=STRICT_SUPPORT_POLICY_ID,
        terminal_universe_id=TERMINAL_UNIVERSE_ID,
    )
    values.update(updates)
    return MaskingQualificationRunContractV4(**values)

def test_v4_requires_all_current_roles_and_is_deterministic():
    c=contract(); c.validate()
    assert c.canonical_digest()==contract().canonical_digest()

def test_placeholder_fails_closed():
    with pytest.raises(ValueError,match="SHA-256"):
        contract(target_panel_sizing_receipt_sha256="PLACEHOLDER").validate()

def test_role_splicing_fails_closed():
    same=h("same")
    with pytest.raises(ValueError,match="role-distinct"):
        contract(target_panel_sizing_plan_sha256=same,target_panel_sizing_receipt_sha256=same).validate()

def test_terminal_outcome_access_before_freeze_fails():
    with pytest.raises(ValueError,match="before terminal outcomes"):
        contract(terminal_outcomes_inspected_before_freeze=True).validate()
