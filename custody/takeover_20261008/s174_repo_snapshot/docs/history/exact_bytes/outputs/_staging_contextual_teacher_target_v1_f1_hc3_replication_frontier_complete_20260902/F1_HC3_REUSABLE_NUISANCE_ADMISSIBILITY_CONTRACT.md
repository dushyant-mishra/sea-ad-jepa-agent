# F1 HC3 reusable nuisance admissibility contract

This freezes a cohort-agnostic procedure, not the current cohort's ranks and not a model-selection rule.

For every later lawful donor cohort: (A) rebuild the mandatory nuisance base from that cohort's frozen primitives; (B) recompute source/operator residual spaces; (C) recompute `LOCAL_NUMERICAL_RANK`, `FULL_DESIGN_INCREMENTAL_RANK`, `DONOR_REPLICATED_RANK`, and `HC3_ADMISSIBLE_RANK`; (D) admit a prefix/direction only through the unchanged full-design rank, leave-one-donor-out replication, and HC3 geometry checks. The procedure must not carry forward HVS rank 6, NPH52 rank 1 or 0, SEA-AD rank 4, donor NPH_906, or any current leverage value.

A `NONREPLICATED_NUISANCE_DIRECTION` in this cohort may become estimable when a larger cohort supplies independent donor replication. A direction estimable here may fail in a larger cohort if new rare operator/source geometry creates a `HC3_DONOR_INDISPENSABLE_DIRECTION`. Measured cohort geometry determines ranks; the algorithm remains frozen. This contract does not authorize automatic model selection.
