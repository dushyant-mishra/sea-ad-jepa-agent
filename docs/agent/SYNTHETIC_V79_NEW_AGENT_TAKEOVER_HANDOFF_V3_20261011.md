# Synthetic/V79 lane — definitive new-agent takeover handoff V3

Date: 2026-10-11

Lane: `SYNTHETIC_DATASET_V79_BAYESIAN_GEOMETRY`

Target-discovery lane: **SEPARATE — DO NOT MIX**.

## Current terminal

`CONTRACT_V2_FINALIZATION_BLOCKED_ON_CROSS_PLATFORM_BYTE_REPRODUCIBILITY__NO_CANONICAL_WORLD_LAUNCH_AUTHORITY_YET__NO_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__REAL_TRAIN_POSTERIOR_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

The scientific V2_CORE structure is frozen and preserved after the structural-support correction. The only active blocker is deterministic finalization of the launch contract. No qualification world has been generated and no qualification fit has run.

## Canonical surfaces

- Audit: PR #260, branch `audit/v79-bayesian-geometry-snapshot-20261010`.
- Handoff: PR #261, branch `handoff/v79-bayesian-geometry-takeover-20261010`.
- Active contract-finalization line: PR #290, branch `feat/v79-v2-core-contract-final-20261011`, head `5394d036ccd423f9c61267fbdfeef6edd4912d37` at this handoff.
- Mask-corrected replay: PR #288, branch `fix/v79-s174-structural-support-mask-20261011`, head `c3cf9ad7472541bfb5ad632465c626c437f9a69c`.
- Duplicate controller-side finalizer PR #289 is closed as non-canonical and must never be consumed as authority.

## Controller rulings to preserve

1. PR #280 comment `6112948943`: prospective operator regularization repair before any repaired S174 metrics.
2. PR #285 comment `6113335756`: freeze `CANDIDATE_V2_CORE`, operator out of the core.
3. PR #286 comment `6113874774`: structural-support correction required before qualification; Q11 donor/PPC hard; terminal-lock semantics.
4. PR #288 comment `6114753697`: mask-corrected replay preserves all A-H classes; V2_CORE remains frozen unchanged; source magnitude reinterpreted.
5. PR #290 comment `6115051726`: finalization scientific payload accepted, but launch authority is blocked until final bytes are cross-platform deterministic by transforming the immutable accepted V2 draft instead of recomputing SciPy-derived reported values.

## Scientific architecture

The lane models real statistical geometry for anonymous synthetic biology and observation processes. It does not discover targets.

Frozen `V2_CORE`:

Detection:
`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive magnitude:
`log(count)|count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Structural decisions:
- quadratic depth: IN;
- broad class: IN;
- source: IN, with narrowed interpretation;
- donor-within-source: IN;
- operator main effect: OUT OF CORE;
- donor×class: OUT;
- source×class: OUT;
- free matrix/dataset identity: OUT;
- genes fit modularly;
- across-gene geometry is second-stage;
- lognormal is the current positive-family qualification family;
- ZTNB remains an unadjudicated challenger.

Source interpretation after masking:
`predictive/acquisition-source structure among estimable measured comparisons`.
It is not universal source biology, not causal source evidence, and not a biological mechanism. For genes measured in only one source, the cross-source estimand is UNDEFINED/UNEVALUABLE.

## Corrected S174 authority and custody

Physical repaired TRAIN substrate:
`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Verified population:
- 4,726 cells;
- 149 donors;
- 42 operators/matrices;
- 3 sources;
- 3 broad classes;
- 426 donor-class groups.

Source composition:
- HVS: 3,072 cells / 62 donors;
- NPH52: 246 cells / 19 donors;
- SEA_AD: 1,408 cells / 68 donors.

