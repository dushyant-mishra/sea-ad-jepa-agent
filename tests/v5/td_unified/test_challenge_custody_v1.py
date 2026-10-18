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


def _deps(**overrides):
    deps = {
        "task2_manifest_sha": "1" * 64,
        "task3_registry_sha": "2" * 64,
        "registry_unit_identities": (("G8", "3" * 64),),
        "producer_actor_identity": "4" * 64,
        "executor_actor_identity": "5" * 64,
        "controller_actor_identity": "6" * 64,
        "adjudicator_actor_identity": "7" * 64,
        "challenge_generator_code_sha": "8" * 40,
        "challenge_generator_policy_sha": "9" * 64,
        "realization_schema_sha": "a" * 64,
        "rng_policy_sha": "b" * 64,
        "challenge_family_sha": "c" * 64,
        "adjudication_contract_sha": "d" * 64,
        "multiplicity_policy_sha": "e" * 64,
        "publication_policy_sha": "f" * 64,
        "genesis_ledger_identity": "0" * 64,
        "authority_scope": "UNIT:G8",
        "authority_restrictions": ("NO_TRAINING_AUTHORITY",),
        "qualification_budget": 2,
    }
    deps.update(overrides)
    return deps


def test_development_campaign_is_explicitly_nonauthorizing():
    camp = c.create_campaign("dev-1", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    assert camp.state is c.CampaignState.CAMPAIGN_CREATED
    assert camp.promotion_authority == "NONE"


def test_final_campaign_refuses_missing_or_caller_forged_barrier_status():
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("final-1", _deps(), barrier_status=None, namespace="FINAL")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("final-1", _deps(), barrier_status=_forged_barrier(), namespace="FINAL")


def test_campaign_requires_complete_closed_dependency_contract():
    for missing in (
        "task2_manifest_sha", "task3_registry_sha", "registry_unit_identities",
        "producer_actor_identity", "executor_actor_identity", "controller_actor_identity",
        "adjudicator_actor_identity", "challenge_generator_code_sha",
        "challenge_generator_policy_sha", "realization_schema_sha", "rng_policy_sha",
        "challenge_family_sha", "adjudication_contract_sha", "multiplicity_policy_sha",
        "publication_policy_sha", "genesis_ledger_identity", "authority_scope",
        "authority_restrictions", "qualification_budget",
    ):
        deps = _deps()
        deps.pop(missing)
        with pytest.raises(c.Task4ChallengeCustodyError):
            c.create_campaign("missing-" + missing, deps, barrier_status=None, namespace="DEVELOPMENT")


def test_campaign_rejects_privileged_actor_aliasing():
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign(
            "actor-alias",
            _deps(controller_actor_identity="4" * 64),
            barrier_status=None,
            namespace="DEVELOPMENT",
        )


def test_new_genesis_ledger_creates_new_campaign_identity():
    a = c.create_campaign("same-id", _deps(genesis_ledger_identity="0" * 64), barrier_status=None, namespace="DEVELOPMENT")
    b = c.create_campaign("same-id", _deps(genesis_ledger_identity="1" * 64), barrier_status=None, namespace="DEVELOPMENT")
    assert a.campaign_identity != b.campaign_identity


def test_campaign_id_binds_every_decision_bearing_dependency():
    camp = c.create_campaign("dev-id", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    for key, value in (
        ("challenge_generator_policy_sha", "1" * 64),
        ("realization_schema_sha", "2" * 64),
        ("publication_policy_sha", "3" * 64),
        ("genesis_ledger_identity", "4" * 64),
    ):
        altered = _deps(**{key: value})
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


def test_realization_budget_must_equal_frozen_campaign_budget():
    camp = c.create_campaign("dev-budget", _deps(qualification_budget=2), barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture-family", hidden_spec=b"hidden")
    rows = [
        {"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
        {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "A"},
    ]
    c.seal_realization_set(camp, definition, rows, budget=2)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.seal_realization_set(camp, definition, rows, budget=3)


def test_finite_realization_set_refuses_duplicates_and_budget_mismatch():
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
        c.seal_realization_set(camp, definition, rows + [rows[0]], budget=3)
