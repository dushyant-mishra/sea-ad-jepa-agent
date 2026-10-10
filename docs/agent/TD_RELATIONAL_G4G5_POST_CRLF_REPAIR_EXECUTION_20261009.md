# TD relational G4/G5 canonical rerun after platform-stable serialization repair

Date: 2026-10-09

Status: `EXECUTION_RUNBOOK_FROZEN__VALUE_BLIND_G4_G5_ONLY`

Repair branch:
`fix/td-preflight-platform-stable-serialization-20261009`

Repair head at runbook freeze:
`1dbf37d5c9a4684e4bac73b9a86fb3875782e23e`

Parent implementation:
`impl/td-relational-corrected-preflight-20261009@6716f044fcbefeb39bddf505c09a82378ce602e8`

Preserved prior failed execution:
PR #245 / `bf6ddda4e1b020fdb959812036b957c40166fede`

Prior terminal:
`FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_BEFORE_G4_G5__MANIFEST_FILE_SHA_MISMATCH__WINDOWS_CRLF_SERIALIZATION`

The #245 output namespace and its CRLF manifest are historical failure evidence. They must not be edited, normalized, deleted, or reused.

Hard authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Scope

This runbook authorizes no new scientific scope. It defines only how to qualify the narrow #248 engineering repair and rerun the already-authorized value-blind G1-G5 preflight on the canonical Windows machine.

Allowed:
- focused tests for G1-G5/preflight code;
- metadata/provenance manifest reconstruction;
- H5AD `obs`/`var` mapping audit as already defined by G4/G5;
- writing new value-blind receipts into the fresh namespace below.

Forbidden:
- reading expression arrays;
- G6 corrected-value materialization;
- G7 value/overlap execution;
- corrected TD56/TD57B/TD57C/TD59 replay;
- target promotion/ranking;
- creating a G6/G7 authorization token.

## 2. Worktree / branch

Create a new clean execution worktree from the exact repair head, not from PR #245 and not from a moving branch tip.

Recommended execution branch:

`exec/td-relational-g4g5-post-crlf-repair-20261009`

It must start exactly at:

`1dbf37d5c9a4684e4bac73b9a86fb3875782e23e`

Before tests/run record:

- `git status --short` is empty;
- `git rev-parse HEAD` equals the SHA above;
- local ref `claude/s174-train-cache-rebuild-20261007` is available because the driver extracts the frozen S174 freeze from it.

## 3. Focused qualification tests

Run with the same canonical Python environment used for the prior attempt unless a documented environment repair is separately required:

```text
python -m pytest -q \
  tests/v5/test_build_td_relational_replay_manifest.py \
  tests/v5/test_run_td_relational_replay_preflight.py \
  tests/v5/test_audit_td_relational_replay_mapping_preflight.py
```

Record the exact Python/numpy/pandas/h5py versions and exact test terminal.

Any failure: preserve output and STOP. Do not modify scientific inputs, hashes, collision policy, mapping policy, or expected manifest bytes to make tests pass.

## 4. Fresh/superseding namespace

Use exactly this new repository-relative output namespace:

`results/target_discovery/td_relational_corrected_replay_20261009/preflight_v2_post_crlf_repair`

Before execution:

- the directory must not exist or must be completely empty;
- no file from PR #245 may be copied into it;
- do not point `--output-dir` at `...corrected_replay_20261007/preflight_v1`.

The repaired driver will fail closed if any artifact already exists in the chosen namespace.

## 5. Canonical driver command

From the clean execution worktree root on the canonical Windows machine:

```text
python scripts/v5/run_td_relational_replay_preflight.py --output-dir results/target_discovery/td_relational_corrected_replay_20261009/preflight_v2_post_crlf_repair
```

Do not edit generated files between producer and driver checks.

The canonical physical input paths remain the driver defaults already authenticated by PR #245:

- `D:/Jepa project/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `D:/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`
- `D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`
- `D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`
- `D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz`
- raw HVS/SEA-AD H5ADs under the already-bound S174 source paths.

Do not substitute the known 1.09-GB non-authority calibration bundle under `exports/`.

## 6. Required serialization evidence

The generated file:

`JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv`

must satisfy all of:

- SHA-256 exactly `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
- zero `CRLF` byte pairs;
- builder receipt terminal `PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST`;
- builder validations all true.

This is a qualification of the producer repair. Do not normalize or rewrite the file after generation.

## 7. G4/G5 success condition

The mapping audit must actually run this time.

Required mapping terminal:

`PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`

Required driver terminal:

`PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`

No PASS may be claimed if the driver stops before the mapping audit, if any authority digest changes, or if any expression array is opened.

## 8. Failure rule

Any failure is preserved exactly and stops the lane.

Do not:
- patch generated bytes;
- substitute genes/cells;
- weaken a hash;
- change collision/mapping policy;
- reuse a partially populated namespace;
- inspect expression values as a debugging shortcut.

Open a draft execution-record PR and report the actual terminal.

## 9. PASS rule and hard stop

If and only if both G4/G5 terminals PASS:

1. preserve and commit the new namespace receipts/artifacts on the execution-record branch;
2. open a draft execution-record PR against PR #248's repair branch (or otherwise clearly bind the exact repair commit); and
3. **STOP**.

Do not execute G6/G7.

A separate owner decision is still required for the later exact value-read token:

`AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_ONLY`

This runbook does not create or imply that authorization.

## 10. Bayesian lane

The Oct-9 Bayesian formulation on PR #249 is terminated after failed preregistered synthetic calibration:

`SAMPLER_NOT_ESTIMABLE`

`STOP_THIS_BAYESIAN_FORMULATION__DO_NOT_TUNE_TO_HISTORICAL_OUTCOMES`

Do not use this G4/G5 rerun to revive or feed that failed Bayesian method spike.
