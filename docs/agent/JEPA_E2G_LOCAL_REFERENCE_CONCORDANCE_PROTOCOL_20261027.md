# E2G public-reference interval concordance: non-authorizing local protocol

Frozen before calculating cross-source enhancer-coordinate recurrence. Seven source files were recovered from the public portal, verified by exact SHA-256 against the prior read-only survey. No SEA-AD or other local patient-level modalities will be used.

## Fixed estimand

Quantify the *reuse of enhancer–gene coordinates across preselected public reference predictions*, not a biological response to LPS, independent microglial validation, or causality. The three ENCODE-rE2G inflammatory macrophage tracks (unqualified condition, LPS 1 h, LPS 4 h) are separate source contexts, not authenticated donor/replicate/time-course observations.

1. Parse all seven public BEDPE files; require exact verified file SHA-256, 10 columns, finite scores in [0,1], valid genomic intervals, and consistent chromosome coordinates. Retain model and study IDs. Use gene symbols only; do NOT silently equate them with unversioned Ensembl IDs.
2. In the three same-family ENCODE-rE2G macrophage contexts, use a key `(gene symbol, enhancer chromosome, start, end, target chromosome, target TSS start)`. Compute exact shared link recurrence, union, gene-level baseline retention and promoter-proximal versus distal (< or >=20 kb enhancer-midpoint to TSS). Do not compare score magnitudes or compute LPS effects.
3. Select one source-blinded negative-control gene for each of the 27 historical target symbols from nonpanel genes in the same reference-condition-unqualified rE2G track, matching chromosome, baseline link count and distal link count. Require at least 1 Mb separation between target TSS and the control TSS. Selection is greedy and deterministic and **must not consult the other two conditions**. Report matching diagnostics and no inferential p-values.
4. Compare reciprocal-overlap >=0.5 for identical target symbols between rE2G macrophage intervals and each of the other selected reference contexts. Cross-family comparisons are **descriptive transfer/overlap checks**, not calibrated model validation. Exclude same-symbol records with incompatible reported target chromosomes/TSS positions. Treat absence in thresholded tracks as unknown biological support, not a negative.
5. Produce a compact BED-like **interval reference catalogue** consisting only of same-family stable rE2G elements for our 27 candidate target symbols, annotated with cross-family interval overlap flags and genomic distance. This is not a ranked JEPA target list or a TF→gene regulatory edge list, and it cannot be used for training.

## Fail-closed boundaries

All original public files are hash pinned. Cross-family gene-symbol coordinate consistency is checked explicitly. No mutation to frozen Stage75, no downstream JEPA target selection, no training, no assessment of disease direction, no donor-level significance or biological condition effect. All output CSV and JSON are compact derived annotations. A null result is not biological absence.

GitHub references: draft PR #457 and source hashes already preserved in `results/regulatory/e2g_public_7track_provisional_result_receipt_v1_20261027.json`.