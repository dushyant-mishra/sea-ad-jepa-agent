# Unified Synthetic Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the missing adapter-first integration layer that composes existing Stage81A3, V79, and PR #311 synthetic mechanics into one candidate-agnostic population with a reader-compatible fit view and physically separate controller truth.

**Architecture:** Reuse existing qualified mechanics rather than rewriting them. A unified compositor produces latent biology and expected molecular state; existing V79/PR311 observation mechanics create measured views; a fit-side adapter emits modern support/address/provenance semantics; a separate controller module derives candidate-specific truth only after world generation. The final mechanics slice stops at downstream preflight compatibility and does not fit models or run TD gates.

**Tech Stack:** Python 3, NumPy, pandas, SciPy sparse matrices, pytest, existing `scripts/v79` modules, existing `scripts/v5` post-TD harness.

**Spec:** `docs/superpowers/specs/2026-10-13-unified-synthetic-integration-design.md`

## Global Constraints

- Base is PR #315 head `af03ef67d52651463944a6de3a08e101ad00e0ea`; PR #311 is already in its ancestry.
- Bind Stage81A3 commit `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`, V79 PR #253 commit `1a0ab6e1108af924ca13e81caa3c70f3101d251c`, PR #311 commit `2b6d3439105e087acdab53a318c57bbb468eae26`, and PR #315 commit `af03ef67d52651463944a6de3a08e101ad00e0ea`.
- Q00-Q11 are immutable and are never regenerated or rewritten.
- Candidate identifiers C1/C2/C3/C6/C4/C5 must not influence latent-world generation.
- Source/operator may alter acquisition/observation but must not directly alter latent biological truth.
- Measured zero and structurally unmeasured are distinct states.
- Controller-only truth must never be serialized into the fit-side package.
- Same-nucleus and separate-nucleus multimodal semantics must remain distinct.
- Donor-first split semantics are mandatory.
- The unresolved 50K `sample_row` issue cannot become hard STAT1 calibration authority in this slice.
- `target_selection_authorized`, `representation_selection_authorized`, `td60_authorized`, `stage4_authorized`, `training_authorized`, `real_data_authorized`, and `synthetic_training_authorized` remain false.
- No model fitting, biological scoring, TD phase 2, pathology opening, Stage4, TD60, or training occurs in this plan.

## Review Focus

- **Source identity drift:** a mismatched bound commit/hash must fail closed rather than silently continuing. Covered in Task 1 tests.
- **Candidate leakage into generation:** generator configuration/state containing C1/C2/C3/C4/C5/C6 semantics must be rejected. Covered in Task 1 tests.
- **Support collapse:** observed zero must remain distinguishable from structural unmeasurement. Covered in Task 2 tests.
- **Controller leakage:** fit-side serialization must exclude latent/controller fields even when the controller object exists in memory. Covered in Task 3 tests.
- **Downstream false authority:** synthetic-package compatibility smoke must leave every existing post-TD authority flag false. Covered in Task 4 tests.

---

### Task 1: Integration manifest and unified biological compositor

**Files:**
- Create: `scripts/v79/unified_synthetic_integration_v1.py`
- Create: `results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_MANIFEST_V1.json`
- Test: `tests/v79/test_unified_synthetic_integration_v1.py`

**Interfaces:**
- Consumes: existing `generate_latent_biology(...)` / `LatentBiology` semantics from V79; PR #311 rare-regime constants/mechanics as bounded reusable inputs; Stage81A3 expected-state/intervention semantics by explicit lineage binding rather than file mutation.
- Produces:
  - `IntegrationAuthority` dataclass
  - `UnifiedBiologyConfig` dataclass
  - `UnifiedBiologyWorld` dataclass
  - `validate_integration_manifest(manifest: Mapping[str, object]) -> IntegrationAuthority`
  - `build_unified_biology(config: UnifiedBiologyConfig, *, seed: int) -> UnifiedBiologyWorld`
  - `hash_unified_world(world: UnifiedBiologyWorld) -> str`

- [ ] **Step 1: Write failing manifest tests**
  - exact source commit identities above are accepted;
  - any source commit drift raises `ValueError`;
  - any generator/config key containing candidate identifiers `C1`, `C2`, `C3`, `C4`, `C5`, or `C6` raises `ValueError`;
  - all authority flags are false.

- [ ] **Step 2: Run manifest tests and verify failure**

Run: `pytest tests/v79/test_unified_synthetic_integration_v1.py -k "manifest or candidate" -v`
Expected: FAIL because integration module does not yet exist.

- [ ] **Step 3: Implement manifest validation and immutable authority dataclass**

`validate_integration_manifest(...)` must compare exact bound identities, reject unknown authority escalation, and preserve the 50K calibration caveat as a non-authorizing manifest field.

- [ ] **Step 4: Write failing compositor tests**
  - one returned population contains both ordinary/common and rare-activity cells;
  - rare eligibility is restricted to configured lineage/state subsets;
  - donor recurrence is explicit;
  - expected molecular state is produced before observation;
  - no candidate label fields occur anywhere in `UnifiedBiologyWorld`.

