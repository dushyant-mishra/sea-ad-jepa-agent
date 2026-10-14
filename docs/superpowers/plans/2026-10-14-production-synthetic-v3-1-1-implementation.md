# Production Synthetic V3.1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Implement tasks sequentially on one stacked branch. Each task receives a fresh implementer context and a separate fresh-context spec/hostile review before the next task begins.

**Goal:** Build the candidate-neutral, sealed, known-truth production synthetic substrate defined by V3.1/V3.1.1, with strict custody, four-state evidence/support semantics, realistic multimodal observation, controller-only truth, adversarial controls, and fail-closed downstream rehearsal interfaces.

**Architecture:** Implement a new `scripts/production_synthetic/` package rather than extending PR #328 biology. Separate canonical identity/custody, calibration provenance, hidden biology, observation, evidence rights/support, controller truth/estimability, hostile controls, fit/controller packaging, downstream rehearsal, qualification and finalization. PR #328 remains mechanics/interface history only. Blocked real-lane gates remain blocked until independently repaired and reclassified.

**Tech Stack:** Python 3, NumPy/SciPy/pandas already present in the repository, pytest, JSON/CSV artifacts, GitHub Actions. No new dependency unless an existing repository dependency cannot satisfy a frozen interface.

**Controlling specs:**
- `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-consolidated-corrective-amendment.md`
  - Git blob SHA: `48e71346c74378729e39a4de6b80699d3cb43d15`
  - SHA-256: `234af6dffa6f5d8bef03802a2eee4d8f65714ecd77718fa99c9b66e1d958b65c`
- `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-1-erratum.md`
  - Git blob SHA: `977faa75e37c31610122e7ad45d2fc26dac536a3`
  - SHA-256: `ab1ae1bb67765cc025f580205d7c082ee4af470dd39ef23c4f000414e8e9363f`
  - controls only the E1–E7 clauses it explicitly amends.

**Plan-binding addendum:**
- `docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-binding-notes-f1-n3-n6.md`
- controls execution semantics only for F1 and N3–N6.
- where this plan conflicts with that addendum on F1/N3–N6, the addendum controls; the two controlling specs above remain higher authority.

**Plan-review provenance:** Macha PR #356 review `docs/agent/MACHA_PR356_PLAN_REVIEW_20261014.md`, audit branch commit `16e411f330c01604d443c735d9b0bc28ed988cf2`, verdict `PLAN_ACCEPTED_WITH_REQUIRED_PLAN_AMENDMENTS_P1_P6__TASKS_1_3_MAY_START__AMEND_BEFORE_TASK_4`. Focused amended-plan acceptance is recorded on the audit branch at commit `2507b967`; it authorizes Task 4 only after Tasks 1–3 each clear their per-task reviews. These reviews are non-controlling evidence; the plan and addendum encode their binding execution implications.

`docs/agent/**`, PR descriptions and review prose are non-controlling. They may supply audit evidence and navigation only.

## Global constraints

- Authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
- Generator source, distributions, mechanism mixture, observation/calibration distributions, difficulty/stress grid, controls, registries, serialization and realization budgets freeze before any downstream exposure to a production generator version.
- After downstream exposure, no later version may become easier except a documented generator-defect repair under V3.1.1 E1; that version is `POST_EXPOSURE_VERSION`, inherits no qualification and must requalify.
- The controller, not any implementer/reviewer subagent, authors and holds the withheld-family specification and nonce off-repo.
- No public code path may uniquely identify the withheld family unless that code path is exercised independently by development/fixture worlds; otherwise the unique code also stays controller-side/off-repo per N3.
- Every decision-bearing number has provenance `AUTHENTICATED_EMPIRICAL_CALIBRATION`, `PINNED_EXECUTOR_MATHEMATICS`, or `PROSPECTIVE_CONVENTION`.
- Candidate-shaped latent/mechanism families and PR #328 disjoint-block/candidate decomposition are prohibited production biology.
- Controller estimability uses each pinned executor's own finite-sample law where one exists, so foreseeable decision-layer insufficiency is represented prospectively as `IDENTIFIABLE_BUT_UNDERPOWERED`; do not rely on the E5 well-powered exception as normal behavior.
- `NOT_DIAGNOSED` is numerical failure, never lawful abstention.
- G6, G8, R1, TargetPortfolio, the G7 decision layer and the V79↔V80 successor-selection conflict remain fail-closed external blockers unless independently resolved by later approved authority.
- No successor-estimator qualification run, human target outcome run, TD60, Stage4 or training is part of this plan.

