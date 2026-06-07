# v2.1 Multi-Target Counterfactual Stability

This summary compares the same Graph-JEPA v2.1 digital perturbations across AT8/pTau, A beta/6e10, GFAP, Iba1, and NeuN. Effects are model-implied prediction shifts, not validated causal effects.

## Module-Level Stability

| module | n_targets | n_targets_up | n_targets_down | mean_abs_delta | max_abs_delta | strongest_target | strongest_delta | AT8_delta | A_beta_6e10_delta | GFAP_delta | Iba1_delta | NeuN_delta | effect_signature |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lysosome_phagocytosis | 5 | 4 | 1 | 0.0483 | 0.0923 | NeuN | 0.0923 | 0.0070 | -0.0213 | 0.0829 | 0.0380 | 0.0923 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| homeostatic_microglia | 5 | 4 | 1 | 0.0415 | 0.0975 | GFAP | 0.0975 | 0.0124 | -0.0077 | 0.0975 | 0.0280 | 0.0621 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| plaque_response | 5 | 3 | 2 | 0.0394 | 0.0867 | NeuN | 0.0867 | -0.0050 | -0.0306 | 0.0479 | 0.0270 | 0.0867 | A beta/6e10:down; AT8/pTau:down; GFAP:up; Iba1:up; NeuN:up |
| disease_associated_microglia | 5 | 3 | 2 | 0.0393 | 0.0858 | NeuN | 0.0858 | -0.0041 | -0.0295 | 0.0498 | 0.0275 | 0.0858 | A beta/6e10:down; AT8/pTau:down; GFAP:up; Iba1:up; NeuN:up |
| lipid_metabolism | 5 | 4 | 1 | 0.0362 | 0.0785 | GFAP | 0.0785 | 0.0138 | -0.0018 | 0.0785 | 0.0349 | 0.0519 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| senescence_stress | 5 | 4 | 1 | 0.0348 | 0.0659 | NeuN | 0.0659 | 0.0119 | -0.0097 | 0.0636 | 0.0227 | 0.0659 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| antigen_presentation | 5 | 3 | 2 | 0.0338 | 0.0806 | NeuN | 0.0806 | -0.0175 | -0.0361 | 0.0241 | 0.0108 | 0.0806 | A beta/6e10:down; AT8/pTau:down; GFAP:up; Iba1:up; NeuN:up |
| vascular_barrier_myeloid | 5 | 3 | 2 | 0.0266 | 0.0610 | NeuN | 0.0610 | -0.0157 | -0.0289 | 0.0125 | 0.0148 | 0.0610 | A beta/6e10:down; AT8/pTau:down; GFAP:up; Iba1:up; NeuN:up |
| complement | 5 | 2 | 3 | 0.0201 | 0.0435 | NeuN | 0.0435 | -0.0091 | -0.0214 | -0.0099 | 0.0164 | 0.0435 | A beta/6e10:down; AT8/pTau:down; GFAP:down; Iba1:up; NeuN:up |
| inflammatory_signaling | 5 | 1 | 4 | 0.0096 | 0.0202 | NeuN | 0.0202 | -0.0094 | -0.0150 | -0.0029 | -0.0005 | 0.0202 | A beta/6e10:down; AT8/pTau:down; GFAP:down; Iba1:down; NeuN:up |

## Gene-Level Stability

| perturbation | n_targets | n_targets_up | n_targets_down | mean_abs_delta | max_abs_delta | strongest_target | strongest_delta | AT8_delta | A_beta_6e10_delta | GFAP_delta | Iba1_delta | NeuN_delta | effect_signature |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APP | 5 | 4 | 1 | 0.0270 | 0.0626 | GFAP | 0.0626 | 0.0129 | -0.0012 | 0.0626 | 0.0192 | 0.0391 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| STAT3 | 5 | 5 | 0 | 0.0255 | 0.0642 | GFAP | 0.0642 | 0.0171 | 0.0045 | 0.0642 | 0.0146 | 0.0270 | A beta/6e10:up; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| GRB2 | 5 | 4 | 1 | 0.0170 | 0.0369 | GFAP | 0.0369 | 0.0063 | -0.0015 | 0.0369 | 0.0147 | 0.0257 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| HSP90AA1 | 5 | 4 | 1 | 0.0165 | 0.0332 | NeuN | 0.0332 | 0.0058 | -0.0068 | 0.0285 | 0.0083 | 0.0332 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| BCL2 | 5 | 4 | 1 | 0.0146 | 0.0278 | GFAP | 0.0278 | 0.0049 | -0.0023 | 0.0278 | 0.0133 | 0.0246 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| HIF1A | 5 | 4 | 1 | 0.0139 | 0.0347 | GFAP | 0.0347 | 0.0041 | -0.0025 | 0.0347 | 0.0094 | 0.0190 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| MAPK1 | 5 | 4 | 1 | 0.0124 | 0.0227 | NeuN | 0.0227 | 0.0025 | -0.0039 | 0.0223 | 0.0104 | 0.0227 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| APOE | 5 | 5 | 0 | 0.0105 | 0.0200 | GFAP | 0.0200 | 0.0063 | 0.0037 | 0.0200 | 0.0154 | 0.0070 | A beta/6e10:up; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| RHOA | 5 | 4 | 1 | 0.0101 | 0.0193 | NeuN | -0.0193 | 0.0014 | 0.0118 | 0.0110 | 0.0070 | -0.0193 | A beta/6e10:up; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:down |
| CTSD | 5 | 3 | 2 | 0.0099 | 0.0246 | NeuN | 0.0246 | 0.0012 | -0.0074 | 0.0147 | -0.0017 | 0.0246 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:down; NeuN:up |
| CX3CR1 | 5 | 4 | 1 | 0.0092 | 0.0221 | GFAP | 0.0221 | 0.0050 | -0.0002 | 0.0221 | 0.0042 | 0.0147 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| CD4 | 5 | 3 | 2 | 0.0086 | 0.0193 | NeuN | 0.0193 | -0.0026 | -0.0072 | 0.0119 | 0.0022 | 0.0193 | A beta/6e10:down; AT8/pTau:down; GFAP:up; Iba1:up; NeuN:up |
| TLR2 | 5 | 3 | 2 | 0.0084 | 0.0165 | GFAP | 0.0165 | -0.0030 | -0.0042 | 0.0165 | 0.0083 | 0.0101 | A beta/6e10:down; AT8/pTau:down; GFAP:up; Iba1:up; NeuN:up |
| CD74 | 5 | 4 | 1 | 0.0068 | 0.0140 | GFAP | 0.0140 | 0.0012 | -0.0013 | 0.0140 | 0.0066 | 0.0109 | A beta/6e10:down; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |
| P2RY12 | 5 | 5 | 0 | 0.0066 | 0.0178 | GFAP | 0.0178 | 0.0020 | 0.0007 | 0.0178 | 0.0063 | 0.0059 | A beta/6e10:up; AT8/pTau:up; GFAP:up; Iba1:up; NeuN:up |

## Interpretation

- A module/gene with the same sign across many targets is likely a broad tissue-state axis.
- A module/gene with opposite signs across targets may separate amyloid/tau burden from gliosis, microglial activation, or neuronal-density readouts.
- NeuN should be interpreted carefully: positive NeuN deltas mean the model predicts higher neuronal marker area after the perturbation.