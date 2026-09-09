# T0 pre-real-T0 external review package

    STOP_BEFORE_REAL_T0_RUN__ALL_PATHOLOGY_BLIND_AUTHORITIES_READY_FOR_EXTERNAL_REVIEW

**Real T0 has not run.** No numeric AT8 or pathology value has been accessed. DEV
and SEALED have not been opened. `real_execution_ready` is False.
Teacher-student training has not begun. No authority is self-promoted to PASS.

Branch: `t0/v20-pathology-blind-materialization-20260908`
Sealed base `21ec629667eeda5a7d37d3f1d822fbf93b213325` untouched and ancestral.

Head history for this package, so a reviewer can tell the revisions apart:

    4552851d   the head the reviewer first inspected
    9ba6fd44   this package assembled; docs and reports only, no artifact rewritten
    82e0d75f   R6 closure: parent replay, Stage A preflight, provenance waiver
               (this line added in the immediately following commit, since a
               document cannot contain the digest of the commit that adds it)

The owner's two decisions of 2026-09-09 re-cut nothing and moved no root. The
subsequent R6 repairs, made at the external reviewer's direction, did move the
eligible-donor parent contract root and package root while leaving its decision
roots unchanged; that is set out under "Roots" and in
`docs/agent/T0_R6_CLOSURE_20260909.md`.

## What is in this package

Replay evidence, in this directory:

    B2_PRODUCTION_REPLAY_REPORT.json                             1,050 B
    TECHNICAL_COMPLETENESS_REPLAY_REPORT.json                    1,909 B
    TECHNICAL_COMPLETENESS_INDEPENDENT_REDERIVATION_REPORT.json  2,391 B
    ELIGIBLE_DONOR_REPLAY_REPORT.json                            3,844 B   (R6)
    ESTIMABILITY_PREFLIGHT_STAGE_A_REPORT.json                   3,779 B   (R6)

Manifests and state, elsewhere on the branch:

    docs/agent/T0_R6_CLOSURE_20260909.md
    docs/agent/T0_PROVENANCE_LABEL_WAIVER_20260909.md
    docs/agent/T0_B2_PRODUCTION_ARTIFACT_MANIFEST_20260909.md
    docs/agent/T0_TECHNICAL_COMPLETENESS_AND_ELIGIBLE_DONOR_ARTIFACT_MANIFEST_20260909.md
    docs/agent/T0_EXTERNAL_REVIEW_HANDOFF_PRE_REAL_T0_20260909.md
    docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json
    docs/agent/memory-os/DECISION_REGISTRY.csv        (DEC-025, DEC-026, DEC-027)

The data artifacts themselves are **not** committed. `outputs/` is gitignored
because committing a package member as tracked text lets the line-ending filter
rewrite its bytes, changing its SHA-256 and breaking the package root that member
is bound by — this already happened once in this lane, where a committed
availability package produced `a4424482…` on a fresh checkout instead of
`e49c4e93…`. Every artifact is named by exact path, byte size and SHA-256 in the
two manifests, with the commands to reproduce it.

## Status

    B2 real population authority      DONE + REPLAYED
    technical completeness            DONE + REPLAYED + INDEPENDENTLY RE-DERIVED
    eligible donor authority          DONE + REPLAYED + PARENTS REPLAYED (R6)
    Stage A estimability preflight    DONE (R6)
    real T0                           NOT RUN
    numeric AT8 / pathology           NOT ACCESSED
    DEV / SEALED                      NOT OPENED
    teacher-student training          NOT BEGUN
    real_execution_ready              False
    Stage A preflight                 RUN, all designs full rank
    Stages B and C preflight          NOT RUN, inputs do not exist pre-real-T0
    frozen donor-role authority v2    NOT BUILT

## Roots

Sources:

    membership              d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529
    complete manifest       66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
    MTG H5AD, 32,978,570,763 B
                            e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79
    B1 feature authority    538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8

B2 substrate and population — reproduced again at this head in 4.4 s, all three
substrate roots rebuilt from the frozen inputs:

    population closure      ec350b8d9a30a8a08573f055b9a0c103d0f6805014998ac9975d94585421d397
    logical row authority   64ea880ff6cf19aca48e0f2e77edfa6d37fc4f5e20022011131c496173896fc3
    physical read plan      cc75cef0ebb9a05e6699546e18ae45b3555f488dc2e46db4c845370c5be23519
    population raw-source   0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
    B2 authority package    98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436

