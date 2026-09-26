#!/usr/bin/env python
"""AGENT 5 - read-only preparatory analysis for the independent Morabito
(GSE174367) RNA/ATAC benchmark of frozen JEPA states.

WHAT THIS IS
    Preparatory reconnaissance only. It computes the quantities the benchmark
    DESIGN needs in order to be written honestly: how many independent
    biological units exist, which covariates are actually deposited, whether a
    cell-level RNA-ATAC join is possible, whether Stage75F is independent of
    this data, and whether the GSE174367 donors overlap the FULL104 cohort.

WHAT THIS IS NOT
    It executes no biological evaluation of any JEPA state. No model is loaded.
    No frozen representation is scored. Every biological outcome in the
    protocol is NOT_EXECUTED.

GOVERNANCE
    TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED |
    D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF

    Reads only: public GEO deposit GSE174367, the repository's own frozen
    Stage75F tables, and the FULL104 donor-identity registry (identifiers and
    tissue state only). Reads no SEA-AD pathology column, no sealed
    confirmation outcome, no terminal masking result, no D_shared artifact.
"""
import argparse
import hashlib
import json
import math
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

FOOTER = ("TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED | "
          "D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF")

RNA_META = "data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz"
ATAC_META = "data/external/gse174367/GSE174367_snATAC-seq_cell_meta.csv.gz"
RNA_H5 = "data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5"
ATAC_H5 = "data/external/gse174367/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5"
SERIES_MATRIX = "data/external/public_schema_audit/GSE174367/GSE174367_series_matrix.txt.gz"
S75_TF_TARGET = "results/tables/stage75_integrated_tf_target_summary_v1.csv"
S75_REGULATOR = "results/tables/stage75_integrated_regulator_summary_v1.csv"
S75_NEG_GATE = "results/tables/stage75_integrated_negative_regulator_gate_v1.csv"
DONOR_REGISTRY = "results/v4/stage81a2_global_donor_registry.csv"

CELL_TYPE_OF_INTEREST = "MG"

# Sample-level covariates that the deposit repeats on every cell of a sample.
# Anything in this list is a DONOR-level variable with 1 independent value per
# sample, not a cell-level variable, however many cell rows carry it.
DECLARED_SAMPLE_LEVEL_FIELDS = [
    "Diagnosis", "Batch", "Age", "Sex", "PMI", "Tangle.Stage", "Plaque.Stage", "RIN",
]


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# --------------------------------------------------------------- 1. inputs

def authenticate_inputs(root, heavy_digests):
    """Record what was actually read. Heavy matrices are digested only when
    explicitly requested; otherwise the digest field says so rather than
    inventing a value."""
    rows = []
    for rel, heavy in [(RNA_META, False), (ATAC_META, False), (SERIES_MATRIX, False),
                       (RNA_H5, True), (ATAC_H5, True),
                       (S75_TF_TARGET, False), (S75_REGULATOR, False),
                       (S75_NEG_GATE, False), (DONOR_REGISTRY, False)]:
        p = os.path.join(root, rel)
        exists = os.path.exists(p)
        if not exists:
            digest = None
            status = "ABSENT"
        elif heavy and not heavy_digests:
            digest = "NOT_MEASURED_THIS_RUN__HEAVY_DIGEST_DISABLED"
            status = "PRESENT_DIGEST_NOT_MEASURED"
        else:
            digest = sha256_file(p)
            status = "PRESENT_DIGEST_MEASURED"
        rows.append(dict(relative_path=rel, exists=bool(exists),
                         size_bytes=(os.path.getsize(p) if exists else None),
                         sha256=digest, status=status,
                         read_by_this_script=bool(exists)))
    return pd.DataFrame(rows)


# ------------------------------------------- 2. sample-level overlap register

