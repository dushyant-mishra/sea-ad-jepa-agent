# Stage 37C-F multi-dataset external support report v1

## Purpose

Stage 37C-F checks local readiness and bounded external support for frozen Stage 36E mechanisms/candidates across prioritized human AD transcriptomic datasets.

## Why these datasets were selected

GSE160936 targets pTau/glial support, GSE125050 pathology-confirmed AD cell-type support, GSE157827 broad AD/control support, and GSE138852 entorhinal cortex smoke-test support. GSE174367 is optional secondary stress-test/projection support because local v2 artifacts already exist.

## Readiness summary

| dataset_id | stage_label | dataset_name | local_data_found | metadata_found | expression_matrix_found | celltype_annotations_found | disease_or_pathology_metadata_found | tau_or_ptau_metadata_found | amyloid_or_abeta_metadata_found | donor_or_sample_metadata_found | analysis_can_run | reason_if_not_ready | safe_claim_level | recommended_use | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse160936 | Stage37C | GSE160936 pTau-linked glial support | False | False | False | False | False | False | False | False | False | no local files found in declared search roots | external_biological_support | pTau-linked glial external support / conditional validation | 0 local paths found; gene_source=no_gene_universe_extracted; primary_dataset=True |
| gse125050 | Stage37D | GSE125050 pathology-confirmed AD cell-type support | False | False | False | False | False | False | False | False | False | no local files found in declared search roots | conditional_validation_support_pending_manual_approval | pathology-confirmed AD cell-type validation/support | 0 local paths found; gene_source=no_gene_universe_extracted; primary_dataset=True |
| gse157827 | Stage37E | GSE157827 broad AD/control snRNA-seq support | True | True | True | False | True | False | False | False | False | gene universe could not be extracted | conditional_validation_support_pending_manual_approval | broad AD/control single-nucleus external mechanism support | 2 local paths found; gene_source=no_gene_universe_extracted; primary_dataset=True |
| gse138852 | Stage37F | GSE138852 Grubman-Leng entorhinal cortex smoke test | True | True | True | True | True | False | False | True | True |  | external_biological_support | smaller entorhinal cortex directional smoke test | 5 local paths found; gene_source=gene_column_from_data/external/grubman_gse138852/GSE138852_counts.csv.gz; primary_dataset=True |
| gse174367 | optional_secondary | GSE174367 Morabito optional secondary stress-test | True | True | True | True | True | False | False | True | False | gene universe could not be extracted | stress_test_projection_support_only | optional secondary stress-test/projection support only | 5 local paths found; gene_source=no_gene_universe_extracted; primary_dataset=False |

## Dataset-specific support summary

| dataset_id | mechanism_id | support_tier | gene_coverage_fraction | microglia_specificity_score | celltype_specificity_tier |
| --- | --- | --- | --- | --- | --- |
| gse160936 | M1 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse160936 | M2 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse160936 | M3 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse160936 | M4 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse125050 | M1 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse125050 | M2 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse125050 | M3 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse125050 | M4 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse157827 | M1 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse157827 | M2 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse157827 | M3 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse157827 | M4 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse138852 | M1 | weak_or_incomplete_external_support | 0.8 | 0.0 | celltype_not_testable |
| gse138852 | M2 | weak_or_incomplete_external_support | 0.4 | 0.0 | celltype_not_testable |
| gse138852 | M3 | weak_or_incomplete_external_support | 0.6 | 0.0 | celltype_not_testable |
| gse138852 | M4 | weak_or_incomplete_external_support | 0.75 | 0.0 | celltype_not_testable |
| gse174367 | M1 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse174367 | M2 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse174367 | M3 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |
| gse174367 | M4 | not_testable_due_to_missing_data | 0.0 | 0.0 | celltype_not_testable |

## Cross-dataset concordance

