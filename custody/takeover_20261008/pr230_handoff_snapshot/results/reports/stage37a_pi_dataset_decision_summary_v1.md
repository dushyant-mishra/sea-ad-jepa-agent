# Stage 37A PI dataset decision summary v1

## Short answer

No already identified resource is currently approved as clean validation under Stage 36E rules.

Resources can still be useful as stress-test support, projection/signature support, robustness-only support, or manual-review candidates, but those roles are not clean validation.

## Candidate datasets/resources

| dataset_id | dataset_name | candidate_role | primary_reason |
| --- | --- | --- | --- |
| GSE138852 | GSE138852 / Grubman-Leng | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| GSE174367 | GSE174367 / Morabito | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| HBCC | HBCC | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| HBCA | HBCA / Human Brain Cell Atlas | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| SEA_AD_PUBLIC_SPATIAL_PATHOLOGY | SEA-AD public spatial/pathology resources | excluded_or_contaminated | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| PUBLIC_CELLXGENE_MICROGLIA | Public CELLxGENE microglia datasets | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| LU_2026_SIGNATURES | Lu et al. 2026 signatures/supplementary tables | projection_or_signature_support | Resource appears suited to mechanism/signature concordance, not full pathology validation unless required frozen readouts are verified. |
| PIG_WGCNA_RESOURCES | PIG / WGCNA resources | projection_or_signature_support | Resource appears suited to mechanism/signature concordance, not full pathology validation unless required frozen readouts are verified. |
| SEA-AD_internal | SEA-AD Microglia-PVM internal benchmark | excluded_or_contaminated | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| GSE157827 | Candidate public external brain snRNA/scRNA dataset | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| GSE147528 | Candidate public external brain snRNA/scRNA dataset | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| GSE203206 | Bulk donor/sample-level external stress test | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| GSE98969 | Mouse DAM/microglia auxiliary candidate | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| GSE181279 | Peripheral immune plausibility/auxiliary dataset | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| GSE127893 | Mouse subseries review required | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| 37a17b78-4864-4a42-b67b-31c00962795a | MSSM_Cohort | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| 5e57cd50-8e42-42d6-940d-5c1660d06864 | RADC_Cohort | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| cff99df2-4904-44f7-9173-ff837f95606e | all cells | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| 203025fe-fa99-4d57-81da-458ed8f0c334 | Brain vascular single-cell multi-omics disease-risk snRNA-seq | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| 0a2d7e87-c3c0-4ed2-86df-ae18811fcc16 | Full Dataset | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| fe2eecbc-977a-4aec-9196-f89c3281d11c | Microglia | requires_manual_review | Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices. |
| b165f033-9dec-468a-9248-802fc6902a74 | All non-neuronal cells | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| 5c97eeeb-7e52-44b3-b010-b832b1f5424c | HBCC_Cohort | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| 4442d412-91cb-4261-acca-8adf5fa04c11 | Aging_Cohort | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| Olah_live_microglia | Olah live human microglia | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| ac0c6561-7a48-4185-af6f-af799f699172 | All Cells - snRNA-seq | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| SEA_AD_CELLXGENE_DLPFC | Whole Taxonomy - DLPFC | excluded_or_contaminated | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| SEA_AD_CELLXGENE_MTG | Whole Taxonomy - MTG | excluded_or_contaminated | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| Tabula_Sapiens_immune | Tabula Sapiens - Immune | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| Tabula_Sapiens_myeloid | Tabula Sapiens myeloid/immune cells | projection_or_signature_support | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| mouse_isocortex_hippocampus | Mouse isocortex and hippocampal formation taxonomy | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| mouse_brain_aging_atlas | BrainAgingSpatialAtlas_snRNAseq | excluded_or_contaminated | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |

## Recommended next action

| recommended_next_stage | recommended_action | rationale |
| --- | --- | --- |
| Stage37B_manual_dataset_approval | Do not run validation yet; perform manual dataset approval and/or acquire a clean validation dataset with frozen readouts. | Stage 37A found no dataset/resource that can honestly be called clean validation under frozen Stage 36E rules. |

## Why pretraining/stress-test resources are not clean validation

A clean validation dataset has to be independent of training, pretraining, model selection, candidate selection, feature selection, and threshold tuning. If a resource helped build, tune, rescue, interpret, or stress-test the system, it can still be informative, but it cannot be used as the primary clean validation set without a new independence audit.

## Manual review required

GSE138852;GSE174367;PUBLIC_CELLXGENE_MICROGLIA;LU_2026_SIGNATURES;PIG_WGCNA_RESOURCES;GSE157827;GSE147528;GSE203206;GSE181279;37a17b78-4864-4a42-b67b-31c00962795a;5e57cd50-8e42-42d6-940d-5c1660d06864;cff99df2-4904-44f7-9173-ff837f95606e;203025fe-fa99-4d57-81da-458ed8f0c334;0a2d7e87-c3c0-4ed2-86df-ae18811fcc16;fe2eecbc-977a-4aec-9196-f89c3281d11c;Olah_live_microglia;ac0c6561-7a48-4185-af6f-af799f699172;Tabula_Sapiens_immune;Tabula_Sapiens_myeloid

## Not clean validation under current evidence

GSE138852;GSE174367;HBCC;HBCA;SEA_AD_PUBLIC_SPATIAL_PATHOLOGY;PUBLIC_CELLXGENE_MICROGLIA;LU_2026_SIGNATURES;PIG_WGCNA_RESOURCES;SEA-AD_internal;GSE157827;GSE147528;GSE203206;GSE98969;GSE181279;GSE127893;37a17b78-4864-4a42-b67b-31c00962795a;5e57cd50-8e42-42d6-940d-5c1660d06864;cff99df2-4904-44f7-9173-ff837f95606e;203025fe-fa99-4d57-81da-458ed8f0c334;0a2d7e87-c3c0-4ed2-86df-ae18811fcc16;fe2eecbc-977a-4aec-9196-f89c3281d11c;b165f033-9dec-468a-9248-802fc6902a74;5c97eeeb-7e52-44b3-b010-b832b1f5424c;4442d412-91cb-4261-acca-8adf5fa04c11;Olah_live_microglia;ac0c6561-7a48-4185-af6f-af799f699172;SEA_AD_CELLXGENE_DLPFC;SEA_AD_CELLXGENE_MTG;Tabula_Sapiens_immune;Tabula_Sapiens_myeloid;mouse_isocortex_hippocampus;mouse_brain_aging_atlas

## Safe lab-meeting language

validation eligibility audit; candidate validation resource; stress-test support; projection/signature support; requires manual review; not clean validation; eligible for proposed next validation only if independence is confirmed

Avoid: validated; external validation completed; clean validation proven; causal regulator; therapeutic target; disease-modifying target

## Pass/fail

| stage37a_run_pass | no_validation_run | no_data_download | no_external_validation_claim |
| --- | --- | --- | --- |
| True | True | True | True |