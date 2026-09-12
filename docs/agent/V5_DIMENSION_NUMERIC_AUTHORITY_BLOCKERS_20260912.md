# V5 numeric dimension authority blockers — 2026-09-12

Status: `HISTORICAL_FULL104_MATERIALIZATION_RECOVERED__CURRENT_REBINDING_AND_NUMERIC_AUTHORITY_OPEN__NO_TRAINING_AUTHORITY`

This document prevents the new dataset-first selector, artifact-binding, and firewall code from being mistaken for a numeric production dimension result.

## Historical correction: FULL104 preparation was already done

A 2026-09-12 repository-history audit recovered that the FULL104 production substrate was historically materialized and subsequently consumed by full-population analysis.

This means the current blocker is **not** “prepare the 4,553,407-cell dataset from scratch.”

Recovered historical evidence includes:

- Level-4 production expression materialization under `docs/history/full104_v014_20260826/03_phase2_state_derivation_v1/`;
- physical block root historically referenced as `outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`;
- 4,553,407 reader-fit cells;
- 104 donors;
- 42 operators / 42 matrices;
- 8,915 Level-4 expression blocks;
- 41,238 molecular addresses;
- block-manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`;
- materialization-contract SHA-256 `612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17`;
- materialization-audit SHA-256 `9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf`;
- Level-4 feature-matrix package root `c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef`;
- Level-4 multiview-feature package root `d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1`.

The FULL104 `ALL` executor was later completed under implementation fingerprint:

`a0fe5bc7be0769c9880763b3831ea330a251dfa710a8635b05f678c5d6e94202`

with terminal run-manifest SHA-256:

`8f292673c84447ee88f3a78936aa88920b96f0ffd681237e2b5af3e7dfe4d60c`.

The independent final adjudication records 4,108 fits, 640 exact production/independent support rows, and terminal `TEACHER_BIOLOGY_LIMIT` for the historical shared-state estimand. It explicitly does **not** claim that the corpus lacks biology. That old scientific result is not current V5 numeric dimension authority.

Therefore the present data task is:

`LOCATE_EXISTING_FULL104_BYTES -> VERIFY_FROZEN_HASHES -> REBIND_UNDER_CURRENT_V5_AUTHORITY`

not:

`REMATERIALIZE_FULL104_BY_DEFAULT`.

Reconstruction/rematerialization should only be considered if the historical heavy store is genuinely missing or corrupt.

## What is now implemented

On `planning/v5-dataset-first-production-closure-20260912`:

1. The corrected 42-shard TRAIN cache cannot masquerade as FULL104.
2. FULL104 production closure is exclusively the 8,915-block V4 binder terminal:
   `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`.
3. A real FULL104 binder receipt is projected and sealed into an exact dimension-input artifact, pinned to block manifest, materialization contract/audit, metadata SQLite, selection, and selection-manifest hashes.
4. The authenticated metadata SQLite digest is pinned to `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`.
5. D_shared mechanics implement the prospective joint-support + one-SE contiguous-prefix rule, including held-donor predictability as a required gate.
6. D_private has a prospectively frozen candidate rule, created before any current FULL104 dimension outcomes are visible; it remains candidate authority pending independent review.
7. D_obs has a prospectively frozen candidate rule using held-operator reconstruction of lawful observation descriptors; it remains candidate authority pending independent review.
8. Metric artifacts bind score rows to exact FULL104 input + execution receipt. D_private additionally binds to the exact frozen D_shared selection.
9. Selection artifacts bind the selected/expansion terminal to the exact metric artifact.
10. The dimension execution firewall now permits a one-SE-selected dimension smaller than the longest jointly supported prefix, but forbids selecting beyond that prefix.
11. Row-identity-only closure no longer satisfies the dimension firewall; physical FULL104 expression closure is required.

None of the above is a current numeric D result.

## Remaining blocker A — recover/location-bind and re-certify historical FULL104 bytes

The exact historical 8,915-block store has not yet been re-located and executed through the current V5 binder in this work lane.

The remote execution contract is:

`docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`

The first operation is to locate the existing heavy store on the GPU laptop / attached drive and verify its frozen parent hashes. Do not rebuild it merely because the current ChatGPT runtime cannot see the >30GB files.

Only if the historical store is unavailable/corrupt should a separate recovery/rematerialization authority be considered.

Until existing physical bytes return the exact current V4 PASS and sealed dimension-input artifact, no **current-authority** real dimension metric execution can begin.

## Remaining blocker B — real full-stream metric executors under the new V5 estimand

The historical FULL104 ALL executor proves full-population execution machinery existed and should be audited for implementation reuse. However, the current V5 selectors consume updated metric rows and do not yet compute those updated metrics from expression.

Production executors still need to compute, over authenticated FULL104 without per-stratum row caps:

### D_shared

- signal above a fully refit matched null;
- donor-resampled subspace stability;
- held-donor cross-view predictability and its donor-level SE;
- independent view/sketch agreement;
- increment beyond frozen measurement-shortcut baselines.

Every selecting null must preserve donor, operator, Q_DEPTH, Q_DETECT, and support/measurability, and refit the complete selecting geometry.

### D_private

Only after D_shared is frozen:

- held-donor incremental common-core biology prediction;
- held-operator increment;
- measurement-shortcut increment;
- same-cell technical-intervention stability.

Raw residual variance is not a lawful private-dimension target.

### D_obs

- held-operator reconstruction of lawful observation descriptors only;
- source/matrix identity are neither free inputs nor reconstruction targets;
- no biology qualification claim.

These executors must produce raw-output receipts whose hashes become the `execution_receipt_sha256` parents of the dimension metric artifacts. Hand-authored row tables are not production evidence.

Historical ALL streaming, sufficient-statistic, checkpoint/restart, storage, and independent-reconstruction code should be reviewed first and reused where compatible; historical numeric conclusions and sampled/cap-4 shortcuts must not be promoted.

## Remaining blocker C — Monte-Carlo / donor-resample precision authority

The repository requires:

- `null_replicates_derived_from_error_budget = true`
- `donor_resamples_derived_from_error_budget = true`

but no recovered frozen executable rule currently determines those replicate counts for the new V5 dimension estimand.

Therefore historical constants such as 256, 999, or 1000 must not be promoted merely because old diagnostics/tests used them.

A lawful successor must prospectively define and independently review:

1. what Monte-Carlo quantity is being precision-controlled;
2. its tolerated error;
3. the family-wise failure/risk budget across ranks/views/gates;
4. the mathematical rule mapping that budget to replicate counts or a predeclared stopping rule;
5. hard minimum/maximum execution bounds if sequential;
6. deterministic RNG and replay semantics.

This rule must be frozen before seeing new V5 dimension outcomes.

## Remaining blocker D — candidate-rule review

`V5_D_PRIVATE_SELECTION_RULE_CANDIDATE_V1.json` and `V5_D_OBS_SELECTION_RULE_CANDIDATE_V1.json` were deliberately written before current real numeric outcomes, but they are still candidate authorities.

They require independent review before a new numeric dimension receipt can be frozen.

## Required terminal before dimensions can become production inputs

No new numeric `D_shared`, `D_private`, `D_total`, or `D_obs` may become production authority until all four blockers above close and the final receipt passes `DimensionExecutionFirewallV1` and `DimensionAuthorityV4` while remaining `training_authorized: false`.

This dimension closure is still only a prerequisite for bounded V5 qualification; it does not authorize production training or relational target activation.
