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


def test_campaign_binds_exact_sealed_definition_identity():
    campaign = c.create_campaign("dev-definition-bind", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    campaign, committed = c.seal_definition(campaign, family="committed-family", hidden_spec=b"committed")
    assert campaign.sealed_definition_sha256 == c._sha(committed.to_payload())

    forged = c.SealedChallengeDefinition(
        campaign_identity=campaign.campaign_identity,
        family="replacement-family",
        hidden_spec_commitment=hashlib.sha256(b"replacement").hexdigest(),
        namespace="DEVELOPMENT",
    )
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.seal_realization_set(campaign, forged, _rows("x", "a", "b"), budget=2)


def test_campaign_binds_exact_realization_root_and_rejects_root_aliasing():
    campaign = c.create_campaign("dev-set-bind", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    campaign, definition = c.seal_definition(campaign, family="committed-family", hidden_spec=b"hidden")
    campaign, committed = c.seal_realization_set(campaign, definition, _rows("r", "a", "b"), budget=2)
    assert campaign.sealed_realization_root == committed.sealed_root

    forged = c.SealedRealizationSet(
        campaign_identity=campaign.campaign_identity,
        definition_sha256=committed.definition_sha256,
        realization_ids=("evil0", "evil1"),
        content_sha256s=("e" * 64, "f" * 64),
        challenge_classes=("EVIL", "EVIL"),
        budget=2,
        sealed_root=committed.sealed_root,
    )
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(campaign, forged, realization_id="evil0", method_scientific_identity="8" * 64)


def test_reveal_rejects_definition_substitution_even_with_matching_hidden_bytes():
    campaign = c.create_campaign("dev-reveal-bind", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    campaign, definition = c.seal_definition(campaign, family="committed-family", hidden_spec=b"hidden")
    campaign, sealed = c.seal_realization_set(campaign, definition, _rows("r", "a", "b"), budget=2)
    for rid in sealed.realization_ids:
        campaign, exposure = c.issue_exposure(campaign, sealed, realization_id=rid, method_scientific_identity=("8" if rid.endswith("0") else "9") * 64)
        campaign, _ = c.freeze_method_output(campaign, exposure, output_sha256=("1" if rid.endswith("0") else "2") * 64)
        campaign = c.record_exposure_terminal(campaign, exposure, terminal_status="EVALUATED")
    assert campaign.state is c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN

    forged_definition = c.SealedChallengeDefinition(
        campaign_identity=campaign.campaign_identity,
        family="different-family",
        hidden_spec_commitment=hashlib.sha256(b"hidden").hexdigest(),
        namespace="DEVELOPMENT",
    )
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(campaign, forged_definition, sealed, hidden_spec=b"hidden")