| mechanism_id | mechanism_name | target | candidate_genes | n_datasets_testable | n_datasets_with_direction_match | n_datasets_with_moderate_or_strong_support | datasets_supporting | datasets_not_supporting | datasets_not_testable | concordance_tier | interpretation | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | multi_target | CTSB;CTSD;LAMP2;LAPTM5;NPC2;CTSB;LAMP2;LAPTM5;NPC2 | 1 | 0 | 0 | gse138852 |  | gse160936;gse125050;gse157827;gse174367 | single_dataset_support | Gene coverage/readiness support only; no clean validation or causal claim | external support / conditional support only; frozen Stage 36E candidates require further validation |
| M2 | Glial activation / disease-associated microglia-astrocyte state | multi_target | APOE;CST7;CTSD;LGALS3;TREM2;APOE;LGALS3 | 1 | 0 | 0 | gse138852 |  | gse160936;gse125050;gse157827;gse174367 | single_dataset_support | Gene coverage/readiness support only; no clean validation or causal claim | external support / conditional support only; frozen Stage 36E candidates require further validation |
| M3 | Oxidative stress / antioxidant response | multi_target | GPX4;HMOX1;NQO1;SOD1;SOD2;GPX4;SOD1;SOD2 | 1 | 0 | 0 | gse138852 |  | gse160936;gse125050;gse157827;gse174367 | single_dataset_support | Gene coverage/readiness support only; no clean validation or causal claim | external support / conditional support only; frozen Stage 36E candidates require further validation |
| M4 | Inflammatory signaling / transport / cell-state modulation | multi_target | BSG;IL27RA;NFKBIA;SLC6A12;BSG;NFKBIA;SLC6A12 | 1 | 0 | 0 | gse138852 |  | gse160936;gse125050;gse157827;gse174367 | single_dataset_support | Gene coverage/readiness support only; no clean validation or causal claim | external support / conditional support only; frozen Stage 36E candidates require further validation |

## Mechanism-level support

| mechanism_id | mechanism_name | best_support_tier | cross_dataset_concordance_tier | dominant_celltype_context |
| --- | --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | weak_or_incomplete_external_support | single_dataset_support | not_testable;contextual |
| M2 | Glial activation / disease-associated microglia-astrocyte state | weak_or_incomplete_external_support | single_dataset_support | not_testable;microglia/myeloid |
| M3 | Oxidative stress / antioxidant response | weak_or_incomplete_external_support | single_dataset_support | not_testable;contextual |
| M4 | Inflammatory signaling / transport / cell-state modulation | weak_or_incomplete_external_support | single_dataset_support | not_testable;contextual |

## Candidate-level support

| candidate_gene | mechanism_id | mechanism_name | target | n_datasets_present | n_datasets_direction_match | n_datasets_moderate_or_strong_support | best_dataset_support | support_summary | limitation | recommended_follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APOE | M2 | Glial activation / disease-associated microglia-astrocyte state | GFAP | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| BSG | M4 | Inflammatory signaling / transport / cell-state modulation | 6e10/Aβ | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| BSG | M4 | Inflammatory signaling / transport / cell-state modulation | AT8 | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CST7 | M2 | Glial activation / disease-associated microglia-astrocyte state | GFAP | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSB | M1 | Endolysosomal / autophagy / proteostasis | NeuN | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M1 | Endolysosomal / autophagy / proteostasis | 6e10/Aβ | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M1 | Endolysosomal / autophagy / proteostasis | AT8 | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M1 | Endolysosomal / autophagy / proteostasis | GFAP | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M1 | Endolysosomal / autophagy / proteostasis | NeuN | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M2 | Glial activation / disease-associated microglia-astrocyte state | 6e10/Aβ | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M2 | Glial activation / disease-associated microglia-astrocyte state | AT8 | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M2 | Glial activation / disease-associated microglia-astrocyte state | GFAP | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| CTSD | M2 | Glial activation / disease-associated microglia-astrocyte state | NeuN | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| GPX4 | M3 | Oxidative stress / antioxidant response | Iba1 | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| HMOX1 | M3 | Oxidative stress / antioxidant response | Iba1 | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| IL27RA | M4 | Inflammatory signaling / transport / cell-state modulation | 6e10/Aβ | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| IL27RA | M4 | Inflammatory signaling / transport / cell-state modulation | AT8 | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| LAMP2 | M1 | Endolysosomal / autophagy / proteostasis | NeuN | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| LAPTM5 | M1 | Endolysosomal / autophagy / proteostasis | NeuN | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| LGALS3 | M2 | Glial activation / disease-associated microglia-astrocyte state | GFAP | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| NFKBIA | M4 | Inflammatory signaling / transport / cell-state modulation | 6e10/Aβ | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| NFKBIA | M4 | Inflammatory signaling / transport / cell-state modulation | AT8 | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| NPC2 | M1 | Endolysosomal / autophagy / proteostasis | NeuN | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| NQO1 | M3 | Oxidative stress / antioxidant response | Iba1 | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| SLC6A12 | M4 | Inflammatory signaling / transport / cell-state modulation | 6e10/Aβ | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| SLC6A12 | M4 | Inflammatory signaling / transport / cell-state modulation | AT8 | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| SOD1 | M3 | Oxidative stress / antioxidant response | Iba1 | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| SOD2 | M3 | Oxidative stress / antioxidant response | Iba1 | 1 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |
| TREM2 | M2 | Glial activation / disease-associated microglia-astrocyte state | GFAP | 0 | 0 | 0 |  | presence/coverage support only unless dataset-specific statistics are available | No external dataset was used for candidate selection; incomplete local metadata limits validation claims | manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability |

## Dataset claim levels

| dataset_id | stage_label | dataset_name | analysis_completed | claim_level_allowed | clean_validation_claim_allowed | external_support_claim_allowed | stress_test_claim_allowed | projection_signature_claim_allowed | reason | required_next_gate_for_clean_validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse160936 | Stage37C | GSE160936 pTau-linked glial support | False | readiness_or_missing_data_only | False | False | False | True | Stage 37B-rev1 clean-validation gate remains closed; Stage 37C-F is support/readiness only | manual metadata approval and Stage 37B-rev1/37C clean-validation gate pass |
| gse125050 | Stage37D | GSE125050 pathology-confirmed AD cell-type support | False | readiness_or_missing_data_only | False | False | False | True | Stage 37B-rev1 clean-validation gate remains closed; Stage 37C-F is support/readiness only | manual metadata approval and Stage 37B-rev1/37C clean-validation gate pass |
| gse157827 | Stage37E | GSE157827 broad AD/control snRNA-seq support | False | readiness_or_missing_data_only | False | False | False | True | Stage 37B-rev1 clean-validation gate remains closed; Stage 37C-F is support/readiness only | manual metadata approval and Stage 37B-rev1/37C clean-validation gate pass |
| gse138852 | Stage37F | GSE138852 Grubman-Leng entorhinal cortex smoke test | True | external_support_claim_only | False | True | False | True | Stage 37B-rev1 clean-validation gate remains closed; Stage 37C-F is support/readiness only | manual metadata approval and Stage 37B-rev1/37C clean-validation gate pass |
| gse174367 | optional_secondary | GSE174367 Morabito optional secondary stress-test | False | readiness_or_missing_data_only | False | False | True | True | Stage 37B-rev1 clean-validation gate remains closed; Stage 37C-F is support/readiness only | manual metadata approval and Stage 37B-rev1/37C clean-validation gate pass |

## Limitations and claim boundaries

This stage does not run SEA-AD model training, select candidates, tune thresholds, claim clean external validation, prove causality, or establish therapeutic relevance. Missing local data are reported as missing rather than fabricated.

Allowed wording: external support / conditional support only; frozen Stage 36E candidates require further validation.

Prohibited wording: validated therapeutic target; causal regulator; clean external validation completed; gene ablation result; disease-modifying target; definitive validation.

## Pass/fail summary

| stage37c_f_run | stage36e_inputs_found | dataset_readiness_checked | acquisition_manifest_written | candidate_mapping_written | mechanism_coverage_written | dataset_specific_support_outputs_written | cross_dataset_concordance_written | mechanism_summary_written | candidate_summary_written | claim_boundary_audit_written | reports_written | analysis_run_for_available_datasets | missing_data_reports_written_if_needed | no_new_sea_ad_model_training | no_model_selection_using_external_datasets | no_candidate_selection_using_external_datasets | no_causal_claim | no_therapeutic_claim | no_definitive_clean_external_validation_claim | safety_audit_pass | stage37c_f_run_pass | controlled_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | Stage 37C-F produced multi-dataset external-support/readiness outputs using frozen Stage 36E candidates; no clean validation, causal, or therapeutic claim was made. |