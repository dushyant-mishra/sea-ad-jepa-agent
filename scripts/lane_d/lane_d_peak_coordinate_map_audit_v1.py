#!/usr/bin/env python
"""LANE D - GSE174367 ATAC peak coordinate-map audit.

READ-ONLY. Three jobs:

  1. Verify the hg38 build claim by containment against hg38.chrom.sizes.
  2. Re-derive the Stage75C nearest-TSS peak-to-gene assignment from
     GENCODE v44 and check it reproduces the frozen table, then QUANTIFY the
     ambiguity that a one-nearest-gene table structurally cannot record:
     nearest-TSS ties, multi-gene windows, and peaks with no gene in range.
  3. Audit the Stage75F cisTarget region mapping for unmapped query peaks.

Nothing is dropped. Every unmapped or ambiguous peak is counted and the counts
are written to the manifest.

Governance: TRAINING=OFF | AUDIT_B_N1=UNOPENED |
PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED |
RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF
"""
import argparse
import collections
import gzip
import json
import os
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd

PROMOTER_BP = 2000      # Stage75C frozen parameter
PROXIMAL_BP = 100000    # Stage75C frozen parameter


def load_chrom_sizes(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            p = line.split()
            if len(p) >= 2:
                out[p[0]] = int(p[1])
    return out


def load_gencode_tss(gtf_gz):
    """Gene-level TSS exactly as Stage75C derived them.

    start is converted to 0-based (col4 - 1); TSS is the strand-aware gene
    boundary. Returns per-chromosome sorted TSS arrays plus gene identity.
    """
    per_chrom = collections.defaultdict(list)
    n_genes = 0
    biotypes = collections.Counter()
    attr_name = re.compile(r'gene_name "([^"]+)"')
    attr_id = re.compile(r'gene_id "([^"]+)"')
    attr_bt = re.compile(r'gene_type "([^"]+)"')
    with gzip.open(gtf_gz, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            chrom, start, end, strand, attrs = p[0], int(p[3]) - 1, int(p[4]), p[6], p[8]
            tss = start if strand == "+" else end
            gname = attr_name.search(attrs)
            gid = attr_id.search(attrs)
            bt = attr_bt.search(attrs)
            per_chrom[chrom].append((tss, gname.group(1) if gname else "",
                                     gid.group(1) if gid else "",
                                     bt.group(1) if bt else ""))
            n_genes += 1
            biotypes[bt.group(1) if bt else ""] += 1
    packed = {}
    for c, v in per_chrom.items():
        v.sort(key=lambda t: t[0])
        packed[c] = dict(tss=np.array([t[0] for t in v]),
                         name=[t[1] for t in v],
                         gid=[t[2] for t in v],
                         biotype=[t[3] for t in v])
    return packed, n_genes, biotypes


def audit(root, out_dir):
    res_dir = os.path.join(root, "results")
    peaks = pd.read_csv(os.path.join(res_dir, "tables",
                                     "stage75c_peak_to_gene_preflight_v1.csv"))
    chrom_sizes = load_chrom_sizes(os.path.join(
        root, "data/external_resources/stage75b/hg38.chrom.sizes"))
    tss, n_genes, biotypes = load_gencode_tss(os.path.join(
        root, "data/external_resources/stage75b/gencode.v44.annotation.gtf.gz"))

    # ---------------- 1. build verification by containment -----------------
    known = peaks.chrom.map(lambda c: c in chrom_sizes)
    size = peaks.chrom.map(lambda c: chrom_sizes.get(c, -1))
    oob_end = (peaks.end > size) & known
    neg_start = peaks.start < 0
    build = dict(
        chrom_sizes_file="data/external_resources/stage75b/hg38.chrom.sizes",
        n_peaks=int(len(peaks)),
        peaks_on_contigs_absent_from_hg38_chrom_sizes=int((~known).sum()),
        peaks_with_end_beyond_hg38_contig_length=int(oob_end.sum()),
        peaks_with_negative_start=int(neg_start.sum()),
        max_observed_end_fraction_of_contig=round(
            float((peaks.end[known] / size[known]).max()), 6),
        gencode_contigs_matching_peak_contigs=sorted(
            set(peaks.chrom) & set(tss)),
        peak_contigs_absent_from_gencode=sorted(set(peaks.chrom) - set(tss)),
        verdict=("hg38_CONSISTENT" if (~known).sum() == 0 and oob_end.sum() == 0
                 and neg_start.sum() == 0 else "BUILD_INCONSISTENT"),
        note=("Containment against hg38.chrom.sizes is a necessary, not sufficient, "
              "test. It rules out hg19/T2T coordinates at the tail of each contig "
              "but does not prove per-peak build identity."))

    # -------- 2. re-derive nearest TSS and quantify hidden ambiguity --------
    rows = []
    for chrom, sub in peaks.groupby("chrom", sort=False):
        if chrom not in tss:
            for r in sub.itertuples():
                rows.append((r.peak_id, None, None, None, 0, 0, 0, True))
            continue
        arr = tss[chrom]["tss"]
        names = np.asarray(tss[chrom]["name"])
        mid = ((sub.start + sub.end) // 2).to_numpy()
        for pid, m in zip(sub.peak_id.to_numpy(), mid):
            if len(arr) == 0:
                rows.append((pid, None, None, None, 0, 0, 0, True))
                continue
            # Exact, unbounded distance vector: ties are enumerated over the
            # whole chromosome, never over a truncated neighbourhood window.
            d = np.abs(arr - m)
            dmin = int(d.min())
            tie_genes = sorted(set(names[d == dmin]))
            n_prom = int(np.count_nonzero(d <= PROMOTER_BP))
            n_prox = int(np.count_nonzero(d <= PROXIMAL_BP))
            rows.append((pid, tie_genes[0], dmin, "|".join(tie_genes),
                         len(tie_genes), n_prom, n_prox, n_prox == 0))
    red = pd.DataFrame(rows, columns=[
        "peak_id", "rederived_nearest_gene", "rederived_abs_distance_to_tss",
        "tied_nearest_genes", "n_tied_nearest_genes",
        "n_gene_tss_within_2kb", "n_gene_tss_within_100kb",
        "no_gene_tss_within_100kb"])
    merged = peaks.merge(red, on="peak_id", how="left", validate="one_to_one")

    dist_match = (merged.abs_distance_to_tss == merged.rederived_abs_distance_to_tss)
    gene_match = (merged.nearest_gene.astype(str) ==
                  merged.rederived_nearest_gene.astype(str))
    gene_in_tie = merged.apply(
        lambda r: str(r.nearest_gene) in str(r.tied_nearest_genes).split("|"), axis=1)

    ambiguity = dict(
        method_recorded_in_stage75c="single nearest gene-level TSS, no tie record",
        promoter_window_bp=PROMOTER_BP, proximal_window_bp=PROXIMAL_BP,
        gencode_release="v44", gencode_genes_parsed=int(n_genes),
        gencode_protein_coding=int(biotypes.get("protein_coding", 0)),
        reproduction=dict(
            peaks_compared=int(len(merged)),
            nearest_tss_distance_reproduced=int(dist_match.sum()),
            nearest_gene_symbol_reproduced=int(gene_match.sum()),
            frozen_gene_is_one_of_the_tied_nearest=int(gene_in_tie.sum()),
            distance_reproduction_fraction=round(float(dist_match.mean()), 6)),
        unmapped=dict(
            peaks_with_no_gene_tss_within_100kb=int(merged.no_gene_tss_within_100kb.sum()),
            peaks_on_contig_with_no_gencode_genes=int(
                merged.rederived_nearest_gene.isna().sum()),
            stage75c_distal_gt_100kb_class=int(
                (peaks.peak_gene_class == "distal_gt_100kb").sum()),
            note=("Stage75C assigns every peak a nearest gene, so its table has zero "
                  "unmapped rows by construction. The regulatorily unassignable set is "
                  "the distal_gt_100kb class: those peaks carry a gene label whose TSS "
                  "is further than the declared 100 kb proximal window.")),
        ambiguous=dict(
            peaks_with_tied_nearest_tss=int((merged.n_tied_nearest_genes > 1).sum()),
            max_tie_multiplicity=int(merged.n_tied_nearest_genes.max()),
            peaks_with_2_or_more_tss_in_promoter_window=int(
                (merged.n_gene_tss_within_2kb >= 2).sum()),
            peaks_with_1_tss_in_promoter_window=int(
                (merged.n_gene_tss_within_2kb == 1).sum()),
            peaks_with_0_tss_in_promoter_window=int(
                (merged.n_gene_tss_within_2kb == 0).sum()),
            peaks_with_2_or_more_tss_in_100kb=int(
                (merged.n_gene_tss_within_100kb >= 2).sum()),
            median_genes_within_100kb=int(merged.n_gene_tss_within_100kb.median()),
            p95_genes_within_100kb=int(np.percentile(merged.n_gene_tss_within_100kb, 95)),
            max_genes_within_100kb=int(merged.n_gene_tss_within_100kb.max()),
            note=("A single-nearest-gene table cannot express any of this. "
                  "Peak-to-gene assignment in Stage75C is many-to-one by fiat; the "
                  "true relation is many-to-many and must be modelled as such, or "
                  "the ambiguity must be carried as an explicit weight.")))

    amb_cols = ["peak_id", "chrom", "start", "end", "peak_gene_class", "nearest_gene",
                "abs_distance_to_tss", "rederived_nearest_gene",
                "rederived_abs_distance_to_tss", "n_tied_nearest_genes",
                "tied_nearest_genes", "n_gene_tss_within_2kb",
                "n_gene_tss_within_100kb", "no_gene_tss_within_100kb"]
    merged[amb_cols].to_csv(
        os.path.join(out_dir, "laneD_peak_gene_ambiguity_map_v1.csv.gz"),
        index=False, compression="gzip")

    # ---------------- 3. Stage75F cisTarget region mapping ----------------
    cis = {}
    cov_p = os.path.join(res_dir, "tables", "stage75f_cistarget_region_coverage_v1.csv")
    map_p = os.path.join(res_dir, "tables", "stage75f_cistarget_region_mapping_v1.csv")
    json_p = os.path.join(res_dir, "reports", "stage75f_cistarget_region_mapping_v1.json")
    if os.path.exists(cov_p) and os.path.exists(map_p):
        cov = pd.read_csv(cov_p)
        mp = pd.read_csv(map_p)
        recorded = json.load(open(json_p)) if os.path.exists(json_p) else {}
        mapped_q = set(mp.query_region)
        all_q = set()
        for path in cov.mapped_db_regions_path.dropna():
            pass
        unmapped_files = [os.path.join(root, p) for p in
                          cov.unmapped_query_regions_path.dropna()]
        unmapped_union = set()
        for f in unmapped_files:
            if os.path.exists(f):
                unmapped_union |= set(x.strip() for x in open(f) if x.strip())
        all_q = mapped_q | unmapped_union
        cis = dict(
            overlap_rule=recorded.get("fraction_overlap_rule"),
            overlap_threshold=recorded.get("fraction_overlap_threshold"),
            cistarget_database_regions=recorded.get("n_parseable_regions"),
            n_query_rows=int(cov.n_query_regions.sum()),
            n_mapped_query_rows=int(cov.n_mapped_query_regions.sum()),
            n_unmapped_query_rows=int(cov.n_unmapped_query_regions.sum()),
            n_exact_coordinate_matches=int(cov.n_exact_query_regions.sum()),
            n_mapping_rows=int(cov.n_mapping_rows.sum()),
            n_unique_query_peaks=int(len(all_q)),
            n_unique_query_peaks_mapped=int(len(mapped_q)),
            n_unique_query_peaks_never_mapped=int(len(unmapped_union - mapped_q)),
            never_mapped_query_peaks=sorted(unmapped_union - mapped_q),
            n_unique_db_regions_screened=int(mp.mapped_db_region.nunique()),
            db_regions_per_query_peak=dict(
                median=float(mp.groupby("query_region").mapped_db_region.nunique().median()),
                max=int(mp.groupby("query_region").mapped_db_region.nunique().max())),
            overlap_fraction_query=dict(
                median=round(float(mp.overlap_fraction_query.median()), 4),
                p10=round(float(mp.overlap_fraction_query.quantile(0.10)), 4)),
            overlap_fraction_db=dict(
                median=round(float(mp.overlap_fraction_db.median()), 4),
                p10=round(float(mp.overlap_fraction_db.quantile(0.10)), 4)),
            ambiguity_note=("Mapping is many-to-many: one GSE174367 peak maps to "
                            "multiple SCREEN regions because the peaks are wider "
                            "than SCREEN regions, and zero mappings are exact "
                            "coordinate matches. Motif evidence attributed to a peak "
                            "is therefore evidence about a set of overlapping SCREEN "
                            "regions, not about that peak's own interval."),
            screened_fraction_of_full_peak_universe=round(
                len(all_q) / float(len(peaks)), 8))

    manifest = dict(
        lane="LANE_D_external_multiomics",
        artifact="peak_coordinate_map_audit",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        execution_class="RECONNAISSANCE_ONLY",
        biological_evaluation_status="NOT_EXECUTED",
        governance_footer=("TRAINING=OFF | AUDIT_B_N1=UNOPENED | "
                           "PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED | "
                           "RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF"),
        hg38_build_verification=build,
        peak_to_gene_ambiguity=ambiguity,
        cistarget_region_mapping=cis)
    with open(os.path.join(out_dir, "laneD_coordinate_map_audit_v1.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(json.dumps(manifest, indent=2)[:9000])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    audit(a.repo_root, a.out_dir)


if __name__ == "__main__":
    main()
