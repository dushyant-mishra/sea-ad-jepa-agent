# V65 promoter ledger denominator and materialization contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE EXECUTION CONTRACT — annotation/evidence ledger only

## Core rule

GENCODE v50 defines candidate existence. SCREEN, FANTOM, Dong, NIH-CARD and Nott are evidence layers and may not prune the denominator merely because activity/support is absent or unmeasured.

## Two linked denominators

Two different GENCODE counts already exist in the project and must not be conflated.

### A. Transcript/promoter-isoform records

One row per GENCODE transcript record with transcript identity preserved.

Current authority: **644,292 transcript records** across **78,733 genes**.

Primary key must preserve at least:

`gene_id × transcript_id × chromosome × strand × exact TSS × GENCODE release`.

This is the appropriate table for Dong promoter-isoform evidence.

### B. Exact TSS loci

Collapse transcript records only when they share the same:

`gene_id × chromosome × strand × exact TSS`.

Current structural preflight authority: **389,280 unique exact TSS candidates** across **78,733 genes**.

This is the appropriate denominator for coordinate-level SCREEN/FANTOM coverage accounting.

Neither table supersedes the other. They answer different questions and must be linked by explicit membership.

## Required outputs

Future materialization must emit:

1. `PROMOTER_TRANSCRIPT_LEDGER`
   - all 644,292 transcript/promoter-isoform records;
   - transcript identity and exact TSS;
   - Dong chromosome-aware evidence;
   - evidence-availability fields.

2. `EXACT_TSS_LEDGER`
   - all 389,280 unique exact TSS loci;
   - transcript membership count/list or stable membership digest;
   - SCREEN/FANTOM coordinate evidence;
   - no activity-based candidate deletion.

3. `TRANSCRIPT_TO_TSS_MEMBERSHIP`
   - deterministic mapping from each transcript candidate to one exact TSS locus.

## Dong bridge

Dong Data 7 must join by `transcript_id + chromosome`, not ENST alone.

Repeated Dong ENST records are retained as annotation-version/chromosome-specific evidence.

Coordinate/gene/strand mismatch is annotation drift or unresolved evidence, not a biological negative.

## Evidence-state rule

For every resource, distinguish:
- measured and supports;
- measured and does not support;
- not measured;
- unresolved/version-drift.

Forbidden:
- `NOT_MEASURED -> 0`
- evidence absence -> candidate deletion
- SCREEN/FANTOM overlap -> promoter existence

## Source-byte gate

Do not claim the full ledger executed until exact source bytes are available and hash-bound for:
- GENCODE v50 GRCh38 annotation;
- SCREEN Registry-V4 PLS;
- FANTOM hg38 CAGE BED;
- Dong Supplementary Data 7.

Existing structural preflights remain evidence about expected counts, not substitutes for byte-level materialization.

## Governance

This ledger is annotation/evidence infrastructure only.

No promoter selection.  
No biological correspondence.  
No multimodal training.  
TRAINING OFF.
