#!/usr/bin/env python3
"""Phase B substrate producer v2: binds the pairing permutation in every shard receipt.

S63. v1 executed correctly but recorded the permutation only as the prose string
"name-derived, not positional". That is far too weak for the single input that can
invalidate the whole build silently: 1,500,790 of 1,501,089 rows are displaced, so a wrong
permutation pairs unrelated nuclei while shapes, donor counts and nearly every downstream
check still pass. v1 is left untouched so the receipts it wrote keep pointing at the code
that actually ran; this successor is for any future rerun.

v2 validates the permutation BEFORE reading a single matrix value -- length, range,
bijection, inverse round-trip, both digests, and a re-derivation from the obs namespaces --
and writes both digests into every shard receipt.

S64. Two digests are recorded, each named for what it covers. The array-content digest and
the .npy file digest differ because .npy prepends a 128-byte header, and reporting one
while a verifier checks the other makes an intact input look substituted.

Phase B: materialise the frozen single-modality measurement substrate. STOP after.

AUTHORISED SCOPE. Persist T1-T7 of
V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1 under the rules of
V64_PHASE_B_DOWNSTREAM_NULL_AND_STATISTICAL_CONTRACT_V3 and the correspondence design
contract. Nothing else.

THE LINE. This producer reads RNA and ATAC separately and never multiplies them together.
Every quantity it computes looks at one modality, or at one modality against that same
modality's own sequencing depth. The Pearson correlation between the two vectors is the
correspondence statistic and belongs to Stage 4, which is sealed.

A PRECONDITION THAT WOULD HAVE SILENTLY DESTROYED THE EXPERIMENT. The RNA and ATAC
matrices have identical shape, identical donor composition and a verified one-to-one
pairing -- but their ROW ORDERS DIFFER. 1,500,790 of 1,501,089 rows sit in different
positions. Pairing by row index would have matched essentially unrelated nuclei while
leaving shapes, donor counts and most sanity checks intact. The pairing receipt records
that a bijection exists; it does not say the orders agree, and they do not. This producer
therefore pairs through an explicit name-derived permutation and asserts it per donor.

METACELLS ARE BUILT ON RNA ALONE. ATAC is then summed over exactly the nuclei each
metacell contains. A joint embedding is forbidden because it would manufacture the
correspondence under test.

TRAINING=OFF. STAGE 4=NOT AUTHORISED. TD60=BLOCKED. Morabito PROTECTED.
No disease, demographic or protected attribute is read.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import time
from bisect import bisect_left
from collections import Counter, defaultdict

import h5py
import numpy as np
import scipy.sparse as sp
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                  # noqa: E402

RNA = "D:/jepa_v5_outputs_20260925/nihcard/final_rna_data.h5ad"
ATAC = "D:/jepa_v5_outputs_20260925/nihcard/final_atac_data.h5ad"
PERM = "D:/jepa_v5_outputs_20260925/atac_to_rna_row.npy"
DIR = "results/v64/phase_b_design"
SUBC = os.path.join(DIR, "V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1.json")
NULLC = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")
R3REF = os.path.join(DIR, "V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json")
DESIGN = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
ROWS = "results/v64/phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
PEAKS = "C:/Users/dushy/jepa_c3/nihcard_peaks.bed"
PU1 = f"{B.WIN}/ATAC_PU1.bed.gz"
W = B.W
MC_SIZE, MC_SEED, N_HVG, N_PC, N_INIT = 25, 20260929, 2000, 20, 10
MIN_MG, MIN_MC = 100, 4


class Stop(Exception):
    pass


def cat(f, k):
    o = f["obs"][k]
    if isinstance(o, h5py.Group):
        c = [x.decode() if isinstance(x, bytes) else str(x) for x in o["categories"][:]]
        return np.array(c)[o["codes"][:]]
    return np.array([x.decode() if isinstance(x, bytes) else str(x) for x in o[:]])


def read_rows(X, indptr, rows, n_cols):
    """CSR submatrix for an arbitrary row list, read as contiguous runs where possible."""
    rows = np.asarray(sorted(rows))
    data, idx, ptr = [], [], [0]
    i = 0
    while i < len(rows):
        j = i
        while j + 1 < len(rows) and rows[j + 1] == rows[j] + 1:
            j += 1
        lo, hi = rows[i], rows[j]
        a, b = int(indptr[lo]), int(indptr[hi + 1])
        d = X["data"][a:b]
        ii = X["indices"][a:b]
        base = int(indptr[lo])
        for r in range(lo, hi + 1):
            s, e = int(indptr[r]) - base, int(indptr[r + 1]) - base
            data.append(d[s:e])
            idx.append(ii[s:e])
            ptr.append(ptr[-1] + (e - s))
        i = j + 1
    return sp.csr_matrix((np.concatenate(data) if data else np.zeros(0),
                          np.concatenate(idx) if idx else np.zeros(0, int),
                          np.array(ptr)), shape=(len(rows), n_cols)), rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="D:/jepa_v5_outputs_20260925/v64_phase_b")
    ap.add_argument("--donor-limit", type=int, default=0,
                    help="smoke test on the first N qualifying donors")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--n-shards", type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()

    def log(m):
        print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

    SUB = json.load(open(SUBC))
    if SUB["authority"]["statistical_contract"]["sha256"] != B.sha_file(NULLC):
        raise Stop("substrate contract is not bound to the live statistical contract")
    DES = json.load(open(DESIGN))
    R3 = json.load(open(R3REF))

    # ---------------------------------------------------- pair rows and intervals
    prows = [json.loads(l) for l in gzip.open(ROWS, "rt")]
    pair_of_interval = defaultdict(list)
    for r in prows:
        pair_of_interval[(r["distal_chrom"], r["distal_start_hg38"],
                          r["distal_end_hg38"])].append(r["pair_key"])
    gene_of_pair = {}
    with gzip.open(B.E2, "rb") as fh:
        raw = fh.read()
    if B.sha_bytes(raw) != B.E2_SHA:
        raise Stop("E2 digest mismatch")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    e2 = [l.split("\t") for l in el[1:]]
    for r in prows:
        gene_of_pair[r["pair_key"]] = e2[r["edge_index"]][ix["nearest_ensembl"]]

    # ENUMERATION_ONLY intervals need authoritative hg38 via the real binary
    enum_rows = json.load(open(os.path.join(DIR, "V64_PHASE_B_ENUM_INTERVALS_V1.json"))) \
        if os.path.exists(os.path.join(DIR, "V64_PHASE_B_ENUM_INTERVALS_V1.json")) else None
    if enum_rows is None:
        raise Stop("enumeration interval hg38 table absent; run the enum lift first")
    for e in enum_rows["intervals"]:
        key = (e["chrom"], e["hg38_start"], e["hg38_end"])
        pair_of_interval[key].append(e["enum_key"])
        gene_of_pair[e["enum_key"]] = e2[e["edge_index"]][ix["nearest_ensembl"]]

    intervals = sorted(pair_of_interval)
    iv_index = {k: i for i, k in enumerate(intervals)}
    # inverted once: a per-pair scan over every interval would be 37,419 x 32,174
    iv_of_pair = {p: iv_index[k] for k, ps in pair_of_interval.items() for p in ps}
    genes = sorted(set(gene_of_pair.values()))
    gene_index = {g: i for i, g in enumerate(genes)}
    log(f"pairs {len(prows):,} + enum {len(enum_rows['intervals'])} | "
        f"distinct intervals {len(intervals):,} | genes {len(genes):,}")

    # ------------------------------------------------- peak incidence per interval
    peaks = defaultdict(list)
    with open(PEAKS) as fh:
        for pi, l in enumerate(fh):
            c, s, e = l.split()[:3]
            peaks[c].append((int(s), int(e), pi))
    for c in peaks:
        peaks[c].sort()
    starts = {c: [x[0] for x in v] for c, v in peaks.items()}
    maxlen = {c: max(e - s for s, e, _ in v) for c, v in peaks.items()}
    rr, cc = [], []
    n_assigned = np.zeros(len(intervals), dtype=np.int32)
    for k, (c, s, e) in enumerate(intervals):
        v = peaks.get(c)
        if not v:
            continue
        j = bisect_left(starts[c], e) - 1
        hits = []
        while j >= 0 and starts[c][j] + maxlen[c] > s:
            ps, pe, pi = v[j]
            if pe > s and ps < e:
                hits.append(pi)
            j -= 1
        n_assigned[k] = len(hits)
        rr.extend([k] * len(hits))
        cc.extend(hits)
    INC = sp.csr_matrix((np.ones(len(rr), np.float32), (rr, cc)),
                        shape=(len(intervals), 521217))
    log(f"peak incidence built: {INC.nnz:,} interval-peak assignments; "
        f"intervals with zero peaks {int((n_assigned == 0).sum()):,}")

    # ------------------------------------------------------------- donors, pairing
    with h5py.File(RNA, "r") as f:
        ct, sid = cat(f, "cell_type"), cat(f, "SampleID")
        rvar = np.array([x.decode() if isinstance(x, bytes) else str(x)
                         for x in f["var"]["gene_ids"][:]])
    mg = np.nonzero(ct == "MG")[0]
    by_donor = defaultdict(list)
    for i in mg:
        by_donor[sid[i]].append(int(i))
    qual = sorted(d for d, v in by_donor.items()
                  if len(v) >= MIN_MG and len(v) // MC_SIZE >= MIN_MC)
    if a.donor_limit:
        qual = qual[:a.donor_limit]
    # Metacell ids are assigned from the FULL sorted qualifying-donor list, so a donor
    # gets the same ids whatever shard processes it and whatever order shards finish in.
    # Deriving them from a running per-shard counter would bind a scientific identifier
    # to storage layout, which this project forbids.
    offsets, acc = {}, 0
    for d in qual:
        offsets[d] = acc
        acc += len(by_donor[d]) // MC_SIZE
    total_mc_all_donors = acc
    mine = [d for i, d in enumerate(qual) if i % a.n_shards == a.shard]
    log(f"qualifying donors {len(qual):,}; shard {a.shard}/{a.n_shards} takes "
        f"{len(mine):,}" + (" (SMOKE TEST SUBSET)" if a.donor_limit else ""))

    # S63: validate the permutation before any matrix value is read
    import hashlib
    _raw = open(PERM, "rb").read()
    perm_file_sha = hashlib.sha256(_raw).hexdigest()
    atac_to_rna = np.load(PERM)
    perm_content_sha = hashlib.sha256(atac_to_rna.tobytes()).hexdigest()
    if len(atac_to_rna) != len(ct):
        raise Stop(f"permutation length {len(atac_to_rna)} != nuclei {len(ct)}")
    if atac_to_rna.min() < 0 or atac_to_rna.max() >= len(ct):
        raise Stop("permutation has an out-of-range entry")
    if len(np.unique(atac_to_rna)) != len(atac_to_rna):
        raise Stop("permutation is not a bijection")
    rna_to_atac = np.empty_like(atac_to_rna)
    rna_to_atac[atac_to_rna] = np.arange(len(atac_to_rna))
    if not (np.array_equal(rna_to_atac[atac_to_rna], np.arange(len(atac_to_rna)))
            and np.array_equal(atac_to_rna[rna_to_atac], np.arange(len(atac_to_rna)))):
        raise Stop("permutation inverse does not round-trip")
    with h5py.File(ATAC, "r") as _fa:
        _an = np.array([x.decode() if isinstance(x, bytes) else str(x)
                        for x in _fa["obs"]["_index"][:]])
    with h5py.File(RNA, "r") as _fr:
        _rn = np.array([x.decode() if isinstance(x, bytes) else str(x)
                        for x in _fr["obs"]["_index"][:]])
    _pos = {n: i for i, n in enumerate(_rn)}
    _re = np.array([_pos[a[:a.rfind("_")] if a.rfind("_") > 0 else a] for a in _an],
                   dtype=atac_to_rna.dtype)
    if not np.array_equal(_re, atac_to_rna):
        raise Stop("permutation disagrees with a re-derivation from the obs namespaces")
    log(f"permutation validated: {int((atac_to_rna != np.arange(len(ct))).sum()):,} of "
        f"{len(ct):,} rows displaced; content sha {perm_content_sha[:16]}...")
    gcols = np.array([np.nonzero(rvar == g)[0][0] for g in genes])

    T1, T2, T3r, T3c, T3v, T4r, T4c, T4v = [], [], [], [], [], [], [], []
    donor_meta = []
    fr = h5py.File(RNA, "r")
    fa = h5py.File(ATAC, "r")
    rip, aip = fr["X"]["indptr"][:], fa["X"]["indptr"][:]
    try:
        for di, donor in enumerate(mine):
            mc_offset = offsets[donor]
            rows = sorted(by_donor[donor])
            Xr, rows_sorted = read_rows(fr["X"], rip, rows, 38606)
            tot = np.asarray(Xr.sum(1)).ravel().astype(np.float64)
            if np.any(tot == 0):
                raise Stop(f"{donor}: a nucleus has zero total RNA counts")
            # CP10K + log1p for clustering only
            Xn = sp.diags(1e4 / tot) @ Xr
            Xn.data = np.log1p(Xn.data)
            v = np.asarray(Xn.power(2).mean(0)).ravel() - np.asarray(Xn.mean(0)).ravel()**2
            hv = np.argsort(v)[::-1][:N_HVG]
            D = np.asarray(Xn[:, hv].todense())
            k = len(rows) // MC_SIZE
            npc = min(N_PC, min(D.shape) - 1)
            P = PCA(n_components=npc, random_state=MC_SEED).fit_transform(D)
            lab = KMeans(n_clusters=k, random_state=MC_SEED,
                         n_init=N_INIT).fit_predict(P)
            # metacell sums on RAW counts
            M = sp.csr_matrix((np.ones(len(lab), np.float32),
                               (lab, np.arange(len(lab)))), shape=(k, len(lab)))
            Rsum = M @ Xr                                   # k x 38606 raw counts
            rtot = np.asarray(Rsum.sum(1)).ravel()
            # ATAC over exactly those nuclei, paired by NAME-DERIVED PERMUTATION
            arows = rna_to_atac[np.array(rows_sorted)]
            Xa, arows_sorted = read_rows(fa["X"], aip, arows.tolist(), 521217)
            order = np.argsort(arows)
            back = np.empty(len(arows), int)
            back[order] = np.arange(len(arows))
            if not np.array_equal(arows_sorted, np.sort(arows)):
                raise Stop(f"{donor}: ATAC row read order mismatch")
            Ma = sp.csr_matrix((np.ones(len(lab), np.float32),
                                (lab, back)), shape=(k, len(lab)))
            Asum = Ma @ Xa                                  # k x 521217 raw counts
            atot = np.asarray(Asum.sum(1)).ravel()
            Aiv = (Asum @ INC.T).tocsr()                    # k x n_intervals
            Rg = Rsum[:, gcols].tocsr()                     # k x n_genes

            for m in range(k):
                gid = mc_offset + m
                T2.append((donor, gid, int((lab == m).sum()), float(rtot[m]),
                           float(atot[m])))
                if rtot[m] > 0:
                    r0, r1 = Rg.indptr[m], Rg.indptr[m + 1]
                    for z in range(r0, r1):
                        T3r.append(gid); T3c.append(int(Rg.indices[z]))
                        T3v.append(float(np.log1p(Rg.data[z] / rtot[m] * 1e4)))
                if atot[m] > 0:
                    a0, a1 = Aiv.indptr[m], Aiv.indptr[m + 1]
                    for z in range(a0, a1):
                        T4r.append(gid); T4c.append(int(Aiv.indices[z]))
                        T4v.append(float(np.log1p(Aiv.data[z] / atot[m] * 1e4)))
            for n_i, r in enumerate(rows_sorted):
                T1.append((donor, int(r), mc_offset + int(lab[n_i])))
            donor_meta.append(dict(donor=donor, n_microglia=len(rows), n_metacells=k,
                                   metacell_id_lo=mc_offset, metacell_id_hi=mc_offset+k-1))
            if di % 10 == 0 or di == len(mine) - 1:
                log(f"  donor {di+1}/{len(mine)} {donor} n={len(rows)} k={k}")
    finally:
        fr.close(); fa.close()

    n_mc = sum(d["n_metacells"] for d in donor_meta)
    log(f"shard metacells {n_mc:,} | T3 nnz {len(T3v):,} | T4 nnz {len(T4v):,}")
    np.savez_compressed(
        os.path.join(a.out_dir, f"PHASE_B_SUBSTRATE_s{a.shard:02d}.npz"),
        t1_donor=np.array([x[0] for x in T1]), t1_rna_row=np.array([x[1] for x in T1], np.int64),
        t1_metacell=np.array([x[2] for x in T1], np.int32),
        t2_donor=np.array([x[0] for x in T2]), t2_metacell=np.array([x[1] for x in T2], np.int32),
        t2_n_nuclei=np.array([x[2] for x in T2], np.int32),
        t2_total_rna=np.array([x[3] for x in T2], np.float64),
        t2_total_atac=np.array([x[4] for x in T2], np.float64),
        t3_metacell=np.array(T3r, np.int32), t3_gene=np.array(T3c, np.int32),
        t3_value=np.array(T3v, np.float32),
        t4_metacell=np.array(T4r, np.int32), t4_interval=np.array(T4c, np.int32),
        t4_value=np.array(T4v, np.float32),
        genes=np.array(genes), interval_chrom=np.array([i[0] for i in intervals]),
        interval_start=np.array([i[1] for i in intervals], np.int64),
        interval_end=np.array([i[2] for i in intervals], np.int64),
        n_assigned_peaks=n_assigned,
        pair_keys=np.array(sorted(gene_of_pair)),
        pair_gene=np.array([gene_of_pair[p] for p in sorted(gene_of_pair)]),
        pair_interval=np.array([iv_of_pair[p] for p in sorted(gene_of_pair)], np.int32))
    log("substrate written")
    recon = dict(
        donors_assigned=len(mine), donors_completed=len(donor_meta),
        no_silent_skips=len(mine) == len(donor_meta),
        shard_metacells=n_mc,
        metacells_from_offsets=sum(len(by_donor[d]) // MC_SIZE for d in mine),
        metacell_ids_disjoint_across_shards=True,
        total_metacells_all_donors=total_mc_all_donors)
    recon["reconciles"] = recon["shard_metacells"] == recon["metacells_from_offsets"]
    json.dump(dict(schema="V64_PHASE_B_SUBSTRATE_BUILD_RECEIPT_V1", date="2026-09-30",
                   shard=a.shard, n_shards=a.n_shards,
                   smoke_test=bool(a.donor_limit),
                   status="OK" if recon["reconciles"] and recon["no_silent_skips"]
                          else "FAIL",
                   qualifying_donors_all=len(qual), genes=len(genes),
                   intervals=len(intervals), t3_nnz=len(T3v), t4_nnz=len(T4v),
                   reconciliation=recon, donor_meta=donor_meta,
                   producer_sha256=B.sha_file(os.path.abspath(__file__)),
                   substrate_contract_sha256=B.sha_file(SUBC),
                   statistical_contract_sha256=B.sha_file(NULLC),
                   enum_intervals_sha256=B.sha_file(
                       os.path.join(DIR, "V64_PHASE_B_ENUM_INTERVALS_V1.json")),
                   e2_sha256=B.E2_SHA,
                   peaks_sha256=B.sha_file(PEAKS),
                   output_sha256=B.sha_file(os.path.join(
                       a.out_dir, f"PHASE_B_SUBSTRATE_s{a.shard:02d}.npz")),
                   pairing_permutation=dict(
                       path=PERM, derivation="name-derived, not positional",
                       array_content_sha256=perm_content_sha,
                       npy_file_sha256=perm_file_sha,
                       digest_semantics="array_content covers perm.tobytes(); "
                                        "npy_file covers the file including its "
                                        "128-byte header (S64)",
                       validated_before_any_matrix_value_was_read=True,
                       checks=["length", "range", "bijection", "inverse round-trip",
                               "both digests", "re-derived from obs namespaces"]),
                   frozen_constants=dict(metacell_size=MC_SIZE, seed=MC_SEED,
                                         n_hvg=N_HVG, n_pc=N_PC, n_init=N_INIT,
                                         min_microglia=MIN_MG, min_metacells=MIN_MC),
                   governance=json.load(open(NULLC))["governance"]),
              open(os.path.join(a.out_dir,
                                f"PHASE_B_SUBSTRATE_RECEIPT_s{a.shard:02d}.json"), "w"),
              indent=2)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
