# Lineage-Composite Production Synthetic V3.1 — Consolidated Corrective Amendment

Date: 2026-10-14
Status: **CONTROLLING DESIGN AMENDMENT — IMPLEMENTATION PLANNING OFF PENDING FOCUSED RE-AUDIT**

This amendment is the single controlling correction layer for PR #344 after the independent Macha hostile audit (`APPROVE_WITH_REQUIRED_AMENDMENTS`, audit head `7497486f674fd70799f7fb91f62d506ea8962f94`). It does not authorize implementation, realization, fitting, scoring, target selection, representation selection, TD60, Stage4, synthetic training, or real training.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 0. Total precedence and supersession law

For production-synthetic design decisions, the following precedence is total and explicit:

1. this V3.1 consolidated corrective amendment;
2. `2026-10-14-lineage-composite-production-synthetic-v3-external-audit-corrections-v1.md` only where not superseded here;
3. `2026-10-14-lineage-composite-production-synthetic-v3-crosslane-alignment-addendum.md` only where not superseded above;
4. `2026-10-14-lineage-composite-production-synthetic-design-v3-amendment.md` only where not superseded above;
5. `2026-10-13-lineage-composite-production-synthetic-design-v2.md` only where not superseded above;
6. PR #328 only as a mechanics/interface fixture and historical implementation example, never as production biological architecture.

When two lower-precedence surfaces conflict, the higher-precedence rule controls. No implementation plan may resolve a design ambiguity itself. Any unresolved contradiction becomes `BLOCKED_DESIGN` or `BLOCKED_EXTERNAL`.

### Explicit supersessions

- Any candidate-shaped latent/mechanism family in V2 is superseded by the candidate-neutral biological mechanism law in §4 below.
- Any G7 percentage/fraction ladder language is superseded by the rights-token law in §6.
- Any G8 599-realization requirement in prior synthetic design is superseded by `BLOCKED_EXTERNAL_G8_DECISION_LAW_CONFLICT`; V3.1 does not choose 299 or 599.
- Any rule that treats `NOT_DIAGNOSED` as lawful abstention is superseded by §9.
- Any use of PR #328 ATAC/fragment generation as production architecture is superseded by §8.
- Any language allowing portfolio C4 after a merely hash-bound downstream implementation is superseded by `BLOCKED_EXTERNAL_TARGETPORTFOLIO` until the real portfolio contract is independently qualified with C6 prerequisite semantics.
- R5 prose PASS labels are superseded by `DESIGN_TEXT_PRESENT__NOT_TESTED` unless backed by executable evidence.

## 1. Generator freeze, anti-gaming, and sealed-seed custody

### 1.1 Freeze-before-use law

The production generator version is frozen **before any downstream method is run on any realization produced by that version**, including development/debug realizations.

The frozen identity must bind at minimum:
- generator source and transitive executable dependencies;
- parameter distributions;
- biological mechanism mixture and mixture weights;
- observation/calibration distributions;
- difficulty grid and stress-regime definitions;
- applicability/control matrix;
- address/support registries and modality namespace registries;
- serialization contract;
- realization budgets.

After any downstream result is inspected, any generator change creates a new generator version and invalidates previously intended sealed qualification for the new version. A changed version may not reduce difficulty or remove an adverse/control regime merely because a method failed.

### 1.2 Seed commitment

For each sealed qualification class, the controller holds a secret nonce with at least 256 bits of entropy.

`sealed_root = H(controller_nonce || generator_semantic_hash || class_tag || realization_budget)`

Before any development-world downstream execution, the controller commits `H(controller_nonce)` and the frozen generator semantic hash in an append-only ledger. The nonce is revealed only after the fit-side output for the sealed run is irrevocably frozen.

All random streams are domain-separated by cryptographic hashing over explicit keys such as:

`H(sealed_root || world_id || component_id || donor_id || cell_id || modality_id || purpose_tag)`

Integer seed offsets are prohibited in the production qualification generator.

### 1.3 Single-realization attestation and withheld family

For each prospectively frozen budget, the producer must attest that it emitted exactly the authorized sealed realizations and did not seed-shop, replace, or discard a failed realization. The receipt binds the complete emitted set before scoring.

At least one mechanism variant or composition regime is sealed-only and withheld from all development realizations. It is prospectively specified before seed commitment and exists to detect overfitting to the development generator family.

