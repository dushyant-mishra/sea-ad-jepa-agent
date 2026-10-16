# Unified Task 4 successor-3 candidate review packet

Status: `SUCCESSOR3_MECHANICALLY_GREEN__HOSTILE_REVIEW_REQUIRED`

Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Original implementation PR: #404  
External-root repair PR: #406  
Sealed-object binding repair PR: #408  
Lifecycle-provenance repair PR: #410  
Active repair branch: `repair/unified-task4-lifecycle-provenance-20261016`

## Authority boundary

Task 4 V1 is non-authorizing custody mechanics. Repository-constructible trust objects, expected heads, campaign objects, sealed definitions, realization sets, and process-local lifecycle tokens cannot create biological, target, representation, Stage 4, protected-value, or training authority. Repository replay remains non-authorizing and no genuine external authority root is wired.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated.

## Rejected candidates — permanent history

### Candidate 1

`b31371d62f3270c965d321e61c35898ca6be3721` on `candidate/unified-task4-green-b31371d6-20261016` is **rejected**. Hostile PR #405, run `38953203662`, job `117149477378`, proved caller-owned signer/verifier/actor/policy/head objects could self-mint the trust graph. Follow-up RED `38953623988` / `117150890636` showed caller inputs could make replay authoritative.

### Candidate 2

`c537db4e7b5b916cb3ddee1872fd4afa623a9b33` on `candidate/unified-task4-successor-green-c537db4e-20261016` is **rejected**. Hostile PR #407, run `38954964212`, job `117155395974`, proved post-seal definition and realization-set substitution.

### Candidate 3

`b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3` on `candidate/unified-task4-successor2-green-b5ed724c-20261016` is **rejected**. Hostile PR #409, run `38956096848`, job `117159222272`, proved a caller could directly construct an advanced `QualificationCampaign` with internally matching fields and bypass the legal lifecycle at exposure and reveal boundaries.

Do not rehabilitate any rejected candidate from earlier green CI.

## Current successor-3 repair

Public campaign fields no longer prove lifecycle provenance. `create_campaign()` issues an opaque process-local lifecycle token; the module stores the exact canonical public-state digest for that token. Every legal transition must match the current registered digest and advances it atomically in the process-local registry. Direct construction has no registered token, while copied-token field mutation has a stale/mismatched digest and fails closed.

This mechanism proves only that a campaign passed through this module's public transition functions in the current process. It is not persistent custody, is not an external trust root, and cannot create authority. A serialized campaign rehydrated in another process has no lifecycle provenance unless a future explicit importer is independently designed and qualified.

Exact mechanically verified code/test head before review-artifact-only edits:

`4d4947af63ba067f2f1f06cb5f80ec1fd5bc67e7`

Read-only Task 4 run `38956553861`, job `117160766667`:

- focused Task 4: `107 passed, 1 skipped`;
- projected 100k replay benchmark: `1 passed`;
- full unified Task 0-4 regression: `298 passed, 1 skipped`.

Same exact head passed:

- Task 2 manifest/access: `38956553918`;
- Task 3 registry: `38956553914`;
- unified synthetic integration: `38956553937`.

Task 1 did not trigger from this lifecycle-only diff; frozen Task 3 ancestry is unchanged.

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
- missing exact sealed-object bindings: `38955121063` / `117155935852`;
- caller-fabricable advanced campaign state: `38956096848` / `117159222272`;
- direct/copy lifecycle provenance forgery: `38956350630` / `117160081568`.

## Required next hostile review

Review the exact newly pinned successor-3 SHA on a separate branch. Retain all prior attack classes and specifically test:

1. stale lawful campaign-object reuse after a later legal transition;
2. copied-token public-state mutation;
3. token leakage through `repr`, `to_payload`, schemas, logs, receipts, or refusal messages;
4. serialized/rehydrated campaign objects claiming lifecycle provenance across processes;
5. exposure/freeze/terminal-accounting ordering around hidden-material reveal;
6. whether hidden material can reveal before every realization has an immutable terminal disposition;
7. exposure-record substitution, output mutation, spent-exposure reset, and post-reveal accounting mutation;
8. all previous trust-root, revocation, sealed-object, replay, and no-echo attacks.

Direct malicious mutation of module-private Python internals is outside the public-API mechanics claim and must not be misrepresented as qualified resistance.

## Acceptance rule

Only an immutable exact SHA may be reviewed. Return explicit `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` with concrete blockers. Even ACCEPT can qualify only non-authorizing Task 4 mechanics; it cannot establish biological truth or grant target, representation, Stage 4, protected-value, or training authority.
