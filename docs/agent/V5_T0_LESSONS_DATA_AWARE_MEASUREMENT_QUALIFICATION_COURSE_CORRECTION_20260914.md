# V5 course correction from T0 lessons — data-aware, outcome-blind measurement qualification

Date: 2026-09-14

Status: `ACTIVE_V5_UPSTREAM_BLOCKER__FULL104_RECONNAISSANCE_AND_V5_MEASUREMENT_PROCEDURE_QUALIFICATION_REQUIRED_BEFORE_REAL_D_SHARED`

This record captures the project-level correction agreed after re-reading the frozen T0 closeout and the T0↔V5 crosswalk. It does not reopen T0 and it does not authorize any D_shared outcome access.

## 1. What T0 actually established

T0 remains closed at:

`T0_MEASUREMENT_PROCEDURE_NOT_QUALIFIED_AT_N28__BIOLOGY_UNRESOLVED`

The frozen T0 closeout tested a specific latent/common-factor measurement procedure at the real n=28 geometry using prospectively frozen synthetic studies. The closeout explicitly states that no pathology value was read during that qualification. It therefore established that the particular T0 measurement procedure was not qualified; it did **not** establish that the biology was absent and it did **not** provide a complete descriptive characterization of the real downstream FULL104 representation problem.

Do not reopen or repair that closed T0 contract. Preserve its lessons.

## 2. V5 is a different procedure, but can repeat the same class of mistake

V5 D_shared is not the T0 latent-factor procedure. V5 proposes a multiview/shared-representation procedure over authenticated FULL104, using matched-null comparisons, donor resampling, held-donor cross-view predictability, independent-view agreement, measurement-shortcut controls, and rank adjudication.

The exact procedures are different.

However, the T0↔V5 audit already identified the largest framework gap as:

- no explicit target-distribution characterization before choosing the objective/measurement rule; and
- no explicit measurement-model/loss qualification stage.

The same audit also identified two additional transferable gaps:

- simpler/nuisance comparator and search-limit reporting must be first-class outputs; and
- donor/influence concentration must be a first-class diagnostic, not inferred only from resampling stability.

Therefore V5 must not treat a statistically well-specified D_shared procedure as automatically scientifically qualified.

## 3. Governing philosophy: data-aware, outcome-blind

The project rule is now:

`UNDERSTAND_FULL104_DEEPLY__KEEP_FINAL_D_SHARED_HYPOTHESIS_TEST_SEALED`

Being prospective does **not** mean being blind to the dataset. The pipeline must be designed around the actual dataset.

Before final D_shared execution, FULL104 may and should be characterized for non-decision-bearing properties needed to design and qualify the measurement system.

Allowed reconnaissance includes, at minimum:

- cells per donor/operator/source/study/technology and relevant intersections;
- depth and detection distributions;
- sparsity, zero structure, support, missingness, floors/ceilings, tails and mass points;
- feature variance/covariance and numerical conditioning;
- effective rank / redundancy of the 512-dimensional derived representations;
- A/B and subview overlap or redundancy diagnostics;
- donor heterogeneity and leverage;
- technical-variable correlations and confounding structure;
- cell-state abundance/support across donors;
- sizes and singleton rates of proposed matched-null strata;
- whether each proposed matching state is already frozen/discrete;
- operator/source/dataset dominance of representation variance;
- estimability of proposed controls at the real geometry;
- I/O, memory and deterministic parallelization mechanics.

This reconnaissance may change upstream design choices **only before** the final D_shared hypothesis test is opened.

## 4. What remains sealed during reconnaissance

Until the measurement procedure is fully qualified and the exact execution binding is frozen, do not inspect or preserve decision-bearing current-V5 D_shared outputs, including:

- per-rank pass/fail curves;
- rank-selection results;
- matched-null exceedance results;
- held-donor cross-view predictive effects used for qualification;
- subspace-stability effects used for qualification;
- independent-view agreement effects used for qualification;
- measurement-shortcut incremental effects used for qualification;
- any derived statistic that reveals which rank is close to passing the final rule.

Mechanics-only timings and non-outcome structural diagnostics are permitted.

## 5. If D_shared is opened prematurely

Opening/inspecting decision-bearing D_shared outcomes before the upstream design and measurement procedure are frozen does not destroy the dataset, but it changes the evidentiary role of that run.

A prematurely inspected run must be labelled exploratory. Any later modification to ranks, thresholds, null construction, matching bins, feature construction, replicate counts, failure handling, or decision rules cannot use that same run as independent confirmatory evidence.

A new prospectively frozen confirmation design/run would then be required for confirmatory standing.

