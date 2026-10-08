# JEPA new-chat handoff — 2026-09-09 FINAL R4

Status: `HANDOFF_READY__NO_TRAINING_AUTHORITY`

This handoff supersedes FINAL R3. It includes the completed T0 V20 result, Claude's completed C2 gate adoption and production-geometry verification, the current V5 full-population/anti-cheat state, formulas, exact script/file locations, heavy-asset references, unresolved gates, and next actions.

## First instructions for the new chat

1. Re-fetch live heads for `main`, `planning/v5-full-population-cheat-proofing-20260909`, and `t0/v20-pathology-blind-materialization-20260908` before writing.
2. Read `START_HERE.md`, `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, `docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`, `docs/agent/CURRENT_AUTHORITY_INDEX.md`, and `docs/agent/CURRENT_SUPERSESSION_MAP.md`.
3. Treat the authenticated real reader-fit population as the production substrate: 4,553,407 cells / 104 donors. Synthetic data may test mechanics only; it may not set production biological, D, schedule, threshold, or training authority.
4. Do not train. Training, successor-u0, TD60, D1 real, reader_validation/oracle, DEV/SEALED, protected populations, and pathology-guided tuning remain closed.

## GitHub snapshot used for this handoff

```text
main before R4 handoff commits: c107c47903e976fe512254d2a7ae1efb78985619
V5 candidate branch:              e17c61643c30d219a4434566f828cdf3171381ae
T0 branch:                        d5d67e21398da92e39095afd864b4fb9ebe3da02
```

Re-fetch before acting because branches may advance.

## T0 V20 — scientific result

Primary:
```text
BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL
p_upper = 0.021
frozen alpha = 0.025
beta = 124.94507515835764
HC3 SE = 65.48932245523241
t = 1.9078694125102356
confirmation donors = 18
residual df = 13
permutations = 9,999
```

Rare tail:
```text
RARE_TAIL_UNDERDETERMINED_MEASUREMENT
support = true
coherence = true
QC veto = true
QC p_upper = 0.018
max mean abs standardized QC contrast = 0.2946862124155104
tail disease test = NOT RUN
```

Interpretation: the broad immune signal is marginal internal support; the rare tail is measurement-underdetermined, not a positive or negative biological result, and must not become a training target.

Primary evidence path:
`outputs/t0_stage3_confirmation_20260909/T0_V20_ADJUDICATION_DECISION.json`

Evidence bytes:
- 84 evidence files committed and byte-verified.
- no matrix NPZ caches committed.
- evidence publication proof commit: `2e6d8d1e33867fa90032492894c92ea4849e3e4a`.

## T0 frozen computation publication and replay status

Claude recovered and published the exact V20 frozen computation and input authorities that had lived in a session scratch directory.

Important T0 commits:
- `95d750953dc1835498ac0c77f9656c8f4d7c373f` — 74-file frozen V20 computation publication.
- `ea8cc7989d512c6e58f03d16cf74dc7bee78d3d8` — frozen input-authority publication.
- `994159883b6e39f690df9fe8090a3be3ab50aefe` — reporting-only sensitivity recovery code.
- `f4287e4c37ad2467857ee2a0cd2a3dd56023c141` — bit-exact replay blocker documented.
- `d5d67e21398da92e39095afd864b4fb9ebe3da02` — Q_DEPTH/Q_DETECT diagnostic.

Published paths:
- `scripts/v4/t0_v20_frozen/`
- `configs/v4/t0_v20_frozen_contract/`
- `configs/v4/t0_v20_frozen_authority/`
- `docs/agent/t0_v20_frozen_package/`
- `tests/v4/test_t0_v20_frozen_code_published_v1.py`

### Remaining T0 replay governance decision

The replay reproduces all decision-relevant science but fails the frozen `np.array_equal` bit-exact float check in `verify_target_v2_against_raw`.

Measured differences:
- beta max abs difference ~5.9e-21
- beta max relative difference ~2.8e-12
- sigma difference at machine-epsilon scale
- final lambda differs by one ULP
- selected ridge exponent remains exactly 2.0
- decision mask identical
- mu identical
- donor order identical
- terminal decisions identical

This is a provenance/numeric-stack issue, not a changed scientific result.

Recommended governance order:
1. First try to reconstruct the original numeric stack if practical.
2. If impossible, create a separately versioned replay-equivalence verifier that requires:
   - exact input digests,
   - exact discrete decisions/masks/order,
   - exact selected hyperparameter/discrete choices,
   - exact terminal decisions,
   - explicitly frozen tight float tolerances justified from the measured cross-stack differences.
3. Do not silently weaken V20's historical verifier.
4. Sensitivity recovery remains reporting-only and must not alter V20.

Files:
- `docs/agent/T0_V20_REPRODUCIBILITY_FINDINGS.md`
- `scripts/v4/t0_sensitivity_recovery_v1.py`

### Q_DEPTH / Q_DETECT diagnostic

Pathology-blind, 28 discovery donors:
```text
Pearson r = 0.9232
Spearman = 0.9146
frozen nuisance condition number = 310.6
nuisance + Q_DEPTH + Q_DETECT condition number = 37,671
Q_DEPTH residual unique variance fraction ≈ 0.087
Q_DETECT residual unique variance fraction ≈ 0.096
```

Interpretation: strongly correlated but not redundant; the second measurement dimension is thin and makes the design much more ill-conditioned. For a successor, measurement descriptors should be derived prospectively and preferably near-orthogonal after nuisance projection rather than inherited because T0 used them.

Files:
- `scripts/v4/t0_qc_metric_diagnostic_v1.py`
- `outputs/t0_qc_diagnostic_20260909/T0_QC_METRIC_DIAGNOSTIC.json`

## Historical T1/C2 failure — now mechanically closed

Historical causal diagnosis:
`C2_CAUSAL_CONDITION_ESTABLISHED_FOR_HISTORICAL_128x8_PATH__BACKWARD_EXECUTED_UNDER_FP16_AUTOCAST`

Historical u10-u205 remain quarantined:
`TRAINING_MECHANICS_DEFECT_INHERITED`

Protected registry:
6 blocks × {attention_norm, attention.query, attention.key, attention.value} × {weight,bias} = 48 tensors.

Claude completed the real production-shape gate adoption work on the T0 branch:
- torch 2.7.0+cu128 with CUDA in `sea-ad-jepa-v3`.
- five gate suites: 44 passed, 0 skipped.
- complete task set: 57 passed, zero skipped.
- exact historical effective batch 128 / microbatch 8 on the same RTX 3080.

Negative control:
```text
gated_historical:
GATE STOPPED
rejected = 48/48
EXACT_ZERO = 48
Adam moments created = 0
parameters moved = 0
```

Corrected successor:
```text
dead protected gradients = 0/48
zero Adam exp_avg = 0/48
zero Adam exp_avg_sq = 0/48
move beyond decay = 48/48
ALL_CRITERIA = true
```

Required successful-update chain:
`FP16_FORWARD → BACKWARD_AUTOCAST_DISABLED → UNSCALE → PROTECTED_48_GRADIENT_GATE → OPTIMIZER_STEP_PROVED_BEYOND_DECAY → ADAM_EXP_AVG_PROVED → ADAM_EXP_AVG_SQ_PROVED → EMA_UPDATE → SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE → ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