## 2. Calibration firewall

### 2.1 Real calibration may constrain observations, never hidden human biology

Authenticated real calibration may constrain observation/population properties only: depth, detection, support, missingness, donor/operator allocation, fragment multiplicity, modality availability, and other explicitly observation-side quantities.

It may not determine latent human disease prevalence, target identity, causal effect size, regulatory truth, candidate truth, or representation truth.

### 2.2 Split firewall

Every calibration artifact must bind donor identities and split provenance. Calibration donors must be disjoint from any real-data development, sealed, validation, oracle, or reserved hold-out population used to evaluate downstream scientific claims. The disjointness proof is by canonical donor ID, not by source label alone.

Calibration stratification by pathology, diagnosis, pathology proxy, or dataset/source identity used as a disease proxy is prohibited unless the quantity is proven observation-only and the use is explicitly justified prospectively.

Synthetic realization classes shall not be named `DEV` or `SEALED` when those names can be confused with real-data partitions. Use `SYNTH_DEBUG` and `SYNTH_QUALIFICATION`.

## 3. Canonical serialization and order invariance

Every artifact used for identity, custody, support, truth, or adjudication has two identities where applicable:
- a raw-byte SHA-256;
- a semantic SHA-256 computed from canonical serialization.

Canonical serialization must specify key ordering, numeric representation, missing-value representation, row ordering, shard ordering, registry ordering, and normalization of line endings/encodings.

The 41,238-address registry is bound by exact artifact identity and ordered-content digest.

Qualification requires hostile permutation tests showing invariant scientific results under JSON key reordering, shard/file reordering, row reordering where row identity is explicit, and equivalent canonical serialization. A scientific result that changes under irrelevant serialization/order mutation is a hard failure.

## 4. Candidate-neutral biological generator

### 4.1 Candidate-shaped latent families are prohibited

The generator may not contain latent families defined as C1, C2, C3, C4, C5, C6, query, relational candidate, composite candidate, or structural mirrors of those candidates.

Mechanisms are specified biologically and generically, for example:
- overlapping transcriptional programs;
- regulators and downstream programs;
- cell-state continua and manifolds;
- context/niche effects;
- donor-level recurrent and donor-specific components;
- perturbation-responsive mechanisms;
- common, rare, weak, null, additive and nonlinear interactions;
- biological modules with heterogeneous positive and negative effects.

Candidate mappings are computed controller-side **after** biological realization and never feed generation.

### 4.2 Out-of-basis requirement

Qualification contains mandatory worlds whose biological structure is not representable by the union of the current C-block candidate basis. At least one deliberately wrong candidate basis and one capacity-only composite control with random additional capacity must be verdict-bearing hostile controls.

### 4.3 Mixture rationale

The biological mechanism mixture and difficulty distribution are frozen before downstream execution and justified by candidate-independent biological/measurement goals. Candidate performance may not alter mixture weights.

## 5. Realism and difficulty acceptance law

The production generator may not reuse PR #328 disjoint contiguous gene-block geometry, fixed rare-effect geometry, or candidate decomposition as production biology.

Before sealed qualification, machine-verifiable acceptance checks must establish:
- overlapping programs rather than purely disjoint blocks;
- heterogeneity of sign, magnitude, sparsity and recurrence;
- effects scaled against authenticated technical-noise envelopes rather than arbitrary synthetic units alone;
- no single latent label that trivially determines candidate eligibility or truth;
- explicit source/cohort-confounded sampling regimes plus matched deconfounded twins;
- emitted-observation comparisons against authenticated TRAIN observation statistics, including mean–variance, detection–mean, correlation-spectrum and intrinsic-dimension summaries;
- frozen ceilings on trivial baselines such as marker-only, PCA-linear, library-only and source-only predictors.

Observation realism checks may reject a generator version; they may not tune hidden biology to improve a downstream target result.

## 6. Evidence rights, support states, and G7 compatibility

### 6.1 Four distinct address/evidence states

The synthetic interface distinguishes at least:
- `STRUCTURALLY_UNMEASURED`;
- `MEASURED_SCALAR`;
- `MEASURED_COLLISION_UNRESOLVED`;
- `WITHHELD_BY_EVIDENCE_RIGHTS`.

Measured zero remains a valid `MEASURED_SCALAR` value. `WITHHELD_BY_EVIDENCE_RIGHTS` is never serialized as structural absence or unresolved collision.

