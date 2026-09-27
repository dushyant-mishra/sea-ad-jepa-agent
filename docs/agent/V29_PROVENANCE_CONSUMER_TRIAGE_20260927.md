# V29 provenance-consumer audit: initial source-trace triage (2026-09-27)

Independent read-only scan of the current PR #178 code at `d3366f18490aa90f8acabf540c6ba6375f23767c`. This is a **targeted preliminary source review**, not an exhaustive grep over every historical snapshot and indirect downstream reader. Nothing here opens controls, reserved readouts or protected outcomes.

## Direct uses of the shared provenance table in the first 19 prioritized live files

| Live source | Provenance use | Finding | Next verification |
|---|---|---|---|
| `scripts/v4/foundation_materialize_discovery_expression.py` lines 34, 46–63 | `HVS_COMMON` / `SEA_AD_COMMON` source_feature_index applied to h5ad CSR column | **Confirmed affected.** Exact 50k artifact contains scrambled HVS/SEA-AD columns; op19 shard physically confirmed. | Decode all affected discovery shards; replay R7/R8/V44 and downstream gene-dependent outputs. |
| `scripts/v4/materialize_full104_phase2_expression.py` lines 161, 177–226 | Same family-level source-index mapping applied to h5ad CSR columns | **Confirmed affected.** Level-4 root cause already diagnosed. | Keep uncorrected originals; validate decoded views, then general-reader mapping across all consumed addresses before training. |
| `scripts/v4/foundation_materialize_nph_discovery_sample.R` lines 10, 18–25 | Per-matrix NPH provenance `source_feature_index+1` applied to `assay(object,\"counts\")` rows of TRAIN full-feature `.qs` derivative | **Needs exact-derivative identity check.** Positional construction parallels Level-4 NPH, but a verification of one artifact is not automatically a verification of a different derivative. | Compare every provenance `source_feature_index` against `rownames(assay(the exact discovery TRAIN derivative,\"counts\"))`; bind its SHA and verify NPH discovery shard counts. |
| `scripts/v4/materialize_full104_phase2_nph_blocks.R` lines 38–55 | Same positional rule on per-matrix NPH derivatives | **Previously verified for NPH52 MG feature axis** (32,176/32,176 and 1-based alternative 0%). | Confirm exact derivative identity and scope for any other NPH operators. Do not infer correctness merely from textbook marker profile. |
| `scripts/v4/foundation_expression_lineage_reaudit.py` | Includes provenance CSV in integrity manifest, re-normalizes existing shard matrices | **Integrity-only consumer.** It proves the frozen shards replay exactly, not that source columns were correctly mapped. | Mark historical PASS as byte-lineage PASS, never semantic-gene correctness. |

The other 14 inspected prioritized scripts showed no literal `source_feature_index` / source provenance table reference in their live source. This does **not** clear indirect consumers of the erroneous discovery NPZ, Level-4 block array, or an equivalent precomputed mapping.

## Required exhaustive follow-through (owner: Claude, source-disk environment)

1. Search **all live source and historical producer snapshots** for the exact provenance basename, alternate copy/basename, `source_feature_index`, `source_to_address`, positional `mapping` uses, and reused source-family table builders. Record source hash, input SHA, whether the consumer touches raw count axes, and each output digest.
2. Build an **artifact dependency graph**, not just a literal-text grep: 50k discovery shards → final NPZ → R7/R8/V44 and gene-labelled PCA/targets; Level-4 blocks → masking/target/expression/reader consumers; source-level NPH branches and any independently materialized pipeline.
3. Categorize direct readers as **CORRECT_SOURCE_AXIS_VERIFIED**, **AFFECTED**, **METADATA_ONLY**, or **UNVERIFIED**. For each affected generated artifact use **REQUIRES_DECODED_REPLAY**, except label-invariant engineering metrics separately proven unaffected. Fail closed for missing or duplicate source identities and ambiguous merged columns.
4. Add a source-axis-negative fixture: two permutations of the same feature set with identical lengths and injective mapping must produce the *same address-identified counts*, or the pipeline must refuse. The old failure would pass all its original internal checks; this fixture must fail the old producer.
5. Prevent future accidental fallback to uncorrected aliases or old cache files; require the exact new corrected-view SHA at downstream consumers. The original artifacts must remain immutable for audit.

## Before teacher-fidelity outcomes: two design qualifications still matter

- **Shared-denominator null:** v3 explicitly admits a shared denominator remains. Depth covariates are not proof that residual technical denominator coupling is gone; a synthetic independent-program numerator control under depth/ambient perturbation must *fail qualification*. Bind this as a prospective acceptance test rather than interpreting a null only after observing real results.
- **Held-out-donor transduction:** v3 uses leave-one-out centering of held-out strata's **own outcome/readout**. This defines a *transductive within-stratum association*, not an inductive prediction on unseen donors. Apply the same preprocessing to real and permuted arms and report the scope prominently. An additional prospective inductive control is appropriate if the intended claim is future-donor prediction.
- **Six related primary tests:** v3 gives each pair a 95th-percentile null threshold but does not explicitly freeze a family-wise/FDR policy for six paired tests. Do not silently imply study-wide 5% error control or program-wide qualification from per-pair thresholds. If confirmatory multiplicity claims are desired, define them in a successor freeze before outcomes.
- **Structural absence:** v3 uses available-only subtraction and says to drop when missingness makes the denominator undefined. Resolve the operative condition for HVS LPL and SEA-AD PGK1 explicitly; missing excluded genes are not measured zeros and should not automatically drop a source that was already qualified for its target panels.

**Execution boundary:** source-consumer audit before control extraction; no teacher fit, no training, no unplanned outcome opening.
