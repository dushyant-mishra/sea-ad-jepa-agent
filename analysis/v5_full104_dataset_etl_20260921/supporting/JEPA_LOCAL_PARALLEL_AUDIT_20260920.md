# JEPA local parallel audit — 2026-09-20

Status: **SUPPORTING/HISTORICAL ONLY unless explicitly labeled current-authority input.**

No terminal masking outcome, D_shared, pathology, DEV/SEALED outcome, or training was opened or executed.

## 1. Local inventory classification

### Current-authority inputs verified byte-for-byte

From `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`:

- `contracts/address_namespace.csv` SHA-256 `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- `support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` SHA-256 `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

These match the current FULL104 authority roots.

### Historical/supporting artifacts available locally

- Foundation 50K discovery sample freeze + operator metadata
- reconstructed 50K 41,238-address expression archive, exact SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- T1 checkpoints u0/u10/u25/u50/u100/u200/u205, each verified against signed checkpoint manifest
- Foundation calibration tables and 84-cell truth table

### Quarantined / never current authority

`66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` hashes to
`001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`.
The 2026-09-19 handoff explicitly labels this a historical supporting result with a prior provenance-mismatch warning and says never current authority. It is not used below to establish a current result.

## 2. Historical 50K source sparsity: aggregate-safe calculation

The final historical 50K matrix contains 50,000 cells × 41,238 addresses with 246,702,069 nonzeros (overall ledger density 0.1196479310).

The old expression audit contains per-shard nnz only for operators 0–34, so row-level alignment to source/operator is not trusted. Source-level aggregate results below use:

- authenticated HVS/SEA-AD shard nnz from the audit;
- NPH52 nnz by exact subtraction from the final matrix total;
- source/operator measured-address counts from the authenticated support table;
- 50K source/operator cell composition from the frozen sample registry.

Measured-zero fraction among each source's **measurable** address slots:

| source | cells | detected fraction | measured-zero fraction | mean nnz/cell |
|---|---:|---:|---:|---:|
| HVS | 10,958 | 0.235657 | **0.764343** | 4,415.27 |
| SEA_AD | 33,821 | 0.149937 | **0.850063** | 5,259.20 |
| NPH52 | 5,221 | 0.117909 | **0.882091** | 3,916.52 |

Interpretation boundary: historical/supporting only. This does **not** estimate current FULL104 source-specific strict-core sparsity, but it demonstrates that large source-dependent detection structure existed in the historical Foundation substrate and motivates the current source/operator sparsity audit.

## 3. Historical teacher representation already encoded technical support strongly

From `FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv`, evaluated on 45 held-out TRAIN donors at u0:

- `partial_H -> source`: balanced accuracy **1.0000**
- `partial_H -> operator`: balanced accuracy **0.4992**
- `partial_H -> support_measured_count`: R² **0.991084**
- `partial_CELL -> source`: balanced accuracy **0.952381**
- `partial_CELL -> support_measured_count`: R² **0.969797**

This is not a current V5 result. It is strong prior evidence that measurement/support geometry can dominate historical representations before training.

## 4. Measured zeros are preserved as measured evidence in the historical packed semantics

From the authenticated 84-cell truth table:

- measured slots: 2,123,806
- measured-zero slots: 1,744,636
- measured-zero fraction: **0.8214667441**
- unmeasured slots with nonzero expression: **0**
- hidden masks outside measured support: **0**

For each of four historical 40% masking views, about **82.1% of hidden measured target addresses were zero-valued**.

This confirms the historical model-side representation did not silently collapse measured zero into unmeasured/missing.

It also motivates a distinct audit: because old target blocks sampled measured addresses uniformly and the historical block JEPA loss was unweighted MSE over block states, most hidden target addresses were zero-valued. With the known trainable target-identity path, target-zero versus target-nonzero contribution to the JEPA objective deserves explicit stratification in any future real-teacher qualification.

