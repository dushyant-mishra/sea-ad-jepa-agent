# F1-A Producer / Replay Pre-Freeze — External Review Handoff, 2026-09-07

Terminal claimed by this submission, and the only thing it may be read as
granting:

```
PASS_F1_U0_PRODUCTION_MECHANICS_PREFREEZE_READY_FOR_INDEPENDENT_REVIEW__REAL_F1_STILL_UNAUTHORIZED
```

The terminal deliberately separates mechanics readiness from execution
permission. It claims no scientific or biological qualification.

The first real F1 run is a REFERENCE PRODUCTION-MECHANICS BASELINE ON CLEAN u0.
It is not a healthy trained-teacher result, not a biological qualification of
u0, not authority to select a future training target, not authority to begin D1
or production teacher training, and not evidence that a data-defined rare
biological target exists. u0 is a mechanics fixture; model width 160 is
architectural, not a biological dimension.

No authorization artifact has been issued, no real sweep has been executed, and
there are no real output bytes anywhere in this package.

## This submission answers a prior STOP

An external review returned `STOP_F1_REAL_PRODUCER_REPLAY_NOT_YET_EXECUTABLE`.
Its findings were accepted in full. What changed:

- `run_production_sweep` was a gate followed by an unconditional STOP with no
  pipeline behind it. It is now a real end-to-end producer: reader_fit row
  resolution, exact normalization, physical observation-state handling,
  query/evidence mask construction, teacher forward, correct-student forwards,
  matched-null student forwards, capture, cache, shard publication, effect-row
  publication, resumable completion, and final completeness verification. A test
  drives it end to end under a valid authorization and a second test interrupts
  and resumes it.
- There was no way to make the frozen source runnable without editing it.
  `REAL_EXECUTION_READY` and the three `FROZEN_REAL_*` roots are gone;
  authorization is an external pre-result artifact.
- Capture completeness was one count per assignment, which a teacher-only set
  satisfied. Four identity topologies are now enforced separately.
- The replay was parity primitives, not a replay of a produced result. It now
  reads the produced artifacts and re-derives everything independently.

Two defects were found by continuing to self-review after those repairs, and
both would have broken the first authorized run: the reviewed shard store takes
four required constructor arguments and has no `exists` method, and the frozen
identity functions key on `canonical_cell_id` and an integer `q` rather than on
the query address string.

## What you are reviewing

Branch `f1-real-producer-replay-prefreeze-20260907`, taken from the previously
reviewed preflight state `f1-real-reader-forward-preflight-20260903` at
`14e41030ffac65b3d58a45ae4159d30b8517e470`.

Bind your review to the package root recorded in
`outputs/f1_real_producer_replay_prefreeze_20260907/F1_PREFREEZE_ROOT_SHA256.txt`
and to the member digests in `F1_PREFREEZE_MANIFEST.csv` beside it. The root is
deliberately not restated in any reviewed document: a document that embeds its
own package root changes the root by stating it, and this project has already
rejected a package for that shape. Recompute the root yourself from the
manifest rather than trusting a quoted value, including this handoff's own
member digest.

Digests are SHA-256 over the bytes **git** holds, not the working tree. A
text-classified source checks out with CRLF on Windows, so a working-tree
digest differs from the immutable blob by one byte per line. Verify with
`git show :<path>`, and expect a mismatch if you hash the checked-out file.

## The claim to attack

Two implementations of the same F1-A production quantities agree, and neither
can borrow the other's arithmetic, and both were byte-frozen before any real
output existed.

Each of those three conjuncts is separately falsifiable, and the third is the
one that cannot be repaired later. If you find that the source could have been
adjusted after outcomes were visible, the correct finding is that the freeze is
void, not that it needs a patch.

## Independence, which is the load-bearing property

Agreement between a producer and a replay is worthless as evidence if the
replay is a wrapper. The specific separations claimed:

- the producer **asserts** the acceptance-contract constants; the replay
  **derives** the same counts by counting rows and distinct `(cell,q)` pairs in
  the frozen CSVs. The suite reproduces 44,496 / 43,108 / 222,480 / 474,188
  from data rather than from a restated constant, and a deliberate geometry
  disagreement is required to be detected;
- identity digests, the identity root, the payload digest, the physical shard
  mapping, cosine, QID and the effect row are each reimplemented in the replay
  from the contract wording;
- cosine is associated differently on purpose — normalise then dot, against dot
  divided by the norm product. Algebraically identical, so parity is asserted
  to a declared float64 tolerance (`PARITY_ULP_MULTIPLIER = 256`), while
  `qid_win` is compared exactly because it is discrete;
- the replay refuses to run as a CLI if the producer or the shared preflight
  executor is present in `sys.modules`, and a test proves that guard fires;
- two AST tests assert neither source imports the other, in both directions.

Attack this by looking for a shared upstream that silently supplies the answer.
The producer does import reviewed upstream helpers — `AtomicShardStore`,
`build_effect_row`, `full_geometry`, `student_forward_identity`,
`teacher_compute_identity`, and `physical_shard_id`. The replay imports none of
them. If any quantity you care about is in fact computed once upstream and
merely read twice, that is a real independence defect and we want it named.

## Verify the comparator before you trust any parity result

A comparator that accepts everything makes every parity test pass. The suite
guards itself: a test perturbs a producer value by `1e-6` and requires the
comparison to fail. Re-run that guard, and consider widening it — if a
perturbation an order of magnitude larger than the declared tolerance still
passes, the tolerance is doing no work.

## Suggested order of attack

1. Recompute the root and every member digest from git bytes. Confirm the five
   frozen sources are exactly the ones the contract names: producer, replay,
   authorization, tests and packager.
2. Confirm the execution boundary. There is no in-source permission left to
   inspect: `REAL_EXECUTION_READY` and the three `FROZEN_REAL_*` roots were
   removed, and a test asserts their absence as attributes and as source text.
   With `F1_EXECUTION_AUTHORIZATION` unset, `run_production_sweep` raises
   `STOP_F1_EXECUTION_AUTHORIZATION_ABSENT`; passing
   `real_execution_ready=True, force=True` still raises it, since those are
   absorbed as unused keyword arguments and authorization resolves first. Try to
   find a parameter, environment variable, monkeypatch or import-order path that
   reaches production work anyway.
3. Confirm the partition gate rejects `reader_validation`, `reader_oracle`,
   `development`, `sealed_holdout` and `whole_study_external_holdout`, and also
   rejects an unrecognised partition rather than ignoring it.
4. Run the suite. Expectations depend on whether you hold the external
   authority files, and this is the paragraph most likely to mislead you if
   skipped.

   The assignment authority is 30 MB and the dedup map 8 MB, and neither is
   tracked, so neither can be a package member. Five checks therefore depend on
   an external tree; they are named in `AUTHORITY_DEPENDENT_TESTS` and a
   meta-test derives that list by AST so it cannot drift.

   | situation | expected |
   |---|---|
   | authorities reachable | 66 passed |
   | `F1_PREFREEZE_AUTHORITY_ROOT=<tree>` plus `F1_PREFREEZE_REQUIRE_AUTHORITIES=1` | 66 passed |
   | clean extraction, no authorities | 61 passed, **5 skipped** |
   | clean extraction plus strict | 61 passed, **5 failed** |

   Those five skips are `NOT_MEASURABLE`, not `PASS`, under the project
   precedence `INVALID > FAIL > NOT_MEASURABLE > PASS`, and they are excluded
   from any production pass count. For a production-readiness judgement run
   strict mode with every authority present. When `F1_PREFREEZE_AUTHORITY_ROOT`
   is set it is the only root consulted, so a stale local path cannot satisfy it
   silently.

   An earlier revision of this handoff told you to expect a full pass count from
   a clean extraction. That was wrong, and the dangerous kind of wrong: it
   invited reading silent skips as verification of the package's central claim.
   Local passes are not certification in any case. There is no CI run for this
   branch, so everything reported here is a reproduction target.