Technical completeness:

    projection root         ef6ccdde0e0268cce819b4e543d7d542120811fa3762225964f78f9172f370e7
    completeness root       360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    parent contract root    9d4e818e20077c42c5500b4df35c385dd1a43cb53375da3a7b4d738257ff5ba5
    package root            0164bccc76ad7ed9385de01fd0ab885dd80770afad0b94ee189e9084ee3cfe99

Eligible donors, after the R6 parent replay. The decision is unchanged and only
the parent binding is stronger, which is the expected signature of R6 items 1
and 2:

    eligible donor root     a5470b9f5389e0fa72b3ca51832c67d7419ed6447a85d6d979884b9fe1444f85   unchanged
    donor role root         799261f54de158f4c24c33a51a674611fe4e5e68509fcbbca681216470fe10bd   unchanged
    parent contract root    620ada0b5d6a6d29b7e8303e277b1cb72a153dc4b700757777df1588a54e344e   moved
    package root            7d372603cb4833a2cba02a047f6f3f3e4ef680ab0c730b8693ccbd958ddfafeb   moved

Stage A estimability preflight:

    preflight root          bf9ee518d59053b3fe446c258c2606f318077b2f179ad73c45c4c6346030df27
    report digest           17a759e9a9e837e37f5a573deae0c4f898c55b69d50f49562ed301e38070071f
    CONFIRMATION rank 4, DISCOVERY rank 4, all 28 DISCOVERY LOODO folds rank 4

## The design as it came out

    candidate donors    46      from the proven B2 population, not a caller list
    eligible donors     46
    CONFIRMATION        18
    DISCOVERY           28
    INELIGIBLE           0
    cells               20,804

    donors  46   cells consumed 20,804   technically complete 46 of 46
    cells      min 67            median 387            max 964
    Q_DEPTH    min 8.19262711    median 8.62742084     max 8.9972022
    Q_DETECT   min 0.0578090262  median 0.0752486785   max 0.096597957

Every one of the four eligibility conjuncts is True for all 46 candidates, so
eligibility turned entirely on `technical_complete`, which came out complete for
all 46.

Tail measurability behaved as separately frozen, which is the point of having
frozen it separately:

    donors below the frozen 80-cell floor:  H20.33.037, 67 cells, DISCOVERY
    CONFIRMATION   n = 18,  tail-measurable 18
    DISCOVERY      n = 28,  tail-measurable 27
    frozen tail_allowed_n = [17, 18]  ->  confirmation tail executable at n = 18

H20.33.037 is `technical_complete = True` despite falling below the 80-cell
floor. That is correct: completeness is threshold-free definedness and
computability, and the 80-cell floor is tail measurability only.

## Owner decisions of 2026-09-09

### 1. `donor_role` stays, scoped narrowly

The owner ruled this in scope for the pre-real-T0 review package: the work order
asked for the eligible-donor authority, the split is deterministic over the
eligible set, and it consumes no numeric AT8. **The package was not re-cut**, so
no root moved. The narrowing is documentary, and it is this:

    donor_role  =  a deterministic pre-real-T0 eligible-set split
    donor_role  != the frozen t0_donor_role_authority_v2 package
    donor_role  != any real-T0 execution authorization

Concretely, what `donor_role` is *not*:

- It is not the frozen `t0_donor_role_authority_v2` package. That module also
  runs nuisance-design rank checks over the confirmation set, the discovery set
  and every discovery LOODO fold. Those need age and sex **values**, which this
  authority deliberately does not carry. That work belongs to the estimability
  preflight, whose Stage A has since been run at the external reviewer's
  direction: CONFIRMATION rank 4, DISCOVERY rank 4, and all 28 DISCOVERY LOODO
  folds rank 4. Running it does not build the frozen v2 package, and Stages B
  and C remain unrun because their inputs do not exist before real T0.
- It does not lift `STOP_T0_DONOR_ROLE_AT8_AVAILABILITY_AUTHORITY_UNBOUND`. That
  STOP remains in `unresolved_blockers` and its disposition is not treated as
  settled here.
- It does not authorize real T0.

### 2. The provenance label is reported, not re-stamped

The owner ruled against re-stamping the lane before external review. Re-stamping
would move package roots already cited, including B2, and force cascading
replays; that is an external-review decision rather than another producer-side
churn cycle. The finding stays visible and explicit, below and in the manifest.

## Known unresolved findings

### F1. The two frozen role modules are not equivalent

    t0_discovery_confirmation_split_v2.generate(support)
        ranks every SEA_AD op31 support donor and takes the first 18
    t0_donor_role_authority_v2.build_role_authority(support, metadata)
        ranks only the metadata-complete donors and takes the first 18

