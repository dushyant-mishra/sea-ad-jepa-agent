# Stage74 directed Micro-PVM GRN in-silico perturbation audit

## Decision audit

| directed_graph_organization_pass | ablation_stability_pass | ablation_control_specificity_pass | biological_coherence_pass | candidate_prioritization_pass | causal_validation_pass | prediction_benchmark_updated | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | False | False | directed perturbation hypotheses only; not causal knockout validation |

## Top regulator priority rows

| regulator | mean_directed_abs_delta | mean_delta_vs_expression_only | mean_delta_vs_reversed | mean_delta_vs_target_shuffled | mean_delta_vs_random | n_regions | n_direct_targets | median_edge_weight | median_abs_rho | control_specificity_score | candidate_for_followup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IRF8 | 0.0313052 | 0.0313052 | 0.0313052 | 0.00693396 | 0.0106683 | 2 | 22 | 0.955 | 0.411765 | 0.0200532 | True |
| STAT1 | 0.0309335 | 0.0309335 | 0.0309335 | 0.00239822 | 0.00576747 | 2 | 27 | 0.95 | 0.434469 | 0.0175082 | True |
| ELF1 | 0.0537613 | 0.0537613 |  | 0.0129609 | 0.00494198 | 2 | 33 | 1 | 0.655315 | 0.023888 | False |
| RELA | 0.0421091 | 0.04328 |  | 0.0120395 | 0.0122058 | 2 | 30 | 0.965 | 0.442724 | 0.0225084 | False |
| BACH1 | 0.0480018 | 0.0480018 |  | 0.0094428 | 0.00835965 | 2 | 29 | 0.99 | 0.595459 | 0.0219348 | False |
| NRF1 | 0.0540168 | 0.0540168 |  | 0.00410123 | 0.00382478 | 2 | 29 | 1 | 0.702786 | 0.0206476 | False |
| SPI1 | 0.0538313 | 0.0538313 |  | 0.00289639 | 0.00257326 | 2 | 32 | 1 | 0.667699 | 0.019767 | False |
| CEBPA | 0.0315941 | 0.0322246 |  | 0.0116406 | 0.00828276 | 2 | 19 | 0.95 | 0.420021 | 0.0173826 | False |
| STAT3 | 0.0433007 | 0.0433007 |  | 0.00843467 | 0.000204815 | 2 | 31 | 0.995 | 0.585139 | 0.0173134 | False |
| MITF | 0.0299518 | 0.0299518 |  | 0.0102918 | 0.00970256 | 2 | 26 | 0.9325 | 0.378741 | 0.0166487 | False |
| NFKB1 | 0.0487244 | 0.0487244 |  | 0.000353019 | 0.000205424 | 2 | 31 | 0.995 | 0.630547 | 0.0164276 | False |
| CEBPB | 0.047125 | 0.047125 |  | -0.00569525 | -0.00224112 | 2 | 30 | 0.995 | 0.631579 | 0.0130629 | False |
| PPARG | 0.0419597 | 0.0419597 |  | -0.0127368 | 0.00796274 | 2 | 29 | 0.99 | 0.535604 | 0.0123952 | False |
| MAFB | 0.0280121 | 0.0280121 |  | 0.00302812 | 0.004875 | 2 | 27 | 0.96 | 0.436533 | 0.0119717 | False |
| MAF | 0.0235454 | 0.0235454 |  | 0.000356051 | 0.00691944 | 2 | 24 | 0.92 | 0.377709 | 0.0102736 | False |
| NFE2L2 | 0.044712 | 0.044712 |  | -0.0143411 | -0.000956708 | 2 | 30 | 0.9925 | 0.596491 | 0.00980472 | False |
| ETS1 | 0.0138968 | 0.0138031 |  | 0.00770027 | 0.00513136 | 2 | 15 | 0.885 | 0.261094 | 0.00887825 | False |
| SREBF1 | 0.0304541 | 0.0283609 |  | -0.011529 | 0.00628892 | 2 | 32 | 0.96 | 0.436533 | 0.00770695 | False |
| JUN | 0.0170281 | 0.0165707 |  | 0.00338567 | -0.000355095 | 2 | 14 | 0.905 | 0.312693 | 0.00653375 | False |
| RUNX1 | 0.0382174 | 0.0367578 |  | -0.0207974 | -0.000434035 | 2 | 27 | 0.985 | 0.587203 | 0.00517545 | False |

