#!/usr/bin/env python3
"""Adversarial qualification of the V21-T1 selection and power executor.

This suite is what makes `t0_v21_selection_and_power_v1.py` an
implementation-qualified executor rather than a transcription of the design
document. It runs entirely on synthetic fixtures with known ground truth. No
AT8 value is read, no partition is opened, no V20 artifact is touched, and
neither estimator selection nor the power gate is executed against real donors —
both remain unauthorized.

The bar it is written against, item by item:

1. exactly 28 outer leave-one-donor-out predictions, every donor held out once;
2. all ridge selection nested strictly inside each 27-donor training fold;
3. no global hyperparameter leakage;
4. one HC3 regression, only after the 28 predictions are assembled;
5. the frozen nuisance design and the expected degrees of freedom;
6. deterministic S0-S4 admissibility and ranking, using all 28 refits;
7. exact sign-consistency and jackknife power behaviour;
8. explicit failure tests for leakage, donor-order dependence, sign
   inconsistency, inadmissible candidates, and rerun nondeterminism;
9. the standardization of the full 28-donor effect against each 27-donor
   influence refit, matching the frozen equation exactly.

Two of these deserve a word on why they are written the way they are.

A leakage test that only checks an honest pipeline proves nothing: it would pass
against a module that never cross-fitted at all. So the honest pipeline and a
deliberately leaky one are run through the same probe, and the test asserts the
probe separates them. A test that cannot fail is not evidence.

The standardization test does not merely check that the numbers are
self-consistent. It recomputes `t / sqrt(n)` independently for the full fit and
for a single influence refit, and asserts the refit divides by sqrt(27) while
the full fit divides by sqrt(28) -- and additionally that dividing the refit by
sqrt(28) would give a different answer, so the test would notice if the two were
ever conflated.
"""

from __future__ import annotations

import ast
import importlib.util
import math
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_v21_selection_and_power_v1 as v21  # noqa: E402

N = v21.V21_DISCOVERY_DONORS  # 28


# --------------------------------------------------------------------------
# Synthetic cohort and two fold pipelines: one honest, one leaky
# --------------------------------------------------------------------------

def make_cohort(n: int = N, seed: int = 11, effect: float = 1.4):
    rng = np.random.default_rng(seed)
    age = np.linspace(66.0, 94.0, n) + rng.normal(scale=0.7, size=n)
    sex = np.array([float(i % 2) for i in range(n)])
    features = rng.normal(size=(n, 3))
    y = (effect * features[:, 0] + 0.35 * features[:, 1]
         + 0.02 * (age - age.mean()) + rng.normal(scale=0.55, size=n))
    return {"age": age, "sex": sex, "features": features, "y": y}


INNER_GRID = (-4.0, -2.0, 0.0, 2.0, 4.0)


def _ridge_fit(x: np.ndarray, y: np.ndarray, exponent: float) -> np.ndarray:
    """The frozen scaling convention: lambda = 10**exponent * trace(gram)/n."""
    gram = x.T @ x
    scale = float(np.trace(gram) / len(x))
    lam = (10.0 ** float(exponent)) * scale
    return np.linalg.solve(gram + lam * np.eye(x.shape[1]), x.T @ y)


def _inner_loo_loss(x: np.ndarray, y: np.ndarray, exponent: float) -> float:
    """Leave-one-out squared error inside the training fold only."""
    total = 0.0
    for held in range(len(y)):
        keep = np.arange(len(y)) != held
        coef = _ridge_fit(x[keep], y[keep], exponent)
        total += float((y[held] - x[held] @ coef) ** 2)
    return total / len(y)


class FoldModel:
    __slots__ = ("coef", "exponent", "train")

    def __init__(self, coef, exponent, train):
        self.coef = coef
        self.exponent = float(exponent)
        self.train = np.asarray(train)


def honest_pipeline(cohort):
    """Ridge selection and fitting confined to the training donors."""
    x, y = cohort["features"], cohort["y"]

    def train_fold(train_idx):
        xt, yt = x[train_idx], y[train_idx]
        exponent = min(INNER_GRID, key=lambda e: (_inner_loo_loss(xt, yt, e), e))
        return FoldModel(_ridge_fit(xt, yt, exponent), exponent, train_idx)

    def predict(model, held_out):
        return float(x[held_out] @ model.coef)

    return train_fold, predict


def leaky_pipeline(cohort):
    """Fits on the whole cohort, ignoring the fold. The negative control."""
    x, y = cohort["features"], cohort["y"]

    def train_fold(train_idx):
        exponent = min(INNER_GRID, key=lambda e: (_inner_loo_loss(x, y, e), e))
        return FoldModel(_ridge_fit(x, y, exponent), exponent, train_idx)

    def predict(model, held_out):
        return float(x[held_out] @ model.coef)

    return train_fold, predict


def run_oof(cohort, pipeline):
    train_fold, predict = pipeline(cohort)
    return v21.outer_lodo_oof(n_donors=len(cohort["y"]), train_fold=train_fold,
                              predict_held_out=predict,
                              fold_ridge_exponent=lambda m: m.exponent)


# --------------------------------------------------------------------------
# 1. Fold coverage: exactly 28, each donor held out exactly once
# --------------------------------------------------------------------------

