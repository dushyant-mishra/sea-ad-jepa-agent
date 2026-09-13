# JEPA V5 New-Chat Handoff — External Review Final Current

Date: 2026-09-13
Repository: `dushyant-mishra/sea-ad-jepa-agent`
Canonical working branch: `planning/v5-dataset-first-production-closure-20260912`

Status:

`V5_EXTERNAL_REVIEW_ENGINEERING_REPAIRS_GREEN__REAL_FULL104_EXECUTION_NEXT__NO_TRAINING_AUTHORITY`

This handoff supersedes `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260913_V5_EXTERNAL_REVIEW_CURRENT.md`, whose red-CI section described an intermediate state that has now been repaired and re-verified.

## 0. First instruction to the next chat

Do **not** restart analysis from scratch.

Before any current-state claim or write:

1. Re-fetch the live head of `planning/v5-dataset-first-production-closure-20260912`.
2. Read `START_HERE.md` first.
3. Read this handoff completely.
4. Read `docs/agent/JEPA_LATEST_HANDOFF_POINTER_20260913.json`.
5. Then read the V5 historical/full-data authority documents listed below.

Parallel work has landed on the planning branch before. Never trust a SHA from this handoff without re-fetching live state.

## 1. Exact verified state at handoff creation

Latest code-bearing external-review repair head:

`a388c773feb48ebf3fc6ce20b8782182abc1891b`

Commit:

`test(v5): update preexecution fixture for geometry authority binding`

GitHub Actions run:

`34739456264`

Exact result:

- `177 passed`
- authority-source compilation PASS
- zero reported test failures

The branch then received documentation-only handoff commits. Exact repository/documentation head before this final handoff was:

`629249ffa54d0906bc0f0733a925d8cdb52ed66c`

GitHub Actions run:

`34739477755`

Conclusion:

`success`

The final handoff commit itself will advance HEAD again. Re-fetch before continuing.

## 2. What V5 means in this project

V5 is the integrated production JEPA pipeline, not only a runtime guard or dimension selector.

The intended dependency chain is:

`heterogeneous human expression corpus`
`-> pathology-blind target discovery / representation qualification`
`-> authenticated FULL104 production substrate`
`-> D_shared / D_private / D_obs authority`
`-> scientific schedule / proposal / packing / restart authority`
`-> data-derived student/teacher runtime geometry`
`-> protected-gradient / Adam / EMA / checkpoint mechanics qualification`
`-> bounded base-learning qualification`
`-> lawful base EMA teacher`
`-> TD60 learned-teacher continuity qualification`
`-> relational student qualification`
`-> integrated independent review`
`-> only then possible explicit production-training authority`

Training is **not** authorized now.

## 3. Core scientific design intent

The corpus was deliberately built from heterogeneous normal, aging, pathological-aging and disease contexts, living and postmortem material, different brain regions, ages, sexes, studies and sequencing/measurement technologies.

The purpose is not to supervise an AD label into the representation. The intended discovery claim is stronger:

> can disease-relevant biology emerge from a pathology-blind representation when technical shortcuts are denied?

This design creates a major confounding threat:

`disease status ~ dataset/source ~ technology ~ living/postmortem ~ region`

Therefore a pooled disease trajectory is **not sufficient** evidence of biology.

Later biological claims should, wherever data support them, require:

- within-study disease-spectrum replication before pooled disease-axis promotion;
- matched donor/region/platform contrasts where available;
- attacks for dataset/source/operator/matrix/technology/living-postmortem/PMI/region/sex/depth/support-family recovery;
- biology-preserving technical perturbations;
- biology-corrupted / technology-preserved negative controls;
- technical-only and randomized/matched-null controls.

Do not inspect protected pathology/confirmation information if it could change a design choice.

Standing rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## 4. Permanent interpretation rule

A zero, failed gate, non-significant association, bad fit or low predictability is not automatically a biological zero.

Keep separate terminals for at least:

- estimator failure;
- measurement-model failure;
- not estimable under available support;
- inadequate Monte-Carlo precision;
- representation failure;
- technical confounding unresolved;
- influence instability;
- incremental prediction not demonstrated;
- biological necessity not demonstrated;
- transport not validated;
- confirmation not authorized;
- target not qualified;
- genuine qualified biological negative.

