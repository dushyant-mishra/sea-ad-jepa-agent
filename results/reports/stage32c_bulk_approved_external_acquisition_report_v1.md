# Stage 32C bulk approved external acquisition report v1

## 1. Executive summary

Approved candidates: `6`. Download attempted: `False`. Download succeeded: `False`. Human matrix built: `False`. Ready for Stage 33: `False`.

## 2. Why Stage 32C was run

Stage 32C performs a bulk acquisition/schema audit for all registry-approved self-supervised pretraining candidates before any Stage 33 external-pretrained JEPA benchmark.

## 3. Approved pretraining candidates

```csv
dataset_id,dataset_name,source,collection_name,priority_rank,approved_for_pretraining,allow_download,metadata_first,download_expression,acquisition_status,local_path,exact_next_action
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,Human Brain Cell Atlas v1.0,0,True,False,False,False,not_acquired_no_download_default,,run with --allow-download --metadata-first first; use --download-expression only after source/version/size are approved
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,1,True,False,False,False,not_acquired_no_download_default,,run with --allow-download --metadata-first first; use --download-expression only after source/version/size are approved
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,2,True,False,False,False,not_acquired_no_download_default,,run with --allow-download --metadata-first first; use --download-expression only after source/version/size are approved
GSE98969,Mouse DAM/microglia auxiliary candidate,GEO,,3,True,False,False,False,not_acquired_no_download_default,,run with --allow-download --metadata-first first; use --download-expression only after source/version/size are approved
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,CELLxGENE,A taxonomy of transcriptomic cell types across the isocortex and hippocampal formation,4,True,False,False,False,not_acquired_no_download_default,,run with --allow-download --metadata-first first; use --download-expression only after source/version/size are approved
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,CELLxGENE,Molecular and spatial signatures of mouse brain aging at single-cell resolution,5,True,False,False,False,not_acquired_no_download_default,,run with --allow-download --metadata-first first; use --download-expression only after source/version/size are approved
```

## 4. Download/acquisition results

```csv
dataset_id,dataset_name,source,acquisition_status,local_path,file_size_bytes,included_in_candidate_matrix,exclusion_reason
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,not_acquired_no_download_default,,0,False,no safe human matrix built in Stage 32C default run
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,CELLxGENE,not_acquired_no_download_default,,0,False,no safe human matrix built in Stage 32C default run
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,CELLxGENE,not_acquired_no_download_default,,0,False,no safe human matrix built in Stage 32C default run
GSE98969,Mouse DAM/microglia auxiliary candidate,GEO,not_acquired_no_download_default,,0,False,no safe human matrix built in Stage 32C default run
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,CELLxGENE,not_acquired_no_download_default,,0,False,no safe human matrix built in Stage 32C default run
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,CELLxGENE,not_acquired_no_download_default,,0,False,no safe human matrix built in Stage 32C default run
```

## 5. Schema and column-name inventory

```csv
dataset_id,dataset_name,source,collection_name,registry_role,allowed_for_pretraining,reserved_for_clean_validation,allowed_for_model_selection,already_used,normalized_role,approved_for_pretraining,clean_holdout_protected,stress_test_only,plausibility_only,internal_dataset,model_selection_excluded,role_exclusion_reason,priority_rank,local_path,schema_loaded,n_obs,n_vars,obsm_keys,uns_keys,gene_identifier_type,example_var_names,raw_available,normalization_status,schema_warning
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,CELLxGENE,Human Brain Cell Atlas v1.0,external_training_pretraining_pool,True,False,False,False,approved_self_supervised_pretraining,True,False,False,False,False,False,none,0,,False,0,0,,,unknown,,False,not_loaded,no_approved_local_loaded_matrix
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,external_training_pretraining_pool,True,False,False,False,approved_self_supervised_pretraining,True,False,False,False,False,False,none,1,,False,0,0,,,unknown,,False,not_loaded,no_approved_local_loaded_matrix
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,CELLxGENE,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,external_training_pretraining_pool,True,False,False,False,approved_self_supervised_pretraining,True,False,False,False,False,False,none,2,,False,0,0,,,unknown,,False,not_loaded,no_approved_local_loaded_matrix
GSE98969,Mouse DAM/microglia auxiliary candidate,GEO,,external_training_pretraining_pool,True,False,False,False,approved_self_supervised_pretraining,True,False,False,False,False,False,none,3,,False,0,0,,,unknown,,False,not_loaded,no_approved_local_loaded_matrix
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,CELLxGENE,A taxonomy of transcriptomic cell types across the isocortex and hippocampal formation,mouse_auxiliary_only,True,False,False,False,approved_self_supervised_pretraining,True,False,False,False,False,False,none,4,,False,0,0,,,unknown,,False,not_loaded,no_approved_local_loaded_matrix
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,CELLxGENE,Molecular and spatial signatures of mouse brain aging at single-cell resolution,mouse_auxiliary_only,True,False,False,False,approved_self_supervised_pretraining,True,False,False,False,False,False,none,5,,False,0,0,,,unknown,,False,not_loaded,no_approved_local_loaded_matrix
```

