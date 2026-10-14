# Unified TD Qualification and Downstream Custody Architecture V1

## 0. Purpose and authority

This specification defines one scientific execution system spanning known-truth qualification, human TD execution, target handoff, and downstream JEPA certification.

It replaces the operating model of independently advancing TD, synthetic, and downstream qualification implementations with one chain of custody:

```text
real calibration/support data
        ↓
known-truth substrate OR sealed human input
        ↓
exact production producers
        ↓
authenticated artifacts
        ↓
exact production executors
        ↓
TD qualification registry
        ↓
frozen TD controller
        ↓
Target Qualification Bundle
        ↓
downstream certification
        ↓
training eligibility review
```

Known-truth mode is a certification mode of the same production system, not a second implementation.

This specification creates no human biological result and authorizes no candidate outcome opening, target selection, representation selection, TD60, Stage4, synthetic training, or real training.

Authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Architectural invariant: producer → artifact → executor → verdict

Scientifically meaningful inputs to a gate must be produced by an authenticated producer, serialized as an authenticated artifact, and consumed by an exact registered executor.

A caller may not acquire scientific authority merely by supplying:

- support labels;
- displacement values;
- margins;
- null distributions;
- qualification booleans;
- receipt strings;
- applicability labels;
- baseline families;
- source/endpoint rosters;
- reference identities;
- precomputed transforms;
- candidate-specific policy decisions.

Any such quantity that affects a scientific verdict must originate from a registered producer or frozen static policy artifact whose code/data identity is bound in the execution manifest.

Qualification attaches to the complete producer/artifact/executor unit, not to a gate name in isolation.

## 2. Shared execution modes

### 2.1 Known-truth mode

Known-truth mode supplies a production-realistic `KNOWN_TRUTH_CASEBUNDLE_V1` to the exact production interfaces.

The hidden answer lives only in an external `TRUTH_BUNDLE_V1` that is inaccessible to all producers, executors, target-controller logic, and downstream model code.

Required flow:

```text
KNOWN_TRUTH_CASEBUNDLE_V1
  → production producer(s)
  → authenticated production-shaped artifact(s)
  → production executor(s)
  → normal TD verdict(s)
  → frozen TD controller
  → TARGET_QUALIFICATION_BUNDLE_V1

TRUTH_BUNDLE_V1
  → external adjudicator only
```

No truth value may influence producer inputs, executor inputs, baselines, support states, estimability classes, candidate policies, reference construction, or winner selection.

### 2.2 Human-sealed mode

Human-sealed mode uses authenticated real inputs under the same gate-facing schemas and the same production producers/executors.

There is no `TRUTH_BUNDLE_V1`.

Human execution is permitted only for registry units whose authority state has lawfully advanced to `HUMAN_EXECUTABLE` and whose real prerequisite receipts exactly match the execution manifest.

### 2.3 Prohibited mode branching

Production gate code must not change scientific behavior based on whether an input is synthetic or human.

Prohibited examples include:

- synthetic-only thresholds;
- synthetic-only support rules;
- synthetic-only null laws;
- synthetic-only metric orientation;
- relaxed receipt validation in known-truth mode;
- direct truth access from a producer or executor;
- gate-specific toy fixtures masquerading as same-code-path qualification.

Synthetic-only labels may exist only for external challenge metadata and truth adjudication, outside the production scientific path.

## 3. `TD_EXECUTION_MANIFEST_V1`

### 3.1 Purpose

The execution manifest freezes the exact scientific machine for one execution attempt.

It binds immutable code/artifact identities, not branch tips or PR numbers.

Any decision-bearing code or policy change creates a new manifest identity.

### 3.2 Required top-level fields

At minimum:

```text
manifest_schema
manifest_version
manifest_created_at
canonical_registry_sha
observation_contract_sha
support_contract_sha
controller_code_sha
controller_policy_sha
candidate_registry_sha
endpoint_registry_sha
source_registry_sha
qualification_registry_sha
required_gate_units[]
authority_snapshot
```

### 3.3 Required per-unit bindings

Each producer/artifact/executor unit must bind, as applicable:

```text
unit_id
estimand_id
producer_code_shas[]
static_policy_shas[]
artifact_schema_sha
executor_code_sha
metric_contract_sha
metric_orientation
observation_operator_contract_sha
support_universe_sha
required_source_roster_sha
required_endpoint_roster_sha
statistical_law_sha
frozen_alpha_or_error_budget
reference_artifact_type_shas[]
baseline_policy_sha
falsifier_policy_sha
challenge_family_registry_sha
known_truth_qualification_receipt_sha
real_prerequisite_receipt_shas[]
current_authority_state
```

