# Stage 36B local knowledge grounding report v1

## 1. Executive summary

Stage 36B run pass: `True`. Knowledge grounding pass: `True`. Stable local resources: `103`.
Stage 36B performs local prior-knowledge grounding of Stage 36A model-implied hypotheses. Knowledge support is not validation.

## 2. Why Stage 36B was run

Stage 36A generated module-level and projected gene-level hypotheses but did not have a stable local knowledge schema for annotation.

## 3. Inputs from Stage 36A

Stage 36A gene hypotheses evaluated: `770`.

## 4. Local resource inventory

```csv
path,size_bytes,extension,keyword_hits,scanned,exclusion_reason
docs\ACTIVE_V3_STATUS.md,11577,.md,AD;GFAP;Iba1;NeuN;microglia,True,
docs\architecture.md,6397,.md,AD;GFAP;GO;Iba1;NeuN;amyloid;microglia;tau,True,
docs\causal_discovery.md,8196,.md,AD;APOE;Alzheimer;GO;TREM2;antigen presentation;complement;lysosome;microglia;phagocytosis;tau,True,
docs\cleanup_manifest.md,1461,.md,AD,True,
docs\current_status.md,97692,.md,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;NeuN;TREM2;amyloid;antigen presentation;chemokine;complement;interferon;lysosome;microglia;oxidative stress;phagocytosis;senescence;tau,True,
docs\dataset_guide.md,12163,.md,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;NeuN;TREM2;amyloid;complement;microglia;phagocytosis;tau,True,
docs\DATASET_REGISTRY.md,4306,.md,AD;Alzheimer;DAM;microglia,True,
docs\external_cohort_reconnaissance.md,5447,.md,AD;Alzheimer;GO;microglia;tau,True,
docs\external_perturbation_benchmarks.md,11014,.md,AD;APOE;Alzheimer;DAM;GO;TREM2;complement;microglia,True,
docs\external_validation_next_steps.md,11567,.md,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;amyloid;antigen presentation;chemokine;complement;lysosome;microglia;phagocytosis;tau,True,
docs\figure_gallery.md,7619,.md,AD;GFAP;NeuN;amyloid;microglia;tau,True,
docs\github_about.md,2482,.md,AD;APOE;Alzheimer;amyloid;microglia,True,
docs\github_repo_checklist.md,1850,.md,AD;Alzheimer;GO;microglia,True,
docs\gpu_setup.md,2341,.md,AD,True,
docs\project_proposal.md,7618,.md,AD;APOE;Alzheimer;GFAP;GO;Iba1;NeuN;TREM2;amyloid;complement;lysosome;microglia;phagocytosis;tau,True,
docs\runbook.md,76980,.md,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;NeuN;TREM2;amyloid;complement;lysosome;microglia;phagocytosis;senescence;tau,True,
docs\scientific_pitch.md,5222,.md,AD;Alzheimer;GFAP;GO;Iba1;NeuN;complement;microglia;tau,True,
docs\stage_c_v21_upgrade_experiments.md,3673,.md,AD;GFAP;NeuN,True,
docs\technical_plan.md,8151,.md,AD;Alzheimer;GFAP;GO;NeuN;complement;lysosome;microglia;phagocytosis,True,
docs\V3_SCORECARD.md,10659,.md,AD;GFAP;GO;Iba1;NeuN;microglia,True,
configs\train\stage34a_hbca_microglia_filtered_external_pretraining_v1.yaml,2556,.yaml,AD;GFAP;Iba1;NeuN;microglia,True,
configs\train\stage_b_adversarial.yaml,1460,.yaml,AD;microglia,True,
results\tables\causal_fold_specific_two_pass_test_loaded.csv,8000,.csv,AD;TREM2;microglia,True,
results\tables\causal_fold_specific_two_pass_test_loaded_modules.csv,5282,.csv,AD;APOE;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\cellxgene_normal_microglia_anchor_qc.csv,260,.csv,microglia,True,
results\tables\cellxgene_normal_microglia_assay_counts.csv,128,.csv,microglia,True,
results\tables\cellxgene_normal_microglia_dataset_id_counts.csv,1558,.csv,AD;microglia,True,
results\tables\cellxgene_normal_microglia_development_stage_counts.csv,3161,.csv,AD;microglia,True,
results\tables\cellxgene_normal_microglia_disease_counts.csv,29,.csv,microglia,True,
results\tables\cellxgene_normal_microglia_donor_id_counts.csv,8141,.csv,AD;microglia,True,
results\tables\cellxgene_normal_microglia_matched_genes.csv,18141,.csv,AD;APOE;DAM;GO;TREM2;microglia;tau,True,
results\tables\cellxgene_normal_microglia_missing_genes.csv,877,.csv,microglia,True,
results\tables\cellxgene_normal_microglia_suspension_type_counts.csv,38,.csv,microglia,True,
results\tables\cellxgene_normal_microglia_tissue_counts.csv,915,.csv,microglia,True,
results\tables\cellxgene_normal_microglia_tissue_general_counts.csv,35,.csv,microglia,True,
results\tables\cell_level_mixing_sample_metadata.csv,350197,.csv,AD,True,
results\tables\confounder_adjusted_module_effects_at8.csv,2945,.csv,AD;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\confounder_adjusted_top_gene_effects_at8.csv,1856,.csv,AD,True,
results\tables\gse138852_graph_jepa_zero_shot_aligned_sea_ad_trajectory_vectors.csv,14213,.csv,AD;GFAP;Iba1;NeuN;tau,True,
results\tables\gse138852_graph_jepa_zero_shot_baseline_sea_ad_trajectory_vectors.csv,14213,.csv,AD;GFAP;Iba1;NeuN;tau,True,
results\tables\microglia_pvm_jepa_all_module_preserved_cell_embeddings.csv,62243025,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_all_module_preserved_donor_embeddings.csv,143004,.csv,microglia,True,
results\tables\microglia_pvm_jepa_all_module_preserved_e100_cell_embeddings.csv,62212055,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_all_module_preserved_e100_donor_embeddings.csv,142987,.csv,microglia,True,
results\tables\microglia_pvm_jepa_all_module_preserved_e100_embedding_ridge.csv,1694,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_all_module_preserved_embedding_ridge.csv,1693,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_cell_embeddings.csv,15558995,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_donor_embeddings.csv,137481,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_cell_embeddings.csv,61585736,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_donor_embeddings.csv,137035,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_embedding_ridge.csv,1701,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_cell_embeddings.csv,61740923,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv,137467,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_embedding_ridge.csv,1693,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_cell_embeddings.csv,61879365,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_donor_embeddings.csv,138107,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_embedding_ridge.csv,1703,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_cell_embeddings.csv,61959919,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_donor_embeddings.csv,138566,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_embedding_ridge.csv,1698,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_cell_embeddings.csv,61586381,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_donor_embeddings.csv,136915,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_embedding_ridge.csv,1705,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_cell_embeddings.csv,61745341,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_donor_embeddings.csv,137506,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_embedding_ridge.csv,1699,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_cell_embeddings.csv,61882912,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv,138150,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_embedding_ridge.csv,1702,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_cell_embeddings.csv,61959516,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_donor_embeddings.csv,138460,.csv,microglia,True,
results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_embedding_ridge.csv,1696,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_embedding_ridge.csv,1693,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_expanded_modules_balanced_e40_cell_embeddings.csv,62196625,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_expanded_modules_balanced_e40_donor_embeddings.csv,142084,.csv,microglia,True,
results\tables\microglia_pvm_jepa_expanded_modules_balanced_e40_embedding_ridge.csv,1704,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_expanded_modules_balanced_e80_cell_embeddings.csv,62197824,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_expanded_modules_balanced_e80_donor_embeddings.csv,142596,.csv,microglia,True,
results\tables\microglia_pvm_jepa_expanded_modules_balanced_e80_embedding_ridge.csv,1693,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_mixed_cell_embeddings.csv,15522488,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_mixed_donor_embeddings.csv,137737,.csv,microglia,True,
results\tables\microglia_pvm_jepa_mixed_embedding_ridge.csv,1677,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_jepa_module_preserved_cell_embeddings.csv,15554599,.csv,,False,file_exceeds_size_limit
results\tables\microglia_pvm_jepa_module_preserved_donor_embeddings.csv,138145,.csv,microglia,True,
results\tables\microglia_pvm_jepa_module_preserved_embedding_ridge.csv,1687,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_model_comparison.csv,11419,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\microglia_pvm_percent_AT8_gene_rankings.csv,1139444,.csv,AD;APOE;DAM;GFAP;GO;microglia;tau,True,
results\tables\microglia_pvm_percent_AT8_gene_set_scores.csv,421,.csv,APOE;TREM2;complement;interferon;microglia,True,
results\tables\microglia_pvm_pseudobulk_ridge_1000genes.csv,1698,.csv,GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\pathology_head_gene_counterfactual_donor.csv,279996,.csv,AD;APOE;GFAP;Iba1;NeuN;TREM2;chemokine;microglia,True,
results\tables\pathology_head_gene_counterfactual_summary.csv,6165,.csv,AD;APOE;GFAP;Iba1;NeuN;TREM2;chemokine;microglia,True,
results\tables\pathology_head_module_counterfactual_donor.csv,306974,.csv,AD;GFAP;GO;Iba1;NeuN;chemokine;complement;interferon;lysosome;microglia;phagocytosis,True,
results\tables\pathology_head_module_counterfactual_summary.csv,7393,.csv,AD;APOE;GFAP;GO;Iba1;NeuN;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\pathology_head_stage_b_frozen_donor_embeddings.csv,125173,.csv,AD,True,
results\tables\pathology_head_stage_b_lp_metrics.csv,1019,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\pathology_head_stage_b_lp_oof_predictions.csv,80346,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\sea_ad_full_metadata_covariate_audit.csv,8198,.csv,AD;APOE;Alzheimer;tau,True,
results\tables\sea_ad_full_metadata_targets_with_covariates.csv,63304,.csv,AD;APOE;Alzheimer;GFAP;Iba1;NeuN;tau,True,
results\tables\sea_ad_low_pathology_anchor_audit_donors.csv,30175,.csv,AD;APOE;Alzheimer;GFAP;Iba1;NeuN;microglia;tau,True,
results\tables\sea_ad_low_pathology_anchor_audit_summary.csv,2290,.csv,AD;GFAP;Iba1;NeuN;microglia,True,
results\tables\sea_ad_low_pathology_microglia_pvm_relaxed_subset_summary.csv,178,.csv,AD;microglia,True,
results\tables\sea_ad_low_pathology_microglia_pvm_strict_subset_summary.csv,82,.csv,AD;microglia,True,
results\tables\stage27_external_matrix_readiness_v1.csv,2564,.csv,AD;DAM;microglia,True,
results\tables\stage32b_candidate_download_plan_v1.csv,2543,.csv,AD;DAM;microglia,True,
results\tables\stage32b_metadata_schema_audit_v1.csv,3583,.csv,AD;microglia,True,
results\tables\stage32c_approved_dataset_download_plan_v1.csv,876,.csv,AD,True,
results\tables\stage32c_download_manifest_v1.csv,492,.csv,AD,True,
results\tables\stage32c_metadata_field_mapping_candidates_v1.csv,349,.csv,AD,True,
results\tables\stage_a_frozen_cellxgene_normal_microglia_coordinates.csv,14703992,.csv,,False,file_exceeds_size_limit
results\tables\stage_a_frozen_sea_ad_low_pathology_relaxed_coordinates.csv,6516499,.csv,,False,file_exceeds_size_limit
results\tables\stage_a_frozen_sea_ad_low_pathology_strict_coordinates.csv,2739641,.csv,AD,True,
results\tables\stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv,14833380,.csv,,False,file_exceeds_size_limit
results\tables\stage_b_rehearsal_cellxgene_normal_microglia_drift.csv,883066,.csv,AD;microglia,True,
results\tables\stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv,6579660,.csv,,False,file_exceeds_size_limit
results\tables\stage_b_rehearsal_sea_ad_low_pathology_relaxed_drift.csv,436961,.csv,AD,True,
results\tables\stage_c_elastic_cov001_epoch_005_sea_ad_microglia_pvm_all_coordinates.csv,59295185,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_elastic_cov001_epoch_005_sea_ad_microglia_pvm_donor_embeddings.csv,222861,.csv,AD;microglia,True,
results\tables\stage_c_elastic_cov001_epoch_010_sea_ad_microglia_pvm_all_coordinates.csv,58875710,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_elastic_cov001_epoch_010_sea_ad_microglia_pvm_donor_embeddings.csv,221985,.csv,AD;microglia,True,
results\tables\stage_c_elastic_w005_epoch_005_sea_ad_microglia_pvm_all_coordinates.csv,58976658,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_elastic_w005_epoch_005_sea_ad_microglia_pvm_donor_embeddings.csv,222688,.csv,AD;microglia,True,
results\tables\stage_c_elastic_w005_epoch_010_sea_ad_microglia_pvm_all_coordinates.csv,58910623,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_elastic_w005_epoch_010_sea_ad_microglia_pvm_donor_embeddings.csv,222520,.csv,AD;microglia,True,
results\tables\stage_c_epoch_005_sea_ad_microglia_pvm_all_coordinates.csv,58757836,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_epoch_005_sea_ad_microglia_pvm_donor_embeddings.csv,222952,.csv,AD;microglia,True,
results\tables\stage_c_epoch_010_sea_ad_microglia_pvm_all_coordinates.csv,58569011,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_epoch_010_sea_ad_microglia_pvm_donor_embeddings.csv,222656,.csv,AD;microglia,True,
results\tables\stage_c_epoch_015_sea_ad_microglia_pvm_all_coordinates.csv,58748110,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_epoch_015_sea_ad_microglia_pvm_donor_embeddings.csv,222971,.csv,AD;microglia,True,
results\tables\stage_c_finetuning_combined_leaderboard.csv,16795,.csv,AD;GFAP;GO;Iba1;NeuN,True,
results\tables\stage_c_rehearsal_cellxgene_normal_microglia_coordinates.csv,14848848,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_rehearsal_cellxgene_normal_microglia_drift.csv,898205,.csv,AD;microglia,True,
results\tables\stage_c_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv,6571012,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_rehearsal_sea_ad_low_pathology_relaxed_drift.csv,442105,.csv,AD,True,
results\tables\stage_c_rehearsal_sea_ad_microglia_pvm_all_coordinates.csv,58595349,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_rehearsal_sea_ad_microglia_pvm_donor_embeddings.csv,222980,.csv,AD;microglia,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_005_coordinates.csv,59158581,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_sweep_02_goldilocks_epoch_005_cosine_knn_metrics.csv,351,.csv,GFAP;GO;Iba1;NeuN,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_005_donor_embeddings.csv,222824,.csv,GO,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_005_latent_metrics.csv,1502,.csv,GFAP;GO;Iba1;NeuN,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_005_ridge_pathology.csv,1708,.csv,GFAP;GO;Iba1;NeuN;tau,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_005_umap_coordinates.csv,19231,.csv,GFAP;GO;Iba1;NeuN,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_010_coordinates.csv,58825105,.csv,,False,file_exceeds_size_limit
results\tables\stage_c_sweep_02_goldilocks_epoch_010_cosine_knn_metrics.csv,353,.csv,GFAP;GO;Iba1;NeuN,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_010_donor_embeddings.csv,221960,.csv,GO,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_010_latent_metrics.csv,1499,.csv,GFAP;GO;Iba1;NeuN,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_010_ridge_pathology.csv,1711,.csv,GFAP;GO;Iba1;NeuN;tau,True,
results\tables\stage_c_sweep_02_goldilocks_epoch_010_umap_coordinates.csv,19215,.csv,GFAP;GO;Iba1;NeuN,True,
results\tables\stage_c_sweep_02_goldilocks_history.csv,3300,.csv,AD;GO,True,
results\tables\stage_c_upgrade_fine_08_pathology_latent_weights.csv,56317,.csv,AD;GFAP;NeuN,True,
results\tables\stage_c_upgrade_fine_08_r0045_cov0005_pc0075_epoch_005_cosine_knn_metrics.csv,350,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\stage_c_upgrade_fine_08_r0045_cov0005_pc0075_epoch_005_latent_metrics.csv,1498,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\stage_c_upgrade_fine_summary.csv,2756,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\stage_c_upgrade_sweep_summary.csv,1202,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\test_graph_connected_feature_wide_threadfix.csv,4428,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\test_graph_connected_feature_wide_threadfix_skip_nn.csv,3372,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\v2_1_gse174367_sea_ad_trajectory_vectors.csv,14213,.csv,AD;GFAP;Iba1;NeuN;tau,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_6e10.csv,5072,.csv,AD;APOE;GO;chemokine;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_6e10_by_donor.csv,354924,.csv,AD;APOE;microglia;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_at8.csv,4987,.csv,AD;APOE;GO;chemokine;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_at8_by_donor.csv,354083,.csv,AD;APOE;microglia;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_gfap.csv,4955,.csv,AD;APOE;GFAP;GO;chemokine;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_gfap_by_donor.csv,347995,.csv,AD;APOE;GFAP;microglia;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_iba1.csv,4996,.csv,AD;APOE;GO;Iba1;chemokine;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_iba1_by_donor.csv,350318,.csv,AD;APOE;Iba1;microglia;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_neun.csv,4951,.csv,AD;APOE;GO;NeuN;chemokine;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_gene_counterfactual_neun_by_donor.csv,349039,.csv,AD;APOE;NeuN;microglia;senescence,True,
results\tables\v2_1_upgrade_fine_08_latent_gene_attributions.csv,3456077,.csv,AD;APOE;DAM;GO;chemokine;complement;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\v2_1_upgrade_fine_08_latent_jacobian_matrix.csv,187998,.csv,AD,True,
results\tables\v2_1_upgrade_fine_08_latent_jacobian_module_annotations.csv,32737,.csv,AD;GO;chemokine;complement;lysosome;microglia;phagocytosis,True,
results\tables\v2_1_upgrade_fine_08_latent_jacobian_top_edges.csv,65953,.csv,AD;GO;lysosome;phagocytosis,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_6e10.csv,2859,.csv,AD;APOE;GO;TREM2;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_6e10_by_donor.csv,156526,.csv,AD;GO;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_at8.csv,2841,.csv,AD;APOE;GO;TREM2;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_at8_by_donor.csv,156452,.csv,AD;GO;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_gfap.csv,2826,.csv,AD;APOE;GFAP;GO;TREM2;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_gfap_by_donor.csv,153899,.csv,AD;GFAP;GO;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_iba1.csv,2831,.csv,AD;APOE;GO;Iba1;TREM2;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_iba1_by_donor.csv,154578,.csv,AD;GO;Iba1;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_neun.csv,2808,.csv,AD;APOE;GO;NeuN;TREM2;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_1_upgrade_fine_08_module_counterfactual_neun_by_donor.csv,153510,.csv,AD;GO;NeuN;complement;lysosome;microglia;phagocytosis;senescence,True,
results\tables\v2_2_abeta_mil_head_attention.csv,2006451,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_metrics.csv,232,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_oof_predictions.csv,3637,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_smoke_attention.csv,284745,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_smoke_metrics.csv,231,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_smoke_oof_predictions.csv,3640,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_stable_attention.csv,2006325,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_stable_metrics.csv,236,.csv,AD,True,
results\tables\v2_2_abeta_mil_head_stable_oof_predictions.csv,3635,.csv,AD,True,
results\tables\v2_2_abeta_responsive_microglia_axis_coefficients_summary.csv,3786,.csv,microglia,True,
results\tables\v2_2_abeta_responsive_microglia_cell_scores_summary.csv,3009769,.csv,microglia,True,
results\tables\v2_2_abeta_responsive_microglia_dge_all_summary.csv,211326,.csv,AD;APOE;DAM;GO;TREM2;microglia;tau,True,
results\tables\v2_2_abeta_responsive_microglia_dge_upregulated_summary.csv,7147,.csv,AD;GO;microglia,True,
results\tables\v2_2_abeta_responsive_microglia_donor_validation_summary.csv,6016,.csv,microglia,True,
results\tables\v2_2_abeta_responsive_microglia_smoke_axis_coefficients_summary.csv,3786,.csv,microglia,True,
results\tables\v2_2_abeta_responsive_microglia_smoke_cell_scores_summary.csv,588473,.csv,microglia,True,
results\tables\v2_2_abeta_responsive_microglia_smoke_dge_all_summary.csv,205136,.csv,AD;APOE;DAM;GO;TREM2;microglia;tau,True,
results\tables\v2_2_abeta_responsive_microglia_smoke_dge_upregulated_summary.csv,3159,.csv,AD;GO;microglia,True,
results\tables\v2_2_abeta_responsive_microglia_smoke_donor_validation_summary.csv,5880,.csv,microglia,True,
results\tables\v2_2_abeta_responsive_microglia_smoke_validation_metrics_summary.csv,768,.csv,APOE;TREM2;microglia,True,
results\tables\v2_2_abeta_responsive_microglia_validation_metrics_summary.csv,771,.csv,APOE;TREM2;microglia,True,
results\tables\v2_2_stage_b_adversarial_checkpoint_ranking.csv,1182,.csv,AD,True,
results\tables\v2_2_stage_b_adversarial_experiment_comparison.csv,839,.csv,AD,True,
results\tables\v2_2_stage_b_adversarial_full_w05_history.csv,6946,.csv,AD,True,
results\tables\v2_2_stage_b_adversarial_history.csv,6949,.csv,AD,True,
results\tables\v2_2_stage_b_adversarial_stateaware_smoke_history.csv,747,.csv,AD,True,
results\tables\v2_2_stage_b_adversarial_ttur_w02_history.csv,6933,.csv,AD,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter.csv,8010,.csv,TREM2;microglia;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_donor.csv,235471,.csv,TREM2;microglia;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_donor_modules.csv,207035,.csv,AD;APOE;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_fold.csv,18362,.csv,TREM2;microglia;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_fold_modules.csv,12642,.csv,AD;APOE;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_modules.csv,5333,.csv,AD;APOE;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter.csv,7896,.csv,GFAP;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_donor.csv,233652,.csv,GFAP;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_donor_modules.csv,205680,.csv,AD;APOE;GFAP;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_fold.csv,18159,.csv,GFAP;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_fold_modules.csv,12521,.csv,AD;APOE;GFAP;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_modules.csv,5287,.csv,AD;APOE;GFAP;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter.csv,7941,.csv,Iba1;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_donor.csv,235046,.csv,Iba1;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_donor_modules.csv,206461,.csv,AD;APOE;GO;Iba1;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_fold.csv,18221,.csv,Iba1;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_fold_modules.csv,12579,.csv,AD;APOE;GO;Iba1;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_modules.csv,5322,.csv,AD;APOE;GO;Iba1;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter.csv,8865,.csv,APOE;NeuN;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_donor.csv,264505,.csv,APOE;NeuN;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_donor_modules.csv,206577,.csv,AD;APOE;GO;NeuN;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_fold.csv,20408,.csv,APOE;NeuN;TREM2;microglia,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_fold_modules.csv,12645,.csv,AD;APOE;GO;NeuN;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_modules.csv,5371,.csv,AD;APOE;GO;NeuN;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter.csv,7975,.csv,AD;TREM2;microglia;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_donor.csv,231085,.csv,AD;TREM2;microglia;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_donor_modules.csv,206438,.csv,AD;APOE;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_fold.csv,18255,.csv,AD;TREM2;microglia;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_fold_modules.csv,12628,.csv,AD;APOE;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_modules.csv,5303,.csv,AD;APOE;GO;TREM2;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_guhcl_abeta42_Grey_matter.csv,2686,.csv,AD;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_guhcl_pTau_Grey_matter.csv,2748,.csv,AD;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_6e10_positive_area_Grey_matter.csv,2928,.csv,AD;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_AT8_positive_area_Grey_matter.csv,2945,.csv,AD;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_GFAP_positive_area_Grey_matter.csv,2961,.csv,AD;GFAP;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_Iba1_positive_area_Grey_matter.csv,2958,.csv,AD;GO;Iba1;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_NeuN_positive_area_Grey_matter.csv,2963,.csv,AD;GO;NeuN;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_ripa_abeta42_Grey_matter.csv,2685,.csv,AD;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\tables\multitarget_causal\confounder_adjusted_module_effects_ripa_pTau_Grey_matter.csv,2719,.csv,AD;GO;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0001_metadata.csv,853,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0002_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0003_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0004_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0005_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0006_metadata.csv,854,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0007_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0008_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0009_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0010_metadata.csv,854,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0011_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0012_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0013_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0014_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0015_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0016_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0017_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0018_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0019_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0020_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0021_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0022_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0023_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0024_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0025_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0026_metadata.csv,856,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0027_metadata.csv,855,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_targeted_manifold_audit_smoke_v1\feature_wide_chunk_0001_metadata.csv,745,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_targeted_manifold_audit_v1\feature_wide_chunk_0001_metadata.csv,721,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\discovery_tier1_pending_manifold_audit_v1_summary\feature_wide_chunk_0001_metadata.csv,773,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_donor.csv,94866,.csv,AD;GFAP;Iba1;NeuN;interferon,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_metadata.csv,749,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_normalized.csv,1696,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_summary.csv,2622,.csv,AD;GFAP;Iba1;NeuN;interferon,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_donor.csv,93754,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_metadata.csv,748,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_normalized.csv,1685,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_summary.csv,2610,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_donor.csv,93629,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_metadata.csv,749,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_normalized.csv,1671,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_summary.csv,2596,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_donor.csv,94947,.csv,AD;GFAP;Iba1;NeuN;interferon,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_metadata.csv,781,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_normalized.csv,1338,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_summary.csv,2302,.csv,AD;GFAP;Iba1;NeuN;interferon,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_donor.csv,93792,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_metadata.csv,781,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_normalized.csv,1335,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_summary.csv,2284,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_donor.csv,93522,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_metadata.csv,780,.csv,AD,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_normalized.csv,1323,.csv,AD;GFAP;Iba1;NeuN,True,
results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_summary.csv,2277,.csv,AD;GFAP;Iba1;NeuN,True,
results\reports\all_jepa_umap_variance_rankings.md,3637,.md,GO;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\reports\discovery_ablation_artifact_readiness_v1.md,2875,.md,AD;GO,True,
results\reports\discovery_ablation_training_decision_packet_v1.md,3825,.md,AD,True,
results\reports\discovery_ablation_training_protocol_v1.md,4517,.md,AD;microglia,True,
results\reports\discovery_atlas_final_state_audit.md,480,.md,AD,True,
results\reports\discovery_atlas_input_availability.md,10426,.md,AD;GO;amyloid,True,
results\reports\discovery_atlas_lightweight_checks.md,3599,.md,AD,True,
results\reports\discovery_baseline_comparison_gate.md,5192,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\discovery_feature_wide_counterfactual_feasibility.md,1648,.md,AD;microglia,True,
results\reports\discovery_final_candidate_shortlist_v1.md,51189,.md,AD;APOE;TREM2;amyloid;tau,True,
results\reports\discovery_final_candidate_shortlist_v2.md,16071,.md,AD;APOE;TREM2,True,
results\reports\discovery_final_candidate_shortlist_v3.md,15316,.md,AD;APOE;TREM2,True,
results\reports\discovery_graph_connected_feature_wide_pathology_axis_fingerprints.md,1915,.md,AD;GFAP;Iba1;NeuN;amyloid;tau,True,
results\reports\discovery_graph_connected_feature_wide_postrun_qc.md,1353,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\discovery_graph_neighborhood_coherence.md,3861,.md,APOE;amyloid,True,
results\reports\discovery_internal_evidence_scorecard_v1.md,11622,.md,AD;APOE;NeuN;TREM2,True,
results\reports\discovery_internal_evidence_scorecard_v1_annotated.md,868,.md,AD,True,
results\reports\discovery_internal_robustness_stability_v1.md,6997,.md,AD;APOE;GFAP;Iba1;amyloid;tau,True,
results\reports\discovery_level2_gliosis_failure_diagnostics_v1.md,1817,.md,GFAP;Iba1,True,
results\reports\discovery_negative_controls.md,20177,.md,AD;APOE;GO;TREM2;amyloid;tau,True,
results\reports\discovery_pathology_axis_fingerprints.md,6854,.md,AD;GFAP;GO;Iba1;NeuN;amyloid;complement;lysosome;microglia;phagocytosis;senescence;tau,True,
results\reports\discovery_pilot_feature_wide_counterfactual_validation.md,1559,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\discovery_scorecard_v2_graph_connected_feature_wide.md,8534,.md,AD;APOE;GO;NeuN;amyloid;tau,True,
results\reports\discovery_scorecard_v2_graph_neighborhood_coherence.md,9852,.md,AD;APOE;amyloid;tau,True,
results\reports\discovery_scorecard_v2_negative_controls.md,14725,.md,AD;APOE;amyloid;tau,True,
results\reports\discovery_targeted_manifold_audit_gene_list_v1.md,11050,.md,AD;APOE;TREM2,True,
results\reports\discovery_targeted_manifold_audit_smoke_v1_feasibility.md,1614,.md,AD;microglia,True,
results\reports\discovery_targeted_manifold_audit_v1.md,4228,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\discovery_targeted_manifold_audit_v1_feasibility.md,1610,.md,AD;microglia,True,
results\reports\discovery_tier1_pending_manifold_audit_v1_feasibility.md,1623,.md,AD;microglia,True,
results\reports\existing_graph_jepa_env_package_audit_v1.md,3535,.md,AD,True,
results\reports\existing_graph_jepa_env_selection_recommendation_v1.md,1270,.md,AD,True,
results\reports\existing_v1_no_graph_ablation_compatibility_v1.md,19832,.md,AD;microglia,True,
results\reports\external_validation_gse174367.md,4589,.md,AD;GFAP;Iba1;NeuN;microglia;tau,True,
results\reports\external_validation_gse174367_smoke.md,3682,.md,AD;GFAP;Iba1;NeuN;microglia;tau,True,
results\reports\graph_ablation_edge_set_manifest_v1.md,2426,.md,AD;microglia,True,
results\reports\graph_jepa_v3_benchmark_discovery_design_spec_v1.md,8917,.md,AD;GFAP;GO;Iba1;NeuN;microglia,True,
results\reports\graph_jepa_v3_causal_inference_layer_spec_v1.md,5961,.md,AD;microglia,True,
results\reports\jepa_representation_overlays.md,1503,.md,AD;GO;NeuN;complement;microglia;tau,True,
results\reports\jepa_v2_translational_actionability.md,3294,.md,AD;GO;microglia,True,
results\reports\microglia_pvm_hypothesis_report.md,1211,.md,NeuN;complement;interferon;microglia;tau,True,
results\reports\microglia_pvm_integrated_report.md,4092,.md,AD;APOE;GO;KEGG;MSigDB;NeuN;Reactome;TREM2;complement;interferon;microglia;tau,True,
results\reports\no_graph_ablation_predictive_representation_comparison_v1.md,5966,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\no_graph_ablation_preflight_v1.md,2554,.md,AD;microglia,True,
results\reports\no_graph_ablation_training_run_manifest_v1.md,3186,.md,AD;microglia,True,
results\reports\open_validation_framework_plan_v1.md,7680,.md,AD;APOE;microglia,True,
results\reports\sea_ad_full_metadata_covariate_audit.md,3100,.md,AD;APOE;Alzheimer;tau,True,
results\reports\sea_ad_low_pathology_anchor_audit.md,3141,.md,AD;GO;microglia,True,
results\reports\shuffled_graph_ablation_preflight_v1.md,4301,.md,AD;microglia,True,
results\reports\shuffled_graph_ablation_training_command_v1.md,1996,.md,AD;microglia,True,
results\reports\stage27c_rescue_report_v1.md,14495,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\stage27_external_pretraining_readiness_v1.md,3062,.md,AD;DAM;microglia,True,
results\reports\stage27_failure_diagnosis_v1.md,1952,.md,GFAP;Iba1;NeuN;amyloid,True,
results\reports\stage27_non_graph_v3_report_v1.md,5944,.md,AD;GFAP;Iba1;NeuN;microglia,True,
results\reports\stage30_graph_controls_report_v1.md,13781,.md,AD;GFAP;GO;Iba1;NeuN;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\reports\stage31_residual_graph_controls_report_v1.md,59668,.md,AD;GFAP;GO;Iba1;NeuN;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\reports\stage32b_approved_external_pretraining_matrix_report_v1.md,25800,.md,AD;DAM;microglia,True,
results\reports\stage32c_bulk_approved_external_acquisition_report_v1.md,7396,.md,AD;GO;microglia,True,
results\reports\stage32_external_pretraining_matrix_report_v1.md,29852,.md,AD;DAM;microglia,True,
results\reports\stage33a_external_pretrained_jepa_report_v1.md,2089,.md,AD,True,
results\reports\stage33b_external_pretrained_jepa_report_v1.md,10897,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\stage33c_external_pretrained_diagnostic_rescue_report_v1.md,18388,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\stage34a_hbca_microglia_filtered_external_pretraining_report_v1.md,13948,.md,AD;GFAP;Iba1;NeuN;microglia,True,
results\reports\stage34b_hbcc_external_pretraining_report_v1.md,14948,.md,AD;GFAP;GO;Iba1;NeuN;microglia,True,
results\reports\stage35a_target_aware_weak_graph_rescue_report_v1.md,26744,.md,AD;GFAP;GO;Iba1;NeuN;amyloid;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\reports\stage35b_graph_laplacian_regularized_ridge_report_v1.md,17342,.md,AD;GFAP;Iba1;NeuN;amyloid;tau,True,
results\reports\stage35c_latent_module_graph_report_v1.md,18460,.md,AD;GFAP;Iba1;NeuN;amyloid;microglia;tau,True,
results\reports\stage35d_perturbation_graph_diagnostic_report_v1.md,2583,.md,AD,True,
results\reports\stage35e_graph_diagnostics_synthesis_report_v1.md,10383,.md,AD;microglia,True,
results\reports\stage36a_agent_readable_hypotheses_v1.md,12976,.md,AD;GFAP;GO;Iba1;NeuN;chemokine;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\reports\stage36a_module_counterfactual_agent_report_v1.md,38995,.md,AD;GFAP;GO;Iba1;NeuN;chemokine;complement;interferon;lysosome;microglia;phagocytosis;senescence,True,
results\reports\stage_c_upgrade_fine_08_hypothesis_report.md,2438,.md,AD;GFAP;NeuN;complement;interferon;microglia;tau,True,
results\reports\strict_shuffled_graph_ablation_predictive_representation_comparison_v1.md,7564,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\strict_shuffled_graph_ablation_preflight_v1.md,4312,.md,AD;microglia,True,
results\reports\strict_shuffled_graph_ablation_training_command_v1.md,2137,.md,AD;microglia,True,
results\reports\strict_shuffled_graph_ablation_training_run_manifest_v1.md,2366,.md,AD;microglia,True,
results\reports\strict_shuffled_graph_edge_generation_v1.md,1843,.md,AD,True,
results\reports\v1_microglia_biological_hypotheses.md,6521,.md,AD;APOE;GFAP;GO;Iba1;NeuN;TREM2;antigen presentation;complement;interferon;lysosome;microglia;phagocytosis;senescence;tau,True,
results\reports\v2_1_microglia_biological_hypotheses.md,13104,.md,AD;APOE;GFAP;GO;NeuN;TREM2;chemokine;complement;lysosome;microglia;phagocytosis;senescence,True,
results\reports\v2_1_multitarget_counterfactual_stability.md,5536,.md,AD;APOE;GFAP;GO;Iba1;NeuN;amyloid;complement;lysosome;microglia;phagocytosis;senescence;tau,True,
results\reports\v2_1_named_biological_programs.md,5365,.md,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;amyloid;antigen presentation;complement;lysosome;microglia;phagocytosis;tau,True,
results\reports\v2_2_cellxgene_alignment_stats.md,1475,.md,AD;Alzheimer;microglia,True,
results\reports\v2_graph_foundation.md,3340,.md,AD;GO;microglia,True,
results\reports\v3_cellxgene_relevant_dataset_search_v1.md,19417,.md,AD;Alzheimer;GO;microglia,True,
results\reports\v3_external_dataset_role_assignment_v1.md,10318,.md,AD;microglia,True,
results\reports\v3_generalization_stability_gates_v1.md,6329,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\v3_locked_benchmark_harness_v1.md,6512,.md,AD;GFAP;Iba1;NeuN,True,
results\reports\v3_primary_baseline_benchmark_suite_v1.md,11534,.md,AD;GFAP;Iba1;NeuN;microglia,True,
results\reports\v3_primary_baseline_protocol_audit_v1.md,4689,.md,AD;GFAP;Iba1;NeuN;microglia,True,
results\reports\v3_public_external_dataset_schema_audit_v1.md,4755,.md,AD;GO;microglia,True,
results\reports\v3_reusable_asset_inventory_v1.md,15374,.md,AD;APOE;GO;KEGG;Reactome;microglia,True,
results\reports\v3_status_scorecard_dataset_registry_lock_v1.md,1667,.md,AD;microglia,True,
```

