# Stage70 rare-microglia auxiliary-head robustness lock audit

## Bottom line

Stage70 freezes the Stage69 best condition (`rare_aux_pls4_w0p2`) and tests whether the internal gain survives repeated donor-held-out folds, stronger controls, ablations, bootstrap deltas, and target guards. This is not external validation.

## Exact reproduction

| condition | stage69_expected_score | stage70_reproduced_score | absolute_difference | exact_reproduction_tolerance | exact_reproduction_pass |
| --- | --- | --- | --- | --- | --- |
| rare_aux_pls4_w0p2 | 0.3591037979163019 | 0.3591037979163019 | 0.0 | 1e-06 | True |

## Lock-gate decision

| exact_stage69_reproduction_pass | mean_beats_stage27c | mean_reaches_material_rescue_threshold | mean_beats_no_aux | mean_beats_shuffled_aux | bootstrap_delta_vs_stage27c_positive | bootstrap_delta_vs_no_aux_positive | bootstrap_delta_vs_shuffled_aux_positive | target_guards_pass | beats_stage41c_unlocked | mean_rare_aux | mean_no_aux | mean_shuffled_aux | robustness_pass | benchmark_lock_candidate_pass | new_locked_benchmark_pass | clean_external_validation_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | False | True | True | True | False | 0.33568006174024184 | 0.31686845403521846 | 0.3157309457909375 | True | False | False | False |

## Repeated-seed summary

| condition | aux_condition_type | mean_pooled_oof_spearman | min_delta_vs_stage27c_target | iba1_spearman | n_targets | delta_vs_stage27c_mean | delta_vs_best_no_aux | delta_vs_best_shuffled_aux | seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_aux_pls4 | no_aux_baseline | 0.3409761863891726 | -0.0720470324194469 | 0.13350277873304828 | 5 | 0.014273746377023111 | 0.0 |  | 10 |
| no_aux_pls4 | no_aux_baseline | 0.3365760706150288 | -0.054676803506034544 | 0.09810278352117703 | 5 | 0.009873630602879324 | 0.0 |  | 11 |
| no_aux_pls4 | no_aux_baseline | 0.2784837577514137 | -0.1493440991802584 | -0.004273374525938983 | 5 | -0.04821868226073578 | 0.0 |  | 12 |
| no_aux_pls4 | no_aux_baseline | 0.3218918745913077 | -0.05285433132047812 | 0.03167931931222535 | 5 | -0.004810565420841795 | 0.0 |  | 13 |
| no_aux_pls4 | no_aux_baseline | 0.3194290945407912 | -0.050363071014422 | 0.03833827051919779 | 5 | -0.007273345471358272 | 0.0 |  | 14 |
| no_aux_pls4 | no_aux_baseline | 0.3398688282267716 | -0.028124798873510548 | 0.07803677978401036 | 5 | 0.013166388214622127 | 0.0 |  | 15 |
| no_aux_pls4 | no_aux_baseline | 0.28864050942070324 | -0.1476809090470346 | -0.04264390270695781 | 5 | -0.03806193059144625 | 0.0 |  | 16 |
| no_aux_pls4 | no_aux_baseline | 0.28968795172981543 | -0.07929781021951769 | -0.0632200538157514 | 5 | -0.03701448828233406 | 0.0 |  | 17 |
| no_aux_pls4 | no_aux_baseline | 0.3696784522720644 | -0.06269805409617615 | 0.20889794443410822 | 5 | 0.04297601225991493 | 0.0 |  | 18 |
| no_aux_pls4 | no_aux_baseline | 0.32874049556548357 | -0.05644933126764573 | 0.0855924760171427 | 5 | 0.002038055553334084 | 0.0 |  | 19 |
| no_aux_pls4 | no_aux_baseline | 0.2715797732848507 | -0.2323246468233161 | 0.05506863444552413 | 5 | -0.055122666727298764 | 0.0 |  | 20 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.37955357351607316 | -0.008079354540288908 | 0.17899944020510428 | 5 | 0.052851133503923675 |  |  | 10 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.36304025426472103 | -0.024480469751488987 | 0.0998652909380779 | 5 | 0.03633781425257154 |  |  | 11 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.33735093404562394 | -0.08432164970564304 | 0.14101123287606715 | 5 | 0.010648494033474454 |  |  | 12 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.30545587212513825 | -0.08775152539267067 | 0.03771540444972098 | 5 | -0.021246567887011236 |  |  | 13 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.35006515983820413 | -0.04562389227654018 | 0.09364826353976258 | 5 | 0.023362719826054645 |  |  | 14 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.3446577459653364 | -0.07366642561416198 | 0.12355232661715022 | 5 | 0.017955305953186895 |  |  | 15 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.3037425838475568 | -0.06370269559828501 | -0.036669098005674236 | 5 | -0.022959856164592674 |  |  | 16 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.3214889662850572 | -0.09066165587482333 | 0.09513392590377329 | 5 | -0.005213473727092299 |  |  | 17 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.34773961467615405 | -0.07468768488510871 | 0.21082215102946775 | 5 | 0.021037174664004565 |  |  | 18 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.30787609745425815 | -0.054463462597067136 | 0.007676182775792021 | 5 | -0.01882634255789134 |  |  | 19 |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.33150987712453767 | -0.053269135663661565 | 0.08877007163469373 | 5 | 0.00480743711238818 |  |  | 20 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.3378007699936069 | -0.07929744517256979 | 0.13080923055776075 | 5 | 0.011098329981457433 |  | 0.0 | 10 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.34550208986481773 | -0.05256034536559817 | 0.0433941481264556 | 5 | 0.018799649852668243 |  | 0.0 | 11 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.3008992721372755 | -0.09058490619985912 | 0.07874350785237329 | 5 | -0.025803167874873967 |  | 0.0 | 12 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.2934427509623546 | -0.09418249153021246 | -0.019404595844700695 | 5 | -0.03325968904979487 |  | 0.0 | 13 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.32991260790144744 | -0.07708040307697889 | 0.0683830799831333 | 5 | 0.0032101678892979546 |  | 0.0 | 14 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.32461119528108384 | -0.10578064598866127 | 0.08185506219524616 | 5 | -0.0020912447310656446 |  | 0.0 | 15 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.3032033055940834 | -0.06233147839482464 | -0.008141937253952524 | 5 | -0.02349913441806606 |  | 0.0 | 16 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.2721900312968676 | -0.10306863147962159 | -0.08699087507585529 | 5 | -0.0545124087152819 |  | 0.0 | 17 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.3379416704691188 | -0.08753805774926027 | 0.19186365236360983 | 5 | 0.01123923045696934 |  | 0.0 | 18 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.31253540714112904 | -0.06708337387564975 | 0.0611157823903758 | 5 | -0.014167032871020446 |  | 0.0 | 19 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.31500130305852847 | -0.06594246095296435 | 0.03287105321996529 | 5 | -0.011701136953621016 |  | 0.0 | 20 |