The historical entrypoint itself was preserved unchanged because its digest is bound. A successor entrypoint was derived with one verified update-call change so it routes through the gated successor step.

Key commits/files:
- `83102b97f92eeb6b5595ac2d085ff9351b110027` — exact 128×8 gate adoption proof.
- `800e9faf02b20ad2f49c4d310d9ea9248355945d` — gate wired into successor of real teacher entrypoint.
- `d4ffa15ade4e90451d913f32bd2d7210dbbf333f` — OOM premise checked and closed.
- `scripts/v4/v5_successor_training_step_v1.py`
- `scripts/v4/v5_successor_teacher_entrypoint_v1.py`
- `scripts/v4/run_c2_t1_exact_path_forensic_v3.py`
- `docs/agent/C2_GATE_ADOPTION_AT_PRODUCTION_GEOMETRY.md`
- `tests/test_v5_successor_teacher_entrypoint_v1.py`
- `tests/test_v5_successor_training_step_v1.py`
- `tests/test_c2_gate_stop_attribution_v1.py`

### OOM correction

The real historical T1 run was not OOM-limited:
- real T1 worst allocated ~5.54 GiB
- real T1 worst reserved ~5.75 GiB
- device 16 GiB
- corrected successor measured ~5.4186 GiB allocated / ~5.7031 GiB reserved
- historical and successor paths are essentially identical in memory.

