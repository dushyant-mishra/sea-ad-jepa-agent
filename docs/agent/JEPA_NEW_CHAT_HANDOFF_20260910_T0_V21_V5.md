# JEPA new-chat handoff — T0 V21 design + V5 hardening

**Date:** 2026-09-10
**Status:** handoff only; not scientific authority; training remains OFF.

## 1. Start here

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Primary live V5 branch:
`planning/v5-full-population-cheat-proofing-20260909`

Live V5 head at handoff:
`97e3d1a0dd9e6e8bbe453de2bdad1f2cf59023a9`

Frozen T0 V20 branch remains:
`t0/v20-pathology-blind-materialization-20260908`
head `d5d67e21398da92e39095afd864b4fb9ebe3da02`

T0 Step 4 result commit:
`4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`

T0 V21 design draft commit:
`e770f6dc83c44a36232d15541d3529e71c7611c9`
file `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`
status `DRAFT_FOR_REVIEW_NOT_FROZEN`.

Do not modify or reinterpret V20 retrospectively. Do not authorize training from any file in this handoff.

## 2. T0 V20 terminal and science state

Frozen V20 terminal:
- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- `training_authorized: false`

Broad-state donor-level result:
- primary beta ~124.945
- HC3 SE ~65.489
- t ~1.9079
- one-sided p ~0.0210, df 13
- composition sensitivity p ~0.019
- measurement sensitivity p ~0.030

The broad-state result remains supported historically. The rare binary tail is not qualified.

## 3. Frozen V20 tail machinery

Frozen tail score concept:

`score_i = sum_{g:x_ig>0} log(1 + 10000*x_ig/L_i) * w_g - mu^T w`, with `w = beta/sigma`.

Within donor the score is centered; the rare tail is the frozen discovery equal-donor 95th-percentile boundary.

Frozen QC donor contrast for metric j:

`Delta_dj = (mean_tail X_dj - mean_rest X_dj) / s_dj`

`T_j = mean_d |Delta_dj|`

`T_max = max_j T_j`

Null: 999 deterministic within-donor tail-label reassignments preserving donor tail counts.

`p = (1 + #{T_max^(r) >= T_max_obs - eps}) / 1000`

Frozen QC alpha = 0.05. Observed `T_max = 0.2946862124155104`, p = 0.018, hence the frozen V20 rare-tail QC veto.

Important interpretation: that gate tests cross-cell association with Q_DEPTH/Q_DETECT, not causal measurement dependence. It is retained as historical V20 authority, but this logic should not become the V21/V5 production rejection rule.

## 4. T0 diagnostic arc — what was learned

### Step 1: QC decomposition

- Q_DEPTH component ~0.24366, descriptive p ~0.171.
- Q_DETECT component ~0.29469, descriptive p ~0.015.
- Pearson depth/detect ~0.9232; Spearman ~0.9146; r^2 ~0.8523.
- Each metric has only about 9% independent residual variance after the other.
- Conclusion: Q_DETECT carries the frozen max statistic, but association does not establish artefact.

### Step 2: same-cell depth thinning

Same cell identity, deterministic molecule thinning, frozen scorer and frozen tail threshold.

Key results:
- retention 1.00: exact reproduction, 516 -> 516, Spearman 1.0.
- 0.90: Spearman ~0.969; roughly 9-11% binary-tail churn.
- 0.75: Spearman ~0.916.
- 0.50: Spearman ~0.808; roughly 39% of original tail lost.
- 0.25: Spearman ~0.649; roughly 57-61% of original tail lost.

The upper score region compresses preferentially under thinning. This establishes measurement sensitivity of the binary boundary, not that the biology is fake.

### Step 3: held-out biology under the same-cell intervention

Uses only frozen `COHERENCE_HOLDOUT` genes and the original fixed tail mask; scoring genes do not enter validation.

- 6,146 decision features.
- baseline mean pairwise donor cosine ~0.104216.
- exact common-direction p ~7.63e-06.
- coherence remained positive through the thinning ladder, including severe thinning, although individual donor directions degraded.

Interpretation: a reproducible held-out donor-consistent program exists underneath the unstable binary score boundary. This still did not remove the pre-existing tail/rest QC contrast.

### Step 4: matched-QC held-out validation

Commit `4d95355e...`.

1:1 within-donor matching succeeded technically:
- all 18 donors eligible;
- all 513 common-support tail cells matched;
- Q_DEPTH mean |SMD| 0.2437 -> 0.0138;
- Q_DETECT mean |SMD| 0.2947 -> 0.0249;
- about 92-94% balance reduction.

But the held-out coherence collapsed:
- unmatched ~0.104216, p ~7.63e-06;
- matched ~-0.000961, p ~0.696;
- LOO positive fraction ~0.444.