### 6.2 Mask selection

Evidence-right membership and reveal order depend only on frozen support/identity metadata and identity-keyed randomness. They are invariant to measured values. Eligibility is unchanged under within-support value permutation. Measured zeros remain eligible.

Each rights token binds a canonical content hash of the address/modality subset it authorizes.

### 6.3 Normalization firewall

Student-visible molecular inputs for biological-evidence ladders are raw/explicitly transformed values computed without any hidden-address total, hidden nGenes statistic, hidden full-bundle library size, or descendant thereof.

No full-bundle total may be supplied directly or indirectly. Values of already-visible addresses are byte-identical across evidence levels. Masked values are poison-tested so arbitrary changes to them cannot alter visible inputs or predictions before they are revealed.

Recomputing a normalization denominator on the changing visible subset is also prohibited when that changes already-visible values across levels. Any normalization used for a rights ladder must be frozen to information lawful at all compared levels and demonstrated not to encode hidden mass.

### 6.4 Evidence versus modality/domain

For canonical G7 rehearsal, an evidence-right ladder changes rights within an already-generated compatible observation object. Changing whether an acquisition modality exists belongs to measurement/domain availability unless an explicit downstream contract defines modality revelation as a rights-only operation without changing acquisition/support. Ambiguous cases are `NOT_REHEARSED`.

### 6.5 G7 real-lane status

PR #346 static nested-rights mechanics are compatible only after content-hash and anti-thinning enforcement above. PR #354 is prospective decision-layer work and is not frozen authority for V3.1.

Status:
`G7_STATIC_COMPATIBLE_WITH_AMENDMENT__G7_DECISION_BLOCKED_EXTERNAL`

Hostile tests must reject a count-thinning ladder even if it carries the `BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION` label.

## 7. R1 truth definition and external blocker

### 7.1 Two controller truths

For synthetic relational qualification, define two distinct controller truths.

**Estimand truth.** For each frozen molecular view, compute the expected-state representation under a frozen ruler/address set. For each anchored cell triplet `(i,j,k)`, use a **single common coordinate set for both d(i,j) and d(i,k)**. Pair-specific value-dependent informative-coordinate selection is prohibited. The metric, scaling and tie tolerance are frozen prospectively. Then:

`q_expected(i;j,k) = sign_tau(d_expected(i,j) - d_expected(i,k))`

where `sign_tau` returns a tie state inside the frozen tolerance.

**Latent-fidelity truth.** Separately compute relational order from the hidden biological manifold/state under its own frozen controller metric. It is reported separately and never substituted for the expected-state estimand.

Observed-data relations are estimator outputs/measurements, not controller truth.

### 7.2 Depth/support counterfactual

Qualification includes same-biology counterfactuals with asymmetric depth/support applied to j versus k. They must not change `q_expected`; they may change whether the observed relation is estimable. A depth-only flip in controller truth is a hard defect.

### 7.3 Real-lane status

PR #350 repairs the static semantic object but does not provide a complete d/q/null/decision executor and is source-name specific. PR #353 is a prospective stress lane, not a frozen production executor.

Status:
`BLOCKED_EXTERNAL_R1_EXECUTOR_AND_SOURCE_PARAMETERIZATION`

No V3.1 implementation plan may claim same-code-path R1 qualification until this blocker is independently resolved.

## 8. Teacher evidence and multimodal observation law

### 8.1 PR #328 is not production architecture

PR #328 remains a qualified mechanics/interface fixture only. Its disjoint biological geometry, candidate mapping, dense near-oracle ATAC construction, role-revealing metadata, and current C4 inconsistency are prohibited as production biological architecture.

### 8.2 Teacher modalities

Every teacher-visible biological modality must pass through a physical sparse observation process appropriate to that modality and calibrated to authenticated observation envelopes. Dense direct functions of expected molecular state or latent signal are controller-only and cannot be teacher evidence.

For ATAC/fragment-style evidence this requires a bound namespace including genome build, contig naming, gene-TSS annotation, peak/tile registry and any sequence/motif resource required by the downstream route.

Repeated destructive-assay realizations of the same biological unit may be controller-only for measurement characterization, or visible only as unlinked independent samples. They cannot be averaged by the teacher as repeated peeks at the same hidden nucleus unless a real acquisition contract supports that operation.

