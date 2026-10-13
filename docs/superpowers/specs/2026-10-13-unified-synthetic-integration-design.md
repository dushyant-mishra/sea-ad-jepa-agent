# Unified synthetic integration design

Date: 2026-10-13
Status: **DESIGN FROZEN FOR REVIEW — NO GENERATION, FITTING, SCORING OR TRAINING AUTHORITY**
Base: PR #315 head `af03ef67d52651463944a6de3a08e101ad00e0ea`

## 1. Purpose

Implement the missing integration layer that turns the already-built synthetic components into one production-shaped, candidate-agnostic biological substrate that can be consumed by the existing Target Discovery and post-TD teacher/student/EMA control planes.

This is not a new synthetic architecture. It is a composition of already-audited lineages:

- Stage81A3 biological mechanics at `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`;
- V79 hierarchical biology and observation machinery from PR #253 (`1a0ab6e1108af924ca13e81caa3c70f3101d251c`);
- PR #311 rare/multimodal/context/perturbation implementation at `2b6d3439105e087acdab53a318c57bbb468eae26`;
- PR #315 corrected unified architecture at `af03ef67d52651463944a6de3a08e101ad00e0ea`;
- downstream consumer contracts from PR #313 and the green post-TD harness, without copying their decision logic into this lane.

The synthetic lane owns the substrate and adapters only. TD owns estimands/gates/adjudication. Macha/V79 owns the separate Q00-Q11 observation/statistical qualification campaign.

## 2. Non-goals and authority boundaries

This work does **not**:

- rerun or audit TD phase 1;
- open TD controller truth;
- authorize TD phase 2;
- regenerate or mutate Q00-Q11;
- invent new real-human effect-size thresholds;
- select a biological target or representation;
- open pathology/protected outcomes;
- authorize TD60, Stage4, JEPA/foundation training, or real training;
- replace the green downstream TD/post-TD control planes with synthetic-specific equivalents.

Global authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## 3. Design choice

Use an **adapter-first composition**.

Do not rewrite Stage81A3, V79, or PR #311 into one monolithic generator. Preserve their qualified mechanics and bind them explicitly through a new integration contract.

The unified flow is:

`candidate-agnostic biological population`
→ `noise-free expected molecular state`
→ `acquisition / observation operators`
→ `reader-compatible fit view`

In a separate trust domain:

`hidden biological truth`
→ `controller-only derived truth`
→ downstream candidate/gate truth, recoverability classes, counterfactuals and scoring truth.

Candidate identifiers C1/C2/C3/C6/C4/C5 must never influence latent world generation.

## 4. Reused components

### 4.1 Stage81A3

Reuse the established scientific separation:

`latent biology -> expected molecular state -> independent measurement realizations`

and preserve intervention/counterfactual semantics. Stage81A3 historical fixtures remain immutable evidence; the new code consumes their semantics rather than mutating their historical artifacts.

### 4.2 V79 biology and observation

Reuse the modern interfaces for:

- anonymous broad-class/substate/donor biology;
- continuous factors;
- structural support;
- capture/depth behavior;
- independent measurement realizations;
- measured support versus unmeasured support.

Source/operator parameters may affect acquisition and observation but must not directly create latent biological state.

### 4.3 PR #311 rare/context/perturbation

Reuse the already-qualified component mechanics for:

- donor-structured rare biology;
- common-to-rare activity regimes;
- technical pseudo-rarity;
- same-nucleus RNA+ATAC semantics;
- separate-nucleus donor-level semantics;
- evidence and depth ladders;
- context true/shuffled/distant controls;
- perturbation actual/null controls;
- teacher-private versus RNA-recoverable challenge logic.

The existing PR #311 challenge packages remain historical qualification evidence. Their mechanisms are integrated into one population; their old challenge files are not relabeled as the unified dataset.

## 5. New integration components

### 5.1 Integration manifest

Add one machine-readable manifest binding exact source commits, source file hashes where practical, schema version, authority flags and compatibility assumptions.

The manifest must fail closed if a bound source identity changes.

### 5.2 Unified population compositor

Create a focused module that composes one multi-lineage donor population with:

- broad lineage/state structure;
- overlapping continuous biological programs;
- common, intermediate and rare activity from the same program families;
- lineage-restricted specialist programs;
- additive and non-additive biological interactions;
- context-responsive and context-insensitive mechanisms;
- perturbable and matched-null mechanisms;
- explicit donor recurrence.

Rare biology must be an activity/frequency regime inside this same population, not a parallel world.

The compositor outputs controller-visible biological state plus a noise-free expected molecular state. It does not emit candidate labels.

### 5.3 Observation composition

Use the existing V79 observation operator as the RNA baseline and attach existing PR #311 modality/context realizers as adapters around the same latent cell/donor population.

Required semantics:

- same latent biology can generate multiple independent observations;
- measured zero remains distinct from structural unmeasurement;
- same-nucleus modalities share one latent cell;
- separate-nucleus modalities sample independently within donor/state distributions;
- technical pseudo-rarity is generated observation-side while the corresponding rare biological program is absent;
- source/operator can create observability differences and sampling association, not latent causal biology.

### 5.4 Controller-only truth adapter

Create a separate module/package that derives downstream truth from the completed biological world.

It may derive:

