# Discovery Atlas Graph-Neighborhood Coherence

This report tests whether candidate genes sit in graph neighborhoods enriched for other scored candidates or for candidates with the same pathology-axis class. Nulls are degree-matched, so high-degree hub genes do not automatically look coherent.

## Configuration

- Scorecard: `results\tables\discovery_candidate_scorecard_v1.csv`
- Graph edges: `results\tables\v2_graph_consensus_edges.csv`
- Null draws per candidate: `1000`
- Initial degree window: `0.2`

## Coherence Status Counts

- `no_graph_enrichment`: 9
- `coherent_same_axis_neighborhood`: 6
- `candidate_enriched_neighborhood`: 4
- `no_scored_candidate_neighbors`: 4
- `not_in_graph_or_isolated`: 1

## Candidate Neighborhood Table

| candidate | pathology_axis_class | coherence_status | degree | n_scored_neighbors | n_same_class_neighbors | scored_neighbor_z | scored_neighbor_p | same_class_neighbor_z | same_class_neighbor_p | covariate_audit_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CSF1R | mixed_or_unclear | candidate_enriched_neighborhood | 56 | 7 | 1 | 4.337 | 0.002997 | 3.443 | 0.05495 | not_audited |
| STAT3 | gliosis_inflating | candidate_enriched_neighborhood | 111 | 9 | 3 | 4.268 | 0.01998 | 3.015 | 0.06494 | not_audited |
| CX3CR1 | gliosis_inflating | candidate_enriched_neighborhood | 31 | 4 | 1 | 2.852 | 0.04196 | 1.313 | 0.1499 | not_audited |
| BCL2 | gliosis_inflating | candidate_enriched_neighborhood | 160 | 6 | 1 | 3.442 | 0.03197 | 1.011 | 0.1868 | not_audited |
| MAPK1 | amyloid_lowering_candidate | coherent_same_axis_neighborhood | 289 | 7 | 3 | 8.35 | 0.000999 | 5.991 | 0.000999 | not_audited |
| ROCK1 | amyloid_lowering_candidate | coherent_same_axis_neighborhood | 151 | 4 | 3 | 2.193 | 0.05195 | 4.188 | 0.02797 | not_audited |
| PLCG2 | mixed_or_unclear | coherent_same_axis_neighborhood | 49 | 3 | 1 | 1.442 | 0.1109 | 4.105 | 0.04795 | not_audited |
| APP | gliosis_inflating | coherent_same_axis_neighborhood | 78 | 6 | 4 | 2.292 | 0.08691 | 3.769 | 0.02398 | CLEARED |
| HSP90AA1 | amyloid_lowering_candidate | coherent_same_axis_neighborhood | 110 | 8 | 3 | 3.708 | 0.03397 | 3.641 | 0.03896 | not_audited |
| HIF1A | amyloid_lowering_candidate | coherent_same_axis_neighborhood | 75 | 5 | 3 | 1.919 | 0.06693 | 3.015 | 0.02398 | not_audited |
| APOE | gliosis_inflating | no_graph_enrichment | 46 | 4 | 2 | 2.295 | 0.06593 | 2.669 | 0.06294 | CLEARED |
| GRB2 | gliosis_inflating | no_graph_enrichment | 91 | 6 | 2 | 2.121 | 0.09091 | 1.471 | 0.1269 | not_audited |
| CD74 | gliosis_inflating | no_graph_enrichment | 72 | 1 | 1 | -0.09004 | 0.4915 | 0.7359 | 0.2098 | not_audited |
| TLR2 | dual_pathology_lowering_candidate | no_graph_enrichment | 46 | 4 | 0 | 2.201 | 0.07393 | -0.1314 | 1 | CLEARED |
| P2RY13 | amyloid_lowering_candidate | no_graph_enrichment | 1 | 1 | 0 | 3.436 | 0.07892 | -0.1353 | 1 | not_audited |
| CD4 | artifact_or_covariate_sensitive | no_graph_enrichment | 89 | 6 | 0 | 2.16 | 0.09091 | -0.248 | 1 | WARNING: Technical Artifact |
| RHOA | neuron_risk | no_graph_enrichment | 142 | 2 | 0 | 0.828 | 0.1588 | -0.2846 | 1 | not_audited |
| P2RY12 | gliosis_inflating | no_graph_enrichment | 13 | 2 | 0 | 2.281 | 0.08492 | -0.3325 | 1 | not_audited |
| CTSD | amyloid_lowering_candidate | no_graph_enrichment | 20 | 3 | 0 | 2.587 | 0.07093 | -0.3347 | 1 | not_audited |
| CHI3L1 | mixed_or_unclear | no_scored_candidate_neighbors | 2 | 0 | 0 | -0.3047 | 1 | -0.04474 | 1 | not_audited |

## Interpretation Boundary

Graph-neighborhood coherence is supportive evidence, not causal proof. A target can be biologically important without a candidate-enriched one-hop neighborhood, and a coherent graph neighborhood can still reflect annotation bias, hub biology, or disease-state correlation.