def test_exactly_28_folds_each_donor_held_out_once():
    result = run_oof(make_cohort(), honest_pipeline)
    assert result["n_folds"] == 28
    assert result["n_donors"] == 28
    assert result["every_donor_held_out_exactly_once"]
    held = [f["held_out_index"] for f in result["folds"]]
    assert sorted(held) == list(range(28))
    assert len(set(held)) == 28
    assert result["oof_predictions"].shape == (28,)


def test_every_fold_trains_on_exactly_27_donors():
    result = run_oof(make_cohort(), honest_pipeline)
    assert result["fold_train_size"] == 27
    assert all(f["n_train"] == 27 for f in result["folds"])


def test_a_cohort_that_is_not_28_donors_stops():
    cohort = make_cohort(n=27, seed=3)
    train_fold, predict = honest_pipeline(cohort)
    with pytest.raises(RuntimeError) as excinfo:
        v21.outer_lodo_oof(n_donors=27, train_fold=train_fold,
                           predict_held_out=predict)
    assert v21.STOP_FOLD_COVERAGE in str(excinfo.value)


def test_the_fold_callable_never_receives_its_held_out_donor():
    """Structural: the executor cannot itself be the leakage channel."""
    cohort = make_cohort()
    seen: list[tuple[int, set[int]]] = []
    order = {"next": 0}

    def train_fold(train_idx):
        held = order["next"]
        order["next"] += 1
        seen.append((held, set(int(i) for i in train_idx)))
        return FoldModel(np.zeros(3), 0.0, train_idx)

    v21.outer_lodo_oof(n_donors=N, train_fold=train_fold,
                       predict_held_out=lambda m, i: 0.0)
    assert len(seen) == 28
    for held, train in seen:
        assert held not in train
        assert train == set(range(28)) - {held}


# --------------------------------------------------------------------------
# 2 and 3. Nested ridge selection, and no global hyperparameter
# --------------------------------------------------------------------------

def test_ridge_exponent_is_selected_inside_each_fold():
    result = run_oof(make_cohort(), honest_pipeline)
    assert result["ridge_selected_inside_each_fold"]
    assert len(result["fold_ridge_exponents"]) == 28
    assert all(e is not None for e in result["fold_ridge_exponents"])


def test_a_folds_ridge_choice_depends_only_on_its_training_donors():
    """Recomputing a fold's selection from its 27 donors reproduces it."""
    cohort = make_cohort()
    result = run_oof(cohort, honest_pipeline)
    x, y = cohort["features"], cohort["y"]
    for held in (0, 7, 19, 27):
        train = np.array([i for i in range(N) if i != held])
        expected = min(INNER_GRID,
                       key=lambda e: (_inner_loo_loss(x[train], y[train], e), e))
        assert result["fold_ridge_exponents"][held] == pytest.approx(expected)


def test_a_globally_selected_hyperparameter_is_visible_in_the_record():
    """A single exponent shared by every fold is recorded as exactly that."""
    cohort = make_cohort()
    honest = run_oof(cohort, honest_pipeline)
    leaky = run_oof(cohort, leaky_pipeline)
    # The leaky pipeline selects once on the full cohort, so every fold reports
    # the same exponent. The record exposes it rather than hiding it.
    assert len(leaky["distinct_fold_ridge_exponents"]) == 1
    assert leaky["fold_ridge_exponents"].count(
        leaky["fold_ridge_exponents"][0]) == 28
    assert honest["fold_ridge_exponents"] is not None


# --------------------------------------------------------------------------
# The decisive leakage test -- and proof that it can fail
# --------------------------------------------------------------------------

def _own_prediction_moves(pipeline, donor: int = 9) -> tuple[bool, bool]:
    """Perturb one donor's outcome; report whether its own and others' move."""
    base = make_cohort()
    perturbed = make_cohort()
    perturbed["y"] = perturbed["y"].copy()
    perturbed["y"][donor] += 25.0

    before = run_oof(base, pipeline)["oof_predictions"]
    after = run_oof(perturbed, pipeline)["oof_predictions"]
    own_moved = not math.isclose(before[donor], after[donor],
                                 rel_tol=0.0, abs_tol=1e-12)
    others = [i for i in range(len(before)) if i != donor]
    others_moved = any(
        not math.isclose(before[i], after[i], rel_tol=0.0, abs_tol=1e-12)
        for i in others)
    return own_moved, others_moved


def test_leakage_a_donors_own_out_of_fold_prediction_does_not_move():
    own_moved, others_moved = _own_prediction_moves(honest_pipeline)
    assert not own_moved, (
        "donor's own out-of-fold prediction moved when only its own outcome "
        "changed: the fold saw the donor it was supposed to hold out")
    assert others_moved, (
        "no other prediction moved either, so the perturbation did nothing and "
        "the test would have passed vacuously")


def test_the_leakage_probe_detects_a_leaky_pipeline():
    """The negative control. Without this, the test above proves nothing."""
    own_moved, others_moved = _own_prediction_moves(leaky_pipeline)
    assert own_moved, (
        "the leakage probe failed to detect a pipeline that trains on the "
        "whole cohort; it cannot be trusted to detect a subtler leak")
    assert others_moved


# --------------------------------------------------------------------------
# 4 and 5. One HC3 regression after assembly; frozen design and df
# --------------------------------------------------------------------------

def test_one_regression_at_n_28_with_the_expected_degrees_of_freedom():
    cohort = make_cohort()
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    effect = v21.oof_effect(y=cohort["y"], age=cohort["age"],
                            sex=cohort["sex"], oof_scores=scores)
    assert effect["estimable"]
    assert effect["n"] == 28
    assert effect["p_full"] == 5
    assert effect["residual_df"] == 23  # 28 - 5
    assert math.isfinite(effect["beta"])
    assert effect["hc3_se"] > 0.0


