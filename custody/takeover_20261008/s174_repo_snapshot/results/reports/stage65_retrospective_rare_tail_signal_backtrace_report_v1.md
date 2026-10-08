# Stage65 retrospective rare-tail signal backtrace

## Bottom line

Stage65 supports the explanation that prior internal attempts may have averaged away sparse Micro-PVM disease-program signals. This is not a benchmark rescue and does not revise Stage27C. It creates a frozen Stage66 external-support handoff.

## Prior stage context

| stage | path | best_model_variant | best_score | delta_vs_stage27c | interpretation |
| --- | --- | --- | --- | --- | --- |
| Stage53 | results/tables/stage53_branch_comparison_v1.csv | all_branches_jepa | 0.318906550572036 | -0.0077958894401135015 | did_not_exceed_stage27c |
| Stage54 | results/tables/stage54_branch_comparison_v1.csv | programming_plus_state_specific_module_programming | 0.3250906145590767 | -0.0016118254530728127 | did_not_exceed_stage27c |
| Stage55 | results/tables/stage55_branch_comparison_v1.csv | programming_plus_state_module_programming | 0.3260301711045864 | -0.0006722689075631116 | did_not_exceed_stage27c |
| Stage56 | results/tables/stage56_branch_comparison_v1.csv | nested_target_gated_programming_vs_state_module | 0.3225068340589248 | -0.0041956059532247125 | did_not_exceed_stage27c |
| Stage57 | results/tables/stage57_branch_comparison_v1.csv | programming_plus_repaired_state_modules_full | 0.3256697377746279 | -0.00103270223752161 | did_not_exceed_stage27c |
| Stage60 | results/tables/stage60_branch_comparison_v1.csv | programming_plus_gene_preserved_state_modules | 0.3245884377847525 | -0.002114002227396994 | did_not_exceed_stage27c |
| Stage61 | results/tables/stage61_branch_comparison_v1.csv | mtg_programming_plus_dlpfc_state_modules | 0.3433239568682606 | 0.01662151685611113 | exceeded_stage27c_in_stage_specific_context |
| Stage62 | results/tables/stage62_branch_comparison_v1.csv | negative_control_state_label_shuffled_within_donor | 0.2813907641819034 | -0.04531167583024609 | did_not_exceed_stage27c |

## Strongest tail-over-mean backtrace results

| dataset | feature | target | best_tail_metric | best_tail_spearman | mean_spearman | best_tail_minus_mean_abs_spearman | any_tail_beats_mean | n_tail_metrics_beating_mean | supports_dilution_hypothesis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DLPFC | disease_program_score | NeuN | variance | -0.3873652133145804 | -0.0457805907172995 | 0.3415846225972809 | True | 8 | True |
| MTG | disease_program_score | NeuN | variance | -0.4713576997063887 | -0.1810266275184772 | 0.2903310721879115 | True | 8 | True |
| DLPFC | lysosomal_endolysosomal | NeuN | variance | -0.5109704641350211 | -0.2395921237693389 | 0.2713783403656822 | True | 8 | True |
| DLPFC | lysosomal_endolysosomal | AT8 | top_1pct_mean | 0.4338490389123301 | 0.2187763713080169 | 0.21507266760431323 | True | 7 | True |
| DLPFC | disease_program_score | AT8 | top_1pct_mean | 0.3151429910923581 | 0.1112048757618378 | 0.2039381153305203 | True | 8 | True |
| DLPFC | dam_lipid_trem2_apoe | NeuN | top_1pct_mean | -0.2764181903422409 | -0.0745194561650257 | 0.2018987341772152 | True | 8 | True |
| DLPFC | lysosomal_endolysosomal | 6e10/A_beta | top_1pct_mean | 0.363877168307548 | 0.1793248945147679 | 0.1845522737927801 | True | 7 | True |
| MTG | antigen_presentation | GFAP | variance | 0.2912827781715095 | 0.1205021767743242 | 0.1707806013971853 | True | 8 | True |
| DLPFC | dam_lipid_trem2_apoe | AT8 | top_1pct_mean | 0.3617440225035162 | 0.2023909985935302 | 0.159353023909986 | True | 8 | True |
| DLPFC | disease_program_score | GFAP | top_1pct_mean | 0.2854195968120019 | 0.1274027191748711 | 0.15801687763713082 | True | 8 | True |
| MTG | complement_phagocytosis | GFAP | variance | 0.4346461476156727 | 0.2876581958084439 | 0.14698795180722884 | True | 6 | True |
| MTG | lysosomal_endolysosomal | NeuN | variance | -0.4892173736964666 | -0.3464614761567278 | 0.14275589753973883 | True | 8 | True |
| MTG | lysosomal_endolysosomal | GFAP | q95 | 0.4174951908474233 | 0.3085957274476055 | 0.10889946339981782 | True | 7 | True |
| DLPFC | lysosomal_endolysosomal | Iba1 | top_1pct_mean | 0.3689873417721518 | 0.2652133145804032 | 0.10377402719174861 | True | 5 | True |
| MTG | lysosomal_endolysosomal | 6e10/A_beta | q90 | 0.4366305558367926 | 0.3355269818770882 | 0.10110357395970443 | True | 8 | True |
| MTG | lysosomal_endolysosomal | AT8 | fraction_high_global_q95 | 0.4190868638651647 | 0.3357092234484155 | 0.08337764041674922 | True | 8 | True |
| MTG | interferon_inflammatory | 6e10/A_beta | fraction_high_global_q95 | 0.3141237217778678 | 0.2338969322668826 | 0.08022678951098519 | True | 4 | True |
| MTG | dam_lipid_trem2_apoe | GFAP | q95 | 0.3673585096689278 | 0.2913030272349903 | 0.0760554824339375 | True | 6 | True |
| DLPFC | disease_program_score | 6e10/A_beta | q99 | 0.2571964369432724 | 0.1828176277543366 | 0.07437880918893577 | True | 8 | True |
| MTG | interferon_inflammatory | GFAP | q90 | 0.3140832236509061 | 0.2475852991799129 | 0.06649792447099317 | True | 6 | True |

