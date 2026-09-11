from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest
import torch

from sea_ad_jepa.v5.qualified_optimizer_guard_v1 import (
    CURSOR_KWARG,
    QualifiedOptimizerStepGuard,
)
from sea_ad_jepa.v5.qualified_teacher_student_runtime_v1 import qualified_production_update
from sea_ad_jepa.v5.qualified_teacher_target_receipt_v1 import (
    REQUIRED_V5_ROOTS,
    seal_qualified_teacher_target_receipt,
    validate_qualified_teacher_target_receipt,
)


def _h(char: str) -> str:
    return char * 64


def _target() -> dict:
    return {
        "kind": "t0_v21_target_freeze_receipt_v1",
        "n_development_donors": 46,
        "package_root": _h("a"),
        "estimator_id": "S2",
        "bindings": {
            "code_sha": _h("b"),
            "contract_sha": _h("c"),
            "expression_root_digest": _h("d"),
            "role_ledger_digest": _h("e"),
        },
    }


def _roots() -> dict[str, str]:
    digits = "12345"
    return {key: _h(digits[i]) for i, key in enumerate(REQUIRED_V5_ROOTS)}


def _receipt() -> dict:
    return seal_qualified_teacher_target_receipt(
        target_freeze_receipt=_target(),
        v5_authority_roots=_roots(),
    )


def _module_with_sgd(momentum: float = 0.0):
    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    optimizer = torch.optim.SGD([parameter], lr=0.1, momentum=momentum)
    parameter.grad = torch.tensor([1.0])
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    return SimpleNamespace(
        optimizer=optimizer,
        parameter=parameter,
        scaler=scaler,
        qualified_target_package_root=_h("a"),
    )


def test_receipt_rejects_28_donor_target() -> None:
    target = _target()
    target["n_development_donors"] = 28
    with pytest.raises(RuntimeError, match="46 development"):
        seal_qualified_teacher_target_receipt(
            target_freeze_receipt=target,
            v5_authority_roots=_roots(),
        )


def test_receipt_tamper_and_stale_runtime_fail() -> None:
    receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    tampered["target_estimator_id"] = "S4"
    with pytest.raises(RuntimeError, match="digest"):
        validate_qualified_teacher_target_receipt(
            tampered,
            expected_target_package_root=_h("a"),
            expected_v5_authority_roots=_roots(),
        )

    stale = _roots()
    stale["v5_runtime_source_sha256"] = _h("f")
    with pytest.raises(RuntimeError, match="v5_runtime_source_sha256"):
        validate_qualified_teacher_target_receipt(
            receipt,
            expected_target_package_root=_h("a"),
            expected_v5_authority_roots=stale,
        )


def test_optimizer_step_without_arm_fails_before_parameter_or_state_change() -> None:
    modules = _module_with_sgd(momentum=0.9)
    guard = QualifiedOptimizerStepGuard(modules.optimizer, _receipt(), _h("a"), _roots())
    before = modules.parameter.detach().clone()
    state_before = copy.deepcopy(modules.optimizer.state_dict())
    with pytest.raises(RuntimeError, match="not armed"):
        modules.optimizer.step(**{CURSOR_KWARG: 0})
    assert torch.equal(modules.parameter, before)
    assert modules.optimizer.state_dict() == state_before
    guard.close()


def test_one_arm_allows_exactly_one_step_then_fails_closed() -> None:
    modules = _module_with_sgd()
    guard = QualifiedOptimizerStepGuard(modules.optimizer, _receipt(), _h("a"), _roots())
    guard.arm_for_step(schedule_cursor=7)
    modules.optimizer.step(**{CURSOR_KWARG: 7})
    assert guard.assert_step_completed(schedule_cursor=7)["guarded_optimizer_step"]

    modules.parameter.grad = torch.tensor([1.0])
    before = modules.parameter.detach().clone()
    with pytest.raises(RuntimeError, match="not armed"):
        modules.optimizer.step(**{CURSOR_KWARG: 7})
    assert torch.equal(modules.parameter, before)
    guard.close()


def test_armed_step_without_presented_cursor_is_refused_and_burns_authorization() -> None:
    modules = _module_with_sgd()
    guard = QualifiedOptimizerStepGuard(modules.optimizer, _receipt(), _h("a"), _roots())
    guard.arm_for_step(schedule_cursor=4)
    before = modules.parameter.detach().clone()
    with pytest.raises(RuntimeError, match="schedule cursor"):
        modules.optimizer.step()
    assert torch.equal(modules.parameter, before)
    assert not guard.is_armed
    guard.close()


def test_stale_authorization_after_skipped_amp_step_cannot_mutate_later() -> None:
    modules = _module_with_sgd()
    guard = QualifiedOptimizerStepGuard(modules.optimizer, _receipt(), _h("a"), _roots())
    guard.arm_for_step(schedule_cursor=11)
    # Simulate GradScaler skipping optimizer.step(): no hook fires and no mutation happens.
    assert guard.is_armed
    before = modules.parameter.detach().clone()
    with pytest.raises(RuntimeError, match="schedule cursor"):
        modules.optimizer.step()  # later unauthorized ordinary step, no cursor presented
    assert torch.equal(modules.parameter, before)
    assert not guard.is_armed
    guard.close()


