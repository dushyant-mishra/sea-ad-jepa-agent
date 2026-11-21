# CURRENT ADDENDUM — MACHA EVENT58 AND PR460 RECOVERY

Before using the rest of this handoff, also read:
`docs/agent/JEPA_MACHA_LANE_STATE_FOR_SOL_20261104.md`.

That file is Macha's complete self-account for 2026-11-02 through 2026-11-04 and controls over older summaries of Macha's own work. It records exact heads, CI, verdicts, seven retracted/overstated claims, and his actual remaining queue.

### Seven Macha claims that must not be propagated

1. NPH52 accession/terms were not unknown: Zenodo 8319719 rev2, CC-BY-4.0.
2. Hardware/offline signing key is optional governance hardening, not a prerequisite.
3. PR #336 already independently audited the Phase-2 9/9 receipt.
4. Synthetic-vs-real source geometry was not simply reversed; the real defect is support semantics and NPH52 gaps.
5. The owner alias-right decision was already made; enforcement code is the missing piece.
6. Level-4 count reads were already done in PR59/69; do not claim none existed.
7. Macha disclosed one 11-03 replay of the #513 QC probe before adjudication; output was byte-identical and the subsequent hold is enforced in code.

### Macha's actual open queue

- Independent fresh-head review of PR #525 at `b493efc35af20bcf2adee29c47376e1dbf4b6dcd`.
- No-read challenge of PR #535 field classifications.
- PR #537 GPU run is **not authorized**. Macha will only execute it with explicit owner authorization. The current owner/audit decision remains HOLD/nonduplication-first.
- PR #536 review only if specifically requested.

Do not turn this queue into automatic assignments. Check whether a later comment/branch has already completed an item before assigning it.

### PR #460 branch incident

Macha accidentally deleted the #460 branch while attempting to post a pointer, immediately restored it to exact prior commit `d5732fe690dc3a6ef89ebaaaf25c98d23fa65493`, but GitHub auto-closed the PR. GPT/Sol reopened PR #460 without changing its restored content. This incident caused no content loss.

Macha also repaired the #322 chronology source-availability failure by adding the two event57-cited Macha documents byte-identically to #322. Treat the event58 branch/account as the correction source for that custody issue.

---

# JEPA GPT lane complete cold-start takeover and no-repeat handoff — 2026-11-04

**Purpose:** allow a future GPT/agent to continue the JEPA target-discovery/downstream lane without recrawling the project, repeating already executed science, re-running source ETL, or rediscovering Macha/Claude review work.

**Authority remains:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

This document is a navigation/custody handoff. It does not promote any biological result, target, representation, source issuer or training authority.

## 1. Repository custody model

Three layers must remain separate:

1. **`main`** — accepted/scoped production code and historical project state. Do not assume every open audit/repair PR is merged.
2. **PR #322** / branch `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013` — canonical append-only science, engineering, review, source/data and chronology audit. This is the permanent historical truth surface.
3. **PR #460** / branch `handoff/jepa-v8-clean-successor-from-audit-20261027` — active operational cold-start pointer for the next agent. It must always point back to the current #322 audit state.

Do not create another narrative-only historical consolidation PR. New implementation belongs on a focused branch/PR; after substantive work, append an audit event to #322 and update #460.

## 2. Mandatory first-read order

A future agent should read these before proposing work:

1. `docs/agent/JEPA_20261104_END_TO_END_SCIENTIFIC_NARRATIVE_AND_DECISION_LINEAGE_V1.md`
   - complete biological story from AD microglia/pathology through graph/rare/regulatory/ATAC/SCENIC+/perturbation/spatial evidence, heterogeneous foundation, teacher/student information limits and C1/C2/C3/C6/C4+C5 target lattice.
2. `results/target_discovery/unified_qualification_v1/JEPA_20261104_MASTER_PRIMARY_SOURCE_NO_REPEAT_INDEX_V1.json`
   - machine no-repeat/source index and current decision corrections.
3. `results/target_discovery/unified_qualification_v1/JEPA_CONTINUOUS_CHRONOLOGY_PROGRESS_V1.json`
   - append-only chronology; events 1–57 at creation of this handoff.
4. `docs/agent/JEPA_20261104_RECENT_TWO_WEEK_SCIENCE_RESOLUTIONS_AND_CORRECTED_NEXT_WORK_V1.md`
   - late-result precedence that retires stale next tasks.
5. `docs/agent/JEPA_20261104_ITERATIVE_PROJECT_WIDE_HISTORY_SATURATION_AND_NEXT_FRONTIER_V1.md`
   - project-wide saturation audit and recovered underindexed science.
6. `docs/agent/JEPA_20261104_LEARNED_STUDENT_BIOLOGICAL_GAP_READONLY_DECISION_V1.md`
   - the narrow unestablished learned-teacher/student biology claim after removing completed work.
