#!/usr/bin/env python3
"""Lane A step 0: is a technical-vs-biological relational gate identifiable at all?

WHY THIS RUNS BEFORE ANY GATE IS DESIGNED

  The 2026-09-28 relational control audit showed the historical TD57B-style
  gate cannot reject a technical-only pseudo-state: a view built from nothing
  but log library size and detected-gene count passes 4/4 donor halves. The
  required successor gate must reject

      NEG-0  clean independent views
      NEG-1  measured technical-only pseudo-state
      NEG-2  LATENT hidden-capture state, of which measured QC is an
             IMPERFECT proxy

  while retaining

      POS-1  planted shared biological state.

  NEG-1 has an obvious answer: residualise each view on the measured QC
  variables. The technical-only view is exactly linear in them, so its shared
  structure vanishes. The question this probe asks is whether that same move
  survives NEG-2, where the shared driver is latent and QC only proxies it.

THE STRUCTURAL WORRY, stated before running so the result cannot be fitted to it

  After residualising on QC, NEG-2 retains the fraction of the hidden factor
  that QC fails to explain, and POS-1 retains essentially all of its biological
  factor. Both are same-cell latents driving both views. They differ only in
  HOW MUCH survives residualisation, which is set by the proxy quality rho -
  a quantity that is unknown in real data.

  If that is the whole story, then no fixed threshold separates NEG-2 from
  POS-1 without assuming rho, and the gate is not identifiable from RNA alone.
  This probe measures the overlap directly instead of arguing about it.

WHAT THIS IS NOT

  Not the gate. Not a decision. No real expression is read; the NPH52 donor,
  operator, library and detected-gene geometry is used only as a realistic
  covariate scaffold, which is what makes the negative arms adversarial rather
  than convenient. No protected readout is touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

PAIR_COUNT = 2048
MIN_INFORMATIVE = 256
DIM = 512


def dig(s):
    return hashlib.sha256(s.encode()).digest()


def pairs(tag, n=DIM):
    c = []
    for a in range(n - 1):
        for b in range(a + 1, n):
            c.append((dig(f"RELCTRL|{tag}|a|{a}|b|{b}"), a, b))
    c.sort(key=lambda x: x[0])
    return np.array([[x[1], x[2]] for x in c[:PAIR_COUNT]], dtype=np.int32)


PX, PY = pairs("X"), pairs("Y")


def distance_matrix(signs):
    p = signs.shape[1]
    pos = (signs == 1).astype(np.int16)
    neg = (signs == -1).astype(np.int16)
    zero = (signs == 0).astype(np.int16)
    nonzero = (signs != 0).sum(1).astype(np.int32)
    same = (pos @ pos.T + neg @ neg.T).astype(np.int32)
    both_zero = (zero @ zero.T).astype(np.int32)
    l1 = nonzero[:, None] + nonzero[None, :] - 2 * same
    info = p - both_zero
    out = np.full((len(signs), len(signs)), np.nan)
    good = info >= MIN_INFORMATIVE
    out[good] = l1[good] / (2.0 * info[good])
    return out


def make_arm(meta, seed, mode, rho=0.7):
    """Two 512-dim views. Only the shared driver differs between arms."""
    n = len(meta)
    rng = np.random.default_rng(seed)
    lib = np.log1p(meta.source_library.to_numpy(float))
    det = np.log1p(meta.detected.to_numpy(float))
    Z = np.c_[(lib - lib.mean()) / lib.std(), (det - det.mean()) / det.std()]

    def emit(driver, k, sd=0.45):
        rr = np.random.default_rng(seed + k)
        inter = rr.normal(0, 0.8, DIM)
        if driver.ndim == 1:
            coef = rr.normal(0, 1, DIM)
            sig = driver[:, None] * coef[None, :]
        else:
            coef = rr.normal(0, 0.9, (driver.shape[1], DIM))
            sig = driver @ coef
        return inter[None, :] + sig + rr.normal(0, sd, (n, DIM))

    if mode == "NEG0_clean":
        return rng.normal(size=(n, DIM)), np.random.default_rng(seed + 999).normal(size=(n, DIM))
    if mode == "NEG1_technical_measured":
        return emit(Z, 10, sd=0.35), emit(Z, 20, sd=0.35)
    if mode == "NEG2_latent_capture":
        # A hidden same-cell factor H drives both views. Measured QC is only a
        # proxy: corr(H, QC-projection) ~= rho. Nothing biological exists here.
        qc = Z @ rng.normal(size=(2,))
        qc = (qc - qc.mean()) / qc.std()
        H = rho * qc + np.sqrt(max(1 - rho ** 2, 0.0)) * rng.normal(size=n)
        return emit(H, 10), emit(H, 20)
    if mode == "POS1_planted_state":
        b = rng.normal(size=n)          # independent of QC by construction
        return emit(b, 10), emit(b, 20)
    raise ValueError(mode)


def residualise(V, Z):
    """Remove the measured-QC subspace (with intercept) from every column."""
    A = np.c_[np.ones(len(Z)), Z]
    beta, *_ = np.linalg.lstsq(A, V, rcond=None)
    return V - A @ beta


def agreement(meta, X, Y):
    """Fraction of within-stratum triplets whose relational order agrees.

    Same shape as the historical statistic: sign-of-pairwise-difference
    distance, triplets inside donor x operator strata.
    """
    donor = meta.donor_id.astype(str).to_numpy()
    op = meta.operator_index.astype(str).to_numpy()
    sx = np.sign(X[:, PX[:, 0]] - X[:, PX[:, 1]]).astype(np.int8)
    sy = np.sign(Y[:, PY[:, 0]] - Y[:, PY[:, 1]]).astype(np.int8)
    hit = tot = 0
    rng = np.random.default_rng(12345)
    for d in np.unique(donor):
        for o in np.unique(op[donor == d]):
            ids = np.where((donor == d) & (op == o))[0]
            if len(ids) < 4:
                continue
            dx = distance_matrix(sx[ids])
            dy = distance_matrix(sy[ids])
            n = len(ids)
            for _ in range(64):
                i, j, k = rng.choice(n, 3, replace=False)
                a, b = dx[i, j], dx[i, k]
                c, e = dy[i, j], dy[i, k]
                if not (np.isfinite(a) and np.isfinite(b)
                        and np.isfinite(c) and np.isfinite(e)):
                    continue
                if a == b or c == e:
                    continue
                tot += 1
                hit += int((a < b) == (c < e))
    return hit / tot if tot else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seeds", type=int, default=8)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    meta = pd.read_csv(a.meta)
    lib = np.log1p(meta.source_library.to_numpy(float))
    det = np.log1p(meta.detected.to_numpy(float))
    Z = np.c_[(lib - lib.mean()) / lib.std(), (det - det.mean()) / det.std()]
    print(f"scaffold: {len(meta)} rows, {meta.donor_id.nunique()} donors, "
          f"{meta.operator_index.nunique()} operators\n")

    rows = []
    arms = ["NEG0_clean", "NEG1_technical_measured", "POS1_planted_state"]
    rhos = [0.3, 0.5, 0.7, 0.9, 0.95]
    print(f"{'arm':30s} {'raw agreement':>16s} {'QC-residualised':>17s}")
    for mode in arms:
        raw, res = [], []
        for s in range(a.seeds):
            X, Y = make_arm(meta, 20260928 + 1000 * s, mode)
            raw.append(agreement(meta, X, Y))
            res.append(agreement(meta, residualise(X, Z), residualise(Y, Z)))
        rows.append({"arm": mode, "rho": None,
                     "raw_mean": float(np.mean(raw)), "raw_sd": float(np.std(raw)),
                     "resid_mean": float(np.mean(res)), "resid_sd": float(np.std(res))})
        print(f"{mode:30s} {np.mean(raw):8.4f} +-{np.std(raw):5.4f} "
              f"{np.mean(res):9.4f} +-{np.std(res):5.4f}")
    for rho in rhos:
        raw, res = [], []
        for s in range(a.seeds):
            X, Y = make_arm(meta, 20260928 + 1000 * s, "NEG2_latent_capture", rho=rho)
            raw.append(agreement(meta, X, Y))
            res.append(agreement(meta, residualise(X, Z), residualise(Y, Z)))
        rows.append({"arm": "NEG2_latent_capture", "rho": rho,
                     "raw_mean": float(np.mean(raw)), "raw_sd": float(np.std(raw)),
                     "resid_mean": float(np.mean(res)), "resid_sd": float(np.std(res))})
        print(f"{'NEG2 latent, proxy rho=' + str(rho):30s} "
              f"{np.mean(raw):8.4f} +-{np.std(raw):5.4f} "
              f"{np.mean(res):9.4f} +-{np.std(res):5.4f}")

    pos = [r for r in rows if r["arm"] == "POS1_planted_state"][0]
    neg2 = [r for r in rows if r["arm"] == "NEG2_latent_capture"]
    worst = max(neg2, key=lambda r: r["resid_mean"])
    separable = worst["resid_mean"] + 2 * worst["resid_sd"] < \
        pos["resid_mean"] - 2 * pos["resid_sd"]

    verdict = {
        "schema": "V5_RELATIONAL_SPECIFICITY_IDENTIFIABILITY_PROBE_V1",
        "rows": rows,
        "pos1_residualised": pos["resid_mean"],
        "worst_neg2_residualised": worst["resid_mean"],
        "worst_neg2_rho": worst["rho"],
        "separable_by_a_fixed_threshold": bool(separable),
        "what_this_is_not": (
            "not the gate and not a decision. A synthetic identifiability "
            "probe on the real NPH52 covariate scaffold. No expression read, "
            "no protected readout touched."),
        "training_authorized": False,
    }
    with open(os.path.join(a.out_dir,
                           "RELATIONAL_SPECIFICITY_IDENTIFIABILITY_PROBE_V1.json"),
              "w") as fh:
        json.dump(verdict, fh, indent=2)

    print(f"\nPOS-1 after residualisation      : {pos['resid_mean']:.4f}")
    print(f"worst NEG-2 after residualisation: {worst['resid_mean']:.4f} "
          f"(proxy rho={worst['rho']})")
    print(f"\nSEPARABLE BY A FIXED THRESHOLD   : {separable}")
    if not separable:
        print("  -> QC residualisation does NOT separate a latent technical\n"
              "     state from a planted biological one. The overlap is set by\n"
              "     the proxy quality rho, which is unobservable in real data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
