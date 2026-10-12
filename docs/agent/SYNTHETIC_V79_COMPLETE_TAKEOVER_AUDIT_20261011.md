# Synthetic/V79 complete takeover audit — 2026-10-11

Independent audit surface for the **synthetic dataset / V79 Bayesian geometry lane**. This file records what is actually established, what failed, what is only development evidence, and what the next controller is allowed to ask Macha to do.

Target discovery is a separate lane.

## Audit verdict

`PASS_ENGINEERING_AND_CUSTODY_TO_REPAIRED_S174_REPLAY__FIRST_STRUCTURE_REPLAY_FAILED_CLOSED_BEFORE_METRICS__PROSPECTIVE_OPERATOR_REGULARIZATION_REPAIR_FIXED_BEFORE_OUTCOMES__MODEL_NOT_QUALIFIED__FACTORIAL_SCIENCE_NOT_RUN__TRAINING_OFF`

## 1. Evidence hierarchy

### Terminal / authoritative evidence
- detection/Bernoulli V2 failed its frozen S4 recovery gate: ESS `361.8761303230284 < 400`; R-hat `1.0050606796610788`; final divergences `0`.
- exact corrected-S174 shard custody was verified on the physical execution machine: 84/84 required files, 0 missing, 0 extra.
- the physical exact-S174 G500 streaming compact cache passed its receipt contract.
- the first exact-S174 structure replay failed closed before any predictive metric was emitted because the operator-within-source logistic proxy did not converge under quasi-separation.
- the controller repair rule was frozen before any replay metric existed.

### Development evidence only
- auxiliary 50K fit-population model tournament and hierarchy pruning.
- current two-part Candidate V2 architecture.
- lognormal as positive-magnitude development default.
- any operator support observed in the auxiliary fit population.

### Not adjudicated
- old Gaussian/lognormal/ZTNB monolithic recovery families: `UNADJUDICATED__METHODOLOGICAL_HOLD`.
- exact-S174 A-H structure questions: unanswered until repaired replay.
- final Bayesian Candidate V2 qualification.
- H1/H2 synthetic authority.
- scientific factorial outcomes.

## 2. Current branches / PRs

- Macha source: `analysis/v79-bayesian-synthetic-geometry-20261009`, head `b06bd819abd7da1be0426767c6909f4cdc7cc7bf`
- audit PR #260: this branch
- controller/handoff PR #261
- resource-safe implementation PR #279
- physical execution record PR #280
- downstream factorial implementation PR #262
- downstream factorial audit PR #264
- downstream factorial handoff PR #265

## 3. Corrected-S174 custody audit

Physical source:
`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Do not substitute or regenerate from the 50K corpus.

Verified facts from PR #280:
- cells: 4,726
- donors: 149
- donor split: HVS 62 / NPH52 19 / SEA_AD 68
- cells by source: HVS 3,072 / NPH52 246 / SEA_AD 1,408
- operators: 42
- sources: 3
- broad classes: 3
- donor-class groups: 426
- authority file: `results/v79/V79_S174_SHARD_AUTHORITY_V1.json`
- authority SHA-256: `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- bridge: `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`
- bridge SHA-256: `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`
- 84 required shard files verified; 0 missing; 0 extra.

The exact repaired row identity/order is part of custody. Reconstructing a nominally similar 4,726-row set from the larger archive would create a different data object and is not allowed for this replay.

## 4. Bayesian scientific audit

### Detection V2
This is a genuine failed confirmatory qualification of that exact parameterization.

Do not relabel it. Do not relax thresholds after the fact. Do not use its parameters as synthetic authority.

### Old Gaussian/lognormal/ZTNB campaign
The later controller determined that the project had frozen plausible models before sufficiently characterizing the TRAIN geometry. The old campaign was therefore stopped on methodological grounds.

Status for each old family:
`UNADJUDICATED__METHODOLOGICAL_HOLD`

This is not a failure and not a pass.

### Empirical development correction
Auxiliary development evidence shows one-piece NB is inadequate relative to a two-part detection + positive-magnitude architecture.

Representative held-out-donor values:
- NB2 fixed-depth LPD `-1.43373`
- NB2 free-depth LPD `-1.40428`
- hurdle lognormal LPD `-1.30285`
- hurdle ZTNB LPD `-1.30617`
- NB2 fixed-depth implied-zero log loss `0.37573`
- NB2 free-depth implied-zero log loss `0.35608`
- explicit logistic detection log loss `0.26179`

