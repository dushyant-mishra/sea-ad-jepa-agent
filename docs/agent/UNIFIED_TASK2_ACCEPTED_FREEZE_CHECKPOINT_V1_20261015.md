# Unified Task 2 Accepted Freeze Checkpoint V1

Date: 2026-10-15
Status: `UNIFIED_TASK2_ACCEPTED_AND_FROZEN__UNIFIED_TASK3_MAY_BEGIN_RED_FIRST`

## Exact accepted implementation

- PR: #390
- accepted head: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- freeze branch: `freeze/unified-task2-accepted-c7dfff1c-20261015`
- frozen Task 1 ancestor: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- frozen Task 0 ancestor: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`

## Independent acceptance

Macha focused re-check head: `57f3496a`

Evidence:
- `docs/agent/MACHA_UNIFIED_TASK2_B1_B4_RECHECK_C7DFFF1C_20261015.md`
- `results/target_discovery/unified_qualification_v1/MACHA_UNIFIED_TASK2_RECHECK_VERDICT_V1.json`

Verdict:

`ACCEPT_UNIFIED_TASK2`

`TASK2_MAY_BE_FROZEN__UNIFIED_TASK3_MAY_BEGIN_PROSPECTIVELY`

The independent hostile re-attack records 27 attacks/positive controls with BAD=0. T2-B1, T2-B2, T2-B3 and T2-B4 are CLOSED. The only real-data read was reader-split partition-identity metadata; no protected biological/candidate/validation/oracle values were opened.

## What was accepted

### T2-B1 — population authority
Every implemented authority consumer re-resolves reader-split bytes, recomputes split identity, exact fit/validation/oracle membership and the five deterministic folds. Copied digest strings do not create authority. The historical population-registry digest `50b29d7e...` remains custody metadata only.

### T2-B2 — producer access receipts
Authoritative observed-access receipts require harness-issued sessions and a harness-stored HMAC-attested ledger. Hand-made V1/V2 ledgers, forged signatures and genuine receipts presented to the wrong registry are refused.

### T2-B3 — sub-policy consistency
Cross-fit, protected-partition and reader-partition sub-policies must equal deterministic derivations of the access policy. Biological-value access, post-hoc folds and validation/oracle rescue semantics are refused.

### T2-B4 — manifest identity surface
The manifest binds normalization/library contract identity, TargetPortfolio code and policy identities, and a closed per-unit execution-identity table. Required fields are code/schema aligned; nested role swaps, missing bytes, omitted fields, empty tables and extra keys are refused.

## Binding carry-forward obligations

These are non-blocking for Task 2 freeze but become explicit downstream obligations.

### R1 — process isolation before human execution
Current application-level custody is not an OS/process sandbox. Before any `HUMAN_EXECUTABLE` or human execution, registry, signing key and reader-fit values must live outside the producer process; harness finalization must be external to the producer; protected partitions must be physically absent from producer processes.

### R2 — nested contract content
Nested objects are identity/role checked, but owning tasks must enforce substantive content schemas for metrics, falsifiers, reference producers, normalization/library contracts and TargetPortfolio policy.

### R3 — fixture authority cannot silently become human authority
`FIXTURE_UNBOUND` receipts validate by design. Every downstream human-authority consumer must explicitly require `AUTHENTICATED_READER_SPLIT`.

### R4 — persistence and key custody
Attested ledgers are currently in-memory and the HMAC key is caller-supplied. Durable ledger persistence and signing-key custody must be designed before receipts cross process boundaries. Task 3 must model this dependency; runtime realization belongs later.

### R5 — cross-fit claim scope
Fold 4 contains only one NPH52 donor. The five-fold law supports pooled donor-level cross-fit analyses, not per-fold source-stratified claims.

### R6 — recursive verification cache
Memoize recursive receipt verification before Task 3 becomes operationally expensive, but any cache must be identity-bound and cannot bypass revalidation after dependency mutation.

## Gate transition

Unified Task 2 is frozen at exactly `c7dfff1c...`.

Unified Task 3 may now begin **prospectively, RED-first**, consuming this exact freeze and carrying R1–R6. Unified Task 4 remains blocked until Unified Task 3 is independently accepted and frozen.

## Authority unchanged

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This checkpoint grants no target winner, representation winner, protected-value access, Stage 4 authority, human-execution authority or training authority.