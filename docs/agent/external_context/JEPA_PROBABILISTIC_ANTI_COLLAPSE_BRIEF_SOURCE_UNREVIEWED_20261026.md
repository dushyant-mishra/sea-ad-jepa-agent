# Agent implementation brief: JEPA anti-collapse and probabilistic quality

Mission: Design, audit, and, if feasible, implement a non-authorizing evaluation system that determines whether our JEPA representations preserve biologically meaningful information, avoid dimensional collapse, generalize across donors, and provide useful, calibrated probabilistic predictions.

The agent should challenge this design rather than implement it uncritically. In particular, it should determine whether probabilistic readouts genuinely measure representation quality or merely reward technical covariates, model capacity, and gene-frequency priors.

The work must be isolated from Unified Task 4, real G7, protected human outcomes, and production training.

## 1. Scientific objectives

We need to distinguish four outcomes that conventional training loss cannot reliably separate.

| Outcome                      | Example                                                                     | Desired assessment                    |
| ---------------------------- | --------------------------------------------------------------------------- | ------------------------------------- |
| Complete collapse            | Every cell receives nearly the same embedding                               | Reject                                |
| Dimensional collapse         | A 160-wide latent uses only a few effective dimensions                      | Detect and investigate                |
| Semantic collapse            | Latent predicts source and depth but little incremental biology             | Reject as a biological representation |
| Valid biological compression | A relatively compact subspace preserves reproducible biological information | Potentially acceptable                |

The agent should not impose an arbitrary requirement that all 160 latent coordinates carry variance. A low-dimensional biological manifold might be genuine. What matters is whether the model discards information required by its scientific target.

A second objective is to test whether a representation predicts distributions, not merely point estimates, while preventing a powerful probabilistic decoder from hiding defects in the encoder.

The scientific questions are:

1. Does the learned state add held-donor predictive information beyond nuisance-only and simple biological baselines?
2. Does it preserve rare, local, relational and multi-program biological structure?
3. Can its uncertainty estimates distinguish missing biological information from insufficient sequencing depth?
4. Does the model remain stable under technical perturbation without becoming insensitive to real biological variation?
5. Does a probabilistic readout detect failures missed by conventional representation-health diagnostics?

## 2. Existing project infrastructure to reuse

The implementation must be based on the actual repository rather than rebuilding the architecture.

| Existing work                                             | Reuse                                                                                             |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| V5 `representation_collapse_guard_v1.py` and V4 telemetry | Variance, rank, covariance and unique-row diagnostics                                             |
| Representation Qualification V3                           | Global, query-local, program and structured-combined family comparison                            |
| Foundation Representation Qualification V4                | Subspace stability, nuisance controls, donor/matrix/technology transfer                           |
| Evidence-versus-Depth Convergence Protocol                | Separate biological-evidence and measurement-depth perturbations                                  |
| Unified Task 2                                            | Authenticated 104-donor `reader_fit` population, five donor-grouped folds and access restrictions |
| Unified Task 3                                            | Qualification-registry concepts and non-promoting evidence records                                |
| Unified Task 4                                            | Sealed-challenge custody requirements; do not modify the active implementation                    |
| V79/V80 and production-synthetic history                  | Negative priors, known-truth fixture requirements and statistical calibration lessons             |
| V5 runtime/teacher/student lineage                        | Existing encoders and representations; no need to build a new JEPA                                |

The agent must verify these files, their exact heads, their current semantics and whether later successors supersede them.

In particular, the historical u205 evidence must remain negative: source decoding was extremely strong, and technology invariance was not established. This is an essential nuisance-only test case, not a representation winner.

## 3. Proposed technical architecture

I recommend an evaluation sidecar rather than modifications to the JEPA training path.

Frozen representation source

Existing encoder, checkpoint or qualified synthetic fixture

Authenticated evaluation adapter

Permitted evidence, split, masks, donor identity and artifact hashes

Geometry diagnostics

Rank, spectrum, covariance and stability

Biological diagnostics

Program, rare-state and query recovery

Probabilistic readouts

Held-out log score, calibration and uncertainty

Shortcut attacks

Depth, source, operator, identity and leakage

Non-authorizing evaluation receipt

Raw metrics, baseline deltas, support, uncertainty, failures and abstentions

