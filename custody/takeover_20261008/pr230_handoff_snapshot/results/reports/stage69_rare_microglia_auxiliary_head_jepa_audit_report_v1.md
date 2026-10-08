# Stage69 rare-microglia auxiliary-head JEPA audit

## Bottom line

Stage69 tests whether frozen rare/high-tail microglia donor features improve donor-held-out pathology inference when used as auxiliary targets in a low-capacity shared-latent model. This is a proxy for adding a rare-microglia auxiliary head to the JEPA latent; it is not a new external validation or causal/therapeutic claim.

## Pass/fail

| stage69_run | inputs_found | aux_target_table_written | model_registry_written | oof_predictions_written | target_metrics_written | mean_metrics_written | negative_controls_written | target_guards_written | reports_written | docs_updated | best_rare_aux_condition | best_rare_aux_mean_pooled_oof_spearman | best_rare_aux_delta_vs_stage27c | best_rare_aux_delta_vs_best_no_aux | best_rare_aux_delta_vs_best_shuffled_aux | beats_stage27c | reaches_material_rescue_threshold | beats_best_no_aux | beats_best_shuffled_aux | iba1_improved_vs_stage27c | target_level_guard_pass | stage69_run_is_internal_auxiliary_head_audit | auxiliary_targets_pathology_blind | donor_heldout_only | negative_shuffled_aux_controls_run | no_new_candidate_selection | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_new_microglia_subtype_claim | no_benchmark_lock_claim | safety_audit_pass | stage69_run_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | rare_aux_pls4_w0p2 | 0.3591037979163019 | 0.03240135790415244 | 0.019040154762973882 | 0.014524542239349736 | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True | True |

## Best conditions

| condition | aux_condition_type | mean_pooled_oof_spearman | min_delta_vs_stage27c_target | iba1_spearman | n_targets | delta_vs_stage27c_mean | delta_vs_best_no_aux | delta_vs_best_shuffled_aux |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.3591037979163019 | -0.0036354921401640095 | 0.08971457470258709 | 5 | 0.03240135790415244 | 0.019040154762973882 | 0.014524542239349736 |
| shuffled_aux_pls8_w0p2 | shuffled_aux_negative_control | 0.3445792556769522 | -0.030356743911458792 | -0.014278987507692492 | 5 | 0.017876815664802703 | 0.004515612523624146 | 0.0 |
| rare_aux_pls6_w0p1 | rare_microglia_auxiliary_head | 0.3440717699806878 | -0.033263176120471374 | -0.017185419716705078 | 5 | 0.017369329968538294 | 0.004008126827359737 | -0.0005074856962644092 |
| rare_aux_pls6_w0p05 | rare_microglia_auxiliary_head | 0.34084340873749325 | -0.02448311784446472 | -0.008405361440698419 | 5 | 0.014140968725343761 | 0.000779765584165204 | -0.003735846939458942 |
| no_aux_pls4 | no_aux_baseline | 0.34006364315332804 | -0.04615477264337389 | -0.03007701623960759 | 5 | 0.013361203141178557 | 0.0 | -0.004515612523624146 |
| shuffled_aux_pls6_w0p2 | shuffled_aux_negative_control | 0.33897511430651767 | -0.02225771148791955 | -0.00296719385798149 | 5 | 0.01227267429436818 | -0.001088528846810377 | -0.005604141370434523 |
| shuffled_aux_pls8_w0p1 | shuffled_aux_negative_control | 0.33879387565869046 | -0.021019703853237176 | -0.004941947449470877 | 5 | 0.012091435646540971 | -0.0012697674946375859 | -0.005785380018261732 |
| shuffled_aux_pls6_w0p05 | shuffled_aux_negative_control | 0.33852875487045936 | -0.01989561334731245 | -0.0038178569435461493 | 5 | 0.011826314858309872 | -0.001534888282868685 | -0.006050500806492831 |
| rare_aux_pls6_w0p2 | rare_microglia_auxiliary_head | 0.335640258797479 | -0.038893755591589835 | -0.022815999187823535 | 5 | 0.00893781878532951 | -0.004423384355849047 | -0.008938996879473193 |
| shuffled_aux_pls6_w0p1 | shuffled_aux_negative_control | 0.335400118626751 | -0.04572944110059157 | -0.02965168469682527 | 5 | 0.008697678614601523 | -0.004663524526577034 | -0.00917913705020118 |
| rare_aux_pls2_w0p1 | rare_microglia_auxiliary_head | 0.334016259155253 | -0.05338278469231528 | 0.08244343070930824 | 5 | 0.007313819143103528 | -0.006047383998075029 | -0.010562996521699175 |
| shuffled_aux_pls4_w0p1 | shuffled_aux_negative_control | 0.3337284210681742 | -0.01773857480891635 | -0.0016608184051500488 | 5 | 0.007025981056024699 | -0.006335222085153858 | -0.010850834608778004 |
| shuffled_aux_pls4_w0p05 | shuffled_aux_negative_control | 0.3304980841576476 | -0.06878848688429072 | -0.052710730480524416 | 5 | 0.0037956441454981005 | -0.009565558995680457 | -0.014081171519304603 |
| rare_aux_pls4_w0p05 | rare_microglia_auxiliary_head | 0.32798943496004473 | -0.0859131449520269 | -0.0698353885482606 | 5 | 0.001286994947895248 | -0.012074208193283309 | -0.016589820716907455 |
| rare_aux_pls2_w0p2 | rare_microglia_auxiliary_head | 0.3276172240344348 | -0.12754059053012412 | 0.1264449915042897 | 5 | 0.0009147840222852865 | -0.01244641911889327 | -0.016962031642517417 |

