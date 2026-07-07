# Conservative donor-held-out benchmarking separates robust and non-lockable signals in SEA-AD pathology prediction

## Title options

1. Conservative donor-held-out benchmarking separates robust and non-lockable signals in SEA-AD pathology prediction
2. A safeguarded SEA-AD benchmark framework for Alzheimer pathology prediction and hypothesis support
3. Claim-bounded multimodal benchmarking of SEA-AD pathology-associated readouts

## Abstract

We developed a safeguarded internal benchmark framework for SEA-AD pathology-associated readouts. Stage27C remains the locked internal donor-held-out benchmark with mean pooled OOF Spearman 0.3267024400121495. Stage41C produced a stronger credible internal signal (0.36808747595423713) but was not locked because its bootstrap lower 95% CI (0.2603604646376338) remained below Stage27C. Stage45 successfully acquired donor-linked CELLxGENE metadata with exact 84/84 overlap and built seven safe feature matrices, but the best Stage45 candidate scored 0.3121433633694442 and did not improve over Stage27C or Stage41C. External data are treated as support/readiness only. No causal, therapeutic, gene-ablation, disease-modifying, external-validation, or clean-validation claim is made.

## Introduction

Alzheimer disease modeling workflows can overstate unstable point estimates, especially in small donor cohorts. We therefore separated locked internal benchmark evidence from credible but unlocked signals and support/readiness analyses.

## Methods

We used donor-held-out folds, pooled OOF Spearman, target-level guards, bootstrap lock criteria, negative controls, proxy/leakage audits, and feature risk tiers. Stage45 added CELLxGENE metadata composition and engineered MRI features without using diagnosis, pathology, Luminex, Braak/CERAD/Thal/ADNC, same-stain, HALO, pseudo-label, or held-out target-derived predictors.

## Results

### Locked internal benchmark and scoring framework

Stage27C remained the official locked benchmark.

### Rescue attempts identified instability and proxy risk

Graph, neural, external pretraining, and auxiliary-head branches did not produce a lockable replacement.

### Stage41 safe metadata/latent blending improved point estimate but failed lock CI

Stage41C reached 0.36808747595423713 but remained credible-unlocked because the lower CI was 0.2603604646376338.

### Stage45 acquired donor-linked CELLxGENE features but did not improve performance

Stage45 achieved exact donor linkage and built seven matrices, but the best result was 0.3121433633694442.

### Frozen mechanisms remain hypothesis-generating

Mechanism bins are retained only as hypothesis-generating anchors.

### External support/readiness remains limited

External resources are readiness/support context only.

### Claim-boundary framework preserves negative and non-testable results

Negative, null, and not-testable results are explicitly preserved.

## Discussion

The project identifies a robust locked baseline and a stronger but unstable internal signal. The Stage45 negative result suggests simple composition and volumetric features are insufficient. Future work should prioritize genuinely new donor-linked spatial or non-target image morphology features rather than additional score-chasing.

## Limitations

Small donor count, bootstrap instability, external dataset incompatibility, metadata proxy risk, no clean external validation, no causal inference, and no therapeutic validation.

## Data/code availability draft

Code and committed summary artifacts are available in the project repository. Raw data and downloaded metadata remain uncommitted local files.

## Author contributions

TBD.

## Conflict of interest

TBD.

## Claim boundary statement

This manuscript reports internal donor-held-out benchmarking and support/readiness synthesis only. external validation; clean validation; causal mechanism; therapeutic target; gene-ablation support; disease-modifying effect are not claimed.
