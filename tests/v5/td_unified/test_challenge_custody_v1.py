from __future__ import annotations

import hashlib

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c
from scripts.v5.td_unified.task4_authority_barrier_v1 import Task4BarrierStatus


def _forged_barrier():
    checks = {
        "C1_PERSISTENT_REVOCATION": "PERSISTENT_EXTERNAL",
        "C3_CURRENT_REGISTRY": "PASS",
        "C4_DIAGNOSTIC_ONLY": "PASS",
        "C5_ACTOR_CREDENTIALS": "AUTHENTICATED_EXTERNAL",
        "C6_REVOCATION_ACTOR_POLICY": "PASS",
        "C7_REQUIREMENT_CLASSES": "PASS",
        "C8_TASK1_CONSTRUCTION_LAW": "PASS",
        "C9_PROCESS_ISOLATION": "PASS",
        "R5_CLAIM_SCOPE": "PASS",
    }
    return Task4BarrierStatus("GREEN", checks)


def _deps():
    return {
        "task2_manifest_sha": "1" * 64,
        "task3_registry_sha": "2" * 64,
        "unit_ids": ("G8",),
        "generator_code_sha": "3" * 40,
        "generator_policy_sha": "4" * 64,
        "rng_policy_sha": "5" * 64,
        "challenge_family_sha": "6" * 64,
        "adjudication_contract_sha": "7" * 64,
        "multiplicity_policy_sha": "8" * 64,
    }


def test_development_campaign_is_explicitly_nonauthorizing():
    camp = c.create_campaign("dev-1", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    assert camp.state is c.CampaignState.CAMPAIGN_CREATED
    assert camp.promotion_authority == "NONE"


def test_final_campaign_refuses_missing_or_caller_forged_barrier_status():
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("final-1", _deps(), barrier_status=None, namespace="FINAL")
    # A caller-created GREEN data object is not evidence that the current
    # registry/custody/actor state was actually re-resolved by the harness.
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("final-1", _deps(), barrier_status=_forged_barrier(), namespace="FINAL")


def test_campaign_id_binds_dependencies():
    camp = c.create_campaign("dev-id", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    altered = dict(_deps(), generator_policy_sha="9" * 64)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.assert_same_campaign_identity(camp, "dev-id", altered)


def test_definition_public_payload_contains_commitment_not_hidden_bytes():
    camp = c.create_campaign("dev-2", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    hidden = b"DUMMY-HIDDEN-SPEC-NEVER-PRODUCTION"
    camp2, definition = c.seal_definition(camp, family="fixture-family", hidden_spec=hidden)
    payload = definition.to_payload()
    assert hidden.decode() not in repr(payload)
    assert payload["hidden_spec_commitment"] == hashlib.sha256(hidden).hexdigest()
    assert camp2.state is c.CampaignState.DEFINITION_SEALED


def test_finite_realization_set_refuses_duplicates_budget_mismatch_and_reordering():
    camp = c.create_campaign("dev-3", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture-family", hidden_spec=b"hidden")
    rows = [
        {"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
        {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "A"},
    ]
    camp2, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    assert camp2.state is c.CampaignState.REALIZATION_SET_SEALED
    assert sealed.realization_ids == ("r0", "r1")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.seal_realization_set(camp, definition, rows, budget=3)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.seal_realization_set(camp, definition, rows + [rows[0]], budget=3)
