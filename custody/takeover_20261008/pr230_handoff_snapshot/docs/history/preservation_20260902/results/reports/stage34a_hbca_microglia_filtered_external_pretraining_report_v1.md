# Stage 34A HBCA microglia/myeloid-filtered external pretraining report v1

## Executive summary

Filtered cells: `10325`. Best Stage 34A condition: `filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph` with mean pooled donor-level OOF Spearman `0.2945`.
Stage 33C best: `0.3049`. Stage 27C reference: `0.3267`.
Run pass: `True`. Biological-filter rescue pass: `False`. Full internal performance pass: `False`. Graph-specific pass: `False`.

## Controlled interpretation

Microglia/myeloid filtering did not rescue the external-pretraining deficit under this implementation.
Real topology outperformed shuffled topology but did not improve over the no-graph identity reference.

This is an internal SEA-AD benchmark using the approved HBCA external pretraining dataset. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.

## Cell-type filter audit

```csv
metadata_column,label,n_cells,match_class,matched_terms
cell_type,central nervous system macrophage,10325,exact_myeloid_or_pvm,macrophage
```

## Filtered matrix manifest

```csv
source_matrix,filtered_matrix,approved_dataset_id,approved_dataset_used,filter_logic,n_source_cells,n_exact_microglia_myeloid_pvm_cells,n_filtered_cells,downsampled,max_cells,n_source_genes,n_filtered_genes,canonical_genes,gene_overlap_fraction,minimum_gene_overlap_fraction,gene_overlap_pass,normalization_status,metadata_cell_type_columns_used,cell_type,assay,tissue,region,donor,sample,disease_condition,suspension_type,dataset_id,canonical_source_gene_count,canonical_target_gene_count,canonical_union_gene_count,canonical_gene_universe_pass
C:\Users\dushy\Desktop\Jepa project\data\external_pretraining\stage32c\stage32c_human_external_pretraining_matrix.h5ad,data/external_pretraining/stage34a/stage34a_hbca_microglia_filtered_pretraining_matrix.h5ad,b165f033-9dec-468a-9248-802fc6902a74,True,exact_microglia_myeloid_pvm_terms,100000,10325,10325,False,100000,2863,2863,2957,0.968211024687183,0.85,True,source_raw_count_like; benchmark_transform_raw_count_size_factor_log1p,cell_type;cell_type_ontology_term_id,cell_type;cell_type_ontology_term_id,assay;assay_ontology_term_id,tissue;tissue_ontology_term_id,tissue,donor_id,donor_id,disease;disease_ontology_term_id,,dataset_id;stage32c_source_dataset_id,2957,2957,2957,True
```

## Mean metrics

```csv
condition,mean_pooled_oof_spearman,min_target_pooled_oof_spearman,n_targets
stage27c_module_pca_ridge_reference,0.3267024400121495,0.016077756403766325,5
stage31_weak_residual_real_graph_alpha_0_05_reference,0.32637035537106407,0.01565252607066923,5
stage33c_best_reference,0.30493874658297054,-0.0865849954439607,5
filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,0.2945226283284398,-0.0051635111876075735,5
filtered_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,0.29219803584084236,-0.12426850258175559,5
filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,0.2734150045560393,-0.07421281765718335,5
filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,0.26469575782120075,-0.12888528905538119,5
filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,0.263804799028045,-0.08834666396679154,5
```

