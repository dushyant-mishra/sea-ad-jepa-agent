from __future__ import annotations

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c


def _sealed_dev():
    deps = {
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
    camp = c.create_campaign("dev-hostile", deps, barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=b"hidden-fixture")
    rows = [
        {"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
        {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "A"},
    ]
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    return camp, definition, sealed


def test_exposure_spend_survives_crash_or_abandonment():
    camp, definition, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity="m1")
    assert camp.exposures_consumed == 1
    camp = c.record_exposure_terminal(camp, e0, terminal_status="TECHNICAL_FAILURE")
    assert camp.exposures_consumed == 1


def test_method_rename_cannot_reset_exposure_count():
    camp, _, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity="m1")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity="m1-renamed")


def test_reveal_before_output_freeze_is_refused():
    camp, definition, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity="m1")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"hidden-fixture")


def test_output_mutation_after_freeze_is_refused():
    camp, _, sealed = _sealed_dev()
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity="m1")
    camp, receipt = c.freeze_method_output(camp, e0, output_sha256="c" * 64)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.freeze_method_output(camp, e0, output_sha256="d" * 64)


def test_reveal_mismatch_is_refused_after_all_outputs_frozen():
    camp, definition, sealed = _sealed_dev()
    for rid, out in [("r0", "c" * 64), ("r1", "d" * 64)]:
        camp, exp = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity="m1")
        camp, _ = c.freeze_method_output(camp, exp, output_sha256=out)
    assert camp.state is c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"wrong")


def test_missing_committed_world_blocks_finalization():
    camp, definition, sealed = _sealed_dev()
    camp, exp = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity="m1")
    camp, _ = c.freeze_method_output(camp, exp, output_sha256="c" * 64)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.finalize_custody(camp, sealed)
