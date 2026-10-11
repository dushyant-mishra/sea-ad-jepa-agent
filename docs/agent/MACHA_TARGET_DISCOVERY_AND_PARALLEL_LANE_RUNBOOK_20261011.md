# Macha Runbook — Real Target Discovery + Parallel Lane Coordination — 2026-10-11

This is the controlling coordination note for Macha while the new agent takes over the target-discovery program.

## 1. Non-negotiable lane separation

### Lane A — REAL target discovery

Current allowed work:

- preserve the completed failed qualification record for PR #282 head `7e482cf50f73a5cecda16482777129dd3ca725a6`;
- wait for a new exact successor commit after stale synthetic test fixtures are repaired;
- when explicitly handed a new exact SHA, run the same qualification gates on that SHA only and stop for audit;
- after explicit owner/auditor approval only, execute replacement G6 once under fresh owner/runtime authority;
- later, only after external G6 audit, execute G7 if explicitly authorized.

Forbidden unless separately authorized:

- ad-hoc patching of the canonical execution environment;
- rerunning qualification at `7e482cf5` and calling it a new qualification;
- creating owner/runtime authority before a fresh successor qualification is accepted;
- corrected TD56/57B/57C/59 replay;
- TD60;
- target selection;
- representation selection;
- Stage4;
- real training.

### Lane B — V79 / synthetic-exact-S174 structure lane

Current state is PR #280:

`EXACT_S174_STRUCTURE_REPLAY_FAILED_CLOSED__OPERATOR_MODEL_LOGISTIC_NONCONVERGENCE__NO_METRICS_COMPUTED__CONTROLLER_REPAIR_DECISION_REQUIRED__BAYESIAN_CONFIRMATION_OFF__TRAINING_OFF`

Do not mix V79 outputs, caches, code, penalties, metrics or authority into Lane A.

## 2. Preserve failed G6 Attempt 0 exactly

Canonical machine root:

`D:\jepa_td_real_g6_20261011\`

Do not delete, edit, rename-in-place or reuse:

`G6_OUT_fafd4309`

Classification:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

The namespace is historical execution evidence, not a biological failure and not the replacement execution namespace.

Preserve:

- `G6_OUT_fafd4309/G6_EXECUTION_START.json`
- `run_record/RUN_RECORD.txt`
- `run_record/G6_NAMESPACE_SHA256.txt`
- `run_record/g6.stdout.txt`
- `run_record/g6.stderr.txt`
- `run_record/PRECONDITION_PINS.txt`

Start-marker SHA:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

No G6 receipt exists for Attempt 0. No corrected H5AD value array was opened.

## 3. Completed successor qualification at 7e482cf5 — preserve and do not rerun

Implementation branch:

`fix/td-g6-global-row-binding-successor-20261011`

Exact qualified candidate that failed:

`7e482cf50f73a5cecda16482777129dd3ca725a6`

Qualification evidence branch:

`qual/td-g6-global-row-successor-7e482cf5-20261011`

Qualification evidence commit:

`e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

Raw evidence directory:

`docs/agent/TD_G6G7_FULL_CUSTODY_SUCCESSOR_20261011/qualification_7e482cf5/`

Files:

- `QUAL_00_environment.txt`
- `QUAL_01_full_focused_suite.txt`
- `QUAL_02_real_sample_freeze_schema.txt`
- `QUAL_03_real_pr259_compat.txt`
- `QUAL_04_changed_files_and_hashes.txt`
- `QUAL_05_no_successor_authority_or_execution.txt`
- `QUAL_06_final_state.txt`

Gate results:

1. Focused suite: **FAIL — 4 failed / 215 passed**.
2. Real Sample-A freeze: **PASS** — `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`; 25,000 rows; exact source counts; physical `global_row` absent as expected.
3. Real PR #259 compatibility: **PASS — 1 passed / 0 skipped / 0 failed**.
4. Worktree clean before and after.

No patch was made during qualification. No rerun occurred. No owner/runtime authority was created. No G6 or G7 was run.

The four failures are stale synthetic unit-test fixtures that invoke the hardened G6 `select_sample_a()` without the real required schema (`donor_id`, `local_row`, `matrix_id`, `operator_index`, and where applicable `cell_id`). Gate 2 demonstrates that the authenticated real Sample-A file satisfies the strengthened contract.

Classification:

`FAILED_GATE_1_STALE_SYNTHETIC_FIXTURES__REAL_SAMPLE_GATE_PASS__PR259_COMPAT_PASS__NO_EXECUTION_AUTHORITY`

Do not reinterpret this as a real-data failure.

## 4. Current immediate Macha state — STOP until a new exact successor SHA is issued

The owner/auditor repair decision is to preserve the stronger production selector contract and repair the stale test fixtures to the real schema. This code repair is being handled on the PR #282 development lane, not by ad-hoc edits in the execution environment.

Until a new exact successor SHA is explicitly handed to you:

- do not rerun `qualification_runner.sh` at `7e482cf5`;
- do not modify the seven evidence files;
- do not create a new qualification folder for the same head;
- do not create owner/runtime authority;
- do not create a replacement G6 output namespace;
- do not run G6/G7;
- do not touch `G6_OUT_fafd4309`.

If asked for status, report only the exact failed qualification above and downstream blocks.

## 5. When a new exact PR #282 successor SHA is issued

Create a fresh clean detached worktree at the exact SHA. Record exact HEAD before doing anything.

Run the qualification runner from that exact worktree:

