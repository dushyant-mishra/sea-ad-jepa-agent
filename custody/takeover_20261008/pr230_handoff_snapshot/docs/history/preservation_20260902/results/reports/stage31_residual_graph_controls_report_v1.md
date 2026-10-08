# Stage 31 residual graph controls report v1

## 1. Executive summary

Best Stage 31 condition: `weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05` (`0.3264`).
Stage 27C reference: `0.3267`; best minus reference: `-0.0003`.
Full Stage 31 pass: `False`. Target-specific partial pass: `True`.
Controlled interpretation: `graph_like_residual_features_contain_structure_but_topology_specific_utility_not_established`.

## 2. Why Stage 31 was run

Stage 30 showed that mandatory graph smoothing beat strict-shuffled topology but underperformed the Stage 27C no-graph rescue baseline. Stage 31 is explicitly an anti-oversmoothing experiment: it tests whether graph information helps when added as an optional residual feature layer rather than forcing sharp module/pathology signals through a smoothing transform.

## 3. Stage 27C and Stage 30 recap

Stage 27C `module_pca_ridge` passed with mean pooled donor-level OOF Spearman `0.3267`. Stage 30 real graph smoothing reached `0.3205`, beat strict-shuffled by about `0.0219`, but failed to beat no-graph/reference and failed the target-degradation gate.

## 4. What was run

- Loaded the frozen Stage 27C module-PCA ridge reference predictions.
- Ran residual real graph, residual no-graph, and residual strict-shuffled graph PCA-ridge controls.
- Ran target-specific ridge gates.
- Ran predeclared weak diffusion anti-oversmoothing conditions at alpha 0.05, 0.10, and 0.20.
- Ran hub-capped real graph residual diagnostics.
- Ran graph-residual-only diagnostic features without the Stage 27C skip path.

## 5. What was not run

- No external matrices, clean holdouts, or model selection on external datasets.
- No high-capacity GNN, full GAT, hyperbolic latent space, or VICReg-JEPA objective.
- No broad hyperparameter search.
- No manuscript claim update.

## 6. Locked benchmark policy

The official metric remains pooled donor-level OOF Spearman on locked Stage 24 donor folds. Required targets are AT8, 6e10/A beta, GFAP, Iba1, and NeuN. Minimum v3 success remains 0.3228, with no target allowed to drop below -0.02 versus module mean or Stage 27C reference for a full pass.

## 7. Feature construction

Stage 27C module features are preserved as an untouched skip path for every full-pass-eligible condition. Scaling, PCA, and ridge fitting occur inside each training fold only. The graph-residual-only condition is diagnostic and is not full-pass eligible.

## 8. Graph residual construction

Graph residuals are module summaries of `graph-smoothed expression minus identity/no-graph expression`. This directly asks what graph topology adds beyond the no-graph representation.

## 9. No-graph and strict-shuffled controls

`residual_no_graph_pca_ridge` controls added feature slots/capacity. `residual_strict_shuffled_graph_pca_ridge` controls graph-like topology while destroying biological edge correspondence.

## 10. Hub-capping / weak-diffusion diagnostics

Weak diffusion alphas were predeclared as 0.05, 0.10, and 0.20. Hub capping downweighted edges touching top-degree hubs to test whether hub dominance contributed to oversmoothing.

## 11. Leakage and holdout controls

No held-out donor leakage, external matrix use, or clean holdout use is permitted. Preprocessing is fold-local.

## 12. Mean pooled OOF results

```csv
condition,mean_pooled_oof_spearman,min_target_pooled_oof_spearman,n_targets
residual_no_graph_pca_ridge,0.3267024400121495,0.016077756403766325,5
stage27c_module_pca_ridge_reference,0.3267024400121495,0.016077756403766325,5
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,0.32637035537106407,0.01565252607066923,5
weak_diffusion_real_graph_residual_pca_ridge,0.3222800445479397,0.014275589753973878,5
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,0.3160554824339374,0.02452161587526577,5
target_gated_real_graph_residual_ridge,0.28679153589146505,-0.03717728055077453,5
residual_strict_shuffled_graph_pca_ridge,0.2682879416826972,0.021565252607066928,5
residual_real_graph_pca_ridge,0.26459046269110054,0.010570011136984915,5
hub_capped_real_graph_residual_pca_ridge,0.2632135263744052,0.013587121595626205,5
graph_residual_only_ridge,0.24853700516351118,-0.10146805710235904,5
```