## Execution authorization and stop gates

The current authorization covers **implementation code and fixture-world tests only**. It does not authorize a production realization, sealed qualification, or finalization.

Three fresh-authorization STOP gates are mandatory:

1. `STOP_A_FIRST_PRODUCTION_REALIZATION` — before the first realization from a frozen production generator version.
2. `STOP_B_SEALED_QUALIFICATION` — after pre-exposure realism/freeze and before any sealed qualification run.
3. `STOP_C_FINALIZER` — after qualification evidence is frozen and before `finalize_package(...)` is invoked.

Tasks 1–3 may begin under the reviewed plan. Task 4 may begin after Tasks 1–3 each finish and clear their required fresh-context per-task reviews. Tasks may implement code for later stages on fixture worlds, but no STOP gate may be crossed without fresh owner authorization.

## Pre-exposure ordering law

- Tasks 8 and 10 use **fixture worlds from an explicitly non-production test generator version only** during implementation/review.
- Trivial-baseline ceilings are part of the frozen **pre-exposure realism metric set**, not downstream method exposure.
- The first invocation of any downstream method on a production generator version happens only after `run_pre_exposure_realism(...)` has selected the first jointly passing realism version and frozen it.
- That first production downstream invocation must atomically call `record_exposure(...)` before/with execution.
- No task may run a downstream method on a candidate production version while realism iteration remains open.

## Withheld-family custody law

- Generic mechanism code may be public only when the same code path is exercised by non-withheld development/fixture realizations.
- The actual withheld-family specification/parameterization/applicability/scoring data are controller-authored and stored off-repo.
- If a mechanism code path would be uniquely exercised only by the withheld family, that code path remains controller-side/off-repo until reveal.
- No implementer or reviewer subagent receives the production withheld specification, nonce, or withheld-only code.
- Only `H(withheld_spec || controller_nonce || generator_semantic_hash || class_tag)` is committed before qualification.
- Before publishing the commitment, the controller runs a private repository-tree scan proving the withheld plaintext/preimage is absent from every committed file and that no committed public path uniquely identifies the withheld family; only a boolean attestation and tree identity are published.
- Unit tests use dummy secrets to verify scanner/commit-reveal and unique-code-path leak detection without exposing the production secret.
- Reveal occurs only after sealed fit outputs are irrevocably frozen.

## Fresh dependency classification — amended plan freeze

Every dependency is an open moving PR. The binding fixture must fail closed on **any** head movement. A moved head is re-read and explicitly classified as `BRANCH_MOVED_NO_SCIENTIFIC_EXECUTABLE_CHANGE` or `BRANCH_MOVED_SCIENTIFIC_CHANGE`; neither is silently accepted.

