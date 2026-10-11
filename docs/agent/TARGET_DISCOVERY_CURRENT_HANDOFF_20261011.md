# Target Discovery — Current Takeover Handoff — 2026-10-11

Status: **ACTIVE REAL TARGET-DISCOVERY LANE**

Hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This document is the current-state addendum to the canonical takeover package in PR #284. It records the latest successor qualification result at exact implementation `7e482cf50f73a5cecda16482777129dd3ca725a6` and supersedes any older statement that PR #282 is merely "pending qualification".

## 1. Latest event: PR #282 successor qualification failed at Gate 1

Canonical qualification evidence branch:

`qual/td-g6-global-row-successor-7e482cf5-20261011`

Qualification evidence commit:

`e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

Parent implementation:

`7e482cf50f73a5cecda16482777129dd3ca725a6`

The worktree was clean before and after. No production patch was made during qualification, no rerun was performed, no owner/runtime authority was created, and neither G6 nor G7 was executed.

### Gate results

1. Focused G6/G7 suite: **FAIL — 4 failed / 215 passed**.
2. Exact real Sample-A freeze schema/global-row compatibility: **PASS** with terminal `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`; 25,000 rows; exact source counts; physical `global_row` absent as expected and derived from freeze-file position.
3. Exact PR #259 physical compatibility: **PASS — 1 passed / 0 skipped / 0 failed**.
4. Worktree integrity: clean before and after.

The four focused-suite failures share one root cause: after the successor strengthened `select_sample_a()` to validate the real input schema, four older synthetic unit-test fixtures still called the G6 selector with deliberately minimal tables lacking required real columns such as `donor_id`, `local_row`, `matrix_id`, `operator_index`, and in one case `cell_id`.

This is a **qualification-harness / stale-fixture regression**, not evidence that the authenticated real Sample-A file is incompatible. Gate 2 directly demonstrates that the real production freeze satisfies the strengthened contract.

### Owner/auditor repair choice

Preserve the stronger production selector contract. Repair the stale unit-test fixtures to instantiate the real schema expected by G6. Do **not** weaken `select_sample_a()` merely to keep underspecified synthetic fixtures green.

Any repair requires:

- a new exact PR #282 successor commit;
- fresh qualification at that exact commit;
- preservation of this failed qualification evidence;
- no authority creation until fresh qualification is accepted.

## 2. Raw qualification evidence

The authoritative seven-file record is pinned by branch+commit above at:

`docs/agent/TD_G6G7_FULL_CUSTODY_SUCCESSOR_20261011/qualification_7e482cf5/`

Files:

- `QUAL_00_environment.txt`
- `QUAL_01_full_focused_suite.txt`
- `QUAL_02_real_sample_freeze_schema.txt`
- `QUAL_03_real_pr259_compat.txt`
- `QUAL_04_changed_files_and_hashes.txt`
- `QUAL_05_no_successor_authority_or_execution.txt`
- `QUAL_06_final_state.txt`

Do not reconstruct or abbreviate the raw log and then call it the original. The evidence commit is the source of truth.

## 3. Current G6/G7 state

### Historical qualified predecessor

PR #277 qualified implementation:

`fafd4309cc086c95076cefdc94064e8b66e58ae4`

Historical qualification there was `217 passed / 0 failed / 0 skipped`, plus PR #259 physical compatibility `1 passed / 0 skipped / 0 failed`.

Its first real G6 execution is preserved as:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

The real authenticated Sample-A freeze did not physically persist `global_row`; the predecessor had assumed it did. A start marker was written, then execution failed before any corrected H5AD expression/count array was opened.

Do not alter or reuse `D:\jepa_td_real_g6_20261011\G6_OUT_fafd4309`.

Start-marker SHA-256:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

No G6 receipt exists for Attempt 0. No biological conclusion exists.

### PR #282 successor

Branch:

`fix/td-g6-global-row-binding-successor-20261011`

Failed-qualified head:

`7e482cf50f73a5cecda16482777129dd3ca725a6`

Important repair lineage:

- `e437f29646f61ac45b74df45e227999a5d603de1` — RED global-row regression.
- `bf815958dc6cd601922dbb176e05cce7eb1a543b` — production global-row/pre-spend repair.
- `4786925f6807cf9b96bc266fe708f21807a2086b` — earlier fixture correction.
- `7e482cf50f73a5cecda16482777129dd3ca725a6` — qualification-runner hardening; now known to fail Gate 1 because four older synthetic fixtures are stale relative to the strengthened selector contract.

**Current qualification state:**

`FAILED_GATE_1_STALE_SYNTHETIC_FIXTURES__REAL_SAMPLE_GATE_PASS__PR259_COMPAT_PASS__NO_EXECUTION_AUTHORITY`

Replacement G6 is blocked.

## 4. Data and custody authorities that remain valid

### Historical 50K CSR

Outer ZIP SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Split parts:

- part001 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`

