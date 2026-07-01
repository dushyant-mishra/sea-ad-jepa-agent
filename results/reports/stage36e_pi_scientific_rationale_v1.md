# Stage 36E PI scientific rationale v1

## Short readout

Stage 36E freezes four biological mechanism bins and a validation protocol from Stage 36C/36D follow-up hypotheses.

## Frozen mechanisms

| mechanism_id | mechanism_name | frozen_priority | representative_genes | primary_pathology_targets |
| --- | --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | 1 | CTSD;CTSB;LAPTM5;NPC2;LAMP2 | NeuN;6e10/Aβ;AT8;GFAP |
| M2 | Glial activation / disease-associated microglia-astrocyte state | 2 | TREM2;CST7;APOE;LGALS3;CTSD | GFAP;Iba1;6e10/Aβ;AT8 |
| M3 | Oxidative stress / antioxidant response | 3 | HMOX1;NQO1;SOD2;SOD1;GPX4 | Iba1 |
| M4 | Inflammatory signaling / transport / cell-state modulation | 4 | BSG;SLC6A12;IL27RA;NFKBIA | 6e10/Aβ;AT8 |

## Top genes/modules by mechanism

| mechanism_id | top_genes_modules | targets |
| --- | --- | --- |
| M4 | BSG;SLC6A12;IL27RA;NFKBIA | 6e10/Aβ;AT8 |
| M1 | CTSD;CTSB;LAPTM5;NPC2;LAMP2;module_pca_component_1;module_at8_associated_first_pass;module_pca_component_2 | 6e10/Aβ;AT8;GFAP;NeuN |
| M2 | CTSD;TREM2;CST7;APOE;LGALS3;module_pca_component_1 | 6e10/Aβ;AT8;GFAP;NeuN;Iba1 |
| M3 | HMOX1;NQO1;SOD2;SOD1;GPX4 | Iba1 |

## Target coverage

| target | candidates | mechanisms |
| --- | --- | --- |
| 6e10/Aβ | BSG;SLC6A12;IL27RA;NFKBIA;CTSD;module_pca_component_1 | M4;M1;M2 |
| AT8 | BSG;SLC6A12;IL27RA;NFKBIA;CTSD;module_at8_associated_first_pass | M4;M1;M2 |
| GFAP | TREM2;CST7;APOE;LGALS3;CTSD;module_pca_component_1 | M2;M1 |
| Iba1 | HMOX1;NQO1;SOD2;SOD1;GPX4;module_pca_component_1 | M3;M2 |
| NeuN | CTSB;LAPTM5;CTSD;NPC2;LAMP2;module_pca_component_2 | M1;M2 |

## Why endolysosomal/proteostasis biology is the strongest first validation theme

The endolysosomal/autophagy/proteostasis bin has broad target relevance in the frozen registry and includes recurrent candidates such as CTSD, CTSB, LAPTM5, NPC2, and LAMP2. If prioritized for first-pass validation, it offers a biologically coherent bridge across neuronal and pathology-linked readouts while remaining safely framed as a follow-up hypothesis.

## Validation routes

- independent cohort replication
- spatial transcriptomic confirmation
- single-cell or single-nucleus expression confirmation
- pathology colocalization
- immunostaining or protein-level confirmation
- perturbation experiment only as future causal follow-up
- manual biological review

## Safe lab-meeting/manuscript-planning language

internally prioritized follow-up hypothesis with model-implied sensitivity and locally grounded prior support; requires independent validation before any strong biological claim

Avoid: validated target; causal regulator; therapeutic target; gene ablation result; external validation; disease-modifying target; in silico counterfactual sensitivity equals validation

## Pass/fail

| stage36e_run_pass | required_target_coverage | safety_audit_pass |
| --- | --- | --- |
| True | 6e10/Aβ;AT8;GFAP;Iba1;NeuN | True |