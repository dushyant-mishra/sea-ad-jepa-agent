#!/usr/bin/env python3
"""Corrected view v3: decoded columns AND a per-element availability mask.

WHAT v3 FIXES IN v2, and why it mattered

  v2 decoded the columns correctly and recorded, per matrix, which target
  addresses are absent from that source. It then wrote those absent addresses
  into the counts array as 0.

  A receipt is read by a person once; the array is read by every downstream
  script forever, and nothing in a 0 announces that it means "never measured".
  Any consumer computing a detection fraction, a sum, a mean or a fit would
  silently treat the absence as an observation of zero expression, which is a
  real biological claim and a false one.

  The scale is not marginal. PGK1 (address 2628) is absent from all eleven
  SEA-AD matrices, so it was written as a zero for 170,528 of 187,909 nuclei -
  90.8%. LPL (13734) is absent from the filtered HVS object, 2,117 nuclei.

  v3 emits `address_available`, a per-nucleus by per-address boolean, in the
  npz itself. Consumers must act on it rather than trust it: a routine that
  uses a gene should REFUSE when that gene is unavailable for the rows it was
  given, not quietly proceed.

  v2 and its output are left in place as the record of the intermediate view.

THE DENOMINATOR, stated exactly

  `total_excluding_29` is the nucleus's total observed count MINUS the ban-set
  addresses that THIS MATRIX ACTUALLY MEASURES. An address the source never
  measured contributes nothing to the total and is not subtracted from it, so
  the arithmetic is self-consistent - but the gene set subtracted differs
  between sources, making this a SOURCE-SPECIFIC reference. That is defensible
  within a source and is not automatically comparable across sources; anything
  transported across sources needs its own comparability check first. The count
  actually subtracted is recorded per matrix as `ban_addresses_subtracted`.

Corrected view: R8's panels for FULL104 myeloid nuclei, with columns decoded.

THIS IS A SEPARATE ARTIFACT, NOT A REPLACEMENT

  The Level-4 blocks put each nucleus's counts at the addresses of DIFFERENT
  genes, because the materializer indexed a family-level provenance table -
  whose `source_feature_index` is the Ensembl-ascending rank over a merged
  feature set - as though it were the h5ad's own genomic-ordered column index.

  Nothing here modifies those blocks. They stay exactly as written, because they
  are the evidence that the defect existed and because provenance records across
  the project point at their digests. This script reads them THROUGH a
  per-matrix decoder and writes a NEW, separately authenticated view beside
  them. full104_myeloid_panel_extraction_v1.py and its output are likewise left
  in place as the record of the uncorrected view.

WHAT MAKES THE CORRECTED VIEW TRUSTWORTHY, and it is not this script

  Each decoder was verified independently by
  full104_level4_column_decoder_v1.py, cell by cell against the authenticated
  source asset, before being written; all twelve HDF5 myeloid matrices reached
  100.00% agreement. Columns where two source features were summed together are
  excluded and listed rather than assigned to one of them.

  NPH52 needs no decoder. Its provenance is keyed to its own object rather than
  to a _COMMON family, and nph52_feature_axis_verifier_v1.py confirmed against
  assay(object,"counts") that rownames[source_feature_index] equals the recorded
  symbol for 32,176 of 32,176 rows, with the 1-based alternative at 0.00%. It is
  read with an identity map and labelled as such.

  This script REFUSES any matrix for which it cannot load a verified decoder or
  an explicitly verified identity, rather than falling back to the naive column
  assumption that caused the defect. It also refuses if any R8 panel address is
  unreachable in a matrix, because a panel silently missing a partner is a
  different target, not a weaker one.

WHAT THIS OPENS AND WHY

  R8 measured three microglial programs on 361 nuclei drawn from TWO operators,
  with a median of about one partner molecule per nucleus, and the reliability
  gate returned INSUFFICIENTLY_MEASURED for all three. That verdict is correct
  about that substrate and says nothing about the targets, because no target
  could have been measured there.

  The FULL104 Level-4 blocks hold raw integer counts for 4,553,407 nuclei over
  41,238 addresses, with the normalization explicitly deferred. 187,909 of
  those nuclei carry a candidate myeloid label. This script reads ONLY the 29
  addresses R8's contract needs, for ONLY those nuclei.

  29 = 21 program addresses (3 programs x query + 4 partners + 2 reserved
  readouts) + 8 disjoint housekeeping reference genes. This is the same
  exclusion count R8 recorded.

WHAT IT DOES NOT OPEN

  No pathology, no donor outcome, no sealed confirmation set. Nothing is
  trained. The reserved readout genes are extracted but must stay reserved -
  they exist so that an independent readout test is possible later, and using
  them now would spend the only held-out signal these panels have.

SOURCES ARE NOT HARMONIZED

  Every nucleus keeps its own source and its own source's label. The SEA-AD
  consortium supertype is attached to SEA_AD 'Immune' nuclei as a column, not
  applied as a filter, so myeloid restriction stays a decision downstream
  rather than something baked in here.

IDENTITY IS CHECKED, NOT ASSUMED

  A cell's identity is its selection_row and its canonical_cell_id, never its
  position in a block. Three checks run and any failure refuses the whole
  extraction: the donor_id in the block metadata must agree with the donor_id
  in the authenticated metadata for every joined nucleus; every eligible
  nucleus must be found exactly once; and no selection_row may repeat.

  Every block actually read is verified against its manifest SHA-256 - both the
  counts file and the metadata file - by hashing the bytes on the way in, which
  costs nothing extra because they are being read anyway.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sqlite3
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

FIT_PARTITION = "reader_fit"

CANDIDATE_LABELS = (
    ("HVS", "Microglia-PVM"),
    ("NPH52", "MG"),
    ("SEA_AD", "Immune"),
    ("SEA_AD", "Microglia-PVMSubclass"),
)

# R8's own recorded addresses, from JEPA_R8_STRUCTURED_TARGET_RESULTS_20260926.json
R8_ADDR = {
    "APOE_LIPID": {"query": 6186, "panel": [6188, 11425, 7194, 2044],
                   "readout": [4748, 13734]},
    "P2RY12_HOMEOSTATIC": {"query": 12469, "panel": [15109, 12239, 12995, 13365],
                           "readout": [2810, 14980]},
    "HLA_DRA_ANTIGEN": {"query": 18511, "panel": [392, 23673, 18500, 20496],
                        "readout": [26659, 10846]},
}
# R8's eight disjoint housekeeping reference genes, resolved against
# address_namespace.csv; each maps to exactly one current_exact address.
HOUSE_ADDR = {"RPLP0": 1817, "EEF1A1": 9924, "PGK1": 2628, "HPRT1": 11587,
              "PPIA": 16586, "RPL13A": 8192, "GUSB": 12595, "SDHA": 1225}

PROGRAM_ADDRS = []
for _p, _g in R8_ADDR.items():
    PROGRAM_ADDRS += [_g["query"]] + list(_g["panel"]) + list(_g["readout"])
BAN_ADDRS = sorted(set(PROGRAM_ADDRS) | set(HOUSE_ADDR.values()))
TARGET_ADDRS = np.asarray(BAN_ADDRS, dtype=np.int64)
assert len(BAN_ADDRS) == 29, f"expected 29 excluded addresses, got {len(BAN_ADDRS)}"


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def load_eligible(db_path: str, immune_h5ad: str | None) -> dict:
    """canonical_cell_id -> (source, native_class, donor_id, matrix_id, supertype)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        where = " or ".join(
            f"(source='{s}' and native_class='{n}')" for s, n in CANDIDATE_LABELS)
        rows = con.execute(
            f"select cell_id, source, native_class, donor_id, matrix_id "
            f"from cells where partition='{FIT_PARTITION}' and ({where})").fetchall()
    finally:
        con.close()
    elig = {r[0]: [r[1], r[2], r[3], r[4], ""] for r in rows}
    if len(elig) != len(rows):
        raise SystemExit("REFUSED: candidate cell_id is not unique in reader_fit")

    if immune_h5ad:
        import h5py
        with h5py.File(immune_h5ad, "r") as f:
            obs = f["obs"]
            idx = obs.attrs["_index"]
            idx = idx.decode() if isinstance(idx, bytes) else str(idx)

            def dec(a):
                return np.asarray([x.decode() if isinstance(x, (bytes, np.bytes_))
                                   else str(x) for x in a], dtype=object)
            bc = obs[idx]
            bc = dec(bc["categories"][:])[bc["codes"][:]] if hasattr(bc, "keys") \
                else dec(bc[:])
            st = obs["Supertype"]
            st = dec(st["categories"][:])[st["codes"][:]] if hasattr(st, "keys") \
                else dec(st[:])
        lut = dict(zip(bc, st))
        hit = 0
        for cid, v in elig.items():
            if v[0] == "SEA_AD" and v[1] == "Immune":
                s = lut.get(cid)
                if s is not None:
                    v[4] = str(s); hit += 1
        print(f"  supertype attached to {hit:,} SEA_AD Immune nuclei", flush=True)
    return elig


