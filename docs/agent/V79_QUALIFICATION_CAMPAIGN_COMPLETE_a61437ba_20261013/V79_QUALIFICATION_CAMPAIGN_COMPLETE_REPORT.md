# V79 V2_CORE Q00–Q11 qualification campaign: COMPLETE, 1,056/1,056 fits, campaign receipt produced by the runner

**Date:** 2026-10-13 (UTC).

**Authority:**
- PR #317 comment `6137248929` covered the first world (88 fits).
- PR #317 comment `6146378159` covered the continuation (records 89–1056).
- One campaign, at the repaired head `a61437ba284e9e75b0557157ad68e56eacd8f8fe`.

**Terminal:**
`V2_CORE_QUALIFICATION_CAMPAIGN_COMPLETE__1056_OF_1056__CAMPAIGN_RECEIPT_A0065925__1053_COMPLETE_3_NOT_DIAGNOSED__STOPPED_BEFORE_SCORING__TRUTH_CLOSED__TRAINING_OFF__CONTROLLER_AUDIT_REQUIRED`

## 1. Required completion report

| item | value |
|---|---|
| exact code head | `a61437ba284e9e75b0557157ad68e56eacd8f8fe`. Fresh detached checkout, clean before, during and after; no ignored files. |
| runtime | Lock `5253ddca79c5…`, 31/31 packages, Windows, Python 3.11.17 (`v79-bayes`). Validated before world 1 and again before the continuation. |
| machine authorization | `a3b79d537619615ef6b14fd983af07ed4622f964c1b479eca24ed6ae6fc2fc4a` (controller side). 1,056-record ledger from the frozen `build_seed_ledger`. |
| custody receipt SHA-256 | **`c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63`**. Unchanged throughout; all 148 custody files and the controller authorization match the run-time ledger. |
| **campaign receipt SHA-256** | **`a0065925789c58409a85ccbf72d24f5c7b1be142a4d17eddc434babdf0d0e340`** (250,641 bytes). Written by the runner after all 1,056 receipts validated, and byte-identical to my independent deterministic reconstruction. It records `code_sha` a61437ba, `custody_receipt_sha256` c5116d62, `planned_fit_count` 1056, `qualification_fits_run` 1056, and `benchmark_run`, `scoring_run`, `truth_accessed`, `training_authorized` all false. |
| valid contiguous prefix | The runner's frozen `completed_prefix(...)` returns **1056 of 1056**, with code-SHA and seed validation of every receipt. |
| each planned fit exactly once | All 1,056 fit IDs equal the authority ledger, and each appears exactly once. Receipts match the frozen queue's order and identities (opaque world, gene, part). |
| seeds | Every attempt's seed equals the authority-ledger seed. |
| first 88 (world 1) | Not rerun. All 176 accepted files are byte-identical to the world-1 ledger. |
| **COMPLETE / NOT_DIAGNOSED** | **1053 / 3**. Detection: 528 COMPLETE. Positive: 525 COMPLETE, 3 NOT_DIAGNOSED. |
| recovery paths | PRIMARY only 1027; PRIMARY+EXTENSION 14; PRIMARY+ESCALATION 12; PRIMARY+ESCALATION+EXTENSION 3. |
| stage use | PRIMARY 1056, ESCALATION 15, EXTENSION 17 |
| divergences | 55 in final diagnostics; 567 across all attempts. 15 fits had any divergence. |
| worst R-hat / bulk ESS / tail ESS | **1.03 / 253 / 425**, final diagnostics over all 1,056 fits including NOT_DIAGNOSED |
| mean tree steps | 15.0–511.0 by fit |
| frozen Q00–Q11 package | Still 498/498 files byte-identical to ledger `4e65f213…` after the campaign. Root `84949723`, digest `40458efe`, index `8ea3e0cb`. |
| flags on every fit receipt | `execution_mode` QUALIFICATION; `benchmark_run` false; `qualification_fits_run` 1; **`scoring_run` false; `truth_accessed` false; `training_authorized` false**. `code_sha` a61437ba; contract `57e19295`. |

## 2. Where the NOT_DIAGNOSED fits, recovery and divergences sit (descriptive; nothing interpreted)

**The three NOT_DIAGNOSED fits** are all in opaque world **`ee384a29a9fc`**, all positive part:

| gene | stages |
|---|---|
| 2 | PRIMARY+ESCALATION |
| 13 | PRIMARY+ESCALATION |
| 43 | PRIMARY+ESCALATION+EXTENSION |

They are preserved exactly as the frozen recovery path terminated them. None was re-run or relabelled.

**World `ee384a29a9fc`:**
- 85 COMPLETE, 3 NOT_DIAGNOSED.
- 16 of its 88 fits used a non-primary recovery path.
- It holds **all 567 attempt divergences** in the campaign.
- Worst R-hat 1.03, worst bulk ESS 253.