## Target-level metrics

| condition | aux_condition_type | target | n_donors | pooled_oof_spearman | stage27c_target_spearman | delta_vs_stage27c_target |
| --- | --- | --- | --- | --- | --- | --- |
| no_aux_pls2 | no_aux_baseline | 6e10/A_beta | 84 | 0.3632478127505821 | 0.3347372684013365 | 0.028510544349245603 |
| no_aux_pls2 | no_aux_baseline | AT8 | 84 | 0.49185341933615073 | 0.5284398096588033 | -0.036586390322652595 |
| no_aux_pls2 | no_aux_baseline | GFAP | 84 | 0.29923748161492164 | 0.3022982687050723 | -0.003060787090150674 |
| no_aux_pls2 | no_aux_baseline | Iba1 | 84 | -0.0531664428477912 | 0.0160777564037663 | -0.0692441992515575 |
| no_aux_pls2 | no_aux_baseline | NeuN | 84 | 0.46530965084382486 | 0.4519590968917688 | 0.013350553952056088 |
| no_aux_pls4 | no_aux_baseline | 6e10/A_beta | 84 | 0.37823879939022464 | 0.3347372684013365 | 0.04350153098888815 |
| no_aux_pls4 | no_aux_baseline | AT8 | 84 | 0.553562937936054 | 0.5284398096588033 | 0.025123128277250717 |
| no_aux_pls4 | no_aux_baseline | GFAP | 84 | 0.314579098692641 | 0.3022982687050723 | 0.012280829987568687 |
| no_aux_pls4 | no_aux_baseline | Iba1 | 84 | -0.03007701623960759 | 0.0160777564037663 | -0.04615477264337389 |
| no_aux_pls4 | no_aux_baseline | NeuN | 84 | 0.4840143959873281 | 0.4519590968917688 | 0.03205529909555932 |
| no_aux_pls6 | no_aux_baseline | 6e10/A_beta | 84 | 0.34828721324601986 | 0.3347372684013365 | 0.01354994484468336 |
| no_aux_pls6 | no_aux_baseline | AT8 | 84 | 0.5439024717817534 | 0.5284398096588033 | 0.01546266212295011 |
| no_aux_pls6 | no_aux_baseline | GFAP | 84 | 0.30196150471320976 | 0.3022982687050723 | -0.00033676399186255424 |
| no_aux_pls6 | no_aux_baseline | Iba1 | 84 | -0.003007701623960759 | 0.0160777564037663 | -0.01908545802772706 |
| no_aux_pls6 | no_aux_baseline | NeuN | 84 | 0.44312118489395175 | 0.4519590968917688 | -0.008837911997817027 |
| no_aux_pls8 | no_aux_baseline | 6e10/A_beta | 84 | 0.32062479127786864 | 0.3347372684013365 | -0.01411247712346786 |
| no_aux_pls8 | no_aux_baseline | AT8 | 84 | 0.5332800095219407 | 0.5284398096588033 | 0.004840199863137329 |
| no_aux_pls8 | no_aux_baseline | GFAP | 84 | 0.28687304963347265 | 0.3022982687050723 | -0.01542521907159966 |
| no_aux_pls8 | no_aux_baseline | Iba1 | 84 | -0.0018532302935515793 | 0.0160777564037663 | -0.01793098669731788 |
| no_aux_pls8 | no_aux_baseline | NeuN | 84 | 0.408851094170825 | 0.4519590968917688 | -0.04310800272094378 |
| rare_aux_pls2_w0p05 | rare_microglia_auxiliary_head | 6e10/A_beta | 84 | 0.3604218091881089 | 0.3347372684013365 | 0.025684540786772403 |
| rare_aux_pls2_w0p05 | rare_microglia_auxiliary_head | AT8 | 84 | 0.4853523509178478 | 0.5284398096588033 | -0.04308745874095554 |
| rare_aux_pls2_w0p05 | rare_microglia_auxiliary_head | GFAP | 84 | 0.30800701322502394 | 0.3022982687050723 | 0.005708744519951625 |
| rare_aux_pls2_w0p05 | rare_microglia_auxiliary_head | Iba1 | 84 | 0.0031190979804037503 | 0.0160777564037663 | -0.01295865842336255 |
| rare_aux_pls2_w0p05 | rare_microglia_auxiliary_head | NeuN | 84 | 0.44474152015272844 | 0.4519590968917688 | -0.007217576739040332 |
| rare_aux_pls2_w0p1 | rare_microglia_auxiliary_head | 6e10/A_beta | 84 | 0.2813544837090212 | 0.3347372684013365 | -0.05338278469231528 |
| rare_aux_pls2_w0p1 | rare_microglia_auxiliary_head | AT8 | 84 | 0.47718044715839225 | 0.5284398096588033 | -0.051259362500411076 |
| rare_aux_pls2_w0p1 | rare_microglia_auxiliary_head | GFAP | 84 | 0.3721481370337858 | 0.3022982687050723 | 0.06984986832871348 |
| rare_aux_pls2_w0p1 | rare_microglia_auxiliary_head | Iba1 | 84 | 0.08244343070930824 | 0.0160777564037663 | 0.06636567430554194 |
| rare_aux_pls2_w0p1 | rare_microglia_auxiliary_head | NeuN | 84 | 0.4569547971657576 | 0.4519590968917688 | 0.0049957002739888234 |
| rare_aux_pls2_w0p2 | rare_microglia_auxiliary_head | 6e10/A_beta | 84 | 0.2875635883104407 | 0.3347372684013365 | -0.047173680090895787 |
| rare_aux_pls2_w0p2 | rare_microglia_auxiliary_head | AT8 | 84 | 0.4008992191286792 | 0.5284398096588033 | -0.12754059053012412 |
| rare_aux_pls2_w0p2 | rare_microglia_auxiliary_head | GFAP | 84 | 0.37646201747940194 | 0.3022982687050723 | 0.07416374877432963 |
| rare_aux_pls2_w0p2 | rare_microglia_auxiliary_head | Iba1 | 84 | 0.1264449915042897 | 0.0160777564037663 | 0.1103672351005234 |
| rare_aux_pls2_w0p2 | rare_microglia_auxiliary_head | NeuN | 84 | 0.44671630374936244 | 0.4519590968917688 | -0.005242793142406332 |
| rare_aux_pls4_w0p05 | rare_microglia_auxiliary_head | 6e10/A_beta | 84 | 0.3555497385302251 | 0.3347372684013365 | 0.020812470128888594 |
| rare_aux_pls4_w0p05 | rare_microglia_auxiliary_head | AT8 | 84 | 0.5438518404077791 | 0.5284398096588033 | 0.015412030748975791 |
| rare_aux_pls4_w0p05 | rare_microglia_auxiliary_head | GFAP | 84 | 0.3219714290337203 | 0.3022982687050723 | 0.019673160328647965 |
| rare_aux_pls4_w0p05 | rare_microglia_auxiliary_head | Iba1 | 84 | -0.0698353885482606 | 0.0160777564037663 | -0.0859131449520269 |
| rare_aux_pls4_w0p05 | rare_microglia_auxiliary_head | NeuN | 84 | 0.48840955537675984 | 0.4519590968917688 | 0.036450458484991066 |

