# Stage53 PI summary

Stage53 found usable donor-linked microglia/PVM `Supertype` labels and Stage45 composition metadata. The benchmark is an internal auxiliary-branch analysis, not validation.

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
