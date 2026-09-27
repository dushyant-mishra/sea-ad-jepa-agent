# The resolution ladder on the corrected view

Date 2026-09-27. Inputs: corrected extraction
`FULL104_MYELOID_R8_PANEL_EXTRACTION_V1.json` (decoded view), ladder
`FULL104_RESOLUTION_LADDER_V1.json`, variance components
`LADDER_VARIANCE_COMPONENTS_V1.json`. Supersedes the ladder retracted in
`V29_LEVEL4_GENE_IDENTITY_DEFECT_AND_RETRACTIONS_20260927.md` for HVS and
SEA-AD; the NPH52 arm was never affected and is unchanged.

## What the correction did to the data

The same nuclei, the same panels, the same producers — only the column identity
differs. Detection of the panel genes moves from implausible to ordinary:

| cohort | program | zero fraction, scrambled | zero fraction, corrected |
|---|---|---|---|
| SEA-AD myeloid-restricted | HLA_DRA_ANTIGEN | 74.5% | **15.0%** |
| SEA-AD myeloid-restricted | P2RY12_HOMEOSTATIC | 83.7% | **20.3%** |
| SEA-AD myeloid-restricted | APOE_LIPID | 79.4% | **29.8%** |

NPH52 is identical in both runs, as it must be: it carries an identity map.

## The ladder

187,909 nuclei, 104 donors, 8,076 blocks all SHA-256 verified, identity closure
exact. Correlations between two halves at matched depth. `mol` holds the nuclei
fixed and splits their molecules — the ceiling. `dis` uses two disjoint sets of
nuclei from the same donor. `scr` is the donor-scramble control.

**SEA-AD Immune, myeloid-restricted — 135,666 nuclei, 46 donors, 316 strata**

| program | | k=1 | k=2 | k=5 | k=10 | k=25 | k=50 | k=100 |
|---|---|---|---|---|---|---|---|---|
| HLA_DRA | mol | 0.544 | 0.655 | 0.798 | 0.877 | 0.942 | 0.972 | 0.985 |
| | dis | 0.127 | 0.235 | 0.465 | 0.643 | 0.811 | 0.903 | 0.948 |
| P2RY12 | mol | 0.464 | 0.568 | 0.744 | 0.844 | 0.928 | 0.963 | 0.983 |
| | dis | 0.149 | 0.263 | 0.499 | 0.670 | 0.838 | 0.907 | 0.956 |
| APOE | mol | 0.433 | 0.521 | 0.682 | 0.778 | 0.882 | 0.933 | 0.964 |
| | dis | 0.066 | 0.133 | 0.289 | 0.437 | 0.649 | 0.793 | 0.890 |

The donor-scramble control collapses in **every cohort and every program** —
all fifteen report `control_collapsed: true`, with scrambled correlations within
±0.09 of zero at every rung. Under the scrambled columns, three of the fifteen
were declared VOID by this same control.

## Variance components, and they pass their own falsification test

The two ladder arms are two equations in the same three unknowns, so
`A/W = (1 + M(k)) / (2k · (M(k)/D(k) − 1))` is closed form, where A is
between-donor variance and W is within-donor nucleus-to-nucleus variance. Every
rung yields an independent estimate and **nothing forces them to agree**, so
their spread is a genuine test of the two-component model rather than a fit
statistic.

| cohort | program | W/A | rung spread | verdict |
|---|---|---|---|---|
| SEA-AD myeloid-restricted | P2RY12 | **2.9×** | 1.15 | consistent |
| SEA-AD myeloid-restricted | HLA_DRA | **4.0×** | 1.11 | consistent |
| SEA-AD myeloid-restricted | APOE | **8.4×** | 1.24 | consistent |
| SEA-AD Immune (unrestricted) | P2RY12 / HLA_DRA / APOE | 3.0 / 4.3 / 9.1 | 1.07–1.32 | consistent |
| SEA-AD caudate | APOE / P2RY12 / HLA_DRA | 12.0 / 9.5 / 12.1 | 1.43–1.83 | consistent |
| NPH52 MG | APOE / HLA_DRA | 7.7 / 6.9 | 1.63–1.70 | consistent |
| NPH52 MG | P2RY12 | 11.5 | 3.02 | **inconsistent** |
| HVS Microglia-PVM | all three | 1.3 / 2.2 / 1.8 | 2.47–3.21 | **inconsistent** |

