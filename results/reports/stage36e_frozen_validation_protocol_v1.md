# Stage 36E frozen validation protocol v1

## Purpose

Stage 36E freezes biological mechanisms, candidate genes/modules, and validation decision rules from Stage 36C/36D outputs before any new validation data are examined.

It is report-only and planning-only. It does not run new modeling, download data, scrape the web, perform external validation, claim causal validation, claim therapeutic targets, or claim gene ablation.

## Inputs

Stage 36E uses the already generated Stage 36C ranked hypothesis outputs and Stage 36D validation handoff outputs. Stage 36C and Stage 36D are not rerun.

## Frozen mechanism registry summary

| mechanism_id | mechanism_name | frozen_priority | primary_pathology_targets | representative_genes | supporting_stage36d_rows |
| --- | --- | --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | 1 | NeuN;6e10/Aβ;AT8;GFAP | CTSD;CTSB;LAPTM5;NPC2;LAMP2 | 8 |
| M2 | Glial activation / disease-associated microglia-astrocyte state | 2 | GFAP;Iba1;6e10/Aβ;AT8 | TREM2;CST7;APOE;LGALS3;CTSD | 8 |
| M3 | Oxidative stress / antioxidant response | 3 | Iba1 | HMOX1;NQO1;SOD2;SOD1;GPX4 | 5 |
| M4 | Inflammatory signaling / transport / cell-state modulation | 4 | 6e10/Aβ;AT8 | BSG;SLC6A12;IL27RA;NFKBIA | 8 |

## Frozen candidate registry summary

| mechanism_id | target | candidates |
| --- | --- | --- |
| M4 | 6e10/Aβ | BSG;SLC6A12;IL27RA;NFKBIA |
| M1 | 6e10/Aβ | CTSD;module_pca_component_1 |
| M2 | 6e10/Aβ | CTSD |
| M4 | AT8 | BSG;SLC6A12;IL27RA;NFKBIA |
| M1 | AT8 | CTSD;module_at8_associated_first_pass |
| M2 | AT8 | CTSD |
| M2 | GFAP | TREM2;CST7;APOE;LGALS3;CTSD |
| M1 | GFAP | CTSD;module_pca_component_1 |
| M3 | Iba1 | HMOX1;NQO1;SOD2;SOD1;GPX4 |
| M1 | NeuN | CTSB;LAPTM5;CTSD;NPC2;LAMP2;module_pca_component_2 |
| M2 | NeuN | CTSD |
| M2 | Iba1 | module_pca_component_1 |

## Validation decision rules

| rule_id | rule_name | rule_text |
| --- | --- | --- |
| R01 | independent_validation_requires_clean_holdout | Independent validation requires a clean holdout dataset not used in model development. |
| R02 | validation_dataset_must_not_have_been_used_for_training | Validation data must not have been used for Stage 27C/36A model fitting. |
| R03 | validation_dataset_must_not_have_been_used_for_pretraining | Validation data must not have been used for external pretraining. |
| R04 | validation_dataset_must_not_have_been_used_for_model_selection | Validation data must not have influenced model/feature/threshold selection. |
| R05 | candidate_direction_must_be_prespecified | The candidate, pathology target, and expected direction must be frozen before validation. |
| R06 | effect_direction_must_match_frozen_hypothesis | A positive validation readout requires the observed direction to match the frozen hypothesis. |
| R07 | negative_result_must_be_reported | Negative and null results must be reported rather than silently filtered. |
| R08 | association_validation_does_not_imply_causality | Predictive or association replication does not imply causal mechanism. |
| R09 | perturbation_required_for_causal_claim | Causal language requires direct perturbational evidence with prespecified outcomes. |
| R10 | therapeutic_claims_prohibited_without_disease_modifying_experimental_evidence | Therapeutic claims are prohibited without disease-modifying experimental evidence. |

## Mechanism-to-assay map

| mechanism_id | validation_category | assay_status |
| --- | --- | --- |
| M1 | independent cohort replication | proposed_not_completed |
| M1 | spatial transcriptomic confirmation | proposed_not_completed |
| M1 | single-cell or single-nucleus expression confirmation | proposed_not_completed |
| M1 | pathology colocalization | proposed_not_completed |
| M1 | immunostaining or protein-level confirmation | proposed_not_completed |
| M1 | perturbation experiment, only as future causal follow-up | proposed_not_completed |
| M1 | manual biological review | proposed_not_completed |
| M2 | independent cohort replication | proposed_not_completed |
| M2 | spatial transcriptomic confirmation | proposed_not_completed |
| M2 | single-cell or single-nucleus expression confirmation | proposed_not_completed |
| M2 | pathology colocalization | proposed_not_completed |
| M2 | immunostaining or protein-level confirmation | proposed_not_completed |
| M2 | perturbation experiment, only as future causal follow-up | proposed_not_completed |
| M2 | manual biological review | proposed_not_completed |
| M3 | independent cohort replication | proposed_not_completed |
| M3 | spatial transcriptomic confirmation | proposed_not_completed |
| M3 | single-cell or single-nucleus expression confirmation | proposed_not_completed |
| M3 | pathology colocalization | proposed_not_completed |
| M3 | immunostaining or protein-level confirmation | proposed_not_completed |
| M3 | perturbation experiment, only as future causal follow-up | proposed_not_completed |
| M3 | manual biological review | proposed_not_completed |
| M4 | independent cohort replication | proposed_not_completed |
| M4 | spatial transcriptomic confirmation | proposed_not_completed |
| M4 | single-cell or single-nucleus expression confirmation | proposed_not_completed |
| M4 | pathology colocalization | proposed_not_completed |
| M4 | immunostaining or protein-level confirmation | proposed_not_completed |
| M4 | perturbation experiment, only as future causal follow-up | proposed_not_completed |
| M4 | manual biological review | proposed_not_completed |

## Claim boundaries

| no_new_modeling_run | no_external_validation_run | no_data_download | no_web_scraping | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_in_silico_validation_claim | no_external_validation_language | all_candidates_described_as_follow_up_hypotheses | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True |

## What Stage 36E does not prove

- It does not prove causality.
- It does not establish therapeutic targets.
- It does not validate gene ablation.
- It does not show external validation.
- It does not show disease-modifying experimental evidence.

## Exact safe interpretation language

internally prioritized follow-up hypothesis with model-implied sensitivity and locally grounded prior support; requires independent validation before any strong biological claim

Disallowed language: validated target; causal regulator; therapeutic target; gene ablation result; external validation; disease-modifying target; in silico counterfactual sensitivity equals validation

## Pass/fail summary

| stage36e_run | stage36c_inputs_found | stage36d_inputs_found | frozen_mechanism_registry_written | priority_candidate_registry_written | validation_decision_rules_written | mechanism_to_assay_map_written | claim_boundaries_audit_written | pi_scientific_rationale_written | required_target_coverage_pass | required_target_coverage | no_new_modeling_run | no_external_validation_run | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_in_silico_validation_claim | safety_audit_pass | stage36e_run_pass | controlled_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | 6e10/Aβ;AT8;GFAP;Iba1;NeuN | True | True | True | True | True | True | True | True | Stage 36E froze mechanisms, candidates, and validation decision rules before new validation data are examined. It is a protocol/registry package only, not validation. |