## Target metrics

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.30448516756100036,0.24517514973779803,0.02077225685740347,0.6076228771886031,0.7252778043513222
filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5023590158955148,0.5018955875195302,0.25107541064819194,0.41113392408877597,0.5019758893759514
filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2226587020350309,0.19323957308425707,0.03429178131560273,0.5058626477267751,0.6119018058993927
filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.0051635111876075735,-0.10055850590352869,-0.1136972166578738,0.36816234569608025,0.46392009140712065
filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4482737673382606,0.4520045743694374,0.15593034526100857,0.40154918633694736,0.5023797515505494
filtered_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3259289257871824,0.3062711887793885,0.08554596927949265,0.5922329072332828,0.7008796841383853
filtered_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5166346056494887,0.5887313234922036,0.34045178989675384,0.3856688002612862,0.4710717775276321
filtered_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2224562114002227,0.1877949392345675,0.005253120115927823,0.5149234690205313,0.6210335519349095
filtered_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.12426850258175559,-0.16331820332451125,-0.20147376849887855,0.37767589454756967,0.48185543386250107
filtered_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5202389389490736,0.5524123008913815,0.30306998984319344,0.3701758532697121,0.4564966198813595
filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.27923458540042523,0.2489426202683269,0.046702503627872205,0.6068607425902917,0.7156105894877947
filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,AT8,AT8,percent AT8 positive area_Grey matter,84,0.4677736154702845,0.4336061360685605,0.1721081286490438,0.4369801987314875,0.5277771968148601
filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2153892882454187,0.18532883504524214,0.01256148267495616,0.5115767437661618,0.6187479928168395
filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.07421281765718335,-0.12039500343718045,-0.14193362491420092,0.37206782689095175,0.469764338430398
filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4788903513212514,0.49456795399810954,0.24430095188588885,0.39192333891100034,0.4753542934053662
filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.2856130403968816,0.26817308049293065,0.03781756270408898,0.6058755353562926,0.7189376786810985
filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.4716816847220816,0.5016226889716483,0.24999348447278857,0.4080239613517235,0.5023383456613694
filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.18161385035942085,0.16847490889374897,-0.02599319185767124,0.516388294379176,0.6307118789500904
filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.12888528905538119,-0.14869642266152228,-0.20526549317937515,0.37959413455407087,0.482615177418416
filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5134555026830009,0.5482477455438572,0.30003229181982305,0.3764621653453359,0.45749040053229995
filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.269130302723499,0.24886019469234166,0.0259280995603155,0.6103633365818029,0.7233659133173446
filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.4595727447605549,0.49425908775579763,0.24179136556866432,0.4100983583646444,0.5050776786779312
filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.1609800546724714,0.1421246412280522,-0.04900255963411393,0.5249451163499048,0.6377449746806421
filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.08834666396679154,-0.12044838867917644,-0.18532355941388623,0.37490563316981385,0.47860592684170217
filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.5176875569504911,0.5526931445256938,0.3049594824652426,0.3722038166405512,0.45587738093092417
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
```

## Graph-control audit

```csv
comparison,left_condition,right_condition,delta_mean_pooled_oof_spearman,graph_gate_pass
real_minus_no_graph_identity,filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph,-0.008719246734838537,False
real_minus_strict_shuffled,filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05,filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05,0.0008909587931557605,True
```

## Leakage audit

```csv
approved_hbca_dataset_used,clean_holdout_used,sea_ad_used_during_external_pretraining,external_labels_used_for_supervised_pathology_prediction,locked_donor_folds_used,fold_local_downstream_scaling_and_ridge,in_silico_ablation_run,leakage_audit_pass
True,False,False,False,True,True,False,True
```

## Pass/fail

```csv
stage34a_run,approved_hbca_dataset_used,microglia_myeloid_filter_attempted,n_filtered_cells,gene_overlap_fraction,best_stage34a_condition,best_stage34a_mean_pooled_oof_spearman,stage33c_best_mean,stage27c_reference_mean,best_minus_stage33c,best_minus_stage27c,all_five_targets_reported,target_degradation_gate_pass,stage34a_run_pass,stage34a_biological_filter_rescue_pass,stage34a_full_internal_performance_pass,stage34a_graph_specific_pass,controlled_interpretation,graph_interpretation
True,True,True,10325,0.968211024687183,filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph,0.2945226283284398,0.3049387465829706,0.3267024400121495,-0.010416118254530815,-0.0321798116837097,True,False,True,False,False,False,Microglia/myeloid filtering did not rescue the external-pretraining deficit under this implementation.,Real topology outperformed shuffled topology but did not improve over the no-graph identity reference.
```
