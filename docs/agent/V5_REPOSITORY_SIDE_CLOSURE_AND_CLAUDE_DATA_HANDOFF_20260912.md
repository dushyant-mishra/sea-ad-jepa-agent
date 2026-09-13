# V5 repository-side closure and Claude real-data handoff — 2026-09-12

Status: `REPOSITORY_SIDE_V5_RECONCILIATION_CLOSED__FULL104_REAL_DATA_EXECUTION_NEXT__NO_TRAINING_AUTHORITY`

This handoff closes the repository-side V5 branch reconciliation performed after reviewing the September 11–12 V5 repair/review lineages and the detailed project handoffs. It does **not** claim current FULL104 byte closure, numeric V5 dimensions, bounded-run authority, TD60 authority, relational-target authority, or production-training authority.

## 1. Working lineage

Canonical successor to continue on:

`planning/v5-dataset-first-production-closure-20260912`

Repository-side reconciliation source branch:

`repair/v5-authority-evidence-integration-20260912`

The planning branch is to be fast-forwarded to the final reconciliation head after this handoff is committed and verified. Do not restart from older repair branches. Preserve the reconciliation branch for provenance.

The last freshly verified **code-bearing** reconciliation head before handoff-only documentation was:

`484fdc6bed5df5b873056d0c381f74dca357162d`

GitHub Actions run:

`34733152678`

Exact result:

- V5 integration regression suite: `106 passed`
- V5 reconciliation regressions: `16 passed`
- authority-source compilation: PASS

The later handoff/CI-only commits must also be green before the planning branch is declared ready.

## 2. Repository-side repairs now present

### A. FULL104 metadata/root authority is frozen

Production FULL104 binding no longer accepts a caller-selected metadata authority. The authenticated metadata SQLite SHA is:

`a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py` binds the real Level-4 block store to this exact metadata identity plus the frozen block manifest, materialization contract/audit, reader-fit selection and selection manifest.

Unit fixtures use only private underscored overrides. Production CLI callers cannot substitute a different metadata SHA.

### B. Schedule/proposal/restart chain uses the same metadata authority

A reconciliation audit found that schedule optimization, schedule materialization and proposal/restart replay could previously accept a caller-chosen matching metadata SHA. A self-consistent alternate metadata database could therefore have minted a schedule even while downstream expression authority came from the real FULL104 store.

This is closed with:

`src/sea_ad_jepa/v5/full104_metadata_authority_v1.py`

The same frozen SHA is now enforced by:

- `scripts/v5_anticheat/derive_full_population_schedule_optimum_v3.py`
- `scripts/v5_anticheat/materialize_full_population_schedule_v4.py`
- `scripts/v5_anticheat/audit_full_population_proposal_weight_restart_v1.py`
- `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Public alternate metadata authority is rejected before production file use. Fixture overrides are private/test-only.

Expanding schedule tests also exposed and repaired a latent restart-replay syntax defect that had not previously been executed in this CI lane.

### C. Executable postqualification authority recovered

The successor now includes the previously divergent reviewed layers:

- `src/sea_ad_jepa/v5/postqualification_dependency_guard_v2.py`
- `src/sea_ad_jepa/v5/qualification_phase_contract_v3.py`

Postqualification eligibility cannot be manufactured by report assertions alone. It requires the current executable-power V4 receipt, frozen-gate execution, raw output bindings, exact code identities and independent recomputation.

The current rejection-capable postqualification gate set is exactly:

1. `donor_recurrence_validation`
2. `heldout_biology_validation`
3. `qc_measurement_confounding_closure`
4. `same_cell_technical_intervention`
5. `shortcut_superiority`
6. `student_representation_collapse`
7. `teacher_representation_collapse`

### D. Current-authority atomic checkpoint guard restored

New successor:

`src/sea_ad_jepa/v5/atomic_checkpoint_guard_v3.py`

It restores the useful invariants of the historical checkpoint V2 guard without reviving obsolete V1 authority vocabulary. It requires:

- exact `TrainerPreexecutionAuthorityV2` authority SHA bundle;
- checkpoint-threshold SHA bound to the preexecution authority;
- no checkpoint-threshold defaults;
- exact `MECHANICS_CHAIN_V2` chronology;
- exact 48-tensor protected-registry identity for gradients, parameter motion beyond decay and both Adam moments;
- successful-base-cell-presentation EMA before/current/after chronology;
- every current critical test `EXECUTED_PASS` — skip is not pass;
- the exact current seven postqualification gates, each `EXECUTED_PASS`, hash/authority bound and `training_authorized=false`;
- proposal/evidence/depth/hardware telemetry PASS;
- protected/forbidden gates closed;
- collapse protection even when JEPA loss worsens;
- lower JEPA loss cannot conceal biology degradation, shortcut ascent or held-out transfer degradation.

The output remains `production_training_authorized=false`.

### E. CI now protects the recovered union

The integration workflow covers the recovered metadata, schedule, postqualification and checkpoint protections.

The planning-successor workflow `.github/workflows/v5_dataset_first_production_closure.yml` has also been expanded so these protections remain continuously tested after the planning branch is fast-forwarded.

## 3. Correct FULL104 historical state

FULL104 was historically materialized and exercised. Do **not** rematerialize it merely because ChatGPT cannot see the heavy bytes.

Expected historical physical root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Recovered production geometry:

- reader-fit cells: `4,553,407`
- donors: `104`
- operators / matrices: `42 / 42`
- Level-4 expression blocks: `8,915`
- molecular addresses: `41,238`
- common measured-core addresses: `17,186`
- donor × operator groups: `1,400`
- groups with >=3 cells: `1,361`, containing `99.9987%` of reader-fit cells

Frozen parent hashes:

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

Historical FULL104 `ALL` implementation fingerprint:

`a0fe5bc7be0769c9880763b3831ea330a251dfa710a8635b05f678c5d6e94202`

Historical terminal run-manifest SHA:

`8f292673c84447ee88f3a78936aa88920b96f0ffd681237e2b5af3e7dfe4d60c`

Historical scientific terminal `TEACHER_BIOLOGY_LIMIT` applies only to that old shared-state estimand. It is **not** evidence that FULL104 lacks biology and is not current V5 numeric-dimension authority.

## 4. Exact first real-data operation

Read and execute:

`docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`

The command in that document is aligned to the hardened binder: there is intentionally no public `--expected-metadata-sha256` flag.

The only accepted real production binder terminal is:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Then seal:

`V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json`

Return compact hashes/receipts only. Do not upload/copy the >30 GB block store.

If any historical byte/hash differs, STOP. Do not silently substitute TRAIN, 50K, another cache or newly reconstructed bytes.

## 5. What remains after physical FULL104 rebind

These are real-data/scientific execution tasks, not reasons to redesign the repository from scratch.

### A. Current-V5 full-stream metric executors

Audit and reuse the historical FULL104 streaming, sufficient-statistic, checkpoint/restart, deterministic-null, storage and independent-reconstruction machinery where semantically compatible. Reuse mechanics, **not** historical biological semantics, cap-4 shortcuts, QID assumptions, fixed ranks, thresholds or replicate counts.

Required `D_shared` metrics over authenticated FULL104:

- signal above a **fully refit** matched null;
- donor-resampled subspace stability;
- held-donor cross-view predictability plus donor-level SE;
- independent view/sketch agreement;
- increment beyond frozen measurement-shortcut baselines.

Selecting nulls must preserve donor/operator/Q_DEPTH/Q_DETECT/support-measurability and refit the complete selecting geometry.

Only after `D_shared` freezes, required `D_private` metrics:

- held-donor incremental common-core biology prediction;
- held-operator increment;
- measurement-shortcut increment;
- same-cell technical-intervention stability.

`D_obs`:

- held-operator reconstruction of lawful observation descriptors;
- source/matrix identity are neither free inputs nor reconstruction targets;
- no biological qualification claim.

Raw metric outputs must be hash-bound to their exact FULL104 input and execution receipts before selection.

### B. Prospective Monte-Carlo / donor-resample precision authority

Do **not** inherit historical `256`, `999`, `1000`, or any convenient replicate count.

Before current V5 dimension outcomes are examined, freeze and test a metric-specific rule defining:

1. the Monte-Carlo quantity being controlled;
2. tolerated error;
3. family-wise/risk budget across ranks/views/gates;
4. the exact replicate-count formula or predeclared stopping rule;
5. hard min/max bounds if sequential;
6. deterministic RNG and exact replay semantics.

Decision-bearing results must be unconditional over the declared evaluation population. Failed/undefined/non-estimable units may not disappear into a conditional-on-success statistic.

### C. Independent candidate-rule review

Before numeric authority:

- independently review `V5_D_PRIVATE_SELECTION_RULE_CANDIDATE_V1.json`;
- independently review `V5_D_OBS_SELECTION_RULE_CANDIDATE_V1.json`.

Do not revise them after seeing current FULL104 outcomes merely to obtain a preferred rank.

## 6. After real dimensions close

Proceed in this order:

1. `D_shared` adjudication;
2. `D_private` adjudication only after frozen `D_shared`;
3. `D_total = D_shared + D_private`;
4. `D_obs` adjudication;
5. pass `DimensionExecutionFirewallV1` and `DimensionAuthorityV4`;
6. derive actual scientific schedule/proposal/packing from authenticated metadata and dimensions;
7. freeze **presentation-based** EMA authority — do not inherit historical fixed momentum `0.996`;
8. run real production-geometry CUDA qualification;
9. close the preexecution dependency bundle;
10. run the bounded base-learning-step qualification;
11. establish a lawful base EMA teacher;
12. only then run TD60;
13. only after TD60 plus the prospective partial-evidence relational-predictability gate, qualify the relational student extension;
14. independent integrated review;
15. only then consider an explicit production-training authority.

The historical V4 runtime values (`width=160`, effective batch `128`, microbatch `8`, views `4`, mask fraction `0.40`, target blocks `16`, EMA momentum `0.996`) are historical mechanics regression values, **not** current dataset-first V5 production geometry authority.

The reusable EMA primitive is exposure-defined biological time:

`m = exp(log(0.5) * presentations_this_update / half_life_presentations)`

The half-life itself must be separately frozen from lawful V5 authority; it is not selected here.

## 7. T0 lessons that transfer — numbers do not

T0 is a methodology/test rig. Do not import T0 biological targets, numerical thresholds, power constants or small-n conclusions into V5.

Transfer these rules:

- conditional-on-success performance is diagnostic; decision-bearing performance is unconditional over the declared evaluation population;
- estimator/measurement failure is not biological absence;
- `NOT_ESTIMABLE`, `ESTIMATOR_FAILED`, `REPRESENTATION_FAILED`, `TECHNICAL_CONFOUNDING_UNRESOLVED`, `BIOLOGY_NOT_DEMONSTRATED` and a genuine qualified biological negative are distinct outcomes;
- numerical repair may not manufacture scientific qualification;
- no post-hoc threshold tuning after seeing which direction helps;
- procedure qualification must use actual production geometry or a prospectively justified geometry-matched falsification study;
- a low loss or apparently stable successful subset is never sufficient.

## 8. Mixed-cohort discovery threat model

The V5 corpus was deliberately built from heterogeneous normal/aging/disease, living/postmortem, region, sex, age, study and technology contexts so disease biology can emerge rather than being directly supervised into the representation.

This creates a severe shortcut threat: dataset/chemistry/living-vs-postmortem can approximate disease status.

Therefore later biological emergence claims require, where data support them:

- within-study disease-spectrum replication before pooled disease-axis claims;
- matched donor/region/platform contrasts where available;
- explicit attacks for dataset/source/operator/technology/living-postmortem/PMI/region/sex/depth/support-family recovery;
- biology-preserving technical interventions;
- technical-only and randomized/matched-null controls.

A pooled disease axis alone is not sufficient biological evidence.

## 9. Hard boundaries remain closed

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

No branch name, green unit test, FULL104 binder PASS, dimension receipt, successful CUDA mechanics run or bounded qualification automatically changes those authorities.

## 10. Claude takeover instruction

Start from the live `planning/v5-dataset-first-production-closure-20260912` head after its final GitHub Actions verification. Read this handoff plus:

1. `START_HERE.md`
2. `docs/agent/V5_FULL104_HISTORICAL_PRODUCTION_RECOVERY_20260912.md`
3. `docs/agent/V5_FULL104_HISTORICAL_EXECUTOR_REUSE_MATRIX_20260912.md`
4. `docs/agent/V5_FULL104_CURRENT_BYTE_REBIND_WORK_ORDER_20260912.md`
5. `docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`
6. `docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`
7. `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_AMENDMENT_20260912.md`
8. `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_CONTRACT_V1.json`

First action is physical FULL104 locate/hash/rebind, not another synthetic dataset build and not a training run.
