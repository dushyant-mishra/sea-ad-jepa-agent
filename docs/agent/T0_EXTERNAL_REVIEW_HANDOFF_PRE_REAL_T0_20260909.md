# T0 external review handoff — before the real T0 run

    STOP_BEFORE_REAL_T0_RUN__ALL_PATHOLOGY_BLIND_AUTHORITIES_READY_FOR_EXTERNAL_REVIEW

Branch `t0/v20-pathology-blind-materialization-20260908`.
Sealed base `21ec629667eeda5a7d37d3f1d822fbf93b213325` is untouched and remains
ancestral.

## What this asks of the reviewer

Every pathology-blind authority T0 depends on has now been built over the real
data and replayed. Real T0 has **not** been run. This handoff asks whether the
authority chain is sound enough to authorize that run — not whether any result
is real, because no result exists.

## State

    B2 real population authority       DONE AND REPLAYED
    technical completeness             DONE AND REPLAYED
    eligible donor authority           DONE AND REPLAYED
    numeric confirmation AT8           NOT ACCESSED
    real_execution_ready               False
    real T0 execution                  NOT RUN
    DEV / SEALED                       NOT OPENED
    teacher-student training           NOT BEGUN
    self-promotion to PASS             none

## The chain, root by root

Sources:

    membership              d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529
    complete manifest       66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
    MTG H5AD (32,978,570,763 B)
                            e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79
    B1 feature authority    538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8

B2 substrate and population, unchanged from DEC-024 and reproduced again by both
replays run today:

    population closure      ec350b8d9a30a8a08573f055b9a0c103d0f6805014998ac9975d94585421d397
    logical row authority   64ea880ff6cf19aca48e0f2e77edfa6d37fc4f5e20022011131c496173896fc3
    physical read plan      cc75cef0ebb9a05e6699546e18ae45b3555f488dc2e46db4c845370c5be23519
    population raw-source   0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
    B2 authority package    98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436

New today:

    projection root         ef6ccdde0e0268cce819b4e543d7d542120811fa3762225964f78f9172f370e7
    completeness root       360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    TC parent contract      9d4e818e20077c42c5500b4df35c385dd1a43cb53375da3a7b4d738257ff5ba5
    TC package root         0164bccc76ad7ed9385de01fd0ab885dd80770afad0b94ee189e9084ee3cfe99
    eligible donor root     a5470b9f5389e0fa72b3ca51832c67d7419ed6447a85d6d979884b9fe1444f85
    donor role root         799261f54de158f4c24c33a51a674611fe4e5e68509fcbbca681216470fe10bd
    ED parent contract      be92b2ac2b347f0da45690e264d1b224584cfb56131ac3df61a01480ad196ae8
    ED package root         af4b71413917cde7dd6b35686b3f8410e94ee323d436a2f4e125ff91b06980fd

Sizes, per-member digests and reproduction commands are in
`T0_TECHNICAL_COMPLETENESS_AND_ELIGIBLE_DONOR_ARTIFACT_MANIFEST_20260909.md`.

## The design, as it actually came out

    candidate donors    46      from the proven B2 population
    eligible donors     46
    CONFIRMATION        18
    DISCOVERY           28
    cells               20,804

    CONFIRMATION tail-measurable   18 of 18
    DISCOVERY tail-measurable      27 of 28   (H20.33.037, 67 cells)

Frozen `tail_allowed_n` is `[17, 18]`, so the confirmation tail analysis is
executable at n = 18. The frozen design needs 18 CONFIRMATION plus at least 18
DISCOVERY; it has 18 and 28.

Eligibility turned entirely on `technical_complete`, because AT8 availability,
age presence and sex presence are all True for every one of the 46 candidates.
All 46 came out technically complete.

## The scope question, now decided by the owner

I flagged that the eligible-donor authority emits a `donor_role` column, since
the lane tracks `donor_roles_computed` as a gated marker and an earlier
instruction was to keep the donor-role STOP closed. The owner ruled on
2026-09-09 that it is in scope for this package and that it must not be re-cut to
remove the column; instead its meaning is narrowed in documentation.

### `donor_role`, scoped by owner decision

The owner ruled on 2026-09-09 that `donor_role` is in scope for this pre-real-T0
review package: the work order asked for the eligible-donor authority, the split
is deterministic over the eligible set, and it consumes no numeric AT8. **The
package was not re-cut**, so no root moved. The narrowing is documentary:

    donor_role  =  a deterministic pre-real-T0 eligible-set split
    donor_role  != the frozen t0_donor_role_authority_v2 package
    donor_role  != any real-T0 execution authorization