## 5. Historical T1 gene-identity drift tracks support geometry

All seven checkpoint files were verified against the checkpoint manifest.

`tokenizer.gene_identity.weight` has shape 41,238 × 48.

Raw u0→u205 online identity drift is nonzero for all rows, including the 289 addresses measured by no source. The optimizer is AdamW with `lr=1e-4`, `weight_decay=0.01`, so raw movement cannot be read directly as learned signal.

A scalar decay component was estimated using the 289 unsupported addresses:

- fitted scalar `u205 ≈ 0.9997919 × u0`
- unsupported median residual after removing that scalar shrink: ~`3.5e-05`

By contrast, median decay-adjusted residual drift was:

- source families = 1: ~**0.01687**
- source families = 2: ~**0.01927**
- source families = 3: ~**0.01593**

Large support-pattern groups:

- NPH52 + SEA-AD, no HVS: n=9,714, median ~**0.01929**
- SEA-AD only: n=4,710, median ~**0.01940**
- strict all-42 common core: n=17,186, median ~**0.01593**
- measured by no source: n=289, median ~**0.000035**

Interpretation boundary: this is historical mechanism evidence, not current V5 closure. It supports the existing concern that address identity can become entangled with measurement/support geometry.

## 6. Current V2 masking-budget nuance

Current `TargetEvidenceBudgetAuthorityV2` intentionally defines burden as a fraction of **strict measured non-target addresses**, not per-cell realized nonzero RNA.

That is a deliberate anti-leakage rule:

> mask eligibility must not depend on whether the realized expression value in a cell is zero or nonzero.

Therefore, if the current FULL104 effective-burden audit finds that equal address cardinality removes systematically different detected-token / UMI / entropy burden across policies, the repair must **not** equalize masks using each held-out cell's realized nonzero pattern. That would make the mask itself value-dependent.

A lawful successor would need a prospective, training-only, value-independent burden definition (for example address-level expected detection or entropy weights), if scientifically justified.

## 7. Current normalization-denominator issue confirmed in code

The authenticated materializers calculate `source_library` from the full raw source row/column **before** filtering/mapping to the 41,238-address ledger.

Thus RNA outside the modeled ledger—including unmapped/blocked features—can affect every retained normalized value via:

`log1p(raw_count * 10000 / source_library)`.

Masking a target column does not remove this denominator route. The current F13 fixture correctly proves that already-materialized features do not recompute `source_library`, but it does not prove that the authentic biological target or excluded RNA contributed no information through the original denominator.

This is a genuine current mechanism requiring the GPU FULL104 denominator audit.

## 8. Historical package provenance quirk

The old `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json` shard list contains operators 0–34 only, whereas the final 50K sample/final matrix include NPH52 operators 35–41. Therefore row-level source/operator alignment was not assumed in this audit. Only aggregate calculations with explicit derivation are retained.

## 9. Files generated by this local parallel audit

- `historical50k_source_sparsity_aggregate_safe.csv`
- `historical_t1_gene_identity_drift_trajectory.csv`
- `historical_t1_gene_identity_drift_by_address.csv`
- `historical_t1_gene_identity_decay_adjusted.csv`
- `historical_t1_identity_drift_by_support_pattern.csv`

Earlier row-aligned `historical50k_sparsity_by_*` exploratory CSVs were generated before the historical audit shard-order mismatch was noticed. They must **not** be used as evidence. The aggregate-safe CSV supersedes them.

## 10. Current action

The GPU/Claude red-team lane should treat this document as prior/supporting evidence only and independently test current FULL104:

1. authentic normalization-denominator fractions;
2. actual policy-specific effective burden under value-independent masks;
3. source-specific target estimability/zero variance;
4. held-out-donor standardization estimand;
5. co-detection vs quantitative partner association;
6. target-identity × target-zero behavior;
7. calibration-cache tail coverage.

No current terminal masking outcome was opened here. `TRAINING_OFF` remains unchanged.