# Macha independent review — Task 0 pre-merger migration/custody (PR #381)

Date: 2026-10-14.

Role:
- `INDEPENDENT_HOSTILE_REVIEWER_OF_CONTROLLER_WORK` for Task 0.
- `AUTHOR_IMPLEMENTER` (provenance only) for old PR #356 Tasks 1–2.

This follows `MACHA_ROLE_INDEPENDENCE_CORRECTION_V1` and review packet V2 (PR #322 @ `5dfb2954`).

This file is non-controlling.

**Read-only.** No candidate outcome, `reader_validation`, `reader_oracle`, DEV/SEALED, pathology or protected object was opened. No GPU or training job was run.

## Verdict

`Task0 c80d7398b41f10208ec1622bc52599383b940be6 = REJECT_WITH_BLOCKING_FINDINGS`

Five IMPORTANT findings (B1–B5) block freezing. None invalidates Task 0 globally; each is a bounded repair to one subcomponent. What already holds:
- the F1 decomposition mechanics;
- the F2 mandatory-boolean mechanics;
- F3 stream completeness;
- the content of F6–F9;
- the old Task 3/4 stop law;
- the Tasks 5–12 stop.

`OldTask1_2 ff597faf2182522a320ec5322f8db9b67c9c6094`: **no independent verdict from Macha (author)**.
- Author attestation: these are exactly the bytes I implemented and reviewed under the PR #356 protocol.
- PR #382 (run `38644641042`, job `116128364543`, `332 passed in 8.94s`) is the independent verification. Its 332 versus my Windows-local 331+1 skip is the wide-float test, which runs on Linux. That closes my deferred item D3.
- On the controller's migration treatment: **ADAPT_AND_WRAP accepted for both**, conditional on B4.

Unified Task 1 must not begin until B1–B5 are repaired and the repaired head is re-accepted.

## A. Exact heads inspected

| object | head |
|---|---|
| Task 0 (PR #381) | `c80d7398b41f10208ec1622bc52599383b940be6`, base `9328f1c0`; local run 29/29 passed (local evidence; CI run `38645994312` also 29 passed) |
| old Tasks 1–2 | `ff597faf…`; `canonical_v1.py` blob `b8a34d8d…`, `custody_v1.py` blob `8efb7622…`; branch tip `f53c13e6` adds only my checkpoint docs |
| PR #382 | `416e36d1` |
| PR #322 | `5dfb2954`. The brief cited `b97810c7`: `BRANCH_MOVED`, documentation only (review packet V2, role-independence correction, no-repeat table). |
| PR #323 | `af0e4e9c`. The brief cited `5643e86d`: `BRANCH_MOVED`, documentation only (handoff V17). |
| PR #380 plan | `5b6bf07e` (taxonomy amendment; **not an ancestor of the Task 0 head**, see B5) |

## B. Findings

### B1 — IMPORTANT, `NEW_BLOCKING_DEFECT` (F5): the F1 machinery contradicts the completeness sidecar about old Tasks 1–2

- **Loci (all at `c80d7398`):**
  - `PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json` → `active_or_partial_work[FORMER_SYNTH_TASKS_1_3_REQUIREMENTS]`, `FORMER_SYNTH_TASKS_4_12`, `artifacts[PR356_SYNTH_PLAN]`;
  - `PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json` → `PR356_SYNTH_PLAN` children.
- **Defect.** In the matrix and decomposition:
  - Old Tasks 1–3 are `REQUIREMENTS_PRESERVED__IMPLEMENTATION_NOT_STARTED`, with `tests_created: []`.
  - The decomposition child `PR356_TASKS1_3_REQUIREMENTS` is `REQUIREMENTS_ONLY__IMPLEMENT_UNDER_UNIFIED_PLAN`, bound to the plan head `2c2723a1`.
  - No matrix or decomposition record binds the implemented substrate at `ff597faf`. Only the separate `PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json` does.
  - Old Task 4's requirements go to destination "none; requirements replaced by unified plan" in the decomposition, against the stop law (`REQUIREMENTS_MIGRATE_ONLY`) in the completeness file.
  - A consumer of the primary matrix would therefore re-implement Tasks 1–2 and drop Task 4's requirements.
- **Why the tests missed it.** `active_or_partial_work` is not validated. No test cross-checks matrix/decomposition against the completeness sidecar.
- **Minimal repair.**
  1. Replace the PR #356 children with five children:
     - `OLD_TASK1_IMPLEMENTATION` (`ff597faf`, blob `b8a34d8d…`, ADAPT_AND_WRAP);
     - `OLD_TASK2_IMPLEMENTATION` (`ff597faf`, blob `8efb7622…`, ADAPT_AND_WRAP);
     - `OLD_TASK3_REQUIREMENTS` (stopped, migrate only);
     - `OLD_TASK4_REQUIREMENTS` (stopped, migrate only, destination CaseBundle/TruthBundle);
     - `OLD_TASKS5_12` (superseded).
  2. Fix both `active_or_partial_work` entries.
  3. Add a validator assertion that each PR #356 object's state and head agree across matrix, decomposition and completeness.
- **Scope.** PR #356 custody subcomponent only.

### B2 — IMPORTANT, `NEW_BLOCKING_DEFECT` (F2 content): available exact identities declared unavailable, for authority-bearing artifacts

- **Loci.**
  - Matrix: `REAL_SUPPORT_PROFILE`, `REAL_GEOMETRY_PROFILE`, `MACHA_REAL_DATA_AUDIT`, `PR356_SYNTH_PLAN`.
  - Dual-stream registry: `MACHA_PR314_CORRECTED_REPLAY`, `MACHA_REAL_DATA_AUDIT`, `MACHA_V79_TERMINAL_NOT_QUALIFIED`, `MACHA_V79_Q00_Q11_REALIZATION_CUSTODY`.
- **Defect.** Each record has `exact_identity_available: false` while its identity exists:

  | artifact | available identity |
  |---|---|
  | `REAL_SUPPORT_PROFILE` | `docs/agent/READER_FIT_SUPPORT_OVERLAP_PROFILE_V1.json` at `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777` (blob `e816483b75116c06979b9fd1507e3e0ebfb281df`, SHA-256 `b78e65af8290245519bac7781f61793150592da9f542593dc0100df5cbdd395a`; file last changed in `a80c4e0981ced78b6ad8bc58d4c74658e26b7458`). The record cites the 6-character `f5a8eb`. |
  | `REAL_GEOMETRY_PROFILE` | `docs/agent/READER_FIT_DATA_GEOMETRY_PROFILE_V1.json` at `f5a8ebed…` (blob `1b50ceb4d28ea2b2e4ad0c88a3c34c816a908fd4`, SHA-256 `1ddf37827d548c84f533add702722e3015ea4abaedf258bf03a9c13e65d36f3a`; file last changed in `f652f5bc5e9cba7d006ef274ca63719717b0c22f`) |
  | `MACHA_REAL_DATA_AUDIT` | commit `ccc3a08939694f5d35b3048c94ec44f44618eef4`; receipt index `results/target_discovery/real_qualification_macha_20261014/QUALIFICATION_RECEIPT_INDEX_V1.json`, SHA-256 `2af2acc3bf29c51aa885626ddd4567e5b8d9b885b747c335031d1b932c0ba86c` (binds every artifact). The record's path is the branch name. |
  | `MACHA_V79_TERMINAL_NOT_QUALIFIED` | receipt `V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V2.json`, SHA-256 `ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd`; scorer `ac1e73d79489438634aaeeca035d229875f3186a`; authorization `4793d8f9024891a6572337246c76dea871b65ebde476d8f3983c483498b80337`. **Bytes local-only** at `D:/jepa_v79_scoring_run_ac1e73d7_20261013/scoring_output/`; the custody record must say so. |
  | `MACHA_V79_Q00_Q11_REALIZATION_CUSTODY` | frozen result/realization-ledger constants in `scripts/v79/v79_v2_core_score_authority.py` at `ac1e73d7` (bind file blob + constants) |
  | `MACHA_PR314_CORRECTED_REPLAY` | commit `c6899a29…` and outcome doc path (bind blob) |

  In addition:
  - Three of these records carry authority (`AUTHENTICATED_CALIBRATION_ONLY`, `…CALIBRATION_AUTHORITY…`, `authority_basis: EXACT_COMMIT_AND_AUTHENTICATED_AUDIT_OR_RECEIPT`) without any bound identity.
  - That is authority without identity: the same stop condition as "a reference cannot be identity-bound".
- **Why the tests missed it.** The validator checks `exact_identity_available` only for presence and type, and enforces fields only when it is `true`. It cannot know availability. It does not validate the commit/digest format; `f5a8eb` passes. No rule forbids authority-bearing classes or bases when identity is `false`.
- **Minimal repair.**
  1. Bind the identities above.
  2. Validator: require `source_commit` to be 40-hex and `artifact_digest` to be 64-hex (or blob + path) when available.
  3. Require an `identity_unavailable_reason` when `false`.
  4. Forbid `authority_basis ∈ {EXACT_COMMIT_AND_AUTHENTICATED_AUDIT_OR_RECEIPT, AUTHENTICATED_CALIBRATION_RECEIPT}` and any `AUTHENTICATED_CALIBRATION*` authority when `exact_identity_available` is `false`.
  5. Add a field stating where the bytes are: repo blob, public-source SHA, or local-only.
- **Scope.** Listed records plus one validator rule.

### B3 — IMPORTANT, `NEW_BLOCKING_DEFECT` (scientific firewall): protected-partition facts routed to calibration; one artifact, two authorities

- **Loci.**
  - Matrix `MACHA_REAL_DATA_AUDIT`: `reusable_components` includes "protected partition facts", with `destination_in_unified_architecture: "calibration inputs + dependency ledger"`.
  - Dual-stream registry: the same `artifact_id` with `current_authority: AUDIT_CUSTODY_AND_CALIBRATION_AUTHORITY_ONLY`, while the matrix has `AUDIT_CUSTODY_AUTHORITY_ONLY`.
- **Defect.** The partition-dependent facts from my audit derive from reader-validation/oracle donor membership:
  - NPH52 has 0 reader-validation and 2 reader-oracle donors;
  - 4,894 NPH52-only addresses are never measured in reader-validation;
  - SEA_AD held-out subclass donor counts.

  V3.1 §2.2 requires calibration donors to be disjoint from validation/oracle by donor ID. The merged law keeps those partitions protected and never usable as rescue pools. My Tasks 1–2 checkpoint (§6 item 4, `f53c13e6`) already recorded this correction to my own earlier suggestion. Separately, one artifact carries two different authority strings across Task 0 files.
- **Why the tests missed it.** `reusable_components` and destination are free text. There is no cross-file single-authority check.
- **Minimal repair.** Split the audit's reusable components into two:
  - **Partition-independent operator-level facts**, which may be calibration inputs once identity-bound: 289 addresses with no scalar-measuring operator; the 17,186-address all-operator core; source-only 730/4,894/4,710; the reader-fit Level-4 depth-retention census.
  - **Partition-dependent facts**, as `PROSPECTIVE_CONVENTION` stress structure only, never `AUTHENTICATED_EMPIRICAL_CALIBRATION`.

  Then unify the authority string, and add a validator check that each `artifact_id` has exactly one authority across matrix, decomposition and dual-stream.
- **Scope.** One artifact plus one validator rule.

### B4 — IMPORTANT, `NEW_BLOCKING_DEFECT` (F5/E): old Task 2 reuse lacks its external obligations; the Tasks 1–2 checkpoint is not in custody

- **Loci.** Completeness `PR356_TASK2` and `PR356_TASK1`; the unresolved ledger.
- **Defect.** The author checkpoint is `docs/agent/PRODUCTION_SYNTHETIC_TASKS_1_2_CHECKPOINT_MACHA_20261014.md` at `f53c13e6`, SHA-256 `412473ac5075f03bcfc1390b93a0db1694d2b595165f74b9fc7c9c61598a94a6`. It is not bound anywhere in Task 0. Its binding obligations do not appear either. The custody substrate is safe only if they hold, and the module documents but cannot enforce them:
  - **O1:** one ledger per testbed, anchored from genesis. A fresh ledger bypasses E1/W1/W2.
  - **O2:** the ledger head is published after every entry, and `expected_head` is checked. Exposure erasure by re-chaining is detectable only against a published head.
  - **O3:** every qualification claim reports both `qualification_draws_for_method` and `qualification_draws_in_lineage`.
  - **O4:** `withheld_check_eligible` is consulted only after the version's own reveal.
  - **O5:** realization content is regenerated from the root at reveal.
  - **O6:** the secret scan runs on a full `git archive` export of each published commit.
  - **O7:** withheld worlds are emitted inside the qualification budget.
  - **O8:** defect justifications are audited.

  Also missing:
  - Deferred minor **D1:** a catch-all `except Exception` wraps internal bugs; only 23 of 182 refusal tests match the message.
  - Open questions for the deciding lane:
    - the E2 precommitment-hash erratum (E2 as written is circular);
    - a post-reveal fresh withheld family (unimplemented; fail-closed ineligible);
    - the V3.1 §2.2 status of reader-fit as a calibration source.
- **Why the tests missed it.** Required unresolved IDs cover review and acceptance of Tasks 1–2, not their reuse conditions.
- **Minimal repair.**
  1. Bind the checkpoint identity in `PR356_TASK1`/`PR356_TASK2`.
  2. Add one unresolved item per O1–O8, for D1, and for each of the three questions; mark O1–O8 `blocks_same_code_path: true` for any unified use of the custody substrate.
  3. Add these IDs to the validator's required set.
- **Scope.** PR #356 custody subcomponent.

### B5 — IMPORTANT, `NEW_BLOCKING_DEFECT` (F4): taxonomy extended by the validator before the plan, then ratified retrospectively

- **Loci.**
  - `scripts/v5/td_unified/premerger_migration_task0.py` `MIGRATION_CLASSES`;
  - `TASK0_MIGRATION_TAXONOMY_V1.json`;
  - `tests/v5/td_unified/test_premerger_migration_task0.py::test_validator_enum_exactly_matches_controlling_migration_taxonomy`.
- **Defect.** Commit chronology:

  | time (EDT) | commit | event |
  |---|---|---|
  | 14:44:53 | `f98f0041` (Task 0) | `HISTORICAL_BIOLOGICAL_EVIDENCE` first enters the validator enum |
  | 15:43:21 | `5b6bf07e` (PR #380 plan) | plan amendment "prospectively add historical biological evidence migration class" |
  | 15:45:03 | `4417949b` (Task 0) | taxonomy JSON created, binding to `5b6bf07e` |

  The amendment is about an hour after the validator extension, and it is not an ancestor of the Task 0 head (Task 0's base is `9328f1c0`). The test compares the validator enum with a JSON file in the same PR, plus a literal head string. It never reads the plan file at the bound commit.

  The content is scientifically fine. The one use, `MACHA_PR314_CORRECTED_REPLAY` with no current authority, is appropriate. The prospective-binding claim is not.
- **Why the tests missed it.** The binding is a string assertion, not a content or ancestry check.
- **Minimal repair.**
  1. Rebase Task 0 onto `5b6bf07e`, or record the amendment commit in its ancestry.
  2. Change the test to read `git show <bound commit>:<amendment path>` (or a vendored copy pinned by blob SHA) and compare its class list with `MIGRATION_CLASSES`.
  3. Label the class `RETROSPECTIVELY_RATIFIED_20261014` in the taxonomy JSON, with the chronology above, rather than "prospective".
- **Scope.** Taxonomy subcomponent only. No reclassification is needed.

### Minor (non-blocking)

- **M1.** F6–F9 enforcement is token-presence in a JSON dump. A token in a negating sentence would pass. Content is correct now; prefer structured boolean states in unified Task 1.
- **M2.** `current_authority` is free text for matrix artifacts and decomposition children. `CURRENT_UNIFIED_SCIENTIFIC_AUTHORITY` is refused only for Macha stream artifacts. Add a global denylist/allowlist.
- **M3.** `mixed_historical_object` is self-declared, so omitting it skips decomposition. This is acceptable with reviewer attestation; consider a reviewer-frozen list of mixed IDs.
- **M4.** History contains probe commits (`x`, `noop`, …) whose files contained only `x`/`noop` and are removed at head. There was no data exposure.
- **M5.** `TASK0_PREMERGER_MIGRATION.exact_head_sha = PENDING_FINAL_TASK0_HEAD` must be bound at freeze.

## C. F-item verdicts

| item | verdict |
|---|---|
| F1 decomposition | **Mechanics accepted.** Each mixed parent has ≥2 children with ≥2 distinct classes; prose-only fails closed. Content for PR #356 is defective (B1); self-declaration caveat M3. |
| F2 exact identity | **Mechanics accepted** (mandatory boolean; deletion fails closed). **Content defective (B2).** |
| F3 dual streams | **Accepted structurally.** Both streams and all eight required artifacts are present, with no promotion. Identity content is covered by B2 and the authority conflict by B3. |
| F4 taxonomy binding | **Not satisfied (B5).** |
| F5 PR #356 merger state | The stop law is **confirmed**: old Task 3 and Task 4 `STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY`; Tasks 5–12 no independent continuation; unified Task 1 not started. Substrate binding and Task 4 destination are defective (B1), and reuse obligations are missing (B4). |
| F6 representation | **Accepted:** `SUBSPACE_ONLY`; T1 coordinates not technology-invariant; axes not promoted; 34/42 identifiability; strong source/acquisition signal kept as a limitation. |
| F7 multimodal | **Accepted:** Stage75F hypothesis-generating only; ATAC independent of RNA-edge circularity; same- versus separate-nucleus distinct; proximity is not target authority; PR #179 `INCOMPLETE_STOPPED` and non-citable; graph negative prior retained. |
| F8 runtime | **Accepted:** optimizer completion before EMA; rejected step cannot advance EMA; typed checkpoint/source provenance; coordinate–value coupling; q-safety not yet executed on the final join; runtime proof ≠ target authority. |
| F9 FULL104 | **Accepted:** denominator/source channel; address parity ≠ evidence parity; zero-fill false ease; explicit noncompensating per-source estimability; within-donor metric blindness; withdrawn finding G not resurrected. |

## D. Old Task 1 — author input and migration-treatment opinion

**Classification `ADAPT_AND_WRAP__DIRECT_REUSE_CANDIDATE_FOR_CANONICAL_PRIMITIVES`: agreed.**

Reusable primitives:
- `canonical_json_bytes`;
- `raw_sha256` and `semantic_sha256`;
- `semantic_text_sha256` and `semantic_json_file_sha256`;
- `ordered_registry_digest`;
- `semantic_row_set_sha256`;
- `load_canonical_json`.

Known-answer digests are frozen, and the docstring is a byte-level specification that an independent reviewer reproduced byte-for-byte.

Adaptations unified Task 1 must decide prospectively:
1. Keep the V1 domain prefixes (`JEPA-PRODUCTION-SYNTHETIC-…-V1`) and wrap them, or re-namespace. Re-namespacing changes every identity and must be a new version.
2. The unified receipt-recursion and authority model is new work.
3. The deferred speed item D2: string escaping is about 9× slower than `json.dumps`. It is safe to optimize under the known-answer tests.

There are no known open defects.

## E. Old Task 2 — author input and migration-treatment opinion

**Classification `ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE`: agreed, conditional on B4.**

Reusable:
- generator freeze with the E1 successor law;
- framed commit/reveal with the precommitment hash;
- the hash-chained ledger with replay validation;
- identity-keyed `derive_stream`;
- per-exposure fit freeze;
- exact realization-set attestation;
- withheld family frozen per lineage, with reveal guards and fail-closed eligibility;
- per-method and lineage draw accounting;
- the secret and nonce absence scanner;
- the unique-withheld-code-path attestation.

Defect: D1, which should be fixed before reuse.

Obligations that must remain external: O1–O8 (B4).

Adaptation: map `SYNTH_DEBUG`/`SYNTH_QUALIFICATION` onto the unified V1.1 sealed development/final challenge vocabulary while keeping the never-`DEV`/`SEALED` naming rule.

## F. GPU/runtime (detected read-only, no compute run)

| item | value |
|---|---|
| GPU | NVIDIA GeForce RTX 3080 Laptop GPU, 16,384 MiB (16.0 GiB), compute capability 8.6 |
| driver | 610.74 (CUDA UMD 13.3) |
| PyTorch | `2.7.0+cu128` (CUDA 12.8, cuDNN 90701), `torch.cuda.is_available() = True`, in env `sea-ad-jepa-v3` |
| Python | 3.11.15 (`sea-ad-jepa-v3`); 3.11.17 (`v79-bayes`, no torch) |
| OS | Windows 11 (10.0.26200); WSL2 Ubuntu running |
| CPU / RAM | Intel i9-11980HK, 16 logical CPUs, 31.8 GiB RAM |
| heavy assets | FULL104 Level-4 block manifest present; foundation metadata SQLite present; FULL104 core sufficient-statistics NPZ present |

Historical capability is not current qualification. Package N must bind this stack at execution time.

## G. No-repeat confirmation

I did not start or continue:
- old Tasks 3–12;
- unified Task 1;
- any re-audit of the settled real-lane gate mechanics (#358–#369);
- the V79 history, the PR #314 replay, or the FULL104 census.

I recomputed nothing and redownloaded nothing. The only reads were:
- the Task 0 bytes and their history;
- the identities of my own historical artifacts, for B2;
- environment detection.

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