| PR | current head | status used by plan | classification / reason |
|---|---|---|---|
| #350 R1 | `9b9078c102fa346644d6eb2bda4ff7b4bdfe854a` | exact-head workflow green | `NOT_REHEARSED_BLOCKED_EXTERNAL`: semantic/static manifest, not complete d/q/null/decision executor. |
| #351 C4←C6 | `2abcb9fe156eac340ff12adff9426ed38d929e3e` | moved from original plan by test-only delta; targeted and full harness now green | `NOT_REHEARSED_BLOCKED_EXTERNAL`: block now rests on V3.1 §15 receipt-enforcement, simultaneous constituent/composite representation and fail-closed NOT_ESTIMABLE gaps, not CI. |
| #352 G6 | `bb1e35d33deb52236829012be452e4c4d8b362fc` | exact-head workflow green | `NOT_REHEARSED_BLOCKED_EXTERNAL`: non-degenerate independently qualified margin generator/human decision contract still absent. |
| #353 R1 stress | `1df20029defaa2bcd7a51869c1026ac6075b1323` | exact-head workflow green | `SEMANTICS_COMPATIBLE_FIXTURE_ONLY`: useful semantics fixture, but not an adversarial R1-control source and not the pinned real R1 executor. |
| #354 G7 decision | `d90047308d633e259195a54501a230373b36d043` | exact-head workflow green | `SEMANTICS_COMPATIBLE_FIXTURE_ONLY`: inherited validator still lacks content-hash/anti-thinning enforcement required by E3. |
| #355 G9/S1/S2 | `6e5182e2dc4e8e263e8cbd309aed6494b5ea7a55` | exact-head workflow green but geometry audit STOP | `SEMANTICS_COMPATIBLE_FIXTURE_ONLY__IMPLEMENTATION_REPAIR_REQUIRED_BEFORE_PROMOTION`: one-donor-short null draws can map measurable stability FAIL to NOT_ESTIMABLE; extra-source rows are silently dropped; caller supplies precomputed displacements, so leakage/null/seed guarantees are not enforced by the decision function. No promotion until the real lane repairs and independently qualifies these mechanics. |

Standing dependencies:
- #349 is scope-limited compatible for donor/support mapping only.
- #343 remains blocked for human G8. Current plan status: `CONFORMAL_BOUND_MECHANICS_QUALIFIED__CALIBRATION_REALIZATION_AND_ENDPOINT_SEMANTICS_OPEN__HUMAN_G8_NOT_EXECUTABLE`. #343 itself freezes `alpha_eff=0.01/6` and `n=599`; open issues are the calibration realization/reference units, displacement interface and support-fraction denominator. V3.1 §13's older blocker label remains historical spec text; the fail-closed result is unchanged.
- #343's thinning implementation is **not reusable** in production synthetic code: it is storage-order keyed, lacks the four-state measurement distinction, and does not thin/update normalization library size.
- #346 contributes static G7 rights vocabulary but is not content-enforcing same code path.

## Authenticated real stress inputs (non-blocking calibration candidates)

If exact artifacts are hash-bound under the calibration firewall, reproduce these support holes in empirical-envelope worlds rather than smoothing them away:
- NPH52: 0 reader-validation donors and 2 reader-oracle donors.
- 4,894 NPH52-only addresses never measured in reader-validation.
- 730 addresses measured only in HVS; 4,710 only in SEA_AD.
- SEA_AD held-out subclass strata: 4–5 donors each.

These constrain observation/support stress only; they do not set latent biology.

## Planned file structure

- `scripts/production_synthetic/canonical_v1.py` — canonical serialization, raw/semantic identities and registry ordering.
- `scripts/production_synthetic/custody_v1.py` — freeze, exposure, commit/reveal, domain-separated RNG, lineage and realization attestation.
- `scripts/production_synthetic/calibration_v1.py` — firewall, numeric provenance, address-universe eligibility, realism stopping/precision budgets.
- `scripts/production_synthetic/biology_v1.py` — candidate-neutral hidden population/program generator.
- `scripts/production_synthetic/observation_v1.py` — RNA/ATAC/fragments, multimodal coupling, pseudo-rarity, depth/thinning operator.
- `scripts/production_synthetic/evidence_v1.py` — four-state support/evidence rights and normalization firewall.
- `scripts/production_synthetic/controller_truth_v1.py` — expected/latent truth, estimability, novelty and controller verdict derivation.
- `scripts/production_synthetic/controls_v1.py` — verdict-bearing hostile controls and applicability matrix.
- `scripts/production_synthetic/package_v1.py` — default-deny fit/controller transport and custody receipts.
- `scripts/production_synthetic/downstream_rehearsal_v1.py` — moving-head bindings and guarded fixture/same-code-path invocation.
- `scripts/production_synthetic/qualification_v1.py` — realism/qualification orchestration and per-stratum reporting.
- `scripts/production_synthetic/finalize_v1.py` — immutable receipt after explicit STOP_C authorization.
- `tests/production_synthetic/` — focused and hostile tests.
- `requirements/production-synthetic-v1.txt` and `.github/workflows/production-synthetic-v1.yml`.
- Generated only after authorization: `results/production_synthetic/v1/` manifests/receipts.

