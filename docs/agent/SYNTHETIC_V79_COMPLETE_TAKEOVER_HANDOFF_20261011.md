# Synthetic/V79 complete takeover handoff — 2026-10-11

This is the canonical human-readable takeover record for the **synthetic dataset / V79 Bayesian geometry lane**. It is intended for a new supervising agent and for directing Macha. Target discovery is a separate lane and must not be mixed into this one.

## 0. Current terminal state

`EXACT_S174_STRUCTURE_REPLAY_FAILED_CLOSED__OPERATOR_MODEL_LOGISTIC_NONCONVERGENCE__NO_METRICS_COMPUTED__PROSPECTIVE_OPERATOR_REGULARIZATION_REPAIR_APPROVED__BAYESIAN_CONFIRMATION_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

Nothing in this handoff authorizes JEPA training, H0-H3 scientific factorial execution, TEST/Morabito/pathology access, target-discovery work, or posterior parameter export.

## 1. Repository control surfaces

### Upstream Bayesian geometry
- Macha source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`
- live source head at takeover: `b06bd819abd7da1be0426767c6909f4cdc7cc7bf`
- independent audit PR: **#260** `audit/v79-bayesian-geometry-snapshot-20261010`
- controller/handoff PR: **#261** `handoff/v79-bayesian-geometry-takeover-20261010`

### Resource-safe exact-S174 development replay
- implementation PR: **#279** `fix/v79-streaming-analysis-cache-20261011`
- verified code head: `2d5de281a171f0510d22a7408780fb069625ea02`
- documentation head used for physical replay snapshot: `615b55eb03b95630484b18d47de0ef7340368d37`
- CI: workflow `38166126568`, job `114548954034`, **15 passed in 1.27 s**

### Physical exact-S174 execution record
- execution PR: **#280** `exec/v79-s174-structure-replay-20261011`
- execution-record head at first failed-closed replay: `2f4b77e7290397130d681c47b82337115e9e9585`
- PR #280 is the immutable record of the first physical replay failure and must not be rewritten into a pass.

### Downstream factorial synthetic-world lane
- hardened implementation PR: **#262**, head `9110c3fae6d34e43463d56631f43004bda33beb8`
- independent factorial audit PR: **#264**, head before this synchronization `9b2c1cf5f8812a5a93296a71c9ec90ee4e3dcd05`
- factorial handoff PR: **#265**, head before this synchronization `d78f99507d886e8b26606061856cd0a5e2b20146`
- PR #262 verification: workflow `38147114407`, job `114492689105`, **94 passed in 1.04 s**
- no H0/H1/H2/H3/C_OBS/C_BIO scientific outcome has been generated or read.

## 2. Scientific objective

The synthetic generator must separate, as far as the real TRAIN design allows:

`latent biology -> observation process -> observed counts`

The intended downstream factorial worlds remain:
- H0 baseline E2 biology + baseline observer
- H1 hierarchical anonymous biology + baseline observer
- H2 baseline E2 biology + explicit observer
- H3 hierarchical anonymous biology + explicit observer
- C_OBS same latent biology through different observation regimes
- C_BIO different latent biology through the same observation regime

Biological identity must stay anonymous. No target-discovery ranks, SCENIC+/ATAC target evidence, pathology, TEST/Morabito, or named real programs may be planted into synthetic truth.

## 3. Corrected S174 data custody

Physical corrected-TRAIN cache on the execution machine:
`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Do not reconstruct S174 from the larger 50K corpus. The repair preserves exactly the historical **4,726 cell IDs in historical order** while correcting physical-source expression values.

Authenticated physical replay facts from PR #280:
- 84/84 shard files verified
- 0 missing, 0 extra
- shard authority: `results/v79/V79_S174_SHARD_AUTHORITY_V1.json`
- authority SHA-256: `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- bridge: `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`
- bridge SHA-256: `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`
- cells: 4,726
- donors: 149 = HVS 62, NPH52 19, SEA_AD 68
- cells by source: HVS 3,072; NPH52 246; SEA_AD 1,408
- operators: 42
- sources: 3
- broad classes: 3
- donor-class groups: 426

Historical repaired TRAIN archive receipt remains part of provenance:
- `s174_rebuilt_real_train_v1.rar`
- historical archive SHA-256 recorded by the V78/S174 lineage: `88067f2...`

## 4. Bayesian model-development history

### 4.1 Detection/Bernoulli V2 is a real failed qualification
The frozen hierarchical Bernoulli V2 failed S4 under its precommitted contract:
- worst ESS `361.8761303230284`
- required minimum `400`
- worst R-hat `1.0050606796610788`
- final divergences `0`

Ruling:
`DETECTION_V2_NOT_QUALIFIED`

