# Stage 39H proxy-safe composition decomposition report

Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims.

## Feature blocks

| feature_block_id | feature_block_name | source_stage | source_file | n_features | feature_examples | provenance_known | train_fold_safe_known | suspected_target_proxy | suspected_donor_proxy | suspected_region_proxy | suspected_batch_proxy | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tier1_safe_metadata | safe pre-pathology metadata | Stage 39D/39H | safe_metadata_covariates | 7 | metadata_APOE Genotype;metadata_Age at Death;metadata_PMI;metadata_Primary Study Name;metadata_RIN | True | True | False | False | False | True | predeclared donor/technical covariate; not a direct target readout |
| tier2_broad_composition | broad composition/count features | Stage 39D/39H | stage39d_composition_features | 6 | composition_count_Class_Non_neuronal_and_Non_neural;composition_count_Subclass_Microglia_PVM;composition_prop_Class_Non_neuronal_and_Non_neural;composition_prop_Subclass_Microglia_PVM;composition_total_cells | True | False | True | False | False | False | biologically meaningful but target-adjacent composition |
| tier3_cell_state_proxy | fine supertype composition | Stage 39D/39H | stage39d_composition_features | 8 | composition_count_Supertype_Lymphocyte;composition_count_Supertype_Micro_PVM_1;composition_count_Supertype_Micro_PVM_2;composition_count_Supertype_Monocyte;composition_prop_Supertype_Lymphocyte | True | False | True | False | False | False | fine cell-state proportions are target-adjacent and proxy-sensitive |
| tier4_forbidden_pseudoprogression | pseudo-progression summaries | Stage 39D/39H | stage39d_composition_features | 5 | composition_pseudoprogression_max;composition_pseudoprogression_mean;composition_pseudoprogression_median;composition_pseudoprogression_min;composition_pseudoprogression_std | True | False | True | False | False | False | pseudo-pathology/state trajectory feature flagged by Stage 39D |
| tier4_forbidden_seaad_state_label | SEAAD-labeled cell-state composition | Stage 39D/39H | stage39d_composition_features | 8 | composition_count_Supertype_Micro_PVM_2_1_SEAAD;composition_count_Supertype_Micro_PVM_2_3_SEAAD;composition_count_Supertype_Micro_PVM_3_SEAAD;composition_count_Supertype_Micro_PVM_4_SEAAD;composition_prop_Supertype_Micro_PVM_2_1_SEAAD | True | False | True | False | False | False | SEAAD cell-state label can encode disease/pathology context |
| tier4_unknown_provenance | unknown provenance feature | Stage 39D/39H | stage39d_composition_features | 6 | composition_count_Brain Region_Human_MTG;composition_count_Brain Region_Human_MTG_All_Layers;composition_count_Brain Region_Human_MTG_L5;composition_prop_Brain Region_Human_MTG;composition_prop_Brain Region_Human_MTG_All_Layers | True | False | True | False | False | False | unclear provenance under proxy-safe audit |

## Risk tiers

| feature_block_id | feature_block_name | source_stage | source_file | n_features | feature_examples | provenance_known | train_fold_safe_known | suspected_target_proxy | suspected_donor_proxy | suspected_region_proxy | suspected_batch_proxy | notes | risk_tier | allowed_for_lock_candidate | comparator_only | forbidden | reason | recommended_use | evidence_from_stage39d_or_stage39f |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tier1_safe_metadata | safe pre-pathology metadata | Stage 39D/39H | safe_metadata_covariates | 7 | metadata_APOE Genotype;metadata_Age at Death;metadata_PMI;metadata_Primary Study Name;metadata_RIN | True | True | False | False | False | True | predeclared donor/technical covariate; not a direct target readout | 1 | True | False | False | predeclared donor/technical covariate; not a direct target readout | lock_candidate_allowed | predeclared low-risk or target-adjacent block |
| tier2_broad_composition | broad composition/count features | Stage 39D/39H | stage39d_composition_features | 6 | composition_count_Class_Non_neuronal_and_Non_neural;composition_count_Subclass_Microglia_PVM;composition_prop_Class_Non_neuronal_and_Non_neural;composition_prop_Subclass_Microglia_PVM;composition_total_cells | True | False | True | False | False | False | biologically meaningful but target-adjacent composition | 2 | False | False | False | biologically meaningful but target-adjacent composition | caution_candidate_only | predeclared low-risk or target-adjacent block |
| tier3_cell_state_proxy | fine supertype composition | Stage 39D/39H | stage39d_composition_features | 8 | composition_count_Supertype_Lymphocyte;composition_count_Supertype_Micro_PVM_1;composition_count_Supertype_Micro_PVM_2;composition_count_Supertype_Monocyte;composition_prop_Supertype_Lymphocyte | True | False | True | False | False | False | fine cell-state proportions are target-adjacent and proxy-sensitive | 3 | False | True | False | fine cell-state proportions are target-adjacent and proxy-sensitive | comparator_only | Stage39D proxy audit and Stage39F lock decision blocked proxy-sensitive context |
| tier4_forbidden_pseudoprogression | pseudo-progression summaries | Stage 39D/39H | stage39d_composition_features | 5 | composition_pseudoprogression_max;composition_pseudoprogression_mean;composition_pseudoprogression_median;composition_pseudoprogression_min;composition_pseudoprogression_std | True | False | True | False | False | False | pseudo-pathology/state trajectory feature flagged by Stage 39D | 4 | False | False | True | pseudo-pathology/state trajectory feature flagged by Stage 39D | forbidden | Stage39D proxy audit and Stage39F lock decision blocked proxy-sensitive context |
| tier4_forbidden_seaad_state_label | SEAAD-labeled cell-state composition | Stage 39D/39H | stage39d_composition_features | 8 | composition_count_Supertype_Micro_PVM_2_1_SEAAD;composition_count_Supertype_Micro_PVM_2_3_SEAAD;composition_count_Supertype_Micro_PVM_3_SEAAD;composition_count_Supertype_Micro_PVM_4_SEAAD;composition_prop_Supertype_Micro_PVM_2_1_SEAAD | True | False | True | False | False | False | SEAAD cell-state label can encode disease/pathology context | 4 | False | False | True | SEAAD cell-state label can encode disease/pathology context | forbidden | Stage39D proxy audit and Stage39F lock decision blocked proxy-sensitive context |
| tier4_unknown_provenance | unknown provenance feature | Stage 39D/39H | stage39d_composition_features | 6 | composition_count_Brain Region_Human_MTG;composition_count_Brain Region_Human_MTG_All_Layers;composition_count_Brain Region_Human_MTG_L5;composition_prop_Brain Region_Human_MTG;composition_prop_Brain Region_Human_MTG_All_Layers | True | False | True | False | False | False | unclear provenance under proxy-safe audit | 4 | False | False | True | unclear provenance under proxy-safe audit | forbidden | Stage39D proxy audit and Stage39F lock decision blocked proxy-sensitive context |

