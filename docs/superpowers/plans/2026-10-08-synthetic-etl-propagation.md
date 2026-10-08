# Synthetic ETL → Generator Propagation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and validate E1–E3 class-aware synthetic worlds under the frozen ETL→generator propagation design, without changing the observer/counting process, runtime authority, target-discovery assets, or real-data training authority.

**Architecture:** Add a small hash-bound class-composition authority derived from the corrected pathology-blind TRAIN calibration, then extend the existing V77 hidden-truth and observer successor path with explicit broad-class assignment, class-shared random-content biology, and within-class continuous biology. Reuse existing V77 matched scoring and corrected S174 replay conventions; preserve World-A/V77 frozen components and add only successor functionality.

**Tech Stack:** Python 3, NumPy, SciPy sparse matrices, pytest, existing V77 generator/observer/scoring utilities, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-08-synthetic-etl-propagation-design.md`

## Global Constraints

- E0 is the current generator and frozen observer; E1–E3 are the only executable new arms in this plan.
- E4 donor×class interaction remains fail-closed and is not implemented or executed here.
- Preserve **real geometry, random content**: real class counts/proportions may be used, but no real gene markers, gene-program memberships, regulatory edges, pathology fields, target-discovery artifacts, or 353-ID remappings may enter class-program content.
- Preserve FULL104 source/donor/operator geometry, 42 operators, 1,400 donor×operator groups, ragged support, zero-quota rescue, structural availability, depth/support targets, count realization, and measurement-seed rules.
- E1–E3 class assignment and within-class state must not key from donor, source, or operator.
- E2 class-program scale is exactly the inherited V77 B1 state scale `0.55`; E3 uses two dimensions at `0.55 / sqrt(2)` each.
- Corrected S174 real values are descriptive references; S159 intervals are not binary qualification gates.
- No JEPA training, optimizer mutation, production EMA selection, TEST/Morabito access, 500K, Stage 4, target freeze, representation freeze, or production estimand selection.

## Review Focus

- **Tiny classes at small N:** deterministic largest-remainder allocation must reconcile exactly to N, and scoring must not silently imply every class satisfies the 200-cell T5 floor.
- **Label/order instability:** class ordering must be frozen in the authority artifact; dictionary or filesystem iteration order must never alter assignments.
- **Shard-size dependence:** class assignments and continuous states must be identical for the same global cell IDs across shardings.
- **Observer drift:** E1 output must be identical to E0 and E2/E3 must change only biological `eta`; availability/depth/counting configuration digests must remain unchanged.
- **Accidental measurement shortcut:** source/operator/donor must not influence class assignment or class loading generation, and a direct test must inspect this dependency boundary.

---

### Task 1: Freeze the corrected class-composition authority

**Files:**
- Create: `scripts/v77/build_v77_class_composition_authority.py`
- Create: `tests/test_v77_class_propagation_v1.py`
- Create after execution: `results/v77/V77_CLASS_COMPOSITION_AUTHORITY_V1.json`

**Interfaces:**
- Consumes: corrected V77 real calibration output containing `cohort.cell_class_counts` and pathology-blind source metadata.
- Produces: `build_authority(calibration_path: Path) -> dict` and `allocate_classes(authority: dict, n_cells: int, seed: int, global_ids: np.ndarray) -> np.ndarray` returning stable integer class indices.

- [ ] **Step 1: Write failing authority-governance tests** in `tests/test_v77_class_propagation_v1.py` asserting:
  - pathology-like metadata keys are rejected;
  - ordered labels/counts are persisted;
  - counts sum to the calibration cohort total;
  - largest-remainder quotas sum exactly to requested `N`;
  - the same global IDs receive the same class indices under different shard partitions;
  - reordering input JSON mappings cannot change frozen class order once the authority artifact exists.

- [ ] **Step 2: Run the authority tests and verify RED**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'authority or quota or shard'`

  Expected: FAIL because the authority builder/allocation interfaces do not yet exist.

- [ ] **Step 3: Implement the minimal authority builder and allocator**

  In `scripts/v77/build_v77_class_composition_authority.py`, implement:
  - `build_authority(calibration_path: Path) -> dict`
  - `largest_remainder_quotas(counts: np.ndarray, n_cells: int) -> np.ndarray`
  - `allocate_classes(authority: dict, n_cells: int, seed: int, global_ids: np.ndarray) -> np.ndarray`

  The allocator must use only frozen class prevalence, global cell identity, seed, and a dedicated class-assignment stream; it must not accept donor/source/operator inputs.