_Showing 20 of 21 rows._

## Control specificity

| dataset | regulator | degree_matched_random_directed | directed_stage72b | expression_only | reversed_directed | target_shuffled_directed | directed_minus_expression_only | directed_minus_reversed | directed_minus_target_shuffled | directed_minus_random |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DLPFC | ELF1 | 0.0486561 | 0.0589526 | 0 |  | 0.0358681 | 0.0589526 |  | 0.0230845 | 0.0102965 |
| MTG | STAT3 | 0.0442508 | 0.044271 | 0 |  | 0.0290697 | 0.044271 |  | 0.0152013 | 2.01642e-05 |
| MTG | RELA | 0.035032 | 0.0409381 |  |  | 0.0267203 |  |  | 0.0142178 | 0.00590611 |
| DLPFC | MITF | 0.0212124 | 0.0326488 | 0 |  | 0.0192194 | 0.0326488 |  | 0.0134294 | 0.0114363 |
| MTG | BACH1 | 0.03916 | 0.046179 | 0 |  | 0.0334151 | 0.046179 |  | 0.0127638 | 0.00701893 |
| MTG | CEBPA | 0.0195209 | 0.0309637 |  |  | 0.0184318 |  |  | 0.0125319 | 0.0114428 |
| DLPFC | CEBPA | 0.0271018 | 0.0322246 | 0 |  | 0.0214754 | 0.0322246 |  | 0.0107492 | 0.00512276 |
| DLPFC | RELA | 0.0247746 | 0.04328 | 0 |  | 0.0334189 | 0.04328 |  | 0.00986115 | 0.0185054 |
| DLPFC | IRF8 | 0.026564 | 0.0345561 | 0 | 0 | 0.0252493 | 0.0345561 | 0.0345561 | 0.00930676 | 0.00799206 |
| MTG | ETS1 | 0.00808643 | 0.0139906 |  |  | 0.00544335 |  |  | 0.00854723 | 0.00590415 |
| MTG | STAT1 | 0.0252118 | 0.0325694 | 0 | 0 | 0.0250391 | 0.0325694 | 0.0325694 | 0.00753027 | 0.00735757 |
| MTG | MITF | 0.019286 | 0.0272548 | 0 |  | 0.0201005 | 0.0272548 |  | 0.0071543 | 0.0079688 |
| DLPFC | ETS1 | 0.00944454 | 0.0138031 | 0 |  | 0.00694979 | 0.0138031 |  | 0.00685332 | 0.00435857 |
| DLPFC | BACH1 | 0.0401243 | 0.0498247 | 0 |  | 0.0437029 | 0.0498247 |  | 0.00612176 | 0.00970037 |
| MTG | NRF1 | 0.0490629 | 0.049191 | 0 |  | 0.0432019 | 0.049191 |  | 0.00598914 | 0.000128101 |
| MTG | MAFB | 0.023676 | 0.0302004 | 0 |  | 0.0254623 | 0.0302004 |  | 0.00473817 | 0.00652439 |
| MTG | IRF8 | 0.0147098 | 0.0280543 | 0 | 0 | 0.0234932 | 0.0280543 | 0.0280543 | 0.00456115 | 0.0133445 |
| MTG | JUN | 0.0156869 | 0.0174856 |  |  | 0.0131078 |  |  | 0.00437781 | 0.00179877 |
| MTG | SPI1 | 0.0485334 | 0.0510861 | 0 |  | 0.0471379 | 0.0510861 |  | 0.00394817 | 0.00255269 |
| DLPFC | FOS | 0.00452241 | 0.00640549 | 0 |  | 0.00256326 | 0.00640549 |  | 0.00384223 | 0.00188308 |

_Showing 20 of 42 rows._

## Claim boundary

| stage74_directed_perturbation_audit_only | no_prediction_benchmark_update | no_model_rescue_training | no_external_validation_claim | no_causal_knockout_claim | no_therapeutic_claim | no_validated_grn_claim | fixed_doses_no_tuning | frozen_stage72b_edges | raw_data_not_committed | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True |
