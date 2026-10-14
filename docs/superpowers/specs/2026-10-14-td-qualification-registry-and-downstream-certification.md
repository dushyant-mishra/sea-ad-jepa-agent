# TD Qualification Registry and Downstream Certification Integration

## Purpose

Unify the production synthetic qualification lane, real TD gate machinery, tournament controller, and downstream JEPA handoff into one scientific chain of custody.

The synthetic lane is a known-truth qualification laboratory for the same producer and executor interfaces used by real TD. It is not an independent biological decision system.

## Universal authority path

Every deciding gate must follow:

`producer -> authenticated artifact -> executor -> verdict`

Caller-supplied deciding labels, precomputed unbound numbers, booleans, literal receipt strings, or caller-selected scientific policy do not carry human authority.

## Qualification lifecycle

Each gate has exactly one registry entry and may advance only through:

1. `SEMANTICS_ONLY`
2. `FIXTURE_SAME_INTERFACE`
3. `SAME_CODE_PATH`
4. `SYNTHETIC_KNOWN_TRUTH_QUALIFIED`
5. `REAL_REFERENCE_READY`
6. `HUMAN_EXECUTABLE`

No state may be skipped. State advancement requires exact identity-bound evidence recorded in the registry.

## Registry contract

Each gate entry binds:
- gate identity and scientific role;
- exact executor repository commit and path;
- exact producer repository commit and path when a qualified producer exists;
- metric identity and orientation;
- support-universe identity;
- statistical law identity;
- required real reference artifacts;
- required synthetic challenge families;
- exact synthetic qualification receipt/workflow identity;
- unresolved real-data prerequisites;
- current lifecycle state;
- authority flags.

Branch names and green CI alone are not scientific identity.

## TD Execution Manifest

The execution manifest is generated from the registry. It freezes one exact approved set of producer/executor identities and their authority classes before any human candidate outcome is opened.

Synthetic rehearsal may include gates at `SYNTHETIC_KNOWN_TRUTH_QUALIFIED`. Human execution requires every deciding dependency for the requested gate to be `HUMAN_EXECUTABLE` and all required real reference artifacts to be authenticated.

## Common synthetic/real gate-facing substrate

Synthetic and real cases must enter the same gate-facing schemas. The gate executor must not branch on `synthetic` versus `real` to change scientific logic.

Controller-only known truth is physically separate from the executor-visible case bundle. The executor-visible object contains only lawful real-shaped identities, support/evidence objects, measurement semantics, observations, and authenticated reference artifacts.

## Producer qualification

Known-truth qualification must exercise the real producer and the real executor together where the gate relies on produced support, displacement, margins, nulls, alignments, thinning, or other deciding quantities.

A decision function passing unit tests on caller-forged numbers is insufficient.

## Sealed end-to-end TD rehearsal

Before human outcomes:
- candidate-neutral/dummy candidate identities flow through the actual tournament controller;
- exact gate registry and execution manifest are used;
- true-positive, true-negative, unsupported, underpowered, confounded and numerical-failure worlds are exercised;
- `NO_WINNER` is a normal valid result;
- no human biological threshold is imported from synthetic outcomes.

## Target Qualification Bundle

The downstream pipeline consumes one immutable bundle, not prose such as `C4 won`.

The bundle carries:
- selected candidate identity or `NONE`;
- canonical molecular addresses;
- support/estimability map identity;
- evidence-right ladder identity;
- required source strata;
- exact gate receipts;
- producer/executor identities;
- mandatory falsifier results;
- nuisance-baseline policy identity;
- uncertainty/reference identities;
- relational semantics/null identity where applicable;
- persistent known limitations;
- registry and execution-manifest identities.

Synthetic qualification establishes machinery and invariants, not which human biology is true.

## Downstream certification bridge

Before real JEPA training can ever become eligible, a second certification bridge must qualify:

`TD-qualified target -> teacher construction -> evidence-restricted student input -> target representation -> JEPA loss/evaluation`

Permanent adversarial classes include hidden-target leakage, query/address bottlenecks, totals/support/normalization leakage, evidence starvation, fake-rich teachers, student/teacher oracle confusion, source pooling rescue, wrong measurement operator, and loss of TD-qualified relational/support semantics.

A completed downstream certification receipt is necessary but not sufficient for real-training authority; global project authority remains separately controlled.

## Cross-lane architectural invariants

- observation technology is a physical observation operator, not biological identity;
- legitimate donor/context biology is not batch error;
- stable subspace does not imply stable axes;
- biological-evidence response and measurement-depth response are distinct estimands;
- biological novelty and measurement OOD remain distinct;
- source noncompensation and support semantics survive downstream;
- count thinning must transform stored counts and normalization library consistently;
- synthetic-derived invariants become permanent regression controls downstream.

## Current authority

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This integration work opens no human candidate outcomes and grants no biological or training authority.