def build_sample_register(rna, atac):
    samples = sorted(set(rna.SampleID) | set(atac.SampleID),
                     key=lambda x: int(x.split("-")[1]))
    rows = []
    for s in samples:
        r = rna[rna.SampleID == s]
        a = atac[atac.SampleID == s]
        src = r if len(r) else a
        rows.append(dict(
            sample_id=s,
            in_rna_deposit=bool(len(r)),
            in_atac_deposit=bool(len(a)),
            rna_cells_all_types=int(len(r)),
            atac_cells_all_types=int(len(a)),
            rna_microglia_cells=int((r["Cell.Type"] == CELL_TYPE_OF_INTEREST).sum()),
            atac_microglia_cells=int((a["Cell.Type"] == CELL_TYPE_OF_INTEREST).sum()),
            diagnosis=str(src.Diagnosis.iloc[0]),
            age_years_capped=int(src.Age.iloc[0]),
            sex=str(src.Sex.iloc[0]),
            pmi_hours=(None if pd.isna(src.PMI.iloc[0]) else float(src.PMI.iloc[0])),
            rin=(None if pd.isna(src.RIN.iloc[0]) else float(src.RIN.iloc[0])),
            tangle_stage=str(src["Tangle.Stage"].iloc[0]),
            plaque_stage=str(src["Plaque.Stage"].iloc[0]),
            rna_batch=(int(r.Batch.iloc[0]) if len(r) else None),
            atac_batch=(int(a.Batch.iloc[0]) if len(a) else None),
            in_both_modalities=bool(len(r) and len(a)),
            admissible_join_level="SAMPLE_DONOR_ONLY",
            cell_level_pairing="NONE_IN_DEPOSIT",
        ))
    tbl = pd.DataFrame(rows)

    # A shared SampleID must mean the same person in both assays, or the
    # sample-level join is invalid. Disagreement on any donor covariate would
    # falsify that.
    cov = ["Age", "Sex", "PMI", "Tangle.Stage", "Plaque.Stage", "Diagnosis",
           "RIN", "Batch"]
    r1 = rna[["SampleID"] + cov].drop_duplicates()
    a1 = atac[["SampleID"] + cov].drop_duplicates()
    merged = r1.merge(a1, on="SampleID", suffixes=("_rna", "_atac"))
    mismatch = {c: int((merged[c + "_rna"].astype(str)
                        != merged[c + "_atac"].astype(str)).sum()) for c in cov}
    return tbl, mismatch, int(len(merged))


# ------------------------------------------- 3. cell-level pairing falsifier

def pairing_falsifier(rna, atac):
    """Attempt, and record the failure of, every cell-level join that a careless
    pipeline might try. This is written to FAIL LOUDLY if a genuine cell-level
    correspondence ever appears in a future deposit revision."""
    rb, ab = set(rna.Barcode), set(atac.Barcode)
    raw_overlap = rb & ab

    # A 10x barcode is <16-mer>-<GEM group>. The 16-mer is the physical bead
    # sequence; the integer suffix is assigned per aggregation run and is
    # therefore assay-local.
    r16 = set(b.rsplit("-", 1)[0] for b in rb)
    a16 = set(b.rsplit("-", 1)[0] for b in ab)
    shared16 = r16 & a16

    # If both assays drew from one shared 737,280-barcode whitelist, the
    # expected 16-mer intersection under independence is |R|*|A|/737280.
    whitelist = 737280
    expected16 = len(r16) * len(a16) / whitelist

    # Where a raw barcode string does coincide, does it name the same sample?
    rmap = dict(zip(rna.Barcode, rna.SampleID))
    amap = dict(zip(atac.Barcode, atac.SampleID))
    collisions = [dict(barcode=b, rna_sample=rmap[b], atac_sample=amap[b],
                       same_sample=bool(rmap[b] == amap[b]))
                  for b in sorted(raw_overlap)]
    n_same = sum(1 for c in collisions if c["same_sample"])

    # The GEM-group suffix itself: does suffix k mean the same sample in both?
    rsuf = (rna.assign(suf=rna.Barcode.str.rsplit("-", n=1).str[1])
               .groupby("suf").SampleID.agg(lambda s: sorted(set(s))))
    asuf = (atac.assign(suf=atac.Barcode.str.rsplit("-", n=1).str[1])
                .groupby("suf").SampleID.agg(lambda s: sorted(set(s))))
    shared_suf = sorted(set(rsuf.index) & set(asuf.index), key=int)
    suffix_agreement = {k: bool(rsuf[k] == asuf[k]) for k in shared_suf}

    return dict(
        verdict="NO_CELL_LEVEL_RNA_ATAC_PAIRING_EXISTS",
        assay_design="separate_nuclei_separate_libraries_not_multiome",
        rna_barcodes=len(rb), atac_barcodes=len(ab),
        raw_barcode_string_overlap=len(raw_overlap),
        raw_overlap_same_sample=n_same,
        raw_overlap_different_sample=len(raw_overlap) - n_same,
        raw_overlap_examples=collisions[:10],
        stripped_16mer_overlap=len(shared16),
        rna_unique_16mers=len(r16), atac_unique_16mers=len(a16),
        expected_16mer_overlap_if_shared_whitelist=round(expected16, 1),
        observed_over_expected_16mer=round(len(shared16) / expected16, 6),
        gem_suffixes_shared=len(shared_suf),
        gem_suffixes_where_same_integer_means_same_sample=int(sum(suffix_agreement.values())),
        admissible_join_keys=["SampleID"],
        forbidden_join_keys=["Barcode", "barcode_16mer", "gem_group_suffix",
                             "row_position", "cell_index"],
        note=("The only key that means the same physical thing in both assays is "
              "SampleID. Every barcode-derived key is assay-local. A cell-level "
              "RNA-ATAC join would fabricate a measurement that was never made."),
    )


