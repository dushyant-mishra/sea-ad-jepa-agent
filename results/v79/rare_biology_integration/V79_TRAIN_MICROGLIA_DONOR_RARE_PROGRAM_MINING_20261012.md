# V79 TRAIN microglia donor-structured rare-program mining — 2026-10-12

Status: `REAL_TRAIN_DISCOVERY__SYNTHETIC_CALIBRATION_AND_TD_HANDOFF__NO_TARGET_PROMOTION`

## Substrate

Read-only analysis of the existing authenticated FOUNDATION discovery expression asset and frozen sample metadata. No new ETL and no pathology fields.

Microglia-like cells were restricted to the existing native/broad labels `Microglia-PVM`, `MG`, and `Microglia-PVMSubclass`.

- 665 cells
- 66 donors
- HVS 128 cells / 23 donors
- NPH52 304 cells / 16 donors
- SEA-AD 233 cells / 27 donors

The analysis aggregated expression to donor means, centered genes within source, selected residual-variance genes, and decomposed donor residual structure. This follows the earlier S174 result that donor effects survive measurement/source adjustment while fixed operator effects are not stable enough to be treated as biology.

## Donor-residual structure

The first eight source-centered donor PCs explain approximately 11.8%, 9.7%, 8.1%, 6.3%, 5.0%, 4.5%, 3.9%, and 3.7% of selected-gene residual variance.

Several PCs had strongly right-skewed donor scores, showing that donor-structured rare tails exist in this TRAIN microglia subset. The strongest PC1 tail had one donor above +2 SD and very high positive skew; other PCs produced recurrent +2 SD cell-level tails across 10–19 donors.

## Candidate biological motifs

Three biologically interpretable motifs were stress-tested because they appeared among high-loading genes:

1. `IRF5_IFIT1`: IRF5, IFIT1, FRAT2, WWC1, VPS29, CTBS, MAPKAPK3, UGP2, CDC42EP4, EDEM1, ACOT4.
2. `CR1_S100A12`: CR1, S100A12, NOXA1, CCDC69, ABI2, BCAP29, ITPK1, GRHPR, CHMP2B, NAB1, VANGL2, COMMD6.
3. `SIGLEC15_NINJ1`: SIGLEC15, NINJ1, TALDO1, GSTZ1, SAAL1, ATP5F1C, GFUS, EIF4B, BFAR, GPN1.

At a within-source +2 SD cell-score threshold:

- `IRF5_IFIT1`: 27 cells / 19 donors; HVS 3, NPH52 12, SEA-AD 12.
- `CR1_S100A12`: 20 cells / 16 donors; HVS 2, NPH52 6, SEA-AD 12.
- `SIGLEC15_NINJ1`: 25 cells / 15 donors; HVS 2, NPH52 13, SEA-AD 10.

No single donor contributed more than 20% of any +2 SD tail. Thus the tails are donor-recurrent rather than single-donor artifacts.

## Critical falsification result

These motifs are **not qualified as cross-source biological programs**.

Median donor-level pairwise gene correlation after source centering was positive when pooled across sources, but source-stratified coherence was not stable:

| module | HVS median corr | NPH52 median corr | SEA-AD median corr |
|---|---:|---:|---:|
| IRF5_IFIT1 | 0.287 | -0.054 | -0.063 |
| CR1_S100A12 | 0.472 | 0.014 | -0.033 |
| SIGLEC15_NINJ1 | 0.634 | -0.079 | -0.058 |

Independent within-source PCA strengthened this warning: among the top-30 genes from PCs 1–6 in each source, the maximum cross-source overlap was only one gene, with zero source-PC pairs sharing two or more top genes.

Therefore these motifs must not be frozen as project biological targets from this analysis alone.

## What is scientifically supported

1. Donor-structured rare expression tails are real enough to model in the synthetic qualification family.
2. Rare-state prevalence should vary strongly by donor, including exact-zero/weak donors.
3. A realistic simulator must allow the *observed gene manifestation* of a shared latent program to vary with source/technology rather than requiring identical observed top genes in every dataset.
4. Technical/source structure can manufacture apparently coherent rare modules; cross-source recurrence must be a hard falsifier.
5. The three motifs above are useful **candidate stress-test motifs / target-discovery leads**, not validated rare-state truth.

## Synthetic-lane consequence

Use the empirical donor recurrence and tail sizes to calibrate donor heterogeneity, but do not copy these exact gene sets into planted truth as if validated. The synthetic rare state should be generated from a latent biological program plus source-specific observation operators, with an explicit world in which a plausible-looking rare gene module is source-specific and therefore biologically false.

## Target-discovery handoff

Target discovery should receive:

- evidence that donor-structured rare residuals persist in real TRAIN microglia;
- the three candidate motifs and their donor/source recurrence;
- the failed cross-source-coherence result;
- a recommendation to test these motifs against stronger regulatory/multimodal evidence before any target promotion.

No pathology, protected validation outcome, DEV/SEALED/TEST outcome, or JEPA optimization was used.
