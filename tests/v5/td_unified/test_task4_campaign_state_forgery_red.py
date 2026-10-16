from __future__ import annotations

import hashlib

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c


def _deps():
    return c.validate_campaign_dependencies({
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
    })


def _forged_advanced_state():
    deps = _deps()
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
    sealed = c.SealedRealizationSet(
        campaign_identity=campaign_identity,
        definition_sha256=definition_sha,
        realization_ids=ids,
        content_sha256s=digests,
        challenge_classes=classes,
        budget=2,
        sealed_root=root,
    )
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


def test_directly_constructed_advanced_campaign_cannot_issue_exposure():
    campaign, _, sealed = _forged_advanced_state()
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(
            campaign,
            sealed,
            realization_id="r0",
            method_scientific_identity="8" * 64,
        )


def test_directly_constructed_reveal_ready_campaign_cannot_reveal_hidden_material():
    campaign, definition, sealed = _forged_advanced_state()
    forged = c.QualificationCampaign(
        **{
            **campaign.__dict__,
            "state": c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN,
            "exposures_consumed": 2,
            "exposed_realization_ids": ("r0", "r1"),
            "issued_exposures": (
                ("exp-1", "r0", "a" * 64, "8" * 64, 1),
                ("exp-2", "r1", "b" * 64, "9" * 64, 2),
            ),
            "frozen_outputs": (("r0", "1" * 64), ("r1", "2" * 64)),
            "terminal_statuses": (("r0", "EVALUATED"), ("r1", "EVALUATED")),
        }
    )
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(
            forged,
            definition,
            sealed,
            hidden_spec=b"forged-hidden",
        )
