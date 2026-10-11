# V79 exact-S174 structure replay, structural-support masked (V4): result and old-vs-masked audit

Date: 2026-10-11

Terminal: `MASK_CORRECTED_EXACT_S174_REPLAY_COMPLETE__V2_CORE_CONTROLLER_REVIEW_REQUIRED__QUALIFICATION_WORLDS_NOT_GENERATED__TRAINING_OFF`

This is development evidence only. Under PR #286 controller ruling 6113874774 it is the corrective replay. Nothing below decides whether V2_CORE stays frozen; the controller decides.

Not done: no qualification world, truth table, benchmark, NUTS fit or posterior export. `training_authorized=false`.

## What changed, and only that

The replay now runs every fit, held-out metric and residual permutation test over **structurally measured** entries only:
- A measured zero is a detection observation, y = 0.
- A structurally unmeasured entry is outside the likelihood.
- Support is resolved per operator (= Stage81A2R matrix) × gene, never collapsed to source.

Everything else is unchanged from V3:
- the G500 cache (`2f922c08…`);
- 200 replay and 50 support genes, with the same identity-blind, prevalence-balanced selection on the cache's frozen all-cell prevalence, so the same genes are compared;
- 3 donor folds, 99 permutations, seed 20261011;
- the models, metrics, operator λ grid {0.25, 1, 4} with primary λ = 1, the bootstrap convention, and the support logic.

## Support mask provenance

| item | value |
|---|---|
| authority | `results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz` @ `95d2cafe`, SHA-256 `ee5d12c1…cdaa` |
| join | cache operator → `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json` (`b83c35e6…`) matrix_id → measured_address(matrix, address) |
| rule | an entry is measured iff `measured_address` is True; a missing pair fails closed (it is never assumed measured); a flag/status contradiction fails closed |
| custody | 0 nonzero counts on unmeasured entries (the builder checks this and stops otherwise) |
| artifact | `V79_G500_STRUCTURAL_SUPPORT_V1.npz` `6203fb2c…`; mask hash `12ad275e…` |
| reproduction | identical to the development mask behind the masked planting calibration V2, so the calibration's join reproduces |

## Removed observations

| scope | entries | structurally unmeasured | fraction |
|---|---|---|---|
| whole G500 cache | 2,363,000 | 136,098 | 5.76% |
| 200 replay genes | 945,200 | 63,002 | 6.67% |
| 50 support genes | 236,300 | 12,608 | 5.34% |

- **Affected genes:** 28 of 200 replay genes and 5 of 50 support genes.
- **Measured observations per gene and source:** in `V79_S174_REPLAY_MASKING_AUDIT_V1.json` (`measured_observations_per_gene_and_source`).

**Undefined estimands.** These are reported, not dropped, and are evaluated under the same unchanged rule:
- **Detection source (C):** 6 genes are measured in one source only. Genes 441, 454, 456, 462 and 488 are HVS-only; gene 497 is SEA_AD-only. Their source increment is now exactly 0 by construction; in V3 it was +0.027 to +0.161, which was the artifact.
- **Positive source (C):** 9 genes have positives in one source only: those 6 plus 367, 444 and 491.

No held-out fold lacks measured cells, and no gene lost its positive held-out predictions.

## Old (V3) vs masked: A–H

The summary columns show the median per-gene gain [95% gene-bootstrap interval], the share of genes improved, and the mean gain. These are the same descriptive conventions as the committed V3 report, which the audit code reproduces exactly before it runs.