7. `results/target_discovery/unified_qualification_v1/JEPA_20261104_PROJECT_LOCAL_ASSET_SHA256_CUSTODY_V1.json`
   - hashes/roles for large uploaded/local artifacts that must not be duplicated into Git.
8. PR #460 `docs/agent/JEPA_NEW_AGENT_LIVE_POINTER_20261029.md`
   - current operational pointer; read the newest top block first.

Only use older handoffs for provenance after these files.

## 3. Original scientific objective

The project is not “train a JEPA” as an end in itself. The biological objective is to learn transferable human brain-cell state representations—initially AD-associated microglia—that connect RNA state to pathology and then to independent regulatory/chromatin/perturbational/spatial evidence and testable mechanistic hypotheses.

The claim ladder remains:

`RNA_REPRESENTATION -> TRANSFERABLE_BIOLOGICAL_STATE -> REGULATORY_SUPPORT -> CAUSAL_PERTURBATIONAL_PREDICTION`

Each arrow requires separate evidence.

## 4. Closed or bounded science that must not be repeated by default

The following are historical evidence, not missing work:

- V1 pathology-aware flat RNA-JEPA and pathology prediction.
- V2/V3 Graph-JEPA, including collapse/tube diagnosis and graph-specificity rules.
- Stage53–70 rare microglia work, including Stage69 positive scoped auxiliary and later graph negatives.
- Stage36–49 AD knowledge/gene/PI work: 103 resources, 770 annotations, 18 traceable genes / four mechanisms.
- Stage72–75F RNA/ATAC/SCENIC+/motif work and Tier A/B/C regulator evidence.
- Original Stage76–79 frozen GeneJEPA perturbation/control mechanics and 152 graph variants.
- Physical CRISPR/bulk clone-aware work and CRISPRbrain negative eligibility.
- Public E2G seven-track survey.
- Spatial Slide-tags/MERFISH/UCDQ provenance and context work.
- Stage81A2/A2R 41,238-address molecular ledger and 42 observation operators.
- Historical 4,096-vocab experiments, 160/224/320/etc. provisional widths; none is a production representation winner.
- PR59 physical Level-4 reads: 387 count blocks plus metadata accounting; PR69 source-label repair without repeating reads.
- FULL104 / D_shared-private-observation design and support-count shortcut diagnosis.
- Original Stage81A3 planted-factor training negatives.
- Original six-IPB 500-step feasibility study:
  - `scripts/v4/stage81a3_ipb_jepa_feasibility.py`
  - `results/v4/stage81a3_ipb_jepa_feasibility.json`
  - frozen receipt SHA `aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308`
- Stage81B JEPA_ONLY/CURRENT/ANCHOR_ONLY causal comparison; anchor was harmful. Do not treat PR537 as automatically novel.
- T0/T1/TCTX short target tests; no winner.
- Original donor-heldout R5 q-aware measured target result; q-aware ~0.4300, technical+q ~0.3496, q-agnostic ~0.2760.
- V44 teacher topology comparison.
- V65/V67 shared/private planted recovery controls.
- TD19 depth-only falsification, TD56/57B/59 measured relational recurrence, corrected spent real replay PR #314.
- PR #336 independent 9/9 Phase-2 known-truth/test-of-test audit.
- PR #328 unified synthetic world, PR #469 source-observation→Task5 integration, PR #526/#531 measurement/support audit, PR #536 actual C3 measured producer and C2 48→512 refusal.
- V79 terminal Q00–Q11 campaign: `NOT_QUALIFIED`, Q08 hard failure.
- V80 eight-world benchmark/custody package: benchmark qualification only; no estimator winner.
- Main D1/V2C/student container scoped path #522–#524 and associated hostile review.
- Macha source/ETL reuse, source qualification and post-TD bridge reviews.
- Earlier G7 run: one-run `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`; do not rerun as if missing.
- S174 masked physical development replay PR #288; do not rerun.

A rerun requires at least one of: a pinned source changed; a new independent executable contradiction exists; new authenticated data changes an unavailable fact; or the scientific question is prospectively different.

## 5. Candidate and representation spaces

Do not collapse target discovery to C2 vs C3.

Foundation/target candidates:
- C1 shared emergent
- C2 relational shared
- C3 query-conditioned measured
- C6 shared + query composite = C1 + C3
- C4 structured composite = C2 + C3, with independent C6 prerequisite/comparator
- C5 regulatory specialist, separate from foundation rescue

Representation families remain separately unresolved:
- global cell
- gene/query-local
- program
- structured

No target winner and no representation winner are established.

## 6. Data, source and large-artifact custody

Do not redownload or Git-duplicate large project data.

