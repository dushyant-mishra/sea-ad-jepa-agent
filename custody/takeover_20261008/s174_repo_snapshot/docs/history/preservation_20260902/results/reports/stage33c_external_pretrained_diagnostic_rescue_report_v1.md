# Stage 33C external-pretrained diagnostic/rescue report v1

## Executive summary

Best Stage 33C condition: `ext_svd32_raw_count_size_factor_log1p_direct_no_graph` with mean pooled donor-level OOF Spearman `0.3049`.
Stage 33B best: `0.2711`. Stage 27C reference: `0.3267`. Stage 31 reference: `0.3264`.
Run pass: `True`. Rescue performance pass: `False`. Graph-specific pass: `False`.

## Controlled interpretation

Stage 33C rescued part of the external-pretraining deficit but did not improve over the Stage 27C internal no-graph reference.
Real topology outperformed shuffled topology but did not improve over the no-graph identity reference.

This is an internal SEA-AD diagnostic benchmark using approved external self-supervised pretraining. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.

## Rescue grid

```csv
condition,n_components_requested,transform,projection_variant,graph_variant,graph_alpha,n_downstream_features,included_in_capped_grid,condition_mean_pooled_oof_spearman,beats_stage33b_best,beats_stage27c_reference
ext_svd16_log1p_direct_no_graph,16,log1p_clipped_nonnegative,direct,no_graph_identity,0.0,16,True,0.28811987445580645,True,False
ext_svd32_log1p_direct_no_graph,32,log1p_clipped_nonnegative,direct,no_graph_identity,0.0,32,True,0.2699564645135163,False,False
ext_svd64_log1p_direct_no_graph,64,log1p_clipped_nonnegative,direct,no_graph_identity,0.0,64,True,0.24395261719145492,False,False
ext_svd128_log1p_direct_no_graph,128,log1p_clipped_nonnegative,direct,no_graph_identity,0.0,128,True,0.25163511187607573,False,False
ext_svd32_raw_count_size_factor_log1p_direct_no_graph,32,raw_count_size_factor_log1p,direct,no_graph_identity,0.0,32,True,0.3049387465829706,True,False
ext_svd32_zscore_gene_after_log1p_direct_no_graph,32,zscore_gene_after_log1p,direct,no_graph_identity,0.0,32,True,0.28003239850156936,True,False
ext_svd32_log1p_concat_module_pca_no_graph,32,log1p_clipped_nonnegative,concat_module_pca,no_graph_identity,0.0,40,True,0.30139516047382814,True,False
ext_svd32_log1p_residualized_by_module_pca_no_graph,32,log1p_clipped_nonnegative,residualized_by_module_pca,no_graph_identity,0.0,32,True,-0.04228814417333199,False,False
ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,32,log1p_clipped_nonnegative,direct,residual_real_graph,0.05,64,True,0.2568755695049104,False,False
ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,32,log1p_clipped_nonnegative,direct,strict_shuffled_residual_graph,0.05,64,True,0.2559967601498431,False,False
```

## Mean metrics

```csv
condition,mean_pooled_oof_spearman,min_target_pooled_oof_spearman,n_targets
stage27c_module_pca_ridge_reference,0.3267024400121495,0.016077756403766325,5
stage31_weak_residual_real_graph_alpha_0_05_reference,0.32637035537106407,0.01565252607066923,5
ext_svd32_raw_count_size_factor_log1p_direct_no_graph,0.3049387465829706,-0.08658499544396071,5
ext_svd32_log1p_concat_module_pca_no_graph,0.30139516047382814,-0.09037157031487295,5
ext_svd16_log1p_direct_no_graph,0.28811987445580645,0.07844487192467349,5
ext_svd32_zscore_gene_after_log1p_direct_no_graph,0.28003239850156936,-0.013850359420876784,5
ext_svd32_log1p_direct_no_graph,0.2699564645135163,-0.044426445276905945,5
ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,0.2568755695049104,-0.08713172015794268,5
ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,0.2559967601498431,-0.07939657790827175,5
ext_svd128_log1p_direct_no_graph,0.25163511187607573,0.04424420370557862,5
ext_svd64_log1p_direct_no_graph,0.24395261719145492,-0.11029664877999391,5
ext_svd32_log1p_residualized_by_module_pca_no_graph,-0.04228814417333199,-0.09136377442543282,5
```

