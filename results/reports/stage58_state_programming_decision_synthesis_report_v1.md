# Stage58 state-programming decision synthesis

| stage | best_model_variant | best_mean_pooled_oof_spearman | delta_vs_stage27c | beats_stage27c | beats_material_threshold |
| --- | --- | --- | --- | --- | --- |
| Stage53 | all_branches_jepa | 0.318906550572036 | -0.0077958894401135015 | False | False |
| Stage54 | programming_plus_state_specific_module_programming | 0.3250906145590767 | -0.0016118254530728127 | False | False |
| Stage55 | programming_plus_state_module_programming | 0.3260301711045864 | -0.0006722689075631116 | False | False |
| Stage56 | nested_target_gated_programming_vs_state_module | 0.3225068340589248 | -0.0041956059532247125 | False | False |
| Stage57 | programming_plus_repaired_state_modules_full | 0.3256697377746279 | -0.00103270223752161 | False | False |

## Decision

Stage55 remains the strongest state-programming near-miss, but no Stage53-57 result beats Stage27C or reaches the material rescue threshold. The next move is new signal, not more tuning: gene-preserved MTG module extraction and DLPFC support audit.

| priority_rank | next_action | reason | claim_boundary |
| --- | --- | --- | --- |
| 1 | Stage60_gene_preserved_MTG_module_rebuild | raw MTG contains missing stress/module genes and decodable Micro-PVM state labels; can test whether missing genes explain near-miss | internal benchmark only |
| 2 | Stage59_DLPFC_Microglia_PVM_acquisition_support_audit | DLPFC Microglia-PVM exists online/local metadata; region support may clarify generality | support/acquisition audit unless donor/pathology linkage exists |
| 3 | spatial_or_plaque_proximity_feature_acquisition | current transcriptomic state modules are subthreshold; spatial/pathology-proximity features are likely missing signal | manual acquisition/readiness only |
