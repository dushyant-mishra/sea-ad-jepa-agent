# Macha — next instruction: repair and qualify PR #268 atomic G7 attempt custody

Current assignment: `REPAIR_PR268_ATOMIC_ATTEMPT_CUSTODY__QUALIFY_SUCCESSOR__THEN_STOP_AT_VALUE_AUTHORITY_BOUNDARY`

Use only:
- PR #268
- branch `fix/td-g7-atomic-attempt-create-20261011`
- exact starting RED head `d8fa3024e06e265b77353c8382453e7ccbf2350f`

PR #267 head `16f05bd3845565bb2c24d70143d447d7ef2b8904` is now blocked and must not be qualified or executed. Controlling audit:
`docs/agent/TD_PR267_CONCURRENT_ATTEMPT_CUSTODY_AUDIT_20261011.md`

## 1. Confirm RED starting state

Create a fresh clean worktree at exact head:
`d8fa3024e06e265b77353c8382453e7ccbf2350f`

Record:
- `git rev-parse HEAD`
- `git status --short`
- Python/numpy/pandas/scipy/h5py/pytest versions

Run only:

```bash
python -m pytest -q tests/v5/test_td_g7_counterpart_attempt_custody.py::test_g7_attempt_concurrent_start_has_exactly_one_winner
```

The starting head is expected to FAIL because PR #267 permits two concurrent successful starters. Preserve the exact RED output. If it unexpectedly passes, STOP and report the discrepancy before editing production code.

## 2. Minimal bounded repair

Modify only:
`scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`

Required behavior:
- G7 marker creation must be an atomic exclusive create;
- exactly one concurrent starter may create the marker;
- a loser encountering an already-created marker must raise the existing `already spent` RuntimeError semantics;
- do not delete the marker on failure or success;
- preserve final-receipt rejection;
- preserve marker schema/content and existing false authority flags.

Use the smallest platform-appropriate exclusive-create primitive, e.g. Python file mode `x` / O_EXCL semantics. Do not add locking services, retry loops, new namespaces, or scientific changes.

Do not modify G6/common/scientific-statistic behavior.

## 3. GREEN regression

After the production patch, run:

```bash
python -m pytest -q tests/v5/test_td_g7_counterpart_attempt_custody.py
```

Require all tests in that file PASS, including exactly-one-winner concurrency behavior.

Then run the focused successor suite:

```bash
python -m pytest -q \
  tests/v5/test_td_relational_value_read_v2_common.py \
  tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py \
  tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py \
  tests/v5/test_td_g7_counterpart_attempt_custody.py
```

Any failure = preserve evidence and STOP. Do not weaken a test or silently rerun after unrelated patching.

## 4. Exact PR #259 physical receipt compatibility

Use exact execution-record head:
`80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`

Driver physical SHA-256:
`62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`

Mapping physical SHA-256:
`6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`

Do not regenerate or normalize either CRLF receipt.

Run separately:

```bash
python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs
```

Canonical acceptance requires exactly:
`1 passed / 0 skipped / 0 failed`.

## 5. Static scope

Compare PR #267 exact head:
`16f05bd3845565bb2c24d70143d447d7ef2b8904`

to the final PR #268 repair head.

Only these files may differ:
1. `tests/v5/test_td_g7_counterpart_attempt_custody.py`
2. `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`

No G6/common/scientific-statistic file may differ.

## 6. Preserve evidence

On PR #268 preserve:
- starting RED head and exact RED log;
- final repair head;
- clean worktree/environment evidence;
- exact code diff;
- focused GREEN logs;
- exact PR259 SHA checks;
- real-receipt result exactly `1 passed / 0 skipped / 0 failed`;
- base-to-head scope comparison;
- confirmation no runtime value authorization was created;
- confirmation G6/G7 were not executed;
- confirmation no corrected expression/count arrays were opened.

## 7. Forbidden

Do NOT:
- create `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2`;
- create an owner-decision record;
- execute G6;
- execute G7;
- open corrected expression/count arrays through this path;
- run corrected TD56/TD57B/TD57C/TD59/TD60;
- select a target or representation winner;
- authorize Stage 4;
- train.

If repair + qualification pass, report the final exact PR #268 head and evidence, then STOP at the value-read authority boundary. Engineering progression does not require a routine owner checkpoint; value reading still requires a separate explicit owner authorization.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
