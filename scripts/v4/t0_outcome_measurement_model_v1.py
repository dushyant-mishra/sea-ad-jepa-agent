#!/usr/bin/env python3
"""Executor for the frozen R4 outcome-measurement contract.

Contract: docs/agent/T0_OUTCOME_MEASUREMENT_ACCESS_AMENDMENT_20260912.md at R4
(`2a964820`). This module implements that contract and nothing else. Where the
contract is silent on an implementation detail, the choice is marked
`CONTRACT_GAP_FILLED` in a comment and listed in `SPECIFICATION_GAPS` so it is
visible rather than silent.

Authorization scope, enforced in `load_declared_indicators`:
  six declared columns (idx 5, 13, 21, 22, 25, 26) plus the already-authorized
  AT8 endpoint (idx 12) and donor id (idx 0), on the 28 DISCOVERY donors only,
  against the source authenticated at ebbe9bc0...

Nothing here touches expression, the fresh-12, the reader-oracle, the 18 spent
donors, or any undeclared pathology column.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

import numpy as np

STOP = "STOP_T0_OUTCOME_MEASUREMENT_REFUSED"

# --- frozen identities (contract section 1) ---------------------------------
SOURCE_SHA256 = "ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a"
HEADER_SHA256 = "88114843211d095dbf3ccbc91cc1add4172ca15f7fe6ced07f9ea679ae785385"
DONOR_SET_SHA256 = (
    "4395fec74bcf7abf192d731db3c827fa25cfde1b5297db4203b041984a780d33")

DONOR_ID_IDX = 0
AT8_AREA_IDX = 12          # already authorized, the incumbent M0a indicator
DECLARED_NEW_IDX = (5, 13, 21, 22, 25, 26)
DECLARED_IDX = (DONOR_ID_IDX, 5, AT8_AREA_IDX, 13, 21, 22, 25, 26)

COLUMN_NAME_SHA16 = {
    0: "b57785e06342c767",
    5: "3cdb1a3d64c2b379",
    12: "95870f7dd3210198",
    13: "af74c64ecc9be627",
    21: "cc296b538889eec5",
    22: "0716f02ae61547dd",
    25: "065f0168c900a054",
    26: "ea91a5c6edb80445",
}

ORDINAL_IDX = 5                                   # Braak
CONTINUOUS_IDX = (12, 13, 21, 22, 25, 26)         # estimand A indicator set

# contract section 7.3: the declared residual-covariance graph E
RESIDUAL_EDGES = ((12, 13), (21, 22), (25, 26))

N_DISCOVERY = 28
SPARSE_REFIT_TRIGGER = 21          # CONVENTION, contract section 4
NONCONVERGENCE_ALLOWANCE = 0.05    # CONVENTION, contract section 9.1
RELIABILITY_WIDTH_MAX = 0.25       # CONVENTION, contract section 11 step 2
MC_RELATIVE_SE = 0.10              # contract section 10
B_INITIAL = 4000                   # contract section 10
LAMBDA_BOUND = 0.999               # parameterization limit; an active
                                   # bound means an improper solution

SPECIFICATION_GAPS = (
    "fit_estimator=ULS_on_offdiagonals: the contract names a one-factor "
    "congeneric model on the latent-Gaussian matrix but does not name the "
    "discrepancy function. Unweighted least squares on the off-diagonal "
    "residuals is used because the copula construction supplies a correlation "
    "matrix and no raw-data likelihood. Flagged for confirmation; not a silent "
    "approximation.",
    "polyserial=olsson_two_step: the contract names polyserial estimation but "
    "not the estimator. Olsson's two-step estimator is used.",
)

# --- terminals (contract section 11 step 5) ---------------------------------
T_PASS = "PASS_T0_SUCCESSOR_ENDPOINT_QUALIFIED"
T_NO_SUCCESSOR = "NO_SUCCESSOR_ENDPOINT_QUALIFIED"
T_RELIABILITY = "MEASUREMENT_RELIABILITY_UNRESOLVED"
T_NO_FACTOR = "COMMON_FACTOR_NOT_ESTABLISHED"
T_STRUCTURE = "ASSOCIATION_STRUCTURE_UNRESOLVED"
T_UNRESOLVED = "UNRESOLVED"
ESTIMAND_A = "COMMON_DONOR_TAU_BURDEN__LATENT_GAUSSIAN_SCALE"


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


# ===========================================================================
# section 5.1 -- one coherent latent-Gaussian association estimator
# ===========================================================================

def spearman_to_latent(rho_s: float) -> float:
    """rho = 2 sin(pi rho_S / 6), inverting rho_S = (6/pi) arcsin(rho/2).

    Exact only under the Gaussian copula (contract section 5.1, named
    assumption).
    """
    return float(2.0 * math.sin(math.pi * float(rho_s) / 6.0))


def _rankdata(x: np.ndarray) -> np.ndarray:
    """Average ranks, ties shared. No scipy dependency."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=np.float64)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    d = float(np.sqrt(np.dot(a, a) * np.dot(b, b)))
    if d <= 0.0:
        return 0.0
    return float(np.dot(a, b) / d)


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    return _pearson(_rankdata(a), _rankdata(b))


