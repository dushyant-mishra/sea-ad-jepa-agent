from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from sea_ad_jepa.v5.masking_qualification_design_authority_v1 import (
    APPROVED_EXPRESSION_ATTACKER_ROLE_IDS,
    APPROVED_NONLINEAR_RETUNING_POLICY_IDS,
    APPROVED_PAIRED_ESTIMAND_IDS,
    APPROVED_POLICY_ARMS,
    APPROVED_POOLED_MEAN_GUARDRAIL_IDS,
    APPROVED_PRIMARY_ATTACKER_APPLICATION_POLICY_IDS,
    APPROVED_PRIMARY_ATTACKER_IDS,
    APPROVED_PRIMARY_SCORE_IDS,
    APPROVED_SCIENTIFIC_SEMANTICS_IDS,
    APPROVED_SECONDARY_ATTACKER_IDS,
    REQUIRED_CONTROLS,
)
from sea_ad_jepa.v5.masking_qualification_design_authority_v2 import (
    MaskingQualificationDesignAuthorityV2,
)
from sea_ad_jepa.v5.target_evidence_budget_authority_v2 import (
    TargetEvidenceBudgetAuthorityV2,
)
from sea_ad_jepa.v5.target_evidence_budget_template_authority_v1 import (
    TargetEvidenceBudgetTemplateAuthorityV1,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def template(**updates):
    values = dict(
        authority_id="TEST_TEMPLATE",
        support_estimability_authority_sha256=h("support"),
        support_semantics_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        census_authority_sha256=h("census"),
        full104_block_manifest_sha256=h("full104"),
        observation_state_sha256=h("obs"),
        terminal_universe_id="FULL_COMMON_CORE_17186_V1",
        budget_semantics_id="MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
        eligibility_rule_id="VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        min_retained_non_target_address_count=0,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )
    values.update(updates)
    return TargetEvidenceBudgetTemplateAuthorityV1(**values)


def concrete_budget(num=1, den=20):
    t = template()
    return TargetEvidenceBudgetAuthorityV2(
        authority_id=t.authority_id,
        support_estimability_authority_sha256=t.support_estimability_authority_sha256,
        support_semantics_id=t.support_semantics_id,
        census_authority_sha256=t.census_authority_sha256,
        full104_block_manifest_sha256=t.full104_block_manifest_sha256,
        observation_state_sha256=t.observation_state_sha256,
        terminal_universe_id=t.terminal_universe_id,
        budget_semantics_id=t.budget_semantics_id,
        eligibility_rule_id=t.eligibility_rule_id,
        rounding_policy_id=t.rounding_policy_id,
        mask_fraction_numerator=num,
        mask_fraction_denominator=den,
        min_retained_non_target_address_count=t.min_retained_non_target_address_count,
        infeasible_policy_id=t.infeasible_policy_id,
    )


def design(**updates):
    values = dict(
        authority_id="TEST_DESIGN_V2",
        full104_substrate_sha256=h("full104"),
        representation_authority_sha256=h("representation"),
        support_estimability_authority_sha256=h("support"),
        canonical_registry_authority_sha256=h("registry"),
        teacher_target_semantics_authority_sha256=h("teacher"),
        target_evidence_budget_template_sha256=template().template_digest(),
        burden_ladder_authority_sha256=h("burden"),
        precision_authority_sha256=h("precision"),
        outer_split_authority_sha256=h("split"),
        target_panel_authority_sha256=h("panel"),
        rng_replay_authority_sha256=h("rng"),
        qualification_runner_source_sha256=h("runner"),
        scientific_semantics_id=APPROVED_SCIENTIFIC_SEMANTICS_IDS[0],
        expression_attacker_role_id=APPROVED_EXPRESSION_ATTACKER_ROLE_IDS[0],
        policy_arms=APPROVED_POLICY_ARMS,
        primary_attacker_id=APPROVED_PRIMARY_ATTACKER_IDS[0],
        primary_attacker_application_policy_id=APPROVED_PRIMARY_ATTACKER_APPLICATION_POLICY_IDS[0],
        secondary_attacker_id=APPROVED_SECONDARY_ATTACKER_IDS[0],
        primary_score_id=APPROVED_PRIMARY_SCORE_IDS[0],
        paired_estimand_id=APPROVED_PAIRED_ESTIMAND_IDS[0],
        controls=REQUIRED_CONTROLS,
        nonlinear_retuning_policy_id=APPROVED_NONLINEAR_RETUNING_POLICY_IDS[0],
        pooled_mean_guardrail_id=APPROVED_POOLED_MEAN_GUARDRAIL_IDS[0],
    )
    values.update(updates)
    return MaskingQualificationDesignAuthorityV2(**values)


class Stub:
    training_authorized = False

    def __init__(self, digest: str, **attrs):
        self._digest = digest
        for key, value in attrs.items():
            setattr(self, key, value)

    def validate(self):
        return None

    def canonical_digest(self):
        return self._digest


def test_burden_free_template_digest_is_compatible_with_existing_v2_template_digest():
    t = template()
    t.validate()
    for num, den in ((1, 20), (1, 10), (3, 20), (1, 5), (3, 10), (1, 2)):
        budget = t.with_fraction(num, den)
        assert budget.template_digest() == t.template_digest()
    assert concrete_budget().template_digest() == t.template_digest()


def test_template_has_no_mask_fraction_field_and_cannot_authorize_training():
    assert "mask_fraction_numerator" not in TargetEvidenceBudgetTemplateAuthorityV1.__dataclass_fields__
    assert "mask_fraction_denominator" not in TargetEvidenceBudgetTemplateAuthorityV1.__dataclass_fields__
    with pytest.raises(ValueError, match="cannot authorize training"):
        template(training_authorized=True).validate()


def test_design_v2_has_no_concrete_budget_or_discovery_universe_root():
    a = design()
    a.validate()
    assert "target_evidence_budget_authority_sha256" not in a.__dataclass_fields__
    assert "address_universe_ladder_authority_sha256" not in a.__dataclass_fields__
    assert a.target_evidence_budget_template_sha256 == template().template_digest()


def test_design_v2_binds_current_roles_and_cross_checks_census_support_registry():
    a = design()
    t = template()
    burden = Stub(a.burden_ladder_authority_sha256, census_authority_sha256=t.census_authority_sha256)
    outer = Stub(a.outer_split_authority_sha256, full104_substrate_sha256=a.full104_substrate_sha256)
    panel = Stub(
        a.target_panel_authority_sha256,
        full104_substrate_sha256=a.full104_substrate_sha256,
        support_estimability_authority_sha256=a.support_estimability_authority_sha256,
        canonical_registry_authority_sha256=a.canonical_registry_authority_sha256,
    )
    precision = Stub(
        a.precision_authority_sha256,
        support_estimability_authority_sha256=a.support_estimability_authority_sha256,
        target_panel_authority_sha256=a.target_panel_authority_sha256,
        outer_split_authority_sha256=a.outer_split_authority_sha256,
    )
    rng = Stub(
        a.rng_replay_authority_sha256,
        canonical_registry_authority_sha256=a.canonical_registry_authority_sha256,
        outer_split_authority_sha256=a.outer_split_authority_sha256,
        target_panel_authority_sha256=a.target_panel_authority_sha256,
        burden_ladder_authority_sha256=a.burden_ladder_authority_sha256,
    )
    a.bind_live_authorities(
        target_evidence_budget_template=t,
        burden_ladder=burden,
        precision=precision,
        outer_split=outer,
        target_panel=panel,
        rng_replay=rng,
    )
    bad_burden = Stub(a.burden_ladder_authority_sha256, census_authority_sha256=h("old-census"))
    with pytest.raises(ValueError, match="different census"):
        a.bind_live_authorities(
            target_evidence_budget_template=t,
            burden_ladder=bad_burden,
            precision=precision,
            outer_split=outer,
            target_panel=panel,
            rng_replay=rng,
        )


def test_current_builders_do_not_import_discovery_universe_or_provisional_freeze_roots():
    paths = (
        "scripts/agent/build_full104_target_evidence_budget_template_authority_v1_20260918.py",
        "scripts/agent/build_full104_burden_ladder_authority_v2_20260918.py",
        "scripts/agent/build_full104_rng_replay_authority_v2_20260918.py",
        "scripts/agent/build_full104_masking_design_authority_v2_20260918.py",
    )
    for path in paths:
        source = Path(path).read_text(encoding="utf-8")
        lowered = source.lower()
        assert "full104_masking_prospective_freeze_status_20260917" not in lowered
        assert "qualification_800_v1" not in lowered
        assert "qualification_6000_v1" not in lowered
        assert "placeholder" not in lowered
    design_source = Path(paths[-1]).read_text(encoding="utf-8")
    assert "address_universe_ladder" not in design_source
    assert "target_evidence_budget_authority_sha256" not in design_source