## 6. Gene overlap results

```csv
dataset_id,dataset_name,local_path,n_genes_raw,n_genes_aligned,gene_overlap_fraction,gene_overlap_status,missing_gene_count,included_in_candidate_matrix
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,,0,0,0.0,not_evaluated_no_matrix,2957,False
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,,0,0,0.0,not_evaluated_no_matrix,2957,False
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,,0,0,0.0,not_evaluated_no_matrix,2957,False
GSE98969,Mouse DAM/microglia auxiliary candidate,,0,0,0.0,not_evaluated_no_matrix,2957,False
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,,0,0,0.0,not_evaluated_no_matrix,2957,False
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,,0,0,0.0,not_evaluated_no_matrix,2957,False
```

## 7. Normalization and layer audit

```csv
dataset_id,normalization_status,raw_available,layer_names,normalization_warning
b165f033-9dec-468a-9248-802fc6902a74,not_loaded,False,,no_approved_local_loaded_matrix
5c97eeeb-7e52-44b3-b010-b832b1f5424c,not_loaded,False,,no_approved_local_loaded_matrix
4442d412-91cb-4261-acca-8adf5fa04c11,not_loaded,False,,no_approved_local_loaded_matrix
GSE98969,not_loaded,False,,no_approved_local_loaded_matrix
mouse_isocortex_hippocampus,not_loaded,False,,no_approved_local_loaded_matrix
mouse_brain_aging_atlas,not_loaded,False,,no_approved_local_loaded_matrix
```

## 8. Human-ready datasets

```csv
dataset_id,dataset_name,recommendation_class,recommended_next_use,reason
```

## 9. Mouse/ortholog-required datasets

```csv
dataset_id,dataset_name,species,ortholog_mapping_required,ortholog_mapping_available,main_human_matrix_eligible
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,human_or_unknown,False,False,False
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,human_or_unknown,False,False,False
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,human_or_unknown,False,False,False
GSE98969,Mouse DAM/microglia auxiliary candidate,mouse,True,False,False
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,mouse,True,False,False
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,mouse,True,False,False
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
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,acquire_or_build_matrix_before_stage33,not ready for Stage 33,no approved loaded matrix or insufficient gene/schema audit
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,acquire_or_build_matrix_before_stage33,not ready for Stage 33,no approved loaded matrix or insufficient gene/schema audit
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,acquire_or_build_matrix_before_stage33,not ready for Stage 33,no approved loaded matrix or insufficient gene/schema audit
GSE98969,Mouse DAM/microglia auxiliary candidate,ortholog_mapping_required,not ready for Stage 33,no approved loaded matrix or insufficient gene/schema audit
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,ortholog_mapping_required,not ready for Stage 33,no approved loaded matrix or insufficient gene/schema audit
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,ortholog_mapping_required,not ready for Stage 33,no approved loaded matrix or insufficient gene/schema audit
```

## 12. Whether Stage 33 can proceed

Stage 33 can proceed only if `stage32c_ready_for_stage33=True`.

## 13. Interpretation boundary

Stage 32C does not train a model. Stage 32C does not run external validation. Stage 32C does not use external labels for supervised prediction. Stage 32C does not validate in silico ablation. Stage 32C does not update manuscript claims. Any dataset used for pretraining is forfeited as clean validation.

## 14. Exact next command

`python scripts/acquire_stage32c_bulk_approved_external_datasets_v1.py --config configs/data/stage32c_bulk_approved_external_acquisition_v1.yaml --allow-download --metadata-first`