## Proxy-target correlation audit

| feature_block_id | feature_name_or_summary | target | correlation_with_target | abs_correlation | high_proxy_risk_flag | computed_train_fold_only | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_max | 6e10/A_beta | 0.8290169079680064 | 0.8290169079680064 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_mean | 6e10/A_beta | 0.8290169079680064 | 0.8290169079680064 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_min | 6e10/A_beta | 0.8290169079680064 | 0.8290169079680064 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_median | 6e10/A_beta | 0.8290169079680064 | 0.8290169079680064 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_max | AT8 | 0.7427761466032197 | 0.7427761466032197 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_mean | AT8 | 0.7427761466032197 | 0.7427761466032197 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_min | AT8 | 0.7427761466032197 | 0.7427761466032197 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_median | AT8 | 0.7427761466032197 | 0.7427761466032197 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_max | NeuN | -0.5742836893793662 | 0.5742836893793662 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_min | NeuN | -0.5742836893793662 | 0.5742836893793662 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_mean | NeuN | -0.5742836893793662 | 0.5742836893793662 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_median | NeuN | -0.5742836893793662 | 0.5742836893793662 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_seaad_state_label | composition_prop_Supertype_Micro_PVM_3_SEAAD | AT8 | 0.5632074516553609 | 0.5632074516553609 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_min | GFAP | 0.43671155209071577 | 0.43671155209071577 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_max | GFAP | 0.43671155209071577 | 0.43671155209071577 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_median | GFAP | 0.43671155209071577 | 0.43671155209071577 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_mean | GFAP | 0.43671155209071577 | 0.43671155209071577 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_seaad_state_label | composition_prop_Supertype_Micro_PVM_3_SEAAD | 6e10/A_beta | 0.39840032398501574 | 0.39840032398501574 | True | False | descriptive proxy audit; not used for model training |
| tier3_cell_state_proxy | composition_count_Supertype_Monocyte | Iba1 | 0.37790790167039306 | 0.37790790167039306 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_seaad_state_label | composition_count_Supertype_Micro_PVM_3_SEAAD | AT8 | 0.37761587146970105 | 0.37761587146970105 | True | False | descriptive proxy audit; not used for model training |
| tier3_cell_state_proxy | composition_prop_Supertype_Micro_PVM_1 | GFAP | 0.3591171408322365 | 0.3591171408322365 | True | False | descriptive proxy audit; not used for model training |
| tier1_safe_metadata | metadata_RIN | AT8 | -0.3551248603630749 | 0.3551248603630749 | False | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_seaad_state_label | composition_prop_Supertype_Micro_PVM_3_SEAAD | GFAP | 0.32351928723296547 | 0.32351928723296547 | True | False | descriptive proxy audit; not used for model training |
| tier1_safe_metadata | metadata_PMI | NeuN | -0.30174540528042965 | 0.30174540528042965 | False | False | descriptive proxy audit; not used for model training |
| tier3_cell_state_proxy | composition_prop_Supertype_Micro_PVM_2 | NeuN | 0.3009010833248963 | 0.3009010833248963 | True | False | descriptive proxy audit; not used for model training |
| tier3_cell_state_proxy | composition_prop_Supertype_Monocyte | Iba1 | 0.2969575348040474 | 0.2969575348040474 | True | False | descriptive proxy audit; not used for model training |
| tier3_cell_state_proxy | composition_prop_Supertype_Lymphocyte | NeuN | -0.2874629813359184 | 0.2874629813359184 | True | False | descriptive proxy audit; not used for model training |
| tier3_cell_state_proxy | composition_count_Supertype_Micro_PVM_1 | GFAP | 0.2663066656818504 | 0.2663066656818504 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_max | Iba1 | 0.2621241267591374 | 0.2621241267591374 | True | False | descriptive proxy audit; not used for model training |
| tier4_forbidden_pseudoprogression | composition_pseudoprogression_mean | Iba1 | 0.2621241267591374 | 0.2621241267591374 | True | False | descriptive proxy audit; not used for model training |