def _normal_quantile(p: float) -> float:
    """Acklam-style inverse normal CDF, adequate for threshold estimation."""
    if p <= 0.0:
        return -np.inf
    if p >= 1.0:
        return np.inf
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _normal_pdf(z: float) -> float:
    if not np.isfinite(z):
        return 0.0
    return float(math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi))


def ordinal_thresholds(y: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Standard-normal thresholds from the ordinal marginal, plus category counts."""
    cats = np.unique(y)
    counts = [int(np.sum(y == c)) for c in cats]
    n = float(len(y))
    cum, taus = 0.0, []
    for c in counts[:-1]:
        cum += c / n
        taus.append(_normal_quantile(cum))
    return np.array(taus, dtype=np.float64), counts


def polyserial(x: np.ndarray, y: np.ndarray) -> float:
    """Olsson two-step polyserial correlation.  CONTRACT_GAP_FILLED.

    rho = r_xy * s_y / sum(phi(tau_j)).
    """
    taus, counts = ordinal_thresholds(y)
    if len(counts) < 2:
        _fail("ordinal indicator has a single category; thresholds not estimable")
    denom = sum(_normal_pdf(float(t)) for t in taus)
    if denom <= 0.0:
        _fail("ordinal thresholds degenerate; polyserial not estimable")
    r_xy = _pearson(x, y.astype(np.float64))
    s_y = float(np.std(y.astype(np.float64), ddof=1))
    rho = r_xy * s_y / denom
    return float(np.clip(rho, -0.999, 0.999))


def latent_gaussian_matrix(values: dict[int, np.ndarray],
                           order: Sequence[int]) -> np.ndarray:
    """Section 5.1: every entry estimates one latent-Gaussian correlation.

    `values` maps column index -> vector. Ordinal columns use polyserial;
    continuous pairs use the Spearman inversion. Pairwise-complete: a pair is
    computed on donors observed for both.
    """
    m = len(order)
    R = np.eye(m, dtype=np.float64)
    for i in range(m):
        for j in range(i + 1, m):
            ci, cj = order[i], order[j]
            a, b = values[ci], values[cj]
            ok = np.isfinite(a) & np.isfinite(b)
            if int(ok.sum()) < 3:
                _fail("pair (%d,%d) has fewer than 3 complete donors" % (ci, cj))
            if ci == ORDINAL_IDX:
                r = polyserial(b[ok], np.round(a[ok]).astype(int))
            elif cj == ORDINAL_IDX:
                r = polyserial(a[ok], np.round(b[ok]).astype(int))
            else:
                r = spearman_to_latent(spearman(a[ok], b[ok]))
            R[i, j] = R[j, i] = float(np.clip(r, -0.999, 0.999))
    return R


# ===========================================================================
# section 5.2 -- non-PD handling
# ===========================================================================

def min_eigenvalue(R: np.ndarray) -> float:
    return float(np.min(np.linalg.eigvalsh(R)))


def higham_nearest_pd(R: np.ndarray, *, tol: float = 1e-10,
                      max_iter: int = 200) -> tuple[np.ndarray, float]:
    """Higham alternating projections to the nearest correlation matrix.

    Returns (projected, frobenius_distance).
    """
    A = 0.5 * (R + R.T)
    dS = np.zeros_like(A)
    Y = A.copy()
    for _ in range(max_iter):
        Rk = Y - dS
        w, V = np.linalg.eigh(0.5 * (Rk + Rk.T))
        w = np.clip(w, tol, None)
        X = (V * w) @ V.T
        dS = X - Rk
        Y = X.copy()
        np.fill_diagonal(Y, 1.0)
        if min_eigenvalue(Y) > tol and np.max(np.abs(Y - X)) < tol:
            break
    np.fill_diagonal(Y, 1.0)
    w = np.linalg.eigvalsh(0.5 * (Y + Y.T))
    if float(np.min(w)) <= 0.0:                 # final safeguard
        Y = Y + (abs(float(np.min(w))) + tol) * np.eye(len(Y))
        d = np.sqrt(np.diag(Y))
        Y = Y / np.outer(d, d)
    return Y, float(np.linalg.norm(Y - R, "fro"))


# ===========================================================================
# section 7.3 -- structural degrees of freedom from the surviving graph
# ===========================================================================

def surviving_edges(surviving: Sequence[int]) -> tuple[tuple[int, int], ...]:
    s = set(surviving)
    return tuple(e for e in RESIDUAL_EDGES if e[0] in s and e[1] in s)


def structural_df(surviving: Sequence[int], *, include_ordinal: bool) -> int:
    """df = m(m-3)/2 - r, computed from the exact surviving graph.

    Never from p. Ordinal thresholds come from the univariate margin and do not
    enter the correlation-structure df (contract section 7.3).
    """
    m = len(surviving) + (1 if include_ordinal else 0)
    r = len(surviving_edges(surviving))
    return m * (m - 3) // 2 - r


# ===========================================================================
# section 7.4 -- congeneric one-factor fit with declared residual edges
# ===========================================================================

@dataclass
class FactorFit:
    converged: bool
    loadings: np.ndarray
    theta: np.ndarray            # residual covariance, diag 1-lambda^2
    order: tuple[int, ...]
    df: int
    edges: tuple[tuple[int, int], ...]
    discrepancy: float


def _implied(lam: np.ndarray, theta_off: dict[tuple[int, int], float],
             m: int, edge_pos: list[tuple[int, int]]) -> np.ndarray:
    S = np.outer(lam, lam)
    np.fill_diagonal(S, 1.0)
    for (a, b), key in zip(edge_pos, theta_off):
        S[a, b] += theta_off[key]
        S[b, a] = S[a, b]
    return S


def fit_congeneric(R: np.ndarray, order: Sequence[int], *,
                   include_ordinal: bool = False,
                   max_iter: int = 500) -> FactorFit:
    """ULS fit of a one-factor model with the declared residual edges.

    CONTRACT_GAP_FILLED: the contract names the model, not the discrepancy
    function. Unweighted least squares on off-diagonal residuals is used.
    """
    order = tuple(order)
    m = len(order)
    cont = [c for c in order if c != ORDINAL_IDX]
    edges = surviving_edges(cont)
    pos = {c: i for i, c in enumerate(order)}
    edge_pos = [(pos[a], pos[b]) for a, b in edges]
    mask = ~np.eye(m, dtype=bool)
    for a, b in edge_pos:                     # edges are free -> not residuals
        mask[a, b] = mask[b, a] = False

    # A FREE residual covariance means the model reproduces that entry exactly.
    # It is therefore solved analytically as theta_ab = R_ab - lam_a lam_b, not
    # optimized: putting it in the parameter vector while excluding those
    # entries from the discrepancy leaves it with no gradient, and it silently
    # stays at its start value. That defect produced theta == 0 and an omega
    # identical to one computed with no residual covariances at all.
    def unpack(v):
        return np.tanh(v[:m]) * LAMBDA_BOUND

    def theta_offdiag(lam):
        return {e: float(R[a, b] - lam[a] * lam[b])
                for e, (a, b) in zip(edges, edge_pos)}

    def loss(v):
        lam = unpack(v)
        S = _implied(lam, theta_offdiag(lam), m, edge_pos)
        d = (R - S)[mask]
        return float(np.dot(d, d))

    # deterministic start: first principal direction of R
    w, V = np.linalg.eigh(R)
    start_lam = V[:, -1] * math.sqrt(max(float(w[-1]), 1e-6))
    if start_lam.sum() < 0:
        start_lam = -start_lam
    start_lam = np.clip(start_lam, -0.95, 0.95)
    v = np.arctanh(start_lam / LAMBDA_BOUND)

    # Nelder-Mead-free deterministic coordinate descent with shrinking step.
    step, best = 0.5, loss(v)
    for _ in range(max_iter):
        improved = False
        for k in range(len(v)):
            for s in (step, -step):
                trial = v.copy()
                trial[k] += s
                c = loss(trial)
                if c < best - 1e-14:
                    v, best, improved = trial, c, True
        if not improved:
            step *= 0.5
            if step < 1e-8:
                break
    lam = unpack(v)
    off = theta_offdiag(lam)
    theta = np.zeros((m, m), dtype=np.float64)
    np.fill_diagonal(theta, 1.0 - lam ** 2)
    for (a, b), e in zip(edge_pos, edges):
        theta[a, b] = theta[b, a] = off[e]
    # Improper (Heywood-type) solutions must be refused, not accepted with a
    # near-zero residual variance. `LAMBDA_BOUND` is the parameterization's own
    # limit, so a loading sitting on it means the unconstrained optimum lies
    # outside the admissible region -- an identification failure, which is what
    # section 9 criterion 1 treats as non-convergence. The 1e-4 is numerical
    # slack for detecting an ACTIVE CONSTRAINT, not a scientific threshold.
    bound_active = bool(np.any(np.abs(lam) >= LAMBDA_BOUND - 1e-4))
    converged = bool(step < 1e-6 and not bound_active
                     and np.all(np.diag(theta) > 1e-3))
    return FactorFit(converged, lam, theta, order,
                     structural_df(cont, include_ordinal=include_ordinal),
                     edges, best)


def omega_w(fit: FactorFit, w: np.ndarray) -> float:
    """omega_w = (w'L)^2 / [(w'L)^2 + w'Theta w]  (contract section 7.4)."""
    num = float(np.dot(w, fit.loadings)) ** 2
    den = num + float(w @ fit.theta @ w)
    if den <= 0:
        return float("nan")
    return float(num / den)


def bartlett_weights(fit: FactorFit) -> np.ndarray:
    """w = (L' Th^-1 L)^-1 L' Th^-1  -- SR-2 scoring rule."""
    Ti = np.linalg.pinv(fit.theta)
    denom = float(fit.loadings @ Ti @ fit.loadings)
    if abs(denom) < 1e-12:
        _fail("Bartlett weights not identified; L'Theta^-1 L is singular")
    return (Ti @ fit.loadings) / denom


def score_determinacy(fit: FactorFit) -> float:
    """Correlation between the Bartlett score and the factor."""
    Ti = np.linalg.pinv(fit.theta)
    q = float(fit.loadings @ Ti @ fit.loadings)
    return float(math.sqrt(q / (1.0 + q))) if q > 0 else 0.0


# ===========================================================================
# section 10 -- Monte Carlo precision budget
# ===========================================================================

def required_B(alpha_star: float, r: float = MC_RELATIVE_SE) -> int:
    """B >= (1 - a*) / (a* r^2).  Controls relative MC SE of the TAIL
    PROBABILITY -- not the numerical precision of the quantile endpoint."""
    a = float(alpha_star)
    if not (0.0 < a < 1.0):
        _fail("alpha_star must lie in (0,1)")
    return int(math.ceil((1.0 - a) / (a * r * r)))


def percentile_interval(draws: np.ndarray, alpha: float = 0.025
                        ) -> tuple[float, float]:
    d = np.sort(np.asarray(draws, dtype=np.float64))
    d = d[np.isfinite(d)]
    if len(d) == 0:
        return float("nan"), float("nan")
    lo = d[max(0, int(math.floor(alpha * len(d))) - 1)]
    hi = d[min(len(d) - 1, int(math.ceil((1 - alpha) * len(d))) - 1)]
    return float(lo), float(hi)


def bca_interval(draws: np.ndarray, point: float, jackknife: np.ndarray,
                 alpha: float = 0.025) -> tuple[float, float, float, float]:
    """Returns (lo, hi, alpha_lo_adjusted, alpha_hi_adjusted)."""
    d = np.asarray(draws, dtype=np.float64)
    d = d[np.isfinite(d)]
    if len(d) < 10:
        return float("nan"), float("nan"), alpha, 1 - alpha
    prop = float(np.mean(d < point))
    prop = min(max(prop, 1.0 / (len(d) + 1)), 1.0 - 1.0 / (len(d) + 1))
    z0 = _normal_quantile(prop)
    jk = np.asarray(jackknife, dtype=np.float64)
    jk = jk[np.isfinite(jk)]
    if len(jk) >= 3:
        jbar = jk.mean()
        num = float(np.sum((jbar - jk) ** 3))
        den = 6.0 * float(np.sum((jbar - jk) ** 2)) ** 1.5
        a = num / den if den > 0 else 0.0
    else:
        a = 0.0
    out = []
    for q in (alpha, 1.0 - alpha):
        z = _normal_quantile(q)
        adj = z0 + (z0 + z) / max(1e-9, (1.0 - a * (z0 + z)))
        out.append(min(max(float(_normal_cdf(adj)), 1e-6), 1 - 1e-6))
    a_lo, a_hi = out
    ds = np.sort(d)
    lo = ds[max(0, int(math.floor(a_lo * len(ds))) - 1)]
    hi = ds[min(len(ds) - 1, int(math.ceil(a_hi * len(ds))) - 1)]
    return float(lo), float(hi), float(a_lo), float(1.0 - a_hi)


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(float(z) / math.sqrt(2.0)))


