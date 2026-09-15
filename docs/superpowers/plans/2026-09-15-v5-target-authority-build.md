# V5 Target Authority and Current Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the current-V5 authority and bounded qualification path around the already-repaired teacher/student/EMA mechanics without inheriting historical V4/V21/T0 target semantics, geometry, receipt schemas, masking, weighting, seeds, or EMA constants.

**Architecture:** Preserve proven mechanics (gradient/optimizer/EMA chronology, resident optimizer guard pattern, current protected-registry pattern, atomic checkpoint pattern) while replacing scientific/numerical authority with explicit current-V5 schemas. Build a new current-V5 path rather than unlocking or widening the historical V4 `production_update`/legacy target-receipt path. Keep all work fail-closed and qualification-only until a separate production-training authorization exists.

**Tech Stack:** Python 3, PyTorch, dataclasses, hashlib/json canonical receipts, pytest, existing `sea_ad_jepa.v5` authority modules.

**Spec:** `docs/agent/JEPA_NEW_CHAT_INSTRUCTIONS_20260915_V5_TARGET_AUTHORITY_BUILD.md`, `docs/agent/V5_TEACHER_STUDENT_EMA_ARCHITECTURE_DRAFT_20260915.md`, `docs/agent/V5_TARGET_IDENTITY_SHORTCUT_AUDIT_SPEC_DRAFT_20260915.md`, and `docs/agent/V5_ACCIDENTAL_CARRYOVER_LEDGER_20260915.md`.

## Global Constraints

- `TRAINING_OFF` throughout this plan.
- `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION` throughout this plan.
- Do not inspect protected/pathology/DEV/SEALED outcomes, D_private, D_obs outcomes or TD60.
- Do not widen `qualified_teacher_target_receipt_v1.py`; create a distinct current-V5 schema.
- Do not use historical `v4.teacher_student_runtime.PRODUCTION_CONFIG` as current authority.
- Do not call historical V4 `production_update` from the current-V5 runtime.
- Do not hard-code `160`, `4 heads`, `6 blocks`, `128`, `8`, `4 views`, `.40`, `16 target blocks`, `.996`, historical LR/betas/weight decay, or historical seeds as current-V5 defaults.
- Do not hard-code a 48-tensor protected registry; consume `ProductionProtectedRegistryAuthorityV1`.
- Do not allow visibility channels into the primary molecular path unless a separately frozen representation authority explicitly permits them.
- Scientific cell weights must be externally supplied from a frozen base-training estimand authority; packing must not change them.
- Every new authority object must default to `training_authorized=False` or contain no training-authorization field at all.
- Target-address conditioning must not obtain predictor gradients through the online encoder's trainable gene-identity table unless a future explicit target-identity authority permits that variant.
- Before each task, re-fetch live branch heads and classify the task `OPEN` or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`; stop if it became `ALREADY_AUDITED` elsewhere.

---

## File Structure

Create focused successors rather than mutating forensic/historical modules in place:

- `src/sea_ad_jepa/v5/critical_test_execution_authority_v1.py` — geometry-neutral list/digest of required critical tests.
- `src/sea_ad_jepa/v5/trainer_preexecution_contract_v3.py` — current-V5 preexecution authority consuming the current protected registry and critical-test authority.
- `src/sea_ad_jepa/v5/current_teacher_target_receipt_v1.py` — distinct current-V5 target/authority receipt schema.
- `src/sea_ad_jepa/v5/qualified_optimizer_guard_v2.py` — resident exactly-once optimizer guard bound to the new receipt.
- `src/sea_ad_jepa/v5/teacher_target_semantics_authority_v1.py` — explicit teacher-target semantic contract; no numerical model geometry defaults.
- `src/sea_ad_jepa/v5/target_address_query_v1.py` — frozen/separate target-address codebook interface and hash binding.
- `src/sea_ad_jepa/v5/masking_authority_v1.py` — explicit masking-policy receipt/schema; no default mask fraction or block count.
- `src/sea_ad_jepa/v5/masking_audit_metrics_v1.py` — outcome-blind shortcut/coverage metrics.
- `src/sea_ad_jepa/v5/ema_presentation_v1.py` — presentation-normalized EMA momentum helper.
- `src/sea_ad_jepa/v5/current_teacher_student_runtime_v1.py` — bounded current-V5 qualification runtime consuming only explicit authorities.
- `tests/test_v5_no_historical_carryover_v1.py` — static/behavioral firewall against accidental historical carryover.
- One focused pytest module for each new source module.

Historical modules remain available for forensic/mechanics replay and are not renamed or deleted by this plan.

---

### Task 1: Add an executable accidental-carryover firewall

**Files:**
- Create: `tests/test_v5_no_historical_carryover_v1.py`

**Interfaces:**
- Consumes: source text for future current-V5 successor modules.
- Produces: a reusable test helper `assert_no_forbidden_current_v5_carryover(source_text: str) -> None`.

- [ ] **Step 1: Write the failing test helper and tests before successor modules exist**

```python
from __future__ import annotations