A frozen-capacity decoder ceiling from teacher evidence to expected state must remain within an authenticated envelope; a near-oracle teacher regime is stress-only and excluded from G6 PASS analogues.

### 8.3 Multimodal coupling

Same-nucleus modalities share a controller-generated per-nucleus technical-quality factor plus modality-specific noise. Separate-nucleus modalities use independent biological/technical draws under the declared pairing law, randomized row/order identities and hostile row-alignment tests.

## 9. Estimability and failure semantics

Controller truth distinguishes at minimum:
- `ESTIMABLE_WITH_TARGET_PRECISION`;
- `IDENTIFIABLE_BUT_UNDERPOWERED`;
- `NOT_ESTIMABLE_BY_CONSTRUCTION`.

`IDENTIFIABLE_BUT_UNDERPOWERED` is tied prospectively to the pinned executor's finite-sample decision law on the realized fit evidence. A calibrated `NOT_ESTIMABLE` output is lawful for this class; false certainty is a hard failure.

`NOT_DIAGNOSED` is not lawful abstention. It is mapped to `NUMERICAL_FAILURE`-class hard failure unless a future contract gives a distinct, prospectively defined meaning.

Per-case estimability truth applies to all challenge families, including evidence ladders, measurement robustness, transfer and relational challenges, not only sparse-positive worlds.

Donor counts and sealed-realization counts must come from a frozen precision/power budget. Replicate sealed worlds are required where operating-characteristic claims such as false qualification, false abstention or false certainty are made.

## 10. Fit custody and leakage firewall

Fit-side transport is **default deny**. A field is absent unless prospectively allowlisted with a fit-side scientific need.

Controller-only by default:
- latent state and expected molecular state;
- held-out outcomes;
- estimability truth;
- challenge-family/role labels;
- active/null perturbation role;
- twin/counterfactual linkage;
- candidate mapping and controller verdicts.

Fit-visible perturbation/twin identifiers must be opaque and role-exchangeable. Package shape and metadata must not predict controller role better than chance under a predeclared test.

Value-dependent eligibility is prohibited for query selection, evidence masks, relation membership, ruler membership and challenge inclusion unless the exact value dependence is itself the prospective estimand. Support state plus frozen identity-keyed randomness controls eligibility.

## 11. Verdict-bearing controls

Every hostile control has a prospective applicability matrix frozen with the generator. Applicable controls are hard gates, not descriptive plots.

Required control families include, where scientifically applicable:
- wrong-query/permuted-query controls;
- capacity-matched query-agnostic controls;
- semantic/nuisance twins;
- randomized relational/graph controls;
- source-only, library-only and marker-only baselines;
- capacity-only composite controls;
- perturbation matched nulls and deliberately contaminated-null positive controls;
- value-permutation eligibility controls;
- support/mask swap controls.

Null distributions use multiple matched draws. The number of null/control realizations follows the frozen precision budget. Twin-only worlds are used to estimate false qualification rate.

## 12. G6 status

PR #345 remains a finite matched-probe mechanics ancestor. PR #352 is prospective and does not yet resolve the non-degenerate margin-generation problem; all-zero reference margins are not acceptable evidence of substantive teacher advantage.

Synthetic qualification may not emit, set, or satisfy a human qualification flag.

Full G6 rehearsal requires:
- a non-degenerate independently qualified same-metric margin generator;
- explicit rejection of all-zero margins;
- noisy no-teacher-private-signal nulls;
- teacher-private positive and underpowered positive cases;
- matched search/model rights;
- teacher evidence satisfying §8.

Status:
`BLOCKED_EXTERNAL_G6_NONDEGENERATE_MARGIN_AND_HUMAN_DECISION_CONTRACT`

## 13. G8 status

V3.1 does not choose between the conflicting real-lane multiplicity laws. The 299-per-donor/depth and 599-per-depth/reference-unit rules represent incompatible families until the real lane freezes one controlling contract.

Before rehearsal, the real contract must define:
- the protected family and multiplicity unit;
- donor dimension of the family-wise error law;
- exact support-fraction numerator and denominator in the support-state vocabulary;
- how collisions and structural absence are treated;
- randomness keyed to cell/scientific unit rather than bare matrix position.