def test_the_design_is_the_frozen_nuisance_design_plus_the_score():
    cohort = make_cohort()
    _, learner = v21._frozen()
    z, center = learner.nuisance_design(cohort["age"], cohort["sex"])
    ac = cohort["age"] - center
    assert z.shape == (28, 4)
    assert np.allclose(z[:, 0], 1.0)
    assert np.allclose(z[:, 1], ac)
    assert np.allclose(z[:, 2], ac * ac)
    assert np.allclose(z[:, 3], cohort["sex"])
    assert v21.NUISANCE_RANK == 4
    assert v21.P_FULL == 5


def test_the_effect_reuses_the_frozen_hc3_engine_exactly():
    """Not a reimplementation: the same call must give the same three numbers."""
    cohort = make_cohort()
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    fl, learner = v21._frozen()
    z, _ = learner.nuisance_design(cohort["age"], cohort["sex"])
    beta, se, t = fl.ols_hc3_last(cohort["y"], np.c_[z, scores])
    effect = v21.oof_effect(y=cohort["y"], age=cohort["age"],
                            sex=cohort["sex"], oof_scores=scores)
    assert effect["beta"] == beta
    assert effect["hc3_se"] == se
    assert effect["t_observed"] == t


def test_a_score_aliased_with_the_nuisance_design_is_not_estimable():
    cohort = make_cohort()
    _, learner = v21._frozen()
    z, _ = learner.nuisance_design(cohort["age"], cohort["sex"])
    effect = v21.oof_effect(y=cohort["y"], age=cohort["age"],
                            sex=cohort["sex"], oof_scores=z[:, 3].copy())
    assert not effect["estimable"]


# --------------------------------------------------------------------------
# 9. Standardization: sqrt(28) for the full fit, sqrt(27) for each refit
# --------------------------------------------------------------------------

def test_standardization_divides_by_the_size_of_the_fitting_sample():
    assert v21.standardized_effect(4.2, 28) == pytest.approx(
        4.2 / math.sqrt(28), rel=0, abs=1e-15)
    assert v21.standardized_effect(4.2, 27) == pytest.approx(
        4.2 / math.sqrt(27), rel=0, abs=1e-15)


def test_full_uses_sqrt_28_and_each_influence_refit_uses_sqrt_27():
    cohort = make_cohort()
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    bound = v21.jackknife_minimum_effect(
        y=cohort["y"], age=cohort["age"], sex=cohort["sex"], oof_scores=scores)

    assert bound["full_n"] == 28
    assert bound["full_standardized_effect"] == pytest.approx(
        bound["full_t"] / math.sqrt(28), rel=0, abs=1e-15)

    assert bound["n_influence_refits"] == 28
    assert bound["refit_n"] == 27
    for refit in bound["influence_refits"]:
        assert refit["n"] == 27
        assert refit["standardized_effect"] == pytest.approx(
            refit["t_observed"] / math.sqrt(27), rel=0, abs=1e-15)
        # And the conflation the contract forbids would give another answer,
        # so this assertion is not satisfied by both conventions at once.
        assert refit["standardized_effect"] != pytest.approx(
            refit["t_observed"] / math.sqrt(28), rel=0, abs=1e-12)


def test_a_refit_reproduces_the_frozen_engine_on_its_own_27_donors():
    """The refit is a genuine 27-donor fit, recentred, not a rescaled 28."""
    cohort = make_cohort()
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    bound = v21.jackknife_minimum_effect(
        y=cohort["y"], age=cohort["age"], sex=cohort["sex"], oof_scores=scores)

    omitted = 5
    keep = np.arange(N) != omitted
    fl, learner = v21._frozen()
    z, _ = learner.nuisance_design(cohort["age"][keep], cohort["sex"][keep])
    _, _, t = fl.ols_hc3_last(cohort["y"][keep], np.c_[z, scores[keep]])
    record = bound["influence_refits"][omitted]
    assert record["omitted_index"] == omitted
    assert record["t_observed"] == t
    assert record["standardized_effect"] == pytest.approx(
        t / math.sqrt(27), rel=0, abs=1e-15)


# --------------------------------------------------------------------------
# 7. Jackknife behaviour and sign consistency
# --------------------------------------------------------------------------

def test_the_conservative_bound_is_bounded_by_the_full_estimate():
    cohort = make_cohort()
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    bound = v21.jackknife_minimum_effect(
        y=cohort["y"], age=cohort["age"], sex=cohort["sex"], oof_scores=scores)
    assert bound["direction_consistent"]
    assert bound["conservative_is_bounded_by_full"]
    values = [r["standardized_effect"] for r in bound["influence_refits"]]
    if bound["direction"] == "positive":
        assert bound["conservative_standardized_effect"] == min(values)
    else:
        assert bound["conservative_standardized_effect"] == max(values)
    assert abs(bound["conservative_standardized_effect"]) <= abs(
        bound["full_standardized_effect"]) + 1e-12


def test_sign_inconsistency_stops():
    """A score with no real association produces refits that cross zero."""
    rng = np.random.default_rng(4)
    for seed in range(60):
        cohort = make_cohort(seed=seed, effect=0.0)
        scores = rng.normal(size=N)
        try:
            v21.jackknife_minimum_effect(y=cohort["y"], age=cohort["age"],
                                         sex=cohort["sex"], oof_scores=scores)
        except RuntimeError as error:
            if v21.STOP_DIRECTION in str(error):
                return
    pytest.fail("no sign-inconsistent fixture was found in 60 null draws; the "
                "STOP path was never exercised")


