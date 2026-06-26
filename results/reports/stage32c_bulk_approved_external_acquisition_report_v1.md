# Stage 32C bulk approved external acquisition report v1

## 1. Executive summary

Approved candidates: `1`. Download attempted: `True`. Download succeeded: `True`. Human matrix built: `True`. Ready for Stage 33: `True`.

## 2. Why Stage 32C was run

Stage 32C performs a bulk acquisition/schema audit for all registry-approved self-supervised pretraining candidates before any Stage 33 external-pretrained JEPA benchmark.

## 3. Approved pretraining candidates

```csv
dataset_id,dataset_name,source,collection_name,priority_rank,approved_for_pretraining,allow_download,metadata_first,download_expression,acquisition_status,local_path,metadata_acquisition_attempted,metadata_acquisition_succeeded,metadata_source,metadata_local_path,metadata_error,cellxgene_census_available,remote_payload_keys,remote_n_obs,remote_n_vars,remote_schema_note,exact_next_action
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,Human Brain Cell Atlas v1.0,0,True,True,False,True,expression_matrix_built,data/external_pretraining/stage32c/stage32c_human_external_pretraining_matrix.h5ad,True,True,cellxgene_census_expression_subset,data/external_pretraining/stage32c/stage32c_human_external_pretraining_manifest.json,,True,,100000,2863,project_gene_subset_expression_matrix_built_with_cell_cap,Stage 33 may proceed after readiness/status review
```

## 4. Download/acquisition results

```csv
dataset_id,dataset_name,source,acquisition_status,local_path,metadata_source,metadata_local_path,metadata_error,file_size_bytes,included_in_candidate_matrix,exclusion_reason
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,expression_matrix_built,data/external_pretraining/stage32c/stage32c_human_external_pretraining_matrix.h5ad,cellxgene_census_expression_subset,data/external_pretraining/stage32c/stage32c_human_external_pretraining_manifest.json,,707295000,True,none
```

## 5. Schema and column-name inventory

```csv
dataset_id,dataset_name,source,collection_name,registry_role,allowed_for_pretraining,reserved_for_clean_validation,allowed_for_model_selection,already_used,normalized_role,approved_for_pretraining,clean_holdout_protected,stress_test_only,plausibility_only,internal_dataset,model_selection_excluded,role_exclusion_reason,priority_rank,local_path,schema_loaded,n_obs,n_vars,obsm_keys,uns_keys,gene_identifier_type,example_var_names,raw_available,normalization_status,schema_warning
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,Human Brain Cell Atlas v1.0,external_training_pretraining_pool,True,False,False,False,approved_self_supervised_pretraining,True,False,False,False,False,False,none,0,data/external_pretraining/stage32c/stage32c_human_external_pretraining_matrix.h5ad,True,100000,2863,,stage32c,project_hgnc_symbol,project_gene_subset,False,raw_count_like,downsampled_to_configured_max_cells
```

## 6. Gene overlap results

```csv
dataset_id,dataset_name,local_path,n_genes_raw,n_genes_aligned,gene_overlap_fraction,gene_overlap_status,missing_gene_count,included_in_candidate_matrix
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,data/external_pretraining/stage32c/stage32c_human_external_pretraining_matrix.h5ad,2863,2863,0.968211024687183,good,94,True
```

## 7. Normalization and layer audit

```csv
dataset_id,normalization_status,raw_available,layer_names,normalization_warning
b165f033-9dec-468a-9248-802fc6902a74,raw_count_like,False,,source_expression_preserved_from_cellxgene_census_no_extra_normalization
```

## 8. Human-ready datasets

```csv
dataset_id,dataset_name,recommendation_class,recommended_next_use,reason
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,human_ready_candidate,Stage 33 candidate,approved human matrix appears usable
```

## 9. Mouse/ortholog-required datasets

```csv
dataset_id,dataset_name,species,ortholog_mapping_required,ortholog_mapping_available,main_human_matrix_eligible
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,human_or_unknown,False,False,True
```

## 10. Protected holdout audit

```csv
dataset_id,dataset_name,registry_role,normalized_role,matrix_downloaded,included,protection_pass
SEA-AD_internal,SEA-AD Microglia-PVM internal benchmark,main_internal_benchmark,excluded_internal,False,False,True
GSE157827,Candidate public external brain snRNA/scRNA dataset,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
GSE147528,Candidate public external brain snRNA/scRNA dataset,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
GSE203206,Bulk donor/sample-level external stress test,external_stress_test,protected_clean_holdout,False,False,True
GSE181279,Peripheral immune plausibility/auxiliary dataset,auxiliary_training_pool,excluded_plausibility_only,False,False,True
GSE174367,Morabito prefrontal cortex snRNA-seq,already_used_plausibility_only,excluded_plausibility_only,False,False,True
GSE138852,Grubman/Leng entorhinal cortex,already_used_plausibility_only,excluded_plausibility_only,False,False,True
37a17b78-4864-4a42-b67b-31c00962795a,MSSM_Cohort,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
5e57cd50-8e42-42d6-940d-5c1660d06864,RADC_Cohort,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
cff99df2-4904-44f7-9173-ff837f95606e,all cells,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
203025fe-fa99-4d57-81da-458ed8f0c334,Brain vascular single-cell multi-omics disease-risk snRNA-seq,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
0a2d7e87-c3c0-4ed2-86df-ae18811fcc16,Full Dataset,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
fe2eecbc-977a-4aec-9196-f89c3281d11c,Microglia,clean_external_holdout_candidate,protected_clean_holdout,False,False,True
Olah_live_microglia,Olah live human microglia,already_used_plausibility_only,excluded_plausibility_only,False,False,True
ac0c6561-7a48-4185-af6f-af799f699172,All Cells - snRNA-seq,already_used_plausibility_only,excluded_plausibility_only,False,False,True
SEA_AD_CELLXGENE_DLPFC,Whole Taxonomy - DLPFC,already_used_plausibility_only,excluded_plausibility_only,False,False,True
SEA_AD_CELLXGENE_MTG,Whole Taxonomy - MTG,already_used_plausibility_only,excluded_plausibility_only,False,False,True
Tabula_Sapiens_immune,Tabula Sapiens - Immune,auxiliary_training_pool,excluded_plausibility_only,False,False,True
Tabula_Sapiens_myeloid,Tabula Sapiens myeloid/immune cells,auxiliary_training_pool,excluded_plausibility_only,False,False,True
```

## 11. Candidate matrix recommendation

```csv
dataset_id,dataset_name,recommendation_class,recommended_next_use,reason
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,human_ready_candidate,Stage 33 candidate,approved human matrix appears usable
```

## 12. Whether Stage 33 can proceed

Stage 33 can proceed only if `stage32c_ready_for_stage33=True`.

## 13. Interpretation boundary

Stage 32C does not train a model. Stage 32C does not run external validation. Stage 32C does not use external labels for supervised prediction. Stage 32C does not validate in silico ablation. Stage 32C does not update manuscript claims. Any dataset used for pretraining is forfeited as clean validation.

## 14. Exact next command

`python scripts/run_stage33a_external_pretrained_jepa_v1.py --config configs/train/stage33a_external_pretrained_jepa_v1.yaml`
