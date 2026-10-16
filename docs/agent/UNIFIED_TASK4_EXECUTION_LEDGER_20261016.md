# Unified Task 4 execution ledger

Plan: `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`  
Binding amendment: `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`  
Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Original implementation PR: #404, `work/unified-task4-impl-20261016`  
Successor repair PR: #406, `repair/unified-task4-external-root-boundary-20261016`  
RED PR: #403, `work/unified-task4-red-20261016`  
Mode: native execution, RED-first.

## Authority boundary

Task 4 remains custody/mechanics only. It grants no biological PASS/FAIL, target winner, representation winner, Stage 4 authority, protected-value authority, or training authority. Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated in this implementation lane.

The successor law is stricter: repository-constructible custody cannot become authoritative. A caller-supplied signer/verifier/actor registry/policy/actor verifier/head publisher/expected head can exercise qualified mechanics, but repository code cannot prove those objects originate from a genuinely independent trust root. `expected_head` is integrity evidence only and `CustodyReplayResult.authoritative` remains `False` in Task 4 V1.

## Preserved RED

The first valid Task 4 RED is GitHub Actions run `38938697657`, job `117100597615`, on PR #403. The token had `Contents: read`; the focused suite produced 14 intentional failures at not-yet-existing Task 4 interfaces. An earlier collection/glob defect was corrected before accepting this RED.

Subsequent RED-first repairs preserved:

- terminal-accounting gap: `38943608912` / `117117078319`;
- campaign schema drift: `38944319232` / `117119472176`;
- incomplete/aliasable C1-C9 law: `38944836349` / `117121219990`;
- signer object without actor-action attestation: `38945592644` / `117123776998`;
- self-asserted actor/process context: `38946266116` / `117126036930`;
- full caller-self-minted trust graph: `38953203662` / `117149477378`;
- caller expected-head authority self-mint: `38953623988` / `117150890636`.

The last two attacks rejected the previously pinned candidate `b31371d62f3270c965d321e61c35898ca6be3721`. Earlier green CI for that SHA does not override the hostile failure.

Each repair remained prospective Task 4 code/tests/schemas/docs. Frozen Task 0-3 production modules were not modified.

## Implemented mechanics laws

Task 4 provides:

- current-`registry_v1` adapter and legacy-registry import firewall;
- canonical defect-bearing revocation identities that ignore cosmetic stage/status/restriction changes;
- persistent append-only cross-process event custody, exact head consistency checking, stale-head refusal, truncation/rechain refusal, and replay mutation tests;
- actor-action attestations for privileged append, bound to exact event subject and sequence;
- closed requirement-class and issuer law;
- closed exact C1-C9/R5 preauthority vocabulary;
- refusal of caller mappings as proof of C5-C9 actor credentials, policy currency, construction law, or process isolation;
- finite sealed challenge lifecycle with exposure spend at issuance, canonical method identity, immutable output freeze, reveal-after-freeze only, regeneration verification, and explicit terminal accounting;
- strict schemas for campaign, custody, exposure, output-freeze, reveal, and evidence objects;
- NO-ECHO publication/secret scanning;
- reference/optimized replay equivalence, 10k mechanics replay, and dedicated 100k mechanics benchmark.

The predecessor implementation treated configured signer/head interfaces plus an expected head as enough to set `authoritative=True`. Hostile review proved those interfaces were caller-mintable. The successor therefore separates replay integrity from authority and removes the self-minted expected-head promotion path.

## Successor verification

Exact successor code/test head before review-artifact-only edits:

`ba3e521ff58ce8ad65f49d9fa0930871991a96de`

Read-only Task 4 run `38954292188`, job `117153130016`:

- focused Task 4 suites: `99 passed, 1 skipped`;
- projected 100k replay benchmark: `1 passed`;
- full unified Task 0-4 regression: `290 passed, 1 skipped`.

Same-head regressions:

- Task 2 manifest/access: `38954292154` PASS;
- Task 3 registry: `38954292151` PASS;
- unified synthetic integration: `38954292464` PASS.

Task 1 did not trigger from the successor diff; frozen Task 3 ancestry is unchanged.

Inherited Task 0 / Task 3 read-only workflows have separately exhibited a pre-existing missing-NumPy setup failure before their intended assertions. This repair does not rewrite those frozen workflows and does not treat those environment failures as positive or negative Task 4 authority evidence.

## Current readiness classification

The predecessor candidate is rejected. The successor is mechanically GREEN at `ba3e521f...` and is being repackaged for an immutable exact-head independent hostile review.

It is **not accepted authority**. Repository Task 4 V1 deliberately has no route to external authority. FINAL C5-C9 context remains unwired/fail-closed. Independent acceptance can qualify only these non-authorizing custody mechanics; it cannot select a target, representation, authorize training or Stage 4, or establish biological truth.