## 5. Schema registry

```csv
resource_id,resource_path,resource_type,parse_status,gene_column,term_column,category_column,evidence_column,target_scope_column,species_column,disease_scope_column,n_rows,n_gene_rows,stable_schema_available,exclusion_reason
resource_001,docs\ACTIVE_V3_STATUS.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_002,docs\architecture.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_003,docs\causal_discovery.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,12,True,
resource_004,docs\cleanup_manifest.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_005,docs\current_status.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,21,True,
resource_006,docs\dataset_guide.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,2,True,
resource_007,docs\DATASET_REGISTRY.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_008,docs\external_cohort_reconnaissance.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_009,docs\external_perturbation_benchmarks.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,10,True,
resource_010,docs\external_validation_next_steps.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,5,True,
resource_011,docs\figure_gallery.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_012,docs\github_about.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,1,True,
resource_013,docs\github_repo_checklist.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_014,docs\gpu_setup.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_015,docs\project_proposal.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,15,True,
resource_016,docs\runbook.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,21,True,
resource_017,docs\scientific_pitch.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,6,True,
resource_018,docs\stage_c_v21_upgrade_experiments.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_019,docs\technical_plan.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,11,True,
resource_020,docs\V3_SCORECARD.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_021,configs\train\stage34a_hbca_microglia_filtered_external_pretraining_v1.yaml,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_022,configs\train\stage_b_adversarial.yaml,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_023,results\tables\causal_fold_specific_two_pass_test_loaded.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,29,25,True,
resource_024,results\tables\causal_fold_specific_two_pass_test_loaded_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,15,115,True,
resource_025,results\tables\cellxgene_normal_microglia_anchor_qc.csv,unknown_schema,no_parse,,,,,,,,6,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_026,results\tables\cellxgene_normal_microglia_assay_counts.csv,unknown_schema,no_parse,,,,,,,,8,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_027,results\tables\cellxgene_normal_microglia_dataset_id_counts.csv,unknown_schema,no_parse,,,,,,,,38,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_028,results\tables\cellxgene_normal_microglia_development_stage_counts.csv,unknown_schema,no_parse,,,,,,,,132,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_029,results\tables\cellxgene_normal_microglia_disease_counts.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_030,results\tables\cellxgene_normal_microglia_donor_id_counts.csv,unknown_schema,no_parse,,,,,,,,692,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_031,results\tables\cellxgene_normal_microglia_matched_genes.csv,gene_list,parsed_table_exact_gene_column,gene,,,,,,,2863,115,True,
resource_032,results\tables\cellxgene_normal_microglia_missing_genes.csv,gene_list,parsed_table_no_query_gene_overlap,gene,,,,,,,94,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_033,results\tables\cellxgene_normal_microglia_suspension_type_counts.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_034,results\tables\cellxgene_normal_microglia_tissue_counts.csv,unknown_schema,no_parse,,,,,,,,42,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_035,results\tables\cellxgene_normal_microglia_tissue_general_counts.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_036,results\tables\cell_level_mixing_sample_metadata.csv,unknown_schema,no_parse,,,,,,,,9799,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_037,results\tables\confounder_adjusted_module_effects_at8.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_038,results\tables\confounder_adjusted_top_gene_effects_at8.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,target,,,,,,,10,10,True,
resource_039,results\tables\gse138852_graph_jepa_zero_shot_aligned_sea_ad_trajectory_vectors.csv,unknown_schema,no_parse,,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_040,results\tables\gse138852_graph_jepa_zero_shot_baseline_sea_ad_trajectory_vectors.csv,unknown_schema,no_parse,,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_042,results\tables\microglia_pvm_jepa_all_module_preserved_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_044,results\tables\microglia_pvm_jepa_all_module_preserved_e100_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_045,results\tables\microglia_pvm_jepa_all_module_preserved_e100_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_046,results\tables\microglia_pvm_jepa_all_module_preserved_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_048,results\tables\microglia_pvm_jepa_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,87,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_050,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_051,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e10_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_053,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_054,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e20_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_056,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_057,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e30_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_059,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_060,results\tables\microglia_pvm_jepa_ema_expanded_balanced_e40_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_062,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_063,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e10_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_065,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_066,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e20_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_068,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_069,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e30_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_071,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_072,results\tables\microglia_pvm_jepa_ema_var_expanded_balanced_e40_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_073,results\tables\microglia_pvm_jepa_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_075,results\tables\microglia_pvm_jepa_expanded_modules_balanced_e40_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_076,results\tables\microglia_pvm_jepa_expanded_modules_balanced_e40_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_078,results\tables\microglia_pvm_jepa_expanded_modules_balanced_e80_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_079,results\tables\microglia_pvm_jepa_expanded_modules_balanced_e80_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_081,results\tables\microglia_pvm_jepa_mixed_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,87,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_082,results\tables\microglia_pvm_jepa_mixed_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_084,results\tables\microglia_pvm_jepa_module_preserved_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,87,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_085,results\tables\microglia_pvm_jepa_module_preserved_embedding_ridge.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_086,results\tables\microglia_pvm_model_comparison.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,102,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_087,results\tables\microglia_pvm_percent_AT8_gene_rankings.csv,gene_list,parsed_table_exact_gene_column,gene,,,,,,,36601,115,True,
resource_088,results\tables\microglia_pvm_percent_AT8_gene_set_scores.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,gene_set,,,,,,4,28,True,
resource_089,results\tables\microglia_pvm_pseudobulk_ridge_1000genes.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_090,results\tables\pathology_head_gene_counterfactual_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,module,,,,,,1246,9,True,
resource_091,results\tables\pathology_head_gene_counterfactual_summary.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,14,9,True,
resource_092,results\tables\pathology_head_module_counterfactual_donor.csv,unknown_schema,no_parse,,module,,,,,,1335,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_093,results\tables\pathology_head_module_counterfactual_summary.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,15,115,True,
resource_094,results\tables\pathology_head_stage_b_frozen_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_095,results\tables\pathology_head_stage_b_lp_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,10,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_096,results\tables\pathology_head_stage_b_lp_oof_predictions.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,840,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_097,results\tables\sea_ad_full_metadata_covariate_audit.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,66,1,True,
resource_098,results\tables\sea_ad_full_metadata_targets_with_covariates.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,84,1,True,
resource_099,results\tables\sea_ad_low_pathology_anchor_audit_donors.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,89,1,True,
resource_100,results\tables\sea_ad_low_pathology_anchor_audit_summary.csv,unknown_schema,no_parse,,,,,,,,4,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_101,results\tables\sea_ad_low_pathology_microglia_pvm_relaxed_subset_summary.csv,unknown_schema,no_parse,,,,,,,,10,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_102,results\tables\sea_ad_low_pathology_microglia_pvm_strict_subset_summary.csv,unknown_schema,no_parse,,,,,,,,4,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_103,results\tables\stage27_external_matrix_readiness_v1.csv,unknown_schema,no_parse,,,,,,,,6,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_104,results\tables\stage32b_candidate_download_plan_v1.csv,unknown_schema,no_parse,,,,,,,,6,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_105,results\tables\stage32b_metadata_schema_audit_v1.csv,unknown_schema,no_parse,,,,,,,,19,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_106,results\tables\stage32c_approved_dataset_download_plan_v1.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_107,results\tables\stage32c_download_manifest_v1.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_108,results\tables\stage32c_metadata_field_mapping_candidates_v1.csv,unknown_schema,no_parse,,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_111,results\tables\stage_a_frozen_sea_ad_low_pathology_strict_coordinates.csv,unknown_schema,no_parse,,,,,,,,1883,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_113,results\tables\stage_b_rehearsal_cellxgene_normal_microglia_drift.csv,unknown_schema,no_parse,,label,,,,,,10000,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_115,results\tables\stage_b_rehearsal_sea_ad_low_pathology_relaxed_drift.csv,unknown_schema,no_parse,,label,,,,,,4467,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_117,results\tables\stage_c_elastic_cov001_epoch_005_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_119,results\tables\stage_c_elastic_cov001_epoch_010_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_121,results\tables\stage_c_elastic_w005_epoch_005_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_123,results\tables\stage_c_elastic_w005_epoch_010_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_125,results\tables\stage_c_epoch_005_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_127,results\tables\stage_c_epoch_010_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_129,results\tables\stage_c_epoch_015_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_130,results\tables\stage_c_finetuning_combined_leaderboard.csv,unknown_schema,no_parse,,,,,,,,49,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_132,results\tables\stage_c_rehearsal_cellxgene_normal_microglia_drift.csv,unknown_schema,no_parse,,label,,,,,,10000,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_134,results\tables\stage_c_rehearsal_sea_ad_low_pathology_relaxed_drift.csv,unknown_schema,no_parse,,label,,,,,,4467,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_136,results\tables\stage_c_rehearsal_sea_ad_microglia_pvm_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_138,results\tables\stage_c_sweep_02_goldilocks_epoch_005_cosine_knn_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_139,results\tables\stage_c_sweep_02_goldilocks_epoch_005_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_140,results\tables\stage_c_sweep_02_goldilocks_epoch_005_latent_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,10,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_141,results\tables\stage_c_sweep_02_goldilocks_epoch_005_ridge_pathology.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_142,results\tables\stage_c_sweep_02_goldilocks_epoch_005_umap_coordinates.csv,unknown_schema,no_parse,,,,,,,,178,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_144,results\tables\stage_c_sweep_02_goldilocks_epoch_010_cosine_knn_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_145,results\tables\stage_c_sweep_02_goldilocks_epoch_010_donor_embeddings.csv,unknown_schema,no_parse,,,,,,,,89,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_146,results\tables\stage_c_sweep_02_goldilocks_epoch_010_latent_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,10,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_147,results\tables\stage_c_sweep_02_goldilocks_epoch_010_ridge_pathology.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,17,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_148,results\tables\stage_c_sweep_02_goldilocks_epoch_010_umap_coordinates.csv,unknown_schema,no_parse,,,,,,,,178,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_149,results\tables\stage_c_sweep_02_goldilocks_history.csv,unknown_schema,no_parse,,,,,,,,10,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_150,results\tables\stage_c_upgrade_fine_08_pathology_latent_weights.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,384,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_151,results\tables\stage_c_upgrade_fine_08_r0045_cov0005_pc0075_epoch_005_cosine_knn_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_152,results\tables\stage_c_upgrade_fine_08_r0045_cov0005_pc0075_epoch_005_latent_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,10,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_153,results\tables\stage_c_upgrade_fine_summary.csv,unknown_schema,no_parse,,,,,,,,8,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_154,results\tables\stage_c_upgrade_sweep_summary.csv,unknown_schema,no_parse,,,,,,,,3,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_155,results\tables\test_graph_connected_feature_wide_threadfix.csv,gene_list,parsed_table_exact_gene_column,gene,,,,,,,15,1,True,
resource_156,results\tables\test_graph_connected_feature_wide_threadfix_skip_nn.csv,gene_list,parsed_table_exact_gene_column,gene,,,,,,,15,1,True,
resource_157,results\tables\v2_1_gse174367_sea_ad_trajectory_vectors.csv,unknown_schema,no_parse,,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_158,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_6e10.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,24,13,True,
resource_159,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_6e10_by_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,target,module,,,,,,2016,13,True,
resource_160,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_at8.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,24,13,True,
resource_161,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_at8_by_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,target,module,,,,,,2016,13,True,
resource_162,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_gfap.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,24,13,True,
resource_163,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_gfap_by_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,target,module,,,,,,2016,13,True,
resource_164,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_iba1.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,24,13,True,
resource_165,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_iba1_by_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,target,module,,,,,,2016,13,True,
resource_166,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_neun.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,24,13,True,
resource_167,results\tables\v2_1_upgrade_fine_08_gene_counterfactual_neun_by_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,target,module,,,,,,2016,13,True,
resource_168,results\tables\v2_1_upgrade_fine_08_latent_gene_attributions.csv,gene_list,parsed_table_exact_gene_column,gene,,,,,,,38441,115,True,
resource_169,results\tables\v2_1_upgrade_fine_08_latent_jacobian_matrix.csv,unknown_schema,no_parse,,,,,,,,128,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_170,results\tables\v2_1_upgrade_fine_08_latent_jacobian_module_annotations.csv,unknown_schema,no_parse,,module,,,,,,384,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_171,results\tables\v2_1_upgrade_fine_08_latent_jacobian_top_edges.csv,unknown_schema,no_parse,,,,,,,,500,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_172,results\tables\v2_1_upgrade_fine_08_module_counterfactual_6e10.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,10,83,True,
resource_173,results\tables\v2_1_upgrade_fine_08_module_counterfactual_6e10_by_donor.csv,gene_term_table,parsed_table_no_query_gene_overlap,target,module,,,,,,840,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_174,results\tables\v2_1_upgrade_fine_08_module_counterfactual_at8.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,10,83,True,
resource_175,results\tables\v2_1_upgrade_fine_08_module_counterfactual_at8_by_donor.csv,gene_term_table,parsed_table_no_query_gene_overlap,target,module,,,,,,840,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_176,results\tables\v2_1_upgrade_fine_08_module_counterfactual_gfap.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,10,83,True,
resource_177,results\tables\v2_1_upgrade_fine_08_module_counterfactual_gfap_by_donor.csv,gene_term_table,parsed_table_no_query_gene_overlap,target,module,,,,,,840,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_178,results\tables\v2_1_upgrade_fine_08_module_counterfactual_iba1.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,10,83,True,
resource_179,results\tables\v2_1_upgrade_fine_08_module_counterfactual_iba1_by_donor.csv,gene_term_table,parsed_table_no_query_gene_overlap,target,module,,,,,,840,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_180,results\tables\v2_1_upgrade_fine_08_module_counterfactual_neun.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,10,83,True,
resource_181,results\tables\v2_1_upgrade_fine_08_module_counterfactual_neun_by_donor.csv,gene_term_table,parsed_table_no_query_gene_overlap,target,module,,,,,,840,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_182,results\tables\v2_2_abeta_mil_head_attention.csv,unknown_schema,no_parse,,,,,,,,38905,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_183,results\tables\v2_2_abeta_mil_head_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_184,results\tables\v2_2_abeta_mil_head_oof_predictions.csv,unknown_schema,no_parse,,,,,,,,84,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_185,results\tables\v2_2_abeta_mil_head_smoke_attention.csv,unknown_schema,no_parse,,,,,,,,5712,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_186,results\tables\v2_2_abeta_mil_head_smoke_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_187,results\tables\v2_2_abeta_mil_head_smoke_oof_predictions.csv,unknown_schema,no_parse,,,,,,,,84,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_188,results\tables\v2_2_abeta_mil_head_stable_attention.csv,unknown_schema,no_parse,,,,,,,,38905,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_189,results\tables\v2_2_abeta_mil_head_stable_metrics.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_190,results\tables\v2_2_abeta_mil_head_stable_oof_predictions.csv,unknown_schema,no_parse,,,,,,,,84,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_191,results\tables\v2_2_abeta_responsive_microglia_axis_coefficients_summary.csv,unknown_schema,no_parse,,,,,,,,128,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_192,results\tables\v2_2_abeta_responsive_microglia_cell_scores_summary.csv,unknown_schema,no_parse,,,,,,,,40000,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_193,results\tables\v2_2_abeta_responsive_microglia_dge_all_summary.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,2957,115,True,
resource_194,results\tables\v2_2_abeta_responsive_microglia_dge_upregulated_summary.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,98,2,True,
resource_195,results\tables\v2_2_abeta_responsive_microglia_donor_validation_summary.csv,unknown_schema,no_parse,,,,,,,,84,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_196,results\tables\v2_2_abeta_responsive_microglia_smoke_axis_coefficients_summary.csv,unknown_schema,no_parse,,,,,,,,128,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_197,results\tables\v2_2_abeta_responsive_microglia_smoke_cell_scores_summary.csv,unknown_schema,no_parse,,,,,,,,7821,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_198,results\tables\v2_2_abeta_responsive_microglia_smoke_dge_all_summary.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,2957,115,True,
resource_199,results\tables\v2_2_abeta_responsive_microglia_smoke_dge_upregulated_summary.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,44,2,True,
resource_200,results\tables\v2_2_abeta_responsive_microglia_smoke_donor_validation_summary.csv,unknown_schema,no_parse,,,,,,,,84,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_201,results\tables\v2_2_abeta_responsive_microglia_smoke_validation_metrics_summary.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,1,11,True,
resource_202,results\tables\v2_2_abeta_responsive_microglia_validation_metrics_summary.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,1,11,True,
resource_203,results\tables\v2_2_stage_b_adversarial_checkpoint_ranking.csv,unknown_schema,no_parse,,,,,,,,4,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_204,results\tables\v2_2_stage_b_adversarial_experiment_comparison.csv,unknown_schema,no_parse,,,,,,,,3,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_205,results\tables\v2_2_stage_b_adversarial_full_w05_history.csv,unknown_schema,no_parse,,,,,,,,20,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_206,results\tables\v2_2_stage_b_adversarial_history.csv,unknown_schema,no_parse,,,,,,,,20,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_207,results\tables\v2_2_stage_b_adversarial_stateaware_smoke_history.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_208,results\tables\v2_2_stage_b_adversarial_ttur_w02_history.csv,unknown_schema,no_parse,,,,,,,,20,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_209,results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,29,25,True,
resource_210,results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_donor.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,2436,25,True,
resource_211,results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_donor_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,1260,115,True,
resource_212,results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_fold.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,87,25,True,
resource_213,results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_by_fold_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,45,115,True,
resource_214,results\tables\multitarget_causal\causal_fold_specific_two_pass_guhcl_pTau_Grey_matter_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,15,115,True,
resource_215,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,29,25,True,
resource_216,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_donor.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,2436,25,True,
resource_217,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_donor_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,1260,115,True,
resource_218,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_fold.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,87,25,True,
resource_219,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_by_fold_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,45,115,True,
resource_220,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_GFAP_positive_area_Grey_matter_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,15,115,True,
resource_221,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,29,25,True,
resource_222,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_donor.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,2436,25,True,
resource_223,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_donor_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,1260,115,True,
resource_224,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_fold.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,87,25,True,
resource_225,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_by_fold_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,45,115,True,
resource_226,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_Iba1_positive_area_Grey_matter_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,15,115,True,
resource_227,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,32,30,True,
resource_228,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_donor.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,2688,30,True,
resource_229,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_donor_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,1260,115,True,
resource_230,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_fold.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,96,30,True,
resource_231,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_by_fold_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,45,115,True,
resource_232,results\tables\multitarget_causal\causal_fold_specific_two_pass_percent_NeuN_positive_area_Grey_matter_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,15,115,True,
resource_233,results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,29,28,True,
resource_234,results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_donor.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,2436,28,True,
resource_235,results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_donor_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,1260,115,True,
resource_236,results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_fold.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,87,28,True,
resource_237,results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_by_fold_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,45,115,True,
resource_238,results\tables\multitarget_causal\causal_fold_specific_two_pass_ripa_pTau_Grey_matter_modules.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,genes,module,,,,,,15,115,True,
resource_239,results\tables\multitarget_causal\confounder_adjusted_module_effects_guhcl_abeta42_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_240,results\tables\multitarget_causal\confounder_adjusted_module_effects_guhcl_pTau_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_241,results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_6e10_positive_area_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_242,results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_AT8_positive_area_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_243,results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_GFAP_positive_area_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_244,results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_Iba1_positive_area_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_245,results\tables\multitarget_causal\confounder_adjusted_module_effects_percent_NeuN_positive_area_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_246,results\tables\multitarget_causal\confounder_adjusted_module_effects_ripa_abeta42_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_247,results\tables\multitarget_causal\confounder_adjusted_module_effects_ripa_pTau_Grey_matter.csv,gene_list,parsed_table_no_query_gene_overlap,target,,,,,,,15,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_248,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0001_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_249,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0002_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_250,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0003_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_251,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0004_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_252,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0005_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_253,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0006_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_254,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0007_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_255,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0008_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_256,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0009_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_257,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0010_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_258,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0011_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_259,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0012_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_260,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0013_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_261,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0014_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_262,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0015_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_263,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0016_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_264,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0017_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_265,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0018_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_266,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0019_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_267,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0020_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_268,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0021_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_269,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0022_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_270,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0023_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_271,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0024_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_272,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0025_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_273,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0026_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_274,results\tables\_feature_wide_counterfactual_chunks\discovery_graph_connected_feature_wide_pathology_axis_counterfactuals\feature_wide_chunk_0027_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_275,results\tables\_feature_wide_counterfactual_chunks\discovery_targeted_manifold_audit_smoke_v1\feature_wide_chunk_0001_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_276,results\tables\_feature_wide_counterfactual_chunks\discovery_targeted_manifold_audit_v1\feature_wide_chunk_0001_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_277,results\tables\_feature_wide_counterfactual_chunks\discovery_tier1_pending_manifold_audit_v1_summary\feature_wide_chunk_0001_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_278,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,module,,,,,,445,1,True,
resource_279,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_280,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_normalized.csv,gene_list,parsed_table_exact_gene_column,gene,,,,,,,5,1,True,
resource_281,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0001_summary.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,5,1,True,
resource_282,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_donor.csv,unknown_schema,no_parse,,module,,,,,,445,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_283,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_284,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_normalized.csv,gene_list,parsed_table_no_query_gene_overlap,gene,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_285,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0002_summary.csv,gene_term_table,parsed_table_no_query_gene_overlap,genes,module,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_286,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_donor.csv,unknown_schema,no_parse,,module,,,,,,445,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_287,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_288,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_normalized.csv,gene_list,parsed_table_no_query_gene_overlap,gene,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_289,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix\feature_wide_chunk_0003_summary.csv,gene_term_table,parsed_table_no_query_gene_overlap,genes,module,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_290,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_donor.csv,gene_list,parsed_markdown_or_text_exact_gene_mentions,,module,,,,,,445,1,True,
resource_291,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_292,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_normalized.csv,gene_list,parsed_table_exact_gene_column,gene,,,,,,,5,1,True,
resource_293,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0001_summary.csv,gene_term_table,parsed_table_exact_gene_column,genes,module,,,,,,5,1,True,
resource_294,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_donor.csv,unknown_schema,no_parse,,module,,,,,,445,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_295,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_296,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_normalized.csv,gene_list,parsed_table_no_query_gene_overlap,gene,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_297,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0002_summary.csv,gene_term_table,parsed_table_no_query_gene_overlap,genes,module,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_298,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_donor.csv,unknown_schema,no_parse,,module,,,,,,445,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_299,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_metadata.csv,unknown_schema,no_parse,,,,,,,,1,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_300,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_normalized.csv,gene_list,parsed_table_no_query_gene_overlap,gene,,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_301,results\tables\_feature_wide_counterfactual_chunks\test_graph_connected_feature_wide_threadfix_skip_nn\feature_wide_chunk_0003_summary.csv,gene_term_table,parsed_table_no_query_gene_overlap,genes,module,,,,,,5,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_302,results\reports\all_jepa_umap_variance_rankings.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_303,results\reports\discovery_ablation_artifact_readiness_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_304,results\reports\discovery_ablation_training_decision_packet_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_305,results\reports\discovery_ablation_training_protocol_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_306,results\reports\discovery_atlas_final_state_audit.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_307,results\reports\discovery_atlas_input_availability.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_308,results\reports\discovery_atlas_lightweight_checks.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_309,results\reports\discovery_baseline_comparison_gate.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_310,results\reports\discovery_feature_wide_counterfactual_feasibility.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_311,results\reports\discovery_final_candidate_shortlist_v1.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,17,True,
resource_312,results\reports\discovery_final_candidate_shortlist_v2.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,17,True,
resource_313,results\reports\discovery_final_candidate_shortlist_v3.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,17,True,
resource_314,results\reports\discovery_graph_connected_feature_wide_pathology_axis_fingerprints.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_315,results\reports\discovery_graph_connected_feature_wide_postrun_qc.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_316,results\reports\discovery_graph_neighborhood_coherence.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,10,True,
resource_317,results\reports\discovery_internal_evidence_scorecard_v1.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,17,True,
resource_318,results\reports\discovery_internal_evidence_scorecard_v1_annotated.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_319,results\reports\discovery_internal_robustness_stability_v1.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,3,True,
resource_320,results\reports\discovery_level2_gliosis_failure_diagnostics_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_321,results\reports\discovery_negative_controls.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,22,True,
resource_322,results\reports\discovery_pathology_axis_fingerprints.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,9,True,
resource_323,results\reports\discovery_pilot_feature_wide_counterfactual_validation.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_324,results\reports\discovery_scorecard_v2_graph_connected_feature_wide.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,4,True,
resource_325,results\reports\discovery_scorecard_v2_graph_neighborhood_coherence.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,1,True,
resource_326,results\reports\discovery_scorecard_v2_negative_controls.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,1,True,
resource_327,results\reports\discovery_targeted_manifold_audit_gene_list_v1.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,10,True,
resource_328,results\reports\discovery_targeted_manifold_audit_smoke_v1_feasibility.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_329,results\reports\discovery_targeted_manifold_audit_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_330,results\reports\discovery_targeted_manifold_audit_v1_feasibility.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_331,results\reports\discovery_tier1_pending_manifold_audit_v1_feasibility.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_332,results\reports\existing_graph_jepa_env_package_audit_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_333,results\reports\existing_graph_jepa_env_selection_recommendation_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_334,results\reports\existing_v1_no_graph_ablation_compatibility_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_335,results\reports\external_validation_gse174367.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_336,results\reports\external_validation_gse174367_smoke.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_337,results\reports\graph_ablation_edge_set_manifest_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_338,results\reports\graph_jepa_v3_benchmark_discovery_design_spec_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_339,results\reports\graph_jepa_v3_causal_inference_layer_spec_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_340,results\reports\jepa_representation_overlays.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_341,results\reports\jepa_v2_translational_actionability.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,7,True,
resource_342,results\reports\microglia_pvm_hypothesis_report.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_343,results\reports\microglia_pvm_integrated_report.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,37,True,
resource_344,results\reports\no_graph_ablation_predictive_representation_comparison_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_345,results\reports\no_graph_ablation_preflight_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_346,results\reports\no_graph_ablation_training_run_manifest_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_347,results\reports\open_validation_framework_plan_v1.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,1,True,
resource_348,results\reports\sea_ad_full_metadata_covariate_audit.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,1,True,
resource_349,results\reports\sea_ad_low_pathology_anchor_audit.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_350,results\reports\shuffled_graph_ablation_preflight_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_351,results\reports\shuffled_graph_ablation_training_command_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_352,results\reports\stage27c_rescue_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_353,results\reports\stage27_external_pretraining_readiness_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_354,results\reports\stage27_failure_diagnosis_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_355,results\reports\stage27_non_graph_v3_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_356,results\reports\stage30_graph_controls_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_357,results\reports\stage31_residual_graph_controls_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_358,results\reports\stage32b_approved_external_pretraining_matrix_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_359,results\reports\stage32c_bulk_approved_external_acquisition_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_360,results\reports\stage32_external_pretraining_matrix_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_361,results\reports\stage33a_external_pretrained_jepa_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_362,results\reports\stage33b_external_pretrained_jepa_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_363,results\reports\stage33c_external_pretrained_diagnostic_rescue_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_364,results\reports\stage34a_hbca_microglia_filtered_external_pretraining_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_365,results\reports\stage34b_hbcc_external_pretraining_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_366,results\reports\stage35a_target_aware_weak_graph_rescue_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_367,results\reports\stage35b_graph_laplacian_regularized_ridge_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_368,results\reports\stage35c_latent_module_graph_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_369,results\reports\stage35d_perturbation_graph_diagnostic_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_370,results\reports\stage35e_graph_diagnostics_synthesis_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_371,results\reports\stage36a_agent_readable_hypotheses_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_372,results\reports\stage36a_module_counterfactual_agent_report_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_373,results\reports\stage_c_upgrade_fine_08_hypothesis_report.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_374,results\reports\strict_shuffled_graph_ablation_predictive_representation_comparison_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_375,results\reports\strict_shuffled_graph_ablation_preflight_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_376,results\reports\strict_shuffled_graph_ablation_training_command_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_377,results\reports\strict_shuffled_graph_ablation_training_run_manifest_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_378,results\reports\strict_shuffled_graph_edge_generation_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_379,results\reports\v1_microglia_biological_hypotheses.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,15,True,
resource_380,results\reports\v2_1_microglia_biological_hypotheses.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,84,True,
resource_381,results\reports\v2_1_multitarget_counterfactual_stability.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,6,True,
resource_382,results\reports\v2_1_named_biological_programs.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,44,True,
resource_383,results\reports\v2_2_cellxgene_alignment_stats.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_384,results\reports\v2_graph_foundation.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_385,results\reports\v3_cellxgene_relevant_dataset_search_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_386,results\reports\v3_external_dataset_role_assignment_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_387,results\reports\v3_generalization_stability_gates_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_388,results\reports\v3_locked_benchmark_harness_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_389,results\reports\v3_primary_baseline_benchmark_suite_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_390,results\reports\v3_primary_baseline_protocol_audit_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_391,results\reports\v3_public_external_dataset_schema_audit_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
resource_392,results\reports\v3_reusable_asset_inventory_v1.md,markdown_gene_mentions,parsed_markdown_or_text_exact_gene_mentions,,,,,,,,0,1,True,
resource_393,results\reports\v3_status_scorecard_dataset_registry_lock_v1.md,unknown_schema,no_parse,,,,,,,,0,0,False,no_exact_query_gene_match_or_no_gene_schema
```

