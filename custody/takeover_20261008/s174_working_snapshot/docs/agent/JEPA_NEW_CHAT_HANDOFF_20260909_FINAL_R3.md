# JEPA new-chat handoff — 2026-09-09 FINAL R3

Status: `HANDOFF_READY__NO_NEW_TRAINING_AUTHORITY`

This handoff supersedes R2. It records the live T0/C2/V5 state, formulas, script/data locations, heavy-asset references, and immediate next work. It does not authorize training, successor-u0, TD60, D1 real execution, DEV/SEALED, reader_validation/oracle, protected populations, or pathology-guided tuning.

## Start here

Re-fetch `main`, `planning/v5-full-population-cheat-proofing-20260909`, and `t0/v20-pathology-blind-materialization-20260908` before writing. Then read `START_HERE.md`, `docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`, `docs/agent/CURRENT_AUTHORITY_INDEX.md`, and `docs/agent/CURRENT_SUPERSESSION_MAP.md`.

Project rule: **derive scale-sensitive production values from the authenticated real dataset; never promote historical pilot constants, synthetic fixtures, or checkpoint-responsive choices into authority.**

## GitHub snapshot

```text
main 90c47b0266a825df7c0aa9bd1da969cf0d3f162f
V5  e17c61643c30d219a4434566f828cdf3171381ae
T0  d5d67e21398da92e39095afd864b4fb9ebe3da02
```

Latest V5 GitHub Actions receipt was still absent when checked. Do not claim remote CI pass without an observed run.

## T0 V20 final result

```text
BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL
p_upper=0.021 vs frozen alpha=0.025
beta=124.94507515835764
HC3 SE=65.48932245523241
t=1.9078694125102356
n=18, residual df=13, permutations=9999

RARE_TAIL_UNDERDETERMINED_MEASUREMENT
tail support/coherence pass; QC veto p_upper=0.018
tail disease test was not run
```

Primary artifact: `outputs/t0_stage3_confirmation_20260909/T0_V20_ADJUDICATION_DECISION.json`. The broad signal is marginal internal support; the rare tail is measurement-underdetermined and must not become a training target.

T0 evidence is committed and byte-verified: 84 evidence files, no matrix caches. Frozen computation and input authorities were recovered from a session scratchpad and published under `scripts/v4/t0_v20_frozen/`, `configs/v4/t0_v20_frozen_contract/`, `configs/v4/t0_v20_frozen_authority/`, and `docs/agent/t0_v20_frozen_package/`.

Important T0 commits: `95d75095` frozen code publication; `ea8cc798` input-authority publication; `99415988` reporting-only sensitivity recovery; `f4287e4c` float replay finding; `d5d67e21` Q_DEPTH/Q_DETECT diagnostic.

### T0 replay blocker

`verify_target_v2_against_raw` requires bit-exact `np.array_equal` float arrays. Current stacks reproduce the science but not every last bit: beta max abs ~5.9e-21, max rel ~2.8e-12; sigma machine-epsilon scale; final lambda one ULP; mu, decision mask, selected exponent 2.0, donor order, and decision terminals are identical.

This blocks replay far enough to recover omitted sensitivity statistics. First try reconstructing the original numeric stack. Do not silently relax V20. If exact-stack recovery fails, create a separately versioned replay-equivalence verifier with documented tolerance plus exact discrete/terminal agreement. Sensitivity recovery remains reporting-only and must not alter V20.

Files: `docs/agent/T0_V20_REPRODUCIBILITY_FINDINGS.md`, `scripts/v4/t0_sensitivity_recovery_v1.py`.

### Q_DEPTH / Q_DETECT diagnostic

```text
Pearson r=0.9232, Spearman=0.9146
nuisance condition number=310.6
nuisance+both QC columns=37,671
unique residual variance: Q_DEPTH=0.087, Q_DETECT=0.096
```

This is a pathology-blind successor-design lesson only. Files: `scripts/v4/t0_qc_metric_diagnostic_v1.py`, `outputs/t0_qc_diagnostic_20260909/T0_QC_METRIC_DIAGNOSTIC.json`.

## Historical T1/C2 failure and repair

Historical diagnosis: `C2_CAUSAL_CONDITION_ESTABLISHED_FOR_HISTORICAL_128x8_PATH__BACKWARD_EXECUTED_UNDER_FP16_AUTOCAST`. Historical u10-u205 remain `TRAINING_MECHANICS_DEFECT_INHERITED`.

Protected registry = 6 blocks × {attention_norm, attention.query, attention.key, attention.value} × {weight,bias} = 48 tensors.

At exact 128×8 geometry the gated historical negative control rejects 48/48 exact-zero protected gradients before Adam state or parameter motion. The corrected successor has 0/48 dead gradients, both Adam moments live for all 48, and 48/48 move beyond decay. Five live torch/CUDA suites report 44 passed, 0 skipped; Claude reported the complete current task set as 57 pass, zero skipped.

