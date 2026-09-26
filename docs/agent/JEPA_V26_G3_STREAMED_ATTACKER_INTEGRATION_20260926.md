# V26 G3 streamed attacker — explicit objective integration (development only)

This is the **scoped successor to draft PR #143**, not a rewrite of historical masking results. Its exact parent is PR #143's current reviewed fit-law reference, which itself descends from experimental PR #77. No Claude implementation, sampling, N1, historic94, linear-comparator or perturbation branch was modified.

## What now changes in runnable code

`full104_masking_streaming_executor_v1.py` retains its existing *default* ridge code and its existing historical scores byte-equivalently at the tested original fixture. In a separately **opted-in development invocation**, `g3_fit_objective=` must explicitly name one of:

- `CURRENT_CELL_WEIGHTED` — reference legacy mass;
- `PRODUCTION_OBJECTIVE_MATCHED` — each outer-training donor has equal mass, then cells uniform inside donor, matching the frozen JEPA base-training scientific objective conditional on the fold;
- `SOURCE_DONOR_BALANCED_DIAGNOSTIC` — each represented TRAIN source receives 1/S of fit mass and its donors share that source's mass.

The opt-in flows through BOTH the `RIDGE8_CONDITIONAL` partner-selection ridge and the primary ridge attacker used to score **all four masking arms**. TOP8 rank-screening, PREFIX3 inner grouping, common random masks, ridge feature count, ridge alpha and original source-balanced heldout score are *unchanged*. The identical base masks/partner choices where the three policies happen to have equal masses are tested against the original canonical streaming code. Source and donor weights refer to TRAIN donors only. The base score's original two changes of scope (source-balanced held-out averaging, held-out-donor feature standardization) are not silently redefined.

Outputs on the new path carry `g3_fit_objective_id` and `g3_scope=DEVELOPMENT_ONLY__UNDEFINED_HELDOUT_TERMS_NOT_QUALIFIED`. The historical, no-opt-in output dictionary retains its prior keys and results. An unknown objective STOPs. New/old outputs must NOT be interchanged or written to the same cache directory.

## Independent self-check

The new CI reruns PR #143's standalone independent direct-row weighted-ridge adversaries, this PR's source-shaped streamed fake block fixture (12 donors, 2 sources, 8 addresses, 3 outer folds), and the original unchanged historical streaming-versus-reference parity suite. The new fixture spies on the real `_fit_ridge_weights` entrypoint to PROVE objective propagation to both RIDGE8's candidate-pool ridge and each arm's primary ridge. It checks every opt-in objective is explicitly marked, that equal donor/source masses reproduce old scores, unknown objectives cannot reach the attacker, and all folds propagate exactly the same objective. No real FULL104 expression opened in CI.

## Critical remaining integration before a scientific JEPA diagnostic verdict

This is a **development-only scored-attacker mechanism**, not a scientifically resolved terminal masking result:

1. Freeze the one real current-V5 DEVELOPMENT diagnostic's exact source/target, visibility, splitter, donor counts/source map and chosen checkpoint. Match the attacked *JEPA representation* and feature protocol, rather than silently using an old scalar expression target as proof about the latent teacher.
2. Physically bind the outer-training donor counts/source IDs to the already authenticated frozen PR #132 pass1 and PR #120/#124 lineage receipts where required; preserve excluded validation/oracle and any nonfit cells. The synthetic fixture's arbitrary `primary_row_weight` values are NOT real-source authority; never use them as a physical credential.
3. Reuse the existing **six-state held-out estimability evidence contract** before making any shortcut/no-shortcut verdict. The legacy scorer still maps an undefined held-out correlation to zero. Its existence in this development-only executor is **intentionally disclosed in every G3 row**, not secretly repaired by fit reweighting. No conclusion about source-balanced terminal masking may be made until the six-state policy is separately adopted under prospective authority.
4. Compare objective-matched fit as the fixed primary; report legacy cell-weighted and source-donor-balanced fits as prespecified sensitivity analyses on the same candidate/mask/target and scientific folds. If a change of training-side fit changes the RIDGE8 selected partners, report that as a *changed* mask (not the same treatment). Do not pick whichever score is favorable.
5. Do not open Audit B N1, D_shared, reader_validation/oracle, foundation sealed, Siletti or pathology data. All physically useful samples must be from approved reader_fit development scope under their separately explicit run authorization.

A **healthy gradient/optimizer/EMA engineering check** can proceed independently of G3 because it measures JEPA mechanics, not how well a fitted external attacker detects molecular shortcuts. A **scientific claim** about masking, source shortcuts or learned biology may NOT.

`G3_WEIGHTED_FIT_MECHANICS = SYNTHETIC_TESTED`
`G3_EXPLICIT_STREAMING_FIT_PROPAGATION = SYNTHETIC_TESTED`
`G3_FULL104_PHYSICAL_SOURCE_REBIND = PENDING`
`G3_HELDOUT_SIX_STATE_SCORE_INTEGRATION = PENDING`
`G3_TERMINAL_PROTECTED_MASKING_OUTCOME = CLOSED`
`CURRENT_V5_REAL_TRAINING = NOT_EXECUTED_HERE`
