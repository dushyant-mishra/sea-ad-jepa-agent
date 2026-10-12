# V79 V2_CORE Qualification Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed, blinded V2_CORE qualification execution lane that can benchmark and later run the frozen 1,056-fit Q00–Q11 campaign without exposing controller truth, followed by a physically separate controller-only scorer.

**Architecture:** Fitting and scoring are separate trust domains. The fit side consumes only `blinded_fit_inputs`, obtains all model/sampler/gate numbers from the immutable Contract V2 via `v79_v2_core_launch.require_launch_authority()`, writes opaque fit receipts, and cannot resolve `controller_truth`. The controller scorer is a separate entry point that accepts only frozen completed fit receipts plus the committed realization-audit truth surface and applies the contract's predeclared gates after fitting is complete.

**Tech Stack:** Python 3.11, NumPy 2.0.2, JAX 0.4.35, NumPyro 0.15.3, pytest; exact qualification runtime versions are governed by `results/v79/v2_core_qualification/inputs/V79_BAYES_ENV_PIP_FREEZE.txt`.

**Spec:** `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json`; realization authority is PR #297 head `bb8923562144a0b19a6d80795adf727986893ded` and controller PASS comment `6118626704`.

## Global Constraints

- Contract SHA must be exactly `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`; all numbers come from that JSON at runtime.
- Realized root manifest SHA must be `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`; world-set directory digest must be `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`; blinded-fit index SHA must be `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`.
- Fit surface permits only opaque world ID, `src`, `donor`, `cls`, `log_lib`, support, and train/same-donor/new-donor observations. No Q label, truth, seed root, operator/matrix identity, or controller-truth path may enter the fitter.
- V2_CORE model is exactly detection Bernoulli + positive lognormal, with quadratic depth, broad class, source, and donor-within-source; operator, donor×class, source×class, dataset/matrix identity remain excluded.
- Likelihood includes only structurally measured entries; measured zero remains a valid detection zero.
- Sampler/recovery/resource settings are read from Contract V2. No fitter-local copies of chains/warmup/draws/target-accept/R-hat/ESS/tree-depth/settle-time/runtime ceiling are allowed.
- Qualification run count is exactly the contract's 1,056 fits. Benchmark fits are marked engineering-only and never count toward qualification.
- First hard scientific FAIL is terminal; later worlds, if run diagnostically, receive only the contract's post-terminal diagnostic label and cannot rescue qualification.
- Fitting never scores truth. Scoring never mutates fit artifacts. Training, real-TRAIN posterior inference, factorial science, TEST/Morabito/pathology, target discovery, and JEPA training remain off.

## Review Focus

1. A path traversal/symlink from the blinded root must not permit reads from `controller_truth`; test on both lexical and resolved paths.
2. Manifest tampering or any `.npy` hash mismatch must fail before model construction or sampler initialization.
3. Structurally unmeasured cells must be absent from both detection and positive likelihoods; positive additionally requires observed > 0.
4. A benchmark receipt must be impossible to relabel as a qualification fit; execution mode is authority-bound and serialized in every receipt.
5. Partial/restarted qualification work must not silently overwrite a prior fit or consume a new seed under the same fit identity; existing artifact mismatch is terminal.

---

### Task 1: Blinded package authority loader

**Files:**
- Create: `scripts/v79/v79_v2_core_fit_surface.py`
- Test: `tests/v79/test_v79_v2_core_fit_surface.py`

**Interfaces:**
- Consumes: repo root, realized package root, Contract V2 via `require_launch_authority()`.
- Produces: `BlindedWorld`, `load_blinded_index(root, package_root)`, `load_blinded_world(package_root, opaque_world_id)`, `load_gene_inputs(world, gene_index, replicate)`.

- [ ] RED: tests refuse non-opaque IDs, Q labels, `controller_truth` resolution, unknown files, wrong root/index/manifest/file hashes, object dtype arrays, malformed shapes, and symlink/path traversal.
- [ ] RED: tests prove loader exposes exactly `src`, `donor`, `cls`, `log_lib`, support and observations; never operator/matrix/truth/seed/world-name.
- [ ] GREEN: implement minimal hash-first loader; all `.npy` use `allow_pickle=False` and are checked against the per-world blinded manifest before return.
- [ ] VERIFY: run focused tests, then full `pytest`.
- [ ] COMMIT: `feat(v79): add blinded V2_CORE fit surface loader`.

### Task 2: Contract-driven model specification

**Files:**
- Create: `scripts/v79/v79_v2_core_fit_model.py`
- Test: `tests/v79/test_v79_v2_core_fit_model.py`

**Interfaces:**
- Consumes: `BlindedWorld` gene inputs + Contract V2 model/priors.
- Produces: `build_detection_model(contract, gene_inputs)`, `build_positive_model(contract, gene_inputs)`, `model_fingerprint(contract)`.

- [ ] RED: tests assert only frozen terms appear and excluded operator/matrix/interactions cannot be injected.
- [ ] RED: tests assert structural support masks detection; positive uses measured & observed>0 only; donor effect is within-source partial pooling using donor identities available on fit surface.
- [ ] RED: test priors are read from contract and changing contract bytes/hash is refused by launch authority before model construction.
- [ ] GREEN: implement NumPyro models with parameter names stable for diagnostics/scoring.
- [ ] VERIFY: focused tests + full suite.
- [ ] COMMIT: `feat(v79): implement contract-driven V2_CORE models`.

