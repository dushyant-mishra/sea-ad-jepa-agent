# F1 ea35 Independent Review — 2026-09-07

Candidate: `ea35b55f63b83547fbb1e0f35fd15ed33901c3fa`
Branch reviewed: `f1-real-producer-replay-prefreeze-20260907`

Independent terminal:

`STOP_F1_EA35_NOT_READY_FOR_EXECUTION_AUTHORIZATION__REAL_F1_REMAINS_UNAUTHORIZED`

The candidate is substantially improved over `799eb3fb...`, but independent review found execution-critical gaps not covered by the reported 66-test suite. No real F1 run is authorized.

## F1-R1 — Production model binding is not executable as currently frozen

`TorchForwardEngine._load()` calls:

`self._model_module.build_teacher_encoder(state)`

but the frozen `src/sea_ad_jepa/v4/ipb_jepa.py` does not define `build_teacher_encoder`.

The engine also calls the returned object as:

`encoder(cell=..., mask=...)`

while the frozen `IPBEncoder.forward()` signature is the lower-level gene/expression/measurement/hidden-mask/view interface. Therefore the real production seam requires a separate adapter/factory module.

That adapter is not currently part of the frozen five-source package, and the execution authorization does not bind its source hash.

Required repair: add a prospectively frozen runtime adapter/factory source that converts the authorized reader row into the exact frozen model call, loads the exact u0 state dict, exposes the teacher and student routes, and is included in both the package root and execution authorization source digests. Add a Torch-installed smoke test that actually loads the real u0 checkpoint and performs at least one teacher, one correct-student and one matched-null forward through the exact production adapter.

## F1-R2 — Reader/runtime implementation is not bound by execution authorization

`validate_execution_authorization()` binds producer/replay/authorization/tests, checkpoint, authority digests, mechanics, geometry and reader-fit roster, but `run_production_sweep()` then accepts arbitrary injected `forward_engine` and `reader` Python objects.

The runtime firewall checks donor membership only. It does not bind:
- exact reader implementation source;
- production loader implementation/source hash;
- metadata/row-locator root;
- observation-state implementation binding;
- exact query/materialization adapter;
- runtime model adapter source.

A caller could therefore validate the same authorization and substitute a different reader/model adapter without changing the authorization artifact.

Required repair: extend the external execution binding to name/hash the exact runtime adapter, reader/loader implementation and required input roots. Runtime must instantiate or verify those exact sources rather than trust arbitrary post-authorization Python objects.

## F1-R3 — Resume is incomplete at the inferential-output level

When a shard `.npz` already exists, `execute_authorized_sweep()` appends the shard id to `resumed`/`published` and immediately `continue`s.

It does not restore that shard's:
- forward capture records;
- effect rows;
- correct/null student sufficient statistics.

Therefore the returned `captures` and `effect_rows` contain only newly executed shards. `verify_sweep_completeness()` requires all forward/effect identities, so a truly interrupted/resumed run cannot pass final completeness.

The reported resume test checks only that old shard files are not rewritten and that only the remaining shard performs forwards; it never calls `verify_sweep_completeness()` on the resumed result.

Required repair: each committed shard must atomically include or bind all per-shard replay/completeness artifacts needed for resume. A resumed run must reload them and the final resumed result must pass the same full completeness and replay path as an uninterrupted run.

## F1-R4 — Capture/effect outputs are not durably published by the producer

`execute_authorized_sweep()` returns `captures` and `effect_rows` as in-memory Python lists. The only durable output committed inside the producer is the `AtomicShardStore` NPZ payload.

`f1_real_replay_v1.py` requires a `capture_path` and `effect_row_path`, but the production sweep never writes those artifacts.

Therefore process termination after a successful sweep loses the capture/effect outputs that the replay and data-only closure are supposed to bind.

Required repair: implement deterministic atomic publication of capture and effect-row artifacts (preferably shard-local plus deterministic final manifests/roots) inside the authorized producer. Their roots must be derivable from produced bytes without editing frozen source.

## F1-R5 — The current 'effect rows' contain no F1 numerical effect

The sweep computes teacher and student states, but each effect-row record currently contains only:

- `assignment_key`
- `evidence_level`
- `shard_id`
- `checkpoint_sha256`

Correct and matched-null student states are discarded after their capture metadata are created. `build_effect_row()` is not called in the production sweep.

Thus the produced artifacts cannot reconstruct the actual correct-vs-null F1 effect/statistical sufficient statistic. The replay verifies effect-row topology only, not the numerical estimand.

Required repair: wire the frozen F1 statistical effect construction into the production path. Persist the exact sufficient statistics/effect values required by the frozen estimand, and make the independent replay re-derive/verify those numerical values from persisted forward/sufficient-statistic artifacts.

## F1-R6 — Matched-null execution is not visibly implemented at the runtime seam

The producer adds `null_source_cell` to the identity record, but the actual `student_forward()` call receives the same recipient cell for both arms and only an `arm` string/mask tuple distinguishes `correct` from `matched_null`.

Because the real adapter is absent/unbound, there is no frozen executable proof that matched-null source context is actually loaded and substituted according to the frozen matched-null map rather than merely relabeled.

Required repair: the runtime adapter must explicitly resolve the frozen matched-null source identity and construct the null student input. Add a metamorphic test where changing the matched-null source changes the null input/state identity but leaves the recipient/query/evidence identity fixed.

## F1-R7 — Evidence-mask construction requires contract-level verification

`build_query_evidence_mask()` currently takes the first measured addresses in index order up to the requested percentage and does not use `query_address` except as a parameter name.

Independent review has not yet established that this is the exact frozen F1 evidence-mask construction. Because F1's scientific estimand depends on query-local evidence semantics, this must be explicitly checked against the controlling evidence-mask authority before execution authorization.

Required repair if mismatch is confirmed: call the exact frozen evidence-mask constructor or reproduce it with an independently verified implementation and metamorphic tests. Do not silently substitute 'first measured addresses' for the frozen query/evidence semantics.

## Required re-review evidence

A successor candidate should not be presented for execution authorization until all of the following are demonstrated:

1. real Torch u0 adapter smoke test executes teacher/correct/null forwards;
2. runtime adapter + reader/loader are immutable and authorization-bound;
3. interrupted/resumed run passes full completeness, not only shard reuse;
4. capture/effect artifacts are atomically persisted;
5. actual F1 numerical effects/sufficient statistics are produced and independently replayed;
6. matched-null source substitution is executable and tested;
7. evidence-mask implementation is proven identical to frozen authority;
8. fresh detached worktree/CI runs the repaired suite with required authorities.

No authority branch should be fast-forwarded and no real F1 sweep should run from `ea35b55...`.
