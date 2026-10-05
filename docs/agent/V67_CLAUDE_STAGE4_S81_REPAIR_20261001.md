# V67 Claude Stage-4 S81 repair instruction — 2026-10-01

Read:

`results/v64/V67_CLAUDE_F1DC_STAGE4_INDEPENDENT_AUDIT_V1.json`

## Scope

Repair **S81 only** in the Stage-4 authority/preflight lane.

Do not implement the executor. Do not compute correspondence. Do not change the frozen statistical design.

## Why S81 remains open

The current G18 consumer-schema gate is useful but incomplete. It checks several shapes/counts and the availability vocabulary, yet it does not independently prove all of the semantic invariants previously requested.

Required executable checks:

1. recompute exact `t3_nnz = 6624289`;
2. recompute exact `t4_nnz = 55467544`;
3. recompute the accepted aggregate binding
   `2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52`
   from the eight accepted shard digests using the frozen Phase-B binding algorithm;
4. prove every `pair_gene` resolves against the gene dictionary, not merely that its dtype is string-like;
5. prove every pair interval resolves against the interval dictionary;
6. prove metacell IDs are exactly `0..3230`;
7. prove gene/interval/pair dictionaries and axis conventions agree across **all eight** shards, not only shard s00.

## Mutation / negative tests

Use artifact-level or synthetic-fixture mutations capable of failing the executable check:

- alter one sparse availability bit so T3 nnz changes;
- alter one sparse availability bit so T4 nnz changes;
- alter one shard digest/order so aggregate binding changes;
- replace one pair_gene with a nonexistent gene ID;
- replace one pair_interval with a nonexistent interval identity/index;
- delete/swap a metacell ID;
- make one shard's dictionary disagree with the others.

A mutation that only changes a restated count in the JSON contract is not enough.

## Stop

After repairing S81 and running the negative tests, STOP FOR INDEPENDENT AUDIT.

G16/G17 remain unsatisfied. No executor. Stage 4 NOT AUTHORIZED. Correspondence UNOPENED.