Shard authority:
- `results/v79/V79_S174_SHARD_AUTHORITY_V1.json`
- SHA-256 `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- 84/84 files verified, 0 missing, 0 extra.

Operator bridge:
- `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`
- SHA-256 `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`.

G500 compact cache:
- SHA-256 `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`;
- size 1,071,307 bytes;
- 500 identity-blind prevalence-stratified genes;
- contains real counts;
- local and intentionally uncommitted;
- reuse without rebuild unless custody/hash fails.

## Resource-safe data path — PR #279

PR #279 is the authoritative streaming/cache implementation lineage.

Verified code head: `2d5de281a171f0510d22a7408780fb069625ea02`.
Execution/doc snapshot: `615b55eb03b95630484b18d47de0ef7340368d37`.
CI: run `38166126568`, job `114548954034`, 15 passed in 1.27 s.

Important files:
- `.github/workflows/v79-streaming-analysis-cache.yml`
- `scripts/v79/build_v79_analysis_cache.py`
- `scripts/v79/run_v79_s174_structure_replay.py`
- `scripts/v79/run_v79_scheduler.py`
- `tests/v79/test_v79_analysis_cache.py`
- `tests/v79/test_v79_s174_structure_replay.py`
- `tests/v79/test_v79_scheduler_resource_defaults.py`
- `docs/agent/V79_S174_STREAMING_STRUCTURE_REPLAY_EXECUTION_20261011.md`

Engineering guarantees:
- two count-shard passes;
- max one count shard resident;
- no global 4,726×41,238 sparse assembly;
- authenticated metadata bytes;
- compact cache only for replay;
- default one heavy fit + 120 s settle.

## Historical model-development evidence

### Detection V2
Terminal `NOT_QUALIFIED`.
Frozen S4: worst ESS 361.8761303230284 < 400; R-hat 1.0050606796610788; 0 divergences. Do not resurrect or relax thresholds.

### Old Gaussian/lognormal/ZTNB campaign
All non-detection families remain `UNADJUDICATED__METHODOLOGICAL_HOLD`. Do not restart the old 18-fit campaign.

### Auxiliary empirical tournaments
Development-only evidence established:
- explicit detection beats count-only detection proxy;
- hurdle architectures outperform NB-only alternatives;
- class is essential;
- source adds detection signal;
- operator gave smaller residual gains but failed stable held-out-donor fixed-effect generalization;
- donor effects are strongly supported;
- donor×class is not broadly supported;
- lognormal is the stable development default; ZTNB implementation remained unadjudicated.

## First exact S174 replay — PR #280

Immutable failed-closed execution record.

G500 cache PASS, then the replay stopped before predictive metrics because operator-within-source logistic fits did not converge.

Diagnosis:
- depth linear: 0/600 failures;
- depth quadratic: 0/600;
- +class: 0/600;
- +source: 0/600;
- +operator: 155/600;
- 84/200 genes had at least one operator failure;
- 351/600 operator fits had a constant all-zero or all-one training operator level.

Interpretation: quasi-separation/ill-posed proxy, not evidence for or against true operator structure.

Important files:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_EXECUTION_RECORD_20261011.md`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_EXECUTION_PROVENANCE.json`
- `results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500_RECEIPT.json`
- `results/v79/development/s174_structure_replay/V79_G500_PANEL_PREVALENCE_COVERAGE.json`
- `results/v79/development/s174_structure_replay/diagnose_replay_convergence.py`
- `results/v79/development/s174_structure_replay/V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS.json`

## Operator repair — PR #283

Prospective rule fixed before metrics:
- primary operator lambda = 1;
- sensitivities = {0.25,1,4};
- penalty applies only to operator-within-source columns;
- no adaptive lambda choice;
- primary lambda=1 must converge or fail closed;
- detection operator support must be directionally/materially stable across lambdas or `PRIOR_SENSITIVE__UNRESOLVED`.

PR #283 head: `02fb78c36473d9863ae9482619133c052ba4a480`.
CI: `38170751947` / `114562666364`, 22 passed.

## Completed unmasked replay — PR #285

Head: `2c230a70d9151e27b14ec2788d1309eb2ac81468`.

A-H before support-mask correction:
- A quadratic depth: SUPPORTED both parts;
- B broad class: SUPPORTED both parts;
- C source: SUPPORTED detection; weak/reproducible positive;
- D operator: detection `PRIOR_SENSITIVE__UNRESOLVED`; positive `NOT_SUPPORTED`;
- E donor: SUPPORTED;
- F operator beyond donor: residual organization present, not transferable as a stable fixed effect;
- G donor×class: OUT;
- H lognormal: stable; ZTNB unadjudicated.

Controller froze V2_CORE and returned operator to separate development.

Important files:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_V3_RESULT_20261011.md`
- `results/v79/development/s174_structure_replay_v3/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3.json`
- `results/v79/development/s174_structure_replay_v3/V79_S174_REPLAY_PER_GENE_NESTED_DELTAS.json`