`docs/agent/TD_G6G7_FULL_CUSTODY_SUCCESSOR_20261011/qualification_runner.sh`

The qualification must remain no-value with respect to corrected H5AD count/expression arrays.

### Required qualification gates

1. **Focused G6/G7 suite**
   - must include `tests/v5/test_td_g6_global_row_binding.py`;
   - the formerly stale fixtures must now exercise the real G6 schema rather than bypass it;
   - no failure/error/skip may be silently omitted.

2. **Exact production Sample-A freeze compatibility**
   - file SHA must be `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`;
   - physical CSV must not contain `global_row`;
   - all G6 physical source columns must exist;
   - successor must derive Sample-A global rows exactly `0..24999` from original freeze-file position;
   - require terminal `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`.

3. **Exact PR #259 physical compatibility**
   - driver receipt SHA `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`;
   - mapping receipt SHA `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`;
   - replay manifest SHA `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
   - a skip is not a PASS.

4. **Exact clean implementation identity**
   - record HEAD before and after;
   - worktree must remain clean;
   - report common/G6/G7 code identities produced by the qualified `code_identity()` implementation.

### Return to owner/auditor

Return every qualification log and the complete output directory listing. Then STOP.

Do **not** create owner/runtime authorization yourself unless explicitly instructed after audit.

## 6. What counts as qualification failure

Any of the following fails closed:

- exact HEAD mismatch;
- dirty tracked worktree;
- focused test failure/error;
- real-sample schema test fails or is absent;
- real-sample freeze SHA mismatch;
- `global_row` derivation not exactly `0..24999` for Sample A;
- PR259 compatibility skip/failure;
- unexpected code-identity drift;
- any corrected H5AD value/count read during qualification.

On failure, preserve logs and stop. Do not repair and rerun in the same qualification record without owner/auditor review.

## 7. Replacement G6 — only after fresh accepted qualification and fresh authority

After a new successor qualification is accepted, the owner/auditor will issue:

- a new owner decision bound to the exact newly qualified successor implementation SHA;
- a new runtime authorization bound to that owner decision and exact implementation identities;
- a new fresh output namespace.

The old `fafd4309` owner decision/runtime authorization must never be reused for the successor.

Before replacement G6:

- verify exact successor HEAD and clean worktree;
- verify new owner/runtime files byte-exact;
- verify PR259 pins;
- verify historical CSR four member hashes;
- verify Sample-A freeze/provenance/collision/Macha freeze/TD artifacts pins;
- verify destination namespace never existed.

The successor is intentionally designed so metadata/schema/TD50/CSR row-binding checks complete **before** the immutable G6 start marker. If one of those checks fails, no G6 value-read attempt should be spent.

Once the replacement G6 marker is created:

- preserve every outcome;
- no delete/repair/rerun without a new explicit owner decision;
- stop after G6;
- do not run G7 automatically.

## 8. Expected replacement G6 success contract

Expected exact G6 receipt terminal:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Expected five-file namespace:

- `G6_EXECUTION_START.json`
- `G6_RECEIPT.json`
- `MANIFEST.json`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz`

Expected accounting semantics:

- HVS+SEA physically reread rows: `23,690`;
- NPH52 authenticated historical pass-through rows: `1,310`;
- total Sample A rows: `25,000`.

Do not serialize a false claim that all 25,000 rows were physically reread.

On success return:

- exact HEAD;
- exact command;
- environment;
- stdout/stderr;
- five artifact SHA-256s;
- receipt and manifest contents;
- verified physical-source SHA accounting;
- warnings or anomalous state.

Then STOP for external audit.

## 9. G7

G7 remains blocked until the owner/auditor accepts replacement G6.

If later authorized, G7 must compare authenticated physical H5AD values against authenticated S174 values. Never substitute the G6 cache as the independent counterpart.

Stop after G7 and return all evidence for audit before any biological replay.

## 10. Corrected biological replay

Macha must not run corrected TD56/57B/57C/59 merely because G6/G7 pass.

A separate owner authorization must reference:

`docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`

Historical outcomes remain immutable:

- TD56 historical positive;
- TD57B historical 24/24 positive;
- TD57C historical FAIL;
- TD59 historical 24/24 positive.

A corrected TD57C PASS would be divergence, not retroactive correction of the historical FAIL.

## 11. TD60 / target / training

TD60 remains:

`PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`

Never call it failed.

No target winner exists.
No representation winner exists.
Stage4 and training are off.

## 12. Reporting discipline

Every report should state:

- lane (`REAL_TD` or `V79`);
- exact branch and SHA;
- whether corrected biological values were opened;
- whether a namespace/attempt marker was created;
- exact terminal;
- what downstream actions remain unauthorized.

Do not use phrases such as “passed biology” for custody, schema or compatibility checks.

## 13. If Claude Code safety blocks local research-data work

Do not route around a safety denial using unrelated tool mechanisms.

Report the exact blocked command and classifier reason. The owner may run a reviewed command/script directly or grant a narrow permission. Public availability alone is not sufficient justification for unrestricted handling. Any exception must remain narrow to the authorized local research workflow and avoid unnecessary export of donor/pathology records.

## 14. V79 parallel lane reminder

If directed to resume V79:

- work only from the controlling V79 PR/decision;
- preserve PR #280 failed-closed result;
- no predictive metric was produced in that failed execution;
- operator-within-source logistic nonconvergence requires a prospective controller repair decision before another replay;
- do not import V79 repair choices into real TD without a prospective cross-lane contract.
