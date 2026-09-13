from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest
import torch

from sea_ad_jepa.v5.qualified_teacher_student_runtime_v1 import qualified_production_update
from sea_ad_jepa.v5.qualified_teacher_target_receipt_v1 import (
    LEGACY_T0_AUTHORITY_SCOPE,
    REQUIRED_V5_ROOTS,
    seal_qualified_teacher_target_receipt,
    validate_qualified_teacher_target_receipt,
)


def _h(char: str) -> str:
    return char * 64


def _roots() -> dict[str, str]:
    digits = "12345"
    return {key: _h(digits[i]) for i, key in enumerate(REQUIRED_V5_ROOTS)}


def _legacy_t0_receipt() -> dict:
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


def _modules():
    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    optimizer = torch.optim.SGD([parameter], lr=0.1)
    parameter.grad = torch.tensor([1.0])
    return SimpleNamespace(
        optimizer=optimizer,
        parameter=parameter,
        scaler=torch.amp.GradScaler("cuda", enabled=False),
        qualified_target_package_root=_h("a"),
    )


def test_v21_receipt_is_explicitly_classified_as_legacy_t0_only() -> None:
    verified = validate_qualified_teacher_target_receipt(
        _legacy_t0_receipt(),
        expected_target_package_root=_h("a"),
        expected_v5_authority_roots=_roots(),
    )
    assert verified["authority_scope"] == LEGACY_T0_AUTHORITY_SCOPE
    assert verified["current_v5_teacher_authority"] is False


def test_active_v5_runtime_refuses_legacy_t0_target_before_any_update() -> None:
    modules = _modules()
    before = modules.parameter.detach().clone()
    reached_update = False

    def update_fn(mods, **kwargs):  # pragma: no cover - must never be reached
        nonlocal reached_update
        reached_update = True
        mods.scaler.step(mods.optimizer)
        mods.scaler.update()
        return {"schedule_cursor": kwargs["schedule_cursor"]}

    with pytest.raises(RuntimeError, match="legacy T0/V21.*current V5 teacher authority"):
        qualified_production_update(
            modules,
            expression=None,
            measurement_mask=None,
            stable_mask_keys=None,
            schedule_cursor=0,
            target_receipt=_legacy_t0_receipt(),
            expected_target_package_root=_h("a"),
            expected_v5_authority_roots=_roots(),
            config=object(),
            _update_fn=update_fn,
        )

    assert reached_update is False
    assert torch.equal(modules.parameter, before)
    assert not hasattr(modules.optimizer, "_v5_qualified_optimizer_guard")


def test_active_v5_runtime_has_no_historical_v4_config_default() -> None:
    parameter = inspect.signature(qualified_production_update).parameters["config"]
    assert parameter.default is None
