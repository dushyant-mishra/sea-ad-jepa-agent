# Discovery Atlas Pathology-Axis Fingerprints

This report is Phase 1 of the Graph-JEPA Discovery Atlas. It converts existing multi-target counterfactual outputs into continuous pathology-axis scores and conservative categorical labels.

## Score Definitions

- `tau_lowering_score = -AT8_delta`
- `amyloid_lowering_score = -A_beta_6e10_delta`
- `neuron_preservation_score = NeuN_delta`
- `gliosis_penalty = max(GFAP_delta, 0) + max(Iba1_delta, 0)`
- `therapeutic_like_score = tau_lowering_score + neuron_preservation_score - gliosis_penalty`
- `amyloid_selectivity_score = amyloid_lowering_score - abs(AT8_delta) - gliosis_penalty`
- `tau_selectivity_score = tau_lowering_score - abs(A_beta_6e10_delta) - gliosis_penalty`

## Gene Class Counts

- `gliosis_inflating`: 8
- `amyloid_lowering_candidate`: 6
- `mixed_or_unclear`: 6
- `dual_pathology_lowering_candidate`: 2
- `artifact_or_covariate_sensitive`: 1
- `neuron_risk`: 1

## Gene Label Confidence Counts

- `weak`: 21
- `moderate`: 3

## Module Class Counts

- `gliosis_inflating`: 4
- `amyloid_lowering_candidate`: 3
- `tau_lowering_neuron_preserving`: 1
- `dual_pathology_lowering_candidate`: 1
- `mixed_or_unclear`: 1

## Module Label Confidence Counts

- `moderate`: 8
- `high`: 1
- `weak`: 1

## Top Gene Fingerprints by Discovery Sort Score

| candidate | pathology_axis_class | pathology_axis_label_confidence | therapeutic_like_score | amyloid_selectivity_score | tau_selectivity_score | gliosis_penalty | covariate_audit_status | classification_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PTPRG | dual_pathology_lowering_candidate | weak | 0.00802681 | -0.0032772 | -0.00670302 | 0.00499011 | not_audited | AT8 and A_beta both lower without strong NeuN loss; not automatically therapeutic |
| CTSD | amyloid_lowering_candidate | weak | 0.00871805 | -0.00842681 | -0.0233211 | 0.014668 | not_audited | A_beta lowered but selectivity score or tau/gliosis penalties weaken amyloid specificity |
| CD4 | artifact_or_covariate_sensitive | weak | 0.00771457 | -0.00953485 | -0.0187253 | 0.0141301 | WARNING: Technical Artifact | covariate audit warning |
| P2RY13 | amyloid_lowering_candidate | weak | 0.00295287 | -0.00378925 | -0.00781996 | 0.00580461 | not_audited | A_beta lowered but selectivity score or tau/gliosis penalties weaken amyloid specificity |
| DRAM1 | mixed_or_unclear | weak | -0.000591391 | -0.00144898 | -0.00245889 | 0.00119278 | not_audited | no conservative pathology-axis rule passed |
| F13A1 | mixed_or_unclear | weak | -0.00144054 | -0.00135206 | -0.00135206 | 0.000263577 | not_audited | no conservative pathology-axis rule passed |
| ROCK1 | amyloid_lowering_candidate | weak | -0.000869484 | -0.00938661 | -0.0134547 | 0.0114207 | not_audited | A_beta lowered but selectivity score or tau/gliosis penalties weaken amyloid specificity |
| CHI3L1 | mixed_or_unclear | weak | -0.00220136 | -0.00075217 | -8.49656e-05 | 0 | not_audited | no conservative pathology-axis rule passed |
| UGCG | mixed_or_unclear | weak | -0.00650793 | -0.0130796 | -0.0171858 | 0.0143355 | not_audited | no conservative pathology-axis rule passed |
| PLCG2 | mixed_or_unclear | weak | -0.00839987 | -0.0104451 | -0.0124905 | 0.0108382 | not_audited | no conservative pathology-axis rule passed |
| CSF1R | mixed_or_unclear | weak | -0.00931715 | -0.0157302 | -0.0199314 | 0.0168821 | not_audited | no conservative pathology-axis rule passed |
| CD74 | gliosis_inflating | weak | -0.0109262 | -0.0204762 | -0.0231558 | 0.020571 | not_audited | GFAP/Iba1 penalty exceeds threshold |

