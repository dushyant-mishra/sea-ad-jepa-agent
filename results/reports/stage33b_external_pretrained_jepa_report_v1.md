# Stage 33B external-pretrained JEPA benchmark report v1

## Executive summary

Best external-pretrained condition: `external_pretrained_no_graph_identity_jepa_ridge` with mean pooled donor-level OOF Spearman `0.2711`.
Stage 27C reference: `0.3267`. Stage 31 reference: `0.3264`.
Run pass: `True`. Internal performance pass: `False`. Graph-specific pass: `False`.

## Interpretation

External pretraining did not improve over the current Stage 27C internal no-graph reference.

This is an internal SEA-AD benchmark after external self-supervised pretraining. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.

## Mean metrics

```csv
condition,mean_pooled_oof_spearman,min_target_pooled_oof_spearman,n_targets
stage27c_module_pca_ridge_reference,0.3267024400121495,0.016077756403766325,5
stage31_weak_residual_real_graph_alpha_0_05_reference,0.32637035537106407,0.01565252607066923,5
external_pretrained_no_graph_identity_jepa_ridge,0.27114710944618814,-0.019985825655563432,5
external_pretrained_non_graph_jepa_ridge,0.27114710944618814,-0.019985825655563432,5
external_pretrained_strict_shuffled_residual_graph_jepa_ridge,0.2649670952718437,-0.060625696061557155,5
external_pretrained_residual_real_graph_jepa_ridge,0.26487394957983196,-0.06904930646957579,5
external_pretrained_weak_diffusion_real_graph_alpha_0_05_jepa_ridge,0.2619378353751139,-0.06390604434544903,5
```

