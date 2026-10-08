# JEPA v2 Graph Foundation

This report summarizes the first graph-topology layer for JEPA v2. The goal is to decide whether the 2,957-gene SEA-AD JEPA feature space is connected enough to support graph-aware representation learning.

## Graph Sources

Three graph views were built:

- **STRING prior graph:** public human protein/functional interaction prior from STRING v12.0.
- **WGCNA/TOM empirical graph:** SEA-AD Microglia-PVM donor pseudobulk co-expression topology using a signed WGCNA-style adjacency and topological overlap matrix.
- **Consensus graph:** union and overlap of STRING high-confidence edges and WGCNA/TOM edges.

## STRING Prior Graph

STRING was evaluated at three confidence thresholds.

| Threshold | Edges | Connected genes | Connected fraction | Largest component | Median degree |
|---:|---:|---:|---:|---:|---:|
| 400 | 55,027 | 2,789 / 2,957 | 0.943 | 2,785 | 21 |
| 700 | 14,565 | 2,311 / 2,957 | 0.782 | 2,261 | 4 |
| 900 | 6,781 | 1,789 / 2,957 | 0.605 | 1,642 | 1 |

Interpretation: STRING is viable as a portable prior graph. Threshold 700 is a good first v2 default because it is high confidence while still connecting most of the feature space.

## WGCNA/TOM Empirical Graph

The WGCNA-style graph used:

```text
pseudobulk: SEA-AD Microglia-PVM donor means
feature space: same 2,957 genes as the JEPA model
network: signed adjacency, power = 6
edge export: top 100,000 TOM edges
```

| Edges | Connected genes | Connected fraction | Largest component | Median degree |
|---:|---:|---:|---:|---:|
| 100,000 | 1,821 / 2,957 | 0.616 | 762 | 13 |

Interpretation: WGCNA/TOM gives a dense SEA-AD-specific empirical subgraph, but it does not cover the full JEPA feature space. This is expected because empirical donor-level co-expression is sparse and cohort-specific.

## Consensus Graph

The consensus graph merged STRING threshold 700 with the WGCNA/TOM top-edge graph.

| Graph view | Edges | Connected genes | Connected fraction | Largest component | Median degree |
|---|---:|---:|---:|---:|---:|
| Union | 114,029 | 2,676 / 2,957 | 0.905 | 2,666 | 26 |
| Supported by both | 536 | 376 / 2,957 | 0.127 | 156 | 0 |
| STRING only | 14,029 | 2,303 / 2,957 | 0.779 | 2,253 | 4 |
| WGCNA only | 99,464 | 1,821 / 2,957 | 0.616 | 762 | 13 |

Interpretation: the strict intersection graph is too small and housekeeping-heavy to use alone. The union graph is the practical v2 message-passing graph. The both-supported graph should be treated as a high-confidence annotation or ablation subset, not the main topology.

## Recommended v2 Use

Use the graph views as an ablation ladder:

1. **Flat JEPA v1:** no graph.
2. **STRING-GNN-JEPA:** external prior only.
3. **WGCNA-GNN-JEPA:** SEA-AD empirical graph only.
4. **Union-GNN-JEPA:** STRING + WGCNA union graph.
5. **Both-supported edge analysis:** high-confidence interpretation subset.

This design avoids overcommitting to either a generic database or a circular SEA-AD-only co-expression graph.

## Interpretation Boundary

STRING is not a pure directed gene-regulatory network; it is a protein/functional association prior. WGCNA/TOM is not causal; it is empirical co-expression topology. Graph-JEPA v2 can become more biologically structured than flat JEPA, but causal claims still require perturbation, time-course, or independent cohort validation.