## 13. Target-level results

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
graph_residual_only_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.21553103168978432,0.21132920184834672,0.043411081426327325,0.6050425408201259,0.7168449087890836
graph_residual_only_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.43071782930039487,0.5578230116910814,0.2996372147012115,0.38615708588960473,0.485428581449837
graph_residual_only_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.27194492254733216,0.2528845443840608,0.06202480670915744,0.4974464182581248,0.6030515631688884
graph_residual_only_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.10146805710235904,-0.16565287459957592,-0.1574065488794727,0.36869622780804284,0.4729362264925675
graph_residual_only_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.42595929938240357,0.4253565223960719,0.16010381813984287,0.39991134118908855,0.5011362129343174
hub_capped_real_graph_residual_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.17312949276095982,0.15777087546224003,0.004426444323594847,0.6239456316825761,0.7313061211280084
hub_capped_real_graph_residual_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.39935202996861396,0.4963349494908283,0.24521008338792183,0.4151837505556509,0.5039377095456817
hub_capped_real_graph_residual_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.28879214336336945,0.260754759347054,0.057134601548139985,0.4961059684103035,0.6046215471653446
hub_capped_real_graph_residual_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.013587121595626205,-0.02558378146364474,-0.11432067391803202,0.3583554341782142,0.46404992646334337
hub_capped_real_graph_residual_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4412068441834565,0.4410381223104304,0.19425157481136135,0.3973985106234104,0.4908431289449161
residual_no_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3347372684013365,0.31635203121758915,0.09975961956193147,0.5908527814398361,0.6954113538288077
residual_no_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5284398096588033,0.662397495221605,0.42808995773853975,0.3514371020098167,0.4386596361996293
residual_no_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.30229826870507237,0.27877065050185995,0.0775241338331295,0.4963336075201987,0.5980483240374915
residual_no_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.016077756403766325,-0.04298590830888682,-0.09295916718496233,0.359161712235905,0.4595804887952489
residual_no_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4519590968917688,0.4724359148185014,0.20964454842080227,0.38969685928713976,0.4861320000855131
residual_real_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.1713880733016098,0.15491256410813434,0.0028490778371604852,0.6244162538277493,0.7318852251085113
residual_real_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.41057001113698494,0.4778443856335364,0.22812570225382378,0.42330700425977125,0.5096090158301443
residual_real_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2865849954439607,0.2607279294815919,0.05705462496797209,0.49594461774991805,0.6046471894989938
residual_real_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.010570011136984915,-0.030514096475772527,-0.11764666216973496,0.35888025416749697,0.4647419510592897
residual_real_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4438392224359624,0.443049159732378,0.19607213692224068,0.39721357176012745,0.4902882933927165
residual_strict_shuffled_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.20346258985521923,0.18568494832674634,0.01876240597288381,0.6184873648095097,0.7260217339612733
residual_strict_shuffled_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.42928014579325713,0.5011853382410798,0.25112518387053706,0.4150911958759573,0.5019592085424966
residual_strict_shuffled_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.24169282170699602,0.23974428064496556,0.046998547839062654,0.5008389959944439,0.6078627806116242
residual_strict_shuffled_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.021565252607066928,-0.011989632471924734,-0.10432699286068647,0.3586450339476053,0.46196434560024474
residual_strict_shuffled_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4454388984509467,0.4480076862750935,0.20031646333661546,0.393362242533786,0.4889923453961966
stage27c_module_pca_ridge_reference,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3347372684013365,0.3163520312175891,0.09975961956193147,0.5908527814398361,0.6954113538288077
stage27c_module_pca_ridge_reference,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5284398096588033,0.6623974952216051,0.4280899577385401,0.35143710200981665,0.4386596361996292
stage27c_module_pca_ridge_reference,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.30229826870507237,0.27877065050186,0.07752413383312962,0.4963336075201987,0.5980483240374914
stage27c_module_pca_ridge_reference,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.016077756403766325,-0.042985908308886815,-0.09295916718496233,0.359161712235905,0.459580488795249
stage27c_module_pca_ridge_reference,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4519590968917688,0.47243591481850106,0.20964454842080216,0.3896968592871398,0.4861320000855132
target_gated_real_graph_residual_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.2860990179204212,0.2855651010836046,0.07936340462986657,0.592736386864239,0.7032449940882274
target_gated_real_graph_residual_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.47739192062367114,0.6063647517919768,0.35536791075515173,0.3743536595084052,0.4657145142191975
target_gated_real_graph_residual_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.26795585704161184,0.27073899453189126,0.0661052191275896,0.49535675277463587,0.6017384255206246
target_gated_real_graph_residual_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.03717728055077453,-0.08886138144165408,-0.17386869278582262,0.3631861838953712,0.4762877088798372
target_gated_real_graph_residual_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4396881644223955,0.4370206553840968,0.18758004087326108,0.3948090363242203,0.49287101127938415
weak_diffusion_real_graph_residual_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3274476055482434,0.31479812545243474,0.09888166528923725,0.5911582967144193,0.6957503691623362
weak_diffusion_real_graph_residual_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5298774931659411,0.6598656510786651,0.4245765892891523,0.3527233490576645,0.44000496423558005
weak_diffusion_real_graph_residual_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3034727143869596,0.2806342581135979,0.07854186380138717,0.49607557087910487,0.5977183318436673
weak_diffusion_real_graph_residual_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.014275589753973878,-0.044718306007656125,-0.09555271192927228,0.35954321664284655,0.46012544798850175
weak_diffusion_real_graph_residual_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.43632681988458033,0.45982771608821954,0.1996970221043214,0.39162249702092095,0.48918169741625095
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.33204414295838813,0.3160025635310978,0.09956542131218338,0.5909258480482622,0.6954863562328477
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.528136073706591,0.6617975636541717,0.4272471074754681,0.3517552984063907,0.438982753685565
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3040194391009416,0.2792586796340216,0.07779071941605731,0.49626708748822457,0.5979619030333984
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.01565252607066923,-0.04353202637769839,-0.09365891323555298,0.35927204577675187,0.4597275840322879
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.45199959501873044,0.4717509978896239,0.20883927819315506,0.389481857020983,0.4863795899279116
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3287840437379771,0.30674595436299057,0.09407276318652114,0.592576543011622,0.6976043673378666
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5131922648577503,0.650165582435818,0.4119811479711333,0.35684106680431915,0.444794530088681
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2909992912827782,0.25242160042589074,0.056365621166227675,0.5008731740592608,0.6048680549640725
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.02452161587526577,-0.04189341307165459,-0.09929430230703362,0.35959969788726187,0.46091050082475216
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.42278019641591574,0.42919215363908053,0.1716262848478629,0.39459335873886126,0.49768681832344974
```

## 14. Pairwise deltas

```csv
comparison,left_condition,right_condition,left_mean_pooled_oof_spearman,right_mean_pooled_oof_spearman,delta_mean_pooled_oof_spearman
residual_real_graph_pca_ridge_minus_stage27c_module_pca_ridge_reference,residual_real_graph_pca_ridge,stage27c_module_pca_ridge_reference,0.26459046269110054,0.3267024400121495,-0.06211197732104895
residual_real_graph_pca_ridge_minus_residual_no_graph_pca_ridge,residual_real_graph_pca_ridge,residual_no_graph_pca_ridge,0.26459046269110054,0.3267024400121495,-0.06211197732104895
residual_real_graph_pca_ridge_minus_residual_strict_shuffled_graph_pca_ridge,residual_real_graph_pca_ridge,residual_strict_shuffled_graph_pca_ridge,0.26459046269110054,0.2682879416826972,-0.00369747899159667
target_gated_real_graph_residual_ridge_minus_stage27c_module_pca_ridge_reference,target_gated_real_graph_residual_ridge,stage27c_module_pca_ridge_reference,0.28679153589146505,0.3267024400121495,-0.03991090412068443
target_gated_real_graph_residual_ridge_minus_residual_no_graph_pca_ridge,target_gated_real_graph_residual_ridge,residual_no_graph_pca_ridge,0.28679153589146505,0.3267024400121495,-0.03991090412068443
target_gated_real_graph_residual_ridge_minus_residual_strict_shuffled_graph_pca_ridge,target_gated_real_graph_residual_ridge,residual_strict_shuffled_graph_pca_ridge,0.28679153589146505,0.2682879416826972,0.01850359420876785
weak_diffusion_real_graph_residual_pca_ridge_minus_stage27c_module_pca_ridge_reference,weak_diffusion_real_graph_residual_pca_ridge,stage27c_module_pca_ridge_reference,0.3222800445479397,0.3267024400121495,-0.004422395464209805
hub_capped_real_graph_residual_pca_ridge_minus_stage27c_module_pca_ridge_reference,hub_capped_real_graph_residual_pca_ridge,stage27c_module_pca_ridge_reference,0.2632135263744052,0.3267024400121495,-0.06348891363774428
weak_diffusion_real_graph_residual_pca_ridge_minus_residual_no_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge,residual_no_graph_pca_ridge,0.3222800445479397,0.3267024400121495,-0.004422395464209805
weak_diffusion_real_graph_residual_pca_ridge_minus_residual_strict_shuffled_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge,residual_strict_shuffled_graph_pca_ridge,0.3222800445479397,0.2682879416826972,0.053992102865242475
hub_capped_real_graph_residual_pca_ridge_minus_residual_real_graph_pca_ridge,hub_capped_real_graph_residual_pca_ridge,residual_real_graph_pca_ridge,0.2632135263744052,0.26459046269110054,-0.001376936316695332
graph_residual_only_ridge_minus_stage27c_module_pca_ridge_reference,graph_residual_only_ridge,stage27c_module_pca_ridge_reference,0.24853700516351118,0.3267024400121495,-0.0781654348486383
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05_minus_stage27c_module_pca_ridge_reference,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,stage27c_module_pca_ridge_reference,0.32637035537106407,0.3267024400121495,-0.00033208464108541724
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05_minus_residual_no_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,residual_no_graph_pca_ridge,0.32637035537106407,0.3267024400121495,-0.00033208464108541724
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05_minus_residual_strict_shuffled_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,residual_strict_shuffled_graph_pca_ridge,0.32637035537106407,0.2682879416826972,0.05808241368836686
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2_minus_stage27c_module_pca_ridge_reference,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,stage27c_module_pca_ridge_reference,0.3160554824339374,0.3267024400121495,-0.010646957578212102
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2_minus_residual_no_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,residual_no_graph_pca_ridge,0.3160554824339374,0.3267024400121495,-0.010646957578212102
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2_minus_residual_strict_shuffled_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,residual_strict_shuffled_graph_pca_ridge,0.3160554824339374,0.2682879416826972,0.04776754075124018
```

## 15. Bootstrap confidence intervals

```csv
bootstrap_metric,condition,left_condition,right_condition,n_bootstrap_resamples,spearman_ci_low,spearman_ci_median,spearman_ci_high,uncertainty_status
condition_mean_pooled_oof_spearman,graph_residual_only_ridge,,,500,0.13674025358659667,0.24194074520816192,0.3395042021359332,complete
condition_mean_pooled_oof_spearman,hub_capped_real_graph_residual_pca_ridge,,,500,0.14825384071061667,0.2612998303903846,0.3728772896741773,complete
condition_mean_pooled_oof_spearman,residual_no_graph_pca_ridge,,,500,0.2098628437196263,0.3294312636902741,0.4279581362694477,complete
condition_mean_pooled_oof_spearman,residual_real_graph_pca_ridge,,,500,0.13626004544876563,0.26711304312998646,0.36813941451985943,complete
condition_mean_pooled_oof_spearman,residual_strict_shuffled_graph_pca_ridge,,,500,0.14515341086502095,0.26256862134944836,0.37920522891715663,complete
condition_mean_pooled_oof_spearman,stage27c_module_pca_ridge_reference,,,500,0.2189458104327562,0.3261216998997063,0.42184491463000645,complete
condition_mean_pooled_oof_spearman,target_gated_real_graph_residual_ridge,,,500,0.17565611999343123,0.2880777689745171,0.39223497010643577,complete
condition_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge,,,500,0.195777593522946,0.3180790130981909,0.41867037208095487,complete
condition_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,,,500,0.1961983617644829,0.3292904529238274,0.4242842999840456,complete
condition_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,,,500,0.2068908729593399,0.3122237338167575,0.42192303204650067,complete
pairwise_delta_mean_pooled_oof_spearman,residual_real_graph_pca_ridge_minus_stage27c_module_pca_ridge_reference,residual_real_graph_pca_ridge,stage27c_module_pca_ridge_reference,500,-0.1147187248402866,-0.061796526704039456,-0.010417333682484825,complete
pairwise_delta_mean_pooled_oof_spearman,residual_real_graph_pca_ridge_minus_residual_no_graph_pca_ridge,residual_real_graph_pca_ridge,residual_no_graph_pca_ridge,500,-0.11635981138788444,-0.061292854739857516,-0.012879926978173997,complete
pairwise_delta_mean_pooled_oof_spearman,residual_real_graph_pca_ridge_minus_residual_strict_shuffled_graph_pca_ridge,residual_real_graph_pca_ridge,residual_strict_shuffled_graph_pca_ridge,500,-0.03580791530211048,-0.0032454294711384557,0.027759743695733443,complete
pairwise_delta_mean_pooled_oof_spearman,target_gated_real_graph_residual_ridge_minus_stage27c_module_pca_ridge_reference,target_gated_real_graph_residual_ridge,stage27c_module_pca_ridge_reference,500,-0.07784721695924322,-0.04063569858120153,0.002322009295792679,complete
pairwise_delta_mean_pooled_oof_spearman,target_gated_real_graph_residual_ridge_minus_residual_no_graph_pca_ridge,target_gated_real_graph_residual_ridge,residual_no_graph_pca_ridge,500,-0.08416539445893807,-0.03921960680267286,0.0032149336111037563,complete
pairwise_delta_mean_pooled_oof_spearman,target_gated_real_graph_residual_ridge_minus_residual_strict_shuffled_graph_pca_ridge,target_gated_real_graph_residual_ridge,residual_strict_shuffled_graph_pca_ridge,500,-0.02045535781832855,0.018230251290966615,0.05670441984531247,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_minus_stage27c_module_pca_ridge_reference,weak_diffusion_real_graph_residual_pca_ridge,stage27c_module_pca_ridge_reference,500,-0.017224372260628857,-0.004232193162646891,0.004698861521149913,complete
pairwise_delta_mean_pooled_oof_spearman,hub_capped_real_graph_residual_pca_ridge_minus_stage27c_module_pca_ridge_reference,hub_capped_real_graph_residual_pca_ridge,stage27c_module_pca_ridge_reference,500,-0.11595917818070355,-0.06355429666140358,-0.007611394140553384,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_minus_residual_no_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge,residual_no_graph_pca_ridge,500,-0.015482928452321115,-0.0042343477325522405,0.0048443555930036564,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_minus_residual_strict_shuffled_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge,residual_strict_shuffled_graph_pca_ridge,500,0.007243964585961083,0.05235121657100138,0.1006905467108637,complete
pairwise_delta_mean_pooled_oof_spearman,hub_capped_real_graph_residual_pca_ridge_minus_residual_real_graph_pca_ridge,hub_capped_real_graph_residual_pca_ridge,residual_real_graph_pca_ridge,500,-0.010567918271625022,-0.0013961444716704408,0.004758316113609706,complete
pairwise_delta_mean_pooled_oof_spearman,graph_residual_only_ridge_minus_stage27c_module_pca_ridge_reference,graph_residual_only_ridge,stage27c_module_pca_ridge_reference,500,-0.13445299219713577,-0.0767879754594721,-0.010268932283797216,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05_minus_stage27c_module_pca_ridge_reference,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,stage27c_module_pca_ridge_reference,500,-0.0035932954655423072,-0.00029780179480573543,0.003155815018871998,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05_minus_residual_no_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,residual_no_graph_pca_ridge,500,-0.004003844985587963,-0.000423479096244489,0.003112306513260511,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05_minus_residual_strict_shuffled_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,residual_strict_shuffled_graph_pca_ridge,500,0.010823977945511612,0.056383141228052686,0.11072809287804206,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2_minus_stage27c_module_pca_ridge_reference,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,stage27c_module_pca_ridge_reference,500,-0.026880414532163836,-0.010322852461339072,0.004401517281417937,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2_minus_residual_no_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,residual_no_graph_pca_ridge,500,-0.026195820629437913,-0.010434285010217842,0.006598778903947158,complete
pairwise_delta_mean_pooled_oof_spearman,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2_minus_residual_strict_shuffled_graph_pca_ridge,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,residual_strict_shuffled_graph_pca_ridge,500,0.010234768423292382,0.047964767196032126,0.09316786149108996,complete
```

## 16. Pass/fail decision

```csv
best_stage31_condition,best_stage31_mean_pooled_oof_spearman,stage27c_reference_mean,official_threshold,best_minus_stage27c_reference,best_real_residual_minus_no_graph_residual,best_real_residual_minus_strict_shuffled_residual,primary_real_residual_mean,primary_real_minus_stage27c_reference,primary_real_minus_no_graph_residual,primary_real_minus_strict_shuffled_residual,full_stage31_pass,target_specific_partial_pass,partial_pass_condition,partial_pass_target,controlled_interpretation,duplicate_oof_rows,expected_rows_per_condition,best_real_meets_stage27c_reference,best_real_meets_official_threshold,best_real_beats_matched_no_graph_residual,best_real_beats_matched_strict_shuffled_residual,all_five_targets_reported,no_target_delta_vs_module_mean_below_minus_0_02,no_target_delta_vs_stage27c_below_minus_0_02,no_heldout_donor_leakage,no_clean_holdout_use,no_external_matrix_use,graph_audit_pass,feature_audit_pass,all_expected_conditions_present,required_pairwise_comparisons_present,oof_predictions_are_donor_level,locked_84_donors_retained,no_duplicate_condition_target_donor_rows,registry_has_no_model_selection_external_dataset
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,0.32637035537106407,0.3267024400121495,0.3228,-0.00033208464108541724,-0.00033208464108541724,0.05808241368836686,0.26459046269110054,-0.06211197732104895,-0.06211197732104895,-0.00369747899159667,False,True,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,GFAP,graph_like_residual_features_contain_structure_but_topology_specific_utility_not_established,0,420,False,True,False,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True
```

## 17. Interpretation boundary

This result does not prove graph topology is validated, Graph-JEPA improves the benchmark, causality, validated gene targets, druggability, spatial plaque proximity, experimental therapeutic efficacy, or in silico ablation validity.

If real residual graph beats strict-shuffled but not no-graph, the allowed claim is only that graph-like residual features contain some structure while topology-specific utility is not established. If no-graph remains best, the current best internal model remains Stage 27C module_pca_ridge / no-graph.

## 18. Recommended next stage

Keep Stage 27C as the internal reference and treat Stage 31 as an anti-oversmoothing diagnostic unless a later preregistered residual graph run passes all gates.

## Feature audit

```csv
condition,role,asset_key,graph_alpha,head,feature_mode,residual_weight_after_fold_scaling,n_stage27c_skip_features,n_graph_residual_features,base_module_overlap_summary,residual_module_overlap_summary,residual_feature_abs_mean,residual_feature_abs_max,anti_oversmoothing_design,hub_cap_percentile,hub_degree_threshold,n_hub_nodes,hub_neighbor_weight
residual_real_graph_pca_ridge,primary_real_residual,real,0.5,pca_ridge,base_plus_residual,1.0,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.11202708161664997,0.3811885206701957,Stage27C module features preserved as untouched skip path,,,,
residual_no_graph_pca_ridge,matched_no_graph_capacity_control,no_graph,0.5,pca_ridge,base_plus_residual,1.0,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.0,0.0,Stage27C module features preserved as untouched skip path,,,,
residual_strict_shuffled_graph_pca_ridge,matched_strict_shuffled_topology_control,strict,0.5,pca_ridge,base_plus_residual,1.0,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.12053816401447284,0.304200463613408,Stage27C module features preserved as untouched skip path,,,,
target_gated_real_graph_residual_ridge,target_specific_low_capacity_gate,real,0.5,ridge,base_plus_residual,1.0,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.11202708161664997,0.3811885206701957,Stage27C module features preserved as untouched skip path,,,,
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,diagnostic_weak_diffusion_anti_oversmoothing,real,0.05,pca_ridge,base_plus_residual,0.1,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.011202708161665,0.03811885206701957,Stage27C module features preserved as untouched skip path,,,,
weak_diffusion_real_graph_residual_pca_ridge,diagnostic_weak_diffusion_anti_oversmoothing,real,0.1,pca_ridge,base_plus_residual,0.2,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.022405416323329996,0.07623770413403914,Stage27C module features preserved as untouched skip path,,,,
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,diagnostic_weak_diffusion_anti_oversmoothing,real,0.2,pca_ridge,base_plus_residual,0.4,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.04481083264665999,0.1524754082680783,Stage27C module features preserved as untouched skip path,,,,
hub_capped_real_graph_residual_pca_ridge,diagnostic_hub_capped_anti_oversmoothing,hub_capped_98_0,0.5,pca_ridge,base_plus_residual,1.0,15,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.11215229428405253,0.38103903912089826,Stage27C module features preserved as untouched skip path,98.0,430.0,55.0,0.25
graph_residual_only_ridge,diagnostic_graph_residual_without_stage27c_skip,real,0.5,ridge,residual_only,1.0,0,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10,0.11202708161664997,0.3811885206701957,diagnostic residual-only branch; not full-pass eligible,,,,
```

## Graph audit

```csv
check_id,status,passed,details
canonical_node_count_2957,pass,True,nodes=2957
all_core_conditions_same_node_count,pass,True,"{'real': (2957, 2957), 'no_graph': (2957, 2957), 'strict': (2957, 2957), 'hub_capped_98_0': (2957, 2957)}"
no_graph_identity_edge_count,pass,True,edges=2957
real_graph_nonempty,pass,True,edges=114029
strict_graph_edge_count_matches_real,pass,True,real=114029; strict=114029
strict_degree_sequence_preserved,pass,True,True
strict_zero_overlap,pass,True,0.0
strict_no_self_loops,pass,True,True
strict_safe_for_training,pass,True,True
```

## Target deltas versus Stage 27C

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse,stage27c_reference_target_spearman,delta_vs_stage27c_reference
graph_residual_only_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.21553103168978432,0.21132920184834672,0.043411081426327325,0.6050425408201259,0.7168449087890836,0.3347372684013365,-0.11920623671155217
graph_residual_only_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.43071782930039487,0.5578230116910814,0.2996372147012115,0.38615708588960473,0.485428581449837,0.5284398096588033,-0.09772198035840846
graph_residual_only_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.27194492254733216,0.2528845443840608,0.06202480670915744,0.4974464182581248,0.6030515631688884,0.30229826870507237,-0.030353346157740213
graph_residual_only_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.10146805710235904,-0.16565287459957592,-0.1574065488794727,0.36869622780804284,0.4729362264925675,0.016077756403766325,-0.11754581350612536
graph_residual_only_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.42595929938240357,0.4253565223960719,0.16010381813984287,0.39991134118908855,0.5011362129343174,0.4519590968917688,-0.025999797509365208
hub_capped_real_graph_residual_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.17312949276095982,0.15777087546224003,0.004426444323594847,0.6239456316825761,0.7313061211280084,0.3347372684013365,-0.16160777564037668
hub_capped_real_graph_residual_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.39935202996861396,0.4963349494908283,0.24521008338792183,0.4151837505556509,0.5039377095456817,0.5284398096588033,-0.12908777969018936
hub_capped_real_graph_residual_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.28879214336336945,0.260754759347054,0.057134601548139985,0.4961059684103035,0.6046215471653446,0.30229826870507237,-0.013506125341702924
hub_capped_real_graph_residual_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.013587121595626205,-0.02558378146364474,-0.11432067391803202,0.3583554341782142,0.46404992646334337,0.016077756403766325,-0.0024906348081401193
hub_capped_real_graph_residual_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4412068441834565,0.4410381223104304,0.19425157481136135,0.3973985106234104,0.4908431289449161,0.4519590968917688,-0.01075225270831226
residual_no_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3347372684013365,0.31635203121758915,0.09975961956193147,0.5908527814398361,0.6954113538288077,0.3347372684013365,0.0
residual_no_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5284398096588033,0.662397495221605,0.42808995773853975,0.3514371020098167,0.4386596361996293,0.5284398096588033,0.0
residual_no_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.30229826870507237,0.27877065050185995,0.0775241338331295,0.4963336075201987,0.5980483240374915,0.30229826870507237,0.0
residual_no_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.016077756403766325,-0.04298590830888682,-0.09295916718496233,0.359161712235905,0.4595804887952489,0.016077756403766325,0.0
residual_no_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4519590968917688,0.4724359148185014,0.20964454842080227,0.38969685928713976,0.4861320000855131,0.4519590968917688,0.0
residual_real_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.1713880733016098,0.15491256410813434,0.0028490778371604852,0.6244162538277493,0.7318852251085113,0.3347372684013365,-0.1633491950997267
residual_real_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.41057001113698494,0.4778443856335364,0.22812570225382378,0.42330700425977125,0.5096090158301443,0.5284398096588033,-0.11786979852181839
residual_real_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2865849954439607,0.2607279294815919,0.05705462496797209,0.49594461774991805,0.6046471894989938,0.30229826870507237,-0.01571327326111166
residual_real_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.010570011136984915,-0.030514096475772527,-0.11764666216973496,0.35888025416749697,0.4647419510592897,0.016077756403766325,-0.005507745266781409
residual_real_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4438392224359624,0.443049159732378,0.19607213692224068,0.39721357176012745,0.4902882933927165,0.4519590968917688,-0.008119874455806364
residual_strict_shuffled_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.20346258985521923,0.18568494832674634,0.01876240597288381,0.6184873648095097,0.7260217339612733,0.3347372684013365,-0.13127467854611727
residual_strict_shuffled_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.42928014579325713,0.5011853382410798,0.25112518387053706,0.4150911958759573,0.5019592085424966,0.5284398096588033,-0.0991596638655462
residual_strict_shuffled_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.24169282170699602,0.23974428064496556,0.046998547839062654,0.5008389959944439,0.6078627806116242,0.30229826870507237,-0.06060544699807635
residual_strict_shuffled_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.021565252607066928,-0.011989632471924734,-0.10432699286068647,0.3586450339476053,0.46196434560024474,0.016077756403766325,0.0054874962033006035
residual_strict_shuffled_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4454388984509467,0.4480076862750935,0.20031646333661546,0.393362242533786,0.4889923453961966,0.4519590968917688,-0.006520198440822078
target_gated_real_graph_residual_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.2860990179204212,0.2855651010836046,0.07936340462986657,0.592736386864239,0.7032449940882274,0.3347372684013365,-0.0486382504809153
target_gated_real_graph_residual_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.47739192062367114,0.6063647517919768,0.35536791075515173,0.3743536595084052,0.4657145142191975,0.5284398096588033,-0.05104788903513219
target_gated_real_graph_residual_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.26795585704161184,0.27073899453189126,0.0661052191275896,0.49535675277463587,0.6017384255206246,0.30229826870507237,-0.034342411663460526
target_gated_real_graph_residual_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.03717728055077453,-0.08886138144165408,-0.17386869278582262,0.3631861838953712,0.4762877088798372,0.016077756403766325,-0.053255036954540855
target_gated_real_graph_residual_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4396881644223955,0.4370206553840968,0.18758004087326108,0.3948090363242203,0.49287101127938415,0.4519590968917688,-0.012270932469373275
weak_diffusion_real_graph_residual_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3274476055482434,0.31479812545243474,0.09888166528923725,0.5911582967144193,0.6957503691623362,0.3347372684013365,-0.007289662853093071
weak_diffusion_real_graph_residual_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5298774931659411,0.6598656510786651,0.4245765892891523,0.3527233490576645,0.44000496423558005,0.5284398096588033,0.0014376835071377991
weak_diffusion_real_graph_residual_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3034727143869596,0.2806342581135979,0.07854186380138717,0.49607557087910487,0.5977183318436673,0.30229826870507237,0.0011744456818872373
weak_diffusion_real_graph_residual_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.014275589753973878,-0.044718306007656125,-0.09555271192927228,0.35954321664284655,0.46012544798850175,0.016077756403766325,-0.0018021666497924464
weak_diffusion_real_graph_residual_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.43632681988458033,0.45982771608821954,0.1996970221043214,0.39162249702092095,0.48918169741625095,0.4519590968917688,-0.015632277007188444
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.33204414295838813,0.3160025635310978,0.09956542131218338,0.5909258480482622,0.6954863562328477,0.3347372684013365,-0.002693125442948363
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.528136073706591,0.6617975636541717,0.4272471074754681,0.3517552984063907,0.438982753685565,0.5284398096588033,-0.0003037359522123362
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3040194391009416,0.2792586796340216,0.07779071941605731,0.49626708748822457,0.5979619030333984,0.30229826870507237,0.0017211703958692204
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.01565252607066923,-0.04353202637769839,-0.09365891323555298,0.35927204577675187,0.4597275840322879,0.016077756403766325,-0.0004252303330970937
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.45199959501873044,0.4717509978896239,0.20883927819315506,0.389481857020983,0.4863795899279116,0.4519590968917688,4.049812696166333e-05
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3287840437379771,0.30674595436299057,0.09407276318652114,0.592576543011622,0.6976043673378666,0.3347372684013365,-0.005953224663359402
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5131922648577503,0.650165582435818,0.4119811479711333,0.35684106680431915,0.444794530088681,0.5284398096588033,-0.015247544801053059
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2909992912827782,0.25242160042589074,0.056365621166227675,0.5008731740592608,0.6048680549640725,0.30229826870507237,-0.011298977422294187
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.02452161587526577,-0.04189341307165459,-0.09929430230703362,0.35959969788726187,0.46091050082475216,0.016077756403766325,0.008443859471499445
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.42278019641591574,0.42919215363908053,0.1716262848478629,0.39459335873886126,0.49768681832344974,0.4519590968917688,-0.02917890047585303
```

