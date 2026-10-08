# Stage60 gene-preserved MTG microglia module rebuild

Selected Micro-PVM raw-H5AD cells: `40000`.

## Branch comparison

| model_variant | latent_dim | seed | mean_pooled_oof_spearman | delta_vs_stage27c_locked | delta_vs_stage55_best |
| --- | --- | --- | --- | --- | --- |
| programming_plus_gene_preserved_state_modules | 8 | 107 | 0.3245884377847525 | -0.002114002227396994 | -0.0014417333198339377 |
| negative_control_programming_plus_state_shuffled_gene_preserved | 8 | 107 | 0.32102865242482537 | -0.0056737875873241195 | -0.005001518679761063 |
| programming_only_pca_jepa | 8 | 107 | 0.3182423812898653 | -0.00846005872228417 | -0.007787789814721113 |
| gene_preserved_state_modules | 8 | 307 | 0.26782221322263844 | -0.05888022678951105 | -0.05820795788194799 |

## Gene availability

| module_name | requested_genes | present_genes | missing_genes | n_present |
| --- | --- | --- | --- | --- |
| dam_lipid_trem2_apoe | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD |  | 8 |
| lysosomal_endolysosomal | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;GBA;PSAP | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;GBA;PSAP |  | 8 |
| complement_phagocytosis | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 |  | 7 |
| antigen_presentation | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M |  | 6 |
| interferon_inflammatory | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG |  | 7 |
| oxidative_stress_gene_preserved | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP |  | 7 |

Best real: `0.324588`; best negative control: `0.321029`; Stage27C: `0.326702`.