What it is not, concretely. It is not the frozen `t0_donor_role_authority_v2`
package, which additionally runs nuisance-design rank checks over the
confirmation set, the discovery set and every discovery LOODO fold; those need
age and sex *values* that this authority deliberately does not carry, so they
have not been run on production data. It does not lift
`STOP_T0_DONOR_ROLE_AT8_AVAILABILITY_AUTHORITY_UNBOUND`, which remains in
`unresolved_blockers`. And it does not authorize real T0.

The owner also ruled against re-stamping the lane for the provenance mislabel in
finding 2 below, before external review: the digest values are reproducible and
CRLF-safe, only the method label is false, and re-stamping would move package
roots already cited including B2 and force cascading replays. That is an
external-review decision rather than another producer-side churn cycle. The
finding stays visible and explicit.

## Findings I am reporting rather than resolving

### 1. The two frozen role modules are not equivalent

    t0_discovery_confirmation_split_v2.generate(support)
        ranks every SEA_AD op31 support donor and takes the first 18
    t0_donor_role_authority_v2.build_role_authority(support, metadata)
        ranks only the metadata-complete donors and takes the first 18

They agree only when every support donor is eligible. If an ineligible donor
ranks inside the top 18 of the full support set, they disagree on who is
CONFIRMATION. `generate()`'s own comment says confirmation is "selected from all
eligible donors", which is the role authority's behaviour, not `generate()`'s.

The role authority is the binding one: it writes a package, re-derives the
assignment on load, and refuses a registry that does not match. The new
eligible-donor authority reproduces that rule, records
`RANK_ELIGIBLE_DONORS_ONLY__NOT_ALL_SUPPORT_DONORS` in its metadata, and
`split_rule_divergence()` measures the disagreement on the real donor set rather
than arguing about it.

**On today's data the two paths agree**, because all 46 donors are eligible and
so the two rankings are over the same set. The latent inconsistency is
unexercised, not absent. It should be resolved in the frozen modules before any
future run where a donor is ineligible.

### 2. A lane-wide provenance mislabel

Every package in this lane records the plain SHA-256 of its derivation module's
LF-normalized content while declaring
`derivation_code_byte_semantics: GIT_BLOB_BYTES__NOT_WORKTREE_BYTES`. A Git blob
digest frames content as `b"blob <len>\0" + content` and is a different value:

    recorded in the TC package  64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49
    sha256 of LF content        64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49
    sha256 of blob framing      6045f84cd1ea7f642f2b91b15756be7e3bb9bdd97fd53224f88f1d04b6f81c4d
    git hash-object             0e8c701b5213a36fc7983b0c6890c93514eb2e9d

The same holds for the B2 population raw-source, AT8 availability and age/sex
packages. The digest values are correct, reproducible and CRLF-safe; only the
one-word method claim is false. The `T0_B2_PRODUCTION_ARTIFACT_MANIFEST` doc
repeats the same wrong description.

The practical risk is a reviewer computing a Git blob digest, getting a
mismatch, and concluding the packages are broken.

Scope note, so this is not read more widely than it should be. The finding is
about the `derivation_code_byte_semantics` field in the T0 authority packages
only. It is *not* about `work_checkpoint`, whose `bytes_authority` states
`GIT_BLOB_BYTES_PLATFORM_INDEPENDENT` and which genuinely does validate tracked
authorities from the immutable Git blob — that was implemented deliberately and
the label there is accurate. Two different mechanisms, one of which is
mislabelled.

The eligible-donor lane now states the method accurately. The other seven
modules are left alone deliberately: correcting them changes their
`derivation_code_sha256` and therefore their package roots, for artifacts
already produced and cited in DEC-024 — including B2, whose re-run means
re-hashing the 33 GB asset. **Whether to re-stamp the lane is the owner's call.**

### 3. The derivation ignores the read plan it builds

Measured against the 1,246 op31 counts blocks totalling 7.35 GB:

    walk order / cache        block loads   bytes read
    no cache                       19,953    114.84 GB
    LRU(48), what ran               3,126     18.35 GB
    block-major locality            1,246      7.35 GB

The frozen membership order is almost perfectly interleaved — 19,953 contiguous
runs across 20,804 rows. The run's own counter recorded exactly 3,126 payload
reads. `build_physical_read_plan` exists to supply block locality and is not
used for the walk, so the run pays 2.5x the I/O and CPU it needs to.

This is efficiency, not correctness: per-row work is order-independent, rows are
keyed by `logical_index`, and the donor reduction uses `math.fsum`, which is
exactly rounded and so depends only on the multiset of per-cell values. A
block-major walk would produce identical roots. Not changed, with a production
run in flight at the time.

