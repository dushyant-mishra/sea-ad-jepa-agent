# V64 promoter/TSS candidate-universe contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE DESIGN ONLY — no promoter atlas executed

## Principle

The candidate promoter denominator must not be defined by measured activity.

Use **GENCODE GRCh38 transcript/TSS annotation** to define the initial candidate promoter/TSS universe. Measurement resources may add evidence to those candidates but may not remove candidates merely because they are not observed in a particular assay.

This prevents CAGE/ATAC/promoter-activity selection from being baked into the denominator before coverage is measured.

## Candidate unit

Preferred key:

`gene_id × transcript/TSS/promoter_id × genome_build`

Context-specific activity is an evidence field, not part of candidate existence.

## Evidence layers that may annotate candidates later

- FANTOM5 CAGE/TSS activity
- SCREEN promoter-like cCRE overlap
- public brain promoter/isoform evidence
- NIH-CARD promoter accessibility
- Nott promoter evidence
- future promoter-specific contact evidence

None is automatically promoter truth.

## Required candidate fields

At minimum:

- gene_id
- gene_symbol
- transcript_id where applicable
- candidate_promoter_id
- chromosome
- strand
- TSS coordinate
- candidate promoter interval definition
- genome build
- GENCODE release/version
- annotation provenance
- evidence-availability mask by source
- evidence values by source
- ambiguity group for genes with multiple candidate promoters

## Ambiguity

Multiple plausible promoters must remain explicit.

Do not collapse to a single promoter because:
- it is canonical;
- it has strongest CAGE;
- it is most accessible;
- it has the most regulatory edges.

Promoter selection, if ever needed, requires a prospective context-specific rule.

## Genome-build rule

The base candidate universe is GRCh38.

Any hg19 evidence must be mapped under an explicitly qualified mapping procedure with:
- source interval retained;
- mapped interval retained;
- chain/binary digests;
- ambiguity state;
- exact mapping status where required.

Do not let failed/unavailable liftover become biological absence.

## Coverage accounting

For every evidence source report separately:

- candidates measurable;
- candidates supporting;
- candidates measured but not supporting;
- candidates not measured.

Do not zero-fill not-measured.

## Access/licensing metadata

Every external resource must record separately:
- download/access status;
- stated license/terms;
- version/release;
- recovery location;
- digest.

Publicly downloadable does not imply openly licensed.

## Governance

This contract does not authorize promoter-atlas ingestion yet.

Execution remains blocked until the current Phase-A exact-control audit stop has been cleared.
