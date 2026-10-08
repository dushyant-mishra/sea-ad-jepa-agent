# Discovery Scorecard v2: Graph-Connected Feature-Wide

## Classification Counts

| class | count |
| --- | ---: |
| mixed_or_unclear | 1,925 |
| neuron_risk | 267 |
| amyloid_lowering_candidate | 153 |
| gliosis_inflating | 152 |
| broad_reactive_state_shift | 80 |
| tau_lowering_neuron_preserving | 58 |
| dual_pathology_lowering_neuron_preserving | 41 |

## Large Movers With Broad-State or Gliosis Penalties

| gene | pathology_axis_class | AT8_delta | A_beta_6e10_delta | NeuN_delta | gliosis_penalty | broad_shift_score | therapeutic_like_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RC3H1 | broad_reactive_state_shift | -0.61896 | -1.0344 | 0.35578 | 1.0466 | 0.69085 | -0.071847 |
| WAPL | broad_reactive_state_shift | 0.25063 | 0.76474 | 0.57796 | 0.34695 | 0.45417 | -0.019623 |
| PHKB | broad_reactive_state_shift | 0.11362 | 0.29459 | 0.24041 | 1.1212 | 0.35397 | -0.99442 |
| HDAC8 | neuron_risk | -0.25491 | -0.2197 | -0.14522 | 1.0203 | 0.32802 | -0.91058 |
| PAFAH1B1 | broad_reactive_state_shift | -0.34532 | -0.53267 | 0.15206 | 0.39442 | 0.29816 | 0.10296 |
| PPP2R5E | neuron_risk | -0.10577 | -0.2634 | -0.049945 | 0.46393 | 0.27329 | -0.4081 |
| DLG1 | broad_reactive_state_shift | -0.22393 | -0.24187 | 0.093892 | 0.70335 | 0.25261 | -0.38553 |
| POLK | broad_reactive_state_shift | -0.093493 | -0.024883 | 0.12625 | 0.65961 | 0.18085 | -0.43988 |
| SMG1 | broad_reactive_state_shift | -0.067739 | 0.056889 | 0.17614 | 0.58147 | 0.17645 | -0.33759 |
| BRAF | mixed_or_unclear | 0.30658 | 0.12351 | 0.38023 | 0.017631 | 0.17068 | 0.056021 |
| HELZ | broad_reactive_state_shift | 0.0043603 | -0.35625 | 0.0031955 | 0.094615 | 0.1663 | -0.09578 |
| ANKHD1 | broad_reactive_state_shift | -0.032945 | -0.22301 | 0.083617 | 0.42851 | 0.16249 | -0.31195 |
| TMEM131 | broad_reactive_state_shift | 0.16572 | 0.081669 | 0.17535 | 0.37018 | 0.15858 | -0.36055 |
| SFSWAP | broad_reactive_state_shift | 0.0045583 | 0.054294 | 0.15454 | 0.27211 | 0.12674 | -0.12213 |
| TRPM7 | broad_reactive_state_shift | 0.046474 | 0.067516 | 0.098176 | 0.38626 | 0.11969 | -0.33456 |

These genes are separated from cleaner candidates because a large favorable pathology delta can coexist with broad-state movement or gliosis inflation.

## Cleaner Therapeutic-Like Movers

| gene | pathology_axis_class | AT8_delta | A_beta_6e10_delta | NeuN_delta | gliosis_penalty | broad_shift_score | therapeutic_like_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UGCG | dual_pathology_lowering_neuron_preserving | -0.033569 | -0.037101 | 0.039379 | 0.0062662 | 0.023263 | 0.066682 |
| SLC38A9 | tau_lowering_neuron_preserving | -0.034169 | -0.026914 | 0.016063 | 0 | 0.024114 | 0.050232 |
| MDM2 | tau_lowering_neuron_preserving | -0.03955 | -0.0037694 | 0.022934 | 0.013295 | 0.015909 | 0.049188 |
| SMARCA4 | dual_pathology_lowering_neuron_preserving | -0.025458 | -0.029959 | 0.030355 | 0.0080957 | 0.019456 | 0.047717 |
| AP1G1 | dual_pathology_lowering_neuron_preserving | -0.014609 | -0.034269 | 0.032152 | 0 | 0.022866 | 0.04676 |
| TLR2 | tau_lowering_neuron_preserving | -0.026138 | -0.018714 | 0.027924 | 0.0078425 | 0.017448 | 0.04622 |
| NEMF | tau_lowering_neuron_preserving | -0.037903 | -0.02555 | 0.0073523 | 0 | 0.024046 | 0.045256 |
| BAZ1A | dual_pathology_lowering_neuron_preserving | -0.021715 | -0.031154 | 0.019613 | 0 | 0.02491 | 0.041328 |
| GMDS | tau_lowering_neuron_preserving | -0.024096 | -0.026406 | 0.016327 | 0 | 0.023586 | 0.040423 |
| BTBD9 | tau_lowering_neuron_preserving | -0.019727 | -0.018971 | 0.020459 | 0 | 0.021335 | 0.040186 |
| ARHGEF7 | tau_lowering_neuron_preserving | -0.020614 | -0.016759 | 0.019146 | 0 | 0.013716 | 0.03976 |
| LRCH3 | tau_lowering_neuron_preserving | -0.026325 | -0.024659 | 0.019727 | 0.0063388 | 0.019514 | 0.039713 |
| KIF1B | tau_lowering_neuron_preserving | -0.032261 | 0.012148 | 0.0070645 | 0 | 0.012855 | 0.039325 |
| RAD51B | tau_lowering_neuron_preserving | -0.022516 | -0.011104 | 0.016497 | 0 | 0.016088 | 0.039014 |
| PI4KA | tau_lowering_neuron_preserving | -0.014171 | -0.0039073 | 0.024364 | 0 | 0.012186 | 0.038535 |

