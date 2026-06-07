# v2.1 Microglia Biological Hypotheses

This report summarizes biology extracted from the Graph-JEPA v2.1 checkpoint `upgrade_fine_08` and compares it with the AT8-strong bridge checkpoint `fine_bridge_06`.

## Interpretation Boundary

These results are model-implied hypotheses. They are not experimental proof of causality. The digital perturbations ask how a trained representation and donor-level pathology head respond when gene or module expression is counterfactually shifted toward a reference value. True causal validation still requires perturbation data or wet-lab follow-up.

## Model Showdown

`upgrade_fine_08` is the preferred v2.1 model because it preserves healthy anchors while improving balanced AT8, NeuN, and GFAP geometry. `fine_bridge_06` remains useful as an AT8-sensitive comparator. The core biology is more credible when both checkpoints point toward overlapping genes, modules, or latent axes.

### upgrade_fine_08 Decoded Latent Axes

| model | latent_factor | top_genes | top_modules | actionable_hits |
| --- | --- | --- | --- | --- |
| upgrade_fine_08 | z_120 | GRB2, RHOA, EP300, ACTB, CSF1R, RAP1A, HIF1A, BCL2 | homeostatic_microglia | CSF1R, BCL2 |
| upgrade_fine_08 | z_26 | CDC42, ATM, CSF1R, BCL2, PTEN, CTNNB1, DDX5, DYRK1A | homeostatic_microglia | CSF1R, BCL2 |
| upgrade_fine_08 | z_30 | BCL2, RAP1A, RHOA, GRB2, RB1, HIF1A, CDC42, PIK3R1 |  | BCL2 |
| upgrade_fine_08 | z_94 | RHOA, HIF1A, RB1, BCL2, RAP1A, ACTB, CUL3, ARID1A |  | BCL2 |
| upgrade_fine_08 | z_71 | GRB2, EP300, RAC1, HIF1A, RHOA, ACTB, CDC42, CD4 |  | CD4 |
| upgrade_fine_08 | z_63 | GRB2, LRRK1, CDKAL1, VPS13B, ANKRD12, RUFY3, CTNND1, UBE2D3 |  | CDKAL1 |
| upgrade_fine_08 | z_1 | GRB2, RHOA, AFF1, AUTS2, UBE2D3, DDX17, BCL2, CSGALNACT1 |  | BCL2 |
| upgrade_fine_08 | z_57 | RAP1A, HIF1A, RAC1, STAT3, RASA1, EP300, CSF1R, RHOA | homeostatic_microglia | CSF1R |
| upgrade_fine_08 | z_103 | CDC42, GRB2, SETD2, LYN, PTEN, CLTC, CSF1R, HERC1 | homeostatic_microglia | CSF1R |
| upgrade_fine_08 | z_100 | CSF1R, BCL2, RAP1A, SPTLC2, CDC42, ROCK1, NAV3, FBXO11 | homeostatic_microglia | CSF1R, BCL2, SPTLC2, ROCK1 |
| upgrade_fine_08 | z_125 | BCL2, USP34, CDC42, RAP1A, CTNNB1, LINC02798, PABPC1, EP300 |  | BCL2 |
| upgrade_fine_08 | z_38 | CDC42, NF1, HSP90AA1, NCK2, CTNNB1, GRB2, CUL1, DDX17 | senescence_stress | NF1 |
| upgrade_fine_08 | z_107 | CTNNB1, CDC42, ATM, RB1, PTEN, RHOA, CREBBP, DYRK1A |  |  |

### fine_bridge_06 Decoded Latent Axes

