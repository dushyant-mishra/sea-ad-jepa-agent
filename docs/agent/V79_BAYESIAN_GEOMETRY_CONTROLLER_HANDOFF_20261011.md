# V79 Bayesian Geometry Controller Handoff — 2026-10-11

## Purpose

This document is for the supervising agent. Always inspect Macha's live source branch before issuing state-dependent instructions.

## Canonical lane

Source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`

Audit PR: #260

Handoff PR: #261

Latest live source head reconciled by the controller: `ea0102132eb25b3d282988181c95387bf4f57ff6`

Latest reconciliation: `docs/agent/V79_BAYESIAN_GEOMETRY_CONTROLLER_RECONCILIATION_20261011_R2.md`

Current terminal state: `SIMULATION_QUALIFICATION_INCOMPLETE`

## Current Bernoulli ruling

The live provenance map claims Bernoulli S0, S1 and S5 are completed. However, the actual completed Bernoulli result JSON payloads are not committed at the expected recovery paths on the live branch, so final R-hat, ESS, divergences, recovery values and A5 status cannot yet be independently audited from GitHub.

Bernoulli S2 and S3 were killed in the earlier oversubscribed run and require completion under the bounded scheduler. S4 remains running from an equivalent earlier snapshot.

Therefore Bernoulli is **not freeze-ready**.

Next Bernoulli instruction:
1. commit completed S0/S1/S5 JSON payloads;
2. explicitly record whether A5 extension was needed and commit the final post-extension result if used;
3. finish S2/S3/S4 under the bounded scheduler/equivalent frozen snapshot;
4. commit all six S0-S5 records plus one combined recovery receipt;
5. freeze Bernoulli only if all preregistered recovery/convergence criteria pass.

Do not start corrected TRAIN yet.

## Qualification order

1. complete and independently audit Bernoulli recovery;
2. finish Gaussian recovery;
3. finish log-normal recovery;
4. finish ZTNB recovery;
5. freeze compute benchmark;
6. begin corrected-TRAIN fits only after simulation gates pass;
7. run held-out PPC and Q5 donor×class adjudication;
8. adjudicate positive-count family;
9. build biology geometry authority;
10. build observation geometry authority;
11. complete self-audit and independent downstream audit.

## Scientific integration policy

Build the richest defensible probabilistic generative model of corrected TRAIN. Preserve posterior distributions and uncertainty where useful.

Biology-side qualified posterior geometry may prospectively parameterize H1. Observation-side qualified posterior geometry may prospectively parameterize H2. H3 composes the independently qualified layers.

Protect identity, not geometry. The desired product is:

`real statistical geometry + synthetic causal identity`

Do not transfer exact real gene-to-program assignments, named pathways/regulons, exact class×gene signatures, exact donor×gene signatures, target-discovery ranks/panels, SCENIC+/ATAC target evidence, pathology-derived effects, TEST/Morabito information, or winner information into planted causal truth.

## Variable semantics

Do not collapse broad class, donor, donor×class, source, measurement operator, and depth/capture into one generic batch variable. Source may mix biology and measurement. Operator is a measurement axis. Donor carries biology. Depth can be downstream of both biology and measurement.

Posterior association is not automatically causal identification.

## Real-data acceptance requirements

After simulation qualification and benchmark freeze, corrected-TRAIN fitting must satisfy convergence and held-out posterior predictive checks covering at least:
- library size;
- detected genes/cell;
- gene detection prevalence;
- positive-count abundance and tails;
- dispersion;
- signed detection correlation structure;
- degree/transitivity/eigenspectrum;
- class/depth/source/operator-conditioned structure;
- positive-expression covariance;
- class, donor, donor×class, source, operator and residual effect spreads.

Q5 must adjudicate whether donor×class materially improves held-out prediction. Do not keep it only because the richer training fit looks better.

## Required terminal authorities

Macha's final qualified package must include separate generator-consumable biology and observation geometry authorities. Each must record schema/version, source SHA, authenticated corrected-TRAIN custody, model family, posterior draw/subsample policy, uncertainty representation, deterministic hashes, absence of forbidden identity fields, and `training_authorized=false`.

A narrative report alone is not enough.

## Fixed prohibitions

Until separately authorized:
- no TEST/Morabito;
- no pathology;
- no target-discovery ranks or panels;
- no SCENIC+/ATAC target evidence;
- no target or representation winner information;
- no Stage4/500K;
- no V78 outcome-driven retuning;
- no JEPA training/checkpoint generation;
- no provisional Bayesian outputs consumed by the factorial lane;
- no post-outcome synthetic-arm rescue.

## Qualified terminal label

Use `BAYESIAN_GEOMETRY_QUALIFIED_FOR_SYNTHETIC_INTEGRATION` only after all required simulation recovery suites pass, parameterizations and benchmark are frozen, corrected-TRAIN fits and convergence diagnostics are complete, held-out PPC and Q5 are adjudicated, count family is ruled, biology and observation authorities exist with exact hashes, self-audit is complete, and `training_authorized=false`.
