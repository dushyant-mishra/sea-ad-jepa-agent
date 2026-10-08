# Stage 27 external pretraining readiness v1

## Summary

Eligible registry datasets scanned: `6`.
Datasets with a local candidate matrix: `0`.
No files were downloaded. Clean external holdouts were excluded from eligibility.

## Readiness table

```csv
dataset_id,dataset_name,collection_name,role,allowed_for_training,allowed_for_pretraining,reserved_for_clean_validation,clean_holdout_protected,local_matrix_found,local_paths,expected_format,requires_preuse_audit,readiness_status,next_action
GSE98969,Mouse DAM/microglia auxiliary candidate,,external_training_pretraining_pool,True,True,False,True,False,,"aligned donor/cell expression H5AD or CSV/TSV mapped to the 2,957-gene universe",True,missing_external_matrix,"build or download one approved processed matrix, then align genes; do not use clean holdouts"
b165f033-9dec-468a-9248-802fc6902a74,All non-neuronal cells,Human Brain Cell Atlas v1.0,external_training_pretraining_pool,True,True,False,True,False,,"aligned donor/cell expression H5AD or CSV/TSV mapped to the 2,957-gene universe",True,missing_external_matrix,"build or download one approved processed matrix, then align genes; do not use clean holdouts"
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,external_training_pretraining_pool,True,True,False,True,False,,"aligned donor/cell expression H5AD or CSV/TSV mapped to the 2,957-gene universe",True,missing_external_matrix,"build or download one approved processed matrix, then align genes; do not use clean holdouts"
4442d412-91cb-4261-acca-8adf5fa04c11,Aging_Cohort,Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution,external_training_pretraining_pool,True,True,False,True,False,,"aligned donor/cell expression H5AD or CSV/TSV mapped to the 2,957-gene universe",True,missing_external_matrix,"build or download one approved processed matrix, then align genes; do not use clean holdouts"
mouse_isocortex_hippocampus,Mouse isocortex and hippocampal formation taxonomy,A taxonomy of transcriptomic cell types across the isocortex and hippocampal formation,mouse_auxiliary_only,True,True,False,True,False,,"aligned donor/cell expression H5AD or CSV/TSV mapped to the 2,957-gene universe",True,missing_external_matrix,"build or download one approved processed matrix, then align genes; do not use clean holdouts"
mouse_brain_aging_atlas,BrainAgingSpatialAtlas_snRNAseq,Molecular and spatial signatures of mouse brain aging at single-cell resolution,mouse_auxiliary_only,True,True,False,True,False,,"aligned donor/cell expression H5AD or CSV/TSV mapped to the 2,957-gene universe",True,missing_external_matrix,"build or download one approved processed matrix, then align genes; do not use clean holdouts"
```

## Next action

Select one registry-approved training/pretraining dataset, obtain a processed matrix, run matrix/gene-overlap/donor-mapping audits, align to the fixed 2,957-gene universe, and only then run Stage 27B.