| model | latent_factor | top_genes | top_modules | actionable_hits |
| --- | --- | --- | --- | --- |
| fine_bridge_06 | z_120 | BCL2, LINC02798, RB1, GRB2, HIF1A, ROCK1, RAP1A, NCOA3 |  | BCL2, ROCK1 |
| fine_bridge_06 | z_26 | RHOA, EP300, HIF1A, RAC1, CDC42, ACTB, CUL3, NRXN1 |  | NRXN1 |
| fine_bridge_06 | z_30 | CDC42, RAC1, CTNNB1, HIF1A, RHOA, ACTB, APP, PTEN |  | APP |
| fine_bridge_06 | z_94 | GRB2, CTNNB1, CD74, MAPK1, PAFAH1B1, RAC1, TRA2B, RHOA | antigen_presentation | CD74, MAPK1 |
| fine_bridge_06 | z_71 | LYN, HIF1A, SH3KBP1, ARHGAP12, TENT2, RAP1A, RAC1, SPIDR |  |  |
| fine_bridge_06 | z_63 | RHOA, EP300, CNOT1, CDC42, RB1, PIK3R1, CSF1R, GRB2 | homeostatic_microglia | CNOT1, CSF1R |
| fine_bridge_06 | z_1 | RHOA, GRB2, EP300, CDC42, BCL2, ACTB, HIF1A, CSF1R | homeostatic_microglia | BCL2, CSF1R |
| fine_bridge_06 | z_57 | RHOA, EP300, APOE, NIPBL, ATM, UBC, DHX9, PTEN | disease_associated_microglia; lipid_metabolism; plaque_response | APOE |
| fine_bridge_06 | z_103 | RHOA, CDC42, EP300, GRB2, ACTB, HSP90AA1, RASA1, PTEN | senescence_stress |  |
| fine_bridge_06 | z_100 | RHOA, RB1, CTNNB1, RAB10, TLR2, CDC42, RAP1A, CD74 | antigen_presentation | TLR2, CD74 |
| fine_bridge_06 | z_125 | TLR2, NIPBL, RHOA, STAT3, PUM2, ATM, CTNNB1, CREBBP |  | TLR2 |
| fine_bridge_06 | z_38 | EP300, GRB2, RHOA, BCL2, ACTB, CUL1, FARS2, CREBBP |  | BCL2 |
| fine_bridge_06 | z_107 | MLLT10, PIK3R1, ADGRB3, SLC25A13, LRRK1, DIP2A, PABPC1, HP1BP3 |  | MLLT10, ADGRB3, DIP2A |

## Predictor Jacobian Sensitivity

Both models show strong predictor sensitivity around lysosome/phagocytosis-annotated latent factors. That convergence suggests the Graph-JEPA predictor is routing disease-relevant information through phagocytic/lysosomal state axes rather than purely through generic donor or batch structure.

### upgrade_fine_08 Top Latent Edges

| source_latent_factor | target_latent_factor | mean_jacobian | source_annotation | target_annotation |
| --- | --- | --- | --- | --- |
| z_59 | z_91 | -2.8706 | lysosome_phagocytosis (-0.37) | lysosome_phagocytosis (+0.42) |
| z_87 | z_46 | -2.7039 | lysosome_phagocytosis (-0.42) | lysosome_phagocytosis (-0.37) |
| z_59 | z_5 | 2.6756 | lysosome_phagocytosis (-0.37) | lysosome_phagocytosis (+0.42) |
| z_87 | z_99 | 2.6397 | lysosome_phagocytosis (-0.42) | lysosome_phagocytosis (-0.41) |
| z_59 | z_87 | -2.6205 | lysosome_phagocytosis (-0.37) | lysosome_phagocytosis (-0.42) |
| z_59 | z_11 | 2.5774 | lysosome_phagocytosis (-0.37) | lysosome_phagocytosis (-0.33) |
| z_59 | z_63 | 2.5540 | lysosome_phagocytosis (-0.37) | lysosome_phagocytosis (-0.17) |
| z_59 | z_118 | 2.5039 | lysosome_phagocytosis (-0.37) | lysosome_phagocytosis (-0.39) |
| z_29 | z_63 | -2.4664 | lysosome_phagocytosis (-0.41) | lysosome_phagocytosis (-0.17) |
| z_59 | z_56 | -2.4339 | lysosome_phagocytosis (-0.37) | lysosome_phagocytosis (-0.40) |

### fine_bridge_06 Top Latent Edges

| source_latent_factor | target_latent_factor | mean_jacobian | source_annotation | target_annotation |
| --- | --- | --- | --- | --- |
| z_124 | z_99 | -0.9079 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (+0.43) |
| z_104 | z_99 | -0.8908 | lysosome_phagocytosis (+0.43) | lysosome_phagocytosis (+0.43) |
| z_59 | z_124 | 0.8632 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (-0.43) |
| z_59 | z_5 | 0.8513 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (-0.43) |
| z_104 | z_46 | 0.8309 | lysosome_phagocytosis (+0.43) | lysosome_phagocytosis (-0.43) |
| z_124 | z_46 | 0.8262 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (-0.43) |
| z_124 | z_17 | 0.8239 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (-0.43) |
| z_59 | z_118 | 0.7862 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (-0.43) |
| z_59 | z_63 | 0.7667 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (-0.43) |
| z_59 | z_70 | -0.7464 | lysosome_phagocytosis (-0.43) | lysosome_phagocytosis (+0.43) |

