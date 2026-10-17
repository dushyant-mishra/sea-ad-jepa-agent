# Unified Task 2 prelaunch review packet V1 — 2026-10-15

Status: `PREPARED__TASK2_NOT_STARTED__BLOCKED_ON_TASK1_INDEPENDENT_ACCEPTANCE`

Binding authority:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## What Task 2 is

Unified Task 2 implements `TD_EXECUTION_MANIFEST_V1` and the current-TD population/data-access law required by architecture amendment A4. Its scientific purpose is to make it impossible for an apparently successful result to gain authority if it was produced with the wrong code, wrong policy, wrong population identity, or forbidden data access.

It is **not** a target-discovery run and it opens no candidate outcomes.

## Gate before launch

Task 0 is frozen at `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.

Current Unified Task 1 review candidate is `86fa996f609bec3f39d0f6a12d7f040b2544af39` in PR #385. Controller verification is GREEN, but fresh independent Macha acceptance is still required. Task 2 must not create its RED implementation branch until that exact head, or a later separately reviewed replacement, is accepted.

If the Task 1 head changes, do not inherit this packet mechanically. Rebind the launch base and confirm the Task 1 interfaces/semantics are unchanged or requalify the changed interface.

## Controlling sources

- accepted architecture PR #379: `3064ca545f0c94859ea989cd49a04fcbd5b9a303`;
- implementation-plan lineage PR #380: `5b6bf07e7d8b69b286ea430b09765a5ee4743325`;
- Task 0 freeze: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`;
- current Task 1 candidate: `86fa996f609bec3f39d0f6a12d7f040b2544af39`;
- detailed prelaunch plan: `docs/superpowers/plans/2026-10-15-unified-task2-td-execution-manifest-prelaunch-plan.md`;
- machine readiness: `results/target_discovery/unified_qualification_v1/UNIFIED_TASK2_PRELAUNCH_READINESS_V1.json`.

## Critical historical distinction

Historical production-synthetic Task 2 at `ff597faf2182522a320ec5322f8db9b67c9c6094` is a **sealed-custody/RNG substrate**, not the new Task 2. The old code/test blobs are preserved in the readiness ledger. Reuse its custody principles later where appropriate, especially Task 4/finalizer work; do not use it as evidence that the manifest/access-law task is already complete.

## Population/access law prepared for implementation

1. Outcome-bearing held-out evaluation is deterministic cross-fitting within `reader_fit` only.
2. `reader_validation` biological values remain inaccessible and cannot rescue fit estimability.
3. `reader_oracle` remains inaccessible until a later explicit authority transition.
4. Frozen partition identities may be bound for custody without granting value access.
5. Every producer receipt records **actual observed** partition/access classes; a policy declaration alone is insufficient.
6. Forbidden access invalidates the receipt even if the numeric output is identical to a lawful output.
7. Donors cannot leak across train/held-out sides of the same cross-fit split.
8. PR numbers, branch tips, free-text `held-out` labels and digest strings are navigation/claims, not scientific authority.

## Population custody already available

No new support census is needed to start Task 2. Reuse the authenticated historical population/split custody:
- population registry payload SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`;
- split SHA-256 `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`;
- 149 donors: 104 fit, 22 validation, 23 oracle;
- 42 operators, 3 sources, 2,028 donor×operator strata.

These are custody facts, not authorization to read protected values.

## One unresolved prelaunch design choice

Exact cross-fit fold count is intentionally not invented here. It must be prospectively frozen before the first outcome-bearing execution. Historical LODO feasibility is evidence that donor-held-out fitting is possible, not proof that LODO must be the unified policy; conversely a convenient K-fold choice has no authority without prospective justification.

Reviewer/implementer must confirm the exact fold assignment law is outcome-blind and frozen before execution. Once outcome-bearing execution starts, changing it requires a new manifest identity and requalification.

## First lawful implementation sequence after Task 1 acceptance

1. Cut Task 2 branch from exact accepted Task 1 head.
2. Freeze launch-base receipt and cross-fit assignment policy.
3. Add only `tests/v5/td_unified/test_manifest_v1.py` with controlling A4 RED tests plus hostile access tests.
4. Run RED and verify intended failure is missing Task 2 implementation, not an unrelated environment failure.
5. Implement `PopulationAccessPolicy` and actual `ProducerAccessReceipt` minimally.
6. Implement closed `TD_EXECUTION_MANIFEST_V1` validation using accepted Task 1 canonical/recursive verification.
7. GREEN Task 2 + Task 1 tests.
8. Run inherited Task 0 and unified-synthetic regressions.
9. Hostile self-audit and repeat RED/GREEN on every discovered defect.
10. Freeze exact controller candidate; do not treat it as independent acceptance without the required review.

## Required RED/hostile targets

The first suite must prove at least:
- cross-fitting cannot leave `reader_fit`;
- validation/oracle access cannot rescue estimability;
- actual accesses are enumerated;
- forbidden observed access defeats numerical success;
- bare `held-out` text has no authority;
- exact code/policy/schema/registry/population identities are bound;
- branch/PR identity cannot substitute for content identity;
- moving a decision-bearing identity changes manifest identity;
- protected aggregates cannot be relabeled as fit-side summaries;
- mutated policy bytes behind an unchanged digest string fail;
- unknown partitions/access classes fail closed.

## Review questions before launch

A reviewer should answer yes/no:

1. Is Task 1 independently accepted at the exact base head?
2. Are all Task 1 dependencies resolved by canonical object verification rather than digest-string trust?
3. Is the exact cross-fit assignment law frozen prospectively?
4. Are validation/oracle value rights explicitly denied in the current policy?
5. Are partition identity custody and partition value access represented separately?
6. Does `ProducerAccessReceipt` capture actual access, not only declared access?
7. Does the manifest bind every A4 identity required by V1.1?
8. Are navigation fields explicitly non-authoritative?
9. Is old synthetic Task 2 clearly quarantined as substrate rather than completion?
10. Are protected data, candidate outcomes and training authority still closed?

Any `no` blocks Task 2 launch or exact-head acceptance, depending on when discovered.
