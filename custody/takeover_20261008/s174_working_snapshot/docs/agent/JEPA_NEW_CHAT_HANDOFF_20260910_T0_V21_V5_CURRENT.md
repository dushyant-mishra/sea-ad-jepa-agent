# JEPA new-chat handoff — 2026-09-10 current

**Status:** handoff/governance only. Not scientific authority. **Training remains OFF.**

## Start here

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Re-fetch these live heads before writing:

- `main` — observed at handoff: `7e08e89a1d9a46a4a681cbc7fda1755a336373a3`
- `planning/v5-full-population-cheat-proofing-20260909` — observed at handoff: `5668e3d71c720219ec823d5ff089f246091f2be2`
- `t0/v20-pathology-blind-materialization-20260908` — frozen V20: `d5d67e21398da92e39095afd864b4fb9ebe3da02`
- `t0/v21-prospective-design-20260910` — V21 draft only: `e770f6dc83c44a36232d15541d3529e71c7611c9`

Branch names never confer scientific authority.

## T0: frozen V20 result

V20 is immutable.

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- `training_authorized: false`

Broad-state historical result:

- beta ~124.945
- HC3 SE ~65.489
- t ~1.9079
- one-sided p ~0.0210
- composition sensitivity p ~0.019
- measurement sensitivity p ~0.030

The broad state remains the strongest supported internal target. The binary rare tail is not a qualified production target.

## T0 rare-tail diagnostic arc

### Step 1 — QC decomposition

Frozen tail QC reproduced exactly: `T_max = 0.2946862124155104`, p=0.018.

- Q_DEPTH component ~0.24366
- Q_DETECT component ~0.29469
- depth/detect Pearson ~0.9232, Spearman ~0.9146, r^2 ~0.8523

Conclusion: the frozen veto is mostly Q_DETECT-driven, but cross-cell association does not establish causal measurement artefact.

### Step 2 — same-cell depth thinning

Same cells, deterministic molecule thinning, frozen score and tail threshold.

- 1.00 retention: exact replay
- 0.90: score rank correlation ~0.969, roughly 9–11% binary-tail churn
- 0.50: ~39% of original tail lost
- 0.25: rank correlation ~0.649, roughly 57–61% of original tail lost

Conclusion: the binary score boundary is measurement-sensitive. This does not prove the underlying biology is artefactual.

### Step 3 — held-out biology under thinning

Independent `COHERENCE_HOLDOUT` genes only; zero scoring-feature overlap.

- 6,146 decision features
- baseline mean pairwise donor cosine ~0.104216
- exact common-direction p ~7.63e-06
- donor-consistent program survives the thinning ladder despite individual-direction degradation

Conclusion: evidence supports an independent donor-consistent program underneath the unstable binary boundary.

### Step 4 — matched-QC validation

Result commit: `4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`.

1:1 matching technically succeeded:

- 18/18 donors eligible
- all 513 common-support tail cells matched
- Q_DEPTH mean |SMD| 0.2437 -> 0.0138
- Q_DETECT mean |SMD| 0.2947 -> 0.0249

But the held-out coherence collapsed to noise:

- unmatched ~0.104216, p ~7.63e-06
- matched ~-0.000961, p ~0.696
- LOO positive fraction ~0.444

A critical size-matched confound-retaining control also collapsed to ~0 at the same sample size. Therefore the matched statistic lost detectability when the rest group dropped from a median of ~290 to ~22 cells/donor.

**Step-4 conclusion:** matching removed the observed imbalance but simultaneously destroyed the statistic's power. The result is uninformative about whether the biological program was confounded. `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` remains correct.

General rule carried forward: **a rejection-capable QC/anti-cheat gate must prove it still discriminates at the exact geometry it creates.**

## T0 V21 current design direction

Draft commit: `e770f6dc83c44a36232d15541d3529e71c7611c9`.

