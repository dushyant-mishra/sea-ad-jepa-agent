# Stage 45 new safe feature acquisition and benchmark

CELLxGENE metadata files were consumed from local untracked `data/sea_ad/stage45/cellxgene/`. Donor-linked composition and engineered MRI features were built where possible. No raw data were committed.

## Lock decision

| candidate_id | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage41c | bootstrap_lower_95 | benchmark_lock_eligible | locked_benchmark_after_stage45 | decision | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| latent_plus_safe_metadata_plus_cellxgene_plus_mri_engineered | 0.3121433633694442 | -0.014559076642705282 | -0.05594411258479293 | 0.21464445278049232 | False | Stage27C | do_not_lock_stage45 | one or more strict lock guards failed |

## Feature matrices

| feature_matrix_id | local_path | n_donors | n_features | risk_tier | training_allowed | committed_to_git |
| --- | --- | --- | --- | --- | --- | --- |
| cellxgene_composition_only | data\sea_ad\stage45\processed\stage45_cellxgene_composition_only_feature_matrix_v1.csv | 84 | 24 | Tier2 | True | False |
| latent_plus_cellxgene_composition | data\sea_ad\stage45\processed\stage45_latent_plus_cellxgene_composition_feature_matrix_v1.csv | 84 | 39 | Tier2 | True | False |
| latent_plus_safe_metadata_plus_cellxgene_composition | data\sea_ad\stage45\processed\stage45_latent_plus_safe_metadata_plus_cellxgene_composition_feature_matrix_v1.csv | 84 | 56 | Tier2 | True | False |
| mri_engineered_only | data\sea_ad\stage45\processed\stage45_mri_engineered_only_feature_matrix_v1.csv | 84 | 150 | Tier1 | True | False |
| latent_plus_mri_engineered | data\sea_ad\stage45\processed\stage45_latent_plus_mri_engineered_feature_matrix_v1.csv | 84 | 165 | Tier1 | True | False |
| latent_plus_safe_metadata_plus_mri_engineered | data\sea_ad\stage45\processed\stage45_latent_plus_safe_metadata_plus_mri_engineered_feature_matrix_v1.csv | 84 | 182 | Tier1 | True | False |
| latent_plus_safe_metadata_plus_cellxgene_plus_mri_engineered | data\sea_ad\stage45\processed\stage45_latent_plus_safe_metadata_plus_cellxgene_plus_mri_engineered_feature_matrix_v1.csv | 84 | 206 | Tier2 | True | False |

## Manual gaps

| missing_feature_class | reason_not_built | exact_resource_needed | source_url | expected_local_path | downstream_script | safety_tier | priority | estimated_complexity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spatial donor summaries | no safe donor-linked processed summaries | donor-level spatial neighborhood table | SEA-AD resources | data/sea_ad/stage45/spatial/ | inventory_stage45_spatial_and_image_resources_v1.py | Tier2 | medium | high |
| non-target image morphology | no precomputed safe embeddings/features | H&E-LFB donor/section morphology summaries | SEA-AD resources | data/sea_ad/stage45/image/ | build_stage45_safe_feature_matrices_v1.py | Tier2 | medium | high |

Prohibited claims: external validation; clean validation; causality; therapeutic relevance; gene-ablation validation; disease-modifying effects
