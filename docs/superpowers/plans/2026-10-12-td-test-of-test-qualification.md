# TD Test-of-Test Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Target-Discovery-owned qualification layer that proves each biological gate behaves correctly on frozen external synthetic truth before that exact gate may reject a real biological claim.

**Architecture:** TD consumes synthetic challenge packages as immutable read-only external inputs. A fit-side TD executor sees only blinded observations; a separate TD qualification controller authenticates controller truth after execution and verifies expected PASS/FAIL/NOT_ESTIMABLE behavior. Synthetic generator/world code is never modified or imported as TD authority.

**Tech Stack:** Python 3; pytest; JSON/hash-bound receipts; existing `scripts/v5` target-discovery framework.

**Spec:** `docs/agent/TD_TEST_OF_TEST_QUALIFICATION_INTERFACE_20261012.md`

## Global Constraints

- All implementation writes remain in the Target Discovery lane.
- Do not modify synthetic generator code, synthetic contracts, synthetic result namespaces, or synthetic authority records.
- Historical #314 remains immutable and spent.
- PR #316 real-data execution remains OFF until exact gate logic passes test-of-test qualification.
- PR #313 real tournament execution remains OFF.
- Fit-side code must not receive controller truth, challenge identity semantics, or expected verdicts.
- `FAIL`, `PASS`, and `NOT_ESTIMABLE` remain distinct.
- Donor is the primary biological replication unit.
- A gate failure may reject only its exact frozen claim scope.
- No numerical threshold may be inferred from historical real TD outcomes.
- No target selection, TD60, Stage4 or training authority is created.

## Review Focus

1. A malicious or accidental synthetic package that exposes controller truth in the fit view must fail closed.
2. A package with valid-looking metadata but wrong content hashes must fail before any TD executor runs.
3. A true but underpowered rare program must route to `NOT_ESTIMABLE`, not `FAIL`.
4. A donor-restricted true program with many exact-zero donors must not be relabeled as technical or globally absent.
5. A fine-scale synthetic failure must not propagate into broad/mesoscale candidate elimination.

---

### Task 1: External synthetic package boundary validator

**Files:**
- Create: `scripts/v5/td_test_qualification_package_v1.py`
- Test: `tests/v5/test_td_test_qualification_package_v1.py`

**Interfaces:**
- Consumes: a TD-owned package-binding JSON that references a frozen external synthetic package by immutable hashes.
- Produces: `validate_external_package_binding(binding: Mapping) -> ValidatedExternalPackage`.

- [ ] **Step 1: Write the failing tests**

Add tests proving the validator:

- accepts a complete binding with package SHA-256, fit-view hashes, controller-truth hash, capability declarations and all authority flags false;
- rejects missing/invalid SHA-256 values;
- rejects any binding that grants world-generation, model-fit, target-selection, TD60, Stage4 or training authority;
- rejects a fit-view schema containing controller-only fields such as `R`, `pseudo_rare`, `challenge_kind`, `expected_status` or `controller_truth`;
- rejects duplicate challenge IDs or capability IDs;
- rejects a package whose declared content digest differs from the authenticated digest supplied by the caller.

- [ ] **Step 2: Run the test file and verify RED**

Run: `pytest -q tests/v5/test_td_test_qualification_package_v1.py`

Expected: FAIL because `td_test_qualification_package_v1` does not exist.

- [ ] **Step 3: Implement the minimal validator**

Create:

```python
@dataclass(frozen=True)
class ValidatedExternalPackage:
    package_id: str
    package_sha256: str
    fit_views: dict[str, str]
    controller_truth_sha256: str
    capabilities: dict[str, dict]


def validate_external_package_binding(binding: Mapping, *, authenticated_package_sha256: str) -> ValidatedExternalPackage:
    ...
```

The module validates identity/capability metadata only. It must not generate worlds, import synthetic generators, or inspect controller truth.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `pytest -q tests/v5/test_td_test_qualification_package_v1.py`

Expected: all tests PASS.

- [ ] **Step 5: Run the full project test command available in the execution environment**

Expected: no new failures. Any pre-existing failure must be reported explicitly.

- [ ] **Step 6: Commit**

Commit message: `feat(td): validate external synthetic qualification packages`

---

### Task 2: Gate qualification contract and controller receipt

**Files:**
- Create: `scripts/v5/td_test_of_test_controller_v1.py`
- Test: `tests/v5/test_td_test_of_test_controller_v1.py`

**Interfaces:**
- Consumes: `ValidatedExternalPackage`, exact gate identities, blinded TD gate outputs, and controller-side expected semantic outcomes.
- Produces: `GateQualificationReceipt` with `QUALIFIED`, `NOT_QUALIFIED`, or `INCOMPLETE` qualification status; never target authority.

