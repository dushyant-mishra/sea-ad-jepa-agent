# Stage72A external multiomic GRN resource eligibility audit

## Bottom line

Stage72A audits and, when requested, acquires public processed GSE174367 Morabito snRNA/snATAC resources needed for a context-specific Micro-PVM regulatory graph branch. It does not construct a graph or train a model.

GEO source: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174367

## Resource inventory

| dataset_id | resource_id | expected_role | url | local_path | exists | size_bytes | sha256 | readable | n_rows_estimate | n_columns | columns_sample | h5_keys | matrix_shape | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GSE174367 | snATAC_cell_metadata | graph_construction_metadata | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snATAC-seq_cell_meta.csv.gz | data/external/gse174367/GSE174367_snATAC-seq_cell_meta.csv.gz | True | 1066930 | 0657e92aa49eed953aae3b3c5f70aacebe86621c0a930356ec53ba0107c81767 | True | 130418 | 12 | Sample.ID;Batch;Age;Sex;PMI;Tangle.Stage;Plaque.Stage;Diagnosis;RIN;cluster;Cell.Type;Barcode |  |  |  |
| GSE174367 | snATAC_peak_matrix | graph_construction_accessibility | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5 | data/external/gse174367/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5 | True | 360317403 | ff7c46e755ec0e3fecb319c5b3dd9ac0ada318525746ebe7dddb8e2c0dcab87f | True |  |  |  | matrix | (219070, 143401) |  |
| GSE174367 | snRNA_cell_metadata | graph_construction_expression_metadata | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snRNA-seq_cell_meta.csv.gz | data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz | True | 435170 | ab1a029deb43196e2bb1fea5907d838885750cfff3850c600c07588c7c7cdb2b | True | 61472 | 12 | Barcode;SampleID;Diagnosis;Batch;Cell.Type;cluster;Age;Sex;PMI;Tangle.Stage;Plaque.Stage;RIN |  |  |  |
| GSE174367 | snRNA_expression_matrix | graph_construction_expression | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5 | data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5 | True | 273975534 | 6ba98a1af8772af08c8cdd5e5e63eebb0890daed48cac2e1b8961dcc67069b77 | True |  |  |  | matrix | (58721, 61770) |  |
| SEA-AD | seaad_mtg_h5ad | benchmark_rna_mtg_available |  | data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad | True | 462024617 | fc40b7c64b8bacd42e19b28227e4b6f02c3a9a3f09aefc8cddc9ea0bde09ca5d | True |  |  |  | X;layers;obs;obsm;obsp;uns;var;varm;varp | (40000, 2977) |  |
| SEA-AD | seaad_dlpfc_h5ad | benchmark_rna_dlpfc_available |  | data/sea_ad/stage45/cellxgene/h5ad_assets/100c6145-7b0e-4ba6-81c1-ffebed0d1ac4.h5ad | True | 715262151 | 3591220dc13aa39aa1d8d551fb8384bd32b205920cae79f399d11b1e72e07011 | True |  |  |  | X;layers;obs;obsm;obsp;raw;uns;var;varm;varp | (42486, 35483) |  |
| GSE157827 | gse157827_schema_dir | protected_external_schema_only |  | data/external/public_schema_audit/GSE157827 | True | 0 |  | True |  |  | GSE157827_series_matrix.txt.gz |  |  | directory_with_1_files |

## Download log

| dataset_id | resource_id | url | local_path | download_attempted | download_succeeded | bytes_written | error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GSE174367 | snATAC_cell_metadata | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snATAC-seq_cell_meta.csv.gz | C:\Users\dushy\Desktop\Jepa project\data\external\gse174367\GSE174367_snATAC-seq_cell_meta.csv.gz | True | True | 1066930 |  |
| GSE174367 | snATAC_peak_matrix | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5 | C:\Users\dushy\Desktop\Jepa project\data\external\gse174367\GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5 | True | True | 360317403 |  |
| GSE174367 | snRNA_cell_metadata | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snRNA-seq_cell_meta.csv.gz | C:\Users\dushy\Desktop\Jepa project\data\external\gse174367\GSE174367_snRNA-seq_cell_meta.csv.gz | False | True | 435170 | already_present |
| GSE174367 | snRNA_expression_matrix | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5 | C:\Users\dushy\Desktop\Jepa project\data\external\gse174367\GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5 | False | True | 273975534 | already_present |

## GRN readiness

| ready_for_stage72b_grn_construction | gse174367_snRNA_available | gse174367_snATAC_available | sea_ad_atac_or_multiome_confirmed_local | sea_ad_rna_context_available | recommended_next_stage | limitation |
| --- | --- | --- | --- | --- | --- | --- |
| True | True | True | False | True | Stage72B_external_morabito_micro_pvm_grn_construction_v1 | SEA-AD ATAC/Multiome controlled-access files are not confirmed local; initial contextualization may be RNA-only unless acquired separately. |

## Protected external expression test

| dataset_id | local_schema_found | prior_stage37e_analysis_can_run | protected_external_expression_ready | manual_approval_required_before_expression_opening | recommended_use | claim_level |
| --- | --- | --- | --- | --- | --- | --- |
| GSE157827 | True | False | False | True | frozen external expression projection only after approval and expression acquisition | conditional external support only; not clean validation unless registry gate changes |

## Next actions

| priority | action | stage | requires_network |
| --- | --- | --- | --- |
| 1 | Use acquired GSE174367 snRNA+snATAC processed files to build a Morabito microglia regulatory graph candidate. | Stage72B | False |
| 2 | Audit whether SEA-AD ATAC/Multiome controlled-access resources are locally available and donor-linkable; if not, prepare manual acquisition list. | Stage72C | False |
| 3 | Keep GSE157827 protected until expression availability and approval are confirmed; use only for frozen projection. | Stage73 | True |

## Claim boundary

| stage72a_is_resource_audit_and_acquisition_only | no_graph_constructed | no_model_training | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | raw_or_large_data_not_committed | downloaded_data_under_data_dir_only | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True |
