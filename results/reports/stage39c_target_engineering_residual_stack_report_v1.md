# Stage 39C target engineering residual-stack report

Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation.

## Why this stage was run

Stage 39B-LPH did not beat Stage 27C and failed the shuffled-target control. Stage 39C therefore tests the report's highest-priority recommendation: target engineering plus target-specific simple models under strict donor-held-out safeguards.

## Training gate

| training_allowed | training_gate_reason | n_donors | missing_targets | covariate_leakage_pass |
| --- | --- | --- | --- | --- |
| True | ok | 84 |  | True |

## Target-transform design

| target_transform | train_fold_only | description |
| --- | --- | --- |
| raw_log1p | True | log1p target modeling |
| winsor_log1p | True | train-fold 5/95 winsorized log1p target |
| rank_inverse_normal | True | train-fold rank inverse-normal target |
| covariate_residual_log1p | True | train-fold safe-covariate residualized log1p target |

## Model registry

| condition | target_transform | feature_mode | model | control |
| --- | --- | --- | --- | --- |
| raw_log1p_module_pca_ridge | raw_log1p | module_pca | ridge | False |
| winsor_log1p_module_pca_ridge | winsor_log1p | module_pca | ridge | False |
| rank_int_module_pca_ridge | rank_inverse_normal | module_pca | ridge | False |
| covariate_residual_log1p_module_pca_ridge | covariate_residual_log1p | module_pca | ridge | False |
| raw_log1p_module_pca_elasticnet | raw_log1p | module_pca | elasticnet | False |
| raw_log1p_module_pca_huber | raw_log1p | module_pca | huber | False |
| raw_log1p_metadata_only_ridge | raw_log1p | metadata_only | ridge | True |
| raw_log1p_module_pca_ridge_donor_shuffled_control | raw_log1p | module_pca | ridge | True |

## Mean metrics

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- |
| rank_int_module_pca_ridge | 0.3458094563126456 | 0.025473321858864025 | 5 |
| raw_log1p_module_pca_huber | 0.33112078566366304 | -0.02824744355573555 | 5 |
| covariate_residual_log1p_module_pca_ridge | 0.3215834767641997 | -0.11313151766730789 | 5 |
| raw_log1p_module_pca_elasticnet | 0.29264212616953955 | -0.08973054562289069 | 5 |
| raw_log1p_module_pca_ridge | 0.2920522425837805 | -0.09755998785056191 | 5 |
| winsor_log1p_module_pca_ridge | 0.28896628530930446 | -0.09745874253315785 | 5 |
| raw_log1p_metadata_only_ridge | 0.1414032600992204 | -0.18086463501063077 | 5 |
| raw_log1p_module_pca_ridge_donor_shuffled_control | -0.1687637946744963 | -0.26712564543889844 | 5 |

## Target metrics