## Module Counterfactuals For AT8

Negative deltas mean the model's predicted AT8 burden moves down after the module is shifted toward the reference value. Positive deltas mean predicted AT8 moves up.

| module | n_genes_perturbed | mean_delta_raw_scale | median_delta_raw_scale | genes |
| --- | --- | --- | --- | --- |
| antigen_presentation | 10 | -0.0175 | -0.0153 | B2M;CD74;HLA-DPA1;HLA-DPB1;HLA-DQA1;HLA-DQB1;HLA-DRA;HLA-DRB1;TAP1;TAP2 |
| vascular_barrier_myeloid | 10 | -0.0157 | -0.0145 | C1QA;C1QB;C1QC;CD163;F13A1;LYVE1;MARCO;MERTK;MRC1;MSR1 |
| lipid_metabolism | 9 | 0.0138 | 0.0136 | ABCA1;ABCA7;APOE;CLU;LPL;MSR1;PLCG2;SORL1;TREM2 |
| homeostatic_microglia | 10 | 0.0124 | 0.0114 | CSF1R;CX3CR1;GPR34;HEXB;OLFML3;P2RY12;P2RY13;SALL1;SELPLG;TMEM119 |
| senescence_stress | 10 | 0.0119 | 0.0122 | CDKN1A;CDKN2A;DDIT3;FOS;GADD45A;HSP90AA1;HSPA1A;HSPA1B;JUN;SERPINE1 |
| inflammatory_signaling | 11 | -0.0094 | -0.0086 | CCL2;CCL3;CCL4;CXCL8;IL18;IL1B;IL27RA;IL6;NFKBIA;TNF;TNFRSF11B |
| complement | 9 | -0.0091 | -0.0081 | C1QA;C1QB;C1QC;C3;C4A;C4B;CFH;SERPING1;VSIG4 |
| lysosome_phagocytosis | 10 | 0.0070 | 0.0069 | CD68;CTSB;CTSD;CTSS;FCGR3A;LAMP1;LAMP2;LAPTM5;MERTK;NPC2 |
| plaque_response | 12 | -0.0050 | -0.0030 | APOE;AXL;CLEC7A;CST7;CTSD;GPNMB;ITGAX;LGALS3;LPL;SPP1;TREM2;TYROBP |
| disease_associated_microglia | 13 | -0.0041 | -0.0024 | APOE;AXL;CD9;CLEC7A;CST7;CTSD;GPNMB;ITGAX;LGALS3;LPL;SPP1;TREM2;TYROBP |

## Ranked Gene Target Matrix

The ranking combines counterfactual effect size, whether the gene appears in decoded latent axes, cross-model support from `fine_bridge_06`, and HPA actionability flags.

