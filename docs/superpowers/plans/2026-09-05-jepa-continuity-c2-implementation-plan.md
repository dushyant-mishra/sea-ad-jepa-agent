# JEPA Continuity and C2 Forensic Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Do not delegate routine tasks. An independent verifier is reserved for the final conclusion-bearing promotion gate.

**Goal:** Build an agent-neutral Codex/Claude continuity system, then identify and regression-test the exact mechanical condition that kills historical T1 attention-path gradients.

**Architecture:** A deterministic checkpoint utility binds Git state, authorities, files, gates, and the exact next action so either coding agent can resume safely. A separate synthetic-only C2 harness reconstructs healthy and historical-scale endpoints, instruments every mandatory tensor, executes a frozen one-factor bisection, and publishes a hash-bound provisional result for external review.

**Tech Stack:** Python 3.11+, pytest, Git, Windows PowerShell, WSL Ubuntu, PyTorch 2.7.0+cu128, CUDA, NumPy, JSON/CSV/SHA-256.

**Spec:** `docs/superpowers/specs/2026-09-05-jepa-peer-agent-continuity-design.md`

## Global Constraints

- Canonical dirty workspace `D:/Jepa project` is read-only for this work.
- Isolated worktree: `D:/jepa_peer_handoff_20260905` on `jepa-peer-handoff-20260905`.
- Base authority: `origin/main@76fe7d63efe81451ef0fae3ef3eaf116be14f6be`.
- No real F1, real training, DEV, SEALED, pathology, reader-validation, or reader-oracle expression.
- C2 uses synthetic expression only and may load authenticated u0 model bytes.
- Do not modify historical F1-B or conclusion-bearing result branches.
- No scientific threshold, F1 positivity rule, evidence-response estimand, program-role mapping, uncertainty definition, observation semantics, rare-target criterion, or production sampling weight is selected here.
- Every file write is staging-first/atomic where the file is resumable or authority-bearing.
- Every behavior change follows red-green TDD.
- Stop after C2 cause localization, regression verification, and external-review handoff.

---

### Task 1: Deterministic continuity checkpoint core

**Files:**
- Create: `scripts/agent/work_checkpoint.py`
- Create: `tests/test_work_checkpoint_v1.py`

**Interfaces:**
- Produces: `canonical_json_bytes(value) -> bytes`
- Produces: `sha256_file(path: Path) -> str`
- Produces: `build_checkpoint(repo, worktree, state) -> dict`
- Produces: `validate_checkpoint(checkpoint, repo, worktree) -> list[str]`
- Produces: `atomic_write_json(path, payload) -> None`
- CLI: `python scripts/agent/work_checkpoint.py build --repo ... --worktree ... --state ... --output ...`
- CLI: `python scripts/agent/work_checkpoint.py validate --repo ... --worktree ... --checkpoint ...`

- [ ] **Step 1: Write failing deterministic-roundtrip and semantic-root tests**

Create tests asserting identical logical input produces byte-identical canonical
JSON and semantic SHA, regardless of dictionary insertion order.

- [ ] **Step 2: Run the focused test and confirm RED**

Run: `python -m pytest tests/test_work_checkpoint_v1.py -q`

Expected: import/file-not-found failure for `scripts/agent/work_checkpoint.py`.

- [ ] **Step 3: Implement canonical serialization, hashes, and atomic JSON write**

The semantic root is SHA-256 over canonical UTF-8 JSON excluding only the
`checkpoint_semantic_sha256` field. Atomic publication writes a sibling staging
file, flushes and fsyncs it, then uses `os.replace`.

- [ ] **Step 4: Add failing identity and mutation tests**

Cover wrong HEAD, wrong branch, changed declared file bytes, missing authority,
unexpected dirty file, corrupted semantic root, and an allowed explicitly
declared dirty file.

- [ ] **Step 5: Run the mutation tests and confirm RED**

Run: `python -m pytest tests/test_work_checkpoint_v1.py -q`

Expected: new mutation cases fail because validation is incomplete.

- [ ] **Step 6: Implement fail-closed Git/file/authority validation**

Use non-mutating Git commands. Record tracked modifications and untracked files
separately. A continuation checkpoint passes only when actual state exactly
matches its declared state.

- [ ] **Step 7: Run focused tests and confirm GREEN**

Run: `python -m pytest tests/test_work_checkpoint_v1.py -q`

- [ ] **Step 8: Inspect diff and commit Task 1**

Run: `git diff --check` and `git status --porcelain`.

Commit: `feat: add deterministic peer work checkpoint core`

### Task 2: Restricted Claude peer bridge