| condition | target | n_donors | pooled_oof_spearman | mse | prediction_variance |
| --- | --- | --- | --- | --- | --- |
| covariate_residual_log1p_module_pca_ridge | 6e10/A_beta | 84 | 0.5424116634605649 | 0.38079692409709903 | 0.16025909478849967 |
| covariate_residual_log1p_module_pca_ridge | AT8 | 84 | 0.5534271539941278 | 0.2130825802616012 | 0.18522759080202042 |
| covariate_residual_log1p_module_pca_ridge | GFAP | 84 | 0.1675002531132935 | 0.3981883750092071 | 0.030649623223393655 |
| covariate_residual_log1p_module_pca_ridge | Iba1 | 84 | -0.11313151766730789 | 0.21411790752342533 | 0.006645590419677251 |
| covariate_residual_log1p_module_pca_ridge | NeuN | 84 | 0.45770983092032 | 0.23964402669044235 | 0.09986378542021677 |
| rank_int_module_pca_ridge | 6e10/A_beta | 84 | 0.4001619925078465 | 1.3450791882953692 | 0.06141440416110783 |
| rank_int_module_pca_ridge | AT8 | 84 | 0.5254834463906044 | 0.5725139813852932 | 0.3541012583546435 |
| rank_int_module_pca_ridge | GFAP | 84 | 0.3122608079376329 | 3.605536437235707 | 0.06205252273939958 |
| rank_int_module_pca_ridge | Iba1 | 84 | 0.025473321858864025 | 2.4380960327601033 | 0.013426922850304118 |
| rank_int_module_pca_ridge | NeuN | 84 | 0.46566771286827985 | 1.8357926008866228 | 0.35088751377278554 |
| raw_log1p_metadata_only_ridge | 6e10/A_beta | 84 | 0.4815227295737572 | 0.41488827242840043 | 0.12263483298646059 |
| raw_log1p_metadata_only_ridge | AT8 | 84 | 0.3971246329857245 | 0.27896434574485524 | 0.08517672100569668 |
| raw_log1p_metadata_only_ridge | GFAP | 84 | 0.010043535486483752 | 0.4034217496342026 | 0.020401650472565355 |
| raw_log1p_metadata_only_ridge | Iba1 | 84 | -0.18086463501063077 | 0.20726127815530282 | 0.003443509460941642 |
| raw_log1p_metadata_only_ridge | NeuN | 84 | -0.0008099625392325605 | 0.3071522036971997 | 0.006003725701373833 |
| raw_log1p_module_pca_elasticnet | 6e10/A_beta | 84 | 0.35004556039283186 | 0.476693810519091 | 0.059028765039699164 |
| raw_log1p_module_pca_elasticnet | AT8 | 84 | 0.5327123620532551 | 0.18596888237566192 | 0.1625381934898262 |
| raw_log1p_module_pca_elasticnet | GFAP | 84 | 0.25503695454085246 | 0.37431068142534263 | 0.023522966721532198 |
| raw_log1p_module_pca_elasticnet | Iba1 | 84 | -0.08973054562289069 | 0.2120256770380733 | 0.007370485147820811 |
| raw_log1p_module_pca_elasticnet | NeuN | 84 | 0.4151462994836489 | 0.24881667214527078 | 0.08703437891853814 |
| raw_log1p_module_pca_huber | 6e10/A_beta | 84 | 0.37576187101346564 | 0.48635787295371624 | 0.13352159297474483 |
| raw_log1p_module_pca_huber | AT8 | 84 | 0.5546420978029767 | 0.198917043782555 | 0.23116803925346183 |
| raw_log1p_module_pca_huber | GFAP | 84 | 0.28152272957375724 | 0.3921860291015008 | 0.10219358550116246 |
| raw_log1p_module_pca_huber | Iba1 | 84 | -0.02824744355573555 | 0.2605097765188591 | 0.04847761672785781 |
| raw_log1p_module_pca_huber | NeuN | 84 | 0.47192467348385136 | 0.25180325012155425 | 0.14440243746881093 |
| raw_log1p_module_pca_ridge | 6e10/A_beta | 84 | 0.35271843677229936 | 0.4811698646789741 | 0.03399577327195229 |
| raw_log1p_module_pca_ridge | AT8 | 84 | 0.5359724612736662 | 0.18482462786497247 | 0.16192959656897019 |
| raw_log1p_module_pca_ridge | GFAP | 84 | 0.21368836691303028 | 0.3824793124962007 | 0.024986304546837174 |
| raw_log1p_module_pca_ridge | Iba1 | 84 | -0.09755998785056191 | 0.2068895876871521 | 0.0035810587252303435 |
| raw_log1p_module_pca_ridge | NeuN | 84 | 0.45544193581046877 | 0.23803824730763162 | 0.0991782869990472 |
| raw_log1p_module_pca_ridge_donor_shuffled_control | 6e10/A_beta | 84 | -0.005689986838108739 | 0.5360293401211449 | 0.003641946256394365 |
| raw_log1p_module_pca_ridge_donor_shuffled_control | AT8 | 84 | -0.26712564543889844 | 0.3632347029748732 | 0.0036636787039160982 |
| raw_log1p_module_pca_ridge_donor_shuffled_control | GFAP | 84 | -0.1918801255441936 | 0.408264999600329 | 0.00533189800680494 |
| raw_log1p_module_pca_ridge_donor_shuffled_control | Iba1 | 84 | -0.19107016300496102 | 0.2012978605830548 | 0.0009237769805885901 |
| raw_log1p_module_pca_ridge_donor_shuffled_control | NeuN | 84 | -0.18805305254631974 | 0.3041709302791176 | 0.002328772139498732 |
| winsor_log1p_module_pca_ridge | 6e10/A_beta | 84 | 0.3605750734028551 | 0.48148513104775603 | 0.03154709079105763 |
| winsor_log1p_module_pca_ridge | AT8 | 84 | 0.5277715905639364 | 0.1899893503555724 | 0.14284616864702823 |
| winsor_log1p_module_pca_ridge | GFAP | 84 | 0.2164827376733826 | 0.3817676649714623 | 0.023728757243200376 |
| winsor_log1p_module_pca_ridge | Iba1 | 84 | -0.09745874253315785 | 0.20656789086836533 | 0.0031973948054869828 |
| winsor_log1p_module_pca_ridge | NeuN | 84 | 0.4374607674395059 | 0.23611509432926667 | 0.08831839535173233 |

