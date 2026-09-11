from __future__ import annotations

import copy

import pytest
import torch

from sea_ad_jepa.v5.qualified_optimizer_guard_v1 import QualifiedOptimizerStepGuard
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


def test_receipt_rejects_28_donor_target() -> None:
    target = _target()
    target["n_development_donors"] = 28
    with pytest.raises(RuntimeError, match="46 development"):
        seal_qualified_teacher_target_receipt(
            target_freeze_receipt=target,
            v5_authority_roots=_roots(),
        )


def test_receipt_tamper_and_stale_runtime_fail() -> None:
    receipt = seal_qualified_teacher_target_receipt(
        target_freeze_receipt=_target(),
        v5_authority_roots=_roots(),
    )
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
    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    optimizer = torch.optim.SGD([parameter], lr=0.1, momentum=0.9)
    parameter.grad = torch.tensor([1.0])
    receipt = seal_qualified_teacher_target_receipt(
        target_freeze_receipt=_target(),
        v5_authority_roots=_roots(),
    )
    guard = QualifiedOptimizerStepGuard(
        optimizer,
        receipt,
        _h("a"),
        _roots(),
    )
    before = parameter.detach().clone()
    state_before = copy.deepcopy(optimizer.state_dict())
    with pytest.raises(RuntimeError, match="not armed"):
        optimizer.step()
    assert torch.equal(parameter, before)
    assert optimizer.state_dict() == state_before
    guard.close()


def test_one_arm_allows_exactly_one_step_then_fails_closed() -> None:
    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    optimizer = torch.optim.SGD([parameter], lr=0.1)
    parameter.grad = torch.tensor([1.0])
    receipt = seal_qualified_teacher_target_receipt(
        target_freeze_receipt=_target(),
        v5_authority_roots=_roots(),
    )
    guard = QualifiedOptimizerStepGuard(
        optimizer,
        receipt,
        _h("a"),
        _roots(),
    )
    guard.arm_for_step(schedule_cursor=7)
    optimizer.step()
    assert guard.assert_step_completed(schedule_cursor=7)["guarded_optimizer_step"]

    parameter.grad = torch.tensor([1.0])
    before = parameter.detach().clone()
    with pytest.raises(RuntimeError, match="not armed"):
        optimizer.step()
    assert torch.equal(parameter, before)
    guard.close()
