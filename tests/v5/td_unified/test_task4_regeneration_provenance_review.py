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


def _revealed_campaign():
    camp = c.create_campaign("regen-provenance", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=b"hidden-fixture")
    rows = [
        {"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
        {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "A"},
    ]
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    for rid, out in (("r0", "c" * 64), ("r1", "d" * 64)):
        camp, exposure = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=METHOD)
        camp, _ = c.freeze_method_output(camp, exposure, output_sha256=out)
        camp = c.record_exposure_terminal(camp, exposure, terminal_status="EVALUATED")
    camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"hidden-fixture")
    return camp, sealed, rows


def test_replaying_preexisting_rows_is_not_deterministic_regeneration_evidence():
    """A caller must not obtain REGENERATION_VERIFIED by echoing already-known sealed rows.

    Verification needs provenance that the frozen generator/code/policy/RNG contract
    actually regenerated the realization set after reveal. Equality to caller-supplied
    rows alone cannot distinguish regeneration from copying the original inventory.
    """
    camp, sealed, original_rows = _revealed_campaign()
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(camp, sealed, original_rows)


def _regenerable_fixture():
    deps = _deps()
    deps.update(c.development_fixture_generator_identities())
    camp = c.create_campaign("regen-valid-fixture", deps, barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=b"hidden-fixture")
    rows = c.generate_development_fixture_rows(camp, definition, hidden_spec=b"hidden-fixture")
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    for rid, out in zip(sealed.realization_ids, ("c" * 64, "d" * 64)):
        camp, exposure = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=METHOD)
        camp, _ = c.freeze_method_output(camp, exposure, output_sha256=out)
        camp = c.record_exposure_terminal(camp, exposure, terminal_status="EVALUATED")
    camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"hidden-fixture")
    return camp, definition, sealed, rows


def test_real_fixture_generator_execution_is_required():
    camp, definition, sealed, _ = _regenerable_fixture()
    camp, receipt = c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=b"hidden-fixture")
    assert camp.state is c.CampaignState.REGENERATION_VERIFIED
    assert receipt.verified is True
    assert receipt.authority_effect == "NONE"
    assert receipt.generator_code_sha == camp.dependencies["challenge_generator_code_sha"]
    camp, custody, evidence = c.finalize_custody(camp, sealed)
    assert camp.state is c.CampaignState.CUSTODY_COMPLETE
    assert custody["promotion_authority"] == "NONE"
    assert evidence["authority_effect"] == "NONE"


def test_deep_copy_even_with_identical_root_cannot_satisfy_regeneration():
    camp, definition, sealed, rows = _regenerable_fixture()
    copied = [dict(row) for row in rows]
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(camp, sealed, copied, definition=definition, hidden_spec=b"hidden-fixture")


def test_caller_supplied_generator_or_receipt_cannot_mint_provenance():
    camp, definition, sealed, rows = _regenerable_fixture()
    class FakeGenerator:
        def __call__(self, *args, **kwargs):
            return [dict(row) for row in rows]
    with pytest.raises((c.Task4ChallengeCustodyError, TypeError)):
        c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=b"hidden-fixture", generator=FakeGenerator())
    with pytest.raises((c.Task4ChallengeCustodyError, TypeError)):
        c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=b"hidden-fixture", receipt={"verified": True})


@pytest.mark.parametrize("field", [
    "challenge_generator_code_sha",
    "challenge_generator_policy_sha",
    "rng_policy_sha",
])
def test_regeneration_rejects_mismatched_generator_identity(field):
    deps = _deps()
    deps.update(c.development_fixture_generator_identities())
    deps[field] = "9" * (40 if field.endswith("code_sha") else 64)
    camp = c.create_campaign("bad-generator-" + field, deps, barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=b"hidden-fixture")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.generate_development_fixture_rows(camp, definition, hidden_spec=b"hidden-fixture")


def test_regeneration_before_reveal_refused():
    deps = _deps()
    deps.update(c.development_fixture_generator_identities())
    camp = c.create_campaign("before-reveal", deps, barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=b"hidden-fixture")
    rows = c.generate_development_fixture_rows(camp, definition, hidden_spec=b"hidden-fixture")
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=b"hidden-fixture")


def test_wrong_hidden_spec_or_sealed_definition_is_refused():
    camp, definition, sealed, _ = _regenerable_fixture()
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=b"substituted")
    from dataclasses import replace
    changed = replace(definition, family="swapped")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(camp, sealed, definition=changed, hidden_spec=b"hidden-fixture")


def test_stale_regeneration_cannot_repeat_or_advance_copied_campaign():
    camp, definition, sealed, rows = _regenerable_fixture()
    from dataclasses import replace
    forged = replace(camp, state=c.CampaignState.REGENERATION_VERIFIED)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.finalize_custody(forged, sealed)
    camp, receipt = c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=b"hidden-fixture")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=b"hidden-fixture")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(camp, sealed, rows)


def test_final_namespace_cannot_use_synthetic_development_generator():
    # FINAL requires independent custody/authority, never a synthetic in-process fixture.
    deps = _deps()
    deps.update(c.development_fixture_generator_identities())
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("no-final-shortcut", deps, barrier_status=None, namespace="FINAL")
