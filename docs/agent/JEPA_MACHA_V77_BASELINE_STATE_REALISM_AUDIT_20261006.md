# JEPA Macha/V77 — baseline synthetic state realism audit

Date: 2026-10-06
Parent audit head before write: `3ed5536e8fe69e071a4fd7194f61208146f0e09a`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Question

Does the current synthetic world already contain a naturally discoverable cell-state program that can stand in for the real class-associated RNA structure behind S157?

## What the generator actually does

B1 creates six synthetic states by a uniform per-cell categorical draw. Each state acts through a 400-address module with mixed positive and negative loadings at scale 0.95. Adjacent state modules partially overlap.

The S157 paired challenge is different. It selects one state and applies a coherent multiplicative effect to a separate 200-address module. With delta 2.0 and beta 0.6, a target-state cell receives about `exp(1.2) ≈ 3.3-fold` multiplicative change on that module, plus the shared challenge noise.

Thus the S157 BIO program is deliberately easier and more coherent than the baseline B1 state structure.

## Evidence

In the S157 NULL world, the chosen state is essentially not linearly recoverable from the top 20 RNA principal components (R2 approximately zero).

Historically, the signed oracle could recover B1 strongly (about 0.864), but that oracle is given the planted module membership and loading signs. It therefore answers a different question: `is the planted state recoverable if I already know where and how to look?`

That historical B1 oracle value was also measured before the S146/S147 support repair, so it is not current repaired-support evidence.

## Current interpretation

`BASELINE_B1_STATE_IS_PLANTED_AND_ORACLE_READABLE__BUT_NATURAL_DISCOVERABILITY_AND_REALISM_ARE_NOT_QUALIFIED`

The S157 challenge validly tests identifiability of a strong planted program, but it does not show that the base V77 world reproduces realistic cell-state organization.

Biological meaning: the simulator contains a hidden cell-state label and gene program, but ordinary RNA variation does not naturally organize around that state the way real cell classes often do. The challenge adds a much cleaner signal so the identifiability test has something strong to detect.

## Consequence for S157

Do not infer from the successful BIO challenge recovery that the simulator has solved the original real-data S157 problem.

The real problem remains:

- real RNA has strong class-associated structure;
- some of that may be biological and some may be measurement-linked;
- current V77 baseline state structure has not been shown to reproduce that balance.

A future S157-realism repair, if pursued, should be judged prospectively against measurement-aware real-data structure and negative controls, not by strengthening B1 until PCA sees it.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object or estimand winner.
