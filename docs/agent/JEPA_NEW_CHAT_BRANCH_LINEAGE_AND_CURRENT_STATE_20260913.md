# JEPA New-Chat Branch Lineage and Current State — 2026-09-13

Repository: `dushyant-mishra/sea-ad-jepa-agent`

This document supplements `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260913_V5_EXTERNAL_REVIEW_FINAL_CURRENT.md` with the full live branch inventory, lineage roles, current heads that materially control work, and the T0/V5 separation needed for a clean new-chat takeover.

## 1. Canonical starting point

Do **not** start from `main`.

Canonical V5 successor:

`planning/v5-dataset-first-production-closure-20260912`

Live head when this addendum was prepared:

`f87765e2644e93089ca18ce58520f1d92834f70b`

Commit:

`docs(v5): record final independent external-review verdict`

Exact-head GitHub Actions run:

`34739941880`

Conclusion:

`success`

The final independent review verdict is:

`REPOSITORY_IMPLEMENTATION_REVIEW_CLOSED__REAL_DATA_QUALIFICATION_NEXT__NO_TRAINING_AUTHORITY`

The next chat must re-fetch the live head before making any current-state claim because parallel work has landed on this branch repeatedly.

Current `main` at handoff preparation:

`ba3f2a1200d0bbaf4b9ee0d7d16ddc17341d779f`

`main` is behind the active V5 successor and does not contain the complete current V5 authority/review lineage. Branch names and merge state do not confer scientific authority.

## 2. Required first reads

