# Corrected TD56/57B/57C/59 Replay Turnkey Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and qualify a fail-closed corrected-replay stage that can authenticate the accepted G6/G7/diagnostic lineage, verify the frozen TD56/TD57B/TD57C/TD59 experiment definitions, and later execute the four biological replays exactly once under fresh replay-only authority without changing the science.

**Architecture:** The stage is split into four independent surfaces: an immutable machine-readable replay contract, a read-only `QUALIFY` gate that authenticates all predecessor and executor identities without producing corrected biological outcomes, an `EXECUTE_ONCE` launcher that spends fresh replay-only authority before outcome-bearing work, and a post-run evidence validator. G7 remains `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`; the stage may advance only because the separately audited metadata diagnostic establishes `GENUINELY_DISJOINT_NATURAL_CELL_SETS`, not because G7 is reinterpreted as PASS.

**Tech Stack:** Python 3.11-compatible stdlib (`argparse`, `dataclasses`, `hashlib`, `json`, `pathlib`, `subprocess`), existing NumPy/SciPy stack used by the frozen replay executors, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-12-td-downstream-turnkey-gates-design.md`

## Global Constraints

- Accepted G6 producer commit is exactly `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`.
- Accepted G6 external acceptance SHA-256 is exactly `89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb`.
- Accepted G6 receipt SHA-256 is exactly `2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b`.
- Corrected values SHA-256 is exactly `fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9`; corrected metadata SHA-256 is exactly `bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74`.
- G7 implementation is exactly `8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27`; marker SHA-256 is `2579b9a6a5cbfc89f4dd38082515a290681fc5413afeb95536b62bbfd46f2667`; receipt SHA-256 is `47f9be6e8fef3fa70c07fbe8011fa1360df72e26b8259fc9655a369768a97fcf`.
- G7 terminal remains exactly `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`; no code may map it to PASS.
- The prerequisite amendment is valid only when diagnostic evidence is bound to commit `0b50938e` and classification `GENUINELY_DISJOINT_NATURAL_CELL_SETS`.
- TD57B frozen executor SHA-256 is `1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`; its historical fast-wrapper identity is separate and must not silently replace the frozen executor unless the contract explicitly binds the wrapper as a verified byte-equivalent acceleration.
- TD57C exact local executor SHA-256 is `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`.
- TD59 must use the admissible replay-closure successor `target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/td59_replay_closure_executor_v1.py`, SHA-256 `870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`; the unrecovered historical original is never impersonated.
- TD56 must bind the recovered exact primary executor artifacts and their prospective freeze; the contract must enumerate the exact HVS/NPH52/SEA_AD executor bytes actually selected before any replay launch. No later worker may choose among historical variants after seeing corrected outcomes.
- Replay order is TD56 → TD57B → TD57C → TD59. The launcher may stop early only where the frozen biological routing requires it; it may not skip an applicable stage for convenience.
- Donor remains the primary biological replication unit; source/acquisition remains an observation operator.
- No scientific thresholds, pair/view definitions, locality fractions, nulls, source weighting, support rules, or outcome interpretation may be changed by this implementation.
- `QUALIFY` must not create a corrected biological result, run the decision-bearing replay kernels, or open protected outcome-bearing values.
- `EXECUTE_ONCE` requires fresh replay-specific owner/runtime/operational authority and a fresh namespace. Once its start marker exists the authority/namespace is spent regardless of result.
- `g6_execution_authorized=false`, `g7_execution_authorized=false`, `target_selection_authorized=false`, `td60_authorized=false`, `stage4_authorized=false`, and `training_authorized=false` remain enforced throughout this module.
- No G6 rerun, G7 rerun, target tournament execution, TD60, Stage 4, or JEPA training is part of this plan.

## Review Focus

1. **G7 relabeling hazard:** a package with the correct G7 receipt but any terminal other than the exact NOT_ESTIMABLE terminal, or any attempt to treat that terminal as PASS, must be refused before replay work.
2. **Diagnostic substitution scope:** missing, altered, or differently classified diagnostic evidence must fail closed; `GENUINELY_DISJOINT_NATURAL_CELL_SETS` substitutes only for the impossible overlap prerequisite and grants no value-agreement claim.
3. **Historical-executor ambiguity:** TD56/TD57B/TD57C must resolve to one prospectively bound executor identity each; TD59 must resolve only to the admitted successor. Ambiguous or multiple candidate executors must fail qualification.
4. **One-shot spending:** a start marker, existing namespace, or previously spent authority must prevent another execution even after exception or NOT_ESTIMABLE.
5. **Cheap estimability:** any replay subtest whose comparison population/support can be established without protected values must prove nonzero estimability before the start marker; a zero comparison population must stop qualification rather than spend replay authority.

---

### Task 1: Freeze the machine-readable corrected-replay contract

**Files:**
- Create: `target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_CONTRACT_V1.json`
- Create: `scripts/v5/td_corrected_replay_contract_v1.py`
- Test: `tests/v5/test_td_corrected_replay_contract_v1.py`

**Interfaces:**
- Consumes: predecessor constants from the Global Constraints and existing historical prospective-screen/result/replay-closure files.
- Produces: `load_contract(path: Path) -> dict`, `validate_contract(contract: dict, repo_root: Path) -> dict`, and a canonical contract JSON containing `predecessors`, `executors`, `stages`, `authority_policy`, `estimability_policy`, `interpretation_policy`, and `downstream_authority`.

- [ ] **Step 1: Write failing contract tests**

Add tests asserting the exact G6/G7/diagnostic identities, exact G7 NOT_ESTIMABLE terminal, TD57B/TD57C/TD59 hashes, four-stage order, all downstream authority flags false, and refusal of any contract that maps G7 NOT_ESTIMABLE to PASS.

- [ ] **Step 2: Run the focused contract test and record RED**

Run: `pytest -q tests/v5/test_td_corrected_replay_contract_v1.py`
Expected: collection/import failure because `td_corrected_replay_contract_v1` does not yet exist.

- [ ] **Step 3: Implement the minimal contract loader/validator and commit the frozen JSON**

`validate_contract()` must hash every repository-resident executor it can bind, require the exact fixed predecessor values, verify the TD59 successor identity, and require an explicit single selected TD56 executor set. It must not read corrected outcome arrays.

- [ ] **Step 4: Run focused tests GREEN**

Run: `pytest -q tests/v5/test_td_corrected_replay_contract_v1.py`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git commit -am "td: freeze corrected replay contract"`

