# V79 Factorial Biology × Observation Synthetic-World Design

Date: 2026-10-10  
Status: PROSPECTIVE DESIGN / NON-TRAINING / NON-PROMOTING  
Parent evidence branch: `design/v79-detection-localization-20261009` @ `62a1ff8cd93bd4250cd6ca11c93c7f3e9e6d6123`  
Frozen V78 scientific baseline: `impl/v78-signed-detection-marginals-20261009` @ `e959d9a732698ae9a41e8cb1f6c10052d7390326`

## 1. Purpose

Design the next synthetic-world mechanism family prospectively from the corrected-TRAIN localization evidence without retuning V78, copying real biological identities, or authorizing JEPA training.

The synthetic world exists to provide a controlled environment in which the latent biological state is known and the measurement process is separately controlled. It must be realistic enough to test whether a JEPA representation learns biology rather than donor/source/depth/operator shortcuts, while remaining synthetic enough that planted truth is not a disguised replay of corrected TRAIN biology.

This document designs the next generator tournament only. It does not implement it, execute it, promote an arm, or authorize checkpoint generation.

## 2. Evidence motivating the redesign

The corrected-S174 diagnostic on the frozen V77/V78 3,000-gene selection reproduced the existing pooled signed-detection object exactly on the rederived semantic evaluation universe:

- pooled positive/negative strong-edge ratio: `59.0185038591`;
- pooled median |r|: `0.1945641999`;
- pooled strong-edge fraction: `0.1348331666`;
- pooled mean degree: `404.3647`;
- pooled transitivity: `0.6672406627`.

Prospective localization then showed:

- L1 broad-class conditioning reduces the strong positive/negative ratio to approximately `1.2251`;
- the large L0→L1 change is driven primarily by collapse of positive co-detection edges, while the negative strong-edge fraction changes little;
- L2 class+detected-depth conditioning reduces the ratio further to approximately `1.0356` and substantially lowers typical absolute correlation magnitude;
- on the exact L3-covered cells, pooled ratio remains approximately `55.88`, broad-class conditioning approximately `1.318`, class+depth approximately `1.102`, and class+depth+source approximately `326.5` because strong negative edges nearly vanish;
- no nested donor stratum satisfies the preregistered support floor, so donor attribution remains unresolved;
- only a very small negative-edge residue is common across the available conditioned views.

Interpretation is intentionally narrow:

1. broad biological class is a major contributor to pooled positive detection topology;
2. depth explains much of typical correlation magnitude but is not assigned a uniquely technical cause;
3. residual signed topology is strongly source-associated, but current evidence does not identify whether that association is measurement-source, source-linked biology, or both;
4. V78's frozen random signed field is not a justified causal model for the corrected-real geometry;
5. a future synthetic mechanism should separate upstream biological hierarchy from downstream observation process and test them factorially.

The diagnostic remains noncanonical until the historical frozen evaluation-universe NPZ container bytes are recovered or a separate custody adjudication establishes semantic rederivation as canonical. This design may use the diagnostic as prospective mechanism-selection evidence only; it does not relabel it canonical.

## 3. Scientific objective

Build a synthetic world with two explicitly separable causal layers:

`latent biological hierarchy -> true latent transcriptome -> observation operator -> observed counts`

The tournament must answer four questions:

1. Is richer hierarchical biology required to reproduce the corrected-real broad-class and within-class geometry?
2. Is a more explicit observation process required to reproduce source/depth/detection behavior?
3. Are both layers required jointly?
4. Does the chosen world support counterfactual measurement twins that let JEPA later be tested for biological invariance across observation changes?

The tournament is successful if it falsifies inadequate mechanism families and identifies a prospectively qualified synthetic-world family. It is not successful merely because one scalar real-data statistic is matched.

## 4. Hard scientific and governance boundaries

All work under this design remains:

- TRAIN-only;
- pathology-blind;
- non-training-authorizing;
- non-promoting until the full synthetic qualification gate passes;
- separate from target discovery;
- separate from Macha's Bayesian geometry lane until that lane is independently audited.

Prohibited inputs or actions:

