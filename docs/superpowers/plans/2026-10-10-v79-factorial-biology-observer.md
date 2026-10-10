# V79 Factorial Biology × Observation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the prospective V79 factorial synthetic-world tournament that independently varies anonymous hierarchical biology and an explicit observation process, generates counterfactual observation/biology controls, and scores all worlds without authorizing JEPA training.

**Architecture:** Keep biology generation and observation generation in separate modules with explicit dataclasses/manifests so H1 cannot see source/operator identity and H2 cannot mutate latent biology. A world builder composes H0/H1/H2/H3 and C_OBS/C_BIO from frozen authorities/seeds, while a scorer reuses V77/V78 legacy metrics plus the V79 localization ladder. The execution driver writes immutable, non-authorizing receipts and applies fail-closed falsification rules.

**Tech Stack:** Python 3, NumPy, SciPy sparse matrices, JSON/NPZ receipts, existing V77/V78 scorer and observer helpers, pytest.

**Spec:** `docs/superpowers/specs/2026-10-10-v79-factorial-biology-observer-design.md`

## Global Constraints

- Base scientific lineage is PR #250 evidence on frozen V78 head `e959d9a732698ae9a41e8cb1f6c10052d7390326`.
- TRAIN-only, pathology-blind, non-promoting, `training_authorized: false` throughout this plan.
- No TEST/Morabito, target discovery, ATAC/SCENIC+/NIH-CARD target evidence, pathology, E4, Stage4, or 500K work.
- H1 may consume only identity-scrubbed biological-geometry summaries; H2 may consume only observation/support/capture summaries.
- Neither layer may consume the real 3K correlation matrix, signed edge list, real module memberships, real donor-by-gene effects, named pathways, or target evidence.
- Biology is generated before observation; source/operator identity cannot define latent biological state.
- `source_library` must never be treated as operator identity; use the authenticated shard→operator bridge/authority only.
- The tournament is H0/H1/H2/H3 plus mandatory C_OBS and C_BIO controls; no post-outcome retuning.
- Reuse frozen V77/V78 scoring semantics for continuity; do not modify V78 tournament code.
- Every scientific receipt must carry `training_authorized: false`, `v78_retuning_authorized: false`, `test_or_morabito_accessed: false`, `pathology_accessed: false`, and `target_discovery_modified: false`.

## Review Focus

1. **Information leakage across layers:** tests must prove H1 receives no source/operator fields and H2 cannot alter latent-truth arrays or anonymous biological assignments.
2. **Identity leakage:** tests must reject real gene-identity keyed biological loadings, real edge lists, named pathways, and donor-by-gene payloads in authority objects.
3. **Counterfactual integrity:** C_OBS pairs must share byte-identical latent truth while changing only observation parameters; C_BIO pairs must differ in latent truth while sharing one observation regime.
4. **Marginal-vs-joint shortcuts:** tests must reject observers that externally force detected-gene counts or directly inject a signed gene-pair field.
5. **Fail-closed authority:** any missing hash, moved frozen baseline, unauthorized flag, or post-outcome arm mutation must block execution before scientific outputs are written.

---

## File Structure

- Create `scripts/v79/v79_hierarchical_biology.py` — anonymous broad-class/substate/continuous/donor-like latent biology and biological authority validation.
- Create `scripts/v79/v79_observation_operator.py` — structural support, capture, anonymous gene propensity, and stochastic count realization.
- Create `scripts/v79/build_v79_factorial_worlds.py` — H0/H1/H2/H3 and C_OBS/C_BIO composition, seed freeze, manifests, and non-authorizing generation receipts.
- Create `scripts/v79/score_v79_factorial_worlds.py` — legacy V77/V78 metrics plus localization-aware synthetic scoring and factorial comparisons.
- Create `scripts/v79/run_v79_factorial_tournament.py` — fail-closed gate, authority loading, one-shot execution, falsification logic, terminal ruling.
- Create `tests/test_v79_hierarchical_biology_v1.py` — biology geometry, anonymity, deterministic replay, no observation leakage.
- Create `tests/test_v79_observation_operator_v1.py` — structural support/capture/count realization, no biology mutation, no forced-detection shortcut.
- Create `tests/test_v79_factorial_worlds_v1.py` — arm composition, counterfactual identity, manifest/seed invariants.
- Create `tests/test_v79_factorial_scoring_v1.py` — frozen scorer reuse, localization path, factorial mechanism-selection logic.
- Create `tests/test_v79_factorial_gate_v1.py` — custody, hard boundaries, immutable arm manifest, non-authorizing receipts.

