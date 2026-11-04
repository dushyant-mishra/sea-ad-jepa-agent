"""Hostile independent test: source-text identity is not executable dependency identity.

Review-only test against exact successor-5 repair head e60689c5.
No production changes, no Task 0-3 changes, no authority claims.
"""
from __future__ import annotations

from types import FunctionType
import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c


def test_copied_generator_code_with_rebound_hash_implementation_is_not_trusted(monkeypatch):
    """A copied code object with attacker globals must not mint fresh generation proof."""
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
    deps.update(c.development_fixture_generator_identities())
    campaign = c.create_campaign(
        "hostile-global-swap", deps, barrier_status=None, namespace="DEVELOPMENT"
    )
    campaign, definition = c.seal_definition(
        campaign, family="fixture", hidden_spec=b"hidden-fixture"
    )
    original_rows = c.generate_development_fixture_rows(
        campaign, definition, hidden_spec=b"hidden-fixture"
    )
    campaign, sealed = c.seal_realization_set(
        campaign, definition, original_rows, budget=2
    )
    for rid, output in zip(sealed.realization_ids, ("c" * 64, "d" * 64)):
        campaign, exposure = c.issue_exposure(
            campaign, sealed, realization_id=rid, method_scientific_identity="1" * 64
        )
        campaign, _ = c.freeze_method_output(
            campaign, exposure, output_sha256=output
        )
        campaign = c.record_exposure_terminal(
            campaign, exposure, terminal_status="EVALUATED"
        )
    campaign, _ = c.reveal_hidden_material(
        campaign, definition, sealed, hidden_spec=b"hidden-fixture"
    )

    # The same exact Python code object/source can execute against a different
    # global namespace. The identity check hashes inspect.getsource(function)
    # but does not bind the helpers actually invoked by that code object.
    genuine = c._development_fixture_generator
    alternate_globals = dict(genuine.__globals__)
    genuine_sha = alternate_globals["_sha"]

    def replay_sha(payload):
        if "ordinal" in payload and "generator_policy_sha" in payload:
            return original_rows[payload["ordinal"]]["content_sha256"]
        return genuine_sha(payload)

    alternate_globals["_sha"] = replay_sha
    swapped = FunctionType(
        genuine.__code__, alternate_globals, name=genuine.__name__
    )
    monkeypatch.setattr(c, "_development_fixture_generator", swapped)

    # The generator code digest is unchanged even though its helper and
    # execution dependencies have been replaced. Require fail-closed.
    assert c.development_fixture_generator_identities() == {
        key: deps[key] for key in c.development_fixture_generator_identities()
    }
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.verify_regeneration(
            campaign, sealed, definition=definition, hidden_spec=b"hidden-fixture"
        )
