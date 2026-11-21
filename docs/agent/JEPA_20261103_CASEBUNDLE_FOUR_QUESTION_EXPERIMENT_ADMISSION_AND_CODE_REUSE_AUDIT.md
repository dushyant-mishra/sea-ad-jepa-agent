# Scientific experiment admission — recover prior evidence before any new JEPA test

**Date:** 2026-11-03. **Author:** GPT source/audit lane. **Type:** exact-source, no-expression-read decision audit. **Disposition:** `NO_NEW_EXPERIMENT__EXISTING_EVIDENCE_AND_CODE_BOUNDARY_FIRST`. **Scope:** *real source → query-bound CaseBundle* only; not a new target architecture, new QC run or general trainer. **Machine mirror:** `results/target_discovery/unified_qualification_v1/JEPA_PROPOSAL_ADMISSION_CASEBUNDLE_EXISTING_EVIDENCE_V1.json`.

**Mandatory project rule from owner:** “Before proposing an experiment, establish what question remains unanswered, which previous experiments already addressed it, what evidence would change our current conclusion, and whether existing code can execute that test.”

Future proposals in this lane must answer these four questions **with source head and receipt**, followed by `REUSE / STOP / CONCRETE_CODE_GAP / NEW_EXECUTION_IF_JUSTIFIED`. A test that will only regenerate already-known output has no admission. Reusing existing science and accepting a negative result is legitimate progress.

## Question 1 — What specifically is unanswered?

**Not:** “Do our publicly accessible expression datasets exist?” They do. **Not:** “Have we read any real raw counts?” Yes, repeatedly. **Not:** “Can one simulate a CaseBundle?” Yes, already tested. **Not:** “Can a student be fit?” It remains prohibited under current training lock.

**Actual unresolved claim:** Can an **existing source observation** (real cell/query integer count; correct source/operator/donor/row identity; private physical source total; address/alias equivalence; structural measurement versus measured zero versus collision; exactly permitted evidence rights and independently q-excluded public D1) be independently bound, from retained source receipts, into a **versioned real CaseBundle** whose issuer and Task2 access session genuinely authenticated the same data? If no, which minimal trust boundary is missing and is it a *retained-artifact* gap or a *software/authority* gap?

The current evidence does **not establish** that exact real-case issue. That narrow statement does **not imply** the original measurements are missing or that another large read is needed.

## Question 2 — What experiments and implementation already addressed parts of it?