- shared/global manifold truth;
- relational ordering/geometry;
- query-conditioned truth;
- regulatory/mechanistic truth;
- additive versus non-additive increment truth;
- context/perturbation counterfactual truth;
- recoverability classes;
- biological versus measurement uncertainty targets.

This adapter is the only place candidate-specific mappings may exist. It must not be importable or reachable from the fit-view construction path.

### 5.5 Reader/support adapter

Expose the unified realization through the modern molecular-address/support semantics expected by the downstream pipeline.

The adapter must preserve:

- canonical address identity;
- explicit measured/unmeasured state;
- measured zero;
- donor/source/operator/cell provenance;
- lawful observation descriptors;
- donor-first split semantics.

The first implementation slice may use deterministic compact fixtures, but the interface must be production-compatible rather than synthetic-only.

### 5.6 Custody and integration receipt

Freeze an integration receipt containing:

- source commit identities;
- integration manifest hash;
- generator/adapter source hashes;
- deterministic fixture hashes;
- fit-view hashes;
- controller-view hashes stored separately;
- proof that authority flags remain false.

Controller truth must not be included in the fit-side package.

## 6. Downstream consumption

The unified synthetic substrate must feed existing downstream code paths rather than creating a parallel synthetic tournament.

Target Discovery consumption target:

- PR #313 case-ledger/firewall/falsifier framework;
- qualified gate executors as the TD lane freezes them;
- the relational executor only after the TD lane completes its own qualification chain.

Post-TD consumption target:

- the already-green target-portfolio/recoverability/topology/EMA harness preserved from `implementation/jepa-post-td-harness-prefreeze-20261013` @ `97dd73f49e1554053bbfab6c5369377a23a72ceb`.

This synthetic lane will supply data/truth adapters, not modify downstream estimands or numerical decision rules.

## 7. 50K STAT1 caveat

The duplicated `sample_row` identity in the 50K discovery sample remains unresolved for historical STAT1 residual/tail numbers that depended on physical-row identity.

Implementation rule:

- do not block integration of already-qualified rare mechanics;
- do not treat affected historical STAT1 numerical values as hard calibration authority;
- where a production parameter would depend on those values, mark it provisional or use an unaffected authenticated calibration until the row-identity repair is completed;
- repeat only affected residualization/tail calculations, not the entire rare-biology program.

## 8. Macha/V79 boundary

Q00-Q11 remain immutable and separate.

The unified simulator may use already-audited V79 mechanics and observation primitives. It must not claim final Layer-A qualification from Macha until a complete 1,056-fit receipt is returned and independently audited.

A later Layer-A result may update a separately governed observation-qualification decision; it cannot silently mutate a frozen unified synthetic realization.

## 9. Error handling / fail-closed behavior

The integration must stop on:

- source commit/hash drift;
- candidate identifiers appearing in generator configuration/state;
- controller fields present in fit-side outputs;
- measured-zero/unmeasured collapse;
- source/operator altering latent truth directly;
- same-nucleus/separate-nucleus semantic collapse;
- donor leakage across prospectively defined splits;
- missing authority manifest or mismatched registry identity.

Failures are preserved as evidence; they are not repaired inside the same scientific realization.

## 10. Verification strategy

The first deterministic fixture must prove, with executable tests:

1. common and rare cells are generated from one population/program system;
2. rare eligibility is biologically restricted where configured;
3. candidate names are absent from latent generator state and configuration;
4. identical latent biology can produce independent measurement realizations;
5. source/operator changes observations without changing latent biological truth;
6. measured zero and structural unmeasurement remain distinct;
7. same-nucleus modalities share a latent cell while separate-nucleus modalities do not expose fake pairing;
8. technical pseudo-rarity can occur without the planted biological rare program;
9. fit-side serialization contains no controller-only truth;
10. controller derivation reproduces deterministic truth from the frozen world without influencing generation;
11. reader adapter emits the expected address/support/provenance schema;
12. all training/target-selection/pathology/TD60/Stage4 authority flags remain false.

No model fitting or biological scoring is part of this first implementation slice.

## 11. Implementation decomposition

The implementation plan should be split into four bounded code increments:

1. **Manifest + compositor fixture** — bind histories and create one deterministic unified biological population.
2. **Observation + reader adapter** — independent RNA realizations, support semantics and modern fit view.
3. **Controller truth adapter + firewall** — candidate-derived truth only after world generation, physically separated from fit side.
4. **Downstream contract smoke** — prove the fit view can enter the existing TD/post-TD preflight interfaces without changing their science code.

Production-scale realization, final sealed seeds and any model/gate execution require separate prospective authority after these mechanics pass.

## 12. Acceptance criteria

This integration design is satisfied when:

- existing Stage81A3/V79/PR311 mechanics are reused rather than reimplemented without cause;
- one candidate-agnostic multi-lineage population contains common and rare activity;
- expected molecular state precedes observation;
- observation operators are separable from biology;
- controller truth is derived only after generation and is inaccessible to fit code;
- modern support/address semantics are preserved;
- downstream TD/post-TD code can consume the fit view via thin adapters;
- no Q00-Q11 mutation occurs;
- no real-human claim or numerical threshold is inferred from synthetic effect sizes;
- all prohibited authority flags remain false.

Terminal after this design:

`UNIFIED_SYNTHETIC_INTEGRATION_DESIGN_FROZEN__IMPLEMENTATION_PLAN_REQUIRES_REVIEW__NO_EXECUTION_AUTHORITY`
