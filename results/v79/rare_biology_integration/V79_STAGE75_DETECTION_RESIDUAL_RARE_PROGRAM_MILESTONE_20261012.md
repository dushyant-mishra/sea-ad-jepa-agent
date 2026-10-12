# V79 Stage75 TRAIN rare-program milestone — detection-residual audit

Date: 2026-10-12
Status: `REAL_TRAIN_SYNTHETIC_CALIBRATION_FINDING__TARGET_DISCOVERY_HANDOFF_REQUIRED__NOT_PROJECT_TARGET_AUTHORITY`

## Question

Do the donor-recurrent Stage75 regulatory-module tails found in the 665-cell / 66-donor pathology-blind TRAIN microglia subset survive a direct measurement-quality challenge, or are they simply high-detection cells?

## Inputs

- Existing authenticated 50K FOUNDATION TRAIN discovery sample and freeze.
- 665 exact-label microglia cells: HVS 128 / 23 donors; NPH52 304 / 16 donors; SEA-AD 233 / 27 donors.
- Frozen Stage75 regulator-target topology. Stage75 edges remain candidate regulatory support only; they are not validated causal GRN edges.
- Seven tested modules: ELF1, SPI1, STAT1, BACH1, CEBPA, IRF8, RELA.

## Method

For each source separately, module score was regressed on standardized detected-gene count plus a quadratic detected-gene term. A residual rare tail was then defined at source-specific mean + 2 SD. This is a measurement-shortcut falsifier, not a new biological target-selection rule.

## Result

All seven regulatory-module tails survive detected-gene residualization and remain donor-recurrent across all three sources.

At the residual +2 SD tail:

| module | tail cells | unique donors |
|---|---:|---:|
| SPI1 | 29 | 20 |
| STAT1 | 27 | 17 |
| ELF1 | 26 | 14 |
| CEBPA | 25 | 18 |
| RELA | 25 | 19 |
| BACH1 | 23 | 19 |
| IRF8 | 21 | 16 |

No module is dominated by one donor. For STAT1 the maximum contribution from any donor is 3/27 tail cells (11.1%). STAT1 residual-tail donors are HVS 7, NPH52 3 and SEA-AD 7.

Critically, the original STAT1 +2 SD tail is almost unchanged after this correction:
- HVS: 7 raw-tail cells -> 7 residual-tail cells; 7/7 retained.
- NPH52: 7 -> 8; all 7 original cells retained.
- SEA-AD: 11 -> 12; all 11 original cells retained.

Thus the STAT1 tail is not explained by detected-gene count alone.

## Empirical STAT1 rarity regimes

Using the same source-specific detection-residual STAT1 direction, progressively stronger residual thresholds give:

| threshold | cells | fraction of 665 | positive donors | zero donors |
|---|---:|---:|---:|---:|
| +1.5 SD | 44 | 6.62% | 28 | 38 |
| +2.0 SD | 27 | 4.06% | 17 | 49 |
| +2.5 SD | 18 | 2.71% | 11 | 55 |
| +3.0 SD | 11 | 1.65% | 7 | 59 |

At +2 SD, source-specific cell prevalence is HVS 5.47%, NPH52 2.63%, SEA-AD 5.15%. Among positive donors, the median within-donor prevalence is 14.3%; many donors are exact zero.

These are calibration observations, not universal biological prevalence claims. They provide empirical donor-heterogeneity and rarity scales for synthetic worlds instead of arbitrary pooled 1%/5% planting.

## Interpretation

STAT1 is the strongest current *synthetic biological prototype*, not a final project target:

1. Its Stage75 regulator-to-target-module association is positive in HVS and NPH52 TRAIN donor summaries, whereas several other regulators reverse sign across sources.
2. Its rare tail recurs across donors and all three sources.
3. The tail survives detected-gene residualization.
4. Its RNA manifestation is strongly source-dependent at the individual target-gene level, consistent with a latent program whose observed RNA evidence can be incomplete under different measurement operators.

This supports using a STAT1-like topology for an initial synthetic donor-structured regulatory program and for a teacher-private/partial-RNA world. It does **not** establish STAT1 as a real project target, causal regulator, or universally coherent RNA program.

## Important remaining falsifier

The previous quality audit also found association with total summed log1p expression. This milestone removes detected-gene count as the dominant simple shortcut but does not claim all measurement-quality dependence is eliminated. The synthetic design must therefore include a frequency-matched high-quality/high-depth pseudo-rare twin and retain an explicit measurement-shortcut gate.

## Synthetic consequence

Initial rare-program construction can now use measured TRAIN scales:
- heterogeneous donor prevalence with many exact-zero donors;
- a recurrent ~4% cell-level regime as a central calibration point, with ~1.5-7% stress regimes available from stronger/weaker residual thresholds;
- source-specific observable target subsets/effect visibility rather than forcing identical RNA coherence across technologies;
- a matched technical pseudo-rare world driven by detection/depth without biological latent state;
- STAT1-like regulatory topology as the first prototype, with SPI1/BACH1/etc. retained as alternate/control topologies.

Q00-Q11 remain immutable. No pathology, protected outcome selection, qualification scoring or JEPA training is opened by this result.