### Task 1: Anonymous hierarchical biology

**Files:**
- Create: `scripts/v79/v79_hierarchical_biology.py`
- Create: `tests/test_v79_hierarchical_biology_v1.py`

**Interfaces:**
- Consumes: canonical vocabulary size, synthetic class frequencies, identity-scrubbed biology authority, frozen seeds, cell count, synthetic donor count.
- Produces: `BiologyAuthority`, `LatentBiology`, `validate_biology_authority(...)`, `generate_latent_biology(...)`.
- `LatentBiology` must expose only anonymous numeric truth: `broad_class`, `substate`, `donor`, `continuous_factors`, `latent_abundance`, `biological_total_scale`, and deterministic truth hashes.

- [ ] **Step 1: Write failing authority/firewall tests**

Add tests asserting:
- an authority containing `gene_ids`, `gene_names`, `edge_list`, `pathway`, `target`, or `donor_gene_effects` is rejected;
- an authority containing `source`, `operator`, or `source_library` fields is rejected by the H1 validator;
- distributional anonymous fields such as module-size distribution, substate prevalence, class frequencies, and donor-effect scale are accepted.

- [ ] **Step 2: Run authority tests and verify RED**

Run: `pytest tests/test_v79_hierarchical_biology_v1.py -k authority -v`
Expected: FAIL because `validate_biology_authority` does not exist.

- [ ] **Step 3: Implement authority dataclasses and validator**

In `v79_hierarchical_biology.py`, define:
- `BiologyAuthority` dataclass for identity-scrubbed distributions only;
- `LatentBiology` dataclass for generated truth;
- `validate_biology_authority(authority: Mapping[str, Any]) -> BiologyAuthority`.

Validation must be allowlist-based, not blacklist-only.

- [ ] **Step 4: Run authority tests and verify GREEN**

Run the Step 2 command; expected PASS.

- [ ] **Step 5: Write failing deterministic hierarchy tests**

Tests must assert that a fixed seed yields byte-identical class/substate/module assignment and latent abundance, different seeds differ, broad-class labels are generated before any observation data exists, and within-class substates produce coherent anonymous block shifts while continuous factors add lower-amplitude variation.

- [ ] **Step 6: Run hierarchy tests and verify RED**

Run: `pytest tests/test_v79_hierarchical_biology_v1.py -k "deterministic or substate or continuous or donor" -v`
Expected: FAIL because `generate_latent_biology` is not implemented.

- [ ] **Step 7: Implement `generate_latent_biology(...) -> LatentBiology`**

Signature must accept only biological authority/configuration and RNG seeds. It must not accept source/operator arguments. Generate broad class → anonymous substate → continuous program amplitudes → donor-like perturbations → nonnegative latent abundance. Module/address membership is random under frozen seeds and never keyed by real gene semantics.

- [ ] **Step 8: Run the Task 1 test file**

Run: `pytest tests/test_v79_hierarchical_biology_v1.py -v`
Expected: PASS.

- [ ] **Step 9: Commit**

Commit message: `feat: add anonymous V79 hierarchical biology`.

### Task 2: Explicit observation process

**Files:**
- Create: `scripts/v79/v79_observation_operator.py`
- Create: `tests/test_v79_observation_operator_v1.py`

**Interfaces:**
- Consumes: immutable `LatentBiology`, authenticated observation authority, observation regime labels, observation seed.
- Produces: `ObservationAuthority`, `ObservationResult`, `validate_observation_authority(...)`, `observe_latent_biology(...)`.
- `ObservationResult` contains sparse observed counts, structural support mask/summary, capture-efficiency draws, observed library totals, detected counts, regime labels, and hashes linking back to unchanged latent truth.

- [ ] **Step 1: Write failing observation-authority tests**

Assert accepted fields are restricted to structural support, anonymous capture/depth distributions, anonymous propensity distributions, realization-family parameters, and authenticated operator/source IDs. Assert rejection of biological module assignments, class-specific biological loadings, gene-pair signed fields, target/pathology fields, and any externally supplied detected-gene count target.