### Task 2: Implement predecessor and diagnostic authentication

**Files:**
- Create: `scripts/v5/td_corrected_replay_preflight_v1.py`
- Test: `tests/v5/test_td_corrected_replay_preflight_v1.py`

**Interfaces:**
- Consumes: `validate_contract()` from Task 1 plus paths to G6 acceptance/receipt, G7 marker/receipt, and diagnostic package.
- Produces: `authenticate_predecessors(contract: dict, inputs: PreflightInputs) -> PreflightReceipt` and CLI mode `QUALIFY_PREDECESSORS`.

- [ ] **Step 1: Write failing predecessor-authentication tests**

Cover exact good fixtures and refusal cases for wrong G6 receipt hash, wrong G7 marker/receipt hash, G7 PASS relabeling, missing diagnostic, wrong diagnostic commit/classification, reused G7 authority, and a diagnostic that claims value agreement.

- [ ] **Step 2: Run tests RED**

Run: `pytest -q tests/v5/test_td_corrected_replay_preflight_v1.py`
Expected: import failure for the new module.

- [ ] **Step 3: Implement metadata/hash-only authentication**

The implementation may parse JSON/text receipts and hash files but must expose no API that opens G6 corrected value arrays or replay result arrays. Emit a deterministic receipt with `technical_prerequisite_closed=true`, `g7_pass=false`, and `closure_reason="G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS"`.

- [ ] **Step 4: Run tests GREEN**

Run: `pytest -q tests/v5/test_td_corrected_replay_preflight_v1.py`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git commit -am "td: authenticate corrected replay predecessors"`

### Task 3: Add pre-marker estimability and executor-binding qualification

**Files:**
- Create: `scripts/v5/td_corrected_replay_qualify_v1.py`
- Test: `tests/v5/test_td_corrected_replay_qualify_v1.py`

**Interfaces:**
- Consumes: validated contract and authenticated predecessor receipt.
- Produces: `qualify_replay(contract: dict, predecessor_receipt: dict, repo_root: Path, metadata_inputs: QualificationInputs) -> QualificationReceipt` and CLI `QUALIFY`.

- [ ] **Step 1: Write failing qualification tests**

Require qualification to resolve exactly four frozen stages, reject multiple/ambiguous TD56 variants, reject altered executor bytes, reject missing support/comparison populations, reject zero estimable cases where metadata can prove zero, and prove no replay output files/start marker are created.

- [ ] **Step 2: Run tests RED**

Run: `pytest -q tests/v5/test_td_corrected_replay_qualify_v1.py`
Expected: import failure.

- [ ] **Step 3: Implement outcome-blind qualification**

Qualification may inspect schemas, metadata/support masks, manifest indices, file sizes/hashes, and executor source bytes. It may not invoke the four decision-bearing kernels or read protected corrected outcomes. The receipt must enumerate exact selected executor paths/hashes and `comparison_population_n`/support diagnostics for every cheap pre-marker check.

- [ ] **Step 4: Run tests GREEN**

Run: `pytest -q tests/v5/test_td_corrected_replay_qualify_v1.py`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git commit -am "td: qualify corrected replay without opening outcomes"`

