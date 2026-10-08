#!/usr/bin/env python3
"""Recover the Level-4 column permutation, and ask what rule generated it.

THE QUESTION

  The Level-4 blocks carry each nucleus's counts complete and intact but at the
  wrong molecular addresses; for HVS the value multiset is identical cell for
  cell, so it is a pure reordering. Two explanations survive and they have very
  different consequences:

    A. THE SUBSTRATE IS WRONG. The materialization applied a bad permutation and
       the blocks have to be rebuilt.
    B. THE DECODER IS MISSING. The blocks are written against a DIFFERENT but
       well-defined address ordering than `address_namespace.csv`, and the
       substrate is fine once the right column map is used.

  B is strongly suggested by the materialization contract, which records
  selection_sha256, selection_manifest_sha256, freeze_manifest_sha256 and
  code_sha256 and references none of the registry semantic hash that the loader
  manifest and address_namespace.csv share. But suggested is not shown.

  The two are distinguished by whether the recovered permutation is a RULE or
  is arbitrary. A rule - "the columns are the same gene set ordered by symbol",
  say - means B. No rule means A.

HOW THE PERMUTATION IS RECOVERED

  Take one block of 512 nuclei and the same 512 rows of the source object.
  Every gene is then a 512-long column vector in each representation. A column
  is identified by the exact pattern of which of the 512 nuclei are nonzero and
  what their values are, which is a near-unique fingerprint for any gene with
  more than a handful of nonzero entries.

  Match on that fingerprint. Columns whose fingerprint is not unique - all-zero
  columns, and the many genes detected in exactly one nucleus at a count of one
  - are reported as AMBIGUOUS and never guessed at.

THEN TEST WHETHER THE MAPPING IS A RULE

  Against the recovered pairs, four candidate orderings of the SAME 41,238
  address space are checked, each of which would make the substrate correct and
  only the decoder wrong:

    * address_namespace order by molecular_address_index   (the assumed one)
    * the same rows sorted by symbol
    * the same rows sorted by molecular_address_id as a string
    * the source object's own var order, offset into the address space

  A candidate that reproduces the recovered pairs is the decoder. If none does,
  the permutation is not a reordering of this address space and explanation A
  stands.

Nothing is trained and no outcome is read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict

import numpy as np


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


def col_fingerprints(indptr, indices, data, n_rows):
    """column -> sha1 of the exact (row, value) pattern, plus its nnz."""
    per = defaultdict(list)
    for r in range(n_rows):
        lo, hi = int(indptr[r]), int(indptr[r + 1])
        for c, v in zip(indices[lo:hi], data[lo:hi]):
            per[int(c)].append((r, float(v)))
    out = {}
    for c, pairs in per.items():
        pairs.sort()
        h = hashlib.sha1(
            ("|".join(f"{r}:{v:.6g}" for r, v in pairs)).encode()).hexdigest()
        out[c] = (h, len(pairs))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l4-root", required=True)
    ap.add_argument("--bundle-root", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--matrix-id", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min-nnz", type=int, default=4,
                    help="columns with fewer nonzeros than this are not matched; "
                         "their fingerprints are not distinctive enough to trust")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    import h5py

    # ---- namespace
    ns_rows = []
    with open(os.path.join(a.bundle_root, "contracts", "address_namespace.csv"),
              newline="") as fh:
        for r in csv.DictReader(fh):
            ns_rows.append((int(r["molecular_address_index"]),
                            r["molecular_address_id"], r["symbol"]))
    ns_rows.sort()
    addr2ensg = {i: e for i, e, _ in ns_rows}
    addr2sym = {i: s for i, _, s in ns_rows}
    ensg2addr = {e: i for i, e, _ in ns_rows}

    # ---- block + source
    man = {}
    with open(os.path.join(a.l4_root, "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
              newline="") as fh:
        for r in csv.DictReader(fh):
            man.setdefault(r["matrix_id"], r)
    assets = {}
    with open(os.path.join(a.l4_root, "ASSET_AUTHENTICATION.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            assets[r["matrix_id"]] = r
    b = man[a.matrix_id]
    R = os.path.join(a.l4_root, os.path.dirname(b["meta_path"]))
    base = os.path.basename(b["meta_path"]).replace(".meta.csv", "")
    meta = list(csv.DictReader(open(os.path.join(R, base + ".meta.csv"), newline="")))
    z = np.load(os.path.join(R, base + ".counts.npz"))
    ip, ind, dat = z["indptr"], z["indices"], z["data"]
    n_rows = len(meta)

    src_path = os.path.join(a.repo_root, assets[a.matrix_id]["path"])
    with h5py.File(src_path, "r") as f:
        g = f["raw"] if ("raw" in f and "X" in f["raw"]) else f
        X = g["X"]
        if "raw" not in f and "layers" in f:
            for k in ("UMIs", "counts", "UMI"):
                if k in f["layers"]:
                    X = f["layers"][k]; break
        var = g["var"] if "raw" in f and "var" in f["raw"] else f["var"]
        ensg = None; ensg_col = None
        vi = index_name(var)
        for c in [vi] + [x for x in var.keys() if x != vi]:
            v = h5_col(var, c)
            if v.size and str(v[0]).startswith("ENSG"):
                ensg = np.asarray([str(x).split(".")[0] for x in v], dtype=object)
                ensg_col = c
                break
        if ensg is None:
            raise SystemExit("REFUSED_NO_ENSEMBL_COLUMN_IN_VAR")
        rp = X["indptr"][:]
        # build the same 512 rows from the source, in block order
        s_indptr = [0]; s_idx = []; s_dat = []
        for m in meta:
            er = int(m["expression_row"])
            lo, hi = int(rp[er]), int(rp[er + 1])
            s_idx.append(X["indices"][lo:hi]); s_dat.append(X["data"][lo:hi])
            s_indptr.append(s_indptr[-1] + (hi - lo))
        s_indptr = np.asarray(s_indptr)
        s_idx = np.concatenate(s_idx); s_dat = np.concatenate(s_dat)

    fp_l4 = col_fingerprints(ip, ind, dat, n_rows)
    fp_src = col_fingerprints(s_indptr, s_idx, s_dat, n_rows)

    src_by_fp = defaultdict(list)
    for c, (h, n) in fp_src.items():
        src_by_fp[h].append(c)

    matched, ambiguous, unmatched = {}, 0, 0
    for c, (h, n) in fp_l4.items():
        if n < a.min_nnz:
            ambiguous += 1; continue
        cand = src_by_fp.get(h, [])
        if len(cand) == 1:
            matched[c] = int(cand[0])
        elif len(cand) > 1:
            ambiguous += 1
        else:
            unmatched += 1

    # ---- is the recovered mapping a RULE over the same address space?
    # candidate orderings: position of the gene when the 41,238 namespace rows
    # are sorted by a given key. If the blocks were written in that order, the
    # L4 column for a gene equals its rank under that key.
    cands = {
        "namespace_molecular_address_index": [i for i, _, _ in ns_rows],
        "namespace_sorted_by_symbol": [i for i, _, _ in sorted(
            ns_rows, key=lambda r: (r[2], r[1]))],
        "namespace_sorted_by_address_id_string": [i for i, _, _ in sorted(
            ns_rows, key=lambda r: r[1])],
    }
    rank = {name: {addr: k for k, addr in enumerate(order)}
            for name, order in cands.items()}

    pairs = []
    for l4c, srcc in matched.items():
        e = str(ensg[srcc])
        pairs.append((l4c, e, ensg2addr.get(e)))

    rule_scores = {}
    for name, rk in rank.items():
        ok = tot = 0
        for l4c, e, canon in pairs:
            if canon is None:
                continue
            tot += 1
            ok += int(rk.get(canon) == l4c)
        rule_scores[name] = {"agree": ok, "of": tot,
                             "fraction": (ok / tot) if tot else None}

    # the source's own var order, offset-free: does L4 column == source column?
    same_col = sum(1 for l4c, srcc in matched.items() if l4c == srcc)
    # monotonicity: is the recovered map order-preserving in the source order?
    mp = sorted(matched.items())
    mono = int(np.all(np.diff([s for _, s in mp]) > 0)) if len(mp) > 1 else None

    ex = []
    for l4c, e, canon in sorted(pairs)[:12]:
        ex.append({"l4_column": l4c, "source_ensg": e,
                   "namespace_address_for_that_ensg": canon,
                   "symbol": addr2sym.get(canon)})

    receipt = {
        "schema": "V5_FULL104_LEVEL4_PERMUTATION_RECOVERY_V1",
        "status": "COLUMN_FINGERPRINT_MATCHING__NO_TRAINING",
        "matrix_id": a.matrix_id,
        "block": b["block_key"],
        "source_asset": assets[a.matrix_id]["path"],
        "source_ensembl_column": ensg_col,
        "nuclei_used": n_rows,
        "min_nnz_to_attempt_match": a.min_nnz,
        "l4_nonzero_columns": len(fp_l4),
        "source_nonzero_columns": len(fp_src),
        "matched_uniquely": len(matched),
        "ambiguous_fingerprint_or_too_sparse": ambiguous,
        "no_source_column_with_that_fingerprint": unmatched,
        "match_rate_over_attempted": len(matched) / max(len(matched) + unmatched, 1),
        "l4_column_equals_source_column": same_col,
        "recovered_map_is_monotone_in_source_order": mono,
        "candidate_orderings_tested": rule_scores,
        "example_recovered_pairs": ex,
        "verdict": None,
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    best = max(rule_scores.items(), key=lambda kv: kv[1]["fraction"] or 0.0)
    if best[1]["fraction"] and best[1]["fraction"] >= 0.95:
        receipt["verdict"] = f"DECODER_FOUND__{best[0]}"
    elif unmatched > len(matched):
        receipt["verdict"] = "NOT_A_PERMUTATION_OF_THIS_SOURCE__VALUES_DIFFER"
    else:
        receipt["verdict"] = "PERMUTATION_RECOVERED_BUT_NO_TESTED_ORDERING_EXPLAINS_IT"
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))

    p = os.path.join(a.out_dir, "FULL104_LEVEL4_PERMUTATION_RECOVERY_V1.json")
    with open(p, "w") as fh:
        json.dump({**receipt,
                   "recovered_map_l4_column_to_source_column":
                       {str(k): v for k, v in sorted(matched.items())}}, fh, indent=2)

    print(f"Permutation recovery - {a.matrix_id}  block {b['block_key']}\n")
    print(f"  nuclei {n_rows}   L4 nonzero cols {len(fp_l4):,}   "
          f"source nonzero cols {len(fp_src):,}")
    print(f"  matched uniquely          {len(matched):,}")
    print(f"  too sparse / ambiguous    {ambiguous:,}")
    print(f"  no matching source column {unmatched:,}")
    print(f"  L4 column == source column in {same_col:,} matches")
    print(f"  recovered map monotone in source order: {mono}")
    print("\n  candidate orderings of the SAME address space:")
    for name, s in rule_scores.items():
        frac = f"{100*s['fraction']:.1f}%" if s["fraction"] is not None else "n/a"
        print(f"      {name:44s} {s['agree']:6d}/{s['of']:<6d}  {frac}")
    print(f"\n  -> {receipt['verdict']}")
    print(f"\n  example recovered pairs:")
    for e in ex[:8]:
        print(f"      L4 col {e['l4_column']:6d}  ==  {e['symbol']} ({e['source_ensg']}) "
              f"whose namespace address is {e['namespace_address_for_that_ensg']}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
