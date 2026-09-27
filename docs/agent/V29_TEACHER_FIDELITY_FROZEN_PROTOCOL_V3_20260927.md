# Frozen protocol v3 — teacher-only biological fidelity

**Supersedes v1 (`027866e8`, sha256 `5aead8ed…`) and v2. v1 and v2 are void; this
document is the sole authority.**

**Frozen 2026-09-27, still before any control gene was extracted and before any
outcome was computed.** Five defects were found in external red-team review, all
structural, none data-dependent. That is what makes these revisions legitimate:
no result existed to steer them.

## The five corrections

1. **Six directed tests, not nine.** With each program read out by the other
   two there are 6 ordered predictor→readout pairs. Three by three counted the
   self-pairs already excluded as circular.
2. **The stratum control is a transformation, not a fitted effect.** A donor
   dummy has no coefficient for a held-out donor. Replaced by leave-one-out
   within-stratum centering, defined below.
3. **One denominator authority.** v1 and v2 each carried two competing
   denominator descriptions. The formula in §3 below is now the only one; every
   other wording is deleted, not superseded-in-place.
4. **The unit of qualification is prospectively defined** in §6. Previously a
   pass was defined per readout with nothing said about the program, leaving
   the aggregation rule to be invented once results were visible.
5. **MEG3 removed from the ambient panel.** Unlike SNAP25, SYT1 and RBFOX3 it
   is not cleanly neuronal-specific — an imprinted lncRNA with broad expression
   — and no rationale was offered for it. A control panel is only as specific as
   its least specific member.

## 1. What is tested

R8's measured per-nucleus program state
`S_P = (activity_P, CLR composition over P's four partners)`. Not a trained
teacher. The question is whether `S_P` carries biological information the
technical confounders do not already supply.

## 2. The six directed tests

| predictor | readout |
|---|---|
| APOE_LIPID | P2RY12_HOMEOSTATIC |
| APOE_LIPID | HLA_DRA_ANTIGEN |
| P2RY12_HOMEOSTATIC | APOE_LIPID |
| P2RY12_HOMEOSTATIC | HLA_DRA_ANTIGEN |
| HLA_DRA_ANTIGEN | APOE_LIPID |
| HLA_DRA_ANTIGEN | P2RY12_HOMEOSTATIC |

All six are reported, including failures. No program gene predicts itself; no
reserved gene is touched.

## 3. Denominator — the single frozen authority

For a directed test with predictor program *P* and readout program *Q*, define
the excluded address set

```
EXCLUDED(P,Q) = query(P) ∪ panel(P)          5 addresses
              ∪ query(Q) ∪ panel(Q)          5
              ∪ RESERVED                     6   SALL1 CTSD CTSS LPL CSF1R HLA-DMB
              ∪ HOUSEKEEPING                 8
              ∪ AMBIENT                     10   §4
              ∪ MYELOID_IDENTITY             6
              ∪ MITOCHONDRIAL                3
```

and for each nucleus *i*

```
D_i(P,Q) = total_all_i  −  Σ  counts_i[a]   over a ∈ EXCLUDED(P,Q) with address_available_i[a]
```

Both activities in that test use **this same** `D_i(P,Q)`:

```
activity_P,i = log1p( 10000 · Σ panel(P) counts_i / D_i(P,Q) )
activity_Q,i = log1p( 10000 · Σ panel(Q) counts_i / D_i(P,Q) )
```

`D` is rebuilt per directed pair and contains **no gene of either program**, so
it cannot induce correlation between them through shared membership. It remains
a *shared* denominator, which still couples the two ratios through sequencing
depth — that coupling is depth, and depth is a control (§4). A nucleus with
`D_i(P,Q) ≤ 0` or with any `EXCLUDED` address unavailable in a way that makes
`D` undefined is dropped, and the count dropped is reported.

## 4. Controls

| control | genes |
|---|---|
| depth | `total_all`, `source_library`, and the log of each |
| ambient RNA (10) | SNAP25, SYT1, RBFOX3 · PLP1, MBP, MOBP · GFAP, AQP4, SLC1A2 · FLT1 |
| generic myeloid identity (6) | AIF1, ITGAM, SPI1, FCER1G, TYROBP, LAPTM5 |
| mitochondrial (3) | MT-CO1, MT-ND1, MT-ATP6 |
| query-only | the queried gene of *P*, alone |

Ambient genes are lineage-foreign to microglia: their detection in a microglial
nucleus is contamination rather than expression. The query-only control is the
sharpest test of the construction itself — if four partners add nothing over the
single queried gene, the target is not earning its complexity.

## 5. Design

- **Stratum control — leave-one-out within-stratum centering.** For every
  predictor and for the readout, subtract the mean of the nucleus's own
  `donor × operator` stratum computed *excluding that nucleus*. Computable on a
  held-out donor from its own cells, so it transfers. Leave-one-out prevents a
  nucleus contributing to the mean subtracted from itself.
  **Disclosed transduction:** centering a held-out stratum uses that stratum's
  own readout values collectively. This is deliberate — the estimand is
  within-stratum association and the stratum mean is a nuisance being profiled
  out — and no nucleus's own readout enters its own centering.
- **Minimum stratum size 20 nuclei.** Smaller strata are dropped; the number
  dropped is reported per cohort.
- **Split:** held-out donors, two thirds fitting / one third evaluation, by hash
  of the source-specific donor identity. Sources never pooled.
- **Model:** ridge; regularisation cross-validated within fitting donors only.
- **Statistic:** per evaluation donor, the increment in Spearman correlation
  between predicted and observed readout from adding `S_P` to the controls.

## 6. Decision rule and unit of qualification

**A directed pair passes** if both:

1. the median per-donor increment exceeds the **95th percentile** of a null
   permuting `S_P` **within stratum**, 200 permutations; and
2. the increment is positive in at least **two thirds** of evaluation donors.

**A program qualifies** only if **both** of its directed tests pass. One of two
is reported as *partial* and does **not** qualify the program. This is stated
now so the aggregation rule cannot be chosen after the results are visible.

**The primary reporting unit is the directed pair.** No program-level claim is
made beyond the rule above, and no cross-program or cross-cohort aggregate
statistic is introduced later.

**Failure is a result.** No refitting, no changing controls, no dropping donors,
no reporting whichever readout looked better.

## 7. What a pass would mean

Preliminary evidence of **same-assay program coherence** — one RNA program's
per-nucleus state predicting another's within a donor and region, beyond depth,
ambient contamination, generic myeloid identity and the queried gene alone.

Not independent validation. Both sides are the same molecules from the same
nucleus on the same assay; a shared technical factor the controls miss would
produce the same signature.

## 8. Standing constraints

- Reserved and frozen: **SALL1, CTSD, CTSS, LPL, CSF1R, HLA-DMB**.
- HVS excluded from anything requiring observed LPL, enforced by the mask.
- Every input recorded by SHA-256 in the result receipt — the direct response to
  R7/R8 hashing their scripts and outputs but not the cache that determined
  their numbers.
- No teacher fitted, no student trained, training off.
- Scope: the audited addresses in candidate myeloid nuclei. Nothing here speaks
  to the other ~41,000 addresses or to the training substrate.