## 6. Knowledge annotation method

Annotations use exact uppercase gene-symbol matching against Stage 36A query genes. Markdown/text mentions are low-confidence local prior support; structured gene tables are medium/high depending on category specificity. No aliases were invented.

## 7. Hypothesis grounding results

```csv
target,target_key,module,gene,evidence_level_from_stage36a,module_importance_score,module_delta_metric,mean_abs_prediction_delta,projection_method,kg_known_ad,kg_known_microglia,kg_known_neuroinflammation,kg_known_amyloid,kg_known_tau,kg_known_astrocyte,kg_known_neuronal,kg_known_target_pathology,kg_any_prior_support,kg_support_terms,kg_support_sources,kg_support_count,kg_grounding_confidence,novelty_status,safe_interpretation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,BSG,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_343,23,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,SLC6A12,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_343,23,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,IL27RA,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_005;resource_015;resource_019;resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_343;resource_380,32,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,NFKBIA,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_019;resource_024;resource_031;resource_038;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_343;resource_379;resource_380,36,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,CTSD,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;unannotated;vascular_barrier_myeloid,resource_005;resource_010;resource_015;resource_016;resource_017;resource_019;resource_024;resource_031;resource_038;resource_087;resource_088;resource_093;resource_158;resource_159;resource_160;resource_161;resource_162;resource_163;resource_164;resource_165;resource_166;resource_167;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_201;resource_202;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_227;resource_228;resource_229;resource_230;resource_231;resource_232;resource_235;resource_237;resource_238;resource_311;resource_312;resource_313;resource_316;resource_317;resource_321;resource_322;resource_327;resource_343;resource_379;resource_380;resource_381;resource_382,63,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,DRAM1,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;unannotated;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_019;resource_024;resource_031;resource_038;resource_087;resource_090;resource_091;resource_093;resource_158;resource_159;resource_160;resource_161;resource_162;resource_163;resource_164;resource_165;resource_166;resource_167;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_321;resource_322;resource_341;resource_343;resource_379,45,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,PTPRG,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;unannotated;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_017;resource_019;resource_024;resource_031;resource_038;resource_087;resource_090;resource_091;resource_093;resource_158;resource_159;resource_160;resource_161;resource_162;resource_163;resource_164;resource_165;resource_166;resource_167;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_321;resource_322;resource_341;resource_343;resource_379;resource_380,47,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,TNFRSF11B,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_019;resource_024;resource_031;resource_038;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_341;resource_343;resource_379;resource_380,37,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,CHI3L1,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;unannotated;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_017;resource_019;resource_024;resource_031;resource_038;resource_087;resource_090;resource_091;resource_093;resource_158;resource_159;resource_160;resource_161;resource_162;resource_163;resource_164;resource_165;resource_166;resource_167;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_316;resource_321;resource_322;resource_341;resource_343;resource_379,47,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_at8_associated_first_pass,S100A4,model_implied_gene_hypothesis,0.1340488002429888,-0.1340488002429888,0.0767983815790326,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_019;resource_024;resource_031;resource_038;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_341;resource_343;resource_379,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,HSPA1B,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,GADD45A,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,CDKN1A,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,FOS,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,JUN,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,HSPA1A,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,HSP90AA1,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;NeuN;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;unannotated;vascular_barrier_myeloid,resource_005;resource_016;resource_024;resource_031;resource_087;resource_093;resource_158;resource_159;resource_160;resource_161;resource_162;resource_163;resource_164;resource_165;resource_166;resource_167;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_194;resource_198;resource_199;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_316;resource_321;resource_380;resource_381;resource_382,49,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,CDKN2A,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,DDIT3,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_senescence_stress,SERPINE1,model_implied_gene_hypothesis,0.0452769059431001,-0.0452769059431001,0.0500499862525562,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_233;resource_234;resource_235;resource_236;resource_237;resource_238;resource_380,31,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,HMOX1,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,NQO1,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,SOD2,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,SOD1,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;NeuN;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_005;resource_016;resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,24,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,GPX4,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,GPX1,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,False,False,False,False,False,False,False,False,False,,,0,low,no_local_prior_found,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,KEAP1,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,TXN,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,PRDX1,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,False,True,True,False,False,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_oxidative_stress,NFE2L2,model_implied_gene_hypothesis,0.0176976814822314,-0.0176976814822314,0.032890392154884,exact_predefined_module_membership_projection,True,True,True,True,True,True,False,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238,22,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,IL1B,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_380,28,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,CCL4,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_380,28,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,CCL2,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_380,28,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,IL27RA,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_005;resource_015;resource_019;resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_343;resource_380,32,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,NFKBIA,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_019;resource_024;resource_031;resource_038;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_343;resource_379;resource_380,36,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,TNF,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_380,28,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,IL18,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_380,28,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,IL6,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_380,28,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,CXCL8,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;DAM;GFAP;GO;Iba1;NeuN;TREM2;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_024;resource_031;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_380,28,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
6e10/Aβ,6e10/A_beta,module_inflammatory_signaling,TNFRSF11B,model_implied_gene_hypothesis,0.0055684924572239,-0.0055684924572239,0.0213624925027616,exact_predefined_module_membership_projection,True,True,True,True,True,True,True,True,True,AD;APOE;Alzheimer;DAM;GFAP;GO;Iba1;KEGG;MSigDB;NeuN;Reactome;TREM2;amyloid;antigen presentation;antigen_presentation;at8_associated_first_pass;chemokine;chemokine_migration;complement;disease_associated_microglia;homeostatic_microglia;inflammatory_signaling;interferon;interferon_response;lipid_metabolism;lysosome;lysosome_phagocytosis;microglia;oxidative stress;oxidative_stress;phagocytosis;plaque_response;senescence;senescence_stress;synapse_pruning;tau;vascular_barrier_myeloid,resource_003;resource_005;resource_015;resource_016;resource_019;resource_024;resource_031;resource_038;resource_087;resource_093;resource_168;resource_172;resource_174;resource_176;resource_178;resource_180;resource_193;resource_198;resource_211;resource_213;resource_214;resource_217;resource_219;resource_220;resource_223;resource_225;resource_226;resource_229;resource_231;resource_232;resource_235;resource_237;resource_238;resource_341;resource_343;resource_379;resource_380,37,high,known_prior_supported,local prior-knowledge annotation only; knowledge support is not validation; requires independent validation
```

