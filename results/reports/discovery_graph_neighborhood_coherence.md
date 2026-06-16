# Discovery Atlas Graph-Neighborhood Coherence

This report tests whether candidate genes sit in graph neighborhoods enriched for other scored candidates or for candidates with the same pathology-axis class. Nulls are degree-matched, so high-degree hub genes do not automatically look coherent.

## Configuration

- Scorecard: `results\tables\discovery_candidate_scorecard_v1.csv`
- Graph edges: `results\tables\v2_graph_consensus_edges.csv`
- Null draws per candidate: `1000`
- Initial degree window: `0.2`

## Coherence Status Counts

- `no_graph_enrichment`: 12
- `coherent_same_axis_neighborhood`: 4
- `no_scored_candidate_neighbors`: 4
- `candidate_enriched_neighborhood`: 3
- `not_in_graph_or_isolated`: 1

## Candidate Neighborhood Table

| candidate | pathology_axis_class | coherence_status | degree | n_scored_neighbors | n_same_class_neighbors | scored_neighbor_z | scored_neighbor_p | same_class_neighbor_z | same_class_neighbor_p | covariate_audit_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CSF1R | mixed_or_unclear | candidate_enriched_neighborhood | 56 | 7 | 1 | 4.337 | 0.002997 | 3.443 | 0.05495 | not_audited |
| HSP90AA1 | broad_reactive_state_shift | candidate_enriched_neighborhood | 110 | 8 | 5 | 3.708 | 0.03397 | 3.009 | 0.05395 | not_audited |
| CX3CR1 | broad_reactive_state_shift | candidate_enriched_neighborhood | 31 | 4 | 1 | 2.852 | 0.04196 | 0.8478 | 0.2877 | not_audited |
| MAPK1 | broad_reactive_state_shift | coherent_same_axis_neighborhood | 289 | 7 | 6 | 8.35 | 0.000999 | 16.91 | 0.000999 | not_audited |
| PLCG2 | mixed_or_unclear | coherent_same_axis_neighborhood | 49 | 3 | 1 | 1.442 | 0.1109 | 4.105 | 0.04795 | not_audited |
| STAT3 | broad_reactive_state_shift | coherent_same_axis_neighborhood | 111 | 9 | 6 | 4.268 | 0.01998 | 3.63 | 0.03896 | not_audited |
| BCL2 | broad_reactive_state_shift | coherent_same_axis_neighborhood | 160 | 6 | 4 | 3.442 | 0.03197 | 3.235 | 0.02597 | not_audited |
| HIF1A | broad_reactive_state_shift | no_graph_enrichment | 75 | 5 | 4 | 1.919 | 0.06693 | 2.371 | 0.06793 | not_audited |
| APP | broad_reactive_state_shift | no_graph_enrichment | 78 | 6 | 4 | 2.292 | 0.08691 | 2.108 | 0.1009 | CLEARED |
| GRB2 | broad_reactive_state_shift | no_graph_enrichment | 91 | 6 | 4 | 2.121 | 0.09091 | 2.009 | 0.1119 | not_audited |
| APOE | broad_reactive_state_shift | no_graph_enrichment | 46 | 4 | 2 | 2.295 | 0.06593 | 1.369 | 0.1159 | CLEARED |
| P2RY13 | amyloid_lowering_selective | no_graph_enrichment | 1 | 1 | 0 | 3.436 | 0.07892 | -0.06334 | 1 | not_audited |
| P2RY12 | gliosis_inflating | no_graph_enrichment | 13 | 2 | 0 | 2.281 | 0.08492 | -0.1428 | 1 | not_audited |
| CTSD | amyloid_lowering_selective | no_graph_enrichment | 20 | 3 | 0 | 2.587 | 0.07093 | -0.1534 | 1 | not_audited |
| TLR2 | gliosis_inflating | no_graph_enrichment | 46 | 4 | 0 | 2.201 | 0.07393 | -0.1925 | 1 | CLEARED |
| ROCK1 | amyloid_lowering_selective | no_graph_enrichment | 151 | 4 | 0 | 2.193 | 0.05195 | -0.2144 | 1 | not_audited |
| CD4 | artifact_or_covariate_sensitive | no_graph_enrichment | 89 | 6 | 0 | 2.16 | 0.09091 | -0.248 | 1 | WARNING: Technical Artifact |
| RHOA | neuron_risk | no_graph_enrichment | 142 | 2 | 0 | 0.828 | 0.1588 | -0.2846 | 1 | not_audited |
| CD74 | gliosis_inflating | no_graph_enrichment | 72 | 1 | 0 | -0.09004 | 0.4915 | -0.2947 | 1 | not_audited |
| PTPRG | mixed_or_unclear | no_scored_candidate_neighbors | 1 | 0 | 0 | -0.2784 | 1 | -0.04474 | 1 | not_audited |

## Interpretation Boundary

Graph-neighborhood coherence is supportive evidence, not causal proof. A target can be biologically important without a candidate-enriched one-hop neighborhood, and a coherent graph neighborhood can still reflect annotation bias, hub biology, or disease-state correlation.
