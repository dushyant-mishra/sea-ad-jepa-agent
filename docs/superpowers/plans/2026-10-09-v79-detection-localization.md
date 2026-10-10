# V79 Detection-Geometry Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a TRAIN-only, non-promoting localization analysis that determines whether corrected real signed-detection geometry is primarily explained by broad-class mixture, measurement depth, source/operator structure, donor structure, or residual within-state biology before any V79 synthetic mechanism is selected.

**Architecture:** Add a pure analysis module under `scripts/v79/` that reuses the frozen V77/V78 gene-selection and signed-metric semantics without modifying them. Add a fail-closed execution driver that authenticates the repaired S174 substrate and V78 authorities, constructs deterministic L0→L5 localization views, and writes descriptive JSON receipts whose ruling can select only a future mechanism family—not a synthetic arm, checkpoint, or training action.

**Tech Stack:** Python 3, NumPy, SciPy sparse/statistics, existing V77/V78 Python analysis modules, pytest, JSON receipts.

**Spec:** `docs/superpowers/specs/2026-10-09-v79-detection-localization-design.md`

## Global Constraints

- Base lineage is exactly `impl/v78-signed-detection-marginals-20261009` @ `e959d9a732698ae9a41e8cb1f6c10052d7390326`.
- TRAIN only; pathology-blind; no TEST/Morabito; no target-discovery inputs; no E4; no Stage4/500K; no production target/representation freeze.
- No JEPA training or checkpoint generation.
- V78 generation, scoring semantics, tournament outputs, and ruling remain frozen; no post-outcome V78 retuning.
- Canonical gene selection remains the corrected frozen evaluation universe followed by the exact existing 3,000-gene CPM-log1p-expression-variance selection, then binary detection correlation on the same selected genes.
- Canonical strong-edge threshold remains `0.30`; sensitivity thresholds are exactly `(0.10, 0.20, 0.30, 0.40)` and are descriptive only.
- Corrected substrate/authority authentication is fail-closed and reuses the V78 custody chain; operator identity comes only from the authenticated shard→operator bridge, never `source_library`.
- All outputs are descriptive/non-promoting. Every ruling must contain `training_authorized: false`, `v78_retuning_authorized: false`, and `synthetic_arm_promoted: null`.
- Macha Bayesian outputs are not consumed by this implementation; later comparison requires separate custody/leakage/identity-scrubbing audit.
- Minimum supported stratum size is prospectively fixed at `100` cells. A supported correlation view also requires at least `50` selected genes with variable binary detection.
- Depth localization starts from five within-class quantile bins and deterministically coarsens adjacent quantile bins by trying `5 → 4 → 3 → 2` bins until every realized bin has at least `100` cells; if no two-bin partition satisfies support, that class is omitted from L2+ with an explicit reason.
- Conditional correlation matrices are combined with cell-count-weighted Fisher-z averaging of off-diagonal correlations, clipping each `r` to `[-0.999999, 0.999999]` before `atanh`; diagonal is reset to `1.0` after `tanh`.
- L5 never emits gene IDs, pair IDs, or edge identities. It may emit only aggregate persistence counts/fractions and topology summaries.

## Review Focus

1. **Constant-detection genes:** supported views must count them, keep canonical selected-gene identity fixed, and never fail or silently reselect genes; tests live in Task 1.
2. **Sparse/unsupported nested strata:** class/depth/operator/donor views below `100` cells or `50` variable genes must be omitted with a reason, never silently pooled; tests live in Tasks 2 and 3.
3. **Zero negative strong edges:** positive/negative ratio must be `null` rather than infinity or division-by-zero; tests live in Task 1.
4. **Operator/source provenance mismatch:** execution must fail closed if operator identity cannot be resolved through the authenticated bridge or disagrees with source custody; tests live in Task 3.
5. **Receipt authority leakage:** every output must remain non-training/non-promoting and the L5 receipt must contain no gene/pair identities; tests live in Task 4.

---

### Task 1: Pure signed-detection correlation and aggregation helpers

