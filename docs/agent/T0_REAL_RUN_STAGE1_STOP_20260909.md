# Real T0 staged execution — STOP at the Stage 1 to Stage 2 boundary

    STOP_REAL_T0_STAGE1__FROZEN_V20_PRODUCTION_ENTRYPOINTS_UNREACHABLE__READINESS_FLAG_CONTRADICTION

**No numeric AT8 value has been read.** Neither discovery nor confirmation. DEV
and SEALED were not opened. Nothing downstream was begun. The design was not
changed.

Stage 1's parent verification **passed in full**. The stop is not a parent
failure: it is that the frozen V20 design's own production entrypoints cannot
consume those verified parents.

## Stage 1 result — all parents verified

Run from committed code at `1585725dd9ae9b1d802cf8db8490a6b495b6bea3`, clean
worktree, sealed base ancestral.

    B2 population raw-source     MATCH   0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
    B2 authority package         MATCH   98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436
    technical completeness       MATCH   360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    TC package                   MATCH   0164bccc76ad7ed9385de01fd0ab885dd80770afad0b94ee189e9084ee3cfe99
    AT8 availability             MATCH   e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b
    AT8 package                  MATCH   3f74fa833bc1838a50d92bf3f6bdb55e6eafdb10b489fbfff142a4240466fc5a
    age/sex                      MATCH   95ed8f75a42368f3308cf794dbab3c651a4467756147a49a937c5a881e1cffff
    age/sex package              MATCH   8212191a03f09d669a383be6a541b5ce3493b32c13608a76f197a88fa18ddf9b
    eligible donor root          MATCH   a5470b9f5389e0fa72b3ca51832c67d7419ed6447a85d6d979884b9fe1444f85
    donor role root              MATCH   799261f54de158f4c24c33a51a674611fe4e5e68509fcbbca681216470fe10bd
    ED package                   MATCH   7d372603cb4833a2cba02a047f6f3f3e4ef680ab0c730b8693ccbd958ddfafeb
    Stage A preflight root       MATCH   bf9ee518d59053b3fe446c258c2606f318077b2f179ad73c45c4c6346030df27

    donor roles          CONFIRMATION 18, DISCOVERY 28, INELIGIBLE 0
    cells consumed       20,804   population rows proven 20,804
    Stage A ranks        CONF 4, DISC 4, 28 LOODO folds all full rank
    contract wellformed  True
    new false labels     refused in code

## The failing check

    stage      Stage 1 to Stage 2 boundary
    file       scratchpad/v20_recovery/current/code/t0_execution_input_authority_v1.py
    line 151   build_pretarget_execution_authority writes 'real_execution_ready': False
    line 158   load_pretarget_execution_authority raises unless it *is* False
    line 191   build_preadjudication_execution_authority writes False
    line 198   load_preadjudication_execution_authority raises unless it *is* False

    file       scratchpad/v20_recovery/current/code/t0_canonical_freeze_v2.py
    line 8     raises STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED
               unless real_execution_ready *is* True

    file       scratchpad/v20_recovery/current/code/t0_adjudicator_v2.py
    line 34    same condition on the pretarget authority
    line 48    same condition on the preadjudication authority

The two requirements are mutually exclusive. A package that loads must carry
`False`; an entrypoint that runs requires `True`. Nothing in the frozen code ever
writes `True`.

## Demonstrated, not inferred

Loader behaviour, exercised on a crafted package written through the module's own
`_write_package`:

    real_execution_ready = False   load_pretarget_execution_authority: OK
    real_execution_ready = True    load_pretarget_execution_authority: RAISES
                                   'pretarget authority metadata mismatch'

Composition, with the verifier standing in for a loaded authority, which by the
loader's contract necessarily carries `False`:

    production  freeze_target_after_role_v2   -> RAISES STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED
    test-only   ..._v2_for_test               -> returns normally

Exhaustive search for a resolving path:

    grep for any assignment of real_execution_ready to True, across the frozen
    V20 code:                    no match
    across all three recovered snapshots
    (v19_ref, v20_recovery, t0_v20_external_review):   no match
    the loader's `is not False` check:  present twice in each of the three
                                        snapshots, identical

The only files in the workspace that set the flag True are two of my own
scratchpad probe scripts, which are not authority code.

## Why there is no legitimate alternative entrypoint