| question | V3 | masked | preserved? |
|---|---|---|---|
| A quadratic depth, detection | +0.00047 [+0.00026, +0.00067], 73%, mean +0.00127 | +0.00034 [+0.00017, +0.00053], 67%, mean +0.00105 | yes (positive) |
| A quadratic depth, positive | +0.0054 [+0.0037, +0.0087], 73% | identical | yes |
| B broad class, detection | +0.0025 [+0.0019, +0.0033], 84.5% | +0.0026 [+0.0017, +0.0036], 82% | yes |
| B broad class, positive | +0.0025 [+0.0018, +0.0035], 76% | identical | yes |
| **C source, detection** | +0.00148 [+0.00094, +0.00235], 78%, **mean +0.0226** | +0.00091 [+0.00053, +0.00129], 73.5%, **mean +0.0090** | yes (still positive; the main correction) |
| C source, positive | +0.00078 [+0.00022, +0.00155], 59% | identical | yes (weak) |
| D operator, detection (λ 0.25 / 1 / 4) | not material / not material / material; 1 failed fit at 0.25 → `PRIOR_SENSITIVE__UNRESOLVED` | not material / not material / material (λ=4 median +0.0016 [+0.0010, +0.0031], 69%); 0 failed fits → `PRIOR_SENSITIVE__UNRESOLVED` | yes |
| D operator, positive | material at no λ → `NOT_SUPPORTED` | identical | yes |
| E donor support (det / pos) | 32/50, 19/50 | 32/50, 19/50 | yes |
| F operator beyond donor (det / pos) | 37/50, 23/50 | 37/50, 23/50 | yes |
| G donor×class (det / pos) | 8/50 (mean excess −), 3/50 | identical | yes, stays OUT |
| H positive lognormal | 1,600 fits, 0 non-finite | identical | yes |

How the structural zeros distorted V3. The split is descriptive:
- **Clean genes:** the 172 clean replay genes are bit-identical in V3 and the masked replay.
- **C (detection source):** in the 28 affected genes the median gain fell from +0.088 (100% improved) to +0.00047 (68% improved). The structural zeros were being fitted as a large source effect.
- **A (quadratic depth):** in the same 28 genes the share improved fell from 96% to 54%. Structural zeros had also inflated the depth curvature.
- **Positive part:** identical to V3 in every per-gene fit and every positive permutation test. No nonzero count lies on an unmeasured entry, so masking cannot change the positive cells.
- **The V3 λ=0.25 failure** (gene 362, partially unmeasured inside NPH52) disappears: that fit now converges.

## Mechanical reading (for the controller; not a decision)

- **Preserved:** every A–H class used for the V2_CORE freeze is preserved under masking. Quadratic depth, broad class and source keep positive held-out-donor gains in detection. Source in the positive part stays weak. Operator stays unresolved in detection and not supported in positive. Donor stays supported. Donor×class stays out. Lognormal stays stable.
- **Reduced:** the detection source evidence is smaller but still clearly positive, and the V3 headline mean was mostly structural absence.

Options for the controller: keep V2_CORE frozen unchanged; reinterpret source; or reopen a component. No synthetic qualification world is generated before that review.

## Artifacts

In `results/v79/development/s174_structure_replay_v4_masked/`:

| file | contents |
|---|---|
| `V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED.json` | the masked replay, SHA-256 `caf2413c…` |
| `V79_S174_REPLAY_MASKING_AUDIT_V1.json` | the machine-readable old-vs-masked A–H audit, `6bd0bfc7…` |
| `V79_S174_REPLAY_PER_GENE_NESTED_DELTAS_V4_MASKED.json` | the masked per-gene deltas |
| `V79_G500_STRUCTURAL_SUPPORT_V1.npz` / `.json` | the support mask and its record |
| `RUN_PROVENANCE.json` | input and output hashes, commits, CI runs, environment, commands |
| RED / GREEN logs, stdout / stderr | local test and run logs |

Code:
- RED `89d3e397`.
- GREEN `ed6359e4`: CI run 38180383133, job 114591484334, **39 passed**.
- Comparison `d255092c`: CI run 38180830921, job 114592834291, **40 passed**.
- Local GREEN log: 33 passed.
- Runs: replay and support builder from a `git archive` snapshot of `ed6359e4`; comparison from `d255092c`. Python 3.9.7, NumPy 1.24.2, SciPy 1.10.1.
