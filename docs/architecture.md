# Architecture

## The Discovery Loop

The architecture is organized around a biological discovery loop, not around a single model.

The system should repeatedly answer:

```text
What cell state predicts pathology?
What genes explain that state?
What evidence supports the hypothesis?
What validation should come next?
```

```text
SEA-AD molecular data
        |
        v
cell-state learning
        |
        v
pathology-grounded prediction
        |
        v
gene/module ranking
        |
        v
evidence-aware hypothesis report
```

## Current Data Flow

```text
SEA-AD donor metadata
        |
        v
donor-level covariates

SEA-AD MTG neuropathology
        |
        v
A beta, pTau, GFAP, Iba1, NeuN targets

SEA-AD MTG snRNA-seq
        |
        v
Microglia-PVM cell-level pilot
        |
        v
JEPA cell-state embeddings
        |
        v
donor-level aggregation
        |
        v
pathology prediction
        |
        v
gene ranking and hypothesis generation
```

## Layer 1: Representation Learning

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

In the first implementation, JEPA is deliberately simple: an MLP context encoder, an MLP target encoder, and a predictor head. That is enough to test whether the representation-learning loop works before adding transformers, pathway-aware masking, or multimodal objectives.

## Layer 2: Pathology-Grounded Evaluation

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

Cell-level splits would leak donor pathology information and overstate performance.

This layer is what makes the project biologically grounded. A representation is useful only if it helps explain measured disease burden, not merely because it separates known cell labels.

## Layer 3: Gene Network Discovery

Once a cell-state feature is associated with pathology, the analysis layer asks:

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

The first implementation ranks genes by donor-level pseudobulk association with pathology. Later versions should add regulon inference, pathway enrichment, and spatial validation.

## Layer 4: Agentic Interpretation

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

The agent is intentionally downstream of the quantitative analysis. Its role is to organize evidence, expose caveats, and propose the next experiment.

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