### Task 4: Build replay-only authority validation and one-shot state machine

**Files:**
- Create: `scripts/v5/td_corrected_replay_authority_v1.py`
- Test: `tests/v5/test_td_corrected_replay_authority_v1.py`

**Interfaces:**
- Consumes: contract SHA, qualification receipt SHA, implementation commit, proposed fresh namespace, owner/runtime/operational authority JSON.
- Produces: `bind_replay_authority(...) -> BoundReplayAuthority`, `assert_fresh_namespace(path: Path) -> None`, `begin_attempt(bound: BoundReplayAuthority, namespace: Path) -> Path`.

- [ ] **Step 1: Write failing authority/state-machine tests**

Test exact replay-only scope, all forbidden authorization flags, implementation/contract/qualification binding, fresh namespace, start-marker atomicity, spent authority, exception-after-marker behavior, and refusal to reuse G6/G7 authorities.

- [ ] **Step 2: Run tests RED**

Run: `pytest -q tests/v5/test_td_corrected_replay_authority_v1.py`
Expected: import failure.

- [ ] **Step 3: Implement minimal fail-closed state machine**

`begin_attempt()` is the only code path that creates `TD_CORRECTED_REPLAY_EXECUTION_START.json`; it must do so only after all pre-marker checks pass and before any protected replay stage is invoked.

- [ ] **Step 4: Run tests GREEN**

Run: `pytest -q tests/v5/test_td_corrected_replay_authority_v1.py`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git commit -am "td: add replay-only one-shot authority state machine"`

### Task 5: Implement the four-stage execution orchestrator without changing science

**Files:**
- Create: `scripts/v5/td_corrected_replay_execute_v1.py`
- Test: `tests/v5/test_td_corrected_replay_execute_v1.py`

**Interfaces:**
- Consumes: `BoundReplayAuthority`, frozen contract, selected executor bindings, corrected replay inputs.
- Produces: per-stage raw artifacts/receipts plus `TD_CORRECTED_REPLAY_RECEIPT_V1.json`.

- [ ] **Step 1: Write failing orchestrator tests with synthetic/stub executors**

Verify TD56→TD57B→TD57C→TD59 order, frozen early-stop rules, preservation of PASS/FAIL/NOT_ESTIMABLE without coercion, no threshold mutation, and no downstream authority. Test exception after start marker is preserved as spent failure.

- [ ] **Step 2: Run tests RED**

Run: `pytest -q tests/v5/test_td_corrected_replay_execute_v1.py`
Expected: import failure.

- [ ] **Step 3: Implement orchestration as a thin subprocess/adapter layer**

The orchestrator must not reimplement the statistics. It invokes the exact bound executors, captures their raw outputs, hashes them, and projects their terminals through the pre-existing frozen replay interpretation only after all applicable stages finish or a frozen stop condition fires.

- [ ] **Step 4: Run tests GREEN**

Run: `pytest -q tests/v5/test_td_corrected_replay_execute_v1.py`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git commit -am "td: orchestrate frozen corrected replay stages"`

### Task 6: Add top-level QUALIFY / EXECUTE_ONCE launcher

**Files:**
- Create: `scripts/v5/run_td_corrected_replay_once.sh`
- Create: `scripts/v5/run_td_corrected_replay_once.py`
- Test: `tests/v5/test_run_td_corrected_replay_once.py`

**Interfaces:**
- Consumes: contract, predecessor package, qualification package, replay-only authority, fresh namespace.
- Produces: deterministic launch record, stdout/stderr capture paths, start marker on EXECUTE only, and replay receipt when execution reaches a scientific terminal.

- [ ] **Step 1: Write failing launcher tests**

Cover `QUALIFY`, `EXECUTE_ONCE`, missing launch-audit acceptance, stale authority, dirty/reused namespace, zero-comparison precheck, forbidden G6/G7 command paths, and second-attempt refusal.

- [ ] **Step 2: Run tests RED**

Run: `pytest -q tests/v5/test_run_td_corrected_replay_once.py`
Expected: failure because launcher does not exist.

- [ ] **Step 3: Implement launcher**

`QUALIFY` must stop before `begin_attempt()`. `EXECUTE_ONCE` must require a separately committed launch-audit acceptance bound to the exact implementation/contract/qualification/authority hashes, then call `begin_attempt()` exactly once and delegate to Task 5.

