from __future__ import annotations

from types import SimpleNamespace

import pytest
import torch

from sea_ad_jepa.v5.qualified_teacher_student_runtime_v1 import qualified_production_update
from sea_ad_jepa.v5.qualified_teacher_target_receipt_v1 import (
    REQUIRED_V5_ROOTS,
    seal_qualified_teacher_target_receipt,
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


def _modules(installed_root: str | None):
    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    optimizer = torch.optim.SGD([parameter], lr=0.1)
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    modules = SimpleNamespace(
        optimizer=optimizer,
        parameter=parameter,
        scaler=scaler,
    )
    if installed_root is not None:
        modules.qualified_target_package_root = installed_root
    return modules


def _must_not_run(*args, **kwargs):  # pragma: no cover - rejection must precede update
    raise AssertionError("update function must not run when target-root binding is invalid")


def test_explicit_expected_root_cannot_override_wrong_installed_root() -> None:
    modules = _modules(_h("b"))
    before = modules.parameter.detach().clone()

    with pytest.raises(RuntimeError, match="caller-observed target package root"):
        qualified_production_update(
            modules,
            expression=None,
            measurement_mask=None,
            stable_mask_keys=None,
            schedule_cursor=2,
            target_receipt=_receipt(),
            expected_target_package_root=_h("a"),
            expected_v5_authority_roots=_roots(),
            observed_target_package_root=_h("a"),
            _update_fn=_must_not_run,
        )

    assert torch.equal(modules.parameter, before)
    assert not hasattr(modules.optimizer, "_v5_qualified_optimizer_guard")


def test_explicit_expected_root_cannot_substitute_for_missing_installed_root() -> None:
    modules = _modules(None)
    before = modules.parameter.detach().clone()

    with pytest.raises(RuntimeError, match="actually installed on the modules"):
        qualified_production_update(
            modules,
            expression=None,
            measurement_mask=None,
            stable_mask_keys=None,
            schedule_cursor=2,
            target_receipt=_receipt(),
            expected_target_package_root=_h("a"),
            expected_v5_authority_roots=_roots(),
            observed_target_package_root=_h("a"),
            _update_fn=_must_not_run,
        )

    assert torch.equal(modules.parameter, before)
    assert not hasattr(modules.optimizer, "_v5_qualified_optimizer_guard")
