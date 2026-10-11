# V79 Bayesian Geometry Controller Handoff — 2026-10-11

## Purpose

This document is for the next supervising agent, not for Macha directly. It explains how to assess Macha's Bayesian dataset-geometry lane, when to let him advance, what evidence must be checked before issuing new instructions, and how his final qualified posterior-generative artifacts should be integrated into the factorial synthetic-world lane.

## Canonical lane identity

Source branch:
`analysis/v79-bayesian-synthetic-geometry-20261009`

Audited source snapshot head:
`ba61ed4cfca6747e32c21aeabbeed6453e5ea31e`

Audit PR:
#260 `audit/v79-bayesian-geometry-snapshot-20261010`

Handoff PR:
#261 `handoff/v79-bayesian-geometry-takeover-20261010`

Do not confuse this lane with PR #249. PR #249 is an older target-discovery Bayesian spike and is not Macha's current synthetic-geometry lane.

## Snapshot terminal state

At the audited snapshot, the lane state was:
`SIMULATION_QUALIFICATION_INCOMPLETE`

Committed / reported status at that point:
- Bernoulli detection S1 passed recovery.
- Bernoulli detection S0 still failed the convergence contract.
- donor×class non-centering materially improved convergence but residual divergences remained under investigation.
- Gaussian recovery was running/restarting under the corrected parameterization.
- positive-count candidate families (ZTNB and log-normal) were still under qualification/recovery.
- compute benchmark had not yet frozen final gene/fold settings.
- real corrected-TRAIN expression-value Bayesian fitting remained gated.
- no scrubbed Output B was qualified for downstream use.
- several long-running jobs existed only on the external execution machine at snapshot and were not terminal GitHub evidence.

Do not infer that those jobs later passed merely because they were launched.

## Controller rule 1: reconcile live state before giving Macha new scientific instructions

The first action in a new session must be to inspect Macha's live source branch and latest committed recovery/qualification artifacts.

Establish:
1. current branch head;
2. whether externally running jobs were reconciled into committed results;
3. which model parameterization, if any, was prospectively frozen;
4. current recovery status for Bernoulli, Gaussian, log-normal, and ZTNB families;
5. benchmark status;
6. whether any real corrected-TRAIN fitting has begun;
7. whether a qualified posterior-generative authority exists.

If live state differs from the snapshot, update the audit before issuing instructions that depend on the newer state.

## Controller rule 2: simulation recovery remains the gate into real TRAIN

Macha must not be instructed to force a failing model through to corrected TRAIN.

A model family may advance only after its preregistered recovery/convergence requirements are satisfied on simulated worlds.

For each likelihood family, the controller should verify:
- planted effects are recovered where present;
- absent effects are not invented;
- shuffled/permuted controls behave appropriately;
- R-hat satisfies the contract;
- ESS satisfies the contract;
- divergences satisfy the contract;
- the selected parameterization was chosen before looking at real-data outcomes;
- previously generated results are either validated under the new parameterization or explicitly superseded.

If a reparameterization is computationally equivalent, require evidence of equivalence. If priors, likelihood, hierarchy, estimand, conditioning, or model structure change, treat it as a scientific model change and amend the contract prospectively.

## Controller rule 3: the Bayesian mission is now high-fidelity generative modeling

Do not tell Macha to compress his final result to a few scalar summaries.

The current project policy is:

> Build the richest defensible probabilistic generative model of corrected TRAIN, preserve posterior uncertainty, and expose as much of the qualified generative structure as possible to the synthetic generator while preserving anonymous causal identities and evaluation firewalls.

This means the controller should encourage Macha to retain qualified posterior structure for:

Biology-side quantities:
- broad-class effect distributions;
- donor-effect distributions;
- donor×class variation;
- residual within-class variance;
- anonymous gene-effect/loading distributions;
- covariance/eigenspectrum geometry;
- state/program-scale distributions where supported;
- uncertainty/posterior draws.

Observation-side quantities:
- source-effect distributions;
- operator-effect distributions;
- capture/detection variability;
- depth distributions;
- gene-observation propensity distributions;
- count dispersion;
- detection/depth/count relationships;
- count-family posterior structure;
- uncertainty/posterior draws.

Do not intentionally degrade realism just to keep the output 'synthetic'.

## Controller rule 4: protect identity, not geometry

Allowed downstream transfer from Macha's qualified model includes statistical distributions and anonymous/high-dimensional geometry.

Do not transfer into planted causal truth:
- exact real gene-to-program assignments;
- named pathways/regulons;
- exact class×gene signatures;
- exact donor×gene biological signatures;
- target-discovery ranks/panels;
- SCENIC+/ATAC target evidence;
- pathology-derived gene effects;
- TEST/Morabito information.

The correct objective is:
`real statistical geometry + synthetic causal identity`

## Controller rule 5: preserve variable semantics

Never collapse the following into a generic 'batch' term:
- broad biological class;
- donor;
- donor×class;
- source;
- measurement operator;
- depth/capture.

Source may carry biology and measurement jointly. Operator is a measurement axis. Donor carries biology. Depth can be downstream of both biology and measurement.

Posterior association is not automatically causal identification.

## Controller rule 6: require held-out PPC before accepting a real-data model

After recovery/benchmark gates pass and corrected TRAIN fitting begins, require held-out posterior predictive checks that cover more than likelihood score.

At minimum inspect:

Marginals:
- library size;
- detected genes/cell;
- gene detection prevalence;
- positive-count abundance;
- abundance tail;
- dispersion.

