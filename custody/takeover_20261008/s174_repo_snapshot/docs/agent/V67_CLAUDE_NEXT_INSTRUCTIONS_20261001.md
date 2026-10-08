# V67 Claude next instructions — 2026-10-01

## First: refresh both branches

Audit the current heads before doing anything else.

Expected last-audited Claude head:
`f1dc9bd08057d88d33f27382ceb531b15e323ef9`

Expected ChatGPT tested head before V67 handoff publication:
`ffef012884a5953d552d8e5ee335ba0da656a199`

If either branch has advanced, inspect the delta first.

## Task A — repair S81 only

Read:

- `results/v64/V67_CLAUDE_F1DC_STAGE4_INDEPENDENT_AUDIT_V1.json`
- `docs/agent/V67_CLAUDE_STAGE4_S81_REPAIR_20261001.md`

Close the remaining artifact-level consumer-schema semantics gap.

Required checks include:

- exact T3 nnz;
- exact T4 nnz;
- aggregate binding recomputation;
- pair_gene resolution;
- pair_interval resolution;
- exact metacell ID range;
- all-eight-shard axis/dictionary agreement.

Use artifact-level negative tests.

Do **not** implement the executor in this task.

STOP after S81 repair for independent audit.

## Task B — independently audit ChatGPT post-red-team repairs

After Task A has stopped, audit ChatGPT's work since the prior Claude audit boundary `c965d77061424cdc6fad6192e091cb0809fbb737`.

Treat all new ChatGPT work as untrusted.

Focus on:

### F1 repair
`scripts/v64/heldout_source_observation_operator_synthetic_v1.py`

Verify that the held-out observation descriptor is really estimated from the technical calibration channel and that planted `TRUE_CAPTURE` is not leaked into the model path.

Verify the 35% misspecification negative test can genuinely fail.

### F2 repair
`scripts/v64/nested_modality_mask_uncertainty_anticollapse_synthetic_v1.py`

Verify RNA now carries nonzero private-state information and that the missing-vs-measured uncertainty gate is not forced by construction.

Verify the strong-RNA-private counterfactual turns the uncertainty gate RED.

### Evidence vs measurement
`scripts/v64/evidence_vs_measurement_response_synthetic_v1.py`

Try to falsify the distinction between:
- adding distinct biological evidence;
- improving measurement precision at fixed evidence identity.

Verify both negative-control relabelling tests are real.

### ChatGPT Stage-4 V5 custody
Audit:

- `results/v64/V66_STAGE4_EXECUTION_AUTHORITY_CONTRACT_V5.json`
- `scripts/v64/validate_stage4_execution_authority_v1.py`
- `tests/v64/test_stage4_execution_authority_validator_v1.py`

Check the cross-branch logic carefully. The intended invariant is:

`source_commit:path blob == stored blob == materialized worktree blob`

Do not replace this with a universal `HEAD:path` assumption because several accepted Phase-A/Phase-B authorities are intentionally sourced from Claude lineage.

Verify CI run `36866125611` really reports:
- V5 Git custody PASS for 10 repo authorities;
- 192 tests passed;
- all three V67 synthetic producers executed.

### Integration contracts
Audit:

- `results/v64/V67_TWO_LANE_INTEGRATION_RECOVERABILITY_CONTRACT_V1.json`
- `results/v64/V67_PRIVILEGED_TEACHER_STATE_CONSTRUCTION_CONTRACT_V1.json`

Try to find any route by which:
- privileged-only state becomes a student inference input;
- `Z_reg_private` enters the RNA student target;
- Stage-4 Delta/LCB/p-values become teacher coordinates;
- Phase-B audit substrate becomes a training tensor without a new producer;
- recoverability TEST can influence target/projection selection;
- synthetic thresholds can become production thresholds.

## Hard boundaries

Do not:

- implement Stage-4 executor during S81 repair;
- compute RNA×ATAC correspondence;
- open recoverability TEST;
- touch Morabito protected outcome;
- touch TD60;
- start real multimodal training;
- promote synthetic qualification to biology.

## Required output

Produce independent audit artifacts with exact head SHAs, reproducible evidence, retractions if needed, and a clear list of any remaining blockers.

Then STOP.
