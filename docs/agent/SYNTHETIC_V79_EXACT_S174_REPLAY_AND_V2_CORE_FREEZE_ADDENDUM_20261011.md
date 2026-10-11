# Synthetic/V79 exact-S174 replay and V2-core freeze addendum — 2026-10-11

This addendum supersedes the earlier `operator repair pending` state for the synthetic/V79 Bayesian dataset-geometry lane.

Target discovery remains a separate lane.

## Execution authority

Operator repair implementation: PR #283, head `02fb78c36473d9863ae9482619133c052ba4a480`.

CI:
- workflow `38170751947`
- job `114562666364`
- `22 passed`

Completed exact-S174 replay: PR #285, head `2c230a70d9151e27b14ec2788d1309eb2ac81468`.

Input was the same authenticated G500 cache, not rebuilt:
`2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`.

Primary lambda=1 converged for every fit. One lambda=0.25 detection sensitivity fit failed and was recorded without rescue.

## Ratification of the materiality convention

The PR #283 operator rule is ratified **for this development replay only** because it was fixed in code before any replay metric existed and the sensitivity set was non-adaptive.

At a lambda, operator increment was called materially present only if:
- there was no failed fit at that lambda;
- median per-gene increment was positive;
- the 95% gene-bootstrap interval for the median excluded zero.

This is not a universal significance rule. Genes share cells and donors, so the gene bootstrap is optimistic and is used only as a predeclared development robustness convention.

## Exact S174 A-H rulings

A. Quadratic depth: SUPPORTED in both hurdle parts.

B. Broad class: SUPPORTED in both hurdle parts; strongest consistent increment after depth.

C. Source:
- detection: SUPPORTED;
- positive magnitude: WEAK BUT REPRODUCIBLE and retained in the core, with later shrinkage/regularization appropriate to the Bayesian implementation.

D. Operator-within-source:
- detection: `PRIOR_SENSITIVE__UNRESOLVED`;
- positive magnitude: `NOT_SUPPORTED`.

E. Donor: SUPPORTED in both parts; 32/50 detection and 19/50 positive genes exceed the per-gene permutation threshold versus ~2.5 expected by chance.

F. Operator beyond donor: residual organization exists (37/50 detection, 23/50 positive), but it does not carry over as a stable operator fixed effect to unseen donors.

G. Donor×class: OUT by default. Positive is at chance; detection signal is marginal and insufficient to restore the layer.

H. Lognormal: stable development representation. ZTNB remains an unadjudicated challenger.

## Controller model-freeze ruling

Freeze `CANDIDATE_V2_CORE` as the non-operator two-part architecture.

Detection per gene:
`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive magnitude per gene:
`log(count) | count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Other structural decisions:
- donor×class OUT;
- source×class OUT;
- arbitrary matrix/dataset identity OUT;
- operator main effect OUT of the core;
- modular per-gene fits;
- across-gene geometry estimated second-stage;
- lognormal remains the positive development default;
- ZTNB remains a challenger, not rejected.

`CANDIDATE_V2_CORE` is **frozen for new synthetic qualification**, not yet qualified.

## Operator extension ruling

Operator is returned to model development as a separate optional observation-layer extension.

Reason: donor-controlled operator residual structure is detectable, but the fixed-proxy effect is prior-sensitive for detection and makes positive held-out-donor prediction worse at every frozen penalty.

A future operator extension must be prospectively specified and use hierarchical shrinkage/partial pooling. It must demonstrate out-of-donor predictive value or another prospectively frozen criterion before it can enter the qualified core or downstream synthetic authority.

The operator extension must not block qualification of V2_CORE.

## Next gate

Do not start corrected-TRAIN Bayesian posterior inference.

Next work is:
1. freeze the exact V2_CORE Bayesian implementation/configuration and parameterization before outcomes;
2. design a new recovery/identifiability contract for V2_CORE;
3. generate **new untouched synthetic qualification worlds** not used during development;
4. run confirmatory recovery/identifiability qualification on V2_CORE;
5. stop for controller audit before any real posterior authority fit.

The old 18-fit Gaussian/lognormal/ZTNB campaign is not authority for V2_CORE and must not be restarted as its qualification.

Downstream V79 factorial engineering remains complete but scientific execution remains OFF until a future Bayesian authority is terminally qualified, frozen, and receives a fresh byte-authenticated preexecution replay plus independent audit.

## Terminal

`CANDIDATE_V2_CORE_FROZEN_FOR_NEW_SYNTHETIC_QUALIFICATION__OPERATOR_EXTENSION_RETURNED_TO_DEVELOPMENT__EXACT_S174_REPLAY_COMPLETE__BAYESIAN_REAL_TRAIN_INFERENCE_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`
