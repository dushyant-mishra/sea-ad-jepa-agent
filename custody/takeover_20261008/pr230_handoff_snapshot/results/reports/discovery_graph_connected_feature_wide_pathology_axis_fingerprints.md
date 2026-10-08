# Graph-Connected Feature-Wide Pathology-Axis Fingerprints

- Genes scored: 2,676
- Universe: Graph-JEPA feature genes connected to the consensus graph.
- Scores are model-implied pathology-head deltas under global-mean intervention.

## Score Definitions

- `tau_lowering_score = -AT8_delta`
- `amyloid_lowering_score = -A_beta_6e10_delta`
- `neuron_preservation_score = NeuN_delta`
- `gliosis_penalty = max(GFAP_delta, 0) + max(Iba1_delta, 0)`
- `therapeutic_like_score = tau_lowering_score + neuron_preservation_score - gliosis_penalty`
- `dual_pathology_lowering_score = tau_lowering_score + amyloid_lowering_score`
- `broad_shift_score = mean absolute delta across all five pathology readouts`

Every score includes a percentile rank against all 2,676 graph-connected genes.

## Distribution Summary

| score | mean | std | p10 | median | p90 | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tau_lowering_score | -0.0014424 | 0.022565 | -0.018065 | -0.0015935 | 0.013994 | 0.020773 | 0.61896 |
| amyloid_lowering_score | -0.00015954 | 0.039286 | -0.028772 | -0.001608 | 0.028247 | 0.039344 | 1.0344 |
| neuron_preservation_score | 0.0032636 | 0.021959 | -0.011913 | 0.0018308 | 0.017039 | 0.023296 | 0.57796 |
| gliosis_penalty | 0.021337 | 0.05333 | 0 | 0.009261 | 0.049953 | 0.069194 | 1.1212 |
| therapeutic_like_score | -0.019516 | 0.047946 | -0.056737 | -0.011803 | 0.014961 | 0.023275 | 0.10846 |
| dual_pathology_lowering_score | -0.0016019 | 0.058556 | -0.042975 | -0.0033631 | 0.038693 | 0.055002 | 1.6533 |
| broad_shift_score | 0.016053 | 0.023702 | 0.0061253 | 0.012534 | 0.025305 | 0.032299 | 0.69085 |

## Boundary

These fingerprints support pathology-delta ranking and null calibration. Nearest-neighbor manifold safety was not computed in the full run. The successful pilot and later targeted audits provide manifold-verified evidence.
