# Stage62 feature source and gene availability

## Feature source

| gene_symbol_source | var_index_contains_ensembl_ids | var_index_must_not_be_used_as_gene_symbols | n_dlpfc_feature_donors | n_pathology_target_donors | n_overlap_donors | n_cells_loaded | n_features | n_state_abundance_features | n_state_expression_module_features | feature_source_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| var/feature_name | True | True | 80 | 84 | 80 | 42486 | 120 | 12 | 108 | True |

## Gene availability

| module_name | requested_genes | present_genes | missing_genes | n_present | usable |
| --- | --- | --- | --- | --- | --- |
| dam_lipid_trem2_apoe | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD |  | 8 | True |
| lysosomal_endolysosomal | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;GBA;PSAP | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;PSAP | GBA | 7 | True |
| complement_phagocytosis | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 |  | 7 | True |
| antigen_presentation | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M |  | 6 | True |
| interferon_inflammatory | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG |  | 7 | True |
| oxidative_stress_gene_preserved | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP |  | 7 | True |
