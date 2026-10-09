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

Evidence: `tests/test_f1_u0_adapter_smoke_v1.py`, run against the real u0
checkpoint under the project's torch environment. It loads the actual state
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

Superseded by the inventory in the dd07862 response section below, which adds
the residual execution-binding attacks. The counts there are authoritative.

`F1_REQUIRE_TORCH_SMOKE=1` turns the NOT_MEASURABLE smoke results into hard
errors, so they can never be counted as passes. A production-readiness
judgement must use the torch environment, where there are no skips.

## What is still not claimed

No execution authorization is issued by this document or this package. The
terminal claims mechanics readiness for independent re-review only, and no
authority branch has been fast-forwarded.


# Response to the dd07862 residual re-review

Reviewed candidate: `dd078625c3537f5ff2c3f8c0b382ba2803b24ee2`
Review terminal:
`STOP_F1_DD078_RUNTIME_VALUE_BINDING_NOT_CLOSED__REAL_F1_REMAINS_UNAUTHORIZED`

Both residual defects are accepted and neither was disputed. R1, R3, R4, R5 and
R7 were not reopened, and R6's causal semantics are unchanged: `S_null`
substitutes source normalized values only and retains the recipient's
`M_physical`, `U_evidence`, q, operator/source and provenance.

## Residual 1 — the source VALUES are now bound, not just the identity

The adapter authenticated `source_row["canonical_cell_id"]` and donor
distinctness, then accepted `source_normalized_expression` independently and
forwarded it. P(c) was a label; the values were free.

The review's sharpest observation is correct and worth recording plainly: the
previous metamorphic test *demonstrated* this hole while being read as proof of
correctness. It fixed one source identity, supplied two materially different
vectors, and required BOTH to be accepted.

The free-vector path is gone. `matched_null_student_state` now accepts only a
`VerifiedSourceValues` object, and that object cannot exist unverified because
construction performs the checks:

1. the normalized vector must equal `log1p(counts*10000/max(library,1))` of the
   declared counts and library, which catches altered values, twice-normalized
   values and a wrong `source_library`;
2. the value digest must recompute over the row locator, canonical source
   identity, counts digest, source library and normalized bytes, which catches
   values lifted from another row;
3. `resolve_authenticated_source_values` checks the locator, cell and donor
   against the frozen map BEFORE any values object is built;
4. the adapter additionally requires the object's locator, cell and donor to be
   the ones the frozen map names for this recipient, and the object is
   immutable with `normalized()` returning a copy.

The discriminator is now the correct way round:

- same authenticated identity plus altered values → STOP, and impossible to
  construct;
- a DIFFERENT authenticated identity carrying its own authentic values may move
  `S_null`, while the recipient's evidence, physical-state and hidden-mask
  digests stay byte-identical.

Each produced null capture carries `matched_null_source_values_sha256` and the
full source provenance, so the binding is visible in the artifacts.

## Residual 2 — the three auxiliary digests are compared, not length-checked

`assert_runtime_binding` did `if len(binding[field]) != 64: STOP`, so
`"0" * 64` was structurally acceptable and the fields named digests nothing was
compared against.

They are now compared against verified values:

- `evidence_mask_authority_sha256` against the frozen contract digest
  `d1eefdab…`;
- `loader_source_sha256` against `267fa42a…`;
- `matched_null_map_sha256` against the digest the adapter itself carries, which
  `load_matched_null_map` sets from the bytes it read, and which must also equal
  the frozen `aba31aea…`.

`load_matched_null_map` now returns the mapping together with that digest. An
adapter constructed from an arbitrary in-memory mapping has no verified digest
and is refused with `STOP_F1_MATCHED_NULL_MAP_DIGEST_UNVERIFIED`, even though
its class is the authorized one.

## Attacks added

Every attack the review named, each paired with a lawful case that must pass so
none can succeed by refusing everything:

- wrong-but-64-character evidence-mask authority digest → STOP;
- wrong-but-64-character matched-null-map digest → STOP;
- wrong-but-64-character loader-source digest → STOP;
- correct adapter module bytes with an unverified in-memory map → STOP;
- correct adapter module bytes with a wrong map digest → STOP;
- same source identity with altered values → STOP;
- same source identity with twice-normalized values → STOP;
- same source identity with a different `source_library` → STOP;
- values carrying another row's digest → STOP;
- wrong locator, wrong cell or wrong donor at the resolver → STOP;
- a free expression array passed to the null arm → STOP;
- adapter and producer normalizations required to agree bit for bit.

## Test inventory after the repair

| suite | no-torch | project torch environment |
|---|---|---|
| producer/replay parity and attacks | 78 passed | 78 passed |
| evidence-mask authority | 14 passed | 14 passed |
| real u0 adapter smoke | 9 NOT_MEASURABLE | 9 passed |
| total | 92 passed, 9 NOT_MEASURABLE | 101 passed, 0 skipped |

## One fabricated threshold removed

The smoke test asserted `|A| < 0.05`. Measured across 15 combinations of row
seed and source-value seed, `|A|` ranged 0.0469 to 0.0681, so that bound sat
inside the observed range and would have passed or failed by seed. It was a
number chosen to make the test pass. It is replaced by the mathematically valid
bound for a difference of two cosines, and the measurement is recorded instead
of a claim. A came out consistently positive because the correct student shares
the recipient's expression with the teacher while the null carries a different
cell's values -- a structural consequence of the construction on an untrained
encoder, not a biological signal.

## Still not claimed

No execution authorization is issued. Real F1 remains unauthorized and no
authority branch was altered.
