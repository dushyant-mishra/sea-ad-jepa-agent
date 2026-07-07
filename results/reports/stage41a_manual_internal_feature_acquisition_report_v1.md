# Stage 41A manual internal feature acquisition report

## Why Stage 41A was run

Stage 41 found zero benchmark-ready donor-linked safe multimodal/spatial/image feature matrices. Stage 41A therefore defines the manual acquisition plan needed before Stage 41B can build safe feature matrices.

## Resource inventory

| resource_id | resource_name | source_url | modality | expected_file_type | expected_size_class | access_type | internal_or_external | expected_donor_linkage_key | expected_feature_value | leakage_risk | proxy_risk | priority | acquisition_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sea_ad_donor_metadata | SEA-AD donor metadata | https://brain-map.org/consortia/sea-ad/our-data | donor_metadata | csv/metadata table | small | manual | internal | Donor ID | safe donor covariates and linkage keys | low | low | high | planned | Safest first source with strict forbidden predictor filter. |
| sea_ad_mri_volumetrics | Postmortem MRI volumetrics | https://brain-map.org/consortia/sea-ad/our-data | MRI | csv/table or supplement | medium | manual | internal | Donor ID | regional volumes / anatomy context | low | low_to_medium | high | planned | Highest priority benchmark feature after donor metadata. |
| cellxgene_snrna_metadata | Processed snRNA-seq / CELLxGENE donor-cell metadata | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | snRNA_metadata | h5ad/cell metadata | large | manual_or_existing_wsl | internal | donor_id / Donor ID | cell type/subclass/state summaries | medium | medium | high | planned | Build donor-level summaries; avoid disease-state labels as predictors. |
| donor_celltype_composition | Donor-level cell-type/subclass composition summaries | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | composition | derived csv | small | derived_after_manual_acquisition | internal | Donor ID | broad cell-type fractions | medium | medium | medium | derived_needed | Tier2 caution features requiring proxy audit. |
| celltype_module_state_summaries | Cell-type-specific module/state summaries | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | state_summary | derived csv | medium | derived_after_manual_acquisition | internal | Donor ID; cell_type | module/state summaries by cell type | medium | medium_to_high | medium | derived_needed | Must exclude pseudo-pathology/SEAAD target-proxy state labels. |
| spatial_transcriptomics_neighborhoods | Spatial transcriptomics neighborhood summaries | https://brain-map.org/consortia/sea-ad/our-data | spatial | spatial tables / h5ad / coordinates | large | manual | internal | Donor ID; section_id; spot/cell_id | local neighborhood context | medium | medium | high | planned | Compute neighborhoods without target labels. |
| snatac_regulatory_modules | snATAC / regulatory module summaries | https://brain-map.org/consortia/sea-ad/our-data | snATAC | fragment/peak/module tables | large | manual | internal | Donor ID; cell_id | regulatory module context | medium | medium | medium | planned | Potential Tier2 feature; requires modality-specific QC. |
| microglia_multiregion_states | Microglia-enriched multiregion state summaries | https://brain-map.org/consortia/sea-ad/our-data | microglia_state | metadata/expression tables | medium | manual | internal | Donor ID; region | microglia state by region | medium | medium_to_high | medium | planned | Avoid SEAAD/disease burden state labels as direct predictors. |
| he_lfb_non_target_morphology | H&E-LFB or non-target image morphology features | https://brain-map.org/consortia/sea-ad/our-resources | image_morphology | image-derived feature table | medium_to_large | manual | internal | Donor ID; slide_id; section_id | non-target morphology / tissue architecture | medium | medium | medium | planned_later | Use non-target stains first; avoid same-stain same-target leakage. |
| cell_id_conversion_tables | Cell ID conversion / donor linkage tables | https://brain-map.org/consortia/sea-ad/our-resources | linkage | csv/table | small | manual | internal | cell_id; donor_id | linkage only | low | low | high | planned | Required for safe aggregation and provenance tracking. |
| sea_ad_whitepapers_methods | SEA-AD white papers and method documents | https://brain-map.org/consortia/sea-ad/our-resources | documentation | pdf/html | small | manual | internal | N/A | provenance and method constraints | low | low | high | planned | Use for provenance, not predictors. |

## Manual download manifest