## Target deltas versus module mean

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse,module_mean_target_spearman,delta_vs_module_mean_baseline
graph_residual_only_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.21553103168978432,0.21132920184834672,0.043411081426327325,0.6050425408201259,0.7168449087890836,0.3267793864533765,-0.11124835476359218
graph_residual_only_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.43071782930039487,0.5578230116910814,0.2996372147012115,0.38615708588960473,0.485428581449837,0.5417434443656981,-0.11102561506530323
graph_residual_only_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.27194492254733216,0.2528845443840608,0.06202480670915744,0.4974464182581248,0.6030515631688884,0.2607876885694037,0.011157233977928449
graph_residual_only_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.10146805710235904,-0.16565287459957592,-0.1574065488794727,0.36869622780804284,0.4729362264925675,0.0291181532854105,-0.13058621038776955
graph_residual_only_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.42595929938240357,0.4253565223960719,0.16010381813984287,0.39991134118908855,0.5011362129343174,0.405770983092032,0.020188316290371544
hub_capped_real_graph_residual_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.17312949276095982,0.15777087546224003,0.004426444323594847,0.6239456316825761,0.7313061211280084,0.3267793864533765,-0.1536498936924167
hub_capped_real_graph_residual_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.39935202996861396,0.4963349494908283,0.24521008338792183,0.4151837505556509,0.5039377095456817,0.5417434443656981,-0.14239141439708414
hub_capped_real_graph_residual_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.28879214336336945,0.260754759347054,0.057134601548139985,0.4961059684103035,0.6046215471653446,0.2607876885694037,0.02800445479396574
hub_capped_real_graph_residual_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.013587121595626205,-0.02558378146364474,-0.11432067391803202,0.3583554341782142,0.46404992646334337,0.0291181532854105,-0.015531031689784296
hub_capped_real_graph_residual_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4412068441834565,0.4410381223104304,0.19425157481136135,0.3973985106234104,0.4908431289449161,0.405770983092032,0.03543586109142449
residual_no_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3347372684013365,0.31635203121758915,0.09975961956193147,0.5908527814398361,0.6954113538288077,0.3267793864533765,0.007957881947959988
residual_no_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5284398096588033,0.662397495221605,0.42808995773853975,0.3514371020098167,0.4386596361996293,0.5417434443656981,-0.013303634706894774
residual_no_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.30229826870507237,0.27877065050185995,0.0775241338331295,0.4963336075201987,0.5980483240374915,0.2607876885694037,0.04151058013566866
residual_no_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.016077756403766325,-0.04298590830888682,-0.09295916718496233,0.359161712235905,0.4595804887952489,0.0291181532854105,-0.013040396881644177
residual_no_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4519590968917688,0.4724359148185014,0.20964454842080227,0.38969685928713976,0.4861320000855131,0.405770983092032,0.04618811379973675
residual_real_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.1713880733016098,0.15491256410813434,0.0028490778371604852,0.6244162538277493,0.7318852251085113,0.3267793864533765,-0.1553913131517667
residual_real_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.41057001113698494,0.4778443856335364,0.22812570225382378,0.42330700425977125,0.5096090158301443,0.5417434443656981,-0.13117343322871317
residual_real_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2865849954439607,0.2607279294815919,0.05705462496797209,0.49594461774991805,0.6046471894989938,0.2607876885694037,0.025797306874557002
residual_real_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.010570011136984915,-0.030514096475772527,-0.11764666216973496,0.35888025416749697,0.4647419510592897,0.0291181532854105,-0.018548142148425588
residual_real_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4438392224359624,0.443049159732378,0.19607213692224068,0.39721357176012745,0.4902882933927165,0.405770983092032,0.03806823934393039
residual_strict_shuffled_graph_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.20346258985521923,0.18568494832674634,0.01876240597288381,0.6184873648095097,0.7260217339612733,0.3267793864533765,-0.12331679659815728
residual_strict_shuffled_graph_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.42928014579325713,0.5011853382410798,0.25112518387053706,0.4150911958759573,0.5019592085424966,0.5417434443656981,-0.11246329857244097
residual_strict_shuffled_graph_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.24169282170699602,0.23974428064496556,0.046998547839062654,0.5008389959944439,0.6078627806116242,0.2607876885694037,-0.01909486686240769
residual_strict_shuffled_graph_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.021565252607066928,-0.011989632471924734,-0.10432699286068647,0.3586450339476053,0.46196434560024474,0.0291181532854105,-0.0075529006783435736
residual_strict_shuffled_graph_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4454388984509467,0.4480076862750935,0.20031646333661546,0.393362242533786,0.4889923453961966,0.405770983092032,0.039667915358914674
target_gated_real_graph_residual_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.2860990179204212,0.2855651010836046,0.07936340462986657,0.592736386864239,0.7032449940882274,0.3267793864533765,-0.04068036853295531
target_gated_real_graph_residual_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.47739192062367114,0.6063647517919768,0.35536791075515173,0.3743536595084052,0.4657145142191975,0.5417434443656981,-0.06435152374202696
target_gated_real_graph_residual_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.26795585704161184,0.27073899453189126,0.0661052191275896,0.49535675277463587,0.6017384255206246,0.2607876885694037,0.007168168472208136
target_gated_real_graph_residual_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,-0.03717728055077453,-0.08886138144165408,-0.17386869278582262,0.3631861838953712,0.4762877088798372,0.0291181532854105,-0.06629543383618502
target_gated_real_graph_residual_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.4396881644223955,0.4370206553840968,0.18758004087326108,0.3948090363242203,0.49287101127938415,0.405770983092032,0.03391718133036348
weak_diffusion_real_graph_residual_pca_ridge,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3274476055482434,0.31479812545243474,0.09888166528923725,0.5911582967144193,0.6957503691623362,0.3267793864533765,0.0006682190948669176
weak_diffusion_real_graph_residual_pca_ridge,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5298774931659411,0.6598656510786651,0.4245765892891523,0.3527233490576645,0.44000496423558005,0.5417434443656981,-0.011865951199756974
weak_diffusion_real_graph_residual_pca_ridge,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3034727143869596,0.2806342581135979,0.07854186380138717,0.49607557087910487,0.5977183318436673,0.2607876885694037,0.0426850258175559
weak_diffusion_real_graph_residual_pca_ridge,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.014275589753973878,-0.044718306007656125,-0.09555271192927228,0.35954321664284655,0.46012544798850175,0.0291181532854105,-0.014842563531436623
weak_diffusion_real_graph_residual_pca_ridge,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.43632681988458033,0.45982771608821954,0.1996970221043214,0.39162249702092095,0.48918169741625095,0.405770983092032,0.030555836792548308
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.33204414295838813,0.3160025635310978,0.09956542131218338,0.5909258480482622,0.6954863562328477,0.3267793864533765,0.005264756505011625
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.528136073706591,0.6617975636541717,0.4272471074754681,0.3517552984063907,0.438982753685565,0.5417434443656981,-0.01360737065910711
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3040194391009416,0.2792586796340216,0.07779071941605731,0.49626708748822457,0.5979619030333984,0.2607876885694037,0.04323175053153788
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.01565252607066923,-0.04353202637769839,-0.09365891323555298,0.35927204577675187,0.4597275840322879,0.0291181532854105,-0.01346562721474127
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.45199959501873044,0.4717509978896239,0.20883927819315506,0.389481857020983,0.4863795899279116,0.405770983092032,0.046228611926698415
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.3287840437379771,0.30674595436299057,0.09407276318652114,0.592576543011622,0.6976043673378666,0.3267793864533765,0.002004657284600586
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,AT8,AT8,percent AT8 positive area_Grey matter,84,0.5131922648577503,0.650165582435818,0.4119811479711333,0.35684106680431915,0.444794530088681,0.5417434443656981,-0.028551179507947833
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.2909992912827782,0.25242160042589074,0.056365621166227675,0.5008731740592608,0.6048680549640725,0.2607876885694037,0.030211602713374475
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.02452161587526577,-0.04189341307165459,-0.09929430230703362,0.35959969788726187,0.46091050082475216,0.0291181532854105,-0.004596537410144732
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_2,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.42278019641591574,0.42919215363908053,0.1716262848478629,0.39459335873886126,0.49768681832344974,0.405770983092032,0.01700921332388372
```

## Best-condition target summary

```csv
condition,target,target_key,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,6e10/Aβ,6e10/A_beta,percent 6e10 positive area_Grey matter,84,0.33204414295838813,0.3160025635310978,0.09956542131218338,0.5909258480482622,0.6954863562328477
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,AT8,AT8,percent AT8 positive area_Grey matter,84,0.528136073706591,0.6617975636541717,0.4272471074754681,0.3517552984063907,0.438982753685565
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,GFAP,GFAP,percent GFAP positive area_Grey matter,84,0.3040194391009416,0.2792586796340216,0.07779071941605731,0.49626708748822457,0.5979619030333984
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,Iba1,Iba1,percent Iba1 positive area_Grey matter,84,0.01565252607066923,-0.04353202637769839,-0.09365891323555298,0.35927204577675187,0.4597275840322879
weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,NeuN,NeuN,percent NeuN positive area_Grey matter,84,0.45199959501873044,0.4717509978896239,0.20883927819315506,0.389481857020983,0.4863795899279116
```
