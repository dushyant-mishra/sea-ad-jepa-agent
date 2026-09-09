# T0 external-review handoff — R5

Successor candidate closing the eight findings of the R4 independent review.

## Standing terminal statements

    PRODUCTION_B2_NOT_RUN
    DONOR_ROLE_GATE_SHUT
    real_execution_ready=False
    NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED

No authority is self-promoted to PASS. Eligible-donor construction is not started.

## The claim being withdrawn

R4 said the fabricated-vector `source_library` API had been "structurally
eliminated" and that B2 defects A–I were closed. That was false as stated. R4
added a safe byte-to-row prover **beside** the unsafe one and left the unsafe one
public — and its own positive test built `[0] * 36_600 + [bound]` and asserted
that the fabricated vector *proved* `source_library`. So the API said to be gone
was reachable and green. The review was right to treat this as a hard STOP.

## Base and review inputs

    R5 base       b08d02f721636eeba43c8612f934e816deec5f05
    sealed base   21ec629667eeda5a7d37d3f1d822fbf93b213325   (unchanged, ancestral)
    disposition   STOP_T0_R4_INDEPENDENT_REVIEW__SAFE_RAW_SOURCE_MODULE_NOT_CLOSED_INTO_EXECUTION_CHAIN
    review branch review/t0-r4-independent-reds-20260909
    review head   f7d8dfb537c1052c656c8bb194f6e154b200086a
    red commit    ceaef0565ea1e9ab935cd7346eaf8c57b5bca4e1

The independent red file was taken **unmodified** from the review branch and run
against the base: **7 of 7 failed**. It is committed here unchanged so the same
run is reproducible.

## The eight findings

**1 · Unsafe prover removed.** `prove_source_library` now always raises
`STOP_T0_B2_CALLER_VECTOR_SOURCE_LIBRARY_PROOF_REMOVED` and names its
replacement. Its seven cases — including the positive one asserting a fabricated
vector passes — are replaced by three asserting the removal across every call
shape. The behaviours the old block covered are exercised against real
authenticated bytes in the raw-source suite.

**2 · Population-level raw-source authority.** `prove_population_from_source_path`
proves **every** accepted logical row from real bytes and binds the exact row
cardinality, the logical root and the source digest.
`assert_population_authority_covers_logical` refuses a proof set that is short,
covers other rows, or whose root does not verify stored == recomputed ==
externally expected. Technical completeness consumes it and takes `Q_DEPTH` from
the **proven** library, not the stored one — recomputing the logical root shows a
value is bound, not that it came out of the H5 row.

**3 · Token demoted.** The module-level sentinel was an ordinary importable
attribute, so it was never a capability. It is now explicitly refused
(`STOP_T0_RAW_SOURCE_LEGACY_TOKEN_IS_NOT_AN_AUTHENTICATION_CAPABILITY`), the real
construction guard is created inside the private opener and is unreachable as a
module attribute, and `AuthenticatedSource` re-derives the digest from the bytes
on the way in — so even a caller reaching the constructor cannot claim a digest
the file does not have. `prove_population_from_source_path` takes a path and no
caller-built handle at all.

**4 · Hash/reopen gap closed.** `_digest_fileobj` hashes the open stream and
rewinds it, and that **same object** is handed to `h5py.File(stream, "r")`. One
open, not two.

**5 · Projection mandatory.** `expected_projection_positions` defaults to 35,076
in both the derivation and the production entrypoint. Small projections are
fixture-only and must say so.

**6 · No fabricated physical parent.** The fallback that recorded the logical root
under the name `physical_read_plan_root_sha256` is gone. A physical read plan is
required and verified three ways, because it is what determines which counts
payloads are read.

**7 · Preflight root binds decisions.** It now binds every records root present
on the stage, the donor-bound flag, the residual degrees of freedom, the tail
inference n and the LOODO fold ranks. Previously it hashed only stage names and
ranks, so different donor-bound designs with identical ranks collided.

