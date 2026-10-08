# Stage44 publication table package

## Table 1

| stage | candidate | role | mean_pooled_oof_spearman | bootstrap_lower_95 | delta_vs_stage27c | lock_status | manuscript_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage27C | module_pca_ridge | official locked internal benchmark | 0.3267024400121495 |  | 0.0 | locked | Official locked internal benchmark. |
| Stage39E | rank_inverse_normal_module_pca8_ridge | credible unlocked reference | 0.35808116279206914 |  | 0.031378722779919654 | credible_unlocked | Strong point estimate; not locked. |
| Stage41B | latent_plus_safe_metadata | credible unlocked signal | 0.3394229016907968 |  | 0.012720461678647321 | credible_unlocked | Safe metadata/latent point-estimate gain. |
| Stage41C | blend_stage41b_with_stage39e_pca8 | best credible unlocked signal | 0.36808747595423713 | 0.2603604646376338 | 0.041385035942087645 | credible_unlocked_not_locked | Best signal but CI below Stage27C. |
| Stage45 | latent_plus_safe_metadata_plus_cellxgene_plus_mri_engineered | negative new-feature result | 0.3121433633694442 | 0.214644 | -0.014559 | do_not_lock | CELLxGENE/MRI additions did not improve. |

Legend: Publication-ready summary table 1.

## Table 2

| strategy | representative_stage | best_outcome | lock_result | reason_not_locked | manuscript_message |
| --- | --- | --- | --- | --- | --- |
| graph/topology rescue | Stage30/31 | did not beat Stage27C | not locked | graph-specific/stability gates failed | Graph machinery did not robustly improve the locked benchmark. |
| external pretraining | Stage33/34 | failed rescue | not locked | no benchmark rescue | External pretraining alone was insufficient. |
| latent prediction head | Stage39B | failed rescue | not locked | no robust material improvement | LPH branch was a useful negative result. |
| neural rescue | Stage40A | failed | not locked | capacity/small donor risk | Stop architecture tuning without new data. |
| safe metadata/MRI | Stage41B | 0.339423 | not locked | CI guard failed | Safe metadata helped point estimate but not robustness. |
| Stage41 stability rescue | Stage41C | 0.368087 | credible unlocked | CI lower bound below Stage27C | Best credible signal but not locked. |
| CELLxGENE/MRI engineered feature acquisition | Stage45 | 0.312143 | not locked | below Stage27C/Stage41C | Successful acquisition but negative performance result. |

Legend: Publication-ready summary table 2.

## Table 3

| candidate | mean_pass | material_threshold_pass | bootstrap_ci_pass | target_guard_pass | abeta_guard_pass | iba1_guard_pass | negative_control_pass | proxy_leakage_pass | final_lock_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stage27C | True | False | True | True | True | True | True | True | locked |
| Stage41C | True | True | False | True | True | True | True | True | credible_unlocked_not_locked |
| Stage45 | False | False | False | True | False | False | True | True | do_not_lock_stage45 |

Legend: Publication-ready summary table 3.

## Table 4

| cellxgene_metadata_available | exact_donor_overlap | feature_matrices_built | best_score | delta_vs_stage27c | delta_vs_stage41c | decision | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| True | 84/84 | 7 | 0.3121433633694442 | -0.014559 | -0.055944 | do_not_lock_stage45 | successful acquisition but negative benchmark result |

Legend: Publication-ready summary table 4.

## Table 5