The OOM belonged to a superseded `production_safe` draft that accumulated live graphs and was never the production path. Do not treat 128×8 OOM as a blocker.

A real-loader gated training update has not been authorized; no training was run.

## Production population authority

Reader-fit:
```text
cells / stable keys = 4,553,407
donors = 104
operators = 42
matrices = 42
donor×operator×source groups = 1,400
molecular addresses = 41,238
common measured core = 17,186
smallest donor = 81 cells
largest donor = 174,111 cells
metadata SQLite SHA-256 = a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913
support geometry SHA-256 = 852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537
```

Production target mass for cell i in donor d:
`p_i = 1/(D*n_d)`
where D is the eligible donor count derived from the authenticated population and n_d is donor d's eligible cell count.

If proposal/schedule probability is q_i:
`w_i = p_i/q_i`

Never type 104 into a production formula as the authority; derive it from the reader-fit ledger.

## V5 full-population schedule

Current V3 candidate:
`docs/agent/TEACHER_STUDENT_V5_FULL_POPULATION_HORIZON_CANDIDATE_V3.json`

Exact real-data candidate:
```text
H = 5,267,086 presentations
full unique-cell coverage = 4,553,407 / 4,553,407
repeat cap = 32
historical group floor sensitivity = 16
ESS fraction = 0.5000000953357726
H-1 ESS = 0.49999986825272125  (fails)
weight ratio = 58037/864 = 67.17245370370371
ledger raw SHA-256 = e05f4a524748cf427b1c3e899a5b672641566c772aa91da8a2a56dae2b9a3c97
ledger domain SHA-256 = 23a5c52e2b472604a9e32c71e114b4752094950180c8d155c7ee45dd95ce8c23
deterministic replay = byte-identical twice
```

Schedule formulas:
`H = Σ_i m_i`
`A = Σ_i 1/(D^2*n_d^2*m_i)`
`ESS_fraction = 1/(H*A)`

Deterministic scientific presentation order:
`slot = (a*presentation_index+b) mod H`
with H=5,267,086, a=2,340,573, b=5,029,443, gcd(a,H)=1.

Key scripts:
- `scripts/v5_anticheat/derive_full_population_schedule_optimum_v3.py`
- `scripts/v5_anticheat/materialize_full_population_schedule_v4.py`
- `scripts/v5_anticheat/derive_actual_presentation_exposure_geometry_v2.py`

## Repeat-cap / conditioning diagnostic

For full coverage with maximum multiplicity C:
`conditioning_ratio >= n_max/(n_min*C)`

Given a prospectively supplied ratio ceiling R:
`C_min = ceil(n_max/(R*n_min))`

With n_min=81, n_max=174111:
- cap32 lower bound = 67.17245, so cap32 is incompatible with a 64× ceiling.
- if 64× were re-adopted independently, cap33 gives 65.1369 fail; cap34 gives 63.2211 pass.
- cap34 floor1 diagnostic H=5,255,116 and ESS=0.500000153433392.

This does not justify the 64× ceiling. It is a conditional diagnostic only.

Files:
- `scripts/v5_anticheat/derive_repeat_cap_from_conditioning_rule_v1.py`
- `docs/agent/v5_anticheat/results/V5_REPEAT_CAP_MINIMAL_REPAIR_DIAGNOSTIC_V1.json`
- `docs/agent/V5_SCHEDULE_GOVERNANCE_RESOLUTION_CANDIDATE_V1.json`

## D hierarchy — numeric values intentionally unresolved

Production dimensions must be re-derived on the full real reader-fit stream.

