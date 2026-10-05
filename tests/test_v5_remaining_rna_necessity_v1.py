from __future__ import annotations

import dataclasses
import hashlib
import inspect
import math

import pytest

from sea_ad_jepa.v5.remaining_rna_necessity_v1 import (
    RemainingRnaNecessityAuthorityV1,
    evaluate_remaining_rna_necessity_v1,
)
from sea_ad_jepa.v5.teacher_target_semantics_authority_v2 import (
    TeacherTargetSemanticsAuthorityV2,
)


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def necessity_authority(**updates: object) -> RemainingRnaNecessityAuthorityV1:
    values: dict[str, object] = {
        "authority_id": "V5_REMAINING_RNA_NECESSITY_AUTHORITY_V1",
        "representation_authority_sha256": h("representation"),
        "support_estimability_authority_sha256": h("support"),
        "target_address_provider_authority_sha256": h("address-provider"),
        "masking_authority_sha256": h("masking"),
        "precision_authority_sha256": h("precision"),
        "protocol_id": "KEEP_QUERY_IDENTITY_AND_LAWFUL_GLOBAL_CONTEXT_FIXED__ABLATE_REMAINING_RNA_V1",
        "metric_id": "QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1",
        "min_median_advantage_numerator": 1,
        "min_median_advantage_denominator": 10,
        "min_win_fraction_numerator": 2,
        "min_win_fraction_denominator": 3,
        "identity_only_comparator_id": "QUERY_IDENTITY_ONLY_V1",
        "global_context_no_rna_comparator_id": "QUERY_IDENTITY_PLUS_LAWFUL_GLOBAL_CONTEXT_NO_REMAINING_RNA_V1",
        "failure_semantics_id": "FAIL_CLOSED_IF_REMAINING_RNA_NOT_NECESSARY_V1",
    }
    values.update(updates)
    return RemainingRnaNecessityAuthorityV1(**values)


def teacher_v2(**updates: object) -> TeacherTargetSemanticsAuthorityV2:
    values: dict[str, object] = {
        "authority_id": "V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V2",
        "representation_authority_sha256": h("representation"),
        "support_estimability_authority_sha256": h("support"),
        "teacher_input_support_authority_sha256": h("teacher-input-support"),
        "target_address_query_authority_sha256": h("address-provider"),
        "student_visible_support_authority_sha256": h("student-visible-support"),
        "scientific_weight_authority_sha256": h("scientific-weight"),
        "masking_authority_sha256": h("masking"),
        "ema_boundary_authority_sha256": h("ema"),
        "target_construction_authority_sha256": h("target-construction"),
        "gradient_boundary_authority_sha256": h("gradient-boundary"),
        "remaining_rna_necessity_authority_sha256": necessity_authority().canonical_digest(),
        "state_semantics_id": "BIOLOGICAL_CELLULAR_LATENT_STATE_V1",
        "query_local_semantics_id": "QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1",
        "scalar_expression_objective_policy_id": "HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1",
        "route_sufficiency_policy_id": "REMAINING_RNA_REQUIRED__IDENTITY_ONLY_AND_GLOBAL_ONLY_INSUFFICIENT_V1",
    }
    values.update(updates)
    return TeacherTargetSemanticsAuthorityV2(**values)


def test_necessity_authority_has_no_scientific_threshold_defaults() -> None:
    sig = inspect.signature(RemainingRnaNecessityAuthorityV1)
    for name in (
        "min_median_advantage_numerator",
        "min_median_advantage_denominator",
        "min_win_fraction_numerator",
        "min_win_fraction_denominator",
    ):
        assert sig.parameters[name].default is inspect._empty


def test_remaining_rna_passes_only_when_it_beats_identity_and_global_context_controls() -> None:
    out = evaluate_remaining_rna_necessity_v1(
        necessity_authority(),
        full_remaining_rna_scores=[0.80, 0.70, 0.90],
        identity_only_scores=[0.50, 0.40, 0.60],
        global_context_no_rna_scores=[0.60, 0.50, 0.70],
    )
    assert out["passed"] is True
    assert out["n_units"] == 3
    assert out["identity_only_median_advantage"] == pytest.approx(0.30)
    assert out["global_context_no_rna_median_advantage"] == pytest.approx(0.20)
    assert out["identity_only_win_fraction"] == pytest.approx(1.0)
    assert out["global_context_no_rna_win_fraction"] == pytest.approx(1.0)


