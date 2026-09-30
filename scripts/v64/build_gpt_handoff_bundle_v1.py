#!/usr/bin/env python3
"""Compact, auditable extracts for the parallel GPT lane. Not a giant archive.

Contents
  1 NIH-CARD paired RNA+ATAC: donor-preserving subset of PAIRED nuclei, with the exact
    RNA<->ATAC pairing key, donor, cell type, RNA counts, ATAC counts, and full feature
    coordinates for both modalities.
  2 FULL104 RNA: donor/source/operator-stratified subset of the authenticated
    foundation discovery corpus (log1p10k), with the 42-operator backbone address list.
  3 Promoter/TSS bridge: Nott promoter coordinates with gene mappings, the frozen E2
    edge table, and the hg19<->hg38 chain/liftOver digests.
  4 Claude exact-sampler / Phase-A output: added when it exists.

EXPOSURE NOTICE, STATED NOT BURIED. Item 1 contains RNA counts and ATAC counts for the
SAME nuclei plus coordinates for both feature spaces. Nothing in this bundle computes
a correspondence, but the bundle is sufficient to compute one. Doing so outside the
frozen NIH-CARD correspondence design would open Stage 4, which is NOT AUTHORISED. The
extract is provided because it was requested for design smoke-testing; the governance
consequence is recorded here so the decision is informed rather than implicit.

Everything is coordinates, counts and identifiers. No disease, demographic or
protected attribute is included: the NIH-CARD obs columns Age, Sex, PMI, Ancestry,
Race, Ethnicity, Brain_bank and batch are deliberately excluded.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import zipfile
from collections import Counter, defaultdict

import numpy as np

NIH_RNA = "D:/jepa_v5_outputs_20260925/nihcard/final_rna_data.h5ad"
NIH_ATAC = "D:/jepa_v5_outputs_20260925/nihcard/final_atac_data.h5ad"
FOUND = "D:/Jepa project/exports/foundation_corpus_discovery_v1"
WIN = "C:/Users/dushy/jepa_c3"
E2 = "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz"
S5 = "C:/Users/dushy/Downloads/NIHMS1066836-supplement-Table_S5.xlsx"

SEED = 20260930
N_DONORS = 24
N_PER_DONOR = 90
N_GENES = 4000
N_PEAKS = 12000
N_FULL104_CELLS = 6000


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage", default="D:/jepa_v5_outputs_20260925/gpt_bundle")
    a = ap.parse_args()
    os.makedirs(a.stage, exist_ok=True)
    rng = np.random.default_rng(SEED)
    man = {"schema": "V64_GPT_HANDOFF_BUNDLE_V1", "date": "2026-09-30",
           "seed": SEED, "files": {}, "provenance": {}, "notes": {}}

    import anndata
    rna = anndata.read_h5ad(NIH_RNA, backed="r")
    atac = anndata.read_h5ad(NIH_ATAC, backed="r")

    # ---- exact pairing key: ATAC obs_name minus one trailing _<sample_id>
    an = np.asarray(atac.obs_names, dtype=object)
    sid = atac.obs["sample_id"].astype(str).values
    stripped = np.array([n[: -(len(s) + 1)] for n, s in zip(an, sid)], dtype=object)
    rn = np.asarray(rna.obs_names, dtype=object)
    ridx = {n: i for i, n in enumerate(rn)}
    a2r = np.array([ridx[x] for x in stripped], dtype=np.int64)
    assert len(set(a2r.tolist())) == len(rn), "pairing is not a bijection"

    ct = rna.obs["cell_type"].astype(str).values
    don = rna.obs["SampleID"].astype(str).values
    mg_atac = np.flatnonzero(ct[a2r] == "MG")
    per = defaultdict(list)
    for i in mg_atac:
        per[don[a2r[i]]].append(i)
    donors = sorted([d for d, v in per.items() if len(v) >= N_PER_DONOR])
    donors = [donors[i] for i in rng.choice(len(donors), min(N_DONORS, len(donors)),
                                            replace=False)]
    sel_atac = []
    for d in sorted(donors):
        v = np.array(sorted(per[d]))
        sel_atac.extend(v[rng.choice(len(v), N_PER_DONOR, replace=False)].tolist())
    sel_atac = np.array(sorted(sel_atac))
    sel_rna = a2r[sel_atac]
    print(f"paired nuclei selected: {len(sel_atac)} over {len(donors)} donors")

    gid = np.array([str(g) for g in rna.var["gene_ids"].values])
    gsym = np.array([str(g) for g in rna.var_names])
    pnames = np.array([str(p) for p in atac.var_names])
    gsel = np.sort(rng.choice(rna.n_vars, N_GENES, replace=False))
    psel = np.sort(rng.choice(atac.n_vars, N_PEAKS, replace=False))

    # Block-wise gather. A contiguous slab read over scattered rows would pull
    # essentially the whole backed matrix into memory; this reads only what is needed.
    import scipy.sparse as _sp

    def gather(X, rows, cols, label):
        rows = np.asarray(rows)
        order = np.argsort(rows)
        out = [None] * len(rows)
        B = 20000
        for lo in range(0, int(rows.max()) + 1, B):
            hi = min(lo + B, int(rows.max()) + 1)
            sel = order[(rows[order] >= lo) & (rows[order] < hi)]
            if len(sel) == 0:
                continue
            blk = X[lo:hi]
            blk = blk.tocsr() if hasattr(blk, "tocsr") else _sp.csr_matrix(blk)
            loc = rows[sel] - lo
            sub = blk[loc][:, cols]
            for j, k in enumerate(sel):
                out[k] = sub[j]
            print(f"  [{label}] {sum(1 for o in out if o is not None)}/{len(rows)}",
                  flush=True)
        return _sp.vstack(out).tocoo()

    Xr = gather(rna.X, sel_rna, gsel, "RNA")
    Xa = gather(atac.X, sel_atac, psel, "ATAC")
    f = os.path.join(a.stage, "nihcard_paired_subset.npz")
    np.savez_compressed(
        f,
        rna_row=Xr.row.astype(np.int32), rna_col=Xr.col.astype(np.int32),
        rna_val=Xr.data.astype(np.int32),
        atac_row=Xa.row.astype(np.int32), atac_col=Xa.col.astype(np.int32),
        atac_val=Xa.data.astype(np.int32),
        n_nuclei=np.int64(len(sel_atac)), n_genes=np.int64(len(gsel)),
        n_peaks=np.int64(len(psel)),
        gene_ids=gid[gsel], gene_symbols=gsym[gsel], peak_names=pnames[psel],
        pairing_rna_obs_name=rn[sel_rna], pairing_atac_obs_name=an[sel_atac],
        donor_id=don[sel_rna], cell_type=ct[sel_rna])
    man["files"]["nihcard_paired_subset.npz"] = {
        "sha256": sha(f), "bytes": os.path.getsize(f),
        "nuclei": int(len(sel_atac)), "donors": len(donors),
        "genes": int(len(gsel)), "peaks": int(len(psel)),
        "rna_values": "raw integer counts from .X (count-like uint16 slot)",
        "atac_values": "raw integer counts from .X",
        "pairing_key": "ATAC obs_name with one trailing _<sample_id> removed equals RNA obs_name; both spellings included per nucleus",
        "layout": "COO triplets; row indexes the nucleus, col indexes gene/peak within this subset"}

    # ---- FULL104 stratified subset
    import scipy.sparse as sp
    M = sp.load_npz(os.path.join(FOUND, "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz")) \
        if os.path.exists(os.path.join(FOUND, "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz")) else None
    rows = list(csv.DictReader(open(os.path.join(FOUND, "FOUNDATION_DISCOVERY_CELL_GEOMETRY.csv"))))
    strata = defaultdict(list)
    for i, r in enumerate(rows):
        strata[(r["source"], r["donor_id"], r["operator_index"])].append(i)
    keys = sorted(strata)
    take = []
    k = 0
    while len(take) < N_FULL104_CELLS and k < 200:
        for key in keys:
            v = strata[key]
            if k < len(v):
                take.append(v[k])
            if len(take) >= N_FULL104_CELLS:
                break
        k += 1
    take = np.array(sorted(take))
    addr = [r for r in csv.DictReader(open(os.path.join(FOUND, "FOUNDATION_GEOMETRY_SELECTED_ADDRESSES.csv")))]
    core = np.array([int(r["molecular_address_index"]) for r in addr], dtype=np.int64)
    sub = M[take][:, core].tocoo()
    f2 = os.path.join(a.stage, "full104_discovery_subset.npz")
    np.savez_compressed(
        f2, row=sub.row.astype(np.int32), col=sub.col.astype(np.int32),
        val=sub.data.astype(np.float32),
        n_cells=np.int64(len(take)), n_addresses=np.int64(len(core)),
        backbone_address_index=core,
        cell_donor=np.array([rows[i]["donor_id"] for i in take], dtype=object),
        cell_source=np.array([rows[i]["source"] for i in take], dtype=object),
        cell_operator=np.array([rows[i]["operator_index"] for i in take], dtype=object),
        cell_sample=np.array([rows[i]["sample"] for i in take], dtype=object),
        cell_native_class=np.array([rows[i]["native_class"] for i in take], dtype=object),
        cell_broad_class=np.array([rows[i]["broad_class"] for i in take], dtype=object),
        cell_id=np.array([rows[i]["cell_id"] for i in take], dtype=object))
    man["files"]["full104_discovery_subset.npz"] = {
        "sha256": sha(f2), "bytes": os.path.getsize(f2),
        "cells": int(len(take)),
        "donors": len(set(rows[i]["donor_id"] for i in take)),
        "sources": sorted(set(rows[i]["source"] for i in take)),
        "operators": len(set(rows[i]["operator_index"] for i in take)),
        "addresses": int(len(core)),
        "values": "log1p10k normalised, q-safe; NOT raw counts",
        "stratification": "round-robin over (source, donor, operator) strata, deterministic, seed 20260930",
        "address_universe": "the 17,186 addresses recorded as measured by ALL 42 operators"}

    # ---- promoter/TSS bridge
    import openpyxl
    wb = openpyxl.load_workbook(S5, read_only=True, data_only=True)
    ws = wb["H3K4me3_around_TSS_annotated_pe"]
    rws = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rws)
              if r and any(str(x).strip() == "PeakID" for x in r if x))
    hdr = [str(x).strip() if x is not None else "" for x in rws[hi]]
    col = {k: i for i, k in enumerate(hdr)}
    want = ["Chr", "Start", "End", "Nearest Ensembl", "Gene Name", "Gene Type",
            "PU1_active_promoter", "NeuN_active_promoter", "Olig2_active_promoter",
            "Distance to TSS"]
    f3 = os.path.join(a.stage, "nott_promoter_annotation_hg19.csv.gz")
    n_prom = 0
    with gzip.open(f3, "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(want)
        for r in rws[hi + 1:]:
            if not r or r[col["Chr"]] is None:
                continue
            w.writerow([r[col[k]] if k in col else "" for k in want])
            n_prom += 1
    man["files"]["nott_promoter_annotation_hg19.csv.gz"] = {
        "sha256": sha(f3), "bytes": os.path.getsize(f3), "rows": n_prom,
        "build": "hg19", "source": "Nott Table S5 H3K4me3_around_TSS_annotated_pe",
        "source_sha256": sha(S5)}

    for src, name in [(E2, "e2_edges_hg38_and_hg19.tsv.gz")]:
        dst = os.path.join(a.stage, name)
        with open(src, "rb") as i_, open(dst, "wb") as o_:
            o_.write(i_.read())
        man["files"][name] = {"sha256": sha(dst), "bytes": os.path.getsize(dst),
                              "note": "frozen E2 edge table, 20,709 rows, both builds"}

    man["provenance"] = {
        "nih_card": {"rna_md5": "f628b17aab355f80b912e3c715543cbd",
                     "atac_md5": "b71589e0033e391e2fe97c1ae3928a7f",
                     "zenodo": "10.5281/zenodo.20834804", "licence": "CC-BY-4.0"},
        "liftover_v479_sha256": sha(f"{WIN}/liftOver_v479"),
        "chain_hg19ToHg38_sha256": sha(f"{WIN}/hg19ToHg38.over.chain.gz"),
        "chain_hg38ToHg19_sha256": sha(f"{WIN}/hg38ToHg19.over.chain.gz"),
        "nott_pu1_atac_hg38_sha256": sha(f"{WIN}/ATAC_PU1.bed.gz"),
        "table_s5_terms": "UNKNOWN -- public PMC availability is not a licence grant"}
    man["notes"] = {
        "EXPOSURE": "nihcard_paired_subset.npz contains RNA and ATAC counts for the SAME nuclei plus both feature coordinate spaces. Nothing here computes a correspondence, but the bundle is SUFFICIENT to compute one. Doing that outside the frozen NIH-CARD correspondence design would open Stage 4, which is NOT AUTHORISED.",
        "EXCLUDED_BY_DESIGN": ["Age", "Sex", "PMI", "Ancestry", "Race", "Ethnicity",
                               "Brain_bank", "batch", "disease or protected outcomes"],
        "GENCODE": "NOT PRESENT on this machine and deliberately not downloaded in this pass; the promoter bridge uses the already-authenticated Nott annotation instead",
        "BACKBONE_DENOMINATOR": "17,186 addresses measured by all 42 operators, located in FOUNDATION_GEOMETRY_SELECTED_ADDRESSES.csv. This supersedes the remembered but unlocated figure of 15,758. Address is not asserted to be 1:1 with gene.",
        "CLAUDE_PHASE_A": "NOT INCLUDED -- the exact-sampler shards were still running when this bundle was built. Receipts and branch SHA follow separately."}

    mp = os.path.join(a.stage, "MANIFEST.json")
    with open(mp, "w") as fh:
        json.dump(man, fh, indent=2)
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(os.listdir(a.stage)):
            z.write(os.path.join(a.stage, n), n)
    print(f"\nbundle: {a.out}  {os.path.getsize(a.out)/1e6:.1f} MB")
    print(f"sha256: {sha(a.out)}")
    for n, v in man["files"].items():
        print(f"  {n:<44} {v['bytes']/1e6:8.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
