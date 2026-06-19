# Strict Shuffled Graph Edge Generation v1

## Original graph summary

- Source: `results\tables\v2_graph_consensus_edges.csv`
- Indexed nodes: 2957
- Undirected edges: 114,029
- Self-loops: 0
- Duplicate undirected edges: 0

## Current shuffled graph summary

- Source: `results\tables\ablation_edge_sets\shuffled_graph_edges_v1.csv`
- Edges: 114,029
- Starting original-edge overlap: 27,815 (24.3929%)
- Degree sequence matches the original graph exactly.

## Strict shuffled generation method

- Graphs were treated as simple undirected graphs using canonical sorted edge pairs.
- Each move was a degree-preserving double-edge swap.
- Self-loops and duplicate edges were rejected.
- Overlap-increasing swaps were rejected.
- Overlap-reducing swaps were preferred; occasional neutral swaps were available after stalls.
- Fixed seed: `20260619`
- Swap attempts: 145,122
- Accepted swaps: 25,913

## Degree preservation result

- Exact node-wise degree preservation: `True`
- Final edge count: 114,029
- Self-loops: 0
- Duplicate undirected edges: 0

## Original-edge overlap before and after

- Before: 27,815 (24.3929%)
- After: 0 (0.0000%)

## Zero-overlap result

Zero original-edge overlap was achieved.

## Recommendation

Use the strict shuffled graph for future approval-gated training.

- Training readiness: `True`
- Output: `results\tables\ablation_edge_sets\strict_shuffled_graph_edges_v1.csv`

## Boundary

- The existing `shuffled_graph_edges_v1.csv` was not overwritten.
- This generation script ran no model training.
- A previously approved Stage A attempt was stopped before producing a completed checkpoint or history CSV; its partial log remains untouched.
- No external validation was run.
- Evidence levels and the strict Level-2 gliosis criterion are unchanged.