- [ ] **Step 5: Run compositor tests and verify failure**

Run: `pytest tests/v79/test_unified_synthetic_integration_v1.py -k "population or rare or expected" -v`
Expected: FAIL because compositor is not implemented.

- [ ] **Step 6: Implement `build_unified_biology(...)` minimally**

Compose broad-class/substate/donor/continuous V79 biology with one-population common→rare activity and bounded context/perturbation annotations. Reuse existing PR #311 mechanics where interfaces fit; do not import old challenge-package labels into the latent world.

- [ ] **Step 7: Run Task 1 tests**

Run: `pytest tests/v79/test_unified_synthetic_integration_v1.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/v79/unified_synthetic_integration_v1.py results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_MANIFEST_V1.json tests/v79/test_unified_synthetic_integration_v1.py
git commit -m "feat(v79): compose unified synthetic biology"
```

### Task 2: Observation composition and reader-compatible fit view

**Files:**
- Create: `scripts/v79/unified_synthetic_fit_view_v1.py`
- Test: `tests/v79/test_unified_synthetic_fit_view_v1.py`

**Interfaces:**
- Consumes: `UnifiedBiologyWorld` from Task 1; existing `observe_latent_biology(...)` semantics from `scripts/v79/v79_observation_operator.py`; PR #311 same/separate-nucleus and technical-pseudo-rarity mechanics.
- Produces:
  - `UnifiedObservationConfig` dataclass
  - `UnifiedFitView` dataclass
  - `observe_unified_world(world: UnifiedBiologyWorld, config: UnifiedObservationConfig, *, seed: int) -> UnifiedFitView`
  - `serialize_fit_view(view: UnifiedFitView) -> dict[str, object]`
  - `fit_view_sha256(view: UnifiedFitView) -> str`

- [ ] **Step 1: Write failing observation tests**
  - two different observation seeds over the same world preserve the same latent-world hash but produce different measured-count hashes;
  - changing source/operator configuration changes observations without changing latent-world hash;
  - technical pseudo-rarity is possible only observation-side when the matching rare biological activity is absent.

- [ ] **Step 2: Run observation tests and verify failure**

Run: `pytest tests/v79/test_unified_synthetic_fit_view_v1.py -k "observation or source or pseudo" -v`
Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement observation composition**

Use V79 RNA observation as baseline. Add thin modality adapters: same-nucleus modalities retain shared entity identity; separate-nucleus modalities expose donor/state relation without a fake paired-cell identity.

- [ ] **Step 4: Write failing reader/support tests**
  - measured zero serializes as measured support with value zero;
  - structural unmeasurement serializes as support=false and cannot be converted to measured zero;
  - output includes canonical address index, donor, source/operator, cell/entity provenance, and lawful observation descriptors;
  - donor split labels are donor-disjoint.

- [ ] **Step 5: Run reader/support tests and verify failure**

Run: `pytest tests/v79/test_unified_synthetic_fit_view_v1.py -k "support or provenance or split" -v`
Expected: FAIL until fit-view serialization is complete.

- [ ] **Step 6: Implement fit-view serialization**

Keep the interface production-shaped and address-index based. Do not expose controller truth, rare labels, expected molecular state, recoverability class, or candidate mapping.

- [ ] **Step 7: Run Task 2 tests**

Run: `pytest tests/v79/test_unified_synthetic_fit_view_v1.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/v79/unified_synthetic_fit_view_v1.py tests/v79/test_unified_synthetic_fit_view_v1.py
git commit -m "feat(v79): add unified synthetic fit view"
```

### Task 3: Controller-only truth derivation and firewall

**Files:**
- Create: `scripts/v79/unified_synthetic_controller_truth_v1.py`
- Test: `tests/v79/test_unified_synthetic_controller_truth_v1.py`

**Interfaces:**
- Consumes: `UnifiedBiologyWorld` from Task 1 only; it must not consume fit-side serialized outputs as truth authority.
- Produces:
  - `UnifiedControllerTruth` dataclass
  - `derive_controller_truth(world: UnifiedBiologyWorld) -> UnifiedControllerTruth`
  - `controller_truth_sha256(truth: UnifiedControllerTruth) -> str`
  - `assert_fit_view_is_controller_free(payload: Mapping[str, object]) -> None`

- [ ] **Step 1: Write failing derivation tests**
  - deterministic world produces deterministic controller truth/hash;
  - shared, relational, query, regulatory, interaction, context/perturbation and recoverability truth are derived from the same completed world;
  - candidate mappings are absent from Task 1 world but may exist in this controller-only object.

- [ ] **Step 2: Run derivation tests and verify failure**

Run: `pytest tests/v79/test_unified_synthetic_controller_truth_v1.py -k "derive or deterministic" -v`
Expected: FAIL because controller module does not exist.

- [ ] **Step 3: Implement controller truth derivation**

Derive truth after generation. Do not feed any controller object back into generation or observation functions.

