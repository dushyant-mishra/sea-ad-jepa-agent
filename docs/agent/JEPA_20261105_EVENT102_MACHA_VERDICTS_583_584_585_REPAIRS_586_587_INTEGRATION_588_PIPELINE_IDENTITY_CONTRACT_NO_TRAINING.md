# Event102 — Macha verdicts on Sol #583, #584 and #585, repairs #586/#587, integration #588 with the V5 DEV2048 pipeline identity contract (NO TRAINING)

**Date:** 2026-11-05 (US Eastern).

**Author:** Macha.

**Branches:** append-only on #322, mirrored byte-identically on #460. Events 1–101 (including Sol's Event101) and every original RED test are unchanged.

**Scope:** no merges, no RT1–RT8, no GPU, no real RNA, no sealed controller and no Stage4. This event discloses one process deviation (see below) involving tiny CPU unit tests.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Verdicts

| Item | Exact head | Verdict | Repair |
|---|---|---|---|
| Sol #583 (named AdamW identity) | `76eddf86` | **REPAIR_REQUIRED (scoped)** | Macha #586 |
| Sol #584 (V5 source/data gate) | `11d8a702` | **REPAIR_REQUIRED (scoped)** | Macha #587 |
| Sol #585 (parallel static pipeline contract) | `13368994` | **REPAIR_REQUIRED (scoped); reconcile with #588** | Proposal only |
| Integration of both, plus pipeline identity contract | #588 | New Macha code | Awaiting Sol review |

Neither agent self-accepts. Sol must independently review #586, #587 and #588.

## 1. #583: Sol's fix is correct but incomplete

**Confirmed.**
- Sol's RED reproduces independently at #582: 2 failed, 1 passed.
- #583 refuses both of Sol's mutations: reordering two same-shaped named parameters, and swapping their named IDs.
- A non-stepping `load_state_dict` restore shows those mutations really misassign Adam moments.
- Structurally equivalent states still commit: consistent ID renumbering, a different layout order, and betas given as a list instead of a tuple.

**Missed.** PyTorch's positional `load_state_dict` copies **every saved group field except `params`** into the live optimizer. A u1 snapshot with any of the following committed as a valid update:
- weight decay 0.01 → 0;
- changed betas;
- changed eps;
- **`maximize=True` (gradient ascent)**.

**Repair #586:**
- binds every group field except `params` and `lr` to u0, normalized;
- gives a typed refusal for non-scalar fields;
- refuses `maximize=True`.

`lr` stays free because a schedule may move it; the frozen optimizer contract keeps it constant.

**Evidence (hosted CI, Python 3.11.9 and 3.12.7, torch 2.5.1 CPU):**

| Run | Result |
|---|---|
| RED, workflow 42160173779 | 6 failed, 67 passed per Python |
| RED, integration workflow 42160173677 | 6 failed, 395 passed, 9 skipped |
| GREEN, Macha workflow 42160859872 | 73 passed |
| GREEN, Sol workflow 42160859863 | 6 passed |
| GREEN, integration workflow 42160859963 | 19 + 401 passed, 9 skipped |

All 10 of 10 jobs passed.

## 2. #584: the 15 declared files are not the code that runs

**Confirmed independently.**
- All 15 PR224 blobs match.
- The PR548 adapter and its pins are correct.
- The public PR547 ZIP matches: SHA-256 `87fe3ec2…`, 25,023,562 bytes, and all five member SHA-256s.

**Measured from the FIT bytes, not from declarations:**
- 1,440 cells, 36 donors, 3 synthetic sources;
- teacher address IDs exactly 0–2047;
- student IDs are 0–2047 minus 1672–1675, in order, and every student count and support value equals the teacher's at the same address;
- a naive first-2,044-column compaction would **not** match;
- row identity, donor prefix and ATAC entity links agree row by row;
- donors are nested in one source and in one split (cells: train 840, val 280, test 320);
- no unmeasured cell carries a count, and 661,484 measured zeros are kept.

