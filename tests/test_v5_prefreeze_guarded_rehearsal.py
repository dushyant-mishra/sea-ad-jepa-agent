import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
AUTH_PATH = ROOT / "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py"
REHEARSAL_PATH = ROOT / "src/sea_ad_jepa/v5/prefreeze_guarded_rehearsal.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


auth = _load("prefreeze_runtime_authority", AUTH_PATH)
rehearsal = _load("prefreeze_guarded_rehearsal", REHEARSAL_PATH)


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class Handle:
    def __init__(self, coll, fn):
        self.coll = coll
        self.fn = fn

    def remove(self):
        if self.fn in self.coll:
            self.coll.remove(self.fn)


class FakeOptimizer:
    def __init__(self, events, *, fail=False):
        self.events = events
        self.fail = fail
        self.pre = []
        self.post = []
        self.mutations = 0

    def register_step_pre_hook(self, fn):
        self.pre.append(fn)
        return Handle(self.pre, fn)

    def register_step_post_hook(self, fn):
        self.post.append(fn)
        return Handle(self.post, fn)

    def step(self, *args, **kwargs):
        for fn in list(self.pre):
            out = fn(self, args, kwargs)
            if out is not None:
                args, kwargs = out
        self.events.append("optimizer_step")
        if self.fail:
            raise RuntimeError("step exploded")
        self.mutations += 1
        for fn in list(self.post):
            fn(self, args, kwargs)
        return self.mutations


def _authority():
    return auth.PrefreezeMechanicalAuthorityV1.issue(
        governance_state=json.loads(STATE_PATH.read_text()),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
    )


def _guard(events, *, fail=False):
    authority = _authority()
    optimizer = FakeOptimizer(events, fail=fail)
    return authority, optimizer, auth.PrefreezeOptimizerGuardV1(authority, optimizer)


def test_rehearsal_runs_optimizer_bound_order_and_roundtrip():
    events = []
    authority, optimizer, guard = _guard(events)

    result = rehearsal.run_test_only_guarded_rehearsal(
        authority=authority,
        guard=guard,
        optimizer_identity="adamw:v1",
        backward=lambda: events.append("backward"),
        unscale=lambda: events.append("unscale"),
        validate_gradients=lambda: events.append("validate") or True,
        ema_update=lambda: events.append("ema"),
        checkpoint=lambda: events.append("checkpoint") or _sha("checkpoint-B"),
    )

    assert events == ["backward", "unscale", "validate", "optimizer_step", "ema", "checkpoint"]
    assert optimizer.mutations == 1
    assert result["schema"] == "V5_PREFREEZE_GUARDED_REHEARSAL_V2"
    assert result["rehearsal_only"] is True
    assert result["training_authorized"] is False
    assert result["execution_authorized"] is False
    assert result["starting_checkpoint_digest"] == _sha("checkpoint-A")
    assert result["checkpoint_digest"] == _sha("checkpoint-B")
    verified = auth.PrefreezeMechanicalAuthorityV1.verify_completed_checkpoint_receipt(
        result["checkpoint_receipt"], _sha("checkpoint-B"),
        governance_state=json.loads(STATE_PATH.read_text())
    )
    assert verified["guarded_step_token"] == result["guarded_step_token"]


def test_failed_gradient_validation_prevents_optimizer_ema_and_checkpoint():
    events = []
    authority, optimizer, guard = _guard(events)
    with pytest.raises(auth.StepCompletionError, match="gradient validation failed"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            backward=lambda: events.append("backward"),
            unscale=lambda: events.append("unscale"),
            validate_gradients=lambda: events.append("validate") or False,
            ema_update=lambda: events.append("ema"),
            checkpoint=lambda: events.append("checkpoint") or _sha("checkpoint-B"),
        )
    assert events == ["backward", "unscale", "validate"]
    assert optimizer.mutations == 0


def test_optimizer_exception_prevents_ema_and_checkpoint():
    events = []
    authority, optimizer, guard = _guard(events, fail=True)
    with pytest.raises(RuntimeError, match="step exploded"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            backward=lambda: events.append("backward"),
            unscale=lambda: events.append("unscale"),
            validate_gradients=lambda: events.append("validate") or True,
            ema_update=lambda: events.append("ema"),
            checkpoint=lambda: events.append("checkpoint") or _sha("checkpoint-B"),
        )
    assert events == ["backward", "unscale", "validate", "optimizer_step"]
    assert optimizer.mutations == 0


def test_post_update_checkpoint_must_be_new_state():
    events = []
    authority, _, guard = _guard(events)
    with pytest.raises(auth.PrefreezeGovernanceError, match="new state"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            backward=lambda: None,
            unscale=lambda: None,
            validate_gradients=lambda: True,
            ema_update=lambda: None,
            checkpoint=lambda: _sha("checkpoint-A"),
        )


def test_rehearsal_refuses_unbound_authority_or_guard():
    authority = _authority()
    other = _authority()
    guard = auth.PrefreezeOptimizerGuardV1(other, FakeOptimizer([]))
    with pytest.raises(auth.PrefreezeGovernanceError, match="bound"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            backward=lambda: None,
            unscale=lambda: None,
            validate_gradients=lambda: True,
            ema_update=lambda: None,
            checkpoint=lambda: _sha("checkpoint-B"),
        )