### Task 3: Sampler and frozen recovery state machine

**Files:**
- Create: `scripts/v79/v79_v2_core_fit_runner.py`
- Test: `tests/v79/test_v79_v2_core_fit_runner.py`

**Interfaces:**
- Consumes: model builder, fit identity, Contract V2 sampler/recovery fields, execution mode (`ENGINEERING_BENCHMARK` or later controller-authorized `QUALIFICATION`).
- Produces: immutable per-fit receipt + posterior artifact hashes; `evaluate_sampler_diagnostics()`; `next_recovery_action()`.

- [ ] RED: primary schedule comes only from Contract V2; local override arguments are refused.
- [ ] RED: recovery sequence is exactly contract-defined and finite; no extra retries or threshold relaxation.
- [ ] RED: existing matching completed receipt is read-only/idempotent; partial or hash-mismatched prior output is terminal, never overwritten.
- [ ] RED: benchmark mode cannot increment `qualification_fits_run` and cannot create qualification-result paths.
- [ ] GREEN: implement runner without any scoring/truth imports.
- [ ] VERIFY: focused tests + full suite.
- [ ] COMMIT: `feat(v79): add frozen V2_CORE sampler state machine`.

### Task 4: Engineering benchmark entry point

**Files:**
- Create: `scripts/v79/run_v79_v2_core_benchmark.py`
- Create: `scripts/v79/v79_v2_core_resource_monitor.py`
- Test: `tests/v79/test_v79_v2_core_benchmark.py`

**Interfaces:**
- Consumes: fit surface + runner in `ENGINEERING_BENCHMARK` mode.
- Produces: benchmark receipt with exact package/code/environment bindings and CPU/RSS/wall-time diagnostics only.

- [ ] RED: benchmark cannot resolve truth/Q labels/operator and must revalidate root/index hashes before execution.
- [ ] RED: benchmark receipt has `benchmark_run=true`, `qualification_fits_run=0`, `scoring_run=false`, `truth_accessed=false`, `training_authorized=false`.
- [ ] RED: one-heavy-fit policy is serialized and concurrent heavy fit acquisition fails closed.
- [ ] GREEN: implement engineering-only benchmark wrapper around actual fitter path.
- [ ] VERIFY: unit tests only in CI; physical benchmark remains controller-authorized locked-machine execution.
- [ ] COMMIT: `feat(v79): add blinded engineering benchmark runner`.

### Task 5: Qualification campaign planner and custody

**Files:**
- Create: `scripts/v79/v79_v2_core_qualification_plan.py`
- Test: `tests/v79/test_v79_v2_core_qualification_plan.py`

**Interfaces:**
- Consumes: blinded index + Contract V2; no truth.
- Produces: deterministic opaque fit queue and campaign custody receipt.

- [ ] RED: queue cardinality reproduces `resources.estimate.n_fits` from contract and uses opaque IDs only.
- [ ] RED: queue ordering is deterministic, identities include world manifest SHA + part + gene + sampler stage, and no Q labels appear.
- [ ] RED: qualification mode requires a future controller authorization receipt distinct from benchmark authority; absent/incorrect authority refuses execution.
- [ ] GREEN: implement planner/custody only; do not authorize or execute the campaign in this PR.
- [ ] VERIFY: tests + full suite.
- [ ] COMMIT: `feat(v79): freeze opaque qualification campaign planner`.

### Task 6: Controller-only scorer boundary

**Files:**
- Create: `scripts/v79/v79_v2_core_score.py`
- Test: `tests/v79/test_v79_v2_core_score.py`

**Interfaces:**
- Consumes: completed frozen fit receipts/posteriors + PR #297 controller-truth audit surface + Contract V2.
- Produces: score table and terminal qualification receipt; never called by fitter process.

- [ ] RED: scorer refuses incomplete campaign, any fit hash mismatch, any contract/package mismatch, or non-frozen truth surface.
- [ ] RED: gate list/counts/classifications come only from contract; exactly four LIMIT gates and all Q11 gates hard FAIL are reproduced via launch authority.
- [ ] RED: first hard FAIL locks terminal `NOT_QUALIFIED`; post-terminal diagnostics cannot change terminal result.
- [ ] RED: no scorer import is reachable from fitter/benchmark modules (static dependency test).
- [ ] GREEN: implement gate evaluation by contract schema; keep descriptive metrics separate from hard/limit verdicts.
- [ ] VERIFY: synthetic fixture tests only; do not score realized Q00–Q11 before campaign authorization/completion.
- [ ] COMMIT: `feat(v79): add controller-only qualification scorer`.

### Task 7: CI and authority audit

**Files:**
- Create: `.github/workflows/v79-v2-core-qualification-executor.yml`
- Test: all tests above.

**Interfaces:**
- Consumes: repository branch bytes.
- Produces: Linux + Windows green structural/unit audit; never runs physical NUTS qualification.

- [ ] CI installs only dependencies needed for structural/unit tests; no realized observation arrays or secrets.
- [ ] CI runs launch-authority, realization-audit-freeze, and new executor tests together.
- [ ] Add static scan ensuring new fit-side modules contain no `controller_truth`, `world_name`, Q-label lookup, operator design load, or scorer import except explicit refusal tests/documentation.
- [ ] Verify both platforms green, record exact source/merge tree identity, and stop for controller audit.
- [ ] COMMIT: `ci(v79): audit V2_CORE qualification executor`.