The sidecar should initially consume frozen embeddings. Its fitting process must not backpropagate through the encoder, update the EMA teacher, change the checkpoint, or tune the production target.

### Candidate implementation modules

These are proposed filenames, not claims about existing files.

```
src/sea_ad_jepa/evaluation/
    geometry_quality_v1.py
    predictive_readout_v1.py
    probabilistic_scores_v1.py
    calibration_v1.py
    evidence_depth_response_v1.py
    nuisance_challenge_v1.py
    quality_receipt_v1.py

tests/evaluation/
    test_geometry_quality_v1.py
    test_probabilistic_scores_v1.py
    test_calibration_v1.py
    test_nuisance_challenge_v1.py
    test_non_authorizing_guards_v1.py
```

The agent should first inspect whether equivalent modules already exist and reuse them. It should not create duplicate evaluators solely to match this proposed structure.

## 4. The first implementation experiment

Start with four planted synthetic scenarios using fixed, known truth.

World A — genuine multi-program biology

Several independent, donor-reproducible biological programs influence the target. A capable representation should retain information about them.

World B — deliberately collapsed representation

Map many distinct biological states onto a single or very narrow coordinate. Geometry must detect the loss; biological predictive scores should reveal which information disappeared.

World C — nuisance-only representation

Latent vectors strongly encode depth/operator/source but lack the planted biological programs. They may achieve good raw likelihood; incremental biological value must fail.

World D — valid compact manifold

Biology genuinely occupies a small, stable subspace. The evaluator must not incorrectly reject it simply because effective rank is low.

This is the most important early experiment because it answers whether the evaluation methodology can discriminate biological richness from both dimensional collapse and nuisance-rich representations.

## 5. What the agent should implement statistically

### Probabilistic readouts

Start with a simple held-donor negative-binomial count readout only when the target is actual raw counts and the observation model is appropriate.

For each evaluation unit, compare:

\\[ \Delta \mathrm{NLL} = \mathrm{NLL}\_{\text{baseline}} - \mathrm{NLL}\_{\text{baseline+JEPA}} \\]

Positive improvement means the augmented readout predicts better. It does not by itself establish biological relevance.

Fit readouts only on the training portion of the relevant donor fold, using nested donor-grouped tuning where necessary. Freeze the checkpoint and input permissions before scoring held-out donors.

For target objects that are not counts, evaluate distributions appropriate to the target semantics rather than forcing a negative-binomial model onto latent coordinates.

### Calibration

Use proper scoring rules and calibration diagnostics, including detection probabilities, predictive interval coverage and log scores. Stratify by source, gene detection regime, measured support and donor.

Estimate uncertainty across independent donors rather than across cells treated as independent observations.

### Anti-collapse geometry

Reuse historical effective-rank and covariance machinery. Add, where missing, spectral concentration, sensitivity to low-rank perturbations and donor-balanced subspace stability.

Do not establish a universal minimum effective rank in advance. The known-truth tests must demonstrate whether the diagnostics distinguish valid compression from damaging compression.

### Evidence versus depth

Keep the two perturbation mechanisms distinct:

- Biological-evidence reduction removes permissible features/program/context.
- Measurement-depth reduction changes count realization while retaining the feature universe.

This distinction is already part of the project contract and must survive any probabilistic implementation.

## 6. Required regression tests

The agent should create a RED-first test matrix. At minimum, the suite needs tests demonstrating these scientific contracts:

| Deliberate attack                              | Required behavior                              |
| ---------------------------------------------- | ---------------------------------------------- |
| Every embedding is identical                   | Detect collapse                                |
| Genuine one- or two-dimensional biology        | Do not automatically reject                    |
| Many high-variance nuisance dimensions         | Do not promote as biological richness          |
| Source-only representation has good likelihood | Incremental biological test must not be fooled |
| `q` enters through normalization               | Reject leakage                                 |
| Unmeasured gene converted to zero              | Reject                                         |
| Technical thinning treated as another donor    | Reject                                         |
| Calibration fit using held-out donors          | Reject                                         |
| Decoder given extra forbidden covariates       | Reject                                         |
| Rare program completely omitted                | Report the missing biological information      |
| Predictive probabilities confidently wrong     | Calibration detects the defect                 |
| Invalid distribution or nonfinite likelihood   | Fail closed                                    |
| Test report contains a fabricated PASS         | Independently recompute and reject             |