| mechanism_id | mechanism_name | frozen_priority | primary_pathology_targets | representative_modules | representative_genes | supporting_stage36c_targets | supporting_stage36d_rows | biological_rationale | key_limitation | allowed_claim_language | disallowed_claim_language | recommended_next_validation_route | claim_status | prohibited_claim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | 1 | NeuN;6e10/Aβ;AT8;GFAP | module_pca_component_1;module_at8_associated_first_pass;module_pca_component_2;module_disease_associated_microglia;module_lysosome_phagocytosis | CTSD;CTSB;LAPTM5;NPC2;LAMP2 | 6e10/Aβ;AT8;GFAP;NeuN | 8 | This bin captures lysosomal, endosomal, autophagy, and proteostasis-linked candidates that recur in Stage 36C/36D ranked hypotheses, especially CTSD/CTSB/LAPTM5/NPC2/LAMP2. It is the strongest first validation theme when supported because it spans neuronal preservation and amyloid/tau/glial pathology contexts. | Stage 36E is a frozen registry and validation-protocol package only. It does not run new modeling, download data, perform external validation, prove causality, or establish therapeutic relevance. | internally prioritized follow-up hypothesis with model-implied sensitivity and locally grounded prior support; requires independent validation before any strong biological claim | validated target; causal regulator; therapeutic target; gene ablation result; external validation; disease-modifying target; in silico counterfactual sensitivity equals validation | independent cohort replication; spatial transcriptomic confirmation; single-cell/single-nucleus expression confirmation; pathology colocalization; immunostaining/protein-level confirmation; future perturbation experiment; manual biological review | hypothesis-generating only | external validation; clean validation; causal mechanism; therapeutic target; gene-ablation support; disease-modifying effect |
| M2 | Glial activation / disease-associated microglia-astrocyte state | 2 | GFAP;Iba1;6e10/Aβ;AT8 | module_pca_component_1;module_at8_associated_first_pass;module_pca_component_2;module_disease_associated_microglia;module_lysosome_phagocytosis | TREM2;CST7;APOE;LGALS3;CTSD | 6e10/Aβ;AT8;GFAP;NeuN | 8 | This bin captures disease-associated microglia/astrocyte-state candidates and glial activation context, including TREM2, CST7, APOE, LGALS3, and CTSD. | Stage 36E is a frozen registry and validation-protocol package only. It does not run new modeling, download data, perform external validation, prove causality, or establish therapeutic relevance. | internally prioritized follow-up hypothesis with model-implied sensitivity and locally grounded prior support; requires independent validation before any strong biological claim | validated target; causal regulator; therapeutic target; gene ablation result; external validation; disease-modifying target; in silico counterfactual sensitivity equals validation | independent cohort replication; spatial transcriptomic confirmation; single-cell/single-nucleus expression confirmation; pathology colocalization; immunostaining/protein-level confirmation; future perturbation experiment; manual biological review | hypothesis-generating only | external validation; clean validation; causal mechanism; therapeutic target; gene-ablation support; disease-modifying effect |
| M3 | Oxidative stress / antioxidant response | 3 | Iba1 | module_pca_component_1;module_oxidative_stress | HMOX1;NQO1;SOD2;SOD1;GPX4 | Iba1 | 5 | This bin captures oxidative-stress and antioxidant-response candidates prioritized for the Iba1 context. | Stage 36E is a frozen registry and validation-protocol package only. It does not run new modeling, download data, perform external validation, prove causality, or establish therapeutic relevance. | internally prioritized follow-up hypothesis with model-implied sensitivity and locally grounded prior support; requires independent validation before any strong biological claim | validated target; causal regulator; therapeutic target; gene ablation result; external validation; disease-modifying target; in silico counterfactual sensitivity equals validation | independent cohort replication; spatial transcriptomic confirmation; single-cell/single-nucleus expression confirmation; pathology colocalization; immunostaining/protein-level confirmation; future perturbation experiment; manual biological review | hypothesis-generating only | external validation; clean validation; causal mechanism; therapeutic target; gene-ablation support; disease-modifying effect |
| M4 | Inflammatory signaling / transport / cell-state modulation | 4 | 6e10/Aβ;AT8 | module_pca_component_1;module_at8_associated_first_pass | BSG;SLC6A12;IL27RA;NFKBIA | 6e10/Aβ;AT8 | 8 | This bin captures inflammatory signaling, transport, and cell-state modulation candidates prioritized in amyloid/tau-linked Stage 36C/36D rows. | Stage 36E is a frozen registry and validation-protocol package only. It does not run new modeling, download data, perform external validation, prove causality, or establish therapeutic relevance. | internally prioritized follow-up hypothesis with model-implied sensitivity and locally grounded prior support; requires independent validation before any strong biological claim | validated target; causal regulator; therapeutic target; gene ablation result; external validation; disease-modifying target; in silico counterfactual sensitivity equals validation | independent cohort replication; spatial transcriptomic confirmation; single-cell/single-nucleus expression confirmation; pathology colocalization; immunostaining/protein-level confirmation; future perturbation experiment; manual biological review | hypothesis-generating only | external validation; clean validation; causal mechanism; therapeutic target; gene-ablation support; disease-modifying effect |

Legend: Publication-ready summary table 5.

## Table 6

| support_tests_ready | support_tests_total | clean_validation_claim | allowed_use | limitation |
| --- | --- | --- | --- | --- |
| 4 | 24 | False | support/readiness only | external compatibility remains limited |

Legend: Publication-ready summary table 6.

## Table 7

| claim | status |
| --- | --- |
| internal donor-held-out benchmark | allowed |
| credible unlocked internal signal | allowed |
| support/readiness only | allowed |
| hypothesis-generating mechanism | allowed |
| external validation | prohibited |
| clean validation | prohibited |
| causality | prohibited |
| therapeutic relevance | prohibited |
| gene-ablation support | prohibited |
| disease-modifying effect | prohibited |
| Stage41C as locked | prohibited |
| Stage45 as improvement | prohibited |

Legend: Publication-ready summary table 7.

