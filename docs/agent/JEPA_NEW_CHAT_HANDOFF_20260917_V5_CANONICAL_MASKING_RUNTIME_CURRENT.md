# JEPA V5 current handoff — canonical masking/runtime framework

Date: 2026-09-17

Status: `CURRENT_V5_CANONICAL_MASKING_RUNTIME_FRAMEWORK_READY__FULL104_QUALIFICATION_PENDING__TRAINING_OFF`

## Read this as a framework/evidence boundary, not as training authority

The current V5 runtime/authority framework is structurally implemented and CI-verified. The actual terminal FULL104 masking qualification has **not** been executed from this environment, no masking policy has been promoted to production authority, and training remains OFF.

The foundation objective remains biological/cellular state inference from partial RNA, including query-local state conditioned on a supplied canonical molecular address. Hidden-gene scalar reconstruction is forbidden as the JEPA objective. Ridge/correlation/nonlinear expression predictors are anti-shortcut diagnostics only.

## Verified implementation anchor

Working branch:

`impl/v5-remaining-rna-target-semantics-20260917`

Verified code head:

`ffbdcce060abb1c9c4463e0505d83b12c342c16e`

PR:

`#18` against `analysis/v5-ridge8-expanded-validation-20260917`

At the exact verified code head all four current workflows completed successfully:

- `V5 runtime closure` — run `35275746415` — SUCCESS
- `V5 FULL104 masking runner` — run `35275746392` — SUCCESS
- `V5 remaining-RNA and target-semantics successor` — run `35275746434` — SUCCESS
- `V5 Stage-A spillover firewall` — run `35275746427` — SUCCESS

The remaining-RNA and Stage-A workflows now fail closed on skipped regression tests. Stage-A was specifically tightened after a hidden NumPy/SciPy import skip was discovered for the newly-current canonical runner.

Governance commits after this code anchor are documentation-only unless explicitly stated otherwise.

## What is actually closed

Do not redo these items unless their inputs change.

### Frozen project authorities already closed before this handoff

- FULL104 substrate lineage and identity: 4,553,407 cells, 104 donors, 42 operators, 41,238 addresses, 17,186 common-core addresses, 8,915 Level-4 blocks.
- FULL104 block-manifest SHA-256: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.
- primary representation: `VALUE_ONLY_256`; QC/visibility channels are observation/QC only and cannot silently re-enter the primary molecular path.
- support/estimability authority.
- donor-uniform / cell-uniform-within-donor base-training estimand.
- canonical address registry mechanics and current shared target-address provider schema.
- Stage-A structural qualification: 11 PASS / 0 FAIL / 0 UNPROVEN. Only the geometry-dependent memorization predicate remains conditional on final geometry.
- historical T0/T1/C2, QID/F1, Stage81A3 and Layer-2 audits. Do not reopen them as current blockers.

### Current runtime/authority framework closed in this successor lane

The current runtime graph now has V2/V3 successors instead of silently accepting stale schemas:

- explicit current authority-root vocabulary V2;
- current authority closure V2;
- current trainer preexecution contract V2;
- current teacher-target receipt V2;
- explicit final training-authority schema;
- optimizer guard V3, which cannot arm from a receipt alone and requires the issued training-authority digest;
- atomic checkpoint guard V2 bound to the training-authority digest and V2 roots;
- dynamic Stage-A/current-source spillover inventory with superseded schemas quarantined.

The current authority closure now rejects legacy `MaskingQualificationExecutionAuthorityV1`. The masking qualification chain is explicitly:

`design -> numeric parameter authority -> frozen run contract -> execution authority V2`

The numeric parameter authority and frozen run-contract authority are first-class current roots rather than being hidden transitively inside an execution digest.

### Canonical primary masking qualification algorithm implemented

Current source:

`src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py`

It is a data-path-agnostic reference implementation. It accepts already-bound sparse arrays and authority objects and implements the prospectively declared primary comparison:

- common-random base masks;
- exact target masking plus authorized non-target co-mask burden;
- exact burden-preserving swaps;
- fail-closed behavior if swaps cannot be completed without changing burden;
- train-donor-only partner screening/fitting;
- TOP8 correlation, RIDGE8 conditional and PREFIX3 selective policy arms plus uniform baseline;
- the **same ridge primary attacker and score across policy arms**;
- within-donor feature standardization and donor-centered target fitting;
- held-donor evaluation;
- primary score `SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1`;
- deterministic replay with policy ID absent from the base-mask seed.

A key correction from exploratory code is enforced: the target-evidence budget is applied to **eligible non-target RNA**, while the query target is masked in addition. Exploratory whole-universe burden arithmetic must not be inherited silently.

### Numeric masking settings are no longer implementation defaults

Current schema:

`src/sea_ad_jepa/v5/masking_qualification_parameters_authority_v1.py`

It explicitly binds outcome-relevant settings such as:

- targeted-partner cap;
- RIDGE candidate-pool size;
- RIDGE score feature count;
- exact rational ridge alpha;
- PREFIX3 candidate count, floor, reduction and three-way inner split;
- primary attacker and score IDs.

