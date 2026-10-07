# Chat-runtime archive content map — 2026-10-07

This is a locator index. Exact top-level archive sizes/SHA-256 values are in `CHAT_RUNTIME_FILE_CUSTODY_20261007.csv`. Large archive bytes are not stored in ordinary Git history.

## `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

SHA-256 `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`; 97 members.

Core handoff/context:
- `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.md` — member SHA-256 `5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`
- `context/FOUNDATION_TARGET_DISCOVERY_PROSPECTIVE_CONTRACT_V1.md`
- `context/PROJECT_HISTORY_TARGET_DISCOVERY_DECISIONS_20260907.md`
- `LOCAL_ARTIFACT_MANIFEST.csv`
- `PACKAGE_MANIFEST.csv`

Actual evidence directories retained inside the archive:
- `evidence/td_iteration13_history_gated/`
- `evidence/td_iteration13b_history_gated_ablation/`
- `evidence/td_iteration14_power_matched/`
- `evidence/td_iteration15_operator_generalization/`
- `evidence/td_iteration19_20_history_gated/`
- `evidence/td_iteration21_dependency_attack/`
- `evidence/td_iteration21b_estimability_sweep/`
- `evidence/td_iteration22_within_donor_dependency/`
- `evidence/td_iteration22b_spearman/`
- `evidence/td_iteration23_row_alias_forensic/`
- `evidence/td_iteration24_depth_attack_corrected/`
- `evidence/td_iteration25_state_geometry_corrected/`
- `evidence/td_iteration28_label_free_relational/`
- `evidence/td_iteration29a_pairunit_falsification/`
- `evidence/td_iteration30_diffusion_signature/`
- `evidence/td_iteration31a_source_conditional_falsification/`
- `evidence/td_iteration31b_splitfit_preprocess/`
- `evidence/td_iteration32_countsplit_measurement/`
- `evidence/td_iteration33_global_row_binding_guard/`
- `evidence/td_iteration34_state_geometry_globalrow/`
- `evidence/td_iteration35_source_conditional_globalrow/`
- `evidence/td_iteration36_class_conditioned_subspace/`

Actual scripts retained inside the archive:
- `scripts/td_iteration23_row_alias_forensic.py`
- `scripts/td_iteration24_depth_attack_corrected.py`
- `scripts/td_iteration25_state_geometry_corrected.py`
- `scripts/td_iteration26_label_firewalled_state_discovery.py`
- `scripts/td_iteration29_pairunit_label_free.py`
- `scripts/td_iteration29a_pairunit_falsification.py`
- `scripts/td_iteration30_diffusion_signature.py`
- `scripts/td_iteration31_source_conditional_subspace.py`
- `scripts/td_iteration31a_source_conditional_falsification.py`
- `scripts/td_iteration31b_splitfit_preprocess.py`
- `scripts/td_iteration32_countsplit_measurement.py`
- `scripts/td_iteration33_global_row_binding_guard.py`
- `scripts/td_iteration34_state_geometry_globalrow.py` — SHA-256 `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`; direct copy also archived in GitHub
- `scripts/td_iteration35_source_conditional_globalrow.py`
- `scripts/td_iteration36_class_conditioned_subspace.py`

## `JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`; 155 members.

Key reconstruction/audit scripts:
- `repro_td41.py` — member SHA-256 `d8630f4cdeb8b3ecaa09084858f74e7f1eb2ba897608e2a274258793c97b7cb0`
- `exact_kendall_state.py` — member SHA-256 `1b2bfd5b69b4f5b6a4487fe05d24e2d698ff75dd399a3c6061e90ff67d51ed06`
- `TD43_RECONSTRUCTED_24_CASES.csv` — member SHA-256 `d15ae4793667c7faf20f96ef6d55c0537c51a7b4a9bc082f83dd5333ebb2c8a4`
- TD41 audit scripts: `audit_td41_*`, `td41_full_one.py`, `td41_full_pairs.py`, `td41_pairwidth.py`, `td41_td43_informativeness_audit*.py`
- TD42: `repro_td42_case.py`, `audit_td42_null_decomp.py`
- TD43: `independent_td43_hvs_p0.py`, `run_td43_sea_panel3.py`, `td43_*`

TD44-TD55:
- `run_td44s_observed.py`, `td44_obs.npz`
- `run_td45_obs.py`, `run_td45_pos.py`, `td45_obs.npz`
- `run_td46_obs.py`, `run_td46_pos.py`, `td46_obs.npz`
- `run_td47.py`, `run_td47_pos.py`, `td47_obs.npz`
- `run_td48_obs.py`, `run_td48_null.py`, `td48_obs.npz`, `td48_null.npy`
- `run_td49_nph_obs.py`
- `compute_td50_source.py`, `run_td50_*`, `td50_{HVS,NPH52,SEA_AD}.npz`, `td50_obs.npz`, null batches and diagnostics
- `run_td51s.py`, `td51s_result.npz`, `td51_donor_audit.py`, `td51_independent_robustness.py`
- `run_td52s.py`, `td52s_result.npz`, source NPZs
- `run_td53s.py`, `run_td53s_msb.py`, result NPZs
- `run_td54s.py`, `run_td54s_msb.py`, result NPZs
- `run_td55s.py`, `td55s_result.npz`, `td55_selection.npz`, `td55_finalize_selection.py`, `td55_independent_primary.py`, `td55_positive_controls.py`, `td55_final_eval.py`