No threshold relaxation or relabeling is allowed. The historical no-V3 rule applies to that specific confirmatory sequence. This failure does **not** mean a separate detection process is unnecessary.

### 4.2 Old Gaussian/lognormal/ZTNB campaign is on methodological hold
The old monolithic Gaussian/lognormal/ZTNB S0-S5 recovery campaign is **not** a failed family result. It is:
`UNADJUDICATED__METHODOLOGICAL_HOLD`

The scheduler was stopped before 17/18 queued fresh fits launched. A running Gaussian S1 fit was stopped under the controller hold and is not a scientific ruling.

Do not restart that campaign.

### 4.3 Empirical auxiliary tournament
Authenticated auxiliary fit-population development used 10,379 donor-balanced cells across all 104 fit donors. This is development evidence only, not final S174 authority.

Key result: a two-part architecture is empirically supported over one-piece NB.

Held-out-donor development values:
- NB2 fixed-depth mean LPD: `-1.43373`
- NB2 free-depth mean LPD: `-1.40428`
- hurdle lognormal mean LPD: `-1.30285`
- hurdle ZTNB mean LPD: `-1.30617`
- NB2 fixed-depth implied-zero log loss: `0.37573`
- NB2 free-depth implied-zero log loss: `0.35608`
- explicit logistic detection log loss: `0.26179`

Explicit detection beat free-depth NB2 on all 10 sampled genes. Positive-family separation between lognormal and ZTNB was negligible (`ZTNB - lognormal` mean LPD about `-0.00332`; 7 lognormal gene wins / 3 ZTNB wins).

Interpretation: keep a separate detection component; do not resurrect the failed deep Bernoulli V2 hierarchy.

### 4.4 Auxiliary hierarchy pruning
On the larger development panel, held-out-donor nested detection log loss was approximately:
- depth linear `0.466368`
- depth quadratic `0.463706`
- + broad class `0.416760`
- + source `0.330816`
- + operator `0.322037`

Positive lognormal held-out-donor LPD was approximately:
- depth `-2.233011`
- + class `-2.187061`
- + source `-2.080901`
- + operator `-2.039129`

Auxiliary residual evidence supported donor strongly, operator provisionally, and did not broadly support donor×class. However, the earlier auxiliary operator residual-support null was weaker because it did not fully control donor composition. Therefore exact S174 must use the stronger donor-controlled operator null described below.

## 5. Current development candidate entering exact S174

This is a **candidate**, not a qualified model.

Per gene, modularly:

### Detection
`detected ~ Bernoulli(logit^-1(intercept + quadratic(log_library) + broad_class + source + operator_within_source + donor_within_source))`

### Positive magnitude
`log(count) | count > 0 ~ Normal(intercept + quadratic(log_library) + broad_class + source + operator_within_source + donor_within_source, sigma)`

Current structural defaults before exact S174 metrics:
- quadratic depth: IN provisionally
- broad class: IN provisionally
- source: IN provisionally
- operator-within-source: IN provisionally
- donor-within-source: IN provisionally
- donor×class: OUT provisionally
- source×class: OUT
- free matrix/dataset identity: OUT
- positive family: lognormal development default
- ZTNB: challenger, not rejected
- genes: modular per-gene fits
- across-gene geometry: second-stage meta-distribution from per-gene summaries

## 6. Resource-safe implementation — PR #279

Important files:
- `.github/workflows/v79-streaming-analysis-cache.yml`
- `scripts/v79/build_v79_analysis_cache.py`
- `scripts/v79/run_v79_s174_structure_replay.py`
- `scripts/v79/run_v79_scheduler.py`
- `tests/v79/test_v79_analysis_cache.py`
- `tests/v79/test_v79_s174_structure_replay.py`
- `tests/v79/test_v79_scheduler_resource_defaults.py`
- `docs/agent/V79_S174_STREAMING_STRUCTURE_REPLAY_EXECUTION_20261011.md`

Qualified engineering behavior:
- exactly two count-stream passes for compact-cache construction
- at most one count-shard CSR resident
- no global 4,726×41,238 CSR assembly / no global `vstack`
- metadata design parsed from the exact authenticated bytes already read
- identity-blind prevalence-stratified gene panel
- hash-bound cache receipt
- later replay reads only the compact cache, not the 41K shards
- NumPy/SciPy only for this development replay; no JAX/NUTS
- full-rank operator-within-source proxy encoding
- donor-held-out folds
- donor-controlled operator-support null using donor-centered residuals and within-donor permutation

Scheduler safety:
- default one machine-wide heavy fit
- default settle interval 120 s
- explicit override required for higher concurrency

Measured historical heavy-fit resource evidence:
- peak RSS ~1.32 GB
- mean process CPU ~10.28 logical CPUs
- whole-machine CPU ~93.1%
- wall time ~1561.5 s