5. Attack the capture-coverage obligation. `plan_mechanics_capture` enumerates
   one capture record per assignment from `assignment_key_sha256`, asserts
   44,496 planned assignments and the 222,480 evidence expansion, and requires
   the keys to be distinct. `assert_capture_coverage` then separates three
   distinct failures — a planned assignment with no capture record, one captured
   twice, and a capture record whose key is not in the plan. Each has its own
   STOP and its own test. `mechanics_capture_record` additionally rejects an
   unrecognised role, an evidence level outside `(20, 40, 60, 80, 100)`, and any
   evidence level attached to a teacher record, since the teacher state is
   evidence-invariant and five teacher forwards per `(cell,q)` would inflate the
   forward count.

   This existed only as a docstring sentence until it was re-audited. Treat it
   as newly written code rather than as reviewed code.
6. Attack the authorization boundary. Confirm the producer cannot run with
   `F1_EXECUTION_AUTHORIZATION` unset; that a valid artifact unlocks the frozen
   source without editing it; that each of package root, source digests,
   checkpoint, partition, donor count, roster root, authority digests,
   mechanics, geometry and scope raises its own named STOP when wrong; that
   editing an issued authorization is detected by its body digest; and that a
   closure artifact is refused as authorization. Try to find any path that
   reaches production work without a validated authorization.

7. Attack the four identity topologies. A teacher-only capture set, a set with
   the right grand total but the wrong role distribution, a complete forward set
   with one missing effect row, and a complete effect-row set with one missing
   shard must all fail. So must a duplicate capture, a duplicate effect row, a
   capture bound to another checkpoint, and a capture referencing a shard
   outside the lawful 1,400.

8. Attack replay independence on outputs. Mutate a produced result -- drop a
   forward, duplicate one, flip a role, alter an evidence level, alter a
   recipient, change a checkpoint, drop or duplicate an effect row -- and
   require the replay to detect it from the artifacts alone. Also confirm the
   replay refuses to run in a process that has imported the producer, and that
   its CLI verification works in a clean process.

9. Attack independence, then the comparator, then the freeze ordering.
10. Read `F1_DATA_ONLY_CLOSURE_DESIGN_20260907.md` and judge whether closure can
   bind real roots without editing frozen source. Step 6 of that ordering —
   re-verifying every pre-freeze source digest after the sweep — is stated as
   the reviewer's job, not the producing lane's. If you would not accept it,
   say so now, before the sweep, because afterwards it cannot be fixed.

## Scope this lane deliberately did not enter

No real sweep. No real capture, replay or effect-row bytes. No runtime
projection or bounded WSL/CUDA soak. No F1-A scientific change. No
reader-validation, reader-oracle, DEV, SEALED, foundation sealed-holdout or
pathology asset opened. The sealed-holdout registry branch and the sealed F1-B
attack authority were not touched — an earlier ledger commit that had landed on
the F1-B branch was relocated to `ledger/t0-v20-binding-20260907` precisely to
keep that seal intact.

## Two self-repairs, recorded rather than hidden

An earlier draft built the shard filename from donor and operator with a `::`
separator, which is illegal on Windows and broke three tests. The reviewed
acceptance validator had already solved this by hashing the logical id into
`shard_<sha256>`. The error was inventing an encoding over a solved problem,
not the separator, and the producer now binds `physical_shard_id` from that
validator while keeping the logical `(donor_id, operator_index)` pair as
canonical compact JSON — an identity, never a filename.

An earlier draft of the replay selected the operator column by substring match.
It now requires the exact column names `canonical_cell_id`,
`selected_query_address`, `donor_id` and `operator_index` and fails closed
otherwise, because substring matching on an authority column is how a schema
change silently selects the wrong field.

## What a STOP should look like

Name the exact file and digest, and the exact conflicting authority. Do not
resolve an authority ambiguity heuristically on our behalf. A STOP that says
the freeze is void is a more useful outcome than a PASS that we would have to
re-earn after the sweep.