def test_global_context_plus_query_identity_cannot_suffice_without_remaining_rna() -> None:
    out = evaluate_remaining_rna_necessity_v1(
        necessity_authority(),
        full_remaining_rna_scores=[0.80, 0.70, 0.90],
        identity_only_scores=[0.50, 0.40, 0.60],
        global_context_no_rna_scores=[0.80, 0.70, 0.90],
    )
    assert out["passed"] is False
    assert out["global_context_no_rna_median_advantage"] == pytest.approx(0.0)


def test_error_metric_orients_advantage_so_positive_still_means_remaining_rna_helps() -> None:
    out = evaluate_remaining_rna_necessity_v1(
        necessity_authority(metric_id="QUERY_LOCAL_LATENT_STATE_COSINE_ERROR_V1"),
        full_remaining_rna_scores=[0.20, 0.30, 0.10],
        identity_only_scores=[0.50, 0.60, 0.40],
        global_context_no_rna_scores=[0.40, 0.50, 0.30],
    )
    assert out["passed"] is True
    assert out["identity_only_median_advantage"] > 0
    assert out["global_context_no_rna_median_advantage"] > 0


def test_necessity_evaluator_fails_closed_on_nonfinite_or_misaligned_inputs() -> None:
    authority = necessity_authority()
    with pytest.raises(ValueError, match="same nonzero length"):
        evaluate_remaining_rna_necessity_v1(
            authority,
            full_remaining_rna_scores=[0.8, 0.7],
            identity_only_scores=[0.5],
            global_context_no_rna_scores=[0.6, 0.5],
        )
    with pytest.raises(ValueError, match="finite"):
        evaluate_remaining_rna_necessity_v1(
            authority,
            full_remaining_rna_scores=[0.8, math.nan],
            identity_only_scores=[0.5, 0.4],
            global_context_no_rna_scores=[0.6, 0.5],
        )


def test_necessity_authority_rejects_expression_metrics_and_arbitrary_protocols() -> None:
    with pytest.raises(ValueError, match="metric_id"):
        dataclasses.replace(
            necessity_authority(), metric_id="HIDDEN_GENE_EXPRESSION_R2"
        ).validate()
    with pytest.raises(ValueError, match="protocol_id"):
        dataclasses.replace(
            necessity_authority(), protocol_id="TRUST_ME_GLOBAL_CONTEXT"
        ).validate()


def test_teacher_target_v2_binds_state_semantics_and_remaining_rna_necessity() -> None:
    authority = teacher_v2()
    authority.validate()
    assert authority.state_semantics_id == "BIOLOGICAL_CELLULAR_LATENT_STATE_V1"
    assert authority.query_local_semantics_id == "QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1"
    assert authority.scalar_expression_objective_policy_id == "HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1"
    assert authority.route_sufficiency_policy_id == "REMAINING_RNA_REQUIRED__IDENTITY_ONLY_AND_GLOBAL_ONLY_INSUFFICIENT_V1"
    assert authority.remaining_rna_necessity_authority_sha256 == necessity_authority().canonical_digest()
    assert authority.training_authorized is False


def test_teacher_target_v2_rejects_scalar_expression_or_identity_only_semantic_drift() -> None:
    with pytest.raises(ValueError, match="state_semantics_id"):
        dataclasses.replace(teacher_v2(), state_semantics_id="HIDDEN_GENE_EXPRESSION").validate()
    with pytest.raises(ValueError, match="scalar_expression_objective_policy_id"):
        dataclasses.replace(
            teacher_v2(), scalar_expression_objective_policy_id="ALLOW_SCALAR_RECONSTRUCTION"
        ).validate()
    with pytest.raises(ValueError, match="route_sufficiency_policy_id"):
        dataclasses.replace(
            teacher_v2(), route_sufficiency_policy_id="QUERY_IDENTITY_IS_ENOUGH"
        ).validate()


def test_teacher_target_v2_digest_changes_when_necessity_binding_changes() -> None:
    good = teacher_v2().canonical_digest()
    changed = teacher_v2(remaining_rna_necessity_authority_sha256=h("other-necessity")).canonical_digest()
    assert good != changed


def test_teacher_target_v2_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        dataclasses.replace(teacher_v2(), training_authorized=True).validate()
