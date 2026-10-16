from __future__ import annotations

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c

METHOD = "1" * 64
METHOD_RENAMED = "2" * 64


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


def _sealed_dev(*, campaign_id="dev-hostile", dependencies=None):
    camp = c.create_campaign(campaign_id, dependencies or _deps(), barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=b"hidden-fixture")
    rows = [
        {"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
        {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "A"},
    ]
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    return camp, definition, sealed


def test_exposure_spend_survives_crash_or_abandonment():
    camp, definition, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=METHOD)
    assert camp.exposures_consumed == 1
    camp = c.record_exposure_terminal(camp, e0, terminal_status="TECHNICAL_FAILURE")
    assert camp.exposures_consumed == 1


def test_method_scientific_identity_must_be_canonical_digest_not_name():
    camp, _, sealed = _sealed_dev()
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity="method-v1")


def test_method_rename_cannot_reset_exposure_count():
    camp, _, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=METHOD)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=METHOD_RENAMED)


def test_hand_constructed_exposure_record_cannot_freeze_output():
    camp, _, sealed = _sealed_dev()
    camp, real = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=METHOD)
    forged = c.ExposureRecord(
        campaign.campaign_identity,
        "forged-exp",
        "r0",
        "a" * 64,
        METHOD_RENAMED,
        real.ordinal,
    )
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.freeze_method_output(camp, forged, output_sha256="c" * 64)


def test_reveal_before_output_freeze_is_refused():
    camp, definition, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=METHOD)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"hidden-fixture")


def test_output_mutation_after_freeze_is_refused():
    camp, _, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=METHOD)
    camp, receipt = c.freeze_method_output(camp, e0, output_sha256="c" * 64)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.freeze_method_output(camp, e0, output_sha256="d" * 64)


def test_reveal_mismatch_is_refused_after_all_outputs_frozen():
    camp, definition, sealed = _sealed_dev()
    for rid, out in [("r0", "c" * 64), ("r1", "d" * 64)]:
        camp, exp = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=METHOD)
        camp, _ = c.freeze_method_output(camp, exp, output_sha256=out)
    assert camp.state is c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"wrong")


def test_missing_committed_world_blocks_finalization():
    camp, definition, sealed = _sealed_dev()
    camp, exp = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=METHOD)
    camp, _ = c.freeze_method_output(camp, exp, output_sha256="c" * 64)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.finalize_custody(camp, sealed)


def test_fresh_ledger_restart_cannot_reuse_same_campaign_identity():
    a, _, _ = _sealed_dev(campaign_id="restart", dependencies=_deps(genesis_ledger_identity="0" * 64))
    b, _, _ = _sealed_dev(campaign_id="restart", dependencies=_deps(genesis_ledger_identity="1" * 64))
    assert a.campaign_identity != b.campaign_identity
