# Scorecard v2 Graph-Neighborhood Coherence

## Configuration

- Scorecard: `results\tables\discovery_scorecard_v2_graph_connected_feature_wide.csv`
- Consensus edges: `results\tables\v2_graph_consensus_edges.csv`
- Genes tested: 2,676
- Degree-matched null draws per gene: 1,000
- Degree bins preserve tied graph degrees.

## Coherence Status Counts

- `no_graph_support`: 2,404
- `isolated_high_score_gene`: 268
- `broad_reactive_neighborhood`: 4

## Explicit Named-Gene Audit

| gene | pathology_axis_class | coherence_status | coherence_evidence_basis | degree | n_scored_neighbors | same_class_neighbor_fraction | mean_neighbor_therapeutic_like_percentile | mean_neighbor_broad_shift_percentile | same_class_neighbor_FDR | neighbor_therapeutic_FDR | neighbor_broad_shift_FDR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APOE | broad_reactive_state_shift | no_graph_support | no_degree_matched_enrichment | 46 | 46 | 0.043478 | 51.186 | 50.062 | 1 | 0.92824 | 0.99942 |
| APP | broad_reactive_state_shift | no_graph_support | no_degree_matched_enrichment | 78 | 78 | 0.051282 | 49.018 | 58.959 | 1 | 0.95476 | 0.99942 |
| CD4 | amyloid_lowering_candidate | no_graph_support | no_degree_matched_enrichment | 89 | 89 | 0.078652 | 48.191 | 49.375 | 1 | 0.89111 | 1 |
| DLG1 | broad_reactive_state_shift | no_graph_support | no_degree_matched_enrichment | 656 | 656 | 0.047256 | 52.846 | 48.927 | 1 | 0.66833 | 1 |
| ERC1 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 534 | 534 | 0.05618 | 50.917 | 50.348 | 1 | 0.95476 | 0.99942 |
| FIP1L1 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 461 | 461 | 0.067245 | 45.858 | 55.252 | 1 | 0.98894 | 0.99595 |
| GSK3B | tau_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 443 | 443 | 0.020316 | 47.102 | 55.568 | 1 | 0.98894 | 0.99595 |
| KIF2A | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 436 | 436 | 0.066514 | 45.618 | 55.489 | 1 | 0.99454 | 0.99595 |
| PAFAH1B1 | broad_reactive_state_shift | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 639 | 639 | 0.048513 | 52.608 | 48.818 | 1 | 0.9468 | 1 |
| PTPN18 | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 56 | 56 | 0.035714 | 35.132 | 79.812 | 1 | 0.99647 | 0.98742 |
| RC3H1 | broad_reactive_state_shift | no_graph_support | no_degree_matched_enrichment | 623 | 623 | 0.048154 | 52.419 | 48.631 | 1 | 0.89111 | 1 |
| SLAIN2 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 445 | 445 | 0.065169 | 45.876 | 55.532 | 1 | 0.98894 | 0.99595 |
| TLR2 | tau_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 46 | 46 | 0.021739 | 50.11 | 45.577 | 1 | 0.95476 | 1 |

## Coherent Cleaner Neighborhoods

_No rows._

## Broad-Reactive Neighborhoods

| gene | pathology_axis_class | coherence_status | coherence_evidence_basis | degree | n_scored_neighbors | same_class_neighbor_fraction | mean_neighbor_therapeutic_like_percentile | mean_neighbor_broad_shift_percentile | same_class_neighbor_FDR | neighbor_therapeutic_FDR | neighbor_broad_shift_FDR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HPS3 | broad_reactive_state_shift | broad_reactive_neighborhood | absolute_neighbor_profile_only | 82 | 82 | 0.13415 | 35.342 | 78.717 | 1 | 1 | 0.71974 |
| KIF16B | broad_reactive_state_shift | broad_reactive_neighborhood | absolute_neighbor_profile_only | 54 | 54 | 0.22222 | 34.133 | 79.412 | 1 | 0.99837 | 0.98742 |
| GGA2 | broad_reactive_state_shift | broad_reactive_neighborhood | absolute_neighbor_profile_only | 21 | 21 | 0.47619 | 34.004 | 80.684 | 1 | 0.99837 | 0.98742 |
| MYH9 | broad_reactive_state_shift | broad_reactive_neighborhood | absolute_neighbor_profile_only | 41 | 41 | 0.43902 | 31.696 | 75.539 | 1 | 0.98894 | 0.99605 |

Broad-reactive status can be assigned from a high absolute mean neighbor broad-shift percentile. Check `coherence_evidence_basis`: `absolute_neighbor_profile_only` means the neighborhood did not survive the degree-matched enrichment test.

