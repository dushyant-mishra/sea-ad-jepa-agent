#!/usr/bin/env python3
"""Frozen operating-characteristic study for the R4 endpoint-selection rule.

Answers the decisive question in the work order:

    Does this procedure distinguish TRUE_COMMON_CONSTRUCT from
    NO_COMMON_CONSTRUCT at n = 28 without systematically manufacturing or
    suppressing qualification?

Convergence rate alone does not answer it. This runs the actual section 11
rule -- including the bootstrap reliability interval it gates on -- and reports
how often each terminal is reached when the truth is known.

FROZEN BEFORE RUNNING. Cells, replicate counts, bootstrap size, interval
method and the two reporting regimes are module constants, committed before any
result exists.

Section 4 of the work order is implemented as the two regimes:

    REGIME_AS_FROZEN   bootstrap non-convergence above the 5% allowance is
                       treated as the contract currently treats it, i.e. as
                       COMMON_FACTOR_NOT_ESTABLISHED -- a statement about the
                       biology.
    REGIME_RECLASSIFIED the same event is reported as
                       MEASUREMENT_ESTIMATOR_NOT_QUALIFIED -- a statement about
                       the estimator.

Running both and comparing them is what shows how much of the frozen rule's
output is driven by estimator adequacy rather than by the construct. The 5%
allowance itself is NOT relaxed anywhere in this file.

Synthetic only. No pathology value is read.

Stated simplifications, declared rather than discovered:
  - the section 10 two-seed replay is not simulated; it affects the UNRESOLVED
    rate, not the discrimination question this study exists to answer;
  - bootstrap intervals use BCa exactly as the contract specifies, including
    the jackknife acceleration, so the simulated rule is the real rule.

Cost, from the measured ~25 ms per matrix+fit:
  4 cells x 40 reps x 3 estimators x (150 bootstrap + 28 jackknife + 1 point)
  = 85,920 fits, ~36 min.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))

import t0_outcome_measurement_model_v1 as M                    # noqa: E402
import t0_measurement_estimator_qualification_v1 as Q          # noqa: E402
from test_t0_outcome_measurement_model_v1 import make_cohort   # noqa: E402

CONT = list(M.CONTINUOUS_IDX)
N28 = M.N_DISCOVERY

# --- FROZEN design ----------------------------------------------------------
CELLS = (
    dict(profile="STRONG", method_rho=0.75, comp_rho=0.55, missing=4,
         braak_ceiling=True, arm="nested", truth="TRUE_COMMON_CONSTRUCT"),
    dict(profile="STRONG", method_rho=0.25, comp_rho=0.15, missing=4,
         braak_ceiling=True, arm="nested", truth="TRUE_COMMON_CONSTRUCT"),
    dict(profile="WEAK", method_rho=0.75, comp_rho=0.55, missing=4,
         braak_ceiling=True, arm="nested", truth="TRUE_COMMON_CONSTRUCT"),
    dict(profile="NULL", method_rho=0.75, comp_rho=0.55, missing=4,
         braak_ceiling=True, arm="nested", truth="NO_COMMON_CONSTRUCT"),
)
REPS = 40
B = 150
SEED0 = 20260913

REGIME_AS_FROZEN = "AS_FROZEN"
REGIME_RECLASSIFIED = "RECLASSIFIED"
T_ESTIMATOR_NOT_QUALIFIED = "MEASUREMENT_ESTIMATOR_NOT_QUALIFIED"
T_NOT_ESTIMABLE = "MEASUREMENT_MODEL_NOT_ESTIMABLE_AT_N28"


def _fit_one(kind, values, idx=None):
    """Fit on the given donor index set; returns None if refused or improper."""
    v = values if idx is None else {c: values[c][idx] for c in values}
    try:
        R = M.latent_gaussian_matrix(v, CONT)
        f = Q.fit(kind, R, CONT)
    except (RuntimeError, np.linalg.LinAlgError):
        return None
    return f if f.converged else None


def _quantities(fit):
    w = np.ones(len(CONT)) / len(CONT)
    out = {"omega_equal": M.omega_w(fit, w),
           "theta12": M.theta_edge_value(fit, (12, 13))}
    try:
        out["omega_bartlett"] = M.omega_w(fit, M.bartlett_weights(fit))
    except (RuntimeError, np.linalg.LinAlgError):
        out["omega_bartlett"] = float("nan")
    return out


def run_rep(kind, cell, seed):
    lam = np.array(Q.LOADING_PROFILES[cell["profile"]]) + 1e-12
    values = make_cohort(seed=seed, factor_loadings=lam,
                         method_rho=cell["method_rho"],
                         compartment_rho=cell["comp_rho"],
                         braak_ceiling=cell["braak_ceiling"],
                         missing_biochem=cell["missing"], n=N28)
    point = _fit_one(kind, values)
    if point is None:
        return {"point_improper": True}
    pq = _quantities(point)

    idx = M.donor_resamples(N28, B, seed=seed)
    draws, failures = [], 0
    for b in range(B):
        f = _fit_one(kind, values, idx[b])
        if f is None:
            failures += 1
            continue
        draws.append(_quantities(f))
    nonconv = failures / float(B)

    jk = []
    for i in range(N28):
        keep = np.array([j for j in range(N28) if j != i])
        f = _fit_one(kind, values, keep)
        jk.append(_quantities(f) if f is not None else None)

    intervals, adjusted = {}, {}
    for key, label in (("omega_equal", "M1a"), ("omega_bartlett", "M2a")):
        d = np.array([x[key] for x in draws], dtype=np.float64)
        j = np.array([x[key] if x else np.nan for x in jk], dtype=np.float64)
        lo, hi, a_lo, a_hi = M.bca_interval(d, pq[key], j)
        intervals[label] = (lo, hi)
        adjusted[label] = (a_lo, a_hi)
    d12 = np.array([x["theta12"] for x in draws if x["theta12"] is not None],
                   dtype=np.float64)
    j12 = np.array([x["theta12"] if x else np.nan for x in jk],
                   dtype=np.float64)
    t12 = M.bca_interval(d12, pq["theta12"], j12)[:2] if len(d12) else None

    rel = {k: v for k, v in intervals.items()
           if np.isfinite(v[0]) and np.isfinite(v[1])}
    R = M.latent_gaussian_matrix(values, CONT)
    res = M.run_steps_1_to_5(values, R, CONT,
                             reliability_intervals=rel or None,
                             theta12_interval=t12)
    return {"point_improper": False, "nonconvergence": nonconv,
            "terminal_steps": res.terminal, "candidate": res.candidate,
            "omega_point": pq["omega_equal"],
            "interval_M1a": intervals["M1a"], "theta12_interval": t12,
            "adjusted_tails": adjusted}


def terminal_for(rep, regime):
    """Apply section 9 criterion 1 under the named regime."""
    if rep["point_improper"]:
        return (M.T_NO_FACTOR if regime == REGIME_AS_FROZEN
                else T_ESTIMATOR_NOT_QUALIFIED)
    if rep["nonconvergence"] > M.NONCONVERGENCE_ALLOWANCE:
        return (M.T_NO_FACTOR if regime == REGIME_AS_FROZEN
                else T_ESTIMATOR_NOT_QUALIFIED)
    return rep["terminal_steps"]


def main(out_path: Path) -> int:
    rows = []
    for cell in CELLS:
        for kind in Q.ESTIMATORS:
            reps = [run_rep(kind, cell, SEED0 + r) for r in range(REPS)]
            row = {"cell": Q.cell_key(cell), "truth": cell["truth"],
                   "estimator": kind, "reps": REPS, "bootstrap_B": B,
                   "point_improper_rate":
                       float(np.mean([r["point_improper"] for r in reps])),
                   "mean_bootstrap_nonconvergence":
                       float(np.mean([r["nonconvergence"] for r in reps
                                      if not r["point_improper"]] or [np.nan])),
                   "omega_true": Q.cell_truth(cell)["omega"]}
            for regime in (REGIME_AS_FROZEN, REGIME_RECLASSIFIED):
                terms = [terminal_for(r, regime) for r in reps]
                counts = {t: terms.count(t) / float(REPS) for t in set(terms)}
                row["terminals_" + regime] = counts
                passed = counts.get(M.T_PASS, 0.0)
                if cell["truth"] == "NO_COMMON_CONSTRUCT":
                    row["false_qualification_" + regime] = passed
                else:
                    row["correct_qualification_" + regime] = passed
                    row["false_rejection_" + regime] = 1.0 - passed
            rows.append(row)
            print("%-20s %-10s improper=%.2f  pass[frozen]=%.2f "
                  "pass[reclass]=%.2f"
                  % (row["cell"], kind, row["point_improper_rate"],
                     row["terminals_" + REGIME_AS_FROZEN].get(M.T_PASS, 0.0),
                     row["terminals_" + REGIME_RECLASSIFIED].get(M.T_PASS, 0.0)),
                  flush=True)
    payload = {
        "schema": "T0_MEASUREMENT_SELECTION_OPERATING_CHARACTERISTICS_V1",
        "frozen_before_running": True,
        "nonconvergence_allowance_unchanged": M.NONCONVERGENCE_ALLOWANCE,
        "reps": REPS, "bootstrap_B": B, "seed0": SEED0,
        "interval_method": "BCa_with_jackknife_acceleration",
        "regimes": [REGIME_AS_FROZEN, REGIME_RECLASSIFIED],
        "rows": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("\nwritten: %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1
                          else HERE.parent.parent / "docs/agent/evidence"
                          / "t0_measurement_selection_oc_20260912.json"))