CI must run the positive control, the hostile mutation, and the repaired case against the actual production evaluator—not a parallel toy scoring function.

## 7. Instructions for the next agent

The following is the handoff I would give Claude or another independent implementation agent.

# JEPA Downstream Anti-Collapse and Probabilistic Quality V1 — Agent Assignment

## Mission

Conduct an independent scientific and engineering feasibility audit, then implement a bounded, non-authorizing diagnostic evaluator if justified.

The objective is to evaluate whether existing and future JEPA representations preserve biologically meaningful variation, resist dimensional and semantic collapse, predict held-out biological observations beyond technical shortcuts, and produce appropriately calibrated uncertainty.

**You are explicitly authorized to challenge, revise, narrow or reject this proposed approach based on evidence. You are not authorized to select a target, train JEPA, open protected biological outcomes, or promote any scientific authority.**

## A. Mandatory initial GitHub audit

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Before writing code:

1. Fetch current `main`, controlling PR heads, freeze branches and CI state. Do not assume that any SHA in this handoff is still the latest.
2. Read the current JEPA takeover/custody records in PRs #322 and #323.
3. Read the cross-lane reconciliation and pending-work register in PR #431.
4. Read Unified architecture #379, implementation plan #380 and accepted Unified Task 3 freeze #401.
5. Check the current cumulative status of Unified Task 4 #428/#429 and any successor.
6. Inspect historical V4/V5 representation-collapse code, training/runtime code and representation qualification contracts.
7. Inspect Foundation PRs #269, #271 and #276; reproduce the documented status of u205 before citing it.
8. Check whether probabilistic likelihood, calibration, uncertainty or generative readouts already exist in the repository. Search other active branches, not only `main`.
9. Inspect relevant V79/V80 and production-synthetic artifacts as bounded scientific evidence. Do not conflate synthetic truth with human biological evidence.
10. Produce a source/commit/reuse/blocker matrix.

Preserve the history of failed experiments, scientific retractions and non-promoting results. Do not substitute newer terminology for historical results without an explicit reconciliation.

## B. Scientific feasibility audit — before implementation

Answer the following questions with explicit evidence:

- Which exact representation objects can be evaluated without training?
- Can the existing checkpoint produce lawful frozen embeddings in this environment?
- Are raw integer counts available and authenticated, or only normalized/log-transformed expression?
- Which outcomes have valid count likelihood semantics?
- Which target objects need a different predictive distribution?
- Can a likelihood readout improve solely because of source, depth or gene-frequency information?
- Can a probabilistic decoder hide dimensional collapse?
- Is biological program information independently evaluable in available synthetic worlds?
- Can we distinguish model uncertainty, missing biological information and measurement-depth uncertainty?
- Which donor-level evaluation folds and source-support restrictions are already frozen?
- Which proposed metrics can be computed without protected human outcomes or an optimizer/EMA update?

Classify each feature as:

`FEASIBLE_NOW`, `FEASIBLE_FIXTURE_ONLY`, `NEEDS_NEW_QUALIFICATION`, `BLOCKED`, or `NOT_SCIENTIFICALLY_JUSTIFIED`.

If an essential design premise fails, document it and stop instead of implementing a misleading evaluator.

## C. Design requirements

Prefer a read-only evaluation sidecar.

Do not change the canonical encoder, teacher, student, predictor, EMA, optimizer, training loss, target definitions or protected data-access policy.

Do not implement a competing synthetic controller or independent verdict path.

Reuse the existing unified producer → authenticated artifact → executor → verdict architecture where safely possible.

The first version must support:

1. Frozen embedding input and provenance verification.
2. Biological-unit-aware geometry metrics.
3. Donor-grouped held-out evaluation.
4. Simple capacity-controlled probabilistic readouts, if justified.
5. Negative-binomial scoring only for suitable observed raw-count targets.
6. Calibration/coverage diagnostics.
7. Technical-only and biology-only control comparisons.
8. Distinct biological-evidence and measurement-depth response curves.
9. Explicit abstention for unsupported strata or missing evidence.
10. Non-authorizing machine-readable receipts.

