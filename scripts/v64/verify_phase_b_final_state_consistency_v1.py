#!/usr/bin/env python3
"""Final-state consistency guard. Run before any commit that claims a clean Phase-B state.

S61. The substrate test receipt committed at 7ad38eaf said FAIL 7/9 while the artifacts it
described were correct and the suite, re-run afterwards, passed 9/9. The mutation sweep had
written the receipt while a mutation was live; the artifacts were restored, the receipt was
not, and the commit shipped a provenance record describing a run that no longer existed.
The artifacts were right the whole time. The record travelling with them was wrong, which
on this project is the more serious of the two.

Undoing that is not enough, because nothing would stop it happening again. This guard makes
the inconsistency detectable mechanically:

  C1  no authoritative receipt may say FAIL
  C2  every digest a contract binds must equal the live file it names
  C3  every test receipt must be CURRENT: re-running its suite must reproduce the same
      verdict, which is what a stale receipt left by a mutation sweep cannot do
  C4  the mutation sweep must declare that it left live artifacts untouched

C3 is the one that would have caught S61 directly.

TRAINING=OFF. PHASE B=STOPPED. No matrix values are read.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

DIR = "results/v64/phase_b_design"
PHASE_A = "results/v64/phase_a_v3"
SUITES = [
    ("scripts/v64/test_phase_b_measurement_substrate_contract_v1.py",
     f"{DIR}/V64_PHASE_B_MEASUREMENT_SUBSTRATE_TESTS_V1.json"),
    ("scripts/v64/test_phase_b_downstream_null_contract_v1.py",
     f"{DIR}/V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_TESTS_V3.json"),
]
SWEEP = f"{DIR}/V64_PHASE_B_S60_MUTATION_SWEEP_V1.json"
# S62: this guard's own receipt is its OUTPUT, not an input to audit. Scanning it would
# make a single failure latch permanently -- the next clean run would still read the
# previous FAIL and report FAIL forever, so the guard would be useless exactly after the
# moment it first did its job.
SELF_RECEIPT = "V64_PHASE_B_FINAL_STATE_CONSISTENCY_V1.json"


def walk_digests(o, path=""):
    """Yield (json_path, named_file, recorded_sha256) for every digest bound to a path."""
    if isinstance(o, dict):
        p = o.get("path")
        s = o.get("sha256")
        if isinstance(p, str) and isinstance(s, str) and len(s) == 64:
            yield path, p, s
        for k, v in o.items():
            yield from walk_digests(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_digests(v, f"{path}[{i}]")


def main() -> int:
    findings = []

    # ---- C1 no authoritative receipt may say FAIL
    c1 = []
    for d in (DIR, PHASE_A):
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json") or f == SELF_RECEIPT:
                continue
            try:
                j = json.load(open(os.path.join(d, f)))
            except Exception:
                continue
            st = j.get("status")
            if isinstance(st, str) and st.upper() in ("FAIL", "STOPPED", "ERROR"):
                c1.append(dict(file=f"{d}/{f}", status=st,
                               failing=[t["name"] for t in j.get("tests", [])
                                        if not t.get("is_a_real_test", True)]))
    if c1:
        findings.append(dict(check="C1_no_receipt_says_FAIL", violations=c1))

    # ---- C2 every bound digest equals the live file it names
    c2 = []
    for d in (DIR, PHASE_A):
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json") or f == SELF_RECEIPT:
                continue
            try:
                j = json.load(open(os.path.join(d, f)))
            except Exception:
                continue
            for jp, named, rec in walk_digests(j):
                if not os.path.exists(named):
                    continue
                live = B.sha_file(named)
                if live != rec:
                    c2.append(dict(receipt=f"{d}/{f}", at=jp, names=named,
                                   recorded=rec, live=live))
    if c2:
        findings.append(dict(check="C2_bound_digests_match_live_files", violations=c2))

    # ---- C3 every test receipt is CURRENT
    c3 = []
    for script, receipt in SUITES:
        if not os.path.exists(receipt):
            c3.append(dict(receipt=receipt, reason="absent"))
            continue
        before = json.load(open(receipt))
        shot = open(receipt, encoding="utf-8").read()
        subprocess.run([sys.executable, script], capture_output=True, text=True)
        after = json.load(open(receipt))
        same = (before.get("status") == after.get("status")
                and before.get("n_real_tests") == after.get("n_real_tests")
                and before.get("n_tests") == after.get("n_tests")
                and [t["name"] for t in before.get("tests", [])]
                == [t["name"] for t in after.get("tests", [])]
                and [t["is_a_real_test"] for t in before.get("tests", [])]
                == [t["is_a_real_test"] for t in after.get("tests", [])])
        if not same:
            c3.append(dict(receipt=receipt,
                           committed_status=before.get("status"),
                           committed_real=f"{before.get('n_real_tests')}/"
                                          f"{before.get('n_tests')}",
                           rerun_status=after.get("status"),
                           rerun_real=f"{after.get('n_real_tests')}/"
                                      f"{after.get('n_tests')}",
                           reason="the receipt on disk does not describe what the suite "
                                  "produces against the current artifacts"))
    if c3:
        findings.append(dict(check="C3_test_receipts_are_current", violations=c3))

    # ---- C4 the mutation sweep left live artifacts untouched
    c4 = []
    if os.path.exists(SWEEP):
        s = json.load(open(SWEEP))
        if s.get("live_artifacts_untouched") is not True:
            c4.append(dict(receipt=SWEEP,
                           reason="the sweep does not assert it left live artifacts "
                                  "untouched, so it may have clobbered a receipt"))
        if s.get("live_digests_before") != s.get("live_digests_after"):
            c4.append(dict(receipt=SWEEP,
                           reason="the sweep's before/after live digests differ"))
    else:
        c4.append(dict(receipt=SWEEP, reason="absent"))
    if c4:
        findings.append(dict(check="C4_sweep_left_live_artifacts_untouched",
                             violations=c4))

    out = dict(
        schema="V64_PHASE_B_FINAL_STATE_CONSISTENCY_V1", date="2026-09-30",
        closes="S61",
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        checks=["C1_no_receipt_says_FAIL", "C2_bound_digests_match_live_files",
                "C3_test_receipts_are_current",
                "C4_sweep_left_live_artifacts_untouched"],
        which_check_would_have_caught_S61="C3",
        self_receipt_excluded_from_C1_and_C2=SELF_RECEIPT,
        why_self_excluded="S62: auditing its own verdict would latch the guard into a "
                          "permanent FAIL after its first real detection",
        why="S61 was a receipt that no longer described the artifacts shipped beside it. "
            "C1 and C2 would not have seen it -- the artifacts were correct and no bound "
            "digest was wrong. Only re-running the suite and comparing verdicts exposes a "
            "receipt left behind by an earlier, different run.",
        findings=findings,
        status="PASS" if not findings else "FAIL")
    p = os.path.join(DIR, "V64_PHASE_B_FINAL_STATE_CONSISTENCY_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    for c in out["checks"]:
        hit = next((f for f in findings if f["check"] == c), None)
        print(f"  {c:<44} {'FAIL ' + str(len(hit['violations'])) if hit else 'PASS'}")
    print(f"\n{out['status']}   receipt sha256 {B.sha_file(p)}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
