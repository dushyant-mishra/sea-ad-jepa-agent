# Target Discovery motif-program evidence layer — chromVAR + limma — 2026-10-15

Status: `SCIENTIFIC_DESIGN_INPUT__NON_AUTHORIZING__NO_TASK3_OR_TASK4_GATE_CHANGE`

This note folds genome-wide motif-associated accessibility into the JEPA Target Discovery evidence framework as a distinct evidence layer. It does not select a target, confer biological validation, alter frozen Tasks 0–2, accept Task 3, start Task 4, open protected values, or authorize training.

Source reviewed:

- NGS101 Part 7, “Genome-Wide Differential TF Activity with chromVAR and limma,” published 2026-10-15: https://ngs101.com/how-to-analyze-single-cell-atac-seq-data-a-complete-beginners-guide-part-7-genome-wide-differential-tf-activity-with-chromvar-and-limma/
- chromVAR Bioconductor package documentation: https://www.bioconductor.org/packages/release/bioc/html/chromVAR.html

## Why this is a separate layer

Peak-level ATAC, footprinting, SCENIC+, expression and perturbation do not answer the same question.

The new layer asks:

> Across all accessible loci carrying a motif, does motif-associated accessibility shift coherently across biological replicates?

That is different from:

- differential accessibility: which loci change;
- footprinting: whether local Tn5 insertion structure changes at motif sites;
- SCENIC+: whether TF–enhancer–gene regulatory relationships are coherent;
- expression: whether RNA abundance changes;
- perturbation: whether intervention produces the predicted downstream response.

Therefore chromVAR evidence must not be collapsed into generic “ATAC support” or counted as an independent biological replication when it is derived from the same underlying ATAC sample.

## Required analysis unit

Biological donors are the statistical replicates.

Required structure:

`cell type -> donor pseudobulk -> fixed-width peak counts -> motif matching -> chromVAR -> replicate-level limma`

Do not test per-cell chromVAR scores as independent replicates for target qualification. Per-cell scores may be used for visualization or descriptive state mapping only.

## Preferred prospective workflow

For each qualified cell type / population:

1. construct donor-level ATAC pseudobulks;
2. use a fixed-width peak representation, with summit-centered or midpoint-centered peaks according to the committed peak contract;
3. recount fragments after resizing rather than reusing an incompatible motif/peak matrix;
4. rematch the committed motif database to the actual tested peaks;
5. compute chromVAR motif deviation z-scores with GC- and accessibility-matched backgrounds;
6. use a high-background setting for differential testing, provisionally 1000–2000 background iterations, and retain the exact random seed;
7. quantify seed sensitivity / reproducibility;
8. perform donor-level differential testing with limma using the committed design matrix and covariates;
9. retain per-donor motif scores so top signals can be checked for single-donor dominance;
10. collapse near-identical motifs to motif families where sequence-level identifiability does not support a specific TF claim;
11. compare the resulting motif-program signal against peak-level accessibility, footprinting, SCENIC+, expression, perturbation and external-dataset evidence.

The exact normalization and design formula remain dataset-specific and must be prospectively committed before qualification. The NGS101 workflow uses quantile-normalized chromVAR z-scores before limma; that is a candidate default, not an automatic authority rule for every dataset.

## Evidence object

A motif-program evidence record should minimally bind:

- dataset / assay identity;
- donor identities and condition labels;
- cell population definition;
- peak-set identity and fixed-width rule;
- genome build;
- fragment/count source;
- motif database name/version;
- motif matching code/version;
- chromVAR version;
- limma version;
- background iteration count;
- random seed(s);
- normalization rule;
- model/design matrix and covariates;
- full motif-level result table;
- motif-family mapping;
- donor-level z-score matrix;
- seed-reproducibility result;
- source/technology claim limitations.

## Claim law

Preferred language:

`motif-associated accessibility increased/decreased`

Do not promote chromVAR alone to:

- direct TF binding;
- causal TF activity;
- TF protein abundance;
- TF-specific identity where several family members share effectively indistinguishable motifs;
- target causality;
- biological validation of a JEPA target.

A specific-TF claim requires additional resolving evidence such as compatible footprinting, ChIP-like evidence, SCENIC+/regulon structure, TF expression/protein evidence, perturbation, or another appropriate orthogonal source.

## Double-counting firewall

Evidence from one ATAC dataset may produce several analytical views, but those views are correlated.

For target integration:

- peak-level differential accessibility and chromVAR may support different mechanistic statements;
- footprinting may provide additional local binding-pattern evidence;
- they must remain separately labeled but grouped under the same assay/source dependency family;
- three concordant ATAC-derived analyses are not equivalent to three independent datasets;
- cross-dataset, cross-donor and cross-modality replication receive additional independence weight;
- SCENIC+ overlap must be examined for shared ATAC inputs before assigning independence credit.

## Convergence interpretation

Strong support is not “chromVAR significant.” Strong support is structured convergence such as:

`motif-program shift`
`+ compatible locus-level accessibility`
`+ compatible footprint / binding-pattern evidence`
`+ compatible SCENIC+ regulatory edge or regulon`
`+ compatible TF/target expression`
`+ compatible perturbation response`
`+ replication in another dataset / donor cohort / technology where available`

Disagreement is retained as evidence, not averaged away.

Examples:

- chromVAR positive, expression negative -> regulatory hypothesis remains unresolved;
- chromVAR family-level signal, SCENIC+ specific TF edge -> specific-TF claim remains limited until sequence/perturbation evidence distinguishes the family member;
- chromVAR signal driven by one donor -> downgraded / unstable, not silently pooled into positive support;
- chromVAR and peak-level ATAC both positive in the same dataset -> convergent analyses from one assay, not independent replication.

## Relationship to existing JEPA science law

This layer inherits the existing constraints:

- donor, not cell, is the biological replication unit for donor-level claims;
- source failure cannot average away;
- measurement evidence is not biological truth;
- technology is an observation operator, not donor identity;
- mechanics evidence cannot become biological authority;
- historical negative priors remain negative priors;
- pre-repair or contaminated results remain non-authorizing;
- no target winner exists until the complete qualified evidence framework adjudicates one.

## Immediate framework effect

Add one explicit evidence channel to future target scoring/adjudication:

`MOTIF_PROGRAM_ACCESSIBILITY`

with claim class:

`TF_FAMILY_ASSOCIATED_CHROMATIN_ACCESSIBILITY`

unless additional evidence prospectively supports a narrower TF-specific claim.

This is a framework addition only. It does not authorize rerunning any spent experiment, does not alter Task 3 acceptance criteria, and does not start Task 4 implementation.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
