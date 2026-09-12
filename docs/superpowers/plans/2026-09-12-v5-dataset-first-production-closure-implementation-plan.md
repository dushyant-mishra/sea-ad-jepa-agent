# V5 Dataset-First Production Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Close the V5 pre-execution qualification chain around authenticated FULL104 data, deriving scientific/model geometry from the dataset before any bounded qualification run.

**Architecture:** Preserve the existing fail-closed guards and dependency graph. Implement the missing real-data producers and exact artifact-binding layers in the order FULL104 -> dimensions -> schedule/proposal/packing -> anti-cheat controls -> production GPU -> bounded qualification. Relational training remains inactive until TD60 and partial-evidence qualification close.

**Tech Stack:** Python 3.11+, pytest, NumPy/SciPy, SQLite, PyTorch/CUDA for production-geometry execution, JSON/CSV/SHA-256, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-12-v5-dataset-first-production-closure-design.md`

## Global Constraints

- Working branch: `planning/v5-dataset-first-production-closure-20260912`; source branch remains untouched.
- Dataset is authority; synthetic fixtures are mechanics-only.
- FULL104 is 4,553,407 reader-fit cells, 104 donors, 42 operators/matrices, 8,915 Level-4 blocks, 41,238 addresses.
- Corrected 42-shard TRAIN cache and 50K discovery archive cannot satisfy FULL104 authority.
- No reader_validation, reader_oracle, DEV, SEALED, pathology, or production training.
- Historical widths and CUDA geometry are non-authoritative for production values.
- Every authority-bearing artifact must be canonical-byte hash-bound to its exact content and parents.
- Relational training remains inactive before lawful base teacher -> TD60 -> partial-evidence qualification.

---

### Task 1: Fail-close the legacy 42-shard full-reader preflight

**Files:**
- Modify: `scripts/v5_anticheat/full_reader_relational_target_preflight_v1.py`
- Create: `tests/test_full_reader_relational_target_preflight_v1.py`

**Interfaces:**
- Produce `classify_expression_authority(loader_schema: str, location_status: str) -> dict`.
- `foundation-train-loader-v1` may report TRAIN-cache physical binding only and must never emit a FULL104 PASS terminal.
- Required production terminal remains `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE` from `bind_full104_expression_blocks_v4.py`.

- [ ] Write failing test proving `foundation-train-loader-v1` plus `PASS_42_OF_42_PHYSICAL_SHARDS_BOUND` is still production STOP.
- [ ] Run focused test and confirm RED because classifier/behavior does not exist.
- [ ] Implement minimal classifier and route main output through it.
- [ ] Assert output records `full104_expression_binding_closed=False` and required binder/terminal.
- [ ] Run focused tests and existing TRAIN/FULL104 binder tests.
- [ ] Commit.

### Task 2: Add canonical artifact byte/hash binding

**Files:**
- Create: `src/sea_ad_jepa/v5/artifact_binding_v1.py`
- Create: `tests/test_artifact_binding_v1.py`
- Modify producers/validators only where necessary to consume exact artifact envelopes.

**Interfaces:**
- `canonical_json_bytes(payload) -> bytes`
- `artifact_sha256(payload) -> str`
- `seal_artifact(schema, payload, parent_sha256) -> dict`
- `validate_artifact(envelope, expected_schema, expected_parents) -> dict`

- [ ] Test dictionary-order-independent canonical bytes/hash.
- [ ] Test payload mutation, parent substitution and digest substitution fail.
- [ ] Implement minimal canonical serializer and envelope validator.
- [ ] Bind new production artifacts to exact parents.
- [ ] Run focused suite and commit.

### Task 3: FULL104 closure receipt producer and remote execution contract

**Files:**
- Modify: `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`
- Modify: `tests/test_bind_full104_expression_blocks_v4.py`
- Create: `docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`

**Interfaces:**
- Binder output must remain fail-closed and training-authorized false.
- On real geometry emit canonical artifact payload suitable for Task 2 sealing.
- Fixture mode must never be promotable.

- [ ] Add failing test that fixture-mode receipt cannot become production artifact.
- [ ] Add canonical parent identity fields required downstream.
- [ ] Run binder unit tests.
- [ ] Document exact remote GPU-laptop invocation and compact receipt return fields.
- [ ] Commit.

### Task 4: Implement missing full-stream dimension producer

**Files:**
- Create: `scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py`
- Create: `tests/test_derive_full_stream_dimension_family_v1.py`
- Reuse: `src/sea_ad_jepa/v5/dimension_execution_firewall_v1.py`
- Reuse: `src/sea_ad_jepa/v5/dimension_authority_guard_v4.py`

**Interfaces:**
- Input requires canonical FULL104 closure artifact.
- Output receipt fields must satisfy `DimensionExecutionFirewallV1` and `DimensionAuthorityV4`.
- `D_shared` selection uses contiguous prefix; supported boundary returns expansion, never boundary selection.
- `D_private` starts only after frozen `D_shared`; zero is lawful.
- `D_obs` is separate observation rank.
- Null and donor-resample counts come from explicit precision/error-budget inputs.

- [ ] Build synthetic mechanics tests for zero, interior prefix, boundary expansion, D arithmetic and forbidden sampled caps.
- [ ] Implement pure adjudication/receipt builder before FULL104 numerical executor.
- [ ] Implement streaming input contract with no production numeric result unless FULL104 artifact is real and non-fixture.
- [ ] Run firewall + producer tests and commit.

### Task 5: Bind schedule/proposal/packing to one FULL104 design context

**Files:**
- Modify or add successor producers around `derive_full_population_schedule_optimum_v3.py`, proposal-weight and packing/restart artifacts.
- Test cross-artifact substitution against `preexecution_dependency_guard_v1.py`.

- [ ] Add tests swapping one FULL104/dimension/schedule artifact while keeping others valid.
- [ ] Ensure all swaps fail before GPU qualification.
- [ ] Seal canonical child artifacts with exact parent hashes.
- [ ] Run dependency-guard tests and commit.

### Task 6: Build executable two-sided anti-cheat control producers

**Files:**
- Create focused producer/harness modules under `scripts/v5_anticheat/`.
- Add tests for the seven canonical rejection-capable gates.

**Interfaces:**
- Each gate produces raw control outputs, raw-output SHA, and summary report.
- Both minimally valid and minimally invalid controls execute the actual gate at exact adjudication geometry.
- Hand-authored pass booleans are not sufficient.

- [ ] Implement one gate at a time using RED/GREEN cycles.
- [ ] Cover donor recurrence, held-out biology, QC/measurement, same-cell intervention, shortcut superiority, student collapse, teacher collapse.
- [ ] Run `rejection_gate_power_calibration_v3` against generated evidence.
- [ ] Commit in independently reviewable gate groups.

### Task 7: Implement production-geometry CUDA qualification runner

**Files:**
- Create: `scripts/v5_anticheat/run_v5_production_geometry_gpu_qualification_v1.py`
- Create: `tests/test_v5_production_geometry_gpu_qualification_runner_v1.py`
- Reuse: `production_geometry_gpu_guard_v1.py` and frozen mechanics chain.

**Interfaces:**
- Real FULL104 reader batch required for production execution.
- Geometry must be bound to data-derived dimension/schedule/packing artifacts.
- Emit exact protected-48 gradient, parameter-motion, Adam-moment, EMA and atomic-commit evidence.

- [ ] Unit-test receipt construction and substitution failures without claiming CUDA authority.
- [ ] Implement runner fail-closed when CUDA/real reader unavailable.
- [ ] Execute remotely only after Tasks 3-6 close.
- [ ] Validate receipt and commit code before outcome interpretation.

### Task 8: Close bounded pre-execution qualification

**Files:**
- Use `preexecution_dependency_guard_v1.py`, `preexecution_qualification_bundle_v2.py`, `trainer_preexecution_contract_v4.py`.
- Add an integration test with real artifact envelopes replaced by deterministic fixtures for mechanics only.

- [ ] Prove all dependency substitutions fail.
- [ ] Prove output is `BOUNDED_QUALIFICATION_ONLY` and production training remains false.
- [ ] Run relevant V5 exact-head suites and clean-archive CI.
- [ ] Commit closeout receipt/documentation.

### Task 9: Lawful base teacher and TD60 handoff

No implementation/execution until Tasks 1-8 close and explicit bounded-qualification authority exists.

- [ ] Freeze exposure-defined base-teacher geometry with relational training inactive.
- [ ] Obtain lawful base EMA checkpoint without outcome-responsive stopping.
- [ ] Run exact frozen TD57B/TD59 TD60 semantics: 24/24 global + 24/24 mesoscale.
- [ ] Proceed to partial-evidence student relational qualification only after TD60 PASS.

## Verification Before Any Success Claim

- Run targeted RED before implementation and GREEN after.
- Run relevant existing V5 tests after every task.
- Use exact pushed branch bytes for final verification.
- Check GitHub workflow status when a workflow covers the branch; otherwise record that CI is not configured for the successor branch and do not imply CI PASS.
- No result may authorize production training in this plan.
