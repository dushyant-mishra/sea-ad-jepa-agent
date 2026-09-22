import dataclasses

import pytest

from sea_ad_jepa.v5.audit_b_execution_contract_v2 import (
    ABSOLUTE_SE_TOLERANCE,
    BURDEN_ESTIMATOR_SOURCE_SHA256,
    CANONICAL_REGISTRY_SHA256,
    EXECUTION_REQUIREMENTS,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    HEAVY_QUALIFICATION_RECEIPT_SHA256,
    MANDATORY_ROBUSTNESS_AGGREGATION_ID,
    MASK_PLAN_GENERATOR_SHA256,
    NORMALIZATION_ID,
    PARENT_PREEXECUTION_CONTRACT_SHA256,
    PHASE_IV_SAMPLE_ARTIFACT_SHA256,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
    PRECISION_ESTIMATOR_ID,
    PRECISION_RULE_AUTHORITY_SHA256,
    PRECISION_SCOPE_ID,
    PRIMARY_METRIC_ID,
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
    PRIMARY_TARGET_AGGREGATION_ID,
    RELATIVE_SE_TOLERANCE,
    REPORTING_SCOPE_ID,
    RNG_AUTHORITY_SHA256,
    SCIENTIFIC_RESOLUTION_SHA256,
    SECONDARY_METRIC_ID,
    SOURCE_STRATIFIED_REPORTING_ID,
    ZERO_MEAN_RULE_ID,
    AuditBExecutionContractV2,
)


def contract(**updates) -> AuditBExecutionContractV2:
    values = dict(
        contract_id="JEPA_V5_FULL104_AUDIT_B_EXECUTION_CONTRACT_V2",
        parent_preexecution_contract_sha256=PARENT_PREEXECUTION_CONTRACT_SHA256,
        scientific_resolution_sha256=SCIENTIFIC_RESOLUTION_SHA256,
        precision_rule_authority_sha256=PRECISION_RULE_AUTHORITY_SHA256,
        phase_iv_sample_freeze_digest=PHASE_IV_SAMPLE_FREEZE_DIGEST,
        phase_iv_sample_artifact_sha256=PHASE_IV_SAMPLE_ARTIFACT_SHA256,
        full104_manifest_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        heavy_artifact_sha256=HEAVY_ARTIFACT_SHA256,
        heavy_qualification_receipt_sha256=HEAVY_QUALIFICATION_RECEIPT_SHA256,
        rng_authority_sha256=RNG_AUTHORITY_SHA256,
        mask_plan_generator_sha256=MASK_PLAN_GENERATOR_SHA256,
        burden_estimator_source_sha256=BURDEN_ESTIMATOR_SOURCE_SHA256,
        precision_scope_id=PRECISION_SCOPE_ID,
        target_aggregation_id=PRIMARY_TARGET_AGGREGATION_ID,
        mandatory_robustness_aggregation_id=MANDATORY_ROBUSTNESS_AGGREGATION_ID,
        primary_policy_id=PRIMARY_POLICY_ID,
        primary_rung_numerator=PRIMARY_RUNG.numerator,
        primary_rung_denominator=PRIMARY_RUNG.denominator,
        precision_estimator_id=PRECISION_ESTIMATOR_ID,
        relative_se_tolerance_numerator=RELATIVE_SE_TOLERANCE.numerator,
        relative_se_tolerance_denominator=RELATIVE_SE_TOLERANCE.denominator,
        absolute_se_tolerance_numerator=ABSOLUTE_SE_TOLERANCE.numerator,
        absolute_se_tolerance_denominator=ABSOLUTE_SE_TOLERANCE.denominator,
        absolute_tolerance_origin_id="ONE_AVERAGE_MASKED_ADDRESS_SHARE_AT_PRIMARY_5_PERCENT_RUNG_V1",
        zero_mean_rule_id=ZERO_MEAN_RULE_ID,
        reporting_scope_id=REPORTING_SCOPE_ID,
        source_stratified_reporting_id=SOURCE_STRATIFIED_REPORTING_ID,
        primary_metric_id=PRIMARY_METRIC_ID,
        secondary_metric_id=SECONDARY_METRIC_ID,
        normalization_id=NORMALIZATION_ID,
        execution_requirements=EXECUTION_REQUIREMENTS,
    )
    values.update(updates)
    return AuditBExecutionContractV2(**values)


def test_b4_contract_is_executable_but_never_training_authority() -> None:
    c = contract()
    c.validate()
    assert c.execution_authorized is True
    c.require_execution_ready()
    assert c.terminal_masking_authorized is False
    assert c.training_authorized is False
    assert len(c.canonical_digest()) == 64


def test_b4_binds_v1_resolution_precision_and_rng_roots() -> None:
    c = contract()
    assert c.parent_preexecution_contract_sha256 == PARENT_PREEXECUTION_CONTRACT_SHA256
    assert c.scientific_resolution_sha256 == SCIENTIFIC_RESOLUTION_SHA256
    assert c.precision_rule_authority_sha256 == PRECISION_RULE_AUTHORITY_SHA256
    assert c.rng_authority_sha256 == RNG_AUTHORITY_SHA256

    with pytest.raises(ValueError, match="scientific_resolution_sha256 drifted"):
        dataclasses.replace(c, scientific_resolution_sha256="0" * 64).validate()
    with pytest.raises(ValueError, match="precision_rule_authority_sha256 drifted"):
        dataclasses.replace(c, precision_rule_authority_sha256="1" * 64).validate()


def test_b4_cannot_switch_weighting_primary_cell_or_near_zero_rule() -> None:
    c = contract()
    with pytest.raises(ValueError, match="target_aggregation_id drifted"):
        dataclasses.replace(
            c,
            target_aggregation_id=MANDATORY_ROBUSTNESS_AGGREGATION_ID,
        ).validate()
    with pytest.raises(ValueError, match="primary_policy_id drifted"):
        dataclasses.replace(c, primary_policy_id="TOP8_CORRELATION").validate()
    with pytest.raises(ValueError, match="primary_rung_denominator drifted"):
        dataclasses.replace(c, primary_rung_denominator=10).validate()
    with pytest.raises(ValueError, match="absolute_se_tolerance_denominator drifted"):
        dataclasses.replace(c, absolute_se_tolerance_denominator=859).validate()


def test_b4_cannot_authorize_terminal_masking_or_training() -> None:
    c = contract()
    with pytest.raises(ValueError, match="terminal_masking_authorized must remain false"):
        dataclasses.replace(c, terminal_masking_authorized=True).validate()
    with pytest.raises(ValueError, match="training_authorized must remain false"):
        dataclasses.replace(c, training_authorized=True).validate()
    with pytest.raises(ValueError, match="audit_b_burden_outcomes_inspected_before_freeze"):
        dataclasses.replace(c, audit_b_burden_outcomes_inspected_before_freeze=True).validate()


def test_b4_execution_requirements_are_not_mutable_free_text() -> None:
    c = contract()
    modified = list(c.execution_requirements)
    modified.remove("all policy adaptation from observed burden" if False else modified[0])
    with pytest.raises(ValueError, match="execution_requirements drifted"):
        dataclasses.replace(c, execution_requirements=tuple(modified)).validate()
