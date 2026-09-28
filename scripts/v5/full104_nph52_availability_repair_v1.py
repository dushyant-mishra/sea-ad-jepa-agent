#!/usr/bin/env python3
"""NPH52 availability repair: derive the mask from the axis, never assume it.

THE DEFECT THIS REPAIRS

  `full104_myeloid_panel_extraction_v3_masked.py` emits `address_available`,
  a per-nucleus by per-address boolean whose whole purpose is to stop a
  structural absence from being read as an observed zero.

  For the twelve HDF5 matrices that mask is DERIVED: `load_addr_to_col` looks
  each target address up in that matrix's verified decoder and gives an
  unfound address column -1, which `process_operator` turns into
  `reachable == False`.

  For NPH52 the same function takes an early return:

      if matrix_id in IDENTITY_VERIFIED_MATRICES:
          return (np.asarray(targets, dtype=np.int64),
                  IDENTITY_VERIFIED_MATRICES[matrix_id], [])

  It returns the target addresses themselves as the columns and an EMPTY
  unreachable list, so `reachable` is all-True and every address is marked
  available for every NPH52 nucleus. The identity verification established
  that block column == molecular address WHERE AN ADDRESS EXISTS. It said
  nothing about WHICH addresses exist, and the early return treats the second
  question as answered by the first.

  Consequence in the published artifact: all 29 addresses are marked available
  for all 15,264 NPH52 nuclei, including two that NPH52's authenticated feature
  axis does not contain at all.

THE AUTHORITY USED INSTEAD

  `stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`
  filtered to the object's own `source_dataset_id`. That is the same table
  `nph52_feature_axis_verifier_v1.py` checked, row by row, against the object's
  `assay(obj,"counts")` rownames at agreement 1.0000, and the same table the
  R materializer indexes. This script REFUSES unless that verifier's receipt
  is present, verified, and carries a provenance digest equal to the digest of
  the provenance file handed to this script - a mask is only as trustworthy as
  the axis it is derived from, and an unbound axis is an assumption wearing a
  filename.

  An address absent from that axis was never a column the materializer could
  write, so it is UNMEASURED. It is not a biological zero, and this script
  does not convert it into one: the counts array is copied byte-for-byte and
  only the mask changes.

TWO AXES, AND WHY BOTH ARE COMPUTED

  `materialize_full104_phase2_nph_blocks.R` lines 39-42 remove every
  `source_feature_index` listed in the collision ledger and the supplemental
  unregistered-collision table BEFORE materializing, then refuses at line 43
  if the surviving map is non-injective. The RAW provenance axis is therefore
  an UPPER BOUND on what was physically written: a fully blocked address is in
  the raw axis and not in the blocks.

  This script computes both when the collision tables are supplied - the raw
  axis and the MATERIALIZED axis (raw minus blocked) - and REFUSES if they
  disagree on any of the artifact's addresses. Agreement is not assumed; if it
  ever fails, the mask that would be written is ambiguous and nothing is
  written. The size of the gap over the whole address space is recorded, since
  it bears on every consumer of the wider census even when it does not touch
  these addresses.

GOVERNANCE

  The six reserved readout addresses are never read. Structural membership in
  a feature axis is not a count and not a statistic, so the mask is repaired
  for them too - leaving a false availability claim standing on a held-out
  readout is the worst place to leave one, and a mask that says UNAVAILABLE
  makes every downstream consumer refuse, which is the fail-closed direction.
  The mask-versus-values consistency check, which DOES read counts, is run for
  non-reserved addresses only and recorded as UNCHECKED_BY_GOVERNANCE for the
  reserved ones. It is not recorded as passing.

  The original artifact is not modified. This is a successor view beside it.
  Nothing is trained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

N_ADDR = 41238

# Frozen. Never indexed into `counts` by this script.
RESERVED_READOUTS = (2810, 4748, 10846, 13734, 14980, 26659)

DEFAULT_SOURCE_DATASET_ID = "NPH52::MG_data_arranged_updatedId_final_batches.qs"
DEFAULT_MATRIX_ID = "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs"

ACCEPTED_AXIS_VERDICTS = (
    "FEATURE_AXIS_VERIFIED__ZERO_BASED__MATERIALIZER_INDEXING_CORRECT",
)


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def load_axis_receipt(path, source_dataset_id, provenance_sha):
    """The verifier's receipt, or a refusal. Binds the axis to its verification.

    A receipt that verified a different object, or a different copy of the
    provenance table, does not license this repair.
    """
    r = json.load(open(path))
    if r.get("schema") != "V5_NPH52_FEATURE_AXIS_VERIFIER_V1":
        raise SystemExit(f"REFUSE_AXIS_RECEIPT_SCHEMA {r.get('schema')!r}")
    if r.get("source_dataset_id") != source_dataset_id:
        raise SystemExit(
            f"REFUSE_AXIS_RECEIPT_WRONG_OBJECT {r.get('source_dataset_id')!r} "
            f"!= {source_dataset_id!r}")
    if r.get("verdict") not in ACCEPTED_AXIS_VERDICTS:
        raise SystemExit(f"REFUSE_AXIS_NOT_VERIFIED {r.get('verdict')!r}")
    if float(r.get("agreement_zero_based", 0.0)) < 1.0:
        raise SystemExit(
            f"REFUSE_AXIS_AGREEMENT_BELOW_1.0 {r.get('agreement_zero_based')}")
    got = (r.get("digests") or {}).get("provenance")
    if got != provenance_sha:
        raise SystemExit(
            "REFUSE_PROVENANCE_NOT_THE_VERIFIED_COPY: axis receipt verified "
            f"provenance sha256={got}, this run was handed {provenance_sha}")
    return r


def blocked_feature_indices(collision_ledger, unregistered, matrix_id):
    """The source_feature_index values the R materializer drops before writing.

    Mirrors materialize_full104_phase2_nph_blocks.R lines 39-42 exactly:
    the collision ledger rows for this matrix, plus the pipe-separated
    source_feature_indices of the supplemental unregistered-collision table.
    """
    import pandas as pd
    c = pd.read_csv(collision_ledger, low_memory=False,
                    usecols=["matrix_id", "source_feature_index"])
    blocked = {int(x) for x in c.loc[c.matrix_id == matrix_id,
                                     "source_feature_index"]}
    u = pd.read_csv(unregistered, low_memory=False)
    for s in u.loc[u.matrix_id == matrix_id, "source_feature_indices"]:
        blocked |= {int(x) for x in str(s).split("|") if str(x).strip()}
    return blocked


def authenticated_axis(provenance_csv, source_dataset_id, blocked=None):
    """-> (raw mask, materialized mask or None, stats dict).

    `raw` is every address the provenance table assigns to this object.
    `materialized` is that set minus the addresses whose every provenance row
    was dropped by the materializer's collision blocking, i.e. what the blocks
    can actually contain. `materialized` is None when the collision tables
    were not supplied, and the caller must then say so rather than imply the
    two are the same.
    """
    import pandas as pd
    df = pd.read_csv(provenance_csv, low_memory=False,
                     usecols=["molecular_address_index", "source_dataset_id",
                              "source_feature_index"])
    sub = df[df.source_dataset_id == source_dataset_id]
    if sub.empty:
        raise SystemExit(f"REFUSE_NO_PROVENANCE_ROWS for {source_dataset_id!r}")
    a = sub.molecular_address_index.astype(np.int64).to_numpy()
    out_of_range = int(((a < 0) | (a >= N_ADDR)).sum())
    if out_of_range:
        raise SystemExit(
            f"REFUSE_ADDRESS_OUT_OF_RANGE {out_of_range} rows outside "
            f"[0,{N_ADDR}); the provenance table is not this address space")
    raw = np.zeros(N_ADDR, dtype=bool)
    raw[a] = True
    stats = {"provenance_rows": int(len(sub)),
             "raw_distinct_addresses": int(raw.sum())}
    mat = None
    if blocked is not None:
        keep = sub[~sub.source_feature_index.astype(np.int64).isin(blocked)]
        ka = keep.molecular_address_index.astype(np.int64).to_numpy()
        mat = np.zeros(N_ADDR, dtype=bool)
        mat[ka] = True
        # The materializer refuses a non-injective surviving map (line 43); if
        # ours is non-injective we have not reproduced what it did.
        dup_sfi = int(keep.source_feature_index.duplicated().sum())
        dup_addr = int(keep.molecular_address_index.duplicated().sum())
        if dup_sfi or dup_addr:
            raise SystemExit(
                "REFUSE_BLOCKING_DID_NOT_REPRODUCE_INJECTIVE_MAP: surviving "
                f"rows carry {dup_sfi} duplicate source_feature_index and "
                f"{dup_addr} duplicate molecular_address_index; the R "
                "materializer would have stopped, so this reconstruction of "
                "its blocking is wrong")
        stats.update({
            "blocked_source_feature_indices": int(len(blocked)),
            "rows_after_blocking": int(len(keep)),
            "materialized_distinct_addresses": int(mat.sum()),
            "addresses_in_raw_axis_never_materialized":
                int((raw & ~mat).sum()),
        })
    return raw, mat, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True,
                    help="FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz (READ ONLY)")
    ap.add_argument("--extraction-receipt", required=True,
                    help="FULL104_MYELOID_R8_PANEL_EXTRACTION_V1.json (READ ONLY)")
    ap.add_argument("--nph52-provenance", required=True)
    ap.add_argument("--axis-receipt", required=True,
                    help="NPH52_FEATURE_AXIS_VERIFIER_V1.json")
    ap.add_argument("--source-dataset-id", default=DEFAULT_SOURCE_DATASET_ID)
    ap.add_argument("--matrix-id", default=DEFAULT_MATRIX_ID)
    ap.add_argument("--collision-ledger", default=None,
                    help="collision_ledger.csv.gz; with --unregistered-"
                         "collisions this reconstructs the MATERIALIZED axis "
                         "and requires it to agree with the raw axis on every "
                         "address in the artifact")
    ap.add_argument("--unregistered-collisions", default=None,
                    help="unregistered_collisions.csv")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    if bool(a.collision_ledger) != bool(a.unregistered_collisions):
        raise SystemExit("REFUSE_PARTIAL_COLLISION_TABLES: supply both or "
                         "neither; one alone reproduces neither axis")

    prov_sha = sha_file(a.nph52_provenance)
    axis_receipt = load_axis_receipt(a.axis_receipt, a.source_dataset_id, prov_sha)
    blocked = None
    if a.collision_ledger:
        blocked = blocked_feature_indices(
            a.collision_ledger, a.unregistered_collisions, a.matrix_id)
    axis, axis_mat, axis_stats = authenticated_axis(
        a.nph52_provenance, a.source_dataset_id, blocked)
    print(f"authenticated axis: {axis_stats['provenance_rows']:,} provenance "
          f"rows -> {axis_stats['raw_distinct_addresses']:,} distinct "
          f"addresses", flush=True)
    if axis_mat is not None:
        print(f"materialized axis:  {axis_stats['materialized_distinct_addresses']:,} "
              f"addresses after blocking "
              f"({axis_stats['blocked_source_feature_indices']:,} feature "
              f"indices blocked; "
              f"{axis_stats['addresses_in_raw_axis_never_materialized']:,} "
              f"addresses in the raw axis were never materialized)", flush=True)

    z = np.load(a.artifact, allow_pickle=True)
    keys = list(z.keys())
    for req in ("address_columns", "address_available", "counts", "matrix_id"):
        if req not in keys:
            raise SystemExit(f"REFUSE_ARTIFACT_MISSING_KEY {req}")
    cols = [int(c) for c in z["address_columns"]]
    avail_old = np.asarray(z["address_available"], dtype=bool)
    counts = z["counts"]
    matrix_id = z["matrix_id"].astype(str)
    n_cells = avail_old.shape[0]
    if counts.shape != avail_old.shape or counts.shape[1] != len(cols):
        raise SystemExit("REFUSE_SHAPE_MISMATCH counts/available/address_columns")

    rows = matrix_id == a.matrix_id
    n_target = int(rows.sum())
    if n_target == 0:
        raise SystemExit(f"REFUSE_NO_ROWS_FOR_MATRIX {a.matrix_id!r}")

    # ---- the two axes must agree on every address we are about to write
    axis_disagreement = []
    if axis_mat is not None:
        for addr in cols:
            if bool(axis[addr]) != bool(axis_mat[addr]):
                axis_disagreement.append(
                    f"address {addr}: raw provenance axis says "
                    f"{'PRESENT' if axis[addr] else 'ABSENT'} but the "
                    f"materialized axis (raw minus collision-blocked) says "
                    f"{'PRESENT' if axis_mat[addr] else 'ABSENT'}")
        if axis_disagreement:
            with open(os.path.join(a.out_dir, "REPAIR_REFUSED.json"), "w") as fh:
                json.dump({"axis_disagreement": axis_disagreement,
                           "axis_stats": axis_stats}, fh, indent=2)
            raise SystemExit(
                "REFUSED_AXES_DISAGREE_ON_A_TARGET_ADDRESS: the mask that "
                "would be written is ambiguous. " + "; ".join(axis_disagreement))

    # ---- the repair: availability is READ OFF the axis, per address
    avail_new = avail_old.copy()
    per_address = []
    flipped_addresses = []
    for j, addr in enumerate(cols):
        present = bool(axis[addr])
        before_n = int(avail_old[rows, j].sum())
        avail_new[rows, j] = present
        after_n = int(avail_new[rows, j].sum())
        per_address.append({
            "address": addr,
            "in_authenticated_axis": present,
            "reserved_readout": addr in RESERVED_READOUTS,
            "nph52_available_before": before_n,
            "nph52_available_after": after_n,
            "changed": before_n != after_n,
        })
        if before_n != after_n:
            flipped_addresses.append(addr)

    # ---- mask-versus-values consistency, non-reserved addresses only
    #
    # A nonzero count sitting at an address the source never measured means the
    # mask and the values disagree and neither can be trusted. This is checked
    # ONLY for non-reserved addresses: running it on a reserved readout would
    # require reading that readout's counts, which is forbidden. It is recorded
    # as unchecked, never as passing.
    consistency = []
    violations = []
    for addr in flipped_addresses:
        j = cols.index(addr)
        if addr in RESERVED_READOUTS:
            consistency.append({
                "address": addr,
                "check": "UNCHECKED_BY_GOVERNANCE",
                "why": ("verifying that the placeholder value is zero would "
                        "require reading a reserved readout column; the "
                        "structural argument is that the materializer writes "
                        "only columns present in its mapping, so no entry can "
                        "exist at an address absent from the axis, but that "
                        "argument was NOT confirmed against the data here"),
            })
            continue
        vals = counts[rows, j]
        nz = int((vals != 0).sum())
        consistency.append({"address": addr, "check": "COUNTS_ALL_ZERO",
                            "nonzero_cells": nz, "pass": nz == 0})
        if nz:
            violations.append(
                f"address {addr}: {nz} NPH52 nuclei carry a nonzero count at "
                f"an address absent from the authenticated feature axis")
    if violations:
        with open(os.path.join(a.out_dir, "REPAIR_REFUSED.json"), "w") as fh:
            json.dump({"violations": violations, "consistency": consistency},
                      fh, indent=2)
        raise SystemExit("REFUSED_MASK_AND_VALUES_DISAGREE: " + "; ".join(violations))

    changed_cells = int((avail_old != avail_new).sum())
    if changed_cells and not flipped_addresses:
        raise SystemExit("REFUSE_INTERNAL_INCONSISTENCY")

    # ---- write the successor view; every other array is copied verbatim
    payload = {k: z[k] for k in keys}
    payload["address_available"] = avail_new
    out_npz = os.path.join(a.out_dir, "FULL104_MYELOID_R8_PANEL_COUNTS_V2.npz")
    np.savez_compressed(out_npz, **payload)

    src_receipt = json.load(open(a.extraction_receipt))
    old_status = (src_receipt.get("decoder_status_by_matrix") or {}).get(a.matrix_id)
    measured = sum(1 for r in per_address if r["in_authenticated_axis"])
    absent = sorted(r["address"] for r in per_address
                    if not r["in_authenticated_axis"])

    receipt = {
        "schema": "V5_FULL104_NPH52_AVAILABILITY_REPAIR_V1",
        "status": "SUCCESSOR_VIEW__NPH52_AVAILABILITY_DERIVED_FROM_AUTHENTICATED_AXIS",
        "repairs": ("address_available for NPH52 nuclei, which the extraction "
                    "assumed rather than derived"),
        "defect_location": {
            "file": "scripts/v5/full104_myeloid_panel_extraction_v3_masked.py",
            "function": "load_addr_to_col  (defined at line 246)",
            "lines": "253-255, the early return for IDENTITY_VERIFIED_MATRICES",
            "code": ("if matrix_id in IDENTITY_VERIFIED_MATRICES:\n"
                     "    return (np.asarray(targets, dtype=np.int64),\n"
                     "            IDENTITY_VERIFIED_MATRICES[matrix_id], [])"),
            "what_it_does": ("returns the target addresses themselves as the "
                             "block columns and an EMPTY unreachable list. The "
                             "decoder branch below it builds `cols` with "
                             "addr2col.get(t, -1) and collects `unreachable` "
                             "from the -1s; the identity branch collects "
                             "nothing, because it never asks whether the "
                             "address exists."),
            "how_it_propagates": (
                "process_operator line 276 computes `reachable = probe_cols "
                ">= 0`. With no -1 there is nothing to be unreachable, so "
                "`reachable` is all-True, is carried into every record as "
                "field 13, and is stacked into `address_available` in main() "
                "at line 483. main()'s own guard at line 488, `if "
                "available.size and counts[~available].any()`, selects zero "
                "elements for NPH52 and so cannot fail there - a check that "
                "was vacuous for exactly the matrix that needed it."),
        },
        "proposed_minimal_change_NOT_APPLIED": {
            "where": "load_addr_to_col, replacing the 253-255 early return",
            "shape": (
                "give the identity branch the same availability derivation the "
                "decoder branch already has, sourced from the authenticated "
                "feature axis instead of a decoder file:\n"
                "\n"
                "    if matrix_id in IDENTITY_VERIFIED_MATRICES:\n"
                "        axis = load_identity_axis(axis_dir, matrix_id)   # NEW\n"
                "        cols = np.asarray([int(t) if axis[int(t)] else -1\n"
                "                           for t in targets], dtype=np.int64)\n"
                "        unreachable = [int(t) for t, c in zip(targets, cols)\n"
                "                       if c < 0]\n"
                "        broken = sorted(set(unreachable) & REQUIRED_ADDRS)\n"
                "        if broken:\n"
                "            return None, f'R8_PANEL_ADDRESSES_UNREACHABLE:"
                "{broken}', unreachable\n"
                "        status = IDENTITY_VERIFIED_MATRICES[matrix_id] + (\n"
                "            '' if not unreachable else "
                "'__NONPANEL_ADDRESSES_ABSENT')\n"
                "        return cols, status, unreachable\n"
                "\n"
                "`load_identity_axis` reads the stage81a2r provenance rows for "
                "that object, subtracts the collision-blocked "
                "source_feature_index values exactly as the R materializer "
                "does, and returns a boolean over the 41,238 addresses. It "
                "must REFUSE when the axis is unavailable rather than fall "
                "back to all-True, since the fallback is the bug."),
            "why_this_shape": (
                "after the change both branches produce a -1 for an address "
                "the source does not carry, so the SAME downstream code marks "
                "it unavailable and the SAME REQUIRED_ADDRS guard refuses when "
                "an R8 panel address is missing. No new mechanism is "
                "introduced and no other function changes."),
            "test_that_must_accompany_it": (
                "a matrix whose axis omits one target address must come back "
                "with that address unavailable and, if it is a query or panel "
                "address, must refuse the matrix outright. Without that test "
                "the branch is unexercised in exactly the direction that "
                "failed here."),
            "status": "PROPOSED_ONLY__NOT_APPLIED__EXTRACTION_SCRIPT_UNCHANGED",
        },
        "source_artifact": {
            "path": os.path.abspath(a.artifact),
            "sha256": sha_file(a.artifact),
            "modified_in_place": False,
        },
        "source_extraction_receipt": {
            "path": os.path.abspath(a.extraction_receipt),
            "sha256": sha_file(a.extraction_receipt),
            "nph52_decoder_status_as_published": old_status,
        },
        "availability_authority": {
            "provenance": os.path.abspath(a.nph52_provenance),
            "provenance_sha256": prov_sha,
            "source_dataset_id": a.source_dataset_id,
            **axis_stats,
            "axis_receipt": os.path.abspath(a.axis_receipt),
            "axis_receipt_sha256": sha_file(a.axis_receipt),
            "axis_verdict": axis_receipt["verdict"],
            "axis_agreement_zero_based": axis_receipt["agreement_zero_based"],
            "collision_ledger": (os.path.abspath(a.collision_ledger)
                                 if a.collision_ledger else None),
            "collision_ledger_sha256": (sha_file(a.collision_ledger)
                                        if a.collision_ledger else None),
            "unregistered_collisions": (os.path.abspath(a.unregistered_collisions)
                                        if a.unregistered_collisions else None),
            "unregistered_collisions_sha256": (
                sha_file(a.unregistered_collisions)
                if a.unregistered_collisions else None),
            "materialized_axis_reconstructed": axis_mat is not None,
            "collision_table_identity_caveat": (
                "materialize_full104_phase2_nph_blocks.R names its inputs "
                "stage81a3r_expression_materialization_collision_ledger."
                "csv.gz and stage81a3r_scalar_mapping_unregistered_"
                "collisions.csv. No file with either name exists on this "
                "machine; the tables used here carry different filenames and "
                "were matched by schema and content. The corroboration is "
                "that applying them reproduces exactly the injective "
                "surviving map the materializer's line-43 guard requires, "
                "which a wrong table would be unlikely to do. That is strong "
                "corroboration and it is NOT a digest match."
                if axis_mat is not None else None),
            "raw_and_materialized_axes_agree_on_every_artifact_address":
                (axis_mat is not None and not axis_disagreement),
        },
        "target_matrix_id": a.matrix_id,
        "nuclei_total": int(n_cells),
        "nuclei_in_target_matrix": n_target,
        "addresses_checked": len(cols),
        "addresses_in_authenticated_axis": measured,
        "addresses_absent_from_authenticated_axis": absent,
        "ban_addresses_measured_by_this_matrix": measured,
        "ban_addresses_total": len(cols),
        "per_address": per_address,
        "mask_elements_changed": changed_cells,
        "mask_elements_changed_expected": n_target * len(absent),
        "mask_value_consistency": consistency,
        "counts_unchanged": True,
        "counts_unchanged_why": (
            "structural absence is not a biological zero. The placeholder "
            "value is left exactly as published; only the mask that declares "
            "it a placeholder is repaired."),
        "total_excluding_29_carried_verbatim": True,
        "total_excluding_29_not_recomputed_why": (
            "recomputing the reference would require summing every ban-set "
            "column including the six reserved readouts. The published column "
            "is copied unchanged. Under the materializer's construction an "
            "address absent from the mapping contributes no entry, so the "
            "arithmetic is unaffected - but that is a structural argument, "
            "not a measurement made here."),
        "raw_vs_materialized_axis": (
            "materialize_full104_phase2_nph_blocks.R removes every "
            "source_feature_index named in the collision ledger and the "
            "supplemental unregistered-collision table (lines 39-42) before "
            "materializing, so the raw provenance axis is an UPPER BOUND on "
            "the physically materialized address set. Both axes were "
            "reconstructed here and agree on every address in this artifact, "
            "so this repair is exact for these addresses. They do NOT agree "
            "over the whole address space: see "
            "addresses_in_raw_axis_never_materialized, which is a defect in "
            "any consumer that takes the raw axis as availability - the "
            "candidate-pool census does exactly that."
            if axis_mat is not None else
            "the collision tables were not supplied, so the materialized axis "
            "was NOT reconstructed and the raw provenance axis used here is "
            "an unquantified upper bound"),
        "reserved_readouts": list(RESERVED_READOUTS),
        "reserved_readout_handling": (
            "structural membership in a feature axis is not a count and not a "
            "statistic, so the mask is repaired for reserved addresses too. "
            "No reserved readout column was indexed into `counts`; the "
            "mask-versus-values check is recorded as UNCHECKED_BY_GOVERNANCE "
            "for them and is NOT recorded as passing."),
        "training_authorized": False,
        "protected_outcomes_opened": False,
        "output_npz": os.path.abspath(out_npz),
        "output_npz_sha256": sha_file(out_npz),
        "producer_sha256": sha_file(os.path.abspath(__file__)),
    }
    p = os.path.join(a.out_dir, "FULL104_NPH52_AVAILABILITY_REPAIR_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"  target matrix nuclei         {n_target:,}")
    print(f"  addresses in axis            {measured} of {len(cols)}")
    print(f"  addresses absent from axis   {absent}")
    print(f"  mask elements changed        {changed_cells:,} "
          f"(expected {n_target * len(absent):,})")
    for r in per_address:
        if r["changed"]:
            print(f"      address {r['address']}: available "
                  f"{r['nph52_available_before']:,} -> "
                  f"{r['nph52_available_after']:,}"
                  + ("   [RESERVED READOUT]" if r["reserved_readout"] else ""))
    print(f"\nwrote {out_npz}")
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