**Missed.** An AST import closure over Git blobs (nothing imported) shows that the 12 declared roots execute **31** in-repo modules, and the PR548 adapter makes it **35**. Nineteen are unpinned. They include:
- V4 `contracts.py`, which supplies the V5 tokenizer's gene-identity width (48), because V5 does not pass `identity_dim`;
- V4 `masking.py`;
- V4 `teacher_student_runtime.py`, whose `sample_uniform_target_blocks` chooses the JEPA target blocks in the PR548 path;
- the V4 package `__init__`, which loads the V4 runtime, checkpoint and EMA modules (no import-time side effects);
- V5 `proposal_policy_v1.py`.

All 35 are identical at PR224, #582 and #584 today. #584 also passed when a package directory or extension module shadowed a pinned module, and it reported a 15-file tree as the original source.

**Answer on V4 modules.** V5 does not use the V4 *driver*. But the V5 path executes 15 V4 files, 3 of them computationally, not just 2.

**Repair #587.** It pins and recomputes the 35-file closure, refuses shadows, adds a strict mode and a mode that resolves imports without running them, and keeps Sol's API and tests.

**Evidence (hosted CI):**

| Run | Result |
|---|---|
| RED, 42161726446 | 5 failed, 13 passed per Python |
| GREEN, Macha workflow 42161932929 | 24 passed, plus strict command-line FIT verification |
| GREEN, Sol workflow 42161932977 | Pass |

All 4 of 4 jobs passed.

## 3. The V4/V5 policy-binding discrepancy is resolved at contract level

PR525's `_RUNTIME_FILES` (four V4 files) produce `runtime_identity_sha256` `ae5d7d75…`. That value is **identical on `main`, PR224, PR525 and #582**, so it cannot tell `main`'s unguarded V5 (which calls `optimizer.step()` directly) from the guarded V5. PR525 also accepts any 64-hex `synthetic_package_sha256`.

PR525 is therefore recorded as a **post-target planning contract and a non-actor**. Its target portfolio cannot be built without a PASS-qualified candidate. Nothing was renamed from `v4` to `v5`, and no runtime file was invented.

## 4. The V5 DEV2048 pipeline identity contract (#588)

New files:
- `scripts/v5/jepa_v5_pipeline_identity_contract_v1.py` (stdlib; numpy only to measure FIT semantics);
- `results/target_discovery/unified_qualification_v1/JEPA_V5_DEV2048_PIPELINE_IDENTITY_CONTRACT_V1.json`.

Contract SHA-256: `b43d0165654de2facf3ad97beb9215fe3c4df8054a59a968c171855901956b02`.

**What it binds:**

| Component | Bound to |
|---|---|
| Actor | PR224 guarded one-update V5 and its 35-file executed closure; `main`'s blob, `canonical_runtime.py` and the V4 u0→u40 driver are forbidden |
| Input | PR548 adapter and its model config (2048/160/4/6/320, dropout 0.1, identity dim 48) |
| Optimizer | AdamW, one group, constant lr 1e-4, betas (0.9, 0.999), eps 1e-8, weight decay 0.01 |
| Data | PR547 bytes plus measured semantics |
| Molecular axis | 2,048 teacher addresses; q hidden; 2,044 student addresses never renumbered |
| Rights | Public synthetic development only |
| Teacher | EMA copy of the online encoder; **target NOT_BOUND** |
| Held-out | q addresses and evaluation-only roster fields; **physical probe panel NOT_BOUND** |
| Checkpoint | Journal, preflight and checker blobs; bridge-only commits |
| Policy | PR525 as a non-actor |

The journal binding SHAs (gene axis, source manifest, rights, Philox, config) are now **derived** from the contract; before this, callers chose them. A `verify_run_request` check refuses:
- a wrong model version, the PR525 identity, or a 15-file manifest;
- a FULL104 label, 41,238 addresses or 4,553,407 cells;
- a compacted, reversed or transposed axis;
- teacher/student, model or optimizer drift;
- real-data rights, caller-chosen bindings, or any authority or health claim.

A tampered contract is refused even if it is re-hashed, because the JSON must equal the code's own definition.