def test_sign_inconsistency_is_not_raised_for_a_consistent_effect():
    cohort = make_cohort(effect=3.0)
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    bound = v21.jackknife_minimum_effect(
        y=cohort["y"], age=cohort["age"], sex=cohort["sex"], oof_scores=scores)
    assert bound["direction_consistent"]
    signs = {np.sign(r["standardized_effect"])
             for r in bound["influence_refits"]}
    assert len(signs) == 1


# --------------------------------------------------------------------------
# Power projection
# --------------------------------------------------------------------------

def test_power_uses_the_target_cohort_degrees_of_freedom():
    p = v21.project_power(standardized_effect_value=0.5, n_target=12)
    assert p["estimable"]
    assert p["residual_df"] == 7          # 12 - 5
    assert p["alpha"] == 0.025
    assert p["expected_t"] == pytest.approx(0.5 * math.sqrt(12))
    assert 0.0 <= p["power"] <= 1.0


def test_power_is_monotone_in_the_effect():
    powers = [v21.project_power(standardized_effect_value=d, n_target=12)["power"]
              for d in (0.1, 0.3, 0.5, 0.8, 1.2)]
    assert powers == sorted(powers)


def test_a_cohort_with_no_residual_degrees_of_freedom_is_not_estimable():
    assert not v21.project_power(standardized_effect_value=0.5,
                                 n_target=5)["estimable"]


def test_the_gate_verdict_follows_the_conservative_bound_not_the_full_effect():
    cohort = make_cohort(effect=2.0)
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    gate = v21.power_gate(y=cohort["y"], age=cohort["age"], sex=cohort["sex"],
                          oof_scores=scores)
    used = gate["projection"]["standardized_effect"]
    assert used == gate["conservative_bound"]["conservative_standardized_effect"]
    assert abs(used) <= abs(
        gate["conservative_bound"]["full_standardized_effect"]) + 1e-12
    assert gate["clears_gate"] == gate["projection"]["meets_target"]


# --------------------------------------------------------------------------
# 8. Donor-order dependence and rerun nondeterminism
# --------------------------------------------------------------------------

def test_rerunning_the_whole_construction_is_bitwise_identical():
    cohort = make_cohort()
    first = run_oof(cohort, honest_pipeline)["oof_predictions"]
    second = run_oof(cohort, honest_pipeline)["oof_predictions"]
    assert np.array_equal(first, second)

    a = v21.power_gate(y=cohort["y"], age=cohort["age"], sex=cohort["sex"],
                       oof_scores=first)
    b = v21.power_gate(y=cohort["y"], age=cohort["age"], sex=cohort["sex"],
                       oof_scores=second)
    assert a["projection"]["power"] == b["projection"]["power"]
    assert (a["conservative_bound"]["conservative_standardized_effect"]
            == b["conservative_bound"]["conservative_standardized_effect"])


def test_permuting_donor_order_does_not_change_the_effect_or_the_verdict():
    cohort = make_cohort()
    scores = run_oof(cohort, honest_pipeline)["oof_predictions"]
    perm = np.random.default_rng(2).permutation(N)
    assert not np.array_equal(perm, np.arange(N))

    straight = v21.power_gate(y=cohort["y"], age=cohort["age"],
                              sex=cohort["sex"], oof_scores=scores)
    shuffled = v21.power_gate(y=cohort["y"][perm], age=cohort["age"][perm],
                              sex=cohort["sex"][perm],
                              oof_scores=scores[perm])

    assert shuffled["conservative_bound"]["full_t"] == pytest.approx(
        straight["conservative_bound"]["full_t"], rel=1e-10, abs=1e-10)
    assert shuffled["clears_gate"] == straight["clears_gate"]

    # The set of influence refits is the same; only the labelling moves.
    straight_values = sorted(r["standardized_effect"] for r
                             in straight["conservative_bound"]["influence_refits"])
    shuffled_values = sorted(r["standardized_effect"] for r
                             in shuffled["conservative_bound"]["influence_refits"])
    assert np.allclose(straight_values, shuffled_values, rtol=1e-10, atol=1e-12)
    assert shuffled["conservative_bound"][
        "conservative_standardized_effect"] == pytest.approx(
        straight["conservative_bound"]["conservative_standardized_effect"],
        rel=1e-10, abs=1e-12)


def test_permuting_donor_order_permutes_the_out_of_fold_predictions_with_it():
    cohort = make_cohort()
    perm = np.random.default_rng(5).permutation(N)
    straight = run_oof(cohort, honest_pipeline)["oof_predictions"]
    reordered = {"age": cohort["age"][perm], "sex": cohort["sex"][perm],
                 "features": cohort["features"][perm], "y": cohort["y"][perm]}
    shuffled = run_oof(reordered, honest_pipeline)["oof_predictions"]
    assert np.allclose(shuffled, straight[perm], rtol=1e-10, atol=1e-12)


# --------------------------------------------------------------------------
# 6. Estimator selection: admissibility, ranking, deterministic tie-breaking
# --------------------------------------------------------------------------

