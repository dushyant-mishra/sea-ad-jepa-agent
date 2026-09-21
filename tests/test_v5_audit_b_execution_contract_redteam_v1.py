"""Qualification tests for the Audit-B prospective execution contract.

The contract shipped without tests. A contract is not in force until something
enforces it, and an untested enforcement is a claim rather than a mechanism, so
these tests exercise the two properties the contract exists for:

1. **the digest covers the decision rule.** The Phase-IV sample freeze failed
   exactly here -- its digest covered the sample and the bound inputs but not the
   0.05 threshold, the statistic definition, the execution requirements or the
   boundary flags, all of which could be edited without moving it. The mutation
   test below is the one that failure calls for.
2. **execution is refused while the precision scope is unresolved.** This is the
   fail-closed default, and it must not be reachable by omission.

One test documents a gap rather than a guarantee; it is named accordingly.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training. No burden outcome is computed.
"""
from __future__ import annotations

import dataclasses

import pytest

from sea_ad_jepa.v5.audit_b_execution_contract_v1 import (
    ALLOWED_PRECISION_SCOPES,
    AuditBExecutionContractV1,
    CANONICAL_REGISTRY_SHA256,
    EXECUTION_REQUIREMENTS,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    MASK_PLAN_GENERATOR_SHA256,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
    PRECISION_SCOPE_ALL_POLICY_RUNG,
    PRECISION_SCOPE_SINGLE_PRIMARY,
    PRECISION_SCOPE_UNRESOLVED,
)

#: Distinct placeholder digests for the roles the contract records but does not
#: pin. They must differ from one another: the contract requires role-distinct
#: hashes so one artifact cannot stand in for another.
_SAMPLE_ARTIFACT = "1" * 64
_QUALIFICATION_RECEIPT = "2" * 64
_RNG_AUTHORITY = "3" * 64
_BURDEN_ESTIMATOR = "4" * 64


def _contract(**overrides) -> AuditBExecutionContractV1:
    base = dict(
        contract_id="AUDIT_B_PREEXECUTION_REVIEW",
        phase_iv_sample_freeze_digest=PHASE_IV_SAMPLE_FREEZE_DIGEST,
        phase_iv_sample_artifact_sha256=_SAMPLE_ARTIFACT,
        full104_manifest_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        heavy_artifact_sha256=HEAVY_ARTIFACT_SHA256,
        heavy_qualification_receipt_sha256=_QUALIFICATION_RECEIPT,
        rng_authority_sha256=_RNG_AUTHORITY,
        mask_plan_generator_sha256=MASK_PLAN_GENERATOR_SHA256,
        burden_estimator_source_sha256=_BURDEN_ESTIMATOR,
    )
    base.update(overrides)
    return AuditBExecutionContractV1(**base)


# --------------------------------------------------------------------------- #
# The test the sample freeze lacked: the digest must cover the decision rule
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("field,value", [
    ("max_relative_standard_error", 0.50),
    ("precision_scope_id", PRECISION_SCOPE_ALL_POLICY_RUNG),
    ("primary_metric_id", "SOMETHING_ELSE"),
    ("secondary_metric_id", "SOMETHING_ELSE"),
    ("normalization_id", "SOMETHING_ELSE"),
    ("target_aggregation_id", "POOLED_OVER_EVERYTHING"),
    ("precision_estimator_id", "WHATEVER_IS_CONVENIENT"),
    ("sample_ladder", (256, 1024, 65536)),
    ("execution_requirements", EXECUTION_REQUIREMENTS[:-1]),
    ("training_authorized", True),
    ("terminal_masking_outcomes_inspected_before_freeze", True),
    ("phase_iv_sample_artifact_sha256", "9" * 64),
    ("heavy_qualification_receipt_sha256", "8" * 64),
    ("rng_authority_sha256", "7" * 64),
    ("burden_estimator_source_sha256", "6" * 64),
    ("contract_id", "A_DIFFERENT_CONTRACT"),
])
def test_every_decision_element_moves_the_canonical_digest(field, value):
    """Mutating any element of the rule MUST change the digest.

    Validation rejects most of these outright, which is a stronger guarantee than
    merely digesting them. Either outcome is a pass; silently producing the same
    digest is the failure this test exists to catch.
    """
    baseline = _contract().canonical_digest()
    mutated = dataclasses.replace(_contract(), **{field: value})
    try:
        digest = mutated.canonical_digest()
    except ValueError:
        return  # refused outright -- stronger than digest coverage
    assert digest != baseline, (
        f"{field} can be changed without moving canonical_digest(); the decision "
        "rule is not frozen")


def test_canonical_digest_is_stable_and_reproducible():
    assert _contract().canonical_digest() == _contract().canonical_digest()
    assert len(_contract().canonical_digest()) == 64


# --------------------------------------------------------------------------- #
# Fail-closed on the unresolved precision scope
# --------------------------------------------------------------------------- #

def test_precision_scope_defaults_to_unresolved():
    """The default must be the refusing state, not a convenient reading."""
    assert _contract().precision_scope_id == PRECISION_SCOPE_UNRESOLVED


def test_execution_is_refused_while_the_precision_scope_is_unresolved():
    contract = _contract()
    assert contract.execution_authorized is False
    with pytest.raises(ValueError, match="STOP_PRECISION_SCOPE_UNRESOLVED"):
        contract.require_execution_ready()