- TEST or Morabito;
- pathology labels or disease outcome information;
- target panels, target ranks, target posteriors;
- ATAC/SCENIC+/NIH-CARD target evidence;
- post-outcome V78 retuning;
- named real biological pathways or regulons as synthetic program truth;
- copying corrected-real gene-gene edge lists or covariance matrices into the generator;
- direct donor-specific real gene signatures;
- E4, Stage4, 500K promotion;
- JEPA training or checkpoint generation;
- using synthetic success to choose a real biological target.

All generated artifacts must carry `training_authorized: false` unless a later, separate governance decision explicitly changes that state after synthetic qualification.

## 5. Core causal architecture

For synthetic cell `i` and canonical address `g`:

### Biological layer

`C_i -> S_i -> Z_i -> lambda_true[i,g]`

with donor-like biology influencing state frequencies and program amplitudes:

`D_i -> (S_i, Z_i)`

where:

- `C_i`: broad biological class;
- `S_i`: anonymous discrete within-class latent substate;
- `Z_i`: continuous within-state biological programs;
- `D_i`: donor-like biological latent variable;
- `lambda_true[i,g]`: pre-measurement latent molecular abundance/intensity.

### Observation layer

`(lambda_true[i,*], O_i) -> X_obs[i,*]`

where `O_i` is an explicit observation regime containing only permitted measurement-process variables.

The architecture must make it impossible for observation regime to define the biological latent state. Biological state is generated first; observation is applied afterward.

## 6. H1 — hierarchical anonymous biology

H1 modifies only the biological layer. It receives no source/operator identity during latent biology generation.

### 6.1 Broad class

Retain the already-qualified coarse broad-class framework. Broad class is a legitimate biological hierarchy because corrected TRAIN localization shows that class mixture materially drives pooled positive topology.

The generator may use identity-scrubbed summaries of broad-class frequency and class-level geometry, but may not assign class programs using real gene names or real class marker lists.

### 6.2 Anonymous discrete substates

Each broad class contains a random number of anonymous substates. A substate jointly activates/deactivates coherent random blocks of canonical addresses.

Substate identities are synthetic and must not correspond to known named cortical cell types, disease states, pathways, or real donor clusters.

Allowed real-derived summaries are distributional only, for example:

- plausible number of substates per broad class;
- substate prevalence concentration/entropy;
- module-size distribution;
- block-overlap distribution;
- class-conditional degree/transitivity envelopes;
- class-conditional covariance strength distribution.

Forbidden:

- copying a real clustering assignment;
- using a real module membership list;
- using named cell-type marker panels to define synthetic states.

### 6.3 Continuous within-state programs

Within each discrete substate, add lower-amplitude continuous latent programs to avoid an unrealistically hard-clustered world.

These programs may perturb synthetic module amplitudes and relative abundances, but their address loadings are random under a frozen seed and constrained by anonymous geometry summaries only.

### 6.4 Donor-like biology

Synthetic donor latent variables may change:

- substate prevalence;
- broad program amplitude;
- total biological RNA-content scale;
- selected anonymous program means.

Donor-like effects must be generated from an identity-scrubbed magnitude/variance distribution. Real donor IDs and donor-specific gene signatures are forbidden.

Donor is biological/ambiguous by default, not automatically a nuisance variable.

## 7. H2 — explicit observation process

H2 modifies only the observation layer. It must consume the same upstream latent biological cell as the corresponding H0/H1 control.

### 7.1 Structural measurement support

Use the canonical registry/source-family support information to represent lawful structural unmeasurement across observation regimes.

This may include identity-preserving vocabulary support masks because the tokenizer/observation space itself is real infrastructure. It may not use target-discovery identities or pathway annotations.

### 7.2 Cell-level capture/measurement efficiency

Introduce a cell-level observation variable `c_i` that controls effective capture/sampling intensity.

Do not equate observed library size with capture efficiency. Biological RNA content and technical capture are separate latent quantities. The generator must therefore distinguish:

- biological total-molecule scale `B_i`;
- technical/measurement efficiency `c_i`;
- observed library total as an outcome.

### 7.3 Anonymous gene-level observation propensity

Synthetic addresses may have different capture/detection propensities. These propensities may borrow only identity-scrubbed distribution/rank geometry from corrected TRAIN or repaired marginal authority.

