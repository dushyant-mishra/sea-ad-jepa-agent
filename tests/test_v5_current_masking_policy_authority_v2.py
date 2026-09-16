"""Attack tests for the masking-authority schema repair (V1 defect, §21).

V1 found that MaskingAuthorityV1 accepts free-form identifiers and binds no SHA roots --
the same weakness that was repaired for the target-address provider authority. This is a
SCHEMA repair only: no production masking policy is instantiated or frozen, because V2 has
not scientifically qualified.
"""
from __future__ import annotations

import dataclasses

import pytest

from sea_ad_jepa.v5.current_masking_policy_authority_v2 import (
    APPROVED_ELIGIBILITY_POLICY_IDS,
    APPROVED_FALLBACK_POLICY_IDS,
    APPROVED_MASKING_POLICY_IDS,
    APPROVED_RNG_REPLAY_AUTHORITY_IDS,
    APPROVED_TARGET_EVIDENCE_BUDGET_AUTHORITY_IDS,
    CurrentMaskingPolicyAuthorityV2,
)
from sea_ad_jepa.v5.current_target_address_provider_authority_v1 import (
    CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
    KNOWN_RAW_ARTIFACT_SHA256,
)

SUPPORT = "1" * 64
SHORTCUT = "2" * 64
BUDGET = "3" * 64
RNG = "4" * 64


def make(**over) -> CurrentMaskingPolicyAuthorityV2:
    base = dict(
        authority_id="V5_CURRENT_MASKING_POLICY_AUTHORITY_SCHEMA_ONLY",
        canonical_registry_authority_sha256=CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
        support_estimability_authority_sha256=SUPPORT,
        shortcut_artifact_sha256=SHORTCUT,
        masking_policy_id="V5_UNIFORM_PLUS_SHORTCUT_COMASK_V2",
        target_evidence_budget_authority_id="V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        target_evidence_budget_authority_sha256=BUDGET,
        rng_replay_authority_id="V5_DETERMINISTIC_MASK_REPLAY_AUTHORITY_V1",
        rng_replay_authority_sha256=RNG,
        eligibility_policy_id="SUPPORT_ESTIMABILITY_AUTHORITY_ELIGIBILITY_V1",
        fallback_policy_id="DETERMINISTIC_UNIFORM_FALLBACK_V1",
    )
    base.update(over)
    return CurrentMaskingPolicyAuthorityV2(**base)


def test_lawful_authority_validates() -> None:
    make().validate()
    assert len(make().canonical_digest()) == 64


# ---------------------------------------------------------------- free-string defect
@pytest.mark.parametrize("field", ["masking_policy_id", "target_evidence_budget_authority_id",
                                   "rng_replay_authority_id", "eligibility_policy_id",
                                   "fallback_policy_id"])
@pytest.mark.parametrize("bad", ["anything", "TD60", "historical_mask", "trust_me",
                                 "corrmask", "pearson_graph_v1", "TD57", "TD59"])
def test_arbitrary_policy_identifiers_fail_closed(field: str, bad: str) -> None:
    with pytest.raises(ValueError, match=field):
        dataclasses.replace(make(), **{field: bad}).validate()


def test_no_approved_vocabulary_carries_a_historical_experiment_name() -> None:
    for vocab in (APPROVED_MASKING_POLICY_IDS, APPROVED_TARGET_EVIDENCE_BUDGET_AUTHORITY_IDS,
                  APPROVED_RNG_REPLAY_AUTHORITY_IDS, APPROVED_ELIGIBILITY_POLICY_IDS,
                  APPROVED_FALLBACK_POLICY_IDS):
        assert vocab
        for v in vocab:
            assert not any(t in v.upper() for t in ("TD57", "TD59", "TD60", "CORRMASK"))


# ---------------------------------------------------------------- exact root binding
@pytest.mark.parametrize("bad", ["b" * 64, "0" * 64, "f" * 64, "deadbeef" * 8])
def test_arbitrary_registry_authority_digest_fails_closed(bad: str) -> None:
    with pytest.raises(ValueError, match="canonical_registry_authority_sha256"):
        dataclasses.replace(make(), canonical_registry_authority_sha256=bad).validate()


@pytest.mark.parametrize("raw", list(KNOWN_RAW_ARTIFACT_SHA256))
def test_raw_artifact_digest_cannot_stand_in_for_an_authority_root(raw: str) -> None:
    with pytest.raises(ValueError):
        dataclasses.replace(make(), canonical_registry_authority_sha256=raw).validate()
    with pytest.raises(ValueError):
        dataclasses.replace(make(), support_estimability_authority_sha256=raw).validate()


# ---------------------------------------------------------------- role splicing
@pytest.mark.parametrize("a,b", [
    ("support_estimability_authority_sha256", "shortcut_artifact_sha256"),
    ("shortcut_artifact_sha256", "target_evidence_budget_authority_sha256"),
    ("target_evidence_budget_authority_sha256", "rng_replay_authority_sha256"),
    ("support_estimability_authority_sha256", "rng_replay_authority_sha256"),
])
def test_distinct_roles_cannot_share_one_digest(a: str, b: str) -> None:
    shared = "9" * 64
    with pytest.raises(ValueError, match="distinct"):
        dataclasses.replace(make(), **{a: shared, b: shared}).validate()


def test_registry_root_cannot_be_reused_as_another_role() -> None:
    with pytest.raises(ValueError, match="distinct"):
        dataclasses.replace(
            make(), shortcut_artifact_sha256=CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256
        ).validate()


# ---------------------------------------------------------------- malformed digests
@pytest.mark.parametrize("field", ["support_estimability_authority_sha256",
                                   "shortcut_artifact_sha256",
                                   "target_evidence_budget_authority_sha256",
                                   "rng_replay_authority_sha256"])
def test_malformed_digest_fails_closed(field: str) -> None:
    for bad in ("not-a-sha", "ABCDEF" * 10 + "abcd", "12345"):
        with pytest.raises(ValueError, match=field):
            dataclasses.replace(make(), **{field: bad}).validate()


# ---------------------------------------------------------------- training authority
def test_authority_cannot_turn_training_on() -> None:
    assert make().training_authorized is False
    with pytest.raises(ValueError, match="training"):
        dataclasses.replace(make(), training_authorized=True).validate()


# ---------------------------------------------------------------- budget ownership
def test_authority_does_not_carry_a_numeric_mask_fraction() -> None:
    """V1 finding: mask burden belongs to the evidence-budget authority, not here."""
    fields = {f.name for f in dataclasses.fields(CurrentMaskingPolicyAuthorityV2)}
    for forbidden in ("mask_fraction", "mask_burden", "n_masked", "blocks", "evidence_budget"):
        assert forbidden not in fields, f"{forbidden} must not live on the masking authority"
    assert "target_evidence_budget_authority_sha256" in fields


def test_digest_is_stable_and_order_independent() -> None:
    assert make().canonical_digest() == make().canonical_digest()
    assert make().canonical_digest() != dataclasses.replace(
        make(), shortcut_artifact_sha256="a" * 64).canonical_digest()
