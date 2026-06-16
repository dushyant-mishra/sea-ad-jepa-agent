# Discovery Atlas Input Availability

This report is Step 0 for the Graph-JEPA Discovery Atlas. It records which existing repo outputs can support the next analyses without retraining or fabricating missing evidence.

## Status Summary

- `available`: 12
- `available_but_needs_parsing`: 9
- `missing`: 1
- `optional`: 0
- `blocked`: 0

## Phase 1 Gate

Phase 1 is clear: all required minimal inputs are present. Some inputs still need deliberate parsing, but there is no blocker for pathology-axis fingerprints and a first discovery scorecard.

## Minimal Viable Phase 1 Inputs

- `gene_multitarget_counterfactual_summary` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_multitarget_gene_counterfactual_summary.csv`
  - role: Primary gene-level multi-pathology fingerprint input.
- `module_multitarget_counterfactual_summary` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_multitarget_module_counterfactual_summary.csv`
  - role: Primary module-level multi-pathology fingerprint input.
- `pathology_head_gene_counterfactual_summary` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/pathology_head_gene_counterfactual_summary.csv`
  - role: Frozen Stage B pathology-head counterfactual readout with manifold-safety columns.
- `ranked_target_matrix` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_ranked_target_matrix.csv`
  - role: v2.1 ranked target matrix from latent decoding and counterfactual extraction.
- `validated_target_matrix_full_covariates` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_target_validation_full_covariates_validated_target_matrix.csv`
  - role: Validated target matrix with manifold, covariate, and within-state artifact checks.
- `target_covariate_audit_wide` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/v2_2_target_covariate_audit.csv`
  - role: Target-level donor covariate and technical-proxy audit.
