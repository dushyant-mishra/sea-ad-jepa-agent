# Production Synthetic → Unified TD Execution Pivot

## Status

This document changes the execution interpretation of the accepted production-synthetic implementation plan after the approved TD/integration architecture pivot.

It does **not** alter the controlling V3.1/V3.1.1 scientific design obligations. It changes where those obligations are implemented and how authority flows.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Retained work

The existing production-synthetic Tasks 1–3 remain authorized shared infrastructure:

1. canonical identity / serialization;
2. custody / commit-reveal / identity-keyed RNG;
3. calibration, numeric provenance and realism-contract infrastructure.

These are common infrastructure for both known-truth and human-sealed execution modes.

## Superseded execution plan after Task 3

The old interpretation of Tasks 4–12 as an independently advancing synthetic implementation is retired.

In particular, there will be no independent production implementation of:

- synthetic G2;
- synthetic G6;
- synthetic G7;
- synthetic G8;
- synthetic R1;
- synthetic G9/S1/S2 geometry;
- synthetic R4/C6/C4 adjudication;
- a synthetic TD controller;
- synthetic winner-selection logic;
- a parallel synthetic target-qualification system.

Any earlier plan text that can be read as authorizing those parallel implementations is superseded by this pivot and by the `Unified TD Qualification and Downstream Custody Architecture V1` specification.

## New execution law

Known-truth certification must exercise the same production producer/artifact/executor interfaces used by human execution.

The required pattern is:

```text
KnownTruthCaseBundle
        |
        v
production producer
        |
        v
authenticated production-shaped artifact
        |
        v
production executor
        |
        v
normal TD verdict
        |
        v
external TruthBundle adjudicator
```

The hidden truth object is external to and inaccessible from producer and executor code.

No production gate may contain a scientific shortcut such as `if synthetic:` that changes gate semantics, thresholds, support rules, metric rules, null laws, or authority.

## Immediate next architecture

The next controlling design layer is:

`docs/superpowers/specs/2026-10-14-unified-td-qualification-downstream-custody-architecture-v1.md`

It defines:

1. `TD_EXECUTION_MANIFEST_V1`;
2. producer → authenticated artifact → executor contracts;
3. `TD_QUALIFICATION_REGISTRY_V1`;
4. known-truth execution mode;
5. human-sealed execution mode;
6. full TD controller rehearsal;
7. `TARGET_QUALIFICATION_BUNDLE_V1`;
8. `DOWNSTREAM_CERTIFICATION_CONTRACT_V1`;
9. authority-state transition law.

## Synthetic-lane ownership after pivot

The former synthetic lane owns the known-truth substrate side of the unified system:

- `KNOWN_TRUTH_CASEBUNDLE_V1`;
- `TRUTH_BUNDLE_V1`;
- deterministic identity-keyed world generation;
- challenge-family registry;
- realistic donor/source/operator/support worlds;
- observation-state and library-mass simulation;
- hidden-truth adjudication;
- sealed realization custody;
- known-truth rehearsal fixtures.

It does **not** own duplicate gate decision logic.

## Joint boundary

The TD/integration lane and known-truth substrate work jointly define:

- shared artifact schemas;
- gate-facing CaseBundle interfaces;
- TruthBundle non-exposure law;
- challenge acceptance criteria;
- downstream inherited invariants;
- promotion rules from fixture compatibility to same-code-path qualification.

## Stop gates

Existing production/sealed/finalization stop gates remain active. This pivot does not authorize a production realization, sealed human execution, target selection, representation selection, TD60, Stage4, or training.