## Top Module Fingerprints by Discovery Sort Score

| candidate | pathology_axis_class | pathology_axis_label_confidence | therapeutic_like_score | amyloid_selectivity_score | tau_selectivity_score | gliosis_penalty | classification_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| antigen_presentation | tau_lowering_neuron_preserving | high | 0.0631974 | -0.0163652 | -0.0534992 | 0.0349322 | AT8 lowered, NeuN preserved/increased, gliosis low, and tau/therapeutic score positive |
| vascular_barrier_myeloid | dual_pathology_lowering_candidate | moderate | 0.0493573 | -0.0141139 | -0.0406209 | 0.0273674 | AT8 and A_beta both lower without strong NeuN loss; not automatically therapeutic |
| inflammatory_signaling | mixed_or_unclear | weak | 0.0296265 | 0.00558837 | -0.00558837 | 0 | no conservative pathology-axis rule passed |
| complement | amyloid_lowering_candidate | moderate | 0.0361162 | -0.0041599 | -0.0287242 | 0.016442 | A_beta lowered but selectivity score or tau/gliosis penalties weaken amyloid specificity |
| plaque_response | amyloid_lowering_candidate | moderate | 0.0167887 | -0.0492188 | -0.100512 | 0.0748655 | A_beta lowered but selectivity score or tau/gliosis penalties weaken amyloid specificity |
| disease_associated_microglia | amyloid_lowering_candidate | moderate | 0.0126306 | -0.0517959 | -0.102717 | 0.0772564 | A_beta lowered but selectivity score or tau/gliosis penalties weaken amyloid specificity |
| senescence_stress | gliosis_inflating | moderate | -0.0323004 | -0.0885464 | -0.107917 | 0.0863017 | GFAP/Iba1 penalty exceeds threshold |
| lysosome_phagocytosis | gliosis_inflating | moderate | -0.0355945 | -0.106642 | -0.149241 | 0.120956 | GFAP/Iba1 penalty exceeds threshold |
| lipid_metabolism | gliosis_inflating | moderate | -0.0752994 | -0.12541 | -0.128943 | 0.113407 | GFAP/Iba1 penalty exceeds threshold |
| homeostatic_microglia | gliosis_inflating | moderate | -0.0758473 | -0.130173 | -0.145634 | 0.125501 | GFAP/Iba1 penalty exceeds threshold |

## Label Semantics

- `amyloid_lowering_candidate` means the perturbation lowers the model-implied A beta/6e10 readout, but tau movement, gliosis, or broad-state penalties weaken selectivity.
- `amyloid_selective` requires positive `amyloid_selectivity_score`, low gliosis penalty, and limited AT8 spillover.
- `tau_lowering_candidate` means the perturbation lowers AT8 but does not satisfy the stricter NeuN-preserving/gliosis-safe rule.
- `tau_lowering_neuron_preserving` requires AT8 lowering, NeuN preservation/increase, low gliosis, and a positive tau-selective or therapeutic-like score.

## A Beta Boundary Note

The `A_beta_6e10_delta` and `amyloid_selectivity_score` columns are the first inputs for the planned A beta boundary analysis. A beta-lowering candidate does not mean plaque-proximal microglia. Amyloid-selective requires positive `amyloid_selectivity_score`. All A beta labels are model-implied and should feed the planned A beta boundary analysis rather than stand alone as plaque biology validation.

## Claim Boundary

These fingerprints classify model-implied counterfactual readouts. They do not prove biological causality or therapeutic efficacy.