Conclusion: heavy Bayesian fitting is primarily CPU-bound; expression I/O was being needlessly repeated but is not the dominant fit bottleneck.

## 7. Physical G500 compact cache result — PASS

PR #280 built the exact corrected-S174 compact cache successfully:
- cache file: `V79_ANALYSIS_CACHE_G500.npz`
- real-count cache stays on the execution machine; do not commit its bytes
- size: 1,071,307 bytes (~1.07 MB)
- SHA-256: `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`
- streaming passes: 2
- max count shards resident: 1
- global sparse assembly: false
- metadata from authenticated bytes: true
- identity-blind genes: 500
- source universe with prevalence >=5%: 14,417 genes
- panel prevalence min `0.050`, median `0.242`, max `0.949`
- prevalence bins: [.05,.1)=96, [.1,.2)=113, [.2,.3)=83, [.3,.5)=103, [.5,.7)=63, [.7,.9)=31, [.9,1]=11
- build wall time reported ~3 s

This cache is valid and should **not be rebuilt** for the next replay unless custody/hash verification fails.

Committed cache evidence in PR #280:
- `results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500_RECEIPT.json`
- `results/v79/development/s174_structure_replay/V79_G500_PANEL_PREVALENCE_COVERAGE.json`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_EXECUTION_PROVENANCE.json`
- `build_cache.stdout.txt`
- `build_cache.stderr.txt`

## 8. First physical structure replay — FAILED CLOSED BEFORE METRICS

Frozen command parameters:
- 200 replay genes
- 50 support genes
- 3 held-out-donor folds
- 99 permutations
- seed `20261011`

The replay stopped on the first non-converged logistic operator fit. No replay JSON, held-out log loss, LPD, A-H answer, or model-selection metric was produced or seen.

The convergence-only diagnosis deliberately computed no predictive metric.

Diagnosis:
- total planned detection fits: 3,000
- all four simpler nested models converged in every fit
- operator-within-source non-converged fits: **155/600**
- genes with at least one operator failure: 84/200
- operator fits with at least one all-zero or all-one training operator level: **351/600**
- failing fits reached maxiter 300
- failing gradient infinity norms about `0.003–0.016`
- failing maximum absolute coefficients about `6–14` on the logit scale

Cause: quasi-separation. Under donor-held-out folds, some operator×gene training cells are all detected or all undetected. The previous tiny common ridge `1e-4` becomes the effective determinant of these operator coefficients.

Interpretation:
- this is a failure of the cheap unrestricted-ish operator fixed proxy under separation;
- it is **not evidence for or against an operator effect**;
- questions A-H remain unanswered because the frozen runner correctly failed closed before writing any metric.

Committed failure/diagnosis artifacts in PR #280:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_EXECUTION_RECORD_20261011.md`
- `results/v79/development/s174_structure_replay/replay.stdout.txt` (empty)
- `results/v79/development/s174_structure_replay/replay.stderr.txt`
- `results/v79/development/s174_structure_replay/diagnose_replay_convergence.py`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS.json`
- active state update on PR #280

## 9. Prospective repair decision — fixed before any predictive metric

The controller decision is preserved as PR #280 issue comment `6112948943` and is now part of this handoff.

### Primary operator regularization
Use an explicit penalty on **operator-within-source columns only**.

Primary convention:
- Gaussian operator coefficient prior SD = 1 on the linear-predictor scale
- equivalent ridge `lambda = 1` on operator-within-source columns only

Intercept, depth, class, and source retain their existing frozen treatment.

### Frozen sensitivity set
Before seeing any replay metric, freeze:
- `lambda = 0.25` (approx prior SD 2)
- `lambda = 1` (primary; prior SD 1)
- `lambda = 4` (approx prior SD 0.5)

These are robustness checks, not selectable alternatives.

### Interpretation rule
Question D / operator effect may be called supported only if:
- the held-out-donor operator increment has the same direction at all three penalties; and
- the increment remains materially present across all three.

If the conclusion changes materially across `{0.25,1,4}`:
`PRIOR_SENSITIVE__UNRESOLVED`

The same robustness rule applies to donor-controlled operator residual support.

### Frozen replay invariants
Do not change:
- folds
- selected G500 cache
- 200-gene replay panel rule
- 50-gene support panel rule
- seed
- metrics
- covariates
- operator pooling
- gene inclusion after outcomes
- maxiter/convergence threshold for the first repaired replay

Every primary `lambda=1` fit must converge or the replay fails closed again. Sensitivity failures are reported; there is no rescue tuning.

### TDD required before rerun
Add tests proving:
1. only operator columns receive the stronger penalty;
2. source + operator-within-source design remains full rank;
3. synthetic separated operator levels converge at primary lambda=1;
4. non-operator nested outputs remain unchanged by the repair;
5. sensitivity set is exactly `{0.25,1,4}` and cannot be adapted from replay outcomes.

## 10. Immediate Macha instruction

Macha should do exactly this next and nothing beyond it:

1. implement the prospective operator-regularization repair on the **PR #279 implementation line**, test-first;
2. get CI green;
3. verify the existing physical G500 cache hash/custody; **do not rebuild it** if valid;
4. rerun the exact same cache-only S174 replay with primary lambda=1 and frozen sensitivities 0.25/4;
5. produce A-H development results and machine-readable receipts;
6. commit provenance, per-gene deltas, convergence status, donor support, donor-controlled operator support, donor×class incremental support, and sensitivity results;
7. stop for controller audit.

No NUTS. No restart of the old 18-fit campaign. No H0-H3 execution. No posterior export. No JEPA training.

Expected successful terminal:
`EXACT_S174_STRUCTURE_REPLAY_COMPLETE__PRIMARY_OPERATOR_LAMBDA_1__FROZEN_SENSITIVITY_0p25_1_4__DEVELOPMENT_ONLY__CONTROLLER_MODEL_FREEZE_REQUIRED__BAYESIAN_CONFIRMATION_OFF__TRAINING_OFF`

If primary lambda=1 still fails:
`EXACT_S174_STRUCTURE_REPLAY_FAILED_CLOSED__REGULARIZED_OPERATOR_MODEL_NONCONVERGENCE__NO_POST_HOC_RESCUE__CONTROLLER_REVIEW_REQUIRED__TRAINING_OFF`

## 11. What A-H must answer after repaired replay

A. Does quadratic depth improve over linear depth on exact S174?

B. Does broad biological class improve detection and/or positive magnitude after depth?

C. Does source retain substantial information after depth + class?

D. Does operator-within-source improve held-out-donor prediction beyond source and remain robust to `{0.25,1,4}`?

E. Is residual donor organization supported after the fixed structure?

F. Does operator structure survive the stronger donor-controlled null, and is that conclusion penalty-robust?

G. Is donor×class increment beyond donor strong enough to restore donor×class to the candidate?

H. Does lognormal remain a stable development representation for positive counts? This cannot declare ZTNB inferior.

## 12. Decision after repaired S174 replay

If exact S174 broadly preserves the candidate:
1. freeze the next Bayesian candidate before simulation outcomes;
2. generate **new untouched synthetic qualification worlds** for that candidate;
3. freeze qualification thresholds/metrics;
4. run confirmatory recovery;
5. only after an independent pass may corrected-TRAIN Bayesian posterior authority be considered.

If S174 materially contradicts the candidate:
- return to development;
- do not add post-outcome terms to rescue it;
- do not choose penalties/genes based on desired direction;
- do not restart the old confirmation campaign as a substitute.

## 13. Downstream factorial state

PR #262 internal engineering is closed and verified (94 tests). That does **not** authorize scientific execution.

The downstream factorial lane must now treat Bayesian observation/biology authority as unresolved:
- old detection V2: NOT QUALIFIED
- old Gaussian/lognormal/ZTNB: UNADJUDICATED__METHODOLOGICAL_HOLD
- current empirical Candidate V2: DEVELOPMENT ONLY
- exact S174 repaired structure replay: pending

No Macha quantity from the held or failed models may be consumed as a qualified H1/H2/H3 authority.

Any future material H1/H2 authority change requires:
- prospective freeze;
- fresh byte-authenticated preexecution replay;
- independent gate audit;
- then and only then H0-H3/C_OBS/C_BIO execution.

## 14. Hard firewalls

Absolutely forbidden in this lane unless separately authorized later:
- TEST/Morabito
- pathology/clinical outcomes
- target-discovery ranks or panels
- SCENIC+/ATAC target evidence
- named real programs or exact real class-gene/donor-gene signatures in planted truth
- V78 outcome-driven retuning
- post-outcome synthetic arm rescue
- H0-H3 scientific execution before authority freeze/gates
- Stage4/500K
- JEPA training/checkpoints

`training_authorized = false`

## 15. New-agent startup checklist

A new supervising agent should, in order:
1. read this file;
2. read PR #280 execution record and controller repair comment;
3. read PR #279 execution contract and code/test inventory;
4. read current machine state `docs/agent/V79_BAYESIAN_GEOMETRY_CONTROLLER_STATE_20261011.json`;
5. confirm Macha source head before giving new instructions;
6. do not interpret any uncommitted local Macha run as terminal evidence;
7. keep target discovery separate;
8. supervise only the repaired S174 replay until it reaches a terminal result;
9. update audit + handoff + downstream factorial state together after that result.

The key methodological correction for this project is: **learn/compare on lawful TRAIN development evidence first; freeze the candidate second; qualify on untouched synthetic worlds third. Do not freeze a merely plausible model and learn only from qualification failure.**
