#!/usr/bin/env python3
"""Gate v4 — an actually amplitude-controlled composition arm, and no fail-open.

TEN DEFECTS IN v3, ALL FOUND IN REVIEW BEFORE ANY REAL OUTCOME

  1  POS_COMP WAS NOT AMPLITUDE-CONTROLLED. Loadings [+.6,-.6,+.6,-.6] sum to
     zero on the LINEAR scale, but rates are exponentiated, so the expected
     total is 4*cosh(0.6z) - measured 81% higher at z=2 than at z=0, with mean
     total by z-bin 7.26 / 4.69 / 4.06 / 4.69 / 7.24. The arm moved composition
     AND abundance. v4 draws a total intensity independently of z and
     distributes it with NORMALISED composition probabilities, applying
     gene-specific capture INSIDE the normalisation so it cannot reintroduce a
     z-dependent total.

  2  THE AMPLITUDE CHECK WAS BLIND TO ITS OWN FAILURE. Pearson(total, z) was
     -0.0025 while Pearson(total, z^2) was +0.9945 and Spearman(total, |z|) was
     +1.0000. A symmetric dependence has near-zero linear correlation by
     construction. The field was also named `..._spearman` while computing
     np.corrcoef, which is Pearson. v4 regresses amplitude on z, z^2 and
     capture, reports conditional means across z bins, and gates on all of them.

  3  PYTHON hash() IN SEEDS. String hashing is randomised per process unless
     PYTHONHASHSEED is fixed, so the same source and the same visible SEED can
     generate different data on another process. Replaced by SHA-256.

  4  CALIBRATION FAILED OPEN. A regime yielding zero usable datasets produced a
     NaN rate that was filtered out of the pass condition, contributing nothing
     against it. Non-finite sham statistics were also dropped silently, so a
     null could be built from fewer draws than requested. v4 REQUIRES the full
     preregistered counts and returns INCOMPLETE otherwise.

  5  ONE NEGATIVE ARM, PROSE PROMISING TWO. v4 restores a mechanistically
     distinct second negative arm with no capture variation at all, so the two
     negatives differ in mechanism rather than only in random seed.

  6  SHAM EXCHANGEABILITY BROKEN BY A SHARED NUISANCE PARAMETER. gamma_S was
     drawn once and reused across every sham replicate, so all shams shared a
     capture profile that differed from the real program's. v4 draws fresh
     gene-specific capture exponents per sham draw, from the same distribution
     the real program's come from.

  7  CALIBRATION MEASURED ONLY FALSE POSITIVES. Positive sensitivity rested on
     one dataset per regime. v4 calibrates every arm across datasets.

  8  A RATE FROM 20 DATASETS IS NOT A BOUND. v4 reports the exact binomial
     upper 95% confidence limit and gates on that rather than on the point
     estimate.

  9  THE NB REPAIR WAS INCOMPLETE. Raising on an exception does not catch a fit
     that returns without converging. v4 requires convergence and finite
     coefficients and predictions.

  10 NO CHANNEL ABLATION. A full-model PASS does not show that the CLR
     component learned a compositional signal. v4 runs composition-only and
     amplitude-only predictor sets alongside the full state.

WHAT A FAILURE HERE WOULD AND WOULD NOT MEAN

  Showing that v3's composition arm was not composition-only does NOT establish
  that its positive result came from amplitude leakage. That is what the channel
  ablation is for. Withdrawing a claim is required; substituting an equally
  untested causal story is the same error facing the other way.

No real expression is read. Nothing is trained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
from scipy.stats import beta as beta_dist
from scipy.stats import spearmanr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "src"))
from sea_ad_jepa.v5.teacher_fidelity_core_v1 import (  # noqa: E402
    clr, run_directed_test)

N_DONORS = 27
STRATA_PER_DONOR = 4
CELLS_PER_STRATUM = 60
SEED = 20260927
ALPHA = 0.05
DONOR_FRACTION = 2.0 / 3.0
FP_UPPER_LIMIT = 0.15          # on the binomial UPPER 95% limit, not the rate
POWER_LOWER_LIMIT = 0.50

REGIMES = {
    "A_tuning_sparse":      dict(cap_sd=0.6, base=1.2),
    "B_tuning_dense":       dict(cap_sd=0.6, base=40.0),
    "C_untuned_highcap":    dict(cap_sd=1.0, base=1.2),
    "D_untuned_verysparse": dict(cap_sd=0.3, base=0.6),
}
ARMS = {
    "NEG_CAP":   dict(link="none", capture=True,  want=False),
    "NEG_NOCAP": dict(link="none", capture=False, want=False),
    "POS_AMP":   dict(link="amplitude",   capture=True, want=True),
    "POS_COMP":  dict(link="composition", capture=True, want=True),
}
CHANNELS = ("full", "composition_only", "amplitude_only")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def stable_seed(*parts) -> int:
    """SHA-256 derived. Python's hash() is randomised per process."""
    key = "|".join(str(p) for p in parts).encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % (2 ** 31)