## Structural-support flaw and corrected replay — PR #288

Flaw: historical replay/cache semantics treated structurally unmeasured entries as measured zeros, violating `MEASURED_SCALAR != STRUCTURALLY_UNMEASURED`.

Support authority:
- Stage81A2R matrix-level measurement-support authority at commit `95d2cafe`;
- authority SHA prefix `ee5d12c1…`;
- joined through S174 operator bridge;
- support mask SHA `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`.

Removed:
- whole G500 cache: 136,098 / 2,363,000 = 5.76%;
- replay panel: 63,002 / 945,200 = 6.67%;
- 28/200 replay genes affected;
- 5/50 support genes affected.

Poison/sentinel tests prove unmeasured values are never consumed. Missing matrix×gene support fails closed.

Masked replay SHA:
`caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`

Masking audit SHA:
`6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41`

All A-H decision classes were preserved. Main quantitative correction:
- source detection median gain +0.00148 → +0.00091;
- mean +0.0226 → +0.0090;
- fraction improved 78% → 73.5%.

Six replay genes have detection source estimand undefined because they are measured in only one source; nine have positive-source estimand undefined. None were silently dropped.

Important files on #288:
- `docs/agent/V79_S174_STRUCTURE_REPLAY_V4_MASKED_RESULT_20261011.md`
- `results/v79/development/s174_structure_replay_v4_masked/V79_G500_STRUCTURAL_SUPPORT_V1.json`
- `results/v79/development/s174_structure_replay_v4_masked/V79_G500_STRUCTURAL_SUPPORT_V1.npz`
- `results/v79/development/s174_structure_replay_v4_masked/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED.json`
- `results/v79/development/s174_structure_replay_v4_masked/V79_S174_REPLAY_MASKING_AUDIT_V1.json`
- `results/v79/development/s174_structure_replay_v4_masked/V79_S174_REPLAY_PER_GENE_NESTED_DELTAS_V4_MASKED.json`
- `scripts/v79/build_v79_structural_support.py`
- `scripts/v79/compare_v79_s174_replay_masking.py`
- `tests/v79/test_v79_s174_structural_support.py`

## Qualification contract history

### V1 draft — PR #286
SHA `70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540`.
Historical pre-controller draft only; never launch authority.

### V2 draft — PR #288/#290 lineage
SHA `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3`.
Accepted historical payload. Must remain byte-immutable.

Frozen prospective scientific rules:
- 12 worlds Q00-Q11;
- 44 genes/world;
- 1,056 planned fits;
- 260 hard statistical gates;
- 28 hard rule gates;
- 4 LIMIT statistical gates;
- familywise false-fail target 0.05;
- alpha = 0.05/260 = 1.923076923076923e-4;
- LIMIT only for Q01 detection donor-SD bias, Q01 positive donor-SD bias, Q08 positive donor-SD bias, Q09 positive donor-SD bias; their coverage remains hard;
- every Q11 gate is hard FAIL;
- first scientific FAIL irreversibly locks `V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED`;
- later worlds may continue only as `POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION`;
- infrastructure/hash/custody/poison failures stop immediately;
- Q11 omitted-operator perturbation = 0.5× donor SD and is explicitly a mild stress only.

## PR #290 finalization and current blocker

PR #290 head at this handoff: `5394d036ccd423f9c61267fbdfeef6edd4912d37`.

Macha generated a final candidate contract:
`results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json`
reported SHA `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`.

Other #290 files:
- `.github/workflows/v79-v2-core-contract.yml`
- `docs/agent/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_FINAL.md`
- `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.sha256`
- `results/v79/v2_core_qualification/finalization/BUILDER_CHECK_local.txt`
- `results/v79/v2_core_qualification/finalization/FINALIZATION_RECEIPT.json`
- `results/v79/v2_core_qualification/finalization/LAUNCH_AUTHORITY_VALIDATION_RECEIPT.json`
- `results/v79/v2_core_qualification/finalization/LINUX_DIAGNOSTIC_python311_docker.txt`
- `scripts/v79/build_v79_v2_core_contract.py`
- `scripts/v79/v79_v2_core_launch.py`
- `tests/v79/test_v79_v2_core_launch_authority.py`