### 3.4 No branch-tip inheritance

A branch or PR number may be recorded as navigation metadata only.

It may never be used as a scientific identity.

If any bound implementation moves, the old manifest remains frozen and a new manifest must be created after explicit reclassification.

## 4. `TD_QUALIFICATION_REGISTRY_V1`

### 4.1 Purpose

The registry records what has actually been demonstrated about each complete producer/artifact/executor unit.

It must prevent ambiguous terms such as simply `qualified`, `green`, or `PASS` from carrying more authority than was established.

### 4.2 Authority states

The minimum lifecycle is:

```text
SEMANTICS_ONLY
FIXTURE_SAME_INTERFACE
SAME_CODE_PATH
KNOWN_TRUTH_QUALIFIED
REAL_REFERENCE_READY
HUMAN_EXECUTABLE
HUMAN_EXECUTED
```

States are monotone with respect to evidence, but any code/policy identity change creates a new registry identity rather than inheriting the old state.

### 4.3 Meaning of states

**SEMANTICS_ONLY** — scientific object is specified but no executable compatibility claim is made.

**FIXTURE_SAME_INTERFACE** — fixtures reproduce the intended input/output schema but do not exercise the exact production scientific implementation.

**SAME_CODE_PATH** — known-truth or fixture execution invokes the exact registered production producer/artifact/executor path with no scientific mode branch.

**KNOWN_TRUTH_QUALIFIED** — the exact unit passes prospectively frozen known-truth challenges, hostile controls, custody tests, and false-certainty/false-abstention tests.

**REAL_REFERENCE_READY** — all required real calibration/reference/support producers and artifacts exist, are independently qualified, and match the manifest.

**HUMAN_EXECUTABLE** — human candidate execution is lawfully permitted under a frozen manifest and controller.

**HUMAN_EXECUTED** — the registered human execution has occurred and an immutable receipt exists.

### 4.4 Hard promotion rules

No state may be skipped.

Green CI alone never advances authority.

A gate decision executor cannot reach `KNOWN_TRUTH_QUALIFIED` if a decision-bearing producer remains caller-supplied or unqualified.

A unit cannot reach `REAL_REFERENCE_READY` based solely on repeated synthetic/technical draws when the required real statistical estimand or exchangeability law is unresolved.

A unit cannot reach `HUMAN_EXECUTABLE` if any required source/endpoint/support/reference dependency remains blocked.

## 5. Producer/artifact/executor qualification units

The following classes of gate must be qualified as integrated units rather than arithmetic executors alone.

### 5.1 G8

Required unit includes:

- observation-state-aware count/library thinning producer;
- support-universe producer;
- reference/calibration producer;
- exact metric contract;
- G8 decision executor.

Known-truth qualification must include measured-zero preservation, structural-state exclusion, identity-keyed randomness, counts-plus-library thinning, exact support denominator binding, and fail-closed statistical-estimand behavior.

### 5.2 G6

Required unit includes:

- teacher/student metric producer;
- substantive measurement/reference-margin producer;
- exact metric-scale contract;
- produced qualification receipt;
- G6 decision executor.

Refit-only or zero substantive margin cannot authorize a human positive claim.

### 5.3 G9/S1/S2

Required unit includes:

- support producer;
- alignment producer;
- displacement producer;
- adverse-null producer;
- stability/reference producer;
- decision executor.

The unit must enforce source noncompensation, reject extra-source rows, prevent underresolved-null masking of an estimable stability failure, verify alignment properties, and fail closed on unresolved eigengap/producer authority.

### 5.4 R1

Required unit includes:

- molecular-view/ruler producer;
- relation-case producer;
- depth/detection-matched null producer;
- Y-cell identity null producer for human execution;
- exact metric/tie contract;
- decision executor.

Known-truth technical diagnostics cannot substitute for the human identity-null producer.

### 5.5 G2

Required unit includes:

- candidate-specific static baseline/applicability policy producer;
- support/strata producer;
- same-metric substantive reference producer;
- deciding artifact producer;
- G2 decision executor.

The strongest prospectively applicable frozen nuisance baseline family must be explicit and input-bound.

### 5.6 G7

Required unit includes:

- evidence-right/support producer;
- content-hash rights validation;
- source roster/support producer;
- source-aware terminal decision executor.

Evidence acquisition and measurement-depth perturbation remain separate scientific axes.

### 5.7 R4/C6/C4

Required unit includes:

