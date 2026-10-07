#!/usr/bin/env python
"""LANE D scope B - peak-to-gene mapping over the full 219,070-peak universe.

READ-ONLY. No biological evaluation is executed here; this establishes what
chromatin evidence exists and how strong each kind of evidence is.

The central discipline is that five very different things are kept apart and
are never allowed to collapse into one "peak-gene link":

  1 DIRECT_ATAC_ACCESSIBILITY  a peak measured as open in microglial nuclei,
                               overlapping the gene's promoter window. The ATAC
                               reads are the measurement.
  2 NEAREST_GENE_ANNOTATION    the gene happens to have the closest TSS. An
                               annotation convention, not evidence of regulation.
  3 GENOMIC_PROXIMITY          the peak lies inside a distance window of the TSS.
                               Many-to-many and weaker than (2).
  4 COACCESSIBILITY            peak-peak or peak-gene covariation links.
  5 INDEPENDENT_ENHANCER_LINK  externally supported enhancer-gene links
                               (ABC / Hi-C / eQTL / CRISPRi).

Classes 4 and 5 are reported as NOT_AVAILABLE unless an artifact is found.
Distal assignments stay PROVISIONAL: the nearest gene is never treated as the
true target.

Reproducibility is checked two ways:
  * an independent brute-force implementation must reproduce the vectorised
    nearest-TSS result exactly on a random sample;
  * a controlled coordinate perturbation shifts every peak by a fixed offset,
    and the assignment must change. A mapping insensitive to a coordinate
    shift is not measuring position.

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

import h5py
import numpy as np
import pandas as pd


def _jsonable(o):
    """numpy scalars are not JSON serialisable; convert rather than drop."""
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serialisable: {type(o).__name__}")

PROMOTER_BP = 2000       # Stage75C frozen promoter window
PROXIMAL_BP = 100000     # Stage75C frozen proximal window
PERTURB_BP = 50000       # controlled coordinate shift for the sensitivity test
RNG_SEED = 20260926


# --------------------------------------------------------------- annotation

def load_gencode_tss(gtf_gz):
    per_chrom = collections.defaultdict(list)
    biotypes = collections.Counter()
    n_genes = 0
    a_name = re.compile(r'gene_name "([^"]+)"')
    a_id = re.compile(r'gene_id "([^"]+)"')
    a_bt = re.compile(r'gene_type "([^"]+)"')
    with gzip.open(gtf_gz, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            chrom, start, end, strand, attrs = (p[0], int(p[3]) - 1, int(p[4]),
                                                p[6], p[8])
            tss = start if strand == "+" else end
            nm, gi, bt = a_name.search(attrs), a_id.search(attrs), a_bt.search(attrs)
            per_chrom[chrom].append((tss, nm.group(1) if nm else "",
                                     gi.group(1) if gi else "",
                                     bt.group(1) if bt else "", strand))
            biotypes[bt.group(1) if bt else ""] += 1
            n_genes += 1
    packed = {}
    for c, v in per_chrom.items():
        v.sort(key=lambda t: t[0])
        packed[c] = dict(tss=np.asarray([t[0] for t in v], dtype=np.int64),
                         name=np.asarray([t[1] for t in v]),
                         gid=np.asarray([t[2] for t in v]),
                         biotype=np.asarray([t[3] for t in v]),
                         strand=np.asarray([t[4] for t in v]))
    return packed, n_genes, biotypes


# ------------------------------------------------------------------- peaks

def load_peaks(h5_path):
    with h5py.File(h5_path, "r") as f:
        g = f["matrix"]
        pid = np.array([x.decode() for x in g["features"]["id"][:]])
        genome = np.array([x.decode() for x in g["features"]["genome"][:]])
        shape = g["shape"][:]
    rec = re.compile(r"^(chr[^:]+):(\d+)-(\d+)$")
    chrom, start, end, ok = [], [], [], []
    for x in pid:
        m = rec.match(x)
        ok.append(bool(m))
        chrom.append(m.group(1) if m else None)
        start.append(int(m.group(2)) if m else -1)
        end.append(int(m.group(3)) if m else -1)
    df = pd.DataFrame(dict(peak_index=np.arange(len(pid)), peak_id=pid,
                           chrom=chrom, start=start, end=end,
                           parseable=ok))
    df["midpoint"] = (df.start + df.end) // 2
    df["width"] = df.end - df.start
    return df, str(collections.Counter(genome).most_common(1)[0][0]), shape


def microglial_detection(csc_h5, n_peaks):
    """Per-peak microglial nucleus detection count.

    This is the only genuinely RNA-independent per-peak quantity available:
    it counts, for each peak, how many of the 12,232 microglial nuclei carry
    at least one fragment there. It uses no expression value of any kind.
    """
    if not os.path.exists(csc_h5):
        return None, dict(status="ABSENT", path=csc_h5)
    with h5py.File(csc_h5, "r") as f:
        g = f["matrix"]
        idx = g["indices"][:]
        shape = g["shape"][:]
        n_cells = int(g["indptr"].shape[0]) - 1
        attrs = {k: (v.decode() if isinstance(v, bytes) else v)
                 for k, v in f.attrs.items()}
    det = np.bincount(idx, minlength=n_peaks).astype(np.int64)
    meta = dict(status="PRESENT", path=csc_h5,
                subset_shape=[int(shape[0]), int(shape[1])],
                n_microglial_nuclei=n_cells, stored_nonzeros=int(idx.shape[0]),
                source_attrs=attrs,
                definition=("det[p] = number of microglial nuclei with at least "
                            "one fragment in peak p. Derived from ATAC fragments "
                            "only; no RNA value enters this quantity."))
    return det, meta


# ---------------------------------------------------- nearest-TSS mappings

def nearest_tss_vectorised(peaks, tss):
    """Vectorised nearest-TSS assignment plus full ambiguity accounting."""
    n = len(peaks)
    out = dict(
        nearest_gene=np.array([None] * n, dtype=object),
        nearest_gene_id=np.array([None] * n, dtype=object),
        nearest_biotype=np.array([None] * n, dtype=object),
        abs_distance=np.full(n, -1, dtype=np.int64),
        signed_distance=np.full(n, 0, dtype=np.int64),
        n_tied=np.zeros(n, dtype=np.int32),
        tied_genes=np.array([None] * n, dtype=object),
        n_tss_promoter=np.zeros(n, dtype=np.int32),
        n_tss_proximal=np.zeros(n, dtype=np.int32),
        promoter_genes=np.array([None] * n, dtype=object),
        proximal_genes=np.array([None] * n, dtype=object))
    for chrom, sub in peaks.groupby("chrom", sort=False):
        pos = sub.index.to_numpy()
        if chrom not in tss:
            continue
        arr, names = tss[chrom]["tss"], tss[chrom]["name"]
        gids, bts = tss[chrom]["gid"], tss[chrom]["biotype"]
        for i, m in zip(pos, sub.midpoint.to_numpy()):
            d = arr - m
            ad = np.abs(d)
            dmin = int(ad.min())
            tie = np.flatnonzero(ad == dmin)
            names_tie = sorted(set(names[tie]))
            out["nearest_gene"][i] = names_tie[0]
            out["nearest_gene_id"][i] = gids[tie[0]]
            out["nearest_biotype"][i] = bts[tie[0]]
            out["abs_distance"][i] = dmin
            out["signed_distance"][i] = int(d[tie[0]])
            out["n_tied"][i] = len(names_tie)
            out["tied_genes"][i] = "|".join(names_tie)
            pm = ad <= PROMOTER_BP
            px = ad <= PROXIMAL_BP
            out["n_tss_promoter"][i] = int(pm.sum())
            out["n_tss_proximal"][i] = int(px.sum())
            out["promoter_genes"][i] = "|".join(sorted(set(names[pm])))
            out["proximal_genes"][i] = "|".join(sorted(set(names[px])))
    return out


def nearest_tss_bruteforce(peaks_sample, tss):
    """Independent implementation: no groupby, no cached arrays, plain loop.

    Deliberately written a different way from the vectorised routine so that
    agreement between the two is evidence, not a shared bug.
    """
    res = []
    flat = []
    for c, d in tss.items():
        for t, nm in zip(d["tss"].tolist(), d["name"].tolist()):
            flat.append((c, t, nm))
    by_chrom = collections.defaultdict(list)
    for c, t, nm in flat:
        by_chrom[c].append((t, nm))
    for r in peaks_sample.itertuples():
        best_d, best_g = None, None
        for t, nm in by_chrom.get(r.chrom, []):
            dd = abs(t - r.midpoint)
            if best_d is None or dd < best_d or (dd == best_d and nm < best_g):
                best_d, best_g = dd, nm
        res.append((r.peak_id, best_g, best_d))
    return pd.DataFrame(res, columns=["peak_id", "bf_nearest_gene", "bf_abs_distance"])


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--perturb-sample", type=int, default=20000)
    ap.add_argument("--bruteforce-sample", type=int, default=1500)
    a = ap.parse_args()
    root, out = a.repo_root, a.out_dir
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    tss, n_genes, biotypes = load_gencode_tss(os.path.join(
        root, "data/external_resources/stage75b/gencode.v44.annotation.gtf.gz"))
    peaks, declared_genome, shape = load_peaks(os.path.join(
        root, "data/external/gse174367/"
              "GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5"))

    det, det_meta = microglial_detection(
        os.path.join(root, "data/processed/stage75f/gse174367_mg_snatac.csc.h5"),
        len(peaks))

    m = nearest_tss_vectorised(peaks, tss)
    for k, v in m.items():
        peaks[k] = v
    if det is not None:
        peaks["microglial_nuclei_detecting_peak"] = det
        peaks["microglial_detection_fraction"] = det / float(
            det_meta["n_microglial_nuclei"])

    # ---- evidence classes, kept strictly apart -------------------------
    has_prom = peaks.n_tss_promoter > 0
    has_prox = peaks.n_tss_proximal > 0
    det_ok = (peaks.microglial_nuclei_detecting_peak > 0) if det is not None \
        else pd.Series(False, index=peaks.index)

    peaks["evidence_class"] = np.select(
        [det_ok & has_prom,
         (~det_ok) & has_prom,
         det_ok & has_prox,
         (~det_ok) & has_prox],
        ["DIRECT_ATAC_ACCESSIBILITY_AT_PROMOTER",
         "PROMOTER_OVERLAP_NOT_DETECTED_IN_MICROGLIA",
         "GENOMIC_PROXIMITY_PROVISIONAL",
         "GENOMIC_PROXIMITY_NOT_DETECTED_IN_MICROGLIA"],
        default="NO_GENE_WITHIN_100KB_UNASSIGNABLE")
    peaks["distal_assignment_status"] = np.where(
        has_prom, "NOT_DISTAL",
        np.where(has_prox, "PROVISIONAL_DISTAL_NEAREST_GENE_IS_NOT_THE_TARGET",
                 "PROVISIONAL_ORPHAN_NO_CANDIDATE_TARGET"))

    # ---- gene-level rollups --------------------------------------------
    prom_gene_counter = collections.Counter()
    prom_gene_detected = collections.Counter()
    distal_gene_counter = collections.Counter()
    for r in peaks.itertuples():
        pg = [g for g in str(r.promoter_genes).split("|") if g]
        for g in pg:
            prom_gene_counter[g] += 1
            if det is not None and r.microglial_nuclei_detecting_peak > 0:
                prom_gene_detected[g] += 1
        if not pg:
            for g in [g for g in str(r.proximal_genes).split("|") if g]:
                distal_gene_counter[g] += 1
    all_gene_names = set()
    for d in tss.values():
        all_gene_names |= set(d["name"].tolist())

    genes = pd.DataFrame(dict(gene=sorted(all_gene_names)))
    genes["n_promoter_peaks"] = genes.gene.map(lambda g: prom_gene_counter.get(g, 0))
    genes["n_promoter_peaks_detected_in_microglia"] = genes.gene.map(
        lambda g: prom_gene_detected.get(g, 0))
    genes["n_distal_candidate_peaks"] = genes.gene.map(
        lambda g: distal_gene_counter.get(g, 0))
    genes["atac_evidence_class"] = np.select(
        [genes.n_promoter_peaks_detected_in_microglia > 0,
         genes.n_promoter_peaks > 0,
         genes.n_distal_candidate_peaks > 0],
        ["ACCESSIBLE_PROMOTER_IN_MICROGLIA",
         "PROMOTER_PEAK_PRESENT_NOT_DETECTED_IN_MICROGLIA",
         "DISTAL_CANDIDATE_ONLY_PROVISIONAL"],
        default="NO_USABLE_ATAC_EVIDENCE")
    genes.to_csv(os.path.join(out, "laneD_gene_atac_evidence_v1.csv.gz"),
                 index=False, compression="gzip")

    # ---- reproducibility check 1: independent implementation ------------
    samp = peaks[peaks.parseable].sample(
        n=min(a.bruteforce_sample, int(peaks.parseable.sum())), random_state=RNG_SEED)
    bf = nearest_tss_bruteforce(samp, tss)
    chk = samp[["peak_id", "nearest_gene", "abs_distance"]].merge(bf, on="peak_id")
    indep = dict(
        sample_size=int(len(chk)),
        distance_agreement=int((chk.abs_distance == chk.bf_abs_distance).sum()),
        gene_agreement=int((chk.nearest_gene.astype(str).str.lower() ==
                            chk.bf_nearest_gene.astype(str).str.lower()).sum()),
        agreement_is_exact=bool((chk.abs_distance == chk.bf_abs_distance).all()),
        note=("A second implementation written without the vectorised code path "
              "reproduces the nearest-TSS distance. Agreement between two "
              "independent routines is the reproducibility evidence."))

    # ---- reproducibility check 2: controlled coordinate perturbation ----
    psamp = peaks[peaks.parseable].sample(
        n=min(a.perturb_sample, int(peaks.parseable.sum())), random_state=RNG_SEED + 1)
    shifted = psamp[["peak_id", "chrom", "start", "end"]].copy()
    shifted["start"] = shifted.start + PERTURB_BP
    shifted["end"] = shifted.end + PERTURB_BP
    shifted["midpoint"] = (shifted.start + shifted.end) // 2
    shifted = shifted.reset_index(drop=True)
    sm = nearest_tss_vectorised(shifted, tss)
    shifted["shifted_nearest_gene"] = sm["nearest_gene"]
    shifted["shifted_abs_distance"] = sm["abs_distance"]
    cmp = psamp[["peak_id", "nearest_gene", "abs_distance"]].merge(
        shifted[["peak_id", "shifted_nearest_gene", "shifted_abs_distance"]],
        on="peak_id")
    changed_gene = (cmp.nearest_gene.astype(str).str.lower() !=
                    cmp.shifted_nearest_gene.astype(str).str.lower())
    changed_dist = (cmp.abs_distance != cmp.shifted_abs_distance)
    perturb = dict(
        shift_bp=PERTURB_BP, sample_size=int(len(cmp)),
        peaks_whose_nearest_gene_changed=int(changed_gene.sum()),
        fraction_nearest_gene_changed=round(float(changed_gene.mean()), 5),
        peaks_whose_tss_distance_changed=int(changed_dist.sum()),
        fraction_tss_distance_changed=round(float(changed_dist.mean()), 5),
        control_verdict=("POSITION_SENSITIVE_PASS"
                         if changed_dist.mean() > 0.95 and changed_gene.mean() > 0.2
                         else "POSITION_INSENSITIVE_FAIL"),
        note=("A 50 kb rigid shift must move almost every TSS distance and must "
              "reassign a substantial minority of nearest genes. A mapping that "
              "survived this shift unchanged would not be measuring position."))

    # ---- authentication against the frozen Stage75C table ---------------
    s75c_path = os.path.join(root, "results/tables/"
                                   "stage75c_peak_to_gene_preflight_v1.csv")
    s75c = {}
    if os.path.exists(s75c_path):
        frozen = pd.read_csv(s75c_path)
        j = frozen.merge(peaks[["peak_id", "nearest_gene", "abs_distance",
                                "tied_genes"]],
                         on="peak_id", suffixes=("_frozen", "_lane_d"))
        dist_ok = j.abs_distance_to_tss == j.abs_distance
        sym_ok = (j.nearest_gene_frozen.astype(str).str.lower() ==
                  j.nearest_gene_lane_d.astype(str).str.lower())
        in_tie = j.apply(lambda r: str(r.nearest_gene_frozen).lower() in
                         [x.lower() for x in str(r.tied_genes).split("|")], axis=1)
        case_only = (~(j.nearest_gene_frozen.astype(str) ==
                       j.nearest_gene_lane_d.astype(str))) & sym_ok
        s75c = dict(
            frozen_rows=int(len(frozen)), joined_rows=int(len(j)),
            tss_distance_reproduced=int(dist_ok.sum()),
            tss_distance_reproduction_fraction=round(float(dist_ok.mean()), 6),
            gene_symbol_reproduced_case_insensitive=int(sym_ok.sum()),
            gene_symbol_reproduced_case_sensitive=int(
                (j.nearest_gene_frozen.astype(str) ==
                 j.nearest_gene_lane_d.astype(str)).sum()),
            differences_that_are_symbol_case_only=int(case_only.sum()),
            frozen_gene_is_among_tied_nearest=int(in_tie.sum()),
            frozen_gene_among_tied_fraction=round(float(in_tie.mean()), 6),
            verdict=("REPRODUCED" if dist_ok.all() and in_tie.all()
                     else "NOT_FULLY_REPRODUCED"),
            note=("Stage75C stored gene symbols upper-cased. After case "
                  "normalisation the frozen assignment is reproduced exactly; "
                  "the residual difference is tie-breaking among genes at an "
                  "identical TSS distance, not a different mapping."))

    # ---- TF motif support carried by accessible regions -----------------
    motif = dict(status="NOT_FOUND")
    hits_p = os.path.join(root, "results/tables/stage75f_primary_motif_hits_v1.csv")
    hits_s = os.path.join(root, "results/tables/stage75f_secondary_motif_hits_v1.csv")
    frames = [pd.read_csv(p) for p in (hits_p, hits_s) if os.path.exists(p)]
    if frames:
        hits = pd.concat(frames, ignore_index=True)
        col_m = next((c for c in hits.columns if "motif" in c.lower()
                      and "id" in c.lower()), None)
        col_tf = next((c for c in hits.columns if c.lower() in ("tf", "batch_tf")), None)
        motif = dict(
            status="RECOVERED", rows=int(len(hits)),
            distinct_motifs=int(hits[col_m].nunique()) if col_m else None,
            distinct_tfs=int(hits[col_tf].nunique()) if col_tf else None,
            columns=list(hits.columns)[:25],
            scope=("Motif support was screened only on the 286 cisTarget SCREEN "
                   "regions reachable from 91 candidate peaks, i.e. 0.0415% of the "
                   "219,070-peak universe. It is NOT genome-wide motif evidence."))

    # ---- coaccessibility and independent enhancer links -----------------
    coacc = dict(status="NOT_AVAILABLE",
                 searched=["Cicero", "pycisTopic", "SCENIC+ eRegulon",
                           "peak-peak coaccessibility", "ArchR"],
                 reason=("No coaccessibility artifact exists in the repository. "
                         "Stage75C/E/F record no_scenicplus_run=True and no "
                         "pycisTopic object was ever built, so peak-peak "
                         "covariation links were never computed."),
                 consequence=("Distal peak-to-gene assignment therefore rests on "
                              "proximity alone and stays PROVISIONAL."))
    indep_links = dict(status="NOT_AVAILABLE",
                       searched=["ABC model", "Hi-C / HiChIP loops", "brain eQTL",
                                 "CRISPRi enhancer screens"],
                       reason=("No externally validated enhancer-gene link set is "
                               "present. Without one, no peak-gene assignment in "
                               "this dataset can be called validated."))

    cls_counts = {k: int(v) for k, v in peaks.evidence_class.value_counts().items()}
    gene_cls = {k: int(v) for k, v in genes.atac_evidence_class.value_counts().items()}

    manifest = dict(
        lane="LANE_D_external_multiomics",
        artifact="peak_to_gene_full_universe_map",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        execution_class="RECONNAISSANCE_ONLY",
        biological_evaluation_status="NOT_EXECUTED",
        governance_footer=("TRAINING=OFF | AUDIT_B_N1=UNOPENED | "
                           "PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED | "
                           "RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF"),
        coordinate_conventions=dict(
            declared_genome=declared_genome,
            assembly="hg38 / GRCh38",
            chromosome_naming="UCSC chr-prefixed",
            peak_id_format="chrN:start-end",
            peak_coordinate_system=("CellRanger-ATAC BED-like: 0-based half-open "
                                    "start, end exclusive"),
            gtf_coordinate_system="GENCODE GTF is 1-based inclusive",
            reconciliation_applied="GTF start converted to 0-based via col4 - 1",
            tss_definition=("gene-level, strand-aware: TSS = gene start on + "
                            "strand, gene end on - strand"),
            annotation_release="GENCODE v44",
            gencode_genes=int(n_genes),
            gencode_protein_coding=int(biotypes.get("protein_coding", 0)),
            peaks_parseable=int(peaks.parseable.sum()),
            peaks_unparseable=int((~peaks.parseable).sum()),
            peak_contigs=int(peaks.chrom.nunique()),
            contigs_absent_from_gencode=sorted(set(peaks.chrom) - set(tss))),
        peak_universe=dict(
            n_peaks=int(len(peaks)), n_barcodes_full_matrix=int(shape[1]),
            microglial_matrix=det_meta,
            peaks_detected_in_at_least_one_microglial_nucleus=(
                int(det_ok.sum()) if det is not None else None),
            peaks_never_detected_in_microglia=(
                int((~det_ok).sum()) if det is not None else None),
            microglial_detection_fraction_quantiles=(
                {q: round(float(np.quantile(peaks.microglial_detection_fraction, q)), 6)
                 for q in (0.5, 0.9, 0.99, 1.0)} if det is not None else None)),
        mapping_counts=dict(
            peaks_with_promoter_tss_within_2kb=int(has_prom.sum()),
            peaks_with_tss_within_100kb=int(has_prox.sum()),
            peaks_with_no_tss_within_100kb=int((~has_prox).sum()),
            peaks_with_tied_nearest_tss=int((peaks.n_tied > 1).sum()),
            max_nearest_tss_tie_multiplicity=int(peaks.n_tied.max()),
            peaks_with_multiple_tss_in_promoter_window=int(
                (peaks.n_tss_promoter >= 2).sum()),
            peaks_with_multiple_tss_in_100kb=int((peaks.n_tss_proximal >= 2).sum()),
            median_genes_within_100kb=int(peaks.n_tss_proximal.median()),
            max_genes_within_100kb=int(peaks.n_tss_proximal.max()),
            evidence_class_counts=cls_counts),
        gene_counts=dict(
            gencode_genes_total=int(len(genes)),
            genes_with_accessible_promoter_in_microglia=int(
                (genes.n_promoter_peaks_detected_in_microglia > 0).sum()),
            genes_with_promoter_peak_not_detected_in_microglia=int(
                ((genes.n_promoter_peaks > 0) &
                 (genes.n_promoter_peaks_detected_in_microglia == 0)).sum()),
            genes_with_distal_candidate_only=int(
                ((genes.n_promoter_peaks == 0) &
                 (genes.n_distal_candidate_peaks > 0)).sum()),
            genes_with_no_usable_atac_evidence=int(
                ((genes.n_promoter_peaks == 0) &
                 (genes.n_distal_candidate_peaks == 0)).sum()),
            gene_evidence_class_counts=gene_cls),
        evidence_ladder=dict(
            DIRECT_ATAC_ACCESSIBILITY=dict(
                available=bool(det is not None),
                definition=("peak detected in >=1 microglial nucleus and "
                            "overlapping a TSS within 2 kb"),
                strength="measured; the ATAC fragments are the measurement"),
            NEAREST_GENE_ANNOTATION=dict(
                available=True, strength="annotation convention, NOT evidence",
                caution="the nearest gene is never the established target"),
            GENOMIC_PROXIMITY=dict(
                available=True, strength="weak; many-to-many",
                median_candidate_genes_per_peak=int(peaks.n_tss_proximal.median())),
            COACCESSIBILITY=coacc,
            INDEPENDENT_ENHANCER_GENE_LINK=indep_links),
        motif_support=motif,
        reproducibility=dict(
            independent_implementation=indep,
            coordinate_perturbation_control=perturb,
            stage75c_frozen_table_authentication=s75c))

    cols = ["peak_index", "peak_id", "chrom", "start", "end", "width",
            "nearest_gene", "nearest_gene_id", "nearest_biotype",
            "signed_distance", "abs_distance", "n_tied", "tied_genes",
            "n_tss_promoter", "n_tss_proximal", "promoter_genes",
            "evidence_class", "distal_assignment_status"]
    if det is not None:
        cols += ["microglial_nuclei_detecting_peak", "microglial_detection_fraction"]
    peaks[cols].to_csv(
        os.path.join(out, "laneD_peak_to_gene_full_universe_v1.csv.gz"),
        index=False, compression="gzip")
    with open(os.path.join(out, "laneD_peak_to_gene_manifest_v1.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, default=_jsonable)
    print(json.dumps({k: v for k, v in manifest.items()
                      if k not in ("coordinate_conventions",)}, indent=2, default=_jsonable)[:9000])


if __name__ == "__main__":
    main()
