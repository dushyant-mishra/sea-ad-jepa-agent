# Lineage-Composite Production Synthetic Substrate Design V3 Amendment

Date: 2026-10-14
Status: **PROSPECTIVE DESIGN AMENDMENT — USER REVIEW REQUIRED — IMPLEMENTATION / REALIZATION / FITTING / SCORING / TRAINING OFF**

Base design: `docs/superpowers/specs/2026-10-13-lineage-composite-production-synthetic-design-v2.md`
Review delta: `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V2_REVIEW_DELTA_20261014.md`
Round-1 audit: `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_SELF_AUDIT_R1_20261014.md`
Round-2 audit: `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_SELF_AUDIT_R2_20261014.md`
Implementation base remains PR #328 exact head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`.

This amendment does not rewrite V2 history. V2 remains preserved evidence. V3 adds and tightens requirements identified by the 2026-10-14 synthetic-lane review. Where V3 conflicts with V2, V3 controls. Otherwise V2 remains binding.

Binding terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Purpose of the amendment

The production simulator must now explicitly combine:

1. the broad hierarchical/observation challenge geometry inherited from V79 and earlier real-distribution work;
2. the sparse-positive identifiability/abstention lessons frozen in V80;
3. empirically calibrated observation behavior from authenticated real TRAIN/S174 and later repaired distribution authority;
4. explicit separation of biological-information gain from measurement-quality gain;
5. explicit separation of biological novelty from unfamiliar measurement/acquisition domains.

These additions qualify the *production synthetic ecosystem design*. They do not change the historical verdict of V79, the frozen V80 benchmark, or any human biological authority.

## 2. V79 + V80 production challenge inheritance

### 2.1 V79 contribution

Retain the V2 V79 inheritance:

- hierarchical donor/source biology separated from observation;
- two-part detection + positive-magnitude observation structure;
- nonlinear depth effects;
- support-aware fitting;
- same-donor and new-donor prediction;
- source/acquisition shift;
- paired counterfactual semantics;
- opaque fit identities and truth-open-last scoring;
- broad Q00-Q11-style challenge diversity as *principle*, not copied realized worlds.

V79 remains permanently `NOT_QUALIFIED`. No V79 seed, failed-fit identity, realized world or frozen threshold is to be regenerated, retuned or reinterpreted for production design.

### 2.2 V80 contribution

The production simulator must add sparse-positive challenge families representing both:

- **estimable sparse-positive cases**: low prevalence, donor imbalance, source shift, support thinning, and held-out/new-donor prediction where enough information remains to identify the requested estimand;
- **non-estimable-by-construction cases**: for example zero measured positive support or structural rank deficiency where the estimand cannot be identified from fit-side evidence.

Controller truth must distinguish estimability from downstream numerical behavior.

The production truth vocabulary may contain:

- `ESTIMABLE`;
- `NOT_ESTIMABLE_BY_CONSTRUCTION`.

It must never contain `NUMERICAL_FAILURE` as a biological or data-generating truth class. `NUMERICAL_FAILURE` is a possible downstream estimator outcome only.

When an estimator-facing qualification is separately authorized, result semantics must remain compatible with:

- `COMPLETE`;
- `NOT_ESTIMABLE`;
- `NUMERICAL_FAILURE`.

False abstention on a controller-`ESTIMABLE` case is a hard error. False certainty on a controller-`NOT_ESTIMABLE_BY_CONSTRUCTION` case is a hard error. Numerical failure is never lawful abstention. No aggregate average may rescue a hard status failure.

### 2.3 Frozen benchmark separation

The frozen V80 package remains separate from the production simulator.

Production worlds must not copy:

- V80 seeds;
- V80 exact parameters;
- V80 thresholds;
- frozen benchmark identities;
- V79 failed-fit identities;
- estimator outcomes observed on either benchmark.

V79/V80 are validation/custody objects. Their lessons inform production challenge classes, not their literal realized bytes.

## 3. Empirical real-distribution calibration contract

The observation layer must be distribution-informed using authenticated real-data calibration artifacts, without promoting empirical frequencies into human biological truth.

### 3.1 Authorized calibration provenance

Every empirical calibration input must be bound by:

- exact artifact identity/hash;
- source dataset/study scope;
- donor/source/operator coverage;
- extraction code identity where available;
- whether the statistic is observation/acquisition-only or contains biological composition;
- supersession status.

Preferred authority order is repaired S174/current TRAIN-derived observation authority first, then explicitly qualified V72-V75 calibration artifacts within their narrow scope. Stale A3R TRAIN calibration is not automatically current authority where later repaired evidence supersedes it.

### 3.2 What empirical calibration may control

Authenticated empirical summaries may govern or constrain:

- library/depth distributions;
- detected-feature distributions;
- support/missingness profiles;
- dropout/detection behavior;
- positive-magnitude dispersion;
- modality availability;
- source/operator acquisition envelopes;
- donor observation heterogeneity;
- fragment multiplicity/coverage behavior where applicable;
- source composition and allocation feasibility.

### 3.3 What empirical calibration may not control

Empirical observation summaries may not be silently promoted into:

- human causal effect sizes;
- target winner identities;
- representation winner identities;
- human regulatory truth;
- disease/pathology truth;
- production candidate identities;
- V79/V80 frozen benchmark thresholds;
- latent program prevalence or latent biological state frequencies when the empirical statistic contains unresolved biological composition.

If a calibration statistic mixes biology and measurement, the simulator must either decompose it with independent authority or label its use as a bounded phenomenological observation fit rather than biological truth. A mixed statistic may shape what the observer emits, but it may not define latent biological prevalence unless a separately qualified biological authority explicitly permits that use.

### 3.4 Stress outside empirical ranges

The production ecosystem may contain prospectively declared stress worlds beyond the empirical envelope, including ultra-sparse or thinned-support regimes. These must be labeled synthetic stress and scored separately from empirical-distribution fidelity. They cannot be represented as observed human prevalence.

No world parameter may be changed after downstream outcomes are inspected merely to obtain a PASS.

## 4. Evidence-response versus depth-response contract

V2's biological-versus-measurement uncertainty distinction is upgraded into explicit intervention families.

Historical anchor: TD58S prospectively reduced student evidence with a fixed address/gene mask while retaining the full teacher relation and explicitly excluded count-depth/measurement uncertainty from that test. V3 generalizes that separation; it does not promote TD58S into target authority.

### 4.1 Biological-evidence response

For each selected case, first generate one frozen full observation bundle from one controller world. The bundle may contain multiple measured features/modalities/context channels, each generated once under its already-bound observation operator realization.

Across evidence levels, hold fixed:

- hidden biological state;
- donor identity;
- all generated measurement realizations;
- measurement-quality regime for any evidence that remains visible;
- teacher/reference identity where the downstream contract requires a fixed teacher target.

Vary only the **lawful subset of already-generated biologically relevant evidence revealed to the student**, prospectively at multiple evidence levels such as 20/40/60/80/100% where the interface supports it.

Evidence levels must change the *scope or set of visible lawful biological evidence*, not regenerate the measurement process. Lawful examples include prospectively nested fixed masks over measured genes/features, revealing an already-generated additional modality, revealing an already-generated context channel, or other nested subsets of the same frozen observation bundle.

A modality may count as additional biological evidence only if it was already generated for that same case before evidence-level masking. Moving from one evidence level to another must never regenerate the cell under a new acquisition operator.

Count thinning, lower library size, reduced capture efficiency or noisier repeated measurement are **not** biological-evidence interventions; they belong exclusively to the measurement-depth/quality family below.

If a downstream interface cannot vary visible biological evidence independently of measurement quality, that case is ineligible for a biological-evidence response curve rather than being silently treated as one.

Controller outputs must support at least:

- distance from partial-evidence inferred state/target to the full-evidence reference;
- incremental change from one evidence level to the next;
- information-efficiency summaries such as the minimum evidence level entering a frozen stable-state neighborhood.

The exact metric/threshold for any downstream gate must be frozen before sealed outcomes are read.

### 4.2 Measurement-depth response

For the same hidden biology and the same visible biological evidence class, vary only measurement quality. Examples include:

- sequencing depth thinning;
- repeated observation realizations;
- capture efficiency variation;
- count-split noise where lawful.

The intended biological channels/features/modalities made available to the student must remain fixed for a measurement-depth curve. If the acquisition operator lawfully changes realized support as depth changes, that support change is measurement-domain behavior and must not be relabeled as biological evidence gain.

Controller truth must support convergence toward the fixed-biology reference as observation quality improves.

### 4.3 Non-confounding rule

Biological-evidence and measurement-depth interventions must be generated and scored separately.

A system must not receive credit for biological-information efficiency merely because sequencing depth increased, nor be penalized as biologically unstable when only measurement quality changed.

Hostile tests must swap or collapse these labels and require detection.

## 5. Measurement-domain transfer versus biological novelty

The sealed production ecosystem must include explicit combinations of biology novelty and measurement-domain familiarity.

For every measurement-domain axis actually represented in the final sealed package, qualification must include a held-out-domain transfer condition unless the axis has only one lawful level. At minimum, the overall package must contain the following controller classes:

1. familiar biology + familiar measurement domain;
2. familiar biology + held-out source/dataset/operator domain;
3. biologically novel state/program combination + familiar measurement domain;
4. biologically novel state/program combination + held-out measurement domain.

### 5.1 Measurement-domain OOD

Measurement/acquisition novelty can arise from held-out:

- dataset/study;
- source;
- platform/chemistry/operator;
- depth/support regime;
- modality availability pattern.

These shifts may change the observation process but may not directly change latent biological truth.

### 5.2 Biological novelty

Biological novelty must be defined in controller truth from latent state/program geometry, for example:

- held-out program combinations;
- rare but lawful state regions;
- donor-level biological shifts;
- context/perturbation states not represented in fit biology.

It must not be defined solely by source, dataset or technology identity.

### 5.3 Joint scoring requirement

Final evaluation must report measurement-domain support and biological novelty separately. A single OOD flag is insufficient.

Conditional technology/source predictability may be measured only after controlling comparable biology; technology distinguishability alone is not a failure if the representation still preserves legitimate biological variation and does not use technology as a shortcut for biology.

## 6. Observation-operator law

The simulator must preserve the causal order:

`hidden biology -> expected molecular state -> observation operator -> observed modality view`

Technology/source/operator belong to the observation operator unless an independently authorized biological sampling effect is modeled separately.

Lawful observation-operator inputs may include:

- modality/platform/chemistry;
- measured address vocabulary/support;
- depth/capture properties;
- source-specific acquisition parameters;
- count/noise realization;
- nucleus versus whole-cell observation semantics where applicable.

Forbidden shortcut: unrestricted dataset/source embeddings or IDs may not directly enter latent biology.

## 7. Address and namespace binding

V2's 41,238-address production-reader requirement remains binding.

Implementation must:

- bind the exact current canonical address registry and production reader projection by hash;
- prove that no 4,096-era/narrower namespace is silently substituted for production qualification;
- preserve A3R three-state support semantics over the canonical address space;
- treat address width as an interface/observation requirement, not biological dimensionality authority.

Any semantic remapping required to make current reader bytes fit synthetic production is a stop condition requiring explicit review.

## 8. Additional hostile audits required by V3

Add to V2's mandatory hostile suite:

1. V79/V80 frozen-identity contamination of production world generation;
2. outcome-driven sparse-positive parameter retuning;
3. empirical prevalence/effect-size promotion into biological truth;
4. evidence-level and depth-level label swapping;
5. apparent evidence gain caused only by additional sequencing depth;
6. evidence-level transition that secretly regenerates a modality/operator realization;
7. apparent biological novelty caused only by held-out technology/source;
8. technology/source shortcut into latent biology;
9. silent 41,238 -> 4,096 namespace fallback;
10. `NUMERICAL_FAILURE` represented as controller truth;
11. false-abstention/false-certainty semantics weakened by aggregation;
12. mixed biology/measurement calibration statistic used to set latent prevalence;
13. unsupported measurement-domain axis omitted from transfer testing without an explicit single-level justification.

Each discovered defect must become a preserved failing regression before repair.

## 9. Implementation-unit amendments

V2 implementation units are retained with these additions:

- Unit 1 lineage/custody registry must include frozen V79/V80 non-authority bindings and empirical calibration provenance.
- Unit 3 acquisition/scaling must materialize authenticated empirical observation envelopes plus separately labeled stress extensions.
- Unit 5 observation/modalities must expose fixed-bundle evidence-response and separate depth-response intervention families.
- Unit 6 hostile challenge families must include V80-style estimable/non-estimable sparse-positive cases without copying V80 realized worlds.
- Unit 7 packaging must preserve controller-only estimability truth and biological-novelty/measurement-domain labels.
- Unit 8 rehearsal must report biological novelty and measurement-domain support separately.
- Unit 9 freeze must bind calibration artifact identities in addition to source/runtime/package identities.

## 10. V3 stop conditions

In addition to V2 stop conditions, stop if:

- production sparse-positive parameters are selected using frozen V79/V80 outcomes;
- real-distribution calibration provenance is missing or stale/superseded without justification;
- empirical observation statistics are being treated as causal biological truth;
- a mixed biology/measurement statistic is used to set latent prevalence without separate authority;
- evidence and measurement-depth interventions cannot be separated;
- an evidence-level change requires regeneration under a different observation operator;
- biological novelty is encoded by source/technology identity;
- a held-out technology shift alters latent truth directly;
- a represented measurement-domain axis cannot be held out or justified as single-level;
- an older 4,096 namespace is substituted for current production address semantics;
- estimator numerical failure is encoded as non-estimability truth;
- hard false-abstention/false-certainty failures are converted into aggregate soft penalties.

## 11. Authority statement

This amendment grants no implementation or execution authority by itself.

Still false:

- human biological truth authority;
- target selection;
- representation selection;
- TD60;
- Stage4;
- synthetic training;
- real training.

Intended design terminal after user approval:

`LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_DESIGN_V3_APPROVED__IMPLEMENTATION_PLAN_AUTHORIZED__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
