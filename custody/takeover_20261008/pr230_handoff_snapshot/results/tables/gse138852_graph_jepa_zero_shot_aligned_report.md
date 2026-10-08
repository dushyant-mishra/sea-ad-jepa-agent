# GSE138852_Grubman_Leng Frozen Graph-JEPA Zero-Shot Projection

This smoke test projects external microglia/immune nuclei through the SEA-AD-trained Graph-JEPA encoder with all weights frozen.

## Strict Freeze

- checkpoint: `results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt`
- embedding space: `projector`
- all model parameters set to `requires_grad=False`
- missing gene imputation: `sea_ad_low_pathology_mean`
- alignment: `control_centroid_shift`

## Feature Alignment

- projected cells: `449`
- external groups: `6`
- matched genes: `2626 / 2957`
- gene overlap fraction: `0.888`
- control-centroid shift applied: `True`
- control-centroid shift L2: `3.8727`

## Summary

| dataset | embedding_space | variable | disease_label | control_label | n_disease | n_control | disease_mean | control_mean | mean_difference_disease_minus_control | rank_biserial_effect | mannwhitney_p | auc_ad_vs_control | category | n_cells_before_filter | n_cells_after_filter | n_external_groups | n_jepa_genes | n_matched_genes | gene_overlap_fraction | control_centroid_shift_applied | control_centroid_shift_l2 | missing_gene_imputation | alignment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GSE138852_Grubman_Leng | projector | z_94 | AD | Control | 3 | 3 | 0.3307 | 0.3179 | 0.01279 | 0.5556 | 0.4 | 0.7778 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_1 | AD | Control | 3 | 3 | 0.0131 | -0.04229 | 0.05539 | 0.3333 | 0.7 | 0.6667 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_120 | AD | Control | 3 | 3 | -0.1676 | -0.2068 | 0.03926 | 0.3333 | 0.7 | 0.6667 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_26 | AD | Control | 3 | 3 | -0.01799 | -0.03073 | 0.01274 | 0.3333 | 0.7 | 0.6667 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_63 | AD | Control | 3 | 3 | -0.1572 | -0.1876 | 0.03038 | 0.3333 | 0.7 | 0.6667 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_57 | AD | Control | 3 | 3 | 0.09822 | 0.109 | -0.01082 | -0.1111 | 1 | 0.4444 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_103 | AD | Control | 3 | 3 | 0.3867 | 0.4206 | -0.03398 | -0.3333 | 0.7 | 0.3333 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_71 | AD | Control | 3 | 3 | 0.2967 | 0.3165 | -0.01977 | -0.3333 | 0.7 | 0.3333 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | z_30 | AD | Control | 3 | 3 | 0.4798 | 0.5137 | -0.03386 | -0.5556 | 0.4 | 0.2222 | latent_axis | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_at8_associated_first_pass | AD | Control | 3 | 3 | 0.4913 | 0.4123 | 0.07897 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_complement | AD | Control | 3 | 3 | 0.5783 | 0.3967 | 0.1815 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_disease_associated_microglia | AD | Control | 3 | 3 | 0.7772 | 0.6408 | 0.1365 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_plaque_response | AD | Control | 3 | 3 | 0.8264 | 0.6797 | 0.1468 | 1 | 0.1 | 1 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_interferon_response | AD | Control | 3 | 3 | 0.3637 | 0.3317 | 0.03197 | 0.5556 | 0.4 | 0.7778 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_lysosome_phagocytosis | AD | Control | 3 | 3 | 0.932 | 0.8436 | 0.08841 | 0.5556 | 0.4 | 0.7778 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_oxidative_stress | AD | Control | 3 | 3 | 0.4061 | 0.3658 | 0.04024 | 0.5556 | 0.4 | 0.7778 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_vascular_barrier_myeloid | AD | Control | 3 | 3 | 0.7819 | 0.6322 | 0.1497 | 0.5556 | 0.4 | 0.7778 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_synapse_pruning | AD | Control | 3 | 3 | 1.277 | 1.228 | 0.04927 | 0.3333 | 0.7 | 0.6667 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_senescence_stress | AD | Control | 3 | 3 | 0.3925 | 0.3167 | 0.07589 | -0.1111 | 1 | 0.4444 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_antigen_presentation | AD | Control | 3 | 3 | 0.7596 | 0.9214 | -0.1619 | -0.3333 | 0.7 | 0.3333 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_lipid_metabolism | AD | Control | 3 | 3 | 0.7369 | 0.8288 | -0.09186 | -0.5556 | 0.4 | 0.2222 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_inflammatory_signaling | AD | Control | 3 | 3 | 0.2928 | 0.3281 | -0.03524 | -0.7778 | 0.2 | 0.1111 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_chemokine_migration | AD | Control | 3 | 3 | 0.5239 | 0.6273 | -0.1033 | -1 | 0.1 | 0 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | module_homeostatic_microglia | AD | Control | 3 | 3 | 0.645 | 0.8636 | -0.2185 | -1 | 0.1 | 0 | module_score | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | predicted_A beta/6e10_model_scale | AD | Control | 3 | 3 | 2.594 | 0.8626 | 1.732 | 0.5556 | 0.4 | 0.7778 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | predicted_NeuN_model_scale | AD | Control | 3 | 3 | 3.054 | 1.29 | 1.764 | 0.3333 | 0.7 | 0.6667 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | predicted_AT8/pTau_model_scale | AD | Control | 3 | 3 | 0.7229 | 0.4824 | 0.2405 | 0.1111 | 1 | 0.5556 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | predicted_Iba1_model_scale | AD | Control | 3 | 3 | 1.32 | 1.45 | -0.1299 | 0.1111 | 1 | 0.5556 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | predicted_GFAP_model_scale | AD | Control | 3 | 3 | -1.644 | 1.735 | -3.379 | -0.3333 | 0.7 | 0.3333 | sea_ad_calibrated_pathology_prediction | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |
| GSE138852_Grubman_Leng | projector | trajectory_A beta/6e10_score | AD | Control | 3 | 3 | 0.4523 | 0.2862 | 0.1661 | 0.3333 | 0.7 | 0.6667 | sea_ad_disease_trajectory | 13214 | 449 | 6 | 2957 | 2626 | 0.8881 | True | 3.873 | sea_ad_low_pathology_mean | control_centroid_shift |

## Interpretation Boundary

This is independent observational-cohort projection, not perturbational causal proof. The GSE138852 labels support an AD/control smoke test, not continuous SEA-AD-style AT8/6e10/GFAP regression validation. SEA-AD-calibrated pathology heads should be interpreted on model scale for ranking/separation; raw-scale values may be out of distribution in small external cohorts. Trajectory scores and module scores are the primary readouts for cross-cohort geometry.
