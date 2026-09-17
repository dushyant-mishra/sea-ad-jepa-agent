from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.measurement_robustness_authority_v2 import MeasurementRobustnessAuthorityV2


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_MEASUREMENT_ROBUSTNESS_AUTHORITY_V2",
        representation_authority_sha256=h("representation"),
        teacher_target_semantics_sha256=h("teacher"),
        precision_authority_sha256=h("precision"),
        perturbation_protocol_authority_sha256=h("perturbation"),
        stratification_guardrail_authority_sha256=h("stratification"),
        execution_source_sha256=h("execution-source"),
        result_artifact_sha256=h("result"),
        primary_metric_id="QUERY_LOCAL_LATENT_STATE_COSINE_STABILITY_V1",
        perturbation_semantics_id="SAME_CELL_MEASUREMENT_DEPTH_PERTURBATION_V1",
        failure_semantics_id="FAIL_CLOSED_ON_STATE_INSTABILITY_OR_INSUFFICIENT_PRECISION_V1",
        execution_status="EXECUTED_PASS",
        training_authorized=False,
    )
    values.update(updates)
    return MeasurementRobustnessAuthorityV2(**values)


def test_valid_measurement_v2_is_deterministic() -> None:
    a = authority(); a.validate()
    assert a.canonical_digest() == authority().canonical_digest()
    assert a.passed is True


def test_measurement_roles_are_exact_sha_roots_and_distinct() -> None:
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(precision_authority_sha256=same, result_artifact_sha256=same).validate()
    with pytest.raises(ValueError, match="result_artifact_sha256"):
        authority(result_artifact_sha256="result.csv").validate()


def test_measurement_metric_perturbation_and_failure_semantics_are_enumerated() -> None:
    with pytest.raises(ValueError, match="primary_metric_id"):
        authority(primary_metric_id="HIDDEN_GENE_EXPRESSION_R2").validate()
    with pytest.raises(ValueError, match="perturbation_semantics_id"):
        authority(perturbation_semantics_id="ARBITRARY_NOISE").validate()
    with pytest.raises(ValueError, match="failure_semantics_id"):
        authority(failure_semantics_id="REPORT_MEAN_AND_CONTINUE").validate()


def test_only_explicit_executed_statuses_are_allowed() -> None:
    for bad in ("NOT_RUN", "SKIPPED", "PENDING", "PASS"):
        with pytest.raises(ValueError, match="execution_status"):
            authority(execution_status=bad).validate()
    assert authority(execution_status="EXECUTED_FAIL").passed is False


def test_measurement_v2_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
