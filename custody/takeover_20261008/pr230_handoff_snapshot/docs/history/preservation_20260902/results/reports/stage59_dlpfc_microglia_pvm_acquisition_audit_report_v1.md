# Stage59 DLPFC Microglia-PVM acquisition audit

## Dataset audit

| dataset_id | title | metadata_csv_found | local_h5ad_found | metadata_cells | metadata_donors | cell_type_values | analysis_ready_for_expression_benchmark |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 100c6145-7b0e-4ba6-81c1-ffebed0d1ac4 | Microglia-PVM - DLPFC: Seattle Alzheimer's Disease Atlas (SEA-AD) | True | False | 42486 | 83 | microglial cell | False |

## Donor overlap

| dlpfc_metadata_donors | mtg_pathology_target_donors | overlap_donors | overlap_fraction_of_dlpfc | overlap_donor_ids |
| --- | --- | --- | --- | --- |
| 83 | 84 | 80 | 0.963855421686747 | H19.33.004;H20.33.001;H20.33.002;H20.33.004;H20.33.005;H20.33.008;H20.33.011;H20.33.012;H20.33.013;H20.33.014;H20.33.015;H20.33.016;H20.33.017;H20.33.018;H20.33.019;H20.33.020;H20.33.024;H20.33.025;H20.33.026;H20.33.027;H20.33.028;H20.33.029;H20.33.030;H20.33.031;H20.33.032;H20.33.033;H20.33.034;H20.33.035;H20.33.036;H20.33.037;H20.33.038;H20.33.039;H20.33.040;H20.33.041;H20.33.044;H20.33.045;H20.33.046;H21.33.001;H21.33.002;H21.33.003;H21.33.004;H21.33.005;H21.33.006;H21.33.007;H21.33.008;H21.33.011;H21.33.012;H21.33.013;H21.33.014;H21.33.015;H21.33.016;H21.33.017;H21.33.018;H21.33.019;H21.33.020;H21.33.021;H21.33.022;H21.33.023;H21.33.025;H21.33.026;H21.33.027;H21.33.028;H21.33.029;H21.33.030;H21.33.031;H21.33.032;H21.33.033;H21.33.034;H21.33.035;H21.33.036;H21.33.037;H21.33.038;H21.33.040;H21.33.041;H21.33.042;H21.33.043;H21.33.044;H21.33.045;H21.33.046;H21.33.047 |

## Acquisition plan

| step | action | status | safety |
| --- | --- | --- | --- |
| 1 | Acquire DLPFC Microglia-PVM H5AD asset to untracked data/sea_ad/stage45/cellxgene/h5ad_assets/ if expression support is needed | pending_manual_or_wsl_download | do not commit h5ad |
| 2 | Inspect DLPFC obs Supertype/Donor ID and gene coverage | ready_after_h5ad | metadata/expression feature summaries only |
| 3 | Run DLPFC state-module support with frozen MTG modules if donor overlap/pathology linkage is adequate | conditional | support only, not clean external validation |