@pytest.mark.parametrize("scope", [PRECISION_SCOPE_SINGLE_PRIMARY,
                                   PRECISION_SCOPE_ALL_POLICY_RUNG])
def test_a_resolved_scope_authorizes_execution(scope):
    """Both readings are lawful once chosen; the contract does not pick one."""
    contract = _contract(precision_scope_id=scope)
    assert contract.execution_authorized is True
    contract.require_execution_ready()


def test_the_contract_does_not_choose_between_the_two_readings():
    """Neither reading may be privileged as the default."""
    assert ALLOWED_PRECISION_SCOPES[0] == PRECISION_SCOPE_UNRESOLVED
    assert PRECISION_SCOPE_SINGLE_PRIMARY in ALLOWED_PRECISION_SCOPES
    assert PRECISION_SCOPE_ALL_POLICY_RUNG in ALLOWED_PRECISION_SCOPES


def test_an_unknown_precision_scope_is_refused():
    with pytest.raises(ValueError, match="unknown precision_scope_id"):
        _contract(precision_scope_id="ALL_CELLS_BUT_ONLY_THE_CONVENIENT_ONES").validate()


# --------------------------------------------------------------------------- #
# Binding
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("field,message", [
    ("phase_iv_sample_freeze_digest", "different Phase-IV sample freeze"),
    ("full104_manifest_sha256", "different FULL104 manifest"),
    ("canonical_registry_sha256", "different canonical registry"),
    ("heavy_artifact_sha256", "different heavy artifact"),
    ("mask_plan_generator_sha256", "different frozen mask-plan generator"),
])
def test_pinned_roots_cannot_be_swapped(field, message):
    with pytest.raises(ValueError, match=message):
        _contract(**{field: "a" * 64}).validate()


@pytest.mark.parametrize("bad", ["", "not-a-digest", "A" * 64, "f" * 63, "g" * 64])
def test_malformed_digests_are_refused(bad):
    with pytest.raises(ValueError):
        _contract(rng_authority_sha256=bad).validate()


def test_roles_must_stay_distinct():
    """One artifact must not be able to stand in for another role."""
    with pytest.raises(ValueError, match="role-distinct"):
        _contract(rng_authority_sha256=_BURDEN_ESTIMATOR).validate()


def test_training_can_never_be_authorized_here():
    with pytest.raises(ValueError, match="cannot authorize training"):
        _contract(training_authorized=True).validate()


def test_the_contract_must_predate_any_terminal_outcome():
    with pytest.raises(ValueError, match="freeze before"):
        _contract(terminal_masking_outcomes_inspected_before_freeze=True).validate()


def test_the_escalation_threshold_is_the_frozen_one():
    assert _contract().max_relative_standard_error == 0.05
    with pytest.raises(ValueError, match="threshold drifted"):
        _contract(max_relative_standard_error=0.5).validate()


def test_the_ladder_is_the_frozen_prefix_ladder():
    assert _contract().sample_ladder == (256, 1024, 4096)
    with pytest.raises(ValueError, match="ladder drifted"):
        _contract(sample_ladder=(256, 1024, 4096, 16384)).validate()


def test_b3_cannot_drive_escalation_per_the_bound_requirements():
    reqs = " ".join(_contract().execution_requirements)
    assert "descriptive only and cannot drive escalation" in reqs
    assert "precision only" in reqs
    assert "prefix" in reqs


# --------------------------------------------------------------------------- #
# The RNG authority is bound by MEANING, not by file bytes
# --------------------------------------------------------------------------- #

def test_the_rng_authority_digest_is_not_pinned_to_a_literal_value():
    """Deliberate, and not the weakness it first looks like.

    ``rng_authority_sha256`` is the canonical digest of the *authority object*,
    rebuilt from the current pre-panel roots, so no literal value can be baked in
    here. What stops a wrong authority being supplied is the pair of semantic
    identifiers asserted below, plus the preflight's reconstruction of the
    authority and comparison of its recomputed canonical digest against this
    field.
    """
    contract = _contract(rng_authority_sha256="d" * 64)
    contract.validate()
    assert contract.rng_authority_sha256 == "d" * 64


def test_the_contract_refuses_the_superseded_v2_rng_authority():
    """The substantive guarantee: V3 cannot be swapped for the authority it
    replaces, whose global seed depended on the target-panel selection."""
    assert _contract().rng_authority_schema_id == "V5_MASKING_RNG_REPLAY_AUTHORITY_V3"
    with pytest.raises(ValueError, match="RNG authority schema drifted"):
        _contract(rng_authority_schema_id="V5_MASKING_RNG_REPLAY_AUTHORITY_V2").validate()


def test_panel_independence_is_pinned_as_a_declared_property():
    """A later target-panel decision may only SUBSET already-defined masks;
    changing panel size must never reroll them. The contract refuses any other
    declared dependency, so the property cannot be weakened silently."""
    assert _contract().rng_target_panel_dependency_id ==         "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS"
    with pytest.raises(ValueError, match="RNG target-panel dependency drifted"):
        _contract(rng_target_panel_dependency_id="TARGET_PANEL_SIZE").validate()