Required successful-update chain:

`FP16_FORWARD → BACKWARD_AUTOCAST_DISABLED → UNSCALE → PROTECTED_48_GRADIENT_GATE → OPTIMIZER_STEP_PROVED_BEYOND_DECAY → ADAM_EXP_AVG_PROVED → ADAM_EXP_AVG_SQ_PROVED → EMA_UPDATE → SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE → ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

Key files: `src/sea_ad_jepa/v5/trainer_preexecution_contract_v2.py`, `scripts/v4/v5_successor_training_step_v1.py`, `scripts/v4/v5_successor_teacher_entrypoint_v1.py`, `scripts/v4/run_c2_t1_exact_path_forensic_v3.py`, `docs/agent/C2_GATE_ADOPTION_AT_PRODUCTION_GEOMETRY.md`.

The real T1 run itself was not OOM-limited: ~5.54 GiB allocated / 5.75 GiB reserved worst case on 16 GiB. The OOM belonged to a superseded `production_safe` draft. No training is authorized.

## Real reader-fit population

```text
4,553,407 cells / unique stable keys
104 donors
42 operators / 42 matrices
1,400 donor×operator×source groups
41,238 molecular addresses
17,186 common-core addresses
smallest donor=81 cells; largest donor=174,111 cells
metadata SQLite SHA=a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913
support SHA=852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537
```

Base target probability: `p_i = 1/(D*n_d)`. If proposal q differs, exact correction: `w_i=p_i/q_i`.

## Full-population schedule

Current V3 full-coverage candidate (`docs/agent/TEACHER_STUDENT_V5_FULL_POPULATION_HORIZON_CANDIDATE_V3.json`) is not execution authority. Old one-population-equivalent with-replacement authorities are quarantined by `docs/agent/V5_SCHEDULE_GOVERNANCE_RESOLUTION_CANDIDATE_V1.json`.

V3 candidate: H=5,267,086; full 4,553,407-cell coverage; cap32; group floor16; ESS=0.5000000953357726; H-1 ESS=0.49999986825272125 fail; exact conditioning ratio 58037/864=67.17245370370371. Multiplicity ledger raw SHA `e05f4a524748cf427b1c3e899a5b672641566c772aa91da8a2a56dae2b9a3c97`, domain-bound SHA `23a5c52e2b472604a9e32c71e114b4752094950180c8d155c7ee45dd95ce8c23`; replayed byte-identically twice.

Scientific order: `slot=(a*presentation_index+b) mod H`, with H=5,267,086, a=2,340,573, b=5,029,443, gcd(a,H)=1.

ESS formula used by the optimizer: `A=Σ_i 1/(D^2*n_d^2*m_i)`, `H=Σ_i m_i`, `ESS_fraction=1/(H*A)`.

Key scripts: `scripts/v5_anticheat/derive_full_population_schedule_optimum_v3.py`, `scripts/v5_anticheat/materialize_full_population_schedule_v4.py`, `scripts/v5_anticheat/derive_actual_presentation_exposure_geometry_v2.py`.

### Repeat-cap diagnostic

Under full coverage and cap C, conditioning ratio is bounded below by `n_max/(n_min*C)`. With n_min=81, n_max=174111, cap32 gives 67.17245 > 64. If a 64× ceiling were prospectively re-adopted, `C_min=ceil(n_max/(64*n_min))=34`; cap33 fails (65.1369), cap34 passes (63.2211). This is diagnostic only and does not justify the 64× ceiling or supersede V3. Files: `scripts/v5_anticheat/derive_repeat_cap_from_conditioning_rule_v1.py`, `docs/agent/v5_anticheat/results/V5_REPEAT_CAP_MINIMAL_REPAIR_DIAGNOSTIC_V1.json`.

## EMA / query / support formulas

Real V3 exposure gaps: donor max 11,384; operator max 37,117; source max 218. EMA unit is successful scientific base presentations, with `momentum=2^(-m/h)=exp(log(0.5)*m/h)`. Numeric h is not frozen.

Singleton query finite-population bound: `B(N,q,w)=w^2*(N-q)/(q*(N-1))`. Choose positive `q_common+q_native=Q` minimizing the two-family sum per operator, then the smallest Q whose worst operator meets the prospectively supplied error bound. Current 5% candidate: Q=21 passes at 0.0476703667; Q=20 fails at 0.0500688184. Files: `scripts/v5_anticheat/derive_singleton_query_floor_v3.py`, `docs/agent/V5_SINGLETON_QUERY_PRECISION_AUTHORITY_CANDIDATE_V1.json`.

Donor-equal support-family masses: COMMON_CORE=0.607055395953596, OPERATOR_NATIVE=0.392944604046404. Rule: weight by expected eligible address mass under `p_i=1/(D*n_d)`, not raw cell frequency. Files: `scripts/v5_anticheat/derive_support_family_mass_v1.py`, `docs/agent/V5_SUPPORT_FAMILY_MASS_AUTHORITY_CANDIDATE_V1.json`.

## D hierarchy

Numeric D values are intentionally unresolved. `D_shared` = reproducible shared biology selected on full reader_fit with full-refit matched null, donor-resampled subspace stability, held-donor predictability, independent-view agreement, and increment beyond measurement shortcuts. `D_private` = additional native-evidence biological rank after D_shared freezes, requiring held-donor/held-operator and same-cell shortcut-stability increments. `D_total=D_shared+D_private`. `D_obs` is separate measurement-state rank. `d_gene` is neural capacity, not biological rank.

Historical 5/96/160/224/320/512 are not production D authority. Files: `docs/agent/V5_DIMENSION_AND_PARAMETER_DERIVATION_CONTRACT_CANDIDATE_V1.json`, `docs/agent/V5_D_DERIVATION_HISTORICAL_COMPATIBILITY_REVIEW_V1.json`, `src/sea_ad_jepa/v5/dimension_authority_guard_v1.py`, `src/sea_ad_jepa/v5/dimension_execution_firewall_v1.py`.

## Full-reader expression blocker

Current terminal: `STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING`. Production D/relational authority requires the exact 42 corrected TRAIN counts/meta shard pairs from historical cache root `D:\Jepa project\data\cache\stage81a3r_corrected_real_train`, validated against loader manifest SHA `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`. Historical full104 level-4 materialization records 8,915 blocks over all 4.55M cells × 41,238 addresses.

Forbidden substitutes: the 50K discovery archive, synthetic expression, different-byte recomputations without new authority, reader_validation/oracle, DEV, SEALED, pathology. Until binding closes, numeric D derivation, full-reader TD57B/TD59 qualification, and full-reader expression shortcut attacks remain blocked.

File: `docs/agent/V5_FULL_READER_EXPRESSION_LOCATION_RECOVERY_CONTRACT_V1.json`.

## z_bio / z_obs and relational anti-cheat

`z_bio` is the only representation allowed to drive biological loss, biological checkpoint selection, future relational geometry, and downstream biology. Donor/source/matrix/operator identity, support fingerprint, pathology, and protected/sealed labels are forbidden free inputs. `z_obs` may carry lawful support/mask/depth/detection/uncertainty and separately documented measurement technology descriptors.

Key candidate files: `src/sea_ad_jepa/v5/biology_observation_adapter_v1.py`, `representation_firewall_v1.py`, `same_cell_technical_intervention_probe_v1.py`, `full_population_conditioning_authority_v1.py`.

TD57B remains 24/24 PASS; TD59 nearest-half remains 24/24 PASS pilot; TD57C failed/closed. Explicit QC shortcut ranges: TD57B 0.55234375–0.6564968785; TD59 0.4804257516–0.5566964286. Learned z_bio must beat the strongest prospectively frozen shortcut baseline by a prospectively frozen increment on held-out units; chance alone is insufficient. Prefer a paired donor-level superiority procedure. File: `src/sea_ad_jepa/v5/relational_shortcut_increment_guard_v1.py`.

## Heavy assets: reference, do not duplicate

```text
FOUNDATION_CALIBRATION_BUNDLE_20260824.zip
SHA 07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444

FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip parts:
part001 SHA b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e
part002 SHA 5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875
assembled SHA 63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7

checkpoints.zip
SHA ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c

t1_checkpoint_u0200.zip
SHA 0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c

expression.zip
SHA 1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4

historical full discovery inner NPZ
SHA 4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92
```

Do not ask the user to move these large files merely for handoff. Use exact hashes/paths; if a new runtime lacks a required physical asset, fail closed rather than substituting a smaller/synthetic object.

## Immediate next work

1. Re-fetch live heads.
2. Resolve T0 replay-equivalence governance without changing V20 science.
3. Recover/bind exact full-reader expression substrate.
4. Derive numeric D_shared → D_private → D_total and D_obs on all 4,553,407 reader-fit cells / 104 donors.
5. Independently adjudicate schedule/repeat-cap/group-floor risk controls.
6. Freeze EMA scope/smoothing and production update geometry after hardware calibration.
7. Freeze held-donor paired relational superiority against measurement shortcuts before checkpoint outcomes.
8. Bind every SHA required by `trainer_preexecution_contract_v2.py`; zero critical skips.
9. Independent review; only then discuss training authority.

Final reminder: **lower loss is not biological qualification. Synthetic data may test mechanics, but it may never set production biological, schedule, threshold, D, or training authority.**
