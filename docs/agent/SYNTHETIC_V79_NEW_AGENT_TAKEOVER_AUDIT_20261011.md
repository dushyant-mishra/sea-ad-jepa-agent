# Synthetic/V79 new-agent takeover audit — 2026-10-11

Independent audit record for the **synthetic dataset / V79 Bayesian geometry lane**. Target discovery is separate and must not be imported into this lane.

## Audit verdict

`PASS_EXACT_S174_DEVELOPMENT_REPLAY__V2_CORE_STRUCTURE_EARNED_WITH_OPERATOR_EXCLUDED__OPERATOR_EXTENSION_UNRESOLVED_AND_RETURNED_TO_DEVELOPMENT__NEW_SYNTHETIC_QUALIFICATION_REQUIRED__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

## 1. What is terminal evidence

### Detection/Bernoulli V2
`NOT_QUALIFIED` under its frozen S4 contract:
- ESS `361.8761303230284 < 400`
- R-hat `1.0050606796610788`
- final divergences `0`

No V2/V3 rescue, threshold relaxation or parameter export is allowed.

### Corrected-S174 custody
PASS:
- 4,726 cells
- 149 donors
- 42 operators
- 3 sources
- 3 broad classes
- 426 donor-class groups
- 84/84 authority files verified
- 0 missing / 0 extra
- authority SHA `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- bridge SHA `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`

The exact 4,726-cell row set/order is part of authority. Do not reconstruct S174 from the 50K archive.

### G500 compact cache
PASS:
- SHA `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`
- 1,071,307 bytes
- 500 identity-blind genes
- prevalence 0.050–0.949, median 0.242
- real count bytes remain local and uncommitted

## 2. Resource engineering authority

PR #279 is the reusable implementation authority for the bounded cache/replay path.

Verified code head:
`2d5de281a171f0510d22a7408780fb069625ea02`

CI:
`38166126568` / `114548954034` — **15 passed in 1.27 s**.

Audited properties:
- two shard passes
- one count-shard CSR resident max
- no global sparse assembly
- authenticated metadata bytes used directly
- cache hash bound to receipt
- repeated analyses consume compact cache only
- scheduler default one heavy fit + 120 s settle

Important code/tests:
- `.github/workflows/v79-streaming-analysis-cache.yml`
- `scripts/v79/build_v79_analysis_cache.py`
- `scripts/v79/run_v79_s174_structure_replay.py`
- `scripts/v79/run_v79_scheduler.py`
- `tests/v79/test_v79_analysis_cache.py`
- `tests/v79/test_v79_s174_structure_replay.py`
- `tests/v79/test_v79_scheduler_resource_defaults.py`

Historical single Gaussian NUTS fit used ~1.32 GB peak RSS but ~93.1% machine CPU for ~1561.5 s. Audit conclusion: heavy fitting is CPU-bound; streaming prevents avoidable I/O/RAM churn but does not justify concurrent heavy fits.

## 3. Immutable first exact-S174 replay failure

PR #280 must remain an immutable historical record.

The frozen runner aborted before emitting predictive metrics.

Diagnosis:
- simpler nested models: 0 failed fits
- operator model: 155/600 non-converged
- 84/200 genes with any failure
- 351/600 operator fits had at least one constant detection level in TRAIN
- cause: quasi-separation with the tiny common ridge `1e-4`

Ruling:
`FAILED_PROXY_UNDER_SEPARATION__NOT_EVIDENCE_FOR_OR_AGAINST_OPERATOR_EFFECT`

Key evidence files in PR #280:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_EXECUTION_RECORD_20261011.md`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_EXECUTION_PROVENANCE.json`
- `results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500_RECEIPT.json`
- `results/v79/development/s174_structure_replay/V79_G500_PANEL_PREVALENCE_COVERAGE.json`
- `results/v79/development/s174_structure_replay/diagnose_replay_convergence.py`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS.json`

## 4. Prospective repair audit

Controller repair was fixed before repaired replay metrics in PR #280 comment `6112948943`.

PR #283 faithfully implemented it:
- head `02fb78c36473d9863ae9482619133c052ba4a480`
- CI `38170751947` / `114562666364`
- **22 passed**

Verified contract:
- operator-only ridge penalty
- primary lambda `1`
- frozen set `{0.25, 1, 4}`
- non-operator paths unchanged
- primary nonconvergence fails closed
- sensitivity failure is recorded, never rescued
- no adaptive penalty choice

The code-fixed materiality rule is ratified only for this development replay. It is not a universal significance threshold.

## 5. Completed exact-S174 replay audit

PR #285 reused the same G500 cache without rebuild.

Scope:
- 200 replay genes
- 50 support genes
- 3 donor-held-out folds
- 99 permutations
- seed `20261011`

Primary lambda=1: all fits converged.
One lambda=0.25 detection sensitivity fit failed and was preserved as a failure.

Key result files:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_V3_RESULT_20261011.md`
- `results/v79/development/s174_structure_replay_v3/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3.json`
- `results/v79/development/s174_structure_replay_v3/V79_S174_REPLAY_PER_GENE_NESTED_DELTAS.json`

