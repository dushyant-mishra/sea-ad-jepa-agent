# Open-Validation Framework Plan v1

## Purpose

Build a future `open_validation/` framework that tests whether final Graph-JEPA evidence tiers generalize to public datasets. The framework should evaluate representation transfer, cell-state concordance, cohort robustness, and, only where appropriate data exist, spatial or perturbational support.

This is a plan only. No external validation run is included here.

## What the framework should not do

- It should not assume or try to force APP, APOE, TLR2, or any current candidate to remain top-ranked.
- It should not treat failure to reproduce a ranking as proof that a gene is biologically irrelevant.
- It should not fabricate spatial, plaque-proximity, or neighborhood evidence from non-spatial data.
- It should not treat an unavailable public artifact as negative evidence.
- It should not silently drop or impute missing genes.
- It should not call a projected embedding reliable without reporting feature coverage and distribution-shift diagnostics.
- It should not convert association, manifold safety, or cross-cohort concordance into a causal claim.

## Proposed modules

### `open_validation/align_to_graph_jepa.py`

Responsibilities:

- Load an external expression matrix and gene identifiers.
- Harmonize gene symbols deterministically.
- Align the matrix to the exact 2,957-feature Graph-JEPA order.
- Report present, missing, duplicated, and remapped genes.
- Apply an explicit missing-feature strategy.
- Produce coverage and reliability diagnostics before projection.

### `open_validation/geo_validation.py`

Responsibilities:

- Load pre-selected public GEO cohorts with donor/sample metadata.
- Separate discovery and confirmatory cohort roles.
- Run donor-aware cell-state or pseudobulk comparisons.
- Test direction and rank concordance without requiring exact numerical replication.
- Mark analyses `not_testable` when target pathology or cell-type metadata are absent.

### `open_validation/cellxgene_validation.py`

Responsibilities:

- Query or load selected CELLxGENE Census microglia/myeloid datasets.
- Apply bounded sampling with dataset and donor provenance.
- Evaluate projection coverage, latent placement, and cell-state concordance.
- Prevent cells from the same donor from crossing validation folds.

### `open_validation/internal_robustness.py`

Responsibilities:

- Re-evaluate final tiers across donor bootstraps, cell subsamples, and pathology strata.
- Report rank stability and direction stability.
- Distinguish robustness from external replication.
- Reuse frozen artifacts; do not retrain unless a later stage explicitly authorizes it.

### `open_validation/no_synapse_evidence_scorecard.py`

Responsibilities:

- Assemble a transparent evidence table for genes or programs where synaptic relevance is hypothesized.
- Record which evidence types are available, absent, or not testable.
- Avoid inferring synapse biology from generic neuronal or inflammatory associations.
- Require direct relevant data before assigning spatial or synaptic support.

## External-matrix adapter rules

1. Align every external matrix to the exact 2,957 Graph-JEPA feature order.
2. Preserve the source gene identifier and the final mapped symbol.
3. Report:
   - total model features;
   - present model features;
   - missing model features;
   - coverage fraction;
   - duplicated or ambiguous mappings;
   - expression sparsity before and after alignment.
4. Never silently substitute genes.
5. Missing features may be imputed only with an explicit method and warning:
   - zero after compatible normalization;
   - reference mean from the training feature space;
   - another pre-specified method justified for that dataset.
6. Store an imputation mask with every projected matrix.
7. Mark projection `unreliable_low_feature_coverage` when coverage falls below a pre-specified threshold. The threshold must be chosen before examining candidate outcomes.
8. Compare external feature distributions with the training reference before interpreting latent distances.
9. Report dataset, donor, assay, disease, brain region, and preprocessing provenance.

## Evidence scorecard

| level | evidence label | minimum interpretation |
| --- | --- | --- |
| 0 | model-implied only | Counterfactual or scorecard hypothesis without added validation. |
| 1 | manifold-QC safe | Perturbation remained within sampled latent support. |
| 2 | internal robustness/stability | Direction or rank is stable across internal resampling or strata. |
| 3 | baseline-comparison support | Added value is shown over relevant simpler baselines for the tested question. |
| 4 | external cohort concordance | Direction, state, or ranking is concordant in an independent cohort. |
| 5 | cell-state/subtype concordance | Evidence is localized to a reproducible cell subtype or state. |
| 6 | spatial/pathology-context support | Direct spatial or pathology-context data support the association. |
| 7 | experimental/perturbation validation | Independent perturbation or wet-lab evidence supports the mechanism. |

Levels are cumulative descriptors, not automatic proof grades. A result can have Level 4 cohort concordance without Level 6 spatial evidence, for example. Every scorecard row should retain individual evidence flags rather than only the maximum level.

## Missing-artifact policy

Use controlled statuses:

- `not_available_public_artifact`: a named public supplement, matrix, image, or metadata table cannot be accessed.
- `not_testable`: the available data do not measure the required modality, target, cell state, or pathology context.
- `insufficient_feature_coverage`: too few Graph-JEPA features are represented for reliable projection.
- `metadata_incomplete`: donor, diagnosis, region, or assay metadata are inadequate for the proposed comparison.
- `not_comparable_preprocessing`: the external representation cannot be made compatible without an unjustified transformation.

For Lu 2026 supplements, spatial public tables, or external cohorts:

1. list the expected artifact;
2. list the attempted source or accession;
3. state the missing fields;
4. assign the controlled status;
5. do not convert missingness into evidence against a candidate.

## Proposed output contract

Each validation adapter should produce:

- a machine-readable manifest;
- feature-coverage table;
- donor/sample inclusion table;
- validation metrics table;
- candidate evidence table;
- concise report with limitations;
- exact command and frozen model identifier.

Candidate evidence rows should include:

- `gene`;
- `dataset`;
- `validation_question`;
- `evidence_level`;
- `evidence_status`;
- `direction_concordant`;
- `feature_coverage_fraction`;
- `donor_aware`;
- `cell_state_specific`;
- `spatial_evidence_available`;
- `perturbation_evidence_available`;
- `claim_boundary`.

## Recommended implementation order

1. Implement and test the feature-alignment adapter on one already-downloaded reference dataset.
2. Add internal robustness outputs as Level 2 evidence.
3. Select one GEO cohort with compatible microglial expression and donor metadata.
4. Add one CELLxGENE cohort for cell-state transfer.
5. Add spatial validation only after a direct spatial/pathology table is available.
6. Add perturbation evidence only from suitable experimental datasets.

## Current boundary

The current project has completed manifold QC and a baseline comparison gate. The baseline gate did not establish overall Graph-JEPA superiority over simpler representations. Future open validation should therefore test where the framework adds useful, reproducible evidence, not attempt to confirm a predetermined winner or candidate ranking.