## Ablation and model registry

| feature_set_id | feature_blocks | risk_tiers_used | allowed_for_lock_candidate | comparator_only | model_name |
| --- | --- | --- | --- | --- | --- |
| latent_only | latent | Tier0 | True | False | ridge |
| safe_metadata_only | tier1_safe_metadata | Tier1 | True | False | ridge |
| safe_composition_only | tier2_broad_composition | Tier2 | False | False | ridge |
| latent_plus_tier1_safe_metadata | latent;tier1_safe_metadata | Tier0;Tier1 | True | False | ridge |
| latent_plus_tier2_composition | latent;tier2_broad_composition | Tier0;Tier2 | False | False | ridge |
| latent_plus_tier1_plus_tier2 | latent;tier1_safe_metadata;tier2_broad_composition | Tier0;Tier1;Tier2 | False | False | ridge |
| tier3_proxy_only_comparator | tier3_cell_state_proxy | Tier3 | False | True | ridge |
| full_39d_reconstruction_comparator | tier2_broad_composition;tier3_cell_state_proxy;tier4_forbidden_pseudoprogression;tier4_forbidden_seaad_state_label | Tier2;Tier3;Tier4 | False | True | ridge |
| restricted_no_pseudo_no_seaad_reconstruction | tier2_broad_composition;tier3_cell_state_proxy | Tier2;Tier3 | False | True | ridge |
| stage39e_pca8_reference | external_reference_oof | Tier0 | False | True | ridge |
| stage27c_reference | external_reference_oof | Tier0 | False | True | ridge |
| target_shuffled_control | latent;tier1_safe_metadata;tier2_broad_composition | control | False | True | ridge |

## Mean OOF results

| candidate_id | feature_set_id | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | full_39d_reconstruction_comparator | 0.4933643818973373 | 0.2375215146299484 | 5 |
| latent_plus_tier1_plus_tier2 | latent_plus_tier1_plus_tier2 | 0.38781411359724616 | 0.11258479295332592 | 5 |
| latent_plus_tier1_safe_metadata | latent_plus_tier1_safe_metadata | 0.37668522830819073 | 0.013688366913030272 | 5 |
| stage39e_pca8_reference | stage39e_pca8_reference | 0.35808116279206914 | 0.056974172849842526 | 5 |
| latent_only | latent_only | 0.3458094563126456 | 0.025473321858864025 | 5 |
| latent_plus_tier2_composition | latent_plus_tier2_composition | 0.34010732003644834 | 0.04837501265566467 | 5 |
| stage27c_reference | stage27c_reference | 0.3267024400121495 | 0.016077756403766325 | 5 |
| safe_metadata_only | safe_metadata_only | 0.24245418649387468 | 0.009800546724713984 | 5 |
| tier3_proxy_only_comparator | tier3_proxy_only_comparator | 0.1718497519489724 | 0.08749620330059735 | 5 |
| restricted_no_pseudo_no_seaad_reconstruction | restricted_no_pseudo_no_seaad_reconstruction | 0.12650804900273363 | -0.007937632884479092 | 5 |
| target_shuffled_control | target_shuffled_control | -0.01542573655968411 | -0.1558975397387871 | 5 |
| safe_composition_only | safe_composition_only | -0.020388885233050727 | -0.21484365112987208 | 5 |

## Feature block contribution

| candidate_id | mean_pooled_oof_spearman | delta_vs_latent_only | delta_vs_stage39e_pca8 | delta_vs_stage27c |
| --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | 0.4933643818973373 | 0.1475549255846917 | 0.13528321910526814 | 0.1666619418851878 |
| latent_plus_tier1_plus_tier2 | 0.38781411359724616 | 0.042004657284600566 | 0.029732950805177016 | 0.06111167358509667 |
| latent_plus_tier1_safe_metadata | 0.37668522830819073 | 0.030875771995545143 | 0.018604065516121593 | 0.04998278829604125 |
| stage39e_pca8_reference | 0.35808116279206914 | 0.01227170647942355 | 0.0 | 0.031378722779919654 |
| latent_only | 0.3458094563126456 | 0.0 | -0.01227170647942355 | 0.019107016300496105 |
| latent_plus_tier2_composition | 0.34010732003644834 | -0.005702136276197256 | -0.017973842755620806 | 0.013404880024298849 |
| stage27c_reference | 0.3267024400121495 | -0.019107016300496105 | -0.031378722779919654 | 0.0 |
| safe_metadata_only | 0.24245418649387468 | -0.10335526981877091 | -0.11562697629819446 | -0.08424825351827481 |
| tier3_proxy_only_comparator | 0.1718497519489724 | -0.1739597043636732 | -0.18623141084309675 | -0.1548526880631771 |
| restricted_no_pseudo_no_seaad_reconstruction | 0.12650804900273363 | -0.21930140730991196 | -0.2315731137893355 | -0.20019439100941586 |
| target_shuffled_control | -0.01542573655968411 | -0.3612351928723297 | -0.37350689935175324 | -0.3421281765718336 |
| safe_composition_only | -0.020388885233050727 | -0.3661983415456963 | -0.37847004802511985 | -0.3470913252452002 |