## 6. Feature-lineage blocker discovered before outcome access

The actual D_shared executor would consume derived matrices such as:

- `A_full`
- `B_full`
- `A_views`
- `B_views`

Historical package roots exist, including:

- feature-matrix root `c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef`
- multiview root `d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1`

Those hashes alone are not sufficient authority. The derivation from authenticated FULL104 must be proved: row identity, address identity, normalization/transformation, view construction, donor/operator mapping, absence of capping/sampling/adaptive outcome choices, and deterministic reproducibility.

If the historical derivation cannot be certified, the matrices must be rebuilt from authenticated FULL104 rather than patched around the gap.

Claude heavy-machine instructions are frozen at:

`docs/agent/V5_CLAUDE_DSHARED_FEATURE_LINEAGE_INSTRUCTIONS_20260914.md`

## 7. V5 must qualify its own measurement procedure before real D_shared

V2 statistical authority repairs J-1 through J-5 and remains useful, but it is not by itself proof that the D_shared measurement procedure can distinguish shared biology from structured technical variation.

Before real D_shared, V5 needs an explicit, prospectively frozen measurement-procedure qualification at the actual FULL104 geometry.

At minimum, the qualification design must contain:

1. **Real-geometry negative controls** — preserve the relevant real donor/operator/cell-count/covariance/feature geometry while breaking only the shared relationship the estimator is supposed to detect. The procedure must not manufacture a positive D_shared result from structured technical dependence.
2. **Real-geometry positive controls** — introduce a controlled shared signal into the real data geometry without using protected outcomes and demonstrate that the complete D_shared procedure can recover it.
3. **Difficulty/detection curve** — prospectively vary controlled signal strength to estimate where the complete procedure ceases to recover the implanted signal reliably.
4. **Unconditional failure accounting** — estimator failures remain nonqualifying and are reported separately; survivor-only evidence is forbidden.
5. **Influence diagnostics** — donor-level leverage/top-k concentration/leave-one-donor sensitivity must be emitted so a nominally stable result cannot hide dependence on one or two donors.
6. **Nuisance/simple comparator** — publish an explicit nuisance-only or simpler comparator beside the decision-bearing measurement, matched to the same evaluation population and folds where applicable.

The exact positive/negative-control generator and acceptance criteria must be frozen and independently reviewed before those controls are executed for decision authority. Synthetic/toy independent-Gaussian fixtures remain mechanics-only and cannot substitute for real-geometry qualification.

## 8. Relationship to D_shared Authority V2

Current D_shared Authority V2 remains prospectively frozen and preserves the repaired statistical semantics:

- ranks 1..512;
- per-quantity/rank counts;
- 10×512 multiplicity;
- deterministic full-population matched-null generator;
- full-refit null geometry;
- strict lower-bound >0 effect rule;
- unconditional failure semantics;
- no post-outcome tuning.

However, V2 is now classified as:

`STATISTICAL_AUTHORITY_FROZEN__NOT_SUFFICIENT_FOR_REAL_D_SHARED_EXECUTION_WITHOUT_UPSTREAM_DATA_AND_MEASUREMENT_QUALIFICATION`

No existing V2 outcome has been generated or inspected, so this upstream correction remains prospective.

## 9. Corrected execution order

The current order is:

`AUTHENTICATED_FULL104 -> FEATURE_LINEAGE_QUALIFICATION_OR_REBUILD -> FULL104_DATA_RECONNAISSANCE -> SUPPORT/ESTIMABILITY_REVIEW -> V5_MEASUREMENT_PROCEDURE_QUALIFICATION_AT_REAL_GEOMETRY -> FREEZE_ANY_NEEDED_SUCCESSOR_AUTHORITY -> EXACT_PREOUTCOME_BINDING -> INDEPENDENT_EXECUTOR_REVIEW -> REAL_D_SHARED_ONCE -> SEAL_RAW_EVIDENCE -> RANK_ADJUDICATION -> DOWNSTREAM_DIMENSIONS`

Only after D_shared is lawfully frozen may D_private/D_obs and downstream teacher/student work proceed.

## 10. Hard boundaries

T0 remains closed.

`training_authorized = false`

`protected_data_authorized = false`

`numeric_dimensions_authorized = false`

`d_shared_real_outcome_access_authorized = false`

`d_private_execution_authorized = false`

`d_obs_execution_authorized = false`

`td60_authorized = false`

`relational_target_activation_authorized = false`

The purpose of this correction is not to add governance for its own sake. It closes a concrete scientific failure mode already demonstrated by T0: choosing or trusting a measurement procedure before establishing that it behaves appropriately on the actual data geometry.
