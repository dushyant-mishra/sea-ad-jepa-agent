# JEPA Macha/V77 — S146/S147 iterative self-audit

Date: 2026-10-06
Branch: `handoff/jepa-20261006-macha-audit-successor`
Parent observed before write: `02386ffebdcf4b6c664a4cd25a95b9334133f459`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## What is verified

The repaired observer uses `S146_S147_NAME_MAPPED_REGISTRY_RELATIVE_V1`.

The repair is structurally correct in the current code:

- source identity is mapped by cohort NAME rather than positional index (S146);
- operator support is converted from registry-relative support to support within the cohort's measurable vocabulary, preventing the same coverage loss from being applied twice (S147);
- source/operator cohort mismatches are refused;
- the active repaired component runner builds every world fresh and checks the support-rule ID before scoring;
- current v3/v4 component oracles refuse pre-repair worlds unless historical reproduction is explicitly requested.

## Repaired detect/reject receipt

`results/v77/V77_COMPONENT_DETECT_REJECT_REPAIRED_SUPPORT_V1.json`

The receipt was executed from clean head `8497916e5a9d9b232597ac1891b6c630d3b17931` and later committed in the branch lineage.

All four intended OFF twins are rejected:

- B4 off rejected
- C1 off rejected
- C2 off rejected
- C3 off rejected

But the ON-world designed-range result is **3/4**, not 4/4.

B4 has `r2_band = 0.8502684499537796` against the frozen designed pass range `[0.25, 0.45]`, so its formal `detect` field is false because it is much MORE recoverable than the designed class.

Therefore the precise statement is:

`ALL_OFF_TWINS_REJECT__3_OF_4_ON_WORLDS_INSIDE_FROZEN_DESIGNED_RANGE__B4_OVERRECOVERABLE`

Biological meaning: the instrument clearly distinguishes B4 present vs absent, but the synthetic B4 effect is stronger/easier than the frozen design expected. That is a calibration warning, not a clean 4/4 pass.

## Historical spillover check

`v77_measure_oracle_ceilings_v2.load_v2_world()` is a lower-level loader that does not itself check the repaired support-rule ID. Direct command-line verdict use is disabled, and current v3/v4 verdict paths perform the support check before loading.

Classification:

`LATENT_BYPASS_PRIMITIVE__NO_CURRENT_VERDICT_PATH_FOUND`

This should eventually be hardened at the loader boundary so future code cannot accidentally bypass the S146/S147 provenance check.

## Current claim ledger

- repaired support semantics: `REPRODUCED_FROM_CODE`
- all four OFF-twin rejections: `SUPPORTED_BY_COMMITTED_RECEIPT`
- 4/4 designed-range detection: `FALSE__ACTUAL_IS_3_OF_4`
- B4 presence/absence discrimination: `SUPPORTED_BUT_OVERRECOVERABLE`
- pre-repair absolute signed values: `SUPERSEDED`

## Boundaries unchanged

`TRAINING=OFF`
`STAGE4=NOT_AUTHORIZED`
`TEST=SEALED`
`MORABITO=PROTECTED`
`TARGET_WINNER=NONE_QUALIFIED`
`REPRESENTATION_WINNER=NONE_QUALIFIED`
