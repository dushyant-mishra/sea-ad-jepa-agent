# JEPA Target Discovery — G6/G7 preauthorization readiness review

Date: 2026-10-09

Status: `PREAUTHORIZATION_REVIEW_COMPLETE__G6_G7_STILL_UNAUTHORIZED`

This review was performed while canonical G4/G5 remains pending on PR #248. It does **not** authorize any expression-value read, corrected-value materialization, TD56/TD57B/TD59 biological replay, target selection, TD60, Stage 4, or training.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Why this review was done now

If the post-CRLF G4/G5 value-blind preflight passes, the next possible operation would be the first corrected expression-value read. The dormant G6/G7 code was therefore audited before any owner authorization so that authorization, if later granted, is not used to discover avoidable engineering defects.

## G6 scientific purpose

G6 does not test whether the relational biology survives. It tests whether the corrected physical HVS/SEA rows are internally consistent with the frozen historical Sample-A cell identities and whole-cell raw library totals.

For the exact 25,000 historical Sample-A cells:

- HVS/SEA-AD values are read from the corrected physical-ID path;
- NPH52 remains the authenticated unaffected historical pass-through path;
- only the exact frozen 9,216 TD56–TD59 addresses are retained in the corrected sparse cache;
- HVS/SEA normalization remains `log1p(raw_count * 10000 / verified_whole_cell_library_total)`;
- historical detected-gene counts are diagnostic only and cannot be a pass/fail gate.

G6 PASS remains:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Any whole-cell library mismatch remains terminal:

`STOP_TD_G6_SOURCE_LIBRARY_MISMATCH`

## G6 issue found and corrected prospectively

The historical V1 implementation decoded physical H5AD values with `int(round(float(v)))`. That is unsafe as an authorization boundary because the value-blind G4/G5 preflight intentionally never opens expression arrays and therefore does not itself prove that every stored physical value is an integer raw count.

No G6 value read has ever been executed, so this defect affected no result.

The authorized candidate entrypoint is now:

`scripts/v5/materialize_td_relational_corrected_sampleA_v2.py`

V2 reuses the frozen V1 implementation but replaces the row-value decoder in-memory before V1 `main()` executes. Every HVS/SEA physical value must be finite, nonnegative, and exactly integer-valued. Fractional/transformed values fail closed rather than being rounded.

The historical V1 entrypoint remains in the repository for lineage only:

`scripts/v5/materialize_td_relational_corrected_sampleA.py`

It is explicitly outside any future authorization produced from the revised template.

## G7 scientific purpose

G7 is an independent cross-lane corroboration against the already-authenticated S174 cache. It uses every naturally overlapping HVS/SEA Sample-A cell and every one of the exact 9,216 replay addresses, comparing raw integer counts with zero tolerance.

No extra cell or address may be selected to manufacture overlap.

Possible terminals:

- `PASS_TD_G7_S174_EXACT_OVERLAP`
- `STOP_TD_G7_S174_CROSSCHECK_MISMATCH`
- `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`

## G7 issue found and corrected prospectively

The previous implementation correctly labeled zero natural overlap as `NOT_ESTIMABLE`, but returned process exit code 0 for that state. That could allow an automation layer to confuse an unestimable corroboration with command success.

No G7 execution has occurred, so this defect affected no result.

The hardened G7 implementation now:

- loads the hardened V2 G6 value decoder;
- independently rejects fractional/non-integer S174 reference values rather than silently casting them;
- returns process success only for `PASS_TD_G7_S174_EXACT_OVERLAP`;
- returns non-success for both mismatch and `NOT_ESTIMABLE`;
- continues to write an immutable receipt before returning.

`NOT_ESTIMABLE` remains scientifically informative but is explicitly **not a PASS**.

## Revised authorization template

`docs/agent/JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_TEMPLATE_20261007.json` has been revised to template schema V2.

It remains a template only and creates no authority.

A future runtime authorization may be created only after explicit owner authorization and only after an authenticated:

`PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`

The template binds:

- G6 entrypoint: `materialize_td_relational_corrected_sampleA_v2.py`;
- direct V1 materializer invocation: forbidden;
- G7 entrypoint: `audit_td_relational_g7_s174_overlap.py`;
- exact historical 25,000-cell / 9,216-address scope;
- training remains false;
- replay remains false.

## What G6/G7 PASS would and would not mean

If G6 and G7 both PASS, we would know that the corrected value-reading path is behaving consistently enough to consider the **actual corrected biological replay**.

It would **not** mean that TD56, TD57B, or TD59 survived biologically.

It would **not** select a target.

It would **not** authorize the TD56/TD57B/TD59 replay itself.

It would **not** authorize training.

After G6/G7 receipts are reviewed, a separate explicit owner decision is required before any corrected historical biological replay.

## Current ordered frontier

1. Macha runs post-repair G4/G5 on the canonical Windows machine from PR #248 in the frozen fresh namespace.
2. Any G4/G5 failure is preserved and stops the lane.
3. If G4/G5 PASS, stop and return the receipts to the owner.
4. Only then may the owner explicitly authorize the exact G6/G7 value-read scope.
5. If authorized, use the hardened V2 G6 entrypoint and hardened G7 auditor from this review branch/successor.
6. G6 or G7 mismatch stops.
7. G7 `NOT_ESTIMABLE` is not a PASS and must be separately adjudicated; do not manufacture overlap.
8. Even G6+G7 PASS stops before corrected TD56/TD57B/TD59 biological replay for a separate owner decision.

## Verification qualification

The changes in this review are code/test/documentation preparation only. The present ChatGPT execution environment cannot access the repository checkout or canonical H5AD/S174 assets, and this repository has no registered GitHub Actions workflow. Therefore no CI or canonical-machine test PASS is claimed here.

The branch contains regression tests for:

- rejecting fractional raw values in the hardened G6 reader;
- preserving whole-row library totals before mapping filters;
- exact 9,216-address filtering behavior;
- exact authorization scope and preflight terminal requirements;
- rejecting modified S174 shard hashes;
- rejecting fractional S174 reference values;
- exact overlap mismatch behavior;
- non-success exit for G7 `NOT_ESTIMABLE`.

These tests must be executed in the repository context before any future value-read authorization is acted on.
