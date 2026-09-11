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

**The planning effect.** The empirical influence minimum across the 28 refits,
conditional on all of them agreeing in sign, and required to be no further from
zero than the full estimate. It is a sensitivity minimum over the donors actually
observed. It is **not** a statistical lower confidence bound, and the code says
so in the field name rather than only in a comment.

**Power.** Calibrated by simulation against the frozen HC3-studentized
Freedman-Lane permutation test -- the procedure that will actually decide -- not
against a parametric noncentral `t`. `project_power` is retained as a planning
approximation and is deliberately not decision-capable.

**The cross-fit artifact.** The gate consumes a sealed artifact carrying all 28
fold records, donor identity and a digest. It does not accept a bare score
vector, which an in-sample predictor could have been passed as.

**Standardization.** `delta = t_n / sqrt(n)`, where `n` is the size of the
sample that produced `t_n`. The full effect divides by sqrt(28); a 27-donor
influence refit divides by sqrt(27), not sqrt(28). It is stated here, applied
through one function, and pinned by a test, because it is a frozen equation and
not something to be reinterpreted once results exist.
"""

from __future__ import annotations

import hashlib
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
STOP_INVALID_INPUT = "STOP_INPUT_STRUCTURALLY_INVALID"
STOP_ARTIFACT = "STOP_CROSS_FIT_ARTIFACT_NOT_VALID"

# Frozen by the contract. Geometry is asserted, never inferred from what arrives.
V21_DISCOVERY_DONORS = 28
V21_CONFIRMATION_DONORS = 12
NUISANCE_RANK = 4           # [1, age_c, age_c^2, sex]
P_FULL = NUISANCE_RANK + 1  # plus the score column
ALPHA = 0.025
TARGET_POWER = 0.80

# p_upper = (1 + #{null >= t_obs}) / (B + 1), so the smallest attainable p-value
# is 1/(B+1) and rejecting at alpha requires B >= ceil(1/alpha) - 1 = 39.
MIN_PERMUTATIONS_FOR_ALPHA = int(math.ceil(1.0 / ALPHA)) - 1
FL_PERMUTATIONS_FROZEN = 9999
POWER_SIMULATIONS_FROZEN = 2000
POWER_SIMULATION_SEED = 20260911

RIDGE_ANCHORS = (-8.0, -4.0, 0.0, 4.0, 8.0)
RIDGE_EXPANSION_STEP = 4.0
RIDGE_MAX_EXPANSIONS = 3
RIDGE_REFINEMENT_STEPS = (2.0, 1.0, 0.5, 0.25)
RIDGE_REFINEMENT_ROUNDS = 4
# A round moves the centre by at most its step, so total movement is bounded by
# the sum of the ladder: 2 + 1 + 0.5 + 0.25 = 3.75, strictly less than the
# anchor spacing of 4. Refinement therefore cannot migrate out of the basin the
# coarse stage identified.
MAX_REFINEMENT_MOVEMENT = float(sum(RIDGE_REFINEMENT_STEPS))
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

def _require_structural_validity(name: str, x: Any, n: int) -> np.ndarray:
    """Structural invalidity fails closed. It is never an estimability result.

    A malformed array is a bug in the caller, not a statement about whether a
    quantity can be estimated from valid data. Merging the two lets a defect be
    reported as a legitimate scientific answer.
    """
    array = np.asarray(x, dtype=np.float64)
    if array.ndim != 1:
        _fail(STOP_INVALID_INPUT,
              "%s must be 1-D; got %d dimensions" % (name, array.ndim))
    if array.size != n:
        _fail(STOP_INVALID_INPUT,
              "%s has length %d, expected %d" % (name, array.size, n))
    if not np.isfinite(array).all():
        _fail(STOP_INVALID_INPUT, "%s contains nonfinite values" % name)
    return array


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
                # Recorded in full, not just counted: the artifact validates
                # training-set identity, and a count cannot show that.
                "train_indices": tuple(int(i) for i in self.train),
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
        # Renamed after external review. The old name was
        # `ridge_selected_inside_each_fold`, which became true merely because a
        # callback had been supplied -- it asserted nesting rather than
        # evidencing it. These two fields record what was actually observed and
        # claim nothing beyond it.
        "fold_ridge_exponents_recorded": fold_ridge_exponent is not None,
        "fold_ridge_exponents_vary": len(distinct) > 1,
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
        _fail(STOP_INVALID_INPUT,
              "y and the out-of-fold scores must be matching 1-D arrays; got "
              "%r and %r" % (y.shape, scores.shape))
    if not (np.isfinite(y).all() and np.isfinite(scores).all()):
        _fail(STOP_INVALID_INPUT,
              "y and the out-of-fold scores must be finite")

    # INVALID and NOT_ESTIMABLE are different answers and must not be merged.
    #
    # The frozen `nuisance_design` raises `ValueError` for three distinct causes:
    # structurally malformed inputs (nonfinite values, wrong dimensionality,
    # length mismatch), a sex coding that is not complete binary 0/1, and a
    # rank-deficient design. Only the last is an estimability statement. An
    # earlier version of this function caught all three and returned
    # `{estimable: False}`, which would have let a malformed array be reported as
    # a legitimate "cannot estimate" -- the same defect class already repaired
    # once in T0.
    #
    # So structure is validated first and fails closed, and only genuine
    # degeneracy is allowed to become a non-estimable result.
    age_arr = _require_structural_validity("age", age, n=int(len(y)))
    sex_arr = _require_structural_validity("sex", sex, n=int(len(y)))
    unique_sex = np.unique(sex_arr)
    if unique_sex.size != 2 or not np.array_equal(unique_sex,
                                                  np.array([0.0, 1.0])):
        _fail(STOP_INVALID_INPUT,
              "sex must be complete binary 0/1 under the frozen V1 authority; "
              "got %r" % (unique_sex.tolist(),))
    try:
        nuisance, center = learner.nuisance_design(age_arr, sex_arr,
                                                   age_center=age_center)
    except ValueError as error:
        # Structure and coding are already known good, so what remains is
        # genuine rank deficiency -- an estimability statement.
        return {"estimable": False,
                "reason": "rank-deficient nuisance design: %s" % error,
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

def choose_planning_effect(*, full_standardized_effect: float,
                           empirical_influence_minimum: float,
                           ) -> dict[str, Any]:
    """Whichever of the two is nearer zero. The bounding requirement, enforced.

    The empirical influence minimum is a sensitivity minimum over the donors
    actually observed. Nothing guarantees it sits between zero and the full
    estimate: every refit can land further from zero than the full fit, and using
    it then would be **anti-conservative** -- the opposite of what the quantity is
    named for. A previous version computed this comparison and ignored it, so the
    bound was conservative in name only.

    Kept as a pure function so both branches are testable directly rather than by
    hunting for a rare fixture.
    """
    full = float(full_standardized_effect)
    influence = float(empirical_influence_minimum)
    bounded = abs(influence) <= abs(full) + 1e-12
    return {
        "planning_standardized_effect": influence if bounded else full,
        "influence_minimum_is_bounded_by_full": bool(bounded),
        "planning_effect_source": ("empirical_influence_minimum" if bounded
                                   else "full_estimate_because_the_influence_"
                                        "minimum_was_less_conservative"),
    }


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

    influence_minimum = (float(values.min()) if signs[0] > 0
                         else float(values.max()))
    full_delta = full["standardized_effect"]
    chosen = choose_planning_effect(
        full_standardized_effect=full_delta,
        empirical_influence_minimum=influence_minimum)

    return {
        "full_n": full["n"],
        "full_t": full["t_observed"],
        "full_standardized_effect": full_delta,
        "n_influence_refits": len(refits),
        "influence_refits": refits,
        "refit_n": n - 1,
        "direction": "positive" if signs[0] > 0 else "negative",
        "direction_consistent": True,
        # Named for what it is: a sensitivity minimum, not a confidence bound.
        "empirical_influence_minimum": influence_minimum,
        "influence_minimum_is_bounded_by_full":
            chosen["influence_minimum_is_bounded_by_full"],
        "planning_standardized_effect":
            float(chosen["planning_standardized_effect"]),
        "planning_effect_source": chosen["planning_effect_source"],
        "is_a_statistical_lower_confidence_bound": False,
    }


# --------------------------------------------------------------------------
# 4. Power projection
# --------------------------------------------------------------------------

def project_power(*, standardized_effect_value: float, n_target: int,
                  p_full: int = P_FULL, alpha: float = ALPHA,
                  ) -> dict[str, Any]:
    """A planning approximation. **Not the gate, and not decision-capable.**

    `delta = t / sqrt(n)`, so the statistic expected at `n_target` is
    `delta * sqrt(n_target)`, and power follows from the noncentral `t` at the
    target's residual degrees of freedom.

    External review was right that this does not demonstrate 80% power. It holds
    only if the residualized predictor geometry and error structure carry over to
    the new cohort, and it assumes a parametric `t` null that the actual
    confirmatory test does not use. It is kept for sizing intuition, and every
    returned dictionary says what it is; `power_gate` calls
    `simulate_power_freedman_lane` instead.
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
        "is_planning_approximation_only": True,
        "not_decision_capable": True,
        "n_target": int(n_target), "residual_df": df, "alpha": float(alpha),
        "standardized_effect": float(standardized_effect_value),
        "expected_t": expected, "t_critical": critical,
        "power": power, "target_power": TARGET_POWER,
        "meets_target": bool(power >= TARGET_POWER),
        "noncentrality_needed_for_target_power": needed,
        "standardized_effect_needed": needed / math.sqrt(float(n_target)),
    }


