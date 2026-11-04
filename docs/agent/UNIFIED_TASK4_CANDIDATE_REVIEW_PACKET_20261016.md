# Unified Task 4 successor-4 candidate review packet

Status: `SUCCESSOR4_MECHANICALLY_GREEN__HOSTILE_REVIEW_REQUIRED`

Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Original implementation PR: #404  
External-root repair PR: #406  
Sealed-object binding repair PR: #408  
Lifecycle-provenance repair PR: #410  
Post-reveal accounting RED PR: #413  
Current repair PR: #414  
Current repair branch: `repair/unified-task4-pre-reveal-accounting-20261016`

## Authority boundary

Task 4 V1 is non-authorizing custody mechanics. Repository-constructible trust objects, expected heads, campaign objects, sealed definitions, realization sets, process-local lifecycle tokens, terminal-status records, and review artifacts cannot create biological, target, representation, Stage 4, protected-value, or training authority. Repository replay remains non-authorizing and no genuine external authority root is wired.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated.

## Rejected candidates — permanent history

### Candidate 1

`b31371d62f3270c965d321e61c35898ca6be3721` on `candidate/unified-task4-green-b31371d6-20261016` is **rejected**. Hostile review proved caller-owned signer/verifier/actor/policy/head objects could self-mint the trust graph. Preserved evidence includes run `38953203662`, job `117149477378`, and later caller-trust-root reproduction run `38999372034`, job `117298839947`.

### Candidate 2

`c537db4e7b5b916cb3ddee1872fd4afa623a9b33` on `candidate/unified-task4-successor-green-c537db4e-20261016` is **rejected**. Hostile PR #407, run `38954964212`, job `117155395974`, proved post-seal definition and realization-set substitution.

### Candidate 3

`b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3` on `candidate/unified-task4-successor2-green-b5ed724c-20261016` is **rejected**. Hostile PR #409, run `38956096848`, job `117159222272`, proved a caller could directly construct an advanced `QualificationCampaign` with internally matching fields and bypass the legal lifecycle at exposure and reveal boundaries.

### Candidate 4 / successor-3

`d41720be93db27801fdac1ae62cfd608084dce25` on `candidate/unified-task4-successor3-green-d41720be-20261016` is **rejected**. Hostile PR #413, run `38999531146`, job `117299315140`, proved hidden qualification material could be revealed while terminal accounting was incomplete, after which `EVALUATED`, `TECHNICAL_FAILURE`, `UNSUPPORTED_NOT_ESTIMABLE`, or `DEFECT_INVALIDATED` classifications could be assigned. That allowed hidden truth to influence outcome classification even though method-output bytes had been frozen.

Do not rehabilitate any rejected candidate from earlier GREEN CI.

## Superseded mechanically green pin

`56b864e2b944956746771fb5d26040835d093dd5` is mechanically GREEN and contains the pre-reveal accounting repair, but the first immutable review pin made from that SHA is **superseded for review-artifact inconsistency** because its human and machine review packet still described successor-3. This is not a mechanics rejection. Independent review must use the later exact SHA that contains the corrected packet and state record as well as the same repaired mechanics.

## Current successor-4 repair

The lifecycle now enforces this ordering:

1. create campaign;
2. seal exact challenge definition;
3. seal exact finite realization set;
4. issue committed exposures;
5. freeze method outputs;
6. record an immutable terminal disposition for every exact sealed realization;
7. only then reveal hidden qualification material;
8. verify deterministic regeneration;
9. finalize non-authorizing custody.

`record_exposure_terminal()` is legal only before hidden reveal, in `EXPOSURE_ACTIVE` or `ALL_REQUIRED_OUTPUTS_FROZEN`. `reveal_hidden_material()` refuses unless terminal-accounting keys exactly equal the sealed realization IDs. Once hidden material is revealed, terminal accounting is closed and cannot be rewritten.

Public campaign fields still do not prove lifecycle provenance. `create_campaign()` issues an opaque process-local lifecycle token; the module stores the exact canonical public-state digest for that token. Every legal transition must match the current registered digest and advances it atomically in the process-local registry. Direct construction has no registered token, while copied-token field mutation has a stale/mismatched digest and fails closed.

This mechanism proves only that a campaign passed through this module's public transition functions in the current process. It is not persistent custody, is not an external trust root, and cannot create authority. A serialized campaign rehydrated in another process has no lifecycle provenance unless a future explicit importer is independently designed and qualified.

Exact mechanically verified code/test head before this review-packet correction:

`56b864e2b944956746771fb5d26040835d093dd5`

Read-only Task 4 run `38999855385`, job `117300282006`:

- focused Task 4: `109 passed, 1 skipped`;
- projected 100k replay benchmark: `1 passed`;
- full unified Task 0-4 regression: `300 passed, 1 skipped`.

Same exact head passed:

- Task 2 manifest/access: `38999855298`;
- Task 3 registry: `38999855309`;
- unified synthetic integration: `38999855304`.

Inherited Task 0 workflow-environment failures remain separately classified; frozen Task 0–3 production code is not modified to cosmetically green unrelated environments.

## RED evidence that must remain explainable

- original missing interfaces: `38938697657` / `117100597615`;
- terminal accounting: `38943608912` / `117117078319`;
- schema drift: `38944319232` / `117119472176`;
- incomplete/aliasable C1-C9 law: `38944836349` / `117121219990`;
- unauthenticated signer object: `38945592644` / `117123776998`;
- self-asserted actor/process context: `38946266116` / `117126036930`;
- full caller-self-minted trust graph: `38953203662` / `117149477378`;
- expected-head authority self-mint: `38953623988` / `117150890636`;
- post-seal definition and realization substitution: `38954964212` / `117155395974`;
- missing exact sealed-object bindings: `38955121063` / `117155935852`;
- caller-fabricable advanced campaign state: `38956096848` / `117159222272`;
- direct/copy lifecycle provenance forgery: `38956350630` / `117160081568`;
- post-reveal terminal-accounting mutation: `38999531146` / `117299315140`.

## Required next hostile review

Review only the newly pinned exact successor-4 review-ready SHA on a separate branch. Retain every prior attack class and specifically test:

1. stale lawful campaign-object reuse after a later legal transition;
2. copied-token public-state mutation;
3. token leakage through `repr`, `to_payload`, schemas, logs, receipts, or refusal messages;
4. serialized/rehydrated campaign objects claiming lifecycle provenance across processes;
5. exposure/freeze/terminal-accounting ordering around hidden-material reveal;
6. missing, extra, duplicate, substituted, or rewritten terminal dispositions;
7. whether any terminal disposition can be chosen or changed after hidden material becomes available;
8. whether hidden material can reveal before every exact sealed realization has an immutable terminal disposition;
9. exposure-record substitution, output mutation, spent-exposure reset, and campaign-identity reuse;
10. all previous trust-root, revocation, sealed-object, replay, no-echo, C1-C9, and authority-firewall attacks.

Direct malicious mutation of module-private Python internals is outside the public-API mechanics claim and must not be misrepresented as qualified resistance.

## Acceptance rule

Only an immutable exact SHA containing internally consistent code, tests, attack matrix, review packet, and machine-readable candidate state may be reviewed. Return explicit `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` with concrete blockers and the exact reviewed SHA. Even ACCEPT can qualify only non-authorizing Task 4 mechanics; it cannot establish biological truth or grant target, representation, Stage 4, protected-value, or training authority.