## Review focus

1. Post-exposure versions cannot become easier or inherit qualification.
2. Evidence masking/support states cannot leak hidden mass or conflate withheld/structural/collision states.
3. Candidate labels/bases cannot influence generation; gate verdicts are controller-derived only.
4. Serialization/custody cannot be gamed by ordering, seed shopping or secret leakage.
5. Green external CI cannot promote a blocked or fixture-only component.

---

### Task 1: Canonical identity and serialization contract

**Files:** create `scripts/production_synthetic/canonical_v1.py`, `tests/production_synthetic/test_canonical_v1.py`.

**Interfaces:** `canonical_json_bytes(obj) -> bytes`, `raw_sha256(data) -> str`, `semantic_sha256(obj) -> str`, `ordered_registry_digest(rows, identity_keys) -> str`.

- [ ] Write RED tests for JSON-key permutation, row/shard reordering with stable identity keys, line-ending normalization, and distinct raw hashes for distinct bytes.
- [ ] Implement canonical numeric/missing/order representation and ordered 41,238-registry digest.
- [ ] Run `pytest tests/production_synthetic/test_canonical_v1.py -v` → PASS.
- [ ] Commit `feat: add canonical synthetic artifact identity`.
- [ ] Fresh-context spec/hostile review before Task 2.

### Task 2: Freeze-before-use custody, withheld commitments and RNG

**Files:** create `scripts/production_synthetic/custody_v1.py`, `tests/production_synthetic/test_custody_v1.py`, `tests/production_synthetic/test_custody_v1_hostile.py`.

**Interfaces:** `freeze_generator_version`, `commit_secret`, `derive_stream`, `record_exposure`, `validate_successor_version`, `attest_realization_set`, `scan_secret_absence`, `attest_no_unique_withheld_code_path`.

- [ ] Write RED tests for ≥256-bit nonce, deterministic domain separation by scientific identity, row-order-invariant streams, exact realization budget, and commit/reveal mismatch failure.
- [ ] Using dummy secrets, test `scan_secret_absence(repo_tree, secret_bytes)` fails if any tracked file contains/matches the dummy preimage and emits only a boolean/tree attestation.
- [ ] Using dummy withheld fixtures, test a committed code path uniquely attributable to the withheld family triggers custody failure; public mechanism code is allowed only if exercised by non-withheld fixture/development worlds too.
- [ ] Hostile tests reject integer-offset seed namespaces, seed replacement/discard and easier exposed successors; documented defect repair yields `POST_EXPOSURE_VERSION` with no inherited qualification.
- [ ] Implement custody state machines. Production withheld data and withheld-only code remain off-repo/controller-only by construction.
- [ ] Run custody tests → PASS.
- [ ] Commit `feat: enforce sealed synthetic custody`.
- [ ] Fresh-context review before Task 3.

### Task 3: Calibration firewall, number provenance and realism contract

**Files:** create `scripts/production_synthetic/calibration_v1.py`, `tests/production_synthetic/test_calibration_v1.py`.

**Interfaces:** `CalibrationArtifact`, `NumericProvenance`, `RealismContract`, `validate_calibration_firewall`, `validate_address_universe_agnostic`, `derive_budget_from_precision`, `advance_realism_iteration`.

- [ ] RED tests reject donor overlap with real development/validation/oracle/reserved holdouts and pathology/proxy stratification unless proven observation-only.
- [ ] Require every decision number to use one allowed provenance class.
- [ ] Freeze realism metric list/bands/adjustable observation parameters/max budget before iteration 1; first jointly passing version stops; exhausted budget → `REALISM_NOT_QUALIFIED`; best-looking failed iteration cannot be selected.
- [ ] Derive donor/world/null counts from frozen precision targets, never downstream performance.
- [ ] **§22.13:** before any V73–V75 detected-feature envelope can be reused, `validate_address_universe_agnostic(...)` must prove the statistic is invariant/valid across the 96-feature versus 41,238-address universe; otherwise mark calibration-ineligible.
- [ ] Add exact authenticated support-hole fixtures only after artifact/hash validation; reader-fit calibration remains observation-side.
- [ ] Implement and run `pytest tests/production_synthetic/test_calibration_v1.py -v` → PASS.
- [ ] Commit `feat: add calibration and numeric provenance firewall`.
- [ ] Fresh-context review. **Task 4 may begin only after Tasks 1–3 each clear their per-task reviews.**

