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
from sea_ad_jepa.v5.current_training_authority_v1 import issue_training_authority_v1
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


def test_training_authority_is_issued_only_after_closure_preexecution_receipt_critical_and_runtime_match() -> None:
    roots = roots_v2()
    closure = closure_for(roots)
    pre = make_preexecution(roots)
    pre.bind_closure_v2(closure)
    receipt = make_receipt(roots, pre)

    authority = issue_training_authority_v1(
        closure_v2=closure,
        preexecution=pre,
        receipt_v2=receipt,
        expected_target_package_root=h("target-package"),
        critical_test=critical_for(roots),
        runtime_source=runtime_for(roots),
    )
    authority.validate()
    assert authority.training_authorized is True
    assert authority.closure_v2_sha256 == closure["closure_digest"]
    assert authority.preexecution_authority_sha256 == pre.canonical_digest()

    bad_runtime = AuthorityStub(h("wrong-runtime"))
    with pytest.raises(ValueError, match="runtime"):
        issue_training_authority_v1(
            closure_v2=closure,
            preexecution=pre,
            receipt_v2=receipt,
            expected_target_package_root=h("target-package"),
            critical_test=critical_for(roots),
            runtime_source=bad_runtime,
        )


def test_optimizer_v3_requires_v2_receipt_and_explicit_matching_training_authority() -> None:
    roots = roots_v2()
    closure = closure_for(roots)
    pre = make_preexecution(roots)
    pre.bind_closure_v2(closure)
    receipt = make_receipt(roots, pre)
    authority = issue_training_authority_v1(
        closure_v2=closure,
        preexecution=pre,
        receipt_v2=receipt,
        expected_target_package_root=h("target-package"),
        critical_test=critical_for(roots),
        runtime_source=runtime_for(roots),
    )
    expected_roots = dict(roots)
    expected_roots["preexecution_authority_sha256"] = pre.canonical_digest()

    optimizer = FakeOptimizer()
    guard = install_current_optimizer_guard_v3(
        optimizer,
        receipt,
        training_authority=authority,
        expected_target_package_root=h("target-package"),
        expected_authority_roots=expected_roots,
        expected_closure_v2_sha256=closure["closure_digest"],
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
