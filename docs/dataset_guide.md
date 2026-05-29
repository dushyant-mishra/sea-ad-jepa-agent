# Dataset Guide

## Overview

This project currently uses data from the **Seattle Alzheimer Disease Brain Cell Atlas (SEA-AD)**.

SEA-AD is a public human brain atlas focused on Alzheimer disease progression. It includes molecular, cellular, spatial, and neuropathology measurements from postmortem human brain tissue. The aim of the dataset is to help researchers understand how different brain cell types change across Alzheimer disease and related pathology.

In this project, SEA-AD is used for one specific purpose:

```text
connect cell-type-specific gene expression programs to measured Alzheimer neuropathology
```

The first pilot focuses on:

```text
Brain region: middle temporal gyrus
Cell population: Microglia-PVM
Molecular assay: single-nucleus RNA-seq
Pathology targets: AT8/pTau, 6e10/A beta, Iba1, GFAP, NeuN, biochemical amyloid/tau
```

## Dataset Components Used

### 1. Donor Metadata

File:

```text
sea-ad_cohort_donor_metadata_072524.xlsx
```

This file describes the human donors included in SEA-AD.

Important fields include:

- donor ID
- age at death
- sex
- cognitive status
- APOE genotype
- Braak stage
- Thal phase
- CERAD score
- overall Alzheimer disease neuropathologic change
- continuous pseudo-progression score

Why it matters:

Donor metadata lets us connect cell-level molecular data to donor-level disease state and pathology burden.

### 2. Quantitative Neuropathology Metadata

File:

```text
sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv
```

This file contains donor-level quantitative pathology measurements from the middle temporal gyrus.

Important target families include:

- AT8/pTau pathology
- 6e10/A beta pathology
- GFAP astrocyte signal
- Iba1 microglia signal
- NeuN neuronal signal
- biochemical amyloid and tau measurements

Why it matters:

These measurements are the biological targets. We use them to ask whether a cell population's gene-expression state predicts real tissue pathology.

### 3. SEA-AD MTG Single-Nucleus RNA-seq

File:

```text
SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

This is the main expression matrix.

It contains:

- nuclei/cells as rows
- genes as columns
- gene-expression counts
- donor labels
- cell class, subclass, and supertype labels
- disease and donor metadata copied into the cell metadata

Why it matters:

This file lets us isolate a cell population such as Microglia-PVM and study its gene-expression programs across donors.

## Current Biological Pilot

The current pilot uses **Microglia-PVM** cells from the SEA-AD MTG snRNA-seq file.

The workflow is:

```text
full SEA-AD MTG snRNA-seq
        -> select Microglia-PVM cells
        -> build donor-level pseudobulk expression
        -> predict donor-level pathology
        -> rank genes associated with pathology
        -> train JEPA on cell-level microglia expression
```

## Why Microglia-PVM

Microglia are resident immune cells of the brain. They are deeply involved in Alzheimer disease biology, including:

- response to amyloid plaques
- inflammatory signaling
- complement activation
- lipid metabolism
- phagocytosis
- lysosomal activity
- interaction with tau and neurodegeneration

PVM stands for **perivascular macrophages**. In the SEA-AD annotation, `Microglia-PVM` groups microglia and closely related perivascular macrophage-like cells.

This population is a strong first target because many Alzheimer-associated genes and pathways are active in microglial biology.

## Abbreviations and Terms

### AD

**Alzheimer disease.**

The neurodegenerative disease focus of this project.

### SEA-AD

**Seattle Alzheimer Disease Brain Cell Atlas.**

A public atlas of human brain molecular and pathology data across Alzheimer disease progression.

### MTG

**Middle temporal gyrus.**

A brain region affected in Alzheimer disease and used prominently in SEA-AD.

### snRNA-seq

**Single-nucleus RNA sequencing.**

A sequencing assay that measures gene expression from individual nuclei. It is commonly used for frozen human brain tissue.

### RNA-seq

**RNA sequencing.**

A broad term for sequencing RNA to measure gene expression.

### AnnData / H5AD

**AnnData** is a common data structure for single-cell analysis.

**H5AD** is the file format used to store AnnData objects.

In this project, the large `.h5ad` file stores the SEA-AD MTG expression matrix and cell metadata.

### Pseudobulk

A donor-level summary made by aggregating single-cell expression values within a cell population.

For example:

```text
all Microglia-PVM cells from donor X
        -> average expression per gene
        -> donor X Microglia-PVM pseudobulk profile
```

Pseudobulk is useful because pathology labels are donor-level, not cell-level.

### Microglia

Resident immune cells of the central nervous system.

They respond to injury, plaques, inflammation, and neurodegenerative changes.

### PVM

**Perivascular macrophage.**

An immune cell population associated with blood vessels in the brain.

### AT8

An antibody commonly used to detect abnormal phosphorylated tau pathology.

In this project, AT8 measures are treated as tau-pathology readouts.

### pTau

**Phosphorylated tau.**

Tau is a protein that forms neurofibrillary tangles in Alzheimer disease. Phosphorylated tau is a disease-associated tau form.

### A beta / Abeta / Aβ

**Amyloid beta.**

A peptide that forms amyloid plaques in Alzheimer disease.

This repository uses plain ASCII spelling `A beta` in most documentation for readability and compatibility.

### 6e10

An antibody used to detect amyloid beta pathology.

SEA-AD includes quantitative 6e10-positive pathology measurements.

### GFAP

**Glial fibrillary acidic protein.**

A marker of astrocytes and reactive gliosis.

### Iba1

**Ionized calcium-binding adapter molecule 1.**

A marker commonly used for microglia/macrophage staining.

### NeuN

**Neuronal nuclei marker.**

A marker used to identify neurons and estimate neuronal signal or density.

### APOE

**Apolipoprotein E.**

A major Alzheimer disease risk gene, especially the APOE4 allele.

### TREM2

**Triggering receptor expressed on myeloid cells 2.**

A microglial gene strongly linked to Alzheimer disease risk and microglial response states.

### JEPA

**Joint Embedding Predictive Architecture.**

A representation-learning approach where a model predicts latent embeddings rather than reconstructing raw inputs.

In this project, JEPA is used to learn disease-relevant cell-state embeddings from gene expression.

### C-JEPA

**Contrastive Joint Embedding Predictive Architecture.**

A JEPA variant that adds additional regularization or contrastive-style structure to stabilize learned representations.

### GRN

**Gene regulatory network.**

A network describing relationships among genes, transcription factors, regulatory programs, and biological pathways.

### IHC

**Immunohistochemistry.**

A staining method that uses antibodies to detect proteins in tissue sections.

### IF

**Immunofluorescence.**

An antibody-based staining method where fluorescent labels are used to visualize proteins or cell markers.

### Spatial Transcriptomics

Methods that measure gene expression while preserving spatial location in tissue.

For this project, spatial transcriptomics is a future validation layer.

## How the Pieces Fit Together

```text
Donor metadata
        |
        v
disease and covariate context

Quantitative neuropathology
        |
        v
pathology targets

snRNA-seq expression
        |
        v
cell-type-specific molecular state

Microglia-PVM pseudobulk / JEPA embeddings
        |
        v
pathology prediction
        |
        v
gene ranking and hypothesis generation
```

## Current Takeaway

The first Microglia-PVM baseline suggests that microglial expression carries donor-level signal for AT8/pTau pathology. This does not prove causality, but it gives a grounded starting point for gene-module discovery and validation.