## Target metrics

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
ext_svd128_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.19919003746076744,0.18830756108354121,-0.05420978079878047,0.6216637160141355,0.7525338726703531
ext_svd128_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.3876683203401843,0.45199906070706575,0.18306954130816377,0.42435258513759894,0.5242716299346728
ext_svd128_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.11718133036347068,0.1323054822018134,-0.10107698839561685,0.5346635459846654,0.6533826746151279
ext_svd128_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.04424420370557862,0.011898935987095044,-0.1632877147949059,0.36390360194729254,0.47413627674381714
ext_svd128_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5098916675103776,0.5426881977603432,0.29388139374726463,0.37313722937729105,0.45949608016316756
ext_svd16_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.2015794269515035,0.1699279094233663,-0.016549753927330046,0.6238745011842957,0.7389700756231251
ext_svd16_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.421443758226182,0.450585880900296,0.20152210715796093,0.4337381122112864,0.5183167706868144
ext_svd16_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.23221625999797513,0.22820071724006719,0.047561830608883415,0.5021930683844326,0.6076831118190928
ext_svd16_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.07844487192467349,0.04119748538553607,-0.03716414409599089,0.3476679282393488,0.4476961517348309
ext_svd16_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.506915055178698,0.517838142652182,0.258665751857159,0.3715261058020045,0.47081470124944486
ext_svd32_log1p_concat_module_pca_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.2697580236914043,0.23889377873241927,0.035695717340886834,0.6078033205591188,0.7197299580018561
ext_svd32_log1p_concat_module_pca_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.487212716411866,0.5729174113763371,0.32722491445602764,0.3921510344862238,0.4757718723382959
ext_svd32_log1p_concat_module_pca_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2744558064189531,0.26145562606157574,0.054892375926186565,0.4962815601160602,0.6053400446775181
ext_svd32_log1p_concat_module_pca_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.09037157031487295,-0.15645814075133202,-0.21778087711249583,0.3775125408941851,0.48511442556616824
ext_svd32_log1p_concat_module_pca_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5659208261617901,0.5656964783669328,0.3181228452439745,0.36266249745285845,0.4515398177821531
ext_svd32_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.1606763187202592,0.12216753910056125,-0.04808464056437245,0.6321834264600175,0.7503445122494363
ext_svd32_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.4070466740913233,0.41969914996269947,0.1754217211804756,0.4382017398089594,0.5267199379765082
ext_svd32_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2895616077756404,0.266032705315939,0.061405677351825005,0.4881186407841266,0.6032505584822266
ext_svd32_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.044426445276905945,-0.08436750970085731,-0.13920905299968833,0.3684759567550627,0.4692035917072225
ext_svd32_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5369241672572644,0.5577767999761025,0.3088816723815476,0.3668821647623344,0.4545892780885575
ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.20293611420471808,0.1463248517569381,-0.056831634971417966,0.6322682404911418,0.753469079724532
ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.390422192973575,0.4238889512901865,0.16845941459131608,0.43312966426392374,0.5289389372815926
ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2450339171813304,0.24896583980359704,0.03485268287529153,0.4986950023575408,0.6117240780299269
ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.08713172015794268,-0.14210704797500057,-0.22669562009239863,0.3808326900785357,0.48688682348710743
ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5331173433228714,0.5533629001944848,0.30614335992750763,0.3691959996629285,0.45548896258618643
ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.1812493672167662,0.12368615143593276,-0.08314084431298974,0.6406716018232762,0.7627900139382499
ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.37896122304343427,0.410141647642281,0.15388786705117918,0.4395463036717399,0.5335532556500813
ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.256940366508049,0.24877210327913515,0.03379868171934586,0.49910052587952125,0.6120580073384414
ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.07939657790827175,-0.12927084894512847,-0.21013494346289008,0.378409553456039,0.48358911293334983
ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5422294218892376,0.5519889155866828,0.30466038215689506,0.3679283695169785,0.45597546039215314
ext_svd32_log1p_residualized_by_module_pca_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,-0.08245418649387466,-0.04796406789743232,-0.15662158768084478,0.6625447759586761,0.788239472760728
ext_svd32_log1p_residualized_by_module_pca_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,-0.09136377442543282,-0.13181099491710757,-0.09067828250215881,0.5163276053534208,0.6057761150386667
ext_svd32_log1p_residualized_by_module_pca_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,-0.0794573250987142,-0.12163151209350571,-0.15677761860104988,0.5386079027005797,0.6697052597417097
ext_svd32_log1p_residualized_by_module_pca_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.0697985218183659,-0.17871139049717633,-0.24132901393505257,0.3751061238676111,0.4897822786296988
ext_svd32_log1p_residualized_by_module_pca_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.11163308696972767,0.11314167946959638,-0.029867969932770855,0.450426619080086,0.5549243204429269
ext_svd32_raw_count_size_factor_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.29261921636124333,0.2432224881473125,0.04466773511217215,0.6107178278630927,0.716373900907084
ext_svd32_raw_count_size_factor_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.45177685532044143,0.4919660089793308,0.2394138928276458,0.4184721712923812,0.5058689309167852
ext_svd32_raw_count_size_factor_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3001316189126253,0.28274081397983936,0.07502761477419084,0.48689578329546007,0.5988570336722973
ext_svd32_raw_count_size_factor_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.08658499544396071,-0.15504582868213465,-0.15339073734528252,0.3742581326889167,0.47211504873294274
ext_svd32_raw_count_size_factor_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5667510377645034,0.5779063148556405,0.32696171566286336,0.35835922421332517,0.448603716944315
ext_svd32_zscore_gene_after_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.23073807836387572,0.2077140589375839,0.02366392001669504,0.6222706705144303,0.7242061385843059
ext_svd32_zscore_gene_after_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5015288042928016,0.5053953495954742,0.25121481231583664,0.41765883798403936,0.501929169363238
ext_svd32_zscore_gene_after_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.1854206742938139,0.17063110031092604,0.008044876763752096,0.5069968525487418,0.6201614744488779
ext_svd32_zscore_gene_after_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.013850359420876784,-0.033017723983134004,-0.12089290423450261,0.36144807574774845,0.46541639094177006
ext_svd32_zscore_gene_after_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.49632479497823234,0.5072950131122497,0.25434706066575963,0.384996776289613,0.47218409070978795
ext_svd64_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.13572947251189635,0.10542874950590352,-0.09581636624252043,0.6413943216827006,0.7672403301634834
ext_svd64_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.39931153184165236,0.4597155864953961,0.20805184051922831,0.4188941267407626,0.5161930938168082
ext_svd64_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.27963956667004153,0.26008164450184407,0.042482375172286924,0.4853307840866035,0.6093013768664571
ext_svd64_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.11029664877999391,-0.131037024172159,-0.24160661996755817,0.3853366916676202,0.4898370420778777
ext_svd64_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5153791637136783,0.5326788115639168,0.2833566540423321,0.37149482861542177,0.4629078222942811
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