BASE_DISPLACEMENT = {"S0": 0.50, "S1": 0.40, "S2": 0.31, "S3": 0.30, "S4": 0.60}
BASE_BIOLOGY = {"S0": 0.00, "S1": 0.05, "S2": 0.06, "S3": 0.04, "S4": 0.02}


def test_selection_picks_the_lowest_worst_case_among_admissible():
    result = v21.select_estimator(worst_case_displacement=BASE_DISPLACEMENT,
                                  biology_degradation=BASE_BIOLOGY,
                                  biology_envelope=0.10,
                                  displacement_envelope=0.0)
    assert result["selected"] == "S3"
    assert result["inadmissible_candidates"] == []


def test_a_flattened_candidate_wins_on_robustness_but_is_inadmissible():
    """The case admissibility exists to catch."""
    displacement = dict(BASE_DISPLACEMENT, S4=0.001)   # perfectly stable
    biology = dict(BASE_BIOLOGY, S4=0.90)              # signal destroyed
    result = v21.select_estimator(worst_case_displacement=displacement,
                                  biology_degradation=biology,
                                  biology_envelope=0.10,
                                  displacement_envelope=0.0)
    assert "S4" in result["inadmissible_candidates"]
    assert result["selected"] != "S4"
    assert result["selected"] == "S3"


def test_no_admissible_candidate_stops():
    biology = {k: 5.0 for k in BASE_BIOLOGY}
    with pytest.raises(RuntimeError) as excinfo:
        v21.select_estimator(worst_case_displacement=BASE_DISPLACEMENT,
                             biology_degradation=biology,
                             biology_envelope=0.10,
                             displacement_envelope=0.0)
    assert v21.STOP_NO_ADMISSIBLE in str(excinfo.value)


def test_ties_break_to_the_earliest_declared_candidate():
    """S2 and S3 are within the envelope; the earlier declared one wins."""
    result = v21.select_estimator(worst_case_displacement=BASE_DISPLACEMENT,
                                  biology_degradation=BASE_BIOLOGY,
                                  biology_envelope=0.10,
                                  displacement_envelope=0.02)
    assert result["tie_break_applied"]
    assert set(result["tied_candidates"]) == {"S2", "S3"}
    assert result["selected"] == "S2"   # earlier in S0 < S1 < S2 < S3 < S4


def test_selection_is_invariant_to_the_order_the_measurements_arrive_in():
    reordered_displacement = {k: BASE_DISPLACEMENT[k]
                              for k in ("S4", "S1", "S3", "S0", "S2")}
    reordered_biology = {k: BASE_BIOLOGY[k]
                         for k in ("S2", "S0", "S4", "S3", "S1")}
    assert list(reordered_displacement) != list(BASE_DISPLACEMENT)

    straight = v21.select_estimator(worst_case_displacement=BASE_DISPLACEMENT,
                                    biology_degradation=BASE_BIOLOGY,
                                    biology_envelope=0.10,
                                    displacement_envelope=0.02)
    shuffled = v21.select_estimator(
        worst_case_displacement=reordered_displacement,
        biology_degradation=reordered_biology,
        biology_envelope=0.10, displacement_envelope=0.02)
    assert straight["selected"] == shuffled["selected"]
    assert straight["tied_candidates"] == shuffled["tied_candidates"]
    assert straight["table"] == shuffled["table"]


def test_selection_is_identical_on_rerun():
    runs = [v21.select_estimator(worst_case_displacement=BASE_DISPLACEMENT,
                                 biology_degradation=BASE_BIOLOGY,
                                 biology_envelope=0.10,
                                 displacement_envelope=0.02)
            for _ in range(5)]
    assert all(r == runs[0] for r in runs)


def test_a_candidate_set_that_does_not_match_the_declared_order_stops():
    with pytest.raises(RuntimeError):
        v21.select_estimator(
            worst_case_displacement={"S0": 0.1, "S1": 0.2},
            biology_degradation={"S0": 0.0, "S1": 0.0},
            biology_envelope=0.1, displacement_envelope=0.0)


# --------------------------------------------------------------------------
# Ridge stability envelopes: per metric, all 28 refits, nothing averaged
# --------------------------------------------------------------------------

def test_one_failing_metric_is_not_masked_by_the_other_two():
    envelopes = {"metric_a": [0.10] * 28, "metric_b": [0.10] * 28,
                 "metric_c": [0.10] * 28}
    induced = {"metric_a": 0.01, "metric_b": 0.01, "metric_c": 0.40}
    # An average would pass: (0.01 + 0.01 + 0.40) / 3 = 0.14 against a mean
    # envelope of 0.10 is still a failure here, but with a milder third metric
    # it would not be -- which is exactly why nothing is averaged.
    result = v21.within_envelope_per_metric(induced=induced,
                                            envelopes=envelopes,
                                            expected_refits=28)
    assert not result["all_within_envelope"]
    assert result["failing_metrics"] == ["metric_c"]
    assert result["per_metric"]["metric_a"]["within_envelope"]
    assert result["per_metric"]["metric_b"]["within_envelope"]


def test_averaging_would_have_masked_the_failure():
    """The masking case stated explicitly, so the rule's value is measurable."""
    envelopes = {"m1": [0.20] * 28, "m2": [0.20] * 28, "m3": [0.20] * 28}
    induced = {"m1": 0.00, "m2": 0.00, "m3": 0.45}
    assert np.mean(list(induced.values())) <= 0.20   # an average would pass
    result = v21.within_envelope_per_metric(induced=induced,
                                            envelopes=envelopes,
                                            expected_refits=28)
    assert result["failing_metrics"] == ["m3"]
    assert not result["all_within_envelope"]


