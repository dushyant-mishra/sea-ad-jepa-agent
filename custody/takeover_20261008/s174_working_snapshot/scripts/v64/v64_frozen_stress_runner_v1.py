#!/usr/bin/env python3
"""V64 frozen statistical red-team: depth-sensitivity ablation + out-of-span stress.

Executes two FROZEN contracts without redesigning anything:

  results/v64/V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_LEAKAGE_DIAGNOSTIC_V1.json
  results/v64/V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_CONTRACT_V1.json

THE ESTIMATOR IS IMPORTED, NOT COPIED. `e2_continuous_adjustment_estimator_v1.py`
is loaded as a module and its scoring code runs unmodified, so "the estimator
must remain unchanged at c4e78de2" is literally true rather than asserted. The
two permitted interventions are applied from OUTSIDE it:

  --drop-depth-sensitivity   wraps build_features and DELETES columns 6 and 7
                             (rna_depth_sensitivity, atac_depth_sensitivity).
                             No replacement covariate is added. The six nonlinear
                             terms never involved those columns, so 14 -> 12
                             features and nothing else moves.

  --include-outspan          adds ONE new negative arm, NEG_TECH_OUTSPAN_1, built
                             exactly as the contract specifies. No basis term is
                             added to the estimator to accommodate it -- that is
                             the whole point of the test.

FORBIDDEN AND NOT DONE: retuning ridge alpha, adding replacement covariates,
changing positive amplitudes, changing M_MIN, altering existing nuisance arms,
adding sin/tanh terms to the ridge basis, choosing a new nuisance after seeing a
result.

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
V63 = os.path.join(os.path.dirname(HERE), "v63")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _load("tour", os.path.join(V63, "e2_synthetic_identifiability_tournament_v2_1.py"))
E = _load("est", os.path.join(V63, "e2_continuous_adjustment_estimator_v1.py"))

M_MIN = T.M_MIN
OUTSPAN = "NEG_TECH_OUTSPAN_1"


def zs(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / (x.std() + 1e-12)


def outspan_geometry(w):
    """g, EXACTLY as frozen in the contract:

        g = zscore( sin(2.5*z_log_distance)
                    + 0.5*tanh(z_degree * z_anchor_frequency)
                    + 0.35*z_accessibility * z_re_density )

    Non-monotonic and multiplicative in a way the frozen 14-term ridge basis
    (linear, squares, and three specific products) cannot represent. No target
    label and no linked status enters it.
    """
    P, D = T.N_PROM, T.N_DISTAL
    zld = zs(np.log(w["distance"]).ravel()).reshape(P, D)
    zdeg = zs(np.repeat(w["degree"][:, None].astype(float), D, 1).ravel()).reshape(P, D)
    zanc = zs(w["anchor_freq"].ravel()).reshape(P, D)
    zacc = zs(w["distal_acc"].ravel()).reshape(P, D)
    zden = zs(w["re_density"].ravel()).reshape(P, D)
    g = (np.sin(2.5 * zld) + 0.5 * np.tanh(zdeg * zanc) + 0.35 * zacc * zden)
    return zs(g.ravel()).reshape(P, D)


def simulate_outspan(w, n_donors, seed):
    """NEG_TECH_OUTSPAN_1. Mirrors T.simulate's donor loop exactly -- same rng
    seeding, same base signals, same measured-depth structure, same hidden-quality
    mixing (0.6*z_meas + 0.8*orthogonal) and the same 0.60 amplitude as
    NEG_TECH_2. ONLY the ATAC-side geometry function differs."""
    g = outspan_geometry(w)
    out = []
    for dn in range(n_donors):
        base = np.random.default_rng(seed * 1_000_003 + dn)            # arm-independent
        eff = np.random.default_rng(seed * 1_000_003 + dn + 7_777_777)  # as T.simulate
        rna_depth = base.normal(0, 1, T.N_METACELL)
        atac_depth = 0.45 * rna_depth + base.normal(
            0, np.sqrt(1 - 0.45 ** 2), T.N_METACELL)
        base.normal(0, 1)                      # consume the operator draw, as T does
        R = base.normal(0, 1, (T.N_METACELL, T.N_PROM)) + 0.35 * rna_depth[:, None]
        A = (base.normal(0, 1, (T.N_METACELL, T.N_PROM, T.N_DISTAL))
             + 0.35 * atac_depth[:, None, None])
        z_meas = 0.5 * (rna_depth + atac_depth) / np.sqrt(2)
        hq = 0.6 * z_meas + 0.8 * eff.normal(0, 1, T.N_METACELL)
        R += 0.60 * hq[:, None]
        A += 0.60 * hq[:, None, None] * g[None, :, :]
        out.append({"R": R, "A": A, "rna_depth": rna_depth, "atac_depth": atac_depth})
    return out


def make_dropped_build_features(orig):
    """Wrapper deleting ONLY columns 6 and 7. The estimator file is untouched."""
    def wrapped(w, rna_sens, atac_sens):
        X = orig(w, rna_sens, atac_sens)
        return np.delete(X, [6, 7], axis=1)
    return wrapped


def run(n_donors, n_seeds, drop_depth, include_outspan, base_seed=20260929):
    arms = list(T.ALL_ARMS)
    if include_outspan:
        arms = [a for a in arms if a != T.TWIN] + [OUTSPAN, T.TWIN]
    asf = {a: [] for a in arms}
    diag = {"ess": [], "conc": [], "resid_corr": [], "r2": []}

    orig_bf = E.build_features
    if drop_depth:
        E.build_features = make_dropped_build_features(orig_bf)
    try:
        for s in range(n_seeds):
            world_rng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors)
            w = T.make_world(world_rng)
            linked_flat = w["linked"].ravel()
            fold_rng = np.random.default_rng(base_seed + 7919 * s + 999)
            folds = fold_rng.permutation(np.arange(T.N_PROM) % E.K_FOLDS)
            pos_world = None
            order = [a for a in arms if a != T.TWIN] + [T.TWIN]
            for arm in order:
                if arm == OUTSPAN:
                    donors = simulate_outspan(w, n_donors, base_seed + s)
                else:
                    donors = T.simulate(w, arm, n_donors, base_seed + s,
                                        twin_source=pos_world)
                    if arm == "POS_BIO_1":
                        pos_world = donors
                pds, mean_resid, dg = E.per_donor_residual_scores(
                    donors, w, linked_flat, folds)
                asf[arm].append(T.loo_arm_score(pds))
                if arm == "POS_BIO_1":
                    diag["r2"].append(dg["nuisance_r2_oof_mean"])
                    lr = mean_resid[linked_flat]
                    a = np.abs(lr)
                    o = np.argsort(-a)
                    tot = a.sum() or 1e-12
                    diag["conc"].append({p: float(a[o[:max(1, int(len(a) * p / 100))]].sum() / tot)
                                         for p in (1, 5, 10)})
                    diag["ess"].append(float(a.sum() ** 2 / max(1e-12, (a ** 2).sum())))
                    Xd = orig_bf(w, np.zeros((T.N_PROM, T.N_DISTAL)),
                                 np.zeros((T.N_PROM, T.N_DISTAL)))
                    diag["resid_corr"].append(
                        {n: (float(np.corrcoef(Xd[linked_flat, j], lr)[0, 1])
                             if Xd[linked_flat, j].std() > 0 else None)
                         for n, j in (("log_distance", 0), ("promoter_degree", 1),
                                      ("distal_accessibility", 3), ("anchor_frequency", 5))})
    finally:
        E.build_features = orig_bf          # always restore
    return asf, diag


def main() -> int:
    T.assert_sealed()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--drop-depth-sensitivity", action="store_true")
    ap.add_argument("--include-outspan", action="store_true")
    ap.add_argument("--label", default="baseline")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    asf, diag = run(a.donors, a.seeds, a.drop_depth_sensitivity, a.include_outspan)
    arm_seed = {k: np.array([f.mean() for f in v]) for k, v in asf.items()}
    med = {k: float(np.median(v)) for k, v in arm_seed.items()}
    pos_min = np.vstack([arm_seed[p] for p in T.POSITIVES]).min(0)

    def fam(arms):
        neg = np.vstack([arm_seed[x] for x in arms]).max(0)
        m = pos_min - neg
        return float(m.mean()), T.lower_confidence_bound(m)

    fams = dict(T.FAMILIES)
    if a.include_outspan:
        fams["OUTSPAN_TECH"] = (OUTSPAN,)
    families = {}
    for f, arms in fams.items():
        mm, ll = fam(arms)
        families[f] = {"margin": mm, "lcb95": ll, "passes_M_MIN": bool(ll > M_MIN)}
    heldout = {}
    for f, arms in T.HELDOUT_FAMILY.items():
        mm, ll = fam(arms)
        heldout[f] = {"margin": mm, "lcb95": ll, "generalises": bool(ll > M_MIN)}

    det_lcb = T.lower_confidence_bound(pos_min - arm_seed["NEG_NULL_0"])
    neg_for_order = [x for arms in fams.values() for x in arms]
    ordering_ok = bool(med["POS_BIO_1"] > med["POS_BIO_2"] >
                       max(med[x] for x in neg_for_order))
    twin_identical = bool(np.allclose(arm_seed[T.TWIN], arm_seed["POS_BIO_1"],
                                      rtol=0, atol=0))
    n_linked = int(T.N_PROM * T.N_LINKED_PER_PROM)
    conc = {p: float(np.mean([c[p] for c in diag["conc"]])) for p in (1, 5, 10)}
    ess = float(np.mean(diag["ess"]))
    rc = {k: float(np.mean([c[k] for c in diag["resid_corr"] if c[k] is not None]))
          for k in diag["resid_corr"][0]}

    out = {
        "schema": "V64_FROZEN_STRESS_RESULT_V1",
        "label": a.label, "date": "2026-09-29",
        "contracts_executed": [
            "V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_LEAKAGE_DIAGNOSTIC_V1"
            if a.drop_depth_sensitivity else None,
            "V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_CONTRACT_V1"
            if a.include_outspan else None],
        "interventions": {"drop_depth_sensitivity": a.drop_depth_sensitivity,
                          "include_outspan": a.include_outspan,
                          "n_features": 12 if a.drop_depth_sensitivity else 14},
        "estimator": "e2_continuous_adjustment_estimator_v1.py IMPORTED UNMODIFIED",
        "governance": {"training": "OFF", "td60": "BLOCKED", "real_data_read": False},
        "config": {"donors": a.donors, "seeds": a.seeds, "M_MIN": M_MIN,
                   "ridge_alpha": E.RIDGE_ALPHA, "k_folds": E.K_FOLDS},
        "arm_medians": med,
        "families": families,
        "all_families_pass": all(v["passes_M_MIN"] for v in families.values()),
        "heldout": heldout,
        "support": {"linked_scored": n_linked, "fraction_scored": 1.0,
                    "kish_ess": ess, "ess_fraction": ess / n_linked,
                    "concentration_top_pct": conc,
                    "nuisance_oof_r2": float(np.mean(diag["r2"])),
                    "residual_corr_on_linked": rc},
        "anti_false_green": {"detectability_lcb95": det_lcb,
                             "detectable": bool(det_lcb > M_MIN),
                             "ordering_ok": ordering_ok,
                             "twin_identical": twin_identical},
    }
    with open(os.path.join(a.out_dir, f"V64_FROZEN_STRESS_{a.label}.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"### {a.label}  features={out['interventions']['n_features']}  "
          f"outspan={a.include_outspan}")
    for k in med:
        tag = "  <- TWIN" if k == T.TWIN else ("  <- OUT-OF-SPAN" if k == OUTSPAN else "")
        print(f"  {k:24s} {med[k]:+10.5f}{tag}")
    print(f"  {'family':14s} {'margin':>10} {'LCB95':>10}  pass")
    for f, v in families.items():
        print(f"  {f:14s} {v['margin']:+10.5f} {v['lcb95']:+10.5f}  "
              f"{'PASS' if v['passes_M_MIN'] else 'FAIL'}")
    for f, v in heldout.items():
        print(f"  {f:14s} {v['margin']:+10.5f} {v['lcb95']:+10.5f}  "
              f"{'generalises' if v['generalises'] else 'DOES NOT GENERALISE'}")
    print(f"  support: ESS {ess:.0f} ({100*ess/n_linked:.1f}%)  "
          f"top1/5/10 {conc[1]:.3f}/{conc[5]:.3f}/{conc[10]:.3f}  "
          f"oof_R2 {out['support']['nuisance_oof_r2']:+.4f}")
    print(f"  resid corr: " + ", ".join(f"{k} {v:+.4f}" for k, v in rc.items()))
    print(f"  detectability {det_lcb:+.5f}  ordering {ordering_ok}  twin {twin_identical}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
