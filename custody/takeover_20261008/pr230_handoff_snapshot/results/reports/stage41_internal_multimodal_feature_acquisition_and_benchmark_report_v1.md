# Stage 41 internal multimodal feature acquisition and benchmark report

## Why Stage 41 was run

Stage 40B concluded that Stage 27C remains the locked benchmark and that internal architecture tuning on the current feature matrix should pause. Stage 41 therefore inventories genuinely new safe internal multimodal/spatial/image feature sources before any further benchmark rescue.

## Source inventory

| source_path | file_name | feature_class_guess | matched_keywords | size_bytes | extension | likely_donor_linked | internal_or_external_guess | stage41_candidate_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| results\reports\stage39d_metadata_composition_stack_report_v1.md | stage39d_metadata_composition_stack_report_v1.md | composition_candidate | composition | 23600 | .md | True | internal_or_project | candidate_for_manual_review |
| results\reports\stage39d_pi_metadata_composition_summary_v1.md | stage39d_pi_metadata_composition_summary_v1.md | composition_candidate | composition | 4897 | .md | True | internal_or_project | candidate_for_manual_review |
| results\reports\stage39h_proxy_safe_composition_decomposition_report_v1.md | stage39h_proxy_safe_composition_decomposition_report_v1.md | composition_candidate | composition | 47824 | .md | True | internal_or_project | candidate_for_manual_review |
| results\tables\stage39d_composition_proxy_audit_v1.csv | stage39d_composition_proxy_audit_v1.csv | composition_candidate | composition | 4787 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\stage39d_donor_composition_features_v1.csv | stage39d_donor_composition_features_v1.csv | composition_candidate | composition | 26680 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\stage39d_restricted_composition_sensitivity_v1.csv | stage39d_restricted_composition_sensitivity_v1.csv | composition_candidate | composition | 1642 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\stage39h_composition_only_results_v1.csv | stage39h_composition_only_results_v1.csv | composition_candidate | composition | 277 | .csv | True | internal_or_project | candidate_for_manual_review |
| data\external\grubman_gse138852\GSE138852_covariates.csv.gz | GSE138852_covariates.csv.gz | covariate_candidate | covariate | 86792 | .gz | False | external_or_public | candidate_for_manual_review |
| results\reports\sea_ad_full_metadata_covariate_audit.md | sea_ad_full_metadata_covariate_audit.md | covariate_candidate | covariate | 3100 | .md | True | internal_or_project | candidate_for_manual_review |
| results\tables\sea_ad_full_metadata_covariate_audit.csv | sea_ad_full_metadata_covariate_audit.csv | covariate_candidate | covariate | 8198 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\sea_ad_full_metadata_targets_with_covariates.csv | sea_ad_full_metadata_targets_with_covariates.csv | covariate_candidate | covariate | 63304 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\stage39c_feature_covariate_audit_v1.csv | stage39c_feature_covariate_audit_v1.csv | covariate_candidate | covariate | 240 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_gse174367_covariate_audit.csv | v2_1_gse174367_covariate_audit.csv | covariate_candidate | covariate | 704 | .csv | False | external_or_public | candidate_for_manual_review |
| results\tables\v2_1_target_validation_covariate_correlations.csv | v2_1_target_validation_covariate_correlations.csv | covariate_candidate | covariate | 6169 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_target_validation_covariate_flags.csv | v2_1_target_validation_covariate_flags.csv | covariate_candidate | covariate | 2077 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_target_validation_full_covariates_alien_cell_check.csv | v2_1_target_validation_full_covariates_alien_cell_check.csv | covariate_candidate | covariate | 1178 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_target_validation_full_covariates_covariate_correlations.csv | v2_1_target_validation_full_covariates_covariate_correlations.csv | covariate_candidate | covariate | 8707 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_target_validation_full_covariates_covariate_flags.csv | v2_1_target_validation_full_covariates_covariate_flags.csv | covariate_candidate | covariate | 1490 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_target_validation_full_covariates_report.md | v2_1_target_validation_full_covariates_report.md | covariate_candidate | covariate | 1454 | .md | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_target_validation_full_covariates_validated_target_matrix.csv | v2_1_target_validation_full_covariates_validated_target_matrix.csv | covariate_candidate | covariate | 6631 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_1_target_validation_full_covariates_within_state_check.csv | v2_1_target_validation_full_covariates_within_state_check.csv | covariate_candidate | covariate | 775 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_2_target_covariate_audit.csv | v2_2_target_covariate_audit.csv | covariate_candidate | covariate | 1798 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\v2_2_target_covariate_audit_long.csv | v2_2_target_covariate_audit_long.csv | covariate_candidate | covariate | 2890 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\grubman_zero_shot_sample_pool_embeddings.csv | grubman_zero_shot_sample_pool_embeddings.csv | embedding_candidate | embedding | 422 | .csv | False | external_or_public | candidate_for_manual_review |
| results\tables\gse138852_graph_jepa_zero_shot_aligned_donor_embeddings.csv | gse138852_graph_jepa_zero_shot_aligned_donor_embeddings.csv | embedding_candidate | embedding | 10785 | .csv | True | external_or_public | candidate_for_manual_review |
| results\tables\gse138852_graph_jepa_zero_shot_baseline_donor_embeddings.csv | gse138852_graph_jepa_zero_shot_baseline_donor_embeddings.csv | embedding_candidate | embedding | 10357 | .csv | True | external_or_public | candidate_for_manual_review |
| results\tables\gse138852_graph_jepa_zero_shot_donor_embeddings.csv | gse138852_graph_jepa_zero_shot_donor_embeddings.csv | embedding_candidate | embedding | 10153 | .csv | True | external_or_public | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_cell_embeddings.csv | microglia_pvm_jepa_all_module_preserved_cell_embeddings.csv | embedding_candidate | embedding | 62243025 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_donor_embeddings.csv | microglia_pvm_jepa_all_module_preserved_donor_embeddings.csv | embedding_candidate | embedding | 143004 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_e100_cell_embeddings.csv | microglia_pvm_jepa_all_module_preserved_e100_cell_embeddings.csv | embedding_candidate | embedding | 62212055 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_e100_donor_embeddings.csv | microglia_pvm_jepa_all_module_preserved_e100_donor_embeddings.csv | embedding_candidate | embedding | 142987 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_e100_embedding_ridge.csv | microglia_pvm_jepa_all_module_preserved_e100_embedding_ridge.csv | embedding_candidate | embedding | 1694 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_embedding_ridge.csv | microglia_pvm_jepa_all_module_preserved_embedding_ridge.csv | embedding_candidate | embedding | 1693 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_cell_embeddings.csv | microglia_pvm_jepa_cell_embeddings.csv | embedding_candidate | embedding | 15558995 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_donor_embeddings.csv | microglia_pvm_jepa_donor_embeddings.csv | embedding_candidate | embedding | 137481 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_cell_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e10_cell_embeddings.csv | embedding_candidate | embedding | 61585736 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_donor_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e10_donor_embeddings.csv | embedding_candidate | embedding | 137035 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_embedding_ridge.csv | microglia_pvm_jepa_ema_expanded_balanced_e10_embedding_ridge.csv | embedding_candidate | embedding | 1701 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_cell_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e20_cell_embeddings.csv | embedding_candidate | embedding | 61740923 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv | embedding_candidate | embedding | 137467 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_embedding_ridge.csv | microglia_pvm_jepa_ema_expanded_balanced_e20_embedding_ridge.csv | embedding_candidate | embedding | 1693 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_cell_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e30_cell_embeddings.csv | embedding_candidate | embedding | 61879365 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_donor_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e30_donor_embeddings.csv | embedding_candidate | embedding | 138107 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_embedding_ridge.csv | microglia_pvm_jepa_ema_expanded_balanced_e30_embedding_ridge.csv | embedding_candidate | embedding | 1703 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_cell_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e40_cell_embeddings.csv | embedding_candidate | embedding | 61959919 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_donor_embeddings.csv | microglia_pvm_jepa_ema_expanded_balanced_e40_donor_embeddings.csv | embedding_candidate | embedding | 138566 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_embedding_ridge.csv | microglia_pvm_jepa_ema_expanded_balanced_e40_embedding_ridge.csv | embedding_candidate | embedding | 1698 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_cell_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e10_cell_embeddings.csv | embedding_candidate | embedding | 61586381 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_donor_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e10_donor_embeddings.csv | embedding_candidate | embedding | 136915 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_embedding_ridge.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e10_embedding_ridge.csv | embedding_candidate | embedding | 1705 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_cell_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e20_cell_embeddings.csv | embedding_candidate | embedding | 61745341 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_donor_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e20_donor_embeddings.csv | embedding_candidate | embedding | 137506 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_embedding_ridge.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e20_embedding_ridge.csv | embedding_candidate | embedding | 1699 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_cell_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e30_cell_embeddings.csv | embedding_candidate | embedding | 61882912 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv | embedding_candidate | embedding | 138150 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_embedding_ridge.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e30_embedding_ridge.csv | embedding_candidate | embedding | 1702 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_cell_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e40_cell_embeddings.csv | embedding_candidate | embedding | 61959516 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_donor_embeddings.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e40_donor_embeddings.csv | embedding_candidate | embedding | 138460 | .csv | True | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_embedding_ridge.csv | microglia_pvm_jepa_ema_var_expanded_balanced_e40_embedding_ridge.csv | embedding_candidate | embedding | 1696 | .csv | False | internal_or_project | candidate_for_manual_review |
| results\tables\microglia_pvm_jepa_embedding_ridge.csv | microglia_pvm_jepa_embedding_ridge.csv | embedding_candidate | embedding | 1693 | .csv | False | internal_or_project | candidate_for_manual_review |

