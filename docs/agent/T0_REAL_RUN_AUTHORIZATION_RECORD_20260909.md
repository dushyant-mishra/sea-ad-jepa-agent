# Real T0 staged execution — pre-run authorization record

    REAL_T0_STAGED_EXECUTION_AUTHORIZED__DISCOVERY_FIRST__CONFIRMATION_AFTER_DISCOVERY_REPLAY

Frozen at Stage 0, **before any numeric AT8 value is read**. This record exists so
that what was authorized is fixed in advance of seeing any pathology value, and
cannot be reinterpreted afterwards in light of a result.

## Provenance of this authorization

    granted by            the project owner, 2026-09-09
    authorization token   AUTHORIZE_ROLLING_REAL_T0_EXECUTION_WITH_FAIL_CLOSED_STAGE_GATES
    reviewed head         1585725dd9ae9b1d802cf8db8490a6b495b6bea3
    branch                t0/v20-pathology-blind-materialization-20260908
    worktree at Stage 0   clean, verified by `git status --porcelain`
    sealed base           21ec629667eeda5a7d37d3f1d822fbf93b213325, ancestral and untouched
    preceding review      EXTERNAL_REVIEW_PASS_R6_PRE_REAL_T0_CHAIN

The external reviewer's R6 PASS removed the review blocker. It was not treated as
authorization: the owner authorized the run separately and explicitly, and this
record is written under that authorization rather than under the review.

## What is authorized

A **staged** T0 execution, and nothing else. Each stage opens only after the
previous one has run from committed code, written an immutable package, replayed
from disk, and passed its own checks.

    Stage 0   freeze this record                       before any numeric AT8
    Stage 1   verify every pathology-blind parent      no numeric AT8
    Stage 2   open DISCOVERY numeric AT8 only
    Stage 3   open CONFIRMATION numeric AT8 only       after Stage 2 replays
    Stage 4   freeze the real T0 decision package
    Stage 5   package the post-real-T0 review bundle, then stop

## Scope of pathology access

    discovery numeric AT8       may be opened at Stage 2
    confirmation numeric AT8    may open at Stage 3, automatically, and only
                                after the discovery package replay passes
    any non-AT8 pathology endpoint      NOT authorized
    protected-population data           NOT authorized
    DEV                                 remains closed
    SEALED                              remains closed

A stage being closed means *do not open it early*. It does not mean stop forever:
the next gate opens automatically on the previous stage's verified replay. But a
gate that is closed at the time of reading is closed, and no stage may be
anticipated.

## Explicitly NOT authorized by this record

    teacher/student training            closed
    successor-u0 materialization        closed
    TD60                                closed
    protected-population sweeps         closed
    biological sweeps                   closed
    exploratory analysis of any kind     closed
    DEV                                 closed
    SEALED                              closed

The real T0 result becomes a **parent candidate** for the later V5
teacher/student join. It is not itself training authorization.

## The design is frozen and may not change after numeric AT8 is read

This is the binding constraint of the whole exercise. After Stage 2 opens
discovery AT8, none of the following may be altered, for any reason, including a
disappointing result:

    donor set and donor roles
    the eligibility predicate
    the discovery/confirmation split
    the AT8 endpoint identity
    covariates and the nuisance design
    the feature set and the projection
    thresholds and alpha values
    tail policy and the tail floor
    the permutation count and the inference method

A negative or null result is **not** an execution failure and must be packaged
exactly as it comes out. What is a STOP is a provenance, replay, donor-set,
endpoint, or design violation.

## Frozen identities this run must consume

