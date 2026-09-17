from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.masking_qualification_design_authority_v1 import (
    MaskingQualificationDesignAuthorityV1,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V1",
        full104_substrate_sha256=h("full104"),
        representation_authority_sha256=h("representation"),
        support_estimability_authority_sha256=h("support"),
        canonical_registry_authority_sha256=h("registry"),
        teacher_target_semantics_authority_sha256=h("teacher"),
        target_evidence_budget_authority_sha256=h("budget"),
        precision_authority_sha256=h("precision"),
        outer_split_authority_sha256=h("split"),
        target_panel_authority_sha256=h("panel"),
        address_universe_ladder_authority_sha256=h("universe"),
        rng_replay_authority_sha256=h("rng"),
        qualification_runner_source_sha256=h("runner"),
        scientific_semantics_id="BIOLOGICAL_QUERY_LOCAL_STATE_NOT_SCALAR_EXPRESSION_V1",
        expression_attacker_role_id="ANTI_SHORTCUT_DIAGNOSTIC_ONLY_NOT_JEPA_LOSS_V1",
        policy_arms=("UNIFORM_RANDOM", "TOP8_CORRELATION", "RIDGE8_CONDITIONAL", "PREFIX3_SELECTIVE"),
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_attacker_application_policy_id="SAME_PRIMARY_ATTACKER_AND_SCORE_FOR_ALL_POLICY_ARMS_V1",
        secondary_attacker_id="NONLINEAR_TREE_ENSEMBLE_EXPRESSION_PROXY_CHALLENGE_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        paired_estimand_id="UNIFORM_MINUS_TARGETED_SCORE_AT_TARGET_X_OUTER_FOLD_V1",
        controls=(
            "PLANTED_SHORTCUT_POSITIVE_CONTROL_V1",
            "WITHIN_DONOR_SHUFFLED_NEGATIVE_CONTROL_V1",
            "UNTREATED_MASK_IDENTITY_CONTROL_V1",
            "DETERMINISTIC_REPLAY_CONTROL_V1",
            "NO_PRIVILEGED_METADATA_CONTROL_V1",
        ),
        nonlinear_retuning_policy_id="NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1",
        pooled_mean_guardrail_id="NO_HARMFUL_SIGN_REVERSAL_HIDDEN_BY_POOLED_MEAN_V1",
        protected_outcomes_authorized=False,
        training_authorized=False,
    )
    values.update(updates)
    return MaskingQualificationDesignAuthorityV1(**values)


def test_valid_design_is_deterministic() -> None:
    a = authority()
    a.validate()
    assert a.canonical_digest() == authority().canonical_digest()


def test_all_authority_roles_are_distinct_and_sha_bound() -> None:
    digest = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(precision_authority_sha256=digest, outer_split_authority_sha256=digest).validate()
    with pytest.raises(ValueError, match="qualification_runner_source_sha256"):
        authority(qualification_runner_source_sha256="runner.py").validate()


def test_policy_arms_are_exact_and_cannot_be_posthoc_combined() -> None:
    with pytest.raises(ValueError, match="policy_arms"):
        authority(policy_arms=("UNIFORM_RANDOM", "RIDGE8_CONDITIONAL")).validate()
    with pytest.raises(ValueError, match="policy_arms"):
        authority(policy_arms=("UNIFORM_RANDOM", "TOP8_CORRELATION", "RIDGE8_CONDITIONAL", "RIDGE8_TOP8_HYBRID")).validate()


def test_expression_attacker_cannot_become_foundation_objective() -> None:
    with pytest.raises(ValueError, match="scientific_semantics_id"):
        authority(scientific_semantics_id="PREDICT_HIDDEN_GENE_EXPRESSION").validate()
    with pytest.raises(ValueError, match="expression_attacker_role_id"):
        authority(expression_attacker_role_id="JEPA_TRAINING_LOSS").validate()


def test_same_primary_attacker_and_score_must_apply_to_every_policy_arm() -> None:
    with pytest.raises(ValueError, match="primary_attacker_application_policy_id"):
        authority(primary_attacker_application_policy_id="PER_ARM_ATTACKER_ALLOWED").validate()


def test_attackers_estimand_and_guardrails_are_enumerated() -> None:
    fields = {
        "primary_attacker_id": "OLS",
        "secondary_attacker_id": "RETUNE_UNTIL_GOOD",
        "primary_score_id": "UNBOUNDED_PARTIAL_R2_RELATIVE_MEAN",
        "paired_estimand_id": "POOLED_ROW_MEAN",
        "nonlinear_retuning_policy_id": "RETUNE_AFTER_RESULTS",
        "pooled_mean_guardrail_id": "MEAN_ONLY",
    }
    for field, value in fields.items():
        with pytest.raises(ValueError, match=field):
            authority(**{field: value}).validate()


def test_required_controls_are_exact() -> None:
    with pytest.raises(ValueError, match="controls"):
        authority(controls=("PLANTED_SHORTCUT_POSITIVE_CONTROL_V1",)).validate()
    with pytest.raises(ValueError, match="controls"):
        authority(controls=authority().controls + ("PATHOLOGY_CONTROL",)).validate()


def test_protected_outcomes_and_training_cannot_be_authorized() -> None:
    with pytest.raises(ValueError, match="protected outcomes"):
        authority(protected_outcomes_authorized=True).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()


def test_live_binder_rejects_wrong_role_even_if_each_object_is_self_consistent() -> None:
    a = authority()

    class Stub:
        training_authorized = False
        def __init__(self, digest: str): self._digest = digest
        def validate(self): return None
        def canonical_digest(self): return self._digest

    correct = {
        "target_evidence_budget": Stub(a.target_evidence_budget_authority_sha256),
        "precision": Stub(a.precision_authority_sha256),
        "outer_split": Stub(a.outer_split_authority_sha256),
        "target_panel": Stub(a.target_panel_authority_sha256),
        "address_universe_ladder": Stub(a.address_universe_ladder_authority_sha256),
        "rng_replay": Stub(a.rng_replay_authority_sha256),
    }
    a.bind_live_authorities(**correct)
    correct["precision"] = Stub(h("other-precision"))
    with pytest.raises(ValueError, match="precision authority root mismatch"):
        a.bind_live_authorities(**correct)
