# Stage 32B approved external pretraining acquisition/build report v1

## Executive summary

Registry datasets scanned: `26`. Approved pretraining candidates: `6`. Local matrices found: `19`. Matrices included: `0`. Matrix built: `False`. Ready for Stage 33A: `False`.

## Boundary

Stage 32B is not external validation, does not train a model, does not use external labels for model selection, and does not update manuscript claims. Datasets used for self-supervised pretraining are forfeited as clean validation.

## Candidate download/build plan

```csv
dataset_id,dataset_name,source,collection_name,priority_rank,approved_for_pretraining,local_matrix_found,local_matrix_loaded,download_default_allowed,requires_allow_download_flag,acquisition_mode,exact_next_action,clean_validation_boundary
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,Human Brain Cell Atlas v1.0,0,True,False,False,False,True,manual_or_allow_download_cellxgene,"manual/approved CELLxGENE Census or H5AD download required; record dataset ID, collection ID, version, URL/source, and command",using this dataset for pretraining forfeits clean-validation use
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,1,True,False,False,False,True,manual_or_allow_download_cellxgene,"manual/approved CELLxGENE Census or H5AD download required; record dataset ID, collection ID, version, URL/source, and command",using this dataset for pretraining forfeits clean-validation use
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,2,True,False,False,False,True,manual_or_allow_download_cellxgene,"manual/approved CELLxGENE Census or H5AD download required; record dataset ID, collection ID, version, URL/source, and command",using this dataset for pretraining forfeits clean-validation use
GSE98969,Mouse DAM/microglia auxiliary candidate,GEO,,3,True,False,False,False,True,manual_or_allow_download_geo,manual/approved GEO processed matrix build required; only parse recognized documented formats,using this dataset for pretraining forfeits clean-validation use
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,CELLxGENE,A taxonomy of transcriptomic cell types across the isocortex and hippocampal formation,4,True,False,False,False,True,manual_or_allow_download_cellxgene,"manual/approved CELLxGENE Census or H5AD download required; record dataset ID, collection ID, version, URL/source, and command",using this dataset for pretraining forfeits clean-validation use
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,CELLxGENE,Molecular and spatial signatures of mouse brain aging at single-cell resolution,5,True,False,False,False,True,manual_or_allow_download_cellxgene,"manual/approved CELLxGENE Census or H5AD download required; record dataset ID, collection ID, version, URL/source, and command",using this dataset for pretraining forfeits clean-validation use
```

## Approved matrix inventory

```csv
matrix_local_path,file_size_bytes,matrix_format,matched_dataset_id,registry_match_method,registry_match_details,approved_registry_match,matrix_found,matrix_loaded,n_cells_or_rows,n_donors_or_samples,n_genes_raw,var_name_example,cell_type_column,donor_column,disease_column,tissue_column,species_column,normalization_status,warnings
data\external\cellxgene\olah_live_microglia.h5ad,95126456,.h5ad,Olah_live_microglia,dataset_id_token_match,unique_match,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\external\cellxgene\rexach_cross_dementia.h5ad,4993733632,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5,273975534,.h5,GSE174367,dataset_id_token_match,unique_match,False,True,False,0,0,0,,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
data\processed\sea_ad_mtg_contiguous_10k_hvg3k.h5ad,163302920,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad,116795656,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad,115680777,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad,458239253,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad,462024617,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\sea_ad_mtg_microglia_pvm_smoke_hvg200.h5ad,178984,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad,15925953,.h5ad,Olah_live_microglia,dataset_id_token_match,unique_match,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad,40155153,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\v2_pretraining\cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad,79250658,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad,50149439,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad,22413461,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\raw\fake_k562.h5ad,376240,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\raw\kampmann_gse178317\GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5,69120984,.h5,,no_registry_match,,False,True,False,0,0,0,,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
data\raw\kampmann_gse178317\GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5,763812,.h5,,no_registry_match,,False,True,False,0,0,0,,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
data\raw\ReplogleWeissman2022_K562_gwps.h5ad,8805466154,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad,36319410584,.h5ad,,no_registry_match,,False,True,False,0,0,0,,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
```

## Gene overlap audit

```csv
dataset_id,dataset_name,matrix_local_path,n_genes_raw,n_genes_aligned,gene_overlap_fraction,gene_overlap_status,missing_gene_count,gene_alignment_method,mouse_ortholog_warning,included_in_pretraining_matrix,exclusion_reason
Olah_live_microglia,Olah live human microglia,data\external\cellxgene\olah_live_microglia.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\external\cellxgene\rexach_cross_dementia.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
GSE174367,Morabito prefrontal cortex snRNA-seq,data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_contiguous_10k_hvg3k.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\sea_ad_mtg_microglia_pvm_smoke_hvg200.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
Olah_live_microglia,Olah live human microglia,data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_pretraining\cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\fake_k562.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\kampmann_gse178317\GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\kampmann_gse178317\GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\ReplogleWeissman2022_K562_gwps.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
,,data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad,0,0,0.0,not_evaluated_excluded_or_unsupported,2957,case_insensitive_hgnc_intersect_only,,False,no_confident_registry_match; not_approved_for_pretraining; matrix_not_loaded_or_unsupported; gene_overlap_below_0_85
```

## Metadata schema audit

```csv
dataset_id,dataset_name,matrix_local_path,matrix_loaded,n_cells_or_rows,n_donors_or_samples,cell_type_column,donor_column,disease_column,tissue_column,species_column,normalization_status,schema_warning
Olah_live_microglia,Olah live human microglia,data\external\cellxgene\olah_live_microglia.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\external\cellxgene\rexach_cross_dementia.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
GSE174367,Morabito prefrontal cortex snRNA-seq,data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5,False,0,0,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
,,data\processed\sea_ad_mtg_contiguous_10k_hvg3k.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\sea_ad_mtg_microglia_pvm_smoke_hvg200.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
Olah_live_microglia,Olah live human microglia,data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\v2_pretraining\cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\processed\v2_pretraining\sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\raw\fake_k562.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\raw\kampmann_gse178317\GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5,False,0,0,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
,,data\raw\kampmann_gse178317\GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5,False,0,0,,,,,,unsupported_for_automatic_stage32_build,format_.h5_inventory_only
,,data\raw\ReplogleWeissman2022_K562_gwps.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
,,data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad,False,0,0,,,,,,not_inspected_excluded_or_large,deep_h5ad_inspection_skipped_not_approved_or_ambiguous
```

## Holdout protection audit

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

## Matrix manifest

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

## Pass/fail

```csv
registry_loaded,roles_normalized,clean_holdouts_protected,no_forbidden_dataset_included,candidate_download_plan_written,matrix_inventory_written,gene_overlap_audit_written,metadata_schema_audit_written,manifest_written,stage32b_audit_complete,stage32b_matrix_built,stage32b_ready_for_stage33a,stage32b_pass,n_registry_datasets_scanned,n_approved_pretraining_candidates,n_local_matrices_found,n_matrices_included,included_dataset_ids,matrix_path
True,True,True,True,True,True,True,True,True,True,False,False,True,26,6,19,0,,
```

## Next action

Stage 33A must be skipped until one specific approved pretraining candidate is manually approved/downloaded/built or an approved local matrix is provided.
