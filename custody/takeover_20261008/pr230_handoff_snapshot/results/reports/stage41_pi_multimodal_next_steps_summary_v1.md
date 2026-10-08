# Stage 41 PI multimodal next-steps summary

## Short answer

Safe new donor-linked multimodal/spatial/image feature classes found for benchmark training: `0`. Benchmark training ran: `False`. Recommended next executable stage: `Stage41A_manual_internal_feature_acquisition`.

## What is missing?

| feature_class | required_source | currently_available | priority | proposed_next_stage |
| --- | --- | --- | --- | --- |
| image-derived morphology features | internal pathology image tiles/whole-slide morphology table linked to donor/section | False | high | Stage41A_manual_internal_feature_acquisition |
| pathology image embeddings | internal image encoder embeddings not trained on held-out target labels | False | high | Stage41A_manual_internal_feature_acquisition |
| section-level image descriptors | section/tile QC and morphology descriptors | False | high | Stage41A_manual_internal_feature_acquisition |
| spatial neighborhood summaries | cell coordinates/spatial transcriptomics neighborhoods | False | high | Stage41A_manual_internal_feature_acquisition |
| region/anatomy covariates | safe anatomy/region labels known before target scoring | False | medium | Stage41A_manual_internal_feature_acquisition |
| cell-density or neighborhood composition | local cell density tables | False | medium | Stage41A_manual_internal_feature_acquisition |
| manual curated internal covariates | curated pathology/slide notes with known provenance | False | medium | Stage41A_manual_internal_feature_acquisition |
| clean external metadata | external dataset metadata repair | False | medium | Stage41B_external_metadata_repair |

## Benchmark decision

| candidate_id | feature_set_id | model_name | feature_classes_used | risk_tiers_used | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39e_pca8 | delta_vs_stage39h_context | lower_ci_above_stage27c | lower_ci_above_material_threshold | target_guard_pass | abeta_guard_pass | iba1_rescue_status | negative_controls_pass | proxy_leakage_risk_pass | high_influence_donor_or_fold_flag | benchmark_lock_eligible | recommended_decision | allowed_claim_language | prohibited_claim_language | recommended_next_stage | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage41_safe_multimodal_candidate | latent_plus_safe_multimodal | ridge |  |  |  |  |  |  | False | False | False | False | not_tested_missing_safe_features | False | False | False | False | manual_feature_acquisition_required | internal multimodal feature acquisition planning only | external validation; causal; therapeutic; gene-ablation; disease-modifying claims | Stage41A_manual_internal_feature_acquisition | new donor-linked safe multimodal/spatial/image feature table not found |

## Safe interpretation

Stage 41 is an internal feature acquisition/readiness workflow. It does not establish external validation, clean validation, causality, therapeutic relevance, gene-ablation support, or disease modification.
