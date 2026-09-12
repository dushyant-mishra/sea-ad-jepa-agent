from __future__ import annotations

import copy

import pytest
import torch

from sea_ad_jepa.v5.qualified_optimizer_guard_v1 import (
    CURSOR_KWARG,
    QualifiedOptimizerStepGuard,
)
from sea_ad_jepa.v5.qualified_teacher_target_receipt_v1 import (
    REQUIRED_V5_ROOTS,
    seal_qualified_teacher_target_receipt,
)


def _h(char: str) -> str:
    return char * 64


def _roots() -> dict[str, str]:
    digits = "12345"
    return {key: _h(digits[i]) for i, key in enumerate(REQUIRED_V5_ROOTS)}


def _receipt() -> dict:
    target = {
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
    return seal_qualified_teacher_target_receipt(
        target_freeze_receipt=target,
        v5_authority_roots=_roots(),
    )


def test_wrong_presented_cursor_fails_before_parameter_or_optimizer_state_change() -> None:
    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    optimizer = torch.optim.SGD([parameter], lr=0.1, momentum=0.9)
    parameter.grad = torch.tensor([1.0])
    guard = QualifiedOptimizerStepGuard(optimizer, _receipt(), _h("a"), _roots())
    guard.arm_for_step(schedule_cursor=7)

    parameter_before = parameter.detach().clone()
    state_before = copy.deepcopy(optimizer.state_dict())

    with pytest.raises(RuntimeError, match="schedule cursor"):
        optimizer.step(**{CURSOR_KWARG: 8})

    assert torch.equal(parameter, parameter_before)
    assert optimizer.state_dict() == state_before
    assert not guard.is_armed
    guard.close()