Never collapse these into `BIOLOGY_ABSENT` merely because a procedure returned zero/failure.

Decision-bearing metrics should be unconditional over the declared evaluation population. Failed fits, undefined comparisons, missing support, failed perturbations and other non-success units may not silently disappear from the denominator. Conditional-on-success statistics may be retained as diagnostics only.

## 5. Repository-side work already completed before the final external review

The September-12 successor work already included substantial dataset-first machinery. Do not rebuild it.

### 5.1 Stale TRAIN -> FULL104 authority path closed

The corrected 42-shard TRAIN cache cannot mint full-reader production authority.

### 5.2 Canonical artifact binding

Receipts are tied to exact serialized payloads and exact parent artifacts instead of caller-supplied matching strings.

### 5.3 FULL104 -> dimension-authority interface

Fixtures/synthetic data cannot substitute for the real authenticated FULL104 substrate.

### 5.4 Frozen FULL104 metadata identity

Authenticated metadata SQLite SHA:

`a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

The production binder no longer accepts caller-selected metadata authority.

### 5.5 Same metadata authority through schedule/proposal/restart

The same frozen metadata authority is enforced by the FULL104 binder, schedule optimization, schedule materialization and proposal/restart audit path.

### 5.6 Full-stream dimension-family producer exists

`scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py`

The D_shared rule includes the explicit held-donor predictability gate and one-SE selection can select a lower supported rank than the longest supported prefix.

### 5.7 D_private / D_obs prospective candidates exist

They remain candidate rules pending independent review and real FULL104 metric evidence. Do not tune them after seeing outcomes merely to obtain a preferred rank.

### 5.8 Dimension metric / selection artifacts are hash-bound

D_private metrics additionally descend from the exact frozen D_shared selection.

### 5.9 Executable postqualification authority recovered

Current layers include:

- `src/sea_ad_jepa/v5/postqualification_dependency_guard_v2.py`
- `src/sea_ad_jepa/v5/qualification_phase_contract_v3.py`

Postqualification cannot be created by report assertions alone. It requires executable-power evidence, exact code identities, raw output bindings and independent recomputation.

### 5.10 Current checkpoint successor exists

`src/sea_ad_jepa/v5/atomic_checkpoint_guard_v3.py`

It restores current-authority threshold, registry, mechanics-chain, EMA chronology, critical-test and anti-cheat bindings without reviving obsolete V1 authority semantics.

## 6. Final external-review findings and repairs

The user requested an adversarial review from three roles: computational biologist, AI/JEPA engineer and scientist/inference reviewer.

The engineering review found real lineage/authority defects and fixed them rather than weakening the gates.

### 6.1 Legacy T0/V21 runtime authority leak quarantined

File:

`src/sea_ad_jepa/v5/qualified_teacher_student_runtime_v1.py`

The historical V21 46-donor target receipt is now explicitly mechanics/forensics-only. It cannot authorize a current V5 base-learning update.

The public V5 update path now requires a distinct current dataset-derived V5 teacher authority. It also refuses to select the historical V4 production configuration implicitly; current V5 runtime config must be supplied explicitly from current authority.

Do not widen the legacy T0 receipt schema into V5 authority.

### 6.2 Fixed 48-tensor protected-registry assumption removed

New authority:

`src/sea_ad_jepa/v5/production_protected_registry_authority_v1.py`

Historical six-block C2/V4 mechanics happened to produce 48 protected tensors. That count is not production authority.

Current expected protected tensors are:

`model_depth * 4 protected roles * 2 parameter kinds`

Protected roles:

- `attention_norm`
- `attention.query`
- `attention.key`
- `attention.value`

Parameters:

- `weight`
- `bias`

The exact tensor identities are canonicalized and hash-bound. GPU qualification, preexecution and checkpoint telemetry use the same protected-registry identity.

### 6.3 Production mechanics chain made explicit

Current protected mechanics chain:

`FP16_FORWARD`
`-> BACKWARD_AUTOCAST_DISABLED`
`-> UNSCALE`
`-> PROTECTED_REGISTRY_GRADIENT_GATE`
`-> OPTIMIZER_STEP_PROVED_BEYOND_DECAY`
`-> ADAM_EXP_AVG_PROVED`
`-> ADAM_EXP_AVG_SQ_PROVED`
`-> EMA_UPDATE`
`-> SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE`
`-> ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

