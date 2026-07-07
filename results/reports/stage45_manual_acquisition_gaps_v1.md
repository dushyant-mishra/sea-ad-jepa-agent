# Stage 45 manual acquisition gaps

| missing_feature_class | reason_not_built | exact_resource_needed | source_url | expected_local_path | downstream_script | safety_tier | priority | estimated_complexity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spatial donor summaries | no safe donor-linked processed summaries | donor-level spatial neighborhood table | SEA-AD resources | data/sea_ad/stage45/spatial/ | inventory_stage45_spatial_and_image_resources_v1.py | Tier2 | medium | high |
| non-target image morphology | no precomputed safe embeddings/features | H&E-LFB donor/section morphology summaries | SEA-AD resources | data/sea_ad/stage45/image/ | build_stage45_safe_feature_matrices_v1.py | Tier2 | medium | high |