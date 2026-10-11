# PR #263 canonical qualification contract

Date: 2026-10-10

Status: `QUALIFICATION_ONLY__NO_VALUE_AUTHORITY__DO_NOT_EXECUTE_G6_G7`

Candidate code freeze:
`a509c59238bcdc60b88fa265e7e4473760a41025`

Upstream accepted G4/G5 evidence:
- PR #259 execution-record head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- driver receipt physical SHA-256 `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping receipt physical SHA-256 `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`

## Important skip hazard

`tests/v5/test_td_relational_pr259_real_receipt_compat.py` intentionally skips when either of these environment variables is absent:

- `TD_PR259_PREFLIGHT_RESULT`
- `TD_PR259_MAPPING_RECEIPT`

Therefore a generic pytest exit code 0 is **not sufficient** for canonical qualification. A run in which this exact-real-receipt test is skipped is **NOT QUALIFIED**.

## Required canonical-machine sequence

1. Create a clean worktree pinned exactly to candidate code freeze `a509c59238bcdc60b88fa265e7e4473760a41025`.
2. Extract the two exact physical PR #259 receipt files from execution-record commit `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947` without newline or JSON normalization.
3. Verify their physical SHA-256 values exactly match the two values above.
4. Set `TD_PR259_PREFLIGHT_RESULT` and `TD_PR259_MAPPING_RECEIPT` to those exact files.
5. Run the exact-real-receipt test alone first:

```text
python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py
```

Required result:
- exactly `1 passed`;
- exactly `0 skipped`;
- exactly `0 failed`.

Anything else = STOP / NOT QUALIFIED.

6. Then run the complete focused suite:

```text
python -m pytest -q \
  tests/v5/test_td_relational_value_read_v2_common.py \
  tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py \
  tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py \
  tests/v5/test_td_relational_pr259_real_receipt_compat.py
```

For the focused suite, the exact-real-receipt test must again be counted as passed, not skipped.

7. Preserve:
- exact `git rev-parse HEAD`;
- clean `git status --short`;
- Python/package environment;
- physical receipt SHA output;
- standalone real-receipt-test output;
- full focused-suite output;
- pass/fail/skip counts.

8. STOP and return evidence.

## Forbidden during qualification

Do not:
- create `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2`;
- invoke G6;
- invoke G7;
- open expression/count arrays;
- modify candidate production code;
- normalize/rewrite the PR #259 receipt JSON;
- treat a skipped real-receipt test as PASS.

## Interpretation

A qualification PASS means only that the hardened standalone future value-path code correctly accepts the exact audited PR #259 evidence and its focused fail-closed tests pass on the canonical machine.

It does not authorize value reading, corrected biological replay, target selection, TD60 or training.

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
