# Response to the F1 ea35 independent review — 2026-09-07

Reviewed candidate: `ea35b55f63b83547fbb1e0f35fd15ed33901c3fa`
Review: `review/f1-ea35-independent-20260907` @ `b0db8ea07ae0a61b5a5d37c51e419d6b2a1044b4`
Review terminal:
`STOP_F1_EA35_NOT_READY_FOR_EXECUTION_AUTHORIZATION__REAL_F1_REMAINS_UNAUTHORIZED`

All seven findings are accepted. None was disputed. Each is answered below with
the authority it was resolved against and the test that holds it.

The scope statement is unchanged: the first real F1 run is a REFERENCE
PRODUCTION-MECHANICS BASELINE ON CLEAN u0. It is not a healthy trained-teacher
result, not a biological qualification of u0, not authority to select a training
target, and not authority to begin D1. No authorization artifact has been
issued and no real sweep has been executed.

## F1-R1 — production model binding is now executable

`build_teacher_encoder` never existed. The real seam is
`construct_query_local_contextual_state` in
`src/sea_ad_jepa/v4/contextual_query_local.py` (`6bd641cd…`), and the reviewed
encoder construction is `run_contextual_target_v1_f0.py::load_encoder`:

```python
loaded = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
encoder = IPBEncoder(vocabulary_size=41_238, width=160, heads=4, blocks=6,
                     gradient_checkpointing=False)
encoder.load_state_dict(loaded["online_encoder"], strict=True)
encoder.eval()
```

`scripts/v4/f1_production_runtime_adapter_v1.py` is the new frozen adapter. It
is a package member and is bound by the authorization's source digests.

Two further contract mismatches surfaced while making it run, and both would
have failed the first authorized call:

- the provenance row digest is `dtype string || JSON shape || C-order bytes`,
  not a name-prefixed hash;
- `_module_state_sha256` iterates `state_dict().items()` in INSERTION order.
  Sorting the names yields a different digest and the authority then refuses to
  bind the encoder.

Evidence: `tests/test_f1_u0_adapter_smoke_v1.py`, 8 tests, run against the real
u0 checkpoint under the project's torch environment. It loads the actual state
dict and executes one teacher, one correct-student and one matched-null forward
through the exact adapter, then builds the real effect row.

## F1-R2 — the runtime implementation is now authorization-bound

`assert_runtime_binding` hashes the module that defines each injected object via
`inspect.getfile(type(obj))` and requires it to equal the digest the
authorization names, plus a complete `runtime_binding` naming the evidence-mask
authority, the matched-null map and the loader source. Validating an
authorization and then accepting arbitrary adapter and reader objects meant the
artifact bound source it did not run; it now binds what actually runs.

Tested by `test_the_authorization_must_bind_the_runtime_adapter_and_reader`,
which rejects an absent binding, a swapped adapter digest and an incomplete
binding, and then shows a matching binding passing the runtime check so the
guard is discriminating.

## F1-R3 — resume is complete at the inferential-output level

Each shard now publishes its own durable capture, effect-row and state
artifacts, and `shard_is_complete` requires all four files. A resumed shard
reloads its capture and effect rows, so the resumed result carries every forward
and effect identity. A payload without its sidecars is NOT complete and is
recomputed rather than counted.

`test_an_interrupted_sweep_resumes_and_passes_full_completeness` interrupts,
resumes, and then calls `verify_sweep_completeness` on the resumed result — the
step the previous resume test never performed — and additionally requires the
resumed capture and effect roots to equal those of an uninterrupted run.

## F1-R4 — capture and effect outputs are durably published

Per-shard artifacts are written atomically through staging plus `os.replace`,
the state sidecar and JSON sidecars are written before the payload commit, and
the payload commit is what makes a shard count. A final
`F1_SWEEP_MANIFEST.json` plus capture, effect-row and shard-set roots are
derived from produced bytes only, so they need no source edit.

