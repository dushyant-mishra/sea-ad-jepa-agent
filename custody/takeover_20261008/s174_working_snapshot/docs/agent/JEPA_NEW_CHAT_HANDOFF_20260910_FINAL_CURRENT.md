# JEPA new-chat handoff — 2026-09-10 FINAL CURRENT

**Purpose:** canonical new-chat handoff for the active T0/V21 investigation and V5 teacher-student pipeline hardening.

**Status:** `HANDOFF_ONLY_NO_TRAINING_AUTHORITY`.

**Training remains OFF.** Nothing in this document authorizes production training, protected-data access, or retrospective modification of frozen T0 V20.

---

## 1. Read this first

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Before doing any work, re-fetch the live heads for:

- `main`
- `t0/v20-pathology-blind-materialization-20260908`
- `t0/v21-prospective-design-20260910`
- `planning/v5-full-population-cheat-proofing-20260909`

Observed immediately before this handoff was finalized:

- `main`: `ff24e12d55200cfcaf64b536a506383b8100f69c`
- frozen V20: `d5d67e21398da92e39095afd864b4fb9ebe3da02`
- V21 design draft: `e770f6dc83c44a36232d15541d3529e71c7611c9`
- V5 engineering: `5668e3d71c720219ec823d5ff089f246091f2be2`
- T0 Step 4 result: `4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`

Branch names never confer scientific authority.

Also read:

- `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
- `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260910_T0_V21_V5_CURRENT.json`
- `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`
- `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md` on the V21 branch
- `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
- `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`

---

## 2. User's operating requirements

The project is being built around the authenticated dataset, not the other way around.

Required working style:

- iterative self-checking;
- adversarial/fail-closed review;
- parallelize independent work where safe;
- do not hard-code historical dimensions or thresholds into production;
- distinguish mechanics PASS, scientific authority and training authority;
- do not rescue failed results by retuning after seeing them;
- keep GitHub current as work proceeds;
- do not proliferate unnecessary branches;
- do not ask the user to re-upload recoverable heavy immutable assets;
- if inspecting confirmation data could change a design choice, do not inspect it.

---

## 3. Authenticated production population

Current full reader-fit authority:

- 4,553,407 cells
- 104 donors
- 42 matrices/operators
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Synthetic fixtures are permitted for unit/mechanics tests only. They cannot set production biology, dimensions, schedules, thresholds or training authority.

---

# PART A — T0

## 4. Frozen T0 V20 terminal

V20 is immutable.

Frozen terminal:

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- `training_authorized: false`

Historical broad-state result:

- beta ~124.945
- HC3 SE ~65.489
- t ~1.9079
- one-sided p ~0.0210
- composition sensitivity p ~0.019
- measurement sensitivity p ~0.030

Do not reinterpret a V21 successor as a retrospective repair of V20.

---

## 5. Frozen V20 tail score and QC statistic

Tail score concept:

`score_i = sum_{g:x_ig>0} log(1 + 10000*x_ig/L_i) * w_g - mu^T w`, with `w = beta/sigma`.

Within donor the score is centered. Tail membership is above the frozen discovery equal-donor 95th-percentile boundary.

Frozen QC donor contrast for metric `j`:

`Delta_dj = (mean_tail X_dj - mean_rest X_dj) / s_dj`

`T_j = mean_d |Delta_dj|`

`T_max = max_j T_j`

Null: 999 deterministic within-donor tail-label reassignments preserving tail counts.

`p = (1 + #{T_max^(r) >= T_max_obs - eps}) / 1000`

Frozen `QC_ALPHA = 0.05`.

Observed:

- `T_max = 0.2946862124155104`
- p = 0.018
- frozen V20 rare-tail QC veto therefore fires.

This is retained as V20 historical authority only. It tests cross-cell association with measurement variables; it does not establish causal measurement artefact.

---

## 6. T0 diagnostic arc

### Step 1 — decomposition

Frozen max-stat reproduced exactly.

- Q_DEPTH component ~0.24366
- Q_DETECT component ~0.29469
- Q_DEPTH descriptive p ~0.171
- Q_DETECT descriptive p ~0.015
- Pearson Q_DEPTH/Q_DETECT ~0.9232
- Spearman ~0.9146
- r^2 ~0.8523

Only roughly 9% independent variance remains in each metric after the other.