## Bootstrap, target guards, Aβ, and Iba1

| candidate_id | n_bootstrap | mean_bootstrap | ci_lower_95 | ci_upper_95 | lower_ci_above_stage27c | lower_ci_above_material_threshold |
| --- | --- | --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | 500 | 0.48562605852141966 | 0.41148045863594956 | 0.5567457694399098 | True | True |
| latent_only | 500 | 0.34047469418588666 | 0.24932456692965593 | 0.4378643786868736 | False | False |
| latent_plus_tier1_plus_tier2 | 500 | 0.38335752717457255 | 0.288386153095105 | 0.4715039773935322 | False | False |
| latent_plus_tier1_safe_metadata | 500 | 0.3742128537164384 | 0.2869113379238427 | 0.45316340444245423 | False | False |
| latent_plus_tier2_composition | 500 | 0.3354374051299467 | 0.22191196854668804 | 0.44268850943181715 | False | False |
| restricted_no_pseudo_no_seaad_reconstruction | 500 | 0.1287296337650917 | 0.013020346875077058 | 0.23875246743854378 | False | False |
| safe_composition_only | 500 | -0.02009348076965321 | -0.11154945587376255 | 0.07007487671709192 | False | False |
| safe_metadata_only | 500 | 0.23891155509747322 | 0.1374147426377436 | 0.33733185435377105 | False | False |
| stage27c_reference | 500 | 0.3251234034929212 | 0.19660534520673442 | 0.42343120844836474 | False | False |
| stage39e_pca8_reference | 500 | 0.35380533287358096 | 0.2566677445582093 | 0.44320229650214776 | False | False |
| target_shuffled_control | 500 | -0.014333686007872338 | -0.09791661291913918 | 0.07328088519207858 | False | False |
| tier3_proxy_only_comparator | 500 | 0.1711632689461784 | 0.040504990905787096 | 0.2782880306895651 | False | False |