**Files:**
- Create: `scripts/agent/claude_peer_bridge.py`
- Create: `tests/test_claude_peer_bridge_v1.py`

**Interfaces:**
- Produces: `discover_claude(explicit: Path | None) -> Path`
- Produces: `build_consult_command(executable, prompt, max_turns) -> list[str]`
- Produces: `consult(executable, prompt_path, output_dir, provenance) -> dict`
- CLI: `python scripts/agent/claude_peer_bridge.py consult --prompt ... --out ... --max-turns 1`

- [ ] **Step 1: Write failing discovery and safe-command tests**

Require explicit path or highest-version Antigravity
`anthropic.claude-code-*/resources/native-binary/claude.exe`. The consultation
command must contain non-interactive JSON output, restricted mode, no permission
prompts, strict MCP isolation, and an explicit turn bound. Reject write-enabled
or dangerously-skip-permissions arguments.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m pytest tests/test_claude_peer_bridge_v1.py -q`

- [ ] **Step 3: Implement discovery, command construction, and atomic review artifact**

Record executable/version/auth status, prompt SHA, repository HEAD, declared
input SHAs, exact argv, stdout/stderr/exit code, response SHA, and timestamps.
Never store authentication tokens.

- [ ] **Step 4: Add failing no-write and malformed-response tests**

Use a fake executable fixture. Assert project tree hashes are unchanged and
non-JSON/failed responses cannot become PASS review artifacts.

- [ ] **Step 5: Implement the fail-closed response boundary**

Only terminal exit zero plus valid JSON yields `CONSULTATION_COMPLETE`; this is
still advisory and cannot promote science.

- [ ] **Step 6: Run focused tests and confirm GREEN**

Run: `python -m pytest tests/test_claude_peer_bridge_v1.py -q`

- [ ] **Step 7: Run one harmless authenticated live smoke**

Prompt Claude to return exactly one JSON object identifying itself as an
advisory peer and confirming it performed no tool use. Use `max_turns=1` and no
project source inputs. Verify no worktree bytes outside the review output change.

- [ ] **Step 8: Inspect diff and commit Task 2**

Commit: `feat: add restricted Claude peer consultation bridge`

### Task 3: Persistent peer entry points and initial checkpoint

**Files:**
- Create: `CLAUDE.md`
- Create: `docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md`
- Create: `docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json`
- Generate: `docs/agent/CURRENT_WORK_CHECKPOINT.json`
- Generate: `docs/agent/CLAUDE_TAKEOVER.md`
- Create: `tests/test_peer_continuity_entrypoints_v1.py`

**Interfaces:**
- `CLAUDE.md` points to the JSON checkpoint and active plan.
- Both agents validate the JSON before acting.
- The state file is human-edited input; the checkpoint and takeover Markdown are
  deterministic generated outputs.

- [ ] **Step 1: Write failing entrypoint-consistency tests**

Require stable pointers, firewall booleans, equal-agent language, exact plan/spec
hashes, exact next action, and prohibition on self-promotion.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m pytest tests/test_peer_continuity_entrypoints_v1.py -q`

- [ ] **Step 3: Create stable entrypoints and active execution plan**

Record terminal `PASS_TO_IMPLEMENT_CONTINUITY_AND_C2_ONLY`. The exact next action
after continuity is the preserved C2 contract/harness. F1-B remains downstream.

- [ ] **Step 4: Generate and validate the initial checkpoint**

Run the Task-1 CLI. Validate in both Windows and WSL path forms against the same
underlying Git worktree.

- [ ] **Step 5: Simulate Codex-to-Claude and Claude-to-Codex takeover**

Change only provenance fields in the state input, regenerate, and prove the next
action and authority hashes remain identical. Restore the live owner to Codex.

- [ ] **Step 6: Run all continuity tests and confirm GREEN**

Run: `python -m pytest tests/test_work_checkpoint_v1.py tests/test_claude_peer_bridge_v1.py tests/test_peer_continuity_entrypoints_v1.py -q`

- [ ] **Step 7: Inspect diff and commit Task 3**

Commit: `feat: establish Codex Claude peer continuity entrypoints`

### Task 4: Freeze the synthetic C2 forensic contract

**Files:**
- Create: `docs/agent/C2_T1_GRADIENT_FORENSIC_CONTRACT_20260905.md`
- Create: `configs/v4/c2_t1_gradient_forensic_v1.json`
- Create: `tests/test_c2_t1_gradient_forensic_contract_v1.py`

**Interfaces:**
- Config defines endpoint IDs, seed list, factor order, token ladder, tensor-role
  registry, instrumentation stages, output schema, and fail-closed rules.
