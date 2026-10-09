# F1-A Real Producer / Replay Pre-Freeze Contract — 2026-09-07

Terminal: `PASS_F1_U0_PRODUCTION_MECHANICS_PREFREEZE_READY_FOR_INDEPENDENT_REVIEW__REAL_F1_STILL_UNAUTHORIZED`

The terminal separates mechanics readiness from execution permission. It claims
no scientific or biological qualification. The first real F1 run is a
REFERENCE PRODUCTION-MECHANICS BASELINE ON CLEAN u0: not a healthy
trained-teacher result, not a biological qualification of u0, not authority to
select a future training target, and not authority to begin D1 or production
teacher training.

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

## Execution authorization, external to the frozen source

`run_production_sweep` is a real end-to-end producer. It resolves reader_fit
rows, applies the exact normalization, handles the physical observation state,
builds query/evidence masks, runs the teacher forward, the correct-student
forwards and the matched-null student forwards, captures, caches, publishes
shards and effect rows, resumes by shard presence, and verifies completeness.

It cannot run without a valid external authorization artifact, and there is no
in-source flag to flip. `REAL_EXECUTION_READY` and the three `FROZEN_REAL_*`
root constants have been removed, and a test asserts their absence as both
attributes and source text. Authorization lives in
`scripts/v4/f1_execution_authorization_v1.py`, is read from
`F1_EXECUTION_AUTHORIZATION`, and binds the package root, the frozen source
digests, the u0 checkpoint, the reader roster, the authority digests, the
accepted mechanics, the frozen geometry and the scope. Each drift is a distinct
STOP, and a post-result closure artifact is rejected as an authorization, so a
run cannot be authorized retroactively. Details are in
`F1_EXECUTION_AUTHORIZATION_DESIGN_20260907.md`.

## Every identity set is enforced separately

A single count is not completeness. The capture record and the forward record
are distinct objects, because an earlier revision blurred them: the record
carried `role` and `evidence_level` while the validator only proved one record
per assignment key, so a set holding one teacher record per assignment passed as
complete while containing no correct-student and no matched-null forward at all.

- `mechanics_capture_record` is ASSIGNMENT level and carries no role or
  evidence level; `plan_mechanics_capture` and `assert_capture_coverage` enforce
  coverage of all 44,496 assignments.
- `forward_capture_record` is FORWARD level and must distinguish role,
  recipient cell, query, evidence level where applicable, correct versus
  matched-null arm, teacher versus student family, shard, and
  model/checkpoint identity.
- `assert_forward_topology` enforces 43,108 teacher, 215,540 correct, 215,540
  matched-null and 474,188 total as separate identity sets, requires the
  correct and matched-null arms to cover identical keys, and requires every
  student key to have its evidence-invariant teacher forward.
- `assert_effect_row_topology` enforces exactly one row per
  (assignment_key, evidence level), 222,480 in total.
- `assert_shard_topology` enforces all 1,400 donor x operator shards, published
  once each and nothing outside the lawful set.
- `verify_sweep_completeness` requires all four; none is sufficient alone.

## Population firewall

Execution is `reader_fit` only, and `foundation` and `train` are not synonyms
for it. The roster comes from the `reader_partition` column of the frozen
`reader_donor_split.csv` (`efe43e63...`), whose declared counts are 104
reader_fit, 22 reader_validation and 23 reader_oracle donors, and the roster
root must equal `a635ddf3...`. Continuation and train donors outside
`reader_fit` are absent by construction; a delivered off-roster donor raises
`STOP_F1_POPULATION_FIREWALL` rather than being filtered away.

## Authority byte classes

Each authority is digested over the bytes that define it, declared per
authority. The three tracked model sources use git blob bytes; the assignment
CSVs and the checkpoint use file bytes. Hashing working-tree bytes for the
tracked sources passed in an LF checkout and failed in a CRLF checkout of the
same commit -- in this worktree `ipb_jepa.py` is `f5bdfb73...` on disk and the
frozen `732ea46f...` in the index. Source digests resolve from the package's own
git, because `contextual_query_local.py` is tracked here and untracked in the
main working repository.

## Real output roots

Still not populated, and no longer expressible in source. They may only be bound
by the data-only closure in `F1_DATA_ONLY_CLOSURE_DESIGN_20260907.md`.

## Repairs made during this work, recorded rather than hidden

Two of these were found by re-auditing this lane *after* it had already been
committed, pushed and reported as complete, against the restated task
specification. Both were places where a requirement was satisfied in prose but
not in code.

`mechanics_capture_record` carried a docstring stating it "covers every one of
the 44,496 assignments" while nothing enumerated or enforced coverage, and
neither `role` nor `evidence_level` was validated. The docstring now explicitly
disclaims the coverage assertion and points at the two functions that enforce
it.

The geometry-versus-derived-counts checks resolved their input authorities
through this machine's hardcoded absolute paths and called `pytest.skip` when
absent. Since those checks are the strongest evidence in the package, an
external reviewer would have seen the central claim vanish silently while the
suite still reported green -- and the first revision of the review handoff told
the reviewer to expect a full pass count from a clean extraction. Both the
mechanism and the handoff are corrected above.


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

## Mechanics capture over all 44,496 assignments

`plan_mechanics_capture` enumerates one capture obligation per statistical
assignment, keyed on the authority's own `assignment_key_sha256` column. It
asserts 44,496 planned assignments, requires the keys to be distinct, and
asserts the 222,480 assignment-by-evidence expansion, so a truncated or extended
authority file cannot quietly shrink the obligation.

`assert_capture_coverage` then separates three failures that have different
causes: a planned assignment with no capture record (a dropped forward), one
captured twice (a double count), and a capture record whose key is not in the
plan (an unauthorised forward). Each raises its own STOP and has its own test.

`mechanics_capture_record` rejects an unrecognised role, an evidence level
outside `(20, 40, 60, 80, 100)`, a malformed assignment key, and any evidence
level attached to a teacher record -- the teacher state is evidence-invariant,
so an evidence level there would imply five teacher forwards per `(cell,q)` and
inflate the forward count.

The replay derives the same coverage independently in
`replay_derive_capture_coverage`, counting the key column without consulting the
producer and reconciling the keys against the
`(canonical_cell_id, selected_query_address)` pairs, and
`compare_capture_coverage` compares the two including an assignment-key root.

## Local verification state

66 of 66 tests pass with the authorities reachable. Four authority modes were
exercised separately, because a skipped check is not a passed one:

| situation | expected |
|---|---|
| authorities reachable | 66 passed |
| explicit root plus `F1_PREFREEZE_REQUIRE_AUTHORITIES=1` | 66 passed |
| clean extraction, no authorities | 61 passed, 5 NOT_MEASURABLE |
| clean extraction plus strict | 61 passed, 5 failed |

Under the project precedence `INVALID > FAIL > NOT_MEASURABLE > PASS`, the five
skips are NOT_MEASURABLE and are excluded from any production pass count.
Production review must use strict mode with every authority present.

These are local results. There is no CI run for this branch, so they are a
reproduction target rather than independent verification.

## Not done here, and not authorized by this freeze

The real sweep. Real capture, replay or effect-row bytes. Runtime projection or
the bounded WSL/CUDA soak. Real output-hash population. Any F1-A scientific
change. Real F1 remains unauthorized.
