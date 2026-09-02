# Stage 34B HBCC external pretraining report v1

## Executive summary

HBCC cells used: `100000`. Best condition: `hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph` with mean pooled donor-level OOF Spearman `0.2782`.
Stage 33C best: `0.3049`. Stage 34A best: `0.2945`. Stage 27C reference: `0.3267`.
Run pass: `True`. Dataset rescue pass: `False`. Full internal performance pass: `False`. Graph-specific pass: `False`.

## Controlled interpretation

HBCC external pretraining did not rescue the external-pretraining deficit under this compact benchmark.
Graph-specific utility remains unestablished.

This is an internal SEA-AD benchmark using an approved HBCC external pretraining dataset. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.

## HBCC cell-type audit

```csv
cell_type,n_cells
oligodendrocyte,27795
L2/3 intratelencephalic projecting glutamatergic neuron,12158
astrocyte,11706
L2/3-6 intratelencephalic projecting glutamatergic neuron,8009
oligodendrocyte precursor cell,7707
VIP GABAergic cortical interneuron,4947
sst GABAergic cortical interneuron,4769
pvalb GABAergic cortical interneuron,4506
microglial cell,4458
GABAergic neuron,2159
endothelial cell,2085
lamp5 GABAergic cortical interneuron,2030
L6 intratelencephalic projecting glutamatergic neuron,1838
pericyte,1071
L6 corticothalamic-projecting glutamatergic cortical neuron,1009
L6b glutamatergic neuron of the primary motor cortex,892
vascular leptomeningeal cell,775
L5/6 near-projecting glutamatergic neuron,773
smooth muscle cell,353
perivascular macrophage,345
T cell,207
natural killer cell,194
L5 extratelencephalic projecting glutamatergic cortical neuron,144
B cell,62
plasma cell,8
```

## HBCC matrix manifest

```csv
dataset_id,dataset_name,approved_for_pretraining,matrix_path,metadata_path,gene_map_path,matrix_reused,n_obs,n_vars,max_cells,downsampled,sampling_logic,gene_overlap_fraction,gene_overlap_pass,normalization_status,benchmark_transform,clean_holdout_used,sea_ad_used_during_external_pretraining,external_labels_used_for_supervised_pathology_prediction,canonical_source_gene_count,canonical_target_gene_count,canonical_union_gene_count,canonical_gene_universe_pass
5c97eeeb-7e52-44b3-b010-b832b1f5424c,HBCC_Cohort,True,data/external_pretraining/stage34b/stage34b_hbcc_external_pretraining_matrix.h5ad,data/external_pretraining/stage34b/stage34b_hbcc_external_pretraining_metadata.csv,data/external_pretraining/stage34b/stage34b_hbcc_external_pretraining_gene_map.csv,False,100000,2863,100000,True,stratified_by_donor_id;cell_type;tissue;disease,0.968211024687183,True,raw_count_like,raw_count_size_factor_log1p,False,False,False,2957,2957,2957,True
```

## Mean metrics

```csv
condition,mean_pooled_oof_spearman,min_target_pooled_oof_spearman,n_targets
stage27c_module_pca_ridge_reference,0.3267024400121495,0.016077756403766325,5
stage31_weak_residual_real_graph_alpha_0_05_reference,0.32637035537106407,0.01565252607066923,5
stage33c_best_reference,0.30493874658297054,-0.0865849954439607,5
stage34a_best_reference,0.2945226283284398,-0.0051635111876075,5
hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,0.27822213222638453,-0.06603219601093449,5
hbcc_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,0.27070163004961023,0.02743748101650299,5
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,0.24724511491343523,0.01816340994229017,5
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,0.21966994026526274,-0.029482636428065204,5
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,0.21835780095170598,-0.01796091930748203,5
```