Interpretation: Q_DETECT carries the frozen max statistic, but the two metrics are highly redundant and association does not establish artefact.

### Step 2 — same-cell depth thinning

Same cells, deterministic molecule thinning, frozen score and frozen tail threshold.

Key observations:

- retention 1.00: exact replay, 516 -> 516, score Spearman 1.0
- 0.90: score Spearman ~0.969; roughly 9–11% binary-tail churn
- 0.75: Spearman ~0.916
- 0.50: Spearman ~0.808; roughly 39% of original tail lost
- 0.25: Spearman ~0.649; roughly 57–61% of original tail lost

The upper score region is disproportionately measurement-sensitive.

Conclusion: the binary score boundary is not measurement-stable. This does not prove the underlying biology is artefactual.

### Step 3 — held-out biology under same-cell thinning

Validation uses only independent frozen `COHERENCE_HOLDOUT` genes and retains the original fixed tail mask.

- 6,146 decision-capable held-out features
- zero scoring-feature overlap
- baseline mean pairwise donor cosine ~0.104216
- exact common-direction p ~7.63e-06
- donor-coherent held-out program survives the thinning ladder, although individual donor directions degrade at severe thinning

Interpretation: evidence supports an independent donor-consistent program underneath the unstable binary score boundary.

Limitation: same-cell thinning does not remove the pre-existing tail/rest Q_DEPTH/Q_DETECT contrast.

### Step 4 — matched-QC validation

Result commit: `4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`.

1:1 within-donor matching technically succeeded:

- all 18 donors eligible
- all 513 common-support tail cells matched
- Q_DEPTH mean |SMD|: 0.2437 -> 0.0138
- Q_DETECT mean |SMD|: 0.2947 -> 0.0249
- roughly 92–94% reduction in imbalance using the corrected fixed denominator

Held-out coherence then collapsed:

- unmatched ~0.104216, p ~7.63e-06
- matched ~-0.000961, p ~0.696
- LOO positive fraction ~0.444

Critical additive control:

Using the same matched tail cells against an equal-sized random rest sample from common support — retaining the confound — also collapsed to essentially zero over 20 replicates:

- mean ~-0.001466
- sd ~0.001296
- range ~-0.003959 to +0.000934

The matched observed value lies inside this range.

Rest-group median fell from roughly 290 cells/donor to roughly 22 cells/donor.

Therefore Step 4 did NOT show that the held-out biological program was a confound. It showed that the 1:1 matched statistic lost detectability at the geometry created by the gate.

Two corrections recorded in the Step-4 artifact:

- `FIXED_DENOMINATOR_BALANCE`: pre/post SMD uses the pre-intervention denominator so balance changes are comparable;
- `SIZE_MATCHED_UNMATCHED_CONTROL`: detects whether a clean null arose because the statistic lost power.

Final Step-4 interpretation:

`RARE_TAIL_UNDERDETERMINED_MEASUREMENT` remains the correct V20 terminal.

General lesson: a gate that removes a confound can simultaneously destroy the ability to detect the signal it is supposed to validate. Therefore a rejection-capable gate must prove discrimination/power at its exact adjudication geometry.

---

## 7. T0 V21 current state

Branch:
`t0/v21-prospective-design-20260910`

Head:
`e770f6dc83c44a36232d15541d3529e71c7611c9`

File:
`docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`

Status:
`DRAFT_FOR_REVIEW_NOT_FROZEN`

Nothing has been executed under V21.

Current design direction:

- broad immune state remains primary;
- rare biology should move away from a hard binary tail toward a continuous/neighbourhood biological direction;
- estimator selection, if used, must be pathology-blind and discovery-only;
- estimator selection must jointly require same-cell measurement robustness AND preservation of independent held-out biology;
- robustness alone is insufficient because a flat/noise estimator can be perfectly stable;
- weighting/matching should be sensitivity analyses rather than central rejection gates;
- donor-level inference remains mandatory;
- every rejection-capable gate requires a prospective power/discrimination control;
- balance comparisons must use fixed denominators;
- no explicit dropout model should enter the primary estimator family yet because it is more assumption-heavy.

Candidate estimator family currently proposed in the draft:

- S0: frozen V20 score baseline;
- S1: matched detected-set offset, `sum_detected (log1p(CP10K)-mu)*w`;
- S2: S0 restricted to a common measured core;
- S3: S1 on the common measured core;
- S4: weighted within-cell ranks on the core.

Do not select among them using confirmation outcomes.

---

## 8. V20 ridge endpoint issue

V20 searched multiplier exponents from -6 through +2 and selected +2, the upper endpoint.

This is a well-posedness defect: the CV optimum was not shown to be interior.

Do not oversell it as the explanation for V20's broad-state significance. Positive predictor rescaling leaves the HC3 t-statistic unchanged; ridge can still alter beta direction, so the issue matters for model definition but did not obviously invalidate the historical state p-value.

Preferred V21 repair:

- freeze a deterministic discovery-only bracketing procedure before execution;
- expand the lambda/exponent range according to a fixed rule until the optimum is interior;
- freeze a maximum number of expansions;
- fail closed if no interior optimum is established;
- publish the complete CV curve;
- never expand or retune after viewing confirmation results.

---

## 9. Highest-value next T0 action

Do exactly one pathology-blind fresh-donor feasibility audit before freezing V21.

Authority facts motivating it:

- AT8 available for 84 donors;
- old primary MTG immune membership contains 46 donors;
- all 46 are already allocated: 28 discovery + 18 confirmation;
- up to 38 AT8-available donors are therefore outside the old membership.

The audit may inspect only pathology availability flags plus authenticated population/eligibility fields needed by the unchanged predicate. It must not read AT8 values.

Determine:

- which unused donors have authenticated MTG immune cells;
- which satisfy the unchanged V20 eligibility predicate;
- exact donor and usable-cell counts;
- whether a V21 population must be newly frozen rather than extending V20.

Do not fit estimators, run weighting, run another tail diagnostic or use confirmation outcomes to choose V21 machinery during this audit.

Standing rule:

**If looking at confirmation data could change a design choice, do not look.**

---

# PART B — V5 TEACHER/STUDENT PIPELINE

## 10. V5 live branch

Branch:
`planning/v5-full-population-cheat-proofing-20260909`

Observed head:
`5668e3d71c720219ec823d5ff089f246091f2be2`

The branch has advanced substantially from the older FINAL R4 snapshot. Do not use `e17c6164...` as the current V5 head.

The branch also contains a lane-local detailed handoff:

`docs/agent/JEPA_NEW_CHAT_HANDOFF_20260910_T0_V21_V5.md`

---

## 11. Core V5 representation firewall

Production intent:

- biological objectives, relational geometry and checkpoint-selection biology must consume `z_bio` only;
- measurement/support/mask/technology descriptors belong in `z_obs`;
- direct/free leakage of donor identity, matrix/source/operator identity, support fingerprints, pathology and sealed/protected labels into biological objectives is forbidden;
- do not blindly force `z_bio` globally uncorrelated with QC, because legitimate biology may correlate with RNA depth/detection;
- do not blindly regress Q_DEPTH/Q_DETECT from biological signal.

Cross-cell association with QC variables is diagnostic/warning evidence, not causal rejection authority.

---

## 12. V5 QC and anti-cheat hardening completed in this chat

The branch now structurally separates:

1. bad-cell exclusion;
2. cross-cell QC association diagnostics;
3. same-cell causal/measurement perturbation qualification;
4. independent held-out biology;
5. donor recurrence/inference.

Major closures implemented:

- same-cell qualification now bridges correctly into QC closure;
- QC qualification requires the complete same-cell intervention family rather than accepting one arbitrary intervention;
- pre-execution gates and learned-checkpoint/post-qualification gates are separated;
- learned evidence binds the exact checkpoint and design context;
- aggregate QC/power artifacts bind the exact child artifacts;
- postqualification bundles are revalidated rather than trusted as serialized blobs;
- trainer entry binds the exact dependency-closed qualification bundle rather than a generic anti-cheat marker;
- bounded qualification is separated from production training;
- qualification horizon must equal an independently frozen horizon;
- proposal-weight packing invariance has an executable gate;
- packing/order/restart invariance has an executable gate;
- historical C2 regression evidence is separated from V5 production GPU qualification;
- V5 production GPU authority cannot be satisfied by a historical 128x8 receipt;
- dimension authority is bound to the exact FULL104 closure artifact;
- the pre-execution data-to-GPU dependency graph is closed and mixed evidence graphs are rejected.