`D_shared`: reproducible shared biological rank.
Required selection evidence:
- full-refit matched null,
- donor-resampled principal-subspace stability,
- held-donor cross-view predictability,
- independent view/sketch agreement,
- increment beyond frozen measurement shortcut baselines,
- contiguous-prefix selection,
- zero is lawful,
- boundary hit means expand search, not select boundary.

`D_private`: additional biological information in operator-native evidence after D_shared freezes.
Must predict common-core biological state/relations beyond D_shared; residual variance or measurement identity is not enough.
Required held-donor, held-operator, shortcut-increment, and same-cell technical-intervention stability checks.
Zero is lawful.

`D_total = D_shared + D_private`

`D_obs`: separate observation/measurement-state rank for z_obs.

`d_gene`: neural token/attention capacity, not biological D.

Historical non-authorities:
- temporary D_shared=5
- latent width 96
- d_gene 160 as a biological ceiling
- D_global 224
- search rank 320 as a selected D
- sketch width 512 as a permanent production constant
- fixed 256 null/bootstrap replicates without a prospective error-budget derivation.

Key files:
- `docs/agent/V5_DIMENSION_AND_PARAMETER_DERIVATION_CONTRACT_CANDIDATE_V1.json`
- `docs/agent/V5_D_DERIVATION_HISTORICAL_COMPATIBILITY_REVIEW_V1.json`
- `docs/agent/V5_PARAMETER_PROVENANCE_AND_DERIVATION_CLASSIFICATION_V1.json`
- `src/sea_ad_jepa/v5/dimension_authority_guard_v1.py`
- `src/sea_ad_jepa/v5/dimension_execution_firewall_v1.py`
- `tests/test_dimension_authority_guard_v1.py`
- `tests/test_dimension_execution_firewall_v1.py`

## Current biggest blocker: full-reader expression binding

Numeric D and full-reader relational qualification require the exact real expression substrate.

Current terminal:
`STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING`

Required historical corrected cache:
`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Required:
- 42 corrected TRAIN counts/meta shard pairs,
- all hashes must match the frozen production loader manifest,
- loader manifest SHA-256 `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`,
- historical full104 Level-4 materialization = 8,915 blocks over 4,553,407 cells × 41,238 addresses.

Binder:
`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Contract:
`docs/agent/V5_FULL_READER_EXPRESSION_LOCATION_RECOVERY_CONTRACT_V1.json`

Forbidden substitutes:
- 50K discovery expression archive,
- synthetic expression,
- reader_validation/oracle,
- DEV/SEALED,
- pathology,
- recomputed different-byte shards unless separately re-authorized.

Until physical binding closes, these remain blocked:
- numeric D_shared/D_private/D_total/D_obs,
- full-reader TD57B/TD59 qualification,
- full-reader expression shortcut attacks.

## z_bio / z_obs anti-cheat architecture

`z_bio` is the only representation allowed into biological loss, biological checkpoint selection, future biological relational geometry, and downstream biology.

Forbidden free/direct inputs to z_bio:
- donor ID,
- source/matrix/operator identity,
- support fingerprint,
- pathology,
- protected/sealed labels.

`z_obs` may carry lawful measurement support, mask state, Q_DEPTH/Q_DETECT, uncertainty, and independently documented measurement technology descriptors.

Primary anti-cheat is same-cell counterfactual stability, not blind source-adversarial erasure.

Key candidate files:
- `src/sea_ad_jepa/v5/biology_observation_adapter_v1.py`
- `src/sea_ad_jepa/v5/representation_firewall_v1.py`
- `src/sea_ad_jepa/v5/same_cell_technical_intervention_probe_v1.py`
- `src/sea_ad_jepa/v5/full_population_conditioning_authority_v1.py`

## Relational target and measurement-shortcut findings

TD57B: 24/24 PASS.
TD59 nearest-half: 24/24 PASS pilot.
TD57C: failed/closed.
TD60: not authorized.

Explicit simple measurement shortcut donor-agreement ranges:
- TD57B: 0.55234375–0.6564968785030993
- TD59: 0.4804257516370549–0.5566964285714286

Structural shortcut facts within a triplet:
- donor constant,
- operator constant,
- source constant,
- support fingerprint/operator mask constant.

