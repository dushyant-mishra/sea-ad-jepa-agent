# Scientific Pitch

## The One-Liner

We are building a pathology-grounded JEPA-agent system that learns Alzheimer disease cell states from SEA-AD and turns them into ranked gene-network hypotheses.

## The Problem

Single-cell atlases are rich, but interpretation often stalls at:

```text
clusters -> marker genes -> enrichment table
```

That is not enough for disease biology. In Alzheimer disease, we need to know whether a molecular state is connected to measured tissue pathology.

The key missing link is:

```text
cell-state program <-> pathology burden <-> candidate mechanism
```

## The Bet

If a microglial expression program consistently predicts AT8/pTau, A beta, Iba1, GFAP, or NeuN pathology across donors, then that program is a better candidate for follow-up than a gene list produced without pathology grounding.

## Why This Is Interesting

This project does not treat SEA-AD as a generic embedding benchmark. It uses pathology as the biological anchor.

The first result already suggests a useful direction:

```text
Microglia-PVM pseudobulk predicts AT8/pTau pathology
Spearman ~= 0.53 across held-out donor folds
```

That means microglial molecular state carries information about tau pathology burden at the donor level.

## Why JEPA Is Worth Trying

Single-cell expression is noisy and sparse. Reconstructing raw counts can overemphasize measurement noise.

JEPA-style learning asks a different question:

```text
Can partial biological context predict latent cell state?
```

That is closer to the scientific goal. We want robust disease-state representations, not perfect reconstruction of every dropout-prone count.

The reason this matters is practical:

```text
good cell-state representation
        -> better donor-level disease features
        -> stronger pathology prediction
        -> clearer gene/module hypotheses
```

If JEPA embeddings do not improve or complement simpler pseudobulk baselines, then the model is not earning its complexity. That comparison is built into the project.

## Why the Agent Matters

The agent is not the model. The agent is the evidence organizer.

It should take:

- pathology prediction metrics
- JEPA latent factors
- gene rankings
- pathway scores
- known Alzheimer biology

and produce:

- ranked hypotheses
- evidence levels
- caveats
- validation suggestions

This makes the output useful to a biologist rather than just technically impressive.

## First Hypothesis Shape

Example output we want:

```text
Hypothesis:
  A Microglia-PVM program associated with AT8/pTau burden reflects a tau-linked inflammatory/lysosomal response.

Evidence:
  - Microglia pseudobulk predicts AT8 pathology in held-out donors.
  - Top associated genes include inflammatory and stress-response candidates.
  - Candidate genes can be checked against spatial proximity to AT8 pathology.

Validation:
  - Test whether the gene module is enriched near AT8-positive regions.
  - Compare with Iba1 activation and plaque/tau co-localization.
  - Prioritize markers for IHC/IF or spatial transcriptomics follow-up.
```

## What Success Looks Like

Short term:

- reliable Microglia-PVM pathology prediction
- interpretable AT8/A beta/Iba1/GFAP/NeuN gene rankings
- JEPA embeddings that improve or complement pseudobulk baselines

Medium term:

- pathway-aware JEPA masking
- mixed random/module-aware JEPA masking for microglia biology
- latent factor interpretation
- spatial validation with SEA-AD spatial transcriptomics
- agent-generated hypothesis reports

Long term:

- multimodal latent disease-state model spanning transcriptomics, pathology, spatial context, imaging, and regulatory evidence

## What We Will Not Claim Prematurely

We will not claim causality from correlation.

Evidence levels must remain explicit:

```text
association -> prediction -> regulatory candidate -> perturbational support -> validation
```

That discipline is part of the value of the project.
