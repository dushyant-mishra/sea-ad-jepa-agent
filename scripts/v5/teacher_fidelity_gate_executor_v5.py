#!/usr/bin/env python3
"""Fail-closed executor successor to teacher_fidelity_synthetic_gate_v4.py.

THE DEFECT THIS EXISTS TO REMOVE

  v4 parses its roster as

      regimes = [r.strip() for r in a.regimes.split(",") if r.strip()]

  so `--regimes ''` yields `[]`. The regime loop then never executes, `results`
  and `calibration` stay empty, and the verdict is a series of `all()` calls
  over empty containers. Python evaluates `all([])` as True. v4 printed
  GATE: PASS and exited 0 having done no work whatsoever.

  That is green-by-non-execution inside the tool built to prevent exactly that.

WHAT IS AND IS NOT CHANGED

  The SCIENCE IS IMPORTED, NOT REWRITTEN. `simulate`, `one_arm`,
  `amplitude_leakage`, `stable_seed`, `binom_upper95`, the regime table, the arm
  table and every frozen constant are taken from the v4 module by import. This
  executor changes only gatekeeping: which runs are allowed to start, and which
  results are allowed to become a verdict. Reimplementing the simulation would
  risk silently changing the estimand while claiming to fix a bug.

  v4 IS NOT EDITED. It and its 33,401-byte receipt are historical execution
  evidence. The four-regime numerical result stands: it was produced by a run
  that did the work.

WHAT IS REFUSED, BEFORE ANY SIMULATION STARTS

  EMPTY ROSTER        `--regimes ''` or all-whitespace. A run with nothing to
                      do is a configuration error, never a pass.
  DUPLICATE REGIME    `A,A` is rejected on the raw argument, BEFORE the list
                      becomes a dict, because dict construction would silently
                      collapse it and the receipt would look like a clean run
                      of fewer regimes than were requested.
  UNKNOWN REGIME      any name outside the frozen table.
  SILENT SUBSET       a roster short of the full frozen set runs only with an
                      explicit --partial-diagnostic flag, and such a run can
                      NEVER report an authoritative pass: its verdict field is
                      the string DIAGNOSTIC_NOT_A_VERDICT.

WHAT IS REFUSED AFTER THE RUN, BEFORE THE VERDICT IS FORMED

  Every predicate is evaluated over a container that is FIRST asserted
  non-empty and complete: exactly one record per regime, exactly four arms per
  regime, exactly three channels per arm, exactly four calibration cells per
  regime. A missing cell is a refusal, not a vacuously satisfied `all()`.

WHAT THE RECEIPT NOW CARRIES, so a later reader can tell what was attempted

  argv, the raw --regimes string, the parsed roster, the number of arms and
  calibration cells attempted versus completed, and whether the run was
  partial. v4's receipt recorded only what succeeded, which is how a run that
  attempted nothing looked identical to a run that attempted everything.

STATUS

  This executor has NOT been used to produce a replacement numerical receipt.
  The v4 receipt remains the gate's numerical evidence, validated independently
  by gate_v4_receipt_validator_v2.py. This file exists so that the NEXT run -
  real or synthetic - cannot pass by not running.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

V4_PATH = Path(__file__).resolve().parent / "teacher_fidelity_synthetic_gate_v4.py"


def _load_v4():
    """Import the frozen v4 module. Its simulation code is the science."""
    spec = importlib.util.spec_from_file_location(
        "teacher_fidelity_synthetic_gate_v4", V4_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # v4 guards main() behind __main__
    return mod


# The one-shot channel signature each arm must show. Binding the verdict to
# this closes the independent review's P1: v4 set
#     r["arm_pass"] = (r["qualifies"] == cfg["want"])
# where r["qualifies"] is the FULL model only, so a future POS_COMP run that
# qualified purely through the amplitude channel would still have been green.
# The composition and amplitude ablations were printed and stored but never
# asserted. (full, composition_only, amplitude_only):
REQUIRED_CHANNEL_PATTERN = {
    "NEG_CAP":   (False, False, False),
    "NEG_NOCAP": (False, False, False),
    "POS_AMP":   (True,  False, True),
    "POS_COMP":  (True,  True,  False),
}

# Budgets frozen by protocol v7 and by the v4 run that produced the standing
# receipt. A run at smaller budgets is a smoke test, not the gate.
FROZEN_B_SHAM = 99
FROZEN_NEG_CALIBRATION = 120
FROZEN_POS_CALIBRATION = 30


class RosterRefusal(SystemExit):
    """Raised before any simulation. Exits nonzero with a named reason."""


def check_budgets(b_sham, neg_cal, pos_cal, allow_diagnostic):
    """Frozen budgets, or an explicit diagnostic run. Never a quiet shortfall."""
    short = []
    if b_sham != FROZEN_B_SHAM:
        short.append(f"--b-sham {b_sham} != frozen {FROZEN_B_SHAM}")
    if neg_cal != FROZEN_NEG_CALIBRATION:
        short.append(f"--neg-calibration-datasets {neg_cal} != frozen "
                     f"{FROZEN_NEG_CALIBRATION}")
    if pos_cal != FROZEN_POS_CALIBRATION:
        short.append(f"--calibration-datasets {pos_cal} != frozen "
                     f"{FROZEN_POS_CALIBRATION}")
    if short and not allow_diagnostic:
        raise RosterRefusal(
            "REFUSE_REDUCED_BUDGET: " + "; ".join(short) +
            ". A reduced-budget run is a smoke test and cannot issue gate "
            "authority. Re-run at the frozen budgets, or pass "
            "--partial-diagnostic and accept DIAGNOSTIC_NOT_A_VERDICT.")
    return short


def arm_verdict(rec, arm, channels):
    """An arm passes only if the FULL model lands where the design wants it AND
    the three-channel signature is exactly the required one."""
    want_full = REQUIRED_CHANNEL_PATTERN[arm][0]
    ch = rec.get("channels", {})
    if set(ch) != set(channels):
        return False, (f"channels {sorted(ch)} != {sorted(channels)}")
    got = tuple(bool(ch[c]["qualifies"]) for c in
                ("full", "composition_only", "amplitude_only"))
    if not isinstance(ch["full"]["qualifies"], bool):
        return False, "full.qualifies is not a boolean"
    if got[0] != want_full:
        return False, (f"full qualification {got[0]} != required {want_full}")
    want = REQUIRED_CHANNEL_PATTERN[arm]
    if got != want:
        return False, (f"channel signature {got} != required {want}; the arm "
                       "reached its verdict through the wrong channel")
    return True, ""


def parse_roster(raw, frozen, allow_partial):
    """Fail-closed roster parsing. Every branch here refuses, none repairs."""
    if raw is None:
        raise RosterRefusal("REFUSE_NO_ROSTER: --regimes was not supplied")

    # Split WITHOUT dropping empties, so ',,' and 'A,,B' are visible as the
    # malformed input they are rather than being silently tidied away.
    fields = [f.strip() for f in str(raw).split(",")]
    if not any(fields):
        raise RosterRefusal(
            "REFUSE_EMPTY_ROSTER: --regimes resolved to zero regimes. A run "
            "with nothing to do cannot pass; all([]) is True and that is "
            "precisely the v4 defect this executor exists to remove.")
    if any(f == "" for f in fields):
        raise RosterRefusal(
            f"REFUSE_MALFORMED_ROSTER: --regimes {raw!r} contains an empty "
            "field. Refusing rather than guessing which regimes were meant.")

    seen = []
    for f in fields:
        if f in seen:
            raise RosterRefusal(
                f"REFUSE_DUPLICATE_REGIME: {f!r} appears more than once in "
                f"--regimes {raw!r}. Rejected on the raw argument, before the "
                "list becomes a dict, because dict construction would collapse "
                "it and the receipt would look like a clean shorter run.")
        seen.append(f)

    unknown = [f for f in seen if f not in frozen]
    if unknown:
        raise RosterRefusal(
            f"REFUSE_UNKNOWN_REGIME: {unknown} not in the frozen table "
            f"{sorted(frozen)}")

    missing = [r for r in frozen if r not in seen]
    if missing and not allow_partial:
        raise RosterRefusal(
            f"REFUSE_SILENT_SUBSET: roster omits {missing}. A short roster is "
            "allowed only with --partial-diagnostic, and such a run can never "
            "report an authoritative pass.")
    return seen, bool(missing)


def assert_complete(results, calib, roster, arms, channels):
    """Every predicate below must run over a container proven non-empty."""
    problems = []
    if not results:
        problems.append("results is empty")
    if not calib:
        problems.append("calibration is empty")
    for reg in roster:
        if reg not in results:
            problems.append(f"{reg}: no result record")
            continue
        got_arms = set(results[reg])
        if got_arms != set(arms):
            problems.append(f"{reg}: arms {sorted(got_arms)} != {sorted(arms)}")
        for a in sorted(got_arms & set(arms)):
            rec = results[reg][a]
            if rec.get("status") != "OK":
                problems.append(f"{reg}|{a}: status {rec.get('status')}")
                continue
            got_ch = set(rec.get("channels", {}))
            if got_ch != set(channels):
                problems.append(f"{reg}|{a}: channels {sorted(got_ch)} != "
                                f"{sorted(channels)}")
        for a in arms:
            if f"{reg}|{a}" not in calib:
                problems.append(f"{reg}|{a}: no calibration cell")
    expected_cells = len(roster) * len(arms)
    if len(calib) != expected_cells:
        problems.append(f"calibration has {len(calib)} cells, expected "
                        f"{expected_cells}")
    return problems


def main():
    v4 = _load_v4()
    frozen = list(v4.REGIMES)
    arms = list(v4.ARMS)
    channels = list(v4.CHANNELS)

    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--regimes", default=",".join(frozen))
    ap.add_argument("--partial-diagnostic", action="store_true",
                    help="permit a roster short of the frozen set. Such a run "
                         "reports DIAGNOSTIC_NOT_A_VERDICT and never a pass.")
    ap.add_argument("--b-sham", type=int, default=99)
    ap.add_argument("--calibration-datasets", type=int, default=30)
    ap.add_argument("--neg-calibration-datasets", type=int, default=120)
    ap.add_argument("--calibration-b-sham", type=int, default=49)
    ap.add_argument("--dry-run-roster-only", action="store_true",
                    help="validate the roster and exit without simulating. "
                         "Exercises every refusal path cheaply.")
    a = ap.parse_args()

    # ---- REFUSALS HAPPEN HERE, before out-dir, before any simulation.
    roster, is_partial = parse_roster(a.regimes, frozen, a.partial_diagnostic)
    budget_shortfalls = check_budgets(
        a.b_sham, a.neg_calibration_datasets, a.calibration_datasets,
        a.partial_diagnostic)
    is_diagnostic = bool(is_partial or budget_shortfalls)

    if a.dry_run_roster_only:
        print(json.dumps({"roster_accepted": roster, "partial": is_partial,
                          "would_simulate_arms": len(roster) * len(arms)},
                         indent=2))
        return 0

    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    started = time.time()
    attempted_arms = attempted_cells = 0
    results, calib, incomplete = {}, {}, []

    for reg in roster:
        print(f"\n=== {reg}  {v4.REGIMES[reg]} ===", flush=True)
        results[reg] = {}
        for arm, cfg in v4.ARMS.items():
            attempted_arms += 1
            import numpy as np
            rng = np.random.default_rng(v4.stable_seed(v4.SEED, reg, arm))
            r = v4.one_arm(rng, reg, arm, a.b_sham, v4.SEED, quality=True)
            if r.get("status") != "OK":
                incomplete.append({"regime": reg, "arm": arm, **r})
                results[reg][arm] = r
                print(f"  {arm:10s} {r['status']}", flush=True)
                continue
            r["required"] = cfg["want"]
            # BOUND TO THE CHANNEL SIGNATURE, not to the full model alone.
            ok, why = arm_verdict(r, arm, channels)
            r["arm_pass"] = ok
            r["required_channel_pattern"] = list(REQUIRED_CHANNEL_PATTERN[arm])
            if not ok:
                r["arm_fail_reason"] = why
            if r["qualifies"] != cfg["want"]:
                r.setdefault("arm_fail_reason", "")
            results[reg][arm] = r
            f = r["channels"]["full"]
            print(f"  {arm:10s} want={str(cfg['want']):5s} full p="
                  f"{f['sham_null_p']:.3f} -> "
                  f"{'PASS' if ok else 'FAIL ' + why}", flush=True)

        for arm in v4.ARMS:
            hits = used = 0
            n_cal = (a.neg_calibration_datasets
                     if (not v4.ARMS[arm]["want"] and a.neg_calibration_datasets)
                     else a.calibration_datasets)
            for i in range(n_cal):
                attempted_cells += 1
                import numpy as np
                rng = np.random.default_rng(
                    v4.stable_seed(v4.SEED, reg, arm, "cal", i))
                rr = v4.one_arm(rng, reg, arm, a.calibration_b_sham, v4.SEED)
                if rr.get("status") != "OK":
                    continue
                used += 1
                hits += int(rr["qualifies"])
            calib[f"{reg}|{arm}"] = {
                "datasets_requested": n_cal, "datasets_used": used,
                "complete": used == n_cal, "qualified": hits,
                "rate": (hits / used) if used else float("nan"),
                "binomial_upper95": (v4.binom_upper95(hits, used) if used
                                     else float("nan")),
                "required_qualification": v4.ARMS[arm]["want"],
            }
            print(f"  CAL {arm:10s} {hits}/{used} complete="
                  f"{used == n_cal}", flush=True)

    # ---- COMPLETENESS BEFORE VERDICT. No all() over an unchecked container.
    problems = assert_complete(results, calib, roster, arms, channels)

    neg_cells = [c for c in calib.values()
                 if c["required_qualification"] is False]
    pos_cells = [c for c in calib.values()
                 if c["required_qualification"] is True]
    arm_records = [v for reg in results for v in results[reg].values()]

    if not arm_records:
        problems.append("no arm records at all")
    if not neg_cells:
        problems.append("no negative calibration cells")
    if not pos_cells:
        problems.append("no positive calibration cells")

    arms_ok = bool(arm_records) and all(v.get("arm_pass", False)
                                        for v in arm_records)
    cal_complete = bool(calib) and all(c["complete"] for c in calib.values())
    fp_ok = bool(neg_cells) and all(
        c["binomial_upper95"] <= v4.FP_UPPER_LIMIT for c in neg_cells)
    power_ok = bool(pos_cells) and all(
        c["rate"] >= v4.POWER_LOWER_LIMIT for c in pos_cells)
    no_fb = bool(arm_records) and all(
        v.get("poisson_fallbacks", 0) == 0 for v in arm_records)

    # frozen calibration budgets must be met cell by cell, not just "complete"
    for key, c in calib.items():
        want_n = (FROZEN_POS_CALIBRATION if c["required_qualification"]
                  else FROZEN_NEG_CALIBRATION)
        if c["datasets_requested"] != want_n:
            problems.append(f"calibration {key}: requested "
                            f"{c['datasets_requested']} != frozen {want_n}")

    gate = bool(arms_ok and cal_complete and fp_ok and power_ok and no_fb
                and not incomplete and not problems)

    verdict = "DIAGNOSTIC_NOT_A_VERDICT" if is_diagnostic else gate

    receipt = {
        "schema": "V5_TEACHER_FIDELITY_GATE_EXECUTOR_V5",
        "status": "SYNTHETIC_ONLY__NO_REAL_EXPRESSION_READ__NO_TRAINING",
        "supersedes": "teacher_fidelity_synthetic_gate_v4.py as an EXECUTOR "
                      "only. v4's numerical receipt is unaffected and remains "
                      "the gate's evidence; v4 is preserved unmodified.",
        "science_imported_from": str(V4_PATH.name),
        "science_sha256": hashlib.sha256(V4_PATH.read_bytes()).hexdigest(),
        # execution evidence v4 never recorded
        "argv": sys.argv[1:],
        "regimes_argument_raw": a.regimes,
        "roster_parsed": roster,
        "roster_is_partial": is_partial,
        "budget_shortfalls": budget_shortfalls,
        "is_diagnostic_run": is_diagnostic,
        "required_channel_pattern": {k: list(v) for k, v
                                     in REQUIRED_CHANNEL_PATTERN.items()},
        "frozen_budgets": {"b_sham": FROZEN_B_SHAM,
                           "negative_calibration": FROZEN_NEG_CALIBRATION,
                           "positive_calibration": FROZEN_POS_CALIBRATION},
        "arms_attempted": attempted_arms,
        "arms_completed": sum(1 for v in arm_records
                              if v.get("status") == "OK"),
        "calibration_datasets_attempted": attempted_cells,
        "calibration_cells": len(calib),
        "completeness_problems": problems,
        "arms": arms, "channels": channels,
        "results": results, "calibration": calib,
        "incomplete_records": incomplete,
        "arms_pass": arms_ok,
        "calibration_complete": cal_complete,
        "false_positive_pass_on_binomial_upper95": fp_ok,
        "power_pass": power_ok,
        "no_silent_model_fallback": no_fb,
        "gate_pass": verdict,
        "bounds": {"fp_binomial_upper95_max": v4.FP_UPPER_LIMIT,
                   "power_rate_min": v4.POWER_LOWER_LIMIT},
        "seeds_are_sha256_derived_not_python_hash": True,
        "training_authorized": False,
        "elapsed_sec": round(time.time() - started, 2),
    }
    receipt["producer_sha256"] = hashlib.sha256(
        Path(__file__).resolve().read_bytes()).hexdigest()

    p = os.path.join(a.out_dir, "TEACHER_FIDELITY_GATE_EXECUTOR_V5.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    if problems:
        print(f"\nCOMPLETENESS PROBLEMS ({len(problems)}):")
        for x in problems[:20]:
            print(f"    {x}")
    print(f"\nGATE: {verdict}")
    print(f"wrote {p}")
    return 0 if verdict is True else 1


if __name__ == "__main__":
    sys.exit(main())
