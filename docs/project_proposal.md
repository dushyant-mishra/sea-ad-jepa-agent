# Project Proposal

## Title

SEA-AD JEPA Agent: Pathology-Grounded Gene Network Discovery in Alzheimer Disease

## Short Pitch

Alzheimer disease datasets increasingly contain single-cell transcriptomics, spatial assays, quantitative pathology, and imaging. The bottleneck is no longer only data access. The bottleneck is turning those modalities into **testable biological hypotheses**.

This project builds a JEPA-agent framework that learns cell-state representations from SEA-AD and asks whether those states explain real neuropathology. The first pilot focuses on Microglia-PVM cells in the middle temporal gyrus and tests whether microglial expression programs predict AT8/pTau, A beta, Iba1, GFAP, and NeuN pathology.

## The Problem

Most single-cell workflows produce clusters, marker genes, and enrichment tables. Those are useful, but they often stop short of the biological question:

```text
Which cell-state programs are actually linked to disease pathology?
```

In Alzheimer disease, this matters because molecular state and tissue pathology are not the same thing.

Single-nucleus RNA-seq tells us what genes are active in a cell population. Neuropathology tells us where disease burden exists and how severe it is. Spatial and imaging assays show tissue context. A useful discovery system should connect these views, not analyze them as separate worlds.

## The Opportunity

SEA-AD is an unusually good setting for this because it provides:

- human Alzheimer disease tissue
- single-nucleus transcriptomics
- donor metadata
- quantitative neuropathology
- spatial transcriptomics resources
- disease progression annotations

For dataset details and abbreviation definitions, see [dataset_guide.md](dataset_guide.md).

This lets us evaluate cell-state representations against real pathology instead of only asking whether they recover known cell types.

## Why Microglia First

Microglia are the right first wedge because they are central to several Alzheimer-relevant axes:

- plaque response
- inflammatory activation
- complement signaling
- lipid metabolism
- phagocytosis and lysosomal biology
- known genetic risk pathways involving `APOE`, `TREM2`, `TYROBP`, `PLCG2`, and related genes

SEA-AD also provides pathology targets that are directly meaningful for this cell population, including A beta plaque measures, AT8/pTau burden, Iba1 signal, and activated Iba1 counts.

The first pilot therefore asks:

> Which microglial expression programs predict donor-level Alzheimer pathology, and which genes/modules should be prioritized for validation?

## Why JEPA

Raw single-cell expression is sparse, noisy, and heavily affected by technical variation. A model that tries to reconstruct every raw gene count can spend capacity learning noise.

JEPA-style learning is attractive because it predicts latent representations rather than raw observations. In this project, the model learns from partial gene-expression context and predicts a target cell-state embedding.

The intended shift is:

```text
reconstruct all counts
        -> predict meaningful biological state
```

That is important for biology because the object we care about is not the exact observed count vector. The object we care about is the underlying disease-relevant cell state.

## Why an Agentic Layer

The agentic layer is not the discovery model. It is the reasoning and orchestration layer.

Its job is to take structured outputs and produce evidence-aware hypotheses:

- Which latent states predict pathology?
- Which genes explain those states?
- Which pathways are enriched?
- Which findings match known Alzheimer biology?
- Which validation experiment should come next?

The agent should never invent evidence. It should operate on tables, model outputs, gene rankings, enrichment results, and curated biological context.

## Minimum Viable Demonstration

The first demonstration has four steps:

1. Build Microglia-PVM donor-level pseudobulk features from SEA-AD MTG.
2. Predict donor-level neuropathology from microglial expression.
3. Train a JEPA model on a Microglia-PVM cell-level pilot.
4. Rank genes and modules associated with the strongest pathology-linked signals.

Success does not require claiming a causal mechanism. Success means showing that the pipeline can move from:

```text
single-cell expression
        -> pathology-linked prediction
        -> candidate genes/modules
        -> clear validation hypotheses
```

## First Result

The first Microglia-PVM pseudobulk baseline shows that microglial expression features predict AT8/pTau-related pathology better than several other targets.

Top held-out donor associations from the initial baseline:

```text
number of AT8 positive cells per area_Grey matter: Spearman ~= 0.536
percent AT8 positive area_Grey matter: Spearman ~= 0.531
percent NeuN positive area_Grey matter: Spearman ~= 0.511
```

The first AT8-associated gene ranking highlights candidates including:

```text
PTPRG
S100A4
CHI3L1
DRAM1
TNFRSF11B
IL27RA
CTSD
NFKBIA
```

These genes are not presented as final biology. They are starting points for enrichment analysis, spatial validation, literature review, and mechanistic follow-up.

## What Makes This Different

This is not just another cell-type classifier.

The distinctive claim is:

> Learn disease-state representations and evaluate them against measured pathology, then convert the predictive signal into ranked gene-network hypotheses.

This makes the project pathology-grounded from the beginning.

## Long-Term Vision

The project can expand in several directions:

- pathway-aware JEPA masking
- spatial transcriptomics validation
- neuropathology image feature extraction
- snATAC regulatory support
- IHC/IF marker recommendation
- perturbation dataset comparison with LINCS or JUMP Cell Painting
- agent-generated biological reports with evidence grading

The eventual system should help answer questions like:

```text
Which microglial programs track tau pathology?
Which genes explain that program?
Where should we look spatially?
Which stain or perturbation would validate it?
```

That is the heart of the project.
