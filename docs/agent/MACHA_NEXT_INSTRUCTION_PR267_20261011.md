# Macha — next instruction: qualify PR #267 only

Use only this branch:
`fix/td-g7-counterpart-auth-immutable-attempt-20261011`

Exact required head:
`16f05bd3845565bb2c24d70143d447d7ef2b8904`

Do not use or qualify PR #263 or any earlier G6/G7 candidate.

## 1. Fresh worktree

Create a fresh clean worktree pinned to the exact head above.

Record:
```text
git rev-parse HEAD
git status --short
```

HEAD must equal:
`16f05bd3845565bb2c24d70143d447d7ef2b8904`

`git status --short` must be empty.

Do not edit production code in this worktree.

Record exact environment versions:
- Python
- numpy
- pandas
- scipy
- h5py
- pytest

## 2. Run the focused qualification suite

Run exactly:

```bash
python -m pytest -q \
  tests/v5/test_td_relational_value_read_v2_common.py \
  tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py \
  tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py \
  tests/v5/test_td_g7_counterpart_attempt_custody.py
```

Any failure = STOP.

Do not patch and silently rerun in the qualification worktree.

Preserve the complete log.

## 3. Verify exact PR #259 receipt bytes

Use the exact committed PR #259 execution-record bytes from head:
`80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`

Driver receipt:
`results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split/PREFLIGHT_RESULT.json`

Required physical SHA-256:
`62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`

Mapping receipt:
`results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split/TD_RELATIONAL_MAPPING_PREFLIGHT.json`

Required physical SHA-256:
`6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`

Do not regenerate, reserialize, pretty-print or normalize either JSON file. Their exact CRLF-containing physical bytes are part of the authority evidence.

## 4. Run the real-receipt compatibility test separately

Point the environment variables required by:
`tests/v5/test_td_relational_pr259_real_receipt_compat.py`

to those two exact physical files.

Then run:

```bash
python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs
```

Qualification requires exactly:
`1 passed / 0 skipped / 0 failed`

Pytest exit 0 with the test skipped does NOT count.

## 5. Verify candidate scope

Compare:
- base: `a509c59238bcdc60b88fa265e7e4473760a41025`
- candidate: `16f05bd3845565bb2c24d70143d447d7ef2b8904`

Only these two files may differ:
1. `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`
2. `tests/v5/test_td_g7_counterpart_attempt_custody.py`

Confirm no G6/common/scientific-statistic file differs.

## 6. Explicitly forbidden

Do NOT:
- create `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2`;
- create an owner-decision record;
- run G6;
- run G7;
- open corrected expression/count arrays;
- run corrected TD56, TD57B, TD57C, TD59 or TD60;
- select a target;
- train anything.

This is qualification only.

## 7. Preserve qualification evidence

Open a new draft evidence-only qualification PR containing:
- exact candidate head;
- clean-worktree evidence;
- exact environment versions;
- complete focused pytest log;
- exact PR #259 driver/mapping physical SHA checks;
- separate real-receipt compatibility test showing exactly `1 passed / 0 skipped / 0 failed`;
- base-to-head changed-file comparison;
- confirmation no production code was edited;
- confirmation no runtime authorization object was created;
- confirmation G6/G7 were not executed;
- confirmation no corrected expression/count array was opened.

If anything fails, preserve the failure exactly and STOP.

If everything passes, preserve the evidence and STOP.

Do not proceed to G6/G7.

## Interpretation of a PASS

A qualification PASS means only:
> the hardened future target-discovery value-reading machinery correctly recognizes the accepted PR #259 evidence and satisfies its current engineering/custody qualification.

It does not authorize value reading.

After the evidence-only qualification PR is opened, return its PR number, exact head, test counts, hashes and confirmation of all forbidden actions remaining false.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