- [ ] **Step 4: Run the authority tests and verify GREEN**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'authority or quota or shard'`

  Expected: PASS.

- [ ] **Step 5: Build and inspect the committed authority artifact**

  Run the builder against the corrected calibration record; verify the JSON records calibration SHA, ordered labels, exact counts/proportions, pathology-blind statement, schema/version, and no gene-program content.

- [ ] **Step 6: Commit Task 1**

  Commit message: `feat(v77): freeze class composition authority`

---

### Task 2: Add E1 class truth with exact E0 observable equivalence

**Files:**
- Create: `scripts/v77/build_v77_class_aware_truth.py`
- Modify: `tests/test_v77_class_propagation_v1.py`

**Interfaces:**
- Consumes: existing `scripts/v77/build_v77_extended_truth.py` primitives plus Task 1 `allocate_classes(...)`.
- Produces: successor hidden-truth builder with arm enum `E0|E1|E2|E3`, where E1 adds `broad_class_index` but does not alter biological rate contributions.

- [ ] **Step 1: Add RED tests for the current missing mechanism and E1 contract**

  Assert:
  - current V73/V77 truth shards contain no `broad_class_index`;
  - successor E1 shards contain `broad_class_index` and authority SHA;
  - assignments are shard-invariant;
  - E1 preserves all existing donor/source/operator assignments;
  - E4 requested through this successor fails closed.

- [ ] **Step 2: Run the E1 truth tests and verify RED**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'truth or e1 or e4'`

  Expected: FAIL because the successor truth builder does not yet exist.

- [ ] **Step 3: Implement `build_v77_class_aware_truth.py` as a successor, not an in-place rewrite**

  Reuse existing World-A/V77 truth primitives and streams. Add dedicated disjoint stream constants for class assignment, class program, and within-class state. Write manifest fields for arm, authority SHA, stream registry, generator source identity, and explicit `class_assignment_inputs=[global_cell_index, seed, class_authority]`.

- [ ] **Step 4: Add E1 observable-equivalence integration test**

  Build E0 and E1 with identical seeds/settings and run the existing frozen observer path without any class contribution. Assert observable count arrays/digests are identical, while hidden truth differs only by class metadata/manifest additions.

- [ ] **Step 5: Run E1 tests and verify GREEN**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'truth or e1 or e4'`

  Expected: PASS.

- [ ] **Step 6: Commit Task 2**

  Commit message: `feat(v77): add isolated broad-class truth`

---

### Task 3: Add E2 class-shared random-content biological programs

**Files:**
- Create: `scripts/v77/build_v77_class_aware_rna_observer.py`
- Modify: `tests/test_v77_class_propagation_v1.py`

**Interfaces:**
- Consumes: class-aware truth shards from Task 2 and existing `build_v77_extended_rna_observer.py` helper conventions.
- Produces: `class_program_contribution(z: dict, seed: int) -> np.ndarray` and successor observer execution where E2 adds only this contribution to pre-count `eta`.

- [ ] **Step 1: Write RED tests for E2 isolation**

  Assert:
  - E2 produces a non-zero class-dependent `eta` contribution;
  - class program content is reproducible from seed/class index and synthetic gene index only;
  - no real gene IDs, marker lists, regulatory edges, donor, source, or operator are accepted as inputs to class loading generation;
  - scale is exactly `SC['state'] == 0.55`;
  - observer availability/depth/counting configuration digests are unchanged from E1;
  - the same class/seed gives the same loading vector across shardings.

- [ ] **Step 2: Run E2 tests and verify RED**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'e2 or class_program or observer_freeze'`

  Expected: FAIL because no E2 class contribution exists.

- [ ] **Step 3: Implement the minimal E2 successor observer**

  Reuse the existing V77 `_dense` convention and pre-count additive `eta` structure. Generate one random dense loading vector per frozen broad class from disjoint synthetic streams at scale `0.55`; select the row by `broad_class_index`. Do not alter availability, depth scaling, count realization, dynamic-range parameters, or operator support logic.

- [ ] **Step 4: Run E2 tests and verify GREEN**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'e2 or class_program or observer_freeze'`

  Expected: PASS.

- [ ] **Step 5: Re-run E0/E1 equivalence tests as spillover protection**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'e0 or e1 or observer_freeze'`

  Expected: PASS with E0/E1 observable identity unchanged.

- [ ] **Step 6: Commit Task 3**

  Commit message: `feat(v77): add class-shared synthetic biology`

---

### Task 4: Add E3 within-class continuous biology without donor/operator keying

**Files:**
- Modify: `scripts/v77/build_v77_class_aware_truth.py`
- Modify: `scripts/v77/build_v77_class_aware_rna_observer.py`
- Modify: `tests/test_v77_class_propagation_v1.py`

**Interfaces:**
- Consumes: Task 2 class assignments and Task 3 successor observer.
- Produces: `z_within_class` with shape `(n_cells, 2)` and class-specific random loading matrices contributing at `0.55 / sqrt(2)` per dimension.

- [ ] **Step 1: Write RED tests for E3**

  Assert:
  - every class with at least two cells has non-zero within-class latent variance;
  - `z_within_class` for a global cell ID is unchanged by shard size;
  - changing donor/source/operator while holding global ID and seed fixed cannot change the E3 latent draw in a unit-level dependency test;
  - each of the two loading dimensions uses exactly `0.55 / sqrt(2)` nominal scale;
  - E3 leaves E2 class assignment and observer/counting configuration unchanged.