- [ ] **Step 4: Write failing firewall tests**
  - serialized fit view contains no latent abundance, expected state, rare labels, pseudo-rare labels, candidate mapping, recoverability class, counterfactual truth, or controller hashes;
  - `assert_fit_view_is_controller_free(...)` rejects injected controller fields;
  - controller module is not imported by `unified_synthetic_fit_view_v1.py`.

- [ ] **Step 5: Run firewall tests and verify failure**

Run: `pytest tests/v79/test_unified_synthetic_controller_truth_v1.py -k "firewall or leak" -v`
Expected: FAIL until firewall is implemented.

- [ ] **Step 6: Implement firewall and controller hashing**

Use explicit field-deny rules plus import-surface test. Preserve fit-side/controller hashes separately.

- [ ] **Step 7: Run Task 3 tests**

Run: `pytest tests/v79/test_unified_synthetic_controller_truth_v1.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/v79/unified_synthetic_controller_truth_v1.py tests/v79/test_unified_synthetic_controller_truth_v1.py
git commit -m "feat(v79): add controller-only unified truth"
```

### Task 4: Integration receipt and downstream preflight compatibility smoke

**Files:**
- Create: `scripts/v79/finalize_unified_synthetic_integration_v1.py`
- Create: `tests/v79/test_finalize_unified_synthetic_integration_v1.py`
- Create at execution time: `results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V1.json`

**Interfaces:**
- Consumes: world/hash from Task 1, fit-view/hash from Task 2, controller/hash from Task 3, exact source identities, and the existing downstream callable `build_synthetic_rehearsal_preflight(...)` from `scripts/v5/jepa_post_td_harness_contract_v1.py`.
- Produces:
  - `build_integration_receipt(...) -> dict[str, object]`
  - `write_integration_receipt_once(path: Path, receipt: Mapping[str, object]) -> None`
  - a deterministic synthetic package SHA-256 over fit-side package identity only.

- [ ] **Step 1: Write failing receipt tests**
  - receipt binds exact source commits, manifest hash, generator/adapter hashes, world hash, fit-view hash and separately stored controller hash;
  - fit package hash does not include controller bytes;
  - receipt is write-once;
  - every authority flag remains false.

- [ ] **Step 2: Run receipt tests and verify failure**

Run: `pytest tests/v79/test_finalize_unified_synthetic_integration_v1.py -k "receipt or authority" -v`
Expected: FAIL because finalizer does not exist.

- [ ] **Step 3: Implement integration receipt/finalizer**

Fail closed on identity mismatch, symlinked outputs, pre-existing receipt, or any true authority flag.

- [ ] **Step 4: Write downstream compatibility smoke**
  - construct a test-only non-authorizing portfolio/architecture fixture using existing post-TD contract helpers;
  - call existing `build_synthetic_rehearsal_preflight(...)` with the fit-side synthetic package SHA-256;
  - assert status `READY_FOR_SYNTHETIC_REHEARSAL_ONLY`;
  - assert `real_data_authorized == False`, `synthetic_training_authorized == False`, and all target/representation/TD60/Stage4/training flags remain false;
  - do not run TD gates, training, scoring or controller adjudication.

- [ ] **Step 5: Run downstream smoke and verify failure if interface is incompatible**

Run: `pytest tests/v79/test_finalize_unified_synthetic_integration_v1.py -k "downstream or preflight" -v`
Expected before adapter completion: FAIL at the specific incompatible interface; after implementation: PASS.

- [ ] **Step 6: Add only the minimum thin compatibility adapter needed for the existing preflight**

Do not copy or modify downstream TD/post-TD decision logic. If the downstream API itself is insufficient, stop and record the incompatibility rather than inventing a synthetic-specific substitute.

- [ ] **Step 7: Run focused and regression tests**

Run:
```bash
pytest tests/v79/test_unified_synthetic_integration_v1.py tests/v79/test_unified_synthetic_fit_view_v1.py tests/v79/test_unified_synthetic_controller_truth_v1.py tests/v79/test_finalize_unified_synthetic_integration_v1.py -v
pytest tests/v79/test_v79_rare_biology_generator_v1.py tests/test_v79_hierarchical_biology_v1.py tests/test_v79_observation_operator_v1.py -v
```
Expected: all PASS; no historical qualified tests regress.

- [ ] **Step 8: Commit**

```bash
git add scripts/v79/finalize_unified_synthetic_integration_v1.py tests/v79/test_finalize_unified_synthetic_integration_v1.py results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V1.json
git commit -m "feat(v79): freeze unified synthetic integration receipt"
```

## Final verification

- [ ] Run all four new test modules together and preserve exact test count/result.
- [ ] Re-run the reused V79/PR311 mechanics tests named above.
- [ ] Verify no Q00-Q11 file changed relative to base.
- [ ] Verify no TD/post-TD science-code file changed relative to base.
- [ ] Verify the final fit-side package contains no controller fields/files.
- [ ] Verify exact source identities and authority flags in the frozen receipt.
- [ ] Stop after mechanics/preflight qualification. Do not fit models or run TD gates.
