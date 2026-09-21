"""Tests for the Phase-IV execution-rule addendum.

The addendum exists because the original sample freeze bound *what is sampled*
but not *how the result will be decided*. The central test here is the one the
original freeze lacked: a **mutation test** proving the decision rule is actually
covered by a digest.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "analysis/v5_full104_information_channel_redteam_20260920"
MOD = LANE / "scripts/freeze_audit_b_execution_rule_addendum_20260921.py"
ADDENDUM = LANE / "evidence/phase_iv/AUDIT_B_EXECUTION_RULE_ADDENDUM.json"
SAMPLE = LANE / "evidence/phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json"

_spec = importlib.util.spec_from_file_location("addendum_b", MOD)
A = importlib.util.module_from_spec(_spec)
sys.modules["addendum_b"] = A
_spec.loader.exec_module(A)


@pytest.fixture(scope="module")
def addendum() -> dict:
    if not ADDENDUM.is_file():
        pytest.fail(f"{ADDENDUM} missing; the execution rule is unbound and N1 must not run.")
    return json.loads(ADDENDUM.read_text(encoding="utf-8"))


def _rule_digest(rule: dict, sources: dict) -> str:
    return hashlib.sha256(A.canonical(
        {"schema": A.SCHEMA, "rule": rule, "rule_sources": sources})).hexdigest()


# --------------------------------------------------------------------------- #
# The test the original freeze did not have
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("label,path,new", [
    ("escalation threshold", ("max_relative_standard_error",), 0.50),
    ("zero-mean rule", ("zero_mean_rule",), "treat as pass"),
    ("primary quantity", ("primary_quantity",), "whatever is convenient"),
    ("aggregation", ("aggregation",), "pooled over everything"),
    ("terminal outcome at N3", ("terminal_outcome_if_unmet_at_N3",), "PROCEED_ANYWAY"),
    ("B3 escalation permission", ("b3_may_drive_escalation",), True),
    ("training boundary", ("boundaries", "training_authorized"), True),
    ("terminal-outcome boundary", ("boundaries", "terminal_masking_outcomes_inspected"), True),
    ("dispute status", ("interpretation_dispute", "status"), "SETTLED"),
])
def test_every_decision_element_is_covered_by_the_rule_digest(addendum, label, path, new):
    """Mutating any decision element MUST move the digest.

    The original sample freeze failed exactly this: its digest covered schema,
    salt, ladder, bound hashes and target lists, so the 0.05 threshold, the
    statistic definition, the execution requirements and even
    training_authorized could all be edited without moving it.
    """
    mutated = copy.deepcopy(addendum["rule"])
    node = mutated
    for key in path[:-1]:
        node = node[key]
    assert node[path[-1]] != new, f"{label}: fixture does not actually change the value"
    node[path[-1]] = new
    assert _rule_digest(mutated, addendum["rule_sources"]) != addendum["rule_digest"], (
        f"{label} can be changed without moving rule_digest; the decision rule is "
        "not frozen")


def test_execution_requirements_are_covered(addendum):
    mutated = copy.deepcopy(addendum["rule"])
    mutated["execution_requirements"] = []
    assert _rule_digest(mutated, addendum["rule_sources"]) != addendum["rule_digest"]


def test_rule_digest_reproduces(addendum):
    assert _rule_digest(addendum["rule"], addendum["rule_sources"]) == addendum["rule_digest"]


def test_execution_contract_digest_binds_sample_and_rule(addendum):
    expected = hashlib.sha256(A.canonical({
        "schema": A.SCHEMA,
        "sample_freeze_digest": addendum["sample_freeze_digest"],
        "rule_digest": addendum["rule_digest"],
    })).hexdigest()
    assert addendum["execution_contract_digest"] == expected
    # And it moves if either half moves.
    other = hashlib.sha256(A.canonical({
        "schema": A.SCHEMA, "sample_freeze_digest": "0" * 64,
        "rule_digest": addendum["rule_digest"]})).hexdigest()
    assert other != addendum["execution_contract_digest"]


# --------------------------------------------------------------------------- #
# The addendum must not disturb the original freeze
# --------------------------------------------------------------------------- #

def test_original_sample_freeze_is_unmodified(addendum):
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert sample["freeze_digest"] == A.EXPECTED_FREEZE_DIGEST
    assert addendum["sample_freeze_digest"] == A.EXPECTED_FREEZE_DIGEST
    assert addendum["original_sample_freeze_unmodified"] is True


def test_rule_source_hashes_match_the_repository(addendum):
    drifted = [role for role, rec in addendum["rule_sources"].items()
               if A.sha256_file(ROOT / rec["path"]) != rec["sha256"]]
    assert not drifted, (
        f"rule sources changed since the addendum: {drifted}. The rule must be "
        "re-bound and the change explained rather than silently reused.")


# --------------------------------------------------------------------------- #
# Ratification gate
# --------------------------------------------------------------------------- #

def test_addendum_is_not_self_ratified(addendum):
    """Binding a mechanism is a defect repair; ratifying a scientific choice is not."""
    assert addendum["ratified"] is False
    assert addendum["rule"]["interpretation_dispute"]["status"] == \
        "REQUIRES_EXPLICIT_RATIFICATION_BEFORE_N1"
    assert "refuse to run while ratified is false" in addendum["execution_gate"]


def test_interpretation_dispute_states_why_it_is_a_new_choice(addendum):
    d = addendum["rule"]["interpretation_dispute"]
    assert d["id"] == "RSE_SCOPE__18_CELL_CONJUNCTION_VS_SINGLE_AGGREGATE"
    assert "singular" in d["why_ambiguous"]
    reasons = " ".join(d["why_this_is_a_new_scientific_choice"]).lower()
    assert "stricter" in reasons
    assert "nowhere in the frozen text" in reasons
    assert "near-zero" in reasons
    # The dispute must not smuggle in an outcome prediction.
    assert "REDUCED_POOL_DIAGNOSTIC" in d["not_predicted_here"]


def test_boundaries_remain_closed(addendum):
    b = addendum["rule"]["boundaries"]
    assert b["training_authorized"] is False
    assert b["terminal_masking_outcomes_inspected"] is False
    assert b["p4_adopted"] is False
    assert b["p1_p2_p3_p4_selected"] is None
    assert b["g5_margin_selected"] is None
    assert b["terminal_target_panel_selected"] is None
    assert b["d_shared_opened"] is False
    assert b["pathology_opened"] is False
    assert addendum["training_authorized"] is False


def test_b3_cannot_drive_escalation(addendum):
    assert addendum["rule"]["b3_may_drive_escalation"] is False
    assert "DESCRIPTIVE_ONLY" in addendum["rule"]["secondary_metric_id"]


def test_rule_matches_the_estimator_constants(addendum):
    """The bound rule must not drift from the code that implements it."""
    import sea_ad_jepa.v5.audit_b_production_burden_v1 as E
    r = addendum["rule"]
    assert r["max_relative_standard_error"] == E.MAX_RELATIVE_STANDARD_ERROR
    assert r["primary_metric_id"] == E.PRIMARY_METRIC_ID
    assert r["secondary_metric_id"] == E.SECONDARY_METRIC_ID
    assert r["normalization_id"] == E.NORMALIZATION_ID
    assert tuple(r["nonuniform_policies"]) == E.NONUNIFORM_POLICIES
    assert [f"{x.numerator}/{x.denominator}" for x in E.BURDEN_RUNGS] == r["burden_rungs"]