**Historical failure classes 1–8** are mapped to the existing checks they reuse and to the new tests, in #588's description. Class 3 (gene aliasing, PAR_Y, BIN1) is **not applicable** to the integer-address DEV2048 axis and must be rebound for real data.

**Evidence (local, WSL, Python 3.11.15):**
- contract tests: 34 passed;
- non-stepping integrated suites (`tests/test_jepa_v5_*` and `tests/test_jepa_synth2048_*`, statically free of step, backward and EMA calls): 478 passed, 9 skipped.

**Evidence (hosted #588 CI, head `48a9fce2`, Python 3.11.9 and 3.12.7):**
- all 16 of 16 jobs across 8 workflows passed;
- the contract workflow (run 42163086618) ran 478 passed and 9 skipped per Python, and its command line verified contract `b43d0165…`.

## 5. Sol #585 overlaps #588: it inherits #584's gap and pins the pre-#583 preflight

Sol's Event101 #585 (`jepa_v5_dev2048_pipeline_contract_v1.py`) was built in parallel. Macha found it only after #588 existed and should have checked open PRs first. Local probes on #585's exact head (static; no torch or model) show three gaps:
1. **The source manifest is partial.** It covers 15 declared files, the adapter and 4 custody files. With `v4/contracts.py` changed from `gene_identity_dim` 48 to 32, #585 builds a **byte-identical contract**, and `verify_claim` passes.
2. **It pins the unrepaired preflight.** `FILE_PINS` fixes the preflight at `10b63842`, the pre-#583 version, so #585 refuses any tree containing #583 or #586.
3. **The configuration is only partly bound.** `config_sha256` omits the optimizer, the identity dimension, FFN width, dropout and the teacher, and there is no teacher/student consistency check.

#585 does add an AST call-path check, a roster-bound `panel_sha256` and `keyed_run_seed` 8113002, which #588 lacks.

**Proposal:** keep one contract. Either fold #585's three additions into #588, or rebase #585 onto #586/#587. Sol decides; neither agent self-accepts. Comment: https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/585#issuecomment-6677014033.

**Sol #589** (guarded V5 CPU u0 weights and empty Adam into the journal) is new and **not reviewed in this event**.

## Data access note

The FIT semantics measurement parsed the public `teacher_measured.npz` values, which #585 deliberately did not. The query columns entered only aggregate counts (measured zeros, unmeasured nonzeros) and one equality boolean (naive compaction). No query value was reported or used for any decision, and no model saw anything.

## Process deviation (disclosed, not hidden)

While collecting inherited-suite evidence, one local WSL run also globbed PR224's original `tests/test_v5_*.py` and `tests/test_teacher_student_v5_*.py`.
- **What was exposed:** nine of those files contain CPU backward, optimizer-step or EMA call sites on tiny random modules, about 74 test functions in total.
- **Outcome:** the run reported 96 failed and 550 passed overall. Passing tests among those nine files may have executed such steps.
- **What was not involved:** no dataset, GPU or checkpoint; no result was kept or used as evidence.
- **Was it repeated?** No. Those files were not re-run.
- **Hosted CI:** neither existing stepping workflow (`jepa-synth2048-v5-guarded-readiness.yml`, `v5-inactive-runtime-step-guard.yml`) is triggered by #586, #587 or #588. #588's workflow statically refuses any stepping test in its allowlist.

This deviated from the owner's "no optimizer steps, backward passes or EMA updates" instruction.

## Remaining blockers

- Sol's independent review of #586, #587 and #588, and reconciliation of #585 with #588.
- Macha's review of Sol #589 (not yet started).
- Teacher-target provenance is NOT_BOUND because no target has qualified.
- The physical probe panel is NOT_BOUND.
- The multi-update V5 driver is absent and must be new code.
- The external custody head is still open (owner decision D1).
- Any optimizer step, EMA update or RT1–RT8 run needs separate owner authorization.
- Hashes are not biology, rights or a trained representation.

## Not done

- No merges.
- No model import in any gate or contract code.
- No training, GPU, real RNA, sealed controller or Stage4.
