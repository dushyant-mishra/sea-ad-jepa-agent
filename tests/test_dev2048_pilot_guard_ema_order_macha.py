"""Mock-only checks of the pinned PR224 optimizer guard and EMA wrapper.

Deliberately NOT in the no-step inventories: it names guard entry points
(run_optimizer_step, run_ema, the guarded wrapper) in order to drive them
with fakes. No tensor is updated anywhere in this file:
- the optimizer is a fake whose pre/post hooks fire around a no-op or a
  raising body (no parameters, no state);
- "parameters" are recording stand-ins whose mul_/add_ only log the call;
- the reference update is patched with a fake that only invokes the
  wrapper's callbacks. No forward, backward, optimizer step or EMA math.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from sea_ad_jepa.v5 import inactive_guarded_update_v1 as wrapper
from sea_ad_jepa.v5.prefreeze_runtime_authority import (
    PrefreezeMechanicalAuthorityV1, PrefreezeOptimizerGuardV1, StepCompletionError,
)

ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"


class FakeOptimizer:
    """Hook-faithful stand-in: pre hooks, body, post hooks. Holds no tensors."""

    def __init__(self, body=None):
        self.pre, self.post, self.body, self.calls = [], [], body, 0

    def register_step_pre_hook(self, fn):
        self.pre.append(fn)
        return SimpleNamespace(remove=lambda: self.pre.remove(fn))

    def register_step_post_hook(self, fn):
        self.post.append(fn)
        return SimpleNamespace(remove=lambda: self.post.remove(fn))

    def step(self, *args, **kwargs):  # the guard's only way in
        for hook in list(self.pre):
            out = hook(self, args, kwargs)
            if out is not None:
                args, kwargs = out
        self.calls += 1
        if self.body is not None:
            self.body()
        for hook in list(self.post):
            hook(self, args, kwargs)

    def zero_grad(self, set_to_none=True):
        pass


class Recorder:
    """Parameter stand-in: logs mul_/add_ instead of computing."""

    def __init__(self, name, log):
        self.name, self.log, self.post_step = name, log, False

    def mul_(self, m):
        self.log.append(("mul_", self.name, m))
        return self

    def add_(self, other, alpha=1.0):
        self.log.append(("add_", self.name, other.name, other.post_step, alpha))
        return self


def _authority():
    return PrefreezeMechanicalAuthorityV1.issue(
        governance_state=json.loads(PREMISE.read_text(encoding="utf-8")),
        optimizer_identity="fake-optimizer-identity", checkpoint_digest="a" * 64)


def _armed_guard(body=None):
    authority = _authority()
    guard = PrefreezeOptimizerGuardV1(authority, FakeOptimizer(body))
    token = guard.begin_step(authority.optimizer_identity, authority.checkpoint_digest)
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    return guard, token


def test_failed_optimizer_step_never_permits_ema():
    def boom():
        raise RuntimeError("optimizer body failed")
    guard, token = _armed_guard(boom)
    with pytest.raises(RuntimeError, match="optimizer body failed"):
        guard.run_optimizer_step(token)
    ema = mock.Mock()
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, ema)
    ema.assert_not_called()


def test_skipped_optimizer_step_never_permits_ema():
    guard, token = _armed_guard()
    ema = mock.Mock()
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, ema)
    ema.assert_not_called()


def test_successful_step_permits_exactly_one_ema():
    guard, token = _armed_guard()
    guard.run_optimizer_step(token)
    ema = mock.Mock()
    guard.run_ema(token, ema)
    ema.assert_called_once_with()
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, ema)
    assert ema.call_count == 1


def _fake_modules(log, body):
    online = [Recorder("online.a", log), Recorder("online.b", log)]
    teacher = [Recorder("teacher.a", log), Recorder("teacher.b", log)]
    predictor = [Recorder("predictor.a", log)]

    def step_body():
        body(online)
    return SimpleNamespace(
        online=SimpleNamespace(parameters=lambda: iter(online)),
        teacher=SimpleNamespace(parameters=lambda: iter(teacher)),
        predictor=SimpleNamespace(parameters=lambda: iter(predictor)),
        optimizer=FakeOptimizer(step_body))


def _fake_reference(try_ema_after_failure: bool):
    def reference(modules, *, backward_loss, before_gradient_validation,
                  guarded_optimizer_step, guarded_ema_step, **_):
        before_gradient_validation()
        try:
            guarded_optimizer_step({})
        except RuntimeError:
            if not try_ema_after_failure:
                raise
            guarded_ema_step(0.9)        # must be refused by the guard
            raise AssertionError("EMA was permitted after a failed step")
        guarded_ema_step(0.9)
        return {"schema": "FAKE"}
    return reference


def test_wrapper_ema_uses_post_step_student_encoder_not_predictor_exactly_once():
    log = []

    def mark_post_step(online):
        for p in online:
            p.post_step = True
    modules = _fake_modules(log, mark_post_step)
    with mock.patch.object(wrapper, "run_inactive_reference_update", _fake_reference(False)):
        report = wrapper.run_guarded_inactive_reference_update(
            modules, authority=_authority(), update_index=0)
    assert report["guarded_optimizer_step"] is True and report["guarded_ema"] is True
    adds = [e for e in log if e[0] == "add_"]
    assert [(e[1], e[2]) for e in adds] == [("teacher.a", "online.a"), ("teacher.b", "online.b")]
    assert all(e[3] is True for e in adds)            # student after the step
    assert all(e[4] == pytest.approx(0.1) for e in adds)
    assert not any("predictor" in str(e) for e in log)
    assert [e for e in log if e[0] == "mul_"] == [("mul_", "teacher.a", 0.9), ("mul_", "teacher.b", 0.9)]
    assert modules.optimizer.calls == 1


def test_wrapper_refuses_ema_after_a_failed_step_and_leaves_teacher_untouched():
    log = []

    def fail(online):
        raise RuntimeError("optimizer body failed")
    modules = _fake_modules(log, fail)
    with mock.patch.object(wrapper, "run_inactive_reference_update", _fake_reference(True)):
        with pytest.raises(StepCompletionError):
            wrapper.run_guarded_inactive_reference_update(
                modules, authority=_authority(), update_index=0)
    assert log == []


def test_existing_runtime_prechecks_accept_a_block_member_the_student_can_see():
    """Characterization (the gap the pilot pre-flight closes): with a block
    member moved to a visible measured gene and the hidden mask unchanged,
    the pinned runtime's own checks pass and execution reaches the teacher
    forward, here a fake that raises immediately (nothing is computed)."""
    import torch
    from sea_ad_jepa.v4.ipb_jepa import TargetBlocks
    from sea_ad_jepa.v5 import inactive_update_reference as reference
    measured = torch.ones(2, 8, dtype=torch.bool)
    measured[:, 7] = False
    hidden = torch.zeros(2, 8, dtype=torch.bool)
    hidden[:, [2, 3]] = True
    indices = torch.tensor([[[2, 5]], [[2, 3]]])          # row 0: gene 5 is visible
    blocks = TargetBlocks(hidden, indices, torch.ones_like(indices, dtype=torch.bool),
                          torch.zeros(2, dtype=torch.int64))

    class ReachedForward(Exception):
        pass

    def teacher_forward(*a, **k):
        raise ReachedForward
    modules = SimpleNamespace(
        teacher=mock.Mock(side_effect=teacher_forward, state_dict=lambda: {}),
        online=mock.Mock(side_effect=AssertionError("student must not run")),
        predictor=mock.Mock(side_effect=AssertionError("predictor must not run")),
        optimizer=SimpleNamespace(state={}, zero_grad=lambda set_to_none=True: None))
    callbacks = {name: mock.Mock(side_effect=AssertionError(name + " must not run"))
                 for name in ("backward_loss", "before_gradient_validation",
                              "guarded_optimizer_step", "guarded_ema_step")}
    with pytest.raises(ReachedForward):
        reference.run_inactive_reference_update(
            modules, expression=torch.ones(2, 8) * measured, measurement_mask=measured,
            stable_cell_keys=torch.tensor([1, 2]), operator_ids=[0, 0],
            measured_tokens_by_operator={0: 7}, scientific_cell_weights=torch.ones(2),
            target_block_views=[blocks], max_teacher_tokens_per_microbatch=14,
            run_seed=1, update_index=0, ema_momentum=0.5, **callbacks)
    for cb in callbacks.values():
        cb.assert_not_called()


def test_only_the_presentation_route_is_accepted_by_the_pilot():
    from scripts.v5 import jepa_v5_dev2048_pilot_preflight_v1 as pilot
    from sea_ad_jepa.v5 import inactive_update_reference as reference
    pilot.require_canonical_ema_route(pilot.canonical_route())
    for scalar_route in (wrapper.run_guarded_inactive_reference_update,
                         reference.run_inactive_reference_update):
        with pytest.raises(pilot.PilotPreflightRefusal, match="CANONICAL_PRESENTATION_EMA_ROUTE"):
            pilot.require_canonical_ema_route(scalar_route)
