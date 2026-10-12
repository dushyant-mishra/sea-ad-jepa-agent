# TD corrected-replay adapter contract qualification — 2026-10-12

Status: `QUALIFIED_METADATA_CONTRACT__NO_CORRECTED_VALUE_READ__NO_REPLAY_AUTHORITY__NO_TARGET_AUTHORITY`

## Purpose

This closes the metadata/custody portion of the existing corrected-replay adapter plan before any corrected biological replay is authorized. It does **not** implement or execute corrected TD56/TD57B/TD57C/TD59.

The qualified module is:

`scripts/v5/td_corrected_replay_adapter_contract_v1.py`

It validates the frozen Sample-A geometry, the admissible historical executor identities, the TD59 successor/original-provenance distinction, the non-biological metadata surface, the per-stage historical-fixture equivalence state, and the external-G7 prerequisite. It can only report readiness for a later separate owner authorization; it never creates that authorization.

## Frozen identities enforced

- Sample-A label `A_NATURAL_MIXTURE`, 25,000 rows, global rows `0..24999`.
- Source counts HVS 1,129; NPH52 1,310; SEA_AD 22,561.
- Exact 9,216 replay-address count.
- TD56 HVS/NPH52/SEA_AD recovered executor SHA-256 values from the provenance ledger.
- TD57B local and fast-wrapper SHA-256 values.
- TD57C recovered executor SHA-256 `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`.
- TD59 admissible replay-closure successor SHA-256 `870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085` while preserving original historical executor SHA-256 `3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0` with `original_executor_bytes_recovered=false`.

## Fail-closed rules

The contract rejects executor substitution, biological/pathology metadata exposure, missing required donor/operator/cell metadata, any claim that the original TD59 executor bytes were recovered, and any true replay/target/TD60/Stage4/training authority flag.

A G7 result is sufficient for readiness only if the frozen terminal is exactly `PASS_TD_G7_S174_EXACT_OVERLAP` **and** the result has been externally accepted. `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` and `STOP_TD_G7_S174_CROSSCHECK_MISMATCH` remain blocking outcomes.

All four historical-fixture equivalence stages must independently be `PASS` before the contract can return:

`READY_FOR_SEPARATE_OWNER_CORRECTED_REPLAY_AUTHORIZATION__NO_REPLAY_AUTHORITY`

Even that terminal keeps every execution and selection authority false.

## TDD evidence

RED was established first with the new focused test importing a nonexistent module; the observed failure was the expected `ModuleNotFoundError: No module named 'td_corrected_replay_adapter_contract_v1'`.

After the minimal implementation, the isolated focused test returned `7 passed`.

The exact branch code head `e8dda431b03e9365d764665fea80c111ee053710` then passed the existing target-discovery qualification workflow with the new test included:

- workflow run `38265363424`
- job `114866049053`
- **322 passed / 0 failed / 0 errors**
- tracked worktree clean before and after
- artifact `11754471954`
- artifact SHA-256 `6d968dc8903b333fcb097f23bea78d6a4cbb2eeac7d32318051daa1c379ff1c3`

## Current preflight state

Machine-readable preflight:

`custody/target_discovery/TD_CORRECTED_REPLAY_ADAPTER_PREFLIGHT_20261012.json`

It currently validates to:

`BLOCKED_G7_NOT_EXTERNALLY_ACCEPTED__NO_REPLAY_AUTHORITY`

All four historical-fixture equivalence entries remain `PENDING`. No corrected value was read and no historical equivalence replay was executed by this qualification.

## Remaining corrected-replay readiness work

1. External acceptance of the one-shot G7 outcome.
2. Historical-fixture adapter equivalence for TD56, TD57B, TD57C and TD59 against the admissible historical executors.
3. Only after both are complete: construct a separate owner-authorized corrected-replay package.
4. Corrected biological execution still requires an explicit later authorization and must stop again after the four stage receipts.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
