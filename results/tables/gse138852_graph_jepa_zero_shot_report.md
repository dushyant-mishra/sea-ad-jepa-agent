# GSE138852_Grubman_Leng Frozen Graph-JEPA Zero-Shot Projection

This smoke test projects external microglia/immune nuclei through the SEA-AD-trained Graph-JEPA encoder with all weights frozen.

## Strict Freeze

- checkpoint: `results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt`
- embedding space: `projector`
- all model parameters set to `requires_grad=False`

## Feature Alignment

- projected cells: `449`
- external groups: `6`
- matched genes: `2626 / 2957`
- gene overlap fraction: `0.888`

## Summary

| dataset | embedding_space | variable | disease_label | control_label | n_disease | n_control | disease_mean | control_mean | mean_difference_disease_minus_control | rank_biserial_effect | mannwhitney_p | auc_ad_vs_control | category | n_cells_before_filter | n_cells_after_filter | n_external_groups | n_jepa_genes | n_matched_genes | gene_overlap_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GSE138852_Grubman_Leng | projector | z_103 | AD | Control | 3 | 3 | 0.1478 | 0.1429 | 0.004887 | 0.3333 | 0.7 | 0.6667 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_71 | AD | Control | 3 | 3 | 0.1962 | 0.1701 | 0.02609 | 0.3333 | 0.7 | 0.6667 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_63 | AD | Control | 3 | 3 | 0.2192 | 0.2146 | 0.004668 | 0.1111 | 1 | 0.5556 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_30 | AD | Control | 3 | 3 | 0.07037 | 0.07232 | -0.001953 | -0.1111 | 1 | 0.4444 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_1 | AD | Control | 3 | 3 | 0.4059 | 0.4096 | -0.003708 | -0.3333 | 0.7 | 0.3333 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_120 | AD | Control | 3 | 3 | 0.174 | 0.1761 | -0.002046 | -0.3333 | 0.7 | 0.3333 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_26 | AD | Control | 3 | 3 | -0.5397 | -0.495 | -0.04468 | -0.3333 | 0.7 | 0.3333 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_57 | AD | Control | 3 | 3 | -0.2226 | -0.203 | -0.01963 | -0.3333 | 0.7 | 0.3333 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | z_94 | AD | Control | 3 | 3 | 0.09657 | 0.1444 | -0.04781 | -0.5556 | 0.4 | 0.2222 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_at8_associated_first_pass | AD | Control | 3 | 3 | 0.1101 | 0.04577 | 0.06433 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_complement | AD | Control | 3 | 3 | 0.5783 | 0.3967 | 0.1815 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_disease_associated_microglia | AD | Control | 3 | 3 | 0.506 | 0.3781 | 0.1279 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_plaque_response | AD | Control | 3 | 3 | 0.5326 | 0.3951 | 0.1375 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_vascular_barrier_myeloid | AD | Control | 3 | 3 | 0.5286 | 0.3858 | 0.1428 | 0.7778 | 0.2 | 0.8889 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_lysosome_phagocytosis | AD | Control | 3 | 3 | 0.3816 | 0.3084 | 0.07322 | 0.5556 | 0.4 | 0.7778 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_interferon_response | AD | Control | 3 | 3 | 0.0753 | 0.05425 | 0.02105 | 0.3333 | 0.7 | 0.6667 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_oxidative_stress | AD | Control | 3 | 3 | 0.204 | 0.1703 | 0.0337 | 0.3333 | 0.7 | 0.6667 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_synapse_pruning | AD | Control | 3 | 3 | 0.5009 | 0.4726 | 0.02827 | 0.3333 | 0.7 | 0.6667 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_senescence_stress | AD | Control | 3 | 3 | 0.3925 | 0.3167 | 0.07589 | -0.1111 | 1 | 0.4444 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_antigen_presentation | AD | Control | 3 | 3 | 0.6461 | 0.8123 | -0.1661 | -0.3333 | 0.7 | 0.3333 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_inflammatory_signaling | AD | Control | 3 | 3 | 0.07268 | 0.1193 | -0.04663 | -0.5556 | 0.4 | 0.2222 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_lipid_metabolism | AD | Control | 3 | 3 | 0.559 | 0.6563 | -0.09735 | -0.7778 | 0.2 | 0.1111 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_chemokine_migration | AD | Control | 3 | 3 | 0.02245 | 0.142 | -0.1196 | -1 | 0.1 | 0 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | module_homeostatic_microglia | AD | Control | 3 | 3 | 0.2438 | 0.4758 | -0.2321 | -1 | 0.1 | 0 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | predicted_NeuN_model_scale | AD | Control | 3 | 3 | 33.36 | 31.49 | 1.865 | 0.3333 | 0.7 | 0.6667 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | predicted_A beta/6e10_model_scale | AD | Control | 3 | 3 | -18.54 | -15.33 | -3.211 | -0.3333 | 0.7 | 0.3333 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | predicted_AT8/pTau_model_scale | AD | Control | 3 | 3 | -15.33 | -13.47 | -1.854 | -0.3333 | 0.7 | 0.3333 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | predicted_GFAP_model_scale | AD | Control | 3 | 3 | -27.92 | -27.43 | -0.4891 | -0.3333 | 0.7 | 0.3333 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |
| GSE138852_Grubman_Leng | projector | predicted_Iba1_model_scale | AD | Control | 3 | 3 | -9.606 | -8.873 | -0.7332 | -0.3333 | 0.7 | 0.3333 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 |

## Interpretation Boundary

This is independent observational-cohort projection, not perturbational causal proof. The GSE138852 labels support an AD/control smoke test, not continuous SEA-AD-style AT8/6e10/GFAP regression validation. SEA-AD-calibrated pathology heads should be interpreted on model scale for ranking/separation; raw-scale values may be out of distribution in small external cohorts.
