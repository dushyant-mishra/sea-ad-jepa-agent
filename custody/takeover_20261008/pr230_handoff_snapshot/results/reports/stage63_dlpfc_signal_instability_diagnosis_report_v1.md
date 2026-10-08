# Stage63 DLPFC signal instability diagnosis

## Bottom line

Stage63 confirms that Stage61's high corrected DLPFC score was split/seed fragile. Stage62 remains the controlling robustness audit: the DLPFC branch is not a locked benchmark, but selected module/state signatures can be carried forward as hypothesis-generating biology for Stage64 external support testing.

## Stage61 versus Stage62 discrepancy

| stage61_model | stage61_best_latent_dim | stage61_best_seed | stage61_corrected_best_score | stage62_model | stage62_aggregate_score | stage62_same80_mtg_score | stage62_best_negative_control | stage62_best_negative_control_score | stage27c_locked_score | stage62_minus_stage61 | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mtg_programming_plus_dlpfc_state_modules | 16 | 307 | 0.3433239568682606 | mtg_programming_plus_dlpfc_state_modules_full | 0.2773150492264417 | 0.2661242381622128 | negative_control_state_label_shuffled_within_donor | 0.2813907641819034 | 0.3267024400121495 | -0.06600890764181894 | single_seed_dim_stage61_gain_not_stable_under_repeated_stage62_audit |

## Target instability

| target | stage61_best_target_score | stage62_aggregate_target_score | stage62_target_sd | stage62_target_min | stage62_target_max | stage62_minus_stage61 | instability_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6e10/A_beta | 0.307219878105954 | 0.1646015002344116 | 0.06798060844645899 | 0.0543131739334271 | 0.307219878105954 | -0.1426183778715424 | stage61_high_score_not_stable |
| AT8 | 0.4521097046413502 | 0.4269210032817628 | 0.04032269630503999 | 0.363947491795593 | 0.4920534458509143 | -0.025188701359587395 | comparatively_stable |
| GFAP | 0.3189639006094702 | 0.23448429442100327 | 0.07838933726699415 | 0.0799109235818096 | 0.326347866854196 | -0.08447960618846695 | stage61_high_score_not_stable |
| Iba1 | 0.1443741209563994 | 0.07654594467885606 | 0.07322031229721179 | -0.0877637130801687 | 0.1655180496952649 | -0.06782817627754334 | stage61_high_score_not_stable |
| NeuN | 0.4939521800281293 | 0.4840225035161744 | 0.044431979915881874 | 0.3860525082044069 | 0.5377871542428505 | -0.009929676511954921 | comparatively_stable |

## Negative-control diagnosis

| negative_control | score | primary_score | delta_primary_minus_control | beats_primary | diagnostic_interpretation |
| --- | --- | --- | --- | --- | --- |
| negative_control_state_label_shuffled_within_donor | 0.2813907641819034 | 0.2773150492264417 | -0.004075714955461718 | True | state_or_donor_structure_can_match_real_branch |
| negative_control_expression_permuted_within_donor | 0.2802904360056258 | 0.2773150492264417 | -0.0029753867791841304 | True | tests whether expression-module values are exchangeable/noisy |
| negative_control_expression_permuted_within_state | 0.2732913736521331 | 0.2773150492264417 | 0.004023675574308605 | False | tests whether expression-module values are exchangeable/noisy |
| negative_control_random_gene_modules_matched_size | 0.2728684950773558 | 0.2773150492264417 | 0.004446554149085902 | False | tests module gene-set specificity |
| negative_control_donor_shuffled_dlpfc_full | 0.2720975152367557 | 0.2773150492264417 | 0.005217533989685996 | False | tests donor-alignment dependence |
| negative_control_module_gene_shuffled_matched_size | 0.2720717299578059 | 0.2773150492264417 | 0.005243319268635804 | False | tests module gene-set specificity |
| negative_control_donor_shuffled_dlpfc_expression_modules | 0.2643696671354899 | 0.2773150492264417 | 0.012945382090951751 | False | tests donor-alignment dependence |
| overall_diagnosis | 0.2813907641819034 | 0.2773150492264417 | -0.004075714955461718 | True | best_negative_control_exceeds_real_branch; do_not_lock_benchmark; likely split/state/donor-structure fragility |

## High-leverage donors