**Files:**
- Create: `scripts/v79/v79_detection_localization.py`
- Test: `tests/test_v79_detection_localization_v1.py`

**Interfaces:**
- Consumes: frozen selection/scoring helpers from `scripts/v77/v77_matched_scoring.py` and `scripts/v77/v78_signed_scoring.py`.
- Produces:
  - `canonical_selection(counts: np.ndarray, universe: np.ndarray, n_hvg: int = 3000) -> dict`
  - `detection_corr(counts: np.ndarray, universe: np.ndarray, selected_positions: np.ndarray) -> dict`
  - `summarize_corr(C: np.ndarray, thresholds: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4)) -> dict`
  - `combine_corr_fisher_z(corrs: list[np.ndarray], n_cells: list[int]) -> np.ndarray`
  - constants `MIN_STRATUM_CELLS = 100`, `MIN_VARIABLE_GENES = 50`, `CANONICAL_THRESHOLD = 0.30`, `SENSITIVITY_THRESHOLDS = (0.10, 0.20, 0.30, 0.40)`.

- [ ] **Step 1: Write failing tests for canonical selection/reproduction and constant-gene handling**

Add tests asserting that `canonical_selection` returns the same selected 3K positions as the frozen V77 `hvg_correlation` path on a deterministic fixture, and that `detection_corr` reports constant selected genes without changing the selected set. Add a zero-negative-edge fixture asserting the canonical ratio is `None`/JSON `null`.

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `pytest -q tests/test_v79_detection_localization_v1.py -k 'selection or constant or zero_negative'`

Expected: FAIL because `scripts/v79/v79_detection_localization.py` does not yet exist.

- [ ] **Step 3: Implement the minimal selection/correlation helpers**

`canonical_selection` must delegate gene selection to the exact frozen V77/V78 CPM-log1p path and return selected positions plus the canonical selection metadata; it must not introduce a new HVG rule. `detection_corr` must binarize counts on the frozen universe, compute correlation only on the frozen selected positions, count variable/constant genes, and preserve matrix shape even for constant genes.

- [ ] **Step 4: Implement `summarize_corr` by delegating the canonical `0.30` signed topology to frozen V78 definitions**

Return the canonical V78 signed diagnostics plus unsigned median absolute correlation, unsigned strong-edge fraction, mean degree, transitivity, full off-diagonal signed quantiles/histogram summary, and threshold-sweep summaries for exactly `0.10/0.20/0.30/0.40`. Do not redefine the legacy `0.30` metric.

- [ ] **Step 5: Write and pass tests for Fisher-z combination**

Test exact behavior for one matrix, identical matrices, unequal cell weights, clipping near ±1, symmetry, and diagonal reset to `1.0`.