## Control results

| comparison | best_condition | control_condition | delta | passes |
| --- | --- | --- | --- | --- |
| rank_int_module_pca_ridge_vs_raw_log1p_module_pca_ridge_donor_shuffled_control | rank_int_module_pca_ridge | raw_log1p_module_pca_ridge_donor_shuffled_control | 0.5145732509871419 | True |
| rank_int_module_pca_ridge_vs_raw_log1p_metadata_only_ridge | rank_int_module_pca_ridge | raw_log1p_metadata_only_ridge | 0.20440619621342518 | True |

## Bootstrap CI and Stage 27C delta

| condition | n_bootstrap | bootstrap_mean | ci_lower_95 | ci_upper_95 |
| --- | --- | --- | --- | --- |
| rank_int_module_pca_ridge | 500 | 0.33886499638236506 | 0.2384706378799647 | 0.4378608499288575 |

| best_condition | stage27c_reference_mean | best_mean_pooled_oof_spearman | delta_vs_stage27c | rescue_threshold | bootstrap_ci_lower_95 | bootstrap_ci_upper_95 | controls_pass | leakage_audit_pass | stage39c_internal_rescue_pass | recommended_next_step | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank_int_module_pca_ridge | 0.3267024400121495 | 0.3458094563126456 | 0.019107016300496105 | 0.3317024400121495 | 0.2384706378799647 | 0.4378608499288575 | True | True | False | do not replace Stage 27C; proceed to metadata/composition Stage 39D or refine target engineering | internal target-engineering benchmark; donor-held-out model comparison; hypothesis prioritization only | clean external validation; causal regulator; therapeutic target; disease-modifying target; gene-ablation result |

## Leakage and claim audits

| covariate_column | forbidden_term_hits | leakage_risk | allowed_for_stage39c | audit_type | audit_item | pass | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Age at Death |  | False | True | covariate |  |  |  |
| PMI |  | False | True | covariate |  |  |  |
| RIN |  | False | True | covariate |  |  |  |
| Years of education |  | False | True | covariate |  |  |  |
| Sex |  | False | True | covariate |  |  |  |
| APOE Genotype |  | False | True | covariate |  |  |  |
| Primary Study Name |  | False | True | covariate |  |  |  |
|  |  |  |  | oof | no_duplicate_condition_target_donor_rows | True | duplicate_rows=0 |
|  |  |  |  | oof | heldout_donor_leakage_not_detected | True | heldout_donor_leakage_detected=False |
|  |  |  |  | oof | clean_holdout_not_used | True | clean_holdout_used=False |

| audit_item | pass | evidence |
| --- | --- | --- |
| train_fold_only_preprocessing | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| donor_heldout_only | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_external_data | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_candidate_selection | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_clean_external_validation_claim | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_causal_claim | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_therapeutic_claim | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_gene_ablation_claim | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| negative_null_results_reported | True | Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| safety_audit_pass | True | all safety checks passed |
