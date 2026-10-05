# JEPA Premise Qualification Program Implementation Plan — Audited V2

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` for Native execution. Execute Tasks 1–7 sequentially and stop before merge for independent Task-8 review.

**Goal:** Publish a fail-closed premise-governance system for future real-RNA target/representation work without authorizing training or Stage-A execution.

**Architecture:** The audited design spec is binding. Human-readable and machine-readable contracts define P1–P6, representation neutrality, claim promotion, Stage-A prefreeze, external-asset roles, estimand choices and synthetic-scale authority. A governance validator/CI workflow prevents semantic drift. No model/training/scientific-result code is changed.

**Tech Stack:** Markdown, JSON, Python 3.12, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-05-premise-qualification-contract-design.md`

## Global constraints

- `TRAINING=OFF`; encoder optimizer updates = 0; EMA updates = 0.
- Stage A remains `PREFREEZE_EXECUTION_CONTRACT__NOT_EXECUTION_AUTHORITY`.
- TEST sealed; Morabito protected; 500K and Stage 4 unauthorized.
- No target, representation, estimand or deciding numeric margin is selected.
- Distinguish `TARGET_OBJECT_RECOVERABILITY` from `BIOLOGICAL_TRUTH_RECOVERABILITY`.
- Track donor/operator/study/technology transfer as separate axes, not one nested pass ladder.
- Fitted diagnostics use inner TRAIN only, freeze before held-donor evaluation, and cannot retune target definition.
- Rare/novel RNA structure is not automatically biological novelty.
- World A/96 is `REDUCED_MEASUREMENT_AND_METRIC_CONTROL_WORLD`.
- Any synthetic result used to qualify canonical production-pipeline behavior requires the canonical 41,238-address identity universe or a prospectively justified equivalent; padding with independent noise is insufficient.
- Task 5 consolidates existing audited evidence from PRs #188–#199 and audits only missing fields.
- Task 6 presents estimand candidates but leaves `selected_estimand=UNSET_REQUIRES_APPROVAL`.
- Authority freshness must be updated whenever current work closes or changes.

## Review focus

1. No document may imply that publication of Stage A authorizes its execution.
2. No real-RNA observation-defined recoverability quantity may be labeled biological-truth recoverability.
3. No representation may silently privilege `cell_state` or one-vector compression.
4. No missing transfer axis may be upgraded to pass.
5. No 96-feature synthetic result may qualify production-scale 41,238-address pipeline behavior.
6. No claim promotion may occur automatically.
7. No post-hoc threshold/readout/target tuning may be permitted.

---

### Task 1 — Publish the premise authority

**Create:**
- `docs/agent/JEPA_PREMISE_QUALIFICATION_CONTRACT_20261005.md`
- `docs/agent/JEPA_PREMISE_QUALIFICATION_STATE_20261005.json`
- `tests/governance/test_premise_qualification_contract.py`

**RED assertions:** state absent; then require P1–P6, seven Stage-A verdicts, `training_authorized=false`, `stage_a_execution_authorized=false`, TEST/Morabito closed, no target/representation/estimand selected, recoverability semantics split, and 96-vs-41K scale firewall.

**GREEN implementation:** publish human + machine authority directly from spec. All unresolved numeric margins use `UNSET_REQUIRES_APPROVAL`.

**Commit:** `govern: publish audited premise qualification contract`

### Task 2 — Freeze representation-family comparison

**Create:**
- `docs/agent/JEPA_REPRESENTATION_FAMILY_QUALIFICATION_20261005.md`
- `docs/agent/JEPA_REPRESENTATION_FAMILY_QUALIFICATION_20261005.json`
- `tests/governance/test_premise_representation_contract.py`

**RED assertions:** exactly `GLOBAL_CELL_STATE`, `QUERY_LOCAL_STATE`, `PROGRAM_STATE`, `STRUCTURED_COMBINED_STATE`; no winner/default; `cell_state` not qualified by name; each family declares intended scope, legitimate losses, shortcut behavior, transfer axes, rare/novel RNA behavior and maximum claim level before external evidence.

**GREEN implementation:** dimensionality unspecified; structured family is not preselected either.

**Commit:** `govern: freeze representation family comparison`

### Task 3 — Freeze claim ladder and promotion firewall