- [ ] **Step 2: Run authority tests and verify RED**

Run: `pytest tests/test_v79_observation_operator_v1.py -k authority -v`
Expected: FAIL because validator is missing.

- [ ] **Step 3: Implement `ObservationAuthority` and validator**

Define an allowlist schema with declared realization family. First implementation supports exactly the prospectively named families needed by the arm manifest: independent thinning/count realization and conditional finite-library multinomial realization; overdispersion is a separate named parameterized arm, not an implicit fallback.

- [ ] **Step 4: Run authority tests and verify GREEN**

Run the Step 2 command; expected PASS.

- [ ] **Step 5: Write failing observation invariance/generation tests**

Assert:
- calling `observe_latent_biology` never mutates any `LatentBiology` array/hash;
- identical latent truth with two observation regimes yields different observed counts when regimes differ;
- observed depth/detection emerge from the generative realization rather than a forced `k` detected genes;
- structural support zeros unsupported addresses;
- replay with the same observation seed is deterministic;
- gene-level propensities are anonymous and not keyed by biology identities.

- [ ] **Step 6: Run generation tests and verify RED**

Run: `pytest tests/test_v79_observation_operator_v1.py -k "observe or support or deterministic or mutate" -v`
Expected: FAIL because `observe_latent_biology` is missing.

- [ ] **Step 7: Implement `observe_latent_biology(...) -> ObservationResult`**

Keep biological total scale and technical capture efficiency distinct. Apply structural support, anonymous gene propensity, cell-level capture, then declared count realization. Observed library total and detected-gene count are outcomes. Do not reuse V78 top-k forced-detection allocation for H2/H3.

- [ ] **Step 8: Run the Task 2 test file**

Run: `pytest tests/test_v79_observation_operator_v1.py -v`
Expected: PASS.

- [ ] **Step 9: Commit**

Commit message: `feat: add V79 observation operator`.

### Task 3: Frozen factorial world builder and counterfactual controls

**Files:**
- Create: `scripts/v79/build_v79_factorial_worlds.py`
- Create: `tests/test_v79_factorial_worlds_v1.py`

**Interfaces:**
- Consumes: H0 baseline/E2 builder inputs, `BiologyAuthority`, `ObservationAuthority`, frozen arm manifest, seeds.
- Produces: `ArmManifest`, per-arm world NPZ/JSON receipts, `build_factorial_worlds(...)` with named H0/H1/H2/H3/C_OBS/C_BIO outputs.

- [ ] **Step 1: Write failing arm-manifest tests**

Pin exact required arm names `H0`, `H1`, `H2`, `H3`, `C_OBS`, `C_BIO`; fixed seeds; cell/donor counts; balancing/crossing rule; realization family per H2/H3 arm; endpoint version; and `training_authorized=false`. Reject duplicate arm names, mutable parameter grids, missing seeds, and post-freeze edits.

- [ ] **Step 2: Run manifest tests and verify RED**

Run: `pytest tests/test_v79_factorial_worlds_v1.py -k manifest -v`
Expected: FAIL because `ArmManifest` is missing.

- [ ] **Step 3: Implement frozen manifest structures**

Define immutable manifest dataclasses and a canonical JSON serialization/hash function used by all receipts.

- [ ] **Step 4: Run manifest tests and verify GREEN**

Run Step 2 command; expected PASS.

- [ ] **Step 5: Write failing factorial-composition tests**

Assert:
- H0 = current E2 biology + current baseline observer;
- H1 = new biology + current observer;
- H2 = E2 biology + new observer;
- H3 = new biology + new observer;
- H1 and H3 share the same upstream biology seed/config for matched comparisons;
- H2 and H3 use the same observation-family configuration when intended by the manifest;
- source/operator is crossed with biology rather than replaying real source×class contingency by default.

- [ ] **Step 6: Write failing C_OBS/C_BIO tests**

Assert C_OBS pair members have identical latent-truth hashes and different observation-regime identifiers; C_BIO pair members have different latent-truth hashes but identical observation-regime configuration. Reject any pair violating those identities.

- [ ] **Step 7: Run composition/control tests and verify RED**

