# D1 — JEPA Biological Program Estimation & Ranking Atlas

Status: `PLANNED_PROSPECTIVE_DISCOVERY_LANE__NOT_YET_IMPLEMENTED`

Date: 2026-09-07

## Purpose

D1 is the project's explicit **estimation and biological-discovery layer**.

The existing F1/T0 machinery is primarily designed to decide whether frozen claims qualify under fail-closed rules. D1 has a different purpose: preserve continuous information and turn a mechanically valid trained JEPA teacher into ranked, inspectable biological hypotheses.

D1 must not become another pass/fail qualification gate. It should estimate, rank, localize, annotate, and quantify uncertainty. Confirmatory gates remain a separate downstream layer.

## Entry criteria

D1 implementation may begin outcome-blind now, but real trained-model D1 execution is blocked until all of the following are true:

1. C2 mechanics closure remains valid.
2. The repaired mandatory 48-tensor gradient gate is adopted into the successor training path after unscale and before optimizer step.
3. All 15 F1-B findings have discriminating executable attacks.
4. The repaired F1-B/C3 successor passes those attacks and external review.
5. A mechanically healthy trained teacher checkpoint exists.
6. The checkpoint and all discovery inputs are byte-/root-bound before biological interpretation.

D1 must never consume DEV, SEALED, pathology, reader-oracle, or other protected outcomes unless a separate prospective authority explicitly permits that use.

## Existing project primitives D1 should reuse

D1 is not starting from zero. Reuse rather than redesign:

- Molecular Ledger / 41,238-address identity and observation-state authority.
- 160-D encoder state.
- donor -> matrix -> dataset/study -> technology holdout hierarchy.
- production hierarchical sampling dataset -> donor -> cell.
- donor-aware inference and HC3 machinery.
- T0 continuous cell scoring, donor state score, donor-centering, and extreme-tail construction.
- F1 continuous effect estimates, confidence intervals, source decomposition, query-identity diagnostics, evidence-response estimates, and direct-state comparison.
- measurement-support versus novelty separation.
- exact provenance and replay practices already established in F1/T0/C2.

## Core outputs

For each discovered program/direction, D1 should emit continuous estimates rather than only categorical decisions.

### 1. Program/direction table

At minimum:

- stable program ID;
- direction vector / subspace identity;
- estimated magnitude;
- uncertainty interval;
- donor recurrence;
- source/operator heterogeneity;
- bootstrap / resampling stability;
- split/seed stability;
- relationship to the frozen 160-D basis;
- measurement-support score;
- novelty score;
- redundancy / correlation with other programs;
- representative cells and donors.

### 2. Cell ranking table

For every program:

- canonical cell ID;
- donor;
- source/study/operator;
- raw program score;
- within-donor centered score;
- percentile/rank;
- measurement support;
- uncertainty / stability;
- extreme-tail membership;
- provenance roots.

The full ranking must be retained. Tail membership is a derived view, not a replacement for the continuous score.

### 3. Molecular interpretation table

For every program:

- positively associated genes/addresses;
- negatively associated genes/addresses;
- effect/loadings or other explicit association measure;
- uncertainty/stability;
- fraction physically measured;
- cross-operator support;
- donor recurrence;
- known-program enrichment annotations;
- novelty annotations.

Known pathway/gene-set annotations are interpretive only. They must not define the discovered program retrospectively.

### 4. Donor/source summary

For every program:

- donor-level effect estimates;
- donor recurrence/sign consistency;
- HVS/NPH52/SEA-AD source summaries where applicable;
- operator summaries;
- technology sensitivity;
- estimated biological versus measurement uncertainty.

### 5. Ranked hypothesis catalog

Each candidate hypothesis should include:

- program ID;
- biological description generated from measured molecular evidence;
- magnitude;
- uncertainty;
- donor recurrence;
- source consistency;
- stability;
- novelty;
- measurement support;
- top positive/negative molecular features;
- representative cells;
- known confounder/sensitivity flags;
- claim status: `DISCOVERY_ONLY` unless separately promoted prospectively.

## Discovery versus confirmation firewall

D1 outputs are **discovery estimates**.

A high ranking is not a confirmatory claim.

No D1 ranking threshold may be silently reinterpreted as a qualification threshold. Any later confirmatory test must be prospectively frozen after the D1 hypothesis is selected and must use an appropriate untouched evaluation population.

## Program discovery principles

The exact algorithm remains to be prospectively frozen before real trained-teacher outcomes are inspected, but the method must satisfy:

1. preserve donor identity;
2. avoid leakage from protected outcomes;
3. quantify stability across seeds/splits/resamples;
4. distinguish biological variation from observation/measurement support;
5. preserve the full continuous score distribution;
6. avoid selecting programs solely because of known labels;
7. allow genuinely novel directions;
8. report redundant/near-collinear programs rather than silently double-counting them;
9. audit 160-D basis/subspace stability;
10. preserve all provenance needed to reproduce every ranking.

## Candidate method families to evaluate prospectively

These are method candidates, not yet frozen choices:

- teacher-state PCA/subspace decomposition with stability selection;
- sparse or rotated components for interpretability;
- donor-aware contrast directions;
- program covariance/eigenspace analysis;
- clustering of directionally similar molecular loadings;
- multi-view stability across masks/evidence conditions;
- cell-state neighborhood localization in latent space;
- teacher-minus-u0 / trained-minus-initial representation changes, but only after mechanically healthy training exists.

No nonlinear or shared-context discovery layer should be added merely because it is flexible; it requires evidence and a separate prospective decision.

## Non-goals

D1 does not itself:

- qualify F1-A;
- repair C2/T1;
- prove causality;
- establish pathology validity;
- certify a therapeutic target;
- replace donor-aware confirmatory inference;
- authorize DEV/SEALED/pathology access;
- turn every latent axis into a biological claim.

## First implementation milestone: D1-A

Before real trained-teacher execution, implement a synthetic/u0-safe prototype that can:

1. ingest frozen teacher states and Molecular Ledger identities;
2. compute a candidate low-dimensional program decomposition;
3. output full program, cell, donor, source, and molecular ranking tables;
4. quantify resampling/subspace stability;
5. show that injected synthetic programs are recovered and ranked correctly;
6. distinguish a stable biological signal from a measurement-support artifact;
7. preserve continuous effect estimates and intervals;
8. produce no confirmatory PASS/FAIL terminal.

D1-A is complete only when known-answer synthetic attacks demonstrate both recovery and failure cases.

## Project relationship

Current critical path remains:

`F1-B executable attacks -> repaired F1-B/C3 mechanics -> mechanically healthy teacher -> D1 real estimation/discovery -> prospectively selected biological hypotheses -> confirmatory studies`

D1-A implementation can proceed in parallel with F1-B/C3 because its algorithm can be developed and tested on synthetic/u0-safe inputs without opening protected biology.

## Governance

- Historical F1/T0/C2 bytes remain immutable.
- D1 has its own manifest and review package.
- Real D1 execution must bind the exact teacher checkpoint and all inputs.
- No post-outcome change to ranking formulas, stability criteria, or hypothesis-selection rules without an explicit new prospective version.