## Target metrics

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
external_pretrained_no_graph_identity_jepa_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.15940062772096789,0.11500522065180775,-0.05299163034382803,0.634866045999411,0.7520989666093701
external_pretrained_no_graph_identity_jepa_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.40868684823326923,0.4387545422006983,0.19248394480067166,0.4339060849603663,0.5212419919443048
external_pretrained_no_graph_identity_jepa_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2692112989774223,0.26441895737275817,0.06157736967851235,0.48896888288256607,0.6031953811673637
external_pretrained_no_graph_identity_jepa_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.019985825655563432,-0.0677440751880747,-0.13539758134571023,0.3669794155497361,0.46841802275206323
external_pretrained_no_graph_identity_jepa_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5384225979548446,0.5505743424552592,0.30308135717531504,0.3692209518036312,0.4564928970040442
external_pretrained_non_graph_jepa_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.15940062772096789,0.11500522065180775,-0.05299163034382803,0.634866045999411,0.7520989666093701
external_pretrained_non_graph_jepa_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.40868684823326923,0.4387545422006983,0.19248394480067166,0.4339060849603663,0.5212419919443048
external_pretrained_non_graph_jepa_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2692112989774223,0.26441895737275817,0.06157736967851235,0.48896888288256607,0.6031953811673637
external_pretrained_non_graph_jepa_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.019985825655563432,-0.0677440751880747,-0.13539758134571023,0.3669794155497361,0.46841802275206323
external_pretrained_non_graph_jepa_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5384225979548446,0.5505743424552592,0.30308135717531504,0.3692209518036312,0.4564928970040442
external_pretrained_residual_real_graph_jepa_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.1993925280955756,0.14321755078847492,-0.05658260982974728,0.6340965438677477,0.7533803031433978
external_pretrained_residual_real_graph_jepa_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.39546420978029767,0.4352847288002828,0.18124718702010056,0.43332355593317534,0.524856059380689
external_pretrained_residual_real_graph_jepa_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.25928925787182344,0.25459956535141987,0.04127584667149242,0.4923807607818037,0.6096851337936167
external_pretrained_residual_real_graph_jepa_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.06904930646957579,-0.13047073289933317,-0.23120554734023369,0.38033554977539846,0.48778101826090914
external_pretrained_residual_real_graph_jepa_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5392730586210388,0.5626157072821633,0.31641924080549466,0.36585361504716307,0.45210353029278344
external_pretrained_strict_shuffled_residual_graph_jepa_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.1866963652931052,0.12861677390185153,-0.07733879557298051,0.6411088516062113,0.7607442561659565
external_pretrained_strict_shuffled_residual_graph_jepa_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.4054267490128582,0.4402525478152564,0.1850750874244549,0.43033096565165774,0.523627696882837
external_pretrained_strict_shuffled_residual_graph_jepa_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.25744659309506934,0.25146743127662574,0.03761526270509896,0.49522432595065813,0.6108479694833453
external_pretrained_strict_shuffled_residual_graph_jepa_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.060625696061557155,-0.11974036525192462,-0.21215242629020747,0.37828333677866394,0.48399205412676305
external_pretrained_strict_shuffled_residual_graph_jepa_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5358914650197428,0.5573845920592595,0.31065785985639705,0.3663643737614975,0.45400475066484297
external_pretrained_weak_diffusion_real_graph_alpha_0_05_jepa_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.20093145692011746,0.14544286296198433,-0.05565183676213192,0.6338829552793678,0.7530483931773552
external_pretrained_weak_diffusion_real_graph_alpha_0_05_jepa_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.41156221524754477,0.442875754233759,0.18814087294292825,0.4294299373519061,0.5226418128683231
external_pretrained_weak_diffusion_real_graph_alpha_0_05_jepa_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.25210084033613445,0.2509599418335971,0.03887845361308262,0.49251781735399824,0.6104469495290346
external_pretrained_weak_diffusion_real_graph_alpha_0_05_jepa_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.06390604434544903,-0.1290402164352672,-0.22818991328792215,0.3793608159319014,0.48718328261861304
external_pretrained_weak_diffusion_real_graph_alpha_0_05_jepa_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5090007087172218,0.5310399160640239,0.2779276246155521,0.3788662365283805,0.4646579246904039
stage27c_module_pca_ridge_reference,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3347372684013365,0.3163520312175891,0.09975961956193147,0.5908527814398361,0.6954113538288077
stage27c_module_pca_ridge_reference,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5284398096588033,0.6623974952216051,0.4280899577385401,0.35143710200981665,0.4386596361996292
stage27c_module_pca_ridge_reference,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.30229826870507237,0.27877065050186,0.07752413383312962,0.4963336075201987,0.5980483240374914
stage27c_module_pca_ridge_reference,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.016077756403766325,-0.042985908308886815,-0.09295916718496233,0.359161712235905,0.459580488795249
stage27c_module_pca_ridge_reference,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4519590968917688,0.47243591481850106,0.20964454842080216,0.3896968592871398,0.4861320000855132
stage31_weak_residual_real_graph_alpha_0_05_reference,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.33204414295838813,0.31600256353109796,0.09956542131218349,0.5909258480482622,0.6954863562328477
stage31_weak_residual_real_graph_alpha_0_05_reference,AT8,AT8,percent AT8 positive area_Grey matter,84,0.528136073706591,0.6617975636541716,0.42724710747546824,0.3517552984063907,0.438982753685565
stage31_weak_residual_real_graph_alpha_0_05_reference,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3040194391009416,0.2792586796340217,0.07779071941605731,0.4962670874882245,0.5979619030333984
stage31_weak_residual_real_graph_alpha_0_05_reference,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.01565252607066923,-0.04353202637769836,-0.09365891323555298,0.3592720457767519,0.459727584032288
stage31_weak_residual_real_graph_alpha_0_05_reference,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.45199959501873044,0.4717509978896238,0.20883927819315518,0.3894818570209831,0.4863795899279116
```

## Leakage audit

```csv
external_labels_used_for_supervised_pathology_prediction,clean_holdout_used,sea_ad_used_during_external_pretraining,donor_leakage_detected,fold_local_scaling_and_ridge_only,locked_donor_folds_used,leakage_audit_pass
False,False,False,False,True,True,True
```

## Graph-control audit

```csv
comparison,left_condition,right_condition,delta_mean_pooled_oof_spearman,graph_gate_pass
real_minus_no_graph_identity,external_pretrained_residual_real_graph_jepa_ridge,external_pretrained_no_graph_identity_jepa_ridge,-0.006273159866356182,False
real_minus_strict_shuffled,external_pretrained_residual_real_graph_jepa_ridge,external_pretrained_strict_shuffled_residual_graph_jepa_ridge,-9.314569201174239e-05,False
```

## External pretraining audit

```csv
stage32c_matrix,n_external_cells,n_external_genes,n_encoder_components,encoder_method,external_transform,external_labels_used_for_supervision,sea_ad_used_during_external_pretraining,clean_holdout_used,stage32c_ready,matrix_path_exists,stage32c_dataset_id,stage32c_gene_overlap_fraction,stage32c_n_obs,stage32c_n_vars
data/external_pretraining/stage32c/stage32c_human_external_pretraining_matrix.h5ad,100000,2863,32,truncated_svd_frozen_external_encoder,log1p_clipped_nonnegative,False,False,False,True,True,b165f033-9dec-468a-9248-802fc6902a74,0.968211024687183,100000,2863
```

## Pass/fail

```csv
stage33b_run,stage32c_ready,matrix_path_exists,best_external_condition,best_external_mean_pooled_oof_spearman,stage27c_reference_mean,stage31_reference_mean,best_minus_stage27c,best_minus_stage31,minimum_success_threshold,all_five_targets_reported,target_degradation_gate_pass,stage33b_run_pass,stage33b_internal_performance_pass,stage33b_graph_specific_pass,controlled_interpretation
True,True,True,external_pretrained_no_graph_identity_jepa_ridge,0.27114710944618814,0.3267024400121495,0.32637035537106407,-0.05555533056596135,-0.05522324592487593,0.3228,True,False,True,False,False,External pretraining did not improve over the current Stage 27C internal no-graph reference.
```