Run: `pytest -q tests/test_v79_detection_localization_v1.py -k 'fisher or summarize or selection or constant or zero_negative'`

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add scripts/v79/v79_detection_localization.py tests/test_v79_detection_localization_v1.py
git commit -m "feat: add V79 detection localization metrics"
```

### Task 2: Deterministic class and depth localization (L0–L2)

**Files:**
- Modify: `scripts/v79/v79_detection_localization.py`
- Modify: `tests/test_v79_detection_localization_v1.py`

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces:
  - `support_status(n_cells: int, n_variable_genes: int) -> dict`
  - `quantile_depth_bins(values: np.ndarray, min_cells: int = 100) -> dict`
  - `localize_by_labels(det_matrix: np.ndarray, labels: np.ndarray, selected_positions: np.ndarray, min_cells: int = 100) -> dict`
  - `build_l0_l2(counts: np.ndarray, universe: np.ndarray, broad_class: np.ndarray) -> dict`.

- [ ] **Step 1: Write failing tests for support and deterministic depth coarsening**

Pin the exact `5→4→3→2` rule: fixtures where five bins pass, where five fails but four passes, where only two pass, and where even two fail. Assert unsupported cases return explicit reasons and do not fabricate a result.

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `pytest -q tests/test_v79_detection_localization_v1.py -k 'depth_bins or support_status'`

Expected: FAIL because the functions are absent.

- [ ] **Step 3: Implement support checks and quantile-bin construction**

Use stable rank/quantile assignment with deterministic tie handling. Each candidate bin count is evaluated from 5 down to 2; accept the first partition where every realized bin has at least `100` cells. Never choose bin count using topology outcomes.

- [ ] **Step 4: Write failing tests for L0 exact reproduction and L1 class localization**

Assert L0 uses the same selected genes and canonical signed object as the frozen V78 real-scoring path on the fixture. For L1, assert every supported class is scored separately, unsupported classes are retained only as omitted records, and the combined class-conditional matrix equals cell-count-weighted Fisher-z combination of the supported class matrices.

- [ ] **Step 5: Implement L0/L1**

L0 is canonical pooled reproduction. L1 scores binary detection separately inside each supported broad class using the same fixed selected positions, retains every class result, and builds a single combined conditional matrix through Task 1 Fisher-z aggregation.

- [ ] **Step 6: Write failing tests for L2 detected-depth primary and library-depth sensitivity paths**

Assert detected-feature depth is primary, library size is sensitivity-only, bins are defined within class, and both paths preserve the canonical selected-gene identity.

- [ ] **Step 7: Implement L2**

Within each supported class, create deterministic depth bins from detected-feature count; compute each supported class×depth correlation matrix; combine supported matrices with Fisher-z weighting. Repeat with library-size bins under a separately labeled sensitivity result. Do not classify depth as purely technical.

- [ ] **Step 8: Run Task 2 tests**

Run: `pytest -q tests/test_v79_detection_localization_v1.py -k 'l0 or l1 or l2 or depth_bins or support_status'`

Expected: PASS.

- [ ] **Step 9: Commit Task 2**

```bash
git add scripts/v79/v79_detection_localization.py tests/test_v79_detection_localization_v1.py
git commit -m "feat: add V79 class and depth localization"
```

### Task 3: Source/operator and donor localization (L3–L5)

**Files:**
- Modify: `scripts/v79/v79_detection_localization.py`
- Modify: `tests/test_v79_detection_localization_v1.py`

**Interfaces:**
- Consumes: Task 2 class/depth strata and authenticated per-cell source/operator/donor labels supplied by the execution driver.
- Produces:
  - `localize_operator_source(det_matrix: np.ndarray, base_strata: np.ndarray, operator_labels: np.ndarray, source_labels: np.ndarray) -> dict`
  - `localize_donor(det_matrix: np.ndarray, base_strata: np.ndarray, donor_labels: np.ndarray) -> dict`
  - `aggregate_residual_persistence(level_views: dict[str, dict]) -> dict`.

- [ ] **Step 1: Write failing tests for operator→source fallback**

Assert an operator with `>=100` cells receives its own result; an operator with `<100` cells may contribute only through its authenticated source if that source has `>=100` cells in the same upstream class+depth stratum; otherwise it is omitted. Assert no pseudo-operator pooling.

- [ ] **Step 2: Implement L3 operator/source localization**

Within each supported L2 primary class+detected-depth stratum, score supported operators. Apply only the fixed source fallback above. Retain operator and source results separately and build the L3 combined matrix from supported realized strata.

- [ ] **Step 3: Write failing tests for donor localization**

Assert donors are evaluated only inside preceding supported strata, donor groups below `100` cells are omitted explicitly, and no donor-associated result is labeled technical/nuisance by the code.

- [ ] **Step 4: Implement L4 donor localization**

Score supported donor groups within the preceding measurement-controlled strata; retain donor-level results and the Fisher-z combined matrix. Metadata must label donor interpretation as `BIOLOGICAL_OR_AMBIGUOUS`, never automatically `TECHNICAL`.

- [ ] **Step 5: Write failing tests for L5 identity-scrubbed persistence**

Construct deterministic synthetic level matrices with known persistent positive/negative edges. Assert L5 reports only aggregate counts/fractions of edges whose sign and threshold status persist across supported L1–L4 combined views, plus topology summaries; assert the serialized L5 object contains no selected gene positions, registry IDs, gene names, or edge pairs.

- [ ] **Step 6: Implement L5 aggregate persistence**

For each threshold `(0.10, 0.20, 0.30, 0.40)`, compute aggregate fractions/counts of off-diagonal pairs that remain positive-above-threshold, negative-below-threshold, sign-consistent but subthreshold, or sign-unstable across available supported conditional level matrices. Canonical interpretation uses `0.30`; other thresholds are sensitivity-only. Do not export pair identities.

- [ ] **Step 7: Run Task 3 tests**

Run: `pytest -q tests/test_v79_detection_localization_v1.py -k 'operator or source or donor or residual or l3 or l4 or l5'`

Expected: PASS.

- [ ] **Step 8: Commit Task 3**

```bash
git add scripts/v79/v79_detection_localization.py tests/test_v79_detection_localization_v1.py
git commit -m "feat: add V79 operator donor residual localization"
```

### Task 4: Fail-closed execution driver and canonical receipts

**Files:**
- Create: `scripts/v79/run_v79_detection_localization.py`
- Modify: `tests/test_v79_detection_localization_v1.py`
- Create at execution time: `results/v79_localization/V79_DETECTION_LOCALIZATION_PREEXECUTION_GATE_V1.json`
- Create at execution time: `results/v79_localization/V79_DETECTION_LOCALIZATION_CANONICAL_V1.json`
- Create at execution time: `results/v79_localization/V79_DETECTION_LOCALIZATION_SENSITIVITY_V1.json`
- Create at execution time: `results/v79_localization/V79_DETECTION_LOCALIZATION_RULING_V1.json`

**Interfaces:**
- Consumes: repaired S174 counts/meta, corrected evaluation universe/class authority, authenticated shard→operator bridge, V78 custody/authentication utilities, Tasks 1–3 analysis helpers.
- Produces:
  - `preexecution_gate(...) -> dict`
  - `run_localization(...) -> dict`
  - `mechanism_ruling(localization: dict) -> dict`
  - CLI that refuses execution unless the gate is `READY`.

- [ ] **Step 1: Write failing gate tests**

Cover: valid repaired-substrate fixture, wrong corrected-calibration digest, missing count/meta shard pair, wrong/missing operator bridge, evaluation-universe mismatch, class-authority mismatch, and any training-authorized contamination. Every invalid case must return `BLOCKED` with an explicit blocker and must prevent scientific execution.

- [ ] **Step 2: Run gate tests and confirm RED**

Run: `pytest -q tests/test_v79_detection_localization_v1.py -k 'gate or custody or bridge'`

Expected: FAIL because the driver does not exist.

- [ ] **Step 3: Implement `preexecution_gate` by reusing V78 authentication logic**

Authenticate the exact repaired S174 42 count + 42 meta lineage, corrected evaluation-universe hash, class-authority hash, repaired marginal authority/custody where needed for source/depth metadata, and operator bridge. Do not create a second competing custody definition.

- [ ] **Step 4: Write failing receipt/ruling tests**

Pin schemas, required level metadata, support reporting, canonical-versus-sensitivity separation, and mandatory non-authorization fields. Assert the ruling contains only mechanism-family recommendations from the spec hierarchy and can never name/promote a synthetic arm.

- [ ] **Step 5: Implement `run_localization` and receipt writing**

Load corrected TRAIN cells from authenticated repaired shards, resolve broad class/source/operator/donor labels from authenticated authorities, compute the frozen canonical 3K selection once, execute L0–L5, and atomically write the four required JSON artifacts. The sensitivity receipt contains library-depth and multi-threshold diagnostics; the canonical receipt retains only canonical selection and `0.30` interpretation plus all per-level support records.

- [ ] **Step 6: Implement `mechanism_ruling` as a descriptive decision map, not a pass/fail gate**

The function must report the observed attenuation/persistence pattern and map it to one or more of: `RICHER_BIOLOGICAL_MIXTURE`, `COUPLED_DEPTH_CAPTURE_OBSERVER`, `PHYSICALLY_INTERPRETABLE_OBSERVATION_OPERATOR`, `PRESERVE_DONOR_LINKED_BIOLOGY`, `RICHER_WITHIN_STATE_BIOLOGY`, or `FACTORIAL_BIOLOGY_X_OBSERVATION_TOURNAMENT`. Because no Bayesian uncertainty authority is yet available, the function must not invent significance thresholds or claim a unique causal winner when attenuation is mixed/ambiguous.

- [ ] **Step 7: Run the full unit suite**

Run: `pytest -q tests/test_v79_detection_localization_v1.py`

Expected: PASS.

- [ ] **Step 8: Run inherited V78/V77 regression tests**

Run at minimum:

```bash
pytest -q \
  tests/test_v78_signed_scoring_v1.py \
  tests/test_v78_preexecution_gate_v1.py \
  tests/test_v78_frozen_execution_driver_v1.py \
  tests/test_v77_class_propagation_tournament_v1.py