**Create:**
- `docs/agent/JEPA_CLAIM_LADDER_20261005.md`
- `docs/agent/JEPA_CLAIM_LADDER_20261005.json`
- `tests/governance/test_jepa_claim_ladder.py`

**RED assertions:** four claim levels; every adjacent promotion requires new independent evidence; no transitive auto-promotion; Stage A maximum = RNA representation.

**GREEN implementation:** explicitly prohibit masked-RNA success -> biology, RNA/ATAC association -> regulatory qualification, observational prediction -> intervention effect.

**Commit:** `govern: freeze JEPA claim ladder`

### Task 4 — Freeze Stage-A real-RNA prefreeze contract

**Create:**
- `docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_20261005.md`
- `docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_20261005.json`
- `tests/governance/test_stage_a_real_rna_gate.py`

**RED assertions:** prefreeze/not execution authority; optimizer/EMA zero; TEST/Morabito closed; leakage/shortcut absolute fail; target-object vs biological-truth recoverability split; separate transfer axes; diagnostic readout firewall; thresholds cannot originate `POST_HOC`; no external asset used for target selection.

**GREEN implementation:** freeze metric names/directions/negative controls/resampling/estimand slots/stop conditions and seven top-level verdicts. Keep open numeric margins unset.

**Commit:** `govern: freeze Stage-A real-RNA prefreeze gate`

### Task 5 — Consolidate external-validation evidence against claim ladder

**Create:**
- `docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_20261005.md`
- `docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_20261005.json`

**Evidence rule:** start from existing PRs #188–#199 and primary ETL/audit artifacts. Do not redo completed audits. For each asset record modality, biological-unit count, pairing, prior exposure, protected/sealed status, independence class, claim transitions it can/cannot test, and provenance grade. Missing facts = `UNKNOWN_REQUIRES_AUDIT`.

Morabito = `PROTECTED_NOT_AVAILABLE_FOR_SELECTION`; exposed assets are not called pristine independent validation; observational multimodal association never receives causal authority.

**Commit:** `audit: consolidate external assets against claim ladder`

### Task 6 — Freeze foundation-population estimand choices without choosing

**Create:**
- `docs/agent/JEPA_FOUNDATION_POPULATION_ESTIMAND_DECISION_20261005.md`
- `docs/agent/JEPA_FOUNDATION_POPULATION_ESTIMAND_DECISION_20261005.json`
- `tests/governance/test_foundation_estimand_contract.py`

**RED assertions:** candidates include cell-weighted, donor-weighted and source-balanced donor-weighted; each declares target population, weighting algorithm/equation, biological interpretation, failure mode and compatibility with donor-level uncertainty; `selected_estimand=UNSET_REQUIRES_APPROVAL`.

**GREEN implementation:** state how each changes the meaning of “good on FULL104”; select none.

**Commit:** `govern: freeze foundation estimand choices`

### Task 7 — Add premise-authority consistency guard

**Create:**
- `scripts/governance/verify_premise_qualification_surface.py`
- `tests/governance/test_verify_premise_qualification_surface.py`
- `.github/workflows/premise-qualification-surface-guard.yml`

**RED adversarial mutations:** training authorized; Stage-A execution authorized; target/representation/estimand selected; `cell_state` default-qualified; TEST/Morabito opened; target-object recoverability promoted to biological-truth recoverability; transfer axes collapsed; post-hoc threshold; nonrecoverable component treated as model failure; claim auto-promotion; 96-feature world promoted to production-scale pipeline authority; independent-noise padding accepted as 41K scale.

**GREEN implementation:** expose `validate_surface(paths: Mapping[str, Path]) -> list[str]`; CLI nonzero on any violation. Workflow runs focused governance tests and rejects skips/xfails/deselections.

**Commit:** `ci: guard audited premise qualification surface`

### Task 8 — Independent whole-branch review; stop before merge

Compare exact branch against current main and verify only docs/governance validator/tests/workflow changes. Run full governance suite. Independent reviewer attacks: scientific overclaim, post-hoc flexibility, implicit representation winner, recoverability semantics, transport overreach, 96->41K scale leakage, synthetic->real contamination, external-asset independence, estimand selection, authority freshness.

Resolve Critical/Important findings through one RED->GREEN fix pass. Do **not** merge until independent review is clean and explicitly reported.
