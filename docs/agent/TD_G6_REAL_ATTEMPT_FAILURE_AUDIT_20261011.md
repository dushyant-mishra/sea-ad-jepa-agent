# REAL TD G6 ATTEMPT FAILURE AUDIT — 2026-10-11

## Auditor terminal

`REAL_G6_ATTEMPT_SPENT__FAILED_BEFORE_ANY_H5AD_VALUE_READ__SAMPLE_A_FREEZE_HAS_NO_GLOBAL_ROW__NO_RECEIPT__G7_BLOCKED__NO_BIOLOGICAL_REPLAY_AUTHORITY`

This is the controlling status for the first owner-authorized real G6 attempt at qualified implementation commit:

`fafd4309cc086c95076cefdc94064e8b66e58ae4`

No G7, corrected TD56/TD57B/TD57C/TD59 replay, TD60, target selection, representation selection, Stage4, or training is authorized by this incident or by any predecessor G6/G7 authorization.

## Attempt status

The attempt is irreversibly spent because the qualified G6 entrypoint successfully created its exclusive execution-start marker before the failure.

Reported preserved local marker:

- `G6_EXECUTION_START.json`
- status: `STARTED_NOT_A_PASS`
- SHA-256: `ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`
- execution-start time reported: 2026-10-11T19:54:24Z

No G6 receipt or corrected-value artifact was written.

The failed namespace must remain immutable. It must never be deleted, repaired in place, renamed into a success namespace, or reused.

## Pre-spend qualification / authority checks

The execution report states that before the marker was created:

- detached worktree HEAD was exactly `fafd4309cc086c95076cefdc94064e8b66e58ae4` and clean;
- the qualified implementation identity matched using the production `code_identity()` implementation;
- owner decision bytes matched SHA-256 `36599b7ade189e051b6e156d53ea1acd4caf42794f26b152d7eada0513a1a273`;
- runtime authorization bytes matched SHA-256 `7cc66f601d6fc294ef9255f4e9ac4b1e1f16db56d1ddf52cf1fb839646fc91fa`;
- exact PR #259 driver/mapping/replay-manifest physical bytes matched their frozen pins;
- Sample-A freeze, provenance, collision ledger, Macha freeze and TD archive matched their pins;
- the four historical CSR members matched their frozen SHA-256 values.

The predecessor owner decision/runtime authorization are therefore consumed and must not be reused for any successor attempt.

## Failure

Reported exception:

`AttributeError: 'DataFrame' object has no attribute 'global_row'`

The defect is visible directly in the qualified G6 source. After `begin_namespace(...)`, G6 loads the real Sample-A freeze and later executes:

`global_row = sample_a.global_row.astype(int).to_numpy()`

The real frozen Sample-A table does not contain a `global_row` column. It contains `sample_row` and the physical row-identification fields used by PR #259.

The crash occurred before the H5AD iteration/value-read loop. Therefore no corrected HVS/SEA H5AD expression/count array was opened by this attempt.

G6 had already authenticated/read small pinned inputs, TD50 historical sentinels and the historical CSR authority; the CSR arrays were memory-mapped but the crash preceded NPH52 row extraction.

## Root cause

This is an implementation/qualification defect, not a data mismatch.

The V2 implementation inherited a V1 assumption that the freeze carried a `global_row` field. The synthetic fixture encoded that assumed field instead of reproducing the real frozen file schema. The qualification suite therefore checked the implementation against a synthetic schema partly defined by the implementation itself and never enforced real-header compatibility for every column consumed by G6.

PR #259 did not expose this because its value-blind mapping path uses the frozen physical row identifiers/local rows and never needed the historical 50K CSR row index.

## Historical row-addressing authority

Do not infer a replacement mapping from the failed real execution.

The repository already contains an immutable forensic correction for the 50K discovery matrix in `target_discovery/iterations/TD23_TD29A_FORENSIC_LEDGER.md`.

It states:

- rows `0..24,999` of the historical 50K discovery matrix are `A_NATURAL_MIXTURE`;
- rows `25,000..49,999` are `B_COVERAGE_DISCOVERY`;
- `sample_row` independently resets to `0..24,999` inside both samples;
- prior B-sample use of reset `sample_row` as a matrix-global row created a serious row-alias artifact and was explicitly invalidated.

Therefore, for the G6 population, which is frozen to Sample A only:

`historical_50k_global_row = sample_row`

This follows from pre-existing row-addressing authority, not from corrected-value outcomes and not from the failed G6 attempt.

Important: this identity is Sample-A-specific. It must not be generalized to Sample B, where the corresponding global row is offset by 25,000.

## Successor engineering requirements

No new value-read attempt is authorized here.

A successor implementation may be developed and tested only after preserving this failure. Minimum requirements before a new owner decision can even be considered:

1. Start from a new successor commit/branch. Never amend `fafd4309` or the spent output namespace.
2. Add a failing real-schema compatibility test first. The test must demonstrate the exact current failure on a fixture whose columns are copied from the real Sample-A freeze header and which intentionally has no `global_row` column.
3. Add an explicit required-input-schema validator covering every freeze column consumed by G6, not only the one that failed.
4. Derive the historical CSR row for Sample A from the already-frozen row-addressing contract, not from a caller-supplied synthetic `global_row` field.
5. Add adversarial tests proving:
   - Sample A maps `sample_row 0..24,999` to historical rows `0..24,999` exactly;
   - a B-sample row cannot silently use the Sample-A rule;
   - missing/duplicate/non-integer/out-of-range `sample_row` fails closed;
   - altered sample label/order cannot change addressing silently.
6. Re-run the existing full focused qualification suite and exact PR #259 physical compatibility checks on one exact successor commit.
7. Add a real-file-header-only qualification step using the pinned Sample-A freeze bytes. This step may inspect schema/header/row identities but must remain value-blind with respect to corrected H5AD expression arrays.
8. Preserve a distinct successor qualification receipt. The 217-green qualification at `fafd4309` is historical evidence only and is insufficient for a successor.
9. Only after external audit of that successor qualification may a new owner decision and new runtime authorization be created, bound to the new exact implementation commit and explicitly representing a new one-shot attempt.
10. A future real attempt must use a new never-used output namespace. The spent `G6_OUT_fafd4309` namespace remains immutable failure evidence.

## Authority boundary

Current terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

G7 is blocked.
Corrected TD56/TD57B/TD57C/TD59 replay is blocked.
TD60 remains `PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`.
V79 remains a separate synthetic lane and is unaffected by this audit.