File: `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`.

Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`. Nothing executed.

Current direction:

- broad immune state remains primary;
- rare biology moves away from a hard binary tail toward a continuous/neighbourhood direction;
- estimator selection, if any, must be pathology-blind and discovery-only;
- selection must jointly require same-cell measurement robustness **and** preservation of independent held-out biology;
- weighting/matching are sensitivity analyses, not central rejection gates;
- donor-level inference remains mandatory;
- every rejection-capable gate needs prospective discrimination/power controls;
- pre/post balance uses a fixed pre-intervention denominator;
- V20 ridge endpoint `+2.0` is treated as a well-posedness problem, not as proof the V20 inference was materially fragile.

Preferred V21 ridge repair: a prospectively frozen, deterministic discovery-only bracketing procedure that expands the lambda range until the CV optimum is interior, with a fixed maximum number of expansions and fail-closed STOP if an interior optimum is not established.

### Highest-value next T0 action

Do **only** the pathology-blind fresh-donor feasibility audit before freezing V21.

Known authority facts from the draft:

- AT8 available for 84 donors
- old MTG immune membership contains 46 donors
- those 46 are already allocated 28 discovery + 18 confirmation
- up to 38 AT8-available donors lie outside the old membership

The audit may inspect availability, partition, region/operator/class eligibility and authenticated population membership only. **Do not read AT8 values.** Do not fit an estimator, run weighting, run another tail diagnostic, or tune a V21 method from confirmation outcomes.

Determine exact unused eligible donor count and usable cell counts under the unchanged eligibility predicate. If new donors qualify, V21 should create a **new** prospectively frozen population authority; never modify V20.

Standing rule: **if looking at confirmation data could change a design choice, do not look.**

## V5 current engineering branch

Branch: `planning/v5-full-population-cheat-proofing-20260909`

Observed head at handoff: `5668e3d71c720219ec823d5ff089f246091f2be2`.

The V5 branch contains the active anti-cheat/qualification hardening plus a previous detailed lane-local handoff at:

`docs/agent/JEPA_NEW_CHAT_HANDOFF_20260910_T0_V21_V5.md`

Major structural closures already implemented:

- representation firewall: biology objectives/checkpoint selection use `z_bio`; nuisance/measurement information belongs in `z_obs`;
- cross-cell QC association is warning-only, not rejection authority;
- complete same-cell technical-intervention family is required for QC qualification;
- pre-execution evidence is separated from learned-checkpoint/post-qualification evidence;
- qualification evidence binds exact design context and exact checkpoint;
- aggregate QC and power artifacts are bound to their exact child artifacts;
- rejection-gate calibration is two-sided: every rejection-capable gate must accept a prospectively frozen minimally-valid control and reject a minimally-invalid control at exact adjudication geometry;
- control reports bind the exact gate artifact SHA, gate authority ID, checkpoint and design context;
- trainer entry is bounded-qualification only and does not authorize production training;
- production-geometry GPU evidence is required; historical 128x8 mechanics may support but cannot substitute for production geometry.

The Step-4 lesson is now explicitly represented in V5: a gate cannot earn rejection authority merely because its target technical association disappears; it must prove both sensitivity and specificity at its own adjudication geometry.

## V5 unresolved blockers

Authenticated FULL104 reader-fit scope:

- 4,553,407 cells
- 104 donors
- 42 matrices/operators
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Still unresolved before production training:

1. exact physical binding of all 42 corrected TRAIN counts/meta shard pairs;
2. production dimensions derived from the full real corpus: `D_shared`, `D_private`, `D_total`, `D_obs`, and separate neural/token capacity `d_gene`;
3. prospective numeric thresholds/authorities for collapse, shortcut superiority and same-cell stability;
4. real proposal-weight invariance;
5. real packing/order/restart invariance;
6. true production-geometry GPU Gate-2 evidence;
7. clean bounded qualification run;
8. independent review of the resulting evidence bundle.

Do not reuse historical 5/96/160/224/320/512 as production dimension authority.

Historical corrected cache location:

`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Frozen loader-manifest SHA-256:

`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`

Binder:

`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Recovery contract:

`docs/agent/V5_FULL_READER_EXPRESSION_LOCATION_RECOVERY_CONTRACT_V1.json`

Manifest builder:

`scripts/v5_anticheat/build_full_reader_expression_location_manifest_v2.py`

Required real-data closure terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

## Real-data V5 smoke test in the ChatGPT runtime

A **small real-data smoke test is appropriate** before Claude moves to V5, but it must remain `REAL_DATA_SMOKE_NON_AUTHORITY`.

It may test:

- real expression identity/data-path binding;
- V5 reader compatibility;
- query masking / leakage firewall;
- forward mechanics;
- one bounded protected-gradient update if torch/CUDA is available;
- same-cell perturbation mechanics;
- packing/order identity preservation.

It may **not** set production dimensions, biology thresholds, schedule thresholds, scientific conclusions or training authority.

Available runtime assets should be verified by SHA before use. Known expected hashes:

- foundation calibration bundle: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- discovery expression archive assembled SHA: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- part001: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- checkpoints.zip: `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- t1 checkpoint u0200: `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- expression.zip: `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`

Likely runtime paths:

- `/mnt/data/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `/mnt/data/checkpoints.zip`
- `/mnt/data/t1_checkpoint_u0200.zip`
- `/mnt/data/expression.zip`

Never ask the user to re-upload a recoverable heavy immutable asset merely for handoff.

## Historical training-mechanics requirement

Mandatory successful update chain:

`FP16_FORWARD -> BACKWARD_AUTOCAST_DISABLED -> UNSCALE -> PROTECTED_48_GRADIENT_GATE -> OPTIMIZER_STEP_PROVED_BEYOND_DECAY -> ADAM_EXP_AVG_PROVED -> ADAM_EXP_AVG_SQ_PROVED -> EMA_UPDATE -> SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE -> ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

Historical C2 failure was exact-zero/invalid protected gradients plus identity/pandas defects, not GPU OOM. Corrected mechanics are necessary but not sufficient for training authority.

## Immediate new-chat work order

1. Re-fetch `main`, V5 and T0 V21 draft heads.
2. Keep Claude/T0 work separate from V5 engineering.
3. T0: inspect the fresh-donor feasibility result if available; otherwise perform only that pathology-blind audit.
4. V5: run a tiny real-data smoke test from the verified discovery expression asset if the runtime can support it; mark it non-authority.
5. Continue V5 structural self-audit and tests while keeping production training OFF.
6. Never infer scientific authority from a smoke test, branch name, unit test, or decreasing loss.

**Training remains OFF until all prospective real-data and post-qualification gates close and are independently reviewed.**