## Feature blocks and risk tiers

| feature_block_id | feature_class | n_sources | source_examples | risk_tiers_observed | available_for_training | notes |
| --- | --- | --- | --- | --- | --- | --- |
| composition_candidate | composition_candidate | 7 | results\reports\stage39d_metadata_composition_stack_report_v1.md;results\reports\stage39d_pi_metadata_composition_summary_v1.md;results\reports\stage39h_proxy_safe_composition_decomposition_report_v1.md;results\tables\stage39d_composition_proxy_audit_v1.csv;results\tables\stage39d_donor_composition_features_v1.csv | 2 | False | requires manual donor-linkage/provenance review before benchmark use |
| covariate_candidate | covariate_candidate | 16 | data\external\grubman_gse138852\GSE138852_covariates.csv.gz;results\reports\sea_ad_full_metadata_covariate_audit.md;results\tables\sea_ad_full_metadata_covariate_audit.csv;results\tables\sea_ad_full_metadata_targets_with_covariates.csv;results\tables\stage39c_feature_covariate_audit_v1.csv | 1;4 | True | requires manual donor-linkage/provenance review before benchmark use |
| embedding_candidate | embedding_candidate | 69 | results\tables\grubman_zero_shot_sample_pool_embeddings.csv;results\tables\gse138852_graph_jepa_zero_shot_aligned_donor_embeddings.csv;results\tables\gse138852_graph_jepa_zero_shot_baseline_donor_embeddings.csv;results\tables\gse138852_graph_jepa_zero_shot_donor_embeddings.csv;results\tables\microglia_pvm_jepa_all_module_preserved_cell_embeddings.csv | 4 | False | requires manual donor-linkage/provenance review before benchmark use |
| pathology_named_candidate | pathology_named_candidate | 193 | data\processed\metadata\pathology_target_columns.csv;data\processed\metadata\pathology_target_spearman_corr.csv;data\processed\metadata\pathology_target_summary.csv;data\processed\metadata\sea_ad_mtg_donor_pathology_targets.csv;data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad | 0;3 | False | requires manual donor-linkage/provenance review before benchmark use |
| spatial_or_neighborhood_candidate | spatial_or_neighborhood_candidate | 4 | results\reports\discovery_graph_neighborhood_coherence.md;results\reports\discovery_scorecard_v2_graph_neighborhood_coherence.md;results\tables\discovery_graph_neighborhood_coherence.csv;results\tables\discovery_scorecard_v2_graph_neighborhood_coherence.csv | 2 | False | requires manual donor-linkage/provenance review before benchmark use |

