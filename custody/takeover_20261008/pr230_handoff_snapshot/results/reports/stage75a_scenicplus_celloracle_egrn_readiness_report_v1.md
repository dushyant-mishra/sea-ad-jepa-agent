# Stage75A SCENIC+/CellOracle eGRN readiness

## Decision

Stage75A does **not** run SCENIC+ or CellOracle. It audits whether the project is
ready to upgrade Stage74 into a true enhancer-supported, state-specific
perturbation framework.

## Pass/fail

| stage75a_run | required_inputs_found | all_required_dependencies_installed | all_required_regulatory_resources_found | ready_for_stage75b_scenicplus_run | ready_for_stage75c_state_response_model | ready_for_stage75d_perturbation_engine | audit_complete | stage75a_readiness_only | no_scenicplus_run | no_celloracle_run | no_model_training | no_prediction_benchmark_update | no_external_validation_claim | no_causal_knockout_claim | no_therapeutic_claim | no_validated_grn_claim | raw_data_not_committed | safety_audit_pass | stage75a_run_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | False | False | False | False | False | True | True | True | True | True | True | True | True | True | True | True | True | True |

## Dependency audit

| python_module | installed_in_current_env | role |
| --- | --- | --- |
| scenicplus | False | enhancer-driven eGRN construction |
| pycisTopic | False | ATAC topic/region processing for SCENIC+ |
| ctxcore | False | motif/ranking context support |
| arboreto | False | GRNBoost-style expression network support |
| celloracle | False | state-specific perturbation simulation framework |
| pyranges | False | genomic interval operations |
| pybiomart | False | gene annotation retrieval/harmonization |
| mudata | False | multiomic object handling |
| scanpy | True | single-cell preprocessing already available |

## Regulatory resource gaps

| resource | local_candidate_found | local_candidate_examples | required_for_true_egrn | stage75a_action |
| --- | --- | --- | --- | --- |
| motif_collection | False |  | True | acquire_or_configure_before_stage75b |
| cistarget_rankings_or_motif_rankings | False |  | True | acquire_or_configure_before_stage75b |
| chromosome_sizes | False |  | True | acquire_or_configure_before_stage75b |
| gene_annotation_gtf_or_bed | False |  | True | acquire_or_configure_before_stage75b |
| peak_to_gene_or_region_to_gene_map | False |  | True | acquire_or_configure_before_stage75b |
| tf_annotation_list | False |  | True | acquire_or_configure_before_stage75b |

## Staged design

| stage | component | purpose | status | causal_validation_claim |
| --- | --- | --- | --- | --- |
| Stage75A | readiness_and_handoff | audit dependencies/resources and freeze design | current stage | False |
| Stage75B | scenicplus_egrn_construction | construct TF->region->gene eRegulons with motif/accessibility/region-gene support | not run yet | False |
| Stage75C | state_specific_response_models | fit regularized target-gene response models in MTG/DLPFC rare-high/background contexts | not run yet | False |
| Stage75D | celloracle_style_perturbation_engine | iterative bounded signed expression-shift propagation with donor bootstrap and JEPA latent readout | not run yet | False |

## State-specific response model plan

| context | model | cv_unit | uses_graph_as_predictor_mask | selects_edges_by_pathology | output |
| --- | --- | --- | --- | --- | --- |
| MTG_rare_high | regularized target_gene ~ signed upstream TF activities + donor/technical covariates | donor_grouped | True | False | state_specific_signed_coefficient_matrix |
| MTG_background | regularized target_gene ~ signed upstream TF activities + donor/technical covariates | donor_grouped | True | False | state_specific_signed_coefficient_matrix |
| DLPFC_rare_high | regularized target_gene ~ signed upstream TF activities + donor/technical covariates | donor_grouped | True | False | state_specific_signed_coefficient_matrix |
| DLPFC_background | regularized target_gene ~ signed upstream TF activities + donor/technical covariates | donor_grouped | True | False | state_specific_signed_coefficient_matrix |

## Perturbation engine plan

| engine_step | max_iterations | fixed_doses | readout | control | required_before_regulator_pass |
| --- | --- | --- | --- | --- | --- |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | no_propagation_tf_perturbation | True |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | degree_preserved_target_shuffled_directed_graph | True |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | sign_shuffled_graph | True |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | tf_label_shuffled_graph | True |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | region_to_gene_shuffled_graph | True |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | state_label_shuffled_coefficients | True |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | expression_matched_random_regulator | True |
| iterative_signed_delta_expression | 3 | 0.25;0.50;0.75;1.00 | frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap | background_coefficients_applied_to_rare_high_cells | True |

## Interpretation

The next scientific step is dependency/resource acquisition for Stage75B, not a
larger GNN. Stage75B should construct true TF→region→gene eRegulons only after
motif/ranking, gene annotation, TF annotation, and peak-to-gene resources are
available.
