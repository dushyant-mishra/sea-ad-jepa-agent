#!/usr/bin/env python3
"""Successor audit of the candidate-pool census. Fixed denominator, plus a
direct check of the artifact's NPH52 availability against the axis.

WHAT CHANGED FROM V1, AND WHY

  V1 compared the census against the independently built 29-address artifact
  for the 23 non-reserved addresses in 3 sources - 69 pairs - but dropped a
  pair from the tally whenever BOTH paths reported the address unavailable:

      if cells.sum() == 0 and n_c[addr] == 0:
          continue

  That makes the denominator a function of the data. V1 reported "68 of 68"
  on a run where SEA_AD|2628 was silently dropped, and after a repair that
  makes NPH52|23673 agree it would report "67 of 67" - a smaller denominator
  as the reward for fixing a defect. Agreement that two paths both call an
  address structurally absent is a real agreement about a real fact, and it
  belongs in the numerator and the denominator, not in a `continue`.

  V2 therefore compares a FIXED 23 x 3 = 69 pairs on every run and records the
  both-unavailable case as an agreeing comparison tagged
  `both_structurally_unavailable`. The disagreement V1 was built to catch -
  available in one path and absent in the other - is still a hard failure.

  V2 also adds `nph52_artifact_availability_matches_axis`: the artifact's own
  `address_available` for the NPH52 matrix is compared, address by address,
  against the authenticated feature axis in the stage81a2r provenance table.
  That check does not go through the census at all, so it can fail even if the
  census and the artifact were built from the same wrong assumption - which is
  the failure mode a two-path comparison cannot see.

  The six reserved readouts are still NOT compared and no statistic is
  computed on them. The axis check is structural membership only: which
  addresses the source object carries, never what any of them measured.
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
DEFAULT_NPH52_MATRIX_ID = "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs"
DEFAULT_NPH52_SOURCE_DATASET_ID = "NPH52::MG_data_arranged_updatedId_final_batches.qs"


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def authenticated_axis(provenance_csv, source_dataset_id):
    import pandas as pd
    df = pd.read_csv(provenance_csv, low_memory=False,
                     usecols=["molecular_address_index", "source_dataset_id"])
    sub = df[df.source_dataset_id == source_dataset_id]
    if sub.empty:
        raise SystemExit(f"REFUSE_NO_PROVENANCE_ROWS for {source_dataset_id!r}")
    a = sub.molecular_address_index.astype(np.int64).to_numpy()
    a = a[(a >= 0) & (a < N_ADDR)]
    m = np.zeros(N_ADDR, dtype=bool)
    m[a] = True
    return m, int(len(sub)), int(m.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--nph52-provenance", default=None,
                    help="stage81a2r provenance csv.gz. When given, the "
                         "artifact's NPH52 availability is checked directly "
                         "against the authenticated feature axis.")
    ap.add_argument("--nph52-matrix-id", default=DEFAULT_NPH52_MATRIX_ID)
    ap.add_argument("--nph52-source-dataset-id",
                    default=DEFAULT_NPH52_SOURCE_DATASET_ID)
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

    # ---- 1. the two independent code paths must agree, on a FIXED denominator
    rows = []
    expected_comparisons = len(sources) * len(compare)
    for s in sources:
        m_c = cz[f"{s}__mean"]; d_c = cz[f"{s}__detect"]; f_c = cz[f"{s}__fano"]
        n_c = cz[f"{s}__n_available"]
        sel = is_fit & (src_col == s)
        for addr in compare:
            j = cols29.index(addr)
            cells = sel & avail[:, j]
            n_art, n_cen = int(cells.sum()), int(n_c[addr])
            base = {"source": s, "address": addr,
                    "gene": PARTNER_NAMES.get(addr, "housekeeping/query"),
                    "n_artifact": n_art, "n_census": n_cen}
            # Both paths calling the address structurally absent is AGREEMENT
            # about a real fact. V1 dropped it from the tally, which made the
            # denominator move with the data; here it is counted.
            if n_art == 0 and n_cen == 0:
                rows.append({**base, "both_structurally_unavailable": True,
                             "agree": True})
                continue
            # available in one path and absent in the other is the disagreement
            # the whole audit exists to catch
            if (n_art == 0) != (n_cen == 0):
                failures.append(
                    f"{s}|{addr} AVAILABILITY DISAGREEMENT: artifact "
                    f"n={n_art} vs census n={n_cen}")
                rows.append({**base, "both_structurally_unavailable": False,
                             "agree": False})
                continue
            v = counts[cells, j]
            want = (v.mean(), (v > 0).mean(),
                    v.var() / v.mean() if v.mean() > 0 else np.nan)
            got = (m_c[addr], d_c[addr], f_c[addr])
            dn = abs(n_art - n_cen)
            bad = (dn != 0 or not np.isclose(want[0], got[0], atol=1e-8)
                   or not np.isclose(want[1], got[1], atol=1e-8)
                   or (np.isfinite(want[2]) and not np.isclose(want[2], got[2],
                                                               atol=1e-6)))
            rows.append({**base, "both_structurally_unavailable": False,
                         "mean_artifact": float(want[0]), "mean_census": float(got[0]),
                         "detect_artifact": float(want[1]), "detect_census": float(got[1]),
                         "agree": not bad})
            if bad:
                failures.append(f"{s}|{addr}: artifact n={n_art} "
                                f"mean={want[0]:.6f} vs census n={n_cen} "
                                f"mean={got[0]:.6f}")
    checks["cross_path_agreement"] = {
        "comparisons": len(rows),
        "agreeing": sum(r["agree"] for r in rows),
        "comparisons_expected": expected_comparisons,
        "denominator_is_fixed": len(rows) == expected_comparisons,
        "both_structurally_unavailable": sum(
            1 for r in rows if r.get("both_structurally_unavailable")),
        "pass": (all(r["agree"] for r in rows)
                 and len(rows) == expected_comparisons
                 and expected_comparisons > 0),
    }

    # ---- 1b. the artifact's NPH52 availability against the axis, directly
    if a.nph52_provenance:
        axis, n_prov_rows, n_distinct = authenticated_axis(
            a.nph52_provenance, a.nph52_source_dataset_id)
        mid = az["matrix_id"].astype(str)
        nrows = mid == a.nph52_matrix_id
        detail, wrong = [], []
        if not nrows.any():
            raise SystemExit(f"REFUSE_NO_ROWS_FOR_MATRIX {a.nph52_matrix_id!r}")
        for j, addr in enumerate(cols29):
            in_axis = bool(axis[addr])
            marked = avail[nrows, j]
            all_true, any_true = bool(marked.all()), bool(marked.any())
            ok = (all_true if in_axis else not any_true)
            detail.append({"address": addr, "in_authenticated_axis": in_axis,
                           "artifact_marks_available_all": all_true,
                           "artifact_marks_available_any": any_true,
                           "reserved_readout": addr in reserved, "pass": ok})
            if not ok:
                wrong.append(
                    f"address {addr}: axis says "
                    f"{'PRESENT' if in_axis else 'ABSENT'} but artifact marks "
                    f"{int(marked.sum())}/{int(nrows.sum())} nuclei available")
        checks["nph52_artifact_availability_matches_axis"] = {
            "pass": not wrong,
            "matrix_id": a.nph52_matrix_id,
            "nuclei": int(nrows.sum()),
            "provenance_rows": n_prov_rows,
            "authenticated_addresses": n_distinct,
            "addresses_checked": len(cols29),
            "problems": wrong,
            "per_address": detail,
            "note": ("structural membership only; no count was read at any "
                     "reserved readout address"),
        }
        failures.extend(wrong)

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

    out = {"schema": "V5_AUDIT_CANDIDATE_POOL_CENSUS_V2",
           "supersedes": "V5_AUDIT_CANDIDATE_POOL_CENSUS_V1",
           "what_v2_changes": (
               "the cross-path denominator is fixed at sources x non-reserved "
               "addresses and both-structurally-unavailable pairs are counted "
               "as agreements instead of skipped; an axis check independent of "
               "the census was added"),
           "census_sha256": sha_file(a.census),
           "receipt_sha256": sha_file(a.receipt),
           "artifact_sha256": sha_file(a.artifact),
           "nph52_provenance_sha256": (sha_file(a.nph52_provenance)
                                       if a.nph52_provenance else None),
           "checks": checks,
           "cross_path_rows": rows,
           "failures": failures,
           "all_checks_pass": all(c["pass"] for c in checks.values()),
           "what_this_is_not": (
               "an audit of the census against an independently built artifact "
               "and against internal consistency. It does not establish that "
               "any candidate gene is an exchangeable sham."),
           "training_authorized": False,
           "protected_outcomes_opened": False,
           "producer_sha256": sha_file(os.path.abspath(__file__))}
    p = os.path.join(a.out_dir, "AUDIT_CANDIDATE_POOL_CENSUS_V2.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)

    for k, v in checks.items():
        print(f"  {'PASS' if v['pass'] else 'FAIL'}  {k}")
    c = checks["cross_path_agreement"]
    print(f"\n  cross-path: {c['agreeing']} of {c['comparisons']} agree "
          f"(expected denominator {c['comparisons_expected']}; "
          f"{c['both_structurally_unavailable']} both-structurally-unavailable)")
    if failures:
        print("\n  FAILURES:")
        for f in failures[:20]:
            print(f"      {f}")
    print(f"\n  ALL_CHECKS_PASS: {out['all_checks_pass']}")
    print(f"wrote {p}")
    return 0 if out["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