CSR members:

- `data.npy` `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`
- `indices.npy` `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`
- `indptr.npy` `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`
- `shape.npy` `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`

Historical row authority remains:

`global_row = np.arange(len(freeze_csv))`

assigned before any filtering or merge. Reset `sample_row` cannot define generic CSR row identity.

### Corrected substrate

Corrected S174 substrate SHA-256:

`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

### PR #259 G4/G5 narrow integrity authority

- execution head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- executed code `bf253a4dd62d943398f9ff59ed8b1e74777140a5`
- driver receipt SHA `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping receipt SHA `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Scope only: authenticated physical mapping and value-blind address resolution. This is not a biological PASS.

## 5. Historical biological evidence — preserve exactly

- TD56/TD56S: historical positive disjoint-view within-donor relational recurrence across HVS/NPH52/SEA_AD; requires corrected replay for current authority.
- TD57B: historical prospective `24/24` positive; weakest observed-minus-null-p95 margin `+0.0375178074843`; requires corrected replay.
- TD57C: immutable historical FAIL `NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`; nearest-third Panel-0 HVS failed `2/4`. Never rescue or relabel. A later corrected PASS would be historical/corrected divergence.
- TD59: historical `24/24` positive; weakest p95 margin `+0.0011566307718604563`; `22/24` above null max. Original executor remains unrecovered; replay-closure successor must never be called the original executor.
- TD60: `PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`. Never call TD60 failed.

Controlling corrected-replay interpretation:

`docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`

Even the strongest corrected relational outcome does not itself select the target or authorize TD60/training.

## 6. Scientific architecture to preserve

Technology/acquisition is an observation operator, not unrestricted biology. Donor is the primary biological replication unit. Source→donor→cell hierarchy is mandatory. Biological uncertainty and measurement uncertainty remain separate. Unsupported targets abstain; measured zero remains a valid observation. Do not force modality imputation. Do not grant authority to named coordinates merely because they are stable. Low neural loss/noncollapse is not biological qualification.

Incumbent hypothesis only, not winner:

`T(c,q) = { Z_shared(c), R_broad/meso(c), Z_query(c,q), Support(c,q), U_bio(c,q), U_meas(c,q), optional Specialist(c,q) }`

The broader foundation-design audits also identified two principles relevant later but not yet executable authority: observation-operator conditioning should use physically meaningful acquisition descriptors rather than free dataset IDs, and basis/subspace stability must be assessed before coordinate-specific uncertainty is treated as biologically meaningful.

## 7. Query-aware target evidence

Historical developmental evidence supports measured q-conditioned non-q same-cell context with q-excluded normalization and q address only on the student side. Historical heldout R²:

- q-specific `0.4300`
- technical+q `0.3496`
- q-agnostic `0.2760`
- q-count-only `0.1610`

These are developmental evidence, not current target authority.

Mandatory falsifiers remain q-count-only, q-address-only, q-agnostic, wrong-q, technical+q, q-excluded teacher, identity+support, matched wrong-cell and fine-neighborhood wrong-cell.

## 8. SCENIC+ / ATAC / Morabito

Regulatory evidence is specialist/soft-prior/falsifier evidence only unless independently requalified.

Historical integrated summary:

- 7 TFs
- 27 targets
- 96 edges
- Tier A: STAT1, ELF1, SPI1
- Tier B: IRF8, BACH1, CEBPA, RELA

Morabito: RNA 4,126; ATAC 12,232. It is not pristine independent validation because relevant evidence has already been used historically.

## 9. V2 target-tournament governance

PR #275 is governance-only relative to this critical path. V1 is scientifically superseded for future real tournament execution. V2 prefreeze is:

`docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze-v2.md`

Do not run a real tournament until G6/G7 are accepted, corrected relational replay is audited, population/evidence rights/splits/support are frozen, and the V2 evidence→receipt→adjudication implementation is independently qualified.

No tournament terminal currently grants target authority.

## 10. Immediate next actions for the new agent

1. Audit PR #282 and the exact failed qualification evidence commit `e4d771cb...`.
2. Patch only the stale tests/fixtures that are inconsistent with the strengthened real schema contract. Do not weaken production validation to satisfy synthetic shortcuts.
3. Commit a new exact PR #282 head.
4. Re-run the same qualification gates fresh at that exact head on the canonical machine. Preserve all logs, including any failure.
5. If and only if all qualification gates PASS and the worktree/code identities are clean, prepare a **new** owner decision and **new** runtime authorization bound to the newly qualified implementation. Never reuse the `fafd4309` authority files.
6. Macha then executes replacement G6 exactly once in a fresh never-used namespace and stops after G6.
7. External auditor reviews all five G6 artifacts, hashes, receipt semantics and physical-source accounting before any G7 authorization.
8. Only after G7 is separately authorized, executed, and externally audited may a separate corrected TD56/57B/57C/59 replay authority be considered.
9. Do not jump to TD60, target selection, representation selection, Stage4 or training.

## 11. Macha instructions now

Until a new PR #282 head is produced and handed back:

- do not rerun qualification at `7e482cf5`;
- do not patch the canonical execution environment ad hoc;
- do not create owner/runtime authority;
- do not create a replacement G6 output namespace;
- do not touch `G6_OUT_fafd4309`;
- do not run G6/G7;
- preserve the seven qualification files and exact evidence commit.

When a new exact successor head is issued, Macha should qualify that head only, report lane/branch/SHA, exact gate results, whether any corrected values were opened, whether any attempt marker was created, and stop for audit.

## 12. Read order for complete takeover

1. `docs/agent/TARGET_DISCOVERY_CURRENT_HANDOFF_20261011.md` (this file)
2. `docs/agent/TARGET_DISCOVERY_START_HERE_20261011.md`
3. `docs/agent/TARGET_DISCOVERY_CANONICAL_TAKEOVER_20261011.md`
4. `docs/agent/TARGET_DISCOVERY_CANONICAL_STATE_20261011.json`
5. `docs/agent/TD_G6_ATTEMPT0_EXECUTION_RECORD_20261011.md`
6. `docs/agent/TARGET_DISCOVERY_HISTORY_AND_AUDIT_LESSONS_20261011.md`
7. `docs/agent/TARGET_DISCOVERY_EVIDENCE_CODE_DATA_INDEX_20261011.md`
8. `docs/agent/MACHA_TARGET_DISCOVERY_AND_PARALLEL_LANE_RUNBOOK_20261011.md`
9. raw qualification evidence branch+commit `qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`
10. corrected-replay interpretation prefreeze
11. historical target-discovery handoff/TD33 guard
12. PR #282 exact code and diff; PR #277 historical custody; PR #259 G4/G5 evidence; PR #275 V2 governance after the real critical path is understood.

## 13. Claim boundary

Nothing in this handoff creates biological authority. Current state remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Immediate executable-development task:

`REPAIR_STALE_G6_SYNTHETIC_TEST_FIXTURES__NEW_EXACT_COMMIT__FRESH_QUALIFICATION__NO_G6_EXECUTION`
