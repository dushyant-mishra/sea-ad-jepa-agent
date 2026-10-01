#!/usr/bin/env python3
"""Mutation sweep for the Phase-B contracts, run in an ISOLATED COPY of the repo files.

S61. The first version of this sweep mutated the live artifacts in place and re-ran the
test suite against them. The suite writes its receipt on every run, so the last mutant's
FAILING receipt was left on disk. I restored the mutated artifacts but not the receipt,
committed, and only then re-ran the tests -- which regenerated a clean receipt that was
never committed. The committed receipt therefore described a mutated run, while my report
cited an uncommitted one. The artifacts were correct throughout; the provenance record
shipped with them was not.

Two structural repairs, so the failure cannot recur rather than merely being undone:

  1. The sweep copies the contract directory into a scratch tree and mutates only the
     copy. Live artifacts are never written to, so no committed receipt can be clobbered
     even if the sweep crashes halfway.
  2. The sweep emits its own receipt from the results it actually observed, instead of a
     receipt hand-authored afterwards from console output.

A test that passes on correct data proves nothing unless it fails on corrupted data, so
each mutation names the test that must catch it and the sweep fails if the wrong test
fires, or if none does.

TRAINING=OFF. PHASE B=STOPPED. No matrix values are read.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

DIR = "results/v64/phase_b_design"
R3 = "V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json"
V3 = "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json"
SUB_TEST = "scripts/v64/test_phase_b_measurement_substrate_contract_v1.py"


def mutations():
    def m(path, fn, name, expect):
        return dict(path=path, fn=fn, name=name, expect=expect)
    return [
      m(R3, lambda d: d["records"][0].__setitem__(
          "realised_large_arm_hg19_start",
          d["records"][0]["realised_large_arm_hg19_start"] + 1),
        "realised large-arm hg19_start incremented", "T19"),
      m(R3, lambda d: (d["records"][0].__setitem__("small_arm_role", "B"),
                       d["records"][0].__setitem__("large_arm_role", "A")),
        "small/large arm roles swapped", "T19"),
      m(R3, lambda d: d["records"][0].__setitem__("required_label", "NONE"),
        "mandatory conditional label removed", "T19"),
      m(R3, lambda d: d["records"][0].__setitem__("reference_id", "R3:bogus"),
        "reference_id renamed so the row binding cannot resolve", "T19"),
      m(R3, lambda d: d["records"][0].__setitem__(
          "realised_large_arm_drawn_side",
          -d["records"][0]["realised_large_arm_drawn_side"]),
        "realised large-arm drawn side flipped", "T19"),
      m(V3, lambda d: d["SECTION_10_ENUMERATION_REFERENCE_RULES"][
          "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"].__setitem__(
          "eligibility", "any pair at all"),
        "R3 eligibility changed under an UNCHANGED identifier", "T17"),
      m(V3, lambda d: d["SECTION_10_ENUMERATION_REFERENCE_RULES"][
          "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"].__setitem__("pairs", 99),
        "R3 declared pair count changed", "T17"),
    ]


def main() -> int:
    live_before = {f: B.sha_file(os.path.join(DIR, f))
                   for f in sorted(os.listdir(DIR)) if f.endswith(".json")}

    scratch = tempfile.mkdtemp(prefix="pbsweep_")
    root = os.path.join(scratch, "repo")
    os.makedirs(os.path.join(root, DIR), exist_ok=True)
    os.makedirs(os.path.join(root, "scripts", "v64"), exist_ok=True)
    for f in os.listdir(DIR):
        shutil.copy2(os.path.join(DIR, f), os.path.join(root, DIR, f))
    for f in os.listdir("scripts/v64"):
        if f.endswith(".py"):
            shutil.copy2(os.path.join("scripts/v64", f),
                         os.path.join(root, "scripts/v64", f))
    for extra in ("results/v64/phase_a_v3", "results/v64/nihcard_exact_supplement",
                  "results/v64/e2_intermediates"):
        if os.path.isdir(extra):
            shutil.copytree(extra, os.path.join(root, extra), dirs_exist_ok=True)
    for f in os.listdir("results/v64"):
        p = os.path.join("results/v64", f)
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(root, "results/v64", f))

    def run_suite():
        r = subprocess.run([sys.executable, SUB_TEST], capture_output=True, text=True,
                           cwd=root)
        failing = set()
        for line in r.stdout.splitlines():
            if "real=False" in line:
                failing.add(line.strip().split("_")[0])
        return failing, r.stdout

    base_fail, base_out = run_suite()
    if base_fail:
        shutil.rmtree(scratch, ignore_errors=True)
        raise SystemExit(f"STOP: the unmutated copy already fails {sorted(base_fail)}")

    results = []
    for mu in mutations():
        p = os.path.join(root, DIR, mu["path"])
        backup = open(p, encoding="utf-8").read()
        d = json.loads(backup)
        mu["fn"](d)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(d, fh, indent=2)
        failing, _ = run_suite()
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(backup)
        caught = mu["expect"] in failing
        results.append(dict(planted=mu["name"], mutated_artifact=mu["path"],
                            must_be_caught_by=mu["expect"],
                            tests_that_fired=sorted(failing),
                            detected=caught,
                            detected_by_the_right_test=caught))
        print(f"  {mu['name']:<52} expect {mu['expect']}  fired {sorted(failing)}  "
              f"{'OK' if caught else 'MISS'}")

    shutil.rmtree(scratch, ignore_errors=True)
    live_after = {f: B.sha_file(os.path.join(DIR, f))
                  for f in sorted(os.listdir(DIR)) if f.endswith(".json")}
    untouched = live_before == live_after

    out = dict(
        schema="V64_PHASE_B_MUTATION_SWEEP_V1", date="2026-09-30", closes="S60, S61",
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        isolation="every mutation was applied to a scratch copy; the live contract "
                  "directory was never written to, so no committed receipt can be "
                  "clobbered by this sweep",
        live_artifacts_untouched=untouched,
        live_digests_before=live_before, live_digests_after=live_after,
        baseline_unmutated_copy_passes=not base_fail,
        n_mutations=len(results),
        all_detected=all(r["detected"] for r in results),
        all_detected_by_the_named_test=all(r["detected_by_the_right_test"]
                                           for r in results),
        mutations=results,
        division_of_labour="T19 guards the conditioning RECORD; T17 guards the rule "
                           "SEMANTICS upstream. Neither alone covers both.",
        status="PASS" if (untouched and not base_fail
                          and all(r["detected"] for r in results)) else "FAIL")
    p = os.path.join(DIR, "V64_PHASE_B_S60_MUTATION_SWEEP_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nlive artifacts untouched: {untouched}")
    print(f"{sum(r['detected'] for r in results)}/{len(results)} detected by the named "
          f"test -> {out['status']}")
    print(f"sweep receipt sha256 {B.sha_file(p)}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
