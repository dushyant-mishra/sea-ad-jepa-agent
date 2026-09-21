"""Tests for the V2 non-estimability evidence contract.

Organised around the ways an undefined score term could still become an ordinary
zero. Three of these tests exist because V1 failed them — they are regressions,
not hypotheticals:

* ``test_non_estimable_term_may_not_carry_a_finite_value`` — V1 accepted
  ``ScoreTerms(values=[0.0], states=[TARGET_NON_VARIABLE])`` and serialized it as
  the JSON number ``0.0``;
* ``test_joint_target_and_prediction_failure_is_its_own_state`` — V1 gave target
  precedence and erased the prediction failure;
* ``test_impossible_correlation_is_rejected`` — V1 accepted ``|r| = 1.7``.

The policy tests assert only that the policies differ and are all reported, never
that one is correct. Selecting a terminal policy is out of scope.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import sea_ad_jepa.v5.evidence_estimability_contract_v2 as C


def _mixed() -> "C.ScoreTerms":
    """Group 0 fully estimable; group 1 carries every failure mode and one survivor."""
    return C.ScoreTerms.from_scorer_components(
        cov=[0.5, 0.4, 0.3, 0.9, 0.2, 0.1, 0.8, 0.6],
        rss_y=[1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0],
        pred_ss=[1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0],
        group=[0, 0, 0, 1, 1, 1, 1, 1],
        present=[True, True, True, True, True, False, True, True],
    )


# --------------------------------------------------------------------------- #
# Regressions against the three V1 faults
# --------------------------------------------------------------------------- #

def test_non_estimable_term_may_not_carry_a_finite_value():
    """V1 REGRESSION. The contract's central promise, enforced at construction.

    V1 validated ESTIMABLE => finite but never the inverse, so a term tagged
    TARGET_NON_VARIABLE could hold 0.0 and serialize as a JSON number. The
    direction of an invariant that is forgotten is the direction the defect
    walks back in.
    """
    for state in (C.TARGET_NON_VARIABLE, C.PREDICTION_NON_VARIABLE,
                  C.TARGET_AND_PREDICTION_NON_VARIABLE, C.MISSING, C.INVALID_NUMERIC):
        with pytest.raises(C.ContractViolation, match="finite value"):
            C.ScoreTerms(values=np.array([0.0]),
                         states=np.array([state], np.int8),
                         group=np.array([0]))


def test_joint_target_and_prediction_failure_is_its_own_state():
    """V1 REGRESSION. V1 gave target precedence and erased the prediction failure."""
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.5], rss_y=[0.0], pred_ss=[0.0], group=[0])
    assert t.states[0] == C.TARGET_AND_PREDICTION_NON_VARIABLE
    assert t.states[0] != C.TARGET_NON_VARIABLE
    assert t.states[0] != C.PREDICTION_NON_VARIABLE


def test_impossible_correlation_is_rejected():
    """V1 REGRESSION. |r| > 1 is not imprecision; it means the computation is wrong."""
    with pytest.raises(C.ContractViolation, match=r"\|r\| > 1"):
        C.ScoreTerms(values=np.array([1.7]), states=np.array([C.ESTIMABLE], np.int8),
                     group=np.array([0]))


def test_factory_classifies_impossible_correlation_as_invalid_numeric():
    """cov far exceeding the denominator must become a STATE, not a clipped value."""
    t = C.ScoreTerms.from_scorer_components(
        cov=[10.0], rss_y=[1.0], pred_ss=[1.0], group=[0])
    assert t.states[0] == C.INVALID_NUMERIC
    assert not np.isfinite(t.values[0])


def test_tiny_floating_point_overshoot_is_tolerated_not_rejected():
    """Backward-stable arithmetic may overshoot 1 by a few ulp; that is not a bug."""
    t = C.ScoreTerms(values=np.array([1.0 + 1e-12]),
                     states=np.array([C.ESTIMABLE], np.int8), group=np.array([0]))
    assert t.states[0] == C.ESTIMABLE


# --------------------------------------------------------------------------- #
# Construction
# --------------------------------------------------------------------------- #

def test_undefined_target_term_is_not_turned_into_zero():
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.7], rss_y=[0.0], pred_ss=[1.0], group=[0])
    assert t.states[0] == C.TARGET_NON_VARIABLE
    assert not np.isfinite(t.values[0])
    assert t.values[0] != 0.0


def test_every_failure_mode_is_distinguishable():
    t = _mixed()
    assert t.states[3] == C.TARGET_NON_VARIABLE
    assert t.states[4] == C.PREDICTION_NON_VARIABLE
    assert t.states[5] == C.MISSING
    assert t.states[6] == C.TARGET_AND_PREDICTION_NON_VARIABLE
    assert len({int(x) for x in t.states[3:7]}) == 4


def test_arrays_are_immutable_after_validation():
    t = _mixed()
    with pytest.raises(ValueError):
        t.values[0] = 0.0
    with pytest.raises(ValueError):
        t.states[0] = C.ESTIMABLE


def test_all_estimable_case_needs_no_policy():
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.5, 0.25], rss_y=[1.0, 1.0], pred_ss=[1.0, 1.0], group=[0, 0])
    agg = C.aggregate(t)
    assert agg.status == "ESTIMABLE"
    assert agg.full_estimand_point_estimated is True
    assert agg.conditional_statistic == pytest.approx(np.mean([0.25, 0.0625]))


# --------------------------------------------------------------------------- #
# Fail-closed aggregation and policies
# --------------------------------------------------------------------------- #

def test_aggregate_refuses_without_an_explicit_policy():
    with pytest.raises(C.NonEstimableError) as exc:
        C.aggregate(_mixed())
    assert "non-estimable" in str(exc.value)


def test_unknown_policy_is_rejected():
    with pytest.raises(ValueError, match="unknown policy"):
        C.aggregate(_mixed(), policy="WHATEVER_MAKES_IT_PASS")


def test_no_policy_claims_to_point_estimate_the_full_estimand():
    """The P3 correction: computing on a subset is not estimating the whole."""
    for policy in (C.P1, C.P2, C.P3, C.P4):
        agg = C.aggregate(_mixed(), policy=policy)
        assert agg.full_estimand_point_estimated is False, (
            f"{policy} claims to point-estimate the full intended estimand while "
            "computing on the estimable subset")


def test_p3_reports_conditional_statistic_and_mandatory_coverage():
    agg = C.aggregate(_mixed(), policy=C.P3).as_dict()
    assert agg["conditional_statistic"] is not None
    assert agg["coverage"] == pytest.approx(4 / 8)
    assert agg["quantity_name"] == "conditional predictability among estimable donors"
    assert "NOT point-estimated" in agg["note"]


def test_p4_refuses_when_a_required_group_has_no_estimable_donor():
    """The coverage guard: a vacuous guardrail must never look clean.

    Group 1 here has no estimable donor at all. P4 must return NOT_ESTIMABLE
    rather than a number, and must not silently drop the group.
    """
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.5, 0.4, 0.9, 0.2],
        rss_y=[1.0, 1.0, 0.0, 0.0],
        pred_ss=[1.0, 1.0, 1.0, 1.0],
        group=[0, 0, 1, 1])
    agg = C.aggregate(t, policy=C.P4)
    assert agg.status == C.NOT_ESTIMABLE
    assert agg.conditional_statistic is None, "a vacuous guardrail produced a number"
    assert agg.group_status["1"] == C.NOT_ESTIMABLE
    assert agg.group_coverage["1"] == 0.0

    # P2 by contrast still returns a number from the surviving group -- which is
    # exactly the difference the coverage guard exists to make.
    assert C.aggregate(t, policy=C.P2).conditional_statistic is not None


def test_p4_scores_normally_when_every_required_group_has_coverage():
    agg = C.aggregate(_mixed(), policy=C.P4)
    assert agg.status == "ESTIMABLE"
    assert agg.conditional_statistic is not None
    assert set(agg.group_status.values()) == {"ESTIMABLE"}


def test_p4_preserves_the_universe_rather_than_excluding_units():
    """P1 excludes the unit; P4 keeps it and reports coverage."""
    t = _mixed()
    assert C.aggregate(t, policy=C.P1).status == "EXCLUDED"
    assert C.aggregate(t, policy=C.P4).status == "ESTIMABLE"


def test_the_defect_would_have_produced_a_strictly_better_score():
    """The defect stated as an executable assertion rather than an argument."""
    t = _mixed()
    honest = C.aggregate(t, policy=C.P4).conditional_statistic
    collapsed_values = np.where(t.estimable, np.nan_to_num(t.values), 0.0)
    per_group = [float(np.mean(collapsed_values[t.group == g] ** 2))
                 for g in np.unique(t.group)]
    collapsed = float(np.mean(per_group))
    assert collapsed < honest, f"collapsed={collapsed:.6f} honest={honest:.6f}"


# --------------------------------------------------------------------------- #
# Boundaries
# --------------------------------------------------------------------------- #

def test_states_survive_json_round_trip():
    t = _mixed()
    back = C.ScoreTerms.from_json(t.to_json())
    assert np.array_equal(back.states, t.states)
    assert back.content_digest() == t.content_digest()


def test_states_survive_npz_round_trip(tmp_path: Path):
    t = _mixed()
    p = tmp_path / "terms.npz"
    t.to_npz(p)
    back = C.ScoreTerms.from_npz(p)
    assert back.counts() == t.counts()
    assert back.content_digest() == t.content_digest()


def test_json_round_trip_does_not_smuggle_zeros():
    payload = json.loads(_mixed().to_json())
    for i, state in enumerate(payload["states"]):
        if state != "ESTIMABLE":
            assert payload["values"][i] is None, (
                f"term {i} in state {state} serialized as {payload['values'][i]!r}")


def test_hand_edited_payload_attaching_a_number_to_an_undefined_term_is_rejected():
    """Deserialization is an entry point too, so the invariant runs there as well."""
    payload = json.loads(_mixed().to_json())
    idx = next(i for i, s in enumerate(payload["states"]) if s != "ESTIMABLE")
    payload["values"][idx] = 0.0
    payload.pop("content_digest")          # isolate the invariant from the digest
    with pytest.raises(C.ContractViolation, match="finite value"):
        C.ScoreTerms.from_json(json.dumps(payload))


def test_tampered_content_digest_is_rejected():
    payload = json.loads(_mixed().to_json())
    payload["content_digest"] = "0" * 64
    with pytest.raises(C.ContractViolation, match="digest"):
        C.ScoreTerms.from_json(json.dumps(payload))


def test_digest_changes_when_a_state_changes():
    a = _mixed()
    b = C.ScoreTerms.from_scorer_components(
        cov=[0.5, 0.4, 0.3, 0.9, 0.2, 0.1, 0.8],
        rss_y=[1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0],     # last term now estimable
        pred_ss=[1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0],
        group=[0, 0, 0, 1, 1, 1, 1],
        present=[True, True, True, True, True, False, True])
    assert a.content_digest() != b.content_digest()


def test_foreign_schema_is_rejected():
    with pytest.raises(C.ContractViolation, match="schema"):
        C.ScoreTerms.from_json(json.dumps({"schema": "SOMETHING_ELSE", "values": [],
                                           "states": [], "group": []}))


def test_unknown_state_name_is_rejected():
    with pytest.raises(C.ContractViolation, match="unknown state"):
        C.ScoreTerms.from_json(json.dumps({"schema": C.SCHEMA, "values": [None],
                                           "states": ["NOT_A_STATE"], "group": [0]}))


# --------------------------------------------------------------------------- #
# Resampling
# --------------------------------------------------------------------------- #

def test_resampling_carries_states_and_group_sizes():
    t = _mixed()
    r = C.resample_donors(t, rng=np.random.default_rng(20260921))
    assert set(np.unique(r.states)).issubset(set(np.unique(t.states)))
    for g in np.unique(t.group):
        assert int((r.group == g).sum()) == int((t.group == g).sum())


def test_resample_of_only_non_estimable_terms_is_non_estimable_not_zero():
    t = C.ScoreTerms.from_scorer_components(
        cov=[0.3, 0.4], rss_y=[0.0, 0.0], pred_ss=[1.0, 1.0], group=[0, 0])
    r = C.resample_donors(t, rng=np.random.default_rng(7))
    with pytest.raises(C.NonEstimableError):
        C.aggregate(r)
    for policy in (C.P2, C.P3, C.P4):
        agg = C.aggregate(r, policy=policy)
        assert agg.conditional_statistic is None, f"{policy} scored an all-undefined resample"
        assert agg.terms_estimable == 0


def test_coverage_is_carried_through_resampling():
    t = _mixed()
    r = C.resample_donors(t, rng=np.random.default_rng(11))
    agg = C.aggregate(r, policy=C.P4).as_dict()
    assert agg["coverage"] is not None
    assert 0.0 <= agg["coverage"] <= 1.0


# --------------------------------------------------------------------------- #
# Policy comparison selects nothing
# --------------------------------------------------------------------------- #

def test_compare_policies_reports_all_four_and_selects_none():
    out = C.compare_policies(_mixed())
    assert out["policy_selected"] is None
    assert set(out["policies"]) == set(C.POLICIES)
    assert out["no_policy"]["refused"] is True
    assert out["content_digest"]


def test_policies_have_materially_different_consequences():
    out = C.compare_policies(_mixed())["policies"]
    assert out[C.P1]["status"] == "EXCLUDED"
    assert out[C.P2]["conditional_statistic"] is not None
    assert out[C.P3]["conditional_statistic"] == pytest.approx(
        out[C.P2]["conditional_statistic"])
    assert "CHANGES THE ESTIMAND" in out[C.P2]["note"]
    assert "NOT point-estimated" in out[C.P3]["note"]
    assert out[C.P4]["quantity_name"] == "conditional predictability among estimable donors"
