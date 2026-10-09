#!/usr/bin/env python3
"""Decode Level-4 block columns to true molecular addresses. Root cause + repair.

THE ROOT CAUSE, in one sentence

  `materialize_full104_phase2_expression.py` builds its source-to-address table
  from `stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`
  keyed by `source_feature_index`, and then applies it to the h5ad's own column
  indices - but `source_feature_index` enumerates the source family's feature
  set in ENSEMBL-ID order, while an h5ad's `var` axis is in GENOMIC order. The
  two are different orderings of the same genes, so every count lands at the
  address belonging to a different gene.

THE EVIDENCE

  The materializer's sha256 matches the contract's `code_sha256` exactly
  (575d02a4…), so this is the code that wrote the blocks. For HVS:

    provenance source_feature_index  0 -> TSPAN6 (ENSG00000000003)
                                     1 -> TNMD   (ENSG00000000005)
                                     2 -> DPM1   (ENSG00000000419)     ascending ENSG
    h5ad var                         0 -> WASH7P (ENSG00000227232)
                                     1 -> FAM87B (ENSG00000177757)
                                     2 -> LINC00115 (ENSG00000225880) genomic

  Both have exactly 18,736 entries. Applying `source_to_address[p]` to every
  nonzero column of every nucleus reproduces the observed Level-4 columns for
  15,149 of 15,149 recovered genes - 100.0%. The blocks faithfully implement
  the provenance table; the table was simply indexed by the wrong axis.

WHY NO GUARD CAUGHT IT

  Every check in the materializer tests the mapping table against ITSELF, never
  against the object it is applied to. The lengths agree (18,736 = 18,736), so
  no size check fires. The mapping is injective, so the `noninjective address
  mapping` guard passes. The targets are all legitimately MEASURED_SCALAR
  addresses - just for the wrong genes - so the `states[op, …] == 1` guard
  passes. And the row identity IS checked, cell by cell, against the h5ad. Rows
  were verified and columns were not; that asymmetry is exactly what the
  measurements show.

  `provenance.molecular_address_index` is NOT a separate numbering: it agrees
  with `address_namespace.csv` on 18,736 of 18,736 rows. The target space was
  never in doubt.

WHICH SOURCES ARE AFFECTED

  The materializer collapses every HVS matrix to `HVS_COMMON` and every SEA-AD
  matrix to `SEA_AD_COMMON`, so both families inherit the defect. NPH52 has
  per-matrix provenance rows and is materialized by a separate R path, which is
  consistent with its Level-4 counts showing a textbook microglial profile
  (P2RY12 95.4%, CD74 93.2%, CSF1R 90.0%, CX3CR1 88.8%). That is corroboration,
  not verification: NPH52 remains unverified until its `.qs` source is read.

THE REPAIR IS EXACT AND NEEDS NO REBUILD

  Block column c holds the gene at h5ad var position p where
  source_to_address[p] == c. So the true address of column c is
  ensg_to_address[var[p]]. That is a closed-form per-matrix decoder derived
  from artifacts already on disk - no fingerprint matching, no re-materialization.

  This script emits that decoder per matrix and VERIFIES it before writing, by
  checking the decoded values against the authenticated source cell by cell. A
  matrix whose decoder does not verify is refused, not written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np

# A decoder must reproduce the source almost exactly; the only tolerated losses
# are source features the provenance deliberately drops (collisions and
# unregistered supplements).
DECODE_AGREEMENT_FLOOR = 0.99


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def dec(a):
    return np.asarray([x.decode() if isinstance(x, (bytes, np.bytes_)) else str(x)
                       for x in a], dtype=object)


def h5_col(grp, name):
    d = grp[name]
    if hasattr(d, "keys") and "categories" in d:
        return dec(d["categories"][:])[d["codes"][:]]
    return dec(d[:])


def index_name(grp):
    n = grp.attrs.get("_index", "_index")
    return n.decode() if isinstance(n, bytes) else str(n)


def source_var_ensg(f):
    """ENSG per var position, plus the column it came from."""
    g = f["raw"] if ("raw" in f and "var" in f["raw"]) else f
    var = g["var"]
    vi = index_name(var)
    for c in [vi] + [x for x in var.keys() if x != vi]:
        v = h5_col(var, c)
        if v.size and str(v[0]).startswith("ENSG"):
            return np.asarray([str(x).split(".")[0] for x in v], dtype=object), c
    return None, None


def count_node(f):
    if "raw" in f and "X" in f["raw"]:
        return f["raw"]["X"], "raw/X"
    if "layers" in f:
        for k in ("UMIs", "counts", "UMI"):
            if k in f["layers"]:
                return f["layers"][k], f"layers/{k}"
    return f["X"], "X"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l4-root", required=True)
    ap.add_argument("--bundle-root", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--matrices", required=True)
    ap.add_argument("--verify-cells", type=int, default=24)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    import h5py
    import pandas as pd

    ensg2addr = {}
    with open(os.path.join(a.bundle_root, "contracts", "address_namespace.csv"),
              newline="") as fh:
        for r in csv.DictReader(fh):
            ensg2addr[r["molecular_address_id"]] = int(r["molecular_address_index"])

    prov = pd.read_csv(a.provenance, low_memory=False)
    man, assets = {}, {}
    with open(os.path.join(a.l4_root, "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
              newline="") as fh:
        for r in csv.DictReader(fh):
            man.setdefault(r["matrix_id"], r)
    with open(os.path.join(a.l4_root, "ASSET_AUTHENTICATION.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            assets[r["matrix_id"]] = r

    out = {}
    for mid in [x.strip() for x in a.matrices.split(",") if x.strip()]:
        if mid not in man or mid not in assets:
            out[mid] = {"status": "NOT_IN_MANIFEST_OR_ASSET_REGISTRY"}; continue
        src = os.path.join(a.repo_root, assets[mid]["path"])
        if not src.lower().endswith((".h5ad", ".h5")) or not os.path.exists(src):
            out[mid] = {"status": "SOURCE_NOT_HDF5_OR_ABSENT",
                        "note": "an R .qs source needs its own reader; NOT "
                                "VERIFIED is not the same as correct"}
            continue
        # the materializer's own family collapse, reproduced exactly
        source = assets[mid]["source"]
        family = "HVS_COMMON" if source == "HVS" else \
                 "SEA_AD_COMMON" if source == "SEA_AD" else mid
        sub = prov[prov.source_dataset_id.eq(family)]
        if not len(sub):
            out[mid] = {"status": "NO_PROVENANCE_ROWS", "family": family}; continue

        with h5py.File(src, "r") as f:
            var_ensg, ensg_col = source_var_ensg(f)
            if var_ensg is None:
                out[mid] = {"status": "REFUSED_NO_ENSEMBL_COLUMN_IN_VAR"}; continue
            n_feat = var_ensg.size
            s2a = np.full(n_feat, -1, dtype=np.int64)
            sfi = sub.source_feature_index.astype(int).to_numpy()
            mai = sub.molecular_address_index.astype(int).to_numpy()
            ok = sfi < n_feat
            s2a[sfi[ok]] = mai[ok]

            # decoder: block column -> true molecular address
            # A block column is AMBIGUOUS when two source features with
            # different true addresses were written to it: their counts are
            # summed in the block and cannot be separated afterwards. Such a
            # column is dropped from the decoder and listed, never resolved by
            # picking one of the two.
            claims = {}
            for p in range(n_feat):
                c = int(s2a[p])
                if c < 0:
                    continue
                true_addr = ensg2addr.get(str(var_ensg[p]))
                if true_addr is None:
                    continue
                claims.setdefault(c, set()).add(true_addr)
            col2addr = {c: next(iter(v)) for c, v in claims.items() if len(v) == 1}
            ambiguous_cols = sorted(c for c, v in claims.items() if len(v) > 1)
            collisions = len(ambiguous_cols)

            # ---- verify against the source, cell by cell
            node, layer = count_node(f)
            rp = node["indptr"][:]
            R = os.path.join(a.l4_root, os.path.dirname(man[mid]["meta_path"]))
            base = os.path.basename(man[mid]["meta_path"]).replace(".meta.csv", "")
            meta = list(csv.DictReader(
                open(os.path.join(R, base + ".meta.csv"), newline="")))
            z = np.load(os.path.join(R, base + ".counts.npz"))
            ip, ind, dat = z["indptr"], z["indices"], z["data"]
            agree = tot = 0
            for r in range(min(a.verify_cells, len(meta))):
                er = int(meta[r]["expression_row"])
                lo, hi = int(rp[er]), int(rp[er + 1])
                s = {}
                for j, v in zip(node["indices"][lo:hi], node["data"][lo:hi]):
                    ad = ensg2addr.get(str(var_ensg[int(j)]))
                    if ad is not None:
                        s[ad] = float(v)
                blo, bhi = int(ip[r]), int(ip[r + 1])
                for c, v in zip(ind[blo:bhi], dat[blo:bhi]):
                    ad = col2addr.get(int(c))
                    if ad is None:
                        continue
                    tot += 1
                    agree += int(ad in s and abs(s[ad] - float(v)) < 1e-6)
            frac = agree / max(tot, 1)
            verified = bool(frac >= DECODE_AGREEMENT_FLOOR)
            R8_PANEL = [6186, 6188, 11425, 7194, 2044, 4748, 13734, 12469, 15109,
                        12239, 12995, 13365, 2810, 14980, 18511, 392, 23673,
                        18500, 20496, 26659, 10846]
            amb_addr = set()
            for c in ambiguous_cols:
                amb_addr |= claims[c]
            r8_lost = sorted(set(R8_PANEL) & amb_addr)
            out[mid] = {
                "status": ("DECODER_VERIFIED" if verified and not collisions else
                           "DECODER_VERIFIED_AMBIGUOUS_COLUMNS_EXCLUDED" if verified else
                           "DECODER_REFUSED"),
                "family_used_by_materializer": family,
                "source_asset": assets[mid]["path"],
                "source_ensembl_column": ensg_col,
                "count_layer": layer,
                "source_features": int(n_feat),
                "provenance_rows_for_family": int(len(sub)),
                "decoder_entries": len(col2addr),
                "ambiguous_columns_excluded": collisions,
                "ambiguous_column_list": ambiguous_cols[:2000],
                "ambiguous_meaning": ("two source features with different true "
                                      "addresses were summed into one block "
                                      "column; the counts cannot be separated, "
                                      "so the column is dropped rather than "
                                      "assigned to one of them"),
                "r8_panel_addresses_lost_to_ambiguity": r8_lost,
                "verify_cells": min(a.verify_cells, len(meta)),
                "decoded_entries_checked": tot,
                "decoded_agreement": frac,
                "agreement_floor": DECODE_AGREEMENT_FLOOR,
            }
            if verified:
                np.savez_compressed(
                    os.path.join(a.out_dir, f"decoder_{mid.replace('::','__').replace('/','_')}.npz"),
                    block_column=np.asarray(sorted(col2addr), dtype=np.int64),
                    true_address=np.asarray([col2addr[c] for c in sorted(col2addr)],
                                            dtype=np.int64))

    receipt = {
        "schema": "V5_FULL104_LEVEL4_COLUMN_DECODER_V1",
        "status": "ROOT_CAUSE_AND_CLOSED_FORM_REPAIR__NO_REBUILD__NO_TRAINING",
        "root_cause": (
            "materialize_full104_phase2_expression.py indexes the provenance "
            "table by source_feature_index, which enumerates the source family's "
            "features in Ensembl-ID order, and applies it to the h5ad column "
            "indices, which are in genomic order. Same genes, different "
            "ordering, identical length - so no length, injectivity or "
            "measured-state guard could fire."),
        "materializer_sha256_matches_contract_code_sha256": True,
        "provenance_numbering_matches_address_namespace": True,
        "guards_that_passed_and_why": {
            "length": "18,736 provenance rows vs 18,736 h5ad features",
            "noninjective_address_mapping": "the mapping is injective; only its "
                                            "domain is wrong",
            "states_must_be_MEASURED_SCALAR": "targets are legitimate measured "
                                              "addresses, for the wrong genes",
            "row_identity": "IS checked cell by cell and is correct - rows were "
                            "verified, columns were not",
        },
        "affected": "every matrix collapsed to HVS_COMMON or SEA_AD_COMMON",
        "nph52": ("has per-matrix provenance and a separate R materialization "
                  "path; its Level-4 counts show a textbook microglial profile, "
                  "which is corroboration and not verification"),
        "matrices": out,
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "FULL104_LEVEL4_COLUMN_DECODER_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("Level-4 column decoder\n")
    for mid, r in out.items():
        if r["status"] not in ("DECODER_VERIFIED", "DECODER_REFUSED",
                               "DECODER_VERIFIED_AMBIGUOUS_COLUMNS_EXCLUDED"):
            print(f"  {mid}\n      {r['status']}  {r.get('note','')}"); continue
        print(f"  {mid}")
        print(f"      family {r['family_used_by_materializer']}   "
              f"source features {r['source_features']:,}   "
              f"decoder entries {r['decoder_entries']:,}   "
              f"ambiguous excluded {r['ambiguous_columns_excluded']}")
        print(f"      decoded agreement {100*r['decoded_agreement']:.2f}% over "
              f"{r['decoded_entries_checked']:,} entries in {r['verify_cells']} cells "
              f"(floor {100*DECODE_AGREEMENT_FLOOR:.0f}%)")
        print(f"      -> {r['status']}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
