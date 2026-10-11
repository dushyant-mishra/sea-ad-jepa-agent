# Synthetic/V79 Bayesian Geometry Lane — Complete Takeover Handoff V4

Date: 2026-10-11

Lane: `SYNTHETIC_DATASET_V79_BAYESIAN_GEOMETRY`

Target discovery is a separate parallel lane. Do not mix target-discovery ranks, SCENIC+, ATAC, pathology, TEST/Morabito, or target-specific evidence into this lane.

## 0. Current controlling terminal

`CANONICAL_CONTRACT_V2_AUTHORITY_REPAIR_PENDING__PR291_FROZEN_WITH_24_TESTS_GREEN__NO_REALIZED_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__REAL_TRAIN_POSTERIOR_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

The scientific V2_CORE term set is frozen after the mask-corrected S174 replay. The current blocker is not the model architecture. The blocker is **single-authority, cross-platform byte reproducibility for Contract V2**.

Controller rulings to read first:
- PR #288 comment `6114753697`: masked S174 replay accepted; V2_CORE frozen unchanged; source magnitude reinterpreted.
- PR #290 comment `6115051726`: Macha's finalization scientifically acceptable but NOT ratified because final bytes differ across Windows/Linux; one canonical authority required.
- PR #291 comment `6115054911`: world-generator engineering frozen until canonical Contract V2 authority is repaired and rebound.

## 1. Immediate next action

Only the PR #290 reproducibility repair is currently active.

Required repair:
1. treat accepted draft `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json` SHA `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3` as an immutable required input;
2. hash-check it exactly;
3. construct final Contract V2 only by applying controller-approved finalization fields to that accepted object;
4. do not recompute SciPy-derived draft reporting values during finalization;
5. preserve `scripts/v79/v79_v2_core_launch.py::require_launch_authority()` as the single downstream launch gate;
6. prove the same final contract SHA/bytes on Linux and Windows;
7. preserve the semantic/tamper/legacy-authority test suite;
8. STOP for controller ratification.

Until that repair is ratified:
- PR #289 SHA `8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d` is historical/provisional only and must not be treated as current canonical launch authority;
- PR #290 SHA `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26` is also not canonical yet;
- PR #291 remains frozen;
- no world realization, benchmark, qualification fitting, corrected-TRAIN Bayesian posterior inference, factorial science, or training is allowed.

## 2. Scientific architecture

Core conceptual separation:

`latent biology -> observation process -> observed counts`

Factorial destination architecture, once authority is qualified:
- H0: baseline E2 biology + baseline observer.
- H1: hierarchical anonymous biology + baseline observer.
- H2: baseline E2 biology + explicit observer.
- H3: hierarchical anonymous biology + explicit observer.
- C_OBS: same latent biology under different observation regimes.
- C_BIO: different latent biology under the same observation regime.

This lane learns defensible anonymous biological/observation geometry. It does not transfer exact real gene/class/donor identities into synthetic planted truth.

## 3. Firewall for synthetic truth

Allowed, if prospectively qualified and identity-randomized:
- broad class effect distributions;
- donor effect distributions;
- anonymous continuous programs / latent state scales;
- anonymous gene-effect distributions;
- residual variance and covariance/eigenspectrum summaries;
- source/operator/capture/detection/depth/dispersion observation geometry;
- posterior uncertainty in those distributions.

Forbidden in planted truth:
- named real pathways/programs;
- exact real class-gene signatures;
- exact donor-gene signatures;
- target-discovery ranks/panels;
- SCENIC+/ATAC target evidence;
- pathology;
- TEST/Morabito;
- V78 outcome-driven retuning;
- post-outcome rescue of synthetic arms.

Donor, source, operator, matrix and broad class are distinct concepts. Depth is not automatically a technical nuisance variable.

## 4. Historical real-data geometry that motivated the lane

Corrected real observation from earlier TRAIN analyses:
- pooled positive:negative strong-edge ratio approximately 59:1;
- after broad-class conditioning approximately 1.2–1.3;
- after broad-class + depth approximately 1.0–1.1.

Interpretation: most pooled positive topology is explained by broad biological class. Residual negative topology is strongly source-associated, but real data do not identify source-linked biology versus acquisition/measurement causally. This motivated anonymous hierarchical biology plus an explicit observation operator and a factorial synthetic design.

## 5. Model-development evidence before exact S174

A mounted 50K auxiliary reader-fit dataset was used only for development:
- 50,000 cells x 41,238 addresses, log1p10k sparse matrix;
- 104 donors;
- source counts: SEA_AD 33,821; HVS 10,958; NPH52 5,221.

Deterministic first-100-per-donor balance:
- 10,379 cells;
- SEA_AD 4,600; HVS 4,100; NPH52 1,679;
- 104 donors, 42 operators;
- no donor spans multiple sources;
- 103/104 donors span >=2 operators, 100/104 span >=3, median 11 operators.

Source is therefore nested/confounded with donor. Never describe source as proven measurement-only causality.

Count replay relation was exact to floating tolerance:
`count = round(expm1(log1p10k) * source_library / 10000)`.

### Family tournament
Historical development scores:
- NB2 fixed depth LPD: -1.43373;
- NB2 free depth: -1.40428;
- hurdle lognormal: -1.30285;
- hurdle ZTNB: -1.30617.

Detection logloss:
- NB fixed: 0.37573;
- NB free: 0.35608;
- explicit logistic detection: 0.26179.

Conclusion: a two-part detection + positive architecture is strongly supported as a development direction. The old Bernoulli V2 qualification failure was a parameterization/fit failure, not evidence that detection should be removed. Lognormal and ZTNB were close; ZTNB remained an unadjudicated challenger.

### Nested structure tournament
Detection donor-held-out mean logloss:
- D0 depth linear 0.4663681
- D1 depth quadratic 0.4637061
- D2 + class 0.4167601
- D3 + source 0.3308157
- D4 class + operator 0.3233763
- D5 class + source + operator 0.3220367
- D6 source×class + operator 0.3222188

Positive lognormal donor-held-out LPD:
- P0 depth -2.2330114
- P1 + class -2.1870610
- P2 + source -2.0809010
- P3 + operator -2.0391289

Development interpretation: class was essential, source was large in detection, operator smaller, source×class not earned. Later exact S174 weakened the operator conclusion substantially.

Earlier operator residual permutation evidence from the auxiliary sample was later recognized as not fully controlling donor composition. Treat that historical operator support as provisional only. Exact S174 used donor-centered within-donor nulls.

Donor×class was not broadly supported after residualizing donor and was removed from the default candidate.

## 6. Failed historical Bayesian campaign

Source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`.

