#!/usr/bin/env python3
"""A candidate transport estimand for the V21 nested cross-fitted procedure.

The V21 power gate has to carry an effect from a 28-donor nested cross-fitted
discovery procedure into a prospective 12-donor confirmation design. The previous
coordinate, `delta = t / sqrt(n)` from the assembled HC3 regression, is not
established to transport: `t0_v21_crossfit_null_calibration_v1.py` measures the
assembled statistic's null spread at 1.304x nominal with a fixed ridge and 1.477x
with inner LOODO selection, so the HC3 standard error understates the procedure's
own variability and `t / sqrt(n)` overstates the effect.

This module defines the candidate that replaces it, and states the derivation
before any simulation, so that the simulations test a prediction rather than
decorate a choice.

--------------------------------------------------------------------------
1. What the confirmation test actually is
--------------------------------------------------------------------------

At confirmation the estimator is **frozen**. Each of the 12 donors is scored by a
fixed function refit on the 46 development donors; nothing is selected, tuned or
cross-fitted at confirmation. The confirmatory model is therefore an ordinary
fixed-predictor linear model,

    y = Z gamma + beta s + eps,    eps ~ N(0, sigma^2),
    Z = [1, age_c, age_c^2, sex]   (p_Z = 4 columns)

with the frozen score `s` as the predictor of interest. All the difficulty lives
on the discovery side, where `s` is built from the outcomes.

--------------------------------------------------------------------------
2. The estimand
--------------------------------------------------------------------------

Let `~` denote residualization on `Z` in the population. Define

    rho = Corr( y~ , s~ )

the **population partial correlation of the frozen score with the outcome, given
the frozen nuisance design**.

Three properties make it a transport coordinate, and all three are the reason it
was chosen over `t / sqrt(n)`:

- it is **free of n**. It is a property of the joint donor population and the
  frozen scoring function, not of how many donors were drawn;
- it is **invariant to positive rescaling** of the score, which matters because
  ridge changes the scale of `beta` freely;
- it contains **no standard error**. `rho_hat = <y~, s~> / (||y~|| ||s~||)` is a
  pure geometric quantity of the residualized data. The part of the previous
  coordinate that was measured to be broken simply does not appear in it.

--------------------------------------------------------------------------
3. Why it should transport, derived
--------------------------------------------------------------------------

For the fixed-predictor model above, the least-squares slope and its
noncentrality are

    beta_hat = <s~, y~> / ||s~||^2,     lambda = beta ||s~|| / sigma

Write sigma_s for the per-observation standard deviation of the residualized
predictor. Decomposing the outcome variance into the part explained by `s~` and
the rest gives

    rho = beta sigma_s / sqrt( beta^2 sigma_s^2 + sigma^2 )
    =>  beta sigma_s / sigma = rho / sqrt(1 - rho^2)

and since `s~` lies in the (n - p_Z)-dimensional orthogonal complement of `Z`,

    ||s~|| / sigma_s  ~=  sqrt(n - p_Z)

Therefore

    lambda(rho, n)  =  rho * sqrt(n - p_Z) / sqrt(1 - rho^2)                (*)

The statistic is a noncentral `t` with `df = n - p_Z - 1` and noncentrality (*).
Every `n` dependence is explicit, and `rho` carries none. That is exactly what a
transport coordinate has to look like: estimate `rho` once at discovery, put the
confirmation cohort's `n` into (*), read power off the distribution of the test
that will actually be run.

--------------------------------------------------------------------------
4. What must be shown before this is usable, and is NOT assumed here
--------------------------------------------------------------------------

The derivation above is for a *fixed* predictor. At discovery the predictor is
out-of-fold and the folds overlap heavily, so none of the following is implied by
the algebra and each is a simulation question:

  T1  Is `rho_hat` from out-of-fold scores calibrated under the null? The
      quantity must not inherit the variance inflation that broke the HC3 `t`.
  T2  Does `rho_hat` from 28 out-of-fold scores overstate the frozen estimator's
      true `rho` on fresh donors? Attenuation is acceptable and conservative;
      inflation is fatal.
  T3  End to end: is power projected from `rho_hat` at n = 12 no greater than the
      actual rejection rate of the frozen confirmatory test on fresh cohorts?
  T4  Does any of this move under ridge selection, leverage profile, or donor
      heterogeneity?
  T5  Negative control: when the transport condition is deliberately violated,
      does the projection visibly fail? A check that cannot fail is not a check.

`t0_v21_transport_estimand_study_v1.py` runs these. Until it does and the results
support the derivation, `EFFECT_TRANSPORT_STATUS` stays OPEN.

Nothing in this module reads AT8, opens a partition, or authorizes anything.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

STOP = "STOP_T0_V21_TRANSPORT_ESTIMAND_REFUSED"

NUISANCE_COLUMNS = 4          # [1, age_c, age_c^2, sex]
ESTIMAND_NAME = "frozen_score_partial_correlation_given_nuisance_v1"


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def residualize(values: np.ndarray, design: np.ndarray) -> np.ndarray:
    """Project `values` onto the orthogonal complement of `design`."""
    q, _ = np.linalg.qr(np.asarray(design, dtype=np.float64))
    v = np.asarray(values, dtype=np.float64)
    return v - q @ (q.T @ v)


def partial_correlation(*, y: np.ndarray, nuisance: np.ndarray,
                        score: np.ndarray) -> float:
    """`rho_hat`: the sample partial correlation of `score` with `y` given `nuisance`.

    No standard error appears. This is the whole point of the estimand: the HC3
    standard error is the quantity measured to misbehave under cross-fit
    dependence, and it is absent here.
    """
    y_r = residualize(y, nuisance)
    s_r = residualize(score, nuisance)
    ny, ns = float(np.linalg.norm(y_r)), float(np.linalg.norm(s_r))
    if ny <= 0.0 or ns <= 0.0:
        _fail("a residualized vector has zero norm; rho is undefined")
    rho = float(np.dot(y_r, s_r) / (ny * ns))
    return max(-1.0, min(1.0, rho))


def noncentrality(rho: float, n: int,
                  nuisance_columns: int = NUISANCE_COLUMNS) -> float:
    """`lambda = rho sqrt(n - p_Z) / sqrt(1 - rho^2)`, equation (*)."""
    rho = float(rho)
    if not -1.0 < rho < 1.0:
        _fail("rho must lie strictly inside (-1, 1); got %r" % rho)
    residual_space = int(n) - int(nuisance_columns)
    if residual_space < 1:
        _fail("no residual space at n = %d with %d nuisance columns"
              % (n, nuisance_columns))
    return rho * math.sqrt(residual_space) / math.sqrt(1.0 - rho * rho)


def implied_t(rho: float, n: int,
              nuisance_columns: int = NUISANCE_COLUMNS) -> float:
    """The OLS `t` that a sample partial correlation `rho` corresponds to.

    This is an exact algebraic identity for a fixed predictor, and it is **not**
    the same expression as `noncentrality`:

        t = r sqrt(n - p_Z - 1) / sqrt(1 - r^2)

    The residual degrees of freedom of the *full* model appear here, because the
    predictor column is also estimated. `noncentrality` uses `n - p_Z` instead,
    because there the quantity being scaled is the residualized predictor's norm,
    which spans an (n - p_Z)-dimensional space. Conflating the two inflates every
    implied `t` by sqrt((n-4)/(n-5)) -- 2.1% at n = 28 -- which is small enough to
    pass unnoticed and large enough to bias a null-calibration check.

    Verified against real OLS fits in
    `test_t0_v21_transport_estimand_v1.py::test_the_partial_correlation_to_t_identity`.
    """
    rho = float(rho)
    if not -1.0 < rho < 1.0:
        _fail("rho must lie strictly inside (-1, 1); got %r" % rho)
    df = int(n) - int(nuisance_columns) - 1
    if df < 1:
        _fail("no residual degrees of freedom at n = %d" % n)
    return rho * math.sqrt(df) / math.sqrt(1.0 - rho * rho)


def parametric_power(*, rho: float, n: int, alpha: float,
                     nuisance_columns: int = NUISANCE_COLUMNS) -> dict[str, Any]:
    """Power of the fixed-predictor `t` test at this `rho` and `n`.

    A reference calculation. The production gate calibrates against the frozen
    Freedman-Lane permutation procedure by simulation, because that is the test
    that will actually decide; this is the analytic companion used to check that
    the simulation and the algebra agree.
    """
    df = int(n) - int(nuisance_columns) - 1
    if df < 1:
        return {"estimable": False, "n": int(n), "residual_df": df}
    lam = noncentrality(rho, n, nuisance_columns)
    critical = float(stats.t.isf(alpha, df))
    return {"estimable": True, "estimand": ESTIMAND_NAME,
            "rho": float(rho), "n": int(n), "residual_df": df,
            "noncentrality": lam, "t_critical": critical,
            "alpha": float(alpha),
            "power": float(stats.nct.sf(critical, df, lam))}


def rho_for_power(*, target_power: float, n: int, alpha: float,
                  nuisance_columns: int = NUISANCE_COLUMNS) -> float:
    """The smallest `rho` reaching `target_power` at this `n`. Monotone bisection."""
    low, high = 0.0, 0.999
    for _ in range(200):
        mid = 0.5 * (low + high)
        p = parametric_power(rho=mid, n=n, alpha=alpha,
                             nuisance_columns=nuisance_columns)
        if not p.get("estimable"):
            _fail("power is not estimable at n = %d" % n)
        if p["power"] < target_power:
            low = mid
        else:
            high = mid
    return float(high)
