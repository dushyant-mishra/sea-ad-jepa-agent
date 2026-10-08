"""Adversarial regression tests for three fail-closed edge cases.

Each of these was a real defect in the reference implementation, found by owner
review after the main Phase-III result had been accepted. The main result stands
-- none of these changes any measured number -- but each was a route by which an
undefined quantity could have become an ordinary number in some later run:

A. a REQUIRED group absent entirely while every supplied term is estimable;
B. zero evidence aggregating to an ESTIMABLE NaN;
C. a materially negative sum of squares laundered into NON_VARIABLE.

The tests are written adversarially: they construct the exact input that used to
slip through, not a nearby input that never did. Each also asserts parity with
the integrated contract, so the two implementations cannot silently diverge.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training. No policy is selected as terminal.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / ("analysis/v5_full104_information_channel_redteam_20260920/scripts/"
              "score_term_evidence_contract_v2.py")

_spec = importlib.util.spec_from_file_location("score_term_contract_v2", MOD)
M = importlib.util.module_from_spec(_spec)
sys.modules["score_term_contract_v2"] = M
_spec.loader.exec_module(M)

import sea_ad_jepa.v5.evidence_estimability_contract_v2 as INTEGRATED  # noqa: E402

POLICIES = (M.P1, M.P2, M.P3, M.P4)


def _estimable_terms_missing_a_group():
    """Four estimable terms in groups 0 and 1. Group 2 will be REQUIRED and absent."""
    return M.ScoreTerms.from_scorer_components(
        cov=[0.5, 0.4, 0.6, 0.55], rss_y=[1.0] * 4, pred_ss=[1.0] * 4, group=[0, 0, 1, 1])


# --------------------------------------------------------------------------- #
# A. a required group that is absent entirely
# --------------------------------------------------------------------------- #

def test_absent_required_group_refuses_without_a_policy():
    """has_non_estimable() is False here -- no term ever carried group 2's label.

    That is exactly why this slipped through: the estimable-early-return fired
    before any group check, so a required source that contributed nothing looked
    identical to one that was never required.
    """
    with pytest.raises(M.NonEstimableError):
        M.aggregate(_estimable_terms_missing_a_group(), required_groups=[0, 1, 2])


def test_absent_required_group_never_claims_the_full_estimand():
    """The load-bearing assertion: no policy may report the full estimand."""
    terms = _estimable_terms_missing_a_group()
    for policy in POLICIES:
        out = M.aggregate(terms, policy=policy, required_groups=[0, 1, 2])
        assert out.full_estimand_point_estimated is False, (
            f"{policy} claims the full estimand while required group 2 is absent")
        assert out.group_status["2"] == M.NOT_ESTIMABLE, (
            f"{policy} does not record group 2 as non-estimable; the source was "
            "dropped silently")


def test_absent_required_group_is_refused_by_the_guarded_policies():
    terms = _estimable_terms_missing_a_group()
    assert M.aggregate(terms, policy=M.P1, required_groups=[0, 1, 2]).status == "EXCLUDED"
    p4 = M.aggregate(terms, policy=M.P4, required_groups=[0, 1, 2])
    assert p4.status == M.NOT_ESTIMABLE
    assert p4.conditional_statistic is None


def test_absent_required_group_leaves_the_conditional_policies_conditional():
    """P2/P3 may still report a number -- that is their definition -- but it must
    be labelled conditional and must carry the absent group's coverage."""
    terms = _estimable_terms_missing_a_group()
    for policy in (M.P2, M.P3):
        out = M.aggregate(terms, policy=policy, required_groups=[0, 1, 2])
        assert out.conditional_statistic is not None
        assert out.full_estimand_point_estimated is False
        assert out.group_coverage["2"] == 0.0


def test_declaring_a_group_required_is_what_changes_the_verdict():
    """Same terms, same policy: the ONLY difference is the required_groups claim."""
    terms = _estimable_terms_missing_a_group()
    without = M.aggregate(terms, policy=M.P4, required_groups=[0, 1])
    with_absent = M.aggregate(terms, policy=M.P4, required_groups=[0, 1, 2])
    assert without.status == "ESTIMABLE"
    assert with_absent.status == M.NOT_ESTIMABLE


# --------------------------------------------------------------------------- #
# B. zero evidence
# --------------------------------------------------------------------------- #

def test_empty_score_terms_cannot_be_constructed():
    with pytest.raises(M.ContractViolation):
        M.ScoreTerms(values=np.array([]), states=np.array([], dtype=np.int8),
                     group=np.array([], dtype=np.int64))


def test_empty_scorer_components_cannot_be_classified():
    with pytest.raises(M.ContractViolation):
        M.ScoreTerms.from_scorer_components(cov=[], rss_y=[], pred_ss=[], group=[])


def test_empty_terms_cannot_arrive_through_serialization():
    """Deserialization is a second door into the same state and must also refuse."""
    payload = ('{"schema": "' + M.SCHEMA +
               '", "values": [], "states": [], "group": []}')
    with pytest.raises(M.ContractViolation):
        M.ScoreTerms.from_json(payload)


def test_all_terms_absent_never_aggregates_to_an_estimable_number():
    """Non-empty but zero *usable* evidence: the other half of B."""
    terms = M.ScoreTerms.from_scorer_components(
        cov=[0.0, 0.0], rss_y=[1.0, 1.0], pred_ss=[1.0, 1.0], group=[0, 0],
        present=[False, False])
    with pytest.raises(M.NonEstimableError):
        M.aggregate(terms)
    for policy in POLICIES:
        out = M.aggregate(terms, policy=policy)
        assert out.status in (M.NOT_ESTIMABLE, "EXCLUDED")
        assert out.conditional_statistic is None
        assert out.full_estimand_point_estimated is False