### Task 4: Candidate-neutral hidden biology

**Files:** create `scripts/production_synthetic/biology_v1.py`, `tests/production_synthetic/test_biology_v1.py`, `tests/production_synthetic/test_biology_v1_hostile.py`.

**Interfaces:** `BiologySpec`, `HiddenPopulation`, `generate_hidden_population(spec, rng_factory)`.

- [ ] RED structural tests require overlapping programs, heterogeneous signs/magnitudes/sparsity, common/rare/weak/null, additive/nonlinear, donor recurrence/donor-specific, context and perturbation mechanisms.
- [ ] Reject C1–C6/query/target/representation labels or structural mirrors from generator schema; changing controller candidate mapping cannot change population bytes.
- [ ] Require out-of-basis worlds and prohibit PR #328 contiguous disjoint-block production geometry.
- [ ] **§22.7:** explicit hostile test that generator outputs contain no gate verdict/PASS/FAIL labels; gate verdicts must be created only by controller functions in Task 7/11.
- [ ] Implement, test → PASS, commit, fresh-context review.

### Task 5: Physical observation and stress geometry

**Files:** create `scripts/production_synthetic/observation_v1.py`, `tests/production_synthetic/test_observation_v1.py`, `tests/production_synthetic/test_observation_v1_hostile.py`.

**Interfaces:** `ObservationBundle`, physical RNA/ATAC/fragment observers, `thin_measured_scalar_by_cell(...) -> ThinnedMeasurement` where the result binds thinned counts and the corresponding normalization-library quantity.

- [ ] Test imbalanced/ragged donor×operator allocation, source-asymmetric support, held-out/source-shift and balanced control regimes, including authenticated real support holes when available.
- [ ] RNA: nonnegative integer counts, nonlinear depth/detection, measured zero retained as measurement.
- [ ] ATAC/fragments: bound genome/contig/TSS/peak-or-tile namespace and sparse physical process; dense expected-state teacher shortcut rejected.
- [ ] Same-nucleus quality coupling; separate-nucleus independent draws and row-alignment hostile tests.
- [ ] Ambient RNA/doublet pseudo-rarity does not activate rare biological truth; matched perturbation null shares delivery burden; contaminated null is controller-detectable.
- [ ] **V3.1 §13 + N4 synthetic thinning:** `thin_measured_scalar_by_cell` operates only on `MEASURED_SCALAR` count entries, keys randomness to cell/scientific identity, passes `STRUCTURALLY_UNMEASURED` and `MEASURED_COLLISION_UNRESOLVED` through unchanged, preserves a thinned-to-zero value as `MEASURED_SCALAR`, and recomputes/thins the corresponding normalization-library quantity under the same measurement realization.
- [ ] Hostile test rejects counts-thinned/library-unthinned inconsistency and rejects exposure of the original full-depth library after thinning.
- [ ] **N5:** do not import, wrap, copy, or use the PR #343 thinning function as production implementation authority; implement prospectively from this contract and verify no dependency on storage order.
- [ ] **§22.14:** any repeated-realization depth stress is explicitly tagged `SYNTHETIC_ONLY` and cannot be used as human real-lane authority.
- [ ] Implement, test → PASS, commit, fresh-context review.

### Task 6: Four-state evidence rights and non-vacuous support coverage

**Files:** create `scripts/production_synthetic/evidence_v1.py`, `tests/production_synthetic/test_evidence_v1.py`, `tests/production_synthetic/test_evidence_v1_hostile.py`.

**Interfaces:** `AddressState`, `RightsToken`, `EvidenceLevel`, `SupportCoverageRequirement`, `build_rights_ladder`, `apply_rights`, `validate_visible_invariance`.

