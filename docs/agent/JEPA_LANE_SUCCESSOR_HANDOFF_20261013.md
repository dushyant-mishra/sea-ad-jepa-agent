# JEPA Target Discovery + downstream lane — successor-agent handoff

Date: 2026-10-13

Terminal status:

`TAKEOVER_READY__HISTORICAL_AUDIT_FROZEN__PHASE1_BLIND_RECEIPT_AUDITED__CONTROLLER_CLOSED__POST_TD_CONTROL_PLANE_GREEN__NO_TARGET_OR_TRAINING_AUTHORITY`

## 0. Your job as successor

Take over the Target Discovery → downstream JEPA architecture lane **without redoing the historical archaeology** and without crossing authority boundaries.

Your first responsibility is preservation: use the frozen historical decisions, gene-identity reclassification, phase-1 blinded evidence, and downstream harness exactly as recorded. Do not reinterpret old failures into successes, do not rerun spent experiments, and do not open controller truth unless a separate explicit phase-2 authorization exists.

The current project authority is still:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Read in this order

1. `docs/agent/JEPA_LANE_SUCCESSOR_HANDOFF_20261013.md` — this file.
2. `docs/agent/JEPA_LANE_SUCCESSOR_AUDIT_20261013.md` — current authoritative audit delta and no-repeat rules.
3. `results/target_discovery/JEPA_LANE_SUCCESSOR_STATE_20261013.json` — machine-readable state.
4. `docs/agent/JEPA_LANE_TAKEOVER_HANDOFF_20261013.md` — prior complete takeover package.
5. `docs/agent/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md` and its JSON mirror.
6. `docs/agent/JEPA_GENE_IDENTITY_RECLASSIFICATION_AUDIT_20261013.md`.
7. `docs/agent/JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.md` and JSON mirror.
8. `docs/agent/TD_PHASE1_INDEPENDENT_RECEIPT_AUDIT_20261013.md`.
9. `docs/agent/JEPA_ROBUST_PIPELINE_POST_JEPA_ANYTHING_AUDIT_20261013.md`.
10. `docs/agent/JEPA_LOCAL_ARTIFACT_CUSTODY_20261013.csv` before touching any local binary/data artifact.

Do **not** start with old chats or scattered PR comments unless one of the indexed documents explicitly sends you there.

## 2. Historical frozen checkpoints

### Architecture/history audit

- PR #322
- frozen audited head: `6d6ec998e38b5da5a5281ebba89c471de16f243f`
- contains historical architecture decision ledger, gene-ID reclassification, downstream-readiness audit, robust-pipeline/JEPA-Anything audit, repaired-41K smoke results, validator/tests/CI.

### Prior handoff/custody

- PR #323
- meaningful head after phase-1 structural audit: `87cd356dd739d12662da14ecc3625ff8d80c21ec`
- includes read-first takeover package, custody manifests, branch map, context snapshots, handoff validator/tests, and `TD_PHASE1_INDEPENDENT_RECEIPT_AUDIT_20261013.md`.

Treat #322/#323 as historical snapshots. This successor is append-only; do not rewrite their conclusions.

## 3. Active TD synthetic qualification chain

### Frozen code/package identities

- TD PR #320: `1f474a44a6baabc667dbfda726e0755426c732e7`
- synthetic V2.1 PR #321: `15f519c00137d581e25232c16be52c2b9badd83e`
- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- controller archive SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`
- final cross-cert receipt SHA-256: `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`

### Phase 1 is already spent

Macha ran the blind fit exactly once.

- evidence branch: `evidence/td-synthetic-phase1-blinded-fit-1f474a44-20261013`
- evidence commit: `a1aed169be5f4552208128f9d71b2d601a657393`
- blinded V4 receipt SHA-256: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`
- controller was not downloaded/opened;
- `adjudicate` was not run;
- output values were not semantically mapped in this lane.

Independent mechanical audit conclusion:

`PASS_PHASE1_RECEIPT_STRUCTURE_AND_CUSTODY__SAFE_TO_CONSIDER_SEPARATE_PHASE2_AUTHORIZATION`

**Do not rerun phase 1.** A different result from a rerun would create an avoidable multiplicity/custody problem.

### What may happen next

Only a new explicit phase-2 authorization may introduce controller truth. That authorization should bind at minimum:

- exact TD commit `1f474a44...`;
- exact blinded receipt SHA `e67aace8...`;
- exact package/binding/controller identities;
- exact V4 adjudication code identity;
- one-shot adjudication semantics;
- downstream authority flags remaining false regardless of outcome.

Absent that explicit authority: STOP. Do not open the controller archive.

## 4. Target-discovery interpretation guardrails

The synthetic experiment qualifies/falsifies **tests of the target hypotheses**. It does not itself choose a biological target.