- It contains no biological endpoint or outcome-dependent threshold.

- [ ] **Step 1: Write failing contract-integrity tests**

Require synthetic-only input, authenticated u0/source hashes, exact 48 mandatory
tensor identities, instrumentation at post-backward/pre-unscale/post-unscale/
post-step, separate Adam moments, movement relative to pure decay, and the frozen
factor order.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m pytest tests/test_c2_t1_gradient_forensic_contract_v1.py -q`

- [ ] **Step 3: Write the prospective contract and config**

Endpoints:

- `HEALTHY_SIMPLIFIED`: batch 2, single backward, reduced token ladder start,
  FP32 loss inputs, existing synthetic seed.
- `HISTORICAL_SCALE`: vocabulary 41,238, effective batch 128, microbatch 8, four
  views, 64 backwards, fp16 autocast, GradScaler, checkpointing, historical loss
  division and mask/block semantics.

Frozen one-factor sequence:

1. FP32-forced versus autocast loss operands.
2. Tokens `512, 4096, 16384, 41238` with all otherwise compatible mechanics
   fixed.
3. Loss division and accumulation decomposition.
4. Teacher hidden-mask semantics.
5. Target-block construction and batch geometry.

The exact zero/nonzero tensor status is descriptive mechanical state, not a
tuned tolerance. No configuration may be added after inspecting results.

- [ ] **Step 4: Hash-bind the contract/config and run GREEN**

Run: `python -m pytest tests/test_c2_t1_gradient_forensic_contract_v1.py -q`

- [ ] **Step 5: Commit Task 4 before executing C2 outcomes**

Commit: `docs: freeze synthetic C2 gradient forensic contract`

### Task 5: Implement the instrumented C2 harness test-first

**Files:**
- Create: `scripts/v4/run_c2_t1_gradient_forensic_v1.py`
- Create: `tests/test_c2_t1_gradient_forensic_v1.py`

**Interfaces:**
- Produces: `mandatory_tensor_registry(model) -> list[TensorIdentity]`
- Produces: `gradient_snapshot(model, stage) -> dict`
- Produces: `moment_snapshot(optimizer, registry) -> dict`
- Produces: `movement_snapshot(before, after, optimizer_group) -> dict`
- Produces: `run_condition(config, condition_id, device) -> dict`
- Produces: `adjudicate_mechanical_transition(results, config) -> dict`
- CLI supports `--config`, `--out`, `--condition`, `--resume`, and `--device`.

- [ ] **Step 1: Write failing tensor-registry and snapshot tests**

Assert exact names/counts, missing-gradient distinction from zero, nonfinite
detection, separate moment states, and no pooled PASS.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m pytest tests/test_c2_t1_gradient_forensic_v1.py -q`

- [ ] **Step 3: Implement instrumentation only**

Reuse authenticated production classes; do not fork the attention mathematics.

- [ ] **Step 4: Add failing synthetic healthy/dead mutation fixtures**

Use tiny analytic modules to prove the adjudicator detects all-live, one-dead,
nonfinite, zero-second-moment, decay-only, and zero-baseline cases.

- [ ] **Step 5: Implement fail-closed condition/result identity**

Bind config, contract, source, checkpoint, environment, seed, condition, and
tensor registry. Write each condition atomically. Resume only exact matches.

- [ ] **Step 6: Run focused CPU tests and confirm GREEN**

Run: `python -m pytest tests/test_c2_t1_gradient_forensic_v1.py -q`

- [ ] **Step 7: Run a reduced CUDA dry run without interpreting results**

Use WSL `jepa-full104`, condition `HEALTHY_SIMPLIFIED`, and a temporary output.
Require finite loss, complete registry, and valid result identity.

- [ ] **Step 8: Inspect diff and commit Task 5**

Commit: `feat: add preserved C2 gradient forensic harness`

### Task 6: Execute the frozen C2 endpoints and bisection

**Files:**
- Generate under: `outputs/c2_t1_gradient_forensic_v1/`
- Generate: `C2_ENVIRONMENT.json`
- Generate: `C2_INVOCATION.json`
- Generate: `conditions/*.json`
- Generate: `C2_CAUSAL_ADJUDICATION.json`
- Generate: `C2_RESULT_MANIFEST.csv`
- Generate: `C2_PACKAGE_ROOT_SHA256.txt`

**Interfaces:**
- Every condition is resumable and identity-bound.
- The adjudication names only a condition supported by the frozen transition
  logic; otherwise terminal is `STOP_C2_CAUSE_NOT_LOCALIZED`.