## Graph-control audit

```csv
comparison,left_condition,right_condition,delta_mean_pooled_oof_spearman,graph_gate_pass
real_minus_no_graph_identity,ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,ext_svd32_log1p_direct_no_graph,-0.013080895008605875,False
real_minus_strict_shuffled,ext_svd32_log1p_direct_residual_real_graph_alpha_0_05,ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,0.0008788093550673448,True
```

## Leakage audit

```csv
external_labels_used_for_supervised_pathology_prediction,clean_holdout_used,sea_ad_used_during_external_pretraining,donor_leakage_detected,fold_local_downstream_scaling_and_ridge,locked_donor_folds_used,in_silico_ablation_run,leakage_audit_pass
False,False,False,False,True,True,False,True
```

## External pretraining diagnostic audit

```csv
stage32c_matrix,n_external_cells,n_external_genes,encoder_method,component_grid_run,transform_grid_run,zscore_transform_note,external_labels_used_for_supervision,sea_ad_used_during_external_pretraining,clean_holdout_used,stage32c_ready,stage33b_loaded,matrix_path_exists,stage32c_dataset_id,stage32c_gene_overlap_fraction,stage32c_n_obs,stage32c_n_vars
data/external_pretraining/stage32c/stage32c_human_external_pretraining_matrix.h5ad,100000,2863,truncated_svd_frozen_external_encoder,16;32;64;128,log1p_clipped_nonnegative;raw_count_size_factor_log1p;zscore_gene_after_log1p,sparse_safe_log1p_std_scaled_without_dense_centering,False,False,False,True,True,True,b165f033-9dec-468a-9248-802fc6902a74,0.968211024687183,100000,2863
```

## Pass/fail

```csv
stage33c_run,stage32c_ready,stage33b_results_loaded,matrix_path_exists,n_external_conditions_run,best_stage33c_condition,best_stage33c_mean_pooled_oof_spearman,stage33b_best_mean,stage27c_reference_mean,stage31_reference_mean,best_minus_stage33b,best_minus_stage27c,minimum_success_threshold,all_five_targets_reported,target_degradation_gate_pass,stage33c_run_pass,stage33c_rescue_performance_pass,stage33c_graph_specific_pass,controlled_interpretation,graph_interpretation
True,True,True,True,10,ext_svd32_raw_count_size_factor_log1p_direct_no_graph,0.3049387465829706,0.27114710944618814,0.3267024400121495,0.32637035537106407,0.03379163713678246,-0.021763693429178887,0.3228,True,False,True,False,False,Stage 33C rescued part of the external-pretraining deficit but did not improve over the Stage 27C internal no-graph reference.,Real topology outperformed shuffled topology but did not improve over the no-graph identity reference.
```
