#!/usr/bin/env python3
"""Fail-closed successor to gate_v4_receipt_validator_v1.py.

WHY A SUCCESSOR RATHER THAN AN EDIT

  v1 and its committed validation receipt are historical execution evidence and
  are NOT modified. This is a separately versioned validator, per the
  independent review of 2026-09-28.

WHAT THE INDEPENDENT PROBE FOUND IN v1

  `JEPA_GATE_V4_VALIDATOR_ADVERSARIAL_PROBE_20260928.py`, supplied by the
  reviewer, mutates the frozen receipt 21 ways and checks that each is rejected
  FOR ITS OWN REASON. Run against v1 on 2026-09-28:

      REJECTED_INTENDED_REASON   7
      FALSE_GREEN               16
      REJECTED_WRONG_REASON      0

  Sixteen corrupted receipts were accepted as valid. v1 caught only empty
  regimes, partial regimes, a missing arm, both channel-pattern swaps, a
  missing channel and a nonzero Poisson-fallback counter. Everything else
  passed, including a forged producer digest and a fabricated calibration key.

  The reviewer identified these by source inspection. Executing the probe
  converts that inspection into proof, and the count is worse than the prose
  suggested.

WHAT v2 ADDS, one entry per false green

  1  DIGEST BINDING IS MANDATORY AND BLOCKING. Both --expect-* digests are
     required, and `script_sha != receipt.producer_sha256` is a FAILURE, not
     an informational field. v1 computed that comparison and then ignored it.
  2  EXACT CALIBRATION CENSUS. The 16 keys must be the exact Cartesian product
     of the four frozen regimes and four frozen arms. v1 checked only that
     there were 16 of them, so renaming one to `FAKE_REGIME|POS_COMP` passed.
  3  CALIBRATION FIELDS MUST BE PRESENT, FINITE AND MUTUALLY CONSISTENT:
     `complete == (datasets_used == datasets_requested)`, the stored `rate`
     must equal `qualified / datasets_used`, `binomial_upper95` must be
     present and equal the recomputed Clopper-Pearson endpoint, and the
     original-v4 run must show exactly 120 datasets per negative cell and 30
     per positive cell.
  4  `required_qualification` MUST BE PRESENT, BOOLEAN, AND MATCH ARM POLARITY.
     In v1 an absent field fell through to the positive branch, so deleting it
     silently moved a negative cell into the power numerator.
  5  MODEL-FAMILY PROVENANCE. `model_families` must be exactly
     ["negative_binomial"] and `poisson_fallbacks` must be present and an
     integer zero. v1 used `.get("poisson_fallbacks", 0)`, so deleting the
     counter read as "no fallbacks occurred" — absence of evidence recorded as
     evidence of absence.
  6  SHAM BUDGET. `sham_draws_requested` must equal the frozen 99.
  7  TYPES AND RANGES. `qualifies` must be a real JSON boolean, not a truthy
     string: v1 wrote `bool(ch["full"]["qualifies"])`, and `bool("true")` is
     True, so a string passed. p-values and donor fractions must be finite and
     in range; v1's `math.isnan` check admitted +/-infinity.
  8  QUALIFICATION IS RECOMPUTED, NOT TRUSTED. The frozen producer rule is
     `qualifies = (sham_null_p <= 0.05) and (fraction_donors_positive >= 2/3)`.
     Verified to reproduce all 48 stored flags in the original receipt with
     zero mismatches, so a receipt whose p contradicts its own qualification
     flag is now detectable.
  9  THE RECEIPT'S OWN VERDICT FLAGS ARE RECOMPUTED AND COMPARED. An
     internally contradictory receipt is not a clean PASS in either direction.
 10  DUPLICATE RAW JSON KEYS ARE REJECTED BEFORE dict CONSTRUCTION.
     `json.load` silently keeps the last of a repeated property, so a receipt
     carrying two `A_tuning_sparse` objects parsed identically to a clean one.

WHAT v2 DELIBERATELY DOES NOT DO

  NO RETROACTIVE AMPLITUDE THRESHOLD. The reviewer is explicit, and correct,
  that v4 provides no precommitted numerical bound for the nonlinear
  amplitude-leakage diagnostic. Inventing one now from the observed PASS would
  be fitting an acceptance criterion to a result already seen. v2 therefore
  requires the diagnostic to be PRESENT and FINITE and stops there. A numerical
  bound needs a prospective protocol amendment and a deliberately planted
  cosh-style leak, tested separately.

  NOT A RE-EXECUTION. This audits a receipt against its source. The original
  Monte Carlo is not rerun, and the honest phrase remains "source and receipt
  audited".

  NOT A PER-DATASET RECOUNT. The receipt publishes aggregate calibration
  counts, not 960 individual outcome booleans, so this cannot and does not
  claim to have independently recounted them. A successor generator should
  publish a digest-bound per-dataset outcome and seed inventory.

  POSITIVE CALIBRATION IS SENSITIVITY AT THE TESTED INJECTED STRENGTH, not
  universal power. Calibration n was raised after earlier pilot outcomes were
  seen, so the current calibration is not an independent post-selection
  confirmation. Regimes C and D were labelled untuned but were viewed during
  iterative diagnostics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import numbers
import os
import sys

from scipy.stats import beta as beta_dist

REQUIRED_REGIMES = ["A_tuning_sparse", "B_tuning_dense",
                    "C_untuned_highcap", "D_untuned_verysparse"]
REQUIRED_ARMS = ["NEG_CAP", "NEG_NOCAP", "POS_AMP", "POS_COMP"]
REQUIRED_CHANNELS = ["full", "composition_only", "amplitude_only"]

# (full, composition_only, amplitude_only) qualification each arm must show
REQUIRED_CHANNEL_PATTERN = {
    "NEG_CAP":   (False, False, False),
    "NEG_NOCAP": (False, False, False),
    "POS_AMP":   (True,  False, True),
    "POS_COMP":  (True,  True,  False),
}
# frozen in the v4 producer; see its ALPHA, DONOR_FRACTION and sham budget
ALPHA = 0.05
DONOR_FRACTION = 2.0 / 3.0
SHAM_DRAWS_REQUIRED = 99
P_FLOOR = 1.0 / (SHAM_DRAWS_REQUIRED + 1)      # 0.01, the permutation p floor
MODEL_FAMILY_REQUIRED = ["negative_binomial"]
NEG_DATASETS_REQUIRED = 120
POS_DATASETS_REQUIRED = 30
FP_UPPER_LIMIT = 0.15
POWER_LOWER_LIMIT = 0.50
AMPLITUDE_SCALARS = ["pearson_amp_z", "pearson_amp_z_squared",
                     "spearman_amp_abs_z", "beta_z", "beta_z_squared",
                     "r2_gain_from_z_terms", "max_bin_spread"]
REGIMES_VIEWED_DURING_DIAGNOSTICS = ["C_untuned_highcap", "D_untuned_verysparse"]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


class DuplicateJSONKey(ValueError):
    pass


def _no_duplicate_pairs(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise DuplicateJSONKey(
                f"duplicate JSON key {k!r}: json.load would silently keep the "
                "last one, hiding a second regime, arm or calibration cell")
        seen.add(k)
    return dict(pairs)


def load_receipt_strict(path):
    """Parse rejecting duplicate keys, which dict construction would erase."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.loads(fh.read(), object_pairs_hook=_no_duplicate_pairs)