TD56-TD58:
- HVS/NPH52/SEA-AD TD56 scripts for primary, numeric-pair, second-block and matching result NPZs
- `run_td57_source.py`, `run_td57a_source.py`, source result NPZs
- `td57b_fixed_relational_recurrence.py`, `td57b_fast.py`, p0/p1 JSONs/stdout/replays
- `td57c_three_view_local_geometry.py`, `td57c_global_same_xy_forensic.py`, primary/replay/post-failure forensic JSONs
- `run_td58_source.py`, `prep_td58_sea.py`, `eval_td58_sea_cached.py`, `td58_HVS_result.npz`, `td58_NPH52_result.npz`, `td58_SEA_AD_result.npz`

Interpretation boundary: TD55 did not cleanly transport to NPH52; TD56-TD58 are evidence of relational structure, not a qualified target. Mixed-source results need corrected HVS/SEA-AD feature-axis replay.

## `JEPA_NEW_CHAT_HANDOFF_LIGHT_20260908.zip`

SHA-256 `3714f4e8af44a20b518642f38508170f0f8f275f08d42cebec1dfe4979fd3554`; 48 members.

Contains:
- `START_HERE.md`, `STATUS.json`, `FORMULAS_AND_THEORY.md`, package/root manifests
- selected TD56 / TD57b / TD57c scripts and results under `core_artifacts/`
- nested historical Sept-7 handoff ZIP
- teacher/student V3 review packages.

## `TEACHER_STUDENT_V5_ELIGIBLE_DONOR_ESTIMATOR_CANDIDATE_20260909.zip`

SHA-256 `206e11c606fc8631c1e527549655fb0f21087cb31e54320ce026d5e2f04fa3c7`; 25 members.

Contains actual candidate code/tests and authorities, including:
- `docs/agent/READER_FIT_ELIGIBLE_DONOR_LEDGER_CANDIDATE_V2.csv`
- `docs/agent/TEACHER_STUDENT_V5_BASE_OBJECTIVE_ESTIMATOR_*`
- `docs/agent/TEACHER_STUDENT_V5_DATASET_FIRST_*`
- `scripts/agent/derive_teacher_student_v5_eligible_donor_authority_v1.py`
- `src/sea_ad_jepa/v5/eligible_donor_authority_v1.py`
- `src/sea_ad_jepa/v5/ema_scale_authority_v1.py`
- `src/sea_ad_jepa/v5/estimator_authority_v1.py`
- `src/sea_ad_jepa/v5/hardware_calibration_boundary_v1.py`
- `src/sea_ad_jepa/v5/inactive_dataset_teacher_update_v1.py`
- `src/sea_ad_jepa/v5/schedule_authority_v4.py`
- corresponding tests.

Use equal-donor weighting principle only; historical reader-fit104 population is not current Stage-A authority.

## `checkpoints.zip`

SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`.

Members:
- `checkpoints/checkpoint_manifest.json` SHA-256 `b8f0e4f5873c72ec3408cec73e8a78279668515bc881783ee040a56064e9ccb5`
- `checkpoints/t1_checkpoint_u0000.pt` SHA-256 `19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4`
- `checkpoints/t1_checkpoint_u0205.pt` SHA-256 `f8b1ad572391d38db474b4de95c56314bcff89086df6e42e86db259940a504fa`

## `t1_checkpoint_u0200.zip`

SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`.

Members:
- u10 SHA-256 `9928005c53043a7e7f33e35c3beb31bc200cf88698b8bae087fe2bafd95d0be7`
- u25 `1df5f974cb3249bb9b2d4b56b192e91adefed02229820d9d4973dd4b1f86d194`
- u50 `39f0a7762e288732449c082fd96c38a988bf594674f3e1aae56e0dadf65d7102`
- u100 `b5302fc45d5d79d663879e407aa5cd97757f4789cbdcd884885a58ae20075340`
- u200 `5cbdd3346ca85a824b0066a771e59c231258dc8865efd81eaa54909286eefd41`

## `expression.zip`

SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`; 48 members.

Contains:
- `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`
- `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` member SHA-256 `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
- `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json` member SHA-256 `50fc39c27149ded58ea49b35d7f28dab7d540096ee5df4c2e762d872c8c7903c`
- 42 `sample_operator_metadata/opXX.meta.csv` files.

## Other archives

- `JEPA_CHAT_EXCLUSIVE_FINAL_SOURCES_20261005.zip` SHA-256 `7a036b5ccf9965088d7730a54715e257e478d9bb7d768d34fe37e4ba3441bf34`; 3 members preserving the chat-exclusive Oct-5 pasted text/markdown and checksum.
- `v77-suite-junit.zip` SHA-256 `bdcbfb1e4a468801f9e4e6ca4b71cd2987ee57f84de2ae2d10c3be437d8eed62`; members `v77_suite_junit.xml` SHA-256 `96645cb5e1423a74953027b894fdbb6a3c6a5aebef2c496f264f017316fb80be` and `v77_suite.log` SHA-256 `fa921b1a279d6aa758965d45366583d2de4a6aedc2f6626a5ee66a734ae15e25`.
