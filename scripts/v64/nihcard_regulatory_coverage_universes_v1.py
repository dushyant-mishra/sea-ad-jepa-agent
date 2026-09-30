#!/usr/bin/env python3
"""Three nested coverage universes A > B > C, measurement/structural only.

A  RNA-covered queries              -- the broad RNA-state target is available
B  NIH-CARD regulatory-measurable   -- paired RNA+ATAC support enough to potentially
                                       construct/test query-local regulatory state
C  Nott/E2 anchored queries         -- the subset with external contact evidence

WHAT THIS DELIBERATELY DOES NOT DO. No regulatory target is constructed. No peak is
selected because it correlates with its gene. No candidate relationship is ranked by
the correspondence outcome under test. Nearest peak is never treated as regulatory
truth. The question is only: how much of the query universe could NIH-CARD
potentially support with analogous paired measurements.

MATRIX ACCESS DECLARATION -- this expands beyond the previous bounded integrity reads
and is recorded precisely.
  READ:  RNA .X restricted to microglia rows, accumulated to PER-GENE COLUMN
         marginals (nonzero count, sum) and per-donor nonzero counts.
         ATAC .X restricted to microglia rows, accumulated to PER-PEAK COLUMN
         marginals (nonzero count).
  NEVER: any gene vector multiplied, correlated or joined against any peak vector.
         There is no code path here that holds a gene's expression vector and a
         peak's accessibility vector at the same time. Marginals are accumulated
         independently into two separate 1-D arrays and never combined.
  WHY OUTCOME-BLIND: a column marginal is a property of one feature's measurement,
  not of a relationship between two features. Correspondence requires the cross
  product, which is never formed.

GENE ANNOTATION. The broader universe cannot be defined by promoter proximity using
an external TSS source -- the frozen contracts forbid external gene annotation. The
Nott Table S5 H3K4me3 promoter annotation is used instead: it is already
authenticated, already the project's promoter authority, and covers far more genes
than E2 itself.

TRAINING=OFF. TD60=BLOCKED. Stage 4 sealed.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from collections import Counter, defaultdict

import numpy as np

E2 = "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz"
E2_SHA = "bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c"
S5 = "C:/Users/dushy/Downloads/NIHMS1066836-supplement-Table_S5.xlsx"
S5_SHA = "81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e"
MG = "MG"
BLOCK = 20000
MIN_MICROGLIA_PER_DONOR = 100
TARGET_METACELL = 25

# Frozen, structural, outcome-blind measurability thresholds.
# Chosen as minimal non-degeneracy conditions, not tuned to any result.
MIN_NUCLEI_DETECTED_GENE = 100      # gene detected in >=100 microglia nuclei
MIN_DONORS_DETECTED_GENE = 30       # and in >=30 donors
MIN_NUCLEI_DETECTED_PEAK = 100      # peak observed in >=100 microglia nuclei


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def col_marginals(X, rows, n_cols, donor_codes, n_donors, log, label):
    """Per-column nonzero counts over selected rows, plus per-column donor breadth.

    Streams row blocks. Accumulates into 1-D arrays only. Never forms a cross
    product between two features.
    """
    nz = np.zeros(n_cols, dtype=np.int64)
    donor_hit = np.zeros((n_cols,), dtype=np.int32)
    seen = np.zeros(n_cols, dtype=np.int32)
    rows = np.asarray(rows)
    done = 0
    for lo in range(0, len(rows), BLOCK):
        idx = rows[lo:lo + BLOCK]
        sub = X[idx[0]:idx[-1] + 1]
        keep = idx - idx[0]
        sub = sub[keep]
        sub = sub.tocsc() if hasattr(sub, "tocsc") else sub
        cnt = np.asarray((sub != 0).sum(axis=0)).ravel()
        nz += cnt.astype(np.int64)
        dc = donor_codes[idx]
        for d in np.unique(dc):
            m = dc == d
            c2 = np.asarray((sub[m] != 0).sum(axis=0)).ravel()
            hit = c2 > 0
            donor_hit[hit] += 1
        done += len(idx)
        if (lo // BLOCK) % 2 == 0:
            log(f"    [{label}] {done:,}/{len(rows):,} nuclei")
    del seen
    return nz, donor_hit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", required=True)
    ap.add_argument("--atac", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    import anndata
    import openpyxl
    if sha256_file(S5) != S5_SHA:
        raise SystemExit("STOP_S5_DIGEST")
    rna = anndata.read_h5ad(a.rna, backed="r")
    atac = anndata.read_h5ad(a.atac, backed="r")

    ct = rna.obs["cell_type"].astype(str).values
    don = rna.obs["SampleID"].astype(str).values
    mg_rows = np.flatnonzero(ct == MG)
    donors = sorted(set(don[mg_rows]))
    dcode = {d: i for i, d in enumerate(donors)}
    donor_codes = np.array([dcode.get(x, -1) for x in don], dtype=np.int32)
    per_donor = Counter(don[mg_rows])
    qual_donors = {d: n for d, n in per_donor.items() if n >= MIN_MICROGLIA_PER_DONOR}
    metacells = {d: n // TARGET_METACELL for d, n in qual_donors.items()}
    log(f"microglia nuclei {len(mg_rows):,} over {len(donors):,} donors; "
        f"{len(qual_donors):,} donors meet the frozen minimum")

    # ---------- C: Nott/E2 anchored
    with gzip.open(E2, "rb") as fh:
        raw = fh.read()
    if hashlib.sha256(raw).hexdigest() != E2_SHA:
        raise SystemExit("STOP_E2_DIGEST")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    er = [l.split("\t") for l in el[1:]]
    e2_genes = set(r[ix["nearest_ensembl"]] for r in er)
    e2_proms = set(f'{r[ix["chrom"]]}:{r[ix["promoter_start_hg38"]]}' for r in er)
    e2_distals = set(f'{r[ix["chrom"]]}:{r[ix["distal_start_hg38"]]}' for r in er)
    log(f"C  Nott/E2: {len(er):,} edges | {len(e2_genes):,} genes | "
        f"{len(e2_proms):,} promoters | {len(e2_distals):,} distinct regulatory intervals")

    # ---------- Nott promoter annotation: the project's promoter authority
    wb = openpyxl.load_workbook(S5, read_only=True, data_only=True)
    ws = wb["H3K4me3_around_TSS_annotated_pe"]
    rws = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rws)
              if r and any(str(x).strip() == "PeakID" for x in r if x))
    hdr = [str(x).strip() if x is not None else "" for x in rws[hi]]
    col = {k: i for i, k in enumerate(hdr)}
    nott_all, nott_pu1 = set(), set()
    for r in rws[hi + 1:]:
        if not r or r[col["Chr"]] is None:
            continue
        e = r[col["Nearest Ensembl"]]
        if e is None or not str(e).strip():
            continue
        e = str(e).strip()
        nott_all.add(e)
        f = r[col["PU1_active_promoter"]]
        if f is True or str(f).strip().upper() in ("TRUE", "1", "YES"):
            nott_pu1.add(e)
    log(f"Nott promoter annotation: {len(nott_all):,} genes total, "
        f"{len(nott_pu1):,} with a PU.1-active promoter")

    # ---------- A: RNA-covered
    gid = np.array([str(g) for g in rna.var["gene_ids"].values])
    log("\nstreaming RNA per-gene column marginals over microglia ...")
    g_nz, g_don = col_marginals(rna.X, mg_rows, rna.n_vars, donor_codes,
                                len(donors), log, "RNA")
    rna_measurable = (g_nz >= MIN_NUCLEI_DETECTED_GENE) & (g_don >= MIN_DONORS_DETECTED_GENE)
    A_genes = set(gid[rna_measurable])
    log(f"A  RNA-covered queries: {len(A_genes):,} of {rna.n_vars:,} genes "
        f"(detected in >={MIN_NUCLEI_DETECTED_GENE} nuclei and >={MIN_DONORS_DETECTED_GENE} donors)")

    # ---------- ATAC peak measurability
    log("\nstreaming ATAC per-peak column marginals over microglia ...")
    p_nz, p_don = col_marginals(atac.X, mg_rows, atac.n_vars, donor_codes,
                                len(donors), log, "ATAC")
    peak_ok = p_nz >= MIN_NUCLEI_DETECTED_PEAK
    log(f"   measurable consensus peaks: {int(peak_ok.sum()):,} of {atac.n_vars:,}")

    out = {
        "schema": "V64_NIH_CARD_REGULATORY_COVERAGE_UNIVERSES_V1",
        "date": "2026-09-30",
        "MATRIX_ACCESS_DECLARATION": {
            "expanded_beyond_bounded_integrity_reads": True,
            "rna_read": "RNA .X restricted to microglia rows, accumulated to per-gene "
                        "column marginals (nonzero count, donor breadth)",
            "atac_read": "ATAC .X restricted to microglia rows, accumulated to per-peak "
                         "column marginals (nonzero count, donor breadth)",
            "never_done": "no gene vector was correlated, multiplied or joined against "
                          "any peak vector; the two marginal arrays are accumulated "
                          "independently and never combined",
            "why_outcome_blind": "a column marginal is a property of ONE feature's "
                                 "measurement, not of a relationship between two. "
                                 "Correspondence requires the cross product, which is "
                                 "never formed.",
            "no_correlation_based_selection": True,
            "nearest_peak_not_treated_as_truth": True},
        "frozen_measurability_rules": {
            "gene": f"detected in >={MIN_NUCLEI_DETECTED_GENE} microglia nuclei AND "
                    f">={MIN_DONORS_DETECTED_GENE} donors",
            "peak": f"observed in >={MIN_NUCLEI_DETECTED_PEAK} microglia nuclei",
            "rationale": "minimal non-degeneracy conditions, fixed before the counts "
                         "were seen; they are not tuned to any result"},
        "population": {
            "microglia_nuclei": int(len(mg_rows)), "donors": len(donors),
            "donors_meeting_frozen_minimum": len(qual_donors),
            "metacells_total": int(sum(metacells.values())) if metacells else 0,
            "metacells_per_donor": {
                "min": int(min(metacells.values())) if metacells else None,
                "median": float(np.median(list(metacells.values()))) if metacells else None,
                "max": int(max(metacells.values())) if metacells else None}},
        "C_nott_e2_anchored": {
            "edges": len(er), "distinct_genes": len(e2_genes),
            "distinct_promoters": len(e2_proms),
            "distinct_regulatory_intervals": len(e2_distals)},
        "nott_promoter_annotation": {"genes_total": len(nott_all),
                                     "genes_with_pu1_active_promoter": len(nott_pu1)},
        "A_rna_covered": {"universe_size": int(rna.n_vars),
                          "measurable_genes": int(rna_measurable.sum())},
        "atac_measurability": {"consensus_peaks": int(atac.n_vars),
                               "measurable_peaks": int(peak_ok.sum())},
        "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                       "stage_4": "NOT_AUTHORISED",
                       "regulatory_targets_constructed": False,
                       "correspondence_computed": False},
    }
    np.savez_compressed(os.path.join(a.out_dir, "marginals.npz"),
                        gene_ids=gid, gene_nz=g_nz, gene_donors=g_don,
                        peak_nz=p_nz, peak_donors=p_don,
                        peak_names=np.array([str(p) for p in atac.var_names], dtype=object))
    with open(os.path.join(a.out_dir,
                           "V64_NIH_CARD_REGULATORY_COVERAGE_UNIVERSES_V1.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    log("\nmarginals written; no correspondence value was computed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
