# System Architecture

## Overview

The project is designed as a staged biological discovery system.

The first stage uses SEA-AD MTG single-nucleus RNA-seq and donor-level neuropathology. Later stages add spatial transcriptomics, pathology image features, and agentic interpretation.

```text
User question
    |
    v
Agentic analysis layer
    |
    v
Structured analysis tools
    |
    +--> AnnData preprocessing
    +--> JEPA training
    +--> pathology prediction
    +--> gene module analysis
    +--> enrichment and regulator ranking
    |
    v
Biological hypothesis report
```

## Data Flow

```text
SEA-AD donor metadata
        |
        v
donor-level covariates

SEA-AD MTG neuropathology
        |
        v
A beta, pTau, GFAP, Iba1, NeuN targets

SEA-AD MTG snRNA-seq AnnData
        |
        v
cell-type pilot subset
        |
        v
JEPA cell-state embeddings
        |
        v
donor-level aggregation
        |
        v
pathology prediction and gene-network discovery
```

## Representation Learning Layer

The JEPA component learns by predicting target embeddings from context embeddings.

For snRNA-seq:

```text
cell expression vector
        |
        +--> context genes/modules --> context encoder
        |
        +--> target genes/modules  --> target encoder

context embedding --> predictor --> predicted target embedding
target embedding  --> stop gradient

loss(predicted target embedding, target embedding)
```

This encourages the model to learn latent biological state rather than reconstruct every noisy count.

## Pathology Prediction Layer

Cell-level embeddings are aggregated at the donor level because pathology targets are donor-level labels.

```text
cell embeddings
        |
        v
group by donor and cell population
        |
        v
mean/proportion/distribution summaries
        |
        v
predict pathology targets
```

Important rule:

```text
Train/test splits must be donor-level splits.
```

Cell-level splits would leak donor pathology information.

## Gene Network Discovery Layer

Once a latent factor or state is associated with pathology, the analysis layer asks:

- Which genes are associated with this state?
- Which pathways are enriched?
- Which regulators may explain the module?
- Does the module match known AD biology?
- Which pathology or imaging readouts support it?

Example:

```text
high A beta predicted state
        |
        v
microglial latent factor
        |
        v
top associated genes
        |
        v
complement / lipid-response enrichment
        |
        v
candidate plaque-responsive microglial network
```

## Agentic Interpretation Layer

The agent should consume structured intermediate results, not invent conclusions from raw files.

Expected inputs:

- model metrics
- target prediction tables
- latent factor summaries
- top gene rankings
- pathway enrichment outputs
- candidate regulator tables
- relevant known marker lists

Expected outputs:

- ranked hypotheses
- evidence summaries
- validation suggestions
- caveats and evidence levels
- figure captions and report text

## Future Multimodal Expansion

After the snRNA-seq pilot:

```text
snRNA-seq embeddings
        + neuropathology image features
        + spatial transcriptomics
        + snATAC/regulatory evidence
        |
        v
multimodal latent disease-state space
```

Potential cross-modal prediction tasks:

- predict transcriptomic state from pathology image features
- predict pathology burden from cell-state composition
- predict spatial neighborhood state from local transcriptomic programs
- align snRNA and spatial transcriptomics latent factors
- connect snATAC regulatory programs to expression-derived disease states