- [ ] State tests distinguish `STRUCTURALLY_UNMEASURED`, `MEASURED_SCALAR`, `MEASURED_COLLISION_UNRESOLVED`, `WITHHELD_BY_EVIDENCE_RIGHTS`; measured zero remains scalar.
- [ ] Eligibility is value-independent and measured zero remains eligible.
- [ ] Rights tokens bind canonical content hashes; strict nested membership; terminal full rights; no removal.
- [ ] Leakage tests: visible bytes invariant across levels; hidden totals/nGenes descendants absent; poisoned withheld values cannot affect visible inputs.
- [ ] Anti-thinning tests reject depth/count thinning mislabeled as biological-evidence restriction.
- [ ] **§20/§22.9:** freeze per-state, per-source/operator-stratum minimum instance counts from executor resolution mathematics + applicability law before qualification.
- [ ] Add separate poison tests for `STRUCTURALLY_UNMEASURED` and `MEASURED_COLLISION_UNRESOLVED`; add separate swap and poison tests for `WITHHELD_BY_EVIDENCE_RIGHTS`. A global/masked-only poison test is insufficient.
- [ ] Implement, test → PASS, commit, fresh-context review.

### Task 7: Controller truth, R1 object, novelty and estimability

**Files:** create `scripts/production_synthetic/controller_truth_v1.py`, `tests/production_synthetic/test_controller_truth_v1.py`, `tests/production_synthetic/test_controller_truth_v1_hostile.py`.

**Interfaces:** `ControllerTruth`, `EstimabilityClass`, `derive_expected_state_truth`, `derive_latent_fidelity_truth`, `derive_estimability`, `derive_novelty`, `derive_gate_verdict`.

- [ ] R1 uses anchored cell triplets with one common coordinate set; expected-state and latent-fidelity truths stay separate; depth asymmetry cannot change expected truth.
- [ ] Provisional R1 metric/tau is `PROSPECTIVE_CONVENTION`; no same-code-path status before the complete pinned executor supplies exact metric/scaling/ruler/tie/null/aggregation.
- [ ] Estimability tests cover three controller classes and numerical failure; pinned executor finite-sample law determines underpowering where available.
- [ ] Novelty separates biological novelty, donor familiarity and measurement OOD.
- [ ] **§22.7:** `derive_gate_verdict(...)` is the only gate-verdict construction path; hostile test rejects generator-supplied verdict labels or verdict fields.
- [ ] Implement, test → PASS, commit, fresh-context review.

### Task 8: Hostile controls and pre-exposure realism metrics

**Files:** create `scripts/production_synthetic/controls_v1.py`, `tests/production_synthetic/test_controls_v1.py`.

**Interfaces:** `ControlApplicability`, `ControlResult`, `build_control_matrix`, `evaluate_control`.

- [ ] During implementation, use fixture worlds from a non-production test generator only.
- [ ] Freeze applicability before exposure; applicable controls are hard gates.
- [ ] Cover wrong/permuted query, query-agnostic capacity control, semantic/nuisance twins, randomized relational/graph, source/library/marker-only, capacity-only composite, perturbation null/contaminated-null, value-permutation and support/mask-swap controls.
- [ ] **N6:** add a library-size-only R1 negative control in which library/depth cues exist but expected-state R1 truth carries no corresponding biological relation signal; success driven by the library-only cue is shortcut failure. The control role stays controller-only and applicability/hard-gate status freezes before exposure.
- [ ] Do not treat PR #353 as providing this adversarial control family; #353 remains semantics fixture only.
- [ ] Null-draw counts come from precision budget.
- [ ] Trivial-baseline ceilings carry numeric provenance and are evaluated as pre-exposure realism metrics; convention ceilings require frozen sensitivity analysis.
- [ ] Implement, fixture-test → PASS, commit, fresh-context review. No production exposure occurs in this task.

### Task 9: Default-deny fit/controller packaging and custody

**Files:** create `scripts/production_synthetic/package_v1.py`, `tests/production_synthetic/test_package_v1.py`, `tests/production_synthetic/test_package_v1_hostile.py`.

