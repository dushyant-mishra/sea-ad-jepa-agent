# Production Synthetic V3.1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the candidate-neutral, sealed, known-truth production synthetic substrate defined by V3.1/V3.1.1, with strict custody, four-state evidence/support semantics, realistic multimodal observation, controller-only truth, adversarial controls, and fail-closed downstream rehearsal interfaces.

**Architecture:** Implement a new production-synthetic package rather than extending PR #328 biology. The package separates canonical identity/custody, calibration provenance, hidden biology, observation operators, evidence rights/support, controller truth/estimability, hostile controls, fit/controller packaging, and downstream rehearsal. PR #328 may supply mechanics examples only; blocked real-lane gates remain `NOT_REHEARSED_BLOCKED_EXTERNAL` until their owning contracts are independently resolved.

**Tech Stack:** Python 3, NumPy/SciPy/pandas as already used in the repository, pytest, JSON/CSV artifacts, GitHub Actions. Do not add a new dependency unless an existing repository dependency cannot satisfy a frozen interface.

**Spec:**
- `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-consolidated-corrective-amendment.md`, Git blob SHA `48e71346c74378729e39a4de6b80699d3cb43d15`.
- `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-1-erratum.md`, Git blob SHA `977faa75e37c31610122e7ad45d2fc26dac536a3`, controlling only the E1–E7 clauses it amends.

## Global Constraints

- Authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED` throughout implementation and testing.
- `docs/agent/**` is non-controlling. Implementation decisions must trace to the two controlling spec blobs above or a later explicitly approved controlling amendment.
- Generator source, distributions, mechanism mixture, observation/calibration distributions, difficulty/stress grid, control applicability, registries, serialization contract, and realization budgets must freeze before any downstream exposure.
- After downstream exposure, difficulty/regime reduction is forbidden except documented generator-defect repair; such a version is `POST_EXPOSURE_VERSION`, inherits no qualification, and must re-pass the withheld-family check.
- The withheld-family specification and controller nonce remain secret under commit/reveal until sealed fit outputs are frozen.
- Every decision-bearing numeric quantity must have provenance `AUTHENTICATED_EMPIRICAL_CALIBRATION`, `PINNED_EXECUTOR_MATHEMATICS`, or `PROSPECTIVE_CONVENTION`; the implementation plan does not invent biological thresholds.
- Candidate-shaped latent/mechanism families and PR #328 disjoint-block/candidate decomposition are prohibited production biology.
- Controller estimability must use the pinned executor's finite-sample rule wherever an executor exists, so a decision-layer insufficiency is represented prospectively as `IDENTIFIABLE_BUT_UNDERPOWERED`; do not rely on the V3.1.1 E5 exception for a nominally well-powered case.
- `NOT_DIAGNOSED` maps to numerical failure, never lawful abstention.
- G6, G8, R1, TargetPortfolio, the G7 decision layer, and the V79↔V80 successor-selection conflict remain fail-closed external blockers unless independently resolved by later approved authority.
- No successor-estimator qualification run is part of this plan.

## Fresh successor classification — 2026-10-14 plan freeze

These classifications are based on exact live heads read immediately before writing this plan. A task may not silently upgrade a classification; any upgrade requires the exact code-path/interface tests specified below and a new plan/audit record.

| PR | exact head | exact-head CI observed | plan classification | reason |
|---|---|---|---|---|
| #350 R1 semantic repair | `9b9078c102fa346644d6eb2bda4ff7b4bdfe854a` | `TD real relational manifest V2` success, run `38508421155` | `NOT_REHEARSED_BLOCKED_EXTERNAL` | repairs anchored-cell semantics but remains a static/source-specific manifest, not the complete d/q/null/decision executor required by V3.1. |
| #351 C4 requires C6 | `b9774be4d9a79f3c64ed999c040f8982150d72d4` | targeted workflow success `38508634368`; broader `JEPA post-TD harness prefreeze` failure `38508634454` | `NOT_REHEARSED_BLOCKED_EXTERNAL` | C4←C6 repair is directionally correct but TargetPortfolio still has unresolved receipt/representation/NOT_ESTIMABLE behavior and failing broader harness. |
| #352 G6 margin decision | `bb1e35d33deb52236829012be452e4c4d8b362fc` | success `38510501468` | `NOT_REHEARSED_BLOCKED_EXTERNAL` | V3.1 blocks G6 until a non-degenerate independently qualified margin generator and human decision contract exist. |
| #353 R1 known-truth stress | `1df20029defaa2bcd7a51869c1026ac6075b1323` | success `38509563682` | `SEMANTICS_COMPATIBLE_FIXTURE_ONLY` | valuable hostile/stress fixture, but it is not the future pinned real R1 executor and cannot confer same-code-path R1 qualification. |
| #354 G7 terminal decision | `d90047308d633e259195a54501a230373b36d043` | success `38509928516` | `SEMANTICS_COMPATIBLE_FIXTURE_ONLY` | decision semantics are useful, but the inherited real G7 validator does not yet enforce content-hashed rights/anti-thinning semantics; E3 forbids `SAME_CODE_PATH`. |
| #355 G9/S1/S2 recurrence engine | `6e5182e2dc4e8e263e8cbd309aed6494b5ea7a55` | success `38511063837` | `SEMANTICS_COMPATIBLE_FIXTURE_ONLY` initially | mechanics are promising and exact-head green, but V3.1 requires explicit reader/interface/hash and invariance proof before `SAME_CODE_PATH`; this plan provides that gate rather than assuming it. |

Additional standing dependencies: #349 split/evidence-support semantics are scope-limited compatible for donor/support mapping; #343 G8 remains blocked by the 299-vs-599 family-law conflict; #346 contributes static G7 rights vocabulary but is not content-enforcing same code path.

## Planned file structure

Create a new package rather than adding production biology to `scripts/v79/`:

- `scripts/production_synthetic/canonical_v1.py` — canonical serialization, semantic/raw hashes, ordered registry identity.
- `scripts/production_synthetic/custody_v1.py` — generator version freeze, nonce/withheld commitments, domain-separated RNG, lineage and single-realization attestation.
- `scripts/production_synthetic/calibration_v1.py` — calibration firewall, donor/split disjointness, numeric provenance registry, realism stopping contract.
- `scripts/production_synthetic/biology_v1.py` — candidate-neutral hidden population/program generator.
- `scripts/production_synthetic/observation_v1.py` — RNA, ATAC/fragments, multimodal coupling, ambient/doublet pseudo-rarity, source/operator acquisition.
- `scripts/production_synthetic/evidence_v1.py` — four evidence/support states, value-independent eligibility, content-hashed rights tokens, normalization firewall.
- `scripts/production_synthetic/controller_truth_v1.py` — expected/latent truths, R1 provisional controller object, novelty, estimability classes, perturbation truth.
- `scripts/production_synthetic/controls_v1.py` — verdict-bearing hostile controls and applicability matrix.
- `scripts/production_synthetic/package_v1.py` — default-deny fit transport, controller transport, manifests/receipts and role-exchangeability checks.
- `scripts/production_synthetic/downstream_rehearsal_v1.py` — exact code-path classification and guarded invocation of eligible downstream components.
- `scripts/production_synthetic/qualification_v1.py` — realism/precision qualification orchestration, hard-status aggregation, per-program/stratum reporting.
- `scripts/production_synthetic/finalize_v1.py` — freeze immutable package receipt only after all required tests/controls pass.
- `requirements/production-synthetic-v1.txt` — exact runtime requirements reused/pinned from repository dependencies.
- `.github/workflows/production-synthetic-v1.yml` — qualification workflow.
- `tests/production_synthetic/` — focused and hostile tests matching modules above.
- `results/production_synthetic/v1/` — manifests/receipts produced only by explicit qualification commands; no hand-authored PASS receipt.

## Review Focus

1. **Post-exposure mutation:** a generator version that has been exposed must never become easier or inherit qualification after a defect repair; owned by Task 2 tests.
2. **Evidence leakage:** hidden mass, masked values, or support/mask conflation must not alter already-visible inputs; owned by Task 6 tests.
3. **Candidate-shaped shortcuts:** candidate IDs/bases must be unable to influence generation, while out-of-basis/wrong-basis worlds remain active; owned by Tasks 4 and 8 tests.
4. **Custody/serialization gaming:** semantic results must survive irrelevant order/serialization permutations and sealed realizations cannot be seed-shopped; owned by Tasks 1–2 and 9 tests.
5. **False authority through adapters:** blocked or fixture-only downstream lanes must not be promoted to `SAME_CODE_PATH` from green CI alone; owned by Task 10 tests.

---

### Task 1: Canonical identity and serialization contract

**Files:**
- Create: `scripts/production_synthetic/canonical_v1.py`
- Create: `tests/production_synthetic/test_canonical_v1.py`

**Interfaces:**
- Produces: `canonical_json_bytes(obj) -> bytes`, `raw_sha256(data: bytes) -> str`, `semantic_sha256(obj) -> str`, `ordered_registry_digest(rows, identity_keys) -> str`.
- Consumed by: Tasks 2, 3, 6, 8, 9, 12.

- [ ] **Step 1: Write failing canonicalization/permutation tests** asserting identical semantic hashes under JSON-key permutation, explicit row/shard reordering with stable identity keys, normalized line endings, and distinct raw-byte hashes when raw bytes differ.
- [ ] **Step 2: Run** `pytest tests/production_synthetic/test_canonical_v1.py -v` and verify RED because the module does not exist.
- [ ] **Step 3: Implement the four interfaces** with one documented canonical numeric/missing/order representation; bind the 41,238 registry by ordered content, never by unordered set membership.
- [ ] **Step 4: Run** `pytest tests/production_synthetic/test_canonical_v1.py -v` and require PASS.
- [ ] **Step 5: Commit** `feat: add canonical synthetic artifact identity`.

### Task 2: Freeze-before-use custody, secret commitments, and domain-separated randomness

**Files:**
- Create: `scripts/production_synthetic/custody_v1.py`
- Create: `tests/production_synthetic/test_custody_v1.py`
- Create: `tests/production_synthetic/test_custody_v1_hostile.py`

**Interfaces:**
- Consumes: canonical hashing from Task 1.
- Produces: `freeze_generator_version(spec) -> GeneratorFreeze`, `commit_secret(nonce, payload_hash, tag) -> str`, `derive_stream(root, *identity_parts) -> np.random.Generator`, `record_exposure(freeze, exposure) -> ExposureState`, `validate_successor_version(parent, child) -> VersionDisposition`, `attest_realization_set(...) -> RealizationAttestation`.

- [ ] **Step 1: Write failing custody tests** for ≥256-bit nonce requirement, withheld-spec commitment without plaintext exposure, deterministic domain separation, identical scientific-unit streams independent of row order, and exact realization-budget attestation.
- [ ] **Step 2: Add hostile tests** proving integer-offset namespaces are rejected, seed replacement/discard is rejected, and an exposed successor with any reduced challenge is rejected unless a documented generator defect creates `POST_EXPOSURE_VERSION` with no inherited qualification.
- [ ] **Step 3: Run** both custody test files and verify RED.
- [ ] **Step 4: Implement minimal custody state machines**; do not expose nonce or withheld specification in fit-side/public manifest before reveal.
- [ ] **Step 5: Run** both custody test files and require PASS.
- [ ] **Step 6: Commit** `feat: enforce sealed synthetic custody`.

### Task 3: Calibration firewall, number provenance, and realism stopping contract

**Files:**
- Create: `scripts/production_synthetic/calibration_v1.py`
- Create: `tests/production_synthetic/test_calibration_v1.py`

**Interfaces:**
- Produces: `CalibrationArtifact`, `NumericProvenance`, `RealismContract`, `validate_calibration_firewall(...)`, `derive_budget_from_precision(...)`, `advance_realism_iteration(...)`.
- Consumed by: Tasks 4–5, 7–8, 11.

- [ ] **Step 1: Write failing tests** that reject calibration donor overlap with real development/validation/oracle/reserved holdouts; reject pathology/proxy stratification unless explicitly observation-only; require every decision number to carry one of the three allowed provenance classes.
- [ ] **Step 2: Add realism stopping tests**: metric list/bands/adjustable observation parameters/max budget are frozen before iteration 1; first jointly passing version stops; exhausted budget returns `REALISM_NOT_QUALIFIED`; best-looking failure cannot be selected.
- [ ] **Step 3: Add precision-budget tests** deriving donor/world/null counts from a frozen target rather than observed method performance.
- [ ] **Step 4: Run** `pytest tests/production_synthetic/test_calibration_v1.py -v` and verify RED.
- [ ] **Step 5: Implement the typed records and validators**; no hidden biological parameter is an allowed realism tuning parameter.
- [ ] **Step 6: Run** the test file and require PASS.
- [ ] **Step 7: Commit** `feat: add calibration and numeric provenance firewall`.

### Task 4: Candidate-neutral hidden biology generator

**Files:**
- Create: `scripts/production_synthetic/biology_v1.py`
- Create: `tests/production_synthetic/test_biology_v1.py`
- Create: `tests/production_synthetic/test_biology_v1_hostile.py`

**Interfaces:**
- Consumes: custody streams and numeric provenance.
- Produces: `BiologySpec`, `HiddenPopulation`, `generate_hidden_population(spec, rng_factory) -> HiddenPopulation`.
- HiddenPopulation exposes controller-only donor/cell identities, latent states, overlapping program loadings, expected molecular state precursor, context/perturbation state and mechanism metadata; it exposes no candidate IDs or verdict labels.

- [ ] **Step 1: Write failing structural tests** requiring overlapping programs, heterogeneous signs/magnitudes/sparsity, common/rare/weak/null mechanisms, additive and nonlinear interactions, donor recurrence plus donor-specific components, context and perturbation mechanisms.
- [ ] **Step 2: Write hostile candidate-neutrality tests** proving C1–C6/query/representation/target labels are rejected from generator schema and changing controller-side candidate mappings cannot change hidden population bytes.
- [ ] **Step 3: Add out-of-basis tests** requiring at least one frozen mechanism/composition family outside the span of the current candidate basis and no PR #328 contiguous disjoint-block production geometry.
- [ ] **Step 4: Run** biology tests and verify RED.
- [ ] **Step 5: Implement the minimal generic biological generator** using identity-keyed streams; controller-side candidate mappings remain outside this module.
- [ ] **Step 6: Run** biology tests and require PASS.
- [ ] **Step 7: Commit** `feat: add candidate-neutral hidden biology`.

### Task 5: Physical observation operators and empirical stress geometry

**Files:**
- Create: `scripts/production_synthetic/observation_v1.py`
- Create: `tests/production_synthetic/test_observation_v1.py`
- Create: `tests/production_synthetic/test_observation_v1_hostile.py`

**Interfaces:**
- Consumes: HiddenPopulation, CalibrationArtifact, custody streams.
- Produces: `ObservationBundle` with RNA counts, sparse ATAC/fragment representation, operator/source/donor allocation, modality identity, technical quality, pseudo-rarity annotations controller-side only.

- [ ] **Step 1: Write failing population-geometry tests** covering highly imbalanced donor/operator allocations, ragged donor×operator occupancy, source-asymmetric support, held-out/source-shift regimes and balanced control regimes. Empirical values are calibration inputs, not latent biology constants.
- [ ] **Step 2: Write RNA observer tests** for raw nonnegative counts, nonlinear depth/detection and measured-zero semantics.
- [ ] **Step 3: Write ATAC/fragment tests** requiring bound genome/contig/TSS/peak-or-tile namespace, sparse physical fragment/count observation and rejecting dense direct functions of expected state as teacher evidence.
- [ ] **Step 4: Write multimodal identity tests**: same-nucleus views share a per-nucleus quality factor; separate-nucleus views use independent draws and remain invariant to row/order randomization.
- [ ] **Step 5: Write pseudo-rarity tests** for ambient RNA and heterotypic doublets that never activate rare biological controller truth; matched perturbation null shares delivery burden; contaminated-null positive control is distinguishable controller-side.
- [ ] **Step 6: Run** observation tests and verify RED.
- [ ] **Step 7: Implement the observation operators** with stress regimes clearly tagged controller-side as empirical-envelope or synthetic-stress.
- [ ] **Step 8: Run** observation tests and require PASS.
- [ ] **Step 9: Commit** `feat: add physical multimodal observation operators`.

### Task 6: Four-state support/evidence rights and normalization firewall

**Files:**
- Create: `scripts/production_synthetic/evidence_v1.py`
- Create: `tests/production_synthetic/test_evidence_v1.py`
- Create: `tests/production_synthetic/test_evidence_v1_hostile.py`

**Interfaces:**
- Produces: `AddressState`, `RightsToken`, `EvidenceLevel`, `build_rights_ladder(...)`, `apply_rights(...)`, `validate_visible_invariance(...)`.
- AddressState must distinguish `STRUCTURALLY_UNMEASURED`, `MEASURED_SCALAR`, `MEASURED_COLLISION_UNRESOLVED`, `WITHHELD_BY_EVIDENCE_RIGHTS`.

- [ ] **Step 1: Write failing state tests** preserving measured zero as scalar and preventing structural/collision/withheld coercion.
- [ ] **Step 2: Write value-independence tests** proving query/mask/ruler eligibility is unchanged under within-support value permutation and measured zero remains eligible.
- [ ] **Step 3: Write rights-token tests** requiring canonical content hashes, strict nested membership, terminal full rights, unique IDs and rejection of rights removal.
- [ ] **Step 4: Add leakage hostile tests**: already-visible bytes remain identical across levels; poison masked values cannot change visible inputs; no hidden full-bundle totals/nGenes descendants are present; a visible-total-only baseline cannot infer hidden mass by construction.
- [ ] **Step 5: Add anti-thinning tests** rejecting count/depth thinning even when falsely labeled `BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION`.
- [ ] **Step 6: Run** evidence tests and verify RED.
- [ ] **Step 7: Implement the evidence module**; modality availability changes remain measurement/domain unless explicitly lawful rights-only reveal.
- [ ] **Step 8: Run** evidence tests and require PASS.
- [ ] **Step 9: Commit** `feat: add support-aware evidence rights firewall`.

### Task 7: Controller truth, novelty, R1 scientific object, and estimability

**Files:**
- Create: `scripts/production_synthetic/controller_truth_v1.py`
- Create: `tests/production_synthetic/test_controller_truth_v1.py`
- Create: `tests/production_synthetic/test_controller_truth_v1_hostile.py`

**Interfaces:**
- Produces: `ControllerTruth`, `EstimabilityClass`, `derive_expected_state_truth(...)`, `derive_latent_fidelity_truth(...)`, `derive_estimability(executor_rule, realized_fit_evidence)`, `derive_novelty(...)`.

- [ ] **Step 1: Write failing R1 object tests** using anchored cell triplets and one common coordinate set for both distances; expected-state truth and latent-fidelity truth must be separate; asymmetric measurement depth may change observed estimability but never expected-state truth.
- [ ] **Step 2: Enforce E6**: provisional synthetic R1 metric/tau must be marked `PROSPECTIVE_CONVENTION`; no `SAME_CODE_PATH` status is possible until a complete pinned real R1 executor supplies the exact metric/scaling/ruler/common-coordinate/tie/null/aggregation law.
- [ ] **Step 3: Write estimability mapping tests** for `ESTIMABLE_WITH_TARGET_PRECISION`, `IDENTIFIABLE_BUT_UNDERPOWERED`, `NOT_ESTIMABLE_BY_CONSTRUCTION`, and hard numerical failure. When a pinned executor exists, derive the class with its finite-sample rule so the E5 well-powered insufficiency exception is not used as normal behavior.
- [ ] **Step 4: Write novelty tests** separating biological novelty, donor familiarity and measurement OOD; include low-density, held-out-combination and new-module cases.
- [ ] **Step 5: Run** controller tests and verify RED.
- [ ] **Step 6: Implement controller-only truth derivation** with no truth fields in fit transport.
- [ ] **Step 7: Run** controller tests and require PASS.
- [ ] **Step 8: Commit** `feat: add production synthetic controller truth`.

### Task 8: Verdict-bearing hostile controls and difficulty/realism qualification inputs

**Files:**
- Create: `scripts/production_synthetic/controls_v1.py`
- Create: `tests/production_synthetic/test_controls_v1.py`

**Interfaces:**
- Produces: `ControlApplicability`, `ControlResult`, `build_control_matrix(...)`, `evaluate_control(...)`.

- [ ] **Step 1: Write failing applicability tests** requiring a frozen applicability matrix before downstream exposure; applicable controls are hard gates.
- [ ] **Step 2: Cover wrong/permuted query, capacity-matched query-agnostic, semantic/nuisance twins, randomized relational/graph, source/library/marker-only baselines, capacity-only composite, matched perturbation null, contaminated-null, value-permutation and support/mask-swap controls.
- [ ] **Step 3: Require multiple matched null draws** and precision-derived counts for empirical false-qualification estimation on twin-only worlds.
- [ ] **Step 4: Add difficulty tests** for trivial-baseline ceilings carrying numeric provenance; convention-based ceilings require frozen sensitivity results.
- [ ] **Step 5: Run** controls tests and verify RED.
- [ ] **Step 6: Implement control definitions/evaluators** without candidate-driven generator changes.
- [ ] **Step 7: Run** tests and require PASS.
- [ ] **Step 8: Commit** `feat: add verdict-bearing synthetic hostile controls`.

### Task 9: Default-deny fit/controller packaging and custody receipts

**Files:**
- Create: `scripts/production_synthetic/package_v1.py`
- Create: `tests/production_synthetic/test_package_v1.py`
- Create: `tests/production_synthetic/test_package_v1_hostile.py`

**Interfaces:**
- Produces: `build_fit_transport(...)`, `build_controller_transport(...)`, `build_manifest(...)`, `verify_transport_separation(...)`.

- [ ] **Step 1: Write failing allowlist tests**: latent state, expected state, held-out outcomes, estimability truth, challenge roles, active/null roles, twin linkage, candidate mapping and controller verdicts are absent fit-side.
- [ ] **Step 2: Require opaque exchangeable IDs** and a predeclared role-predictability test at chance from fit metadata/package shape.
- [ ] **Step 3: Add raw/semantic hash and order-invariance tests** for fit/controller transports and manifest.
- [ ] **Step 4: Add sealed commitment tests** proving the withheld specification remains absent before reveal and exact realization set is bound before scoring.
- [ ] **Step 5: Run** package tests and verify RED.
- [ ] **Step 6: Implement packaging and validators** using Task 1 canonical identity and Task 2 custody.
- [ ] **Step 7: Run** tests and require PASS.
- [ ] **Step 8: Commit** `feat: add sealed fit and controller transports`.

### Task 10: Downstream rehearsal classifier and guarded adapters

**Files:**
- Create: `scripts/production_synthetic/downstream_rehearsal_v1.py`
- Create: `tests/production_synthetic/test_downstream_rehearsal_v1.py`
- Test existing only when classification permits: `scripts/v5/td_real_geometry_recurrence_engine_v1.py`, `scripts/v5/td_real_g7_terminal_decision_v2.py`, `scripts/v5/td_r1_known_truth_stress_v1.py`.

**Interfaces:**
- Produces: `CodePathClass = SAME_CODE_PATH | SEMANTICS_COMPATIBLE_FIXTURE_ONLY | NOT_REHEARSED_BLOCKED_EXTERNAL`, `DownstreamBinding`, `classify_binding(...)`, `invoke_binding(...)`.

- [ ] **Step 1: Freeze exact current dependency heads** in a machine-readable binding fixture and fail if the checked-out implementation differs.
- [ ] **Step 2: Write tests reproducing the classifications in the table above**. Green CI alone must not upgrade a blocked/fixture-only component.
- [ ] **Step 3: Write a hard blocker test** ensuring G6, G8, R1 and TargetPortfolio invocations return `NOT_REHEARSED_BLOCKED_EXTERNAL`; no adapter may fabricate a PASS analogue.
- [ ] **Step 4: Enforce E3 for G7**: until the real validator content-checks rights hashes/anti-thinning/support distinction, classify #354 as fixture-only even though its decision workflow is green.
- [ ] **Step 5: Gate #355 upgrade prospectively**: run the exact real recurrence implementation through the production synthetic fit-side reader; require exact interface/hash binding plus semantic/order invariance. If all pass, emit a separate reviewed binding artifact proposing `SAME_CODE_PATH`; otherwise remain fixture-only. Do not auto-upgrade inside this task.
- [ ] **Step 6: Run** `pytest tests/production_synthetic/test_downstream_rehearsal_v1.py -v` and require PASS with blocked components still blocked.
- [ ] **Step 7: Commit** `feat: add fail-closed downstream rehearsal bindings`.

### Task 11: Production qualification orchestrator and per-stratum reporting

**Files:**
- Create: `scripts/production_synthetic/qualification_v1.py`
- Create: `tests/production_synthetic/test_qualification_v1.py`
- Create: `tests/production_synthetic/test_qualification_v1_hostile.py`

**Interfaces:**
- Consumes: Tasks 2–10.
- Produces: `QualificationResult`, `run_pre_exposure_realism(...)`, `run_synthetic_qualification(...)`, `aggregate_hard_statuses(...)`.

- [ ] **Step 1: Write pre-exposure realism tests** for frozen metrics/bands, first-pass stopping, budget exhaustion, source/cohort-confounded plus deconfounded twins, and prohibition on hidden-biology tuning.
- [ ] **Step 2: Write hard-status tests**: false certainty, false abstention where truly estimable, numerical failure, failed applicable control and custody failure cannot be rescued by averages.
- [ ] **Step 3: Write E5 tests**: underpowered cases permit calibrated COMPLETE or NOT_ESTIMABLE, but derive underpowering from the pinned executor finite-sample law whenever available.
- [ ] **Step 4: Require per-program/per-rare-stratum outputs** and both donor-spread and 1–2-donor-concentrated rare regimes; global averages cannot erase failures.
- [ ] **Step 5: Score evidence curves against realized full reference, noise-free expected truth and latent truth as distinct outputs.
- [ ] **Step 6: Run** qualification tests and verify RED, then implement minimal orchestration.
- [ ] **Step 7: Run** qualification tests and require PASS.
- [ ] **Step 8: Commit** `feat: add production synthetic qualification orchestrator`.

### Task 12: Finalizer, workflow, and immutable qualification receipt

**Files:**
- Create: `scripts/production_synthetic/finalize_v1.py`
- Create: `tests/production_synthetic/test_finalize_v1.py`
- Create: `requirements/production-synthetic-v1.txt`
- Create: `.github/workflows/production-synthetic-v1.yml`
- Generated on explicit run only: `results/production_synthetic/v1/PRODUCTION_SYNTHETIC_MANIFEST_V1.json`, `results/production_synthetic/v1/PRODUCTION_SYNTHETIC_RECEIPT_V1.json`.

**Interfaces:**
- Produces: `finalize_package(inputs) -> FinalReceipt` only when all required design, custody, realism, control, packaging and eligible rehearsal conditions are satisfied.

- [ ] **Step 1: Write failing finalizer tests** requiring exact source/dependency hashes, controlling spec blob SHAs, numeric-provenance registry, canonical registries, custody commitments/reveals, complete emitted realization set, control matrix/results, code-path classifications and authority fields false.
- [ ] **Step 2: Add negative tests**: any blocked external gate stays recorded as blocked and cannot be converted to PASS; missing provenance or withheld commitment fails; any `POST_EXPOSURE_VERSION` must prove its full requalification lineage.
- [ ] **Step 3: Create the workflow** to run all `tests/production_synthetic/` plus only explicitly eligible inherited regressions. Do not run real human outcomes or successor-estimator qualification.
- [ ] **Step 4: Pin runtime requirements** to the existing repository-compatible scientific stack and record exact versions in the receipt at execution time.
- [ ] **Step 5: Run locally** `pytest tests/production_synthetic -q` and require all tests PASS before any finalizer invocation.
- [ ] **Step 6: Run inherited fixture regressions** needed to prove that reused PR #328 mechanics were not broken, while keeping PR #328 authority fixture-only.
- [ ] **Step 7: Invoke finalizer once only after all preconditions pass**; verify raw and semantic receipt identities and authority fields.
- [ ] **Step 8: Commit** `feat: finalize production synthetic qualification package`.

## Explicitly out of scope for this plan

- Resolving the G6 non-degenerate human margin contract.
- Choosing between G8 299 vs 599 or changing either real-lane contract.
- Completing or parameterizing the real R1 executor.
- Repairing/qualifying TargetPortfolio beyond observing #351 as an external dependency.
- Upgrading G7 to same-code-path before the real validator enforces E3 content semantics.
- Resolving V79 terminal-lock versus V80 291-pass successor-selection law.
- Running any successor estimator, human target tournament, target/representation selection, TD60, Stage4, JEPA training, or real training.

## Plan self-review

- **Spec coverage:** V3.1 §§1–22 and V3.1.1 E1–E7 each map to at least one task; external blockers remain explicit rather than receiving plan-invented fixes.
- **Step scan:** each implementation step names a file/interface or one verification action; no task requires the implementer to invent a scientific threshold.
- **Type consistency:** identity/custody/calibration types flow forward into biology/observation/evidence, then controller/controls/package, then downstream/qualification/finalizer.
- **Review Focus:** all five listed failure modes have owning hostile tests.
- **Proportion:** the plan defines interfaces and tests rather than implementation bodies; blocked downstream science is not reproduced inside the synthetic package.

## Execution gate

This document is an implementation plan only. Writing or approving it creates no implementation, realization, fitting, scoring, target, representation, Stage4 or training authority.

Before execution, review this plan against the two controlling spec blobs above and verify the live heads of all external dependencies again. Any moved dependency that changes semantics requires reclassification before its adapter is implemented.