| candidate_id | target | target_score | stage39e_pca8_target_reference | delta_vs_stage39e_pca8 | guard_threshold | target_guard_pass |
| --- | --- | --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | 6e10/A_beta | 0.7306469575782121 | 0.3746733755407961 | 0.35597358203741597 | -0.05 | True |
| full_39d_reconstruction_comparator | AT8 | 0.6959805608990586 | 0.5155185235317487 | 0.18046203736730992 | -0.05 | True |
| full_39d_reconstruction_comparator | GFAP | 0.3136174951908475 | 0.3823049963928304 | -0.06868750120198291 | -0.05 | False |
| full_39d_reconstruction_comparator | Iba1 | 0.2375215146299484 | 0.056974172849842526 | 0.18054734178010587 | -0.05 | True |
| full_39d_reconstruction_comparator | NeuN | 0.48905538118862 | 0.4609347456451279 | 0.028120635543492145 | -0.05 | True |
| latent_only | 6e10/A_beta | 0.4001619925078465 | 0.3746733755407961 | 0.025488616967050404 | -0.05 | True |
| latent_only | AT8 | 0.5254834463906044 | 0.5155185235317487 | 0.009964922858855751 | -0.05 | True |
| latent_only | GFAP | 0.3122608079376329 | 0.3823049963928304 | -0.0700441884551975 | -0.05 | False |
| latent_only | Iba1 | 0.025473321858864025 | 0.056974172849842526 | -0.031500850990978504 | -0.05 | True |
| latent_only | NeuN | 0.46566771286827985 | 0.4609347456451279 | 0.004732967223151974 | -0.05 | True |
| latent_plus_tier1_plus_tier2 | 6e10/A_beta | 0.6238938949073606 | 0.3746733755407961 | 0.24922051936656447 | -0.05 | True |
| latent_plus_tier1_plus_tier2 | AT8 | 0.5622354966082819 | 0.5155185235317487 | 0.04671697307653322 | -0.05 | True |
| latent_plus_tier1_plus_tier2 | GFAP | 0.26996051432621243 | 0.3823049963928304 | -0.11234448206661796 | -0.05 | False |
| latent_plus_tier1_plus_tier2 | Iba1 | 0.11258479295332592 | 0.056974172849842526 | 0.055610620103483395 | -0.05 | True |
| latent_plus_tier1_plus_tier2 | NeuN | 0.37039586919104994 | 0.4609347456451279 | -0.09053887645407793 | -0.05 | False |
| latent_plus_tier1_safe_metadata | 6e10/A_beta | 0.6347878910600385 | 0.3746733755407961 | 0.2601145155192424 | -0.05 | True |
| latent_plus_tier1_safe_metadata | AT8 | 0.566791535891465 | 0.5155185235317487 | 0.051273012359716374 | -0.05 | True |
| latent_plus_tier1_safe_metadata | GFAP | 0.26627518477270423 | 0.3823049963928304 | -0.11602981162012616 | -0.05 | False |
| latent_plus_tier1_safe_metadata | Iba1 | 0.013688366913030272 | 0.056974172849842526 | -0.043285805936812256 | -0.05 | True |
| latent_plus_tier1_safe_metadata | NeuN | 0.40188316290371573 | 0.4609347456451279 | -0.059051582741412145 | -0.05 | False |
| latent_plus_tier2_composition | 6e10/A_beta | 0.3193074820289562 | 0.3746733755407961 | -0.0553658935118399 | -0.05 | False |
| latent_plus_tier2_composition | AT8 | 0.5080895008605852 | 0.5155185235317487 | -0.00742902267116341 | -0.05 | True |
| latent_plus_tier2_composition | GFAP | 0.356019034119672 | 0.3823049963928304 | -0.02628596227315838 | -0.05 | True |
| latent_plus_tier2_composition | Iba1 | 0.04837501265566467 | 0.056974172849842526 | -0.008599160194177856 | -0.05 | True |
| latent_plus_tier2_composition | NeuN | 0.4687455705173636 | 0.4609347456451279 | 0.007810824872235722 | -0.05 | True |
| restricted_no_pseudo_no_seaad_reconstruction | 6e10/A_beta | -0.007937632884479092 | 0.3746733755407961 | -0.3826110084252752 | -0.05 | False |
| restricted_no_pseudo_no_seaad_reconstruction | AT8 | 0.05854004252303331 | 0.5155185235317487 | -0.45697848100871535 | -0.05 | False |
| restricted_no_pseudo_no_seaad_reconstruction | GFAP | 0.11944922547332186 | 0.3823049963928304 | -0.2628557709195085 | -0.05 | False |
| restricted_no_pseudo_no_seaad_reconstruction | Iba1 | 0.2856940366508049 | 0.056974172849842526 | 0.22871986380096238 | -0.05 | True |
| restricted_no_pseudo_no_seaad_reconstruction | NeuN | 0.17679457325098716 | 0.4609347456451279 | -0.2841401723941407 | -0.05 | False |
| safe_composition_only | 6e10/A_beta | -0.21484365112987208 | 0.3746733755407961 | -0.5895170266706682 | -0.05 | False |
| safe_composition_only | AT8 | -0.0029665028172032293 | 0.5155185235317487 | -0.5184850263489519 | -0.05 | False |
| safe_composition_only | GFAP | -0.026769397435786137 | 0.3823049963928304 | -0.40907439382861654 | -0.05 | False |
| safe_composition_only | Iba1 | 0.11171464875433593 | 0.056974172849842526 | 0.0547404759044934 | -0.05 | True |
| safe_composition_only | NeuN | 0.03092047646327188 | 0.4609347456451279 | -0.430014269181856 | -0.05 | False |
| safe_metadata_only | 6e10/A_beta | 0.5211906449326719 | 0.3746733755407961 | 0.14651726939187576 | -0.05 | True |
| safe_metadata_only | AT8 | 0.4066011946947454 | 0.5155185235317487 | -0.10891732883700322 | -0.05 | False |
| safe_metadata_only | GFAP | 0.08283891870001013 | 0.3823049963928304 | -0.29946607769282024 | -0.05 | False |
| safe_metadata_only | Iba1 | 0.009800546724713984 | 0.056974172849842526 | -0.04717362612512854 | -0.05 | True |
| safe_metadata_only | NeuN | 0.19183962741723196 | 0.4609347456451279 | -0.2690951182278959 | -0.05 | False |
| stage27c_reference | 6e10/A_beta | 0.3347372684013365 | 0.3746733755407961 | -0.03993610713945961 | -0.05 | True |
| stage27c_reference | AT8 | 0.5284398096588033 | 0.5155185235317487 | 0.012921286127054676 | -0.05 | True |
| stage27c_reference | GFAP | 0.30229826870507237 | 0.3823049963928304 | -0.08000672768775802 | -0.05 | False |
| stage27c_reference | Iba1 | 0.016077756403766325 | 0.056974172849842526 | -0.0408964164460762 | -0.05 | True |
| stage27c_reference | NeuN | 0.4519590968917688 | 0.4609347456451279 | -0.0089756487533591 | -0.05 | True |
| stage39e_pca8_reference | 6e10/A_beta | 0.3746733755407961 | 0.3746733755407961 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | AT8 | 0.5155185235317487 | 0.5155185235317487 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | GFAP | 0.3823049963928304 | 0.3823049963928304 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | Iba1 | 0.056974172849842526 | 0.056974172849842526 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | NeuN | 0.4609347456451279 | 0.4609347456451279 | 0.0 | -0.05 | True |
| target_shuffled_control | 6e10/A_beta | 0.20024298876176977 | 0.3746733755407961 | -0.17443038677902634 | -0.05 | False |
| target_shuffled_control | AT8 | -0.12651614862812594 | 0.5155185235317487 | -0.6420346721598746 | -0.05 | False |
| target_shuffled_control | GFAP | -0.1558975397387871 | 0.3823049963928304 | -0.5382025361316175 | -0.05 | False |
| target_shuffled_control | Iba1 | -0.018446896831021565 | 0.056974172849842526 | -0.0754210696808641 | -0.05 | False |
| target_shuffled_control | NeuN | 0.023488913637744257 | 0.4609347456451279 | -0.43744583200738363 | -0.05 | False |
| tier3_proxy_only_comparator | 6e10/A_beta | 0.08749620330059735 | 0.3746733755407961 | -0.2871771722401988 | -0.05 | False |
| tier3_proxy_only_comparator | AT8 | 0.11238230231851776 | 0.5155185235317487 | -0.4031362212132309 | -0.05 | False |
| tier3_proxy_only_comparator | GFAP | 0.19653741014478082 | 0.3823049963928304 | -0.18576758624804957 | -0.05 | False |
| tier3_proxy_only_comparator | Iba1 | 0.2649792447099322 | 0.056974172849842526 | 0.2080050718600897 | -0.05 | True |
| tier3_proxy_only_comparator | NeuN | 0.19785359927103374 | 0.4609347456451279 | -0.26308114637409413 | -0.05 | False |