Eleven of fifteen are consistent, with seven independent rungs agreeing to
within a factor of 1.07 to 1.83. The four that are not are the two smallest
cohorts: HVS has 2,117 nuclei across 30 donors, so its upper rungs rest on very
few pairs. Those four are reported as inconsistent rather than quoted.

**Within-donor, nucleus-to-nucleus variance is 3 to 12 times the between-donor
variance**, in every cohort where the model holds.

Removing lymphocytes and monocytes barely moves it — 9.1 → 8.4, 3.0 → 2.9,
4.3 → 4.0 — so the 1.9% non-myeloid fraction was not driving the result. The
striatal caudate cohort sits systematically higher (9.5–12.1) than the cortical
ones, which is a difference worth its own question rather than an average.

## What this does and does not establish

It establishes that a per-nucleus quantity here is **measurable** — molecule-split
reliability at k=1 is 0.43 to 0.68, not noise — and that most of what it measures
is **not** shared with the donor. A donor-level or neighbourhood-level target
discards the larger part of the variation. That is the necessary condition for a
per-nucleus teacher target, and it is the first time this project has had it on
verified data.

It does not establish that W is biology. W is within-donor variance of the
measured activity ratio, and per-nucleus technical variation that fails to
cancel in that ratio — ambient RNA, capture efficiency, nuclear size,
dissociation stress — lives there too. Separating them requires the six reserved
readout genes, which are extracted and deliberately unspent.

No teacher has been fitted and no biological claim is made from either view.

---

## Correction and supersession, 2026-09-27

Two defects in the artifact these results were computed from, both found in
review after the results above were reported.

### 1. Unmeasured written as zero

Two addresses are structurally absent from their sources: LPL (13734) from the
filtered HVS object, PGK1 (2628) from all eleven SEA-AD matrices. The extractor
recorded both, per matrix, in the receipt — and wrote their values into the
counts array as `0`, indistinguishable from a measured zero. PGK1 is affected
in **170,528 of 187,909 nuclei, 90.8%**; LPL in 2,117, 1.1%.

The ladder above was not misled — every query and panel address is available in
every matrix, and the panel sums never touch either gene. But the artifact is
unsafe for any later consumer, and one diagnostic reported above IS wrong: the
"8-gene housekeeping reference" is a **7-gene** reference for SEA-AD, so its
quoted zero fraction is understated.

`full104_myeloid_panel_extraction_v3_masked.py` emits `address_available` per
nucleus per address, and refuses to write if a nonzero count ever sits at an
unavailable address. `full104_resolution_ladder_v2_masked.py` requires that
mask, refuses any artifact lacking it, and marks a program VOID rather than
computing when a partner address is unavailable for the rows it was given.

**Consequence for the independent-readout test, which has not run:** LPL is a
reserved readout of APOE_LIPID. HVS must be excluded from any evaluation
requiring observed LPL, and the mask is what makes that enforceable rather than
remembered.

### 2. My description of the denominator was wrong, not merely loose

I wrote that "HVS's reference denominator therefore includes LPL where other
sources exclude it." That is false. HVS never measured LPL, so LPL contributes
nothing to HVS's total observed count and there is nothing to include.

What the implementation actually computes:

> `total_excluding_29` = the nucleus's total observed count **minus the ban-set
> addresses that this matrix actually measures**.

An unmeasured address contributes nothing to the total and is not subtracted
from it, so the arithmetic is self-consistent. But the subtracted gene set
differs between sources — 29 for NPH52, 28 for HVS and for each SEA-AD matrix —
which makes this a **source-specific reference**. That is defensible within a
source. It is not automatically comparable across sources, and any cross-source
transport claim needs an explicit comparability check first. No such check has
been run, and none of the results above depends on one, because every cohort is
reported on its own.
