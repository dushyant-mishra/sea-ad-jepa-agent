#!/usr/bin/env python3
"""Do the FULL104 Level-4 blocks put each gene's counts at the right address?

WHY THIS EXISTS

  Extracting R8's gene panels from the Level-4 blocks produced numbers that are
  not biologically possible. In 512 SEA-AD middle-temporal-gyrus nuclei, C1QA
  was detected in 0.0% and CSF1R in 0.2%; in an HVS myeloid block, APOE and
  CSF1R were detected in 0.0% while TREM2 appeared in 79.3%. C1QA and CSF1R are
  among the most reliably detected genes in any microglial population, and the
  source objects carry them at 35% and 55%.

  The obvious suspects were checked first and cleared. The address namespace
  holds exactly the intended symbol at all 29 addresses, every one
  current_exact. None of them appear in the collision ledger. The support
  ledger declares every one measured in every matrix. Every CSR row is sorted,
  and a dense readback that assumes nothing about ordering reproduces the
  extraction exactly. So the reading was right and the question moved upstream.

WHAT THIS CHECKS

  For a block, take each nucleus's expression_row into the AUTHENTICATED source
  asset named in ASSET_AUTHENTICATION.csv, and compare the Level-4 row against
  the source row address by address, joining on Ensembl gene ID.

  Three things are reported and they separate cleanly:

    ROW identity     does the block's canonical_cell_id equal the source's own
                     index at expression_row, and does source_library equal the
                     source row's total? This tests WHICH CELL.
    COLUMN identity  does the Level-4 value at address A equal the source value
                     for the gene that the address namespace says A is? This
                     tests WHICH GENE.
    PERMUTATION      is the multiset of values identical between the two rows?
                     If yes, no counts were lost or invented and the defect is
                     purely a reordering.

  A high row agreement with a low column agreement is the signature of a
  scrambled gene mapping: the right cell, the right total, the wrong genes.

IDENTIFIER JOINS ARE THE TRAP AND ARE HANDLED EXPLICITLY

  Source objects disagree about what their var index holds. The HVS CELLxGENE
  object indexes by Ensembl ID; the SEA-AD object indexes by SYMBOL and keeps
  Ensembl IDs in var['gene_ids']. Joining an Ensembl-keyed namespace against a
  symbol-keyed index returns exactly 0.0% agreement for a reason that has
  nothing to do with the data. This script locates an Ensembl column, refuses
  to run if it cannot find one, and records which column it joined on.

  Counts also do not always live in X. CELLxGENE objects put raw counts in
  raw/X and a normalized layer in X; the SEA-AD object puts them in
  layers['UMIs'] and a normalized layer in X. Comparing against a normalized
  layer would produce a meaningless mismatch, so the layer used is chosen
  explicitly and recorded.

Nothing is trained and no outcome is read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter

import numpy as np

# agreement below this, with row identity intact, is treated as a scrambled
# column mapping rather than noise. Chance agreement at these count
# distributions - many 1s and 2s landing on an address that is also nonzero -
# sits around 4-5%, so the bound is set well above that and far below the
# >95% a correct mapping must produce.
COLUMN_AGREEMENT_FLOOR = 0.90


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


def find_ensg_column(var):
    """Return (values, column_name) for the Ensembl IDs, or (None, None)."""
    vi = index_name(var)
    cand = [vi] + [c for c in var.keys() if c != vi]
    for c in cand:
        try:
            v = h5_col(var, c)
        except Exception:
            continue
        if v.size and str(v[0]).startswith("ENSG"):
            return np.asarray([str(x).split(".")[0] for x in v], dtype=object), c
    return None, None


def pick_count_layer(f):
    """Raw counts, never a normalized layer. Returns (group, label)."""
    if "raw" in f and "X" in f["raw"]:
        return f["raw"]["X"], "raw/X"
    if "layers" in f:
        for k in ("UMIs", "counts", "UMI", "raw_counts"):
            if k in f["layers"]:
                return f["layers"][k], f"layers/{k}"
    return f["X"], "X"


def verify_block(l4_root, block_row, asset_path, n_cells, addr2ensg):
    import h5py
    R = os.path.join(l4_root, os.path.dirname(block_row["meta_path"]))
    base = os.path.basename(block_row["meta_path"]).replace(".meta.csv", "")
    meta = list(csv.DictReader(open(os.path.join(R, base + ".meta.csv"), newline="")))
    z = np.load(os.path.join(R, base + ".counts.npz"))
    ip, ind, dat = z["indptr"], z["indices"], z["data"]

    with h5py.File(asset_path, "r") as f:
        ensg, ensg_col = find_ensg_column(f["var"])
        if ensg is None:
            return {"status": "REFUSED_NO_ENSEMBL_COLUMN_IN_VAR",
                    "var_columns": list(f["var"].keys())}
        X, layer = pick_count_layer(f)
        # a raw-count layer must be integral; a normalized one is not
        probe = X["data"][:4096] if hasattr(X, "keys") else X[:1, :]
        integral = bool(np.all(np.abs(np.asarray(probe, dtype=np.float64)
                                      - np.rint(probe)) < 1e-6))
        obs_ix = h5_col(f["obs"], index_name(f["obs"]))
        rp = X["indptr"][:]
        xi, xd = X["indices"], X["data"]

        rows = []
        row_ok = col_match = col_tot = perm_ok = 0
        for r in range(min(n_cells, len(meta))):
            m = meta[r]
            er = int(m["expression_row"])
            lo, hi = ip[r], ip[r + 1]
            l4 = dict(zip(ind[lo:hi].tolist(), dat[lo:hi].tolist()))
            slo, shi = rp[er], rp[er + 1]
            src = {ensg[j]: float(v) for j, v in zip(xi[slo:shi], xd[slo:shi])}
            id_match = str(obs_ix[er]) == m["canonical_cell_id"]
            lib_match = abs(sum(src.values()) - float(m["source_library"])) <= \
                max(2.0, 0.01 * float(m["source_library"]))
            match = sum(1 for a, v in l4.items()
                        if addr2ensg.get(a) in src
                        and abs(src[addr2ensg[a]] - v) < 1e-6)
            perm = (Counter(round(v, 6) for v in l4.values())
                    == Counter(round(v, 6) for v in src.values()))
            row_ok += int(id_match and lib_match)
            col_match += match
            col_tot += len(l4)
            perm_ok += int(perm)
            rows.append({
                "expression_row": er,
                "cell_id_matches_source_index": bool(id_match),
                "source_library_matches_source_row_total": bool(lib_match),
                "l4_nonzero": len(l4), "source_nonzero": len(src),
                "l4_total": float(sum(l4.values())),
                "source_total": float(sum(src.values())),
                "column_agreement": match / max(len(l4), 1),
                "value_multiset_identical": bool(perm),
            })

    agree = col_match / max(col_tot, 1)
    return {
        "status": "CHECKED",
        "asset": asset_path,
        "ensembl_column": ensg_col,
        "count_layer": layer,
        "count_layer_is_integral": integral,
        "cells_checked": len(rows),
        "row_identity_ok": row_ok,
        "row_identity_fraction": row_ok / max(len(rows), 1),
        "column_agreement": agree,
        "column_agreement_floor": COLUMN_AGREEMENT_FLOOR,
        "pure_permutation_cells": perm_ok,
        "verdict": ("COLUMN_IDENTITY_OK" if agree >= COLUMN_AGREEMENT_FLOOR else
                    "GENE_IDENTITY_SCRAMBLED__RIGHT_CELL_WRONG_GENES"
                    if row_ok == len(rows) else
                    "ROW_AND_COLUMN_BOTH_SUSPECT"),
        "per_cell": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l4-root", required=True)
    ap.add_argument("--bundle-root", required=True)
    ap.add_argument("--repo-root", required=True,
                    help="directory the ASSET_AUTHENTICATION paths are relative to")
    ap.add_argument("--matrices", required=True,
                    help="comma-separated matrix_id values to verify")
    ap.add_argument("--cells-per-block", type=int, default=8)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    addr2ensg = {}
    with open(os.path.join(a.bundle_root, "contracts", "address_namespace.csv"),
              newline="") as fh:
        for r in csv.DictReader(fh):
            addr2ensg[int(r["molecular_address_index"])] = r["molecular_address_id"]

    assets = {}
    with open(os.path.join(a.l4_root, "ASSET_AUTHENTICATION.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            assets[r["matrix_id"]] = r

    man = {}
    with open(os.path.join(a.l4_root, "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
              newline="") as fh:
        for r in csv.DictReader(fh):
            man.setdefault(r["matrix_id"], r)   # first block of each matrix

    out = {}
    for mid in [x.strip() for x in a.matrices.split(",") if x.strip()]:
        if mid not in man:
            out[mid] = {"status": "NO_BLOCK_IN_MANIFEST"}; continue
        if mid not in assets:
            out[mid] = {"status": "NO_ASSET_AUTHENTICATION_ROW"}; continue
        ap_path = os.path.join(a.repo_root, assets[mid]["path"])
        if not os.path.exists(ap_path):
            out[mid] = {"status": "ASSET_NOT_ON_DISK", "path": assets[mid]["path"]}
            continue
        if not ap_path.lower().endswith((".h5ad", ".h5")):
            out[mid] = {"status": "ASSET_NOT_READABLE_BY_THIS_VERIFIER",
                        "path": assets[mid]["path"],
                        "note": "only HDF5 sources are verifiable here; an R .qs "
                                "source needs its own reader and is NOT verified, "
                                "which is not the same as being correct"}
            continue
        res = verify_block(a.l4_root, man[mid], ap_path, a.cells_per_block, addr2ensg)
        res["asset_sha256_recorded"] = assets[mid]["sha256"]
        out[mid] = res

    receipt = {
        "schema": "V5_FULL104_LEVEL4_GENE_IDENTITY_VERIFIER_V1",
        "status": "VERIFICATION_AGAINST_AUTHENTICATED_SOURCE_ASSETS",
        "question": "does the Level-4 value at molecular address A equal the "
                    "source's value for the gene the address namespace says A is?",
        "cleared_before_concluding": [
            "all 29 panel addresses hold the intended symbol and are current_exact",
            "none appear in the collision ledger",
            "the support ledger declares them measured in every matrix checked",
            "every CSR row is index-sorted",
            "a dense readback assuming no ordering reproduces the extraction",
        ],
        "matrices": out,
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "FULL104_LEVEL4_GENE_IDENTITY_VERIFIER_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("Level-4 gene identity verification\n")
    for mid, r in out.items():
        if r.get("status") != "CHECKED":
            print(f"  {mid}\n      {r['status']}  {r.get('note','')}")
            continue
        print(f"  {mid}")
        print(f"      source      {os.path.basename(r['asset'])}")
        print(f"      joined on   var['{r['ensembl_column']}']   counts from "
              f"{r['count_layer']} (integral={r['count_layer_is_integral']})")
        print(f"      ROW    identity ok in {r['row_identity_ok']}/{r['cells_checked']} cells")
        print(f"      COLUMN agreement {100*r['column_agreement']:.1f}%  "
              f"(floor {100*COLUMN_AGREEMENT_FLOOR:.0f}%)")
        print(f"      value multiset identical in "
              f"{r['pure_permutation_cells']}/{r['cells_checked']} cells")
        print(f"      -> {r['verdict']}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