| resource_id | resource_name | source_url | manual_download_instruction | recommended_local_path | add_to_git | expected_downstream_script | checksum_required | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sea_ad_donor_metadata | SEA-AD donor metadata | https://brain-map.org/consortia/sea-ad/our-data | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/donor_metadata/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Safest first source with strict forbidden predictor filter. |
| sea_ad_mri_volumetrics | Postmortem MRI volumetrics | https://brain-map.org/consortia/sea-ad/our-data | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/mri_volumetrics/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Highest priority benchmark feature after donor metadata. |
| cellxgene_snrna_metadata | Processed snRNA-seq / CELLxGENE donor-cell metadata | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/cellxgene_snrna/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Build donor-level summaries; avoid disease-state labels as predictors. |
| donor_celltype_composition | Donor-level cell-type/subclass composition summaries | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/donor_celltype_composition/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Tier2 caution features requiring proxy audit. |
| celltype_module_state_summaries | Cell-type-specific module/state summaries | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/celltype_module_state_summaries/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Must exclude pseudo-pathology/SEAAD target-proxy state labels. |
| spatial_transcriptomics_neighborhoods | Spatial transcriptomics neighborhood summaries | https://brain-map.org/consortia/sea-ad/our-data | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/spatial/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Compute neighborhoods without target labels. |
| snatac_regulatory_modules | snATAC / regulatory module summaries | https://brain-map.org/consortia/sea-ad/our-data | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/snatac/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Potential Tier2 feature; requires modality-specific QC. |
| microglia_multiregion_states | Microglia-enriched multiregion state summaries | https://brain-map.org/consortia/sea-ad/our-data | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/microglia_multiregion_states/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Avoid SEAAD/disease burden state labels as direct predictors. |
| he_lfb_non_target_morphology | H&E-LFB or non-target image morphology features | https://brain-map.org/consortia/sea-ad/our-resources | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/image_morphology/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Use non-target stains first; avoid same-stain same-target leakage. |
| cell_id_conversion_tables | Cell ID conversion / donor linkage tables | https://brain-map.org/consortia/sea-ad/our-resources | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | data/manual/sea_ad/linkage_tables/ | False | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Required for safe aggregation and provenance tracking. |
| sea_ad_whitepapers_methods | SEA-AD white papers and method documents | https://brain-map.org/consortia/sea-ad/our-resources | Manually locate and download approved files; record filename, URL, checksum, and provenance before Stage41B. | docs/sea_ad_manual_provenance/ | docs_only_if_license_allows | scripts/build_stage41b_safe_feature_matrices_v1.py | True | Use for provenance, not predictors. |

## Feature source priority

