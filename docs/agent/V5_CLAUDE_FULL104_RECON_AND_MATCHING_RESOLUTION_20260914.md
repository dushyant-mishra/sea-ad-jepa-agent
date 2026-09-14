# Claude next instructions — FULL104 reconnaissance + matching-state resolution

Date: 2026-09-14

Branch: `repair/v5-dshared-authority-v2-20260914`

Read first:

1. `docs/superpowers/specs/2026-09-14-v5-dshared-reconnaissance-resolution-v1.md`
2. `docs/agent/V5_CURRENT_AUTHORITY_AND_BLOCKERS_20260913.md`
3. `docs/agent/V5_MASTER_OPEN_ITEMS_20260913.md`
4. `docs/agent/V5_FULL104_RECONNAISSANCE_AUTHORITY_V1.json`
5. `docs/agent/V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2.json`

## Hard boundary

Do **not** execute or inspect any current-V5 D_shared decision-bearing outcome.

Do not generate or preserve:

- candidate-rank D_shared scores;
- matched-null D_shared effect values;
- shared-subspace qualification curves;
- held-donor cross-view D_shared qualification values;
- independent-view D_shared qualification values;
- measurement-shortcut D_shared pass/fail values;
- selected rank / D_shared;
- any final D_shared pass/fail conclusion.

Also keep D_private, D_obs, training, pathology/protected confirmation, TD60, and relational activation OFF.

Everything below is **outcome-blind dataset/measurement reconnaissance**.

## Task A — lossless discrete-preimage test for the V2 matching states

V2 cannot currently execute because stored `Q_DEPTH` and `Q_DETECT` are continuous float32 values. Do not invent bins.

Test whether they are lossless encodings of discrete generating counts.

### A1. Q_DEPTH

Stored semantic:

`Q_DEPTH = float32(log1p(source_library_count))`

For every one of the 4,553,407 rows:

1. Recover candidate integer:
   `Q_DEPTH_COUNT = round(expm1(float64(Q_DEPTH)))`.
2. Require candidate >= 0 and integer-valued.
3. Recompute with the exact historical numeric semantics:
   `float32(log1p(Q_DEPTH_COUNT))`.
4. Compare recomputed float32 to stored Q_DEPTH **bitwise** (preferred) and also report absolute error diagnostics.
5. Report total rows, mismatches, max absolute error, and min/median/p95/max recovered count.

If any mismatch exists, classify Q_DEPTH as not losslessly recoverable under this rule. Do not change tolerances after seeing results.

### A2. Q_DETECT

Stored semantic:

`Q_DETECT = float32(nonzero_count / max(scalar_support_count, 1))`

Recover the frozen per-operator `scalar_support_count` from `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` / the exact frozen observation-state authority.

For every row:

1. Let `s = max(scalar_support_count(operator), 1)`.
2. Recover candidate integer:
   `Q_DETECT_COUNT = round(float64(Q_DETECT) * s)`.
3. Require `0 <= Q_DETECT_COUNT <= s`.
4. Recompute `float32(Q_DETECT_COUNT / s)` using the historical semantics.
5. Compare recomputed float32 to stored Q_DETECT bitwise and report absolute-error diagnostics.

If any mismatch exists, classify Q_DETECT as not losslessly recoverable. Do not invent bins.

### A3. If either preimage fails

STOP the V2 matching resolution with:

`STOP_D_SHARED_CONTINUOUS_MATCHING_STATE_REQUIRES_V3_NULL`

Return the evidence; do not design a V3 null on the fly and do not execute D_shared.

## Task B — exact matching-stratum occupancy

If both A1 and A2 are lossless, construct the outcome-blind candidate key:

`(donor, operator, Q_DEPTH_COUNT, Q_DETECT_COUNT)`

Do not include `support_measurability` in the key if Task C proves it is exactly redundant with operator.

Report **complete population occupancy**, not a sample:

- total cells;
- total unique strata;
- cells and strata of size 1;
- cells and strata of size 2–3;
- cells and strata of size 4–7;
- cells and strata of size >=8;
- min, median, p95, max stratum size;
- fraction of all cells in singleton strata;
- fraction of all cells in nonpermutable strata under the frozen view-permutation rule;
- occupancy broken down by donor and operator so concentration is visible.

This report is allowed reconnaissance. It must contain no D_shared effect values.

If the lossless key is technically valid but overwhelmingly singleton/nonpermutable, report that plainly. Do not merge strata or invent bins.

## Task C — prove support-measurability redundancy

The prior report found the support-measurability descriptor columns are constant per operator.

Prove this exactly over the full population:

1. produce the operator -> support-measurability-state table;
2. verify every row's support state equals the frozen state of its operator;
3. report mismatches;
4. hash the mapping table and the verification receipt.

If mismatches are zero, classify:

`SUPPORT_MEASURABILITY_EXACTLY_REDUNDANT_WITH_OPERATOR`

If not, report the actual dependence structure; do not force the redundancy conclusion.

## Task D — complete the FULL104 data-aware, outcome-blind reconnaissance evidence package

The repo now requires actual hash-bound evidence for every allowed reconnaissance diagnostic. A statement such as “diagnostic completed” is not enough.

