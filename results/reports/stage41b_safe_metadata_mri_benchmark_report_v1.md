# Stage 41B safe metadata/MRI benchmark report

Stage 41B built donor-linked Tier-1 candidate feature matrices from Stage 41ABC SEA-AD donor metadata and MRI volumetrics downloads, excluding diagnosis, cognitive, neuropathology, Luminex, and direct target/pathology fields.

Allowed claim: internal SEA-AD safe metadata/MRI benchmark support only. Disallowed claim: external validation; clean validation; causal mechanism; therapeutic target; gene-ablation validation; disease-modifying effect.

## Matrix manifest
| feature_matrix_id | local_processed_path | safe_feature_matrix_built | n_donors | n_features | tier | training_allowed | committed_to_git |
| --- | --- | --- | --- | --- | --- | --- | --- |
| safe_metadata_only | data\sea_ad\stage41b\processed\stage41b_safe_metadata_only_feature_matrix_v1.csv | True | 84 | 17 | Tier1 | True | False |
| mri_only | data\sea_ad\stage41b\processed\stage41b_mri_only_feature_matrix_v1.csv | True | 84 | 148 | Tier1 | True | False |
| safe_metadata_plus_mri | data\sea_ad\stage41b\processed\stage41b_safe_metadata_plus_mri_feature_matrix_v1.csv | True | 84 | 165 | Tier1 | True | False |
| latent_plus_safe_metadata | data\sea_ad\stage41b\processed\stage41b_latent_plus_safe_metadata_feature_matrix_v1.csv | True | 84 | 32 | Tier1 | True | False |
| latent_plus_mri | data\sea_ad\stage41b\processed\stage41b_latent_plus_mri_feature_matrix_v1.csv | True | 84 | 163 | Tier1 | True | False |
| latent_plus_safe_metadata_plus_mri | data\sea_ad\stage41b\processed\stage41b_latent_plus_safe_metadata_plus_mri_feature_matrix_v1.csv | True | 84 | 180 | Tier1 | True | False |

## Mean benchmark metrics
| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- |
| latent_plus_safe_metadata | 0.3394229016907968 | 0.03239850156930242 | 5 |
| latent_plus_safe_metadata_plus_mri | 0.3214012351928724 | 0.07548850865647465 | 5 |
| latent_plus_mri | 0.26698390199453276 | 0.03778475245519895 | 5 |
| safe_metadata_plus_mri | 0.26301913536498944 | 0.039951402247646046 | 5 |
| mri_only | 0.19411556258525117 | -0.023124664622675786 | 5 |
| safe_metadata_only | 0.1704849650703655 | -0.05313354257365597 | 5 |

## Benchmark lock decision
| candidate | benchmark_training_ran | mean_pooled_oof_spearman | benchmark_lock_eligible | locked_benchmark_preserved | stage27c_reference | material_threshold | bootstrap_lower_95 | decision | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| latent_plus_safe_metadata | True | 0.3394229016907968 | False | True | 0.3267024400121495 | 0.3317 | 0.24331358424470376 | do_not_lock_stage41b | one or more strict lock guards failed |

## Target-level results
| condition | target | spearman | n_donors |
| --- | --- | --- | --- |
| safe_metadata_only | AT8 | 0.43239850156930243 | 84 |
| safe_metadata_only | 6e10/A_beta | 0.3831932773109244 | 84 |
| safe_metadata_only | GFAP | 0.10045560392831832 | 84 |
| safe_metadata_only | Iba1 | -0.05313354257365597 | 84 |
| safe_metadata_only | NeuN | -0.010489014883061658 | 84 |
| mri_only | AT8 | 0.2952647085775367 | 84 |
| mri_only | 6e10/A_beta | 0.19356275755530455 | 84 |
| mri_only | GFAP | 0.2349117638245725 | 84 |
| mri_only | Iba1 | -0.023124664622675786 | 84 |
| mri_only | NeuN | 0.26996324759151796 | 84 |
| safe_metadata_plus_mri | AT8 | 0.3470486989976714 | 84 |
| safe_metadata_plus_mri | 6e10/A_beta | 0.3285410549762074 | 84 |
| safe_metadata_plus_mri | GFAP | 0.3232762984711957 | 84 |
| safe_metadata_plus_mri | Iba1 | 0.039951402247646046 | 84 |
| safe_metadata_plus_mri | NeuN | 0.27627822213222636 | 84 |
| latent_plus_safe_metadata | AT8 | 0.5838817454692721 | 84 |
| latent_plus_safe_metadata | 6e10/A_beta | 0.45637339273058625 | 84 |
| latent_plus_safe_metadata | GFAP | 0.30760352333704566 | 84 |
| latent_plus_safe_metadata | Iba1 | 0.03239850156930242 | 84 |
| latent_plus_safe_metadata | NeuN | 0.3168573453477777 | 84 |
| latent_plus_mri | AT8 | 0.41447808038878203 | 84 |
| latent_plus_mri | 6e10/A_beta | 0.23191252404576287 | 84 |
| latent_plus_mri | GFAP | 0.3116330869697277 | 84 |
| latent_plus_mri | Iba1 | 0.03778475245519895 | 84 |
| latent_plus_mri | NeuN | 0.33911106611319225 | 84 |
| latent_plus_safe_metadata_plus_mri | AT8 | 0.49857244102460263 | 84 |
| latent_plus_safe_metadata_plus_mri | 6e10/A_beta | 0.3408727346360231 | 84 |
| latent_plus_safe_metadata_plus_mri | GFAP | 0.3773412979649691 | 84 |
| latent_plus_safe_metadata_plus_mri | Iba1 | 0.07548850865647465 | 84 |
| latent_plus_safe_metadata_plus_mri | NeuN | 0.3147311936822922 | 84 |

## Safety/proxy decision
| feature_recipe | proxy_leakage_decision | tier3_used | tier4_used | notes |
| --- | --- | --- | --- | --- |
| metadata_mri_tier1 | tier1_safe_after_forbidden_column_exclusion | False | False | diagnosis/cognitive/neuropathology/Luminex/target columns excluded |