# -------------------------------------------------- 4. effective replication

def kish_effective_clusters(counts):
    """Effective NUMBER OF SAMPLES when a per-sample quantity is formed by
    equally weighting cells. Not a cell count."""
    c = np.asarray(counts, dtype=float)
    c = c[c > 0]
    if c.size == 0:
        return None
    return float(c.sum() ** 2 / (c ** 2).sum())


def binomial_sf(k, n, p=0.5):
    """P(X >= k) for Binomial(n, p), exact."""
    return float(sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i)
                     for i in range(k, n + 1)))


def sign_consistency_critical(n, alpha=0.05):
    for k in range(n, 0, -1):
        if binomial_sf(k, n) > alpha:
            return dict(n=n, critical_k=k + 1, achieved_alpha=binomial_sf(k + 1, n),
                        alpha_target=alpha)
    return dict(n=n, critical_k=None, achieved_alpha=None, alpha_target=alpha)


def fisher_z_mde(n, alpha=0.05, power=0.80):
    """Smallest |rho| detectable with the stated power, two-sided, Fisher-z."""
    if n <= 3:
        return None
    from statistics import NormalDist
    za = NormalDist().inv_cdf(1 - alpha / 2)
    zb = NormalDist().inv_cdf(power)
    z = (za + zb) / math.sqrt(n - 3)
    return float(math.tanh(z))


def paired_d_mde(n, alpha=0.05, power=0.80):
    from statistics import NormalDist
    za = NormalDist().inv_cdf(1 - alpha / 2)
    zb = NormalDist().inv_cdf(power)
    return float((za + zb) / math.sqrt(n))


def deff_table(mean_cluster_size, iccs=(0.0, 0.01, 0.05, 0.10, 0.25, 0.50)):
    """Design effect for cluster sampling. ICC is NOT measured here; this is a
    sensitivity table, not a result."""
    out = []
    for icc in iccs:
        deff = 1.0 + (mean_cluster_size - 1.0) * icc
        out.append(dict(assumed_icc=icc, design_effect=round(deff, 4),
                        status="ASSUMED_NOT_MEASURED"))
    return out