- matched increment producer;
- required comparator set;
- same-metric reference artifacts;
- source/endpoint support producer;
- common adjudicator.

C6 must be tested against all required constituent comparators and C4 cannot bypass independently qualified C6.

## 6. `KNOWN_TRUTH_CASEBUNDLE_V1`

### 6.1 Purpose

This is the production-realistic input substrate for known-truth certification.

It must expose exactly the gate-facing information that lawful human execution would expose, using the same schemas and contracts.

### 6.2 Required modeled structure

At minimum:

- canonical molecular-address universe;
- donor/source/operator hierarchy;
- four-state observation semantics;
- stored versus unmaterialized library mass;
- measured zero distinct from unsupported/unmeasured;
- candidate-specific support;
- evidence-right ladders;
- count/depth observation processes;
- biological donor/state/context variation;
- technical nuisance variation;
- source asymmetry;
- rare/sparse strata;
- reference-generation opportunities;
- numerical failure opportunities;
- candidate/endpoint/source identities in the same canonical format used by human execution.

### 6.3 Observation operator doctrine

Technology/measurement descriptors may condition the observation model when physically justified.

Arbitrary dataset identity must not define latent biology.

Biological donor/state/context variability must not be erased merely because it predicts source.

### 6.4 Library-mass semantics

Observation simulation must separately track:

- observed measured-scalar counts;
- off-address/unmaterialized library mass when relevant;
- structural/unmeasured states;
- collision-unresolved states;
- evidence-right withholding.

Any depth/thinning operator acting on measured scalar counts must transform the matching normalization-library quantity consistently.

Measured zero remains a measurement.

## 7. `TRUTH_BUNDLE_V1`

### 7.1 Separation law

`TRUTH_BUNDLE_V1` is physically and logically separate from `KNOWN_TRUTH_CASEBUNDLE_V1`.

It may contain:

- latent biological mechanisms;
- true candidate/target status;
- true support/estimability labels where controller-known by construction;
- true positive/negative/null status;
- challenge-family identity;
- expected lawful TD terminal state;
- expected `TARGET=NONE` state;
- known malformed-artifact truth.

It must never be serialized into the producer/executor input tree.

### 7.2 External adjudication only

Truth is consumed only after normal production verdict/controller output is frozen.

The adjudicator scores correctness but cannot repair, rerun, tune, select, discard, or replace a realization after seeing outcomes.

## 8. Challenge-family registry

Known-truth qualification is organized around reusable scientific worlds, not bespoke per-gate toy fixtures.

The minimum V1 world family is:

### World A — clean identifiable biology

A real biological target exists, donor support is adequate, nuisance controls lose, and the correct target should survive.

### World B — nuisance-only

Only operator/library/depth nuisance exists. Correct terminal result is `TARGET=NONE` / `NO_WINNER`.

### World C — source-confounded

Apparent signal is restricted to one source/operator structure. Source noncompensation must prevent promotion.

### World D — sparse lawful

Biology is real but inferential resolution is insufficient. Required result is `NOT_ESTIMABLE`, not PASS or FAIL.

### World E — structural absence

Required evidence was never measurable. Zero-fill and false biological failure are prohibited.

### World F — measurement artifact

Library/depth variation counterfeits geometry/relations under an invalid observation/null producer. Correct producer/executor path must defeat the artifact.

### World G — leakage trap

Query, totals, support, normalization, or related metadata expose shortcut information. Downstream certification must detect the leak.

### World H — unstable coordinates / stable subspace

Subspace is scientifically stable while individual axes rotate. Coordinate-wise biological interpretation must be refused.

### World I — malformed producer artifact

Numeric values can be superficially correct while receipt/input/support identity is wrong. The artifact must acquire no authority.

Additional challenge families may be added prospectively, but no family may be weakened or removed after exposure merely because a method fails it.

## 9. Full TD known-truth rehearsal

### 9.1 Required execution chain

The first major integrated qualification milestone is an end-to-end known-truth TD rehearsal:

```text
CaseBundle
  ↓
candidate policies
  ↓
reference producers
  ↓
gate producers
  ↓
authenticated artifacts
  ↓
exact executors
  ↓
qualification registry checks
  ↓
mandatory falsifiers
  ↓
TargetPortfolio
  ↓
winner OR NO_WINNER
  ↓
TARGET_QUALIFICATION_BUNDLE_V1
  ↓
external truth adjudication
```

### 9.2 Required adjudication questions

The rehearsal must establish, prospectively:

- gates abstain when they should;
- unsupported biology remains unsupported;
- nuisance-only candidates lose;
- source-confounded signals cannot be rescued by pooling;
- truly identifiable targets can survive;
- sparse/underpowered lawful biology returns `NOT_ESTIMABLE` when required;
- `NO_WINNER` is a valid terminal result;
- malformed artifacts cannot gain authority;
- numerical failure cannot be converted into biological FAIL or lawful abstention;
- target/portfolio semantics exported downstream match the object that was actually qualified.

### 9.3 Controller freeze

The real TD controller, candidate policies, target portfolio rules, gate registry bindings, falsifier policies, and winner/no-winner law must be frozen before human candidate outcomes are opened.

Known-truth failures require prospective repair and requalification before human execution.

Human outcomes may not be used to tune challenge families, thresholds, support laws, producer semantics, registry promotion, or controller policy.

## 10. `TARGET_QUALIFICATION_BUNDLE_V1`

### 10.1 Purpose

This is the only lawful TD→downstream scientific handoff object.

Downstream systems must not consume a bare winner label.

### 10.2 Lawful no-target state

The schema must support:

```text
TARGET = NONE
```

as a first-class terminal result.

### 10.3 Required contents for a selected target/portfolio

At minimum:

```text
target_or_portfolio_identity
target_semantics
canonical_addresses
relation_semantics
observation_contract_sha
support_universe_sha
evidence_rights_contract_sha
estimability_scope
required_sources
required_endpoints
gate_receipts[]
producer_receipts[]
reference_receipts[]
mandatory_falsifiers[]
negative_controls[]
uncertainty_semantics
known_limitations[]
forbidden_interpretations[]
downstream_regression_requirements[]
execution_manifest_sha
qualification_registry_sha
controller_receipt_sha
```

### 10.4 Inherited invariants

The bundle exports the reasons a target was allowed to qualify, not merely its identity.

Examples of inherited downstream obligations include:

- library-size-only R1 counterfeit remains a permanent negative control;
- counts and normalization library move together under lawful thinning;
- source noncompensation remains mandatory where qualification required it;
- measured zero remains distinct from unsupported evidence;
- stable-subspace qualification does not authorize axis-wise biological interpretation;
- evidence-right acquisition remains distinct from depth remeasurement;
- biological novelty remains distinct from measurement OOD;
- target support/estimability scope cannot be silently widened downstream.

## 11. `DOWNSTREAM_CERTIFICATION_CONTRACT_V1`

### 11.1 Purpose

This is the second qualification firewall between TD and JEPA training eligibility.

The production downstream chain is:

```text
Target Qualification Bundle
  ↓
teacher construction
  ↓
student evidence restriction
  ↓
target representation
  ↓
JEPA objective
  ↓
evaluation
```

Known-truth certification must exercise the real downstream construction/evaluation code paths wherever they exist.

### 11.2 Mandatory historical hostile tests

The contract must permanently test at least:

- normalization leakage;
- query-scalar leakage;
- hidden-total/nGenes leakage;
- support leakage;
- wrong-cell pairing;
- donor leakage;
- source leakage;
- fake rich teachers;
- target incorrectly included in teacher/student inputs;
- teacher/student oracle confusion;
- evidence starvation;
- target-semantics drift between TD and training;
- stable-subspace versus unstable-axis interpretation;
- unlawful widening of support/estimability scope.

### 11.3 Training eligibility

Passing downstream certification does not itself turn training on.

It only makes the project eligible for a later explicit training-authorization decision.

Until that separate authorization exists:

`REAL_TRAINING_OFF` remains binding.

## 12. Authority-state transition law

### 12.1 Structural states, not prose claims

Registry/manifest/bundle schemas must structurally distinguish:

```text
MECHANICS_QUALIFIED
SAME_CODE_PATH
KNOWN_TRUTH_QUALIFIED
REAL_REFERENCE_READY
HUMAN_EXECUTABLE
HUMAN_EXECUTED
DOWNSTREAM_CERTIFIED
TRAINING_ELIGIBLE
TRAINING_AUTHORIZED
```

No single string such as `PASS`, `GREEN`, or `QUALIFIED` may substitute for these states.

### 12.2 Promotion evidence

Every transition requires an immutable receipt that binds:

- prior state;
- new state;
- exact code identities;
- exact artifact identities;
- exact challenge/reference identities;
- authority flags;
- independent review identity where required.

### 12.3 Fail closed

Missing, stale, moved, contradictory, unsigned/unbound, or schema-incomplete scientific dependencies fail closed.

No fallback threshold, inferred branch head, legacy prose PASS, or caller assertion may fill a missing authority object.

