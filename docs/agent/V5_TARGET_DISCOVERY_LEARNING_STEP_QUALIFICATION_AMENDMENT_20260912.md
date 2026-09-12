# V5 / Target Discovery learning-step qualification amendment — 2026-09-12

Status: `PROSPECTIVE_AMENDMENT__NO_TRAINING_AUTHORITY__NO_PROTECTED_ACCESS`

## Purpose

This amendment incorporates a methodological lesson from the T0 V21 closeout into the V5 / Foundation Target Discovery production pipeline without importing T0 biology, endpoints, or numerical thresholds.

Controlling methodological source:

- branch/commit: `t0/v21-closeout-candidate-20260911 @ a61eff05`
- document: `docs/agent/T0_LEARNING_STEP_FINDINGS_20260912.md`

T0 found that downstream work on transport and confirmation had been built before the upstream learning step was shown to be resolvable. That is a general design failure mode. The V5 / Target Discovery pipeline must therefore establish that a candidate learned representation is doing resolvable work beyond explicit null/technical comparators before learned geometry can receive scientific interpretation.

This amendment is prospective. It does not rewrite TD56/TD57B/TD57C/TD59, does not make T0 a biological target authority, and does not authorize training, pathology access, `reader_validation`, or `reader_oracle`.

Permanent lane separation remains:

`FOUNDATION_TARGET_DISCOVERY_TD13_TD60_IS_NOT_T0_V18_V20_V21`

`T0_METHOD_DEVELOPMENT_INFORMS_FOUNDATION_TARGET_DISCOVERY_AND_V5_CHEAT_PROOFING_WITHOUT_SUPPLYING_THE_BIOLOGICAL_TARGET`

## Corrected ordering

The production order is now:

```text
FULL104 physical-byte closure
    ↓
V5 mechanics / optimizer / RNG / packing / anti-cheat qualification
    ↓
freeze BASE_LEARNING_STEP_QUALIFICATION protocol
    ↓
explicit owner authority for a bounded reader_fit learning-step qualification run
    ↓
BASE_LEARNING_STEP_QUALIFICATION evidence + independent validation
    ↓
scientific promotion of an exposure-defined base EMA teacher becomes eligible
    ↓
TD60 learned-geometry continuity
    ↓
partial-evidence relational predictability / matched-null qualification
    ↓
production relational protocol + dimensions/runtime qualification
    ↓
independent integrated review
    ↓
explicit production-training authority, if separately granted
```

A protocol freeze is not run authority. A bounded qualification-run authority is not production-training authority. A learning-step PASS is not TD60 authority and is not relational-target activation authority.

## Required learning-step questions

### 1. What is the analysis-level sample size?

Every candidate must declare separately:

- the representation observation unit;
- the statistical generalization unit;
- whether any aggregation changes the effective sample size of the claim;
- why that aggregation is required by the estimand.

The pipeline must not collapse millions of cells to one scalar per donor merely because an upstream representation is cell-level. Donor-held-out inference remains required where a biological generalization claim is donor-level, but representation-learning diagnostics should retain cell-level/native-support information whenever the estimand permits it.

### 2. What does “nothing learned” look like?

A qualification result must publish the full objective/CV/qualification curve beside frozen comparators, not only the winning point. At minimum the comparator family must cover:

1. `NO_LEARNED_SIGNAL_OR_LIMITING_OBJECT` — the explicit limiting/asymptotic object the learner approaches when its learned contribution vanishes;
2. `TECHNICAL_ONLY_OR_IDENTITY_ONLY` — a shortcut/identity/technical baseline appropriate to the candidate;
3. `RANDOMIZED_OR_MATCHED_NULL` — an intervention/null that destroys the intended learned relation while preserving the relevant nuisance structure.

Comparator definitions must be frozen before observing their result.

### 3. Boundary selection is a diagnosis trigger

If the chosen hyperparameter lies on a search boundary, the limiting object must be derived and measured before any grid expansion is allowed to become scientific evidence.

A boundary hit may indicate that the learned contribution is being shrunk away, that the model family is approaching a different estimator, or that the grid is too narrow. Those hypotheses must be distinguished. “Expand the grid” is not an automatic repair.

### 4. Effective capacity must be reported

Every regularized or constrained learner must report an interpretable active-capacity diagnostic:

- effective degrees of freedom when mathematically defined; or
- a model-specific active-capacity quantity with a frozen definition otherwise.

The threshold/interpretation must be production-derived or model-defined. T0's observed `edf ≤ 0.28` is methodological evidence from a different model and may not be copied as a V5 threshold.

### 5. Qualification geometry must resemble FULL104