This is a ranking category, not evidence of therapeutic efficacy or causal biology.

## Named Mover Audit

| gene | named_review_group | named_review_support | pathology_axis_class | movement_profile | AT8_delta | NeuN_delta | gliosis_penalty | broad_shift_score | therapeutic_like_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SLAIN2 | proposed_cleaner_mover_audit | not_supported_by_current_v2_profile | amyloid_lowering_candidate | large_mover_with_broad_or_gliosis_penalty | -0.050297 | 0.066313 | 0.0081465 | 0.047072 | 0.10846 |
| FIP1L1 | proposed_cleaner_mover_audit | not_supported_by_current_v2_profile | amyloid_lowering_candidate | large_mover_with_broad_or_gliosis_penalty | -0.058939 | 0.038035 | 0.019978 | 0.039952 | 0.076996 |
| ERC1 | proposed_cleaner_mover_audit | not_supported_by_current_v2_profile | amyloid_lowering_candidate | large_mover_with_broad_or_gliosis_penalty | -0.05535 | 0.011773 | 0 | 0.069723 | 0.067123 |
| KIF2A | proposed_cleaner_mover_audit | not_supported_by_current_v2_profile | amyloid_lowering_candidate | large_mover_with_broad_or_gliosis_penalty | -0.046697 | 0.027498 | 0.014859 | 0.037328 | 0.059336 |
| PTPN18 | proposed_cleaner_mover_audit | not_supported_by_current_v2_profile | dual_pathology_lowering_neuron_preserving | other_or_unresolved | -0.046942 | 0.012767 | 0.018736 | 0.023962 | 0.040973 |
| PAFAH1B1 | proposed_large_mover_audit | supported_by_current_v2_profile | broad_reactive_state_shift | large_mover_with_broad_or_gliosis_penalty | -0.34532 | 0.15206 | 0.39442 | 0.29816 | 0.10296 |
| RC3H1 | proposed_large_mover_audit | supported_by_current_v2_profile | broad_reactive_state_shift | large_mover_with_broad_or_gliosis_penalty | -0.61896 | 0.35578 | 1.0466 | 0.69085 | -0.071847 |
| DLG1 | proposed_large_mover_audit | supported_by_current_v2_profile | broad_reactive_state_shift | large_mover_with_broad_or_gliosis_penalty | -0.22393 | 0.093892 | 0.70335 | 0.25261 | -0.38553 |

The proposed cleaner-mover examples are retained as an explicit audit set. They are not promoted when their full-universe percentiles indicate broad-state or gliosis spillover.

## Prior Candidate Screen Genes

| gene | pathology_axis_class | AT8_delta | A_beta_6e10_delta | NeuN_delta | gliosis_penalty | broad_shift_score | therapeutic_like_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UGCG | dual_pathology_lowering_neuron_preserving | -0.033569 | -0.037101 | 0.039379 | 0.0062662 | 0.023263 | 0.066682 |
| TLR2 | tau_lowering_neuron_preserving | -0.026138 | -0.018714 | 0.027924 | 0.0078425 | 0.017448 | 0.04622 |
| CD4 | amyloid_lowering_candidate | -0.027316 | -0.046484 | 0.016868 | 0.02933 | 0.02751 | 0.014854 |
| CSF1R | mixed_or_unclear | -0.02801 | -0.0263 | -0.010465 | 0.028344 | 0.02022 | -0.010799 |
| APOE | broad_reactive_state_shift | -0.035331 | -0.053681 | 0.0037983 | 0.050222 | 0.035052 | -0.011093 |
| ROCK1 | mixed_or_unclear | -0.01206 | -0.020009 | 0.0023291 | 0.026911 | 0.012262 | -0.012521 |
| BCL2 | amyloid_lowering_candidate | -0.010626 | -0.032751 | -0.0099861 | 0.021472 | 0.014967 | -0.020832 |
| CX3CR1 | mixed_or_unclear | 0.00019749 | -0.01549 | 0.012123 | 0.049242 | 0.016764 | -0.037316 |
| STAT3 | neuron_risk | -0.024383 | -0.013964 | -0.032165 | 0.080931 | 0.051036 | -0.088713 |
| MAPK1 | neuron_risk | -0.014351 | -0.083936 | -0.02705 | 0.10328 | 0.062321 | -0.11598 |
| P2RY12 | gliosis_inflating | 0.034703 | 0.029033 | -0.0082981 | 0.07773 | 0.029953 | -0.12073 |
| APP | broad_reactive_state_shift | -0.034901 | -0.01589 | 0.023161 | 0.19593 | 0.053977 | -0.13787 |

## Amyloid Selectivity Rule

`amyloid_selective_stringent_flag` is true only for top-5% amyloid lowering with low gliosis and broad-shift spillover and limited AT8 movement. The main conservative class remains `amyloid_lowering_candidate`; no stronger biological conclusion is implied.

## Boundary

The graph-connected feature-wide run is used for pathology-delta ranking and null calibration. Nearest-neighbor manifold safety was not computed in the full run due to the Windows sklearn/threadpoolctl issue. Manifold-verified evidence comes from the successful pilot and any later targeted top-hit audits.

Biological conclusions should not be rewritten until scorecard-v2 negative controls are complete.