Run: `pytest tests/test_v79_factorial_worlds_v1.py -k "factorial or counterfactual or c_obs or c_bio" -v`
Expected: FAIL because world builder is missing.

- [ ] **Step 8: Implement `build_factorial_worlds(...)`**

Compose existing frozen H0 pieces without modifying them; use Tasks 1–2 for H1/H2/H3; emit counterfactual pair manifests with truth/observer hashes; serialize sparse counts and identity-scrubbed truth metadata. Do not expose real gene identities as synthetic biological truth.

- [ ] **Step 9: Run Task 3 tests**

Run: `pytest tests/test_v79_factorial_worlds_v1.py -v`
Expected: PASS.

- [ ] **Step 10: Commit**

Commit message: `feat: build V79 factorial synthetic worlds`.

### Task 4: Legacy + localization-aware scoring

**Files:**
- Create: `scripts/v79/score_v79_factorial_worlds.py`
- Create: `tests/test_v79_factorial_scoring_v1.py`

**Interfaces:**
- Consumes: generated worlds, frozen evaluation universe/selection rules, existing V77/V78 scoring helpers, V79 localization helper.
- Produces: `score_world(...)`, `score_factorial_tournament(...)`, per-arm score receipt, factorial comparison summary.

- [ ] **Step 1: Write failing frozen-continuity tests**

Use a deterministic fixture to assert V79 scorer delegates canonical 3K selection and V78 signed metrics rather than reimplementing them. Pin `|r|>0.3` canonical and sensitivity thresholds `0.1/0.2/0.3/0.4`.

- [ ] **Step 2: Run continuity tests and verify RED**

Run: `pytest tests/test_v79_factorial_scoring_v1.py -k continuity -v`
Expected: FAIL because scoring wrapper is absent.

- [ ] **Step 3: Implement legacy scoring wrapper**

Reuse existing V77/V78 functions for expression/detection topology, T5, abundance, depth, and signed metrics. Do not change frozen semantics.

- [ ] **Step 4: Write failing localization-aware scoring tests**

Assert every arm reports pooled, broad-class, class+depth, and supported class+depth+source/operator views using the same V79 localization support rules. Synthetic donor support must be deliberately sufficient for a donor-conditioned descriptive view.

- [ ] **Step 5: Write failing counterfactual metric tests**

Assert scorer reports latent distance and observed distance for C_OBS/C_BIO pairs but does not run JEPA or produce representation metrics.

- [ ] **Step 6: Implement localization and control scoring**

Call the existing V79 localization helpers and produce identity-scrubbed aggregate outputs only. Preserve all per-arm raw topology summaries needed for audit while excluding real/synthetic gene identity lists from ruling exports.

- [ ] **Step 7: Write failing mechanism-comparison tests**

Pin causal comparison labels: `BIOLOGY_NECESSARY`, `OBSERVER_NECESSARY`, `BOTH_AND_INTERACTION`, `BIOLOGY_ONLY_SUFFICIENT`, `OBSERVER_ONLY_SUFFICIENT`, `COUPLING_FALSIFIED`, or `FAMILY_UNRESOLVED`. Tests must prove no label can be selected from aggregate distance alone.

- [ ] **Step 8: Implement `score_factorial_tournament(...)`**

Return per-arm metrics plus comparison evidence; leave promotion decision to the terminal gate in Task 5.

- [ ] **Step 9: Run Task 4 tests**

Run: `pytest tests/test_v79_factorial_scoring_v1.py -v`
Expected: PASS.

- [ ] **Step 10: Commit**

Commit message: `feat: score V79 factorial synthetic worlds`.

### Task 5: Fail-closed execution, falsification, and receipts

**Files:**
- Create: `scripts/v79/run_v79_factorial_tournament.py`
- Create: `tests/test_v79_factorial_gate_v1.py`

**Interfaces:**
- Consumes: frozen V78/V79 authorities, arm manifest, Tasks 1–4, corrected-TRAIN scorer-only references.
- Produces exactly versioned non-authorizing receipts for preexecution gate, arm manifest, biological authority, observation authority, counterfactual manifest, per-arm generation, per-arm scoring, and terminal ruling.

- [ ] **Step 1: Write failing preexecution/custody tests**

Assert execution blocks before generation if the frozen V78 base moves, any required authority hash mismatches, the arm manifest hash differs from preregistration, any prohibited data flag is present, or `training_authorized` is true anywhere upstream.

