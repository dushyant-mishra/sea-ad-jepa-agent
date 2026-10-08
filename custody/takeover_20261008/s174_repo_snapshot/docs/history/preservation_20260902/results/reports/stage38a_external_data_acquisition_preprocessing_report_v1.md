# Stage 38A external data acquisition/preprocessing report v1

## Purpose

Acquire/preprocess local external dataset inputs for Stage 38B using frozen Stage 36E candidates. No validation or modeling is run.

## Acquisition plan

```csv
dataset_id,accession,dataset_name,intended_stage,intended_use,priority,expected_modality,expected_metadata,expected_pathology_or_disease_readout,acquisition_status,automated_download_possible,manual_download_required,local_expected_root,notes
gse160936,GSE160936,GSE160936 pTau-linked glial support,Stage37C/38B,pTau/AT8-linked glial external support,high,human AD transcriptomic expression with glial/pathology metadata,"cell type, donor/sample, disease/pathology, pTau/tau where available","pTau/AT8, GFAP/Iba1-relevant glial metadata if available",manual_acquisition_required,False,True,data/external/gse160936/,Stage 38A did not download; use official GEO/SRA manually if needed.
gse125050,GSE125050,GSE125050 pathology-confirmed AD cell-type support,Stage37D/38B,pathology-confirmed AD/control cell-type support,high,human AD single-cell/single-nucleus expression,"cell type, donor/sample, AD/control, pathology-confirmed labels",amyloid/pathology-confirmed AD/control where available,manual_acquisition_required,False,True,data/external/gse125050/,Stage 38A did not download; use official GEO/SRA manually if needed.
gse157827,GSE157827,GSE157827 broad AD/control snRNA-seq support,Stage37E/38B,broad AD/control mechanism directionality support,high,human AD single-nucleus expression,"cell type, donor/sample, disease status",AD/control labels,local_files_found,False,False,data/external/gse157827/,Stage 38A did not download; use official GEO/SRA manually if needed.
gse138852,GSE138852,GSE138852 Grubman-Leng entorhinal cortex smoke test,Stage37F/38B,entorhinal cortex directional smoke test,medium,human AD/control single-nucleus expression,cell type and AD/control covariates,AD/control labels,local_files_found,False,False,data/external/gse138852/,Stage 38A did not download; use official GEO/SRA manually if needed.
gse174367,GSE174367,GSE174367 Morabito optional secondary stress-test,optional_secondary,optional stress-test/projection only,low,human AD single-nucleus expression,"cell type, donor/sample, disease status if available",optional secondary AD/control labels,local_files_found,False,False,data/external/gse174367/,Stage 38A did not download; use official GEO/SRA manually if needed.
```

## Preprocessing readiness

```csv
dataset_id,local_data_found,raw_expression_found,processed_expression_found,metadata_found,celltype_annotations_found,disease_or_diagnosis_metadata_found,tau_or_ptau_metadata_found,amyloid_or_abeta_metadata_found,donor_or_sample_metadata_found,preprocessing_attempted,preprocessing_success,analysis_ready_for_stage38b,reason_if_not_ready,recommended_next_action
gse160936,False,False,False,False,False,False,False,False,False,False,False,False,manual_acquisition_or_full_preprocessing_required,manual acquisition/preprocessing required
gse125050,False,False,False,False,False,False,False,False,False,False,False,False,manual_acquisition_or_full_preprocessing_required,manual acquisition/preprocessing required
gse157827,True,True,False,False,False,False,False,False,False,False,False,False,manual_acquisition_or_full_preprocessing_required,manual acquisition/preprocessing required
gse138852,True,True,True,True,True,True,False,False,True,True,True,True,,run Stage 38B
gse174367,True,True,False,True,False,True,False,False,True,False,False,False,manual_acquisition_or_full_preprocessing_required,manual acquisition/preprocessing required
```

## Processed input index

```csv
dataset_id,processed_expression_path,processed_metadata_path,processed_gene_index_path,processed_celltype_column,processed_disease_column,processed_pathology_columns,n_samples_or_cells,n_genes,n_candidate_genes_detectable,analysis_ready,analysis_ready_for_stage38b,notes
gse160936,,,,,,,0,0,0,False,False,manual_acquisition_or_full_preprocessing_required
gse125050,,,,,,,0,0,0,False,False,manual_acquisition_or_full_preprocessing_required
gse157827,,,,,,,0,0,0,False,False,manual_acquisition_or_full_preprocessing_required
gse138852,data\external\gse138852\processed\stage38a_gse138852_candidate_expression.csv,data\external\gse138852\processed\stage38a_gse138852_metadata.csv,data\external\gse138852\processed\stage38a_gse138852_gene_index.csv,oupSample.cellType,oupSample.batchCond,,13214,12,12,True,True,candidate-gene matrix prepared from local files
gse174367,,,,,Diagnosis,Plaque.Stage,0,0,0,False,False,manual_acquisition_or_full_preprocessing_required
```

## Missing/manual acquisition requirements

- GSE160936 (gse160936): place expression, metadata, and gene metadata under data/external/gse160936/raw/ then rerun Stage 38A.
- GSE125050 (gse125050): place expression, metadata, and gene metadata under data/external/gse125050/raw/ then rerun Stage 38A.
- GSE157827 (gse157827): place expression, metadata, and gene metadata under data/external/gse157827/raw/ then rerun Stage 38A.
- GSE174367 (gse174367): place expression, metadata, and gene metadata under data/external/gse174367/raw/ then rerun Stage 38A.

## Claim boundaries

Allowed: acquired/prepared external support dataset; not yet clean validation. Avoid: validated; clean external validation completed; causal regulator; therapeutic target; disease-modifying target; gene ablation result.

## Pass/fail

stage38a_run,stage36e_inputs_found,stage37c_f_inputs_found,acquisition_plan_written,download_manifest_written,local_file_inventory_written,checksum_manifest_written,preprocessing_readiness_written,processed_input_index_written,gene_symbol_harmonization_written,metadata_harmonization_written,celltype_metadata_summary_written,pathology_metadata_summary_written,claim_level_written,data_commit_exclusion_audit_written,no_new_sea_ad_model_training,no_model_selection_using_external_datasets,no_candidate_selection_using_external_datasets,no_threshold_tuning_using_external_datasets,no_clean_external_validation_claim,no_causal_claim,no_therapeutic_claim,no_gene_ablation_claim,raw_data_not_committed,safety_audit_pass,stage38a_run_pass,controlled_interpretation
True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,"Stage 38A acquired/prepared local external inputs only; it does not validate, train, tune, or select candidates."
