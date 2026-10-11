# TD PR #267 concurrent-attempt custody audit — 2026-10-11

Status: `PR267_BLOCKED__DO_NOT_QUALIFY__DO_NOT_EXECUTE`

Audited candidate:
- PR #267
- branch `fix/td-g7-counterpart-auth-immutable-attempt-20261011`
- exact head `16f05bd3845565bb2c24d70143d447d7ef2b8904`

## Finding

The G7 attempt-custody primitive is not atomic.

At the audited head, `begin_g7_attempt()` performs:
1. `out.exists() or marker.exists()`;
2. later, ordinary `marker.write_text(...)`.

Two concurrent starters can both observe the marker as absent before either write occurs, then both write the same marker and both proceed as successful starters. This violates the intended invariant that one logical G7 execution identity is spent exactly once.

## Reproduction

A deterministic concurrency regression synchronized two starters after the existence checks and before the marker write. Against the exact PR #267 algorithm the regression produced:

`2 successful starters / 0 rejected starters`

Expected custody behavior is:

`1 successful starter / 1 rejected starter`

The regression was committed test-first on successor PR #268:
- branch `fix/td-g7-atomic-attempt-create-20261011`
- RED commit `d8fa3024e06e265b77353c8382453e7ccbf2350f`
- test: `test_g7_attempt_concurrent_start_has_exactly_one_winner`

## Consequence

PR #267 must not be canonically qualified. Its existing sequential retry tests are insufficient to establish immutable single-spend semantics.

This finding does not affect accepted PR #259 G4/G5 evidence and does not authorize any value read.

No G6 or G7 was executed. No runtime value authorization was created. No corrected expression/count arrays were opened. No corrected biological replay, target selection, TD60, Stage 4, or training occurred.

## Required bounded repair

The successor must make marker creation an atomic exclusive-create operation so exactly one concurrent starter can create the marker. A pre-existing marker must reject the loser as already spent. The marker remains permanent on both failure and success.

The repair must preserve:
- physical-H5-before-S174-count-loader ordering;
- same-authority G6 PASS requirement;
- exact PR #259 receipt binding;
- all existing biological replay / target selection / TD60 / training false gates.

No G6/common/scientific-statistic behavior may change.

After the atomic repair is implemented, the successor—not PR #267—must undergo canonical engineering/custody qualification before any later authority decision.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
