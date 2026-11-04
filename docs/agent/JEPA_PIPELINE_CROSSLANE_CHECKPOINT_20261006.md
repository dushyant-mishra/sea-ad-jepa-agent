# JEPA pipeline cross-lane checkpoint — 2026-10-06

## Purpose

This checkpoint records the current three-lane project state for takeover continuity. It does not grant training, Stage-A, production-world, or target-selection authority.

## Lane A — runtime reconciliation (this chat/agent)

Active branch: `reconcile/v64-runtime-authority-onto-main-20261006`.

Scope remains runtime-only: recover/adapt historical V64 authority and optimizer-guard semantics into the current V5 path; exhaustively map optimizer/EMA/checkpoint mutation routes; add RED bypass tests before runtime implementation; keep training disabled and `main` untouched.

Canonical intended ordering remains:

`authenticated/q-safe 41K input -> encoder -> predictor -> EMA teacher -> loss -> backward -> CurrentTrainingAuthorityV2 -> OptimizerGuardV4 -> guarded optimizer step -> completion assertion -> EMA -> authority-bound checkpoint -> deterministic reload`

Key invariant: gradient validation occurs after unscaling and before stepping; EMA may advance only after a successfully proven optimizer mutation. Rejected, skipped, ambiguous, overflowed, or incomplete steps must not advance EMA.

## Lane B — Macha V77 synthetic qualification

Scientific baseline: `d76631b6d5f2f6cbf9ae57e202d9b38c4c400b32`.

Current decision remains:

`SUPPORTED_FOR_NEXT_STAGE__WITH_TWO_NAMED_UNRESOLVED_ISSUES`

### Settled findings

- A_REPLICA was prospectively frozen before the current family and passed with a 50-PC unsupervised readout: recoverable ~0.9821, non-recoverable ~-0.0012.
- The current sub-state/block-switching family can generate near-clique latent structure (latent transitivity ~0.965-0.9999).
- With the revised observation process, observed transitivity reached 0.8844 within the frozen real envelope [0.8752, 0.8928]; mean degree 1855.9 vs 1843.8 real; fraction |corr|>0.3 0.6188 vs 0.6148 real.
- The exact per-cell detected-gene-count constraint was a major observer defect. Removing it substantially increased observed covariance topology.
- Historical failure of 37 factor/hurdle candidates must not be treated as clean evidence that the latent generator alone was the fundamental problem, because the same observer ceiling affected multiple latent families.
- T5 remained held; hidden sub-states are generated independently of annotated class, preventing known-class separation from explaining the structure.

### Open Issue 1 — HIGH

Abundance and detection/capture remain incorrectly coupled. Full abundance spread approximately preserves the real abundance marginal but loses topology; narrowing abundance to ~0.3 preserves topology but destroys the abundance marginal (e.g. max/median and top-1% share collapse). One scalar cannot satisfy both.

Next discriminating experiment: hold the sub-state generator fixed and decouple latent biological abundance from gene/cell capture and stochastic observation. Detected-gene count must remain an outcome, not a forced input. Prospectively freeze the observer candidate roster and real-data abundance acceptance region before evaluating candidates.

### Open Issue 2 — MEDIUM

Positive/negative correlation balance and largest-community fraction remain mismatched. Existing levers include module number/size, sign structure, independent-gene fraction, and lawful selection noise. They must be calibrated jointly only after Issue 1 closes, while retaining transitivity and T5.

### Authority limits

No production generator freeze. No production 100K world rebuild. No target selection. No JEPA training. A prior 100K control/qualification computation exists and must be distinguished from an unauthorized production-world rebuild.

## Lane C — real-data premise/qualification governance

PR #220 was merged to `main` at `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777` as governance/prefreeze only.

This lane governs future real-data work: representation-family competition, observation-operator semantics, estimands, stability, biological-evidence vs sequencing-depth uncertainty, external validation, and Stage-A gates.

The merge explicitly does not authorize Stage A, JEPA training, multimodal training, 500K, Stage 4, TEST opening, or Morabito opening.

## Cross-lane interpretation

The three lanes are distinct and none authorizes another:

1. Runtime reconciliation establishes whether the training machinery is authority-bound, bypass-resistant, EMA-safe, and deterministically restartable.
2. Macha synthetic qualification establishes whether a controlled synthetic world can reproduce critical real-data structure without cheating.
3. Premise/qualification governance establishes which scientific questions, representations, uncertainty operators, estimands, and external evidence are legitimate for future real-data work.

A pass in any one lane does not grant production training authority.