Synthetic/mechanics fixtures remain useful for unit tests, but production scientific qualification cannot be earned from toy geometry. Simulation/adversarial qualification used for the learning-step claim must represent the relevant FULL104 structure, including as applicable:

- 4,553,407 reader-fit cells;
- 104 donors;
- 42 operators/matrices;
- 41,238 canonical addresses;
- native/ragged measurement support;
- source/operator/donor imbalance;
- masking and packing laws;
- the actual proposal/weighting law;
- technical shortcut channels that exist in the real substrate.

This requirement does not mean every simulation must instantiate all 4.55M cells in memory. It means the simulated/adversarial geometry and sufficient statistics must reproduce the production support and dependence structure relevant to the tested claim.

### 6. Learning and biology are distinct conclusions

Failure terminal:

`STOP_BASE_LEARNING_STEP_NOT_ESTABLISHED__DOWNSTREAM_SCIENTIFIC_INTERPRETATION_BLOCKED`

means only that the candidate learning design has not established a resolvable learned contribution under the frozen qualification. It must not be reworded as “biology absent,” “dataset has no biology,” or an equivalent global conclusion.

A pass terminal:

`PASS_BASE_LEARNING_STEP_QUALIFICATION__NO_TRAINING_AUTHORITY`

means only that the learning step has passed the frozen methodological gate. It does not authorize production training, TD60, relational target activation, protected data, pathology, or outcome-guided tuning.

## Run-authority firewall

Evidence from a learned candidate is admissible only if the evidence-producing run was separately and explicitly authorized with scope exactly:

`BOUNDED_READER_FIT_LEARNING_STEP_QUALIFICATION_ONLY`

The authority object must be content-addressed. It must explicitly state that production training remains unauthorized.

Until such an authority exists, this amendment and its validator can be frozen/tested, but no new learned FULL104 evidence may be generated under their name.

## Machine-enforced receipt surface

Validator:

`scripts/v5_anticheat/validate_base_learning_step_qualification_v1.py`

The receipt schema is:

`JEPA_V5_BASE_LEARNING_STEP_QUALIFICATION_RECEIPT_V1`

The validator fail-closes on at least:

- FULL104 binding not closed;
- missing explicit bounded qualification-run authority;
- protected/pathology/confirmation access;
- production-training claims;
- undeclared analysis/generalization unit;
- aggregation that sets effective n without estimand justification;
- missing comparator classes;
- winner-only reporting without a full curve;
- missing limiting/null comparator;
- boundary selection without limiting-object diagnosis;
- grid expansion before boundary diagnosis;
- missing effective-capacity diagnostic;
- non-production-derived capacity threshold;
- importing a numeric T0 capacity threshold;
- FULL104 geometry mismatch;
- failure to preserve ragged/native support;
- toy/mismatched simulation as production authority;
- missing evidence digests;
- biological-null overclaim;
- loss of T0/Target Discovery lane separation.

Even on PASS the validator emits:

- `td60_authorized = false`
- `relational_target_activation_authorized = false`
- `training_authorized = false`

## Dependency effect on TD60

TD60 remains a separate learned-geometry continuity test using the exact frozen TD57B/TD59 relational semantics. This amendment adds an upstream prerequisite: a teacher checkpoint cannot be scientifically promoted into TD60 merely because its training mechanics are healthy or because it reached an exposure milestone. The underlying learner must first have a valid base-learning-step qualification receipt.

TD60 then asks a different question: whether the learned geometry preserves the previously demonstrated relational biology. The two gates must not be merged.

## Dependency effect on partial-evidence student qualification

Partial-evidence relational predictability remains downstream of TD60. It cannot rescue a base learner that never established a resolvable contribution over null/technical comparators. Likewise, a strong student shortcut attack result cannot retroactively establish the teacher's learning step.

## T0 findings used only as methodology

The following T0 observations motivated the amendment but are not V5 thresholds or biological claims:

- effective df of the T0 fitted expression component was at most 0.28;
- the V20 CV curve was monotone toward its edge;
- the nuisance-only limiting comparator was unresolved from the best finite-ridge point at n=28;
- donor-level pseudobulk reduced the effective learning sample to tens of donors despite hundreds of thousands of cells;
- a low-dimensional simulation failed to represent the actual high-dimensional learning geometry.

Their role here is to specify failure modes the V5/TD pipeline must detect prospectively.

## Current authority statement

As of this amendment:

- FULL104 current-byte rebinding is still required;
- the learning-step protocol may be developed and tested;
- no bounded learning-step qualification run is authorized by this document;
- no production training is authorized;
- TD60 is not authorized;
- relational target activation is not authorized;
- protected partitions and pathology remain closed.

`training_authorized = false`