- [ ] **Step 1: Write failing tests for exact identity binding**

Tests must reject any mismatch in:

- `qualified_gate_executor_sha256`;
- `estimand_sha256`;
- `decision_rule_sha256`;
- package SHA-256;
- challenge set/order.

- [ ] **Step 2: Write failing tests for semantic classes**

Use minimal controller fixtures showing:

- supported positive truth + gate PASS -> qualification case PASS;
- supported positive truth + gate FAIL -> test sensitivity failure;
- biological-null or technical-twin truth + gate PASS -> specificity failure;
- underidentified positive truth + gate `NOT_ESTIMABLE` -> correct;
- underidentified positive truth + gate FAIL -> qualification failure;
- expected PASS/FAIL/NOT_ESTIMABLE may not be read by fit-side input structures.

- [ ] **Step 3: Verify RED**

Run: `pytest -q tests/v5/test_td_test_of_test_controller_v1.py`

Expected: FAIL because controller module does not exist.

- [ ] **Step 4: Implement minimal controller**

Create:

```python
@dataclass(frozen=True)
class GateQualificationReceipt:
    candidate_id: str
    gate_id: str
    executor_sha256: str
    estimand_sha256: str
    decision_rule_sha256: str
    package_sha256: str
    challenge_results: tuple[dict, ...]
    qualification_status: str
    failure_scope: str
    authority: dict[str, bool]


def adjudicate_gate_qualification(... ) -> GateQualificationReceipt:
    ...
```

Qualification status rules:

- any required semantic mismatch -> `NOT_QUALIFIED`;
- any missing required challenge/capability -> `INCOMPLETE`;
- all required challenge semantics correct -> `QUALIFIED`.

No aggregate score may rescue a hard semantic mismatch.

- [ ] **Step 5: Verify GREEN and full-suite spillover**

Run focused tests, then the full available suite.

- [ ] **Step 6: Commit**

Commit message: `feat(td): add synthetic test-of-test controller`

---

### Task 3: TD57C-successor estimability router

**Files:**
- Create: `scripts/v5/td_relational_successor_estimability_v1.py`
- Test: `tests/v5/test_td_relational_successor_estimability_v1.py`

**Interfaces:**
- Consumes: donor/source cell-support counts for a frozen scale/program stratum.
- Produces: `PASS_TO_TEST` or `NOT_ESTIMABLE` routing only. It does not determine biological PASS/FAIL.

- [ ] **Step 1: Write failing tests**

Tests must prove:

- insufficient neighborhood support -> `NOT_ESTIMABLE`;
- insufficient active donors for the explicit hypothesis -> `NOT_ESTIMABLE`;
- donors known by truth/definition to have zero program prevalence are not counted as failed biological replications;
- source-specific missing support produces source-specific `NOT_ESTIMABLE`, not global FAIL;
- sufficient support routes onward without manufacturing a biological verdict.

The exact numeric support minima must come from the already-approved/frozen PR #316 design or a separately prospectively reviewed amendment; do not infer them from #314 outcomes.

- [ ] **Step 2: Verify RED**

Run the focused test file and confirm missing-module failure.

- [ ] **Step 3: Implement minimal routing logic**

Expose one pure function whose return object records support counts and the reason for `NOT_ESTIMABLE`.

- [ ] **Step 4: Verify GREEN and full suite**

- [ ] **Step 5: Commit**

Commit message: `feat(td): add relational successor estimability routing`

---

### Task 4: TD57C-successor scale/rare test executor

**Files:**
- Create: `scripts/v5/td_relational_successor_gate_v1.py`
- Test: `tests/v5/test_td_relational_successor_gate_v1.py`

**Interfaces:**
- Consumes: blinded molecular views, donor/source IDs, support masks, prospectively frozen scale list, rare-state membership only when that membership is lawfully defined independently of the relational outcome, and the Task-3 estimability router.
- Produces: raw scale/program-specific sufficient statistics and scoped status; no candidate-level aggregation.

- [ ] **Step 1: Write failing unit tests using deterministic TD-owned fixtures**

Fixtures should encode only the minimum mathematical behaviors needed to test the executor:

- broad/mesoscale recurrence;
- fine recurrent recurrence;
- multiple disconnected local islands;
- no relational structure;
- wrong-cell/technical structure;
- underpowered support.

These unit fixtures are TD test fixtures, not new synthetic-lane scientific worlds.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement the frozen scale-response logic**

Requirements:

- no early stopping;
- every frozen scale is evaluated when estimable;
- source results remain separate;
- donor is the replication unit;
- fine and mesoscale results remain separate;
- rare-conditioned and common/global results remain separate;
- disconnected rare islands are not forced into one connected global neighborhood;
- matched wrong-cell/technical controls are verdict-bearing;
- one stratum FAIL cannot automatically erase another stratum PASS.