def replication_block(register):
    rna = register[register.in_rna_deposit]
    atac = register[register.in_atac_deposit]
    both = register[register.in_both_modalities]

    rna_mg = rna.rna_microglia_cells.values
    atac_mg = atac.atac_microglia_cells.values
    both_atac_mg = both.atac_microglia_cells.values

    def block(label, n_units, counts):
        counts = np.asarray(counts, dtype=float)
        return dict(
            stratum=label,
            independent_units_n=int(n_units),
            independent_unit_definition="one postmortem donor sample (SampleID)",
            total_cells=int(counts.sum()),
            cells_per_unit_min=int(counts.min()) if counts.size else None,
            cells_per_unit_median=float(np.median(counts)) if counts.size else None,
            cells_per_unit_max=int(counts.max()) if counts.size else None,
            cells_per_unit_mean=round(float(counts.mean()), 3) if counts.size else None,
            kish_effective_number_of_units=round(kish_effective_clusters(counts), 4),
            cell_level_effective_sample_size="UNKNOWN__REQUIRES_ICC_OF_THE_SCORED_STATISTIC",
            cell_level_ess_formula="ESS_cells = total_cells / (1 + (mean_cells_per_unit - 1) * ICC)",
            design_effect_sensitivity=deff_table(float(counts.mean())) if counts.size else None,
            sign_consistency_alpha05=sign_consistency_critical(int(n_units)),
            spearman_mde_power80=round(fisher_z_mde(int(n_units)), 4),
            paired_cohens_d_mde_power80=round(paired_d_mde(int(n_units)), 4),
        )

    return dict(
        rna_microglia=block("rna_microglia_all_deposited_samples", len(rna), rna_mg),
        atac_microglia=block("atac_microglia_all_deposited_samples", len(atac), atac_mg),
        atac_microglia_shared_only=block(
            "atac_microglia_restricted_to_samples_with_rna", len(both), both_atac_mg),
        cross_modality=dict(
            stratum="rna_atac_sample_level_join",
            independent_units_n=int(len(both)),
            independent_unit_definition="one donor sample present in BOTH assays",
            note=("Cross-modality statistics have n = number of shared samples. "
                  "The 4,126 RNA nuclei and the 10,944 ATAC nuclei on those samples "
                  "reduce the measurement error of each sample's summary; they do "
                  "not add independent subjects."),
            sign_consistency_alpha05=sign_consistency_critical(int(len(both))),
            spearman_mde_power80=round(fisher_z_mde(int(len(both))), 4),
            paired_cohens_d_mde_power80=round(paired_d_mde(int(len(both))), 4),
        ),
    )


# ------------------------------------ 5. permutation-space adequacy for N1

def restricted_permutation_space(register, strata_fields):
    """A restricted permutation control cannot produce a p-value smaller than
    1/(number of distinct restricted permutations). If that floor is above the
    acceptance alpha, the control is unusable and must be redesigned."""
    both = register[register.in_both_modalities]
    out = {}
    for name, fields in strata_fields.items():
        if not fields:
            sizes = [len(both)]
        else:
            sizes = both.groupby(list(fields)).size().tolist()
        total = 1
        for s in sizes:
            total *= math.factorial(int(s))
        # Permutations that leave every unit in place are not informative.
        floor_p = 1.0 / total if total > 0 else 1.0
        # A stratum of size 1 pins its unit: that sample's label can never move,
        # so the control cannot challenge it at all.
        fixed = int(sum(1 for s in sizes if int(s) == 1))
        movable = int(sum(int(s) for s in sizes if int(s) > 1))
        out[name] = dict(
            strata_fields=list(fields),
            n_strata=len(sizes),
            stratum_sizes=sorted(int(s) for s in sizes),
            n_distinct_restricted_permutations=int(total) if total < 10 ** 18 else "GT_1E18",
            minimum_attainable_permutation_p=(floor_p if floor_p > 1e-12
                                              else "LT_1E-12"),
            adequate_for_alpha_0p05=bool(floor_p <= 0.05),
            units_pinned_by_a_singleton_stratum=fixed,
            units_that_can_actually_move=movable,
            fraction_of_units_exchangeable=round(
                movable / float(sum(int(s) for s in sizes)), 4) if sizes else None,
            vacuity_warning=("PARTIALLY_VACUOUS__SOME_UNITS_CANNOT_MOVE" if fixed
                             else "ALL_UNITS_EXCHANGEABLE_WITHIN_STRATUM"),
        )
    return out


# --------------------------------------------- 6. covariate availability

