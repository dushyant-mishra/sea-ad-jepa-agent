# Unified Task 3 successor repair ledger — 2026-10-15

Status: `TASK3_CANDIDATE_GREEN__INDEPENDENT_RECHECK_REQUIRED`

This ledger records successor custody after the independent Macha rejection of Unified Task 3. It is not yet an acceptance, freeze, training authorization, target decision, representation decision, or Task 4 authorization.

## Controlling authority

- frozen Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- frozen Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- frozen Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- rejected historical Task 3 candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`
- Macha rejection review: `869ca777a498181c519ccfc04b8bf5db0f2888c7`
- repaired Task 3 code candidate: `68df31584d17f91da2635cdf8e03bbe93695f9d1`
- review-package head before this pinning-only ledger commit: `5f8d2854ac157cf961748c211058da26b9f046de`
- global authority remains: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Preserved RED baseline

Read-only CI reproduced the independent findings before repair: `11 failed, 53 passed`. Failures were B1, B2, five B3 identity attacks, two B4 cache attacks, and B5 H5/H6 history attacks.

## Repair status

- B1: frozen Task 1 authority validation enforced at every promotion boundary; `NO_TRAINING_AUTHORITY` units cannot enter training stages.
- B2: closed stage-evidence policy; unavailable sealed-challenge/human-execution evidence fails closed.
- B3: frozen identity-bound actor registry; aliases, lookalikes, unknown and self-minted actors are rejected.
- B4: caller-controlled verification cache is non-authoritative; readiness uses fresh internal verification state.
- B5: external append-only `RegistryHistoryCustody` anchored at a history-free genesis; lawful promotion/revocation events are HMAC-attested and exact history/current unit state are checked.
- B6: self-rewriting RED6/cycle4 workflows were removed before repair; read-only workflow policy passes. Historical bot-authored mutations remain custody evidence, not authority.
- Dead public authority-like inputs `asserted_ready` and `prerequisite_evidence_verifier` were removed from the public Task 3 API.

## Exact-head verification

Code candidate: `68df31584d17f91da2635cdf8e03bbe93695f9d1`

All required read-only CI is GREEN on this exact code candidate:

- Unified Task 3 registry — run `38806385403`, job `116668232197`: focused Task 3 `74 passed`; full `tests/v5/td_unified` `177 passed`; token permission `Contents: read`.
- Unified Task 3 B6 workflow policy — run `38806385464`: PASS.
- Frozen Task 0 regression — run `38806385387`: PASS.
- Frozen Task 1 regression — run `38806385399`: PASS.
- Frozen Task 2 regression — run `38806385406`: PASS.
- Unified synthetic integration — run `38806385364`: PASS.

Diff audit from frozen Task 2 `c7dfff1c...` to code candidate `68df3158...` shows Task 3/workflow/docs/schema/test additions only; frozen Task 0-2 production files are not modified.

## Focused independent recheck brief

Review only B1-B6 on repaired code candidate `68df31584d17f91da2635cdf8e03bbe93695f9d1`; do not restart historical audits.

Required questions:
1. Can a `UNIT:*` / `NO_TRAINING_AUTHORITY` unit reach a forbidden training stage?
2. Can any stage advance without its closed evidence requirement?
3. Can aliases, Unicode lookalikes, unknown/self-minted actors, or same-actor identities bypass independence?
4. Can caller cache state create or preserve false readiness?
5. Can deleted/fabricated promotion or revocation history regain readiness or permit an advanced transition without the external genesis/head anchor?
6. Can any qualification workflow rewrite Task 3 production code/tests or push an automatic GREEN repair?

Acceptance requires all six answers to be no and no new authority/custody blocker of equivalent severity.

Task 3 remains non-authoritative until that independent review accepts the repaired bytes. Task 4 remains blocked until then.
