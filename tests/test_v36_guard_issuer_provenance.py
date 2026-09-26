"""V36 independent red-team of the REAL optimizer-guard issuance boundary.

A complete set of fake hashes MUST NOT install any production guard.
Only tests explicitly monkeypatching the guard module use test-only stubs;
those controls do not establish any real authority graph or authorize training.
No expression, protected outcomes, or genuine optimizer updates.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import inspect
import json

import pytest

from test_v30_issuance_source_provenance import fabricated_envelope, digest
from sea_ad_jepa.v5.current_authority_closure_v2 import validate_current_v5_authority_closure_v2
from sea_ad_jepa.v5.current_training_authority_v1 import (
    CurrentTrainingAuthorityV1, ISSUANCE_POLICY_ID,
)
from sea_ad_jepa.v5.qualified_optimizer_guard_v3 import (
    CurrentOptimizerStepGuardV3, install_current_optimizer_guard_v3,
)
import sea_ad_jepa.v5.qualified_optimizer_guard_v3 as guard_module


class Handle:
    def __init__(self, owner, which, callback):
        self.owner, self.which, self.callback = owner, which, callback

    def remove(self):
        self.owner.hooks[self.which].remove(self.callback)


class DummyOptimizer:
    def __init__(self):
        self.hooks = {"pre": [], "post": []}

    def register_step_pre_hook(self, cb):
        self.hooks["pre"].append(cb)
        return Handle(self, "pre", cb)

    def register_step_post_hook(self, cb):
        self.hooks["post"].append(cb)
        return Handle(self, "post", cb)

    def step(self, **kwargs):
        args = ()
        for cb in list(self.hooks["pre"]):
            ret = cb(self, args, kwargs)
            if ret is not None:
                args, kwargs = ret
        for cb in list(self.hooks["post"]):
            cb(self, args, kwargs)


def canonical_digest(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode()).hexdigest()


def forged_public_token(critical, runtime, closure, pre, receipt, target):
    core = {
        "schema": "V5_CURRENT_TRAINING_AUTHORITY_V1",
        "authority_id": "V5_CURRENT_TRAINING_AUTHORITY_V1",
        "closure_v2_sha256": closure["closure_digest"],
        "preexecution_authority_sha256": pre.canonical_digest(),
        "receipt_v2_sha256": receipt["receipt_digest"],
        "target_package_root": target,
        "critical_test_authority_sha256": critical.canonical_digest(),
        "runtime_source_authority_sha256": runtime.canonical_digest(),
        "issuance_policy_id": ISSUANCE_POLICY_ID,
        "training_authorized": True,
    }
    authority = CurrentTrainingAuthorityV1(
        **{k: v for k, v in core.items() if k not in ("schema", "training_authorized")},
        issuance_proof_sha256=canonical_digest(core),
    )
    authority.validate()  # demonstrates legacy self-hash is coherent
    return authority


def payload():
    critical, runtime, closure, pre, receipt, target = fabricated_envelope()
    fake = {key: object() for key in
            inspect.signature(validate_current_v5_authority_closure_v2).parameters}
    fake["critical_test"] = critical
    fake["runtime_source"] = runtime
    roots = dict(closure["authority_roots"])
    roots["preexecution_authority_sha256"] = pre.canonical_digest()
    token = forged_public_token(critical, runtime, closure, pre, receipt, target)
    return {
        "receipt": receipt, "training_authority": token,
        "expected_target_package_root": target,
        "expected_authority_roots": roots,
        "expected_closure_v2_sha256": closure["closure_digest"],
        "closure_v2": closure, "preexecution": pre,
        "critical_test": critical, "runtime_source": runtime,
        "closure_inputs": fake,
    }


def test_forged_public_token_without_live_graph_cannot_register_hooks():
    x = payload()
    opt = DummyOptimizer()
    del x["closure_inputs"]
    with pytest.raises(ValueError, match="requires live closure_inputs"):
        install_current_optimizer_guard_v3(opt, **x)
    assert opt.hooks == {"pre": [], "post": []}
    assert not hasattr(opt, "_v5_current_optimizer_guard_v3")


def test_complete_fake_role_vocabulary_cannot_pass_real_graph_validator():
    x = payload()
    opt = DummyOptimizer()
    # Exact role names + valid self-consistent digests do NOT make scientific
    # objects real or current. This runs production validator, unmocked.
    with pytest.raises((ValueError, TypeError), match="current|schema|typed|must"):
        install_current_optimizer_guard_v3(opt, **x)
    assert opt.hooks == {"pre": [], "post": []}
    assert not hasattr(opt, "_v5_current_optimizer_guard_v3")


def test_public_constructor_does_not_bypass_guard_live_issuer():
    x = payload()
    opt = DummyOptimizer()
    x["closure_inputs"] = None
    with pytest.raises(ValueError, match="requires live closure_inputs"):
        CurrentOptimizerStepGuardV3(optimizer=opt, **x)
    assert opt.hooks == {"pre": [], "post": []}


def test_fake_test_only_issuer_must_return_exact_presented_token(monkeypatch):
    x = payload()
    opt = DummyOptimizer()
    forged = x["training_authority"]
    different = replace(
        forged, authority_id="WRONG_BUT_SELF_CONSISTENT",
        issuance_proof_sha256=forged.issuance_proof_sha256,
    )
    # Repair checksum so the substituted token passes its own validate().
    different = replace(
        different, issuance_proof_sha256=canonical_digest(different._proof_payload())
    )
    assert different.canonical_digest() != forged.canonical_digest()
    monkeypatch.setattr(
        guard_module, "issue_training_authority_v1", lambda **kwargs: different
    )
    with pytest.raises(ValueError, match="not authenticated by live issuance"):
        install_current_optimizer_guard_v3(opt, **x)
    assert opt.hooks == {"pre": [], "post": []}


def test_step_revalidates_issuer_after_install_and_detects_change(monkeypatch):
    x = payload()
    opt = DummyOptimizer()
    authentic_only_as_test_fixture = x["training_authority"]
    calls = []
    def synthetic_issuer_spy(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            return authentic_only_as_test_fixture
        raise ValueError("fixture live evidence was revoked")
    monkeypatch.setattr(guard_module, "issue_training_authority_v1", synthetic_issuer_spy)
    guard = install_current_optimizer_guard_v3(opt, **x)
    assert len(calls) == 1
    with pytest.raises(RuntimeError, match="authority chain is no longer valid"):
        guard.arm_for_step(schedule_cursor=0)
    assert len(calls) == 2
    assert guard._armed_cursor is None
    assert len(opt.hooks["pre"]) == len(opt.hooks["post"]) == 1


def test_reinstallation_with_spliced_evidence_identity_fails(monkeypatch):
    x = payload()
    opt = DummyOptimizer()
    monkeypatch.setattr(
        guard_module, "issue_training_authority_v1",
        lambda **kwargs: x["training_authority"],
    )
    installed = install_current_optimizer_guard_v3(opt, **x)
    assert installed.training_authority_digest == x["training_authority"].canonical_digest()
    clone = dict(x)
    clone["closure_inputs"] = dict(x["closure_inputs"])
    with pytest.raises(ValueError, match="live evidence changed"):
        install_current_optimizer_guard_v3(opt, **clone)
    assert len(opt.hooks["pre"]) == len(opt.hooks["post"]) == 1
    installed.close()
    assert opt.hooks == {"pre": [], "post": []}
