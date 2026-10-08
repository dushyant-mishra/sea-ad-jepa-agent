# FULL104 nonlinear masking challenge successor — 2026-09-18

Status: implementation ready for prospective numeric binding; terminal outcomes unopened; training off.

Historical exploratory work established that a tree-based nonlinear expression
attacker was useful as a secondary challenge. That finding is retained as
design context only.

The current successor does not import the historical 6,000-address matrix,
15% or 900-address burden, 32-target panel, fixed discovery target positions,
or discovery seed. It keeps only the scientific role: train-donor-only
screening, tree-ensemble challenge, held-donor evaluation, and reporting
without policy retuning.

Every runtime-sensitive model setting and the per-donor row cap are explicit in
NonlinearMaskingChallengeAuthorityV1. There are no production defaults. A
concrete instance must be chosen from an outcome-blind runtime/capacity
benchmark and frozen before terminal masking outcomes.

Sampling is deterministic within donor, and each donor receives equal total fit
weight so large donors cannot dominate merely because they contain more cells.