## Bootstrap delta CIs

| comparison | mean_delta | ci_lower_2p5 | ci_upper_97p5 | bootstrap_iterations |
| --- | --- | --- | --- | --- |
| rare_aux_vs_no_aux | 0.018664624329619378 | 0.00043516738079989604 | 0.035741999654947294 | 1000 |
| rare_aux_vs_shuffled_aux | 0.020163418571363133 | 0.010504680383650641 | 0.030436819506625423 | 1000 |
| rare_aux_vs_stage27c | 0.008914351064863098 | -0.004341274075937947 | 0.022128152835915228 | 1000 |

## Target guards

| target | mean_repeated_spearman | median_repeated_spearman | min_repeated_spearman | stage27c_target_mean_delta | guard_no_catastrophic_collapse | guard_mean_not_worse_than_stage27c_by_0p05 |
| --- | --- | --- | --- | --- | --- | --- |
| 6e10/A_beta | 0.34445641608529054 | 0.33567300018400104 | 0.28027380580426936 | 0.009719147683954018 | True | True |
| AT8 | 0.48014953385520176 | 0.48281591738226315 | 0.43777815378398 | -0.04829027580360156 | True | True |
| GFAP | 0.28456936728465726 | 0.2841187018880362 | 0.2276105838199636 | -0.01772890142041508 | True | True |
| Iba1 | 0.09459319926944869 | 0.09513392590377329 | -0.036669098005674236 | 0.07851544286568239 | True | True |
| NeuN | 0.47463179220661117 | 0.4668013682036068 | 0.4381351841688636 | 0.022672695314842426 | True | True |

## Stronger negative controls