| source_path | feature_class_guess | risk_tier | allowed_for_benchmark_candidate | comparator_only | forbidden | reason | recommended_use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| results\reports\stage39d_metadata_composition_stack_report_v1.md | composition_candidate | 2 | False | False | False | biologically meaningful but target-adjacent feature class | caution_candidate_after_proxy_audit |
| results\reports\stage39d_pi_metadata_composition_summary_v1.md | composition_candidate | 2 | False | False | False | biologically meaningful but target-adjacent feature class | caution_candidate_after_proxy_audit |
| results\reports\stage39h_proxy_safe_composition_decomposition_report_v1.md | composition_candidate | 2 | False | False | False | biologically meaningful but target-adjacent feature class | caution_candidate_after_proxy_audit |
| results\tables\stage39d_composition_proxy_audit_v1.csv | composition_candidate | 2 | False | False | False | biologically meaningful but target-adjacent feature class | caution_candidate_after_proxy_audit |
| results\tables\stage39d_donor_composition_features_v1.csv | composition_candidate | 2 | False | False | False | biologically meaningful but target-adjacent feature class | caution_candidate_after_proxy_audit |
| results\tables\stage39d_restricted_composition_sensitivity_v1.csv | composition_candidate | 2 | False | False | False | biologically meaningful but target-adjacent feature class | caution_candidate_after_proxy_audit |
| results\tables\stage39h_composition_only_results_v1.csv | composition_candidate | 2 | False | False | False | biologically meaningful but target-adjacent feature class | caution_candidate_after_proxy_audit |
| data\external\grubman_gse138852\GSE138852_covariates.csv.gz | covariate_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\reports\sea_ad_full_metadata_covariate_audit.md | covariate_candidate | 1 | True | False | False | safe pre-pathology metadata/context candidate if provenance is confirmed | manual_review_then_candidate |
| results\tables\sea_ad_full_metadata_covariate_audit.csv | covariate_candidate | 1 | True | False | False | safe pre-pathology metadata/context candidate if provenance is confirmed | manual_review_then_candidate |
| results\tables\sea_ad_full_metadata_targets_with_covariates.csv | covariate_candidate | 1 | True | False | False | safe pre-pathology metadata/context candidate if provenance is confirmed | manual_review_then_candidate |
| results\tables\stage39c_feature_covariate_audit_v1.csv | covariate_candidate | 1 | True | False | False | safe pre-pathology metadata/context candidate if provenance is confirmed | manual_review_then_candidate |
| results\tables\v2_1_gse174367_covariate_audit.csv | covariate_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\v2_1_target_validation_covariate_correlations.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_1_target_validation_covariate_flags.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_1_target_validation_full_covariates_alien_cell_check.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_1_target_validation_full_covariates_covariate_correlations.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_1_target_validation_full_covariates_covariate_flags.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_1_target_validation_full_covariates_report.md | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_1_target_validation_full_covariates_validated_target_matrix.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_1_target_validation_full_covariates_within_state_check.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_2_target_covariate_audit.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\v2_2_target_covariate_audit_long.csv | covariate_candidate | 4 | False | False | True | possible target-derived or disease-state proxy feature | forbidden_for_training |
| results\tables\grubman_zero_shot_sample_pool_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\gse138852_graph_jepa_zero_shot_aligned_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\gse138852_graph_jepa_zero_shot_baseline_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\gse138852_graph_jepa_zero_shot_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_e100_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_e100_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_e100_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_all_module_preserved_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_cell_embeddings.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_donor_embeddings.csv | embedding_candidate | 4 | False | False | True | unclear provenance | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |
| results\tables\microglia_pvm_jepa_embedding_ridge.csv | embedding_candidate | 4 | False | False | True | not clearly donor-linked or provenance unclear | missing_or_manual_review |