def test_an_envelope_built_from_fewer_than_28_refits_stops():
    with pytest.raises(RuntimeError) as excinfo:
        v21.within_envelope_per_metric(induced={"m1": 0.01},
                                       envelopes={"m1": [0.10] * 27},
                                       expected_refits=28)
    assert v21.STOP_RIDGE in str(excinfo.value)


def test_the_envelope_is_the_maximum_not_a_percentile():
    series = [0.01] * 27 + [0.50]
    assert v21.lodo_envelope(series) == 0.50
    assert v21.lodo_envelope([-0.7, 0.2]) == 0.7


def _paired_losses(centre: float, exponents, n_donors=N, spread=0.0, seed=1):
    """Per-donor CV losses with a common donor offset, so pairing bites."""
    rng = np.random.default_rng(seed)
    donor_offset = rng.normal(scale=5.0, size=(n_donors, 1))  # large, shared
    curve = np.array([spread * (e - centre) ** 2 for e in exponents])
    noise = rng.normal(scale=0.001, size=(n_donors, len(exponents)))
    return donor_offset + curve[None, :] + noise


def test_a_decisive_surface_gives_a_narrow_near_optimal_set():
    exps = [-4.0, -2.0, 0.0, 2.0, 4.0]
    result = v21.near_optimal_set(
        exponents=exps,
        per_donor_losses=_paired_losses(0.0, exps, spread=1.0))
    assert result["minimum_exponent"] == 0.0
    assert result["near_optimal_set"] == [0.0]
    assert result["flag"] is None


def _flat_paired_losses(exponents, n_donors=N):
    """A genuinely flat surface: equal mean loss, unequal per-donor losses.

    Each exponent gets a donor-varying perturbation that sums to zero across
    donors, so every exponent has the same mean CV loss while the paired
    differences still have a real, nonzero standard error. Built deterministically
    because a noisy fixture leaves a systematic gap between the sample argmin and
    the rest, which is a decisive surface, not a flat one.
    """
    donor_offset = np.linspace(2.0, 6.0, n_donors)[:, None]
    zero_sum = np.arange(n_donors, dtype=float) - (n_donors - 1) / 2.0
    scale = np.array([0.30, 0.10, 0.70, 0.20, 0.50])[:len(exponents)]
    return donor_offset + zero_sum[:, None] * scale[None, :]


def test_a_flat_surface_is_flagged_but_not_rejected():
    exps = [-4.0, -2.0, 0.0, 2.0, 4.0]
    losses = _flat_paired_losses(exps)
    assert np.allclose(losses.mean(axis=0), losses.mean())  # genuinely flat
    result = v21.near_optimal_set(exponents=exps, per_donor_losses=losses)
    assert result["near_optimal_set"] == exps
    assert result["width_in_decades"] == 8.0
    assert result["flag"] == v21.FLAG_RIDGE_CV_SURFACE_FLAT
    # A flag, never a rejection: the call returned rather than raising.
    assert all(d["paired_standard_error"] >= 0.0
               for d in result["per_exponent"])
    assert any(d["paired_standard_error"] > 0.0
               for d in result["per_exponent"]), (
        "every paired standard error was zero, so inclusion was degenerate")


def test_the_near_optimal_set_uses_the_paired_standard_error():
    """The shared donor offset must cancel; an unpaired SE would swamp it."""
    exps = [-4.0, -2.0, 0.0, 2.0, 4.0]
    losses = _paired_losses(0.0, exps, spread=1.0)
    unpaired_se = float(losses[:, 0].std(ddof=1) / math.sqrt(losses.shape[0]))
    result = v21.near_optimal_set(exponents=exps, per_donor_losses=losses)
    paired_se = max(d["paired_standard_error"] for d in result["per_exponent"])
    assert paired_se < unpaired_se / 100.0, (
        "the standard error was not computed on paired differences")
    assert result["near_optimal_set"] == [0.0]


def test_the_strongest_regularisation_in_the_set_is_selected():
    exps = [-4.0, -2.0, 0.0, 2.0, 4.0]
    near = v21.near_optimal_set(exponents=exps,
                                per_donor_losses=_flat_paired_losses(exps))
    assert near["strongest_regularisation_in_set"] == 4.0
    verdict = v21.ridge_stability_verdict(
        induced={m: 0.01 for m in v21.RIDGE_STABILITY_METRICS},
        envelopes={m: [0.10] * 28 for m in v21.RIDGE_STABILITY_METRICS},
        near_optimal=near)
    assert verdict["identified"]
    assert verdict["selected_exponent"] == 4.0
    assert verdict["lambda_weakly_identified"]
    assert verdict["estimator_identified"]


def test_the_verdict_requires_exactly_the_three_named_metrics():
    near = {"strongest_regularisation_in_set": 0.0, "flag": None}
    with pytest.raises(RuntimeError) as excinfo:
        v21.ridge_stability_verdict(
            induced={"beta_direction": 0.01, "donor_summaries": 0.01},
            envelopes={"beta_direction": [0.1] * 28,
                       "donor_summaries": [0.1] * 28},
            near_optimal=near)
    assert v21.STOP_RIDGE in excinfo.value.args[0]
    assert "cell_score_geometry" in str(excinfo.value)


