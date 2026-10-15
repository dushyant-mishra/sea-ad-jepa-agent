# Unified Task 3 successor repair ledger — 2026-10-15

Status: `TASK3_REJECTED_OPEN_REPAIR_REQUIRED`

This ledger records successor custody after the independent Macha rejection of Unified Task 3. It is not an acceptance, freeze, training authorization, target decision, representation decision, or Task 4 authorization.

## Controlling authority

- frozen Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- frozen Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- frozen Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- rejected Task 3 candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`
- Macha review: `869ca777a498181c519ccfc04b8bf5db0f2888c7`
- global authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Preserved RED baseline

Read-only CI reproduced Macha B1-B5/B6-related attacks before production repair: `11 failed, 53 passed`. The failures were B1, B2, five B3 identity attacks, two B4 cache attacks, and B5 H5/H6 history attacks.

## Repair status

- B6: self-rewriting RED6 and cycle4 workflows deleted before production repair; read-only B6 workflow policy now passes.
- B1: frozen Task 1 authority validation enforced at every promotion boundary; training stages remain forbidden for `NO_TRAINING_AUTHORITY` units.
- B2: closed stage-evidence policy; unavailable sealed-challenge and human-execution evidence fails closed rather than being fabricated.
- B3: frozen identity-bound actor registry with strict registered actor/role checks; alias and self-minted identities are rejected.
- B4: caller-supplied verification cache is non-authoritative; each readiness call owns a fresh internal cache.
- B5: RED custody tests added first. Candidate implementation preserves the pre-B5 registry byte-for-byte in `registry_v1_legacy.py` and places an external `RegistryHistoryCustody` facade in `registry_v1.py`. Genesis must be history-free and no later than `KNOWN_TRUTH_QUALIFIED`; lawful promotion/revocation events are append-only and HMAC-attested; actor-registry, exact event history and current unit state are validated; prerequisite-only additions are permitted; `HUMAN_EXECUTABLE` and advanced revocation require matching external custody.

B5 candidate commits:
- `5c5aa6608fb3e5767fde5b87358612c68c834a20` — preserve pre-custody implementation as legacy evidence.
- `4d3552a62f85657debe4505a28c20e8cfb1762e5` — external append-only history custody facade.

Task 3 remains rejected until exact-head focused/full regression and focused independent Macha B1-B6 recheck succeed.
