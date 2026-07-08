# Stage61 DLPFC Microglia-PVM support audit

## Acquisition

| dataset_id | local_h5ad | download_attempted | download_succeeded | filesize_bytes | source |
| --- | --- | --- | --- | --- | --- |
| 100c6145-7b0e-4ba6-81c1-ffebed0d1ac4 | C:\Users\dushy\Desktop\Jepa project\data\sea_ad\stage45\cellxgene\h5ad_assets\100c6145-7b0e-4ba6-81c1-ffebed0d1ac4.h5ad | True | True | 715262151 | CELLxGENE collection API |

## Donor/schema overlap

| dlpfc_feature_donors | pathology_target_donors | overlap_donors | donor_column | state_column | n_cells_loaded |
| --- | --- | --- | --- | --- | --- |
| 83 | 84 | 80 | donor_id | Supertype | 42486 |

## Branch comparison

| model_variant | latent_dim | seed | mean_pooled_oof_spearman | delta_vs_stage27c_locked | delta_vs_stage55_mtg_best |
| --- | --- | --- | --- | --- | --- |
| mtg_programming_plus_dlpfc_state_modules | 16 | 307 | 0.33876699484294426 | 0.012064554830794771 | 0.012736823738357828 |
| mtg_programming_only | 16 | 307 | 0.3358368495077356 | 0.009134409495586138 | 0.009806678403149194 |
| negative_control_mtg_programming_plus_donor_shuffled_dlpfc | 16 | 307 | 0.332962962962963 | 0.00626052295081353 | 0.006932791858376586 |
| dlpfc_state_modules_only | 8 | 107 | 0.20036568213783404 | -0.12633675787431545 | -0.1256644889667524 |

Best real: `0.33876699484294426`; best negative control: `0.332962962962963`.

This is regional/internal support only, not clean external validation.