## Target guards for rare-auxiliary conditions

| condition | mean_pooled_oof_spearman | beats_best_no_aux | beats_best_shuffled_aux | beats_stage27c_mean | reaches_material_rescue_threshold | iba1_improved_vs_stage27c | target_level_guard_pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rare_aux_pls2_w0p05 | 0.3203283582928226 | False | False | False | False | False | True |
| rare_aux_pls2_w0p1 | 0.334016259155253 | False | False | True | True | True | False |
| rare_aux_pls2_w0p2 | 0.3276172240344348 | False | False | True | False | True | False |
| rare_aux_pls4_w0p05 | 0.32798943496004473 | False | False | True | False | False | False |
| rare_aux_pls4_w0p1 | 0.3259626210942552 | False | False | False | False | False | False |
| rare_aux_pls4_w0p2 | 0.3591037979163019 | True | True | True | True | True | True |
| rare_aux_pls6_w0p05 | 0.34084340873749325 | True | False | True | True | False | True |
| rare_aux_pls6_w0p1 | 0.3440717699806878 | True | False | True | True | False | True |
| rare_aux_pls6_w0p2 | 0.335640258797479 | False | False | True | True | False | True |
| rare_aux_pls8_w0p05 | 0.3251612754297236 | False | False | False | False | False | True |
| rare_aux_pls8_w0p1 | 0.3215416503933525 | False | False | False | False | False | True |
| rare_aux_pls8_w0p2 | 0.32220363166207244 | False | False | False | False | False | True |