| candidate_id | target | abeta_score | stage39e_pca8_target_reference | delta_vs_stage39e_pca8 | guard_threshold | abeta_guard_pass |
| --- | --- | --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | 6e10/A_beta | 0.7306469575782121 | 0.3746733755407961 | 0.35597358203741597 | -0.05 | True |
| latent_only | 6e10/A_beta | 0.4001619925078465 | 0.3746733755407961 | 0.025488616967050404 | -0.05 | True |
| latent_plus_tier1_plus_tier2 | 6e10/A_beta | 0.6238938949073606 | 0.3746733755407961 | 0.24922051936656447 | -0.05 | True |
| latent_plus_tier1_safe_metadata | 6e10/A_beta | 0.6347878910600385 | 0.3746733755407961 | 0.2601145155192424 | -0.05 | True |
| latent_plus_tier2_composition | 6e10/A_beta | 0.3193074820289562 | 0.3746733755407961 | -0.0553658935118399 | -0.05 | False |
| restricted_no_pseudo_no_seaad_reconstruction | 6e10/A_beta | -0.007937632884479092 | 0.3746733755407961 | -0.3826110084252752 | -0.05 | False |
| safe_composition_only | 6e10/A_beta | -0.21484365112987208 | 0.3746733755407961 | -0.5895170266706682 | -0.05 | False |
| safe_metadata_only | 6e10/A_beta | 0.5211906449326719 | 0.3746733755407961 | 0.14651726939187576 | -0.05 | True |
| stage27c_reference | 6e10/A_beta | 0.3347372684013365 | 0.3746733755407961 | -0.03993610713945961 | -0.05 | True |
| stage39e_pca8_reference | 6e10/A_beta | 0.3746733755407961 | 0.3746733755407961 | 0.0 | -0.05 | True |
| target_shuffled_control | 6e10/A_beta | 0.20024298876176977 | 0.3746733755407961 | -0.17443038677902634 | -0.05 | False |
| tier3_proxy_only_comparator | 6e10/A_beta | 0.08749620330059735 | 0.3746733755407961 | -0.2871771722401988 | -0.05 | False |

| candidate_id | feature_set_id | target | n_donors | pooled_oof_spearman | stage27c_iba1_score | delta_vs_stage27c | iba1_nonnegative | iba1_improved_vs_stage27c | iba1_rescue_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | full_39d_reconstruction_comparator | Iba1 | 84 | 0.2375215146299484 | 0.016077756403766325 | 0.22144375822618206 | True | True | Iba1 improved |
| latent_only | latent_only | Iba1 | 84 | 0.025473321858864025 | 0.016077756403766325 | 0.0093955654550977 | True | True | Iba1 improved |
| latent_plus_tier1_plus_tier2 | latent_plus_tier1_plus_tier2 | Iba1 | 84 | 0.11258479295332592 | 0.016077756403766325 | 0.0965070365495596 | True | True | Iba1 improved |
| latent_plus_tier1_safe_metadata | latent_plus_tier1_safe_metadata | Iba1 | 84 | 0.013688366913030272 | 0.016077756403766325 | -0.002389389490736053 | True | False | Iba1 not improved |
| latent_plus_tier2_composition | latent_plus_tier2_composition | Iba1 | 84 | 0.04837501265566467 | 0.016077756403766325 | 0.032297256251898346 | True | True | Iba1 improved |
| restricted_no_pseudo_no_seaad_reconstruction | restricted_no_pseudo_no_seaad_reconstruction | Iba1 | 84 | 0.2856940366508049 | 0.016077756403766325 | 0.26961628024703854 | True | True | Iba1 improved |
| safe_composition_only | safe_composition_only | Iba1 | 84 | 0.11171464875433593 | 0.016077756403766325 | 0.0956368923505696 | True | True | Iba1 improved |
| safe_metadata_only | safe_metadata_only | Iba1 | 84 | 0.009800546724713984 | 0.016077756403766325 | -0.006277209679052341 | True | False | Iba1 not improved |
| stage27c_reference | stage27c_reference | Iba1 | 84 | 0.016077756403766325 | 0.016077756403766325 | 0.0 | True | False | Iba1 not improved |
| stage39e_pca8_reference | stage39e_pca8_reference | Iba1 | 84 | 0.056974172849842526 | 0.016077756403766325 | 0.0408964164460762 | True | True | Iba1 improved |
| target_shuffled_control | target_shuffled_control | Iba1 | 84 | -0.018446896831021565 | 0.016077756403766325 | -0.034524653234787886 | False | False | Iba1 not improved |
| tier3_proxy_only_comparator | tier3_proxy_only_comparator | Iba1 | 84 | 0.2649792447099322 | 0.016077756403766325 | 0.2489014883061659 | True | True | Iba1 improved |

