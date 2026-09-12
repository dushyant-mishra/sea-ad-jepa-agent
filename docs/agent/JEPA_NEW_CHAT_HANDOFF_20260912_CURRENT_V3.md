# JEPA new-chat handoff — current V3

Date: 2026-09-12
Repository: `dushyant-mishra/sea-ad-jepa-agent`

Status:
`DATASET_FIRST_V5_PRODUCTION_QUALIFICATION_IN_PROGRESS__FULL104_HISTORICALLY_PREPARED__CURRENT_REBIND_AND_NEW_V5_QUALIFICATION_REQUIRED__NO_TRAINING_AUTHORITY`

## 0. Exact current branch state

Primary working branch:

`planning/v5-dataset-first-production-closure-20260912`

Verified live head immediately before this handoff was created:

`57cad11160615518f326a4b882c2d2bc4e4c3a3d`

Important CI nuance:

- The latest code-bearing baseline referenced by the current V2 handoff was
  `2c278364a5717e4248ac65ae8107754fbc625d1d`.
- GitHub Actions run `34699776996` completed SUCCESS on that exact code-bearing head.
- The recorded verified suite at that point was `103 passed` plus authority-source compile PASS.
- The three commits from `2c278364...` to `57cad111...` are documentation-only:
  - `JEPA_NEW_CHAT_HANDOFF_20260912_CURRENT_V2.md`
  - `JEPA_NEW_CHAT_STATE_20260912_CURRENT_V2.json`
  - `CLAUDE_COMPREHENSIVE_WORK_ORDER_20260912.md`
- Therefore no production code changed after the last verified code-bearing head.

Re-fetch the live branch before every write because this branch is active.

The original V5 repair branch remains preserved:

`repair/v5-qualified-target-guard-20260911`

Do not mutate it.

---

# 1. Startup instructions for the new chat

Do not restart the project from scratch.

First:

1. Connect to GitHub repo `dushyant-mishra/sea-ad-jepa-agent`.
2. Re-fetch live heads.
3. Read `START_HERE.md`.
4. Read this handoff fully.
5. Then read:
   - `docs/superpowers/specs/2026-09-12-v5-dataset-first-production-closure-design.md`
   - `docs/agent/V5_FULL104_HISTORICAL_PRODUCTION_RECOVERY_20260912.md`
   - `docs/agent/V5_FULL104_HISTORICAL_EXECUTOR_REUSE_MATRIX_20260912.md`
   - `docs/agent/V5_FULL104_CURRENT_BYTE_REBIND_WORK_ORDER_20260912.md`
   - `docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`
   - `docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`
   - `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_AMENDMENT_20260912.md`
   - `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_CONTRACT_V1.json`
   - `docs/agent/CLAUDE_COMPREHENSIVE_WORK_ORDER_20260912.md`
   - `scripts/v5_anticheat/validate_base_learning_step_qualification_v1.py`
   - `scripts/v5_anticheat/validate_full104_execution_plan_v1.py`
   - `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`
   - `scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py`
   - the current Target Discovery→V5 integration authority at its live path.
6. Keep training OFF.
7. Keep reader_validation, reader_oracle, pathology, AT8, and protected confirmation closed.
8. Do not activate TD60 or relational training without explicit later authority.

Standing rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

Permanent lane separation:

`FOUNDATION_TARGET_DISCOVERY_TD13_TD60_IS_NOT_T0_V18_V20_V21`

`T0_METHOD_DEVELOPMENT_INFORMS_FOUNDATION_TARGET_DISCOVERY_AND_V5_CHEAT_PROOFING_WITHOUT_SUPPLYING_THE_BIOLOGICAL_TARGET`

---

# 2. Dataset-first governing principle

The pipeline must be built around the dataset we actually have.

Correct order:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Do not choose convenient model geometry and force FULL104 into it.

Synthetic fixtures are for mechanics/fail-closed testing only.

Historical 50K discovery data, the 3,292-cell mechanics inventory, and the corrected 4,726-row TRAIN cache are not substitutes for FULL104 production authority.

---

# 3. Critical FULL104 historical correction

FULL104 was NOT an unbuilt dataset.

Historical production preparation and use already occurred.

Recovered historical geometry:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / 42 matrices
- 8,915 Level-4 expression blocks
- 41,238 molecular addresses
- 17,186 common measured-core addresses
- 1,400 donor×operator groups
- 1,361 / 1,400 groups have >=3 cells and contain 99.9987% of reader-fit cells

Historical physical root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical materialization lineage includes frozen materialization contracts, asset authentication, block manifests, audits, materialization scripts, Level-4 feature/multiview packages, the old full-population ALL executor, and independent reconstruction/adjudication.

Important frozen hashes:

- block manifest: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- materialization contract: `612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17`
- materialization audit: `9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf`
- selection: `edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b`
- selection manifest: `3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e`
- metadata SQLite: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

Historical downstream package roots:

- Level-4 feature-matrix package root: `c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef`
- Level-4 multiview-feature package root: `d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1`

