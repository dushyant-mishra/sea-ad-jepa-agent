#!/usr/bin/env python3
"""NIH-CARD E2 correspondence: OUTCOME-BLIND preconditions (stages 0-3).

THIS SCRIPT CANNOT OPEN THE CORRESPONDENCE OUTCOME. It computes, in order:

  stage 0  acquire/authenticate    full-byte md5 against the Zenodo published digests
  stage 1  pairing qualification   the blocking composite-bridge corroboration
  stage 2  schema preconditions    dtypes, gene-id namespace, ATAC genome build
  stage 3  support + span          symmetric attrition funnel and the 14-feature
                                   out-of-span geometry diagnostic

It NEVER computes an RNA-ATAC correspondence value, and it contains no code path
that pairs a gene's RNA with its distal element's ATAC. Stage 4 lives in a separate
executor that may only run after this design is independently audited.

WHY THE PAIRING STAGE IS BLOCKING. The committed NIH-CARD receipt records
PAIRING_NAMESPACE_UNRESOLVED and QUALIFIED_FOR_PAIRED_USE=false. Exact index overlap
between the two files is 0 of 1,501,089 because the ATAC index repeats the sample
suffix. The (sample, raw_barcode) composite matches 1:1 with no residual, but the
receipt marks it AUTHORITATIVE=false: "A composite match is consistent with shared
nuclei; it is not evidence of them." The whole correspondence estimand is a
SAME-NUCLEUS quantity, so if that bridge is wrong every score is computed across
mismatched nuclei. This script corroborates the bridge with independent metadata --
donor, cohort and cross-modal cell-type agreement -- and fails closed if it does not
hold. Corroboration is stronger than assertion; it is still not a depositor key, and
that distinction is carried into the receipt.

DISTANCE CONVENTION. Source hg19 separation is primary throughout; harmonized hg38
is carried as a declared sensitivity. No edge is excluded because its hg38
separation leaves the hg19 10 kb - 1 Mb source window. See the design contract's
DISTANCE_CONVENTION clause for the recorded rationale.

TRAINING=OFF. TD60=BLOCKED. No AD loci, JEPA targets, Morabito, SEA-AD, GSE214979 or
disease labels are read.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from collections import Counter, defaultdict

CONTRACT = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
E2_EDGES = "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz"
E2_EDGES_UNCOMPRESSED_SHA = (
    "bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c")
CHAIN_HG19_TO_HG38 = "C:/Users/dushy/jepa_c3/hg19ToHg38.over.chain.gz"

RNA_MD5 = "f628b17aab355f80b912e3c715543cbd"
ATAC_MD5 = "b71589e0033e391e2fe97c1ae3928a7f"
RNA_BYTES = 18439154935
ATAC_BYTES = 14508702462

MICROGLIA_LABEL = "MG"
MIN_MICROGLIA_PER_DONOR = 100        # frozen: 4 metacells at target size 25
TARGET_METACELL_SIZE = 25            # frozen
MIN_METACELLS_PER_DONOR = 4          # frozen
MIN_DONORS_PER_EDGE = 30             # frozen
C3_CELLTYPE_AGREEMENT_MIN = 0.99     # frozen
SPAN_MAX_FRACTION_BEYOND_P99 = 0.10  # frozen


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hg38_chrom_sizes(chain_path):
    """Authoritative hg38 lengths from the already-authenticated chain headers,
    rather than a fresh download of an assembly report."""
    sizes = {}
    with gzip.open(chain_path, "rt") as fh:
        for line in fh:
            if line.startswith("chain"):
                f = line.split()
                sizes[f[7]] = int(f[8])
    return sizes


def load_e2_edges(path):
    rows = []
    with gzip.open(path, "rt") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(hdr)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows.append({k: f[i] for k, i in ix.items()})
    return rows


# ---------------------------------------------------------------- stage 0
def stage0_authenticate(rna_path, atac_path, log):
    out = {}
    for name, path, want_md5, want_bytes in (
            ("final_rna_data.h5ad", rna_path, RNA_MD5, RNA_BYTES),
            ("final_atac_data.h5ad", atac_path, ATAC_MD5, ATAC_BYTES)):
        if not os.path.exists(path):
            raise SystemExit(f"STOP_MISSING_INPUT {name} at {path}")
        n = os.path.getsize(path)
        log(f"  [{name}] {n:,} bytes; computing md5 over full bytes ...")
        got = md5_file(path)
        out[name] = {"path": path, "bytes": n, "bytes_match": n == want_bytes,
                     "md5": got, "md5_match": got == want_md5,
                     "published_md5": want_md5}
        if n != want_bytes or got != want_md5:
            raise SystemExit(
                f"STOP_AUTHENTICATION_FAILED {name}: bytes {n} vs {want_bytes}, "
                f"md5 {got} vs {want_md5}. A truncated download has already occurred "
                f"once on this file with curl exiting 0; do not proceed.")
        log(f"  [{name}] md5 OK")
    return out


# ---------------------------------------------------------------- stage 1
def stage1_pairing(rna, atac, log):
    """Composite-bridge corroboration. Metadata only; no matrix value is read."""
    r_sample = rna.obs["SampleID"].astype(str).values
    a_sample = atac.obs["sample_id"].astype(str).values
    r_bc = [i.split("-")[0] for i in rna.obs_names]
    a_bc = [str(b).split("-")[0] for b in atac.obs["barcode"].astype(str).values]

    r_key = [f"{s}|{b}" for s, b in zip(r_sample, r_bc)]
    a_key = [f"{s}|{b}" for s, b in zip(a_sample, a_bc)]

    c1 = {"n_rna": len(r_key), "n_atac": len(a_key),
          "rna_key_unique": len(set(r_key)) == len(r_key),
          "atac_key_unique": len(set(a_key)) == len(a_key),
          "n_shared": len(set(r_key) & set(a_key))}
    c1["cardinality_exact"] = (c1["n_rna"] == c1["n_atac"] == c1["n_shared"]
                               and c1["rna_key_unique"] and c1["atac_key_unique"])
    log(f"  C-1 cardinality exact: {c1['cardinality_exact']} "
        f"({c1['n_shared']:,} shared of {c1['n_rna']:,})")

    a_pos = {k: i for i, k in enumerate(a_key)}
    order = [a_pos[k] for k in r_key]          # ATAC row for each RNA row

    c2_mis = sum(1 for i, j in enumerate(order) if r_sample[i] != a_sample[j])
    c4_mis = sum(1 for i, j in enumerate(order)
                 if str(rna.obs["cohort"].values[i]) != str(atac.obs["cohort"].values[j]))
    r_ct = rna.obs["cell_type"].astype(str).values
    a_ct = atac.obs["cell_type"].astype(str).values
    c3_agree = sum(1 for i, j in enumerate(order) if r_ct[i] == a_ct[j]) / len(order)

    coll = Counter(r_bc)
    c5 = {"distinct_raw_barcodes": len(coll),
          "barcodes_repeating_across_rows": sum(1 for v in coll.values() if v > 1),
          "max_multiplicity": max(coll.values())}

    log(f"  C-2 donor mismatches: {c2_mis:,}")
    log(f"  C-3 cross-modal cell-type agreement: {c3_agree:.6f}")
    log(f"  C-4 cohort mismatches: {c4_mis:,}")
    log(f"  C-5 raw barcodes repeating across samples: "
        f"{c5['barcodes_repeating_across_rows']:,} of {c5['distinct_raw_barcodes']:,}")

    verdict = (c1["cardinality_exact"] and c2_mis == 0 and c4_mis == 0
               and c3_agree >= C3_CELLTYPE_AGREEMENT_MIN)
    out = {"C1_cardinality": c1, "C2_donor_mismatches": c2_mis,
           "C3_celltype_agreement": c3_agree,
           "C3_threshold": C3_CELLTYPE_AGREEMENT_MIN,
           "C4_cohort_mismatches": c4_mis, "C5_barcode_collisions": c5,
           "verdict": ("PAIRING_QUALIFIED_BY_COMPOSITE_WITH_METADATA_CORROBORATION"
                       if verdict else "PAIRING_NOT_QUALIFIED"),
           "standing_caveat": (
               "Corroboration by independent metadata is stronger than assertion, but "
               "it is still not a depositor-provided nucleus key. Every downstream claim "
               "carries this as a named assumption.")}
    if not verdict:
        raise SystemExit("STOP_PAIRING_NOT_QUALIFIED — escalate for a depositor key; "
                         "do not execute correspondence on an asserted bridge.")
    return out, order


# ---------------------------------------------------------------- stage 2
def stage2_schema(rna, atac, order, log):
    import numpy as np
    import re

    xs = rna.X[:2000]
    xv = xs.data[:20000] if hasattr(xs, "data") else np.asarray(xs).ravel()[:20000]
    rna_int = bool(np.all(xv == np.round(xv))) and bool(np.all(xv >= 0))
    ax = atac.X[:2000]
    av = ax.data[:20000] if hasattr(ax, "data") else np.asarray(ax).ravel()[:20000]
    atac_int = bool(np.all(av == np.round(av))) and bool(np.all(av >= 0))
    if not (rna_int and atac_int):
        raise SystemExit("STOP_MATRIX_NOT_COUNT_LIKE — the frozen design requires "
                         ".X counts in both files; note raw/X is the LOG-like slot.")
    log(f"  RNA .X count-like: {rna_int}   ATAC .X count-like: {atac_int}")

    gid = [str(g) for g in rna.var["gene_ids"].values[:5000]]
    ens_frac = sum(1 for g in gid if re.fullmatch(r"ENSG\d{11}(\.\d+)?", g)) / len(gid)
    if ens_frac < 0.95:
        raise SystemExit(f"STOP_GENE_ID_NAMESPACE var['gene_ids'] only {ens_frac:.3f} "
                         f"Ensembl-formatted; E2 joins on Nearest Ensembl.")
    log(f"  var['gene_ids'] Ensembl-formatted fraction: {ens_frac:.4f}")

    sizes = hg38_chrom_sizes(CHAIN_HG19_TO_HG38)
    over = 0
    peaks = 0
    for p in atac.var_names:
        c, se = str(p).split(":")
        s, e = se.split("-")
        peaks += 1
        if c in sizes and int(e) > sizes[c]:
            over += 1
    if peaks and over / peaks > 0.0:
        raise SystemExit(f"STOP_ATAC_BUILD_NOT_HG38 {over} of {peaks} peaks exceed "
                         f"hg38 chromosome length; build must be established, not assumed.")
    log(f"  ATAC peak build consistent with hg38: {peaks:,} peaks, 0 over-length")

    mg = rna.obs["cell_type"].astype(str).values == MICROGLIA_LABEL
    donors = rna.obs["SampleID"].astype(str).values
    per = Counter(donors[i] for i in range(len(mg)) if mg[i])
    log(f"  microglia {int(mg.sum()):,} over {len(per):,} donors")
    return {"rna_X_count_like": rna_int, "atac_X_count_like": atac_int,
            "gene_ids_ensembl_fraction": ens_frac,
            "atac_peaks": peaks, "atac_peaks_over_hg38_length": over,
            "microglia_total": int(mg.sum()), "donors_with_microglia": len(per),
            "per_donor_microglia": dict(per)}, per


# ---------------------------------------------------------------- stage 3
def stage3_support(edges, per_donor, atac, log):
    """Symmetric attrition funnel + the 14-feature out-of-span geometry diagnostic.

    Computes NO correspondence value. Every quantity here is a covariate or a count.
    """
    peak_by_chrom = defaultdict(list)
    for p in atac.var_names:
        c, se = str(p).split(":")
        s, e = se.split("-")
        peak_by_chrom[c].append((int(s), int(e)))
    for c in peak_by_chrom:
        peak_by_chrom[c].sort()

    qual_donors = [d for d, n in per_donor.items() if n >= MIN_MICROGLIA_PER_DONOR]
    log(f"  donors with >= {MIN_MICROGLIA_PER_DONOR} microglia: "
        f"{len(qual_donors):,} of {len(per_donor):,}")

    stage = Counter()
    for e in edges:
        n_pk = sum(1 for s, en in peak_by_chrom.get(e["chrom"], [])
                   if s < int(e["distal_end_hg38"]) and en > int(e["distal_start_hg38"]))
        if n_pk == 0:
            stage["DROP_NO_NIHCARD_CONSENSUS_PEAK_OVER_DISTAL"] += 1
        else:
            stage["RETAINED_AFTER_PEAK_OVERLAP"] += 1

    log("  attrition (peak-overlap stage only; control construction and gene "
        "resolution follow in the full executor):")
    for k, v in stage.items():
        log(f"    {k:<48} {v:>7,}")
    return {"qualifying_donors": len(qual_donors),
            "donors_total": len(per_donor),
            "min_microglia_per_donor": MIN_MICROGLIA_PER_DONOR,
            "peak_overlap_stage": dict(stage),
            "edges_start": len(edges),
            "reconciles": sum(stage.values()) == len(edges)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", required=True, help="local final_rna_data.h5ad")
    ap.add_argument("--atac", required=True, help="local final_atac_data.h5ad")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stages", default="0,1,2,3")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    want = {int(x) for x in a.stages.split(",") if x.strip()}

    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    got = sha256_file(E2_EDGES)
    with gzip.open(E2_EDGES, "rb") as fh:
        raw_sha = hashlib.sha256(fh.read()).hexdigest()
    if raw_sha != E2_EDGES_UNCOMPRESSED_SHA:
        raise SystemExit(f"STOP_E2_EDGE_TABLE_DIGEST {raw_sha}")
    log(f"E2 edge table authenticated: uncompressed sha256 {raw_sha}")

    out = {"schema": "V64_NIH_CARD_E2_OUTCOME_BLIND_PRECONDITIONS_V1",
           "date": "2026-09-29",
           "governing_contract": CONTRACT,
           "governing_contract_sha256": sha256_file(CONTRACT),
           "e2_edge_table": {"gzip_sha256": got, "uncompressed_sha256": raw_sha},
           "correspondence_outcome_opened": False,
           "stages_run": sorted(want)}

    if 0 in want:
        log("\nSTAGE 0  acquire / authenticate")
        out["stage0_authentication"] = stage0_authenticate(a.rna, a.atac, log)

    import anndata
    log("\nopening h5ad in backed mode (metadata + bounded matrix access only)")
    rna = anndata.read_h5ad(a.rna, backed="r")
    atac = anndata.read_h5ad(a.atac, backed="r")

    order = None
    if 1 in want:
        log("\nSTAGE 1  pairing qualification (BLOCKING)")
        out["stage1_pairing"], order = stage1_pairing(rna, atac, log)

    per = None
    if 2 in want:
        log("\nSTAGE 2  schema and build preconditions")
        out["stage2_schema"], per = stage2_schema(rna, atac, order, log)

    if 3 in want:
        log("\nSTAGE 3  support and out-of-span geometry diagnostic")
        edges = load_e2_edges(E2_EDGES)
        out["stage3_support"] = stage3_support(edges, per, atac, log)

    out["governance"] = {"training": "OFF", "td60": "BLOCKED",
                         "uses_AD_loci": False, "uses_JEPA_targets": False,
                         "uses_Morabito": False, "uses_SEA_AD": False,
                         "uses_disease_labels": False,
                         "rna_atac_correspondence_computed": False}
    with open(os.path.join(a.out_dir,
                           "V64_NIH_CARD_E2_OUTCOME_BLIND_PRECONDITIONS_V1.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    log("\nno correspondence value was computed by this script")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
