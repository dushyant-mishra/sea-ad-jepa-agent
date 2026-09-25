# Cross-study ETL characterization — metadata authority only (2026-09-24)

Source: experimental PR #77 exact parent 9a2a30e4c4c99be2a8f948aba680524c786d2737; reviewed documents and receipts under `analysis/therapeutic_perturbation_etl/`. **This document is an evidence-based review of existing ETL, not a new physical re-read. No previously unread outcomes were inspected.** Full reproducible metadata audit and tests were generated in the conversation artifact; this repository note preserves the actionable result.

## Scientific conclusion

The eight GEO studies cannot be pooled into one expression-response prediction experiment. The experimental units, biological systems and interventions differ. A shared gene symbol is not proof of comparable treatments or readouts. Define the estimand and sample unit before any cross-study fitting.

| Study | Existing qualification | Main remaining scientific boundary |
|---|---|---|
| GSE178317 | Day-8 iTF microglia CRISPRi; 39 targets, 37 within-well supported; 33 support-qualified CRISPRbrain comparison | One pooled preparation, four technical wells; all Day-8 profiles development-exposed; no biological replication |
| GSE301119 | Primary macrophage CRISPRi/a guide-by-donor effects; 19,162 measured genes common to both modes | Two donors; transcriptome-wide donor-aware inference unfinished; macrophages are not microglia |
| GSE293118 | HMC3 noncoding CRISPRi; 64,148 single-guide cells; six measurable gene-target engagements | 77 other targets lack direct authenticated cis-target mapping; 23.2% of guide-called cells multiplets |
| GSE311359 | Seven-sample iPSC microglial Perturb-seq; 82 targets computationally unaffected by BIN1 bug | Three BIN1 guide names collide; 14 phantom pseudobulk rows; BIN1 STOP pending authentic feature-ID/protospacer map |
| GSE175721 | Organoid microglia gene matrices and 14 guide sequences authenticated | Per-cell guide metadata absent; no genetic-perturbation effects justified |
| GSE254205 | APOE4/4 iMG amyloid/GNE-317 bulk, three samples per condition | Drug not CRISPR; corrected physical V2 and three other assay assets pending; one model/timepoint |
| GSE241858 | TREM2 R47H by cytokine, two independent clones per genotype | Clone-level biological n=2/genotype; within-clone wells are not independent; genotype not CRISPR |
| GSE240609 | Purified post-coculture microglia genotype 2x2, one sample per design cell | Descriptive only, no biological SE; corrected V2 rerun pending; not cell-autonomous |

## Comparison strata and unseen-outcome firewall

CRISPRbrain acquisition includes seven RNA response screens and two 170-feature CITE protein screens. Day-8 RNA response outcomes have already been read and are DEVELOPMENT. Eight further screen acquisitions displayed aggregate target-engagement QC, but their per-target response profiles were recorded as unread. They are *potential* reserved outcomes only after rechecking exposure across lanes.

Nearest candidate microglial cross-experiment RNA comparators: the 31-target iTF and 31-target iPSC microglia CROP-seq screens, but their exact target overlap, clone/donor overlap, differentiation/timepoint and feature identity have not been authenticated. Their CITE counterparts are separate protein outcomes, not RNA DE replication. Neuron CRISPRi, neuron CRISPRa and undifferentiated iPSC outcomes are separate transport questions. No astrocyte transcriptome-wide perturbation table exists in this nine-screen acquisition; catalogue astrocyte screens are phenotypic, not RNA.

The historic FULL104 symbol-space receipt reports 344 of 352 CRISPRbrain intervention targets within its feature registry. This is **not** frozen cross-study HGNC/Ensembl identity, measured-response feature overlap or donor/lineage nonoverlap; those remain unchecked.

## Required next physical work

1. Complete metadata-only source, guide/target, donor/clone and gene-identity joins for candidate iTF/iPSC microglia comparisons *before* reading reserved response profiles. Output exact target and measured-feature intersections and independent-preparation evidence, with explicit NONESTIMABLE states.
2. Execute donor-aware transcriptome-wide GSE301119 ETL, corrected physical V2 GSE254205/GSE240609, authentic feature-ID rescue for BIN1, and request GSE175721's author-described per-cell guide metadata. Treat drug, genotype and CRISPR as distinct scientific interventions.
3. Perform deep **descriptive** Day-8 response characterization on the already-exposed data only; retain the currently uninformative mean-profile baseline as a visible negative result. Do not choose a benchmark by repeatedly inspecting reserved outcomes.

Additional review: `outputs/README.md` still attributes larger magnitude to a stricter guide caller without a controlled caller-sensitivity test; that causal explanation remains hypothetical.

**Authority:** METADATA_AUDIT_ONLY; no new physical ETL result, independent biological replication, cross-study model performance, training authorization or therapeutic ranking is claimed. Standing FULL104/N1/protected outcome stops unchanged.
