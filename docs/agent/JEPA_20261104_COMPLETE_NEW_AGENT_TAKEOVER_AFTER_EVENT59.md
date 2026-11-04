# JEPA complete new-agent takeover after audit event59 — 2026-11-04

**Active operational handoff:** PR #460  
**Canonical audit source:** PR #322 exact head `9996d03aa68e9f69fa7dfd3f9bfaf3853f821b28` at creation of this file  
**Standing authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the operational cold-start document for the next GPT/Sol agent. It is deliberately downstream of the canonical #322 audit and must not be used to replace primary receipts.

## 1. First five reads

Read these in order before proposing any work:

1. PR #322: `docs/agent/JEPA_20261104_GPT_LANE_COMPLETE_COLD_START_TAKEOVER_AND_NO_REPEAT_V1.md`
2. PR #322: `docs/agent/JEPA_MACHA_LANE_STATE_FOR_SOL_20261104.md`
3. PR #322: `results/target_discovery/unified_qualification_v1/JEPA_20261104_GPT_LANE_COMPLETE_COLD_START_TAKEOVER_V1.json`
4. PR #322: `results/target_discovery/unified_qualification_v1/JEPA_20261104_MASTER_PRIMARY_SOURCE_NO_REPEAT_INDEX_V1.json`
5. PR #322: `results/target_discovery/unified_qualification_v1/JEPA_CONTINUOUS_CHRONOLOGY_PROGRESS_V1.json`

Then read the complete biological narrative:
`docs/agent/JEPA_20261104_END_TO_END_SCIENTIFIC_NARRATIVE_AND_DECISION_LINEAGE_V1.md`.

Do **not** begin with old PR descriptions or older handoffs.

## 2. What has already been done

The project has already moved through:

- AD microglia/pathology representation work;
- flat RNA-JEPA and Graph-JEPA;
- graph-specificity controls and collapse analysis;
- rare microglia;
- 18-gene/PI evidence synthesis;
- RNA/ATAC/SCENIC+/motif/regulatory triangulation;
- frozen GeneJEPA perturbation/control mechanics;
- physical CRISPR/bulk perturbation work;
- public E2G survey;
- spatial provenance/context work;
- 41,238-address heterogeneous molecular ledger;
- 42 observation operators and FULL104 support/estimability work;
- teacher-target leakage diagnosis;
- Stage81A3/A3R/B teacher/student/anchor experiments;
- R5 query-conditioned measured target experiment;
- V65/V67 planted shared/private-factor recovery;
- TD19 depth-only falsification;
- TD56/57B/59 real relational recurrence and spent PR314 replay;
- C1/C2/C3/C6/C4+C5 candidate framework;
- independent Phase2 known-truth audit #336;
- unified synthetic world #328;
- cross-gate qualification #369;
- synthetic→Task5 integration #469;
- measured-panel audit #526 and Macha correction #531;
- actual measured C3 producer / C2 48→512 refusal #536;
- V79 terminal campaign and V80 benchmark;
- D1/V2C/student-container path on main;
- source qualification/ETL reuse/alias/QC work;
- CaseBundle and Tasks0–8 downstream machinery;
- target portfolio / architecture / teacher / student / matched-compute / EMA infrastructure.

Do not propose rebuilding any of those as a generic next step.

## 3. Data and artifact custody

Large physical data remain on the GPU/project storage and are not duplicated into Git. Use the checksum/index file:

`results/target_discovery/unified_qualification_v1/JEPA_20261104_PROJECT_LOCAL_ASSET_SHA256_CUSTODY_V1.json`

It records the calibration bundle, 41K multipart expression archive, expression sample, checkpoints, T1 checkpoint sequence, NPZ program/molecular-address archive, historical text notes, and the new Macha transcript upload.

The original Macha transcript upload has SHA-256:
`2eaea727bcf2ca33b6d22f7c78e6677855ae4bf76d52df5dcbff2af8cb140c67`

