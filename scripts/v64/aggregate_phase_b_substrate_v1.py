#!/usr/bin/env python3
"""Reconcile the sharded Phase-B substrate, and revalidate the pairing permutation.

S63. The permutation that pairs RNA rows to ATAC rows is the single most consequential
input to this build -- 1,500,790 of 1,501,089 rows are displaced, so a wrong permutation
would match unrelated nuclei while leaving shapes, donor counts and nearly every
downstream check intact. The shard receipts bound it only as the prose string
"name-derived, not positional", which is far too weak for an input that can invalidate
everything silently.

This aggregator therefore refuses to accept the substrate unless the permutation passes
six checks, five of them required by the audit and one added here:

  P1  sha256 equals the prequalified value
  P2  length equals the nucleus count
  P3  every entry lies in range
  P4  entries are unique, i.e. it is a bijection
  P5  the inverse round-trips in both directions
  P6  ADDED: the permutation is RE-DERIVED independently from the two obs name
      namespaces and must equal the file element for element

P6 is the one that matters most. A hash proves the file has not changed; it cannot prove
the file was ever right. Re-deriving from the names proves correctness rather than
stability, and the two together prove the build used a correct and unaltered input.

If the permutation fails, the substrate is invalid no matter how cleanly everything
downstream reconciles, and this script stops rather than reporting a tidy aggregate.

TRAINING=OFF. STAGE 4=NOT AUTHORISED. No RNA x ATAC quantity is computed.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import h5py
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

OUT = "D:/jepa_v5_outputs_20260925/v64_phase_b"
PERM = "D:/jepa_v5_outputs_20260925/atac_to_rna_row.npy"
RNA = "D:/jepa_v5_outputs_20260925/nihcard/final_rna_data.h5ad"
ATAC = "D:/jepa_v5_outputs_20260925/nihcard/final_atac_data.h5ad"
DIR = "results/v64/phase_b_design"
# S64, a recurrence of S49. The digest reported when the permutation was built -- and
# which the audit then quoted back as a requirement -- covers the ARRAY BYTES, not the
# .npy file, which prepends a 128-byte header. Validating the file digest against an
# array digest made an intact input look corrupt. Both are recorded here, each named for
# exactly what it covers, and both are checked. The failure mode is the dangerous one: it
# makes a correct artifact look substituted, which trains a reviewer to shrug at digest
# mismatches.
EXPECT_PERM_CONTENT_SHA = "c28335d72627d195c0b997a659e3d320139a0a038f746e354ca6de4567b9e120"
EXPECT_PERM_FILE_SHA = "2396c3e9ccef2a4354824a80815d6acb8819f662f6c641d4df72d85bad498828"
N_NUCLEI = 1501089


class Stop(Exception):
    pass


def names(p):
    with h5py.File(p, "r") as f:
        return np.array([x.decode() if isinstance(x, bytes) else str(x)
                         for x in f["obs"]["_index"][:]])


def validate_permutation():
    if not os.path.exists(PERM):
        raise Stop("the pairing permutation file is absent")
    raw = open(PERM, "rb").read()
    file_sha = hashlib.sha256(raw).hexdigest()
    perm = np.load(PERM)
    content_sha = hashlib.sha256(perm.tobytes()).hexdigest()
    checks = {}
    checks["P1a_array_content_sha256_matches_prequalified"] = (
        content_sha == EXPECT_PERM_CONTENT_SHA)
    checks["P1b_npy_file_sha256_matches"] = (file_sha == EXPECT_PERM_FILE_SHA)
    checks["P2_length_equals_nucleus_count"] = (len(perm) == N_NUCLEI)
    checks["P3_all_entries_in_range"] = bool(
        perm.min() >= 0 and perm.max() < N_NUCLEI) if len(perm) else False
    checks["P4_entries_unique_bijection"] = (len(np.unique(perm)) == len(perm))
    inv = np.empty_like(perm)
    inv[perm] = np.arange(len(perm))
    checks["P5_inverse_round_trips_both_ways"] = bool(
        np.array_equal(inv[perm], np.arange(len(perm)))
        and np.array_equal(perm[inv], np.arange(len(perm))))

    # P6: re-derive from the obs namespaces rather than trusting the stored array
    rn, an = names(RNA), names(ATAC)
    an_s = np.array([a[:a.rfind("_")] if a.rfind("_") > 0 else a for a in an])
    pos = {n: i for i, n in enumerate(rn)}
    if set(an_s) != set(rn):
        raise Stop("the ATAC stripped-name namespace is not the RNA namespace")
    rederived = np.array([pos[n] for n in an_s], dtype=perm.dtype)
    checks["P6_rederived_from_obs_names_matches_file"] = bool(
        np.array_equal(rederived, perm))

    displaced = int((perm != np.arange(len(perm))).sum())
    out = dict(path=PERM,
               array_content_sha256=content_sha,
               expected_array_content_sha256=EXPECT_PERM_CONTENT_SHA,
               npy_file_sha256=file_sha,
               expected_npy_file_sha256=EXPECT_PERM_FILE_SHA,
               digest_semantics={
                 "array_content_sha256": "sha256 of perm.tobytes() -- the 12,008,712 "
                     "bytes of int64 values; this is the digest reported when the "
                     "permutation was built and quoted by the audit",
                 "npy_file_sha256": "sha256 of the 12,008,840-byte .npy file, which "
                     "prepends a 128-byte header; this is what sha256sum reports"},
               length=int(len(perm)), rows_displaced=displaced,
               fraction_displaced=round(displaced / len(perm), 8),
               checks=checks, all_passed=all(checks.values()),
               why_P6_matters="a hash proves the file did not change; it cannot prove it "
                              "was ever correct. Re-deriving from the obs namespaces "
                              "proves correctness, and the two together prove the build "
                              "used a correct and unaltered input.")
    if not out["all_passed"]:
        raise Stop(f"pairing permutation failed: "
                   f"{[k for k, v in checks.items() if not v]}. The substrate is invalid "
                   f"regardless of how cleanly it reconciles downstream.")
    return out


def main() -> int:
    perm_report = validate_permutation()
    print("PERMUTATION REVALIDATION")
    for k, v in perm_report["checks"].items():
        print(f"  {k:<44} {v}")
    print(f"  rows displaced {perm_report['rows_displaced']:,} of "
          f"{perm_report['length']:,} ({perm_report['fraction_displaced']:.6%})")

    recs = [json.load(open(p)) for p in
            sorted(glob.glob(os.path.join(OUT, "PHASE_B_SUBSTRATE_RECEIPT_s*.json")))]
    if len(recs) != 8:
        raise Stop(f"expected 8 shard receipts, found {len(recs)}")
    bad = [r["shard"] for r in recs if r["status"] != "OK"]
    if bad:
        raise Stop(f"shards reporting non-OK status: {bad}")

    # inputs must agree across shards
    keys = ("producer_sha256", "substrate_contract_sha256",
            "statistical_contract_sha256", "enum_intervals_sha256", "e2_sha256",
            "peaks_sha256", "genes", "intervals", "qualifying_donors_all")
    agree = {k: {r[k] for r in recs} for k in keys}
    if any(len(v) != 1 for v in agree.values()):
        raise Stop(f"shard inputs disagree: "
                   f"{[k for k, v in agree.items() if len(v) != 1]}")

    donors = sum(r["reconciliation"]["donors_completed"] for r in recs)
    assigned = sum(r["reconciliation"]["donors_assigned"] for r in recs)
    mcs = sum(r["reconciliation"]["shard_metacells"] for r in recs)
    total_declared = recs[0]["reconciliation"]["total_metacells_all_donors"]

    # metacell ids must be globally disjoint across shards
    seen, overlap = set(), 0
    t3n = t4n = 0
    dmeta = []
    for p in sorted(glob.glob(os.path.join(OUT, "PHASE_B_SUBSTRATE_s*.npz"))):
        d = np.load(p, allow_pickle=True)
        ids = set(np.unique(d["t2_metacell"]).tolist())
        overlap += len(seen & ids)
        seen |= ids
        t3n += len(d["t3_value"])
        t4n += len(d["t4_value"])
    for r in recs:
        dmeta.extend(r["donor_meta"])
    if overlap:
        raise Stop(f"metacell ids collide across shards on {overlap} ids")
    nuc = sum(x["n_microglia"] for x in dmeta)

    agg = dict(
        schema="V64_PHASE_B_SUBSTRATE_AGGREGATE_V1", date="2026-09-30",
        closes="S63",
        PAIRING_PERMUTATION=perm_report,
        shards=len(recs), all_shards_OK=True,
        donors_assigned=assigned, donors_completed=donors,
        no_silent_skipped_work=(assigned == donors),
        qualifying_donors_declared=recs[0]["qualifying_donors_all"],
        donors_reconcile=(donors == recs[0]["qualifying_donors_all"]),
        metacells_total=mcs,
        metacells_declared_from_full_donor_list=total_declared,
        metacells_reconcile=(mcs == total_declared),
        metacell_ids_globally_disjoint=(overlap == 0),
        distinct_metacell_ids=len(seen),
        microglia_covered=nuc,
        genes=recs[0]["genes"], intervals=recs[0]["intervals"],
        t3_nnz=t3n, t4_nnz=t4n,
        inputs_agreed_across_shards={k: sorted(v)[0] for k, v in agree.items()},
        shard_output_sha256={f"s{r['shard']:02d}": r["output_sha256"] for r in recs},
        aggregate_binding=hashlib.sha256(
            "".join(r["output_sha256"] for r in sorted(recs, key=lambda x: x["shard"]))
            .encode()).hexdigest(),
        frozen_constants=recs[0]["frozen_constants"],
        modality_firewall="no RNA x ATAC quantity exists in any shard output",
        governance=recs[0]["governance"])
    gates = {
        "permutation_valid": perm_report["all_passed"],
        "all_shards_OK": True,
        "no_silent_skipped_work": agg["no_silent_skipped_work"],
        "donors_reconcile": agg["donors_reconcile"],
        "metacells_reconcile": agg["metacells_reconcile"],
        "metacell_ids_globally_disjoint": agg["metacell_ids_globally_disjoint"],
        "inputs_agreed_across_shards": True,
    }
    agg["gates"] = gates
    agg["failed_gates"] = [k for k, v in gates.items() if not v]
    agg["status"] = "PASS" if not agg["failed_gates"] else "FAIL"
    p = os.path.join(DIR, "V64_PHASE_B_SUBSTRATE_AGGREGATE_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(agg, fh, indent=2)

    print()
    print(f"shards {agg['shards']} all OK | donors {donors}/{assigned} "
          f"(declared {agg['qualifying_donors_declared']})")
    print(f"metacells {mcs:,} vs declared {total_declared:,} "
          f"reconcile={agg['metacells_reconcile']} disjoint={agg['metacell_ids_globally_disjoint']}")
    print(f"microglia covered {nuc:,} | genes {agg['genes']:,} | "
          f"intervals {agg['intervals']:,}")
    print(f"T3 nnz {t3n:,} | T4 nnz {t4n:,}")
    print(f"aggregate binding {agg['aggregate_binding']}")
    print(f"\nSTATUS {agg['status']}   receipt sha256 {B.sha_file(p)}")
    return 0 if agg["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
