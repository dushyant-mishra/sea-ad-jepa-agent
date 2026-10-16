from __future__ import annotations

import hashlib

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c


def _deps():
    return {
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


def _rows(prefix: str, first: str, second: str):
    return [
        {"realization_id": f"{prefix}0", "content_sha256": first * 64, "challenge_class": "A"},
        {"realization_id": f"{prefix}1", "content_sha256": second * 64, "challenge_class": "B"},
    ]


def test_postseal_definition_substitution_is_rejected():
    campaign = c.create_campaign("dev-seal-substitution", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    campaign, committed_definition = c.seal_definition(
        campaign,
        family="committed-family",
        hidden_spec=b"committed-hidden-spec",
    )

    forged_definition = c.SealedChallengeDefinition(
        campaign_identity=campaign.campaign_identity,
        family="replacement-family",
        hidden_spec_commitment=hashlib.sha256(b"replacement-hidden-spec").hexdigest(),
        namespace="DEVELOPMENT",
    )

    assert forged_definition != committed_definition
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.seal_realization_set(
            campaign,
            forged_definition,
            _rows("x", "a", "b"),
            budget=2,
        )


def test_postseal_realization_set_substitution_is_rejected_at_exposure():
    campaign = c.create_campaign("dev-set-substitution", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    campaign, definition = c.seal_definition(campaign, family="committed-family", hidden_spec=b"hidden")
    campaign, committed = c.seal_realization_set(campaign, definition, _rows("r", "a", "b"), budget=2)

    forged = c.SealedRealizationSet(
        campaign_identity=campaign.campaign_identity,
        definition_sha256="d" * 64,
        realization_ids=("evil0", "evil1"),
        content_sha256s=("e" * 64, "f" * 64),
        challenge_classes=("EVIL", "EVIL"),
        budget=2,
        sealed_root="9" * 64,
    )

    assert forged.sealed_root != committed.sealed_root
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(
            campaign,
            forged,
            realization_id="evil0",
            method_scientific_identity="8" * 64,
        )