## High-leverage donor rare-burden summary

| analysis_label | rare_burden_dataset | n_high_leverage_donors_with_burden | mean_abs_influence | mean_rare_burden_fraction_high_q95 | spearman_abs_influence_vs_rare_burden | spearman_abs_influence_vs_tail_variance |
| --- | --- | --- | --- | --- | --- | --- |
| stage61_best | DLPFC | 8 | 0.01343658714703015 | 0.060504197966612 | 0.7857142857142858 | 0.5476190476190477 |
| stage61_best | MTG | 8 | 0.01343658714703015 | 0.06731162233202219 | 0.4523809523809524 | 0.30952380952380953 |
| stage62_aggregate | DLPFC | 8 | 0.014973538533665088 | 0.06517277520117637 | 0.6190476190476191 | 0.11904761904761905 |
| stage62_aggregate | MTG | 8 | 0.014973538533665088 | 0.06475777156781212 | 0.28571428571428575 | -0.07142857142857144 |

## Prior feature dilution audit

| inventory | exists | n_rows | has_tail_or_rare_feature_terms | tail_term_count_proxy | mean_or_state_average_term_count_proxy | retrospective_interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| stage55_state_feature_inventory | True | 16600 | True | 2 | 2 | included_some_tail_like_terms_but_not_full_stage64_rare_burden_suite |
| stage57_repaired_state_module_feature_inventory | True | 7476 | True | 1 | 2 | included_some_tail_like_terms_but_not_full_stage64_rare_burden_suite |
| stage61_dlpfc_feature_inventory | True | 120 | True | 1 | 3 | included_some_tail_like_terms_but_not_full_stage64_rare_burden_suite |

## Mechanism interpretation

| mechanism_or_feature | target | dataset | best_tail_metric | tail_spearman | mean_spearman | interpretation | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- |
| disease_program_score | NeuN | DLPFC | variance | -0.3873652133145804 | -0.0457805907172995 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| disease_program_score | NeuN | MTG | variance | -0.4713576997063887 | -0.1810266275184772 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | NeuN | DLPFC | variance | -0.5109704641350211 | -0.2395921237693389 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | AT8 | DLPFC | top_1pct_mean | 0.4338490389123301 | 0.2187763713080169 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| disease_program_score | AT8 | DLPFC | top_1pct_mean | 0.3151429910923581 | 0.1112048757618378 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| dam_lipid_trem2_apoe | NeuN | DLPFC | top_1pct_mean | -0.2764181903422409 | -0.0745194561650257 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | 6e10/A_beta | DLPFC | top_1pct_mean | 0.363877168307548 | 0.1793248945147679 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| antigen_presentation | GFAP | MTG | variance | 0.2912827781715095 | 0.1205021767743242 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| dam_lipid_trem2_apoe | AT8 | DLPFC | top_1pct_mean | 0.3617440225035162 | 0.2023909985935302 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| disease_program_score | GFAP | DLPFC | top_1pct_mean | 0.2854195968120019 | 0.1274027191748711 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| complement_phagocytosis | GFAP | MTG | variance | 0.4346461476156727 | 0.2876581958084439 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | NeuN | MTG | variance | -0.4892173736964666 | -0.3464614761567278 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | GFAP | MTG | q95 | 0.4174951908474233 | 0.3085957274476055 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | Iba1 | DLPFC | top_1pct_mean | 0.3689873417721518 | 0.2652133145804032 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | 6e10/A_beta | MTG | q90 | 0.4366305558367926 | 0.3355269818770882 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| lysosomal_endolysosomal | AT8 | MTG | fraction_high_global_q95 | 0.4190868638651647 | 0.3357092234484155 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| interferon_inflammatory | 6e10/A_beta | MTG | fraction_high_global_q95 | 0.3141237217778678 | 0.2338969322668826 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| dam_lipid_trem2_apoe | GFAP | MTG | q95 | 0.3673585096689278 | 0.2913030272349903 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| disease_program_score | 6e10/A_beta | DLPFC | q99 | 0.2571964369432724 | 0.1828176277543366 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| interferon_inflammatory | GFAP | MTG | q90 | 0.3140832236509061 | 0.2475852991799129 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| dam_lipid_trem2_apoe | 6e10/A_beta | DLPFC | q95 | 0.3171120487576184 | 0.2510079699953118 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| interferon_inflammatory | AT8 | MTG | fraction_high_global_q95 | 0.4409031082312444 | 0.381046876581958 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| oxidative_stress_gene_preserved | GFAP | MTG | q99 | 0.3064493267186393 | 0.2527893084944821 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| oxidative_stress_gene_preserved | Iba1 | DLPFC | q95 | 0.3418424753867792 | 0.290014064697609 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |
| disease_program_score | AT8 | MTG | q90 | 0.4293611420471803 | 0.3787587324086262 | tail_metric_stronger_than_mean_consistent_with_signal_dilution | external_support_test_with_frozen_tail_signature |

_Showing 25 of 50 rows._