# --------------------------------------------------------------------------
# 4b. The cross-fit artifact -- what the gate is allowed to consume
# --------------------------------------------------------------------------

def _digest_cross_fit(donor_ids: Sequence[Any], y: np.ndarray, age: np.ndarray,
                      sex: np.ndarray, scores: np.ndarray,
                      folds: Sequence[dict[str, Any]]) -> str:
    h = hashlib.sha256()
    h.update(b"T0_V21_CROSS_FIT_ARTIFACT_V1")
    for donor in donor_ids:
        h.update(("|id:%s" % (donor,)).encode("utf-8"))
    for name, array in (("y", y), ("age", age), ("sex", sex),
                        ("scores", scores)):
        h.update(("|%s:" % name).encode("utf-8"))
        h.update(np.ascontiguousarray(array, dtype=np.float64).tobytes())
    for fold in folds:
        h.update(("|fold:%d:%d:%s:%s"
                  % (fold["held_out_index"], fold["n_train"],
                     ",".join(str(i) for i in fold["train_indices"]),
                     repr(fold["fold_ridge_exponent"]))).encode("utf-8"))
        h.update(np.float64(fold["out_of_fold_prediction"]).tobytes())
    return h.hexdigest()


def seal_cross_fit(*, oof_result: dict[str, Any], donor_ids: Sequence[Any],
                   y: np.ndarray, age: np.ndarray, sex: np.ndarray,
                   ) -> dict[str, Any]:
    """Bind out-of-fold scores to the folds and donors that produced them.

    The gate previously accepted a bare score vector, so an in-sample predictor
    could have been handed to it and a verdict computed. No code can prove a
    caller's closure did not leak -- closures are opaque -- but a decision can be
    made to require *evidence of structure*: 28 donors, each held out exactly
    once, each training set the complement of its held-out donor, donor identity
    recorded, and a digest over all of it. A naked array cannot satisfy that, and
    tampering afterwards breaks the digest.
    """
    n = int(oof_result.get("n_donors", -1))
    if n != V21_DISCOVERY_DONORS:
        _fail(STOP_ARTIFACT, "the contract fixes %d discovery donors; the "
              "cross-fit reports %d" % (V21_DISCOVERY_DONORS, n))

    ids = list(donor_ids)
    if len(ids) != n:
        _fail(STOP_ARTIFACT, "%d donor identifiers for %d donors"
              % (len(ids), n))
    if len(set(map(str, ids))) != n:
        _fail(STOP_ARTIFACT, "donor identifiers are not unique")

    y = _require_structural_validity("y", y, n=n)
    age = _require_structural_validity("age", age, n=n)
    sex = _require_structural_validity("sex", sex, n=n)

    folds = list(oof_result.get("folds", []))
    if len(folds) != n:
        _fail(STOP_ARTIFACT, "%d fold records for %d donors" % (len(folds), n))

    everything = set(range(n))
    held_seen: set[int] = set()
    for fold in folds:
        held = int(fold["held_out_index"])
        train = tuple(int(i) for i in fold["train_indices"])
        if held in held_seen:
            _fail(STOP_ARTIFACT, "donor %d held out more than once" % held)
        held_seen.add(held)
        if len(train) != n - 1 or set(train) != everything - {held}:
            _fail(STOP_ARTIFACT,
                  "fold %d does not train on the exact complement of its "
                  "held-out donor" % held)
        if not math.isfinite(float(fold["out_of_fold_prediction"])):
            _fail(STOP_ARTIFACT, "fold %d has a nonfinite prediction" % held)
    if held_seen != everything:
        _fail(STOP_ARTIFACT, "not every donor was held out exactly once")

    scores = np.asarray(oof_result["oof_predictions"], dtype=np.float64)
    if scores.shape != (n,):
        _fail(STOP_ARTIFACT, "the score vector has shape %r, expected (%d,)"
              % (scores.shape, n))
    by_fold = np.array([f["out_of_fold_prediction"]
                        for f in sorted(folds,
                                        key=lambda f: f["held_out_index"])],
                       dtype=np.float64)
    if not np.array_equal(scores, by_fold):
        _fail(STOP_ARTIFACT,
              "the score vector does not match the per-fold predictions")

    artifact = {
        "kind": "t0_v21_cross_fit_artifact_v1",
        "n_donors": n,
        "donor_ids": tuple(str(d) for d in ids),
        "y": y, "age": age, "sex": sex, "oof_scores": scores,
        "folds": tuple(dict(f) for f in folds),
        "fold_ridge_exponents": tuple(oof_result.get("fold_ridge_exponents",
                                                     ())),
        "fold_ridge_exponents_recorded":
            bool(oof_result.get("fold_ridge_exponents_recorded", False)),
        "fold_ridge_exponents_vary":
            bool(oof_result.get("fold_ridge_exponents_vary", False)),
    }
    artifact["artifact_digest"] = _digest_cross_fit(
        artifact["donor_ids"], y, age, sex, scores, artifact["folds"])
    return artifact


