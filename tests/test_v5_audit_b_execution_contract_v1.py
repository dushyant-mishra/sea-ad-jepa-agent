import dataclasses
import hashlib

import pytest

from sea_ad_jepa.v5.audit_b_execution_contract_v1 import (
    CANONICAL_REGISTRY_SHA256,
    EXECUTION_REQUIREMENTS,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    MASK_PLAN_GENERATOR_SHA256,
    MAX_RELATIVE_STANDARD_ERROR,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
    PRECISION_SCOPE_ALL_POLICY_RUNG,
    PRECISION_SCOPE_SINGLE_PRIMARY,
    PRECISION_SCOPE_UNRESOLVED,
    AuditBExecutionContractV1,
)


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def contract(**updates) -> AuditBExecutionContractV1:
    values = dict(
        contract_id="TEST_AUDIT_B_EXECUTION_V1",
        phase_iv_sample_freeze_digest=PHASE_IV_SAMPLE_FREEZE_DIGEST,
        phase_iv_sample_artifact_sha256=h("sample-artifact"),
        full104_manifest_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        heavy_artifact_sha256=HEAVY_ARTIFACT_SHA256,
        heavy_qualification_receipt_sha256=h("heavy-qualification-v2"),
        rng_authority_sha256=h("rng-v3"),
        mask_plan_generator_sha256=MASK_PLAN_GENERATOR_SHA256,
        burden_estimator_source_sha256=h("burden-estimator"),
    )
    values.update(updates)
    return AuditBExecutionContractV1(**values)


def test_unresolved_precision_scope_explicitly_forbids_execution() -> None:
    c = contract()
    c.validate()
    assert c.execution_authorized is False
    with pytest.raises(ValueError, match="STOP_PRECISION_SCOPE_UNRESOLVED"):
        c.require_execution_ready()


@pytest.mark.parametrize(
    "scope",
    [PRECISION_SCOPE_SINGLE_PRIMARY, PRECISION_SCOPE_ALL_POLICY_RUNG],
)
def test_only_explicitly_resolved_precision_scope_can_be_execution_ready(scope: str) -> None:
    c = contract(precision_scope_id=scope)
    c.require_execution_ready()
    assert c.execution_authorized is True


def test_contract_digest_changes_when_precision_scope_changes() -> None:
    unresolved = contract().canonical_digest()
    one = contract(precision_scope_id=PRECISION_SCOPE_SINGLE_PRIMARY).canonical_digest()
    eighteen = contract(precision_scope_id=PRECISION_SCOPE_ALL_POLICY_RUNG).canonical_digest()
    assert len({unresolved, one, eighteen}) == 3


def test_scientific_execution_rules_are_not_mutable_without_invalidating_contract() -> None:
    with pytest.raises(ValueError, match="threshold drifted"):
        dataclasses.replace(
            contract(),
            max_relative_standard_error=MAX_RELATIVE_STANDARD_ERROR + 0.01,
        ).validate()

    changed = list(EXECUTION_REQUIREMENTS)
    changed[-1] = "N1/N2/N3 may be changed after results"
    with pytest.raises(ValueError, match="execution requirements drifted"):
        dataclasses.replace(contract(), execution_requirements=tuple(changed)).validate()


def test_original_sample_freeze_and_bound_artifact_roots_cannot_be_swapped() -> None:
    with pytest.raises(ValueError, match="different Phase-IV sample freeze"):
        dataclasses.replace(
            contract(), phase_iv_sample_freeze_digest=h("other-freeze")
        ).validate()
    with pytest.raises(ValueError, match="different heavy artifact"):
        dataclasses.replace(contract(), heavy_artifact_sha256=h("other-heavy")).validate()
    with pytest.raises(ValueError, match="different frozen mask-plan generator"):
        dataclasses.replace(
            contract(), mask_plan_generator_sha256=h("other-plan")
        ).validate()


def test_outcome_or_training_state_cannot_be_laundered_into_contract() -> None:
    with pytest.raises(ValueError, match="freeze before"):
        dataclasses.replace(
            contract(), terminal_masking_outcomes_inspected_before_freeze=True
        ).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        dataclasses.replace(contract(), training_authorized=True).validate()


def test_every_scientific_choice_is_digest_covered() -> None:
    base = contract(precision_scope_id=PRECISION_SCOPE_SINGLE_PRIMARY)
    digest = base.canonical_digest()

    # Fields that define how Audit B would be interpreted cannot be omitted from
    # the canonical scientific state. Each lawful alternative or bound-root change
    # must therefore change the digest, while illegal drift fails validation.
    assert digest != dataclasses.replace(
        base, precision_scope_id=PRECISION_SCOPE_ALL_POLICY_RUNG
    ).canonical_digest()
    assert digest != dataclasses.replace(
        base, rng_authority_sha256=h("other-rng")
    ).canonical_digest()
    assert digest != dataclasses.replace(
        base, burden_estimator_source_sha256=h("other-estimator")
    ).canonical_digest()


def test_duplicate_role_hashes_are_rejected() -> None:
    c = contract(rng_authority_sha256=h("sample-artifact"))
    with pytest.raises(ValueError, match="role-distinct"):
        c.validate()
