# Target-discovery handoff — STAT1-like donor-structured rare program

Date: 2026-10-12  
Status: `REAL_TRAIN_DISCOVERY_HANDOFF__NOT_TARGET_PROMOTION`

## What the synthetic lane found

Using the authenticated 50K pathology-blind TRAIN discovery sample, restricted to 665 exact-label microglia cells from 66 donors across HVS, NPH52 and SEA-AD, the Stage75 STAT1 target module retained a donor-recurrent upper tail after source-specific correction for detected-gene count.

At source-specific residual +2 SD:

- 27/665 cells (4.06%);
- 17/66 donors positive;
- HVS: 7 cells / 7 donors;
- NPH52: 8 cells / 3 donors;
- SEA-AD: 12 cells / 7 donors;
- no donor contributes more than 3 tail cells.

The original raw STAT1 +2 SD tail is almost entirely retained after the detected-gene correction, so detected-gene count alone does not explain the state.

Empirical stress regimes from the same residual direction are:

- +1.5 SD: 6.62% cells, 28 positive donors;
- +2.0 SD: 4.06% cells, 17 positive donors;
- +2.5 SD: 2.71% cells, 11 positive donors;
- +3.0 SD: 1.65% cells, 7 positive donors.

Among positive donors at +2 SD, median within-donor prevalence is 14.3%, Q75 is 22.2%, and many donors are exact zero.

## Why STAT1 is the strongest current regulatory lead

Stage75 classifies STAT1 as Tier A with direct motif support. The direct candidate module contains 15 targets: AIF1, APOE, B2M, BSG, C1QB, CD74, CTSB, FCER1G, GPX4, HLA-DPA1, LAPTM5, NFKBIA, NPC2, PRDX1 and TXNIP. Stage76 candidate sign is positive for all except GPX4. These remain candidate/soft regulatory edges, not validated regulation or causality.

In donor summaries, regulator-to-target-module association is positive in HVS and NPH52, unlike several alternate regulators that reverse sign across sources. Individual target detectability varies strongly by source, so this is better viewed as a candidate latent regulatory program with source-dependent RNA manifestation than as a universally identical marker panel.

## Important limits

This result does **not** establish STAT1 as the project target, causal regulator, universal microglial state, or same-cell multimodal truth.

- Full-module RNA gene-gene coherence is not stable across all sources.
- The earlier quality audit found some association with total summed expression; detected-gene correction removes one major shortcut but not every possible measurement confound.
- Current Stage81A1B evidence says exact same-nucleus multiome linkage is available, but STAT1-specific multiome edge support was not inferred/frozen there.
- GSE214979 is authenticated same-nucleus RNA+ATAC, but no current cached result demonstrates STAT1-specific same-cell RNA/ATAC coherence.
- Morabito remains separate-nucleus donor-level evidence only.

## What the synthetic lane froze from this

PR #311 now contains an implemented/tested fixture generator using:

- donor activity probability calibrated from 17/66 positive donors for the central regime;
- positive-donor prevalence sampled from the measured donor-prevalence distribution;
- source-specific target visibility from the TRAIN microglia subset;
- source assigned after latent biology so technology cannot cause R;
- separate same-nucleus, separate-nucleus, RNA-only and frequency-matched technical-twin worlds;
- STAT1 Stage75/76 topology as the first prototype.

The generator fixture passed 7/7 local invariant tests. A 100-seed central-regime check produced mean donor-active fraction 26.1% and mean cell prevalence 4.89%; this is synthetic fixture behavior, not new real-data evidence.

## Target-discovery recommendation

Carry STAT1 forward as a **high-priority candidate rare regulatory program for adjudication**, alongside the failed-cross-source PCA-derived motifs as lower-confidence stress-test leads.

The next lawful biological tests are:

1. remaining measurement shortcut checks on the real TRAIN state;
2. donor-primary source-aware recurrence under the target-discovery rare-program contract;
3. after foundation target freeze, same-nucleus GSE214979 RNA+ATAC coherence/recoverability;
4. Morabito donor-level separate-nucleus recurrence;
5. perturbational support only after target-engagement qualification.

Do not use the synthetic planted ATAC component as evidence that real STAT1 chromatin coherence already exists. It is a prospective hypothesis derived from the regulatory evidence structure.
