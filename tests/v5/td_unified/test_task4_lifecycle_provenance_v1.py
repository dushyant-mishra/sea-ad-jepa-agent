from __future__ import annotations

import hashlib
from dataclasses import replace

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


def _rows():
    return [
        {"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
        {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "B"},
    ]


def _forged_advanced_state():
    deps = c.validate_campaign_dependencies(_deps())
    campaign_id = "forged-campaign"
    campaign_identity = c._campaign_identity(campaign_id, deps, "DEVELOPMENT")
    definition = c.SealedChallengeDefinition(
        campaign_identity=campaign_identity,
        family="forged-family",
        hidden_spec_commitment=hashlib.sha256(b"forged-hidden").hexdigest(),
        namespace="DEVELOPMENT",
    )
    definition_sha = c._sha(definition.to_payload())
    ids = ("r0", "r1")
    digests = ("a" * 64, "b" * 64)
    classes = ("A", "B")
    root = c._sha({
        "campaign_identity": campaign_identity,
        "definition_sha256": definition_sha,
        "realization_ids": ids,
        "content_sha256s": digests,
        "challenge_classes": classes,
        "budget": 2,
    })
    sealed = c.SealedRealizationSet(campaign_identity, definition_sha, ids, digests, classes, 2, root)
    campaign = c.QualificationCampaign(
        campaign_id=campaign_id,
        dependencies=deps,
        namespace="DEVELOPMENT",
        promotion_authority="NONE",
        state=c.CampaignState.REALIZATION_SET_SEALED,
        campaign_identity=campaign_identity,
        sealed_definition_sha256=definition_sha,
        sealed_realization_root=root,
        exposures_consumed=0,
        sealed_budget=2,
    )
    return campaign, definition, sealed


def test_direct_advanced_campaign_construction_is_not_lawful_provenance():
    campaign, _, sealed = _forged_advanced_state()
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(campaign, sealed, realization_id="r0", method_scientific_identity="8" * 64)


def test_copying_token_from_lawful_campaign_does_not_authorize_forged_state():
    campaign = c.create_campaign("copy-token-attack", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    campaign, definition = c.seal_definition(campaign, family="family", hidden_spec=b"hidden")
    campaign, sealed = c.seal_realization_set(campaign, definition, _rows(), budget=2)

    forged = replace(
        campaign,
        state=c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN,
        exposures_consumed=2,
        exposed_realization_ids=("r0", "r1"),
        issued_exposures=(
            ("exp-1", "r0", "a" * 64, "8" * 64, 1),
            ("exp-2", "r1", "b" * 64, "9" * 64, 2),
        ),
        frozen_outputs=(("r0", "1" * 64), ("r1", "2" * 64)),
        terminal_statuses=(("r0", "EVALUATED"), ("r1", "EVALUATED")),
    )

    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(forged, definition, sealed, hidden_spec=b"hidden")


def test_lawful_transition_chain_remains_usable():
    campaign = c.create_campaign("lawful-chain", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    campaign, definition = c.seal_definition(campaign, family="family", hidden_spec=b"hidden")
    campaign, sealed = c.seal_realization_set(campaign, definition, _rows(), budget=2)
    campaign, exposure = c.issue_exposure(campaign, sealed, realization_id="r0", method_scientific_identity="8" * 64)
    assert exposure.realization_id == "r0"
