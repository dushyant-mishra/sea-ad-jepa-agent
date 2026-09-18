import hashlib
import dataclasses
import pytest

from sea_ad_jepa.v5.masking_target_semantics_authority_v1 import (
    MaskingTargetSemanticsAuthorityV1,
    verify_target_construction_source,
)
from sea_ad_jepa.v5.masking_qualification_design_authority_v2 import (
    MaskingQualificationDesignAuthorityV2,
)
from sea_ad_jepa.v5.masking_qualification_design_authority_v1 import (
    APPROVED_POLICY_ARMS, REQUIRED_CONTROLS,
)


def h(x): return hashlib.sha256(x.encode()).hexdigest()


def semantics(**updates):
    values=dict(
        authority_id="TEST",
        representation_authority_sha256=h("representation"),
        support_estimability_authority_sha256=h("support"),
        canonical_registry_authority_sha256=h("registry"),
        target_construction_authority_source_sha256=h("target-construction-source"),
    )
    values.update(updates)
    return MaskingTargetSemanticsAuthorityV1(**values)


def design(**updates):
    roots={name:h(name) for name in (
        "substrate","representation","support","registry","semantics","budget",
        "precision","split","panel","universe","rng","runner"
    )}
    values=dict(
        authority_id="TEST",
        full104_substrate_sha256=roots["substrate"],
        representation_authority_sha256=roots["representation"],
        support_estimability_authority_sha256=roots["support"],
        canonical_registry_authority_sha256=roots["registry"],
        masking_target_semantics_authority_sha256=roots["semantics"],
        target_evidence_budget_template_sha256=roots["budget"],
        precision_authority_sha256=roots["precision"],
        outer_split_authority_sha256=roots["split"],
        target_panel_authority_sha256=roots["panel"],
        address_universe_ladder_authority_sha256=roots["universe"],
        rng_replay_authority_sha256=roots["rng"],
        qualification_runner_source_sha256=roots["runner"],
        scientific_semantics_id="BIOLOGICAL_QUERY_LOCAL_STATE_NOT_SCALAR_EXPRESSION_V1",
        expression_attacker_role_id="ANTI_SHORTCUT_DIAGNOSTIC_ONLY_NOT_JEPA_LOSS_V1",
        policy_arms=APPROVED_POLICY_ARMS,
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_attacker_application_policy_id="SAME_PRIMARY_ATTACKER_AND_SCORE_FOR_ALL_POLICY_ARMS_V1",
        secondary_attacker_id="NONLINEAR_TREE_ENSEMBLE_EXPRESSION_PROXY_CHALLENGE_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        paired_estimand_id="UNIFORM_MINUS_TARGETED_SCORE_AT_TARGET_X_OUTER_FOLD_V1",
        controls=REQUIRED_CONTROLS,
        nonlinear_retuning_policy_id="NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1",
        pooled_mean_guardrail_id="NO_HARMFUL_SIGN_REVERSAL_HIDDEN_BY_POOLED_MEAN_V1",
    )
    values.update(updates)
    return MaskingQualificationDesignAuthorityV2(**values)


def test_masking_semantics_has_no_downstream_mask_or_remaining_rna_root():
    a=semantics(); a.validate()
    fields=set(a.__dataclass_fields__)
    assert "masking_authority_sha256" not in fields
    assert "remaining_rna_necessity_authority_sha256" not in fields
    assert "query_artifact_sha256" not in fields


def test_masking_semantics_rejects_downstream_binding_flags():
    with pytest.raises(ValueError, match="remaining-RNA"):
        semantics(remaining_rna_authority_bound=True).validate()
    with pytest.raises(ValueError, match="selected masking"):
        semantics(selected_masking_policy_bound=True).validate()


def test_target_construction_semantics_are_mechanically_required():
    source=" ".join([
        "QUERY_IDENTITY_SUPPLIED_V1",
        "QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1",
        "NON_QUERY_LAWFUL_RNA_VISIBLE_V1",
        "LAWFUL_GLOBAL_BIOLOGICAL_CONTEXT_ALLOWED_V1",
        "TEACHER_STOPGRAD_V1",
        "QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1",
        "SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1",
    ])
    verify_target_construction_source(semantics(),source)
    with pytest.raises(ValueError, match="missing frozen semantics"):
        verify_target_construction_source(semantics(),source.replace("TEACHER_STOPGRAD_V1",""))


def test_design_v2_has_no_circular_teacher_target_root():
    a=design(); a.validate()
    fields=set(a.__dataclass_fields__)
    assert "teacher_target_semantics_authority_sha256" not in fields
    assert "masking_target_semantics_authority_sha256" in fields


def test_design_v2_refuses_selected_policy_or_remaining_rna():
    with pytest.raises(ValueError, match="before a masking policy"):
        design(selected_masking_policy_bound=True).validate()
    with pytest.raises(ValueError, match="downstream"):
        design(remaining_rna_authority_bound=True).validate()


def test_design_v2_requires_exact_policy_and_control_sets():
    with pytest.raises(ValueError, match="policy_arms"):
        design(policy_arms=tuple(reversed(APPROVED_POLICY_ARMS))).validate()
    with pytest.raises(ValueError, match="controls"):
        design(controls=REQUIRED_CONTROLS[:-1]).validate()
