# Stage 39E PI simple-model leaderboard summary

## Short answer

Best condition: `rank_inverse_normal_module_direct_elasticnet`. Mean pooled OOF Spearman: `0.37851256756728835`. Delta versus Stage 39C: `0.03270311125464276`. Stage 39E material leaderboard pass: `False`.

## Top leaderboard rows

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets | target_transform | feature_view | n_components | model | primary_leaderboard_allowed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank_inverse_normal_module_direct_elasticnet | 0.37851256756728835 | 0.12208036796026417 | 5 | rank_inverse_normal | direct |  | elasticnet | True |
| rank_inverse_normal_module_pca8_ridge | 0.35808116279206914 | 0.056974172849842526 | 5 | rank_inverse_normal | pca | 8.0 | ridge | True |
| rank_inverse_normal_module_pca8_huber | 0.35501069559916243 | -0.015960059795832177 | 5 | rank_inverse_normal | pca | 8.0 | huber | True |
| rank_inverse_normal_module_pca12_ridge | 0.3441957425548366 | 0.0721139503845945 | 5 | rank_inverse_normal | pca | 12.0 | ridge | True |
| rank_inverse_normal_module_pca4_huber | 0.34286388270560486 | 0.16955538144772725 | 5 | rank_inverse_normal | pca | 4.0 | huber | True |
| rank_inverse_normal_module_direct_ridge | 0.34123240177127856 | 0.06999741961217766 | 5 | rank_inverse_normal | direct |  | ridge | True |
| rank_inverse_normal_module_pca16_ridge | 0.34123240177127856 | 0.06999741961217766 | 5 | rank_inverse_normal | pca | 16.0 | ridge | True |
| rank_inverse_normal_module_pca12_huber | 0.3336317223197651 | 0.05467535713051899 | 5 | rank_inverse_normal | pca | 12.0 | huber | True |
| rank_inverse_normal_module_direct_huber | 0.33240631677446497 | 0.0025114814907147083 | 5 | rank_inverse_normal | direct |  | huber | True |
| rank_inverse_normal_module_pca16_huber | 0.33240631677446497 | 0.0025114814907147083 | 5 | rank_inverse_normal | pca | 16.0 | huber | True |
| rank_inverse_normal_module_pca8_elasticnet | 0.33220078538945647 | 0.015541478923225355 | 5 | rank_inverse_normal | pca | 8.0 | elasticnet | True |
| raw_log1p_module_pca8_huber | 0.33112078566366304 | -0.02824744355573555 | 5 | raw_log1p | pca | 8.0 | huber | True |

## Best-model target deltas

| target | stage39e | stage39c | delta_vs_stage39c |
| --- | --- | --- | --- |
| 6e10/A_beta | 0.33392422739803806 | 0.4001619925078465 | -0.06623776510980844 |
| AT8 | 0.6297023981186389 | 0.5254834463906044 | 0.10421895172803453 |
| GFAP | 0.3369586193142646 | 0.3122608079376329 | 0.024697811376631684 |
| Iba1 | 0.12208036796026417 | 0.025473321858864 | 0.09660704610140017 |
| NeuN | 0.46989722504523623 | 0.4656677128682798 | 0.00422951217695644 |

## Safe interpretation

Stage 39E is an internal simple-model leaderboard. It excludes the Stage 39D composition/proxy features from the primary benchmark. It does not establish external validation, causality, therapeutic relevance, disease modification, or gene-ablation effects.