## Safe feature matrix manifest

| safe_feature_matrix_built | reason | n_candidate_sources | n_new_safe_multimodal_sources | candidate_source_paths | matrix_path | training_allowed |
| --- | --- | --- | --- | --- | --- | --- |
| False | new donor-linked safe multimodal/spatial/image feature table not found | 289 | 0 |  |  | False |

## Missing feature acquisition plan

| feature_class | required_source | internal_or_external | currently_available | expected_biological_signal | expected_target_relevance | leakage_risk | proxy_risk | acquisition_complexity | preprocessing_needed | donor_linkage_needed | allowed_use | prohibited_use | priority | proposed_next_stage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| image-derived morphology features | internal pathology image tiles/whole-slide morphology table linked to donor/section | internal | False | plaque/tangle/glial morphology | AT8/6e10/GFAP/Iba1/NeuN residual variation | medium | medium | high | tile QC; feature extraction; donor/section linkage; train-fold normalization | donor_id and section_id | candidate benchmark after proxy audit | target label-derived morphology or post-hoc target scores | high | Stage41A_manual_internal_feature_acquisition |
| pathology image embeddings | internal image encoder embeddings not trained on held-out target labels | internal | False | morphology and tissue architecture | pathology morphology without scalar target leakage | medium | medium | high | embedding provenance audit; donor aggregation | donor_id and slide/tile IDs | candidate benchmark after provenance audit | embeddings trained on target labels | high | Stage41A_manual_internal_feature_acquisition |
| section-level image descriptors | section/tile QC and morphology descriptors | internal | False | section heterogeneity and staining context | technical/pathology context | low_to_medium | medium | medium | section linkage; train-fold aggregation | donor_id and section_id | covariate/context benchmark after audit | direct pathology score reuse | high | Stage41A_manual_internal_feature_acquisition |
| spatial neighborhood summaries | cell coordinates/spatial transcriptomics neighborhoods | internal | False | cell-cell and plaque-neighborhood context | GFAP/Iba1/NeuN local microenvironment | medium | medium | high | neighborhood computation without targets | donor_id/cell/spot coordinates | candidate benchmark after proxy audit | target-derived neighborhoods | high | Stage41A_manual_internal_feature_acquisition |
| region/anatomy covariates | safe anatomy/region labels known before target scoring | internal | False | anatomical context | stabilize donor-level variation | low | low | medium | manual provenance audit | donor_id/region | Tier1 context covariate | post-target region proxies | medium | Stage41A_manual_internal_feature_acquisition |
| cell-density or neighborhood composition | local cell density tables | internal | False | cell abundance/neighborhood context | gliosis/neuron preservation | medium | medium | high | local density computation; proxy audit | donor_id/section/celltype | Tier2 caution candidate | global disease-state labels | medium | Stage41A_manual_internal_feature_acquisition |
| manual curated internal covariates | curated pathology/slide notes with known provenance | internal | False | expert morphology/context descriptors | broad pathology context | medium | medium | medium | manual curation and leakage audit | donor_id/section_id | candidate after provenance audit | held-out target-derived pseudo-labels | medium | Stage41A_manual_internal_feature_acquisition |
| clean external metadata | external dataset metadata repair | external | False | support/readiness only | cross-dataset support context | low | medium | medium | metadata repair/harmonization | sample/cell IDs | support/readiness only | training/model selection or clean validation claim | medium | Stage41B_external_metadata_repair |

