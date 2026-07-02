# Stage 39D PI metadata/composition summary

## Short answer

Best condition: `rank_int_latent_composition_ridge`. Mean pooled OOF Spearman: `0.5048658499544396`. Delta versus Stage 39C: `0.15905639364179402`. Delta versus Stage 27C: `0.17816340994229013`. Stage 39D context enrichment pass: `False`.

| best_condition | stage27c_reference_mean | stage39c_best_mean | best_mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39c | bootstrap_ci_lower_95 | bootstrap_ci_upper_95 | n_targets_improved_vs_stage39c | block_ablation_pass | leakage_audit_pass | n_high_pathology_proxy_features | n_moderate_cell_state_proxy_features | no_pseudo_no_seaad_mean_pooled_oof_spearman | broad_subclass_count_only_mean_pooled_oof_spearman | composition_proxy_sensitivity_pass | stage39d_context_enrichment_pass | recommended_next_step | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank_int_latent_composition_ridge | 0.3267024400121495 | 0.3458094563126456 | 0.5048658499544396 | 0.17816340994229013 | 0.15905639364179402 | 0.4243225718919451 | 0.5696572943742619 | 5 | True | True | 13 | 8 | 0.31541966184063985 | 0.34010732003644834 | False | False | do not replace Stage 39C yet; inspect composition proxy sensitivity before treating Stage 39D as a benchmark | internal metadata/composition enrichment benchmark; donor-held-out model comparison; hypothesis prioritization only | clean external validation; causal regulator; therapeutic target; disease-modifying target; gene-ablation result |

## Top conditions

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- |
| rank_int_latent_composition_ridge | 0.5048658499544396 | 0.13704566163814924 | 5 |
| rank_int_latent_metadata_composition_interactions_ridge | 0.5008970335122 | 0.15126050420168066 | 5 |
| rank_int_latent_metadata_composition_ridge | 0.498382099827883 | 0.17146906955553307 | 5 |
| rank_int_composition_only_ridge | 0.4915379163713679 | 0.23203401842664775 | 5 |
| rank_int_metadata_composition_ridge | 0.4906996051432621 | 0.23557760453579024 | 5 |
| rank_int_latent_metadata_ridge | 0.37668522830819073 | 0.013688366913030272 | 5 |
| stage39c_rank_int_latent_only_reproduction | 0.3458094563126456 | 0.025473321858864025 | 5 |
| rank_int_metadata_only_ridge | 0.24245418649387468 | 0.009800546724713984 | 5 |

## Interpretation

Stage 39D tests whether explicit safe metadata and microglia/PVM composition features add internal predictive signal beyond the Stage 39C rank-transformed latent baseline. Because fine cell-state and pseudo-progression summaries can act as pathology proxies, the restricted sensitivity table should be treated as the primary safeguard before promoting Stage 39D over Stage 39C. It is not external validation and does not support causal, therapeutic, disease-modifying, or gene-ablation claims.

## Proxy sensitivity

| sensitivity_mode | condition | n_composition_features | mean_pooled_oof_spearman | delta_vs_full_best | delta_vs_stage39c | proxy_sensitivity_interpretation | 6e10/A_beta_spearman | AT8_spearman | GFAP_spearman | Iba1_spearman | NeuN_spearman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_composition | sensitivity_full_composition_latent_composition_ridge | 33 | 0.5048658499544396 | 0.0 | 0.15905639364179402 | full context benchmark; includes audited proxy-risk features | 0.7684114609699302 | 0.7183152779183962 | 0.35885390300698594 | 0.13704566163814924 | 0.5417029462387365 |
| no_pseudoprogression | sensitivity_no_pseudoprogression_latent_composition_ridge | 28 | 0.296766224562114 | -0.20809962539232563 | -0.0490432317505316 | does_not_survive_restricted_proxy_removal | 0.26390604434544906 | 0.48198845803381596 | 0.2563328946036246 | 0.11436671053963755 | 0.3672370152880429 |
| no_seaad_supertypes | sensitivity_no_seaad_supertypes_latent_composition_ridge | 25 | 0.5231183557760454 | 0.018252505821605758 | 0.17730889946339978 | survives restricted proxy removal versus Stage39C | 0.7760858560291587 | 0.6968512706287334 | 0.37958894401133947 | 0.18467145894502382 | 0.5783942492659715 |
| no_pseudo_no_seaad | sensitivity_no_pseudo_no_seaad_latent_composition_ridge | 20 | 0.31541966184063985 | -0.18944618811379976 | -0.030389794472005738 | does_not_survive_restricted_proxy_removal | 0.2755492558469171 | 0.44797003138604846 | 0.2499544396071682 | 0.16701427558975396 | 0.43661030677331175 |
| broad_subclass_count_only | sensitivity_broad_subclass_count_only_latent_composition_ridge | 6 | 0.34010732003644834 | -0.16475852991799128 | -0.005702136276197256 | does_not_survive_restricted_proxy_removal | 0.3193074820289562 | 0.5080895008605852 | 0.356019034119672 | 0.04837501265566467 | 0.4687455705173636 |
