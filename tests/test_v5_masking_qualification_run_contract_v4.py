import hashlib
import pytest
from sea_ad_jepa.v5.masking_qualification_run_contract_v4 import (
    MaskingQualificationRunContractV4, DECISION_RULE_ID, EXECUTION_SOURCE_ROLE_ID,
    FREEZE_POLICY_ID, STRICT_SUPPORT_POLICY_ID, TERMINAL_UNIVERSE_ID,
    EXPECTED_FULL104_BLOCK_MANIFEST_SHA256, EXPECTED_OBSERVATION_STATE_SHA256,
    TERMINAL_EXECUTION_INPUT_ROLE_ID, CALIBRATION_CACHE_ROLE_ID
)

def h(x): return hashlib.sha256(x.encode()).hexdigest()

def contract(**updates):
    names=[
        "design","params","calibration-cache","support","census","budget","burden","split",
        "panel-plan","calibration-precision","panel-receipt","panel","precision","nl-plan","nl-receipt","nonlinear","rng",
        "checkpoint","reference","streaming","panel-source","calibration-precision-source","capacity-source","cache-builder-source","cache-evaluator-source","panel-authority-source","precision-source",
        "donor-source","control-source","nlcal-source","nlauth-source","nlexec-source","decision-source",
        "execution-source","spillover-source"
    ]
    r={n:h(n) for n in names}
    values=dict(
        authority_id="TEST",
        qualification_design_authority_sha256=r["design"],
        qualification_parameters_authority_sha256=r["params"],
        full104_block_manifest_sha256=EXPECTED_FULL104_BLOCK_MANIFEST_SHA256,
        observation_state_sha256=EXPECTED_OBSERVATION_STATE_SHA256,
        support_estimability_authority_sha256=r["support"],
        census_authority_sha256=r["census"],
        control_calibration_cache_manifest_sha256=r["calibration-cache"],
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
        control_calibration_cache_builder_source_sha256=r["cache-builder-source"],
        control_calibration_cache_evaluator_source_sha256=r["cache-evaluator-source"],
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
        execution_input_role_id=TERMINAL_EXECUTION_INPUT_ROLE_ID,
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


def test_terminal_contract_refuses_calibration_cache_as_execution_input():
    c=contract(); c.validate()
    c.assert_terminal_execution_input_role(TERMINAL_EXECUTION_INPUT_ROLE_ID)
    with pytest.raises(ValueError,match="forbidden as terminal"):
        c.assert_terminal_execution_input_role(CALIBRATION_CACHE_ROLE_ID)


def test_terminal_contract_pins_actual_full104_substrate_and_observation_state():
    with pytest.raises(ValueError,match="block-manifest"):
        contract(full104_block_manifest_sha256=h("wrong-manifest")).validate()
    with pytest.raises(ValueError,match="observation-state"):
        contract(observation_state_sha256=h("wrong-observation")).validate()


class _BoundStub:
    training_authorized = False
    def __init__(self, digest, **attrs):
        self._digest = digest
        for key, value in attrs.items():
            setattr(self, key, value)
    def validate(self):
        return None
    def canonical_digest(self):
        return self._digest


def test_final_contract_rejects_design_v1_concrete_budget_binding():
    c = contract()
    old_design = _BoundStub(
        c.qualification_design_authority_sha256,
        full104_substrate_sha256=c.full104_block_manifest_sha256,
        support_estimability_authority_sha256=c.support_estimability_authority_sha256,
        target_evidence_budget_authority_sha256=h("concrete-budget"),
        precision_authority_sha256=c.precision_authority_sha256,
        outer_split_authority_sha256=c.outer_split_authority_sha256,
        target_panel_authority_sha256=c.target_panel_authority_sha256,
        rng_replay_authority_sha256=c.rng_replay_authority_sha256,
    )
    with pytest.raises(ValueError, match="DesignAuthorityV2"):
        c.bind_design(old_design)


def test_final_contract_accepts_design_v2_template_and_burden_roots():
    c = contract()
    design = _BoundStub(
        c.qualification_design_authority_sha256,
        full104_substrate_sha256=c.full104_block_manifest_sha256,
        support_estimability_authority_sha256=c.support_estimability_authority_sha256,
        target_evidence_budget_template_sha256=c.target_evidence_budget_template_sha256,
        burden_ladder_authority_sha256=c.burden_ladder_authority_sha256,
        precision_authority_sha256=c.precision_authority_sha256,
        outer_split_authority_sha256=c.outer_split_authority_sha256,
        target_panel_authority_sha256=c.target_panel_authority_sha256,
        rng_replay_authority_sha256=c.rng_replay_authority_sha256,
    )
    c.bind_design(design)


def test_final_contract_rejects_precision_plan_v1_receipt_as_authority_role():
    c = contract()
    old = _BoundStub(
        c.control_calibration_precision_plan_sha256,
        census_authority_sha256=c.census_authority_sha256,
        support_estimability_authority_sha256=c.support_estimability_authority_sha256,
        target_eligibility_receipt_sha256=h("elig"),
        outer_split_authority_sha256=h("raw-split-receipt"),
    )
    cache = _BoundStub(
        c.control_calibration_cache_manifest_sha256,
        split_receipt_sha256=h("raw-split-receipt"),
        target_eligibility_receipt_sha256=h("elig"),
    )
    with pytest.raises(ValueError, match="PlanV2"):
        c.bind_control_calibration_precision_plan(old, cache)


def test_final_contract_accepts_precision_plan_v2_with_explicit_fold_receipt_and_cache_root():
    c = contract()
    split_receipt = h("fold-receipt-current")
    eligibility = h("elig-current")
    cache = _BoundStub(
        c.control_calibration_cache_manifest_sha256,
        split_receipt_sha256=split_receipt,
        target_eligibility_receipt_sha256=eligibility,
    )
    plan = _BoundStub(
        c.control_calibration_precision_plan_sha256,
        census_authority_sha256=c.census_authority_sha256,
        support_estimability_authority_sha256=c.support_estimability_authority_sha256,
        target_eligibility_receipt_sha256=eligibility,
        fold_assignment_artifact_sha256=split_receipt,
        calibration_cache_manifest_sha256=c.control_calibration_cache_manifest_sha256,
    )
    c.bind_control_calibration_precision_plan(plan, cache)


def test_control_calibration_provenance_is_bound_but_not_promoted_to_terminal_input():
    c = contract()
    fold_receipt = h("fold-receipt")
    eligibility_receipt = h("eligibility-receipt")
    cache = _BoundStub(
        c.control_calibration_cache_manifest_sha256,
        cache_role_id=CALIBRATION_CACHE_ROLE_ID,
        terminal_masking_qualification_authorized=False,
        full104_block_manifest_sha256=c.full104_block_manifest_sha256,
        census_authority_sha256=c.census_authority_sha256,
        support_estimability_authority_sha256=c.support_estimability_authority_sha256,
        split_receipt_sha256=fold_receipt,
        target_eligibility_receipt_sha256=eligibility_receipt,
    )
    outer = _BoundStub(
        c.outer_split_authority_sha256,
        full104_substrate_sha256=c.full104_block_manifest_sha256,
        fold_assignment_artifact_sha256=fold_receipt,
    )
    sizing = _BoundStub(
        c.target_panel_sizing_plan_sha256,
        target_eligibility_receipt_sha256=eligibility_receipt,
    )
    c.bind_control_calibration_provenance(cache, outer, sizing)
    with pytest.raises(ValueError, match="forbidden as terminal"):
        c.assert_terminal_execution_input_role(cache.cache_role_id)


def test_control_calibration_provenance_fails_if_fold_receipt_is_spliced():
    c = contract()
    cache = _BoundStub(
        c.control_calibration_cache_manifest_sha256,
        cache_role_id=CALIBRATION_CACHE_ROLE_ID,
        terminal_masking_qualification_authorized=False,
        full104_block_manifest_sha256=c.full104_block_manifest_sha256,
        census_authority_sha256=c.census_authority_sha256,
        support_estimability_authority_sha256=c.support_estimability_authority_sha256,
        split_receipt_sha256=h("fold-a"),
        target_eligibility_receipt_sha256=h("elig"),
    )
    outer = _BoundStub(
        c.outer_split_authority_sha256,
        full104_substrate_sha256=c.full104_block_manifest_sha256,
        fold_assignment_artifact_sha256=h("fold-b"),
    )
    sizing = _BoundStub(
        c.target_panel_sizing_plan_sha256,
        target_eligibility_receipt_sha256=h("elig"),
    )
    with pytest.raises(ValueError, match="fold-assignment"):
        c.bind_control_calibration_provenance(cache, outer, sizing)


def test_final_contract_rejects_provisional_nonlinear_calibration_plan_without_v2_roots():
    c=contract()
    old_plan=_BoundStub(c.nonlinear_sampling_calibration_plan_sha256)
    receipt=_BoundStub(c.nonlinear_sampling_calibration_receipt_sha256)
    nonlinear=_BoundStub(
        c.nonlinear_challenge_authority_sha256,
        sampling_calibration_plan_sha256=c.nonlinear_sampling_calibration_plan_sha256,
        sampling_calibration_receipt_sha256=c.nonlinear_sampling_calibration_receipt_sha256,
        target_panel_authority_sha256=c.target_panel_authority_sha256,
        primary_parameters_authority_sha256=c.qualification_parameters_authority_sha256,
        outer_split_authority_sha256=c.outer_split_authority_sha256,
    )
    with pytest.raises(ValueError,match="plan V2"):
        c.bind_nonlinear(nonlinear,old_plan,receipt)
