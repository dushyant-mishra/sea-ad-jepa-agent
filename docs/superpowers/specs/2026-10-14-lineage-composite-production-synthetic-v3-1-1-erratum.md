# Lineage-Composite Production Synthetic V3.1.1 — Focused Erratum

Date: 2026-10-14
Status: **CONTROLLING ERRATUM — E1–E7 ONLY — IMPLEMENTATION PLAN STILL OFF PENDING FOCUSED ACCEPTANCE**

This erratum amends the accepted V3.1 design solely to close E1–E7 from the Macha focused acceptance review (`dcd0754d901e862d3a06b6751e93126ff2874042`). It introduces no implementation, realization, fitting, scoring, target, representation, TD60, Stage4, synthetic-training or real-training authority.

Precedence: this erratum controls over V3.1 only for the clauses explicitly amended below. All other V3.1 requirements and external blockers remain unchanged.

Binding authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## E1 — post-exposure generator versions may not become easier

Replace the intent-based difficulty clause with the following law.

Once any downstream method has been exposed to any realization from a generator version, no later version may reduce, remove, relax or make easier any frozen difficulty dimension, adverse regime, control family, support challenge, population-imbalance challenge, novelty regime or measurement challenge.

The sole exception is correction of a **documented generator defect** that makes the generator scientifically invalid or violates the frozen design contract. Such a correction:
- creates a new generator version;
- is labeled `POST_EXPOSURE_VERSION`;
- records the exact defect, old/new generator hashes and affected challenge dimensions in the append-only lineage ledger;
- does not inherit qualification from the exposed predecessor;
- must re-run all pre-exposure realism/validity checks;
- must pass the committed withheld-family check described in E2 before any qualification claim;
- may not delete a difficult regime merely because it was implicated in a method failure.

If defect correction necessarily changes difficulty in an incomparable direction, the version is treated as a new scientific testbed rather than a continuation of the prior qualification substrate.

## E2 — the withheld-family specification is itself secret until reveal

The sealed-only withheld mechanism/composition check is not stored in readable generator source or public configuration before qualification.

Before any downstream exposure, the controller privately freezes:
- the complete withheld-family specification;
- its parameterization/distribution law;
- its applicability and scoring rule;
- its realization budget.

The controller publishes only a cryptographic commitment:
`H(withheld_spec || controller_nonce || generator_semantic_hash || withheld_class_tag)`.

The withheld specification and nonce remain controller-only until the sealed fit outputs are irrevocably frozen. They are then revealed and verified against the prior commitment before scoring. The public generator identity binds the **commitment**, not the readable withheld specification.

Any mismatch, early disclosure, alternative withheld-family draw, or selective replacement is a hard custody failure.

## E3 — G7 anti-thinning enforcement point

V3.1 biological-evidence semantics are not `SAME_CODE_PATH` qualified merely because a synthetic fixture enforces content-hashed rights and rejects thinning.

For G7 to be classified `SAME_CODE_PATH`, the real G7 validator/executor itself must prospectively enforce, from content rather than label alone:
- rights-token content hashes;
- strict nested evidence-right membership;
- unchanged bytes for already-visible evidence;
- rejection of count/depth thinning as biological-evidence restriction;
- distinction between `WITHHELD_BY_EVIDENCE_RIGHTS` and structural/unresolved support states.

Until the real validator enforces these properties, the synthetic status is:
`G7_EVIDENCE_SEMANTICS_COMPATIBLE_FIXTURE_ONLY__NOT_SAME_CODE_PATH`

and the dependency must be raised to the real lane as an explicit external blocker. A label such as `BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION` is never sufficient proof of semantics.

## E4 — provenance and derivation law for every frozen numeric design quantity

No implementation plan may invent or silently choose a decision-bearing number. Every frozen numeric quantity must carry:
1. a machine-readable provenance class;
2. exact source artifact / executor / mathematical derivation when one exists;
3. the derivation procedure;
4. whether it is empirical, mathematical, or a prospective convention;
5. a sensitivity or robustness requirement when convention-based.

Allowed provenance classes are:
- `AUTHENTICATED_EMPIRICAL_CALIBRATION` — derived only from a hash-bound, outcome-blind calibration artifact under the V3.1 calibration firewall;
- `PINNED_EXECUTOR_MATHEMATICS` — forced by the exact frozen statistical/executor law (for example finite-sample resolution);
- `PROSPECTIVE_CONVENTION` — no external biological authority is claimed; the value is declared before downstream exposure and must be stress-tested prospectively.

Specific requirements:

### Baseline ceilings
Marker-only, PCA-linear, library-only, source-only and other trivial-baseline ceilings must be derived from authenticated calibration/control distributions or labeled `PROSPECTIVE_CONVENTION`. They may not be tuned after candidate or downstream results are seen. Convention-based ceilings require a prospectively frozen sensitivity analysis and cannot become human biological thresholds.