| Original source | Evidence to reuse, not rerun | Limit that still binds |
|---|---|---|
| [#59](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/59) `1bdff2a8...` | **387 actual SHA-checked raw Level4 count blocks**, 8,915 metadata-block SHA checks, 4,553,407 selection rows accounted once, six donors ×17,186 strict-core raw `donor_nnz/umi` integer equality | Output is a donor aggregate, not a source-authenticated per-cell q+physical total CaseBundle; do not misstate 8,915 metadata checks as 8,915 raw count reads |
| [#69](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/69) `83b85382...` | **Corrects FOUR transposed SEAAD/NPH52 source labels** of #59; 33/35 arrays value-identical, six donors unchanged | Prior raw reaggregation explicitly **need not rerun**. Corrected source mapping must be used |
| [#492](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/492) `79d2f936...` | 50k×41,238 expression sample, 246,702,069 nonzero values inverted; source residual breakdown | Sampled expression ≠ complete per-cell q/right/cell custody |
| [#314](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/314) `c6899a29...` | Authorized one-time corrected **real C2 relational replay**, TD56/57B/59 PASS, TD57C FAIL | Spent result; not a CaseBundle issuer and MUST NOT be replicated just to make a source path |
| [#513](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/513) `0b1af4f...`, corrected by [#528](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/528) | Source/QC/alias/rights tables; deposited SEAAD `source_library` equals depositor UMI count for 4,118,213 cells *within same deposit*, 11 active restrictions; original QC receipt already exists | No count matrices were opened by that probe. `sample_id` was per nucleus, **not** specimen; unknown SEAAD query-selection dependence and NPH52 internal hold remain |
| [#505](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/505), [#531](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/531) | Correct structural support vs detection/collision audit; synthetic `VISIBILITY>0` is not source assay presence | No real q/source support selected by synthetic toy |
| [#390](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/390) | Existing Task2 `manifest_v1.py` verifies frozen reader split and harness-owned access session, not simple digest strings | No molecular data issuer/physical read identity comes solely from an access permission |
| [#474](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/474) and independent [#478](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/478) | **Existing query-excluded depth producer**; 60 synthetic worlds and independent off-ledger, q-in-base and richer-level failure counterexamples | Conditional fixture math; q not an API input, off-ledger mass unproven, policy self-supplied. **Must reuse this code**, not create another depth algorithm |
| [#451](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/451), [#469](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/469) | Task5 exact `KNOWN_TRUTH_CASEBUNDLE_V1` fixture-only validator, seven synthetic interop edges already run | No real CaseBundle. `library_size` means physical total in the fixture; q-excluded `base_rights_normalization_depth` is DIFFERENT. Treating one as the other breaks richer-level counts |
| Main `28cbe3b2...` | `observation_d1_base_only_student_v2c_fixture_v1.py` builds q-outside-base student D1 with explicit `base_rights_normalization_depth` and no physical total | It expressly declares source/policy issuer authentication false; not a real authority |
| Main `scripts/v4/f1_real_producer_v1.py` | Existing **real F1 forward** code with external authorization, frozen reader-fit partition and reader/encoder execution | F1 is **not** a V3.1 Task5 CaseBundle issuer. Historic `log1p(c/source_library)` may leak q via denominator when q contributes (#505 *analytic conditional*, not observed real-cell leakage); never repurpose silently |

**Negative historical decisions retained:** PR #336 has already independently audited Phase2 test-of-test, V79 Q08 remains failed, V80 is a benchmark not an estimator, #526 structural support extrapolation withdrawn, #525 Macha reviewer repairs only author-green on newest head, all donor/split/rights gates preserve original nonpromotion. No new experiment can be justified merely by a desire to turn one of these into green.

## Question 3 — What evidence would change the existing conclusion?

The present conclusion is `REAL_CASEBUNDLE_ISSUANCE_NOT_QUALIFIED__SOURCE_DATA_ALREADY_READ`. It changes **only** under one of two pathways:

**A. Retrospective accepted evidence (prefer):** An exact original source and independently reviewed receipt already materialized (or can lawfully derive without opening values) one cell+query raw integer count, the **same** cell's private physical library total, source/block/selection-row identity, true donor/library hierarchy, frozen operator/address 0/1/2 measurement state, alias class/rights, q-outside-base assertion, off-ledger closure or explicit `NOT_ESTIMABLE`, and Task2 authenticated producer-session/parent bytes. Show a separately redacted D1 with stable bytes under wrong/right-query and withheld-mass synthetic adversaries. Then **reuse** it; no new source read.

**B. Exact indispensable missing field (only if A fails):** A reproducible field-coverage audit identifies what was not retained in the historical six-donor aggregate, old 50k sample or source-QC receipts; old data/code cannot derive it without reopening source values. FIRST implement a minimal adapter/receipt validator using existing Task2, #474, main D1 and Task5 interfaces with hostile synthetic tests, and seek independent review. Only then consider the **previously owner-approved one-block maximum** under a new pre-result, source-bound plan, not as an automatic task. A passing test is a *mechanics* result and never a biological target PASS.

**Falsifiers of the proposed real producer:** hidden q changes D1, query is assigned BASE right, off-ledger q molecule changes base normalization, alias copies leak a withheld gene, measured zero becomes structural absence, collision turns into scalar zero, repeated cell/group or swapped donor/source passes, fake producer access receipt or post-hoc policy passes, `physical_library_total` appears in any student artifact, or a richer teacher count is rejected because code falsely equates it with student base depth. Any one forces `STOP/NOT_ESTIMABLE`; no average metric can compensate.

**What would NOT change scientific conclusion:** re-running PR #59 donor aggregation, repeating 50k sample, copying #474 conditional math with caller-supplied hashes, a fixture CI PASS, self-declared signed-looking strings, selecting a convenient high-expression block, or an encouraging R² from any new fit before the source is admitted.

## Question 4 — Can existing code execute the decisive test?

**Partial YES, real end-to-end NO at reviewed heads:**

- **Already executable:** Original Level4 physical count reader (already executed PR59), corrected source metadata (PR69), Stage81A2R/A3R operator support, Task2 donor/reader/session gate ([#390](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/390), `manifest_v1.py` Git blob `b66b2cc0...`), PR474 fixture rights-ladder/depth function (blob `449b50a6...`), main D1 fixture (blob `edee1b8a...`), PR451 fixture CaseBundle (blob `23bbdcfc...`), PR469 seven-edge synthetic bridge. These are **components to reuse**, not new packages to reinvent.
- **Existing independently documented inability:** PR478 [review](https://github.com/dushyant-mishra/sea-ad-jepa-agent/blob/b7aa56e2915d2af7dd733f0f0253e684164ce70a/docs/agent/JEPA_PR474_INDEPENDENT_Q_EXCLUDED_DEPTH_REVIEW_20261027.md) explicitly shows conditional q-excluded total can leak off-ledger molecules, the producer cannot reject q assigned BASE because q is not an input, and richer teacher counts can be larger than D1 depth, violating legacy CaseBundle's `count <= library_size`.
- **Exact remaining interface gap:** no accepted source-issued **real** CaseBundle tying the *same* authentic per-cell source q value to private total, operator/alias/rights, Task2 session and publicly redacted D1 under a correct **two-depth schema**. Existing donor aggregate, QC table, F1 forward generator and synthetic bridge do **not** supply this by name alone. Searched source set is main + accepted/targeted PR59/69/390/451/469/474/478/492/505/513/528/531; not a claim of 824 exhaustive code audits. Check latest accepted producer before proposing code.
- **Executable next work:** read-free, input/receipt-only field-coverage verification; if no adequate old provenance record, **minimal nonexperimental contract/adapter fixture test**, authored as a narrow versioned successor **only after** review. No new biology experiment is admitted yet.

## Field-level coverage classification and its limits

See machine mirror for all **14** fields. Summary:

| Field | Current verdict | Reason |
|---|---|---|
| Old Level4 count-block custody; cell/donor/source metadata | `EXISTING_PHYSICALLY_EVIDENCED` | PR59 physical raw count read / metadata; PR69 corrected source IDs |
| Private per-cell physical library total, operator support, alias rights, Task2 policy, fixture q/depth code | `PRESENT_BUT_UNQUALIFIED` | Separate records exist but **same-source exact q/per-cell binding** not independently authenticated |
| Per-cell source q count in an old independently bound receipt; real CaseBundle issue | `NOT_RETAINED_IN_OLD_RECEIPT` | Old reads produced aggregates and fixtures, no accepted joined case |
| Off-ledger hidden-q molecule completeness and depositor query-independent selection | `NOT_ESTIMABLE` | PR478 counterexample and PR513 selection/alias caveats; need source law or fail-closed receipt |

No status here claims the physical data are absent or Macha must re-ETL anything. They specify what the **reviewed persisted receipts** establish.

## Decision and next action for the successor

**Decision:** `NO_NEW_EXPERIMENT__REUSE_EXISTING_EVIDENCE_AND_CODE_FIRST`. The 2026-11-03 owner-delegated QC allowlist remains a limited policy approval. The **single SEAAD block permission is a maximum conditional scope**, superseded as an immediate task by recovered PR59 and PR69. **No new block, no count matrix, no QC replay, no synthetic world, no fit, no training** is assigned.

**First concrete deliverable, before writing new code:** an exact-head source-field→existing-artifact→consumer-obligation matrix, identifying any accepted new real producer. If a field is retained, no new read is lawful merely for convenience. If a field is not retained, articulate the minimal unavailable trust proof and the existing interfaces it must bind; request independent review of any truly novel test. This document itself contains **no experimental authorization**.

**Global lock:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