Critical added control: with the same matched tail cells and an equal-size random rest group from common support that RETAINS the confound, 20 replicates also produced essentially zero coherence (mean ~-0.001466, sd ~0.001296, range ~-0.003959 to +0.000934). Therefore the matched result has no power to distinguish confound removal from loss of detectability. Rest-group median fell from ~290/donor to ~22/donor.

Step 4 conclusion:
- matching removed the observed imbalance;
- the resulting statistic was underpowered;
- the result is uninformative about whether the held-out program was confounded;
- `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` remains correct.

General lesson now carried into V5: every rejection-capable QC/anti-cheat gate must demonstrate that it can still discriminate under the exact geometry it creates. A gate that removes a confound but destroys signal detectability cannot reject.

## 5. T0 V21 draft — current direction

V21 is not frozen and nothing has run.

Current proposed structure:
- broad immune state remains the primary target;
- rare biology moves away from a hard binary tail toward a continuous/neighbourhood biological direction;
- estimator selection, if used, is discovery-only and pathology-blind;
- selection must require BOTH same-cell measurement robustness and preservation of independent held-out biology, so a flat/noise estimator cannot win by stability alone;
- matching/weighting are sensitivities, not central rejection gates;
- donor-level inference remains mandatory;
- rejection-capable gates require prospectively frozen power/discrimination controls;
- pre/post balance uses a fixed pre-intervention denominator;
- numeric environment, resolved input paths, replay-equivalence policy and decision statistics must be recorded.

Candidate estimator family in the draft:
- S0 frozen V20 score baseline;
- S1 matched detected-set offset: `sum_detected (log1p(CP10K)-mu)*w`;
- S2 common-measured-core restricted S0;
- S3 S1 on common measured core;
- S4 weighted within-cell ranks on the core.

Do NOT add an explicit dropout model to the primary family yet; it is more assumption-heavy and should remain sensitivity-only unless separately justified.

### Ridge boundary issue

V20 searched multiplier exponents from -6 to +2 and selected +2, the endpoint. This is a well-posedness issue, not evidence that the V20 HC3 result was materially fragile: the t-statistic is invariant to positive predictor rescaling, though ridge can alter beta direction.

Preferred V21 repair: prospectively freeze a deterministic discovery-only bracketing procedure that expands the lambda range until the CV optimum is interior, with a fixed maximum number of expansions and fail-closed STOP if an interior optimum is not established. Do not extend after seeing confirmation results.

## 6. Highest-value next T0 action for Claude/new chat

Do ONLY the pathology-blind fresh-donor feasibility audit before freezing V21.

Authority reading in the V21 draft found:
- 84 donors have AT8 available;
- old primary MTG immune membership contains 46 donors;
- all 46 are already spent: 28 discovery + 18 confirmation;
- therefore up to 38 AT8-available donors lie outside the old membership.

The audit may read availability/eligibility and authenticated population membership only. It must NOT read AT8 values, fit estimators, run weighting, run another tail diagnostic, or make design choices from confirmation outcomes.

Determine:
- which unused donors have authenticated MTG immune cells;
- which satisfy the unchanged V20 eligibility predicate;
- exact fresh donor count and usable cell counts;
- whether this requires a NEW V21 population authority rather than modifying V20.

If a useful fresh cohort exists, V21 can obtain genuinely new confirmation. If not, any V21 reuse of the old 18 donors must be labeled revised-method analysis rather than independent confirmation.

Standing rule: **if looking at confirmation data could change a design choice, do not look.**

## 7. V5 live engineering state

Live V5 branch:
`planning/v5-full-population-cheat-proofing-20260909`
head `97e3d1a0dd9e6e8bbe453de2bdad1f2cf59023a9`.

V5 work is intentionally proceeding here while Claude stays on T0.

Major closures already implemented:
- representation firewall: biological objectives/checkpoint selection consume `z_bio`; nuisance/measurement information belongs in `z_obs`;
- cross-cell QC association is warning-only, not direct rejection authority;
- complete same-cell intervention family is required for QC qualification;
- pre-execution evidence is separated from learned-checkpoint/post-qualification evidence;
- qualification evidence binds to exact design context and exact checkpoint;
- postqualification dependency closure binds aggregate QC and power artifacts to their exact child artifacts;
- two-sided rejection-gate calibration: every rejection-capable gate must accept a prospectively frozen minimally-valid control AND reject a minimally-invalid control at exact adjudication geometry;
- power/control reports bind exact gate artifact SHA, gate authority ID, checkpoint and design context;
- trainer entry now uses `TrainerPreexecutionAuthorityV4`, requiring the dependency-closed V2 preexecution bundle and an exact prospectively frozen bounded qualification horizon;
- production-geometry GPU evidence is required; historical 128x8 GPU mechanics can only support, not substitute for, production geometry;
- these contracts never authorize production training.

Latest trainer-entry commit:
`97e3d1a0...` — `v5: require dependency-closed V2 bundle at trainer entry`.

Training remains OFF.

## 8. V5 real-data/full-population facts and unresolved blockers