| resource_id | resource_name | source_url | modality | expected_file_type | expected_size_class | access_type | internal_or_external | expected_donor_linkage_key | expected_feature_value | leakage_risk | proxy_risk | priority | acquisition_status | notes | recommended_order | safest_first_benchmark_source | why_priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sea_ad_whitepapers_methods | SEA-AD white papers and method documents | https://brain-map.org/consortia/sea-ad/our-resources | documentation | pdf/html | small | manual | internal | N/A | provenance and method constraints | low | low | high | planned | Use for provenance, not predictors. | 0 | False | important after core linkage/MRI |
| sea_ad_donor_metadata | SEA-AD donor metadata | https://brain-map.org/consortia/sea-ad/our-data | donor_metadata | csv/metadata table | small | manual | internal | Donor ID | safe donor covariates and linkage keys | low | low | high | planned | Safest first source with strict forbidden predictor filter. | 1 | True | core linkage and safe covariates |
| sea_ad_mri_volumetrics | Postmortem MRI volumetrics | https://brain-map.org/consortia/sea-ad/our-data | MRI | csv/table or supplement | medium | manual | internal | Donor ID | regional volumes / anatomy context | low | low_to_medium | high | planned | Highest priority benchmark feature after donor metadata. | 2 | True | safe anatomy/volume signal with lower direct target leakage risk |
| cell_id_conversion_tables | Cell ID conversion / donor linkage tables | https://brain-map.org/consortia/sea-ad/our-resources | linkage | csv/table | small | manual | internal | cell_id; donor_id | linkage only | low | low | high | planned | Required for safe aggregation and provenance tracking. | 3 | False | required for donor-safe aggregation |
| cellxgene_snrna_metadata | Processed snRNA-seq / CELLxGENE donor-cell metadata | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | snRNA_metadata | h5ad/cell metadata | large | manual_or_existing_wsl | internal | donor_id / Donor ID | cell type/subclass/state summaries | medium | medium | high | planned | Build donor-level summaries; avoid disease-state labels as predictors. | 4 | False | important after core linkage/MRI |
| donor_celltype_composition | Donor-level cell-type/subclass composition summaries | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | composition | derived csv | small | derived_after_manual_acquisition | internal | Donor ID | broad cell-type fractions | medium | medium | medium | derived_needed | Tier2 caution features requiring proxy audit. | 5 | False | important after core linkage/MRI |
| celltype_module_state_summaries | Cell-type-specific module/state summaries | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | state_summary | derived csv | medium | derived_after_manual_acquisition | internal | Donor ID; cell_type | module/state summaries by cell type | medium | medium_to_high | medium | derived_needed | Must exclude pseudo-pathology/SEAAD target-proxy state labels. | 6 | False | important after core linkage/MRI |
| spatial_transcriptomics_neighborhoods | Spatial transcriptomics neighborhood summaries | https://brain-map.org/consortia/sea-ad/our-data | spatial | spatial tables / h5ad / coordinates | large | manual | internal | Donor ID; section_id; spot/cell_id | local neighborhood context | medium | medium | high | planned | Compute neighborhoods without target labels. | 7 | False | important after core linkage/MRI |
| snatac_regulatory_modules | snATAC / regulatory module summaries | https://brain-map.org/consortia/sea-ad/our-data | snATAC | fragment/peak/module tables | large | manual | internal | Donor ID; cell_id | regulatory module context | medium | medium | medium | planned | Potential Tier2 feature; requires modality-specific QC. | 8 | False | important after core linkage/MRI |
| microglia_multiregion_states | Microglia-enriched multiregion state summaries | https://brain-map.org/consortia/sea-ad/our-data | microglia_state | metadata/expression tables | medium | manual | internal | Donor ID; region | microglia state by region | medium | medium_to_high | medium | planned | Avoid SEAAD/disease burden state labels as direct predictors. | 9 | False | important after core linkage/MRI |
| he_lfb_non_target_morphology | H&E-LFB or non-target image morphology features | https://brain-map.org/consortia/sea-ad/our-resources | image_morphology | image-derived feature table | medium_to_large | manual | internal | Donor ID; slide_id; section_id | non-target morphology / tissue architecture | medium | medium | medium | planned_later | Use non-target stains first; avoid same-stain same-target leakage. | 10 | False | important after core linkage/MRI |

## Feature safety tiers

| risk_tier | tier_name | examples | allowed_for_lock_candidate | comparator_only | forbidden | recommended_use |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | existing internal module/latent features | Stage 27C/39E module PCA or train-fold-safe equivalents | True | False | False | reference/baseline |
| 1 | safe donor metadata and MRI/anatomy | age, sex, PMI, RIN, APOE, MRI volumetrics, broad region/anatomy, technical covariates | True | False | False | first benchmark candidate tier |
| 2 | target-adjacent biology/context | cell-type composition, spatial neighborhoods, state summaries, snATAC modules, H&E-LFB morphology | False | False | False | caution candidate after proxy audit |
| 3 | high-risk proxy features | section/pathology-adjacent summaries, disease-burden descriptors, highly target-correlated features | False | True | False | comparator-only |
| 4 | forbidden predictors | quantitative target summaries, Luminex Aβ/tau, Braak/CERAD/Thal/ADNC, same-stain same-target features, HALO target quantifications, pseudo-labels | False | False | True | do not use for benchmark predictors |

## Donor linkage requirements

