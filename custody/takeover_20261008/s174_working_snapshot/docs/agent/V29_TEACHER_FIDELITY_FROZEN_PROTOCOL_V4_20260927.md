# Frozen protocol v4 — teacher-only biological fidelity

**Prospectively dated successor to v3
(`d3366f18`, sha256 `3ecfa1953d2239528357c5d517a33d0dfe233f8300ca5759ad4e64279d4f725d`).**
v1, v2 and v3 are **preserved as historical record** and are not edited. This
document is the sole authority for execution.

**Frozen 2026-09-27, before any control gene was extracted and before any
outcome was computed.** Every change below is structural and data-independent.

## What changed from v3, and the one that matters

### A. Excluding genes does not fix a shared denominator — structural fix

v3 rebuilt the denominator per comparison to exclude every gene of both
programs, and I wrote that it therefore "cannot induce correlation between them
through shared membership," treating the remainder as depth that the controls
handled. **That reasoning was wrong.** Gene exclusion removes *membership*
leakage only. Both activities remain monotone decreasing in `D`, so if `D`
varies at all, two statistically independent numerators produce a clean,
confident, entirely artefactual correlation. A depth covariate helps only insofar
as it captures the exact functional form of `D`'s effect on a `log1p` ratio,
which it does not.

**v4 closes the pathway structurally rather than adjusting for it.** The primary
analysis contains no ratio on either side:

- **Readout:** the readout program's partner **count** `N_Q`, modelled by a
  negative-binomial GLM with **`log D` as an offset**. The denominator never
  appears as a ratio.
- **Predictor:** `S_P` decomposed into the part that is denominator-free by
  construction and the part that is not —
  - `CLR_P`: centred log-ratio over *P*'s own four partner counts. Invariant to
    any common scaling, so it carries no `D` whatsoever. **This is the primary
    predictor.**
  - `log1p(N_P)`: *P*'s partner count, a count and not a ratio, entering
    alongside the offset.

The v3 ratio-based formulation is retained only as a **secondary, explicitly
labelled susceptible** analysis, reported beside the primary and never used to
qualify anything on its own.

### B. Synthetic negative control, run before any real outcome

A simulation in which the two programs' counts are **independent by
construction** while the shared denominator varies as the real one does. The
full test pipeline — offsets, controls, centering, permutation null,
multiplicity — is run on it unchanged.

**If the test declares an association there, the test is broken and no real
result from it means anything.** This is a gate, not a diagnostic: it executes
and must pass before any real data is touched. A matched positive arm, with a
genuine injected association, must also pass, because a test that rejects
everything is equally useless.

### C. Denominator-matched sham program, on real data

For each directed test, a **sham predictor**: four genes drawn to match *P*'s
partner abundance distribution, with no biological relation to *Q*, carried
through the identical pipeline. The real program must beat the sham, not merely
beat zero.

### D. Statistic computed within stratum, then aggregated