**Interfaces:** `build_fit_transport`, `build_controller_transport`, `build_manifest`, `verify_transport_separation`.

- [ ] Fit allowlist excludes latent/expected state, outcomes, estimability truth, challenge/perturbation roles, twin linkage, candidate mapping and controller verdicts.
- [ ] Opaque exchangeable IDs and chance-level role-predictability test.
- [ ] Raw/semantic hash and order invariance.
- [ ] Commitment tests prove withheld plaintext and withheld-only code are absent before reveal and realization set is bound before scoring; production secret remains controller-only/off-repo.
- [ ] **§22.8:** manifest records historical R5 prose PASS claims as `DESIGN_TEXT_PRESENT__NOT_TESTED`, never executable evidence.
- [ ] **§22.12:** normalize Stage70/71 history to #325 authority labels (`NEGATIVE_PRIOR` / `INTERNAL_ROBUSTNESS_ONLY` as applicable), not conflicting legacy labels.
- [ ] Implement, test → PASS, commit, fresh-context review.

### Task 10: Moving-head downstream bindings and guarded adapters

**Files:** create `scripts/production_synthetic/downstream_rehearsal_v1.py`, `tests/production_synthetic/test_downstream_rehearsal_v1.py`.

**Interfaces:** `CodePathClass`, `DownstreamBinding`, `classify_binding`, `invoke_binding`.

- [ ] All implementation/review calls use fixture worlds only; no production generator realization in Task 10.
- [ ] Machine-readable fixture binds exact head for every open dependency and fails closed on any movement. A test-only move still requires explicit `BRANCH_MOVED_NO_SCIENTIFIC_EXECUTABLE_CHANGE` reclassification.
- [ ] Reproduce classifications above; green CI alone cannot upgrade anything.
- [ ] G6, G8, R1, TargetPortfolio remain `NOT_REHEARSED_BLOCKED_EXTERNAL`.
- [ ] G7 remains fixture-only until real validator enforces E3 content semantics.
- [ ] **#355:** do not attempt promotion on current implementation. Encode `IMPLEMENTATION_REPAIR_REQUIRED_BEFORE_PROMOTION` with hostile fixtures for: one-donor-short null resolution must not hide a measurable FAIL as NOT_ESTIMABLE; extra-source rows must not be silently discarded; leakage/null/seed invariants must be enforced inside the executor rather than accepted as caller flags/precomputed displacement. A later repaired exact head requires a separate reviewed binding artifact before any `SAME_CODE_PATH` proposal.
- [ ] Implement, fixture-test → PASS, commit, fresh-context review.

### Task 11: Qualification orchestration — code first, production only behind STOP gates

**Files:** create `scripts/production_synthetic/qualification_v1.py`, `tests/production_synthetic/test_qualification_v1.py`, `tests/production_synthetic/test_qualification_v1_hostile.py`.

**Interfaces:** `QualificationResult`, `run_pre_exposure_realism`, `run_synthetic_qualification`, `aggregate_hard_statuses`.

- [ ] Implement/test on fixture worlds: first-pass realism stopping, budget exhaustion, source/cohort-confounded/deconfounded twins, no hidden-biology tuning.
- [ ] Hard-status aggregation: false certainty, false abstention where truly estimable, numerical/custody/control failure cannot be averaged away.
- [ ] E5: underpowered permits calibrated COMPLETE or NOT_ESTIMABLE; derive underpowering from executor finite-sample law whenever available.
- [ ] Per-program/per-rare-stratum output; donor-spread and 1–2-donor concentrated rare regimes.
- [ ] Evidence curves report realized full-reference, expected-state and latent-truth views separately.
- [ ] Implement all code/tests and pass fixture suite.
- [ ] **STOP_A_FIRST_PRODUCTION_REALIZATION:** obtain fresh authorization before creating the first production-version realization.
- [ ] After STOP_A authorization, run `run_pre_exposure_realism(...)`; freeze the first jointly passing production version, then call `record_exposure(...)` on the first downstream invocation.
- [ ] **STOP_B_SEALED_QUALIFICATION:** obtain separate fresh authorization before generating/running sealed qualification realizations.
- [ ] Only after STOP_B may `run_synthetic_qualification(...)` execute on sealed production worlds.
- [ ] Commit code separately from any later authorized execution receipts.