Searchable normalized Git custody copy:
`docs/agent/archive/user_supplied_evidence_20261104/MACHA_EXECUTION_REVIEW_TRANSCRIPT_PASTED_TEXT_20261104_NORMALIZED.txt`

Do not claim the normalized copy is byte-identical to the original upload.

## 4. Macha lane — controlling state

Read:
`docs/agent/JEPA_MACHA_LANE_STATE_FOR_SOL_20261104.md`.

It controls over older summaries of Macha's work.

Important corrections that must not regress:
- NPH52 access/license is known: Zenodo 8319719 rev2, CC-BY-4.0.
- Hardware/offline signing key is optional hardening, not a prerequisite.
- PR #336 already independently audited the Phase2 9/9 receipt.
- Synthetic-vs-real source geometry was not simply reversed.
- Alias-right owner decision was already made; code enforcement is the remaining issue.
- PR59/69 already performed Level-4 reads; do not say none occurred.
- Macha disclosed one QC replay before adjudication; the hold is now active.

Macha's actual current queue at event58:
- independent review of PR #525 current head `b493efc35af20bcf2adee29c47376e1dbf4b6dcd`;
- no-read challenge of PR #535 if still useful;
- PR #537 GPU run is HOLD and requires explicit owner authorization;
- PR #536 review only if requested.

Search Macha/Claude/GPU/experiment branches before assigning anything. Event56 exists specifically to prevent duplicate assignments.

## 5. Current owner rulings

Audit event57 controls:

### QC metadata
Approved narrowly:
- SEA-AD `Doublet score`
- HVS `is_primary_data`

Metadata-only QC/provenance. Never use as pathology, target, expression/model feature, teacher/student input or donor/specimen surrogate.

### Real Level-4 CaseBundle
No new count read authorized now.
Reuse PR59/69 historical physical reads and receipts. Any future read requires a frozen decision-bearing experiment and rights/selection binding first.

### Synthetic support semantics
Macha #531 five-rule semantics are accepted as the required contract for a future successor world:
- structural absence;
- measured zero;
- detection probability;
- collision-unresolved;
- rights withholding.

No corrected synthetic world, fit or training is authorized now. PR328 V2 remains frozen.

## 6. Key implementation/result entry points

### Historical six-IPB / Stage81
- `scripts/v4/stage81a3_ipb_jepa_feasibility.py`
- `results/v4/stage81a3_ipb_jepa_feasibility.json`
- receipt SHA: `aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308`

Stage81B later performed matched JEPA_ONLY/CURRENT/ANCHOR_ONLY work and rejected the anchor. Do not run PR537 until exact novelty is demonstrated and the owner authorizes it.

### Real target discovery
- TD19: `target_discovery/iterations/td19_claude_followup/TD19_DECISION.md`
- TD60 prospective design: `target_discovery/iterations/td60_learned_teacher_continuity/TD60_PROSPECTIVE_SCREEN.md`
- corrected real replay: PR #314, spent;
- Phase2 independent audit: PR #336.

TD60 is already designed. Do not redesign it.

### Synthetic integrated world
PR #328:
- `scripts/v79/unified_synthetic_integration_v1.py`
- `scripts/v79/unified_synthetic_fit_view_v1.py`
- `scripts/v79/unified_synthetic_controller_truth_v1.py`
- `results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2.json`

PR #526:
- `scripts/v79/audit_frozen_measured_panel_observability_v1.py`
- `results/v79/unified_synthetic/JEPA_FROZEN_Q_OTHER_8_MEASUREMENT_REUSE_20261102_V1.json`

PR #531 corrects the support interpretation and gives the future observation contract.

### Post-TD / teacher-student control plane
PR #525 current head:
`b493efc35af20bcf2adee29c47376e1dbf4b6dcd`