Tested by `test_capture_and_effect_artifacts_are_durably_published` and by
`test_the_replay_verifies_artifacts_the_producer_actually_wrote`, which closes
the loop by replaying the producer's own files.

## F1-R5 — effect rows now carry the real F1 estimand

`build_effect_row` is called in the production path. One forward yields both
readouts — `h_query` is the DIRECT state and
`contextual_state = layer_norm(h_query - mu_context)` is the CONTEXTUAL state —
which is why 474,188 forwards suffice for the six vectors the estimand needs.
Each row carries `A`, `direct_delta`, `qid_margin`, `qid_win`,
`own_similarity`, `paired_wrong_similarity` and the three evidence digests.

The six state vectors are persisted per shard in float64 while the shard payload
stays float32 as the accepted mechanics require. The forwards are float32 so
their values are exactly representable, and widening the verification copy lets
the replay reproduce the producer's float64 arithmetic exactly rather than to
about 1e-8. `test_the_persisted_states_allow_independent_effect_recomputation`
re-derives `A` from the persisted bytes and agrees to 1e-12.

## F1-R6 — matched-null substitution is executable and tested

`F1_MATCHED_NULL_CAUSAL_CONTRACT.md` fixes it exactly, and it corrects a natural
misreading. `S_null(c,q,e)` takes the normalized values of the frozen
donor-distinct source row but retains the RECIPIENT's `M_physical`,
`U_evidence(e,q)`, query identity and operator/source: "The permutation occurs
before the encoder. It changes normalized values, not M, U, q, operator or
source." Substituting the source's physical state as well would be a different
and unauthorised experiment.

The frozen map is cell level, 2,781 recipients matching `recipient_cells` in the
geometry, each with one donor-distinct source. The adapter resolves the source
from that map and refuses an improvised or same-donor substitute. A metamorphic
test shows a different source moving `S_null` while the recipient's evidence,
physical-state and hidden-mask digests stay byte-identical.

## F1-R7 — the evidence mask is now the frozen construction

The mismatch is confirmed, and the previous rule was wrong in three independent
ways. `scripts/v4/f1_evidence_mask_authority_v1.py` implements
`CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md` (`d1eefdab…`, resolved by
`F1_EVIDENCE_MASK_AUTHORITY.json` `b637e2b8…`):

- `E = {j : state[r,j] == MEASURED_SCALAR and j != q}`, rejecting a query that
  is not scalar-measured;
- `SHA256(seed || "|" || row-locator || "|" || decimal-q || "|" || decimal-j)`
  with seed `c5c5bc47…`, sorted by digest bytes then integer address;
- level `p` takes the first `floor(p * |E| / 100)` of that single ordering, so
  the levels nest and 100% is all of `E`;
- the teacher-rich target uses all of `E`, which is why the teacher state is
  evidence-invariant.

The old rule took the first measured addresses in address order at a ROUNDED
percentage and did not withhold the query. `tests/test_f1_evidence_mask_authority_v1.py`
has 14 tests including one that reconstructs the old rule and requires it to
disagree, so the repair cannot be silently reverted.

## Test inventory

| suite | no-torch interpreter | project torch environment |
|---|---|---|
| producer/replay parity and attacks | 72 passed | 72 passed |
| evidence-mask authority | 14 passed | 14 passed |
| real u0 adapter smoke | 8 NOT_MEASURABLE | 8 passed |
| total | 86 passed, 8 NOT_MEASURABLE | 94 passed, 0 skipped |

`F1_REQUIRE_TORCH_SMOKE=1` turns the NOT_MEASURABLE smoke results into hard
errors, so they can never be counted as passes. A production-readiness
judgement must use the torch environment, where there are no skips.

## What is still not claimed

No execution authorization is issued by this document or this package. The
terminal claims mechanics readiness for independent re-review only, and no
authority branch has been fast-forwarded.