v3 computed a per-donor Spearman increment. v4 computes the increment **within
each `donor × operator` stratum first**, then aggregates strata to the donor
(median across that donor's strata), then summarises across evaluation donors.
For SEA-AD a donor spans up to ten strata, and pooling them before computing the
statistic would let between-region variation enter a quantity that is supposed
to be within-region.

### E. Multiplicity across the six directed tests

Six related comparisons at a nominal 0.05 each would yield 0.3 expected false
positives. v4 computes an exact permutation p-value per directed test with
**B = 999** permutations —
`p = (1 + #{null ≥ observed}) / (1 + B)` — and applies **Benjamini–Hochberg at
q = 0.05 across the six directed tests within a cohort**. B rises from 200 to
999 so the p-value has the resolution BH needs.

### F. MEG3

Removed in v3 and it stays removed. It is an imprinted lncRNA with broad
expression, not cleanly neuronal-specific, and no rationale was offered for it.
The ambient panel is ten genes, each individually defensible.

## 1. What is tested

R8's measured per-nucleus program state — not a trained teacher — and whether it
carries biological information the technical confounders do not already supply.

## 2. The six directed tests

| # | predictor *P* | readout *Q* |
|---|---|---|
| 1 | APOE_LIPID | P2RY12_HOMEOSTATIC |
| 2 | APOE_LIPID | HLA_DRA_ANTIGEN |
| 3 | P2RY12_HOMEOSTATIC | APOE_LIPID |
| 4 | P2RY12_HOMEOSTATIC | HLA_DRA_ANTIGEN |
| 5 | HLA_DRA_ANTIGEN | APOE_LIPID |
| 6 | HLA_DRA_ANTIGEN | P2RY12_HOMEOSTATIC |

All six reported, including failures. No program gene predicts itself; no
reserved gene is touched.

## 3. The denominator — single frozen authority, with missingness

```
EXCLUDED(P,Q) = query(P) ∪ panel(P) ∪ query(Q) ∪ panel(Q)     10 addresses
              ∪ RESERVED 6 ∪ HOUSEKEEPING 8
              ∪ AMBIENT 10 ∪ MYELOID_IDENTITY 6 ∪ MITOCHONDRIAL 3

D_i(P,Q) = total_all_i − Σ counts_i[a]  over a ∈ EXCLUDED(P,Q)
                                         with address_available_i[a] == True
```

**Structural missingness.** An address with `address_available == False` is
never summed, never treated as a zero, and its absence is recorded per matrix.
A nucleus is **dropped** if `D_i ≤ 0`, or if any address of `panel(P)` or
`panel(Q)` is unavailable for it. Drops are counted and reported per cohort and
per directed test; they are never silently excluded.

`D` enters the primary analysis **only** as `log D`, an offset. It is never a
divisor there.

## 4. Controls

| control | genes |
|---|---|
| depth | `total_all`, `source_library`, logs of each |
| ambient RNA (10) | SNAP25, SYT1, RBFOX3 · PLP1, MBP, MOBP · GFAP, AQP4, SLC1A2 · FLT1 |
| generic myeloid identity (6) | AIF1, ITGAM, SPI1, FCER1G, TYROBP, LAPTM5 |
| mitochondrial (3) | MT-CO1, MT-ND1, MT-ATP6 |
| query-only | the queried gene of *P*, alone |
| sham program | four abundance-matched genes, §C |

## 5. Design

- **Stratum:** leave-one-out within-`donor × operator` centering of every
  predictor and of the readout. A transformation, so it transfers to held-out
  donors; LOO stops a nucleus contributing to the mean subtracted from itself.
  The transduction — a held-out stratum's own readouts forming its mean — is
  disclosed, and no nucleus's own readout enters its own centering.
- **Minimum stratum size 20 nuclei**; smaller strata dropped and counted.
- **Split:** held-out donors, two thirds fitting / one third evaluation, by hash
  of the source-specific donor identity. Sources never pooled.
- **Model:** negative-binomial GLM, `log D` offset; regularisation and
  dispersion estimated within fitting donors only.
- **Statistic:** increment in Spearman between predicted and observed readout
  count from adding `S_P` to the controls — computed **within stratum**, then
  median across a donor's strata, then summarised across evaluation donors.

## 6. Decision rule and unit of qualification

**A directed pair passes** if all three hold:

1. permutation p-value (within-stratum permutation of `S_P`, B = 999) survives
   **Benjamini–Hochberg at q = 0.05 across the six directed tests**;
2. the increment is positive in at least **two thirds** of evaluation donors;
3. the real program's increment **exceeds the abundance-matched sham's**.

**A program qualifies** only if **both** of its directed tests pass. One of two
is reported as *partial* and does not qualify the program.

**Primary reporting unit is the directed pair.** No other aggregate is
introduced later.

**Gates that must pass before any real result is read:** the synthetic negative
control must **not** declare an association, and the synthetic positive arm
must declare one.

**Failure is a result.** No refitting, no changed controls, no dropped donors,
no reporting whichever readout looked better.

## 7. What a pass would mean

Preliminary **same-assay program coherence** only. Not independent validation:
both sides are the same molecules from the same nucleus on the same assay.
It does not authorise teacher training.

## 8. Standing constraints

- Reserved and frozen: **SALL1, CTSD, CTSS, LPL, CSF1R, HLA-DMB**.
- HVS excluded from anything requiring observed LPL, enforced by the mask.
- Every input recorded by SHA-256 in the result receipt.
- No teacher fitted, no student trained, `TRAINING=OFF`, protected outcomes
  unopened.
- Scope: audited addresses in candidate myeloid nuclei. The 29-address repair
  does not license the general FULL104 reader.
