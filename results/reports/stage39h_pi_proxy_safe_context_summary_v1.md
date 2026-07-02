# Stage 39H PI proxy-safe context summary

## Short answer

Best proxy-safe/caution candidate: `latent_plus_tier1_plus_tier2`. New benchmark lock eligible candidates: `0`.

## Mean results

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

## Safe interpretation

Stage 39H decomposes the Stage 39D context jump. It is an internal proxy-safety audit only and does not establish external validation, causality, therapeutic relevance, disease modification, or gene-ablation support.
