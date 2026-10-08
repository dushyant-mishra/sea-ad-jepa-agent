# Stage61 DLPFC Microglia-PVM support audit

## Acquisition

| dataset_id | local_h5ad | download_attempted | download_succeeded | filesize_bytes | source |
| --- | --- | --- | --- | --- | --- |
| 100c6145-7b0e-4ba6-81c1-ffebed0d1ac4 | C:\Users\dushy\Desktop\Jepa project\data\sea_ad\stage45\cellxgene\h5ad_assets\100c6145-7b0e-4ba6-81c1-ffebed0d1ac4.h5ad | False | True | 715262151 | CELLxGENE collection API |

## Donor/schema overlap

| dlpfc_feature_donors | pathology_target_donors | overlap_donors | donor_column | state_column | n_cells_loaded |
| --- | --- | --- | --- | --- | --- |
| 83 | 84 | 80 | donor_id | Supertype | 42486 |

## Feature-source audit

DLPFC gene symbols are read from `var/feature_name`; `var/_index` contains Ensembl IDs in this H5AD. The DLPFC branch contains 120 features: 12 obs-derived state abundance features and 108 gene-expression module-score features computed within Supertype/state strata. The feature inventory labels these sources explicitly.

## Gene availability

| module_name | requested_genes | present_genes | missing_genes | n_present | usable |
| --- | --- | --- | --- | --- | --- |
| dam_lipid_trem2_apoe | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD |  | 8 | True |
| lysosomal_endolysosomal | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;GBA;PSAP | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;PSAP | GBA | 7 | True |
| complement_phagocytosis | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 |  | 7 | True |
| antigen_presentation | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M |  | 6 | True |
| interferon_inflammatory | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG |  | 7 | True |
| oxidative_stress_gene_preserved | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP |  | 7 | True |

## Branch comparison

| model_variant | latent_dim | seed | mean_pooled_oof_spearman | delta_vs_stage27c_locked | delta_vs_stage55_mtg_best |
| --- | --- | --- | --- | --- | --- |
| mtg_programming_plus_dlpfc_state_modules | 16 | 307 | 0.34332395686826067 | 0.016621516856111185 | 0.01729378576367424 |
| mtg_programming_only | 16 | 307 | 0.3358368495077356 | 0.009134409495586138 | 0.009806678403149194 |
| negative_control_mtg_programming_plus_donor_shuffled_dlpfc | 16 | 307 | 0.32714017815283636 | 0.0004377381406868719 | 0.001110007048249928 |
| dlpfc_state_modules_only | 8 | 211 | 0.21836849507735584 | -0.10833394493479365 | -0.10766167602723059 |

Best real: `0.34332395686826067`; best negative control: `0.32714017815283636`.

This is regional/internal support only, not clean external validation.
