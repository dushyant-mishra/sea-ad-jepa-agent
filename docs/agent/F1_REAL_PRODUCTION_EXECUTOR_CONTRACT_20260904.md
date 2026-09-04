# F1 Real Production Executor Contract — 2026-09-04

Status: `FROZEN_PRE_RESULT_IMPLEMENTATION_CONTRACT`

This contract governs implementation and synthetic/technical-fixture validation of the contextual-teacher F1 production executor. It does **not** authorize real F1 execution. Production execution must fail closed with `STOP_F1_REAL_RUN_NOT_EXTERNALLY_AUTHORIZED` until a separately reviewed launch authority is supplied and authenticated.

## Frozen scientific and data authorities

The executor must authenticate the following bytes before opening expression:

| Authority | SHA-256 |
|---|---|
| F1 assignments | `12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617` |
| execution dedup map | `3fcd11908723e2cc80db0f5a0f017ad382bd1ed9be522f97081587ae989c2423` |
| matched-null map | `aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6` |
| fit-104 reader split | `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511` |
| FULL104 row lineage | `a6065751667b35a38c5990107c6b3f0177e262f7d145addb24bea24206eeb61b` |
| observation states | `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537` |
| address namespace | `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd` |
| namespace semantic root | `595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f` |
| program weights | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` |
| evidence-mask contract | `d1eefdab177501a00370d71521ae86932e60540fb9f769dfe2b56c7994ca5c5a` |
| u0 checkpoint | `19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4` |
| query-local constructor | `6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa` |
| encoder | `732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a` |
| tokenizer | `2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4` |
| accepted real-forward preflight package root | `52691e1397e91eaedc8417f72623cd176108d8b57d84cd1d2d0b9fe7064b959e` |
| repaired mechanics package root | `37c6e70b982dd300082a2b53a8fe0074c4426b9f571d1f825b8f6ad0d4d5f534` |

The production population is reader-fit only. Reader-validation, reader-oracle, DEV, SEALED, pathology and quarantined/original mixed-NPH expression are forbidden. The model-facing reader return object contains only `normalized_values` and `observation_states`; identity and provenance remain sidecars.

## Modes and launch guard

The CLI has three explicit, mutually exclusive modes: `synthetic`, `technical-fixture`, and `production`. There is no row-limit option that can turn production into a partial scientific run.

`production` requires a separate external JSON launch authority. The executor must authenticate its schema, exact executor and contract byte hashes, Git commit, frozen authority roots, intended output root and an exact boolean `real_f1_execution_authorized: true`. Missing, malformed, stale, mismatched, truthy-non-boolean, environment-variable-only, or self-created authority must stop before expression with `STOP_F1_REAL_RUN_NOT_EXTERNALLY_AUTHORIZED`. This implementation task must not create such an authority.

## Exact topology

- recipient cells: 2,781
- inferential assignments: 44,496
- unique `(cell,q)` teacher computations: 43,108
- computational deduplications only: 1,388
- teacher forwards: 43,108
- correct-student forwards: 215,540
- matched-null-student forwards: 215,540
- total expensive forwards: 474,188
- assignment×evidence effect rows: 222,480
- logical donor×operator shards: 1,400

Deduplication is computational only. Every assignment remains in every inferential estimator with its frozen replicate, program, cell-within-donor and donor hierarchy. No post-dedup query weight is permitted.

## Execution and semantics

Execution is block-major over authenticated FULL104 materialized CSR blocks, with hash verification before use and exactly-once normalization `float32 log1p(raw_count * (10000/source_library))`. Whole-corpus densification is forbidden. Physical reads may be cached only under authenticated block identity; outputs are restored to canonical logical order.

For each unique `(recipient,q)`, the teacher uses the recipient's lawful rich evidence with query self-ablated. For each assignment and evidence level, correct student input uses the recipient; matched-null student input uses the frozen donor/operator-matched null source while retaining recipient/query semantics. QID-v2 is distinct: at 60% evidence it compares the own query with the prospectively frozen cyclic wrong-query mapping over the cell's sorted unique queries. It is not the matched-null comparison.

Each effect row contains only the four frozen endpoint values: `A`, `direct_delta`, `qid_margin`, and `qid_win`, plus immutable assignment/provenance identifiers. `A` is correct-minus-null contextual cosine. `direct_delta` is contextual effect minus direct effect. QID margin is own-minus-wrong cosine; win is 1, 0.5 or 0.

## Cache identity

Every cache key binds the authenticated model/checkpoint, constructor/semantic snapshot, role, recipient, query, evidence level, physical/evidence-mask identity, input-source cell, null-map authority, assignment/dedup authority, dtype and autocast. Teacher reuse is lawful only when every teacher identity field matches. Correct, matched-null and QID-wrong student forwards are role-separated and can never collide. Recipient and null-source identity cannot be interchanged.

## Shards, resume and finalization

Logical membership is the frozen donor×operator partition. Physical subdivision may be used for bounded files but must preserve logical membership and ordered record IDs. Every shard is written staging-first, fsynced, atomically renamed, and contains identity plus a semantic payload SHA-256 recomputed at load. Resume accepts only complete shards whose authority, implementation fingerprint, membership, order, dtype and scientific payload hashes all match. Corrupt, partial, duplicate, foreign-fingerprint or mixed-version shards stop; they are never silently repaired or counted complete.

Finalization independently reconciles exact assignment/effect/forward/cache/shard multiplicities and rejects missing, duplicate or extra rows. Progress telemetry is outcome-blind and limited to counts, identifiers/hashes, timing, resource use and failure codes; no cosine, effect, endpoint, program outcome, threshold result or scientific selection is displayed during execution.

## Implementation promotion gates

Before any real launch: implementer tests must pass; exactly one fresh `MANDATORY_IMPLEMENTATION_VERIFIER_V1` must independently reconstruct conclusion-bearing mechanics and defeat all required mutations; the independent production validator must derive its conclusions from raw artifacts; a bounded end-to-end technical-fixture dry run must exercise read, teacher/correct/null/QID forwards, caching, shard interruption/resume and final reconciliation; and scoped specialist/Red-Team review must pass. All code and package bytes must be hash-bound.

Real F1 remains forbidden by this contract. Successful completion of this implementation phase ends at `PASS_F1_REAL_PRODUCTION_EXECUTOR_IMPLEMENTATION_AWAITING_EXTERNAL_REVIEW`.