def read_manifest(l4_root: str) -> list:
    p = os.path.join(l4_root, "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv")
    out = []
    with open(p, newline="") as fh:
        for row in csv.DictReader(fh):
            out.append(row)
    return out



IDENTITY_VERIFIED_MATRICES = {
    # verified by nph52_feature_axis_verifier_v1.py against assay(obj,"counts")
    "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs":
        "NPH52_FEATURE_AXIS_VERIFIED_ZERO_BASED",
}


# Losing a QUERY or PANEL address breaks the R8 target itself: its contract
# requires exactly four partners and raises on any other length, so three of
# four is a different target, not a weaker one. Losing a RESERVED READOUT or a
# HOUSEKEEPING address costs a diagnostic, not the target, and is recorded
# rather than refused. HVS is a filtered CELLxGENE object of 18,736 genes and
# genuinely lacks LPL (address 13734), a reserved readout.
REQUIRED_ADDRS = set()
for _p, _g in R8_ADDR.items():
    REQUIRED_ADDRS.add(_g["query"])
    REQUIRED_ADDRS.update(_g["panel"])


def load_addr_to_col(decoder_dir, matrix_id, targets):
    """Return (block columns per target address, status, unreachable list).

    Refuses rather than guessing: a matrix with no verified decoder and no
    verified identity is not read at all. A target that is unreachable is given
    column -1, which the reader treats as a measured absence, never as a zero.
    """
    if matrix_id in IDENTITY_VERIFIED_MATRICES:
        return (np.asarray(targets, dtype=np.int64),
                IDENTITY_VERIFIED_MATRICES[matrix_id], [])
    stem = matrix_id.replace("::", "__").replace("/", "_")
    path = os.path.join(decoder_dir, f"decoder_{stem}.npz")
    if not os.path.exists(path):
        return None, "NO_VERIFIED_DECODER", []
    z = np.load(path)
    addr2col = {int(a): int(c) for c, a in zip(z["block_column"], z["true_address"])}
    cols = np.asarray([addr2col.get(int(t), -1) for t in targets], dtype=np.int64)
    unreachable = [int(t) for t, c in zip(targets, cols) if c < 0]
    broken = sorted(set(unreachable) & REQUIRED_ADDRS)
    if broken:
        return None, f"R8_PANEL_ADDRESSES_UNREACHABLE:{broken}", unreachable
    status = ("DECODER_VERIFIED" if not unreachable else
              "DECODER_VERIFIED_NONPANEL_ADDRESSES_ABSENT")
    return cols, status, unreachable