- [ ] **Step 2: Run E3 tests and verify RED**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'e3 or within_class'`

  Expected: FAIL because E3 is not implemented.

- [ ] **Step 3: Implement E3 truth and observer contributions**

  Add two per-cell standard-normal coordinates from disjoint streams and two class-specific random dense loading vectors. Keep state generation independent of donor/source/operator and add the contribution to `eta` only for E3.

- [ ] **Step 4: Run E3 tests and verify GREEN**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'e3 or within_class'`

  Expected: PASS.

- [ ] **Step 5: Commit Task 4**

  Commit message: `feat(v77): add within-class continuous biology`

---

### Task 5: Freeze replay/scoring, smoke support, and provenance for E0–E3

**Files:**
- Create: `scripts/v77/run_v77_class_propagation_tournament.py`
- Modify: `tests/test_v77_class_propagation_v1.py`
- Create: `.github/workflows/v77-synthetic-class-propagation.yml`
- Create after execution: `results/v77/V77_CLASS_PROPAGATION_TOURNAMENT_V1.json`
- Create after execution: `docs/agent/V77_CLASS_PROPAGATION_TOURNAMENT_AUDIT_20261008.md`

**Interfaces:**
- Consumes: E0–E3 successor builders, frozen evaluation universe, and existing `v77_matched_scoring.score_matched(...)`.
- Produces: one receipt containing arm definitions, source/config digests, authority SHA, seeds/streams, observer freeze hashes, 2K operator-support evidence, and the same corrected multi-statistic scoring panel for all arms.

- [ ] **Step 1: Write RED tournament/provenance tests**

  Assert the runner:
  - refuses dirty/untracked executor state unless explicitly marked development-only;
  - binds authority SHA, generator/observer source digests, arm, seed, stream registry, evaluation universe, and scoring rule;
  - exposes E0–E3 only and rejects E4;
  - calls `v77_matched_scoring.score_matched` rather than reimplementing T5/scoring;
  - reports all frozen panel fields: expression median |r|, expression fraction >0.3, top-10-PC variance, detection median |r|, detection fraction >0.3, degree, transitivity, largest community fraction, T5, abundance max/median, top-1% share, median detected genes/cell;
  - labels corrected real points descriptive and does not emit a binary S159 pass/fail;
  - verifies the 2K synthetic population retains 42/42 operators with minimum count >=1.

- [ ] **Step 2: Run tournament tests and verify RED**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py -k 'tournament or receipt or support_2k'`

  Expected: FAIL because the tournament runner/receipt does not yet exist.

- [ ] **Step 3: Implement the tournament runner and dedicated CI workflow**

  Use one frozen seed protocol and identical observer/counting configuration across E0–E3. The runner must record but not tune to the corrected reference points.

- [ ] **Step 4: Run the complete focused test file**

  Run: `pytest -q tests/test_v77_class_propagation_v1.py`

  Expected: all tests PASS.

- [ ] **Step 5: Run relevant historical spillover checks**

  Run the existing V77 historical spillover audit and any existing operator-support regression referenced by the current synthetic/S174 lane. Any unexpected change to E0, World-A frozen behavior, or 42-operator support blocks scientific execution.

- [ ] **Step 6: Execute E0–E2 first, record receipt, and self-audit before E3**

  Use the frozen corrected evaluation universe/scoring implementation. Do not change effect scales after reading results. Record whether E1 is observably identical to E0 and whether E2 moves T5/class geometry in the expected direction without gross panel deterioration.

- [ ] **Step 7: Execute E3 only after the E0–E2 self-audit confirms contract compliance**

  Run with the same seeds, observer/counting configuration, evaluation universe, and scoring functions. Do not retune E2/E3 parameters.

- [ ] **Step 8: Write the audit record**

  `docs/agent/V77_CLASS_PROPAGATION_TOURNAMENT_AUDIT_20261008.md` must distinguish mechanistic observations from qualification claims, state that S159 remains unresolved, and explicitly say whether E4 remains unauthorized.

- [ ] **Step 9: Run GitHub CI and record the exact workflow run / commit SHA**

  The dedicated workflow should run the focused class-propagation tests plus the selected historical spillover/operator-support checks. Do not call local pytest GitHub CI.

- [ ] **Step 10: Commit Task 5**

  Commit message: `test(v77): qualify class propagation synthetic arms`

---

## Final Verification Before Any Scientific Claim

- [ ] Compare the implementation branch against its base and verify no runtime/optimizer/EMA/checkpoint, target-discovery, corrected-real-cache, 353-ID, TEST/Morabito, or production-authority files changed.
- [ ] Verify E1 observable counts are identical to E0 under matched seeds/settings.
- [ ] Verify observer/counting configuration hashes are identical across E0–E3.
- [ ] Verify all 42 observation operators remain represented at 2K with minimum support >=1.
- [ ] Verify no E2/E3 program content derives from real gene identity/program membership.
- [ ] Verify the receipt uses existing matched scorers and contains the complete frozen panel.
- [ ] Verify there was no post-outcome parameter tuning.
- [ ] Verify E4 is still fail-closed.
- [ ] Record exact commit SHAs and GitHub workflow run IDs in the audit/handoff.
