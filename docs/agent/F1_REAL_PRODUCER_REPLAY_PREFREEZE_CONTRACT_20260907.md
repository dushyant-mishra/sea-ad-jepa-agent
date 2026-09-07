# F1-A Real Producer / Replay Pre-Freeze Contract — 2026-09-07

Terminal: `PRODUCER_AND_REPLAY_SOURCE_FROZEN__REAL_F1_STILL_UNAUTHORIZED`

Branch `f1-real-producer-replay-prefreeze-20260907`, from the reviewed preflight
state `f1-real-reader-forward-preflight-20260903` at
`14e41030ffac65b3d58a45ae4159d30b8517e470`.

Source-only. No real sweep was executed. No reader-validation, reader-oracle,
DEV, SEALED, foundation sealed-holdout or pathology asset was opened. No F1-A
scientific rule was changed. The sealed-holdout registry branch and the frozen
F1-B attack authority were not touched.

## What this freezes

Two implementations and their behavioural test suite, so their bytes are fixed
*before* any real output exists:

| role | path |
|---|---|
| primary production producer | `scripts/v4/f1_real_producer_v1.py` |
| independent replay | `scripts/v4/f1_real_replay_v1.py` |
| behavioural parity and attacks | `tests/test_f1_real_producer_replay_parity_v1.py` |

Exact SHA-256 values are recorded in
`outputs/f1_real_producer_replay_prefreeze_20260907/F1_PREFREEZE_MANIFEST.csv`
and are regenerated as the last step of packaging, so a stale digest cannot be
recorded for a file that changed afterwards.

## Authority binding

The producer re-verifies all seven frozen preflight authorities against bytes on
disk before planning, and fails closed on any missing or mismatched digest:

```
F1_QUERY_ASSIGNMENTS_2DRAW.csv        12fd5f15…
F1_QUERY_EXECUTION_DEDUP_MAP.csv      3fcd1190…
F1_MATCHED_NULL_PRIMARY_MAP.csv       aba31aea…
t1_checkpoint_u0000.pt                19fb0c25…
src/sea_ad_jepa/v4/ipb_jepa.py        732ea46f…
src/sea_ad_jepa/v4/gene_tokenizer.py  2a2ba7f4…
contextual_query_local.py             6bd641cd…
```

Accepted real-forward root `007bc6f182354a133a2ec49ce0ef5966831d4995a0a2a5f004bb845772469ad3`.
Accepted mechanics are fixed and retuning is forbidden: forward batch 4, reader
block 4, workers 4, prefetch 4, pinned memory off, float32, no autocast,
`torch.no_grad`, encoder eval, no gradient checkpointing.

Lawful partition is `reader_fit` only. `assert_lawful_partition` rejects
`reader_validation`, `reader_oracle`, `development`, `sealed_holdout` and
`whole_study_external_holdout`, and also rejects any partition it does not
recognise rather than ignoring it.

## Hard geometry assertions

The producer asserts the acceptance-contract constants and their internal
reconciliations:

```
statistical assignments            44,496
unique (cell,q)                    43,108
compute-only dedups                 1,388
teacher forwards                   43,108
correct-student forwards          215,540
matched-null-student forwards     215,540
total expensive forwards          474,188
assignment × evidence rows        222,480
logical donor×operator shards       1,400
```

## Why the replay is genuinely independent

Agreement between a producer and a replay is only evidence if neither can borrow
the other's arithmetic. Therefore:

- the producer **asserts** the frozen constants; the replay **derives** the same
  counts by counting rows and distinct `(cell,q)` pairs in the frozen CSVs. The
  suite confirms 44,496 / 43,108 / 222,480 / 474,188 from the data, not from a
  restated constant;
- identity digests, the identity root, the payload digest, the physical shard
  mapping, cosine, QID and the effect row are each reimplemented in the replay
  from the contract wording;
- cosine is deliberately associated differently — normalise then dot, rather
  than dot divided by the norm product. The two are algebraically identical, so
  parity is asserted to a declared float64 tolerance
  (`PARITY_ULP_MULTIPLIER = 256`) rather than to bit equality. `qid_win` is
  compared exactly, since it is a discrete score;
- the replay refuses to run as a CLI if the producer or the shared preflight
  executor has been imported into its process, and a test proves that guard
  fires rather than assuming it;
- two AST tests assert neither source imports the other.

The parity comparator is itself guarded: a test perturbs a producer value by
`1e-6` and requires the comparison to fail, so a comparator that accepted
everything could not pass.

## Attacks that must fail closed

Covered behaviourally in the suite: duplicate shard write; wrong dtype at commit
and at load; stale membership root; wrong forward root; wrong shard id;
reordered payload; teacher identity that is not evidence-invariant;
correct/null identity collision; identity failing to separate query, recipient,
evidence level or matched-null source; identity reusable across a different
bound forward root; geometry disagreement between asserted and derived counts;
forbidden partition; execution without authorization; and any caller parameter
attempting to relax the execution gate.

Interrupted and resumed execution is exercised directly: a run is interrupted
after two of three shards, resumed, and required to reproduce identical ordered
payload digests and an identical identity root, while reusing already-committed
shards rather than rewriting them.

## Execution gate

`REAL_EXECUTION_READY` is `False` and all three real output roots are `None`, so
`run_production_sweep` raises `STOP_F1_REAL_PRODUCER_EXECUTION_NOT_AUTHORIZED`.
The gate is checked before any argument is inspected, and there is no parameter
that relaxes it — a test passes `real_execution_ready=True, force=True` and
still requires the STOP.

Real output hashes are deliberately **not** populated here. They may only be
bound by the data-only closure step in
`F1_DATA_ONLY_CLOSURE_DESIGN_20260907.md`, never by editing this source after
outcomes exist.

## Repairs made during this work, recorded rather than hidden

An earlier draft built the shard filename directly from donor and operator with
a `::` separator, which is an illegal Windows filename character and broke three
tests. The reviewed acceptance validator had already solved this by hashing the
logical id into `shard_<sha256>`. The producer now binds
`physical_shard_id` from that validator and keeps the logical
`(donor_id, operator_index)` pair as canonical compact JSON, which is an identity
and never a filename. This is recorded because inventing an encoding over a
solved problem is the error, not the broken separator.

An earlier draft of the replay selected the operator column by substring match.
It now requires the exact column names `canonical_cell_id`,
`selected_query_address`, `donor_id` and `operator_index`, and fails closed if
any is absent, because substring matching on an authority column is how a schema
change silently selects the wrong field.

## Local verification state

25 of 25 behavioural tests pass. These are local pre-freeze results and do not
substitute for independent review.

## Not done here, and not authorized by this freeze

The real sweep. Real capture, replay or effect-row bytes. Runtime projection or
the bounded WSL/CUDA soak. Real output-hash population. Any F1-A scientific
change. Real F1 remains unauthorized.