def process_operator(args):
    l4_root, blocks, elig_sub, probe_cols = args
    # probe_cols[i] is the BLOCK COLUMN holding TARGET_ADDRS[i] in this
    # matrix. searchsorted needs a sorted probe, so sort and un-permute.
    reachable = probe_cols >= 0
    order = np.argsort(np.where(reachable, probe_cols, np.iinfo(np.int64).max))
    sorted_probe = probe_cols[order]
    sorted_reachable = reachable[order]
    recs = []
    read_blocks = 0
    skipped_blocks = 0
    donor_mismatch = []
    for b in blocks:
        mp = os.path.join(l4_root, b["meta_path"])
        with open(mp, "rb") as fh:
            mb = fh.read()
        if sha_bytes(mb) != b["meta_sha256"]:
            raise RuntimeError(f"META_SHA_MISMATCH {b['block_key']}")
        rdr = csv.DictReader(io.StringIO(mb.decode()))
        meta = list(rdr)
        sel = [(i, m) for i, m in enumerate(meta)
               if m["canonical_cell_id"] in elig_sub]
        if not sel:
            skipped_blocks += 1
            continue

        cp = os.path.join(l4_root, b["counts_path"])
        with open(cp, "rb") as fh:
            cb = fh.read()
        if sha_bytes(cb) != b["counts_sha256"]:
            raise RuntimeError(f"COUNTS_SHA_MISMATCH {b['block_key']}")
        z = np.load(io.BytesIO(cb))
        indptr = z["indptr"]; indices = z["indices"]; data = z["data"]
        read_blocks += 1

        for i, m in sel:
            lo, hi = int(indptr[i]), int(indptr[i + 1])
            ridx = indices[lo:hi]
            rdat = data[lo:hi]
            # CSR row indices are ascending, so a searchsorted lookup is exact
            pos = np.searchsorted(ridx, sorted_probe)
            pos_c = np.clip(pos, 0, max(len(ridx) - 1, 0))
            found = ((len(ridx) > 0) & (pos < len(ridx))
                     & (ridx[pos_c] == sorted_probe) & sorted_reachable)
            sv = np.zeros(sorted_probe.shape[0], dtype=np.int64)
            sv[found] = rdat[pos_c[found]]
            vals = np.empty_like(sv)
            vals[order] = sv          # back to TARGET_ADDRS order
            total_all = int(rdat.sum())
            total_excl = total_all - int(vals.sum())
            e = elig_sub[m["canonical_cell_id"]]
            if str(m["donor_id"]) != str(e[2]):
                donor_mismatch.append(
                    {"cell_id": m["canonical_cell_id"], "block_meta_donor": m["donor_id"],
                     "authenticated_donor": e[2], "block": b["block_key"]})
            recs.append((
                m["canonical_cell_id"], e[0], e[1], e[2], e[3], e[4],
                int(m["selection_row"]), int(m["source_library"]),
                int(b["operator_index"]), b["block_key"],
                total_all, total_excl, vals, reachable))
    return recs, read_blocks, skipped_blocks, donor_mismatch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l4-root", required=True)
    ap.add_argument("--metadata-sqlite", required=True)
    ap.add_argument("--immune-h5ad", default=None)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--decoder-dir", required=True,
                    help="directory of verified per-matrix decoder .npz files "
                         "written by full104_level4_column_decoder_v1.py")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit-operators", type=int, default=0,
                    help="smoke test: process only the first N operators")
    ap.add_argument("--only-operators", default="",
                    help="comma-separated operator indices to process")
    ap.add_argument("--eligible-cache", default=None,
                    help="JSON cache of the eligible set. Building it costs a "
                         "full scan of the 2.7 GB metadata (about six minutes), "
                         "which is wasteful to repeat across runs. The cache is "
                         "keyed by the metadata SHA-256 and is REBUILT, never "
                         "trusted, if that digest differs.")
    a = ap.parse_args()

    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    contract_p = os.path.join(a.l4_root, "MATERIALIZATION_CONTRACT.json")
    contract = json.load(open(contract_p))
    if contract.get("status") != "PASS_PHASE2_EXPRESSION_MATERIALIZED":
        raise SystemExit(f"REFUSED_CONTRACT_NOT_PASS {contract.get('status')}")
    if int(contract["addresses"]) != 41238:
        raise SystemExit("REFUSED_ADDRESS_SPACE_MISMATCH")

    meta_sha = sha_file(a.metadata_sqlite)
    h5_sha = sha_file(a.immune_h5ad) if a.immune_h5ad else None
    elig = None
    if a.eligible_cache and os.path.exists(a.eligible_cache):
        try:
            c = json.load(open(a.eligible_cache))
            # a cache keyed by a different input is not a cache, it is a
            # different dataset wearing the same filename
            if c.get("metadata_sha256") == meta_sha and c.get("immune_sha256") == h5_sha:
                elig = {k: list(v) for k, v in c["eligible"].items()}
                print(f"  eligible set restored from cache "
                      f"({len(elig):,} nuclei, digests match)", flush=True)
            else:
                print("  eligible cache REJECTED: input digests differ; "
                      "rebuilding", flush=True)
        except Exception as exc:
            print(f"  eligible cache unreadable ({exc}); rebuilding", flush=True)
    if elig is None:
        print("loading eligible nuclei...", flush=True)
        elig = load_eligible(a.metadata_sqlite, a.immune_h5ad)
        if a.eligible_cache:
            with open(a.eligible_cache, "w") as fh:
                json.dump({"metadata_sha256": meta_sha, "immune_sha256": h5_sha,
                           "eligible": elig}, fh)
    print(f"  {len(elig):,} candidate myeloid nuclei", flush=True)

    man = read_manifest(a.l4_root)
    by_op = defaultdict(list)
    for b in man:
        by_op[int(b["operator_index"])].append(b)
    ops = sorted(by_op)
    if a.only_operators:
        want = {int(x) for x in a.only_operators.split(",") if x.strip()}
        ops = [o for o in ops if o in want]
    elif a.limit_operators:
        ops = ops[:a.limit_operators]

    # Each operator is a single matrix, so an operator's eligible set is just
    # the nuclei from that matrix. Subsetting keeps the pickled payload small.
    op_matrix = {op: by_op[op][0]["matrix_id"] for op in ops}
    by_matrix = defaultdict(dict)
    for cid, v in elig.items():
        by_matrix[v[3]][cid] = v

    jobs = []
    decoder_status = {}
    refused = {}
    for op in ops:
        mid = op_matrix[op]
        sub = by_matrix.get(mid, {})
        if not sub:
            continue
        cols, status, unreachable = load_addr_to_col(a.decoder_dir, mid, TARGET_ADDRS)
        decoder_status[mid] = {
            "status": status,
            "addresses_absent_from_source": unreachable,
            "ban_addresses_subtracted": int(len(TARGET_ADDRS) - len(unreachable)),
            "ban_addresses_total": int(len(TARGET_ADDRS)),
        }
        if cols is None:
            refused[mid] = status
            continue
        jobs.append((a.l4_root, by_op[op], sub, cols))
    if refused:
        print("  REFUSED (no verified decoder / unreachable targets):", flush=True)
        for k, v in refused.items():
            print(f"      {k}  {v}", flush=True)
    print(f"  {len(jobs)} operators carry candidate nuclei "
          f"(of {len(ops)} considered)", flush=True)

    all_recs, tot_read, tot_skip, mism = [], 0, 0, []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(process_operator, j): j[2] for j in jobs}
        done = 0
        for f in as_completed(futs):
            recs, rb, sb, dm = f.result()
            all_recs.extend(recs); tot_read += rb; tot_skip += sb; mism.extend(dm)
            done += 1
            print(f"  [{done}/{len(jobs)}] +{len(recs):,} nuclei "
                  f"(blocks read {rb}, skipped {sb})", flush=True)

    if mism:
        with open(os.path.join(a.out_dir, "DONOR_MISMATCHES.json"), "w") as fh:
            json.dump(mism[:500], fh, indent=2)
        raise SystemExit(
            f"REFUSED_DONOR_IDENTITY_MISMATCH on {len(mism)} nuclei; the block "
            "metadata donor disagrees with the authenticated metadata donor. "
            "Examples written to DONOR_MISMATCHES.json")

    cids = [r[0] for r in all_recs]
    sel_rows = np.asarray([r[6] for r in all_recs], dtype=np.int64)
    dup_cells = len(cids) - len(set(cids))
    dup_sel = sel_rows.size - np.unique(sel_rows).size
    processed_matrices = {op_matrix[op] for op in ops} - set(refused)
    expected = sum(1 for cid, v in elig.items() if v[3] in processed_matrices)
    missing = expected - len(set(cids))

    identity = {
        "eligible_total": len(elig),
        "expected_in_processed_operators": expected,
        "recovered": len(set(cids)),
        "missing": int(missing),
        "duplicate_cell_ids": int(dup_cells),
        "duplicate_selection_rows": int(dup_sel),
        "donor_id_mismatches": 0,
        "all_checks_pass": bool(dup_cells == 0 and dup_sel == 0 and missing == 0),
    }
    partial_run = bool(a.limit_operators or a.only_operators)
    if not identity["all_checks_pass"] and not partial_run:
        with open(os.path.join(a.out_dir, "IDENTITY_FAILURE.json"), "w") as fh:
            json.dump(identity, fh, indent=2)
        raise SystemExit(f"REFUSED_IDENTITY_CLOSURE_FAILED {identity}")

    counts = np.stack([r[12] for r in all_recs]).astype(np.int32) if all_recs \
        else np.zeros((0, 29), dtype=np.int32)
    np.savez_compressed(
        os.path.join(a.out_dir, "FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz"),
        cell_id=np.asarray(cids, dtype=object),
        source=np.asarray([r[1] for r in all_recs], dtype=object),
        native_class=np.asarray([r[2] for r in all_recs], dtype=object),
        donor_id=np.asarray([r[3] for r in all_recs], dtype=object),
        matrix_id=np.asarray([r[4] for r in all_recs], dtype=object),
        supertype=np.asarray([r[5] for r in all_recs], dtype=object),
        selection_row=sel_rows,
        source_library=np.asarray([r[7] for r in all_recs], dtype=np.int64),
        operator_index=np.asarray([r[8] for r in all_recs], dtype=np.int32),
        total_all=np.asarray([r[10] for r in all_recs], dtype=np.int64),
        total_excluding_29=np.asarray([r[11] for r in all_recs], dtype=np.int64),
        address_columns=TARGET_ADDRS,
        counts=counts,
        address_available=available)

    receipt = {
        "schema": "V5_FULL104_MYELOID_R8_PANEL_EXTRACTION_V1",
        "status": "RAW_COUNTS_READ_FOR_29_ADDRESSES_ON_CANDIDATE_MYELOID_NUCLEI",
        "l4_contract": contract,
        "l4_manifest_sha256": sha_file(
            os.path.join(a.l4_root, "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv")),
        "blocks_read_and_sha_verified": tot_read,
        "blocks_skipped_no_candidate_nuclei": tot_skip,
        "every_block_read_was_sha256_verified": True,
        "identity_closure": identity,
        "addresses_extracted": {
            "r8_programs": R8_ADDR,
            "housekeeping_reference": HOUSE_ADDR,
            "total_excluded_from_observed_total": len(BAN_ADDRS),
        },
        "reserved_readouts_must_stay_reserved": (
            "the six readout addresses are extracted so an independent-readout "
            "test is possible later; spending them now would consume the only "
            "held-out signal these panels have"),
        "normalization_not_applied": (
            "raw integer counts and source_library are stored as-is; the "
            "materialization contract defers log1p(raw*10000/library) to "
            "exactly one downstream application"),
        "corrected_view": True,
        "address_available_emitted": True,
        "address_available_semantics": (
            "address_available[i, j] is False when this nucleus's matrix does "
            "not measure address_columns[j]. counts[i, j] is then a PLACEHOLDER "
            "ZERO and must not be read as an observation. Consumers must refuse "
            "rather than proceed when a gene they need is unavailable."),
        "reference_definition": (
            "total_excluding_29 = the nucleus's total observed count minus the "
            "ban-set addresses THIS MATRIX MEASURES. An unmeasured address "
            "contributes nothing to the total and is not subtracted from it. "
            "The subtracted set therefore differs between sources, making this "
            "a SOURCE-SPECIFIC reference: defensible within a source, and not "
            "automatically comparable across sources."),
        "supersedes": "full104_myeloid_panel_extraction_v2_decoded.py output, "
                      "which wrote unmeasured addresses as indistinguishable zeros",
        "originals_untouched": (
            "the Level-4 blocks and the v1 uncorrected extraction are left "
            "exactly as they are; this is a separate authenticated artifact"),
        "decoder_dir": a.decoder_dir,
        "decoder_status_by_matrix": decoder_status,
        "matrices_refused": refused,
        "sources_not_harmonized": True,
        "supertype_is_a_column_not_a_filter": True,
        "training_authorized": False,
        "protected_outcomes_opened": False,
        "smoke_test_operator_limit": a.limit_operators or None,
        "only_operators": a.only_operators or None,
        "partial_run": partial_run,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    with open(os.path.join(a.out_dir, "FULL104_MYELOID_R8_PANEL_EXTRACTION_V1.json"),
              "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"\n  nuclei extracted   {len(all_recs):,}")
    print(f"  blocks read        {tot_read:,} (all SHA-256 verified)")
    print(f"  blocks skipped     {tot_skip:,}")
    print(f"  identity closure   {identity}")
    print(f"\nwrote {a.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
