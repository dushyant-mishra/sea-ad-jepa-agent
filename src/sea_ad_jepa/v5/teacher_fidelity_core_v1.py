"""Core estimator for the teacher-fidelity test, frozen by protocol v5.

The protocol is `docs/agent/V29_TEACHER_FIDELITY_FROZEN_PROTOCOL_V5_20260927.md`
(sha256 fe429ede1aa9c1960f8c60a379d17b98ab5882ae07a9063681219ea857c2e362). This
module implements it and nothing else; any behaviour not specified there is a
defect in this module, not a licence.

TWO SPACES, KEPT APART

  MODEL SPACE       negative-binomial GLM on the RAW nonnegative readout count,
                    with log D as an offset. The response is never centered,
                    residualised or rescaled - a centered count can be negative
                    and is not an NB response.

  EVALUATION SPACE  within-stratum Spearman between observed count and the
                    fitted model's predicted mean.

  Predictors ARE leave-one-out centered within stratum, because that is what
  confines the comparison to one donor and one brain region and it transfers to
  a held-out donor. It touches only predictor values, so it is preprocessing,
  not outcome leakage. The readout is never centered: within a stratum the
  centering is a positive affine map, which preserves ranks, so a rank statistic
  is invariant to it and it would buy nothing while forcing a transductive
  design.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.stats import spearmanr

MIN_STRATUM = 20
PSEUDOCOUNT = 0.5


def clr(counts: np.ndarray, pseudo: float = PSEUDOCOUNT) -> np.ndarray:
    """Centred log-ratio over a program's own partner counts.

    Scale-invariant only WITHOUT a pseudocount. With log(x + pseudo), scaling
    x by c does not factor out unless pseudo scales too, so at the one-to-four
    molecule counts these programs actually have, capture efficiency leaks in.
    That is precisely why the synthetic gate has a sparse arm.
    """
    lg = np.log(counts + pseudo)
    return lg - lg.mean(axis=1, keepdims=True)


def loo_center_within_stratum(x: np.ndarray, strata: np.ndarray) -> np.ndarray:
    """Leave-one-out centering, per stratum, column-wise.

    x_i - (S - x_i)/(n - 1)  =  x_i·n/(n-1) - S/(n-1)
    A positive affine map within a stratum, so it preserves within-stratum
    ranks. Applied to predictors only.
    """
    out = np.array(x, dtype=np.float64, copy=True)
    if out.ndim == 1:
        out = out[:, None]
    for s in np.unique(strata):
        m = strata == s
        n = int(m.sum())
        if n < 2:
            out[m] = 0.0
            continue
        blk = out[m]
        tot = blk.sum(axis=0, keepdims=True)
        out[m] = blk - (tot - blk) / (n - 1)
    return out


class ModelFallback(RuntimeError):
    """The negative-binomial fit failed.

    A failed fit must NOT become an apparently successful result through an
    unreported change of statistical model. The previous version silently
    dropped to Poisson on any exception, so a run whose NB fits all failed would
    have produced numbers indistinguishable from a healthy one. Fail closed; the
    caller decides whether a Poisson fallback is acceptable and records it.
    """


def _fit_nb(y, X, log_offset, allow_poisson_fallback=False):
    """NB GLM on raw counts with a fixed offset. Fails CLOSED by default."""
    import statsmodels.api as sm
    Xc = sm.add_constant(X, has_constant="add")
    try:
        aux = sm.GLM(y, Xc, family=sm.families.Poisson(),
                     offset=log_offset).fit()
        mu = np.maximum(aux.fittedvalues, 1e-9)
        # method-of-moments dispersion, bounded away from degeneracy
        num = ((y - mu) ** 2 - mu).sum()
        den = (mu ** 2).sum()
        alpha = float(np.clip(num / den if den > 0 else 0.0, 1e-6, 50.0))
        model = sm.GLM(y, Xc, family=sm.families.NegativeBinomial(alpha=alpha),
                       offset=log_offset).fit()
        return model, alpha, "negative_binomial"
    except Exception as exc:
        if not allow_poisson_fallback:
            raise ModelFallback(
                f"negative-binomial fit failed ({type(exc).__name__}: {exc}); "
                "refusing to substitute Poisson silently") from exc
        model = sm.GLM(y, Xc, family=sm.families.Poisson(),
                       offset=log_offset).fit()
        return model, None, "poisson_FALLBACK"


def _predict(model, X, log_offset):
    import statsmodels.api as sm
    return model.predict(sm.add_constant(X, has_constant="add"),
                         offset=log_offset)


def within_stratum_spearman(y, yhat, strata):
    """Spearman inside each stratum; returns {stratum: rho}."""
    out = {}
    for s in np.unique(strata):
        m = strata == s
        if m.sum() < MIN_STRATUM:
            continue
        a, b = y[m], yhat[m]
        if np.unique(a).size < 2 or np.unique(b).size < 2:
            continue
        rho = spearmanr(a, b).statistic
        if np.isfinite(rho):
            out[str(s)] = float(rho)
    return out


@dataclass
class TestResult:
    increment_per_donor: dict = field(default_factory=dict)
    median_increment: float = float("nan")
    fraction_donors_positive: float = float("nan")
    n_eval_donors: int = 0
    n_strata_used: int = 0
    dropped_small_strata: int = 0
    permutation_p: float = float("nan")
    n_permutations: int = 0
    dispersion_alpha: float = float("nan")
    model_families_used: tuple = ()
    poisson_fallbacks: int = 0


def run_directed_test(*, y_count, log_D, controls, state, strata, donors,
                      fit_mask, eval_mask, n_perm=999, seed=0) -> TestResult:
    """One directed predictor -> readout test, exactly as protocol v5 specifies.

    y_count   raw nonnegative readout partner counts, never transformed
    log_D     the frozen offset
    controls  control design matrix (uncentered; centered here)
    state     S_P columns (uncentered; centered here)
    strata    donor x operator label per nucleus
    donors    donor identity per nucleus
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y_count, dtype=np.float64)

    sizes = {s: int((strata == s).sum()) for s in np.unique(strata)}
    small = {s for s, n in sizes.items() if n < MIN_STRATUM}
    keep = ~np.isin(strata, list(small)) if small else np.ones(y.shape, bool)

    Xc = loo_center_within_stratum(np.asarray(controls, float), strata)
    Xs = loo_center_within_stratum(np.asarray(state, float), strata)

    f = fit_mask & keep
    e = eval_mask & keep
    res = TestResult(dropped_small_strata=len(small),
                     n_strata_used=int(np.unique(strata[e]).size),
                     n_eval_donors=int(np.unique(donors[e]).size),
                     n_permutations=n_perm)
    if f.sum() < 50 or e.sum() < MIN_STRATUM:
        return res

    families = []

    def increment(Xs_use):
        m0, _, fam0 = _fit_nb(y[f], Xc[f], log_D[f])
        m1, alpha, fam1 = _fit_nb(y[f], np.hstack([Xc[f], Xs_use[f]]), log_D[f])
        families.extend((fam0, fam1))
        p0 = _predict(m0, Xc[e], log_D[e])
        p1 = _predict(m1, np.hstack([Xc[e], Xs_use[e]]), log_D[e])
        r0 = within_stratum_spearman(y[e], p0, strata[e])
        r1 = within_stratum_spearman(y[e], p1, strata[e])
        common = sorted(set(r0) & set(r1))
        if not common:
            return {}, alpha
        # per stratum, then median within donor, then across donors
        s2d = {}
        for s in common:
            idx = np.flatnonzero((strata == s) & e)
            s2d.setdefault(str(donors[idx[0]]), []).append(r1[s] - r0[s])
        return {d: float(np.median(v)) for d, v in s2d.items()}, alpha

    per_donor, alpha = increment(Xs)
    if not per_donor:
        return res
    vals = np.asarray(list(per_donor.values()), dtype=float)
    res.increment_per_donor = per_donor
    res.median_increment = float(np.median(vals))
    res.fraction_donors_positive = float(np.mean(vals > 0))
    res.dispersion_alpha = float(alpha) if alpha is not None else float("nan")
    res.model_families_used = tuple(sorted(set(families)))
    res.poisson_fallbacks = sum(1 for x in families if x.endswith("FALLBACK"))

    # within-stratum permutation of the state, preserving everything else
    ge = 1
    for _ in range(n_perm):
        perm = np.arange(y.size)
        for s in np.unique(strata):
            m = np.flatnonzero(strata == s)
            perm[m] = rng.permutation(m)
        pd_, _ = increment(Xs[perm])
        if pd_:
            nv = np.median(list(pd_.values()))
            if nv >= res.median_increment:
                ge += 1
    res.permutation_p = ge / (n_perm + 1)
    return res


def benjamini_hochberg(pvals, q=0.05):
    """Return the boolean reject vector at FDR q, order preserved."""
    p = np.asarray(pvals, dtype=float)
    n = p.size
    order = np.argsort(p)
    thresh = q * (np.arange(1, n + 1) / n)
    passed = p[order] <= thresh
    k = np.flatnonzero(passed)
    out = np.zeros(n, dtype=bool)
    if k.size:
        cut = k.max()
        out[order[: cut + 1]] = True
    return out