Detection V2 terminally failed qualification at S4:
- worst ESS `361.8761303230284` < 400;
- R-hat `1.0050606796610788`;
- divergences 0.

Terminal: `NOT_QUALIFIED`.

Do not relax thresholds or resurrect that exact parameterization.

Old Gaussian/lognormal/ZTNB monolithic hierarchy remains `UNADJUDICATED__METHODOLOGICAL_HOLD`, not scientifically failed. The old 18-fit campaign must not restart automatically.

Measured historical heavy fit resource use: about 10.28/16 logical CPUs, ~93.1% whole-machine CPU, ~1.32 GB peak RSS, ~1561.5 s wall. CPU saturation, not S174 storage, is the main heavy-fit bottleneck. Heavy-job default is one machine-wide fit plus 120 s settle.

## 7. Exact corrected-S174 custody

Physical repaired TRAIN substrate (canonical data machine):
`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Population:
- 4,726 cells;
- 149 donors: HVS 62, NPH52 19, SEA_AD 68;
- cell source counts: HVS 3,072, NPH52 246, SEA_AD 1,408;
- 42 operators;
- 3 sources;
- 3 broad classes;
- 426 donor-class groups.

Custody:
- 84/84 required count+metadata shards verified;
- 0 missing;
- 0 extra.

Authority SHA-256:
`04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`

S174 operator bridge SHA-256:
`b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`

Do not reconstruct S174 from the larger 50K corpus. Exact cell identity/order is part of custody.

## 8. PR #279 — true streaming S174 infrastructure

PR #279 branch `fix/v79-streaming-analysis-cache-20261011`.

Verified production code head:
`2d5de281a171f0510d22a7408780fb069625ea02`

Documentation/execution snapshot head:
`615b55eb03b95630484b18d47de0ef7340368d37`

CI:
- run `38166126568`
- job `114548954034`
- 15 passed in 1.27 s.

Important files:
- `.github/workflows/v79-streaming-analysis-cache.yml`
- `scripts/v79/build_v79_analysis_cache.py`
- `scripts/v79/run_v79_s174_structure_replay.py`
- `scripts/v79/run_v79_scheduler.py`
- `tests/v79/test_v79_analysis_cache.py`
- `tests/v79/test_v79_s174_structure_replay.py`
- `tests/v79/test_v79_scheduler_resource_defaults.py`

Engineering properties:
- two streaming count-shard passes;
- max one count shard resident;
- no global 4,726 x 41,238 CSR assembly;
- metadata parsed from authenticated bytes;
- compact cache hash-bound to receipt;
- repeated replay is cache-only NumPy/SciPy, no JAX/NUTS.

## 9. G500 compact cache

Physical G500 cache is real-count data and remains local by design.

`V79_ANALYSIS_CACHE_G500.npz`
- size 1,071,307 bytes;
- SHA-256 `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`.

Panel:
- 500 identity-blind genes;
- prevalence universe >=5%;
- panel prevalence approximately 0.050 to 0.949, median ~0.242.

Do not commit or rebuild this cache unless custody/hash validation fails.

## 10. PR #280 — first exact S174 replay failed closed

PR #280 branch `exec/v79-s174-structure-replay-20261011`.

G500 construction passed. Replay failed before any predictive metric because the first non-converged operator logistic fit stopped the run.

Diagnosis:
- depth linear: 0/600 failures;
- quadratic: 0/600;
- +class: 0/600;
- +source: 0/600;
- +operator: 155/600 failures;
- 84/200 genes had >=1 operator failure;
- 351/600 operator fits contained an all-detected or no-detected training operator level.

Cause: quasi-separation with only a tiny common ridge `1e-4`.

This was not evidence for or against an operator effect.

Prospective controller repair ruling: PR #280 comment `6112948943`.

## 11. PR #283 — operator-only regularization repair

PR #283 head:
`02fb78c36473d9863ae9482619133c052ba4a480`

CI:
- run `38170751947`
- job `114562666364`
- 22 passed.

Frozen repair:
- primary operator-within-source ridge lambda = 1;
- sensitivities `{0.25, 1, 4}`;
- only operator columns receive the new penalty;
- same convention in both hurdle parts;
- maxiter/convergence/folds/panel/seed/metrics unchanged;
- every primary lambda=1 fit must converge or fail closed;
- sensitivity failures are reported, never rescued.

## 12. PR #285 — exact S174 replay V3 completed

PR #285 head:
`2c230a70d9151e27b14ec2788d1309eb2ac81468`

Same authenticated G500 cache reused.

Recipe:
- 200 replay genes;
- 50 support genes;
- 3 donor-heldout folds;
- 99 permutations;
- seed 20261011;
- lambda grid `{0.25,1,4}`.

All primary lambda=1 fits converged. One lambda=0.25 detection sensitivity fit failed and was recorded without rescue.

A-H V3 conclusions:
- A quadratic depth: SUPPORTED both parts;
- B broad class: SUPPORTED, strongest consistent increment;
- C source: SUPPORTED detection, weak/reproducible positive magnitude;
- D operator: detection `PRIOR_SENSITIVE__UNRESOLVED`; positive `NOT_SUPPORTED`;
- E donor: SUPPORTED, 32/50 detection and 19/50 positive support genes versus ~2.5 expected by chance;
- F operator beyond donor: 37/50 detection, 23/50 positive residual organization, but not a stable fixed effect on unseen donors;
- G donor×class: OUT;
- H lognormal: stable development default; ZTNB unadjudicated.

Controller freeze: V2_CORE without operator.

## 13. Structural-support flaw and mask-corrected replay

A later audit found that V3 had treated structurally unmeasured matrix×gene entries as measured zeros.

Magnitude:
- 5.76% of whole G500 cell-gene entries structurally unmeasured;
- 59/500 genes affected;
- replay panel: 63,002/945,200 entries removed = 6.67%;
- 28/200 replay genes and 5/50 support genes affected.

Hard invariant:
`MEASURED_SCALAR != STRUCTURALLY_UNMEASURED`

Stage81A2R matrix-level support authority at commit `95d2cafe`, SHA prefix `ee5d12c1...`; joined through the S174 operator bridge.

Support mask SHA-256:
`12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`

Canonical correction package: PR #288, branch `fix/v79-s174-structural-support-mask-20261011`, head `c3cf9ad7472541bfb5ad632465c626c437f9a69c`.

Important files on PR #288:
- `scripts/v79/build_v79_structural_support.py`
- `scripts/v79/compare_v79_s174_replay_masking.py`
- `scripts/v79/run_v79_s174_structure_replay.py` corrected path in this branch
- `tests/v79/test_v79_s174_structural_support.py`
- `results/v79/development/s174_structure_replay_v4_masked/V79_G500_STRUCTURAL_SUPPORT_V1.json`
- `results/v79/development/s174_structure_replay_v4_masked/V79_G500_STRUCTURAL_SUPPORT_V1.npz`
- `results/v79/development/s174_structure_replay_v4_masked/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED.json`
- `results/v79/development/s174_structure_replay_v4_masked/V79_S174_REPLAY_MASKING_AUDIT_V1.json`
- `docs/agent/V79_S174_STRUCTURE_REPLAY_V4_MASKED_RESULT_20261011.md`

Masked replay SHA-256:
`caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`

Masking audit SHA-256:
`6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41`

Poison/sentinel tests prove unmeasured entries are not read. Fully measured mode reproduces V3.

Masked replay preserves every A-H structural class. Main numerical correction:
- detection source median gain approximately +0.00148 -> +0.00091;
- mean approximately +0.0226 -> +0.0090;
- improved genes 78% -> 73.5%;
- interval remains above zero.

Six detection-source genes and nine positive-source genes have an undefined cross-source estimand because measured support exists in only one source. They are reported as unevaluable, not treated as zeros.

Controller ruling PR #288 comment `6114753697`:
- V2_CORE stays frozen unchanged;
- source stays in the model but is interpreted narrowly as predictive/acquisition-source structure among estimable measured comparisons;
- no universal causal source-biological claim;
- exact V3 panel reuse for corrective comparison approved;
- V1 preserved and a new V2 contract file preferred.

## 14. Frozen V2_CORE

Status scientifically: `FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY`.

Detection:
`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive:
`log(count) | count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Frozen decisions:
- quadratic depth IN;
- broad class IN;
- source IN, with narrowed predictive/acquisition interpretation;
- donor-within-source IN;
- operator main effect OUT;
- donor×class OUT;
- source×class OUT;
- free matrix/dataset identity OUT;
- genes modular per gene;
- across-gene geometry second-stage;
- lognormal current qualification family;
- ZTNB separate unadjudicated challenger.

Operator residual organization remains scientifically interesting but is a separate development extension, not V2_CORE authority.

## 15. Qualification Contract evolution

### V1 historical draft — PR #286
Path:
`results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json`

SHA-256:
`70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540`

Historical pre-controller draft only. Not launch authority.

### V2 accepted draft payload — PR #288
Path:
`results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json`

SHA-256:
`cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3`

This accepted payload contains the prospective scientific contract and is now the immutable input that final launch-authority finalization must consume without recomputing its accepted derived statistics.

Accepted contract rules include:
- 12 worlds Q00-Q11;
- 44 genes/world;
- 1,056 planned fits;
- 260 hard statistical gates;
- 28 hard rule gates;
- 4 LIMIT statistical gates;
- familywise false-fail target 0.05;
- alpha = 0.05/260;
- LIMIT only on Q01 detection donor-SD bias, Q01 positive donor-SD bias, Q08 positive donor-SD bias, Q09 positive donor-SD bias;
- coverage stays hard for those cases;
- every Q11 gate hard;
- first scientific FAIL irreversibly locks NOT_QUALIFIED;
- later frozen worlds may continue only as `POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION`;
- infrastructure/hash/custody/poison failures stop immediately;
- Q11 omitted-operator size 0.5 x donor SD is a mild stress only.

### PR #289 controller-side finalization
PR #289 produced an authority envelope SHA:
`8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d`

It was initially controller-ratified and used as the provisional basis for PR #291 engineering. A competing Macha finalization then exposed the need for one sole canonical authority. Controller comment on PR #290 now explicitly says #289 cannot coexist as a second canonical launch authority. Treat #289 as historical/provisional engineering evidence, not current launch authority.

### PR #290 Macha finalization — current repair target
PR #290 head:
`5394d036ccd423f9c61267fbdfeef6edd4912d37`

Proposed final SHA:
`57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`

Scientific payload passes audit. Launch gate:
`scripts/v79/v79_v2_core_launch.py`

Windows CI final head:
- run `38183718225`
- job `114601480065`
- 30 passed.

Blocking defect:
- Windows reported power: `0.8003456396475284`;
- Linux same pinned libraries: `0.8003456396475286`;
- final exact bytes therefore differ because finalization recomputes a SciPy-derived report value.

Controller repair ruling: PR #290 comment `6115051726`.

Correct repair is not rounding the accepted draft. The finalizer must load/hash-check the immutable accepted V2 draft and apply finalization-only fields without recomputing accepted statistical reporting values. Linux and Windows must then yield identical final SHA.

Current authority state: **no canonical launch SHA until this repair is GREEN and controller-ratified**.

## 16. Q10/Q11 prospective pairing amendment

During PR #291 engineering, a prospective semantic defect was found before any world bytes existed: Q10 and Q11 were intended as a contrast but world-index-based streams would have redrawn core truth/noise.

Controller correction PR #291 comment `6114906562` fixed the intended design as a paired counterfactual:
- Q11 inherits Q10 exact design;
- structural-support mask identical;
- planted core parameters identical;
- donor effects/factors identical;
- factor-loading assignment identical;
- base detection/positive observation-noise streams identical;
- Q11 differs only by omitted-operator offsets in streams 22/23, centered within source;
- all Q11 gates remain HARD FAIL.

First amendment SHA under provisional #289 authority:
`09f60d91817a041badaa4fc5108125f02a02d1ebbe8242a0f012aa6978d56f7c`

That amendment's **scientific semantics remain accepted**, but its authority binding must be regenerated prospectively against the future sole canonical Contract V2 SHA after PR #290 repair. Do not reuse the old authority binding silently.

## 17. PR #291 world-generator engineering — preserved but frozen

PR #291 branch:
`feat/v79-v2-core-world-generator-20261011`

Current head at takeover:
`714a36f3ca4f8c01e65f1fb2d5d80741a5b0af27`

Latest preserved observation-generator CI:
- run `38183909388`
- job `114602059598`
- 24 passed in 0.33 s on Ubuntu/Python 3.11.17.

No realized world bytes, truth tables, benchmark outputs, or qualification fits were emitted.

Controller hold PR #291 comment `6115054911`:
- stop further generator changes;
- current binding to `8be47cb2...` is provisional;
- after PR #290 is repaired and ratified, rebase/rebind #291 to the sole canonical final contract;
- use #290 `require_launch_authority()` as sole gate;
- regenerate the Q10/Q11 pairing amendment with same semantics but new contract SHA;
- rerun all generator tests on Linux + Windows;
- only after a separate controller decision may physical world realization occur.

## 18. World definitions in accepted payload

Q00 baseline: ordinary nonzero depth/class/source/donor effects.
Q01 weak donor.
Q02 strong donor.
Q03 weak source.
Q04 source absent.
Q05 class absent.
Q06 quadratic depth absent.
Q07 donor absent.
Q08 sparse detection.
Q09 positive-tail stress.
Q10 exact S174 design imbalance.
Q11 paired Q10 counterfactual plus mild omitted-operator perturbation.

Every world includes structural measurement absence as part of truth. Structurally unmeasured values are outside the likelihood; poison values are implementation sentinels, not scientific truth.

## 19. Factorial downstream state

Factorial implementation PR #262 remains internally engineered/verified:
- implementation head `9110c3fae6d34e43463d56631f43004bda33beb8`;
- workflow `38147114407`;
- job `114492689105`;
- 94 passed in 1.04 s.

No H0/H1/H2/H3/C_OBS/C_BIO scientific execution has occurred.

Current Bayesian work does not yet authorize any H1/H2/H3 parameter authority. Even after V2_CORE qualification passes, corrected-TRAIN posterior authority would need separate authorization/audit before factorial authority can be frozen.

A future material authority change still requires prospectively frozen authority bytes, fresh byte-authenticated factorial preexecution replay, and independent final audit before scientific execution.

## 20. Evidence hierarchy

Use this hierarchy when adjudicating disagreements:
1. explicit controller rulings posted before relevant outcomes;
2. immutable accepted/ratified contract payloads and hashes;
3. authenticated physical custody receipts/hashes;
4. exact execution records;
5. independent audit records;
6. development tournaments/diagnostics;
7. prose summaries.

Never promote a development metric into qualification authority by wording alone.

## 21. Hard firewalls

Currently OFF / forbidden:
- realized Q00-Q11 worlds;
- world truth-table emission;
- benchmark;
- qualification NUTS fits;
- corrected-TRAIN Bayesian posterior authority fit;
- posterior export to factorial H1/H2;
- H0/H1/H2/H3/C_OBS/C_BIO scientific execution;
- old 18-fit campaign restart;
- Bernoulli V2/V3 rescue;
- TEST/Morabito;
- pathology;
- target discovery in this lane;
- SCENIC+/ATAC target evidence in planted truth;
- Stage4/500K;
- JEPA training/checkpoints.

`training_authorized=false`

## 22. New-agent startup checklist

A new controller agent should do this in order:
1. read PR #260 and PR #261 current bodies;
2. read this handoff and the matching V4 artifact index;
3. read PR #290 comment `6115051726` and PR #291 comment `6115054911`;
4. inspect live heads of #290 and #291 because Macha may have pushed a repair;
5. do not trust PR #289 or #290 final SHA as canonical until one sole authority is controller-ratified after cross-platform reproduction;
6. if PR #290 repair exists, audit that it loads/hash-checks `cbfa332b...` and never recomputes accepted draft derived statistics during finalization;
7. require identical final bytes/SHA on Linux + Windows and retained semantic/tamper tests;
8. after ratification, update PR #260/#261 together;
9. then rebind PR #291 to that final SHA, regenerate the Q10/Q11 amendment against it, rerun Linux+Windows generator tests, and STOP for controller authorization before world realization;
10. if world realization is later authorized, commit hash-bound truth/manifests before any benchmark or fit;
11. qualification fitting remains a separate explicit gate.

## 23. Standing synchronization rule

At every meaningful terminal checkpoint, update together:
- PR #260 independent audit;
- PR #261 canonical handoff;
- current machine-readable state/index;
- PR #264/#265 downstream factorial state if Bayesian authority status changes.

Preserve immutable failed attempts and historical authorities rather than rewriting them.
