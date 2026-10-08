#!/usr/bin/env python3
"""Outcome-blind candidate-pool census over the FULL104 myeloid nuclei.

THE QUESTION THIS ANSWERS, AND THE ONE IT DOES NOT

  ANSWERS: for each of the twelve frozen partner-gene slots, how many real
  genes in the authenticated 41,238-address space are available and marginally
  comparable, per source and in the prospectively eligible combined population?

  DOES NOT ANSWER: whether any of those genes is a technically exchangeable
  sham. The independent counterexample of 2026-09-28 settles that marginal
  matching cannot establish exchangeability. This is a FEASIBILITY census. A
  large pool does not qualify a null; an empty pool does refute one.

WHY THIS IS NOT A SUBSTRATE REGENERATION

  Per-address marginals are streaming accumulators. Each block is read once,
  its CSR rows are mapped through that matrix's authenticated decoder, and the
  entries are folded into fixed-length arrays with np.bincount. No dense
  cell-by-41K matrix is ever built. Peak memory is one block.

THE OUTCOME FIREWALL, ENFORCED BEFORE ANY STATISTIC IS COMPUTED

  FORBIDDEN = 21 program addresses (3 queries + 12 partners + 6 reserved
  readouts) + 8 housekeeping references + 19 nuisance controls = 48 addresses.
  Every one is dropped from the candidate universe before pool sizes are
  computed, and a test asserts the drop actually happened. The six reserved
  readouts are never read as outcomes: their columns contribute to nothing
  except the frozen `total_excluding_29` that the artifact already published.

  SELECTION USES FITTING DONORS ONLY. The split is declared here, in code,
  before any pool size exists, and is a pure function of the donor identity:

      h = sha256(f"{source}|{donor_id}") -> first 8 bytes, big-endian
      rank donors within each source by h ascending
      lowest ceil(n/3) -> EVALUATION, remainder -> FITTING

  Ranking within source, rather than `h % 3`, guarantees exactly one third
  evaluation per source even at NPH52's 16 donors. Sources are never pooled,
  per frozen protocol v7.

STRUCTURAL AVAILABILITY IS NOT ZERO

  HVS/SEA-AD: an address is available in a matrix iff that matrix's verified
  decoder maps it. This is the authoritative structural axis.

  NPH52: identity-verified (block column == true address, agreement 1.0000),
  so it has no decoder file. Its availability is read from the AUTHENTICATED
  FEATURE AXIS in the stage81a2r provenance table, filtered to the MG object -
  the same table the verifier checked against the object's own rownames at
  agreement 1.0000.

  An earlier version used the union of columns physically observed with a
  nonzero count. That is a lower bound and a materially wrong one: the
  authenticated axis holds 31,621 distinct addresses while only 28,099 are ever
  observed nonzero in myeloid nuclei, so 3,522 genuinely measured genes were
  being treated as unmeasured. A measured gene may legitimately be zero in
  every sampled nucleus, and calling that "absent" is the same confusion
  between structural absence and observed zero that this mask exists to
  prevent - just pointing the other way.

DEPTH REFERENCE

  `D = total_excluding_29`, taken from the published corrected artifact. That
  is the artifact's own frozen reference definition. The pair-specific
  `D(P,Q)` is NOT used and NOT altered here: this is a screen, not the test,
  and the estimand is untouched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

N_ADDR = 41238

# ---- the frozen forbidden set ------------------------------------------------
R8_ADDR = {
    "APOE_LIPID": {"query": 6186, "panel": [6188, 11425, 7194, 2044],
                   "readout": [4748, 13734]},
    "P2RY12_HOMEOSTATIC": {"query": 12469, "panel": [15109, 12239, 12995, 13365],
                           "readout": [2810, 14980]},
    "HLA_DRA_ANTIGEN": {"query": 18511, "panel": [392, 23673, 18500, 20496],
                        "readout": [26659, 10846]},
}
PARTNER_NAMES = {
    6188: "APOC1", 11425: "ABCA1", 7194: "GPNMB", 2044: "TREM2",
    15109: "TMEM119", 12239: "CX3CR1", 12995: "GPR34", 13365: "C1QA",
    392: "CD74", 23673: "HLA-DPA1", 18500: "HLA-DMA", 20496: "IFI30",
}
HOUSEKEEPING = [1817, 9924, 2628, 11587, 16586, 8192, 12595, 1225]
AMBIENT = [6584, 1015, 11973, 5370, 17102, 12238, 6359, 13053, 3762, 2690]
MYELOID = [18579, 12586, 966, 10205, 305, 10670]
MITO = [17359, 17409, 17415]
NUISANCE = AMBIENT + MYELOID + MITO                       # 19, not 20

BAN_29 = sorted({p["query"] for p in R8_ADDR.values()}
                | {a for p in R8_ADDR.values() for a in p["panel"]}
                | {a for p in R8_ADDR.values() for a in p["readout"]}
                | set(HOUSEKEEPING))
FORBIDDEN = sorted(set(BAN_29) | set(NUISANCE))
assert len(BAN_29) == 29 and len(NUISANCE) == 19 and len(FORBIDDEN) == 48

RESERVED_READOUTS = sorted({a for p in R8_ADDR.values() for a in p["readout"]})

# PROTECTED: dropped from the CSR entries BEFORE normalisation and before any
# accumulator sees them. Excluding them only at selection time, as the first
# version did, still computes and persists their mean, detection, Fano and both
# correlations - which spends the hold-out no matter what happens downstream.
# The other 42 forbidden addresses stay accumulated: they are already published
# in the 29-address artifact and the cross-path audit needs them.
PROTECTED = np.zeros(N_ADDR, dtype=bool)
PROTECTED[np.asarray(RESERVED_READOUTS)] = True
NOT_COMPUTED = -1                      # sentinel for n_available, never 0

IDENTITY_VERIFIED = {
    "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs":
        "NPH52_FEATURE_AXIS_VERIFIED_ZERO_BASED",
}

# ---- matching tiers, declared before any pool size is computed ---------------
TIERS = [
    ("T1_mean",                 ("mean",)),
    ("T2_mean_detect",          ("mean", "detect")),
    ("T3_mean_detect_fano",     ("mean", "detect", "fano")),
    ("T4_plus_depth",           ("mean", "detect", "fano", "depth")),
    ("T5_all_five",             ("mean", "detect", "fano", "depth", "hk")),
]
MEAN_RATIO_LO, MEAN_RATIO_HI = 0.80, 1.25
DETECT_ABS = 0.10
FANO_FACTOR = 1.5
DEPTH_ABS = 0.15
HK_ABS = 0.15


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def donor_hash(source, donor_id):
    d = hashlib.sha256(f"{source}|{donor_id}".encode("utf-8")).digest()
    return int.from_bytes(d[:8], "big")


def split_donors(pairs):
    """pairs: iterable of (source, donor_id). Returns dict -> 'FIT' | 'EVAL'."""
    by_source = defaultdict(list)
    for s, d in set(pairs):
        by_source[s].append(d)
    assign = {}
    for s, donors in by_source.items():
        ranked = sorted(donors, key=lambda d: (donor_hash(s, d), str(d)))
        n_eval = math.ceil(len(ranked) / 3)
        for i, d in enumerate(ranked):
            assign[(s, d)] = "EVAL" if i < n_eval else "FIT"
    return assign


class Acc:
    """Streaming per-address accumulators for one source."""

    def __init__(self):
        z = lambda: np.zeros(N_ADDR, dtype=np.float64)
        self.nnz = np.zeros(N_ADDR, dtype=np.int64)
        self.sum_c = z(); self.sum_c2 = z()
        self.sum_y = z(); self.sum_y2 = z()
        self.sum_ylogD = z(); self.sum_yhk = z()
        self.n_cells = 0
        # Per-MATRIX cell-level sums. An address available in only some matrices
        # must be compared against the covariate moments of exactly those
        # matrices' cells; a source-wide sum would use the wrong denominator.
        self.per_matrix = defaultdict(
            lambda: {"n": 0, "sum_logD": 0.0, "sum_logD2": 0.0,
                     "sum_hk": 0.0, "sum_hk2": 0.0})

    def add_cells(self, matrix_id, n, logD, hk):
        self.n_cells += n
        r = self.per_matrix[matrix_id]
        r["n"] += n
        r["sum_logD"] += float(logD.sum()); r["sum_logD2"] += float((logD ** 2).sum())
        r["sum_hk"] += float(hk.sum()); r["sum_hk2"] += float((hk ** 2).sum())

    def add_entries(self, addr, cnt, y, logD_rep, hk_rep):
        self.nnz += np.bincount(addr, minlength=N_ADDR).astype(np.int64)
        self.sum_c += np.bincount(addr, weights=cnt, minlength=N_ADDR)
        self.sum_c2 += np.bincount(addr, weights=cnt * cnt, minlength=N_ADDR)
        self.sum_y += np.bincount(addr, weights=y, minlength=N_ADDR)
        self.sum_y2 += np.bincount(addr, weights=y * y, minlength=N_ADDR)
        self.sum_ylogD += np.bincount(addr, weights=y * logD_rep, minlength=N_ADDR)
        self.sum_yhk += np.bincount(addr, weights=y * hk_rep, minlength=N_ADDR)


def finish(acc, avail_by_matrix):
    """Per-address marginals. A zero count is a real zero; an UNAVAILABLE
    address gets NaN and is never compared.

    Covariate moments are summed over exactly the matrices in which each
    address is available, so a partially-available address is compared against
    its own cells and not the whole source.
    """
    n = np.zeros(N_ADDR, dtype=np.float64)
    sum_logD = np.zeros(N_ADDR); sum_logD2 = np.zeros(N_ADDR)
    sum_hk = np.zeros(N_ADDR); sum_hk2 = np.zeros(N_ADDR)
    for mid, r in acc.per_matrix.items():
        m = avail_by_matrix[mid]
        n[m] += r["n"]
        sum_logD[m] += r["sum_logD"]; sum_logD2[m] += r["sum_logD2"]
        sum_hk[m] += r["sum_hk"]; sum_hk2[m] += r["sum_hk2"]
    ok = n > 0
    out = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        safe = np.maximum(n, 1)
        mean = np.where(ok, acc.sum_c / safe, np.nan)
        var = np.where(ok, acc.sum_c2 / safe - mean ** 2, np.nan)
        out["mean"] = mean
        out["detect"] = np.where(ok, acc.nnz / safe, np.nan)
        out["fano"] = np.where(ok & (mean > 0), var / np.maximum(mean, 1e-12), np.nan)

        def pearson(sum_xy, sum_z, sum_z2):
            # x = normalised expression, which is exactly 0 at every zero count,
            # so the sparse sums are complete over the available cells.
            cov = sum_xy - acc.sum_y * sum_z / safe
            vx = acc.sum_y2 - acc.sum_y ** 2 / safe
            vz = sum_z2 - sum_z ** 2 / safe
            d = np.sqrt(np.maximum(vx, 0) * np.maximum(vz, 0))
            return np.where(ok & (d > 0), cov / np.where(d > 0, d, 1), np.nan)

        out["depth"] = pearson(acc.sum_ylogD, sum_logD, sum_logD2)
        out["hk"] = pearson(acc.sum_yhk, sum_hk, sum_hk2)
    out["n_available"] = n.astype(np.int64)
    out["nnz"] = acc.nnz.copy()
    return out


def nph52_authenticated_axis(provenance_csv, dataset_id):
    """The measurable address set for one NPH52 object, from provenance.

    Refuses rather than falling back: a census that silently substitutes
    observed nonzeros for a structural axis produces availability that is
    wrong in a direction nobody checks.
    """
    import pandas as pd
    df = pd.read_csv(provenance_csv, low_memory=False,
                     usecols=["molecular_address_index", "source_dataset_id"])
    sub = df[df.source_dataset_id == dataset_id]
    if sub.empty:
        raise SystemExit(f"REFUSE_NO_NPH52_PROVENANCE for {dataset_id!r}")
    a = sub.molecular_address_index.astype(np.int64).to_numpy()
    a = a[(a >= 0) & (a < N_ADDR)]
    m = np.zeros(N_ADDR, dtype=bool)
    m[a] = True
    return m, int(len(sub)), int(m.sum())


def build_col2addr(decoder_dir, matrix_id):
    """-> (lookup array over block columns, status, n_mapped) or (None, why, 0)."""
    if matrix_id in IDENTITY_VERIFIED:
        return "IDENTITY", IDENTITY_VERIFIED[matrix_id], -1
    stem = matrix_id.replace("::", "__").replace("/", "_")
    p = os.path.join(decoder_dir, f"decoder_{stem}.npz")
    if not os.path.exists(p):
        return None, "NO_VERIFIED_DECODER", 0
    z = np.load(p)
    lut = np.full(N_ADDR, -1, dtype=np.int64)
    bc = z["block_column"].astype(np.int64)
    ta = z["true_address"].astype(np.int64)
    keep = (bc >= 0) & (bc < N_ADDR)
    lut[bc[keep]] = ta[keep]
    return lut, "DECODER_VERIFIED", int(keep.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l4-root", required=True)
    ap.add_argument("--decoder-dir", required=True)
    ap.add_argument("--artifact", required=True,
                    help="FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz")
    ap.add_argument("--nph52-provenance", required=True,
                    help="stage81a2r_foundation_molecular_address_source_"
                         "provenance_candidate.csv.gz - the authenticated "
                         "feature axis. Required: observed nonzeros are not a "
                         "structural axis.")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-blocks", type=int, default=0,
                    help="smoke only; a truncated run is marked PARTIAL and "
                         "may not be used as a census")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    started = time.time()

    # ---- authenticated cell inventory from the published artifact
    z = np.load(a.artifact, allow_pickle=True)
    cell_ids = z["cell_id"].astype(str)
    sources = z["source"].astype(str)
    donors = z["donor_id"].astype(str)
    D_all = z["total_excluding_29"].astype(np.float64)
    counts29 = z["counts"]
    cols29 = list(z["address_columns"])
    avail29 = z["address_available"]
    hk_cols = [cols29.index(h) for h in HOUSEKEEPING]
    hk_score = np.log1p(np.where(avail29[:, hk_cols], counts29[:, hk_cols], 0)
                        .sum(1) * 1e4 / np.maximum(D_all, 1))

    assign = split_donors(zip(sources, donors))
    is_fit = np.array([assign[(s, d)] == "FIT" for s, d in zip(sources, donors)])
    idx_of = {c: i for i, c in enumerate(cell_ids)}

    fit_donor_list = sorted({f"{s}|{d}" for s, d, f
                             in zip(sources, donors, is_fit) if f})
    eval_donor_list = sorted({f"{s}|{d}" for s, d, f
                              in zip(sources, donors, is_fit) if not f})
    print(f"donors: {len(fit_donor_list)} FIT / {len(eval_donor_list)} EVAL")
    print(f"fitting nuclei: {int(is_fit.sum())} of {len(cell_ids)}")

    # ---- stream the blocks
    man = os.path.join(a.l4_root, "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv")
    with open(man, newline="", encoding="utf-8") as fh:
        blocks = list(csv.DictReader(fh))
    if a.max_blocks:
        blocks = blocks[:a.max_blocks]

    accs = defaultdict(Acc)
    matrix_status = {}
    avail_by_matrix = {}
    nph_cols_seen = {}
    read_blocks = skipped = 0
    n_protected_dropped = 0
    donor_mismatch = []
    n_entries = 0

    for bi, b in enumerate(blocks):
        mid = b["matrix_id"]
        mp = os.path.join(a.l4_root, b["meta_path"])
        with open(mp, "rb") as fh:
            mb = fh.read()
        if sha_bytes(mb) != b["meta_sha256"]:
            raise SystemExit(f"META_SHA_MISMATCH {b['block_key']}")
        meta = list(csv.DictReader(io.StringIO(mb.decode())))
        sel = [(i, m) for i, m in enumerate(meta)
               if m["canonical_cell_id"] in idx_of
               and is_fit[idx_of[m["canonical_cell_id"]]]]
        if not sel:
            skipped += 1
            continue

        # A decoder is required only for a block that actually contributes
        # fitting nuclei. The Level-4 manifest spans every matrix in FULL104,
        # including many with no myeloid cells at all; demanding a decoder for
        # those would refuse the run over matrices this census never reads.
        if mid not in matrix_status:
            lut, status, nmap = build_col2addr(a.decoder_dir, mid)
            if lut is None:
                raise SystemExit(f"REFUSE_UNDECODABLE_MATRIX {mid}: {status}")
            matrix_status[mid] = (lut, status, nmap)
        lut, status, _ = matrix_status[mid]

        cp = os.path.join(a.l4_root, b["counts_path"])
        with open(cp, "rb") as fh:
            cb = fh.read()
        if sha_bytes(cb) != b["counts_sha256"]:
            raise SystemExit(f"COUNTS_SHA_MISMATCH {b['block_key']}")
        zz = np.load(io.BytesIO(cb))
        indptr, indices, data = zz["indptr"], zz["indices"], zz["data"]
        read_blocks += 1

        rows, cols, dats = [], [], []
        gi = []
        for i, m in sel:
            g = idx_of[m["canonical_cell_id"]]
            if str(m["donor_id"]) != str(donors[g]):
                # FAIL CLOSED. A block whose metadata disagrees with the
                # authenticated donor identity means the join is wrong, and a
                # census that records the disagreement and carries on still
                # writes OUTCOME_BLIND_CANDIDATE_POOL_CENSUS over bad data.
                raise SystemExit(
                    f"REFUSE_DONOR_IDENTITY_MISMATCH {m['canonical_cell_id']} "
                    f"in {b['block_key']}: block meta says {m['donor_id']!r}, "
                    f"authenticated metadata says {donors[g]!r}")
            lo, hi = int(indptr[i]), int(indptr[i + 1])
            cols.append(indices[lo:hi]); dats.append(data[lo:hi])
            rows.append(hi - lo); gi.append(g)
        gi = np.asarray(gi)
        allc = np.concatenate(cols).astype(np.int64)
        alld = np.concatenate(dats).astype(np.float64)
        rep = np.repeat(np.arange(len(gi)), np.asarray(rows))

        src = b["source"]
        acc = accs[src]
        Dg = D_all[gi]; logD = np.log(np.maximum(Dg, 1.0)); hk = hk_score[gi]

        if isinstance(lut, str):                      # NPH52 identity axis
            addr = allc
            ok = (addr >= 0) & (addr < N_ADDR)
            nph_cols_seen.setdefault(mid, set()).update(
                np.unique(addr[ok]).tolist())
        else:
            addr = lut[np.clip(allc, 0, N_ADDR - 1)]
            ok = addr >= 0
            if mid not in avail_by_matrix:
                # Availability is a property of the ADDRESS, not of the block
                # column. `lut` is indexed by column and HOLDS the address, so
                # `lut >= 0` is a column mask and marks the wrong entries. The
                # SEA-AD decoders are complete permutations - identity fraction
                # 0.0000 - so using the column mask mislabelled 1,469 addresses
                # in each direction and reported CD74 as unmeasured.
                am = np.zeros(N_ADDR, dtype=bool)
                mapped = lut[lut >= 0]
                am[mapped[(mapped >= 0) & (mapped < N_ADDR)]] = True
                avail_by_matrix[mid] = am

        n_unmapped_this_block = int((~ok).sum())
        ok &= ~PROTECTED[np.clip(addr, 0, N_ADDR - 1)]
        addr = addr[ok]; cnt = alld[ok]; r = rep[ok]
        n_protected_dropped += int((~ok).sum()) - int(n_unmapped_this_block)
        y = np.log1p(cnt * 1e4 / np.maximum(Dg[r], 1.0))
        acc.add_entries(addr, cnt, y, logD[r], hk[r])
        n_entries += int(ok.sum())
        acc.add_cells(mid, len(gi), logD, hk)

        if bi % 500 == 0:
            print(f"  block {bi}/{len(blocks)}  read={read_blocks} "
                  f"entries={n_entries/1e6:.1f}M  {time.time()-started:.0f}s",
                  flush=True)

    # NPH52 availability: the AUTHENTICATED feature axis, not observed nonzeros
    nph_axis_info = {}
    for mid in nph_cols_seen:
        dsid = mid.replace("NPH52::matrix::", "NPH52::")
        m, rows, n_addr = nph52_authenticated_axis(a.nph52_provenance, dsid)
        avail_by_matrix[mid] = m
        nph_axis_info[mid] = {
            "provenance_rows": rows, "authenticated_addresses": n_addr,
            "observed_nonzero_union": len(nph_cols_seen[mid]),
            "measured_but_never_nonzero": n_addr - len(
                set(nph_cols_seen[mid]) & set(np.flatnonzero(m).tolist()))}

    seen_total = sum(a.n_cells for a in accs.values())
    if seen_total != int(is_fit.sum()):
        raise SystemExit(
            f"REFUSE_INCOMPLETE_CENSUS: folded {seen_total} fitting nuclei but "
            f"{int(is_fit.sum())} were expected. Exactly-once over the declared "
            "population is a completion requirement, not a diagnostic.")

    stats = {src: finish(acc, avail_by_matrix) for src, acc in accs.items()}
    # Belt and braces: even though no protected entry ever reached an
    # accumulator, stamp an explicit NOT_COMPUTED sentinel rather than leaving a
    # value that could be mistaken for a measurement. Never zero - a zero reads
    # as "measured and absent", which is the error this project keeps making.
    for src, d in stats.items():
        for f in ("mean", "detect", "fano", "depth", "hk"):
            d[f][PROTECTED] = np.nan
        d["n_available"][PROTECTED] = NOT_COMPUTED
        d["nnz"][PROTECTED] = NOT_COMPUTED
    np.savez_compressed(
        os.path.join(a.out_dir, "FULL104_CANDIDATE_POOL_CENSUS_V1.npz"),
        **{f"{s}__{k}": v for s, d in stats.items() for k, v in d.items()},
        sources=np.array(sorted(stats)), forbidden=np.array(FORBIDDEN))

    receipt = {
        "schema": "V5_FULL104_CANDIDATE_POOL_CENSUS_V1",
        "status": ("PARTIAL_SMOKE_NOT_A_CENSUS" if a.max_blocks
                   else "OUTCOME_BLIND_CANDIDATE_POOL_CENSUS"),
        "blocks_total": len(blocks), "blocks_read": read_blocks,
        "blocks_skipped_no_fitting_nuclei": skipped,
        "nonzero_entries_folded": n_entries,
        "fitting_nuclei": int(is_fit.sum()),
        "evaluation_nuclei_excluded": int((~is_fit).sum()),
        "fitting_donors": fit_donor_list,
        "evaluation_donors_never_used": eval_donor_list,
        "donor_split_rule": ("sha256('<source>|<donor_id>')[:8] big-endian; "
                             "rank ascending within source; lowest ceil(n/3) "
                             "-> EVAL. Sources never pooled."),
        "depth_reference": "total_excluding_29 from the published artifact",
        "forbidden_addresses": FORBIDDEN,
        "reserved_readouts_never_read_as_outcomes": RESERVED_READOUTS,
        "protected_entries_dropped_before_accumulation": n_protected_dropped,
        "protected_statistics": "NOT_COMPUTED",
        "protected_sentinel": NOT_COMPUTED,
        "matrix_decoder_status": {k: v[1] for k, v in matrix_status.items()},
        "matrix_decoder_mapped": {k: v[2] for k, v in matrix_status.items()},
        "nph52_availability_source": "AUTHENTICATED_PROVENANCE_FEATURE_AXIS",
        "nph52_axis": nph_axis_info,
        "donor_id_mismatches": "FAIL_CLOSED_NONE_TOLERATED",
        "fitting_nuclei_folded_exactly_once": seen_total,
        "per_source_available_addresses": {
            s: int((d["n_available"] > 0).sum()) for s, d in stats.items()},
        "training_authorized": False,
        "protected_outcomes_opened": False,
        "elapsed_sec": round(time.time() - started, 1),
        "producer_sha256": sha_file(os.path.abspath(__file__)),
        "artifact_sha256": sha_file(a.artifact),
    }
    with open(os.path.join(a.out_dir,
                           "FULL104_CANDIDATE_POOL_CENSUS_V1.json"), "w") as fh:
        json.dump(receipt, fh, indent=2)
    print(json.dumps({k: v for k, v in receipt.items()
                      if k not in ("fitting_donors",
                                   "evaluation_donors_never_used",
                                   "forbidden_addresses")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
