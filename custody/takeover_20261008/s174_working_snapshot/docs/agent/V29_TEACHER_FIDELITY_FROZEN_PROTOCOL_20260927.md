# Frozen protocol — teacher-only biological fidelity

**Frozen 2026-09-27, before any control gene was extracted and before any
outcome was computed.** Nothing below may be changed after seeing a result. If
the analysis turns out to need a different rule, that rule is a new protocol
with a new freeze, and the result computed under it is labelled exploratory.

## What is being tested, and what "teacher" means here

Not a trained neural teacher. The object under test is the **measured target
construction** itself — R8's per-nucleus program state — and the question is
whether it carries biological information that the technical confounders do
not already supply.

For program *P*, the per-nucleus state is
`S_P = (activity, CLR composition over the four partners)`, activity being
`log1p(10000 · partner_sum / reference)` exactly as R8 defines it, with the
reference being the source-specific `total_excluding_29 + controls` denominator
recorded in the artifact.

## The readout, and why it is not circular

The readout for program *P* is the **activity of the other two programs**,
which are non-reserved and disjoint in gene membership from *P*. For
APOE_LIPID the readouts are the P2RY12_HOMEOSTATIC and HLA_DRA_ANTIGEN
activities; and symmetrically.

This is a real biological expectation rather than an arbitrary pairing:
homeostatic microglial identity (P2RY12, TMEM119, CX3CR1, GPR34) and
disease-associated lipid handling (APOE, APOC1, GPNMB, TREM2, ABCA1) are
reported to trade off within a donor. If the per-nucleus state is biology, one
program's state should carry information about another's **within a single
donor and region**, beyond depth and contamination.

A program gene is never used to predict itself, and no reserved readout is
touched.

**Shared-denominator hazard, and its fix.** Two activities computed against the
same denominator correlate through the denominator alone. Each program's
activity is therefore computed against a denominator that EXCLUDES every gene
of both the predictor and the readout program. Denominators are rebuilt per
comparison; the artifact's single `total_excluding_29` is not reused for this.

## Controls, all of which the program state must beat

| control | built from |
|---|---|
| depth | `total_all`, `source_library`, log of each |
| ambient RNA | lineage-foreign module: SNAP25, SYT1, RBFOX3, MEG3 (neuronal), PLP1, MBP, MOBP (oligodendrocyte), GFAP, AQP4, SLC1A2 (astrocyte), FLT1 (endothelial) — detection of these in a microglial nucleus is contamination, not expression |
| generic cell identity | pan-myeloid module: AIF1, ITGAM, SPI1, FCER1G, TYROBP, LAPTM5 |
| mitochondrial | MT-CO1, MT-ND1, MT-ATP6 |
| query-only | the queried gene's own count, alone (APOE / P2RY12 / HLA-DRA) |
| stratum | donor × operator fixed effect, so every comparison is within one donor and one brain region |

The query-only control is the one that matters most for the project's own
question: if the four-partner state adds nothing over the single queried gene,
the elaborate target construction is not earning its complexity.

## Design

- **Donor split.** Held-out **donors**, not cells. Two thirds of each source's
  donors to fitting, one third to evaluation, assigned by a hash of the
  source-specific donor identity so the split is reproducible and independent
  of any outcome. Sources are never pooled.
- **Model.** Ridge regression, predicting readout activity from controls, then
  from controls plus `S_P`. Regularisation chosen by cross-validation **within
  the fitting donors only**.
- **Statistic.** Per evaluation donor, the increment in Spearman correlation
  between predicted and observed readout, from adding `S_P` to the controls.
  Reported per donor; summarised by the median across evaluation donors.

## Decision rule, frozen

A program passes for a given readout if **both** hold:

1. the observed median per-donor increment exceeds the **95th percentile** of a
   null in which `S_P` is permuted **within stratum** (donor × region),
   200 permutations; and
2. the increment is positive in at least **two thirds** of evaluation donors.

The permutation null is the primary instrument precisely so that no arbitrary
effect-size threshold has to be defended. The two-thirds donor criterion exists
because a large effect in one donor is not a per-nucleus finding.

**Failure is a result.** A program failing either criterion is recorded as
unqualified and is NOT rescued by refitting, by changing controls, by dropping
donors, or by trying the other readout and reporting the better one. All
program × readout combinations are reported, including the failures.

## What a pass would and would not mean

A pass is **preliminary evidence of same-assay program coherence**: one RNA
program's per-nucleus state predicting another RNA program's per-nucleus state
within a donor and region, beyond depth, ambient contamination, generic myeloid
identity and the queried gene alone.

It is **not** independent biological validation. Both sides come from the same
molecules in the same nucleus on the same assay, so a shared technical factor
not captured by the controls would produce the same signature. Independent
validation needs a different modality, and that is a separate lane.

## Standing constraints

- The six reserved readouts — **SALL1, CTSD, CTSS, LPL, CSF1R, HLA-DMB** —
  are frozen and used by nothing here.
- HVS is excluded from anything requiring observed LPL. The availability mask
  enforces this rather than a reader remembering it.
- No teacher is fitted, no student is trained, and production training stays
  off.
- Scope remains the audited addresses in candidate myeloid nuclei. Nothing here
  speaks to the other 41,000-odd addresses or to the training substrate.