Parents accepted at R6:

    B2 population raw-source      0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
    B2 authority package          98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436
    population closure            ec350b8d9a30a8a08573f055b9a0c103d0f6805014998ac9975d94585421d397
    logical row authority         64ea880ff6cf19aca48e0f2e77edfa6d37fc4f5e20022011131c496173896fc3
    physical read plan            cc75cef0ebb9a05e6699546e18ae45b3555f488dc2e46db4c845370c5be23519
    B1 feature authority          538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8
    B1 projection root            ef6ccdde0e0268cce819b4e543d7d542120811fa3762225964f78f9172f370e7
    technical completeness        360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    TC package                    0164bccc76ad7ed9385de01fd0ab885dd80770afad0b94ee189e9084ee3cfe99
    eligible donor root           a5470b9f5389e0fa72b3ca51832c67d7419ed6447a85d6d979884b9fe1444f85
    donor role root               799261f54de158f4c24c33a51a674611fe4e5e68509fcbbca681216470fe10bd
    ED package                    7d372603cb4833a2cba02a047f6f3f3e4ef680ab0c730b8693ccbd958ddfafeb
    Stage A preflight root        bf9ee518d59053b3fe446c258c2606f318077b2f179ad73c45c4c6346030df27
    AT8 availability root         e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b
    AT8 availability package      3f74fa833bc1838a50d92bf3f6bdb55e6eafdb10b489fbfff142a4240466fc5a
    age/sex root                  95ed8f75a42368f3308cf794dbab3c651a4467756147a49a937c5a881e1cffff
    age/sex package               8212191a03f09d669a383be6a541b5ce3493b32c13608a76f197a88fa18ddf9b

Sources:

    membership                    d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529
    complete block manifest       66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
    MTG H5AD, 32,978,570,763 B    e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79
    pathology target CSV          ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a

The AT8 endpoint identity, from the availability authority's own metadata, which
recorded it without ever parsing a magnitude:

    at8_field        "percent AT8 positive area_Grey matter"
    donor_id_field   "Donor ID"
    source path      data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv

Design as it stands after the pathology-blind lane:

    candidate donors    46      eligible 46
    CONFIRMATION        18      all 18 tail-measurable
    DISCOVERY           28      27 tail-measurable, H20.33.037 has 67 cells
    cells               20,804
    nuisance design     [1, age_c, age_c^2, sex], 4 columns, full rank on both
                        roles and on all 28 DISCOVERY LOODO folds

## Byte-semantics requirement for every new artifact

Every package and module created by this run must declare

    SHA256_OVER_LF_NORMALIZED_FILE_CONTENT__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES

and must not carry the waived legacy label `GIT_BLOB_BYTES__NOT_WORKTREE_BYTES`.
This is enforced in code by
`t0_input_dependency_contract_v1.assert_byte_semantics_label_lawful`, whose
waived allowlist is frozen at six legacy modules and cannot grow, so a new
real-T0 module declaring the legacy label raises
`STOP_T0_NEW_ARTIFACT_CARRIES_THE_WAIVED_FALSE_BYTE_SEMANTICS_LABEL`.

## The readiness flag

`real_execution_ready` must not be flipped as a shortcut. If any readiness field
is recorded by this run, it must be *derived* by the real-T0 execution package
from verified parents and stage terminals. No manual assignment.

## Stage terminals

    Stage 1   REAL_T0_STAGE0_PARENTS_VERIFIED__DISCOVERY_NUMERIC_AT8_READY_TO_OPEN
    Stage 2   DISCOVERY_STAGE_DONE_AND_REPLAYED__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN
    Stage 3   CONFIRMATION_STAGE_DONE_AND_REPLAYED__REAL_T0_DECISION_READY_TO_FREEZE
    Stage 4   REAL_T0_DONE_AND_REPLAYED
    Stage 5   STOP_AFTER_REAL_T0_REPLAY__AWAITING_POST_T0_REVIEW

On any STOP or unexpected condition: stop immediately and report the exact
failing check, file, root and stage. Do not work around it, and do not change the
design in response to it.

## Status at Stage 0

    numeric AT8 accessed          NO, neither discovery nor confirmation
    DEV opened                    NO
    SEALED opened                 NO
    protected populations opened  NO
    training begun                NO
    successor-u0 materialized     NO
    TD60 run                      NO
    design changed since freeze   NO
