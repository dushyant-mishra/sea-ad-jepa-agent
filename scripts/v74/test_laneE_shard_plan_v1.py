#!/usr/bin/env python3
"""Behavioural tests for the V74 Lane E motif shard plan.

Each case names the defect it targets and then constructs an input that exhibits it,
so that every assertion has a reachable failure.

Run:  python scripts/v74/test_laneE_shard_plan_v1.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from laneE_shard_plan_v1 import build_plan, verify_plan, ordered_digest  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append(bool(cond))
    print(("PASS  " if cond else "FAIL  ") + name + ("  " + detail if detail else ""))


def main() -> int:
    # The real shape: 10,249 motifs, which is not a multiple of any round shard size.
    U = ["m%05d" % i for i in range(10249)]

    for size in (128, 256, 512, 1024, 2048):
        plan = build_plan(len(U), size)
        checks, detail, recon = verify_plan(U, plan)
        check("tiles exactly at shard_size=%d (%d shards, tail=%d)"
              % (size, len(plan), plan[-1]["count"]),
              all(checks.values()), "")

    # ---- the ragged tail is real and is covered ------------------------------
    plan512 = build_plan(10249, 512)
    check("512 gives 21 shards with a 9-motif tail",
          len(plan512) == 21 and plan512[-1]["count"] == 9,
          "n=%d tail=%d" % (len(plan512), plan512[-1]["count"]))

    # ---- NEGATIVE: drop the tail shard -> omissions must be detected ----------
    # Would fail if: the checker only verified that each slice was in range.
    bad = plan512[:-1]
    checks, detail, _ = verify_plan(U, bad)
    check("dropping the tail shard is DETECTED as omissions",
          not checks["zero_omissions"] and not checks["counts_sum_to_n"],
          "n_omissions=%d" % detail["n_omissions"])

    # ---- NEGATIVE: off-by-one overlap -> duplicates must be detected ----------
    # Would fail if: slices were only checked for coverage, not for disjointness.
    over = [dict(s) for s in plan512]
    over[1]["start_1based"] -= 1
    over[1]["count"] += 1
    checks, detail, _ = verify_plan(U, over)
    check("an off-by-one overlapping slice is DETECTED as a duplicate",
          not checks["zero_duplicates"], "n_duplicates=%d" % detail["n_duplicates"])

    # ---- NEGATIVE: a GAP of one motif ---------------------------------------
    gap = [dict(s) for s in plan512]
    gap[0]["count"] -= 1
    gap[0]["end_1based"] -= 1
    checks, detail, _ = verify_plan(U, gap)
    check("a one-motif gap is DETECTED",
          not checks["zero_omissions"] and not checks["slices_are_contiguous_and_non_overlapping"],
          "n_omissions=%d" % detail["n_omissions"])

    # ---- NEGATIVE: REORDERED shards with IDENTICAL membership ----------------
    # The case a membership check cannot see. Would fail if the checker compared
    # sets rather than ordered sequences.
    perm = [plan512[1], plan512[0]] + plan512[2:]
    checks, detail, recon = verify_plan(U, perm)
    check("reordered shards: membership is INTACT (no dupes, no omissions)",
          checks["zero_duplicates"] and checks["zero_omissions"])
    check("reordered shards: the ORDERED digest still catches it",
          not checks["ordered_digest_matches"]
          and not checks["element_by_element_identical_in_order"])
    check("reordered shards: a set comparison would have PASSED (so the ordered "
          "check is doing real work)", set(recon) == set(U))

    # ---- NEGATIVE: a shard size of 1 and of N both still tile -----------------
    for size in (1, 10249, 20000):
        plan = build_plan(10249, size)
        checks, _, _ = verify_plan(U, plan)
        check("degenerate shard_size=%d still tiles exactly (%d shards)"
              % (size, len(plan)), all(checks.values()))

    # ---- a non-positive shard size is rejected, not silently clamped ---------
    for bad_size in (0, -1):
        try:
            build_plan(10249, bad_size)
            ok = False
        except ValueError:
            ok = True
        check("shard_size=%d raises rather than looping forever" % bad_size, ok)

    # ---- ordered_digest sanity: it must distinguish order --------------------
    check("ordered_digest distinguishes a swap of two elements",
          ordered_digest(["a", "b"]) != ordered_digest(["b", "a"]))
    check("ordered_digest is stable for identical input",
          ordered_digest(["a", "b"]) == ordered_digest(["a", "b"]))

    n_fail = sum(1 for r in RESULTS if not r)
    print("\n%d tests, %d failures" % (len(RESULTS), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
