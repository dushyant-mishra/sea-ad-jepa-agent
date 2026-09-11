#!/usr/bin/env python3
"""Executable machinery for the V21-T1 estimator selection and power gate.

This is the **executor** for the procedures specified in
`docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`. The commit that cleared the
external design review repaired the contract; it did not make the contract
runnable. This module does, and `test_t0_v21_selection_and_power_v1.py` is what
qualifies it.

Nothing here runs on real data by being imported. There is no `__main__` that
opens a cohort, no AT8 value is read, no partition is opened, and no V20
artifact is touched. Every entry point takes arrays and callables, so the
machinery is exercised against synthetic fixtures with known ground truth long
before it is pointed at donors. Selection and the power gate remain
unauthorized; this module only makes them implementable.

The frozen numerics are reused, never reimplemented: `ols_hc3_last` from
`t0_studentized_fl_v1` is the HC3 engine, and `nuisance_design` from
`t0_target_learner_v1` builds `[1, age_c, age_c^2, sex]`. The frozen
`tail_hc3_t` wrapper is deliberately not used: it declares `n in {17, 18}` and
this procedure runs at n = 28.

The procedures, and the properties the tests hold them to.

**Outer leave-one-donor-out prediction.** Exactly 28 folds, every donor held out
exactly once, ridge selection nested strictly inside each 27-donor training
fold. The fold callable is handed the training indices and nothing else, so a
fold cannot reach its held-out donor through this module; whether the caller
leaks one is what the leakage test settles.

**The out-of-fold effect.** One HC3 regression, fit once, after the 28
out-of-fold predictions are assembled. Not one per fold: under
leave-one-donor-out a fold contains a single donor and no donor-level regression
is estimable there. That error in an earlier draft is the reason this module
exists.

**The conservative bound.** The jackknife minimum across the 28 influence
refits, conditional on all of them agreeing in sign.

**Standardization.** `delta = t_n / sqrt(n)`, where `n` is the size of the
sample that produced `t_n`. The full effect divides by sqrt(28); a 27-donor
influence refit divides by sqrt(27), not sqrt(28). It is stated here, applied
through one function, and pinned by a test, because it is a frozen equation and
not something to be reinterpreted once results exist.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# The committed frozen V20 code, resolved relative to this file.
FROZEN_V20 = HERE / "t0_v20_frozen"

STOP = "STOP_T0_V21_SELECTION_OR_POWER_REFUSED"
STOP_DIRECTION = "STOP_EFFECT_DIRECTION_NOT_CONSISTENT"
STOP_NO_ADMISSIBLE = "STOP_NO_ADMISSIBLE_ESTIMATOR"
STOP_RIDGE = "STOP_RIDGE_SELECTION_NOT_IDENTIFIED"
STOP_RIDGE_BOUNDARY = "STOP_RIDGE_OPTIMUM_ON_BRACKET_BOUNDARY"
STOP_FOLD_COVERAGE = "STOP_OUTER_FOLD_COVERAGE_INVALID"
STOP_LEAKAGE = "STOP_HELD_OUT_DONOR_VISIBLE_TO_ITS_OWN_FOLD"

# Frozen by the contract. Geometry is asserted, never inferred from what arrives.
V21_DISCOVERY_DONORS = 28
V21_CONFIRMATION_DONORS = 12
NUISANCE_RANK = 4           # [1, age_c, age_c^2, sex]
P_FULL = NUISANCE_RANK + 1  # plus the score column
ALPHA = 0.025
TARGET_POWER = 0.80

RIDGE_ANCHORS = (-8.0, -4.0, 0.0, 4.0, 8.0)
RIDGE_EXPANSION_STEP = 4.0
RIDGE_MAX_EXPANSIONS = 3
RIDGE_REFINEMENT_STEPS = (2.0, 1.0, 0.5, 0.25)
RIDGE_REFINEMENT_ROUNDS = 4
# The frozen V20 near-tie tolerance, read from `t0_target_learner_v1.fit_t0_target`
# rather than restated: `tol = 1e-12 * max(1.0, abs(minloss))`.
V20_TIE_RELATIVE_TOLERANCE = 1e-12

DECLARED_ESTIMATOR_ORDER = ("S0", "S1", "S2", "S3", "S4")


def _fail(marker: str, message: str) -> None:
    raise RuntimeError("%s: %s" % (marker, message))


def _frozen():
    """The frozen numerics: the HC3 engine and the nuisance design.

    Loaded from the committed `scripts/v4/t0_v20_frozen/` directory, resolved
    relative to this file. Deliberately **not** routed through
    `t0_stage2a_pre_at8_gate_v1._frozen`, whose `FROZEN_V20` is an absolute path
    into a session temp directory: that resolves on one machine and nowhere
    else, so a reviewer's clone would fail at import while the suite looked green
    locally. The committed copies are byte-identical to the ones that path
    reaches, so nothing numeric changes.

    V20 is imported and read. It is never written.
    """
    if not FROZEN_V20.is_dir():
        _fail(STOP, "the committed frozen V20 directory is missing at %s"
              % FROZEN_V20)
    if str(FROZEN_V20) not in sys.path:
        sys.path.insert(0, str(FROZEN_V20))
    modules = (__import__("t0_studentized_fl_v1"),
               __import__("t0_target_learner_v1"))
    for module in modules:
        resolved = Path(module.__file__).resolve()
        if resolved.parent != FROZEN_V20.resolve():
            _fail(STOP,
                  "%s resolved to %s, outside the committed frozen V20 "
                  "directory %s" % (module.__name__, resolved, FROZEN_V20))
    return modules


# --------------------------------------------------------------------------
# 0. Standardization -- one definition, used everywhere
# --------------------------------------------------------------------------

def standardized_effect(t_statistic: float, n: int) -> float:
    """`delta = t_n / sqrt(n)`, with `n` the sample that produced `t_n`.

    The frozen equation reads `delta = t_28 / sqrt(28)` for the full effect. A
    leave-one-donor-out influence refit is a 27-donor fit, so it divides by
    sqrt(27). Dividing a 27-donor `t` by sqrt(28) would deflate every refit by
    sqrt(27/28) and make the jackknife minimum conservative for an arithmetic
    reason rather than a statistical one.

    Kept as a single function so the divisor is one auditable decision rather
    than an incidental consequence of whatever array length happened to arrive.
    """
    if n <= 0:
        _fail(STOP, "standardization needs a positive sample size")
    return float(t_statistic) / math.sqrt(float(n))


# --------------------------------------------------------------------------
# 1. Outer leave-one-donor-out with strictly nested fold training
# --------------------------------------------------------------------------

class FoldRecord:
    """What one outer fold did, recorded so the run is checkable afterwards."""

    __slots__ = ("held_out", "train", "prediction", "ridge_exponent")

    def __init__(self, held_out: int, train: np.ndarray, prediction: float,
                 ridge_exponent: float | None):
        self.held_out = int(held_out)
        self.train = np.asarray(train, dtype=np.int64)
        self.prediction = float(prediction)
        self.ridge_exponent = (None if ridge_exponent is None
                               else float(ridge_exponent))

    def as_dict(self) -> dict[str, Any]:
        return {"held_out_index": self.held_out,
                "n_train": int(self.train.size),
                "out_of_fold_prediction": self.prediction,
                "fold_ridge_exponent": self.ridge_exponent}


def outer_lodo_oof(*, n_donors: int,
                   train_fold: Callable[[np.ndarray], Any],
                   predict_held_out: Callable[[Any, int], float],
                   fold_ridge_exponent: Callable[[Any], float] | None = None,
                   expected_n_donors: int | None = V21_DISCOVERY_DONORS,
                   ) -> dict[str, Any]:
    """Exactly `n_donors` folds, each donor held out once, nothing shared.

    `train_fold` receives the training indices and nothing else. It is expected
    to run its own inner ridge selection on those donors alone; because it never
    receives the held-out index, this module cannot be the channel through which
    a fold sees its own donor. Whether the *caller* leaks one is what the
    leakage test settles, and the per-fold ridge exponents recorded here are what
    make a single global hyperparameter visible if one is ever used.
    """
    n_donors = int(n_donors)
    if expected_n_donors is not None and n_donors != expected_n_donors:
        _fail(STOP_FOLD_COVERAGE,
              "the contract fixes %d discovery donors; %d were supplied"
              % (expected_n_donors, n_donors))
    if n_donors < P_FULL + 1:
        _fail(STOP_FOLD_COVERAGE,
              "n = %d leaves no residual degrees of freedom at p = %d"
              % (n_donors, P_FULL))

    everything = np.arange(n_donors, dtype=np.int64)
    records: list[FoldRecord] = []
    for held_out in range(n_donors):
        train = everything[everything != held_out]
        if train.size != n_donors - 1:
            _fail(STOP_FOLD_COVERAGE,
                  "fold %d trains on %d donors, expected %d"
                  % (held_out, train.size, n_donors - 1))
        if int(held_out) in set(int(i) for i in train):
            _fail(STOP_LEAKAGE,
                  "fold %d would train on its own held-out donor" % held_out)
        model = train_fold(train.copy())
        value = float(predict_held_out(model, int(held_out)))
        if not math.isfinite(value):
            _fail(STOP, "nonfinite out-of-fold prediction for donor %d"
                  % held_out)
        exponent = (None if fold_ridge_exponent is None
                    else float(fold_ridge_exponent(model)))
        records.append(FoldRecord(held_out, train, value, exponent))

    held = [r.held_out for r in records]
    if sorted(held) != list(range(n_donors)):
        _fail(STOP_FOLD_COVERAGE,
              "each donor must be held out exactly once; got %r" % (held,))

    exponents = [r.ridge_exponent for r in records]
    distinct = sorted({e for e in exponents if e is not None})
    return {
        "n_donors": n_donors,
        "n_folds": len(records),
        "every_donor_held_out_exactly_once": True,
        "fold_train_size": n_donors - 1,
        "oof_predictions": np.array([r.prediction for r in records],
                                    dtype=np.float64),
        "fold_ridge_exponents": exponents,
        "distinct_fold_ridge_exponents": distinct,
        "ridge_selected_inside_each_fold": fold_ridge_exponent is not None,
        "folds": [r.as_dict() for r in records],
    }


# --------------------------------------------------------------------------
# 2. The out-of-fold effect: one HC3 regression, after assembly
# --------------------------------------------------------------------------

def oof_effect(*, y: np.ndarray, age: np.ndarray, sex: np.ndarray,
               oof_scores: np.ndarray, age_center: float | None = None,
               ) -> dict[str, Any]:
    """A single donor-level HC3 regression across the assembled predictions."""
    fl, learner = _frozen()
    y = np.asarray(y, dtype=np.float64)
    scores = np.asarray(oof_scores, dtype=np.float64)
    if y.ndim != 1 or y.shape != scores.shape:
        _fail(STOP, "y and the out-of-fold scores must be matching 1-D arrays")
    if not (np.isfinite(y).all() and np.isfinite(scores).all()):
        _fail(STOP, "y and the out-of-fold scores must be finite")

    # The frozen nuisance design refuses a cohort whose sex coding is not
    # complete binary, and refuses a rank-deficient design, by raising
    # ValueError. That is reachable in a jackknife refit -- omitting a donor can
    # empty a sex level -- so it is converted here into a non-estimable result
    # rather than being allowed to escape as an unhandled exception.
    try:
        nuisance, center = learner.nuisance_design(
            np.asarray(age, dtype=np.float64),
            np.asarray(sex, dtype=np.float64), age_center=age_center)
    except ValueError as error:
        return {"estimable": False, "reason": "nuisance design: %s" % error,
                "n": int(len(y))}
    if nuisance.shape[1] != NUISANCE_RANK:
        _fail(STOP, "the frozen nuisance design must have %d columns, got %d"
              % (NUISANCE_RANK, nuisance.shape[1]))
    design = np.c_[nuisance, scores]
    if design.shape[1] != P_FULL:
        _fail(STOP, "the full design must have %d columns, got %d"
              % (P_FULL, design.shape[1]))

    n = int(len(y))
    try:
        beta, se, t = fl.ols_hc3_last(y, design)
    except fl.NotEstimableError as error:
        return {"estimable": False, "reason": str(error), "n": n}
    df = n - P_FULL
    return {
        "estimable": True,
        "beta": float(beta), "hc3_se": float(se), "t_observed": float(t),
        "n": n, "residual_df": df, "p_full": P_FULL,
        "age_center": float(center),
        "standardized_effect": standardized_effect(float(t), n),
        "p_upper": float(stats.t.sf(float(t), df)),
    }


# --------------------------------------------------------------------------
# 3. The conservative bound: jackknife minimum, sign-consistency required
# --------------------------------------------------------------------------

def jackknife_minimum_effect(*, y: np.ndarray, age: np.ndarray,
                             sex: np.ndarray, oof_scores: np.ndarray,
                             ) -> dict[str, Any]:
    """The worst case over the leave-one-donor-out influence refits.

    Cross-fitting removes in-sample optimism; it does not produce a lower bound.
    This does, without introducing a constant: recompute the single regression
    with each donor omitted in turn and take the smallest standardized effect in
    the observed direction.

    Sign consistency is a precondition, not a nicety. A minimum taken across
    refits that disagree in direction is an arbitrary number rather than a
    conservative one.
    """
    y = np.asarray(y, dtype=np.float64)
    age = np.asarray(age, dtype=np.float64)
    sex = np.asarray(sex, dtype=np.float64)
    scores = np.asarray(oof_scores, dtype=np.float64)
    n = int(len(y))

    full = oof_effect(y=y, age=age, sex=sex, oof_scores=scores)
    if not full.get("estimable"):
        _fail(STOP, "the full out-of-fold effect is not estimable: %s"
              % full.get("reason"))

    refits: list[dict[str, Any]] = []
    for omitted in range(n):
        keep = np.arange(n) != omitted
        # The age centre is recentred within each refit, as the frozen nuisance
        # design does whenever it is handed a cohort.
        refit = oof_effect(y=y[keep], age=age[keep], sex=sex[keep],
                           oof_scores=scores[keep])
        if not refit.get("estimable"):
            _fail(STOP, "influence refit omitting donor %d is not estimable: %s"
                  % (omitted, refit.get("reason")))
        if refit["n"] != n - 1:
            _fail(STOP, "influence refit omitting donor %d used n = %d"
                  % (omitted, refit["n"]))
        refits.append({"omitted_index": omitted, "n": refit["n"],
                       "t_observed": refit["t_observed"],
                       "standardized_effect": refit["standardized_effect"]})

    values = np.array([r["standardized_effect"] for r in refits],
                      dtype=np.float64)
    signs = np.sign(values)
    if not (np.all(signs == signs[0]) and signs[0] != 0):
        _fail(STOP_DIRECTION,
              "influence refits disagree in sign (%d positive, %d negative, "
              "%d zero); the conservative bound is undefined"
              % (int(np.sum(values > 0)), int(np.sum(values < 0)),
                 int(np.sum(values == 0))))

    conservative = float(values.min()) if signs[0] > 0 else float(values.max())
    full_delta = full["standardized_effect"]
    return {
        "full_n": full["n"],
        "full_t": full["t_observed"],
        "full_standardized_effect": full_delta,
        "n_influence_refits": len(refits),
        "influence_refits": refits,
        "refit_n": n - 1,
        "direction": "positive" if signs[0] > 0 else "negative",
        "direction_consistent": True,
        "conservative_standardized_effect": conservative,
        "conservative_is_bounded_by_full":
            bool(abs(conservative) <= abs(full_delta) + 1e-12),
    }


# --------------------------------------------------------------------------
# 4. Power projection
# --------------------------------------------------------------------------

def project_power(*, standardized_effect_value: float, n_target: int,
                  p_full: int = P_FULL, alpha: float = ALPHA,
                  ) -> dict[str, Any]:
    """Project a standardized effect onto a target cohort size.

    `delta = t / sqrt(n)`, so the statistic expected at `n_target` is
    `delta * sqrt(n_target)`, and power follows from the noncentral `t` at the
    target's residual degrees of freedom against the frozen one-sided alpha.
    """
    df = int(n_target) - int(p_full)
    if df < 1:
        return {"estimable": False, "n_target": int(n_target),
                "residual_df": df,
                "reason": "no residual degrees of freedom at this cohort size"}
    expected = float(standardized_effect_value) * math.sqrt(float(n_target))
    critical = float(stats.t.isf(alpha, df))
    power = float(stats.nct.sf(critical, df, expected))

    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if stats.nct.sf(critical, df, mid) < TARGET_POWER:
            lo = mid
        else:
            hi = mid
    needed = float(hi)
    return {
        "estimable": True,
        "n_target": int(n_target), "residual_df": df, "alpha": float(alpha),
        "standardized_effect": float(standardized_effect_value),
        "expected_t": expected, "t_critical": critical,
        "power": power, "target_power": TARGET_POWER,
        "meets_target": bool(power >= TARGET_POWER),
        "noncentrality_needed_for_target_power": needed,
        "standardized_effect_needed": needed / math.sqrt(float(n_target)),
    }


def power_gate(*, y: np.ndarray, age: np.ndarray, sex: np.ndarray,
               oof_scores: np.ndarray,
               n_target: int = V21_CONFIRMATION_DONORS) -> dict[str, Any]:
    """The whole gate: assembled out-of-fold predictions to a verdict."""
    bound = jackknife_minimum_effect(y=y, age=age, sex=sex,
                                     oof_scores=oof_scores)
    projection = project_power(
        standardized_effect_value=bound["conservative_standardized_effect"],
        n_target=n_target)
    return {"conservative_bound": bound, "projection": projection,
            "clears_gate": bool(projection.get("meets_target", False))}


# --------------------------------------------------------------------------
# 5. Leave-one-out envelopes, per metric, nothing averaged
# --------------------------------------------------------------------------

RIDGE_STABILITY_METRICS = ("beta_direction", "cell_score_geometry",
                           "donor_summaries")
RIDGE_FLAT_SURFACE_DECADES = 2.0
FLAG_RIDGE_CV_SURFACE_FLAT = "RIDGE_CV_SURFACE_FLAT"


def near_optimal_set(*, exponents: Sequence[float],
                     per_donor_losses: np.ndarray) -> dict[str, Any]:
    """Section 3.3 step 1 -- the near-optimal set, by paired LOODO uncertainty.

    The same donors are held out at every lambda, so the standard error of the
    *difference* in CV loss between two lambdas is the right scale, and it is far
    tighter than an unpaired comparison. A lambda joins the near-optimal set when
    its mean paired difference from the minimum is within one standard error of
    zero.

    No constant is chosen: the width of the set is set by the data's own
    donor-to-donor variability.
    """
    exps = [float(e) for e in exponents]
    losses = np.asarray(per_donor_losses, dtype=np.float64)
    if losses.ndim != 2 or losses.shape[1] != len(exps):
        _fail(STOP_RIDGE,
              "per-donor losses must be (n_donors, n_exponents); got %r for %d "
              "exponents" % (losses.shape, len(exps)))
    if losses.shape[0] < 2:
        _fail(STOP_RIDGE, "a paired standard error needs at least two donors")
    if not np.isfinite(losses).all():
        _fail(STOP_RIDGE, "per-donor CV losses must be finite")

    mean_loss = {e: float(losses[:, j].mean()) for j, e in enumerate(exps)}
    best = v20_tie_choice(exps, mean_loss)
    j_best = exps.index(best)

    n = losses.shape[0]
    members, detail = [], []
    for j, e in enumerate(exps):
        paired = losses[:, j] - losses[:, j_best]
        mean_difference = float(paired.mean())
        se = float(paired.std(ddof=1) / math.sqrt(n))
        within = bool(mean_difference <= se)
        detail.append({"exponent": e, "mean_paired_difference": mean_difference,
                       "paired_standard_error": se, "in_near_optimal_set": within})
        if within:
            members.append(e)

    members.sort()
    width = float(members[-1] - members[0]) if members else 0.0
    return {
        "minimum_exponent": float(best),
        "near_optimal_set": members,
        "width_in_decades": width,
        "flat_surface_threshold_decades": RIDGE_FLAT_SURFACE_DECADES,
        # A flag, never a rejection -- section 3.3 is explicit about the split.
        "flag": (FLAG_RIDGE_CV_SURFACE_FLAT
                 if width > RIDGE_FLAT_SURFACE_DECADES else None),
        "strongest_regularisation_in_set": float(members[-1]) if members else None,
        "per_exponent": detail,
    }


def ridge_stability_verdict(*, induced: dict[str, float],
                            envelopes: dict[str, Sequence[float]],
                            near_optimal: dict[str, Any],
                            expected_refits: int = V21_DISCOVERY_DONORS,
                            ) -> dict[str, Any]:
    """Section 3.3 step 4 -- the decision, over exactly the three named metrics.

    All three must be present and all three must pass. On success lambda is
    reported as weakly identified while the estimator is not, and the selected
    exponent is the strongest regularisation in the near-optimal set, chosen
    deterministically rather than by preference.
    """
    missing = sorted(set(RIDGE_STABILITY_METRICS) - set(induced))
    extra = sorted(set(induced) - set(RIDGE_STABILITY_METRICS))
    if missing or extra:
        _fail(STOP_RIDGE,
              "section 3.3 names exactly %r; missing %r, unexpected %r"
              % (list(RIDGE_STABILITY_METRICS), missing, extra))

    checked = within_envelope_per_metric(induced=induced, envelopes=envelopes,
                                         expected_refits=expected_refits)
    if not checked["all_within_envelope"]:
        _fail(STOP_RIDGE,
              "lambda-induced displacement exceeds the donor-resampling "
              "envelope for %r; the estimator is not identified across the "
              "near-optimal set" % (checked["failing_metrics"],))

    selected = near_optimal.get("strongest_regularisation_in_set")
    if selected is None:
        _fail(STOP_RIDGE, "the near-optimal set is empty")
    return {
        "identified": True,
        "selected_exponent": float(selected),
        "selection_rule": "strongest regularisation in the near-optimal set",
        "lambda_weakly_identified": bool(near_optimal.get("flag")
                                         == FLAG_RIDGE_CV_SURFACE_FLAT),
        "estimator_identified": True,
        "flag": near_optimal.get("flag"),
        "per_metric": checked["per_metric"],
    }


def lodo_envelope(displacements: Sequence[float]) -> float:
    """The maximum displacement across the leave-one-out refits."""
    values = np.asarray(list(displacements), dtype=np.float64)
    if values.size == 0:
        _fail(STOP_RIDGE, "an empty envelope cannot bound anything")
    if not np.isfinite(values).all():
        _fail(STOP_RIDGE, "envelope displacements must be finite")
    return float(np.max(np.abs(values)))


def within_envelope_per_metric(*, induced: dict[str, float],
                               envelopes: dict[str, Sequence[float]],
                               expected_refits: int | None = None,
                               ) -> dict[str, Any]:
    """Every metric passes on its own. Nothing is averaged or pooled.

    Averaging would let a large failure on one metric be hidden by agreement on
    the others, which is the masking this rule exists to prevent.
    """
    if set(induced) != set(envelopes):
        _fail(STOP_RIDGE,
              "induced displacements and envelopes cover different metrics: "
              "%r vs %r" % (sorted(induced), sorted(envelopes)))
    per_metric: dict[str, Any] = {}
    for metric in sorted(induced):
        series = list(envelopes[metric])
        if expected_refits is not None and len(series) != expected_refits:
            _fail(STOP_RIDGE,
                  "metric %r supplied %d refits, the contract requires all %d"
                  % (metric, len(series), expected_refits))
        bound = lodo_envelope(series)
        value = abs(float(induced[metric]))
        per_metric[metric] = {"induced_displacement": value,
                              "lodo_maximum_envelope": bound,
                              "n_refits": len(series),
                              "within_envelope": bool(value <= bound)}
    failing = sorted(m for m, r in per_metric.items()
                     if not r["within_envelope"])
    return {"per_metric": per_metric, "failing_metrics": failing,
            "all_within_envelope": not failing}


# --------------------------------------------------------------------------
# 6. The ridge bracketing search
# --------------------------------------------------------------------------

def v20_tie_choice(candidates: Sequence[float],
                   losses: dict[float, float]) -> float:
    """The frozen V20 tie rule, reused rather than redefined.

    `fit_t0_target` computes `tol = 1e-12 * max(1.0, abs(minloss))`, takes every
    exponent whose loss is within `minloss + tol`, and selects `choices[-1]` --
    the **largest** exponent among the near-ties, because the exponent grid is
    ascending. More regularization wins a tie.

    Stage D of the V21 ridge procedure says this rule is reused verbatim, so it
    is implemented here as V20 implements it. An earlier version of this module
    used the opposite convention -- smallest exponent, exact equality only --
    which would have silently disagreed with the frozen learner on any near-tie.
    """
    ordered = sorted(float(c) for c in candidates)
    if not ordered:
        _fail(STOP_RIDGE, "a tie rule needs at least one candidate")
    minloss = min(losses[c] for c in ordered)
    tol = V20_TIE_RELATIVE_TOLERANCE * max(1.0, abs(minloss))
    near = [c for c in ordered if losses[c] <= minloss + tol]
    return float(near[-1])


def ridge_bracket_search(evaluate: Callable[[float], float],
                         anchors: Iterable[float] = RIDGE_ANCHORS,
                         ) -> dict[str, Any]:
    """Stages A-D of section 3.1, implemented as written.

    Stage C is implemented **literally**: the minimum must remain strictly
    interior at every refinement round, and a round whose minimum lands on a
    refinement-interval endpoint is `STOP_RIDGE_OPTIMUM_ON_BRACKET_BOUNDARY`.

    That literal reading has a consequence worth stating plainly rather than
    quietly designing around, because it is a property of the contract and not
    of this code: a refinement round evaluates only `{c - step, c, c + step}`
    and requires the centre to win, so the accepted exponent can never move away
    from the coarse-stage minimum. Refinement can confirm or refuse; it cannot
    resolve. Across the frozen ladder 2, 1, 0.5, 0.25 that confines an
    acceptable optimum to within 0.125 of the coarse minimum, which on a grid
    of anchors spaced 4 apart will refuse most surfaces.

    `characterize_refinement_reach` quantifies this, and it is reported rather
    than repaired here: the V21 draft is not frozen, and choosing whichever
    reading makes a fixture pass would be exactly the kind of after-the-fact
    reinterpretation the contract exists to prevent.

    Every exponent visited is recorded with the stage that visited it, so the
    search is replayable and its determinism is checkable rather than asserted.
    """
    trace: list[dict[str, Any]] = []
    losses: dict[float, float] = {}

    def loss_at(exponent: float, stage: str) -> float:
        exponent = float(exponent)
        if exponent not in losses:
            value = float(evaluate(exponent))
            if not math.isfinite(value):
                _fail(STOP_RIDGE, "nonfinite CV loss at exponent %r" % exponent)
            losses[exponent] = value
            trace.append({"exponent": exponent, "cv_loss": value,
                          "stage": stage})
        return losses[exponent]

    for exponent in sorted(float(a) for a in anchors):
        loss_at(exponent, "anchor")

    # Stage B -- expand while the minimum sits at either end.
    expansions = {"low": 0, "high": 0}
    while True:
        grid = sorted(losses)
        best = v20_tie_choice(grid, losses)
        if best == grid[0] and expansions["low"] < RIDGE_MAX_EXPANSIONS:
            expansions["low"] += 1
            loss_at(grid[0] - RIDGE_EXPANSION_STEP, "expand_low")
            continue
        if best == grid[-1] and expansions["high"] < RIDGE_MAX_EXPANSIONS:
            expansions["high"] += 1
            loss_at(grid[-1] + RIDGE_EXPANSION_STEP, "expand_high")
            continue
        break

    grid = sorted(losses)
    best = v20_tie_choice(grid, losses)
    if best in (grid[0], grid[-1]):
        _fail(STOP_RIDGE_BOUNDARY,
              "the minimum remains at a bracket endpoint (exponent %r) after "
              "%r expansions; that is a misspecified design, not an "
              "under-searched one" % (best, expansions))

    # Stage C -- refine, requiring interiority at every round.
    rounds: list[dict[str, Any]] = []
    for step in RIDGE_REFINEMENT_STEPS:
        loss_at(best - step, "refine")
        loss_at(best + step, "refine")
        window = [best - step, best, best + step]
        chosen = v20_tie_choice(window, losses)
        rounds.append({"step": float(step), "centre": float(best),
                       "chosen": float(chosen),
                       "interior": bool(chosen == best)})
        if chosen != best:
            _fail(STOP_RIDGE_BOUNDARY,
                  "refinement round at step %r selected exponent %r, an "
                  "endpoint of the interval [%r, %r]; section 3.1 stage C "
                  "requires the minimum to remain interior at each round"
                  % (step, chosen, best - step, best + step))

    return {"selected_exponent": float(best),
            "selected_cv_loss": float(losses[best]),
            "expansions": expansions,
            "refinement_rounds": rounds,
            "n_refinement_rounds": len(rounds),
            "evaluations": len(losses),
            "trace": trace,
            "interior": True}


def characterize_refinement_reach(
        steps: Sequence[float] = RIDGE_REFINEMENT_STEPS) -> dict[str, Any]:
    """How far the true optimum may lie from the coarse minimum and still pass.

    A refinement round at `step` accepts only if the centre `c` beats both
    `c - step` and `c + step`. For a loss that is symmetric and increasing in
    `|e - e*|`, the centre wins exactly when `|c - e*| < step / 2`. The binding
    constraint is therefore the smallest step, and since the centre never moves,
    the whole ladder is only as permissive as its last round.

    Reported as a quantity rather than an opinion, so the contract question it
    raises can be settled on numbers.
    """
    steps = [float(s) for s in steps]
    per_round = [{"step": s, "max_offset_that_passes": s / 2.0} for s in steps]
    binding = min(s / 2.0 for s in steps)
    return {"refinement_steps": steps,
            "n_rounds": len(steps),
            "per_round": per_round,
            "binding_tolerance": binding,
            "anchor_spacing": float(RIDGE_EXPANSION_STEP),
            "fraction_of_anchor_spacing": binding / float(RIDGE_EXPANSION_STEP),
            "selected_exponent_can_move_during_refinement": False}


# --------------------------------------------------------------------------
# 7. Estimator selection: admissibility, ranking, deterministic tie-break
# --------------------------------------------------------------------------

def select_estimator(*, worst_case_displacement: dict[str, float],
                     biology_degradation: dict[str, float],
                     biology_envelope: float,
                     displacement_envelope: float,
                     declared_order: Sequence[str] = DECLARED_ESTIMATOR_ORDER,
                     ) -> dict[str, Any]:
    """Admissible on held-out biology, ranked on worst case, ties to earliest.

    Admissibility is what stops a candidate winning on robustness by flattening
    the score into noise: a perfectly stable estimator that has destroyed the
    held-out signal is not a better estimator.

    The result depends only on the declared order and the measured values, never
    on the iteration order of the dictionaries handed in, which is what makes
    the rerun and reordering tests meaningful.
    """
    order = list(declared_order)
    if len(set(order)) != len(order):
        _fail(STOP, "the declared order repeats a candidate")
    if not order:
        _fail(STOP, "no candidates declared")
    if set(order) != set(worst_case_displacement):
        _fail(STOP, "declared order and displacement candidates disagree: "
                    "%r vs %r" % (order, sorted(worst_case_displacement)))
    if set(order) != set(biology_degradation):
        _fail(STOP, "declared order and biology candidates disagree: %r vs %r"
              % (order, sorted(biology_degradation)))

    rows = []
    for rank, name in enumerate(order):
        degradation = float(biology_degradation[name])
        rows.append({"candidate": name, "declared_rank": rank,
                     "worst_case_displacement":
                         float(worst_case_displacement[name]),
                     "biology_degradation": degradation,
                     "biology_envelope": float(biology_envelope),
                     "admissible":
                         bool(degradation <= float(biology_envelope) + 1e-12)})

    admissible = [r for r in rows if r["admissible"]]
    if not admissible:
        _fail(STOP_NO_ADMISSIBLE,
              "no candidate preserves held-out biology within the envelope")

    best = min(r["worst_case_displacement"] for r in admissible)
    tied = [r for r in admissible
            if r["worst_case_displacement"] - best
            <= float(displacement_envelope) + 1e-12]
    selected = min(tied, key=lambda r: r["declared_rank"])

    return {
        "selected": selected["candidate"],
        "selection_rule":
            "admissible on held-out biology; ranked by worst-case "
            "displacement; ties within the displacement envelope broken to the "
            "earliest candidate in the declared order",
        "declared_order": order,
        "tie_break_applied": len(tied) > 1,
        "tied_candidates": [r["candidate"] for r in tied],
        "best_worst_case_displacement": float(best),
        "displacement_envelope": float(displacement_envelope),
        "inadmissible_candidates": [r["candidate"] for r in rows
                                    if not r["admissible"]],
        "table": rows,
    }
