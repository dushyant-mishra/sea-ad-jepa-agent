# Current Public Figures

This page contains the figures that describe the **current JEPA v4 / Contextual Target project**.

Older Graph-JEPA v1-v3 figures remain in `results/figures/` for provenance, but they are no longer used as the public project summary. In particular, old Stage C leaderboards, pathology geometry plots, and v1-v3 multi-target validation figures should be treated as historical rather than current.

## 1. Contextual JEPA overview

![Contextual JEPA overview](../results/figures/public_v4_contextual_jepa_overview.svg)

**What it shows:** The current project predicts biological programs and state from partial RNA evidence rather than trying to reconstruct every hidden transcript.

The model keeps molecular address identity and respects the difference between a measured value, a measured zero, and a structurally unavailable measurement. For a query, the scalar can be withheld while the query identity remains present. The representation must then use the rest of the lawful cellular context.

**Key point:** the scientific target is biological state, not imputation accuracy.

## 2. FULL104 lawful reader-fit scope

![FULL104 reader-fit scope](../results/figures/public_v4_full104_scope.svg)

**What it shows:** The frozen corpus on which dataset-dependent quantities are defined.

- 4,553,407 lawful reader-fit cells
- 104 donors
- 42 measurement operators
- 41,238 molecular addresses
- SEA-AD: 4,118,213 cells
- NPH52: 236,476 cells
- HVS: 198,718 cells

Development and sealed expression are outside this reader-fit scope.

**Key point:** scale-dependent quantities are derived on the full lawful corpus rather than copied from smaller pilot datasets.

## Current interpretation boundary

These figures describe the current objective and frozen data scope. They do **not** claim that the final F1 biological gate has passed.

Contextual Target V1 F0 and the HC3 numerical-robustness repair have passed their respective reviews. The real F1 model-forward result is still blocked pending the prospective evidence-trend numerical repair described in [`START_HERE.md`](../START_HERE.md).

This distinction is deliberate: public figures should show only what has actually been established.