def test_amp_scaler_step_hits_the_same_optimizer_hook_on_cpu_disabled_scaler() -> None:
    modules = _module_with_sgd()
    guard = QualifiedOptimizerStepGuard(modules.optimizer, _receipt(), _h("a"), _roots())
    with pytest.raises(RuntimeError, match="not armed"):
        modules.scaler.step(modules.optimizer, **{CURSOR_KWARG: 3})
    guard.arm_for_step(schedule_cursor=3)
    modules.scaler.step(modules.optimizer, **{CURSOR_KWARG: 3})
    modules.scaler.update()
    assert guard.assert_step_completed(schedule_cursor=3)["guarded_optimizer_step"]
    guard.close()


def test_qualified_update_entrypoint_arms_guard_at_the_update_boundary() -> None:
    modules = _module_with_sgd()

    def update_fn(mods, **kwargs):
        mods.scaler.step(mods.optimizer)
        mods.scaler.update()
        return {"schema": "teacher-student-update-v1", "schedule_cursor": kwargs["schedule_cursor"]}

    result = qualified_production_update(
        modules,
        expression=None,
        measurement_mask=None,
        stable_mask_keys=None,
        schedule_cursor=5,
        target_receipt=_receipt(),
        expected_target_package_root=_h("a"),
        expected_v5_authority_roots=_roots(),
        _update_fn=update_fn,
    )
    assert result["qualified_optimizer_guard"]["completed"]["guarded_optimizer_step"]
    assert result["qualified_optimizer_guard"]["resident_on_optimizer"]
    assert result["qualified_target_authority"]["target_package_root"] == _h("a")
    assert result["production_training_authorized"] is False


def test_resident_guard_blocks_direct_step_after_qualified_entrypoint_returns() -> None:
    modules = _module_with_sgd()

    def update_fn(mods, **kwargs):
        mods.scaler.step(mods.optimizer)
        mods.scaler.update()
        return {"schema": "teacher-student-update-v1", "schedule_cursor": kwargs["schedule_cursor"]}

    qualified_production_update(
        modules,
        expression=None,
        measurement_mask=None,
        stable_mask_keys=None,
        schedule_cursor=6,
        target_receipt=_receipt(),
        expected_target_package_root=_h("a"),
        expected_v5_authority_roots=_roots(),
        _update_fn=update_fn,
    )
    modules.parameter.grad = torch.tensor([1.0])
    before = modules.parameter.detach().clone()
    with pytest.raises(RuntimeError, match="not armed"):
        modules.optimizer.step()
    assert torch.equal(modules.parameter, before)


def test_qualified_update_entrypoint_fails_if_update_does_not_step_optimizer() -> None:
    modules = _module_with_sgd()

    def no_step_fn(mods, **kwargs):
        return {"schema": "teacher-student-update-v1", "schedule_cursor": kwargs["schedule_cursor"]}

    before = modules.parameter.detach().clone()
    with pytest.raises(RuntimeError, match="expected guarded optimizer step did not complete"):
        qualified_production_update(
            modules,
            expression=None,
            measurement_mask=None,
            stable_mask_keys=None,
            schedule_cursor=9,
            target_receipt=_receipt(),
            expected_target_package_root=_h("a"),
            expected_v5_authority_roots=_roots(),
            _update_fn=no_step_fn,
        )
    assert torch.equal(modules.parameter, before)


def test_qualified_update_entrypoint_refuses_stale_target_receipt_before_step() -> None:
    modules = _module_with_sgd()
    receipt = _receipt()
    before = modules.parameter.detach().clone()

    def update_fn(mods, **kwargs):  # pragma: no cover - must never be reached
        mods.scaler.step(mods.optimizer)
        return {"schedule_cursor": kwargs["schedule_cursor"]}

    with pytest.raises(RuntimeError, match="target package root mismatch"):
        qualified_production_update(
            modules,
            expression=None,
            measurement_mask=None,
            stable_mask_keys=None,
            schedule_cursor=1,
            target_receipt=receipt,
            expected_target_package_root=_h("f"),
            expected_v5_authority_roots=_roots(),
            _update_fn=update_fn,
        )
    assert torch.equal(modules.parameter, before)


def test_qualified_update_binds_target_root_installed_on_modules() -> None:
    modules = _module_with_sgd()
    modules.qualified_target_package_root = _h("b")

    def update_fn(mods, **kwargs):  # pragma: no cover - must never be reached
        mods.scaler.step(mods.optimizer)
        return {"schedule_cursor": kwargs["schedule_cursor"]}

    before = modules.parameter.detach().clone()
    with pytest.raises(RuntimeError, match="installed target package root"):
        qualified_production_update(
            modules,
            expression=None,
            measurement_mask=None,
            stable_mask_keys=None,
            schedule_cursor=2,
            target_receipt=_receipt(),
            expected_target_package_root=_h("a"),
            expected_v5_authority_roots=_roots(),
            _update_fn=update_fn,
        )
    assert torch.equal(modules.parameter, before)
