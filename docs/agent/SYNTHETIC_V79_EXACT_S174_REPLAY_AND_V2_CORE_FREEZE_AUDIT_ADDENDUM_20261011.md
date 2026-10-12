# Synthetic/V79 exact-S174 replay and V2-core freeze audit addendum — 2026-10-11

Audit scope: synthetic/V79 Bayesian dataset-geometry lane only. Target discovery is separate.

## Verified execution

PR #283 implemented the prospectively frozen operator-penalty repair from PR #280.

Code head: `02fb78c36473d9863ae9482619133c052ba4a480`.

Independent CI:
- run `38170751947`
- job `114562666364`
- SUCCESS
- `22 passed`

The repair is faithful to the pre-outcome contract:
- operator-within-source columns only receive the stronger penalty;
- primary lambda=1;
- frozen sensitivity set `{0.25,1,4}`;
- non-operator nested paths remain unchanged;
- sensitivity values are not CLI-selectable/adaptive;
- primary fits fail closed;
- sensitivity failures are recorded, not rescued.

PR #285 then reran the exact same S174 replay on the same authenticated G500 cache SHA `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`.

Primary lambda=1: all fits converged.
Sensitivity lambda=0.25: one detection fit failed and was retained as a failure.
No cache rebuild occurred.

## Ratified development convention

The code-fixed `materially present` operator convention is ratified for this development replay only. It was established before any repaired replay metric and is non-adaptive.

It is not a general inferential threshold because the gene bootstrap is optimistic under shared donors/cells.

## Audited A-H outcome

- A quadratic depth: SUPPORTED in both parts.
- B broad class: SUPPORTED in both parts.
- C source: SUPPORTED for detection; weak but reproducible for positive magnitude.
- D operator: detection `PRIOR_SENSITIVE__UNRESOLVED`; positive `NOT_SUPPORTED`.
- E donor: SUPPORTED, 32/50 detection and 19/50 positive genes.
- F operator beyond donor: residual organization above chance, 37/50 detection and 23/50 positive, but not a stable transferable fixed operator effect.
- G donor×class: OUT by default.
- H lognormal: stable development default; ZTNB unadjudicated.

## Audit interpretation

The apparent tension between D and F is scientifically meaningful, not contradictory:
- operator-associated residual structure is present within S174;
- a direct operator main effect does not generalize reliably to held-out donors;
- stronger shrinkage can make detection operator terms look beneficial, proving prior sensitivity;
- in positive magnitude the operator proxy is harmful at all frozen penalties.

Therefore residual operator organization cannot be promoted automatically into a frozen operator main effect.

## Controller freeze decision

Audit accepts the controller decision to freeze `CANDIDATE_V2_CORE` without operator:

Detection:
`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive magnitude:
`log(count)|count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

- donor×class OUT;
- source×class OUT;
- operator main effect OUT of core;
- genes modular;
- across-gene geometry second-stage;
- lognormal positive family development default;
- ZTNB challenger unresolved.

This is a **development freeze for new synthetic qualification**, not a qualification pass.

Operator returns to a separate model-development track and must not block V2_CORE qualification. Any future operator extension requires prospectively frozen hierarchical shrinkage and evidence of out-of-donor value or another predeclared external criterion.

## Downstream consequence

No current Bayesian posterior quantity is qualified for V79 factorial H1/H2/H3 authority.

PR #262 remains engineering-verified only. H0/H1/H2/H3/C_OBS/C_BIO science remains OFF.

After a future V2_CORE terminal qualification, any material H1/H2 authority update still requires fresh byte-authenticated preexecution replay and independent audit.

## Next audit gate

The next legitimate work is to freeze the exact V2_CORE Bayesian implementation/config and create **new untouched synthetic qualification worlds** plus a prospective recovery/identifiability contract.

Do not use the old 18-fit campaign as authority for this new candidate. Do not start corrected-TRAIN NUTS/posterior inference before the new synthetic qualification and controller audit.

## Audit verdict

`PASS_EXACT_S174_DEVELOPMENT_REPLAY__V2_CORE_STRUCTURE_EARNED_WITH_OPERATOR_EXCLUDED__OPERATOR_EXTENSION_UNRESOLVED_AND_RETURNED_TO_DEVELOPMENT__NEW_SYNTHETIC_QUALIFICATION_REQUIRED__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`