Lawful FULL104 reader-fit scope:
- 4,553,407 cells;
- 104 donors;
- 42 matrices/operators;
- 41,238 molecular addresses;
- 17,186 common core addresses;
- historical materialization geometry 8,915 blocks x 512 with final partial block.

Exact production dimensions remain unresolved and must be derived from full real data:
`D_shared`, `D_private`, `D_total`, `D_obs`, `d_gene`.
Do not copy historical 5/96/160/224/320/512 values as authority.

Corrected expression cache historical local location:
`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Frozen loader-manifest SHA:
`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`

Binder:
`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Recovery contract:
`docs/agent/V5_FULL_READER_EXPRESSION_LOCATION_RECOVERY_CONTRACT_V1.json`

Manifest builder:
`scripts/v5_anticheat/build_full_reader_expression_location_manifest_v2.py`

Required full closure terminal:
`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Still unresolved before any production training:
- exact 42 corrected TRAIN expression shard-pair binding;
- production dimensions derived from the real corpus;
- prospective numerical thresholds/authorities for collapse, shortcut superiority and same-cell stability;
- real proposal-weight invariance;
- real packing/order/restart invariance;
- true production-geometry GPU Gate-2 evidence;
- clean bounded qualification run;
- independent review of resulting evidence bundle.

## 9. Historical mechanics that must remain in V5

Mandatory successful update chain:

`FP16_FORWARD -> BACKWARD_AUTOCAST_DISABLED -> UNSCALE -> PROTECTED_48_GRADIENT_GATE -> OPTIMIZER_STEP_PROVED_BEYOND_DECAY -> ADAM_EXP_AVG_PROVED -> ADAM_EXP_AVG_SQ_PROVED -> EMA_UPDATE -> SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE -> ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

Historical C2 showed the old path could silently produce 48/48 exact-zero protected gradients. The corrected successor produced protected movement and Adam moments. Historical 128x8 did not OOM; the failure was gradient/identity mechanics, not memory. Corrected mechanics are necessary but never sufficient for training authority.

## 10. Can the next chat run a small REAL-data V5 smoke test?

Yes. This runtime contains the real-data reference assets needed to prepare one without asking the user to upload them again.

The smoke test must be explicitly **mechanics/data-path validation only**, not T0 science authority, V5 qualification authority, or training authorization.

Recommended next-chat sequence:
1. verify the heavy-asset hashes below;
2. assemble the discovery expression archive from `part001` + `part002` and verify the assembled SHA before extraction;
3. inspect its manifest/NPZ identity and select a tiny deterministic, donor/operator-stratified subset;
4. bind it through the current V5 data contract/reader and representation firewall;
5. run forward + masking/query-leakage checks and, if torch/CUDA is available, one bounded mechanics update through the protected-gradient gate;
6. run same-cell perturbation summaries on that tiny real subset without choosing production thresholds;
7. compare logical ordering/identity before and after packing;
8. publish the smoke artifact with exact source hashes and mark it `REAL_DATA_SMOKE_NON_AUTHORITY`.

Do not infer production dimensions or scientific thresholds from a tiny subset.

## 11. Heavy assets confirmed present in this runtime

`/mnt/data/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

`/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
SHA-256 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`

`/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
SHA-256 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`

Expected assembled discovery archive SHA-256:
`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

`/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`

`/mnt/data/checkpoints.zip`
SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`

`/mnt/data/t1_checkpoint_u0200.zip`
SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`

`/mnt/data/expression.zip`
SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
This archive contains the discovery sample freeze plus operator metadata; it is useful for identity/metadata smoke setup but not sufficient by itself for expression forward passes.

`/mnt/data/JEPA_NEW_CHAT_TRANSFER_20260910_FROM_FINAL_R4.zip`
contains the prior FINAL-R4 handoff/formula/path/asset ledgers.

Also present:
- `/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
- `/mnt/data/Pasted markdown(5).md`
- `/mnt/data/WSL execution issue.txt`

Do not ask the user to re-upload these while they remain mounted.

## 12. First actions for the new chat

1. Read this handoff and the prior FINAL-R4 transfer bundle.
2. Refetch the V5 live branch; do not assume `97e3d1a0...` is still head.
3. Refetch T0 commits `4d95355e...` and `e770f6dc...` before discussing V21 details.
4. Keep Claude/T0 and V5 work separated: T0 first resolves the pathology-blind fresh-donor feasibility question; V5 can independently continue engineering/smoke validation.
5. For V5, run the tiny real-data smoke test described above if the runtime still has the heavy assets. This smoke test must not set production dimensions, thresholds or training authority.
6. Continue iterative adversarial review of V5 dependency binding, checkpoint substitution, gate blindness/fail-open behavior, identity/order/restart invariance and protected-gradient mechanics.
7. Training remains OFF until all preexecution and postqualification authorities close and independent review accepts them.
