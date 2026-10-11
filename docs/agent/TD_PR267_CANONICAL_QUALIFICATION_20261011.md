# TD PR #267 canonical qualification contract

Date: 2026-10-11

Status: `QUALIFICATION_CONTRACT_ONLY__NO_VALUE_AUTHORITY__DO_NOT_RUN_G6_G7`

Candidate PR: #267

Exact candidate head:
`16f05bd3845565bb2c24d70143d447d7ef2b8904`

Successor branch:
`fix/td-g7-counterpart-auth-immutable-attempt-20261011`

Superseded parent head:
`a509c59238bcdc60b88fa265e7e4473760a41025`

## Purpose

Qualify the bounded G7 custody repair only. This qualification must not create a runtime value-read authorization, must not run G6 or G7, and must not open corrected expression/count arrays.

The repair changes only:
- `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`
- `tests/v5/test_td_g7_counterpart_attempt_custody.py`

Relative to the superseded parent, no G6/common/scientific-statistic file may differ.

## Required clean worktree

Pin exactly:
`16f05bd3845565bb2c24d70143d447d7ef2b8904`

Record:
- `git rev-parse HEAD`
- `git status --short`
- Python, numpy, pandas, scipy, h5py, pytest versions

HEAD must match exactly and the worktree must be clean.

## Required focused tests

Run:

```bash
python -m pytest -q \
  tests/v5/test_td_relational_value_read_v2_common.py \
  tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py \
  tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py \
  tests/v5/test_td_g7_counterpart_attempt_custody.py
```

Any failure = STOP. Do not patch and silently rerun in the qualification worktree.

The new custody regression file must prove, at minimum:
- physical-H5 authentication failure prevents any S174 count-loader invocation;
- G7 attempt marker binds authority trace + G6 receipt SHA;
- same-attempt retry is rejected;
- pre-existing final receipt is rejected;
- deterministic sidecar marker path.

## Exact PR #259 receipt compatibility — mandatory non-skipped test

Use the exact physical PR #259 receipt bytes from execution-record head:
`80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`

Driver receipt:
`results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split/PREFLIGHT_RESULT.json`

Required physical SHA-256:
`62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`

Mapping receipt:
`results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split/TD_RELATIONAL_MAPPING_PREFLIGHT.json`

Required physical SHA-256:
`6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`

Git-blob audit already confirmed these committed files preserve CRLF bytes. Do not regenerate, pretty-print, or normalize them.

Set the exact receipt paths required by:
`tests/v5/test_td_relational_pr259_real_receipt_compat.py`

Then run that file separately.

Canonical acceptance requires exactly:
`1 passed, 0 skipped, 0 failed`

A pytest exit code 0 with that test skipped is NOT qualification.

## Static scope verification

Compare:
- base `a509c59238bcdc60b88fa265e7e4473760a41025`
- candidate `16f05bd3845565bb2c24d70143d447d7ef2b8904`

Expected changed files only:
1. `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`
2. `tests/v5/test_td_g7_counterpart_attempt_custody.py`

Expected intent:
- authenticate physical H5AD before S174 count loader for overlap matrices;
- immutable `STARTED_NOT_A_PASS` G7 attempt marker created after exact runtime authority + same-authority G6 PASS but before value-bearing work;
- pre-existing marker or final receipt rejects retry;
- success leaves start marker intact;
- no scientific behavior changes.

## Qualification evidence to preserve

Open a draft qualification-record PR containing:
- exact candidate head;
- clean-worktree evidence;
- environment versions;
- full focused pytest log;
- exact PR259 receipt SHA verification;
- real-receipt compatibility test showing `1 passed / 0 skipped / 0 failed`;
- base-to-head changed-file comparison;
- confirmation no runtime value authorization object was created;
- confirmation G6/G7 were not executed;
- confirmation no corrected expression/count arrays were opened.

Then STOP for owner review.

## Explicitly forbidden during qualification

- no `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2` runtime authority;
- no owner-decision record construction;
- no G6 execution;
- no G7 execution;
- no corrected TD56/TD57B/TD57C/TD59/TD60 replay;
- no target selection;
- no training.

A future G6/G7 integrity authorization requires a separate explicit owner decision, preserved as an immutable owner-decision record and cryptographically bound by the runtime authorization.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