The positive-family difference was negligible at this stage. Therefore lognormal is only a stable development default; ZTNB remains an unresolved challenger.

## 5. Candidate V2 audit status

Candidate before exact S174 metrics:

Detection:
`quadratic depth + broad class + source + operator-within-source + donor-within-source`

Positive magnitude:
`log(count)|count>0 ~ Normal(quadratic depth + broad class + source + operator-within-source + donor-within-source, sigma)`

Provisional exclusions:
- no donor×class default layer
- no source×class default layer
- no free matrix/dataset identity term

Implementation strategy:
- fit genes modularly
- estimate across-gene geometry second-stage
- avoid the previous monolithic hyper-SD hierarchy unless later evidence requires it

Audit correction: earlier auxiliary operator residual-support counts used a weaker source-stratified null. They are not sufficient authority. Exact S174 must evaluate operator beyond donor with donor-centered residuals and a within-donor permutation null fixed before outcomes.

## 6. Resource engineering audit — PR #279

Relevant implementation files:
- `.github/workflows/v79-streaming-analysis-cache.yml`
- `scripts/v79/build_v79_analysis_cache.py`
- `scripts/v79/run_v79_s174_structure_replay.py`
- `scripts/v79/run_v79_scheduler.py`
- `tests/v79/test_v79_analysis_cache.py`
- `tests/v79/test_v79_s174_structure_replay.py`
- `tests/v79/test_v79_scheduler_resource_defaults.py`
- `docs/agent/V79_S174_STREAMING_STRUCTURE_REPLAY_EXECUTION_20261011.md`

Verified code head:
`2d5de281a171f0510d22a7408780fb069625ea02`

Verification:
- workflow `38166126568`
- job `114548954034`
- **15 passed in 1.27 s**

The tests forced repairs for:
- hidden global sparse `vstack`
- verification paths that reloaded the full matrix
- metadata reread after authentication
- provenance time-of-check/time-of-use gap
- prevalence-biased cache subpanel selection
- rank-deficient source+operator encoding
- operator support null not controlling donor
- unsafe scheduler default of two simultaneous heavy fits

Qualified cache behavior:
- two count-stream passes
- max one count-shard CSR resident
- no global sparse assembly
- metadata design parsed from authenticated bytes
- compact cache hash-bound to receipt
- later replay consumes only compact cache

Scheduler default:
- one machine-wide heavy fit
- 120-second settle interval

Historical measured Bayesian fit resource evidence:
- ~1.32 GB peak RSS
- ~10.28 logical CPUs average process usage
- ~93.1% whole-machine CPU
- ~1561.5 seconds wall time

Audit interpretation: heavy NUTS is CPU-bound; streaming is still necessary to eliminate redundant I/O/RAM churn but does not solve sampler CPU saturation.

## 7. Physical G500 cache audit — PASS

Physical cache:
- SHA-256 `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`
- bytes `1,071,307`
- 500 identity-blind genes
- source prevalence universe >=5%: 14,417 genes
- min prevalence `0.050`
- median `0.242`
- max `0.949`
- bins [.05,.1)=96 / [.1,.2)=113 / [.2,.3)=83 / [.3,.5)=103 / [.5,.7)=63 / [.7,.9)=31 / [.9,1]=11

The cache contains real counts and therefore remains local. Its receipt and coverage summary are committed; the count bytes are not.

Do not rebuild it unless its hash/custody fails.

## 8. First structure replay audit — FAILED CLOSED

Frozen replay scope:
- 200 genes
- 50 support genes
- 3 donor-held-out folds
- 99 permutations
- seed `20261011`

No predictive metric was produced.

Convergence-only diagnosis:
- simpler nested models: 0 failures
- operator-within-source model: 155 non-converged fits / 600
- genes with any failure: 84 / 200
- operator fits with at least one constant all-zero/all-one training operator level: 351 / 600

Observed failure signature:
- maxiter 300 reached
- gradient infinity norms ~0.003–0.016
- maximum absolute coefficients ~6–14

The previous common ridge `1e-4` is too weak under separation and becomes the effective determinant of some operator coefficients.

Audit ruling:
`FAILED_PROXY_UNDER_SEPARATION__NOT_EVIDENCE_FOR_OR_AGAINST_OPERATOR_EFFECT`