- [ ] **Step 2: Run custody tests and verify RED**

Run: `pytest tests/test_v79_factorial_gate_v1.py -k "gate or custody or hash or unauthorized" -v`
Expected: FAIL because execution gate is missing.

- [ ] **Step 3: Implement preexecution gate and atomic receipt writer**

Reuse existing V78/V79 custody checks where possible. Gate result must be `READY` only with zero blockers; otherwise write only the blocked gate receipt and no scientific arm output.

- [ ] **Step 4: Write failing falsification-rule tests**

Pin all design failures: pooled improvement with implausible within-class geometry; signed-ratio match with damaged degree/transitivity; source-dependent biological assignment; forced detection count; broken C_OBS truth identity; collapsed C_BIO truth; identity leakage; post-outcome parameter mutation; protected-data access; any training authorization.

- [ ] **Step 5: Implement terminal falsification/ruling logic**

The ruling may recommend a mechanism family only when all prespecified adequacy/control requirements pass. It must never authorize JEPA training. If all arms fail, emit `FAMILY_UNRESOLVED`/reopen-mechanism-family rather than expanding the same parameter search automatically.

- [ ] **Step 6: Write failing receipt-schema tests**

Assert all receipts include lineage hashes, manifest hash, seed set, endpoint version, protected-data false flags, and non-authorizing fields. Terminal ruling must contain `training_authorized: false`, `v78_retuning_authorized: false`, and `synthetic_arm_promoted` either null or a synthetic-family recommendation explicitly marked `NOT_TRAINING_AUTHORITY`.

- [ ] **Step 7: Implement `run_v79_factorial_tournament.py` CLI**

CLI accepts authority/manifests/output paths only; no free-form post-hoc parameter overrides. It executes one frozen tournament and writes receipts atomically.

- [ ] **Step 8: Run Task 5 tests**

Run: `pytest tests/test_v79_factorial_gate_v1.py -v`
Expected: PASS.

- [ ] **Step 9: Run full V79 suite**

Run: `pytest tests/test_v79_hierarchical_biology_v1.py tests/test_v79_observation_operator_v1.py tests/test_v79_factorial_worlds_v1.py tests/test_v79_factorial_scoring_v1.py tests/test_v79_factorial_gate_v1.py tests/test_v79_detection_localization_v1.py tests/test_v79_detection_localization_receipts_v1.py tests/test_v79_detection_localization_execution_v1.py -v`
Expected: all PASS.

- [ ] **Step 10: Commit**

Commit message: `feat: add fail-closed V79 factorial tournament`.

### Task 6: Frozen preexecution package only — no scientific run yet

**Files:**
- Create: `docs/agent/V79_FACTORIAL_TOURNAMENT_PREEXECUTION_20261010.md`
- Create: `results/v79_factorial/V79_FACTORIAL_ARM_MANIFEST_V1.json`
- Create: `results/v79_factorial/V79_FACTORIAL_PREEXECUTION_GATE_V1.json` only when the gate is actually run.

**Interfaces:**
- Consumes: reviewed implementation, exact authorities/seeds/cell counts/arm parameters.
- Produces: immutable execution contract and arm manifest; no scientific outcomes until the manifest is committed and independently reviewed.

- [ ] **Step 1: Freeze exact arm parameters and seeds before execution**

Record cell count, synthetic donor count, class balancing rule, substate-count distribution, module-size distribution, donor-effect scale authority, observation realization families, any prospectively fixed magnitude grid, and every seed. No `TBD` values are allowed.

- [ ] **Step 2: Write preexecution contract**

Document exact command, input hashes, output names, protected-data prohibitions, expected arm count, and hard stop on any gate blocker.

- [ ] **Step 3: Run manifest validation only**

Run the CLI in `--preexecution-only` mode. Expected: READY gate plus manifest receipts only; no H0/H1/H2/H3 scientific metrics.

- [ ] **Step 4: Commit preexecution package**

Commit message: `docs: freeze V79 factorial tournament preexecution`.

- [ ] **Step 5: Stop for independent review before scientific execution**

Do not run the scientific tournament in the same unreviewed commit that first freezes its exact parameters. The next action after this plan is an implementation review and then a separate explicit execution decision.