At that exact head, the author CI includes the byte-identical Macha #527/#530/#532 tests and is green. The last independent Macha verdict was against the prior `0588788f...` head, so the current head must not be called independently accepted until Macha's fresh-head review is complete.

## 7. Current scientific frontier

The project has already established measured broad/mesoscale relational recurrence. The unresolved claim is narrower:

**Can a lawfully learned frozen EMA teacher preserve correct-cell broad/mesoscale biological ordering supported by independent measured RNA panels, and—only if the teacher succeeds—can a lawful partial-RNA student recover that ordering above matched depth/operator/source/donor and wrong-cell controls?**

C3 query-specific biology is separate. Original R5 already showed query-aware measured-target signal.

Before executing the learned-teacher experiment:
- reconcile TD60's old fixed-u40 checkpoint with the later V5 exposure-based checkpoint recommendation;
- preserve TD57C fine-locality failure;
- inherit source/measurement-state estimability rules;
- do not use low JEPA loss as biology;
- do not use controller truth as the measured teacher target.

## 8. Candidate dependencies

Do not reduce the project to C2 versus C3:

- C1 = shared emergent
- C2 = relational shared
- C3 = query-conditioned measured
- C6 = C1 + C3 composite
- C4 = C2 + C3 composite, tested against independently qualified C6
- C5 = regulatory specialist, separate

C6/C4 are dependent composites. C5 cannot rescue failed foundation targets.

Representation families are separately unresolved:
global-cell, gene/query-local, program, structured.

## 9. Explicit no-repeat list

Do not repeat by default:
- PR59/69 Level-4 reads;
- PR314 replay;
- R5;
- Stage81B;
- PR336;
- PR469;
- PR526/#531 review;
- V79/V80 original realized worlds/benchmark;
- D1/V2C fixture/container work already accepted on main;
- source qualification/ETL reuse already done by Macha;
- post-TD bridge review already done;
- generic synthetic-real pipeline integration;
- generic teacher/student/EMA construction;
- generic CaseBundle/Tasks0–8 construction;
- generic architecture rescue on the old feature matrix;
- generic C5 tuning after V53–V57/V63 negative evidence.

A rerun needs a changed source, new contradictory executable result, new authenticated data, or deliberately changed prospective question.

## 10. PR460 recovery incident

On 2026-11-04 Macha accidentally deleted the #460 handoff branch after a script error. It was immediately restored to exact prior commit `d5732fe690dc3a6ef89ebaaaf25c98d23fa65493`; no content was lost. GitHub auto-closed the PR. Sol/GPT reopened PR #460 before writing this handoff.

Do not interpret the closed/reopened event as a scientific or custody reset.

## 11. Future-agent execution discipline

For every candidate next action:

1. Check #322 event59 package and latest chronology.
2. Search latest PR comments and Macha/Claude/GPU branches.
3. Prove the action is not already complete.
4. State the exact unanswered claim or demonstrated defect.
5. State the exact result that would change the scientific decision.
6. Reuse existing machinery and frozen worlds where possible.
7. Define stop/no-go conditions before execution.
8. Keep GPT implementation and Macha independent review separate.
9. After substantive work:
   - focused implementation/review PR;
   - append #322 event;
   - update no-repeat/source index if planning changes;
   - verify exact #322 CI;
   - update #460 pointer;
   - verify exact #460 CI.

Do not create a third historical-consolidation branch.

## 12. What to do in the first session

Do not immediately launch training.

First:
- verify the latest #322 and #460 heads/CI;
- check whether Macha completed the #525 fresh-head review after event58;
- check whether #535 challenge has been completed;
- keep PR537 HOLD unless the owner explicitly authorizes it;
- if planning a learned-teacher experiment, reconcile TD60/V5 checkpoint semantics first and write the exact prospective falsifier without changing existing biology outcomes.

If a proposed action cannot survive this no-repeat check, do not assign it.

This file should be updated at the top or superseded by a new dated operational pointer as the project progresses; preserve the historical version for audit.