## Negative controls and proxy/leakage decision

| candidate_id | feature_set_id | mean_pooled_oof_spearman | min_target_spearman | n_targets | control_type | real_score | control_score | delta_vs_control | control_pass | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | full_39d_reconstruction_comparator | 0.4933643818973373 | 0.2375215146299484 | 5 | full_39d_reconstruction_comparator | 0.38781411359724616 | 0.4933643818973373 | -0.10555026830009112 | False | control matches/exceeds candidate |
| restricted_no_pseudo_no_seaad_reconstruction | restricted_no_pseudo_no_seaad_reconstruction | 0.12650804900273363 | -0.007937632884479092 | 5 | restricted_no_pseudo_no_seaad_reconstruction | 0.38781411359724616 | 0.12650804900273363 | 0.26130606459451255 | True | real candidate exceeds control |
| safe_composition_only | safe_composition_only | -0.020388885233050727 | -0.21484365112987208 | 5 | safe_composition_only | 0.38781411359724616 | -0.020388885233050727 | 0.40820299883029687 | True | real candidate exceeds control |
| safe_metadata_only | safe_metadata_only | 0.24245418649387468 | 0.009800546724713984 | 5 | safe_metadata_only | 0.38781411359724616 | 0.24245418649387468 | 0.14535992710337148 | True | real candidate exceeds control |
| stage39e_pca8_reference | stage39e_pca8_reference | 0.35808116279206914 | 0.056974172849842526 | 5 | stage39e_pca8_reference | 0.38781411359724616 | 0.35808116279206914 | 0.029732950805177016 | True | real candidate exceeds control |
| target_shuffled_control | target_shuffled_control | -0.01542573655968411 | -0.1558975397387871 | 5 | target_shuffled_control | 0.38781411359724616 | -0.01542573655968411 | 0.40323985015693026 | True | real candidate exceeds control |
| tier3_proxy_only_comparator | tier3_proxy_only_comparator | 0.1718497519489724 | 0.08749620330059735 | 5 | tier3_proxy_only_comparator | 0.38781411359724616 | 0.1718497519489724 | 0.21596436164827376 | True | real candidate exceeds control |

| candidate_id | feature_set_id | mean_pooled_oof_spearman | min_target_spearman | n_targets | risk_tiers_used | allowed_for_lock_candidate | comparator_only | proxy_leakage_risk_pass | proxy_leakage_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | full_39d_reconstruction_comparator | 0.4933643818973373 | 0.2375215146299484 | 5 | Tier2;Tier3;Tier4 | False | True | False | proxy_sensitive_or_caution_only |
| latent_only | latent_only | 0.3458094563126456 | 0.025473321858864025 | 5 | Tier0 | True | False | True | proxy_safe_or_allowed |
| latent_plus_tier1_plus_tier2 | latent_plus_tier1_plus_tier2 | 0.38781411359724616 | 0.11258479295332592 | 5 | Tier0;Tier1;Tier2 | False | False | False | proxy_sensitive_or_caution_only |
| latent_plus_tier1_safe_metadata | latent_plus_tier1_safe_metadata | 0.37668522830819073 | 0.013688366913030272 | 5 | Tier0;Tier1 | True | False | True | proxy_safe_or_allowed |
| latent_plus_tier2_composition | latent_plus_tier2_composition | 0.34010732003644834 | 0.04837501265566467 | 5 | Tier0;Tier2 | False | False | False | proxy_sensitive_or_caution_only |
| restricted_no_pseudo_no_seaad_reconstruction | restricted_no_pseudo_no_seaad_reconstruction | 0.12650804900273363 | -0.007937632884479092 | 5 | Tier2;Tier3 | False | True | False | proxy_sensitive_or_caution_only |
| safe_composition_only | safe_composition_only | -0.020388885233050727 | -0.21484365112987208 | 5 | Tier2 | False | False | False | proxy_sensitive_or_caution_only |
| safe_metadata_only | safe_metadata_only | 0.24245418649387468 | 0.009800546724713984 | 5 | Tier1 | True | False | True | proxy_safe_or_allowed |
| stage27c_reference | stage27c_reference | 0.3267024400121495 | 0.016077756403766325 | 5 | Tier0 | False | True | True | proxy_safe_or_allowed |
| stage39e_pca8_reference | stage39e_pca8_reference | 0.35808116279206914 | 0.056974172849842526 | 5 | Tier0 | False | True | True | proxy_safe_or_allowed |
| target_shuffled_control | target_shuffled_control | -0.01542573655968411 | -0.1558975397387871 | 5 | control | False | True | False | proxy_sensitive_or_caution_only |
| tier3_proxy_only_comparator | tier3_proxy_only_comparator | 0.1718497519489724 | 0.08749620330059735 | 5 | Tier3 | False | True | False | proxy_sensitive_or_caution_only |

