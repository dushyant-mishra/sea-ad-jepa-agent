# Macha V77 cross-lane audit — 2026-10-07

Status: `AWARENESS_AND_REUSE_BOUNDARY_ONLY`

Audited branch: `claude/v77-synthetic-premise-custody-20261005`

Audited head: `976d2be6c8cfaf46e7dfd79bf900fb9fc4c0d4bd`

This note records what the target-discovery / physical-axis repair lane may reuse from Macha's V77 synthetic-qualification lane and what it must not infer.

## Current V77 state

Macha's lane remains a synthetic qualification / anti-cheat lane. `TRAINING=OFF`; mutation/training promotion is not authorized; no target, representation, estimand, weighting, threshold, multimodal object or biological winner is selected.

The branch has advanced substantially since the Oct-5 checkpoint, including repaired measurement support, adapter / bridge qualification, dynamic-range and background investigations, shortcut audits, S157 paired challenge work, and S174 cache-axis investigation.

## S157 terminal result

The frozen S157 terminal receipt establishes engineering/identifiability facts only:

- an exact same-assay semantic twin is observationally non-identifiable;
- raw source/operator identity can separate some operator-linked nuisance but is an exploratory positive control, never an authorized learned input;
- lawful depth/support descriptors do not resolve the operator twin;
- measurable-address count is a strong identity proxy;
- the current synthetic state signal is too weak for S157 to establish cell-state biology;
- seed 7302 is DEVELOPMENT_CALIBRATION only;
- no biological or representation winner is selected.

Do not cite S157 as evidence that a particular real biological target is correct.

## S149 calibration status

Historical pooled real-data calibration results are suspended.

The earlier claim that pooled real dependence is dominated by cohort composition (`S149`) was computed from the Stage81A3R corrected-real TRAIN cache. S174 later established that this cache carries the HVS/SEA-AD physical feature-axis defect. Therefore S149 is not currently valid evidence; it is suspended pending corrected replay, not declared false.

Anything address-specific or pooled across HVS/SEA-AD/NPH from the affected cache is non-reusable until repaired. Some within-family gene-label-free summaries may survive, but they require claim-specific review.

## S174 value-level result — REUSE, DO NOT REPEAT

Macha prospectively pre-registered and then executed the owner-authorized narrow read-only TRAIN probe on 36 cells: 12 from one HVS matrix and 12 each from SEA-AD MTG and DFC/A9.

Result:

| matrix | agreement with historical positional map | agreement with true gene-ID map | decoder agreement |
| --- | ---: | ---: | ---: |
| HVS c5e9db26 | 1.0000 | 0.0298 | 1.0000 |
| SEA-AD MTG | 1.0000 | 0.0249 | 0.9990 |
| SEA-AD DFC/A9 | 1.0000 | 0.0240 | 0.9991 |

Interpretation: the V77 real TRAIN cache reproduces the scrambled positional mapping exactly and agrees with true gene identity only near chance; the Sept-27 decoder recovers the true values at ~99.9-100% in the probed matrices.

Named marker examples include MBP, PLP1 and SNAP25 where the source contains substantial counts but the cache value at the intended gene address is zero because the slot corresponds to a different physical gene.

This result is already prospectively bound and should be reused as an existing sentinel suite. The target-discovery / physical-axis lane must not reread the same cells merely to prove the same defect again.

## Repair direction shared by both lanes

Macha records the owner's preferred repair direction as:

`matrix-native stable gene ID -> physical H5AD column -> canonical molecular address`

with the Sept-27 decoder retained as an independent validation oracle.

This matches `JEPA_HVS_SEAAD_PHYSICAL_AXIS_REPAIR_CONTRACT_20261007.md`.

The production repair should not automatically inherit the decoder's conservative 682 SEA-AD dropped columns when a fresh gene-ID join can uniquely resolve them; those differences must instead be reported explicitly.

## Cross-lane reuse rules

1. Reuse the S174 pre-registration, result hashes and 36-cell value-level evidence as existing physical-axis sentinels.
2. Do not rerun S149 or any affected V77 real calibration until a corrected substrate exists and replay is separately authorized.
3. Do not interpret S157 as selecting global, local, program or structured-combined biological targets.
4. Preserve S157's anti-cheat lessons: raw operator/source identity is not a production learned input; support pattern / measurable-address count can act as identity shortcuts.
5. Do not execute Macha's bounded-mutation successor from this lane; runtime mutation remains a separate authority.
6. Do not open multimodal / Morabito evidence merely because the V77 evidence matrix discusses it; no multimodal object is selected.
7. Keep historical contaminated V77 artifacts immutable.

## Verification caveat

Macha's head commit reports `124/124` V77 tests passing locally. GitHub's combined-status endpoint currently exposes no remote status checks for that head, so treat the local test claim as recorded evidence, not an independently observed CI run.

## Current cross-lane conclusion

`S174 = VALUE_VERIFIED`

`V77_REAL_CACHE = CONTAMINATED_FOR_HVS_SEAAD_GENE_IDENTITY`

`S149 = SUSPENDED_PENDING_CORRECTED_REPLAY`

`S157 = SYNTHETIC_IDENTIFIABILITY / ANTICHEAT EVIDENCE, NOT BIOLOGICAL_TARGET_SELECTION`

`REPAIR_DIRECTION = FRESH_GENE_ID_JOIN + DECODER_CROSS_CHECK`

`REBUILD = NOT_AUTHORIZED`

`TRAINING = OFF`
