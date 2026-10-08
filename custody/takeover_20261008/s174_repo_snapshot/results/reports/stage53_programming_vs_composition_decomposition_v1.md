# Stage53 heterogeneity/composition auxiliary JEPA report

Stage53 tested whether donor-level disease-state recovery improves when donor-average microglia/PVM programming features are augmented with real donor-linked SEA-AD microglia/PVM `Supertype` heterogeneity features and Stage45 CELLxGENE cell-type composition features.

This stage does not change the official benchmark. Stage27C remains locked at `0.326702`. Stage41C remains credible-unlocked, Stage45 remains negative, and Stage51 remains graph-topology-null.

## Inputs and branch construction

- Programming input: `data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv`
- Heterogeneity input found: `1`
- Composition input found: `1`
- Auxiliary training ran: `True`
- Pathology/diagnosis/CERAD/Braak/cognitive labels used as features: `False`

## Branch benchmark summary

| model_variant | latent_dim | seed | mean_pooled_oof_spearman | delta_vs_stage27c_locked |
| --- | --- | --- | --- | --- |
| all_branches_jepa | 8 | 107 | 0.31890655057203604 | -0.007795889440113446 |
| programming_only_jepa | 8 | 107 | 0.3182423812898653 | -0.00846005872228417 |
| programming_plus_heterogeneity_jepa | 8 | 107 | 0.3180722891566265 | -0.008630150855522989 |
| programming_plus_composition_jepa | 8 | 107 | 0.3172461273666093 | -0.009456312645540199 |
| negative_control_programming_plus_donor_shuffled_heterogeneity | 8 | 107 | 0.31597043636731803 | -0.010732003644831456 |
| heterogeneity_only_jepa | 8 | 211 | 0.27465424724106513 | -0.052048192771084356 |
| heterogeneity_plus_composition_jepa | 16 | 107 | 0.23600688468158348 | -0.090695555330566 |
| composition_only_jepa | 16 | 307 | 0.21327933583071781 | -0.11342310418143167 |
| programming_residualized_against_composition_jepa | 8 | 107 | 0.0045155411562215145 | -0.322186898855928 |

## Hidden microglia/PVM state audit

| microglia_state | state_fraction_vs_target_spearman | support_level |
| --- | --- | --- |
| Micro-PVM_3-SEAAD | 0.23990685430798825 | possible_state |
| Micro-PVM_1 | 0.10507239040194391 | weak_support |
| Micro-PVM_4-SEAAD | 0.09157659926297809 | weak_support |
| Monocyte | 0.0898112008941304 | weak_support |
| Lymphocyte | 0.05052066723971418 | weak_support |
| Micro-PVM_2_1-SEAAD | 0.027577568514056634 | weak_support |
| Micro-PVM_2_3-SEAAD | -0.057539738787081095 | weak_support |
| Micro-PVM_2 | -0.09420269312544297 | weak_support |

These state scores are post hoc donor-level associations only. They nominate candidate follow-up substates; they do not discover a new cell type, prove pathogenic causality, or establish a therapeutic target.

## Limitations

- Supertype composition is donor-linked and useful, but it is still a composition/heterogeneity feature rather than direct causal evidence.
- Cell-level expression/module quantiles were not materialized in this first Stage53 run to avoid loading raw expression layers.
- All pathology readouts were used only after label-free feature construction, through frozen donor-held-out probes.
