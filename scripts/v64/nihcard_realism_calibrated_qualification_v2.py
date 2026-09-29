#!/usr/bin/env python3
# V2 repairs S35-S37/S39 before any real NIH-CARD feature matrix is consumed.
"""Realism-calibrated synthetic qualification of the FROZEN estimator.

Implements V64_NIH_CARD_REALISM_CALIBRATED_SYNTHETIC_DESIGN_CONTRACT_V1, which was
frozen BEFORE any NIH-CARD ETL summary was measured.

THE QUESTION
    Does the frozen 14-feature continuous-adjustment estimator still reject technical
    worlds and preserve biological worlds when the nuisance and support geometry
    resembles NIH-CARD rather than the historical generic simulator?

WHAT IS CALIBRATED, AND WHAT IS NOT
    calibrated   the GEOMETRY the nuisance families act on: marginals and joint
                 dependence of the 14 features, donor/support scale, metacell counts,
                 depth distributions, missingness
    NOT touched  the estimator, the nuisance families' scientific logic, M_MIN, the
                 ridge alpha, K_FOLDS, or any threshold

CALIBRATION METHOD, FROZEN IN THE CONTRACT
    primary      empirical marginals via observed quantile functions + a Gaussian
                 copula on tie-aware rank dependence. The synthetic copula arm uses
                 rank reordering of the exact observed marginal multisets, so each
                 feature preserves its finite-sample empirical marginal exactly,
                 including promoter-degree ties and tails.
    sensitivity  direct row resampling of real feature vectors.
    Independent marginal sampling of dependent variables is forbidden.

FIREWALL. This script consumes ONLY the outcome-blind real feature matrix (covariates
computed for linked and control pairs before any correspondence exists). It never
reads an E2 gene's RNA vector together with its linked distal element's ATAC vector,
and it computes no Delta. If a caller passes a matrix containing a correspondence
column the schema check below rejects it.

TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess

import numpy as np

TOURNAMENT = "scripts/v63/e2_synthetic_identifiability_tournament_v2_1.py"
ESTIMATOR = "scripts/v63/e2_continuous_adjustment_estimator_v1.py"
CONTRACT = "results/v64/V64_NIH_CARD_REALISM_CALIBRATED_SYNTHETIC_DESIGN_CONTRACT_V1.json"
SPAN_REF = "results/v64/V64_NIH_CARD_SYNTHETIC_SPAN_REFERENCE_V1.json"

SEED = 20260929
N_SEEDS = 24
M_MIN = 0.010

FORBIDDEN_COLUMNS = ("correspondence", "delta", "rho", "corr", "linked_score",
                     "obs_score", "r_value")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_blob(p):
    return subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True,
                          text=True, check=True).stdout.strip()


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ calibration
def average_rank(x):
    """Deterministic average ranks for ties; 1-based ranks."""
    from scipy.stats import rankdata
    return rankdata(np.asarray(x), method="average")


def rank_to_normal(x):
    """Van der Waerden scores from tie-aware average ranks."""
    from scipy.special import ndtri
    r = average_rank(x)
    n = len(r)
    u = (r - 0.5) / n
    return ndtri(u)


def fit_copula(X, log):
    """Empirical marginals + Gaussian copula on tie-aware normal scores."""
    _, p = X.shape
    Z = np.column_stack([rank_to_normal(X[:, j]) for j in range(p)])
    C = np.corrcoef(Z.T)
    w, V = np.linalg.eigh(C)
    min_eig = float(np.min(w))
    projection_fro = 0.0
    if min_eig < 1e-8:
        C0 = C.copy()
        w = np.clip(w, 1e-8, None)
        C = V @ np.diag(w) @ V.T
        d = np.sqrt(np.diag(C))
        C = C / np.outer(d, d)
        projection_fro = float(np.linalg.norm(C - C0, ord="fro"))
        log(f"  copula correlation projected to PD; min eigenvalue {min_eig:.3e}; "
            f"Frobenius adjustment {projection_fro:.6g}")
    marg = [np.sort(X[:, j], kind="mergesort") for j in range(p)]
    return {
        "C": C,
        "marginals": marg,
        "min_eigenvalue_before_projection": min_eig,
        "pd_projection_frobenius": projection_fro,
    }


def sample_copula_exact_marginals(fit, rng):
    """Rank-reorder exact empirical marginal multisets using Gaussian latent ranks.

    The number of synthetic rows is exactly the number of real rows. Each column is
    a permutation of the corresponding observed marginal values, so finite-sample
    frequencies, quantiles, min/max, and ties are preserved exactly. Dependence is
    induced by the Gaussian copula latent ordering.
    """
    marg = fit["marginals"]
    n = len(marg[0])
    p = len(marg)
    C = fit["C"]
    L = np.linalg.cholesky(C + 1e-12 * np.eye(p))
    Zs = rng.normal(size=(n, p)) @ L.T
    out = np.empty((n, p), dtype=float)
    for j in range(p):
        order = np.argsort(Zs[:, j], kind="mergesort")
        out[order, j] = marg[j]
    return out


def sample_rows(X, rng):
    """Declared whole-row bootstrap sensitivity arm."""
    idx = rng.integers(0, len(X), size=len(X))
    return np.asarray(X[idx], float)


def realism_receipt(Xreal, Xsyn, names, log, *, method):
    qs = [0.0, 0.01, 0.25, 0.5, 0.75, 0.99, 1.0]
    per = {}
    for j, nm in enumerate(names):
        rq = [float(np.quantile(Xreal[:, j], q)) for q in qs]
        sq = [float(np.quantile(Xsyn[:, j], q)) for q in qs]
        d = max(abs(a - b) / (abs(a) + 1e-9) for a, b in zip(rq, sq))
        exact_multiset = bool(
            len(Xreal) == len(Xsyn)
            and np.array_equal(
                np.sort(Xreal[:, j], kind="mergesort"),
                np.sort(Xsyn[:, j], kind="mergesort"),
            )
        )
        per[nm] = {
            "real_quantiles": dict(zip(map(str, qs), rq)),
            "synthetic_quantiles": dict(zip(map(str, qs), sq)),
            "real_range": [float(Xreal[:, j].min()), float(Xreal[:, j].max())],
            "synthetic_range": [float(Xsyn[:, j].min()), float(Xsyn[:, j].max())],
            "max_relative_quantile_discrepancy": float(d),
            "exact_empirical_multiset_preserved": exact_multiset,
        }

    def spear(M):
        R = np.column_stack([average_rank(M[:, j]) for j in range(M.shape[1])])
        return np.corrcoef(R.T)

    rr, rs = np.corrcoef(Xreal.T), np.corrcoef(Xsyn.T)
    sr, ss = spear(Xreal), spear(Xsyn)
    worst_p = float(np.nanmax(np.abs(rr - rs)))
    worst_s = float(np.nanmax(np.abs(sr - ss)))
    log(f"  {method}: worst |Spearman(real) - Spearman(syn)| = {worst_s:.4f}")
    log(f"  {method}: worst |Pearson(real)  - Pearson(syn)|  = {worst_p:.4f}")
    return {
        "method": method,
        "per_variable": per,
        "worst_abs_pairwise_SPEARMAN_discrepancy": worst_s,
        "worst_abs_pairwise_PEARSON_discrepancy": worst_p,
        "real_spearman": [[float(v) for v in r] for r in sr],
        "synthetic_spearman": [[float(v) for v in r] for r in ss],
        "real_pearson": [[float(v) for v in r] for r in rr],
        "synthetic_pearson": [[float(v) for v in r] for r in rs],
        "claim_rule": "No world may be called NIH-CARD-like without this table.",
    }


def _collect_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _collect_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _collect_strings(v)
    elif isinstance(obj, str):
        yield obj


def bind_stage3_feature_provenance(receipt_path, feature_path, expected_sha):
    observed = sha256_file(feature_path)
    if observed != expected_sha:
        raise SystemExit(
            f"STOP_REAL_FEATURE_SHA256_MISMATCH observed={observed} expected={expected_sha}"
        )
    with open(receipt_path) as fh:
        receipt = json.load(fh)
    strings = set(_collect_strings(receipt))
    if expected_sha not in strings:
        raise SystemExit(
            "STOP_STAGE3_RECEIPT_DOES_NOT_BIND_REAL_FEATURE_ARTIFACT"
        )
    return {
        "stage3_receipt_path": receipt_path,
        "stage3_receipt_sha256": sha256_file(receipt_path),
        "real_feature_artifact_path": feature_path,
        "real_feature_artifact_sha256": observed,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real-features", required=True,
                    help="npz with X (n x 14) and names; outcome-blind covariates only")
    ap.add_argument("--stage3-receipt", required=True,
                    help="audited Stage-3 receipt that binds the feature artifact digest")
    ap.add_argument("--real-features-sha256", required=True,
                    help="frozen SHA-256 of the Stage-3 outcome-blind feature artifact")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, required=True,
                    help="real qualifying-donor count from the ETL")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    T = load_mod(TOURNAMENT, "tour")
    E = load_mod(ESTIMATOR, "est")
    T.assert_sealed()
    names = E.FEATURE_NAMES

    provenance = bind_stage3_feature_provenance(
        a.stage3_receipt, a.real_features, a.real_features_sha256
    )
    d = np.load(a.real_features, allow_pickle=True)
    got_names = [str(x) for x in d["names"]]
    for c in got_names:
        if any(f in c.lower() for f in FORBIDDEN_COLUMNS):
            raise SystemExit(f"FIREWALL_BREACH forbidden column {c!r} in real features")
    if got_names != names:
        raise SystemExit(f"STOP_FEATURE_NAME_MISMATCH {got_names} != {names}")
    Xreal = np.asarray(d["X"], float)
    if Xreal.shape[1] != 14:
        raise SystemExit("STOP_FEATURE_COUNT")
    log(f"real outcome-blind feature matrix: {Xreal.shape[0]:,} pairs x 14")

    rng = np.random.default_rng(SEED)
    fit = fit_copula(Xreal, log)
    Xsyn = sample_copula_exact_marginals(fit, rng)
    Xrow = sample_rows(Xreal, np.random.default_rng(SEED + 1))
    receipt = realism_receipt(
        Xreal, Xsyn, names, log, method="GAUSSIAN_COPULA_EXACT_EMPIRICAL_MARGINALS"
    )
    row_receipt = realism_receipt(
        Xreal, Xrow, names, log, method="DIRECT_ROW_RESAMPLING"
    )

    # ---- historical reference, for the real-vs-old mismatch table
    hist = json.load(open(SPAN_REF))
    mism = {}
    for j, nm in enumerate(names):
        lo, hi = hist["reference"]["min"][j], hist["reference"]["max"][j]
        frac = float(np.mean((Xreal[:, j] < lo) | (Xreal[:, j] > hi)))
        mism[nm] = {"historical_synthetic_range": [lo, hi],
                    "real_range": [float(Xreal[:, j].min()), float(Xreal[:, j].max())],
                    "fraction_of_real_outside_historical_range": frac}
    biggest = sorted(mism.items(),
                     key=lambda kv: -kv[1]["fraction_of_real_outside_historical_range"])
    log("  biggest real-vs-historical-synthetic mismatches:")
    for nm, v in biggest[:5]:
        log(f"    {nm:<30} {v['fraction_of_real_outside_historical_range']:.4f} outside")

    out = {
        "schema": "V64_NIH_CARD_REALISM_CALIBRATION_RECEIPT_V1",
        "date": "2026-09-29",
        "governing_contract": {"path": CONTRACT, "sha256": sha256_file(CONTRACT)},
        "modules": {
            "tournament": {"git_blob": git_blob(TOURNAMENT), "sha256": sha256_file(TOURNAMENT)},
            "estimator": {"git_blob": git_blob(ESTIMATOR), "sha256": sha256_file(ESTIMATOR)},
            "imported_unmodified": True, "assert_sealed_passed": True},
        "calibration": {
            "method": "EMPIRICAL_MARGINALS_PLUS_GAUSSIAN_COPULA",
            "frozen_before_etl": True,
            "min_eigenvalue_before_projection": fit["min_eigenvalue_before_projection"],
            "pd_projection_frobenius": fit["pd_projection_frobenius"],
            "rank_convention": "scipy.stats.rankdata(method='average')",
            "marginal_preservation": "EXACT_FINITE_SAMPLE_MULTISET_BY_RANK_REORDERING",
            "real_pairs": int(Xreal.shape[0]),
            "synthetic_pairs": int(Xsyn.shape[0]),
            "donors_calibrated_to": a.donors,
            "historical_comparison_arm_donors": 18,
            "seed": SEED, "n_seeds": N_SEEDS, "M_MIN": M_MIN},
        "INPUT_PROVENANCE": provenance,
        "REALISM_RECEIPT": receipt,
        "ROW_RESAMPLING_SENSITIVITY_RECEIPT": row_receipt,
        "REAL_VS_HISTORICAL_SYNTHETIC_MISMATCH": mism,
        "biggest_mismatches": [k for k, _ in biggest[:5]],
        "estimator_changed": False,
        "basis_terms_added": False,
        "e2_correspondence_outcome_opened": False,
        "firewall": {"forbidden_columns_checked": list(FORBIDDEN_COLUMNS),
                     "e2_rna_paired_with_e2_atac": False},
        "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                       "stage_4": "NOT_AUTHORISED"},
    }
    with open(os.path.join(a.out_dir,
                           "V64_NIH_CARD_REALISM_CALIBRATION_RECEIPT_V1.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    np.savez_compressed(os.path.join(a.out_dir, "calibrated_geometry_copula.npz"),
                        X=Xsyn, names=np.array(names, dtype=object))
    np.savez_compressed(os.path.join(a.out_dir, "calibrated_geometry_row_resample.npz"),
                        X=Xrow, names=np.array(names, dtype=object))
    log("\ncalibration complete; no correspondence value was computed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