def donor_resamples(n: int, B: int, seed: int) -> np.ndarray:
    """Donor-level resampling only. Never cells, never within-donor values."""
    g = np.random.Generator(np.random.PCG64(int(seed)))
    return g.integers(0, n, size=(int(B), int(n)), dtype=np.int64)


def digest_indices(idx: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(idx, dtype=np.int64)
                          .tobytes()).hexdigest()


# ===========================================================================
# section 11 -- deterministic selection, steps 1-5
# ===========================================================================

@dataclass
class StepsResult:
    terminal: str
    candidate: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


def _standardize_with(train: np.ndarray, target: np.ndarray
                      ) -> np.ndarray:
    """Section 8: the map is estimated on `train` and applied to `target`."""
    mu = float(np.nanmean(train))
    sd = float(np.nanstd(train, ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        _fail("standardization map has nonpositive SD")
    return (target - mu) / sd


def run_steps_1_to_5(values: dict[int, np.ndarray], R: np.ndarray,
                     order: Sequence[int], *,
                     reliability_intervals: dict[str, tuple[float, float]] | None
                     = None,
                     theta12_interval: tuple[float, float] | None = None
                     ) -> StepsResult:
    """Steps 1-5 only. Never step 0 -- see section 5.2.1 termination note."""
    cont = [c for c in order if c != ORDINAL_IDX]

    # STEP 1 -- MM-C admissibility
    fit = fit_congeneric(R, cont, include_ordinal=False)
    if not fit.converged:
        return StepsResult(T_NO_FACTOR, detail={"reason": "mmc_not_converged"})
    if fit.df < 1:
        return StepsResult(T_NO_FACTOR,
                           detail={"reason": "not_overidentified", "df": fit.df})

    # STEP 2 -- reliability must be identified informatively.
    # Interval supplied by the caller (bootstrap); absent means unresolved.
    if reliability_intervals is None:
        return StepsResult(T_RELIABILITY, detail={"reason": "no_interval"})
    widths = {k: (hi - lo) for k, (lo, hi) in reliability_intervals.items()
              if np.isfinite(lo) and np.isfinite(hi)}
    admissible = [k for k, w in widths.items() if w <= RELIABILITY_WIDTH_MAX]
    if not admissible:
        return StepsResult(T_RELIABILITY,
                           detail={"reason": "interval_too_wide",
                                   "widths": widths})

    # STEP 3 -- parsimony of the scoring map, one declared exception.
    # Method dependence counts as ESTABLISHED only when the bootstrap interval
    # for theta_12 excludes zero. The caller supplies that interval; absent it
    # the exception cannot fire, which is the conservative direction.
    method_established = bool(
        theta12_interval is not None
        and np.isfinite(theta12_interval[0]) and np.isfinite(theta12_interval[1])
        and (theta12_interval[0] > 0.0 or theta12_interval[1] < 0.0))
    if method_established and "M2a" in admissible:
        chosen = "M2a"
    elif "M1a" in admissible:
        chosen = "M1a"
    else:
        chosen = sorted(admissible)[0]          # STEP 4, frozen order M1a<M2a
    return StepsResult(T_PASS, candidate=chosen,
                       detail={"df": fit.df, "edges": fit.edges,
                               "method_established": method_established})


def theta_edge_value(fit: FactorFit, edge: tuple[int, int]) -> float | None:
    """The fitted residual covariance on a declared edge, or None if the edge
    did not survive."""
    if edge not in fit.edges:
        return None
    i = fit.order.index(edge[0])
    j = fit.order.index(edge[1])
    return float(fit.theta[i, j])


# ===========================================================================
# access loader -- the authorization boundary
# ===========================================================================

def load_declared_indicators(rows: Sequence[Sequence[str]],
                             header: Sequence[str],
                             *, included_donors: set[str],
                             requested_idx: Sequence[int],
                             expected_source_sha256: str,
                             expected_donor_set_sha256: str,
                             source_bytes: bytes) -> dict[str, Any]:
    """Refuse before parsing: undeclared columns, wrong source, wrong donors.

    Mirrors the discipline of `t0_stage2b_discovery_at8_v1.load_role_numeric_at8`:
    the refusal happens before any value is converted.
    """
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != expected_source_sha256:
        _fail("source digest %s does not reproduce the authorized %s"
              % (actual, expected_source_sha256))

    undeclared = [i for i in requested_idx if i not in DECLARED_IDX]
    if undeclared:
        _fail("columns %s are not declared by the R4 amendment" % undeclared)

    for i in requested_idx:
        if i >= len(header):
            _fail("column index %d absent from the authenticated header" % i)
        got = hashlib.sha256(header[i].encode()).hexdigest()[:16]
        if got != COLUMN_NAME_SHA16[i]:
            _fail("column %d identity %s does not match declared %s"
                  % (i, got, COLUMN_NAME_SHA16[i]))

    values: dict[int, list[float]] = {i: [] for i in requested_idx
                                      if i != DONOR_ID_IDX}
    donors: list[str] = []
    skipped = 0
    for row in rows:
        did = row[DONOR_ID_IDX].strip()
        if did not in included_donors:
            skipped += 1
            continue                      # refused before any value is parsed
        donors.append(did)
        for i in requested_idx:
            if i == DONOR_ID_IDX:
                continue
            raw = row[i].strip() if i < len(row) else ""
            values[i].append(float(raw) if raw else float("nan"))

    if len(donors) != N_DISCOVERY:
        _fail("expected %d discovery donors, loaded %d"
              % (N_DISCOVERY, len(donors)))
    dsha = hashlib.sha256("\n".join(sorted(donors)).encode()).hexdigest()
    if dsha != expected_donor_set_sha256:
        _fail("donor set digest %s does not reproduce the frozen %s"
              % (dsha, expected_donor_set_sha256))

    return {
        "donors": donors,
        "values": {i: np.array(v, dtype=np.float64) for i, v in values.items()},
        "rows_outside_discovery_skipped_unread": skipped,
        "source_sha256": actual,
        "donor_set_sha256": dsha,
    }