**8 · Counts geometry mandatory.** Technical completeness requires the
authenticated closure and passes its bound `rows` and `nnz` into the payload
verifier on the production path, so declaration and payload are obligatorily
reconciled rather than through optional arguments.

## A contradiction in the independent suite, reported not worked around

Two of the seven cases cannot both hold.

- `test_technical_completeness_must_require_raw_source_proof_for_q_depth`
  requires `build_production_authority` to **raise**.
- `test_technical_completeness_must_not_invent_a_physical_plan_parent`
  requires the same call to **succeed**.

Their inputs were verified identical: the same eight kwargs, the same
one-position projection, the same `source_library` of 9999, and neither supplies
a raw-source proof.

The work order sides with the raise — item 2 requires a population raw-source
proof and item 5 requires the full projection — so that is what is implemented.
**Six of seven independent reds are green**; the physical-plan case fails on this
contradiction. Its *intent* is preserved by
`test_the_physical_plan_parent_is_the_verified_plan_not_the_logical_root`, which
asserts the substrate records the verified plan root and not the logical root,
under the lawful contract.

If the reviewer wants that case green as written, one of items 2 or 5 has to be
relaxed, and I would rather not relax either without being told to.

## Suite counts

Kept separate from the earlier accountings: R3 was 482 across twelve, R4 was 556
across thirteen. R5 is **577 across thirteen producer suites**, plus the
reviewer's 7-case file.

| suite | R4 | R5 |
|---|---|---|
| `test_work_checkpoint_v1` | 33 | 33 |
| `test_t0_at8_availability_authority_v1` | 32 | 32 |
| `test_t0_v20_feature_projection_authority_v1` | 38 | 38 |
| `test_t0_v20_row_count_authority_v1` | 50 | **46** |
| `test_t0_v20_row_count_authority_r2_red_v1` | 48 | 48 |
| `test_t0_input_dependency_contract_v1` | 56 | 56 |
| `test_t0_immune_fraction_authority_v1` | 47 | 47 |
| `test_t0_immune_fraction_authority_r2_v1` | 26 | 26 |
| `test_t0_immune_support_count_authority_v1` | 35 | 35 |
| `test_t0_age_sex_authority_v1` | 50 | 50 |
| `test_t0_technical_completeness_authority_v1` | 64 | **69** |
| `test_t0_estimability_preflight_v1` | 42 | **49** |
| `test_t0_raw_source_row_authority_v1` | 35 | **48** |
| **producer total** | **556** | **577** |
| `test_t0_r4_independent_external_reds_v1` | — | 7 (6 green) |

Two counts went **down or sideways** for reasons worth stating plainly:
`row_count` fell 50 → 46 because seven cases exercising the removed prover were
replaced by three asserting the removal. `technical_completeness` rose 64 → 69
after **retiring six** pre-R5 detached-value derivation cases — they called the
derivation with no population proof and no closure geometry, so keeping them
would have meant weakening the requirement the review asked for — and adding
eleven lawful-contract cases.

No CI is attached, so counts should be reproduced rather than trusted.

## Known limitations

- The population raw-source authority has run on synthetic H5AD fixtures and on a
  three-row spot check of the real 33 GB asset. It has **never** run over the real
  20,804-row population, because that needs the production B2 substrate, which is
  forbidden. Closure over the real population remains unproven.
- Technical completeness and the estimability preflight have no production run.
- The lawful production fixture uses a full 35,076-position projection but only
  three cells, so the projection size is exercised while the population size is
  not.
- No eligible-donor authority exists; 46 donors remain the candidate upper bound.
- No CI.

## What to attack next

Whether any path still reaches a `source_library` value that was not proven from
bytes — particularly whether `_build_rows_from_values` or
`_build_authority_from_values` can be reached from anything a production caller
touches. Then whether the construction guard can be obtained by any import,
subclass or pickle route. Then whether the population authority can be satisfied
by a proof set that covers the right cardinality with the wrong rows.