## 8. What passed

Inventory, schema registry, gene annotations, hypothesis grounding, safety audit, and report were written. No web scraping, downloads, model training, external validation, or ablation reruns were performed.

## 9. What remains unresolved

No clean external validation was run. No causal or therapeutic claims are supported. Genes without local prior support should be described as no-local-prior-found, not validated novel targets.

## 10. Safe claim language

- Stage 36B performs local prior-knowledge grounding of Stage 36A model-implied hypotheses.
- Knowledge support is not validation.
- No clean external validation was run.
- No causal or therapeutic claims are supported.
- Genes without local prior support should be described as no-local-prior-found, not validated novel targets.

## 11. Forbidden claim language

- Do not claim validated targets.
- Do not claim therapeutic targets.
- Do not claim causal regulators.
- Do not claim external validation succeeded.
- Do not claim novel genes were discovered.
- Do not claim Graph-JEPA proves causality.

## 12. Recommended next step

Use Stage 36B annotations as inputs to a ranked follow-up hypothesis package while keeping validation and causality claims out of scope.

## Audit

```csv
clean_holdout_used,external_validation_run,external_labels_used_for_supervised_pathology_prediction,web_scraping_run,new_resource_downloaded,in_silico_ablation_run,causal_validation_claim_used,therapeutic_target_language_used,novelty_overclaim_used,annotation_fabrication_detected,knowledge_grounding_audit_pass
False,False,False,False,False,False,False,False,False,False,True
```

## Pass/fail

```csv
stage36b_run,stage36a_inputs_found,local_resource_inventory_written,schema_registry_written,n_local_resources_scanned,n_schema_stable_resources,n_stage36a_gene_hypotheses,n_gene_hypotheses_annotated,stage36b_knowledge_grounding_pass,stage36b_run_pass,no_web_scraping,no_downloads,no_external_validation,no_causal_claim,no_therapeutic_claim,controlled_interpretation
True,True,True,True,393,103,770,770,True,True,True,True,True,True,True,"Stage 36B created a local prior-knowledge grounding schema for Stage 36A model-implied hypotheses. Knowledge support is annotation only, not validation."
```
