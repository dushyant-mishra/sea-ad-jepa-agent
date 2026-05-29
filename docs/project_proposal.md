# Project Proposal

## Title

Multimodal JEPA-Agent Framework for Alzheimer Disease Gene Network Discovery

## One-Sentence Summary

This project aims to learn robust latent disease-state representations from SEA-AD single-nucleus transcriptomics and neuropathology data, then use an agentic transformer layer to generate interpretable, evidence-aware Alzheimer disease gene-network hypotheses.

## Motivation

Gene network discovery in neurodegeneration is difficult because each data modality observes only part of the disease process.

Single-nucleus RNA-seq captures cell-type and cell-state expression programs, but it is sparse, noisy, and affected by donor and technical variation. Neuropathology and immunostaining capture tissue-level disease burden, but they often lack direct genome-wide molecular resolution. Spatial and imaging data preserve tissue context, but they can be difficult to connect to regulatory mechanisms.

The central premise of this project is that a JEPA-style predictive representation model can learn a stable biological state space across noisy observations, while a transformer-based agent can orchestrate downstream analysis and translate latent states into testable biological hypotheses.

The goal is not to build a chatbot over biological data. The goal is to build a biological discovery system where:

```text
single-cell molecular state
        + pathology burden
        + spatial/imaging context
        -> latent disease-state representation
        -> candidate gene networks
        -> ranked hypotheses and validation experiments
```

## Why SEA-AD

SEA-AD is a strong starting dataset because it is public, disease-focused, and multimodal. It includes processed single-nucleus profiling, donor metadata, quantitative neuropathology, and spatial transcriptomics resources focused on Alzheimer disease progression.

This makes SEA-AD useful for asking questions that go beyond cell-type classification:

- Which latent cell states track Alzheimer pathology burden?
- Which microglial, astrocytic, and neuronal programs are associated with A beta, pTau, gliosis, or neuronal loss?
- Can transcriptomic state predict donor-level neuropathology?
- Can pathology-associated latent factors be translated into candidate gene modules or regulators?
- Which outputs deserve follow-up with IHC, IF, spatial transcriptomics, or perturbation experiments?

## First Biological Question

The first pilot question is:

> Can transcriptomic cell-state embeddings learned from SEA-AD MTG nuclei predict donor-level neuropathology burden and reveal candidate AD-associated gene networks?

The first pathology targets are:

- 6e10/A beta plaque burden
- AT8/pTau burden
- GFAP/reactive astrocyte burden
- Iba1 and activated Iba1 microglial burden
- NeuN neuronal signal and density
- Biochemical amyloid and tau measures

## Initial Cell Populations

The first model will focus on a manageable subset rather than the entire atlas.

Microglia are a natural first target because they are central to AD inflammation, plaque response, and known genetic risk pathways such as APOE, TREM2, TYROBP, and complement signaling.

Astrocytes are the second target because GFAP pathology gives a direct tissue-level readout of reactive gliosis.

Excitatory neurons are the third target because neuronal vulnerability and loss are central to disease progression, and NeuN gives a tissue-level neuronal readout.

## Proposed System

The long-term system has three layers.

### 1. Representation Learning Layer

The JEPA model learns latent biological states by predicting target embeddings from context embeddings.

For snRNA-seq, the context could be a subset of genes or gene modules, and the target could be a held-out gene module embedding or a full-cell latent embedding.

For imaging and pathology, the context could be tissue regions or stain-derived features, and the target could be transcriptomic or pathology embeddings.

The key idea is to avoid reconstructing every raw count or pixel. Instead, the model learns predictive biological structure.

### 2. Gene Network Discovery Layer

The learned embeddings are connected to downstream biological interpretation:

- disease-state clustering
- pathology prediction
- gene-module extraction
- pathway enrichment
- candidate transcription factor or regulator ranking
- cross-modal validation with pathology, spatial transcriptomics, or imaging

### 3. Agentic Transformer Layer

The agentic layer does not replace the discovery model. It coordinates and explains the analysis.

Example tasks:

- Select pathology-associated latent factors.
- Extract top genes or modules linked to those factors.
- Run enrichment analysis.
- Compare candidates to known AD biology.
- Rank hypotheses by evidence level.
- Suggest IHC, IF, spatial, or perturbation validation.
- Produce figure-ready summaries.

## Minimum Viable Demonstration

The first useful demo is deliberately narrow:

```text
SEA-AD MTG snRNA-seq
        -> pilot subset by cell population
        -> JEPA-style latent embeddings
        -> donor-level aggregation
        -> pathology prediction
        -> gene-module/regulator hypotheses
```

Success for the first demo means:

- The pipeline can load and subset SEA-AD processed AnnData.
- The model learns embeddings that preserve cell identity and donor structure.
- Aggregated embeddings predict one or more pathology targets better than simple baselines.
- Pathology-associated latent factors yield biologically plausible genes and pathways.
- The outputs can be described as ranked hypotheses rather than unsupported causal claims.

## Scientific Caution

The framework should not claim causality from association alone.

If a latent microglial state is associated with A beta burden, the correct claim is:

```text
This state is associated with, and may predict, A beta burden.
```

It is not automatically correct to claim:

```text
This state causes A beta burden.
```

The documentation, reports, and agent outputs should separate evidence levels:

- association
- held-out prediction
- regulatory candidate
- perturbational support
- experimental validation

## Long-Term Vision

After the snRNA-seq plus neuropathology pilot works, the framework can expand to:

- SEA-AD spatial transcriptomics
- neuropathology image-derived features
- IHC/IF validation marker selection
- snATAC regulatory evidence
- external perturbation datasets such as LINCS or JUMP Cell Painting
- literature-aware agentic hypothesis ranking

The final research story is a multimodal biological discovery system that learns disease-state representations from SEA-AD and helps convert them into testable gene-network hypotheses.

