# Stage50 manual acquisition gaps

- strict_graph_controls: Build no-graph, beta0, random, gene-label-shuffled, and degree-preserving shuffled controls over the same node universe.
- graph_expression_overlap: Align graph nodes to the selected donor expression/module matrix before any JEPA run.
- frozen_embeddings_for_probe: Only after leakage-safe pretraining, evaluate frozen embeddings with donor-held-out probes.
- external_validation_cohort: Required before external validation language.
