# JEPA target-discovery Bayesian replication spike — preregistration

Date: 2026-10-09

Status: `SPIKE_PREREGISTERED__HISTORICAL_ONLY__NON_AUTHORIZING__NO_CORRECTED_REPLAY_INGESTED`

## Purpose

Test whether a dependency-aware Bayesian hierarchical replication model can recover the qualitative structure of the historical relational target-discovery evidence without being told the historical PASS/FAIL labels and without treating related source/panel/split cases as independent evidence.

This is a throwaway scientific-method spike. It is not production target-discovery infrastructure and creates no target, representation, TD60, Stage 4, model, EMA, or training authority.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Frozen probe question

Can a skeptical hierarchical model fitted to historical TD57B, TD57C, and TD59 case-level margins over their frozen null/comparator produce calibrated posterior and posterior-predictive summaries that distinguish strong recurrent evidence, failure/weak evidence, and marginal evidence without using the historical verdict labels during fitting?

Historical verdicts are withheld from fitting and are consulted only after the posterior summaries are produced as an external sanity check.

## Input authority

Primary historical archive:

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

Exact SHA-256 already bound by the target-discovery custody lane:

`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

The archive has been materialized read-only for this spike. No corrected TD replay output from the current G4-G7 implementation lane has been ingested.

## Evidence unit

The probe will use the finest authenticated historical case-level statistic available without inventing pseudo-replicates. Candidate dimensions include:

- stage: TD57B / TD57C / TD59;
- source: HVS / NPH52 / SEA_AD;
- panel;
- donor split / half where explicitly present;
- observed statistic;
- frozen null/comparator statistic;
- margin = observed - frozen comparator;
- authenticated gene/pair/panel identity hashes where available.

If the historical artifacts do not expose a claimed dimension, the spike must not synthesize or infer it.

## Dependency rule

Cases sharing biological samples, substrate, source, panel construction, or other frozen scientific material must not be counted as independent merely because they occupy separate rows.

The exploratory ledger will therefore record, where available:

- source;
- panel/view;
- split/half;
- cell/sample/substrate identity root;
- gene/pair identity root;
- producer/result identity.

The model may partially pool across cases but must not multiply confidence by pretending correlated repeated analyses are independent experiments.

## Planned model family

Initial model is deliberately simple and skeptical.

For case-level margin `y_i`:

`y_i ~ StudentT(nu, mu_stage[i] + source_effect + panel_effect, sigma)`

with zero-centered weakly informative priors and positive half-normal/half-t priors for heterogeneity scales. Exact numerical prior scales will be set from the historical margin scale only through a label-blind scale summary; no historical PASS/FAIL label or corrected replay result may tune a prior.

Primary exploratory outputs:

- posterior probability that the latent stage-level margin is > 0;
- posterior stage-level effect distribution;
- source heterogeneity posterior;
- panel/split heterogeneity where estimable;
- posterior predictive probability of a positive margin in a new case drawn from the same stage hierarchy;
- posterior predictive distribution for an unseen source/case under the model assumptions.

No target-level posterior is permitted in this spike.

## Calibration / falsification checks

Before interpreting historical results, the spike must include synthetic controls that test at minimum:

1. null margins centered at zero do not generate high replication confidence;
2. one-source-only positive signal is not mistaken for source-general replication;
3. duplicated rows do not create proportional certainty inflation when dependency grouping identifies them as duplicates;
4. heterogeneous sign-flipping sources produce high heterogeneity / low predictive replication confidence;
5. genuinely shared positive signal is recoverable;
6. posterior conclusions are reported under at least three reasonable prior scales.

If conclusions are materially prior-sensitive, terminal label is `PRIOR_SENSITIVE` rather than a positive scientific claim.

## Historical adjudication firewall

The model cannot change historical stage dispositions.

In particular:

- TD57B historical prospective PASS remains historical evidence only;
- TD57C historical frozen failure remains `NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL` regardless of any exploratory posterior;
- TD59 remains historical statistic/evidence without production locality or training authority;
- corrected replay, when available, is a distinct future evidence object and may not be used to retroactively relabel the historical experiments.

## Corrected replay firewall

Macha currently owns the value-blind G4/G5 local preflight for the corrected relational replay lane. This Bayesian spike must not consume any corrected replay outcome before the exploratory model definition and synthetic calibration are complete.

No G6/G7 value-read authorization is created by this document.

## Success criterion for the spike

The spike is useful only if all of the following hold:

- historical evidence can be represented without invented pseudo-replicates;
- synthetic calibration behaves sensibly;
- duplicate/dependent evidence does not inflate confidence materially;
- posterior predictive summaries are interpretable in the native TD evidence geometry;
- prior sensitivity is acceptable and explicitly reported;
- historical labels are not used in fitting.

If those conditions fail, stop and report that this Bayesian formulation is unsuitable for the target-discovery evidence rather than tuning it until it reproduces desired historical conclusions.

## Repository / authority status

This preregistration belongs to draft PR #243 as a non-authorizing method sidecar. It does not modify the frozen G1-G7 corrected replay implementation and does not alter the role of PR #237 as custody/scientific-history base.
