# Macha role-independence correction V1 — 2026-10-14

Status: `CONTROLLING_ROLE_CLARIFICATION__NO_AUTHORITY_PROMOTION`

## Purpose

Correct an ambiguity in the merged-lane handoff/review instructions. Macha is a Claude coding/execution agent on the GPU laptop and also a valuable hostile reviewer of controller-authored work. Those roles are both real, but independence is claim-specific.

## Controlling role law

Macha may act as:

1. `GPU_EXECUTION_AGENT`
   - execute exact frozen GPU qualification commands;
   - access heavy/FULL104 assets on the GPU laptop;
   - emit source/config/runtime/hardware/artifact receipts.

2. `AUTHOR_IMPLEMENTER`
   - old PR #356 Tasks 1–2 at exact head `ff597faf2182522a320ec5322f8db9b67c9c6094` were implemented by Macha;
   - for those bytes Macha may explain design intent, attest provenance, reproduce behavior, and answer hostile questions;
   - those actions are author evidence, not independent review.

3. `INDEPENDENT_HOSTILE_REVIEWER_OF_CONTROLLER_WORK`
   - Macha may independently review controller/merged-lane artifacts that he did not author, including the Task 0 custody/consolidation at exact head `c80d7398b41f10208ec1622bc52599383b940be6`;
   - he may challenge whether controller migration classifications, no-repeat rules, F1/F2/F5–F9 completeness, and old Task 3/4 stop law are correct.

## Independence boundary

`SAME_AGENT_SEPARATE_PASS != INDEPENDENT_REVIEW`

A later pass by the same agent does not make that agent independent of its own implementation or execution.

Therefore:

- Macha must **not** be described as the independent qualifier/adjudicator of his own old Task 1–2 implementation;
- controller review PR #382 is the current independent verification layer over those exact Macha-authored bytes;
- Macha may review the **controller's proposed migration/classification** of those bytes, because that classification is controller-authored;
- any future GPU run executed by Macha requires a distinct reviewer/adjudicator before the run can promote qualification stage or runtime eligibility;
- if Macha writes or materially modifies a future qualification implementation, he cannot be the sole independent reviewer for that implementation.

## Correct Task 0 review split

### Macha reviews independently

At Task 0 exact head `c80d7398b41f10208ec1622bc52599383b940be6`, Macha should independently review:

- the Task 0 migration/custody implementation and hostile tests;
- F1/F2 repair closure;
- F5–F9 completeness;
- the controller's migration classifications for old Tasks 1–2;
- whether old Tasks 3–4 are correctly stopped with requirements-migrate-only;
- whether old Tasks 5–12 remain stopped as an independent authority lane;
- whether the Task 0 package is complete enough to freeze and allow unified Task 1 to begin RED-first.

### Macha does not independently review his own implementation

For old Task 1–2 exact head `ff597faf2182522a320ec5322f8db9b67c9c6094`, Macha's role is author/provenance attestation only. Technical independent verification is already represented by controller review PR #382:

- focused run `38644641042`, job `116128364543`: `332 passed in 8.94s`;
- inherited run `38644640881`: success.

Macha may identify defects in his own implementation, but a self-review cannot satisfy an independence requirement.

## GPU consequence

The project already has a GPU execution environment through Macha. Future package J/N/L/R work should use that environment when authorized, but the role split is:

`Macha executes -> exact receipts freeze -> different reviewer/adjudicator reviews -> only then possible promotion`

Macha's historical GPU capability is evidence that an executor exists; it does not itself qualify the current merged runtime.

## No-repeat / no-action boundary now

This clarification does not authorize any new execution. In particular, Macha should not:

- start old synthetic Task 3 or Task 4;
- start old Tasks 5–12;
- start unified Task 1 before Task 0 acceptance;
- run new production GPU training;
- open candidate outcomes, `reader_validation`, or `reader_oracle` for Task 0 review.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
