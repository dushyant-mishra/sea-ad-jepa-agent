# Stage 36D PI meeting summary v1

## One-line readout

Stage 36D converts the Stage 36C ranked, locally grounded hypotheses into a frozen validation-planning shortlist. It does not add new modeling or validation.

## Top candidates by target

| target | top_module | top_gene_candidates |
| --- | --- | --- |
| 6e10/Aβ | module_pca_component_1 | BSG; SLC6A12; IL27RA; NFKBIA; CTSD |
| AT8 | module_at8_associated_first_pass | BSG; SLC6A12; IL27RA; NFKBIA; CTSD |
| GFAP | module_pca_component_1 | TREM2; CST7; APOE; LGALS3; CTSD |
| Iba1 | module_pca_component_1 | HMOX1; NQO1; SOD2; SOD1; GPX4 |
| NeuN | module_pca_component_2 | CTSB; LAPTM5; CTSD; NPC2; LAMP2 |

## Safe interpretation language

Stage 36D freezes a follow-up hypothesis from Stage 36C for validation planning only; the candidate is not validated, causal, or therapeutic.

Avoid saying that these are causal regulators, therapeutic targets, validated mechanisms, or completed external-validation results.

## Recommended next steps

1. Choose a small subset of target/gene/module hypotheses for independent cohort replication or spatial/single-cell confirmation.
2. For candidates that remain coherent, design pre-registered perturbation or staining/colocalization assays.
3. Keep Stage 36D candidate status frozen until new evidence is generated and audited.

## Validation readiness audit

| stage36d_run | stage36c_inputs_found | candidate_shortlist_written | assay_planning_table_written | pi_report_written | no_new_modeling_run | no_external_validation_run | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_in_silico_validation_claim | safety_audit_pass | stage36d_run_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True |