Synthetic measurement thinning must operate only on `MEASURED_SCALAR` count entries; collision-unresolved and structurally unmeasured states pass through as states, and thinned-to-zero remains measured scalar.

Status:
`BLOCKED_EXTERNAL_G8_DECISION_LAW_CONFLICT_299_VS_599`

## 14. G11/G12 transfer/coverage status

PR #349 split/evidence-support semantics are reusable for donor transfer and fail-closed evidence support, subject to synthetic mapping of support states:
- collision-unresolved is never `UNSUPPORTED_STRUCTURAL`;
- evidence-right withheld is never structural absence;
- unresolved evidence contracts remain blocked.

Non-donor held-out transfer axes and biological novelty are not currently equivalent to #349's contract and must be reported as `SYNTHETIC_ONLY` or `BLOCKED_EXTERNAL`, not promoted to human transfer authority.

Synthetic transfer testing includes explicit fit/held-out partitions for every axis that claims held-out transfer. Same-donor repeated observations, when present, are labeled as a separate repeated-measurement design and cannot violate donor-partition independence claims.

Status:
`G11_G12_COMPATIBLE_WITH_AMENDMENT__NON_DONOR_TRANSFER_AND_NOVELTY_NOT_HUMAN_BOUND`

## 15. TargetPortfolio status

PR #351 prospectively repairs C4<-C6 but remains a moving external dependency and does not, by itself, resolve all portfolio issues identified by audit (receipt enforcement, simultaneous constituent/composite representation, fail-closed NOT_ESTIMABLE behavior).

Full synthetic portfolio same-code-path qualification is therefore:

`BLOCKED_EXTERNAL_TARGETPORTFOLIO`

Synthetic design must continue to enforce the scientific law that composites cannot rescue failed constituents and composite failure cannot erase independently qualified constituents.

## 16. Same-code-path declaration law

Every downstream component in the future implementation plan must be classified prospectively as exactly one of:
- `SAME_CODE_PATH` — exact qualified downstream implementation invoked through the same reader/support/decision path;
- `SEMANTICS_COMPATIBLE_FIXTURE_ONLY` — synthetic exercise of an interface, explicitly not same-code-path qualification;
- `NOT_REHEARSED_BLOCKED_EXTERNAL`.

Phrases such as "where interfaces permit" or "thin adapter" are insufficient without an exact declaration, hash-bound interface and invariance test.

The current external blockers include at least G6, G8, R1 and TargetPortfolio. G7 decision remains external. G11/G12 are partially compatible as specified above. New successor PRs such as #355 are not automatically bound merely by existing.

## 17. Source/cohort confounding and pseudo-rarity

Qualification includes a sampling-confounded regime in which source/cohort is correlated with biological composition, plus a matched deconfounded twin. Source-only shortcuts are verdict-bearing controls.

Library size/RNA content may have both biological and technical components; the generator separates these controller-side rather than forcing all library variation into a purely technical observer.

Measurement-generated pseudo-rarity includes at least heterotypic doublets and ambient RNA contamination. These must not activate rare biological truth.

## 18. Novelty and rare/local scoring

Biological novelty is frozen by a candidate-independent latent criterion, including:
- low-density/held-out regions under the fit latent distribution;
- held-out lawful module combinations;
- new-module novelty where prospectively specified;
- donor familiarity as a separate axis from biological novelty and measurement OOD.

Rare/local performance is reported and gated per program and per rare stratum as well as globally. Qualification contains rare mechanisms spread across donors and mechanisms concentrated in one or two donors so donor imbalance cannot be averaged away.

Gate verdict labels are never stored as generator-side world labels; they are derived controller-side from biological parameters and realized evidence.

## 19. Perturbation null law

Matched perturbation nulls share delivery/handling burden with the active arm rather than being a no-op. Qualification includes a prospectively small contaminated-null positive control that the pipeline must detect as contaminated.

Arm roles and twin linkage remain controller-only; fit-side codes are opaque.

## 20. Support-state coverage and hostile minimum counts

Support qualification may not pass vacuously. Before sealed qualification, the generator freezes minimum instance counts per required support state and source/operator stratum, informed by authenticated historical support geometry without copying anonymous V75 identities.

Both `STRUCTURALLY_UNMEASURED` and `MEASURED_COLLISION_UNRESOLVED` receive poison-value hostile tests. `WITHHELD_BY_EVIDENCE_RIGHTS` receives separate swap/poison tests.

