# T0 external-review handoff — R4

Successor candidate for independent implementation review. It repairs the four
gaps the R3 review found and does not begin eligible-donor construction, which
remains the next work item only after this candidate passes review.

## Standing terminal statements

    PRODUCTION_B2_NOT_RUN
    DONOR_ROLE_GATE_SHUT
    real_execution_ready=False
    NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED

No authority is self-promoted to PASS.

## The correction this candidate answers

The R3 handoff claimed "B2 defects A–I closed". That was too strong, and the
review was right to call it a hard STOP rather than a documentation issue. The
authenticated-NPZ path was materially repaired, but:

- `prove_source_library` authenticated **labels a caller supplied**, not bytes it
  had read. A fabricated vector with the correct sum, the correct frozen source
  digest string, the correct cell and donor identity, the correct
  `expression_row`, the correct width and the correct `layers/UMIs` label proved
  `source_library`.
- technical completeness had the same detached-value shape: `cells_by_donor`
  carried `(source_library, projected_nonzero_count)` pairs while `substrate` was
  only parent-root **strings**, which named the parents without binding the
  values.

Both are now byte- and object-authenticated.

## Branch and ancestry

    branch      t0/v20-pathology-blind-materialization-20260908
    sealed base 21ec629667eeda5a7d37d3f1d822fbf93b213325   (unchanged, ancestral)
    R4 base     ab61cf5599663c417d2b2c5ef95ca7e5a37a312c
    successor   see the commit carrying this document

## Repair 1 — raw-H5 byte-to-row authentication

New module `scripts/v4/t0_raw_source_row_authority_v1.py`.

`prove_source_library_from_authenticated_source` takes **no values parameter at
all**. There is no door through which a caller-created vector can enter; that is
structural, not a check that could be skipped. It:

1. digests the whole asset and compares it to the frozen identity, before opening;
2. opens `layers/UMIs`, requires `encoding-type == csr_matrix`, and checks shape;
3. selects the bound `expression_row`;
4. requires `obs` at that row to carry the bound cell and donor identity;
5. requires the stored values to be non-negative and integral;
6. **computes** `source_library` from that row and compares it to the bound value.

`AuthenticatedSource` carries a module-private token that only
`open_authenticated_source` supplies, so a look-alike object claiming the right
digest is refused. `refuse_caller_supplied_values` gives a named STOP if the
removed parameters ever return.

**Verified against the real 33 GB asset**, not only synthetic fixtures:

    asset      SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad
    bytes      32,978,570,763  — all hashed, in 222.6 s
    sha256     e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79  matched
    geometry   1,178,694 x 36,601 from layers/UMIs  matched

    PROVEN  expression_row  170190  donor H19.33.004  stored  7943  library   48642
    PROVEN  expression_row  548283  donor H19.33.004  stored  3667  library   10123
    PROVEN  expression_row  172231  donor H19.33.004  stored 10096  library  100878

    raw_source_proof_root  4d450d6c650c2e0b0122c8f799329b8b21d2fe7496d0082b56f25f88157f2d5d

    negative control: a bound library off by one is refused on real bytes.

`obs` reads are confined to `exp_component_name` and `Donor ID`. The asset's
`obs` also carries Braak, Thal, CERAD score and other pathology columns; none is
read, and `assert_no_pathology_read` refuses a widened field set.

This was a read-only spot check of three rows. It materialized nothing and is
**not** a production B2 run.

## Repair 2 — technical completeness derives from authenticated parents

`build_production_authority` now takes the authenticated B2 logical row
authority, the counts payload bytes each logical row's own `counts_sha256`
authenticates, and the B1 projection, with the logical root, the closure root and
the projection root all externally bound. `source_library` is read off the
authenticated logical row; the projected non-zero count is computed from the
authenticated payload through the bound projection. Each donor summary records
the cell identities it consumed, and the completeness root binds them.

`cells_by_donor` and the bare `substrate` mapping are gone from the production
path, `refuse_detached_values` names the STOP if they return, and the
values-based builder survives only as `_build_rows_from_values`.

The attack the review asked for is
`test_genuine_parent_roots_with_forged_values_cannot_produce_an_authority`:
entirely genuine root strings accompanying the forged pair `(9470, 3000)`.

## Repair 3 — estimability inputs bound by donor identity

The array primitives aligned covariates by position only, so permuting one was
structurally valid and changed matrix rank. The production stages now key values
by donor, take the donor order from the role authority rather than from array
indices, and bind the whole record set with `records_root`, a typed digest over
every `(donor, field, value)` triple in authoritative order.

`test_permuting_a_covariate_cannot_rescue_a_non_estimable_design` is the case the
review specified. With `STATE_SCORE` exactly equal to `Q_DEPTH` the correctly
aligned measurement design is rank deficient, which is the truth about it. The
test then rotates `STATE_SCORE` across donors, shows that the permuted design
**would** be full rank (rank 7 of 7), and requires the permutation to be refused
on the records digest rather than reported as estimable.

