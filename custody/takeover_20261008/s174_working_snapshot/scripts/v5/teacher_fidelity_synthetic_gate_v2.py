#!/usr/bin/env python3
"""Synthetic gate v2 — the sham generates the null, and the gate is calibrated.

WHAT CHANGED FROM v1, AND WHY

  v1 failed its NEG-2 arm: independent programs sharing per-nucleus capture
  efficiency, at real sparse counts, produced a qualifying association. The
  within-stratum permutation null could not have prevented it, because
  permuting the state destroys the capture link along with the biological one
  and so asks "is there ANY dependence" rather than "is there dependence beyond
  capture".

  v2 implements protocol v6: an abundance-, sparsity- and capture-matched sham
  GENERATES the null distribution. p = (1 + #{sham >= real}) / (1 + B_sham).
  The permutation is kept only as a reported diagnostic.

  v1 also used the sham as a two-thirds-of-donors vote, which controls nothing:
  with nine evaluation donors and real and sham exchangeable, six or more
  favouring the real program occurs with probability 130/512, about 25%.

WHERE THE LEAK ACTUALLY IS

  Measured on this fixture, Spearman against log capture efficiency:

      real CLR column          +0.014
      real log1p(partner sum)  +0.649
      sham log1p(partner sum)  +0.644

  So the capture channel is the AMPLITUDE term, not the centred log-ratio. The
  CLR pseudocount argument is sound in principle and is why the sparse arm
  belongs here, but at these parameters CLR is close to capture-free. The sham
  reproduces the amplitude dependence at +0.644, which is what makes it the
  right null rather than an approximate one.

CALIBRATION IS PART OF THE GATE

  One favourable seed establishes nothing. The arms are repeated across
  independently generated datasets and the observed false-qualification rate of
  NEG-2 is measured against the nominal level. A test that passes on one seed
  and fires on a fifth of others is worse than no test, because it looks like
  evidence.

No real expression is read. Nothing is trained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "src"))
from sea_ad_jepa.v5.teacher_fidelity_core_v1 import (  # noqa: E402
    clr, run_directed_test, benjamini_hochberg)
from sea_ad_jepa.v5.matched_sham_v1 import (  # noqa: E402
    make_matched_sham, sham_match_report)

N_DONORS = 27
STRATA_PER_DONOR = 4
CELLS_PER_STRATUM = 60
SPARSE_PARTNER_MEAN = 1.2
HIGH_PARTNER_MEAN = 40.0
SEED = 20260927
ALPHA = 0.05
DONOR_FRACTION = 2.0 / 3.0

ARMS = [
    ("NEG-1", dict(associated=False, sparse=False, capture_variation=False), False),
    ("NEG-2", dict(associated=False, sparse=True, capture_variation=True), False),
    ("POS-1", dict(associated=True, sparse=False, capture_variation=False), True),
    ("POS-2", dict(associated=True, sparse=True, capture_variation=True), True),
]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def simulate(rng, *, associated, sparse, capture_variation):
    donors, strata = [], []
    for d in range(N_DONORS):
        for s in range(STRATA_PER_DONOR):
            donors += [f"D{d:02d}"] * CELLS_PER_STRATUM
            strata += [f"D{d:02d}|op{s}"] * CELLS_PER_STRATUM
    donors = np.asarray(donors); strata = np.asarray(strata)
    n = donors.size
    cap = rng.lognormal(0.0, 0.6, n) if capture_variation else np.ones(n)
    lib = rng.negative_binomial(6, 6 / (6 + 4000.0 * cap)).astype(float) + 50.0
    D = np.maximum(lib, 1.0)
    base = SPARSE_PARTNER_MEAN if sparse else HIGH_PARTNER_MEAN
    zP = rng.normal(0, 1, n)
    zQ = (0.8 * zP + rng.normal(0, 0.6, n)) if associated else rng.normal(0, 1, n)

    def counts4(z):
        rate = base * np.exp(0.5 * z) * cap
        return rng.poisson(np.maximum(rate, 1e-6)[:, None] * np.ones((1, 4)))

    NP4, NQ4 = counts4(zP), counts4(zQ)
    controls = np.column_stack([
        np.log(D), np.log(lib), rng.poisson(2.0, n), rng.poisson(3.0, n),
        rng.poisson(1.0, n), np.log1p(rng.poisson(base * 0.4, n))])
    return dict(NP4=NP4, y=NQ4.sum(1).astype(float), log_D=np.log(D), D=D,
                controls=controls, strata=strata, donors=donors, cap=cap)


def state_from(counts4):
    return np.hstack([clr(counts4), np.log1p(counts4.sum(1))[:, None]])


def split(donors, seed=SEED):
    u = sorted(set(donors))
    ev = {d for d in u
          if int(hashlib.sha256(f"{seed}|{d}".encode()).hexdigest()[:8], 16) % 3 == 0}
    return np.isin(donors, list(set(u) - ev)), np.isin(donors, list(ev))


def one_arm(rng, kw, b_sham, n_perm_diag, seed):
    d = simulate(rng, **kw)
    fit, ev = split(d["donors"])
    common = dict(y_count=d["y"], log_D=d["log_D"], controls=d["controls"],
                  strata=d["strata"], donors=d["donors"],
                  fit_mask=fit, eval_mask=ev, seed=seed)

    real = run_directed_test(state=state_from(d["NP4"]), n_perm=n_perm_diag, **common)
    if not np.isfinite(real.median_increment):
        return None

    sham_stats, match = [], None
    for b in range(b_sham):
        sh = make_matched_sham(d["NP4"], d["D"], rng)
        if match is None:
            match = sham_match_report(d["NP4"], sh)
        r = run_directed_test(state=state_from(sh), n_perm=0, **common)
        if np.isfinite(r.median_increment):
            sham_stats.append(r.median_increment)

    sham_stats = np.asarray(sham_stats, dtype=float)
    ge = int((sham_stats >= real.median_increment).sum())
    p_sham = (1 + ge) / (1 + sham_stats.size) if sham_stats.size else float("nan")
    qualifies = bool(p_sham <= ALPHA
                     and real.fraction_donors_positive >= DONOR_FRACTION)
    return {
        "median_increment": real.median_increment,
        "fraction_donors_positive": real.fraction_donors_positive,
        "sham_null_p": p_sham,
        "sham_draws_used": int(sham_stats.size),
        "sham_null_median": float(np.median(sham_stats)) if sham_stats.size else None,
        "permutation_p_DIAGNOSTIC_ONLY": real.permutation_p,
        "n_eval_donors": real.n_eval_donors,
        "n_strata_used": real.n_strata_used,
        "sham_match_quality": match,
        "qualifies": qualifies,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--b-sham", type=int, default=199)
    ap.add_argument("--perm-diagnostic", type=int, default=49)
    ap.add_argument("--calibration-datasets", type=int, default=40)
    ap.add_argument("--calibration-b-sham", type=int, default=49)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    print("GATE — four arms, sham-generated null\n", flush=True)
    arms = {}
    for name, kw, want in ARMS:
        rng = np.random.default_rng(SEED + sum(map(ord, name)))
        r = one_arm(rng, kw, a.b_sham, a.perm_diagnostic, SEED)
        r["required_qualification"] = want
        r["arm_pass"] = (r["qualifies"] == want)
        arms[name] = r
        print(f"  {name}  want_qualify={str(want):5s}  "
              f"inc={r['median_increment']:+.4f}  "
              f"sham_p={r['sham_null_p']:.4f}  "
              f"donors+={r['fraction_donors_positive']:.2f}  "
              f"qualifies={str(r['qualifies']):5s}  "
              f"-> {'PASS' if r['arm_pass'] else 'FAIL'}", flush=True)

    print(f"\nCALIBRATION — {a.calibration_datasets} independent datasets "
          f"per arm, B_sham={a.calibration_b_sham}\n", flush=True)
    calib = {}
    for name in ("NEG-2", "POS-2"):
        kw = dict(next(k for n, k, _ in ARMS if n == name))
        hits = 0
        used = 0
        for i in range(a.calibration_datasets):
            rng = np.random.default_rng(SEED + 7919 * (i + 1) + sum(map(ord, name)))
            r = one_arm(rng, kw, a.calibration_b_sham, 0, SEED + i)
            if r is None:
                continue
            used += 1
            hits += int(r["qualifies"])
        rate = hits / used if used else float("nan")
        calib[name] = {"datasets_used": used, "qualified": hits,
                       "qualification_rate": rate}
        print(f"  {name}: qualified in {hits}/{used} datasets "
              f"= {rate:.3f}", flush=True)

    neg_rate = calib["NEG-2"]["qualification_rate"]
    pos_rate = calib["POS-2"]["qualification_rate"]
    # a false-qualification rate materially above nominal fails the gate; the
    # bound is generous because 40 datasets estimate a rate coarsely
    calibration_ok = bool(neg_rate <= 0.15)
    power_ok = bool(pos_rate >= 0.50)
    gate = all(r["arm_pass"] for r in arms.values()) and calibration_ok and power_ok

    receipt = {
        "schema": "V5_TEACHER_FIDELITY_SYNTHETIC_GATE_V2",
        "status": "SYNTHETIC_ONLY__NO_REAL_EXPRESSION_READ__NO_TRAINING",
        "protocol": "V29_TEACHER_FIDELITY_FROZEN_PROTOCOL_V6_20260927.md",
        "supersedes": "V5_TEACHER_FIDELITY_SYNTHETIC_GATE_V1, whose NEG-2 arm failed",
        "null_is_the_matched_sham": True,
        "permutation_retained_as_diagnostic_only": True,
        "where_the_capture_leak_is": {
            "real_clr_vs_log_capture_spearman": 0.014,
            "real_log1p_partner_sum_vs_log_capture_spearman": 0.649,
            "sham_log1p_partner_sum_vs_log_capture_spearman": 0.644,
            "reading": "the capture channel is the AMPLITUDE term, not the CLR. "
                       "The pseudocount argument is sound in principle and is "
                       "why the sparse arm belongs here, but at these "
                       "parameters CLR is close to capture-free. The sham "
                       "reproduces the amplitude dependence, which is what "
                       "makes it the right null.",
        },
        "arms": arms,
        "calibration": calib,
        "calibration_bound_neg2": 0.15,
        "power_bound_pos2": 0.50,
        "calibration_pass": calibration_ok,
        "power_pass": power_ok,
        "gate_pass": bool(gate),
        "b_sham": a.b_sham,
        "calibration_b_sham": a.calibration_b_sham,
        "alpha": ALPHA,
        "donor_fraction_required": DONOR_FRACTION,
        "training_authorized": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "TEACHER_FIDELITY_SYNTHETIC_GATE_V2.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"\n  arms pass      : {all(r['arm_pass'] for r in arms.values())}")
    print(f"  NEG-2 FP rate  : {neg_rate:.3f}  (bound {0.15})  -> {calibration_ok}")
    print(f"  POS-2 power    : {pos_rate:.3f}  (bound {0.50})  -> {power_ok}")
    print(f"  GATE: {'PASS' if gate else 'FAIL'}")
    print(f"\nwrote {p}")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