## Benchmark lock decision

| candidate_id | feature_set_id | model_name | risk_tiers_used | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39e_pca8 | lower_ci_above_stage27c | lower_ci_above_material_threshold | target_guard_pass | abeta_guard_pass | iba1_rescue_status | negative_controls_pass | proxy_leakage_risk_pass | high_influence_donor_or_fold_flag | benchmark_lock_eligible | recommended_decision | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_39d_reconstruction_comparator | full_39d_reconstruction_comparator | ridge_or_reference | Tier2;Tier3;Tier4 | 0.4933643818973373 | 0.1666619418851878 | 0.13528321910526814 | True | True | False | True | Iba1 improved | False | False | False | False | proxy_sensitive_not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| latent_only | latent_only | ridge_or_reference | Tier0 | 0.3458094563126456 | 0.019107016300496105 | -0.01227170647942355 | False | False | False | True | Iba1 improved | False | True | False | False | proxy_safe_context_not_sufficient | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| latent_plus_tier1_plus_tier2 | latent_plus_tier1_plus_tier2 | ridge_or_reference | Tier0;Tier1;Tier2 | 0.38781411359724616 | 0.06111167358509667 | 0.029732950805177016 | False | False | False | True | Iba1 improved | False | False | False | False | proxy_sensitive_not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| latent_plus_tier1_safe_metadata | latent_plus_tier1_safe_metadata | ridge_or_reference | Tier0;Tier1 | 0.37668522830819073 | 0.04998278829604125 | 0.018604065516121593 | False | False | False | True | Iba1 not improved | False | True | False | False | proxy_safe_context_not_sufficient | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| latent_plus_tier2_composition | latent_plus_tier2_composition | ridge_or_reference | Tier0;Tier2 | 0.34010732003644834 | 0.013404880024298849 | -0.017973842755620806 | False | False | False | False | Iba1 improved | False | False | False | False | proxy_sensitive_not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| restricted_no_pseudo_no_seaad_reconstruction | restricted_no_pseudo_no_seaad_reconstruction | ridge_or_reference | Tier2;Tier3 | 0.12650804900273363 | -0.20019439100941586 | -0.2315731137893355 | False | False | False | False | Iba1 improved | True | False | True | False | proxy_sensitive_not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| safe_composition_only | safe_composition_only | ridge_or_reference | Tier2 | -0.020388885233050727 | -0.3470913252452002 | -0.37847004802511985 | False | False | False | False | Iba1 improved | True | False | False | False | proxy_sensitive_not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| safe_metadata_only | safe_metadata_only | ridge_or_reference | Tier1 | 0.24245418649387468 | -0.08424825351827481 | -0.11562697629819446 | False | False | False | True | Iba1 not improved | True | True | False | False | not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage27c_reference | stage27c_reference | ridge_or_reference | Tier0 | 0.3267024400121495 | 0.0 | -0.031378722779919654 | False | False | False | True | Iba1 not improved | True | True | False | False | not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39e_pca8_reference | stage39e_pca8_reference | ridge_or_reference | Tier0 | 0.35808116279206914 | 0.031378722779919654 | 0.0 | False | False | True | True | Iba1 improved | True | True | False | False | proxy_safe_context_not_sufficient | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| target_shuffled_control | target_shuffled_control | ridge_or_reference | control | -0.01542573655968411 | -0.3421281765718336 | -0.37350689935175324 | False | False | False | False | Iba1 not improved | True | False | False | False | proxy_sensitive_not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| tier3_proxy_only_comparator | tier3_proxy_only_comparator | ridge_or_reference | Tier3 | 0.1718497519489724 | -0.1548526880631771 | -0.18623141084309675 | False | False | False | False | Iba1 improved | True | False | True | False | proxy_sensitive_not_lockable | internal proxy-safe context audit; feature-block decomposition; candidate benchmark evidence only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |

## Claim boundaries

| audit_item | pass | evidence |
| --- | --- | --- |
| no_external_data_used | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_external_model_selection | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_candidate_selection | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| frozen_candidates_preserved | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| donor_held_out_evaluation_preserved | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| train_fold_only_preprocessing_preserved | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| forbidden_features_excluded | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| proxy_risk_features_comparator_only | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| negative_controls_reported | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_clean_external_validation_claim | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_causal_claim | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_therapeutic_claim | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_gene_ablation_claim | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_disease_modifying_claim | True | Stage 39H is an internal proxy-safe context decomposition audit. It uses donor-held-out folds, train-fold-only preprocessing, and simple ridge models to decompose Stage 39D context signal. It does not use external data, train new architectures, select candidates, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| safety_audit_pass | True | all safety checks passed |
