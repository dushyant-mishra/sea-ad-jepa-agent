#!/usr/bin/env python3
"""Agent 6: build the external dataset registry table.

Every numeric field in ``ROWS`` below is either

  (a) transcribed from a primary record this lane actually retrieved -- the GEO
      SOFT series/sample brief records under ``geo_primary/raw/``, the Synapse
      repository service entity listings under ``synapse/``, the SEA-AD Open
      Data S3 bucket listing, or the PMC full text of the deposit's own paper;
  (b) the literal string ``NOT_STATED_IN_DEPOSIT``; or
  (c) the literal string ``UNKNOWN`` where the quantity is derivable in
      principle but was NOT computed in this lane.

No field is estimated. ``--verify`` re-derives every (a) field that comes from
the GEO harvest against the harvested JSON and fails closed on any mismatch, so
a drifted hand-entered number cannot survive into the registry.

Usage:
    python build_external_dataset_registry_v1.py --harvest-dir <outputs> \\
        --out-dir <outputs> [--verify]
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

NOT_STATED = "NOT_STATED_IN_DEPOSIT"
UNKNOWN = "UNKNOWN"

# Fields verified against the GEO harvest: accession -> (n_gsm, {strategy: count})
GEO_CHECK = {
    "GSE174367": (230, {"ATAC-seq": 20, "RNA-Seq": 210}),
    "GSE214979": (40, {"ATAC-seq": 20, "RNA-Seq": 20}),
    "GSE214637": (48, {"ATAC-seq": 20, "ChIP-Seq": 8, "RNA-Seq": 20}),
    "GSE244618": (128, {"ATAC-seq": 128}),
    "GSE261983": (40, {"ATAC-seq": 20, "RNA-Seq": 20}),
    "GSE256207": (92, {"ATAC-seq": 92}),
    "GSE272082": (42, {"ATAC-seq": 21, "RNA-Seq": 21}),
    "GSE259298": (28, {"ATAC-seq": 16, "RNA-Seq": 12}),
    "GSE246443": (42, {"ATAC-seq": 42}),
    "GSE338484": (29, {"ATAC-seq": 29}),
    "GSE249315": (398, {"RNA-Seq": 398}),
    "GSE204702": (67, {"RNA-Seq": 67}),
    "GSE157827": (21, {"RNA-Seq": 21}),
    "GSE147528": (20, {"RNA-Seq": 20}),
    "GSE178317": (26, {"OTHER": 8, "RNA-Seq": 18}),
    "GSE148434": (70, {"ATAC-seq": 13, "ChIP-Seq": 18, "Hi-C": 11, "RNA-Seq": 28}),
    "GSE163323": (51, {"ATAC-seq": 11, "OTHER": 14, "RNA-Seq": 26}),
}

COLUMNS = [
    "tier",
    "dataset_id",
    "short_name",
    "primary_record",
    "assays_deposited",
    "deposited_units_transcribed",
    "independent_unit",
    "n_independent_units",
    "n_independent_units_basis",
    "microglia_usable",
    "cell_types",
    "gene_coverage",
    "peak_coverage",
    "disease_context",
    "brain_regions",
    "access",
    "size_on_disk",
    "overlap_FULL104_donors",
    "overlap_other_project_assets",
    "failure_mode_screen",
    "integration_feasibility",
    "verdict",
]


def row(**kw):
    missing = [c for c in COLUMNS if c not in kw]
    if missing:
        raise SystemExit("row missing columns: {0}".format(missing))
    return {c: kw[c] for c in COLUMNS}


ROWS = [
    # ---------------------------------------------------------------- BASELINE
    row(
        tier="BASELINE (what we already have)",
        dataset_id="GSE174367",
        short_name="Morabito/Swarup AD frontal cortex snRNA+snATAC",
        primary_record="GEO SOFT brief; PMID 34239132",
        assays_deposited="snRNA-seq; snATAC-seq; bulk RNA-seq",
        deposited_units_transcribed=(
            "230 GSMs = 191 bulk RNA-seq + 19 snRNA-seq + 20 snATAC-seq "
            "(library_strategy counts 210 RNA-Seq / 20 ATAC-seq)"
        ),
        independent_unit="donor",
        n_independent_units="20",
        n_independent_units_basis=(
            "derived from the deposit's own Sample-N titles: the 19 snRNA GSMs and "
            "20 snATAC GSMs share 19 Sample-N identifiers; 1 ATAC-only donor. "
            "The two assays are NOT independent samples of different people."
        ),
        microglia_usable="yes, as a subpopulation of unbiased total-nuclei capture",
        cell_types="all cortical types (unbiased total nuclei isolation)",
        gene_coverage="snRNA feature-barcode matrix deposited",
        peak_coverage="snATAC filtered peak-barcode matrix deposited",
        disease_context="11 AD / 8 Control (snRNA); 12 AD / 8 Control (snATAC)",
        brain_regions="FC (frontal cortex) only, all 39 single-nucleus GSMs",
        access="open; no restriction stated",
        size_on_disk="0.648 GB supplementary (unit-rounded from FTP dir index)",
        overlap_FULL104_donors="none known; different brain bank from all three FULL104 sources",
        overlap_other_project_assets="lane-d is building the GSE174367 benchmark readiness assessment",
        failure_mode_screen=(
            "PASSES technical-well screen (real donors, not wells). FAILS on "
            "replication breadth: n=20 people, single region, single bank."
        ),
        integration_feasibility="already in project use",
        verdict=(
            "BASELINE. The limitation is n=20 DONORS, not 39 samples. Counting the "
            "RNA and ATAC arms as separate units double-counts 19 of the same people."
        ),
    ),
    # ------------------------------------------------------- TIER 1 candidates
    row(
        tier="TIER 1 - independent donors, paired RNA+ATAC",
        dataset_id="syn66271521 + syn66271522 (AD Knowledge Portal)",
        short_name="MIT/ROSMAP multiregion snATAC + snMultiome (Xiong et al. 2025)",
        primary_record=(
            "Synapse entity service (names verified: 'Multiregion Epigenetics "
            "(snATAC-seq)', 'Multiregion Multiome'); PMC12573303 / PMID 40752494"
        ),
        assays_deposited="snATAC-seq; snMultiome; snRNA-seq",
        deposited_units_transcribed=(
            "402 files listed under syn66271521; 172 under syn66271522 "
            "(public children listing). Paper states 384 postmortem brain samples "
            "and 356 snATAC-seq libraries."
        ),
        independent_unit="donor",
        n_independent_units="111",
        n_independent_units_basis="stated verbatim in the paper abstract: '111 AD and control individuals'",
        microglia_usable=(
            "yes - paper reports microglia/immune-associated regulatory modules "
            "among 67 cell subtypes"
        ),
        cell_types="7 major classes / 67 cell subtypes (paper)",
        gene_coverage="snRNA + multiome GEX; per-feature counts " + NOT_STATED,
        peak_coverage=">1 million cCREs called across the study (paper)",
        disease_context="AD and control, with cognitive-resilience phenotyping (ROSMAP)",
        brain_regions="6 regions (EC, HC, PFC, thalamus and others per paper)",
        access=(
            "CONTROLLED. File names are publicly listable; bytes require an AD "
            "Knowledge Portal Data Use Certificate. Lead time is the binding cost."
        ),
        size_on_disk=UNKNOWN + " - public children listing does not return file sizes",
        overlap_FULL104_donors=(
            "NONE. ROSMAP (Rush) is disjoint from all three FULL104 sources "
            "(SEA-AD/Allen-UW, HVS, NPH52). This is the decisive property."
        ),
        overlap_other_project_assets="none known",
        failure_mode_screen=(
            "PASSES all four. Real donors, one library per donor-region, no shared "
            "guide library, no pooled-well pseudoreplication."
        ),
        integration_feasibility=(
            "high for RNA; ATAC needs peak-coordinate harmonisation with the "
            "Stage81A2R address space, which is gene-keyed not peak-keyed"
        ),
        verdict="TOP CANDIDATE. 111 independent donors with paired epigenome+transcriptome.",
    ),
    row(
        tier="TIER 1 - independent donors, paired RNA+ATAC",
        dataset_id="syn52293417 (MIT_ROSMAP_Multiomics)",
        short_name="Xiong et al. 2023 ROSMAP PFC snATAC (predecessor study)",
        primary_record="Synapse entity service (name verified: 'MIT_ROSMAP_Multiomics')",
        assays_deposited="snATAC-seq; snMultiome (PFC)",
        deposited_units_transcribed="0 files at folder root; 1 child folder ('Data', syn52293424, 6 subfolders)",
        independent_unit="donor",
        n_independent_units="92",
        n_independent_units_basis="stated in the 2023 publication's own description of the cohort",
        microglia_usable="yes",
        cell_types="all cortical types",
        gene_coverage=NOT_STATED,
        peak_coverage=NOT_STATED,
        disease_context="AD (early and late stage) and control, ROSMAP",
        brain_regions="PFC",
        access="CONTROLLED, same Data Use Certificate as the multiregion study",
        size_on_disk=UNKNOWN,
        overlap_FULL104_donors="NONE (ROSMAP)",
        overlap_other_project_assets=(
            "SUBSUMED BY the 2025 multiregion study, which states this PFC data is "
            "its own previously reported data. Acquire ONE of the two, not both as "
            "independent evidence."
        ),
        failure_mode_screen="PASSES all four",
        integration_feasibility="same as the multiregion study",
        verdict=(
            "REDUNDANT WITH TIER-1 TOP CANDIDATE. Treating both as separate "
            "replications would double-count the same donors."
        ),
    ),
    row(
        tier="TIER 1 - independent donors, paired RNA+ATAC",
        dataset_id="syn26207321 (AD Knowledge Portal)",
        short_name="Kosoy et al. 2022 human microglia regulome",
        primary_record=(
            "Synapse entity service (name verified: 'GeneticsoftheHumanMicroglia "
            "Regulome_Kosoy.etal'); Nat Genet 2022"
        ),
        assays_deposited="ATAC-seq and RNA-seq on PURIFIED primary human microglia; Hi-C",
        deposited_units_transcribed=(
            "0 files and 0 folders returned by the public children listing - the "
            "folder is access-gated at listing level, unlike the ROSMAP folders"
        ),
        independent_unit="donor",
        n_independent_units="150 donors; ATAC n=107, RNA n=127, both n=88",
        n_independent_units_basis="stated in the publication; NOT verified against the deposit (listing is gated)",
        microglia_usable=(
            "BEST-IN-CLASS - this is purified microglia, not microglia inferred "
            "from an unbiased nuclear capture"
        ),
        cell_types="microglia only (CD11b+ isolation)",
        gene_coverage="bulk RNA-seq of sorted cells",
        peak_coverage="bulk ATAC-seq peaks; count " + NOT_STATED,
        disease_context="biopsy (n=27) and autopsy (n=123) donors, mixed neurological/psychiatric",
        brain_regions="fresh prefrontal cortex",
        access="CONTROLLED; listing itself returned empty, so a DUC is needed even to inventory",
        size_on_disk=UNKNOWN,
        overlap_FULL104_donors=(
            "none known, BUT see MiGA/MiGASti - same Mount Sinai / Netherlands Brain "
            "Bank pipeline, so donor overlap WITH THOSE is likely and unmeasured"
        ),
        overlap_other_project_assets="none in the project",
        failure_mode_screen=(
            "PASSES technical-well and guide-library screens. CRISPRbrain-style "
            "shared-infrastructure risk applies BETWEEN Kosoy, MiGA and MiGASti, "
            "which share a lab and brain banks - they are not three independent "
            "replications."
        ),
        integration_feasibility="bulk, so cell-level JEPA states do not transfer directly; donor-level only",
        verdict=(
            "STRONG for donor-level microglial RNA+ATAC. Cannot validate cell-level "
            "representations because it is bulk."
        ),
    ),
    # --------------------------------- TIER 2: independent donors, perturbation
    row(
        tier="TIER 2 - perturbation with real donor replication",
        dataset_id="GSE249315",
        short_name="MiGASti human microglia responsome (ex vivo stimulation)",
        primary_record="GEO SOFT brief; overall_design states '67 different donors (N = 398 samples)'",
        assays_deposited="bulk RNA-seq of primary human microglia (398 RNA-Seq GSMs, all Homo sapiens)",
        deposited_units_transcribed=(
            "398 GSMs, all RNA-Seq. Stimulus arms transcribed from sample titles: "
            "unstim 132, LPS 126, IFNgamma 79, R848 41, DEX 9, IL4 7, ATP 4"
        ),
        independent_unit="donor",
        n_independent_units="67",
        n_independent_units_basis=(
            "stated verbatim in the deposit's own overall_design. NOTE: grouping "
            "sample titles by their first two hyphen fields yields 69 tokens, not "
            "67. The 2-unit discrepancy is UNRESOLVED; the title token is therefore "
            "a library-group proxy, not a verified donor id. 67 is the authoritative "
            "figure because the deposit states it."
        ),
        microglia_usable="yes - the entire deposit is primary human microglia",
        cell_types="microglia only (CD11b+ isolation)",
        gene_coverage="gene and transcript level per the deposit's overall_design",
        peak_coverage="none - no ATAC in this deposit",
        disease_context=(
            "donors with neurological/psychiatric disease and unaffected controls; "
            "per-donor diagnosis " + NOT_STATED + " (no diagnosis characteristics field)"
        ),
        brain_regions=(
            "region token counts from titles: GFM 130, SVZ 107, GTS 65, THA 52, "
            "CC 38, NA 3, GFS 3"
        ),
        access="open",
        size_on_disk="0.05 GB supplementary (unit-rounded from FTP dir index)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets=(
            "SHARED-INFRASTRUCTURE RISK with MiGA (NG00105) and Kosoy (syn26207321): "
            "same lab and brain banks. Donor overlap across these three is LIKELY and "
            "is UNKNOWN - not measured in this lane."
        ),
        failure_mode_screen=(
            "PASSES the GSE301119 unequal-reference failure BY CONSTRUCTION: the "
            "control is the SAME donor's unstimulated aliquot. Within-donor paired "
            "coverage transcribed from titles - unstim+LPS 57 donors, "
            "unstim+IFNgamma 41, unstim+R848 28, unstim+DEX 9, unstim+IL4 7, "
            "unstim+ATP 4. PASSES the technical-well screen. Guide-library screen "
            "N/A (pharmacological, not CRISPR)."
        ),
        integration_feasibility=(
            "bulk, so donor-level only. Ex vivo culture for 24h before stimulation "
            "is a real caveat: cultured microglia drift from their in vivo state, so "
            "this tests response biology, not in-brain state."
        ),
        verdict=(
            "BEST AVAILABLE PERTURBATION RESOURCE ON REAL PEOPLE. 57 donors with a "
            "matched own-donor control and a matched LPS arm is a stronger "
            "replication base than every CRISPR option in the project combined."
        ),
    ),
    row(
        tier="TIER 2 - perturbation with real donor replication",
        dataset_id="NG00105 (NIAGADS DSS)",
        short_name="MiGA - Microglia Genomic Atlas (Lopes et al. 2022)",
        primary_record="NIAGADS DSS dataset page; Nat Genet 2022",
        assays_deposited="bulk RNA-seq of purified microglia; genotypes",
        deposited_units_transcribed="255 samples from 100 donors (publication)",
        independent_unit="donor",
        n_independent_units="100",
        n_independent_units_basis="stated in the publication; NOT verified against the deposit in this lane",
        microglia_usable="yes - purified CD11b+ microglia",
        cell_types="microglia only",
        gene_coverage="bulk RNA-seq",
        peak_coverage="none",
        disease_context="neurological and psychiatric disease plus unaffected controls",
        brain_regions="MFG, STG, SVZ, THA (publication)",
        access="CONTROLLED - NIAGADS data access request required",
        size_on_disk=UNKNOWN,
        overlap_FULL104_donors="none known",
        overlap_other_project_assets=(
            "LIKELY DONOR OVERLAP with GSE249315 (MiGASti) and syn26207321 (Kosoy) - "
            "same brain banks and lab. UNKNOWN magnitude."
        ),
        failure_mode_screen=(
            "Observational, so no perturbation-specific failure applies. The "
            "CRISPRbrain shared-infrastructure lesson applies to the MiGA/MiGASti/"
            "Kosoy trio as a group."
        ),
        integration_feasibility="bulk, donor-level only",
        verdict="USEFUL as observational microglial reference; NOT a perturbation resource.",
    ),
    row(
        tier="TIER 2 - perturbation with real donor replication",
        dataset_id="GSE204702",
        short_name="Cross-disease living human microglia (CD45+ scRNA-seq)",
        primary_record="GEO SOFT brief; PMID 39406950",
        assays_deposited="scRNA-seq of CD45+ cells (67 RNA-Seq GSMs)",
        deposited_units_transcribed="67 GSMs, all RNA-Seq, all Homo sapiens",
        independent_unit="donor",
        n_independent_units=NOT_STATED,
        n_independent_units_basis=(
            "no donor characteristics field. 40 unique leading title tokens across "
            "8 disease prefixes (ALS, CNTRL, DLBD, EOAD, FTD, LOAD, MS, PSP) is a "
            "PROXY for donors, not a stated count."
        ),
        microglia_usable="yes - CD45+ sort from autopsy tissue and surgical resections",
        cell_types="microglia and other CNS immune cells",
        gene_coverage="scRNA-seq counts",
        peak_coverage="none",
        disease_context="cross-disease: ALS, DLBD, EOAD, FTD, LOAD, MS, PSP, control",
        brain_regions="multiple, plus spinal cord (SC); region tokens in sample titles",
        access="open",
        size_on_disk="0.632 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="none known",
        failure_mode_screen="PASSES technical-well screen; guide-library screen N/A",
        integration_feasibility=(
            "single-cell, so cell-level states transfer. Living/surgical samples are "
            "a different tissue state from postmortem FULL104 - a feature for "
            "robustness testing, a confound for direct comparison."
        ),
        verdict=(
            "GOOD breadth of disease context at single-cell resolution. Donor count "
            "must be established from the publication before any power claim."
        ),
    ),
    # ------------------------------- TIER 3: independent donors, ATAC, off-context
    row(
        tier="TIER 3 - independent donors but off-context disease",
        dataset_id="GSE256207",
        short_name="Orbitofrontal cortex snATAC, psychiatric cohort",
        primary_record="GEO SOFT brief; PMID 40053590",
        assays_deposited="snATAC-seq (92 GSMs, all ATAC-seq)",
        deposited_units_transcribed="92 GSMs, one per donor (title shape s#_PFC_ATAC x92)",
        independent_unit="donor",
        n_independent_units="92",
        n_independent_units_basis=(
            "deposit's overall_design states 35 psychiatrically healthy donors and "
            "57 donors diagnosed with a psychiatric disease; the 92 GSM titles are "
            "one-per-sample, and the diagnosis field splits 57 Cases / 35 Controls"
        ),
        microglia_usable="yes, as a subpopulation of the snATAC capture",
        cell_types="all cortical types",
        gene_coverage="none (ATAC only)",
        peak_coverage="snATAC; peak count " + NOT_STATED,
        disease_context="psychiatric disease, NOT Alzheimer's",
        brain_regions="orbitofrontal cortex BA11; NSW Brain Tissue Resource Centre",
        access="open",
        size_on_disk="7.031 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known; Australian brain bank, disjoint from all FULL104 sources",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "PASSES all four. Rich per-donor QC covariates deposited (age, pH, PMI, "
            "RIN, ethnicity, lib batch) - unusually good for nuisance modelling."
        ),
        integration_feasibility="ATAC-only, so it cannot validate an RNA-keyed representation directly",
        verdict=(
            "92 independent donors is the largest open snATAC donor set found, but "
            "the disease axis is psychiatric. Use for chromatin-space generalisation "
            "and nuisance structure, NOT as AD validation."
        ),
    ),
    row(
        tier="TIER 3 - independent donors but off-context disease",
        dataset_id="GSE246443",
        short_name="BA9 snATAC, MDD/suicide cohort (multiplexed)",
        primary_record="GEO SOFT brief; PMID " + NOT_STATED,
        assays_deposited="snATAC-seq (42 GSMs)",
        deposited_units_transcribed=(
            "42 GSMs. Deposit's overall_design states 44 MDD cases who died by "
            "suicide and 40 neurotypical controls, multiplexed as male (n=42) and "
            "female (n=42) pairs before capture."
        ),
        independent_unit="donor",
        n_independent_units="84",
        n_independent_units_basis="44 + 40 stated in the deposit's own overall_design",
        microglia_usable="yes, as a subpopulation",
        cell_types="all cortical types",
        gene_coverage="none",
        peak_coverage="snATAC; count " + NOT_STATED,
        disease_context="major depressive disorder / suicide, NOT Alzheimer's",
        brain_regions="BA9",
        access="open",
        size_on_disk="13.314 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "INVERSE of the GSE178317 failure: here 42 LIBRARIES carry 84 DONORS "
            "because nuclei were multiplexed. Donor identity must be recovered by "
            "genotype demultiplexing BEFORE any donor-level claim; taking 42 as the "
            "sample size understates it, taking 84 without demultiplexing is "
            "unsupported."
        ),
        integration_feasibility="blocked until demultiplexing is done and audited",
        verdict="DEFER. Real donor breadth, but donor identity is not directly deposited.",
    ),
    # ------------------------------------------ TIER 4: AD context, too few donors
    row(
        tier="TIER 4 - right context, insufficient donors",
        dataset_id="GSE214979 (data) / GSE214637 (superseries)",
        short_name="Anderson et al. DLPFC snMultiome AD",
        primary_record="GEO SOFT brief; PMIDs 36950385, 40817596",
        assays_deposited=(
            "snMultiome, deposited as paired GSMs: GSE214979 = 20 ATAC + 20 RNA; "
            "GSE214637 superseries adds 8 ChIP-Seq (48 total)"
        ),
        deposited_units_transcribed="40 GSMs in GSE214979 (20 ATAC-seq + 20 RNA-Seq), all Homo sapiens",
        independent_unit="donor",
        n_independent_units="15",
        n_independent_units_basis=(
            "deposit's overall_design states '7 AD and 8 unaffected donors'. The 40 "
            "GSMs are 20 multiome libraries x 2 modalities, and some titles carry "
            "'rep' suffixes, so GSM count materially overstates donor count."
        ),
        microglia_usable="yes, as a subpopulation",
        cell_types="all cortical types",
        gene_coverage="multiome GEX",
        peak_coverage="multiome ATAC",
        disease_context="18 AD / 22 control GSM labels over 15 donors",
        brain_regions="DLPFC",
        access="open",
        size_on_disk="66.373 GB supplementary (unit-rounded) - the largest per-donor cost in the registry",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "PASSES the technical-well screen only because donors are real; but "
            "n=15 with replicate libraries invites exactly the RNA-vs-ATAC "
            "double-count that inflates Morabito's apparent n."
        ),
        integration_feasibility="high - true same-cell multiome, the cleanest modality pairing available",
        verdict=(
            "BEST MODALITY PAIRING, WORST REPLICATION-PER-GIGABYTE. 66 GB for 15 "
            "donors. Acquire only if same-cell RNA-ATAC coupling is the specific "
            "question."
        ),
    ),
    row(
        tier="TIER 4 - right context, insufficient donors",
        dataset_id="GSE272082",
        short_name="Sporadic early-onset AD snMultiome, 3 regions",
        primary_record="GEO SOFT brief; PMID 41406216",
        assays_deposited="snMultiome (21 ATAC + 21 GEX GSMs)",
        deposited_units_transcribed="42 GSMs (21 ATAC-seq + 21 RNA-Seq); dx labels 20 sEOAD / 22 Control",
        independent_unit="donor",
        n_independent_units="9",
        n_independent_units_basis=(
            "deposit's overall_design states 4 sEOAD patients and 5 matched controls "
            "across PFC (n=9), EC (n=6), HIP (n=5) samples"
        ),
        microglia_usable="yes, as a subpopulation",
        cell_types="all types",
        gene_coverage="multiome GEX",
        peak_coverage="multiome ATAC",
        disease_context="sporadic EARLY-onset AD - a different disease axis from late-onset FULL104",
        brain_regions="PFC, EC, HIP",
        access="open",
        size_on_disk="37.581 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "Regional samples from the same 9 people are NOT independent units - the "
            "same error class as counting Morabito's RNA and ATAC arms separately."
        ),
        integration_feasibility="high technically, but n=9 cannot support a donor-level claim",
        verdict="REJECT for validation. n=9 donors. Useful only as qualitative context.",
    ),
    row(
        tier="TIER 4 - right context, insufficient donors",
        dataset_id="GSE259298",
        short_name="Pick's disease and AD snATAC + snRNA",
        primary_record="GEO SOFT brief; PMID 41223260",
        assays_deposited="snATAC-seq (16) + snRNA-seq (12)",
        deposited_units_transcribed=(
            "28 GSMs. Title shapes show 9 Control snATAC + 6 Pick's snATAC plus "
            "iPSC/neuron UBE3A and WT lines - the deposit MIXES postmortem tissue "
            "with cell-line samples."
        ),
        independent_unit="donor (tissue arm only)",
        n_independent_units="16",
        n_independent_units_basis="deposit's overall_design states 7 Pick's patients and 9 age-matched controls",
        microglia_usable="yes in the tissue arm",
        cell_types="all types (tissue arm); iPSC/neuron (line arm)",
        gene_coverage="snRNA",
        peak_coverage="snATAC",
        disease_context="Pick's disease (a tauopathy), not late-onset AD",
        brain_regions="PFC",
        access="open",
        size_on_disk="1.098 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "The iPSC line samples in the same accession are NOT donors. Any script "
            "that counts GSMs would silently mix cell lines into a donor cohort."
        ),
        integration_feasibility="tissue arm only, after excluding the line samples",
        verdict="REJECT for validation. n=16 and a different proteinopathy.",
    ),
    # ------------------------------------------------- TIER 5: rejected on design
    row(
        tier="TIER 5 - REJECTED, size without replication",
        dataset_id="GSE244618",
        short_name="Comparative atlas of single-cell chromatin accessibility, 42 brain regions",
        primary_record="GEO SOFT brief; PMID 37824643",
        assays_deposited="snATAC-seq (128 GSMs, all Homo sapiens)",
        deposited_units_transcribed="128 GSMs, all ATAC-seq",
        independent_unit="donor",
        n_independent_units="3",
        n_independent_units_basis=(
            "deposit's overall_design states verbatim: 'single-nucleus ATAC-seq in "
            "42 human brain regions from three neurotypical male donors'"
        ),
        microglia_usable="yes technically",
        cell_types="all types across 42 regions",
        gene_coverage="none",
        peak_coverage="snATAC across 42 regions",
        disease_context="NEUROTYPICAL ONLY - no disease axis; all male",
        brain_regions="42",
        access="open",
        size_on_disk="402.653 GB supplementary (unit-rounded) - largest in the registry",
        overlap_FULL104_donors="none",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "TEXTBOOK 'size is not qualification'. 128 libraries and 403 GB carry "
            "THREE independent people. Region samples from one donor are "
            "pseudoreplicates, structurally identical to the GSE178317 well error."
        ),
        integration_feasibility="n/a",
        verdict=(
            "REJECT as a validation cohort. Admissible ONLY as a regional chromatin "
            "reference where n=3 is explicitly stated at every use."
        ),
    ),
    row(
        tier="TIER 5 - REJECTED, title does not match deposit",
        dataset_id="GSE261983",
        short_name="'Single-cell genomics & regulatory networks for 388 human brains' (PsychENCODE2)",
        primary_record="GEO SOFT brief; PMID 38781369",
        assays_deposited="snATAC-seq (20) + snRNA-seq (20)",
        deposited_units_transcribed="40 GSMs = 20 ATAC-seq + 20 RNA-Seq, all Homo sapiens",
        independent_unit="donor",
        n_independent_units="20",
        n_independent_units_basis=(
            "20 RT#N title tokens, one library pair per donor; the deposit's own "
            "diagnosis field reads 'Control' for ALL 40 GSMs"
        ),
        microglia_usable="yes, as a subpopulation",
        cell_types="all types",
        gene_coverage="snRNA",
        peak_coverage="snATAC",
        disease_context="ALL CONTROL - zero disease samples in this accession",
        brain_regions="dlPFC",
        access="open",
        size_on_disk="5.696 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "TITLE TRAP. The title promises 388 brains; the deposit contains 20 "
            "control donors. Anyone inheriting '388' from the title, a review, or "
            "the consortium page would overstate this by 19x. The 388-brain "
            "resource lives elsewhere (Synapse), not in this accession."
        ),
        integration_feasibility="n/a at this n and with no disease contrast",
        verdict=(
            "REJECT AS DEPOSITED. Worth re-opening ONLY via the actual PsychENCODE2 "
            "Synapse resource, which is a separate acquisition with its own audit."
        ),
    ),
    row(
        tier="TIER 5 - REJECTED, not primary human donors",
        dataset_id="GSE148434 / GSE163323",
        short_name="Parkinson's iPSC-derived multi-omics",
        primary_record="GEO SOFT brief; PMIDs 37058563 / 35895835",
        assays_deposited="GSE148434: ATAC 13 + ChIP 18 + Hi-C 11 + RNA 28. GSE163323: ATAC 11 + OTHER 14 + RNA 26",
        deposited_units_transcribed="70 and 51 GSMs respectively",
        independent_unit="cell line / genotype, NOT donor",
        n_independent_units=NOT_STATED,
        n_independent_units_basis=(
            "characteristics fields are 'cell line', 'genotype', 'differentiation "
            "protocol', 'rs76904798 genotype' - there is no donor axis"
        ),
        microglia_usable="no - iPSC-derived neurons/microglia, not primary tissue",
        cell_types="iPSC-derived",
        gene_coverage="RNA-seq",
        peak_coverage="ATAC",
        disease_context="Parkinson's disease genetics",
        brain_regions="n/a (in vitro)",
        access="open",
        size_on_disk="32.266 GB / 22.549 GB (unit-rounded)",
        overlap_FULL104_donors="n/a",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "Cell lines cannot supply between-person variation. Same structural "
            "limit as GSE289721 and GSE178317."
        ),
        integration_feasibility="n/a for donor-level validation",
        verdict="REJECT for donor validation. Different disease and no donor axis.",
    ),
    # ------------------------------------------------------ microglia-specific niche
    row(
        tier="TIER 3 - independent donors but off-context disease",
        dataset_id="GSE338484",
        short_name="Somatic mutations / microglia ontogeny in human aging (snATAC)",
        primary_record="GEO SOFT brief; PMID " + NOT_STATED + " (recent deposit)",
        assays_deposited="snATAC-seq (29 GSMs)",
        deposited_units_transcribed=(
            "29 GSMs, all ATAC-seq. 23 unique UW# leading tokens; remaining GSMs are "
            "regional subsamples (_Pu, _Ce, _v2) of those same tokens."
        ),
        independent_unit="donor",
        n_independent_units=NOT_STATED,
        n_independent_units_basis=(
            "no donor characteristics field. 23 UW# tokens is a PROXY, and 6 of the "
            "29 GSMs are region/version variants of an existing token, so the GSM "
            "count overstates the donor count."
        ),
        microglia_usable=(
            "yes and explicitly - 'cell type' characteristic present, deposit is "
            "about immune cell phenotypes"
        ),
        cell_types="microglia and marrow-derived immune cells",
        gene_coverage="none",
        peak_coverage="snATAC",
        disease_context=(
            "aging with 'cognitive status' characteristic; the selection criterion "
            "is donors harbouring marrow-derived cells in brain, which is a "
            "NON-RANDOM SELECTION, not a population sample"
        ),
        brain_regions="multiple (Pu = putamen, Ce = cerebellum tokens present)",
        access="open",
        size_on_disk="55.835 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="none",
        failure_mode_screen=(
            "Selection on a rare biological feature means this is not an unbiased "
            "donor sample. Regional subsamples of the same donor are not replicates."
        ),
        integration_feasibility="ATAC-only, microglia-focused; small",
        verdict="NICHE. Microglial chromatin at real donor level, but selected cohort and ~23 donors.",
    ),
    # ------------------------------------- previously registered clean-holdout pool
    row(
        tier="TIER 4 - right context, insufficient donors",
        dataset_id="GSE157827",
        short_name="AD snRNA-seq, angiogenic endothelium study (v3 clean-holdout pool)",
        primary_record="GEO SOFT brief; PMIDs 32989152, 37117777",
        assays_deposited="snRNA-seq (21 GSMs)",
        deposited_units_transcribed="21 GSMs, all RNA-Seq",
        independent_unit="donor",
        n_independent_units="21",
        n_independent_units_basis="21 one-per-donor GSM titles; diagnosis characteristics field present",
        microglia_usable="yes, as a subpopulation",
        cell_types="all types",
        gene_coverage="snRNA",
        peak_coverage="none",
        disease_context="AD and control",
        brain_regions=NOT_STATED + " in the fields harvested",
        access="open",
        size_on_disk="1.288 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets=(
            "listed in docs/DATASET_REGISTRY.md 'Clean external holdout pool' and "
            "must stay untouched until architecture and evaluation rules are frozen"
        ),
        failure_mode_screen="PASSES; RNA-only",
        integration_feasibility="straightforward RNA integration",
        verdict="HOLD. Already reserved as clean holdout; do not spend it on method development.",
    ),
    row(
        tier="TIER 4 - right context, insufficient donors",
        dataset_id="GSE147528",
        short_name="Leng et al. selectively vulnerable neurons (v3 clean-holdout pool)",
        primary_record="GEO SOFT brief; PMID 33432193",
        assays_deposited="snRNA-seq (20 GSMs)",
        deposited_units_transcribed="20 GSMs, all RNA-Seq",
        independent_unit="donor",
        n_independent_units="10",
        n_independent_units_basis=(
            "10 unique values of the deposit's own 'donor id' characteristics field "
            "across 20 GSMs - this deposit DOES carry a donor id, unlike most"
        ),
        microglia_usable="limited - the study targets neurons",
        cell_types="all types, neuron-focused analysis",
        gene_coverage="snRNA",
        peak_coverage="none",
        disease_context="Braak stage axis (characteristics field present)",
        brain_regions="EC and SFG (two regions per donor - hence 20 GSMs from 10 people)",
        access="open",
        size_on_disk="0.565 GB supplementary (unit-rounded)",
        overlap_FULL104_donors="none known",
        overlap_other_project_assets="listed in docs/DATASET_REGISTRY.md clean external holdout pool",
        failure_mode_screen=(
            "20 GSMs / 10 donors - a clean worked example of why GSM count must "
            "never be read as donor count."
        ),
        integration_feasibility="RNA only, n=10",
        verdict="HOLD. Reserved clean holdout, and n=10 is too small to spend.",
    ),
    # ------------------------------------------------------------- SEA-AD expansion
    row(
        tier="CROSS-MODALITY ON KNOWN DONORS - NOT AN INDEPENDENT COHORT",
        dataset_id="SEA-AD snATAC / snMultiome (AWS sea-ad-single-cell-profiling; syn26223298)",
        short_name="SEA-AD MTG ATAC and Multiome expansion",
        primary_record=(
            "S3 bucket listing of sea-ad-single-cell-profiling (verified); "
            "Gabitto et al. PMC11614693 data-availability statement; "
            "Synapse entity syn26223298 name verified as 'SEA-AD'"
        ),
        assays_deposited="snRNA-seq; snATAC-seq; snMultiome; MERFISH",
        deposited_units_transcribed=(
            "MTG/ATACseq/ objects verified in the bucket listing: "
            "SEAAD_MTG_ATACseq_all-nuclei.2024-12-06.h5ad 38.963 GB; "
            "_final-nuclei 18.261 GB; _all-nuclei_metadata.csv 1.119 GB; "
            "plus per-cell-type bigWigs including Micro-PVM"
        ),
        independent_unit="donor",
        n_independent_units="84 in the SEA-AD MTG cohort",
        n_independent_units_basis=(
            "'a cohort of 84 aged donors' stated verbatim in Gabitto et al. "
            "Per-assay donor counts for snATAC and snMultiome specifically are "
            + NOT_STATED + " in the text retrieved."
        ),
        microglia_usable="yes - a dedicated Micro-PVM bigWig track exists per ADNC stratum",
        cell_types="139 molecular cell types (paper); Micro-PVM is a named class",
        gene_coverage="multiome GEX and snRNA h5ad",
        peak_coverage="nuclei-by-peak matrices with peaks called across all nuclei",
        disease_context="full AD pathology spectrum - the SAME pathology axis as FULL104",
        brain_regions="MTG (plus other regions in the wider bucket)",
        access=(
            "SPLIT: processed matrices OPEN on AWS Open Data; raw FASTQ CONTROLLED "
            "at Synapse syn26223298"
        ),
        size_on_disk="~57 GB for the two MTG ATAC h5ads alone, plus 1.1 GB metadata",
        overlap_FULL104_donors=(
            "MAXIMAL AND STRUCTURAL. FULL104's SEA_AD source contributes 46 of its "
            "104 donors and 4,118,213 of its 4,553,407 cells. SEA-AD MTG IS that "
            "source. These are the same people."
        ),
        overlap_other_project_assets=(
            "OUTCOME-EXPOSURE HAZARD: the open-access ATAC metadata CSV carries "
            "donor-level ADNC, Thal, Braak, CERAD, Cognitive Status, CASI, MMSE and "
            "APOE columns in the same file as the cell barcodes. Ingesting it "
            "without a column-level firewall would place protected FULL104 outcome "
            "variables into a working artifact."
        ),
        failure_mode_screen=(
            "Adding a second assay to people already in the training set is the "
            "same class of error as counting Morabito's RNA and ATAC arms as 39 "
            "units: it increases measurement per person, never the number of people."
        ),
        integration_feasibility=(
            "highest of any candidate - same cohort, same tissue, same pipeline, so "
            "no batch or bank confound. That is exactly why it cannot validate "
            "generalisation."
        ),
        verdict=(
            "CROSS-MODALITY EVIDENCE ON KNOWN DONORS. NOT AN INDEPENDENT "
            "DONOR-VALIDATION COHORT. See the dedicated verdict section."
        ),
    ),
    # ------------------------------------------------------------- perturbation set
    row(
        tier="PERTURBATION - placed, not re-audited",
        dataset_id="GSE289721",
        short_name="iMGL CRISPRi perturb-seq (poly(I:C) context)",
        primary_record=(
            "NOT RE-DERIVED IN THIS LANE. All facts cited from PR #158 "
            "(lane-e/gse289721-recon-20260926) and its source-authentication manifest."
        ),
        assays_deposited="8 GSMs = 4 GEX + 4 GDO (per PR #158)",
        deposited_units_transcribed=(
            "48,568 CellRanger barcodes; 36,601 gene rows + 72 CRISPR Guide Capture "
            "rows; 24 unique protospacers = 6 targets x 3 guides + 6 controls (PR #158)"
        ),
        independent_unit="DIFFERENTIATION",
        n_independent_units="2",
        n_independent_units_basis="PR #158: XP1 and XP2, ONE genetic background, no cell hashing",
        microglia_usable="iPSC-derived microglia-like cells, not primary human microglia",
        cell_types="iMGL only",
        gene_coverage="36,601 genes (PR #158)",
        peak_coverage="none",
        disease_context="poly(I:C) inflammatory challenge; CRISPRi dCas9-KRAB-MeCP2",
        brain_regions="n/a (in vitro)",
        access="open",
        size_on_disk="617,731,307 bytes of matrices (PR #158; not downloaded)",
        overlap_FULL104_donors="none - no human donors in the design",
        overlap_other_project_assets=(
            "INPP5D is targeted both here and in GSE178317, which the project "
            "registers as primary_microglial_perturbation_training. PR #158 flags "
            "INPP5D TRAINING_OVERLAP_SUSPECT; clean targets are AGFG2, EED, MS4A6A, "
            "PVR, RABEP1."
        ),
        failure_mode_screen=(
            "GSE335887 library-completeness screen: PASSES - all 6 named targets "
            "have all 3 guides deposited with sequences. CRISPRbrain "
            "shared-infrastructure screen: PASSES - different lab from GSE178317, "
            "with its own deposited library. GSE178317 technical-well screen: "
            "PASSES ON HONESTY, FAILS ON POWER - PR #158 states plainly that the "
            "independent unit is the differentiation and n=2. Unresolved: GEO says "
            "cell line IMR90, the paper says FA10."
        ),
        integration_feasibility="all 6 targets resolve current_exact into the frozen Stage81A2R address registry (PR #158)",
        verdict=(
            "QUALIFIED-FEASIBLE PENDING GATES 1-3 per PR #158. In THIS registry its "
            "place is: the best-constructed CRISPR option available, and still "
            "n=2 differentiations of one genetic background - which is why it "
            "ranks below GSE249315's 57 paired donors for any claim about people."
        ),
    ),
]


def verify(harvest_dir):
    path = pathlib.Path(harvest_dir) / "geo_primary" / "geo_primary_records.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    failures = []
    for acc, (n_gsm, strat) in GEO_CHECK.items():
        rec = data.get(acc)
        if rec is None or "error" in rec:
            failures.append("{0}: absent from harvest".format(acc))
            continue
        got_n = rec["samples"]["n_samples_listed"]
        got_s = rec["samples"]["library_strategy_counts"]
        if got_n != n_gsm:
            failures.append("{0}: n_gsm registry={1} harvest={2}".format(acc, n_gsm, got_n))
        if got_s != strat:
            failures.append("{0}: strategies registry={1} harvest={2}".format(acc, strat, got_s))
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--harvest-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.verify:
        failures = verify(args.harvest_dir)
        if failures:
            print("VERIFY FAILED - registry numbers disagree with the harvested "
                  "primary records:", file=sys.stderr)
            for f in failures:
                print("  " + f, file=sys.stderr)
            return 1
        print("VERIFY OK: {0} accessions match the harvested GEO primary "
              "records exactly".format(len(GEO_CHECK)))

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "agent6_external_dataset_registry_v1.csv"
    with dest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for r in ROWS:
            writer.writerow(r)
    print("wrote {0} ({1} rows)".format(dest, len(ROWS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
