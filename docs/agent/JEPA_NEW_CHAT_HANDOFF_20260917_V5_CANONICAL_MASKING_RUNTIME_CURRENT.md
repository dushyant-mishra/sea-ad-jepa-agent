# JEPA V5 current handoff — streaming masking executor parity closed

Date: 2026-09-17

Status: `CURRENT_V5_STREAMING_MASKING_EXECUTOR_PARITY_READY__FULL104_GPU_QUALIFICATION_PENDING__TRAINING_OFF`

## Read this as a framework/evidence boundary, not training authority

The current V5 runtime/authority framework, canonical in-memory masking reference, and authenticated Level-4 streaming/sufficient-statistics masking executor are implemented and CI-verified.

The actual terminal FULL104 masking qualification has **not** been executed from this environment. No masking policy has been promoted to production authority. No final training authority has been issued. Training remains OFF.

The foundation objective remains biological/cellular state inference from partial RNA, including query-local state conditioned on a supplied canonical molecular address. Hidden-gene scalar reconstruction is forbidden as the JEPA objective. Ridge/correlation/nonlinear expression predictors are anti-shortcut diagnostics only.

## Verified implementation anchor

Working branch:

`impl/v5-remaining-rna-target-semantics-20260917`

Verified code head:

`8ee5d0a5be483e18819a6f6975efa183327b2158`

PR:

`#18` against `analysis/v5-ridge8-expanded-validation-20260917`

At this exact code head all four current workflows completed successfully:

- `V5 runtime closure` — run `35278901437` — SUCCESS
- `V5 FULL104 masking runner` — run `35278901430` — SUCCESS
- `V5 remaining-RNA and target-semantics successor` — run `35278901433` — SUCCESS
- `V5 Stage-A spillover firewall` — run `35278901569` — SUCCESS

The FULL104 runner workflow includes the canonical in-memory runner, the streaming parity suite, run-contract regressions, and a fail-closed no-skip check. Remaining-RNA and Stage-A also fail closed on skipped tests.

Governance commits after this code anchor are documentation-only unless explicitly stated otherwise.

## What is actually closed

Do not redo these items unless their inputs change.

### Frozen project authorities already closed

- FULL104 substrate lineage and identity: 4,553,407 cells, 104 donors, 42 operators, 41,238 addresses, 17,186 common-core addresses, 8,915 Level-4 blocks.
- FULL104 block-manifest SHA-256: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.
- primary representation: `VALUE_ONLY_256`; QC/visibility channels are observation/QC only and cannot silently re-enter the primary molecular path.
- support/estimability authority.
- donor-uniform / cell-uniform-within-donor base-training estimand.
- canonical address registry mechanics and current shared target-address provider schema.
- Stage-A structural qualification: 11 PASS / 0 FAIL / 0 UNPROVEN. Only the geometry-dependent memorization predicate remains conditional on final geometry.
- historical T0/T1/C2, QID/F1, Stage81A3 and Layer-2 audits.

### Current runtime/authority framework closed in this successor lane

The current runtime graph uses V2/V3 successors rather than silently accepting stale schemas:

- explicit current authority-root vocabulary V2;
- current authority closure V2;
- current trainer preexecution contract V2;
- current teacher-target receipt V2;
- explicit final training-authority schema;
- optimizer guard V3, which cannot arm from a receipt alone and requires the issued training-authority digest;
- atomic checkpoint guard V2 bound to training-authority digest and V2 roots;
- dynamic Stage-A/current-source spillover inventory with superseded schemas quarantined.

Current closure rejects legacy `MaskingQualificationExecutionAuthorityV1`.

The masking qualification chain is:

`design -> numeric parameter authority -> frozen run contract -> execution authority V2`

The numeric parameter authority and frozen run-contract authority are first-class current roots rather than hidden transitive implementation choices.

### Canonical primary masking qualification reference

Current source:

`src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py`

It implements the prospectively declared primary comparison on already-bound sparse arrays:

