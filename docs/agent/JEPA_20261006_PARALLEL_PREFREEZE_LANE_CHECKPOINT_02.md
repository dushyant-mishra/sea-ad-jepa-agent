# JEPA parallel premise-prefreeze lane checkpoint 02 — 2026-10-06

This is a takeover checkpoint only; it does not authorize Stage A or training.

Working branch:

`design/premise-qualification-contract-v3-20261006`

Current progress:

- `b149de6e60aa2b068453dd7926217af5e107667a` — V3 premise design from current `main@102aa267...`, adding observation-operator, basis/subspace stability, evidence-vs-depth and dual-OOD support contracts.
- `47739d86b2c7cb50809436386062d2f2d0d5ade5` — four-family representation tournament prefreeze, no winner.
- `b17f5016242894ef0190539e29ba61af55942e16` — observation-operator prefreeze contract, with lawful measurement descriptors and forbidden unrestricted identity covariates.

Important interpretation:

- `GLOBAL_CELL_STATE`, `QUERY_LOCAL_STATE`, `PROGRAM_STATE`, `STRUCTURED_COMBINED_STATE` remain co-equal candidates.
- `cell_state` has no incumbent advantage.
- `width=160` remains architecture capacity only.
- coordinate-level biological interpretation requires axis stability; a stable rotating subspace permits subspace/block claims only.
- biological-evidence convergence and measurement-depth convergence are now separate required diagnostics.
- `D_measurement` and `D_biological_support` are separate OOD axes.
- technology should be modeled as an observation process, not an unrestricted biological covariate or free dataset-ID embedding.

Hard boundaries unchanged:

`TRAINING=OFF`; `STAGE_A_EXECUTION=NOT_AUTHORIZED`; TEST sealed; Morabito protected; no target/representation/estimand selected.

Next tasks for this lane:

1. external-validation asset matrix using existing PRs #188-#199 without redoing completed audits;
2. foundation-population estimand comparison with selection left `UNSET_REQUIRES_APPROVAL`;
3. basis/subspace stability protocol details;
4. biological-evidence vs measurement-depth protocol details;
5. machine-readable premise/representation/observation contracts and governance tests once wording stabilizes.

Runtime reconciliation is a separate lane. Do not duplicate optimizer/EMA/checkpoint work here.