## Auxiliary target learnability

| condition | aux_condition_type | mean_aux_oof_spearman | median_aux_oof_spearman | n_aux_target_fold_contexts |
| --- | --- | --- | --- | --- |
| rare_aux_pls4_w0p2 | rare_microglia_auxiliary_head | 0.4217487913201056 | 0.45833333333333337 | 1950 |
| rare_aux_pls2_w0p2 | rare_microglia_auxiliary_head | 0.41926460862307846 | 0.4191176470588236 | 1950 |
| rare_aux_pls6_w0p05 | rare_microglia_auxiliary_head | 0.41715456286223196 | 0.45857843137254906 | 1950 |
| rare_aux_pls8_w0p2 | rare_microglia_auxiliary_head | 0.4119378874295869 | 0.39436274509803926 | 1950 |
| rare_aux_pls6_w0p1 | rare_microglia_auxiliary_head | 0.4115438183720439 | 0.44240196078431376 | 1950 |
| rare_aux_pls2_w0p1 | rare_microglia_auxiliary_head | 0.4072611111500476 | 0.4227941176470589 | 1950 |
| rare_aux_pls8_w0p1 | rare_microglia_auxiliary_head | 0.40638996173505715 | 0.40527107348244507 | 1950 |
| rare_aux_pls8_w0p05 | rare_microglia_auxiliary_head | 0.406248295108401 | 0.42401960784313725 | 1950 |
| rare_aux_pls4_w0p1 | rare_microglia_auxiliary_head | 0.4061789069415283 | 0.45098039215686275 | 1950 |
| rare_aux_pls6_w0p2 | rare_microglia_auxiliary_head | 0.4045678754829749 | 0.4264705882352942 | 1950 |
| rare_aux_pls4_w0p05 | rare_microglia_auxiliary_head | 0.3996280079165057 | 0.4266013673301507 | 1950 |
| rare_aux_pls2_w0p05 | rare_microglia_auxiliary_head | 0.38963948554328043 | 0.4068627450980392 | 1950 |
| shuffled_aux_pls4_w0p2 | shuffled_aux_negative_control | 0.029484189268724603 | 0.041421568627450986 | 1950 |
| shuffled_aux_pls8_w0p1 | shuffled_aux_negative_control | 0.024110011768555862 | 0.03921568627450981 | 1950 |
| shuffled_aux_pls8_w0p2 | shuffled_aux_negative_control | 0.021177253427034543 | 0.019607843137254905 | 1950 |
| shuffled_aux_pls8_w0p05 | shuffled_aux_negative_control | 0.02073553853544514 | 0.02647058823529412 | 1950 |
| shuffled_aux_pls4_w0p1 | shuffled_aux_negative_control | 0.02021891729627083 | 0.02696078431372549 | 1950 |
| shuffled_aux_pls2_w0p2 | shuffled_aux_negative_control | 0.01752008535144763 | 0.025138347241713314 | 1950 |
| shuffled_aux_pls6_w0p2 | shuffled_aux_negative_control | 0.011551964218194115 | 0.018158822172829082 | 1950 |
| shuffled_aux_pls6_w0p1 | shuffled_aux_negative_control | 0.01108081253819449 | 0.009803921568627453 | 1950 |

## Claim boundary

| stage69_run_is_internal_auxiliary_head_audit | auxiliary_targets_pathology_blind | donor_heldout_only | negative_shuffled_aux_controls_run | no_new_candidate_selection | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_new_microglia_subtype_claim | no_benchmark_lock_claim | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True |
