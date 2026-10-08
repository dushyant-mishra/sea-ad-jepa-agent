# Stage 36D validation handoff report v1

## Purpose

Stage 36D is a report-only and planning-only handoff from the already completed Stage 36C ranked hypothesis package. It freezes a compact target-level shortlist and maps each hypothesis to possible next validation routes.

No new modeling was run. No data were downloaded. No external validation, perturbation experiment, causal validation, or therapeutic assessment was performed.

## Inputs

- Stage 36C ranked gene hypotheses
- Stage 36C ranked module hypotheses
- Stage 36C target-level hypothesis summary
- Stage 36C validation planning table
- Stage 36C safety and pass/fail audits
- Stage 36C technical and PI-readable reports

Stage 36A and Stage 36B were not rerun. Stage 36D only consumes already-generated local outputs.

## Candidate-freezing logic

For each required target, Stage 36D retains the Stage 36C top module and the top ranked gene candidates from Stage 36C. The shortlist preserves Stage 36C rank and priority fields where available, along with local knowledge-grounding status and conservative claim boundaries.

## Frozen target-level shortlist

| target | target_key | top_module | local_knowledge_grounding_status | top_genes | max_stage36c_priority_score |
| --- | --- | --- | --- | --- | --- |
| 6e10/Aβ | 6e10/A_beta | module_pca_component_1 | passed | BSG; SLC6A12; IL27RA; NFKBIA; CTSD | 1.25 |
| AT8 | AT8 | module_at8_associated_first_pass | passed | BSG; SLC6A12; IL27RA; NFKBIA; CTSD | 1.25 |
| GFAP | GFAP | module_pca_component_1 | passed | TREM2; CST7; APOE; LGALS3; CTSD | 1.239036 |
| Iba1 | Iba1 | module_pca_component_1 | passed | HMOX1; NQO1; SOD2; SOD1; GPX4 | 1.25 |
| NeuN | NeuN | module_pca_component_2 | passed | CTSB; LAPTM5; CTSD; NPC2; LAMP2 | 1.25 |

## Validation readiness

| stage36d_run | stage36c_inputs_found | candidate_shortlist_written | assay_planning_table_written | pi_report_written | no_new_modeling_run | no_external_validation_run | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_in_silico_validation_claim | safety_audit_pass | stage36d_run_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True |

## Proposed validation route categories

- independent cohort replication
- spatial transcriptomic confirmation
- single-cell expression confirmation
- perturbation experiment
- immunostaining / pathology colocalization
- literature/manual biological review

These are proposed next validation routes only. They are not completed validation results.

## Key limitations and claim boundaries

- Candidates are follow-up hypotheses only.
- Model-implied counterfactual sensitivity is not gene ablation.
- Local knowledge grounding is annotation and context, not validation.
- Stage 36D does not prove causality, druggability, therapeutic relevance, or spatial pathology proximity.
- Stage 36D must not be described as external validation.

Allowed language: Stage 36D freezes a follow-up hypothesis from Stage 36C for validation planning only; the candidate is not validated, causal, or therapeutic.

Disallowed language: causal validation; therapeutic target; drug target; validated mechanism; in silico counterfactual sensitivity equals gene ablation; Stage 36D external validation

## Pass/fail summary

| stage36d_run | stage36c_inputs_found | candidate_shortlist_written | assay_planning_table_written | pi_report_written | no_new_modeling_run | no_external_validation_run | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_in_silico_validation_claim | safety_audit_pass | stage36d_run_pass | n_stage36c_inputs_expected | n_stage36c_inputs_found | outputs_written | controlled_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True | 8 | 8 | candidate_shortlist;assay_planning_table;validation_readiness_audit;pass_fail;report;pi_report | Stage 36D froze Stage 36C ranked, locally grounded follow-up hypotheses into a validation-facing handoff package. It is planning only: no new modeling, data download, external validation, causal validation, therapeutic claim, or gene-ablation claim was made. |

## Output tables

- `results/tables/stage36d_candidate_shortlist_v1.csv`
- `results/tables/stage36d_assay_planning_table_v1.csv`
- `results/tables/stage36d_validation_readiness_audit_v1.csv`
- `results/tables/stage36d_pass_fail_v1.csv`