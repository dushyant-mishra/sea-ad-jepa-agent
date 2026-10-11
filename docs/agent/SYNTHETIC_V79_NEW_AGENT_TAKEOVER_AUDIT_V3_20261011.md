# Synthetic/V79 lane — definitive takeover audit V3

Date: 2026-10-11

Audit verdict:

`V2_CORE_SCIENTIFIC_STRUCTURE_PRESERVED_AFTER_MASK_CORRECTION__CONTRACT_FINALIZATION_SCIENTIFIC_PAYLOAD_ACCEPTED__CROSS_PLATFORM_BYTE_REPRODUCIBILITY_BLOCKS_CANONICAL_LAUNCH_AUTHORITY__NO_WORLDS__NO_QUALIFICATION_FITS__TRAINING_OFF`

## Scope
Independent audit of the synthetic/V79 Bayesian dataset-geometry lane. Target discovery is a separate lane and must not be mixed into this evidence.

## Controlling conclusions
- V2_CORE is frozen unchanged after the mask-corrected exact-S174 replay.
- Detection source remains in the model only as predictive/acquisition-source structure among estimable measured comparisons; no universal causal/biological source claim is authorized.
- Operator fixed effect remains out of the core; residual operator organization exists but did not generalize as a stable held-out-donor fixed effect.
- donor×class and source×class remain out.
- lognormal remains the current qualification family; ZTNB is unadjudicated.
- No qualification world, benchmark, or qualification fit has run.
- No corrected-TRAIN Bayesian authority fit, factorial science, or JEPA training is authorized.

## Data custody
Corrected S174 physical root: `D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`.
Authority SHA `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`.
Operator bridge SHA `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`.
G500 cache SHA `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`, local/uncommitted by design.

## Historical evidence chain
1. Detection V2: NOT_QUALIFIED; S4 ESS failure, no threshold relaxation.
2. Old Gaussian/lognormal/ZTNB campaign: methodological hold; do not restart.
3. PR #279: streaming/cache implementation GREEN, 15 passed; bounded data path established.
4. PR #280: G500 PASS; first exact replay failed closed before metrics due operator quasi-separation.
5. PR #283: prospectively frozen operator-only penalty λ primary 1, sensitivity {0.25,1,4}; 22 passed.
6. PR #285: exact replay complete; A-H gave quadratic depth IN, broad class IN, source IN, donor IN, operator OUT/UNRESOLVED, donor×class OUT, lognormal stable.
7. PR #286: prospective qualification contract drafted; structural-support flaw discovered before worlds.
8. PR #288: support mask correction and physical replay completed; all A-H classes preserved. Mask SHA `12ad275e...`, replay SHA `caf2413c...`, masking audit SHA `6bd0bfc7...`.
9. PR #290: final V2 contract candidate generated and semantic launch-gate tests pass on Windows, but final bytes differ by one last-bit reported power value on Linux. Controller comment `6115051726` blocks launch authority until deterministic finalization is derived from immutable accepted V2 draft bytes/content.
10. PR #289: duplicate controller-side finalization branch closed as non-canonical to eliminate authority collision.

## Structural-support audit
Historical V3 incorrectly treated structural absence as zero. Corrected masked replay removes 5.76% of whole-cache entries and 6.67% of replay-panel entries from likelihood/scoring.

Effect on A-H:
- all decision classes preserved;
- source detection magnitude materially reduced: median +0.00148→+0.00091, mean +0.0226→+0.0090, improved fraction 78%→73.5%;
- positive part bit-identical to V3;
- donor/operator-support/donor×class support counts unchanged;
- six detection-source and nine positive-source estimands become undefined because only one source is measured; none are silently dropped.

Audit conclusion: model-structure freeze survives; source interpretation must remain narrowed.

## Frozen V2_CORE
Detection: `detected ~ quadratic(log_library) + broad_class + source + donor_within_source`.
Positive: `log(count)|count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`.

Excluded: operator, donor×class, source×class, free matrix/dataset ID.

## Qualification contract scientific payload
Immutable accepted V2 draft SHA: `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3`.
Historical V1 SHA: `70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540`.

Frozen rules:
- 12 worlds Q00-Q11;
- G=44 genes/world;
- 1,056 planned fits;
- 260 hard statistical gates;
- 28 hard rule gates;
- 4 LIMIT statistical gates;
- alpha=0.05/260;
- LIMIT only the four controller-approved donor-SD bias gates; coverage remains hard;
- every Q11 gate is hard;
- first scientific FAIL irreversibly locks NOT_QUALIFIED;
- post-terminal worlds cannot rescue qualification;
- Q11 operator perturbation is a mild 0.5×donor-SD stress only.

## PR #290 audit
Reported final candidate SHA: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`.
Windows CI final head `5394d036...`: run `38183718225`, job `114601480065`, 30 passed. Earlier Windows run `38183422953` / `114600601441`: 30 passed.
Linux: 29 passed, 1 failed because `worlds.gene_count_derivation.power` was `0.8003456396475286` versus Windows `0.8003456396475284`; G, alpha, t-critical and all gates were unchanged.

Controller finding: frozen environment did not prospectively bind OS, so Windows-only exact-byte regeneration is insufficient for immutable authority.

Required repair:
- hash-check immutable V2 draft `cbfa332b...`;
- load accepted draft content directly;
- construct final V2 by applying only approved finalization-field changes;
- do not recompute accepted SciPy-derived draft reporting values during finalization;
- prove identical final SHA/bytes on Linux and Windows;
- retain semantic/tamper/legacy-authority tests;
- no world generation in the repair.

Until that passes, PR #290 is not canonical launch authority.

## Downstream status
Factorial implementation PR #262 is engineering GREEN: 94 passed in 1.04 s. Scientific H0-H3/C_OBS/C_BIO execution remains OFF. A future qualified Bayesian authority still requires independent audit and fresh preexecution replay before factorial science.

## Immediate audit gate
Macha may repair PR #290 only. Stop after cross-platform GREEN and report final SHA + Linux/Windows CI evidence. Controller audit must explicitly ratify the final contract before world generation.

## Firewalls
No TEST/Morabito, pathology, target discovery in this lane, SCENIC+/ATAC target evidence in truth, old campaign restart, corrected-TRAIN posterior fit, factorial science, Stage4/500K, or JEPA training/checkpoints.

`training_authorized=false`