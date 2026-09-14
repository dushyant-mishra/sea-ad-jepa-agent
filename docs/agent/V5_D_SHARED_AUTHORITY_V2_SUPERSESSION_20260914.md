# V5 D_shared Authority V2 supersession — 2026-09-14

Status: `V2_PROSPECTIVELY_FROZEN__V1_PRESERVED_AS_PROVENANCE__D_SHARED_NOT_RUN__NO_TRAINING_AUTHORITY`

## Why V2 exists

Heavy-machine reconnaissance completed before any current-V5 D_shared outcome was generated or inspected and demonstrated five pre-outcome execution-authority defects in V1:

1. per-quantity precision counts were collapsed to scalar maxima by the execution plan/firewall;
2. matched-null preservation constraints did not identify a unique generator;
3. precision tolerances were correctly declared non-effect thresholds, but no separate prospective effect criterion existed for the five D_shared gates;
4. the positive-rank search envelope was not frozen;
5. the 0.05 precision-risk budget covered ten quantities but did not explicitly cover the rank ladder used for selection.

No V1 D_shared result exists. Therefore a prospective successor could be frozen without post-outcome adaptation.

## Preserved V1 provenance

The following artifacts remain immutable and valid as provenance only:

- V1 precision authority SHA-256: `cc4ac4d5116fa81990f1c3bd0497fc578eda86bb2d7d3cd2747abcf7ffcf9428`
- V1 FULL104↔precision cross-binding receipt SHA-256: `eccc30f9f5d01f7905a0740982d678d0ce45532a08cd5a61c51f5448b63b3d3a`

They MUST NOT authorize D_shared metric execution after V2.

## V2 frozen authority

Artifact:

`docs/agent/V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2.json`

Canonical SHA-256:

`f9568eb19a22f106b0be3ce0580bc1058695ca1a2de6dd2d0475c3240a6bbda2`

V2 freezes:

- ranks `1..512`;
- familywise precision risk `0.05` over `10 × 512` quantity/rank cells;
- per-cell alpha `9.765625e-6`;
- Hoeffding fixed-N execution counts carried per quantity/rank rather than scalar maxima;
- five D_shared contrast quantities at 9,784 replicates per rank under the frozen `[-1,1]`, epsilon `0.05` declarations;
- matched-null generator `DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1`;
- exact matching tuple `(donor, operator, Q_DEPTH, Q_DETECT, support_measurability)`;
- requirement that all matching-state components already have frozen discrete representations, otherwise STOP;
- full-refit every null replicate;
- effect criterion `SIMULTANEOUS_LOWER_BOUND_STRICTLY_GT_ZERO_V1`;
- RNG policy `SHA256_PARENT_QUANTITY_RANK_REPLICATE_INDEX_V2`;
- unconditional denominator and failure-is-nonqualifying semantics;
- D_shared-only stage authority.

## V2 code path

- `src/sea_ad_jepa/v5/d_shared_authority_v2.py`
- `src/sea_ad_jepa/v5/d_shared_execution_firewall_v2.py`
- `src/sea_ad_jepa/v5/d_shared_rank_adjudication_v2.py`

The V2 pre-outcome binding schema is:

`JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2`

A heavy-machine binding receipt under this schema is required before the production D_shared metric executor may run.

## Stage boundary

A valid V2 pre-outcome binding may authorize only D_shared metric execution.

The following remain false:

- `d_private_execution_authorized`
- `d_obs_execution_authorized`
- `training_authorized`
- `protected_data_authorized`
- `td60_authorized`
- `relational_target_activation_authorized`

## No-outcome declaration

At V2 freeze and repository implementation:

- no current-V5 D_shared metric value was generated or inspected;
- no D_shared rank score was generated or inspected;
- no current-V5 matched-null distribution was generated or inspected;
- no current-V5 held-donor score was generated or inspected;
- D_private and D_obs were not executed;
- training remained OFF;
- protected data remained closed;
- TD60 remained OFF;
- relational activation remained OFF.

## Next lawful action

On the authenticated heavy-data machine:

1. verify the exact V2 code/authority head;
2. verify the matching tuple is represented by pre-existing frozen discrete state with no newly invented binning;
3. create and seal `JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2` against the exact sealed FULL104 input;
4. return that receipt for independent review;
5. only after that review may the production D_shared metric executor be implemented/executed under the V2 firewall.
