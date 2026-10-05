# JEPA Premise Qualification Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish and operationalize the prospective premise-qualification framework that constrains future real-RNA target/representation experiments before any deciding TRAIN-only result is opened.

**Architecture:** Keep the program docs/governance-first. The frozen design remains the source of truth; implementation consists of machine-readable contracts, human-readable qualification specifications, validation scripts/tests for governance consistency, and separate audit artifacts for representation families, claim levels, external-validation assets, and the foundation-population estimand. No model/training code is changed by this plan.

**Tech Stack:** Markdown, JSON, Python 3.12 governance validators, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-05-premise-qualification-contract-design.md`

## Global Constraints

- `TRAINING=OFF` throughout this plan.
- Encoder optimizer updates = 0 and EMA updates = 0 for target-selection work.
- TEST remains sealed; Morabito remains protected.
- No 500K promotion or Stage-4 authorization.
- No target or representation winner is selected by this plan.
- Numeric margins remain `UNSET_REQUIRES_APPROVAL` unless bound to pre-existing independent authority or a prospectively approved calibration procedure.
- Lower claim levels never automatically promote to higher claim levels.
- Synthetic Worlds A/B/C/D may validate metric behavior but may not retrofit real-RNA target meaning or deciding thresholds.
- The 41,238-address ledger is the lawful RNA observation universe, not complete cellular state.

## Review Focus

1. A future agent must not infer that `QUALIFIED_FOR_RNA_REPRESENTATION` authorizes production training or a transferable-biological-state claim.
2. A biologically relevant but nonrecoverable component must not be converted into a model-failure verdict.
3. Representation comparisons must not privilege `cell_state` or a single-vector design by default.
4. Transport claims must preserve the hierarchy donor < operator < study < technology and must not upgrade missing higher-level evidence to a pass.
5. Any deciding threshold introduced after candidate outcomes are visible must be rejected by governance validation.

---

### Task 1: Publish the prospective premise contract as project authority

**Files:**
- Existing spec: `docs/superpowers/specs/2026-10-05-premise-qualification-contract-design.md`
- Create: `docs/agent/JEPA_PREMISE_QUALIFICATION_CONTRACT_20261005.md`
- Create: `docs/agent/JEPA_PREMISE_QUALIFICATION_STATE_20261005.json`

**Interfaces:**
- Consumes: frozen design spec.
- Produces: one human-readable project contract and one machine-readable state object carrying P1-P6, protected boundaries, verdict enums, and `training_authorized=false`.

- [ ] **Step 1: Write schema/contract assertions before publishing the authority files**

Create tests asserting the JSON contains P1-P6, the seven Stage-A verdicts, `training_authorized=false`, `test_open=false`, `morabito_open=false`, and no selected target/representation.

- [ ] **Step 2: Run the tests and verify RED**

Expected: FAIL because the machine-readable state file does not yet exist.

- [ ] **Step 3: Create the human-readable authority and machine-readable state from the approved spec**

The state must represent unset numeric margins as `UNSET_REQUIRES_APPROVAL`, not `null` interpreted as permission.

- [ ] **Step 4: Run tests and verify GREEN**

Expected: all contract-schema assertions PASS.

- [ ] **Step 5: Commit**

Commit message: `govern: publish premise qualification contract`

### Task 2: Formalize representation-family qualification

**Files:**
- Create: `docs/agent/JEPA_REPRESENTATION_FAMILY_QUALIFICATION_20261005.md`
- Create: `docs/agent/JEPA_REPRESENTATION_FAMILY_QUALIFICATION_20261005.json`
- Test: `tests/governance/test_premise_representation_contract.py`

**Interfaces:**
- Consumes: Task 1 machine-readable premise state.
- Produces: frozen comparison definitions for `GLOBAL_CELL_STATE`, `QUERY_LOCAL_STATE`, `PROGRAM_STATE`, `STRUCTURED_COMBINED_STATE`.

- [ ] **Step 1: Write failing tests for representation neutrality**

Assert exactly the four required families exist; none is marked winner/default; `cell_state` is not qualified by name; each family has required evidence fields for global, local, program, rare/novel, shortcut and transport behavior.

- [ ] **Step 2: Run targeted test and verify RED**

- [ ] **Step 3: Publish representation-family contract**

For each family define: extraction object, intended biological scope, information it may legitimately lose, mandatory controls, minimum transport evidence, and allowed verdicts. Keep dimensionality unspecified.

- [ ] **Step 4: Run targeted test and full governance suite**

Expected: PASS with zero skips.

- [ ] **Step 5: Commit**

Commit message: `govern: freeze representation family comparison`

### Task 3: Formalize the claim ladder and promotion firewall

**Files:**
- Create: `docs/agent/JEPA_CLAIM_LADDER_20261005.md`
- Create: `docs/agent/JEPA_CLAIM_LADDER_20261005.json`
- Test: `tests/governance/test_jepa_claim_ladder.py`

**Interfaces:**
- Consumes: Task 1 premise state.
- Produces: four claim levels and explicit evidence required for promotion between adjacent levels.

- [ ] **Step 1: Write failing promotion tests**

Assert `RNA_REPRESENTATION -> TRANSFERABLE_BIOLOGICAL_STATE` requires independent transport/semantic evidence; `TRANSFERABLE_BIOLOGICAL_STATE -> REGULATORY_SUPPORT` requires independent chromatin/regulatory evidence; `REGULATORY_SUPPORT -> CAUSAL_PERTURBATIONAL_PREDICTION` requires intervention evidence. Assert no transitive auto-promotion.

- [ ] **Step 2: Run tests and verify RED**

- [ ] **Step 3: Create claim-ladder artifacts**

Include forbidden inference examples: masked-RNA success != biological validity; RNA/ATAC association != regulatory qualification; observational prediction != intervention effect.

- [ ] **Step 4: Run tests and verify GREEN**

- [ ] **Step 5: Commit**

Commit message: `govern: freeze JEPA claim ladder`

### Task 4: Freeze the Stage-A real-RNA target/representation execution contract

**Files:**
- Create: `docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_20261005.md`
- Create: `docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_20261005.json`
- Test: `tests/governance/test_stage_a_real_rna_gate.py`

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: executable governance contract for a future TRAIN-only, zero-encoder-update target/representation discrimination experiment.

- [ ] **Step 1: Write failing tests for hard boundaries and verdict semantics**

Assert optimizer/EMA updates are zero; TEST and Morabito closed; leakage and shortcut are absolute-fail gates; donor-level uncertainty is mandatory; absence of higher transport levels is `TRANSPORT_LEVEL_NOT_TESTED`, never PASS; deciding thresholds cannot have origin `POST_HOC`.

- [ ] **Step 2: Run targeted test and verify RED**

- [ ] **Step 3: Publish Stage-A gate**

Freeze metric names, comparison directions, negative-control roster, resampling unit declaration, estimand declaration slots, stop conditions, and allowed verdicts. Leave unjustified numeric margins unset.

- [ ] **Step 4: Run targeted test and governance suite**

Expected: PASS with zero skips.

- [ ] **Step 5: Commit**

Commit message: `govern: freeze Stage-A real-RNA qualification gate`

### Task 5: Audit external-validation assets against the claim ladder

**Files:**
- Create: `docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_20261005.md`
- Create: `docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_20261005.json`

**Interfaces:**
- Consumes: Task 3 claim ladder and repository provenance/audit records.
- Produces: dataset-by-claim matrix for ATAC, SCENIC+, GSE214979, Morabito, perturbation and spatial assets, including prior exposure and independence status.

- [ ] **Step 1: Inventory candidate assets from repository authorities**

For every asset record modality, biological-unit count, pairing structure, prior project exposure, protected/sealed status, and which claim transitions it can and cannot test.

- [ ] **Step 2: Cross-check provenance against primary ETL/audit artifacts**

Do not infer missing donor counts or independence; mark unsupported fields `UNKNOWN_REQUIRES_AUDIT`.

- [ ] **Step 3: Publish human and machine-readable matrices**

Morabito must remain `PROTECTED_NOT_AVAILABLE_FOR_SELECTION`; previously exposed assets must not be labeled pristine independent validation.

- [ ] **Step 4: Self-audit for claim leakage**

Verify no asset is assigned causal authority solely from observational multimodal association and no large cell count substitutes for biological-unit count.

- [ ] **Step 5: Commit**

Commit message: `audit: map external assets to claim levels`

### Task 6: Freeze the foundation-population estimand decision sheet

**Files:**
- Create: `docs/agent/JEPA_FOUNDATION_POPULATION_ESTIMAND_DECISION_20261005.md`
- Create: `docs/agent/JEPA_FOUNDATION_POPULATION_ESTIMAND_DECISION_20261005.json`
- Test: `tests/governance/test_foundation_estimand_contract.py`

**Interfaces:**
- Consumes: FULL104 population/count authorities and Task 1 P5 transport requirements.
- Produces: explicit candidate estimands without silently selecting one: cell-weighted, donor-weighted, source-balanced donor-weighted, plus any evidence-justified alternative.

- [ ] **Step 1: Write failing tests that forbid implicit estimand selection**

Assert every candidate has target population, weighting equation/algorithm, biological interpretation, failure mode and compatibility with donor-level uncertainty; assert `selected_estimand` is `UNSET_REQUIRES_APPROVAL`.

- [ ] **Step 2: Run test and verify RED**

- [ ] **Step 3: Publish estimand decision sheet**

Include how each candidate changes the meaning of “good on FULL104” and which source/donor imbalances it emphasizes or suppresses.

- [ ] **Step 4: Run tests and verify GREEN**

- [ ] **Step 5: Commit**

Commit message: `govern: freeze foundation estimand choices`

### Task 7: Add a premise-authority consistency guard

**Files:**
- Create: `scripts/governance/verify_premise_qualification_surface.py`
- Create: `tests/governance/test_verify_premise_qualification_surface.py`
- Create: `.github/workflows/premise-qualification-surface-guard.yml`

**Interfaces:**
- Consumes: machine-readable artifacts from Tasks 1-6.
- Produces: fail-closed validator that prevents future drift among premise state, representation contract, claim ladder, Stage-A gate and estimand state.

- [ ] **Step 1: Write adversarial tests**

Mutations must fail for: training authorized; target winner selected; `cell_state` promoted to qualified by default; TEST/Morabito opened; claim auto-promotion; post-hoc threshold origin; nonrecoverable truth mapped to model failure; transport hierarchy collapsed.

- [ ] **Step 2: Run tests and verify RED**

Expected: validator import/file missing.

- [ ] **Step 3: Implement minimal validator**

Expose `validate_surface(paths: Mapping[str, Path]) -> list[str]`, returning an empty list only for a consistent surface; CLI exits nonzero on any violation.

- [ ] **Step 4: Run adversarial tests and verify GREEN**

- [ ] **Step 5: Add isolated GitHub Actions workflow**

Trigger only on the premise/representation/claim/gate/estimand files, validator and its tests. Require zero skipped/xfailed/deselected governance tests.

- [ ] **Step 6: Commit**

Commit message: `ci: guard premise qualification authority surface`

### Task 8: Independent review and main-branch publication

**Files:**
- No new scientific files unless review finds defects.

**Interfaces:**
- Consumes: Tasks 1-7.
- Produces: reviewed docs-only/governance PR suitable for merge to `main`.

- [ ] **Step 1: Compare branch to its exact main base**

Acceptance: only docs/governance validator/tests/workflow files; no model, training, result, threshold or protected-data changes.

- [ ] **Step 2: Run full governance tests and compile validator**

Expected: PASS, zero skips.

- [ ] **Step 3: Request independent whole-branch review**

Review focus: scientific overclaim, post-hoc degrees of freedom, implicit representation winner, transport overreach, synthetic-to-real contamination.

- [ ] **Step 4: Resolve review findings without changing scientific rules after seeing deciding data**

- [ ] **Step 5: Merge only after checks/review are clean**

Post-merge verify `main` authority surface and leave `TRAINING=OFF`.
