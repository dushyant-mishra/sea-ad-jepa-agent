"""Independent hostile test of duplicate campaign minting and exposure reset.

Pinned baseline: successor-5 36e3b46f1ca44465864a11872b459b5d108d6a67.
Tests only; no changes to candidate or frozen Task 0–3.
"""
from __future__ import annotations

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c


def _deps():
    x = {
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
    x.update(c.development_fixture_generator_identities())
    return x


def test_same_campaign_identity_cannot_remint_budget_after_spending_exposure():
    """Minting the same campaign twice must not reset its already-spent exam."""
    deps = _deps()
    first = c.create_campaign(
        "same-ledger-no-reset", deps, barrier_status=None, namespace="DEVELOPMENT"
    )
    first, definition = c.seal_definition(
        first, family="fixture", hidden_spec=b"hidden-fixture"
    )
    rows = c.generate_development_fixture_rows(
        first, definition, hidden_spec=b"hidden-fixture"
    )
    first, sealed = c.seal_realization_set(
        first, definition, rows, budget=deps["qualification_budget"]
    )
    first, exposure = c.issue_exposure(
        first,
        sealed,
        realization_id=sealed.realization_ids[0],
        method_scientific_identity="a" * 64,
    )
    assert first.exposures_consumed == 1
    assert exposure.ordinal == 1

    # Reusing exact campaign ID, dependencies, and genesis ledger currently
    # allocates another process-local token with zero exposures. That would
    # make the same committed exam available for another independent spend.
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign(
            "same-ledger-no-reset", deps, barrier_status=None, namespace="DEVELOPMENT"
        )