Audited A–H:
- A quadratic depth: SUPPORTED both parts
- B broad class: SUPPORTED both parts
- C source: SUPPORTED detection; weak but reproducible positive
- D operator: detection `PRIOR_SENSITIVE__UNRESOLVED`; positive `NOT_SUPPORTED`
- E donor: SUPPORTED (32/50 detection, 19/50 positive)
- F operator beyond donor: residual structure above chance (37/50, 23/50) but not a stable transferable fixed effect
- G donor×class: OUT
- H lognormal: stable development default; ZTNB unadjudicated

## 6. Audit interpretation

The exact S174 data support a simpler two-part core.

Residual operator organization is real, but the project may not infer from that alone that an operator main effect belongs in the model. Detection gain is prior-sensitive and positive magnitude is harmed by the fixed operator proxy on held-out donors.

Therefore operator is excluded from the core and returned to a separate development track.

## 7. Frozen V2_CORE

Status:
`FROZEN_FOR_NEW_SYNTHETIC_QUALIFICATION__NOT_YET_QUALIFIED`

Detection:
`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive:
`log(count)|count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Audit rulings:
- quadratic depth IN
- broad class IN
- source IN; positive source requires shrinkage because effect is weak but reproducible
- donor-within-source IN as hierarchical effect
- operator OUT of core
- donor×class OUT
- source×class OUT
- free matrix/dataset identity OUT
- per-gene modular fits
- across-gene geometry second-stage
- lognormal development default
- ZTNB unresolved challenger

Controller model-freeze decision is preserved in PR #285 comment `6113335756`.

## 8. Operator extension audit status

`DEVELOPMENT_ONLY__NOT_AUTHORITY__MUST_NOT_BLOCK_V2_CORE`

Any future operator extension must be prospectively frozen, use hierarchical shrinkage, and demonstrate out-of-donor predictive value or another prospectively defined external criterion.

The Q11 omitted-operator stress world may test robustness of the core but does not authorize fitting operator.

## 9. Next confirmatory gate

No corrected-TRAIN Bayesian posterior fit yet.

Macha must first commit:
`V79_V2_CORE_FROZEN_MODEL_AND_PROSPECTIVE_SYNTHETIC_QUALIFICATION_CONTRACT`

Before qualification outcomes exist, the contract must freeze:
- exact model implementation/config
- priors
- parameterization
- new fresh world manifest
- truth table/seeds
- metrics
- thresholds
- recovery / retry policy
- sampler/environment versions
- resource policy
- result schema
- terminal combined-receipt logic

Required new world families:
Q0 baseline; Q1 weak donor; Q2 strong donor; Q3 weak source; Q4 source absent; Q5 class absent; Q6 quadratic absent; Q7 donor absent; Q8 sparse detection stress; Q9 positive tail stress; Q10 realistic weak-crossing imbalance; Q11 omitted-operator misspecification stress.

The old recovery worlds cannot be the sole confirmation set for V2_CORE.

If the frozen candidate fails a frozen criterion after its allowed recovery path, that qualification generation fails. Do not tune within the same confirmatory cycle.

If all worlds pass, stop for independent controller audit before corrected-TRAIN posterior inference.

## 10. Downstream factorial status

PR #262 remains engineering-qualified only:
- head `9110c3fae6d34e43463d56631f43004bda33beb8`
- CI `38147114407` / `114492689105`
- **94 passed in 1.04 s**

No scientific H0/H1/H2/H3/C_OBS/C_BIO outcomes are authorized.

No current Bayesian posterior quantity is synthetic authority.

A future qualified V2_CORE authority still requires:
1. frozen authority bytes / receipt
2. fresh byte-authenticated factorial preexecution replay
3. independent final gate audit
4. only then scientific factorial execution

## 11. Firewalls

Still forbidden:
- TEST/Morabito
- pathology
- target discovery in this lane
- SCENIC+/ATAC target evidence in planted truth
- V78 outcome-driven retuning
- old 18-fit restart
- detection V2/V3 rescue
- corrected-TRAIN posterior fit before new synthetic qualification + audit
- H0-H3/C_OBS/C_BIO scientific execution
- Stage4/500K
- JEPA training/checkpoints

`training_authorized=false`

## 12. Audit checklist for successor agent

Before approving any Macha execution:
1. inspect PR #285 and controller comment `6113335756`;
2. verify controller state and handoff agree;
3. verify exact V2_CORE does not contain operator or donor×class;
4. require the qualification contract to be committed before outcomes;
5. verify fresh seeds/scenarios are not recycled from old qualification;
6. verify absent-effect controls exist;
7. verify sampler retry path is frozen and fail-closed;
8. verify one-heavy-fit resource policy;
9. after terminal qualification, update audit, handoff and factorial integration states together.

This audit intentionally distinguishes **development evidence**, **frozen model structure**, and **confirmatory qualification**. The core is frozen; it is not yet qualified.
