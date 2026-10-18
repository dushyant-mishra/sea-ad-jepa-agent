"""Macha T4-B1R hostile RED: forged nested values inside exact-type custody objects.

Pinned against rejected candidate 64535753. Every attack passes ordinary Python
values to public functions; none mutates module-private registries.
"""
from __future__ import annotations

from dataclasses import fields
import hashlib

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c

HIDDEN = b"hidden"
M1 = "1" * 64


def deps(**over):
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
    d.update(over)
    return d


def sealed(cid):
    a = c.create_campaign(cid, deps(), barrier_status=None, namespace="DEVELOPMENT")
    a, d = c.seal_definition(a, family="fixture", hidden_spec=HIDDEN)
    rows = c.generate_development_fixture_rows(a, d, hidden_spec=HIDDEN)
    a, s = c.seal_realization_set(a, d, rows, budget=2)
    return a, d, s


def expose(a, s, rid):
    a, e = c.issue_exposure(a, s, realization_id=rid, method_scientific_identity=M1)
    a, _ = c.freeze_method_output(a, e, output_sha256=hashlib.sha256(rid.encode()).hexdigest())
    return c.record_exposure_terminal(a, e, terminal_status="EVALUATED")


class EqAnyStr(str):
    """Canonical bytes are its own value, but it compares equal to anything."""
    __hash__ = str.__hash__

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


class BudgetShrinkDeps(dict):
    """dict()/JSON copy the stored values; subscripting reports budget 1."""
    def __getitem__(self, key):
        return 1 if key == "qualification_budget" else dict.__getitem__(self, key)


class ShowDistinctDeps(dict):
    """Subscripting shows a distinct controller; dict() stores controller == producer."""
    def __getitem__(self, key):
        return "6" * 64 if key == "controller_actor_identity" else dict.__getitem__(self, key)


def test_N6_dict_subclass_dependencies_cannot_shrink_finite_exam():
    lawful = c.create_campaign("b1r-n6", deps(), barrier_status=None, namespace="DEVELOPMENT")
    lawful, d = c.seal_definition(lawful, family="fixture", hidden_spec=HIDDEN)
    kw = {f.name: getattr(lawful, f.name) for f in fields(lawful)}
    kw["dependencies"] = BudgetShrinkDeps(lawful.dependencies)
    forged = c.QualificationCampaign(**kw)
    with pytest.raises(c.Task4ChallengeCustodyError):
        rows = c.generate_development_fixture_rows(forged, d, hidden_spec=HIDDEN)
        c.seal_realization_set(forged, d, rows, budget=1)


def test_N3_exact_exposure_with_eq_anything_realization_id_cannot_freeze_unexposed_world():
    a, d, s = sealed("b1r-n3")
    a, e0 = c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)
    ghost = c.ExposureRecord(e0.campaign_identity, e0.exposure_id, EqAnyStr("r1"),
                             e0.realization_content_sha256, M1, e0.ordinal)
    a, _ = c.freeze_method_output(a, e0, output_sha256="a" * 64)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.freeze_method_output(a, ghost, output_sha256="b" * 64)


def test_N4_exact_definition_with_ne_nothing_commitment_cannot_reveal_uncommitted_spec():
    a, d, s = sealed("b1r-n4")
    a = expose(a, s, "r0")
    a = expose(a, s, "r1")
    ghost = c.SealedChallengeDefinition(d.campaign_identity, d.family, EqAnyStr(d.hidden_spec_commitment), d.namespace)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(a, ghost, s, hidden_spec=b"a-different-hidden-spec")


def test_N7_eq_anything_realization_id_argument_cannot_misbind_exposure_content():
    a, d, s = sealed("b1r-n7")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(a, s, realization_id=EqAnyStr("r1"), method_scientific_identity=M1)


def test_N8_dependency_validation_cannot_differ_from_stored_dependencies():
    raw = deps(controller_actor_identity="4" * 64)  # controller == producer
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("b1r-n8", ShowDistinctDeps(raw), barrier_status=None, namespace="DEVELOPMENT")


def test_N9_eq_anything_terminal_status_cannot_rewrite_terminal_accounting():
    a, d, s = sealed("b1r-n9")
    a, e0 = c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)
    a = c.record_exposure_terminal(a, e0, terminal_status="TECHNICAL_FAILURE")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.record_exposure_terminal(a, e0, terminal_status=EqAnyStr("EVALUATED"))


def test_value_equal_copy_of_issued_objects_is_not_the_issued_handle():
    a, d, s = sealed("b1r-copy")
    s_copy = c.SealedRealizationSet(**{f.name: getattr(s, f.name) for f in fields(s)})
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.issue_exposure(a, s_copy, realization_id="r0", method_scientific_identity=M1)


def test_lawful_chain_still_completes_custody():
    a, d, s = sealed("b1r-lawful")
    a = expose(a, s, "r0")
    a = expose(a, s, "r1")
    a, _ = c.reveal_hidden_material(a, d, s, hidden_spec=HIDDEN)
    a, _ = c.verify_regeneration(a, s, definition=d, hidden_spec=HIDDEN)
    done, receipt, _ = c.finalize_custody(a, s)
    assert done.state is c.CampaignState.CUSTODY_COMPLETE and receipt["exposures_consumed"] == 2