### Teacher decoder ceiling
The teacher-to-expected-state decoder ceiling must be derived from authenticated observation/noise envelopes under the same modality observer. If no defensible empirical envelope exists, the ceiling is a `PROSPECTIVE_CONVENTION`, the affected G6-style claim remains synthetic-only, and sensitivity to the convention must be reported.

### Minimum support counts
Minimum required counts for support states/strata must come from the pinned executor's identifiability/resolution mathematics plus the frozen challenge-applicability law. Historical counts such as A3R incidence may be used to prove non-vacuous challenge availability, not copied as universal minima unless independently justified by the current support registry.

### R1 tie tolerance
The R1 tie tolerance `tau` must equal the pinned real R1 executor's tolerance once that executor exists. Before then, synthetic R1 same-code-path status remains blocked. Any temporary synthetic-only `tau` must be labeled `PROSPECTIVE_CONVENTION`, frozen before exposure, and accompanied by sensitivity analysis; it cannot become the real R1 threshold.

### Precision targets and realization budgets
False-qualification, false-abstention, false-certainty and related operating-characteristic precision targets are prospective statistical design conventions unless dictated by a pinned executor. The target error/interval requirement is frozen first; donor/world/null realization counts are then derived mathematically from that requirement. Counts may not be chosen by observing downstream performance.

### Realism iteration stopping rule
All realism calibration/tuning occurs **before any downstream method sees any realization from that generator version**.

Before the first realism iteration, freeze:
- the finite list of emitted-observation realism metrics;
- each metric's acceptance band and provenance class;
- the allowed observation-side parameters that may be adjusted;
- a maximum iteration/budget rule, labeled by provenance;
- the rule that hidden biological parameters may not be tuned to improve candidate/downstream performance.

Stop at the first generator version that simultaneously satisfies all frozen realism checks. If the budget is exhausted first, the generator is `REALISM_NOT_QUALIFIED`; do not choose the best-looking failed iteration. Once a version is exposed downstream, E1 applies and realism iteration cannot be used as a route to an easier post-exposure testbed.

## E5 — explicit estimability-to-output mapping

Controller truth and lawful downstream output map as follows:

- `ESTIMABLE_WITH_TARGET_PRECISION`: a calibrated `COMPLETE` result is lawful; `NOT_ESTIMABLE` is false abstention unless the exact pinned executor separately establishes a lawful decision-layer insufficiency not represented in controller truth.
- `IDENTIFIABLE_BUT_UNDERPOWERED`: either a calibrated `COMPLETE` result **or** a calibrated `NOT_ESTIMABLE` result is lawful. A `COMPLETE` result must still satisfy all estimator validity/uncertainty requirements; underpowered does not prohibit estimation, it prohibits forcing a decisive claim.
- `NOT_ESTIMABLE_BY_CONSTRUCTION`: lawful output is `NOT_ESTIMABLE`; `COMPLETE` is false certainty.
- `NUMERICAL_FAILURE` / historical `NOT_DIAGNOSED`: always hard estimator failure and never lawful abstention.

Gate-specific PASS/FAIL authority is separate from whether an estimate is `COMPLETE`. No mapping above creates human biological authority.

## E6 — R1 metric must bind to the future real executor

V3.1's expected-state relational truth fixes the scientific object but does not independently choose a production distance metric.

When a complete real R1 executor is prospectively qualified, the synthetic same-code-path rehearsal must use the **exact same**:
- distance metric;
- scaling/normalization law;
- ruler/address-set construction;
- common-coordinate rule;
- tie handling/tolerance;
- null construction;
- donor/source aggregation orientation.

If the real executor differs from the provisional synthetic-only metric, the synthetic rehearsal must be regenerated/requalified under the pinned real metric. Until then R1 remains:
`BLOCKED_EXTERNAL_R1_EXECUTOR_AND_SOURCE_PARAMETERIZATION`.

## E7 — controlling versus non-controlling documents

Only files under the controlling design/spec hierarchy explicitly named by PR #344's READ FIRST order may define or amend production-synthetic scientific requirements.

`docs/agent/**` files, including current-state summaries, handoffs, ledgers, audit reports, recovery maps and readiness notes, are **non-controlling navigation/audit/custody surfaces**. They may summarize or record evidence, but they cannot silently amend, weaken, supersede or create a scientific design rule.

If a `docs/agent/**` file conflicts with a controlling design/spec, the controlling design/spec wins and the conflict must be corrected visibly. Any new decision-bearing rule discovered in an audit must be promoted into an explicitly controlling design amendment before implementation planning may rely on it.

## Closure gate

This erratum closes design text only. A focused reviewer should inspect E1–E7 only.

Until that focused check passes:
`IMPLEMENTATION_PLAN_OFF__IMPLEMENTATION_OFF`.

On focused acceptance, the maximum next authorization becomes:
`WRITE_IMPLEMENTATION_PLAN_ONLY`.

That implementation plan must freshly re-read and classify the exact live heads of PRs #350, #351, #352, #353, #354 and #355 before freezing any downstream interface or dependency.

All existing V3.1 external blockers remain fail-closed unless independently resolved.