from pathlib import Path

FORBIDDEN_SNIPPETS = (
    "PRODUCTION_CONFIG",
    "v4.teacher_student_runtime import production_update",
    "ema_momentum: float = 0.996",
    "mask_fraction: float = 0.40",
    "target_blocks: int = 16",
    "protected registry must contain exactly 48",
    "HISTORICAL_128X8_CORRECTED_UPDATE_REGRESSION",
)


def assert_no_forbidden_current_v5_carryover(source_text: str) -> None:
    hits = [item for item in FORBIDDEN_SNIPPETS if item in source_text]
    assert not hits, f"historical carryover found: {hits}"


def test_current_runtime_source_has_no_historical_defaults() -> None:
    path = Path("src/sea_ad_jepa/v5/current_teacher_student_runtime_v1.py")
    assert path.exists(), "current V5 runtime successor is not implemented yet"
    assert_no_forbidden_current_v5_carryover(path.read_text(encoding="utf-8"))


def test_preexecution_v3_has_no_48_or_128x8_carryover() -> None:
    path = Path("src/sea_ad_jepa/v5/trainer_preexecution_contract_v3.py")
    assert path.exists(), "current V5 preexecution successor is not implemented yet"
    assert_no_forbidden_current_v5_carryover(path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the tests and verify they fail because the successor files do not exist**

Run:

```bash
pytest tests/test_v5_no_historical_carryover_v1.py -q
```

Expected: FAIL on missing successor files. A skip is not acceptable.

- [ ] **Step 3: Keep the firewall red while Tasks 2-8 build the successor modules**

Do not weaken `FORBIDDEN_SNIPPETS` to get a green test. If an unavoidable historical string is required only in a negative test fixture, keep it outside production successor source and document why.

- [ ] **Step 4: Commit the red test**

```bash
git add tests/test_v5_no_historical_carryover_v1.py
git commit -m "test(v5): add historical carryover firewall"
```

---

### Task 2: Replace fixed critical-test vocabulary with explicit current authority

**Files:**
- Create: `src/sea_ad_jepa/v5/critical_test_execution_authority_v1.py`
- Create: `tests/test_v5_critical_test_execution_authority_v1.py`

**Interfaces:**
- Produces: `CriticalTestExecutionAuthorityV1(required_test_ids: tuple[str, ...], authority_id: str, training_authorized: bool = False)`.
- Produces: `validate_critical_test_execution_v1(authority, statuses) -> dict[str, object]`.
- Consumed by: Task 3 preexecution contract.

- [ ] **Step 1: Write failing tests for exact externally supplied test IDs**

```python
import pytest

from sea_ad_jepa.v5.critical_test_execution_authority_v1 import (
    CriticalTestExecutionAuthorityV1,
    validate_critical_test_execution_v1,
)


def test_current_critical_tests_are_explicit_not_historical_constants() -> None:
    authority = CriticalTestExecutionAuthorityV1(
        authority_id="current-v5-mechanics-suite",
        required_test_ids=(
            "CURRENT_PROTECTED_REGISTRY_GRADIENT_GATE",
            "CURRENT_ADAM_MOMENT_GATE",
            "CURRENT_PARAMETER_MOTION_BEYOND_DECAY",
            "CURRENT_EMA_AFTER_PROVED_STEP",
            "CURRENT_HARDWARE_PACKING_SCIENCE_PARITY",
        ),
    )
    statuses = {name: "EXECUTED_PASS" for name in authority.required_test_ids}
    out = validate_critical_test_execution_v1(authority, statuses)
    assert out["executed_pass"] == 5
    assert out["skipped_critical"] == 0


def test_missing_or_skipped_current_critical_test_fails() -> None:
    authority = CriticalTestExecutionAuthorityV1(
        authority_id="current-v5-mechanics-suite",
        required_test_ids=("CURRENT_EMA_AFTER_PROVED_STEP",),
    )
    with pytest.raises(RuntimeError, match="critical tests not executed-pass"):
        validate_critical_test_execution_v1(authority, {"CURRENT_EMA_AFTER_PROVED_STEP": "SKIPPED"})
```

- [ ] **Step 2: Run tests to verify import failure**

```bash
pytest tests/test_v5_critical_test_execution_authority_v1.py -q
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement the minimal geometry-neutral authority**

```python
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping


@dataclass(frozen=True)
class CriticalTestExecutionAuthorityV1:
    authority_id: str
    required_test_ids: tuple[str, ...]
    training_authorized: bool = False

    def validate(self) -> None:
        if not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if not self.required_test_ids or len(set(self.required_test_ids)) != len(self.required_test_ids):
            raise ValueError("required_test_ids must be nonempty and unique")
        if any(not isinstance(x, str) or not x.strip() for x in self.required_test_ids):
            raise ValueError("required test IDs must be nonempty strings")
        if self.training_authorized is not False:
            raise ValueError("critical-test authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        payload = json.dumps(
            {
                "schema": "V5_CRITICAL_TEST_EXECUTION_AUTHORITY_V1",
                "authority_id": self.authority_id,
                "required_test_ids": list(self.required_test_ids),
                "training_authorized": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def validate_critical_test_execution_v1(
    authority: CriticalTestExecutionAuthorityV1,
    statuses: Mapping[str, object],
) -> dict[str, object]:
    authority.validate()
    failures = {
        test_id: statuses.get(test_id, "MISSING")
        for test_id in authority.required_test_ids
        if statuses.get(test_id) != "EXECUTED_PASS"
    }
    if failures:
        raise RuntimeError(f"critical tests not executed-pass: {failures}")
    extras = sorted(set(statuses) - set(authority.required_test_ids))
    return {
        "executed_pass": len(authority.required_test_ids),
        "skipped_critical": 0,
        "extra_status_ids": extras,
        "authority_sha256": authority.canonical_digest(),
    }
```

- [ ] **Step 4: Run focused tests**

```bash
pytest tests/test_v5_critical_test_execution_authority_v1.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/sea_ad_jepa/v5/critical_test_execution_authority_v1.py tests/test_v5_critical_test_execution_authority_v1.py
git commit -m "feat(v5): add geometry-neutral critical-test authority"
```

---

### Task 3: Create current-V5 preexecution contract V3

**Files:**
- Create: `src/sea_ad_jepa/v5/trainer_preexecution_contract_v3.py`
- Create: `tests/test_v5_trainer_preexecution_contract_v3.py`

**Interfaces:**
- Consumes: `ProductionProtectedRegistryAuthorityV1`, `CriticalTestExecutionAuthorityV1`.
- Produces: `TrainerPreexecutionAuthorityV3` and `validate_current_v5_preexecution_v3(...)`.
- Must not contain a six-block/48-tensor/128x8 constant.

- [ ] **Step 1: Write failing tests using a two-block synthetic registry**

```python
from sea_ad_jepa.v5.production_protected_registry_authority_v1 import (
    PROTECTED_PARAMETERS,
    PROTECTED_ROLES,
    ProductionProtectedRegistryAuthorityV1,
)
from sea_ad_jepa.v5.critical_test_execution_authority_v1 import CriticalTestExecutionAuthorityV1
from sea_ad_jepa.v5.trainer_preexecution_contract_v3 import TrainerPreexecutionAuthorityV3


def make_registry(depth: int) -> ProductionProtectedRegistryAuthorityV1:
    rows = []
    for block in range(depth):
        for role in PROTECTED_ROLES:
            for parameter in PROTECTED_PARAMETERS:
                rows.append(
                    {
                        "block_index": block,
                        "role": role,
                        "parameter": parameter,
                        "tensor_name": f"blocks.{block}.{role}.{parameter}",
                    }
                )
    return ProductionProtectedRegistryAuthorityV1(
        authority_id=f"depth-{depth}", model_depth=depth, records=rows
    )


def test_preexecution_v3_accepts_non_six_block_registry() -> None:
    registry = make_registry(2)
    tests = CriticalTestExecutionAuthorityV1(
        authority_id="suite",
        required_test_ids=("CURRENT_PROTECTED_REGISTRY_GRADIENT_GATE",),
    )
    authority = TrainerPreexecutionAuthorityV3(
        authority_roots={"design_freeze_sha256": "a" * 64},
        protected_registry_authority_sha256=registry.canonical_digest(),
        critical_test_authority_sha256=tests.canonical_digest(),
        presentation_horizon=100,
        ema_half_life_presentations=25,
        effective_base_cells_per_update=8,
        masked_views_per_base_cell=2,
        relational_training_active=False,
        optimizer_started=False,
    )
    authority.validate()
```

- [ ] **Step 2: Run test to verify import failure**

```bash
pytest tests/test_v5_trainer_preexecution_contract_v3.py -q
```

Expected: FAIL because V3 does not exist.

- [ ] **Step 3: Implement V3 with explicit roots and no fixed registry/test vocabulary**

Use a frozen dataclass with:

```python
@dataclass(frozen=True)
class TrainerPreexecutionAuthorityV3:
    authority_roots: Mapping[str, str]
    protected_registry_authority_sha256: str
    critical_test_authority_sha256: str
    presentation_horizon: int
    ema_half_life_presentations: int
    effective_base_cells_per_update: int
    masked_views_per_base_cell: int
    relational_training_active: bool
    optimizer_started: bool
    training_authorized: bool = False
```

Validation requirements:

- every SHA field is lowercase 64-hex;
- `authority_roots` is nonempty, exact caller-supplied mapping with no built-in historical names required by the module;
- numeric schedule fields are explicit positive integers;
- `relational_training_active is False` for the initial base-learning authority;
- `optimizer_started is False`;
- `training_authorized is False`;
- no `48`, `range(6)`, `PROTECTED_48`, `128X8` or historical test ID is present in source.

- [ ] **Step 4: Run V3 tests plus carryover firewall**

```bash
pytest tests/test_v5_trainer_preexecution_contract_v3.py tests/test_v5_no_historical_carryover_v1.py -q
```

Expected: V3 tests PASS; carryover test for the not-yet-created runtime may remain red until Task 9, but the preexecution assertion must pass.

- [ ] **Step 5: Commit**

```bash
git add src/sea_ad_jepa/v5/trainer_preexecution_contract_v3.py tests/test_v5_trainer_preexecution_contract_v3.py
git commit -m "feat(v5): add geometry-neutral preexecution authority v3"
```

---

### Task 4: Create a distinct current-V5 teacher-target receipt schema

**Files:**
- Create: `src/sea_ad_jepa/v5/current_teacher_target_receipt_v1.py`
- Create: `tests/test_v5_current_teacher_target_receipt_v1.py`

**Interfaces:**
- Produces: `seal_current_teacher_target_receipt_v1(...) -> dict[str, object]`.
- Produces: `validate_current_teacher_target_receipt_v1(...) -> dict[str, object]`.
- Consumed by: Task 5 optimizer guard and Task 9 runtime.

- [ ] **Step 1: Write tests proving legacy receipts cannot pass**

```python
import pytest

from sea_ad_jepa.v5.current_teacher_target_receipt_v1 import (
    CURRENT_V5_TARGET_RECEIPT_KIND,
    seal_current_teacher_target_receipt_v1,
    validate_current_teacher_target_receipt_v1,
)


def roots() -> dict[str, str]:
    names = (
        "full104_substrate_sha256",
        "representation_authority_sha256",
        "base_training_estimand_sha256",
        "teacher_target_semantics_sha256",
        "target_address_query_authority_sha256",
        "masking_authority_sha256",
        "model_geometry_authority_sha256",
        "schedule_authority_sha256",
        "ema_authority_sha256",
        "anti_cheat_authority_sha256",
        "preexecution_authority_sha256",
        "runtime_source_sha256",
    )
    return {name: f"{index + 1:064x}"[-64:] for index, name in enumerate(names)}


def test_current_receipt_is_current_kind_and_cannot_authorize_training() -> None:
    receipt = seal_current_teacher_target_receipt_v1(
        target_package_root="f" * 64,
        authority_roots=roots(),
    )
    assert receipt["kind"] == CURRENT_V5_TARGET_RECEIPT_KIND
    assert receipt["production_training_authorized"] is False
    out = validate_current_teacher_target_receipt_v1(
        receipt,
        expected_target_package_root="f" * 64,
        expected_authority_roots=roots(),
    )
    assert out["current_v5_teacher_authority"] is True
    assert out["production_training_authorized"] is False


def test_legacy_kind_is_rejected() -> None:
    legacy = {
        "kind": "v5_qualified_teacher_target_receipt_v1",
        "production_training_authorized": False,
    }
    with pytest.raises(RuntimeError, match="current V5 teacher-target receipt"):
        validate_current_teacher_target_receipt_v1(
            legacy,
            expected_target_package_root="f" * 64,
            expected_authority_roots=roots(),
        )
```

- [ ] **Step 2: Run tests to verify import failure**

```bash
pytest tests/test_v5_current_teacher_target_receipt_v1.py -q
```

Expected: FAIL because module is absent.

- [ ] **Step 3: Implement exact-field current receipt**

Use a new kind string:

```python
CURRENT_V5_TARGET_RECEIPT_KIND = "v5_current_teacher_target_receipt_v1"
```

The sealed body must contain only:

- `kind`;
- `authority_scope = "CURRENT_V5_DATASET_DERIVED_TEACHER_TARGET"`;
- `target_package_root`;
- exact `authority_roots` mapping supplied by caller;
- `production_training_authorized = False`;
- canonical `receipt_digest`.

The module must know nothing about 46 development donors, V21, T0, historical estimator IDs or historical package roots.

- [ ] **Step 4: Run focused tests**

```bash
pytest tests/test_v5_current_teacher_target_receipt_v1.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/sea_ad_jepa/v5/current_teacher_target_receipt_v1.py tests/test_v5_current_teacher_target_receipt_v1.py
git commit -m "feat(v5): add distinct current teacher-target receipt"
```

---

### Task 5: Rebind the resident optimizer guard to the current receipt

**Files:**
- Create: `src/sea_ad_jepa/v5/qualified_optimizer_guard_v2.py`
- Create: `tests/test_v5_qualified_optimizer_guard_v2.py`

**Interfaces:**
- Consumes: `validate_current_teacher_target_receipt_v1`.
- Produces: `QualifiedOptimizerStepGuardV2` and `install_qualified_optimizer_guard_v2(...)`.

- [ ] **Step 1: Write tests for deny-by-default, exact cursor consumption and legacy rejection**

Reuse a small `torch.optim.AdamW` fixture. Required cases:

```python
def test_direct_unarmed_optimizer_step_is_rejected(): ...
def test_armed_cursor_must_be_presented_exactly_once(): ...
def test_uncompleted_amp_authorization_can_be_disarmed_not_carried_forward(): ...
def test_installed_guard_rejects_receipt_digest_change(): ...
def test_legacy_receipt_cannot_install_v2_guard(): ...
```

Each case must assert a raised `RuntimeError`; no skip markers.

- [ ] **Step 2: Run tests and verify failure because V2 is absent**

```bash
pytest tests/test_v5_qualified_optimizer_guard_v2.py -q
```

- [ ] **Step 3: Port only the guard mechanics from V1**

Keep:

- resident optimizer pre-hook/post-hook;
- private cursor kwarg;
- one armed cursor at a time;
- exactly-once consumption;
- explicit disarm for uncompleted AMP step;
- receipt digest mismatch rejection.

Replace only the semantic validator with `validate_current_teacher_target_receipt_v1`. Do not import `qualified_teacher_target_receipt_v1.py`.

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_v5_qualified_optimizer_guard_v2.py tests/test_v5_current_teacher_target_receipt_v1.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/sea_ad_jepa/v5/qualified_optimizer_guard_v2.py tests/test_v5_qualified_optimizer_guard_v2.py
git commit -m "feat(v5): bind optimizer guard to current target receipt"
```

---

### Task 6: Freeze target-address conditioning away from online trainable identity

**Design gate:** Execute this task only after the target-identity design decision is explicitly approved. The leading candidate is fixed/separate address conditioning; this plan does not make the empirical identity-shortcut result for you.

**Files:**
- Create: `src/sea_ad_jepa/v5/target_address_query_v1.py`
- Create: `tests/test_v5_target_address_query_v1.py`

**Interfaces:**
- Produces: `FrozenTargetAddressCodebook(nn.Module)`.
- Constructor: `FrozenTargetAddressCodebook(codebook: torch.Tensor, authority_sha256: str)`.
- Method: `forward(target_indices: torch.Tensor) -> torch.Tensor`.
- The codebook is a registered buffer, never an `nn.Parameter`.

- [ ] **Step 1: Write tests proving no trainable target-address parameter exists**

```python
import torch

from sea_ad_jepa.v5.target_address_query_v1 import FrozenTargetAddressCodebook


def test_target_address_codebook_is_buffer_not_parameter() -> None:
    code = torch.randn(11, 7)
    module = FrozenTargetAddressCodebook(code, authority_sha256="a" * 64)
    assert dict(module.named_parameters()) == {}
    assert "codebook" in dict(module.named_buffers())
    assert module.codebook.requires_grad is False


def test_lookup_preserves_shape_and_never_requires_grad() -> None:
    code = torch.arange(35, dtype=torch.float32).reshape(5, 7)
    module = FrozenTargetAddressCodebook(code, authority_sha256="b" * 64)
    out = module(torch.tensor([[0, 2], [4, 1]], dtype=torch.long))
    assert out.shape == (2, 2, 7)
    assert out.requires_grad is False
```

- [ ] **Step 2: Run tests to verify import failure**

```bash
pytest tests/test_v5_target_address_query_v1.py -q
```

- [ ] **Step 3: Implement the minimal fixed codebook**

Requirements:

- clone/detach caller tensor in constructor;
- require finite floating codebook `[vocabulary, address_width]`;
- register it as `self.register_buffer("codebook", codebook.detach().clone(), persistent=True)`;
- validate lower-case 64-hex authority digest;
- validate index dtype/range;
- never create a target-address trainable parameter.

Do **not** invent a production codebook generator in this task. The codebook itself is an authority-bound input; its construction/freeze is a separate design artifact.

- [ ] **Step 4: Add a source-level test that the current successor predictor/runtime never passes `online.tokenizer.gene_identity` as target query authority**

Add to `tests/test_v5_no_historical_carryover_v1.py` after Task 9 source exists:

```python
assert "online.tokenizer.gene_identity" not in runtime_source
```

- [ ] **Step 5: Run tests and commit**

```bash
pytest tests/test_v5_target_address_query_v1.py -q
git add src/sea_ad_jepa/v5/target_address_query_v1.py tests/test_v5_target_address_query_v1.py tests/test_v5_no_historical_carryover_v1.py
git commit -m "feat(v5): add frozen target-address query authority"
```

---

### Task 7: Add outcome-blind masking authority and audit metrics

**Files:**
- Create: `src/sea_ad_jepa/v5/masking_authority_v1.py`
- Create: `src/sea_ad_jepa/v5/masking_audit_metrics_v1.py`
- Create: `tests/test_v5_masking_authority_v1.py`
- Create: `tests/test_v5_masking_audit_metrics_v1.py`

**Interfaces:**
- `MaskingAuthorityV1` stores explicit policy ID, dependency-source authority ID, random/structural mixture numerators/denominators or another exact caller-supplied representation, target evidence budget authority ID, RNG authority ID, and `training_authorized=False`.
- Metrics functions consume masks/support/dependency edges but no biological/protected outcomes.

- [ ] **Step 1: Write failing tests that prove there are no default mask fractions/block counts**

```python
import inspect

from sea_ad_jepa.v5.masking_authority_v1 import MaskingAuthorityV1


def test_masking_authority_requires_every_policy_input_explicitly() -> None:
    sig = inspect.signature(MaskingAuthorityV1)
    for name, param in sig.parameters.items():
        if name == "training_authorized":
            continue
        assert param.default is inspect._empty
```

- [ ] **Step 2: Write metric tests on a tiny dependency graph**

For a 6-address fixture with dependency edges `(0,1)`, `(2,3)`, masks must report exact correlated-partner exposure, per-address coverage counts, Gini/concentration or an explicitly defined normalized concentration metric, and deterministic replay equality.

Example expectation:

```python
assert correlated_partner_exposure(mask, edges) == 0.5
assert address_coverage(masks, vocabulary_size=6).tolist() == [1, 1, 2, 0, 0, 0]
```

Use fixture values that make these assertions exact.

- [ ] **Step 3: Run tests and verify modules are absent**

```bash
pytest tests/test_v5_masking_authority_v1.py tests/test_v5_masking_audit_metrics_v1.py -q
```

- [ ] **Step 4: Implement pure authority/metric modules**

No FULL104 access, no D_shared, no protected outcomes, no structural ratio chosen from results.

- [ ] **Step 5: Run tests and commit**

```bash
pytest tests/test_v5_masking_authority_v1.py tests/test_v5_masking_audit_metrics_v1.py -q
git add src/sea_ad_jepa/v5/masking_authority_v1.py src/sea_ad_jepa/v5/masking_audit_metrics_v1.py tests/test_v5_masking_authority_v1.py tests/test_v5_masking_audit_metrics_v1.py
git commit -m "feat(v5): add outcome-blind masking authority and metrics"
```

---

### Task 8: Implement presentation-normalized EMA time mechanics

**Files:**
- Create: `src/sea_ad_jepa/v5/ema_presentation_v1.py`
- Create: `tests/test_v5_ema_presentation_v1.py`

**Interfaces:**
- Produces: `ema_momentum_for_presentations(*, presentations_this_update: int, half_life_presentations: int) -> float`.
- Does not select the half-life.

- [ ] **Step 1: Write the mathematical tests**

```python
import math

from sea_ad_jepa.v5.ema_presentation_v1 import ema_momentum_for_presentations


def test_one_half_life_gives_half() -> None:
    assert math.isclose(
        ema_momentum_for_presentations(
            presentations_this_update=100, half_life_presentations=100
        ),
        0.5,
        rel_tol=0.0,
        abs_tol=1e-15,
    )


def test_packing_composition_is_invariant() -> None:
    a = ema_momentum_for_presentations(presentations_this_update=17, half_life_presentations=100)
    b = ema_momentum_for_presentations(presentations_this_update=23, half_life_presentations=100)
    together = ema_momentum_for_presentations(presentations_this_update=40, half_life_presentations=100)
    assert math.isclose(a * b, together, rel_tol=1e-15, abs_tol=1e-15)
```

- [ ] **Step 2: Run tests and verify import failure**

```bash
pytest tests/test_v5_ema_presentation_v1.py -q
```

- [ ] **Step 3: Implement exactly the prospective formula**

```python
import math


def ema_momentum_for_presentations(*, presentations_this_update: int, half_life_presentations: int) -> float:
    if isinstance(presentations_this_update, bool) or not isinstance(presentations_this_update, int) or presentations_this_update < 1:
        raise ValueError("presentations_this_update must be a positive integer")
    if isinstance(half_life_presentations, bool) or not isinstance(half_life_presentations, int) or half_life_presentations < 1:
        raise ValueError("half_life_presentations must be a positive integer")
    return math.exp(math.log(0.5) * presentations_this_update / half_life_presentations)
```

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/test_v5_ema_presentation_v1.py -q
git add src/sea_ad_jepa/v5/ema_presentation_v1.py tests/test_v5_ema_presentation_v1.py
git commit -m "feat(v5): add presentation-normalized EMA mechanics"
```

---

### Task 9: Build a bounded current-V5 runtime that cannot fall through to V4 defaults

**Design gate:** Execute only after teacher-target semantics, base-training estimand interface, target-address query authority and masking authority are explicitly approved. This task creates a **bounded qualification runtime**, not production-training authorization.

**Files:**
- Create: `src/sea_ad_jepa/v5/current_teacher_student_runtime_v1.py`
- Create: `tests/test_v5_current_teacher_student_runtime_v1.py`
- Modify: `tests/test_v5_no_historical_carryover_v1.py`

**Interfaces:**
- Consumes explicit model modules already constructed from current model-geometry authority.
- Consumes explicit scientific cell weights.
- Consumes explicit mask views from masking authority; does not choose mask fraction/block count internally.
- Consumes `FrozenTargetAddressCodebook` or approved target-address provider.
- Consumes current teacher-target receipt V1 and optimizer guard V2.
- Uses `weighted_block_jepa_loss` from `v5.data_first_geometry` or an approved successor with identical scientific-weight semantics.
- Uses presentation-normalized EMA momentum from Task 8.
- Returns a bounded qualification receipt with `production_training_authorized=False`.

- [ ] **Step 1: Write a source-level no-fallback test**

Add:

```python
runtime_source = Path("src/sea_ad_jepa/v5/current_teacher_student_runtime_v1.py").read_text(encoding="utf-8")
assert "v4.teacher_student_runtime import production_update" not in runtime_source
assert "PRODUCTION_CONFIG" not in runtime_source
assert "validate_production_config" not in runtime_source
assert "online.tokenizer.gene_identity" not in runtime_source
```

- [ ] **Step 2: Write a synthetic weighted-loss invariance test**

Create a two-cell synthetic fixture with weights `[1.0, 3.0]`. Run the same prediction/target rows packed as one microbatch and as two microbatches. Assert identical scientific loss and identical accepted scientific weight mass to tight tolerance. The test must fail if the runtime averages microbatch means equally.

- [ ] **Step 3: Write a teacher-gradient/EMA chronology test**

Required assertions after one bounded synthetic update:

- teacher parameters have no gradients;
- optimizer step counter advances by exactly one;
- EMA update count advances by exactly one;
- failed/skipped optimizer step does not advance EMA;
- returned receipt says `production_training_authorized is False`.

- [ ] **Step 4: Write target-address isolation test**

Construct a fixed address codebook and assert no target-address parameter exists in the optimizer parameter groups. Hidden target expression must not enter student input. Visible online identity parameters may still be trained through visible student encoding; the hidden target query itself must not be sourced from online trainable identity.

- [ ] **Step 5: Run tests and verify runtime is absent**

```bash
pytest tests/test_v5_current_teacher_student_runtime_v1.py tests/test_v5_no_historical_carryover_v1.py -q
```

Expected: FAIL until implementation exists.

- [ ] **Step 6: Implement the minimal bounded runtime**

The runtime must accept all scientific/numerical authority from arguments/authority objects. It may reuse low-level mechanical helpers only when they do not bring historical defaults with them. If a V4 helper has an embedded semantic or numeric default, port the mechanical logic into a current-V5 focused helper rather than importing the historical policy.

Do not provide a default config object representing production values.

- [ ] **Step 7: Run focused and adjacent regressions**

```bash
pytest \
  tests/test_v5_current_teacher_student_runtime_v1.py \
  tests/test_v5_no_historical_carryover_v1.py \
  tests/test_v5_current_teacher_target_receipt_v1.py \
  tests/test_v5_qualified_optimizer_guard_v2.py \
  tests/test_v5_ema_presentation_v1.py \
  -q
```

Then run existing C2/EMA/optimizer mechanics suites relevant to the repaired chronology. Any skip in a critical test must be reported as unresolved, not green.

- [ ] **Step 8: Commit**

```bash
git add src/sea_ad_jepa/v5/current_teacher_student_runtime_v1.py tests/test_v5_current_teacher_student_runtime_v1.py tests/test_v5_no_historical_carryover_v1.py
git commit -m "feat(v5): add authority-driven bounded teacher student runtime"
```

---

### Task 10: Rebind checkpoint/preexecution governance without historical vocabulary

**Files:**
- Create: `src/sea_ad_jepa/v5/atomic_checkpoint_guard_v4.py`
- Create: `tests/test_v5_atomic_checkpoint_guard_v4.py`

**Interfaces:**
- Consumes: `TrainerPreexecutionAuthorityV3`, `CriticalTestExecutionAuthorityV1`, `ProductionProtectedRegistryAuthorityV1`.
- Must not import `trainer_preexecution_contract_v2`.

- [ ] **Step 1: Write source-level test forbidding V2 import**

```python
source = Path("src/sea_ad_jepa/v5/atomic_checkpoint_guard_v4.py").read_text(encoding="utf-8")
assert "trainer_preexecution_contract_v2" not in source
assert "PROTECTED_48" not in source
assert "HISTORICAL_128X8" not in source
```

- [ ] **Step 2: Write a two-block protected-registry checkpoint test**

Use the Task 3 `make_registry(2)` fixture and assert V4 accepts telemetry bound to its computed registry digest/count and rejects telemetry claiming 48 tensors.

- [ ] **Step 3: Implement by porting only current-registry/atomic invariants from checkpoint V3**

Preserve:

- exact authority-binding set comparison;
- current protected-registry SHA/count validation;
- mechanics sequence validation;
- threshold authority hash binding;
- forbidden-gate enforcement;
- atomic telemetry completeness.

Replace V2 critical-test validation with Task 2 authority.

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/test_v5_atomic_checkpoint_guard_v4.py tests/test_v5_trainer_preexecution_contract_v3.py -q
git add src/sea_ad_jepa/v5/atomic_checkpoint_guard_v4.py tests/test_v5_atomic_checkpoint_guard_v4.py
git commit -m "feat(v5): remove historical preexecution vocabulary from checkpoint guard"
```

---

### Task 11: Governance integration and verification

**Files:**
- Modify only after independent review: `START_HERE.md`, `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, current handoff/state files and authority index/supersession map as appropriate.
- Create a review receipt under `docs/agent/` binding exact implementation/test commit SHAs.

**Interfaces:**
- Consumes: Tasks 1-10 passing on an approved implementation branch.
- Produces: current-V5 bounded-qualification authority references; still no production training authority.

- [ ] **Step 1: Run the complete focused successor suite**

```bash
pytest \
  tests/test_v5_no_historical_carryover_v1.py \
  tests/test_v5_critical_test_execution_authority_v1.py \
  tests/test_v5_trainer_preexecution_contract_v3.py \
  tests/test_v5_current_teacher_target_receipt_v1.py \
  tests/test_v5_qualified_optimizer_guard_v2.py \
  tests/test_v5_target_address_query_v1.py \
  tests/test_v5_masking_authority_v1.py \
  tests/test_v5_masking_audit_metrics_v1.py \
  tests/test_v5_ema_presentation_v1.py \
  tests/test_v5_current_teacher_student_runtime_v1.py \
  tests/test_v5_atomic_checkpoint_guard_v4.py \
  -q
```

Expected: all executed tests PASS, zero critical skips.

- [ ] **Step 2: Run adjacent historical mechanics regression suites**

Run the existing repaired C2/T1/EMA/optimizer/checkpoint tests. Historical mechanics regression failure blocks the successor. Historical scientific defaults passing their forensic tests do not promote them to current authority.

- [ ] **Step 3: Perform manual anti-carryover review**

Search the new production-facing V5 successor files for:

```text
0.996
0.40
128
microbatch=8
blocks=6
range(6)
48
PROTECTED_48
HISTORICAL_128X8
PRODUCTION_CONFIG
validate_production_config
v4.teacher_student_runtime.production_update
v5_qualified_teacher_target_receipt_v1
online.tokenizer.gene_identity
```

For any hit, adjudicate whether it is a test assertion/negative fixture or an actual policy dependency. Production policy dependency is a blocker unless explicitly authorized by a current authority root.

- [ ] **Step 4: Verify forbidden data remained closed**

The review receipt must explicitly state:

```text
training_executed = false
real_d_shared_outcome_inspected = false
protected_outcome_inspected = false
d_private_executed = false
d_obs_outcome_executed = false
td60_executed = false
```

- [ ] **Step 5: Independent review before governance promotion**

Have an independent lane review:

- receipt exact-field semantics;
- no legacy schema widening;
- target-address gradient isolation;
- scientific-weight preservation;
- no 6/48/128x8 geometry carryover;
- no V4 production-update fallback;
- EMA presentation-unit semantics;
- checkpoint current-registry binding.

- [ ] **Step 6: Update governance docs only after review passes**

Even after governance promotion, retain:

`TRAINING_OFF`

until a separate, explicit production-training authorization binds all upstream immutable roots.

- [ ] **Step 7: Commit governance update**

```bash
git add START_HERE.md docs/agent
git commit -m "docs(v5): bind reviewed current target-authority successor"
```

---

## Self-Review Results

**Spec coverage:** This plan covers the discovered carryover seams in the runtime fallback, legacy receipt validator, fixed preexecution geometry/test vocabulary, checkpoint V2 vocabulary dependency, target-address shared-parameter path, masking-policy defaults, EMA `.996`, and scientific-weight preservation. It deliberately does not choose the primary representation, base-training estimand, teacher target semantics, mask mixture or model width before those separate authorities are approved.

**Placeholder scan:** No implementation step relies on `TBD`, `TODO`, or unspecified error handling. The two explicit design gates are intentional project governance boundaries, not missing implementation details.

**Type consistency:** Current receipt V1 feeds optimizer guard V2 and current runtime V1; critical-test authority V1 and protected-registry authority V1 feed preexecution V3 and checkpoint V4; target-address codebook feeds current runtime V1; EMA presentation helper feeds current runtime V1.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-15-v5-target-authority-build.md`.

Recommended execution mode after the design decisions are explicitly approved: **Subagent-Driven** for independent tasks (preexecution/receipt/EMA/masking authority), with serial integration at the runtime/checkpoint seams. If subagents are unavailable, execute inline in task order with a review checkpoint after every commit.
