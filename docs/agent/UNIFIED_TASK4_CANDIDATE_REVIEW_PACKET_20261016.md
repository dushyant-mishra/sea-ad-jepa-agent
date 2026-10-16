# Unified Task 4 successor-2 candidate review packet

Status: `SUCCESSOR2_MECHANICALLY_GREEN__HOSTILE_REVIEW_REQUIRED`

Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Original implementation PR: #404  
External-root repair PR: #406  
Sealed-object binding repair PR: #408  
Active repair branch: `repair/unified-task4-sealed-object-binding-20261016`

## Authority boundary

Task 4 V1 is non-authorizing custody mechanics. Repository-constructible signers, verifiers, actor policies, head publishers, expected heads, campaigns, challenge definitions, and realization sets cannot create biological, target, representation, Stage 4, protected-value, or training authority. Repository replay remains non-authorizing and genuine external authority remains unwired.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated.

## Rejected candidates — permanent history

### Candidate 1

`b31371d62f3270c965d321e61c35898ca6be3721` on `candidate/unified-task4-green-b31371d6-20261016` is **rejected**. Hostile PR #405, run `38953203662`, job `117149477378`, proved that caller-owned signer/verifier/actor/policy/head objects could self-mint the whole trust graph. Follow-up RED `38953623988` / `117150890636` showed caller inputs could make replay authoritative.

### Candidate 2

`c537db4e7b5b916cb3ddee1872fd4afa623a9b33` on `candidate/unified-task4-successor-green-c537db4e-20261016` is **rejected**. Hostile PR #407, run `38954964212`, job `117155395974`, proved post-seal substitution: a caller could replace the committed challenge definition and committed realization set with hand-constructed objects sharing the campaign identity.

Do not rehabilitate either rejected candidate from earlier green CI.

## Current successor-2 repair

The campaign now binds the exact sealed definition SHA-256 and exact realization-set root. Every downstream transition that consumes sealed objects validates those bindings, and a supplied realization set must recompute to its claimed root. Definition substitution, realization substitution, and root-alias objects therefore fail closed.

Exact mechanically verified code/schema head before review-artifact-only edits:

`89fb48d581ba37bce9496854d039d900535d47c8`

Read-only Task 4 run `38955545446`, job `117157367488`:

- focused Task 4: `104 passed, 1 skipped`;
- projected 100k replay benchmark: `1 passed`;
- full unified Task 0-4 regression: `295 passed, 1 skipped`.

Same exact head passed:

- Task 1 A1-A9: `38955545469`;
- Task 2 manifest/access: `38955545455`;
- Task 3 registry: `38955545397`;
- unified synthetic integration: `38955545761`.

## RED evidence that must remain explainable

- original missing interfaces: `38938697657` / `117100597615`;
- terminal accounting: `38943608912` / `117117078319`;
- schema drift: `38944319232` / `117119472176`;
- incomplete/aliasable C1-C9 law: `38944836349` / `117121219990`;
- unauthenticated signer object: `38945592644` / `117123776998`;
- self-asserted actor/process context: `38946266116` / `117126036930`;
- full caller-self-minted trust graph: `38953203662` / `117149477378`;
- expected-head authority self-mint: `38953623988` / `117150890636`;
- post-seal object substitution: `38954964212` / `117155395974`;
- missing exact sealed-object bindings: `38955121063` / `117155935852`.

## Required next hostile review

The next review must attack the exact newly pinned SHA, on a separate branch. In particular, test whether a caller can bypass the lifecycle by directly constructing `QualificationCampaign` in an advanced state with matching attacker-chosen sealed-definition/root fields, without traversing the legal transitions. Also retain all prior trust-root, revocation, exposure, reveal, accounting, replay, and no-echo attacks.

Any caller-fabricable advanced lifecycle state that permits downstream mechanics without lawful provenance is a rejection blocker, even though Task 4 remains non-authorizing.

## Acceptance rule

Only an immutable exact SHA may be reviewed. Return explicit `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` with concrete blockers. Even ACCEPT can qualify only non-authorizing Task 4 mechanics; it cannot establish biological truth or grant target, representation, Stage 4, protected-value, or training authority.