Canonical local/upload custody is indexed in:
`results/target_discovery/unified_qualification_v1/JEPA_20261104_PROJECT_LOCAL_ASSET_SHA256_CUSTODY_V1.json`.

Important frozen artifacts include:
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- multipart `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001/.part002` plus checksum CSV
- `expression.zip`
- `checkpoints.zip`
- `t1_checkpoint_u0200.zip`
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
- historical text notes `WSL execution issue.txt`, `Status and Repair Plan.txt`, prior pasted historical notes

Macha/GPU laptop owns physical execution and large-data access. GPT owns scientific synthesis, architecture, implementation, GitHub custody and reciprocal review. Neither agent accepts the other's result without challenge.

Public-source access already established within scope:
- SEA-AD processed releases
- HVS CELLxGENE collection
- NPH52 Zenodo 8319719 rev 2, open/CC-BY-4.0

Public accessibility is not scientific qualification or query issuance.

## 7. Source / CaseBundle / QC decisions

Current owner rulings are chronology event57:

1. **QC-only allowlist APPROVED** for:
   - SEA-AD `Doublet score`
   - HVS `is_primary_data`
   Use only for versioned QC/provenance eligibility. Never use as pathology, target, expression feature, teacher/student input or donor/specimen surrogate.

2. **No new Level-4 count→real CaseBundle read now.**
   Historical PR59/69 reads and receipts must be reused. A future read requires one exact frozen decision-bearing experiment and q/alias/selection/source rights bound first.

3. **PR #531 five-rule support-semantics amendment accepted as a future prerequisite**, but no corrected synthetic world, fit or training is authorized now.
   Keep structural absence, measured zero, detection probability, collision-unresolved state and rights withholding distinct.

The prior immediate-read / immediate-new-world request is superseded.

## 8. Synthetic pipeline and real-pipeline integration

Do not build a new generator by default.

Key reusable implementation/results:
- PR #328 exact frozen synthetic world:
  - `scripts/v79/unified_synthetic_integration_v1.py`
  - `scripts/v79/unified_synthetic_fit_view_v1.py`
  - `scripts/v79/unified_synthetic_controller_truth_v1.py`
  - `results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2.json`
- PR #318 relational known-truth/null/technical-twin package.
- PR #369 cross-gate sealed battery after hostile repairs.
- PR #451 post-TD bridge repair/review lineage.
- PR #469 PR328 observations → existing Task5 fixture integration.
- PR #526:
  - `scripts/v79/audit_frozen_measured_panel_observability_v1.py`
  - `results/v79/unified_synthetic/JEPA_FROZEN_Q_OTHER_8_MEASUREMENT_REUSE_20261102_V1.json`
- PR #531 independent replication + support-semantics correction/reuse matrix.
- PR #536 actual measured C3 producer; C2 rejects 48-address fixture because it requires 3×512 measured features.
- PR #533 V79/V80 terminal 207-confirmatory/85-forensic selection audit.
- PR #534 frozen V80 cross-host SHA mismatch is an isolated compatibility/custody RED; it does not erase original V80 scientific status.
- PR #537 remains GPU HOLD until exact overlap with already-executed Stage81B/six-IPB work is established.

Controller truth != measured target != fitted prediction != gate known truth != human biology.

## 9. Current implementation/review status that must be described precisely

### Main D1/V2C/student path
#522–#524 are already scoped-reviewed/accepted on main within their narrow fixture/container scope. Do not rebuild the same D1/V2C route.

### Post-TD #525
Current head: `b493efc35af20bcf2adee29c47376e1dbf4b6dcd`.
At that head, workflows `41592222345`, C4→C6 and prefreeze are green; byte-identical Macha #527/#530/#532 hostile suites are included.
However the last independent Macha verdict was #532 against earlier `0588788f...`, where M01/M02/S01 were RED. The current head is an author repair carrying those tests; do not call it independently accepted without a later non-author verdict.

### Query-address rights #538
Open author-scoped conservative implementation at `b901d3fe25857a09f7e0cbc48d4e75d75d9ca3e0`. It is not a new source issuer and has no current independent Macha comment on the PR thread. Do not make it a prerequisite for already accepted main fixture behavior unless consciously adopted.

### Source qualification
#509/#513/#528 contain source/ETL/alias/QC/public-access corrections. Preserve later errata over earlier statements. Do not resurrect “NPH52 accession missing” or “hardware signing key required for public download.”

## 10. Current narrow scientific frontier

After historical saturation, the unestablished claim is not “does relational biology exist?” Measured broad/mesoscale RNA recurrence has already been tested.

The remaining learned claim is:

**Can a lawfully learned frozen EMA teacher preserve correct-cell broad/mesoscale biological ordering supported by independent measured RNA panels, and—only if the teacher does—can a student with complementary incomplete RNA recover that correct-cell ordering incrementally beyond matched depth/operator/source/donor and wrong-cell controls?**

Important constraints:
- C3 query-specific biology is separate; original R5 already ran.
- TD60 is already designed:
  `target_discovery/iterations/td60_learned_teacher_continuity/TD60_PROSPECTIVE_SCREEN.md`
- Do not redesign TD60.
- TD60's old fixed-u40 biological checkpoint conflicts with later V5 exposure-based recommendation:
  `docs/agent/TEACHER_STUDENT_V5_CONVERGENCE_RECOMMENDATION_20260908.md`
- Resolve checkpoint semantics before any future learned-teacher execution.
- Do not authorize a real source read or corrected synthetic world until the exact experiment is frozen and demonstrably needs it.

## 11. Error traps future agents must not repeat

- Do not equate low JEPA loss with biological recovery.
- Do not infer a teacher target from controller truth.
- Do not use whole-source library denominator when the query must be hidden.
- Do not turn structural absence into measured zero.
- Do not infer gene identity from overlapping genomic span.
- Do not turn source/detection/support shortcuts into biology.
- Do not treat V80 benchmark qualification as estimator qualification.
- Do not treat author-green CI as independent scientific acceptance.
- Do not infer “missing experiment” from one stale handoff; follow blocker → implementation → hostile review → repair → re-review → supersession.
- Search Macha/Claude/GPU/experiment branch families before assigning Macha any work.
- Never ask Macha to redo PR59/69 Level-4 reads, PR336, PR469, #526/#531 review, D1/V2C composition, source qualification, post-TD bridge or other completed branch work.
- Do not automatically run PR537.
- Do not reopen completed PR314/R5/V44/rare/ATAC/CRISPR/V79/V80 experiments at their frozen questions.
- Do not treat “training OFF” as an implementation defect; it is a scientific/authority state.

## 12. Macha/Claude branch evidence

Macha work is not consistently named `macha-*`. Search at least:
- `review/macha-*`
- `audit/macha-*`
- `repair/macha-*`
- `claude/*`
- `gpu/*`
- `experiment/*`
- scientific branches with no agent name

Verified completed Macha scopes include source qualification/ETL reuse, D1→V2C review, student-boundary hostile review, post-TD bridge review/repair, PR526 replication/support correction, Phase-2 audit reconciliation and multiple production-synthetic/task hostile reviews.

Chronology event56 exists specifically to prevent reassigning this work.

## 13. New conversation-source custody

The 2026-11-04 uploaded Macha execution/review transcript is now preserved as a normalized Git text copy at:

`docs/agent/archive/user_supplied_evidence_20261104/MACHA_EXECUTION_REVIEW_TRANSCRIPT_PASTED_TEXT_20261104_NORMALIZED.txt`

Original uploaded file:
- filename: `Pasted text.txt`
- bytes: 374,129
- lines observed locally: 4,840 physical lines / Files renderer 4,841 lines
- original SHA-256: `2eaea727bcf2ca33b6d22f7c78e6677855ae4bf76d52df5dcbff2af8cb140c67`

The Git copy is normalized text for retrieval; the original upload SHA is the byte-level identity. Do not silently claim the normalized Git blob is byte-identical.

## 14. New-agent first-session algorithm

1. Read the mandatory first-read files in §2.
2. Verify current #322 and #460 exact heads and CI; never inherit green status from an older head.
3. Read the latest comments/heads only for PRs that matter to the proposed action.
4. Search Macha/Claude/GPU branches before assigning execution/review.
5. Classify each proposed item:
   - DONE accepted/scoped
   - DONE scientifically negative
   - DONE authority-limited by design
   - superseded
   - genuinely unresolved science
   - genuinely missing implementation/repair
6. Propose work only in the last two classes.
7. Every new proposed action must name:
   - exact unanswered claim/defect
   - exact source proving it remains unresolved
   - adjacent completed work not to repeat
   - minimal new action
   - decision/result it would change
   - owner (GPT vs Macha)
   - stop/no-go condition
8. If no defensible delta remains, say so instead of inventing another experiment.

## 15. Ongoing update protocol

For every substantive future step in this lane:

1. implementation/science/review happens on the appropriate focused PR or existing source branch;
2. append one dated event to #322 chronology with exact source/result/review scope and no-promotion state;
3. update the master no-repeat/source index if the new result changes what future agents should or should not do;
4. verify #322 exact-head CI;
5. update #460 live pointer to the exact new #322 state and current operational next step;
6. verify #460 exact-head CI;
7. preserve failed/negative reviewer evidence rather than rewriting history.

This handoff itself must remain append-only historical evidence when superseded; future updates should add a newer top pointer, not erase this state.