The V20 package's own equivalence audit,
`audit_t0_v20_execution_authority_equivalence.py`, declares the canonical set and
the superseded set explicitly:

    exact_three_v20_entrypoints
        t0_canonical_freeze_v2.py   freeze_target_after_role_v2
        t0_canonical_freeze_v2.py   freeze_tail_after_discovery_authority_v2
        t0_adjudicator_v2.py        adjudicate_from_raw_v2

    v18_entrypoints_superseded — each classified
    SUPERSEDED_NON_AUTHORITATIVE_PRIMITIVE
        t0_canonical_freeze_v1.py   freeze_target_after_role
        t0_canonical_freeze_v1.py   freeze_tail_after_discovery_authority
        t0_adjudicator_v1.py        adjudicate_from_raw

All three canonical entrypoints are gated on the unsatisfiable condition. The
three v1 entrypoints are not gated, but the V20 contract classifies them as
non-authoritative primitives, so a production conclusion may not be drawn
through them.

The audit also asserts `production_*_no_bypass_arg`: the production entrypoints
deliberately do not expose `allow_synthetic_test_fixture`. The bypass exists only
on the `_for_test` entrypoints, whose own docstrings say "never production
authority".

## What I did not do

Three workarounds were available and all three were refused:

1. **Call the `_for_test` entrypoints.** They accept the bypass and would have
   produced a fitted object. Their docstrings say they are never production
   authority, and the audit exists to keep them separate.
2. **Use the superseded v1 entrypoints.** They would run. The V20 contract
   classifies them as non-authoritative, and the whole purpose of v2 is the
   external input authority enforcement that v1 lacks.
3. **Patch the frozen code so the builder writes `True`.** This is the exact
   thing the authorization forbids — "do not set `real_execution_ready=True` as a
   shortcut... it must be derived, not manually flipped" — and it would edit
   frozen design code after authorization.

Each would have produced a number. None would have produced a result anyone
should rely on.

## Why this had to surface before Stage 2, and did

Stage 2 opens discovery numeric AT8 in order to fit the discovery object. Had I
built the Stage 2 runner and executed it, the sequence would have been: open
discovery AT8, compute the pseudobulk, assemble the discovery metadata, call the
canonical freeze — and only then hit this STOP, with the pathology-blind property
of the lane already spent and nothing to show for it.

Reading the authoritative implementation before running it is what prevented
that. The endpoint identity check is what led here: verifying that the frozen
design's `AT8` column is the availability authority's
`percent AT8 positive area_Grey matter` required reading the fit, which led to
the canonical freeze, which led to the gate.

## What this is, and what it is not

It is not a defect in the pathology-blind lane. Every parent verified.

It is not a data problem. No data was read.

It is a **specification-versus-implementation contradiction in the frozen V20
package as recovered**: the design declares an external input authority that must
be materialized with `real_execution_ready=True`, and ships builders and loaders
that make that state unrepresentable. The STOP name says exactly this —
`EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED` — which suggests the intended
resolution was an external materialization step that either was never written or
was not recovered with the package.

## What resolution requires — an owner and reviewer decision, not mine

Any of these changes the frozen design and therefore needs explicit
authorization:

1. **Recover the missing materializer.** If a component outside the recovered
   package was intended to write the pretarget and preadjudication authorities
   with `real_execution_ready=True`, it must be found. The loader would still
   have to be reconciled, because as written it refuses `True`.
2. **Correct the loader.** If `is not False` was meant to be a
   presence-and-type check rather than a value check, that is a one-line defect
   with a large consequence, and correcting it is a change to frozen design code
   that must be authorized and reviewed, not made quietly by me.
3. **Re-freeze the readiness semantics.** Decide what `real_execution_ready`
   means at this boundary, who derives it from what, and record it in the V20
   contract before any execution.

I have not chosen among these and have written no code toward any of them.

## Gate status at this STOP

    numeric AT8 accessed          NO, neither discovery nor confirmation
    DEV opened                    NO
    SEALED opened                 NO
    protected populations opened  NO
    training begun                NO
    successor-u0 materialized     NO
    TD60 run                      NO
    design changed                NO
    frozen V20 code modified      NO
    Stage 1 terminal reached      NO — parents verified, but
                                  DISCOVERY_NUMERIC_AT8_READY_TO_OPEN cannot be
                                  asserted while the consumer refuses to run