def test_one_metric_outside_its_envelope_stops_the_whole_verdict():
    near = {"strongest_regularisation_in_set": 0.0, "flag": None}
    induced = {m: 0.01 for m in v21.RIDGE_STABILITY_METRICS}
    induced["cell_score_geometry"] = 0.90
    with pytest.raises(RuntimeError) as excinfo:
        v21.ridge_stability_verdict(
            induced=induced,
            envelopes={m: [0.10] * 28 for m in v21.RIDGE_STABILITY_METRICS},
            near_optimal=near)
    assert v21.STOP_RIDGE in str(excinfo.value)
    assert "cell_score_geometry" in str(excinfo.value)


def test_mismatched_metric_sets_stop():
    with pytest.raises(RuntimeError):
        v21.within_envelope_per_metric(induced={"m1": 0.1, "m2": 0.1},
                                       envelopes={"m1": [0.2] * 28})


# --------------------------------------------------------------------------
# Ridge bracketing search
# --------------------------------------------------------------------------

def test_the_search_recovers_an_optimum_near_the_coarse_minimum():
    """0.05 is inside the 0.125 the frozen refinement ladder can tolerate."""
    result = v21.ridge_bracket_search(lambda e: (e - 0.05) ** 2)
    assert result["interior"]
    assert result["selected_exponent"] == 0.0
    assert result["n_refinement_rounds"] == v21.RIDGE_REFINEMENT_ROUNDS
    assert all(r["interior"] for r in result["refinement_rounds"])


def test_the_search_stops_when_the_optimum_sits_on_a_boundary():
    """Stage B must be the stage that refuses, not stage C downstream of it.

    Both stages raise the same STOP marker, so a test that only checks the
    marker would pass even with stage B removed -- the mutation audit found
    exactly that. The refusing stage is asserted by its message.
    """
    with pytest.raises(RuntimeError) as excinfo:
        v21.ridge_bracket_search(lambda e: e)   # decreasing without bound
    message = str(excinfo.value)
    assert v21.STOP_RIDGE_BOUNDARY in message
    assert "bracket endpoint" in message, (
        "stage B did not refuse; the refusal came from a later stage")


def test_the_search_stops_for_an_optimum_beyond_the_expansion_reach():
    """-30 lies past the -20 the three permitted expansions can reach."""
    with pytest.raises(RuntimeError) as excinfo:
        v21.ridge_bracket_search(lambda e: (e + 30.0) ** 2)
    message = str(excinfo.value)
    assert v21.STOP_RIDGE_BOUNDARY in message
    assert "bracket endpoint" in message
    assert "{'low': 3, 'high': 0}" in message or "'low': 3" in message


def test_the_search_finds_an_optimum_reached_by_expansion():
    result = v21.ridge_bracket_search(lambda e: (e + 12.0) ** 2)
    assert result["expansions"]["low"] >= 1
    assert result["selected_exponent"] == -12.0
    assert all(r["interior"] for r in result["refinement_rounds"])


def test_stage_c_refuses_an_optimum_between_the_anchors():
    """The literal contract STOPs at 1.25, and that is the finding, not a bug.

    A refinement round evaluates only the centre and the two points a step
    away, and section 3.1 requires the centre to win. An optimum at 1.25 is
    nearer to 2 than to 0 at the first round, so the round's minimum lands on
    an endpoint and the search refuses.
    """
    with pytest.raises(RuntimeError) as excinfo:
        v21.ridge_bracket_search(lambda e: (e - 1.25) ** 2)
    assert v21.STOP_RIDGE_BOUNDARY in str(excinfo.value)
    assert "stage c" in str(excinfo.value).lower()


def test_refinement_cannot_move_the_selected_exponent():
    """The consequence of the literal reading, asserted rather than described."""
    for target in (0.0, -0.05, 0.1, -4.0, 4.05):
        try:
            result = v21.ridge_bracket_search(lambda e: (e - target) ** 2)
        except RuntimeError:
            continue
        centres = {r["centre"] for r in result["refinement_rounds"]}
        assert len(centres) == 1, "refinement moved the centre"
        assert result["selected_exponent"] in centres
        assert result["selected_exponent"] % v21.RIDGE_EXPANSION_STEP == 0.0


def test_the_refinement_reach_is_an_eighth_of_an_anchor_spacing():
    reach = v21.characterize_refinement_reach()
    assert reach["n_rounds"] == 4
    assert reach["binding_tolerance"] == 0.125
    assert reach["anchor_spacing"] == 4.0
    assert reach["fraction_of_anchor_spacing"] == 0.03125
    assert not reach["selected_exponent_can_move_during_refinement"]


def test_the_search_is_deterministic_and_evaluates_each_exponent_once():
    calls: list[float] = []

    def evaluate(e):
        calls.append(e)
        return (e - 0.05) ** 2

    first = v21.ridge_bracket_search(evaluate)
    assert len(calls) == len(set(calls)), "an exponent was evaluated twice"
    second = v21.ridge_bracket_search(lambda e: (e - 0.05) ** 2)
    assert first["selected_exponent"] == second["selected_exponent"]
    assert first["trace"] == second["trace"]
    assert first["refinement_rounds"] == second["refinement_rounds"]


# --------------------------------------------------------------------------
# The frozen V20 tie rule, reused rather than redefined
# --------------------------------------------------------------------------

def test_the_tie_rule_prefers_more_regularization_as_v20_does():
    losses = {-4.0: 1.0, 0.0: 1.0, 4.0: 2.0}
    assert v21.v20_tie_choice([-4.0, 0.0, 4.0], losses) == 0.0


