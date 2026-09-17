# JEPA Scientific Blocker Execution

Date: 2026-09-17

Status: `V5_CANONICAL_MASKING_RUNTIME_FRAMEWORK_READY__STREAMING_FULL104_EXECUTOR_NEXT__NO_MASKING_AUTHORITY__TRAINING_OFF`

Working branch:

`impl/v5-remaining-rna-target-semantics-20260917`

Verified code anchor:

`ffbdcce060abb1c9c4463e0505d83b12c342c16e`

## Scientific semantic invariant

The foundation objective is **not** numerical reconstruction of a hidden gene.

Masking removes molecular evidence and asks whether the remaining RNA supports recovery of the underlying biological/cellular state, including the query-local biological state associated with the supplied masked address.

Accordingly:

- the address identifies which local biological state must be inferred;
- the hidden scalar expression value is not the JEPA target;
- ridge/correlation/nonlinear expression predictors are anti-shortcut diagnostics only;
- suppressing expression-proxy predictability does not by itself establish biological-state recovery;
- the masking policy must preserve a state-inference task.

## What changed in this closeout

The current masking/runtime framework has moved beyond the exploratory RIDGE8-only stage.

Implemented and CI-verified:

- canonical current authority roots/closure V2;
- preexecution V2, receipt V2, explicit training-authority schema, optimizer V3 and checkpoint V2;
- numeric masking qualification parameter authority with no production defaults;
- frozen masking qualification run-contract schema;
- masking qualification execution authority V2 bound to the run contract;
- canonical primary in-memory masking qualification reference runner;
- current closure rejection of legacy masking execution V1;
- Stage-A/current-source inventory updated to V2 successors;
- fail-closed no-skip CI for Stage-A and current remaining-RNA/semantic regression suites.

The verified code head passed all four current workflows.

## Current exploratory evidence state

September 17 discovery work still supports RIDGE8 as the strongest broad candidate tested so far under matched comparisons, with TOP8 as comparator and PREFIX3 as a sparse/selective arm. Nonlinear challenges remain supporting evidence.

This evidence is **not** a production masking decision and does not freeze cap 8, ridge alpha 0.01, any mask fraction, PREFIX3 thresholds, target counts or other exploratory values.

## Primary engineering blocker now

The authenticated production FULL104 expression substrate is sharded and larger than this environment can hold as one convenient matrix.

Historical full-reader recovery shows:

- 42 authenticated SciPy CSR counts shards plus per-row metadata;
- 4,553,407 reader-fit cells;
- 104 donors;
- 41,238 addresses;
- authenticated reader-fit membership/order through metadata SQLite;
- a later Level-4 materialization with 8,915 blocks.

The new `full104_masking_qualification_runner_v1.py` is the canonical **algorithmic reference** but expects already-bound sparse arrays. The next production component must therefore be a streaming/sufficient-statistics FULL104 executor that is parity-tested against this reference.

Do **not** make a monolithic 4,553,407 x 17,186 CSR a required production intermediate solely to fit the reference API.

## Immediate sequence

1. Design the streaming FULL104 adapter around the authenticated shard/Level-4 layout. Preserve row identity, donor/source mapping, support semantics and exact normalization authority.
2. Add controlled fixture parity tests against `full104_masking_qualification_runner_v1.py` for:
   - training-only partner screening;
   - TOP8/RIDGE8/PREFIX3 partner selection;
   - common-random base masks;
   - exact burden-preserving swaps;
   - ridge fit sufficient statistics;
   - donor-centered heldout prediction correlation squared;
   - source-balanced score aggregation;
   - deterministic replay.
3. Ensure the streaming executor produces the same target x outer-fold primary estimands as the canonical reference within a preregistered numerical tolerance on fixtures.
4. On a canonical Git worktree, build and validate `docs/agent/CURRENT_WORK_CHECKPOINT.json` with `scripts/agent/work_checkpoint.py`.
5. Prospectively instantiate/freeze the real masking qualification design, numeric parameter authority and run contract. Bind the exact SHA-256 of the execution source. Do this **before** terminal FULL104 outcomes are inspected.
6. Execute the address-universe ladder through terminal `FULL_COMMON_CORE_17186_V1` on the GPU/full-data machine.
7. Run all required positive/negative/replay/no-privileged-metadata controls and target-clustered precision. Report nonlinear challenge without retuning.
8. Issue the real `MaskingQualificationExecutionAuthorityV2` and bind the selected policy only if the frozen contract passes.
9. Continue remaining real-evidence closure: healthy-current-teacher remaining-RNA necessity, measurement robustness, production geometry and geometry-specific memorization, runtime provenance, and critical-test closure.
10. Issue final explicit training authority only after the actual current graph closes.

## Heavy-data references

Historical authenticated reader implementation source:

`planning/v5-full-population-cheat-proofing-20260909`

Key historical files:

- `scripts/v5_anticheat/build_full_reader_expression_identity_closure_v3.py`
- `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Historical corrected-cache root:

`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Current GPU/external-drive Level-4 root known from project history:

`D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical code is provenance/support, not automatically current authority. Port/review only the minimum needed functionality and bind current source hashes.

## Hard boundaries

- Training remains OFF.
- No pathology labels in foundation representation learning.
- DEV/SEALED RNA remain closed unless separately authorized.
- No D_shared outcome inspection while upstream masking/design choices remain open.
- Terminal FULL104 successor outcomes must not be inspected before the prospective current run contract is frozen.
- Hidden-gene numerical expression reconstruction must not be substituted for biological/query-local state.
- Historical T1 remains failure/adversarial evidence and cannot serve as healthy-teacher authority.
- Do not silently promote exploratory mask burden, cap 8, RIDGE8, PREFIX3, alpha 0.01 or other exploratory hyperparameters into authority.
- Legacy `MaskingQualificationExecutionAuthorityV1` is superseded for current closure.
- Skipped critical regression tests are failures, not passes.

## Governance note

`AGENTS.md` requires a validator-built `docs/agent/CURRENT_WORK_CHECKPOINT.json`. This GitHub-connector environment cannot truthfully generate and validate the machine/worktree-bound checkpoint because it does not own the canonical Git worktree. Do not fabricate a validator PASS.

The canonical-worktree/GPU lane must build and validate that checkpoint before authority-bearing promotion or expensive FULL104 execution.
