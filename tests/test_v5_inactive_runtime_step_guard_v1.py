from pathlib import Path

import pytest
import torch

from sea_ad_jepa.v5.inactive_runtime_step_guard_v1 import (
    CURSOR_KWARG,
    InactiveReferenceOptimizerStepGuardV1,
    install_inactive_reference_optimizer_guard_v1,
)


def _optimizer():
    p = torch.nn.Parameter(torch.tensor([1.0]))
    return p, torch.optim.SGD([p], lr=0.1)


def test_direct_step_is_rejected_when_guard_installed():
    p, opt = _optimizer()
    guard = install_inactive_reference_optimizer_guard_v1(opt)
    p.grad = torch.ones_like(p)
    before = p.detach().clone()
    with pytest.raises(RuntimeError, match="authority not armed"):
        opt.step()
    assert torch.equal(p.detach(), before)
    guard.close()


def test_guarded_step_requires_explicit_completion_acknowledgement():
    p, opt = _optimizer()
    guard = install_inactive_reference_optimizer_guard_v1(opt)
    p.grad = torch.ones_like(p)
    guard.arm_for_step(schedule_cursor=0)
    opt.step(**{CURSOR_KWARG: 0})
    with pytest.raises(RuntimeError, match="prior step unacknowledged"):
        guard.arm_for_step(schedule_cursor=1)
    proof = guard.assert_step_completed(schedule_cursor=0)
    assert proof["guarded_optimizer_step"] is True
    assert proof["training_authorized"] is False
    guard.close()


def test_wrong_cursor_fails_closed_without_parameter_update():
    p, opt = _optimizer()
    guard = install_inactive_reference_optimizer_guard_v1(opt)
    p.grad = torch.ones_like(p)
    before = p.detach().clone()
    guard.arm_for_step(schedule_cursor=0)
    with pytest.raises(RuntimeError, match="cursor mismatch"):
        opt.step(**{CURSOR_KWARG: 1})
    assert torch.equal(p.detach(), before)
    guard.close()


def test_guard_is_explicitly_mechanics_only_and_never_training_authority():
    _, opt = _optimizer()
    guard = install_inactive_reference_optimizer_guard_v1(opt)
    assert isinstance(guard, InactiveReferenceOptimizerStepGuardV1)
    assert guard.mechanics_only is True
    assert guard.training_authorized is False
    guard.close()


def test_canonical_consumer_does_not_mutate_teacher_ema_directly():
    """EMA must be owned by the mutation guard, not the V5 consumer body."""
    source = Path("src/sea_ad_jepa/v5/inactive_update_reference.py").read_text(encoding="utf-8")
    forbidden = (
        "teacher.mul_(m).add_(online,alpha=1.0-m)",
        "teacher.mul_(m).add_(online, alpha=1.0-m)",
    )
    assert not any(fragment in source for fragment in forbidden), (
        "inactive_update_reference.py still has a directly reachable EMA mutation path; "
        "the canonical successor must route EMA through the guarded completion boundary"
    )