def test_the_tie_rule_uses_the_frozen_relative_tolerance():
    """A difference below 1e-12 relative is a tie; just above it is not."""
    base = 3.0
    inside = base * (1.0 + 1e-13)
    outside = base * (1.0 + 1e-9)
    assert v21.v20_tie_choice([0.0, 4.0], {0.0: base, 4.0: inside}) == 4.0
    assert v21.v20_tie_choice([0.0, 4.0], {0.0: base, 4.0: outside}) == 0.0


def test_the_tie_rule_matches_the_frozen_learner_on_the_same_losses():
    """Compared against V20's own selection code path, not against my reading."""
    _, learner = v21._frozen()
    exponents = learner.MULTIPLIER_EXPONENTS
    rng = np.random.default_rng(17)
    for _ in range(200):
        losses = rng.random(len(exponents))
        losses[rng.integers(len(exponents))] = losses.min()   # force ties
        # V20's own rule, transcribed from `fit_t0_target`.
        minloss = float(np.min(losses))
        tol = 1e-12 * max(1.0, abs(minloss))
        expected = float(exponents[int(np.flatnonzero(
            losses <= minloss + tol)[-1])])
        mapping = {float(e): float(v) for e, v in zip(exponents, losses)}
        assert v21.v20_tie_choice(list(mapping), mapping) == expected


def test_a_nonfinite_cv_loss_stops():
    with pytest.raises(RuntimeError) as excinfo:
        v21.ridge_bracket_search(lambda e: float("nan"))
    assert v21.STOP_RIDGE in str(excinfo.value)


# --------------------------------------------------------------------------
# The executor opens nothing
# --------------------------------------------------------------------------

def test_the_frozen_numerics_resolve_inside_this_checkout():
    """The executor must run from a clone, not only from this machine.

    An earlier version reached the frozen numerics through
    `t0_stage2a_pre_at8_gate_v1._frozen`, whose FROZEN_V20 is an absolute path
    into a session temp directory. Every test here passed locally while the
    module would have failed at import on a reviewer's clone. This pins the
    resolution to the committed directory so that cannot recur silently.
    """
    fl, learner = v21._frozen()
    for module in (fl, learner):
        resolved = Path(module.__file__).resolve()
        assert resolved.parent == (HERE / "t0_v20_frozen").resolve(), (
            "%s resolved to %s, outside the committed frozen V20 directory"
            % (module.__name__, resolved))
        assert resolved.is_file()


def test_frozen_import_refuses_a_module_already_cached_from_elsewhere(tmp_path):
    """The realistic way the wrong frozen source gets used.

    `__import__` returns whatever is in `sys.modules`, so inserting the frozen
    directory on `sys.path` does nothing if some other lane script — one whose
    own frozen path points at a session temp directory — imported the same
    module name earlier in the same process. Running the whole scripts/v4 suite
    in one pytest process is enough to arrange that. The executor must refuse
    rather than silently compute on a different copy.
    """
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    name = "t0_studentized_fl_v1"
    shutil.copy(HERE / "t0_v20_frozen" / (name + ".py"), decoy / (name + ".py"))

    spec = importlib.util.spec_from_file_location(name, decoy / (name + ".py"))
    planted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planted)

    saved = sys.modules.get(name)
    sys.modules[name] = planted
    try:
        with pytest.raises(RuntimeError) as excinfo:
            v21._frozen()
        assert v21.STOP in str(excinfo.value)
        assert "outside the committed frozen V20 directory" in str(excinfo.value)
    finally:
        if saved is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = saved

    # And the executor still works once the planted module is gone.
    fl, _ = v21._frozen()
    assert Path(fl.__file__).resolve().parent == (HERE / "t0_v20_frozen").resolve()


def test_the_executor_does_not_depend_on_any_absolute_path():
    """No drive-letter or temp-directory literal anywhere in the module."""
    source = (HERE / "t0_v21_selection_and_power_v1.py").read_text(
        encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
            assert not re.match(r"^[A-Za-z]:[\\/]", text), (
                "absolute path literal %r" % text)
            assert "AppData" not in text and "/tmp/" not in text, (
                "temp-directory literal %r" % text)


def test_the_module_has_no_entry_point_that_could_run_against_real_data():
    """Checked on the parse tree, not by searching the text.

    A substring search cannot tell code from prose: this module's own docstring
    says it has no `__main__` and reads no AT8 value, and a text search flags
    those sentences as if they were the thing they deny. The guard has to look
    at what the module *does*.
    """
    source = (HERE / "t0_v21_selection_and_power_v1.py").read_text(
        encoding="utf-8")
    tree = ast.parse(source)

    # No `if __name__ == "__main__":` block anywhere.
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            for sub in ast.walk(node.test):
                assert not (isinstance(sub, ast.Name) and sub.id == "__name__"), \
                    "the executor defines a __main__ entry point"

    # No command-line or file-reading imports.
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for forbidden in ("argparse", "pandas", "csv", "json", "sqlite3",
                      "h5py", "anndata", "scipy.sparse"):
        assert forbidden not in imported, (
            "the executor imports %r; it must take arrays and callables only"
            % forbidden)

    # No I/O calls in the executable body.
    io_calls = {"open", "read_csv", "read_text", "read_bytes", "load",
                "loadtxt", "genfromtxt", "read_parquet"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            assert name not in io_calls, (
                "the executor calls %r; it must not read data itself" % name)