Engineering evidence:
- RED commit `41b256d0`, CI failed as expected;
- initial Linux GREEN: 29 passed / 1 failed because one reported power float differed in the last binary digit;
- Windows environment fixes followed;
- Windows run `38183422953` / job `114600601441`: 30 passed;
- final head run `38183718225` / job `114601480065`: 30 passed.

Blocking controller audit, PR #290 comment `6115051726`:
- scientific payload accepted;
- Windows-only byte reproducibility is insufficient because the frozen authority was not prospectively OS-bound;
- do not round or alter the accepted V2 draft;
- finalization must hash-check and load the immutable accepted V2 draft bytes/content, then apply only controller-approved finalization-field changes;
- launch-authority generation must not recompute SciPy-derived draft values;
- Linux + Windows CI must produce identical final bytes/SHA;
- existing semantic/tamper/legacy-authority tests must remain;
- until repaired, #290 is NOT canonical launch authority.

PR #289 was closed as a non-canonical duplicate to eliminate authority collision.

## Immediate Macha task

Work only on PR #290.

1. Preserve V2 draft SHA `cbfa332b...` unchanged.
2. Make the finalizer treat that draft as immutable required input.
3. Verify its hash before use.
4. Create final V2 only by a deterministic bounded transformation adding/changing the already-approved finalization fields.
5. Do not call SciPy/statistical derivation to reconstruct accepted draft numbers in finalization.
6. Add Linux and Windows CI proving the same final SHA and byte content.
7. Retain all 30 semantic/tamper/legacy-authority tests.
8. Do not generate worlds in this repair.
9. Stop for controller audit with final SHA and both CI runs.

If any non-finalization scientific field changes, fail closed and report rather than rewriting authority.

## World qualification remains OFF

No Q00-Q11 realized world, truth table, world manifest, benchmark, or NUTS qualification fit exists yet.

Even after finalization becomes canonical, the next gate should be **world generation only**, with truth/manifests/hash custody committed before any fit. Do not combine world generation with qualification fitting.

## Downstream factorial lane

Factorial engineering is closed but scientific execution remains off.

PR #262 implementation head `9110c3fae6d34e43463d56631f43004bda33beb8`.
CI `38147114407` / `114492689105`: 94 passed in 1.04 s.
Audit #264; handoff #265.

No H0/H1/H2/H3/C_OBS/C_BIO scientific execution until a later qualified and audited Bayesian authority exists, is frozen prospectively, and passes fresh byte-authenticated preexecution replay.

## Foundation representation context

Separate synthetic-side representation work found strong source/acquisition imprint and weak broad-class transfer. Technology invariance is not qualified. FULL104 remains physical-data pending. This context motivates explicit observation-process handling but is not authority for changing V2_CORE during qualification.

## Hard firewalls

Still forbidden:
- TEST/Morabito;
- pathology;
- target discovery in this lane;
- SCENIC+/ATAC target evidence in planted truth;
- old 18-fit campaign restart;
- Bernoulli V2/V3 resurrection;
- corrected-TRAIN Bayesian posterior authority fit before synthetic qualification + audit;
- posterior export to H1/H2;
- H0-H3/C_OBS/C_BIO scientific execution;
- Stage4/500K;
- JEPA training/checkpoints.

`training_authorized=false`

## New-agent operating rule

At every Macha checkpoint:
1. fetch the live PR head and comments;
2. audit code/config against the prospective controller contract;
3. inspect failures and retries, not just terminal successes;
4. keep development evidence separate from qualification evidence;
5. update PR #260 and #261 together;
6. update downstream factorial handoff/audit if Bayesian authority status changes;
7. never promote engineering GREEN to scientific qualification or launch authority without the explicit controller gate.

The immediate objective is narrow: **repair #290 into a cross-platform deterministic finalization of the immutable accepted V2 draft, then stop for audit.**