1. `START_HERE.md`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260913_V5_EXTERNAL_REVIEW_FINAL_CURRENT.md`
3. this branch-lineage addendum
4. `docs/agent/JEPA_LATEST_HANDOFF_POINTER_20260913.json`
5. `docs/agent/V5_EXTERNAL_REVIEW_FINAL_VERDICT_20260913.md`
6. `docs/agent/V5_REPOSITORY_SIDE_CLOSURE_AND_CLAUDE_DATA_HANDOFF_20260912.md`
7. `docs/agent/V5_FULL104_HISTORICAL_PRODUCTION_RECOVERY_20260912.md`
8. `docs/agent/V5_FULL104_HISTORICAL_EXECUTOR_REUSE_MATRIX_20260912.md`
9. `docs/agent/V5_FULL104_CURRENT_BYTE_REBIND_WORK_ORDER_20260912.md`
10. `docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`
11. `docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`
12. `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_AMENDMENT_20260912.md`
13. `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_CONTRACT_V1.json`

## 3. What V5 means

V5 is the entire production JEPA chain, not merely dimension selection or runtime guards:

`heterogeneous human data`
`-> pathology-blind target discovery / representation qualification`
`-> authenticated FULL104 production substrate`
`-> D_shared / D_private / D_obs`
`-> teacher target / teacher authority`
`-> student objective`
`-> EMA teacher chronology`
`-> schedule / proposal / packing / restart`
`-> optimizer / protected gradients / Adam state / CUDA mechanics`
`-> atomic checkpoint and telemetry`
`-> executable anti-cheat evidence`
`-> bounded base-learning qualification`
`-> lawful learned EMA teacher`
`-> TD60`
`-> relational student qualification`
`-> integrated review`
`-> only then possible explicit production-training authority`

T0/V20/V21 is a separate methodology/test-rig lane. Transfer methodological lessons, not T0 biological targets, numerical thresholds, small-n power constants, dimensions or runtime geometry.

## 4. Full live branch inventory and roles

The live repository contained 45 branches at handoff preparation. Preserve branches for provenance until a deliberate ancestry/content audit proves their unique work is absorbed. Do not blindly merge or delete divergent branches.

### 4.1 Canonical/current V5 and V5 historical lines

- `planning/v5-dataset-first-production-closure-20260912` — **canonical current V5 successor**. Continue current work here after re-fetching the live head.
- `repair/v5-authority-evidence-integration-20260912` — reconciliation/source lane from this chat; frozen at `b2b990d4b62d838ea0627fd969615ded40ff4dd2`; protections were reconciled into the canonical successor. Preserve for provenance; do not resume as a second production lane.
- `repair/v5-installed-target-root-binding-20260912` — divergent historical repair that supplied frozen FULL104 metadata/root-binding protections. Its unique reviewed behavior was reconciled; preserve provenance.
- `repair/v5-qualified-target-guard-20260911` — historical target/runtime guard lane; became part of successor ancestry. Included zero-safe/scale-stable same-cell cosine and target-guard work.
- `repair/v5-executable-power-authority-20260911` — historical executable-power/postqualification lane. Current successor recovered the reviewed V2/V3 authority rather than trusting report booleans.
- `fix/v5-schedule-metadata-hash-revalidation-20260910` — historical schedule metadata/hash repair lineage; use as provenance, not current authority by name alone.
- `planning/v5-full-population-cheat-proofing-20260909` — historical full-population anti-cheat/preexecution development; substantial mechanics informed the successor.
- `planning/v5-preexecution-hardening-20260909` — historical preexecution dependency hardening.
- `planning/v5-pretraining-qualification-20260909` — historical qualification work; not current training authority.
- `planning/teacher-student-v5-dataset-schedule-20260909` — historical dataset schedule/EMA candidate work. Useful lineage for presentation-based biological time, but historical numeric schedule values are not current authority.
- `planning/teacher-student-v5-gpu-rng-mechanics-20260908` — historical GPU/RNG/mechanics candidate work; mechanics evidence only.
- `governance/integrated-target-discovery-v5-handoff-20260911` — governance handoff joining target discovery and V5 into one production-review chain.

### 4.2 Integrated V5 review family

These are historical independent-review/reconciliation surfaces. They are not parallel canonical production branches now:

- `review/integrated-target-v5-repairs-20260911`
- `review/integrated-target-v5-repairs-code-20260911`
- `review/integrated-target-v5-repairs-exec-20260911`
- `review/integrated-target-v5-repairs-finalwork-20260911`
- `review/integrated-target-v5-repairs-work-20260911`

Earlier branch-DAG review demonstrated real divergence in this family, so deletion/merge decisions must be content-based, not name-based.

### 4.3 T0 primary lanes

- `t0/v20-pathology-blind-materialization-20260908` — immutable V20/pathology-blind T0 lineage; historical methodology evidence.
- `t0/v21-prospective-design-20260910` — prospective V21 design line.
- `t0/v21-closeout-candidate-20260911` — current T0 closeout candidate; live head at handoff preparation remained `c22031f92b65c5aa284d40e23f9405f5f235dae0`.

### 4.4 T0 repair/review lines

- `repair/t0-v21-authority-hardening-20260911`
- `repair/t0-v21-authority-restoration-20260911`
- `repair/t0-v21-integrated-authority-regression-20260911`
- `review/t0-v21-integrated-candidate-20260911`
- `review/t0-v21-integrated-restored-20260911`
- `review/t0-v21-integrated-restored-v2-20260911`
- `review/t0-v21-successor-20260911`
- `review/t0-v20-replay-equivalence-20260910`
- `review/t0-v2-api-surface-portability-20260911`
- `review/t0-r4-dataset-bound-hardening-20260909`
- `review/t0-r4-dataset-bound-inputs-20260908`
- `review/t0-r4-independent-reds-20260909`
- `review/t0-r4-independent-review-20260909`
- `review/t0-r5-dataset-chain-hardening-20260909`
- `review/t0-r5-dataset-first-framework-20260909`
- `review/t0-r5-external-hardening-20260909`
- `docs/t0-closeout-handoff-20260911`
- `handoff/jepa-t0-v2-claude-ready-20260911`

These branches preserve T0 methodology, authority restoration and independent-review history. They do not authorize V5 biology or production training.

### 4.5 F1 historical line

- `fix/f1-review-closeout-20260911` — historical F1 review/closeout lineage. Retain because the old QID/matched-null semantic gap remains a historical estimand/authority lesson; do not automatically import that estimand into V5.

### 4.6 Governance / lineage / handoff branches

- `governance/project-lineage-reconstruction-20260911` — project lineage/governance reconstruction.
- `handoff/jepa-new-chat-20260910-t0-v21-v5`
- `handoff/jepa-new-chat-20260911-asap-repair-status`
- `handoff/jepa-new-chat-20260911-post-v21-repair-current`
- `handoff/jepa-new-chat-r2-20260908`
- `handoff/jepa-new-chat-20260913-full-lineage-current` — provenance branch used to prepare this addendum from the current reviewed V5 head.

These handoff branches are documentary/provenance aids, not scientific authority surfaces.

### 4.7 Main

- `main` — live head `ba3f2a1200d0bbaf4b9ee0d7d16ddc17341d779f` at handoff preparation. It is **not** the current V5 implementation ledger. Do not reset current work to `main`.

## 5. What was completed in the September 12–13 V5 successor

### 5.1 Dataset/FULL104 authority

- stale 42-shard TRAIN -> FULL104 authority loophole closed;
- canonical payload hashing and exact parent binding added;
- physical FULL104 expression authority required; row-identity-only closure cannot substitute;
- frozen metadata SQLite authority enforced;
- same metadata authority propagated through schedule/proposal/restart;
- real FULL104 -> dimension input interface exists;
- historical FULL104 is treated as already materialized and exercised, so the next data task is locate/hash/rebind, not rebuilding 4.55M cells.

### 5.2 Dimension authority machinery

- `derive_full_stream_dimension_family_v1.py` exists;
- D_shared uses supported cumulative prefixes and explicit held-donor predictability;
- one-SE selection may select a lower supported rank than the longest supported prefix;
- D_shared=0 is lawful;
- D_private is incremental and must descend from exact frozen D_shared;
- D_obs is separate observation-state rank with no biological claim;
- metric and selection artifacts are hash-bound;
- `DimensionExecutionFirewallV1` / `DimensionAuthorityV4` remain downstream gates;
- no production numeric D_shared/D_private/D_total/D_obs authority exists yet.

### 5.3 Runtime/teacher/student/EMA hardening

- historical T0/V21 target receipt is mechanics/forensics-only and cannot authorize current V5 teacher/student runtime;
- current V5 runtime requires dataset-derived current teacher authority and explicit current runtime configuration;
- historical V4 width/batch/microbatch/mask/target-block/EMA constants are not current V5 authority;
- presentation-based EMA primitive is reusable, but its half-life must be frozen prospectively;
- production protected registry is now model-depth-derived rather than fixed at historical 48 tensors;
- exact protected-registry identity is canonicalized and hash-bound;
- current protected mechanics chain requires fp16 forward, backward autocast disabled, unscale, protected-gradient gate, movement beyond decay, both Adam moments, EMA, successful-presentation cursor, atomic checkpoint telemetry.

### 5.4 GPU/preexecution/checkpoint anti-splice hardening

- production GPU evidence must bind exact FULL104, dimensions, proposal, packing/restart, representation firewall, protected registry and update geometry;
- historical 128x8 C2/V4 mechanics is supporting-only;
- real FULL104 reader batch and exact production geometry must be demonstrated;
- trainer preexecution V4 binds the same update-geometry authority and protected registry as the dependency closure;
- mismatched geometry/registry stops fail-closed;
- `atomic_checkpoint_guard_v3.py` binds thresholds, registry, mechanics chain, EMA chronology, critical tests and executable postqualification evidence;
- lower JEPA loss cannot hide biology degradation, shortcut ascent or transfer degradation.

### 5.5 Executable postqualification authority

Current seven rejection-capable gate names are exactly:

1. `donor_recurrence_validation`
2. `heldout_biology_validation`
3. `qc_measurement_confounding_closure`
4. `same_cell_technical_intervention`
5. `shortcut_superiority`
6. `student_representation_collapse`
7. `teacher_representation_collapse`

Current authority requires executable/raw-output/hash-bound evidence rather than caller booleans. Full production producers at adjudication geometry remain work to execute/complete on real geometry.

## 6. Final external-review cycle

The user requested a fresh review pretending to be three external experts: computational biologist, AI/JEPA engineer and scientist/statistical reviewer.

The final review found and repaired actual repository defects rather than weakening gates:

- quarantined legacy T0/V21 runtime authority leakage;
- removed the historical fixed 48-tensor protected-registry assumption;
- made the production mechanics chain explicit;
- prevented GPU evidence from self-declaring production geometry;
- closed trainer/dependency geometry and protected-registry anti-splice gaps;
- preserved the stronger production invariant when a stale test fixture went RED; the fixture, not the guard, was repaired.

Code-bearing reviewed head:

`a388c773feb48ebf3fc6ce20b8782182abc1891b`

Verified CI:

`34739456264` -> `177 passed`, authority-source compile PASS.

Final current documentation/review head:

`f87765e2644e93089ca18ce58520f1d92834f70b`

Exact-head CI:

`34739941880` -> success.

Final verdict document:

`docs/agent/V5_EXTERNAL_REVIEW_FINAL_VERDICT_20260913.md`

Verdict:

`REPOSITORY_IMPLEMENTATION_REVIEW_CLOSED__REAL_DATA_QUALIFICATION_NEXT__NO_TRAINING_AUTHORITY`

No additional repository implementation defect was demonstrated that should be patched before real-data execution. Open items now require authenticated data/model execution or prospective scientific choices; inventing constants to make the repo look complete would violate dataset-first design.

## 7. FULL104 historical production substrate

Expected physical root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical geometry:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / matrices
- 8,915 Level-4 expression blocks
- 41,238 molecular addresses
- 17,186 common measured-core addresses
- 1,400 donor x operator groups
- 1,361 groups >=3 cells, 99.9987% of cells

Frozen hashes:

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

Historical FULL104 ALL implementation fingerprint:

`a0fe5bc7be0769c9880763b3831ea330a251dfa710a8635b05f678c5d6e94202`

Historical terminal manifest:

`8f292673c84447ee88f3a78936aa88920b96f0ffd681237e2b5af3e7dfe4d60c`

Historical scientific terminal `TEACHER_BIOLOGY_LIMIT` is narrow: no shared dimension qualified under that old estimand/procedure. It is not evidence that FULL104 lacks biology and is not current V5 numeric authority.

## 8. T0 current methodology state

Live T0 closeout candidate at handoff preparation:

`t0/v21-closeout-candidate-20260911 @ c22031f92b65c5aa284d40e23f9405f5f235dae0`

That committed evidence corrected the earlier conditional-vs-unconditional AUC interpretation:

ULS true-vs-NULL AUC:

- STRONG: 0.992 conditional -> 0.636 unconditional
- MODERATE: 0.935 -> 0.601
- WEAK: 0.735 -> 0.532

The later nested synthetic run completed locally but had not reached GitHub at handoff preparation. Reported ULS end-to-end n=28 results were:

- STRONG: PASS 0.025; improper 0.17; mean bootstrap nonconvergence 0.358
- MODERATE: PASS 0; improper 0.33; mean bootstrap nonconvergence 0.458
- WEAK: PASS 0; improper 0.53; mean bootstrap nonconvergence 0.501
- NULL: PASS 0; improper 0.42; mean bootstrap nonconvergence 0.522

Correct interpretation:

`T0 n=28 MEASUREMENT PROCEDURE NOT QUALIFIED`

`BIOLOGICAL COMMON FACTOR UNRESOLVED, NOT REJECTED`

Do not claim tau biology absent.

Important retractions/lessons:

- conditional AUC cannot be presented as end-to-end operating characteristics;
- the n≈100 extrapolation based on conditional-AUC multiplication is retracted;
- bootstrap intervals over surviving converged refits are not unconditional sampling uncertainty when failures are informative;
- convergence/improper rate is not monotone enough to promote as construct evidence;
- the 0.375 NULL value from the local nested evidence is an intermediate steps-1–5 candidate-selection frequency unless terminal ordering proves more; do not automatically call it 37.5% final false qualification;
- no omega floor was added and the 5% constant was not retrospectively changed.

T0 is a test rig. Do not spend V5 authority by trying to rescue T0.

## 9. Mixed-cohort scientific intent and confounding threat

The production corpus was deliberately acquired across normal, aging, pathological-aging, disease, living/postmortem, region, age, sex, study and sequencing/measurement technology so disease biology can emerge rather than be supplied as a training label.

This creates a severe shortcut risk:

`disease ~ dataset/source ~ technology ~ living/postmortem ~ region`

Therefore a pooled disease trajectory alone is insufficient.

Later biological promotion should require where supported:

- within-study disease-spectrum emergence/replication;
- matched donor/region/platform contrasts;
- attacks for dataset/source/operator/matrix/batch/technology/living-postmortem/PMI/region/sex/age/depth/support-family;
- same-cell biology-preserving technical interventions;
- biology-corrupted / technology-preserved negatives;
- technical-only controls;
- randomized/matched-null controls;
- explicit influence/contribution concentration diagnostics.

Standing protected-data rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## 10. Permanent interpretation and denominator rules

Keep distinct:

- `MEASUREMENT_MODEL_FAILED`
- `ESTIMATOR_FAILED`
- `NOT_ESTIMABLE`
- `MC_PRECISION_INADEQUATE`
- `REPRESENTATION_FAILED`
- `TECHNICAL_CONFOUNDING_UNRESOLVED`
- `INFLUENCE_UNSTABLE`
- `INCREMENTAL_PREDICTION_NOT_DEMONSTRATED`
- `BIOLOGICAL_NECESSITY_NOT_DEMONSTRATED`
- `TRANSPORT_NOT_VALIDATED`
- `CONFIRMATION_NOT_AUTHORIZED`
- `TARGET_NOT_QUALIFIED`
- a genuine qualified biological negative

A zero is not automatically absence of biology.

Decision-bearing metrics must be unconditional over the declared evaluation population. Failed fits, undefined comparisons, zero-gradient units, missing support, non-estimable donors and failed perturbations do not silently disappear from the denominator. Conditional statistics are diagnostic only.

## 11. Exact next operational sequence

### GPU/heavy-data machine / Claude

1. Re-fetch the live canonical V5 branch.
2. Locate existing historical FULL104 Level-4 bytes; do not rematerialize by default.
3. Verify frozen historical parent hashes.
4. Run the hardened binder per `V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`.
5. Require terminal `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`.
6. Seal `V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json`.
7. Before inspecting current numeric dimension outcomes, freeze metric-specific Monte-Carlo/donor-resample precision authority; do not inherit 256/999/1000.
8. Independently review D_private/D_obs candidate selection rules before outcome-dependent revision is possible.
9. Run current-V5 full-stream D_shared metric executors over authenticated FULL104.
10. Adjudicate D_shared.
11. Only after D_shared freezes, execute/adjudicate D_private.
12. Compute D_total = D_shared + D_private.
13. Execute/adjudicate D_obs separately.
14. Pass DimensionExecutionFirewall / DimensionAuthority.
15. Derive schedule/proposal/packing and model/update geometry from authenticated data and frozen dimensions.
16. Freeze presentation-based EMA authority prospectively; do not inherit 0.996.
17. Run production-geometry CUDA qualification with exact protected registry and mechanics chain.
18. Close preexecution dependency bundle.
19. Run bounded base-learning-step qualification.
20. Establish lawful dataset-derived EMA teacher.
21. Only then run TD60.
22. Only after TD60 plus prospective partial-evidence relational-predictability qualification, activate relational student qualification.
23. Integrated independent review.
24. Only then consider explicit production-training authority.

### Lightweight/repository environment

Repository implementation review is closed unless a new demonstrated defect appears. Do not invent additional constants or redesign for appearance of completeness. If a new defect is demonstrated, use:

`RED -> minimal fix -> GREEN -> adversarial mutation -> exact-head relevant suite`

## 12. Hard boundaries

Remain closed unless a new explicit authority artifact says otherwise:

```text
V5_FULL104_EXPRESSION_CLOSURE = FALSE until real binder receipt
V5_PRODUCTION_TRAINING_AUTHORIZED = FALSE
training_authorized = false
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

No green CI, branch name, FULL104 binder PASS, numeric dimension receipt, CUDA mechanics result or bounded qualification automatically changes these authority flags.

## 13. Bottom line for the new chat

The repository-side V5 implementation has completed a fresh three-perspective external review and is exact-head green at `f87765e...`. The next scientifically meaningful phase is real-data qualification on the authenticated historical FULL104 substrate, beginning with byte/hash rebinding on the GPU machine.

Do not restart architecture design from scratch.

Do not use `main` as the current implementation ledger.

Do not import T0/V4 numbers into V5.

Do not interpret failed measurement/estimator/runtime gates as absence of biology.

Do not let dataset/technology/postmortem shortcuts masquerade as emergent disease biology.