| analysis_label | donor_id | base_score | score_without_donor | influence_score_without_minus_base | abs_influence | high_leverage_cutoff |
| --- | --- | --- | --- | --- | --- | --- |
| stage61_best | H21.33.020 | 0.3433239568682607 | 0.3266601752677702 | -0.016663781600490535 | 0.016663781600490535 | 0.010482509286306733 |
| stage61_best | H21.33.042 | 0.3433239568682607 | 0.3598247322297955 | 0.01650077536153477 | 0.01650077536153477 | 0.010482509286306733 |
| stage61_best | H21.33.045 | 0.3433239568682607 | 0.3288315481986368 | -0.014492408669623924 | 0.014492408669623924 | 0.010482509286306733 |
| stage61_best | H21.33.017 | 0.3433239568682607 | 0.35707400194741973 | 0.013750045079159001 | 0.013750045079159001 | 0.010482509286306733 |
| stage61_best | H20.33.032 | 0.3433239568682607 | 0.35594936708860764 | 0.012625410220346911 | 0.012625410220346911 | 0.010482509286306733 |
| stage61_best | H20.33.012 | 0.3433239568682607 | 0.3546543330087634 | 0.011330376140502696 | 0.011330376140502696 | 0.010482509286306733 |
| stage61_best | H20.33.045 | 0.3433239568682607 | 0.332064264849075 | -0.011259692019185752 | 0.011259692019185752 | 0.010482509286306733 |
| stage61_best | H21.33.011 | 0.3433239568682607 | 0.33245374878286277 | -0.010870208085397959 | 0.010870208085397959 | 0.010482509286306733 |
| stage62_aggregate | H21.33.042 | 0.28477730895452413 | 0.30433300876338854 | 0.019555699808864402 | 0.019555699808864402 | 0.010864618269681643 |
| stage62_aggregate | H21.33.045 | 0.28477730895452413 | 0.2677799415774099 | -0.016997367377114214 | 0.016997367377114214 | 0.010864618269681643 |
| stage62_aggregate | H21.33.020 | 0.28477730895452413 | 0.26787244401168453 | -0.016904864942839604 | 0.016904864942839604 | 0.010864618269681643 |
| stage62_aggregate | H21.33.017 | 0.28477730895452413 | 0.29972249269717627 | 0.014945183742652135 | 0.014945183742652135 | 0.010864618269681643 |
| stage62_aggregate | H19.33.004 | 0.28477730895452413 | 0.29870009737098346 | 0.01392278841645933 | 0.01392278841645933 | 0.010864618269681643 |
| stage62_aggregate | H21.33.011 | 0.28477730895452413 | 0.2716358325219085 | -0.01314147643261565 | 0.01314147643261565 | 0.010864618269681643 |
| stage62_aggregate | H21.33.004 | 0.28477730895452413 | 0.27197176241480037 | -0.012805546539723767 | 0.012805546539723767 | 0.010864618269681643 |
| stage62_aggregate | H20.33.045 | 0.28477730895452413 | 0.27326192794547227 | -0.011515381009051862 | 0.011515381009051862 | 0.010864618269681643 |

## Signature handoff preview

| signature_type | signature_name | leave_one_out_score | estimated_positive_contribution | evidence_strength | handoff_status | allowed_claim | candidate_for_external_support | keep_for_supplement | drop_as_unstable | manual_review_required | recommended_stage64_test | disallowed_claim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| state_or_supertype | Micro-PVM_3-SEAAD | 0.2725740740740741 | 0.004740975152367599 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating state-stratified signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_family | lysosomal_endolysosomal | 0.274648382559775 | 0.002666666666666706 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating module signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_family | dam_lipid_trem2_apoe | 0.2749383497421472 | 0.0023766994842944755 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating module signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| state_or_supertype | Micro-PVM_1 | 0.2750813408345054 | 0.002233708391936262 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating state-stratified signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_family | complement_phagocytosis | 0.2751078293483356 | 0.0022072198781060703 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating module signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| state_or_supertype | Micro-PVM_1_1-SEAAD | 0.2753251289263947 | 0.0019899203000469656 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating state-stratified signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| state_or_supertype | Micro-PVM_2_1-SEAAD | 0.275374589779653 | 0.001940459446788667 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating state-stratified signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| state_or_supertype | Micro-PVM_2 | 0.2755478199718706 | 0.0017672292545710677 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating state-stratified signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_family | antigen_presentation | 0.2762637130801688 | 0.0010513361462728965 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating module signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_family | oxidative_stress_gene_preserved | 0.2763581809657759 | 0.0009568682606657664 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating module signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_family | interferon_inflammatory | 0.2765764181903422 | 0.0007386310360995019 | weak_positive_diagnostic | candidate_for_external_support | hypothesis-generating module signature only | True | False | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| state_or_supertype | Micro-PVM_2_2-SEAAD | 0.2782566807313643 | -0.0009416315049226021 | unstable_or_negative | keep_for_supplement | hypothesis-generating state-stratified signature only | False | True | False | False | external_microglia_signature_support_if_matching_dataset_available | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
