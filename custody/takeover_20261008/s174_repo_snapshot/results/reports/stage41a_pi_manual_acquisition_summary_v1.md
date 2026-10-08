# Stage 41A PI manual acquisition summary

## Short answer

Acquire SEA-AD donor metadata and postmortem MRI volumetrics first. The safest first benchmark source is donor-linked MRI + safe metadata. Then acquire donor/cell linkage and CELLxGENE/snRNA metadata to build broad composition/state summaries with Tier2 proxy audits.

## Highest priority resources

| resource_id | resource_name | source_url | modality | expected_file_type | expected_size_class | access_type | internal_or_external | expected_donor_linkage_key | expected_feature_value | leakage_risk | proxy_risk | priority | acquisition_status | notes | recommended_order | safest_first_benchmark_source | why_priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sea_ad_whitepapers_methods | SEA-AD white papers and method documents | https://brain-map.org/consortia/sea-ad/our-resources | documentation | pdf/html | small | manual | internal | N/A | provenance and method constraints | low | low | high | planned | Use for provenance, not predictors. | 0 | False | important after core linkage/MRI |
| sea_ad_donor_metadata | SEA-AD donor metadata | https://brain-map.org/consortia/sea-ad/our-data | donor_metadata | csv/metadata table | small | manual | internal | Donor ID | safe donor covariates and linkage keys | low | low | high | planned | Safest first source with strict forbidden predictor filter. | 1 | True | core linkage and safe covariates |
| sea_ad_mri_volumetrics | Postmortem MRI volumetrics | https://brain-map.org/consortia/sea-ad/our-data | MRI | csv/table or supplement | medium | manual | internal | Donor ID | regional volumes / anatomy context | low | low_to_medium | high | planned | Highest priority benchmark feature after donor metadata. | 2 | True | safe anatomy/volume signal with lower direct target leakage risk |
| cell_id_conversion_tables | Cell ID conversion / donor linkage tables | https://brain-map.org/consortia/sea-ad/our-resources | linkage | csv/table | small | manual | internal | cell_id; donor_id | linkage only | low | low | high | planned | Required for safe aggregation and provenance tracking. | 3 | False | required for donor-safe aggregation |
| cellxgene_snrna_metadata | Processed snRNA-seq / CELLxGENE donor-cell metadata | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | snRNA_metadata | h5ad/cell metadata | large | manual_or_existing_wsl | internal | donor_id / Donor ID | cell type/subclass/state summaries | medium | medium | high | planned | Build donor-level summaries; avoid disease-state labels as predictors. | 4 | False | important after core linkage/MRI |
| donor_celltype_composition | Donor-level cell-type/subclass composition summaries | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | composition | derived csv | small | derived_after_manual_acquisition | internal | Donor ID | broad cell-type fractions | medium | medium | medium | derived_needed | Tier2 caution features requiring proxy audit. | 5 | False | important after core linkage/MRI |

## What not to use

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

## Next executable stage

| next_stage | required_inputs | expected_outputs | manual_work_required | priority | estimated_complexity | recommended_order |
| --- | --- | --- | --- | --- | --- | --- |
| Stage41B_metadata_mri_matrix_build | donor metadata; MRI volumetrics; donor linkage table | safe metadata/MRI feature matrix + audit | manual downloads/checksums | high | medium | 1 |
| Stage41C_metadata_mri_benchmark | Stage41B safe metadata/MRI matrix | donor-held-out benchmark against Stage27C/39E | none after matrix exists | high | medium | 2 |
| Stage41D_cellxgene_composition_build | CELLxGENE/snRNA donor-cell metadata; linkage table | broad donor cell-type/state summaries | manual download/schema mapping | medium | high | 3 |

## Safe interpretation

Stage 41A is planning-only. It performs no model training, no downloads, and no validation. It does not support causal, therapeutic, gene-ablation, disease-modifying, or clean external-validation claims.
