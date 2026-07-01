# Stage 37B-rev1 dataset claim reclassification report v1

## Why revision was needed

Stage 37A/37B correctly kept the clean-validation gate closed, but the prior Stage 37B wording could make missing metadata look like dataset rejection.

## Corrected principle

Missing metadata is not rejection. A resource is disqualified from clean validation only when explicit disqualifying evidence exists.

## Revised dataset claim-level summary

| revised_claim_level | n_datasets |
| --- | --- |
| conditional_clean_validation_candidate | 4 |
| external_biological_support_candidate | 2 |
| known_disqualified_from_clean_validation | 9 |
| manual_metadata_review_required | 7 |
| projection_or_signature_support_candidate | 8 |
| robustness_only | 4 |

## Conditional validation candidates

| dataset_id | dataset_name | why_candidate_is_reasonable |
| --- | --- | --- |
| GSE174367 | GSE174367 / Morabito | Morabito resource remains reasonable to reuse, but local v2 artifacts require contamination/independence review before any clean-validation claim. |
| GSE157827 | Candidate public external brain snRNA/scRNA dataset | Scientifically plausible validation/acquisition candidate; missing evidence is not rejection. |
| GSE147528 | Candidate public external brain snRNA/scRNA dataset | Scientifically plausible validation/acquisition candidate; missing evidence is not rejection. |
| ROSMAP_AMP_AD | ROSMAP / AMP-AD | Scientifically plausible validation/acquisition candidate; missing evidence is not rejection. |

## External support candidates

| dataset_id | dataset_name | support_type | allowed_analysis_type | priority |
| --- | --- | --- | --- | --- |
| GSE138852 | GSE138852 / Grubman-Leng | external_biological_support_candidate | directional smoke-test; external biological support; projection/signature support | medium |
| HBCC | HBCC | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | medium |
| HBCA | HBCA / Human Brain Cell Atlas | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | medium |
| PUBLIC_CELLXGENE_MICROGLIA | Public CELLxGENE microglia datasets | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| LU_2026_SIGNATURES | Lu et al. 2026 signatures/supplementary tables | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| PIG_WGCNA_RESOURCES | PIG / WGCNA resources | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| GSE181279 | Peripheral immune plausibility/auxiliary dataset | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| b165f033-9dec-468a-9248-802fc6902a74 | All non-neuronal cells | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | low |
| 5c97eeeb-7e52-44b3-b010-b832b1f5424c | HBCC_Cohort | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | low |
| Olah_live_microglia | Olah live human microglia | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| ac0c6561-7a48-4185-af6f-af799f699172 | All Cells - snRNA-seq | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| Tabula_Sapiens_immune | Tabula Sapiens - Immune | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| Tabula_Sapiens_myeloid | Tabula Sapiens myeloid/immune cells | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| GSE160936 | GSE160936 | external_biological_support_candidate | external biological support and manual metadata review for possible conditional validation | high |

## Known disqualified datasets with explicit reasons only

| dataset_id | dataset_name | disqualification_reason | explicit_evidence | still_useful_for | claim_boundary |
| --- | --- | --- | --- | --- | --- |
| HBCC | HBCC | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| HBCA | HBCA / Human Brain Cell Atlas | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| SEA_AD_PUBLIC_SPATIAL_PATHOLOGY | SEA-AD public spatial/pathology resources | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_training_or_source_domain;sea_ad_source_domain_not_clean_external;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| SEA-AD_internal | SEA-AD Microglia-PVM internal benchmark | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_training_or_source_domain;sea_ad_source_domain_not_clean_external;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| GSE98969 | Mouse DAM/microglia auxiliary candidate | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| GSE127893 | Mouse subseries review required | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| b165f033-9dec-468a-9248-802fc6902a74 | All non-neuronal cells | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| 5c97eeeb-7e52-44b3-b010-b832b1f5424c | HBCC_Cohort | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| 4442d412-91cb-4261-acca-8adf5fa04c11 | Aging_Cohort | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| SEA_AD_CELLXGENE_DLPFC | Whole Taxonomy - DLPFC | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_training_or_source_domain;sea_ad_source_domain_not_clean_external;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| SEA_AD_CELLXGENE_MTG | Whole Taxonomy - MTG | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_training_or_source_domain;sea_ad_source_domain_not_clean_external;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| mouse_isocortex_hippocampus | Mouse isocortex and hippocampal formation taxonomy | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |
| mouse_brain_aging_atlas | BrainAgingSpatialAtlas_snRNAseq | Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role. | used_for_pretraining_or_rescue_modeling;approved_or_used_for_pretraining;explicit_contamination_audit_disqualification | robustness/provenance/context only, with explicit non-clean-validation label | not clean validation; may be scientifically useful only at bounded support level |

## Stage 37C gate

| stage37c_clean_external_validation_allowed | reason | approved_datasets | conditional_candidates | recommended_next_stage | claim_boundary |
| --- | --- | --- | --- | --- | --- |
| False | No dataset has explicit complete approval evidence in the repo. |  | GSE174367;GSE157827;GSE147528;ROSMAP_AMP_AD | Stage37C_external_support_first_pass_or_manual_metadata_review | Stage 37B-rev1 reclassifies claim levels only; it does not complete validation. |

## What can be reused now

Resources can be reused only at their bounded claim level: conditional/manual review, external biological support, projection/signature support, stress-test support, or robustness-only support.

## What cannot be claimed

Avoid: validated; clean validation proven; external validation completed; causal regulator; therapeutic target; disease-modifying target.

## Recommended next stage

Stage37C_external_support_first_pass_or_manual_metadata_review

## Pass/fail summary

| stage37b_rev1_run | stage37a_inputs_found | stage37b_inputs_found | stage36e_inputs_found | claim_level_matrix_written | reclassification_summary_written | conditional_candidates_written | external_support_candidates_written | known_disqualified_table_written | manual_metadata_review_queue_written | stage37c_gate_written | no_new_modeling_run | no_validation_run | no_data_download | no_web_scraping | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | missing_metadata_not_treated_as_rejection | known_disqualification_requires_explicit_evidence | safety_audit_pass | stage37b_rev1_run_pass | stage37c_clean_external_validation_allowed | controlled_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | False | Stage 37B-rev1 corrected claim-level classification; missing metadata is not rejection, and no validation was run. |