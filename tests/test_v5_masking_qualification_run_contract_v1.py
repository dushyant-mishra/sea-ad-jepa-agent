from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import MaskingQualificationParametersAuthorityV1
from sea_ad_jepa.v5.masking_qualification_run_contract_v1 import MaskingQualificationRunContractV1
from sea_ad_jepa.v5.masking_qualification_execution_authority_v2 import MaskingQualificationExecutionAuthorityV2


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def params(**updates) -> MaskingQualificationParametersAuthorityV1:
    values = dict(
        authority_id="V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1",
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        targeted_partner_cap=7,
        ridge_candidate_pool_count=19,
        ridge_score_feature_count=13,
        ridge_alpha_numerator=3,
        ridge_alpha_denominator=1000,
        prefix_inner_fold_count=3,
        prefix_candidate_count=11,
        prefix_floor_numerator=1,
        prefix_floor_denominator=20,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
    )
    values.update(updates)
    return MaskingQualificationParametersAuthorityV1(**values)


def test_parameter_authority_binds_all_outcome_relevant_numeric_knobs_without_defaults() -> None:
    p = params()
    p.validate()
    assert p.ridge_alpha == pytest.approx(0.003)
    assert p.prefix_floor == pytest.approx(0.05)
    assert p.prefix_reduction == pytest.approx(0.5)
    assert len(p.canonical_digest()) == 64
    for field, bad in (
        ("targeted_partner_cap", 0),
        ("ridge_candidate_pool_count", 0),
        ("ridge_score_feature_count", 0),
        ("ridge_alpha_numerator", 0),
        ("prefix_inner_fold_count", 2),
        ("prefix_candidate_count", 0),
        ("prefix_floor_numerator", 21),
        ("prefix_reduction_numerator", 21),
    ):
        with pytest.raises(ValueError):
            replace(p, **{field: bad}).validate()


def test_run_contract_binds_design_parameters_runner_and_freeze_before_outcomes() -> None:
    p = params()
    c = MaskingQualificationRunContractV1(
        authority_id="V5_MASKING_QUALIFICATION_RUN_CONTRACT_V1",
        qualification_design_authority_sha256=h("design"),
        qualification_parameters_authority_sha256=p.canonical_digest(),
        runner_source_sha256=h("runner-source"),
        freeze_policy_id="FROZEN_BEFORE_QUALIFICATION_OUTCOMES_V1",
        support_state_policy_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
    )
    c.validate()
    c.bind_parameters(p)
    with pytest.raises(ValueError, match="parameters"):
        replace(c, qualification_parameters_authority_sha256=h("other")).bind_parameters(p)
    with pytest.raises(ValueError, match="freeze_policy_id"):
        replace(c, freeze_policy_id="CHOOSE_AFTER_RESULTS").validate()


def test_execution_v2_binds_run_contract_not_an_untracked_source_only() -> None:
    p = params()
    c = MaskingQualificationRunContractV1(
        authority_id="V5_MASKING_QUALIFICATION_RUN_CONTRACT_V1",
        qualification_design_authority_sha256=h("design"),
        qualification_parameters_authority_sha256=p.canonical_digest(),
        runner_source_sha256=h("runner-source"),
        freeze_policy_id="FROZEN_BEFORE_QUALIFICATION_OUTCOMES_V1",
        support_state_policy_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
    )
    e = MaskingQualificationExecutionAuthorityV2(
        authority_id="V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V2",
        run_contract_authority_sha256=c.canonical_digest(),
        result_artifact_sha256=h("result"),
        execution_status="EXECUTED_PASS",
        selected_policy_id="RIDGE8_CONDITIONAL",
        terminal_universe_status_id="FULL_COMMON_CORE_17186_EXECUTED_V1",
        controls_status_id="ALL_REQUIRED_CONTROLS_EXECUTED_PASS_V1",
        nonlinear_status_id="NONLINEAR_CHALLENGE_REPORTED_WITHOUT_RETUNING_V1",
        precision_status_id="BOUND_PRECISION_REQUIREMENTS_MET_V1",
    )
    e.validate()
    e.bind_run_contract(c)
    assert e.passed is True
    with pytest.raises(ValueError, match="run contract"):
        replace(e, run_contract_authority_sha256=h("wrong")).bind_run_contract(c)
