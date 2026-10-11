# JEPA Macha operator handoff — 2026-10-11

Status: `CURRENT_MACHA_COORDINATION_HANDOFF__NO_VALUE_AUTHORITY`

This document lets a new coordinator manage Macha as the canonical-machine execution worker without relying on chat history.

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Roles

The coordinator owns scientific adjudication, authority boundaries, prospective-freeze interpretation, Macha instructions, independent audit of every return, and synchronization of PR #247 / PR #251.

Macha may create clean worktrees at exact approved heads, run exact qualification/execution commands, collect hashes/logs/receipts, open evidence-only draft PRs and report failures exactly. Macha may not infer authority from PASS, mergeability, file access or prior instructions.

Never give Macha a generic `continue`; every instruction must bind an exact branch/head, allowed actions, forbidden actions, evidence requirements and STOP condition.

## 2. Accepted target-discovery evidence

Accepted value-blind corrected-substrate execution remains PR #259:
- execution head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- executed code `bf253a4dd62d943398f9ff59ed8b1e74777140a5`
- driver physical SHA `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping physical SHA `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Interpretation remains narrow: G4/G5 technical/data-integrity PASS only. No corrected expression/count arrays were opened; G6/G7 were not run; no value-read authorization exists; no corrected biological replay occurred.

## 3. PR #267 is blocked

PR #267:
- branch `fix/td-g7-counterpart-auth-immutable-attempt-20261011`
- exact head `16f05bd3845565bb2c24d70143d447d7ef2b8904`
- status `BLOCKED_CONCURRENT_ATTEMPT_RACE__DO_NOT_QUALIFY__DO_NOT_EXECUTE`

Controlling audit:
`docs/agent/TD_PR267_CONCURRENT_ATTEMPT_CUSTODY_AUDIT_20261011.md`

The defect is a TOCTOU race in `begin_g7_attempt()`: existence is checked before an ordinary marker write, so two concurrent starters can both succeed. A deterministic regression produced two successful starters for one logical identity.

Do not send the old `MACHA_NEXT_INSTRUCTION_PR267_20261011.md`; it is historical/superseded instruction evidence.

## 4. Current engineering successor — PR #268

Current successor:
- PR #268
- branch `fix/td-g7-atomic-attempt-create-20261011`
- starting RED head `d8fa3024e06e265b77353c8382453e7ccbf2350f`
- status `RED_TEST_COMMITTED__PRODUCTION_REPAIR_PENDING__DO_NOT_EXECUTE_G6_G7`

The RED commit changes only `tests/v5/test_td_g7_counterpart_attempt_custody.py` and adds:
`test_g7_attempt_concurrent_start_has_exactly_one_winner`.

The current ready-to-send Macha instruction is:
`docs/agent/MACHA_NEXT_INSTRUCTION_PR268_ATOMIC_CUSTODY_20261011.md`

Current assignment:
`REPAIR_PR268_ATOMIC_ATTEMPT_CUSTODY__QUALIFY_SUCCESSOR__THEN_STOP_AT_VALUE_AUTHORITY_BOUNDARY`

Routine engineering progression does not require an owner checkpoint. The next true authority boundary is value reading.

## 5. What Macha must do now

Macha must:
1. pin exact RED head `d8fa3024e06e265b77353c8382453e7ccbf2350f` in a clean worktree;
2. reproduce/preserve the expected failing concurrency test;
3. make the smallest production repair: atomic exclusive marker creation with exactly one concurrent winner;
4. preserve existing marker schema, permanent marker semantics, final-receipt rejection and all false authority flags;
5. change no G6/common/scientific-statistic behavior;
6. run the full focused common/G6/G7/custody suite;
7. verify exact PR #259 receipt hashes;
8. run the real-receipt compatibility test with exactly `1 passed / 0 skipped / 0 failed`;
9. preserve complete RED/GREEN/environment/scope evidence on PR #268;
10. STOP at the value-read authority boundary.

## 6. Forbidden during PR #268 repair/qualification

Macha must not:
- create `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2`;
- create an owner-decision record;
- run G6;
- run G7;
- open corrected expression/count arrays through the target-discovery value path;
- run corrected TD56/TD57B/TD57C/TD59/TD60;
- select a target or representation winner;
- authorize Stage 4;
- train.

## 7. Coordinator audit after Macha returns

For every Macha return:
1. verify exact branch/head before conclusions;
2. inspect committed receipts/logs rather than prose;
3. verify exact hashes, schemas, test counts and scope;
4. verify no forbidden downstream operation occurred;
5. state only the narrowest supported conclusion;
6. update PR #247 and PR #251;
7. issue the next exact instruction only if it remains below an authority boundary.

If PR #268 repair or qualification fails, preserve the exact failure and diagnose prospectively. Do not silently patch in a qualification worktree and do not weaken a gate.

## 8. Value-read authority remains separate

Even a fully qualified PR #268 will not authorize value reading.

Before any G6/G7 execution, the owner must explicitly authorize:
`AUTHORIZE_G6_G7_INTEGRITY_ONLY`

That decision must be preserved immutably and cryptographically bound into a future runtime authorization together with exact PR #259 physical receipt hashes and the exact qualified implementation identity.

A later G6/G7 PASS would establish only value integrity/corroboration, not corrected biological recurrence.

## 9. Corrected biological replay remains separately authorized

A second explicit owner authorization is required before corrected TD56/TD57B/TD57C/TD59 replay.

Replay remains prospectively frozen. Macha must not improvise panels, donor splits, nulls, thresholds, locality fractions, address universe or stage interpretation. TD57C historical FAIL remains immutable. TD59 original executor bytes remain unrecovered; only the separately validated replay-closure successor is admissible.

## 10. Bayesian lane remains separate

PR #249 remains:
- `SAMPLER_NOT_ESTIMABLE`
- `STOP_THIS_BAYESIAN_FORMULATION__DO_NOT_TUNE_TO_HISTORICAL_OUTCOMES`

Do not revive/tune that Bayesian formulation to force a historical result. No Bayesian PASS, sampler recovery or posterior result grants target-discovery value-read, replay, target-selection or training authority.

## 11. Current instruction pointer

Current instruction:
`docs/agent/MACHA_NEXT_INSTRUCTION_PR268_ATOMIC_CUSTODY_20261011.md`

Current next gate:
**atomic PR #268 repair + canonical engineering/custody qualification, then STOP at explicit value-read authorization.**