---

## 13. Step-4 lesson incorporated into V5 power gates

Every rejection-capable V5 gate must earn rejection authority rather than merely produce a null association.

The power/discrimination gate is now two-sided:

- it must accept a prospectively frozen minimally-valid control;
- it must reject a prospectively frozen minimally-invalid control;
- both controls must be evaluated at the exact adjudication geometry;
- power-control evidence binds the exact gate artifact SHA, gate authority ID, design context and checkpoint where applicable;
- substitution of a compatible-looking result from another gate/checkpoint/run is rejected.

This prevents three failure modes:

- blind gate: cannot see anything and therefore always says clean;
- over-rejecting gate: always rejects;
- fail-open/substitution path: passes using unrelated evidence.

---

## 14. Historical C2/T1 mechanics that must carry forward

Historical checkpoint failures were not primarily GPU OOM.

Historical defects included exact-zero/invalid protected gradients plus identity/pandas mechanics defects.

The corrected historical 128x8 successor established that those mechanics can work, but this is regression evidence only.

Mandatory successful update chain:

`FP16_FORWARD -> BACKWARD_AUTOCAST_DISABLED -> UNSCALE -> PROTECTED_48_GRADIENT_GATE -> OPTIMIZER_STEP_PROVED_BEYOND_DECAY -> ADAM_EXP_AVG_PROVED -> ADAM_EXP_AVG_SQ_PROVED -> EMA_UPDATE -> SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE -> ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

V5 production geometry must earn its own hardware evidence.

---

## 15. V5 production dimensions remain unresolved

Do not hard-code historical values such as 5/96/160/224/320/512.

Still to derive from the authenticated full real reader-fit stream:

- `D_shared`
- `D_private`
- `D_total = D_shared + D_private`
- `D_obs`
- `d_gene` as separate neural/token capacity

Numeric dimensions must be justified from full-corpus geometry, nulls, donor stability, held-donor predictability, independent-view agreement and shortcut comparisons rather than from prior small-cohort convenience values.

---

## 16. FULL104 expression closure remains a real-data blocker

Historical corrected cache:

`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Frozen loader-manifest SHA-256:

`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`

Binder:

`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Recovery contract:

`docs/agent/V5_FULL_READER_EXPRESSION_LOCATION_RECOVERY_CONTRACT_V1.json`

Manifest builder:

`scripts/v5_anticheat/build_full_reader_expression_location_manifest_v2.py`

Required successful closure terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Do not substitute the smaller discovery archive, validation/oracle data, DEV/SEALED, pathology-bearing inputs, synthetic data, or differently recomputed shards for this closure.

---

## 17. Current V5 remaining blockers

Before production training can even be considered, still close:

1. exact physical binding of all 42 corrected TRAIN counts/meta shard pairs;
2. FULL104 identity closure;
3. production dimensions from full real data;
4. prospectively frozen numerical qualification thresholds/authorities;
5. real proposal-weight invariance evidence;
6. real packing/order/restart invariance evidence;
7. true production-geometry GPU Gate-2 evidence;
8. a clean bounded qualification run;
9. learned-checkpoint shortcut-superiority and collapse evidence;
10. same-cell measurement robustness on the learned representation;
11. dependency-closed postqualification bundle;
12. independent review.

Training remains OFF until these close.

---

# PART C — RUNTIME DATA AVAILABLE TO THE NEXT CHAT

## 18. Hash-verified heavy assets in `/mnt/data`

A handoff verification pass confirmed the following runtime objects by SHA-256:

### Foundation calibration bundle

Path:
`/mnt/data/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`

Size:
410,278,055 bytes

SHA-256:
`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

### Discovery expression part 001

Path:
`/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`

Size:
303,979,881 bytes

SHA-256:
`b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`

### Discovery expression part 002

Path:
`/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`

Size:
303,979,880 bytes

SHA-256:
`5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`

### Assembled discovery expression stream

Construction:
`part001 || part002`

Size:
607,959,761 bytes

