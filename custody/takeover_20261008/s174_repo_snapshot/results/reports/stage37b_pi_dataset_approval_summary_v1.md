# Stage 37B PI dataset approval summary v1

## Short answer

Stage 37C clean validation allowed now: `False`.

No dataset should be treated as clean validation until the PI/manual approval gate passes with documented metadata and independence evidence.

## Datasets/resources needing manual review

| review_id | dataset_id | dataset_name | review_priority | recommended_decision_before_stage37c |
| --- | --- | --- | --- | --- |
| MR001 | LU_2026_SIGNATURES | Lu et al. 2026 signatures/supplementary tables | medium | PI_REVIEW_PENDING |
| MR002 | PIG_WGCNA_RESOURCES | PIG / WGCNA resources | medium | PI_REVIEW_PENDING |
| MR003 | GSE157827 | Candidate public external brain snRNA/scRNA dataset | high | PI_REVIEW_PENDING |
| MR004 | GSE147528 | Candidate public external brain snRNA/scRNA dataset | high | PI_REVIEW_PENDING |
| MR005 | GSE203206 | Bulk donor/sample-level external stress test | high | PI_REVIEW_PENDING |
| MR006 | 37a17b78-4864-4a42-b67b-31c00962795a | MSSM_Cohort | high | PI_REVIEW_PENDING |
| MR007 | 5e57cd50-8e42-42d6-940d-5c1660d06864 | RADC_Cohort | high | PI_REVIEW_PENDING |
| MR008 | cff99df2-4904-44f7-9173-ff837f95606e | all cells | high | PI_REVIEW_PENDING |
| MR009 | 203025fe-fa99-4d57-81da-458ed8f0c334 | Brain vascular single-cell multi-omics disease-risk snRNA-seq | high | PI_REVIEW_PENDING |
| MR010 | 0a2d7e87-c3c0-4ed2-86df-ae18811fcc16 | Full Dataset | high | PI_REVIEW_PENDING |
| MR011 | fe2eecbc-977a-4aec-9196-f89c3281d11c | Microglia | high | PI_REVIEW_PENDING |

## Restricted to stress-test/projection/signature support

| dataset_id | dataset_name | stage37b_decision | stage37b_allowed_use |
| --- | --- | --- | --- |
| LU_2026_SIGNATURES | Lu et al. 2026 signatures/supplementary tables | allow_projection_or_signature_support_only | projection/signature or robustness support after manual boundaries are confirmed |
| PIG_WGCNA_RESOURCES | PIG / WGCNA resources | allow_projection_or_signature_support_only | projection/signature or robustness support after manual boundaries are confirmed |

## Rejected for clean validation

| dataset_id | dataset_name | reason_for_decision |
| --- | --- | --- |
| GSE138852 | GSE138852 / Grubman-Leng | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| GSE174367 | GSE174367 / Morabito | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| HBCC | HBCC | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| HBCA | HBCA / Human Brain Cell Atlas | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| SEA_AD_PUBLIC_SPATIAL_PATHOLOGY | SEA-AD public spatial/pathology resources | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| PUBLIC_CELLXGENE_MICROGLIA | Public CELLxGENE microglia datasets | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| SEA-AD_internal | SEA-AD Microglia-PVM internal benchmark | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| GSE98969 | Mouse DAM/microglia auxiliary candidate | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| GSE181279 | Peripheral immune plausibility/auxiliary dataset | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| GSE127893 | Mouse subseries review required | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| b165f033-9dec-468a-9248-802fc6902a74 | All non-neuronal cells | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| 5c97eeeb-7e52-44b3-b010-b832b1f5424c | HBCC_Cohort | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| 4442d412-91cb-4261-acca-8adf5fa04c11 | Aging_Cohort | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| Olah_live_microglia | Olah live human microglia | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| ac0c6561-7a48-4185-af6f-af799f699172 | All Cells - snRNA-seq | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| SEA_AD_CELLXGENE_DLPFC | Whole Taxonomy - DLPFC | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| SEA_AD_CELLXGENE_MTG | Whole Taxonomy - MTG | SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow. |
| Tabula_Sapiens_immune | Tabula Sapiens - Immune | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| Tabula_Sapiens_myeloid | Tabula Sapiens myeloid/immune cells | Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven. |
| mouse_isocortex_hippocampus | Mouse isocortex and hippocampal formation taxonomy | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |
| mouse_brain_aging_atlas | BrainAgingSpatialAtlas_snRNAseq | Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited. |

## Exact decision needed from PI

Decide which manual-review resources should receive metadata acquisition/review, and whether any should be advanced later to Stage 37C only after all clean-validation gates pass.

## Recommended next action

Run manual metadata approval/data acquisition, not validation.

## Safe lab-meeting language

manual dataset approval; validation-readiness dossier; candidate validation resource; requires manual metadata confirmation; not yet approved for clean validation; approved only for stress-test support; approved only for projection/signature support; Stage 37C clean validation not allowed unless gate passes

Avoid: validated; external validation completed; clean validation proven; causal regulator; therapeutic target; disease-modifying target; approved clean validation dataset

## Pass/fail

| stage37b_run_pass | stage37c_clean_external_validation_allowed | no_validation_run | no_external_validation_claim |
| --- | --- | --- | --- |
| True | False | True | True |