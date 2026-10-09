#!/usr/bin/env python3
"""Continuous-adjustment estimator — Branch 2, implementing the FROZEN contract.

Contract: results/v63/V63_CONTINUOUS_ADJUSTMENT_ESTIMATOR_CONTRACT_V1.json,
committed at 4f774e0b BEFORE this script was written or run. Every number below
follows that specification; nothing here may add a term, move a threshold or
search a hyperparameter.

WHY THIS ESTIMATOR, in one sentence: coarsened binning balances geometry only to
WITHIN a bin while the NEG_TECH_2 latent is keyed to geometry CONTINUOUSLY, so
binning must buy balance with retention -- which is exactly the frontier that had
no feasible region. A continuous adjustment does not face that trade.

THE NINE FROZEN POINTS
  1 same donor-level linked-vs-control correspondence contrast
  2 eight continuous adjustment variables
  3 NO bins, NO trimming: all 960 linked pairs are scored
  4 nuisance expectation fitted on UNLINKED/CONTROL PAIRS ONLY
  5 cross-fitted by PROMOTER (K=5) -- never predicts a promoter it trained on
  6 ridge on standardised main effects + exactly six predeclared nonlinear terms
  7 alpha FIXED PROSPECTIVELY at 1.0; no search against TECH or any arm label
  8 per pair: observed, expected-nuisance, residual correspondence
  9 donor-level scoring on the residuals, existing seed/bootstrap machinery intact

TRAINING=OFF. TD60=BLOCKED. Synthetic only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "tour", os.path.join(HERE, "e2_synthetic_identifiability_tournament_v2_1.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

M_MIN = T.M_MIN                 # 0.010, inherited. NOT redefined.
RIDGE_ALPHA = 1.0               # frozen in the contract, point 7
K_FOLDS = 5                     # frozen, point 5
FEATURE_NAMES = ["log_distance", "promoter_degree", "promoter_activity",
                 "distal_accessibility", "re_density", "anchor_frequency",
                 "rna_depth_sensitivity", "atac_depth_sensitivity",
                 "log_distance^2", "degree^2", "accessibility^2",
                 "log_distance_x_degree", "log_distance_x_accessibility",
                 "degree_x_anchor_frequency"]


def build_features(w, rna_sens, atac_sens):
    """(N_PROM*N_DISTAL, 14). Main effects then the six predeclared products."""
    P, D = T.N_PROM, T.N_DISTAL
    ld = np.log(w["distance"])
    deg = np.repeat(w["degree"][:, None].astype(float), D, 1)
    act = np.repeat(w["prom_activity"][:, None], D, 1)
    acc = w["distal_acc"]
    den = w["re_density"]
    anc = w["anchor_freq"]
    cols = [ld, deg, act, acc, den, anc, rna_sens, atac_sens,
            ld ** 2, deg ** 2, acc ** 2, ld * deg, ld * acc, deg * anc]
    return np.stack([c.ravel() for c in cols], 1)


def ridge_fit(X, y, alpha=RIDGE_ALPHA):
    """Closed-form ridge on standardised X with centred y. The intercept is the
    mean of y and is not penalised."""
    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    Xs = (X - mu) / sd
    ybar = y.mean()
    A = Xs.T @ Xs + alpha * np.eye(Xs.shape[1])
    beta = np.linalg.solve(A, Xs.T @ (y - ybar))
    return {"mu": mu, "sd": sd, "beta": beta, "ybar": ybar}


def ridge_predict(m, X):
    return ((X - m["mu"]) / m["sd"]) @ m["beta"] + m["ybar"]


def per_donor_residual_scores(donors, w, linked_flat, folds, ablate=None):
    """Returns (per-donor score, per-pair mean residual over donors, diagnostics)."""
    P, D = T.N_PROM, T.N_DISTAL
    unlinked_flat = ~linked_flat
    scores, resid_acc = [], np.zeros(P * D)
    r2s = []
    for d in donors:
        R0, A0 = d["R"], d["A"]
        M = R0.shape[0]
        # depth sensitivities on the RAW signals, BEFORE QC residualisation, so
        # they carry information instead of being ~0 by construction (contract 2a)
        rz = (R0 - R0.mean(0)) / np.maximum(R0.std(0), 1e-9)
        az = (A0 - A0.mean(0)) / np.maximum(A0.std(0), 1e-9)
        dz = (d["rna_depth"] - d["rna_depth"].mean()) / (d["rna_depth"].std() + 1e-9)
        tz = (d["atac_depth"] - d["atac_depth"].mean()) / (d["atac_depth"].std() + 1e-9)
        rna_sens = np.repeat(((rz * dz[:, None]).mean(0))[:, None], D, 1)
        atac_sens = (az * tz[:, None, None]).mean(0)

        # observed correspondence, same pipeline as the frozen tournament
        R, A = R0.copy(), A0.copy()
        Z = np.c_[np.ones(M), d["rna_depth"], d["atac_depth"]]
        R = R - Z @ np.linalg.lstsq(Z, R, rcond=None)[0]
        A2 = A.reshape(M, -1)
        A2 = A2 - Z @ np.linalg.lstsq(Z, A2, rcond=None)[0]
        A = A2.reshape(A.shape)
        R = (R - R.mean(0)) / np.maximum(R.std(0), 1e-9)
        A = (A - A.mean(0)) / np.maximum(A.std(0), 1e-9)
        obs = (np.einsum("mp,mpd->pd", R, A) / M).ravel()

        X = build_features(w, rna_sens, atac_sens)
        pred = np.empty_like(obs)
        for k in range(K_FOLDS):
            test_prom = (folds == k)
            test = np.repeat(test_prom, D)
            train = (~test) & unlinked_flat        # contract 4 + 5
            if ablate == "intercept_only":
                # ABLATION, not part of the frozen estimator. Replaces the fitted
                # nuisance surface with the training-fold MEAN. If the headline
                # result is unchanged under this, the continuous adjustment is
                # doing nothing and the effect comes from the control-set change
                # (all-unlinked instead of a matched subset) -- a different change
                # from the one authorised, and it would have to be reported as such.
                pred[test] = obs[train].mean()
            else:
                m = ridge_fit(X[train], obs[train])
                pred[test] = ridge_predict(m, X[test])
            ss = obs[test & unlinked_flat]
            pp = pred[test & unlinked_flat]
            if len(ss) > 2 and ss.var() > 0:
                r2s.append(1 - ((ss - pp) ** 2).mean() / ss.var())
        resid = obs - pred
        resid_acc += resid
        scores.append(float(resid[linked_flat].mean() - resid[unlinked_flat].mean()))
    return (np.array(scores), resid_acc / max(1, len(donors)),
            {"nuisance_r2_oof_mean": float(np.mean(r2s)) if r2s else None})


def run(n_donors, n_seeds, base_seed=20260929, ablate=None):
    arm_seed_fold = {a: [] for a in T.ALL_ARMS}
    diag = {"nuisance_r2": [], "resid_corr": [], "concentration": [],
            "ess": [], "linked_vs_control_smd": []}
    for s in range(n_seeds):
        world_rng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors)
        w = T.make_world(world_rng)
        linked_flat = w["linked"].ravel()
        fold_rng = np.random.default_rng(base_seed + 7919 * s + 999)
        folds = fold_rng.permutation(np.arange(T.N_PROM) % K_FOLDS)
        pos_world = None
        order = [a for a in T.ALL_ARMS if a != T.TWIN] + [T.TWIN]
        for arm in order:
            donors = T.simulate(w, arm, n_donors, base_seed + s, twin_source=pos_world)
            if arm == "POS_BIO_1":
                pos_world = donors
            pd_scores, mean_resid, dg = per_donor_residual_scores(
                donors, w, linked_flat, folds, ablate=ablate)
            arm_seed_fold[arm].append(T.loo_arm_score(pd_scores))
            if arm == "POS_BIO_1":
                diag["nuisance_r2"].append(dg["nuisance_r2_oof_mean"])
                lr = mean_resid[linked_flat]
                # contribution concentration and Kish ESS on the linked contributions
                a = np.abs(lr)
                order_i = np.argsort(-a)
                tot = a.sum() or 1e-12
                diag["concentration"].append(
                    {p: float(a[order_i[:max(1, int(len(a) * p / 100))]].sum() / tot)
                     for p in (1, 5, 10)})
                diag["ess"].append(float(a.sum() ** 2 / max(1e-12, (a ** 2).sum())))
                # residual correlation with the adjustment variables, on LINKED pairs
                # (out-of-sample for the nuisance model, so this is the real check)
                Xd = build_features(w, np.zeros((T.N_PROM, T.N_DISTAL)),
                                    np.zeros((T.N_PROM, T.N_DISTAL)))
                cc = {}
                for name, j in (("log_distance", 0), ("promoter_degree", 1),
                                ("distal_accessibility", 3), ("anchor_frequency", 5)):
                    v = Xd[linked_flat, j]
                    cc[name] = float(np.corrcoef(v, lr)[0, 1]) if v.std() > 0 else None
                diag["resid_corr"].append(cc)
                smd = {}
                for name, j in (("log_distance", 0), ("promoter_degree", 1),
                                ("promoter_activity", 2), ("distal_accessibility", 3),
                                ("re_density", 4), ("anchor_frequency", 5)):
                    a1, b1 = Xd[linked_flat, j], Xd[~linked_flat, j]
                    psd = np.sqrt((a1.var(ddof=1) + b1.var(ddof=1)) / 2) or 1e-9
                    smd[name] = float((a1.mean() - b1.mean()) / psd)
                diag["linked_vs_control_smd"].append(smd)
    return arm_seed_fold, diag


def main() -> int:
    T.assert_sealed()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--ablate", choices=["intercept_only"], default=None,
                    help="DIAGNOSTIC ablation; not part of the frozen estimator")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    asf, diag = run(a.donors, a.seeds, ablate=a.ablate)
    arm_seed = {k: np.array([f.mean() for f in v]) for k, v in asf.items()}
    med = {k: float(np.median(v)) for k, v in arm_seed.items()}
    pos_stack = np.vstack([arm_seed[p] for p in T.POSITIVES])
    pos_min = pos_stack.min(0)

    def fam(arms):
        neg = np.vstack([arm_seed[x] for x in arms]).max(0)
        m = pos_min - neg
        return float(m.mean()), T.lower_confidence_bound(m)

    families = {}
    for f, arms in T.FAMILIES.items():
        mm, ll = fam(arms)
        families[f] = {"margin": mm, "lcb95": ll, "passes_M_MIN": bool(ll > M_MIN)}
    heldout = {}
    for f, arms in T.HELDOUT_FAMILY.items():
        mm, ll = fam(arms)
        heldout[f] = {"margin": mm, "lcb95": ll, "generalises_at_M_MIN": bool(ll > M_MIN)}

    det = pos_min - arm_seed["NEG_NULL_0"]
    det_lcb = T.lower_confidence_bound(det)
    ordering_ok = bool(med["POS_BIO_1"] > med["POS_BIO_2"] >
                       max(med[x] for x in T.NEG_ARMS))
    twin_identical = bool(np.allclose(arm_seed[T.TWIN], arm_seed["POS_BIO_1"],
                                      rtol=0, atol=0))

    n_linked = int(T.N_PROM * T.N_LINKED_PER_PROM)
    conc = {p: float(np.mean([c[p] for c in diag["concentration"]])) for p in (1, 5, 10)}
    rc = {k: float(np.mean([c[k] for c in diag["resid_corr"] if c[k] is not None]))
          for k in diag["resid_corr"][0]}
    smd = {k: float(np.mean([s[k] for s in diag["linked_vs_control_smd"]]))
           for k in diag["linked_vs_control_smd"][0]}
    ess = float(np.mean(diag["ess"]))

    all_pass = all(v["passes_M_MIN"] for v in families.values())
    tech_pass = families["TECH"]["passes_M_MIN"]
    others_green = all(v["passes_M_MIN"] for f, v in families.items() if f != "TECH")
    broad = bool(conc[10] < 0.5 and ess > 0.3 * n_linked)

    out = {
        "schema": "V63_E2_CONTINUOUS_ADJUSTMENT_ESTIMATOR_V1",
        "date": "2026-09-29",
        "contract": "results/v63/V63_CONTINUOUS_ADJUSTMENT_ESTIMATOR_CONTRACT_V1.json @ 4f774e0b",
        "governance": {"training": "OFF", "td60": "BLOCKED", "real_data_read": False},
        "ablation": a.ablate,
        "config": {"donors": a.donors, "seeds": a.seeds, "M_MIN": M_MIN,
                   "ridge_alpha": RIDGE_ALPHA, "k_folds_by_promoter": K_FOLDS,
                   "features": FEATURE_NAMES},
        "arm_medians": med,
        "A_REPRESENTED_NUISANCE_SPECIFICITY": {"families": families,
                                               "all_families_pass": all_pass},
        "B_IDENTIFIABILITY_BOUNDARY": {
            "twin_median": med[T.TWIN], "pos_bio_1_median": med["POS_BIO_1"],
            "twin_identical_to_POS_BIO_1": twin_identical,
            "classification": "NON_IDENTIFIABLE_BY_DESIGN", "is_a_gate_failure": False},
        "SUPPORT_PROOF": {
            "linked_pairs_scored": n_linked,
            "linked_pairs_total": n_linked,
            "fraction_of_linked_scored": 1.0,
            "no_trimming": True,
            "kish_effective_sample_size": ess,
            "ess_fraction_of_linked": ess / n_linked,
            "contribution_concentration_top_pct": conc,
            "residual_correlation_with_adjustment_vars_on_LINKED": rc,
            "worst_abs_residual_correlation": float(max(abs(v) for v in rc.values())),
            "linked_vs_control_SMD_before_adjustment": smd,
            "worst_abs_linked_vs_control_SMD": float(max(abs(v) for v in smd.values())),
            "nuisance_model_out_of_fold_r2": float(np.mean(diag["nuisance_r2"])),
        },
        "ANTI_FALSE_GREEN": {
            "positive_detectability_lcb95": det_lcb,
            "detectable": bool(det_lcb > M_MIN),
            "ordering_POS1_gt_POS2_gt_negatives": ordering_ok,
            "twin_identical": twin_identical,
            "heldout_family": heldout,
        },
    }
    if not others_green:
        cls = "D_ANOTHER_FAMILY_BROKE__STOP"
        note = ("A represented family other than TECH failed. Per the predeclared "
                "interpretation this is a STOP: do not trade one nuisance failure for "
                "another, exactly as no_anchor_matching exposed.")
    elif tech_pass and broad:
        cls = "A_TECH_CLEARS_WITH_BROAD_COVERAGE"
        note = ("Strong evidence that the problem was COARSE SUPPORT ADJUSTMENT rather "
                "than intrinsic non-identifiability.")
    elif tech_pass and not broad:
        cls = "B_TECH_CLEARS_BUT_CONCENTRATED__SAME_FAILURE_DISGUISED"
        note = ("TECH clears but a small subset of links carries the result. Per the "
                "predeclared interpretation this is the same failure disguised as "
                "continuous adjustment, and is NOT a pass.")
    else:
        cls = "C_TECH_STILL_FAILS__INVESTIGATE_IDENTIFIABILITY_ITSELF"
        note = ("TECH still fails. If the nuisance fit and support are good, this is "
                "stronger evidence that the current observables are insufficient. The "
                "next step is to investigate IDENTIFIABILITY ITSELF, not estimator "
                "#2, #3, #4.")
    out["PREDECLARED_CLASSIFICATION"] = cls
    out["classification_note"] = note
    out["broad_coverage_test"] = {
        "rule": "top-10% contribution share < 0.50 AND Kish ESS > 30% of linked pairs",
        "top10_share": conc[10], "ess_fraction": ess / n_linked, "broad": broad}

    with open(os.path.join(a.out_dir, "V63_E2_CONTINUOUS_ADJUSTMENT_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"{'arm':22s} {'median':>10}")
    for k in T.ALL_ARMS:
        print(f"{k:22s} {med[k]:+10.5f}{'  <- NON_IDENTIFIABLE_BY_DESIGN' if k == T.TWIN else ''}")
    print(f"\nfamily margins (M_MIN={M_MIN})")
    for f, v in families.items():
        print(f"   {f:8s} {v['margin']:+10.5f} LCB {v['lcb95']:+10.5f}  "
              f"{'PASS' if v['passes_M_MIN'] else 'FAIL'}")
    for f, v in heldout.items():
        print(f"   {f:8s} {v['margin']:+10.5f} LCB {v['lcb95']:+10.5f}  "
              f"{'generalises' if v['generalises_at_M_MIN'] else 'DOES NOT GENERALISE'}")
    sp = out["SUPPORT_PROOF"]
    print(f"\nSUPPORT: {sp['fraction_of_linked_scored']*100:.0f}% of {n_linked} linked "
          f"scored, ESS {ess:.0f} ({100*ess/n_linked:.1f}%), "
          f"top1/5/10% share {conc[1]:.3f}/{conc[5]:.3f}/{conc[10]:.3f}")
    print(f"  nuisance out-of-fold R2 {sp['nuisance_model_out_of_fold_r2']:+.4f}")
    print(f"  residual corr on linked: " +
          ", ".join(f"{k} {v:+.4f}" for k, v in rc.items()))
    print(f"  linked-vs-control SMD before adjustment, worst "
          f"{sp['worst_abs_linked_vs_control_SMD']:.3f}")
    print(f"\ndetectability LCB {det_lcb:+.5f}  ordering {ordering_ok}  twin_identical {twin_identical}")
    print(f"CLASSIFICATION: {cls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