Historical FULL104 shared-state ALL execution was completed and independently adjudicated.

Final old result:

`TEACHER_BIOLOGY_LIMIT`

That result is narrow. It says the prospectively frozen historical shared-state estimand failed its qualification rule. It does NOT mean the dataset lacks biology and it is NOT the new V5 numeric-dimension authority.

Current FULL104 task:

`RECOVER/LOCATE EXISTING BYTES -> VERIFY -> CURRENT V5 REBIND`

NOT rematerialization from scratch.

---

# 4. Current FULL104 rebind path

Use:

`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Required current V5 terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Work orders:

- `docs/agent/V5_FULL104_CURRENT_BYTE_REBIND_WORK_ORDER_20260912.md`
- `docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`

Return only compact receipts and hashes.

If historical bytes fail current integrity checks, STOP and record the mismatch. Do not silently regenerate or substitute.

---

# 5. Historical executor reuse work

Do not write a new full-stream engine from scratch before auditing/reusing historical engineering patterns.

Read:

`docs/agent/V5_FULL104_HISTORICAL_EXECUTOR_REUSE_MATRIX_20260912.md`

Reusable engineering patterns already identified include complete-manifest authentication, coordinate separation, same-byte hash/parse/consume coupling, anti-splice parent binding, physical-plan-to-logical restoration, external pre-result run authority, atomic shard publication, strict resume completeness, produced-byte closure roots, independent replay/reconstruction, tracked-source vs untracked-data byte classes, and binding actual loaded runtime assets.

Do NOT inherit old biology, QID semantics, rank limits, thresholds, historical execution authority, cap-4 sampling, rank-32 ceilings, or historical replicate counts.

After physical-byte PASS, validate the execution-plan receipt with:

`scripts/v5_anticheat/validate_full104_execution_plan_v1.py`

---

# 6. V5 mechanics/provenance completed on the successor branch

Completed or materially repaired:

1. stale 42-shard TRAIN cache cannot masquerade as FULL104;
2. physical 8,915-block binder is the only production FULL104 closure;
3. canonical artifact serialization / SHA-256 / parent binding exists;
4. real FULL104 receipts can be sealed into exact dimension-input artifacts;
5. metadata SQLite digest is pinned;
6. row-identity-only closure cannot substitute for physical expression closure;
7. `derive_full_stream_dimension_family_v1.py` now exists;
8. D_shared uses consecutive cumulative prefixes, explicit held-donor predictability, joint support, one-SE selection, lawful zero, and search-boundary expansion;
9. the dimension firewall now correctly allows one-SE-selected D_shared below the longest jointly supported prefix;
10. D_private has an outcome-blind prospective candidate selector;
11. D_obs has an outcome-blind held-operator reconstruction selector;
12. metric artifacts bind score rows to exact FULL104 input + execution receipt;
13. D_private additionally binds to the exact frozen D_shared selection;
14. selection artifacts bind decisions to exact metric artifacts;
15. runtime optimizer/target guard remains resident/fail-closed with cursor and target-root binding;
16. same-cell cosine edge cases are covered;
17. successor CI workflow exists.

---

# 7. Numeric dimension authority is NOT closed

No production numeric `D_shared`, `D_private`, `D_total`, or `D_obs` has been frozen.

Remaining blockers:

- current-byte FULL104 rebind;
- real full-stream current-V5 metric executors;
- prospective Monte-Carlo/resample precision authority;
- independent review of D_private/D_obs candidate rules.

D_shared metrics required:
- full-refit matched-null signal;
- donor-resampled subspace stability;
- held-donor cross-view prediction + SE;
- independent-view/sketch agreement;
- measurement-shortcut increment.

D_private only after D_shared freezes:
- held-donor incremental biology;
- held-operator increment;
- measurement-shortcut increment;
- same-cell technical-intervention stability.

D_obs:
- held-operator reconstruction of lawful observation descriptors only;
- source/matrix identity is not a target.

Do not inherit historical 256/999/1000 replicate counts.

---

# 8. Base-learning-step qualification

A new upstream gate prevents scientific promotion of a learner merely because mechanics look healthy.

Read:

- `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_AMENDMENT_20260912.md`
- `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_CONTRACT_V1.json`
- `scripts/v5_anticheat/validate_base_learning_step_qualification_v1.py`

Comparator classes:

- `NO_LEARNED_SIGNAL_OR_LIMITING_OBJECT`
- `TECHNICAL_ONLY_OR_IDENTITY_ONLY`
- `RANDOMIZED_OR_MATCHED_NULL`

Pass terminal:

`PASS_BASE_LEARNING_STEP_QUALIFICATION__NO_TRAINING_AUTHORITY`

Evidence-producing runs require separate exact scope:

`BOUNDED_READER_FIT_LEARNING_STEP_QUALIFICATION_ONLY`

Protocol freeze != run authority.
Bounded qualification != production training.
Even PASS does not automatically authorize TD60.

---

# 9. T0-derived methodology gaps relevant to V5

Last reported T0 branch in the current handoff lineage:

`t0/v21-closeout-candidate-20260911 @ 5e01e54957c5f8627d9862b1be5078a8cfcc6818`

Re-fetch before use.

T0 remains biologically separate but methodologically informative.

Three V5 framework gaps identified:

1. measurement-model / target-distribution qualification before objective choice;
2. simpler/limiting comparator + full curve;
3. first-class influence-concentration diagnostics.

Gap 2 is now structurally addressed by the base-learning-step qualification gate, pending real evidence.

Gaps 1 and 3 remain to be built prospectively.

Do not import T0 numerical thresholds into V5.

---

# 10. Target Discovery state

Target Discovery is not T0.

- TD57B global recurrence: PASS 24/24
- TD57C nearest-third locality: FAIL; failure stands
- TD59 nearest-half mesoscale: PASS 24/24, pilot only
- TD60: prospective learned-teacher continuity gate

TD60 requires direct cell-state cosine and exact frozen TD57B/TD59 semantics:

- 24/24 global
- 24/24 mesoscale
- 48/48 total

Do not inherit nearest-half as production locality.
Do not reactivate nearest-third as primary.
TD60 requires a lawful exposure-defined base teacher first.
Relational target activation remains OFF.

---

# 11. Anti-cheat/runtime work still open

Need executable two-sided evidence producers for:

- donor identity;
- source/operator/batch/library/depth;
- specimen;
- same-cell leakage;
- shared-view leakage;
- duplicate/lookup;
- technical-only;
- corrupted-biology;
- biology-preserved / technology-perturbed;
- shortcut superiority;
- collapse.

Each rejection-capable gate should accept a minimally valid control and reject a minimally invalid control at exact adjudication geometry with raw-output hashes.

Caller-supplied booleans are not evidence.

---

# 12. Production-geometry CUDA

Validator exists; real production-geometry runner remains downstream.

Must eventually use real FULL104 data and data-derived geometry and prove:

- protected gradients live elementwise;
- parameter motion beyond decay;
- both Adam moments live;
- EMA update;
- atomic checkpoint/telemetry commit.

Historical 128x8 CUDA evidence is mechanics regression only.

---

# 13. Current Claude work order

Read:

`docs/agent/CLAUDE_COMPREHENSIVE_WORK_ORDER_20260912.md`

Main workstreams:

1. extend FULL104 historical executor reuse audit;
2. prospective Monte-Carlo precision authority;
3. measurement-model qualification;
4. influence-concentration diagnostics;
5. preserve/extend base-learning-step qualification;
6. real current-V5 dimension metric executors;
7. current FULL104 byte rebind when heavy drive is available;
8. executable anti-cheat evidence producers;
9. preserve current dimension mechanics;
10. preserve Target Discovery/TD60 activation boundaries.

Do not let parallel agents edit the same authority surface concurrently.

---

# 14. Recommended next-chat order

1. Re-fetch live head and exact CI state.
2. Extend the FULL104 historical executor reuse matrix.
3. Freeze the Monte-Carlo/resample precision rule under TDD.
4. Design measurement-model/target-distribution qualification with negative controls.
5. Design influence-concentration diagnostics with tests.
6. Build the first real current-V5 full-stream metric executor by reusing only semantically compatible historical machinery.
7. When the heavy drive is available, execute the exact current-byte FULL104 rebind and return the compact receipt.
8. Continue executable anti-cheat producers.
9. Do not run a learned FULL104 candidate without explicit bounded qualification-run authority.
10. Do not run TD60 without lawful base-teacher authority.

Iterative process:

- identify exact defect/hypothesis;
- write failing test/negative control;
- record RED;
- minimal root fix;
- focused GREEN;
- full exact-head suite;
- semantic self-review;
- mutation/adversarial test where appropriate;
- clean replay where relevant;
- small commit;
- re-fetch exact head;
- record exact tests/hashes.

---

# 15. Hard boundaries

`training_authorized = false`

`protected_data_authorized = false`

`reader_validation_closed = true`

`reader_oracle_closed = true`

`pathology_closed = true`

`td60_authorized = false`

`relational_target_activation_authorized = false`

No protected confirmation may be inspected while design choices remain mutable.

---

# 16. One-paragraph summary

FULL104 was historically materialized and exercised at full scale; the present task is to recover/rebind those exact bytes to the current V5 authority chain and run new V5 qualification rather than rebuild the dataset or reuse the old shared-state conclusion. The current successor branch has closed major mechanics/provenance gaps around stale TRAIN escalation, artifact binding, FULL104 sealing, D_shared selection/firewall semantics, prospective D_private/D_obs selectors, metric provenance, execution-plan validation, and base-learning-step qualification. The primary open scientific/engineering work is the prospective Monte-Carlo precision rule, measurement-model qualification, influence diagnostics, real full-stream V5 metric executors, executable anti-cheat evidence, current-byte FULL104 rebind on the heavy-data machine, production CUDA qualification, then lawful base EMA teacher -> TD60 -> partial-evidence relational qualification. Training and protected data remain closed.
