"""V74 Lane A -- candidate decision functions for the Stage-4 G2 successor.

DESIGN ARTIFACT. This module contains NO production margin and NO default margin.
Every candidate that needs a margin takes it as a required argument and REFUSES when
it is absent. That refusal is the whole point: S102 was created by an executor
silently supplying a deciding quantity the contract never fixed, and a module that
carries a default would recreate it.

Nothing here reads a substrate, a receipt, or a result. It operates on a vector of
per-donor values and on scalar summaries that a caller supplies.

THE RECOVERED QUANTITY (as implemented in scripts/v64/stage4_executor_v1.py, not as
described in prose anywhere):

  Delta_CVC_d = aggregate_delta(resid[d, CONTROL_A(e)], resid[d, CONTROL_B(e)],
                                gene=gene(CONTROL_A(e)),
                                promoter=promoter(CONTROL_A(e)),
                                weighting=GENE_BALANCED)
                for e in calib_edges
                     = {e : CONTROL_A(e) eligible} & {e : CONTROL_B(e) eligible}

  theta_CVC   = mean over donors d with a finite Delta_CVC_d
  boot        = 4000 donor-cluster bootstrap means, seed 20260929, sorted ascending

and the historical gate was

  G2_pass  <=>  boot exists and quantile(boot, 0.025) <= 0 <= quantile(boot, 0.975)

donor_bootstrap below reproduces that bootstrap exactly so that candidate decision
rules are compared on the same resampling object the historical gate used.
"""
from __future__ import annotations

import numpy as np

DEFAULT_REPLICATES = 4000
DEFAULT_SEED = 20260929

PASS = "PASS"
FAIL = "FAIL"
INDETERMINATE = "INDETERMINATE"
REFUSED = "REFUSED_INSUFFICIENT_EVIDENCE"
NOT_APPLICABLE = "NOT_APPLICABLE"


class MarginNotFrozen(Exception):
    """Raised when a candidate that requires a margin is called without one.

    This is deliberately an exception and not a default. A margin-requiring rule with
    no margin has no verdict, and inventing one here is the S102 defect.
    """


def _finite(per_donor_values):
    return np.asarray([v for v in per_donor_values
                       if v is not None and np.isfinite(v)], float)


def donor_bootstrap(per_donor_values, replicates=DEFAULT_REPLICATES, seed=DEFAULT_SEED):
    """Byte-for-byte the executor's donor cluster bootstrap. Donors are the only
    resampling unit. Returns None when fewer than two donors contribute, which every
    caller must treat as a refusal and never as a pass.
    """
    vals = _finite(per_donor_values)
    if len(vals) < 2:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(replicates, len(vals)))
    return np.sort(vals[idx].mean(1))


def summarise(per_donor_values, conf=0.95, replicates=DEFAULT_REPLICATES,
              seed=DEFAULT_SEED):
    """The continuous summary every candidate consumes.

    theta        point estimate of mu = E[Delta_CVC]
    lo, hi       two-sided percentile interval for mu at level conf
    half_width   (hi - lo) / 2, the precision of the estimate (question C)
    u_mag        upper confidence bound on |mu| = max(|lo|, |hi|). Conservative:
                 P(|mu| <= u_mag) >= conf whenever the interval covers mu.
    l_mag        lower confidence bound on |mu|: min(|lo|, |hi|) when the interval
                 excludes zero, else 0. This is what makes a three-valued verdict
                 possible -- it is the evidence that the drift is genuinely large.
    """
    vals = _finite(per_donor_values)
    boot = donor_bootstrap(vals, replicates=replicates, seed=seed)
    if boot is None:
        return dict(available=False, n_donors=int(len(vals)), theta=None, lo=None,
                    hi=None, half_width=None, u_mag=None, l_mag=None, donor_sd=None,
                    conf=conf)
    a = (1.0 - conf) / 2.0
    lo = float(np.quantile(boot, a))
    hi = float(np.quantile(boot, 1.0 - a))
    excludes_zero = (lo > 0.0) or (hi < 0.0)
    return dict(
        available=True, n_donors=int(len(vals)), theta=float(vals.mean()),
        lo=lo, hi=hi, half_width=float((hi - lo) / 2.0),
        u_mag=float(max(abs(lo), abs(hi))),
        l_mag=float(min(abs(lo), abs(hi))) if excludes_zero else 0.0,
        donor_sd=float(vals.std(ddof=1)) if len(vals) > 1 else None,
        conf=conf)