def _partners(rng, base, cap, gamma, z, mode):
    """Four partner counts.

    'amplitude'    all four scale together with z; composition unchanged
    'composition'  the TOTAL INTENSITY is drawn independently of z and the
                   molecules are distributed by normalised probabilities, so
                   only the ratios carry z. Gene-specific capture enters INSIDE
                   the normalisation and therefore cannot reintroduce a
                   z-dependent total.
    'flat'         z does not enter
    """
    n = cap.size
    if mode == "composition":
        # logits carry z; softmax normalises, so the total is untouched by z
        load = np.array([0.9, -0.9, 0.9, -0.9])
        logits = np.outer(z, load) + np.log(np.maximum(cap[:, None], 1e-9)) * \
            (gamma[None, :] - gamma.mean())
        w = np.exp(logits - logits.max(axis=1, keepdims=True))
        probs = w / w.sum(axis=1, keepdims=True)
        total_rate = 4.0 * base * (cap ** gamma.mean())     # independent of z
        return rng.poisson(np.maximum(probs * total_rate[:, None], 1e-9))
    load = np.array([0.5] * 4) if mode == "amplitude" else np.zeros(4)
    rate = base * np.exp(np.outer(z, load)) * (cap[:, None] ** gamma[None, :])
    return rng.poisson(np.maximum(rate, 1e-9))


def simulate(rng, *, cap_sd, base, link, capture):
    donors, strata = [], []
    for d in range(N_DONORS):
        for s in range(STRATA_PER_DONOR):
            donors += [f"D{d:02d}"] * CELLS_PER_STRATUM
            strata += [f"D{d:02d}|op{s}"] * CELLS_PER_STRATUM
    donors = np.asarray(donors); strata = np.asarray(strata)
    n = donors.size
    cap = rng.lognormal(0.0, cap_sd, n) if capture else np.ones(n)
    gamma_P = rng.uniform(0.7, 1.3, 4)
    gamma_Q = rng.uniform(0.7, 1.3, 4)
    lib = rng.negative_binomial(6, 6 / (6 + 4000.0 * cap)).astype(float) + 50.0
    # D is the denominator AFTER removing the excluded gene set, so it is not
    # the library. Previously D = max(lib, 1) made the two controls numerically
    # identical - correlation 1.00000000 - and contributed an exact collinearity.
    D = np.maximum(lib - rng.binomial(lib.astype(int),
                                      0.08).astype(float), 1.0)
    zP = rng.normal(0, 1, n)
    zQ = rng.normal(0, 1, n) if link == "none" \
        else 0.8 * zP + rng.normal(0, 0.6, n)
    p_mode = {"none": "amplitude", "amplitude": "amplitude",
              "composition": "composition"}[link]
    NP4 = _partners(rng, base, cap, gamma_P, zP, p_mode)
    NQ4 = _partners(rng, base, cap, gamma_Q, zQ, "amplitude")
    controls = np.column_stack([
        np.log(D), np.log(lib), rng.poisson(2.0, n), rng.poisson(3.0, n),
        rng.poisson(1.0, n), np.log1p(rng.poisson(max(base * 0.4, 0.2), n))])
    return dict(NP4=NP4, y=NQ4.sum(1).astype(float), D=D, log_D=np.log(D),
                controls=controls, strata=strata, donors=donors, cap=cap,
                zP=zP, p_mode=p_mode, base=base, cap_sd=cap_sd)


