# TD relational G4/G5 canonical rerun — self-audit-hardened

Date: 2026-10-09

Status: `EXECUTION_RUNBOOK_FROZEN__VALUE_BLIND_G4_G5_ONLY__SELF_AUDIT_HARDENED`

Repair branch:
`fix/td-preflight-platform-stable-serialization-20261009`

**Canonical execution code freeze:**
`b3ff8366f28280e7d3269c305efa6317a05c8834`

Parent implementation:
`impl/td-relational-corrected-preflight-20261009@6716f044fcbefeb39bddf505c09a82378ce602e8`

Preserved prior failed execution:
PR #245 / `bf6ddda4e1b020fdb959812036b957c40166fede`

Prior terminal:
`FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_BEFORE_G4_G5__MANIFEST_FILE_SHA_MISMATCH__WINDOWS_CRLF_SERIALIZATION`

The #245 namespace and CRLF manifest are historical failure evidence. Never edit, normalize, delete, copy into the new run, or reuse that namespace.

Hard authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. What changed after self-audit

The original CRLF/freshness repair was necessary but not sufficient as a custody boundary. Self-audit found three additional weaknesses before any rerun was sent to the canonical machine:

1. the driver checked that the calibration and TD historical archives existed but did not itself enforce their frozen SHA-256 values;
2. the mapping audit checked source H5AD size but inherited their SHA values without re-hashing the physical bytes;
3. the driver's default output path still named the old `20261007/preflight_v1` namespace.

All three are repaired in the execution code freeze above.

The hardened driver now cryptographically binds, inside the run itself:

- Sample-A freeze;
- Stage81A2R provenance;
- Stage81A3R collision ledger;
- exact calibration bundle SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`;
- exact TD41-TD58 archive SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`;
- exact Macha S174 freeze;
- every one of the 35 HVS/SEA-AD source H5ADs by size **and SHA-256** against that freeze;
- the regenerated 9,216-address manifest physical bytes.

The mapping phase still opens only H5AD `var`/`obs` identity metadata after byte authentication. It does not open `raw/X` or `X` expression arrays.

## 2. Scope

Allowed:
- focused tests for the manifest/preflight/mapping code;
- exact byte authentication of the frozen authorities above;
- metadata/provenance manifest reconstruction;
- H5AD `obs`/`var` mapping audit;
- writing new value-blind receipts into the fresh namespace below.

Forbidden:
- reading expression arrays;
- G6 corrected-value materialization;
- G7 value/overlap execution;
- corrected TD56/TD57B/TD57C/TD59 biological replay;
- target promotion/ranking;
- creating any value-read authorization file/token.

## 3. Worktree / branch

Create a new clean execution worktree from exactly:

`b3ff8366f28280e7d3269c305efa6317a05c8834`

Recommended execution branch:

`exec/td-relational-g4g5-self-audit-hardened-20261009`

Before testing:

- `git status --short` must be empty;
- `git rev-parse HEAD` must equal the SHA above;
- local ref `claude/s174-train-cache-rebuild-20261007` must be available because the driver extracts the exact S174 freeze from it.

Do not execute from the earlier `1dbf37d5...` repair freeze. It predates the self-audit custody hardening.

## 4. Focused qualification tests

Run:

```text
python -m pytest -q \
  tests/v5/test_build_td_relational_replay_manifest.py \
  tests/v5/test_run_td_relational_replay_preflight.py \
  tests/v5/test_audit_td_relational_replay_mapping_preflight.py
```

Record exact:
- Python/numpy/pandas/h5py versions;
- command;
- passed/failed/skipped counts.

Any failure: preserve and STOP. Do not alter scientific inputs, expected hashes, collision policy, mapping policy, or manifest bytes to obtain a pass.

## 5. Fresh immutable namespace

Use exactly:

`results/target_discovery/td_relational_corrected_replay_20261009/preflight_v3_self_audit_hardened`

This is also the hardened driver's default output namespace.

Before execution it must not exist or must be completely empty. The driver refuses any non-empty namespace.

Do not use:
`results/target_discovery/td_relational_corrected_replay_20261007/preflight_v1`

Do not use the previously proposed `preflight_v2_post_crlf_repair` namespace for this authoritative rerun.

## 6. Canonical driver command

From the clean worktree root:

```text
python scripts/v5/run_td_relational_replay_preflight.py \
  --output-dir results/target_discovery/td_relational_corrected_replay_20261009/preflight_v3_self_audit_hardened
```

Canonical physical paths remain:

- `D:/Jepa project/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `D:/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`
- `D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`
- `D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`
- `D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz`
- the 35 HVS/SEA-AD H5AD paths frozen by S174.

Do not substitute the known unrelated larger same-named calibration bundle under `exports/`.

Because the mapping phase now re-hashes the 35 physical H5ADs itself, do not replace this with an informal/manual assertion. The PASS receipt must contain the code-enforced `all_35_h5_source_sha256_verified=true` check.

## 7. Required manifest evidence

Generated:
`JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv`

Must have:

- SHA-256 exactly `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
- zero CRLF byte pairs;
- builder terminal `PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST`;
- all builder validations true.

Do not normalize or rewrite the file after generation.

## 8. Required G4/G5 PASS evidence

Mapping terminal:
`PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`

Driver terminal:
`PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`

Mapping receipt schema must be:
`JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V2`

Driver receipt schema must be:
`JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V2`

Mapping checks must include true:

- `all_35_h5_source_sha256_verified`
- `source_files_exactly_hash_bound`
- `all_9216_addresses_one_to_one`
- `all_sample_A_h5_cell_rows_exact`
- `count_arrays_never_opened_by_design`

No PASS may be claimed if any one of these is false or absent.

## 9. Failure rule

Any failure is preserved exactly and stops the lane.

Do not:
- patch generated bytes;
- substitute genes/cells/files;
- weaken or update an expected hash after seeing a result;
- change collision/mapping policy;
- reuse a partially populated namespace;
- inspect expression values as a debugging shortcut;
- rerun into the same failed namespace.

Open a separate draft execution-record PR and report the actual terminal/error and the last completed gate.

## 10. PASS rule and hard stop

If and only if all required evidence above is present:

1. preserve the entire fresh namespace and exact execution/environment record;
2. open a draft execution-record PR bound to code freeze `b3ff8366f28280e7d3269c305efa6317a05c8834`;
3. **STOP**.

Do not execute G6 or G7.

PR #251 contains prospective hardening for a possible later G6/G7 decision, but it is not part of this run and creates no value-read authority. Its authorization design is separately audited and must be reviewed after this G4/G5 result before the owner decides anything about corrected values.

## 11. Bayesian lane

PR #249 is terminated:

`SAMPLER_NOT_ESTIMABLE`

`STOP_THIS_BAYESIAN_FORMULATION__DO_NOT_TUNE_TO_HISTORICAL_OUTCOMES`

Do not use this run to revive or feed that method spike.
