# SEA-AD JEPA v1 Biological Hypothesis Report

This report extracts the biology that the current SEA-AD JEPA v1 model appears to rely on when predicting neuropathology from Microglia-PVM expression. These are model-implied hypotheses, not experimental proof of causality.

## Core Interpretation Boundary

- Association means a gene, module, or latent factor tracks pathology in the observed SEA-AD cohort.
- Prediction means the representation improves held-out pathology ranking or neighborhood structure.
- Digital knockout means the trained model changes its prediction after an in-silico perturbation.
- Causal validation requires an external perturbation experiment, such as CRISPRi, CRISPR knockout, or drug response.

## Key Latent Finding: jepa_63

`jepa_63` is the strongest latent coefficient for AT8/pTau in the current pathology-weight table.

| Target | Mean coefficient | Std. coefficient | Interpretation |
|---|---:|---:|---|
| AT8 / pTau | -0.118 | 0.023 | Lower `jepa_63` is associated with higher model-predicted AT8 burden. |
| NeuN | -0.055 | 0.020 | Lower `jepa_63` is also associated with higher model-predicted NeuN signal in this head, making this factor pleiotropic rather than AT8-only. |

Top module annotations for `jepa_63`:

| Module | Correlation |
|---|---:|
| complement | +0.386 |
| antigen_presentation | +0.342 |
| synapse_pruning | +0.336 |

Top directed latent Jacobian edges involving `jepa_63`:

| Source | Target | Mean Jacobian | Source annotation | Target annotation |
|---:|---:|---:|---|---|
| 63 | 89 | -0.050 | complement (+0.39) | complement (-0.38) |
| 75 | 63 | +0.049 | vascular_barrier_myeloid (-0.29) | complement (+0.39) |
| 64 | 63 | +0.044 | homeostatic_microglia (+0.50) | complement (+0.39) |

Working interpretation: `jepa_63` looks like a complement/antigen-presentation/synapse-pruning axis that the model uses when ranking tau pathology and neuronal marker readouts. This should be treated as a candidate microglial immune-state axis for follow-up, not as a named biological pathway yet.

## Strongest AT8 Gene-Level Hypotheses

Negative digital-knockout deltas mean that reducing that gene in-silico lowers the model's AT8 prediction. The confounder-adjusted partial Spearman column asks whether the gene still tracks AT8 after adjusting for donor-level covariates included in the current workflow.

| Gene | Module | Knockout delta | Confounder partial Spearman | Adjusted slope |
|---|---|---:|---:|---:|
| CHI3L1 | at8_associated_first_pass | -0.0043 | +0.416 | +4.047 |
| PTPRG | at8_associated_first_pass | -0.0047 | +0.355 | +1.893 |
| NFKBIA | at8_associated_first_pass; inflammatory_signaling | -0.0010 | +0.349 | +6.193 |
| S100A4 | at8_associated_first_pass | -0.0018 | +0.333 | +9.556 |
| TNFRSF11B | at8_associated_first_pass; inflammatory_signaling | -0.0012 | +0.306 | +10.498 |
| DRAM1 | at8_associated_first_pass | -0.0023 | +0.281 | +4.377 |
| P2RY12 | homeostatic_microglia | -0.0023 | -0.153 | -1.054 |
| MRC1 | vascular_barrier_myeloid | -0.0036 | -0.137 | -1.101 |
| MSR1 | vascular_barrier_myeloid | -0.0014 | -0.081 | -0.511 |
| CTSD | at8_associated_first_pass | -0.0025 | +0.040 | +0.275 |

The most direct v1 AT8-reduction hypotheses are therefore centered on the AT8-associated first-pass genes, especially PTPRG, CHI3L1, NFKBIA, S100A4, TNFRSF11B, DRAM1, CTSD, and P2RY12. Several of these survive confounder-adjusted association, but this still does not prove that perturbing them will reduce tau pathology in a biological system.

## Module-Level Hypotheses

| Module | Global-mean knockout delta | Zero/mean sign-stable | Max absolute delta | Confounder partial Spearman |
|---|---:|---|---:|---:|
| at8_associated_first_pass | -0.0024 | True | 0.0214 | +0.441 |
| interferon_response | +0.0005 | True | 0.0030 | -0.026 |
| senescence_stress | +0.0003 | True | 0.0016 | +0.106 |
| lysosome_phagocytosis | +0.0002 | False | 0.0182 | -0.154 |
| disease_associated_microglia | +0.0006 | False | 0.0141 | -0.124 |
| plaque_response | +0.0006 | False | 0.0135 | -0.129 |
| vascular_barrier_myeloid | +0.0017 | False | 0.0115 | -0.282 |
| lipid_metabolism | +0.0008 | False | 0.0102 | -0.314 |
| homeostatic_microglia | -0.0004 | False | 0.0093 | -0.049 |
| antigen_presentation | +0.0007 | False | 0.0092 | -0.115 |

The AT8-associated first-pass module is the cleanest model-implied AT8-lowering module under multiple intervention styles. Vascular/barrier, lipid, complement, and synapse-pruning modules are also repeatedly implicated, but their sign can depend on the intervention definition. That sign sensitivity is biologically important: these modules may represent tissue context, resilience, or mixed cell-state programs rather than simple one-directional disease drivers.

## Three Concrete v1 Hypotheses

1. **AT8-linked inflammatory/stress program.** The model predicts lower AT8 when the AT8-associated first-pass gene set is perturbed, with strong individual signals for PTPRG, CHI3L1, NFKBIA, S100A4, TNFRSF11B, DRAM1, CTSD, and P2RY12. Validation path: test whether these markers spatially enrich near AT8-positive regions and whether their perturbation changes tau-associated microglial states in an iPSC-microglia system.

2. **Complement/synapse-pruning latent axis.** `jepa_63` links AT8 prediction to complement, antigen presentation, and synapse-pruning annotations. Validation path: map `jepa_63`-high and `jepa_63`-low donors/cells to C1QA/C1QB/C1QC, HLA genes, synaptic pruning markers, and AT8 burden.

3. **Vascular/barrier and lipid context as modifiers.** Vascular/barrier and lipid/complement modules have strong confounder-adjusted relationships, but their counterfactual signs are not always simple. Validation path: treat these as context-modifier hypotheses and test them against vascular adjacency, plaque proximity, and APOE/TREM2/LPL-associated microglial states rather than expecting a single monotonic knockout effect.

## Next Biological Checks

- Plot `jepa_63` across donors and color by AT8, NeuN, and disease progression.
- Extract top genes correlated with `jepa_63` directly from cell-level expression, not only curated module annotations.
- Re-run the gene/module reports for Abeta/6e10, GFAP, Iba1, and NeuN to find stable multi-pathology modules.
- Treat Kampmann/iPSC-microglia CRISPRi as external stress testing, while reserving SEA-AD internal reports for AD-specific hypothesis generation.