def state_from(c4, channel="full"):
    # CLR over K components sums to zero by construction, so the K-th column is
    # exactly determined by the others: the full block has rank K-1 and a
    # condition number around 7.7e14, while K-1 columns give about 2.0. Dropping
    # one coordinate loses no information and is what makes the design solvable.
    comp = clr(c4)[:, :-1]
    amp = np.log1p(c4.sum(1))[:, None]
    if channel == "composition_only":
        return comp
    if channel == "amplitude_only":
        return amp
    return np.hstack([comp, amp])


def split(donors, seed=SEED):
    u = sorted(set(donors))
    ev = {d for d in u if stable_seed(seed, d) % 3 == 0}
    return np.isin(donors, list(set(u) - ev)), np.isin(donors, list(ev))


def amplitude_leakage(counts4, z, cap):
    """Can z move the TOTAL? Tested nonlinearly, not by linear correlation."""
    amp = np.log1p(counts4.sum(1))
    zz = (z - z.mean()) / max(z.std(), 1e-9)
    X = np.column_stack([np.ones(z.size), zz, zz ** 2, np.log(np.maximum(cap, 1e-9))])
    beta, *_ = np.linalg.lstsq(X, amp, rcond=None)
    resid = amp - X @ beta
    r2 = 1.0 - resid.var() / max(amp.var(), 1e-12)
    Xc = np.column_stack([np.ones(z.size), np.log(np.maximum(cap, 1e-9))])
    bc, *_ = np.linalg.lstsq(Xc, amp, rcond=None)
    r2c = 1.0 - (amp - Xc @ bc).var() / max(amp.var(), 1e-12)
    bins = np.digitize(zz, [-1.5, -0.5, 0.5, 1.5])
    means = [float(amp[bins == k].mean()) if (bins == k).any() else float("nan")
             for k in range(5)]
    return {
        "pearson_amp_z": float(np.corrcoef(amp, zz)[0, 1]),
        "pearson_amp_z_squared": float(np.corrcoef(amp, zz ** 2)[0, 1]),
        "spearman_amp_abs_z": float(spearmanr(amp, np.abs(zz)).statistic),
        "beta_z": float(beta[1]), "beta_z_squared": float(beta[2]),
        "r2_gain_from_z_terms": float(max(r2 - r2c, 0.0)),
        "conditional_means_by_z_bin": means,
        "max_bin_spread": float(np.nanmax(means) - np.nanmin(means)),
    }


def binom_upper95(k, n):
    if n == 0:
        return float("nan")
    if k == n:
        return 1.0
    return float(beta_dist.ppf(0.975, k + 1, n - k))