def verify_cross_fit_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Recompute the digest and re-check the structure before any inference."""
    if not isinstance(artifact, dict) or \
            artifact.get("kind") != "t0_v21_cross_fit_artifact_v1":
        _fail(STOP_ARTIFACT,
              "the power gate requires a sealed cross-fit artifact, not a bare "
              "score vector")
    for key in ("donor_ids", "y", "age", "sex", "oof_scores", "folds",
                "artifact_digest"):
        if key not in artifact:
            _fail(STOP_ARTIFACT, "the artifact is missing %r" % key)
    recomputed = _digest_cross_fit(
        artifact["donor_ids"], artifact["y"], artifact["age"],
        artifact["sex"], artifact["oof_scores"], artifact["folds"])
    if recomputed != artifact["artifact_digest"]:
        _fail(STOP_ARTIFACT,
              "the artifact digest does not recompute; it was altered after "
              "sealing (recorded %s, recomputed %s)"
              % (artifact["artifact_digest"][:16], recomputed[:16]))
    return {"verified": True, "artifact_digest": artifact["artifact_digest"],
            "n_donors": int(artifact["n_donors"])}


# --------------------------------------------------------------------------
# 4c. Power calibrated to the frozen Freedman-Lane confirmatory test
# --------------------------------------------------------------------------

def _frozen_inference():
    """The frozen Freedman-Lane inference path, loaded like the other frozen code."""
    if str(FROZEN_V20) not in sys.path:
        sys.path.insert(0, str(FROZEN_V20))
    module = __import__("t0_inference_safe_v1")
    resolved = Path(module.__file__).resolve()
    if resolved.parent != FROZEN_V20.resolve():
        _fail(STOP, "t0_inference_safe_v1 resolved to %s, outside the "
                    "committed frozen V20 directory" % resolved)
    return module


def frozen_permutations(n: int, n_permutations: int, seed: int) -> np.ndarray:
    """Deterministic permutation block for the Freedman-Lane test."""
    if n_permutations < MIN_PERMUTATIONS_FOR_ALPHA:
        _fail(STOP,
              "p_upper is (1 + #{null >= t}) / (B + 1), so the smallest "
              "attainable p-value is 1/(B+1); rejecting at alpha = %r needs "
              "B >= %d, not %d"
              % (ALPHA, MIN_PERMUTATIONS_FOR_ALPHA, n_permutations))
    rng = np.random.default_rng(seed)
    return np.array([rng.permutation(n) for _ in range(n_permutations)],
                    dtype=np.int64)


def power_meets_target(*, power: float, monte_carlo_standard_error: float,
                       target_power: float = TARGET_POWER) -> dict[str, Any]:
    """The gate clears on the lower Monte Carlo limit, not the point estimate.

    Power here is measured by simulation, so it carries its own error. Comparing
    the point estimate to 80% would let simulation noise be what passes the gate:
    at 2000 replicates the standard error near 0.8 is about 0.9 percentage
    points, and at a few hundred it is several. The lower limit is what must
    clear.

    A pure function so both branches are testable without having to manufacture a
    simulated fixture that happens to straddle the boundary.
    """
    power = float(power)
    se = float(monte_carlo_standard_error)
    lower = max(0.0, power - 1.96 * se)
    return {"power": power, "monte_carlo_standard_error": se,
            "power_lower_95": lower, "target_power": float(target_power),
            "meets_target": bool(power - 1.96 * se >= target_power)}


def _simulate_statistics(*, z, signal_to_noise, n_simulations, n_permutations,
                         seed, alpha, inference):
    """Shared simulation core: returns the observed statistics and rejections."""
    n = z.shape[0]
    permutations = frozen_permutations(n, n_permutations, seed)
    rng = np.random.default_rng(seed + 1)
    q, _ = np.linalg.qr(z)

    statistics: list[float] = []
    rejections = 0
    for _ in range(int(n_simulations)):
        x = rng.normal(size=n)
        x_resid = x - q @ (q.T @ x)
        norm = float(np.linalg.norm(x_resid))
        if norm <= 0.0:
            continue
        # theta scaled so the underlying per-observation signal-to-noise is
        # exactly `signal_to_noise`, with unit error variance.
        theta = float(signal_to_noise) * math.sqrt(n) / norm
        y = theta * x + rng.normal(size=n)
        result = inference.safe_studentized_fl(y, z, x, permutations)
        if not result.get("estimable"):
            continue
        statistics.append(float(result["t_observed"]))
        if float(result["p_upper"]) <= alpha:
            rejections += 1
    return statistics, rejections


def measure_hc3_statistic_scaling(*, age: np.ndarray, sex: np.ndarray,
                                  n_simulations: int, n_permutations: int,
                                  seed: int) -> dict[str, Any]:
    """How much of `snr * sqrt(n)` the HC3 statistic actually reaches, measured.

    HC3 divides squared residuals by `(1 - h)^2`, so its standard error grows with
    leverage. Mean leverage is `p / n`, which is 0.179 at n = 28 and 0.417 at
    n = 12, and the statistic shrinks accordingly. The shrinkage is a property of
    the design, so it is measured on the design rather than assumed away.

    This is what makes `delta = t / sqrt(n)` safe to carry between cohort sizes:
    divide it out at the discovery design to recover the underlying effect, and
    apply it again at the confirmation design.
    """
    inference = _frozen_inference()
    _, learner = _frozen()
    n = int(len(np.asarray(age)))
    age = _require_structural_validity("age", age, n=n)
    sex = _require_structural_validity("sex", sex, n=n)
    z, _ = learner.nuisance_design(age, sex)

    statistics, _ = _simulate_statistics(
        z=z, signal_to_noise=1.0, n_simulations=n_simulations,
        n_permutations=n_permutations, seed=seed, alpha=ALPHA,
        inference=inference)
    if not statistics:
        _fail(STOP, "no replicate was estimable while measuring HC3 scaling")
    mean_t = float(np.mean(statistics))
    naive = math.sqrt(n)
    return {"n": n, "mean_observed_t": mean_t,
            "naive_noncentrality_at_unit_snr": naive,
            "hc3_scaling": mean_t / naive,
            "mean_leverage": float(z.shape[1] + 1) / n,
            "n_simulations": int(n_simulations)}


def signal_to_noise_from_observed_effect(
        *, observed_standardized_effect: float, age: np.ndarray,
        sex: np.ndarray, n_simulations: int, n_permutations: int,
        seed: int) -> dict[str, Any]:
    """Invert the discovery design's HC3 scaling to recover the underlying effect."""
    scaling = measure_hc3_statistic_scaling(
        age=age, sex=sex, n_simulations=n_simulations,
        n_permutations=n_permutations, seed=seed)
    factor = scaling["hc3_scaling"]
    if factor <= 0.0:
        _fail(STOP, "the measured HC3 scaling is not positive")
    return {"observed_standardized_effect": float(observed_standardized_effect),
            "discovery_hc3_scaling": factor,
            "signal_to_noise": float(observed_standardized_effect) / factor,
            "discovery_design": scaling}


