# Stage 40B PI next-steps summary

## Short answer

The locked benchmark remains Stage 27C `module_pca_ridge` (`0.3267024400121495`). The best credible unlocked candidate is Stage 39E `rank_inverse_normal_module_pca8_ridge` (`0.35808116279206914`), but it is not locked. Stage 40A neural rescue failed, so internal architecture tuning on the current feature matrix should pause.

## What to do next

| decision | value | rationale | next_action |
| --- | --- | --- | --- |
| keep_stage27c_locked | True | No Stage 39C-H or Stage 40A candidate was benchmark-lock eligible. | Use Stage 27C for official internal benchmark language. |
| continue_internal_architecture_tuning_on_current_features | False | Stage 40A failed badly versus Stage 39E pca8; further tuning risks overfitting 84 donors. | Pause architecture rescue on current feature matrix. |
| start_manual_multimodal_feature_acquisition | True | Useful signal likely requires safer additional internal modalities/features. | Run Stage41A manual/internal multimodal feature acquisition. |
| continue_external_metadata_repair | True | External branch remains useful for support/readiness but not clean validation. | Maintain as separate support-readiness branch. |

## What to acquire next

| feature_class | source | recommended_priority | allowed_use | next_stage |
| --- | --- | --- | --- | --- |
| image_pathology_morphology | internal pathology images | high | train-fold-safe internal feature engineering; benchmark candidate after audit | Stage41A |
| spatial_neighborhood_summaries | spatial transcriptomics / cell coordinates if available | high | feature acquisition and proxy audit | Stage41A |
| section_slide_covariates | internal slide/section metadata | high | covariate audit and train-fold preprocessing | Stage41A |
| manual_pathology_metadata | manual/expert-curated pathology descriptors | high | candidate features after provenance review | Stage41A |
| external_metadata_repair | external dataset annotations | medium | support-only analysis and eligibility audit | Stage41B_or_external_repair |
| donor_cell_neighborhood_composition | internal cell neighborhoods | medium | proxy-safe decomposition after acquisition | Stage41A |

## Safe language

Use internal benchmark-rescue synthesis, point-estimate improvement, unlocked candidate, support/readiness branch, and next-data acquisition. Do not claim external validation, causality, therapeutic targets, gene ablation, or disease modification.
