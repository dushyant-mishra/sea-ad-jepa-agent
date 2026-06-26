# Stage 32 external pretraining matrix report v1

## 1. Executive summary

Registry datasets scanned: `26`. Approved for pretraining: `6`. Local matrices found: `19`. Matrices included: `0`. Matrix built: `False`. Stage 33 ready: `False`.

## 2. Why Stage 32 was run

Stage 31 showed that weak residual graph diffusion nearly matched but did not beat Stage 27C. The next useful step is to build an approved external self-supervised pretraining substrate, not to keep tuning the 84-donor supervised benchmark.

## 3. Stage 27C / Stage 30 / Stage 31 recap

Stage 27C remains the current best internal no-graph benchmark at mean pooled OOF Spearman 0.326702. Stage 30 mandatory graph smoothing failed graph-specific pass. Stage 31 weak residual graph reached 0.326370 but did not beat Stage 27C/no-graph.

## 4. Dataset role policy

Primary inclusion gate: `allowed_for_pretraining == True`. Always excluded: reserved clean validation, model-selection datasets, stress-test-only datasets, plausibility-only datasets without explicit pretraining approval, already-used datasets without explicit pretraining approval, internal SEA-AD files, and clean AD/dementia holdout candidates.

## 5. Approved pretraining candidates

Expected currently approved set from config: `GSE98969, b165f033-9dec-468a-9248-802fc6902a74, 5c97eeeb-7e52-44b3-b010-b832b1f5424c, 4442d412-91cb-4261-acca-8adf5fa04c11, mouse_isocortex_hippocampus, mouse_brain_aging_atlas`.

```csv
dataset_id,dataset_name,source,collection_name,registry_role,normalized_role,approved_for_pretraining,clean_holdout_protected,stress_test_only,plausibility_only,internal_dataset,model_selection_excluded,already_used,role_exclusion_reason
GSE98969,Mouse DAM/microglia auxiliary candidate,GEO,,external_training_pretraining_pool,approved_self_supervised_pretraining,True,False,False,False,False,False,False,none
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,Human Brain Cell Atlas v1.0,external_training_pretraining_pool,approved_self_supervised_pretraining,True,False,False,False,False,False,False,none
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,external_training_pretraining_pool,approved_self_supervised_pretraining,True,False,False,False,False,False,False,none
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,external_training_pretraining_pool,approved_self_supervised_pretraining,True,False,False,False,False,False,False,none
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,CELLxGENE,A taxonomy of transcriptomic cell types across the isocortex and hippocampal formation,mouse_auxiliary_only,approved_self_supervised_pretraining,True,False,False,False,False,False,False,none
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,CELLxGENE,Molecular and spatial signatures of mouse brain aging at single-cell resolution,mouse_auxiliary_only,approved_self_supervised_pretraining,True,False,False,False,False,False,False,none
```

## 6. Protected holdouts

```csv
dataset_id,dataset_name,registry_role,normalized_role,clean_holdout_protected,stress_test_only,plausibility_only,internal_dataset,matrix_found,matrix_loaded,included,protection_pass
GSE157827,Candidate public external brain snRNA/scRNA dataset,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
GSE147528,Candidate public external brain snRNA/scRNA dataset,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
GSE203206,Bulk donor/sample-level external stress test,external_stress_test,protected_clean_holdout,True,True,False,False,False,False,False,True
GSE181279,Peripheral immune plausibility/auxiliary dataset,auxiliary_training_pool,excluded_plausibility_only,False,False,True,False,False,False,False,True
GSE174367,Morabito prefrontal cortex snRNA-seq,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,True,False,False,True
GSE138852,Grubman/Leng entorhinal cortex,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
37a17b78-4864-4a42-b67b-31c00962795a,MSSM_Cohort,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
5e57cd50-8e42-42d6-940d-5c1660d06864,RADC_Cohort,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
cff99df2-4904-44f7-9173-ff837f95606e,all cells,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
203025fe-fa99-4d57-81da-458ed8f0c334,Brain vascular single-cell multi-omics disease-risk snRNA-seq,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
0a2d7e87-c3c0-4ed2-86df-ae18811fcc16,Full Dataset,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
fe2eecbc-977a-4aec-9196-f89c3281d11c,Microglia,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
Olah_live_microglia,Olah live human microglia,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,True,False,False,True
ac0c6561-7a48-4185-af6f-af799f699172,All Cells - snRNA-seq,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
SEA_AD_CELLXGENE_DLPFC,Whole Taxonomy - DLPFC,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
SEA_AD_CELLXGENE_MTG,Whole Taxonomy - MTG,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
Tabula_Sapiens_immune,Tabula Sapiens - Immune,auxiliary_training_pool,excluded_plausibility_only,False,False,True,False,False,False,False,True
Tabula_Sapiens_myeloid,Tabula Sapiens myeloid/immune cells,auxiliary_training_pool,excluded_plausibility_only,False,False,True,False,False,False,False,True
```

