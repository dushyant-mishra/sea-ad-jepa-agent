# JEPA Macha/V77 — pre-S149 mechanism-verdict spillover audit

Date: 2026-10-06
Parent before write: `05068b99d1806b065fbc9b1d2459acaa592efe32`
Working Macha head: `a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Finding

Two preserved V77 receipts contain strong mechanistic verdict language derived from the old pooled real topology target:

- `V77_STEP3_FACTOR_FAMILY_FALSIFICATION_V1.json`: `FACTOR_MODEL_FAMILY_FALSIFIED...`
- `V77_SUBSTATE_FAMILY_DECISION_V1.json`: `SUPPORTED_FOR_NEXT_STAGE...`

Both use pooled real topology quantities such as detection transitivity ~0.887, mean degree ~1844 and fraction |r|>0.3 ~0.615 as the reference structure.

S149 subsequently showed that a large fraction of that pooled topology can arise from study/coverage composition without within-stratum gene dependence. The later `V77_WITHIN_COHORT_AUTHORITY_CORRECTION_V1.json` explicitly states that pooled envelopes are composition-inclusive references and **not a biological target**.

## Correct current interpretation

The old experiments remain useful engineering/mechanistic explorations of how synthetic generators behave against the historical pooled reference.

They do **not** currently establish:

- that continuous factor biology is falsified as a model of real biological structure;
- that discrete sub-state biology is supported as the correct real mechanism;
- that the historical pooled transitivity must be reproduced biologically.

Current classifications:

`V77_STEP3_FACTOR_FAMILY_FALSIFICATION_V1 = SUPERSEDED_AS_BIOLOGICAL_MECHANISM_VERDICT__HISTORICAL_POOLED_REFERENCE_EXPLORATION_ONLY`

`V77_SUBSTATE_FAMILY_DECISION_V1 = SUPERSEDED_AS_BIOLOGICAL_MECHANISM_SUPPORT__HISTORICAL_POOLED_REFERENCE_EXPLORATION_ONLY`

## Biological meaning

The earlier logic treated a highly clustered gene-correlation graph as if cells themselves generated all of that structure. S149 showed that combining studies with different measurable gene sets can manufacture much of the same graph.

Therefore we cannot conclude that biology requires giant discrete gene blocks merely because those blocks mimic the pooled graph.

## What survives

Useful surviving observations include:

- exact per-cell detection constraints can strongly alter observed correlation topology;
- observation/capture mechanics can destroy or create apparent graph structure;
- synthetic family comparisons are useful once the correct biological/measurement estimand is prospectively defined.

These are mechanism diagnostics, not current biological selection authority.

## Supersession-map gap

The canonical `CURRENT_SUPERSESSION_MAP.md` does not yet name these V77 receipts specifically. Combined with their strong internal `FALSIFIED` / `SUPPORTED` wording, this creates a historical-spillover risk.

A future coordinated canonical-governance refresh should explicitly route them as superseded biological-mechanism verdicts while preserving their historical bytes.

## Authority unchanged

TRAINING=OFF; STAGE_A_EXECUTION=OFF; STAGE4=NOT_AUTHORIZED; TEST=SEALED; MORABITO=PROTECTED; 500K=NOT_AUTHORIZED; no target/representation/estimand winner.
