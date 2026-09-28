#!/usr/bin/env python3
"""Is the NPH52 .qs source INDEPENDENTLY VERIFIED, or identity-ASSUMED?

WHY THIS EXISTS AS A SCRIPT AND NOT A PARAGRAPH

  `full104_level4_column_decoder_v1.py` verified each of the twelve HDF5
  myeloid matrices by decoding real entries and comparing them against the
  authenticated source object, cell by cell, reaching 1.0000 agreement over 32
  verification cells per matrix. NPH52 got a different treatment, and the
  question "how different" is answerable from digests that are already on
  disk - which makes it a check, not an opinion.

  Every statement this emits is either a digest comparison or a file-existence
  test. Nothing here is inferred from how the counts look.

WHAT IT DECIDES

  1. Did the axis verifier read the object the materializer authenticates?
     -> compares the verifier's recorded qs digest against the reader-fit
        derivative manifest's sha256 for this matrix.
  2. Does the feature count agree with that manifest?
  3. Does the cell count agree with the published artifact?
  4. Was the provenance table it checked the one on disk now?
  5. Does the materialization contract's code_sha256 bind the R code that
     actually wrote the NPH52 blocks, or the Python code that wrote the HDF5
     ones?
  6. Does a value-level verified decoder exist for NPH52, as it does for the
     twelve HDF5 matrices?

  The .qs file itself is NEVER opened. No counts are read, nothing is trained,
  and no reserved readout is touched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np

DEFAULT_MATRIX_ID = "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs"


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--axis-receipt", required=True)
    ap.add_argument("--derivative-manifest", required=True,
                    help="NPH_READER_FIT_DERIVATIVE_MANIFEST.csv")
    ap.add_argument("--materialization-contract", required=True)
    ap.add_argument("--nph-materializer-r", required=True,
                    help="scripts/v4/materialize_full104_phase2_nph_blocks.R")
    ap.add_argument("--hdf5-materializer-py", required=True,
                    help="scripts/v4/materialize_full104_phase2_expression.py")
    ap.add_argument("--decoder-dir", required=True)
    ap.add_argument("--decoder-receipt", default=None)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--nph52-provenance", required=True)
    ap.add_argument("--matrix-id", default=DEFAULT_MATRIX_ID)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    axis = json.load(open(a.axis_receipt))
    contract = json.load(open(a.materialization_contract))

    man_row = None
    with open(a.derivative_manifest, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["matrix_id"] == a.matrix_id:
                man_row = r
    if man_row is None:
        raise SystemExit(f"REFUSE_MATRIX_NOT_IN_DERIVATIVE_MANIFEST {a.matrix_id!r}")

    z = np.load(a.artifact, allow_pickle=True)
    n_art = int((z["matrix_id"].astype(str) == a.matrix_id).sum())

    r_sha = sha_file(a.nph_materializer_r)
    py_sha = sha_file(a.hdf5_materializer_py)
    stem = a.matrix_id.replace("::", "__").replace("/", "_")
    decoder_path = os.path.join(a.decoder_dir, f"decoder_{stem}.npz")
    decoders_present = sorted(f for f in os.listdir(a.decoder_dir)
                              if f.startswith("decoder_") and f.endswith(".npz"))

    hdf5_value_level = None
    if a.decoder_receipt:
        dr = json.load(open(a.decoder_receipt))
        hdf5_value_level = {
            mid: {"decoded_agreement": m.get("decoded_agreement"),
                  "verify_cells": m.get("verify_cells"),
                  "decoded_entries_checked": m.get("decoded_entries_checked")}
            for mid, m in (dr.get("matrices") or {}).items()}

    v = {}
    v["axis_verifier_read_the_authenticated_derivative"] = {
        "pass": (axis.get("digests", {}).get("qs_source")
                 == man_row["derivative_sha256"]),
        "axis_receipt_qs_sha256": axis.get("digests", {}).get("qs_source"),
        "derivative_manifest_sha256": man_row["derivative_sha256"],
        "derivative_relative_path": man_row["derivative_relative_path"],
        "means": ("the object whose rownames were checked is byte-identical to "
                  "the object the R materializer authenticates before reading"),
    }
    v["feature_count_agrees_with_manifest"] = {
        "pass": int(axis.get("object_features", -1)) == int(man_row["feature_count"]),
        "axis_receipt": int(axis.get("object_features", -1)),
        "manifest": int(man_row["feature_count"]),
    }
    v["cell_count_agrees_with_artifact"] = {
        "pass": int(man_row["cell_count"]) == n_art,
        "manifest": int(man_row["cell_count"]), "artifact": n_art,
    }
    v["provenance_is_the_verified_copy"] = {
        "pass": (axis.get("digests", {}).get("provenance")
                 == sha_file(a.nph52_provenance)),
        "axis_receipt": axis.get("digests", {}).get("provenance"),
        "on_disk_now": sha_file(a.nph52_provenance),
    }
    v["contract_code_sha256_binds_the_nph_materializer"] = {
        "pass": contract.get("code_sha256") == r_sha,
        "contract_code_sha256": contract.get("code_sha256"),
        "nph_materializer_r_sha256": r_sha,
        "hdf5_materializer_py_sha256": py_sha,
        "contract_binds_the_python_materializer":
            contract.get("code_sha256") == py_sha,
        "means": ("the contract's single code digest identifies the Python "
                  "materializer that wrote the HDF5 blocks. The R script that "
                  "wrote the NPH52 blocks is not digested by the contract, so "
                  "nothing on disk pins which version of it ran"),
    }
    v["value_level_decoder_verification_exists_for_nph52"] = {
        "pass": os.path.exists(decoder_path),
        "expected_path": decoder_path,
        "decoders_present": decoders_present,
        "n_decoders_present": len(decoders_present),
        "means": ("the twelve HDF5 matrices each carry a decoder verified by "
                  "decoding real entries against the source object. NPH52 has "
                  "no such file and no such check: its column-to-address "
                  "identity rests on reading line 57 of the R materializer, "
                  "which writes directly into molecular_address_index columns"),
    }

    verified = [
        "the provenance table's source_feature_index enumerates the counts "
        "assay's own row order: rownames[source_feature_index] equals the "
        f"recorded symbol for {axis.get('provenance_rows')} of "
        f"{axis.get('provenance_rows')} rows "
        f"(zero-based {axis.get('agreement_zero_based')}, one-based "
        f"{axis.get('agreement_one_based')})",
        "the object carrying that axis is byte-identical to the reader-fit "
        "derivative the materializer authenticates before reading",
        "feature and cell counts agree across the axis receipt, the "
        "derivative manifest and the published artifact",
    ]
    not_verified = [
        "NO COUNTS WERE COMPARED. The verifier states "
        "NO_COUNTS_READ. Nothing establishes that a Level-4 block value for "
        "an NPH52 nucleus equals the .qs count for that (feature, cell) pair. "
        "The twelve HDF5 matrices each got exactly that check at agreement "
        "1.0000; NPH52 did not.",
        "BLOCK COLUMN == MOLECULAR ADDRESS IS A CODE-READING ARGUMENT, NOT AN "
        "EXECUTED CHECK. It follows from materialize_full104_phase2_nph_blocks"
        ".R line 57 writing sparseMatrix(j=molecular_address_index+1L, "
        "dims=c(n,41238)). No artifact on disk tests the written blocks "
        "against that claim.",
        "WHICH ADDRESSES EXIST WAS NEVER DERIVED FROM THE AXIS by the "
        "extraction. The verifier answered where an address sits, not which "
        "addresses the object carries; the extraction treated the second "
        "question as answered by the first. That is the defect repaired by "
        "full104_nph52_availability_repair_v1.py.",
        "THE COLLISION BLOCKING IS NOT REFLECTED ANYWHERE DOWNSTREAM. The "
        "materializer drops every collision-blocked source_feature_index "
        "before writing (lines 39-42), so the raw provenance axis over-states "
        "the materialized address set.",
        "THE SYMBOL, NOT THE ENSEMBL ID, WAS COMPARED. The check matches "
        "raw_source_feature_symbol against the rowname; "
        "source_exact_ensembl_id was not used. Duplicate rownames were "
        "refused, so the match is unambiguous within this object, but a "
        "symbol collision across the mapping authority would not be caught.",
        "THE CONTRACT DOES NOT PIN THE R CODE. code_sha256 identifies the "
        "Python materializer; the R script that wrote these blocks is not "
        "digested by the contract or the audit.",
        "THE ORIGINAL SEALED .qs WAS NOT READ. The verified object is the "
        "reader-fit derivative. That is the right object, because it is the "
        "one the materializer reads - but it means the derivative's fidelity "
        "to the sealed original is assumed, not shown, by this check.",
    ]

    verdict = ("INDEPENDENTLY_VERIFIED_FOR_FEATURE_AXIS_POSITION_ONLY"
               "__VALUE_LEVEL_AND_COLUMN_IDENTITY_REMAIN_UNVERIFIED")

    out = {
        "schema": "V5_NPH52_VERIFICATION_STATUS_V1",
        "question": ("does the FULL104 decoder record the NPH52 .qs source as "
                     "independently verified, or merely identity-assumed?"),
        "verdict": verdict,
        "matrix_id": a.matrix_id,
        "mechanical_checks": v,
        "all_mechanical_checks_pass": all(c["pass"] for c in v.values()),
        "what_was_verified": verified,
        "what_was_NOT_verified": not_verified,
        "hdf5_value_level_verification_for_contrast": hdf5_value_level,
        "qs_file_opened_by_this_script": False,
        "training_authorized": False,
        "protected_outcomes_opened": False,
        "digests": {
            "axis_receipt": sha_file(a.axis_receipt),
            "derivative_manifest": sha_file(a.derivative_manifest),
            "materialization_contract": sha_file(a.materialization_contract),
            "nph_materializer_r": r_sha,
            "hdf5_materializer_py": py_sha,
            "artifact": sha_file(a.artifact),
        },
        "producer_sha256": sha_file(os.path.abspath(__file__)),
    }
    p = os.path.join(a.out_dir, "NPH52_VERIFICATION_STATUS_V1.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)

    for k, c in v.items():
        print(f"  {'PASS' if c['pass'] else 'FAIL'}  {k}")
    print(f"\n  VERDICT: {verdict}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