Allowed:

- prevalence distribution;
- anonymous rank distribution;
- source-conditioned support-rate distribution;
- anonymous abundance/capture heterogeneity distribution.

Forbidden:

- corrected-real gene-specific propensity copied by identity;
- real gene-pair signed field;
- target-specific propensities.

### 7.4 Stochastic molecular realization

Observed counts must arise from a declared generative sampling process rather than a forced detected-gene count plus post hoc allocation.

The first tournament should compare a small preregistered family rather than a flexible omnibus model. Candidate realization families may include:

- independent molecule thinning followed by count realization;
- conditional finite-library multinomial realization;
- mild overdispersion extension only if preregistered as a separate arm.

The realization mechanism must be fixed before observing its real-geometry scores.

### 7.5 Source/operator handling

Observation source/operator identity is allowed only in `O_i` and only through the authenticated bridge/authority.

`source_library` is not operator identity.

Operator/source may alter:

- structural support;
- capture-efficiency distribution;
- anonymous gene-level measurement propensity distribution;
- count-sampling parameters.

Operator/source may not directly alter the upstream biological module assignment.

## 8. Information firewall

The generator must receive less information than the scorer.

### 8.1 H1 may receive

Only identity-scrubbed TRAIN summaries needed for biological geometry:

- broad-class frequency distribution;
- class-conditional expression/detection geometry summaries;
- class-conditional module-size/degree/transitivity envelopes;
- anonymous within-class state/prevalence distributions if prospectively derived;
- anonymous donor-effect magnitude/variance distributions if later supported by audited Bayesian geometry.

### 8.2 H2 may receive

Only identity-scrubbed TRAIN summaries needed for observation geometry:

- authenticated source/operator support masks from canonical registry infrastructure;
- source/operator-conditioned depth/capture summary distributions;
- anonymous prevalence/capture-propensity distributions;
- repaired marginal abundance/depth summaries already authorized for synthetic calibration;
- source/operator support rates.

### 8.3 Neither H1 nor H2 may receive

- real 3,000-gene correlation matrix;
- real signed edge list;
- real community membership list;
- real gene identities attached to biology-derived loadings;
- real donor-by-gene effects;
- pathology or target-discovery information;
- TEST/Morabito-derived summaries.

### 8.4 Scorer-only sealed evidence

The following may be used for evaluation but not generator fitting unless explicitly listed above:

- pooled and conditioned signed-detection topology;
- full threshold-sweep edge metrics;
- L0→L3 localization path;
- class-conditional and source-conditioned adequacy metrics;
- counterfactual invariance metrics;
- synthetic JEPA recoverability metrics, once training is separately authorized.

## 9. Factorial tournament

Use a frozen factorial design to separate biology and observation effects.

### H0 — baseline control

Current E2 biological generator + current baseline observer.

Purpose: preserve the audited reference and detect unintended implementation drift.

### H1 — biology-only repair

Hierarchical anonymous biology + current baseline observer.

Purpose: test whether richer biological hierarchy alone repairs pooled/class-conditional geometry.

### H2 — observer-only repair

Current E2 biology + explicit observation process.

Purpose: test whether the observation layer alone repairs source/depth/detection behavior.

### H3 — coupled factorial candidate

Hierarchical anonymous biology + explicit observation process.

Purpose: test whether both layers are jointly required and whether their interaction produces the corrected-real geometry without direct covariance copying.

No arm may be retuned after outcome inspection. Any magnitude grid or small mechanism subfamily must be frozen prospectively as named arms before execution.

## 10. Counterfactual control worlds

The tournament must include two control families that are not optional diagnostics.

### C_OBS — observation twins

For the same exact latent biological cell `z_i`, generate multiple observed realizations under different lawful observation regimes:

`z_i -> O_a -> X_ia`

`z_i -> O_b -> X_ib`

The biological truth is identical across the pair.

Purpose:

- verify that observation changes can substantially alter measured RNA without changing latent biology;
- later provide a direct JEPA invariance test after training is separately authorized.

### C_BIO — biological twins under fixed observation

Generate distinct latent biological states under the same observation regime:

`z_i -> O_a`