## 21. V79/V80 controller ruling

### 21.1 V79 remains frozen NOT_QUALIFIED

No V79 result is retroactively repaired, rescued, or promoted.

### 21.2 Terminal-lock ruling

The V79 terminal-lock law controls model selection. The 85 post-terminal rows may be retained and reported as **non-blind forensic/known-answer regression diagnostics**, but they cannot select, reject, or qualify a successor model version.

Binding V79 non-regression for prospective successor selection is limited to the 207 confirmatory rows that precede the terminal boundary, unless an exact frozen controller artifact proves a different authorized selection set.

The recovery ledger language claiming all 291 historical passes are binding non-regression requirements is superseded for production-synthetic planning.

### 21.3 V80 conflict is prospective, not rewritten silently

The frozen V80 package currently states that all 291 V79 historical hard passes are protected for future successor qualification. V3.1 does **not** mutate the frozen V80 benchmark/package bytes or rewrite its historical receipt. Instead it records an explicit prospective contract conflict:

`BLOCKED_EXTERNAL_V79_TERMINAL_LOCK_VS_V80_291_NONREGRESSION_SELECTION`

No successor-estimator qualification run may proceed until that conflict is resolved prospectively without changing V79 history or using the 85 post-terminal rows for model selection.

V80 remains a qualified benchmark/package/custody object; no successor estimator is qualified.

## 22. Moderate/minor findings that are mandatory plan requirements

A future implementation plan, if authorized after re-audit, must explicitly encode the following rather than silently defer them:

1. Evidence curves are scored against both the realized full reference and controller noise-free expected/latent truth, with roles kept separate.
2. Pseudo-rarity includes ambient RNA and heterotypic doublets.
3. Novelty uses the frozen latent/donor criteria in §18.
4. Contaminated-null perturbation control is verdict-bearing.
5. Same-nucleus quality coupling and separate-nucleus row-alignment hostile tests are mandatory.
6. Rare/local results are reported per program/stratum and cannot be rescued by global averages.
7. Gate verdicts are controller-derived, never generator labels.
8. Historical R5 prose PASS statements are treated as `DESIGN_TEXT_PRESENT__NOT_TESTED`.
9. Support-state tests have minimum non-vacuous instance counts and poison tests.
10. Every composed downstream component receives the §16 code-path classification.
11. TargetPortfolio residual gaps remain explicit external blockers until repaired and qualified.
12. Stage70/71 labels must be normalized to the #325 historical authority classification.
13. Any V73-V75 detected-feature envelope reused at 41,238 addresses must first prove that the statistic is address-universe agnostic; otherwise it is calibration-ineligible.
14. Depth stress by repeated synthetic realization is labeled `SYNTHETIC_ONLY` unless a real-lane acquisition analogue is explicitly frozen.

## 23. Focused hostile tests required before implementation planning

The focused re-audit must verify, at minimum, that V3.1 text now requires tests for:
- generator freeze before any downstream run;
- seed commit/reveal and single-realization attestation;
- withheld sealed-only mechanism;
- common-coordinate expected-state R1 truth and depth-asymmetry counterfactual;
- four-state evidence/support semantics;
- hidden-total poison invariance and visible-byte invariance across G7 levels;
- rejection of mislabeled thinning ladders;
- candidate-neutral biological families plus out-of-basis/wrong-basis controls;
- realism/difficulty ceilings and source-confounding twins;
- underpowered estimability class and precision budget;
- calibration donor/pathology firewall;
- non-oracle teacher modality generation;
- default-deny fit custody and role-predictability attack;
- value-independent eligibility;
- serialization/order invariance;
- verdict-bearing controls and empirical false-qualification measurement;
- `NOT_DIAGNOSED` hard-failure semantics;
- explicit external blockers for G6/G8/R1/TargetPortfolio;
- G11/G12 partial compatibility without overclaim;
- ATAC/fragment namespace binding;
- V79 terminal-lock ruling and explicit V80 prospective conflict.

## 24. Authorization state

This amendment authorizes only a focused design re-audit against the Macha findings list.

Current terminal:

`LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_1__CONSOLIDATED_CORRECTIVE_AMENDMENT_WRITTEN__FOCUSED_REAUDIT_REQUIRED__IMPLEMENTATION_PLAN_OFF__IMPLEMENTATION_OFF__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
