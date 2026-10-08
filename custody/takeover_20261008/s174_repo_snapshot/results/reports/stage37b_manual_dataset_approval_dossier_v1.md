# Stage 37B manual dataset approval dossier v1

## Purpose

Stage 37B turns the Stage 37A validation eligibility audit into a PI-facing manual dataset approval and validation-readiness dossier.

It does not run validation, run new modeling, download datasets, scrape the web, or claim external validation.

## Inputs and relationship to Stage 37A

Stage 37A found zero clean external validation candidates and recommended manual dataset approval. Stage 37B therefore creates decision packets and keeps the clean-validation gate closed unless complete evidence is already present.

## Dataset decision matrix summary

| stage37b_decision | n_datasets |
| --- | --- |
| allow_projection_or_signature_support_only | 2 |
| manual_metadata_review_required | 9 |
| reject_for_clean_validation | 21 |

## Manual review priorities

| review_priority | n_review_items |
| --- | --- |
| high | 9 |
| medium | 2 |

## Clean validation gate status

| gate_id | gate_name | gate_pass | evidence_source | consequence_if_fail | stage37c_allowed_if_pass |
| --- | --- | --- | --- | --- | --- |
| G_FINAL | stage37c_clean_external_validation_allowed | False | Stage 37A found zero clean validation candidates; Stage 37B found no complete explicit approval evidence | Stage 37C clean external validation is not allowed; proceed to manual approval/data acquisition | False |

## Required metadata checklist

| metadata_item_id | metadata_item | required_for_clean_validation | failure_consequence |
| --- | --- | --- | --- |
| MD01 | Dataset not used for training | True | dataset cannot be approved for clean validation |
| MD02 | Dataset not used for pretraining | True | dataset cannot be approved for clean validation |
| MD03 | Dataset not used for model selection | True | dataset cannot be approved for clean validation |
| MD04 | Dataset not used for candidate selection | True | dataset cannot be approved for clean validation |
| MD05 | Dataset not used for threshold tuning | True | dataset cannot be approved for clean validation |
| MD06 | Donor/sample-level metadata available | True | dataset cannot be approved for clean validation |
| MD07 | Frozen candidate direction can be tested | True | dataset cannot be approved for clean validation |
| MD08 | Pathology or mechanism readout available | True | dataset cannot be approved for clean validation |
| MD09 | Gene/module measurement available | True | dataset cannot be approved for clean validation |
| MD10 | Negative/null results can be reported | True | dataset cannot be approved for clean validation |
| MD11 | Licensing/access permits analysis | True | dataset cannot be approved for clean validation |
| MD12 | Batch/sample provenance documented | True | dataset cannot be approved for clean validation |

## Dataset-use policy

| dataset_use_category | allowed_actions | prohibited_actions | required_next_gate |
| --- | --- | --- | --- |
| clean_external_validation | run pre-registered Stage 37C validation only after gate passes | use before PI approval; tune models or thresholds; make causal/therapeutic claims | Stage37B clean validation gate |
| stress_test_support | run robustness/stress-test analyses after labeling as non-clean support | call external validation or clean validation | manual claim-boundary audit |
| projection_or_signature_support | compare frozen mechanisms/candidates to signatures or projections | claim pathology validation or causality | manual metadata and claim-boundary review |
| robustness_only | use for domain robustness or plausibility context | use as primary validation | manual role confirmation |
| manual_review_pending | inspect metadata, independence, readouts, and licensing | run validation before approval | PI approval |
| excluded_or_contaminated | document provenance and exclusion | use for clean validation | none; excluded from clean validation |

## Candidate-to-validation-route summary

| mechanism_id | mechanism_name | preferred_validation_dataset_type | minimum_required_readout |
| --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | clean independent donor/sample-level dataset with frozen pathology or mechanism readouts | frozen target/mechanism readout plus candidate gene/module measurement |
| M2 | Glial activation / disease-associated microglia-astrocyte state | clean independent donor/sample-level dataset with frozen pathology or mechanism readouts | frozen target/mechanism readout plus candidate gene/module measurement |
| M3 | Oxidative stress / antioxidant response | clean independent donor/sample-level dataset with frozen pathology or mechanism readouts | frozen target/mechanism readout plus candidate gene/module measurement |
| M4 | Inflammatory signaling / transport / cell-state modulation | clean independent donor/sample-level dataset with frozen pathology or mechanism readouts | frozen target/mechanism readout plus candidate gene/module measurement |

## Stage 37C recommendation

Stage 37C clean external validation is not allowed now. The next action is PI/manual dataset approval and metadata acquisition for candidate resources.

## Claim boundaries

Safe wording: manual dataset approval; validation-readiness dossier; candidate validation resource; requires manual metadata confirmation; not yet approved for clean validation; approved only for stress-test support; approved only for projection/signature support; Stage 37C clean validation not allowed unless gate passes.

Avoid: validated; external validation completed; clean validation proven; causal regulator; therapeutic target; disease-modifying target; approved clean validation dataset.

## What Stage 37B does not prove

- It does not validate any dataset.
- It does not complete external validation.
- It does not prove any dataset is clean validation.
- It does not support causal, therapeutic, or disease-modifying claims.

## Pass/fail summary

| stage37b_run | stage37a_inputs_found | stage36e_inputs_found | dataset_decision_matrix_written | manual_review_packet_written | metadata_checklist_written | dataset_use_policy_written | candidate_validation_route_written | pi_approval_template_written | clean_validation_gate_written | no_new_modeling_run | no_validation_run | no_data_download | no_web_scraping | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_unapproved_clean_validation_dataset | safety_audit_pass | stage37b_run_pass | stage37c_clean_external_validation_allowed | controlled_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | False | Stage 37B is a manual dataset approval dossier only; Stage 37C clean validation is not allowed unless the clean-validation gate passes. |