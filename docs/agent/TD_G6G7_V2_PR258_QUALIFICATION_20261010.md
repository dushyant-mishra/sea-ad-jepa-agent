# PR #258 qualification (standalone G6/G7 V2 against the V3 preflight), 2026-10-10: STOPPED at the focused tests

Terminal (assigned in this record): `STOP_PR258_QUALIFICATION__FOCUSED_TEST_FAILURE__G7_G6_GATE_MESSAGE_ASSERTION`

Hard authority unchanged:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

**Do not merge.** This is a qualification record. It changes no production code, test, hash or input.

## 1. Bottom line

- One focused test failed: **29 passed, 1 failed, 0 skipped**. Per the instruction ("Any failure = STOP. Do not patch and rerun silently"), qualification stopped at step 2.
- Steps 3-5 were **not** run: no extraction of the PR #259 receipts, no `load_bound_preflight()` call, no compatibility result. A compatibility script was prepared beforehand and is attached for review, labelled `NOT_EXECUTED_...`; it was not run.
- The failing test is `tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py::test_g7_requires_same_authority_g6_pass_receipt` (assertion at line 182).
- What the failure shows: the gate behaves correctly. Given a G6 receipt whose status is `STOP_TD_G6_SOURCE_LIBRARY_MISMATCH`, `load_g6_pass_receipt` refuses with a RuntimeError. The test then requires the error text to contain `"g6 pass"`. The head commit changed the message to `"G7 requires G6 V2 PASS before execution: <schema> / <status>"`, and `"g6 pass"` is not a substring of `"g6 v2 pass"`. The code's refusal is right; the test and the message no longer agree.
- Cause, from history: `c5d9c64c` (the head under qualification, "fix: load G1b result and freeze together from exact pass commit") replaced
  `raise RuntimeError(f"G7 requires G6 PASS before execution: {receipt.get('status')}")`
  with
  `raise RuntimeError(f"G7 requires G6 V2 PASS before execution: {receipt.get('schema')} / {receipt.get('status')}")`.
  The test assertion dates from `42adcf2d` ("test: require same-authority G6 PASS before G7") and was not updated. `gh pr checks 258` reports no CI checks on the branch, so CI did not catch this.
- The repair (aligning the test or the message) belongs to the implementation lane. Nothing was patched here.

## 2. Code and worktree

| Item | Value |
|---|---|
| Code under qualification | `c5d9c64cf42dc8c12d91672458689c0a0a67f472` (branch `impl/td-g6g7-standalone-v2-v3preflight-20261010`, PR #258) |
| Base relation | `bf253a4dd62d943398f9ff59ed8b1e74777140a5` (the code that produced PR #259) is an ancestor of `c5d9c64c` (verified with `git merge-base --is-ancestor`) |
| Qualification branch and worktree | `qual/td-g6g7-standalone-v2-pr258-20261010`, `D:/jepa_wt_td_pr258_qual_20261010` (fresh, from exactly `c5d9c64c`) |
| `git rev-parse HEAD` | `c5d9c64cf42dc8c12d91672458689c0a0a67f472` |
| `git status --short` before and after the tests | empty |
| `core.autocrlf` | false |
| Production code edited | no |

## 3. Environment (local execution, not CI)

`C:/Users/dushy/anaconda3/python.exe`, Python 3.9.7. numpy 1.24.2, pandas 1.5.3, h5py 3.2.1, scipy 1.10.1, pytest 6.2.4. `Windows-10-10.0.26200-SP0`, launched from Git Bash. This is the same interpreter that produced PR #259.

## 4. Focused tests

```text
python -m pytest -q tests/v5/test_td_relational_value_read_v2_common.py tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py -rs
```

- Start 2026-10-10T21:33:32Z, end 2026-10-10T21:34:54Z, exit 1.
- **29 passed, 1 failed, 0 skipped** (3 third-party DeprecationWarnings).
- Full log: `docs/agent/TD_G6G7_V2_PR258_QUALIFICATION_20261010/focused_tests.log`.

Failure excerpt:

```text
    receipt["status"] = "STOP_TD_G6_SOURCE_LIBRARY_MISMATCH"
    ...
    except RuntimeError as e:
>       assert "g6 pass" in str(e).lower()
E   AssertionError: assert 'g6 pass' in 'g7 requires g6 v2 pass before execution: jepa_td_relational_g6_receipt_v2 / stop_td_g6_source_library_mismatch'
tests\v5\test_audit_td_relational_g7_s174_overlap_v2.py:182: AssertionError
```

## 5. Steps not performed because of the STOP

- Step 3: the PR #259 receipt blobs were not extracted and their SHA-256 values were not checked.
- Step 4: `load_bound_preflight()` was not called.
- Step 5: no authorization object of any kind was created.

## 6. Boundary confirmations

- No production code was edited.
- No H5AD file, expression array or count array was opened. The focused tests use synthetic fixtures under pytest temporary directories.
- No `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2` object was created, temporary or otherwise.
- G6 and G7 were not run. Corrected TD56, TD57B, TD57C, TD59 and TD60 were not run. Nothing was trained.

## 7. To resume

Once the implementation lane aligns the test with the new message (or the message with the test) on a new exact head, rerun this qualification from a fresh worktree at that head. Steps 3-5 can then use the attached script unchanged, provided it is reviewed first.