`z_j -> O_a`

Purpose:

- prove that biological changes remain detectable under a fixed measurement process;
- prevent a future representation from succeeding merely by becoming invariant to everything.

### Control requirement

A future JEPA qualification should require both:

- high consistency for C_OBS pairs relative to biological-distance-matched controls;
- sensitivity to C_BIO state differences under fixed observation.

This design does not yet set JEPA thresholds or authorize JEPA execution.

## 11. Synthetic population design

Do not automatically replay the real source×class contingency table.

Because corrected TRAIN source and biology are confounded, the synthetic world should create a deliberately crossed design wherever lawful measurement support permits:

- same biological mixture through multiple observation regimes;
- multiple biological mixtures through the same observation regime;
- balanced counterfactual subsets for clean causal comparisons.

Realistic source prevalence may be used in a separate descriptive realism view, but causal qualification must use the crossed design so source and biology are identifiable.

The declared estimand must be explicit. Cell-weighted, donor-weighted, source-weighted, and balanced factorial views are not interchangeable.

## 12. Qualification endpoints

No single scalar may promote an arm.

### 12.1 Legacy continuity endpoints

Preserve the corrected-real scoring family used by V77/V78:

- median absolute expression correlation;
- fraction |expression correlation| > 0.3;
- detection median |r|;
- detection strong-edge fraction;
- detection mean degree;
- transitivity;
- positive/negative strong-edge ratio;
- T5 class-conditional/pooled expression ratio;
- abundance max/median nonzero;
- top-1% count share;
- median detected per cell.

### 12.2 Localization-aware endpoints

Score synthetic data using the same prospective localization ladder as corrected TRAIN:

- pooled detection topology;
- broad-class-conditioned topology;
- class+depth-conditioned topology;
- class+depth+source/operator topology where supported;
- donor-conditioned views where synthetic support is deliberately sufficient.

The synthetic world should reproduce the qualitative decomposition, not merely the pooled `59:1` ratio.

### 12.3 Distributional endpoints

Report:

- full signed correlation distribution;
- threshold sweep at 0.1, 0.2, 0.3, 0.4 with 0.3 canonical;
- positive/negative degree distributions;
- negative-edge gene participation fraction;
- community/transitivity structure;
- class-conditional abundance/depth distributions;
- source-conditioned detection/depth distributions.

### 12.4 Counterfactual endpoints

For C_OBS and C_BIO, report ground-truth separations at the latent and observed levels so later JEPA evaluation can distinguish desired invariance from accidental signal destruction.

## 13. Mechanism-selection logic

Interpret arms causally:

- H1 improves class/pool geometry while H2 does not: biological hierarchy is necessary;
- H2 improves source/depth geometry while H1 does not: observation process is necessary;
- H1 and H2 each fix their respective layer but H3 alone achieves joint adequacy: both are necessary and interaction matters;
- H1 alone achieves joint adequacy without source-specific observer changes: reject unnecessary observer complexity;
- H2 alone achieves joint adequacy without hierarchical biology: reject unnecessary biological complexity;
- H3 fails despite each component helping separately: current coupling formulation is falsified;
- all arms fail: do not expand parameter search inside the same family indefinitely; reopen mechanism family.

No arm is promoted because it has the lowest aggregate distance alone. Promotion requires prespecified multi-endpoint adequacy and absence of control failures.

## 14. Falsification rules

The tournament must be able to fail.

At minimum, reject an arm/family if any of the following occurs:

1. pooled geometry improves while class-conditioned geometry becomes implausible;
2. pooled signed ratio is matched by destroying overall degree/transitivity;
3. source matching is achieved only by source-dependent biological program assignment;
4. abundance/depth realism is achieved by forcing detected-gene counts externally rather than generating them;
5. C_OBS twins do not share identical latent truth by construction;
6. C_BIO states collapse to indistinguishable latent truth;
7. identity leakage occurs through named real program membership, donor signatures, target evidence, or copied real correlation structure;
8. an arm requires post-outcome parameter changes;
9. any arm opens TEST/Morabito/pathology information;
10. any receipt sets `training_authorized=true`.

## 15. Macha Bayesian geometry role