A-H remain unanswered.

PR #280 artifacts to preserve:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_EXECUTION_RECORD_20261011.md`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_EXECUTION_PROVENANCE.json`
- `results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500_RECEIPT.json`
- `results/v79/development/s174_structure_replay/V79_G500_PANEL_PREVALENCE_COVERAGE.json`
- `results/v79/development/s174_structure_replay/replay.stdout.txt`
- `results/v79/development/s174_structure_replay/replay.stderr.txt`
- `results/v79/development/s174_structure_replay/diagnose_replay_convergence.py`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS.json`

## 9. Prospective operator repair audit

Controller decision is frozen in PR #280 comment `6112948943`, created before any predictive replay metric.

Primary operator penalty:
- ridge lambda `1` on operator-within-source columns only
- equivalent Gaussian prior SD ~1 on operator coefficients

Frozen sensitivity set:
- lambda `0.25`
- lambda `1` primary
- lambda `4`

Approximate prior SDs:
- 2
- 1
- 0.5

No post-hoc penalty selection is allowed.

Question D / operator may be supported only if the held-out-donor increment has the same direction and remains materially present across all three penalties. Otherwise:
`PRIOR_SENSITIVE__UNRESOLVED`

Operator residual-support adjudication must use donor-centered residuals and within-donor permutation at all three penalties under the same robustness rule.

Frozen invariants for first repaired replay:
- G500 cache
- folds
- panel-selection rule
- support-panel rule
- seed
- covariates
- metrics
- maxiter
- convergence criterion

Do not pool rare operators, drop failing genes, or add post-outcome covariates.

Required RED/GREEN tests before rerun:
1. only operator columns receive new penalty
2. source + operator-within-source design remains full rank
3. synthetic separated operator levels converge at primary lambda=1
4. non-operator nested outputs unchanged
5. frozen sensitivity set exactly `{0.25, 1, 4}` and not adaptive

## 10. Downstream factorial audit status

PR #262 engineering remains closed and verified:
- head `9110c3fae6d34e43463d56631f43004bda33beb8`
- workflow `38147114407`
- job `114492689105`
- **94 passed in 1.04 s**

This proves implementation/scoring/receipt behavior only.

Current upstream authority status for factorial integration:
- old detection V2: NOT QUALIFIED
- old Gaussian/lognormal/ZTNB: methodological hold / not authority
- empirical Candidate V2: development only
- exact S174 repaired replay: pending

Therefore no Macha Bayesian quantity may yet be consumed into H1/H2/H3 as qualified authority.

Any material successor authority requires prospective freeze + fresh byte-authenticated preexecution replay + independent audit before scientific factorial execution.

## 11. Next allowed Macha work

Only:
1. implement operator-only regularization repair on PR #279 line, test-first;
2. obtain green CI;
3. verify existing G500 cache hash/custody and reuse it;
4. rerun the same cache-only exact-S174 replay with primary lambda=1 and frozen sensitivities 0.25/4;
5. commit A-H metrics/results, per-gene deltas, convergence record, donor support, donor-controlled operator support, donor×class increment, positive-lognormal stability, and sensitivity results;
6. stop for controller review.

No NUTS. No old recovery queue. No factorial science. No training.

## 12. Firewalls

Forbidden:
- TEST/Morabito
- pathology/clinical outcomes
- target-discovery work in this lane
- SCENIC+/ATAC target evidence in planted truth
- V78 outcome-driven retuning
- post-outcome synthetic rescue
- H0-H3/C_OBS/C_BIO scientific execution before authority gates
- Stage4/500K
- JEPA training/checkpoints

## 13. New-agent audit checklist

A new auditor should verify, in order:
1. live Macha source head has not moved unexpectedly;
2. PR #280 remains the immutable failed-closed first replay record;
3. operator repair exactly matches comment `6112948943`;
4. RED/GREEN evidence exists for the repair;
5. physical cache SHA still equals `2f922c08...` before reuse;
6. repaired replay does not alter panels/folds/seeds/metrics;
7. no hidden predictive metric was generated before the repair choice;
8. A-H are reported without selective omission;
9. audit + handoff + factorial downstream states are updated together after the repaired replay.

The governing methodological principle is now explicit: **empirical development first, prospective freeze second, untouched confirmatory qualification third.**