def covariate_audit(rna, atac):
    """Which baseline covariates actually exist in the deposit, at which level.
    A baseline specification that names a column the deposit does not have is
    not a specification."""
    rows = []
    for assay, df, sample_key in [("snRNA", rna, "SampleID"), ("snATAC", atac, "SampleID")]:
        for col in df.columns:
            per_sample_unique = df.groupby(sample_key)[col].nunique(dropna=False)
            constant_within_sample = bool((per_sample_unique <= 1).all())
            level = ("sample_level" if constant_within_sample and col != sample_key
                     else ("identity_key" if col in (sample_key, "Barcode")
                           else "cell_level"))
            rows.append(dict(
                assay=assay, column=col, dtype=str(df[col].dtype),
                n_unique=int(df[col].nunique(dropna=False)),
                n_missing=int(df[col].isna().sum()),
                varies_within_sample=not constant_within_sample,
                variable_level=level,
                usable_as_cell_level_technical_covariate=bool(
                    level == "cell_level" and col not in ("cluster", "Cell.Type")),
            ))
    tbl = pd.DataFrame(rows)

    deposited_cell_level = sorted(set(
        tbl[(tbl.variable_level == "cell_level")].column))
    missing_expected = [c for c in ["nUMI", "nCount_RNA", "nFeature_RNA", "nGene",
                                    "percent.mt", "percent.mito", "nCount_peaks",
                                    "nFragments", "FRiP", "TSS_enrichment",
                                    "nucleosome_signal", "blacklist_ratio",
                                    "doublet_score"]
                        if c not in set(tbl.column)]
    return tbl, dict(
        cell_level_columns_present=deposited_cell_level,
        standard_qc_columns_absent_from_deposit=missing_expected,
        consequence=("No sequencing-depth, detection-rate, mitochondrial-fraction, "
                     "FRiP, TSS-enrichment or doublet column is deposited. The "
                     "technical-only baseline B1 therefore CANNOT be built from the "
                     "cell metadata; every technical covariate must be recomputed "
                     "from the count matrices themselves (column sum = depth, "
                     "column nnz = detection) under a rule frozen in advance."),
        sample_level_fields_declared=DECLARED_SAMPLE_LEVEL_FIELDS,
        sample_level_fields_confirmed=sorted(set(
            tbl[(tbl.variable_level == "sample_level")].column)),
    )


# --------------------------------------------------- 7. Stage75F circularity

def stage75f_circularity(root):
    p = os.path.join(root, S75_TF_TARGET)
    if not os.path.exists(p):
        return dict(status="STAGE75F_TABLE_ABSENT", independence="UNKNOWN")
    t = pd.read_csv(p)
    reg = pd.read_csv(os.path.join(root, S75_REGULATOR))
    neg = pd.read_csv(os.path.join(root, S75_NEG_GATE))

    edge_types = {k: int(v) for k, v in t.edge_edge_type.value_counts().items()}
    n_samples = {str(k): int(v) for k, v in t.edge_n_samples.value_counts().items()}
    derived_from_same_rna = bool(
        set(t.edge_edge_type.unique()) == {"microglia_snrna_sample_coactivity"})

    return dict(
        stage75f_rows=int(len(t)),
        stage75f_regulators_in_summary=int(len(reg)),
        stage75f_negative_gate_regulators=int(len(neg)),
        stage75f_tfs_with_edges=int(t.tf.nunique()),
        stage75f_tf_list=sorted(t.tf.unique().tolist()),
        stage75f_unique_target_genes=int(t.target_gene.nunique()),
        stage75f_rows_per_tf={k: int(v) for k, v in t.tf.value_counts().items()},
        edge_type_counts=edge_types,
        edge_n_samples_counts=n_samples,
        edge_atac_support_status={k: int(v) for k, v in
                                  t.edge_atac_peak_support_status.value_counts().items()},
        edge_motif_support_status={k: int(v) for k, v in
                                   t.edge_motif_support_status.value_counts().items()},
        peak_gene_class_counts={k: int(v) for k, v in
                                t.peak_gene_classes.value_counts().items()},
        evidence_tier_counts={k: int(v) for k, v in
                              t.evidence_tier.value_counts().items()},
        abs_spearman_rho=dict(
            min=round(float(t.edge_spearman_rho.abs().min()), 6),
            median=round(float(t.edge_spearman_rho.abs().median()), 6),
            max=round(float(t.edge_spearman_rho.abs().max()), 6)),
        edges_derived_from_gse174367_rna=derived_from_same_rna,
        independence_verdict=("NON_INDEPENDENT__DERIVED_FROM_THE_SAME_GSE174367_"
                              "MICROGLIAL_RNA_SAMPLES" if derived_from_same_rna
                              else "UNKNOWN__EDGE_PROVENANCE_NOT_UNIFORM"),
        independence_basis=(
            "Every Stage75F TF-target row records edge_edge_type="
            "'microglia_snrna_sample_coactivity' over edge_n_samples=18. Those are "
            "the same 18 GSE174367 snRNA samples and the same 4,126 microglial "
            "nuclei that this benchmark would evaluate. The candidate regions were "
            "selected from the same GSE174367 snATAC microglia. Stage75F therefore "
            "shares both its RNA and its ATAC substrate with the proposed "
            "validation data and cannot be an independent outcome for it."),
        permitted_use=("PRIOR_ONLY__EVERY_ASSESSMENT_USING_IT_MARKED_NON_INDEPENDENT"),
        forbidden_use=("May not define the target representation and then be scored "
                       "as an independent validation outcome; may not contribute to "
                       "any PASS verdict."),
    )