**The other 11 worlds:**
- 0 divergences.
- 0 NOT_DIAGNOSED.
- 13 fits used a non-primary path (escalation or extension) and all ended COMPLETE.
- Worst R-hat 1.01.

Opaque world IDs were not mapped to Q labels, controller truth was not opened, and nothing was compared against planted values. What this pattern means is a matter for scoring, under separate authority. Per-world detail is in
`record/CAMPAIGN_DIAGNOSTICS_SUMMARY.json` and per-fit detail in `record/PER_FIT_DIAGNOSTICS.csv`.

## 3. Runtime and resources

**Execution windows.** World 1 ran 03:20:11Z → 03:55:34Z (2,123 s). The continuation ran 13:33:36Z → 19:15:20Z
(20,504 s), which includes the frozen 120 s settle between worlds.

**Total execution: 22,627 s = 6.29 h**, against the frozen 72 h ceiling. The benchmark-formula projection was 1.52 h,
and the world-1 extrapolation 7.48 h.

**Per-world time** from first fit start to last fit end: 1,538–2,195 s.

| measure | value |
|---|---|
| sampling wall per fit | mean 3.42 s, median 3.27 s, max 9.59 s; total 3,612 s |
| process CPU per fit | mean 3.47 s, max 9.56 s |
| peak working set | max 1,392,254,976 bytes, median 1,092,919,296 bytes |

As found in world 1, most wall time is the per-fit post-sampling work: posterior predictive checks, the held-out
predictive summaries and the identified summaries.

**Machine load.**
- During the continuation, machine CPU averaged 31.9% and peaked at 55.2% over 340 one-minute `typeperf` samples.
- Background load at launch was Docker, Task Manager and a remote-desktop host, about 1.6 cores.
- During world 1, a user Chrome process was running.
- **The authorized TD synthetic phase-1 blinded fit** (a separate lane) ran 62 s of CPU concurrently, 17:52:40Z →
  17:53:42Z.

None of this changes frozen inference semantics. Contention affects timing only.

## 4. Confirmations

- **No world regeneration and no frozen byte modified.** The package was verified 498/498 before and after.
- **No seed modification.** All attempts match the authority ledger.
- **No setting changes and no tuning.** Sampler, prior, threshold, model and recovery settings were unchanged.
- **No selective, manual or repeated runs.**
  - World 1 ran once.
  - The continuation ran once.
  - The first 88 were validated and skipped by the runner.
  - Nothing was deleted or repaired.
- **No scoring.** I ran no PR #306 scorer and no 292-gate evaluation, and produced no qualification PASS/FAIL.
- **No truth opening.** No controller truth was opened, and no opaque ID was mapped to a Q label.
- **No training.**

## 5. Evidence

**This directory (all copies byte-exact; see `SOURCE_SHA256.txt`):**
- **`receipts/`**:
  - **the campaign receipt** (`a0065925…`);
  - the custody receipt;
  - the sanitized and controller-side authorizations;
  - the fit contract view.
- **`record/`** (continuation records):
  - `PRE_RESUME_*`;
  - `run_continuation.sh`, `CAMPAIGN_RUN_RECORD.txt`, `CAMPAIGN_STDOUT_invocation1.json`, `CAMPAIGN_STDERR_invocation1.txt` (empty);
  - `MACHINE_CPU_TYPEPERF_invocation1.csv`, `CONTENTION_CHECK.txt`;
  - `COMPLETION_VERIFICATION.json`, `CAMPAIGN_DIAGNOSTICS_SUMMARY.json`, `PER_FIT_DIAGNOSTICS.csv`;
  - `POST_CAMPAIGN_CHECKS.txt`;
  - **`RESULT_FILE_LEDGER_SHA256.txt`**.
- **`RESULT_FILE_LEDGER_SHA256.txt`** (SHA-256 `d467bb9b51336278ee46566173148a4f112eaa79cf578b8bbfae502cb4388b89`): path, size and SHA-256 for all **2,113** result files (193,904,663 bytes): 1,056 fit receipts, 1,056 donor-draw files and the campaign receipt.

**On the execution storage, referenced by the ledger.** The 1,056 fit receipts (about 68 MB) and 1,056 donor-draw
NPZ files (about 126 MB) are too large to commit as loose files. Their original bytes remain at
`D:/jepa_v79_qualification_world1_a61437ba/result/`. None is omitted: each is authenticated by the ledger and by the
campaign receipt, which lists every fit receipt's SHA-256.

**Earlier evidence:**
- The world-1 records and its 88 receipts are already on `evidence/v79-qualification-world1-a61437ba-20261013` @ `b0ccae06`.
- The spent `559a1c10` attempt is on `evidence/v79-qualification-campaign-attempt-559a1c10-20261013` @ `3af9e1b4`.

STOP before scoring or truth opening. Controller audit required.
