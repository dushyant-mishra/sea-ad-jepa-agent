#!/usr/bin/env python3
"""V74 LANE E: build and PROVE a motif shard plan over the frozen ordered motif universe.

The merge validator already checks that the shards it is handed tile the universe. That
check runs at merge time -- after ~33 h of scoring. This runs the same arithmetic at
PLAN time, over the real 10,249-entry list, before a single motif is scanned.

The invariant, stated once:

    concat(universe[start_i : start_i + count_i] for i in shard order) == universe

  exactly: equal length, zero duplicates, zero omissions, element by element, with a
  matching order-sensitive digest.

The failure this guards is the ragged tail. 10,249 is not a multiple of any round shard
size, so the last shard is short, and an off-by-one there would silently drop or
duplicate motifs without crashing anything. A membership check could not see a
reordering; only an ordered digest can.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ordered_digest(items) -> str:
    """Order-sensitive. A permuted axis with identical membership must not pass."""
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode())
        h.update(b"\x1f")
        h.update(str(s).encode())
        h.update(b"\x1e")
    return h.hexdigest()


def read_universe(path: Path):
    # explicit encoding: an undeclared read decodes cp1252 on Windows
    return [ln.strip() for ln in
            path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def build_plan(n_total: int, shard_size: int):
    """1-based [start, count] slices, exactly as the shard driver's `sed -n a,bp` wants."""
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")
    plan = []
    start = 1
    while start <= n_total:
        count = min(shard_size, n_total - start + 1)
        plan.append({"shard_index": len(plan),
                     "shard_id": "SHARD_%05d" % len(plan),
                     "start_1based": start,
                     "count": count,
                     "end_1based": start + count - 1})
        start += count
    return plan


def verify_plan(universe, plan):
    """Returns (checks dict, reconstructed list). Every check is a separate question;
    a single boolean would hide which property failed."""
    recon = []
    for s in plan:
        recon.extend(universe[s["start_1based"] - 1: s["end_1based"]])

    seen_counts = {}
    for m in recon:
        seen_counts[m] = seen_counts.get(m, 0) + 1
    duplicates = sorted(m for m, c in seen_counts.items() if c > 1)
    omissions = [m for m in universe if m not in seen_counts]

    contiguous = all(
        plan[i]["end_1based"] + 1 == plan[i + 1]["start_1based"]
        for i in range(len(plan) - 1)) if plan else False

    checks = {
        "reconstructed_length_equals_universe_length": len(recon) == len(universe),
        "zero_duplicates": len(duplicates) == 0,
        "zero_omissions": len(omissions) == 0,
        "element_by_element_identical_in_order": recon == universe,
        "ordered_digest_matches": ordered_digest(recon) == ordered_digest(universe),
        "slices_are_contiguous_and_non_overlapping": contiguous,
        "first_slice_starts_at_1": bool(plan) and plan[0]["start_1based"] == 1,
        "last_slice_ends_at_n": bool(plan) and plan[-1]["end_1based"] == len(universe),
        "counts_sum_to_n": sum(s["count"] for s in plan) == len(universe),
    }
    detail = {"n_duplicates": len(duplicates), "n_omissions": len(omissions),
              "first_few_duplicates": duplicates[:5], "first_few_omissions": omissions[:5]}
    return checks, detail, recon


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen-motif-list", required=True)
    ap.add_argument("--frozen-motif-list-sha256", required=True)
    ap.add_argument("--shard-size", type=int, required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)

    path = Path(a.frozen_motif_list)
    if not path.exists():
        print(json.dumps({"status": "REFUSED__FROZEN_MOTIF_LIST_ABSENT",
                          "path": str(path)}, indent=2))
        return 2
    got = sha256_file(path)
    if got != a.frozen_motif_list_sha256.lower():
        print(json.dumps({"status": "REFUSED__FROZEN_MOTIF_LIST_SHA256_MISMATCH",
                          "expected": a.frozen_motif_list_sha256.lower(),
                          "observed": got}, indent=2))
        return 2

    universe = read_universe(path)
    plan = build_plan(len(universe), a.shard_size)
    checks, detail, _ = verify_plan(universe, plan)

    # verdict decided here, then written; it must not exist only in stdout
    status = ("PASS__SHARD_PLAN_TILES_THE_UNIVERSE_EXACTLY" if all(checks.values())
              else "FAIL__SHARD_PLAN_DOES_NOT_TILE_THE_UNIVERSE")

    rec = {
        "schema": "V74_LANEE_MOTIF_SHARD_PLAN_V1",
        "status": status,
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_motif_list": str(path),
        "frozen_motif_list_sha256": got,
        "n_motifs": len(universe),
        "shard_size": a.shard_size,
        "n_shards": len(plan),
        "last_shard_count": plan[-1]["count"] if plan else None,
        "ragged_tail": bool(plan) and plan[-1]["count"] != a.shard_size,
        "universe_ordered_digest": ordered_digest(universe),
        "reconstruction_checks": checks,
        "reconstruction_detail": detail,
        "plan": plan,
        "note": ("This proves the PLAN tiles the universe. It does not prove the shards "
                 "were produced correctly -- that is the merge validator's job, against "
                 "the motif axes actually present in the output feathers."),
    }
    out = Path(a.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")

    persisted = json.loads(out.read_text(encoding="utf-8"))
    print(json.dumps({k: persisted[k] for k in
                      ("status", "n_motifs", "shard_size", "n_shards",
                       "last_shard_count", "ragged_tail", "reconstruction_checks")},
                     indent=2))
    return 0 if persisted["status"].startswith("PASS") else 3


if __name__ == "__main__":
    raise SystemExit(main())