Preserve these failure scopes:

- fine-scale failure → fine-scale claim only;
- source failure → cross-source universality only;
- technical-control failure → biological/program interpretation only;
- `NOT_ESTIMABLE` is not biological failure;
- no rare relational increment is not absence of a rare program;
- narrow relational failure cannot erase C2 biology globally, rare-state biology, or dataset utility.

PR #314 remains frozen/spent. PR #313 remains a separate real-tournament lane. Do not silently modify either.

## 5. Historical architecture evidence — what is closed

Do not waste compute retesting these as if unresolved unless the frozen ledger explicitly marks a replay requirement:

- hidden-gene/CELL anchor as encoder objective — rejected;
- ANCHOR_ONLY — rejected;
- core-only evidence and evidence-starvation/tier-hiding production cascade — rejected/insufficient;
- T0/T1/TCTX historical target family — no production target qualified;
- V6R5B residual target — did not rescue;
- historical PROD41K/T1 — defective optimization trajectory; forensic only;
- rare auxiliary head — signal did not earn benchmark lock;
- graph auxiliary — real graph failed randomized control;
- arithmetic block-mean target — negative prior;
- Signed-V2 production target — rejected;
- historical fixed EMA `.996` or other betas — no production authority.

Keep negative results as negative priors. Do not delete them because they are inconvenient.

## 6. Gene identity: mandatory evidence classification

The later gene-ID recovery means historical evidence must be classified before use.

Allowed classes:

- `SOURCE_NATIVE_SAFE`
- `FROZEN_4K_IDENTITY_AUDITED`
- `REPAIRED_41K_ADDRESS_BOUND`
- `SEMANTICS_FREE_MECHANICS`

Anything pre-repair that uses NPH/cross-source gene semantics without repaired address binding is:

`GENE_IDENTITY_PROVENANCE_UNRESOLVED__NOT_ARCHITECTURE_AUTHORITY`

Important nuance: this is not a blanket invalidation of all historical work. SEA-AD-only source-native rare/graph experiments and semantics-free EMA/optimizer mechanics retain their original status. It also does not resurrect experiments rejected for other reasons.

## 7. Repaired local data/custody available to this project

Use `docs/agent/JEPA_LOCAL_ARTIFACT_CUSTODY_20261013.csv` for exact byte identities.

Key safe substrate:

- reconstructed discovery archive: `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip`
- 607,959,761 bytes
- SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- split parts are separately hash-bound;
- paired calibration bundle is separately hash-bound;
- repaired program-weight NPZ is separately hash-bound.

These are pilot/smoke/replay assets, not automatic production-training authority.

Historical `t1_checkpoint_u0200.zip` is forensic only and must never be resumed as valid training authority.

Large binaries are intentionally not copied into public GitHub. Do not create duplicate repositories of biological data simply to make handoff easier; use byte custody.

## 8. Downstream implementation status

The post-TD control plane is now materially implemented rather than merely discussed.

Original implementation source:

- branch `implementation/jepa-post-td-harness-prefreeze-20261013`
- head `97dd73f49e1554053bbfab6c5369377a23a72ceb`
- tree `2f391e02fdc663de001f52a83e0b84ec5d1082e8`
- workflow run `38448458550` → `success`

This successor carries the same implementation tree squashed cleanly onto the audited handoff base at clean consolidation commit:

`ef8364c98a10a4679e998b9b41aa66416d553ee4`

### Runnable modules

- `scripts/v5/jepa_post_td_harness_contract_v1.py`
- `scripts/v5/jepa_post_td_rehearsal_preflight_v1.py`
- `scripts/v5/jepa_post_td_tournament_controller_v1.py`
- `scripts/v5/jepa_post_td_presentation_ema_v1.py`

### Tests

- `tests/v5/test_jepa_post_td_harness_contract_v1.py`
- `tests/v5/test_jepa_post_td_rehearsal_preflight_v1.py`
- `tests/v5/test_jepa_post_td_tournament_controller_v1.py`
- `tests/v5/test_jepa_post_td_presentation_ema_v1.py`

### CI

- `.github/workflows/jepa-post-td-harness-prefreeze.yml`

### What the harness already enforces

- target portfolio dependency rules;
- lawful teacher evidence masks/policies;
- zero-update teacher-target screens before neural training;
- matched-compute architecture manifests;
- per-block non-compensation;
- explicit eligible versus missing/`NOT_ESTIMABLE` supervision;
- recoverability class → lawful student output semantics;
- teacher-private information → critic-only, never fake point target;
- independent-teacher/specialist-student complexity stays blocked without new interference evidence;
- optional factorization is block-internal only;
- write-once rehearsal preflight;
- presentation-normalized EMA half-life, not inherited fixed beta;
- three-arm EMA screen: short/intermediate/long, no winner preselected;
- restart-safe cumulative successful-presentation state;
- checkpoint overlay binds portfolio, architecture and EMA state;
- all target/representation/training/continuation authority remains false.

