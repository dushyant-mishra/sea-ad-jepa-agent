# V64 promoter annotation-release drift rule

GENCODE v50 defines the base candidate TSS namespace. External promoter-isoform resources are evidence layers and must be crosswalked rather than silently substituted.

The Dong/Roussos brain atlas demonstrates why this matters:

- 98.0% of Supplementary Data 7 transcript IDs persist in GENCODE v50;
- only 82.1% of overlapping IDs retain the exact same TSS;
- the TSS-shift distribution has a long tail;
- some stable transcript IDs no longer carry the same gene assignment.

Therefore an ENST identifier by itself is not sufficient promoter identity across annotation releases.

## Mapping states

Every external transcript/promoter row must land in one of:

1. `ID_ABSENT_IN_CURRENT_GENCODE`
2. `ID_PRESENT_EXACT_GENE_CHROM_STRAND_TSS`
3. `ID_PRESENT_SAME_GENE_CHROM_STRAND_SHIFTED_TSS`
4. `ID_PRESENT_GENE_MISMATCH`
5. `ID_PRESENT_CHROM_OR_STRAND_MISMATCH`

No fuzzy TSS tolerance is frozen yet.

Do not:
- force a shifted TSS onto the current exact-TSS candidate;
- merge nearby TSSs merely because the shift appears small;
- treat a stable ENST as proof of unchanged promoter identity;
- discard old evidence when mapping is unresolved.

Instead preserve the external evidence object and its mapping state. A later prospectively justified bridge may determine how shifted historical TSS evidence contributes to a current candidate.

The base GENCODE v50 structural universe currently contains:
- 78,733 genes with transcripts;
- 644,292 transcripts;
- 389,280 unique gene×exact-TSS candidates;
- 34,598 genes (43.9%) with more than one exact-TSS candidate.

This is a candidate universe, not a claim that all candidates are active promoters.

TRAINING OFF. No promoter winner selected. Phase B stopped. Stage 4 unauthorized.