## 7. Matrix inventory

```csv
matrix_local_path,file_size_bytes,matrix_format,matched_dataset_id,registry_match_method,registry_match_details,matrix_found,approved_registry_match,matrix_loaded,n_cells_or_rows,n_donors_or_samples,n_genes_raw,var_name_example,cell_type_column,donor_column,disease_column,tissue_column,species_column,normalization_status,warnings
data\external\cellxgene\olah_live_microglia.h5ad,95126456,.h5ad,Olah_live_microglia,dataset_id_token_match,unique_match,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\external\cellxgene\rexach_cross_dementia.h5ad,4993733632,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5,273975534,.h5,GSE174367,dataset_id_token_match,unique_match,True,False,False,0,0,0,,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
data\processed\sea_ad_mtg_contiguous_10k_hvg3k.h5ad,163302920,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad,116795656,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad,115680777,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad,458239253,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad,462024617,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\sea_ad_mtg_microglia_pvm_smoke_hvg200.h5ad,178984,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad,15925953,.h5ad,Olah_live_microglia,dataset_id_token_match,unique_match,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad,40155153,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\v2_pretraining\cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad,79250658,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad,50149439,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad,22413461,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\raw\fake_k562.h5ad,376240,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\raw\kampmann_gse178317\GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5,69120984,.h5,,no_registry_match,,True,False,False,0,0,0,,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
data\raw\kampmann_gse178317\GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5,763812,.h5,,no_registry_match,,True,False,False,0,0,0,,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
data\raw\ReplogleWeissman2022_K562_gwps.h5ad,8805466154,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad,36319410584,.h5ad,,no_registry_match,,True,False,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
```

## 8. Gene overlap and alignment

Canonical gene universe source: `results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv`; verified source/target/union gene counts equal 2,957.

```csv
dataset_id,dataset_name,matrix_local_path,n_genes_raw,n_genes_aligned,gene_overlap_fraction,gene_overlap_status,missing_gene_count,missing_gene_method,included_in_pretraining_matrix,exclusion_reason
Olah_live_microglia,Olah live human microglia,data\external\cellxgene\olah_live_microglia.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\external\cellxgene\rexach_cross_dementia.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
GSE174367,Morabito prefrontal cortex snRNA-seq,data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_contiguous_10k_hvg3k.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_smoke_hvg200.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
Olah_live_microglia,Olah live human microglia,data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_pretraining\cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\fake_k562.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\kampmann_gse178317\GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\kampmann_gse178317\GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\ReplogleWeissman2022_K562_gwps.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,intersect_only_no_imputation,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
```

## 9. Normalization status

No arbitrary normalization was applied. Source matrix status was inspected heuristically when H5AD files were readable. Missing gene method: intersect-only, no imputation.

## 10. Matrix build result

```csv
dataset_id,dataset_name,source,registry_role,matrix_local_path,matrix_found,matrix_loaded,n_cells_or_rows,n_genes_raw,n_genes_aligned,gene_overlap_fraction,included_in_pretraining_matrix,exclusion_reason,used_dataset_removed_from_clean_validation_pool
Olah_live_microglia,Olah live human microglia,CELLxGENE,already_used_plausibility_only,data\external\cellxgene\olah_live_microglia.h5ad,True,False,0,0,0,0.0,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\external\cellxgene\rexach_cross_dementia.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
GSE174367,Morabito prefrontal cortex snRNA-seq,GEO,already_used_plausibility_only,data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5,True,False,0,0,0,0.0,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\sea_ad_mtg_contiguous_10k_hvg3k.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\sea_ad_mtg_microglia_pvm_smoke_hvg200.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
Olah_live_microglia,Olah live human microglia,CELLxGENE,already_used_plausibility_only,data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad,True,False,0,0,0,0.0,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\v2_pretraining\cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\raw\fake_k562.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\raw\kampmann_gse178317\GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\raw\kampmann_gse178317\GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\raw\ReplogleWeissman2022_K562_gwps.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
,,,,data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad,True,False,0,0,0,0.0,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85,False
```

## 11. Holdout protection result

