# V5 Masking Authority Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete prospective masking-authority stack so FULL104 execution can be frozen before qualification outcomes are inspected.

**Architecture:** Keep partner-selection policy, mask burden, precision, donor splits, target panels and address-universe ladder as separate hash-bound authorities. A qualification-design authority binds them into one prospective contract; no exploratory numeric value becomes production authority implicitly.

**Tech Stack:** Python 3.12, dataclasses, hashlib/json, pytest, existing `sea_ad_jepa.v5` authority patterns.

**Spec:** `docs/superpowers/specs/2026-09-17-v5-production-authority-closure-design.md`

## Global Constraints

- TRAINING_OFF.
- Protected/pathology/DEV/SEALED/D_shared outcomes remain sealed.
- Expression prediction is an anti-shortcut diagnostic only.
- Target evidence budget is separate from masking partner selection.
- No free-form behavioral identifiers.
- Every authority validates SHA-256 roots and emits a deterministic canonical digest.

---

### Task 1: Target evidence-budget authority

**Files:**
- Create: `src/sea_ad_jepa/v5/target_evidence_budget_authority_v1.py`
- Create: `tests/test_v5_target_evidence_budget_authority_v1.py`

**Interfaces:**
- Produces: `TargetEvidenceBudgetAuthorityV1.validate()`, `.canonical_digest()`, `.mask_count(eligible_count:int)->int`.
- Consumes: explicit rational burden and minimum retained evidence; no masking-policy identifiers.

- [ ] **Step 1: Write failing tests** for rational burden validation, exact deterministic mask count, minimum-retained-evidence fail-closed behavior, and `training_authorized=False`.
- [ ] **Step 2: Run** `python -m pytest -q tests/test_v5_target_evidence_budget_authority_v1.py` and require failure because the module is absent.
- [ ] **Step 3: Implement** a frozen dataclass with enumerated `budget_semantics_id='MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1'`, numerator/denominator, minimum retained count, infeasible-policy enum and canonical digest.
- [ ] **Step 4: Run the test file** and require PASS with zero skips.
- [ ] **Step 5: Commit** `feat(v5): add target evidence budget authority`.

### Task 2: Precision authority

**Files:**
- Create: `src/sea_ad_jepa/v5/precision_authority_v1.py`
- Create: `tests/test_v5_precision_authority_v1.py`

**Interfaces:**
- Produces: `QualificationPrecisionAuthorityV1` binding minimum targets, minimum target-fold units, uncertainty method and insufficient-support semantics.

- [ ] **Step 1: Write failing tests** requiring enumerated target-clustered uncertainty, positive sample minima, valid rational confidence level, and explicit fail-closed insufficient-support behavior.
- [ ] **Step 2: Run** the focused test and confirm RED.
- [ ] **Step 3: Implement** the dataclass and deterministic digest; do not supply production numeric defaults.
- [ ] **Step 4: Run** the focused test and require PASS.
- [ ] **Step 5: Commit** `feat(v5): add qualification precision authority`.

### Task 3: Outer split, target panel and address-universe authorities

**Files:**
- Create: `src/sea_ad_jepa/v5/outer_split_authority_v1.py`
- Create: `src/sea_ad_jepa/v5/target_panel_authority_v1.py`
- Create: `src/sea_ad_jepa/v5/address_universe_ladder_authority_v1.py`
- Create: `tests/test_v5_masking_design_population_authorities_v1.py`

**Interfaces:**
- `OuterDonorSplitAuthorityV1`: binds deterministic donor IDs/fold assignment artifact and forbids held-out donor use in fit/screen.
- `TargetPanelAuthorityV1`: binds deterministic outcome-blind selector artifact and exact target-list root.
- `AddressUniverseLadderAuthorityV1`: binds ordered universe roots and requires terminal `FULL_COMMON_CORE_17186_V1`.

- [ ] **Step 1: Write failing tests** for missing/duplicate donors, target-panel outcome-selection prohibition, universe ordering uniqueness and required terminal common-core entry.
- [ ] **Step 2: Run** focused tests and confirm RED.
- [ ] **Step 3: Implement** the three authorities with exact digest validation and enumerated semantics.
- [ ] **Step 4: Run** tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): bind masking qualification population design`.

### Task 4: Deterministic masking RNG/replay authority

**Files:**
- Create: `src/sea_ad_jepa/v5/masking_rng_replay_authority_v1.py`
- Create: `tests/test_v5_masking_rng_replay_authority_v1.py`

**Interfaces:**
- Produces `MaskingRngReplayAuthorityV1` with common-random-base seed semantics and explicit rule that policy name is absent from the base-mask seed.

- [ ] **Step 1: Write failing tests** rejecting policy-dependent base seeds and free-form RNG identifiers.
- [ ] **Step 2: Run** tests and confirm RED.
- [ ] **Step 3: Implement** enumerated replay/seed composition authority with bound canonical registry/split/panel roots.
- [ ] **Step 4: Run** tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): add deterministic masking replay authority`.

### Task 5: Masking qualification design authority

**Files:**
- Create: `src/sea_ad_jepa/v5/masking_qualification_design_authority_v1.py`
- Create: `tests/test_v5_masking_qualification_design_authority_v1.py`
- Modify: `analysis/v5_masking_successor_spike_20260917/contracts/validate_masking_successor_contract_draft.py`

**Interfaces:**
- Produces `MaskingQualificationDesignAuthorityV1` binding FULL104, representation, support, canonical registry, teacher semantics, evidence budget, precision, split, panel, universe ladder and RNG roots.
- Approved comparator set is exactly `UNIFORM_RANDOM`, `TOP8_CORRELATION`, `RIDGE8_CONDITIONAL`, `PREFIX3_SELECTIVE`.

- [ ] **Step 1: Write failing tests** for missing roots, role-spliced digests, comparator drift, nonterminal common-core universe, expression attacker becoming training loss, and protected-outcome authorization.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** the authority with enumerated primary/secondary attacker roles, paired target×fold estimand, target-clustered uncertainty binding and required controls.
- [ ] **Step 4: Upgrade the draft validator** to validate against this schema without filling unresolved scientific numbers.
- [ ] **Step 5: Run** focused tests and contract validator; require PASS.
- [ ] **Step 6: Commit** `feat(v5): add prospective masking qualification design authority`.

### Task 6: Integrate masking stack into current spillover/closure tests

**Files:**
- Modify: `src/sea_ad_jepa/v5/current_masking_policy_authority_v2.py`
- Modify: `tests/test_v5_current_masking_policy_authority_v2.py`
- Modify: `tests/test_v5_current_stage_a_spillover_firewall_v1.py`
- Modify: `tests/test_v5_current_stage_a_spillover_firewall_v2.py`

**Interfaces:**
- `CurrentMaskingPolicyAuthorityV2` keeps partner selection separate but must bind real evidence-budget and RNG authority digests.

- [ ] **Step 1: Add failing tests** proving arbitrary 64-char placeholders cannot stand in for wrong authority roles when live binders are supplied.
- [ ] **Step 2: Run** focused tests and confirm RED.
- [ ] **Step 3: Add explicit binder helpers** for evidence budget/RNG/support/registry role equality; preserve schema compatibility where possible.
- [ ] **Step 4: Add all new current masking modules to Stage-A spillover source tracking; quarantine no current module.
- [ ] **Step 5: Run** all masking, Stage-A and closure tests with a no-skip guard.
- [ ] **Step 6: Commit** `fix(v5): bind complete current masking authority stack`.
