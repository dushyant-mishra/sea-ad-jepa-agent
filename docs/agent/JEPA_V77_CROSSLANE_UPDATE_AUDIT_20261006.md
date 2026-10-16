# V77 cross-lane update audit — 2026-10-06

## Scope

This checkpoint audits the Claude/Macha local-GPU update supplied in chat against the shared qualification-interface and runtime-convergence work. It does not treat pasted local state as equivalent to pushed GitHub state.

## Exact repository state independently observed

- Remote branch: `claude/v77-synthetic-premise-custody-20261005`
- Latest pushed head independently observed during this audit: `8497916e5a9d9b232597ac1891b6c630d3b17931`
- That head contains the S146/S147 downstream executor to re-run component detect/reject on repaired worlds.
- The supplied transcript describes additional later local commits and background jobs after `8497916e...`; those later commits were not yet present on the remote when checked here and therefore remain transcript evidence until pushed and independently re-audited.

## Decision-changing findings from the Claude/Macha update

### S135/S146/S147 — measurement support and source/operator identity

The synthetic adapter initially could not know which zero entries were structurally unmeasured because the observer recorded only a per-cell support count, not per-element support. The later audit found two observer defects introduced in the canonical V2 path:

1. truth `source_index` order `(SEA_AD, NPH52, HVS)` was interpreted using a coverage table ordered `(HVS, NPH52, SEA_AD)`, swapping HVS and SEA-AD support for most cells;
2. operator attrition already expressed relative to registry coverage was applied again inside cohort coverage, double-counting missingness (especially severe for HVS).

The local lane reports repairs that write per-element support and refuse pre-repair worlds rather than guessing support downstream.

### S149 — pooled real topology calibration is study/cohort dominated

The supplied update reports a pathology-blind TRAIN-only diagnostic on the real 4,726-cell calibration cache. On the frozen 3,000-gene detection envelope, a null preserving cohort-specific detection rates but no within-cohort dependence reproduced approximately 89% of pooled correlation density/degree and exceeded pooled transitivity. Within individual study strata, dependence was much weaker.

The update further reports that, among cells from the 104 FULL104 production donors, detection-inferred coverage strata agreed 100% with the study identity implied by production operator records. This supports the interpretation that the effect is a real study/measurement-process signal rather than merely sequencing-depth stratification.

Important qualification: later within-cohort envelope and validation commits shown in the transcript were not yet independently observed on the remote at this audit point. The S149 diagnostic itself is nevertheless decision-changing enough that the previous pooled real detection envelope must not be treated as an uncontested biological calibration target.

## Consequences for the shared qualification interface

Two requirements were missing from the original shared-interface plan and are now mandatory before V77 adapter integration:

### 1. Observation/source/operator identity receipt

Feature identity alone is insufficient. The interface needs a mechanically proven observation-operator identity chain that binds at least:

`source/study identity -> source ordering -> operator identity -> operator-to-source mapping -> structural-support rule/version -> lawful operator-context representation`

A positional integer such as `source_index` is not sufficient authority. A same-shaped reordered source roster must fail.

### 2. Per-element measurement-support receipt

`measurement_mask_digest` alone is too weak if the mask was reconstructed or guessed by a downstream adapter. The batch must bind a producer-side support receipt proving the exact per-element measured/unmeasured support used to construct the model-visible batch.

For synthetic worlds, the receipt must bind the observer manifest/rule and the support-mask bytes or their canonical digest. A pre-repair world that lacks element-level support must fail closed rather than be inferred from counts, source coverage, or observed nonzeros.

For future real RNA, the analogous receipt must bind the lawful reader/operator support semantics rather than infer measurability from value alone.

### 3. Calibration/evaluation strata must stay separate from model features

S149 reinforces the already-frozen visibility rule. Study/cohort/operator identity is needed for split/evaluation/estimand auditing, but must not silently become an unrestricted encoder feature. The qualification batch must preserve grouping metadata for inference and diagnostics while the visibility firewall controls what enters the model.

### 4. Synthetic realism target is a scientific-contract decision

The runtime/interface lane must not unilaterally replace the pooled calibration envelope with a within-cohort target. The shared protocol must be able to express stratified calibration and cohort-aware synthetic worlds, but the exact real-data target/envelope belongs to the real-data scientific/reviewer lane and requires prospective freeze.

Previously seen dynamic-range arms cannot become confirmatory evidence against a newly chosen target. They are exploratory after unblinding/re-targeting.

## Consequences for PR #223 implementation

- Preserve the existing feature-identity REDs.
- Add REDs for source-order permutations and wrong operator-to-source mapping.
- Add REDs showing a batch cannot be constructed from a measurement-mask digest without producer-side support provenance.
- Add REDs refusing support reconstructed from observed nonzero values or a support-count scalar.
- Bind the support receipt into `QualificationBatchIdentityV1` and end-to-end provenance.
- Keep study/source identifiers non-model-visible unless a future scientific contract explicitly classifies a lawful operator descriptor as model-visible/operator-context.

## Consequences for V77 integration

The eventual V77 adapter should consume the repaired observer's per-element support directly and produce:

- authenticated synthetic feature identity;
- authenticated source/operator identity;
- authenticated per-element measurement-support receipt;
- value-independent hidden-target mask restricted to measured entries;
- ordinary `QualificationBatchV1` with no oracle fields;
- separate `SyntheticOracleTruthV1` downstream only.

Pre-repair canonical V2 worlds are forensic evidence, not valid adapter inputs, unless explicitly requalified under a successor support contract.

## Status / authority

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- no target/representation/estimand winner selected
- no pooled or within-cohort calibration envelope promoted by this audit
- V77 remains an instrument/pipeline-validation lane
- later local Claude/Macha commits must be pushed and independently audited before being treated as repository-qualified state

## Next actions

1. make PR #223 GREEN on its current richer shared-batch RED tests;
2. add RED-first operator/source identity and producer-side support receipts;
3. independently re-audit the V77 remote after Claude/Macha pushes the later S149/within-cohort/detect-reject commits;
4. route the S149 scientific implication to the real-data qualification/reviewer lane before freezing any replacement calibration target;
5. only then implement the V77 adapter against the shared interface.