def simulate_power_freedman_lane(
        *, signal_to_noise: float, age: np.ndarray,
        sex: np.ndarray, n_simulations: int, n_permutations: int, seed: int,
        alpha: float = ALPHA) -> dict[str, Any]:
    """Power of the **actual** confirmatory test, estimated by simulation.

    The gate previously projected the effect into a noncentral `t`. That is not
    the test that will be run: V20's broad-state inference, and therefore V21's,
    is HC3-studentized Freedman-Lane permutation. Power calibrated against a
    different procedure than the one that decides is not power.

    There is no closed form for the permutation test's power, so it is measured:
    simulate donor-level data at the target cohort size on the frozen nuisance
    design, with the predictor scaled so the per-observation standardized effect
    equals the planning effect, run the frozen procedure, and count rejections.

    The Monte Carlo uncertainty is reported. A point estimate of power carries
    its own error and should not be compared to 80% as if it were exact.
    """
    inference = _frozen_inference()
    _, learner = _frozen()

    n = int(len(np.asarray(age)))
    age = _require_structural_validity("age", age, n=n)
    sex = _require_structural_validity("sex", sex, n=n)
    z, _ = learner.nuisance_design(age, sex)
    if n - (z.shape[1] + 1) < 1:
        _fail(STOP, "no residual degrees of freedom at n = %d" % n)

    snr = float(signal_to_noise)
    statistics, rejections = _simulate_statistics(
        z=z, signal_to_noise=snr, n_simulations=n_simulations,
        n_permutations=n_permutations, seed=seed, alpha=alpha,
        inference=inference)
    usable = len(statistics)
    if usable == 0:
        _fail(STOP, "no simulation replicate was estimable")

    power = rejections / usable
    se = math.sqrt(max(power * (1.0 - power), 0.0) / usable)
    verdict = power_meets_target(power=power, monte_carlo_standard_error=se,
                                 target_power=TARGET_POWER)
    mean_t = float(np.mean(statistics))
    naive = snr * math.sqrt(n)
    return {
        "test": "HC3-studentized Freedman-Lane permutation (frozen V20 engine)",
        "n_target": n, "alpha": float(alpha),
        "signal_to_noise": snr,
        # What the statistic actually reaches, against what a naive
        # `snr * sqrt(n)` projection would assume. Below 1 at small n because
        # HC3 inflates the standard error as leverage rises.
        "mean_observed_t": mean_t,
        "naive_noncentrality": naive,
        "hc3_scaling": (mean_t / naive) if naive != 0.0 else None,
        "mean_leverage": float(z.shape[1] + 1) / n,
        "n_simulations": int(n_simulations), "usable_replicates": usable,
        "n_permutations": int(n_permutations),
        "smallest_attainable_p_value": 1.0 / (n_permutations + 1),
        "power": float(power),
        "monte_carlo_standard_error": float(se),
        "power_lower_95": verdict["power_lower_95"],
        "target_power": TARGET_POWER,
        "meets_target": verdict["meets_target"],
    }


