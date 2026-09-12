# V5 numeric dimension authority blockers — 2026-09-12

Status: `DIMENSION_MECHANICS_HARDENING_IN_PROGRESS__NUMERIC_AUTHORITY_NOT_CLOSED__NO_TRAINING_AUTHORITY`

This document prevents the new dataset-first selector, artifact-binding, and firewall code from being mistaken for a numeric production dimension result.

## What is now implemented

On `planning/v5-dataset-first-production-closure-20260912`:

1. The corrected 42-shard TRAIN cache cannot masquerade as FULL104.
2. FULL104 production closure is exclusively the 8,915-block V4 binder terminal:
   `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`.
3. A real FULL104 binder receipt is projected and sealed into an exact dimension-input artifact, pinned to block manifest, materialization contract/audit, metadata SQLite, selection, and selection-manifest hashes.
4. The authenticated metadata SQLite digest is pinned to `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`.
5. D_shared mechanics implement the prospective joint-support + one-SE contiguous-prefix rule, including held-donor predictability as a required gate.
6. D_private has a prospectively frozen candidate rule, created before any FULL104 dimension outcomes are visible; it remains candidate authority pending independent review.
7. D_obs has a prospectively frozen candidate rule using held-operator reconstruction of lawful observation descriptors; it remains candidate authority pending independent review.
8. Metric artifacts bind score rows to exact FULL104 input + execution receipt. D_private additionally binds to the exact frozen D_shared selection.
9. Selection artifacts bind the selected/expansion terminal to the exact metric artifact.
10. The dimension execution firewall now permits a one-SE-selected dimension smaller than the longest jointly supported prefix, but forbids selecting beyond that prefix.
11. Row-identity-only closure no longer satisfies the dimension firewall; physical FULL104 expression closure is required.

None of the above is a numeric D result.

## Remaining blocker A — physical FULL104 execution

The exact 8,915-block store has not been executed in this ChatGPT runtime.

The remote execution contract is:

`docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`

Until the physical store returns the exact V4 PASS and sealed dimension-input artifact, no real dimension metric execution can begin.

## Remaining blocker B — real full-stream metric executors

The current selectors consume metric rows but do not compute them from expression.

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

## Remaining blocker C — Monte-Carlo / donor-resample precision authority

The repository requires:

- `null_replicates_derived_from_error_budget = true`
- `donor_resamples_derived_from_error_budget = true`

but no recovered frozen executable rule currently determines those replicate counts.

Therefore historical constants such as 256, 999, or 1000 must not be promoted merely because old diagnostics/tests used them.

A lawful successor must prospectively define and independently review:

1. what Monte-Carlo quantity is being precision-controlled;
2. its tolerated error;
3. the family-wise failure/risk budget across ranks/views/gates;
4. the mathematical rule mapping that budget to replicate counts or a predeclared stopping rule;
5. hard minimum/maximum execution bounds if sequential;
6. deterministic RNG and replay semantics.

This rule must be frozen before seeing FULL104 dimension outcomes.

## Remaining blocker D — candidate-rule review

`V5_D_PRIVATE_SELECTION_RULE_CANDIDATE_V1.json` and `V5_D_OBS_SELECTION_RULE_CANDIDATE_V1.json` were deliberately written before real numeric outcomes, but they are still candidate authorities.

They require independent review before a real numeric dimension receipt can be frozen.

## Required terminal before dimensions can become production inputs

No numeric `D_shared`, `D_private`, `D_total`, or `D_obs` may become production authority until all four blockers above close and the final receipt passes `DimensionExecutionFirewallV1` and `DimensionAuthorityV4` while remaining `training_authorized: false`.

This dimension closure is still only a prerequisite for bounded V5 qualification; it does not authorize production training or relational target activation.
