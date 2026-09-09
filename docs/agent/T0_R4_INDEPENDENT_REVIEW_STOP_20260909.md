# T0 R4 independent external review — STOP

Reviewed producer candidate:

```
branch      t0/v20-pathology-blind-materialization-20260908
candidate   b08d02f721636eeba43c8612f934e816deec5f05
R4 base     ab61cf5599663c417d2b2c5ef95ca7e5a37a312c
```

Standing terminals remain unchanged:

```
PRODUCTION_B2_NOT_RUN
DONOR_ROLE_GATE_SHUT
real_execution_ready=False
NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED
```

## Disposition

`STOP_T0_R4_INDEPENDENT_REVIEW__SAFE_RAW_SOURCE_MODULE_NOT_CLOSED_INTO_EXECUTION_CHAIN`

R4 materially improves the design, but it does not yet close the implementation
chain.  The producer's 556-case local suite remains producer evidence, not
external PASS.

## Defect A — the old caller-vector source-library prover is still public and green

R4 adds `t0_raw_source_row_authority_v1.prove_source_library_from_authenticated_source`,
which correctly has no values argument.  However,
`t0_v20_row_count_authority_v1.prove_source_library` still exists publicly with
the old signature:

```
raw_source_row_values
raw_source_provenance
```

and the existing positive test still manufactures

```
raw = [0] * 36_600 + [bound]
```

and asserts that this fabricated vector proves the library.

So the exact API shape R4 says has been structurally removed still exists in the
active B2 module.

Required closure: remove the public function, make it an unmistakable
fixture-only helper, or make every production/consumer path structurally unable
to resolve it.  The active suite must contain a red attack using all-correct
labels plus fabricated values and require refusal.

## Defect B — the safe raw-source proof is not consumed by technical completeness

`t0_technical_completeness_authority_v1` never consumes an
`AuthenticatedSource`, raw-source proof object, or externally expected
`raw_source_proof_root`.  Q_DEPTH is computed directly from
`logical["rows"][i]["source_library"]` after recomputing the logical root.

That proves the metadata value is bound by the logical object; it does not prove
the value was derived from the authenticated H5 row.  R4's three-row real-asset
spot check proves mechanics for three rows, not the 20,804-row population.

Required closure: build a population-level raw-source authority over every logical
row, externally bind the logical root and source digest, require exact cardinality
and row identity, then require technical completeness to consume that authority
(or derive Q_DEPTH in the same authenticated operation).  A logical root built
around invented source_library values must not be sufficient.

## Defect C — the authentication token is forgeable in-process

`_HANDLE_TOKEN` is a normal Python module attribute.  A caller can use

```
AuthenticatedSource(_HANDLE_TOKEN, ...)
```

with a fabricated H5 handle and a claimed frozen digest.  The current negative
test passes `object()`, not the actual accessible module token.

This makes the token a convention, not an authentication capability.

Required closure: do not rely on a secret Python object for provenance.  The
production proof should own authentication and consumption itself, ideally from
one file descriptor/file object that the caller cannot replace with a labelled
handle.

## Defect D — hash/open is a check-then-use gap

`open_authenticated_source` hashes one open of the path, closes it, then calls

```
h5py.File(str(asset), "r")
```

which reopens the path.  A path replacement between those operations makes the
H5 handle refer to bytes different from the bytes whose SHA was recorded.

Required closure: open once, hash through that same descriptor/file object, seek
back, and give that same object/descriptor to HDF5; or otherwise prove file
identity/inode/content continuity across authentication and use.

## Defect E — production Q_DETECT geometry is permissive by default

`derive_rows_from_authenticated_parents(...,
expected_projection_positions=None)` and
`build_production_authority(..., expected_projection_positions=None)` allow a
small projection to be accepted, while Q_DETECT is still divided by 35,076.

This is already acknowledged in the R4 handoff and is a production gap.

Required closure: the production entrypoint must unconditionally require exactly
35,076 distinct in-range B1 projection positions.  Any small-projection support
belongs in a private fixture helper.

## Defect F — technical completeness fabricates a physical-plan parent identity

The production builder does not accept or verify a physical plan, yet constructs:

```
physical_read_plan_root_sha256 =
    logical.get("physical_read_plan_root_sha256")
    or expected_logical_root_sha256
```

The normal logical authority does not carry the physical-plan root, so the
fallback records the logical root under a different parent name.  That is a
well-formed but false parent identity.

Required closure: either remove the physical plan from this authority's parent
contract if it is genuinely not a dependency, or accept the physical plan and
establish stored == recomputed == externally expected using
`assert_physical_plan_lawful`.  Never substitute another root.

## Defect G — estimability preflight root does not bind the records it checked

The donor-keyed stage functions correctly compare a `records_root`, but
`preflight_root` hashes only the stage name and rank checks.  It ignores the
records root, donor order, residual df and tail inference n.

Thus two different donor-bound designs with the same ranks produce the same
preflight root.

Required closure: bind each stage's externally checked records root and exact
donor order (or an authority root that fixes it), plus all decision-bearing stage
outputs, into the preflight root.  Add a test that changing only
`records_root_sha256` moves `preflight_root`.

## Defect H — manifest nnz is bound but not closed against payload bytes on the production chain

`build_population_closure` requires and binds `nnz`, but it does not receive
counts payload bytes and therefore cannot compare the declaration to the actual
CSR payload.  `verify_block_row_from_authenticated_payload` can compare
`declared_nnz`, but that argument is optional and technical completeness calls
the verifier without `declared_rows` or `declared_nnz`.

Required closure: carry authenticated block geometry from the closure into every
counts-payload consumption path and require the verifier to compare both rows and
nnz.  The comparison should not be optional in a production entrypoint.

## Independent red evidence

Review branch:

```
review/t0-r4-independent-reds-20260909
ceaef0565ea1e9ab935cd7346eaf8c57b5bca4e1
```

File:

```
tests/v4/test_t0_r4_independent_external_reds_v1.py
```

The file preserves attacks for:
- legacy fabricated-vector acceptance;
- forgeable module token;
- Q_DEPTH without population raw-source proof;
- permissive projection geometry;
- fabricated physical-plan parent root;
- preflight root omitting records identity;
- two-open hash/use source authentication.

## What may remain credited from R4

The following are meaningful improvements and should be preserved:
- real 33 GB source asset SHA/geometry spot check;
- byte-to-row H5 reader mechanics;
- pathology-blind obs-field restriction;
- donor-keyed estimability stage inputs;
- logical/closure/projection root checking in technical completeness;
- required manifest rows/nnz columns and closure-root binding;
- explicit standing terminals and honest 556-case accounting.

None of these should be discarded while closing the defects above.

## Gate decision

Do not start eligible-donor construction and do not run production B2 from this
candidate.  A successor should close A-H, preserve the standing terminals, run
red-before against b08d02f7, and return for independent re-review.