Detection geometry:
- positive/negative correlation distributions;
- strong-edge fractions;
- degree;
- transitivity;
- eigenspectrum;
- class-conditioned structure;
- depth-conditioned structure;
- source/operator-conditioned structure.

Positive-expression geometry:
- expression correlation distribution;
- within-class covariance;
- class-conditioned covariance;
- eigenspectrum;
- gene-level variability.

Hierarchical effects:
- class spread;
- donor spread;
- donor×class spread;
- source spread;
- operator spread;
- residual spread.

A model with good held-out likelihood but major PPC failure must carry that failure forward. Do not hide misspecification behind a single model-selection score.

## Controller rule 7: Q5 donor×class adjudication matters

The held-out test asking whether donor×class earns its place is scientifically important.

Do not retain donor×class merely because the richer model fits the training observations better.

Require held-out predictive evidence that the donor×class term improves the preregistered target(s) without destabilizing the model.

If unsupported, simplify prospectively and document the ruling.

## Controller rule 8: final Macha output must be generator-consumable

The terminal package should include at least two logically distinct authorities.

### Biology geometry authority
Qualified posterior-generative structure permitted to parameterize H1.

### Observation geometry authority
Qualified posterior-generative structure permitted to parameterize H2.

Each should include:
- schema/version;
- exact source code SHA;
- corrected-TRAIN custody inputs;
- model-family identity;
- posterior draw/subsample policy;
- uncertainty representation;
- forbidden identity fields absent by construction;
- deterministic hashes;
- `training_authorized=false`.

A narrative report alone is not sufficient for downstream use.

## Controller rule 9: maximum-realism diagnostic may coexist with planted-truth authority

Macha may also produce a more directly fitted maximum-realism generative representation of corrected TRAIN.

That object is useful to ask how faithfully the Bayesian model reproduces real data.

But it must be labeled as a realism/generative diagnostic, not as independently known biological truth.

It must not be used alone to prove JEPA biological recovery.

## Controller rule 10: integration into factorial lane is prospective and field-level

The factorial lane is PR #253/#256/#257, with registry-memory hardening in PR #262.

Do not let Macha directly edit those branches.

Once Macha is terminally qualified:
1. audit the biology and observation authorities;
2. freeze exact SHAs;
3. define a field-level mapping from Macha biology authority -> H1;
4. define a field-level mapping from Macha observation authority -> H2;
5. preserve H3 as composition of those independently generated layers;
6. keep C_OBS and C_BIO mandatory;
7. create a prospectively frozen successor calibration/execution package if the mapping materially changes H1/H2;
8. only then run the definitive factorial tournament.

Do not use Macha after seeing H0/H1/H2/H3 outcomes to rescue a failing arm.

## Controller rule 11: what the next instructions to Macha should look like

If the lane is still in simulation qualification, instruct Macha to:
1. reconcile and commit all completed external recovery jobs;
2. finish the Bernoulli V1 S0/S1 experiment;
3. freeze the successful Bernoulli parameterization prospectively if it passes;
4. rerun the full Bernoulli recovery suite;
5. finish Gaussian recovery;
6. finish log-normal qualification/recovery;
7. finish ZTNB qualification/recovery;
8. run and freeze the benchmark;
9. stop any family that cannot satisfy recovery instead of forcing it forward.

If all required families are qualified and benchmark is frozen, instruct Macha to:
1. begin corrected-TRAIN fitting under the exact frozen contracts;
2. run held-out PPC and Q5;
3. select the positive-count family by the preregistered predictive/count-scale rule;
4. produce biology and observation posterior-generative authorities;
5. produce a maximum-realism diagnostic if useful;
6. write the report and complete self-audit;
7. keep `training_authorized=false`.

If a qualified authority already exists, do not ask him to rerun models immediately. Audit the authority and its provenance first.

## Controller rule 12: audit chronology rigorously

For every material Macha change, require:
- why it changed;
- pre/post real-data-outcome timing;
- previous code SHA;
- new code SHA;
- whether the statistical model changed or only computation/parameterization;
- simulation consequences;
- whether old results remain valid or are superseded.

No retroactive contract edits after seeing corrected-TRAIN outcomes unless explicitly labeled as a new successor experiment.

## Fixed prohibitions

Until separately authorized, Macha must not use:
- TEST/Morabito;
- pathology;
- target-discovery ranks/panels;
- SCENIC+/ATAC target evidence;
- target winner information;
- representation winner information;
- Stage4/500K;
- 353-ID repair as Bayesian synthetic evidence;
- V78 outcome-driven retuning;
- JEPA training/checkpoint generation.

## Controller terminal conditions

Macha's lane may be called `BAYESIAN_GEOMETRY_QUALIFIED_FOR_SYNTHETIC_INTEGRATION` only if all of the following are true:
- required simulation recovery suites pass;
- selected parameterizations are frozen prospectively;
- benchmark is frozen;
- corrected-TRAIN fits are complete on authenticated inputs;
- convergence diagnostics pass or unresolved failures are explicitly disqualifying;
- held-out PPC is complete;
- Q5 is adjudicated;
- count-family choice is adjudicated;
- biology geometry authority exists;
- observation geometry authority exists;
- self-audit is complete;
- exact SHAs/hashes are recorded;
- `training_authorized=false`.

If any required item is missing, preserve a nonterminal state.

## Recommended controller response pattern

When the user asks, 'What should I tell Macha next?', the supervising agent should first inspect Macha's latest committed state, then issue the shortest instruction set needed to reach the next gate. Do not repeat old instructions blindly.

The controller's job is to keep Macha advancing, but also to prevent simulation failures, real-data outcomes, and downstream synthetic tuning from being mixed into one adaptive loop.