- common-random base masks;
- target always masked plus authorized non-target co-mask burden;
- exact burden-preserving swaps;
- fail-closed behavior if exact swaps cannot be completed;
- train-donor-only partner screening/fitting;
- uniform, TOP8 correlation, RIDGE8 conditional and PREFIX3 selective arms;
- the same ridge primary attacker and score across all policy arms;
- donor-centered target fitting and within-donor feature standardization;
- held-donor evaluation;
- primary score `SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1`;
- deterministic replay with policy ID absent from the base-mask seed.

The target-evidence budget is applied to **eligible non-target RNA** while the query target is masked in addition. Exploratory whole-universe burden arithmetic must not be inherited silently.

### Numeric masking settings are explicit authority inputs

Current schema:

`src/sea_ad_jepa/v5/masking_qualification_parameters_authority_v1.py`

It binds outcome-relevant settings including:

- targeted-partner cap;
- RIDGE candidate-pool size;
- RIDGE score feature count;
- exact rational ridge alpha;
- PREFIX3 candidate count, floor, reduction and inner split;
- primary attacker and score IDs.

There are **no production defaults**. Historical exploratory values such as cap 8, alpha 0.01, 15% masking, PREFIX3 thresholds or exploratory target counts are not authority merely because tests or discovery scripts used them.

## Streaming FULL104 execution adapter — now implemented and parity-verified

Current source:

`src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py`

Current regression suite:

`tests/test_v5_full104_masking_streaming_executor_v1.py`

Workflow:

`.github/workflows/v5-full104-masking-runner.yml`

This closes the engineering blocker previously described as “streaming FULL104 adapter with parity to canonical reference.”

### Physical layout supported

The adapter consumes the authenticated Phase-2 Level-4 block format:

- 8,915 sparse SciPy CSR `*.counts.npz` blocks across 42 operators;
- matching per-block row metadata CSV;
- raw nonnegative integer counts;
- per-row `source_library`;
- `selection_row` identity;
- donor/source metadata supplied by current binding inputs.

The Level-4 block-manifest schema is:

`block_key, source, operator_index, matrix_id, rows, nnz, counts_path, counts_sha256, meta_path, meta_sha256`

Each row metadata file uses:

`selection_row, canonical_cell_id, donor_id, expression_row, primary_row_weight, source_library`

Historical raw-reader scripts may still be useful provenance, but the current adapter is built around the authenticated Level-4 block layout rather than requiring a 42-shard raw-reader reconstruction.

### Exact normalization boundary

For requested expression columns, the adapter applies:

`log1p(raw_count * 10000 / source_library)`

exactly once.

It does not treat measured zero as missing; support eligibility remains a separate authority.

### No monolithic FULL104 x common-core matrix

The adapter does **not** require a 4,553,407 x 17,186 CSR.

It streams authenticated blocks and accumulates per-donor sufficient statistics needed for:

- source-balanced absolute-correlation screening;
- ridge Gram matrices and target cross-products;
- donor-standardized ridge fitting;
- held-donor prediction correlation squared;
- PREFIX3 inner-donor evaluation;
- exact primary target x outer-fold estimands.

This is an exact reference-compatible execution method, not a scientific shortcut.

### Parity and failure tests

At code anchor `8ee5d0a5...`, CI verifies:

- exact log1p10K normalization parity on controlled raw-count blocks;
- donor identity preservation;
- row-for-row output parity with `full104_masking_qualification_runner_v1.py` for all four primary policy arms on controlled fixtures;
- matching targeted partners, mask cardinalities, primary scores, uniform scores and deltas;
- exact burden-preserving swaps;
- counts-block hash corruption fails closed;
- duplicate `selection_row` within a block fails closed;
- the executor source does not construct a monolithic matrix through `vstack`;
- no training/protected-outcome switch is present.

A red-team pass also added the streaming executor to the current Stage-A source inventory, so this production path is not outside the spillover firewall.

### Scope of this closure

This proves implementation/reference parity and fail-closed mechanics.

It does **not** prove that the real 4.55M-cell terminal FULL104 qualification has executed or passed. It does not select RIDGE8 or any other masking arm.

## Supporting exploratory masking evidence — not production authority

September 17 discovery work remains supporting evidence:

