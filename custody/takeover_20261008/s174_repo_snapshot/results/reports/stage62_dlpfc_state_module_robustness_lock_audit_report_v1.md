# Stage62 DLPFC state-module robustness lock audit

## Bottom line

The corrected DLPFC state-module signal remains promising regional support but did not satisfy the stricter robustness/lock criteria.

## Feature-source audit

| gene_symbol_source | var_index_contains_ensembl_ids | var_index_must_not_be_used_as_gene_symbols | n_dlpfc_feature_donors | n_pathology_target_donors | n_overlap_donors | n_cells_loaded | n_features | n_state_abundance_features | n_state_expression_module_features | feature_source_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| var/feature_name | True | True | 80 | 84 | 80 | 42486 | 120 | 12 | 108 | True |

## Branch comparison

| model_variant | mean_pooled_oof_spearman | median_pooled_oof_spearman | min_seed_dim_score | max_seed_dim_score | sd_seed_dim_score | n_seed_dim_runs | delta_vs_stage27c_locked |
| --- | --- | --- | --- | --- | --- | --- | --- |
| negative_control_state_label_shuffled_within_donor | 0.28139076418190345 | 0.2774730426629161 | 0.2394702297233943 | 0.34307079231129867 | 0.03114149022816151 | 20 | -0.045311675830246034 |
| negative_control_expression_permuted_within_donor | 0.28029043600562586 | 0.27669948429442104 | 0.23028598218471635 | 0.3421190811064229 | 0.032307043244436964 | 20 | -0.04641200400652362 |
| mtg_programming_plus_dlpfc_state_modules_full | 0.2773150492264417 | 0.2747257383966245 | 0.23203000468823257 | 0.34332395686826067 | 0.03185350943301839 | 20 | -0.04938739078570781 |
| mtg_programming_plus_dlpfc_state_expression_modules | 0.2761298640412565 | 0.27463666197843417 | 0.23294889826535398 | 0.34314580403188 | 0.03223246899095773 | 20 | -0.050572575970892986 |
| negative_control_expression_permuted_within_state | 0.27329137365213313 | 0.2726863572433193 | 0.23000468823253634 | 0.3330004688232536 | 0.03283013813818313 | 20 | -0.05341106636001636 |
| negative_control_random_gene_modules_matched_size | 0.27286849507735583 | 0.2723980309423347 | 0.22452883263009848 | 0.3383544303797469 | 0.03500861144039061 | 20 | -0.053833944934793654 |
| negative_control_donor_shuffled_dlpfc_full | 0.27209751523675574 | 0.2646647913736522 | 0.22188935771214252 | 0.3395030473511486 | 0.0317194276749064 | 20 | -0.05460492477539375 |
| negative_control_module_gene_shuffled_matched_size | 0.27207172995780593 | 0.27073605250820443 | 0.23407876230661043 | 0.33495546179090485 | 0.03260943464768901 | 20 | -0.054630710054343556 |
| mtg_programming_plus_dlpfc_state_abundance | 0.2666490857946554 | 0.26436240037505865 | 0.22089076418190343 | 0.3377449601500234 | 0.03404287512309488 | 20 | -0.06005335421749408 |
| mtg_programming_only_same80 | 0.26612423816221287 | 0.26413970932958275 | 0.2189639006094702 | 0.3358368495077356 | 0.033899077366436756 | 20 | -0.06057820184993662 |
| negative_control_donor_shuffled_dlpfc_expression_modules | 0.2643696671354899 | 0.2619432723863104 | 0.22107829348335678 | 0.3254758556024379 | 0.030611356710792847 | 20 | -0.06233277287665956 |
| dlpfc_state_expression_modules_only | 0.17239943741209565 | 0.18248476324425694 | 0.09943272386310362 | 0.233033286451008 | 0.04246999798212341 | 20 | -0.15430300260005383 |
| dlpfc_state_modules_only | 0.1686964369432724 | 0.17577824660103145 | 0.0890576652601969 | 0.23543366150961093 | 0.0438568393985798 | 20 | -0.15800600306887708 |
| dlpfc_state_abundance_only | 0.14558087201125175 | 0.14863806844819505 | 0.09623066104078763 | 0.20109235818096577 | 0.024388838728702386 | 20 | -0.18112156800089774 |

## Delta summary

| comparison | primary_score | comparison_score | delta | comparison_model |
| --- | --- | --- | --- | --- |
| primary_minus_same80_mtg_programming | 0.2773150492264417 | 0.26612423816221287 | 0.011190811064228812 |  |
| primary_minus_best_negative_control | 0.2773150492264417 | 0.28139076418190345 | -0.004075714955461773 | negative_control_state_label_shuffled_within_donor |
| primary_minus_stage27c_locked | 0.2773150492264417 | 0.3267024400121495 | -0.04938739078570781 |  |

## Bootstrap summary

| comparison | bootstrap_iterations | delta_mean | delta_ci_low | delta_ci_high | ci_low_above_zero |
| --- | --- | --- | --- | --- | --- |
| mtg_programming_plus_dlpfc_state_modules_full_minus_mtg_programming_only_same80 | 500 | 0.00527583495092229 | -0.009148179651891297 | 0.019785205463101554 | False |
| mtg_programming_plus_dlpfc_state_modules_full_minus_negative_control_state_label_shuffled_within_donor | 500 | -0.00640253479598635 | -0.020458584378151793 | 0.005532240768239512 | False |
| mtg_programming_plus_dlpfc_state_modules_full_minus_stage27c_locked | 500 | -0.045251183165277466 | -0.1592038775954503 | 0.06995109053436281 | False |

## Lock gate decision

| robust_regional_support_pass | benchmark_lock_candidate_pass | new_locked_benchmark_pass | clean_external_validation_pass | primary_branch | primary_score | same80_mtg_programming_score | best_negative_control | best_negative_control_score | stage27c_locked_score | decision_basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | False | False | False | mtg_programming_plus_dlpfc_state_modules_full | 0.2773150492264417 | 0.26612423816221287 | negative_control_state_label_shuffled_within_donor | 0.28139076418190345 | 0.3267024400121495 | aggregate across predeclared seeds/latent dims, bootstrap deltas, negative controls, feature-source and claim-boundary audits |

## Claim boundary

Stage62 is regional/internal support only. It is not clean external validation, causal validation, therapeutic validation, validated gene ablation, or a new microglial subtype discovery.