```csv
dataset_id,dataset_name,registry_role,normalized_role,clean_holdout_protected,stress_test_only,plausibility_only,internal_dataset,matrix_found,matrix_loaded,included,protection_pass
SEA-AD_internal,SEA-AD Microglia-PVM internal benchmark,main_internal_benchmark,excluded_internal,False,False,False,True,False,False,False,True
GSE157827,Candidate public external brain snRNA/scRNA dataset,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
GSE147528,Candidate public external brain snRNA/scRNA dataset,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
GSE203206,Bulk donor/sample-level external stress test,external_stress_test,protected_clean_holdout,True,True,False,False,False,False,False,True
GSE181279,Peripheral immune plausibility/auxiliary dataset,auxiliary_training_pool,excluded_plausibility_only,False,False,True,False,False,False,False,True
GSE174367,Morabito prefrontal cortex snRNA-seq,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,True,False,False,True
GSE138852,Grubman/Leng entorhinal cortex,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
37a17b78-4864-4a42-b67b-31c00962795a,MSSM_Cohort,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
5e57cd50-8e42-42d6-940d-5c1660d06864,RADC_Cohort,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
cff99df2-4904-44f7-9173-ff837f95606e,all cells,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
203025fe-fa99-4d57-81da-458ed8f0c334,Brain vascular single-cell multi-omics disease-risk snRNA-seq,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
0a2d7e87-c3c0-4ed2-86df-ae18811fcc16,Full Dataset,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
fe2eecbc-977a-4aec-9196-f89c3281d11c,Microglia,clean_external_holdout_candidate,protected_clean_holdout,True,False,False,False,False,False,False,True
Olah_live_microglia,Olah live human microglia,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,True,False,False,True
ac0c6561-7a48-4185-af6f-af799f699172,All Cells - snRNA-seq,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
SEA_AD_CELLXGENE_DLPFC,Whole Taxonomy - DLPFC,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
SEA_AD_CELLXGENE_MTG,Whole Taxonomy - MTG,already_used_plausibility_only,excluded_plausibility_only,False,False,True,False,False,False,False,True
Tabula_Sapiens_immune,Tabula Sapiens - Immune,auxiliary_training_pool,excluded_plausibility_only,False,False,True,False,False,False,False,True
Tabula_Sapiens_myeloid,Tabula Sapiens myeloid/immune cells,auxiliary_training_pool,excluded_plausibility_only,False,False,True,False,False,False,False,True
```

## 12. Pass/fail decision

```csv
registry_loaded,roles_normalized,audit_complete,holdouts_protected,no_clean_holdout_included,no_stress_test_only_included,no_plausibility_only_included,all_included_datasets_explicitly_approved,gene_overlap_audit_complete,matrix_manifest_written,matrix_built,stage32_ready_for_stage33,stage32_pass,n_registry_datasets_scanned,n_approved_for_pretraining,n_protected_as_clean_holdout,n_local_matrices_found,n_matrices_included,matrix_path,allow_download
True,True,True,True,True,True,True,True,True,True,False,False,True,26,6,9,19,0,,False
```

## 13. Whether Stage 33 can proceed

Stage 33 should not proceed until an approved registry pretraining dataset has a local processed matrix or download/build approval is granted.

## 14. Required next actions

- If no matrix was built, select/download/build one of the approved pretraining datasets with explicit approval, then rerun Stage 32.
- If a matrix was built, Stage 33 may use it for self-supervised pretraining only; used datasets must not later be claimed as clean validation.

## 15. Interpretation boundary

Stage 32 does not train a model. Stage 32 does not update benchmark results. Stage 32 does not create graph-specific evidence. Stage 32 does not validate in silico ablation. Stage 32 does not create clean external validation. Any dataset used for pretraining is removed from the clean-validation pool.

## Cell/sample summary

```csv
dataset_id,dataset_name,matrix_local_path,matrix_loaded,n_cells_or_rows,n_donors_or_samples,cell_type_column,donor_column,disease_column,tissue_column,species_column,normalization_status,warnings
Olah_live_microglia,Olah live human microglia,data\external\cellxgene\olah_live_microglia.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\external\cellxgene\rexach_cross_dementia.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
GSE174367,Morabito prefrontal cortex snRNA-seq,data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5,False,0,0,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
,,data\processed\sea_ad_mtg_contiguous_10k_hvg3k.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\sea_ad_mtg_microglia_pvm_smoke_hvg200.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
Olah_live_microglia,Olah live human microglia,data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\v2_pretraining\cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\raw\fake_k562.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\raw\kampmann_gse178317\GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5,False,0,0,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
,,data\raw\kampmann_gse178317\GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5,False,0,0,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
,,data\raw\ReplogleWeissman2022_K562_gwps.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
,,data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_registry_match
```
