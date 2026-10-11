# Synthetic/V79 new-agent takeover handoff — 2026-10-11

This is the canonical human-readable handoff for the **synthetic dataset / V79 Bayesian geometry lane**. Target discovery is a separate parallel lane and must not be mixed into this work.

## 0. Current terminal state

`CANDIDATE_V2_CORE_FROZEN_FOR_NEW_SYNTHETIC_QUALIFICATION__OPERATOR_EXTENSION_RETURNED_TO_DEVELOPMENT__EXACT_S174_REPLAY_COMPLETE__BAYESIAN_REAL_TRAIN_INFERENCE_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

The project has completed empirical model development on exact corrected S174 and has frozen a **core model structure** for a new confirmatory synthetic qualification cycle. The model is **not yet qualified**. No corrected-TRAIN Bayesian posterior authority fit is authorized yet.

## 1. Start here

Canonical branches / PRs:
- audit: PR #260, branch `audit/v79-bayesian-geometry-snapshot-20261010`
- handoff: PR #261, branch `handoff/v79-bayesian-geometry-takeover-20261010`
- streaming / replay implementation: PR #279
- immutable first failed exact-S174 replay: PR #280
- operator regularization repair: PR #283
- completed exact-S174 replay: PR #285
- downstream factorial implementation: PR #262
- downstream factorial audit: PR #264
- downstream factorial handoff: PR #265

Machine-readable controller state:
`docs/agent/V79_BAYESIAN_GEOMETRY_CONTROLLER_STATE_20261011.json` schema V8.

Artifact index:
`docs/agent/SYNTHETIC_V79_TAKEOVER_ARTIFACT_INDEX_V2_20261011.json`.

Macha next-execution contract:
`docs/agent/SYNTHETIC_V79_MACHA_V2_CORE_QUALIFICATION_CONTRACT_20261011.md`.

## 2. Historical Bayesian status

### Detection/Bernoulli V2
Terminally **NOT_QUALIFIED** under its frozen S4 contract:
- worst ESS `361.8761303230284`
- frozen minimum ESS `400`
- worst R-hat `1.0050606796610788`
- final divergences `0`

This is a real failure of that exact parameterization. Do not resurrect it, relax its thresholds, or treat its parameters as authority.

### Old Gaussian / lognormal / ZTNB monolithic campaign
Status for all three:
`UNADJUDICATED__METHODOLOGICAL_HOLD`

The old 18-fit recovery campaign was stopped because the project had frozen plausible models before sufficiently characterizing TRAIN geometry. Those old results are neither pass nor fail authority for the new V2 core.

## 3. Methodological correction now governing this lane

The operating rule is now:

**empirical development -> model comparison -> freeze -> new untouched qualification -> real posterior fit**

not:

**plausible model -> freeze early -> learn from qualification failure**.

Development failures can inform a new generation, but a changed model must receive a new prospective qualification suite. A failed confirmatory cycle is never retroactively erased.

## 4. Exact corrected-S174 custody

Physical repaired TRAIN substrate:
`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Do not reconstruct it from the larger 50K archive. Exact historical 4,726-cell row identity/order is part of custody.

Verified in PR #280:
- 4,726 cells
- 149 donors
- HVS: 3,072 cells / 62 donors
- NPH52: 246 cells / 19 donors
- SEA_AD: 1,408 cells / 68 donors
- 42 operators
- 3 sources
- 3 broad classes
- 426 donor-class groups
- 84/84 authority files verified
- 0 missing
- 0 extra

Authority:
`results/v79/V79_S174_SHARD_AUTHORITY_V1.json`
SHA-256:
`04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`

Operator bridge:
`results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`
SHA-256:
`b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`

## 5. Resource-safe data path

PR #279 replaced pseudo-streaming with a true bounded two-pass cache builder.

Verified code head:
`2d5de281a171f0510d22a7408780fb069625ea02`

CI:
- run `38166126568`
- job `114548954034`
- **15 passed in 1.27 s**

Important files:
- `.github/workflows/v79-streaming-analysis-cache.yml`
- `scripts/v79/build_v79_analysis_cache.py`
- `scripts/v79/run_v79_s174_structure_replay.py`
- `scripts/v79/run_v79_scheduler.py`
- `tests/v79/test_v79_analysis_cache.py`
- `tests/v79/test_v79_s174_structure_replay.py`
- `tests/v79/test_v79_scheduler_resource_defaults.py`
- `docs/agent/V79_S174_STREAMING_STRUCTURE_REPLAY_EXECUTION_20261011.md`

