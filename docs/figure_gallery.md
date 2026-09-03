# Current Public Figures

These are the figures used by the current **Contextual JEPA / FULL104** project overview.

Older Graph-JEPA v1-v3 figures remain under `results/figures/` for provenance. They are historical and should not be read as the current result set.

## 1. Why partial biology?

![Why Contextual JEPA uses partial RNA](../results/figures/public_v4_contextual_jepa_overview.svg)

**What it shows:** Partial evidence is deliberate. Different assays expose different parts of the molecular state, and the model must distinguish measured zero from structural non-measurement and collision-unresolved measurements.

The student is evaluated across 20/40/60/80/100% evidence. The goal is to recover biological state/program structure from context rather than reproduce the exact hidden transcript realization.

**Interpretation boundary:** This is the scientific objective and evidence design, not an F1 result.

## 2. Current architecture family

![Current Contextual JEPA architecture](../results/figures/public_v4_architecture.svg)

**What it shows:** The full 41,238-address Molecular Ledger feeds a token-preserving IPB backbone with two complementary routes:

- direct biological/state route;
- nonlinear contextual residual route;
- singleton/query-local readout.

The query identity remains available while its scalar can be withheld. The query-safe teacher uses the richest lawful context, but the queried scalar is removed before contextual mixing.

**Key point:** global cell state and query-local molecular context are treated as distinct biological axes.

## 3. FULL104 lawful reader-fit scope

![FULL104 reader-fit scope](../results/figures/public_v4_full104_scope.svg)

**Frozen scope:**

- 4,553,407 lawful reader-fit cells
- 104 donors
- 42 measurement operators
- 1,400 donor×operator strata
- 41,238 molecular addresses
- SEA-AD: 4,118,213 cells
- NPH52: 236,476 cells
- HVS: 198,718 cells

Reader-validation, reader-oracle, DEV, SEALED and pathology expression remain outside this scope.

**Key point:** dataset-dependent quantities are derived from the lawful full corpus rather than transplanted from smaller pilots.

## 4. Single-GPU engineering

![Single-GPU streaming and compute strategy](../results/figures/public_v4_single_gpu_engineering.svg)

**What it shows:** The project is being developed on one RTX 3080 Laptop GPU with 16 GB VRAM. The full corpus is never densified in GPU or host memory.

The executor relies on:

- immutable source shards;
- exact row lineage;
- donor×operator accounting;
- block-major/sorted physical reads;
- restoration of frozen logical order;
- resume-safe boundaries;
- reuse of expensive passes when scientific semantics permit;
- sufficient-statistic reduction rather than unnecessary durable hidden-state storage.

The historical FULL104 ALL executor is included as a solved engineering example: a replicate-major design projected beyond 100 days was replaced, without changing the estimator, by a validated K=32 block-major plan with 16 effective passes and ~23.8 h projected wall time.

The current F1 sufficient-statistics design would reduce final qualification storage to ~4.05 MiB of scalar arrays after independent validation. That is a prospective execution plan, not a biological result.

## Current interpretation boundary

These figures describe the current scientific objective, architecture, frozen reader-fit scope, and accepted/reviewed engineering strategy.

They do **not** claim that real F1 biology has passed.

Current status is maintained in [`START_HERE.md`](../START_HERE.md). Contextual Target V1 F0 and the HC3 numerical-robustness repair are accepted; real F1 remains blocked until the prospective evidence-trend numerical repair passes external review and the reader/forward/executor preflight is completed.