| condition | aux_condition_type | mean_pooled_oof_spearman | min_delta_vs_stage27c_target | iba1_spearman | n_targets | delta_vs_stage27c_mean | delta_vs_best_no_aux | delta_vs_best_shuffled_aux | control_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_aux_baseline | no_aux_baseline | 0.34006364315332804 | -0.04615477264337389 | -0.03007701623960759 | 5 | 0.013361203141178557 | 0.0 |  | no_aux_baseline |
| shuffled_aux_train_rows | shuffled_aux_negative_control | 0.3220875496982861 | -0.03679140893844063 | 0.01368149795949827 | 5 | -0.004614890313863362 |  | 0.0 | shuffled_aux_train_rows |
| donor_shuffled_aux_targets | rare_microglia_auxiliary_head | 0.3219783244454288 | -0.09895664559735166 | -0.08287888919358537 | 5 | -0.004724115566720699 |  |  | donor_shuffled_aux_targets |
| random_matched_aux_targets | rare_microglia_auxiliary_head | 0.32609824176266733 | -0.06454529839796225 | -0.048467541994195944 | 5 | -0.0006041982494821574 |  |  | random_matched_aux_targets |
| mean_module_aux_targets | rare_microglia_auxiliary_head | 0.3348807496027001 | -0.05710199639927148 | -0.041024239995505175 | 5 | 0.008178309590550603 |  |  | mean_module_aux_targets |

## Auxiliary ablations

| condition | aux_condition_type | mean_pooled_oof_spearman | min_delta_vs_stage27c_target | iba1_spearman | n_targets | delta_vs_stage27c_mean | delta_vs_best_no_aux | delta_vs_best_shuffled_aux | ablation | n_aux_features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rare_aux_ablation__all | rare_microglia_auxiliary_head | 0.3591037979163019 | -0.0036354921401640095 | 0.08971457470258709 | 5 | 0.03240135790415244 |  |  | all | 78 |
| rare_aux_ablation__top_tail_only | rare_microglia_auxiliary_head | 0.344569638206795 | -0.002957031728908155 | 0.02719083791358464 | 5 | 0.017867198194645495 |  |  | top_tail_only | 48 |
| rare_aux_ablation__mtg_only | rare_microglia_auxiliary_head | 0.34439387950014716 | -0.0021532118483924157 | 0.013924544555373885 | 5 | 0.017691439487997673 |  |  | mtg_only | 39 |
| rare_aux_ablation__dlpfc_only | rare_microglia_auxiliary_head | 0.3386985773420352 | -0.010460601351902632 | 0.03032006283548321 | 5 | 0.011996137329885692 |  |  | dlpfc_only | 39 |
| rare_aux_ablation__dam_lipid_only | rare_microglia_auxiliary_head | 0.33450587401016074 | -0.04246856593926037 | -0.02639080953549407 | 5 | 0.0078034339980112555 |  |  | dam_lipid_only | 12 |
| rare_aux_ablation__fraction_only | rare_microglia_auxiliary_head | 0.33419645074754156 | -0.041516633438747536 | -0.02543887703498124 | 5 | 0.007494010735392076 |  |  | fraction_only | 16 |
| rare_aux_ablation__lysosomal_only | rare_microglia_auxiliary_head | 0.33289527619305254 | -0.05285880791294299 | -0.03678105150917669 | 5 | 0.00619283618090305 |  |  | lysosomal_only | 12 |
| rare_aux_ablation__disease_program_only | rare_microglia_auxiliary_head | 0.331498226400576 | -0.03793169614958219 | -0.021853939745815888 | 5 | 0.004795786388426537 |  |  | disease_program_only | 16 |
| rare_aux_ablation__complement_only | rare_microglia_auxiliary_head | 0.3280997832876835 | -0.06081858392786944 | -0.04474082752410315 | 5 | 0.0013973432755340354 |  |  | complement_only | 12 |
| rare_aux_ablation__variance_only | rare_microglia_auxiliary_head | 0.3269099146055116 | -0.054833561504432374 | -0.03875580510066608 | 5 | 0.00020747459336212248 |  |  | variance_only | 12 |
| rare_aux_ablation__antigen_only | rare_microglia_auxiliary_head | 0.32335265815793435 | -0.07383170374870977 | -0.05775394734494347 | 5 | -0.003349781854215139 |  |  | antigen_only | 18 |

## Claim boundary

| stage70_run_is_internal_robustness_audit | frozen_stage69_setup | no_new_feature_tuning | donor_heldout_only | stronger_negative_controls_run | predeclared_auxiliary_ablations_run | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_new_microglia_subtype_claim | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True |