## Isolated High-Score Genes

| gene | pathology_axis_class | coherence_status | coherence_evidence_basis | degree | n_scored_neighbors | same_class_neighbor_fraction | mean_neighbor_therapeutic_like_percentile | mean_neighbor_broad_shift_percentile | same_class_neighbor_FDR | neighbor_therapeutic_FDR | neighbor_broad_shift_FDR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SLAIN2 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 445 | 445 | 0.065169 | 45.876 | 55.532 | 1 | 0.98894 | 0.99595 |
| PAFAH1B1 | broad_reactive_state_shift | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 639 | 639 | 0.048513 | 52.608 | 48.818 | 1 | 0.9468 | 1 |
| CD300A | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 161 | 161 | 0.1118 | 39.068 | 69.097 | 1 | 0.99991 | 0.96758 |
| GSK3B | tau_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 443 | 443 | 0.020316 | 47.102 | 55.568 | 1 | 0.98894 | 0.99595 |
| FIP1L1 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 461 | 461 | 0.067245 | 45.858 | 55.252 | 1 | 0.98894 | 0.99595 |
| ETS2 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 5 | 5 | 0 | 26.644 | 77.182 | 1 | 0.99839 | 0.98742 |
| ABL1 | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 127 | 127 | 0.015748 | 40.521 | 71.12 | 1 | 0.98894 | 0.99181 |
| SNX13 | broad_reactive_state_shift | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 290 | 290 | 0.051724 | 46.226 | 55.982 | 1 | 0.98894 | 0.99181 |
| KATNBL1 | broad_reactive_state_shift | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 255 | 255 | 0.10196 | 46.759 | 57.653 | 1 | 0.9468 | 0.99942 |
| ERC1 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 534 | 534 | 0.05618 | 50.917 | 50.348 | 1 | 0.95476 | 0.99942 |
| UGCG | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 8 | 8 | 0.125 | 47.552 | 55.47 | 1 | 0.98894 | 0.99595 |
| CPQ | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 35 | 35 | 0.028571 | 26.377 | 94.184 | 1 | 0.99837 | 0.97756 |
| KIF2A | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 436 | 436 | 0.066514 | 45.618 | 55.489 | 1 | 0.99454 | 0.99595 |
| VPS50 | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 237 | 237 | 0.021097 | 45.054 | 58.81 | 1 | 0.97645 | 0.99942 |
| BRAF | mixed_or_unclear | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 692 | 692 | 0.70376 | 52.122 | 48.654 | 1 | 0.95287 | 1 |
| SERGEF | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 404 | 404 | 0.017327 | 44.631 | 55.689 | 1 | 0.99837 | 0.99595 |
| SCYL2 | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 443 | 443 | 0.020316 | 46.026 | 55.305 | 1 | 0.98894 | 0.99595 |
| MIGA1 | amyloid_lowering_candidate | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 435 | 435 | 0.066667 | 45.43 | 55.725 | 1 | 0.99647 | 0.99498 |
| PARP4 | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 343 | 343 | 0.017493 | 44.397 | 57.24 | 1 | 0.99837 | 0.98564 |
| SLC38A9 | tau_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 67 | 67 | 0.029851 | 36.668 | 77.045 | 1 | 0.98894 | 0.99491 |
| MDM2 | tau_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 81 | 81 | 0.024691 | 46.532 | 56.235 | 1 | 0.95476 | 0.99942 |
| ZDHHC17 | tau_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 384 | 384 | 0.018229 | 47.858 | 53.45 | 1 | 0.97645 | 0.99942 |
| SMARCA4 | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 75 | 75 | 0.013333 | 40.059 | 65.281 | 1 | 0.98894 | 0.99718 |
| AP1G1 | dual_pathology_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 106 | 106 | 0 | 40.463 | 66.628 | 1 | 0.98894 | 0.99605 |
| TLR2 | tau_lowering_neuron_preserving | isolated_high_score_gene | high_focal_score_without_neighbor_enrichment | 46 | 46 | 0.021739 | 50.11 | 45.577 | 1 | 0.95476 | 1 |

## Degree-Matching Diagnostics

- Genes using nearest degree-bin fallback: 0
- Genes with no testable degree-matched pool: 0
- Genes surviving any degree-matched neighborhood FDR test: 0

## Boundary

Graph-neighborhood coherence is supportive evidence only. It does not imply regulatory causality because STRING/WGCNA edges are associative. Coherence can reflect annotation density, co-expression, protein interaction priors, or shared disease-state correlation.
