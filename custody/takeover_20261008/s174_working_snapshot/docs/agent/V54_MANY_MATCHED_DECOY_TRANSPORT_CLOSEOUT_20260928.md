# JEPA V54 — 100 fully matched pseudo-cis modules

Date: 2026-09-28  
Status: synthetic qualification attempt — **RED / NOT QUALIFIED**  
Governance: `TRAINING=OFF`, `TD60=BLOCKED`, no real regulatory biology opened.

## Prospective change from V53

V53 showed that transported frozen cis weights were the strongest candidate, but four pseudo-cis modules left a broad random-null tail. V54 changed one scientific feature prospectively: each of 18 genes received **100 fully matched pseudo-cis modules**.

Everything load-bearing was frozen before execution:

- 12 development donors;
- 18 separate-nucleus-style confirmation donors;
- 5 cis peaks per gene;
- ridge lambda 8, carried forward from V53;
- rank/ordinal transforms;
- program-excluded RNA and ATAC QC;
- full matching on GC-like composition, accessibility, peak length, gene-density/locality, mappability-like structure, and TSS/local-architecture structure;
- negatives: independent, development-only same-nucleus, donor-global, locus-structured;
- mandatory positives: coherent, mixed-sign, sparse;
- weak mixed positive: power curve only;
- success rule unchanged from V53: minimum mandatory-positive q10 minus maximum negative q90 must be > 0.

A mechanical batched-`solve` RHS bug was fixed before any result existed. Two monolithic executions then exceeded the local tool window. The final run used process isolation plus one BLAS thread per worker; this changed execution mechanics only. The frozen seed block and all scientific inputs/statistics were unchanged.

## Primary result

Primary statistic: mean empirical percentile rank of the frozen true cis module among 100 equally trained, fully matched pseudo-cis modules in the independent confirmation cohort.

Robust margin:

`-0.014301430143014326`

Therefore V54 is **RED**.

The limiting boundary is narrow:

- `POS_MIXED` q10 = **0.6016**
- `NEG_LOCUS` q90 = **0.6159**

Other mandatory positives were more clearly separated:

- coherent q10 = **0.6412**, median = **0.8487**
- sparse q10 = **0.6856**, median = **0.8273**
- mixed median = **0.7195**

Negative medians remained near the expected matched-null center:

- independent = **0.5102**
- development-only same-nucleus = **0.4986**
- donor-global = **0.4807**
- locus-structured = **0.5193**

This is substantial improvement over V53, but the predeclared pass criterion was not met.

## Mutation/diagnostic controls

The controls reproduce the two V53 design lessons.

### Under-matching is dangerous

For `NEG_LOCUS`:

- full matching median rank = **0.5193**
- partial matching median rank = **0.6111**

Failing to match gene-density/mappability/local-architecture-like covariates pushes a purely technical locus-structured world toward a false positive.

### Program-inclusive QC attenuates the positive

For `POS_MIXED`:

- program-excluded QC median = **0.7195**
- program-inclusive QC median = **0.5806**

Therefore target-program genes/cis peaks must remain excluded from nuisance/QC covariates.

## Secondary ATAC-only PC1 result

The unsupervised ATAC-only PC1 module did not qualify:

robust margin = **-0.18377**.

It works well for coherent and sparse positives but performs poorly for mixed-direction cis structure. It should not replace the supervised transported module as the primary candidate.

## Scientific interpretation

Do **not** increase the number of decoys again simply to make the margin cross zero. With 100 decoys, the dominant uncertainty is no longer Monte-Carlo null resolution; it is seed/donor-level relational variance, particularly for mixed-sign programs.

The next scientifically justified change is to align the statistic with the actual JEPA target:

**test transported within-donor relational/ordinal state across genes, rather than treating every gene as an independent endpoint.**

This is not a threshold change. It is a different prospectively defined biological object: whether an externally learned cis model reproduces the ordering/geometry of the multi-gene cellular state in a separate-nucleus confirmation cohort.

Exact observable semantic twins remain outside the identifiable claim class.

## Custody

Local exact SHA-256:

- scientific producer: `d1da94c9dc1893a4b30666b23c63f4461bbdd4ecec65ea7665e9c2645b256e84`
- process-isolated runner: `8c8343af6803c761cf7ed121525b5aed7b33737d94ee981c756e95979d248c16`
- result JSON: `5c01e654216d344281389e6470e0e83f4e0768e5820d5fe97771207279d7860e`

No real biological outcome was opened.
