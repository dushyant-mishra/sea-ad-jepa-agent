# Unified Task 4 execution ledger

Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Original implementation PR: #404  
Trust-root repair PR: #406  
Sealed-object binding repair PR: #408  
Mode: native execution, RED-first.

## Authority boundary

Task 4 remains custody/mechanics only. It grants no biological PASS/FAIL, target winner, representation winner, Stage 4 authority, protected-value authority, or training authority. Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Repository-constructible custody remains non-authorizing. `expected_head` is an integrity check only. No genuine external authority root is wired. No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated.

## Preserved rejection history

The first pinned candidate, `b31371d62f3270c965d321e61c35898ca6be3721`, is rejected. Hostile PR #405 (`38953203662` / `117149477378`) showed that a caller could self-mint the injected trust graph; semantic RED `38953623988` / `117150890636` showed that caller-owned trust inputs plus a caller expected head could create `authoritative=True`.

The second pinned candidate, `c537db4e7b5b916cb3ddee1872fd4afa623a9b33`, is rejected. Hostile PR #407 (`38954964212` / `117155395974`) showed that post-seal challenge definitions and realization sets could be substituted by hand-constructed objects sharing the campaign identity.

Earlier green CI for either rejected SHA is not acceptance evidence.

## Current repair law

Task 4 now binds:

- the exact sealed challenge-definition SHA-256 into campaign state;
- the exact sealed realization-set root into campaign state;
- realization-set roots to the exact campaign identity, committed definition SHA, realization IDs, content hashes, challenge classes, and budget;
- every downstream exposure/reveal/regeneration/finalization transition to those exact bindings.

A realization object whose fields do not recompute to its claimed root is refused. A definition or realization set from another post-seal construction is refused even if it shares the campaign identity.

The rest of the mechanics laws remain: persistent revocation, actor-action binding, closed C1-C9/R5 vocabulary, exposure spent at issuance, immutable output freeze, reveal-after-freeze, explicit terminal accounting, strict schemas, no-echo checks, and reference/optimized replay qualification.

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
- missing exact sealed-object bindings: `38955121063` / `117155935852`.

## Current verification

Exact code/schema head before review-artifact-only edits:

`89fb48d581ba37bce9496854d039d900535d47c8`

Task 4 run `38955545446`, job `117157367488`, with read-only `Contents: read` token:

- focused Task 4: `104 passed, 1 skipped`;
- projected 100k replay: `1 passed`;
- full unified regression: `295 passed, 1 skipped`.

Same-head regressions all passed:

- Task 1 `38955545469`;
- Task 2 `38955545455`;
- Task 3 `38955545397`;
- unified synthetic integration `38955545761`.

## Current readiness classification

Mechanically GREEN, not accepted. Review artifacts are being rebound to the second rejection before a new immutable candidate is pinned. After pinning, hostile review must specifically test direct caller construction of advanced `QualificationCampaign` state in addition to all previous attacks.

FINAL external authority and C5-C9 context remain unwired/fail-closed. Independent acceptance can qualify only these non-authorizing mechanics and cannot establish biological truth or authorize target/representation selection, training, or Stage 4.
