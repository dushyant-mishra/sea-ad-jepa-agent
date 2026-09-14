# Claude instructions — D_shared feature-lineage qualification before execution

Status: `ACTIVE_HEAVY_MACHINE_INSTRUCTIONS__NO_D_SHARED_OUTCOMES`

Branch to use:

`repair/v5-dshared-authority-v2-20260914`

Starting verified head before this instruction commit:

`86332a044a9df0710086254d073d52b359541bf2`

These instructions are prospective. Do **not** run or inspect current-V5 D_shared outcomes while carrying them out.

## Current frozen V2 statistical authority

Do not alter the V2 statistical authority during this task.

- D_shared Authority V2 SHA-256: `f9568eb19a22f106b0be3ce0580bc1058695ca1a2de6dd2d0475c3240a6bbda2`
- rank envelope: `1..512`
- matched-null generator: `DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1`
- RNG policy: `SHA256_PARENT_QUANTITY_RANK_REPLICATE_INDEX_V2`
- effect rule: `SIMULTANEOUS_LOWER_BOUND_STRICTLY_GT_ZERO_V1`
- training: OFF
- protected data: CLOSED
- TD60: OFF
- relational activation: OFF

## Immediate blocker

The next D_shared metrics would consume historical derived feature matrices such as:

- `feature_matrix_level4/A_full`
- `feature_matrix_level4/B_full`
- `feature_matrix_level4/A_views`
- `feature_matrix_level4/B_views`

Known historical package roots from reconnaissance:

- feature-matrix root: `c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef`
- multiview root: `d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1`

Those roots are not currently sufficient D_shared authority merely because their hashes exist. Their derivation from authenticated FULL104 must be qualified first.

# Task 1 — recover and audit the exact feature derivation

For each of `A_full`, `B_full`, `A_views`, and `B_views`, recover and report:

1. exact producing script(s) and commit lineage;
2. exact source FULL104 block/input parents;
3. row identity mapping back to all 4,553,407 authenticated cells;
4. feature/address mapping back to the 41,238 Molecular Ledger addresses;
5. exact normalization/transformation formula;
6. exact view construction rule and whether A/B and their subviews are disjoint as intended;
7. donor and operator mapping;
8. any filtering, clipping, winsorization, imputation, centering, scaling, PCA/SVD, rank truncation, row sampling, stratum sampling, or other cap;
9. any pathology-dependent choice;
10. any protected-data-dependent choice;
11. any checkpoint-outcome-dependent choice;
12. any adaptive choice made after inspection of biological outcomes;
13. all file/package/contract/script hashes needed to reproduce or validate the matrices.

Pay special attention to historical directories containing files such as:

- `ABORTED_PREPUBLICATION_ATTEMPT.json`
- `FAILED_FINAL_VALIDATION_ATTEMPT_1.json`

Determine whether those attempts affect the exact matrix bytes proposed for V5 or are abandoned historical attempts only.

Do not infer provenance from filenames. Bind it from exact files, manifests, scripts, hashes, and row/address identities.

# Task 2 — classify whether the historical feature matrices are certifiable

Classify the feature derivation into exactly one of:

- `CERTIFIABLE_EXACT_DERIVATION`
- `CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY`
- `NOT_CERTIFIABLE_REBUILD_FROM_AUTHENTICATED_FULL104_REQUIRED`

Do not select a certifiable status merely because the package hashes match. The derivation itself must be reproducible, outcome-blind, identity-preserving, and free of unbound adaptive choices.

If certifiable, prepare a **proposed** feature-lineage receipt containing at minimum:

- exact sealed FULL104 artifact SHA;
- feature matrix package root;
- multiview package root;
- row count;
- donor count;
- operator count;
- address count;
- exact `A_full`, `B_full`, `A_views`, `B_views` shapes;
- exact producer-script SHAs;
- exact transformation/normalization contract SHA;
- row identity closure;
- address identity closure;
- donor/operator identity closure;
- no pathology flag;
- no protected-data flag;
- no checkpoint-outcome flag;
- no row/stratum sampling or cap;
- deterministic reproduction status;
- terminal classification.

Do **not** promote this proposed receipt to V2 execution authority unless the live repository contains the successor feature-lineage binding contract that explicitly accepts it.

If the derivation is not certifiable, do not patch around the gap. Report the exact earliest unprovable transformation and what must be rebuilt from authenticated FULL104.

# Task 3 — prove the V2 matched-null states are already frozen and discrete

Independently verify that each V2 matched-null state already exists in the authenticated production substrate and does not require a newly invented bin or threshold:

- donor;
- operator;
- `Q_DEPTH`;
- `Q_DETECT`;
- `support_measurability`.

For each state report:

- exact source field/table;
- exact definition;
- cardinality;
- whether already discrete;
- whether frozen before current D_shared outcomes;
- exact parent/hash authority.

If `Q_DEPTH`, `Q_DETECT`, or `support_measurability` requires newly chosen cut points, bins, thresholds, or recoding, STOP with:

`STOP_D_SHARED_MATCHED_NULL_STRATIFICATION_UNSPECIFIED`

Do not invent bins.

# Task 4 — mechanics-only resource benchmark

Only after Tasks 1–3 are complete, you may benchmark execution mechanics without preserving, displaying, ranking, or inspecting any decision-bearing D_shared value.

Benchmark:

- one authenticated FULL104 pass needed to construct donor sufficient statistics;
- one representative 512×512 generalized eigensolve;
- deterministic sharded execution overhead;
- memory footprint;
- temporary storage;
- feature-matrix reading cost versus direct authenticated-block reading cost;
- safe parallelization opportunities that leave the frozen estimand unchanged.

Do not aggregate or inspect:

- biological scores;
- rank curves;
- matched-null exceedance values;
- held-donor predictive values;
- subspace-stability results;
- view-agreement results;
- measurement-shortcut increments;
- any statistic capable of revealing whether a rank is likely to pass.

Mechanics benchmarks must be outcome-blind.

# Task 5 — return the evidence package, then STOP

Return all of the following:

A. feature-derivation lineage;

B. one of the three certification classifications;

C. exact hashes and parents;

D. matching-state discreteness report;

E. mechanics-only resource benchmark;

F. any defect that forces rebuild from authenticated FULL104;

G. proposed feature-lineage receipt, if and only if the derivation is certifiable;

H. exact proposed heavy-machine command sequence for the new feature-lineage/V2 pre-outcome binding once the repository-side successor contract exists.

Then STOP.

## Hard prohibitions

Until a new repo-side feature-lineage authority has been independently verified:

- no D_shared outcome execution;
- no inspection of any current-V5 D_shared metric;
- no rank selection;
- no null distribution inspection;
- no D_private;
- no D_obs;
- no training;
- no protected data;
- no TD60;
- no relational activation;
- no post-outcome threshold, null, rank-envelope, binning, replicate-count, or feature-construction change.

If any task would require viewing current-V5 D_shared outcome values in order to decide what to do, STOP and report the authority gap instead.

`training_authorized = false`
