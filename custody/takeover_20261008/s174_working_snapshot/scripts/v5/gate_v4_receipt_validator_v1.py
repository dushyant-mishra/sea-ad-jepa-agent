#!/usr/bin/env python3
"""Independent validator for the immutable gate-v4 script/receipt pair.

WHY A SEPARATE VALIDATOR

  The v4 executor can issue an authoritative-looking PASS having done nothing.
  Demonstrated: `--regimes ''` records zero regimes and zero calibration cells,
  and every pass condition is an `all()` over an empty container, which Python
  evaluates True. It printed GATE: PASS and exited 0.

  That defect is in the EXECUTOR's verdict logic. It does not invalidate the
  recorded four-regime numerical result, which was produced by a run that did
  the work. So the original script and its 33,401-byte receipt are preserved
  unmodified as historical execution evidence, and this validator recomputes
  the verdict from that receipt independently, pinned to both digests.

WHAT IT ENFORCES, none of which the executor checked

  COMPLETENESS   exactly the four frozen regimes, no omissions, duplicates or
                 unknown names; each with exactly four arms; each arm with
                 exactly three channels. 16 calibration cells, all complete.
  CHANNEL BINDING  the executor's arm_pass inspected the FULL model only, so a
                 run in which POS_COMP qualified solely on the amplitude channel
                 would still have passed. Required per regime:
                     POS_AMP   full True,  composition False, amplitude True
                     POS_COMP  full True,  composition True,  amplitude False
                     both NEG  unqualified in every channel
  ARITHMETIC     the negative and positive calibration totals are recomputed
                 from the per-cell records rather than trusted.
  THE STATED TEST  the false-positive bound is the exact Clopper-Pearson upper
                 endpoint beta.ppf(0.975, k+1, n-k) against 0.15. It is
                 recomputed with that formula and not silently replaced by a
                 different interval.
  HYGIENE        no NaN anywhere in a verdict-bearing field, no Poisson
                 fallback, no incomplete records.

WHAT IT DOES NOT CLAIM

  This audits a receipt against its source. It is NOT a re-execution of the
  Monte Carlo. Without the original runtime command, stdout and environment
  from the machine that ran it, the honest statement is "source and receipt
  audited", never "independently reexecuted".

  30/30 positive calibration is sensitivity AT THE TESTED INJECTED STRENGTH,
  not universal power.

  Regimes C and D were labelled untuned in the frozen design, but they were
  viewed during iterative diagnostics. They are not a pristine post-selection
  benchmark and this validator does not describe them as one.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

from scipy.stats import beta as beta_dist

REQUIRED_REGIMES = {"A_tuning_sparse", "B_tuning_dense",
                    "C_untuned_highcap", "D_untuned_verysparse"}
REQUIRED_ARMS = {"NEG_CAP", "NEG_NOCAP", "POS_AMP", "POS_COMP"}
REQUIRED_CHANNELS = {"full", "composition_only", "amplitude_only"}
# (full, composition_only, amplitude_only) qualification each arm must show
REQUIRED_CHANNEL_PATTERN = {
    "NEG_CAP":   (False, False, False),
    "NEG_NOCAP": (False, False, False),
    "POS_AMP":   (True,  False, True),
    "POS_COMP":  (True,  True,  False),
}
FP_UPPER_LIMIT = 0.15
POWER_LOWER_LIMIT = 0.50
REGIMES_VIEWED_DURING_DIAGNOSTICS = {"C_untuned_highcap", "D_untuned_verysparse"}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def clopper_pearson_upper(k, n, conf=0.975):
    if n == 0:
        return float("nan")
    if k >= n:
        return 1.0
    return float(beta_dist.ppf(conf, k + 1, n - k))


def validate(receipt, script_sha, receipt_sha):
    f = []          # failures
    res = receipt.get("results", {})
    cal = receipt.get("calibration", {})

    # ---- completeness
    got_regimes = set(res)
    if got_regimes != REQUIRED_REGIMES:
        f.append(f"regimes {sorted(got_regimes)} != required "
                 f"{sorted(REQUIRED_REGIMES)}")
    if len(res) != len(REQUIRED_REGIMES):
        f.append(f"expected {len(REQUIRED_REGIMES)} regime records, got {len(res)}")
    if not res:
        f.append("ZERO regime records: a verdict over empty containers is vacuous")

    for reg, arms in res.items():
        if set(arms) != REQUIRED_ARMS:
            f.append(f"{reg}: arms {sorted(arms)} != {sorted(REQUIRED_ARMS)}")
        for arm, rec in arms.items():
            if rec.get("status") != "OK":
                f.append(f"{reg}|{arm}: status {rec.get('status')}")
                continue
            ch = rec.get("channels", {})
            if set(ch) != REQUIRED_CHANNELS:
                f.append(f"{reg}|{arm}: channels {sorted(ch)} != "
                         f"{sorted(REQUIRED_CHANNELS)}")
                continue
            # ---- channel binding, which the executor never enforced
            want = REQUIRED_CHANNEL_PATTERN.get(arm)
            got = (bool(ch["full"]["qualifies"]),
                   bool(ch["composition_only"]["qualifies"]),
                   bool(ch["amplitude_only"]["qualifies"]))
            if want is not None and got != want:
                f.append(f"{reg}|{arm}: channel pattern {got} != required {want}")
            for cn, cv in ch.items():
                for key in ("sham_null_p", "median_increment",
                            "fraction_donors_positive"):
                    v = cv.get(key)
                    if v is None or (isinstance(v, float) and math.isnan(v)):
                        f.append(f"{reg}|{arm}|{cn}: {key} is NaN/absent")
            if rec.get("poisson_fallbacks", 0):
                f.append(f"{reg}|{arm}: {rec['poisson_fallbacks']} Poisson fallbacks")

    # ---- calibration, recomputed rather than trusted
    if len(cal) != len(REQUIRED_REGIMES) * len(REQUIRED_ARMS):
        f.append(f"expected {len(REQUIRED_REGIMES)*len(REQUIRED_ARMS)} "
                 f"calibration cells, got {len(cal)}")
    negK = negN = posK = posN = 0
    for key, c in cal.items():
        if not c.get("complete"):
            f.append(f"calibration {key} incomplete: "
                     f"{c.get('datasets_used')}/{c.get('datasets_requested')}")
        if c.get("datasets_used", 0) == 0:
            f.append(f"calibration {key} used zero datasets")
        k, n = c.get("qualified", 0), c.get("datasets_used", 0)
        if c.get("required_qualification") is False:
            negK += k; negN += n
            up = clopper_pearson_upper(k, n)
            if not (up <= FP_UPPER_LIMIT):
                f.append(f"calibration {key}: Clopper-Pearson upper {up:.4f} "
                         f"exceeds {FP_UPPER_LIMIT}")
            if c.get("binomial_upper95") is not None and \
                    abs(c["binomial_upper95"] - up) > 1e-9:
                f.append(f"calibration {key}: recorded upper "
                         f"{c['binomial_upper95']:.6f} != recomputed {up:.6f}")
        else:
            posK += k; posN += n
            if n and (k / n) < POWER_LOWER_LIMIT:
                f.append(f"calibration {key}: power {k/n:.3f} below "
                         f"{POWER_LOWER_LIMIT}")

    if receipt.get("incomplete_records"):
        f.append(f"{len(receipt['incomplete_records'])} incomplete records present")

    summary = {
        "script_sha256": script_sha,
        "receipt_sha256": receipt_sha,
        "producer_sha256_in_receipt": receipt.get("producer_sha256"),
        "script_sha_matches_producer_field":
            script_sha == receipt.get("producer_sha256"),
        "regimes_validated": sorted(got_regimes),
        "calibration_cells": len(cal),
        "negative_calibration": {"qualified": negK, "datasets": negN,
                                 "rate": negK / negN if negN else None,
                                 "pooled_clopper_pearson_upper":
                                     clopper_pearson_upper(negK, negN)},
        "positive_calibration": {"qualified": posK, "datasets": posN,
                                 "rate": posK / posN if posN else None},
        "channel_observations_checked":
            sum(len(r.get("channels", {})) for reg in res.values()
                for r in reg.values()),
        "failures": f,
        "validated_pass": not f,
    }
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--expect-receipt-sha256", default=None)
    ap.add_argument("--expect-script-sha256", default=None)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rsha, ssha = sha_file(a.receipt), sha_file(a.script)
    pinned = []
    if a.expect_receipt_sha256 and rsha != a.expect_receipt_sha256:
        pinned.append(f"receipt sha {rsha} != pinned {a.expect_receipt_sha256}")
    if a.expect_script_sha256 and ssha != a.expect_script_sha256:
        pinned.append(f"script sha {ssha} != pinned {a.expect_script_sha256}")

    receipt = json.load(open(a.receipt))
    out = validate(receipt, ssha, rsha)
    out["pinned_digest_failures"] = pinned
    if pinned:
        out["failures"] = pinned + out["failures"]
        out["validated_pass"] = False
    out["schema"] = "V5_GATE_V4_RECEIPT_VALIDATOR_V1"
    out["what_this_is_not"] = (
        "an audit of a receipt against its source, NOT a re-execution of the "
        "Monte Carlo. Without the original runtime command, stdout and "
        "environment from the machine that ran it, the honest statement is "
        "'source and receipt audited', never 'independently reexecuted'.")
    out["power_caveat"] = ("positive calibration is sensitivity AT THE TESTED "
                           "INJECTED STRENGTH, not universal power.")
    out["regime_provenance_caveat"] = (
        f"{sorted(REGIMES_VIEWED_DURING_DIAGNOSTICS)} were labelled untuned in "
        "the frozen design but were viewed during iterative diagnostics. They "
        "are not a pristine post-selection benchmark.")
    out["producer_sha256"] = sha_file(os.path.abspath(__file__))

    p = os.path.join(a.out_dir, "GATE_V4_RECEIPT_VALIDATION_V1.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)

    print("Independent validation of the gate-v4 receipt\n")
    print(f"  script  sha256 {ssha}")
    print(f"  receipt sha256 {rsha}")
    print(f"  script matches receipt producer_sha256: "
          f"{out['script_sha_matches_producer_field']}")
    print(f"  regimes {len(out['regimes_validated'])}  "
          f"calibration cells {out['calibration_cells']}  "
          f"channel observations {out['channel_observations_checked']}")
    def _r(v, fmt="{:.4f}"):
        # a vacuous receipt has no rate at all; reporting must still be clean,
        # because a crash is not a clean rejection
        return "n/a" if v is None or (isinstance(v, float) and math.isnan(v))             else fmt.format(v)
    n = out["negative_calibration"]; q = out["positive_calibration"]
    print(f"  negative {n['qualified']}/{n['datasets']} = {_r(n['rate'])}  "
          f"pooled Clopper-Pearson upper "
          f"{_r(n['pooled_clopper_pearson_upper'])}")
    print(f"  positive {q['qualified']}/{q['datasets']} = {_r(q['rate'])}")
    if out["failures"]:
        print(f"\n  FAILURES ({len(out['failures'])}):")
        for x in out["failures"][:30]:
            print(f"      {x}")
    print(f"\n  VALIDATED_PASS: {out['validated_pass']}")
    print(f"\nwrote {p}")
    return 0 if out["validated_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