- RIDGE8 was the strongest broad exploratory candidate among tested arms;
- outside-original-800 32-target challenge favored RIDGE8 over TOP8 under matched ridge attack;
- nonlinear challenges were directionally supportive;
- PREFIX3 was sparse/selective;
- STABLE15 was vacuous and STABLE10 ineffective for the tested threat model.

None of these freeze a production masking policy. They preceded the final prospective current run contract and terminal FULL104 execution.

## Exact remaining masking path

Do not invent another masking family before completing this path unless the frozen qualification itself exposes a real failure.

1. On the canonical GPU Git worktree, generate and validate `docs/agent/CURRENT_WORK_CHECKPOINT.json` with `scripts/agent/work_checkpoint.py`. This connector session cannot truthfully fabricate the machine/worktree-bound PASS.
2. Authenticate/bind the actual FULL104 Level-4 substrate at the known GPU/external-drive location. Do not substitute discovery, synthetic, DEV/SEALED, pathology, validation-oracle or smaller-cache data.
3. Instantiate the real target panel, split, universe ladder and other live artifacts required by the already-defined authorities.
4. Prospectively instantiate/freeze the masking design and numeric parameter authority.
5. Bind the exact canonical in-memory reference source in the design and the exact streaming executor source used for execution in the run contract. Freeze before terminal qualification outcomes are inspected.
6. Execute the qualification ladder through terminal `FULL_COMMON_CORE_17186_V1` with all required controls, target-clustered precision and nonlinear challenge reported without retuning.
7. Issue the actual `MaskingQualificationExecutionAuthorityV2`. PASS requires a fixed candidate policy; FAIL requires `NO_POLICY_QUALIFIED`.
8. Only then bind the selected current masking policy and continue the remaining real-evidence closure.

## Heavy FULL104 execution references

Known current GPU/external-drive Level-4 root:

`D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical corrected-cache root:

`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Historical provenance branch:

`planning/v5-full-population-cheat-proofing-20260909`

Historical helper scripts:

- `scripts/v5_anticheat/build_full_reader_expression_identity_closure_v3.py`
- `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Historical code is provenance/support, not automatic current authority.

## Other real-evidence closure still required before training

Schema/mechanics existence is not evidence that the real scientific gate passed. Before final training authority, current live artifacts must substantiate the applicable gates, including:

- terminal FULL104 masking qualification;
- selected masking policy from the frozen real execution;
- remaining-RNA necessity using a healthy current teacher, not historical failed T1 checkpoints;
- measurement robustness under current teacher/target semantics;
- production geometry selection and geometry-specific memorization qualification;
- exact current runtime-source/environment provenance;
- all critical-test execution with no silent skips;
- current V2 closure roots with fixtures/placeholders replaced by real authority artifacts.

Only after the actual graph closes may an explicit `CurrentTrainingAuthorityV1` be issued and consumed by optimizer V3/checkpoint V2.

## Performance note

The streaming adapter is an exact sufficient-statistics reference adapter. It may rescan authenticated blocks across targets/arms and has not yet been performance-qualified on the 4.55M-cell terminal run.

If terminal runtime is excessive, optimize I/O without changing the frozen scientific estimand—for example by adding an authenticated/memmap sufficient-statistics cache whose equivalence is tested against this reference. Do not change scientific parameters or inspect terminal outcomes to tune the algorithm.

## Hard boundaries

- `TRAINING_OFF`
- `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
- no pathology/DEV/SEALED outcome opening while upstream design remains open;
- no hidden-gene scalar reconstruction objective;
- no policy promotion from exploratory RIDGE8 evidence alone;
- no receipt-only optimizer unlock;
- no legacy masking-execution V1 in current closure;
- no silent skipped critical tests;
- no unauthenticated or smaller substitute for FULL104 heavy data;
- no monolithic FULL104 matrix is required for masking qualification.

## Recommended next work

The next implementation/execution lane is now on the canonical GPU worktree, not another redesign in this connector environment:

`CURRENT_WORK_CHECKPOINT -> authenticated Level-4 binding -> prospective design/parameters/run-contract freeze -> terminal FULL104 qualification`

Do not spend another cycle re-auditing settled T0/T1/QID/F1/Layer-2/Stage-A or streaming-reference parity history unless an input changed.