This preserves the historical lesson that fp16 autocast backward killed protected gradients, without promoting the historical 128x8 geometry to current production authority.

### 6.4 Production GPU evidence can no longer self-declare geometry

File:

`src/sea_ad_jepa/v5/production_geometry_gpu_guard_v1.py`

Current GPU qualification binds exact:

- design context;
- FULL104 expression artifact;
- production dimension artifact;
- proposal-weight artifact;
- packing/restart artifact;
- representation firewall artifact;
- historical C2 receipt as supporting-only;
- protected registry SHA;
- update-geometry authority SHA;
- effective batch;
- microbatch;
- model width;
- model depth.

The geometry must be frozen before GPU execution and reported as `DATA_DERIVED_PRODUCTION_AUTHORITY`.

The receipt must prove:

- CUDA available and device identified;
- production geometry actually executed;
- real FULL104 reader batch used;
- synthetic loader not used;
- exact mechanics chain;
- exact protected registry/count;
- gradients live for all protected tensors;
- movement beyond decay for all protected tensors;
- both Adam moments live for all protected tensors;
- EMA update proved;
- atomic checkpoint/telemetry commit proved;
- training authority remains false.

### 6.5 End-to-end trainer/dependency anti-splice gap closed

File:

`src/sea_ad_jepa/v5/trainer_preexecution_contract_v4.py`

A real defect was found: the trainer could validate its own geometry/protected-registry authority and consume an individually valid dependency closure from a different geometry/registry.

Repair requires exact equality of:

`trainer authorities[update_geometry_authority_sha256]`

with:

`dependency closure update_geometry_authority_sha256`

and exact equality of trainer and dependency protected-registry SHA.

Fail-closed mismatch terminals include:

`STOP_V5_PREEXECUTION_V4_UPDATE_GEOMETRY_AUTHORITY_MISMATCH`

`STOP_V5_PREEXECUTION_V4_PROTECTED_REGISTRY_AUTHORITY_MISMATCH`

This is an end-to-end lineage invariant, not a cosmetic assertion.

### 6.6 RED after anti-splice repair was a stale fixture, not a reason to weaken the invariant

Commit `0536dcb5795e5f7f6a64172bde87bf9c8f1bcde0` correctly added the anti-splice requirement, but CI run `34739274544` initially failed 4 tests because the old `tests/test_preexecution_dependency_guard_v1.py` valid GPU fixture omitted the newly mandatory `update_geometry_authority_sha256` binding.

Observed red result:

`4 failed, 173 passed`

Root cause:

`STOP_V5_PREEXECUTION_GPU_BINDING_SET_MISMATCH`

The production guard was correct; the fixture was stale.

Minimal repair commit:

`a388c773feb48ebf3fc6ce20b8782182abc1891b`

The valid test fixture now includes the new geometry-authority binding. No guard was weakened.

Verified result:

`177 passed in 4.30s`

authority-source compile PASS.

## 7. Current FULL104 state

FULL104 was historically materialized and used at production scale. Do **not** rebuild it unless the existing heavy store is missing/corrupt by hash.

Expected physical root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical geometry:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / matrices
- 8,915 Level-4 blocks
- 41,238 molecular addresses
- 17,186 common measured-core addresses
- 1,400 donor x operator groups
- 1,361 groups with >=3 cells, containing 99.9987% of reader-fit cells

Frozen historical hashes:

```text
block manifest              66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
materialization contract    612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17
materialization audit       9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf
reader-fit selection        edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b
selection manifest          3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e
metadata SQLite             a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913
feature-matrix root         c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef
multiview-feature root      d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1
```

Historical FULL104 ALL execution fingerprint:

`a0fe5bc7be0769c9880763b3831ea330a251dfa710a8635b05f678c5d6e94202`

Historical terminal manifest:

`8f292673c84447ee88f3a78936aa88920b96f0ffd681237e2b5af3e7dfe4d60c`

Historical `TEACHER_BIOLOGY_LIMIT` applies only to that old shared-state estimand. It is not evidence that FULL104 lacks biology and is not current V5 dimension authority.

## 8. Heavy-data boundary

The >30 GB FULL104 store is not available in this chat/container. It is available to Claude on the user's GPU-enabled laptop/external drive.

Do not pretend to inspect those bytes here.

The first real-data action is recovery/location + current V5 rebinding of the existing bytes, not synthetic rebuilding.

Read:

`docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`

Required binder terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Then seal:

`V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json`

Return compact receipts/hashes only; do not upload the >30 GB substrate.

If any historical hash differs: STOP. Do not silently substitute TRAIN, 50K, reconstructed bytes or a new dataset.

## 9. Numeric dimensions are still not authorized

No production numeric authority yet for `D_shared`, `D_private`, `D_total`, or `D_obs`.

Required real FULL104 metric families include:

### D_shared

- full-refit matched-null signal;
- donor-resampled subspace stability;
- held-donor cross-view prediction plus donor-level uncertainty;
- independent view/sketch agreement;
- increment beyond frozen measurement-shortcut baselines.

### D_private only after D_shared freezes

- held-donor incremental common-core biology prediction;
- held-operator increment;
- measurement-shortcut increment;
- same-cell technical-intervention stability.

### D_obs

- held-operator reconstruction of lawful observation descriptors;
- source/matrix identity are neither free biology inputs nor reconstruction targets;
- no biological qualification claim.

Raw metric outputs must be hash-bound to exact FULL104 input and exact execution receipts before selection.

## 10. Monte-Carlo / resampling precision authority remains open

Do not inherit `256`, `999`, `1000`, or any other convenient historical replicate count.

Before observing current V5 numeric outcomes, freeze a metric-specific precision rule defining:

1. controlled Monte-Carlo quantity;
2. tolerated error;
3. family-wise/risk allocation across ranks/views/gates;
4. exact count formula or prospective stopping rule;
5. hard min/max if sequential;
6. deterministic RNG and replay semantics;
7. unconditional decision-bearing operating characteristics.

Estimator/MC failure is not a biology failure.

## 11. Anti-cheat evidence remains a major production qualification task

Current rejection-capable postqualification gate vocabulary is exactly:

1. `donor_recurrence_validation`
2. `heldout_biology_validation`
3. `qc_measurement_confounding_closure`
4. `same_cell_technical_intervention`
5. `shortcut_superiority`
6. `student_representation_collapse`
7. `teacher_representation_collapse`

Do not accept caller booleans as evidence. Each gate ultimately needs executable, raw-output, hash-bound evidence at the adjudication geometry and must accept a minimally valid control while rejecting a minimally invalid control.

The broader computational-biology external review should continue checking explicit protection against:

- donor memorization;
- dataset/source/operator/matrix/batch;
- sequencing technology;
- library/depth/support-family shortcuts;
- specimen identity;
- living vs postmortem status;
- PMI where available;
- region;
- sex/age where estimand-appropriate and authorized;
- same-cell/shared-view leakage;
- duplicate/lookup leakage;
- technical-only shortcuts;
- biology-corrupted/technology-preserved negatives;
- biology-preserved/technology-perturbed positives.

Do not invent thresholds from T0 or historical V4.

## 12. Runtime geometry / EMA remain dataset-first

Historical V4 values such as:

- width 160
- effective batch 128
- microbatch 8
- views 4
- mask fraction 0.40
- target blocks 16
- EMA momentum 0.996

are historical mechanics regression values only.

They are **not** current V5 production authority.

Reusable EMA biological-time primitive:

`m = exp(log(0.5) * presentations_this_update / half_life_presentations)`

The half-life itself must be separately frozen prospectively from lawful V5 authority.

The runtime now requires an explicit current V5 data-derived config rather than silently falling back to historical V4 config.