## 13. Integration with current repair surfaces

The current real TD lane is actively repairing individual producer/executor units.

Those PRs are navigation/evidence surfaces, not enduring scientific identifiers.

As each repaired unit becomes available, integration proceeds by:

1. freezing exact producer/executor/policy/artifact identities into a new `TD_EXECUTION_MANIFEST_V1`;
2. registering the unit at its demonstrated lifecycle state;
3. running same-code-path known-truth challenges;
4. advancing to `KNOWN_TRUTH_QUALIFIED` only after hostile qualification;
5. separately satisfying real reference/support prerequisites;
6. advancing to `HUMAN_EXECUTABLE` only under a frozen controller and manifest.

Known-truth infrastructure must not be blocked while incomplete units remain at lower registry states.

An incomplete unit is represented explicitly, for example:

```text
SAME_CODE_PATH = false
KNOWN_TRUTH_QUALIFIED = false
REAL_REFERENCE_READY = false
HUMAN_EXECUTABLE = false
```

rather than replaced with a synthetic analogue.

## 14. Division of ownership

### 14.1 Known-truth substrate ownership

The former synthetic-dataset lane owns:

- `KNOWN_TRUTH_CASEBUNDLE_V1`;
- `TRUTH_BUNDLE_V1`;
- deterministic identity-keyed world generation;
- challenge-family registry;
- realistic donor/source/operator/support worlds;
- observation-state and library-mass simulation;
- hidden-truth adjudicator;
- sealed realization custody;
- known-truth rehearsal fixtures.

### 14.2 TD/integration ownership

The TD/integration lane owns:

- `TD_EXECUTION_MANIFEST_V1`;
- registration of exact production producers/executors;
- `TD_QUALIFICATION_REGISTRY_V1`;
- authority-state transition law;
- real reference dependency binding;
- TD controller integration;
- `TARGET_QUALIFICATION_BUNDLE_V1`;
- downstream contract interface.

### 14.3 Joint ownership

Both sides jointly freeze:

- shared artifact schemas;
- CaseBundle gate-facing schema;
- TruthBundle non-exposure law;
- challenge acceptance criteria;
- downstream inherited invariants;
- same-code-path promotion criteria.

## 15. Migration from the former production-synthetic plan

### 15.1 Retained Tasks 1–3

The accepted canonical identity, custody/RNG, and calibration/provenance tasks remain shared foundation work.

### 15.2 Superseded Tasks 4–12

Independent synthetic implementations of biology→gate→controller→winner logic are not to be executed as previously planned.

Their useful scientific obligations are migrated into:

- known-truth substrate generation;
- production-realistic observation/support semantics;
- challenge families;
- external truth adjudication;
- exact producer/executor rehearsal;
- registry/manifest/bundle custody;
- downstream certification.

### 15.3 Historical evidence retained

Existing synthetic fixtures, sealed batteries, negative priors, and failed experiments remain historical evidence and test-design inputs.

They do not become controlling production logic unless explicitly promoted through this architecture.

## 16. Immediate milestone sequence

The next architectural sequence is:

1. complete/review shared Tasks 1–3;
2. freeze this unified architecture spec;
3. define machine schemas for the four shared integration objects;
4. define `KNOWN_TRUTH_CASEBUNDLE_V1` and `TRUTH_BUNDLE_V1` schemas;
5. define the challenge-family registry and acceptance rules;
6. register available exact producer/executor units at their current lifecycle states;
7. build same-code-path adapters only where production interfaces are actually ready;
8. construct the first end-to-end known-truth TD rehearsal;
9. require one lawful `TARGET=NONE` world and one identifiable-target world at minimum;
10. emit a real `TARGET_QUALIFICATION_BUNDLE_V1` from the rehearsal;
11. certify the downstream teacher/student transformation against that bundle;
12. only then consider a separate human execution/training authorization milestone.

## 17. Non-goals

This specification does not:

- choose a biological target;
- choose a representation;
- open current human candidate outcomes;
- invent real thresholds;
- qualify unresolved real reference estimands;
- authorize Stage4;
- authorize TD60;
- authorize synthetic or human training;
- merge or rewrite historical Git branches destructively.

## 18. Terminal invariant

The project is no longer considered TD-ready merely because individual gate executors are green.

TD readiness means the full custody system is qualified:

```text
producer
→ authenticated artifact
→ executor
→ qualification registry
→ frozen controller
→ Target Qualification Bundle
→ downstream certification
```

with known-truth and human-sealed execution using one scientific implementation and with all authority transitions explicit, receipt-bound, and fail-closed.