def nested_permutation_null(
        *, n_donors: int,
        pipeline_factory: Callable[[np.ndarray], tuple],
        y: np.ndarray, age: np.ndarray, sex: np.ndarray,
        n_permutations: int, seed: int) -> dict[str, Any]:
    """A Freedman-Lane null for the discovery-side effect, over the whole nested
    procedure.

    Why this exists rather than trusting the assembled HC3 `t`. The 28
    out-of-fold predictions are **mutually dependent**: folds `i` and `j` share
    26 of their 27 training donors, so `score_i` is a function of `y_j` for every
    `j != i`. Per-donor honesty -- donor `i`'s prediction never sees donor `i`'s
    outcome -- holds and is tested elsewhere in this module, but it is a weaker
    property than joint independence across donors, and the single HC3 regression
    treats the 28 pairs as independent observations. The parametric `t` null is
    therefore not guaranteed at this sample size.

    Permuting resolves it without an independence assumption. Following the frozen
    Freedman-Lane construction, the reduced-model residuals are permuted while the
    nuisance fit stays fixed, and then the **entire nested procedure is re-run** on
    the permuted outcome -- all 28 folds, each with its own inner selection. That
    is what makes the null reflect the procedure rather than one regression inside
    it.

    `pipeline_factory(y_used)` returns `(train_fold, predict_held_out,
    fold_ridge_exponent_or_None)` built against the outcome handed to it, which is
    what allows the folds to be refit under each permutation.

    Cost is `(B + 1) * 28` fold fits, so `n_permutations` is a parameter here
    rather than a frozen constant; the production value belongs in the contract.
    """
    _, learner = _frozen()
    n = int(n_donors)
    y = _require_structural_validity("y", y, n=n)
    age = _require_structural_validity("age", age, n=n)
    sex = _require_structural_validity("sex", sex, n=n)
    if n_permutations < MIN_PERMUTATIONS_FOR_ALPHA:
        _fail(STOP,
              "the smallest attainable p-value is 1/(B+1); rejecting at alpha = "
              "%r needs B >= %d, not %d"
              % (ALPHA, MIN_PERMUTATIONS_FOR_ALPHA, n_permutations))

    z, _ = learner.nuisance_design(age, sex)
    coefficients, *_ = np.linalg.lstsq(z, y, rcond=None)
    fitted = z @ coefficients
    residual = y - fitted

    def statistic(outcome):
        train_fold, predict_held_out, exponent_of = pipeline_factory(outcome)
        folds = outer_lodo_oof(n_donors=n, train_fold=train_fold,
                               predict_held_out=predict_held_out,
                               fold_ridge_exponent=exponent_of,
                               expected_n_donors=n)
        effect = oof_effect(y=outcome, age=age, sex=sex,
                            oof_scores=folds["oof_predictions"])
        if not effect.get("estimable"):
            _fail(STOP, "a permutation replicate was not estimable: %s"
                  % effect.get("reason"))
        return float(effect["t_observed"])

    observed = statistic(y)
    rng = np.random.default_rng(seed)
    null = np.empty(int(n_permutations), dtype=np.float64)
    for i in range(int(n_permutations)):
        null[i] = statistic(fitted + residual[rng.permutation(n)])

    upper = (1 + int(np.sum(null >= observed))) / (len(null) + 1)
    return {
        "t_observed": observed,
        "n_permutations": int(n_permutations),
        "p_upper": float(upper),
        "smallest_attainable_p_value": 1.0 / (n_permutations + 1),
        "null_t": null,
        "construction": "Freedman-Lane residual permutation, with the full "
                        "28-fold nested procedure re-run under each permutation",
        "assumes_independent_out_of_fold_observations": False,
    }