| resource_id | required_linkage_keys | minimum_required_fields | aggregation_unit | linkage_risk | stage41b_requirement |
| --- | --- | --- | --- | --- | --- |
| sea_ad_donor_metadata | Donor ID | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |
| sea_ad_mri_volumetrics | Donor ID | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |
| cellxgene_snrna_metadata | donor_id / Donor ID | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |
| donor_celltype_composition | Donor ID | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |
| celltype_module_state_summaries | Donor ID; cell_type | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |
| spatial_transcriptomics_neighborhoods | Donor ID; section_id; spot/cell_id | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | high | Must link to locked donor IDs without using target values. |
| snatac_regulatory_modules | Donor ID; cell_id | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | high | Must link to locked donor IDs without using target values. |
| microglia_multiregion_states | Donor ID; region | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |
| he_lfb_non_target_morphology | Donor ID; slide_id; section_id | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |
| cell_id_conversion_tables | cell_id; donor_id | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | high | Must link to locked donor IDs without using target values. |
| sea_ad_whitepapers_methods | N/A | donor_id; source_file; provenance; feature_generation_date | donor or donor-region/section before donor-held-out folds | medium | Must link to locked donor IDs without using target values. |

## Expected feature matrix schemas

| feature_matrix_name | modality | unit_of_observation | required_rows | required_columns | donor_id_column | region_column | feature_columns | target_columns_allowed | target_columns_forbidden | preprocessing_required | train_fold_only_required | expected_stage41b_output |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage41b_donor_metadata_mri_matrix | metadata_mri | donor | one row per locked SEA-AD donor | donor_id + safe metadata/MRI features | donor_id | optional region if region-specific MRI | age/sex/PMI/RIN/APOE/MRI volumes | none as predictors | AT8/6e10/GFAP/Iba1/NeuN forbidden as feature columns | impute/scale inside train folds | True | results/tables/stage41b_safe_metadata_mri_feature_matrix_v1.csv |
| stage41b_celltype_composition_matrix | snRNA_composition | donor or donor-region | one row per donor or donor-region | donor_id + broad cell-type fractions | donor_id | optional region | broad cell type/subclass fractions | none as predictors | disease-state labels and target pathology fields | aggregate without targets; train-fold scaling | True | results/tables/stage41b_celltype_composition_feature_matrix_v1.csv |
| stage41b_spatial_neighborhood_matrix | spatial | donor/section/region | donor-linked spatial summaries | donor_id + section_id + neighborhood features | donor_id | region/section | neighborhood densities/distances not derived from targets | none as predictors | target-derived neighborhoods | compute before target modeling; fold-safe aggregation | True | results/tables/stage41b_spatial_neighborhood_feature_matrix_v1.csv |
| stage41b_non_target_image_morphology_matrix | image_morphology | donor/slide/section | donor-linked non-target morphology summaries | donor_id + slide/section IDs + morphology features | donor_id | section/region | H&E-LFB/non-target morphology descriptors | none as predictors | same-stain same-target features; HALO target quantifications | tile QC; aggregate inside train folds where needed | True | results/tables/stage41b_non_target_image_morphology_feature_matrix_v1.csv |

## Forbidden predictors

| forbidden_feature | feature_source | reason_forbidden | affected_target | allowed_alternative_use |
| --- | --- | --- | --- | --- |
| AT8 stain features as AT8 predictors | target image stain | same-stain same-target leakage/proxy risk | AT8 | use only as outcome or cross-target sensitivity with explicit audit |
| 6E10 stain features as A_beta predictors | target image stain | same-stain same-target leakage/proxy risk | 6e10/A_beta | use only as outcome or cross-target sensitivity with explicit audit |
| GFAP stain features as GFAP predictors | target image stain | same-stain same-target leakage/proxy risk | GFAP | use non-target morphology features instead |
| IBA1 stain features as Iba1 predictors | target image stain | same-stain same-target leakage/proxy risk | Iba1 | use non-target morphology or safe microenvironment features |
| NeuN stain features as NeuN predictors | target image stain | same-stain same-target leakage/proxy risk | NeuN | use non-target morphology or safe anatomy features |
| HALO target quantifications | HALO/pathology quantification | direct or near-direct target leakage | all pathology targets | outcome/label audit only |
| Luminex A_beta/tau predictors | biochemical pathology | direct disease/pathology burden proxy | A_beta/tau-related targets | support-only/manual review, not benchmark predictor |
| Braak/CERAD/Thal/ADNC predictors | neuropathology staging | disease burden proxy | all pathology targets | stratification/reporting only |
| quantitative neuropathology summaries as predictors | pathology metadata | target-adjacent leakage | all pathology targets | outcome/support context only |
| pseudo-labels derived from held-out targets | derived labels | fold leakage and target leakage | all targets | forbidden |

