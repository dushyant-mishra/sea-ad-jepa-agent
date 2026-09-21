# GPT parallel supporting audit — 2026-09-20

Status: **SUPPORTING/HISTORICAL ONLY unless explicitly labeled current-authority input.**

No terminal masking outcome, D_shared, pathology, DEV/SEALED outcome, or training was opened or executed.

## Current-authority inputs independently verified locally

From `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`:

- `contracts/address_namespace.csv` SHA-256 `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- `support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` SHA-256 `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

These match the current FULL104 authority roots.

## Historical 50K source sparsity — aggregate-safe

The historical final 50K matrix is 50,000 × 41,238 with 246,702,069 nonzeros. The old expression-audit shard list covers operators 0–34 only, while the final sample also contains NPH52 operators 35–41, so row-level historical source/operator alignment is not used here.

Source-level aggregates are safe because HVS/SEA-AD nnz come from authenticated shard totals, NPH52 nnz is exact subtraction from the final matrix total, and denominators use authenticated measured-support counts.

| source | cells | detected fraction among measurable slots | measured-zero fraction | mean nnz/cell |
|---|---:|---:|---:|---:|
| HVS | 10,958 | 0.235657 | **0.764343** | 4,415.27 |
| SEA_AD | 33,821 | 0.149937 | **0.850063** | 5,259.20 |
| NPH52 | 5,221 | 0.117909 | **0.882091** | 3,916.52 |

Interpretation: historical/supporting only. This is not a current FULL104 source-specific strict-core estimate, but it demonstrates that large source-dependent sparsity existed historically and gives the current Audit A/B/C lane a concrete prior to falsify.

## Historical teacher representation encoded support geometry before training

From `FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv`, evaluated on 45 held-out TRAIN donors at u0:

- `partial_H -> source`: balanced accuracy **1.0000**
- `partial_H -> operator`: balanced accuracy **0.4992**
- `partial_H -> support_measured_count`: R² **0.991084**
- `partial_CELL -> source`: balanced accuracy **0.952381**
- `partial_CELL -> support_measured_count`: R² **0.969797**

This is strong historical evidence that observation/support geometry can dominate representations even before training. It is not current V5 closure.

## Historical measured-zero semantics and zero-target pressure

In the authenticated 84-cell historical truth table:

- measured slots: 2,123,806
- measured-zero slots: 1,744,636
- measured-zero fraction: **0.8214667441**
- unmeasured slots with nonzero expression: **0**
- hidden masks outside measured support: **0**

Across four historical uniform 40% target-block views, about **82.1% of hidden measured target addresses were zero-valued**. Historical masking sampled measured addresses uniformly and the block-JEPA loss was unweighted MSE on block states. This motivates the current target-identity × target-zero decomposition; it does not by itself establish a current failure.

## Historical T1 gene-identity movement tracks measurement support

All seven checkpoint files u0/u10/u25/u50/u100/u200/u205 were independently verified against the checkpoint manifest. `tokenizer.gene_identity.weight` is 41,238 × 48.

Raw identity drift includes AdamW decay. A scalar decay component estimated from the 289 addresses measured by no source gives u205 ≈ 0.9997919 × u0. After subtracting that shrinkage:

- unsupported-address median residual drift: ~`3.5e-05`
- source-family count 1 median: ~`0.01687`
- source-family count 2 median: ~`0.01927`
- source-family count 3 median: ~`0.01593`
- NPH52+SEA_AD but no HVS, n=9,714: median ~`0.01929`
- SEA_AD-only, n=4,710: median ~`0.01940`
- strict all-42 common core, n=17,186: median ~`0.01593`

This is historical mechanism evidence for target-identity/support entanglement, not current V5 authority.

## Current V2 burden nuance

`TargetEvidenceBudgetAuthorityV2` deliberately masks a fraction of strict measured **addresses**, not realized nonzero genes. This is an anti-leakage rule: mask eligibility must not depend on the held-out cell's realized zero/nonzero state.

If the current effective-burden audit finds policy-specific differences in detected-token/UMI/entropy burden despite equal address cardinality, a successor must not simply equalize realized nonzero counts per held-out cell. Any repair must stay value-independent, for example using prospectively frozen TRAINING-ONLY address weights if scientifically justified.

## Current normalization-denominator mechanism confirmed in code

The authenticated materializers calculate `source_library` from full raw source counts **before** filtering/mapping to the 41,238-address ledger. RNA outside the modeled ledger, including unmapped/blocked features, can therefore influence every retained normalized value via `log1p(raw_count * 10000 / source_library)`.

Masking a target column removes the direct mapped target route but does not automatically remove this denominator route. The current F13 fixture proves already-materialized features do not recompute `source_library`; it does not prove that authentic biological target or excluded RNA contributed no information through the original denominator.

## Independent review corrections for early PR #33 results

### Audit D

The established blindness should be phrased narrowly. The within-donor-centred correlation is blind to **pure between-donor/source location or scale channels**. It can still detect source-specific within-donor feature→target relationships and cell-varying denominator channels. Avoid the broader statement that it cannot express any donor/source-level channel.

### Audit G

The cache uses deterministic hash-priority bottom-k selection **within each donor**. The observed marginal high-complexity shift is real, but causal attribution requires separating:

1. deliberate donor/source composition reweighting from the 1,024-per-donor cap;
2. residual within-donor selection imbalance.

Before calling the selector itself high-complexity-biased, compare cache vs full distribution within donor/source and compute the composition-only expected marginal.

## Quarantined local artifact

`66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` hashes to `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`, the historical provenance-mismatch family. It was not used as current authority or as a G4 fixture.

## Standing boundaries

`TERMINAL_MASKING_OUTCOMES = UNOPENED`

`D_SHARED = SEALED`

`PATHOLOGY / DEV / SEALED = SEALED`

`TRAINING_OFF`

Future agents must re-fetch live PR #33 before relying on its head. This document is prior/supporting evidence for the FULL104 information-channel red-team, not a replacement for the real 4.55M-cell audits.