# ------------------------------------------------------------------ C1 (status quo)
def c1_null_significance(s, alpha=0.05):
    """CANDIDATE 1 -- classical two-sided null test; the historical implementation.

    Estimand mu. H0: mu = 0. PASS iff H0 is not rejected at level alpha.
    Margin parameter: alpha, a convention with no biological content.
    Documented defect: the acceptance region is |theta| < z * sd / sqrt(D), so it
    shrinks as 1/sqrt(D). Against any fixed nonzero drift the pass probability goes
    to zero with more donors, and it rises as the evidence gets noisier.
    """
    if not s["available"]:
        return dict(verdict=REFUSED, why="fewer than two contributing donors")
    if abs(1.0 - alpha - s["conf"]) > 1e-12:
        return dict(verdict=REFUSED,
                    why="summary confidence %r does not match alpha %r"
                        % (s["conf"], alpha))
    ok = (s["lo"] <= 0.0 <= s["hi"])
    return dict(verdict=PASS if ok else FAIL, statistic=s["theta"],
                interval=[s["lo"], s["hi"]], alpha=alpha,
                answers="QUESTION_A_CENTRING_ONLY")


# ------------------------------------------------------- C3 (point magnitude only)
def c3_absolute_point_magnitude(s, m_abs=None):
    """CANDIDATE 3 -- |theta| <= m_abs, ignoring uncertainty entirely.

    Estimand |mu|, estimated by the plug-in |theta|. Margin: m_abs, on the scale of
    the residualised gene-balanced correlation delta.
    Documented defect: it is C1's exact mirror image. C1 is all precision and no
    magnitude; this is all magnitude and no precision. A noisy theta that lands near
    zero passes, so the gate is most permissive where the calibration evidence is
    weakest. Retained as a reportable diagnostic, never as a gate.
    """
    if m_abs is None:
        raise MarginNotFrozen("c3_absolute_point_magnitude requires m_abs")
    if not s["available"]:
        return dict(verdict=REFUSED, why="fewer than two contributing donors")
    return dict(verdict=PASS if abs(s["theta"]) <= m_abs else FAIL,
                statistic=abs(s["theta"]), m_abs=m_abs,
                answers="QUESTION_B_MAGNITUDE_ONLY_IGNORES_PRECISION")


# ----------------------------------------- C2 / C4 (equivalence; the same decision)
def c4_magnitude_upper_bound(s, m_abs=None):
    """CANDIDATES 2 and 4 -- equivalence on the absolute scale.

    Estimand |mu|. Equivalence statement: H0: |mu| >= m_abs against H1: |mu| < m_abs.
    PASS iff u_mag = max(|lo|, |hi|) <= m_abs.

    This is ALGEBRAICALLY THE SAME RULE as TOST at level alpha using a (1 - 2*alpha)
    interval: TOST accepts exactly when the interval lies inside (-m, +m), which is
    exactly u_mag < m. C2 and C4 are therefore one candidate with two reporting
    conventions, and the upper-bound form is preferred because the number it reports
    -- "the control-versus-control discrepancy is at most u_mag" -- is the sentence
    the Stage-4 contract actually needs.

    Behaviour: u_mag -> |mu| as donors accumulate, so the gate becomes EASIER to pass
    as evidence grows whenever mu is genuinely small, and settles above m_abs when it
    is not. That is the correct shape for a gate certifying negligibility.
    """
    if m_abs is None:
        raise MarginNotFrozen("c4_magnitude_upper_bound requires m_abs")
    if not s["available"]:
        return dict(verdict=REFUSED, why="fewer than two contributing donors")
    return dict(verdict=PASS if s["u_mag"] <= m_abs else FAIL,
                statistic=s["u_mag"], m_abs=m_abs,
                answers="QUESTIONS_B_AND_C_JOINTLY_BUT_NOT_SEPARATELY")


# ---------------------------------------------------- C5 (standardised / scale free)
def c5_standardised_magnitude(s, d_star=None):
    """CANDIDATE 5 -- |mu| / sd_donor against a standardised margin d_star.

    Estimand: a Cohen-style standardised drift on the donor distribution of
    Delta_CVC_d. Margin: d_star, justifiable only by convention imported from the
    effect-size literature.
    Documented defect, and in this lane's judgement a disqualifying one: sd_donor is
    a property of the pipeline under test. A noisier pipeline has a larger sd and
    therefore a SMALLER standardised drift, so degrading the pipeline makes the
    false-green control easier to pass. Reported for completeness; not recommended.
    """
    if d_star is None:
        raise MarginNotFrozen("c5_standardised_magnitude requires d_star")
    if not s["available"] or not s.get("donor_sd"):
        return dict(verdict=REFUSED, why="donor dispersion unavailable")
    stat = abs(s["theta"]) / s["donor_sd"]
    return dict(verdict=PASS if stat <= d_star else FAIL, statistic=float(stat),
                d_star=d_star, answers="QUESTION_B_ON_A_PIPELINE_DEPENDENT_SCALE",
                perverse_incentive="a noisier pipeline passes more easily")