## Whitepaper / provenance inventory

| provenance_id | document_name | source_url | document_type | needed_for | review_status |
| --- | --- | --- | --- | --- | --- |
| sea_ad_methods_overview | SEA-AD methods / resources overview | https://brain-map.org/consortia/sea-ad/our-resources | documentation | provenance and modality definitions | planned_manual_review |
| donor_metadata_dictionary | Donor metadata data dictionary | https://brain-map.org/consortia/sea-ad/our-resources | documentation | field definitions and linkage keys | planned_manual_review |
| mri_processing_methods | Postmortem MRI processing methods | https://brain-map.org/consortia/sea-ad/our-resources | documentation | MRI feature provenance and scaling | planned_manual_review |
| snrna_cellxgene_schema | CELLxGENE collection schema and cell metadata | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | documentation | cell/donor metadata fields and donor linkage | planned_manual_review |
| image_processing_methods | Image acquisition/processing methods | https://brain-map.org/consortia/sea-ad/our-resources | documentation | stain/source provenance and same-target leakage rules | planned_manual_review |

## Next build steps

| next_stage | required_inputs | expected_outputs | manual_work_required | priority | estimated_complexity | recommended_order |
| --- | --- | --- | --- | --- | --- | --- |
| Stage41B_metadata_mri_matrix_build | donor metadata; MRI volumetrics; donor linkage table | safe metadata/MRI feature matrix + audit | manual downloads/checksums | high | medium | 1 |
| Stage41C_metadata_mri_benchmark | Stage41B safe metadata/MRI matrix | donor-held-out benchmark against Stage27C/39E | none after matrix exists | high | medium | 2 |
| Stage41D_cellxgene_composition_build | CELLxGENE/snRNA donor-cell metadata; linkage table | broad donor cell-type/state summaries | manual download/schema mapping | medium | high | 3 |
| Stage41E_celltype_state_proxy_audit | Stage41D summaries | Tier2 proxy audit and benchmark-readiness decision | manual review of state labels | medium | medium | 4 |
| Stage41F_spatial_summary_build | spatial transcriptomics/coordinate summaries | donor-linked spatial neighborhood features | manual acquisition and linkage | medium | high | 5 |
| Stage41G_snatac_regulatory_summary_build | snATAC/regulatory module summaries | donor-linked regulatory features | manual acquisition/QC | low | high | 6 |
| Stage41H_non_target_image_morphology_build | H&E-LFB/non-target image morphology features | donor/section-linked morphology feature matrix | image feature extraction/provenance | low | high | 7 |

## Claim boundary audit

| audit_item | pass | evidence |
| --- | --- | --- |
| no_model_training | True | Stage 41A is planning-only and writes safety boundaries. |
| no_feature_fabrication | True | Stage 41A is planning-only and writes safety boundaries. |
| no_downloads_performed | True | Stage 41A is planning-only and writes safety boundaries. |
| no_raw_data_added_to_git | True | Stage 41A is planning-only and writes safety boundaries. |
| no_external_model_selection | True | Stage 41A is planning-only and writes safety boundaries. |
| target_predictors_forbidden | True | Stage 41A is planning-only and writes safety boundaries. |
| same_stain_same_target_predictors_forbidden | True | Stage 41A is planning-only and writes safety boundaries. |
| halo_target_quantification_predictors_forbidden | True | Stage 41A is planning-only and writes safety boundaries. |
| braak_cerad_thal_adnc_predictors_forbidden | True | Stage 41A is planning-only and writes safety boundaries. |
| frozen_candidates_preserved | True | Stage 41A is planning-only and writes safety boundaries. |
| no_clean_external_validation_claim | True | Stage 41A is planning-only and writes safety boundaries. |
| no_causal_claim | True | Stage 41A is planning-only and writes safety boundaries. |
| no_therapeutic_claim | True | Stage 41A is planning-only and writes safety boundaries. |
| no_gene_ablation_claim | True | Stage 41A is planning-only and writes safety boundaries. |
| no_disease_modifying_claim | True | Stage 41A is planning-only and writes safety boundaries. |
| safety_audit_pass | True | all safety checks passed |