Do not encode #314 historical margins as thresholds.

- [ ] **Step 4: Verify GREEN and full suite**

- [ ] **Step 5: Commit**

Commit message: `feat(td): implement scoped relational successor gate`

---

### Task 5: External known-truth qualification adapter for the relational gate

**Files:**
- Create: `scripts/v5/td_relational_successor_synthetic_adapter_v1.py`
- Test: `tests/v5/test_td_relational_successor_synthetic_adapter_v1.py`

**Interfaces:**
- Consumes: Task-1 validated package plus externally supplied capabilities:
  - `REL_BROAD_MESO_POSITIVE`
  - `REL_FINE_RECURRENT_POSITIVE`
  - `REL_RARE_LOCAL_ISLAND_POSITIVE`
  - `REL_MULTI_ISLAND_POSITIVE`
  - `REL_DONOR_RESTRICTED_POSITIVE`
  - `REL_SOURCE_VISIBILITY_STRESS`
  - `REL_TECHNICAL_TWIN_NEGATIVE`
  - `REL_NULL_NEGATIVE`
  - `REL_UNDERPOWERED_POSITIVE`
- Produces: blinded executor inputs and a separate controller challenge map.

- [ ] **Step 1: Write failing tests for lane separation**

Tests must fail if the adapter:

- imports or calls a synthetic generator;
- accepts mutable/generated-on-demand worlds;
- exposes challenge capability names or expected outcomes to the fit-side executor;
- puts controller truth fields into the fit view.

- [ ] **Step 2: Write failing tests for complete capability coverage**

Missing any mandatory capability must result in `INCOMPLETE`, never implicit qualification.

- [ ] **Step 3: Verify RED**

- [ ] **Step 4: Implement read-only adapter**

The adapter should only translate authenticated external arrays/metadata into the TD executor input schema and keep controller metadata physically/logically separate.

- [ ] **Step 5: Verify GREEN and full suite**

- [ ] **Step 6: Commit**

Commit message: `feat(td): bind external relational truth read-only`

---

### Task 6: Require synthetic gate qualification in PR #313 readiness

**Files:**
- Modify: `results/target_discovery/real_tournament/TD_REAL_GATE_EXECUTOR_READINESS_V1.json` only on a dedicated prospective successor branch stacked from the current #313 executor framework, not on #313 itself until explicit supersession review.
- Modify/Create as required: TD-side readiness validator in `scripts/v5/`.
- Test: corresponding `tests/v5/` readiness tests.

**Interfaces:**
- Consumes: exact gate qualification receipts from Task 2.
- Produces: real-execution readiness only when every required candidate×gate role has both callable code identity and successful test-of-test qualification.

- [ ] **Step 1: Write failing readiness tests**

Required behavior:

- callable executor without synthetic qualification -> BLOCKED;
- synthetic qualification for a different executor/estimand/rule hash -> BLOCKED;
- incomplete capability suite -> BLOCKED;
- qualified exact identities -> eligible for the next outcome-blind QUALIFY step, but still no execution authority.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement minimal readiness extension**

Do not alter existing candidate aggregation or one-shot execution machinery.

- [ ] **Step 4: Verify GREEN and full suite**

- [ ] **Step 5: Commit**

Commit message: `feat(td): require test-of-test evidence for gate readiness`

---

### Task 7: Freeze and execute the external synthetic qualification only after package delivery

**Files:**
- Create under TD only: `results/target_discovery/test_qualification/<gate-version>/...`
- No writes to synthetic-lane paths.

**Interfaces:**
- Consumes: externally frozen synthetic package identities supplied by the other lane.
- Produces: hash-bound TD qualification receipts.

- [ ] **Step 1: Authenticate package bytes/hashes before creating an execution namespace**

- [ ] **Step 2: Freeze exact TD executor/estimand/rule identities and expected challenge semantics**

- [ ] **Step 3: Run fit-side TD executor without controller truth**

- [ ] **Step 4: Open controller truth only in the TD qualification controller**

- [ ] **Step 5: Produce one immutable qualification receipt per gate**

- [ ] **Step 6: Stop for independent audit**

No real #316/#313 biological execution may follow automatically.

---

## Self-review result

The plan covers the current identified gap without changing synthetic-lane science. It deliberately separates (a) package authentication, (b) gate test qualification, (c) estimability, (d) biological gate execution, and (e) #313 readiness. The external relational truth package remains an upstream dependency owned by the synthetic lane; absence of that package blocks only the known-truth qualification run, not TD-side interface/code development.