def test_no_aggregate_ever_returns_an_estimable_nan():
    """The invariant B exists to protect, stated directly."""
    terms = _estimable_terms_missing_a_group()
    for required in ([0, 1], [0, 1, 2]):
        for policy in POLICIES:
            out = M.aggregate(terms, policy=policy, required_groups=required)
            if out.status == "ESTIMABLE":
                assert out.conditional_statistic is not None
                assert np.isfinite(out.conditional_statistic), (
                    "an ESTIMABLE aggregate carries NaN")


# --------------------------------------------------------------------------- #
# C. negative sums of squares
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("rss_y,pred_ss,expected", [
    (-1e-15, 1.0, M.TARGET_NON_VARIABLE),
    (1.0, -1e-15, M.PREDICTION_NON_VARIABLE),
    (-1e-13, 1.0, M.TARGET_NON_VARIABLE),
    (-1.0, 1.0, M.INVALID_NUMERIC),
    (1.0, -1.0, M.INVALID_NUMERIC),
    (-1.0, -1.0, M.INVALID_NUMERIC),
    (-1e-6, 1.0, M.INVALID_NUMERIC),
    (-1.1e-12, 1.0, M.INVALID_NUMERIC),
])
def test_negative_sums_of_squares_route_by_magnitude(rss_y, pred_ss, expected):
    """Noise around zero is non-variable; a materially negative SS is arithmetic
    failure and must not be laundered into a legitimate scientific state."""
    terms = M.ScoreTerms.from_scorer_components(
        cov=[0.1], rss_y=[rss_y], pred_ss=[pred_ss], group=[0])
    assert int(terms.states[0]) == expected, (
        f"rss_y={rss_y} pred_ss={pred_ss} classified as "
        f"{M.STATE_NAMES[int(terms.states[0])]}")


def test_invalid_numeric_from_negative_ss_still_carries_no_value():
    """INVALID_NUMERIC is non-estimable, so the bidirectional invariant applies."""
    terms = M.ScoreTerms.from_scorer_components(
        cov=[0.1], rss_y=[-1.0], pred_ss=[1.0], group=[0])
    assert not np.isfinite(terms.values[0])


def test_a_materially_negative_ss_cannot_be_hidden_by_a_good_neighbour():
    """Vectorized routing must be per-term, not decided by the array as a whole."""
    terms = M.ScoreTerms.from_scorer_components(
        cov=[0.1, 0.5, 0.1], rss_y=[1.0, -1.0, 1.0], pred_ss=[1.0, 1.0, 1.0],
        group=[0, 0, 0])
    assert int(terms.states[0]) == M.ESTIMABLE
    assert int(terms.states[1]) == M.INVALID_NUMERIC
    assert int(terms.states[2]) == M.ESTIMABLE


# --------------------------------------------------------------------------- #
# Parity with the integrated contract
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("rss_y,pred_ss", [
    (-1e-15, 1.0), (1.0, -1e-15), (-1.0, 1.0), (1.0, -1.0), (-1.0, -1.0),
    (-1e-6, 1.0), (-1.1e-12, 1.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0),
])
def test_classification_matches_the_integrated_contract(rss_y, pred_ss):
    mine = M.ScoreTerms.from_scorer_components(
        cov=[0.1], rss_y=[rss_y], pred_ss=[pred_ss], group=[0])
    theirs = INTEGRATED.ScoreTermsV2.from_scorer_components(
        cov=[0.1], rss_y=[rss_y], pred_ss=[pred_ss], group=[0])
    assert int(mine.states[0]) == int(theirs.states[0]), (
        f"rss_y={rss_y} pred_ss={pred_ss}: reference "
        f"{M.STATE_NAMES[int(mine.states[0])]} != integrated "
        f"{INTEGRATED._STATUS_NAMES[int(theirs.states[0])]}")


def test_absent_required_group_verdicts_match_the_integrated_contract():
    kw = dict(cov=[0.5, 0.4, 0.6, 0.55], rss_y=[1.0] * 4, pred_ss=[1.0] * 4,
              group=[0, 0, 1, 1])
    mine = M.ScoreTerms.from_scorer_components(**kw)
    theirs = INTEGRATED.ScoreTermsV2.from_scorer_components(**kw)
    with pytest.raises(M.NonEstimableError):
        M.aggregate(mine, required_groups=[0, 1, 2])
    with pytest.raises(INTEGRATED.NonEstimableError):
        INTEGRATED.aggregate(theirs, required_groups=[0, 1, 2])
    for policy in POLICIES:
        a = M.aggregate(mine, policy=policy, required_groups=[0, 1, 2])
        b = INTEGRATED.aggregate(theirs, policy=policy, required_groups=[0, 1, 2])
        assert a.status == b.status, policy
        assert a.full_estimand_point_estimated == b.full_estimand_point_estimated, policy
        assert a.group_status == b.group_status, policy


def test_empty_evidence_is_refused_by_both_implementations():
    with pytest.raises(M.ContractViolation):
        M.ScoreTerms.from_scorer_components(cov=[], rss_y=[], pred_ss=[], group=[])
    with pytest.raises(INTEGRATED.ContractViolation):
        INTEGRATED.ScoreTermsV2.from_scorer_components(
            cov=[], rss_y=[], pred_ss=[], group=[])


def test_no_policy_is_selected_as_terminal():
    """Standing boundary: this file must not encode a terminal P1/P2/P3/P4 choice."""
    terms = _estimable_terms_missing_a_group()
    compared = M.compare_policies(terms, required_groups=[0, 1, 2])
    assert compared.get("policy_selected") is None