Qualified cache behavior:
- exactly two count-shard passes
- at most one count-shard CSR resident
- no global sparse `vstack`
- metadata parsed from exact authenticated bytes already read
- compact cache hash-bound to receipt
- repeated folds consume only compact cache

Heavy scheduler defaults:
- one machine-wide heavy fit
- 120-second settle interval

Historical resource evidence from one Gaussian NUTS fit:
- peak RSS ~1.32 GB
- mean process CPU ~10.28 logical CPUs
- mean whole-machine CPU ~93.1%
- wall time ~1561.5 s

Interpretation: heavy Bayesian inference is CPU-bound more than expression-I/O-bound. Streaming removes avoidable RAM/I/O churn but does not justify parallel heavy NUTS fits.

## 6. Physical G500 cache

Status: PASS.

SHA-256:
`2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`

Size: `1,071,307` bytes.

Contents:
- 500 identity-blind genes
- prevalence range 0.050 to 0.949
- median prevalence 0.242
- real counts

The raw cache stays local and is not committed. Reuse it for replay evidence. Do not rebuild it unless hash/custody fails.

## 7. First exact-S174 replay — immutable failure record

PR #280 is the immutable failed-closed record.

No predictive metric was emitted before failure.

Convergence-only diagnosis:
- four simpler nested models: 0 failures
- operator-within-source model: 155/600 non-converged fits
- 84/200 genes had at least one failure
- 351/600 operator fits had at least one all-zero/all-one operator level in TRAIN

Cause:
`QUASI_SEPARATION_WITH_TINY_COMMON_RIDGE_1E-4`

This was a proxy/identifiability problem, not evidence for or against a real operator effect.

Important PR #280 files:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_EXECUTION_RECORD_20261011.md`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_EXECUTION_PROVENANCE.json`
- `results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500_RECEIPT.json`
- `results/v79/development/s174_structure_replay/V79_G500_PANEL_PREVALENCE_COVERAGE.json`
- `results/v79/development/s174_structure_replay/diagnose_replay_convergence.py`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS.json`
- replay stdout/stderr logs

## 8. Prospective operator repair

Frozen before repaired replay metrics in PR #280 comment `6112948943`.

Implemented by PR #283:
- head `02fb78c36473d9863ae9482619133c052ba4a480`
- CI run `38170751947`
- job `114562666364`
- **22 passed**

Frozen operator penalties:
- primary lambda `1`
- sensitivities `0.25` and `4`
- operator-within-source columns only
- same convention in detection and positive proxies
- non-operator paths unchanged
- primary failures fail closed
- sensitivity failures recorded, not rescued

The code-fixed operator materiality convention is ratified **for this development replay only**. It is not a universal inferential threshold because genes share cells/donors and the gene bootstrap is optimistic.

## 9. Completed exact-S174 replay

PR #285:
- head `2c230a70d9151e27b14ec2788d1309eb2ac81468`
- same authenticated G500 cache reused; not rebuilt
- 200 replay genes
- 50 support genes
- 3 donor-held-out folds
- 99 permutations
- seed `20261011`
- every primary lambda=1 fit converged
- one lambda=0.25 detection sensitivity fit failed and was retained, not rescued

Important result files:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_V3_RESULT_20261011.md`
- `results/v79/development/s174_structure_replay_v3/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3.json`
- `results/v79/development/s174_structure_replay_v3/V79_S174_REPLAY_PER_GENE_NESTED_DELTAS.json`
- replay stdout/stderr

### Exact S174 A-H rulings

A. Quadratic depth — **SUPPORTED in both parts**.

B. Broad class — **SUPPORTED in both parts** and the strongest consistent increment.

C. Source — **SUPPORTED for detection**; **weak but reproducible for positive magnitude**.

D. Operator main effect:
- detection: `PRIOR_SENSITIVE__UNRESOLVED`
- positive magnitude: `NOT_SUPPORTED`

E. Donor — **SUPPORTED**:
- detection 32/50 support genes
- positive 19/50
- chance expectation ~2.5/50

F. Operator beyond donor — residual organization exists:
- detection 37/50
- positive 23/50
but this structure did **not** behave like a stable transferable fixed operator effect across unseen donors.

G. Donor×class — **OUT by default**. Positive is at chance; detection is marginal and not sufficient to justify a default hierarchy.

H. Lognormal — **stable development default**. ZTNB remains an unadjudicated challenger, not rejected.

## 10. Frozen CANDIDATE_V2_CORE

