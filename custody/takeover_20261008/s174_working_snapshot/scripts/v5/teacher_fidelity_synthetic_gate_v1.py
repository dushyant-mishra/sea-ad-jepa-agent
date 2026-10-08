#!/usr/bin/env python3
"""The synthetic gate. Four arms. All must return their required verdict.

WHY THIS RUNS BEFORE ANY REAL DATA

  Two ratios sharing a denominator correlate through that denominator even when
  their numerators are independent. Excluding genes from the denominator removes
  MEMBERSHIP leakage and does nothing about that. Protocol v5 closes the pathway
  structurally - a count model with log D as an offset, and a CLR predictor that
  is scale-invariant - but "structurally closed" is an argument, and an argument
  is not a test.

  So the whole pipeline, unchanged, is run on data where the truth is known.

THE FOUR ARMS

  NEG-1  independent numerators, varying denominator, HIGH counts
         -> must find NO association
  NEG-2  independent numerators, varying CAPTURE EFFICIENCY, SPARSE counts
         -> must find NO association
  POS-1  genuinely associated numerators, varying denominator, high counts
         -> must FIND the association
  POS-2  genuinely associated, varying capture efficiency, sparse counts
         -> must FIND the association

  NEG-2 is the arm that matters. CLR is scale-invariant only without a
  pseudocount; with log(x + 0.5), scaling x by c does not factor out unless the
  pseudocount scales too. At the one-to-four molecule medians these programs
  actually have, that invariance fails and capture efficiency leaks into a
  predictor assumed to carry none. Passing NEG-1 alone would certify the test in
  a regime the real data is not in.

  The positive arms are equally load-bearing: a test that rejects everything is
  as useless as one that accepts everything, and only the pair distinguishes a
  working test from a dead one.

GEOMETRY MATCHED TO THE REAL COHORT

  Stratum and donor structure, and the sparse arms' count medians, are set from
  the audited FULL104 myeloid artifact rather than chosen for convenience.

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

N_DONORS = 27
STRATA_PER_DONOR = 4
CELLS_PER_STRATUM = 60
SPARSE_PARTNER_MEAN = 1.2      # real partner medians are 1-4 molecules
HIGH_PARTNER_MEAN = 40.0
SEED = 20260927


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def simulate(rng, *, associated: bool, sparse: bool, capture_variation: bool):
    """Return the arrays the estimator consumes.

    associated          is there a genuine per-nucleus link P -> Q?
    sparse              counts at real single-nucleus depth, or high?
    capture_variation   does a per-nucleus capture factor scale EVERYTHING?
    """
    donors, strata = [], []
    for d in range(N_DONORS):
        for s in range(STRATA_PER_DONOR):
            donors += [f"D{d:02d}"] * CELLS_PER_STRATUM
            strata += [f"D{d:02d}|op{s}"] * CELLS_PER_STRATUM
    donors = np.asarray(donors)
    strata = np.asarray(strata)
    n = donors.size

    # per-nucleus capture efficiency: scales every gene alike, so it cancels in
    # a ratio and is invisible to an offset - but NOT to a pseudocounted CLR
    cap = (rng.lognormal(0.0, 0.6, n) if capture_variation else np.ones(n))
    # library size, and the frozen denominator
    lib = rng.negative_binomial(6, 6 / (6 + 4000.0 * cap)).astype(float) + 50.0
    D = np.maximum(lib, 1.0)

    base = SPARSE_PARTNER_MEAN if sparse else HIGH_PARTNER_MEAN
    # latent per-nucleus program levels
    zP = rng.normal(0, 1, n)
    zQ = (0.8 * zP + rng.normal(0, 0.6, n)) if associated else rng.normal(0, 1, n)

    def counts4(z):
        rate = base * np.exp(0.5 * z) * cap
        return rng.poisson(np.maximum(rate, 1e-6)[:, None] * np.ones((1, 4)))

    NP4 = counts4(zP)
    NQ4 = counts4(zQ)

    state = np.hstack([clr(NP4), np.log1p(NP4.sum(1))[:, None]])
    controls = np.column_stack([
        np.log(D), np.log(lib),
        rng.poisson(2.0, n),                       # ambient proxy
        rng.poisson(3.0, n),                       # myeloid identity proxy
        rng.poisson(1.0, n),                       # mitochondrial proxy
        np.log1p(rng.poisson(base * 0.4, n)),      # query-only proxy
    ])
    return dict(y=NQ4.sum(1).astype(float), log_D=np.log(D), controls=controls,
                state=state, strata=strata, donors=donors)


def split(donors, seed=SEED):
    uniq = sorted(set(donors))
    ev = {d for d in uniq
          if int(hashlib.sha256(f"{seed}|{d}".encode()).hexdigest()[:8], 16) % 3 == 0}
    return np.isin(donors, list(set(uniq) - ev)), np.isin(donors, list(ev))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n-perm", type=int, default=199,
                    help="permutations per arm for the GATE; the real run uses "
                         "the frozen B=999")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    ARMS = [
        ("NEG-1", dict(associated=False, sparse=False, capture_variation=False),
         "no_association"),
        ("NEG-2", dict(associated=False, sparse=True, capture_variation=True),
         "no_association"),
        ("POS-1", dict(associated=True, sparse=False, capture_variation=False),
         "association"),
        ("POS-2", dict(associated=True, sparse=True, capture_variation=True),
         "association"),
    ]

    out, pvals = {}, []
    for name, kw, required in ARMS:
        rng = np.random.default_rng(SEED + sum(map(ord, name)))
        d = simulate(rng, **kw)
        fit, ev = split(d["donors"])
        r = run_directed_test(y_count=d["y"], log_D=d["log_D"],
                              controls=d["controls"], state=d["state"],
                              strata=d["strata"], donors=d["donors"],
                              fit_mask=fit, eval_mask=ev,
                              n_perm=a.n_perm, seed=SEED)
        out[name] = {
            "required": required, "settings": kw,
            "median_increment": r.median_increment,
            "fraction_donors_positive": r.fraction_donors_positive,
            "permutation_p": r.permutation_p,
            "n_eval_donors": r.n_eval_donors,
            "n_strata_used": r.n_strata_used,
            "dispersion_alpha": r.dispersion_alpha,
        }
        pvals.append(r.permutation_p)
        print(f"  {name}  required={required:16s} "
              f"median_inc={r.median_increment:+.4f}  "
              f"p={r.permutation_p:.4f}  "
              f"donors+={r.fraction_donors_positive:.2f}  "
              f"strata={r.n_strata_used}", flush=True)

    # Each arm is judged on its own at the per-test level. BH belongs to the
    # REAL family of six directed tests, which are related hypotheses about one
    # dataset; four synthetic arms are four separate experiments and pooling
    # them into one FDR family is a category error. It also makes the POSITIVE
    # arms unpassable whenever the permutation count is small, since BH across
    # four at q=0.05 demands p <= 0.0125 while B permutations floor p at
    # 1/(B+1) - which is how this was caught.
    #
    # Judging NEG at the uncorrected 0.05 is the CONSERVATIVE choice for a gate:
    # it is the easiest level at which a false association can fire, so passing
    # here is a stronger statement than passing under BH.
    ALPHA = 0.05
    verdicts = {}
    for name, _kw, required in ARMS:
        rej = out[name]["permutation_p"] <= ALPHA
        called = bool(rej and out[name]["fraction_donors_positive"] >= 2 / 3)
        out[name]["alpha_used"] = ALPHA
        out[name]["per_test_reject"] = bool(rej)
        out[name]["association_called"] = called
        ok = (called is False) if required == "no_association" else (called is True)
        out[name]["arm_pass"] = ok
        verdicts[name] = ok

    gate = all(verdicts.values())
    receipt = {
        "schema": "V5_TEACHER_FIDELITY_SYNTHETIC_GATE_V1",
        "status": "SYNTHETIC_ONLY__NO_REAL_EXPRESSION_READ__NO_TRAINING",
        "protocol": "V29_TEACHER_FIDELITY_FROZEN_PROTOCOL_V5_20260927.md",
        "protocol_sha256":
            "fe429ede1aa9c1960f8c60a379d17b98ab5882ae07a9063681219ea857c2e362",
        "why": ("two ratios sharing a denominator correlate through it even "
                "when their numerators are independent; excluding genes removes "
                "membership leakage only. v5 closes the pathway structurally, "
                "and this tests that argument rather than trusting it."),
        "NEG_2_is_the_load_bearing_arm": (
            "CLR is scale-invariant only without a pseudocount. With "
            "log(x + 0.5), scaling x by c does not factor out unless the "
            "pseudocount scales too, so at the one-to-four molecule medians "
            "these programs have, capture efficiency leaks into a predictor "
            "assumed to carry none. NEG-1 alone would certify the test in a "
            "regime the real data is not in."),
        "arms": out,
        "gate_pass": gate,
        "consequence_if_failed": (
            "a failing NEG arm means the pipeline manufactures association and "
            "no real result from it means anything. A failing POS arm means it "
            "detects nothing and a null on real data would be uninformative. "
            "Either way the real run does not proceed."),
        "n_permutations_this_gate": a.n_perm,
        "frozen_B_for_the_real_run": 999,
        "multiplicity_note": (
            "each arm is judged at the uncorrected per-test alpha = 0.05. "
            "Benjamini-Hochberg at q = 0.05 belongs to the REAL family of six "
            "directed tests on one dataset; four synthetic arms are four "
            "separate experiments and are not an FDR family. For a NEG arm the "
            "uncorrected level is the conservative choice, being the easiest "
            "level at which a false association could fire."),
        "bh_machinery_checked_separately": True,
        "training_authorized": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "TEACHER_FIDELITY_SYNTHETIC_GATE_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"\n  arm verdicts: " + "  ".join(
        f"{k}={'PASS' if v else 'FAIL'}" for k, v in verdicts.items()))
    print(f"  GATE: {'PASS' if gate else 'FAIL'}")
    print(f"\nwrote {p}")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
