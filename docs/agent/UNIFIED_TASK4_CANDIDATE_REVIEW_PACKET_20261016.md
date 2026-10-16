# Unified Task 4 successor candidate review packet

Status: `SUCCESSOR_CANDIDATE_ONLY__INDEPENDENT_EXACT_HEAD_REVIEW_REQUIRED`

Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Original implementation PR: #404  
Successor repair PR: #406  
Successor repair branch: `repair/unified-task4-external-root-boundary-20261016`

## Authority boundary

Task 4 V1 now makes a narrower claim than the rejected predecessor: repository-constructible custody is **mechanics only**. A Python signer, verifier, actor registry/policy, actor-attestation verifier, head publisher, or caller-supplied expected head cannot establish that its trust root is genuinely external. Therefore repository replay is always non-authorizing. `expected_head` is an integrity/consistency check only.

No biological PASS/FAIL, target selection, representation selection, Stage 4, protected-value, or training authority is created. Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated.

## Rejected predecessor — preserve this history

The first pinned candidate was:

- branch `candidate/unified-task4-green-b31371d6-20261016`;
- exact SHA `b31371d62f3270c965d321e61c35898ca6be3721`.

It is **rejected**, despite its earlier green CI. Hostile review PR #405 constructed the entire trust graph from caller-owned objects. Run `38953203662`, job `117149477378`, failed with `DID NOT RAISE Task4CustodyError`: caller-owned signer, verifier, actor verifier, actor registry/policy, and head publisher could manufacture custody accepted as authoritative.

A follow-up semantic RED on the successor repair branch, run `38953623988`, job `117150890636`, showed the underlying authority bug directly: caller-owned trust inputs and a caller-supplied expected head produced `replay().authoritative == True`.

Do not rehabilitate `b31371d6...` based on its earlier green runs.

## Successor repair

The repair changes the authority law rather than pretending repository code can authenticate an external root:

- custody event chaining, signatures, actor-action checks, durable revocation, head publication mechanics, replay equivalence, and scale remain testable;
- `expected_head` remains exact-match integrity evidence;
- append no longer self-mints a new expected head;
- `CustodyReplayResult.authoritative` is always `False` in repository Task 4 V1;
- genuine external authority remains unwired and fail-closed;
- C1/C5-C9 authority cannot become GREEN from repository-constructible objects.

Last fully verified successor code/test head before review-artifact-only edits:

`ba3e521ff58ce8ad65f49d9fa0930871991a96de`

Fresh read-only Task 4 run `38954292188`, job `117153130016`:

- focused Task 4: `99 passed, 1 skipped`;
- projected 100k replay benchmark: `1 passed`;
- full unified Task 0-4 regression: `290 passed, 1 skipped`.

Same-head regressions:

- Task 2 manifest/access: `38954292154` PASS;
- Task 3 registry: `38954292151` PASS;
- unified synthetic integration: `38954292464` PASS.

Task 1 was not triggered by this successor diff; its frozen Task 3 base is unchanged.

## Read first

1. `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`
2. `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`
3. `docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md`
4. `results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json`
5. `results/target_discovery/unified_qualification_v1/TASK4_ATTACK_MATRIX_V1.json`
6. `tests/v5/td_unified/test_task4_external_root_boundary_v1.py`
7. Task 4 production modules and strict Task 4 schemas/tests.

## RED evidence that must remain explainable

- original missing interfaces: `38938697657` / `117100597615`;
- terminal accounting: `38943608912` / `117117078319`;
- schema drift: `38944319232` / `117119472176`;
- incomplete/aliasable C1-C9 law: `38944836349` / `117121219990`;
- unauthenticated signer object: `38945592644` / `117123776998`;
- self-asserted actor/process context: `38946266116` / `117126036930`;
- full caller-self-minted trust graph: `38953203662` / `117149477378`;
- expected-head authority self-mint: `38953623988` / `117150890636`.

## Inherited CI defects outside Task 4

Some frozen Task 0 / Task 3 read-only workflows have historically failed before their intended assertions because their environments omit NumPy. Do not infer Task 4 authority from those failures, and do not silently rewrite frozen Task 0-3 workflow authority in this review.

## Required hostile review questions

Reject the successor if any answer is YES:

1. Can any repository-constructible signer/verifier/actor/policy/publisher/expected-head object graph make `replay().authoritative` true?
2. Can cosmetic stage/status/restriction mutation, restart, truncation, or rechain erase persistent revocation?
3. Can any Task 4 route regain authority through `registry_v1_legacy`, stale readiness diagnostics, or hand-constructed registry/status objects?
4. Can C5-C9 become GREEN without genuine external evidence for actor credentials, privileged-policy currency, requirement/construction law, and process isolation?
5. Can exposure crash/rerun/rename reset spent exposure?
6. Can hidden material reveal before required outputs freeze, or mutate after freeze?
7. Can missing/unsupported/technical-failure realizations disappear from terminal accounting or be favorably zero-filled?
8. Can logs/artifacts/receipts/refusal messages leak hidden material or echo attacker secrets?
9. Can reference and optimized replay disagree, or can 10k/100k replay violate committed mechanics semantics?
10. Did the successor modify frozen Task 0-3 production code or create biological/target/representation/training/Stage4 authority?

## Acceptance rule

Pin the exact successor candidate SHA named in the PR conversation. Run or independently reproduce the hostile suites on a separate review branch. Return explicit `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` with concrete blockers.

Even ACCEPT means only that the **non-authorizing Task 4 custody mechanics** are accepted. External authority remains a separate future integration problem and cannot be inferred from an ACCEPT verdict here.