This structure is frozen for **new synthetic qualification**, not yet qualified.

### Detection per gene

`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

### Positive magnitude per gene

`log(count) | count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Structural rulings:
- quadratic depth IN
- broad class IN
- source IN
- positive source retained with appropriate shrinkage because the signal is weak but reproducible
- donor-within-source IN as hierarchical / partially pooled structure
- donor×class OUT
- source×class OUT
- operator main effect OUT of core
- free matrix/dataset identity OUT
- genes modular per gene
- across-gene geometry second-stage
- lognormal current positive-family development default
- ZTNB separate challenger

## 11. Operator extension

Operator is not deleted from scientific consideration. It is moved to a **separate development extension**.

Reason:
- donor-controlled residual operator organization is real;
- fixed operator detection effect is prior-sensitive;
- fixed operator positive effect worsens held-out-donor prediction.

A future operator extension must be prospectively specified, use hierarchical shrinkage, and demonstrate out-of-donor predictive value or another predeclared external criterion before it can enter authority.

It must not block V2_CORE qualification.

## 12. Immediate next Macha task

Do **not** run corrected-TRAIN NUTS.

Immediate deliverable:
`V79_V2_CORE_FROZEN_MODEL_AND_PROSPECTIVE_SYNTHETIC_QUALIFICATION_CONTRACT`

Macha must first commit, before expensive fitting:
1. exact Bayesian V2_CORE implementation/config
2. exact priors
3. exact centered/non-centered parameterization choices
4. new untouched synthetic-world manifest
5. truth table and seeds
6. recovery/identifiability metrics
7. frozen thresholds
8. retry/extension path
9. sampler/environment lock
10. resource policy
11. result schema
12. combined terminal receipt logic

Required world families:
- Q0 baseline
- Q1 weak donor
- Q2 strong donor
- Q3 weak source
- Q4 source absent
- Q5 class absent
- Q6 quadratic depth absent
- Q7 donor absent
- Q8 sparse detection stress
- Q9 positive-magnitude tail stress
- Q10 realistic weak-crossing / imbalance stress
- Q11 mild omitted-operator misspecification stress

The omitted-operator world is allowed only as a robustness test of the **core**. It does not authorize fitting operator.

After contract freeze, Macha may run confirmatory synthetic qualification. Any frozen criterion failure after the allowed retry path is a real failed qualification generation. No within-cycle tuning.

Even after a complete PASS, Macha must stop for controller audit before any corrected-TRAIN posterior fit.

## 13. Downstream factorial lane

PR #262 engineering is closed and verified:
- head `9110c3fae6d34e43463d56631f43004bda33beb8`
- CI `38147114407`
- job `114492689105`
- **94 passed in 1.04 s**

This is engineering only. No H0/H1/H2/H3/C_OBS/C_BIO outcome has been authorized or read.

No present Bayesian posterior quantity is qualified to alter H1/H2/H3.

If V2_CORE later qualifies and a material synthetic authority is frozen, downstream factorial still requires:
1. frozen authority bytes/receipt
2. fresh byte-authenticated preexecution replay
3. independent final audit
4. only then scientific factorial execution

## 14. Hard firewalls

Forbidden in this lane unless the controller later changes state:
- TEST / Morabito
- pathology / clinical labels
- target-discovery work
- SCENIC+ / ATAC target evidence in synthetic planted truth
- V78 outcome-driven retuning
- old 18-fit campaign resurrection
- detection V2/V3 rescue
- corrected-TRAIN posterior inference before V2_CORE synthetic qualification + audit
- H0/H1/H2/H3/C_OBS/C_BIO scientific execution
- Stage4/500K
- JEPA training/checkpoints

`training_authorized=false`

## 15. New-agent supervision checklist

Before giving Macha any new instruction:
1. read PR #285 result and controller freeze comment `6113335756`;
2. read this handoff and controller state V8;
3. verify Macha has not started corrected-TRAIN posterior inference;
4. require prospective contract commit before qualification outcomes;
5. verify new world seeds/scenarios are fresh;
6. verify operator is absent from V2_CORE fitting;
7. verify old qualification worlds are not used as the sole confirmation set;
8. preserve one-heavy-fit machine rule;
9. update audit + handoff + downstream factorial states together after any terminal qualification ruling.

The scientific objective is still to obtain the richest defensible synthetic causal geometry without confusing source/operator acquisition structure with biological identity. The current V2_CORE is the first version in this sequence whose core structure was empirically earned before confirmatory qualification.