- [ ] **Step 4: Run tests GREEN**

Run: `pytest -q tests/v5/test_run_td_corrected_replay_once.py`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git commit -am "td: add corrected replay qualify and one-shot launcher"`

### Task 7: Implement evidence-package validation and routing projection

**Files:**
- Create: `scripts/v5/td_corrected_replay_evidence_v1.py`
- Test: `tests/v5/test_td_corrected_replay_evidence_v1.py`

**Interfaces:**
- Consumes: completed or failed replay namespace.
- Produces: `validate_evidence(namespace: Path) -> EvidenceVerdict` and machine-readable `CORRECTED_REPLAY_ROUTING_INPUT_V2.json` compatible with existing `scripts/v5/td_corrected_replay_routing_v2.py`.

- [ ] **Step 1: Write failing evidence-validator tests**

Test complete PASS/FAIL patterns, TD57C divergence, source disagreement, NOT_ESTIMABLE, partial post-marker failure, missing/tampered artifacts, and any attempt to set target/TD60/Stage4/training authority true.

- [ ] **Step 2: Run tests RED**

Run: `pytest -q tests/v5/test_td_corrected_replay_evidence_v1.py`
Expected: import failure.

- [ ] **Step 3: Implement validator and routing projection**

The validator must reproduce hashes from bytes on disk, require the start marker for any executed evidence, preserve incomplete failure states, and emit only the exact statuses accepted by `td_corrected_replay_routing_v2.py`.

- [ ] **Step 4: Run tests GREEN**

Run: `pytest -q tests/v5/test_td_corrected_replay_evidence_v1.py tests/v5/test_td_corrected_replay_routing_v2_c6.py`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git commit -am "td: validate corrected replay evidence and routing input"`

### Task 8: Add focused CI and real-file dry qualification

**Files:**
- Create or modify: `.github/workflows/td-corrected-replay-turnkey-qualification.yml`
- Create: `docs/agent/TD_CORRECTED_REPLAY_TURNKEY_QUALIFICATION_20261012.md`

**Interfaces:**
- Consumes: Tasks 1–7.
- Produces: a reproducible CI qualification and a real-file `QUALIFY` package that proves the exact physical predecessor/executor wiring without running corrected biological replay.

- [ ] **Step 1: Add the new tests to a dedicated focused workflow**

The workflow must run all Task 1–7 tests plus existing corrected-routing tests on the pinned Python environment, capture dependency versions, and assert clean tracked worktree after tests.

- [ ] **Step 2: Run CI and require the expected RED/GREEN history to be preserved**

Do not rewrite or squash away the initial RED evidence for this module. Final qualification must show all focused tests passing.

- [ ] **Step 3: Run `QUALIFY` against the exact real predecessor files**

Expected terminal: `PASS_TD_CORRECTED_REPLAY_TURNKEY_QUALIFICATION__NO_BIOLOGICAL_REPLAY_RUN__LAUNCH_AUDIT_REQUIRED`.

The dry qualification must show: accepted G6 authenticated; G7 remains NOT_ESTIMABLE; diagnostic classification exact; selected replay executors exact; cheap estimability checks pass where applicable; no corrected replay result/start marker exists; G6/G7 namespaces unchanged.

- [ ] **Step 4: Freeze qualification evidence**

Record exact implementation head, contract SHA-256, launcher/check/validator SHA-256 values, CI run/job/artifact IDs and artifact SHA-256, real-file qualification receipt SHA, proposed fresh replay namespace, and all negative-case results.

- [ ] **Step 5: STOP for external launch audit**

Do not create replay execution authority as a side effect of CI. Fresh replay-only owner/runtime/operational authority and a launch-audit acceptance are separate subsequent records. Corrected TD56/57B/57C/59 must still be unexecuted at this point.

## Self-Review Outcome

- **Spec coverage:** all four turnkey layers in Module 1 of the downstream design are mapped to Tasks 1–8; no downstream target/TD60/training authority is introduced.
- **Step scan:** implementation tasks are separated by reviewable interfaces; no task is permitted to choose new biological thresholds or statistics.
- **Type/interface consistency:** contract → predecessor receipt → qualification receipt → bound authority → execution namespace → evidence verdict is the single directed dependency chain.
- **Review-focus coverage:** each of the five named high-risk failure classes has an explicit negative test owner.
- **Proportion:** executor statistical internals are intentionally excluded; this plan wraps frozen science rather than rewriting it.

## Execution Handoff

The user has already approved native continued execution for routine target-discovery readiness work. Implement this plan task-by-task with strict RED→GREEN TDD. Stop only at the final external launch-audit boundary; do not execute corrected biology under this plan without a separately audited launch package.