They agree only when every support donor is eligible. If an ineligible donor
ranks inside the top 18 of the full support set, they disagree on who is
CONFIRMATION. `generate()`'s own comment says confirmation is "selected from all
eligible donors", which describes the role authority's behaviour, not its own.

The role authority is binding: it writes a package, re-derives the assignment on
load, and refuses a registry that does not match. The eligible-donor authority
reproduces that rule and records
`RANK_ELIGIBLE_DONORS_ONLY__NOT_ALL_SUPPORT_DONORS`.

**On this data the two paths agree**, because all 46 donors are eligible and the
two rankings are therefore over the same set. The inconsistency is unexercised,
not absent. It should be resolved in the frozen modules before any run in which
a donor is ineligible.

### F2. A lane-wide provenance mislabel — values correct, method claim false

Every authority package records the plain SHA-256 of its derivation module's
LF-normalized content while declaring
`derivation_code_byte_semantics: GIT_BLOB_BYTES__NOT_WORKTREE_BYTES`. A Git blob
digest frames content as `b"blob <len>\0" + content` and is a different value.
Measured on the technical-completeness authority module:

    recorded in the package  64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49
    sha256 of LF content     64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49   <- match
    sha256 of blob framing   6045f84cd1ea7f642f2b91b15756be7e3bb9bdd97fd53224f88f1d04b6f81c4d
    git hash-object          0e8c701b5213a36fc7983b0c6890c93514eb2e9d

The same holds for the B2 population raw-source, AT8 availability and age/sex
packages. `T0_B2_PRODUCTION_ARTIFACT_MANIFEST_20260909.md` repeats the same wrong
description in prose.

The digest **values** are correct, reproducible and CRLF-safe. Only the one-word
method claim is false. The practical risk is a reviewer computing a Git blob
digest, getting a mismatch, and concluding the packages are broken.

The eligible-donor lane and the estimability preflight state the method
accurately. The other six modules are untouched by owner decision, and R6 item
5 is closed by an explicit waiver record at
`docs/agent/T0_PROVENANCE_LABEL_WAIVER_20260909.md`, which carries the scope, the
re-stamp cascade, five conditions and the recommended correction. That waiver is
recorded by the producer at the owner's instruction and does not assert reviewer
acceptance.

Scope note so this is not read too widely: the finding concerns
`derivation_code_byte_semantics` in the T0 authority packages only. It does *not*
concern `work_checkpoint`, whose `bytes_authority` of
`GIT_BLOB_BYTES_PLATFORM_INDEPENDENT` is accurate — that lane genuinely validates
tracked authorities from the immutable Git blob. Two different mechanisms, one
mislabelled.

### F3. The derivation ignores the read plan it builds

Measured against the 1,246 op31 counts blocks totalling 7.35 GB:

    walk order / cache        block loads   bytes read
    no cache                       19,953    114.84 GB
    LRU(48), what ran               3,126     18.35 GB
    block-major locality            1,246      7.35 GB

The frozen membership order is almost perfectly interleaved — 19,953 contiguous
runs across 20,804 rows. The run's own counter recorded exactly 3,126 payload
reads, matching the model. `build_physical_read_plan` exists to supply block
locality and is not used for the walk, so the run pays 2.5x the I/O and CPU it
needs to.

Efficiency, not correctness: per-row work is order-independent, rows are keyed by
`logical_index`, and the donor reduction uses `math.fsum`, which is exactly
rounded and therefore depends only on the multiset of per-cell values. A
block-major walk would produce identical roots. Unchanged.

### F4. Standing items from earlier reviews

    STOP_T0_DONOR_ROLE_AT8_AVAILABILITY_AUTHORITY_UNBOUND      unresolved
    frozen donor-role authority v2 package                     not built
    Stages B and C of the preflight                            not run, inputs absent
    R4 independent reviewer suite tests 3 and 5                mutually contradictory
    no CI attached                                             suite counts must be reproduced

The R4 contradiction was verified on identical inputs — the same eight kwargs,
the same one-position projection, the same `source_library` of 9999 — where one
case requires `build_production_authority` to raise and the other requires the
same call to succeed. It was reported rather than worked around; the work order
sided with the raise, and the other case's intent is preserved by a replacement
assertion.

## Defects found in my own work during this lane

All were found by reading emitted values or attacking my own tests, not by any
test failing. Listed because a governance lane's value is that its failures are
visible, and because the pattern matters more than the individual items.

Provenance, in artifacts that were internally consistent throughout:

1. A 40-character Git SHA-1, `ee1253309c7e23f48f63f2a1b35f55b6263f5207`, recorded
   under `derivation_code_sha256`. `build_authority` now refuses any code
   identity that is not a lowercase 64-character hex digest.
2. The Git-blob method label, F2 above.

Authority checks that would have admitted a self-consistent but wrong package:

3. `eligible` was never checked against the conjunction of its own row's flags.
4. The manifest was never reconciled against the member bytes on disk.
5. Metadata counts, role counts and the confirmation floor were never checked
   against the registry they summarise.
6. `donor_role` was read off the row on load rather than re-derived, so a
   role-swapped registry with recomputed digests would have passed.
7. `_boolean` accepted the string `"True"` in derivations, which would let an
   unparsed CSV column decide eligibility.

Verifiers that reported the wrong thing while appearing to work:

8. Mutation tests stopped at the manifest check instead of reaching the checks
   their names claimed, because mutating a member breaks three things at once.
9. The re-derivation comparison pitted the package's twelve-place rendering
   against a fresh full-repr float and failed on identical numbers.
10. A reported "largest raw float delta" was presented as bounding re-derivation
    drift. It measured the write's quantization error and lies in `[0, 5e-13)` by
    construction once the strings agree, so it could never detect drift. It is
    relabelled a quantization check with its bound asserted.

Items 8 through 10 share one shape: a check that looked green while measuring
something other than what its name said. Three of the four provenance and
verifier defects were caught by reading emitted values rather than by a failing
test. That bears directly on how much weight the suite counts below deserve.

## The independent re-derivation

    donors compared                46
    field comparisons             184
    payload reads / cache hits    3,126 / 17,678   identical to the production run
    re-derived completeness root  360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    stored completeness root      360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470

Every donor's Q_DEPTH, Q_DETECT, cell count and completeness flag was recomputed
from authenticated bytes and matched at twelve places, which is the precision at
which the authority defines the quantity: the writer renders through `"%.12f"`
and the root frames through `_typed_float(places=12)`.

What this shows: the numbers reproduce from authenticated bytes, not merely the
digests from themselves.

What it cannot show, stated so the report is not over-read: **re-derivation drift
below 1e-12 is not observable from this artifact**, because the artifact retains
twelve places and nothing finer. Root equality is the statement about
reproduction.

## Corrections to earlier producer statements

- The producer suite baseline was **561**, not the 577 previously carried
  forward. With the two new suites it is **652**.
- The R4 independent reviewer suite is **6 passed, 1 failed**, that failure being
  the mutual contradiction in F4.
- `SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN` is retired and confirmed absent from
  the first real technical-completeness package, whose status was decided by
  measured coverage rather than a caller flag.

## Verification a reviewer can run

    python -m pytest tests/v4/test_t0_age_sex_authority_v1.py \
        tests/v4/test_t0_at8_availability_authority_v1.py \
        tests/v4/test_t0_eligible_donor_authority_v1.py \
        tests/v4/test_t0_eligible_donor_production_run_v1.py \
        tests/v4/test_t0_estimability_preflight_v1.py \
        tests/v4/test_t0_estimability_preflight_production_run_v1.py \
        tests/v4/test_t0_r6_parent_replay_reds_v1.py \
        tests/v4/test_t0_immune_fraction_authority_r2_v1.py \
        tests/v4/test_t0_immune_fraction_authority_v1.py \
        tests/v4/test_t0_immune_support_count_authority_v1.py \
        tests/v4/test_t0_input_dependency_contract_v1.py \
        tests/v4/test_t0_raw_source_row_authority_v1.py \
        tests/v4/test_t0_technical_completeness_authority_v1.py \
        tests/v4/test_t0_v20_feature_projection_authority_v1.py \
        tests/v4/test_t0_v20_row_count_authority_r2_red_v1.py \
        tests/v4/test_t0_v20_row_count_authority_v1.py -q
    # expect 688 passed

    python -m pytest tests/v4/test_t0_r4_independent_external_reds_v1.py -q
    # expect 6 passed, 1 failed (F4)

Name the suites explicitly. A bare `tests/v4` glob pulls in unrelated files that
error at import.

Reproduction commands for every artifact are in the two manifests. The stronger
technical-completeness check is `--rederive`, which costs a second full pass over
the counts store.

## What must not happen next without explicit authorization

Do not run real T0. Do not access numeric AT8 or pathology values. Do not open
DEV or SEALED. Do not set or bypass `real_execution_ready=True`. Do not begin
teacher-student training. Do not self-promote any authority to PASS.