Therefore the main cell-varying simple shortcuts are depth/detection-like measurement quality.

Future learned z_bio must beat the strongest prospectively frozen shortcut baseline by a prospectively frozen increment on held-out units; >0.5 alone is insufficient.

Preferred future gate: paired donor-level learned-minus-shortcut superiority with a prospectively frozen sign/sign-flip procedure and effect requirement.

Files:
- `src/sea_ad_jepa/v5/relational_shortcut_increment_guard_v1.py`
- `target_discovery/independent_checks/20260909_measurement_shortcut_attack/TD57B_EXPLICIT_MEASUREMENT_SHORTCUT_ATTACK_V1.json`
- `target_discovery/independent_checks/20260909_measurement_shortcut_attack/TD59_EXPLICIT_MEASUREMENT_SHORTCUT_ATTACK_V1.json`

## Query precision / support-family / EMA

Singleton query finite-population bound:
`B(N,q,w)=w^2*(N-q)/(q*(N-1))`

For each Q, require positive q_common+q_native=Q, choose the per-operator allocation minimizing the exact two-family bound, then choose the smallest Q whose worst operator is below the prospectively supplied risk fraction.

Current candidate with risk fraction 0.05:
- Q=21 passes: worst 0.0476703666914567
- Q=20 fails: worst 0.05006881843151968

Files:
- `scripts/v5_anticheat/derive_singleton_query_floor_v3.py`
- `docs/agent/V5_SINGLETON_QUERY_PRECISION_AUTHORITY_CANDIDATE_V1.json`

Support-family mass under donor-equal target:
`family_mass_f = E_p[addresses in family f] / E_p[total measured addresses]`

Current candidate:
- COMMON_CORE = 0.607055395953596
- OPERATOR_NATIVE = 0.392944604046404

Files:
- `scripts/v5_anticheat/derive_support_family_mass_v1.py`
- `docs/agent/V5_SUPPORT_FAMILY_MASS_AUTHORITY_CANDIDATE_V1.json`

EMA time unit must be successful scientific base presentations, not optimizer steps.
Per successful update with m presentations and half-life h:
`momentum = 2^(-m/h) = exp(log(0.5)*m/h)`

Real V3 exposure gaps:
- max donor gap = 11,384 presentations
- max operator gap = 37,117
- max source gap = 218

Numeric EMA half-life is not frozen.
File: `docs/agent/V5_EMA_EXPOSURE_DERIVATION_CANDIDATE_V1.json`

## Heavy files — reference, do not duplicate

See `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`.

Important known large assets:
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` SHA `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- discovery expression assembled archive SHA `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- discovery expression inner NPZ SHA `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`
- `checkpoints.zip` SHA `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- `t1_checkpoint_u0200.zip` SHA `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- `expression.zip` SHA `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`

Do not ask the user to re-download or re-upload these merely for handoff. Recover them by exact known path/hash if present. If missing, fail closed and report the missing physical substrate.

## Immediate next work for new chat

1. Re-fetch all live heads.
2. Do not reopen T0 design. Resolve only the explicit replay-equivalence governance issue and reporting-only sensitivity recovery.
3. Recover/bind the exact 42 full-reader corrected expression shard pairs; require 42/42 hash and identity closure.
4. Once expression binding closes, derive D_shared → D_private → D_total and D_obs on the full 4,553,407-cell / 104-donor reader-fit population.
5. Independently adjudicate the schedule risk-control choices: repeat cap, weight-conditioning ceiling, group-floor semantics, ESS floor. Do not choose them from model/checkpoint outcomes.
6. Keep the C2 gate as mandatory. C2 mechanics are closed, but training remains closed until all V5 scientific/hardware gates are complete.
7. Freeze the relational shortcut-superiority calibration before learned checkpoint outcomes.
8. Complete hardware/CUDA Gate-2 and packing invariance for the actual V5 architecture after D_total/query geometry are known.
9. Update governance and obtain independent review.
10. Only then consider training authority.

Final rule: **derive production numbers from authenticated real-data geometry or a prospectively frozen risk/error rule. Do not let synthetic fixtures, historical constants, training loss, checkpoint outcomes, pathology, or protected data choose them.**
