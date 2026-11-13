# Unified Task 4 — Sealed Challenge Custody Preparation V1

Date: 2026-10-15
Status: `PREPARED__IMPLEMENTATION_BLOCKED_ON_TASK3_ACCEPTANCE`
Authority effect: **NONE**

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Gate

Unified Task 4 may be designed now but implementation must not begin until Unified Task 3 is independently accepted and frozen on an exact head.

Task 4 will then consume:

- frozen Task 1 canonical/authority primitives;
- frozen Task 2 manifest/access authority at `c7dfff1cee608e4a101855d42cf0af08491c2aaf`;
- frozen Task 3 registry/prerequisite/revocation authority.

No real sealed challenge worlds, hidden nonces or final qualification set should be generated during preparation.

## 2. Purpose

Implement architecture A3: strict separation of development challenges from sealed final qualification challenges, prospective commitment before exposure, append-only exposure history, frozen outputs before reveal, deterministic regeneration, and no post-exposure mutation that makes qualification easier.

Planned files:

- `scripts/v5/td_unified/challenge_custody_v1.py`
- `schemas/target_discovery/unified_v1/sealed_challenge_manifest_v1.json`
- `tests/v5/td_unified/test_challenge_custody_v1.py`

Planned interfaces:

- `DevelopmentChallengeManifest`
- `SealedQualificationCommitment`
- `SealedQualificationReveal`
- `commit_final_qualification(...)`
- `verify_reveal(...)`
- `record_qualification_exposure(...)`

## 3. Historical substrate to reuse, not re-authorize

Old production-synthetic Task 2 exact implementation:

`ff597faf2182522a320ec5322f8db9b67c9c6094`

Classification:

`ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE`

Reuse its tested concepts and hostile cases, not its authority status.

Mandatory inherited mechanics:

- append-only custody ledger;
- commitment/reveal lifecycle;
- explicit exposure records;
- linear lineage and supersession refusal;
- withheld-family nonce separation;
- fit/output freeze after exposure;
- deterministic RNG identity vocabulary;
- no-change successor/reroll guards;
- public/reused-family refusal;
- final eligibility only after own reveal;
- secret scanning;
- deterministic regeneration from the sealed root.

## 4. Mandatory historical attacks to migrate

The old Task 2 review repaired thirteen concrete holes. Unified Task 4 RED tests must reproduce them through the new interface:

1. can’t-get-easier rule ignoring some changed components;
2. replaced/superseded version still commit/expose capable;
3. withheld commitment allowed debug nonce;
4. easier withheld-family swap;
5. no-change successor reroll;
6. reused family remained secret after reveal;
7. class-nonce reveal leaked shared open-run family;
8. successor reverted to public family;
9. method rename reset draw count/multiplicity;
10. late exposure after fit freeze;
11. secret scanner failed realistic secret sizes;
12. eligibility true before own reveal;
13. ledger construction pathologically slow.

These are regressions, not optional examples.

## 5. Prospective E2 commitment clarification

The prior written commitment law was circular. Unified Task 4 must specify the accepted non-circular rule before implementation:

- public commitment payload contains lawful public metadata plus cryptographic commitments to hidden material;
- hidden nonce/specification bytes are absent from the public payload before reveal;
- the commitment identity is the canonical digest of that public commitment payload;
- reveal supplies hidden material and verification recomputes the committed digests;
- no payload digest is required to contain itself.

A test must fail any implementation that sneaks hidden challenge bytes into public commitment material or trusts caller-supplied reveal identity without regeneration.

## 6. D1 exception hardening before reuse

Old custody code broadly wrapped exceptions. Unified Task 4 must not count “crashed internally and got wrapped as CustodyError” as correct fail-closed behavior.

Before promoting reused primitives:

- narrow exception boundaries;
- preserve cause/class where safe;
- match specific refusal reasons in late-exposure, reveal-gating and lineage tests;
- add a deliberate internal-programming-error test proving it is distinguishable from lawful custody refusal.

## 7. Object model

### Development challenge

`DevelopmentChallengeManifest` must carry explicit `promotion_authority = NONE` and may be used for debugging/tuning only. Development challenge success can never produce `KNOWN_TRUTH_QUALIFIED`.

### Final commitment

`SealedQualificationCommitment` must freeze at minimum:

- exact frozen Task 2 manifest identity;
- exact frozen Task 3 registry identity;
- exact unit identities under qualification;
- challenge family/version;
- generator code and policy identities;
- number of worlds/realizations;
- RNG derivation law and root commitment;
- expected challenge classes and qualification budget;
- multiplicity/draw accounting law;
- controller and adjudicator identities;
- required hidden holdout count;
- fit/output freeze rule;
- cryptographic commitments to hidden specification/nonces;
- lineage parent for successors.

### Exposure record

Append-only record binds commitment, exposed world/family identity, exposure order, exact manifest/registry/code/policy identities, fit-freeze transition, previous ledger head and new ledger head.

No summary may erase earlier exposure.

### Reveal

`SealedQualificationReveal` supplies hidden material only after outputs are frozen. `verify_reveal(...)` must regenerate the committed worlds from the sealed root and compare exact identities; caller-provided world lists are non-authoritative.

## 8. Mutation law after exposure

After any final challenge exposure:

- failed worlds cannot be removed or replaced;
- challenge family cannot be swapped for an easier one;
- unchanged successor cannot reroll RNG;
- method rename cannot reset draw/multiplicity history;
- successor cannot revert to a public/reused family;
- late exposure after fit freeze is refused;
- post-exposure repair requires a new qualification identity and a newly sealed set;
- any allowed “harder/additional challenge” transition must be explicit, monotone and independently reviewable.

## 9. Task 2 residuals that Task 4 must respect

- R1: producer process cannot own future real harness registry/key/reader-fit values before human execution.
- R2: challenge generator/adjudicator/content contracts need substantive schemas, not identity labels only.
- R3: fixture challenge custody cannot silently become `AUTHENTICATED_READER_SPLIT` authority.
- R4: cross-process ledger persistence/key custody must be solved before sealed receipts cross processes.
- R5: pooled donor-level cross-fit scope cannot be widened to per-fold source-stratified claims.
- R6: recursive/custody verification caching must be identity-bound and invalidated on dependency mutation.

## 10. RED-first minimum matrix

Before implementation, preserve RED for at least:

1. development challenge cannot promote known-truth stage;
2. final commitment freezes family, generator, RNG law, realization count, class budget, multiplicity, controller and adjudicator;
3. at least one holdout stays hidden until output freeze;
4. early reveal hard-fails;
5. reveal mismatch hard-fails;
6. reveal world list is regenerated, not trusted;
7. failed exposed world cannot be removed/replaced;
8. post-exposure family swap refused;
9. no-change successor reroll refused;
10. method rename cannot reset draw count;
11. public/reused family cannot become “secret” again;
12. superseded commitment cannot expose or finalize;
13. final eligibility impossible before own reveal;
14. debug nonce cannot satisfy withheld commitment;
15. hidden material cannot appear in public commitment payload;
16. post-exposure repair creates new qualification identity/new sealed set;
17. internal programming exception is not mistaken for lawful custody refusal;
18. commitment with stale Task 2 identity refused;
19. commitment with stale/revoked Task 3 registry identity refused;
20. fixture-only authority cannot create human sealed authority;
21. ledger head mutation/reordering is detected;
22. secret scan handles realistic secret sizes;
23. large ledger replay/build meets a declared deterministic performance ceiling without changing scientific semantics.

## 11. Implementation sequence after Task 3 acceptance

1. branch from exact frozen Task 3 head;
2. add RED tests only, including all inherited thirteen attacks;
3. preserve RED commit;
4. adapt minimal proven primitives from old Task 2, not the whole module blindly;
5. implement non-circular commitment schema;
6. implement append-only exposure/reveal verification;
7. harden exception semantics;
8. run focused Task 4 suite;
9. run Task 3, frozen Task 2, frozen Task 1 and inherited synthetic regressions;
10. self-attack lineage, exposure, RNG, reveal and secret-custody boundaries;
11. freeze exact review candidate;
12. obtain independent Macha exact-head review before Task 5.

## 12. Explicit non-goals

Task 4 does not create biological truth, construct CaseBundle/TruthBundle, execute real target discovery, open validation/oracle values, select a target or representation, or authorize Stage 4/training.

The purpose is to make the future qualification exam tamper-evident and non-retunable—not to make any scientific claim by itself.