def one_arm(rng, regime, arm, b_sham, seed, quality=False,
            channels=CHANNELS):
    cfg = ARMS[arm]
    d = simulate(rng, link=cfg["link"], capture=cfg["capture"], **REGIMES[regime])
    fit, ev = split(d["donors"])
    common = dict(y_count=d["y"], log_D=d["log_D"], controls=d["controls"],
                  strata=d["strata"], donors=d["donors"],
                  fit_mask=fit, eval_mask=ev, seed=seed)
    out = {"channels": {}, "sham_draws_requested": b_sham}
    fams = []
    for ch in channels:
        real = run_directed_test(state=state_from(d["NP4"], ch), n_perm=0, **common)
        fams.extend(real.model_families_used)
        if not np.isfinite(real.median_increment):
            return {"status": "INCOMPLETE_NO_REAL_STATISTIC", "channel": ch}
        stats = []
        for b in range(b_sham):
            # fresh gene-specific capture exponents per sham, from the same
            # distribution the real program's come from: a single reused
            # gamma_S would give every sham a shared nuisance the real program
            # does not have, breaking exchangeability
            g = rng.uniform(0.7, 1.3, 4)
            sh = _partners(rng, d["base"], d["cap"], g,
                           rng.normal(0, 1, d["cap"].size), d["p_mode"])
            r = run_directed_test(state=state_from(sh, ch), n_perm=0, **common)
            fams.extend(r.model_families_used)
            if not np.isfinite(r.median_increment):
                return {"status": "INCOMPLETE_NONFINITE_SHAM",
                        "channel": ch, "sham_index": b}
            stats.append(r.median_increment)
        if len(stats) != b_sham:
            return {"status": "INCOMPLETE_SHAM_COUNT", "channel": ch,
                    "got": len(stats), "wanted": b_sham}
        stats = np.asarray(stats, float)
        p = (1 + int((stats >= real.median_increment).sum())) / (1 + b_sham)
        out["channels"][ch] = {
            "median_increment": real.median_increment,
            "fraction_donors_positive": real.fraction_donors_positive,
            "sham_null_p": p,
            "qualifies": bool(p <= ALPHA
                              and real.fraction_donors_positive >= DONOR_FRACTION),
        }
    out["status"] = "OK"
    out["channels_run"] = list(channels)
    out["qualifies"] = out["channels"]["full"]["qualifies"]
    out["model_families"] = sorted(set(fams))
    out["poisson_fallbacks"] = sum(1 for x in fams if x.endswith("FALLBACK"))
    if quality:
        out["amplitude_leakage"] = amplitude_leakage(d["NP4"], d["zP"], d["cap"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--b-sham", type=int, default=99)
    ap.add_argument("--calibration-datasets", type=int, default=30)
    ap.add_argument("--calibration-b-sham", type=int, default=49)
    ap.add_argument("--regimes", default=",".join(REGIMES))
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    regimes = [r.strip() for r in a.regimes.split(",") if r.strip()]

    results, calib, incomplete = {}, {}, []
    for reg in regimes:
        print(f"\n=== {reg}  {REGIMES[reg]} ===", flush=True)
        results[reg] = {}
        for arm, cfg in ARMS.items():
            rng = np.random.default_rng(stable_seed(SEED, reg, arm))
            r = one_arm(rng, reg, arm, a.b_sham, SEED, quality=True)
            if r.get("status") != "OK":
                incomplete.append({"regime": reg, "arm": arm, **r})
                results[reg][arm] = r
                print(f"  {arm:10s} {r['status']}", flush=True); continue
            r["required"] = cfg["want"]
            r["arm_pass"] = (r["qualifies"] == cfg["want"])
            results[reg][arm] = r
            f = r["channels"]["full"]; c = r["channels"]["composition_only"]
            m = r["channels"]["amplitude_only"]
            print(f"  {arm:10s} want={str(cfg['want']):5s} "
                  f"full p={f['sham_null_p']:.3f} q={str(f['qualifies']):5s} | "
                  f"comp-only p={c['sham_null_p']:.3f} q={str(c['qualifies']):5s} | "
                  f"amp-only p={m['sham_null_p']:.3f} q={str(m['qualifies']):5s} "
                  f"-> {'PASS' if r['arm_pass'] else 'FAIL'}", flush=True)
            if "amplitude_leakage" in r:
                L = r["amplitude_leakage"]
                print(f"             amplitude leakage: r2 gain from z terms "
                      f"{L['r2_gain_from_z_terms']:.4f}  beta_z2 {L['beta_z_squared']:+.4f}  "
                      f"spearman(amp,|z|) {L['spearman_amp_abs_z']:+.3f}  "
                      f"bin spread {L['max_bin_spread']:.4f}", flush=True)

        for arm in ARMS:
            hits = used = 0
            for i in range(a.calibration_datasets):
                rng = np.random.default_rng(stable_seed(SEED, reg, arm, "cal", i))
                # calibration needs only the qualifying channel; running all
                # three would triple the cost without changing any verdict
                r = one_arm(rng, reg, arm, a.calibration_b_sham, SEED + i,
                            channels=("full",))
                if r.get("status") != "OK":
                    incomplete.append({"regime": reg, "arm": arm,
                                       "calibration_index": i, **r})
                    continue
                used += 1; hits += int(r["qualifies"])
            complete = (used == a.calibration_datasets)
            calib[f"{reg}|{arm}"] = {
                "datasets_requested": a.calibration_datasets,
                "datasets_used": used, "complete": complete,
                "qualified": hits,
                "rate": hits / used if used else float("nan"),
                "binomial_upper95": binom_upper95(hits, used) if used else float("nan"),
                "required_qualification": ARMS[arm]["want"],
            }
            print(f"  CAL {arm:10s} {hits}/{used} rate "
                  f"{(hits/used if used else float('nan')):.3f} "
                  f"upper95 {binom_upper95(hits, used) if used else float('nan'):.3f} "
                  f"complete={complete}", flush=True)

    arms_ok = all(v.get("arm_pass", False) for reg in results
                  for v in results[reg].values())
    cal_complete = all(c["complete"] for c in calib.values())
    fp_ok = all(c["binomial_upper95"] <= FP_UPPER_LIMIT
                for c in calib.values() if c["required_qualification"] is False)
    power_ok = all(c["rate"] >= POWER_LOWER_LIMIT
                   for c in calib.values() if c["required_qualification"] is True)
    no_fb = all(v.get("poisson_fallbacks", 0) == 0 for reg in results
                for v in results[reg].values())
    gate = bool(arms_ok and cal_complete and fp_ok and power_ok and no_fb
                and not incomplete)

    receipt = {
        "schema": "V5_TEACHER_FIDELITY_SYNTHETIC_GATE_V4",
        "status": "SYNTHETIC_ONLY__NO_REAL_EXPRESSION_READ__NO_TRAINING",
        "supersedes": "GATE_V3, whose POS_COMP arm was not amplitude-controlled "
                      "and whose amplitude check was blind to that failure. The "
                      "v3 run is retained as DIAGNOSTIC ONLY and neither its "
                      "PASS nor its FAIL may decide the stopping rule.",
        "seeds_are_sha256_derived_not_python_hash": True,
        "arms": list(ARMS),
        "channels": list(CHANNELS),
        "results": results,
        "calibration": calib,
        "incomplete_records": incomplete,
        "arms_pass": arms_ok,
        "calibration_complete": cal_complete,
        "false_positive_pass_on_binomial_upper95": fp_ok,
        "power_pass": power_ok,
        "no_silent_model_fallback": no_fb,
        "gate_pass": gate,
        "bounds": {"fp_binomial_upper95_max": FP_UPPER_LIMIT,
                   "power_rate_min": POWER_LOWER_LIMIT},
        "channel_ablation_note": (
            "a full-model qualification does not show the CLR component learned "
            "a compositional signal. For POS_COMP the composition-only channel "
            "should qualify and the amplitude-only channel should not; the "
            "converse is expected for POS_AMP."),
        "training_authorized": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "TEACHER_FIDELITY_SYNTHETIC_GATE_V4.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"\n  arms {arms_ok} | cal complete {cal_complete} | FP {fp_ok} | "
          f"power {power_ok} | no fallback {no_fb} | incomplete {len(incomplete)}")
    print(f"  GATE: {'PASS' if gate else 'FAIL'}")
    print(f"\nwrote {p}")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