Create one deterministic evidence artifact for each of these 14 diagnostics:

1. `donor_operator_source_study_technology_counts`
2. `depth_detection_distributions`
3. `sparsity_zero_support_missingness`
4. `feature_variance_covariance_conditioning`
5. `effective_rank_redundancy`
6. `view_overlap_redundancy`
7. `donor_heterogeneity_leverage`
8. `technical_variable_correlations`
9. `cell_state_support_across_donors`
10. `matched_null_stratum_size_singleton_rates`
11. `matching_state_discreteness`
12. `operator_source_dataset_variance_dominance`
13. `control_estimability`
14. `io_memory_parallelization_mechanics`

Requirements:

- use the authenticated 4,553,407-row FULL104 population or the certified historical features where appropriate;
- no sampling unless the artifact is explicitly labeled mechanics-only and the production diagnostic is separately complete;
- bind every evidence artifact to exact input hashes;
- canonicalize output where possible;
- compute SHA-256 for every diagnostic artifact;
- create a deterministic diagnostic-evidence map `{diagnostic_id: sha256}`;
- compute a root SHA-256 over the canonical sorted evidence map;
- record scripts and script SHA-256 values used to produce each diagnostic;
- record row counts / donor counts / operator counts for each applicable artifact.

Do not put D_shared rank/effect/pass data in these artifacts.

### Minimum scientific content expected

In addition to the matching-state work above, characterize:

- donor/operator/source/study/technology imbalance;
- library-depth and detection distributions;
- zero/sparsity/missing-support structure;
- feature variance and covariance spectrum;
- numerical conditioning;
- effective dimensionality / redundancy without using D_shared pass criteria;
- A/B and within-A/within-B view overlap/redundancy;
- donor leverage / concentration;
- associations of feature structure with operator/source/study/technology and other technical variables;
- cell-state support across donors and datasets;
- whether proposed positive/negative measurement controls are estimable at real geometry;
- I/O, memory, cache, parallel-sharding mechanics.

This is exactly the “understand the data before choosing the assay” stage that T0 taught us was missing.

## Task E — feature-lineage evidence needed by the hardened repo contract

The recovered feature lineage is useful but the repo-side validator is being hardened. Return exact evidence for:

1. donor identity digest across all 4,553,407 rows;
2. operator identity digest across all 4,553,407 rows;
3. row-order identity digest;
4. address identity digest;
5. complete explicit transform disclosure, including:
   - normalization formula;
   - sketch/projection semantics;
   - visibility-channel construction;
   - `views = 4`;
   - visible fraction `0.60` / mask fraction `0.40`;
   - no clipping;
   - no winsorization;
   - no imputation;
   - no PCA/SVD feature reduction;
   - no row/stratum sampling or capping;
6. exact hashes for:
   - feature builder;
   - assembler;
   - validator/publisher;
   - feature contract;
   - projections NPZ;
   - matrix manifest;
   - multiview manifest;
   - validation-only patch/diff;
7. a logical-name -> published-file-hash map that does not depend on stale absolute Windows staging paths.

### F1 ruling

Do not claim exact replay of the original historical writer if `writer_code_sha256 4c39d215…` remains unresolved.

Instead report:

`ORIGINAL_WRITER_HASH_UNRESOLVED__PUBLISHED_BYTES_AND_SEMANTICS_VERIFIED`

and bind the mechanics-repair evidence separately.

### F2 ruling

The historical four-view / 0.60-visible geometry is **not yet current-V5 biological measurement authority**.

It may be certified as historical/provenance/mechanics input, but do not claim it is approved for final D_shared merely because the bytes are valid.

### F3 ruling

Use:

`CONTENT_HASH_AND_LOGICAL_NAME_AUTHORITATIVE__ABSOLUTE_PATH_INFORMATIONAL_ONLY_V1`

for relocated published artifacts whose bytes match the frozen manifest.

## Task F — data-informed measurement-qualification planning inputs

Using only the outcome-blind reconnaissance above, return the quantities needed for us to prospectively freeze the V5 positive/negative-control qualification plan, such as:

- natural feature variance scales;
- donor-to-donor heterogeneity scales;
- technical-confound strength scales;
- effective dimension/conditioning summaries;
- feasible controlled-signal injection scales expressed relative to observed variance;
- feasible replicate/runtime envelope;
- donor influence thresholds that can be specified without seeing D_shared outcomes.

Do **not** choose final qualification thresholds by looking at D_shared results.

Do not run the final measurement-qualification experiment yet unless a newer repo authority explicitly freezes the numeric plan.

## Return package

Return one report with these sections:

A. Q_DEPTH lossless-preimage result
B. Q_DETECT lossless-preimage result
C. matching-stratum occupancy
D. support-measurability redundancy proof
E. 14-diagnostic FULL104 reconnaissance evidence map + root SHA
F. feature-lineage hardened evidence package
G. F1/F2/F3 terminals
H. data-informed inputs for the future measurement-qualification plan
I. exact scripts/commands and hashes
J. explicit no-outcome declaration

If A or B fails, return the STOP terminal and still complete the other non-outcome reconnaissance items that do not depend on a valid V2 matching key.

Final hard boundary:

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