| gene | module | upgrade_best_latent | upgrade_best_rank | bridge_best_latent | bridge_best_rank | mean_delta_raw_scale | abs_mean_delta_raw_scale | direction | druggability_evidence | cross_model_support | evidence_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APP | unannotated | z_71 | 105 | z_30 | 7 | 0.0129 | 0.0129 | AT8-up when perturbed | HPA/FDA drug target; predicted membrane; predicted secreted | also decoded in fine_bridge_06 | 2.9583 |
| BCL2 | unannotated | z_30 | 1 | z_120 | 1 | 0.0049 | 0.0049 | AT8-up when perturbed | HPA/FDA drug target; predicted membrane | also decoded in fine_bridge_06 | 2.5000 |
| TLR2 | unannotated | z_125 | 9 | z_125 | 1 | -0.0030 | 0.0030 | AT8-down when perturbed | HPA/FDA drug target; predicted membrane | also decoded in fine_bridge_06 | 2.4167 |
| CD4 | unannotated | z_71 | 8 | z_26 | 10 | -0.0026 | 0.0026 | AT8-down when perturbed | HPA/FDA drug target; predicted membrane | also decoded in fine_bridge_06 | 2.3750 |
| P2RY12 | homeostatic_microglia | z_1 | 9 | z_125 | 29 | 0.0020 | 0.0020 | AT8-up when perturbed | HPA/FDA drug target; predicted membrane | also decoded in fine_bridge_06 | 2.2500 |
| APOE | disease_associated_microglia;lipid_metabolism;plaque_response | z_30 | 169 | z_57 | 3 | 0.0063 | 0.0063 | AT8-up when perturbed | predicted secreted | also decoded in fine_bridge_06 | 2.1250 |
| MAPK1 | unannotated | z_30 | 10 | z_94 | 4 | 0.0025 | 0.0025 | AT8-up when perturbed | HPA/FDA drug target | also decoded in fine_bridge_06 | 2.0833 |
| CX3CR1 | chemokine_migration;homeostatic_microglia;synapse_pruning | z_94 | 154 | z_107 | 261 | 0.0050 | 0.0050 | AT8-up when perturbed | predicted membrane | also decoded in fine_bridge_06 | 2.0417 |
| STAT3 | unannotated | z_57 | 4 | z_125 | 4 | 0.0171 | 0.0171 | AT8-up when perturbed | no HPA actionability flag | also decoded in fine_bridge_06 | 2.0000 |
| CSF1R | homeostatic_microglia | z_100 | 1 | z_63 | 7 | 0.0009 | 0.0009 | AT8-up when perturbed | HPA/FDA drug target; predicted membrane | also decoded in fine_bridge_06 | 2.0000 |
| UGCG | unannotated | z_100 | 88 | z_94 | 10 | 0.0008 | 0.0008 | AT8-up when perturbed | HPA/FDA drug target; predicted membrane | also decoded in fine_bridge_06 | 1.9583 |
| ROCK1 | unannotated | z_100 | 6 | z_120 | 6 | -0.0019 | 0.0019 | AT8-down when perturbed | HPA/FDA drug target | also decoded in fine_bridge_06 | 1.9583 |
| GRB2 | unannotated | z_120 | 1 | z_94 | 1 | 0.0063 | 0.0063 | AT8-up when perturbed | no HPA actionability flag | also decoded in fine_bridge_06 | 1.9167 |
| F13A1 | vascular_barrier_myeloid | z_71 | 1548 | z_26 | 1674 | 0.0008 | 0.0008 | AT8-up when perturbed | HPA/FDA drug target; predicted secreted | also decoded in fine_bridge_06 | 1.9167 |
| HSP90AA1 | senescence_stress | z_38 | 3 | z_103 | 6 | 0.0058 | 0.0058 | AT8-up when perturbed | no HPA actionability flag | also decoded in fine_bridge_06 | 1.8333 |
| CD74 | antigen_presentation | z_57 | 27 | z_94 | 3 | 0.0012 | 0.0012 | AT8-up when perturbed | predicted membrane; predicted secreted | also decoded in fine_bridge_06 | 1.8333 |
| PTPRG | at8_associated_first_pass | z_107 | 996 | z_71 | 2150 | -0.0025 | 0.0025 | AT8-down when perturbed | predicted membrane | also decoded in fine_bridge_06 | 1.7917 |
| HIF1A | unannotated | z_94 | 2 | z_71 | 2 | 0.0041 | 0.0041 | AT8-up when perturbed | no HPA actionability flag | also decoded in fine_bridge_06 | 1.7083 |
| P2RY13 | homeostatic_microglia | z_63 | 1388 | z_57 | 1657 | -0.0017 | 0.0017 | AT8-down when perturbed | predicted membrane | also decoded in fine_bridge_06 | 1.6667 |
| CTSD | at8_associated_first_pass;disease_associated_microglia;lysosome_phagocytosis;plaque_response | z_107 | 343 | z_71 | 330 | 0.0012 | 0.0012 | AT8-up when perturbed | predicted secreted | also decoded in fine_bridge_06 | 1.5417 |

## Working Biological Hypotheses

1. Antigen-presentation and vascular/barrier myeloid programs are the strongest AT8-lowering module-level counterfactuals in `upgrade_fine_08`.
2. Lysosome/phagocytosis is the most stable predictor-Jacobian routing signal across both v2.1 and bridge checkpoints.
3. STAT3, APP, GRB2, APOE, HSP90AA1, CX3CR1, BCL2, and HIF1A are the largest AT8-up single-gene perturbation responses in the current screen.
4. TLR2, CD4, PTPRG, ROCK1, and P2RY13 show AT8-down perturbation direction in the current screen and should be treated as candidate intervention hypotheses.
5. The model now produces coherent biology. Further tuning should pause unless independent validation or a new target metric shows that the biological ranking is unstable.

## Next Validation Step

The next best scientific step is not more architecture tuning. It is testing whether the same ranked modules and genes reproduce in an independent AD/control or perturbation dataset, while keeping the SEA-AD-trained encoder frozen.