No probabilistic loss has been selected. If `STOCHASTIC_IDENTIFIABLE` becomes active, freeze that mechanics question prospectively rather than inventing a likelihood after seeing outcomes.

## 9. Recommended downstream sequence after TD target qualification

Do not run the full Cartesian product of every historical idea.

### A. Freeze target portfolio

Consume only qualified C1/C2/C3/C5/composite blocks with their exact failure scopes. No architecture can rescue an unqualified biological block.

### B. Zero-update teacher construction screen

Before optimizer or EMA updates, compare only lawful constructions relevant to the qualified block:

- value-visible rich reference where relevant;
- value-blind rich complementary teacher where query-conditioned state is relevant;
- block-blind/program construction only for a block/program biological target.

Use shortcut controls; do not pick by raw reconstruction alone.

### C. Assign recoverability

Each target component must be typed as one of:

- `POINT_IDENTIFIABLE`
- `STOCHASTIC_IDENTIFIABLE`
- `TEACHER_PRIVATE`
- `NOT_ESTIMABLE`

Then use only lawful student semantics.

### D. Teacher/student topology tournament

Primary teacher candidates:

1. single rich EMA teacher;
2. shared EMA backbone + typed heads.

Independent complementary teachers enter only after demonstrated shared-teacher interference.

Primary student candidate:

`full-capacity shared student + typed prediction heads`

Specialist students enter only after demonstrated negative transfer.

### E. EMA screen

Use successful base-cell presentations as the native time unit. Run a compact short/intermediate/long half-life screen only after architecture semantics are frozen. Do not translate old `.996` into authority.

### F. Optional internal factorization

Only after typed biological heads are qualified may a capacity-matched OPF/fixed-orthogonal/multi-head numerical comparison be run **inside** a biological block. Never allow a global rotation to erase block accountability.

### G. Privileged modalities

ATAC/SCENIC/spatial/regulatory information should generally act as privileged critics/corroboration when it is not point-identifiable from RNA. Do not force the RNA student to reproduce realization-level teacher-private state.

## 10. JEPA-Anything interpretation

Do not organize the project around “beating JEPA-Anything.” The paper is a useful external reference for factorized prediction/capacity allocation, not a new biological authority.

Our robust pipeline objective is broader:

- biologically valid target semantics;
- lawful evidence boundaries;
- donor/source transport;
- rare-state fidelity;
- relational biology;
- observation-operator separation;
- recoverability and uncertainty;
- fail-closed governance.

OPF is therefore an optional numerical tool, not the scientific target-discovery mechanism.

## 11. Open work list

At takeover, these are the legitimate open items:

1. Decide whether to issue a separate explicit phase-2 authorization for synthetic TD adjudication.
2. If authorized, run phase 2 once against exact frozen identities; freeze adjudication receipt; do not let it auto-grant real execution.
3. Audit the phase-2 receipt independently before using its biological interpretation.
4. Continue real target qualification only under the appropriate separate authority.
5. When a target portfolio is frozen, instantiate the already-built post-TD harness rather than writing a new architecture stack.
6. Add a probabilistic loss only if a qualified target is `STOCHASTIC_IDENTIFIABLE`, under a new prospective mechanics contract.
7. Keep training off until explicit authority.

## 12. What you must not do

- Do not rerun phase 1.
- Do not open controller truth without separate phase-2 authority.
- Do not treat synthetic qualification as human biological validation.
- Do not average source failures away.
- Do not turn `NOT_ESTIMABLE` into zero.
- Do not use pre-repair NPH gene semantics as architecture authority.
- Do not resume historical PROD41K/T1 checkpoints.
- Do not resurrect graph/rare-specialist/anchor targets merely because architecture fashion changed.
- Do not modify PR #314's spent result.
- Do not silently modify PR #313 from this lane.
- Do not select a target from smoke tests.
- Do not let aggregate JEPA loss compensate for a failed biological gate.

## 13. Minimum takeover report before doing new science

A successor should report back these exact checks before new execution:

- current checked-out branch/SHA;
- confirms this handoff + successor audit were read;
- confirms PR #322 historical ledger was read;
- confirms gene-identity evidence policy;
- confirms phase-1 receipt hash `e67aace8...` and that phase 1 is spent;
- confirms controller remains closed unless separately authorized;
- confirms post-TD harness modules/tests exist and CI provenance is known;
- states which open item above is being advanced;
- states why the action does not duplicate a closed historical experiment.

That is sufficient to take over this lane without repeating months of audit work.
