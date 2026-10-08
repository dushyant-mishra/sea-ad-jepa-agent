# Stage 41C stability rescue report

Stage 41C tested metadata pruning, stronger ridge shrinkage, donor bagging, and predeclared OOF blends against Stage 27C/39E/Stage41B references.

## Metadata stability audit
| feature_name | feature_type | n_missing | missing_fraction | n_unique | rare_category_flag | fold_imbalance_flag | high_influence_flag | safe_tier | recommended_action | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| module_plaque_response | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_complement | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_lipid_metabolism | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_lysosome_phagocytosis | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_interferon_response | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_inflammatory_signaling | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_at8_associated_first_pass | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_homeostatic_microglia | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_disease_associated_microglia | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_senescence_stress | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_oxidative_stress | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_synapse_pruning | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_antigen_presentation | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_vascular_barrier_myeloid | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| module_chemokine_migration | module | 0 | 0.0 | 84 | False | False | False | Tier1 | keep | Tier0 latent/module feature |
| meta__Age at Death | metadata | 0 | 0.0 | 30 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__Sex_Female | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__Sex_Male | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__Highest level of education_Bachelors | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__Highest level of education_Graduate (PhD/Masters) | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__Highest level of education_High School | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__Highest level of education_Professional | metadata | 0 | 0.0 | 2 | True | False | False | Tier1 | drop_for_lock_candidate | high missingness, sparse category, or fold imbalance |
| meta__Highest level of education_Trade School/ Tech School | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__Years of education | metadata | 0 | 0.0 | 10 | True | False | False | Tier1 | drop_for_lock_candidate | high missingness, sparse category, or fold imbalance |
| meta__APOE Genotype_2/2 | metadata | 0 | 0.0 | 2 | True | False | False | Tier1 | drop_for_lock_candidate | high missingness, sparse category, or fold imbalance |
| meta__APOE Genotype_2/3 | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__APOE Genotype_2/4 | metadata | 0 | 0.0 | 2 | True | False | False | Tier1 | drop_for_lock_candidate | high missingness, sparse category, or fold imbalance |
| meta__APOE Genotype_3/3 | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__APOE Genotype_3/4 | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |
| meta__APOE Genotype_4/4 | metadata | 0 | 0.0 | 2 | False | False | False | Tier1 | keep | safe metadata column with acceptable missingness/fold balance |

## Candidate decisions
| candidate_id | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39e_pca8 | delta_vs_stage41b_original | bootstrap_lower_95 | lower_ci_above_stage27c | material_threshold_pass | target_guard_pass | abeta_guard_pass | iba1_rescue_status | negative_controls_pass | proxy_leakage_pass | donor_fold_stability_pass | stage41c_success | recommended_decision | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blend_stage41b_with_stage39e_pca8 | 0.36808747595423713 | 0.041385035942087645 | 0.01000631316216799 | 0.028664574263440323 | 0.2603604646376338 | False | True | True | True | pass | True | True | True | False | credible_unlocked_stability_signal | CI/robustness or guard limits prevent lock |
| guard_aware_target_specific_blend | 0.36421180520400936 | 0.03750936519185988 | 0.006130642411940224 | 0.024788903513212557 | 0.26341045893303894 | False | True | True | True | pass | True | True | True | False | credible_unlocked_stability_signal | CI/robustness or guard limits prevent lock |
| latent_plus_stable_metadata_shared_alpha | 0.36307785764908374 | 0.03637541763693425 | 0.004996694857014594 | 0.023654955958286927 | 0.2662344164001352 | False | True | True | True | pass | True | True | True | False | credible_unlocked_stability_signal | CI/robustness or guard limits prevent lock |
| blend_stage41b_with_stage27c_and_stage39e_pca8 | 0.3625473321858864 | 0.03584489217373693 | 0.004466169393817276 | 0.02312443049508961 | 0.2620679788859309 | False | True | True | True | pass | True | True | True | False | credible_unlocked_stability_signal | CI/robustness or guard limits prevent lock |
| blend_stage41b_with_stage27c | 0.3583031284803078 | 0.03160068846815833 | 0.0002219656882386789 | 0.018880226789511012 | 0.2519556017379069 | False | True | True | True | fail | True | True | True | False | credible_unlocked_stability_signal | CI/robustness or guard limits prevent lock |
| stage39e_pca8_reference | 0.35808116279206914 | 0.031378722779919654 | 0.0 | 0.018658261101272333 | 0.26027030467967577 | False | True | True | True | pass | True | True | True | False | credible_unlocked_stability_signal | CI/robustness or guard limits prevent lock |
| stage41b_latent_plus_safe_metadata_original | 0.3394229016907968 | 0.012720461678647321 | -0.018658261101272333 | 0.0 | 0.24960775493368131 | False | True | True | True | pass | True | True | True | False | credible_unlocked_stability_signal | CI/robustness or guard limits prevent lock |
| stage27c_reference | 0.3246937329148527 | -0.00200870709729678 | -0.033387429877216435 | -0.014729168775944101 | 0.20803586671931393 | False | False | True | True | fail | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| stage41b_latent_plus_safe_metadata_plus_mri_original | 0.3214012351928724 | -0.005301204819277094 | -0.03667992759919675 | -0.018021666497924416 | 0.221669264725526 | False | False | True | True | pass | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| latent_only_control | 0.2843697478991597 | -0.04233269211298979 | -0.07371141489290944 | -0.05505315379163711 | 0.1540571214651874 | False | False | True | True | pass | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| latent_plus_stable_metadata_pruned | 0.2810165029867369 | -0.04568593702541257 | -0.07706465980533223 | -0.05840639870405989 | 0.19376646222203256 | False | False | False | True | fail | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| latent_plus_stable_metadata_target_specific_alpha | 0.2810165029867369 | -0.04568593702541257 | -0.07706465980533223 | -0.05840639870405989 | 0.20078948900074448 | False | False | False | True | fail | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| latent_plus_stable_metadata_strong_ridge | 0.2778050015186798 | -0.04889743849346967 | -0.08027616127338932 | -0.06161790017211699 | 0.15710608224301728 | False | False | True | True | fail | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| latent_plus_stable_metadata_bagged_ridge | 0.26930444466943404 | -0.05739799534271545 | -0.0887767181226351 | -0.07011845702136277 | 0.15506304129832066 | False | False | True | True | fail | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| metadata_only_control | 0.05443353244912421 | -0.2722689075630253 | -0.30364763034294495 | -0.2849893692416726 | -0.05319386971822173 | False | False | False | True | fail | True | True | True | False | do_not_promote | CI/robustness or guard limits prevent lock |
| target_shuffled_control | 0.03884580338159359 | -0.2878566366305559 | -0.31923535941047554 | -0.3005770983092032 | -0.07188785546500251 | False | False | False | False | fail | True | True | False | False | do_not_promote | CI/robustness or guard limits prevent lock |