# ------------------------------------------------------------ C6 (relative to G1)
def c6_relative_to_primary(s, primary_lcb95=None, g1_passed=None, f=None):
    """CANDIDATE 6 -- the discrepancy must not be able to explain the claimed effect.

    Estimand: rho = |mu_CVC| / mu_primary, evaluated conservatively as
    u_mag(CVC) / LCB95(primary) so that numerator and denominator both move in the
    cautious direction. PASS iff rho_conservative <= f.

    Margin f is the ONLY margin in this candidate set with a derivation that is not a
    convention: f = 1 is the point at which the control-versus-control discrepancy is
    as large as the entire effect it would have to explain, which the Stage-4 design
    contract itself calls the point of non-interpretability. Any f < 1 is a safety
    factor and must be labelled a convention.

    Guards, all mandatory:
      * evaluated only when G1 passed; otherwise NOT_APPLICABLE, never PASS, because
        a null or negative primary makes the ratio meaningless rather than small.
      * LCB95(primary) must be strictly positive.
    Documented residual weakness: the denominator is the quantity under test, so a
    pipeline that manufactures a LARGER primary effect is granted a LARGER tolerated
    discrepancy. This candidate must never be the only gate.
    """
    if f is None:
        raise MarginNotFrozen("c6_relative_to_primary requires f")
    if g1_passed is None:
        raise MarginNotFrozen("c6_relative_to_primary requires an explicit G1 verdict")
    if not g1_passed:
        return dict(verdict=NOT_APPLICABLE,
                    why="G1 did not pass; the primary effect is not established and "
                        "the ratio has no denominator worth dividing by")
    if not s["available"]:
        return dict(verdict=REFUSED, why="fewer than two contributing donors")
    if primary_lcb95 is None or not np.isfinite(primary_lcb95) or primary_lcb95 <= 0:
        return dict(verdict=REFUSED, why="primary LCB95 is absent or non-positive")
    rho = s["u_mag"] / float(primary_lcb95)
    return dict(verdict=PASS if rho <= f else FAIL, statistic=float(rho), f=f,
                numerator=s["u_mag"], denominator=float(primary_lcb95),
                answers="QUESTION_B_RELATIVE_TO_THE_EFFECT_IT_WOULD_HAVE_TO_EXPLAIN")


# ------------------------------------------------ C7 (three-valued conjunctive form)
def c7_three_valued(s, m=None, scale="ABSOLUTE", primary_lcb95=None, g1_passed=None,
                    min_donors=None, min_calibration_edges=None,
                    calibration_edges=None):
    """CANDIDATE 7 -- the recommended SHAPE. The margin is still an input.

    Partitions the magnitude question into three reachable verdicts instead of two:

      PASS           u_mag <= m          the drift is demonstrably within the margin
      FAIL           l_mag >  m          the drift is demonstrably outside it
      INDETERMINATE  otherwise           the data cannot separate the two, and the
                                         run reports no confirmed Stage-4 result

    The third verdict exists because a two-valued gate must fold the precision
    question into one of the other two. The historical gate folded it into PASS,
    which is how an uninformative run became a green one. Folding it into FAIL is
    safer but still mislabels "we could not tell" as "the pipeline is broken".

    scale selects which margin applies. ABSOLUTE compares u_mag and l_mag to m
    directly; RELATIVE divides both by LCB95(primary) first, which lets the one
    derivable margin (f, see C6) drive a three-valued verdict.
    """
    if m is None:
        raise MarginNotFrozen("c7_three_valued requires a margin m")
    if scale not in ("ABSOLUTE", "RELATIVE"):
        raise ValueError("scale must be ABSOLUTE or RELATIVE")
    if not s["available"]:
        return dict(verdict=REFUSED, why="fewer than two contributing donors")
    if min_donors is not None and s["n_donors"] < min_donors:
        return dict(verdict=REFUSED,
                    why="donors contributing %d < required %d"
                        % (s["n_donors"], min_donors))
    if min_calibration_edges is not None:
        if calibration_edges is None:
            return dict(verdict=REFUSED, why="calibration edge count not supplied")
        if calibration_edges < min_calibration_edges:
            return dict(verdict=REFUSED,
                        why="calibration edges %d < required %d"
                            % (calibration_edges, min_calibration_edges))
    u, l = s["u_mag"], s["l_mag"]
    denom = 1.0
    if scale == "RELATIVE":
        if g1_passed is None:
            raise MarginNotFrozen("RELATIVE scale requires an explicit G1 verdict")
        if not g1_passed:
            return dict(verdict=NOT_APPLICABLE, why="G1 did not pass")
        if primary_lcb95 is None or not np.isfinite(primary_lcb95) or primary_lcb95 <= 0:
            return dict(verdict=REFUSED, why="primary LCB95 is absent or non-positive")
        denom = float(primary_lcb95)
    u, l = u / denom, l / denom
    if u <= m:
        v = PASS
    elif l > m:
        v = FAIL
    else:
        v = INDETERMINATE
    return dict(verdict=v, upper=float(u), lower=float(l), m=m, scale=scale,
                centring_interval=[s["lo"], s["hi"]], half_width=s["half_width"],
                answers="A_B_AND_C_REPORTED_SEPARATELY")