## Defects I found in my own work today and fixed

Each was found by reading my own output or attacking my own tests, not by
review. Listing them because a governance lane's value is that its failures are
visible.

1. **A 40-character SHA-1 recorded as `_sha256`.** The first real eligible-donor
   build recorded `ee1253309c7e23f48f63f2a1b35f55b6263f5207`, because the runner
   shelled out to `git hash-object`. The package was internally consistent and
   nothing in it revealed the mislabelling. `build_authority` now refuses any
   `derivation_code_sha256` that is not a lowercase 64-character hex digest.

2. **Three loader gaps, each describing a package that is self-consistent under
   every digest it publishes and still wrong.** `eligible` was never checked
   against the conjunction of its own row's flags; the manifest was never
   reconciled against the member bytes on disk; metadata counts, role counts and
   the confirmation floor were never checked against the registry they
   summarise. All three are now checked, on write and on load.

3. **My own mutation tests were not reaching the checks their names claimed.**
   Mutating a member breaks the manifest, the package root and the member's own
   assertion at once, so the outer check fired and the inner one was never
   exercised. They now restamp the manifest first, and the two tests that share
   `STOP_ROLE_RULE` assert on distinguishing message text so it is clear which
   check fired.

4. **`_boolean` accepted the string `"True"` in derivations.** The loader needs
   the textual form because CSV has no booleans; a derivation must not have it,
   or an unparsed CSV column could decide eligibility. Now opened by the loader
   alone, with both directions pinned by test.

5. **Roles were not re-derived on load.** The loader recomputed each
   `split_hash` but read `donor_role` off the row, so a role-swapped registry
   with recomputed digests would have passed. Now re-derived on write and load.

## Corrections to my own earlier statements

- The producer suite baseline was **561**, not the 577 I carried forward. With
  the two new suites it is **652**. The R4 independent reviewer suite is
  unchanged at 6 passed / 1 failed, that failure being the previously reported
  mutual contradiction between its tests 3 and 5.
- The `SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN` terminal is retired and confirmed
  absent from the first real TC package, whose status was decided by measured
  coverage rather than a flag.

## Verification the reviewer can run

    python -m pytest tests/v4/test_t0_*.py -q      # name the T0 suites explicitly;
                                                   # a bare tests/v4 glob pulls in
                                                   # unrelated files that error at import

Two strengths of TC replay are available. The default verifies that the package
agrees with itself and with the parents on disk. `--rederive` walks the
substrate again and recomputes every donor's Q_DEPTH, Q_DETECT, cell count and
completeness flag from authenticated bytes, comparing field by field — the only
mode that shows the numbers reproduce rather than that the digests are
consistent. It costs a second full pass over the counts store.

## The independent re-derivation

Ran to completion under a corrected comparison. It walks the substrate again and
recomputes every donor's Q_DEPTH, Q_DETECT, cell count and completeness flag
from authenticated bytes.

    donors compared                46
    field comparisons             184
    payload reads / cache hits    3,126 / 17,678   (identical to the production run)
    re-derived completeness root  360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    stored completeness root      360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470

    TECHNICAL COMPLETENESS REPLAY PASS (INDEPENDENTLY RE-DERIVED)

So the numbers reproduce from authenticated bytes, not merely the digests from
themselves.

Two corrections to my own verifier, both found by reading its output rather than
by review, and both of the same shape as the provenance defects above -- a check
that reported the wrong thing while appearing to work.

The first run failed on identical numbers. It compared the package's twelve-place
rendering `8.388476413096` against the fresh value's full repr
`8.388476413095692` and called them different. The writer renders through
`"%.12f"` and the root frames through `_typed_float(places=12)`, so twelve places
is the precision at which this authority defines the quantity; comparing there is
exact rather than tolerant.

The second is a metric that could not do what its name said. I had reported a
"largest raw float delta below the recorded precision" of 4.973799150320701e-13
as though it bounded re-derivation drift. It does not: it compares the stored
twelve-place string against the fresh float, so it measures the *write's*
quantization error, and once the strings agree it lies in [0, 5e-13) by
construction. It can never detect drift. It is now labelled a quantization check
and its half-last-place bound is asserted rather than merely printed.

What follows from that, stated plainly: **re-derivation drift below 1e-12 is not
observable from this artifact**, because the artifact retains twelve places and
nothing finer. Root equality is the statement about reproduction, and it holds.

## What must not happen next without explicit authorization

Do not run real T0. Do not access numeric AT8 or pathology values. Do not open
DEV or SEALED. Do not set or bypass `real_execution_ready=True`. Do not begin
teacher-student training. Do not self-promote any authority to PASS.
