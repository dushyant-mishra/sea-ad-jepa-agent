# Unified Task 4 execution ledger

Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Original implementation PR: #404  
Trust-root repair PR: #406  
Sealed-object binding repair PR: #408  
Lifecycle-provenance repair PR: #410  
Pre-reveal terminal-accounting repair PR: #414  
Mode: native execution, RED-first.

## Authority boundary

Task 4 remains custody/mechanics only. It grants no biological PASS/FAIL, target winner, representation winner, Stage 4 authority, protected-value authority, or training authority. Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Repository-constructible custody remains non-authorizing. `expected_head` is an integrity check only. Process-local lifecycle provenance is mechanics only. No genuine external authority root is wired. No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated.

## Preserved rejection history

Candidate 1, `b31371d62f3270c965d321e61c35898ca6be3721`, is rejected. PR #405 (`38953203662` / `117149477378`) proved caller self-minting of the injected trust graph; follow-up RED `38953623988` / `117150890636` proved caller inputs could create authoritative replay.

Candidate 2, `c537db4e7b5b916cb3ddee1872fd4afa623a9b33`, is rejected. PR #407 (`38954964212` / `117155395974`) proved post-seal definition and realization-set substitution.

Candidate 3, `b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3`, is rejected. PR #409 (`38956096848` / `117159222272`) proved direct construction of advanced `QualificationCampaign` state could bypass lawful exposure and reveal transitions. Repair RED `38956350630` / `117160081568` additionally demonstrated both direct construction and copied-state mutation before the lifecycle-provenance fix.

Candidate 4 / successor-3, `d41720be93db27801fdac1ae62cfd608084dce25`, is rejected. PR #413 (`38999531146` / `117299315140`) proved hidden material could be revealed before terminal exposure classifications were frozen, allowing terminal disposition to be chosen after hidden truth became available.

The mechanically green pin `56b864e2b944956746771fb5d26040835d093dd5` is not a mechanics rejection; it is superseded only because its first immutable review pin carried stale successor-3 review artifacts. Earlier green CI for any rejected or superseded SHA is not acceptance evidence.

## Current repair law

Task 4 now enforces four separate mechanics boundaries:

- repository custody replay is integrity-only and never establishes external authority;
- campaign state binds the exact sealed definition SHA and exact realization-set root;
- public campaign fields are not lifecycle provenance;
- terminal exposure accounting is complete and immutable before hidden qualification material can be revealed.

`create_campaign()` issues an opaque process-local token and registers the canonical public-state digest. Each public legal transition verifies the exact current token/digest pair and advances the registered digest. Directly constructed advanced campaign objects have no registered provenance; copied-token objects whose public state was mutated have a mismatched digest and fail closed.

`record_exposure_terminal()` is legal only before hidden reveal, while the campaign is in `EXPOSURE_ACTIVE` or `ALL_REQUIRED_OUTPUTS_FROZEN`. `reveal_hidden_material()` requires terminal-status keys to equal the exact sealed realization IDs. After reveal, terminal accounting is closed. This prevents hidden truth from influencing whether an exposure is labeled evaluated, technical failure, unsupported/not estimable, or defect-invalidated.

The lifecycle registry remains process-local by design. It is excluded from serialized campaign payloads, does not survive process boundaries, and is not a substitute for persistent custody or an external trust root. No cross-process lifecycle restoration/importer is authorized by Task 4 V1.

Other mechanics laws remain: persistent revocation, actor-action binding, closed C1-C9/R5 vocabulary, exposure spent at issuance, immutable output freeze, exact sealed-object binding, strict schemas, no-echo checks, and reference/optimized replay qualification.

## Preserved RED sequence

- initial missing interfaces: `38938697657` / `117100597615`;
- terminal accounting: `38943608912` / `117117078319`;
- schema drift: `38944319232` / `117119472176`;
- C1-C9 vocabulary: `38944836349` / `117121219990`;
- actor-action signer binding: `38945592644` / `117123776998`;
- self-asserted authority context: `38946266116` / `117126036930`;
- caller-self-minted full trust graph: `38953203662` / `117149477378`;
- expected-head authority self-mint: `38953623988` / `117150890636`;
- post-seal definition/realization substitution: `38954964212` / `117155395974`;
- missing exact sealed-object bindings: `38955121063` / `117155935852`;
- caller-fabricable advanced campaign state: `38956096848` / `117159222272`;
- lifecycle provenance direct/copy forgery: `38956350630` / `117160081568`;
- post-reveal terminal-accounting mutation: `38999531146` / `117299315140`.

## Current verification

Exact repaired mechanics head before review-artifact consistency edits:

`56b864e2b944956746771fb5d26040835d093dd5`

Task 4 run `38999855385`, job `117300282006`, with read-only `Contents: read` token:

- focused Task 4: `109 passed, 1 skipped`;
- projected 100k replay: `1 passed`;
- full unified regression: `300 passed, 1 skipped`.

Same exact head passed:

- Task 2 `38999855298`;
- Task 3 registry `38999855309`;
- unified synthetic integration `38999855304`.

The later review-artifact-only head must pass the same Task 4 consistency suite before immutable review pinning. Inherited Task 0 environment failures remain separately classified and frozen Task 0–3 production code is not changed to cosmetically green them.

## Current readiness classification

Successor-4 mechanics are GREEN, but independent hostile acceptance is still required. Review artifacts must preserve all four rejections and the pre-reveal terminal-accounting law before a review-ready immutable SHA is pinned.

FINAL external authority and C5-C9 context remain unwired/fail-closed. Independent acceptance can qualify only these non-authorizing mechanics and cannot establish biological truth or authorize target/representation selection, training, or Stage 4.