- `druggability_biomarker_summary` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/v2_2_druggability_summary.csv`
  - role: UniProt localization and ChEMBL triage for artifact-cleared targets.
- `consensus_graph_edges` - **available**
  - path: `C:/Users/dushy/Desktop/Jepa project/results/tables/v2_graph_consensus_edges.csv`
  - role: Consensus graph edges for 1-hop and 2-hop target-neighborhood coherence.
- `module_definitions` - **available_but_needs_parsing**
  - path: `C:/Users/dushy/Desktop/Jepa project/src/sea_ad_jepa/gene_sets.py`
  - role: Gene-module definitions for module scoring and module fingerprints.
- `donor_pathology_metadata` - **available_but_needs_parsing**
  - path: `C:/Users/dushy/Desktop/Jepa project/data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv`
  - role: Donor-level pathology and covariates for context dependency and audits.

## Recommended Next Analyses

1. Build gene and module pathology-axis fingerprints from `v2_1_multitarget_*_counterfactual_summary.csv`.
2. Merge covariate and druggability annotations into a first discovery scorecard.
3. Add graph-neighborhood coherence using `v2_graph_consensus_edges.csv`.
4. Treat donor-context dependency and pairwise interaction screens as optional until by-donor or paired-perturbation inputs are confirmed.
5. Add negative controls before making strong discovery-tier claims; current negative-control inputs are incomplete unless new files are added.

## Full Input Table

| input_key | category | priority | status | primary_path | role | recommended_action |
| --- | --- | --- | --- | --- | --- | --- |
| gene_multitarget_counterfactual_summary | counterfactual_deltas | core | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_multitarget_gene_counterfactual_summary.csv | Primary gene-level multi-pathology fingerprint input. | Ready for direct table loading. |
| module_multitarget_counterfactual_summary | counterfactual_deltas | core | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_multitarget_module_counterfactual_summary.csv | Primary module-level multi-pathology fingerprint input. | Ready for direct table loading. |
| pathology_head_gene_counterfactual_summary | counterfactual_deltas | core | available | C:/Users/dushy/Desktop/Jepa project/results/tables/pathology_head_gene_counterfactual_summary.csv | Frozen Stage B pathology-head counterfactual readout with manifold-safety columns. | Ready for direct table loading. |
| pathology_head_module_counterfactual_summary | counterfactual_deltas | recommended | available | C:/Users/dushy/Desktop/Jepa project/results/tables/pathology_head_module_counterfactual_summary.csv | Frozen Stage B module-level pathology-head counterfactual readout. | Ready for direct table loading. |
| ranked_target_matrix | target_prioritization | core | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_ranked_target_matrix.csv | v2.1 ranked target matrix from latent decoding and counterfactual extraction. | Ready for direct table loading. |
| validated_target_matrix_full_covariates | artifact_validation | core | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_target_validation_full_covariates_validated_target_matrix.csv | Validated target matrix with manifold, covariate, and within-state artifact checks. | Ready for direct table loading. |
| target_covariate_audit_wide | artifact_validation | core | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_2_target_covariate_audit.csv | Target-level donor covariate and technical-proxy audit. | Ready for direct table loading. |
| target_covariate_audit_long | artifact_validation | recommended | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_2_target_covariate_audit_long.csv | Long-form covariate audit with per-covariate p-values and warning flags. | Ready for direct table loading. |
| druggability_biomarker_summary | translation | recommended | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_2_druggability_summary.csv | UniProt localization and ChEMBL triage for artifact-cleared targets. | Ready for direct table loading. |
| consensus_graph_edges | graph_topology | core | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_graph_consensus_edges.csv | Consensus graph edges for 1-hop and 2-hop target-neighborhood coherence. | Ready for direct table loading. |
| consensus_graph_stats | graph_topology | recommended | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_graph_consensus_stats.csv | Summary statistics for the consensus graph. | Ready for direct table loading. |
| string_graph_edges | graph_topology | optional | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_graph_string_edges_t700.csv | STRING graph source for graph-source ablations. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| wgcna_graph_edges | graph_topology | optional | available | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_graph_wgcna_edges.csv | WGCNA/TOM graph source for graph-source ablations. | Ready for direct table loading. |
| module_definitions | modules | core | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/src/sea_ad_jepa/gene_sets.py | Gene-module definitions for module scoring and module fingerprints. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| donor_pathology_metadata | metadata | core | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv | Donor-level pathology and covariates for context dependency and audits. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| donor_level_counterfactual_outputs | donor_context | recommended | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_upgrade_fine_08_gene_counterfactual_6e10_by_donor.csv | By-donor counterfactual deltas for donor-context dependency. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| baseline_prediction_leaderboard | baselines | recommended | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/results/tables/multitarget_oof_jepa_vs_pseudobulk_summary.csv | Existing donor-held-out baseline metrics for minimal Graph-JEPA sanity check. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| stage_c_sweep_leaderboards | baselines | optional | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/results/tables/stage_c_finetuning_combined_leaderboard.csv | Stage C sweep and checkpoint summaries for current active model context. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| negative_control_outputs | negative_controls | recommended | missing |  | Existing shuffled-label, decoy, degree-matched, or random-graph control outputs. | Required/recommended input is absent; write TODO row in downstream atlas. |
| target_rank_stability_outputs | robustness | recommended | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/results/tables/stage_c_fine_loose_01_r005_cov0005_epoch_005_cosine_knn_metrics.csv | Bootstrap, jackknife, seed, or leave-one-donor-out target-rank stability. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| latent_jacobian_outputs | latent_interpretation | optional | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_1_upgrade_fine_08_latent_jacobian_top_edges.csv | Latent Jacobian edges and module annotations for mechanism-context notes. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
| abeta_responsive_outputs | amyloid_axis | optional | available_but_needs_parsing | C:/Users/dushy/Desktop/Jepa project/results/tables/v2_2_abeta_frozen_embedding_elasticnet_sweep.csv | Frozen A beta ElasticNet and responder-cell outputs for bounded amyloid notes. | Multiple matching files or globbed inputs; downstream script must choose/merge deliberately. |
