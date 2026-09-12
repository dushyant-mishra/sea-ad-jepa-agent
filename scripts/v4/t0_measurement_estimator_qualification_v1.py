#!/usr/bin/env python3
"""Frozen estimator-qualification design for the R4 measurement model.

Blocker being addressed:
    MEASUREMENT_ESTIMATOR_NOT_YET_QUALIFIED_AT_REAL_N28_GEOMETRY

The 19-20% improper-solution rate measured at `5e583c1f` characterizes
ULS-on-off-diagonals with one parameterization on one synthetic parameter set.
It does not establish that n = 28 makes the latent tau measurement problem
impossible. This module decides that question prospectively, on synthetic data
only.

EVERYTHING IN THIS FILE IS FROZEN BEFORE IT IS RUN. The estimator family, the
DGP grid, the replicate counts and the reported metrics are module constants,
committed before any result is produced, so that nothing here can be chosen
after seeing an outcome.

What this module does NOT do:
  - it does not change the biological model, the indicator set, the declared
    residual-edge graph, or the endpoint-selection rule;
  - it does not read any pathology value;
  - it does not relax NONCONVERGENCE_ALLOWANCE.

Grid size was fixed from a measured cost of ~25 ms per (matrix + fit):
  main grid    24 cells x 300 reps x 3 estimators =  21,600 fits  ~9 min
  nested rule   4 cells x  40 reps x B=150 x 3    =  72,000 fits  ~30 min
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))

import t0_outcome_measurement_model_v1 as M            # noqa: E402
# The cohort generator lives with the fixture-geometry guard test, which is the
# authoritative assertion that it reproduces the real study shape. Importing it
# here rather than duplicating keeps the two from drifting apart.
from test_t0_outcome_measurement_model_v1 import make_cohort   # noqa: E402

CONT = list(M.CONTINUOUS_IDX)
N28 = M.N_DISCOVERY

# ===========================================================================
# FROZEN: the estimator family (section 1 of the work order)
# ===========================================================================
# Three defensible estimators for the already-frozen MM-C model. No model
# shopping: the model is fixed, only the discrepancy function varies.
#
#   uls        current -- unweighted least squares on off-diagonal residuals
#   ml         normal-theory ML discrepancy for a correlation structure,
#              log|S| + tr(R S^-1) - log|R| - m
#   uls_floor  ULS with an explicit residual-variance floor. The constraint is
#              stated, not hidden, and its effect on reliability is measured
#              rather than assumed. Expected direction: capping lambda lowers
#              the omega numerator while the floor raises w'Theta w, so the
#              constraint should bias omega DOWNWARD (conservative). Asserted
#              nowhere; reported as `omega_bias`.
ESTIMATORS = ("uls", "ml", "uls_floor")
RESIDUAL_VARIANCE_FLOOR = 0.05      # CONVENTION, declared before running

# ===========================================================================
# FROZEN: the DGP grid (section 2 of the work order)
# ===========================================================================
# Every cell is n = 28 and preserves the declared assay structure: six
# indicators, the three residual edges, measurement-semantic marginals.
LOADING_PROFILES = {
    "STRONG":   (0.82, 0.78, 0.70, 0.55, 0.66, 0.50),
    "MODERATE": (0.62, 0.59, 0.53, 0.41, 0.50, 0.38),
    "WEAK":     (0.41, 0.39, 0.35, 0.28, 0.33, 0.25),
    # NULL keeps the residual-edge structure but removes the common factor:
    # pairwise dependence exists, a shared construct does not. This is the
    # false-qualification case.
    "NULL":     (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
}
METHOD_RHO = (0.25, 0.75)
COMP_RHO = (0.15, 0.55)

CORE_MISSING, CORE_BRAAK = 4, True        # realistic defaults for core cells
REPS_MAIN = 300
REPS_NESTED = 40
B_NESTED = 150
SEED0 = 20260912


def frozen_grid() -> tuple[dict, ...]:
    """24 cells. Core is fully crossed; the extra arm varies nuisance shape."""
    cells = []
    for prof in LOADING_PROFILES:
        for mr in METHOD_RHO:
            for cr in COMP_RHO:
                cells.append(dict(profile=prof, method_rho=mr, comp_rho=cr,
                                  missing=CORE_MISSING, braak_ceiling=CORE_BRAAK,
                                  arm="core"))
    for prof in ("STRONG", "NULL"):
        for missing, braak in ((0, True), (8, True), (4, False), (0, False)):
            cells.append(dict(profile=prof, method_rho=0.75, comp_rho=0.35,
                              missing=missing, braak_ceiling=braak, arm="extra"))
    return tuple(cells)


GRID = frozen_grid()
NESTED_CELLS = ("STRONG/0.75/0.55", "STRONG/0.25/0.15",
                "NULL/0.75/0.55", "WEAK/0.75/0.55")


# ===========================================================================
# estimators
# ===========================================================================

def _theta_offdiag(R, lam, edge_pos, edges):
    return {e: float(R[a, b] - lam[a] * lam[b])
            for e, (a, b) in zip(edges, edge_pos)}


def _implied(lam, off, edge_pos, edges):
    S = np.outer(lam, lam)
    np.fill_diagonal(S, 1.0)
    for (a, b), e in zip(edge_pos, edges):
        S[a, b] = S[b, a] = S[a, b] + off[e]
    return S


def _discrepancy(kind: str, R, lam, off, edge_pos, edges, mask):
    S = _implied(lam, off, edge_pos, edges)
    if kind in ("uls", "uls_floor"):
        d = (R - S)[mask]
        return float(np.dot(d, d))
    w = np.linalg.eigvalsh(0.5 * (S + S.T))
    if float(np.min(w)) <= 1e-10:
        return 1e12                       # ML is undefined off the PD cone
    sign, logdet = np.linalg.slogdet(S)
    if sign <= 0:
        return 1e12
    m = len(lam)
    _, logdetR = np.linalg.slogdet(R)
    return float(logdet + np.trace(R @ np.linalg.inv(S)) - logdetR - m)


def fit(kind: str, R: np.ndarray, order: Sequence[int],
        max_iter: int = 500) -> M.FactorFit:
    """One fit of the frozen MM-C model under the named discrepancy."""
    order = tuple(order)
    m = len(order)
    cont = [c for c in order if c != M.ORDINAL_IDX]
    edges = M.surviving_edges(cont)
    pos = {c: i for i, c in enumerate(order)}
    edge_pos = [(pos[a], pos[b]) for a, b in edges]
    mask = ~np.eye(m, dtype=bool)
    for a, b in edge_pos:
        mask[a, b] = mask[b, a] = False

    bound = (math.sqrt(1.0 - RESIDUAL_VARIANCE_FLOOR) if kind == "uls_floor"
             else M.LAMBDA_BOUND)

    def unpack(v):
        return np.tanh(v) * bound

    def loss(v):
        lam = unpack(v)
        return _discrepancy(kind, R, lam, _theta_offdiag(R, lam, edge_pos, edges),
                            edge_pos, edges, mask)

    w, V = np.linalg.eigh(R)
    start = V[:, -1] * math.sqrt(max(float(w[-1]), 1e-6))
    if start.sum() < 0:
        start = -start
    start = np.clip(start, -0.9 * bound, 0.9 * bound)
    v = np.arctanh(start / bound)

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
    off = _theta_offdiag(R, lam, edge_pos, edges)
    theta = np.zeros((m, m))
    np.fill_diagonal(theta, 1.0 - lam ** 2)
    for (a, b), e in zip(edge_pos, edges):
        theta[a, b] = theta[b, a] = off[e]
    bound_active = bool(np.any(np.abs(lam) >= bound - 1e-4))
    converged = bool(step < 1e-6 and not bound_active
                     and np.all(np.diag(theta) > 1e-3))
    return M.FactorFit(converged, lam, theta, order,
                       M.structural_df(cont, include_ordinal=False), edges, best)


# ===========================================================================
# truth for a cell, so bias is measured against something real
# ===========================================================================

def cell_truth(cell: dict) -> dict:
    lam = np.array(LOADING_PROFILES[cell["profile"]], dtype=np.float64)
    rhos = [cell["method_rho"], cell["comp_rho"], cell["comp_rho"]]
    theta = np.diag(1.0 - lam ** 2)
    for (a, b), rho in zip([(0, 1), (2, 3), (4, 5)], rhos):
        c = math.sqrt(1 - lam[a] ** 2) * math.sqrt(1 - lam[b] ** 2) * rho
        theta[a, b] = theta[b, a] = c
    w = np.ones(6) / 6.0
    num = float(np.dot(w, lam)) ** 2
    omega = num / (num + float(w @ theta @ w))
    return {"lam": lam, "theta": theta, "omega": omega,
            "theta_edges": np.array([theta[a, b]
                                     for a, b in [(0, 1), (2, 3), (4, 5)]])}


def cell_key(cell: dict) -> str:
    return "%s/%.2f/%.2f" % (cell["profile"], cell["method_rho"],
                             cell["comp_rho"])


# ===========================================================================
# section 3 -- operating characteristics
# ===========================================================================

def run_cell(cell: dict, kind: str, reps: int, seed0: int) -> dict:
    truth = cell_truth(cell)
    w = np.ones(6) / 6.0
    proper = 0
    lam_s, th_s, om_s, sc_s = [], [], [], []
    om_all = [float("nan")] * reps          # every cohort, NaN when improper
    for r in range(reps):
        seed = seed0 + r
        v = make_cohort(seed=seed,
                        factor_loadings=np.array(
                            LOADING_PROFILES[cell["profile"]]) + 1e-12,
                        method_rho=cell["method_rho"],
                        compartment_rho=cell["comp_rho"],
                        braak_ceiling=cell["braak_ceiling"],
                        missing_biochem=cell["missing"], n=N28)
        try:
            R = M.latent_gaussian_matrix(v, CONT)
            f = fit(kind, R, CONT)
        except RuntimeError:
            continue
        if not f.converged:
            continue
        proper += 1
        lam_s.append(f.loadings)
        th_s.append([f.theta[f.order.index(a), f.order.index(b)]
                     for a, b in f.edges])
        om_s.append(M.omega_w(f, w))
        om_all[r] = om_s[-1]
        try:
            bw = M.bartlett_weights(f)
            sc_s.append(float(np.sum(np.abs(bw))))
        except RuntimeError:
            sc_s.append(float("nan"))
    out = {"cell": cell_key(cell), "arm": cell["arm"], "estimator": kind,
           "profile": cell["profile"], "method_rho": cell["method_rho"],
           "comp_rho": cell["comp_rho"], "missing": cell["missing"],
           "braak_ceiling": cell["braak_ceiling"], "reps": reps,
           "proper_rate": proper / reps, "omega_true": truth["omega"]}
    if proper >= 5:
        L = np.array(lam_s)
        T = np.array(th_s)
        O = np.array(om_s, dtype=np.float64)
        out.update({
            "lam_bias": float(np.mean(L.mean(0) - truth["lam"])),
            "lam_abs_bias_max": float(np.max(np.abs(L.mean(0) - truth["lam"]))),
            "lam_sd_mean": float(np.mean(L.std(0))),
            "theta_bias": float(np.mean(T.mean(0) - truth["theta_edges"])),
            "omega_mean": float(np.nanmean(O)),
            "omega_bias": float(np.nanmean(O) - truth["omega"]),
            "omega_sd": float(np.nanstd(O)),
            "omega_draws": [float(x) for x in O],
        })
    out["omega_all"] = [float(x) for x in om_all]
    return out


def auc(pos: Sequence[float], neg: Sequence[float]) -> float:
    """CONDITIONAL on proper fits: P(a TRUE draw exceeds a NULL draw).

    0.5 = no discrimination. This is a diagnostic about the estimator, NOT the
    operating characteristic of the procedure -- it silently drops every cohort
    that produced an improper fit. Use `auc_unconditional` for the procedure.
    """
    p = np.asarray([x for x in pos if np.isfinite(x)])
    q = np.asarray([x for x in neg if np.isfinite(x)])
    if len(p) == 0 or len(q) == 0:
        return float("nan")
    gt = float(np.sum(p[:, None] > q[None, :]))
    eq = float(np.sum(p[:, None] == q[None, :]))
    return (gt + 0.5 * eq) / (len(p) * len(q))


def auc_unconditional(pos: Sequence[float], neg: Sequence[float]) -> float:
    """UNCONDITIONAL over every simulated cohort, improper fits included.

    An improper fit yields no omega, so it cannot favour either hypothesis.
    Counting every comparison involving one as a tie (0.5) is the neutral
    convention and is declared here rather than chosen later. Both arms must be
    padded to their full replicate count by the caller, with NaN marking an
    improper or refused fit."""
    p = np.asarray(pos, dtype=np.float64)
    q = np.asarray(neg, dtype=np.float64)
    if len(p) == 0 or len(q) == 0:
        return float("nan")
    ok = np.isfinite(p)[:, None] & np.isfinite(q)[None, :]
    gt = float(np.sum((p[:, None] > q[None, :]) & ok))
    eq = float(np.sum((p[:, None] == q[None, :]) & ok))
    ties = float(np.sum(~ok))
    return (gt + 0.5 * eq + 0.5 * ties) / (len(p) * len(q))


def main(out_path: Path) -> int:
    results = []
    for cell in GRID:
        for kind in ESTIMATORS:
            results.append(run_cell(cell, kind, REPS_MAIN, SEED0))
            r = results[-1]
            print("%-22s %-10s proper=%.3f omega_bias=%s"
                  % (r["cell"] + "/" + r["arm"], kind, r["proper_rate"],
                     ("%.3f" % r["omega_bias"]) if "omega_bias" in r else "n/a"),
                  flush=True)
    disc = {}
    for kind in ESTIMATORS:
        for pos_key in ("STRONG/0.75/0.55", "MODERATE/0.75/0.55",
                        "WEAK/0.75/0.55"):
            p = next((r for r in results if r["cell"] == pos_key
                      and r["estimator"] == kind and r["arm"] == "core"), None)
            n = next((r for r in results if r["cell"] == "NULL/0.75/0.55"
                      and r["estimator"] == kind and r["arm"] == "core"), None)
            if p and n and "omega_draws" in p and "omega_draws" in n:
                disc["%s|%s_vs_NULL" % (kind, pos_key)] = {
                    "auc_conditional_on_proper_fits": auc(
                        p["omega_draws"], n["omega_draws"]),
                    "auc_unconditional_all_cohorts": auc_unconditional(
                        p["omega_all"], n["omega_all"]),
                    "proper_rate_true": p["proper_rate"],
                    "proper_rate_null": n["proper_rate"],
                }
    payload = {
        "schema": "T0_MEASUREMENT_ESTIMATOR_QUALIFICATION_V1",
        "frozen_before_running": True,
        "estimators": list(ESTIMATORS),
        "residual_variance_floor": RESIDUAL_VARIANCE_FLOOR,
        "grid_cells": len(GRID),
        "reps_main": REPS_MAIN,
        "seed0": SEED0,
        "nonconvergence_allowance_unchanged": M.NONCONVERGENCE_ALLOWANCE,
        "omega_auc_true_vs_null": disc,
        "discrimination_note":
            "conditional AUC drops improper-fit cohorts and is a DIAGNOSTIC; "
            "unconditional AUC counts them as uninformative ties and is the "
            "procedure's operating characteristic",
        "cells": [{k: v for k, v in r.items()
                   if k not in ("omega_draws", "omega_all")}
                  for r in results],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("\nwritten: %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1
                          else HERE.parent.parent / "docs/agent/evidence"
                          / "t0_measurement_estimator_qualification_20260912.json"))