There are **no production defaults**. Historical exploratory values such as cap 8, alpha 0.01, 15% masking, PREFIX3 thresholds, or the exploratory target counts are not authority merely because tests instantiate them.

## Supporting exploratory masking evidence — not production authority

The September 17 discovery work remains useful supporting evidence:

- RIDGE8 was the strongest broad exploratory candidate among the tested arms;
- the outside-original-800 32-target challenge favored RIDGE8 over TOP8 under the matched ridge attacker;
- nonlinear challenges were directionally supportive;
- PREFIX3 was sparse/selective;
- STABLE15 was vacuous and STABLE10 ineffective for the tested threat model.

None of those results freeze a production masking policy. They were obtained before the final prospective current run contract and before terminal FULL104 execution.

## Exact remaining masking path

The next agent must not invent another masking family before completing this path.

1. On a canonical Git worktree, generate/validate `docs/agent/CURRENT_WORK_CHECKPOINT.json` with `scripts/agent/work_checkpoint.py`. This GitHub-connector session cannot truthfully fabricate that machine/worktree-bound PASS.
2. Recover the authenticated FULL104 reader-fit physical substrate and verify it before use. Do not substitute discovery, synthetic, validation/oracle, DEV/SEALED or pathology data.
3. Instantiate and prospectively freeze the actual masking design, numeric parameter authority and run contract, including the exact SHA-256 of the runner/executor source used for execution.
4. Implement/review the **streaming FULL104 execution adapter** described below. Do not materialize an unnecessary 4,553,407 x 17,186 monolithic CSR merely to satisfy the in-memory reference API.
5. Execute the qualification ladder with terminal `FULL_COMMON_CORE_17186_V1`, all required controls, target-clustered precision, and nonlinear challenge reported without retuning.
6. Issue `MaskingQualificationExecutionAuthorityV2` from the actual result artifact. PASS requires a fixed candidate policy; FAIL requires `NO_POLICY_QUALIFIED`.
7. Only then bind the selected current masking policy and continue through remaining real-evidence closure. Do not issue final training authority from test fixtures or schema existence.

## Heavy FULL104 execution boundary discovered in this closeout

The historical authenticated physical reader proves that production expression is sharded, not a single matrix.

Historical recovery source:

`planning/v5-full-population-cheat-proofing-20260909`

Useful historical scripts include:

- `scripts/v5_anticheat/build_full_reader_expression_identity_closure_v3.py`
- `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

The recovered physical format is 42 authenticated SciPy CSR `*.counts.npz` shards plus `*.meta.npz` row metadata. Reader-fit membership/order is supplied by the authenticated metadata SQLite. The full-reader identity closure expects 4,553,407 reader-fit rows, 104 donors and 41,238 addresses.

The historical heavy-asset ledger records the old corrected-cache root as:

`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

and the newer FULL104 Level-4 materialization is available on the user's GPU/external-drive machine at:

`D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

### Important implementation conclusion

`full104_masking_qualification_runner_v1.py` is the canonical **algorithmic reference**, not yet a complete heavy-substrate executor. A production terminal run needs a streaming/sufficient-statistics adapter over the authenticated shards/Level-4 blocks so that donor-level correlations, ridge sufficient statistics and held-donor scores can be computed without loading a >30 GB monolithic matrix.

Do not claim `FULL104_EXECUTION_READY` until that adapter is implemented, tested against small fixtures for parity with the reference runner, and bound into the prospective run contract.

This is the main new engineering blocker exposed by the final heavy-path audit. It is preferable to discovering an out-of-memory/noncanonical materialization failure after freezing the contract.

## Other real-evidence closure still required before training

Schema/mechanics existence is not evidence that the real scientific gate has passed. Before final training authority, current live artifacts must substantiate the applicable gates, including:

- masking qualification execution on the terminal FULL104 universe;
- remaining-RNA necessity using a healthy current teacher, not historical failed T1 checkpoints;
- measurement robustness under the current teacher/target semantics;
- production geometry selection and geometry-specific memorization qualification;
- exact current runtime-source/environment provenance;
- all critical-test execution with no silent skips;
- any other current V2 closure roots with placeholders/test fixtures replaced by real authority artifacts.

Only after the actual current graph closes may an explicit `CurrentTrainingAuthorityV1` be issued and consumed by optimizer V3/checkpoint V2.

## Hard boundaries

- `TRAINING_OFF`
- `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
- no pathology/DEV/SEALED outcome opening while upstream design remains open;
- no hidden-gene scalar reconstruction objective;
- no policy promotion from exploratory RIDGE8 evidence alone;
- no receipt-only optimizer unlock;
- no legacy masking-execution V1 in current closure;
- no silent skipped critical tests;
- no unauthenticated or smaller substitute for FULL104 heavy data.

## Recommended next work

The immediate next implementation is the streaming FULL104 qualification adapter, but treat it as a bounded new subsystem with explicit parity tests against `full104_masking_qualification_runner_v1.py`. After that, build the canonical work checkpoint, freeze the prospective authorities and hand execution to the GPU/full-data machine.

Do not spend another cycle re-auditing already-settled T0/T1/QID/F1/Layer-2/Stage-A history unless an input changed.