### Task 12: Finalizer, workflow and immutable receipt

**Files:** create `scripts/production_synthetic/finalize_v1.py`, `tests/production_synthetic/test_finalize_v1.py`, `requirements/production-synthetic-v1.txt`, `.github/workflows/production-synthetic-v1.yml`.

**Interfaces:** `finalize_package(inputs) -> FinalReceipt`.

- [ ] Tests require exact source/dependency hashes, both controlling spec Git blob SHA identities **and the full 64-character SHA-256 values** listed at the top of this plan and in the F1/N3–N6 addendum, numeric provenance, registries, custody commitments/reveals, complete realization set, controls, code-path classifications and all authority fields false.
- [ ] Negative tests reject shortened/truncated spec SHA-256 strings, blocked gates promoted to PASS, missing provenance/withheld commitment, and `POST_EXPOSURE_VERSION` without full requalification lineage.
- [ ] Workflow runs `tests/production_synthetic/` and eligible inherited fixture regressions only; never human outcomes/successor-estimator qualification.
- [ ] Pin runtime requirements and record exact execution versions in receipt.
- [ ] Implement and run fixture/local test suite; no finalizer invocation yet.
- [ ] **STOP_C_FINALIZER:** after an authorized sealed qualification has frozen its evidence, obtain fresh authorization before `finalize_package(...)`.
- [ ] Only after STOP_C invoke finalizer once, verify raw/semantic receipt identity and false authority fields, then custody the exact bytes.

## Explicitly out of scope

- Resolving G6 human margin contract.
- Resolving G8 realization/reference/displacement/support-fraction semantics or executing human G8.
- Completing the real R1 executor.
- Repairing/qualifying TargetPortfolio beyond tracking external repair.
- Upgrading G7 before real content enforcement.
- Repairing #355 in the synthetic branch; real-lane implementation repair is external.
- Resolving V79 terminal-lock vs V80 291-pass successor-selection law.
- Successor estimator, human target tournament, target/representation selection, TD60, Stage4 or training.

## Plan self-review after P1–P6 + F1/N3–N6

- **P1:** fixture-only Tasks 8/10; production first exposure is after realism freeze and goes through `record_exposure`.
- **P2/N3:** production withheld spec is controller-authored off-repo; subagents never see it; public mechanism code must be exercised outside the withheld family or remain off-repo; private tree-scan attestation covers both plaintext and unique-code-path leakage.
- **P3:** STOP_A, STOP_B and STOP_C require fresh authorization.
- **P4:** §20/§22.9 state/stratum minima + distinct poison tests, §13 thinning, §22.14 synthetic-only repeated depth, §22.13 address-universe check, §22.8 R5 label, §22.12 Stage70/71 labels, §22.7 controller-only verdicts are all assigned to owning tests.
- **N4/N5:** Task 5 thins measured-scalar counts and the matching normalization library under cell-identity keyed randomness, preserves support states, and does not reuse #343's thinning implementation.
- **N6:** Task 8 owns a library-size-only adversarial R1 negative control; #353 is not treated as hostile-control authority.
- **P5:** #351 updated to `2abcb9fe…`; G8 status updated; every moving dependency fails closed on head movement; #355 cannot promote without implementation repair and separate review.
- **P6/F1:** controlling specs are cited by Git blob SHA and full 64-character SHA-256; Task 12 explicitly rejects shortened forms.
- **N1/N2:** executor finite-sample estimability and in-repo controlling spec identities remain explicit.
- **Authority:** unchanged and false throughout.

## Execution handoff

Execution mode is **subagent-driven**, sequential on one stacked branch. Each task requires a separate fresh-context implementer and fresh-context reviewer; no subagent touches real-lane PRs. The controller alone manages the withheld-family secret. Tasks 1–3 may start now. Task 4 begins only after Tasks 1–3 each clear their per-task reviews. Production realizations, sealed qualification and finalization remain separately authorization-gated.
