"""Tests for the Phase III proposed non-estimability evidence contract.

The contract exists to stop an undefined score term becoming a perfect zero. So
the tests are organised around the ways that could still happen:

* a state could be lost at construction;
* a state could be lost crossing a serialization boundary;
* a state could be lost in resampling;
* an aggregate could quietly supply a default policy;
* two scientifically different failures could be collapsed into one.

Each is covered by a test that fails if the collapse occurs.

The policy-comparison tests deliberately assert only *that the policies differ
and are all reported*, never that a particular one is right. Selecting a policy
is out of scope for Phase III and must not be done by observing outcomes.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / ("analysis/v5_full104_information_channel_redteam_20260920/scripts/"
              "score_term_evidence_contract_v1.py")
_spec = importlib.util.spec_from_file_location("score_term_contract", MOD)
C = importlib.util.module_from_spec(_spec)
# Register before exec: @dataclass resolves annotations through sys.modules, and a
# dynamically loaded module that is absent from it fails on `float | None`.
sys.modules["score_term_contract"] = C
_spec.loader.exec_module(C)


def _mixed() -> "C.ScoreTerms":
    """Two groups; group 0 fully estimable, group 1 carrying each failure mode."""
    return C.ScoreTerms.from_scorer_components(
        cov=[0.5, 0.4, 0.3, 0.9, 0.2, 0.1],
        rss_y=[1.0, 1.0, 1.0, 0.0, 1.0, 1.0],      # index 3: target non-variable
        pred_ss=[1.0, 1.0, 1.0, 1.0, 0.0, 1.0],    # index 4: prediction non-variable
        group=[0, 0, 0, 1, 1, 1],
        present=[True, True, True, True, True, False],   # index 5: missing
    )


# --------------------------------------------------------------------------- #
# Construction: the defect must not recur at the boundary where it lives
# --------------------------------------------------------------------------- #

def test_undefined_target_term_is_not_turned_into_zero():
    """The whole point. rss_y == 0 must produce a STATE, never the value 0.0."""
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.7], rss_y=[0.0], pred_ss=[1.0], group=[0])
    assert t.states[0] == C.TARGET_NON_VARIABLE
    assert not np.isfinite(t.values[0]), (
        "an undefined term carries a finite value; it can still be summed as if measured")
    assert t.values[0] != 0.0


def test_target_and_prediction_failures_are_kept_distinct():
    """Collapsing them would hide which question could not be answered."""
    t = _mixed()
    assert t.states[3] == C.TARGET_NON_VARIABLE
    assert t.states[4] == C.PREDICTION_NON_VARIABLE
    assert t.states[3] != t.states[4]


def test_missing_donor_is_distinct_from_non_variable():
    t = _mixed()
    assert t.states[5] == C.MISSING
    assert t.states[5] not in (C.TARGET_NON_VARIABLE, C.PREDICTION_NON_VARIABLE)


def test_estimable_terms_may_not_carry_non_finite_values():
    with pytest.raises(ValueError, match="non-finite"):
        C.ScoreTerms(values=np.array([np.nan]), states=np.array([C.ESTIMABLE], np.int8),
                     group=np.array([0]))


def test_all_estimable_case_needs_no_policy():
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.5, 0.25], rss_y=[1.0, 1.0], pred_ss=[1.0, 1.0], group=[0, 0])
    agg = C.aggregate(t)
    assert agg.value == pytest.approx(np.mean([0.25, 0.0625]))
    assert agg.excluded is False
    assert agg.terms_estimable == 2


# --------------------------------------------------------------------------- #
# Fail-closed aggregation
# --------------------------------------------------------------------------- #

def test_aggregate_refuses_without_an_explicit_policy():
    """There is no default. A different silent default would be no improvement."""
    with pytest.raises(C.NonEstimableError) as exc:
        C.aggregate(_mixed())
    assert "non-estimable" in str(exc.value)
    assert "P1_PROSPECTIVE_ELIGIBILITY" in str(exc.value)


def test_unknown_policy_is_rejected():
    with pytest.raises(ValueError, match="unknown policy"):
        C.aggregate(_mixed(), policy="WHATEVER_MAKES_IT_PASS")


def test_p1_excludes_the_unit_and_says_so_rather_than_scoring_it():
    agg = C.aggregate(_mixed(), policy="P1_PROSPECTIVE_ELIGIBILITY")
    assert agg.value is None
    assert agg.excluded is True
    assert "excluded" in agg.note


def test_p2_and_p3_report_conditionality_not_just_a_number():
    for policy in ("P2_ABSTAIN_AND_REWEIGHT", "P3_REPORT_CONDITIONALITY"):
        agg = C.aggregate(_mixed(), policy=policy)
        d = agg.as_dict()
        assert d["value"] is not None
        assert d["terms_total"] == 6
        assert d["terms_estimable"] == 3
        assert d["estimable_fraction"] == pytest.approx(0.5)
        assert d["state_counts"]["TARGET_NON_VARIABLE"] == 1
        assert d["state_counts"]["PREDICTION_NON_VARIABLE"] == 1
        assert d["state_counts"]["MISSING"] == 1


def test_the_defect_would_have_produced_a_strictly_better_score():
    """Quantify what the current collapse buys, on this fixture.

    Under the frozen scorer the three non-estimable terms become r = 0, so group 1
    contributes a mean of zero -- the best attainable. Under any policy that
    excludes them, group 1 is scored only on its estimable term. The contract must
    make that difference visible rather than absorbing it.
    """
    t = _mixed()
    honest = C.aggregate(t, policy="P2_ABSTAIN_AND_REWEIGHT").value

    # Emulate the current collapse: undefined -> 0.0, treated as measured.
    collapsed_values = np.where(t.estimable, np.nan_to_num(t.values), 0.0)
    per_group = [float(np.mean(collapsed_values[t.group == g] ** 2))
                 for g in np.unique(t.group)]
    collapsed = float(np.mean(per_group))

    assert collapsed < honest, (
        "on this fixture the collapse should look cleaner than the honest aggregate; "
        f"collapsed={collapsed:.6f} honest={honest:.6f}")


# --------------------------------------------------------------------------- #
# The states must survive every boundary
# --------------------------------------------------------------------------- #

def test_states_survive_json_round_trip():
    t = _mixed()
    back = C.ScoreTerms.from_json(t.to_json())
    assert np.array_equal(back.states, t.states)
    assert np.array_equal(back.group, t.group)
    assert np.array_equal(np.isfinite(back.values), np.isfinite(t.values))
    np.testing.assert_allclose(back.values[back.estimable], t.values[t.estimable])


def test_states_survive_npz_round_trip(tmp_path: Path):
    t = _mixed()
    p = tmp_path / "terms.npz"
    t.to_npz(p)
    back = C.ScoreTerms.from_npz(p)
    assert np.array_equal(back.states, t.states)
    assert back.counts() == t.counts()


def test_json_round_trip_does_not_smuggle_zeros():
    """A non-estimable term must not deserialize as 0.0."""
    t = _mixed()
    payload = json.loads(t.to_json())
    for i, state in enumerate(payload["states"]):
        if state != "ESTIMABLE":
            assert payload["values"][i] is None, (
                f"term {i} in state {state} serialized as {payload['values'][i]!r}; "
                "a reader could treat it as a measured value")


def test_foreign_schema_is_rejected():
    with pytest.raises(ValueError, match="schema"):
        C.ScoreTerms.from_json(json.dumps({"schema": "SOMETHING_ELSE",
                                           "values": [], "states": [], "group": []}))


# --------------------------------------------------------------------------- #
# Resampling
# --------------------------------------------------------------------------- #

def test_resampling_carries_states():
    t = _mixed()
    rng = np.random.default_rng(20260921)
    r = C.resample_donors(t, rng=rng)
    assert r.states.size == t.states.size
    assert set(np.unique(r.states)).issubset(set(np.unique(t.states)))
    assert np.array_equal(np.unique(r.group), np.unique(t.group))


def test_resample_of_only_non_estimable_terms_is_non_estimable_not_zero():
    """A bootstrap draw that happens to select only undefined terms must refuse."""
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.3, 0.4], rss_y=[0.0, 0.0], pred_ss=[1.0, 1.0], group=[0, 0])
    rng = np.random.default_rng(7)
    r = C.resample_donors(t, rng=rng)
    with pytest.raises(C.NonEstimableError):
        C.aggregate(r)
    agg = C.aggregate(r, policy="P2_ABSTAIN_AND_REWEIGHT")
    assert agg.value is None, "an all-undefined resample produced a number"
    assert agg.terms_estimable == 0


def test_resampling_preserves_group_sizes():
    t = _mixed()
    r = C.resample_donors(t, rng=np.random.default_rng(3))
    for g in np.unique(t.group):
        assert int((r.group == g).sum()) == int((t.group == g).sum())


# --------------------------------------------------------------------------- #
# Policy comparison selects nothing
# --------------------------------------------------------------------------- #

def test_compare_policies_reports_all_three_and_selects_none():
    out = C.compare_policies(_mixed())
    assert out["policy_selected"] is None
    assert set(out["policies"]) == set(C.POLICIES)
    assert out["no_policy"]["refused"] is True


def test_policies_have_materially_different_consequences():
    """If every policy agreed, the choice would be inconsequential. It is not."""
    out = C.compare_policies(_mixed())
    p1 = out["policies"]["P1_PROSPECTIVE_ELIGIBILITY"]
    p2 = out["policies"]["P2_ABSTAIN_AND_REWEIGHT"]
    p3 = out["policies"]["P3_REPORT_CONDITIONALITY"]
    assert p1["value"] is None and p1["excluded"] is True
    assert p2["value"] is not None
    # P2 and P3 may coincide numerically while licensing different claims; that
    # is the point, so it is asserted rather than treated as redundancy.
    assert p3["value"] == pytest.approx(p2["value"])
    assert p2["note"] != p3["note"]
    assert "CHANGES THE ESTIMAND" in p2["note"]
    assert "estimand unchanged" in p3["note"]
