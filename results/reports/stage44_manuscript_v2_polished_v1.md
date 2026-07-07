# Conservative donor-held-out benchmarking separates robust and non-lockable signals in SEA-AD pathology prediction

## Abstract

We present a claim-bounded SEA-AD pathology prediction benchmark that separates locked internal evidence from non-lockable but informative signals. Stage27C remains the official locked internal benchmark (mean pooled OOF Spearman 0.3267024400121495). Stage41C is the best credible unlocked signal (0.36808747595423713) but is not locked because its bootstrap lower 95% CI (0.2603604646376338) falls below Stage27C. Stage45 successfully acquired donor-linked CELLxGENE metadata and engineered MRI features but did not improve performance (0.3121433633694442). External resources are treated as support/readiness only. The manuscript preserves negative and non-testable results and makes no claims of external validation; clean validation; causality; therapeutic relevance; gene-ablation validation; disease-modifying effects.

## Introduction

Small donor cohorts make benchmark discipline essential. This study uses fixed donor-held-out evaluation, strict lock rules, and explicit claim boundaries to distinguish robust internal benchmarks from exploratory signals.

## Methods

We used donor-held-out folds, pooled OOF Spearman, target-level guards, bootstrap confidence intervals, negative controls, proxy/leakage audits, and feature risk tiers. Stage45 incorporated metadata-only CELLxGENE donor composition and engineered MRI features while excluding diagnosis, cognitive, pathology, Luminex, Braak/CERAD/Thal/ADNC, same-stain, HALO, pseudo-label, and target-derived predictors.

## Results

Stage27C remained the locked internal benchmark. Multiple rescue attempts did not meet lock criteria. Stage41C produced the best credible unlocked signal but failed the CI lock gate. Stage45 showed that successful donor-linked CELLxGENE/MRI acquisition did not rescue performance. Frozen mechanisms remain hypothesis-generating, and external support remains readiness-only.

## Discussion

The central contribution is a safeguarded benchmark narrative: robust locked evidence is separated from credible-but-unlocked signal and from negative acquisition results. Future gains likely require genuinely new donor-linked spatial or non-target morphology features rather than further model tuning.

## Limitations

Limitations include small donor count, bootstrap instability, limited external dataset compatibility, metadata proxy risk, no clean external validation, no causal inference, and no therapeutic interpretation.

## Data and code availability

Committed summary tables, scripts, and reports are available in the project repository. Raw downloaded data and local metadata are intentionally not committed.

## Author contributions placeholder

TBD.

## Conflict of interest placeholder

TBD.

## Claim boundary statement

Stage27C remains locked; Stage41C is not locked; Stage45 is not an improvement. No external validation; clean validation; causality; therapeutic relevance; gene-ablation validation; disease-modifying effects is claimed.