All new outputs must preserve actual sample sizes, supported donors, excluded units and reasons for non-estimability.

## D. Known-truth qualification

Use a prospective, fixed synthetic fixture suite with at least:

- multi-program recoverable biology;
- dimensional/constant collapse;
- nuisance-rich but biology-poor representation;
- valid compact biological manifold;
- sparse or rare-program biology;
- changing depth without changing biological evidence;
- reducing biological information without simply thinning molecules;
- wrong-query and q-leakage attacks;
- source imbalance and inadequate independent donors;
- distributional miscalibration.

Critically, implement controls showing that the evaluator itself can fail.

Do not claim qualification from a suite that merely produces passing assertions.

Do not tune metrics, thresholds or calibration rules after inspecting the sealed final outcomes.

## E. Required workflow

Use the following sequence:

1. Inventory and independently audit reusable code.
2. Submit a bounded scientific design and feasibility verdict.
3. Write hostile tests before new production code.
4. Demonstrate intended RED against the actual missing or defective behavior.
5. Implement only the minimal required evaluator.
6. Run focused tests and inherited regressions.
7. Prove encoder parameters, optimizer steps and EMA state remained unchanged.
8. Run known-truth development fixtures using lawful access paths.
9. Independently recompute scores from raw numeric outputs.
10. Request an external hostile review at an exact frozen commit.
11. Repair only confirmed defects in a successor branch, preserving immutable RED evidence.
12. Return a final audit packet. Do not promote science or run protected data.

Use separate GitHub PRs for the design, implementation, hostile review and non-authorizing handoff if that best matches existing repository conventions. Never edit active Unified Task 4 or real G7 repair branches for this work.

## F. Acceptance criteria

A feasible V1 implementation is accepted for *diagnostic engineering scope only* if:

- exact input/checkpoint/split identities are validated;
- donor overlap and q leakage fail closed;
- no model training, EMA update or protected data read occurs;
- known-truth planted positives and negatives are discriminated by appropriate scientific metrics;
- nuisance-only high-likelihood solutions are not classified as biologically qualified;
- valid low-dimensional biological manifolds are not rejected solely for low rank;
- probabilistic scores and calibration are independently reproducible;
- unsupported cases return an honest abstention;
- raw outputs, code hashes and verdict derivations are inspectable;
- focused and inherited CI pass on one exact head;
- independent review accepts the bounded implementation.

No numerical acceptance threshold may be selected post hoc to make the tested candidate pass.

## G. Deliverables

Provide:

1. Feasibility audit with exact GitHub references.
2. Existing-code reuse and dependency map.
3. Proposed statistical estimands and likelihood semantics.
4. Threat model and hostile RED test matrix.
5. Minimal implementation, if scientifically and technically justified.
6. Executable example using fixture-only inputs.
7. Full test and CI evidence with exact commit SHAs.
8. Machine-readable diagnostic receipts.
9. Independent-review packet and open scientific questions.
10. An explicit recommendation: `ADOPT_DIAGNOSTIC_V1`, `REVISE_DESIGN`, `DEFER`, or `REJECT`.

The implementation must never award biological, representation or training authority by itself.

## H. Global non-negotiable state

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Protected human candidate outcomes, reader-validation and reader-oracle remain sealed under their applicable access laws.

Historical failures must remain failures. Fixture PASS is not human biological truth. Passing CI is not independent scientific acceptance.

**Do not implement the proposal just because it appears plausible. Determine first whether it can detect the failures we actually care about.**

## 8. How I would scope the agent's first assignment

I would not ask the agent to implement every item immediately.

The first checkpoint should be narrow and independently reviewable:

Milestone 1 — Feasibility + four-world discriminator

Historical code/protocol inventory

Required

Four-world synthetic test design

Required

Minimal likelihood + geometry prototype

Conditional

Independent negative-control evidence

Required

Production or protected-data execution

Forbidden

If the first milestone demonstrates that the probabilistic metrics distinguish genuine biological information from nuisance-only predictions—and expose representation damage that simple rank diagnostics miss—then the agent can recommend a V1 implementation for incorporation into the unified downstream qualification path.

If those metrics add nothing reliable beyond existing geometry and biological controls, we should retain the existing methods and avoid additional complexity.

The guiding requirement is scientific discrimination, not accumulating more metrics.