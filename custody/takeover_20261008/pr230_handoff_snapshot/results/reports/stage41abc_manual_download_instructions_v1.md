# Stage 41ABC manual download instructions

## safe donor metadata

- Resource: SEA-AD donor metadata table/data dictionary
- URL: https://brain-map.org/consortia/sea-ad/our-data
- Why not automatic: not found as directly downloadable safe table or requires manual portal selection
- Save under: `data/sea_ad/stage41abc/raw/donor_metadata/`
- Downstream script: `build_stage41abc_donor_feature_matrices_v1.py`
- Priority/complexity: high / medium

## postmortem MRI volumetrics

- Resource: SEA-AD postmortem MRI volumetric table
- URL: https://brain-map.org/consortia/sea-ad/our-data
- Why not automatic: not found as ready small table or requires manual portal selection
- Save under: `data/sea_ad/stage41abc/raw/mri_volumetrics/`
- Downstream script: `build_stage41abc_donor_feature_matrices_v1.py`
- Priority/complexity: high / medium

## CELLxGENE donor-cell metadata

- Resource: SEA-AD CELLxGENE metadata/h5ad
- URL: https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30
- Why not automatic: large/raw metadata access requires explicit CELLxGENE/Census export
- Save under: `data/sea_ad/stage41abc/raw/cellxgene_metadata/`
- Downstream script: `build_stage41abc_donor_feature_matrices_v1.py`
- Priority/complexity: high / high

## spatial neighborhood summaries

- Resource: SEA-AD spatial transcriptomics processed metadata
- URL: https://brain-map.org/consortia/sea-ad/our-data
- Why not automatic: raw/large spatial resources are manifest-only by policy
- Save under: `data/sea_ad/stage41abc/raw/spatial/`
- Downstream script: `build_stage41abc_donor_feature_matrices_v1.py`
- Priority/complexity: medium / high

## snATAC regulatory summaries

- Resource: SEA-AD snATAC processed summaries
- URL: https://brain-map.org/consortia/sea-ad/our-data
- Why not automatic: not present as small approved table
- Save under: `data/sea_ad/stage41abc/raw/snatac/`
- Downstream script: `build_stage41abc_donor_feature_matrices_v1.py`
- Priority/complexity: medium / high

## non-target image morphology

- Resource: H&E-LFB or non-target image feature summaries
- URL: https://brain-map.org/consortia/sea-ad/our-resources
- Why not automatic: raw images forbidden for automatic download
- Save under: `data/sea_ad/stage41abc/raw/image_morphology/`
- Downstream script: `build_stage41abc_donor_feature_matrices_v1.py`
- Priority/complexity: medium / high