Macha's Bayesian lane remains external evidence, not hidden generator tuning.

If a returned artifact passes custody, leakage, and identity-scrubbing audit, it may inform prospectively frozen distributions such as:

- relative variance attributed to broad class, donor, source/operator, donor×class, and residual within-class biology;
- uncertainty intervals for those components;
- posterior-predictive geometry envelopes.

It may not:

- retroactively change V78;
- alter an already-executed V79 arm;
- introduce real gene identities into synthetic truth;
- convert descriptive localization into a unique causal claim without supporting uncertainty evidence.

If Bayesian evidence conflicts with deterministic localization, freeze the conflict and design a resolving experiment rather than averaging the conclusions.

## 16. Seeds and preregistration

Before executing any scientific arm, freeze:

- generator seed(s);
- biological hierarchy seed(s);
- anonymous module assignment seed(s);
- observation-process seed(s);
- cell counts;
- donor counts;
- class frequencies or balancing rule;
- source/operator crossing rule;
- all mechanism-arm labels;
- parameter grids, if any;
- all primary endpoints;
- support floors;
- promotion/falsification rules.

Seeds must not encode real identities.

## 17. Expected implementation boundaries

Prefer new V79 generator modules rather than modifying frozen V78 semantics in place.

Likely surfaces after written-spec approval and implementation planning:

- `scripts/v79/v79_hierarchical_biology.py` — anonymous broad-class/substate/continuous/donor-like latent biology;
- `scripts/v79/v79_observation_operator.py` — explicit structural support/capture/sampling layer;
- `scripts/v79/build_v79_factorial_worlds.py` — H0/H1/H2/H3 + counterfactual world construction;
- `scripts/v79/score_v79_factorial_worlds.py` — legacy and localization-aware synthetic scoring;
- focused tests proving information firewall, layer independence, counterfactual identity, deterministic replay, and non-authorizing receipts.

Frozen V78 scorer functions should be reused where appropriate for legacy continuity rather than silently reimplemented.

## 18. Required receipts

A future execution should produce separate immutable receipts for:

- preexecution custody/gate;
- frozen arm manifest;
- biological-hierarchy authority;
- observation-operator authority;
- counterfactual-pair manifest;
- per-arm generator receipt;
- per-arm adequacy score;
- terminal tournament ruling.

Every receipt before a later explicit training authorization must state:

- `training_authorized: false`;
- `v78_retuning_authorized: false`;
- `test_or_morabito_accessed: false`;
- `pathology_accessed: false`;
- `target_discovery_modified: false`.

## 19. What qualifies the synthetic world for the next stage

Synthetic-world qualification is not JEPA qualification.

A synthetic family may be recommended for later JEPA training only if it demonstrates all of the following:

1. realistic corrected-real marginal behavior;
2. realistic pooled and class-conditional dependence geometry;
3. realistic localization pattern across biological and observation layers;
4. no identity leakage;
5. counterfactual observation twins with identical latent truth;
6. counterfactual biological differences under fixed observation;
7. deterministic replay and authenticated receipts;
8. no hard falsification-rule failure.

Only after that scientific qualification should a separate decision consider a small JEPA engineering/training run and checkpoint generation.

## 20. Explicit non-goals

This design does not attempt to:

- make synthetic RNA a perfect generative model of human cortex;
- infer a true mechanistic capture efficiency for each real cell;
- identify causal disease biology;
- reproduce real named pathways;
- establish donor effects as technical or biological uniquely;
- select the eventual JEPA target architecture;
- authorize production-scale training.

The goal is narrower: create a controlled, realistic enough world that can falsifiably test whether JEPA learns planted biology rather than observation shortcuts.

## 21. Design decision

The recommended V79 family is therefore:

**factorial anonymous biological hierarchy × explicit observation process, with mandatory counterfactual measurement and biological controls.**

This design rejects both extremes:

- a single flexible covariance model that can hide biology and measurement together;
- a measurement-only or biology-only fix selected without factorial comparison.

The intended next sequence is:

`corrected-TRAIN localization -> V79 design freeze -> implementation plan -> H0/H1/H2/H3 + controls -> scientific qualification -> only then reconsider synthetic JEPA training/checkpoints`.
