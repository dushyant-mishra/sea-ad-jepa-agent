from __future__ import annotations

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c

METHOD = "1" * 64


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


def _all_outputs_frozen_without_terminals():
    camp = c.create_campaign("pre-reveal-accounting", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=b"hidden-fixture")
    rows = [
        {"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
        {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "A"},
    ]
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    exposures = []
    for rid, out in (("r0", "c" * 64), ("r1", "d" * 64)):
        camp, exposure = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=METHOD)
        exposures.append(exposure)
        camp, _ = c.freeze_method_output(camp, exposure, output_sha256=out)
    return camp, definition, sealed, exposures


def test_hidden_material_requires_complete_terminal_accounting_before_reveal():
    camp, definition, sealed, _ = _all_outputs_frozen_without_terminals()
    assert camp.state is c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN
    assert camp.terminal_statuses == ()
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"hidden-fixture")


def test_terminal_accounting_is_closed_once_hidden_material_is_revealed():
    camp, definition, sealed, exposures = _all_outputs_frozen_without_terminals()
    for exposure in exposures:
        camp = c.record_exposure_terminal(camp, exposure, terminal_status="EVALUATED")
    camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"hidden-fixture")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.record_exposure_terminal(camp, exposures[0], terminal_status="EVALUATED")