## Target metrics

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
hbcc_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.162114002227397,0.15109264622614224,0.003679376452717542,0.6191359892876032,0.7315804518648649
hbcc_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.35814518578515747,0.38320222260174636,0.14580407345684399,0.4473648485395048,0.5360959927018641
hbcc_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2190746177989268,0.19257724336683363,0.030409096883606823,0.5136417728198128,0.6131306648482383
hbcc_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.02743748101650299,-0.0023683077151335275,-0.05942501661976207,0.3604926100133624,0.4524751431590821
hbcc_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5867368634200668,0.6253031980790275,0.3894570443912194,0.3542262466052669,0.4272687160402613
hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.24254328237319026,0.257423590629054,0.06109268741376528,0.5966143543697314,0.7101889211849315
hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.4509263946542473,0.559777419090559,0.3129829422591256,0.4023364201160176,0.4807813061207997
hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.23849346967702745,0.19745330119551976,0.014467973389184374,0.5153897638245267,0.6181503823192162
hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.06603219601093449,-0.12708707322291174,-0.17959691361040764,0.37173924770088035,0.4774483842315554
hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5251797104383922,0.538830150046078,0.2897009406009582,0.3720687601986827,0.4608542564739456
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.126293408929837,0.11243773215284356,-0.026398077063503722,0.6268505344837598,0.7425410147564366
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.3868178596739901,0.41710573910385845,0.1709188604320997,0.44653114014986417,0.528156137240219
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.22472410651007393,0.1996101528514288,0.022645893639992254,0.5106317783048178,0.615580341428151
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.01816340994229017,-0.038529617985282,-0.10436169548950902,0.3624184211070775,0.46197160398085885
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4802267895109851,0.49026543114247406,0.2302192100608017,0.38708061273651384,0.47976274171671285
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.13204414295838818,0.07739383287082624,-0.0792508041652038,0.6421813031192178,0.761419022899649
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.33631669535284,0.3564414713129256,0.09932787021042178,0.4605033032086664,0.550487136421348
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.1447605548243394,0.11013958803312747,-0.13036190422235006,0.5500717666288667,0.6620145389277337
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.01796091930748203,-0.06604201444742949,-0.1562835636975266,0.3679371193649219,0.47270673528061713
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.49662853093044446,0.5341966705132016,0.28456313985682036,0.3771939438325564,0.46251800009004124
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.10841348587627822,0.08268757838445383,-0.08117819647139002,0.6405457269816341,0.7620986140260319
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.38106712564543893,0.4013560028095628,0.1451652718140879,0.4500089012511309,0.536296412177064
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.1550470790725929,0.1032669066999539,-0.1319905112622093,0.548494398429229,0.6624912771585041
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.029482636428065204,-0.09559124607409897,-0.17098031844558825,0.3705855640936487,0.4757013807434571
hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4833046471600689,0.4905441649664246,0.23413805448733416,0.3879623324664469,0.4785399815936543
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
stage33c_best_reference,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.2926192163612433,0.2432224881473125,0.0446677351121721,0.6107178278630927,0.716373900907084
stage33c_best_reference,AT8,AT8,percent AT8 positive area_Grey matter,84,0.4517768553204414,0.4919660089793308,0.2394138928276458,0.4184721712923812,0.5058689309167852
stage33c_best_reference,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3001316189126253,0.2827408139798393,0.0750276147741908,0.48689578329546,0.5988570336722973
stage33c_best_reference,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.0865849954439607,-0.1550458286821346,-0.1533907373452825,0.3742581326889167,0.4721150487329427
stage33c_best_reference,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5667510377645034,0.5779063148556405,0.3269617156628633,0.3583592242133251,0.448603716944315
stage34a_best_reference,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3044851675610003,0.245175149737798,0.0207722568574034,0.6076228771886031,0.7252778043513222
stage34a_best_reference,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5023590158955148,0.5018955875195302,0.2510754106481919,0.4111339240887759,0.5019758893759514
stage34a_best_reference,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2226587020350309,0.193239573084257,0.0342917813156027,0.5058626477267751,0.6119018058993927
stage34a_best_reference,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.0051635111876075,-0.1005585059035286,-0.1136972166578738,0.3681623456960802,0.4639200914071206
stage34a_best_reference,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4482737673382606,0.4520045743694374,0.1559303452610085,0.4015491863369473,0.5023797515505494
```

## Graph-control audit

```csv
comparison,left_condition,right_condition,delta_mean_pooled_oof_spearman,graph_gate_pass
real_minus_no_graph_identity,hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,-0.02888731396172925,False
real_minus_strict_shuffled,hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,-0.0013121393135567538,False
```

## Leakage audit

```csv
approved_hbcc_dataset_used,clean_holdout_used,sea_ad_used_during_external_pretraining,external_labels_used_for_supervised_pathology_prediction,locked_donor_folds_used,fold_local_downstream_scaling_and_ridge,in_silico_ablation_run,leakage_audit_pass
True,False,False,False,True,True,False,True
```

## Pass/fail

```csv
stage34b_run,approved_hbcc_dataset_used,n_hbcc_cells,gene_overlap_fraction,best_stage34b_condition,best_stage34b_mean_pooled_oof_spearman,stage33c_best_mean,stage34a_best_mean,stage27c_reference_mean,best_minus_stage33c,best_minus_stage34a,best_minus_stage27c,all_five_targets_reported,target_degradation_gate_pass,stage34b_run_pass,stage34b_dataset_rescue_pass,stage34b_full_internal_performance_pass,stage34b_graph_specific_pass,controlled_interpretation,graph_interpretation
True,True,100000,0.968211024687183,hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,0.27822213222638453,0.3049387465829706,0.2945226283284398,0.3267024400121495,-0.026716614356586066,-0.01630049610205525,-0.04848030778576495,True,False,True,False,False,False,HBCC external pretraining did not rescue the external-pretraining deficit under this compact benchmark.,Graph-specific utility remains unestablished.
```