def power_gate(*, artifact: dict[str, Any],
               confirmation_age: np.ndarray, confirmation_sex: np.ndarray,
               n_simulations: int = POWER_SIMULATIONS_FROZEN,
               n_permutations: int = FL_PERMUTATIONS_FROZEN,
               seed: int = POWER_SIMULATION_SEED) -> dict[str, Any]:
    """The whole gate, from a sealed cross-fit artifact to a verdict.

    Takes an artifact, never a bare score vector: the previous signature would
    have computed a verdict from an in-sample predictor handed to it directly.
    """
    verification = verify_cross_fit_artifact(artifact)
    bound = jackknife_minimum_effect(
        y=artifact["y"], age=artifact["age"], sex=artifact["sex"],
        oof_scores=artifact["oof_scores"])
    # The discovery statistic is HC3-deflated by its own design's leverage, and
    # the confirmation design deflates differently. Carrying `delta` across
    # cohort sizes unchanged would silently assume the two are the same. So the
    # projection is routed through the underlying effect instead.
    underlying = signal_to_noise_from_observed_effect(
        observed_standardized_effect=bound["planning_standardized_effect"],
        age=artifact["age"], sex=artifact["sex"],
        n_simulations=n_simulations, n_permutations=n_permutations, seed=seed)
    calibration = simulate_power_freedman_lane(
        signal_to_noise=underlying["signal_to_noise"],
        age=confirmation_age, sex=confirmation_sex,
        n_simulations=n_simulations, n_permutations=n_permutations, seed=seed)
    return {
        "artifact": verification,
        "planning_effect": bound,
        "underlying_effect": underlying,
        "calibration": calibration,
        "clears_gate": bool(calibration["meets_target"]),
    }


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
    """Stages A-D of section 3.1, as amended after the a89f4c3f external review.

    The previous wording required the minimum to remain interior at every
    refinement round. Implementing it showed the rule was degenerate: a round
    evaluates only `{c - step, c, c + step}` and required the centre to win, so
    the accepted exponent could never move away from the coarse minimum, and
    across the ladder 2, 1, 0.5, 0.25 an acceptable optimum had to lie within
    0.125 of an anchor spaced 4 apart. That is confirmation of a coarse guess,
    not refinement, and it would have refused almost every real surface.

    **Amended.** Each round selects the minimum of the three-point window under
    the frozen V20 tie rule and **recentres** on it. A round moves the centre by
    at most its step, so total movement is bounded by 3.75 -- strictly less than
    the anchor spacing -- and refinement cannot leave the basin the coarse stage
    found. Interiority is now checked against the **full evaluated grid**, which
    is the well-posedness property section 3.5 actually asks for, rather than
    against a three-point window.

    After the final round the centre beats `c +/- 0.25`, so on a unimodal surface
    the optimum is localised to within 0.125 -- now a resolution guarantee rather
    than an admission constraint.

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

    # Stage C -- refine, recentring on the winner at each round.
    coarse = best
    rounds: list[dict[str, Any]] = []
    for step in RIDGE_REFINEMENT_STEPS:
        loss_at(best - step, "refine")
        loss_at(best + step, "refine")
        window = [best - step, best, best + step]
        chosen = v20_tie_choice(window, losses)
        rounds.append({"step": float(step), "centre": float(best),
                       "chosen": float(chosen),
                       "moved": bool(chosen != best)})
        best = chosen

    # Stage D -- interiority of the full evaluated grid, not of a three-point
    # window. The window version made refinement a no-op; see the docstring.
    grid = sorted(losses)
    if best in (grid[0], grid[-1]):
        _fail(STOP_RIDGE_BOUNDARY,
              "stage C: refinement settled on exponent %r, an endpoint of the "
              "full evaluated grid [%r, %r]; refinement walked out of the "
              "bracket rather than settling inside it"
              % (best, grid[0], grid[-1]))

    movement = abs(float(best) - float(coarse))
    if movement > MAX_REFINEMENT_MOVEMENT + 1e-12:
        _fail(STOP_RIDGE,
              "refinement moved %r from the coarse minimum, beyond the %r the "
              "frozen ladder permits; the search is not behaving as specified"
              % (movement, MAX_REFINEMENT_MOVEMENT))

    return {"selected_exponent": float(best),
            "selected_cv_loss": float(losses[best]),
            "coarse_minimum": float(coarse),
            "refinement_movement": movement,
            "expansions": expansions,
            "refinement_rounds": rounds,
            "n_refinement_rounds": len(rounds),
            "evaluations": len(losses),
            "trace": trace,
            "interior": True}


def characterize_refinement_reach(
        steps: Sequence[float] = RIDGE_REFINEMENT_STEPS) -> dict[str, Any]:
    """What the amended refinement ladder can reach and resolve.

    Under the amended rule each round recentres, so the ladder both *moves* and
    *resolves*. Two quantities characterise it, and both are properties of the
    frozen steps rather than of any data:

    - **reach** -- the furthest the centre can travel from the coarse minimum,
      the sum of the steps. Bounded below the anchor spacing by construction, so
      refinement stays inside the basin the coarse stage identified.
    - **resolution** -- after the final round the centre beats `c +/- s_last`, so
      on a unimodal surface the optimum lies within `s_last / 2`.
    """
    steps = [float(s) for s in steps]
    reach = float(sum(steps))
    resolution = steps[-1] / 2.0
    return {"refinement_steps": steps,
            "n_rounds": len(steps),
            "maximum_reach": reach,
            "anchor_spacing": float(RIDGE_EXPANSION_STEP),
            "reach_stays_within_one_anchor_spacing":
                bool(reach < float(RIDGE_EXPANSION_STEP)),
            "resolution": resolution,
            "selected_exponent_can_move_during_refinement": True}


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