- [ ] **Step 1: Authenticate environment and source/checkpoint hashes**

Record Python, PyTorch, CUDA, cuDNN, GPU, autocast/scaler settings, BLAS, OS, Git
HEAD, imported file paths, and raw/LF hash conventions.

- [ ] **Step 2: Run `HEALTHY_SIMPLIFIED`**

Require at least one finite nonzero gradient for every mandatory tensor and live
moments after the controlled step. Failure terminal:
`STOP_C2_HEALTHY_ENDPOINT_NOT_REPRODUCED`.

- [ ] **Step 3: Run `HISTORICAL_SCALE`**

Require reproduction of exact-zero gradients for all 48 mandatory tensors from
backward 1 onward while attention-output/FFN/predictor paths are live. Failure
terminal: `STOP_C2_HISTORICAL_ENDPOINT_NOT_REPRODUCED`.

- [ ] **Step 4: Execute the frozen factor sequence unchanged**

Do not skip later factors because an earlier result looks persuasive. Do not add
conditions after outcomes are visible.

- [ ] **Step 5: Run automatic causal adjudication**

Return `C2_GRADIENT_SEVERING_CONDITION_LOCALIZED` only if the frozen contrast
uniquely isolates a transition and repeated seeds agree. Otherwise return the
specific STOP and preserve all results.

- [ ] **Step 6: Rehash all outputs from disk and publish manifest/root**

No result is valid if output inventory differs from the expected condition set.

### Task 7: Add the observed-cause regression without changing T1

**Files:**
- Modify: `tests/test_c2_t1_gradient_forensic_v1.py`
- Create: `scripts/v4/validate_c2_t1_gradient_forensic_v1.py`
- Create: `tests/test_validate_c2_t1_gradient_forensic_v1.py`

**Interfaces:**
- Validator independently reads contract/results and recomputes the tensor-level
  transition without importing the production adjudicator.

- [ ] **Step 1: Write a failing regression for the uniquely adjudicated condition**

The test loads the frozen condition IDs from the result package. It asserts the
defective endpoint remains reproducible and the isolated counter-condition makes
all mandatory gradients finite/nonzero. It does not edit T1 production code.

- [ ] **Step 2: Run the regression and confirm RED against a deliberate mutation**

Mutate one stored tensor status in a temporary package and require rejection.

- [ ] **Step 3: Implement the independent validator**

Recompute manifests, source/input identity, per-stage tensor states, moment
states, movement, repeated-seed agreement, and the unique factor transition.

- [ ] **Step 4: Run focused and historical regression tests**

Run: `python -m pytest tests/test_c2_t1_gradient_forensic_v1.py tests/test_validate_c2_t1_gradient_forensic_v1.py tests/v4/test_stage81a3_ipb_jepa.py tests/v4/test_stage81a3_jepa_loss.py -q`

- [ ] **Step 5: Validate the real C2 package independently**

Expected terminal: `PASS_C2_MECHANICAL_CAUSE_INDEPENDENTLY_RECONSTRUCTED`, or a
specific STOP.

- [ ] **Step 6: Inspect all source/result diffs and commit Task 7**

Commit: `test: lock historical T1 gradient severing regression`

### Task 8: Close C2 historically and stop for external review

**Files:**
- Create: `docs/review_packets/c2_t1_gradient_forensic_20260905/C2_EXTERNAL_REVIEW_HANDOFF.md`
- Update: `docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json`
- Regenerate: `docs/agent/CURRENT_WORK_CHECKPOINT.json`
- Regenerate: `docs/agent/CLAUDE_TAKEOVER.md`

**Interfaces:**
- The handoff reports exact cause or exact STOP, changed files, tests, package
  hashes, and firewall status.
- It explicitly states T1 is historical and is neither repaired nor retrained.

- [ ] **Step 1: Write the evidence-tiered external-review handoff**

Separate authenticated historical checkpoint facts, reproduced synthetic facts,
causal bisection result, and remaining uncertainties.

- [ ] **Step 2: Run the complete authorized test set**

Run all continuity and C2 tests plus compile checks for new Python sources.

- [ ] **Step 3: Refresh the peer checkpoint**

Set the exact next action to external scientific review. F1-B implementation
remains unstarted and downstream.

- [ ] **Step 4: Commit the completed authorized unit**

Commit: `docs: hand off C2 mechanical closure for external review`

- [ ] **Step 5: STOP**

Do not amend DEC-013, modify T1, implement F1-B, run real F1, or start training in
this execution. Return the package to the user and ChatGPT external reviewer.