# ------------------------------------------------- 8. FULL104 donor overlap

def full104_overlap(root, register):
    p = os.path.join(root, DONOR_REGISTRY)
    if not os.path.exists(p):
        return dict(status="DONOR_REGISTRY_ABSENT",
                    donor_identity_overlap="UNKNOWN")
    d = pd.read_csv(p)
    core = d[d.tissue_state != "adapter_or_validation"]
    adapter = d[d.tissue_state == "adapter_or_validation"]

    gse_ids = set(register.sample_id.astype(str))
    core_ids = set(core.canonical_person_id.astype(str))
    core_src = set(core.source_donor_id.astype(str))
    all_ids = set(d.canonical_person_id.astype(str))

    # Direct string overlap on every identifier column in the registry.
    string_hits = {}
    for col in d.columns:
        vals = set(d[col].astype(str))
        hit = sorted(vals & gse_ids)
        if hit:
            string_hits[col] = hit

    series_in_registry = sorted({s for s in d.study_id.astype(str)
                                 if "174367" in s} |
                                {s for s in d.partition_id.astype(str)
                                 if "174367" in s})

    return dict(
        registry_path=DONOR_REGISTRY,
        registry_rows=int(len(d)),
        registry_unique_persons=int(d.canonical_person_id.nunique()),
        full104_parent_cohort_persons=int(core.canonical_person_id.nunique()),
        full104_parent_cohort_by_study={k: int(v) for k, v in
                                        core.groupby("study_id").canonical_person_id
                                        .nunique().items()},
        full104_parent_cohort_by_tissue_state={k: int(v) for k, v in
                                               core.groupby("tissue_state")
                                               .canonical_person_id.nunique().items()},
        adapter_or_validation_studies=sorted(set(adapter.study_id.astype(str))),
        gse174367_present_as_a_registered_study=bool(series_in_registry),
        gse174367_registry_study_hits=series_in_registry,
        gse174367_sample_ids=sorted(gse_ids),
        identifier_string_overlap_any_column=string_hits,
        n_identifier_string_overlaps=int(sum(len(v) for v in string_hits.values())),
        full104_donor_id_namespace_examples=sorted(core_src.__iter__())[:5],
        full104_canonical_id_namespace_examples=sorted(core_ids)[:5],
        namespaces_disjoint=bool(not (gse_ids & all_ids)),
        exact_donor_identity_overlap="UNTESTABLE_FROM_DEPOSIT",
        exact_donor_identity_overlap_reason=(
            "GEO supplies no donor identifier for GSE174367 - only the within-series "
            "labels Sample-17 .. Sample-101 and de-identified age/sex/PMI/RIN. There "
            "is no key on which an exact person-level match to a FULL104 donor could "
            "be computed, in either direction. The correct value is UNKNOWN, not "
            "zero."),
        residual_overlap_risk="UNKNOWN_BUT_LOW_ON_PROVENANCE_GROUNDS",
        provenance_evidence=dict(
            gse174367_contact_institute="University of California Irvine",
            gse174367_pubmed_id="34239132",
            gse174367_tissue="postmortem frozen prefrontal/frontal cortex (FC)",
            full104_sources=["SEA_AD (postmortem brain)",
                             "HVS (living surgical cortex)",
                             "NPH52 (living NPH cortex)"],
            argument=("Different brain banks, different accession namespaces, and "
                      "GSE174367 does not appear anywhere in the project's donor "
                      "registry - including its adapter/validation study list.")),
    )


