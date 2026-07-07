# Stage 41ABC PI download/feature summary

Stage 27C remains the locked official benchmark. Stage 41ABC focused on acquiring/analyzing safe SEA-AD resources rather than trying another model prematurely.

- Resource pages fetched: 3 / 3
- Files downloaded: 18
- Benchmark training ran: False
- Benchmark lock decision: manual_feature_acquisition_required
- Highest-priority remaining acquisition: safe donor metadata

## Top remaining manual acquisitions
| missing_feature_class | required_resource | source_url | reason_not_downloaded | manual_download_or_processing_instruction | expected_local_path | downstream_script_needed | priority | estimated_complexity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| safe donor metadata | SEA-AD donor metadata table/data dictionary | https://brain-map.org/consortia/sea-ad/our-data | not found as directly downloadable safe table or requires manual portal selection | Download public donor metadata table; save checksum and schema. | data/sea_ad/stage41abc/raw/donor_metadata/ | build_stage41abc_donor_feature_matrices_v1.py | high | medium |
| postmortem MRI volumetrics | SEA-AD postmortem MRI volumetric table | https://brain-map.org/consortia/sea-ad/our-data | not found as ready small table or requires manual portal selection | Download MRI volumetrics workbook/table and provenance document. | data/sea_ad/stage41abc/raw/mri_volumetrics/ | build_stage41abc_donor_feature_matrices_v1.py | high | medium |
| CELLxGENE donor-cell metadata | SEA-AD CELLxGENE metadata/h5ad | https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30 | large/raw metadata access requires explicit CELLxGENE/Census export | Export donor/cell metadata only; avoid raw expression unless approved. | data/sea_ad/stage41abc/raw/cellxgene_metadata/ | build_stage41abc_donor_feature_matrices_v1.py | high | high |
| spatial neighborhood summaries | SEA-AD spatial transcriptomics processed metadata | https://brain-map.org/consortia/sea-ad/our-data | raw/large spatial resources are manifest-only by policy | Acquire processed donor-linked coordinates/summaries; do not download huge raw matrices automatically. | data/sea_ad/stage41abc/raw/spatial/ | build_stage41abc_donor_feature_matrices_v1.py | medium | high |
| snATAC regulatory summaries | SEA-AD snATAC processed summaries | https://brain-map.org/consortia/sea-ad/our-data | not present as small approved table | Acquire processed donor-linked module/regulatory summaries. | data/sea_ad/stage41abc/raw/snatac/ | build_stage41abc_donor_feature_matrices_v1.py | medium | high |
| non-target image morphology | H&E-LFB or non-target image feature summaries | https://brain-map.org/consortia/sea-ad/our-resources | raw images forbidden for automatic download | Acquire precomputed donor/section-level morphology summaries only. | data/sea_ad/stage41abc/raw/image_morphology/ | build_stage41abc_donor_feature_matrices_v1.py | medium | high |

Safe language: these are resource-readiness and follow-up benchmark-preparation results only. They are not external validation and do not establish causality or therapeutic relevance.