SHA-256:
`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

### checkpoints.zip

Path:
`/mnt/data/checkpoints.zip`

Size:
71,356,460 bytes

SHA-256:
`ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`

### t1 checkpoint u0200

Path:
`/mnt/data/t1_checkpoint_u0200.zip`

Size:
233,729,581 bytes

SHA-256:
`0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`

### expression.zip

Path:
`/mnt/data/expression.zip`

Size:
3,599,456 bytes

SHA-256:
`1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`

Full machine-readable status is in:

`docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`

---

## 19. Important runtime provenance mismatch

Do NOT use this object as the historical operator-address authority without reconciliation:

`/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`

Observed during final handoff verification:

- observed size: 1,531,109 bytes
- observed SHA-256: `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`

Historical expected authority previously recorded:

- expected size: 4,985 bytes
- expected SHA-256: `1473430393179ce8242c9b5ce24d7b84c39d9289492b5a96332eb81436ae68a6`

Status:

`PROVENANCE_MISMATCH_DO_NOT_USE`

This mismatch was found by iterative handoff self-checking and is intentionally carried forward fail-closed.

---

## 20. Small real-data V5 smoke test is allowed

The next chat may run a small subset of the hash-verified real discovery expression data through the V5 pipeline to check whether the mechanics/data path behave as intended.

It must be explicitly labelled:

`REAL_DATA_SMOKE_NON_AUTHORITY`

Allowed goals:

- verify real expression identity/data path;
- verify V5 reader compatibility;
- verify masking/leakage firewall mechanics;
- execute forward mechanics;
- execute one bounded protected-gradient mechanics step if torch/CUDA is available;
- test same-cell perturbation mechanics;
- test packing/order identity preservation.

It may NOT set:

- production dimensions;
- production thresholds;
- biology conclusions;
- schedule authority;
- scientific confirmation;
- training authority.

Use only hash-verified inputs. Exclude the mismatched operator-address NPZ unless provenance is first reconciled.

---

# PART D — IMMEDIATE NEW-CHAT WORK ORDER

## 21. T0 lane

Claude/current T0 lane remains focused on T0 until V21 is understood and prospectively frozen.

Immediate next action:

`PATHOLOGY_BLIND_FRESH_DONOR_FEASIBILITY_AUDIT_ONLY`

If Claude returns that audit, independently inspect the pushed commit and authorities before interpreting it.

Do not move Claude to V5 simply because V5 engineering has progressed here.

---

## 22. V5 lane

The new ChatGPT environment should continue V5 in parallel.

Recommended immediate order:

1. Re-fetch the V5 branch and inspect head `5668e3d...` or its successor.
2. Verify the hash-verified runtime assets from the runtime-status file.
3. Run a tiny `REAL_DATA_SMOKE_NON_AUTHORITY` using the discovery expression asset if local runtime dependencies support it.
4. Use that smoke to find integration/data-shape/path bugs only; do not derive production science or thresholds.
5. Continue structural self-audit of the V5 qualification graph.
6. Close any fail-open, substitution, stale-artifact, wrong-checkpoint, wrong-design-context or powerless-gate paths found.
7. Keep the real FULL104 42-shard closure as the production-data requirement.
8. Keep training OFF.

---

## 23. Permanent anti-cheat/science rules

- Loss decreasing is not biological qualification.
- Pretty embeddings are not biological qualification.
- Mechanical GPU success is not biological qualification.
- A gate reporting no technical association is not valid if it has become blind.
- Cross-cell technical association is weaker evidence than same-cell counterfactual perturbation.
- Held-out biology and donor recurrence are required to prevent trivial measurement-stability solutions.
- Learned biology must beat prospectively frozen shortcut baselines by a prospectively frozen positive increment on held-out units.
- Collapse checks must cover variance/rank/effective dimension/constant embeddings/identity degeneracy/trivial channels.
- Evidence must bind the exact data, design context, checkpoint, gate authority and child artifacts it claims to certify.
- Production dimensions and thresholds must come from the authenticated production dataset and prospective contracts, not historical convenience values.

---

## 24. Final handoff state

T0 V20: immutable.

T0 V21: design draft only, not frozen, not executed.

T0 rare binary tail: unresolved measurement identifiability, not a production target.

T0 broad immune state: historically supported internal target.

V5: structurally hardened substantially, but real-data/dimension/production-GPU/learned-checkpoint qualification blockers remain.

Runtime: major real discovery/calibration/checkpoint assets hash-verified and available for a non-authority V5 smoke; one operator-address NPZ has a provenance mismatch and must not be used.

**Training remains OFF.**