# ------------------------------------------------- 9. biological context gap

def biological_context_register(root, register):
    rna_reg = register[register.in_rna_deposit]
    atac_reg = register[register.in_atac_deposit]
    return dict(
        benchmark_cohort=dict(
            accession="GSE174367",
            region="frontal / prefrontal cortex (FC) only",
            tissue_state="postmortem frozen",
            isolation="unbiased total nuclei isolation",
            rna_platform="10x Chromium Single Cell 3' v3, GRCh38.p12 pre-mRNA reference",
            atac_platform="10x Chromium Single Cell ATAC v1, hg38, cellranger-atac 1.1.0",
            diagnosis_levels=sorted(set(register.diagnosis)),
            rna_diagnosis_counts={k: int(v) for k, v in
                                  rna_reg.diagnosis.value_counts().items()},
            atac_diagnosis_counts={k: int(v) for k, v in
                                   atac_reg.diagnosis.value_counts().items()},
            age_range_years=[int(register.age_years_capped.min()),
                             int(register.age_years_capped.max())],
            age_is_capped_at_90=bool((register.age_years_capped == 90).any()),
            sex_counts={k: int(v) for k, v in register.sex.value_counts().items()},
            tangle_stages=sorted(set(register.tangle_stage)),
            plaque_stages=sorted(set(register.plaque_stage)),
            severity_coverage="late-stage AD versus control; no intermediate arm",
        ),
        training_cohort=dict(
            name="FULL104",
            regions=("SEA-AD multi-region cortex and caudate (MTG, ANG, DFC, HIP, "
                     "MEC, LEC, ITG, STG, V1C, FI, CaH); HVS and NPH52 living "
                     "cortex"),
            tissue_state="mixed postmortem and living surgical",
            design_intent=("deliberately mixed - healthy, pathological aging and AD, "
                           "living and postmortem, many platforms"),
        ),
        context_differences_that_bound_the_claim=[
            dict(axis="brain_region",
                 difference="benchmark is frontal cortex only; FULL104 is multi-region",
                 consequence=("Microglial state is regionally patterned. A negative "
                              "result may reflect region transfer, not absence of "
                              "cellular-state information.")),
            dict(axis="tissue_state",
                 difference=("benchmark is entirely postmortem; FULL104 contains "
                             "living surgical and NPH cortex"),
                 consequence=("Microglia are the cell type most altered by "
                              "postmortem interval and by surgical handling. A "
                              "model fitted across both states may transport "
                              "poorly in either direction for reasons that are "
                              "not disease biology.")),
            dict(axis="disease_severity",
                 difference="benchmark is late-stage AD vs control, binary",
                 consequence=("The benchmark cannot test graded or early pathology "
                              "and cannot support any claim about a continuum.")),
            dict(axis="assay_chemistry",
                 difference=("10x 3' v3 pre-mRNA reference here; FULL104 includes "
                             "10x Multiome and other chemistries"),
                 consequence=("Detection-rate and intronic-read differences are a "
                              "technical axis that the technical-only baseline B1 "
                              "must absorb before any biological claim.")),
            dict(axis="annotation_vocabulary",
                 difference=("GRCh38.p12 pre-mRNA reference here; Stage81A2R "
                             "Ensembl identity layer for FULL104"),
                 consequence=("Non-overlapping addresses are missing by design and "
                              "must never be imputed as zero.")),
        ],
    )


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--heavy-digests", action="store_true",
                    help="also SHA-256 the two multi-hundred-MB matrices")
    args = ap.parse_args()
    root, out = args.repo_root, args.out_dir
    os.makedirs(out, exist_ok=True)

    rna = pd.read_csv(os.path.join(root, RNA_META))
    atac = pd.read_csv(os.path.join(root, ATAC_META)).rename(
        columns={"Sample.ID": "SampleID"})

    inputs = authenticate_inputs(root, args.heavy_digests)
    inputs.to_csv(os.path.join(out, "agent5_input_authentication_v1.csv"), index=False)

    register, cov_mismatch, n_shared_cov = build_sample_register(rna, atac)
    register.to_csv(os.path.join(out, "agent5_sample_overlap_register_v1.csv"),
                    index=False)

    cov_tbl, cov_summary = covariate_audit(rna, atac)
    cov_tbl.to_csv(os.path.join(out, "agent5_covariate_availability_v1.csv"),
                   index=False)

    perm = restricted_permutation_space(register, {
        "unrestricted": (),
        "within_batch": ("rna_batch",),
        "within_diagnosis": ("diagnosis",),
        "within_batch_and_diagnosis": ("rna_batch", "diagnosis"),
        "within_batch_diagnosis_sex": ("rna_batch", "diagnosis", "sex"),
    })

    manifest = dict(
        agent="AGENT_5_biological_validation_and_jepa_comparison_design",
        artifact="morabito_gse174367_benchmark_preparatory_reconnaissance_v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        repo_root=root,
        governance_footer=FOOTER,
        execution_class="READ_ONLY_PREPARATORY_ANALYSIS",
        biological_evaluation_status="NOT_EXECUTED",
        model_loaded=False,
        frozen_state_scored=False,
        protected_outcomes_touched=False,
        input_authentication=json.loads(inputs.to_json(orient="records")),
        sample_overlap=dict(
            samples_total=int(len(register)),
            rna_samples=int(register.in_rna_deposit.sum()),
            atac_samples=int(register.in_atac_deposit.sum()),
            shared_samples=int(register.in_both_modalities.sum()),
            rna_only_samples=sorted(register.loc[
                register.in_rna_deposit & ~register.in_atac_deposit,
                "sample_id"].tolist()),
            atac_only_samples=sorted(register.loc[
                register.in_atac_deposit & ~register.in_rna_deposit,
                "sample_id"].tolist()),
            rna_cells_all_types=int(register.rna_cells_all_types.sum()),
            atac_cells_all_types=int(register.atac_cells_all_types.sum()),
            rna_microglia_cells=int(register.rna_microglia_cells.sum()),
            atac_microglia_cells=int(register.atac_microglia_cells.sum()),
            atac_microglia_cells_on_shared_samples=int(
                register.loc[register.in_both_modalities,
                             "atac_microglia_cells"].sum()),
            donor_covariate_rows_compared=n_shared_cov,
            donor_covariate_mismatches=cov_mismatch,
            sample_id_is_a_valid_donor_key=bool(sum(cov_mismatch.values()) == 0),
        ),
        cell_level_pairing=pairing_falsifier(rna, atac),
        effective_replication=replication_block(register),
        restricted_permutation_adequacy=perm,
        covariate_availability=cov_summary,
        stage75f_circularity=stage75f_circularity(root),
        full104_donor_overlap=full104_overlap(root, register),
        biological_context=biological_context_register(root, register),
        artifacts=[
            "agent5_input_authentication_v1.csv",
            "agent5_sample_overlap_register_v1.csv",
            "agent5_covariate_availability_v1.csv",
            "agent5_preparatory_manifest_v1.json",
        ],
    )

    mp = os.path.join(out, "agent5_preparatory_manifest_v1.json")
    with open(mp, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=False)
    print(json.dumps(dict(
        wrote=mp,
        shared_samples=manifest["sample_overlap"]["shared_samples"],
        rna_microglia=manifest["sample_overlap"]["rna_microglia_cells"],
        atac_microglia=manifest["sample_overlap"]["atac_microglia_cells"],
        stage75f=manifest["stage75f_circularity"]["independence_verdict"],
        full104=manifest["full104_donor_overlap"]["exact_donor_identity_overlap"],
    ), indent=2))


if __name__ == "__main__":
    main()