## 13. Target discovery / teacher / student order

Keep the scientific order:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Do not reverse it.

Target discovery is separate from T0.

Historical relational continuity work includes:

- TD57B global recurrence PASS 24/24
- TD57C nearest-third locality FAIL and remains failed
- TD59 nearest-half mesoscale PASS 24/24 as pilot evidence only
- TD60 prospective learned-teacher continuity gate still not authorized

Relational object:

`q(i;j,k) = sign(d(i,j) - d(i,k))`

TD60 requires a lawful learned base teacher first. Do not inherit nearest-half locality as production authority merely because TD59 piloted it.

## 14. T0 is a test rig, not the V5 target

T0/V20/V21 is a separate methodology lane.

Transfer lessons, not biological/numeric authority.

Important current lessons:

- conditional estimator performance != unconditional procedure performance;
- bootstrap survivor interval != unconditional sampling uncertainty when failures are informative;
- failure to measure != absence of biology;
- estimator nonconvergence cannot be silently dropped from decision denominators;
- do not tune thresholds after learning which direction helps;
- false-qualification control matters in addition to interval width;
- numerical repair/projection cannot manufacture scientific qualification.

Latest committed T0 branch known during this handoff:

`t0/v21-closeout-candidate-20260911 @ c22031f92b65c5aa284d40e23f9405f5f235dae0`

That commit corrected the conditional-vs-unconditional AUC interpretation.

Claude subsequently completed a nested synthetic measurement-selection operating-characteristic run locally, but at the time of this handoff the final nested JSON / closeout had not yet been committed to GitHub because Claude hit its session limit.

The reported local ULS operating characteristics at n=28 were:

- STRONG pass 0.025; point improper 0.17; mean bootstrap nonconvergence 0.358
- MODERATE pass 0.000; point improper 0.33; mean bootstrap nonconvergence 0.458
- WEAK pass 0.000; point improper 0.53; mean bootstrap nonconvergence 0.501
- NULL pass 0.000; point improper 0.42; mean bootstrap nonconvergence 0.522

Interpretation:

`T0 n=28 measurement procedure not qualified; biological common factor unresolved, not rejected.`

Do not claim tau biology absent.

Important wording caution: the local evidence reported `candidate_freq_unconditional=0.375` under NULL for steps 1-5. Until code-level terminal ordering demonstrates equivalence, call this an **intermediate candidate-selection rate**, not automatically a 37.5% final false-qualification rate.

## 15. Hard boundaries remain closed

```text
V5_FULL104_EXPRESSION_CLOSURE = FALSE until real binder receipt returns
V5_PRODUCTION_TRAINING_AUTHORIZED = FALSE
protected_data_authorized = false
reader_validation_closed = true
reader_oracle_closed = true
pathology_closed = true
td60_authorized = false
relational_target_activation_authorized = false
S0_S4_SELECTION_AUTHORIZED = FALSE
FRESH_READER_VALIDATION_OPEN_AUTHORIZED = FALSE
READER_ORACLE_OPEN_AUTHORIZED = FALSE
```

No branch name, passing CI, binder PASS, dimension receipt, CUDA mechanics run or bounded qualification automatically changes these authorities.

## 16. Required reading order for the next chat / Claude

After `START_HERE.md` and this handoff:

1. `docs/agent/V5_REPOSITORY_SIDE_CLOSURE_AND_CLAUDE_DATA_HANDOFF_20260912.md`
2. `docs/superpowers/specs/2026-09-12-v5-dataset-first-production-closure-design.md`
3. `docs/agent/V5_FULL104_HISTORICAL_PRODUCTION_RECOVERY_20260912.md`
4. `docs/agent/V5_FULL104_HISTORICAL_EXECUTOR_REUSE_MATRIX_20260912.md`
5. `docs/agent/V5_FULL104_CURRENT_BYTE_REBIND_WORK_ORDER_20260912.md`
6. `docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`
7. `docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`
8. `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_AMENDMENT_20260912.md`
9. `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_CONTRACT_V1.json`
10. `src/sea_ad_jepa/v5/production_protected_registry_authority_v1.py`
11. `src/sea_ad_jepa/v5/production_geometry_gpu_guard_v1.py`
12. `src/sea_ad_jepa/v5/preexecution_dependency_guard_v1.py`
13. `src/sea_ad_jepa/v5/trainer_preexecution_contract_v4.py`
14. `src/sea_ad_jepa/v5/atomic_checkpoint_guard_v3.py`
15. `src/sea_ad_jepa/v5/qualified_teacher_target_receipt_v1.py`
16. `src/sea_ad_jepa/v5/qualified_teacher_student_runtime_v1.py`