```

Expected: PASS with no frozen-score or authority drift.

- [ ] **Step 9: Commit Task 4**

```bash
git add scripts/v79/run_v79_detection_localization.py tests/test_v79_detection_localization_v1.py
git commit -m "feat: add V79 localization execution gate"
```

### Task 5: Execute on corrected TRAIN custody and freeze the localization result

**Files:**
- Create/update only from the authenticated execution: `results/v79_localization/*.json`
- Modify if needed after exact-head verification: PR body/documentation only; no post-outcome mechanism retuning.

**Interfaces:**
- Consumes: Task 4 READY gate and actual repaired S174 TRAIN bytes.
- Produces: exact-head canonical/sensitivity/ruling receipts suitable to inform a later prospective V79 mechanism-design spec.

- [ ] **Step 1: Run the preexecution gate against the actual repaired S174 substrate**

Expected: `READY`, zero blockers, 42 authenticated count shards, 42 authenticated meta shards, authenticated operator bridge, exact evaluation universe/class authority.

- [ ] **Step 2: Execute localization exactly once under the frozen plan**

Run the driver without changing support thresholds, depth binning, selected genes, thresholds, fallback rules, or interpretation hierarchy after seeing any L0–L5 outcome.

- [ ] **Step 3: Verify required receipts and non-authorization fields**

Check all four JSON artifacts exist, are internally hash/custody bound, contain explicit support/omission records, and state:

```json
{
  "training_authorized": false,
  "v78_retuning_authorized": false,
  "synthetic_arm_promoted": null
}
```

- [ ] **Step 4: Run exact-head CI/regression verification**

Require the new V79-localization test workflow (or repository-equivalent pytest CI) plus inherited V78/V77 tests to pass on the exact implementation head before interpreting the localization result.

- [ ] **Step 5: Freeze the scientific interpretation**

Record which causal layer(s) the localization map supports according to the preregistered hierarchy. Do not implement the resulting V79 synthetic mechanism in the same outcome-reading commit; mechanism design begins in a new prospective design phase.

- [ ] **Step 6: Commit result receipts without changing analysis code**

```bash
git add results/v79_localization
git commit -m "results: freeze V79 detection localization"
```

## Self-Review

- **Spec coverage:** L0–L5, canonical/sensitivity separation, corrected-S174 custody, fixed gene selection, threshold sweep, support reporting, donor ambiguity, operator fallback, L5 identity scrubbing, four required receipts, and all hard non-authorization boundaries are assigned to Tasks 1–5.
- **Step scan:** implementation choices that would otherwise be discretionary are pinned: `100`-cell minimum, `50` variable-gene minimum, deterministic `5→4→3→2` depth coarsening, Fisher-z conditional combination, canonical `0.30` threshold, and identity-free L5 persistence categories.
- **Type consistency:** Tasks 2–4 consume only interfaces defined in earlier tasks; the execution driver passes per-cell labels into pure analysis helpers rather than teaching analysis code how to discover custody metadata.
- **Review focus:** all five listed failure classes have explicit tests in the owning task.
- **Proportion:** the plan keeps algorithm bodies out of the document except where the preregistration itself requires exact behavior; implementation remains concentrated in two new Python files and one focused test file.
