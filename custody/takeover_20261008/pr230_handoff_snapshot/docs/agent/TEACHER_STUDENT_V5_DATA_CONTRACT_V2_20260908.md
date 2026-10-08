# Teacher/Student V5 data contract V2 — 2026-09-08

Status: `PROSPECTIVE_DESIGN_ONLY__NO_TRAINING_AUTHORITY`

## Principle

The reader-fit dataset defines what is observed and what is estimable. Scientific weighting defines what population the objective represents. Compute packing may execute that objective efficiently, but may not redefine support, sampling weights, or relational contribution.

## 1. Native biological support is the information-preserving view

The 41,238-address namespace remains canonical, but measured scalar support differs materially across operators.

- HVS: 18,736 measured scalar addresses/operator.
- NPH52: 30,294–34,405 measured scalar addresses/operator.
- SEA_AD: 35,076 measured scalar addresses/operator.

The native-support JEPA view therefore retains every structurally measured address available to the operator. Structurally unmeasured addresses are not manufactured as zeros and need not consume packed compute.

No fixed production mask fraction, visible-gene count, target-block count, or block size is selected here.

## 2. Common support is a comparability/calibration view, not a replacement input

Outcome-blind support profiling found exactly 17,186 canonical addresses measured by all 42 reader-fit operators (41.675% of the 41,238-address universe).

Relative to source-wide all-operator measured support, that common core retains approximately:

- HVS: 17,186 / 18,736 = 91.73%.
- NPH52: 17,186 / 29,136 = 58.99%.
- SEA_AD: 17,186 / 35,076 = 49.00%.

Using only the common core as the primary teacher input would therefore discard genuine measured information, especially in NPH52 and SEA_AD. V5 instead separates:

- `native_support_policy_id`: information-preserving teacher/student support;
- `comparable_support_policy_id`: an exact cross-operator support set;
- `comparable_support_role`: restricted to `CALIBRATION_ONLY`, `CONSISTENCY_DIAGNOSTIC_ONLY`, or `DISABLED` until a separately reviewed objective says otherwise.

Merely defining the common core does **not** authorize a second loss, loss coefficient, auxiliary optimization target, or masking rule.

## 3. Scientific target and proposal sampler are separate authorities

Reader-fit cell counts are highly source-imbalanced:

- HVS: 198,718 / 4,553,407 = 4.36% of cells;
- NPH52: 236,476 / 4,553,407 = 5.19%;
- SEA_AD: 4,118,213 / 4,553,407 = 90.44%.

Donor counts are much less skewed: HVS 41, NPH52 17, SEA_AD 46 of 104 donors.

The descriptive estimand analysis therefore keeps the following distinct:

- target estimand `p(cell)`;
- proposal sampler `q(cell)`;
- importance-weight policy `p/q`;
- compute microbatch packing.

No target or proposal is selected here. Under a cell-uniform proposal, a donor-uniform target has ~2149.52x max/min importance-weight spread with ~9.68% relative ESS; a source-donor-uniform target has ~5816.34x spread with ~3.67% relative ESS. Those diagnostics are reasons to design the proposal around the chosen scientific estimand, not reasons to let compute convenience choose the estimand.

Weighted block-JEPA accumulation is required to be invariant to unequal compute partitioning.

## 4. Relational sampling authority is not a per-group scalar weight

Full reader-fit donor×operator groups are ragged: median 228 cells, maximum 42,209. Exhaustive anchored triplets are impossible at production scale.

A future relational training authority must separately bind:

- which scientific relations are eligible;
- the finite sampling policy;
- how groups/cells are weighted in the relational objective;
- the compute budget used to realize the policy.

The V2 contract therefore uses `relational_sampling_policy_id` under scientific sampling and a separate `relational_compute_budget_id` under compute packing. A scalar `triplets_per_group` must not silently become scientific group weighting.

The exact TD57B/TD59/TD60 qualification triplets/nulls remain separate frozen qualification semantics.

## 5. RNG and packed execution boundary

Packed execution is a new numerical implementation, not bitwise V4 continuation. The reference stochastic address is collision-free over the actual uint64 reader-fit stable-key domain:

`[stable_cell_key_low32, stable_cell_key_high32, canonical_token_key+1, feature_index]`

with run/update/view/layer/site deriving the Philox key.

The proof encoder is bound to that reference contract. Tensor position, packed position, microbatch ordinal, and device are not scientific random identities.

Even with objective/gradient agreement, floating reduction order can change near-zero gradients enough for AdamW to diverge. Therefore packed V5 requires its own mechanical qualification before any execution authority.

## 6. Qualification mechanics remain distinct

Historical bounded qualification values such as batch 128, microbatch 8, 4 views, 40% within-measured masking, 16 blocks, replay cap 8, and u40 are not promoted to full-reader production values by inheritance.

Production schedule quantities require separate reader-fit/hardware-derived authority, including exposure-aware training horizon and EMA half-life.

## Current authority

- V4 remains the frozen audited baseline.
- V5 remains prospective/inactive.
- No scientific estimand is selected.
- No proposal sampler is selected.
- No production evidence dose, block geometry, relational budget, GPU token budget, training horizon, or EMA horizon is frozen.
- `training_authorized = false`
- `successor_u0_materialization_authorized = false`
- `td60_execution_authorized = false`
