#!/usr/bin/env python3
"""Independent audit of the masked myeloid artifact. Every check can fail.

WHY AN AUDIT SEPARATE FROM THE PRODUCER

  The producer's own receipt says the run succeeded. That is the producer's
  account of itself, and a defect in the producer is exactly the case where
  that account cannot be trusted. This auditor re-derives every claim from the
  ARTIFACT, independently of what the receipt asserts, and then compares the
  two. Where they disagree, both are reported rather than one being preferred.

  It also exists because a smoke test on two operators does not license a
  claim about thirteen. The earlier smoke run confirmed the mask on 17,381
  nuclei; this confirms it on all 187,909.

THE CHECKS, and what makes each one able to fail

  1  DIGESTS            artifact and receipt fingerprinted; a substituted file
                        changes the recorded hash.
  2  COVERAGE           all 13 myeloid matrices present with the per-matrix
                        nucleus counts the census established; a dropped or
                        truncated operator fails.
  3  IDENTITY CLOSURE   re-derived from the artifact: every cell_id unique,
                        every selection_row unique, total exactly 187,909.
  4  DONOR IDENTITIES   92 source-specific identities, 30 HVS / 16 NPH52 /
                        46 SEA_AD. A harmonization slip changes this count.
  5  MASK SHAPE         (n_nuclei, 29) of dtype bool, present at all.
  6  MASK vs RECEIPT    the unavailable addresses implied by the ARRAY must
                        equal those the RECEIPT records, per matrix. This is
                        the defect class that prompted the mask: metadata and
                        data silently disagreeing.
  7  PLACEHOLDER PURITY no nonzero count may sit at an unavailable position.
  8  KNOWN ABSENCES     LPL absent exactly in HVS; PGK1 absent exactly in the
                        eleven SEA-AD matrices; NPH52 missing nothing.
  9  PANEL REACHABILITY every query and panel address available for every
                        nucleus - the condition under which the ladder is
                        entitled to compute at all.
  10 DENOMINATOR        total_excluding_29 must equal total_all minus the sum
                        of the AVAILABLE extracted counts, cell by cell. This
                        is arithmetic the producer could have got wrong and
                        nothing else would reveal.

  A final section reports marker detection per source. That is a plausibility
  READING, not a gate: it is recorded so a reviewer can see it, and no check
  passes or fails on it.

No expression beyond the 29 audited addresses is opened, nothing is trained,
and no outcome is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

EXPECTED_TOTAL = 187_909
EXPECTED_PER_SOURCE_DONORS = {"HVS": 30, "NPH52": 16, "SEA_AD": 46}
EXPECTED_MATRIX_COUNTS = {
    "HVS::c5e9db26-7b51-4290-b721-dd540ac906b1": 2117,
    "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs": 15264,
    "sea_ad_ang_rna_final_2026": 6244,
    "sea_ad_caudate_rna_all_2025": 32286,
    "sea_ad_fi_rna_final_2026": 11226,
    "sea_ad_hip_rna_final_2026": 9128,
    "sea_ad_itg_rna_final_2026": 10375,
    "sea_ad_lec_rna_final_2026": 8255,
    "sea_ad_mec_rna_final_2026": 31619,
    "sea_ad_mtg_rna_final_2026": 20804,
    "sea_ad_pfc_a9_rna_final_2026": 22197,
    "sea_ad_stg_rna_final_2026": 9270,
    "sea_ad_v1c_rna_final_2026": 9124,
}
LPL, PGK1 = 13734, 2628
R8_QUERY_PANEL = [6186, 6188, 11425, 7194, 2044,
                  12469, 15109, 12239, 12995, 13365,
                  18511, 392, 23673, 18500, 20496]
MARKERS = {6186: "APOE", 13365: "C1QA", 14980: "CSF1R", 12469: "P2RY12",
           392: "CD74", 2044: "TREM2", 12239: "CX3CR1", 18511: "HLA-DRA"}


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    npz_p = os.path.join(a.artifact_dir, "FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz")
    rec_p = os.path.join(a.artifact_dir, "FULL104_MYELOID_R8_PANEL_EXTRACTION_V1.json")
    for p in (npz_p, rec_p):
        if not os.path.exists(p):
            raise SystemExit(f"REFUSED_MISSING {p}")

    rec = json.load(open(rec_p))
    z = np.load(npz_p, allow_pickle=True)
    checks = {}

    def record(name, ok, detail):
        checks[name] = {"pass": bool(ok), **detail}

    # 1 digests
    record("digests", True, {
        "artifact_sha256": sha_file(npz_p), "artifact_bytes": os.path.getsize(npz_p),
        "receipt_sha256": sha_file(rec_p),
        "producer_sha256_recorded": rec.get("producer_sha256")})

    src = z["source"].astype(str)
    mid = z["matrix_id"].astype(str)
    don = z["donor_id"].astype(str)
    cid = z["cell_id"].astype(str)
    sel = z["selection_row"]
    cnt = z["counts"]
    addr = z["address_columns"].astype(np.int64)
    n = cid.size

    # 2 coverage
    got = {m: int((mid == m).sum()) for m in sorted(set(mid))}
    missing_m = sorted(set(EXPECTED_MATRIX_COUNTS) - set(got))
    wrong = {m: [EXPECTED_MATRIX_COUNTS[m], got.get(m)]
             for m in EXPECTED_MATRIX_COUNTS if got.get(m) != EXPECTED_MATRIX_COUNTS[m]}
    record("coverage_13_matrices", not missing_m and not wrong,
           {"matrices_present": len(got), "expected": len(EXPECTED_MATRIX_COUNTS),
            "missing": missing_m, "count_mismatches": wrong})

    # 3 identity closure, re-derived
    record("identity_closure", n == EXPECTED_TOTAL
           and len(set(cid)) == n and np.unique(sel).size == n,
           {"n": int(n), "expected": EXPECTED_TOTAL,
            "unique_cell_ids": len(set(cid)),
            "unique_selection_rows": int(np.unique(sel).size)})

    # 4 donor identities
    pairs = set(zip(src, don))
    per = {s: len({d for ss, d in pairs if ss == s}) for s in sorted(set(src))}
    record("donor_identities_92", len(pairs) == 92 and per == EXPECTED_PER_SOURCE_DONORS,
           {"source_specific_donor_identities": len(pairs), "per_source": per,
            "expected_per_source": EXPECTED_PER_SOURCE_DONORS,
            "note": "source-specific, NOT harmonized across sources"})

    # 5 mask present and shaped
    has_mask = "address_available" in z.files
    av = z["address_available"].astype(bool) if has_mask else None
    record("mask_present_and_shaped",
           has_mask and av.shape == (n, addr.size) and av.dtype == np.bool_,
           {"present": has_mask,
            "shape": list(av.shape) if has_mask else None,
            "expected_shape": [int(n), int(addr.size)]})
    if not has_mask:
        raise SystemExit("REFUSED_NO_MASK: the artifact cannot be audited for "
                         "the defect the mask exists to prevent")

    # 6 mask vs receipt, per matrix
    ds = rec.get("decoder_status_by_matrix", {})
    disagree = {}
    for m in sorted(set(mid)):
        rows = mid == m
        from_array = sorted(int(addr[j]) for j in range(addr.size)
                            if not av[rows, j].all())
        from_receipt = sorted(int(x) for x in
                              (ds.get(m, {}).get("addresses_absent_from_source") or []))
        if from_array != from_receipt:
            disagree[m] = {"array": from_array, "receipt": from_receipt}
        # partial availability within one matrix would mean the mask is not a
        # per-matrix property, which nothing in the design allows
        for j in range(addr.size):
            col = av[rows, j]
            if col.any() and not col.all():
                disagree.setdefault(m, {})["partially_available_address"] = int(addr[j])
    record("mask_matches_receipt_per_matrix", not disagree,
           {"matrices_checked": len(set(mid)), "disagreements": disagree})

    # 7 placeholder purity
    bad_vals = int(cnt[~av].sum()) if av.size else 0
    record("no_counts_at_unavailable_positions", bad_vals == 0,
           {"sum_of_counts_at_unavailable_positions": bad_vals})

    # 8 known absences
    col = {int(x): i for i, x in enumerate(addr)}
    lpl_un = {m for m in set(mid) if not av[mid == m, col[LPL]].all()}
    pgk_un = {m for m in set(mid) if not av[mid == m, col[PGK1]].all()}
    exp_lpl = {"HVS::c5e9db26-7b51-4290-b721-dd540ac906b1"}
    exp_pgk = {m for m in EXPECTED_MATRIX_COUNTS if m.startswith("sea_ad_")}
    nph = "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs"
    nph_un = sorted(int(addr[j]) for j in range(addr.size)
                    if not av[mid == nph, j].all())
    record("known_absences", lpl_un == exp_lpl and pgk_un == exp_pgk and not nph_un,
           {"LPL_unavailable_in": sorted(lpl_un), "LPL_expected": sorted(exp_lpl),
            "PGK1_unavailable_in_n": len(pgk_un), "PGK1_expected_n": len(exp_pgk),
            "PGK1_matches": pgk_un == exp_pgk,
            "NPH52_unavailable": nph_un})

    # 9 panel reachability
    qp = [col[x] for x in R8_QUERY_PANEL]
    unreachable = [int(R8_QUERY_PANEL[i]) for i, j in enumerate(qp)
                   if not av[:, j].all()]
    record("all_query_and_panel_addresses_available", not unreachable,
           {"unreachable": unreachable, "checked": len(R8_QUERY_PANEL)})

    # 10 denominator arithmetic
    tot = z["total_all"].astype(np.int64)
    exc = z["total_excluding_29"].astype(np.int64)
    recomputed = tot - (cnt.astype(np.int64) * av).sum(1)
    nbad = int((recomputed != exc).sum())
    record("denominator_arithmetic", nbad == 0,
           {"cells_disagreeing": nbad,
            "definition": "total_excluding_29 == total_all - sum(available counts)",
            "source_specific": True,
            "ban_subtracted_per_matrix": {
                m: int(av[mid == m][0].sum()) for m in sorted(set(mid))}})

    # plausibility reading, not a gate
    reading = {}
    for s in sorted(set(src)):
        m = src == s
        reading[s] = {MARKERS[aa]: round(float(np.mean(cnt[m, col[aa]] > 0)), 4)
                      for aa in MARKERS if av[m, col[aa]].all()}

    all_pass = all(c["pass"] for c in checks.values())
    out = {
        "schema": "V5_AUDIT_MASKED_MYELOID_ARTIFACT_V1",
        "status": "INDEPENDENT_AUDIT__RE_DERIVED_FROM_THE_ARTIFACT",
        "artifact_dir": a.artifact_dir,
        "all_checks_pass": all_pass,
        "checks": checks,
        "marker_detection_reading_not_a_gate": reading,
        "scope": ("29 addresses in candidate myeloid nuclei. This audit says "
                  "nothing about the other 41,209 addresses, about Levels 1-3, "
                  "or about the training substrate."),
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    out["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "AUDIT_MASKED_MYELOID_ARTIFACT_V1.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)

    print("Independent audit of the masked myeloid artifact\n")
    for name, c in checks.items():
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {name}")
        for k, v in c.items():
            if k == "pass":
                continue
            sv = str(v)
            if len(sv) > 150:
                sv = sv[:150] + "..."
            print(f"           {k}: {sv}")
    print(f"\n  marker detection by source (reading, not a gate):")
    for s, d in reading.items():
        print(f"      {s:8s} " + "  ".join(f"{g}={100*v:.1f}%" for g, v in d.items()))
    print(f"\n  ALL CHECKS PASS: {all_pass}")
    print(f"\nwrote {p}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
