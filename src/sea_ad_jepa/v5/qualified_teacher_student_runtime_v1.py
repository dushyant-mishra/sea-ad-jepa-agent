"""V5 qualified teacher/student update entrypoint.

This module is the production-facing bridge between a qualified V21 target receipt
and the historical v4 teacher/student runtime.  It does not authorize training;
production_training_authorized remains false.  It only makes bounded qualification
updates fail closed unless the optimizer is armed by the exact 46-donor target
receipt immediately before the parameter-mutation boundary.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from sea_ad_jepa.v4.teacher_student_runtime import PRODUCTION_CONFIG, production_update

from .qualified_optimizer_guard_v1 import QualifiedOptimizerStepGuard
from .qualified_teacher_target_receipt_v1 import validate_qualified_teacher_target_receipt

STOP = "STOP_V5_QUALIFIED_UPDATE_NOT_VALID"


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def qualified_production_update(
    modules: Any,
    *,
    expression: Any,
    measurement_mask: Any,
    stable_mask_keys: Any,
    schedule_cursor: int,
    target_receipt: Mapping[str, Any],
    expected_target_package_root: str,
    expected_v5_authority_roots: Mapping[str, str],
    config: Any = PRODUCTION_CONFIG,
    _update_fn: Callable[..., dict[str, Any]] = production_update,
) -> dict[str, Any]:
    """Run one bounded-qualification update with the optimizer guard installed.

    The guard is registered directly on `modules.optimizer`, armed for exactly the
    schedule cursor requested here, and required to report completion after the
    update function returns.  Direct optimizer steps and AMP `scaler.step` are both
    intercepted because both invoke `optimizer.step()` on the guarded optimizer.
    """
    verified = validate_qualified_teacher_target_receipt(
        target_receipt,
        expected_target_package_root=expected_target_package_root,
        expected_v5_authority_roots=expected_v5_authority_roots,
    )
    cursor = int(schedule_cursor)
    if cursor < 0:
        raise ValueError("schedule_cursor must be nonnegative")
    if not hasattr(modules, "optimizer"):
        _fail("modules object must expose the optimizer to be guarded")

    guard = QualifiedOptimizerStepGuard(
        modules.optimizer,
        target_receipt,
        expected_target_package_root,
        expected_v5_authority_roots,
    )
    try:
        armed = guard.arm_for_step(schedule_cursor=cursor)
        result = _update_fn(
            modules,
            expression=expression,
            measurement_mask=measurement_mask,
            stable_mask_keys=stable_mask_keys,
            schedule_cursor=cursor,
            config=config,
        )
        if not isinstance(result, dict):
            _fail("qualified update function must return a dictionary receipt")
        completed = guard.assert_step_completed(schedule_cursor=cursor)
    finally:
        guard.close()

    if int(result.get("schedule_cursor", cursor)) != cursor:
        _fail("update receipt schedule cursor mismatch")
    result = dict(result)
    result["qualified_target_authority"] = verified
    result["qualified_optimizer_guard"] = {"armed": armed, "completed": completed}
    result["production_training_authorized"] = False
    return result
