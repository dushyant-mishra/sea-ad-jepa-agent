#!/usr/bin/env python3
"""Independent audit of the candidate-pool census.

THE CHECK THAT MATTERS

  The census reads Level-4 blocks, decodes every column through each matrix's
  verified decoder, and folds entries into streaming accumulators. The
  published 29-address artifact was built by a DIFFERENT code path months of
  work earlier: it probed 29 specific columns per row with searchsorted.

  If the census is correct, then for the 23 non-reserved addresses the artifact
  also holds, the two paths must agree on mean, detection and Fano over exactly
  the same fitting nuclei. That is an end-to-end verification of decode plus
  accumulate against an independently constructed artifact, not a self-check.

  The six reserved readouts are NOT compared. They are in both objects, but
  computing a statistic on them here would be an inspection, and the ledger
  already records one exposure too many.

The audit refuses on any disagreement beyond floating-point tolerance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from full104_candidate_pool_census_v1 import (          # noqa: E402
    FORBIDDEN, HOUSEKEEPING, PARTNER_NAMES, R8_ADDR, N_ADDR, split_donors)

TOL = 1e-9


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    cz = np.load(a.census, allow_pickle=True)
    receipt = json.load(open(a.receipt))
    az = np.load(a.artifact, allow_pickle=True)

    sources = [str(s) for s in cz["sources"]]
    src_col = az["source"].astype(str)
    donors = az["donor_id"].astype(str)
    counts = az["counts"].astype(np.float64)
    avail = az["address_available"]
    cols29 = [int(c) for c in az["address_columns"]]

    assign = split_donors(zip(src_col, donors))
    is_fit = np.array([assign[(s, d)] == "FIT" for s, d in zip(src_col, donors)])

    reserved = {x for p in R8_ADDR.values() for x in p["readout"]}
    compare = [c for c in cols29 if c not in reserved]

    checks, failures = {}, []

    # ---- 1. the two independent code paths must agree
    rows = []
    for s in sources:
        m_c = cz[f"{s}__mean"]; d_c = cz[f"{s}__detect"]; f_c = cz[f"{s}__fano"]
        n_c = cz[f"{s}__n_available"]
        sel = is_fit & (src_col == s)
        for addr in compare:
            j = cols29.index(addr)
            cells = sel & avail[:, j]
            if cells.sum() == 0 or n_c[addr] == 0:
                continue
            v = counts[cells, j]
            want = (v.mean(), (v > 0).mean(), v.var() / v.mean() if v.mean() > 0 else np.nan)
            got = (m_c[addr], d_c[addr], f_c[addr])
            dn = abs(int(cells.sum()) - int(n_c[addr]))
            bad = (dn != 0 or not np.isclose(want[0], got[0], atol=1e-8)
                   or not np.isclose(want[1], got[1], atol=1e-8)
                   or (np.isfinite(want[2]) and not np.isclose(want[2], got[2], atol=1e-6)))
            rows.append({"source": s, "address": addr,
                         "gene": PARTNER_NAMES.get(addr, "housekeeping/query"),
                         "n_artifact": int(cells.sum()), "n_census": int(n_c[addr]),
                         "mean_artifact": float(want[0]), "mean_census": float(got[0]),
                         "detect_artifact": float(want[1]), "detect_census": float(got[1]),
                         "agree": not bad})
            if bad:
                failures.append(f"{s}|{addr}: artifact n={int(cells.sum())} "
                                f"mean={want[0]:.6f} vs census n={int(n_c[addr])} "
                                f"mean={got[0]:.6f}")
    checks["cross_path_agreement"] = {
        "comparisons": len(rows),
        "agreeing": sum(r["agree"] for r in rows),
        "pass": all(r["agree"] for r in rows) and len(rows) > 0,
    }

    # ---- 2. the firewall actually held
    checks["reserved_readouts_not_compared"] = {
        "pass": not (set(compare) & reserved),
        "reserved": sorted(reserved)}
    checks["forbidden_count"] = {"pass": len(FORBIDDEN) == 48,
                                 "n": len(FORBIDDEN)}

    # ---- 3. evaluation donors contributed nothing
    ev = set(receipt["evaluation_donors_never_used"])
    ft = set(receipt["fitting_donors"])
    checks["donor_arms_disjoint"] = {"pass": not (ev & ft),
                                     "n_fit": len(ft), "n_eval": len(ev)}
    checks["fitting_nuclei_match"] = {
        "pass": receipt["fitting_nuclei"] == int(is_fit.sum()),
        "receipt": receipt["fitting_nuclei"], "recomputed": int(is_fit.sum())}

    # ---- 4. structural availability is not a zero
    n_by_src = {s: int((cz[f"{s}__n_available"] > 0).sum()) for s in sources}
    checks["availability_is_source_specific"] = {
        "pass": len(set(n_by_src.values())) > 1,
        "available_addresses_per_source": n_by_src,
        "why": "if every source reported the same count, the per-matrix "
               "availability masks would not be doing anything"}

    # ---- 5. no negative or impossible marginals
    bad_marg = []
    for s in sources:
        m = cz[f"{s}__mean"]; d = cz[f"{s}__detect"]
        fin = np.isfinite(m)
        if (m[fin] < 0).any():
            bad_marg.append(f"{s}: negative mean")
        if ((d[np.isfinite(d)] < 0) | (d[np.isfinite(d)] > 1)).any():
            bad_marg.append(f"{s}: detection outside [0,1]")
    checks["marginals_in_range"] = {"pass": not bad_marg, "problems": bad_marg}

    out = {"schema": "V5_AUDIT_CANDIDATE_POOL_CENSUS_V1",
           "census_sha256": sha_file(a.census),
           "receipt_sha256": sha_file(a.receipt),
           "artifact_sha256": sha_file(a.artifact),
           "checks": checks,
           "cross_path_rows": rows,
           "failures": failures,
           "all_checks_pass": all(c["pass"] for c in checks.values()),
           "what_this_is_not": (
               "an audit of the census against an independently built artifact "
               "and against internal consistency. It does not establish that "
               "any candidate gene is an exchangeable sham."),
           "producer_sha256": sha_file(os.path.abspath(__file__))}
    p = os.path.join(a.out_dir, "AUDIT_CANDIDATE_POOL_CENSUS_V1.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)

    for k, v in checks.items():
        print(f"  {'PASS' if v['pass'] else 'FAIL'}  {k}")
    if failures:
        print("\n  FAILURES:")
        for f in failures[:20]:
            print(f"      {f}")
    print(f"\n  ALL_CHECKS_PASS: {out['all_checks_pass']}")
    print(f"wrote {p}")
    return 0 if out["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
