# Target-discovery handoff from V79 real-biology inspection — 2026-10-12

Status: `INFORMATION_HANDOFF__NO_AUTOMATIC_TARGET_AUTHORITY`

## Why this exists

The V79 synthetic lane inspected authenticated TRAIN biology to make rare synthetic worlds realistic. These biological findings may also matter to target discovery and should not remain siloed.

## Inputs used

- frozen V6R5A/T1 program weights SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`
- authenticated 50K × 41,238 TRAIN discovery expression NPZ SHA-256 `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`
- 50K sample: 104 TRAIN donors; HVS 10,958 cells, NPH52 5,221, SEA-AD 33,821
- no pathology/DEV/SEALED/TEST outcomes used

## Findings to carry into target discovery

1. `innovation_tail`, `recurrent_5pct`, and `recurrent_1pct` use the same molecular weight vector. Historical rare5/rare1 are frequency thresholds on one direction, not distinct biological programs.
2. That historical innovation direction is strongly source-shifted in the 50K TRAIN sample:
   - upper 5%: NPH52 1,889 / HVS 347 / SEA-AD 264
   - upper 1%: NPH52 499 / HVS 1 / SEA-AD 0
3. A bounded native-label microglia subset contained 665 cells across 66 donors. Its upper-tail cells occurred across all three sources and multiple donors, so donor-recurrent rarity is feasible, but this subset is too small/uneven and the score too source-shifted to freeze prevalence from it.
4. Therefore any candidate rare biological target derived from this historical direction needs source/operator-aware re-evaluation before promotion.

## Cross-lane rule

Synthetic work may continue to discover/freeze real TRAIN biological programs when needed for realistic synthetic worlds. Any such program, topology, prevalence/effect estimate, or confounding finding that could inform target discovery should be handed into this lane with hashes and provenance.

This handoff does not select a target by itself. Target discovery may use these findings under its own current governance and compare them with corrected replay, regulatory, spatial, multimodal and other evidence.