## 17. Exact next operational sequence

### On this/lightweight environment

Continue read-only / code-level external review only if useful, especially checking whether the mixed-cohort shortcut protections are executable rather than prose-only. Any new demonstrated defect should use:

`RED -> minimal fix -> GREEN -> adversarial mutation -> exact-head full relevant suite`

Do not create another V5 implementation branch unless truly necessary.

### On Claude's GPU/heavy-data machine

First real-data action:

1. re-fetch live planning branch;
2. locate historical FULL104 bytes;
3. verify frozen historical hashes;
4. run hardened V5 FULL104 binder;
5. require `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
6. seal `V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json`;
7. return compact receipt/hashes;
8. then implement/run the current-V5 full-stream metric executors using reusable historical streaming/checkpoint/reconstruction mechanics where semantically compatible;
9. freeze prospective MC/donor-resample precision authority before reading dimension outcomes;
10. adjudicate D_shared;
11. only then D_private;
12. D_obs separately;
13. pass DimensionExecutionFirewall / DimensionAuthority;
14. derive actual schedule/proposal/packing and runtime geometry from authenticated data/dimensions;
15. freeze presentation-based EMA authority;
16. run production-geometry CUDA qualification;
17. close preexecution dependencies;
18. run bounded base-learning qualification;
19. establish lawful base EMA teacher;
20. only then TD60;
21. only after TD60 and prospective relational-predictability qualification, activate relational student work;
22. integrated independent review;
23. only then consider explicit training authority.

## 18. Historical machinery that may be reused

Audit before rewriting:

- FULL104 streaming;
- sufficient statistics;
- deterministic null machinery;
- atomic shards;
- restart/checkpoint semantics;
- execution fingerprints;
- produced-byte closure;
- independent reconstruction/adjudication.

Reuse mechanics only where semantically compatible.

Do **not** inherit old biology, QID assumptions, cap-4 subsets, rank 32, thresholds, locality, or replicate counts.

## 19. Branch hygiene

Relevant historical V5 branches include:

- `planning/v5-dataset-first-production-closure-20260912`
- `repair/v5-authority-evidence-integration-20260912`
- `repair/v5-installed-target-root-binding-20260912`
- `repair/v5-qualified-target-guard-20260911`
- `repair/v5-executable-power-authority-20260911`
- `review/integrated-target-v5-repairs-*`

Do not blindly merge or delete them based on names. Earlier reconciliation showed real divergence and unique reviewed protections.

The planning branch is the canonical successor ledger now. Preserve old branches for provenance unless/until a deliberate cleanup verifies all unique work has been absorbed.

## 20. Current bottom line

Repository-side V5 is materially stronger than the earlier September-12 handoff:

- historical T0/V21 cannot authorize V5 updates;
- historical fixed 48-tensor mechanics cannot define production registry size;
- production GPU geometry is exact, data-derived and authority-bound;
- protected registry is exact and hash-bound;
- trainer and dependency closure must bind the same geometry and registry;
- stale preexecution fixtures were repaired without weakening the guards;
- exact code-bearing CI is `177 passed` plus compile PASS;
- current documentation head was also exact-head GREEN before this final handoff commit.

What is **not** done is the real-data scientific qualification. The next major phase is existing FULL104 byte rebinding and current-V5 metric execution on the GPU machine.

Do not open training early.

Do not treat a failed measurement/estimator/runtime gate as proof of absent biology.

Do not allow dataset/technology/postmortem shortcuts to masquerade as emergent disease biology.

The correct next phase is actual data qualification under the now-hardened V5 authority chain.