## Repair 4 — manifest geometry required, verified and root-bound

`rows` and `nnz` are now required manifest columns. The declared row count is
checked against the authenticated metadata unconditionally — it was previously
behind a presence test, so omitting the column skipped the check that consumed
it. `nnz` was carried and never used; the counts payload verifier now compares
the stored value count against it. Both are bound into the population closure
root, so a mutated manifest geometry moves the root.

## Suite counts

Kept separate from the R3 accounting, as requested. The R3 candidate was **482
across twelve suites**; this candidate is **556 across thirteen**.

| suite | R3 | R4 |
|---|---|---|
| `test_work_checkpoint_v1` | 33 | 33 |
| `test_t0_at8_availability_authority_v1` | 32 | 32 |
| `test_t0_v20_feature_projection_authority_v1` | 38 | 38 |
| `test_t0_v20_row_count_authority_v1` | 50 | 50 |
| `test_t0_v20_row_count_authority_r2_red_v1` | 36 | **48** |
| `test_t0_input_dependency_contract_v1` | 56 | 56 |
| `test_t0_immune_fraction_authority_v1` | 47 | 47 |
| `test_t0_immune_fraction_authority_r2_v1` | 26 | 26 |
| `test_t0_immune_support_count_authority_v1` | 35 | 35 |
| `test_t0_age_sex_authority_v1` | 50 | 50 |
| `test_t0_technical_completeness_authority_v1` | 51 | **64** |
| `test_t0_estimability_preflight_v1` | 28 | **42** |
| `test_t0_raw_source_row_authority_v1` | — | **35** |
| **total** | **482** | **556** |

74 new cases: 35 raw-source, 13 technical completeness, 14 estimability, 12
manifest geometry.

No CI is attached to these commits, so a reviewer cannot use a status check as
evidence and should reproduce the counts.

## Red-before evidence

Each changed module was replaced by its `ab61cf55` version, the affected suite
run, and every module restored with a digest check (`exact=True` for all four).

| attack set | against ab61cf55 | now |
|---|---|---|
| raw-H5 byte-to-row | 1 collection error — the module does not exist at base | 35 green |
| technical completeness detached values | 24 failed / 40 passed | 64 green |
| estimability donor-keyed binding | 28 failed / 14 passed | 42 green |
| B2 manifest geometry | 14 failed / 34 passed | 48 green |

Being precise about those failure counts, because they are not all defect
reproductions. The genuinely new attack cases are 13, 14 and 12 respectively; the
remainder fail at the base because this candidate made three previously public
helpers private (`build_rows`, `build_authority`, the three array stages) and
changed two signatures, so the retargeted existing cases cannot resolve those
names at the base commit. The raw-source suite is wholly red at base because the
module is absent.

## Changed files

    scripts/v4/t0_raw_source_row_authority_v1.py            (new)
    scripts/v4/t0_technical_completeness_authority_v1.py    (modified)
    scripts/v4/t0_estimability_preflight_v1.py              (modified)
    scripts/v4/t0_v20_row_count_authority_v1.py             (modified)
    tests/v4/test_t0_raw_source_row_authority_v1.py         (new)
    tests/v4/test_t0_technical_completeness_authority_v1.py (modified)
    tests/v4/test_t0_estimability_preflight_v1.py           (modified)
    tests/v4/test_t0_v20_row_count_authority_r2_red_v1.py   (modified)
    docs/agent/T0_EXTERNAL_REVIEW_HANDOFF_R4_20260909.md    (new)

## Source identities

    MTG H5AD source            e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79
    MTG donor pathology table  ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a
    accepted immune membership d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529
    complete Phase2 manifest   66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29

## Known limitations

- The technical-completeness authority still has no production run, because that
  needs the authenticated B2 substrate and production B2 is not authorized. Its
  derivation path is exercised on synthetic CSR payloads only.
- The estimability preflight has no production run, because the donor-role gate is
  shut.
- `derive_rows_from_authenticated_parents` accepts
  `expected_projection_positions=None` by default, so a fixture may use a small
  projected position set. A production call must pass 35,076; that is not yet
  enforced by default and a reviewer should treat the default as permissive.
- Opening the authenticated source costs a full 33 GB read (~223 s here). The
  handle is reused across rows within a run, and `digest_bytes_read` distinguishes
  a real authentication from a skipped one.
- No eligible-donor authority exists. The 46 donors remain the candidate upper
  bound.
- No CI.

## What a reviewer should attack next

Whether any path reaches a `source_library` proof without an
`AuthenticatedSource`, and whether the token guard can be bypassed. Then whether
`derive_rows_from_authenticated_parents` can be driven with a projection that
does not correspond to the bound feature authority. Then the records-digest
binding in the preflight, specifically whether a donor set can be reordered
without moving the digest.