## Benchmark decision

| candidate_id | feature_set_id | model_name | feature_classes_used | risk_tiers_used | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39e_pca8 | delta_vs_stage39h_context | lower_ci_above_stage27c | lower_ci_above_material_threshold | target_guard_pass | abeta_guard_pass | iba1_rescue_status | negative_controls_pass | proxy_leakage_risk_pass | high_influence_donor_or_fold_flag | benchmark_lock_eligible | recommended_decision | allowed_claim_language | prohibited_claim_language | recommended_next_stage | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage41_safe_multimodal_candidate | latent_plus_safe_multimodal | ridge |  |  |  |  |  |  | False | False | False | False | not_tested_missing_safe_features | False | False | False | False | manual_feature_acquisition_required | internal multimodal feature acquisition planning only | external validation; causal; therapeutic; gene-ablation; disease-modifying claims | Stage41A_manual_internal_feature_acquisition | new donor-linked safe multimodal/spatial/image feature table not found |

## Claim boundaries

| audit_item | pass | evidence |
| --- | --- | --- |
| no_external_data_used_for_model_training | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| no_external_model_selection | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| no_candidate_selection | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| frozen_candidates_preserved | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| donor_held_out_evaluation_preserved | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| train_fold_only_preprocessing_preserved | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| forbidden_features_excluded | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| proxy_risk_features_comparator_only | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| negative_controls_reported | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| no_clean_external_validation_claim | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| no_causal_claim | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| no_therapeutic_claim | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| no_gene_ablation_claim | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| no_disease_modifying_claim | True | Stage 41 inventory/acquisition workflow; no unsupported claims. |
| safety_audit_pass | True | all safety checks passed |

## Interpretation

No new donor-linked safe multimodal/spatial/image feature matrix was found in the repository. Stage 41 therefore did not run benchmark training and recommends manual/internal feature acquisition before further internal rescue modeling.
