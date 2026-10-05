# JEPA V53 — synthetic diagnosis of the RED cis positive-control problem

Date: 2026-09-28
Base: b5c970de0a956188019a6d757a85ca9a31b2ee66 (V52 / PR #191 head)
Governance: TRAINING=OFF · TD60=BLOCKED · synthetic/technical only · no real regulatory biological outcome opened

## Why this lane exists

Claude's V50 red-team proposed a positive discriminating signature:

cis correspondence - accessibility-matched trans/pseudo-cis correspondence

but his only implementation was RED. The planted biological positive cancelled because cis peak loadings were assigned mixed/random signs, so a signed mean correlation could destroy a real planted regulatory signal. Claude reported the technical arm at approximately +0.0142 and the biological arm at approximately +0.0029.

V53 diagnoses that failure without opening any real regulatory biology.

## External method precedent used only as design support

Signac LinkPeaks does not interpret raw peak-gene correlation alone. It compares nearby peak-gene correlation against expected correlations from background peaks matched on GC content, accessibility, and peak length:

https://stuartlab.org/signac/reference/linkpeaks

ArchR peak-to-gene linkage additionally exposes empirical non-same-chromosome and sample-permutation nulls and excludes depth-correlated dimensions:

https://www.archrproject.com/reference/addPeak2GeneLinks.html

V53 treats those as a minimum control floor, not biological proof. Our synthetic nuisance class is stricter: it also contains residual latent quality plus locus structure tied to gene density/mappability-like covariates.

## Frozen synthetic worlds

Negative families:

- NEG_INDEPENDENT: no shared RNA/ATAC state.
- NEG_GLOBAL: shared technical/global quality state.
- NEG_LOCUS: shared donor technical state with locus-dependent sensitivities.
- NEG_DEV_SAME_NUC: same-nucleus shared nuisance exists in the development cohort but is absent in the separate-nucleus confirmation cohort.
- NEG_DONOR_GLOBAL: donor-level technical state persists across both cohorts.
- exact semantic twin: identical observables, different hidden biological/technical interpretation. This is not separable by any observable statistic and is retained as a claim boundary.

Positive families:

- POS_COHERENT: regulatory cis peaks carry a coherent planted program.
- POS_MIXED: true cis effects have mixed signs.
- POS_SPARSE: only a subset of local peaks carry the planted program.
- POS_MIXED_WEAK: weaker mixed-sign effect. This is a power diagnostic only, not a mandatory gate arm; otherwise arbitrary effect attenuation can force any method to fail.

Development/confirmation donor counts were intentionally set to the current project-relevant order of magnitude:

- development: 12 donors;
- separate-nucleus confirmation: 18 donors.

All testing remains synthetic.

## Control design

Static peak/locus covariates represent:

1. GC-like composition;
2. baseline accessibility;
3. peak-length-like structure;
4. gene-density/locality structure;
5. mappability-like structure.

Two decoy families were constructed:

- full matched: all locus covariates matched;
- partial matched: only the first three matched, leaving density/mappability-like structure uncontrolled.

QC was also tested two ways:

- program-excluded QC: technical covariates do not include the target program genes/cis peaks;
- program-inclusive QC: a deliberately unsafe diagnostic where program signal contributes to the QC covariate.

## Tournament 1 — pairwise cis-vs-decoy statistics

Candidate statistics included signed Pearson excess, absolute-correlation excess, squared-correlation excess, Fisher-transformed absolute excess, Spearman absolute excess, partial-matching diagnostics, and program-inclusive-QC diagnostics.

Development seeds and held-out seeds were separate.

Result: no pairwise statistic achieved positive held-out separation at n=12 or n=18.

At n=18 the best development-selected candidate was spearman_abs_full, but the held-out robust margin (minimum positive q10 minus maximum negative q90) remained -0.05895.

Important diagnostics:

- NEG_LOCUS, full matching median: approximately -0.0019;
- NEG_LOCUS, partial matching median: approximately +0.0599;
- POS_MIXED, full/excluded-QC median: approximately +0.0502;
- POS_MIXED, program-inclusive-QC median: approximately -0.0169;
- signed statistic on POS_MIXED: negative median.

Interpretation:

1. replacing signed mean correlation with sign-invariant magnitude fixes Claude's exact cancellation mechanism;
2. under-matching locus covariates creates a false technical positive;
3. program-inclusive QC can erase or reverse the positive;
4. donor count remains a major limitation.

This is RED as a qualification gate.

## Tournament 2 — ATAC-only cis-module PC1

For each gene, cis peaks were residualized and compressed using ATAC-only PC1; RNA association used the absolute cross-donor correlation of that PC1 versus matched decoy modules.

This avoids using RNA to choose the sign of the cis module.

At n=18:

- coherent positive median: approximately 0.214;
- mixed-sign positive median: approximately 0.098;
- sparse positive median: approximately 0.123;
- locus-negative median: approximately -0.0044.

But the held-out robust margin remained negative, largely because mixed/weak positives and random-null tails overlap.

Program-inclusive QC again destroyed the planted coherent/mixed signal.

This is also RED as a gate.

## Tournament 3 — transported frozen cis weights

This test was designed to match the proposed real evidence sequence more closely:

1. learn cis weights only in a 12-donor external development cohort;
2. freeze the weights;
3. test them without refitting in an independent 18-donor confirmation cohort;
4. model confirmation as separate-nucleus RNA/ATAC;
5. compare true cis prediction against fully matched pseudo-cis modules;
6. use rank/ordinal transforms so source-specific scaling does not define the result.

Candidate ridge penalties were selected only on development simulation seeds and evaluated on separate held-out simulation seeds.

Development selected rank_ridge_full_l8.0.

Held-out distributions:

| world | q10 | median | q90 |
|---|---:|---:|---:|
| NEG_INDEPENDENT | -0.0971 | +0.0199 | +0.1001 |
| NEG_DEV_SAME_NUC | -0.0666 | +0.0095 | +0.0858 |
| NEG_DONOR_GLOBAL | -0.0369 | +0.0040 | +0.0419 |
| NEG_LOCUS | -0.0396 | -0.0103 | +0.0249 |
| POS_COHERENT | +0.1372 | +0.2312 | +0.4141 |
| POS_MIXED | +0.0499 | +0.1921 | +0.3299 |
| POS_SPARSE | +0.0775 | +0.1622 | +0.2908 |
| POS_MIXED_WEAK | -0.0310 | +0.0289 | +0.0987 |

The overall held-out strict robust margin remained -0.13102.

Therefore this is not qualified.

However this tournament produced the strongest mechanistic result so far:

- a nuisance present only as same-nucleus development covariance did not transport strongly into the separate-nucleus confirmation cohort;
- coherent, mixed-sign, and sparse planted biology all produced substantially larger median transported cis excess;
- program-inclusive QC again nearly erased the mixed positive;
- rank/ordinal transport handled cross-source scaling by construction.

This supports the logic of Morabito-before-SEA-AD sequencing, but it does not authorize biological execution.

## What V53 demonstrates

V53 demonstrates:

1. Claude's first RED result was partly caused by a real statistic-design defect: signed averaging cancels mixed-direction cis effects.
2. A positive signature should be sign-aware or sign-invariant.
3. Full locus matching is load-bearing. GC/accessibility/length matching alone is insufficient in the adversarial synthetic nuisance used here.
4. QC covariates must exclude the target program genes and target cis peaks.
5. Learning a module externally and transporting frozen weights into a separate-nucleus cohort is materially more discriminating than testing same-cohort raw correlation.
6. The strongest current transported statistic still has too much null/seed overlap to qualify at these donor counts.

## What V53 does NOT demonstrate

V53 does not demonstrate:

- that real FULL104 relational state is regulatory;
- that any real Morabito/SEA-AD/GSE214979 biological outcome is positive;
- that cis coupling has passed;
- that a biological-versus-arbitrary-technical semantic twin is identifiable;
- that SCENIC+, chromVAR, motif activity, peak topics, or cis modules are biologically validated;
- training authority.

## Scientific interpretation

The correct state after V53 is:

CIS_POSITIVE_SIGNATURE_IMPROVED_BUT_NOT_QUALIFIED__TRANSPORTED_MODULE_ROUTE_PROMISING__REAL_BIOLOGY_STILL_CLOSED

Do not tune a numerical threshold against these simulations until it passes.

The next successor should reduce null variance or add independent structure prospectively, not alter the failure criterion after seeing the result.

## Prospective V54 design requirements

The next synthetic successor should compare, before real outcome access:

1. many matched pseudo-cis modules, not four, with a computationally efficient internal null;
2. rank/ordinal cross-cohort transport;
3. program-excluded RNA and ATAC QC;
4. full matching on at least GC, accessibility, peak length, gene density/locality, mappability, and distance-to-TSS/local architecture;
5. an ATAC-only module construction route so confirmation RNA is never used to define its own regulatory object;
6. a transported supervised route with weights learned only in development, as a separate candidate;
7. coherent, mixed-sign, and sparse mandatory positives;
8. weak positive only as a power curve;
9. same-nucleus-only, donor-global, and locus-structured technical negatives;
10. exact semantic twin retained as an explicit non-identifiability boundary.

If none of those prospectively separates the mandatory planted positives from the frozen nuisance class, record INSUFFICIENTLY_SPECIFIC_AGAINST_SHARED_CROSS_MODAL_TECHNICAL_STATE and stop rather than spending Morabito or SEA-AD.

## Local execution custody

Exact local development artifacts from this chat:

- pairwise producer: SHA-256 c666f74ded102554867231289d60eec475d5232601b7862992f732c12b7e391f
- pairwise result JSON: 0c3638cd54a9ebcbbfc57857d74b4e5f40f7492c29186c58d92580e4ccd9209a
- PC1 module producer: d5a46b303ba1804da05951697ed8e588cad5ec19aeebf5fff3dd25ec30d2fe5e
- PC1 result JSON: 0ae2b5303bda857389b21506213eea3437964566ad2f1b6add8e8ed784d669d3
- transported-module optimized producer: 626127294a5eaad5f6be181ea98024f08392fe93fe2b7d66921b37015f8a8ff6
- transported-module result JSON: 69cd16bf9d99a4940620addf4d6bc7e8c5aa1ea29cde06d6002e734b71f46b49

Two exploratory many-decoy implementations exceeded the fixed local execution window and produced no accepted scientific result. They are not used as evidence.

No protected biological outcome was opened.