def clopper_pearson_upper(k, n, conf=0.975):
    if n == 0:
        return float("nan")
    if k >= n:
        return 1.0
    return float(beta_dist.ppf(conf, k + 1, n - k))


def _num(v):
    """A finite real number, and not a bool (JSON true is an int in Python)."""
    return (isinstance(v, numbers.Real) and not isinstance(v, bool)
            and math.isfinite(float(v)))


def validate(receipt, script_sha, receipt_sha):
    f = []
    res = receipt.get("results", {})
    cal = receipt.get("calibration", {})

    # ---- 1. digest binding is BLOCKING, not informational
    producer_field = receipt.get("producer_sha256")
    sha_ok = (script_sha == producer_field)
    if not sha_ok:
        f.append(f"producer digest mismatch: the supplied script hashes to "
                 f"{script_sha}, the receipt names {producer_field}. The "
                 "receipt was not produced by this script.")

    # ---- 2. completeness of regimes and arms
    if sorted(res) != sorted(REQUIRED_REGIMES):
        f.append(f"regimes {sorted(res)} != required {sorted(REQUIRED_REGIMES)}")
    if not res:
        f.append("ZERO regime records: a verdict over empty containers is vacuous")

    recomputed_arm_pass = True
    recomputed_no_fallback = True

    for reg in sorted(res):
        arms = res[reg]
        if sorted(arms) != sorted(REQUIRED_ARMS):
            f.append(f"{reg}: arms {sorted(arms)} != {sorted(REQUIRED_ARMS)}")
        for a in sorted(arms):
            rec = arms[a]
            if rec.get("status") != "OK":
                f.append(f"{reg}|{a}: status {rec.get('status')}")
                recomputed_arm_pass = False
                continue

            # ---- 5. model-family provenance, absence is NOT zero
            fam = rec.get("model_families")
            if fam != MODEL_FAMILY_REQUIRED:
                f.append(f"{reg}|{a}: model_families {fam!r} != "
                         f"{MODEL_FAMILY_REQUIRED!r}; the negative-binomial "
                         "model family is not evidenced")
                recomputed_no_fallback = False
            if "poisson_fallbacks" not in rec:
                f.append(f"{reg}|{a}: poisson_fallbacks counter ABSENT; a "
                         "missing counter is not proof of zero fallbacks")
                recomputed_no_fallback = False
            else:
                pf = rec["poisson_fallbacks"]
                if isinstance(pf, bool) or not isinstance(pf, int):
                    f.append(f"{reg}|{a}: poisson_fallbacks {pf!r} is not an integer")
                    recomputed_no_fallback = False
                elif pf != 0:
                    f.append(f"{reg}|{a}: {pf} Poisson fallbacks")
                    recomputed_no_fallback = False

            # ---- 6. sham budget
            if rec.get("sham_draws_requested") != SHAM_DRAWS_REQUIRED:
                f.append(f"{reg}|{a}: sham_draws_requested "
                         f"{rec.get('sham_draws_requested')!r} != "
                         f"{SHAM_DRAWS_REQUIRED}")

            # ---- channels present, and channels_run agrees
            ch = rec.get("channels", {})
            if sorted(ch) != sorted(REQUIRED_CHANNELS):
                f.append(f"{reg}|{a}: channels {sorted(ch)} != "
                         f"{sorted(REQUIRED_CHANNELS)}")
                recomputed_arm_pass = False
                continue
            if sorted(rec.get("channels_run", [])) != sorted(REQUIRED_CHANNELS):
                f.append(f"{reg}|{a}: channels_run "
                         f"{rec.get('channels_run')!r} != {REQUIRED_CHANNELS!r}")

            # ---- 7/8. types, ranges, and RECOMPUTED qualification
            got = []
            for cn in REQUIRED_CHANNELS:
                cv = ch[cn]
                q = cv.get("qualifies")
                if not isinstance(q, bool):
                    f.append(f"{reg}|{a}|{cn}: qualifies {q!r} is type "
                             f"{type(q).__name__}, not a JSON boolean; a "
                             "truthy string must not pass as True")
                p = cv.get("sham_null_p")
                fd = cv.get("fraction_donors_positive")
                mi = cv.get("median_increment")
                if not _num(p) or not (P_FLOOR - 1e-12 <= float(p) <= 1.0):
                    f.append(f"{reg}|{a}|{cn}: sham_null_p {p!r} is not finite "
                             f"within [{P_FLOOR}, 1]")
                if not _num(fd) or not (0.0 <= float(fd) <= 1.0):
                    f.append(f"{reg}|{a}|{cn}: fraction_donors_positive {fd!r} "
                             "is not finite within [0, 1]")
                if not _num(mi):
                    f.append(f"{reg}|{a}|{cn}: median_increment {mi!r} is not finite")
                if _num(p) and _num(fd):
                    want_q = (float(p) <= ALPHA) and (float(fd) >= DONOR_FRACTION)
                    if isinstance(q, bool) and q != want_q:
                        f.append(
                            f"{reg}|{a}|{cn}: stored qualifies={q} contradicts "
                            f"the frozen rule (p={float(p):.4g} <= {ALPHA} and "
                            f"donors={float(fd):.4g} >= {DONOR_FRACTION:.4g}) "
                            f"which gives {want_q}")
                got.append(bool(q) if isinstance(q, bool) else None)

            # ---- channel binding, which the v1 executor never enforced
            want = REQUIRED_CHANNEL_PATTERN.get(a)
            if want is not None and tuple(got) != want:
                f.append(f"{reg}|{a}: channel pattern {tuple(got)} != required {want}")
                recomputed_arm_pass = False

            # ---- amplitude diagnostic present and finite; NO retroactive bound
            amp = rec.get("amplitude_leakage")
            if not isinstance(amp, dict):
                f.append(f"{reg}|{a}: amplitude_leakage diagnostic ABSENT")
            else:
                for key in AMPLITUDE_SCALARS:
                    if not _num(amp.get(key)):
                        f.append(f"{reg}|{a}: amplitude_leakage.{key} "
                                 f"{amp.get(key)!r} absent or not finite")
                bins = amp.get("conditional_means_by_z_bin")
                if not isinstance(bins, list) or not bins or \
                        not all(_num(x) for x in bins):
                    f.append(f"{reg}|{a}: amplitude_leakage."
                             "conditional_means_by_z_bin absent, empty or "
                             "not all finite")

    # ---- 2b/3/4. calibration census by exact identity, then arithmetic
    required_keys = {f"{r}|{a}" for r in REQUIRED_REGIMES for a in REQUIRED_ARMS}
    got_keys = set(cal)
    if got_keys != required_keys:
        for k in sorted(got_keys - required_keys):
            f.append(f"calibration key {k!r} is not a frozen regime|arm cell")
        for k in sorted(required_keys - got_keys):
            f.append(f"calibration cell {k!r} is MISSING from the census")

    negK = negN = posK = posN = 0
    recomputed_cal_complete = (got_keys == required_keys)
    recomputed_fp_pass = True
    recomputed_power_pass = True

    for key in sorted(got_keys & required_keys):
        c = cal[key]
        arm_name = key.split("|", 1)[1]
        polarity = arm_name.startswith("POS")

        rq = c.get("required_qualification")
        if not isinstance(rq, bool):
            f.append(f"calibration {key}: required_qualification {rq!r} absent "
                     "or not boolean; its absence must not default an arm into "
                     "the power numerator")
            recomputed_cal_complete = False
            continue
        if rq != polarity:
            f.append(f"calibration {key}: required_qualification {rq} "
                     f"contradicts arm polarity ({arm_name} implies {polarity})")

        req, used = c.get("datasets_requested"), c.get("datasets_used")
        k, rate = c.get("qualified"), c.get("rate")
        for nm, v in (("datasets_requested", req), ("datasets_used", used),
                      ("qualified", k)):
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                f.append(f"calibration {key}: {nm} {v!r} is not a non-negative integer")
        if not all(isinstance(v, int) and not isinstance(v, bool)
                   for v in (req, used, k)):
            recomputed_cal_complete = False
            continue

        expect_n = POS_DATASETS_REQUIRED if polarity else NEG_DATASETS_REQUIRED
        if req != expect_n:
            f.append(f"calibration {key}: datasets_requested {req} != the "
                     f"original-v4 {expect_n} for a "
                     f"{'positive' if polarity else 'negative'} cell")
        if used == 0:
            f.append(f"calibration {key} used zero datasets")
            recomputed_cal_complete = False
        if k > used:
            f.append(f"calibration {key}: qualified {k} exceeds datasets_used {used}")
        if c.get("complete") is not (used == req):
            f.append(f"calibration {key}: complete={c.get('complete')!r} "
                     f"contradicts datasets_used {used} vs requested {req}")
            recomputed_cal_complete = False
        if used and (not _num(rate) or abs(float(rate) - k / used) > 1e-9):
            f.append(f"calibration {key}: stored rate {rate!r} != recomputed "
                     f"{k}/{used} = {k / used:.6f}")

        up = clopper_pearson_upper(k, used)
        if polarity:
            posK += k; posN += used
            if used and (k / used) < POWER_LOWER_LIMIT:
                f.append(f"calibration {key}: power {k / used:.3f} below "
                         f"{POWER_LOWER_LIMIT}")
                recomputed_power_pass = False
        else:
            negK += k; negN += used
            stored_up = c.get("binomial_upper95")
            if not _num(stored_up):
                f.append(f"calibration {key}: binomial_upper95 {stored_up!r} "
                         "absent or not finite")
            elif abs(float(stored_up) - up) > 1e-9:
                f.append(f"calibration {key}: recorded upper {float(stored_up):.6f} "
                         f"!= recomputed Clopper-Pearson {up:.6f}")
            if not (up <= FP_UPPER_LIMIT):
                f.append(f"calibration {key}: Clopper-Pearson upper {up:.4f} "
                         f"exceeds {FP_UPPER_LIMIT}")
                recomputed_fp_pass = False

    if receipt.get("incomplete_records"):
        f.append(f"{len(receipt['incomplete_records'])} incomplete records present")

    # ---- 9. the receipt's own verdict flags, recomputed and compared
    recomputed = {
        "arms_pass": recomputed_arm_pass,
        "calibration_complete": recomputed_cal_complete,
        "false_positive_pass_on_binomial_upper95": recomputed_fp_pass,
        "power_pass": recomputed_power_pass,
        "no_silent_model_fallback": recomputed_no_fallback,
    }
    recomputed["gate_pass"] = all(recomputed.values())
    for flag, mine in recomputed.items():
        if flag in receipt and receipt[flag] is not mine:
            f.append(f"receipt reports {flag}={receipt[flag]!r} but independent "
                     f"recomputation gives {mine!r}; an internally "
                     "contradictory receipt is not a clean verdict")

    return {
        "schema": "V5_GATE_V4_RECEIPT_VALIDATOR_V2",
        "supersedes": "gate_v4_receipt_validator_v1.py, which the independent "
                      "2026-09-28 probe showed accepted 16 of 21 corrupted "
                      "receipts. v1 and its receipt are preserved unmodified.",
        "script_sha256": script_sha,
        "receipt_sha256": receipt_sha,
        "producer_sha256_in_receipt": producer_field,
        "script_sha_matches_producer_field": sha_ok,
        "regimes_validated": sorted(res),
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
        "recomputed_verdict_flags": recomputed,
        "failures": f,
        "validated_pass": not f,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--script", required=True)
    # MANDATORY in v2: an unpinned run cannot attest which bytes it read.
    ap.add_argument("--expect-receipt-sha256", required=True)
    ap.add_argument("--expect-script-sha256", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")

    rsha, ssha = sha_file(a.receipt), sha_file(a.script)
    pinned = []
    if rsha != a.expect_receipt_sha256:
        pinned.append(f"receipt sha {rsha} != pinned {a.expect_receipt_sha256}")
    if ssha != a.expect_script_sha256:
        pinned.append(f"script sha {ssha} != pinned {a.expect_script_sha256}")

    try:
        receipt = load_receipt_strict(a.receipt)
    except DuplicateJSONKey as exc:
        os.makedirs(a.out_dir, exist_ok=True)
        out = {"schema": "V5_GATE_V4_RECEIPT_VALIDATOR_V2",
               "receipt_sha256": rsha, "script_sha256": ssha,
               "failures": [f"RAW JSON REJECTED: {exc}"] + pinned,
               "validated_pass": False}
        with open(os.path.join(a.out_dir,
                               "GATE_V4_RECEIPT_VALIDATION_V2.json"), "w") as fh:
            json.dump(out, fh, indent=2)
        print(f"RAW JSON REJECTED: {exc}")
        print("\n  VALIDATED_PASS: False")
        return 1

    os.makedirs(a.out_dir, exist_ok=True)
    out = validate(receipt, ssha, rsha)
    out["pinned_digest_failures"] = pinned
    if pinned:
        out["failures"] = pinned + out["failures"]
        out["validated_pass"] = False
    out["what_this_is_not"] = (
        "an audit of a receipt against its source, NOT a re-execution of the "
        "Monte Carlo, and NOT an independent recount of the 960 per-dataset "
        "outcomes, which the receipt publishes only in aggregate.")
    out["power_caveat"] = (
        "positive calibration is sensitivity AT THE TESTED INJECTED STRENGTH, "
        "not universal power. Calibration n was raised after earlier pilot "
        "outcomes were seen, so it is not an independent post-selection "
        "confirmation.")
    out["amplitude_caveat"] = (
        "the nonlinear amplitude-leakage diagnostic is checked for presence and "
        "finiteness only. v4 froze no numerical bound for it, and inventing one "
        "now from an observed PASS would fit the criterion to the result.")
    out["regime_provenance_caveat"] = (
        f"{REGIMES_VIEWED_DURING_DIAGNOSTICS} were labelled untuned in the "
        "frozen design but were viewed during iterative diagnostics. They are "
        "not a pristine post-selection benchmark.")
    out["producer_sha256"] = sha_file(os.path.abspath(__file__))

    p = os.path.join(a.out_dir, "GATE_V4_RECEIPT_VALIDATION_V2.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)

    print("Fail-closed validation of the gate-v4 receipt (v2)\n")
    print(f"  script  sha256 {ssha}")
    print(f"  receipt sha256 {rsha}")
    print(f"  script matches receipt producer_sha256: "
          f"{out['script_sha_matches_producer_field']}")
    print(f"  regimes {len(out['regimes_validated'])}  "
          f"calibration cells {out['calibration_cells']}  "
          f"channel observations {out['channel_observations_checked']}")

    def _r(v, fmt="{:.4f}"):
        return ("n/a" if v is None or (isinstance(v, float) and not math.isfinite(v))
                else fmt.format(v))

    n, q = out["negative_calibration"], out["positive_calibration"]
    print(f"  negative {n['qualified']}/{n['datasets']} = {_r(n['rate'])}  "
          f"pooled Clopper-Pearson upper {_r(n['pooled_clopper_pearson_upper'])}")
    print(f"  positive {q['qualified']}/{q['datasets']} = {_r(q['rate'])}")
    print(f"  recomputed flags: {out['recomputed_verdict_flags']}")
    if out["failures"]:
        print(f"\n  FAILURES ({len(out['failures'])}):")
        for x in out["failures"][:40]:
            print(f"      {x}")
    print(f"\n  VALIDATED_PASS: {out['validated_pass']}")
    print(f"\nwrote {p}")
    return 0 if out["validated_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
