"""RED: authentic issued custody objects mutated after issuance (sibling routes).

Extends the independent PR #429 RED (mutated ExposureRecord) to every other
issued object. `object.__setattr__` defeats frozen dataclasses, and a mutable
mapping can be edited in place, so the module must keep private snapshots and
refuse any issued handle whose contents no longer match them.
"""
from __future__ import annotations

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c

HIDDEN = b"hidden"
M1 = "1" * 64


def deps():
    d = dict(task2_manifest_sha="1" * 64, task3_registry_sha="2" * 64,
             registry_unit_identities=(("G8", "3" * 64),),
             producer_actor_identity="4" * 64, executor_actor_identity="5" * 64,
             controller_actor_identity="6" * 64, adjudicator_actor_identity="7" * 64,
             realization_schema_sha="a" * 64, challenge_family_sha="c" * 64,
             adjudication_contract_sha="d" * 64, multiplicity_policy_sha="e" * 64,
             publication_policy_sha="f" * 64, genesis_ledger_identity="0" * 64,
             authority_scope="UNIT:G8", authority_restrictions=("NO_TRAINING_AUTHORITY",),
             qualification_budget=2)
    d.update(c.development_fixture_generator_identities())
    return d


class EqAnyStr(str):
    __hash__ = str.__hash__

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


def sealed(cid):
    a = c.create_campaign(cid, deps(), barrier_status=None, namespace="DEVELOPMENT")
    a, d = c.seal_definition(a, family="fixture", hidden_spec=HIDDEN)
    rows = c.generate_development_fixture_rows(a, d, hidden_spec=HIDDEN)
    a, s = c.seal_realization_set(a, d, rows, budget=2)
    return a, d, s


def all_frozen(cid):
    a, d, s = sealed(cid)
    for rid in ("r0", "r1"):
        a, e = c.issue_exposure(a, s, realization_id=rid, method_scientific_identity=M1)
        a, _ = c.freeze_method_output(a, e, output_sha256=("a" if rid == "r0" else "b") * 64)
        a = c.record_exposure_terminal(a, e, terminal_status="EVALUATED")
    return a, d, s


def test_mutated_issued_definition_commitment_cannot_reveal_uncommitted_spec():
    a, d, s = all_frozen("mut-definition")
    object.__setattr__(d, "hidden_spec_commitment", EqAnyStr(d.hidden_spec_commitment))
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(a, d, s, hidden_spec=b"a-different-hidden-spec")


def test_mutated_issued_sealed_set_cannot_expose_uncommitted_world():
    a, d, s = sealed("mut-sealed")
    object.__setattr__(s, "realization_ids", ("r0", "r9"))
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(a, s, realization_id="r9", method_scientific_identity=M1)


def test_mutated_issued_campaign_terminal_accounting_cannot_reveal():
    a, d, s = sealed("mut-terminal")
    a, e = c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)
    a, _ = c.freeze_method_output(a, e, output_sha256="a" * 64)
    a = c.record_exposure_terminal(a, e, terminal_status="EVALUATED")
    a, e1 = c.issue_exposure(a, s, realization_id="r1", method_scientific_identity=M1)
    a, _ = c.freeze_method_output(a, e1, output_sha256="b" * 64)
    # r1 terminal accounting never recorded; forge it into the authentic handle
    object.__setattr__(a, "terminal_statuses", (("r0", "EVALUATED"), ("r1", "EVALUATED")))
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(a, d, s, hidden_spec=HIDDEN)


def test_eq_anything_value_swapped_into_issued_campaign_is_refused_even_if_json_identical():
    a, d, s = sealed("mut-eqany-campaign")
    a, e = c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)
    object.__setattr__(a, "exposed_realization_ids", (EqAnyStr("r0"),))
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.freeze_method_output(a, e, output_sha256="a" * 64)


def test_in_place_edit_of_issued_campaign_dependencies_is_refused():
    a = c.create_campaign("mut-deps", deps(), barrier_status=None, namespace="DEVELOPMENT")
    a, d = c.seal_definition(a, family="fixture", hidden_spec=HIDDEN)
    a.dependencies["qualification_budget"] = 1
    with pytest.raises(c.Task4ChallengeCustodyError):
        rows = c.generate_development_fixture_rows(a, d, hidden_spec=HIDDEN)
        c.seal_realization_set(a, d, rows, budget=1)


def test_unmutated_handles_still_complete_custody():
    a, d, s = all_frozen("mut-lawful")
    a, _ = c.reveal_hidden_material(a, d, s, hidden_spec=HIDDEN)
    a, _ = c.verify_regeneration(a, s, definition=d, hidden_spec=HIDDEN)
    done, receipt, _ = c.finalize_custody(a, s)
    assert done.state is c.CampaignState.CUSTODY_COMPLETE and receipt["exposures_consumed"] == 2
