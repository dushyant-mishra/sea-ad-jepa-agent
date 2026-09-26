"""Synthetic hash/optimizer mechanics tests. Guard issuer is MOCKED in this file ONLY.
No test here demonstrates actual live source qualification or final authorization.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from sea_ad_jepa.v5.current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS
from sea_ad_jepa.v5.current_authority_roots_v2 import (
    CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2,
    CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2,
)
from sea_ad_jepa.v5.current_trainer_preexecution_contract_v2 import CurrentTrainerPreexecutionAuthorityV2
from sea_ad_jepa.v5.current_teacher_target_receipt_v1 import seal_current_teacher_target_receipt_v1
from sea_ad_jepa.v5.current_teacher_target_receipt_v2 import (
    seal_current_teacher_target_receipt_v2,
    validate_current_teacher_target_receipt_v2,
)
from sea_ad_jepa.v5.current_training_authority_v1 import (CurrentTrainingAuthorityV1, ISSUANCE_POLICY_ID, CLOSURE_INPUT_ROLES, issue_training_authority_v1)
import sea_ad_jepa.v5.qualified_optimizer_guard_v3 as optimizer_guard_module
from sea_ad_jepa.v5.qualified_optimizer_guard_v3 import install_current_optimizer_guard_v3


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def canonical_digest(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


def roots_v2() -> dict[str, str]:
    return {name: h(name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}


class AuthorityStub:
    training_authorized = False

    def __init__(self, digest: str) -> None:
        self._digest = digest

    def validate(self) -> None:
        return None

    def canonical_digest(self) -> str:
        return self._digest


class FakeHandle:
    def remove(self) -> None:
        return None


class FakeOptimizer:
    def __init__(self) -> None:
        self.pre = None
        self.post = None

    def register_step_pre_hook(self, fn):
        self.pre = fn
        return FakeHandle()

    def register_step_post_hook(self, fn):
        self.post = fn
        return FakeHandle()

    def step(self, **kwargs):
        args = ()
        if self.pre is not None:
            out = self.pre(self, args, dict(kwargs))
            if out is not None:
                args, kwargs = out
        if self.post is not None:
            self.post(self, args, kwargs)
        return "stepped"


def closure_for(roots: dict[str, str]) -> dict:
    core = {
        "schema": "V5_CURRENT_AUTHORITY_CLOSURE_V2",
        "authority_roots": dict(roots),
        "training_authorized": False,
    }
    return {**core, "closure_digest": canonical_digest(core)}


def critical_for(roots: dict[str, str]) -> AuthorityStub:
    return AuthorityStub(roots["critical_test_authority_sha256"])


def runtime_for(roots: dict[str, str]) -> AuthorityStub:
    return AuthorityStub(roots["runtime_source_authority_sha256"])


def make_preexecution(roots: dict[str, str]) -> CurrentTrainerPreexecutionAuthorityV2:
    closure = closure_for(roots)
    return CurrentTrainerPreexecutionAuthorityV2(
        authority_roots=roots,
        closure_v2_sha256=closure["closure_digest"],
        protected_registry_authority_sha256=roots["protected_registry_authority_sha256"],
        critical_test_authority_sha256=roots["critical_test_authority_sha256"],
        relational_training_active=False,
        optimizer_started=False,
    )


def make_receipt(roots: dict[str, str], pre: CurrentTrainerPreexecutionAuthorityV2) -> dict:
    receipt_roots = dict(roots)
    receipt_roots["preexecution_authority_sha256"] = pre.canonical_digest()
    return seal_current_teacher_target_receipt_v2(
        target_package_root=h("target-package"),
        authority_roots=receipt_roots,
        closure_v2_sha256=pre.closure_v2_sha256,
    )



def synthetic_guard_token_for_mechanics_only(roots, closure, pre, receipt):
    """Never call production issuer here: no real typed closure exists.

    This constructed token isolates optimizer hook/cursor mechanics only.
    Its acceptance is NOT a provenance or issuance positive control.
    """
    core = {
        "schema": "V5_CURRENT_TRAINING_AUTHORITY_V1",
        "authority_id": "SYNTHETIC_GUARD_FIXTURE_ONLY",
        "closure_v2_sha256": closure["closure_digest"],
        "preexecution_authority_sha256": pre.canonical_digest(),
        "receipt_v2_sha256": receipt["receipt_digest"],
        "target_package_root": h("target-package"),
        "critical_test_authority_sha256": roots["critical_test_authority_sha256"],
        "runtime_source_authority_sha256": roots["runtime_source_authority_sha256"],
        "issuance_policy_id": ISSUANCE_POLICY_ID,
        "training_authorized": True,
    }
    token = CurrentTrainingAuthorityV1(
        authority_id=core["authority_id"],
        closure_v2_sha256=core["closure_v2_sha256"],
        preexecution_authority_sha256=core["preexecution_authority_sha256"],
        receipt_v2_sha256=core["receipt_v2_sha256"],
        target_package_root=core["target_package_root"],
        critical_test_authority_sha256=core["critical_test_authority_sha256"],
        runtime_source_authority_sha256=core["runtime_source_authority_sha256"],
        issuance_policy_id=ISSUANCE_POLICY_ID,
        issuance_proof_sha256=canonical_digest(core),
    )
    token.validate()
    return token


@pytest.fixture(autouse=True)
def _synthetic_optimizer_mechanics_issuer_only(monkeypatch):
    """MOCK only the optimizer's issuer import, not production issuer tests.

    A real typed closure is intentionally absent in this synthetic-mechanics
    file. Separate V36 guard provenance tests call the original unmocked guard.
    """
    def issue_synthetic_mechanics_only(**kwargs):
        c, pre, receipt = kwargs["closure_v2"], kwargs["preexecution"], kwargs["receipt_v2"]
        pre.bind_closure_v2(c)
        live = kwargs["closure_inputs"]
        if set(live) != CLOSURE_INPUT_ROLES:
            raise AssertionError("mechanics-only fake requires exact role vocabulary")
        if live["critical_test"] is not kwargs["critical_test"] or live["runtime_source"] is not kwargs["runtime_source"]:
            raise AssertionError("mechanics-only fake requires same critical/runtime objects")
        return synthetic_guard_token_for_mechanics_only(c["authority_roots"], c, pre, receipt)
    monkeypatch.setattr(optimizer_guard_module, "issue_training_authority_v1", issue_synthetic_mechanics_only)


def _mechanics_live_inputs(roots):
    # Correct role names, deliberately fake scientific authority values.
    # The REAL validator would reject these; only the test spy accepts them.
    inputs = {role: object() for role in CLOSURE_INPUT_ROLES}
    inputs["critical_test"] = critical_for(roots)
    inputs["runtime_source"] = runtime_for(roots)
    return inputs


def test_preexecution_v2_requires_exact_v2_root_vocabulary_and_live_closure_binding() -> None:
    roots = roots_v2()
    pre = make_preexecution(roots)
    pre.bind_closure_v2(closure_for(roots))
    assert tuple(pre.normalized_roots()) == CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
    assert pre.training_authorized is False

    legacy = {name: h(name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS}
    with pytest.raises(ValueError, match="V2 upstream roots"):
        replace(pre, authority_roots=legacy).validate()

    bad = closure_for(roots)
    bad["authority_roots"] = {**roots, "masking_authority_sha256": h("splice")}
    with pytest.raises(ValueError, match="closure.*roots|digest"):
        pre.bind_closure_v2(bad)


def test_receipt_v2_seals_v2_roots_preexecution_and_closure_and_rejects_v1_receipt() -> None:
    roots = roots_v2()
    pre = make_preexecution(roots)
    receipt = make_receipt(roots, pre)
    expected = dict(roots)
    expected["preexecution_authority_sha256"] = pre.canonical_digest()
    verified = validate_current_teacher_target_receipt_v2(
        receipt,
        expected_target_package_root=h("target-package"),
        expected_authority_roots=expected,
        expected_closure_v2_sha256=pre.closure_v2_sha256,
    )
    assert tuple(verified["authority_roots"]) == CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2
    assert verified["training_authorized"] is False

    legacy_roots = {name: h(name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS}
    legacy_roots["preexecution_authority_sha256"] = h("legacy-pre")
    legacy = seal_current_teacher_target_receipt_v1(h("target-package"), legacy_roots)
    with pytest.raises(ValueError):
        validate_current_teacher_target_receipt_v2(
            legacy,
            expected_target_package_root=h("target-package"),
            expected_authority_roots=expected,
            expected_closure_v2_sha256=pre.closure_v2_sha256,
        )


def test_final_issuer_rejects_legacy_synthetic_hash_only_closure() -> None:
    roots = roots_v2()
    closure = closure_for(roots)
    pre = make_preexecution(roots)
    pre.bind_closure_v2(closure)
    receipt = make_receipt(roots, pre)
    # This is the original legacy hash-only synthetic positive control.
    # It must now fail even though closure, receipt and SHA roots agree.
    with pytest.raises(ValueError, match="live closure_inputs required"):
        issue_training_authority_v1(
            closure_v2=closure, preexecution=pre, receipt_v2=receipt,
            expected_target_package_root=h("target-package"),
            critical_test=critical_for(roots), runtime_source=runtime_for(roots),
        )


def test_optimizer_v3_requires_v2_receipt_and_explicit_matching_training_authority() -> None:
    roots = roots_v2()
    closure = closure_for(roots)
    pre = make_preexecution(roots)
    pre.bind_closure_v2(closure)
    receipt = make_receipt(roots, pre)
    authority = synthetic_guard_token_for_mechanics_only(roots, closure, pre, receipt)
    expected_roots = dict(roots)
    expected_roots["preexecution_authority_sha256"] = pre.canonical_digest()

    optimizer = FakeOptimizer()
    fake_live = _mechanics_live_inputs(roots)
    guard = install_current_optimizer_guard_v3(
        optimizer,
        receipt,
        training_authority=authority,
        expected_target_package_root=h("target-package"),
        expected_authority_roots=expected_roots,
        expected_closure_v2_sha256=closure["closure_digest"],
        closure_v2=closure,
        preexecution=pre,
        critical_test=fake_live["critical_test"],
        runtime_source=fake_live["runtime_source"],
        closure_inputs=fake_live,
    )
    guard.arm_for_step(schedule_cursor=3)
    optimizer.step(v5_current_guard_schedule_cursor=3)
    assert guard.assert_step_completed(schedule_cursor=3)["guarded_optimizer_step"] is True

    legacy_roots = {name: h(name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS}
    legacy_roots["preexecution_authority_sha256"] = h("legacy-pre")
    legacy = seal_current_teacher_target_receipt_v1(h("target-package"), legacy_roots)
    with pytest.raises(ValueError):
        install_current_optimizer_guard_v3(
            FakeOptimizer(),
            legacy,
            training_authority=authority,
            expected_target_package_root=h("target-package"),
            expected_authority_roots=expected_roots,
            expected_closure_v2_sha256=closure["closure_digest"],
        )


def _guard_for_cursor_redteam():
    roots = roots_v2()
    closure = closure_for(roots)
    pre = make_preexecution(roots)
    pre.bind_closure_v2(closure)
    receipt = make_receipt(roots, pre)
    authority = synthetic_guard_token_for_mechanics_only(roots, closure, pre, receipt)
    receipt_roots = dict(roots)
    receipt_roots["preexecution_authority_sha256"] = pre.canonical_digest()
    optimizer = FakeOptimizer()
    fake_live = _mechanics_live_inputs(roots)
    guard = install_current_optimizer_guard_v3(
        optimizer,
        receipt,
        training_authority=authority,
        expected_target_package_root=h("target-package"),
        expected_authority_roots=receipt_roots,
        expected_closure_v2_sha256=closure["closure_digest"],
        closure_v2=closure,
        preexecution=pre,
        critical_test=fake_live["critical_test"],
        runtime_source=fake_live["runtime_source"],
        closure_inputs=fake_live,
    )
    return optimizer, guard


def test_optimizer_v3_step_proof_is_single_use_and_rejects_replayed_cursor() -> None:
    optimizer, guard = _guard_for_cursor_redteam()
    guard.arm_for_step(schedule_cursor=3)
    optimizer.step(v5_current_guard_schedule_cursor=3)
    assert guard.assert_step_completed(schedule_cursor=3)["guarded_optimizer_step"]
    with pytest.raises(RuntimeError, match="did not complete"):
        guard.assert_step_completed(schedule_cursor=3)
    with pytest.raises(RuntimeError, match="nonsequential"):
        guard.arm_for_step(schedule_cursor=3)
    with pytest.raises(RuntimeError, match="nonsequential"):
        guard.arm_for_step(schedule_cursor=2)
    with pytest.raises(RuntimeError, match="nonsequential"):
        guard.arm_for_step(schedule_cursor=5)
    guard.arm_for_step(schedule_cursor=4)
    optimizer.step(v5_current_guard_schedule_cursor=4)
    assert guard.assert_step_completed(schedule_cursor=4)["schedule_cursor"] == 4


def test_optimizer_v3_must_acknowledge_completed_step_before_arming_next() -> None:
    optimizer, guard = _guard_for_cursor_redteam()
    guard.arm_for_step(schedule_cursor=10)
    optimizer.step(v5_current_guard_schedule_cursor=10)
    with pytest.raises(RuntimeError, match="not been acknowledged"):
        guard.arm_for_step(schedule_cursor=11)
    with pytest.raises(RuntimeError, match="no uncompleted authorization"):
        guard.disarm_uncompleted_step(schedule_cursor=10, reason="completed")
    assert guard.assert_step_completed(schedule_cursor=10)["schedule_cursor"] == 10
    guard.arm_for_step(schedule_cursor=11)
    with pytest.raises(RuntimeError, match="already armed"):
        guard.arm_for_step(schedule_cursor=12)
    assert guard.disarm_uncompleted_step(schedule_cursor=11, reason="no optimizer step")["disarmed"]
    guard.arm_for_step(schedule_cursor=11)  # aborted-but-unstepped cursor can be retried
    optimizer.step(v5_current_guard_schedule_cursor=11)
    assert guard.assert_step_completed(schedule_cursor=11)["schedule_cursor"] == 11


def test_optimizer_v3_wrong_step_cursor_fails_before_step_and_does_not_advance() -> None:
    optimizer, guard = _guard_for_cursor_redteam()
    guard.arm_for_step(schedule_cursor=0)
    with pytest.raises(RuntimeError, match="schedule cursor mismatch"):
        optimizer.step(v5_current_guard_schedule_cursor=1)
    with pytest.raises(RuntimeError, match="did not complete"):
        guard.assert_step_completed(schedule_cursor=0)
    guard.arm_for_step(schedule_cursor=0)
    optimizer.step(v5_current_guard_schedule_cursor=0)
    assert guard.assert_step_completed(schedule_cursor=0)["schedule_cursor"] == 0
    guard.close()
    with pytest.raises(RuntimeError, match="closed"):
        guard.assert_step_completed(schedule_cursor=0)
